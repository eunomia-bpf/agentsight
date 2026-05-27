// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::core::Event;
use crate::framework::semantic::{
    CanonicalEvent, EventKind, body_json, extract_model, extract_token_usage,
    extract_token_usage_from_sse, normalize_event, provider_from_host,
};
use chrono::{SecondsFormat, Utc};
use rusqlite::{Connection, params};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{HashMap, VecDeque};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

pub type StorageResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

#[derive(Debug, Clone)]
struct PendingRequest {
    canonical_event_id: String,
    timestamp_ms: u64,
    pid: u32,
    comm: String,
    provider: Option<String>,
    model: Option<String>,
    host: Option<String>,
    path: Option<String>,
    body_json: Option<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenSummary {
    pub group: String,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_tokens: i64,
    pub calls: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditRow {
    pub timestamp_ms: u64,
    pub audit_type: String,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub subject: Option<String>,
    pub action: Option<String>,
    pub target: Option<String>,
    pub status: Option<String>,
    pub summary: Option<String>,
}

#[derive(Debug, Clone, Copy)]
pub struct SnapshotOptions {
    pub event_limit: usize,
    pub audit_limit: usize,
}

impl Default for SnapshotOptions {
    fn default() -> Self {
        Self {
            event_limit: 10_000,
            audit_limit: 10_000,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub schema_version: u16,
    pub generated_at: String,
    pub summary: SnapshotSummary,
    pub token_summary: Vec<TokenSummary>,
    pub events: Vec<EventRow>,
    pub audit_events: Vec<AuditEventRow>,
    pub sessions: Vec<SessionRow>,
    pub agents: Vec<AgentRow>,
    pub interruptions: Vec<InterruptionRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotSummary {
    pub source: String,
    pub raw_events: i64,
    pub canonical_events: i64,
    pub llm_calls: i64,
    pub token_usage_rows: i64,
    pub audit_events: i64,
    pub sessions: i64,
    pub interruptions: i64,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub event_limit: usize,
    pub audit_limit: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventRow {
    pub id: String,
    pub timestamp_ms: u64,
    pub source: String,
    pub kind: String,
    pub severity: String,
    pub summary: Option<String>,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub host: Option<String>,
    pub method: Option<String>,
    pub path: Option<String>,
    pub status_code: Option<u16>,
    pub provider: Option<String>,
    pub model: Option<String>,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub adapter_id: Option<String>,
    pub confidence: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEventRow {
    pub id: String,
    pub timestamp_ms: u64,
    pub audit_type: String,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub subject: Option<String>,
    pub action: Option<String>,
    pub target: Option<String>,
    pub status: Option<String>,
    pub summary: Option<String>,
    pub details: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionRow {
    pub id: String,
    pub agent_type: String,
    pub agent_name: Option<String>,
    pub pid: Option<u32>,
    pub comm: Option<String>,
    pub start_timestamp_ms: u64,
    pub end_timestamp_ms: Option<u64>,
    pub status: String,
    pub model: Option<String>,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub adapter_id: String,
    pub confidence: Option<f64>,
    pub attributes: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRow {
    pub agent_type: String,
    pub agent_name: Option<String>,
    pub sessions: i64,
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub total_tokens: i64,
    pub last_seen_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InterruptionRow {
    pub id: String,
    pub timestamp_ms: u64,
    pub session_id: Option<String>,
    pub conversation_id: Option<String>,
    pub severity: String,
    pub category: String,
    pub status: String,
    pub reason: String,
    pub evidence: Value,
    pub adapter_id: Option<String>,
    pub confidence: Option<f64>,
}

pub struct SqliteStore {
    conn: Connection,
    next_seq: u64,
}

impl SqliteStore {
    pub fn open(path: impl AsRef<Path>) -> StorageResult<Self> {
        let conn = Connection::open(path)?;
        let mut store = Self { conn, next_seq: 0 };
        store.init()?;
        Ok(store)
    }

    #[cfg(test)]
    pub fn open_in_memory() -> StorageResult<Self> {
        let conn = Connection::open_in_memory()?;
        let mut store = Self { conn, next_seq: 0 };
        store.init()?;
        Ok(store)
    }

    #[cfg(test)]
    pub fn connection(&self) -> &Connection {
        &self.conn
    }

    pub fn connection_mut(&mut self) -> &mut Connection {
        &mut self.conn
    }

    fn init(&mut self) -> StorageResult<()> {
        self.conn.pragma_update(None, "journal_mode", "WAL").ok();
        self.conn.pragma_update(None, "foreign_keys", "ON")?;
        self.conn.execute_batch(SCHEMA)?;
        Ok(())
    }

    pub fn insert_event(
        &mut self,
        event: &Event,
        projector: &mut GenericProjector,
    ) -> StorageResult<CanonicalEvent> {
        self.next_seq += 1;
        let raw_id = format!(
            "raw-{}-{}-{}-{}",
            event.timestamp,
            sanitize_id(&event.source),
            event.pid,
            self.next_seq
        );
        let ingest_ms = now_ms();
        let canonical = normalize_event(event, raw_id.clone(), ingest_ms);
        let raw_json = serde_json::to_string(event)?;
        let attrs_json = serde_json::to_string(&canonical.attributes)?;

        self.conn.execute(
            "INSERT OR REPLACE INTO raw_events (id, timestamp_ms, source, pid, comm, raw_json)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                raw_id,
                event.timestamp as i64,
                event.source,
                event.pid as i64,
                event.comm,
                raw_json
            ],
        )?;

        self.insert_canonical(&canonical, &attrs_json)?;
        projector.process(self, &canonical)?;
        Ok(canonical)
    }

    fn insert_canonical(&self, event: &CanonicalEvent, attrs_json: &str) -> StorageResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO canonical_events (
                id, raw_event_id, schema_version, timestamp_ms, ingest_timestamp_ms,
                source, kind, severity, summary, pid, tid, ppid, uid, comm, container_id,
                host, method, path, status_code, provider, model, request_id, trace_id,
                session_id, conversation_id, parent_event_id, adapter_id, adapter_version,
                confidence, attributes_json
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15,
                       ?16, ?17, ?18, ?19, ?20, ?21, ?22, ?23, ?24, ?25, ?26, ?27, ?28, ?29, ?30)",
            params![
                event.event_id,
                event.raw_event_id,
                event.schema_version as i64,
                event.timestamp_ms as i64,
                event.ingest_timestamp_ms as i64,
                event.source,
                event.kind.as_str(),
                event.severity.as_str(),
                event.summary,
                event.pid.map(|v| v as i64),
                event.tid.map(|v| v as i64),
                event.ppid.map(|v| v as i64),
                event.uid.map(|v| v as i64),
                event.comm,
                event.container_id,
                event.host,
                event.method,
                event.path,
                event.status_code.map(|v| v as i64),
                event.provider,
                event.model,
                event.request_id,
                event.trace_id,
                event.session_id,
                event.conversation_id,
                event.parent_event_id,
                event.adapter_id,
                event.adapter_version,
                event.confidence,
                attrs_json,
            ],
        )?;
        Ok(())
    }

    fn insert_llm_call(&self, call: &LlmCallInsert<'_>) -> StorageResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO llm_calls (
                id, request_event_id, response_event_id, start_timestamp_ms, end_timestamp_ms,
                pid, comm, provider, model, host, path, status_code, error_type, error_message,
                request_body_json, response_body_json, adapter_id, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18)",
            params![
                call.id,
                call.request_event_id,
                call.response_event_id,
                call.start_timestamp_ms as i64,
                call.end_timestamp_ms.map(|v| v as i64),
                call.pid as i64,
                call.comm,
                call.provider,
                call.model,
                call.host,
                call.path,
                call.status_code.map(|v| v as i64),
                call.error_type,
                call.error_message,
                call.request_body_json,
                call.response_body_json,
                call.adapter_id,
                call.confidence,
            ],
        )?;
        Ok(())
    }

    fn insert_token_usage(&self, token: &TokenInsert<'_>) -> StorageResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO token_usage (
                id, llm_call_id, timestamp_ms, pid, comm, provider, model,
                input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                total_tokens, source, adapter_id, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15)",
            params![
                token.id,
                token.llm_call_id,
                token.timestamp_ms as i64,
                token.pid as i64,
                token.comm,
                token.provider,
                token.model,
                token.input_tokens,
                token.output_tokens,
                token.cache_creation_tokens,
                token.cache_read_tokens,
                token.total_tokens,
                token.source,
                token.adapter_id,
                token.confidence,
            ],
        )?;
        Ok(())
    }

    fn insert_audit_event(&self, audit: &AuditInsert<'_>) -> StorageResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO audit_events (
                id, canonical_event_id, timestamp_ms, audit_type, pid, comm, subject,
                action, target, status, summary, details_json
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            params![
                audit.id,
                audit.canonical_event_id,
                audit.timestamp_ms as i64,
                audit.audit_type,
                audit.pid.map(|v| v as i64),
                audit.comm,
                audit.subject,
                audit.action,
                audit.target,
                audit.status,
                audit.summary,
                audit.details_json,
            ],
        )?;
        Ok(())
    }

    fn insert_interruption(&self, interruption: &InterruptionInsert<'_>) -> StorageResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO interruptions (
                id, timestamp_ms, session_id, conversation_id, severity, category,
                status, reason, evidence_json, adapter_id, confidence
             ) VALUES (?1, ?2, NULL, NULL, ?3, ?4, 'open', ?5, ?6, ?7, ?8)",
            params![
                interruption.id,
                interruption.timestamp_ms as i64,
                interruption.severity,
                interruption.category,
                interruption.reason,
                interruption.evidence_json,
                interruption.adapter_id,
                interruption.confidence,
            ],
        )?;
        Ok(())
    }

