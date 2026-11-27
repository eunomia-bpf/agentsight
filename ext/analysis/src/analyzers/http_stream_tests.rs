// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::*;
use crate::analyzers::{HTTPDecompressor, SSEProcessor};
use crate::view::MaterializedView;
use futures::stream;
use loona_hpack::Encoder;
use serde_json::json;

fn ssl(seq: u64, handle: &str, direction: &str, bytes: &[u8]) -> Event {
    Event::new_with_timestamp(
        seq,
        "ssl".into(),
        42,
        "kimi".into(),
        json!({
            "tid": if direction == "WRITE" { 100 } else { 200 }, "function": direction,
            "transport_handle": handle, "process_start_ns": 123, "tls_library": "openssl",
            "capture_seq": seq, "len": bytes.len(), "buf_size": bytes.len(), "truncated": false,
            "ringbuf_reserve_failures": 0, "data": String::from_utf8_lossy(bytes), "data_hex": hex::encode(bytes),
        }),
    )
}

fn request(seq: u64, handle: &str) -> Event {
    ssl(seq, handle, "WRITE", b"POST /v1/chat/completions HTTP/1.1\r\nHost: api.test\r\nContent-Length: 13\r\n\r\n{\"model\":\"m\"}")
}

fn delta(id: &str, text: &str) -> Vec<u8> {
    format!(
        "data: {}\r\n\r\n",
        json!({"id": id, "choices":[{"index":0,"delta":{"content":text},"finish_reason":"stop"}]})
    )
    .into_bytes()
}

fn transfer_chunk(payload: &[u8]) -> Vec<u8> {
    let mut bytes = format!("{:x}\r\n", payload.len()).into_bytes();
    bytes.extend_from_slice(payload);
    bytes.extend_from_slice(b"\r\n");
    bytes
}

async fn pipeline(input: Vec<Event>) -> Vec<Event> {
    let parsed = HTTPParser::new()
        .process(Box::pin(stream::iter(input)))
        .await
        .unwrap();
    let decompressed = HTTPDecompressor::new().process(parsed).await.unwrap();
    SSEProcessor::new()
        .defer_transport_to_http()
        .process(decompressed)
        .await
        .unwrap()
        .collect()
        .await
}

#[tokio::test]
async fn http1_interleaved_sse_retains_utf8_usage_and_capture_provenance() {
    let header =
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n";
    let a = delta("a", "你好");
    let cut = a
        .windows(3)
        .position(|bytes| bytes == "你".as_bytes())
        .unwrap()
        + 1;
    let mut first = header.to_vec();
    first.extend(transfer_chunk(&a[..cut]));
    let mut second = transfer_chunk(&a[cut..]);
    second.extend(transfer_chunk(b"data: {\"id\":\"a\",\"usage\":{\"prompt_tokens\":2,\"completion_tokens\":3,\"total_tokens\":5}}\n\ndata: [DONE]\n\n"));
    second.extend(b"0\r\nX-Trailer: ok\r\n\r\n");
    let b = delta("b", "independent");
    let mut other = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\n\r\n",
        b.len()
    )
    .into_bytes();
    other.extend(b);
    let output = pipeline(vec![
        request(1, "0xa"),
        request(2, "0xb"),
        ssl(3, "0xa", "READ", &first),
        ssl(4, "0xb", "READ", &other),
        ssl(5, "0xa", "READ", &second),
    ])
    .await;
    let responses: Vec<_> = output
        .iter()
        .filter(|event| event.source == "sse_processor")
        .collect();
    assert_eq!(responses.len(), 2);
    assert_eq!(responses[0].data["text_content"], "independent");
    let response = responses[1];
    assert_eq!(response.data["text_content"], "你好");
    assert_eq!(response.data["capture_fragment_count"], 2);
    assert_eq!(response.data["capture_seq_start"], 3);
    assert_eq!(response.data["capture_seq_end"], 5);
    assert_eq!(
        response.data["capture_captured_len"],
        first.len() + second.len()
    );
    assert_eq!(response.data["incomplete"], false);
    let mut view = MaterializedView::new();
    for event in output {
        view.ingest_event(&event).unwrap();
    }
    let calls = view.llm_call_rows(10);
    assert_eq!(calls.len(), 2);
    assert!(calls.iter().all(
        |call| call.status == "complete" && call.correlation_status.as_deref() == Some("exact")
    ));
    assert_eq!(calls.iter().map(|call| call.total_tokens).sum::<i64>(), 5);
}

