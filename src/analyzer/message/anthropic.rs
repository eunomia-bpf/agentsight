//! Anthropic Messages API parser
//!
//! This module provides parsing functionality for Anthropic Messages API
//! request and response bodies.
//!
//! # Supported Endpoints
//! - `/v1/messages`
//!
//! # Example
//! ```rust,ignore
//! use agentsight::analyzer::message::{AnthropicParser, AnthropicRequest, AnthropicResponse};
//!
//! let parser = AnthropicParser;
//!
//! // Parse request body
//! let request_json: serde_json::Value = serde_json::from_str(request_body)?;
//! if let Some(request) = parser.parse_request(&request_json) {
//!     println!("Model: {}", request.model);
//! }
//!
//! // Parse response body
//! let response_json: serde_json::Value = serde_json::from_str(response_body)?;
//! if let Some(response) = parser.parse_response(&response_json) {
//!     println!("Message ID: {}", response.id);
//! }
//! ```

use super::types::{AnthropicRequest, AnthropicResponse, AnthropicContentBlock, AnthropicUsage, MessageRole, AnthropicSseEvent};

/// Parser for Anthropic Messages API
///
/// Provides methods to parse JSON request and response bodies
/// from Anthropic-compatible APIs.
pub struct AnthropicParser;

impl AnthropicParser {
    /// Parse an Anthropic Messages request body from JSON
    ///
    /// # Arguments
    /// * `body` - The JSON value representing the request body
    ///
    /// # Returns
    /// * `Some(AnthropicRequest)` if parsing succeeds
    /// * `None` if the JSON doesn't match the expected format
    ///
    /// # Example
    /// ```rust,ignore
    /// let json = serde_json::json!({
    ///     "model": "claude-3-opus-20240229",
    ///     "max_tokens": 1024,
    ///     "messages": [{"role": "user", "content": "Hello"}]
    /// });
    /// let request = AnthropicParser::parse_request(&json);
    /// ```
    pub fn parse_request(body: &serde_json::Value) -> Option<AnthropicRequest> {
        // Quick validation - must have model, messages, and max_tokens fields
        if !body.get("model").is_some()
            || !body.get("messages").is_some()
            || !body.get("max_tokens").is_some()
        {
            log::trace!("Anthropic request missing required fields: model, messages, or max_tokens");
            return None;
        }

        match serde_json::from_value::<AnthropicRequest>(body.clone()) {
            Ok(request) => {
                log::debug!(
                    "Parsed Anthropic request: model={}, messages={}, max_tokens={}",
                    request.model,
                    request.messages.len(),
                    request.max_tokens
                );
                Some(request)
            }
            Err(e) => {
                log::trace!("Failed to parse Anthropic request: {}", e);
                None
            }
        }
    }

    /// Parse an Anthropic Messages response body from JSON
    ///
    /// # Arguments
    /// * `body` - The JSON value representing the response body
    ///
    /// # Returns
    /// * `Some(AnthropicResponse)` if parsing succeeds
    /// * `None` if the JSON doesn't match the expected format
    ///
    /// # Example
    /// ```rust,ignore
    /// let json = serde_json::json!({
    ///     "id": "msg_123",
    ///     "type": "message",
    ///     "role": "assistant",
    ///     "content": [{"type": "text", "text": "Hello!"}],
    ///     "model": "claude-3-opus-20240229",
    ///     "usage": {"input_tokens": 10, "output_tokens": 5}
    /// });
    /// let response = AnthropicParser::parse_response(&json);
    /// ```
    pub fn parse_response(body: &serde_json::Value) -> Option<AnthropicResponse> {
        // Try standard response format first (has id, type="message", content)
        if body.get("id").is_some() 
            && body.get("type").and_then(|v| v.as_str()) == Some("message")
            && body.get("content").is_some() 
        {
            match serde_json::from_value::<AnthropicResponse>(body.clone()) {
                Ok(response) => {
                    log::debug!(
                        "Parsed Anthropic response: id={}, model={}, content_blocks={}",
                        response.id,
                        response.model,
                        response.content.len()
                    );
                    return Some(response);
                }
                Err(e) => {
                    log::trace!("Failed to parse Anthropic response: {}", e);
                }
            }
        }

        // Try SSE events array format (body is an array of SSE events)
        if let Some(events) = body.as_array() {
            return Self::aggregate_sse_events(events);
        }

        None
    }

