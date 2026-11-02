// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{
    CaptureMetadataAccumulator, Event, HashMap, SSEAccumulator, SSEEvent, SSEProcessor, json,
};

#[cfg(test)]
#[path = "sse_stream_tests.rs"]
mod tests;

const MAX_SSE_BYTES: usize = 4 * 1024 * 1024;
const MAX_TOTAL_SSE_BYTES: usize = 64 * 1024 * 1024;
const MAX_SSE_EVENTS: usize = 100_000;

// Only protocol-bound HTTP responses enter this path. Raw/legacy SSE retains
// the existing processor's compatibility rules.
pub(super) struct StreamingSSE {
    buffers: HashMap<String, StreamState>,
    retired: HashMap<String, u64>,
    timeout_ms: u64,
    max_buffers: usize,
    max_total_bytes: usize,
}

struct StreamState {
    content: SSEAccumulator,
    remainder: Vec<u8>,
    received: usize,
    retained: usize,
    limited: bool,
}

impl StreamingSSE {
    pub(super) fn new(timeout_ms: u64, max_buffers: usize) -> Self {
        Self {
            buffers: HashMap::new(),
            retired: HashMap::new(),
            timeout_ms,
            max_buffers,
            max_total_bytes: MAX_TOTAL_SSE_BYTES,
        }
    }

    pub(super) fn handle(&mut self, event: Event) -> Vec<Event> {
        let mut output = Vec::new();
        let expired: Vec<_> = self
            .buffers
            .iter()
            .filter(|(_, state)| {
                event.timestamp.saturating_sub(state.content.last_update) > self.timeout_ms
            })
            .map(|(id, _)| id.clone())
            .collect();
        self.retired
            .retain(|_, timestamp| event.timestamp.saturating_sub(*timestamp) <= self.timeout_ms);
        for id in expired {
            self.flush(&id, "timeout", event.timestamp, &mut output);
        }
        let Some(id) = event.data["http_exchange_id"]
            .as_str()
            .filter(|id| !id.is_empty())
            .map(str::to_string)
        else {
            output.push(event);
            return output;
        };
        if event.source == "http_correlation" {
            let reason = event.data["completion_reason"]
                .as_str()
                .unwrap_or("partial");
            self.flush(&id, reason, event.timestamp, &mut output);
            output.push(event);
            return output;
        }
        let is_chunk = event.data["message_type"] == "response_chunk";
        if event.source != "http_parser"
            || event.data["correlation_version"] != 2
            || !(is_chunk || event.data["message_type"] == "response")
            || !SSEProcessor::http_content_type_is_sse(&event.data)
        {
            output.push(event);
            return output;
        }
        if self.retired.contains_key(&id) {
            return output;
        }
        if self.buffers.len() >= self.max_buffers
            && !self.buffers.contains_key(&id)
            && let Some(oldest) = self
                .buffers
                .iter()
                .min_by_key(|(_, state)| state.content.last_update)
                .map(|(id, _)| id.clone())
        {
            self.flush(&oldest, "evicted", event.timestamp, &mut output);
        }
        let payload = event.data["body_hex"]
            .as_str()
            .and_then(|value| hex::decode(value).ok())
            .unwrap_or_else(|| {
                event.data["body"]
                    .as_str()
                    .unwrap_or("")
                    .as_bytes()
                    .to_vec()
            });
        let available_total = self
            .max_total_bytes
            .saturating_sub(self.buffers.values().map(|state| state.retained).sum());
        let state = self.buffers.entry(id.clone()).or_insert_with(|| {
            let mut content = SSEAccumulator::new(&event);
            // Keep identity/headers, not an unbounded extra copy of the
            // first body chunk outside the retention budget.
            for key in ["body", "body_hex", "raw_data"] {
                content
                    .template_event
                    .data
                    .as_object_mut()
                    .unwrap()
                    .remove(key);
            }
            StreamState {
                content,
                remainder: Vec::new(),
                received: 0,
                retained: 0,
                limited: false,
            }
        });
        state.content.last_update = event.timestamp;
        state.content.end_time = event.timestamp;
        if event.data["capture_metadata_scope"] == "http_message" {
            // The parser emits cumulative message snapshots. Adding them would
            // count a TLS fragment again for every derived body chunk.
            state.content.capture_metadata = CaptureMetadataAccumulator::default();
        }
        state.content.capture_metadata.observe_event(&event);
        let ended = event.data["end_stream"] == true || !is_chunk;
        let available = MAX_SSE_BYTES
            .saturating_sub(state.received)
            .min(available_total);
        state.received = state.received.saturating_add(payload.len());
        if !state.limited {
            state.retained += payload.len().min(available);
            state
                .remainder
                .extend_from_slice(&payload[..payload.len().min(available)]);
            state.limited = payload.len() > available;
            state.consume_records(ended);
        }
        // finish_reason and usage can precede later choices/usage/[DONE]. For a
        // known exchange only HTTP end/termination, not a provider hint, flushes.
        if ended {
            let reason = if event.data["body_truncated"] == true {
                "truncated"
            } else {
                event.data["completion_reason"].as_str().unwrap_or("done")
            };
            self.flush(&id, reason, event.timestamp, &mut output);
        }
        output
    }

