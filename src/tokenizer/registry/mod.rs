//! Tokenizer registry with automatic model detection
//!
//! This module provides a unified registry for managing multiple tokenizers
//! and automatic model detection from request/response data.

use anyhow::{anyhow, Result};
use std::collections::HashMap;

use crate::analyzer::{OpenAIChatMessage, OpenAIRequest, OpenAIResponse, OpenAIChoice};
use crate::tokenizer::core::{ChatTemplateType, Tokenizer, ChatTokenCount};
use crate::tokenizer::model::TokenizerModel;

/// Token count breakdown for detailed analysis
#[derive(Debug, Clone)]
pub struct TokenCountBreakdown {
    /// Total tokens
    pub total: usize,
    /// Tokens from messages/prompt
    pub prompt_tokens: usize,
    /// Tokens from completion/response
    pub completion_tokens: usize,
    /// Per-message breakdown (for request)
    pub per_message_tokens: Vec<usize>,
    /// Per-choice breakdown (for response)
    pub per_choice_tokens: Vec<usize>,
    /// Formatted prompt (for debugging)
    pub formatted_prompt: Option<String>,
    /// Detected model used for tokenization
    pub detected_model: Option<String>,
}

/// Unified tokenizer registry with automatic model detection
///
/// This struct provides a high-level interface for token counting
/// with support for OpenAI request/response format and automatic
/// model detection from request/response data.
pub struct TokenizerRegistry {
    /// Map of model names to their tokenizers
    tokenizers: HashMap<String, Box<dyn Tokenizer>>,
    /// Default tokenizer to use when model is not found
    default_tokenizer: Option<Box<dyn Tokenizer>>,
    /// Default chat template type
    default_template_type: ChatTemplateType,
}

impl TokenizerRegistry {
    /// Create a new empty tokenizer registry
    pub fn new() -> Self {
        Self {
            tokenizers: HashMap::new(),
            default_tokenizer: None,
            default_template_type: ChatTemplateType::Qwen,
        }
    }

    /// Register a tokenizer for a specific model
    ///
    /// # Arguments
    /// * `model_name` - The model name to register (e.g., "gpt-4", "qwen2.5")
    /// * `tokenizer` - The tokenizer instance
    pub fn register(&mut self, model_name: impl Into<String>, tokenizer: Box<dyn Tokenizer>) {
        self.tokenizers.insert(model_name.into(), tokenizer);
    }

    /// Set the default tokenizer to use when model is not found
    pub fn set_default_tokenizer(&mut self, tokenizer: Box<dyn Tokenizer>) {
        self.default_tokenizer = Some(tokenizer);
    }

    /// Set the default chat template type
    pub fn set_default_template_type(&mut self, template_type: ChatTemplateType) {
        self.default_template_type = template_type;
    }

    /// Get or detect tokenizer for a model name
    fn get_tokenizer(&self, model_name: &str) -> Result<(&dyn Tokenizer, ChatTemplateType)> {
        // First, try exact match
        if let Some(tokenizer) = self.tokenizers.get(model_name) {
            let template_type = TokenizerModel::from_model_name(model_name)
                .map(|m| m.chat_template_type())
                .unwrap_or(self.default_template_type);
            return Ok((tokenizer.as_ref(), template_type));
        }

        // Try to detect model type from name
        if let Some(model_type) = TokenizerModel::from_model_name(model_name) {
            // Look for a registered tokenizer of the same type
            for (registered_name, tokenizer) in &self.tokenizers {
                if let Some(registered_type) = TokenizerModel::from_model_name(registered_name) {
                    if registered_type == model_type {
                        return Ok((tokenizer.as_ref(), model_type.chat_template_type()));
                    }
                }
            }
        }

        // Fall back to default tokenizer
        if let Some(ref default) = self.default_tokenizer {
            let template_type = TokenizerModel::from_model_name(model_name)
                .map(|m| m.chat_template_type())
                .unwrap_or(self.default_template_type);
            return Ok((default.as_ref(), template_type));
        }

        Err(anyhow!(
            "No tokenizer found for model '{}' and no default tokenizer set",
            model_name
        ))
    }

    /// Count tokens for an OpenAI request with automatic model detection
    pub fn count_request(&self, request: &OpenAIRequest) -> Result<TokenCountBreakdown> {
        let (tokenizer, template_type) = self.get_tokenizer(&request.model)?;
        let template = template_type.create_template();

        // Count message tokens
        let chat_count = super::count_chat_tokens(
            tokenizer,
            template.as_ref(),
            &request.messages,
        )?;

        let mut prompt_tokens = chat_count.total_tokens;

        // Count tools if present
        if let Some(ref tools) = request.tools {
            for tool in tools {
                let tool_json = serde_json::to_string(tool)?;
                prompt_tokens += tokenizer.count(&tool_json)?;
            }
        }

        // Count response_format if present
        if let Some(ref response_format) = request.response_format {
            let format_json = serde_json::to_string(response_format)?;
            prompt_tokens += tokenizer.count(&format_json)?;
        }

        Ok(TokenCountBreakdown {
            total: prompt_tokens,
            prompt_tokens,
            completion_tokens: 0,
            per_message_tokens: chat_count.per_message_tokens,
            per_choice_tokens: vec![],
            formatted_prompt: Some(chat_count.formatted_prompt),
            detected_model: Some(request.model.clone()),
        })
    }

