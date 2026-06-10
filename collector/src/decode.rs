// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Decode stage: the single owner of raw event JSON navigation.
//!
//! Converts an untyped runner [`Event`] into a typed
//! [`SemanticEvent`](crate::semantic::SemanticEvent) exactly once. Everything
//! downstream (the materialized view, sinks, surfaces) consumes typed fields;
//! no JSON key access is allowed outside this module and debug surfaces.

use crate::event::Event;
use crate::providers::{
    body_json, extract_model, extract_model_from_path, extract_model_from_sse,
    extract_token_usage, extract_token_usage_from_sse, is_llm_path, provider_from_host,
};
use crate::semantic::{
    FileWrite, HttpInfo, LlmRequest, LlmResponse, NetworkOp, Observations, ProcessInfo,
    ResourceSample, SemanticBody, SemanticEvent, ToolUse,
};
use serde_json::Value;

pub(crate) fn decode_event(event: &Event, raw_event_id: String) -> SemanticEvent {
    let data = &event.data;
    let event_id = format!("canon-{}", raw_event_id);
    let tid = data.get("tid").and_then(Value::as_u64);
    let ppid = data.get("ppid").and_then(Value::as_u64).map(|v| v as u32);

    let (body, summary) = match event.source.as_str() {
        "http_parser" => decode_http(data),
        "sse_processor" => (SemanticBody::LlmResponse(decode_sse(data)), None),
        "process" => decode_process(data),
        "system" => (
            SemanticBody::ResourceSample(decode_resource_sample(data)),
            None,
        ),
        _ => (SemanticBody::Other, None),
    };

    let mut observations = Observations::default();
    crate::agents::decode_observations(
        event,
        &event_id,
        extract_host(data).as_deref(),
        &mut observations,
    );

    SemanticEvent {
        event_id,
        timestamp_ms: event.timestamp,
        pid: event.pid,
        tid,
        ppid,
        comm: event.comm.clone(),
        summary,
        body,
        observations,
        raw: data.clone(),
    }
}

fn decode_http(data: &Value) -> (SemanticBody, Option<String>) {
    let host = extract_host(data);
    let mut path = data.get("path").and_then(Value::as_str).map(String::from);
    let status_code = data
        .get("status_code")
        .and_then(Value::as_u64)
        .map(|v| v as u16);
    let message_type = data.get("message_type").and_then(Value::as_str);
    let request_id = extract_request_id(data);
    let provider = host.as_deref().map(provider_from_host);

    let body = body_json(data);
    let model = body
        .as_ref()
        .and_then(extract_model)
        .or_else(|| path.as_deref().and_then(extract_model_from_path));
    let path_is_llm = path.as_deref().map(is_llm_path).unwrap_or(false);

    match message_type {
        Some("request") => {
            if path.is_none() {
                path = first_line_token(data, 1);
            }
            if path_is_llm {
                (
                    SemanticBody::LlmRequest(LlmRequest {
                        provider,
                        model,
                        host,
                        path,
                        request_id,
                        body,
                    }),
                    None,
                )
            } else {
                (
                    SemanticBody::HttpRequest(HttpInfo {
                        host,
                        path,
                        status_code,
                    }),
                    None,
                )
            }
        }
        Some("response") => {
            let is_error = status_code.map(|c| c >= 400).unwrap_or(false);
            let body_is_llm = body.as_ref().is_some_and(|body| {
                extract_model(body).is_some() || !extract_token_usage(body).is_empty()
            });
            if path_is_llm || body_is_llm {
                let usage = body.as_ref().map(extract_token_usage).unwrap_or_default();
                (
                    SemanticBody::LlmResponse(LlmResponse {
                        provider,
                        model,
                        host,
                        path,
                        status_code,
                        request_id,
                        is_error,
                        usage,
                        body,
                        tool_uses: Vec::new(),
                    }),
                    None,
                )
            } else {
                (
                    SemanticBody::HttpResponse(HttpInfo {
                        host,
                        path,
                        status_code,
                    }),
                    None,
                )
            }
        }
        _ => (SemanticBody::Other, None),
    }
}

