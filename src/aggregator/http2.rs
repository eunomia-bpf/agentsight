//! HTTP/2 Stream Aggregator - correlates HTTP/2 request/response frames by stream ID
//!
//! This module implements aggregation logic for HTTP/2 frames, grouping frames
//! by their stream_id and correlating request (client->server) with response (server->client)
//! to form complete HTTP/2 request/response pairs.

use std::collections::HashMap;
use std::num::NonZeroUsize;
use lru::LruCache;
use crate::config::DEFAULT_CONNECTION_CAPACITY;
use crate::parser::http2::ParsedHttp2Frame;
use crate::parser::sse::{SseParser, SSEParser};
use crate::aggregator::http::ConnectionId;
use crate::aggregator::result::AggregatedResult;
use crate::chrome_trace::{ChromeTraceEvent, ToChromeTraceEvent, ns_to_us};

/// Stream identifier within an HTTP/2 connection
#[derive(Debug, Clone, Copy, Hash, Eq, PartialEq)]
pub struct StreamId {
    pub connection_id: ConnectionId,
    pub stream_id: u32,
}

impl StreamId {
    /// Create a new StreamId from connection and stream
    pub fn new(connection_id: ConnectionId, stream_id: u32) -> Self {
        StreamId {
            connection_id,
            stream_id,
        }
    }
}

/// Direction of the frame (request or response)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StreamDirection {
    /// Client -> Server (request direction, rw=1 for SSL_write)
    Request,
    /// Server -> Client (response direction, rw=0 for SSL_read)
    Response,
}

impl StreamDirection {
    /// Determine direction from SslEvent rw field
    pub fn from_rw(rw: i32) -> Self {
        if rw == 1 {
            StreamDirection::Request
        } else {
            StreamDirection::Response
        }
    }
}

/// State of an HTTP/2 stream during aggregation
#[derive(Debug, Clone)]
pub enum Http2StreamState {
    /// Waiting for request data (HEADERS or DATA frames)
    WaitingRequestData {
        request_headers: Option<ParsedHttp2Frame>,
        request_data_frames: Vec<ParsedHttp2Frame>,
    },
    /// Request complete, waiting for response
    RequestComplete {
        request_headers: Option<ParsedHttp2Frame>,
        request_data_frames: Vec<ParsedHttp2Frame>,
    },
    /// Receiving response data
    ReceivingResponse {
        request_headers: Option<ParsedHttp2Frame>,
        request_data_frames: Vec<ParsedHttp2Frame>,
        response_headers: Option<ParsedHttp2Frame>,
        response_data_frames: Vec<ParsedHttp2Frame>,
    },
    /// Stream complete (both request and response have END_STREAM)
    Complete(Http2Stream),
}

impl Http2StreamState {
    pub fn state_name(&self) -> &str {
        match self {
            Http2StreamState::WaitingRequestData { .. } => "WaitingRequestData",
            Http2StreamState::RequestComplete { .. } => "RequestComplete",
            Http2StreamState::ReceivingResponse { .. } => "ReceivingResponse",
            Http2StreamState::Complete(_) => "Complete",
        }
    }
}

/// A complete or partial HTTP/2 stream
#[derive(Debug, Clone)]
pub struct Http2Stream {
    /// Stream identifier
    pub stream_id: StreamId,
    /// Request headers frame (HEADERS with END_HEADERS)
    pub request_headers: Option<ParsedHttp2Frame>,
    /// Request data frames (DATA frames in request direction)
    pub request_data_frames: Vec<ParsedHttp2Frame>,
    /// Response headers frame
    pub response_headers: Option<ParsedHttp2Frame>,
    /// Response data frames (DATA frames in response direction)
    pub response_data_frames: Vec<ParsedHttp2Frame>,
    /// Whether the request has END_STREAM
    pub request_complete: bool,
    /// Whether the response has END_STREAM
    pub response_complete: bool,
    /// Timestamp of the first frame
    pub start_timestamp_ns: u64,
    /// Timestamp of the last frame
    pub end_timestamp_ns: u64,
}

