//! HTTP/2 Frame types
//!
//! Defines `Http2FrameType` and `ParsedHttp2Frame` for zero-copy
//! HTTP/2 binary frame representation.

use std::fmt;
use std::rc::Rc;
use crate::probes::sslsniff::SslEvent;
use crate::chrome_trace::{TraceArgs, ToChromeTraceEvent, ChromeTraceEvent, ns_to_us};
use serde_json::json;
use hpack::Decoder;

/// HTTP/2 frame type (RFC 7540 Section 6)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Http2FrameType {
    Data,
    Headers,
    Priority,
    RstStream,
    Settings,
    PushPromise,
    Ping,
    Goaway,
    WindowUpdate,
    Continuation,
    Unknown(u8),
}

impl Http2FrameType {
    /// Parse from raw frame type byte
    pub fn from_u8(value: u8) -> Self {
        match value {
            0 => Http2FrameType::Data,
            1 => Http2FrameType::Headers,
            2 => Http2FrameType::Priority,
            3 => Http2FrameType::RstStream,
            4 => Http2FrameType::Settings,
            5 => Http2FrameType::PushPromise,
            6 => Http2FrameType::Ping,
            7 => Http2FrameType::Goaway,
            8 => Http2FrameType::WindowUpdate,
            9 => Http2FrameType::Continuation,
            v => Http2FrameType::Unknown(v),
        }
    }

    /// Get human-readable name
    pub fn name(&self) -> &'static str {
        match self {
            Http2FrameType::Data => "DATA",
            Http2FrameType::Headers => "HEADERS",
            Http2FrameType::Priority => "PRIORITY",
            Http2FrameType::RstStream => "RST_STREAM",
            Http2FrameType::Settings => "SETTINGS",
            Http2FrameType::PushPromise => "PUSH_PROMISE",
            Http2FrameType::Ping => "PING",
            Http2FrameType::Goaway => "GOAWAY",
            Http2FrameType::WindowUpdate => "WINDOW_UPDATE",
            Http2FrameType::Continuation => "CONTINUATION",
            Http2FrameType::Unknown(_) => "UNKNOWN",
        }
    }
}

/// Parsed HTTP/2 frame (zero-copy)
#[derive(Clone)]
pub struct ParsedHttp2Frame {
    pub frame_type: Http2FrameType,
    pub flags: u8,
    pub stream_id: u32,
    pub payload_offset: usize,
    pub payload_len: usize,
    pub source_event: Rc<SslEvent>,
}

impl ParsedHttp2Frame {
    /// Zero-copy access to frame payload
    pub fn payload(&self) -> &[u8] {
        &self.source_event.buf[self.payload_offset..self.payload_offset + self.payload_len]
    }

    /// Payload as UTF-8 string
    pub fn body_str(&self) -> &str {
        std::str::from_utf8(self.payload()).unwrap_or("")
    }

    /// Try to parse payload as JSON (useful for DATA frames)
    pub fn json_body(&self) -> Option<serde_json::Value> {
        if self.payload_len == 0 {
            return None;
        }
        let body_str = String::from_utf8_lossy(self.payload());
        serde_json::from_str(&body_str).ok()
    }

    pub fn is_data(&self) -> bool {
        self.frame_type == Http2FrameType::Data
    }

    pub fn is_headers(&self) -> bool {
        self.frame_type == Http2FrameType::Headers
    }

    pub fn is_settings(&self) -> bool {
        self.frame_type == Http2FrameType::Settings
    }

    /// Check END_STREAM flag (0x01) on DATA/HEADERS frames
    pub fn has_end_stream(&self) -> bool {
        matches!(self.frame_type, Http2FrameType::Data | Http2FrameType::Headers)
            && (self.flags & 0x01) != 0
    }

    /// Check END_HEADERS flag (0x04) on HEADERS/CONTINUATION frames
    pub fn has_end_headers(&self) -> bool {
        matches!(self.frame_type, Http2FrameType::Headers | Http2FrameType::Continuation)
            && (self.flags & 0x04) != 0
    }

