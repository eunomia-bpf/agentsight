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

// ─── Query result types ────────────────────────────────────────────────────────

/// One data-point in a token time-series response
#[derive(Debug, serde::Serialize)]
pub struct TimeseriesBucket {
    pub bucket_start_ns: i64,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
}

/// One data-point in a per-model token time-series response
#[derive(Debug, serde::Serialize)]
pub struct ModelTimeseriesBucket {
    pub bucket_start_ns: i64,
    pub model: String,
    pub total_tokens: i64,
}

/// Per-agent token usage summary (all-time aggregation)
#[derive(Debug, serde::Serialize)]
pub struct AgentTokenSummary {
    pub agent_name: String,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub request_count: i64,
}

/// Summary of a single gen_ai.session_id within a time window
#[derive(Debug, serde::Serialize)]
pub struct SessionSummary {
    pub session_id: String,
    pub trace_count: i64,
    pub first_seen_ns: i64,
    pub last_seen_ns: i64,
    pub total_input_tokens: i64,
    pub total_output_tokens: i64,
    pub model: Option<String>,
    pub agent_name: Option<String>,
}

/// Summary of a single trace_id within a session
#[derive(Debug, serde::Serialize)]
pub struct TraceSummary {
    pub trace_id: String,
    pub call_count: i64,
    pub total_input_tokens: i64,
    pub total_output_tokens: i64,
    pub start_ns: i64,
    pub end_ns: Option<i64>,
    pub model: Option<String>,
    /// The first user_query string recorded in this trace (best-effort)
    pub user_query: Option<String>,
}

/// One LLM call event within a trace
#[derive(Debug, serde::Serialize)]
pub struct TraceEventDetail {
    pub id: i64,
    pub call_id: Option<String>,
    pub start_timestamp_ns: i64,
    pub end_timestamp_ns: Option<i64>,
    pub model: Option<String>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    /// JSON string of input messages array
    pub input_messages: Option<String>,
    /// JSON string of output messages array
    pub output_messages: Option<String>,
    /// JSON string of system instructions
    pub system_instructions: Option<String>,
    pub agent_name: Option<String>,
    pub process_name: Option<String>,
    pub pid: Option<i64>,
    /// The user query that triggered this LLM call
    pub user_query: Option<String>,
    /// Raw full event JSON stored at write time — used as fallback when
    /// output_messages is NULL (e.g. SSE streams that weren't fully parsed)
    pub event_json: Option<String>,
    /// Trace ID (conversation_id) — needed for session-level ATIF export
    /// to group events by trace.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    /// Cache read tokens — maps to ATIF cached_tokens
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cache_read_tokens: Option<i64>,
}

/// SQLite-backed GenAI event storage
pub struct GenAISqliteStore {
    conn: Mutex<Connection>,
}