#[tokio::test]
async fn http1_streaming_completion_preserves_pipelined_next_response() {
    let mut requests = request(1, "0xa");
    let raw = hex::decode(requests.data["data_hex"].as_str().unwrap())
        .unwrap()
        .repeat(2);
    requests = ssl(1, "0xa", "WRITE", &raw);
    let mut raw =
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n"
            .to_vec();
    raw.extend(transfer_chunk(&delta("first", "one")));
    raw.extend(b"0\r\n\r\n");
    let body = delta("second", "two");
    raw.extend(
        format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\n\r\n",
            body.len()
        )
        .bytes(),
    );
    raw.extend(body);
    let output = pipeline(vec![requests, ssl(2, "0xa", "READ", &raw)]).await;
    assert_eq!(output.len(), 4);
    assert_eq!(output[2].data["text_content"], "one");
    assert_eq!(output[3].data["text_content"], "two");
    assert_eq!(
        output[0].data["http_exchange_id"],
        output[2].data["http_exchange_id"]
    );
    assert_eq!(
        output[1].data["http_exchange_id"],
        output[3].data["http_exchange_id"]
    );
    assert_eq!(output[3].data["capture_fragment_count"], 1);
}

fn frame(kind: u8, flags: u8, id: u32, payload: &[u8]) -> Vec<u8> {
    let n = payload.len();
    let mut bytes = vec![(n >> 16) as u8, (n >> 8) as u8, n as u8, kind, flags];
    bytes.extend(id.to_be_bytes());
    bytes.extend(payload);
    bytes
}

#[tokio::test]
async fn http2_streams_wait_for_end_stream_including_trailers() {
    let mut enc = Encoder::new();
    let req = enc.encode([
        (&b":method"[..], &b"GET"[..]),
        (&b":path"[..], &b"/v1/chat/completions"[..]),
    ]);
    let mut requests = frame(1, 5, 1, &req);
    let req = enc.encode([
        (&b":method"[..], &b"GET"[..]),
        (&b":path"[..], &b"/v1/chat/completions"[..]),
    ]);
    requests.extend(frame(1, 5, 3, &req));
    let mut enc = Encoder::new();
    let h = enc.encode([
        (&b":status"[..], &b"200"[..]),
        (&b"content-type"[..], &b"text/event-stream"[..]),
    ]);
    let mut headers = frame(1, 4, 1, &h);
    let h = enc.encode([
        (&b":status"[..], &b"200"[..]),
        (&b"content-type"[..], &b"text/event-stream"[..]),
    ]);
    headers.extend(frame(1, 4, 3, &h));
    let mut data = frame(0, 0, 1, &delta("one", "A"));
    data.extend(frame(0, 1, 3, &delta("three", "B")));
    let trailers = frame(1, 5, 1, &enc.encode([(&b"x-end"[..], &b"yes"[..])]));
    let output = pipeline(vec![
        ssl(1, "0xa", "WRITE", &requests),
        ssl(2, "0xa", "READ", &headers),
        ssl(3, "0xa", "READ", &data),
        ssl(4, "0xa", "READ", &trailers),
    ])
    .await;
    let responses: Vec<_> = output
        .iter()
        .filter(|event| event.source == "sse_processor")
        .collect();
    assert_eq!(responses.len(), 2);
    assert_eq!(responses[0].data["stream_id"], 3);
    assert_eq!(responses[1].data["stream_id"], 1);
    assert_eq!(responses[1].data["text_content"], "A");
    assert_eq!(responses[1].data["capture_fragment_count"], 3);
    assert_eq!(responses[1].data["incomplete"], false);
}

