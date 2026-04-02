//! Qwen ChatML template implementation using MiniJinja

use crate::analyzer::{MessageRole, OpenAIChatMessage};
use crate::tokenizer::core::ChatTemplate;
use anyhow::{Context, Result};
use minijinja::{Environment, Value as JinjaValue, Error as JinjaError};
use serde::Serialize;
use serde_json::Value;
use serde_json::ser::{Formatter, Serializer};
use std::io::{self, Write};

/// Python 风格的 JSON 格式化器（冒号后有空格，与 Python json.dumps 一致）
struct PythonStyleFormatter;

impl Formatter for PythonStyleFormatter {
    fn begin_object_value<W: ?Sized + Write>(&mut self, writer: &mut W) -> io::Result<()> {
        writer.write_all(b": ") // 冒号后加空格
    }

    fn begin_array_value<W: ?Sized + Write>(&mut self, writer: &mut W, first: bool) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ") // 逗号后加空格
        }
    }

    fn begin_object_key<W: ?Sized + Write>(&mut self, writer: &mut W, first: bool) -> io::Result<()> {
        if first {
            Ok(())
        } else {
            writer.write_all(b", ")
        }
    }
}

/// 生成 Python 风格的 JSON 字符串（与 Python json.dumps 格式一致）
fn to_string_python_style<T: Serialize>(value: &T) -> serde_json::Result<String> {
    let mut buf = Vec::new();
    let mut serializer = Serializer::with_formatter(&mut buf, PythonStyleFormatter);
    value.serialize(&mut serializer)?;
    Ok(String::from_utf8(buf).unwrap())
}

/// Default Qwen2.5 ChatML template (Jinja2 format)
///
/// This template is adapted from tokenizer_config.json for minijinja compatibility.
/// The template supports:
/// - Multi-modal content (images, videos)
/// - Tool/function calling
/// - Reasoning/thinking content
/// - System messages
const DEFAULT_QWEN_TEMPLATE: &str = include_str!("qwen_chat_template.jinja");

/// Qwen chat template using MiniJinja
///
/// Uses the ChatML format:
/// ```text
/// <|im_start|>system
/// You are a helpful assistant.<|im_end|>
/// <|im_start|>user
/// Hello<|im_end|>
/// <|im_start|>assistant
/// ```
pub struct QwenChatTemplate {
    name: String,
    template_str: String,
}

impl QwenChatTemplate {
    /// Create a new Qwen chat template with default template
    pub fn new() -> Self {
        Self::with_template(DEFAULT_QWEN_TEMPLATE).expect("Default template should be valid")
    }

    /// Create a new Qwen chat template with custom Jinja2 template
    ///
    /// # Arguments
    /// * `template_str` - Jinja2 template string (HuggingFace format)
    ///
    /// # Returns
    /// Result containing the template or an error if template is invalid
    /// Create a configured MiniJinja environment with required filters
    fn create_env() -> Environment<'static> {
        let mut env = Environment::new();
        
        // Add tojson filter for JSON serialization (Python-compatible format)
        env.add_filter("tojson", |value: JinjaValue| -> Result<String, JinjaError> {
            Ok(to_string_python_style(&value).unwrap_or_else(|_| "null".to_string()))
        });

        // Add Python-compatible string methods as functions
        // startswith(string, prefix) -> bool
        env.add_function("startswith", |s: &str, prefix: &str| -> bool {
            s.starts_with(prefix)
        });

        // endswith(string, suffix) -> bool
        env.add_function("endswith", |s: &str, suffix: &str| -> bool {
            s.ends_with(suffix)
        });

        // split(string, delimiter) -> list
        env.add_filter("split", |s: &str, delimiter: &str| -> Vec<String> {
            s.split(delimiter).map(|x| x.to_string()).collect()
        });

        // rstrip filter (strip trailing whitespace or specific chars)
        env.add_filter("rstrip", |s: &str, chars: Option<&str>| -> String {
            match chars {
                Some(c) => s.trim_end_matches(|ch: char| c.contains(ch)).to_string(),
                None => s.trim_end().to_string(),
            }
        });

        // lstrip filter (strip leading whitespace or specific chars)
        env.add_filter("lstrip", |s: &str, chars: Option<&str>| -> String {
            match chars {
                Some(c) => s.trim_start_matches(|ch: char| c.contains(ch)).to_string(),
                None => s.trim_start().to_string(),
            }
        });

        // raise_exception function for template errors
        env.add_function("raise_exception", |msg: &str| -> Result<String, JinjaError> {
            Err(JinjaError::new(
                minijinja::ErrorKind::InvalidOperation,
                msg.to_string(),
            ))
        });
        
