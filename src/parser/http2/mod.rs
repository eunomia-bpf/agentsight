//! HTTP/2 parser module
//!
//! Provides HTTP/2 binary frame parsing for passively captured SSL traffic.

mod frame;
mod parser;

pub use frame::{Http2FrameType, ParsedHttp2Frame};
pub use parser::Http2Parser;
