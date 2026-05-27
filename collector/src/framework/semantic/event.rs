// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::core::Event;
use crate::framework::semantic::llm::{
    body_json, extract_model, extract_model_from_path, is_llm_path, provider_from_host,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EventKind {
    HttpRequest,
    HttpResponse,
    LlmRequest,
    LlmResponse,
    LlmError,
    TokenUsage,
    ProcessExec,
    ProcessExit,
    ProcessSignal,
    FsOpen,
    FsWrite,
    FsMutation,
    StdioMessage,
    StdioRpc,
    ResourceSample,
    AgentStatus,
    SessionStart,
    SessionEnd,
    ToolCall,
    Interruption,
    Unknown,
}

impl EventKind {
    pub fn as_str(self) -> &'static str {
        match self {
            EventKind::HttpRequest => "http.request",
            EventKind::HttpResponse => "http.response",
            EventKind::LlmRequest => "llm.request",
            EventKind::LlmResponse => "llm.response",
            EventKind::LlmError => "llm.error",
            EventKind::TokenUsage => "token.usage",
            EventKind::ProcessExec => "process.exec",
            EventKind::ProcessExit => "process.exit",
            EventKind::ProcessSignal => "process.signal",
            EventKind::FsOpen => "fs.open",
            EventKind::FsWrite => "fs.write",
            EventKind::FsMutation => "fs.mutation",
            EventKind::StdioMessage => "stdio.message",
            EventKind::StdioRpc => "stdio.rpc",
            EventKind::ResourceSample => "resource.sample",
            EventKind::AgentStatus => "agent.status",
            EventKind::SessionStart => "session.start",
            EventKind::SessionEnd => "session.end",
            EventKind::ToolCall => "tool.call",
            EventKind::Interruption => "interruption",
            EventKind::Unknown => "unknown",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Severity {
    Debug,
    Info,
    Warning,
    Error,
}

impl Severity {
    pub fn as_str(self) -> &'static str {
        match self {
            Severity::Debug => "debug",
            Severity::Info => "info",
            Severity::Warning => "warning",
            Severity::Error => "error",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CanonicalEvent {
    pub schema_version: u16,
    pub event_id: String,
    pub raw_event_id: String,
    pub timestamp_ms: u64,
    pub ingest_timestamp_ms: u64,
    pub source: String,
    pub kind: EventKind,
    pub severity: Severity,
    pub summary: Option<String>,
    pub pid: Option<u32>,
    pub tid: Option<u64>,
    pub ppid: Option<u32>,
    pub uid: Option<u32>,
    pub comm: Option<String>,
    pub container_id: Option<String>,
    pub host: Option<String>,
    pub method: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,
    pub provider: Option<String>,
    pub model: Option<String>,
    pub request_id: Option<String>,
    pub trace_id: Option<String>,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub parent_event_id: Option<String>,
    pub adapter_id: Option<String>,
    pub adapter_version: Option<String>,
    pub confidence: Option<f32>,
    pub attributes: Value,
}

pub fn normalize_event(
    event: &Event,
    raw_event_id: String,
    ingest_timestamp_ms: u64,
) -> CanonicalEvent {
    let data = &event.data;
    let source = event.source.clone();
    let tid = data.get("tid").and_then(|v| v.as_u64());
    let uid = data.get("uid").and_then(|v| v.as_u64()).map(|v| v as u32);
    let ppid = data.get("ppid").and_then(|v| v.as_u64()).map(|v| v as u32);

    let mut method = data
        .get("method")
        .and_then(|v| v.as_str())
        .map(String::from);
    let mut path = data.get("path").and_then(|v| v.as_str()).map(String::from);
    let status_code = data
        .get("status_code")
        .and_then(|v| v.as_u64())
        .map(|v| v as u16);
    let host = data
        .get("host")
        .and_then(|v| v.as_str())
        .or_else(|| {
            data.get("headers")
                .and_then(|h| h.get("host"))
                .and_then(|v| v.as_str())
                .or_else(|| {
                    data.get("headers")
                        .and_then(|h| h.get(":authority"))
                        .and_then(|v| v.as_str())
                })
        })
        .map(String::from);

    let message_type = data.get("message_type").and_then(|v| v.as_str());
    let provider = host.as_deref().map(provider_from_host);

    let body = body_json(data);
    let mut model = body
        .as_ref()
        .and_then(extract_model)
        .or_else(|| path.as_deref().and_then(extract_model_from_path));

    let mut kind = EventKind::Unknown;
    let mut severity = Severity::Info;

    if source == "http_parser" {
        match message_type {
            Some("request") => {
                let llm = path.as_deref().map(is_llm_path).unwrap_or(false);
                kind = if llm {
                    EventKind::LlmRequest
                } else {
                    EventKind::HttpRequest
                };
            }
            Some("response") => {
                kind = if status_code.map(|c| c >= 400).unwrap_or(false) {
                    severity = Severity::Error;
                    EventKind::LlmError
                } else {
                    EventKind::HttpResponse
                };
            }
            _ => kind = EventKind::Unknown,
        }
    } else if source == "sse_processor" {
        kind = EventKind::LlmResponse;
        model = model.or_else(|| extract_sse_model(data));
    } else if source == "process" {
        let event_name = data.get("event").and_then(|v| v.as_str()).unwrap_or("");
        kind = match event_name {
            "EXEC" => EventKind::ProcessExec,
            "EXIT" => EventKind::ProcessExit,
            e if e.contains("FILE_OPEN") => EventKind::FsOpen,
            e if e.contains("FILE_WRITE") => EventKind::FsWrite,
            e if e.contains("FILE_") => EventKind::FsMutation,
            _ => EventKind::Unknown,
        };
    } else if source == "stdio" || source == "stdiocap" || source == "cli_output" {
        kind = if data.get("rpc_method").is_some() {
            EventKind::StdioRpc
        } else {
            EventKind::StdioMessage
        };
    } else if source == "system" {
        kind = EventKind::ResourceSample;
        if data.get("alert").and_then(|v| v.as_bool()).unwrap_or(false) {
            severity = Severity::Warning;
        }
    }

    if method.is_none() && kind == EventKind::HttpRequest {
        method = data
            .get("first_line")
            .and_then(|v| v.as_str())
            .and_then(|line| line.split_whitespace().next())
            .map(String::from);
    }
    if path.is_none() && kind == EventKind::HttpRequest {
        path = data
            .get("first_line")
            .and_then(|v| v.as_str())
            .and_then(|line| line.split_whitespace().nth(1))
            .map(String::from);
    }

    let summary = build_summary(kind, &method, &host, &path, status_code, data);

    CanonicalEvent {
        schema_version: 1,
        event_id: format!("canon-{}", raw_event_id),
        raw_event_id,
        timestamp_ms: event.timestamp,
        ingest_timestamp_ms,
        source,
        kind,
        severity,
        summary,
        pid: Some(event.pid),
        tid,
        ppid,
        uid,
        comm: Some(event.comm.clone()),
        container_id: None,
        host,
        method,
        path,
        status_code,
        provider,
        model,
        request_id: data
            .get("request_id")
            .and_then(|v| v.as_str())
            .map(String::from),
        trace_id: None,
        session_id: None,
        conversation_id: None,
        parent_event_id: None,
        adapter_id: None,
        adapter_version: None,
        confidence: Some(0.75),
        attributes: data.clone(),
    }
}

fn build_summary(
    kind: EventKind,
    method: &Option<String>,
    host: &Option<String>,
    path: &Option<String>,
    status_code: Option<u16>,
    data: &Value,
) -> Option<String> {
    match kind {
        EventKind::LlmRequest | EventKind::HttpRequest => Some(format!(
            "{} {}{}",
            method.as_deref().unwrap_or("HTTP"),
            host.as_deref().unwrap_or(""),
            path.as_deref().unwrap_or("")
        )),
        EventKind::LlmResponse | EventKind::HttpResponse | EventKind::LlmError => Some(format!(
            "HTTP {}",
            status_code
                .map(|c| c.to_string())
                .unwrap_or_else(|| "response".to_string())
        )),
        EventKind::ProcessExec => data
            .get("filename")
            .and_then(|v| v.as_str())
            .map(|f| format!("exec {}", f)),
        EventKind::ProcessExit => Some("process exit".to_string()),
        EventKind::FsOpen | EventKind::FsWrite | EventKind::FsMutation => data
            .get("path")
            .or_else(|| data.get("filepath"))
            .and_then(|v| v.as_str())
            .map(|p| format!("file {}", p)),
        EventKind::StdioMessage => data
            .get("stream")
            .and_then(|v| v.as_str())
            .map(|stream| format!("{} output", stream)),
        _ => None,
    }
}

fn extract_sse_model(data: &Value) -> Option<String> {
    let events = data.get("sse_events")?.as_array()?;
    for event in events {
        let parsed = event.get("parsed_data")?;
        if let Some(model) = parsed
            .get("message")
            .and_then(|m| m.get("model"))
            .and_then(|v| v.as_str())
            .or_else(|| parsed.get("modelVersion").and_then(|v| v.as_str()))
            .or_else(|| parsed.get("model").and_then(|v| v.as_str()))
        {
            return Some(model.to_string());
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn normalizes_anthropic_llm_request() {
        let event = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let canonical = normalize_event(&event, "raw-1".to_string(), 2);
        assert_eq!(canonical.kind, EventKind::LlmRequest);
        assert_eq!(canonical.provider.as_deref(), Some("anthropic"));
        assert_eq!(canonical.model.as_deref(), Some("claude-sonnet-4-20250514"));
    }
}
