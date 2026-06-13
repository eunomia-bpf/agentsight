// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::{Value, json};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use super::protocol_events::SSEProcessorEvent;

const MAX_BUFFERS: usize = 1024;

pub struct SSEProcessor {
    sse_buffers: Arc<Mutex<HashMap<String, SSEAccumulator>>>,
    timeout_ms: u64,
    max_buffers: usize,
}

struct SSEAccumulator {
    message_id: Option<String>,
    accumulated_text: String,
    accumulated_json: String,
    events: Vec<SSEEvent>,
    is_complete: bool,
    last_update: u64,
    has_message_start: bool,
    start_time: u64,
    end_time: u64,
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
        Self::new_with_timeout(30_000)
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

        let mut has_content_deltas = false;
        let mut has_message_start = false;
        let mut metadata_only_count = 0;

        for event in &accumulator.events {
            if Self::sse_event_has_usage(event) {
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
        event.parsed_data.as_ref().is_some_and(|data| {
            data.get("usageMetadata").is_some()
                || data.get("usage").is_some()
                || data.get("message").and_then(|m| m.get("usage")).is_some()
        })
    }

    fn sse_event_completes_stream(event: &SSEEvent) -> bool {
        event.data.as_deref() == Some("[DONE]")
            || event.parsed_data.as_ref().is_some_and(|data| {
                data.get("usageMetadata").is_some() || data.get("usage").is_some()
            })
    }

    fn accumulate_content(accumulator: &mut SSEAccumulator, events: &[SSEEvent]) {
        for event in events {
            accumulator.events.push(event.clone());

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
        }
    }

    fn create_merged_event(
        connection_id: String,
        accumulator: &SSEAccumulator,
        original_event: &Event,
    ) -> Event {
        let json_content = if !accumulator.accumulated_json.is_empty() {
            match serde_json::from_str::<Value>(&accumulator.accumulated_json) {
                Ok(parsed_json) => serde_json::to_string_pretty(&parsed_json)
                    .unwrap_or(accumulator.accumulated_json.clone()),
                Err(_) => accumulator.accumulated_json.clone(),
            }
        } else {
            String::new()
        };

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
            original_source: "ssl".to_string(),
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
                if event.source != "ssl" {
                    return Some(event);
                }

                let data_str = match event.data.get("data").and_then(|v| v.as_str()) {
                    Some(s) => s,
                    None => return Some(event),
                };

                let sse_events = if Self::is_sse_data(data_str) {
                    Self::parse_sse_events(data_str)
                } else if let Some(event) = Self::parse_usage_metadata_fragment(data_str) {
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

                let should_skip_chunk = !has_content_potential && sse_events.iter().all(|e| {
                    e.event.as_deref().is_some_and(|t| matches!(t, "ping" | "message_delta"))
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

                buffers_lock.retain(|_, acc| event.timestamp.saturating_sub(acc.last_update) <= timeout_ms);
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
                            let has_message_stop = accumulator.events.iter().any(|e| {
                                e.event.as_deref() == Some("message_stop")
                            });
                            if !has_message_stop {
                                final_connection_id = existing_id.clone();
                                break;
                            }
                        }
                    }
                }

                let accumulator = buffers_lock.entry(final_connection_id.clone()).or_insert_with(|| SSEAccumulator {
                    message_id: None,
                    accumulated_text: String::new(),
                    accumulated_json: String::new(),
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

                if Self::is_sse_complete(accumulator) {
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
