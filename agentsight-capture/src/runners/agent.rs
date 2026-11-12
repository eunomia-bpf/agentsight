// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use async_trait::async_trait;
use futures::stream::select_all;

/// AgentRunner composes multiple runners into a single unified stream
/// with optional global analyzers applied to the merged stream.
#[derive(Default)]
pub struct AgentRunner {
    runners: Vec<Box<dyn Runner>>,
    analyzers: Vec<Box<dyn Analyzer>>,
}

impl AgentRunner {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_runner(mut self, runner: Box<dyn Runner>) -> Self {
        self.runners.push(runner);
        self
    }

    pub fn add_global_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }

    pub fn runner_count(&self) -> usize {
        self.runners.len()
    }

    pub fn analyzer_count(&self) -> usize {
        self.analyzers.len()
    }
}

#[async_trait]
impl Runner for AgentRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        if self.runners.is_empty() {
            return Err("No runners configured for AgentRunner".into());
        }

        let mut streams = Vec::new();
        for runner in &mut self.runners {
            streams.push(runner.run().await?);
        }
        let mut stream = Box::pin(select_all(streams)) as EventStream;
        for analyzer in &mut self.analyzers {
            stream = analyzer
                .process(stream)
                .await
                .map_err(|error| format!("Global analyzer error: {error}"))?;
        }
        Ok(stream)
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzers::AnalyzerError;
    use crate::event::Event;
    use futures::{StreamExt, stream};

    struct MemoryRunner(Vec<Event>);

    #[async_trait]
    impl Runner for MemoryRunner {
        async fn run(&mut self) -> Result<EventStream, RunnerError> {
            Ok(Box::pin(stream::iter(std::mem::take(&mut self.0))))
        }

        fn add_analyzer(self, _analyzer: Box<dyn Analyzer>) -> Self {
            self
        }
    }

    struct CountAnalyzer;

    #[async_trait]
    impl Analyzer for CountAnalyzer {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            Ok(Box::pin(stream.map(|mut event| {
                event.data["seen"] = serde_json::json!(true);
                event
            })))
        }
    }

    fn event(pid: u32) -> Event {
        Event::new_with_timestamp(1, "test".into(), pid, "agent".into(), serde_json::json!({}))
    }

    #[tokio::test]
    async fn merges_runners_and_applies_stable_analyzer_boundary() {
        let mut runner = AgentRunner::new()
            .add_runner(Box::new(MemoryRunner(vec![event(1)])))
            .add_runner(Box::new(MemoryRunner(vec![event(2)])))
            .add_global_analyzer(Box::new(CountAnalyzer));

        let events: Vec<_> = runner.run().await.unwrap().collect().await;
        assert_eq!(events.len(), 2);
        assert!(events.iter().all(|event| event.data["seen"] == true));
    }

    #[tokio::test]
    async fn rejects_empty_runner_set_and_propagates_runner_errors() {
        assert!(AgentRunner::new().run().await.is_err());

        struct Failing;
        #[async_trait]
        impl Runner for Failing {
            async fn run(&mut self) -> Result<EventStream, RunnerError> {
                Err("runner failed".into())
            }
            fn add_analyzer(self, _analyzer: Box<dyn Analyzer>) -> Self { self }
        }
        assert!(AgentRunner::new().add_runner(Box::new(Failing)).run().await.is_err());
    }
}
