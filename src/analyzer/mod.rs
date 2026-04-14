//! Analyzer module - pure logic analysis layer
//!
//! Extracts structured records from aggregated results.
//! Contains `AuditAnalyzer` for behavior auditing, `TokenParser` for token usage extraction,
//! and `MessageParser` for LLM API message format parsing.
//!
//! Use `Analyzer` for a unified interface that combines all analyzers.

pub mod audit;
pub mod message;
pub mod token;
mod result;
mod unified;

// Re-export audit types
pub use audit::{AuditAnalyzer, AuditEventType, AuditExtra, AuditRecord, AuditSummary};

// Re-export token types from the token module
pub use token::{TokenParser, TokenUsage, TokenRecord, LLMProvider};

// Re-export message types from the message module
pub use message::{
    MessageParser, ParsedApiMessage,
    OpenAIRequest, OpenAIResponse, OpenAIChatMessage, OpenAIContent, OpenAIUsage, OpenAIChoice,
    AnthropicRequest, AnthropicResponse, AnthropicMessage, AnthropicUsage,
    MessageRole,
};

// Re-export analysis result
pub use result::{AnalysisResult, PromptTokenCount, HttpRecord, TokenConsumptionBreakdown, MessageTokenCount, OutputTokenCount};

// Re-export unified analyzer
pub use unified::{Analyzer, count_request_tokens, count_response_tokens, RequestTokenCount, ResponseTokenCount};
