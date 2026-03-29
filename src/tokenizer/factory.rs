//! Factory functions for creating tokenizers

use anyhow::Result;
use std::path::Path;

use crate::tokenizer::core::{ChatTemplate, Tokenizer};
use crate::tokenizer::model::TokenizerModel;
use crate::tokenizer::providers::QwenTokenizer;
use crate::tokenizer::registry::TokenizerRegistry;
use crate::tokenizer::templates::QwenChatTemplate;

/// Create a tokenizer for the specified model from a local file
///
/// # Arguments
/// * `model` - The tokenizer model to use
/// * `tokenizer_path` - Path to the tokenizer.json file
///
/// # Example
/// ```rust,ignore
/// let tokenizer = create_tokenizer(TokenizerModel::Qwen35Plus, "/path/to/tokenizer.json")?;
/// let count = tokenizer.count("你好，世界！")?;
/// ```
pub fn create_tokenizer(model: TokenizerModel, tokenizer_path: &Path) -> Result<Box<dyn Tokenizer>> {
    match model {
        TokenizerModel::Qwen35Plus
        | TokenizerModel::Qwen25
        | TokenizerModel::Qwen2 => {
            let tokenizer = QwenTokenizer::from_file(tokenizer_path, model.display_name())?;
            Ok(Box::new(tokenizer))
        }
    }
}

/// Create a tokenizer from a local file with auto-detection of model type
///
/// # Arguments
/// * `tokenizer_path` - Path to the tokenizer.json file
///
/// # Example
/// ```rust,ignore
/// let tokenizer = create_tokenizer_from_file("/path/to/tokenizer.json")?;
/// let count = tokenizer.count("Hello, world!")?;
/// ```
pub fn create_tokenizer_from_file(tokenizer_path: &Path) -> Result<Box<dyn Tokenizer>> {
    let tokenizer = QwenTokenizer::from_file(tokenizer_path, tokenizer_path.to_string_lossy().as_ref())?;
    Ok(Box::new(tokenizer))
}

/// Create a tokenizer from a URL
///
/// # Arguments
/// * `url` - URL to the tokenizer.json file
/// * `model_name` - Human-readable name for the model
///
/// # Example
/// ```rust,ignore
/// let tokenizer = create_tokenizer_from_url(
///     "https://www.modelscope.cn/models/Qwen/Qwen3.5-27B/resolve/master/tokenizer.json",
///     "Qwen3.5-27B"
/// )?;
/// let count = tokenizer.count("你好，世界！")?;
/// ```
pub fn create_tokenizer_from_url(url: &str, model_name: &str) -> Result<Box<dyn Tokenizer>> {
    let tokenizer = QwenTokenizer::from_url(url, model_name)?;
    Ok(Box::new(tokenizer))
}

/// Create a tokenizer registry with a single model
///
/// # Arguments
/// * `model` - The tokenizer model to use
/// * `tokenizer_path` - Path to the tokenizer.json file
///
/// # Example
/// ```rust,ignore
/// let registry = create_tokenizer_registry(TokenizerModel::Qwen35Plus, "/path/to/tokenizer.json")?;
/// let breakdown = registry.count_request(&openai_request)?;
/// println!("Prompt tokens: {}", breakdown.prompt_tokens);
/// ```
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
///
/// # Example
/// ```rust,ignore
/// let models = vec![
///     (TokenizerModel::Qwen35Plus, Path::new("/path/to/qwen35_tokenizer.json")),
///     (TokenizerModel::Qwen25, Path::new("/path/to/qwen25_tokenizer.json")),
/// ];
/// let registry = create_tokenizer_registry_multi(&models)?;
/// ```
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
/// and creates a QwenChatTemplate with the loaded template.
///
/// # Arguments
/// * `tokenizer_path` - Path to the tokenizer.json file
///
/// # Returns
/// A Box<dyn ChatTemplate> that can be used to format messages
///
/// # Example
/// ```rust,ignore
/// let template = create_chat_template_from_file(Path::new("/path/to/tokenizer.json"))?;
/// let messages = vec![
///     serde_json::json!({"role": "user", "content": "Hello"}),
/// ];
/// let prompt = template.apply_chat_template(&messages, true)?;
/// ```
pub fn create_chat_template_from_file(tokenizer_path: &Path) -> Result<Box<dyn ChatTemplate>> {
    let content = std::fs::read_to_string(tokenizer_path)
        .map_err(|e| anyhow::anyhow!("Failed to read tokenizer file: {}", e))?;
    
    let template = QwenChatTemplate::from_tokenizer_json(&content)?;
    Ok(Box::new(template))
}

/// Create a chat template from tokenizer.json content string
///
/// # Arguments
/// * `tokenizer_json` - Content of tokenizer.json file
///
/// # Returns
/// A Box<dyn ChatTemplate> that can be used to format messages
///
/// # Example
/// ```rust,ignore
/// let json_content = r#"{"chat_template": "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"}"#;
/// let template = create_chat_template_from_json(json_content)?;
/// ```
pub fn create_chat_template_from_json(tokenizer_json: &str) -> Result<Box<dyn ChatTemplate>> {
    let template = QwenChatTemplate::from_tokenizer_json(tokenizer_json)?;
    Ok(Box::new(template))
}

/// Create a chat template with custom Jinja2 template string
///
/// # Arguments
/// * `template_str` - Jinja2 template string (HuggingFace format)
///
/// # Returns
/// A Box<dyn ChatTemplate> that can be used to format messages
///
/// # Example
/// ```rust,ignore
/// let template_str = r#"{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"#;
/// let template = create_chat_template_with_template(template_str)?;
/// ```
pub fn create_chat_template_with_template(template_str: &str) -> Result<Box<dyn ChatTemplate>> {
    let template = QwenChatTemplate::with_template(template_str)?;
    Ok(Box::new(template))
}