#[tokio::test]
async fn interrupted_sse_is_preserved_and_never_materialized_as_complete() {
    for reason in ["capture_loss", "closed", "capture_end"] {
        let mut response = b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n\r\n".to_vec();
        response.extend(delta("partial", "retained"));
        response.extend(b"data: {\"unfinished\":");
        let mut input = vec![request(1, "0xa"), ssl(2, "0xa", "READ", &response)];
        if reason == "closed" {
            let mut close = ssl(3, "0xa", "CLOSE", b"");
            close.data["connection_closed"] = json!(true);
            input.push(close);
        }
        if reason == "capture_loss" {
            input.push(Event::new_with_timestamp(
                3,
                "ssl".into(),
                42,
                "sslsniff".into(),
                json!({"function":"CAPTURE_LOSS","ringbuf_reserve_failures":1}),
            ));
        }
        let output = pipeline(input).await;
        let response = output
            .iter()
            .find(|event| event.source == "sse_processor")
            .unwrap();
        assert_eq!(response.data["completion_reason"], reason);
        assert_eq!(response.data["incomplete"], true);
        assert_eq!(response.data["text_content"], "retained");
        assert_eq!(
            response.data["unparsed_sse_hex"],
            hex::encode(b"data: {\"unfinished\":")
        );
        let mut view = MaterializedView::new();
        for event in output {
            view.ingest_event(&event).unwrap();
        }
        let calls = view.llm_call_rows(10);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].status, "partial");
    }
}