impl Http2Stream {
    /// Create a new empty stream
    pub fn new(stream_id: StreamId, timestamp_ns: u64) -> Self {
        Http2Stream {
            stream_id,
            request_headers: None,
            request_data_frames: Vec::new(),
            response_headers: None,
            response_data_frames: Vec::new(),
            request_complete: false,
            response_complete: false,
            start_timestamp_ns: timestamp_ns,
            end_timestamp_ns: timestamp_ns,
        }
    }

    /// Check if the stream is complete (both request and response have END_STREAM)
    pub fn is_complete(&self) -> bool {
        self.request_complete && self.response_complete
    }

    /// Add a frame to the stream
    /// Returns true if the stream becomes complete after adding this frame
    pub fn add_frame(&mut self, frame: &ParsedHttp2Frame, direction: StreamDirection) -> bool {
        self.end_timestamp_ns = self.end_timestamp_ns.max(frame.source_event.timestamp_ns);

        match direction {
            StreamDirection::Request => {
                if frame.is_headers() {
                    self.request_headers = Some(frame.clone());
                    if frame.has_end_stream() {
                        self.request_complete = true;
                    }
                } else if frame.is_data() {
                    self.request_data_frames.push(frame.clone());
                    if frame.has_end_stream() {
                        self.request_complete = true;
                    }
                }
            }
            StreamDirection::Response => {
                if frame.is_headers() {
                    self.response_headers = Some(frame.clone());
                    if frame.has_end_stream() {
                        self.response_complete = true;
                    }
                } else if frame.is_data() {
                    self.response_data_frames.push(frame.clone());
                    if frame.has_end_stream() {
                        self.response_complete = true;
                    }
                }
            }
        }

        self.is_complete()
    }

    /// Concatenate all request data frames into a single buffer
    pub fn request_body(&self) -> Vec<u8> {
        let mut result = Vec::new();
        if let Some(ref headers) = self.request_headers {
            // Include any data from HEADERS frame (though typically empty for HEADERS)
            let payload = headers.payload();
            if !payload.is_empty() {
                result.extend_from_slice(payload);
            }
        }
        for frame in &self.request_data_frames {
            result.extend_from_slice(frame.payload());
        }
        result
    }

    /// Concatenate all response data frames into a single buffer
    pub fn response_body(&self) -> Vec<u8> {
        let mut result = Vec::new();
        if let Some(ref headers) = self.response_headers {
            let payload = headers.payload();
            if !payload.is_empty() {
                result.extend_from_slice(payload);
            }
        }
        for frame in &self.response_data_frames {
            result.extend_from_slice(frame.payload());
        }
        result
    }

    /// Get request body as string (concatenates all data frames)
    pub fn request_body_str(&self) -> Option<String> {
        let body = self.request_body();
        if body.is_empty() {
            None
        } else {
            String::from_utf8(body).ok()
        }
    }

    /// Get response body as string (concatenates all data frames)
    pub fn response_body_str(&self) -> Option<String> {
        let body = self.response_body();
        if body.is_empty() {
            None
        } else {
            String::from_utf8(body).ok()
        }
    }

    /// Try to parse request body as JSON (concatenates all data frames first)
    pub fn request_json_body(&self) -> Option<serde_json::Value> {
        self.request_body_str()
            .and_then(|s| serde_json::from_str(&s).ok())
    }

    /// Try to parse response body as JSON (concatenates all data frames first)
    pub fn response_json_body(&self) -> Option<serde_json::Value> {
        self.response_body_str()
            .and_then(|s| serde_json::from_str(&s).ok())
    }

    /// Parse response body as SSE events and return JSON array of event data
    /// 
    /// This method parses the response body as SSE (Server-Sent Events) stream
    /// and returns a JSON array containing each event's data field.
    /// If the body is not valid SSE format, returns None.
    pub fn response_sse_json_array(&self) -> Option<serde_json::Value> {
        let body_str = self.response_body_str()?;
        
        // Use legacy SSEParser to parse the stream (returns owned data)
        let sse_events = SSEParser::parse_stream(&body_str);
        
        if sse_events.events.is_empty() {
            return None;
        }
        
        // Extract JSON data from each event
        let json_array: Vec<serde_json::Value> = sse_events.events
            .iter()
            .filter_map(|event| {
                // Skip [DONE] marker
                if event.data.trim() == "[DONE]" {
                    return None;
                }
                // Try to parse event data as JSON
                serde_json::from_str::<serde_json::Value>(&event.data).ok()
            })
            .collect();
        
        if json_array.is_empty() {
            None
        } else {
            Some(serde_json::Value::Array(json_array))
        }
    }

