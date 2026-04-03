//! Unified tokenizer + chat template adapter wrapping `llm-tokenizer` crate.
//!
//! `LlmTokenizer` implements both the agentsight [`Tokenizer`] trait and the
//! [`ChatTemplate`] trait, replacing the previous separate `QwenTokenizer` and
//! `QwenChatTemplate` types.

use anyhow::{anyhow, Result};
use minijinja::{context, Environment, Error as MjError, ErrorKind, Value as MjValue};
use serde_json::Value;
use std::io::Write;
use std::path::Path;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use crate::analyzer::{MessageRole, OpenAIChatMessage};
use crate::tokenizer::core::{ChatTemplate, Tokenizer};

/// Default Qwen2.5 ChatML template (Jinja2 format)
const DEFAULT_QWEN_TEMPLATE: &str = include_str!("templates/qwen_chat_template.jinja");

// ── Custom Jinja2 functions for HuggingFace template compatibility ───────

/// `raise_exception(msg)` - raises a template error (matches HuggingFace Python behavior)
fn jinja_raise_exception(msg: String) -> std::result::Result<String, MjError> {
    Err(MjError::new(ErrorKind::InvalidOperation, msg))
}

/// `startswith(s, prefix)` - standalone function form of str.startswith()
fn jinja_startswith(s: MjValue, prefix: String) -> bool {
    s.to_str().map_or(false, |s| s.starts_with(&prefix))
}

/// `endswith(s, suffix)` - standalone function form of str.endswith()
fn jinja_endswith(s: MjValue, suffix: String) -> bool {
    s.to_str().map_or(false, |s| s.ends_with(&suffix))
}

/// Build a pre-configured minijinja Environment with HuggingFace-compatible
/// features: Python string methods, raise_exception, tojson, startswith/endswith.
fn build_template_env(template: String) -> Result<Environment<'static>> {
    let mut env = Environment::new();

    // Match HuggingFace's Jinja2 defaults
    env.set_trim_blocks(true);
    env.set_lstrip_blocks(true);

    // Register template
    env.add_template_owned("chat".to_owned(), template)
        .map_err(|e| anyhow!("Failed to add template: {}", e))?;

    // Python string method compatibility (startswith, endswith, split, etc. as methods)
    env.set_unknown_method_callback(minijinja_contrib::pycompat::unknown_method_callback);

    // HuggingFace-specific global functions
    env.add_function("raise_exception", jinja_raise_exception);
    env.add_function("startswith", jinja_startswith);
    env.add_function("endswith", jinja_endswith);

    Ok(env)
}

/// Render the "chat" template with messages and parameters.
fn render_template(
    env: &Environment<'_>,
    messages: &[Value],
    tools: Option<&[Value]>,
    add_generation_prompt: bool,
) -> Result<String> {
    let tmpl = env
        .get_template("chat")
        .map_err(|e| anyhow!("Failed to get template: {}", e))?;

    let minijinja_messages: Vec<MjValue> = messages.iter().map(MjValue::from_serialize).collect();
    let tools_value = tools.map_or(MjValue::UNDEFINED, MjValue::from_serialize);

    let ctx = context! {
        messages => &minijinja_messages,
        add_generation_prompt => add_generation_prompt,
        tools => tools_value,
    };

    tmpl.render(&ctx)
        .map_err(|e| anyhow!("Failed to render chat template: {}", e))
}

/// Unified tokenizer + chat template adapter wrapping `llm-tokenizer` crate.
///
/// This struct implements both [`Tokenizer`] and [`ChatTemplate`] traits,
/// providing a single object for token counting, encoding/decoding, and
/// chat template rendering.
///
/// # Example
/// ```rust,ignore
/// let tok = LlmTokenizer::from_file("/path/to/tokenizer.json", "Qwen3.5-Plus")?;
/// let count = tok.count("Hello, world!")?;
/// ```
#[derive(Clone)]
pub struct LlmTokenizer {
    /// The underlying llm-tokenizer instance (behind Arc for Clone).
    inner: llm_tokenizer::Tokenizer,
    /// Compiled Jinja2 environment (behind Arc for Clone since Environment is not Clone).
    template_env: Option<Arc<Environment<'static>>>,
    /// Human-readable model name.
    model_name: String,
}

