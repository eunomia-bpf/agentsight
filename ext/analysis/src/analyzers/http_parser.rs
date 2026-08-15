// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::protocol_events::HTTPEvent;
use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_trait::async_trait;
use flate2::{Decompress, FlushDecompress};
use futures::{stream, stream::StreamExt};
use hpack::Decoder as HpackDecoder;
use std::collections::HashMap;

const MAX_HTTP2_STREAMS: usize = 1024;
const MAX_HTTP2_PENDING_HEADERS: usize = 1024;
const MAX_HTTP_BODY_BYTES: usize = 1024 * 1024;
const MAX_HTTP2_HEADER_BLOCK_BYTES: usize = 64 * 1024;

/// HTTP Parser Analyzer that parses SSL traffic into HTTP requests/responses
pub struct HTTPParser {
    /// Flag to include raw data in parsed events (default: true)
    include_raw_data: bool,
    http2: HTTP2State,
    websocket: WebSocketState,
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

#[derive(Default)]
struct WebSocketState {
    connections: HashMap<u32, WebSocketConnection>,
}

struct WebSocketConnection {
    path: String,
    headers: HashMap<String, String>,
    inflater: Decompress,
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

impl Default for HTTPParser {
    fn default() -> Self {
        Self::new()
    }
}

impl HTTPParser {
    /// Create a new HTTPParser with default settings (raw data included)
    pub fn new() -> Self {
        HTTPParser {
            include_raw_data: true,
            http2: HTTP2State::default(),
            websocket: WebSocketState::default(),
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
        let body_hex = parsed_message
            .body
            .as_deref()
            .map(ssl_json_string_to_bytes)
            .map(hex::encode);

        // Calculate total size from parsed components
        let total_size = parsed_message.first_line.len() +
            parsed_message.headers.iter().map(|(k, v)| k.len() + v.len() + 4).sum::<usize>() + // +4 for ": \r\n"
            parsed_message.body.as_ref().map(|b| b.len()).unwrap_or(0) +
            4; // +4 for \r\n\r\n separator

        HTTPEvent {
            tid,
            message_type: message_type_str.to_string(),
            first_line: parsed_message.first_line,
            method: parsed_message.method,
            path: parsed_message.path,
            protocol: parsed_message.protocol,
            status_code: parsed_message.status_code,
            status_text: parsed_message.status_text,
            headers: parsed_message.headers,
            body: parsed_message.body,
            body_hex,
            total_size,
            has_body,
            is_chunked,
            content_length,
            original_source: "ssl".to_string(),
            raw_data: include_raw_data.then_some(parsed_message.raw_data),
        }
        .to_event(original_event)
    }

    /// Handle SSL events (HTTP request/response data)
    fn handle_ssl_event(
        http2: &mut HTTP2State,
        websocket: &mut WebSocketState,
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
            websocket.observe_handshake(&event, &parsed_message);
            let tid = ssl_data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
            return vec![Self::create_http_event(
                tid,
                parsed_message,
                &event,
                include_raw_data,
            )];
        }

        let data_bytes = ssl_data
            .get("data_hex")
            .and_then(|v| v.as_str())
            .and_then(|v| hex::decode(v).ok())
            .unwrap_or_else(|| ssl_json_string_to_bytes(data_str));
        if let Some(events) = websocket.handle_event(&event, &data_bytes, include_raw_data) {
            return events;
        }
        if let Some(events) = http2.handle_event(&event, &data_bytes, include_raw_data) {
            return events;
        }

        // If not parseable as HTTP, pass through original event
        vec![event]
    }
}

impl WebSocketState {
    fn observe_handshake(&mut self, event: &Event, message: &HTTPMessage) {
        if message.message_type != HTTPMessageType::Request
            || !message
                .headers
                .get("upgrade")
                .is_some_and(|v| v.eq_ignore_ascii_case("websocket"))
        {
            return;
        }
        let Some(path) = message.path.as_ref() else {
            return;
        };
        if !path.contains("/v1/responses") && !path.contains("/codex/responses") {
            return;
        }
        self.connections.insert(
            event.pid,
            WebSocketConnection {
                path: path.clone(),
                headers: message.headers.clone(),
                inflater: Decompress::new(false),
            },
        );
    }