impl GenAISqliteStore {
    /// Create a new GenAI SQLite store at the default path
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let path = Self::default_path();
        Self::new_with_path(&path)
    }

    /// Create a new GenAI SQLite store at an arbitrary path
    pub fn new_with_path(path: &std::path::Path) -> Result<Self, Box<dyn std::error::Error>> {
        let conn = create_connection(path)?;
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
                trace_id TEXT,
                session_id TEXT,
                instance TEXT,
                start_timestamp_ns INTEGER NOT NULL,
                end_timestamp_ns INTEGER,
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
            CREATE INDEX IF NOT EXISTS idx_genai_trace_id ON genai_events(trace_id);
            CREATE INDEX IF NOT EXISTS idx_genai_instance ON genai_events(instance);
            CREATE INDEX IF NOT EXISTS idx_genai_start_timestamp ON genai_events(start_timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_genai_pid ON genai_events(pid);
            CREATE INDEX IF NOT EXISTS idx_genai_model ON genai_events(model);
            CREATE INDEX IF NOT EXISTS idx_genai_call_id ON genai_events(call_id);
            CREATE INDEX IF NOT EXISTS idx_genai_provider ON genai_events(provider);
            -- Composite indexes for common query patterns
            CREATE INDEX IF NOT EXISTS idx_genai_session_timestamp ON genai_events(session_id, start_timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_genai_trace_timestamp ON genai_events(trace_id, start_timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_genai_pid_timestamp ON genai_events(pid, start_timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_genai_instance_timestamp ON genai_events(instance, start_timestamp_ns);",
        )?;
        Ok(())
    }

    // ─── Query methods ───────────────────────────────────────────────────────

    /// List all sessions within a nanosecond timestamp range.
    pub fn list_sessions(
        &self,
        start_ns: i64,
        end_ns: i64,
    ) -> Result<Vec<SessionSummary>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT session_id,
                    COUNT(DISTINCT trace_id) AS trace_count,
                    MIN(start_timestamp_ns)  AS first_seen_ns,
                    MAX(start_timestamp_ns)  AS last_seen_ns,
                    COALESCE(SUM(input_tokens), 0)  AS total_input,
                    COALESCE(SUM(output_tokens), 0) AS total_output,
                    MAX(model)               AS model,
                    MAX(agent_name)          AS agent_name
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND session_id IS NOT NULL
               AND start_timestamp_ns BETWEEN ?1 AND ?2
             GROUP BY session_id
             ORDER BY last_seen_ns DESC",
        )?;
        let rows = stmt.query_map(params![start_ns, end_ns], |row| {
            Ok(SessionSummary {
                session_id: row.get(0)?,
                trace_count: row.get(1)?,
                first_seen_ns: row.get(2)?,
                last_seen_ns: row.get(3)?,
                total_input_tokens: row.get(4)?,
                total_output_tokens: row.get(5)?,
                model: row.get(6)?,
                agent_name: row.get(7)?,
            })
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
    }

    /// List all trace IDs under a given session, with aggregated token stats.
    pub fn list_traces_by_session(
        &self,
        session_id: &str,
    ) -> Result<Vec<TraceSummary>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT trace_id,
                    COUNT(*)                        AS call_count,
                    COALESCE(SUM(input_tokens), 0)  AS total_input,
                    COALESCE(SUM(output_tokens), 0) AS total_output,
                    MIN(start_timestamp_ns)         AS start_ns,
                    MAX(end_timestamp_ns)           AS end_ns,
                    MAX(model)                      AS model,
                    MIN(user_query)                 AS user_query
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND session_id = ?1
               AND trace_id IS NOT NULL
             GROUP BY trace_id
             ORDER BY start_ns ASC",
        )?;
        let rows = stmt.query_map(params![session_id], |row| {
            Ok(TraceSummary {
                trace_id: row.get(0)?,
                call_count: row.get(1)?,
                total_input_tokens: row.get(2)?,
                total_output_tokens: row.get(3)?,
                start_ns: row.get(4)?,
                end_ns: row.get(5)?,
                model: row.get(6)?,
                user_query: row.get(7)?,
            })
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
    }

    /// List all distinct agent_name values observed in the given time window.
    pub fn list_agent_names(
        &self,
        start_ns: i64,
        end_ns: i64,
    ) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT DISTINCT agent_name
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND agent_name IS NOT NULL
               AND start_timestamp_ns BETWEEN ?1 AND ?2
             ORDER BY agent_name ASC",
        )?;
        let rows = stmt.query_map(params![start_ns, end_ns], |row| {
            row.get::<_, String>(0)
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
    }

    /// One bucket in a token time-series query.
    pub fn get_token_timeseries(
        &self,
        start_ns: i64,
        end_ns: i64,
        agent_name: Option<&str>,
        bucket_count: u32,
    ) -> Result<Vec<TimeseriesBucket>, Box<dyn std::error::Error>> {
        let bucket_count = bucket_count.max(1);
        let range_ns = (end_ns - start_ns).max(1);
        let bucket_ns = range_ns / bucket_count as i64;

        let conn = self.conn.lock().unwrap();

        // Build query with optional agent_name filter
        let sql = if agent_name.is_some() {
            "SELECT
                (start_timestamp_ns - ?1) / ?3            AS bucket_idx,
                ?1 + ((start_timestamp_ns - ?1) / ?3) * ?3 AS bucket_start_ns,
                COALESCE(SUM(input_tokens), 0)            AS input_tokens,
                COALESCE(SUM(output_tokens), 0)           AS output_tokens,
                COALESCE(SUM(total_tokens), 0)            AS total_tokens
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND start_timestamp_ns BETWEEN ?1 AND ?2
               AND agent_name = ?4
             GROUP BY bucket_idx
             ORDER BY bucket_idx ASC"
        } else {
            "SELECT
                (start_timestamp_ns - ?1) / ?3            AS bucket_idx,
                ?1 + ((start_timestamp_ns - ?1) / ?3) * ?3 AS bucket_start_ns,
                COALESCE(SUM(input_tokens), 0)            AS input_tokens,
                COALESCE(SUM(output_tokens), 0)           AS output_tokens,
                COALESCE(SUM(total_tokens), 0)            AS total_tokens
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND start_timestamp_ns BETWEEN ?1 AND ?2
             GROUP BY bucket_idx
             ORDER BY bucket_idx ASC"
        };

        let rows: Vec<TimeseriesBucket> = if let Some(name) = agent_name {
            let mut stmt = conn.prepare(sql)?;
            stmt.query_map(params![start_ns, end_ns, bucket_ns, name], |row| {
                Ok(TimeseriesBucket {
                    bucket_start_ns: row.get(1)?,
                    input_tokens: row.get(2)?,
                    output_tokens: row.get(3)?,
                    total_tokens: row.get(4)?,
                })
            })?.collect::<Result<Vec<_>, _>>()?
        } else {
            let mut stmt = conn.prepare(sql)?;
            stmt.query_map(params![start_ns, end_ns, bucket_ns], |row| {
                Ok(TimeseriesBucket {
                    bucket_start_ns: row.get(1)?,
                    input_tokens: row.get(2)?,
                    output_tokens: row.get(3)?,
                    total_tokens: row.get(4)?,
                })
            })?.collect::<Result<Vec<_>, _>>()?
        };

        Ok(rows)
    }

    /// Model-level token breakdown time-series.
    pub fn get_model_timeseries(
        &self,
        start_ns: i64,
        end_ns: i64,
        agent_name: Option<&str>,
        bucket_count: u32,
    ) -> Result<Vec<ModelTimeseriesBucket>, Box<dyn std::error::Error>> {
        let bucket_count = bucket_count.max(1);
        let range_ns = (end_ns - start_ns).max(1);
        let bucket_ns = range_ns / bucket_count as i64;

        let conn = self.conn.lock().unwrap();

        let sql = if agent_name.is_some() {
            "SELECT
                (start_timestamp_ns - ?1) / ?3            AS bucket_idx,
                ?1 + ((start_timestamp_ns - ?1) / ?3) * ?3 AS bucket_start_ns,
                COALESCE(model, 'unknown')                 AS model,
                COALESCE(SUM(total_tokens), 0)            AS total_tokens
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND start_timestamp_ns BETWEEN ?1 AND ?2
               AND agent_name = ?4
             GROUP BY bucket_idx, model
             ORDER BY bucket_idx ASC"
        } else {
            "SELECT
                (start_timestamp_ns - ?1) / ?3            AS bucket_idx,
                ?1 + ((start_timestamp_ns - ?1) / ?3) * ?3 AS bucket_start_ns,
                COALESCE(model, 'unknown')                 AS model,
                COALESCE(SUM(total_tokens), 0)            AS total_tokens
             FROM genai_events
             WHERE event_type = 'llm_call'
               AND start_timestamp_ns BETWEEN ?1 AND ?2
             GROUP BY bucket_idx, model
             ORDER BY bucket_idx ASC"
        };

        let rows: Vec<ModelTimeseriesBucket> = if let Some(name) = agent_name {
            let mut stmt = conn.prepare(sql)?;
            stmt.query_map(params![start_ns, end_ns, bucket_ns, name], |row| {
                Ok(ModelTimeseriesBucket {
                    bucket_start_ns: row.get(1)?,
                    model: row.get(2)?,
                    total_tokens: row.get(3)?,
                })
            })?.collect::<Result<Vec<_>, _>>()?
        } else {
            let mut stmt = conn.prepare(sql)?;
            stmt.query_map(params![start_ns, end_ns, bucket_ns], |row| {
                Ok(ModelTimeseriesBucket {
                    bucket_start_ns: row.get(1)?,
                    model: row.get(2)?,
                    total_tokens: row.get(3)?,
                })
            })?.collect::<Result<Vec<_>, _>>()?
        };

        Ok(rows)
    }

    /// Return per-agent token usage aggregated over all recorded history.
    ///
    /// Groups by `COALESCE(agent_name, process_name, 'unknown')` so that every
    /// LLM call is attributed to some label even when agent_name is NULL.
    pub fn get_agent_token_summary(
        &self,
    ) -> Result<Vec<AgentTokenSummary>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT COALESCE(agent_name, process_name, 'unknown') AS agent,
                    COALESCE(SUM(input_tokens),  0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COALESCE(SUM(total_tokens),  0) AS total_tokens,
                    COUNT(*)                        AS request_count
             FROM genai_events
             WHERE event_type = 'llm_call'
             GROUP BY agent
             ORDER BY total_tokens DESC",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(AgentTokenSummary {
                agent_name:    row.get(0)?,
                input_tokens:  row.get(1)?,
                output_tokens: row.get(2)?,
                total_tokens:  row.get(3)?,
                request_count: row.get(4)?,
            })
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
    }

    /// Fetch all LLM call events for a given trace ID.
    pub fn get_trace_events(
        &self,
        trace_id: &str,
    ) -> Result<Vec<TraceEventDetail>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, call_id, start_timestamp_ns, end_timestamp_ns,
                    model,
                    COALESCE(input_tokens, 0)  AS input_tokens,
                    COALESCE(output_tokens, 0) AS output_tokens,
                    COALESCE(total_tokens, 0)  AS total_tokens,
                    input_messages, output_messages, system_instructions,
                    agent_name, process_name, pid, user_query, event_json,
                    trace_id, cache_read_tokens
             FROM genai_events
             WHERE trace_id = ?1
               AND event_type = 'llm_call'
             ORDER BY start_timestamp_ns ASC",
        )?;
        let rows = stmt.query_map(params![trace_id], |row| {
            Ok(TraceEventDetail {
                id: row.get(0)?,
                call_id: row.get(1)?,
                start_timestamp_ns: row.get(2)?,
                end_timestamp_ns: row.get(3)?,
                model: row.get(4)?,
                input_tokens: row.get(5)?,
                output_tokens: row.get(6)?,
                total_tokens: row.get(7)?,
                input_messages: row.get(8)?,
                output_messages: row.get(9)?,
                system_instructions: row.get(10)?,
                agent_name: row.get(11)?,
                process_name: row.get(12)?,
                pid: row.get(13)?,
                user_query: row.get(14)?,
                event_json: row.get(15)?,
                trace_id: row.get(16)?,
                cache_read_tokens: row.get(17)?,
            })
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
    }

    /// Fetch all LLM call events for a given session ID (across all traces).
    pub fn get_events_by_session(
        &self,
        session_id: &str,
    ) -> Result<Vec<TraceEventDetail>, Box<dyn std::error::Error>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, call_id, start_timestamp_ns, end_timestamp_ns,
                    model,
                    COALESCE(input_tokens, 0)  AS input_tokens,
                    COALESCE(output_tokens, 0) AS output_tokens,
                    COALESCE(total_tokens, 0)  AS total_tokens,
                    input_messages, output_messages, system_instructions,
                    agent_name, process_name, pid, user_query, event_json,
                    trace_id, cache_read_tokens
             FROM genai_events
             WHERE session_id = ?1
               AND event_type = 'llm_call'
             ORDER BY start_timestamp_ns ASC",
        )?;
        let rows = stmt.query_map(params![session_id], |row| {
            Ok(TraceEventDetail {
                id: row.get(0)?,
                call_id: row.get(1)?,
                start_timestamp_ns: row.get(2)?,
                end_timestamp_ns: row.get(3)?,
                model: row.get(4)?,
                input_tokens: row.get(5)?,
                output_tokens: row.get(6)?,
                total_tokens: row.get(7)?,
                input_messages: row.get(8)?,
                output_messages: row.get(9)?,
                system_instructions: row.get(10)?,
                agent_name: row.get(11)?,
                process_name: row.get(12)?,
                pid: row.get(13)?,
                user_query: row.get(14)?,
                event_json: row.get(15)?,
                trace_id: row.get(16)?,
                cache_read_tokens: row.get(17)?,
            })
        })?;
        let mut result = Vec::new();
        for row in rows {
            result.push(row?);
        }
        Ok(result)
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

                // Get instance ID (same logic as SLS uploader)
                let instance = crate::genai::sls::SlsUploader::get_instance_id();

                conn.execute(
                    "INSERT INTO genai_events (
                        event_type, call_id, trace_id, session_id, instance,
                        start_timestamp_ns, end_timestamp_ns, duration_ns, pid, process_name, agent_name,
                        operation_name, provider, model, request_model, response_model,
                        temperature, max_tokens, top_p, frequency_penalty, presence_penalty,
                        finish_reasons, server_address,
                        input_tokens, output_tokens, total_tokens,
                        cache_creation_tokens, cache_read_tokens,
                        system_instructions, input_messages, output_messages,
                        user_query, http_method, http_path, status_code,
                        is_sse, sse_event_count, event_json
                    ) VALUES (
                        ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11,
                        ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20, ?21,
                        ?22, ?23, ?24, ?25, ?26, ?27, ?28, ?29, ?30, ?31,
                        ?32, ?33, ?34, ?35, ?36, ?37, ?38
                    )",
                    params![
                        "llm_call",
                        call.call_id,
                        call.metadata.get("conversation_id"),
                        call.metadata.get("session_id"),
                        instance,
                        call.start_timestamp_ns as i64,
                        call.end_timestamp_ns as i64,
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
