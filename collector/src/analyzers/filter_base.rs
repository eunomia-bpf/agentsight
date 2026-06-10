// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::filter_metrics::MetricsSlot;
use super::{Analyzer, AnalyzerError};
use crate::runners::EventStream;
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::Value;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

pub(super) trait FilterExpr: Clone + Send + Sync + 'static {
    fn evaluate(&self, data: &Value) -> bool;
}

/// Shared boolean expression tree for filter DSLs. The condition type `C`
/// carries each filter's field/operator semantics; And/Or/Empty behavior is
/// identical across filters and lives here once.
#[derive(Debug, Clone)]
pub(super) enum ExprNode<C> {
    And(Vec<ExprNode<C>>),
    Or(Vec<ExprNode<C>>),
    Condition(C),
    Empty,
}

impl<C> ExprNode<C> {
    pub(super) fn evaluate(&self, eval: &impl Fn(&C) -> bool) -> bool {
        match self {
            ExprNode::And(nodes) => nodes.iter().all(|node| node.evaluate(eval)),
            ExprNode::Or(nodes) => nodes.iter().any(|node| node.evaluate(eval)),
            ExprNode::Condition(condition) => eval(condition),
            ExprNode::Empty => false,
        }
    }
}

/// String comparison shared by filter condition evaluators.
pub(super) fn cmp_str(actual: &str, op: &str, expected: &str) -> bool {
    match op {
        "exact" => actual == expected,
        "not_equal" => actual != expected,
        "contains" => actual.contains(expected),
        "prefix" => actual.starts_with(expected),
        "suffix" => actual.ends_with(expected),
        _ => false,
    }
}

pub(super) fn cmp_num(actual: u64, op: &str, expected: &str) -> bool {
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

pub(super) fn cmp_float(actual: f64, op: &str, expected: &str) -> bool {
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

pub(super) enum MetricsStrategy {
    AddOnDrop,
    SetPerEvent,
}

pub(super) struct FilterBase<E: FilterExpr> {
    filters: Vec<E>,
    total: Arc<AtomicU64>,
    filtered: Arc<AtomicU64>,
    passed: Arc<AtomicU64>,
    source_name: &'static str,
    strategy: MetricsStrategy,
    global_slot: &'static MetricsSlot,
}

impl<E: FilterExpr> FilterBase<E> {
    pub fn new(
        source_name: &'static str,
        strategy: MetricsStrategy,
        global_slot: &'static MetricsSlot,
    ) -> Self {
        if matches!(strategy, MetricsStrategy::SetPerEvent) {
            super::filter_metrics::set(global_slot, 0, 0, 0);
        }
        Self {
            filters: Vec::new(),
            total: Arc::new(AtomicU64::new(0)),
            filtered: Arc::new(AtomicU64::new(0)),
            passed: Arc::new(AtomicU64::new(0)),
            source_name,
            strategy,
            global_slot,
        }
    }

    pub fn with_patterns(mut self, patterns: Vec<String>, parse: impl Fn(&str) -> E) -> Self {
        self.filters = patterns.iter().map(|p| parse(p)).collect();
        self
    }

    fn publish_global(&self) {
        let t = self.total.load(Ordering::Relaxed);
        let f = self.filtered.load(Ordering::Relaxed);
        let p = self.passed.load(Ordering::Relaxed);
        match self.strategy {
            MetricsStrategy::AddOnDrop => super::filter_metrics::add(self.global_slot, t, f, p),
            MetricsStrategy::SetPerEvent => super::filter_metrics::set(self.global_slot, t, f, p),
        }
    }
}

#[async_trait]
impl<E: FilterExpr> Analyzer for FilterBase<E> {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let filters = self.filters.clone();
        let source_name = self.source_name;
        let set_per_event = matches!(self.strategy, MetricsStrategy::SetPerEvent);
        let total = self.total.clone();
        let filtered = self.filtered.clone();
        let passed = self.passed.clone();
        let global_slot: &'static MetricsSlot = self.global_slot;

        let out = stream.filter_map(move |event| {
            let filters = filters.clone();
            let total = total.clone();
            let filtered = filtered.clone();
            let passed = passed.clone();

            async move {
                total.fetch_add(1, Ordering::Relaxed);

                let should_filter = !filters.is_empty()
                    && event.source == source_name
                    && filters.iter().any(|f| f.evaluate(&event.data));

                if should_filter {
                    filtered.fetch_add(1, Ordering::Relaxed);
                } else {
                    passed.fetch_add(1, Ordering::Relaxed);
                }

                if set_per_event {
                    super::filter_metrics::set(
                        global_slot,
                        total.load(Ordering::Relaxed),
                        filtered.load(Ordering::Relaxed),
                        passed.load(Ordering::Relaxed),
                    );
                }

                if should_filter { None } else { Some(event) }
            }
        });

        Ok(Box::pin(out))
    }
}

impl<E: FilterExpr> Drop for FilterBase<E> {
    fn drop(&mut self) {
        if matches!(self.strategy, MetricsStrategy::AddOnDrop) {
            self.publish_global();
        }
    }
}
