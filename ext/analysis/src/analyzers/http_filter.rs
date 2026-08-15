// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::filter_base::{FilterBase, FilterExpr, MetricsStrategy};
use super::{Analyzer, AnalyzerError};
use crate::runners::EventStream;
use async_trait::async_trait;
use serde_json::Value;

static GLOBAL_METRICS: super::filter_metrics::MetricsSlot = std::sync::OnceLock::new();

pub fn print_global_http_filter_metrics() {
    super::filter_metrics::print("HTTPFilter", &GLOBAL_METRICS);
}

pub struct HTTPFilter {
    base: FilterBase<HttpFilterExpr>,
}

#[derive(Debug, Clone)]
pub struct HttpFilterExpr {
    parsed: FilterNode,
}

#[derive(Debug, Clone)]
enum FilterNode {
    And(Vec<FilterNode>),
    Or(Vec<FilterNode>),
    Condition {
        target: String,
        field: String,
        operator: String,
        value: String,
    },
    Empty,
}

impl FilterExpr for HttpFilterExpr {
    fn evaluate(&self, data: &Value) -> bool {
        evaluate_node(&self.parsed, data)
    }
}

impl HTTPFilter {
    pub fn with_patterns(patterns: Vec<String>) -> Self {
        Self {
            base: FilterBase::new("http_parser", MetricsStrategy::SetPerEvent, &GLOBAL_METRICS)
                .with_patterns(patterns, HttpFilterExpr::parse),
        }
    }
}

#[async_trait]
impl Analyzer for HTTPFilter {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        self.base.process(stream).await
    }
}

// --- Expression parsing ---

impl HttpFilterExpr {
    pub fn parse(expression: &str) -> Self {
        let trimmed = expression.trim();
        if trimmed.is_empty() {
            return Self {
                parsed: FilterNode::Empty,
            };
        }
        Self {
            parsed: parse_or(trimmed),
        }
    }
}

fn parse_or(expr: &str) -> FilterNode {
    let parts: Vec<&str> = expr.split('|').map(str::trim).collect();
    if parts.len() > 1 {
        FilterNode::Or(parts.into_iter().map(parse_and).collect())
    } else {
        parse_and(expr)
    }
}

fn parse_and(expr: &str) -> FilterNode {
    let parts: Vec<&str> = expr.split('&').map(str::trim).collect();
    if parts.len() > 1 {
        FilterNode::And(parts.into_iter().map(parse_single).collect())
    } else {
        parse_single(expr)
    }
}

fn parse_single(cond: &str) -> FilterNode {
    let cond = cond.trim();
    if !cond.contains('=') {
        return FilterNode::Condition {
            target: "request".into(),
            field: "path".into(),
            operator: "contains".into(),
            value: cond.into(),
        };
    }
    let Some((key, value)) = cond.split_once('=') else {
        return FilterNode::Empty;
    };
    let (key, value) = (key.trim(), value.trim());

    if let Some((target_raw, field)) = key.split_once('.') {
        let (target, operator) = match target_raw.trim() {
            "request" | "req" => {
                let op = match field.trim() {
                    "path_prefix" | "path_starts_with" => "prefix",
                    "path_contains" | "path_includes" => "contains",
                    _ => "exact",
                };
                ("request", op)
            }
            "response" | "resp" | "res" => ("response", "exact"),
            _ => ("request", "exact"),
        };
        FilterNode::Condition {
            target: target.into(),
            field: field.trim().into(),
            operator: operator.into(),
            value: value.into(),
        }
    } else {
        let operator = match key {
            "path_prefix" | "path_starts_with" => "prefix",
            "path_contains" | "path_includes" => "contains",
            _ => "exact",
        };
        FilterNode::Condition {
            target: "request".into(),
            field: key.into(),
            operator: operator.into(),
            value: value.into(),
        }
    }
}

// --- Evaluation ---

