// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

pub mod adapters;
pub mod analyzers;
pub mod binary_extractor;
pub mod capture;
pub mod core;
pub mod runners;
pub mod semantic;
pub mod storage;

// Re-export commonly used types for convenience
// Note: These may show as unused in main.rs but they're exported for external use
#[allow(unused_imports)]
pub use analyzers::{Analyzer, OutputAnalyzer};
#[allow(unused_imports)]
pub use binary_extractor::BinaryExtractor;
#[allow(unused_imports)]
pub use core::Event;
#[cfg(test)]
#[allow(unused_imports)]
pub use runners::FakeRunner;
#[allow(unused_imports)]
pub use runners::{EventStream, ProcessRunner, Runner, RunnerError, SslRunner, StdioRunner};
