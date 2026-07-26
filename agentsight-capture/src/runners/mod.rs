// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
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
    fn add_analyzer(self, analyzer: Box<dyn crate::analyzers::Analyzer>) -> Self
    where
        Self: Sized;
}

pub mod agent;
pub mod common;
#[cfg(test)]
pub mod fake;
pub mod process;
pub mod system;

pub use agent::AgentRunner;
pub use common::BinaryRunner;
#[cfg(test)]
pub use fake::FakeRunner;
pub use process::ProcessRunner;
pub use system::SystemRunner;
