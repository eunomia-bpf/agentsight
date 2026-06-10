// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Claude Code. Statically links BoringSSL, so SSL capture needs the real
//! binary path (`record -- claude` resolves it automatically). Writes native
//! session logs under `~/.claude/projects` (primary attribution), and also
//! reports per-call token usage and tool outcomes via telemetry batches
//! (Datadog uploads or raw SSL payloads) decoded below.

use super::{AgentAdapter, Attribution, Discover, NativeSessions};
use crate::event::Event;
use crate::json::i64_field as json_i64;
use crate::providers::body_json;
use crate::semantic::{Observations, ObservedToolCall, ObservedUsage, TokenUsage};
use serde_json::Value;

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "claude",
    exec_names: &["claude", "claude-code"],
    exec_name_prefixes: &[],
    package_path_markers: &["@anthropic-ai/claude-code", "/claude-code/"],
    discover: Some(Discover {
        id: "claude-code",
        display_name: "Claude Code",
        command: "claude",
        recommended_capture: "agentsight record --db record.db -- claude -p 'hello' --output-format json",
    }),
    native_sessions: Some(NativeSessions {
        dir_parts: [".claude", "projects"],
        path_marker: "/.claude/",
    }),
    attribution: Attribution::NativeSessionFiles,
    decode_observations: Some(decode_telemetry),
};

/// Claude Code telemetry batches carry `tengu_api_success` (token usage) and
/// `tengu_tool_use_success` (tool outcomes) messages.
fn decode_telemetry(event: &Event, event_id: &str, host: Option<&str>, out: &mut Observations) {
    if !host.unwrap_or_default().contains("datadoghq.com") && event.source != "ssl" {
        return;
    }
    let body = body_json(&event.data).or_else(|| {
        event
            .data
            .get("data")
            .and_then(Value::as_str)
            .and_then(|text| serde_json::from_str(text).ok())
    });
    let Some(Value::Array(items)) = body else {
        return;
    };
    for (idx, item) in items.iter().enumerate() {
        let message = item
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or_default();
        if message == "tengu_api_success" {
            let input = json_i64(item, "input_tokens");
            let output = json_i64(item, "output_tokens");
            let cache = json_i64(item, "cached_input_tokens");
            let total = input + output + cache;
            if total <= 0 {
                continue;
            }
            let model = item
                .get("model")
                .and_then(Value::as_str)
                .unwrap_or("unknown");
            out.token_usage.push(ObservedUsage {
                llm_call_id: format!("claude-telemetry-{}-{idx}", event_id),
                provider: "anthropic",
                model: model.to_string(),
                usage: TokenUsage {
                    input_tokens: input,
                    output_tokens: output,
                    cache_read_tokens: cache,
                    total_override: Some(total),
                    ..Default::default()
                },
                source: "claude_telemetry",
                confidence: 0.80,
            });
        } else if message == "tengu_tool_use_success" {
            out.tool_calls.push(ObservedToolCall {
                id: format!("claude-tool-telemetry-{}-{idx}", event_id),
                tool_name: item
                    .get("tool_name")
                    .and_then(Value::as_str)
                    .unwrap_or("?")
                    .to_string(),
                tool_call_id: item
                    .get("request_id")
                    .and_then(Value::as_str)
                    .map(str::to_string),
                duration_ms: item
                    .get("duration_ms")
                    .and_then(Value::as_i64)
                    .map(|v| v as u64),
                confidence: 0.75,
            });
        }
    }
}
