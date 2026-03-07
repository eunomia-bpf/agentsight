// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common::{AnalyzerProcessor, BinaryExecutor};
use super::{EventStream, Runner, RunnerError, StdioConfig};
use crate::framework::analyzers::Analyzer;
use crate::framework::core::Event;
use async_trait::async_trait;
use futures::future;
use futures::stream::StreamExt;
use std::path::Path;

/// Runner for collecting stdio payload events
pub struct StdioRunner {
    config: StdioConfig,
    analyzers: Vec<Box<dyn Analyzer>>,
    binary_path: String,
    additional_args: Vec<String>,
}

impl StdioRunner {
    /// Create from binary extractor (real execution mode)
    pub fn from_binary_extractor(binary_path: impl AsRef<Path>) -> Self {
        let path_str = binary_path.as_ref().to_string_lossy().to_string();
        Self {
            config: StdioConfig::default(),
            analyzers: Vec::new(),
            binary_path: path_str,
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

    fn build_args(&self) -> Vec<String> {
        let mut args = Vec::new();

        if let Some(pid) = self.config.pid {
            args.extend(["-p".to_string(), pid.to_string()]);
        }
        if let Some(uid) = self.config.uid {
            args.extend(["-u".to_string(), uid.to_string()]);
        }
        if self.config.all_fds {
            args.push("--all-fds".to_string());
        }
        if let Some(max_bytes) = self.config.max_bytes {
            args.extend(["--max-bytes".to_string(), max_bytes.to_string()]);
        }

        args.extend(self.additional_args.iter().cloned());
        args
    }

    fn parse_stdio_event(json_value: serde_json::Value) -> Option<Event> {
        let timestamp = match json_value.get("timestamp_ns").and_then(|v| v.as_u64()) {
            Some(value) => value,
            None => {
                log::warn!("Skipping stdio event without timestamp_ns: {}", json_value);
                return None;
            }
        };

        let pid = match json_value.get("pid").and_then(|v| v.as_u64()) {
            Some(value) => value as u32,
            None => {
                log::warn!("Skipping stdio event without pid: {}", json_value);
                return None;
            }
        };

        let comm = match json_value.get("comm").and_then(|v| v.as_str()) {
            Some(value) => value.to_string(),
            None => {
                log::warn!("Skipping stdio event without comm: {}", json_value);
                return None;
            }
        };

        Some(Event::new_with_timestamp(
            timestamp,
            "stdio".to_string(),
            pid,
            comm,
            json_value,
        ))
    }
}

#[async_trait]
impl Runner for StdioRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let args = self.build_args();
        let executor = BinaryExecutor::new(self.binary_path.clone())
            .with_args(&args)
            .with_runner_name("Stdio".to_string());
        let json_stream = executor.get_json_stream().await?;

        let event_stream = json_stream.filter_map(|json_value| {
            future::ready(Self::parse_stdio_event(json_value))
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

    #[test]
    fn test_stdio_runner_build_args_from_config() {
        let runner = StdioRunner::from_binary_extractor("/fake/path/stdiocap")
            .pid(4321)
            .uid(1001)
            .all_fds(true)
            .max_bytes(2048)
            .with_args(["--verbose"]);

        assert_eq!(
            runner.build_args(),
            vec![
                "-p".to_string(),
                "4321".to_string(),
                "-u".to_string(),
                "1001".to_string(),
                "--all-fds".to_string(),
                "--max-bytes".to_string(),
                "2048".to_string(),
                "--verbose".to_string(),
            ]
        );
    }

    #[test]
    fn test_stdio_runner_skips_invalid_events() {
        let invalid = serde_json::json!({
            "timestamp_ns": 1,
            "pid": 1234
        });

        assert!(StdioRunner::parse_stdio_event(invalid).is_none());
    }

    #[test]
    fn test_stdio_runner_parses_valid_event() {
        let valid = serde_json::json!({
            "timestamp_ns": 1,
            "pid": 1234,
            "comm": "python3",
            "data": "hello"
        });

        let event = StdioRunner::parse_stdio_event(valid).expect("valid stdio event");
        assert_eq!(event.source, "stdio");
        assert_eq!(event.pid, 1234);
        assert_eq!(event.comm, "python3");
        assert_eq!(event.timestamp, 1);
    }
}
