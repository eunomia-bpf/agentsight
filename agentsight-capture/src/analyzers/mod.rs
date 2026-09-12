// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::runners::EventStream;
use async_trait::async_trait;

/// Type alias for errors that can be sent between threads.
pub type AnalyzerError = Box<dyn std::error::Error + Send + Sync>;

/// Stable processing boundary between native capture and extensions.
#[async_trait]
pub trait Analyzer: Send + Sync {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError>;
}
