//! Parser module for protocol parsing
//!
//! This module provides parsers for various protocols including HTTP and SSE.
//!
//! # Quick Start
//! ```rust,ignore
//! use agentsight::parser::{HttpParser, SseParser, ParsedHttpMessage};
//! use agentsight::aggregator::HttpConnectionAggregator;
//!
//! let http_parser = HttpParser::new();
//! let sse_parser = SseParser::new();
//! let mut aggregator = HttpConnectionAggregator::new();
//!
//! // Parse and aggregate
//! for ssl_event in ssl_events {
//!     if let Some(msg) = http_parser.parse(rc_event.clone()) {
//!         // Handle HTTP message
//!     } else {
//!         let sse_events = sse_parser.parse(rc_event);
//!         // Handle SSE events
//!     }
//! }
//! ```
//!
//! For a unified interface, use `Parser`:
//! ```rust,ignore
//! use agentsight::parser::Parser;
//!
//! let mut parser = Parser::new();
//! let result = parser.parse_ssl_event(&ssl_event);
//! ```

pub mod http;
pub mod http2;
pub mod sse;
pub mod proctrace;
mod result;
mod unified;

// Re-export result types
pub use result::{ParsedMessage, ParseResult};

// Re-export unified parser
pub use unified::Parser;

// Re-export HTTP types
pub use http::{HttpParser, ParsedHttpMessage, ParsedRequest, ParsedResponse};

// Re-export SSE types
pub use sse::{SseParser, ParsedSseEvent};

// Re-export proctrace types
pub use proctrace::{ProcTraceParser, ParsedProcEvent, ProcEventType};

// Re-export HTTP/2 types
pub use http2::{Http2Parser, Http2FrameType, ParsedHttp2Frame};