    /// Check if response content-type indicates SSE stream
    pub fn is_response_sse(&self) -> bool {
        self.response_headers.as_ref()
            .map(|h| {
                let headers = h.decode_headers_stateless();
                headers.iter()
                    .find(|(name, _)| name.eq_ignore_ascii_case("content-type"))
                    .and_then(|(_, value)| value.clone())
                    .map(|ct| ct.contains("text/event-stream"))
                    .unwrap_or(false)
            })
            .unwrap_or(false)
    }

    /// Extract HTTP method from request headers (e.g., "GET", "POST")
    pub fn method(&self) -> String {
        self.request_headers.as_ref()
            .map(|h| {
                let headers = h.decode_headers_stateless();
                headers.iter()
                    .find(|(name, _)| name == ":method")
                    .and_then(|(_, value)| value.clone())
                    .unwrap_or_else(|| "POST".to_string())
            })
            .unwrap_or_else(|| "POST".to_string())
    }

    /// Extract path from request headers (e.g., "/v1/chat/completions")
    pub fn path(&self) -> String {
        self.request_headers.as_ref()
            .map(|h| {
                let headers = h.decode_headers_stateless();
                headers.iter()
                    .find(|(name, _)| name == ":path")
                    .and_then(|(_, value)| value.clone())
                    .unwrap_or_default()
            })
            .unwrap_or_default()
    }

    /// Extract status code from response headers
    pub fn status_code(&self) -> u16 {
        self.response_headers.as_ref()
            .map(|h| {
                let headers = h.decode_headers_stateless();
                headers.iter()
                    .find(|(name, _)| name == ":status")
                    .and_then(|(_, value)| value.clone())
                    .and_then(|v| v.parse().ok())
                    .unwrap_or(0)
            })
            .unwrap_or(0)
    }

    /// Get request headers as JSON string
    pub fn request_headers_json(&self) -> String {
        if let Some(ref headers) = self.request_headers {
            let decoded = headers.decode_headers_stateless()
                .into_iter()
                .filter_map(|(name, value)| value.map(|v| (name, v)))
                .collect::<std::collections::HashMap<String, String>>();
            serde_json::to_string(&decoded).unwrap_or_default()
        } else {
            String::new()
        }
    }

    /// Get response headers as JSON string
    pub fn response_headers_json(&self) -> String {
        if let Some(ref headers) = self.response_headers {
            let decoded = headers.decode_headers_stateless()
                .into_iter()
                .filter_map(|(name, value)| value.map(|v| (name, v)))
                .collect::<std::collections::HashMap<String, String>>();
            serde_json::to_string(&decoded).unwrap_or_default()
        } else {
            String::new()
        }
    }

    /// Get process command name from source event
    pub fn comm(&self) -> String {
        self.request_headers.as_ref()
            .map(|h| h.source_event.comm_str())
            .or_else(|| self.request_data_frames.first().map(|f| f.source_event.comm_str()))
            .or_else(|| self.response_headers.as_ref().map(|h| h.source_event.comm_str()))
            .or_else(|| self.response_data_frames.first().map(|f| f.source_event.comm_str()))
            .unwrap_or_default()
    }

    /// Get process ID from source event
    pub fn pid(&self) -> u32 {
        self.request_headers.as_ref()
            .map(|h| h.source_event.pid)
            .or_else(|| self.request_data_frames.first().map(|f| f.source_event.pid))
            .or_else(|| self.response_headers.as_ref().map(|h| h.source_event.pid))
            .or_else(|| self.response_data_frames.first().map(|f| f.source_event.pid))
            .unwrap_or(0)
    }
}

