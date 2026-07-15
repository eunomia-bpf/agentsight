// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{Analyzer, AnalyzerError};
use crate::event::Event;
use crate::runners::EventStream;
use async_trait::async_trait;
use flate2::read::{DeflateDecoder, GzDecoder, ZlibDecoder};
use futures::stream::StreamExt;
use serde_json::{Value, json};
use std::io::{Cursor, Read};

pub struct HTTPDecompressor;

impl HTTPDecompressor {
    pub fn new() -> Self {
        Self
    }

    fn process_event(mut event: Event) -> Event {
        if event.source != "http_parser" {
            return event;
        }
        if event.data.get("message_type").and_then(Value::as_str) != Some("response") {
            return event;
        }

        let Some(encoding) = content_encoding(&event.data) else {
            return event;
        };
        let Some(compressed) = http_body_bytes(&event.data) else {
            return event;
        };
        let payload = if is_chunked(&event.data) {
            decode_chunked(&compressed).unwrap_or(compressed)
        } else {
            compressed
        };

        let Ok(decompressed) = decompress_body(&encoding, &payload) else {
            return event;
        };
        let decompressed_len = decompressed.len();
        let decompressed_body = String::from_utf8_lossy(&decompressed).to_string();

        event.data["body"] = Value::String(decompressed_body);
        event.data["body_hex"] = Value::String(hex::encode(&decompressed));
        event.data["has_body"] = Value::Bool(decompressed_len > 0);
        event.data["content_length"] = json!(decompressed_len);
        event.data["decompressed"] = Value::Bool(true);
        event.data["original_content_encoding"] = Value::String(encoding);
        event.data["decompressed_body_size"] = json!(decompressed_len);

        if let Some(headers) = event.data.get_mut("headers").and_then(Value::as_object_mut) {
            headers.remove("content-encoding");
            headers.remove("Content-Encoding");
            headers.remove("content-length");
            headers.remove("Content-Length");
        }

        event
    }
}

#[async_trait]
impl Analyzer for HTTPDecompressor {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let processed = stream.map(Self::process_event);
        Ok(Box::pin(processed))
    }
}

fn content_encoding(data: &Value) -> Option<String> {
    let headers = data.get("headers")?.as_object()?;
    headers
        .iter()
        .find(|(key, _)| key.eq_ignore_ascii_case("content-encoding"))
        .and_then(|(_, value)| value.as_str())
        .map(|value| {
            value
                .split(',')
                .next()
                .unwrap_or(value)
                .trim()
                .to_ascii_lowercase()
        })
        .filter(|encoding| {
            matches!(
                encoding.as_str(),
                "gzip" | "x-gzip" | "deflate" | "br" | "brotli" | "zstd" | "zstandard"
            )
        })
}

fn is_chunked(data: &Value) -> bool {
    if data
        .get("is_chunked")
        .and_then(Value::as_bool)
        .unwrap_or(false)
    {
        return true;
    }
    let Some(headers) = data.get("headers").and_then(Value::as_object) else {
        return false;
    };
    headers.iter().any(|(key, value)| {
        key.eq_ignore_ascii_case("transfer-encoding")
            && value
                .as_str()
                .is_some_and(|v| v.to_ascii_lowercase().contains("chunked"))
    })
}

fn decode_chunked(bytes: &[u8]) -> Option<Vec<u8>> {
    let cursor = Cursor::new(bytes);
    let mut decoder = chunked_transfer::Decoder::new(cursor);
    let mut out = Vec::new();
    decoder.read_to_end(&mut out).ok()?;
    Some(out)
}

fn http_body_bytes(data: &Value) -> Option<Vec<u8>> {
    data.get("body_hex")
        .and_then(Value::as_str)
        .and_then(|value| hex::decode(value).ok())
        .or_else(|| {
            data.get("body")
                .and_then(Value::as_str)
                .map(http_body_string_to_bytes)
        })
}

fn decompress_body(encoding: &str, body: &[u8]) -> Result<Vec<u8>, std::io::Error> {
    match encoding {
        "gzip" | "x-gzip" => read_all(GzDecoder::new(Cursor::new(body))),
        "deflate" => read_all(ZlibDecoder::new(Cursor::new(body)))
            .or_else(|_| read_all(DeflateDecoder::new(Cursor::new(body)))),
        "br" | "brotli" => read_all(brotli::Decompressor::new(Cursor::new(body), 4096)),
        "zstd" | "zstandard" => {
            zstd::stream::decode_all(Cursor::new(body)).map_err(std::io::Error::other)
        }
        _ => Ok(body.to_vec()),
    }
}

