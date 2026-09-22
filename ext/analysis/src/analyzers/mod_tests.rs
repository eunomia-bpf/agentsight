use super::*;
use crate::runners::{EventStream, FakeRunner, Runner};
use crate::view::MaterializedView;
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::json;
use std::sync::{
    Arc,
    atomic::{AtomicUsize, Ordering},
};

fn materializer() -> MaterializingAnalyzer {
    MaterializingAnalyzer::with_view(MaterializedView::shared_bounded())
}

fn correlated_ssl_event(
    timestamp: u64,
    tid: u64,
    function: &str,
    data: String,
) -> crate::event::Event {
    crate::event::Event::new_with_timestamp(
        timestamp,
        "ssl".to_string(),
        4321,
        "node".to_string(),
        json!({
            "timestamp_ns": timestamp,
            "tid": tid,
            "function": function,
            "transport_handle": "0x1234",
            "process_start_ns": 987654,
            "tls_library": "openssl",
            "data": data,
        }),
    )
}

#[tokio::test]
async fn new_capture_sse_reaches_http_parser_before_sse_aggregation() {
    let request_body = "{}";
    let request = correlated_ssl_event(
        1_000,
        10,
        "WRITE/SEND",
        format!(
            "POST /v1/chat/completions HTTP/1.1\r\nHost: api.example.test\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{request_body}",
            request_body.len()
        ),
    );
    let response_body = concat!(
        "data: {\"id\":\"chatcmpl-chain\",\"choices\":[{\"index\":0,\"delta\":{\"content\":\"hello\"},\"finish_reason\":null}]}\n\n",
        "data: {\"id\":\"chatcmpl-chain\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\n",
        "data: [DONE]\n\n",
    );
    let response = correlated_ssl_event(
        2_000,
        11,
        "READ/RECV",
        format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\n\r\n{response_body}",
            response_body.len()
        ),
    );

    let stream: EventStream = Box::pin(futures::stream::iter(vec![request, response]));
    let mut legacy_sse = SSEProcessor::new_with_timeout(5_000).defer_transport_to_http();
    let stream = legacy_sse.process(stream).await.unwrap();
    let mut http = HTTPParser::new().disable_raw_data();
    let stream = http.process(stream).await.unwrap();
    let mut decompressor = HTTPDecompressor::new();
    let stream = decompressor.process(stream).await.unwrap();
    let mut correlated_sse = SSEProcessor::new_with_timeout(5_000);
    let output: Vec<_> = correlated_sse
        .process(stream)
        .await
        .unwrap()
        .collect()
        .await;

    let merged = output
        .iter()
        .find(|event| event.source == "sse_processor")
        .expect("the post-HTTP SSE processor should emit a merged response");
    assert_eq!(merged.data["correlation_version"], 2);
    assert_eq!(merged.data["correlation_method"], "h1_connection_fifo");
    assert_eq!(merged.data["correlation_status"], "exact");
    assert_eq!(merged.data["text_content"], "hello");
    assert!(
        merged.data["http_exchange_id"]
            .as_str()
            .is_some_and(|value| value.contains("-h1-1"))
    );
}

#[tokio::test]
async fn test_complex_analyzer_chain_composition() {
    struct FilterAnalyzer;

    #[async_trait]
    impl Analyzer for FilterAnalyzer {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            Ok(Box::pin(stream.filter(|event| {
                futures::future::ready(event.source == "ssl")
            })))
        }
    }

    let mut runner = FakeRunner::new()
        .event_count(5)
        .delay_ms(10)
        .add_analyzer(Box::new(FilterAnalyzer))
        .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000)))
        .add_analyzer(Box::new(HTTPParser::new().disable_raw_data()))
        .add_analyzer(Box::new(materializer()));

    let stream = runner.run().await.unwrap();
    let events: Vec<_> = stream.collect().await;

    assert!(!events.is_empty());
    let non_ssl_events = events
        .iter()
        .filter(|e| e.source != "ssl" && e.source != "sse_processor" && e.source != "http_parser")
        .count();
    assert_eq!(non_ssl_events, 0);
}

#[tokio::test]
async fn test_analyzer_chain_error_resilience() {
    struct ErrorSimulatorAnalyzer {
        error_on_event_number: usize,
    }

    #[async_trait]
    impl Analyzer for ErrorSimulatorAnalyzer {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            let error_event = self.error_on_event_number;
            let counter = Arc::new(AtomicUsize::new(0));

            let processed_stream = stream.map(move |event| {
                let count = counter.fetch_add(1, Ordering::SeqCst) + 1;
                if count == error_event {
                    let mut error_event = event;
                    if let Some(data) = error_event.data.as_object_mut() {
                        data.insert("analyzer_error".to_string(), json!("Simulated error"));
                    }
                    error_event
                } else {
                    event
                }
            });

            Ok(Box::pin(processed_stream))
        }
    }

    let mut runner = FakeRunner::new()
        .event_count(5)
        .delay_ms(10)
        .add_analyzer(Box::new(ErrorSimulatorAnalyzer {
            error_on_event_number: 3,
        }))
        .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000)));

    let stream = runner.run().await.unwrap();
    let events: Vec<_> = stream.collect().await;

    assert!(events.len() >= 10);
    let error_events = events
        .iter()
        .filter(|e| e.data.get("analyzer_error").is_some())
        .count();
    assert!(error_events > 0);
}
