//! Aggregated HTTP Response types
//
//! This module defines the aggregated response structure that combines
//! parsed response data with aggregation metadata.

use crate::chrome_trace::{ChromeTraceEvent, ToChromeTraceEvent, TraceArgs, ns_to_us};
use crate::parser::http::ParsedResponse;
use crate::parser::sse::ParsedSseEvent;
use serde_json::json;

/// Aggregated HTTP Response with metadata
#[derive(Debug, Clone)]
pub struct AggregatedResponse {
    /// Parsed response data
    pub parsed: ParsedResponse,
    /// SSE events collected during streaming (if is_sse is true)
    pub sse_events: Vec<ParsedSseEvent>,
}

impl AggregatedResponse {
    /// Create from ParsedResponse
    pub fn from_parsed(parsed: ParsedResponse) -> Self {
        AggregatedResponse {
            parsed,
            sse_events: Vec::new(),
        }
    }

    pub fn body(&self) -> &[u8] {
        &self.parsed.body()
    }

    pub fn body_string(&self) -> String {
        let first = std::str::from_utf8(self.body()).unwrap_or("");
        let sse_body: String = self.sse_events
            .iter()
            .map(|event| event.body_str())
            .collect::<Vec<_>>()
            .join("");
        if first.is_empty() {
            sse_body
        } else if sse_body.is_empty() {
            first.to_string()
        } else {
            format!("{}{}", first, sse_body)
        }
    }

    /// Get JSON bodies from SSE events, aggregated into a Vec
    ///
    /// Parses each SSE event's payload as JSON and collects into a Vec,
    /// skipping events that are not valid JSON (e.g., [DONE] markers).
    pub fn json_body(&self) -> Vec<serde_json::Value> {
        self.sse_events
            .iter()
            .filter_map(|event| event.json_body())
            .collect()
    }

    /// Get start timestamp (first packet) in nanoseconds
    /// Derived from parsed.source_event.timestamp_ns
    pub fn start_timestamp_ns(&self) -> u64 {
        self.parsed.source_event.timestamp_ns
    }

    /// Get end timestamp (last packet) in nanoseconds
    /// For SSE: last event's timestamp; for regular response: same as start
    pub fn end_timestamp_ns(&self) -> u64 {
        self.sse_events
            .last()
            .map(|e| e.source_event().timestamp_ns)
            .unwrap_or_else(|| self.start_timestamp_ns())
    }

    /// Get duration in nanoseconds
    pub fn duration_ns(&self) -> u64 {
        self.end_timestamp_ns()
            .saturating_sub(self.start_timestamp_ns())
    }

    /// Get status code
    pub fn status_code(&self) -> u16 {
        self.parsed.status_code
    }

    /// Get reason phrase
    pub fn reason(&self) -> &str {
        &self.parsed.reason
    }

    /// Check if SSE response
    pub fn is_sse(&self) -> bool {
        self.parsed.is_sse()
    }

    /// Get process ID
    pub fn pid(&self) -> u32 {
        self.parsed.source_event.pid
    }

    /// Get thread ID
    pub fn tid(&self) -> u32 {
        self.parsed.source_event.tid
    }

    /// Get SSE event count
    pub fn sse_event_count(&self) -> usize {
        self.sse_events.len()
    }

    /// Add SSE event
    pub fn add_sse_event(&mut self, event: ParsedSseEvent) {
        self.sse_events.push(event);
    }

    /// Set SSE events (replace existing)
    pub fn set_sse_events(&mut self, events: Vec<ParsedSseEvent>) {
        self.sse_events = events;
    }

    /// Get combined SSE data
    pub fn combined_sse_data(&self) -> String {
        self.sse_events
            .iter()
            .map(|e| String::from_utf8_lossy(e.data()).to_string())
            .collect::<Vec<_>>()
            .join("")
    }
}

impl TraceArgs for AggregatedResponse {
    fn to_trace_args(&self) -> serde_json::Value {
        let mut args = serde_json::Map::new();

        args.insert("status_code".to_string(), json!(self.parsed.status_code));
        args.insert("reason".to_string(), json!(&self.parsed.reason));
        args.insert(
            "version".to_string(),
            json!(format!("HTTP/1.{}", self.parsed.version)),
        );

        // Add headers if present
        if !self.parsed.headers.is_empty() {
            args.insert("headers".to_string(), json!(&self.parsed.headers));
        }

        if self.parsed.is_sse() {
            args.insert("is_sse".to_string(), json!(true));
            if !self.sse_events.is_empty() {
                args.insert("sse_event_count".to_string(), json!(self.sse_events.len()));

                // Add SSE events data
                let events_data: Vec<_> = self
                    .sse_events
                    .iter()
                    .map(|e| {
                        let data_str = String::from_utf8_lossy(e.data()).to_string();
                        serde_json::json!({
                            "id": &e.id,
                            "event": &e.event,
                            "data": data_str,
                        })
                    })
                    .collect();
                args.insert("sse_events".to_string(), json!(events_data));
            }
        }

        if self.parsed.body_len > 0 && !self.parsed.is_sse() {
            args.insert("body_length".to_string(), json!(self.parsed.body_len));

            // Try to parse as JSON first, fallback to string
            if let Some(json_body) = self.parsed.json_body() {
                args.insert("body".to_string(), json_body);
            } else {
                let body = self.parsed.body();
                let body_str = String::from_utf8_lossy(body).to_string();
                if !body_str.is_empty() {
                    args.insert("body".to_string(), json!(body_str));
                }
            }
        }

        serde_json::Value::Object(args)
    }
}

impl ToChromeTraceEvent for AggregatedResponse {
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let ts_us = ns_to_us(self.start_timestamp_ns());
        let dur_us = ns_to_us(self.duration_ns());

        // Minimum duration: 10ms = 10,000 microseconds
        const MIN_DUR_US: u64 = 10_000;
        let dur_us = dur_us.max(MIN_DUR_US);

        let event = ChromeTraceEvent::complete(
            format!("{} {}", self.parsed.status_code, self.parsed.reason),
            "http.response",
            self.parsed.source_event.pid,
            self.parsed.source_event.tid as u64,
            ts_us,
            dur_us,
        )
        .with_trace_args(self);

        vec![event]
    }
}
