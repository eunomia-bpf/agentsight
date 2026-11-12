// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::{Value, json};
use std::collections::{BTreeMap, HashMap};
use std::sync::{Arc, Mutex};

use super::protocol_events::SSEProcessorEvent;

const MAX_BUFFERS: usize = 1024;

pub struct SSEProcessor {
    sse_buffers: Arc<Mutex<HashMap<String, SSEAccumulator>>>,
    timeout_ms: u64,
    max_buffers: usize,
}

impl Default for SSEProcessor {
    fn default() -> Self {
        Self::new_with_timeout(30_000)
    }
}

struct SSEAccumulator {
    message_id: Option<String>,
    accumulated_text: String,
    accumulated_json: String,
    openai_reasoning: String,
    openai_tool_calls: BTreeMap<u64, OpenAIToolCallAccumulator>,
    events: Vec<SSEEvent>,
    is_complete: bool,
    last_update: u64,
    has_message_start: bool,
    start_time: u64,
    end_time: u64,
}

#[derive(Clone, Debug, Default)]
struct OpenAIToolCallAccumulator {
    id: Option<String>,
    type_name: Option<String>,
    function_name: Option<String>,
    function_arguments: String,
}

#[derive(Clone, Debug)]
pub struct SSEEvent {
    pub event: Option<String>,
    pub data: Option<String>,
    pub id: Option<String>,
    pub parsed_data: Option<Value>,
    pub raw_data: Option<String>,
}