fn evaluate_node(node: &FilterNode, data: &Value) -> bool {
    match node {
        FilterNode::Empty => false,
        FilterNode::And(cs) => cs.iter().all(|c| evaluate_node(c, data)),
        FilterNode::Or(cs) => cs.iter().any(|c| evaluate_node(c, data)),
        FilterNode::Condition {
            target,
            field,
            operator,
            value,
        } => {
            let msg_type = data
                .get("message_type")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let matches_target = match target.as_str() {
                "request" => msg_type == "request",
                "response" => msg_type == "response",
                _ => false,
            };
            if !matches_target {
                return false;
            }
            if target == "request" {
                eval_request(field, operator, value, data)
            } else {
                eval_response(field, value, data)
            }
        }
    }
}

fn eval_request(field: &str, operator: &str, value: &str, data: &Value) -> bool {
    match field {
        "method" | "verb" => {
            let m = data.get("method").and_then(|v| v.as_str()).unwrap_or("");
            m.eq_ignore_ascii_case(value)
        }
        "path" | "path_exact" => {
            let p = data.get("path").and_then(|v| v.as_str()).unwrap_or("");
            match operator {
                "prefix" => p.starts_with(value),
                "contains" => p.contains(value),
                _ => p == value,
            }
        }
        "path_prefix" | "path_starts_with" => data
            .get("path")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .starts_with(value),
        "path_contains" | "path_includes" => data
            .get("path")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .contains(value),
        "host" | "hostname" => header_val(data, "host").unwrap_or("") == value,
        "body" | "body_contains" => data
            .get("body")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .contains(value),
        _ => {
            let path = data.get("path").and_then(|v| v.as_str()).unwrap_or("");
            path.split_once('?')
                .map(|(_, q)| q.contains(&format!("{field}={value}")))
                .unwrap_or(false)
        }
    }
}

fn eval_response(field: &str, value: &str, data: &Value) -> bool {
    match field {
        "status_code" | "status" | "code" => {
            let sc = data
                .get("status_code")
                .and_then(|v| v.as_u64())
                .unwrap_or(0);
            value.parse::<u64>().ok().is_some_and(|v| sc == v)
        }
        "status_text" | "status_message" => {
            let t = data
                .get("status_text")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            t.to_lowercase().contains(&value.to_lowercase())
        }
        "content_type" | "content-type" => header_val(data, "content-type")
            .unwrap_or("")
            .contains(value),
        "body" | "body_contains" => data
            .get("body")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .contains(value),
        _ => header_val(data, field).unwrap_or("").contains(value),
    }
}

fn header_val<'a>(data: &'a Value, name: &str) -> Option<&'a str> {
    data.get("headers")?.get(name)?.as_str()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_expression_parsing() {
        let expr = HttpFilterExpr::parse("request.path=/health");
        assert!(expr.evaluate(&json!({"message_type": "request", "path": "/health"})));
        assert!(!expr.evaluate(&json!({"message_type": "request", "path": "/api"})));
    }

    #[test]
    fn test_request_filtering() {
        let f = HttpFilterExpr::parse("request.method=GET");
        assert!(f.evaluate(&json!({"message_type": "request", "method": "GET"})));
        assert!(!f.evaluate(&json!({"message_type": "request", "method": "POST"})));
    }

    #[test]
    fn test_response_filtering() {
        let f = HttpFilterExpr::parse("response.status_code=404");
        assert!(f.evaluate(&json!({"message_type": "response", "status_code": 404})));
        assert!(!f.evaluate(&json!({"message_type": "response", "status_code": 200})));
    }

    #[test]
    fn test_complex_expressions() {
        let f = HttpFilterExpr::parse("request.method=GET | response.status_code=404");
        assert!(f.evaluate(&json!({"message_type": "request", "method": "GET"})));
        assert!(f.evaluate(&json!({"message_type": "response", "status_code": 404})));
        assert!(!f.evaluate(&json!({"message_type": "request", "method": "POST"})));
    }
}
