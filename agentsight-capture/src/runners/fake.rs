// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::common::AnalyzerProcessor;
use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use async_trait::async_trait;
use serde_json::json;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::time::{Duration, sleep};

/// Fake runner that generates simulated SSL events for testing
pub struct FakeRunner {
    analyzers: Vec<Box<dyn Analyzer>>,
    event_count: usize,
    delay_ms: u64,
}

impl FakeRunner {
    /// Create a new FakeRunner
    pub fn new() -> Self {
        Self {
            analyzers: Vec::new(),
            event_count: 5, // Default to 5 pairs (10 events total)
            delay_ms: 100,  // 100ms delay between events
        }
    }

    /// Set custom event count (this will generate 2x events - request + response pairs)
    pub fn event_count(mut self, count: usize) -> Self {
        self.event_count = count;
        self
    }

    /// Set delay between events in milliseconds  
    pub fn delay_ms(mut self, delay: u64) -> Self {
        self.delay_ms = delay;
        self
    }

    /// Add an analyzer to the chain
    pub fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }

    /// Generate a realistic SSL request event
    fn generate_ssl_request(pair_id: usize) -> Event {
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64; // Use milliseconds for HTTP analyzer compatibility

        let pid = 12345 + pair_id as u32;
        let tid = pid;

        // Generate realistic HTTP request data
        let request_data = format!(
            "POST /v1/chat/completions HTTP/1.1\r\n\
            Host: api.openai.com\r\n\
            Accept-Encoding: gzip, deflate\r\n\
            Connection: keep-alive\r\n\
            Accept: application/json\r\n\
            Content-Type: application/json\r\n\
            User-Agent: OpenAI/Python 1.59.6\r\n\
            Authorization: Bearer sk-test-key\r\n\
            Content-Length: 150\r\n\r\n\
            {{\"model\":\"gpt-4\",\"messages\":[{{\"role\":\"user\",\"content\":\"Test request {}\"}}]}}",
            pair_id
        );

        Event::new_with_timestamp(
            current_time,
            "ssl".to_string(),
            pid,
            "python".to_string(),
            json!({
                "comm": "python",
                "data": request_data,
                "function": "WRITE/SEND",
                "is_handshake": false,
                "latency_ms": 0.214,
                "len": request_data.len(),
                "pid": pid,
                "tid": tid,
                "time_s": current_time as f64 / 1000.0, // Convert back to seconds for this field
                "timestamp_ns": current_time * 1_000_000, // Convert to nanoseconds
                "truncated": false,
                "uid": 1000
            }),
        )
    }

    /// Generate a realistic SSL response event  
    fn generate_ssl_response(pair_id: usize) -> Event {
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
            + 500; // Response comes 500ms after request

        let pid = 12345 + pair_id as u32;
        let tid = pid;

        // Generate realistic HTTP response data
        let response_data = format!(
            "HTTP/1.1 200 OK\r\n\
            Content-Type: application/json\r\n\
            Content-Length: 120\r\n\
            Date: Fri, 11 Jul 2025 19:01:04 GMT\r\n\
            Connection: keep-alive\r\n\r\n\
            {{\"id\":\"chatcmpl-test{}\",\"object\":\"chat.completion\",\"choices\":[{{\"message\":{{\"content\":\"Test response {}\"}}}}]}}",
            pair_id, pair_id
        );

        Event::new_with_timestamp(
            current_time,
            "ssl".to_string(),
            pid,
            "python".to_string(),
            json!({
                "comm": "python",
                "data": response_data,
                "function": "READ/RECV",
                "is_handshake": false,
                "latency_ms": 45.2,
                "len": response_data.len(),
                "pid": pid,
                "tid": tid,
                "time_s": current_time as f64 / 1000.0, // Convert back to seconds for this field
                "timestamp_ns": current_time * 1_000_000, // Convert to nanoseconds
                "truncated": false,
                "uid": 1000
            }),
        )
    }
}

impl Default for FakeRunner {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl Runner for FakeRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let event_count = self.event_count;
        let delay_ms = self.delay_ms;

        // Create event stream using a simple generator
        let event_stream = async_stream::stream! {
            for i in 0..event_count {
                // Generate and yield request
                let request_event = Self::generate_ssl_request(i);
                yield request_event;

                // Small delay between request and response
                sleep(Duration::from_millis(delay_ms / 4)).await;

                // Generate and yield response
                let response_event = Self::generate_ssl_response(i);
                yield response_event;

                // Longer delay between pairs (except for the last pair)
                if i < event_count - 1 {
                    sleep(Duration::from_millis(delay_ms)).await;
                }
            }

        };

