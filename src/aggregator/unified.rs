//! Unified Aggregator - high-level entry point for event aggregation
//!
//! This module provides a unified interface for aggregating parsed messages.
//! It combines HTTP Connection Aggregator and Process Event Aggregator.

use super::http::{ConnectionId, HttpConnectionAggregator};
use super::proctrace::ProcessEventAggregator;
use super::result::AggregatedResult;
use crate::chrome_trace::{export_trace_events, ToChromeTraceEvent};
use crate::parser::{ParseResult, ParsedMessage};

/// Unified aggregator for all event types
///
/// This aggregator provides a unified entry point for aggregating parsed messages.
/// It internally manages HTTP connections and process lifecycles.
pub struct Aggregator {
    http: HttpConnectionAggregator,
    process: ProcessEventAggregator,
}

impl Default for Aggregator {
    fn default() -> Self {
        Self::new()
    }
}

impl Aggregator {
    /// Create new unified aggregator
    pub fn new() -> Self {
        Aggregator {
            http: HttpConnectionAggregator::new(),
            process: ProcessEventAggregator::new(),
        }
    }

    /// Process a parsed message
    ///
    /// Returns aggregated result when a complete unit is formed.
    pub fn process_message(&mut self, msg: ParsedMessage) -> Option<AggregatedResult> {
        let result = match msg {
            ParsedMessage::Request(req) => {
                self.http.process_request(req);
                None
            }
            ParsedMessage::Response(resp) => self.http.process_response(resp),
            ParsedMessage::SseEvent(sse_event) => {
                let conn_id = ConnectionId::from_ssl_event(sse_event.source_event());
                self.http.process_sse_event(&conn_id, sse_event)
            }
            ParsedMessage::ProcEvent(proc_event) => self
                .process
                .process_parsed_event(&proc_event)
                .map(AggregatedResult::ProcessComplete),
        };

        // Export chrome trace if enabled
        if let Some(ref r) = result {
            export_trace_events(r);
        }

        result
    }

    /// Process parse result
    pub fn process_result(&mut self, result: ParseResult) -> Vec<AggregatedResult> {
        log::debug!(
            "Aggregating parsed results({}): {}",
            result.messages.len(),
            result
                .messages
                .iter()
                .map(|x| x.message_type())
                .collect::<Vec<_>>()
                .join(", ")
        );
        result
            .messages
            .into_iter()
            .filter_map(|msg| self.process_message(msg))
            .collect()
    }

    /// Get reference to HTTP aggregator
    pub fn http(&self) -> &HttpConnectionAggregator {
        &self.http
    }

    /// Get mutable reference to HTTP aggregator
    pub fn http_mut(&mut self) -> &mut HttpConnectionAggregator {
        &mut self.http
    }

    /// Get reference to process aggregator
    pub fn process(&self) -> &ProcessEventAggregator {
        &self.process
    }

    /// Get mutable reference to process aggregator
    pub fn process_mut(&mut self) -> &mut ProcessEventAggregator {
        &mut self.process
    }

    /// Check if there are any pending aggregations
    pub fn has_pending(&self) -> bool {
        self.http.has_pending() || self.process.has_pending()
    }

    /// Clear all aggregations
    pub fn clear(&mut self) {
        self.http.clear();
        self.process.clear();
    }
}
