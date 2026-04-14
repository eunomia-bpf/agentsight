//! Utility functions for token data extraction

use serde_json::Value;
use super::Provider;

/// Detect provider from API endpoint path and/or JSON content
///
/// For standard paths like `/v1/chat/completions` or `/v1/messages`,
/// the provider is determined by the path itself.
///
/// For compatible mode paths like `/compatible-mode/v1/chat/completions`,
/// the provider is detected from the JSON content structure.
///
/// # Arguments
/// * `path` - The API endpoint path
/// * `request_json` - Optional request body for content-based detection
pub fn detect_provider(path: &str, request_json: Option<&Value>) -> Option<Provider> {
    // First, try to detect from path
    if let Some(provider) = detect_provider_from_path(path) {
        return Some(provider);
    }

    // For compatible mode or unknown paths, try to detect from JSON content
    if let Some(json) = request_json {
        return detect_provider_from_json(json);
    }

    None
}

/// Detect provider from API endpoint path only
///
/// This function only checks the URL path and does not inspect JSON content.
/// Returns `None` for compatible mode paths that require JSON content detection.
pub fn detect_provider_from_path(path: &str) -> Option<Provider> {
    // Check for compatible mode paths first - these need JSON content detection
    if path.contains("/compatible-mode") || path.contains("/compat-mode") {
        return None;
    }

    if path.contains("/v1/messages") && !path.contains("chat") {
        Some(Provider::Anthropic)
    } else if path.contains("/v1/chat/completions") || path.contains("/v1/completions") {
        Some(Provider::OpenAI)
    } else {
        None
    }
}

/// Detect provider from JSON content structure
///
/// This function analyzes the JSON content to determine the protocol format:
/// - Anthropic: Has "system" as top-level field or "max_tokens" (required in Anthropic)
/// - OpenAI: Has "messages" with "function_call" or "response_format"
///
/// # Arguments
/// * `json` - The request JSON body
pub fn detect_provider_from_json(json: &Value) -> Option<Provider> {
    // Check for Anthropic-specific fields
    // Anthropic has "system" as a top-level field (not inside messages)
    // Note: "max_tokens" alone is not unique to Anthropic (OpenAI also has it)
    if json.get("system").is_some() {
        return Some(Provider::Anthropic);
    }

    // Check for OpenAI-specific fields
    // OpenAI has "response_format", "seed", "parallel_tool_calls"
    if json.get("response_format").is_some()
        || json.get("seed").is_some()
        || json.get("parallel_tool_calls").is_some()
    {
        return Some(Provider::OpenAI);
    }

    // Check messages structure
    if let Some(messages) = json.get("messages").and_then(|m| m.as_array()) {
        // Look at the first message to determine format
        if let Some(first_msg) = messages.first() {
            // OpenAI messages often have "name" in function/tool contexts
            if first_msg.get("name").is_some() {
                return Some(Provider::OpenAI);
            }

            // Check for tool_calls which is OpenAI-specific
            if first_msg.get("tool_calls").is_some() {
                return Some(Provider::OpenAI);
            }
        }
    }

    // Default to OpenAI for compatible mode if we can't determine
    // This is because most compatible endpoints follow OpenAI format
    Some(Provider::OpenAI)
}

/// Extract model name from JSON (check request first, then response)
pub fn extract_model_from_json(
    request: Option<&Value>,
    response: Option<&Value>,
) -> Option<String> {
    request
        .and_then(|r| r.get("model").and_then(|m| m.as_str()))
        .or_else(|| response.and_then(|r| r.get("model").and_then(|m| m.as_str())))
        .map(|s| s.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_openai_path() {
        assert_eq!(
            detect_provider_from_path("/v1/chat/completions"),
            Some(Provider::OpenAI)
        );
        assert_eq!(
            detect_provider_from_path("/v1/completions"),
            Some(Provider::OpenAI)
        );
    }

    #[test]
    fn test_detect_anthropic_path() {
        assert_eq!(
            detect_provider_from_path("/v1/messages"),
            Some(Provider::Anthropic)
        );
    }

    #[test]
    fn test_detect_unknown_path() {
        assert_eq!(detect_provider_from_path("/v1/embeddings"), None);
        assert_eq!(detect_provider_from_path("/v1/models"), None);
    }

    #[test]
    fn test_extract_model_from_request() {
        let request = serde_json::json!({"model": "gpt-4"});
        let model = extract_model_from_json(Some(&request), None);
        assert_eq!(model, Some("gpt-4".to_string()));
    }

    #[test]
    fn test_extract_model_from_response() {
        let response = serde_json::json!({"model": "claude-3-opus"});
        let model = extract_model_from_json(None, Some(&response));
        assert_eq!(model, Some("claude-3-opus".to_string()));
    }

    #[test]
    fn test_extract_model_request_priority() {
        let request = serde_json::json!({"model": "gpt-4"});
        let response = serde_json::json!({"model": "gpt-3.5"});
        let model = extract_model_from_json(Some(&request), Some(&response));
        assert_eq!(model, Some("gpt-4".to_string()));
    }

    #[test]
    fn test_detect_provider_with_compatible_mode() {
        // Compatible mode path with OpenAI format JSON
        let openai_request = serde_json::json!({
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider("/compatible-mode/v1/chat/completions", Some(&openai_request));
        assert_eq!(provider, Some(Provider::OpenAI));

        // Compatible mode path with Anthropic format JSON
        let anthropic_request = serde_json::json!({
            "model": "claude-3-opus",
            "max_tokens": 1024,
            "system": "You are Claude",
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider("/compatible-mode/v1/chat/completions", Some(&anthropic_request));
        assert_eq!(provider, Some(Provider::Anthropic));
    }

    #[test]
    fn test_detect_provider_from_json_openai() {
        let request = serde_json::json!({
            "model": "gpt-4",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider_from_json(&request);
        assert_eq!(provider, Some(Provider::OpenAI));
    }

    #[test]
    fn test_detect_provider_from_json_anthropic() {
        let request = serde_json::json!({
            "model": "claude-3-opus",
            "max_tokens": 1024,
            "system": "You are Claude",
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider_from_json(&request);
        assert_eq!(provider, Some(Provider::Anthropic));
    }

    #[test]
    fn test_detect_provider_from_path_takes_priority() {
        // Even with Anthropic-like JSON, standard OpenAI path should return OpenAI
        let request = serde_json::json!({
            "model": "claude-3-opus",
            "max_tokens": 1024,
            "system": "You are Claude",
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider("/v1/chat/completions", Some(&request));
        assert_eq!(provider, Some(Provider::OpenAI));

        // Even with OpenAI-like JSON, standard Anthropic path should return Anthropic
        let request = serde_json::json!({
            "model": "gpt-4",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": "Hello"}]
        });
        let provider = detect_provider("/v1/messages", Some(&request));
        assert_eq!(provider, Some(Provider::Anthropic));
    }
}
