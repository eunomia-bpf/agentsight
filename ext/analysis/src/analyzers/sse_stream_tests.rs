// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::*;
use serde_json::Value;

fn chunk(id: &str, timestamp: u64, bytes: &[u8], ended: bool) -> Event {
    Event::new_with_timestamp(
        timestamp,
        "http_parser".into(),
        42,
        "kimi".into(),
        json!({
            "tid":100, "message_type":"response_chunk", "correlation_version":2,
            "correlation_status":"exact", "connection_id":"tls-1", "http_exchange_id":id,
            "headers":{"content-type":"text/event-stream"}, "body_hex":hex::encode(bytes),
            "end_stream":ended, "status_code":200,
        }),
    )
}

fn record(event: &str, data: Value) -> String {
    format!("event: {event}\ndata: {data}\n\n")
}

fn merged(event: &Event) -> Value {
    serde_json::from_str(event.data["json_content"].as_str().unwrap()).unwrap()
}

#[test]
fn bytewise_utf8_crlf_multiline_and_final_cr_are_lossless() {
    let bytes = ": heartbeat\r\nevent: custom\r\nid: event-1\r\ndata: 你好\r\ndata:  world\r\n\r\ndata: last\r\r".as_bytes();
    let mut processor = StreamingSSE::new(30_000, 2);
    for (index, byte) in bytes.iter().enumerate() {
        // Completing an SSE record does not finish the HTTP response.
        assert!(
            processor
                .handle(chunk("a", index as u64, &[*byte], false))
                .is_empty()
        );
    }
    let output = processor.handle(chunk("a", bytes.len() as u64, b"", true));
    assert_eq!(output.len(), 1);
    assert_eq!(output[0].data["event_count"], 2);
    assert_eq!(output[0].data["sse_events"][0]["data"], "你好\n world");
    assert_eq!(output[0].data["sse_events"][0]["event"], "custom");
    assert_eq!(output[0].data["sse_events"][0]["id"], "event-1");
    assert_eq!(output[0].data["sse_events"][1]["data"], "last");
    assert_eq!(output[0].data["incomplete"], false);
    assert!(processor.finish().is_empty());
}

#[test]
fn choices_refusals_tools_and_late_usage_stay_in_one_exchange() {
    let first = record(
        "message",
        json!({"id":"shared-provider-id","choices":[
            {"index":0,"delta":{"content":"A", "tool_calls":[{"index":0,"id":"t0","function":{"name":"read","arguments":"{\"x\":"}}]}},
            {"index":1,"delta":{"content":"B", "tool_calls":[{"index":0,"id":"t1","function":{"name":"write","arguments":"{}"}}]}},
            {"index":2,"delta":{"refusal":"cannot"},"finish_reason":"stop"}
        ]}),
    );
    let second = record(
        "message",
        json!({"id":"shared-provider-id","choices":[
            {"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"1}"}}]},"finish_reason":"tool_calls"}
        ]}),
    );
    let usage = record(
        "message",
        json!({"id":"shared-provider-id","choices":[],"usage":{"total_tokens":7}}),
    );
    let mut processor = StreamingSSE::new(30_000, 2);
    assert!(
        processor
            .handle(chunk("a", 1, first.as_bytes(), false))
            .is_empty()
    );
    // A provider ID is not a grouping key: a distinct exchange must stay distinct.
    let other = processor.handle(chunk("b", 2, usage.as_bytes(), true));
    assert_eq!(other[0].data["http_exchange_id"], "b");
    assert!(
        processor
            .handle(chunk("a", 3, second.as_bytes(), false))
            .is_empty()
    );
    let output = processor.handle(chunk("a", 4, usage.as_bytes(), true));
    let data = merged(&output[0]);
    assert_eq!(output[0].data["text_content"], "A");
    assert_eq!(data["choices"][1]["text"], "B");
    assert_eq!(data["choices"][2]["refusal"], "cannot");
    assert_eq!(
        data["tool_calls"][0]["function"]["arguments_json"],
        json!({"x":1})
    );
    assert_eq!(data["tool_calls"][1]["choice_index"], 1);
    assert_eq!(data["tool_calls"][1]["id"], "t1");
    assert_eq!(data["usage"]["total_tokens"], 7);
}

#[test]
fn anthropic_blocks_keep_thinking_signatures_tools_and_usage() {
    let records = [
        (
            "message_start",
            json!({"message":{"id":"msg-1","model":"claude","usage":{"input_tokens":5}}}),
        ),
        (
            "content_block_start",
            json!({"index":0,"content_block":{"type":"thinking","thinking":"think"}}),
        ),
        (
            "content_block_delta",
            json!({"index":0,"delta":{"type":"thinking_delta","thinking":" more"}}),
        ),
        (
            "content_block_delta",
            json!({"index":0,"delta":{"type":"signature_delta","signature":"signed"}}),
        ),
        ("content_block_stop", json!({"index":0})),
        (
            "content_block_start",
            json!({"index":1,"content_block":{"type":"tool_use","id":"t1","name":"read","input":{}}}),
        ),
        (
            "content_block_delta",
            json!({"index":1,"delta":{"type":"input_json_delta","partial_json":"{\"path\":"}}),
        ),
        (
            "content_block_delta",
            json!({"index":1,"delta":{"type":"input_json_delta","partial_json":"\"a\"}"}}),
        ),
        ("content_block_stop", json!({"index":1})),
        (
            "message_delta",
            json!({"delta":{"stop_reason":"tool_use"},"usage":{"output_tokens":3}}),
        ),
    ];
    let mut processor = StreamingSSE::new(30_000, 2);
    for (index, (kind, data)) in records.into_iter().enumerate() {
        assert!(
            processor
                .handle(chunk(
                    "a",
                    index as u64,
                    record(kind, data).as_bytes(),
                    false
                ))
                .is_empty()
        );
    }
    let output = processor.handle(chunk("a", 20, b"event: message_stop\ndata: {}\n\n", true));
    let data = merged(&output[0]);
    assert_eq!(output[0].data["text_content"], "");
    assert_eq!(output[0].data["response_id"], "msg-1");
    assert_eq!(data["content_blocks"][0]["thinking"], "think more");
    assert_eq!(data["content_blocks"][0]["signature"], "signed");
    assert_eq!(data["content_blocks"][1]["input"], json!({"path":"a"}));
    assert_eq!(data["usage"], json!({"input_tokens":5,"output_tokens":3}));
    assert_eq!(data["stop_reason"], "tool_use");
}

