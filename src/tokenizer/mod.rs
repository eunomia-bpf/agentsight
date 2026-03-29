//! Tokenizer module - text to token count conversion
//!
//! Provides tokenizer implementations for various LLM models.
//! Uses Hugging Face tokenizers library for tokenization.
//!
//! # Supported Models
//! - Qwen series (Qwen3.5 Plus, Qwen2.5, Qwen2)
//!
//! # Architecture
//!
//! This module is organized into submodules:
//! - [`core`] - Core traits and types (Tokenizer trait, ChatTemplate trait, etc.)
//! - [`model`] - Model definitions and detection (TokenizerModel enum)
//! - [`providers`] - Model-specific tokenizer implementations (Qwen, etc.)
//! - [`templates`] - Chat template implementations for formatting messages
//! - [`registry`] - Tokenizer registry with automatic model detection
//! - [`factory`] - Factory functions for creating tokenizers
//!
//! # Usage
//!
//! ```rust,ignore
//! use agentsight::tokenizer::{TokenizerRegistry, TokenizerModel, create_tokenizer_registry};
//!
//! // Create registry with automatic model detection
//! let registry = create_tokenizer_registry(TokenizerModel::Qwen35Plus, "/path/to/tokenizer.json")?;
//! let breakdown = registry.count_request(&openai_request)?;
//! println!("Prompt tokens: {}", breakdown.prompt_tokens);
//! ```

pub mod core;
pub mod model;
pub mod providers;
pub mod templates;
pub mod registry;
pub mod factory;

// Re-export core types
pub use core::{Tokenizer, ChatTemplate, ChatTemplateType, ChatTokenCount};

// Re-export model types
pub use model::TokenizerModel;

// Re-export provider types
pub use providers::QwenTokenizer;

// Re-export template types
pub use templates::QwenChatTemplate;

// Re-export registry types and functions
pub use registry::{TokenizerRegistry, TokenCountBreakdown, count_chat_tokens};

// Re-export factory functions
pub use factory::{
    create_tokenizer,
    create_tokenizer_from_file,
    create_tokenizer_from_url,
    create_tokenizer_registry,
    create_tokenizer_registry_from_file,
    create_tokenizer_registry_multi,
    create_chat_template_from_file,
    create_chat_template_from_json,
    create_chat_template_with_template,
};

// Deprecated re-exports for backward compatibility
#[deprecated(since = "0.2.0", note = "Use TokenizerRegistry instead")]
pub use registry::TokenizerRegistry as UnifiedTokenizer;

#[deprecated(since = "0.2.0", note = "Use create_tokenizer_registry instead")]
pub use factory::create_tokenizer_registry as create_unified_tokenizer;

#[deprecated(since = "0.2.0", note = "Use create_tokenizer_registry_from_file instead")]
pub use factory::create_tokenizer_registry_from_file as create_unified_tokenizer_from_file;

#[deprecated(since = "0.2.0", note = "Use create_tokenizer_registry_multi instead")]
pub use factory::create_tokenizer_registry_multi as create_unified_tokenizer_multi;