impl SSEProcessor {
    #[cfg(test)]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn new_with_timeout(timeout_ms: u64) -> Self {
        SSEProcessor {
            sse_buffers: Arc::new(Mutex::new(HashMap::new())),
            timeout_ms,
            max_buffers: MAX_BUFFERS,
        }
    }

    pub fn is_sse_data(data: &str) -> bool {
        let has_sse_patterns = data.contains("event:") && data.contains("data:");
        let has_sse_content_type = data.contains("text/event-stream");
        let has_chunked_sse = data.contains("Transfer-Encoding: chunked")
            && (data.contains("event:") || data.contains("data:"));
        let has_sse_data_only =
            data.contains("data:") && (data.contains("\r\n\r\n") || data.contains("\n\n"));
        has_sse_patterns || has_sse_content_type || has_chunked_sse || has_sse_data_only
    }

    pub fn parse_sse_events_from_chunk(chunk_content: &str) -> Vec<SSEEvent> {
        let mut events = Vec::new();
        let normalized = chunk_content.replace("\r\n", "\n");
        let event_blocks: Vec<&str> = normalized.split("\n\n").collect();

        for block in event_blocks {
            if block.trim().is_empty() {
                continue;
            }

            let mut event = SSEEvent {
                event: None,
                data: None,
                id: None,
                parsed_data: None,
                raw_data: None,
            };
            let mut data_lines = Vec::new();

            for line in block.split('\n') {
                let line = line.trim();
                if let Some(rest) = line.strip_prefix("event:") {
                    event.event = Some(rest.trim().to_string());
                } else if let Some(rest) = line.strip_prefix("data:") {
                    data_lines.push(rest.trim());
                } else if let Some(rest) = line.strip_prefix("id:") {
                    event.id = Some(rest.trim().to_string());
                }
            }

            if !data_lines.is_empty() {
                let combined_data = data_lines.join("\n");
                event.data = Some(combined_data.clone());
                match serde_json::from_str::<Value>(&combined_data) {
                    Ok(parsed_json) => {
                        event.parsed_data = Some(parsed_json);
                    }
                    Err(_) => {
                        event.raw_data = Some(combined_data);
                    }
                }
            }

            if event.event.is_some() || event.data.is_some() {
                events.push(event);
            }
        }

        events
    }

    pub fn parse_sse_events(data: &str) -> Vec<SSEEvent> {
        let clean_data = Self::clean_chunked_content(data);
        let sse_data = if clean_data.trim().is_empty() {
            data
        } else {
            clean_data.as_str()
        };
        Self::parse_sse_events_from_chunk(sse_data)
    }

    fn sse_payload(event: &Event) -> Option<(&str, bool)> {
        if event.source == "ssl" {
            return event
                .data
                .get("data")
                .and_then(|v| v.as_str())
                .map(|data| (data, true));
        }

        if event.source != "http_parser"
            || event.data.get("message_type").and_then(|v| v.as_str()) != Some("response")
        {
            return None;
        }

        let body = event.data.get("body").and_then(|v| v.as_str())?;
        (Self::http_content_type_is_sse(&event.data) || Self::is_sse_data(body))
            .then_some((body, false))
    }

    fn http_content_type_is_sse(data: &Value) -> bool {
        let Some(headers) = data.get("headers").and_then(|v| v.as_object()) else {
            return false;
        };
        headers.iter().any(|(key, value)| {
            key.eq_ignore_ascii_case("content-type")
                && value
                    .as_str()
                    .is_some_and(|v| v.to_ascii_lowercase().contains("text/event-stream"))
        })
    }

    fn parse_usage_metadata_fragment(data: &str) -> Option<SSEEvent> {
        let usage = extract_json_object_after_key(data, "\"usageMetadata\"")?;
        let usage_json: Value = serde_json::from_str(usage).ok()?;
        let has_tokens = usage_json.get("promptTokenCount").is_some()
            || usage_json.get("candidatesTokenCount").is_some()
            || usage_json.get("totalTokenCount").is_some();
        if !has_tokens {
            return None;
        }

        let mut parsed = serde_json::Map::new();
        parsed.insert("usageMetadata".to_string(), usage_json);
        if let Some(model) = extract_json_string_field(data, "modelVersion")
            .or_else(|| extract_json_string_field(data, "model"))
        {
            parsed.insert("modelVersion".to_string(), Value::String(model));
        }

        Some(SSEEvent {
            event: Some("message_stop".to_string()),
            data: None,
            id: None,
            parsed_data: Some(Value::Object(parsed)),
            raw_data: None,
        })
    }

    pub fn clean_chunked_content(content: &str) -> String {
        let mut content_parts = Vec::new();
        let lines: Vec<&str> = content.split("\r\n").collect();

        let mut i = 0;
        while i < lines.len() {
            let line = lines[i].trim();
            if !line.is_empty() && line.chars().all(|c| c.is_ascii_hexdigit()) {
                let chunk_size = u32::from_str_radix(line, 16).unwrap_or(0);
                if chunk_size == 0 {
                    break;
                }
                i += 1;
                if i < lines.len() {
                    content_parts.push(lines[i]);
                }
            }
            i += 1;
        }

        content_parts.join("\n")
    }

    fn generate_connection_id(event: &Event, sse_events: &[SSEEvent]) -> String {
        let pid = event.data.get("pid").and_then(|v| v.as_u64()).unwrap_or(0);
        let tid = event.data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);

        if let Some(message_id) = Self::extract_message_id(sse_events) {
            return format!("{}:{}:{}", pid, tid, message_id);
        }

        let timestamp = event.timestamp;
        let window = timestamp / 600_000_000_000;
        format!("{}:{}:{}", pid, tid, window)
    }

    fn extract_message_id(events: &[SSEEvent]) -> Option<String> {
        for event in events {
            if let Some(event_type) = &event.event
                && event_type == "message_start"
                && let Some(parsed_data) = &event.parsed_data
                && let Some(message) = parsed_data.get("message")
                && let Some(id) = message.get("id")
                && let Some(id_str) = id.as_str()
            {
                return Some(id_str.to_string());
            }
        }
        for event in events {
            if let Some(parsed_data) = &event.parsed_data
                && let Some(id) = parsed_data.get("id").and_then(|id| id.as_str())
            {
                return Some(id.to_string());
            }
            if let Some(parsed_data) = &event.parsed_data {
                if let Some(id) = parsed_data.get("response_id").and_then(|id| id.as_str()) {
                    return Some(id.to_string());
                }
                if let Some(id) = parsed_data
                    .get("response")
                    .and_then(|response| response.get("id"))
                    .and_then(|id| id.as_str())
                {
                    return Some(id.to_string());
                }
            }
        }
        None
    }

    fn is_sse_complete(accumulator: &SSEAccumulator) -> bool {
        for event in &accumulator.events {
            if Self::sse_event_completes_stream(event) {
                return true;
            }
            if let Some(event_type) = &event.event {
                match event_type.as_str() {
                    "message_stop" => return true,
                    "error" => return true,
                    _ => {}
                }
            }
        }
        accumulator.accumulated_text.len() > 50000 || accumulator.accumulated_json.len() > 50000
    }

    fn has_meaningful_content(accumulator: &SSEAccumulator) -> bool {
        if !accumulator.accumulated_text.is_empty() || !accumulator.accumulated_json.is_empty() {
            return true;
        }
        if !accumulator.openai_reasoning.is_empty() || !accumulator.openai_tool_calls.is_empty() {
            return true;
        }

        let mut has_content_deltas = false;
        let mut has_message_start = false;
        let mut metadata_only_count = 0;

        for event in &accumulator.events {
            if Self::sse_event_has_usage(event) {
                return true;
            }
            if Self::sse_event_has_openai_delta(event) || Self::sse_event_has_terminal_finish(event)
            {
                return true;
            }
            if Self::sse_event_has_openai_response_delta(event)
                || Self::sse_event_has_openai_response_terminal(event)
            {
                return true;
            }
            if let Some(event_type) = &event.event {
                match event_type.as_str() {
                    "content_block_delta" => has_content_deltas = true,
                    "message_start" => has_message_start = true,
                    "message_stop"
                    | "message_delta"
                    | "ping"
                    | "content_block_stop"
                    | "content_block_start" => {
                        metadata_only_count += 1;
                    }
                    _ => {}
                }
            }
        }

        has_content_deltas
            || (has_message_start
                && accumulator.events.len() > 3
                && metadata_only_count < accumulator.events.len())
    }

    fn sse_event_has_usage(event: &SSEEvent) -> bool {
        event
            .parsed_data
            .as_ref()
            .is_some_and(|data| Self::meaningful_usage(data).is_some())
    }

    fn sse_event_completes_stream(event: &SSEEvent) -> bool {
        event.data.as_deref() == Some("[DONE]")
            || event.parsed_data.as_ref().is_some_and(|data| {
                Self::has_stream_completing_usage(data) || Self::has_openai_response_terminal(data)
            })
    }

    fn has_stream_completing_usage(data: &Value) -> bool {
        [
            data.get("usageMetadata"),
            data.get("usage"),
            data.get("response")
                .and_then(|response| response.get("usage")),
        ]
        .into_iter()
        .flatten()
        .any(Self::usage_has_meaningful_fields)
    }

    fn meaningful_usage(data: &Value) -> Option<&Value> {
        [
            data.get("usageMetadata"),
            data.get("usage"),
            data.get("message").and_then(|m| m.get("usage")),
            data.get("response")
                .and_then(|response| response.get("usage")),
        ]
        .into_iter()
        .flatten()
        .find(|usage| Self::usage_has_meaningful_fields(usage))
    }

    fn usage_has_meaningful_fields(usage: &Value) -> bool {
        usage
            .as_object()
            .is_some_and(|fields| fields.values().any(|value| !value.is_null()))
    }

    fn sse_event_has_openai_delta(event: &SSEEvent) -> bool {
        event
            .parsed_data
            .as_ref()
            .and_then(|data| data.get("choices"))
            .and_then(|choices| choices.as_array())
            .is_some_and(|choices| {
                choices.iter().any(|choice| {
                    choice
                        .get("delta")
                        .and_then(|delta| delta.as_object())
                        .is_some_and(|delta| {
                            delta
                                .get("content")
                                .and_then(|v| v.as_str())
                                .is_some_and(|v| !v.is_empty())
                                || delta
                                    .get("tool_calls")
                                    .and_then(|v| v.as_array())
                                    .is_some_and(|v| !v.is_empty())
                                || delta.get("function_call").is_some()
                                || Self::openai_reasoning_delta(delta).is_some()
                        })
                })
            })
    }

    fn sse_event_has_openai_response_delta(event: &SSEEvent) -> bool {
        event
            .parsed_data
            .as_ref()
            .is_some_and(Self::has_openai_response_delta)
    }

    fn has_openai_response_delta(data: &Value) -> bool {
        matches!(
            Self::openai_response_event_type(data),
            Some(
                "response.output_text.delta"
                    | "response.reasoning_text.delta"
                    | "response.reasoning_summary_text.delta"
                    | "response.function_call_arguments.delta"
                    | "response.function_call_arguments.done"
                    | "response.output_item.added"
                    | "response.output_item.done"
            )
        )
    }

    fn sse_event_has_terminal_finish(event: &SSEEvent) -> bool {
        event
            .parsed_data
            .as_ref()
            .is_some_and(Self::has_terminal_finish_reason)
    }

    fn has_terminal_finish_reason(data: &Value) -> bool {
        data.get("choices")
            .and_then(|choices| choices.as_array())
            .is_some_and(|choices| {
                choices.iter().any(|choice| {
                    choice
                        .get("finish_reason")
                        .is_some_and(|reason| !reason.is_null())
                })
            })
    }

    fn sse_event_has_openai_response_terminal(event: &SSEEvent) -> bool {
        event
            .parsed_data
            .as_ref()
            .is_some_and(Self::has_openai_response_terminal)
    }

    fn has_openai_response_terminal(data: &Value) -> bool {
        matches!(
            Self::openai_response_event_type(data),
            Some(
                "response.completed"
                    | "response.failed"
                    | "response.incomplete"
                    | "response.cancelled"
            )
        )
    }

    fn openai_response_event_type(data: &Value) -> Option<&str> {
        data.get("type")
            .and_then(|value| value.as_str())
            .filter(|value| value.starts_with("response."))
    }

    fn openai_reasoning_delta(delta: &serde_json::Map<String, Value>) -> Option<&str> {
        [
            "reasoning_content",
            "reasoning",
            "reasoning_text",
            "thinking",
        ]
        .into_iter()
        .find_map(|key| delta.get(key).and_then(|v| v.as_str()))
        .filter(|value| !value.is_empty())
    }

    fn accumulate_content(accumulator: &mut SSEAccumulator, events: &[SSEEvent]) {
        for event in events {
            accumulator.events.push(event.clone());

            if accumulator.message_id.is_none() {
                accumulator.message_id = Self::extract_message_id(std::slice::from_ref(event));
            }

            if let Some(event_type) = &event.event {
                match event_type.as_str() {
                    "message_start" => {
                        accumulator.has_message_start = true;
                        if accumulator.message_id.is_none() {
                            accumulator.message_id =
                                Self::extract_message_id(std::slice::from_ref(event));
                        }
                    }
                    "content_block_delta" => {
                        if let Some(parsed_data) = &event.parsed_data
                            && let Some(delta) = parsed_data.get("delta")
                        {
                            let delta_type = delta.get("type").and_then(|v| v.as_str());
                            let text = if delta_type == Some("text_delta") {
                                delta.get("text").and_then(|v| v.as_str())
                            } else if delta_type == Some("thinking_delta") {
                                delta.get("thinking").and_then(|v| v.as_str())
                            } else {
                                None
                            };
                            if let Some(t) = text {
                                accumulator.accumulated_text.push_str(t);
                            }
                            if let Some(partial_json) =
                                delta.get("partial_json").and_then(|v| v.as_str())
                            {
                                accumulator.accumulated_json.push_str(partial_json);
                            }
                        }
                    }
                    _ => {}
                }
            }
            if let Some(parsed_data) = &event.parsed_data {
                Self::accumulate_openai_content(accumulator, parsed_data);
                Self::accumulate_openai_responses_content(accumulator, parsed_data);
            }
        }
    }

    fn accumulate_openai_content(accumulator: &mut SSEAccumulator, data: &Value) {
        let Some(choices) = data.get("choices").and_then(|choices| choices.as_array()) else {
            return;
        };
        for choice in choices {
            let Some(delta) = choice.get("delta").and_then(|delta| delta.as_object()) else {
                continue;
            };
            if let Some(content) = delta.get("content").and_then(|v| v.as_str()) {
                accumulator.accumulated_text.push_str(content);
            }
            if let Some(reasoning) = Self::openai_reasoning_delta(delta) {
                accumulator.openai_reasoning.push_str(reasoning);
            }
            if let Some(tool_calls) = delta.get("tool_calls").and_then(|v| v.as_array()) {
                for (fallback_index, tool_call) in tool_calls.iter().enumerate() {
                    Self::accumulate_openai_tool_call(
                        accumulator,
                        tool_call,
                        fallback_index as u64,
                    );
                }
            }
            if let Some(function_call) = delta.get("function_call") {
                Self::accumulate_openai_function_call(accumulator, function_call);
            }
        }
    }

    fn accumulate_openai_responses_content(accumulator: &mut SSEAccumulator, data: &Value) {
        match Self::openai_response_event_type(data) {
            Some("response.output_text.delta") => {
                if let Some(delta) = data.get("delta").and_then(|value| value.as_str()) {
                    accumulator.accumulated_text.push_str(delta);
                }
            }
            Some("response.reasoning_text.delta" | "response.reasoning_summary_text.delta") => {
                if let Some(delta) = data.get("delta").and_then(|value| value.as_str()) {
                    accumulator.openai_reasoning.push_str(delta);
                }
            }
            Some("response.function_call_arguments.delta") => {
                Self::accumulate_openai_response_function_arguments(accumulator, data, false);
            }
            Some("response.function_call_arguments.done") => {
                Self::accumulate_openai_response_function_arguments(accumulator, data, true);
            }
            Some("response.output_item.added" | "response.output_item.done") => {
                Self::accumulate_openai_response_item(accumulator, data);
            }
            _ => {}
        }
    }

    fn accumulate_openai_response_item(accumulator: &mut SSEAccumulator, data: &Value) {
        let Some(item) = data.get("item").and_then(|value| value.as_object()) else {
            return;
        };
        if item.get("type").and_then(|value| value.as_str()) != Some("function_call") {
            return;
        }
        let index = data
            .get("output_index")
            .and_then(|value| value.as_u64())
            .unwrap_or(accumulator.openai_tool_calls.len() as u64);
        let entry = accumulator.openai_tool_calls.entry(index).or_default();
        entry
            .type_name
            .get_or_insert_with(|| "function".to_string());
        if let Some(id) = item.get("id").and_then(|value| value.as_str()) {
            entry.id = Some(id.to_string());
        } else if let Some(id) = item.get("call_id").and_then(|value| value.as_str()) {
            entry.id = Some(id.to_string());
        }
        if let Some(name) = item.get("name").and_then(|value| value.as_str()) {
            entry.function_name = Some(name.to_string());
        }
        if let Some(arguments) = item.get("arguments").and_then(|value| value.as_str()) {
            entry.function_arguments = arguments.to_string();
        }
    }

    fn accumulate_openai_response_function_arguments(
        accumulator: &mut SSEAccumulator,
        data: &Value,
        replace: bool,
    ) {
        let index = data
            .get("output_index")
            .and_then(|value| value.as_u64())
            .unwrap_or(0);
        let entry = accumulator.openai_tool_calls.entry(index).or_default();
        entry
            .type_name
            .get_or_insert_with(|| "function".to_string());
        if let Some(id) = data.get("item_id").and_then(|value| value.as_str()) {
            entry.id = Some(id.to_string());
        }
        let payload_key = if replace { "arguments" } else { "delta" };
        if let Some(arguments) = data.get(payload_key).and_then(|value| value.as_str()) {
            if replace {
                entry.function_arguments = arguments.to_string();
            } else {
                entry.function_arguments.push_str(arguments);
            }
        }
    }

    fn accumulate_openai_tool_call(
        accumulator: &mut SSEAccumulator,
        tool_call: &Value,
        fallback_index: u64,
    ) {
        let index = tool_call
            .get("index")
            .and_then(|v| v.as_u64())
            .unwrap_or(fallback_index);
        let entry = accumulator.openai_tool_calls.entry(index).or_default();
        if let Some(id) = tool_call.get("id").and_then(|v| v.as_str()) {
            entry.id = Some(id.to_string());
        }
        if let Some(type_name) = tool_call.get("type").and_then(|v| v.as_str()) {
            entry.type_name = Some(type_name.to_string());
        }
        if let Some(function) = tool_call.get("function").and_then(|v| v.as_object()) {
            if let Some(name) = function.get("name").and_then(|v| v.as_str()) {
                entry.function_name = Some(name.to_string());
            }
            if let Some(arguments) = function.get("arguments").and_then(|v| v.as_str()) {
                entry.function_arguments.push_str(arguments);
            }
        }
    }

    fn accumulate_openai_function_call(accumulator: &mut SSEAccumulator, function_call: &Value) {
        let entry = accumulator.openai_tool_calls.entry(0).or_default();
        entry
            .type_name
            .get_or_insert_with(|| "function".to_string());
        if let Some(name) = function_call.get("name").and_then(|v| v.as_str()) {
            entry.function_name = Some(name.to_string());
        }
        if let Some(arguments) = function_call.get("arguments").and_then(|v| v.as_str()) {
            entry.function_arguments.push_str(arguments);
        }
    }

    fn create_merged_event(
        connection_id: String,
        accumulator: &SSEAccumulator,
        original_event: &Event,
    ) -> Event {
        let json_content = Self::merged_json_content(accumulator);

        let text_content = accumulator.accumulated_text.clone();

        let sse_events_json: Vec<Value> = accumulator
            .events
            .iter()
            .map(|e| {
                json!({
                    "event": e.event,
                    "data": e.data,
                    "id": e.id,
                    "parsed_data": e.parsed_data,
                    "raw_data": e.raw_data
                })
            })
            .collect();

        let total_size = json_content.len() + text_content.len();

        SSEProcessorEvent {
            connection_id,
            message_id: accumulator.message_id.clone(),
            start_time: accumulator.start_time,
            end_time: accumulator.end_time,
            duration_ns: accumulator.end_time.saturating_sub(accumulator.start_time),
            original_source: original_event.source.clone(),
            host: Self::event_host(original_event),
            method: original_event
                .data
                .get("method")
                .and_then(|v| v.as_str())
                .map(str::to_string),
            path: original_event
                .data
                .get("path")
                .and_then(|v| v.as_str())
                .map(str::to_string),
            status_code: original_event
                .data
                .get("status_code")
                .and_then(|v| v.as_u64())
                .map(|v| v as u16),
            function: original_event
                .data
                .get("function")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown")
                .to_string(),
            tid: original_event
                .data
                .get("tid")
                .and_then(|v| v.as_u64())
                .unwrap_or(0),
            json_content,
            text_content,
            total_size,
            event_count: accumulator.events.len(),
            has_message_start: accumulator.has_message_start,
            sse_events: sse_events_json,
        }
        .to_event(original_event)
    }

    fn merged_json_content(accumulator: &SSEAccumulator) -> String {
        let has_openai_json =
            !accumulator.openai_reasoning.is_empty() || !accumulator.openai_tool_calls.is_empty();
        if !has_openai_json {
            return Self::formatted_accumulated_json(&accumulator.accumulated_json);
        }

        let mut merged = serde_json::Map::new();
        if !accumulator.accumulated_json.is_empty() {
            match serde_json::from_str::<Value>(&accumulator.accumulated_json) {
                Ok(parsed_json) => {
                    merged.insert("partial_json".to_string(), parsed_json);
                }
                Err(_) => {
                    merged.insert(
                        "partial_json".to_string(),
                        Value::String(accumulator.accumulated_json.clone()),
                    );
                }
            }
        }
        if !accumulator.openai_reasoning.is_empty() {
            merged.insert(
                "reasoning_content".to_string(),
                Value::String(accumulator.openai_reasoning.clone()),
            );
        }
        if !accumulator.openai_tool_calls.is_empty() {
            let tool_calls = accumulator
                .openai_tool_calls
                .iter()
                .map(|(index, tool_call)| {
                    json!({
                        "index": index,
                        "id": tool_call.id,
                        "type": tool_call.type_name,
                        "function": {
                            "name": tool_call.function_name,
                            "arguments": tool_call.function_arguments,
                        }
                    })
                })
                .collect::<Vec<_>>();
            merged.insert("tool_calls".to_string(), Value::Array(tool_calls));
        }
        if merged.is_empty() {
            String::new()
        } else {
            serde_json::to_string_pretty(&Value::Object(merged)).unwrap_or_default()
        }
    }

    fn formatted_accumulated_json(json_content: &str) -> String {
        if json_content.is_empty() {
            String::new()
        } else if let Ok(parsed_json) = serde_json::from_str::<Value>(json_content) {
            serde_json::to_string_pretty(&parsed_json).unwrap_or_else(|_| json_content.to_string())
        } else {
            json_content.to_string()
        }
    }

    fn event_host(event: &Event) -> Option<String> {
        event
            .data
            .get("host")
            .and_then(|v| v.as_str())
            .or_else(|| {
                event
                    .data
                    .get("headers")
                    .and_then(|headers| headers.as_object())
                    .and_then(|headers| {
                        headers.iter().find_map(|(key, value)| {
                            (key.eq_ignore_ascii_case("host") || key == ":authority")
                                .then(|| value.as_str())
                                .flatten()
                        })
                    })
            })
            .map(str::to_string)
    }

    fn evict_over_capacity(buffers: &mut HashMap<String, SSEAccumulator>, max: usize) {
        while buffers.len() > max {
            let oldest_key = buffers
                .iter()
                .min_by_key(|(_, acc)| acc.last_update)
                .map(|(k, _)| k.clone());
            if let Some(key) = oldest_key {
                buffers.remove(&key);
            } else {
                break;
            }
        }
    }
}