    /// Aggregate SSE events into a single AnthropicResponse
    fn aggregate_sse_events(events: &[serde_json::Value]) -> Option<AnthropicResponse> {
        let mut content_parts: Vec<String> = Vec::new();
        let mut stop_reason: Option<String> = None;
        let mut usage: Option<AnthropicUsage> = None;
        let mut message_start: Option<AnthropicSseEvent> = None;

        for event_value in events {
            // Try to parse as AnthropicSseEvent
            if let Ok(sse_event) = serde_json::from_value::<AnthropicSseEvent>(event_value.clone()) {
                // Extract data for aggregation based on event type
                match &sse_event {
                    AnthropicSseEvent::MessageStart { message } => {
                        message_start = Some(sse_event.clone());
                        usage = Some(message.usage.clone());
                    }
                    AnthropicSseEvent::ContentBlockDelta { delta, .. } => {
                        use super::types::AnthropicSseDelta;
                        if let AnthropicSseDelta::TextDelta { text } = delta {
                            content_parts.push(text.clone());
                        }
                    }
                    AnthropicSseEvent::MessageDelta { delta, usage: delta_usage } => {
                        stop_reason = delta.stop_reason.clone();
                        if let Some(du) = delta_usage {
                            usage = Some(AnthropicUsage {
                                input_tokens: usage.as_ref().map(|u| u.input_tokens).unwrap_or(0),
                                output_tokens: du.output_tokens,
                                cache_creation_input_tokens: usage.as_ref().and_then(|u| u.cache_creation_input_tokens),
                                cache_read_input_tokens: usage.as_ref().and_then(|u| u.cache_read_input_tokens),
                            });
                        }
                    }
                    _ => {}
                }
            }
        }

        // Build aggregated response from message_start
        if let Some(AnthropicSseEvent::MessageStart { message }) = message_start {
            let combined_content = content_parts.join("");
            Some(AnthropicResponse {
                id: message.id,
                type_: "message".to_string(),
                role: MessageRole::Assistant,
                content: vec![AnthropicContentBlock::Text {
                    text: combined_content,
                    cache_control: None,
                }],
                model: message.model,
                stop_reason,
                stop_sequence: None,
                usage: usage.unwrap_or(AnthropicUsage {
                    input_tokens: 0,
                    output_tokens: 0,
                    cache_creation_input_tokens: None,
                    cache_read_input_tokens: None,
                }),
            })
        } else {
            None
        }
    }

    /// Check if a path matches Anthropic API endpoints
    ///
    /// # Arguments
    /// * `path` - The HTTP request path
    ///
    /// # Returns
    /// * `true` if the path matches Anthropic endpoints
    pub fn matches_path(path: &str) -> bool {
        path.contains("/v1/messages")
    }
}

