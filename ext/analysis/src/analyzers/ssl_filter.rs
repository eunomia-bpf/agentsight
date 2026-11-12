// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common;
use super::filter_base::{FilterBase, FilterExpr, MetricsStrategy};
use super::{Analyzer, AnalyzerError};
use crate::runners::EventStream;
use async_trait::async_trait;
use serde_json::Value;

static GLOBAL_METRICS: super::filter_metrics::MetricsSlot = std::sync::OnceLock::new();

pub fn print_global_ssl_filter_metrics() {
    super::filter_metrics::print("SSLFilter", &GLOBAL_METRICS);
}

pub struct SSLFilter {
    base: FilterBase<SslFilterExpr>,
}

#[derive(Debug, Clone)]
pub struct SslFilterExpr {
    parsed: FilterNode,
}

#[derive(Debug, Clone)]
enum FilterNode {
    And(Box<FilterNode>, Box<FilterNode>),
    Or(Box<FilterNode>, Box<FilterNode>),
    Condition {
        field: String,
        operator: String,
        value: String,
    },
    Empty,
}

impl FilterExpr for SslFilterExpr {
    fn evaluate(&self, data: &Value) -> bool {
        evaluate_node(&self.parsed, data)
    }
}

impl SSLFilter {
    pub fn with_patterns(patterns: Vec<String>) -> Self {
        Self {
            base: FilterBase::new("ssl", MetricsStrategy::AddOnDrop, &GLOBAL_METRICS)
                .with_patterns(patterns, SslFilterExpr::parse),
        }
    }
}

#[async_trait]
impl Analyzer for SSLFilter {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        self.base.process(stream).await
    }
}

// --- Expression parsing ---

impl SslFilterExpr {
    pub fn parse(expression: &str) -> Self {
        Self {
            parsed: parse_expression(expression),
        }
    }

    pub fn process_escape_sequences(value: &str) -> String {
        let mut result = String::new();
        let mut chars = value.chars().peekable();
        while let Some(ch) = chars.next() {
            if ch == '\\' {
                match chars.peek() {
                    Some('r') => {
                        chars.next();
                        result.push('\r');
                    }
                    Some('n') => {
                        chars.next();
                        result.push('\n');
                    }
                    Some('t') => {
                        chars.next();
                        result.push('\t');
                    }
                    Some('\\') => {
                        chars.next();
                        result.push('\\');
                    }
                    Some('"') => {
                        chars.next();
                        result.push('"');
                    }
                    _ => result.push(ch),
                }
            } else {
                result.push(ch);
            }
        }
        result
    }
}

fn parse_expression(expr: &str) -> FilterNode {
    let expr = expr.trim();
    if expr.is_empty() {
        return FilterNode::Empty;
    }
    if let Some(pos) = find_operator(expr, '|') {
        return FilterNode::Or(
            Box::new(parse_expression(&expr[..pos])),
            Box::new(parse_expression(&expr[pos + 1..])),
        );
    }
    if let Some(pos) = find_operator(expr, '&') {
        return FilterNode::And(
            Box::new(parse_expression(&expr[..pos])),
            Box::new(parse_expression(&expr[pos + 1..])),
        );
    }
    parse_condition(expr)
}

fn find_operator(expr: &str, op: char) -> Option<usize> {
    let mut depth = 0;
    for (i, c) in expr.chars().enumerate() {
        match c {
            '(' => depth += 1,
            ')' => depth -= 1,
            _ if c == op && depth == 0 => return Some(i),
            _ => {}
        }
    }
    None
}

fn parse_condition(expr: &str) -> FilterNode {
    let expr = expr.trim();
    if expr.starts_with('(') && expr.ends_with(')') {
        return parse_expression(&expr[1..expr.len() - 1]);
    }
    for &op in &[">=", "<=", "!=", "=", ">", "<", "~"] {
        if let Some(pos) = expr.find(op) {
            let field = expr[..pos].trim().to_string();
            let raw_value = expr[pos + op.len()..].trim();
            let operator = match op {
                "=" => "exact",
                "!=" => "not_equal",
                ">" => "gt",
                "<" => "lt",
                ">=" => "gte",
                "<=" => "lte",
                "~" => "contains",
                _ => "exact",
            }
            .to_string();
            return FilterNode::Condition {
                field,
                operator,
                value: SslFilterExpr::process_escape_sequences(raw_value),
            };
        }
    }
    FilterNode::Empty
}

// --- Evaluation ---