        env
    }

    pub fn with_template(template_str: &str) -> Result<Self> {
        // Validate the template by trying to parse it
        let mut env = Self::create_env();
        env.add_template("chat_template", template_str)
            .context("Failed to parse chat template")?;
        
        // Drop the env, we only need to validate
        drop(env);

        Ok(Self {
            name: "qwen".to_string(),
            template_str: template_str.to_string(),
        })
    }

    /// Create a new Qwen chat template from tokenizer.json content
    ///
    /// # Arguments
    /// * `tokenizer_json` - Content of tokenizer.json file
    ///
    /// # Returns
    /// Result containing the template or an error
    pub fn from_tokenizer_json(tokenizer_json: &str) -> Result<Self> {
        let json: Value = serde_json::from_str(tokenizer_json)
            .context("Failed to parse tokenizer.json")?;

        let template = json
            .get("chat_template")
            .and_then(|v| v.as_str())
            .unwrap_or(DEFAULT_QWEN_TEMPLATE);

        Self::with_template(template)
    }

    /// Get the template string
    pub fn template_str(&self) -> &str {
        &self.template_str
    }

    /// Format a single message (public for reuse)
    pub fn format_message(&self, message: &OpenAIChatMessage) -> String {
        let role = match message.role {
            MessageRole::System => "system",
            MessageRole::Developer => "developer",
            MessageRole::User => "user",
            MessageRole::Assistant => "assistant",
            MessageRole::Tool => "tool",
        };

        let content = message.content.as_ref().map(|c| c.as_text()).unwrap_or_default();

        // Include reasoning_content if present (for models like Qwen with reasoning)
        let formatted = if let Some(ref reasoning) = message.reasoning_content {
            if !reasoning.is_empty() {
                format!("{}<|im_start|>{}\n{}<|im_end|>\n", reasoning, role, content)
            } else {
                format!("<|im_start|>{}\n{}<|im_end|>\n", role, content)
            }
        } else {
            format!("<|im_start|>{}\n{}<|im_end|>\n", role, content)
        };

        formatted
    }
}

impl Default for QwenChatTemplate {
    fn default() -> Self {
        Self::new()
    }
}

impl ChatTemplate for QwenChatTemplate {
    fn format_messages(&self, messages: &[OpenAIChatMessage]) -> String {
        let mut result = String::new();
        for msg in messages {
            result.push_str(&self.format_message(msg));
        }
        // Add assistant prefix at the end for token counting
        result.push_str("<|im_start|>assistant\n");
        result
    }

    fn apply_chat_template(&self, messages: &[Value], add_generation_prompt: bool) -> Result<String> {
        self.apply_chat_template_with_tools(messages, None, add_generation_prompt)
    }

    fn apply_chat_template_with_tools(
        &self,
        messages: &[Value],
        tools: Option<&[Value]>,
        add_generation_prompt: bool,
    ) -> Result<String> {
        // Create a new environment for each render to avoid lifetime issues
        let mut env = QwenChatTemplate::create_env();
        env.add_template("chat_template", &self.template_str)
            .context("Failed to parse chat template")?;
        
        let template = env
            .get_template("chat_template")
            .context("Failed to get chat template")?;

        // Pre-process messages: parse tool_call arguments from JSON string to object
        // This mirrors the Python approach in test.py
        let processed_messages: Vec<Value> = messages.iter().map(|msg| {
            let mut msg = msg.clone();
            if let Some(tool_calls) = msg.get_mut("tool_calls").and_then(|tc| tc.as_array_mut()) {
                for tool_call in tool_calls.iter_mut() {
                    if let Some(func) = tool_call.get_mut("function") {
                        if let Some(args) = func.get("arguments") {
                            if let Some(args_str) = args.as_str() {
                                // Try to parse arguments string as JSON object
                                if let Ok(parsed) = serde_json::from_str::<Value>(args_str) {
                                    func["arguments"] = parsed;
                                }
                            }
                        }
                    }
                }
            }
            msg
        }).collect();

        // Convert messages to JinjaValue
        let messages_value = JinjaValue::from_serialize(&processed_messages);

        // Convert tools: use provided tools or empty vec
        let tools_value = match tools {
            Some(t) if !t.is_empty() => JinjaValue::from_serialize(t),
            _ => JinjaValue::from_serialize(Vec::<Value>::new()),
        };
        // println!("Rendering template with messages: {:?}", messages_value);
        let result = template
            .render(minijinja::context! {
                messages => messages_value,
                add_generation_prompt => add_generation_prompt,
                // Provide default values for optional variables used in the template
                add_vision_id => false,
                enable_thinking => true,
                tools => tools_value,
            })
            .context(format!("Failed to render chat template: {}", serde_json::to_string(messages).unwrap())).unwrap();
        // println!("Rendered template: {}", result);
        Ok(result)
    }