impl LlmTokenizer {
    /// Create a tokenizer from a local file.
    ///
    /// Loads both the tokenizer and chat template (if present in the config).
    pub fn from_file<P: AsRef<Path>>(path: P, model_name: &str) -> Result<Self> {
        let path = path.as_ref();
        let path_str = path.to_str()
            .ok_or_else(|| anyhow!("Tokenizer path is not valid UTF-8: {:?}", path))?;

        let inner = llm_tokenizer::Tokenizer::from_file(path_str)
            .map_err(|e| anyhow!("Failed to load tokenizer from '{}': {}", path.display(), e))?;

        // Try to load chat template from tokenizer_config.json or tokenizer.json
        let template_str = Self::load_template_str_for_file(path)?;
        let env = build_template_env(template_str)?;

        Ok(Self {
            inner,
            template_env: Some(Arc::new(env)),
            model_name: model_name.to_string(),
        })
    }

    /// Extract the chat template string from a tokenizer file's directory.
    fn load_template_str_for_file(tokenizer_path: &Path) -> Result<String> {
        // Priority 1: Try tokenizer_config.json in the same directory
        if let Some(parent) = tokenizer_path.parent() {
            let config_path = parent.join("tokenizer_config.json");
            if config_path.exists() {
                if let Ok(content) = std::fs::read_to_string(&config_path) {
                    if let Ok(json) = serde_json::from_str::<Value>(&content) {
                        if let Some(tmpl) = json.get("chat_template").and_then(|v| v.as_str()) {
                            return Ok(tmpl.to_string());
                        }
                    }
                }
            }
        }

        // Priority 2: Try to extract from tokenizer.json itself
        if let Ok(content) = std::fs::read_to_string(tokenizer_path) {
            if let Ok(json) = serde_json::from_str::<Value>(&content) {
                if let Some(tmpl) = json.get("chat_template").and_then(|v| v.as_str()) {
                    return Ok(tmpl.to_string());
                }
            }
        }

        // Fallback: use default Qwen template
        Ok(DEFAULT_QWEN_TEMPLATE.to_string())
    }

    /// Create a tokenizer from a URL.
    ///
    /// Downloads the tokenizer.json file and loads it. Retries up to 5 times.
    pub fn from_url(url: &str, model_name: &str) -> Result<Self> {
        const MAX_RETRIES: u32 = 5;
        const RETRY_DELAY_SECS: u64 = 10;

        let mut last_error = None;
        for attempt in 1..=MAX_RETRIES {
            match Self::try_download(url, model_name) {
                Ok(tokenizer) => return Ok(tokenizer),
                Err(e) => {
                    last_error = Some(e);
                    if attempt < MAX_RETRIES {
                        eprintln!(
                            "Download attempt {}/{} failed. Retrying in {} seconds...",
                            attempt, MAX_RETRIES, RETRY_DELAY_SECS
                        );
                        thread::sleep(Duration::from_secs(RETRY_DELAY_SECS));
                    }
                }
            }
        }

        Err(anyhow!(
            "Failed to download tokenizer from '{}' after {} retries: {:?}",
            url, MAX_RETRIES, last_error
        ))
    }

    /// Try to download and load tokenizer once.
    fn try_download(url: &str, model_name: &str) -> Result<Self> {
        let dir = std::env::temp_dir().join(format!("agentsight-tok-{}", std::process::id()));
        std::fs::create_dir_all(&dir)
            .map_err(|e| anyhow!("Failed to create temporary directory: {}", e))?;
        let temp_path = dir.join("tokenizer.json");

        let response = ureq::get(url)
            .call()
            .map_err(|e| anyhow!("Failed to download tokenizer from '{}': {}", url, e))?;

        let mut file = std::fs::File::create(&temp_path)
            .map_err(|e| anyhow!("Failed to create temporary file: {}", e))?;

        let mut reader = response.into_reader();
        std::io::copy(&mut reader, &mut file)
            .map_err(|e| anyhow!("Failed to write tokenizer to temporary file: {}", e))?;

        file.flush()
            .map_err(|e| anyhow!("Failed to flush temporary file: {}", e))?;

        let result = Self::from_file(&temp_path, model_name);

        // Clean up temp dir
        let _ = std::fs::remove_dir_all(&dir);

        result
    }

    /// Create a template-only instance (no real tokenizer backend).
    ///
    /// Used in fallback paths where only `ChatTemplate` functionality is needed
    /// (e.g., alongside `ByteCountTokenizer`).
    pub fn default_template() -> Result<Self> {
        let env = build_template_env(DEFAULT_QWEN_TEMPLATE.to_string())?;

        // Use mock tokenizer as backend (only template functionality is used)
        let inner = llm_tokenizer::Tokenizer::from_arc(
            Arc::new(llm_tokenizer::MockTokenizer::new())
        );

        Ok(Self {
            inner,
            template_env: Some(Arc::new(env)),
            model_name: "qwen-default-template".to_string(),
        })
    }