fn decode_sse(data: &Value) -> LlmResponse {
    LlmResponse {
        provider: None,
        model: extract_model_from_sse(data),
        host: None,
        path: None,
        status_code: None,
        request_id: None,
        is_error: false,
        usage: extract_token_usage_from_sse(data),
        // The accumulated SSE payload is the response evidence.
        body: Some(data.clone()),
        tool_uses: decode_sse_tool_uses(data),
    }
}

fn decode_sse_tool_uses(data: &Value) -> Vec<ToolUse> {
    let Some(events) = data.get("sse_events").and_then(Value::as_array) else {
        return Vec::new();
    };
    let mut tool_uses = Vec::new();
    for (idx, sse) in events.iter().enumerate() {
        let Some(block) = sse.pointer("/parsed_data/content_block") else {
            continue;
        };
        if block.get("type").and_then(Value::as_str) != Some("tool_use") {
            continue;
        }
        tool_uses.push(ToolUse {
            index: idx,
            name: block
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or("?")
                .to_string(),
            tool_call_id: block.get("id").and_then(Value::as_str).map(str::to_string),
            input_json: block.get("input").map(Value::to_string),
        });
    }
    tool_uses
}

fn decode_process(data: &Value) -> (SemanticBody, Option<String>) {
    let event_name = data.get("event").and_then(Value::as_str).unwrap_or("");
    match event_name {
        "EXEC" => {
            let info = process_info(data);
            let summary = info.filename.as_deref().map(|f| format!("exec {}", f));
            (SemanticBody::ProcessExec(info), summary)
        }
        "EXIT" => {
            let info = process_info(data);
            let summary = process_exit_summary(data).or_else(|| Some("process exit".to_string()));
            (SemanticBody::ProcessExit(info), summary)
        }
        name if name.contains("FILE_OPEN") => {
            if is_writable_open(data) {
                let write = file_write(data);
                let summary = file_summary(&write);
                (SemanticBody::FileWrite(write), summary)
            } else {
                (SemanticBody::Other, None)
            }
        }
        name if name.contains("FILE_") => {
            let write = file_write(data);
            let summary = file_summary(&write);
            (SemanticBody::FileWrite(write), summary)
        }
        "SUMMARY" if data.get("type").and_then(Value::as_str) == Some("WRITE") => {
            (SemanticBody::FileWrite(file_write(data)), None)
        }
        _ => {
            if let Some(action) = process_network_action(data)
                .filter(|name| name.starts_with("NET_"))
                .map(str::to_string)
            {
                let target = data
                    .get("detail")
                    .or_else(|| data.get("host"))
                    .and_then(Value::as_str)
                    .map(str::to_string);
                (SemanticBody::NetworkOp(NetworkOp { action, target }), None)
            } else {
                (SemanticBody::Other, None)
            }
        }
    }
}

