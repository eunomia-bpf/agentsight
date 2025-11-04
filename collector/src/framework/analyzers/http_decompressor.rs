use super::{Analyzer, AnalyzerError};
use super::event::HTTPEvent;
use crate::framework::runners::EventStream;
use crate::framework::core::Event;
use async_trait::async_trait;
use futures::stream::StreamExt;
use flate2::read::GzDecoder;
use std::io::Read;

/// HTTP Decompressor Analyzer that decompresses gzip/deflate encoded HTTP response bodies
pub struct HTTPDecompressor {
    /// Flag to keep the raw compressed data alongside decompressed data
    keep_compressed: bool,
}

impl HTTPDecompressor {
    /// Create a new HTTPDecompressor with default settings
    pub fn new() -> Self {
        HTTPDecompressor {
            keep_compressed: false,
        }
    }

    /// Keep the compressed data in the event (adds a compressed_body field)
    pub fn keep_compressed(mut self) -> Self {
        self.keep_compressed = true;
        self
    }

    /// Check if the HTTP event has gzip encoding
    fn has_gzip_encoding(http_event: &HTTPEvent) -> bool {
        http_event.headers.get("content-encoding")
            .map(|v| v.to_lowercase().contains("gzip"))
            .unwrap_or(false)
    }

    /// Check if the HTTP event has deflate encoding
    fn has_deflate_encoding(http_event: &HTTPEvent) -> bool {
        http_event.headers.get("content-encoding")
            .map(|v| v.to_lowercase().contains("deflate"))
            .unwrap_or(false)
    }

    /// Decode JSON-escaped string to raw bytes (handles the eBPF output format)
    fn decode_json_escaped_string(s: &str) -> Vec<u8> {
        let mut result = Vec::new();
        for c in s.chars() {
            let cp = c as u32;
            if cp < 256 {
                result.push(cp as u8);
            } else {
                // This came from valid UTF-8 in binary data
                let utf8_bytes = c.to_string().into_bytes();
                result.extend_from_slice(&utf8_bytes);
            }
        }
        result
    }

    /// Try to decompress gzip data
    fn decompress_gzip(data: &[u8]) -> Result<String, String> {
        let mut decoder = GzDecoder::new(data);
        let mut decompressed = Vec::new();

        decoder.read_to_end(&mut decompressed)
            .map_err(|e| format!("Gzip decompression failed: {}", e))?;

        String::from_utf8(decompressed)
            .map_err(|e| format!("UTF-8 conversion failed: {}", e))
    }

    /// Try to decompress deflate data
    fn decompress_deflate(data: &[u8]) -> Result<String, String> {
        use flate2::read::DeflateDecoder;
        let mut decoder = DeflateDecoder::new(data);
        let mut decompressed = Vec::new();

        decoder.read_to_end(&mut decompressed)
            .map_err(|e| format!("Deflate decompression failed: {}", e))?;

        String::from_utf8(decompressed)
            .map_err(|e| format!("UTF-8 conversion failed: {}", e))
    }

    /// Handle chunked transfer encoding - extract the actual data from chunks
    fn extract_from_chunked(body: &str) -> Option<Vec<u8>> {
        // Parse chunked transfer encoding format:
        // <chunk-size-hex>\r\n<chunk-data>\r\n...
        let mut result = Vec::new();
        let mut remaining = body;

        loop {
            // Find the first \r\n which separates chunk size from data
            if let Some(newline_pos) = remaining.find("\r\n") {
                let chunk_size_str = &remaining[..newline_pos];

                // Parse chunk size as hex
                let chunk_size = match usize::from_str_radix(chunk_size_str.trim(), 16) {
                    Ok(size) => size,
                    Err(_) => return None, // Invalid chunk size
                };

                // If chunk size is 0, we've reached the end
                if chunk_size == 0 {
                    break;
                }

                // Extract chunk data
                let data_start = newline_pos + 2; // Skip \r\n
                if data_start + chunk_size > remaining.len() {
                    return None; // Incomplete chunk
                }

                let chunk_data = &remaining[data_start..data_start + chunk_size];
                result.extend_from_slice(&Self::decode_json_escaped_string(chunk_data));

                // Move to next chunk (skip chunk data and trailing \r\n)
                remaining = &remaining[data_start + chunk_size + 2..];
            } else {
                break;
            }
        }

        if result.is_empty() {
            None
        } else {
            Some(result)
        }
    }

