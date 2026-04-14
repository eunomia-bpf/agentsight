//! LLM API Message Format Parser
//!
//! This module provides structured parsing for LLM API request and response bodies.
//!
//! # Supported APIs
//!
//! ## OpenAI Chat Completions
//! - Endpoint: `/v1/chat/completions`, `/v1/completions`
//! - Request: model, messages, temperature, max_tokens, stream, etc.
//! - Response: id, choices, usage, model, etc.
//!
//! ## Anthropic Messages
//! - Endpoint: `/v1/messages`
//! - Request: model, messages, max_tokens, system, stream, etc.
//! - Response: id, content, usage, model, stop_reason, etc.
//!
//! # Example
//!
//! ```rust,ignore
//! use agentsight::analyzer::message::{MessageParser, ParsedApiMessage};
//!
//! let parser = MessageParser::new();
//!
//! // Parse based on API path
//! let path = "/v1/chat/completions";
//! let request_body: serde_json::Value = serde_json::from_str(request_json)?;
//! let response_body: serde_json::Value = serde_json::from_str(response_json)?;
//!
//! if let Some(parsed) = parser.parse_by_path(path, Some(&request_body), Some(&response_body)) {
//!     match parsed {
//!         ParsedApiMessage::OpenAICompletion { request, response } => {
//!             println!("OpenAI completion parsed");
//!         }
//!         ParsedApiMessage::AnthropicMessage { request, response } => {
//!             println!("Anthropic message parsed");
//!         }
//!     }
//! }
//! ```

mod anthropic;
mod openai;
pub mod types;

pub use anthropic::AnthropicParser;
pub use openai::OpenAIParser;
pub use types::*;

use crate::parser::sse::ParsedSseEvent;

/// Unified message format parser for multiple LLM providers
///
/// Provides a single entry point for parsing both OpenAI and Anthropic
/// API request/response bodies based on the API endpoint path.
pub struct MessageParser;

impl MessageParser {
    /// Create a new message parser
    pub fn new() -> Self {
        MessageParser
    }

    /// Parse request/response bodies based on API path
    ///
    /// Automatically detects the LLM provider based on the request path:
    /// - Paths containing `/v1/messages` → Anthropic
    /// - Paths containing `/v1/chat/completions` or `/v1/completions` → OpenAI
    ///
    /// # Arguments
    /// * `path` - The HTTP request path (e.g., "/v1/chat/completions")
    /// * `request_body` - Optional JSON body from the HTTP request
    /// * `response_body` - Optional JSON body from the HTTP response
    ///
    /// # Returns
    /// * `Some(ParsedApiMessage)` if the path matches a known provider and parsing succeeds
    /// * `None` if the path doesn't match or both bodies fail to parse
    ///
    /// # Example
    /// ```rust,ignore
    /// let parser = MessageParser::new();
    /// let parsed = parser.parse_by_path(
    ///     "/v1/chat/completions",
    ///     Some(&request_json),
    ///     Some(&response_json),
    /// );
    /// ```
    pub fn parse_by_path(
        &self,
        path: &str,
        request_body: Option<&serde_json::Value>,
        response_body: Option<&serde_json::Value>,
    ) -> Option<ParsedApiMessage> {
        // Try Anthropic first (more specific path)
        if AnthropicParser::matches_path(path) {
            let request = request_body.and_then(AnthropicParser::parse_request);
            let response = response_body.and_then(AnthropicParser::parse_response);

            // Return Some only if at least one was parsed
            if request.is_some() || response.is_some() {
                return Some(ParsedApiMessage::AnthropicMessage { request, response });
            }
        }

        // Try OpenAI
        if OpenAIParser::matches_path(path) {
            let request = request_body.and_then(OpenAIParser::parse_request);
            let response = response_body.and_then(OpenAIParser::parse_response);

            // Return Some only if at least one was parsed
            if request.is_some() || response.is_some() {
                return Some(ParsedApiMessage::OpenAICompletion { request, response });
            }
        }

        log::warn!("Path '{}' does not match any known LLM API endpoint", path);
        None
    }

    /// Parse request body and SSE events based on API path
    ///
    /// This method handles streaming responses where the response is delivered
    /// via Server-Sent Events (SSE) instead of a single JSON body.
    /// SSE events are converted to a JSON array and passed to parse_response.
    ///
    /// # Arguments
    /// * `path` - The HTTP request path (e.g., "/v1/chat/completions")
    /// * `request_body` - Optional JSON body from the HTTP request
    /// * `sse_events` - Slice of SSE events from the streaming response
    ///
    /// # Returns
    /// * `Some(ParsedApiMessage)` if parsing succeeds
    /// * `None` if the path doesn't match or parsing fails
    pub fn parse_by_path_with_sse(
        &self,
        path: &str,
        request_body: Option<&serde_json::Value>,
        sse_events: &[ParsedSseEvent],
    ) -> Option<ParsedApiMessage> {
        // Convert SSE events to JSON array
        let chunks: Vec<serde_json::Value> = sse_events
            .iter()
            .filter(|e| !e.is_done())
            .filter_map(|e| {
                let data = String::from_utf8_lossy(e.data());
                serde_json::from_str(&data).ok()
            })
            .collect();

        let response_body = if chunks.is_empty() {
            None
        } else {
            Some(serde_json::Value::Array(chunks))
        };

        // Use parse_by_path with the converted response body
        self.parse_by_path(path, request_body, response_body.as_ref())
    }