#[test]
fn conflicting_response_ids_are_reported_not_used_to_regroup() {
    let mut processor = StreamingSSE::new(30_000, 2);
    let bytes =
        b"data: {\"id\":\"one\",\"choices\":[]}\n\ndata: {\"id\":\"two\",\"choices\":[]}\n\n";
    let output = processor.handle(chunk("a", 1, bytes, true));
    assert_eq!(output.len(), 1);
    assert_eq!(output[0].data["http_exchange_id"], "a");
    assert_eq!(output[0].data["response_id"], "one");
    assert_eq!(output[0].data["correlation_status"], "ambiguous");
    assert_eq!(output[0].data["incomplete"], true);
}

#[test]
fn eviction_and_timeout_emit_partial_once_and_ignore_late_chunks() {
    let mut processor = StreamingSSE::new(10, 1);
    assert!(
        processor
            .handle(chunk("a", 1, b"data: A\n\n", false))
            .is_empty()
    );
    let evicted = processor.handle(chunk("b", 2, b"data: B\n\n", false));
    assert_eq!(evicted[0].data["http_exchange_id"], "a");
    assert_eq!(evicted[0].data["completion_reason"], "evicted");
    assert!(
        processor
            .handle(chunk("a", 3, b"data: late\n\n", true))
            .is_empty()
    );
    let expired = processor.handle(chunk("b", 20, b"data: late\n\n", true));
    assert_eq!(expired.len(), 1);
    assert_eq!(expired[0].data["completion_reason"], "timeout");
    assert_eq!(expired[0].data["incomplete"], true);
    assert!(processor.finish().is_empty());
}

#[test]
fn byte_and_event_limits_preserve_prefix_without_claiming_completion() {
    let mut processor = StreamingSSE::new(30_000, 2);
    let bytes = vec![b'x'; MAX_SSE_BYTES + 1];
    assert!(processor.handle(chunk("a", 1, &bytes, false)).is_empty());
    let output = processor.handle(chunk("a", 2, b"", true));
    assert_eq!(output[0].data["completion_reason"], "truncated");
    assert_eq!(output[0].data["received_bytes"], bytes.len());
    assert_eq!(
        output[0].data["unparsed_sse_hex"].as_str().unwrap().len(),
        2 * MAX_SSE_BYTES
    );
    assert_eq!(output[0].data["incomplete"], true);
    let bytes = b"data:x\n\n".repeat(MAX_SSE_EVENTS + 1);
    let output = processor.handle(chunk("b", 3, &bytes, true));
    assert_eq!(output[0].data["event_count"], MAX_SSE_EVENTS);
    assert_eq!(output[0].data["completion_reason"], "truncated");
}

#[test]
fn complete_body_fallback_keeps_upstream_truncation_semantics() {
    for reason in ["truncated", "closed"] {
        let mut processor = StreamingSSE::new(30_000, 2);
        let mut event = chunk(
            "a",
            1,
            b"data: {\"choices\":[{\"delta\":{\"content\":\"prefix\"}}]}\n\n",
            false,
        );
        event.data["message_type"] = json!("response");
        event.data["body_truncated"] = json!(reason == "truncated");
        event.data["completion_reason"] = json!(reason);
        let output = processor.handle(event);
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["completion_reason"], reason);
        assert_eq!(output[0].data["text_content"], "prefix");
        assert_eq!(output[0].data["incomplete"], true);
    }
}

#[test]
fn total_retention_is_bounded_and_released_when_an_exchange_finishes() {
    let mut processor = StreamingSSE::new(30_000, 8);
    processor.max_total_bytes = 12;
    assert!(
        processor
            .handle(chunk("a", 1, b"data:A\n\n", false))
            .is_empty()
    );
    assert!(
        processor
            .handle(chunk("b", 2, b"data:B\n\n", false))
            .is_empty()
    );
    assert_eq!(
        processor
            .buffers
            .values()
            .map(|state| state.retained)
            .sum::<usize>(),
        12
    );
    assert!(
        processor.buffers["a"]
            .content
            .template_event
            .data
            .get("body_hex")
            .is_none()
    );
    let limited = processor.handle(chunk("b", 3, b"", true));
    assert_eq!(limited[0].data["completion_reason"], "truncated");
    assert_eq!(limited[0].data["received_bytes"], 8);
    assert_eq!(limited[0].data["incomplete"], true);
    let complete = processor.handle(chunk("a", 4, b"", true));
    assert_eq!(complete[0].data["incomplete"], false);
    let next = processor.handle(chunk("c", 5, b"data:C\n\n", true));
    assert_eq!(next[0].data["incomplete"], false);
    assert_eq!(next[0].data["event_count"], 1);
}
