// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common::{AnalyzerProcessor, BinaryExecutor, current_boot_time_ns, parse_json_event};
use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use crate::sources::proc::{PidSeed, kernel_starttime_ticks};
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::Value;
use std::path::Path;
use std::sync::{Arc, atomic::AtomicU64};

/// Reads a task's kernel start ticks by pid. A function pointer rather than a
/// trait object because the reader has to be `Copy` to live in the stream
/// closure, and there are only ever two: procfs, and a test double for the
/// platforms that have no procfs to read.
pub type StartTicksReader = fn(u32) -> Option<u64>;

pub struct ProcessRunner {
    analyzers: Vec<Box<dyn Analyzer>>,
    executor: BinaryExecutor,
    args: Vec<String>,
    start_ticks: StartTicksReader,
}

impl ProcessRunner {
    pub fn from_binary_extractor(binary_path: impl AsRef<Path>) -> Self {
        Self {
            analyzers: Vec::new(),
            executor: BinaryExecutor::new(binary_path.as_ref().to_string_lossy().into_owned())
                .with_runner_name("Process".to_string()),
            args: Vec::new(),
            start_ticks: kernel_starttime_ticks,
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

    /// Replace the start-ticks reader. Only tests use it: procfs exists on the
    /// platform this runner captures on, and nowhere else.
    #[cfg(test)]
    fn with_start_ticks_reader(mut self, reader: StartTicksReader) -> Self {
        self.start_ticks = reader;
        self
    }

    fn parse_process_event(
        json_value: serde_json::Value,
        errors: &AtomicU64,
        start_ticks: StartTicksReader,
    ) -> Event {
        if json_value.get("event").and_then(|v| v.as_str()) == Some("CLOCK_SYNC") {
            return Event::new_with_timestamp(
                current_boot_time_ns(),
                "diagnostic".to_string(),
                0,
                "process".to_string(),
                json_value,
            );
        }
        let mut event = parse_json_event("process", "timestamp", json_value, errors);
        attach_start_ticks(&mut event, start_ticks);
        event
    }
}

/// Stamp an exec event with the kernel start ticks of the task it reports.
///
/// Read here, at arrival, because this is the last moment the task is likely to
/// still exist: `/proc/<pid>/stat` goes away when it exits, and a later reader
/// would either miss it or read a reused pid's ticks. Together with the pid this
/// is the identity a bridge consumer correlates on.
///
/// A failed read — no procfs, or the task already gone — leaves the field
/// absent. It is never filled from the event timestamp: that number would be the
/// collector's arithmetic, not the kernel's identity, and the two are not
/// interchangeable for reuse detection.
fn attach_start_ticks(event: &mut Event, start_ticks: StartTicksReader) {
    if event.data.get("event").and_then(Value::as_str) != Some("EXEC") {
        return;
    }
    let Some(ticks) = start_ticks(event.pid) else {
        return;
    };
    if let Some(fields) = event.data.as_object_mut() {
        fields.insert("start_ticks".to_string(), Value::from(ticks));
    }
}

#[async_trait]
impl Runner for ProcessRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let json_stream = self.executor.get_json_stream().await?;
        let errors = Arc::new(AtomicU64::new(0));
        let start_ticks = self.start_ticks;
        let stream = json_stream.map(move |v| Self::parse_process_event(v, &errors, start_ticks));
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
    use serde_json::json;

    fn ticks_for_4310(pid: u32) -> Option<u64> {
        (pid == 4310).then_some(918_500)
    }

    fn no_ticks(_pid: u32) -> Option<u64> {
        None
    }

    fn exec_event() -> Value {
        json!({
            "event": "EXEC",
            "timestamp": 1_760_000_003_000u64,
            "pid": 4310,
            "ppid": 4242,
            "comm": "bash",
            "filename": "/bin/bash",
        })
    }

    fn parse(raw: Value, reader: StartTicksReader) -> Event {
        let errors = AtomicU64::new(0);
        ProcessRunner::parse_process_event(raw, &errors, reader)
    }

    #[test]
    fn an_exec_event_carries_the_ticks_read_at_arrival() {
        let event = parse(exec_event(), ticks_for_4310);
        assert_eq!(event.data.get("start_ticks"), Some(&json!(918_500)));
    }

    #[test]
    fn a_reader_that_finds_nothing_leaves_the_field_absent() {
        let event = parse(exec_event(), no_ticks);
        assert!(event.data.get("start_ticks").is_none());
    }

    #[test]
    fn only_exec_events_are_stamped() {
        let mut exit = exec_event();
        exit["event"] = json!("EXIT");
        let event = parse(exit, ticks_for_4310);
        assert!(event.data.get("start_ticks").is_none());

        let sync = parse(json!({ "event": "CLOCK_SYNC" }), ticks_for_4310);
        assert!(sync.data.get("start_ticks").is_none());
    }

    #[test]
    fn the_reader_is_asked_about_the_pid_the_event_reports() {
        fn echo_pid(pid: u32) -> Option<u64> {
            Some(u64::from(pid))
        }
        let event = parse(exec_event(), echo_pid);
        assert_eq!(event.data.get("start_ticks"), Some(&json!(4310)));
    }

    #[test]
    fn the_reader_a_runner_carries_is_the_one_its_stream_uses() {
        let runner = ProcessRunner::from_binary_extractor("/tmp/process")
            .with_start_ticks_reader(ticks_for_4310);
        let errors = AtomicU64::new(0);
        let event = ProcessRunner::parse_process_event(exec_event(), &errors, runner.start_ticks);
        assert_eq!(event.data.get("start_ticks"), Some(&json!(918_500)));
    }

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