        // Process through analyzer chain
        AnalyzerProcessor::process_through_analyzers(Box::pin(event_stream), &mut self.analyzers)
            .await
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self
    where
        Self: Sized,
    {
        self.analyzers.push(analyzer);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzers::{HTTPParser, MaterializingAnalyzer, SSEProcessor};
    use crate::view::MaterializedView;
    use futures::stream::StreamExt;

    fn materializer() -> MaterializingAnalyzer {
        MaterializingAnalyzer::with_view(MaterializedView::shared_bounded())
    }

    #[tokio::test]
    async fn test_fake_runner_basic() {
        let mut runner = FakeRunner::new().event_count(2).delay_ms(10); // Fast for testing

        let stream = runner.run().await.unwrap();
        let events: Vec<_> = stream.collect().await;

        // Should generate 2 pairs = 4 events total
        assert_eq!(events.len(), 4);

        // Check that we have alternating request/response events
        assert_eq!(events[0].data["function"].as_str().unwrap(), "WRITE/SEND"); // Request
        assert_eq!(events[1].data["function"].as_str().unwrap(), "READ/RECV"); // Response
        assert_eq!(events[2].data["function"].as_str().unwrap(), "WRITE/SEND"); // Request
        assert_eq!(events[3].data["function"].as_str().unwrap(), "READ/RECV"); // Response

        // All events should have ssl source
        for event in &events {
            assert_eq!(event.source, "ssl");
        }
    }

    #[tokio::test]
    async fn test_fake_runner_with_chunk_merger() {
        let mut runner = FakeRunner::new()
            .event_count(2)
            .delay_ms(10)
            .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000))); // 5 second timeout

        let stream = runner.run().await.unwrap();
        let events: Vec<_> = stream.collect().await;

        let ssl_events = events.iter().filter(|e| e.source == "ssl").count();
        let chunk_events = events.iter().filter(|e| e.source == "chunk_merger").count();

        // Should have exactly 4 SSL events (2 pairs = 4 events)
        assert_eq!(
            ssl_events, 4,
            "Should have exactly 4 SSL events (2 request/response pairs)"
        );

        // Since fake events don't contain chunked data, ChunkMerger just passes them through
        // So we expect 0 chunk_merger events and all original SSL events preserved
        assert_eq!(
            chunk_events, 0,
            "Should have no chunk_merger events since fake data isn't chunked"
        );
        assert_eq!(events.len(), 4, "All original events should be preserved");

        // Verify all events are SSL events
        for event in &events {
            assert_eq!(event.source, "ssl", "All events should have ssl source");
        }
    }

    #[tokio::test]
    async fn test_fake_runner_with_materializer() {
        let mut runner = FakeRunner::new()
            .event_count(2)
            .delay_ms(10)
            .add_analyzer(Box::new(HTTPParser::new().disable_raw_data()))
            .add_analyzer(Box::new(materializer()));

        let stream = runner.run().await.unwrap();
        let events: Vec<_> = stream.collect().await;

        assert!(
            events.len() >= 4,
            "Should preserve the original request/response events"
        );
    }

    #[tokio::test]
    async fn test_analyzer_chain_empty_stream() {
        let mut runner = FakeRunner::new()
            .event_count(0)
            .delay_ms(10)
            .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000)));

        let stream = runner.run().await.unwrap();
        let events: Vec<_> = stream.collect().await;
        assert_eq!(events.len(), 0);
    }

    #[tokio::test]
    async fn test_full_analyzer_chain() {
        let mut runner = FakeRunner::new()
            .event_count(3)
            .delay_ms(10)
            .add_analyzer(Box::new(SSEProcessor::new_with_timeout(10000)))
            .add_analyzer(Box::new(HTTPParser::new().disable_raw_data()))
            .add_analyzer(Box::new(materializer()));

        let stream = runner.run().await.unwrap();
        let events: Vec<_> = stream.collect().await;

        let http_events = events
            .iter()
            .filter(|event| event.source == "http_parser")
            .count();
        assert!(http_events >= 6, "Should have parsed HTTP events");

        for event in events.iter().filter(|e| e.source == "http_parser") {
            assert!(event.data.get("method").is_some() || event.data.get("status_code").is_some(),);
            assert!(event.pid > 0);
        }
    }

    #[test]
    fn test_ssl_event_structure() {
        let request = FakeRunner::generate_ssl_request(0);
        let response = FakeRunner::generate_ssl_response(0);

        // Verify request structure
        assert_eq!(request.source, "ssl");
        assert_eq!(request.data["function"].as_str().unwrap(), "WRITE/SEND");
        assert_eq!(request.data["pid"].as_u64().unwrap(), 12345);
        assert!(
            request.data["data"]
                .as_str()
                .unwrap()
                .contains("POST /v1/chat/completions")
        );

        // Verify response structure
        assert_eq!(response.source, "ssl");
        assert_eq!(response.data["function"].as_str().unwrap(), "READ/RECV");
        assert_eq!(response.data["pid"].as_u64().unwrap(), 12345);
        assert!(
            response.data["data"]
                .as_str()
                .unwrap()
                .contains("HTTP/1.1 200 OK")
        );

        // Verify timing
        assert!(
            response.timestamp > request.timestamp,
            "Response should come after request"
        );
    }
}
