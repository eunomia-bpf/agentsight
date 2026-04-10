use serde::{Deserialize, Serialize};
use std::fmt;
use std::rc::Rc;
use crate::chrome_trace::{ChromeTraceEvent, ns_to_us};
use crate::probes::sslsniff::SslEvent;

/// SSE Event - Standard Server-Sent Events message (legacy version with String data)
/// Follows the W3C EventSource specification: https://html.spec.whatwg.org/multipage/server-sent-events.html
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SSEEvent {
    /// Event ID (optional, used for reconnection)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<String>,
    /// Event type/name (default is "message")
    #[serde(skip_serializing_if = "Option::is_none")]
    pub event: Option<String>,
    /// Event data (can be multi-line, joined with \n)
    pub data: String,
    /// Retry hint in milliseconds (optional)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub retry: Option<u64>,
}

/// Parsed SSE Event - zero-copy version with SslEvent reference
/// Follows the W3C EventSource specification
#[derive(Clone)]
pub struct ParsedSseEvent {
    /// Event ID (optional, used for reconnection)
    pub id: Option<String>,
    /// Event type/name (default is "message")
    pub event: Option<String>,
    /// Retry hint in milliseconds (optional)
    pub retry: Option<u64>,
    /// Data offset in source_event.buf
    data_offset: usize,
    /// Data length
    data_len: usize,
    /// Original SslEvent (Rc to avoid cloning)
    source_event: Rc<SslEvent>,
}

impl ParsedSseEvent {
    /// Create a new ParsedSseEvent
    pub fn new(
        id: Option<String>,
        event: Option<String>,
        retry: Option<u64>,
        data_offset: usize,
        data_len: usize,
        source_event: Rc<SslEvent>,
    ) -> Self {
        Self {
            id,
            event,
            retry,
            data_offset,
            data_len,
            source_event,
        }
    }

    /// Parse data as JSON value
    pub fn json_body(&self) -> Option<serde_json::Value> {
        serde_json::from_slice::<serde_json::Value>(self.data()).ok()
    }

    /// Get data (zero-copy)
    pub fn data(&self) -> &[u8] {
        let buf_len = self.source_event.buf.len();
        let start = self.data_offset.min(buf_len);
        let end = (self.data_offset + self.data_len).min(buf_len);
        &self.source_event.buf[start..end]
    }

    pub fn body_str(&self) -> &str {
        std::str::from_utf8(self.data()).unwrap_or("")
    }

    /// Check if this is a completion marker
    pub fn is_done(&self) -> bool {
        let data = self.data();
        let text = String::from_utf8_lossy(data);
        let trimmed = text.trim();
        trimmed == "[DONE]" || trimmed == "[END]"
    }

    /// Get data length
    pub fn data_len(&self) -> usize {
        self.data_len
    }

    /// Get reference to source SslEvent
    pub fn source_event(&self) -> &SslEvent {
        &self.source_event
    }
}

impl fmt::Debug for ParsedSseEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut debug = f.debug_struct("ParsedSseEvent");
        
        if let Some(ref id) = self.id {
            debug.field("id", id);
        }
        if let Some(ref event) = self.event {
            debug.field("event", event);
        }
        if let Some(retry) = self.retry {
            debug.field("retry", &retry);
        }
        
        // Check if this is a done marker
        if self.is_done() {
            debug.field("done", &true);
        }
        
        // Format data with smart detection
        let data = self.data();
        if !data.is_empty() {
            debug.field("data", &format_sse_data(data));
        }
        
        // Add metadata
        debug
            .field("data_len", &self.data_len)
            .field("pid", &self.source_event.pid)
            .field("timestamp_ns", &self.source_event.timestamp_ns);
        
        debug.finish()
    }
}

