// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::capture_metadata::CaptureMetadataAccumulator;
use super::connection_registry::{ConnectionIdentity, ConnectionRegistry};
use super::protocol_events::HTTPEvent;
use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_trait::async_trait;
use flate2::{Decompress, FlushDecompress};
use futures::stream::StreamExt;
use hpack::Decoder as HpackDecoder;
use std::collections::{BTreeSet, HashMap, HashSet, VecDeque};

const MAX_HTTP2_STREAMS: usize = 1024;
const MAX_HTTP2_PENDING_HEADERS: usize = 1024;
const MAX_HTTP_BODY_BYTES: usize = 1024 * 1024;
const MAX_HTTP2_HEADER_BLOCK_BYTES: usize = 64 * 1024;
const MAX_HTTP2_FRAME_BUFFER_BYTES: usize = (16 * 1024 * 1024) + 9;
const MAX_HTTP1_CONNECTIONS: usize = 1_024;
const MAX_HTTP2_CONNECTIONS: usize = 1_024;
const MAX_HTTP1_BUFFER_BYTES: usize = 2 * 1024 * 1024;
const MAX_BUFFERED_FRAGMENTS: usize = 4_096;
const MAX_HTTP1_PENDING_REQUESTS: usize = 1_024;

/// HTTP Parser Analyzer that parses SSL traffic into HTTP requests/responses
pub struct HTTPParser {
    /// Flag to include raw data in parsed events (default: true)
    include_raw_data: bool,
    registry: ConnectionRegistry,
    http1: HashMap<String, HTTP1ConnectionState>,
    http2: HashMap<String, HTTP2State>,
    websocket: WebSocketState,
    quarantined: HashSet<String>,
    last_loss_count: Option<u64>,
}

#[derive(Default)]
struct HTTP1ConnectionState {
    request_buffer: Vec<u8>,
    response_buffer: Vec<u8>,
    request_metadata: FragmentBuffer,
    response_metadata: FragmentBuffer,
    pending: VecDeque<(String, bool)>,
    next_request_seq: u64,
}

#[derive(Debug, Clone, Copy, Hash, PartialEq, Eq)]
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
    request_capture_metadata: MessageMetadata,
    response_capture_metadata: MessageMetadata,
}

struct PendingHTTP2Headers {
    direction: HTTP2Direction,
    block: Vec<u8>,
    end_stream: bool,
}

struct HTTP2Frame {
    frame_type: u8,
    flags: u8,
    stream_id: u32,
    payload: Vec<u8>,
}

// Keep provenance alongside buffered bytes. A TLS call may span frames/messages,
// and several frames may share one call. Count each contributing call once per
// derived message, including calls that supplied only a partial frame/header.
#[derive(Default)]
struct FragmentBuffer {
    next_id: u64,
    fragments: VecDeque<(usize, u64, Event)>,
}

#[derive(Default)]
struct MessageMetadata {
    last_id: Option<u64>,
    capture: CaptureMetadataAccumulator,
}

impl FragmentBuffer {
    fn push(&mut self, len: usize, event: &Event) {
        if len == 0 {
            return;
        }
        self.next_id += 1;
        let mut metadata_event = event.clone();
        if let Some(data) = metadata_event.data.as_object_mut() {
            data.remove("data");
            data.remove("data_hex");
        }
        self.fragments
            .push_back((len, self.next_id, metadata_event));
    }

    fn consume(&mut self, mut bytes: usize, target: &mut MessageMetadata) {
        while bytes > 0 {
            let Some((remaining, id, event)) = self.fragments.front_mut() else {
                break;
            };
            if target.last_id != Some(*id) {
                target.capture.observe_event(event);
                target.last_id = Some(*id);
            }
            let take = bytes.min(*remaining);
            bytes -= take;
            *remaining -= take;
            if *remaining == 0 {
                self.fragments.pop_front();
            }
        }
    }
}

struct HTTP2State {
    request_decoder: HpackDecoder<'static>,
    response_decoder: HpackDecoder<'static>,
    request_remainder: Vec<u8>,
    response_remainder: Vec<u8>,
    request_metadata: FragmentBuffer,
    response_metadata: FragmentBuffer,
    streams: HashMap<u32, HTTP2StreamState>,
    pending_headers: HashMap<(HTTP2Direction, u32), PendingHTTP2Headers>,
    request_hpack_valid: bool,
    response_hpack_valid: bool,
    goaway_last_stream_id: Option<u32>,
}

#[derive(Default)]
struct WebSocketState {
    connections: HashMap<String, WebSocketConnection>,
}

struct WebSocketConnection {
    path: String,
    headers: HashMap<String, String>,
    inflater: Decompress,
    handshake_capture_metadata: CaptureMetadataAccumulator,
}