    pub fn token_summary(&self, group_by: &str) -> StorageResult<Vec<TokenSummary>> {
        let group_expr = match group_by {
            "provider" => "COALESCE(provider, 'unknown')",
            "comm" => "COALESCE(comm, 'unknown')",
            "pid" => "CAST(pid AS TEXT)",
            _ => "COALESCE(model, 'unknown')",
        };
        let sql = format!(
            "SELECT {group_expr} AS grp,
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COALESCE(SUM(cache_creation_tokens), 0),
                    COALESCE(SUM(cache_read_tokens), 0),
                    COALESCE(SUM(total_tokens), 0),
                    COUNT(*)
             FROM token_usage
             GROUP BY grp
             ORDER BY SUM(total_tokens) DESC"
        );
        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map([], |row| {
            Ok(TokenSummary {
                group: row.get(0)?,
                input_tokens: row.get(1)?,
                output_tokens: row.get(2)?,
                cache_creation_tokens: row.get(3)?,
                cache_read_tokens: row.get(4)?,
                total_tokens: row.get(5)?,
                calls: row.get(6)?,
            })
        })?;
        let mut out = Vec::new();
        for row in rows {
            out.push(row?);
        }
        Ok(out)
    }

    pub fn audit_rows(
        &self,
        audit_type: Option<&str>,
        limit: usize,
    ) -> StorageResult<Vec<AuditRow>> {
        let limit = limit.clamp(1, 10_000) as i64;
        let sql = if audit_type.is_some() {
            "SELECT timestamp_ms, audit_type, pid, comm, subject, action, target, status, summary
             FROM audit_events WHERE audit_type = ?1 ORDER BY timestamp_ms DESC LIMIT ?2"
        } else {
            "SELECT timestamp_ms, audit_type, pid, comm, subject, action, target, status, summary
             FROM audit_events WHERE (?1 IS NULL) ORDER BY timestamp_ms DESC LIMIT ?2"
        };
        let mut stmt = self.conn.prepare(sql)?;
        let rows = stmt.query_map(params![audit_type, limit], |row| {
            Ok(AuditRow {
                timestamp_ms: row.get::<_, i64>(0)? as u64,
                audit_type: row.get(1)?,
                pid: row.get::<_, Option<i64>>(2)?.map(|v| v as u32),
                comm: row.get(3)?,
                subject: row.get(4)?,
                action: row.get(5)?,
                target: row.get(6)?,
                status: row.get(7)?,
                summary: row.get(8)?,
            })
        })?;
        let mut out = Vec::new();
        for row in rows {
            out.push(row?);
        }
        Ok(out)
    }

