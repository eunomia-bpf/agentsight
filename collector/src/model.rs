// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

pub type ViewResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

pub(crate) const AGENT_NATIVE_SOURCE: &str = "agent_native_session";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenSummary {
    pub group: String,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_tokens: i64,
    pub calls: i64,
    pub sessions: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsageRow {
    pub id: String,
    pub llm_call_id: String,
    pub timestamp_ms: u64,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub provider: Option<String>,
    pub model: Option<String>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_tokens: i64,
    pub source: String,
    pub view_source: String,
    pub confidence: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmCallRow {
    pub id: String,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub start_timestamp_ms: u64,
    pub end_timestamp_ms: Option<u64>,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub provider: Option<String>,
    pub model: Option<String>,
    pub call_kind: Option<String>,
    pub status: String,
    pub error_type: Option<String>,
    pub finish_reason: Option<String>,
    pub host: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub request: Value,
    pub response: Value,
}

#[derive(Debug, Clone, Copy)]
pub struct SnapshotOptions {
    pub audit_limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub schema_version: u16,
    pub generated_at: String,
    pub summary: SnapshotSummary,
    pub token_summary: Vec<TokenSummary>,
    pub network_targets: Vec<NetworkTargetRow>,
    pub process_nodes: Vec<ProcessNodeRow>,
    pub audit_events: Vec<AuditEventRow>,
    pub resource_samples: Vec<ResourceSampleRow>,
    pub sessions: Vec<SessionRow>,
    pub tool_calls: Vec<ToolCallRow>,
}

impl Snapshot {
    pub(crate) fn empty(source: impl Into<String>) -> Self {
        Self {
            schema_version: 1,
            generated_at: String::new(),
            summary: SnapshotSummary::empty(source),
            token_summary: Vec::new(),
            network_targets: Vec::new(),
            process_nodes: Vec::new(),
            audit_events: Vec::new(),
            resource_samples: Vec::new(),
            sessions: Vec::new(),
            tool_calls: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotSummary {
    pub source: String,
    pub view_events: i64,
    pub llm_calls: i64,
    pub token_usage_rows: i64,
    pub audit_events: i64,
    pub sessions: i64,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub audit_limit: usize,
}

impl SnapshotSummary {
    pub(crate) fn empty(source: impl Into<String>) -> Self {
        Self {
            source: source.into(),
            view_events: 0,
            llm_calls: 0,
            token_usage_rows: 0,
            audit_events: 0,
            sessions: 0,
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            start_timestamp_ms: None,
            end_timestamp_ms: None,
            audit_limit: 0,
        }
    }

    pub(crate) fn duration_s(&self) -> f64 {
        match (self.start_timestamp_ms, self.end_timestamp_ms) {
            (Some(start), Some(end)) if end > start => (end - start) as f64 / 1000.0,
            _ => 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkTargetRow {
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub host: String,
    pub path: Option<String>,
    pub count: i64,
    pub error_count: i64,
    pub first_timestamp_ms: Option<u64>,
    pub last_timestamp_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceSampleRow {
    pub timestamp_ms: u64,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub cpu_percent: Option<f64>,
    pub rss_mb: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEventRow {
    pub id: String,
    pub timestamp_ms: u64,
    pub audit_type: String,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub subject: Option<String>,
    pub action: Option<String>,
    pub target: Option<String>,
    pub status: Option<String>,
    pub summary: Option<String>,
    pub details: Value,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct AuditCounters {
    pub(crate) process_execs: usize,
    pub(crate) process_exits: usize,
    pub(crate) process_exit_success: usize,
    pub(crate) process_exit_failure: usize,
    pub(crate) file_events: usize,
    pub(crate) network_events: usize,
    pub(crate) unique_files: BTreeSet<String>,
    pub(crate) pids: BTreeSet<u32>,
}

impl AuditCounters {
    pub(crate) fn from_rows<'a>(rows: impl IntoIterator<Item = &'a AuditEventRow>) -> Self {
        let mut counters = Self::default();
        for row in rows {
            counters.observe(row);
        }
        counters
    }

    pub(crate) fn by_pid<'a>(
        rows: impl IntoIterator<Item = &'a AuditEventRow>,
    ) -> BTreeMap<u32, Self> {
        let mut by_pid = BTreeMap::new();
        for row in rows {
            if let Some(pid) = row.pid {
                by_pid.entry(pid).or_insert_with(Self::default).observe(row);
            }
        }
        by_pid
    }

    fn observe(&mut self, row: &AuditEventRow) {
        if let Some(pid) = row.pid {
            self.pids.insert(pid);
        }
        match row.audit_type.as_str() {
            "process" if row.action.as_deref() == Some("exec") => self.process_execs += 1,
            "process" if row.action.as_deref() == Some("exit") => {
                self.process_exits += 1;
                match row.status.as_deref() {
                    Some("success") => self.process_exit_success += 1,
                    Some("failure") => self.process_exit_failure += 1,
                    _ => {}
                }
            }
            "file" => {
                self.file_events += 1;
                if let Some(target) = &row.target {
                    self.unique_files.insert(target.clone());
                }
            }
            "network" => self.network_events += 1,
            _ => {}
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessNodeRow {
    pub id: String,
    pub pid: u32,
    pub ppid: Option<u32>,
    pub root_pid: Option<u32>,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub comm: Option<String>,
    pub command: Option<String>,
    pub argv: Vec<String>,
    pub cwd: Option<String>,
    pub exit_code: Option<i32>,
    pub status: Option<String>,
    pub view_source: String,
    pub confidence: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCallRow {
    pub id: String,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub timestamp_ms: u64,
    pub tool_name: Option<String>,
    pub tool_call_id: Option<String>,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub duration_ms: Option<u64>,
    pub status: Option<String>,
    pub input: Value,
    pub output: Value,
    pub related_pid: Option<u32>,
    pub related_event_id: Option<String>,
    pub view_source: String,
    pub confidence: Option<f32>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SessionRow {
    pub id: String,
    pub agent_type: String,
    pub start_timestamp_ms: u64,
    pub end_timestamp_ms: Option<u64>,
    pub status: String,
    pub model: Option<String>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub view_source: String,
    pub confidence: Option<f64>,
    pub attributes: Value,
}

pub trait ViewSink: Send {
    fn llm_call(&mut self, _row: &LlmCallRow) -> ViewResult<()> {
        Ok(())
    }

    fn token_usage(&mut self, _row: &TokenUsageRow) -> ViewResult<()> {
        Ok(())
    }

    fn audit_event(&mut self, _row: &AuditEventRow) -> ViewResult<()> {
        Ok(())
    }

    fn process_node(&mut self, _row: &ProcessNodeRow) -> ViewResult<()> {
        Ok(())
    }

    fn tool_call(&mut self, _row: &ToolCallRow) -> ViewResult<()> {
        Ok(())
    }

    fn network_target(&mut self, _row: &NetworkTargetRow) -> ViewResult<()> {
        Ok(())
    }

    fn resource_sample(&mut self, _row: &ResourceSampleRow) -> ViewResult<()> {
        Ok(())
    }
}
