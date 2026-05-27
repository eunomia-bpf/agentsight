// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::event::HTTPEvent;
use super::{Analyzer, AnalyzerError};
use crate::framework::core::Event;
use crate::framework::runners::EventStream;
use async_trait::async_trait;
use futures::{stream, stream::StreamExt};
use hpack::Decoder as HpackDecoder;
use std::collections::HashMap;

/// HTTP Parser Analyzer that parses SSL traffic into HTTP requests/responses
pub struct HTTPParser {
    /// Flag to include raw data in parsed events (default: true)
    include_raw_data: bool,
    http2: HTTP2State,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum HTTP2Direction {
    Request,
    Response,
}

#[derive(Default)]
struct HTTP2StreamState {
    request_headers: HashMap<String, String>,
    response_headers: HashMap<String, String>,
    request_body: Vec<u8>,
    response_body: Vec<u8>,
    request_emitted: bool,
    response_emitted: bool,
}

struct PendingHTTP2Headers {
    direction: HTTP2Direction,
    block: Vec<u8>,
}

struct HTTP2Frame<'a> {
    frame_type: u8,
    flags: u8,
    stream_id: u32,
    payload: &'a [u8],
}

struct HTTP2State {
    request_decoder: HpackDecoder<'static>,
    response_decoder: HpackDecoder<'static>,
    streams: HashMap<(u64, u32), HTTP2StreamState>,
    pending_headers: HashMap<(u64, u32), PendingHTTP2Headers>,
}

impl Default for HTTP2State {
    fn default() -> Self {
        Self {
            request_decoder: HpackDecoder::new(),
            response_decoder: HpackDecoder::new(),
            streams: HashMap::new(),
            pending_headers: HashMap::new(),
        }
    }
}

#[derive(Clone, PartialEq, Debug)]
pub enum HTTPMessageType {
    Request,
    Response,
}

/// Parsed HTTP message
#[derive(Clone, Debug)]
pub struct HTTPMessage {
    pub message_type: HTTPMessageType,
    pub first_line: String,
    pub headers: HashMap<String, String>,
    pub body: Option<String>,
    pub raw_data: String,
    // Request-specific fields
    pub method: Option<String>,
    pub path: Option<String>,
    pub protocol: Option<String>,
    // Response-specific fields
    pub status_code: Option<u16>,
    pub status_text: Option<String>,
}

impl HTTPParser {
    /// Create a new HTTPParser with default settings (raw data included)
    pub fn new() -> Self {
        HTTPParser {
            include_raw_data: true,
            http2: HTTP2State::default(),
        }
    }

    /// Disable raw data inclusion
    pub fn disable_raw_data(mut self) -> Self {
        self.include_raw_data = false;
        self
    }

    /// Check if SSL data contains HTTP protocol data
    pub fn is_http_data(data: &str) -> bool {
        // Look for HTTP patterns
        let has_http_request = data.contains("HTTP/1.")
            && (data.contains("GET ")
                || data.contains("POST ")
                || data.contains("PUT ")
                || data.contains("DELETE ")
                || data.contains("HEAD ")
                || data.contains("OPTIONS ")
                || data.contains("PATCH "));

        let has_http_response = data.starts_with("HTTP/1.") || data.contains("\r\nHTTP/1.");

        // Look for common HTTP headers
        let has_http_headers = data.contains("Content-Type:")
            || data.contains("content-type:")
            || data.contains("Host:")
            || data.contains("host:")
            || data.contains("User-Agent:")
            || data.contains("user-agent:");

        has_http_request || has_http_response || has_http_headers
    }