    /// Count tokens for an OpenAI response
    pub fn count_response(&self, response: &OpenAIResponse) -> Result<TokenCountBreakdown> {
        let (tokenizer, _) = self.get_tokenizer(&response.model)?;
        let mut completion_tokens = 0;
        let mut per_choice_tokens = Vec::with_capacity(response.choices.len());

        for choice in &response.choices {
            let choice_tokens = self.count_choice(tokenizer, choice)?;
            completion_tokens += choice_tokens;
            per_choice_tokens.push(choice_tokens);
        }

        Ok(TokenCountBreakdown {
            total: completion_tokens,
            prompt_tokens: 0,
            completion_tokens,
            per_message_tokens: vec![],
            per_choice_tokens,
            formatted_prompt: None,
            detected_model: Some(response.model.clone()),
        })
    }

    /// Count tokens for a single choice
    fn count_choice(&self, tokenizer: &dyn Tokenizer, choice: &OpenAIChoice) -> Result<usize> {
        let mut tokens = 0;

        // Count content tokens
        if let Some(ref content) = choice.message.content {
            tokens += tokenizer.count(&content.as_text())?;
        }

        // Count reasoning_content if present
        if let Some(ref reasoning) = choice.message.reasoning_content {
            tokens += tokenizer.count(reasoning)?;
        }

        // Count tool_calls if present
        if let Some(ref tool_calls) = choice.message.tool_calls {
            for tool_call in tool_calls {
                let tool_json = serde_json::to_string(tool_call)?;
                tokens += tokenizer.count(&tool_json)?;
            }
        }

        // Count refusal if present
        if let Some(ref refusal) = choice.message.refusal {
            tokens += tokenizer.count(refusal)?;
        }

        // Count function_call if present (deprecated)
        if let Some(ref function_call) = choice.message.function_call {
            let func_json = serde_json::to_string(function_call)?;
            tokens += tokenizer.count(&func_json)?;
        }

        Ok(tokens)
    }

    /// Count tokens for a complete request-response pair
    pub fn count_conversation(
        &self,
        request: &OpenAIRequest,
        response: &OpenAIResponse,
    ) -> Result<TokenCountBreakdown> {
        let request_breakdown = self.count_request(request)?;
        let response_breakdown = self.count_response(response)?;

        Ok(TokenCountBreakdown {
            total: request_breakdown.prompt_tokens + response_breakdown.completion_tokens,
            prompt_tokens: request_breakdown.prompt_tokens,
            completion_tokens: response_breakdown.completion_tokens,
            per_message_tokens: request_breakdown.per_message_tokens,
            per_choice_tokens: response_breakdown.per_choice_tokens,
            formatted_prompt: request_breakdown.formatted_prompt,
            detected_model: request_breakdown.detected_model,
        })
    }

    /// Count tokens for a single message
    pub fn count_message(&self, model_name: &str, message: &OpenAIChatMessage) -> Result<usize> {
        let (tokenizer, template_type) = self.get_tokenizer(model_name)?;
        let template = template_type.create_template();

        let formatted = template.format_messages(&[message.clone()]);
        tokenizer.count(&formatted)
    }

    /// Get a registered tokenizer by model name
    pub fn get_registered_tokenizer(&self, model_name: &str) -> Option<&dyn Tokenizer> {
        self.tokenizers.get(model_name).map(|t| t.as_ref())
    }

    /// Check if a tokenizer is registered
    pub fn has_tokenizer(&self, model_name: &str) -> bool {
        self.tokenizers.contains_key(model_name) || self.default_tokenizer.is_some()
    }
}

impl Default for TokenizerRegistry {
    fn default() -> Self {
        Self::new()
    }
}

/// Count tokens for chat messages
pub fn count_chat_tokens(
    tokenizer: &dyn Tokenizer,
    template: &dyn crate::tokenizer::core::ChatTemplate,
    messages: &[crate::analyzer::OpenAIChatMessage],
) -> anyhow::Result<ChatTokenCount> {
    // Convert OpenAIChatMessage to serde_json::Value for apply_chat_template
    let json_messages: Vec<serde_json::Value> = messages
        .iter()
        .map(|msg| {
            use crate::analyzer::MessageRole;
            let role_str = match msg.role {
                MessageRole::System => "system",
                MessageRole::Developer => "developer",
                MessageRole::User => "user",
                MessageRole::Assistant => "assistant",
                MessageRole::Tool => "tool",
            };
            let mut obj = serde_json::Map::new();
            obj.insert("role".to_string(), serde_json::Value::String(role_str.to_string()));
            if let Some(ref content) = msg.content {
                obj.insert("content".to_string(), serde_json::Value::String(content.as_text().to_string()));
            } else {
                obj.insert("content".to_string(), serde_json::Value::String(String::new()));
            }
            // Include reasoning_content if present
            if let Some(ref reasoning) = msg.reasoning_content {
                obj.insert("reasoning_content".to_string(), serde_json::Value::String(reasoning.clone()));
            }
            serde_json::Value::Object(obj)
        })
        .collect();

    // Use apply_chat_template for accurate template rendering
    let formatted = template.apply_chat_template(&json_messages, true)?;

    // Count total tokens
    let total_tokens = tokenizer.count(&formatted)?;

    // Count per-message tokens using individual message formatting
    let mut per_message_tokens = Vec::with_capacity(messages.len());
    for (i, _msg) in messages.iter().enumerate() {
        // Format messages up to and including this one
        let partial_messages: Vec<serde_json::Value> = json_messages.iter().take(i + 1).cloned().collect();
        let partial_formatted = template.apply_chat_template(&partial_messages, false)?;
        
        // Count tokens for this partial prompt
        let partial_tokens = tokenizer.count(&partial_formatted)?;
        
        // This message's tokens = partial total - previous total
        let prev_total: usize = per_message_tokens.iter().sum();
        per_message_tokens.push(partial_tokens.saturating_sub(prev_total));
    }

    Ok(ChatTokenCount {
        total_tokens,
        per_message_tokens,
        formatted_prompt: formatted,
    })
}
