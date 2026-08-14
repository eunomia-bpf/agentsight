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

    /// Restrict the eBPF process probe to a cgroup. `children` additionally
    /// keeps descendants of matched tasks that left the cgroup. Both flags are
    /// parsed by the `process` binary itself; this is the only Rust-side path
    /// that reaches them.
    pub fn with_cgroup_filter(mut self, cgroup_path: Option<&str>, children: bool) -> Self {
        let Some(cgroup_path) = cgroup_path.filter(|path| !path.trim().is_empty()) else {
            return self;
        };
        self.args.push("--cgroup-filter".to_string());
        self.args.push(cgroup_path.to_string());
        if children {
            self.args.push("--cgroup-filter-children".to_string());
        }
        self.executor.set_args(&self.args);
        self
    }

    /// Arguments handed to the `process` binary, in order.
    pub fn args(&self) -> &[String] {
        &self.args
    }

    fn parse_process_event(json_value: serde_json::Value, errors: &AtomicU64) -> Event {
        if json_value.get("event").and_then(|v| v.as_str()) == Some("CLOCK_SYNC") {
            return Event::new_with_timestamp(
                current_boot_time_ns(),
                "diagnostic".to_string(),
                0,
                "process".to_string(),
                json_value,
            );
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
    fn cgroup_filter_appends_both_flags_after_existing_args() {
        let runner = ProcessRunner::from_binary_extractor("/tmp/process")
            .with_args(["-p", "42"])
            .with_cgroup_filter(Some("/sys/fs/cgroup/aro/cell-1"), true);
        assert_eq!(
            runner.args(),
            [
                "-p",
                "42",
                "--cgroup-filter",
                "/sys/fs/cgroup/aro/cell-1",
                "--cgroup-filter-children"
            ]
        );
    }

    #[test]
    fn cgroup_filter_without_children_omits_the_children_flag() {
        let runner = ProcessRunner::from_binary_extractor("/tmp/process")
            .with_cgroup_filter(Some("/sys/fs/cgroup/aro/cell-1"), false);
        assert_eq!(
            runner.args(),
            ["--cgroup-filter", "/sys/fs/cgroup/aro/cell-1"]
        );
    }

    #[test]
    fn missing_or_blank_cgroup_path_adds_nothing() {
        assert!(
            ProcessRunner::from_binary_extractor("/tmp/process")
                .with_cgroup_filter(None, true)
                .args()
                .is_empty()
        );
        assert!(
            ProcessRunner::from_binary_extractor("/tmp/process")
                .with_cgroup_filter(Some("  "), true)
                .args()
                .is_empty()
        );
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
