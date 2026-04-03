//! Multi-model tokenizer manager
//!
//! Provides a unified interface for managing multiple LLM tokenizers,
//! allowing different models to be used based on model name.

use crate::config::{HF_ENDPOINT, hf_home};
use crate::tokenizer::llm_tok::LlmTokenizer;
use crate::tokenizer::model_mapping::map_to_hf_model_id;
use anyhow::{Result, anyhow};
use hf_hub::api::sync::{Api, ApiBuilder};
use once_cell::sync::OnceCell;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::{Arc, Mutex, MutexGuard};

static GLOBAL_TOKENIZER: OnceCell<Mutex<MultiModelTokenizer>> = OnceCell::new();

fn get_global_manager() -> MutexGuard<'static, MultiModelTokenizer> {
    GLOBAL_TOKENIZER
        .get_or_init(|| Mutex::new(MultiModelTokenizer::new()))
        .lock()
        .expect("Failed to lock global tokenizer")
}

pub fn get_global_tokenizer(model_id: &str) -> Result<Arc<LlmTokenizer>> {
    get_global_manager().get_for_model(model_id)
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
    pub fn new(
        tokenizer: LlmTokenizer,
        model_id: impl Into<String>,
        name: impl Into<String>,
    ) -> Self {
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
    /// HuggingFace Hub API client (cached)
    hf_api: Option<Api>,
}

impl MultiModelTokenizer {
    /// Create a new empty multi-model tokenizer manager
    pub fn new() -> Self {
        Self {
            tokenizers: HashMap::new(),
            hf_api: None,
        }
    }

    /// Get or create the HuggingFace Hub API client
    fn get_hf_api(&mut self) -> Result<&Api> {
        if self.hf_api.is_none() {
            let api = ApiBuilder::new()
                .with_cache_dir(hf_home())
                .with_endpoint(HF_ENDPOINT.to_string())
                .with_progress(true)
                .build()
                .expect("failed to build hf api");
            self.hf_api = Some(api);
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

    /// Get a tokenizer for a specific model ID
    pub fn get(&self, model_id: &str) -> Option<Arc<LlmTokenizer>> {
        self.tokenizers
            .get(model_id)
            .map(|entry| Arc::clone(&entry.tokenizer))
    }

    /// Get a tokenizer for a model name, auto-register from HuggingFace if not found
    ///
    /// This method will:
    /// 1. Map the model name to HuggingFace model ID using predefined mappings
    /// 2. Check the cache with the original model name
    /// 3. Download tokenizer from HuggingFace Hub if not cached
    pub fn get_for_model(&mut self, model_name: &str) -> Result<Arc<LlmTokenizer>> {
        // Try direct lookup first (with original model name)
        if let Some(tokenizer) = self.get(model_name) {
            return Ok(tokenizer);
        }

        // Map model name to HuggingFace model ID
        let hf_model_id = map_to_hf_model_id(model_name);
        
        // Try lookup with HF model ID (in case same HF ID was registered under different name)
        if hf_model_id != model_name {
            if let Some(tokenizer) = self.get(hf_model_id) {
                // Cache under original model name too
                let entry = self.tokenizers.get(hf_model_id).cloned();
                if let Some(entry) = entry {
                    self.tokenizers.insert(model_name.to_string(), entry);
                }
                return Ok(tokenizer);
            }
        }

        // Register from HuggingFace Hub using mapped ID
        self.register_from_hf(hf_model_id)?;

        // If we used a different HF ID, also cache under original model name
        if hf_model_id != model_name {
            if let Some(entry) = self.tokenizers.get(hf_model_id).cloned() {
                self.tokenizers.insert(model_name.to_string(), entry);
            }
        }

        // Return the tokenizer
        self.get(model_name).ok_or_else(|| {
            anyhow!(
                "Failed to get tokenizer after registration for model '{}'",
                model_name
            )
        })
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
    }

    /// Iterate over all registered tokenizer entries
    pub fn iter(&self) -> impl Iterator<Item = (&String, &TokenizerEntry)> {
        self.tokenizers.iter()
    }
}