    fn template_name(&self) -> &str {
        &self.name
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::analyzer::{OpenAIChatMessage, OpenAIContent};

    #[test]
    fn test_qwen_format_single_message() {
        let template = QwenChatTemplate::new();
        let msg = OpenAIChatMessage {
            role: MessageRole::User,
            content: Some(OpenAIContent::Text("Hello".to_string())),
            reasoning_content: None,
            refusal: None,
            function_call: None,
            tool_calls: None,
            tool_call_id: None,
            name: None,
            annotations: None,
            audio: None,
        };

        let formatted = template.format_message(&msg);
        assert_eq!(formatted, "<|im_start|>user\nHello<|im_end|>\n");
    }

    #[test]
    fn test_qwen_format_messages() {
        let template = QwenChatTemplate::new();
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

        let formatted = template.format_messages(&messages);
        assert!(formatted.contains("<|im_start|>system"));
        assert!(formatted.contains("<|im_start|>user"));
        assert!(formatted.ends_with("<|im_start|>assistant\n"));
    }

    #[test]
    fn test_apply_chat_template_basic() {
        let template = QwenChatTemplate::new();
        let messages = vec![
            serde_json::json!({
                "role": "system",
                "content": "You are a helpful assistant."
            }),
            serde_json::json!({
                "role": "user",
                "content": "Hello"
            }),
        ];

        let result = template.apply_chat_template(&messages, true).unwrap();
        assert!(result.contains("<|im_start|>system"));
        assert!(result.contains("You are a helpful assistant."));
        assert!(result.contains("<|im_start|>user"));
        assert!(result.contains("Hello"));
        assert!(result.contains("<|im_start|>assistant"));
    }

    #[test]
    fn test_apply_chat_template_without_generation_prompt() {
        let template = QwenChatTemplate::new();
        let messages = vec![
            serde_json::json!({
                "role": "user",
                "content": "Hi"
            }),
        ];

        let result = template.apply_chat_template(&messages, false).unwrap();
        assert!(result.contains("<|im_start|>user"));
        assert!(result.contains("Hi"));
        // Without add_generation_prompt, should not end with assistant
        assert!(!result.contains("<|im_start|>assistant"));
    }

    #[test]
    fn test_apply_chat_template_with_reasoning() {
        let template = QwenChatTemplate::new();
        let messages = vec![
            serde_json::json!({
                "role": "user",
                "content": "What is the answer to life?"
            }),
            serde_json::json!({
                "role": "assistant",
                "content": "The answer is 42.",
                "reasoning_content": "Let me think..."
            }),
        ];

        let result = template.apply_chat_template(&messages, false).unwrap();
        assert!(result.contains("<|im_start|>assistant"));
        assert!(result.contains("The answer is 42."));
    }

    #[test]
    fn test_from_tokenizer_json() {
        let tokenizer_json = r#"{
            "chat_template": "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}"
        }"#;

        let template = QwenChatTemplate::from_tokenizer_json(tokenizer_json).unwrap();
        assert_eq!(template.template_str(), "{% for message in messages %}{{ message['role'] }}: {{ message['content'] }}\n{% endfor %}");

        let messages = vec![
            serde_json::json!({
                "role": "user",
                "content": "Hello"
            }),
        ];

        let result = template.apply_chat_template(&messages, false).unwrap();
        assert!(result.contains("user: Hello"));
    }

    #[test]
    fn test_from_tokenizer_json_fallback_to_default() {
        // tokenizer.json without chat_template field
        let tokenizer_json = r#"{"tokenizer_class": "PreTrainedTokenizer"}"#;

        let template = QwenChatTemplate::from_tokenizer_json(tokenizer_json).unwrap();
        // Should use default template
        assert!(template.template_str().contains("<|im_start|>"));
    }

    #[test]
    fn test_with_template_invalid() {
        let result = QwenChatTemplate::with_template("{% invalid syntax");
        assert!(result.is_err());
    }

    #[test]
    fn test_apply_chat_template_with_array_content() {
        // Test the format from test.json with array content
        let template = QwenChatTemplate::new();
        let messages = vec![
            serde_json::json!({
                "role": "system",
                "content": "You are a helpful assistant."
            }),
            serde_json::json!({
                "role": "user",
                "content": [
                    {
                        "text": "Sender (untrusted metadata):\n```json\n{}
```\n\n[Tue 2026-03-24 23:32 GMT+8] ls",
                        "type": "text"
                    }
                ]
            }),
            serde_json::json!({
                "role": "assistant",
                "content": null,
                "reasoning_content": "The user is asking me to run `ls` command.",
                "tool_calls": [
                    {
                        "function": {
                            "arguments": "{\"command\":\"ls -la\"}",
                            "name": "exec"
                        },
                        "id": "call123",
                        "type": "function"
                    }
                ]
            }),
            serde_json::json!({
                "role": "tool",
                "content": "total 68\ndrwxrwxr-x  8 admin admin 4096",
                "tool_call_id": "call123"
            }),
        ];

        let result = template.apply_chat_template(&messages, true);
        println!("Result: {:?}", result);
        assert!(result.is_ok(), "Failed to apply chat template: {:?}", result.err());
        
        let formatted = result.unwrap();
        assert!(formatted.contains("<|im_start|>system"));
        assert!(formatted.contains("<|im_start|>user"));
        assert!(formatted.contains("<|im_start|>assistant"));
    }
}
