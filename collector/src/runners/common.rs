// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use async_trait::async_trait;
use futures::stream::{Stream, StreamExt};
use log::debug;
use std::path::Path;
use std::pin::Pin;
use std::process::Stdio;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command as TokioCommand;

/// Type alias for JSON stream
pub type JsonStream = Pin<Box<dyn Stream<Item = serde_json::Value> + Send>>;
const RUNNER_ERROR_TYPE: &str = "runner_error";

fn preview_line(line: &str, max_chars: usize) -> String {
    let mut chars = line.chars();
    let preview: String = chars.by_ref().take(max_chars).collect();
    if chars.next().is_some() {
        format!("{preview}...")
    } else {
        preview
    }
}

fn runner_label(runner_name: Option<&str>, binary_path: &str) -> String {
    runner_name.map(str::to_string).unwrap_or_else(|| {
        Path::new(binary_path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("binary")
            .to_string()
    })
}

fn runner_error_json(runner: &str, message: String) -> serde_json::Value {
    let timestamp = current_boot_time_ns();
    serde_json::json!({
        "timestamp": timestamp,
        "timestamp_ns": timestamp,
        "pid": 0,
        "comm": runner,
        "type": RUNNER_ERROR_TYPE,
        "message": message,
    })
}

pub fn runner_error_from_event(event: &Event) -> Option<RunnerError> {
    (event.data.get("type").and_then(|v| v.as_str()) == Some(RUNNER_ERROR_TYPE)).then(|| {
        RunnerError::from(
            event
                .data
                .get("message")
                .and_then(|v| v.as_str())
                .unwrap_or("runner failed")
                .to_string(),
        )
    })
}

struct ProbeProcessGuard {
    pgid: Option<libc::pid_t>,
    needs_sudo: bool,
}

impl ProbeProcessGuard {
    fn new(pid: Option<u32>, needs_sudo: bool) -> Self {
        Self {
            pgid: pid.map(|pid| pid as libc::pid_t),
            needs_sudo,
        }
    }

    fn disarm(&mut self) {
        self.pgid = None;
    }

    fn terminate(&mut self) {
        let Some(pgid) = self.pgid.take() else {
            return;
        };
        if self.needs_sudo {
            let _ = std::process::Command::new("sudo")
                .args(["-n", "kill", "-TERM", "--", &format!("-{pgid}")])
                .status();
        } else {
            unsafe {
                libc::killpg(pgid, libc::SIGTERM);
            }
        }
    }
}

impl Drop for ProbeProcessGuard {
    fn drop(&mut self) {
        self.terminate();
    }
}

pub fn current_boot_time_ns() -> u64 {
    std::fs::read_to_string("/proc/uptime")
        .ok()
        .and_then(|uptime| uptime.split_whitespace().next()?.parse::<f64>().ok())
        .map(|secs| (secs * 1_000_000_000.0) as u64)
        .unwrap_or(0)
}

pub fn parse_error_event(
    runner: &'static str,
    raw: serde_json::Value,
    reason: impl Into<String>,
    errors: &AtomicU64,
) -> Event {
    let timestamp = raw
        .get("timestamp_ns")
        .or_else(|| raw.get("timestamp"))
        .and_then(|v| v.as_u64())
        .unwrap_or_else(current_boot_time_ns);
    let pid = raw
        .get("pid")
        .and_then(|v| v.as_u64())
        .map(|v| v as u32)
        .unwrap_or(0);
    let comm = raw
        .get("comm")
        .and_then(|v| v.as_str())
        .unwrap_or(runner)
        .to_string();
    let count = errors.fetch_add(1, Ordering::Relaxed) + 1;

    Event::new_with_timestamp(
        timestamp,
        "diagnostic".to_string(),
        pid,
        comm,
        serde_json::json!({
            "type": "runner_parse_error",
            "runner": runner,
            "reason": reason.into(),
            "parse_error_count": count,
            "raw": raw,
        }),
    )
}

pub fn parse_json_event(
    runner: &'static str,
    timestamp_field: &'static str,
    raw: serde_json::Value,
    errors: &AtomicU64,
) -> Event {
    let Some(timestamp) = raw.get(timestamp_field).and_then(|v| v.as_u64()) else {
        return parse_error_event(runner, raw, format!("missing {timestamp_field}"), errors);
    };
    let Some(pid) = raw.get("pid").and_then(|v| v.as_u64()).map(|v| v as u32) else {
        return parse_error_event(runner, raw, "missing pid", errors);
    };
    let Some(comm) = raw.get("comm").and_then(|v| v.as_str()).map(str::to_string) else {
        return parse_error_event(runner, raw, "missing comm", errors);
    };

    Event::new_with_timestamp(timestamp, runner.to_string(), pid, comm, raw)
}

/// Common binary executor for runners - now supports streaming
pub struct BinaryExecutor {
    binary_path: String,
    additional_args: Vec<String>,
    runner_name: Option<String>,
}

impl BinaryExecutor {
    pub fn new(binary_path: String) -> Self {
        Self {
            binary_path,
            additional_args: Vec::new(),
            runner_name: None,
        }
    }

    pub fn with_args(mut self, args: &[String]) -> Self {
        self.additional_args = args.to_vec();
        self
    }

    pub fn set_args(&mut self, args: &[String]) {
        self.additional_args = args.to_vec();
    }

    pub fn with_runner_name(mut self, name: String) -> Self {
        self.runner_name = Some(name);
        self
    }

    /// Execute binary and get raw JSON stream.
    /// When not running as root, automatically wraps the command with `sudo` so
    /// eBPF programs get the privileges they need while the parent process
    /// (and the user's agent) stay unprivileged.
    pub async fn get_json_stream(&self) -> Result<JsonStream, RunnerError> {
        let needs_sudo = unsafe { libc::geteuid() } != 0;

        if needs_sudo {
            log::info!(
                "Executing binary (via sudo): {} {}",
                self.binary_path,
                self.additional_args.join(" ")
            );
        } else if self.additional_args.is_empty() {
            log::info!("Executing binary: {}", self.binary_path);
        } else {
            log::info!(
                "Executing binary: {} {}",
                self.binary_path,
                self.additional_args.join(" ")
            );
        }

        let mut cmd = if needs_sudo {
            let mut c = TokioCommand::new("sudo");
            c.arg(&self.binary_path);
            c
        } else {
            TokioCommand::new(&self.binary_path)
        };
        cmd.stdout(Stdio::piped()).stderr(Stdio::piped());
        cmd.kill_on_drop(true);
        cmd.process_group(0);

        // Add additional arguments if any
        if !self.additional_args.is_empty() {
            cmd.args(&self.additional_args);
            debug!("Added arguments: {:?}", self.additional_args);
        }

        let mut child = cmd.spawn().map_err(|e| {
            Box::new(std::io::Error::other(format!(
                "Failed to start binary: {}",
                e
            ))) as RunnerError
        })?;

        let stdout = child.stdout.take().ok_or_else(|| {
            Box::new(std::io::Error::other("Failed to get stdout")) as RunnerError
        })?;

        let stderr = child.stderr.take().ok_or_else(|| {
            Box::new(std::io::Error::other("Failed to get stderr")) as RunnerError
        })?;

        let child_pid = child.id();
        if let Some(pid) = child_pid {
            debug!("Binary started with PID: Some({})", pid);
        }

        // Clone needed data for the stream
        let runner_name = self.runner_name.clone();
        let binary_path = self.binary_path.clone();
        let label = runner_label(runner_name.as_deref(), &binary_path);

        // Spawn a task to read and log stderr
        let stderr_label = label.clone();
        tokio::spawn(async move {
            let mut stderr_reader = BufReader::new(stderr);
            let mut stderr_line = String::new();

            loop {
                stderr_line.clear();
                match stderr_reader.read_line(&mut stderr_line).await {
                    Ok(0) => {
                        // EOF reached
                        break;
                    }
                    Ok(_) => {
                        let trimmed = stderr_line.trim();
                        if !trimmed.is_empty() {
                            log::warn!("[{}] STDERR: {}", stderr_label, trimmed);
                        }
                    }
                    Err(e) => {
                        if e.kind() != std::io::ErrorKind::UnexpectedEof {
                            log::warn!("Error reading stderr: {}", e);
                        }
                        break;
                    }
                }
            }
        });

        let stream = async_stream::stream! {
            let mut guard = ProbeProcessGuard::new(child_pid, needs_sudo);
            let mut reader = BufReader::new(stdout);
            let mut line = Vec::new();
            let mut line_count = 0;

            debug!("Reading from binary stdout");

            loop {
                line.clear();

                match reader.read_until(b'\n', &mut line).await {
                    Ok(0) => {
                        debug!("Binary stdout closed (EOF)");
                        break;
                    }
                    Ok(_) => {
                        line_count += 1;
                        let decoded = String::from_utf8_lossy(&line);
                        let trimmed = decoded.trim();

                        if !trimmed.is_empty() {
                            debug!("Line {}: {}", line_count, preview_line(trimmed, 100));

                            // Try to parse as JSON
                            if trimmed.starts_with('{') && trimmed.ends_with('}') {
                                match serde_json::from_str::<serde_json::Value>(trimmed) {
                                    Ok(json_value) => {
                                        debug!("Parsed JSON value");
                                        yield json_value;
                                    }
                                    Err(e) => {
                                        log::warn!("Failed to parse JSON from line {}: {} - Line: {}",
                                            line_count, e,
                                            preview_line(trimmed, 200)
                                        );
                                    }
                                }
                            } else {
                                // Check if this might be a stderr message or debug output
                                if trimmed.contains("error") || trimmed.contains("warn") ||
                                   trimmed.contains("failed") || trimmed.contains("Error:") {
                                    log::warn!("Possible error message from binary at line {}: {}",
                                        line_count, trimmed);
                                } else {
                                    log::warn!("Skipping non-JSON line {} from binary: {}",
                                        line_count,
                                        preview_line(trimmed, 100)
                                    );
                                }
                            }
                        }
                    }
                    Err(e) => {
                        if e.kind() == std::io::ErrorKind::Interrupted {
                            // Retry on interrupted system calls
                            log::debug!("Read interrupted, retrying...");
                            continue;
                        } else {
                            log::warn!("Error reading from binary: {} (kind: {:?})", e, e.kind());
                            break;
                        }
                    }
                }
            }

            log::info!("Terminating binary process");

            // Terminate the child process
            guard.terminate();
            if let Err(e) = child.kill().await {
                log::warn!("Failed to kill binary process: {}", e);
            }

            // Wait for process to finish
            match child.wait().await {
                Ok(status) => {
                    debug!("Binary process terminated with status: {}", status);
                    guard.disarm();
                    if !status.success() {
                        yield runner_error_json(&label, format!("{label} exited with {status}"));
                    }
                }
                Err(e) => {
                    yield runner_error_json(&label, format!("failed to wait for {label}: {e}"));
                }
            }
        };

        Ok(Box::pin(stream))
    }
}

/// Common analyzer processor for runners
pub struct AnalyzerProcessor;

impl AnalyzerProcessor {
    /// Process events through a chain of analyzers
    pub async fn process_through_analyzers(
        mut stream: EventStream,
        analyzers: &mut [Box<dyn Analyzer>],
    ) -> Result<EventStream, RunnerError> {
        for analyzer in analyzers.iter_mut() {
            stream = analyzer.process(stream).await?;
        }
        Ok(stream)
    }
}

pub struct BinaryRunner {
    analyzers: Vec<Box<dyn Analyzer>>,
    executor: BinaryExecutor,
    source: &'static str,
    timestamp_field: &'static str,
}

impl BinaryRunner {
    pub fn new(
        runner_name: &str,
        source: &'static str,
        timestamp_field: &'static str,
        binary_path: impl AsRef<Path>,
    ) -> Self {
        Self {
            analyzers: Vec::new(),
            executor: BinaryExecutor::new(binary_path.as_ref().to_string_lossy().into_owned())
                .with_runner_name(runner_name.to_string()),
            source,
            timestamp_field,
        }
    }

    pub fn ssl(binary_path: impl AsRef<Path>) -> Self {
        Self::new("SSL", "ssl", "timestamp_ns", binary_path)
    }

    pub fn stdio(binary_path: impl AsRef<Path>) -> Self {
        Self::new("Stdio", "stdio", "timestamp_ns", binary_path)
    }

    pub fn with_args<I, S>(mut self, args: I) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        let args: Vec<_> = args.into_iter().map(|s| s.as_ref().to_string()).collect();
        self.executor = self.executor.with_args(&args);
        self
    }
}

#[async_trait]
impl Runner for BinaryRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let json_stream = self.executor.get_json_stream().await?;
        let errors = Arc::new(AtomicU64::new(0));
        let source = self.source;
        let ts_field = self.timestamp_field;
        let stream = json_stream.map(move |v| parse_json_event(source, ts_field, v, &errors));
        AnalyzerProcessor::process_through_analyzers(Box::pin(stream), &mut self.analyzers).await
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }
}
