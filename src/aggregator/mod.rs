//! Aggregator module for correlating parsed messages
//!
//! This module provides aggregators for correlating HTTP requests/responses
//! and SSE events into complete flows.
//!
//! # Example
//! ```rust,ignore
//! use agentsight::aggregator::Aggregator;
//! use agentsight::parser::Parser;
//!
//! let mut parser = Parser::new();
//! let mut aggregator = Aggregator::new();
//!
//! for event in events {
//!     let result = parser.parse_event(&event);
//!     let aggregated = aggregator.process_result(result);
//!     // Handle aggregated results
//! }
//! ```

mod http;
mod http2;
mod proctrace;
mod result;
mod unified;

// Re-export unified aggregator
pub use unified::Aggregator;

// Re-export aggregated result
pub use result::AggregatedResult;

// Re-export HTTP types
pub use http::{
    HttpConnectionAggregator, ConnectionId, ConnectionState,
    HttpPair, ParsedRequest, AggregatedResponse,
};

// Re-export HTTP/2 types
pub use http2::{
    Http2StreamAggregator, Http2Stream, Http2StreamState, StreamId, StreamDirection,
};

// Re-export proctrace types
pub use proctrace::{ProcessEventAggregator, AggregatedProcess};
