// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

#[cfg(test)]
#[allow(clippy::module_inception)]
mod sse_processor_tests {
    use super::super::Analyzer;
    use super::super::sse_processor::SSEProcessor;
    use crate::framework::core::Event;
    use crate::framework::runners::EventStream;
    use crate::framework::storage::{GenericProjector, SqliteStore};
    use futures::stream;
    use futures::stream::StreamExt;
    use serde_json::json;

    #[tokio::test]
    async fn test_is_sse_data() {
        assert!(SSEProcessor::is_sse_data(
            "event: content_block_delta\ndata: {\"type\":\"content_block_delta\"}\r\n0\r\n\r\n"
        ));
        assert!(SSEProcessor::is_sse_data(
            "event: message_start\ndata: {\"message\":{\"id\":\"123\"}}\r\n0\r\n\r\n"
        ));
        assert!(SSEProcessor::is_sse_data(
            "Transfer-Encoding: chunked\r\nevent: content_block_delta\r\ndata: {\"type\":\"content_block_delta\"}\r\n0\r\n\r\n"
        ));
        assert!(SSEProcessor::is_sse_data(
            "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\n"
        ));
        assert!(SSEProcessor::is_sse_data(
            "Transfer-Encoding: chunked\r\n\r\n1a\r\nevent: message_start\r\n"
        ));
        assert!(SSEProcessor::is_sse_data(
            "data: {\"message\": \"hello\"}\r\n\r\n"
        ));
        assert!(!SSEProcessor::is_sse_data("regular text"));
        assert!(!SSEProcessor::is_sse_data(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"data\":\"value\"}"
        ));
    }

    #[tokio::test]
    async fn test_gemini_usage_metadata_completes_sse_stream() {
        let mut processor = SSEProcessor::new();
        let test_data = "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata: {\"usageMetadata\":{\"promptTokenCount\":11,\"candidatesTokenCount\":4,\"totalTokenCount\":15}}\r\n\r\n";
        let test_event = Event::new_with_timestamp(
            2,
            "ssl".to_string(),
            1234,
            "node".to_string(),
            json!({
                "data": test_data,
                "function": "READ/RECV",
                "pid": 1234,
                "tid": 99,
                "timestamp_ns": 2
            }),
        );

        let input_stream: EventStream = Box::pin(stream::iter(vec![test_event]));
        let output_stream = processor.process(input_stream).await.unwrap();
        let collected: Vec<_> = output_stream.collect().await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "sse_processor");

        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1internal:streamGenerateContent?alt=sse",
                "headers": { "host": "cloudcode-pa.googleapis.com" },
                "body": "{\"model\":\"gemini-2.5-pro\"}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&collected[0], &mut projector).unwrap();

        let total: i64 = store
            .connection()
            .query_row(
                "SELECT COALESCE(SUM(total_tokens), 0)
                 FROM token_usage WHERE source = 'response_usage'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        assert_eq!(total, 15);
    }

    #[tokio::test]
    async fn test_gemini_usage_metadata_fragment_completes_sse_stream() {
        let mut processor = SSEProcessor::new();
        let test_data = r#""text": ""}]},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":11,"candidatesTokenCount":4,"totalTokenCount":15},"modelVersion":"gemini-3-flash-preview","responseId":"abc"}"#;
        let test_event = Event::new_with_timestamp(
            2,
            "ssl".to_string(),
            1234,
            "node".to_string(),
            json!({
                "data": test_data,
                "function": "READ/RECV",
                "pid": 1234,
                "tid": 99,
                "timestamp_ns": 2
            }),
        );

        let input_stream: EventStream = Box::pin(stream::iter(vec![test_event]));
        let output_stream = processor.process(input_stream).await.unwrap();
        let collected: Vec<_> = output_stream.collect().await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "sse_processor");
        assert_eq!(
            collected[0].data["sse_events"][0]["parsed_data"]["modelVersion"],
            "gemini-3-flash-preview"
        );
    }

    #[tokio::test]
    async fn test_sse_processor_ignores_non_ssl_events() {
        let mut processor = SSEProcessor::new();

        let test_event = Event::new(
            "process".to_string(),
            1234,
            "test".to_string(),
            json!({
                "comm": "test",
                "data": "some data",
                "pid": 1234
            }),
        );

        let events = vec![test_event.clone()];
        let input_stream: EventStream = Box::pin(stream::iter(events));
        let output_stream = processor.process(input_stream).await.unwrap();

        let collected: Vec<_> = output_stream.collect().await;

        // Should pass through non-SSL events unchanged
        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "process");
    }

    #[tokio::test]
    async fn test_sse_processor_ignores_non_sse_ssl_events() {
        let mut processor = SSEProcessor::new();

        let test_event = Event::new(
            "ssl".to_string(),
            1234,
            "test".to_string(),
            json!({
                "comm": "test",
                "data": "regular HTTP data without SSE",
                "function": "READ/RECV",
                "pid": 1234
            }),
        );

        let events = vec![test_event.clone()];
        let input_stream: EventStream = Box::pin(stream::iter(events));
        let output_stream = processor.process(input_stream).await.unwrap();

        let collected: Vec<_> = output_stream.collect().await;

        // Should pass through non-SSE SSL events unchanged
        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "ssl");
    }

    #[tokio::test]
    async fn test_enhanced_chunked_content_cleaning() {
        // Test enhanced chunked content cleaning like ssl_log_analyzer.py

        let chunked_data = "1a\r\nevent: content_block_delta\r\n0\r\n\r\n";
        let cleaned = SSEProcessor::clean_chunked_content(chunked_data);
        assert!(cleaned.contains("event: content_block_delta"));
        assert!(!cleaned.contains("1a")); // Chunk size should be removed

        let multi_chunk_data =
            "10\r\nevent: message_start\r\n15\r\ndata: {\"id\": \"123\"}\r\n0\r\n\r\n";
        let cleaned_multi = SSEProcessor::clean_chunked_content(multi_chunk_data);
        assert!(cleaned_multi.contains("event: message_start"));
        assert!(cleaned_multi.contains("data: {\"id\": \"123\"}"));
        assert!(!cleaned_multi.contains("10")); // Chunk sizes should be removed
        assert!(!cleaned_multi.contains("15"));
    }
}