fn process_info(data: &Value) -> ProcessInfo {
    let argv = data
        .get("argv")
        .and_then(Value::as_array)
        .map(|argv| {
            argv.iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let filename = data
        .get("filename")
        .and_then(Value::as_str)
        .map(str::to_string);
    let command = filename
        .clone()
        .or_else(|| {
            data.get("command")
                .and_then(Value::as_str)
                .map(str::to_string)
        })
        .or_else(|| argv.first().cloned());
    ProcessInfo {
        filename,
        command,
        argv,
        cwd: data.get("cwd").and_then(Value::as_str).map(str::to_string),
        exit_code: data.get("exit_code").and_then(Value::as_i64),
    }
}

fn process_exit_summary(data: &Value) -> Option<String> {
    let exit_code = data.get("exit_code").and_then(Value::as_i64)?;
    let mut summary = format!("exit code {}", exit_code);
    if let Some(duration_ms) = data.get("duration_ms").and_then(Value::as_u64) {
        summary.push_str(&format!(" ({}ms)", duration_ms));
    }
    Some(summary)
}

fn file_write(data: &Value) -> FileWrite {
    FileWrite {
        path: data
            .get("path")
            .or_else(|| data.get("filepath"))
            .and_then(Value::as_str)
            .map(str::to_string),
    }
}

fn file_summary(write: &FileWrite) -> Option<String> {
    write.path.as_deref().map(|p| format!("file {}", p))
}

fn is_writable_open(data: &Value) -> bool {
    let flags = data.get("flags").and_then(Value::as_i64).unwrap_or(0);
    const O_ACCMODE: i64 = 0o3;
    const O_CREAT: i64 = 0o100;
    const O_TRUNC: i64 = 0o1000;
    const O_APPEND: i64 = 0o2000;
    (flags & O_ACCMODE) != 0 || (flags & (O_CREAT | O_TRUNC | O_APPEND)) != 0
}

fn process_network_action(data: &Value) -> Option<&str> {
    let event = data.get("event").and_then(Value::as_str)?;
    if event == "SUMMARY" {
        data.get("type").and_then(Value::as_str)
    } else {
        Some(event)
    }
}

fn decode_resource_sample(data: &Value) -> ResourceSample {
    ResourceSample {
        cpu_percent: number_or_string(data.get("cpu").and_then(|v| v.get("percent"))),
        rss_mb: number_or_string(data.get("memory").and_then(|v| v.get("rss_mb"))),
    }
}

fn number_or_string(value: Option<&Value>) -> Option<f64> {
    value.and_then(|v| {
        v.as_f64()
            .or_else(|| v.as_str().and_then(|s| s.parse::<f64>().ok()))
    })
}

fn extract_host(data: &Value) -> Option<String> {
    data.get("host")
        .and_then(Value::as_str)
        .or_else(|| {
            data.get("headers")
                .and_then(|h| h.get("host"))
                .and_then(Value::as_str)
                .or_else(|| {
                    data.get("headers")
                        .and_then(|h| h.get(":authority"))
                        .and_then(Value::as_str)
                })
        })
        .map(String::from)
}

fn extract_request_id(data: &Value) -> Option<String> {
    let direct = data
        .get("request_id")
        .or_else(|| data.get("requestId"))
        .or_else(|| data.get("requestID"))
        .and_then(Value::as_str);
    if let Some(id) = direct {
        return Some(id.to_string());
    }

    let headers = data.get("headers")?.as_object()?;
    [
        "request-id",
        "x-request-id",
        "x-correlation-id",
        "x-amzn-requestid",
        "x-amzn-request-id",
        "x-goog-request-id",
        "x-openai-request-id",
        "anthropic-request-id",
    ]
    .iter()
    .find_map(|name| header_value(headers, name).map(String::from))
}

fn header_value<'a>(headers: &'a serde_json::Map<String, Value>, name: &str) -> Option<&'a str> {
    headers.iter().find_map(|(key, value)| {
        key.eq_ignore_ascii_case(name)
            .then(|| value.as_str())
            .flatten()
    })
}

