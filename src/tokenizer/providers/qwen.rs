//! Qwen tokenizer implementation
//!
//! Uses Hugging Face tokenizers library to load Qwen tokenizers from local files or URLs.
//! Supports Qwen3.5 Plus, Qwen2.5, and Qwen2 series models.
//!
//! # Usage
//!
//! ```rust,ignore
//! use agentsight::tokenizer::QwenTokenizer;
//!
//! // Load from a local file
//! let tokenizer = QwenTokenizer::from_file("/path/to/tokenizer.json", "Qwen3.5-Plus")?;
//! let count = tokenizer.count("Hello, world!")?;
//!
//! // Load from URL
//! let tokenizer = QwenTokenizer::from_url(
//!     "https://www.modelscope.cn/models/Qwen/Qwen3.5-27B/resolve/master/tokenizer.json",
//!     "Qwen3.5-27B"
//! )?;
//! ```

use anyhow::{anyhow, Result};
use std::io::Write;
use std::path::Path;
use tempfile::NamedTempFile;
use tokenizers::Tokenizer as HFTokenizer;

use crate::tokenizer::core::Tokenizer;

/// Qwen tokenizer wrapper
///
/// This struct wraps a Hugging Face tokenizer and provides
/// a simplified interface for text to token conversion.
pub struct QwenTokenizer {
    tokenizer: HFTokenizer,
    model_name: String,
}

impl QwenTokenizer {
    /// Create a tokenizer from a local file
    ///
    /// # Arguments
    /// * `path` - Path to the tokenizer.json file
    /// * `model_name` - Human-readable name for the model
    ///
    /// # Example
    /// ```rust,ignore
    /// let tokenizer = QwenTokenizer::from_file("/path/to/tokenizer.json", "Qwen3.5-Plus")?;
    /// ```
    pub fn from_file<P: AsRef<Path>>(path: P, model_name: &str) -> Result<Self> {
        let path = path.as_ref();
        let tokenizer = HFTokenizer::from_file(path)
            .map_err(|e| anyhow!("Failed to load tokenizer from file '{}': {}", path.display(), e))?;

        Ok(Self {
            tokenizer,
            model_name: model_name.to_string(),
        })
    }

    /// Create a tokenizer from a URL
    ///
    /// Downloads the tokenizer.json file from the given URL and loads it.
    /// The file is downloaded to a temporary location and loaded from there.
    ///
    /// # Arguments
    /// * `url` - URL to the tokenizer.json file
    /// * `model_name` - Human-readable name for the model
    ///
    /// # Example
    /// ```rust,ignore
    /// let tokenizer = QwenTokenizer::from_url(
    ///     "https://www.modelscope.cn/models/Qwen/Qwen3.5-27B/resolve/master/tokenizer.json",
    ///     "Qwen3.5-27B"
    /// )?;
    /// ```
    pub fn from_url(url: &str, model_name: &str) -> Result<Self> {
        // Download to a temporary file
        let mut temp_file = NamedTempFile::new()
            .map_err(|e| anyhow!("Failed to create temporary file: {}", e))?;

        let response = ureq::get(url)
            .call()
            .map_err(|e| anyhow!("Failed to download tokenizer from '{}': {}", url, e))?;

        let mut reader = response.into_reader();
        std::io::copy(&mut reader, &mut temp_file)
            .map_err(|e| anyhow!("Failed to write tokenizer to temporary file: {}", e))?;

        // Flush and get the path
        temp_file.flush()
            .map_err(|e| anyhow!("Failed to flush temporary file: {}", e))?;

        let temp_path = temp_file.path();

        // Load tokenizer from the temporary file
        let tokenizer = HFTokenizer::from_file(temp_path)
            .map_err(|e| anyhow!("Failed to load tokenizer from temporary file: {}", e))?;

        Ok(Self {
            tokenizer,
            model_name: model_name.to_string(),
        })
    }

    /// Count tokens in the given text
    ///
    /// This is a convenience method that returns just the count.
    pub fn count_tokens(&self, text: &str) -> Result<usize> {
        self.count(text)
    }

    /// Encode text with special tokens
    ///
    /// By default, special tokens (like <|im_start|>, <|im_end|>) are included.
    pub fn encode_with_special_tokens(&self, text: &str) -> Result<Vec<u32>> {
        let encoding = self
            .tokenizer
            .encode(text, true)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;

        Ok(encoding.get_ids().to_vec())
    }

    /// Encode text without special tokens
    pub fn encode_without_special_tokens(&self, text: &str) -> Result<Vec<u32>> {
        let encoding = self
            .tokenizer
            .encode(text, false)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;

        Ok(encoding.get_ids().to_vec())
    }

    /// Get the vocabulary size
    pub fn vocab_size(&self) -> usize {
        self.tokenizer.get_vocab_size(true)
    }
}

impl Tokenizer for QwenTokenizer {
    /// Count the number of tokens in the text
    fn count(&self, text: &str) -> Result<usize> {
        let encoding = self
            .tokenizer
            .encode(text, false)
            .map_err(|e| anyhow!("Failed to encode text: {}", e))?;

        Ok(encoding.len())
    }

    /// Encode text into token IDs
    fn encode(&self, text: &str) -> Result<Vec<u32>> {
        self.encode_without_special_tokens(text)
    }

    /// Decode token IDs back to text
    fn decode(&self, tokens: &[u32]) -> Result<String> {
        self.tokenizer
            .decode(tokens, false)
            .map_err(|e| anyhow!("Failed to decode tokens: {}", e))
    }

    /// Get the model name
    fn model_name(&self) -> &str {
        &self.model_name
    }
}

impl std::fmt::Debug for QwenTokenizer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("QwenTokenizer")
            .field("model_name", &self.model_name)
            .field("vocab_size", &self.vocab_size())
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_from_file() {
        // Skip if no test tokenizer file is available
        if std::env::var("TOKENIZER_TEST_FILE").is_err() {
            return;
        }

        let path = std::env::var("TOKENIZER_TEST_FILE").unwrap();
        let tokenizer = QwenTokenizer::from_file(&path, "test").expect("Failed to load tokenizer");

        // Test basic text
        let text = "Hello, world!";
        let count = tokenizer.count(text).expect("Failed to count tokens");
        assert!(count > 0, "Token count should be positive");

        // Test encoding/decoding roundtrip
        let tokens = tokenizer.encode(text).expect("Failed to encode");
        let decoded = tokenizer.decode(&tokens).expect("Failed to decode");
        assert_eq!(decoded, text, "Roundtrip should preserve text");
    }

    #[test]
    fn test_chinese_text() {
        if std::env::var("TOKENIZER_TEST_FILE").is_err() {
            return;
        }

        let path = std::env::var("TOKENIZER_TEST_FILE").unwrap();
        let tokenizer = QwenTokenizer::from_file(&path, "test").expect("Failed to load tokenizer");

        // Test Chinese text
        let text = "你好，世界！";
        let count = tokenizer.count(text).expect("Failed to count tokens");
        assert!(count > 0, "Token count should be positive for Chinese text");

        // Test encoding/decoding roundtrip
        let tokens = tokenizer.encode(text).expect("Failed to encode");
        let decoded = tokenizer.decode(&tokens).expect("Failed to decode");
        assert_eq!(decoded, text, "Roundtrip should preserve Chinese text");
    }
}