#[async_trait]
impl Analyzer for SSEProcessor {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let sse_buffers = Arc::clone(&self.sse_buffers);
        let timeout_ms = self.timeout_ms;
        let max_buffers = self.max_buffers;

        let processed_stream = stream.filter_map(move |event| {
            let buffers = Arc::clone(&sse_buffers);

            async move {
                let Some((data_str, allow_json_fragment)) = Self::sse_payload(&event) else {
                    return Some(event);
                };

                let sse_events = if Self::is_sse_data(data_str) {
                    Self::parse_sse_events(data_str)
                } else if allow_json_fragment
                    && let Some(event) = Self::parse_usage_metadata_fragment(data_str)
                {
                    vec![event]
                } else {
                    return Some(event);
                };
                if sse_events.is_empty() {
                    return Some(event);
                }

                let has_content_potential = sse_events.iter().any(|sse_event| {
                    if let Some(event_type) = &sse_event.event {
                        !matches!(event_type.as_str(), "message_delta" | "ping")
                    } else {
                        true
                    }
                });

                let should_skip_chunk = !has_content_potential
                    && sse_events.iter().all(|e| {
                        e.event
                            .as_deref()
                            .is_some_and(|t| matches!(t, "ping" | "message_delta"))
                    });

                if should_skip_chunk {
                    let connection_id = Self::generate_connection_id(&event, &sse_events);
                    let buffers_lock = buffers.lock().unwrap();
                    let has_existing = buffers_lock.contains_key(&connection_id);
                    drop(buffers_lock);
                    if !has_existing {
                        return None;
                    }
                }

                let connection_id = Self::generate_connection_id(&event, &sse_events);

                let mut buffers_lock = buffers.lock().unwrap();

                buffers_lock
                    .retain(|_, acc| event.timestamp.saturating_sub(acc.last_update) <= timeout_ms);
                Self::evict_over_capacity(&mut buffers_lock, max_buffers);

                let mut final_connection_id = connection_id.clone();

                if let Some(message_id) = Self::extract_message_id(&sse_events) {
                    let pid = event.data.get("pid").and_then(|v| v.as_u64()).unwrap_or(0);
                    let tid = event.data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
                    final_connection_id = format!("{}:{}:{}", pid, tid, message_id);
                } else {
                    let pid = event.data.get("pid").and_then(|v| v.as_u64()).unwrap_or(0);
                    let tid = event.data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
                    let conn_prefix = format!("{}:{}:", pid, tid);

                    for (existing_id, accumulator) in buffers_lock.iter() {
                        if existing_id.starts_with(&conn_prefix) && !accumulator.is_complete {
                            let has_message_stop = accumulator
                                .events
                                .iter()
                                .any(|e| e.event.as_deref() == Some("message_stop"));
                            if !has_message_stop {
                                final_connection_id = existing_id.clone();
                                break;
                            }
                        }
                    }
                }

                let accumulator = buffers_lock
                    .entry(final_connection_id.clone())
                    .or_insert_with(|| SSEAccumulator {
                        message_id: None,
                        accumulated_text: String::new(),
                        accumulated_json: String::new(),
                        openai_reasoning: String::new(),
                        openai_tool_calls: BTreeMap::new(),
                        events: Vec::new(),
                        is_complete: false,
                        last_update: event.timestamp,
                        has_message_start: false,
                        start_time: event.timestamp,
                        end_time: event.timestamp,
                    });

                accumulator.last_update = event.timestamp;
                accumulator.end_time = event.timestamp;

                Self::accumulate_content(accumulator, &sse_events);

                let terminal_finish_completes_http_body = !allow_json_fragment
                    && sse_events.iter().any(Self::sse_event_has_terminal_finish);

                if Self::is_sse_complete(accumulator) || terminal_finish_completes_http_body {
                    let result_event = if Self::has_meaningful_content(accumulator) {
                        Some(Self::create_merged_event(
                            final_connection_id.clone(),
                            accumulator,
                            &event,
                        ))
                    } else {
                        None
                    };

                    buffers_lock.remove(&final_connection_id);
                    drop(buffers_lock);

                    result_event
                } else {
                    None
                }
            }
        });

