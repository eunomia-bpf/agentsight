// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::runners::EventStream;
use async_trait::async_trait;

/// Type alias for errors that can be sent between threads
pub type AnalyzerError = Box<dyn std::error::Error + Send + Sync>;

/// Base trait for all analyzers that process event streams
#[async_trait]
pub trait Analyzer: Send + Sync {
    /// Process an event stream and return a processed stream
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError>;
}

pub mod auth_header_remover;
pub mod common;
mod filter_base;
mod filter_metrics;
pub mod http_decompressor;
pub mod http_filter;
pub mod http_parser;
pub mod materializing;
mod protocol_events;
pub mod sse_processor;
pub mod ssl_filter;
pub mod timestamp_normalizer;

#[cfg(test)]
mod sse_processor_tests;

pub use auth_header_remover::AuthHeaderRemover;
pub use http_decompressor::HTTPDecompressor;
pub use http_filter::{HTTPFilter, print_global_http_filter_metrics};
pub use http_parser::HTTPParser;
pub use materializing::MaterializingAnalyzer;
pub use sse_processor::SSEProcessor;
pub use ssl_filter::{SSLFilter, print_global_ssl_filter_metrics};
pub use timestamp_normalizer::TimestampNormalizer;

#[cfg(test)]
#[path = "mod_tests.rs"]
mod comprehensive_analyzer_chain_tests;
