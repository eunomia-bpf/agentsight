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
const MAX_HTTP1_STREAMS: usize = 1024;
const MAX_HTTP_BODY_BYTES: usize = 1024 * 1024;
const MAX_HTTP2_HEADER_BLOCK_BYTES: usize = 64 * 1024;

/// HTTP Parser Analyzer that parses SSL traffic into HTTP requests/responses
pub struct HTTPParser {
    /// Flag to include raw data in parsed events (default: true)
    include_raw_data: bool,
    http1: HTTP1State,
    http2: HTTP2State,
    websocket: WebSocketState,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
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
struct HTTP1State {
    streams: HashMap<(u32, u64, HTTP2Direction), HTTP1Acc>,
}

struct HTTP1Acc {
    buf: Vec<u8>,
    original: Event,
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
            http1: HTTP1State::default(),
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
            .and_then(|value| parse_http1_content_length_value(value).ok());
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
        http1: &mut HTTP1State,
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

        let data_bytes = ssl_data
            .get("data_hex")
            .and_then(|v| v.as_str())
            .and_then(|v| hex::decode(v).ok())
            .unwrap_or_else(|| ssl_json_string_to_bytes(data_str));
        if let Some(events) = http1.handle(&event, &data_bytes, include_raw_data, websocket) {
            return events;
        }
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

impl HTTP1State {
    fn handle(
        &mut self,
        event: &Event,
        bytes: &[u8],
        include_raw_data: bool,
        websocket: &mut WebSocketState,
    ) -> Option<Vec<Event>> {
        let direction = direction_from_function(
            event
                .data
                .get("function")
                .and_then(|v| v.as_str())
                .unwrap_or(""),
        )?;
        let tid = event.data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
        let key = (event.pid, tid, direction);

        if event
            .data
            .get("truncated")
            .and_then(|v| v.as_bool())
            .unwrap_or(false)
        {
            // A truncated record lost its tail, so anything accumulated for
            // this key can never complete; drop the pending state.
            self.streams.remove(&key);
            return None;
        }

        if bytes.len() > MAX_HTTP_BODY_BYTES {
            self.streams.remove(&key);
            return None;
        }

        let mut acc = if looks_like_http1_start(bytes) {
            // A recognizable new start on this key resyncs the stream: any
            // incomplete message left pending can no longer complete.
            self.streams.remove(&key);
            HTTP1Acc {
                buf: bytes.to_vec(),
                original: event.clone(),
            }
        } else {
            let mut acc = self.streams.remove(&key)?;
            let buffered_len = acc.buf.len().checked_add(bytes.len())?;
            if buffered_len > MAX_HTTP_BODY_BYTES {
                // Never front-truncate: the retained bytes must stay a valid
                // prefix of the stream, so drop the whole state instead.
                return None;
            }
            acc.buf.extend_from_slice(bytes);
            acc
        };
        let tid = acc
            .original
            .data
            .get("tid")
            .and_then(|v| v.as_u64())
            .unwrap_or(tid);

        let mut events = Vec::new();
        let mut cursor = 0usize;
        loop {
            match scan_http1_message(&acc.buf[cursor..]) {
                Http1Scan::Complete { message, consumed } => {
                    websocket.observe_handshake(&acc.original, &message);
                    events.push(HTTPParser::create_http_event(
                        tid,
                        *message,
                        &acc.original,
                        include_raw_data,
                    ));
                    cursor += consumed;
                }
                Http1Scan::Incomplete => break,
                Http1Scan::Malformed => {
                    cursor = acc.buf.len();
                    break;
                }
            }
        }

        if cursor > 0 {
            acc.buf.drain(0..cursor);
        }
        if !acc.buf.is_empty() {
            self.streams.insert(key, acc);
            evict_http1(&mut self.streams);
        }

        Some(events)
    }
}

fn looks_like_http1_start(bytes: &[u8]) -> bool {
    let text = String::from_utf8_lossy(bytes);
    // Resynchronization is only safe at byte offset zero. Leading CR/LF may
    // finish framing buffered from the prior record (for example, the final
    // empty line after a zero chunk) and must be appended before scanning.
    let first = text.split(['\r', '\n']).next().unwrap_or("");
    if first.starts_with("HTTP/1.") {
        return true;
    }
    let parts: Vec<&str> = first.splitn(3, ' ').collect();
    parts.len() >= 3
        && matches!(
            parts[0],
            "GET" | "POST" | "PUT" | "DELETE" | "HEAD" | "OPTIONS" | "PATCH"
        )
        && parts[2].starts_with("HTTP/1.")
}

enum Http1Scan {
    Complete {
        message: Box<HTTPMessage>,
        consumed: usize,
    },
    Incomplete,
    Malformed,
}

/// Scan one HTTP/1 message at the front of `buf`.
///
/// `Complete` returns the exact byte boundary of the message so a pipelined
/// next message can be scanned right after it. `Incomplete` means more bytes
/// are required. `Malformed` means the framing is broken and the pending
/// state should be dropped.
fn scan_http1_message(buf: &[u8]) -> Http1Scan {
    // A record boundary may leave empty lines in front of the message start.
    let lead = buf
        .iter()
        .take_while(|byte| **byte == b'\r' || **byte == b'\n')
        .count();
    let buf = &buf[lead..];
    const SEP: &[u8] = b"\r\n\r\n";
    let Some(pos) = buf.windows(4).position(|window| window == SEP) else {
        return Http1Scan::Incomplete;
    };
    let header_end = pos + 4;
    let headers = &buf[..pos];
    let content_length = match http1_content_length(headers) {
        Http1ContentLength::Absent => None,
        Http1ContentLength::Valid(value) => Some(value),
        Http1ContentLength::Invalid => return Http1Scan::Malformed,
    };
    let body_end = if http1_header_is_chunked(headers) {
        match chunked_message_end(buf, header_end) {
            ChunkedEnd::Complete(end) => end,
            ChunkedEnd::Incomplete => return Http1Scan::Incomplete,
            ChunkedEnd::Malformed => return Http1Scan::Malformed,
        }
    } else if let Some(content_length) = content_length {
        let Some(need) = header_end.checked_add(content_length) else {
            return Http1Scan::Malformed;
        };
        if buf.len() < need {
            return Http1Scan::Incomplete;
        }
        need
    } else {
        // Requests carry no body without Content-Length or chunked framing,
        // so the message ends at the header terminator; a response without
        // either is close-delimited and the buffered bytes are its body.
        let header_text = String::from_utf8_lossy(&buf[..pos]);
        let first_line = header_text
            .split(['\r', '\n'])
            .find(|line| !line.is_empty())
            .unwrap_or("");
        if first_line.starts_with("HTTP/1.") {
            buf.len()
        } else {
            header_end
        }
    };
    let Some(message) = HTTPParser::parse_http_message(&String::from_utf8_lossy(&buf[..body_end]))
    else {
        return Http1Scan::Malformed;
    };
    Http1Scan::Complete {
        message: Box::new(message),
        consumed: body_end + lead,
    }
}

enum ChunkedEnd {
    Complete(usize),
    Incomplete,
    Malformed,
}

/// Walk the chunked framing from `start` through the zero chunk and its
/// trailer block. Returns the exact end of the message, or signals that more
/// bytes are needed, or that the framing is malformed.
fn chunked_message_end(buf: &[u8], start: usize) -> ChunkedEnd {
    let mut cursor = start;
    loop {
        let Some(size_pos) = find_crlf(buf, cursor) else {
            return ChunkedEnd::Incomplete;
        };
        let Some(size) = parse_chunk_size(&buf[cursor..size_pos]) else {
            return ChunkedEnd::Malformed;
        };
        let Some(data_start) = size_pos.checked_add(2) else {
            return ChunkedEnd::Malformed;
        };
        if size == 0 {
            // A zero chunk is followed by zero or more trailer field lines and
            // one final empty line. Do not stop after the first trailer.
            let mut trailer_start = data_start;
            loop {
                let Some(line_end) = find_crlf(buf, trailer_start) else {
                    return ChunkedEnd::Incomplete;
                };
                let Some(next) = line_end.checked_add(2) else {
                    return ChunkedEnd::Malformed;
                };
                if line_end == trailer_start {
                    return ChunkedEnd::Complete(next);
                }
                trailer_start = next;
            }
        }
        let Some(data_end) = data_start.checked_add(size) else {
            return ChunkedEnd::Malformed;
        };
        let Some(next) = data_end.checked_add(2) else {
            return ChunkedEnd::Malformed;
        };
        if buf.len() < next {
            return ChunkedEnd::Incomplete;
        }
        if &buf[data_end..next] != b"\r\n" {
            return ChunkedEnd::Malformed;
        }
        cursor = next;
    }
}

fn find_crlf(buf: &[u8], from: usize) -> Option<usize> {
    buf.get(from..)?
        .windows(2)
        .position(|window| window == b"\r\n")
        .map(|pos| from + pos)
}

fn parse_chunk_size(line: &[u8]) -> Option<usize> {
    let end = line
        .iter()
        .position(|&byte| byte == b';')
        .unwrap_or(line.len());
    let size = std::str::from_utf8(&line[..end]).ok()?;
    if size.is_empty() {
        return None;
    }
    usize::from_str_radix(size, 16).ok()
}

enum Http1ContentLength {
    Absent,
    Valid(usize),
    Invalid,
}

fn http1_content_length(headers: &[u8]) -> Http1ContentLength {
    let text = String::from_utf8_lossy(headers);
    let mut found = None;
    for line in text.split("\r\n") {
        let Some((key, value)) = line.split_once(':') else {
            continue;
        };
        if key.eq_ignore_ascii_case("content-length") {
            // RFC 9110 permits recipients to combine identical duplicate
            // values into a comma-separated field. Any empty, non-decimal,
            // overflowing, or conflicting value is invalid framing.
            let Ok(value) = parse_http1_content_length_value(value) else {
                return Http1ContentLength::Invalid;
            };
            match found {
                Some(previous) if previous != value => {
                    return Http1ContentLength::Invalid;
                }
                Some(_) => {}
                None => found = Some(value),
            }
        }
    }
    match found {
        Some(value) => Http1ContentLength::Valid(value),
        None => Http1ContentLength::Absent,
    }
}

fn parse_http1_content_length_value(values: &str) -> Result<usize, ()> {
    let mut found = None;
    for value in values.split(',') {
        let value = value.trim();
        if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err(());
        }
        let value = value.parse::<usize>().map_err(|_| ())?;
        match found {
            Some(previous) if previous != value => return Err(()),
            Some(_) => {}
            None => found = Some(value),
        }
    }
    found.ok_or(())
}

fn http1_header_is_chunked(headers: &[u8]) -> bool {
    let text = String::from_utf8_lossy(headers);
    text.split("\r\n").any(|line| {
        line.split_once(':')
            .map(|(key, value)| {
                key.eq_ignore_ascii_case("transfer-encoding")
                    && value.to_ascii_lowercase().contains("chunked")
            })
            .unwrap_or(false)
    })
}

fn evict_http1(map: &mut HashMap<(u32, u64, HTTP2Direction), HTTP1Acc>) {
    while map.len() > MAX_HTTP1_STREAMS {
        let Some(key) = map.keys().next().copied() else {
            break;
        };
        map.remove(&key);
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
        let mut http1 = std::mem::take(&mut self.http1);
        let mut http2 = std::mem::take(&mut self.http2);
        let mut websocket = std::mem::take(&mut self.websocket);

        let processed_stream = stream.flat_map(move |event| {
            let events = if event.source == "ssl" {
                Self::handle_ssl_event(
                    &mut http1,
                    &mut http2,
                    &mut websocket,
                    event,
                    include_raw_data,
                )
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

    #[tokio::test]
    async fn reassembles_split_http1_codex_request_into_llm_call() {
        // Codex 0.153 posts ~40KB /v1/responses bodies. OpenSSL/rustls emit
        // 8-16KB records, so the first chunk is not valid JSON and used to
        // be dropped before llm_calls/audit_events were written.
        let prompt = "agentsight mock prompt collect this exact text";
        let body = json!({
            "model": "gpt-agentsight-mock",
            "input": [{"role": "user", "content": prompt}],
        })
        .to_string();
        let header = format!(
            "POST /v1/responses HTTP/1.1\r\nHost: 127.0.0.1\r\n\
Content-Type: application/json\r\nContent-Length: {}\r\n\r\n",
            body.len()
        );
        let mut raw = header.into_bytes();
        raw.extend(body.as_bytes());
        let first = raw.len() / 3;
        let second = first * 2;
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "READ/RECV", raw[..first].to_vec()),
            ssl_event(2, "READ/RECV", raw[first..second].to_vec()),
            ssl_event(3, "READ/RECV", raw[second..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 1);
        assert_eq!(output[0].source, "http_parser");
        assert_eq!(output[0].data["path"], "/v1/responses");
        assert!(output[0].data["body"].as_str().unwrap().contains(prompt));

        let mut view = MaterializedView::new();
        view.ingest_event(&output[0]).unwrap();
        let calls = view.llm_call_rows(10);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].path.as_deref(), Some("/v1/responses"));
        assert!(calls[0].request.to_string().contains(prompt));
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 8 });
        assert!(
            snapshot
                .audit_events
                .iter()
                .any(|event| event.audit_type == "llm"
                    && event.action.as_deref() == Some("request")
                    && event.details.to_string().contains(prompt))
        );
    }

    #[tokio::test]
    async fn http1_segmented_body_emits_only_when_content_length_reached() {
        let body = r#"{"model":"gpt-4","messages":[{"role":"user","content":"boundary probe"}]}"#
            .to_string();
        let raw = format!(
            "POST /v1/chat/completions HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Type: application/json\r\nContent-Length: {}\r\n\r\n{body}",
            body.len()
        )
        .into_bytes();
        let first = raw.len() / 3;
        let second = first * 2;
        let parts = [
            raw[..first].to_vec(),
            raw[first..second].to_vec(),
            raw[second..].to_vec(),
        ];

        for count in 1..parts.len() {
            let events: Vec<Event> = parts[..count]
                .iter()
                .enumerate()
                .map(|(i, chunk)| ssl_event(i as u64 + 1, "WRITE/SEND", chunk.clone()))
                .collect();
            let input: EventStream = Box::pin(stream::iter(events));
            let mut parser = HTTPParser::new().disable_raw_data();
            let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
            assert_eq!(
                output.len(),
                0,
                "no event may be emitted before Content-Length bytes arrive"
            );
        }

        let events: Vec<Event> = parts
            .iter()
            .enumerate()
            .map(|(i, chunk)| ssl_event(i as u64 + 1, "WRITE/SEND", chunk.clone()))
            .collect();
        let input: EventStream = Box::pin(stream::iter(events));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["path"], "/v1/chat/completions");
        assert_eq!(output[0].data["body"].as_str().unwrap(), body);
    }