    /// Parse HTTP message from accumulated data
    pub fn parse_http_message(data: &str) -> Option<HTTPMessage> {
        let lines: Vec<&str> = data.split("\r\n").collect();

        if lines.is_empty() {
            return None;
        }

        let first_line = lines[0];
        let mut headers = HashMap::new();
        let mut body_start = None;
        let mut message_type = HTTPMessageType::Request;
        let mut method = None;
        let mut path = None;
        let mut protocol = None;
        let mut status_code = None;
        let mut status_text = None;

        // Parse first line to determine message type
        if first_line.starts_with("HTTP/") {
            // Response
            message_type = HTTPMessageType::Response;
            let parts: Vec<&str> = first_line.splitn(3, ' ').collect();
            if parts.len() >= 2 {
                if let Ok(code) = parts[1].parse::<u16>() {
                    status_code = Some(code);
                }
                if parts.len() >= 3 {
                    status_text = Some(parts[2].to_string());
                }
                protocol = Some(parts[0].to_string());
            }
        } else {
            // Request
            let parts: Vec<&str> = first_line.splitn(3, ' ').collect();
            if parts.len() < 3
                || !matches!(
                    parts[0],
                    "GET" | "POST" | "PUT" | "DELETE" | "HEAD" | "OPTIONS" | "PATCH"
                )
                || !parts[2].starts_with("HTTP/")
            {
                return None;
            }
            method = Some(parts[0].to_string());
            path = Some(parts[1].to_string());
            protocol = Some(parts[2].to_string());
        }

        // Parse headers
        for (i, line) in lines.iter().enumerate().skip(1) {
            if line.is_empty() {
                body_start = Some(i + 1);
                break;
            }
            if let Some(colon_pos) = line.find(':') {
                let key = line[..colon_pos].trim().to_lowercase();
                let value = line[colon_pos + 1..].trim().to_string();
                headers.insert(key, value);
            }
        }

        // Extract body if present
        let body = if let Some(start) = body_start {
            if start < lines.len() {
                let body_lines: Vec<&str> = lines[start..].to_vec();
                let body_content = body_lines.join("\r\n");
                if !body_content.trim().is_empty() {
                    Some(body_content)
                } else {
                    None
                }
            } else {
                None
            }
        } else {
            None
        };

        Some(HTTPMessage {
            message_type,
            first_line: first_line.to_string(),
            headers,
            body,
            raw_data: data.to_string(),
            method,
            path,
            protocol,
            status_code,
            status_text,
        })
    }

    /// Create HTTP event from parsed message
    fn create_http_event(
        tid: u64,
        parsed_message: HTTPMessage,
        original_event: &Event,
        include_raw_data: bool,
    ) -> Event {
        let message_type_str = match parsed_message.message_type {
            HTTPMessageType::Request => "request",
            HTTPMessageType::Response => "response",
        };

        // Determine content properties
        let content_length = parsed_message
            .headers
            .get("content-length")
            .and_then(|v| v.parse::<usize>().ok());
        let is_chunked = parsed_message
            .headers
            .get("transfer-encoding")
            .map(|v| v.to_lowercase().contains("chunked"))
            .unwrap_or(false);
        let has_body = parsed_message.body.is_some();

        // Calculate total size from parsed components
        let total_size = parsed_message.first_line.len() +
            parsed_message.headers.iter().map(|(k, v)| k.len() + v.len() + 4).sum::<usize>() + // +4 for ": \r\n"
            parsed_message.body.as_ref().map(|b| b.len()).unwrap_or(0) +
            4; // +4 for \r\n\r\n separator

        let mut http_event = HTTPEvent::new(
            tid,
            message_type_str.to_string(),
            parsed_message.first_line,
            parsed_message.method,
            parsed_message.path,
            parsed_message.protocol,
            parsed_message.status_code,
            parsed_message.status_text,
            parsed_message.headers,
            parsed_message.body,
            total_size,
            has_body,
            is_chunked,
            content_length,
            "ssl".to_string(),
        );

        // Include raw data if requested
        if include_raw_data {
            http_event = http_event.with_raw_data(parsed_message.raw_data);
        }

        http_event.to_event(original_event)
    }