fn first_line_token(data: &Value, index: usize) -> Option<String> {
    data.get("first_line")
        .and_then(Value::as_str)
        .and_then(|line| line.split_whitespace().nth(index))
        .map(String::from)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn decodes_anthropic_llm_request() {
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
        let semantic = decode_event(&event, "raw-1".to_string());
        let SemanticBody::LlmRequest(req) = &semantic.body else {
            panic!("expected LlmRequest, got {:?}", semantic.body);
        };
        assert_eq!(req.provider.as_deref(), Some("anthropic"));
        assert_eq!(req.model.as_deref(), Some("claude-sonnet-4-20250514"));
        assert_eq!(semantic.tid, Some(7));
        assert_eq!(semantic.event_id, "canon-raw-1");
    }

    #[test]
    fn decodes_sse_response_with_tool_use() {
        let event = Event::new_with_timestamp(
            2,
            "sse_processor".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "sse_events": [
                    {"parsed_data": {"message": {"model": "claude-sonnet", "usage": {"input_tokens": 3}}}},
                    {"parsed_data": {"content_block": {"type": "tool_use", "name": "Bash", "id": "tu_1", "input": {"command": "ls"}}}},
                    {"parsed_data": {"usage": {"output_tokens": 9}}}
                ]
            }),
        );
        let semantic = decode_event(&event, "raw-2".to_string());
        let SemanticBody::LlmResponse(resp) = &semantic.body else {
            panic!("expected LlmResponse");
        };
        assert_eq!(resp.model.as_deref(), Some("claude-sonnet"));
        assert_eq!(resp.usage.input_tokens, 3);
        assert_eq!(resp.usage.output_tokens, 9);
        assert_eq!(resp.tool_uses.len(), 1);
        assert_eq!(resp.tool_uses[0].name, "Bash");
        assert_eq!(resp.tool_uses[0].tool_call_id.as_deref(), Some("tu_1"));
    }

    #[test]
    fn decodes_process_exec_and_exit() {
        let exec = Event::new_with_timestamp(
            3,
            "process".to_string(),
            42,
            "bash".to_string(),
            json!({"event": "EXEC", "filename": "/bin/ls", "argv": ["ls", "-l"], "ppid": 1}),
        );
        let semantic = decode_event(&exec, "raw-3".to_string());
        assert!(matches!(semantic.body, SemanticBody::ProcessExec(_)));
        assert_eq!(semantic.summary.as_deref(), Some("exec /bin/ls"));
        assert_eq!(semantic.ppid, Some(1));

        let exit = Event::new_with_timestamp(
            4,
            "process".to_string(),
            42,
            "bash".to_string(),
            json!({"event": "EXIT", "exit_code": 0, "duration_ms": 12}),
        );
        let semantic = decode_event(&exit, "raw-4".to_string());
        assert!(matches!(semantic.body, SemanticBody::ProcessExit(_)));
        assert_eq!(semantic.summary.as_deref(), Some("exit code 0 (12ms)"));
    }

    #[test]
    fn decodes_claude_telemetry_observations() {
        let event = Event::new_with_timestamp(
            5,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "message_type": "request",
                "path": "/api/v2/logs",
                "headers": { "host": "http-intake.logs.datadoghq.com" },
                "body": "[{\"message\":\"tengu_api_success\",\"model\":\"claude-sonnet\",\"input_tokens\":10,\"output_tokens\":5,\"cached_input_tokens\":2}]"
            }),
        );
        let semantic = decode_event(&event, "raw-5".to_string());
        assert_eq!(semantic.observations.token_usage.len(), 1);
        let usage = &semantic.observations.token_usage[0];
        assert_eq!(usage.provider, "anthropic");
        assert_eq!(usage.usage.total_tokens(), 17);
        assert_eq!(usage.source, "claude_telemetry");
    }

    #[test]
    fn decodes_gemini_stdio_stats() {
        let event = Event::new_with_timestamp(
            6,
            "stdio".to_string(),
            42,
            "gemini".to_string(),
            json!({
                "data": "{\"stats\":{\"models\":{\"gemini-2.5-pro\":{\"tokens\":{\"prompt\":7,\"candidates\":3,\"total\":10}}}}}"
            }),
        );
        let semantic = decode_event(&event, "raw-6".to_string());
        assert_eq!(semantic.observations.token_usage.len(), 1);
        let usage = &semantic.observations.token_usage[0];
        assert_eq!(usage.provider, "gcp.gen_ai");
        assert_eq!(usage.model, "gemini-2.5-pro");
        assert_eq!(usage.usage.total_tokens(), 10);
    }
}