/// HTTP/2 Stream Aggregator
///
/// Aggregates HTTP/2 frames by stream_id within a connection,
/// correlating request and response frames to form complete streams.
#[derive(Debug)]
pub struct Http2StreamAggregator {
    /// Active streams being aggregated (key: StreamId)
    streams: LruCache<StreamId, Http2StreamState>,
    /// Completed streams waiting to be retrieved
    completed_streams: Vec<Http2Stream>,
}

impl Default for Http2StreamAggregator {
    fn default() -> Self {
        Self::new()
    }
}

impl Http2StreamAggregator {
    /// Create a new aggregator with default capacity
    pub fn new() -> Self {
        Http2StreamAggregator {
            streams: LruCache::new(NonZeroUsize::new(DEFAULT_CONNECTION_CAPACITY * 4).unwrap()),
            completed_streams: Vec::new(),
        }
    }

    /// Create a new aggregator with custom capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Http2StreamAggregator {
            streams: LruCache::new(NonZeroUsize::new(capacity).unwrap()),
            completed_streams: Vec::new(),
        }
    }

    /// Process a batch of HTTP/2 frames
    ///
    /// Returns completed streams that have both request and response with END_STREAM
    pub fn process_frames(&mut self, frames: Vec<ParsedHttp2Frame>) -> Vec<Http2Stream> {
        let mut completed = Vec::new();

        for frame in frames {
            // Skip non-stream frames (SETTINGS, PING, etc.)
            if frame.stream_id == 0 {
                continue;
            }

            let connection_id = ConnectionId::from_ssl_event(&frame.source_event);
            let stream_id = StreamId::new(connection_id, frame.stream_id);
            let direction = StreamDirection::from_rw(frame.source_event.rw);

            // Get or create stream state
            let state = self.streams.pop(&stream_id);
            let mut state = state.unwrap_or_else(|| {
                Http2StreamState::WaitingRequestData {
                    request_headers: None,
                    request_data_frames: Vec::new(),
                }
            });

            // Process frame based on current state and direction
            state = self.process_frame_in_state(state, frame, direction, &stream_id);

            // Check if stream is now complete
            match state {
                Http2StreamState::Complete(stream) => {
                    completed.push(stream);
                }
                _ => {
                    self.streams.put(stream_id, state);
                }
            }
        }

        completed
    }

    /// Process a single frame within the context of a stream state
    fn process_frame_in_state(
        &self,
        state: Http2StreamState,
        frame: ParsedHttp2Frame,
        direction: StreamDirection,
        stream_id: &StreamId,
    ) -> Http2StreamState {
        log::debug!("Processing http/2 frame in state: {}, stream_id: {:?}", state.state_name(), stream_id);
        match state {
            Http2StreamState::WaitingRequestData { mut request_headers, mut request_data_frames } => {
                if direction == StreamDirection::Request {
                    if frame.is_headers() {
                        request_headers = Some(frame.clone());
                        if frame.has_end_stream() {
                            // Request is complete (no body)
                            return Http2StreamState::RequestComplete {
                                request_headers,
                                request_data_frames,
                            };
                        }
                    } else if frame.is_data() {
                        request_data_frames.push(frame.clone());
                        if frame.has_end_stream() {
                            // Request is complete
                            return Http2StreamState::RequestComplete {
                                request_headers,
                                request_data_frames,
                            };
                        }
                    }
                    // Continue waiting for more request data
                    Http2StreamState::WaitingRequestData {
                        request_headers,
                        request_data_frames,
                    }
                } else {
                    // Unexpected response before request complete, stay in waiting state
                    Http2StreamState::WaitingRequestData {
                        request_headers,
                        request_data_frames,
                    }
                }
            }

            Http2StreamState::RequestComplete { request_headers, request_data_frames } => {
                if direction == StreamDirection::Response {
                    let mut response_headers = None;
                    let mut response_data_frames = Vec::new();
                    
                    if frame.is_headers() {
                        response_headers = Some(frame.clone());
                        if frame.has_end_stream() {
                            // Response is complete (no body)
                            let mut stream = Http2Stream::new(*stream_id, 
                                request_headers.as_ref().map(|h| h.source_event.timestamp_ns)
                                    .unwrap_or(frame.source_event.timestamp_ns));
                            stream.request_headers = request_headers;
                            stream.request_data_frames = request_data_frames;
                            stream.request_complete = true;
                            stream.response_headers = response_headers;
                            stream.response_complete = true;
                            stream.end_timestamp_ns = frame.source_event.timestamp_ns;
                            return Http2StreamState::Complete(stream);
                        }
                    } else if frame.is_data() {
                        response_data_frames.push(frame.clone());
                        if frame.has_end_stream() {
                            // Response is complete
                            let mut stream = Http2Stream::new(*stream_id,
                                request_headers.as_ref().map(|h| h.source_event.timestamp_ns)
                                    .unwrap_or(frame.source_event.timestamp_ns));
                            stream.request_headers = request_headers;
                            stream.request_data_frames = request_data_frames;
                            stream.request_complete = true;
                            stream.response_headers = response_headers;
                            stream.response_data_frames = response_data_frames;
                            stream.response_complete = true;
                            stream.end_timestamp_ns = frame.source_event.timestamp_ns;
                            return Http2StreamState::Complete(stream);
                        }
                    }
                    
                    // Continue receiving response data
                    Http2StreamState::ReceivingResponse {
                        request_headers,
                        request_data_frames,
                        response_headers,
                        response_data_frames,
                    }
                } else {
                    // Stay in request complete state
                    Http2StreamState::RequestComplete {
                        request_headers,
                        request_data_frames,
                    }
                }
            }

            Http2StreamState::ReceivingResponse {
                request_headers,
                request_data_frames,
                mut response_headers,
                mut response_data_frames,
            } => {
                if direction == StreamDirection::Response {
                    if frame.is_headers() {
                        response_headers = Some(frame.clone());
                        if frame.has_end_stream() {
                            // Response is complete
                            let mut stream = Http2Stream::new(*stream_id,
                                request_headers.as_ref().map(|h| h.source_event.timestamp_ns)
                                    .unwrap_or(frame.source_event.timestamp_ns));
                            stream.request_headers = request_headers;
                            stream.request_data_frames = request_data_frames;
                            stream.request_complete = true;
                            stream.response_headers = response_headers;
                            stream.response_data_frames = response_data_frames;
                            stream.response_complete = true;
                            stream.end_timestamp_ns = frame.source_event.timestamp_ns;
                            return Http2StreamState::Complete(stream);
                        }
                    } else if frame.is_data() {
                        response_data_frames.push(frame.clone());
                        if frame.has_end_stream() {
                            // Response is complete
                            let mut stream = Http2Stream::new(*stream_id,
                                request_headers.as_ref().map(|h| h.source_event.timestamp_ns)
                                    .unwrap_or(frame.source_event.timestamp_ns));
                            stream.request_headers = request_headers;
                            stream.request_data_frames = request_data_frames;
                            stream.request_complete = true;
                            stream.response_headers = response_headers;
                            stream.response_data_frames = response_data_frames;
                            stream.response_complete = true;
                            stream.end_timestamp_ns = frame.source_event.timestamp_ns;
                            return Http2StreamState::Complete(stream);
                        }
                    }
                }
                // Continue receiving response data
                Http2StreamState::ReceivingResponse {
                    request_headers,
                    request_data_frames,
                    response_headers,
                    response_data_frames,
                }
            }

            Http2StreamState::Complete(stream) => {
                // Stream already complete, shouldn't receive more frames
                Http2StreamState::Complete(stream)
            }
        }
    }

    /// Check if there are any pending streams
    pub fn has_pending(&self) -> bool {
        !self.streams.is_empty()
    }

    /// Get count of active streams
    pub fn active_stream_count(&self) -> usize {
        self.streams.len()
    }

    /// Clear all streams
    pub fn clear(&mut self) {
        self.streams.clear();
        self.completed_streams.clear();
    }

    /// Drain all pending streams and return them as completed
    /// Useful for shutdown or forced completion
    pub fn drain_pending(&mut self) -> Vec<Http2Stream> {
        let mut result = Vec::new();
        
        // Move all streams from LRU cache
        while let Some((stream_id, state)) = self.streams.pop_lru() {
            if let Some(stream) = self.stream_from_state(state, stream_id) {
                result.push(stream);
            }
        }
        
        result
    }

    /// Convert a stream state to a Http2Stream if possible
    fn stream_from_state(&self, state: Http2StreamState, stream_id: StreamId) -> Option<Http2Stream> {
        match state {
            Http2StreamState::Complete(stream) => Some(stream),
            Http2StreamState::RequestComplete { request_headers, request_data_frames } => {
                let timestamp_ns = request_headers.as_ref()
                    .map(|h| h.source_event.timestamp_ns)
                    .unwrap_or_else(|| request_data_frames.first()
                        .map(|f| f.source_event.timestamp_ns)
                        .unwrap_or(0));
                let mut stream = Http2Stream::new(stream_id, timestamp_ns);
                stream.request_headers = request_headers;
                stream.request_data_frames = request_data_frames;
                stream.request_complete = true;
                Some(stream)
            }
            Http2StreamState::ReceivingResponse { 
                request_headers, 
                request_data_frames, 
                response_headers, 
                response_data_frames 
            } => {
                let timestamp_ns = request_headers.as_ref()
                    .map(|h| h.source_event.timestamp_ns)
                    .unwrap_or_else(|| request_data_frames.first()
                        .map(|f| f.source_event.timestamp_ns)
                        .unwrap_or(0));
                let mut stream = Http2Stream::new(stream_id, timestamp_ns);
                stream.request_headers = request_headers;
                stream.request_data_frames = request_data_frames;
                stream.request_complete = true;
                stream.response_headers = response_headers;
                stream.response_data_frames = response_data_frames;
                Some(stream)
            }
            Http2StreamState::WaitingRequestData { .. } => None,
        }
    }
}

