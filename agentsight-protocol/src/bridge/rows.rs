// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Row projections carried by bridge mutations.
//!
//! Every mutable row carries `row_id` (stable source row id) plus `revision`
//! (0 on first emit, incremented only when the row's state actually changed).
//! All non-`content` fields are metadata-only and are the sole fields populated
//! under [`super::DisclosureMode::MetadataOnly`]; the optional `content` struct
//! is populated only under research/incident disclosure.

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Agent session as observed by the collector.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeSessionRow {
    pub row_id: String,
    pub revision: u64,
    pub agent_type: String,
    pub start_ts_ms: u64,
    pub end_ts_ms: Option<u64>,
    pub status: String,
    pub model: Option<String>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub view_source: String,
    pub confidence: Option<f64>,
    pub cwd_class: Option<String>,
    pub content: Option<SessionContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SessionContent {
    pub cwd: Option<String>,
}

/// One model call observed on the wire.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeLlmCallRow {
    pub row_id: String,
    pub revision: u64,
    pub session_row_id: Option<String>,
    pub start_ts_ms: u64,
    pub end_ts_ms: Option<u64>,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub provider: Option<String>,
    pub model: Option<String>,
    pub call_kind: Option<String>,
    pub status: String,
    pub error_type: Option<String>,
    pub finish_reason: Option<String>,
    pub status_code: Option<u16>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub destination_class: Option<String>,
    pub content: Option<LlmContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LlmContent {
    pub host: Option<String>,
    pub path: Option<String>,
    pub request: Option<Value>,
    pub response: Option<Value>,
}

/// Token accounting attached to a model call. Counts only; no content struct.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeTokenUsageRow {
    pub row_id: String,
    pub revision: u64,
    pub llm_call_row_id: Option<String>,
    pub ts_ms: u64,
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

/// One framework-brokered tool call.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeToolCallRow {
    pub row_id: String,
    pub revision: u64,
    pub session_row_id: Option<String>,
    pub ts_ms: u64,
    pub tool_name: Option<String>,
    pub semantic_category: Option<String>,
    pub native_tool_call_id: Option<String>,
    pub start_ts_ms: Option<u64>,
    pub end_ts_ms: Option<u64>,
    pub duration_ms: Option<u64>,
    pub status: Option<String>,
    pub related_pid: Option<u32>,
    pub view_source: String,
    pub confidence: Option<f32>,
    pub content: Option<ToolContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ToolContent {
    pub input: Option<Value>,
    pub output: Option<Value>,
}

/// One process in the observed process tree.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeProcessNodeRow {
    pub row_id: String,
    pub revision: u64,
    pub pid: u32,
    /// Kernel process start time in clock ticks (`CLK_TCK` units since boot,
    /// field 22 of `/proc/<pid>/stat`). Together with `pid` this is the identity
    /// that survives pid reuse. `None` when the capture channel does not report
    /// it — never derive it from a timestamp.
    pub start_ticks: Option<u64>,
    pub ppid: Option<u32>,
    pub root_pid: Option<u32>,
    pub start_ts_ms: Option<u64>,
    pub end_ts_ms: Option<u64>,
    pub comm: Option<String>,
    pub executable_basename: Option<String>,
    pub command_fingerprint: Option<String>,
    pub argv_shape: Option<String>,
    pub cwd_class: Option<String>,
    pub exit_code: Option<i32>,
    pub status: Option<String>,
    pub view_source: String,
    pub confidence: Option<f32>,
    pub content: Option<ProcessContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProcessContent {
    pub command: Option<String>,
    pub argv: Vec<String>,
    pub cwd: Option<String>,
}

/// One audit record. Insert-only: audit rows are never revised.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeAuditEventRow {
    pub row_id: String,
    pub ts_ms: u64,
    /// `process` | `file` | `network` | `llm`.
    pub audit_type: String,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub action: Option<String>,
    pub path_class: Option<String>,
    pub extension: Option<String>,
    pub destination_class: Option<String>,
    pub port: Option<u16>,
    pub protocol: Option<String>,
    pub bytes_or_count: Option<i64>,
    pub status: Option<String>,
    pub raw_target_digest: Option<String>,
    pub content: Option<AuditContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AuditContent {
    pub subject: Option<String>,
    pub target: Option<String>,
    pub summary: Option<String>,
    pub details: Option<Value>,
}

/// Rolled-up network destination for one process.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeNetworkTargetRow {
    pub row_id: String,
    pub revision: u64,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub destination_class: String,
    pub port: Option<u16>,
    pub count: i64,
    pub error_count: i64,
    pub first_ts_ms: Option<u64>,
    pub last_ts_ms: Option<u64>,
    pub raw_target_digest: Option<String>,
    pub content: Option<NetworkContent>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NetworkContent {
    pub host: Option<String>,
    pub path: Option<String>,
}

/// One CPU/RSS sample. Insert-only, and metadata-only by construction.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeResourceSampleRow {
    pub ts_ms: u64,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub cpu_percent: Option<f64>,
    pub rss_mb: Option<i64>,
}
