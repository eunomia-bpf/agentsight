//! Multi-model tokenizer manager
//!
//! Provides a unified interface for managing multiple LLM tokenizers,
//! allowing different models to be used based on model name.

use crate::tokenizer::llm_tok::LlmTokenizer;
use anyhow::{anyhow, Result};
use hf_hub::api::sync::Api;
use once_cell::sync::OnceCell;
use std::collections::HashMap;
use std::sync::{Arc, Mutex, MutexGuard};

/// Global MultiModelTokenizer instance
static GLOBAL_TOKENIZER: OnceCell<Mutex<MultiModelTokenizer>> = OnceCell::new();

/// Initialize the global tokenizer manager.
pub fn init_global_tokenizer<F>(init_fn: F) -> Result<()>
where
    F: FnOnce(&mut MultiModelTokenizer) -> Result<()>,
{
    let mut manager = MultiModelTokenizer::new();
    init_fn(&mut manager)?;
    GLOBAL_TOKENIZER
        .set(Mutex::new(manager))
        .map_err(|_| anyhow!("Global tokenizer already initialized"))?;
    Ok(())
}

/// Initialize the global tokenizer manager with a pre-built manager.
pub fn set_global_tokenizer(manager: MultiModelTokenizer) -> Result<()> {
    GLOBAL_TOKENIZER
        .set(Mutex::new(manager))
        .map_err(|_| anyhow!("Global tokenizer already initialized"))?;
    Ok(())
}

/// Get a reference to the global tokenizer manager.
fn get_global_manager() -> Result<MutexGuard<'static, MultiModelTokenizer>> {
    GLOBAL_TOKENIZER
        .get()
        .ok_or_else(|| anyhow!("Global tokenizer not initialized. Call init_global_tokenizer() first."))?
        .lock()
        .map_err(|e| anyhow!("Failed to lock global tokenizer: {}", e))
}

/// Get a tokenizer for a specific model ID from the global manager.
pub fn get_global_tokenizer(model_id: &str) -> Result<Arc<LlmTokenizer>> {
    let manager = get_global_manager()?;
    manager.get_for_model(model_id)
}

/// Check if the global tokenizer manager has been initialized.
pub fn is_global_tokenizer_initialized() -> bool {
    GLOBAL_TOKENIZER.get().is_some()
}

/// Register a tokenizer in the global manager.
pub fn register_global_tokenizer(model_id: &str, tokenizer: LlmTokenizer) -> Result<()> {
    let mut manager = get_global_manager()?;
    manager.register(model_id, tokenizer);
    Ok(())
}

/// Set the default model for the global tokenizer manager.
pub fn set_global_default_model(model_id: &str) -> Result<()> {
    let mut manager = get_global_manager()?;
    manager.set_default_model(model_id);
    Ok(())
}

/// Tokenizer entry containing the tokenizer instance and its metadata
#[derive(Debug, Clone)]
pub struct TokenizerEntry {
    /// The tokenizer instance (wrapped in Arc for cheap cloning)
    pub tokenizer: Arc<LlmTokenizer>,
    /// The model ID
    pub model_id: String,
    /// Human-readable name
    pub name: String,
}

impl TokenizerEntry {
    /// Create a new tokenizer entry
    pub fn new(tokenizer: LlmTokenizer, model_id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            tokenizer: Arc::new(tokenizer),
            model_id: model_id.into(),
            name: name.into(),
        }
    }
}

/// Multi-model tokenizer manager
#[derive(Debug, Default)]
pub struct MultiModelTokenizer {
    /// Map of model IDs to tokenizer entries
    tokenizers: HashMap<String, TokenizerEntry>,
    /// Default tokenizer model ID to use when model is not found
    default_model: Option<String>,
    /// HuggingFace Hub API client (cached)
    hf_api: Option<Api>,
}

impl Clone for MultiModelTokenizer {
    fn clone(&self) -> Self {
        Self {
            tokenizers: self.tokenizers.clone(),
            default_model: self.default_model.clone(),
            hf_api: None,
        }
    }
}

