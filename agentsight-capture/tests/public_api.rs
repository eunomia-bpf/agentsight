// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agentsight_capture_core::{
    Event,
    analyzers::{Analyzer, AnalyzerError},
    runners::{AgentRunner, EventStream, Runner, RunnerError},
};
use async_trait::async_trait;
use futures::{StreamExt, stream};

struct InMemoryRunner {
    events: Vec<Event>,
}

#[async_trait]
impl Runner for InMemoryRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        Ok(Box::pin(stream::iter(std::mem::take(&mut self.events))))
    }

    fn add_analyzer(self, _analyzer: Box<dyn Analyzer>) -> Self {
        self
    }
}

struct PassthroughAnalyzer;

#[async_trait]
impl Analyzer for PassthroughAnalyzer {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        Ok(stream)
    }
}

#[tokio::test]
async fn downstream_crate_can_build_and_run_capture_pipeline() {
    let runner = InMemoryRunner {
        events: vec![Event::new_with_timestamp(
            1_000_000,
            "test".to_string(),
            42,
            "agent".to_string(),
            serde_json::json!({"type": "test"}),
        )],
    };
    let mut capture = AgentRunner::new()
        .add_runner(Box::new(runner))
        .add_global_analyzer(Box::new(PassthroughAnalyzer));

    let events: Vec<_> = capture.run().await.unwrap().collect().await;

    assert_eq!(events.len(), 1);
    assert_eq!(events[0].source, "test");
    assert_eq!(events[0].pid, 42);
}
