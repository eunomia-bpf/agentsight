// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::core::Event;
use async_trait::async_trait;
use futures::stream::Stream;
use std::pin::Pin;

/// Type alias for event streams
pub type EventStream = Pin<Box<dyn Stream<Item = Event> + Send>>;

/// Type alias for errors that can be sent between threads
pub type RunnerError = Box<dyn std::error::Error + Send + Sync>;

/// Base trait for all runners that collect observability data
#[async_trait]
pub trait Runner: Send + Sync {
    /// Run the data collection and return a stream of events
    async fn run(&mut self) -> Result<EventStream, RunnerError>;
    
    /// Add an analyzer to this runner's processing chain
    fn add_analyzer(self, analyzer: Box<dyn crate::framework::analyzers::Analyzer>) -> Self
    where
        Self: Sized;
    
    /// Get the name of this runner
    #[allow(dead_code)]
    fn name(&self) -> &str;
    
    /// Get a unique identifier for this runner instance
    #[allow(dead_code)]
    fn id(&self) -> String;
}

/// Configuration for SSL/TLS monitoring (only exercised by builder/tests).
#[cfg(test)]
#[derive(Debug, Clone, Default)]
pub struct SslConfig {
    pub tls_version: Option<String>,
}

/// Configuration for process monitoring (only exercised by builder/tests).
#[cfg(test)]
#[derive(Debug, Clone, Default)]
pub struct ProcessConfig {
    pub pid: Option<u32>,
}


/// Configuration for stdio payload monitoring
#[derive(Debug, Clone, Default)]
pub struct StdioConfig {
    pub pid: Option<u32>,
    pub uid: Option<u32>,
    pub all_fds: bool,
    pub max_bytes: Option<u32>,
}


pub mod common;
pub mod ssl;
pub mod process;
#[cfg(test)]
pub mod fake; // Test-only fake runner (compiled only for tests)
pub mod agent; // Add agent runner for flexible composition
pub mod stdio;
pub mod system; // Add system runner for CPU and memory monitoring

pub use ssl::SslRunner;
pub use stdio::StdioRunner;
pub use process::ProcessRunner;
#[cfg(test)]
pub use fake::FakeRunner; // Export FakeRunner (tests only)
pub use agent::AgentRunner; // Export AgentRunner
pub use system::SystemRunner; // Export SystemRunner