/// Convert Http2Stream to AggregatedResult
impl From<Http2Stream> for AggregatedResult {
    fn from(stream: Http2Stream) -> Self {
        AggregatedResult::Http2StreamComplete(stream)
    }
}

impl ToChromeTraceEvent for Http2Stream {
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let mut events = Vec::new();
        let ts_us = ns_to_us(self.start_timestamp_ns);
        let dur_us = ns_to_us(self.end_timestamp_ns.saturating_sub(self.start_timestamp_ns));
        const MIN_DUR_US: u64 = 1_000;
        let actual_dur = dur_us.max(MIN_DUR_US);

        // Create a single complete event representing the entire stream
        let stream_event = ChromeTraceEvent::complete(
            format!("HTTP/2 stream={}", self.stream_id.stream_id),
            "http2.stream",
            self.stream_id.connection_id.pid,
            0, // tid not available at stream level
            ts_us,
            actual_dur,
        );

        events.push(stream_event);

        // Add events for individual frames
        if let Some(ref headers) = self.request_headers {
            events.extend(headers.to_chrome_trace_events());
        }
        for frame in &self.request_data_frames {
            events.extend(frame.to_chrome_trace_events());
        }
        if let Some(ref headers) = self.response_headers {
            events.extend(headers.to_chrome_trace_events());
        }
        for frame in &self.response_data_frames {
            events.extend(frame.to_chrome_trace_events());
        }