    /// Handle SSL events (HTTP request/response data)
    fn handle_ssl_event(
        http2: &mut HTTP2State,
        event: Event,
        include_raw_data: bool,
    ) -> Vec<Event> {
        let ssl_data = &event.data;

        let data_str = match ssl_data.get("data").and_then(|v| v.as_str()) {
            Some(s) => s,
            None => return vec![event],
        };

        // Only process if it's HTTP data AND can be parsed as a complete HTTP message
        if Self::is_http_data(data_str)
            && let Some(parsed_message) = Self::parse_http_message(data_str)
        {
            let tid = ssl_data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
            return vec![Self::create_http_event(
                tid,
                parsed_message,
                &event,
                include_raw_data,
            )];
        }

        let data_bytes = ssl_json_string_to_bytes(data_str);
        if let Some(events) = http2.handle_event(&event, &data_bytes, include_raw_data) {
            return events;
        }

        // If not parseable as HTTP, pass through original event
        vec![event]
    }
}

impl HTTP2State {
    fn handle_event(
        &mut self,
        original_event: &Event,
        bytes: &[u8],
        include_raw_data: bool,
    ) -> Option<Vec<Event>> {
        let tid = original_event
            .data
            .get("tid")
            .and_then(|v| v.as_u64())
            .unwrap_or(0);
        let direction = direction_from_function(
            original_event
                .data
                .get("function")
                .and_then(|v| v.as_str())
                .unwrap_or(""),
        )?;
        let frames = parse_http2_frames(bytes)?;
        let mut events = Vec::new();

        for frame in frames {
            let key = (tid, frame.stream_id);
            match frame.frame_type {
                0x0 => {
                    if frame.stream_id == 0 {
                        continue;
                    }
                    let payload = data_payload(frame.flags, frame.payload);
                    let state = self.streams.entry(key).or_default();
                    match direction {
                        HTTP2Direction::Request => {
                            state.request_body.extend_from_slice(payload);
                            if frame.flags & 0x1 != 0 && !state.request_emitted {
                                events.push(create_http2_request_event(
                                    tid,
                                    frame.stream_id,
                                    state,
                                    original_event,
                                    include_raw_data,
                                ));
                                state.request_emitted = true;
                            }
                        }
                        HTTP2Direction::Response => {
                            state.response_body.extend_from_slice(payload);
                            if (frame.flags & 0x1 != 0
                                || looks_like_complete_json(&state.response_body))
                                && !state.response_emitted
                            {
                                events.push(create_http2_response_event(
                                    tid,
                                    frame.stream_id,
                                    state,
                                    original_event,
                                    include_raw_data,
                                ));
                                state.response_emitted = true;
                            }
                        }
                    }
                }
                0x1 => {
                    if frame.stream_id == 0 {
                        continue;
                    }
                    let fragment = headers_payload(frame.flags, frame.payload);
                    if frame.flags & 0x4 != 0 {
                        if let Some(headers) = self.decode_headers(direction, fragment) {
                            let state = self.streams.entry(key).or_default();
                            apply_headers(state, direction, headers);
                            if frame.flags & 0x1 != 0 {
                                match direction {
                                    HTTP2Direction::Request if !state.request_emitted => {
                                        events.push(create_http2_request_event(
                                            tid,
                                            frame.stream_id,
                                            state,
                                            original_event,
                                            include_raw_data,
                                        ));
                                        state.request_emitted = true;
                                    }
                                    HTTP2Direction::Response if !state.response_emitted => {
                                        events.push(create_http2_response_event(
                                            tid,
                                            frame.stream_id,
                                            state,
                                            original_event,
                                            include_raw_data,
                                        ));
                                        state.response_emitted = true;
                                    }
                                    _ => {}
                                }
                            }
                        }
                    } else {
                        self.pending_headers.insert(
                            key,
                            PendingHTTP2Headers {
                                direction,
                                block: fragment.to_vec(),
                            },
                        );
                    }
                }
                0x9 => {
                    if frame.stream_id == 0 {
                        continue;
                    }
                    let Some(mut pending) = self.pending_headers.remove(&key) else {
                        continue;
                    };
                    pending.block.extend_from_slice(frame.payload);
                    if frame.flags & 0x4 != 0 {
                        if let Some(headers) =
                            self.decode_headers(pending.direction, &pending.block)
                        {
                            let state = self.streams.entry(key).or_default();
                            apply_headers(state, pending.direction, headers);
                        }
                    } else {
                        self.pending_headers.insert(key, pending);
                    }
                }
                _ => {}
            }

            if self
                .streams
                .get(&key)
                .map(|s| s.request_emitted && s.response_emitted)
                .unwrap_or(false)
            {
                self.streams.remove(&key);
            }
        }

        Some(if events.is_empty() {
            Vec::new()
        } else {
            events
        })
    }

