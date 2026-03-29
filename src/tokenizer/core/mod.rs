//! Core tokenizer types and traits
//!
//! This module defines the fundamental traits and types for tokenization,
//! including the base [`Tokenizer`] trait and chat template abstractions.

use anyhow::Result;
use serde_json::Value;

/// Tokenizer trait for text to token conversion
///
/// This trait provides a unified interface for all tokenizer implementations.
/// Each model family should implement this trait.
pub trait Tokenizer: Send + Sync {
    /// Encode text into tokens and return token count
    fn count(&self, text: &str) -> Result<usize>;

    /// Encode text into tokens and return the token IDs
    fn encode(&self, text: &str) -> Result<Vec<u32>>;

    /// Decode token IDs back to text
    fn decode(&self, tokens: &[u32]) -> Result<String>;

    /// Get the model name
    fn model_name(&self) -> &str;
}

/// Chat template trait for formatting messages
pub trait ChatTemplate: Send + Sync {
    /// Format messages into the model-specific prompt format
    fn format_messages(&self, messages: &[crate::analyzer::OpenAIChatMessage]) -> String;

    /// Apply chat template to JSON messages (compatible with HuggingFace format)
    ///
    /// # Arguments
    /// * `messages` - Array of message objects with `role` and `content` fields
    /// * `add_generation_prompt` - Whether to add the assistant prefix at the end
    ///
    /// # Returns
    /// Formatted prompt string
    fn apply_chat_template(&self, messages: &[Value], add_generation_prompt: bool) -> Result<String>;

    /// Apply chat template with tools (for accurate token counting)
    ///
    /// When tools are provided, the template renders additional instruction text
    /// (tool usage format, examples, reminders) that must be counted as input tokens.
    ///
    /// Default implementation ignores tools and delegates to `apply_chat_template`.
    ///
    /// # Arguments
    /// * `messages` - Array of message objects
    /// * `tools` - Optional array of tool definition objects
    /// * `add_generation_prompt` - Whether to add the assistant prefix
    fn apply_chat_template_with_tools(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        // Default: ignore tools, delegate to base method
        self.apply_chat_template(messages, add_generation_prompt)
    }

    /// Get the template name
    fn template_name(&self) -> &str;
}

/// Token count result for chat messages
#[derive(Debug, Clone)]
pub struct ChatTokenCount {
    /// Total token count
    pub total_tokens: usize,
    /// Token count per message
    pub per_message_tokens: Vec<usize>,
    /// Formatted prompt (for debugging)
    pub formatted_prompt: String,
}

/// Supported chat template types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ChatTemplateType {
    /// Qwen ChatML format
    Qwen,
}

impl ChatTemplateType {
    /// Create a chat template instance
    pub fn create_template(&self) -> Box<dyn ChatTemplate> {
        match self {
            ChatTemplateType::Qwen => Box::new(super::templates::QwenChatTemplate::new()),
        }
    }
}
