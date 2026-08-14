// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Reassembles newline-delimited JSON-RPC messages captured from local MCP
//! stdio streams.
//!
//! `stdiocap` observes read/write syscalls, so one JSON-RPC message may be
//! split across several events and one event may contain several messages.
//! This analyzer keeps a bounded buffer per process/fd/direction and emits one
//! enriched event per complete JSON-RPC object.

use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_stream::stream;
use async_trait::async_trait;
use futures::StreamExt;
use serde_json::{Map, Value};
use std::collections::HashMap;

const DEFAULT_MAX_BUFFER_BYTES: usize = 1 << 20;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct StdioStreamKey {
    pid: u32,
    fd: String,
    direction: String,
}

pub struct McpStdioAnalyzer {
    buffers: HashMap<StdioStreamKey, String>,
    max_buffer_bytes: usize,
}

impl McpStdioAnalyzer {
    pub fn new() -> Self {
        Self {
            buffers: HashMap::new(),
            max_buffer_bytes: DEFAULT_MAX_BUFFER_BYTES,
        }
    }

    #[cfg(test)]
    fn with_max_buffer_bytes(mut self, max_buffer_bytes: usize) -> Self {
        self.max_buffer_bytes = max_buffer_bytes;
        self
    }

    fn decode_event(
        event: Event,
        buffers: &mut HashMap<StdioStreamKey, String>,
        max_buffer_bytes: usize,
    ) -> Vec<Event> {
        if event.source != "stdio" && event.source != "stdiocap" {
            return vec![event];
        }

        let Some(payload) = event.data.get("data").and_then(Value::as_str) else {
            return vec![event];
        };
        let Some(key) = stream_key(&event) else {
            return vec![event];
        };
        if event
            .data
            .get("truncated")
            .and_then(Value::as_bool)
            .unwrap_or(false)
        {
            buffers.remove(&key);
            return vec![event];
        }

        let oversized = {
            let buffer = buffers.entry(key.clone()).or_default();
            buffer.push_str(payload);
            buffer.len() > max_buffer_bytes
        };
        if oversized {
            buffers.remove(&key);
            return vec![event];
        }

        let mut messages = Vec::new();
        let buffer = buffers.get_mut(&key).expect("buffer inserted above");
        while let Some(newline) = buffer.find('\n') {
            let line = buffer[..newline].trim_end_matches('\r').trim().to_string();
            buffer.drain(..=newline);
            if line.is_empty() {
                continue;
            }
            let Ok(value) = serde_json::from_str::<Value>(&line) else {
                continue;
            };
            if value.is_object() {
                messages.push(enriched_event(&event, &line, value));
            }
        }

        if messages.is_empty() {
            return vec![event];
        }
        messages
    }
}

impl Default for McpStdioAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl Analyzer for McpStdioAnalyzer {
    async fn process(&mut self, mut stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let mut buffers = std::mem::take(&mut self.buffers);
        let max_buffer_bytes = self.max_buffer_bytes.max(1);
        let processed = stream! {
            while let Some(event) = stream.next().await {
                for event in Self::decode_event(event, &mut buffers, max_buffer_bytes) {
                    yield event;
                }
            }
        };
        Ok(Box::pin(processed))
    }
}

fn stream_key(event: &Event) -> Option<StdioStreamKey> {
    let fd = event
        .data
        .get("fd")
        .map(Value::to_string)
        .or_else(|| event.data.get("fd_role").map(Value::to_string))?;
    Some(StdioStreamKey {
        pid: event.pid,
        fd,
        direction: event
            .data
            .get("direction")
            .and_then(Value::as_str)
            .unwrap_or("unknown")
            .to_ascii_uppercase(),
    })
}