    fn flush(&mut self, id: &str, reason: &str, timestamp: u64, output: &mut Vec<Event>) {
        if let Some(state) = self.buffers.remove(id) {
            output.push(state.finish(reason, timestamp));
            self.retired.insert(id.to_string(), timestamp);
            if self.retired.len() > self.max_buffers
                && let Some(oldest) = self
                    .retired
                    .iter()
                    .min_by_key(|(_, timestamp)| *timestamp)
                    .map(|(id, _)| id.clone())
            {
                self.retired.remove(&oldest);
            }
        }
    }

    pub(super) fn finish(&mut self) -> Vec<Event> {
        self.buffers
            .drain()
            .map(|(_, state)| {
                let timestamp = state.content.end_time;
                state.finish("capture_end", timestamp)
            })
            .collect()
    }
}

impl StreamState {
    fn consume_records(&mut self, end_of_stream: bool) {
        let mut offset = 0;
        while let Some((end, consumed)) = sse_record_end(&self.remainder[offset..], end_of_stream) {
            let record = String::from_utf8_lossy(&self.remainder[offset..offset + end]);
            let events = parse_record(&record);
            if !events.is_empty() && self.content.events.len() >= MAX_SSE_EVENTS {
                self.limited = true;
                break;
            }
            SSEProcessor::accumulate_content(&mut self.content, &events);
            offset += consumed;
        }
        self.remainder.drain(..offset);
    }

    fn finish(mut self, reason: &str, timestamp: u64) -> Event {
        if !self.limited {
            self.consume_records(true);
        }
        let reason = if self.limited { "truncated" } else { reason };
        let reason = if reason == "done"
            && self.content.events.iter().any(|event| {
                event.event.as_deref() == Some("error")
                    || event.parsed_data.as_ref().is_some_and(|data| {
                        data["type"] == "error"
                            || data["type"] == "response.failed"
                            || !data["error"].is_null()
                    })
            }) {
            "error"
        } else {
            reason
        };
        self.content.end_time = timestamp;
        let mut original = self.content.template_event.clone();
        original.data["completion_reason"] = json!(reason);
        let mut output = SSEProcessor::create_merged_event(
            original.data["http_exchange_id"]
                .as_str()
                .unwrap()
                .to_string(),
            &self.content,
            &original,
        );
        output.data["received_bytes"] = json!(self.received);
        output.data["duration_ns"] = json!(
            timestamp
                .saturating_sub(self.content.start_time)
                .saturating_mul(1_000_000)
        );
        output.data["incomplete"] = json!(
            !matches!(reason, "done" | "error")
                || !self.remainder.is_empty()
                || self.content.protocol_mismatch
        );
        output.data["response_id"] = json!(self.content.response_id);
        if self.content.protocol_mismatch {
            output.data["correlation_status"] = json!("ambiguous");
        }
        // No synthetic SSE event is created from an unterminated record.
        // Preserve its exact bytes separately, including incomplete UTF-8.
        if !self.remainder.is_empty() {
            output.data["unparsed_sse_hex"] = json!(hex::encode(&self.remainder));
        }
        output
    }
}

// SSE permits LF, CRLF, and CR. A trailing CR remains pending until its next
// byte arrives, so a split CRLF cannot be mistaken for two empty lines.
fn sse_record_end(bytes: &[u8], end_of_stream: bool) -> Option<(usize, usize)> {
    let mut line_start = 0;
    let mut cursor = 0;
    while cursor < bytes.len() {
        let length = match bytes[cursor] {
            b'\n' => 1,
            b'\r' if cursor + 1 == bytes.len() && !end_of_stream => return None,
            b'\r' if bytes.get(cursor + 1) == Some(&b'\n') => 2,
            b'\r' => 1,
            _ => {
                cursor += 1;
                continue;
            }
        };
        if cursor == line_start {
            return Some((cursor, cursor + length));
        }
        cursor += length;
        line_start = cursor;
    }
    None
}

fn parse_record(record: &str) -> Vec<SSEEvent> {
    let mut event = SSEEvent {
        event: None,
        data: None,
        id: None,
        parsed_data: None,
        raw_data: None,
    };
    let mut data = Vec::new();
    for line in record.split(['\r', '\n']) {
        if line.starts_with(':') {
            continue;
        }
        let (field, value) = line.split_once(':').unwrap_or((line, ""));
        let value = value.strip_prefix(' ').unwrap_or(value);
        match field {
            "event" => event.event = Some(value.to_string()),
            "data" => data.push(value),
            "id" if !value.contains('\0') => event.id = Some(value.to_string()),
            _ => {}
        }
    }
    if data.is_empty() {
        return Vec::new();
    }
    let data = data.join("\n");
    event.parsed_data = serde_json::from_str(&data).ok();
    if event.parsed_data.is_none() {
        event.raw_data = Some(data.clone());
    }
    event.data = Some(data);
    vec![event]
}
