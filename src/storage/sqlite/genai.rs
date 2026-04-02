//! GenAI semantic events SQLite storage
//!
//! Stores GenAI events (LLM calls, tool uses, etc.) to SQLite when SLS is not configured.
//! Implements the GenAIExporter trait for pluggable integration.

use std::path::PathBuf;
use std::sync::Mutex;
use rusqlite::{params, Connection};

use crate::genai::semantic::GenAISemanticEvent;
use crate::genai::exporter::GenAIExporter;
use super::connection::{create_connection, default_base_path};

/// SQLite-backed GenAI event storage
pub struct GenAISqliteStore {
    conn: Mutex<Connection>,
}

impl GenAISqliteStore {
    /// Create a new GenAI SQLite store
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let path = Self::default_path();
        let conn = create_connection(&path)?;
        let store = GenAISqliteStore {
            conn: Mutex::new(conn),
        };
        store.init_tables()?;
        Ok(store)
    }

    /// Default database path
    pub fn default_path() -> PathBuf {
        default_base_path().join("genai_events.db")
    }

    /// Initialize database tables
    fn init_tables(&self) -> Result<(), Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS genai_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                call_id TEXT,
                session_id TEXT,
                conversation_id TEXT,
                timestamp_ns INTEGER NOT NULL,
                duration_ns INTEGER,
                pid INTEGER,
                process_name TEXT,
                agent_name TEXT,
                -- GenAI standard fields
                operation_name TEXT,
                provider TEXT,
                model TEXT,
                request_model TEXT,
                response_model TEXT,
                temperature REAL,
                max_tokens INTEGER,
                top_p REAL,
                frequency_penalty REAL,
                presence_penalty REAL,
                finish_reasons TEXT,
                server_address TEXT,
                -- Token usage
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                cache_creation_tokens INTEGER,
                cache_read_tokens INTEGER,
                -- Messages (JSON)
                system_instructions TEXT,
                input_messages TEXT,
                output_messages TEXT,
                -- AgentSight extensions
                user_query TEXT,
                http_method TEXT,
                http_path TEXT,
                status_code INTEGER,
                is_sse INTEGER,
                sse_event_count INTEGER,
                -- Full event as JSON (fallback)
                event_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_genai_session_id ON genai_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_genai_conversation_id ON genai_events(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_genai_timestamp ON genai_events(timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_genai_pid ON genai_events(pid);
            CREATE INDEX IF NOT EXISTS idx_genai_model ON genai_events(model);
            CREATE INDEX IF NOT EXISTS idx_genai_call_id ON genai_events(call_id);
            CREATE INDEX IF NOT EXISTS idx_genai_provider ON genai_events(provider);
            CREATE INDEX IF NOT EXISTS idx_genai_event_type ON genai_events(event_type);",
        )?;
        Ok(())
    }

    /// Store a single GenAI event
    fn store_event(&self, event: &GenAISemanticEvent) -> Result<(), Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let event_json = serde_json::to_string(event)?;

        match event {
            GenAISemanticEvent::LLMCall(call) => {
                let (input_tokens, output_tokens, total_tokens) = call.token_usage.as_ref()
                    .map(|u| (u.input_tokens as i64, u.output_tokens as i64, u.total_tokens as i64))
                    .unwrap_or((0, 0, 0));
                let cache_creation = call.token_usage.as_ref()
                    .and_then(|u| u.cache_creation_input_tokens.map(|v| v as i64));
                let cache_read = call.token_usage.as_ref()
                    .and_then(|u| u.cache_read_input_tokens.map(|v| v as i64));

                // Extract system instructions
                let system_instructions: Option<String> = {
                    let sys_msgs: Vec<_> = call.request.messages.iter()
                        .filter(|m| m.role == "system")
                        .collect();
                    if sys_msgs.is_empty() { None }
                    else { serde_json::to_string(&sys_msgs).ok() }
                };

                // Extract input messages (incremental: latest round only)
                let input_messages: Option<String> = {
                    let non_system: Vec<_> = call.request.messages.iter()
                        .filter(|m| m.role != "system")
                        .collect();
                    let latest = if let Some(idx) = non_system.iter().rposition(|m| m.role == "user") {
                        &non_system[idx..]
                    } else {
                        &non_system[..]
                    };
                    if latest.is_empty() { None }
                    else { serde_json::to_string(&latest).ok() }
                };

                // Extract output messages
                let output_messages: Option<String> = if call.response.messages.is_empty() {
                    None
                } else {
                    serde_json::to_string(&call.response.messages).ok()
                };

                // Extract finish reasons
                let finish_reasons: Option<String> = if call.response.messages.is_empty() {
                    None
                } else {
                    let reasons: Vec<_> = call.response.messages.iter()
                        .filter_map(|m| m.finish_reason.as_deref())
                        .collect();
                    if reasons.is_empty() { None }
                    else { serde_json::to_string(&reasons).ok() }
                };

                conn.execute(
                    "INSERT INTO genai_events (
                        event_type, call_id, session_id, conversation_id,
                        timestamp_ns, duration_ns, pid, process_name, agent_name,
                        operation_name, provider, model, request_model, response_model,
                        temperature, max_tokens, top_p, frequency_penalty, presence_penalty,
                        finish_reasons, server_address,
                        input_tokens, output_tokens, total_tokens,
                        cache_creation_tokens, cache_read_tokens,
                        system_instructions, input_messages, output_messages,
                        user_query, http_method, http_path, status_code,
                        is_sse, sse_event_count, event_json
                    ) VALUES (
                        ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10,
                        ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20,
                        ?21, ?22, ?23, ?24, ?25, ?26, ?27, ?28, ?29, ?30,
                        ?31, ?32, ?33, ?34, ?35, ?36
                    )",
                    params![
                        "llm_call",
                        call.call_id,
                        call.metadata.get("session_id"),
                        call.metadata.get("conversation_id"),
                        call.start_timestamp_ns as i64,
                        call.duration_ns as i64,
                        call.pid,
                        call.process_name,
                        call.agent_name,
                        call.metadata.get("operation_name"),
                        call.provider,
                        call.model,
                        call.model, // request_model
                        call.model, // response_model (same for now)
                        call.request.temperature,
                        call.request.max_tokens.map(|v| v as i64),
                        call.request.top_p,
                        call.request.frequency_penalty,
                        call.request.presence_penalty,
                        finish_reasons,
                        call.metadata.get("server.address"),
                        input_tokens,
                        output_tokens,
                        total_tokens,
                        cache_creation,
                        cache_read,
                        system_instructions,
                        input_messages,
                        output_messages,
                        call.metadata.get("user_query"),
                        call.metadata.get("method"),
                        call.metadata.get("path"),
                        call.metadata.get("status_code").and_then(|s| s.parse::<i64>().ok()),
                        call.metadata.get("is_sse").map(|s| if s == "true" { 1i64 } else { 0 }),
                        call.metadata.get("sse_event_count").and_then(|s| s.parse::<i64>().ok()),
                        event_json,
                    ],
                )?;
            }
            GenAISemanticEvent::ToolUse(tool) => {
                conn.execute(
                    "INSERT INTO genai_events (
                        event_type, call_id, timestamp_ns, pid,
                        event_json
                    ) VALUES (?1, ?2, ?3, ?4, ?5)",
                    params![
                        "tool_use",
                        tool.parent_llm_call_id,
                        tool.timestamp_ns as i64,
                        tool.pid,
                        event_json,
                    ],
                )?;
            }
            GenAISemanticEvent::AgentInteraction(interaction) => {
                conn.execute(
                    "INSERT INTO genai_events (
                        event_type, timestamp_ns, pid,
                        event_json
                    ) VALUES (?1, ?2, ?3, ?4)",
                    params![
                        "agent_interaction",
                        interaction.timestamp_ns as i64,
                        interaction.pid,
                        event_json,
                    ],
                )?;
            }
            GenAISemanticEvent::StreamChunk(chunk) => {
                conn.execute(
                    "INSERT INTO genai_events (
                        event_type, call_id, timestamp_ns, pid,
                        event_json
                    ) VALUES (?1, ?2, ?3, ?4, ?5)",
                    params![
                        "stream_chunk",
                        chunk.parent_llm_call_id,
                        chunk.timestamp_ns as i64,
                        chunk.pid,
                        event_json,
                    ],
                )?;
            }
        }
        Ok(())
    }
}

impl GenAIExporter for GenAISqliteStore {
    fn name(&self) -> &str {
        "sqlite"
    }

    fn export(&self, events: &[GenAISemanticEvent]) {
        for event in events {
            if let Err(e) = self.store_event(event) {
                log::warn!("Failed to store GenAI event to SQLite: {}", e);
            }
        }
    }
}
