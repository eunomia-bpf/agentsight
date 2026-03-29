//! Extracted token data types for local tokenization
//!
//! These types represent the actual text content extracted from LLM API
//! request/response bodies that would be counted as tokens.

use serde::{Deserialize, Serialize};

/// Extracted token data from request/response for local tokenization
///
/// This struct contains the actual text content that would be counted as tokens,
/// allowing for local token counting and analysis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenData {
    /// Provider type (openai, anthropic, etc.)
    pub provider: String,
    /// Model name
    pub model: String,
    /// Request messages that contribute to input tokens
    pub request_messages: Vec<MessageTokenData>,
    /// System prompt (if present)
    pub system_prompt: Option<String>,
    /// Tools definitions (if present)
    pub tools: Vec<String>,
    /// Response content that contributes to output tokens
    pub response_content: Vec<ResponseTokenData>,
    /// Response reasoning content (if present, e.g., Qwen reasoning models)
    pub reasoning_content: Option<String>,
    /// Tool calls in response (if present)
    pub tool_calls: Vec<String>,
}

impl TokenData {
    /// Create a new TokenData instance
    pub fn new(provider: impl Into<String>, model: impl Into<String>) -> Self {
        Self {
            provider: provider.into(),
            model: model.into(),
            request_messages: Vec::new(),
            system_prompt: None,
            tools: Vec::new(),
            response_content: Vec::new(),
            reasoning_content: None,
            tool_calls: Vec::new(),
        }
    }

    /// Add a request message
    pub fn add_request_message(mut self, role: impl Into<String>, content: impl Into<String>) -> Self {
        self.request_messages.push(MessageTokenData {
            role: role.into(),
            content: content.into(),
        });
        self
    }

    /// Set system prompt
    pub fn with_system_prompt(mut self, prompt: impl Into<String>) -> Self {
        self.system_prompt = Some(prompt.into());
        self
    }

    /// Add a tool definition
    pub fn add_tool(mut self, tool_json: impl Into<String>) -> Self {
        self.tools.push(tool_json.into());
        self
    }

    /// Add response content
    pub fn add_response_content(mut self, content: impl Into<String>) -> Self {
        self.response_content.push(ResponseTokenData {
            content: content.into(),
        });
        self
    }

    /// Set reasoning content
    pub fn with_reasoning_content(mut self, content: impl Into<String>) -> Self {
        self.reasoning_content = Some(content.into());
        self
    }

    /// Add a tool call
    pub fn add_tool_call(mut self, tool_call_json: impl Into<String>) -> Self {
        self.tool_calls.push(tool_call_json.into());
        self
    }

    /// Get all request text content combined
    pub fn request_text(&self) -> String {
        let mut parts = Vec::new();
        
        if let Some(ref system) = self.system_prompt {
            parts.push(format!("system: {}", system));
        }
        
        for msg in &self.request_messages {
            parts.push(format!("{}: {}", msg.role, msg.content));
        }
        
        for tool in &self.tools {
            parts.push(format!("tool: {}", tool));
        }
        
        parts.join("\n")
    }

    /// Get all response text content combined
    pub fn response_text(&self) -> String {
        let mut parts = Vec::new();
        
        if let Some(ref reasoning) = self.reasoning_content {
            parts.push(format!("reasoning: {}", reasoning));
        }
        
        for content in &self.response_content {
            parts.push(content.content.clone());
        }
        
        for tool_call in &self.tool_calls {
            parts.push(format!("tool_call: {}", tool_call));
        }
        
        parts.join("\n")
    }

    /// Get all text content (request + response)
    pub fn all_text(&self) -> String {
        format!("{}\n{}", self.request_text(), self.response_text())
    }

    /// Get messages grouped by role
    pub fn messages_by_role(&self) -> std::collections::HashMap<String, Vec<&MessageTokenData>> {
        let mut map: std::collections::HashMap<String, Vec<&MessageTokenData>> = 
            std::collections::HashMap::new();
        
        for msg in &self.request_messages {
            map.entry(msg.role.clone())
                .or_insert_with(Vec::new)
                .push(msg);
        }
        
        map
    }

    /// Count messages by role
    pub fn count_by_role(&self) -> std::collections::HashMap<String, usize> {
        let mut counts: std::collections::HashMap<String, usize> = 
            std::collections::HashMap::new();
        
        for msg in &self.request_messages {
            *counts.entry(msg.role.clone()).or_insert(0) += 1;
        }
        
        counts
    }

    /// Check if there are any messages
    pub fn has_messages(&self) -> bool {
        !self.request_messages.is_empty()
    }

    /// Get total character count (rough estimate for token calculation)
    pub fn total_chars(&self) -> usize {
        let mut total = 0;
        
        if let Some(ref system) = self.system_prompt {
            total += system.len();
        }
        
        for msg in &self.request_messages {
            total += msg.content.len();
        }
        
        for tool in &self.tools {
            total += tool.len();
        }
        
        for content in &self.response_content {
            total += content.content.len();
        }
        
        if let Some(ref reasoning) = self.reasoning_content {
            total += reasoning.len();
        }
        
        for tool_call in &self.tool_calls {
            total += tool_call.len();
        }
        
        total
    }
}

/// Message token data for request messages
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageTokenData {
    /// Message role (system, user, assistant, tool)
    pub role: String,
    /// Message content
    pub content: String,
}

/// Response token data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseTokenData {
    /// Response content text
    pub content: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_data_builder() {
        let data = TokenData::new("openai", "gpt-4")
            .with_system_prompt("You are a helpful assistant")
            .add_request_message("user", "Hello")
            .add_response_content("Hi there!");

        assert_eq!(data.provider, "openai");
        assert_eq!(data.model, "gpt-4");
        assert_eq!(data.system_prompt, Some("You are a helpful assistant".to_string()));
        assert_eq!(data.request_messages.len(), 1);
        assert_eq!(data.response_content.len(), 1);
    }

    #[test]
    fn test_token_data_text_extraction() {
        let data = TokenData::new("openai", "gpt-4")
            .with_system_prompt("System prompt")
            .add_request_message("user", "Hello")
            .add_response_content("Hi!");

        let request_text = data.request_text();
        assert!(request_text.contains("System prompt"));
        assert!(request_text.contains("Hello"));

        let response_text = data.response_text();
        assert!(response_text.contains("Hi!"));
    }
}
