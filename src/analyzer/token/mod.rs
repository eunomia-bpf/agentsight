//! Token usage tracking module for AgentSight
//!
//! This module provides functionality for:
//! - Extracting token usage from LLM API responses (OpenAI, Anthropic, etc.)
//! - Token record types for storage
//!
//! # Submodules
//!
//! - [`types`] - Core type definitions (TokenRecord, TokenUsage, etc.)
//! - [`parser`] - SSE event parser for extracting token usage from streaming responses
//!
//! # Example
//!
//! ```rust,ignore
//! use agentsight::analyzer::token::TokenParser;
//!
//! // Parse token usage from SSE events
//! let parser = TokenParser::new();
//! for event in sse_events {
//!     if let Some(usage) = parser.parse_event(&event) {
//!         println!("Tokens: {} in, {} out", usage.input_tokens, usage.output_tokens);
//!     }
//! }
//! ```

mod record;
mod data;
mod parser;

// Extractor submodule for JSON token data extraction
mod extractor;
pub use extractor::extract_token_data_from_json;
pub use extractor::openai::extract_response_content;

// Re-export record types
pub use record::TokenRecord;

// Data types are kept for internal use but not re-exported
// pub use data::{TokenData, MessageTokenData, ResponseTokenData};

// Re-export parser
pub use parser::TokenParser;

use serde::{Deserialize, Serialize};

// ============================================================================
// Shared Types
// ============================================================================

/// LLM Provider type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum LLMProvider {
    #[default]
    Unknown,
    OpenAI,
    Anthropic,
    Gemini,
}

impl std::fmt::Display for LLMProvider {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LLMProvider::OpenAI => write!(f, "openai"),
            LLMProvider::Anthropic => write!(f, "anthropic"),
            LLMProvider::Gemini => write!(f, "gemini"),
            LLMProvider::Unknown => write!(f, "unknown"),
        }
    }
}

impl std::str::FromStr for LLMProvider {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "openai" | "gpt" => Ok(LLMProvider::OpenAI),
            "anthropic" | "claude" => Ok(LLMProvider::Anthropic),
            "gemini" | "google" => Ok(LLMProvider::Gemini),
            _ => Ok(LLMProvider::Unknown),
        }
    }
}

/// Extracted token usage information
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TokenUsage {
    /// Input/prompt tokens
    pub input_tokens: u64,
    /// Output/completion tokens
    pub output_tokens: u64,
    /// Cache creation input tokens (Anthropic)
    pub cache_creation_input_tokens: Option<u64>,
    /// Cache read input tokens (Anthropic)
    pub cache_read_input_tokens: Option<u64>,
    /// Model name
    pub model: Option<String>,
    /// Provider detected
    pub provider: LLMProvider,
}

impl TokenUsage {
    /// Total tokens (input + output)
    pub fn total_tokens(&self) -> u64 {
        self.input_tokens + self.output_tokens
    }

    /// Check if usage is empty
    pub fn is_empty(&self) -> bool {
        self.input_tokens == 0 && self.output_tokens == 0
    }
}

// ============================================================================
// Shared Utility Functions
// ============================================================================

/// Extract usage from a JSON usage object
///
/// This is the core extraction logic used by TokenParser.
pub fn extract_usage_object(
    usage: &serde_json::Value,
    provider: LLMProvider,
    full_json: &serde_json::Value,
) -> Option<TokenUsage> {
    let (input_tokens, output_tokens) = match provider {
        LLMProvider::OpenAI => {
            let input = usage.get("prompt_tokens").and_then(|v| v.as_u64())?;
            let output = usage.get("completion_tokens").and_then(|v| v.as_u64()).unwrap_or(0);
            (input, output)
        }
        LLMProvider::Anthropic => {
            let input = usage.get("input_tokens").and_then(|v| v.as_u64())?;
            let output = usage.get("output_tokens").and_then(|v| v.as_u64()).unwrap_or(0);
            (input, output)
        }
        LLMProvider::Gemini => {
            let input = usage.get("prompt_token_count").and_then(|v| v.as_u64())?;
            let output = usage
                .get("candidates_token_count")
                .and_then(|v| v.as_u64())
                .unwrap_or(0);
            (input, output)
        }
        LLMProvider::Unknown => {
            // Try OpenAI format first, then Anthropic
            if let (Some(input), Some(output)) = (
                usage.get("prompt_tokens").and_then(|v| v.as_u64()),
                usage.get("completion_tokens").and_then(|v| v.as_u64()),
            ) {
                (input, output)
            } else if let (Some(input), Some(output)) = (
                usage.get("input_tokens").and_then(|v| v.as_u64()),
                usage.get("output_tokens").and_then(|v| v.as_u64()),
            ) {
                (input, output)
            } else {
                return None;
            }
        }
    };

    // Extract cache tokens (Anthropic-specific)
    let cache_creation_input_tokens = usage
        .get("cache_creation_input_tokens")
        .and_then(|v| v.as_u64());
    let cache_read_input_tokens = usage
        .get("cache_read_input_tokens")
        .and_then(|v| v.as_u64());

    // Extract model name
    let model = full_json
        .get("model")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string());

    Some(TokenUsage {
        input_tokens,
        output_tokens,
        cache_creation_input_tokens,
        cache_read_input_tokens,
        model,
        provider,
    })
}

/// Detect provider from usage object structure
pub fn detect_provider_from_usage(usage: &serde_json::Value) -> LLMProvider {
    // Anthropic uses input_tokens/output_tokens
    if usage.get("input_tokens").is_some() && usage.get("output_tokens").is_some() {
        return LLMProvider::Anthropic;
    }

    // OpenAI uses prompt_tokens/completion_tokens
    if usage.get("prompt_tokens").is_some() && usage.get("completion_tokens").is_some() {
        return LLMProvider::OpenAI;
    }

    // Gemini uses prompt_token_count/candidates_token_count
    if usage.get("prompt_token_count").is_some() {
        return LLMProvider::Gemini;
    }

    LLMProvider::Unknown
}

/// Detect provider from API endpoint URL
pub fn detect_provider_from_endpoint(endpoint: Option<&str>) -> LLMProvider {
    match endpoint {
        Some(ep) if ep.contains("openai.com") || ep.contains("api.openai.com") => {
            LLMProvider::OpenAI
        }
        Some(ep) if ep.contains("anthropic.com") || ep.contains("api.anthropic.com") => {
            LLMProvider::Anthropic
        }
        Some(ep) if ep.contains("generativelanguage.googleapis.com")
            || ep.contains("gemini") =>
        {
            LLMProvider::Gemini
        }
        _ => LLMProvider::Unknown,
    }
}
