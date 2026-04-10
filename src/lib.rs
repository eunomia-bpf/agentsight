//! AgentSight - AI Agent observability library
//!
//! This crate provides eBPF-based observability for AI agents, including:
//! - SSL/TLS traffic capture and parsing
//! - HTTP request/response aggregation
//! - LLM token usage tracking
//! - Process lifecycle monitoring
//!
//! # Architecture
//!
//! ```text
//! probes → parser → aggregator → analyzer → storage
//!   ↓         ↓          ↓           ↓         ↓
//! Event  ParsedMessage  AggregatedResult  AnalysisResult  持久化
//! ```
//!
//! # Usage
//!
//! ```rust,ignore
//! use agentsight::{AgentSight, AgentsightConfig};
//!
//! let config = AgentsightConfig::new();
//! let mut sight = AgentSight::new(config)?;  // auto-attaches and starts polling
//! sight.run()?;  // blocking event loop
//! ```

pub mod probes;
pub mod config;

// Re-export config types
pub use config::{AgentsightConfig, default_base_path};
pub mod event;
pub mod parser;
pub mod aggregator;
pub mod analyzer;
pub mod storage;
pub mod chrome_trace;
pub mod discovery;
pub mod health;
pub mod tokenizer;
pub mod genai;
pub mod atif;
#[cfg(feature = "server")]
pub mod server;
pub mod token_breakdown;
mod unified;
pub mod ffi;

// Re-export common types for convenience
pub use aggregator::{
    Aggregator, AggregatedResult,
    HttpConnectionAggregator, ConnectionId, ConnectionState,
    HttpPair,
    ProcessEventAggregator, AggregatedProcess,
    AggregatedResponse,
};
pub use parser::{
    HttpParser, ParsedHttpMessage, ParsedRequest, ParsedResponse,
    SseParser, ParsedSseEvent,
    ProcTraceParser, ParsedProcEvent, ProcEventType,
    Http2Parser, Http2FrameType, ParsedHttp2Frame,
    Parser, ParsedMessage, ParseResult,
};
pub use analyzer::{
    AuditAnalyzer, AuditEventType, AuditExtra, AuditRecord, AuditSummary,
    TokenParser, TokenUsage, TokenRecord, LLMProvider,
    MessageParser, ParsedApiMessage,
    OpenAIRequest, OpenAIResponse, OpenAIChatMessage, OpenAIContent, OpenAIUsage,
    AnthropicRequest, AnthropicResponse, AnthropicMessage, AnthropicUsage,
    MessageRole,
    AnalysisResult, PromptTokenCount, HttpRecord, Analyzer,
    TokenConsumptionBreakdown, MessageTokenCount, OutputTokenCount,
    count_request_tokens, count_response_tokens, RequestTokenCount, ResponseTokenCount,
};
pub use chrome_trace::{ChromeTraceEvent, TraceArgs, ToChromeTraceEvent, ns_to_us, next_flow_id};
pub use storage::{
    Storage, StorageBackend, SqliteConfig,
    SqliteStore, AuditStore,
    TokenStore, TokenQuery,
    HttpStore,
    TokenConsumptionStore, TokenConsumptionRecord,
    TokenConsumptionFilter, TokenConsumptionQueryResult,
    TimePeriod, TokenQueryResult, TokenBreakdown, TokenComparison, Trend,
    format_tokens, format_tokens_with_commas,
};

// Re-export unified entry point
pub use unified::{AgentSight, ProcessResult};

// Re-export discovery types
pub use discovery::{AgentInfo, AgentMatcher, AgentScanner, DiscoveredAgent, ProcessContext, known_agents};


// Re-export genai types
pub use genai::{
    GenAIBuilder, GenAISemanticEvent, LLMCall, LLMRequest, LLMResponse,
    MessagePart, InputMessage, OutputMessage, ToolUse, AgentInteraction, StreamChunk, ToolDefinition,
    GenAIStore, GenAIStoreStats, SlsUploader, GenAIExporter,
};