    fn decode_headers(
        &mut self,
        direction: HTTP2Direction,
        block: &[u8],
    ) -> Option<HashMap<String, String>> {
        let decoder = match direction {
            HTTP2Direction::Request => &mut self.request_decoder,
            HTTP2Direction::Response => &mut self.response_decoder,
        };
        let decoded = decoder.decode(block).ok()?;
        let mut headers = HashMap::new();
        for (name, value) in decoded {
            let name = String::from_utf8_lossy(&name).to_ascii_lowercase();
            let value = String::from_utf8_lossy(&value).to_string();
            headers.insert(name, value);
        }
        if let Some(authority) = headers.get(":authority").cloned() {
            headers.entry("host".to_string()).or_insert(authority);
        }
        Some(headers)
    }
}

fn apply_headers(
    state: &mut HTTP2StreamState,
    direction: HTTP2Direction,
    headers: HashMap<String, String>,
) {
    match direction {
        HTTP2Direction::Request => state.request_headers.extend(headers),
        HTTP2Direction::Response => state.response_headers.extend(headers),
    }
}

fn direction_from_function(function: &str) -> Option<HTTP2Direction> {
    let upper = function.to_ascii_uppercase();
    if upper.contains("READ") || upper.contains("RECV") {
        Some(HTTP2Direction::Response)
    } else if upper.contains("WRITE") || upper.contains("SEND") {
        Some(HTTP2Direction::Request)
    } else {
        None
    }
}

fn parse_http2_frames(mut bytes: &[u8]) -> Option<Vec<HTTP2Frame<'_>>> {
    const PREFACE: &[u8] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";
    if bytes.starts_with(PREFACE) {
        bytes = &bytes[PREFACE.len()..];
    }
    if bytes.len() < 9 {
        return None;
    }

    let mut frames = Vec::new();
    let mut offset = 0usize;
    while offset + 9 <= bytes.len() {
        let length = ((bytes[offset] as usize) << 16)
            | ((bytes[offset + 1] as usize) << 8)
            | bytes[offset + 2] as usize;
        let frame_type = bytes[offset + 3];
        let flags = bytes[offset + 4];
        let stream_id = ((bytes[offset + 5] as u32 & 0x7f) << 24)
            | ((bytes[offset + 6] as u32) << 16)
            | ((bytes[offset + 7] as u32) << 8)
            | bytes[offset + 8] as u32;
        offset += 9;
        if length > bytes.len().saturating_sub(offset) || frame_type > 0x9 {
            return None;
        }
        let payload = &bytes[offset..offset + length];
        offset += length;
        frames.push(HTTP2Frame {
            frame_type,
            flags,
            stream_id,
            payload,
        });
    }

    if frames.is_empty() || offset != bytes.len() {
        None
    } else {
        Some(frames)
    }
}

fn headers_payload(flags: u8, payload: &[u8]) -> &[u8] {
    let mut start = 0usize;
    let mut end = payload.len();
    if flags & 0x8 != 0 {
        let Some(pad_len) = payload.first().copied() else {
            return &[];
        };
        start += 1;
        end = end.saturating_sub(pad_len as usize);
    }
    if flags & 0x20 != 0 {
        start = start.saturating_add(5);
    }
    if start > end || end > payload.len() {
        &[]
    } else {
        &payload[start..end]
    }
}