    /// Human-readable frame type name
    pub fn type_name(&self) -> &'static str {
        self.frame_type.name()
    }

    /// Human-readable flags description
    pub fn flags_description(&self) -> String {
        let mut flags = Vec::new();
        match self.frame_type {
            Http2FrameType::Data => {
                if self.flags & 0x01 != 0 { flags.push("END_STREAM"); }
                if self.flags & 0x08 != 0 { flags.push("PADDED"); }
            }
            Http2FrameType::Headers => {
                if self.flags & 0x01 != 0 { flags.push("END_STREAM"); }
                if self.flags & 0x04 != 0 { flags.push("END_HEADERS"); }
                if self.flags & 0x08 != 0 { flags.push("PADDED"); }
                if self.flags & 0x20 != 0 { flags.push("PRIORITY"); }
            }
            Http2FrameType::Settings | Http2FrameType::Ping => {
                if self.flags & 0x01 != 0 { flags.push("ACK"); }
            }
            Http2FrameType::Continuation => {
                if self.flags & 0x04 != 0 { flags.push("END_HEADERS"); }
            }
            Http2FrameType::PushPromise => {
                if self.flags & 0x04 != 0 { flags.push("END_HEADERS"); }
                if self.flags & 0x08 != 0 { flags.push("PADDED"); }
            }
            _ => {}
        }
        if flags.is_empty() {
            format!("0x{:02x}", self.flags)
        } else {
            flags.join(" | ")
        }
    }

    /// Decode HPACK-encoded headers using a provided decoder
    /// 
    /// This method requires a stateful HPACK decoder because HTTP/2 header
    /// compression uses a dynamic table that persists across frames.
    /// 
    /// # Arguments
    /// * `decoder` - A mutable reference to an HPACK decoder (maintains dynamic table state)
    /// 
    /// # Returns
    /// * `Some(Vec<(String, String)>)` - Decoded header name-value pairs on success
    /// * `None` - If this is not a HEADERS frame or decoding failed
    pub fn decode_headers(&self, decoder: &mut Decoder) -> Option<Vec<(String, String)>> {
        if !self.is_headers() && self.frame_type != Http2FrameType::Continuation {
            return None;
        }
        
        let payload = self.payload();
        if payload.is_empty() {
            return Some(Vec::new());
        }
        
        decoder.decode(payload).ok().map(|headers| {
            headers
                .into_iter()
                .map(|(name, value)| {
                    let name_str = String::from_utf8_lossy(&name).to_string();
                    let value_str = String::from_utf8_lossy(&value).to_string();
                    (name_str, value_str)
                })
                .collect()
        })
    }

    /// Decode headers using only the static HPACK table (stateless)
    /// 
    /// This method does NOT maintain dynamic table state, so it can only
    /// decode headers that use static table indices. Useful for quick inspection
    /// without tracking connection state.
    /// 
    /// # Returns
    /// Decoded header name-value pairs (only static table entries will be resolved)
    pub fn decode_headers_stateless(&self) -> Vec<(String, Option<String>)> {
        if !self.is_headers() && self.frame_type != Http2FrameType::Continuation {
            return Vec::new();
        }
        
        let payload = self.payload();
        if payload.is_empty() {
            return Vec::new();
        }
        
        let mut result = Vec::new();
        let mut pos = 0;
        
        while pos < payload.len() {
            let first_byte = payload[pos];
            
            // Indexed Header Field (1xxxxxxx) - fully indexed in static or dynamic table
            if first_byte & 0x80 != 0 {
                let index = (first_byte & 0x7F) as usize;
                if let Some((name, value)) = Self::get_static_table_entry(index) {
                    result.push((name.to_string(), Some(value.to_string())));
                } else if index == 0 {
                    break; // Invalid
                } else {
                    // Dynamic table index - cannot decode without state
                    result.push((format!("<dynamic:{}>", index), None));
                }
                pos += 1;
            }
            // Literal Header Field with Incremental Indexing (01xxxxxx)
            else if first_byte & 0xC0 == 0x40 {
                let (name, value, consumed) = self.decode_literal_header(payload, pos, true);
                result.push((name, Some(value)));
                pos += consumed;
            }
            // Dynamic Table Size Update (001xxxxx)
            else if first_byte & 0xE0 == 0x20 {
                // Skip this for stateless decoding
                pos += 1;
            }
            // Literal Header Field without Indexing (0000xxxx) or Never Indexed (0001xxxx)
            else {
                let (name, value, consumed) = self.decode_literal_header(payload, pos, false);
                result.push((name, Some(value)));
                pos += consumed;
            }
        }
        
        result
    }

    /// Decode a literal header field
    fn decode_literal_header(&self, payload: &[u8], start: usize, _indexed: bool) -> (String, String, usize) {
        let mut pos = start;
        let first_byte = payload[pos];
        pos += 1;
        
        // Extract name (either from static table or literal)
        let name: String;
        let name_index = (first_byte & 0x3F) as usize;
        
        if name_index > 0 {
            // Name is in static table
            if let Some((n, _)) = Self::get_static_table_entry(name_index) {
                name = n.to_string();
            } else {
                name = format!("<unknown:{}>", name_index);
            }
        } else {
            // Name is literal string
            let (lit_name, consumed) = Self::decode_literal_string(payload, pos);
            name = lit_name;
            pos += consumed;
        }
        
        // Decode value string
        let (value, consumed) = Self::decode_literal_string(payload, pos);
        pos += consumed;
        
        (name, value, pos - start)
    }

    /// Decode a literal string (length-prefixed, possibly Huffman encoded)
    fn decode_literal_string(payload: &[u8], start: usize) -> (String, usize) {
        if start >= payload.len() {
            return (String::new(), 0);
        }
        
        let mut pos = start;
        let first_byte = payload[pos];
        let is_huffman = (first_byte & 0x80) != 0;
        
        // Decode length (variable length integer, 7 bits in first byte)
        let mut length = (first_byte & 0x7F) as usize;
        pos += 1;
        
        // Check if more length bytes follow (this is a simplification)
        // In full HPACK, length can be multi-byte
        if length == 0x7F && pos < payload.len() {
            // Extended length encoding (not common in practice)
            length = 0;
            loop {
                let b = payload[pos];
                pos += 1;
                length += (b & 0x7F) as usize;
                if b & 0x80 == 0 {
                    break;
                }
            }
        }
        
        if pos + length > payload.len() {
            return (String::new(), pos - start);
        }
        
        let string_bytes = &payload[pos..pos + length];
        
        let result = if is_huffman {
            // Huffman decode
            Self::huffman_decode(string_bytes)
        } else {
            String::from_utf8_lossy(string_bytes).to_string()
        };
        
        (result, pos + length - start)
    }

    /// Simple Huffman decoder for HPACK
    fn huffman_decode(data: &[u8]) -> String {
        // HPACK uses a specific Huffman code. For simplicity, we'll use
        // a basic approach - in production, use the hpack crate's decoder
        // which handles this correctly.
        // 
        // For now, return a placeholder indicating Huffman-encoded data
        // The proper implementation would use the Huffman tree from RFC 7541
        format!("<huffman:{} bytes>", data.len())
    }

    /// Get an entry from the HPACK static table (RFC 7541 Appendix A)
    fn get_static_table_entry(index: usize) -> Option<(&'static str, &'static str)> {
        match index {
            1 => Some((":authority", "")),
            2 => Some((":method", "GET")),
            3 => Some((":method", "POST")),
            4 => Some((":path", "/")),
            5 => Some((":path", "/index.html")),
            6 => Some((":scheme", "http")),
            7 => Some((":scheme", "https")),
            8 => Some((":status", "200")),
            9 => Some((":status", "204")),
            10 => Some((":status", "206")),
            11 => Some((":status", "304")),
            12 => Some((":status", "400")),
            13 => Some((":status", "404")),
            14 => Some((":status", "500")),
            15 => Some(("accept-charset", "")),
            16 => Some(("accept-encoding", "gzip, deflate")),
            17 => Some(("accept-language", "")),
            18 => Some(("accept-ranges", "")),
            19 => Some(("accept", "")),
            20 => Some(("access-control-allow-origin", "")),
            21 => Some(("age", "")),
            22 => Some(("allow", "")),
            23 => Some(("authorization", "")),
            24 => Some(("cache-control", "")),
            25 => Some(("content-disposition", "")),
            26 => Some(("content-encoding", "")),
            27 => Some(("content-language", "")),
            28 => Some(("content-length", "")),
            29 => Some(("content-location", "")),
            30 => Some(("content-range", "")),
            31 => Some(("content-type", "")),
            32 => Some(("date", "")),
            33 => Some(("etag", "")),
            34 => Some(("expect", "")),
            35 => Some(("expires", "")),
            36 => Some(("from", "")),
            37 => Some(("host", "")),
            38 => Some(("if-match", "")),
            39 => Some(("if-modified-since", "")),
            40 => Some(("if-none-match", "")),
            41 => Some(("if-range", "")),
            42 => Some(("if-unmodified-since", "")),
            43 => Some(("last-modified", "")),
            44 => Some(("link", "")),
            45 => Some(("location", "")),
            46 => Some(("max-forwards", "")),
            47 => Some(("proxy-authenticate", "")),
            48 => Some(("proxy-authorization", "")),
            49 => Some(("range", "")),
            50 => Some(("referer", "")),
            51 => Some(("refresh", "")),
            52 => Some(("retry-after", "")),
            53 => Some(("server", "")),
            54 => Some(("set-cookie", "")),
            55 => Some(("strict-transport-security", "")),
            56 => Some(("transfer-encoding", "")),
            57 => Some(("user-agent", "")),
            58 => Some(("vary", "")),
            59 => Some(("via", "")),
            60 => Some(("www-authenticate", "")),
            61 => Some(("x-forwarded-for", "")),
            _ => None,
        }
    }
}