impl Default for AnthropicParser {
    fn default() -> Self {
        Self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_request_simple() {
        let json = serde_json::json!({
            "model": "claude-3-opus-20240229",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ]
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert_eq!(request.model, "claude-3-opus-20240229");
        assert_eq!(request.max_tokens, 1024);
        assert_eq!(request.messages.len(), 1);
    }

    #[test]
    fn test_parse_request_with_system() {
        let json = serde_json::json!({
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2048,
            "system": "You are a helpful AI assistant.",
            "messages": [
                {"role": "user", "content": "Tell me a joke."}
            ],
            "temperature": 0.7,
            "stream": true
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert_eq!(request.model, "claude-3-sonnet-20240229");
        assert_eq!(request.max_tokens, 2048);
        assert!(request.system.is_some());
        assert_eq!(request.temperature, Some(0.7));
        assert_eq!(request.stream, Some(true));
    }

    #[test]
    fn test_parse_request_with_system_blocks() {
        let json = serde_json::json!({
            "model": "claude-3-opus-20240229",
            "max_tokens": 1024,
            "system": [
                {
                    "type": "text",
                    "text": "You are a helpful assistant.",
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert!(request.system.is_some());
    }

    #[test]
    fn test_parse_request_missing_model() {
        let json = serde_json::json!({
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_none());
    }

    #[test]
    fn test_parse_request_missing_max_tokens() {
        let json = serde_json::json!({
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_none());
    }

    #[test]
    fn test_parse_response_simple() {
        let json = serde_json::json!({
            "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! I'm doing well, thank you for asking."
                }
            ],
            "model": "claude-3-opus-20240229",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 12,
                "output_tokens": 15
            }
        });

        let response = AnthropicParser::parse_response(&json);
        assert!(response.is_some());

        let response = response.unwrap();
        assert_eq!(response.id, "msg_01XFDUDYJgAACzvnptvVoYEL");
        assert_eq!(response.model, "claude-3-opus-20240229");
        assert_eq!(response.content.len(), 1);
        assert_eq!(response.stop_reason, Some("end_turn".to_string()));
        assert_eq!(response.usage.input_tokens, 12);
        assert_eq!(response.usage.output_tokens, 15);
    }

    #[test]
    fn test_parse_response_with_cache_tokens() {
        let json = serde_json::json!({
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello!"}
            ],
            "model": "claude-3-opus-20240229",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_creation_input_tokens": 10,
                "cache_read_input_tokens": 20
            }
        });

        let response = AnthropicParser::parse_response(&json);
        assert!(response.is_some());

        let response = response.unwrap();
        assert_eq!(response.usage.input_tokens, 100);
        assert_eq!(response.usage.output_tokens, 50);
        assert_eq!(response.usage.cache_creation_input_tokens, Some(10));
        assert_eq!(response.usage.cache_read_input_tokens, Some(20));
    }

    #[test]
    fn test_parse_response_missing_id() {
        let json = serde_json::json!({
            "type": "message",
            "content": []
        });

        let response = AnthropicParser::parse_response(&json);
        assert!(response.is_none());
    }

    #[test]
    fn test_parse_response_wrong_type() {
        let json = serde_json::json!({
            "id": "msg_123",
            "type": "error",
            "content": []
        });

        let response = AnthropicParser::parse_response(&json);
        assert!(response.is_none());
    }

    #[test]
    fn test_matches_path() {
        assert!(AnthropicParser::matches_path("/v1/messages"));
        assert!(AnthropicParser::matches_path("https://api.anthropic.com/v1/messages"));
        assert!(!AnthropicParser::matches_path("/v1/chat/completions"));
        assert!(!AnthropicParser::matches_path("/v1/completions"));
    }

    #[test]
    fn test_parse_response_with_tool_use() {
        let json = serde_json::json!({
            "id": "msg_456",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll check the weather for you."
                },
                {
                    "type": "tool_use",
                    "id": "toolu_01A09q90qw90lq917835lhl",
                    "name": "get_weather",
                    "input": {"location": "San Francisco, CA"}
                }
            ],
            "model": "claude-3-opus-20240229",
            "stop_reason": "tool_use",
            "usage": {
                "input_tokens": 50,
                "output_tokens": 30
            }
        });

        let response = AnthropicParser::parse_response(&json);
        assert!(response.is_some());

        let response = response.unwrap();
        assert_eq!(response.content.len(), 2);
        assert_eq!(response.stop_reason, Some("tool_use".to_string()));
    }

    #[test]
    fn test_parse_request_with_content_blocks() {
        let json = serde_json::json!({
            "model": "claude-3-opus-20240229",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": "base64_encoded_data_here"
                            }
                        },
                        {
                            "type": "text",
                            "text": "What is in this image?"
                        }
                    ]
                }
            ]
        });

        let request = AnthropicParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert_eq!(request.messages.len(), 1);
    }
}
