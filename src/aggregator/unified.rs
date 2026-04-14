//! Unified Aggregator - high-level entry point for event aggregation
//!
//! This module provides a unified interface for aggregating parsed messages.
//! It combines HTTP Connection Aggregator and Process Event Aggregator.

use super::http::{ConnectionId, HttpConnectionAggregator};
use super::http2::Http2StreamAggregator;
use super::proctrace::ProcessEventAggregator;
use super::result::AggregatedResult;
use crate::chrome_trace::{export_trace_events, ToChromeTraceEvent};
use crate::parser::{ParseResult, ParsedMessage};

/// Unified aggregator for all event types
///
/// This aggregator provides a unified entry point for aggregating parsed messages.
/// It internally manages HTTP connections, HTTP/2 streams, and process lifecycles.
pub struct Aggregator {
    http: HttpConnectionAggregator,
    http2: Http2StreamAggregator,
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
            http2: Http2StreamAggregator::new(),
            process: ProcessEventAggregator::new(),
        }
    }

    /// Process a parsed message
    ///
    /// Returns aggregated results when complete units are formed.
    /// Note: Returns a Vec because HTTP/2 frame processing can produce multiple completed streams.
    fn process_message(&mut self, msg: ParsedMessage) -> Vec<AggregatedResult> {
        match msg {
            ParsedMessage::Request(req) => {
                self.http.process_request(req);
                vec![]
            }
            ParsedMessage::Response(resp) => {
                self.http.process_response(resp).into_iter().collect()
            }
            ParsedMessage::SseEvent(sse_event) => {
                let conn_id = ConnectionId::from_ssl_event(sse_event.source_event());
                self.http.process_sse_event(&conn_id, sse_event).into_iter().collect()
            }
            ParsedMessage::ProcEvent(proc_event) => {
                self.process
                    .process_parsed_event(&proc_event)
                    .map(AggregatedResult::ProcessComplete)
                    .into_iter()
                    .collect()
            }
            ParsedMessage::Http2Frames(frames) => {
                // Use HTTP/2 stream aggregator to correlate frames by stream_id
                let completed_streams = self.http2.process_frames(frames);
                completed_streams
                    .into_iter()
                    .map(AggregatedResult::Http2StreamComplete)
                    .collect()
            }
        }
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
        let results: Vec<AggregatedResult> = result
            .messages
            .into_iter()
            .flat_map(|msg| self.process_message(msg))
            .collect();
        
        // Export chrome trace if enabled
        for r in &results {
            export_trace_events(r);
        }
        
        results
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
        self.http.has_pending() || self.http2.has_pending() || self.process.has_pending()
    }

    /// Clear all aggregations
    pub fn clear(&mut self) {
        self.http.clear();
        self.http2.clear();
        self.process.clear();
    }
}
