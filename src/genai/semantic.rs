//! GenAI Semantic Data Structures
//!
//! This module defines GenAI-specific semantic structures that represent
//! LLM interactions at a higher abstraction level than raw HTTP requests/responses.

use serde::{Serialize, Deserialize};
use std::collections::HashMap;

/// GenAI semantic event types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GenAISemanticEvent {
    /// LLM API call with request/response
    LLMCall(LLMCall),
    /// Tool/function invocation
    ToolUse(ToolUse),
    /// Agent interaction/decision
    AgentInteraction(AgentInteraction),
    /// Streaming response chunk
    StreamChunk(StreamChunk),
}

/// LLM API call representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMCall {
    /// Unique identifier for this call
    pub call_id: String,
    /// Timestamp when the call started (nanoseconds)
    pub start_timestamp_ns: u64,
    /// Timestamp when the call completed (nanoseconds)
    pub end_timestamp_ns: u64,
    /// Duration in nanoseconds
    pub duration_ns: u64,
    /// LLM provider (openai, anthropic, etc.)
    pub provider: String,
    /// Model name
    pub model: String,
    /// Request details
    pub request: LLMRequest,
    /// Response details
    pub response: LLMResponse,
    /// Token usage information
    pub token_usage: Option<TokenUsage>,
    /// Error information if any
    pub error: Option<String>,
    /// Process ID that made the call
    pub pid: i32,
    /// Process name
    pub process_name: String,
    /// Resolved agent name from discovery registry (e.g. "OpenClaw", "Cosh")
    pub agent_name: Option<String>,
    /// Additional metadata
    pub metadata: HashMap<String, String>,
}

/// LLM request details
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMRequest {
    /// Request messages in OTel parts-based format
    pub messages: Vec<InputMessage>,
    /// Temperature setting
    pub temperature: Option<f64>,
    /// Max tokens
    pub max_tokens: Option<u32>,
    /// Frequency penalty
    pub frequency_penalty: Option<f64>,
    /// Presence penalty
    pub presence_penalty: Option<f64>,
    /// Top-p sampling
    pub top_p: Option<f64>,
    /// Top-k sampling
    pub top_k: Option<f64>,
    /// Seed for reproducibility
    pub seed: Option<i64>,
    /// Stop sequences
    pub stop_sequences: Option<Vec<String>>,
    /// Stream mode enabled
    pub stream: bool,
    /// Tools/functions available
    pub tools: Option<Vec<ToolDefinition>>,
    /// Raw request body (optional, for debugging)
    pub raw_body: Option<String>,
}

/// LLM response details
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMResponse {
    /// Response messages in OTel parts-based format
    pub messages: Vec<OutputMessage>,
    /// Whether response was streamed
    pub streamed: bool,
    /// Raw response body (optional, for debugging)
    pub raw_body: Option<String>,
}

/// Message part types (OTel GenAI parts-based format)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum MessagePart {
    /// Text content
    #[serde(rename = "text")]
    Text { content: String },
    /// Reasoning/thinking content
    #[serde(rename = "reasoning")]
    Reasoning { content: String },
    /// Tool call request from model
    #[serde(rename = "tool_call")]
    ToolCall {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        id: Option<String>,
        name: String,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        arguments: Option<serde_json::Value>,
    },
    /// Tool call response
    #[serde(rename = "tool_call_response")]
    ToolCallResponse {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        id: Option<String>,
        response: serde_json::Value,
    },
}

/// Input message (OTel ChatMessage)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputMessage {
    /// Role (system, user, assistant, tool)
    pub role: String,
    /// Message parts
    pub parts: Vec<MessagePart>,
    /// Participant name
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
}

/// Output message (OTel OutputMessage)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputMessage {
    /// Role (usually assistant)
    pub role: String,
    /// Message parts
    pub parts: Vec<MessagePart>,
    /// Participant name
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    /// Finish reason (stop, length, tool_call, etc.)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub finish_reason: Option<String>,
}

/// Tool definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    /// Tool name
    pub name: String,
    /// Tool description
    pub description: String,
    /// Parameters schema (JSON)
    pub parameters: serde_json::Value,
}

/// Token usage information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    /// Input/prompt tokens
    pub input_tokens: u32,
    /// Output/completion tokens
    pub output_tokens: u32,
    /// Total tokens
    pub total_tokens: u32,
    /// Cache creation tokens
    pub cache_creation_input_tokens: Option<u32>,
    /// Cache read tokens
    pub cache_read_input_tokens: Option<u32>,
}

/// Tool/function use event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolUse {
    /// Unique identifier
    pub tool_use_id: String,
    /// Timestamp (nanoseconds)
    pub timestamp_ns: u64,
    /// Tool name
    pub tool_name: String,
    /// Tool arguments
    pub arguments: serde_json::Value,
    /// Tool result/output
    pub result: Option<String>,
    /// Duration in nanoseconds (if completed)
    pub duration_ns: Option<u64>,
    /// Success/failure status
    pub success: bool,
    /// Error message if failed
    pub error: Option<String>,
    /// Associated LLM call ID
    pub parent_llm_call_id: Option<String>,
    /// Process ID
    pub pid: i32,
}

/// Agent interaction/decision event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInteraction {
    /// Unique identifier
    pub interaction_id: String,
    /// Timestamp (nanoseconds)
    pub timestamp_ns: u64,
    /// Agent name/type
    pub agent_name: String,
    /// Interaction type (think, plan, decide, etc.)
    pub interaction_type: String,
    /// Content/description of the interaction
    pub content: String,
    /// Associated LLM call ID
    pub parent_llm_call_id: Option<String>,
    /// Process ID
    pub pid: i32,
}

/// Streaming response chunk
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamChunk {
    /// Unique identifier for the stream
    pub stream_id: String,
    /// Chunk sequence number
    pub chunk_index: u32,
    /// Timestamp (nanoseconds)
    pub timestamp_ns: u64,
    /// Chunk content
    pub content: String,
    /// Associated LLM call ID
    pub parent_llm_call_id: String,
    /// Process ID
    pub pid: i32,
}

impl LLMCall {
    /// Create a new LLMCall instance
    pub fn new(
        call_id: String,
        start_timestamp_ns: u64,
        provider: String,
        model: String,
        request: LLMRequest,
        pid: i32,
        process_name: String,
    ) -> Self {
        LLMCall {
            call_id,
            start_timestamp_ns,
            end_timestamp_ns: 0, // Will be set when response arrives
            duration_ns: 0,
            provider,
            model,
            request,
            response: LLMResponse {
                messages: vec![],
                streamed: false,
                raw_body: None,
            },
            token_usage: None,
            error: None,
            pid,
            process_name,
            agent_name: None,
            metadata: HashMap::new(),
        }
    }

    /// Set response and calculate duration
    pub fn set_response(&mut self, response: LLMResponse, end_timestamp_ns: u64) {
        self.end_timestamp_ns = end_timestamp_ns;
        self.duration_ns = end_timestamp_ns.saturating_sub(self.start_timestamp_ns);
        self.response = response;
    }

    /// Set token usage
    pub fn set_token_usage(&mut self, usage: TokenUsage) {
        self.token_usage = Some(usage);
    }

    /// Set error
    pub fn set_error(&mut self, error: String) {
        self.error = Some(error);
    }
}
