// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common::{AnalyzerProcessor, BinaryExecutor};
use super::{EventStream, Runner, RunnerError, StdioConfig};
use crate::framework::analyzers::Analyzer;
use crate::framework::core::Event;
use async_trait::async_trait;
use futures::stream::StreamExt;
use std::path::Path;

/// Runner for collecting stdio payload events
pub struct StdioRunner {
    config: StdioConfig,
    analyzers: Vec<Box<dyn Analyzer>>,
    executor: BinaryExecutor,
    additional_args: Vec<String>,
}

impl StdioRunner {
    /// Create from binary extractor (real execution mode)
    pub fn from_binary_extractor(binary_path: impl AsRef<Path>) -> Self {
        let path_str = binary_path.as_ref().to_string_lossy().to_string();
        Self {
            config: StdioConfig::default(),
            analyzers: Vec::new(),
            executor: BinaryExecutor::new(path_str).with_runner_name("Stdio".to_string()),
            additional_args: Vec::new(),
        }
    }

    /// Add additional command-line arguments to pass to the binary
    pub fn with_args<I, S>(mut self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        self.additional_args = args.into_iter().map(|s| s.as_ref().to_string()).collect();
        self.executor = self
            .executor
            .with_args(&self.additional_args)
            .with_runner_name("Stdio".to_string());
        self
    }

    /// Set the PID to monitor
    #[allow(dead_code)]
    pub fn pid(mut self, pid: u32) -> Self {
        self.config.pid = Some(pid);
        self
    }

    /// Set the UID to monitor
    #[allow(dead_code)]
    pub fn uid(mut self, uid: u32) -> Self {
        self.config.uid = Some(uid);
        self
    }

    /// Capture all file descriptors instead of only 0/1/2
    #[allow(dead_code)]
    pub fn all_fds(mut self, enabled: bool) -> Self {
        self.config.all_fds = enabled;
        self
    }

    /// Limit captured payload bytes per event
    #[allow(dead_code)]
    pub fn max_bytes(mut self, max_bytes: u32) -> Self {
        self.config.max_bytes = Some(max_bytes);
        self
    }
}

#[async_trait]
impl Runner for StdioRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let json_stream = self.executor.get_json_stream().await?;

        let event_stream = json_stream.map(|json_value| {
            let timestamp = json_value
                .get("timestamp_ns")
                .and_then(|v| v.as_u64())
                .unwrap_or_else(|| {
                    panic!("Missing timestamp_ns field in stdio event: {}", json_value);
                });

            let pid = json_value
                .get("pid")
                .and_then(|v| v.as_u64())
                .map(|p| p as u32)
                .unwrap_or_else(|| {
                    panic!("Missing pid field in stdio event: {}", json_value);
                });

            let comm = json_value
                .get("comm")
                .and_then(|v| v.as_str())
                .unwrap_or_else(|| {
                    panic!("Missing comm field in stdio event: {}", json_value);
                })
                .to_string();

            Event::new_with_timestamp(timestamp, "stdio".to_string(), pid, comm, json_value)
        });

        AnalyzerProcessor::process_through_analyzers(Box::pin(event_stream), &mut self.analyzers)
            .await
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }

    fn name(&self) -> &str {
        "stdio"
    }

    fn id(&self) -> String {
        "stdio".to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stdio_runner_creation() {
        let runner = StdioRunner::from_binary_extractor("/fake/path/stdiocap");
        assert_eq!(runner.name(), "stdio");
        assert_eq!(runner.id(), "stdio");
        assert_eq!(runner.config.pid, None);
        assert_eq!(runner.config.uid, None);
        assert!(!runner.config.all_fds);
        assert_eq!(runner.config.max_bytes, None);
    }

    #[test]
    fn test_stdio_runner_with_custom_config() {
        let runner = StdioRunner::from_binary_extractor("/fake/path/stdiocap")
            .pid(1234)
            .uid(1000)
            .all_fds(true)
            .max_bytes(4096);

        assert_eq!(runner.config.pid, Some(1234));
        assert_eq!(runner.config.uid, Some(1000));
        assert!(runner.config.all_fds);
        assert_eq!(runner.config.max_bytes, Some(4096));
    }
}