fn read_all<R: Read>(mut reader: R) -> Result<Vec<u8>, std::io::Error> {
    let mut out = Vec::new();
    reader.read_to_end(&mut out)?;
    Ok(out)
}

fn http_body_string_to_bytes(data: &str) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(data.len());
    for ch in data.chars() {
        let code = ch as u32;
        if code <= 0xff {
            bytes.push(code as u8);
        } else {
            let mut buf = [0u8; 4];
            bytes.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
        }
    }
    bytes
}

#[cfg(test)]
mod tests {
    use super::*;
    use flate2::Compression;
    use flate2::write::{DeflateEncoder, GzEncoder, ZlibEncoder};
    use std::io::Write;

    fn http_response(body: Vec<u8>, encoding: &str) -> Event {
        Event::new(
            "http_parser".to_string(),
            123,
            "agent".to_string(),
            json!({
                "tid": 7,
                "message_type": "response",
                "status_code": 200,
                "headers": {
                    "content-encoding": encoding,
                    "content-type": "text/event-stream"
                },
                "body": bytes_to_http_body_string(&body),
                "has_body": true,
                "is_chunked": false
            }),
        )
    }

    fn bytes_to_http_body_string(bytes: &[u8]) -> String {
        bytes.iter().map(|b| char::from(*b)).collect()
    }

    #[test]
    fn decompresses_gzip_response_body() {
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder
            .write_all(b"data: {\"usage\":{\"input_tokens\":1}}\n\n")
            .unwrap();
        let event =
            HTTPDecompressor::process_event(http_response(encoder.finish().unwrap(), "gzip"));

        assert_eq!(event.data["decompressed"], true);
        assert_eq!(
            event.data["body"].as_str().unwrap(),
            "data: {\"usage\":{\"input_tokens\":1}}\n\n"
        );
        assert!(event.data["headers"].get("content-encoding").is_none());
    }

    #[test]
    fn decompresses_zlib_and_raw_deflate() {
        let mut zlib = ZlibEncoder::new(Vec::new(), Compression::default());
        zlib.write_all(b"zlib-body").unwrap();
        let event =
            HTTPDecompressor::process_event(http_response(zlib.finish().unwrap(), "deflate"));
        assert_eq!(event.data["body"].as_str().unwrap(), "zlib-body");

        let mut raw = DeflateEncoder::new(Vec::new(), Compression::default());
        raw.write_all(b"raw-body").unwrap();
        let event =
            HTTPDecompressor::process_event(http_response(raw.finish().unwrap(), "deflate"));
        assert_eq!(event.data["body"].as_str().unwrap(), "raw-body");
    }

    #[test]
    fn decompresses_brotli_and_zstd_response_bodies() {
        let mut br = Vec::new();
        {
            let mut encoder = brotli::CompressorWriter::new(&mut br, 4096, 5, 22);
            encoder.write_all(b"brotli-body").unwrap();
        }
        let event = HTTPDecompressor::process_event(http_response(br, "br"));
        assert_eq!(event.data["body"].as_str().unwrap(), "brotli-body");

        let zstd = zstd::stream::encode_all(Cursor::new(b"zstd-body"), 1).unwrap();
        let event = HTTPDecompressor::process_event(http_response(zstd, "zstd"));
        assert_eq!(event.data["body"].as_str().unwrap(), "zstd-body");
    }

    #[test]
    fn leaves_requests_and_unknown_encodings_unchanged() {
        let mut request = http_response(b"abc".to_vec(), "gzip");
        request.data["message_type"] = Value::String("request".to_string());
        assert_eq!(
            HTTPDecompressor::process_event(request).data["body"].as_str(),
            Some("abc")
        );

        let event = http_response(b"abc".to_vec(), "identity");
        assert!(
            HTTPDecompressor::process_event(event)
                .data
                .get("decompressed")
                .is_none()
        );
    }

    #[test]
    fn prefers_body_hex_for_non_utf8_compressed_payloads() {
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder
            .write_all(b"data: {\"usage\":{\"total_tokens\":7}}\n\n")
            .unwrap();
        let compressed = encoder.finish().unwrap();
        let mut event = http_response(Vec::new(), "gzip");
        event.data["body"] = Value::String("\u{fffd}\u{fffd}".to_string());
        event.data["body_hex"] = Value::String(hex::encode(compressed));

        let event = HTTPDecompressor::process_event(event);

        assert_eq!(
            event.data["body"].as_str().unwrap(),
            "data: {\"usage\":{\"total_tokens\":7}}\n\n"
        );
        assert_eq!(
            hex::decode(event.data["body_hex"].as_str().unwrap()).unwrap(),
            b"data: {\"usage\":{\"total_tokens\":7}}\n\n"
        );
    }
}
