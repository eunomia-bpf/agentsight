//! Fallback tokenizer - byte-based token estimation
//!
//! Provides a simple tokenizer implementation that estimates token counts
//! based on byte/character counts. Used as a fallback when no proper
//! tokenizer is available.
//!
//! # Estimation Strategy
//!
//! - English text: ~4 characters per token (0.25 ratio)
//! - Chinese/Unicode text: ~1-2 characters per token (0.5-1.0 ratio)
//!
//! This implementation uses a conservative estimate of 0.3 tokens per byte
//! for mixed content, which tends to over-count rather than under-count.

use anyhow::Result;

use crate::tokenizer::core::Tokenizer;

/// Byte-based tokenizer for fallback token estimation
///
/// This tokenizer provides approximate token counts when no proper
/// tokenizer model is available. It uses character/byte heuristics
/// to estimate token counts.
pub struct ByteCountTokenizer {
    model_name: String,
    /// Characters per token ratio (default: 4.0 for English-like text)
    chars_per_token: f32,
}

impl ByteCountTokenizer {
    /// Create a new byte-based tokenizer with default settings
    ///
    /// # Example
    /// ```rust,ignore
    /// let tokenizer = ByteCountTokenizer::new();
    /// let count = tokenizer.count("Hello, world!")?;
    /// ```
    pub fn new() -> Self {
        Self {
            model_name: "byte-count-fallback".to_string(),
            chars_per_token: 4.0, // Conservative estimate: ~4 chars per token
        }
    }

    /// Create with custom chars-per-token ratio
    ///
    /// # Arguments
    /// * `chars_per_token` - Expected characters per token (e.g., 4.0 for English, 1.5 for Chinese)
    pub fn with_ratio(chars_per_token: f32) -> Self {
        Self {
            model_name: "byte-count-fallback".to_string(),
            chars_per_token: chars_per_token.max(1.0),
        }
    }

    /// Estimate token count from text
    ///
    /// Uses a simple heuristic:
    /// - Count Unicode characters
    /// - Divide by chars_per_token ratio
    /// - Return as ceiling integer
    fn estimate_tokens(&self, text: &str) -> usize {
        let char_count = text.chars().count();
        let estimated = (char_count as f32) / self.chars_per_token;
        estimated.ceil() as usize
    }
}

impl Default for ByteCountTokenizer {
    fn default() -> Self {
        Self::new()
    }
}

impl Tokenizer for ByteCountTokenizer {
    fn count(&self, text: &str) -> Result<usize> {
        Ok(self.estimate_tokens(text))
    }

    fn encode(&self, text: &str) -> Result<Vec<u32>> {
        // Generate pseudo-token IDs based on character positions
        // This is not a real encoding, just for API compatibility
        let token_count = self.estimate_tokens(text);
        Ok((0..token_count).map(|i| i as u32).collect())
    }

    fn decode(&self, tokens: &[u32]) -> Result<String> {
        // Cannot decode from pseudo-token IDs
        // Return placeholder text
        Ok(format!("[{} tokens]", tokens.len()))
    }

    fn model_name(&self) -> &str {
        &self.model_name
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_byte_tokenizer_english() {
        let tokenizer = ByteCountTokenizer::new();
        // "Hello, world!" = 13 chars, ~3-4 tokens expected
        let count = tokenizer.count("Hello, world!").unwrap();
        assert!(count >= 3 && count <= 4);
    }

    #[test]
    fn test_byte_tokenizer_chinese() {
        // Chinese needs different ratio
        let tokenizer = ByteCountTokenizer::with_ratio(1.5);
        // "你好世界" = 4 chars, ~2-3 tokens expected
        let count = tokenizer.count("你好世界").unwrap();
        assert!(count >= 2 && count <= 3);
    }

    #[test]
    fn test_byte_tokenizer_empty() {
        let tokenizer = ByteCountTokenizer::new();
        assert_eq!(tokenizer.count("").unwrap(), 0);
    }

    #[test]
    fn test_encode_decode() {
        let tokenizer = ByteCountTokenizer::new();
        let text = "Test";
        let tokens = tokenizer.encode(text).unwrap();
        assert!(!tokens.is_empty());
        let decoded = tokenizer.decode(&tokens).unwrap();
        assert!(decoded.contains("tokens"));
    }
}
