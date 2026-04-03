//! Tokenizer module - text to token count conversion
//!
//! Provides tokenizer implementations for various LLM models.
//! Uses `llm-tokenizer` crate for tokenization and chat template rendering.

pub mod llm_tok;
pub mod multi_model;

// Re-export types
pub use llm_tok::LlmTokenizer;
pub use multi_model::{
    MultiModelTokenizer, TokenizerEntry,
    // Global instance functions
    init_global_tokenizer, set_global_tokenizer, get_global_tokenizer,
    is_global_tokenizer_initialized,
    register_global_tokenizer, set_global_default_model,
};
