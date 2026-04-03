//! Unified tokenizer + chat template adapter wrapping `llm-tokenizer` crate.
//!
//! `LlmTokenizer` implements both the agentsight [`Tokenizer`] trait and the
//! [`ChatTemplate`] trait, replacing the previous separate `QwenTokenizer` and
//! `QwenChatTemplate` types.

use anyhow::{anyhow, Result};
use serde_json::Value;
use std::path::Path;
use std::sync::Arc;

use crate::analyzer::{MessageRole, OpenAIChatMessage};
use llm_tokenizer::{Decoder as _, Encoder as _, HuggingFaceTokenizer, TokenizerTrait, chat_template::ChatTemplateParams};

/// Unified tokenizer + chat template adapter wrapping `llm-tokenizer` crate.
///
/// This struct implements both [`Tokenizer`] and [`ChatTemplate`] traits,
/// providing a single object for token counting, encoding/decoding, and
/// chat template rendering.
///
/// # Example
/// ```rust,ignore
/// let tok = LlmTokenizer::from_file("/path/to/tokenizer.json")?;
/// let count = tok.count("Hello, world!")?;
/// ```
#[derive(Clone)]
pub struct LlmTokenizer {
    /// The underlying llm-tokenizer instance (behind Arc for Clone).
    inner: Arc<HuggingFaceTokenizer>,
    /// Human-readable model name.
    model_name: String,
}

impl LlmTokenizer {
    /// Create a tokenizer from a local file with explicit config path.
    ///
    /// Loads both the tokenizer and chat template from the specified config file.
    ///
    /// # Arguments
    /// * `tokenizer_path` - Path to the tokenizer.json file
    /// * `config_path` - Path to the tokenizer_config.json file (for chat template)
    pub fn from_file<P: AsRef<Path>>(
        tokenizer_path: P,
        config_path: P,
    ) -> Result<Self> {
        let tokenizer_path = tokenizer_path.as_ref();
        let config_path = config_path.as_ref();
        let tokenizer_str = tokenizer_path.to_str()
            .ok_or_else(|| anyhow!("Tokenizer path is not valid UTF-8: {:?}", tokenizer_path))?;
        let config_str = config_path.to_str()
            .ok_or_else(|| anyhow!("Config path is not valid UTF-8: {:?}", config_path))?;

        // Use HuggingFaceTokenizer with explicit chat template config
        let tokenizer = HuggingFaceTokenizer::from_file_with_chat_template(tokenizer_str, Some(config_str))
            .map_err(|e| anyhow!("Failed to load tokenizer from '{}': {}", tokenizer_path.display(), e))?;

        Ok(Self {
            inner: Arc::new(tokenizer),
            model_name: tokenizer_path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string(),
        })
    }

    /// Create a tokenizer from a URL (backward compatibility).
    ///
    /// This is deprecated in favor of `from_hf` which uses HuggingFace Hub directly.
    /// For URLs pointing to HuggingFace (e.g., huggingface.co/...), consider using
    /// `from_hf` with the model ID instead.
    #[deprecated]
    pub fn from_url(url: &str, model_name: &str) -> Result<Self> {
        todo!()
    }

    /// Encode text with special tokens.
    pub fn encode_with_special_tokens(&self, text: &str) -> Result<Vec<u32>> {
        let encoding = self.inner.encode(text, true)
            .map_err(|e| anyhow!("Failed to encode text with special tokens: {}", e))?;
        Ok(encoding.token_ids().to_vec())
    }

    /// Encode text without special tokens.
    pub fn encode_without_special_tokens(&self, text: &str) -> Result<Vec<u32>> {
        let encoding = self.inner.encode(text, false)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;
        Ok(encoding.token_ids().to_vec())
    }

    /// Get the vocabulary size.
    pub fn vocab_size(&self) -> usize {
        self.inner.vocab_size()
    }

    /// Apply chat template using the underlying tokenizer's implementation.
    fn do_apply_chat_template(
        &self,
        messages: &[Value],
        _tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        // Use the llm-tokenizer crate's built-in chat template support
        self.inner.apply_chat_template(
            messages,
            ChatTemplateParams {
                add_generation_prompt,
                ..Default::default()
            },
        )
        .map_err(|e| anyhow!("Failed to apply chat template: {}", e))
    }

    /// Convert OpenAIChatMessage to serde_json::Value for template rendering.
    pub fn messages_to_json(messages: &[OpenAIChatMessage]) -> Vec<Value> {
       todo!()
    }

    /// Count tokens in text
    pub fn count(&self, text: &str) -> Result<usize> {
        let encoding = self.inner.encode(text, false)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;
        Ok(encoding.token_ids().len())
    }

    /// Encode text into token IDs
    pub fn encode(&self, text: &str) -> Result<Vec<u32>> {
        self.encode_without_special_tokens(text)
    }

    /// Decode token IDs back to text
    pub fn decode(&self, tokens: &[u32]) -> Result<String> {
        self.inner.decode(tokens, false)
            .map_err(|e| anyhow!("Failed to decode tokens: {}", e))
    }

    /// Get the model name
    pub fn model_name(&self) -> &str {
        &self.model_name
    }

    /// Count tokens with special token recognition
    pub fn count_with_special_tokens(&self, text: &str) -> Result<usize> {
        let encoding = self.inner.encode(text, true)
            .map_err(|e| anyhow!("Failed to encode text with special tokens: {}", e))?;
        Ok(encoding.token_ids().len())
    }

    /// Apply chat template to JSON messages
    pub fn apply_chat_template(&self, messages: &[Value], add_generation_prompt: bool) -> Result<String> {
        self.do_apply_chat_template(messages, None, add_generation_prompt)
    }

    /// Apply chat template with tools
    pub fn apply_chat_template_with_tools(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        self.do_apply_chat_template(messages, tools, add_generation_prompt)
    }
}

impl std::fmt::Debug for LlmTokenizer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LlmTokenizer")
            .field("model_name", &self.model_name)
            .field("vocab_size", &self.vocab_size())
            .finish()
    }
}
