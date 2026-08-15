// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
use async_trait::async_trait;
use futures::stream::Stream;
use std::pin::Pin;

pub type EventStream = Pin<Box<dyn Stream<Item = Event> + Send>>;
pub type RunnerError = Box<dyn std::error::Error + Send + Sync>;

#[async_trait]
pub trait Runner: Send + Sync {
    async fn run(&mut self) -> Result<EventStream, RunnerError>;

    fn add_analyzer(self, analyzer: Box<dyn crate::analyzers::Analyzer>) -> Self
    where
        Self: Sized;
}

pub mod agent;
pub mod common;
#[cfg(any(test, feature = "test-support"))]
pub mod fake;
pub mod process;

pub use agent::AgentRunner;
pub use common::BinaryRunner;
#[cfg(any(test, feature = "test-support"))]
pub use fake::FakeRunner;
pub use process::ProcessRunner;
