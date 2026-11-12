// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common::{AnalyzerProcessor, BinaryExecutor, current_boot_time_ns, parse_json_event};
use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use crate::sources::proc::PidSeed;
use async_trait::async_trait;
use futures::stream::StreamExt;
use std::path::Path;
use std::sync::{Arc, atomic::AtomicU64};

pub struct ProcessRunner {
    analyzers: Vec<Box<dyn Analyzer>>,
    executor: BinaryExecutor,
    args: Vec<String>,
}

impl ProcessRunner {
    pub fn from_binary_extractor(binary_path: impl AsRef<Path>) -> Self {
        Self {
            analyzers: Vec::new(),
            executor: BinaryExecutor::new(binary_path.as_ref().to_string_lossy().into_owned())
                .with_runner_name("Process".to_string()),
            args: Vec::new(),
        }
    }

    pub fn with_args<I, S>(mut self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        self.args = args.into_iter().map(|s| s.as_ref().to_string()).collect();
        self.executor.set_args(&self.args);
        self
    }

    pub fn with_seed_pids(mut self, seeds: &[PidSeed]) -> Self {
        for seed in seeds {
            self.args.push("--seed-pid".to_string());
            self.args.push(seed.arg_value());
        }
        self.executor.set_args(&self.args);
        self
    }

    fn parse_process_event(mut json_value: serde_json::Value, errors: &AtomicU64) -> Event {
        if json_value.get("event").and_then(|v| v.as_str()) == Some("CLOCK_SYNC") {
            return Event::new_with_timestamp(
                current_boot_time_ns(),
                "diagnostic".to_string(),
                0,
                "process".to_string(),
                json_value,
            );
        }
        if json_value.get("event").and_then(|v| v.as_str()) == Some("PROBE_LIVENESS") {
            // Older bundled probes emitted liveness without process identity.
            if let Some(record) = json_value.as_object_mut() {
                record.entry("pid").or_insert(serde_json::json!(0));
                record.entry("comm").or_insert(serde_json::json!("process"));
            }
        }
        parse_json_event("process", "timestamp", json_value, errors)
    }
}

#[async_trait]
impl Runner for ProcessRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let json_stream = self.executor.get_json_stream().await?;
        let errors = Arc::new(AtomicU64::new(0));
        let stream = json_stream.map(move |v| Self::parse_process_event(v, &errors));
        AnalyzerProcessor::process_through_analyzers(Box::pin(stream), &mut self.analyzers).await
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn liveness_is_a_process_event_without_parse_errors() {
        let errors = AtomicU64::new(0);
        for kind in ["start", "alive"] {
            let raw = serde_json::json!({
                "event": "PROBE_LIVENESS", "kind": kind,
                "timestamp": 25741617824027_u64, "every": 2,
                "wall_time_ns": 1791244800000000000_u64,
            });
            let event = ProcessRunner::parse_process_event(raw.clone(), &errors);
            assert_eq!(event.source, "process");
            assert_eq!(event.pid, 0);
            assert_eq!(event.comm, "process");
            assert_eq!(event.timestamp, raw["timestamp"].as_u64().unwrap());
            assert_eq!(event.data["event"], "PROBE_LIVENESS");
            assert_eq!(event.data["kind"], kind);
            assert_eq!(event.data["wall_time_ns"], raw["wall_time_ns"]);
        }
        assert_eq!(errors.load(std::sync::atomic::Ordering::Relaxed), 0);
        let invalid = ProcessRunner::parse_process_event(
            serde_json::json!({"event": "FILE_OPEN", "timestamp": 1}),
            &errors,
        );
        assert_eq!(invalid.data["reason"], "missing pid");
        assert_eq!(invalid.data["parse_error_count"], 1);
    }

    #[tokio::test]
    #[ignore = "requires real binary and sudo"]
    async fn test_process_runner_with_real_binary() {
        use tokio::time::timeout;
        let binary_path = "../src/process";
        if !Path::new(binary_path).exists() {
            return;
        }
        let mut runner = ProcessRunner::from_binary_extractor(binary_path);
        if let Ok(mut stream) = runner.run().await {
            let _ = timeout(std::time::Duration::from_secs(30), async {
                while futures::StreamExt::next(&mut stream).await.is_some() {}
            })
            .await;
        }
    }
}