    pub fn export_snapshot(&self, options: SnapshotOptions) -> StorageResult<Snapshot> {
        Ok(Snapshot {
            schema_version: 1,
            generated_at: Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true),
            summary: self.snapshot_summary(options)?,
            token_summary: self.token_summary("model")?,
            events: self.snapshot_events(options.event_limit)?,
            audit_events: self.snapshot_audit_events(options.audit_limit)?,
            sessions: self.snapshot_sessions()?,
            agents: self.snapshot_agents()?,
            interruptions: self.snapshot_interruptions()?,
        })
    }

    fn snapshot_summary(&self, options: SnapshotOptions) -> StorageResult<SnapshotSummary> {
        let (input_tokens, output_tokens, total_tokens): (i64, i64, i64) = self.conn.query_row(
            "SELECT COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COALESCE(SUM(total_tokens), 0)
             FROM token_usage",
            [],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )?;
        let (start_timestamp_ms, end_timestamp_ms): (Option<i64>, Option<i64>) =
            self.conn.query_row(
                "SELECT MIN(timestamp_ms), MAX(timestamp_ms) FROM canonical_events",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )?;

        Ok(SnapshotSummary {
            source: "sqlite".to_string(),
            raw_events: self.count_table("raw_events")?,
            canonical_events: self.count_table("canonical_events")?,
            llm_calls: self.count_table("llm_calls")?,
            token_usage_rows: self.count_table("token_usage")?,
            audit_events: self.count_table("audit_events")?,
            sessions: self.count_table("agent_sessions")?,
            interruptions: self.count_table("interruptions")?,
            input_tokens,
            output_tokens,
            total_tokens,
            start_timestamp_ms: start_timestamp_ms.map(|v| v as u64),
            end_timestamp_ms: end_timestamp_ms.map(|v| v as u64),
            event_limit: options.event_limit,
            audit_limit: options.audit_limit,
        })
    }

    fn count_table(&self, table: &str) -> StorageResult<i64> {
        let sql = match table {
            "raw_events" => "SELECT COUNT(*) FROM raw_events",
            "canonical_events" => "SELECT COUNT(*) FROM canonical_events",
            "llm_calls" => "SELECT COUNT(*) FROM llm_calls",
            "token_usage" => "SELECT COUNT(*) FROM token_usage",
            "audit_events" => "SELECT COUNT(*) FROM audit_events",
            "agent_sessions" => "SELECT COUNT(*) FROM agent_sessions",
            "interruptions" => "SELECT COUNT(*) FROM interruptions",
            _ => return Err(format!("unknown table '{}'", table).into()),
        };
        Ok(self.conn.query_row(sql, [], |r| r.get(0))?)
    }

    fn snapshot_events(&self, limit: usize) -> StorageResult<Vec<EventRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, timestamp_ms, source, kind, severity, summary, pid, comm,
                    host, method, path, status_code, provider, model, session_id,
                    conversation_id, adapter_id, confidence
             FROM canonical_events
             ORDER BY timestamp_ms, id
             LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![bounded_limit(limit)], |row| {
            Ok(EventRow {
                id: row.get(0)?,
                timestamp_ms: row.get::<_, i64>(1)? as u64,
                source: row.get(2)?,
                kind: row.get(3)?,
                severity: row.get(4)?,
                summary: row.get(5)?,
                pid: row.get::<_, Option<i64>>(6)?.map(|v| v as u32),
                comm: row.get(7)?,
                host: row.get(8)?,
                method: row.get(9)?,
                path: row.get(10)?,
                status_code: row.get::<_, Option<i64>>(11)?.map(|v| v as u16),
                provider: row.get(12)?,
                model: row.get(13)?,
                session_id: row.get(14)?,
                conversation_id: row.get(15)?,
                adapter_id: row.get(16)?,
                confidence: row.get(17)?,
            })
        })?;
        collect_rows(rows)
    }

    fn snapshot_audit_events(&self, limit: usize) -> StorageResult<Vec<AuditEventRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, timestamp_ms, audit_type, pid, comm, subject, action,
                    target, status, summary, details_json
             FROM audit_events
             ORDER BY timestamp_ms, id
             LIMIT ?1",
        )?;
        let rows = stmt.query_map(params![bounded_limit(limit)], |row| {
            let details_json: String = row.get(10)?;
            Ok(AuditEventRow {
                id: row.get(0)?,
                timestamp_ms: row.get::<_, i64>(1)? as u64,
                audit_type: row.get(2)?,
                pid: row.get::<_, Option<i64>>(3)?.map(|v| v as u32),
                comm: row.get(4)?,
                subject: row.get(5)?,
                action: row.get(6)?,
                target: row.get(7)?,
                status: row.get(8)?,
                summary: row.get(9)?,
                details: parse_json_value(&details_json),
            })
        })?;
        collect_rows(rows)
    }

    fn snapshot_sessions(&self) -> StorageResult<Vec<SessionRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, agent_type, agent_name, pid, comm, start_timestamp_ms,
                    end_timestamp_ms, status, model, input_tokens, output_tokens,
                    total_tokens, adapter_id, confidence, attributes_json
             FROM agent_sessions
             ORDER BY start_timestamp_ms, id",
        )?;
        let rows = stmt.query_map([], |row| {
            let attributes_json: String = row.get(14)?;
            Ok(SessionRow {
                id: row.get(0)?,
                agent_type: row.get(1)?,
                agent_name: row.get(2)?,
                pid: row.get::<_, Option<i64>>(3)?.map(|v| v as u32),
                comm: row.get(4)?,
                start_timestamp_ms: row.get::<_, i64>(5)? as u64,
                end_timestamp_ms: row.get::<_, Option<i64>>(6)?.map(|v| v as u64),
                status: row.get(7)?,
                model: row.get(8)?,
                input_tokens: row.get(9)?,
                output_tokens: row.get(10)?,
                total_tokens: row.get(11)?,
                adapter_id: row.get(12)?,
                confidence: row.get(13)?,
                attributes: parse_json_value(&attributes_json),
            })
        })?;
        collect_rows(rows)
    }

    fn snapshot_agents(&self) -> StorageResult<Vec<AgentRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT agent_type,
                    MAX(agent_name),
                    COUNT(*),
                    COALESCE(SUM(input_tokens), 0),
                    COALESCE(SUM(output_tokens), 0),
                    COALESCE(SUM(total_tokens), 0),
                    MAX(COALESCE(end_timestamp_ms, start_timestamp_ms))
             FROM agent_sessions
             GROUP BY agent_type
             ORDER BY agent_type",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(AgentRow {
                agent_type: row.get(0)?,
                agent_name: row.get(1)?,
                sessions: row.get(2)?,
                input_tokens: row.get(3)?,
                output_tokens: row.get(4)?,
                total_tokens: row.get(5)?,
                last_seen_ms: row.get::<_, Option<i64>>(6)?.map(|v| v as u64),
            })
        })?;
        collect_rows(rows)
    }

    fn snapshot_interruptions(&self) -> StorageResult<Vec<InterruptionRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, timestamp_ms, session_id, conversation_id, severity,
                    category, status, reason, evidence_json, adapter_id, confidence
             FROM interruptions
             ORDER BY timestamp_ms, id",
        )?;
        let rows = stmt.query_map([], |row| {
            let evidence_json: String = row.get(8)?;
            Ok(InterruptionRow {
                id: row.get(0)?,
                timestamp_ms: row.get::<_, i64>(1)? as u64,
                session_id: row.get(2)?,
                conversation_id: row.get(3)?,
                severity: row.get(4)?,
                category: row.get(5)?,
                status: row.get(6)?,
                reason: row.get(7)?,
                evidence: parse_json_value(&evidence_json),
                adapter_id: row.get(9)?,
                confidence: row.get(10)?,
            })
        })?;
        collect_rows(rows)
    }
}