        events
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::rc::Rc;
    use crate::probes::sslsniff::SslEvent;

    fn create_test_event(pid: u32, ssl_ptr: u64, rw: i32, timestamp_ns: u64) -> Rc<SslEvent> {
        Rc::new(SslEvent {
            source: 0,
            timestamp_ns,
            delta_ns: 0,
            pid,
            tid: 1,
            uid: 0,
            len: 0,
            rw,
            comm: "test".to_string(),
            buf: Vec::new(),
            is_handshake: false,
            ssl_ptr,
        })
    }

    fn create_test_frame(
        stream_id: u32,
        frame_type: u8,
        flags: u8,
        payload: Vec<u8>,
        event: Rc<SslEvent>,
    ) -> ParsedHttp2Frame {
        let payload_offset = 9; // Skip frame header
        let payload_len = payload.len();
        
        // Create a new event with the payload in buf
        let mut buf = Vec::with_capacity(9 + payload_len);
        // Frame header
        buf.push(((payload_len >> 16) & 0xFF) as u8);
        buf.push(((payload_len >> 8) & 0xFF) as u8);
        buf.push((payload_len & 0xFF) as u8);
        buf.push(frame_type);
        buf.push(flags);
        buf.push(((stream_id >> 24) & 0x7F) as u8);
        buf.push(((stream_id >> 16) & 0xFF) as u8);
        buf.push(((stream_id >> 8) & 0xFF) as u8);
        buf.push((stream_id & 0xFF) as u8);
        // Payload
        buf.extend_from_slice(&payload);
        
        let event_with_buf = Rc::new(SslEvent {
            source: event.source,
            timestamp_ns: event.timestamp_ns,
            delta_ns: event.delta_ns,
            pid: event.pid,
            tid: event.tid,
            uid: event.uid,
            len: buf.len() as u32,
            rw: event.rw,
            comm: event.comm.clone(),
            buf,
            is_handshake: event.is_handshake,
            ssl_ptr: event.ssl_ptr,
        });

        ParsedHttp2Frame {
            frame_type: match frame_type {
                0 => crate::parser::http2::Http2FrameType::Data,
                1 => crate::parser::http2::Http2FrameType::Headers,
                _ => crate::parser::http2::Http2FrameType::Unknown(frame_type),
            },
            flags,
            stream_id,
            payload_offset,
            payload_len,
            source_event: event_with_buf,
        }
    }

