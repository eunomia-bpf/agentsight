//! Token Parser - Extract token usage from SSE events
//!
//! This module provides functionality to extract LLM token usage information
//! from SSE (Server-Sent Events) streaming responses.
//!
//! Supported providers:
//! - OpenAI (GPT-4, GPT-3.5, etc.)
//! - Anthropic (Claude)
//! - Gemini
//!
//! # Example
//! ```rust,ignore
//! use agentsight::analyzer::token::{TokenParser, TokenUsage};
//! use agentsight::parser::ParsedSseEvent;
//!
//! let parser = TokenParser::new();
//! for event in sse_events {
//!     if let Some(usage) = parser.parse_event(&event) {
//!         println!("Tokens: {} in, {} out", usage.input_tokens, usage.output_tokens);
//!     }
//! }
//! ```

use super::{detect_provider_from_usage, extract_usage_object, LLMProvider, TokenUsage};
use crate::parser::sse::ParsedSseEvent;

/// Token parser for extracting usage from SSE events
pub struct TokenParser;

impl TokenParser {
    /// Create a new token parser
    pub fn new() -> Self {
        TokenParser
    }

    /// Parse token usage from a ParsedSseEvent
    ///
    /// Returns `Some(TokenUsage)` if the event contains usage information,
    /// `None` otherwise.
    pub fn parse_event(&self, event: &ParsedSseEvent) -> Option<TokenUsage> {
        // Skip done markers
        if event.is_done() {
            return None;
        }

        // Get event data as string
        let data = event.data();
        let data_str = std::str::from_utf8(data).ok()?;

        // Parse as JSON
        self.parse_data(data_str)
    }

    /// Parse token usage from raw SSE data string
    ///
    /// This is useful when you have raw SSE data without a ParsedSseEvent.
    pub fn parse_data(&self, data: &str) -> Option<TokenUsage> {
        // Skip done markers
        if data.trim() == "[DONE]" || data.trim() == "[END]" {
            return None;
        }

        // Parse as JSON
        let json: serde_json::Value = serde_json::from_str(data).ok()?;
        self.parse_json(&json).inspect(|_usage| {
            log::debug!("token usage parsed from data: {data}");
        })
    }

    /// Internal method to parse JSON and extract token usage
    pub fn parse_json(&self, json: &serde_json::Value) -> Option<TokenUsage> {
        // 1. Check for message_start event (Anthropic streaming)
        if json.get("type").and_then(|v| v.as_str()) == Some("message_start") {
            if let Some(message) = json.get("message") {
                if let Some(usage) = message.get("usage") {
                    return extract_usage_object(usage, LLMProvider::Anthropic, json);
                }
            }
        }

        // 2. Check for message_delta event (Anthropic streaming final)
        if json.get("type").and_then(|v| v.as_str()) == Some("message_delta") {
            if let Some(usage) = json.get("usage") {
                return extract_usage_object(usage, LLMProvider::Anthropic, json);
            }
        }

        // 3. Check for usage object directly (OpenAI and compatible APIs)
        if let Some(usage) = json.get("usage") {
            // Try to detect provider from content structure
            let provider = detect_provider_from_usage(usage);
            return extract_usage_object(usage, provider, json);
        }

        None
    }
}

impl Default for TokenParser {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Create a mock ParsedSseEvent for testing
    ///
    /// Note: SslEvent is large (~512KB), so we allocate it on the heap
    fn create_test_event(data: &str) -> ParsedSseEvent {
        use crate::probes::sslsniff::SslEvent;
        use std::rc::Rc;

        let ssl_event = Rc::new(SslEvent {
            source: 0,
            timestamp_ns: 1234567890,
            delta_ns: 0,
            pid: 1234,
            tid: 5678,
            uid: 0,
            len: data.len() as u32,
            rw: 0,
            comm: String::new(),
            buf: data.as_bytes().to_vec(),
            is_handshake: false,
            ssl_ptr: 0,
        });

        ParsedSseEvent::new(None, None, None, 0, data.len(), ssl_event)
    }

