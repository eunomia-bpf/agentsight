//! Aggregated process data structure
//!
//! Defines the `AggregatedProcess` structure for representing a complete
//! process lifecycle with exec, stdout, stderr, and exit events.

use crate::chrome_trace::{ChromeTraceEvent, ToChromeTraceEvent, ns_to_us, next_flow_id};

/// Aggregated process data for a specific PID
#[derive(Debug, Clone)]
pub struct AggregatedProcess {
    /// Process ID
    pub pid: u32,
    /// Parent PID
    pub ppid: u32,
    /// Parent TID (thread ID that spawned this process)
    pub ptid: u32,
    /// Thread ID
    pub tid: u32,
    /// Process name
    pub comm: String,
    /// Executable filename (from exec event)
    pub filename: Option<String>,
    /// Command arguments (from exec event)
    pub args: Option<String>,
    /// Collected stdout data
    pub stdout_data: Vec<u8>,
    /// Collected stderr data
    pub stderr_data: Vec<u8>,
    /// Whether this aggregation is complete (process exited)
    pub is_complete: bool,
    /// First timestamp when this process was seen (nanoseconds)
    pub start_timestamp_ns: u64,
    /// Last timestamp when data was added
    pub end_timestamp_ns: u64,
}

impl AggregatedProcess {
    /// Create a new aggregated process
    pub fn new(pid: u32, tid: u32, ppid: u32, ptid: u32, comm: String, timestamp_ns: u64) -> Self {
        AggregatedProcess {
            pid,
            ppid,
            ptid,
            tid,
            comm,
            filename: None,
            args: None,
            stdout_data: Vec::new(),
            stderr_data: Vec::new(),
            is_complete: false,
            start_timestamp_ns: timestamp_ns,
            end_timestamp_ns: timestamp_ns,
        }
    }

    /// Add exec event data
    pub fn add_exec(&mut self, filename: String, args: String, timestamp_ns: u64) {
        self.filename = Some(filename);
        self.args = Some(args);
        self.end_timestamp_ns = timestamp_ns;
    }

    /// Add stdout data
    pub fn add_stdout(&mut self, data: &[u8], timestamp_ns: u64) {
        self.stdout_data.extend_from_slice(data);
        self.end_timestamp_ns = timestamp_ns;
    }

    /// Add stderr data
    pub fn add_stderr(&mut self, data: &[u8], timestamp_ns: u64) {
        self.stderr_data.extend_from_slice(data);
        self.end_timestamp_ns = timestamp_ns;
    }

    /// Mark this aggregation as complete (process exited)
    pub fn mark_complete(&mut self, timestamp_ns: u64) {
        self.is_complete = true;
        self.end_timestamp_ns = timestamp_ns;
    }

    /// Get stdout data as string (lossy conversion)
    pub fn stdout_string(&self) -> String {
        String::from_utf8_lossy(&self.stdout_data).into_owned()
    }

    /// Get stderr data as string (lossy conversion)
    pub fn stderr_string(&self) -> String {
        String::from_utf8_lossy(&self.stderr_data).into_owned()
    }

    /// Get the duration in nanoseconds
    pub fn duration_ns(&self) -> u64 {
        self.end_timestamp_ns.saturating_sub(self.start_timestamp_ns)
    }

    /// Get total stdout data size
    pub fn stdout_size(&self) -> usize {
        self.stdout_data.len()
    }

    /// Get total stderr data size
    pub fn stderr_size(&self) -> usize {
        self.stderr_data.len()
    }

    /// Build event name with stdout preview (max 50 chars)
    fn build_event_name(&self, stdout_str: &str, stderr_str: &str) -> String {
        let stdout_preview = if stdout_str.len() > 50 {
            format!("{}...", &stdout_str[..50].trim())
        } else if !stdout_str.is_empty() {
            stdout_str.trim().to_string()
        } else {
            String::new()
        };

        match (stdout_preview.is_empty(), stderr_str.is_empty()) {
            (false, false) => format!("process: {} | stdout: {} | stderr: {}", self.comm, stdout_preview, self.stderr_size()),
            (false, true) => format!("process: {} | stdout: {}", self.comm, stdout_preview),
            (true, false) => format!("process: {} | stderr: {}", self.comm, self.stderr_size()),
            (true, true) => format!("process: {}", self.comm),
        }
    }
}

impl ToChromeTraceEvent for AggregatedProcess {
    /// Convert to Chrome Trace Events with fork-process flow association
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let mut events = Vec::new();
        let flow_id = next_flow_id();
        let ts_us = ns_to_us(self.start_timestamp_ns);
        let has_parent = self.ppid != 0 && self.ptid != 0;

        // 1. Fork event in parent process (if valid parent info)
        if has_parent {
            let fork_args = serde_json::json!({
                "child_pid": self.pid,
                "child_tid": self.tid,
                "child_comm": &self.comm,
                "child_filename": self.filename,
                "child_args": self.args,
            });
            
            let fork_event = ChromeTraceEvent::complete(
                format!("fork: {}", self.comm),
                "process.fork",
                self.ppid,
                self.ptid as u64,
                ts_us,
                10_000, // 10ms duration
            )
            .with_trace_args_value(fork_args);
            events.push(fork_event);
        }

        // 2. Child process lifecycle event
        let stdout_str = self.stdout_string();
        let stderr_str = self.stderr_string();
        
        // Build event name with stdout preview (max 50 chars)
        let name = self.build_event_name(&stdout_str, &stderr_str);
        
        let args = serde_json::json!({
            "pid": self.pid,
            "ppid": self.ppid,
            "ptid": self.ptid,
            "tid": self.tid,
            "comm": &self.comm,
            "is_complete": self.is_complete,
            "stdout_size": self.stdout_size(),
            "stderr_size": self.stderr_size(),
            "flow_id": flow_id,
            "filename": self.filename,
            "args": self.args,
            "stdout": if stdout_str.is_empty() { None } else { Some(&stdout_str) },
            "stderr": if stderr_str.is_empty() { None } else { Some(&stderr_str) },
        });

        let lifecycle_event = ChromeTraceEvent::complete(
            name,
            "process_lifecycle",
            self.pid,
            self.tid as u64,
            ts_us,
            ns_to_us(self.duration_ns()),
        )
        .with_trace_args_value(args);
        events.push(lifecycle_event);

        // 3. Create flow events linking parent fork to child lifecycle
        if has_parent {
            let (flow_start, flow_end) = ChromeTraceEvent::flow_from_events_with_id(
                events.first().unwrap(),
                events.last().unwrap(),
                flow_id,
            );
            events.push(flow_start);
            events.push(flow_end);
        }

        events
    }
}
