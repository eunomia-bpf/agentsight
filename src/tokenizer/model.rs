//! Tokenizer model definitions and detection

use crate::tokenizer::core::ChatTemplateType;

/// Supported tokenizer models
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TokenizerModel {
    /// Qwen3.5 Plus (uses Qwen2.5 tokenizer)
    Qwen35Plus,
    /// Qwen2.5 series
    Qwen25,
    /// Qwen2 series
    Qwen2,
}

impl TokenizerModel {
    /// Get the default tokenizer filename for this model
    pub fn default_filename(&self) -> &'static str {
        match self {
            TokenizerModel::Qwen35Plus => "qwen25_tokenizer.json",
            TokenizerModel::Qwen25 => "qwen25_tokenizer.json",
            TokenizerModel::Qwen2 => "qwen2_tokenizer.json",
        }
    }

    /// Get the display name for this model
    pub fn display_name(&self) -> &'static str {
        match self {
            TokenizerModel::Qwen35Plus => "Qwen3.5-Plus",
            TokenizerModel::Qwen25 => "Qwen2.5",
            TokenizerModel::Qwen2 => "Qwen2",
        }
    }

    /// Detect model type from OpenAI/Anthropic model name
    pub fn from_model_name(model_name: &str) -> Option<Self> {
        let lower = model_name.to_lowercase();

        // Qwen models
        if lower.contains("qwen3.5") || lower.contains("qwen-3.5") {
            Some(TokenizerModel::Qwen35Plus)
        } else if lower.contains("qwen2.5") || lower.contains("qwen-2.5") {
            Some(TokenizerModel::Qwen25)
        } else if lower.contains("qwen2") || lower.contains("qwen-2") {
            Some(TokenizerModel::Qwen2)
        } else if lower.contains("qwen") {
            Some(TokenizerModel::Qwen25)
        }
        // OpenAI GPT models
        else if lower.contains("gpt-4") || lower.contains("gpt4") {
            Some(TokenizerModel::Qwen35Plus)
        } else if lower.contains("gpt-3.5") || lower.contains("gpt3.5") {
            Some(TokenizerModel::Qwen25)
        }
        // Anthropic Claude models
        else if lower.contains("claude-3") || lower.contains("claude3") {
            Some(TokenizerModel::Qwen35Plus)
        } else if lower.contains("claude") {
            Some(TokenizerModel::Qwen25)
        }
        // Default fallback
        else {
            None
        }
    }

    /// Get the corresponding chat template type for this model
    pub fn chat_template_type(&self) -> ChatTemplateType {
        match self {
            TokenizerModel::Qwen35Plus | TokenizerModel::Qwen25 | TokenizerModel::Qwen2 => {
                ChatTemplateType::Qwen
            }
        }
    }
}

impl std::fmt::Display for TokenizerModel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.display_name())
    }
}