    #[tokio::test]
    async fn http1_pipelined_buffer_emits_every_complete_message() {
        let first_body =
            r#"{"model":"gpt-4","messages":[{"role":"user","content":"first"}]}"#.to_string();
        let second_body =
            r#"{"model":"gpt-4","messages":[{"role":"user","content":"second"}]}"#.to_string();
        let raw = format!(
            "POST /first HTTP/1.1\r\nHost: api.openai.com\r\nContent-Length: {}\r\n\r\n{first_body}\
POST /second HTTP/1.1\r\nHost: api.openai.com\r\nContent-Length: {}\r\n\r\n{second_body}",
            first_body.len(),
            second_body.len()
        )
        .into_bytes();

        let input: EventStream =
            Box::pin(stream::iter(vec![ssl_event(1, "WRITE/SEND", raw.clone())]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/first");
        assert_eq!(
            output[0].data["body"].as_str().unwrap(),
            first_body,
            "first message body must be exactly the declared Content-Length"
        );
        assert_eq!(output[1].data["path"], "/second");
        assert_eq!(
            output[1].data["body"].as_str().unwrap(),
            second_body,
            "second message body must be exactly the declared Content-Length"
        );

        // Split the second message across a TLS chunk boundary: the tail of
        // the first chunk is retained under the same stream key and the
        // message only completes once the remaining bytes arrive.
        let split_at = raw.len() - second_body.len() / 2;
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..split_at].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[split_at..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/first");
        assert_eq!(output[0].data["body"].as_str().unwrap(), first_body);
        assert_eq!(output[1].data["path"], "/second");
        assert_eq!(
            output[1].data["body"].as_str().unwrap(),
            second_body,
            "split tail must complete from retained bytes plus later chunk"
        );
    }

    #[tokio::test]
    async fn http1_strict_content_length_holds_complete_json_with_trailing_whitespace() {
        // Declared Content-Length includes trailing legal whitespace bytes,
        // so the JSON body is syntactically complete before the declared
        // length is reached. A complete JSON body must not override the
        // declared Content-Length: nothing may emit before the final byte,
        // and a stream that ends short must emit nothing at all.
        let json_body =
            r#"{"model":"gpt-4","messages":[{"role":"user","content":"strict tail"}]}"#.to_string();
        let body = format!("{json_body} \n");
        assert!(serde_json::from_str::<serde_json::Value>(&json_body).is_ok());
        assert!(
            body.strip_prefix(&json_body)
                .is_some_and(|trailing| trailing.bytes().all(|b| b.is_ascii_whitespace()))
        );

        let raw = format!(
            "POST /v1/chat/completions HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Type: application/json\r\nContent-Length: {}\r\n\r\n{body}",
            body.len()
        )
        .into_bytes();

        // No event before the final declared byte arrives (also EOF
        // short-body: the stream ends under the declared Content-Length).
        let input: EventStream = Box::pin(stream::iter(vec![ssl_event(
            1,
            "WRITE/SEND",
            raw[..raw.len() - 1].to_vec(),
        )]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(
            output.len(),
            0,
            "complete JSON must not override the declared Content-Length"
        );

        // Exactly one event after the final declared byte arrives.
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..raw.len() - 1].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[raw.len() - 1..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["path"], "/v1/chat/completions");
        assert_eq!(output[0].data["body"].as_str().unwrap(), body);
    }

    #[tokio::test]
    async fn http1_no_content_length_requests_end_at_header_end() {
        // Two GETs without Content-Length pipelined in one record: each
        // message ends at its header terminator, so neither swallows the
        // other's bytes as a body.
        let raw = b"GET /one HTTP/1.1\r\nHost: api.openai.com\r\n\r\n\
GET /two HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";
        let input: EventStream =
            Box::pin(stream::iter(vec![ssl_event(1, "WRITE/SEND", raw.to_vec())]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/one");
        assert_eq!(output[1].data["path"], "/two");
        assert_eq!(output[0].data["has_body"], false);
        assert_eq!(output[1].data["has_body"], false);
    }

    #[tokio::test]
    async fn http1_split_chunked_completes_incrementally_with_pipelined_next() {
        let chunked_body = "5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n";
        let raw = format!(
            "POST /upload HTTP/1.1\r\nHost: api.openai.com\r\n\
Transfer-Encoding: chunked\r\n\r\n{chunked_body}\
GET /next HTTP/1.1\r\nHost: api.openai.com\r\n\r\n"
        )
        .into_bytes();

        // Whole record at once: the chunked request completes at its zero
        // chunk + trailer terminator and the pipelined GET parses right after.
        let input: EventStream =
            Box::pin(stream::iter(vec![ssl_event(1, "WRITE/SEND", raw.clone())]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/upload");
        assert_eq!(output[0].data["is_chunked"], true);
        assert_eq!(
            output[0].data["body"].as_str().unwrap(),
            chunked_body,
            "chunked body must keep the exact raw framing through the zero chunk"
        );
        assert_eq!(output[1].data["path"], "/next");

        // Split across a TLS record inside the last chunk's data: the chunked
        // message must not emit until the zero chunk and trailer terminator
        // arrive, then the pipelined GET must still parse from the remainder.
        let split_at = raw
            .windows(3)
            .position(|window| window == b"0\r\n")
            .unwrap()
            - 4; // inside " world"
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..split_at].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[split_at..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/upload");
        assert_eq!(output[0].data["body"].as_str().unwrap(), chunked_body);
        assert_eq!(output[1].data["path"], "/next");

        // When the final empty line after the zero chunk straddles the record
        // boundary, its leading CRLF completes the pending message before the
        // pipelined request. It is not an offset-zero resynchronization point.
        let split_at = raw
            .windows(8)
            .position(|window| window == b"0\r\n\r\nGET")
            .unwrap()
            + 3; // after "0\r\n"
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..split_at].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[split_at..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/upload");
        assert_eq!(output[0].data["body"].as_str().unwrap(), chunked_body);
        assert_eq!(output[1].data["path"], "/next");
    }

    #[tokio::test]
    async fn http1_chunked_waits_for_complete_trailer_section() {
        let chunked_body = "1\r\na\r\n0\r\nX-Checksum: one\r\nX-Trace: two\r\n\r\n";
        let raw = format!(
            "POST /trailers HTTP/1.1\r\nHost: api.openai.com\r\n\
Transfer-Encoding: chunked\r\n\r\n{chunked_body}\
GET /next HTTP/1.1\r\nHost: api.openai.com\r\n\r\n"
        )
        .into_bytes();
        let split_at = raw
            .windows(b"X-Trace".len())
            .position(|window| window == b"X-Trace")
            .unwrap();
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..split_at].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[split_at..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/trailers");
        assert_eq!(output[0].data["body"].as_str().unwrap(), chunked_body);
        assert_eq!(output[1].data["path"], "/next");
    }

    #[tokio::test]
    async fn http1_malformed_or_overflowing_framing_drops_state() {
        // Non-hex chunk size: the message is malformed, nothing emits, and the
        // pending state is dropped so a later request on the same key can parse.
        let malformed = b"POST /bad HTTP/1.1\r\nHost: api.openai.com\r\n\
Transfer-Encoding: chunked\r\n\r\nzz\r\n";
        let recovered = b"GET /after HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", malformed.to_vec()),
            ssl_event(2, "WRITE/SEND", recovered.to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["path"], "/after");

        // Chunk size that overflows usize: also malformed, state dropped.
        let overflow = b"POST /big HTTP/1.1\r\nHost: api.openai.com\r\n\
Transfer-Encoding: chunked\r\n\r\nFFFFFFFFFFFFFFFFFFFFF\r\n";
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", overflow.to_vec()),
            ssl_event(2, "WRITE/SEND", recovered.to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["path"], "/after");

        // Content-Length that overflows the header/body offset math: malformed,
        // state dropped, recovery still works.
        let cl_overflow = b"POST /huge HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: 184467440737095516150\r\n\r\n";
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", cl_overflow.to_vec()),
            ssl_event(2, "WRITE/SEND", recovered.to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["path"], "/after");
    }

    #[tokio::test]
    async fn http1_content_length_rejects_malformed_and_conflicting_values() {
        let recovered = b"GET /after HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";
        let invalid_messages: [&[u8]; 3] = [
            b"POST /signed HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: +4\r\n\r\ntest",
            b"POST /overflow HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: 184467440737095516150\r\n\r\n",
            b"POST /conflict HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: 4\r\nContent-Length: 5\r\n\r\ntest!",
        ];

        for invalid in invalid_messages {
            let input: EventStream = Box::pin(stream::iter(vec![
                ssl_event(1, "WRITE/SEND", invalid.to_vec()),
                ssl_event(2, "WRITE/SEND", recovered.to_vec()),
            ]));
            let mut parser = HTTPParser::new().disable_raw_data();
            let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
            assert_eq!(output.len(), 1);
            assert_eq!(output[0].data["path"], "/after");
        }

        // Identical duplicate values, including a comma-combined field, are
        // unambiguous and retain the exact body boundary.
        let valid = b"POST /same HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: 4\r\nContent-Length: 4, 4\r\n\r\ntest\
GET /next HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";
        let input: EventStream = Box::pin(stream::iter(vec![ssl_event(
            1,
            "WRITE/SEND",
            valid.to_vec(),
        )]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["path"], "/same");
        assert_eq!(output[0].data["body"], "test");
        assert_eq!(output[0].data["content_length"], 4);
        assert_eq!(output[1].data["path"], "/next");
    }

    #[tokio::test]
    async fn http1_close_delimited_response_keeps_http_looking_body_bytes() {
        let body = "prefix\r\nGET /not-a-pipeline HTTP/1.1\r\nHost: body.example\r\n\r\n";
        let raw = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n{body}"
        )
        .into_bytes();
        let input: EventStream = Box::pin(stream::iter(vec![ssl_event(1, "READ/RECV", raw)]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["message_type"], "response");
        assert_eq!(output[0].data["body"].as_str().unwrap(), body);
    }

    #[tokio::test]
    async fn http1_truncated_event_drops_pending_state_and_recovers() {
        let body = "abcdefghijklmnopqrstuvwxyz012345";
        let raw = format!(
            "POST /chat HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: {}\r\n\r\n{body}",
            body.len()
        )
        .into_bytes();
        let recovered = b"GET /after HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";

        let mut events: Vec<Event> = Vec::new();
        // Partial request body is pending when the next record arrives...
        // The first record includes the complete request line so it is
        // recognized as HTTP/1, while the declared body remains incomplete.
        for chunk in raw.chunks(24) {
            events.push(ssl_event(
                events.len() as u64 + 1,
                "WRITE/SEND",
                chunk.to_vec(),
            ));
        }
        // ...and is truncated, dropping the pending accumulation.
        events.pop();
        let truncated_bytes = &raw[50..];
        let truncated_event =
            ssl_event_truncated(events.len() as u64 + 1, "WRITE/SEND", truncated_bytes);
        let expected_truncated = truncated_event.clone();
        events.push(truncated_event);
        events.push(ssl_event(
            events.len() as u64 + 1,
            "WRITE/SEND",
            recovered.to_vec(),
        ));

        let input: EventStream = Box::pin(stream::iter(events));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        let preserved = output
            .iter()
            .find(|event| event.source == "ssl")
            .expect("truncated SSL record must pass through unchanged");
        assert_eq!(preserved, &expected_truncated);
        let parsed: Vec<&Event> = output
            .iter()
            .filter(|event| event.source == "http_parser")
            .collect();
        assert_eq!(parsed.len(), 1);
        assert_eq!(parsed[0].data["path"], "/after");
    }

    fn ssl_event_truncated(timestamp: u64, function: &str, bytes: &[u8]) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            4242,
            "node".to_string(),
            json!({
                "tid": 7,
                "function": function,
                "data": bytes_to_ssl_json_string(bytes),
                "data_hex": hex::encode(bytes),
                "truncated": true,
            }),
        )
    }

    #[tokio::test]
    async fn http1_cap_overflow_drops_whole_state_and_recovers() {
        // The accumulated buffer crosses the 1MiB cap: the whole pending state
        // is dropped (never front-truncated) and the next fresh request parses.
        let header =
            "POST /big HTTP/1.1\r\nHost: api.openai.com\r\nContent-Length: 1200000\r\n\r\n";
        let part1 = format!("{header}{}", "a".repeat(900_000)).into_bytes();
        let part2 = vec![b'b'; 300_000];
        let recovered = b"GET /after HTTP/1.1\r\nHost: api.openai.com\r\n\r\n";
        let overflow_event = ssl_event(2, "WRITE/SEND", part2);
        let expected_overflow = overflow_event.clone();

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", part1),
            overflow_event,
            ssl_event(3, "WRITE/SEND", recovered.to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 2);
        let preserved = output
            .iter()
            .find(|event| event.source == "ssl")
            .expect("overflowing SSL record must pass through unchanged");
        assert_eq!(preserved, &expected_overflow);
        let parsed: Vec<&Event> = output
            .iter()
            .filter(|event| event.source == "http_parser")
            .collect();
        assert_eq!(parsed.len(), 1);
        assert_eq!(parsed[0].data["path"], "/after");
    }

    #[tokio::test]
    async fn http1_many_pipelined_requests_emit_in_order() {
        let mut raw = Vec::new();
        for i in 0..10 {
            raw.extend_from_slice(
                format!("GET /page{i} HTTP/1.1\r\nHost: api.openai.com\r\n\r\n").as_bytes(),
            );
        }

        // All ten in one record.
        let input: EventStream =
            Box::pin(stream::iter(vec![ssl_event(1, "WRITE/SEND", raw.clone())]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 10);
        for (i, event) in output.iter().enumerate() {
            assert_eq!(event.data["path"], format!("/page{i}"));
        }

        // Last request split across a record boundary, inside its headers.
        let split_at = raw.len() - 10;
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", raw[..split_at].to_vec()),
            ssl_event(2, "WRITE/SEND", raw[split_at..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;
        assert_eq!(output.len(), 10);
        for (i, event) in output.iter().enumerate() {
            assert_eq!(event.data["path"], format!("/page{i}"));
        }
    }

    #[tokio::test]
    async fn http1_direction_keys_isolate_request_and_response_streams() {
        // Same pid/tid, opposite directions: interleaved partial records must
        // accumulate under separate keys and complete independently.
        let request_body = "abcdefghijklmnopqrstuvwxyz012345";
        let response_body = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345";
        assert_eq!(request_body.len(), 32);
        assert_eq!(response_body.len(), 32);
        let request = format!(
            "POST /chat HTTP/1.1\r\nHost: api.openai.com\r\n\
Content-Length: 32\r\n\r\n{request_body}"
        )
        .into_bytes();
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\
Content-Length: 32\r\n\r\n{response_body}"
        )
        .into_bytes();
        let cut_req = request.len() - 16; // split inside the body
        let cut_resp = response.len() - 16;

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", request[..cut_req].to_vec()),
            ssl_event(2, "READ/RECV", response[..cut_resp].to_vec()),
            ssl_event(3, "WRITE/SEND", request[cut_req..].to_vec()),
            ssl_event(4, "READ/RECV", response[cut_resp..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["message_type"], "request");
        assert_eq!(output[0].data["path"], "/chat");
        assert_eq!(output[0].data["body"].as_str().unwrap(), request_body);
        assert_eq!(output[1].data["message_type"], "response");
        assert_eq!(output[1].data["status_code"], 200);
        assert_eq!(output[1].data["body"].as_str().unwrap(), response_body);
    }
}