fn bounded_limit(limit: usize) -> i64 {
    limit.min(100_000) as i64
}

fn parse_json_value(text: &str) -> Value {
    serde_json::from_str(text).unwrap_or_else(|_| Value::String(text.to_string()))
}

fn collect_rows<T, F>(rows: rusqlite::MappedRows<'_, F>) -> StorageResult<Vec<T>>
where
    F: FnMut(&rusqlite::Row<'_>) -> rusqlite::Result<T>,
{
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

#[derive(Default)]
pub struct GenericProjector {
    pending: HashMap<(u32, u64), VecDeque<PendingRequest>>,
}

impl GenericProjector {
    pub fn new() -> Self {
        Self::default()
    }

    fn process(&mut self, store: &SqliteStore, event: &CanonicalEvent) -> StorageResult<()> {
        match event.kind {
            EventKind::LlmRequest => {
                if let (Some(pid), Some(tid)) = (event.pid, event.tid) {
                    self.pending
                        .entry((pid, tid))
                        .or_default()
                        .push_back(PendingRequest {
                            canonical_event_id: event.event_id.clone(),
                            timestamp_ms: event.timestamp_ms,
                            pid,
                            comm: event.comm.clone().unwrap_or_default(),
                            provider: event.provider.clone(),
                            model: event.model.clone(),
                            host: event.host.clone(),
                            path: event.path.clone(),
                            body_json: body_json(&event.attributes),
                        });
                }
            }
            EventKind::HttpResponse | EventKind::LlmResponse | EventKind::LlmError => {
                if let (Some(pid), Some(tid)) = (event.pid, event.tid) {
                    let key = (pid, tid);
                    let mut remove_key = false;
                    let req = self.pending.get_mut(&key).and_then(|requests| {
                        let req = requests.pop_front();
                        remove_key = requests.is_empty();
                        req
                    });
                    if remove_key {
                        self.pending.remove(&key);
                    }
                    if let Some(req) = req {
                        self.project_llm_pair(store, req, event)?;
                    }
                }
            }
            EventKind::ProcessExec => self.project_process_audit(store, event, "exec")?,
            EventKind::ProcessExit => self.project_process_audit(store, event, "exit")?,
            EventKind::FsWrite | EventKind::FsMutation => self.project_file_audit(store, event)?,
            _ => {}
        }
        Ok(())
    }

    fn project_llm_pair(
        &self,
        store: &SqliteStore,
        req: PendingRequest,
        resp: &CanonicalEvent,
    ) -> StorageResult<()> {
        let response_body = body_json(&resp.attributes);
        let response_body = response_body.or_else(|| {
            if resp.source == "sse_processor" {
                Some(resp.attributes.clone())
            } else {
                None
            }
        });
        let model = req
            .model
            .clone()
            .or_else(|| response_body.as_ref().and_then(extract_model))
            .or_else(|| resp.model.clone());
        let provider = req
            .provider
            .clone()
            .or_else(|| req.host.as_deref().map(provider_from_host));
        let status_code = resp.status_code;
        let llm_call_id = format!("llm-{}", req.canonical_event_id);
        let request_body_json = req.body_json.as_ref().map(|v| v.to_string());
        let response_body_json = response_body.as_ref().map(|v| v.to_string());
        let error_type = status_code
            .filter(|c| *c >= 400)
            .map(|c| format!("http_{}", c));
        let error_message = error_type.clone();

        store.insert_llm_call(&LlmCallInsert {
            id: &llm_call_id,
            request_event_id: &req.canonical_event_id,
            response_event_id: Some(resp.event_id.as_str()),
            start_timestamp_ms: req.timestamp_ms,
            end_timestamp_ms: Some(resp.timestamp_ms),
            pid: req.pid,
            comm: &req.comm,
            provider: provider.as_deref(),
            model: model.as_deref(),
            host: req.host.as_deref(),
            path: req.path.as_deref(),
            status_code,
            error_type: error_type.as_deref(),
            error_message: error_message.as_deref(),
            request_body_json: request_body_json.as_deref(),
            response_body_json: response_body_json.as_deref(),
            adapter_id: "generic",
            confidence: 0.80,
        })?;

        let usage = if resp.source == "sse_processor" {
            extract_token_usage_from_sse(&resp.attributes)
        } else {
            response_body
                .as_ref()
                .map(extract_token_usage)
                .unwrap_or_default()
        };
        if !usage.is_empty() {
            store.insert_token_usage(&TokenInsert {
                id: &format!("token-{}", llm_call_id),
                llm_call_id: &llm_call_id,
                timestamp_ms: resp.timestamp_ms,
                pid: req.pid,
                comm: &req.comm,
                provider: provider.as_deref(),
                model: model.as_deref(),
                input_tokens: usage.input_tokens,
                output_tokens: usage.output_tokens,
                cache_creation_tokens: usage.cache_creation_tokens,
                cache_read_tokens: usage.cache_read_tokens,
                total_tokens: usage.total_tokens(),
                source: "response_usage",
                adapter_id: "generic",
                confidence: 0.80,
            })?;
        }

        let status = if status_code.map(|c| c >= 400).unwrap_or(false) {
            "failure"
        } else {
            "success"
        };
        store.insert_audit_event(&AuditInsert {
            id: &format!("audit-{}", llm_call_id),
            canonical_event_id: Some(resp.event_id.as_str()),
            timestamp_ms: resp.timestamp_ms,
            audit_type: "llm",
            pid: Some(req.pid),
            comm: Some(&req.comm),
            subject: model.as_deref(),
            action: Some("call"),
            target: req.host.as_deref(),
            status: Some(status),
            summary: Some("LLM call"),
            details_json: response_body_json.as_deref().unwrap_or("{}"),
        })?;

        if status == "failure" {
            store.insert_interruption(&InterruptionInsert {
                id: &format!("interrupt-{}", llm_call_id),
                timestamp_ms: resp.timestamp_ms,
                severity: "error",
                category: "llm_error",
                reason: error_message.as_deref().unwrap_or("LLM call failed"),
                evidence_json: response_body_json.as_deref().unwrap_or("{}"),
                adapter_id: "generic",
                confidence: 0.80,
            })?;
        }

        Ok(())
    }

    fn project_process_audit(
        &self,
        store: &SqliteStore,
        event: &CanonicalEvent,
        action: &str,
    ) -> StorageResult<()> {
        let target = event.attributes.get("filename").and_then(|v| v.as_str());
        store.insert_audit_event(&AuditInsert {
            id: &format!("audit-{}", event.event_id),
            canonical_event_id: Some(event.event_id.as_str()),
            timestamp_ms: event.timestamp_ms,
            audit_type: "process",
            pid: event.pid,
            comm: event.comm.as_deref(),
            subject: event.comm.as_deref(),
            action: Some(action),
            target,
            status: Some("observed"),
            summary: event.summary.as_deref(),
            details_json: &event.attributes.to_string(),
        })
    }

    fn project_file_audit(&self, store: &SqliteStore, event: &CanonicalEvent) -> StorageResult<()> {
        let target = event
            .attributes
            .get("path")
            .or_else(|| event.attributes.get("filepath"))
            .and_then(|v| v.as_str());
        store.insert_audit_event(&AuditInsert {
            id: &format!("audit-{}", event.event_id),
            canonical_event_id: Some(event.event_id.as_str()),
            timestamp_ms: event.timestamp_ms,
            audit_type: "file",
            pid: event.pid,
            comm: event.comm.as_deref(),
            subject: event.comm.as_deref(),
            action: Some("write"),
            target,
            status: Some("observed"),
            summary: event.summary.as_deref(),
            details_json: &event.attributes.to_string(),
        })
    }
}

struct LlmCallInsert<'a> {
    id: &'a str,
    request_event_id: &'a str,
    response_event_id: Option<&'a str>,
    start_timestamp_ms: u64,
    end_timestamp_ms: Option<u64>,
    pid: u32,
    comm: &'a str,
    provider: Option<&'a str>,
    model: Option<&'a str>,
    host: Option<&'a str>,
    path: Option<&'a str>,
    status_code: Option<u16>,
    error_type: Option<&'a str>,
    error_message: Option<&'a str>,
    request_body_json: Option<&'a str>,
    response_body_json: Option<&'a str>,
    adapter_id: &'a str,
    confidence: f32,
}

struct TokenInsert<'a> {
    id: &'a str,
    llm_call_id: &'a str,
    timestamp_ms: u64,
    pid: u32,
    comm: &'a str,
    provider: Option<&'a str>,
    model: Option<&'a str>,
    input_tokens: i64,
    output_tokens: i64,
    cache_creation_tokens: i64,
    cache_read_tokens: i64,
    total_tokens: i64,
    source: &'a str,
    adapter_id: &'a str,
    confidence: f32,
}

struct AuditInsert<'a> {
    id: &'a str,
    canonical_event_id: Option<&'a str>,
    timestamp_ms: u64,
    audit_type: &'a str,
    pid: Option<u32>,
    comm: Option<&'a str>,
    subject: Option<&'a str>,
    action: Option<&'a str>,
    target: Option<&'a str>,
    status: Option<&'a str>,
    summary: Option<&'a str>,
    details_json: &'a str,
}

