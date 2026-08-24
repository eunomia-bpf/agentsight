// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agentsight_capture::{
    Event, MaterializedView,
    analyzers::{Analyzer, AnalyzerError},
    model::SessionRow,
    runners::{
        AgentRunner, EventStream, Runner, RunnerError,
        agent::AgentRunner as NestedAgentRunner,
        common::BinaryRunner as NestedBinaryRunner,
        process::ProcessRunner as NestedProcessRunner,
        system::{SystemConfig as NestedSystemConfig, SystemRunner as NestedSystemRunner},
    },
    sinks::sqlite::SqliteStore,
    sources::agent_native,
    view::SharedMaterializedView,
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
    async fn process(&mut self, events: EventStream) -> Result<EventStream, AnalyzerError> {
        Ok(events)
    }
}

#[tokio::test]
async fn legacy_capture_and_analysis_imports_still_compile_and_run() {
    let _: Option<NestedAgentRunner> = None;
    let _: Option<NestedBinaryRunner> = None;
    let _: Option<NestedProcessRunner> = None;
    let _: Option<NestedSystemConfig> = None;
    let _: Option<NestedSystemRunner> = None;

    let runner = InMemoryRunner {
        events: vec![Event::new_with_timestamp(
            1_000_000,
            "test".into(),
            42,
            "agent".into(),
            serde_json::json!({"type": "test"}),
        )],
    };
    let mut capture = AgentRunner::new()
        .add_runner(Box::new(runner))
        .add_global_analyzer(Box::new(PassthroughAnalyzer));

    let events: Vec<_> = capture.run().await.unwrap().collect().await;
    assert_eq!(events.len(), 1);

    let _: Option<MaterializedView> = None;
    let _: Option<SharedMaterializedView> = None;
    let _: Option<SessionRow> = None;
    let _: Option<SqliteStore> = None;
    let _ = agent_native::snapshot;
}
