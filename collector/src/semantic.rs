// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Typed semantic event contract between the decode stage and the
//! materialized view. Decode (`crate::decode`) is the only module that
//! navigates raw event JSON; everything downstream consumes these types.

use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TokenUsage {
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_override: Option<i64>,
}

impl TokenUsage {
    pub fn total_tokens(&self) -> i64 {
        self.total_override.unwrap_or(
            self.input_tokens
                + self.output_tokens
                + self.cache_creation_tokens
                + self.cache_read_tokens,
        )
    }

    pub fn is_empty(&self) -> bool {
        self.total_tokens() == 0
    }
}

/// One decoded event. `raw` carries the original payload for evidence
/// (audit `details`); it must never be navigated outside `crate::decode`.
#[derive(Debug, Clone)]
pub struct SemanticEvent {
    pub event_id: String,
    pub timestamp_ms: u64,
    pub pid: u32,
    pub tid: Option<u64>,
    pub ppid: Option<u32>,
    pub comm: String,
    pub summary: Option<String>,
    pub body: SemanticBody,
    /// Agent-specific telemetry decoded from the same payload (e.g. Claude
    /// telemetry batches, Gemini CLI stdout stats). Ingested for every event
    /// regardless of `body`.
    pub observations: Observations,
    pub raw: Value,
}

#[derive(Debug, Clone)]
pub enum SemanticBody {
    LlmRequest(LlmRequest),
    LlmResponse(LlmResponse),
    HttpRequest(HttpInfo),
    HttpResponse(HttpInfo),
    ProcessExec(ProcessInfo),
    ProcessExit(ProcessInfo),
    FileWrite(FileWrite),
    NetworkOp(NetworkOp),
    ResourceSample(ResourceSample),
    Other,
}

#[derive(Debug, Clone)]
pub struct LlmRequest {
    pub provider: Option<String>,
    pub model: Option<String>,
    pub host: Option<String>,
    pub path: Option<String>,
    pub request_id: Option<String>,
    /// Request body parsed once at decode time (None when not valid JSON).
    pub body: Option<Value>,
}

#[derive(Debug, Clone)]
pub struct LlmResponse {
    pub provider: Option<String>,
    pub model: Option<String>,
    pub host: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,
    pub request_id: Option<String>,
    pub is_error: bool,
    /// Token usage extracted once at decode time (SSE-derived for streamed
    /// responses, body-derived otherwise).
    pub usage: TokenUsage,
    /// Response body for evidence: parsed JSON body for plain HTTP, the full
    /// accumulated SSE payload for streamed responses.
    pub body: Option<Value>,
    pub tool_uses: Vec<ToolUse>,
}

#[derive(Debug, Clone)]
pub struct ToolUse {
    pub index: usize,
    pub name: String,
    pub tool_call_id: Option<String>,
    pub input_json: Option<String>,
}

#[derive(Debug, Clone)]
pub struct HttpInfo {
    pub host: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,
}

#[derive(Debug, Clone)]
pub struct ProcessInfo {
    pub filename: Option<String>,
    pub command: Option<String>,
    pub argv: Vec<String>,
    pub cwd: Option<String>,
    pub exit_code: Option<i64>,
}

#[derive(Debug, Clone)]
pub struct FileWrite {
    pub path: Option<String>,
}

#[derive(Debug, Clone)]
pub struct NetworkOp {
    pub action: String,
    pub target: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ResourceSample {
    pub cpu_percent: Option<f64>,
    pub rss_mb: Option<f64>,
}

#[derive(Debug, Clone, Default)]
pub struct Observations {
    pub token_usage: Vec<ObservedUsage>,
    pub tool_calls: Vec<ObservedToolCall>,
}

/// Token usage reported by the agent itself (telemetry, stdout stats),
/// independent of a captured HTTP exchange.
#[derive(Debug, Clone)]
pub struct ObservedUsage {
    /// Synthetic llm_call id, computed at decode time so row ids stay stable.
    pub llm_call_id: String,
    pub provider: &'static str,
    pub model: String,
    pub usage: TokenUsage,
    pub source: &'static str,
    pub confidence: f32,
}

#[derive(Debug, Clone)]
pub struct ObservedToolCall {
    pub id: String,
    pub tool_name: String,
    pub tool_call_id: Option<String>,
    pub duration_ms: Option<u64>,
    pub confidence: f32,
}
