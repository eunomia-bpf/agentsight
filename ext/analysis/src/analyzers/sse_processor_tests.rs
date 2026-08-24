// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

#[cfg(test)]
#[allow(clippy::module_inception)]
mod sse_processor_tests {
    use super::super::Analyzer;
    use super::super::sse_processor::SSEProcessor;
    use crate::event::Event;
    use crate::runners::EventStream;
    use crate::view::MaterializedView;
    use futures::stream;
    use futures::stream::StreamExt;
    use serde_json::json;

    fn ssl_sse_chunk(timestamp: u64, data: &str) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            1234,
            "node".to_string(),
            json!({
                "data": data,
                "function": "READ/RECV",
                "pid": 1234,
                "tid": 99,
                "timestamp_ns": timestamp
            }),
        )
    }

    fn http_sse_response(timestamp: u64, body: &str) -> Event {
        let body = if body.contains("\n\n") || body.contains("\r\n\r\n") {
            body.to_string()
        } else {
            format!("{body}\n\n")
        };
        Event::new_with_timestamp(
            timestamp,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "response",
                "status_code": 200,
                "headers": { "content-type": "text/event-stream", "host": "api.example.test" },
                "path": "/v1/chat/completions",
                "body": body
            }),
        )
    }

    async fn process_chunks(chunks: &[&str]) -> Vec<Event> {
        let mut processor = SSEProcessor::new();
        let events = chunks
            .iter()
            .enumerate()
            .map(|(idx, data)| {
                let data = if data.contains("\n\n") || data.contains("\r\n\r\n") {
                    (*data).to_string()
                } else {
                    format!("{data}\n\n")
                };
                ssl_sse_chunk((idx + 2) as u64, &data)
            })
            .collect::<Vec<_>>();
        let input_stream: EventStream = Box::pin(stream::iter(events));
        processor
            .process(input_stream)
            .await
            .unwrap()
            .collect()
            .await
    }

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

        let mut view = MaterializedView::new();
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
        view.ingest_event(&req).unwrap();
        view.ingest_event(&collected[0]).unwrap();

        let total = view
            .export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 })
            .token_summary
            .into_iter()
            .map(|row| row.total_tokens)
            .sum::<i64>();
        assert_eq!(total, 15);
    }

    #[tokio::test]
    async fn test_openai_compatible_usage_completes_sse_stream() {
        let mut processor = SSEProcessor::new();
        let chunks = [
            "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\ndata: {\"message\":{\"usage\":{\"input_tokens\":5,\"cache_read_input_tokens\":2}}}\r\n\r\n",
            "data: {\"usage\":{\"output_tokens\":3}}\r\n\r\n",
            "data: [DONE]\r\n\r\n",
        ];
        let input_stream: EventStream = Box::pin(stream::iter(chunks.into_iter().enumerate().map(
            |(idx, data)| {
                Event::new_with_timestamp(
                    (idx + 2) as u64,
                    "ssl".to_string(),
                    1234,
                    "node".to_string(),
                    json!({
                        "data": data,
                        "function": "READ/RECV",
                        "pid": 1234,
                        "tid": 99,
                        "timestamp_ns": idx + 2
                    }),
                )
            },
        )));
        let output_stream = processor.process(input_stream).await.unwrap();
        let collected: Vec<_> = output_stream.collect().await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "sse_processor");

        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.example.test" },
                "body": "{\"model\":\"example-model\"}"
            }),
        );
        let empty_req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.example.test" }
            }),
        );
        view.ingest_event(&req).unwrap();
        view.ingest_event(&empty_req).unwrap();
        view.ingest_event(&collected[0]).unwrap();

        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.llm_calls, 1);
        assert_eq!(snapshot.summary.token_usage_rows, 1);
        assert_eq!(snapshot.summary.input_tokens, 5);
        assert_eq!(snapshot.summary.output_tokens, 3);
        assert_eq!(snapshot.summary.total_tokens, 10);
        assert_eq!(snapshot.token_summary[0].group, "example-model");
    }

    #[tokio::test]
    async fn test_openai_stream_without_usage_emits_accumulated_response() {
        let chunks = [
            r#"data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}"#,
            r#"data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}"#,
            r#"data: {"id":"chatcmpl-1","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}"#,
            "data: [DONE]\n\n",
        ];
        let collected = process_chunks(&chunks).await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "sse_processor");
        assert_eq!(collected[0].data["message_id"], "chatcmpl-1");
        assert_eq!(collected[0].data["text_content"], "Hello");
        assert!(
            collected[0].data["connection_id"]
                .as_str()
                .unwrap()
                .ends_with(":chatcmpl-1")
        );

        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.example.test" },
                "body": "{\"model\":\"openai-mock\"}"
            }),
        );
        view.ingest_event(&req).unwrap();
        view.ingest_event(&collected[0]).unwrap();
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.llm_calls, 1);
        assert_eq!(snapshot.summary.token_usage_rows, 0);
        let calls = view.llm_call_rows(10);
        assert_eq!(calls[0].status, "complete");
        assert_eq!(calls[0].finish_reason.as_deref(), Some("stop"));
    }

    #[tokio::test]
    async fn test_openai_usage_null_does_not_complete_or_split_stream() {
        let chunks = [
            r#"data: {"id":"chatcmpl-null","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"Hel"},"finish_reason":null}],"usage":null}"#,
            r#"data: {"id":"chatcmpl-null","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"lo"},"finish_reason":null}],"usage":null}"#,
            r#"data: {"id":"chatcmpl-null","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":null}"#,
            "data: [DONE]\n\n",
        ];
        let collected = process_chunks(&chunks).await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].data["message_id"], "chatcmpl-null");
        assert_eq!(collected[0].data["text_content"], "Hello");
    }

    #[tokio::test]
    async fn test_openai_final_usage_chunk_completes_once() {
        let chunks = [
            r#"data: {"id":"chatcmpl-usage","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}"#,
            r#"data: {"id":"chatcmpl-usage","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}"#,
            r#"data: {"id":"chatcmpl-usage","object":"chat.completion.chunk","model":"openai-mock","choices":[],"usage":{"prompt_tokens":2,"completion_tokens":5,"total_tokens":7}}"#,
            "data: [DONE]\n\n",
        ];
        let collected = process_chunks(&chunks).await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].data["text_content"], "Hello");

        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.example.test" },
                "body": "{\"model\":\"openai-mock\"}"
            }),
        );
        view.ingest_event(&req).unwrap();
        view.ingest_event(&collected[0]).unwrap();
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.token_usage_rows, 1);
        assert_eq!(snapshot.summary.input_tokens, 2);
        assert_eq!(snapshot.summary.output_tokens, 5);
        assert_eq!(snapshot.summary.total_tokens, 7);
    }

    #[tokio::test]
    async fn test_openai_response_id_separates_keepalive_streams() {
        let mut processor = SSEProcessor::new();
        let input_stream: EventStream = Box::pin(stream::iter(vec![
            http_sse_response(
                2,
                r#"data: {"id":"chatcmpl-a","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"A"},"finish_reason":"stop"}]}"#,
            ),
            http_sse_response(
                3,
                r#"data: {"id":"chatcmpl-b","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"content":"B"},"finish_reason":"stop"}]}"#,
            ),
        ]));
        let collected: Vec<_> = processor
            .process(input_stream)
            .await
            .unwrap()
            .collect()
            .await;

        assert_eq!(collected.len(), 2);
        assert_eq!(collected[0].data["message_id"], "chatcmpl-a");
        assert_eq!(collected[0].data["text_content"], "A");
        assert_eq!(collected[1].data["message_id"], "chatcmpl-b");
        assert_eq!(collected[1].data["text_content"], "B");
    }

    #[tokio::test]
    async fn test_openai_streamed_tool_calls_are_accumulated() {
        let chunks = [
            r#"data: {"id":"chatcmpl-tool","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"lookup","arguments":"{\"q\":"}}]},"finish_reason":null}]}"#,
            r#"data: {"id":"chatcmpl-tool","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\"x\"}"}}]},"finish_reason":null}]}"#,
            r#"data: {"id":"chatcmpl-tool","object":"chat.completion.chunk","model":"openai-mock","choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}]}"#,
            "data: [DONE]\n\n",
        ];
        let collected = process_chunks(&chunks).await;

        assert_eq!(collected.len(), 1);
        let json_content: serde_json::Value =
            serde_json::from_str(collected[0].data["json_content"].as_str().unwrap()).unwrap();
        assert_eq!(json_content["tool_calls"][0]["id"], "call_1");
        assert_eq!(json_content["tool_calls"][0]["function"]["name"], "lookup");
        assert_eq!(
            json_content["tool_calls"][0]["function"]["arguments"],
            "{\"q\":\"x\"}"
        );

        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": { "host": "api.example.test" },
                "body": "{\"model\":\"openai-mock\"}"
            }),
        );
        view.ingest_event(&req).unwrap();
        view.ingest_event(&collected[0]).unwrap();
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.tool_calls.len(), 1);
        assert_eq!(snapshot.tool_calls[0].tool_name.as_deref(), Some("lookup"));
        assert_eq!(
            snapshot.tool_calls[0].tool_call_id.as_deref(),
            Some("call_1")
        );
        assert_eq!(snapshot.tool_calls[0].input["q"], "x");
    }

    #[tokio::test]
    async fn test_openai_responses_stream_accumulates_text_usage_and_tools() {
        let chunks = [
            r#"event: response.output_item.added
data: {"type":"response.output_item.added","response_id":"resp_1","output_index":0,"item":{"id":"fc_1","type":"function_call","name":"lookup","arguments":""}}"#,
            r#"event: response.function_call_arguments.delta
data: {"type":"response.function_call_arguments.delta","response_id":"resp_1","item_id":"fc_1","output_index":0,"delta":"{\"q\":"}"#,
            r#"event: response.function_call_arguments.done
data: {"type":"response.function_call_arguments.done","response_id":"resp_1","item_id":"fc_1","output_index":0,"arguments":"{\"q\":\"x\"}"}"#,
            r#"event: response.output_text.delta
data: {"type":"response.output_text.delta","response_id":"resp_1","output_index":1,"content_index":0,"delta":"Hello"}"#,
            r#"event: response.completed
data: {"type":"response.completed","response":{"id":"resp_1","status":"completed","usage":{"input_tokens":2,"output_tokens":5,"total_tokens":7}}}"#,
        ];
        let collected = process_chunks(&chunks).await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].data["message_id"], "resp_1");
        assert_eq!(collected[0].data["text_content"], "Hello");
        let json_content: serde_json::Value =
            serde_json::from_str(collected[0].data["json_content"].as_str().unwrap()).unwrap();
        assert_eq!(json_content["tool_calls"][0]["id"], "fc_1");
        assert_eq!(json_content["tool_calls"][0]["function"]["name"], "lookup");
        assert_eq!(
            json_content["tool_calls"][0]["function"]["arguments"],
            "{\"q\":\"x\"}"
        );

        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            1234,
            "codex".to_string(),
            json!({
                "tid": 99,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/responses",
                "headers": { "host": "api.openai.com" },
                "body": "{\"model\":\"gpt-test\"}"
            }),
        );
        view.ingest_event(&req).unwrap();
        view.ingest_event(&collected[0]).unwrap();
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.llm_calls, 1);
        assert_eq!(snapshot.summary.token_usage_rows, 1);
        assert_eq!(snapshot.summary.input_tokens, 2);
        assert_eq!(snapshot.summary.output_tokens, 5);
        assert_eq!(snapshot.tool_calls.len(), 1);
        assert_eq!(snapshot.tool_calls[0].tool_name.as_deref(), Some("lookup"));
        assert_eq!(snapshot.tool_calls[0].input["q"], "x");
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
    async fn test_http_parser_sse_response_body_is_processed() {
        let mut processor = SSEProcessor::new();
        let test_event = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "response",
                "status_code": 200,
                "headers": { "content-type": "text/event-stream", "host": "api.example.test" },
                "path": "/v1/chat/completions",
                "body": "data: {\"usage\":{\"input_tokens\":2,\"output_tokens\":3}}\n\ndata: [DONE]\n\n"
            }),
        );

        let input_stream: EventStream = Box::pin(stream::iter(vec![test_event]));
        let output_stream = processor.process(input_stream).await.unwrap();
        let collected: Vec<_> = output_stream.collect().await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "sse_processor");
        assert_eq!(collected[0].data["original_source"], "http_parser");
        assert_eq!(collected[0].data["host"], "api.example.test");
        assert_eq!(collected[0].data["path"], "/v1/chat/completions");
        assert_eq!(collected[0].data["status_code"], 200);
    }

    #[tokio::test]
    async fn test_http_parser_non_streaming_usage_response_passes_through() {
        let mut processor = SSEProcessor::new();
        let test_event = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            1234,
            "node".to_string(),
            json!({
                "tid": 99,
                "message_type": "response",
                "status_code": 200,
                "headers": { "content-type": "application/json" },
                "body": "{\"usageMetadata\":{\"promptTokenCount\":11,\"totalTokenCount\":11}}"
            }),
        );

        let input_stream: EventStream = Box::pin(stream::iter(vec![test_event.clone()]));
        let output_stream = processor.process(input_stream).await.unwrap();
        let collected: Vec<_> = output_stream.collect().await;

        assert_eq!(collected.len(), 1);
        assert_eq!(collected[0].source, "http_parser");
        assert_eq!(collected[0].data, test_event.data);
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
