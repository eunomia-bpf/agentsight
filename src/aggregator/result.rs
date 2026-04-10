//! Aggregated Result types for event aggregation
//!
//! This module defines the `AggregatedResult` enum which represents
//! the output of aggregating parsed messages from various sources.

use crate::chrome_trace::{ChromeTraceEvent, ToChromeTraceEvent};
use crate::parser::http2::ParsedHttp2Frame;
use super::http::{ConnectionId, HttpPair, ParsedRequest, AggregatedResponse};
use super::http2::Http2Stream;
use super::proctrace::AggregatedProcess;

/// Aggregated result from any aggregator
#[derive(Debug, Clone)]
pub enum AggregatedResult {
    /// HTTP request/response pair complete
    HttpComplete(HttpPair),
    /// SSE stream complete (received [DONE])
    SseComplete(HttpPair),
    /// Process lifecycle complete
    ProcessComplete(AggregatedProcess),
    /// Standalone request (no matching response yet)
    RequestOnly {
        connection_id: ConnectionId,
        request: ParsedRequest,
    },
    /// Standalone response (no matching request)
    ResponseOnly {
        connection_id: ConnectionId,
        response: AggregatedResponse,
    },
    /// HTTP/2 frames (pass-through, no stream reassembly)
    Http2Frames {
        connection_id: ConnectionId,
        frames: Vec<ParsedHttp2Frame>,
    },
    /// HTTP/2 stream complete (request/response aggregated by stream_id)
    Http2StreamComplete(Http2Stream),
}

impl AggregatedResult {
    /// Get the result type as a string
    pub fn result_type(&self) -> &'static str {
        match self {
            AggregatedResult::HttpComplete(_) => "http_complete",
            AggregatedResult::SseComplete(_) => "sse_complete",
            AggregatedResult::ProcessComplete(_) => "process_complete",
            AggregatedResult::RequestOnly { .. } => "request_only",
            AggregatedResult::ResponseOnly { .. } => "response_only",
            AggregatedResult::Http2Frames { .. } => "http2_frames",
            AggregatedResult::Http2StreamComplete(_) => "http2_stream_complete",
        }
    }
}


impl ToChromeTraceEvent for AggregatedResult {
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        match self {
            AggregatedResult::HttpComplete(pair) => pair.to_chrome_trace_events(),
            AggregatedResult::SseComplete(pair) => pair.to_chrome_trace_events(),
            AggregatedResult::ProcessComplete(process) => process.to_chrome_trace_events(),
            AggregatedResult::RequestOnly { .. } => {
                log::warn!("RequestOnly: {:?}", self);
                vec![]
            },
            AggregatedResult::ResponseOnly { .. } => {
                log::warn!("ResponseOnly: {:?}", self);
                vec![]
            },
            AggregatedResult::Http2Frames { frames, .. } => {
                frames.iter().flat_map(|f| f.to_chrome_trace_events()).collect()
            },
            AggregatedResult::Http2StreamComplete(stream) => {
                stream.to_chrome_trace_events()
            },
        }
    }
}
