//! Process trace event parser
//!
//! Parses process events (execve, stdout, exit) from VariableEvent.

use crate::chrome_trace::{ChromeTraceEvent, TraceArgs, ns_to_us};
use crate::probes::proctrace::VariableEvent;
use serde_json::json;

/// Parser for process events
pub struct ProcTraceParser;

/// Process event type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProcEventType {
    /// Process execution (execve)
    Exec,
    /// Stdout output
    Stdout,
    /// Process exit
    Exit,
}

/// Parsed process event
#[derive(Debug, Clone)]
pub struct ParsedProcEvent {
    /// Event type
    pub event_type: ProcEventType,
    /// Process ID
    pub pid: u32,
    /// Thread ID
    pub tid: u32,
    /// Parent PID (for exec events)
    pub ppid: u32,
    /// Parent TID (thread ID that spawned this process)
    pub ptid: u32,
    /// Process name
    pub comm: String,
    /// Timestamp in nanoseconds
    pub timestamp_ns: u64,
    /// Command arguments (for exec events)
    pub args: Option<String>,
    /// Stdout data (for stdout events)
    pub stdout_data: Option<String>,
}

impl ProcTraceParser {
    /// Parse a variable-length process event
    pub fn parse_variable(event: &VariableEvent) -> Option<ParsedProcEvent> {
        match event {
            VariableEvent::Exec { header, filename, args } => {
                Some(ParsedProcEvent {
                    event_type: ProcEventType::Exec,
                    pid: header.pid,
                    tid: header.tid,
                    ppid: header.ppid,
                    ptid: header.ptid,
                    comm: event.comm_str(),
                    timestamp_ns: header.timestamp_ns,
                    args: Some(args.clone()).filter(|s| !s.is_empty()),
                    stdout_data: None,
                })
            }
            VariableEvent::Stdout { header, payload, .. } => {
                let stdout_data = String::from_utf8(payload.clone()).ok();
                Some(ParsedProcEvent {
                    event_type: ProcEventType::Stdout,
                    pid: header.pid,
                    tid: header.tid,
                    ppid: header.ppid,
                    ptid: header.ptid,
                    comm: event.comm_str(),
                    timestamp_ns: header.timestamp_ns,
                    args: None,
                    stdout_data,
                })
            }
            VariableEvent::Exit { header, .. } => {
                Some(ParsedProcEvent {
                    event_type: ProcEventType::Exit,
                    pid: header.pid,
                    tid: header.tid,
                    ppid: header.ppid,
                    ptid: header.ptid,
                    comm: event.comm_str(),
                    timestamp_ns: header.timestamp_ns,
                    args: None,
                    stdout_data: None,
                })
            }
            VariableEvent::Unknown(_) => None,
        }
    }

    /// Convert a variable-length process event to Chrome Trace Event format
    pub fn to_chrome_trace_event(event: &VariableEvent) -> Option<ChromeTraceEvent> {
        let parsed = Self::parse_variable(event)?;
        let ts_us = ns_to_us(parsed.timestamp_ns);

        match parsed.event_type {
            ProcEventType::Exec => {
                let name = format!("exec: {}", parsed.comm);
                let args = json!({
                    "pid": parsed.pid,
                    "ppid": parsed.ppid,
                    "comm": parsed.comm,
                    "args": parsed.args,
                });

                Some(ChromeTraceEvent {
                    name,
                    cat: "process.exec".to_string(),
                    ph: "i".to_string(),
                    ts: ts_us,
                    dur: None,
                    pid: parsed.pid,
                    tid: parsed.tid as u64,
                    args: Some(args),
                    id: None,
                    bp: None,
                })
            }
            ProcEventType::Stdout => {
                let data = parsed.stdout_data?;
                let display_data = if data.len() > 100 {
                    format!("{}...", &data[..100])
                } else {
                    data.clone()
                };

                Some(ChromeTraceEvent {
                    name: format!("stdout: {}", display_data.trim()),
                    cat: "process.stdout".to_string(),
                    ph: "i".to_string(),
                    ts: ts_us,
                    dur: None,
                    pid: parsed.pid,
                    tid: parsed.tid as u64,
                    args: Some(json!({
                        "pid": parsed.pid,
                        "comm": parsed.comm,
                        "data": data,
                        "len": data.len(),
                    })),
                    id: None,
                    bp: None,
                })
            }
            ProcEventType::Exit => {
                Some(ChromeTraceEvent {
                    name: format!("exit: {}", parsed.comm),
                    cat: "process.exit".to_string(),
                    ph: "i".to_string(),
                    ts: ts_us,
                    dur: None,
                    pid: parsed.pid,
                    tid: parsed.tid as u64,
                    args: Some(json!({
                        "pid": parsed.pid,
                        "comm": parsed.comm,
                    })),
                    id: None,
                    bp: None,
                })
            }
        }
    }

    /// Parse multiple variable-length events
    pub fn parse_events(events: &[VariableEvent]) -> Vec<ParsedProcEvent> {
        events.iter().filter_map(Self::parse_variable).collect()
    }

    /// Convert multiple variable-length events to Chrome Trace Events
    pub fn to_chrome_trace_events(events: &[VariableEvent]) -> Vec<ChromeTraceEvent> {
        events.iter().filter_map(Self::to_chrome_trace_event).collect()
    }
}

impl TraceArgs for ParsedProcEvent {
    fn to_trace_args(&self) -> serde_json::Value {
        let mut args = serde_json::Map::new();
        
        // Common fields
        args.insert("pid".to_string(), json!(self.pid));
        args.insert("comm".to_string(), json!(&self.comm));
        
        // Event type specific fields
        match self.event_type {
            ProcEventType::Exec => {
                args.insert("ppid".to_string(), json!(self.ppid));
                args.insert("ptid".to_string(), json!(self.ptid));
                if let Some(ref cmd_args) = self.args {
                    args.insert("args".to_string(), json!(cmd_args));
                }
            }
            ProcEventType::Stdout => {
                if let Some(ref data) = self.stdout_data {
                    args.insert("len".to_string(), json!(data.len()));
                    
                    // Add data preview (truncated)
                    let preview = if data.len() > 200 {
                        format!("{}... ({} bytes total)", &data[..200], data.len())
                    } else {
                        data.clone()
                    };
                    args.insert("data".to_string(), json!(preview));
                }
            }
            ProcEventType::Exit => {
                // Exit event has minimal args
            }
        }
        
        serde_json::Value::Object(args)
    }
}

impl ParsedProcEvent {
    /// Convert to Chrome Trace Event
    pub fn to_chrome_trace_event(&self) -> ChromeTraceEvent {
        let ts_us = ns_to_us(self.timestamp_ns);
        let name = match self.event_type {
            ProcEventType::Exec => format!("exec: {}", self.comm),
            ProcEventType::Stdout => {
                let data = self.stdout_data.as_ref().cloned().unwrap_or_default();
                let display_data = if data.len() > 100 {
                    format!("{}...", &data[..100])
                } else {
                    data.clone()
                };
                format!("stdout: {}", display_data.trim())
            }
            ProcEventType::Exit => format!("exit: {}", self.comm),
        };
        
        let cat = match self.event_type {
            ProcEventType::Exec => "process.exec",
            ProcEventType::Stdout => "process.stdout",
            ProcEventType::Exit => "process.exit",
        };

        ChromeTraceEvent {
            name,
            cat: cat.to_string(),
            ph: "i".to_string(),
            ts: ts_us,
            dur: None,
            pid: self.pid,
            tid: self.tid as u64,
            args: Some(self.to_trace_args()),
            id: None,
            bp: None,
        }
    }
}