fn data_payload(flags: u8, payload: &[u8]) -> &[u8] {
    if flags & 0x8 == 0 {
        return payload;
    }
    let Some(pad_len) = payload.first().copied() else {
        return &[];
    };
    let start = 1usize;
    let end = payload.len().saturating_sub(pad_len as usize);
    if start > end || end > payload.len() {
        &[]
    } else {
        &payload[start..end]
    }
}

fn looks_like_complete_json(bytes: &[u8]) -> bool {
    let text = String::from_utf8_lossy(bytes);
    text.contains("usageMetadata") && serde_json::from_str::<serde_json::Value>(&text).is_ok()
}

fn create_http2_request_event(
    tid: u64,
    stream_id: u32,
    state: &HTTP2StreamState,
    original_event: &Event,
    include_raw_data: bool,
) -> Event {
    let method = state.request_headers.get(":method").cloned();
    let path = state.request_headers.get(":path").cloned();
    let first_line = format!(
        "{} {} HTTP/2",
        method.as_deref().unwrap_or("HTTP"),
        path.as_deref().unwrap_or("/")
    );
    let body = body_string(&state.request_body);
    let total_size = headers_size(&state.request_headers) + state.request_body.len();
    let mut event = HTTPEvent::new(
        synthetic_http2_tid(tid, stream_id),
        "request".to_string(),
        first_line,
        method,
        path,
        Some("HTTP/2".to_string()),
        None,
        None,
        state.request_headers.clone(),
        body.clone(),
        total_size,
        body.is_some(),
        false,
        body.as_ref().map(String::len),
        "ssl.http2".to_string(),
    );
    if include_raw_data {
        event = event.with_raw_data(String::from_utf8_lossy(&state.request_body).to_string());
    }
    event.to_event(original_event)
}

fn create_http2_response_event(
    tid: u64,
    stream_id: u32,
    state: &HTTP2StreamState,
    original_event: &Event,
    include_raw_data: bool,
) -> Event {
    let status_code = state
        .response_headers
        .get(":status")
        .and_then(|s| s.parse::<u16>().ok())
        .or(Some(200));
    let first_line = format!("HTTP/2 {}", status_code.unwrap_or(200));
    let body = body_string(&state.response_body);
    let total_size = headers_size(&state.response_headers) + state.response_body.len();
    let mut event = HTTPEvent::new(
        synthetic_http2_tid(tid, stream_id),
        "response".to_string(),
        first_line,
        None,
        None,
        Some("HTTP/2".to_string()),
        status_code,
        None,
        state.response_headers.clone(),
        body.clone(),
        total_size,
        body.is_some(),
        false,
        body.as_ref().map(String::len),
        "ssl.http2".to_string(),
    );
    if include_raw_data {
        event = event.with_raw_data(String::from_utf8_lossy(&state.response_body).to_string());
    }
    event.to_event(original_event)
}

fn synthetic_http2_tid(tid: u64, stream_id: u32) -> u64 {
    tid.saturating_mul(1_000_000)
        .saturating_add(stream_id as u64)
}

fn body_string(body: &[u8]) -> Option<String> {
    if body.is_empty() {
        None
    } else {
        Some(String::from_utf8_lossy(body).to_string())
    }
}

fn headers_size(headers: &HashMap<String, String>) -> usize {
    headers.iter().map(|(k, v)| k.len() + v.len()).sum()
}

fn ssl_json_string_to_bytes(data: &str) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(data.len());
    for ch in data.chars() {
        let code = ch as u32;
        if code <= 0xff {
            bytes.push(code as u8);
        } else {
            let mut buf = [0u8; 4];
            bytes.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
        }
    }
    bytes
}

#[async_trait]
impl Analyzer for HTTPParser {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let include_raw_data = self.include_raw_data;
        let mut http2 = std::mem::take(&mut self.http2);

