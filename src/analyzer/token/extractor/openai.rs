//! OpenAI token data extraction

use serde_json::Value;
use super::super::data::{TokenData, MessageTokenData, ResponseTokenData};
use super::utils::extract_model_from_json;

/// Extract token data from OpenAI format JSON
pub fn extract_token_data(
    request_json: Option<&Value>,
    response_json: Option<&Value>,
) -> Option<TokenData> {
    let model = extract_model_from_json(request_json, response_json)
        .unwrap_or_else(|| "unknown".to_string());

    let mut token_data = TokenData::new("openai", model);
    let mut has_content = false;

    // Extract from request
    if let Some(req) = request_json {
        // Extract messages
        if let Some(messages) = req.get("messages").and_then(|m| m.as_array()) {
            for msg in messages {
                if let Some((role, content)) = extract_message(msg) {
                    token_data.request_messages.push(MessageTokenData { role, content });
                    has_content = true;
                }
            }
        }

        // Extract tools
        if let Some(tools) = req.get("tools").and_then(|t| t.as_array()) {
            for tool in tools {
                if let Ok(tool_str) = serde_json::to_string(tool) {
                    token_data.tools.push(tool_str);
                    has_content = true;
                }
            }
        }
    }

    // Extract from response using shared logic
    if let Some((content, reasoning, tool_calls)) = extract_response_content(response_json) {
        if !content.is_empty() {
            token_data.response_content.push(ResponseTokenData { content });
            has_content = true;
        }
        if let Some(r) = reasoning {
            token_data.reasoning_content = Some(r);
            has_content = true;
        }
        for tool_call in tool_calls {
            token_data.tool_calls.push(tool_call);
            has_content = true;
        }
    }

    if has_content {
        Some(token_data)
    } else {
        None
    }
}

/// Extract response content from OpenAI format response JSON
/// 
/// Returns a tuple of (content, reasoning_content, tool_calls)
/// - content: The main response text
/// - reasoning_content: Optional reasoning/thinking content
/// - tool_calls: Vec of formatted tool call strings "name: arguments"
pub fn extract_response_content(
    response_json: Option<&Value>,
) -> Option<(String, Option<String>, Vec<String>)> {
    let resp = response_json?;
    let choices = resp.get("choices").and_then(|c| c.as_array())?;
    
    let mut content = String::new();
    let mut reasoning = None;
    let mut tool_calls = Vec::new();
    let mut has_data = false;

    for choice in choices {
        // Support both "message" (standard response) and "delta" (SSE streaming) formats
        let msg_or_delta = choice.get("message").or_else(|| choice.get("delta"));
        
        if let Some(msg) = msg_or_delta {
            // Extract content
            if let Some(c) = msg.get("content").and_then(|c| c.as_str()) {
                if !c.is_empty() {
                    content.push_str(c);
                    has_data = true;
                }
            }

            // Extract reasoning_content
            if let Some(r) = msg.get("reasoning_content").and_then(|r| r.as_str()) {
                if !r.is_empty() {
                    // For SSE chunks, accumulate reasoning content
                    reasoning = match reasoning {
                        Some(existing) => Some(existing + r),
                        None => Some(r.to_string()),
                    };
                    has_data = true;
                }
            }

            // Extract tool_calls - only extract function name and arguments
            if let Some(calls) = msg.get("tool_calls").and_then(|t| t.as_array()) {
                for tool_call in calls {
                    if let Some(func) = tool_call.get("function") {
                        let name = func.get("name").and_then(|n| n.as_str()).unwrap_or("");
                        let arguments = func.get("arguments").and_then(|a| a.as_str()).unwrap_or("");
                        let tool_content = format!("{}: {}", name, arguments);
                        if !tool_content.is_empty() {
                            tool_calls.push(tool_content);
                            has_data = true;
                        }
                    }
                }
            }
        }
    }

    if has_data {
        Some((content, reasoning, tool_calls))
    } else {
        None
    }
}

/// Extract role and content from OpenAI message JSON
fn extract_message(msg: &Value) -> Option<(String, String)> {
    let role = msg.get("role").and_then(|r| r.as_str())?;
    let content = extract_content(msg.get("content"))?;
    
    if content.is_empty() {
        None
    } else {
        Some((role.to_string(), content))
    }
}

/// Extract text content from OpenAI content field (string or array)
fn extract_content(content: Option<&Value>) -> Option<String> {
    match content? {
        Value::String(s) => {
            if s.is_empty() {
                None
            } else {
                Some(s.clone())
            }
        }
        Value::Array(parts) => {
            let text: String = parts
                .iter()
                .filter_map(|p| {
                    if p.get("type").and_then(|t| t.as_str()) == Some("text") {
                        p.get("text").and_then(|t| t.as_str())
                    } else {
                        None
                    }
                })
                .collect::<Vec<_>>()
                .join("");
            
            if text.is_empty() {
                None
            } else {
                Some(text)
            }
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_openai_request() {
        let request = serde_json::json!({
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"}
            ]
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.provider, "openai");
        assert_eq!(data.model, "gpt-4");
        assert_eq!(data.request_messages.len(), 2);
        assert_eq!(data.request_messages[0].role, "system");
        assert_eq!(data.request_messages[0].content, "You are helpful");
    }

    #[test]
    fn test_extract_openai_response() {
        let response = serde_json::json!({
            "model": "gpt-4",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hi there!"
                }
            }]
        });

        let token_data = extract_token_data(None, Some(&response));
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.response_content.len(), 1);
        assert_eq!(data.response_content[0].content, "Hi there!");
    }

    #[test]
    fn test_extract_with_tools() {
        let request = serde_json::json!({
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "What's the weather?"}],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info"
                }
            }]
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.tools.len(), 1);
    }

    #[test]
    fn test_extract_reasoning_content() {
        let response = serde_json::json!({
            "model": "qwen",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "The answer is 42",
                    "reasoning_content": "Let me think about this..."
                }
            }]
        });

        let token_data = extract_token_data(None, Some(&response));
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.reasoning_content, Some("Let me think about this...".to_string()));
    }

    #[test]
    fn test_extract_content_array() {
        let request = serde_json::json!({
            "model": "gpt-4-vision",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "http://example.com/image.jpg"}}
                ]
            }]
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.request_messages.len(), 1);
        assert_eq!(data.request_messages[0].content, "What's in this image?");
    }

    #[test]
    fn test_empty_content_returns_none() {
        let request = serde_json::json!({"model": "gpt-4"});
        let result = extract_token_data(Some(&request), None);
        assert!(result.is_none());
    }
}
