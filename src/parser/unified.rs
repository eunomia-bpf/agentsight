//! Unified Parser - high-level entry point for protocol parsing
//
//! This module provides a unified interface for parsing SSL events and process events.
//! It combines HTTP Parser, SSE Parser, and ProcTrace Parser, but does NOT include aggregation logic.
//
//! For aggregation, use:
//! - `HttpConnectionAggregator` for HTTP/SSE events
//! - `ProcessEventAggregator` for process events

use super::{ParseResult, ParsedMessage};
use crate::event::Event;
use crate::parser::http::{HttpParser, ParsedHttpMessage};
use crate::parser::http2::Http2Parser;
use crate::parser::proctrace::ProcTraceParser;
use crate::parser::sse::SseParser;
use crate::probes::proctrace::VariableEvent;
use crate::probes::sslsniff::SslEvent;
use std::rc::Rc;

/// Unified parser for SSL and process events
///
/// This parser provides a unified entry point for parsing but does NOT
/// aggregate or correlate messages. Use aggregators for that.
pub struct Parser {
    http_parser: HttpParser,
    http2_parser: Http2Parser,
    sse_parser: SseParser,
}

impl Default for Parser {
    fn default() -> Self {
        Self::new()
    }
}

impl Parser {
    /// Create new parser
    pub fn new() -> Self {
        Parser {
            http_parser: HttpParser::new(),
            http2_parser: Http2Parser::new(),
            sse_parser: SseParser::new(),
        }
    }

    /// Parse SSL event into messages
    //
    /// Returns parsed HTTP Request/Response or SSE Events.
    /// Does NOT aggregate or correlate - use `HttpConnectionAggregator` for that.
    pub fn parse_ssl_event(&self, ssl_event: Rc<SslEvent>) -> ParseResult {
        log::debug!("parse_ssl_event: length={}", ssl_event.buf_size());

        // 1. HTTP/1.x detection (text-based protocols)
        if ssl_event.is_http() {
            match self.http_parser.parse(ssl_event.clone()) {
                Ok(msg) => {
                    let message = match msg {
                        ParsedHttpMessage::Request(req) => ParsedMessage::Request(req),
                        ParsedHttpMessage::Response(resp) => ParsedMessage::Response(resp),
                    };
                    return ParseResult {
                        messages: vec![message],
                    };
                }
                Err(e) => {
                    log::debug!("Failed to parse HTTP/1.x event: {e}");
                }
            }
        }

        // 2. HTTP/2 detection (binary frame protocol)
        if ssl_event.is_http2() {
            let frames = self.http2_parser.parse(ssl_event.clone());
            if !frames.is_empty() {
                return ParseResult {
                    messages: vec![ParsedMessage::Http2Frames(frames)],
                };
            }
        }

        // 3. Fallback: SSE data
        let sse_events = self.sse_parser.parse(ssl_event.clone());
        let messages = sse_events
            .into_iter()
            .map(ParsedMessage::SseEvent)
            .collect();
        ParseResult { messages }
    }

    /// Parse process event into messages
    ///
    /// Returns parsed process event (Exec/Stdout/Exit).
    /// Does NOT aggregate - use `ProcessEventAggregator` for that.
    pub fn parse_proc_event(&self, event: &VariableEvent) -> ParseResult {
        match ProcTraceParser::parse_variable(event) {
            Some(parsed) => ParseResult {
                messages: vec![ParsedMessage::ProcEvent(parsed)],
            },
            None => ParseResult {
                messages: Vec::new(),
            },
        }
    }

    /// Parse unified Event
    pub fn parse_event(&self, event: Event) -> ParseResult {
        log::debug!("Parsing event({:?})", event.event_type());
        match event {
            Event::Ssl(ssl_event) => self.parse_ssl_event(Rc::new(ssl_event)),
            Event::Proc(proc_event) => self.parse_proc_event(&proc_event),
            Event::ProcMon(_) => ParseResult { messages: Vec::new() },
        }
    }

    /// Get reference to HTTP parser
    pub fn http_parser(&self) -> &HttpParser {
        &self.http_parser
    }

    /// Get reference to SSE parser
    pub fn sse_parser(&self) -> &SseParser {
        &self.sse_parser
    }

    /// Get reference to HTTP/2 parser
    pub fn http2_parser(&self) -> &Http2Parser {
        &self.http2_parser
    }
}