    /// Create from a custom Jinja2 template string.
    pub fn with_template(template_str: &str) -> Result<Self> {
        let env = build_template_env(template_str.to_string())?;

        let inner = llm_tokenizer::Tokenizer::from_arc(
            Arc::new(llm_tokenizer::MockTokenizer::new())
        );

        Ok(Self {
            inner,
            template_env: Some(Arc::new(env)),
            model_name: "custom-template".to_string(),
        })
    }

    /// Create from tokenizer.json content string (extracts chat_template field).
    pub fn from_tokenizer_json(tokenizer_json: &str) -> Result<Self> {
        let json: Value = serde_json::from_str(tokenizer_json)
            .map_err(|e| anyhow!("Failed to parse tokenizer.json: {}", e))?;

        let template_str = json
            .get("chat_template")
            .and_then(|v| v.as_str())
            .unwrap_or(DEFAULT_QWEN_TEMPLATE);

        Self::with_template(template_str)
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

    /// Apply chat template using the compiled Jinja2 environment.
    fn do_apply_chat_template(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        let env = self.template_env.as_ref()
            .ok_or_else(|| anyhow!("Chat template not available - no template configured"))?;

        render_template(env, messages, tools, add_generation_prompt)
    }

    /// Convert OpenAIChatMessage to serde_json::Value for template rendering.
    fn messages_to_json(messages: &[OpenAIChatMessage]) -> Vec<Value> {
        messages
            .iter()
            .map(|msg| {
                let role_str = match msg.role {
                    MessageRole::System => "system",
                    MessageRole::Developer => "developer",
                    MessageRole::User => "user",
                    MessageRole::Assistant => "assistant",
                    MessageRole::Tool => "tool",
                };
                let mut obj = serde_json::Map::new();
                obj.insert("role".to_string(), Value::String(role_str.to_string()));
                if let Some(ref content) = msg.content {
                    obj.insert("content".to_string(), Value::String(content.as_text().to_string()));
                } else {
                    obj.insert("content".to_string(), Value::String(String::new()));
                }
                if let Some(ref reasoning) = msg.reasoning_content {
                    obj.insert("reasoning_content".to_string(), Value::String(reasoning.clone()));
                }
                Value::Object(obj)
            })
            .collect()
    }
}

// ── Implement agentsight Tokenizer trait ─────────────────────────────────

impl Tokenizer for LlmTokenizer {
    fn count(&self, text: &str) -> Result<usize> {
        let encoding = self.inner.encode(text, false)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;
        Ok(encoding.token_ids().len())
    }

    fn encode(&self, text: &str) -> Result<Vec<u32>> {
        self.encode_without_special_tokens(text)
    }

    fn decode(&self, tokens: &[u32]) -> Result<String> {
        self.inner.decode(tokens, false)
            .map_err(|e| anyhow!("Failed to decode tokens: {}", e))
    }

    fn model_name(&self) -> &str {
        &self.model_name
    }

    fn count_with_special_tokens(&self, text: &str) -> Result<usize> {
        let encoding = self.inner.encode(text, true)
            .map_err(|e| anyhow!("Failed to encode text with special tokens: {}", e))?;
        Ok(encoding.token_ids().len())
    }
}

// ── Implement agentsight ChatTemplate trait ──────────────────────────────

impl ChatTemplate for LlmTokenizer {
    fn format_messages(&self, messages: &[OpenAIChatMessage]) -> String {
        let json_messages = Self::messages_to_json(messages);
        self.apply_chat_template(&json_messages, true)
            .unwrap_or_else(|_| {
                // Fallback to simple ChatML format if template rendering fails
                let mut result = String::new();
                for msg in messages {
                    let role = match msg.role {
                        MessageRole::System => "system",
                        MessageRole::Developer => "developer",
                        MessageRole::User => "user",
                        MessageRole::Assistant => "assistant",
                        MessageRole::Tool => "tool",
                    };
                    let content = msg.content.as_ref().map(|c| c.as_text()).unwrap_or_default();
                    result.push_str(&format!("<|im_start|>{}\n{}<|im_end|>\n", role, content));
                }
                result.push_str("<|im_start|>assistant\n");
                result
            })
    }

