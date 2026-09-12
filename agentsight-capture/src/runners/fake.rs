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

/// Fake runner that generates simulated SSL events for tests and extension fixtures.
pub struct FakeRunner {
    analyzers: Vec<Box<dyn Analyzer>>,
    event_count: usize,
    delay_ms: u64,
}

impl FakeRunner {
    pub fn new() -> Self {
        Self {
            analyzers: Vec::new(),
            event_count: 5,
            delay_ms: 100,
        }
    }

    pub fn event_count(mut self, count: usize) -> Self {
        self.event_count = count;
        self
    }

    pub fn delay_ms(mut self, delay: u64) -> Self {
        self.delay_ms = delay;
        self
    }

    pub fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }

    fn generate_ssl_request(pair_id: usize) -> Event {
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;
        let pid = 12345 + pair_id as u32;
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
                "tid": pid,
                "time_s": current_time as f64 / 1000.0,
                "timestamp_ns": current_time * 1_000_000,
                "truncated": false,
                "uid": 1000
            }),
        )
    }

    fn generate_ssl_response(pair_id: usize) -> Event {
        let current_time = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
            + 500;
        let pid = 12345 + pair_id as u32;
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
                "tid": pid,
                "time_s": current_time as f64 / 1000.0,
                "timestamp_ns": current_time * 1_000_000,
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
        let event_stream = async_stream::stream! {
            for i in 0..event_count {
                yield Self::generate_ssl_request(i);
                sleep(Duration::from_millis(delay_ms / 4)).await;
                yield Self::generate_ssl_response(i);
                if i < event_count - 1 {
                    sleep(Duration::from_millis(delay_ms)).await;
                }
            }
        };
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
    use crate::analyzers::AnalyzerError;
    use futures::StreamExt;

    struct Mark;

    #[async_trait]
    impl Analyzer for Mark {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            Ok(Box::pin(stream.map(|mut event| {
                event.data["marked"] = json!(true);
                event
            })))
        }
    }

    #[tokio::test]
    async fn fake_runner_preserves_pair_shape() {
        let mut runner = FakeRunner::new().event_count(2).delay_ms(1);
        let events: Vec<_> = runner.run().await.unwrap().collect().await;
        assert_eq!(events.len(), 4);
        assert_eq!(events[0].data["function"], "WRITE/SEND");
        assert_eq!(events[1].data["function"], "READ/RECV");
        assert!(events.iter().all(|event| event.source == "ssl"));
    }

    #[tokio::test]
    async fn fake_runner_uses_stable_analyzer_trait() {
        let mut runner = FakeRunner::new().event_count(1).delay_ms(1).add_analyzer(Box::new(Mark));
        let events: Vec<_> = runner.run().await.unwrap().collect().await;
        assert!(events.iter().all(|event| event.data["marked"] == true));
    }
}