    /// Detect provider from path without parsing
    ///
    /// # Arguments
    /// * `path` - The HTTP request path
    ///
    /// # Returns
    /// * `Some("anthropic")` for Anthropic paths
    /// * `Some("openai")` for OpenAI paths
    /// * `None` for unknown paths
    pub fn detect_provider(path: &str) -> Option<&'static str> {
        if AnthropicParser::matches_path(path) {
            Some("anthropic")
        } else if OpenAIParser::matches_path(path) {
            Some("openai")
        } else {
            None
        }
    }

    /// Check if a path matches any known LLM API endpoint
    pub fn is_llm_api_path(path: &str) -> bool {
        AnthropicParser::matches_path(path) || OpenAIParser::matches_path(path)
    }
}

impl Default for MessageParser {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_openai_by_path() {
        let parser = MessageParser::new();

        let request = serde_json::json!({
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        });

        let response = serde_json::json!({
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Hi there!"},
                "finish_reason": "stop"
            }]
        });

        let result = parser.parse_by_path("/v1/chat/completions", Some(&request), Some(&response));
        assert!(result.is_some());

        match result.unwrap() {
            ParsedApiMessage::OpenAICompletion {
                request: req,
                response: resp,
            } => {
                assert!(req.is_some());
                assert!(resp.is_some());
                assert_eq!(req.unwrap().model, "gpt-4");
                assert_eq!(resp.unwrap().id, "chatcmpl-123");
            }
            _ => panic!("Expected OpenAICompletion"),
        }
    }

    #[test]
    fn test_parse_anthropic_by_path() {
        let parser = MessageParser::new();

        let request = serde_json::json!({
            "model": "claude-3-opus-20240229",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": "Hello"}]
        });

        let response = serde_json::json!({
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hi there!"}],
            "model": "claude-3-opus-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 5}
        });

        let result = parser.parse_by_path("/v1/messages", Some(&request), Some(&response));
        assert!(result.is_some());

        match result.unwrap() {
            ParsedApiMessage::AnthropicMessage {
                request: req,
                response: resp,
            } => {
                assert!(req.is_some());
                assert!(resp.is_some());
                assert_eq!(req.unwrap().model, "claude-3-opus-20240229");
                assert_eq!(resp.unwrap().id, "msg_123");
            }
            _ => panic!("Expected AnthropicMessage"),
        }
    }

    #[test]
    fn test_parse_with_only_request() {
        let parser = MessageParser::new();

        let request = serde_json::json!({
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        });

        let result = parser.parse_by_path("/v1/chat/completions", Some(&request), None);
        assert!(result.is_some());

        match result.unwrap() {
            ParsedApiMessage::OpenAICompletion { request: req, response: resp } => {
                assert!(req.is_some());
                assert!(resp.is_none());
            }
            _ => panic!("Expected OpenAICompletion"),
        }
    }

    #[test]
    fn test_parse_with_only_response() {
        let parser = MessageParser::new();

        let response = serde_json::json!({
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello!"}],
            "model": "claude-3-opus-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 5}
        });

        let result = parser.parse_by_path("/v1/messages", None, Some(&response));
        assert!(result.is_some());

        match result.unwrap() {
            ParsedApiMessage::AnthropicMessage { request: req, response: resp } => {
                assert!(req.is_none());
                assert!(resp.is_some());
            }
            _ => panic!("Expected AnthropicMessage"),
        }
    }

    #[test]
    fn test_unknown_path_returns_none() {
        let parser = MessageParser::new();

        let body = serde_json::json!({"model": "gpt-4"});

        let result = parser.parse_by_path("/v1/embeddings", Some(&body), None);
        assert!(result.is_none());
    }

    #[test]
    fn test_detect_provider() {
        assert_eq!(MessageParser::detect_provider("/v1/messages"), Some("anthropic"));
        assert_eq!(
            MessageParser::detect_provider("/v1/chat/completions"),
            Some("openai")
        );
        assert_eq!(MessageParser::detect_provider("/v1/completions"), Some("openai"));
        assert_eq!(MessageParser::detect_provider("/v1/embeddings"), None);
    }

    #[test]
    fn test_is_llm_api_path() {
        assert!(MessageParser::is_llm_api_path("/v1/messages"));
        assert!(MessageParser::is_llm_api_path("/v1/chat/completions"));
        assert!(MessageParser::is_llm_api_path("/v1/completions"));
        assert!(!MessageParser::is_llm_api_path("/v1/embeddings"));
        assert!(!MessageParser::is_llm_api_path("/health"));
    }

    #[test]
    fn test_parsed_api_message_methods() {
        let openai_msg = ParsedApiMessage::OpenAICompletion {
            request: Some(OpenAIRequest {
                model: "gpt-4".to_string(),
                messages: vec![],
                temperature: None,
                max_tokens: None,
                stream: Some(true),
                top_p: None,
                n: None,
                stop: None,
                presence_penalty: None,
                frequency_penalty: None,
                user: None,
                tools: None,
                tool_choice: None,
                response_format: None,
                seed: None,
                logprobs: None,
                top_logprobs: None,
                parallel_tool_calls: None,
            }),
            response: None,
        };

        assert_eq!(openai_msg.provider(), "openai");
        assert_eq!(openai_msg.model(), Some("gpt-4"));
        assert_eq!(openai_msg.is_streaming(), Some(true));
    }

    #[test]
    fn test_full_url_paths() {
        let parser = MessageParser::new();

        // Should work with full URLs too
        assert!(MessageParser::is_llm_api_path(
            "https://api.openai.com/v1/chat/completions"
        ));
        assert!(MessageParser::is_llm_api_path(
            "https://api.anthropic.com/v1/messages"
        ));
    }
}
