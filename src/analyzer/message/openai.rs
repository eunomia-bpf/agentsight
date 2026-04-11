//! OpenAI Chat Completions API parser
//!
//! This module provides parsing functionality for OpenAI Chat Completions API
//! request and response bodies.
//!
//! # Supported Endpoints
//! - `/v1/chat/completions`
//! - `/v1/completions` (legacy)
//!
//! # Example
//! ```rust,ignore
//! use agentsight::analyzer::message::{OpenAIParser, OpenAIRequest, OpenAIResponse};
//!
//! let parser = OpenAIParser;
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
//!     println!("Completion ID: {}", response.id);
//! }
//! ```

use super::types::{OpenAIRequest, OpenAIResponse, OpenAIChoice, OpenAIChatMessage, MessageRole, OpenAIContent, OpenAiSseChunk};

/// Parser for OpenAI Chat Completions API
///
/// Provides methods to parse JSON request and response bodies
/// from OpenAI-compatible APIs.
pub struct OpenAIParser;

impl OpenAIParser {
    /// Parse an OpenAI Chat Completions request body from JSON
    ///
    /// # Arguments
    /// * `body` - The JSON value representing the request body
    ///
    /// # Returns
    /// * `Some(OpenAIRequest)` if parsing succeeds
    /// * `None` if the JSON doesn't match the expected format
    ///
    /// # Example
    /// ```rust,ignore
    /// let json = serde_json::json!({
    ///     "model": "gpt-4",
    ///     "messages": [{"role": "user", "content": "Hello"}]
    /// });
    /// let request = OpenAIParser::parse_request(&json);
    /// ```
    pub fn parse_request(body: &serde_json::Value) -> Option<OpenAIRequest> {
        // Quick validation - must have model and messages fields
        if !body.get("model").is_some() || !body.get("messages").is_some() {
            log::trace!("OpenAI request missing required fields: model or messages");
            return None;
        }

        match serde_json::from_value::<OpenAIRequest>(body.clone()) {
            Ok(request) => {
                log::debug!(
                    "Parsed OpenAI request: model={}, messages={}",
                    request.model,
                    request.messages.len()
                );
                Some(request)
            }
            Err(e) => {
                log::trace!("Failed to parse OpenAI request: {}", e);
                None
            }
        }
    }

    /// Parse an OpenAI Chat Completions response body from JSON
    ///
    /// # Arguments
    /// * `body` - The JSON value representing the response body
    ///
    /// # Returns
    /// * `Some(OpenAIResponse)` if parsing succeeds
    /// * `None` if the JSON doesn't match the expected format
    ///
    /// # Example
    /// ```rust,ignore
    /// let json = serde_json::json!({
    ///     "id": "chatcmpl-123",
    ///     "object": "chat.completion",
    ///     "created": 1677652288,
    ///     "model": "gpt-4",
    ///     "choices": [...]
    /// });
    /// let response = OpenAIParser::parse_response(&json);
    /// ```
    pub fn parse_response(body: &serde_json::Value) -> Option<OpenAIResponse> {
        // Try standard response format first (has id and choices)
        if body.get("id").is_some() && body.get("choices").is_some() {
            match serde_json::from_value::<OpenAIResponse>(body.clone()) {
                Ok(response) => {
                    log::debug!(
                        "Parsed OpenAI response: id={}, model={}, choices={}",
                        response.id,
                        response.model,
                        response.choices.len()
                    );
                    return Some(response);
                }
                Err(e) => {
                    log::trace!("Failed to parse OpenAI response: {}", e);
                }
            }
        }

        // Try SSE chunks array format (body is an array of SSE chunks)
        if let Some(chunks) = body.as_array() {
            return Self::aggregate_sse_chunks(chunks);
        }

        None
    }

    /// Aggregate SSE chunks into a single OpenAIResponse
    fn aggregate_sse_chunks(chunks: &[serde_json::Value]) -> Option<OpenAIResponse> {
        use std::collections::HashMap;

        let mut content_parts: Vec<String> = Vec::new();
        let mut reasoning_parts: Vec<String> = Vec::new();
        let mut finish_reason: Option<String> = None;
        let mut first_chunk: Option<&serde_json::Value> = None;
        // Merge tool_call deltas by index: index -> (id, name, arguments_accumulated)
        let mut tool_call_map: HashMap<u32, (String, String, String)> = HashMap::new();

        for chunk in chunks {
            // Try to parse as OpenAiSseChunk
            if let Ok(sse_chunk) = serde_json::from_value::<OpenAiSseChunk>(chunk.clone()) {
                if first_chunk.is_none() {
                    first_chunk = Some(chunk);
                }
                // Extract content delta for aggregation
                for choice in &sse_chunk.choices {
                    if let Some(content) = &choice.delta.content {
                        if !content.is_empty() {
                            content_parts.push(content.clone());
                        }
                    }
                    // Extract reasoning_content delta
                    if let Some(reasoning) = &choice.delta.reasoning_content {
                        if !reasoning.is_empty() {
                            reasoning_parts.push(reasoning.clone());
                        }
                    }
                    // Extract and merge tool_call deltas by index
                    if let Some(calls) = &choice.delta.tool_calls {
                        for tc in calls {
                            let idx = tc.get("index").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
                            let entry = tool_call_map.entry(idx)
                                .or_insert_with(|| (String::new(), String::new(), String::new()));
                            if let Some(id) = tc.get("id").and_then(|v| v.as_str()) {
                                if !id.is_empty() {
                                    entry.0 = id.to_string();
                                }
                                // 空字符串不覆盖已有的 id
                            }
                            if let Some(func) = tc.get("function") {
                                if let Some(name) = func.get("name").and_then(|v| v.as_str()) {
                                    entry.1 = name.to_string();
                                }
                                if let Some(args) = func.get("arguments").and_then(|v| v.as_str()) {
                                    entry.2.push_str(args);
                                }
                            }
                        }
                    }
                    if finish_reason.is_none() && choice.finish_reason.is_some() {
                        finish_reason = choice.finish_reason.clone();
                    }
                }
            }
        }

        // Build merged tool_calls
        let tool_calls = if tool_call_map.is_empty() {
            None
        } else {
            let mut sorted_indices: Vec<u32> = tool_call_map.keys().cloned().collect();
            sorted_indices.sort();
            let merged: Vec<serde_json::Value> = sorted_indices.into_iter().filter_map(|idx| {
                tool_call_map.remove(&idx).map(|(id, name, arguments)| {
                    serde_json::json!({
                        "id": id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": arguments
                        }
                    })
                })
            }).collect();
            if merged.is_empty() { None } else { Some(merged) }
        };

