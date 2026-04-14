//! Anthropic token data extraction

use serde_json::Value;
use super::super::data::{TokenData, MessageTokenData, ResponseTokenData};
use super::utils::extract_model_from_json;

/// Extract token data from Anthropic format JSON
pub fn extract_token_data(
    request_json: Option<&Value>,
    response_json: Option<&Value>,
) -> Option<TokenData> {
    let model = extract_model_from_json(request_json, response_json)
        .unwrap_or_else(|| "unknown".to_string());

    let mut token_data = TokenData::new("anthropic", model);
    let mut has_content = false;

    // Extract from request
    if let Some(req) = request_json {
        // Extract system prompt
        if let Some(system) = req.get("system") {
            let system_text = match system {
                Value::String(s) => Some(s.clone()),
                Value::Array(blocks) => {
                    let text: String = blocks
                        .iter()
                        .filter_map(|b| b.get("text").and_then(|t| t.as_str()))
                        .collect::<Vec<_>>()
                        .join("\n");
                    if text.is_empty() { None } else { Some(text) }
                }
                _ => None,
            };
            if let Some(text) = system_text {
                token_data.system_prompt = Some(text);
                has_content = true;
            }
        }

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

    // Extract from response
    if let Some(resp) = response_json {
        // Extract content blocks
        if let Some(content) = resp.get("content").and_then(|c| c.as_array()) {
            for block in content {
                let block_type = block.get("type").and_then(|t| t.as_str());
                
                match block_type {
                    Some("text") => {
                        if let Some(text) = block.get("text").and_then(|t| t.as_str()) {
                            if !text.is_empty() {
                                token_data.response_content.push(ResponseTokenData {
                                    content: text.to_string(),
                                });
                                has_content = true;
                            }
                        }
                    }
                    Some("tool_use") => {
                        let name = block.get("name").and_then(|n| n.as_str()).unwrap_or("unknown");
                        if let Some(input) = block.get("input") {
                            if let Ok(input_str) = serde_json::to_string(input) {
                                token_data.tool_calls.push(format!("{}: {}", name, input_str));
                                has_content = true;
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
    }

    if has_content {
        Some(token_data)
    } else {
        None
    }
}

/// Extract role and content from Anthropic message JSON
fn extract_message(msg: &Value) -> Option<(String, String)> {
    let role = msg.get("role").and_then(|r| r.as_str())?;
    let content = extract_content(msg.get("content"))?;
    
    if content.is_empty() {
        None
    } else {
        Some((role.to_string(), content))
    }
}

/// Extract text content from Anthropic content field (string or array)
fn extract_content(content: Option<&Value>) -> Option<String> {
    match content? {
        Value::String(s) => {
            if s.is_empty() {
                None
            } else {
                Some(s.clone())
            }
        }
        Value::Array(blocks) => {
            let text: String = blocks
                .iter()
                .filter_map(|b| {
                    if b.get("type").and_then(|t| t.as_str()) == Some("text") {
                        b.get("text").and_then(|t| t.as_str())
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
    fn test_extract_anthropic_request() {
        let request = serde_json::json!({
            "model": "claude-3-opus",
            "system": "You are Claude",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.provider, "anthropic");
        assert_eq!(data.model, "claude-3-opus");
        assert_eq!(data.system_prompt, Some("You are Claude".to_string()));
        assert_eq!(data.request_messages.len(), 1);
    }

    #[test]
    fn test_extract_anthropic_response() {
        let response = serde_json::json!({
            "model": "claude-3-opus",
            "content": [
                {"type": "text", "text": "Hello!"}
            ]
        });

        let token_data = extract_token_data(None, Some(&response));
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.response_content.len(), 1);
        assert_eq!(data.response_content[0].content, "Hello!");
    }

    #[test]
    fn test_extract_system_array() {
        let request = serde_json::json!({
            "model": "claude-3-opus",
            "system": [
                {"type": "text", "text": "You are Claude"},
                {"type": "text", "text": "Be helpful"}
            ],
            "messages": []
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.system_prompt, Some("You are Claude\nBe helpful".to_string()));
    }

    #[test]
    fn test_extract_content_array() {
        let request = serde_json::json!({
            "model": "claude-3-opus",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "text", "text": "World"}
                ]
            }]
        });

        let token_data = extract_token_data(Some(&request), None);
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.request_messages.len(), 1);
        assert_eq!(data.request_messages[0].content, "Hello World");
    }

    #[test]
    fn test_extract_tool_use() {
        let response = serde_json::json!({
            "model": "claude-3-opus",
            "content": [
                {"type": "tool_use", "name": "get_weather", "input": {"city": "Beijing"}}
            ]
        });

        let token_data = extract_token_data(None, Some(&response));
        assert!(token_data.is_some());

        let data = token_data.unwrap();
        assert_eq!(data.tool_calls.len(), 1);
        assert!(data.tool_calls[0].contains("get_weather"));
    }

    #[test]
    fn test_empty_content_returns_none() {
        let request = serde_json::json!({"model": "claude-3-opus"});
        let result = extract_token_data(Some(&request), None);
        assert!(result.is_none());
    }
}
