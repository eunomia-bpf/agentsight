//! Audit record types for behavior auditing
//!
//! Defines `AuditRecord`, `AuditEventType`, and `AuditExtra` for representing
//! agent behavior events extracted from aggregated results.

use serde::{Deserialize, Serialize};

/// Audit event type tag
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuditEventType {
    LlmCall,
    ProcessAction,
}

impl std::fmt::Display for AuditEventType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuditEventType::LlmCall => write!(f, "llm_call"),
            AuditEventType::ProcessAction => write!(f, "process_action"),
        }
    }
}

impl std::str::FromStr for AuditEventType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "llm_call" | "llm" => Ok(AuditEventType::LlmCall),
            "process_action" | "process" => Ok(AuditEventType::ProcessAction),
            _ => Err(format!("unknown event type: {}", s)),
        }
    }
}

/// Extra fields specific to each event type, serialized as JSON into the `extra` column
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum AuditExtra {
    LlmCall {
        provider: Option<String>,
        model: Option<String>,
        request_method: Option<String>,
        request_path: Option<String>,
        response_status: Option<u16>,
        input_tokens: u64,
        output_tokens: u64,
        cache_creation_tokens: u64,
        cache_read_tokens: u64,
        is_sse: bool,
    },
    ProcessAction {
        filename: Option<String>,
        args: Option<String>,
        exit_code: Option<i32>,
    },
}

/// Unified audit record
#[derive(Debug, Clone)]
pub struct AuditRecord {
    /// Database row ID (None for new records not yet inserted)
    pub id: Option<i64>,
    /// Event type discriminator
    pub event_type: AuditEventType,
    /// Timestamp in nanoseconds
    pub timestamp_ns: u64,
    /// Process ID
    pub pid: u32,
    /// Parent process ID
    pub ppid: Option<u32>,
    /// Process command name
    pub comm: String,
    /// Duration in nanoseconds
    pub duration_ns: u64,
    /// Type-specific extra fields (serialized as JSON)
    pub extra: AuditExtra,
}

/// Summary statistics for audit events
#[derive(Debug, Clone, Serialize)]
pub struct AuditSummary {
    pub total_llm_calls: u64,
    pub total_process_actions: u64,
    pub total_input_tokens: u64,
    pub total_output_tokens: u64,
    pub providers: Vec<(String, u64)>,
    pub top_commands: Vec<(String, u64)>,
}