        // Build aggregated response from chunks
        first_chunk.and_then(|first| {
            serde_json::from_value::<OpenAiSseChunk>(first.clone()).ok().map(|chunk| {
                let combined_content = content_parts.join("");
                let combined_reasoning = if reasoning_parts.is_empty() {
                    None
                } else {
                    Some(reasoning_parts.join(""))
                };
                OpenAIResponse {
                    id: chunk.id,
                    object: "chat.completion".to_string(),
                    created: chunk.created,
                    model: chunk.model,
                    choices: vec![OpenAIChoice {
                        index: 0,
                        message: OpenAIChatMessage {
                            role: MessageRole::Assistant,
                            content: Some(OpenAIContent::Text(combined_content)),
                            reasoning_content: combined_reasoning,
                            refusal: None,
                            function_call: None,
                            tool_calls,
                            tool_call_id: None,
                            name: None,
                            annotations: None,
                            audio: None,
                        },
                        finish_reason,
                        logprobs: None,
                    }],
                    usage: None,
                    system_fingerprint: chunk.system_fingerprint,
                }
            })
        })
    }

    /// Check if a path matches OpenAI API endpoints
    ///
    /// # Arguments
    /// * `path` - The HTTP request path
    ///
    /// # Returns
    /// * `true` if the path matches OpenAI endpoints
    pub fn matches_path(path: &str) -> bool {
        path.contains("/v1/chat/completions") || path.contains("/v1/completions")
    }
}

impl Default for OpenAIParser {
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
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ]
        });

        let request = OpenAIParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert_eq!(request.model, "gpt-4");
        assert_eq!(request.messages.len(), 1);
    }

    #[test]
    fn test_parse_request_with_options() {
        let json = serde_json::json!({
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me a joke."}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": true,
            "top_p": 0.9
        });

        let request = OpenAIParser::parse_request(&json);
        assert!(request.is_some());

        let request = request.unwrap();
        assert_eq!(request.model, "gpt-4-turbo");
        assert_eq!(request.messages.len(), 2);
        assert_eq!(request.temperature, Some(0.7));
        assert_eq!(request.max_tokens, Some(1000));
        assert_eq!(request.stream, Some(true));
        assert_eq!(request.top_p, Some(0.9));
    }

    #[test]
    fn test_parse_request_missing_model() {
        let json = serde_json::json!({
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        });

        let request = OpenAIParser::parse_request(&json);
        assert!(request.is_none());
    }

    #[test]
    fn test_parse_request_missing_messages() {
        let json = serde_json::json!({
            "model": "gpt-4"
        });

        let request = OpenAIParser::parse_request(&json);
        assert!(request.is_none());
    }

    #[test]
    fn test_parse_response_simple() {
        let json = serde_json::json!({
            "id": "chatcmpl-123456",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm doing well, thank you for asking."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        });

        let response = OpenAIParser::parse_response(&json);
        assert!(response.is_some());

        let response = response.unwrap();
        assert_eq!(response.id, "chatcmpl-123456");
        assert_eq!(response.model, "gpt-4");
        assert_eq!(response.choices.len(), 1);

        let usage = response.usage.unwrap();
        assert_eq!(usage.prompt_tokens, 10);
        assert_eq!(usage.completion_tokens, 15);
        assert_eq!(usage.total_tokens, 25);
    }

    #[test]
    fn test_parse_response_missing_id() {
        let json = serde_json::json!({
            "object": "chat.completion",
            "choices": []
        });

        let response = OpenAIParser::parse_response(&json);
        assert!(response.is_none());
    }

    #[test]
    fn test_parse_response_missing_choices() {
        let json = serde_json::json!({
            "id": "chatcmpl-123",
            "object": "chat.completion"
        });

        let response = OpenAIParser::parse_response(&json);
        assert!(response.is_none());
    }

    #[test]
    fn test_matches_path() {
        assert!(OpenAIParser::matches_path("/v1/chat/completions"));
        assert!(OpenAIParser::matches_path("/v1/completions"));
        assert!(OpenAIParser::matches_path("https://api.openai.com/v1/chat/completions"));
        assert!(!OpenAIParser::matches_path("/v1/messages"));
        assert!(!OpenAIParser::matches_path("/v1/embeddings"));
    }

    #[test]
    fn test_parse_response_with_tool_calls() {
        let json = serde_json::json!({
            "id": "chatcmpl-789",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": null,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": "{\"location\": \"Boston\"}"
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        });

        let response = OpenAIParser::parse_response(&json);
        assert!(response.is_some());

        let response = response.unwrap();
        assert_eq!(response.choices[0].finish_reason, Some("tool_calls".to_string()));
    }
}