        let processed_stream = stream.flat_map(move |event| {
            let events = if event.source == "ssl" {
                Self::handle_ssl_event(&mut http2, event, include_raw_data)
            } else {
                vec![event]
            };
            stream::iter(events)
        });

        Ok(Box::pin(processed_stream))
    }

    fn name(&self) -> &str {
        "HTTPParser"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::framework::storage::{GenericProjector, SqliteStore};
    use futures::StreamExt;
    use hpack::Encoder as HpackEncoder;
    use serde_json::json;

    fn ssl_event(timestamp: u64, function: &str, bytes: Vec<u8>) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            4242,
            "node".to_string(),
            json!({
                "tid": 7,
                "function": function,
                "data": bytes_to_ssl_json_string(&bytes),
            }),
        )
    }

    fn bytes_to_ssl_json_string(bytes: &[u8]) -> String {
        bytes.iter().map(|b| char::from(*b)).collect()
    }

    fn frame(frame_type: u8, flags: u8, stream_id: u32, payload: &[u8]) -> Vec<u8> {
        let len = payload.len();
        let mut out = vec![
            ((len >> 16) & 0xff) as u8,
            ((len >> 8) & 0xff) as u8,
            (len & 0xff) as u8,
            frame_type,
            flags,
            ((stream_id >> 24) & 0x7f) as u8,
            ((stream_id >> 16) & 0xff) as u8,
            ((stream_id >> 8) & 0xff) as u8,
            (stream_id & 0xff) as u8,
        ];
        out.extend_from_slice(payload);
        out
    }

    #[tokio::test]
    async fn parses_http2_gemini_usage_into_http_events() {
        let mut request_encoder = HpackEncoder::new();
        let mut response_encoder = HpackEncoder::new();
        let request_headers = [
            (&b":method"[..], &b"POST"[..]),
            (&b":scheme"[..], &b"https"[..]),
            (&b":authority"[..], &b"cloudcode-pa.googleapis.com"[..]),
            (&b":path"[..], &b"/v1internal:generateContent"[..]),
        ];
        let response_headers = [
            (&b":status"[..], &b"200"[..]),
            (&b"content-type"[..], &b"application/json"[..]),
        ];
        let request_body = br#"{"model":"gemini-2.5-pro","request":{"contents":[]}}"#;
        let response_body = br#"{"usageMetadata":{"promptTokenCount":11,"candidatesTokenCount":4,"totalTokenCount":15}}"#;

        let mut request_bytes = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".to_vec();
        request_bytes.extend(frame(0x1, 0x4, 1, &request_encoder.encode(request_headers)));
        request_bytes.extend(frame(0x0, 0x1, 1, request_body));

        let mut response_bytes = Vec::new();
        response_bytes.extend(frame(
            0x1,
            0x4,
            1,
            &response_encoder.encode(response_headers),
        ));
        response_bytes.extend(frame(0x0, 0x1, 1, response_body));

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", request_bytes),
            ssl_event(2, "READ/RECV", response_bytes),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 2);
        assert_eq!(output[0].source, "http_parser");
        assert_eq!(output[0].data["message_type"], "request");
        assert_eq!(output[0].data["path"], "/v1internal:generateContent");
        assert_eq!(
            output[0].data["headers"]["host"],
            "cloudcode-pa.googleapis.com"
        );
        assert_eq!(output[1].source, "http_parser");
        assert_eq!(output[1].data["message_type"], "response");
        assert_eq!(output[1].data["status_code"], 200);
        assert!(
            output[1].data["body"]
                .as_str()
                .unwrap()
                .contains("usageMetadata")
        );

        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        for event in output {
            store.insert_event(&event, &mut projector).unwrap();
        }
        let total: i64 = store
            .connection()
            .query_row(
                "SELECT COALESCE(SUM(total_tokens), 0)
                 FROM token_usage WHERE source = 'response_usage'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(total, 15);
    }

    #[test]
    fn rejects_non_http2_frames() {
        assert!(parse_http2_frames(b"GET / HTTP/1.1\r\n\r\n").is_none());
    }
}