impl TraceArgs for ParsedHttp2Frame {
    fn to_trace_args(&self) -> serde_json::Value {
        let mut args = serde_json::Map::new();
        args.insert("frame_type".to_string(), json!(self.type_name()));
        args.insert("flags".to_string(), json!(self.flags_description()));
        args.insert("stream_id".to_string(), json!(self.stream_id));
        args.insert("payload_len".to_string(), json!(self.payload_len));
        args.insert("pid".to_string(), json!(self.source_event.pid));
        args.insert("tid".to_string(), json!(self.source_event.tid));
        args.insert("comm".to_string(), json!(self.source_event.comm_str()));

        if self.is_data() && self.payload_len > 0 {
            if let Some(json_body) = self.json_body() {
                args.insert("body".to_string(), json_body);
            } else {
                let preview = self.body_str();
                if !preview.is_empty() {
                    let truncated = if preview.len() > 200 { &preview[..200] } else { preview };
                    args.insert("body_preview".to_string(), json!(truncated));
                }
            }
        }

        // Decode HPACK headers for HEADERS frames
        if self.is_headers() && self.payload_len > 0 {
            let headers = self.decode_headers_stateless();
            if !headers.is_empty() {
                let headers_json: serde_json::Map<String, serde_json::Value> = headers
                    .into_iter()
                    .map(|(name, value)| {
                        let v = value.unwrap_or_else(|| "<undecoded>".to_string());
                        (name, json!(v))
                    })
                    .collect();
                args.insert("headers".to_string(), serde_json::Value::Object(headers_json));
            }
        }

        serde_json::Value::Object(args)
    }
}

