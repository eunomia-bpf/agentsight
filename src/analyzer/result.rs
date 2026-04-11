//! Analysis result types
//!
//! This module defines the `AnalysisResult` enum which represents
//! the output from different analyzers.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use super::{AuditRecord, TokenRecord, ParsedApiMessage};

/// Computed prompt token count for a request
#[derive(Debug, Clone)]
pub struct PromptTokenCount {
    /// Provider name (e.g., "openai", "anthropic")
    pub provider: String,
    /// Model name
    pub model: String,
    /// Number of messages in the request
    pub message_count: usize,
    /// Total prompt tokens computed by tokenizer
    pub prompt_tokens: usize,
    /// Per-message token counts
    pub per_message_tokens: Vec<usize>,
    /// Formatted prompt (for debugging)
    pub formatted_prompt: String,
}

/// HTTP request/response record for persistence
///
/// Contains the key fields from an HTTP exchange suitable for
/// storage and later querying.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HttpRecord {
    /// Timestamp in nanoseconds since Unix epoch (from request)
    pub timestamp_ns: u64,
    /// Process ID
    pub pid: u32,
    /// Process command name
    pub comm: String,
    /// HTTP method (GET, POST, etc.)
    pub method: String,
    /// Request path (e.g., "/v1/chat/completions")
    pub path: String,
    /// HTTP status code (e.g., 200)
    pub status_code: u16,
    /// Request headers as JSON string
    pub request_headers: String,
    /// Request body (JSON string if parseable, otherwise raw text)
    pub request_body: Option<String>,
    /// Response headers as JSON string
    pub response_headers: String,
    /// Response body (JSON string for non-SSE, aggregated SSE payloads for SSE)
    pub response_body: Option<String>,
    /// Duration in nanoseconds (response end - request start)
    pub duration_ns: u64,
    /// Whether this is an SSE streaming response
    pub is_sse: bool,
    /// Number of SSE events (0 for non-SSE)
    pub sse_event_count: usize,
}

/// Token consumption breakdown by message role
///
/// This struct provides detailed token counting for each message role
/// (system, user, assistant, tool) in a request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenConsumptionBreakdown {
    /// Timestamp in nanoseconds since Unix epoch (from the originating HTTP request)
    pub timestamp_ns: u64,
    /// Process ID of the agent process
    pub pid: u32,
    /// Process command name
    pub comm: String,
    /// Provider type (openai, anthropic, etc.)
    pub provider: String,
    /// Model name
    pub model: String,
    /// Total input tokens (from all request messages)
    pub total_input_tokens: usize,
    /// Total output tokens (from response)
    pub total_output_tokens: usize,
    /// Token count by role (system, user, assistant, tool)
    pub by_role: HashMap<String, usize>,
    /// Per-message token counts with role information
    pub per_message: Vec<MessageTokenCount>,
    /// Tool definitions token count
    pub tools_tokens: usize,
    /// System prompt token count (for Anthropic-style separate system)
    pub system_prompt_tokens: usize,
    /// Output token count by content type (text, reasoning, tool_calls, refusal)
    pub output_by_type: HashMap<String, usize>,
    /// Per-content-block token counts for output
    pub output_per_block: Vec<OutputTokenCount>,
}

/// Per-content-block token count for output
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputTokenCount {
    /// Content type (text, reasoning, tool_use, refusal)
    pub content_type: String,
    /// Token count for this content block
    pub tokens: usize,
}

/// Per-message token count with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageTokenCount {
    /// Message role (system, user, assistant, tool)
    pub role: String,
    /// Token count for this message
    pub tokens: usize,
}

/// Unified analysis result from different analyzers
#[derive(Debug, Clone)]
pub enum AnalysisResult {
    /// Audit record from AuditAnalyzer
    Audit(AuditRecord),
    /// Token record from TokenParser (from SSE response)
    Token(TokenRecord),
    /// Parsed API message from MessageParser
    Message(ParsedApiMessage),
    /// Computed prompt token count (from tokenizer)
    PromptTokens(PromptTokenCount),
    /// HTTP request/response record
    Http(HttpRecord),
    /// Token consumption breakdown by message role
    TokenConsumption(TokenConsumptionBreakdown),
}
