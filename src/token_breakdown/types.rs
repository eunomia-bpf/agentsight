//! Data structures for ChatML token consumption breakdown
//!
//! Defines all types used in the ChatML parsing and token breakdown pipeline:
//! - Input types: ChatMLBlock, ChatMLDocument
//! - Classification types: ConversationTurnType, ConversationTurn, ResponseData
//! - Output types: EventNode, SummaryItem, TokenBreakdownNode, ResponseItem, ChatMLTokenBreakdown

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// A single block from a ChatML document (between <|im_start|> and <|im_end|>)
#[derive(Debug, Clone)]
pub struct ChatMLBlock {
    /// Role of this block: "system", "user", or "assistant"
    pub role: String,
    /// Raw content text (after the role line, before <|im_end|>)
    pub raw_content: String,
}

/// Parsed ChatML document containing all blocks
#[derive(Debug, Clone)]
pub struct ChatMLDocument {
    /// All parsed blocks in order
    pub blocks: Vec<ChatMLBlock>,
    /// Original raw text of the entire file
    pub raw_text: String,
}

/// Type of a conversation message (used internally for classification)
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConversationTurnType {
    /// User message (role=user, no <tool_response>)
    UserMessage,
    /// Assistant text response (role=assistant, no <tool_call>)
    AssistantText,
    /// Tool call (role=assistant, contains <tool_call>)
    ToolCall,
    /// Tool response (role=user, contains <tool_response>)
    ToolResponse,
}

/// A single conversation message with its classification
#[derive(Debug, Clone)]
pub struct ConversationTurn {
    /// Type of this message (used for grouping, not serialized to output)
    pub turn_type: ConversationTurnType,
    /// Full text content of the message
    pub content: String,
    /// Whether this is a history message (true) or the current prompt (false)
    pub is_history: bool,
}

/// Response data from AggregatedResponse (SSE stream aggregation)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseData {
    /// Text content fragments from choices[].delta.content
    pub content: Vec<String>,
    /// Reasoning/thinking content from choices[].delta.reasoning_content (may be empty)
    pub reasoning_content: Option<String>,
    /// Tool calls in "name: arguments" format (may be empty)
    pub tool_calls: Vec<String>,
}

/// Result of classifying a ChatML document
#[derive(Debug, Clone)]
pub struct ClassifiedDocument {
    /// System prompt raw content (treated as a whole, no sub-segmentation)
    pub system_content: String,
    /// Classified conversation messages
    pub messages: Vec<ConversationTurn>,
    /// Response data from AggregatedResponse (optional)
    pub response: Option<ResponseData>,
}

// === Output types (serialized to JSON) ===

/// Summary statistics for a label category
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SummaryItem {
    /// Number of items with this label
    pub count: usize,
    /// Total tokens for this label
    pub tokens: usize,
    /// Percentage of event total tokens
    pub percentage: f64,
}

/// An event node in the events array (top-level element)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventNode {
    /// Event type identifier: "request" or "response"
    #[serde(rename = "type")]
    pub event_type: String,
    /// Human-readable label for display
    pub label: String,
    /// Total tokens for this event
    pub tokens: usize,
    /// Percentage of total tokens
    pub percentage: f64,
    /// Character count
    pub char_count: usize,
    /// Summary statistics by label (aggregated from children)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<BTreeMap<String, SummaryItem>>,
    /// Child breakdown nodes
    pub children: Vec<TokenBreakdownNode>,
}

/// A node in the token breakdown tree (JSON output)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenBreakdownNode {
    /// Machine-readable name
    pub name: String,
    /// Human-readable label for display
    pub label: String,
    /// Number of tokens in this node
    pub tokens: usize,
    /// Percentage of total tokens (relative to root total_tokens)
    pub percentage: f64,
    /// Character count of the content
    pub char_count: usize,
    /// Whether this is a history message (for request messages)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_history: Option<bool>,
    /// Full text content (for single-item nodes)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    /// Child nodes (for nested structures)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub children: Option<Vec<TokenBreakdownNode>>,
    /// Response items (for response sub-categories with multiple fragments)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub response_items: Option<Vec<ResponseItem>>,
}

/// A single response item within a response sub-category (no is_history field)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseItem {
    /// Sequential index within this sub-category (0-based)
    pub index: usize,
    /// Number of tokens
    pub tokens: usize,
    /// Character count
    pub char_count: usize,
    /// Full text content
    pub content: String,
}

/// Complete token breakdown result (JSON output root)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMLTokenBreakdown {
    /// Path to the analyzed file
    pub file_path: String,
    /// Model name used for tokenization
    pub model_name: String,
    /// Total tokens across all events
    pub total_tokens: usize,
    /// Summary statistics by input/output and label
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<BTreeMap<String, BTreeMap<String, SummaryItem>>>,
    /// Ordered array of trace events (request, response, ...)
    pub events: Vec<EventNode>,
}
