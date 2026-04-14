//! HTTP aggregation module
//
//! Provides aggregators for HTTP requests/responses.

mod aggregator;
mod pair;
mod response;

// Re-export main types
pub use aggregator::{HttpConnectionAggregator, ConnectionId, ConnectionState};
pub use pair::HttpPair;
pub use response::AggregatedResponse;

// Re-export ParsedRequest from parser (replaces AggregatedRequest)
pub use crate::parser::http::ParsedRequest;
