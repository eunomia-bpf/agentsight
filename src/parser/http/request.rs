//! HTTP Request types

use std::collections::HashMap;
use std::fmt;
use std::rc::Rc;
use crate::probes::sslsniff::SslEvent;
use crate::chrome_trace::{TraceArgs, ToChromeTraceEvent, ChromeTraceEvent, ns_to_us};
use serde_json::json;

/// 解析后的 HTTP Request
#[derive(Clone)]
pub struct ParsedRequest {
    pub method: String,              // GET, POST, etc.
    pub path: String,                // /api/chat
    pub version: u8,                 // 11 for HTTP/1.1
    pub headers: HashMap<String, String>,
    pub body_offset: usize,          // body 在 source_event.buf 中的起始位置
    pub body_len: usize,             // body 长度
    pub source_event: Rc<SslEvent>,  // 原始 SslEvent (Rc 避免拷贝)
}

impl ParsedRequest {
    /// 获取 body 数据（零拷贝）
    pub fn body(&self) -> &[u8] {
        &self.source_event.buf[self.body_offset..self.body_offset + self.body_len]
    }

    pub fn body_str(&self) -> &str {
        std::str::from_utf8(self.body()).unwrap_or("")
    }
    
    /// 尝试将 body 解析为 JSON
    /// 
    /// 如果 body 是有效的 UTF-8 且是有效的 JSON，返回解析后的 Value
    /// 否则返回 null
    pub fn json_body(&self) -> Option<serde_json::Value> {
        if self.body_len == 0 {
            return None;
        }
        let body = self.body();
        let body_str = String::from_utf8_lossy(body);
        serde_json::from_str(&body_str).ok()
    }
}

impl TraceArgs for ParsedRequest {
    fn to_trace_args(&self) -> serde_json::Value {
        let mut args = serde_json::Map::new();
        
        // Basic request info
        args.insert("method".to_string(), json!(&self.method));
        args.insert("path".to_string(), json!(&self.path));
        args.insert(
            "version".to_string(),
            json!(format!("HTTP/1.{}", self.version)),
        );

        // Process info
        args.insert("pid".to_string(), json!(self.source_event.pid));
        args.insert("tid".to_string(), json!(self.source_event.tid));
        args.insert("comm".to_string(), json!(self.source_event.comm_str()));
        
        // Add headers if present
        if !self.headers.is_empty() {
            args.insert("headers".to_string(), json!(&self.headers));
        }
        
        // Add body info if present
        if self.body_len > 0 {
            args.insert("body_length".to_string(), json!(self.body_len));
            
            // Try to parse as JSON first, fallback to full string
            if let Some(json_body) = self.json_body() {
                args.insert("body".to_string(), json_body);
            } else {
                let body_str = String::from_utf8_lossy(self.body()).to_string();
                if !body_str.is_empty() {
                    args.insert("body".to_string(), json!(body_str));
                }
            }
        }
        
        serde_json::Value::Object(args)
    }
}

impl ToChromeTraceEvent for ParsedRequest {
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let ts_us = ns_to_us(self.source_event.timestamp_ns);
        
        // Minimum duration: 10ms = 10,000 microseconds
        const MIN_DUR_US: u64 = 10_000;
        
        let event = ChromeTraceEvent::complete(
            format!("{} {}", self.method, self.path),
            "http.request",
            self.source_event.pid,
            self.source_event.tid as u64,
            ts_us,
            MIN_DUR_US,
        )
        .with_trace_args(self);
        
        vec![event]
    }
}

impl fmt::Debug for ParsedRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut debug = f.debug_struct("ParsedRequest");
        debug
            .field("method", &self.method)
            .field("path", &self.path)
            .field("version", &format!("HTTP/1.{}", self.version));
        
        // Format headers
        debug.field("headers", &self.headers);
        
        // Format body with smart detection
        let body = self.body();
        if !body.is_empty() {
            debug.field("body", &format_body(body));
        }
        
        // Add metadata from source_event
        debug
            .field("pid", &self.source_event.pid)
            .field("tid", &self.source_event.tid)
            .field("timestamp_ns", &self.source_event.timestamp_ns);
        
        debug.finish()
    }
}

/// Format body data for debug output
fn format_body(data: &[u8]) -> String {
    // Try JSON first
    if let Ok(json) = serde_json::from_slice::<serde_json::Value>(data) {
        let formatted = serde_json::to_string_pretty(&json).unwrap_or_default();
        format!("(json, {} bytes)\n{}", data.len(), formatted)
    } else if let Ok(text) = std::str::from_utf8(data) {
        // Text content
        let text = text.trim();
        format!("(text, {} bytes)\n{}", data.len(), text)
    } else {
        // Binary data - show as base64
        format!("(binary, {} bytes)\n{}", data.len(), base64::encode(data))
    }
}