fn enriched_event(event: &Event, raw: &str, payload: Value) -> Event {
    let mut data = match event.data.clone() {
        Value::Object(data) => data,
        _ => Map::new(),
    };
    let kind = rpc_kind(&payload);
    let method = payload.get("method").and_then(Value::as_str);
    let id = payload
        .get("id")
        .filter(|id| !id.is_null())
        .map(stringify_rpc_id);
    let tool_name = payload
        .pointer("/params/name")
        .and_then(Value::as_str)
        .filter(|name| !name.is_empty());

    data.insert("data".to_string(), Value::String(raw.to_string()));
    data.insert("len".to_string(), Value::from(raw.len()));
    data.insert("buf_size".to_string(), Value::from(raw.len()));
    data.insert("rpc_kind".to_string(), Value::String(kind.to_string()));
    data.insert("rpc_payload".to_string(), payload);
    if let Some(method) = method {
        data.insert("rpc_method".to_string(), Value::String(method.to_string()));
    }
    if let Some(id) = id {
        data.insert("rpc_id".to_string(), Value::String(id.clone()));
        data.insert("request_id".to_string(), Value::String(id));
    }
    if let Some(tool_name) = tool_name {
        data.insert(
            "rpc_tool_name".to_string(),
            Value::String(tool_name.to_string()),
        );
    }
    if let Some(direction) = event.data.get("direction").cloned() {
        data.insert("rpc_direction".to_string(), direction);
    }

    Event {
        data: Value::Object(data),
        ..event.clone()
    }
}

fn rpc_kind(payload: &Value) -> &'static str {
    if payload.get("method").and_then(Value::as_str).is_some() {
        if payload.get("id").is_some_and(|id| !id.is_null()) {
            "request"
        } else {
            "notification"
        }
    } else if payload.get("result").is_some() {
        "response"
    } else if payload.get("error").is_some() {
        "error"
    } else {
        "unknown"
    }
}

fn stringify_rpc_id(value: &Value) -> String {
    value
        .as_str()
        .map(str::to_string)
        .unwrap_or_else(|| value.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use futures::stream;
    use serde_json::json;

    fn event(timestamp: u64, data: &str) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "stdio".to_string(),
            42,
            "mcp-server".to_string(),
            json!({
                "direction": "READ",
                "fd": 0,
                "fd_role": "stdin",
                "data": data,
                "len": data.len(),
                "truncated": false,
            }),
        )
    }

    #[tokio::test]
    async fn reassembles_fragmented_and_coalesced_json_rpc() {
        let input = vec![
            event(1, r#"{"jsonrpc":"2.0","id":1,"method":"tools/c"#),
            event(
                2,
                concat!(
                    r#"all","params":{"name":"echo","arguments":{"text":"hi"}}}"#,
                    "\n",
                    r#"{"jsonrpc":"2.0","id":1,"result":{}}"#,
                    "\n",
                ),
            ),
        ];
        let mut analyzer = McpStdioAnalyzer::new();
        let output = analyzer
            .process(Box::pin(stream::iter(input)))
            .await
            .unwrap()
            .collect::<Vec<_>>()
            .await;
        let rpc = output
            .iter()
            .filter(|event| event.data.get("rpc_kind").is_some())
            .collect::<Vec<_>>();

        assert_eq!(rpc.len(), 2);
        assert_eq!(rpc[0].data["rpc_method"], "tools/call");
        assert_eq!(rpc[0].data["rpc_tool_name"], "echo");
        assert_eq!(rpc[1].data["rpc_kind"], "response");
        assert_eq!(rpc[1].data["rpc_id"], "1");
    }

    #[tokio::test]
    async fn keeps_capture_safe_when_a_message_is_truncated_or_oversized() {
        let mut truncated = event(1, "{\"jsonrpc\":\"2.0\"}");
        truncated.data["truncated"] = json!(true);
        let oversized = event(2, "0123456789");
        let mut analyzer = McpStdioAnalyzer::new().with_max_buffer_bytes(4);
        let output = analyzer
            .process(Box::pin(stream::iter(vec![truncated, oversized])))
            .await
            .unwrap()
            .collect::<Vec<_>>()
            .await;

        assert_eq!(output.len(), 2);
        assert!(output.iter().all(|event| event.data.get("rpc_kind").is_none()));
    }
}
