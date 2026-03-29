//! Parse result types
//
//! This module defines the `ParsedMessage` and `ParseResult` types
//! representing the output from parsing events.

use crate::parser::http::{ParsedRequest, ParsedResponse};
use crate::parser::sse::ParsedSseEvent;
use crate::parser::proctrace::ParsedProcEvent;

/// Parsed message from events
#[derive(Debug, Clone)]
pub enum ParsedMessage {
    /// HTTP Request
    Request(ParsedRequest),
    /// HTTP Response
    Response(ParsedResponse),
    /// SSE Event
    SseEvent(ParsedSseEvent),
    /// Process Event
    ProcEvent(ParsedProcEvent),
}

impl ParsedMessage {
    /// Get the message type name for logging/debugging
    pub fn message_type(&self) -> &'static str {
        match self {
            ParsedMessage::Request(_) => "Request",
            ParsedMessage::Response(_) => "Response",
            ParsedMessage::SseEvent(_) => "SseEvent",
            ParsedMessage::ProcEvent(_) => "ProcEvent",
        }
    }
}

/// Parse result
#[derive(Debug)]
pub struct ParseResult {
    /// Parsed messages (may be empty if data is incomplete)
    pub messages: Vec<ParsedMessage>,
}