    fn apply_chat_template(&self, messages: &[Value], add_generation_prompt: bool) -> Result<String> {
        self.do_apply_chat_template(messages, None, add_generation_prompt)
    }

    fn apply_chat_template_with_tools(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        self.do_apply_chat_template(messages, tools, add_generation_prompt)
    }

    fn template_name(&self) -> &str {
        &self.model_name
    }
}

impl std::fmt::Debug for LlmTokenizer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LlmTokenizer")
            .field("model_name", &self.model_name)
            .field("vocab_size", &self.vocab_size())
            .field("has_template", &self.template_env.is_some())
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzer::OpenAIContent;

    #[test]
    fn test_default_template() {
        let tok = LlmTokenizer::default_template().expect("Failed to create default template");
        let messages = vec![
            serde_json::json!({"role": "system", "content": "You are a helpful assistant."}),
            serde_json::json!({"role": "user", "content": "Hello"}),
        ];
        let result = tok.apply_chat_template(&messages, true).unwrap();
        assert!(result.contains("<|im_start|>system"));
        assert!(result.contains("You are a helpful assistant."));
        assert!(result.contains("<|im_start|>user"));
        assert!(result.contains("Hello"));
        assert!(result.contains("<|im_start|>assistant"));
    }

    #[test]
    fn test_with_template() {
        let tok = LlmTokenizer::with_template(
            "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"
        ).unwrap();
        let messages = vec![
            serde_json::json!({"role": "user", "content": "Hello"}),
        ];
        let result = tok.apply_chat_template(&messages, false).unwrap();
        assert!(result.contains("user: Hello"));
    }

    #[test]
    fn test_with_template_invalid() {
        let result = LlmTokenizer::with_template("{% invalid syntax");
        assert!(result.is_err());
    }

    #[test]
    fn test_from_tokenizer_json() {
        let json = r#"{
            "chat_template": "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"
        }"#;
        let tok = LlmTokenizer::from_tokenizer_json(json).unwrap();
        let messages = vec![
            serde_json::json!({"role": "user", "content": "Hello"}),
        ];
        let result = tok.apply_chat_template(&messages, false).unwrap();
        assert!(result.contains("user: Hello"));
    }

    #[test]
    fn test_from_tokenizer_json_fallback() {
        let json = r#"{"tokenizer_class": "PreTrainedTokenizer"}"#;
        let tok = LlmTokenizer::from_tokenizer_json(json).unwrap();
        // Should use default template
        let messages = vec![
            serde_json::json!({"role": "user", "content": "Hi"}),
        ];
        let result = tok.apply_chat_template(&messages, true).unwrap();
        assert!(result.contains("<|im_start|>user"));
    }

    #[test]
    fn test_format_messages() {
        let tok = LlmTokenizer::default_template().unwrap();
        let messages = vec![
            OpenAIChatMessage {
                role: MessageRole::System,
                content: Some(OpenAIContent::Text("You are helpful.".to_string())),
                reasoning_content: None,
                refusal: None,
                function_call: None,
                tool_calls: None,
                tool_call_id: None,
                name: None,
                annotations: None,
                audio: None,
            },
            OpenAIChatMessage {
                role: MessageRole::User,
                content: Some(OpenAIContent::Text("Hi".to_string())),
                reasoning_content: None,
                refusal: None,
                function_call: None,
                tool_calls: None,
                tool_call_id: None,
                name: None,
                annotations: None,
                audio: None,
            },
        ];

        let formatted = tok.format_messages(&messages);
        assert!(formatted.contains("<|im_start|>system"));
        assert!(formatted.contains("<|im_start|>user"));
        // Qwen template adds <think>\n after assistant prompt for reasoning
        assert!(formatted.contains("<|im_start|>assistant\n"));
    }

    #[test]
    fn test_from_file_not_found() {
        let result = LlmTokenizer::from_file("/nonexistent/tokenizer.json", "test");
        assert!(result.is_err());
    }

    #[test]
    fn test_raise_exception_in_template() {
        let tok = LlmTokenizer::default_template().unwrap();
        // Empty messages should trigger raise_exception('No messages provided.')
        let result = tok.apply_chat_template(&[], true);
        assert!(result.is_err());
        let err_msg = result.unwrap_err().to_string();
        assert!(err_msg.contains("No messages provided"), "Error should contain validation message, got: {}", err_msg);
    }
}
