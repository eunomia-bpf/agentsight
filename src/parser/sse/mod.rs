//! SSE (Server-Sent Events) Parser module
//!
//! This module provides functionality for parsing SSE (Server-Sent Events) streams.
//! Includes both legacy API and new zero-copy API.
//!
//! For SSE aggregation, use `agentsight::aggregator::SseEventAggregator`.
//!
//! # Example (New API)
//! ```rust,ignore
//! use agentsight::parser::sse::{SseParser, ParsedSseEvent};
//! use std::rc::Rc;
//!
//! let parser = SseParser::new();
//! for event in ssl_events {
//!     let sse_events = parser.parse(Rc::new(event));
//!     for evt in sse_events {
//!         println!("SSE: id={:?}, data={}", evt.id, String::from_utf8_lossy(evt.data()));
//!     }
//! }
//! ```

mod event;
pub(crate) mod parser;

// Re-export new API (Spec compliant)
pub use event::ParsedSseEvent;
pub use parser::SseParser;

// Re-export legacy event types (for backward compatibility)
pub use event::{SSEEvent, SSEEvents};