/// Format SSE data for debug output
fn format_sse_data(data: &[u8]) -> String {
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

/// SSE Events container - holds one or more SSE events from a parse operation
#[derive(Debug, Clone)]
pub struct SSEEvents {
    /// Parsed SSE events
    pub events: Vec<SSEEvent>,
    /// Unconsumed buffer data (incomplete event at end)
    pub remaining: String,
    /// Total number of bytes consumed from input
    pub consumed_bytes: usize,
}

impl SSEEvents {
    /// Create a new empty SSEEvents container
    pub fn new() -> Self {
        SSEEvents {
            events: Vec::new(),
            remaining: String::new(),
            consumed_bytes: 0,
        }
    }

    /// Check if any events were parsed
    pub fn is_empty(&self) -> bool {
        self.events.is_empty()
    }

    /// Get the number of parsed events
    pub fn len(&self) -> usize {
        self.events.len()
    }

    /// Convert all SSE events to Chrome Trace Events
    pub fn to_chrome_trace_events(
        &self,
        pid: u32,
        tid: u64,
        base_timestamp_ns: u64,
    ) -> Vec<ChromeTraceEvent> {
        self.events
            .iter()
            .map(|event| event.to_chrome_trace_event(pid, tid, base_timestamp_ns))
            .collect()
    }

    /// Take the events, leaving the container empty
    pub fn take_events(&mut self) -> Vec<SSEEvent> {
        std::mem::take(&mut self.events)
    }

    /// Convert SSEEvents to a single Chrome Trace Event
    ///
    /// This aggregates all SSE events into one trace event with:
    /// - Event count in name
    /// - Combined data from all events
    /// - Total data size
    pub fn to_chrome_trace_event(
        &self,
        pid: u32,
        tid: u64,
        timestamp_ns: u64,
    ) -> Option<ChromeTraceEvent> {
        if self.events.is_empty() {
            return None;
        }

        // Build event name with count
        let name = format!("SSE Stream ({} events)", self.events.len());

        // Build args with aggregated information
        let mut args = serde_json::Map::new();
        args.insert("event_count".to_string(), serde_json::json!(self.events.len()));
        args.insert("consumed_bytes".to_string(), serde_json::json!(self.consumed_bytes));
        args.insert("remaining_bytes".to_string(), serde_json::json!(self.remaining.len()));

        // Aggregate data from all events
        let total_data_size: usize = self.events.iter().map(|e| e.data.len()).sum();
        args.insert("total_data_size".to_string(), serde_json::json!(total_data_size));

        // Combine all events' data (no truncation, no limit)
        let all_data: Vec<String> = self.events
            .iter()
            .map(|e| {
                format!("[{}] {}", e.event.as_deref().unwrap_or("message"), e.data)
            })
            .collect();

        if !all_data.is_empty() {
            args.insert("data".to_string(), serde_json::json!(all_data));
        }

        // Collect all event types
        let event_types: Vec<&str> = self.events
            .iter()
            .filter_map(|e| e.event.as_deref())
            .collect();
        if !event_types.is_empty() {
            args.insert("event_types".to_string(), serde_json::json!(event_types));
        }

        // Convert timestamp from nanoseconds to microseconds
        let ts = ns_to_us(timestamp_ns);

        Some(ChromeTraceEvent {
            name,
            cat: "sse_stream".to_string(),
            ph: "X".to_string(), // Complete event (represents a stream)
            ts,
            dur: Some(0), // Duration would need end timestamp
            pid,
            tid,
            args: Some(serde_json::Value::Object(args)),
            id: None,
            bp: None,
        })
    }
}

impl SSEEvent {
    /// Create a new SSEEvent with just data
    pub fn new(data: impl Into<String>) -> Self {
        SSEEvent {
            id: None,
            event: None,
            data: data.into(),
            retry: None,
        }
    }

    /// Check if this is a "ping" or keepalive event (data is empty and no other fields)
    pub fn is_keepalive(&self) -> bool {
        self.data.is_empty()
            && self.id.is_none()
            && self.event.is_none()
            && self.retry.is_none()
    }

    /// Format as SSE protocol string
    pub fn to_sse_string(&self) -> String {
        let mut result = String::new();

        if let Some(id) = &self.id {
            result.push_str(&format!("id:{}\n", id));
        }
        if let Some(event) = &self.event {
            result.push_str(&format!("event:{}\n", event));
        }
        if let Some(retry) = self.retry {
            result.push_str(&format!("retry:{}\n", retry));
        }

        // Data can be multi-line
        for line in self.data.lines() {
            result.push_str(&format!("data:{}\n", line));
        }

        result.push('\n'); // Empty line to terminate event
        result
    }

    /// Convert SSE Event to Chrome Trace Event format for Perfetto visualization
    ///
    /// # Arguments
    /// * `pid` - Process ID
    /// * `tid` - Thread ID
    /// * `timestamp_ns` - Event timestamp in nanoseconds
    ///
    /// # Returns
    /// A ChromeTraceEvent suitable for visualization in Perfetto
    pub fn to_chrome_trace_event(
        &self,
        pid: u32,
        tid: u64,
        timestamp_ns: u64,
    ) -> ChromeTraceEvent {
        // Build event name based on event type or data preview
        let name = match &self.event {
            Some(event_type) => format!("SSE {}", event_type),
            None => "SSE Message".to_string(),
        };

        // Build args with SSE information
        let mut args = serde_json::Map::new();

        // Add data (truncated for display if very long)
        let data_preview = if self.data.len() > 500 {
            format!("{}... ({} bytes total)", &self.data[..500], self.data.len())
        } else {
            self.data.clone()
        };
        args.insert("data".to_string(), serde_json::json!(data_preview));
        args.insert("data_length".to_string(), serde_json::json!(self.data.len()));

        if let Some(id) = &self.id {
            args.insert("id".to_string(), serde_json::json!(id));
        }
        if let Some(event) = &self.event {
            args.insert("event_type".to_string(), serde_json::json!(event));
        }
        if let Some(retry) = self.retry {
            args.insert("retry".to_string(), serde_json::json!(retry));
        }

        // Convert timestamp from nanoseconds to microseconds
        let ts = ns_to_us(timestamp_ns);

        ChromeTraceEvent {
            name,
            cat: "sse".to_string(),
            ph: "i".to_string(), // Instant event (SSE events are point-in-time)
            ts,
            dur: None,
            pid,
            tid,
            args: Some(serde_json::Value::Object(args)),
            id: None,
            bp: None,
        }
    }
}
