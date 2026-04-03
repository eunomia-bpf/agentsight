//! Factory functions for creating tokenizers

use anyhow::Result;
use std::path::Path;

use crate::tokenizer::core::{ChatTemplate, Tokenizer};
use crate::tokenizer::llm_tok::LlmTokenizer;
use crate::tokenizer::model::TokenizerModel;
use crate::tokenizer::registry::TokenizerRegistry;

/// Create a tokenizer for the specified model from a local file
///
/// # Arguments
/// * `model` - The tokenizer model to use
/// * `tokenizer_path` - Path to the tokenizer.json file
///
/// # Example
/// ```rust,ignore
/// let tokenizer = create_tokenizer(TokenizerModel::Qwen35Plus, "/path/to/tokenizer.json")?;
/// let count = tokenizer.count("Hello")?;
/// ```
pub fn create_tokenizer(model: TokenizerModel, tokenizer_path: &Path) -> Result<Box<dyn Tokenizer>> {
    let tokenizer = LlmTokenizer::from_file(tokenizer_path, model.display_name())?;
    Ok(Box::new(tokenizer))
}

/// Create a tokenizer from a local file with auto-detection of model type
///
/// # Arguments
/// * `tokenizer_path` - Path to the tokenizer.json file
pub fn create_tokenizer_from_file(tokenizer_path: &Path) -> Result<Box<dyn Tokenizer>> {
    let tokenizer = LlmTokenizer::from_file(tokenizer_path, tokenizer_path.to_string_lossy().as_ref())?;
    Ok(Box::new(tokenizer))
}

/// Create a tokenizer from a URL
///
/// # Arguments
/// * `url` - URL to the tokenizer.json file
/// * `model_name` - Human-readable name for the model
pub fn create_tokenizer_from_url(url: &str, model_name: &str) -> Result<Box<dyn Tokenizer>> {
    let tokenizer = LlmTokenizer::from_url(url, model_name)?;
    Ok(Box::new(tokenizer))
}

/// Create a tokenizer registry with a single model
///
/// # Arguments
/// * `model` - The tokenizer model to use
/// * `tokenizer_path` - Path to the tokenizer.json file
pub fn create_tokenizer_registry(
    model: TokenizerModel,
    tokenizer_path: &Path,
) -> Result<TokenizerRegistry> {
    let mut registry = TokenizerRegistry::new();
    let tokenizer = create_tokenizer(model, tokenizer_path)?;
    registry.register(model.display_name(), tokenizer);
    registry.set_default_template_type(model.chat_template_type());
    Ok(registry)
}

/// Create a tokenizer registry from a local file with auto-detection
///
/// The tokenizer is registered as the default and will be used for all model types.
pub fn create_tokenizer_registry_from_file(tokenizer_path: &Path) -> Result<TokenizerRegistry> {
    let mut registry = TokenizerRegistry::new();
    let tokenizer = create_tokenizer_from_file(tokenizer_path)?;
    registry.set_default_tokenizer(tokenizer);
    Ok(registry)
}

/// Create a tokenizer registry with multiple models
///
/// # Arguments
/// * `models` - Vector of (model, path) tuples to register
pub fn create_tokenizer_registry_multi(
    models: &[(TokenizerModel, &Path)],
) -> Result<TokenizerRegistry> {
    let mut registry = TokenizerRegistry::new();

    for (model, path) in models {
        let tokenizer = create_tokenizer(*model, path)?;
        registry.register(model.display_name(), tokenizer);
    }

    // Set the first model as default if available
    if let Some((first_model, _)) = models.first() {
        registry.set_default_template_type(first_model.chat_template_type());
    }

    Ok(registry)
}

/// Create a chat template from tokenizer.json file
///
/// This function reads the chat_template field from tokenizer.json
/// and creates a template that can be used to format messages.
pub fn create_chat_template_from_file(tokenizer_path: &Path) -> Result<Box<dyn ChatTemplate>> {
    let content = std::fs::read_to_string(tokenizer_path)
        .map_err(|e| anyhow::anyhow!("Failed to read tokenizer file: {}", e))?;

    let template = LlmTokenizer::from_tokenizer_json(&content)?;
    Ok(Box::new(template))
}

/// Create a chat template from tokenizer.json content string
pub fn create_chat_template_from_json(tokenizer_json: &str) -> Result<Box<dyn ChatTemplate>> {
    let template = LlmTokenizer::from_tokenizer_json(tokenizer_json)?;
    Ok(Box::new(template))
}

/// Create a chat template with custom Jinja2 template string
pub fn create_chat_template_with_template(template_str: &str) -> Result<Box<dyn ChatTemplate>> {
    let template = LlmTokenizer::with_template(template_str)?;
    Ok(Box::new(template))
}