    /// Process an HTTP event and decompress if needed
    fn process_http_event(
        mut event: Event,
        keep_compressed: bool,
    ) -> Event {
        // Try to deserialize as HTTPEvent
        let http_event: HTTPEvent = match serde_json::from_value(event.data.clone()) {
            Ok(h) => h,
            Err(_) => return event, // Not an HTTP event, pass through
        };

        // Only process responses with body
        if http_event.message_type != "response" || http_event.body.is_none() {
            return event;
        }

        let body = http_event.body.as_ref().unwrap();
        let is_gzip = Self::has_gzip_encoding(&http_event);
        let is_deflate = Self::has_deflate_encoding(&http_event);

        if !is_gzip && !is_deflate {
            return event; // No compression
        }

        // Extract bytes from the body
        let body_bytes = if http_event.is_chunked {
            // Handle chunked transfer encoding
            match Self::extract_from_chunked(body) {
                Some(bytes) => bytes,
                None => {
                    // Failed to parse chunks, try direct decoding
                    Self::decode_json_escaped_string(body)
                }
            }
        } else {
            Self::decode_json_escaped_string(body)
        };

        // Try to decompress
        let decompressed = if is_gzip {
            Self::decompress_gzip(&body_bytes)
        } else {
            Self::decompress_deflate(&body_bytes)
        };

        match decompressed {
            Ok(decompressed_text) => {
                // Update the event data with decompressed body
                if let Some(data) = event.data.as_object_mut() {
                    // Update body with decompressed content
                    data.insert("body".to_string(), serde_json::json!(decompressed_text));

                    // Optionally keep the compressed data
                    if keep_compressed {
                        data.insert("compressed_body".to_string(), serde_json::json!(body));
                    }

                    // Add decompression metadata
                    data.insert("decompressed".to_string(), serde_json::json!(true));
                    data.insert("original_encoding".to_string(),
                        serde_json::json!(if is_gzip { "gzip" } else { "deflate" }));
                    data.insert("decompressed_size".to_string(),
                        serde_json::json!(decompressed_text.len()));
                    data.insert("compressed_size".to_string(),
                        serde_json::json!(body_bytes.len()));
                }
                event
            }
            Err(_err) => {
                // Decompression failed, pass through original event
                // Optionally add error metadata
                if let Some(data) = event.data.as_object_mut() {
                    data.insert("decompression_failed".to_string(), serde_json::json!(true));
                }
                event
            }
        }
    }
}

#[async_trait]
impl Analyzer for HTTPDecompressor {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let keep_compressed = self.keep_compressed;

        let processed_stream = stream.map(move |event| {
            // Only process HTTP parser events
            if event.source == "http_parser" {
                Self::process_http_event(event, keep_compressed)
            } else {
                event // Pass through other events
            }
        });

        Ok(Box::pin(processed_stream))
    }

    fn name(&self) -> &str {
        "HTTPDecompressor"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_extract_from_chunked() {
        // Test chunked transfer encoding with simple text
        let chunked_data = "e\r\ntest data here\r\n0\r\n\r\n";
        let result = HTTPDecompressor::extract_from_chunked(chunked_data);
        assert!(result.is_some());
        let bytes = result.unwrap();
        assert_eq!(bytes, b"test data here");
    }

    #[test]
    fn test_has_gzip_encoding() {
        let mut headers = HashMap::new();
        headers.insert("content-encoding".to_string(), "gzip".to_string());

        let event = HTTPEvent::new(
            1,
            "response".to_string(),
            "HTTP/1.1 200 OK".to_string(),
            None,
            None,
            Some("HTTP/1.1".to_string()),
            Some(200),
            Some("OK".to_string()),
            headers,
            Some("test".to_string()),
            100,
            true,
            false,
            None,
            "ssl".to_string(),
        );

        assert!(HTTPDecompressor::has_gzip_encoding(&event));
    }

    #[test]
    fn test_has_deflate_encoding() {
        let mut headers = HashMap::new();
        headers.insert("content-encoding".to_string(), "deflate".to_string());

        let event = HTTPEvent::new(
            1,
            "response".to_string(),
            "HTTP/1.1 200 OK".to_string(),
            None,
            None,
            Some("HTTP/1.1".to_string()),
            Some(200),
            Some("OK".to_string()),
            headers,
            Some("test".to_string()),
            100,
            true,
            false,
            None,
            "ssl".to_string(),
        );

        assert!(HTTPDecompressor::has_deflate_encoding(&event));
    }

    #[test]
    fn test_decompress_gzip_real_data() {
        use flate2::write::GzEncoder;
        use flate2::Compression;
        use std::io::Write as IoWrite;

        // Create actual gzip compressed data
        let original_text = "Hello, this is test data for gzip decompression!";
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(original_text.as_bytes()).unwrap();
        let compressed = encoder.finish().unwrap();

        // Decompress using our function
        let result = HTTPDecompressor::decompress_gzip(&compressed);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), original_text);
    }
}