#[tokio::test]
async fn long_http1_sse_drains_body_without_hitting_the_whole_message_limit() {
    let mut input = vec![request(1, "0xa"), ssl(2, "0xa", "READ",
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n")];
    let mut comment = vec![b'x'; 96 * 1024];
    comment[0] = b':';
    comment.extend(b"\n\n");
    for seq in 3..27 {
        input.push(ssl(seq, "0xa", "READ", &transfer_chunk(&comment)));
    }
    let mut last = transfer_chunk(&delta("large", "retained"));
    last.extend(b"0\r\n\r\n");
    input.push(ssl(27, "0xa", "READ", &last));
    let output = pipeline(input).await;
    assert_eq!(output.len(), 2);
    assert_eq!(output[1].data["text_content"], "retained");
    assert!(output[1].data["received_bytes"].as_u64().unwrap() > MAX_HTTP1_BUFFER_BYTES as u64);
    assert_eq!(output[1].data["capture_fragment_count"], 26);
    assert_eq!(output[1].data["incomplete"], false);
}

#[tokio::test]
async fn compressed_sse_keeps_the_existing_whole_body_decompression_path() {
    use flate2::{Compression, write::GzEncoder};
    use std::io::Write;
    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(&delta("gzip", "decoded")).unwrap();
    let bytes = encoder.finish().unwrap();
    let mut response = format!("HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Encoding: gzip\r\nContent-Length: {}\r\n\r\n", bytes.len()).into_bytes();
    response.extend(bytes);
    let output = pipeline(vec![request(1, "0xa"), ssl(2, "0xa", "READ", &response)]).await;
    assert_eq!(output.len(), 2);
    assert_eq!(output[1].data["text_content"], "decoded");
    assert_eq!(output[1].data["incomplete"], false);
}

#[tokio::test]
async fn provider_error_is_not_a_successful_llm_call_even_with_http_200() {
    for body in [
        "event: error\ndata: {\"type\":\"error\",\"error\":{\"message\":\"overloaded\"}}\n\n",
        "data: {\"error\":{\"message\":\"overloaded\"}}\n\n",
    ] {
        let mut response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\n\r\n",
            body.len()
        )
        .into_bytes();
        response.extend(body.as_bytes());
        let output = pipeline(vec![request(1, "0xa"), ssl(2, "0xa", "READ", &response)]).await;
        assert_eq!(output[1].data["completion_reason"], "error");
        let mut view = MaterializedView::new();
        for event in output {
            view.ingest_event(&event).unwrap();
        }
        assert_eq!(view.llm_call_rows(10)[0].status, "error");
    }
}

#[tokio::test]
async fn http2_reset_preserves_the_partial_sse_body() {
    let mut enc = Encoder::new();
    let req = enc.encode([
        (&b":method"[..], &b"GET"[..]),
        (&b":path"[..], &b"/v1/chat/completions"[..]),
    ]);
    let mut enc = Encoder::new();
    let headers = enc.encode([
        (&b":status"[..], &b"200"[..]),
        (&b"content-type"[..], &b"text/event-stream"[..]),
    ]);
    let mut response = frame(1, 4, 1, &headers);
    response.extend(frame(0, 0, 1, &delta("reset", "retained")));
    response.extend(frame(3, 0, 1, &8u32.to_be_bytes()));
    let output = pipeline(vec![
        ssl(1, "0xa", "WRITE", &frame(1, 5, 1, &req)),
        ssl(2, "0xa", "READ", &response),
    ])
    .await;
    let aggregate = output
        .iter()
        .find(|event| event.source == "sse_processor")
        .unwrap();
    assert_eq!(aggregate.data["text_content"], "retained");
    assert_eq!(aggregate.data["completion_reason"], "reset");
    assert_eq!(aggregate.data["incomplete"], true);
}

#[tokio::test]
async fn one_thread_raw_tls_does_not_contaminate_two_chunked_sse_exchanges() {
    // Maintainer's reproducer: sequential POSTs on one connection, interleaved
    // with a gateway-like non-HTTP TLS connection on the very same PID/TID.
    let mut input = Vec::new();
    let mut seq = 0;
    for id in ["first", "second"] {
        seq += 1;
        let body = json!({"model":"m", "stream":true, "messages":[
            {"role":"user", "content":"x".repeat(135_000)}
        ]})
        .to_string();
        let req = format!(
            "POST /v1/chat/completions HTTP/1.1\r\nHost: api.test\r\nContent-Length: {}\r\n\r\n{body}",
            body.len()
        );
        input.push(ssl(seq, "0xa", "WRITE", req.as_bytes()));
        seq += 1;
        input.push(ssl(seq, "0xa", "READ", b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n"));
        for _ in 0..5 {
            seq += 1;
            let chunk = transfer_chunk(&delta(id, id));
            // Split a transfer chunk too, so the foreign bytes arrive while
            // the HTTP framing scanner has an unfinished chunk buffered.
            input.push(ssl(seq, "0xa", "READ", &chunk[..7]));
            seq += 1;
            input.push(ssl(seq, "0xb", "READ", b"\x81\x05frame"));
            seq += 1;
            input.push(ssl(seq, "0xa", "READ", &chunk[7..]));
        }
        seq += 1;
        input.push(ssl(seq, "0xa", "READ", b"0\r\n\r\n"));
    }
    for event in &mut input {
        event.data["tid"] = json!(100);
    }
    let output = pipeline(input).await;
    let raw: Vec<_> = output
        .iter()
        .filter(|event| event.source == "ssl")
        .collect();
    assert_eq!(raw.len(), 10);
    assert!(
        raw.iter()
            .all(|event| event.data["data_hex"] == hex::encode(b"\x81\x05frame"))
    );
    let responses: Vec<_> = output
        .iter()
        .filter(|event| event.source == "sse_processor")
        .collect();
    assert_eq!(responses.len(), 2);
    for (response, id) in responses.iter().zip(["first", "second"]) {
        assert_eq!(response.data["text_content"], id.repeat(5));
        assert_eq!(response.data["incomplete"], false);
        assert_eq!(response.data["capture_fragment_count"], 12);
    }
    assert_ne!(
        responses[0].data["http_exchange_id"],
        responses[1].data["http_exchange_id"]
    );
    let mut view = MaterializedView::new();
    for event in output {
        view.ingest_event(&event).unwrap();
    }
    let calls = view.llm_call_rows(10);
    assert_eq!(calls.len(), 2);
    assert!(calls.iter().all(
        |call| call.status == "complete" && call.correlation_status.as_deref() == Some("exact")
    ));
}

#[tokio::test]
async fn server_written_sse_streams_and_binds_at_headers() {
    let mut req = request(1, "0xa");
    req.data["function"] = json!("READ");
    let mut parser = HTTPParser::new();
    let request = parser.handle_ssl_event(req).pop().unwrap();
    let headers = parser.handle_ssl_event(ssl(
        2,
        "0xa",
        "WRITE",
        b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n",
    ));
    assert_eq!(headers.len(), 1);
    assert_eq!(headers[0].data["message_type"], "response_chunk");
    assert_eq!(
        headers[0].data["http_exchange_id"],
        request.data["http_exchange_id"]
    );
    assert_eq!(headers[0].data["end_stream"], false);
    let body = parser.handle_ssl_event(ssl(
        3,
        "0xa",
        "WRITE",
        &transfer_chunk(&delta("server", "hello")),
    ));
    assert_eq!(body[0].data["end_stream"], false);
    let end = parser.handle_ssl_event(ssl(4, "0xa", "WRITE", b"0\r\n\r\n"));
    assert_eq!(end[0].data["end_stream"], true);
    let output: Vec<_> = SSEProcessor::new()
        .process(Box::pin(stream::iter(
            headers.into_iter().chain(body).chain(end),
        )))
        .await
        .unwrap()
        .collect()
        .await;
    assert_eq!(output.len(), 1);
    assert_eq!(output[0].data["text_content"], "hello");
    assert_eq!(output[0].data["incomplete"], false);
    assert_eq!(output[0].data["capture_fragment_count"], 3);
}

#[tokio::test]
async fn http2_fragmented_sse_headers_bind_before_body_and_flush_on_eof() {
    let mut enc = Encoder::new();
    let request = enc.encode([
        (&b":method"[..], &b"GET"[..]),
        (&b":path"[..], &b"/v1/chat/completions"[..]),
    ]);
    let mut enc = Encoder::new();
    let headers = enc.encode([
        (&b":status"[..], &b"200"[..]),
        (&b"content-type"[..], &b"text/event-stream"[..]),
    ]);
    for split in [false, true] {
        let mut parser = HTTPParser::new();
        let req = parser.handle_ssl_event(ssl(1, "0xa", "WRITE", &frame(1, 5, 1, &request)));
        let bound = if split {
            assert!(
                parser
                    .handle_ssl_event(ssl(2, "0xa", "READ", &frame(1, 0, 1, &headers[..2])))
                    .is_empty()
            );
            parser.handle_ssl_event(ssl(3, "0xa", "READ", &frame(9, 4, 1, &headers[2..])))
        } else {
            parser.handle_ssl_event(ssl(2, "0xa", "READ", &frame(1, 4, 1, &headers)))
        };
        assert_eq!(bound.len(), 1);
        assert_eq!(
            bound[0].data["http_exchange_id"],
            req[0].data["http_exchange_id"]
        );
        assert_eq!(bound[0].data["end_stream"], false);
        let output: Vec<_> = SSEProcessor::new()
            .process(Box::pin(stream::iter(bound)))
            .await
            .unwrap()
            .collect()
            .await;
        assert_eq!(output.len(), 1);
        assert_eq!(output[0].data["completion_reason"], "capture_end");
        assert_eq!(output[0].data["incomplete"], true);
    }
}

#[tokio::test]
async fn truncated_stream_keeps_prefix_and_never_claims_http_completion() {
    let bytes = delta("cut", "retained");
    let mut response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\n\r\n",
        bytes.len() + 20
    )
    .into_bytes();
    response.extend(bytes);
    let mut cut = ssl(2, "0xa", "READ", &response);
    cut.data["truncated"] = json!(true);
    cut.data["bytes_lost"] = json!(20);
    cut.data["len"] = json!(response.len() + 20);
    let output = pipeline(vec![request(1, "0xa"), cut]).await;
    let response = output
        .iter()
        .find(|event| event.source == "sse_processor")
        .unwrap();
    assert_eq!(response.data["text_content"], "retained");
    assert_eq!(response.data["incomplete"], true);
    assert_eq!(response.data["completion_reason"], "truncated");
    assert_eq!(response.data["capture_truncated"], true);
    assert_eq!(response.data["capture_fragment_count"], 1);
}