    #[test]
    fn test_parse_openai_usage() {
        let parser = TokenParser::new();
        let data = r#"{
            "id": "chatcmpl-123",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }"#;

        let event = create_test_event(data);
        let usage = parser.parse_event(&event);
        assert!(usage.is_some());

        let usage = usage.unwrap();
        assert_eq!(usage.input_tokens, 100);
        assert_eq!(usage.output_tokens, 50);
        assert_eq!(usage.total_tokens(), 150);
        assert_eq!(usage.provider, LLMProvider::OpenAI);
        assert_eq!(usage.model, Some("gpt-4".to_string()));
    }

    #[test]
    fn test_parse_anthropic_message_start() {
        let parser = TokenParser::new();
        let data = r#"{
            "type": "message_start",
            "message": {
                "id": "msg_123",
                "model": "claude-3-opus",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 0
                }
            }
        }"#;

        let event = create_test_event(data);
        let usage = parser.parse_event(&event);
        assert!(usage.is_some());

        let usage = usage.unwrap();
        assert_eq!(usage.input_tokens, 100);
        assert_eq!(usage.output_tokens, 0);
        assert_eq!(usage.provider, LLMProvider::Anthropic);
    }

    #[test]
    fn test_parse_anthropic_message_delta() {
        let parser = TokenParser::new();
        let data = r#"{
            "type": "message_delta",
            "delta": {},
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_creation_input_tokens": 10,
                "cache_read_input_tokens": 20
            }
        }"#;

        let event = create_test_event(data);
        let usage = parser.parse_event(&event);
        assert!(usage.is_some());

        let usage = usage.unwrap();
        assert_eq!(usage.input_tokens, 100);
        assert_eq!(usage.output_tokens, 50);
        assert_eq!(usage.cache_creation_input_tokens, Some(10));
        assert_eq!(usage.cache_read_input_tokens, Some(20));
        assert_eq!(usage.provider, LLMProvider::Anthropic);
    }

    #[test]
    fn test_parse_openai_sse_streaming() {
        let parser = TokenParser::new();
        let data = r#"{"choices":[],"object":"chat.completion.chunk","usage":{"prompt_tokens":61744,"completion_tokens":61,"total_tokens":61805},"created":1773640825,"model":"qwen3.5-plus","id":"chatcmpl-816f7538-0ac9-98c4-8259-9bade0c2cde7"}"#;

        let event = create_test_event(data);
        let usage = parser.parse_event(&event);
        assert!(usage.is_some(), "Should extract usage from SSE streaming data");

        let usage = usage.unwrap();
        assert_eq!(usage.input_tokens, 61744);
        assert_eq!(usage.output_tokens, 61);
        assert_eq!(usage.total_tokens(), 61805);
        assert_eq!(usage.provider, LLMProvider::OpenAI);
        assert_eq!(usage.model, Some("qwen3.5-plus".to_string()));
    }

    #[test]
    fn test_skip_done_marker() {
        let parser = TokenParser::new();

        let event = create_test_event("[DONE]");
        assert!(parser.parse_event(&event).is_none());

        let event = create_test_event("[END]");
        assert!(parser.parse_event(&event).is_none());
    }

    #[test]
    fn test_parse_no_usage() {
        let parser = TokenParser::new();
        let data = r#"{"choices":[{"delta":{"content":"Hello"}}]}"#;

        let event = create_test_event(data);
        assert!(parser.parse_event(&event).is_none());
    }

    #[test]
    fn test_parse_data_directly() {
        let parser = TokenParser::new();
        let data = r#"{"usage":{"prompt_tokens":10,"completion_tokens":5},"model":"gpt-3.5"}"#;

        let usage = parser.parse_data(data);
        assert!(usage.is_some());

        let usage = usage.unwrap();
        assert_eq!(usage.input_tokens, 10);
        assert_eq!(usage.output_tokens, 5);
    }
}
