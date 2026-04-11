//! Token Data Extractor - Internal module for extracting tokenizable content from JSON
//!
//! This module provides internal functionality to extract text content that would be
//! counted as tokens from raw JSON request/response bodies.
//!
//! Unlike the message parser which deserializes into structured types,
//! this extractor works directly with JSON values to extract text content
//! for local token counting.
//!
//! # Supported Providers
//! - OpenAI (GPT-4, GPT-3.5, etc.)
//! - Anthropic (Claude)
//!
//! Note: This module is for internal use only and not exposed in the public API.

pub mod openai;
mod anthropic;
mod utils;

use serde_json::Value;
use super::data::{TokenData, MessageTokenData, ResponseTokenData};

/// Extract token data from JSON request/response bodies
///
/// This function automatically detects the protocol format from the URL path
/// and/or JSON content, then dispatches to the appropriate extractor.
///
/// For standard paths like `/v1/chat/completions` or `/v1/messages`, the
/// provider is determined by the path itself.
///
/// For compatible mode paths like `/compatible-mode/v1/chat/completions`,
/// the provider is detected from the JSON content structure.
///
/// # Arguments
/// * `path` - The API endpoint path (used to detect provider)
/// * `request_json` - Optional request body as JSON
/// * `response_json` - Optional response body as JSON
///
/// # Returns
/// * `Some(TokenData)` if content could be extracted
/// * `None` if path doesn't match known endpoints or no content found
///
/// # Example
/// ```rust,ignore
/// use agentsight::analyzer::token::extract_token_data_from_json;
///
/// // Standard OpenAI path
/// let token_data = extract_token_data_from_json(
///     "/v1/chat/completions",
///     Some(&request_json),
///     None
/// );
///
/// // Compatible mode path (auto-detects format from JSON)
/// let token_data = extract_token_data_from_json(
///     "/compatible-mode/v1/chat/completions",
///     Some(&request_json),
///     None
/// );
/// ```
pub fn extract_token_data_from_json(
    path: &str,
    request_json: Option<&Value>,
    response_json: Option<&Value>,
) -> Option<TokenData> {
    let provider = utils::detect_provider(path, request_json)?;

    match provider {
        Provider::OpenAI => openai::extract_token_data(request_json, response_json),
        Provider::Anthropic => anthropic::extract_token_data(request_json, response_json),
    }
}

/// Provider type for extractor
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Provider {
    OpenAI,
    Anthropic,
}

// Re-export utility functions for internal use
pub use utils::extract_model_from_json;
