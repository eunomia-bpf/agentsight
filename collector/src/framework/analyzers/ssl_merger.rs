use super::{Analyzer, AnalyzerError};
use crate::framework::runners::EventStream;
use crate::framework::core::Event;
use async_trait::async_trait;
use futures::stream::StreamExt;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// SSL Merger Analyzer that accumulates SSL READ/RECV events from the same thread
/// until a complete HTTP message is received, then emits a single merged event.
///
/// This is necessary because HTTP responses (especially chunked ones) often span
/// multiple SSL_read() calls. The HTTP parser needs the complete response to
/// properly parse headers and extract the full body.
pub struct SSLMerger {
    /// Buffer to accumulate SSL data by thread ID
    buffers: Arc<Mutex<HashMap<u64, SSLBuffer>>>,
    /// Timeout in milliseconds to flush incomplete buffers
    timeout_ms: u64,
}

/// Buffer for accumulating SSL data from a single thread
struct SSLBuffer {
    /// Accumulated data from multiple READ events
    accumulated_data: String,
    /// Timestamp of the first event in this buffer
    first_timestamp: u64,
    /// Timestamp of the last event added to this buffer
    last_timestamp: u64,
    /// The original event (used for metadata)
    original_event: Option<Event>,
    /// Number of events merged into this buffer
    event_count: usize,
}

impl SSLMerger {
    /// Create a new SSLMerger with default timeout (5 seconds)
    pub fn new() -> Self {
        Self::with_timeout(5000)
    }

    /// Create a new SSLMerger with custom timeout
    pub fn with_timeout(timeout_ms: u64) -> Self {
        SSLMerger {
            buffers: Arc::new(Mutex::new(HashMap::new())),
            timeout_ms,
        }
    }

    /// Check if accumulated data contains a complete HTTP message
    fn is_complete_http_message(data: &str) -> bool {
        // Check if it's an HTTP message
        let is_http = data.starts_with("HTTP/") ||
                      data.contains(" HTTP/1.") ||
                      data.contains("GET ") || data.contains("POST ") ||
                      data.contains("PUT ") || data.contains("DELETE ");

        if !is_http {
            return false;
        }

        // Find the header/body separator
        let header_end = data.find("\r\n\r\n");
        if header_end.is_none() {
            return false; // Headers not complete yet
        }

        let header_end = header_end.unwrap();
        let headers = &data[..header_end];
        let body = &data[header_end + 4..];

        // Check if it's chunked encoding
        let is_chunked = headers.to_lowercase().contains("transfer-encoding: chunked");

        if is_chunked {
            // For chunked encoding, check if we have the terminating chunk (0\r\n\r\n)
            return body.ends_with("0\r\n\r\n") || body.contains("\r\n0\r\n\r\n");
        } else {
            // For non-chunked, check Content-Length
            if let Some(cl_start) = headers.to_lowercase().find("content-length:") {
                let cl_line = &headers[cl_start..];
                if let Some(cl_end) = cl_line.find("\r\n") {
                    let cl_value = &cl_line[15..cl_end].trim();
                    if let Ok(content_length) = cl_value.parse::<usize>() {
                        return body.len() >= content_length;
                    }
                }
            }

            // If no Content-Length and not chunked, consider it complete
            // (some responses like 204 No Content have no body)
            true
        }
    }

    /// Create a merged event from accumulated buffer
    fn create_merged_event(buffer: &SSLBuffer) -> Option<Event> {
        let original = buffer.original_event.as_ref()?;

        let mut merged_event = original.clone();

        // Update the data field with accumulated content
        if let Some(data) = merged_event.data.as_object_mut() {
            data.insert("data".to_string(), serde_json::json!(buffer.accumulated_data));
            data.insert("len".to_string(), serde_json::json!(buffer.accumulated_data.len()));
            data.insert("merged_events".to_string(), serde_json::json!(buffer.event_count));
            data.insert("first_timestamp_ns".to_string(), serde_json::json!(buffer.first_timestamp));
        }

        // Use the timestamp from the last event
        merged_event.timestamp = buffer.last_timestamp;

        Some(merged_event)
    }
}

#[async_trait]
impl Analyzer for SSLMerger {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let buffers = Arc::clone(&self.buffers);
        let timeout_ms = self.timeout_ms;

        let processed_stream = stream.filter_map(move |event| {
            let buffers = Arc::clone(&buffers);

            async move {
                // Only process SSL READ/RECV events
                if event.source != "ssl" {
                    return Some(event);
                }

                let function = event.data.get("function")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");

                if function != "READ/RECV" {
                    return Some(event); // Pass through non-READ events
                }

                let tid = event.data.get("tid")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0);

                let data = event.data.get("data")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");

                let timestamp_ns = event.data.get("timestamp_ns")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(event.timestamp);

                let mut buffers = buffers.lock().unwrap();

                // Get or create buffer for this thread
                let buffer = buffers.entry(tid).or_insert_with(|| SSLBuffer {
                    accumulated_data: String::new(),
                    first_timestamp: timestamp_ns,
                    last_timestamp: timestamp_ns,
                    original_event: Some(event.clone()),
                    event_count: 0,
                });

                // Append data to buffer
                buffer.accumulated_data.push_str(data);
                buffer.last_timestamp = timestamp_ns;
                buffer.event_count += 1;

                // Check if we have a complete HTTP message
                if Self::is_complete_http_message(&buffer.accumulated_data) {
                    // Create merged event and clear buffer
                    let merged_event = Self::create_merged_event(buffer);
                    buffers.remove(&tid);
                    return merged_event;
                }

                // Check for timeout
                let time_diff = if timestamp_ns > buffer.first_timestamp {
                    (timestamp_ns - buffer.first_timestamp) / 1_000_000 // Convert ns to ms
                } else {
                    0
                };

                if time_diff > timeout_ms {
                    // Timeout reached, flush incomplete buffer
                    let merged_event = Self::create_merged_event(buffer);
                    buffers.remove(&tid);
                    return merged_event;
                }

                // Not complete yet, don't emit anything
                None
            }
        });

        Ok(Box::pin(processed_stream))
    }

    fn name(&self) -> &str {
        "SSLMerger"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_complete_http_message_chunked() {
        // Complete chunked HTTP response
        let complete = "HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1a\r\nHello World\r\n0\r\n\r\n";
        assert!(SSLMerger::is_complete_http_message(complete));

        // Incomplete chunked response (missing end marker)
        let incomplete = "HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n1a\r\nHello World\r\n";
        assert!(!SSLMerger::is_complete_http_message(incomplete));
    }

    #[test]
    fn test_is_complete_http_message_content_length() {
        // Complete response with Content-Length
        let complete = "HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nHello";
        assert!(SSLMerger::is_complete_http_message(complete));

        // Incomplete response
        let incomplete = "HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nHello";
        assert!(!SSLMerger::is_complete_http_message(incomplete));
    }

    #[test]
    fn test_is_complete_http_message_no_body() {
        // Response with no body (e.g., 204 No Content)
        let no_body = "HTTP/1.1 204 No Content\r\n\r\n";
        assert!(SSLMerger::is_complete_http_message(no_body));
    }
}