impl Default for HTTP2State {
    fn default() -> Self {
        Self {
            request_decoder: HpackDecoder::new(),
            response_decoder: HpackDecoder::new(),
            request_remainder: Vec::new(),
            response_remainder: Vec::new(),
            request_metadata: FragmentBuffer::default(),
            response_metadata: FragmentBuffer::default(),
            streams: HashMap::new(),
            pending_headers: HashMap::new(),
            request_hpack_valid: true,
            response_hpack_valid: true,
            goaway_last_stream_id: None,
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
    body_bytes: Option<Vec<u8>>,
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
            registry: ConnectionRegistry::default(),
            http1: HashMap::new(),
            http2: HashMap::new(),
            websocket: WebSocketState::default(),
            quarantined: HashSet::new(),
            last_loss_count: None,
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
            body_bytes: None,
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
        connection: &ConnectionIdentity,
        http_exchange_id: Option<String>,
        correlation_method: Option<&str>,
    ) -> Event {
        let provisional = parsed_message.message_type == HTTPMessageType::Response
            && parsed_message
                .status_code
                .is_some_and(|code| code < 200 && code != 101);
        let message_type_str = match parsed_message.message_type {
            HTTPMessageType::Request => "request",
            HTTPMessageType::Response if provisional => "informational_response",
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
            .body_bytes
            .as_ref()
            .map(hex::encode)
            .or_else(|| {
                parsed_message
                    .body
                    .as_deref()
                    .map(ssl_json_string_to_bytes)
                    .map(hex::encode)
            });

        // Calculate total size from parsed components
        let total_size = parsed_message.first_line.len() +
            parsed_message.headers.iter().map(|(k, v)| k.len() + v.len() + 4).sum::<usize>() + // +4 for ": \r\n"
            parsed_message.body.as_ref().map(|b| b.len()).unwrap_or(0) +
            4; // +4 for \r\n\r\n separator

        HTTPEvent {
            capture_metadata: {
                let mut metadata = CaptureMetadataAccumulator::default();
                metadata.observe_event(original_event);
                metadata.finish()
            },
            tid,
            connection_id: Some(connection.id.clone()),
            connection_generation: Some(connection.generation),
            stream_id: None,
            http_exchange_id,
            correlation_method: correlation_method.map(str::to_string),
            correlation_status: correlation_method.map(|_| {
                if connection.exact {
                    "exact"
                } else {
                    "inferred"
                }
                .to_string()
            }),
            confidence: correlation_method.map(|_| if connection.exact { 0.98 } else { 0.75 }),
            correlation_version: if connection.exact { 2 } else { 1 },
            completion_reason: (!provisional).then(|| "done".to_string()),
            end_stream: !provisional,
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

    fn terminate_connection_state(
        &mut self,
        event: &Event,
        connection: &ConnectionIdentity,
        completion_reason: &str,
    ) -> Vec<Event> {
        self.quarantined.remove(&connection.id);
        let mut events = Vec::new();
        if let Some(mut state) = self.http1.remove(&connection.id) {
            if completion_reason == "closed"
                && !state.response_buffer.is_empty()
                && let Some((message, consumed)) = parse_next_http1_message(
                    &state.response_buffer,
                    HTTP2Direction::Response,
                    state.pending.front().is_some_and(|(_, head)| *head),
                    true,
                )
            {
                let mut metadata = MessageMetadata::default();
                state.response_metadata.consume(consumed, &mut metadata);
                let mut original = event.clone();
                original.data.as_object_mut().unwrap().extend(
                    serde_json::to_value(metadata.capture.finish())
                        .unwrap()
                        .as_object()
                        .unwrap()
                        .clone(),
                );
                let exchange = state.pending.pop_front().map(|(id, _)| id);
                let method = exchange.as_ref().map(|_| "h1_connection_fifo");
                let tid = event.data["tid"].as_u64().unwrap_or(0);
                let mut response = Self::create_http_event(
                    tid,
                    message,
                    &original,
                    self.include_raw_data,
                    connection,
                    exchange,
                    method,
                );
                response.data["completion_reason"] = serde_json::json!("closed");
                events.push(response);
                state.response_buffer.drain(..consumed);
            }
            for (direction, buffer) in [
                ("request", &state.request_buffer),
                ("response", &state.response_buffer),
            ] {
                if !buffer.is_empty() {
                    events.push(http_partial_event(
                        event,
                        connection,
                        "HTTP/1.1",
                        direction,
                        completion_reason,
                        buffer,
                        self.include_raw_data,
                    ));
                }
            }
            let exchanges = state.pending.drain(..).collect::<Vec<_>>();
            for (exchange_id, _) in exchanges {
                events.push(http1_terminal_event(
                    event,
                    connection,
                    &exchange_id,
                    completion_reason,
                ));
            }
        }
        if let Some(state) = self.http2.remove(&connection.id) {
            for (direction, remainder) in [
                ("request", &state.request_remainder),
                ("response", &state.response_remainder),
            ] {
                if !remainder.is_empty() {
                    events.push(http_partial_event(
                        event,
                        connection,
                        "HTTP/2",
                        direction,
                        completion_reason,
                        remainder,
                        self.include_raw_data,
                    ));
                }
            }
            let stream_ids = state
                .streams
                .keys()
                .copied()
                .chain(
                    state
                        .pending_headers
                        .keys()
                        .map(|(_, stream_id)| *stream_id),
                )
                .collect::<BTreeSet<_>>();
            for stream_id in stream_ids {
                events.push(http2_terminal_event(
                    event,
                    connection,
                    stream_id,
                    completion_reason,
                ));
            }
        }
        self.websocket.connections.remove(&connection.id);
        events
    }

    /// Handle SSL events (HTTP request/response data)
    fn handle_ssl_event(&mut self, mut event: Event) -> Vec<Event> {
        let mut terminal_events = Vec::new();
        let loss_count = event
            .data
            .get("ringbuf_reserve_failures")
            .and_then(serde_json::Value::as_u64);
        let loss_changed = loss_count.is_some_and(|now| {
            self.last_loss_count
                .map_or(now > 0, |previous| now != previous)
        });
        if let Some(count) = loss_count {
            self.last_loss_count = Some(count);
        }
        if loss_changed {
            // This counter is tracer-wide: it cannot identify which connection
            // lost bytes. Stop matching all active connections until a new
            // connection lifetime is observed, rather than guessing FIFO/HPACK.
            for connection in self.registry.active_identities() {
                terminal_events.extend(self.terminate_connection_state(
                    &event,
                    &connection,
                    "capture_loss",
                ));
                self.quarantined.insert(connection.id);
            }
        }
        if event.data["function"] == "CAPTURE_LOSS" {
            terminal_events.push(event);
            return terminal_events;
        }
        if event
            .data
            .get("connection_closed")
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            let closed = self.registry.close(&event);
            if let Some(connection) = closed {
                terminal_events.extend(self.terminate_connection_state(
                    &event,
                    &connection,
                    "closed",
                ));
                event.data["connection_id"] = serde_json::json!(connection.id);
                event.data["connection_generation"] = serde_json::json!(connection.generation);
                event.data["completion_reason"] = serde_json::json!("closed");
                terminal_events.push(event);
                return terminal_events;
            }
            terminal_events.push(event);
            return terminal_events;
        }

        let connection = self.registry.resolve(&event);
        terminal_events.extend(
            self.registry
                .take_retired()
                .into_iter()
                .flat_map(|(retired, reason)| {
                    self.terminate_connection_state(&event, &retired, reason)
                })
                .collect::<Vec<_>>(),
        );
        if connection.exact
            && (event.data["truncated"] == true
                || event
                    .data
                    .get("bytes_lost")
                    .and_then(serde_json::Value::as_u64)
                    .is_some_and(|n| n > 0))
        {
            terminal_events.extend(self.terminate_connection_state(
                &event,
                &connection,
                "capture_loss",
            ));
            self.quarantined.insert(connection.id.clone());
        }
        if self.quarantined.contains(&connection.id) {
            terminal_events.push(event);
            return terminal_events;
        }
        let ssl_data = &event.data;

        let data_str = match ssl_data.get("data").and_then(|v| v.as_str()) {
            Some(s) => s,
            None => {
                terminal_events.push(event);
                return terminal_events;
            }
        };

        // Raw events recorded before correlation v2 have no transport handle.
        // Preserve the original one-buffer parsing behavior for those traces.
        if !connection.exact
            && Self::is_http_data(data_str)
            && let Some(parsed_message) = Self::parse_http_message(data_str)
        {
            let tid = ssl_data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
            self.websocket
                .observe_handshake(&connection.id, &event, &parsed_message);
            terminal_events.push(Self::create_http_event(
                tid,
                parsed_message,
                &event,
                self.include_raw_data,
                &connection,
                None,
                None,
            ));
            return terminal_events;
        }

        let data_bytes = ssl_data
            .get("data_hex")
            .and_then(|v| v.as_str())
            .and_then(|v| hex::decode(v).ok())
            .unwrap_or_else(|| ssl_json_string_to_bytes(data_str));
        if let Some(events) =
            self.websocket
                .handle_event(&connection.id, &event, &data_bytes, self.include_raw_data)
        {
            terminal_events.extend(events);
            return terminal_events;
        }

        let h2_active = self.http2.contains_key(&connection.id);
        if h2_active || looks_like_http2_bytes(&data_bytes) {
            let state = self.http2.entry(connection.id.clone()).or_default();
            if let Some(events) =
                state.handle_event(&connection, &event, &data_bytes, self.include_raw_data)
            {
                let unreliable = events
                    .iter()
                    .find_map(|output| {
                        output
                            .data
                            .get("completion_reason")
                            .and_then(serde_json::Value::as_str)
                            .filter(|reason| {
                                matches!(*reason, "protocol_error" | "truncated" | "evicted")
                            })
                    })
                    .map(str::to_string);
                terminal_events.extend(events);
                if let Some(reason) = unreliable {
                    terminal_events.extend(self.terminate_connection_state(
                        &event,
                        &connection,
                        &reason,
                    ));
                    if connection.exact {
                        self.quarantined.insert(connection.id.clone());
                    }
                }
                if !connection.exact && self.http2.len() > MAX_HTTP2_CONNECTIONS {
                    terminal_events.extend(self.terminate_connection_state(
                        &event,
                        &connection,
                        "evicted",
                    ));
                }
                return terminal_events;
            }
            if h2_active {
                terminal_events.extend(self.terminate_connection_state(
                    &event,
                    &connection,
                    "protocol_error",
                ));
                if connection.exact {
                    self.quarantined.insert(connection.id);
                }
                terminal_events.push(event);
                return terminal_events;
            }
        }

        let h1_active = self.http1.contains_key(&connection.id);
        if h1_active || looks_like_http1_fragment(&data_bytes) {
            let state = self.http1.entry(connection.id.clone()).or_default();
            if let Some(mut events) = state.handle_event(
                &connection,
                &event,
                &data_bytes,
                self.include_raw_data,
                &mut self.websocket,
            ) {
                if events
                    .iter()
                    .any(|output| output.data["completion_reason"] == "truncated")
                    || state.pending.len() > MAX_HTTP1_PENDING_REQUESTS
                {
                    events.extend(self.terminate_connection_state(
                        &event,
                        &connection,
                        "truncated",
                    ));
                    if connection.exact {
                        self.quarantined.insert(connection.id.clone());
                    }
                }
                if !connection.exact && self.http1.len() > MAX_HTTP1_CONNECTIONS {
                    events.extend(self.terminate_connection_state(&event, &connection, "evicted"));
                }
                terminal_events.extend(events);
                return terminal_events;
            }
        }

        // If not parseable as HTTP, pass through original event
        terminal_events.push(event);
        terminal_events
    }
}

impl HTTP1ConnectionState {
    fn handle_event(
        &mut self,
        connection: &ConnectionIdentity,
        event: &Event,
        bytes: &[u8],
        include_raw_data: bool,
        websocket: &mut WebSocketState,
    ) -> Option<Vec<Event>> {
        let direction = direction_from_function(
            event
                .data
                .get("function")
                .and_then(|value| value.as_str())
                .unwrap_or(""),
        )?;
        let current_len = match direction {
            HTTP2Direction::Request => self.request_buffer.len(),
            HTTP2Direction::Response => self.response_buffer.len(),
        };
        let fragments = match direction {
            HTTP2Direction::Request => self.request_metadata.fragments.len(),
            HTTP2Direction::Response => self.response_metadata.fragments.len(),
        };
        if current_len.saturating_add(bytes.len()) > MAX_HTTP1_BUFFER_BYTES
            || fragments >= MAX_BUFFERED_FRAGMENTS
        {
            match direction {
                HTTP2Direction::Request => self.request_buffer.clear(),
                HTTP2Direction::Response => self.response_buffer.clear(),
            }
            return Some(vec![correlation_diagnostic_event(
                event,
                connection,
                "truncated",
                "http1_buffer_limit",
            )]);
        }
        match direction {
            HTTP2Direction::Request => self.request_buffer.extend_from_slice(bytes),
            HTTP2Direction::Response => self.response_buffer.extend_from_slice(bytes),
        }

        let tid = event
            .data
            .get("tid")
            .and_then(|value| value.as_u64())
            .unwrap_or(0);
        let mut events = Vec::new();

        let (buffer, metadata) = match direction {
            HTTP2Direction::Request => (&mut self.request_buffer, &mut self.request_metadata),
            HTTP2Direction::Response => (&mut self.response_buffer, &mut self.response_metadata),
        };
        metadata.push(bytes.len(), event);
        while let Some((message, consumed)) = parse_next_http1_message(
            buffer,
            direction,
            self.pending.front().is_some_and(|(_, head)| *head),
            false,
        ) {
            buffer.drain(..consumed);
            let mut capture = MessageMetadata::default();
            metadata.consume(consumed, &mut capture);
            let mut message_event = event.clone();
            message_event.data.as_object_mut().unwrap().extend(
                serde_json::to_value(capture.capture.finish())
                    .unwrap()
                    .as_object()
                    .unwrap()
                    .clone(),
            );

            let (exchange_id, method) = match message.message_type {
                HTTPMessageType::Request => {
                    self.next_request_seq = self.next_request_seq.saturating_add(1);
                    let exchange_id =
                        format!("http-{}-h1-{}", connection.id, self.next_request_seq);
                    self.pending.push_back((
                        exchange_id.clone(),
                        message.method.as_deref() == Some("HEAD"),
                    ));
                    websocket.observe_handshake(&connection.id, &message_event, &message);
                    (
                        Some(exchange_id),
                        Some(if connection.exact {
                            "h1_connection_fifo"
                        } else {
                            "legacy_pid_tid_single"
                        }),
                    )
                }
                HTTPMessageType::Response => {
                    let provisional = message
                        .status_code
                        .is_some_and(|code| code < 200 && code != 101);
                    let exchange_id = if provisional {
                        self.pending.front().map(|(id, _)| id.clone())
                    } else {
                        self.pending.pop_front().map(|(id, _)| id)
                    };
                    let method = exchange_id.as_ref().map(|_| {
                        if connection.exact {
                            "h1_connection_fifo"
                        } else {
                            "legacy_pid_tid_single"
                        }
                    });
                    (exchange_id, method)
                }
            };

            events.push(HTTPParser::create_http_event(
                tid,
                message,
                &message_event,
                include_raw_data,
                connection,
                exchange_id,
                method,
            ));
        }

        Some(events)
    }
}

fn parse_next_http1_message(
    buffer: &[u8],
    direction: HTTP2Direction,
    head_request: bool,
    closed: bool,
) -> Option<(HTTPMessage, usize)> {
    let header_end = find_bytes(buffer, b"\r\n\r\n")? + 4;
    let header_text = String::from_utf8_lossy(&buffer[..header_end]);
    let first_line = header_text.split("\r\n").next()?;
    let expected_direction = if first_line.starts_with("HTTP/") {
        HTTP2Direction::Response
    } else {
        HTTP2Direction::Request
    };
    if expected_direction != direction {
        return None;
    }

    let headers = parse_header_map(&header_text);
    let status_code = first_line
        .strip_prefix("HTTP/")
        .and_then(|_| first_line.split_whitespace().nth(1))
        .and_then(|value| value.parse::<u16>().ok());
    let no_body = direction == HTTP2Direction::Response
        && (head_request
            || status_code.is_some_and(|code| code < 200 || code == 204 || code == 304));
    let chunked = headers
        .get("transfer-encoding")
        .is_some_and(|value| value.to_ascii_lowercase().contains("chunked"));
    let consumed = if no_body {
        header_end
    } else if chunked {
        header_end + complete_chunked_len(&buffer[header_end..])?
    } else if let Some(content_length) = headers
        .get("content-length")
        .and_then(|value| value.parse::<usize>().ok())
    {
        let consumed = header_end.checked_add(content_length)?;
        (buffer.len() >= consumed).then_some(consumed)?
    } else if direction == HTTP2Direction::Request {
        header_end
    } else if closed {
        buffer.len()
    } else {
        return None;
    };

    let text = String::from_utf8_lossy(&buffer[..consumed]).to_string();
    HTTPParser::parse_http_message(&text).map(|mut message| {
        let body = if chunked {
            decode_chunked_body(&buffer[header_end..consumed]).unwrap_or_default()
        } else {
            buffer[header_end..consumed].to_vec()
        };
        message.body = body_string(&body);
        message.body_bytes = (!body.is_empty()).then_some(body);
        if chunked {
            // The HTTP parser has already removed transfer framing. Downstream
            // decompressors/SSE parsers must not dechunk the body a second time.
            message.headers.remove("transfer-encoding");
            message.headers.remove("content-length");
        }
        (message, consumed)
    })
}

fn parse_header_map(header_text: &str) -> HashMap<String, String> {
    header_text
        .split("\r\n")
        .skip(1)
        .filter_map(|line| {
            let (name, value) = line.split_once(':')?;
            Some((name.trim().to_ascii_lowercase(), value.trim().to_string()))
        })
        .collect()
}

fn complete_chunked_len(bytes: &[u8]) -> Option<usize> {
    let mut offset = 0usize;
    loop {
        let line_end = find_bytes(&bytes[offset..], b"\r\n")? + offset;
        let size_text = std::str::from_utf8(&bytes[offset..line_end]).ok()?;
        let size = usize::from_str_radix(size_text.split(';').next()?.trim(), 16).ok()?;
        offset = line_end + 2;
        if size == 0 {
            if bytes
                .get(offset..offset + 2)
                .is_some_and(|value| value == b"\r\n")
            {
                return Some(offset + 2);
            }
            let trailer_end = find_bytes(&bytes[offset..], b"\r\n\r\n")? + offset + 4;
            return Some(trailer_end);
        }
        let data_end = offset.checked_add(size)?;
        if bytes.get(data_end..data_end.checked_add(2)?)? != b"\r\n" {
            return None;
        }
        offset = data_end + 2;
    }
}

fn decode_chunked_body(bytes: &[u8]) -> Option<Vec<u8>> {
    let mut decoded = Vec::new();
    let mut offset = 0usize;
    loop {
        let line_end = find_bytes(&bytes[offset..], b"\r\n")? + offset;
        let size_text = std::str::from_utf8(&bytes[offset..line_end]).ok()?;
        let size = usize::from_str_radix(size_text.split(';').next()?.trim(), 16).ok()?;
        offset = line_end + 2;
        if size == 0 {
            return Some(decoded);
        }
        let data_end = offset.checked_add(size)?;
        decoded.extend_from_slice(bytes.get(offset..data_end)?);
        if bytes.get(data_end..data_end.checked_add(2)?)? != b"\r\n" {
            return None;
        }
        offset = data_end + 2;
    }
}

fn find_bytes(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
}

fn looks_like_http1_fragment(bytes: &[u8]) -> bool {
    bytes.first().is_some_and(|byte| byte.is_ascii_alphabetic())
        && bytes.iter().take(32).all(|byte| {
            byte.is_ascii() && (!byte.is_ascii_control() || matches!(byte, b'\r' | b'\n' | b'\t'))
        })
}

fn looks_like_http2_bytes(bytes: &[u8]) -> bool {
    const PREFACE: &[u8] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";
    bytes.starts_with(PREFACE)
        || (!bytes.is_empty() && bytes.len() < PREFACE.len() && PREFACE.starts_with(bytes))
        || (bytes.len() >= 9
            && bytes[3] <= 0x9
            && (((bytes[0] as usize) << 16) | ((bytes[1] as usize) << 8) | bytes[2] as usize)
                <= bytes.len().saturating_sub(9))
}

fn correlation_diagnostic_event(
    original_event: &Event,
    connection: &ConnectionIdentity,
    completion_reason: &str,
    reason: &str,
) -> Event {
    Event::new_with_timestamp(
        original_event.timestamp,
        "http_correlation".to_string(),
        connection.pid,
        connection.comm.clone(),
        serde_json::json!({
            "connection_id": connection.id,
            "connection_generation": connection.generation,
            "correlation_status": "unlinked",
            "correlation_version": if connection.exact { 2 } else { 1 },
            "completion_reason": completion_reason,
            "reason": reason,
        }),
    )
}

fn http_partial_event(
    original_event: &Event,
    connection: &ConnectionIdentity,
    protocol: &str,
    direction: &str,
    termination_reason: &str,
    buffered: &[u8],
    include_raw_data: bool,
) -> Event {
    Event::new_with_timestamp(
        original_event.timestamp,
        "http_correlation".to_string(),
        connection.pid,
        connection.comm.clone(),
        serde_json::json!({
            "connection_id": connection.id,
            "connection_generation": connection.generation,
            "protocol": protocol,
            "direction": direction,
            "correlation_status": "unlinked",
            "correlation_version": if connection.exact { 2 } else { 1 },
            "completion_reason": "partial",
            "termination_reason": termination_reason,
            "buffered_bytes": buffered.len(),
            "raw_data": include_raw_data.then(|| String::from_utf8_lossy(buffered).to_string()),
            "raw_data_hex": include_raw_data.then(|| hex::encode(buffered)),
        }),
    )
}

fn http1_terminal_event(
    original_event: &Event,
    connection: &ConnectionIdentity,
    exchange_id: &str,
    completion_reason: &str,
) -> Event {
    Event::new_with_timestamp(
        original_event.timestamp,
        "http_correlation".to_string(),
        connection.pid,
        connection.comm.clone(),
        serde_json::json!({
            "connection_id": connection.id,
            "connection_generation": connection.generation,
            "http_exchange_id": exchange_id,
            "correlation_method": if connection.exact { "h1_connection_fifo" } else { "legacy_pid_tid_single" },
            "correlation_status": "unlinked",
            "confidence": if connection.exact { 0.98 } else { 0.75 },
            "correlation_version": if connection.exact { 2 } else { 1 },
            "completion_reason": completion_reason,
        }),
    )
}

impl WebSocketState {
    fn observe_handshake(&mut self, connection_id: &str, event: &Event, message: &HTTPMessage) {
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
            connection_id.to_string(),
            WebSocketConnection {
                path: path.clone(),
                headers: message.headers.clone(),
                inflater: Decompress::new(false),
                handshake_capture_metadata: {
                    let mut metadata = CaptureMetadataAccumulator::default();
                    metadata.observe_event(event);
                    metadata
                },
            },
        );
    }

    fn handle_event(
        &mut self,
        connection_id: &str,
        event: &Event,
        bytes: &[u8],
        include_raw_data: bool,
    ) -> Option<Vec<Event>> {
        let connection = self.connections.get_mut(connection_id)?;
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
            connection_id,
            &connection.path,
            &connection.headers,
            &connection.handshake_capture_metadata,
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
    connection_id: &str,
    path: &str,
    headers: &HashMap<String, String>,
    handshake_capture_metadata: &CaptureMetadataAccumulator,
    body: String,
    include_raw_data: bool,
) -> Event {
    let tid = original_event
        .data
        .get("tid")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);
    let mut capture_metadata = handshake_capture_metadata.clone();
    capture_metadata.observe_event(original_event);
    HTTPEvent {
        capture_metadata: capture_metadata.finish(),
        tid,
        connection_id: Some(connection_id.to_string()),
        connection_generation: None,
        stream_id: None,
        http_exchange_id: None,
        correlation_method: None,
        correlation_status: None,
        confidence: None,
        correlation_version: 1,
        completion_reason: Some("done".to_string()),
        end_stream: true,
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
        connection: &ConnectionIdentity,
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
        let remainder_len = match direction {
            HTTP2Direction::Request => self.request_remainder.len(),
            HTTP2Direction::Response => self.response_remainder.len(),
        };
        let fragments = match direction {
            HTTP2Direction::Request => self.request_metadata.fragments.len(),
            HTTP2Direction::Response => self.response_metadata.fragments.len(),
        };
        if remainder_len.saturating_add(bytes.len()) > MAX_HTTP2_FRAME_BUFFER_BYTES
            || fragments >= MAX_BUFFERED_FRAGMENTS
        {
            match direction {
                HTTP2Direction::Request => self.request_remainder.clear(),
                HTTP2Direction::Response => self.response_remainder.clear(),
            }
            return Some(vec![correlation_diagnostic_event(
                original_event,
                connection,
                "truncated",
                "http2_frame_buffer_limit",
            )]);
        }
        let mut buffered = match direction {
            HTTP2Direction::Request => std::mem::take(&mut self.request_remainder),
            HTTP2Direction::Response => std::mem::take(&mut self.response_remainder),
        };
        buffered.extend_from_slice(bytes);
        let (frames, consumed) = parse_http2_frame_prefix(&buffered)?;
        let remainder = buffered[consumed..].to_vec();
        match direction {
            HTTP2Direction::Request => self.request_remainder = remainder,
            HTTP2Direction::Response => self.response_remainder = remainder,
        }
        let mut events = Vec::new();

        let metadata = match direction {
            HTTP2Direction::Request => &mut self.request_metadata,
            HTTP2Direction::Response => &mut self.response_metadata,
        };
        metadata.push(bytes.len(), original_event);
        let prefix_len = consumed
            - frames
                .iter()
                .map(|frame| 9 + frame.payload.len())
                .sum::<usize>();
        metadata.consume(prefix_len, &mut MessageMetadata::default());

        for frame in frames {
            let key = frame.stream_id;
            if self
                .pending_headers
                .keys()
                .any(|(pending_direction, stream_id)| {
                    *pending_direction == direction
                        && (frame.frame_type != 0x9 || frame.stream_id != *stream_id)
                })
            {
                events.push(correlation_diagnostic_event(
                    original_event,
                    connection,
                    "protocol_error",
                    "missing_continuation",
                ));
                break;
            }
            if frame.stream_id != 0
                && self
                    .goaway_last_stream_id
                    .is_some_and(|last_stream_id| frame.stream_id > last_stream_id)
            {
                events.push(http2_terminal_event(
                    original_event,
                    connection,
                    frame.stream_id,
                    "protocol_error",
                ));
                continue;
            }

            let metadata = match direction {
                HTTP2Direction::Request => &mut self.request_metadata,
                HTTP2Direction::Response => &mut self.response_metadata,
            };
            if frame.stream_id != 0 && matches!(frame.frame_type, 0x0 | 0x1 | 0x9) {
                let state = self.streams.entry(frame.stream_id).or_default();
                let target = match direction {
                    HTTP2Direction::Request => &mut state.request_capture_metadata,
                    HTTP2Direction::Response => &mut state.response_capture_metadata,
                };
                metadata.consume(9 + frame.payload.len(), target);
            } else {
                metadata.consume(9 + frame.payload.len(), &mut MessageMetadata::default());
            }
            match frame.frame_type {
                0x0 => {
                    if frame.stream_id == 0 {
                        continue;
                    }
                    let has_headers = self.streams.get(&key).is_some_and(|state| match direction {
                        HTTP2Direction::Request => !state.request_headers.is_empty(),
                        HTTP2Direction::Response => !state.response_headers.is_empty(),
                    });
                    if !has_headers {
                        self.streams.remove(&key);
                        self.pending_headers
                            .retain(|(_, stream_id), _| *stream_id != key);
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            frame.stream_id,
                            "protocol_error",
                        ));
                        continue;
                    }
                    let payload = data_payload(frame.flags, &frame.payload);
                    let state = self.streams.entry(key).or_default();
                    match direction {
                        HTTP2Direction::Request => {
                            if state.request_body.len().saturating_add(payload.len())
                                > MAX_HTTP_BODY_BYTES
                            {
                                events.push(http2_terminal_event(
                                    original_event,
                                    connection,
                                    frame.stream_id,
                                    "truncated",
                                ));
                                self.streams.remove(&key);
                                self.pending_headers
                                    .retain(|(_, stream_id), _| *stream_id != key);
                                continue;
                            }
                            state.request_body.extend_from_slice(payload);
                            if frame.flags & 0x1 != 0 && !state.request_emitted {
                                events.push(create_http2_request_event(
                                    connection,
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
                            if state.response_body.len().saturating_add(payload.len())
                                > MAX_HTTP_BODY_BYTES
                            {
                                events.push(http2_terminal_event(
                                    original_event,
                                    connection,
                                    frame.stream_id,
                                    "truncated",
                                ));
                                self.streams.remove(&key);
                                self.pending_headers
                                    .retain(|(_, stream_id), _| *stream_id != key);
                                continue;
                            }
                            state.response_body.extend_from_slice(payload);
                            if frame.flags & 0x1 != 0 && !state.response_emitted {
                                events.push(create_http2_response_event(
                                    connection,
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
                    let fragment = headers_payload(frame.flags, &frame.payload);
                    if fragment.len() > MAX_HTTP2_HEADER_BLOCK_BYTES {
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            frame.stream_id,
                            "truncated",
                        ));
                        break;
                    }
                    if frame.flags & 0x4 != 0 {
                        if let Some(headers) = self.decode_headers(direction, fragment) {
                            let state = self.streams.entry(key).or_default();
                            apply_headers(state, direction, headers);
                            if frame.flags & 0x1 != 0 {
                                match direction {
                                    HTTP2Direction::Request if !state.request_emitted => {
                                        events.push(create_http2_request_event(
                                            connection,
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
                                            connection,
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
                        } else {
                            self.streams.remove(&key);
                            events.push(http2_terminal_event(
                                original_event,
                                connection,
                                frame.stream_id,
                                "protocol_error",
                            ));
                        }
                    } else if fragment.len() <= MAX_HTTP2_HEADER_BLOCK_BYTES {
                        self.pending_headers.insert(
                            (direction, key),
                            PendingHTTP2Headers {
                                direction,
                                block: fragment.to_vec(),
                                end_stream: frame.flags & 0x1 != 0,
                            },
                        );
                        while self.pending_headers.len() > MAX_HTTP2_PENDING_HEADERS {
                            let Some((pending_direction, stream_id)) =
                                self.pending_headers.keys().next().copied()
                            else {
                                break;
                            };
                            self.pending_headers.remove(&(pending_direction, stream_id));
                            self.streams.remove(&stream_id);
                            events.push(http2_terminal_event(
                                original_event,
                                connection,
                                stream_id,
                                "evicted",
                            ));
                        }
                    } else {
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            frame.stream_id,
                            "truncated",
                        ));
                    }
                }
                0x9 => {
                    if frame.stream_id == 0 {
                        continue;
                    }
                    let Some(mut pending) = self.pending_headers.remove(&(direction, key)) else {
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            frame.stream_id,
                            "protocol_error",
                        ));
                        continue;
                    };
                    pending.block.extend_from_slice(&frame.payload);
                    if pending.block.len() > MAX_HTTP2_HEADER_BLOCK_BYTES {
                        self.streams.remove(&key);
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            frame.stream_id,
                            "truncated",
                        ));
                        continue;
                    }
                    if frame.flags & 0x4 != 0 {
                        if let Some(headers) =
                            self.decode_headers(pending.direction, &pending.block)
                        {
                            let state = self.streams.entry(key).or_default();
                            apply_headers(state, pending.direction, headers);
                            if pending.end_stream {
                                match pending.direction {
                                    HTTP2Direction::Request if !state.request_emitted => {
                                        events.push(create_http2_request_event(
                                            connection,
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
                                            connection,
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
                        } else {
                            self.streams.remove(&key);
                            events.push(http2_terminal_event(
                                original_event,
                                connection,
                                frame.stream_id,
                                "protocol_error",
                            ));
                        }
                    } else {
                        self.pending_headers.insert((direction, key), pending);
                    }
                }
                0x3 => {
                    self.streams.remove(&key);
                    self.pending_headers
                        .retain(|(_, stream_id), _| *stream_id != key);
                    events.push(http2_terminal_event(
                        original_event,
                        connection,
                        frame.stream_id,
                        "reset",
                    ));
                }
                0x7 => {
                    // Client GOAWAY refers to server-initiated streams, not the
                    // client requests tracked here.
                    if direction != HTTP2Direction::Response {
                        continue;
                    }
                    let last_stream_id = frame
                        .payload
                        .get(..4)
                        .and_then(|bytes| <[u8; 4]>::try_from(bytes).ok())
                        .map(u32::from_be_bytes)
                        .map(|stream_id| stream_id & 0x7fff_ffff)
                        .unwrap_or(0);
                    self.goaway_last_stream_id = Some(
                        self.goaway_last_stream_id
                            .map(|current| current.min(last_stream_id))
                            .unwrap_or(last_stream_id),
                    );
                    for stream_id in self
                        .streams
                        .keys()
                        .copied()
                        .filter(|stream_id| *stream_id > last_stream_id)
                        .collect::<Vec<_>>()
                    {
                        events.push(http2_terminal_event(
                            original_event,
                            connection,
                            stream_id,
                            "goaway",
                        ));
                        self.streams.remove(&stream_id);
                        self.pending_headers
                            .retain(|(_, pending_stream_id), _| *pending_stream_id != stream_id);
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
                self.pending_headers
                    .retain(|(_, stream_id), _| *stream_id != key);
            }
            while self.streams.len() > MAX_HTTP2_STREAMS {
                let Some(stream_id) = self.streams.keys().next().copied() else {
                    break;
                };
                self.streams.remove(&stream_id);
                self.pending_headers
                    .retain(|(_, pending_stream_id), _| *pending_stream_id != stream_id);
                events.push(http2_terminal_event(
                    original_event,
                    connection,
                    stream_id,
                    "evicted",
                ));
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
        let (decoder, valid) = match direction {
            HTTP2Direction::Request => (&mut self.request_decoder, &mut self.request_hpack_valid),
            HTTP2Direction::Response => {
                (&mut self.response_decoder, &mut self.response_hpack_valid)
            }
        };
        if !*valid {
            return None;
        }
        let decoded = match decoder.decode(block) {
            Ok(decoded) => decoded,
            Err(_) => {
                *valid = false;
                return None;
            }
        };
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

fn parse_http2_frame_prefix(mut bytes: &[u8]) -> Option<(Vec<HTTP2Frame>, usize)> {
    const PREFACE: &[u8] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";
    let original_len = bytes.len();
    let mut prefix_len = 0usize;
    if bytes.starts_with(PREFACE) {
        bytes = &bytes[PREFACE.len()..];
        prefix_len = PREFACE.len();
    } else if !bytes.is_empty() && bytes.len() < PREFACE.len() && PREFACE.starts_with(bytes) {
        return Some((Vec::new(), 0));
    }
    if bytes.len() < 9 {
        return Some((Vec::new(), prefix_len));
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
            offset -= 9;
            break;
        }
        let payload = bytes[offset..offset + length].to_vec();
        offset += length;
        frames.push(HTTP2Frame {
            frame_type,
            flags,
            stream_id,
            payload,
        });
    }

    let consumed = prefix_len + offset;
    debug_assert!(consumed <= original_len);
    Some((frames, consumed))
}

#[cfg(test)]
fn parse_http2_frames(bytes: &[u8]) -> Option<Vec<HTTP2Frame>> {
    let (frames, consumed) = parse_http2_frame_prefix(bytes)?;
    (consumed == bytes.len() && !frames.is_empty()).then_some(frames)
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

fn create_http2_request_event(
    connection: &ConnectionIdentity,
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
        capture_metadata: state.request_capture_metadata.capture.finish(),
        tid,
        connection_id: Some(connection.id.clone()),
        connection_generation: Some(connection.generation),
        stream_id: Some(stream_id),
        http_exchange_id: Some(format!("http-{}-h2-{stream_id}", connection.id)),
        correlation_method: Some(if connection.exact {
            "h2_stream".to_string()
        } else {
            "legacy_pid_tid_single".to_string()
        }),
        correlation_status: Some(if connection.exact {
            "exact".to_string()
        } else {
            "inferred".to_string()
        }),
        confidence: Some(if connection.exact { 1.0 } else { 0.75 }),
        correlation_version: if connection.exact { 2 } else { 1 },
        completion_reason: Some("done".to_string()),
        end_stream: true,
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
    connection: &ConnectionIdentity,
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
        capture_metadata: state.response_capture_metadata.capture.finish(),
        tid,
        connection_id: Some(connection.id.clone()),
        connection_generation: Some(connection.generation),
        stream_id: Some(stream_id),
        http_exchange_id: Some(format!("http-{}-h2-{stream_id}", connection.id)),
        correlation_method: Some(if connection.exact {
            "h2_stream".to_string()
        } else {
            "legacy_pid_tid_single".to_string()
        }),
        correlation_status: Some(if connection.exact {
            "exact".to_string()
        } else {
            "inferred".to_string()
        }),
        confidence: Some(if connection.exact { 1.0 } else { 0.75 }),
        correlation_version: if connection.exact { 2 } else { 1 },
        completion_reason: Some("done".to_string()),
        end_stream: true,
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

fn http2_terminal_event(
    original_event: &Event,
    connection: &ConnectionIdentity,
    stream_id: u32,
    completion_reason: &str,
) -> Event {
    Event::new_with_timestamp(
        original_event.timestamp,
        "http_correlation".to_string(),
        connection.pid,
        connection.comm.clone(),
        serde_json::json!({
            "connection_id": connection.id,
            "connection_generation": connection.generation,
            "stream_id": stream_id,
            "http_exchange_id": format!("http-{}-h2-{stream_id}", connection.id),
            "correlation_method": if connection.exact { "h2_stream" } else { "legacy_pid_tid_single" },
            "correlation_status": "unlinked",
            "confidence": if connection.exact { 1.0 } else { 0.75 },
            "correlation_version": if connection.exact { 2 } else { 1 },
            "completion_reason": completion_reason,
        }),
    )
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
        let mut parser = HTTPParser {
            include_raw_data: self.include_raw_data,
            registry: std::mem::take(&mut self.registry),
            http1: std::mem::take(&mut self.http1),
            http2: std::mem::take(&mut self.http2),
            websocket: std::mem::take(&mut self.websocket),
            quarantined: std::mem::take(&mut self.quarantined),
            last_loss_count: self.last_loss_count,
        };

        let processed_stream = async_stream::stream! {
            let mut input = stream;
            let mut last_event = None;
            while let Some(event) = input.next().await {
                if event.source == "ssl" {
                    last_event = Some(event.clone());
                    for output in parser.handle_ssl_event(event) {
                        yield output;
                    }
                } else {
                    yield event;
                }
            }
            if let Some(event) = last_event {
                // End of capture is not a TLS close: do not present buffered
                // close-delimited bodies as complete responses.
                for connection in parser.registry.active_identities() {
                    for output in parser.terminate_connection_state(&event, &connection, "capture_end") {
                        yield output;
                    }
                }
            }
        };

        Ok(Box::pin(processed_stream))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzers::{HTTPDecompressor, SSEProcessor};
    use crate::view::MaterializedView;
    use flate2::write::GzEncoder;
    use flate2::{Compress, Compression, FlushCompress};
    use futures::{StreamExt, stream};
    use hpack::Encoder as HpackEncoder;
    use serde_json::json;
    use std::io::Write;

    fn ssl_event(timestamp: u64, function: &str, bytes: Vec<u8>) -> Event {
        let len = bytes.len();
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
                "transport_handle": "0xabc",
                "process_start_ns": 12345,
                "tls_library": "openssl",
                "capture_seq": timestamp,
                "len": len,
                "buf_size": len,
                "truncated": false,
                "ringbuf_reserve_failures": 0,
            }),
        )
    }

    fn ssl_event_on(
        timestamp: u64,
        tid: u64,
        handle: &str,
        function: &str,
        bytes: Vec<u8>,
    ) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            4242,
            "node".to_string(),
            json!({
                "tid": tid,
                "transport_handle": handle,
                "process_start_ns": 12345,
                "tls_library": "openssl",
                "function": function,
                "data": bytes_to_ssl_json_string(&bytes),
                "data_hex": hex::encode(&bytes),
            }),
        )
    }

    fn ssl_close_on(timestamp: u64, tid: u64, handle: &str) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            4242,
            "node".to_string(),
            json!({
                "tid": tid,
                "transport_handle": handle,
                "process_start_ns": 12345,
                "tls_library": "openssl",
                "function": "CLOSE",
                "connection_closed": true,
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
    async fn http1_events_expose_capture_metadata_and_accept_legacy_input() {
        let request =
            b"POST /v1/messages HTTP/1.1\r\nHost: api.example.test\r\nContent-Length: 2\r\n\r\n{}"
                .to_vec();
        let legacy = Event::new_with_timestamp(
            2,
            "ssl".to_string(),
            4242,
            "node".to_string(),
            json!({
                "tid": 7,
                "function": "READ/RECV",
                "data": "HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n"
            }),
        );
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", request),
            legacy,
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 3);
        assert_eq!(output[2].data["completion_reason"], "capture_end");
        assert_eq!(output[0].data["capture_fragment_count"], 1);
        assert_eq!(output[0].data["transport_handle"], "0xabc");
        assert_eq!(output[0].data["capture_metadata_complete"], true);
        assert_eq!(output[1].data["capture_fragment_count"], 1);
        assert!(output[1].data["transport_handle"].is_null());
        assert!(output[1].data["capture_original_len"].is_null());
        assert_eq!(output[1].data["capture_metadata_complete"], false);
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

        assert_eq!(output.len(), 4);
        assert_eq!(output[3].data["completion_reason"], "capture_end");
        assert_eq!(output[2].data["path"], "/backend-api/codex/responses");
        assert!(output[2].data["body"].as_str().unwrap().contains(prompt));
        assert_eq!(output[2].data["capture_fragment_count"], 2);
        assert_eq!(output[2].data["capture_seq_start"], 1);
        assert_eq!(output[2].data["capture_seq_end"], 3);
        assert_eq!(output[2].data["transport_handle"], "0xabc");
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

        let response_headers_bytes = frame(0x1, 0x4, 1, &response_encoder.encode(response_headers));
        let response_body_bytes = frame(0x0, 0x1, 1, response_body);
        let expected_response_capture_len =
            response_headers_bytes.len() + response_body_bytes.len();

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event(1, "WRITE/SEND", request_bytes),
            ssl_event(2, "READ/RECV", response_headers_bytes),
            ssl_event(3, "READ/RECV", response_body_bytes),
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
        assert_eq!(output[0].data["capture_fragment_count"], 1);
        assert_eq!(output[1].data["capture_fragment_count"], 2);
        assert_eq!(output[1].data["capture_seq_start"], 2);
        assert_eq!(output[1].data["capture_seq_end"], 3);
        assert_eq!(
            output[1].data["capture_original_len"],
            expected_response_capture_len
        );
        assert_eq!(output[1].data["capture_identity_consistent"], true);
        assert_eq!(output[1].data["capture_metadata_complete"], true);

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
    async fn http1_fragments_follow_connection_across_threads_without_cross_talk() {
        let request_a = b"POST /v1/chat/completions HTTP/1.1\r\nHost: a.test\r\nContent-Length: 13\r\n\r\n{\"model\":\"a\"}";
        let request_b = b"POST /v1/messages HTTP/1.1\r\nHost: b.test\r\nContent-Length: 13\r\n\r\n{\"model\":\"b\"}";
        let response_a = b"HTTP/1.1 200 OK\r\nContent-Length: 19\r\n\r\n{\"id\":\"chatcmpl-a\"}";
        let response_b = b"HTTP/1.1 200 OK\r\nContent-Length: 14\r\n\r\n{\"id\":\"msg_b\"}";

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event_on(1, 7, "0xa", "WRITE/SEND", request_a[..17].to_vec()),
            ssl_event_on(2, 7, "0xb", "WRITE/SEND", request_b.to_vec()),
            ssl_event_on(3, 8, "0xa", "WRITE/SEND", request_a[17..].to_vec()),
            ssl_event_on(4, 91, "0xb", "READ/RECV", response_b.to_vec()),
            ssl_event_on(5, 92, "0xa", "READ/RECV", response_a[..11].to_vec()),
            ssl_event_on(6, 93, "0xa", "READ/RECV", response_a[11..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 4);
        let request_a = output
            .iter()
            .find(|event| event.data["path"] == "/v1/chat/completions")
            .unwrap();
        let request_b = output
            .iter()
            .find(|event| event.data["path"] == "/v1/messages")
            .unwrap();
        let response_a = output
            .iter()
            .find(|event| {
                event.data["body"]
                    .as_str()
                    .is_some_and(|body| body.contains("chatcmpl-a"))
            })
            .unwrap();
        let response_b = output
            .iter()
            .find(|event| {
                event.data["body"]
                    .as_str()
                    .is_some_and(|body| body.contains("msg_b"))
            })
            .unwrap();
        assert_eq!(
            request_a.data["http_exchange_id"],
            response_a.data["http_exchange_id"]
        );
        assert_eq!(
            request_b.data["http_exchange_id"],
            response_b.data["http_exchange_id"]
        );
        assert_ne!(
            request_a.data["connection_id"],
            request_b.data["connection_id"]
        );
        assert_eq!(response_a.data["tid"], 93);
        assert_eq!(request_a.data["capture_fragment_count"], 2);
        assert_eq!(request_a.data["capture_tids"], json!([7, 8]));
        assert_eq!(response_a.data["capture_fragment_count"], 2);
        assert_eq!(response_a.data["capture_tids"], json!([92, 93]));
        assert_eq!(response_a.data["correlation_method"], "h1_connection_fifo");
    }

    #[tokio::test]
    async fn http1_pipelined_messages_use_connection_fifo() {
        let request = |model: &str| {
            let body = format!("{{\"model\":\"{model}\"}}");
            format!(
                "POST /v1/chat/completions HTTP/1.1\r\nHost: api.example.test\r\nContent-Length: {}\r\n\r\n{body}",
                body.len()
            )
        };
        let response = |id: &str| {
            let body = format!("{{\"id\":\"{id}\"}}");
            format!(
                "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n{body}",
                body.len()
            )
        };
        let requests = format!("{}{}", request("one"), request("two")).into_bytes();
        let responses = format!("{}{}", response("first"), response("second")).into_bytes();
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event_on(1, 7, "0xfifo", "WRITE/SEND", requests),
            ssl_event_on(2, 8, "0xfifo", "READ/RECV", responses),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 4);
        assert_eq!(output[0].data["message_type"], "request");
        assert_eq!(output[1].data["message_type"], "request");
        assert_eq!(output[2].data["message_type"], "response");
        assert_eq!(output[3].data["message_type"], "response");
        assert_eq!(
            output[0].data["http_exchange_id"],
            output[2].data["http_exchange_id"]
        );
        assert_eq!(
            output[1].data["http_exchange_id"],
            output[3].data["http_exchange_id"]
        );
    }

    #[tokio::test]
    async fn http2_frame_remainders_and_streams_are_connection_scoped() {
        let mut request_encoder = HpackEncoder::new();
        let mut response_encoder = HpackEncoder::new();
        let mut request_bytes = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".to_vec();
        for stream_id in [1, 3] {
            request_bytes.extend(frame(
                0x1,
                0x4,
                stream_id,
                &request_encoder.encode([
                    (&b":method"[..], &b"POST"[..]),
                    (&b":authority"[..], &b"api.openai.com"[..]),
                    (&b":path"[..], &b"/v1/chat/completions"[..]),
                ]),
            ));
        }
        request_bytes.extend(frame(0x0, 0x1, 1, br#"{"model":"one"}"#));
        request_bytes.extend(frame(0x0, 0x1, 3, br#"{"model":"three"}"#));

        let mut response_bytes = Vec::new();
        for stream_id in [3, 1] {
            response_bytes.extend(frame(
                0x1,
                0x4,
                stream_id,
                &response_encoder.encode([
                    (&b":status"[..], &b"200"[..]),
                    (&b"content-type"[..], &b"application/json"[..]),
                ]),
            ));
            response_bytes.extend(frame(
                0x0,
                0x1,
                stream_id,
                format!("{{\"model\":\"stream-{stream_id}\"}}").as_bytes(),
            ));
        }

        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event_on(1, 7, "0xh2", "WRITE/SEND", request_bytes[..5].to_vec()),
            ssl_event_on(2, 8, "0xh2", "WRITE/SEND", request_bytes[5..37].to_vec()),
            ssl_event_on(3, 9, "0xh2", "WRITE/SEND", request_bytes[37..].to_vec()),
            ssl_event_on(4, 90, "0xh2", "READ/RECV", response_bytes[..7].to_vec()),
            ssl_event_on(5, 91, "0xh2", "READ/RECV", response_bytes[7..].to_vec()),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 4);
        for stream_id in [1, 3] {
            let events = output
                .iter()
                .filter(|event| event.data["stream_id"] == stream_id)
                .collect::<Vec<_>>();
            assert_eq!(events.len(), 2);
            assert_eq!(
                events[0].data["http_exchange_id"],
                events[1].data["http_exchange_id"]
            );
            assert_eq!(events[0].data["correlation_method"], "h2_stream");
            assert_eq!(events[0].data["confidence"], 1.0);
        }
    }

    #[tokio::test]
    async fn same_http2_stream_id_is_isolated_between_connections() {
        fn exchange(handle: &str, model: &str, response_id: &str) -> Vec<Event> {
            let mut request_encoder = HpackEncoder::new();
            let mut response_encoder = HpackEncoder::new();
            let mut request = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".to_vec();
            request.extend(frame(
                0x1,
                0x4,
                1,
                &request_encoder.encode([
                    (&b":method"[..], &b"POST"[..]),
                    (&b":authority"[..], &b"api.example.test"[..]),
                    (&b":path"[..], &b"/v1/chat/completions"[..]),
                ]),
            ));
            request.extend(frame(
                0x0,
                0x1,
                1,
                format!("{{\"model\":\"{model}\"}}").as_bytes(),
            ));
            let mut response = frame(
                0x1,
                0x4,
                1,
                &response_encoder.encode([
                    (&b":status"[..], &b"200"[..]),
                    (&b"content-type"[..], &b"application/json"[..]),
                ]),
            );
            response.extend(frame(
                0x0,
                0x1,
                1,
                format!("{{\"id\":\"{response_id}\"}}").as_bytes(),
            ));
            vec![
                ssl_event_on(1, 7, handle, "WRITE/SEND", request),
                ssl_event_on(2, 8, handle, "READ/RECV", response),
            ]
        }

        let mut input_events = exchange("0xh2-a", "model-a", "response-a");
        input_events.extend(exchange("0xh2-b", "model-b", "response-b"));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser
            .process(Box::pin(stream::iter(input_events)))
            .await
            .unwrap()
            .collect()
            .await;

        assert_eq!(output.len(), 4);
        let a = output
            .iter()
            .find(|event| {
                event.data["body"]
                    .as_str()
                    .is_some_and(|body| body.contains("model-a"))
            })
            .unwrap();
        let b = output
            .iter()
            .find(|event| {
                event.data["body"]
                    .as_str()
                    .is_some_and(|body| body.contains("model-b"))
            })
            .unwrap();
        assert_eq!(a.data["stream_id"], 1);
        assert_eq!(b.data["stream_id"], 1);
        assert_ne!(a.data["connection_id"], b.data["connection_id"]);
        assert_ne!(a.data["http_exchange_id"], b.data["http_exchange_id"]);
    }

    #[tokio::test]
    async fn connection_close_flushes_bound_sse_with_explicit_terminal_reason() {
        let request = b"POST /v1/chat/completions HTTP/1.1\r\nHost: api.example.test\r\nContent-Length: 2\r\n\r\n{}".to_vec();
        let response = b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata: {\"id\":\"chatcmpl-close\",\"choices\":[{\"index\":0,\"delta\":{\"content\":\"partial\"}}]}\n\n".to_vec();
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event_on(1, 7, "0xclose", "WRITE/SEND", request),
            ssl_event_on(2, 8, "0xclose", "READ/RECV", response),
            ssl_close_on(3, 9, "0xclose"),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let parsed = parser.process(input).await.unwrap();
        let mut sse = SSEProcessor::new();
        let output: Vec<Event> = sse.process(parsed).await.unwrap().collect().await;

        let request = output
            .iter()
            .find(|event| event.data["message_type"] == "request")
            .unwrap();
        let response = output
            .iter()
            .find(|event| event.source == "sse_processor")
            .unwrap();
        assert_eq!(response.data["text_content"], "partial");
        assert_eq!(response.data["completion_reason"], "closed");
        assert_eq!(
            request.data["http_exchange_id"],
            response.data["http_exchange_id"]
        );
    }

    #[tokio::test]
    async fn idle_connection_reuse_terminates_old_generation_before_new_request() {
        let request = |model: &str| {
            let body = format!("{{\"model\":\"{model}\"}}");
            format!(
                "POST /v1/chat/completions HTTP/1.1\r\nHost: api.example.test\r\nContent-Length: {}\r\n\r\n{body}",
                body.len()
            )
            .into_bytes()
        };
        let input: EventStream = Box::pin(stream::iter(vec![
            ssl_event_on(1, 7, "0xidle", "WRITE/SEND", request("old")),
            ssl_event_on(600_002, 8, "0xidle", "WRITE/SEND", request("new")),
        ]));
        let mut parser = HTTPParser::new().disable_raw_data();
        let output: Vec<Event> = parser.process(input).await.unwrap().collect().await;

        assert_eq!(output.len(), 4);
        assert_eq!(output[3].data["completion_reason"], "capture_end");
        assert_eq!(output[1].source, "http_correlation");
        assert_eq!(output[1].data["completion_reason"], "timeout");
        assert_eq!(
            output[0].data["http_exchange_id"],
            output[1].data["http_exchange_id"]
        );
        assert_ne!(
            output[0].data["connection_id"],
            output[2].data["connection_id"]
        );
        assert_eq!(output[2].data["connection_generation"], 1);
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

    #[test]
    fn http1_chunked_body_waits_for_trailers_and_decodes_payload() {
        let message = b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\nx-checksum: ok\r\n\r\n";
        assert!(
            parse_next_http1_message(
                &message[..message.len() - 2],
                HTTP2Direction::Response,
                false,
                false
            )
            .is_none()
        );

        let (parsed, consumed) =
            parse_next_http1_message(message, HTTP2Direction::Response, false, false).unwrap();
        assert_eq!(consumed, message.len());
        assert_eq!(parsed.body.as_deref(), Some("hello"));
    }

    #[tokio::test]
    async fn http1_informational_and_head_responses_do_not_shift_fifo() {
        let requests = b"HEAD /one HTTP/1.1\r\n\r\nGET /two HTTP/1.1\r\n\r\n";
        let responses = b"HTTP/1.1 100 Continue\r\n\r\nHTTP/1.1 200 OK\r\nContent-Length: 123\r\n\r\nHTTP/1.1 204 No Content\r\n\r\n";
        let mut parser = HTTPParser::new();
        let output: Vec<_> = parser
            .process(Box::pin(stream::iter(vec![
                ssl_event(1, "WRITE/SEND", requests.to_vec()),
                ssl_event(2, "READ/RECV", responses.to_vec()),
            ])))
            .await
            .unwrap()
            .collect()
            .await;
        assert_eq!(output.len(), 5);
        assert_eq!(output[2].data["message_type"], "informational_response");
        assert_eq!(output[2].data["end_stream"], false);
        assert_eq!(
            output[0].data["http_exchange_id"],
            output[3].data["http_exchange_id"]
        );
        assert_eq!(
            output[1].data["http_exchange_id"],
            output[4].data["http_exchange_id"]
        );
        assert_eq!(output[3].data["has_body"], false);
    }

    #[tokio::test]
    async fn http1_gzip_body_keeps_binary_bytes_across_tls_fragments() {
        let body = "{\"model\":\"模型\",\"usage\":{\"total_tokens\":5}}";
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(body.as_bytes()).unwrap();
        let compressed = encoder.finish().unwrap();
        let mut response = format!("HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nTransfer-Encoding: chunked\r\n\r\n{:x}\r\n", compressed.len()).into_bytes();
        response.extend(&compressed);
        response.extend(b"\r\n0\r\n\r\n");
        let split = response.len() - 8;
        let mut parser = HTTPParser::new();
        let input = parser
            .process(Box::pin(stream::iter(vec![
                ssl_event(1, "READ/RECV", response[..split].to_vec()),
                ssl_event(2, "READ/RECV", response[split..].to_vec()),
            ])))
            .await
            .unwrap();
        let output: Vec<_> = HTTPDecompressor::new()
            .process(input)
            .await
            .unwrap()
            .collect()
            .await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["body"], body);
        assert_eq!(output[0].data["capture_fragment_count"], 2);
        assert_eq!(output[0].data["capture_captured_len"], response.len());
    }

    #[tokio::test]
    async fn capture_loss_stops_pairing_and_terminal_counter_reaches_view() {
        for final_counter_only in [false, true] {
            let request = ssl_event(
                1,
                "WRITE/SEND",
                b"POST /v1/messages HTTP/1.1\r\nContent-Length: 2\r\n\r\n{}".to_vec(),
            );
            let mut loss = if final_counter_only {
                Event::new_with_timestamp(
                    2,
                    "ssl".into(),
                    9000,
                    "sslsniff".into(),
                    json!({"function":"CAPTURE_LOSS"}),
                )
            } else {
                ssl_event(
                    2,
                    "READ/RECV",
                    b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}".to_vec(),
                )
            };
            loss.data["ringbuf_reserve_failures"] = json!(1);
            let mut parser = HTTPParser::new();
            let output: Vec<_> = parser
                .process(Box::pin(stream::iter(vec![request, loss])))
                .await
                .unwrap()
                .collect()
                .await;
            assert!(
                !output
                    .iter()
                    .any(|event| event.data["message_type"] == "response")
            );
            let terminal = output
                .iter()
                .find(|event| event.source == "http_correlation")
                .unwrap();
            assert_eq!(terminal.pid, 4242);
            assert_eq!(terminal.data["completion_reason"], "capture_loss");
            let mut view = MaterializedView::new();
            for event in &output {
                view.ingest_event(event).unwrap();
            }
            let calls = view.llm_call_rows(10);
            assert_eq!(calls.len(), 1);
            assert_eq!(calls[0].completion_reason.as_deref(), Some("capture_loss"));
            assert_eq!(calls[0].correlation_status.as_deref(), Some("unlinked"));
        }
    }

    #[tokio::test]
    async fn truncated_connection_stays_unlinked_until_close_and_handle_reuse() {
        let request = b"GET / HTTP/1.1\r\n\r\n".to_vec();
        let response = b"HTTP/1.1 204 No Content\r\n\r\n".to_vec();
        let mut partial = ssl_event(2, "READ/RECV", b"HTTP/1.1".to_vec());
        partial.data["truncated"] = json!(true);
        let input = vec![
            ssl_event(1, "WRITE/SEND", request.clone()),
            partial,
            ssl_event(3, "READ/RECV", response.clone()),
            ssl_close_on(4, 7, "0xabc"),
            ssl_event(5, "WRITE/SEND", request),
            ssl_event(6, "READ/RECV", response),
        ];
        let output: Vec<_> = HTTPParser::new()
            .process(Box::pin(stream::iter(input)))
            .await
            .unwrap()
            .collect()
            .await;
        let parsed: Vec<_> = output
            .iter()
            .filter(|event| event.source == "http_parser")
            .collect();
        assert_eq!(parsed.len(), 3);
        assert_ne!(
            parsed[0].data["connection_id"],
            parsed[1].data["connection_id"]
        );
        assert_eq!(
            parsed[1].data["http_exchange_id"],
            parsed[2].data["http_exchange_id"]
        );
    }

    #[tokio::test]
    async fn http2_continuation_tracks_fragment_provenance_and_rst_terminates() {
        let block = HpackEncoder::new().encode([
            (&b":method"[..], &b"POST"[..]),
            (&b":path"[..], &b"/v1/messages"[..]),
        ]);
        let split = block.len() / 2;
        let mut start = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".to_vec();
        start.extend(frame(1, 1, 1, &block[..split]));
        let continuation = frame(9, 4, 1, &block[split..]);
        let output: Vec<_> = HTTPParser::new()
            .process(Box::pin(stream::iter(vec![
                ssl_event(1, "WRITE/SEND", start),
                ssl_event(2, "WRITE/SEND", continuation[..5].to_vec()),
                ssl_event(3, "WRITE/SEND", continuation[5..].to_vec()),
                ssl_event(4, "READ/RECV", frame(3, 0, 1, &0u32.to_be_bytes())),
            ])))
            .await
            .unwrap()
            .collect()
            .await;
        assert_eq!(output.len(), 2);
        assert_eq!(output[0].data["capture_fragment_count"], 3);
        assert_eq!(output[0].data["capture_seq_start"], 1);
        assert_eq!(output[0].data["capture_seq_end"], 3);
        assert_eq!(output[1].data["completion_reason"], "reset");
        assert_eq!(
            output[0].data["http_exchange_id"],
            output[1].data["http_exchange_id"]
        );
    }
}