    fn handle_event(
        &mut self,
        event: &Event,
        bytes: &[u8],
        include_raw_data: bool,
    ) -> Option<Vec<Event>> {
        let connection = self.connections.get_mut(&event.pid)?;
        let (compressed, mut payload) = parse_masked_websocket_frame(bytes)?;
        if compressed {
            payload.extend_from_slice(&[0, 0, 0xff, 0xff]);
            let mut decoded = Vec::with_capacity(MAX_HTTP_BODY_BYTES);
            let input_before = connection.inflater.total_in();
            connection
                .inflater
                .decompress_vec(&payload, &mut decoded, FlushDecompress::Sync)
                .ok()?;
            if connection.inflater.total_in() - input_before != payload.len() as u64 {
                return None;
            }
            payload = decoded;
        }
        let body = String::from_utf8(payload).ok()?;
        let json: serde_json::Value = serde_json::from_str(&body).ok()?;
        if json.get("type").and_then(|v| v.as_str()) != Some("response.create") {
            return None;
        }
        Some(vec![create_websocket_request_event(
            event,
            &connection.path,
            &connection.headers,
            body,
            include_raw_data,
        )])
    }
}

fn parse_masked_websocket_frame(bytes: &[u8]) -> Option<(bool, Vec<u8>)> {
    if bytes.len() < 2
        || bytes[0] & 0x80 == 0
        || bytes[0] & 0x30 != 0
        || !matches!(bytes[0] & 0x0f, 1 | 2)
        || bytes[1] & 0x80 == 0
    {
        return None;
    }
    let mut offset = 2;
    let mut payload_len = (bytes[1] & 0x7f) as usize;
    if payload_len == 126 {
        payload_len = usize::from(u16::from_be_bytes(
            bytes.get(offset..offset + 2)?.try_into().ok()?,
        ));
        offset += 2;
    } else if payload_len == 127 {
        payload_len = usize::try_from(u64::from_be_bytes(
            bytes.get(offset..offset + 8)?.try_into().ok()?,
        ))
        .ok()?;
        offset += 8;
    }
    let mask: [u8; 4] = bytes.get(offset..offset + 4)?.try_into().ok()?;
    offset += 4;
    let payload = bytes.get(offset..offset.checked_add(payload_len)?)?;
    if offset + payload_len != bytes.len() {
        return None;
    }
    Some((
        bytes[0] & 0x40 != 0,
        payload
            .iter()
            .enumerate()
            .map(|(i, byte)| byte ^ mask[i % 4])
            .collect(),
    ))
}

fn create_websocket_request_event(
    original_event: &Event,
    path: &str,
    headers: &HashMap<String, String>,
    body: String,
    include_raw_data: bool,
) -> Event {
    let tid = original_event
        .data
        .get("tid")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    HTTPEvent {
        tid,
        message_type: "request".to_string(),
        first_line: format!("POST {path} WebSocket"),
        method: Some("POST".to_string()),
        path: Some(path.to_string()),
        protocol: Some("WebSocket".to_string()),
        status_code: None,
        status_text: None,
        headers: headers.clone(),
        content_length: Some(body.len()),
        has_body: true,
        is_chunked: false,
        body_hex: Some(hex::encode(body.as_bytes())),
        total_size: headers_size(headers) + body.len(),
        original_source: "ssl.websocket".to_string(),
        raw_data: include_raw_data.then(|| body.clone()),
        body: Some(body),
    }
    .to_event(original_event)
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
                            extend_capped(&mut state.request_body, payload, MAX_HTTP_BODY_BYTES);
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
                            extend_capped(&mut state.response_body, payload, MAX_HTTP_BODY_BYTES);
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
                    } else if fragment.len() <= MAX_HTTP2_HEADER_BLOCK_BYTES {
                        self.pending_headers.insert(
                            key,
                            PendingHTTP2Headers {
                                direction,
                                block: fragment.to_vec(),
                            },
                        );
                        evict_over_capacity(&mut self.pending_headers, MAX_HTTP2_PENDING_HEADERS);
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
                    if pending.block.len() > MAX_HTTP2_HEADER_BLOCK_BYTES {
                        continue;
                    }
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
            evict_over_capacity(&mut self.streams, MAX_HTTP2_STREAMS);
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
        if length > bytes.len().saturating_sub(offset) {
            return None;
        }
        let payload = &bytes[offset..offset + length];
        offset += length;
        // Skip unknown frame types per HTTP/2 spec (only process 0x0..=0x9)
        if frame_type > 0x9 {
            continue;
        }
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
    let body_hex = (!state.request_body.is_empty()).then(|| hex::encode(&state.request_body));
    let total_size = headers_size(&state.request_headers) + state.request_body.len();
    HTTPEvent {
        tid: synthetic_http2_tid(tid, stream_id),
        message_type: "request".to_string(),
        first_line,
        method,
        path,
        protocol: Some("HTTP/2".to_string()),
        status_code: None,
        status_text: None,
        headers: state.request_headers.clone(),
        content_length: body.as_ref().map(String::len),
        has_body: body.is_some(),
        is_chunked: false,
        body,
        body_hex,
        total_size,
        original_source: "ssl.http2".to_string(),
        raw_data: include_raw_data
            .then(|| String::from_utf8_lossy(&state.request_body).to_string()),
    }
    .to_event(original_event)
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
    let body_hex = (!state.response_body.is_empty()).then(|| hex::encode(&state.response_body));
    let total_size = headers_size(&state.response_headers) + state.response_body.len();
    HTTPEvent {
        tid: synthetic_http2_tid(tid, stream_id),
        message_type: "response".to_string(),
        first_line,
        method: None,
        path: None,
        protocol: Some("HTTP/2".to_string()),
        status_code,
        status_text: None,
        headers: state.response_headers.clone(),
        content_length: body.as_ref().map(String::len),
        has_body: body.is_some(),
        is_chunked: false,
        body,
        body_hex,
        total_size,
        original_source: "ssl.http2".to_string(),
        raw_data: include_raw_data
            .then(|| String::from_utf8_lossy(&state.response_body).to_string()),
    }
    .to_event(original_event)
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
        let mut websocket = std::mem::take(&mut self.websocket);

        let processed_stream = stream.flat_map(move |event| {
            let events = if event.source == "ssl" {
                Self::handle_ssl_event(&mut http2, &mut websocket, event, include_raw_data)
            } else {
                vec![event]
            };
            stream::iter(events)
        });

        Ok(Box::pin(processed_stream))
    }
}

fn extend_capped(buffer: &mut Vec<u8>, data: &[u8], max: usize) {
    buffer.extend_from_slice(data);
    let overflow = buffer.len().saturating_sub(max);
    if overflow > 0 {
        buffer.drain(0..overflow);
    }
}

fn evict_over_capacity<T>(map: &mut HashMap<(u64, u32), T>, max: usize) {
    while map.len() > max {
        let Some(key) = map.keys().next().copied() else {
            break;
        };
        map.remove(&key);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzers::{HTTPDecompressor, SSEProcessor};
    use crate::view::MaterializedView;
    use flate2::write::GzEncoder;
    use flate2::{Compress, Compression, FlushCompress};
    use futures::StreamExt;
    use hpack::Encoder as HpackEncoder;
    use serde_json::json;
    use std::io::Write;

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
                "data_hex": hex::encode(&bytes),
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

    fn compressed_websocket_frame(compressor: &mut Compress, payload: &[u8]) -> Vec<u8> {
        let mut compressed = Vec::with_capacity(payload.len() * 2 + 64);
        compressor
            .compress_vec(payload, &mut compressed, FlushCompress::Sync)
            .unwrap();
        assert!(compressed.ends_with(&[0, 0, 0xff, 0xff]));
        compressed.truncate(compressed.len() - 4);

        let mut frame = vec![0xc1];
        if compressed.len() <= 125 {
            frame.push(0x80 | compressed.len() as u8);
        } else {
            frame.push(0x80 | 126);
            frame.extend_from_slice(&(compressed.len() as u16).to_be_bytes());
        }
        let mask = [0x12, 0x34, 0x56, 0x78];
        frame.extend_from_slice(&mask);
        frame.extend(
            compressed
                .iter()
                .enumerate()
                .map(|(i, byte)| byte ^ mask[i % 4]),
        );
        frame
    }

    #[tokio::test]
    async fn parses_compressed_websocket_responses_with_context_takeover() {
        let handshake = b"GET /backend-api/codex/responses HTTP/1.1\r\n\
Host: chatgpt.com\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n\
sec-websocket-extensions: permessage-deflate\r\n\r\n"
            .to_vec();
        let shared = "shared context ".repeat(400);
        let first = json!({
            "type": "response.create",
            "model": "gpt-test",
            "input": [{"role": "developer", "content": shared}],
        })
        .to_string();
        let prompt = "agentsight websocket exact prompt 7f31";
        let second = json!({
            "type": "response.create",
            "model": "gpt-test",
            "input": [{"role": "user", "content": format!("{shared}{prompt}")}],
        })
        .to_string();
        let mut compressor = Compress::new(Compression::fast(), false);
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", handshake),
            ssl_event(
                2,
                "WRITE/SEND",
                compressed_websocket_frame(&mut compressor, first.as_bytes()),
            ),
            ssl_event(
                3,
                "WRITE/SEND",
                compressed_websocket_frame(&mut compressor, second.as_bytes()),
            ),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 3);
        assert_eq!(output[2].data["path"], "/backend-api/codex/responses");
        assert!(output[2].data["body"].as_str().unwrap().contains(prompt));
        let mut view = MaterializedView::new();
        for event in output {
            view.ingest_event(&event).unwrap();
        }
        let calls = view.llm_call_rows(10);
        assert_eq!(calls.len(), 2);
        assert_eq!(calls[0].call_kind.as_deref(), Some("responses"));
        assert!(
            calls
                .iter()
                .any(|call| call.request.to_string().contains(prompt))
        );
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

        let mut view = MaterializedView::new();
        for event in output {
            view.ingest_event(&event).unwrap();
        }
        let total = view
            .export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 })
            .token_summary
            .into_iter()
            .map(|row| row.total_tokens)
            .sum::<i64>();
        assert_eq!(total, 15);
    }

    #[tokio::test]
    async fn http2_gzip_sse_capture_pipeline_reaches_materialized_view() {
        let mut request_encoder = HpackEncoder::new();
        let mut response_encoder = HpackEncoder::new();
        let request_headers = [
            (&b":method"[..], &b"POST"[..]),
            (&b":scheme"[..], &b"https"[..]),
            (&b":authority"[..], &b"api.openai.com"[..]),
            (&b":path"[..], &b"/v1/chat/completions"[..]),
        ];
        let response_headers = [
            (&b":status"[..], &b"200"[..]),
            (&b"content-type"[..], &b"text/event-stream"[..]),
            (&b"content-encoding"[..], &b"gzip"[..]),
        ];
        let request_body = br#"{"model":"gpt-test","metadata":{"session_id":"sess-h2"}}"#;
        let mut gzip = GzEncoder::new(Vec::new(), Compression::default());
        gzip.write_all(
            b"data: {\"choices\":[{\"finish_reason\":\"stop\"}],\"usage\":{\"prompt_tokens\":2,\"completion_tokens\":5}}\n\ndata: [DONE]\n\n",
        )
        .unwrap();
        let response_body = gzip.finish().unwrap();

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
        response_bytes.extend(frame(0x0, 0x1, 1, &response_body));

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", request_bytes),
            ssl_event(2, "READ/RECV", response_bytes),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let parsed = parser.process(input).await.unwrap();
        let mut decompressor = HTTPDecompressor::new();
        let decompressed = decompressor.process(parsed).await.unwrap();
        let mut sse = SSEProcessor::new();
        let output: Vec<Event> = sse.process(decompressed).await.unwrap().collect().await;

        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["message_type"], "request");
        assert_eq!(output[1].source, "sse_processor");
        assert_eq!(output[1].data["status_code"], 200);

        let mut view = MaterializedView::new();
        for event in output {
            view.ingest_event(&event).unwrap();
        }
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.llm_calls, 1);
        assert_eq!(snapshot.summary.token_usage_rows, 1);
        assert_eq!(snapshot.summary.input_tokens, 2);
        assert_eq!(snapshot.summary.output_tokens, 5);
        assert_eq!(snapshot.summary.total_tokens, 7);
        let calls = view.llm_call_rows(10);
        assert_eq!(calls[0].status, "complete");
        assert_eq!(calls[0].session_id.as_deref(), Some("sess-h2"));
        assert_eq!(calls[0].call_kind.as_deref(), Some("chat"));
        assert_eq!(calls[0].finish_reason.as_deref(), Some("stop"));
    }

    #[test]
    fn rejects_non_http2_frames() {
        assert!(parse_http2_frames(b"GET / HTTP/1.1\r\n\r\n").is_none());
    }
}
