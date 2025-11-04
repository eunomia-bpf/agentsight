use super::*;
use crate::framework::core::Event;
use crate::framework::analyzers::event::HTTPEvent;
use std::collections::HashMap;
use flate2::write::GzEncoder;
use flate2::Compression;
use std::io::Write;

#[cfg(test)]
mod http_decompressor_tests {
    use super::*;

    fn create_gzip_compressed_data(text: &str) -> String {
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(text.as_bytes()).unwrap();
        let compressed = encoder.finish().unwrap();

        // Convert to the format that comes from eBPF (simulating JSON escaped string)
        compressed.iter().map(|&b| {
            if b < 128 {
                (b as char).to_string()
            } else {
                format!("\\u{:04x}", b)
            }
        }).collect()
    }

    #[test]
    fn test_decompress_gzip_response() {
        // Create test data
        let original_text = r#"{"message":"Hello World","data":"This is test data"}"#;
        let compressed_body = create_gzip_compressed_data(original_text);

        // Create HTTP event with gzip encoding
        let mut headers = HashMap::new();
        headers.insert("content-encoding".to_string(), "gzip".to_string());
        headers.insert("content-type".to_string(), "application/json".to_string());

        let http_event = HTTPEvent::new(
            12345,
            "response".to_string(),
            "HTTP/1.1 200 OK".to_string(),
            None,
            None,
            Some("HTTP/1.1".to_string()),
            Some(200),
            Some("OK".to_string()),
            headers,
            Some(compressed_body.clone()),
            1000,
            true,
            false,
            None,
            "ssl".to_string(),
        );

        // Create Event from HTTPEvent
        let event_data = serde_json::to_value(&http_event).unwrap();
        let event = Event::new_with_timestamp(
            123456789,
            "http_parser".to_string(),
            12345,
            "curl".to_string(),
            event_data,
        );

        // Process the event
        let result = HTTPDecompressor::process_http_event(event.clone(), false);

        // Verify decompression
        assert!(result.data.get("decompressed").is_some());
        assert_eq!(result.data.get("decompressed").unwrap(), &serde_json::json!(true));

        // Check the decompressed body
        let body = result.data.get("body").and_then(|v| v.as_str());
        assert!(body.is_some(), "Decompressed body should exist");

        println!("Original text: {}", original_text);
        println!("Decompressed body: {}", body.unwrap());
    }

    #[test]
    fn test_pass_through_non_gzip_response() {
        // Create HTTP event without gzip encoding
        let mut headers = HashMap::new();
        headers.insert("content-type".to_string(), "application/json".to_string());

        let body_text = r#"{"message":"Hello World"}"#;
        let http_event = HTTPEvent::new(
            12345,
            "response".to_string(),
            "HTTP/1.1 200 OK".to_string(),
            None,
            None,
            Some("HTTP/1.1".to_string()),
            Some(200),
            Some("OK".to_string()),
            headers,
            Some(body_text.to_string()),
            100,
            true,
            false,
            None,
            "ssl".to_string(),
        );

        let event_data = serde_json::to_value(&http_event).unwrap();
        let event = Event::new_with_timestamp(
            123456789,
            "http_parser".to_string(),
            12345,
            "curl".to_string(),
            event_data,
        );

        // Process the event
        let result = HTTPDecompressor::process_http_event(event.clone(), false);

        // Should not have decompression flag
        assert!(result.data.get("decompressed").is_none());

        // Body should be unchanged
        let body = result.data.get("body").and_then(|v| v.as_str());
        assert_eq!(body, Some(body_text));
    }

    #[test]
    fn test_pass_through_request() {
        // Create HTTP request (should not be decompressed)
        let mut headers = HashMap::new();
        headers.insert("content-encoding".to_string(), "gzip".to_string());

        let http_event = HTTPEvent::new(
            12345,
            "request".to_string(), // Request, not response
            "POST /api HTTP/1.1".to_string(),
            Some("POST".to_string()),
            Some("/api".to_string()),
            Some("HTTP/1.1".to_string()),
            None,
            None,
            headers,
            Some("test".to_string()),
            100,
            true,
            false,
            None,
            "ssl".to_string(),
        );

        let event_data = serde_json::to_value(&http_event).unwrap();
        let event = Event::new_with_timestamp(
            123456789,
            "http_parser".to_string(),
            12345,
            "curl".to_string(),
            event_data,
        );

        // Process the event
        let result = HTTPDecompressor::process_http_event(event.clone(), false);

        // Should not be decompressed (requests are not decompressed)
        assert!(result.data.get("decompressed").is_none());
    }
}