impl ToChromeTraceEvent for ParsedHttp2Frame {
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let ts_us = ns_to_us(self.source_event.timestamp_ns);
        const MIN_DUR_US: u64 = 1_000;

        let event = ChromeTraceEvent::complete(
            format!("H2 {} stream={}", self.type_name(), self.stream_id),
            "http2.frame",
            self.source_event.pid,
            self.source_event.tid as u64,
            ts_us,
            MIN_DUR_US,
        )
        .with_trace_args(self);

        vec![event]
    }
}

impl fmt::Debug for ParsedHttp2Frame {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut debug = f.debug_struct("ParsedHttp2Frame");
        debug
            .field("type", &self.type_name())
            .field("flags", &self.flags_description())
            .field("stream_id", &self.stream_id)
            .field("payload_len", &self.payload_len);

        if self.is_data() && self.payload_len > 0 {
            let body = self.payload();
            if let Ok(json) = serde_json::from_slice::<serde_json::Value>(body) {
                let formatted = serde_json::to_string_pretty(&json).unwrap_or_default();
                debug.field("body", &format!("(json, {} bytes)\n{}", body.len(), formatted));
            } else if let Ok(text) = std::str::from_utf8(body) {
                let text = text.trim();
                if text.len() > 200 {
                    debug.field("body", &format!("(text, {} bytes)\n{}...", body.len(), &text[..200]));
                } else {
                    debug.field("body", &format!("(text, {} bytes)\n{}", body.len(), text));
                }
            } else {
                debug.field("body", &format!("(binary, {} bytes)", body.len()));
            }
        }

        // Decode HPACK headers for HEADERS frames
        if self.is_headers() && self.payload_len > 0 {
            let headers = self.decode_headers_stateless();
            if !headers.is_empty() {
                let header_strs: Vec<String> = headers
                    .into_iter()
                    .map(|(name, value)| {
                        match value {
                            Some(v) => format!("  {}: {}", name, v),
                            None => format!("  {}: <undecoded>", name),
                        }
                    })
                    .collect();
                debug.field("headers", &format!("\n{}", header_strs.join("\n")));
            }
        }

        debug
            .field("pid", &self.source_event.pid)
            .field("tid", &self.source_event.tid)
            .field("timestamp_ns", &self.source_event.timestamp_ns);

        debug.finish()
    }
}