struct InterruptionInsert<'a> {
    id: &'a str,
    timestamp_ms: u64,
    severity: &'a str,
    category: &'a str,
    reason: &'a str,
    evidence_json: &'a str,
    adapter_id: &'a str,
    confidence: f32,
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn sanitize_id(s: &str) -> String {
    s.chars()
        .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
        .collect()
}

const SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS raw_events (
  id TEXT PRIMARY KEY,
  timestamp_ms INTEGER NOT NULL,
  source TEXT NOT NULL,
  pid INTEGER,
  comm TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_events (
  id TEXT PRIMARY KEY,
  raw_event_id TEXT NOT NULL REFERENCES raw_events(id),
  schema_version INTEGER NOT NULL,
  timestamp_ms INTEGER NOT NULL,
  ingest_timestamp_ms INTEGER NOT NULL,
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info',
  summary TEXT,
  pid INTEGER,
  tid INTEGER,
  ppid INTEGER,
  uid INTEGER,
  comm TEXT,
  container_id TEXT,
  host TEXT,
  method TEXT,
  path TEXT,
  status_code INTEGER,
  provider TEXT,
  model TEXT,
  request_id TEXT,
  trace_id TEXT,
  session_id TEXT,
  conversation_id TEXT,
  parent_event_id TEXT,
  adapter_id TEXT,
  adapter_version TEXT,
  confidence REAL,
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_canonical_time ON canonical_events(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_kind_time ON canonical_events(kind, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_pid_time ON canonical_events(pid, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_comm_time ON canonical_events(comm, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_host_time ON canonical_events(host, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_model_time ON canonical_events(model, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_canonical_session_time ON canonical_events(session_id, timestamp_ms);

CREATE TABLE IF NOT EXISTS llm_calls (
  id TEXT PRIMARY KEY,
  request_event_id TEXT,
  response_event_id TEXT,
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  pid INTEGER,
  comm TEXT,
  provider TEXT,
  model TEXT,
  host TEXT,
  path TEXT,
  status_code INTEGER,
  error_type TEXT,
  error_message TEXT,
  request_body_json TEXT,
  response_body_json TEXT,
  adapter_id TEXT,
  confidence REAL
);

CREATE TABLE IF NOT EXISTS token_usage (
  id TEXT PRIMARY KEY,
  llm_call_id TEXT REFERENCES llm_calls(id),
  timestamp_ms INTEGER NOT NULL,
  pid INTEGER,
  comm TEXT,
  provider TEXT,
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cache_creation_tokens INTEGER DEFAULT 0,
  cache_read_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  source TEXT NOT NULL,
  adapter_id TEXT,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_token_time ON token_usage(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_token_model_time ON token_usage(model, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_token_comm_time ON token_usage(comm, timestamp_ms);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  canonical_event_id TEXT REFERENCES canonical_events(id),
  timestamp_ms INTEGER NOT NULL,
  audit_type TEXT NOT NULL,
  pid INTEGER,
  comm TEXT,
  subject TEXT,
  action TEXT,
  target TEXT,
  status TEXT,
  summary TEXT,
  details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agent_sessions (
  id TEXT PRIMARY KEY,
  agent_type TEXT NOT NULL,
  agent_name TEXT,
  pid INTEGER,
  comm TEXT,
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  status TEXT NOT NULL DEFAULT 'active',
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  adapter_id TEXT NOT NULL,
  confidence REAL,
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES agent_sessions(id),
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  model TEXT,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active',
  attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  conversation_id TEXT,
  timestamp_ms INTEGER NOT NULL,
  tool_name TEXT,
  tool_call_id TEXT,
  status TEXT,
  input_json TEXT,
  output_json TEXT,
  related_pid INTEGER,
  related_event_id TEXT,
  adapter_id TEXT NOT NULL,
  confidence REAL
);

CREATE TABLE IF NOT EXISTS interruptions (
  id TEXT PRIMARY KEY,
  timestamp_ms INTEGER NOT NULL,
  session_id TEXT,
  conversation_id TEXT,
  severity TEXT NOT NULL,
  category TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  reason TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}',
  adapter_id TEXT,
  confidence REAL
);

CREATE TABLE IF NOT EXISTS adapter_runs (
  id TEXT PRIMARY KEY,
  adapter_id TEXT NOT NULL,
  adapter_version TEXT NOT NULL,
  started_at_ms INTEGER NOT NULL,
  finished_at_ms INTEGER,
  mode TEXT NOT NULL,
  input_range_start_ms INTEGER,
  input_range_end_ms INTEGER,
  status TEXT NOT NULL,
  error_message TEXT
);
"#;

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn stores_anthropic_pair_and_tokens() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"model\":\"claude-sonnet-4-20250514\",\"usage\":{\"input_tokens\":10,\"output_tokens\":5}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();
        let summary = store.token_summary("model").unwrap();
        assert_eq!(summary.len(), 1);
        assert_eq!(summary[0].total_tokens, 15);
    }

    #[test]
    fn exports_api_shaped_snapshot() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "response",
                "status_code": 200,
                "body": "{\"model\":\"claude-sonnet-4-20250514\",\"usage\":{\"input_tokens\":10,\"output_tokens\":5}}"
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&resp, &mut projector).unwrap();
        store
            .connection_mut()
            .execute(
                "INSERT INTO agent_sessions (
                    id, agent_type, agent_name, pid, comm, start_timestamp_ms,
                    end_timestamp_ms, status, model, input_tokens, output_tokens,
                    total_tokens, adapter_id, confidence, attributes_json
                 ) VALUES (
                    'claude-code-pid-42', 'claude-code', 'Claude Code', 42,
                    'claude', 1, 2, 'observed', 'claude-sonnet-4-20250514',
                    10, 5, 15, 'claude-code', 0.9, '{\"projection\":\"test\"}'
                 )",
                [],
            )
            .unwrap();

        let snapshot = store.export_snapshot(SnapshotOptions::default()).unwrap();
        assert_eq!(snapshot.schema_version, 1);
        assert_eq!(snapshot.summary.source, "sqlite");
        assert_eq!(snapshot.summary.canonical_events, 2);
        assert_eq!(snapshot.summary.total_tokens, 15);
        assert_eq!(snapshot.token_summary[0].total_tokens, 15);
        assert_eq!(snapshot.events.len(), 2);
        assert_eq!(snapshot.audit_events.len(), 1);
        assert_eq!(snapshot.sessions[0].agent_type, "claude-code");
        assert_eq!(snapshot.agents[0].sessions, 1);
        assert!(snapshot.interruptions.is_empty());
    }

    #[test]
    fn stores_sse_tokens() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        let req = Event::new_with_timestamp(
            1,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet-4-20250514\"}"
            }),
        );
        let sse = Event::new_with_timestamp(
            2,
            "sse_processor".to_string(),
            42,
            "claude".to_string(),
            json!({
                "tid": 7,
                "sse_events": [
                    {"event":"message_start","parsed_data":{"message":{"model":"claude-sonnet-4-20250514","usage":{"input_tokens":9}}}},
                    {"event":"message_delta","parsed_data":{"usage":{"output_tokens":6}}}
                ]
            }),
        );
        store.insert_event(&req, &mut projector).unwrap();
        store.insert_event(&sse, &mut projector).unwrap();
        let summary = store.token_summary("model").unwrap();
        assert_eq!(summary[0].total_tokens, 15);
    }

    #[test]
    fn correlates_multiple_pending_requests_on_same_thread_fifo() {
        let mut store = SqliteStore::open_in_memory().unwrap();
        let mut projector = GenericProjector::new();
        for (timestamp, model) in [(1, "claude-a"), (2, "claude-b")] {
            let req = Event::new_with_timestamp(
                timestamp,
                "http_parser".to_string(),
                42,
                "claude".to_string(),
                json!({
                    "tid": 7,
                    "message_type": "request",
                    "method": "POST",
                    "path": "/v1/messages",
                    "headers": { "host": "api.anthropic.com" },
                    "body": format!("{{\"model\":\"{}\"}}", model)
                }),
            );
            store.insert_event(&req, &mut projector).unwrap();
        }
        for (timestamp, total) in [(3, 10), (4, 20)] {
            let resp = Event::new_with_timestamp(
                timestamp,
                "http_parser".to_string(),
                42,
                "claude".to_string(),
                json!({
                    "tid": 7,
                    "message_type": "response",
                    "status_code": 200,
                    "body": format!("{{\"usage\":{{\"input_tokens\":{},\"output_tokens\":0}}}}", total)
                }),
            );
            store.insert_event(&resp, &mut projector).unwrap();
        }

        let count: i64 = store
            .connection()
            .query_row("SELECT COUNT(*) FROM llm_calls", [], |r| r.get(0))
            .unwrap();
        let total: i64 = store
            .connection()
            .query_row(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM token_usage",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 2);
        assert_eq!(total, 30);
    }
}