        Ok(Box::pin(processed_stream))
    }
}

fn extract_json_object_after_key<'a>(text: &'a str, key: &str) -> Option<&'a str> {
    let key_index = text.find(key)?;
    let object_start = text[key_index..].find('{')? + key_index;
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escape = false;

    for (offset, ch) in text[object_start..].char_indices() {
        if in_string {
            if escape {
                escape = false;
            } else if ch == '\\' {
                escape = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }

        match ch {
            '"' => in_string = true,
            '{' => depth += 1,
            '}' => {
                depth = depth.saturating_sub(1);
                if depth == 0 {
                    let end = object_start + offset + ch.len_utf8();
                    return Some(&text[object_start..end]);
                }
            }
            _ => {}
        }
    }

    None
}

fn extract_json_string_field(text: &str, key: &str) -> Option<String> {
    let key_pattern = format!("\"{}\"", key);
    let key_index = text.find(&key_pattern)?;
    let after_key = &text[key_index + key_pattern.len()..];
    let colon = after_key.find(':')?;
    let mut chars = after_key[colon + 1..].char_indices().peekable();
    while let Some((_, ch)) = chars.peek().copied() {
        if ch.is_whitespace() {
            chars.next();
        } else {
            break;
        }
    }
    let (start_offset, quote) = chars.next()?;
    if quote != '"' {
        return None;
    }
    let value_start = key_index + key_pattern.len() + colon + 1 + start_offset + quote.len_utf8();
    let rest = &text[value_start..];
    let mut escape = false;
    for (offset, ch) in rest.char_indices() {
        if escape {
            escape = false;
        } else if ch == '\\' {
            escape = true;
        } else if ch == '"' {
            let raw = &rest[..offset];
            return serde_json::from_str::<String>(&format!("\"{}\"", raw)).ok();
        }
    }
    None
}