    #[test]
    fn test_stream_direction_from_rw() {
        assert_eq!(StreamDirection::from_rw(1), StreamDirection::Request);
        assert_eq!(StreamDirection::from_rw(0), StreamDirection::Response);
    }

    #[test]
    fn test_aggregator_process_request_response() {
        let mut aggregator = Http2StreamAggregator::new();
        let _conn_id = ConnectionId { pid: 1234, ssl_ptr: 0x1000 };

        // Create request HEADERS frame (rw=1, write) with END_STREAM (no body)
        let req_event = create_test_event(1234, 0x1000, 1, 1000);
        let req_headers = create_test_frame(
            1, // stream_id
            1, // HEADERS
            0x05, // END_HEADERS | END_STREAM - request has no body
            b":method: POST\n:path: /api/test".to_vec(),
            req_event,
        );

        // Process request
        let completed = aggregator.process_frames(vec![req_headers]);
        assert!(completed.is_empty()); // Request complete but waiting for response
        assert_eq!(aggregator.active_stream_count(), 1);

        // Create response HEADERS frame (rw=0, read)
        let resp_event = create_test_event(1234, 0x1000, 0, 2000);
        let resp_headers = create_test_frame(
            1, // stream_id
            1, // HEADERS
            0x05, // END_HEADERS | END_STREAM
            b":status: 200".to_vec(),
            resp_event,
        );

        // Process response
        let completed = aggregator.process_frames(vec![resp_headers]);
        assert_eq!(completed.len(), 1);
        
        let stream = &completed[0];
        assert_eq!(stream.stream_id.stream_id, 1);
        assert!(stream.request_complete);
        assert!(stream.response_complete);
        assert!(stream.is_complete());
    }

    #[test]
    fn test_aggregator_with_data_frames() {
        let mut aggregator = Http2StreamAggregator::new();

        // Request HEADERS (no END_STREAM, expecting body) - rw=1 for request
        let req_event = create_test_event(1234, 0x1000, 1, 1000);
        let req_headers = create_test_frame(1, 1, 0x04, vec![], req_event.clone());

        // Request DATA with END_STREAM
        let req_data = create_test_frame(1, 0, 0x01, b"{\"key\":\"value\"}".to_vec(), req_event);

        // Process request
        let completed = aggregator.process_frames(vec![req_headers, req_data]);
        assert!(completed.is_empty()); // Still waiting for response

        // Response HEADERS with END_STREAM (no body) - rw=0 for response
        let resp_event = create_test_event(1234, 0x1000, 0, 2000);
        let resp_headers = create_test_frame(1, 1, 0x05, b":status: 200".to_vec(), resp_event);

        let completed = aggregator.process_frames(vec![resp_headers]);
        assert_eq!(completed.len(), 1);
        
        let stream = &completed[0];
        assert_eq!(stream.request_data_frames.len(), 1);
        assert_eq!(stream.response_data_frames.len(), 0);
    }
}
