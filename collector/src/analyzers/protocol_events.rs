// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// SSE Processor Event - represents a complete SSE interaction with timing information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SSEProcessorEvent {
    pub connection_id: String,
    pub message_id: Option<String>,
    pub start_time: u64,
    pub end_time: u64,
    pub duration_ns: u64,
    pub original_source: String,
    pub function: String,
    pub tid: u64,
    pub json_content: String,
    pub text_content: String,
    pub total_size: usize,
    pub event_count: usize,
    pub has_message_start: bool,
    pub sse_events: Vec<Value>,
}

impl SSEProcessorEvent {
    pub fn to_event(&self, original_event: &Event) -> Event {
        // Serialize struct to JSON Value to ensure exact match with struct fields
        let data = serde_json::to_value(self).unwrap_or_else(|_| serde_json::json!({}));

        // Use merged end_time if events were merged, otherwise use original timestamp
        let timestamp = if self.event_count > 1 {
            self.end_time
        } else {
            original_event.timestamp
        };

        Event::new_with_timestamp(
            timestamp,
            "sse_processor".to_string(),
            original_event.pid,
            original_event.comm.clone(),
            data,
        )
    }
}

/// HTTP Event - represents a parsed HTTP request or response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HTTPEvent {
    pub tid: u64,
    pub message_type: String,
    pub first_line: String,
    pub method: Option<String>,
    pub path: Option<String>,
    pub protocol: Option<String>,
    pub status_code: Option<u16>,
    pub status_text: Option<String>,
    pub headers: HashMap<String, String>,
    pub body: Option<String>,
    pub total_size: usize,
    pub has_body: bool,
    pub is_chunked: bool,
    pub content_length: Option<usize>,
    pub original_source: String,
    pub raw_data: Option<String>,
}

impl HTTPEvent {
    pub fn to_event(&self, original_event: &Event) -> Event {
        // Serialize struct to JSON Value to ensure exact match with struct fields
        let data = serde_json::to_value(self).unwrap_or_else(|_| serde_json::json!({}));

        Event::new_with_timestamp(
            original_event.timestamp, // Use original event timestamp directly
            "http_parser".to_string(),
            original_event.pid,
            original_event.comm.clone(),
            data,
        )
    }
}
