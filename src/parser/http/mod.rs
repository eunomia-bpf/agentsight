//! HTTP Parser module
//!
//! This module provides HTTP request/response parsing functionality.
//! Stateless HTTP parser that parses SslEvent into ParsedRequest/ParsedResponse.

mod parser;
mod request;
mod response;

// Re-export types
pub use parser::{HttpParser, ParsedHttpMessage};
pub use request::ParsedRequest;
pub use response::ParsedResponse;