impl MultiModelTokenizer {
    /// Create a new empty multi-model tokenizer manager
    pub fn new() -> Self {
        Self {
            tokenizers: HashMap::new(),
            default_model: None,
            hf_api: None,
        }
    }

    /// Get or create the HuggingFace Hub API client
    fn get_hf_api(&mut self) -> Result<&Api> {
        if self.hf_api.is_none() {
            self.hf_api = Some(Api::new()?);
        }
        Ok(self.hf_api.as_ref().unwrap())
    }

    /// Register a tokenizer from HuggingFace Hub for a specific model
    pub fn register_from_hf(&mut self, model_id: &str) -> Result<()> {
        let api = self.get_hf_api()?;
        let repo = api.model(model_id.to_string());
        // Download both tokenizer.json and tokenizer_config.json
        let tokenizer_path = repo.get("tokenizer.json")?;
        let config_path = repo.get("tokenizer_config.json")?;
        let tokenizer = LlmTokenizer::from_file(&tokenizer_path, &config_path)?;
        let entry = TokenizerEntry::new(tokenizer, model_id, model_id);
        self.tokenizers.insert(model_id.to_string(), entry);
        Ok(())
    }

    /// Register a tokenizer with a model ID
    pub fn register(&mut self, model_id: &str, tokenizer: LlmTokenizer) {
        let entry = TokenizerEntry::new(tokenizer, model_id, model_id);
        self.tokenizers.insert(model_id.to_string(), entry);
    }

    /// Set the default model to use when model detection fails
    pub fn set_default_model(&mut self, model_id: &str) {
        self.default_model = Some(model_id.to_string());
    }

    /// Get the default model ID
    pub fn default_model(&self) -> Option<&str> {
        self.default_model.as_deref()
    }

    /// Get a tokenizer for a specific model ID
    pub fn get(&self, model_id: &str) -> Option<Arc<LlmTokenizer>> {
        self.tokenizers.get(model_id).map(|entry| Arc::clone(&entry.tokenizer))
    }

    /// Get a tokenizer for a model name
    pub fn get_for_model(&self, model_name: &str) -> Result<Arc<LlmTokenizer>> {
        // Try direct lookup
        if let Some(tokenizer) = self.get(model_name) {
            return Ok(tokenizer);
        }

        // Fall back to default model
        if let Some(default) = &self.default_model {
            if let Some(tokenizer) = self.get(default) {
                return Ok(tokenizer);
            }
        }

        Err(anyhow!(
            "No tokenizer found for model '{}' and no default set",
            model_name
        ))
    }

    /// Get a tokenizer entry for a specific model ID
    pub fn get_entry(&self, model_id: &str) -> Option<&TokenizerEntry> {
        self.tokenizers.get(model_id)
    }

    /// Check if a tokenizer is registered for the given model
    pub fn has(&self, model_id: &str) -> bool {
        self.tokenizers.contains_key(model_id)
    }

    /// Remove a tokenizer for a specific model
    pub fn remove(&mut self, model_id: &str) -> Option<TokenizerEntry> {
        self.tokenizers.remove(model_id)
    }

    /// Get all registered model IDs
    pub fn registered_models(&self) -> Vec<&String> {
        self.tokenizers.keys().collect()
    }

    /// Get the number of registered tokenizers
    pub fn len(&self) -> usize {
        self.tokenizers.len()
    }

    /// Check if no tokenizers are registered
    pub fn is_empty(&self) -> bool {
        self.tokenizers.is_empty()
    }

    /// Clear all registered tokenizers
    pub fn clear(&mut self) {
        self.tokenizers.clear();
        self.default_model = None;
    }

    /// Iterate over all registered tokenizer entries
    pub fn iter(&self) -> impl Iterator<Item = (&String, &TokenizerEntry)> {
        self.tokenizers.iter()
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_empty() {
        let manager = MultiModelTokenizer::new();
        assert!(manager.is_empty());
        assert_eq!(manager.len(), 0);
    }

    #[test]
    fn test_default_model() {
        let mut manager = MultiModelTokenizer::new();
        assert!(manager.default_model().is_none());

        manager.set_default_model("qwen3.5-plus");
        assert_eq!(manager.default_model(), Some("qwen3.5-plus"));
    }
}