fn evaluate_node(node: &FilterNode, data: &Value) -> bool {
    match node {
        FilterNode::And(l, r) => evaluate_node(l, data) && evaluate_node(r, data),
        FilterNode::Or(l, r) => evaluate_node(l, data) || evaluate_node(r, data),
        FilterNode::Condition {
            field,
            operator,
            value,
        } => eval_condition(field, operator, value, data),
        FilterNode::Empty => false,
    }
}

fn eval_condition(field: &str, operator: &str, expected: &str, data: &Value) -> bool {
    if field == "data.type" {
        if let Some(v) = data.get("data").and_then(|v| v.as_str()) {
            return cmp_str(common::detect_data_type(v), operator, expected);
        }
        return false;
    }
    match field {
        "is_handshake" | "truncated" => {
            data.get(field).and_then(|v| v.as_bool()).unwrap_or(false) == (expected == "true")
        }
        "len" | "pid" | "tid" | "uid" | "timestamp_ns" => data
            .get(field)
            .and_then(|v| v.as_u64())
            .map(|n| cmp_num(n, operator, expected))
            .unwrap_or(false),
        "latency_ms" => data
            .get("latency_ms")
            .and_then(|v| v.as_f64())
            .map(|n| cmp_float(n, operator, expected))
            .unwrap_or(false),
        _ => data
            .get(field)
            .and_then(|v| v.as_str())
            .map(|v| cmp_str(v, operator, expected))
            .unwrap_or(false),
    }
}

fn cmp_str(actual: &str, op: &str, expected: &str) -> bool {
    match op {
        "exact" => actual == expected,
        "not_equal" => actual != expected,
        "contains" => actual.contains(expected),
        "prefix" => actual.starts_with(expected),
        "suffix" => actual.ends_with(expected),
        _ => false,
    }
}

fn cmp_num(actual: u64, op: &str, expected: &str) -> bool {
    let Ok(e) = expected.parse::<u64>() else {
        return false;
    };
    match op {
        "exact" => actual == e,
        "not_equal" => actual != e,
        "gt" => actual > e,
        "lt" => actual < e,
        "gte" => actual >= e,
        "lte" => actual <= e,
        _ => false,
    }
}

fn cmp_float(actual: f64, op: &str, expected: &str) -> bool {
    let Ok(e) = expected.parse::<f64>() else {
        return false;
    };
    match op {
        "exact" => (actual - e).abs() < f64::EPSILON,
        "not_equal" => (actual - e).abs() >= f64::EPSILON,
        "gt" => actual > e,
        "lt" => actual < e,
        "gte" => actual >= e,
        "lte" => actual <= e,
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_expression_parsing() {
        let expr = SslFilterExpr::parse("function=READ/RECV");
        assert!(expr.evaluate(&json!({"function": "READ/RECV"})));
        assert!(!expr.evaluate(&json!({"function": "WRITE/SEND"})));
    }

    #[test]
    fn test_data_filtering() {
        let expr = SslFilterExpr::parse("data~chunked");
        assert!(expr.evaluate(&json!({"data": "chunked data here"})));
        assert!(!expr.evaluate(&json!({"data": "plain text"})));
    }

    #[test]
    fn test_numeric_filtering() {
        let expr = SslFilterExpr::parse("len<10");
        assert!(expr.evaluate(&json!({"len": 5})));
        assert!(!expr.evaluate(&json!({"len": 15})));
    }

    #[test]
    fn test_complex_expressions() {
        let expr = SslFilterExpr::parse("data~chunked&function=READ/RECV");
        assert!(expr.evaluate(&json!({"data": "chunked data", "function": "READ/RECV"})));
        assert!(!expr.evaluate(&json!({"data": "chunked data", "function": "WRITE/SEND"})));
        assert!(!expr.evaluate(&json!({"data": "plain text", "function": "WRITE/SEND"})));
    }

    #[test]
    fn test_escape_sequences() {
        assert_eq!(
            SslFilterExpr::process_escape_sequences("0\\r\\n\\r\\n"),
            "0\r\n\r\n"
        );
        assert_eq!(
            SslFilterExpr::process_escape_sequences("hello\\tworld\\n"),
            "hello\tworld\n"
        );

        let expr = SslFilterExpr::parse("data=0\\r\\n\\r\\n");
        assert!(expr.evaluate(&json!({"data": "0\r\n\r\n"})));
        assert!(!expr.evaluate(&json!({"data": "HTTP/1.1 200 OK"})));
    }
}
