// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::json::{parse_optional_value as parse_optional_json, parse_value as parse_json_value};
use crate::model::{
    AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow, ResourceSampleRow, TokenUsageRow,
    ToolCallRow, ViewResult, ViewSink,
};
use rusqlite::{Connection, OpenFlags, params};
use std::path::Path;

pub(crate) struct SqliteStore {
    conn: Connection,
}

impl SqliteStore {
    pub(crate) fn open(path: impl AsRef<Path>) -> ViewResult<Self> {
        let conn = Connection::open(path)?;
        let mut store = Self { conn };
        store.init()?;
        Ok(store)
    }

    pub(crate) fn open_readonly(path: impl AsRef<Path>) -> ViewResult<Self> {
        let conn = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
        Ok(Self { conn })
    }

    fn has_column(&self, table: &str, column: &str) -> bool {
        self.conn
            .prepare(&format!("SELECT {column} FROM {table} LIMIT 0"))
            .is_ok()
    }

    #[cfg(test)]
    pub(crate) fn connection(&self) -> &Connection {
        &self.conn
    }

    fn init(&mut self) -> ViewResult<()> {
        self.conn.pragma_update(None, "journal_mode", "WAL").ok();
        self.conn
            .busy_timeout(std::time::Duration::from_millis(500))
            .ok();
        self.conn.pragma_update(None, "foreign_keys", "ON")?;
        self.conn.execute_batch(SCHEMA)?;
        self.ensure_llm_call_columns()?;
        Ok(())
    }

    fn ensure_llm_call_columns(&self) -> ViewResult<()> {
        for (column, ty) in [
            ("session_id", "TEXT"),
            ("conversation_id", "TEXT"),
            ("call_kind", "TEXT"),
            ("status", "TEXT NOT NULL DEFAULT 'observed'"),
            ("error_type", "TEXT"),
            ("finish_reason", "TEXT"),
        ] {
            if !self.has_column("llm_calls", column) {
                self.conn.execute(
                    &format!("ALTER TABLE llm_calls ADD COLUMN {column} {ty}"),
                    [],
                )?;
            }
        }
        Ok(())
    }

    fn upsert_network_target(&self, target: &NetworkTargetRow) -> ViewResult<()> {
        let id = network_target_id(target);
        self.conn.execute(
            "INSERT INTO network_targets (
                id, pid, comm, host, path, count, error_count, first_timestamp_ms, last_timestamp_ms
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)
             ON CONFLICT(id) DO UPDATE SET
                count = count + excluded.count,
                error_count = error_count + excluded.error_count,
                first_timestamp_ms = MIN(first_timestamp_ms, excluded.first_timestamp_ms),
                last_timestamp_ms = MAX(last_timestamp_ms, excluded.last_timestamp_ms)",
            params![
                id,
                target.pid.map(|v| v as i64),
                target.comm.as_deref(),
                target.host.as_str(),
                target.path.as_deref(),
                target.count,
                target.error_count,
                target.first_timestamp_ms.map(|v| v as i64),
                target.last_timestamp_ms.map(|v| v as i64),
            ],
        )?;
        Ok(())
    }

    fn insert_resource_sample(&self, sample: &ResourceSampleRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT INTO resource_samples (timestamp_ms, pid, comm, cpu_percent, rss_mb)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                sample.timestamp_ms as i64,
                sample.pid.map(|v| v as i64),
                sample.comm.as_deref(),
                sample.cpu_percent,
                sample.rss_mb,
            ],
        )?;
        Ok(())
    }

    fn insert_llm_call(&self, call: &LlmCallRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO llm_calls (
                id, session_id, conversation_id, start_timestamp_ms, end_timestamp_ms,
                pid, comm, provider, model, call_kind, status, error_type, finish_reason,
                host, path, status_code, request_body_json, response_body_json,
                view_source, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20)",
            params![
                call.id,
                call.session_id.as_deref(),
                call.conversation_id.as_deref(),
                call.start_timestamp_ms as i64,
                call.end_timestamp_ms.map(|v| v as i64),
                call.pid.map(|v| v as i64),
                call.comm.as_deref(),
                call.provider.as_deref(),
                call.model.as_deref(),
                call.call_kind.as_deref(),
                call.status.as_str(),
                call.error_type.as_deref(),
                call.finish_reason.as_deref(),
                call.host.as_deref(),
                call.path.as_deref(),
                call.status_code.map(|v| v as i64),
                call.request.to_string(),
                call.response.to_string(),
                "live_view",
                1.0f32,
            ],
        )?;
        Ok(())
    }

    fn insert_token_usage(&self, token: &TokenUsageRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO token_usage (
                id, llm_call_id, timestamp_ms, pid, comm, provider, model,
                input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                total_tokens, source, view_source, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15)",
            params![
                token.id,
                token.llm_call_id,
                token.timestamp_ms as i64,
                token.pid.map(|v| v as i64),
                token.comm.as_deref(),
                token.provider.as_deref(),
                token.model.as_deref(),
                token.input_tokens,
                token.output_tokens,
                token.cache_creation_tokens,
                token.cache_read_tokens,
                token.total_tokens,
                token.source,
                token.view_source,
                token.confidence.unwrap_or(1.0),
            ],
        )?;
        Ok(())
    }

    fn insert_audit_event(&self, audit: &AuditEventRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO audit_events (
                id, timestamp_ms, audit_type, pid, comm, subject,
                action, target, status, summary, details_json
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
            params![
                audit.id,
                audit.timestamp_ms as i64,
                audit.audit_type,
                audit.pid.map(|v| v as i64),
                audit.comm.as_deref(),
                audit.subject.as_deref(),
                audit.action.as_deref(),
                audit.target.as_deref(),
                audit.status.as_deref(),
                audit.summary.as_deref(),
                audit.details.to_string(),
            ],
        )?;
        Ok(())
    }

    fn upsert_process_node(&self, process: &ProcessNodeRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT INTO process_nodes (
                id, pid, ppid, root_pid, start_timestamp_ms, end_timestamp_ms,
                comm, command, argv_json, cwd, exit_code, status, view_source, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)
             ON CONFLICT(id) DO UPDATE SET
                ppid = COALESCE(excluded.ppid, ppid),
                root_pid = COALESCE(excluded.root_pid, root_pid),
                start_timestamp_ms = CASE
                    WHEN start_timestamp_ms IS NULL THEN excluded.start_timestamp_ms
                    WHEN excluded.start_timestamp_ms IS NULL THEN start_timestamp_ms
                    ELSE MIN(start_timestamp_ms, excluded.start_timestamp_ms)
                END,
                end_timestamp_ms = CASE
                    WHEN end_timestamp_ms IS NULL THEN excluded.end_timestamp_ms
                    WHEN excluded.end_timestamp_ms IS NULL THEN end_timestamp_ms
                    ELSE MAX(end_timestamp_ms, excluded.end_timestamp_ms)
                END,
                comm = COALESCE(excluded.comm, comm),
                command = COALESCE(excluded.command, command),
                argv_json = CASE
                    WHEN argv_json = '[]' AND excluded.argv_json != '[]' THEN excluded.argv_json
                    ELSE argv_json
                END,
                cwd = COALESCE(excluded.cwd, cwd),
                exit_code = COALESCE(excluded.exit_code, exit_code),
                status = COALESCE(excluded.status, status),
                confidence = MAX(COALESCE(confidence, 0), COALESCE(excluded.confidence, 0))",
            params![
                process.id,
                process.pid as i64,
                process.ppid.map(|v| v as i64),
                process.root_pid.map(|v| v as i64),
                process.start_timestamp_ms.map(|v| v as i64),
                process.end_timestamp_ms.map(|v| v as i64),
                process.comm.as_deref(),
                process.command.as_deref(),
                serde_json::to_string(&process.argv)?,
                process.cwd.as_deref(),
                process.exit_code.map(|v| v as i64),
                process.status.as_deref(),
                process.view_source,
                process.confidence.unwrap_or(1.0),
            ],
        )?;
        Ok(())
    }

    fn insert_tool_call(&self, tool: &ToolCallRow) -> ViewResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO tool_calls (
                id, session_id, conversation_id, timestamp_ms, tool_name, tool_call_id,
                start_timestamp_ms, end_timestamp_ms, duration_ms, status, input_json,
                output_json, related_pid, related_event_id, view_source, confidence
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16)",
            params![
                tool.id,
                tool.session_id.as_deref(),
                tool.conversation_id.as_deref(),
                tool.timestamp_ms as i64,
                tool.tool_name.as_deref(),
                tool.tool_call_id.as_deref(),
                tool.start_timestamp_ms.map(|v| v as i64),
                tool.end_timestamp_ms.map(|v| v as i64),
                tool.duration_ms.map(|v| v as i64),
                tool.status.as_deref(),
                tool.input.to_string(),
                tool.output.to_string(),
                tool.related_pid.map(|v| v as i64),
                tool.related_event_id.as_deref(),
                tool.view_source,
                tool.confidence.unwrap_or(1.0),
            ],
        )?;
        Ok(())
    }

    pub(crate) fn all_llm_call_rows(&self) -> ViewResult<Vec<LlmCallRow>> {
        let optional_cols = [
            ("session_id", "NULL AS session_id"),
            ("conversation_id", "NULL AS conversation_id"),
            ("call_kind", "NULL AS call_kind"),
            ("status", "'observed' AS status"),
            ("error_type", "NULL AS error_type"),
            ("finish_reason", "NULL AS finish_reason"),
        ];
        let optional_select = optional_cols
            .iter()
            .map(|(column, fallback)| {
                if self.has_column("llm_calls", column) {
                    (*column).to_string()
                } else {
                    (*fallback).to_string()
                }
            })
            .collect::<Vec<_>>()
            .join(", ");
        let mut stmt = self.conn.prepare(&format!(
            "SELECT id, {optional_select}, start_timestamp_ms, end_timestamp_ms, pid, comm,
                    provider, model, host, path, status_code,
                    COALESCE(request_body_json, '{{}}'), COALESCE(response_body_json, '{{}}')
             FROM llm_calls
             ORDER BY start_timestamp_ms DESC"
        ))?;
        let rows = stmt.query_map([], read_llm_call_row)?;
        collect_rows(rows)
    }

    pub(crate) fn token_usage_rows(&self) -> ViewResult<Vec<TokenUsageRow>> {
        let has_view_source = self.has_column("token_usage", "view_source");
        let extra_cols = if has_view_source {
            ", view_source, confidence"
        } else {
            ""
        };
        let sql = format!(
            "SELECT id, llm_call_id, timestamp_ms, pid, comm, provider, model,
                    input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
                    total_tokens, source{extra_cols}
             FROM token_usage
             ORDER BY timestamp_ms, id"
        );
        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map([], move |row| {
            Ok(TokenUsageRow {
                id: row.get(0)?,
                llm_call_id: row.get::<_, Option<String>>(1)?.unwrap_or_default(),
                timestamp_ms: row.get::<_, i64>(2)? as u64,
                pid: row.get::<_, Option<i64>>(3)?.map(|v| v as u32),
                comm: row.get(4)?,
                provider: row.get(5)?,
                model: row.get(6)?,
                input_tokens: row.get(7)?,
                output_tokens: row.get(8)?,
                cache_creation_tokens: row.get(9)?,
                cache_read_tokens: row.get(10)?,
                total_tokens: row.get(11)?,
                source: row
                    .get::<_, Option<String>>(12)?
                    .unwrap_or_else(|| "unknown".to_string()),
                view_source: if has_view_source {
                    row.get::<_, Option<String>>(13)?
                        .unwrap_or_else(|| "view".to_string())
                } else {
                    "view".to_string()
                },
                confidence: if has_view_source { row.get(14)? } else { None },
            })
        })?;
        collect_rows(rows)
    }

    pub(crate) fn tool_call_rows(&self) -> ViewResult<Vec<ToolCallRow>> {
        let has_view_source = self.has_column("tool_calls", "view_source");
        let extra_cols = if has_view_source {
            ", view_source, confidence"
        } else {
            ""
        };
        let sql = format!(
            "SELECT id, session_id, conversation_id, timestamp_ms, tool_name, tool_call_id,
                    start_timestamp_ms, end_timestamp_ms, duration_ms, status, input_json,
                    output_json, related_pid, related_event_id{extra_cols}
             FROM tool_calls
             ORDER BY timestamp_ms, id"
        );
        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map([], move |row| {
            let input_json: Option<String> = row.get(10)?;
            let output_json: Option<String> = row.get(11)?;
            Ok(ToolCallRow {
                id: row.get(0)?,
                session_id: row.get(1)?,
                conversation_id: row.get(2)?,
                timestamp_ms: row.get::<_, i64>(3)? as u64,
                tool_name: row.get(4)?,
                tool_call_id: row.get(5)?,
                start_timestamp_ms: row.get::<_, Option<i64>>(6)?.map(|v| v as u64),
                end_timestamp_ms: row.get::<_, Option<i64>>(7)?.map(|v| v as u64),
                duration_ms: row.get::<_, Option<i64>>(8)?.map(|v| v as u64),
                status: row.get(9)?,
                input: parse_optional_json(input_json.as_deref()),
                output: parse_optional_json(output_json.as_deref()),
                related_pid: row.get::<_, Option<i64>>(12)?.map(|v| v as u32),
                related_event_id: row.get(13)?,
                view_source: if has_view_source {
                    row.get::<_, Option<String>>(14)?
                        .unwrap_or_else(|| "view".to_string())
                } else {
                    "view".to_string()
                },
                confidence: if has_view_source { row.get(15)? } else { None },
            })
        })?;
        collect_rows(rows)
    }

    pub(crate) fn resource_sample_rows(&self) -> ViewResult<Vec<ResourceSampleRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT timestamp_ms, pid, comm, cpu_percent, rss_mb
             FROM resource_samples
             ORDER BY timestamp_ms",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(ResourceSampleRow {
                timestamp_ms: row.get::<_, i64>(0)? as u64,
                pid: row.get::<_, Option<i64>>(1)?.map(|v| v as u32),
                comm: row.get(2)?,
                cpu_percent: row.get(3)?,
                rss_mb: row.get(4)?,
            })
        })?;
        collect_rows(rows)
    }

    pub(crate) fn network_target_rows(&self) -> ViewResult<Vec<NetworkTargetRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT pid, comm, host, path, count, error_count, first_timestamp_ms, last_timestamp_ms
             FROM network_targets
             ORDER BY count DESC, host, path",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(NetworkTargetRow {
                pid: row.get::<_, Option<i64>>(0)?.map(|v| v as u32),
                comm: row.get(1)?,
                host: row.get(2)?,
                path: row.get(3)?,
                count: row.get(4)?,
                error_count: row.get(5)?,
                first_timestamp_ms: row.get::<_, Option<i64>>(6)?.map(|v| v as u64),
                last_timestamp_ms: row.get::<_, Option<i64>>(7)?.map(|v| v as u64),
            })
        })?;
        collect_rows(rows)
    }

    pub(crate) fn all_audit_event_rows(&self) -> ViewResult<Vec<AuditEventRow>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, timestamp_ms, audit_type, pid, comm, subject, action,
                    target, status, summary, details_json
             FROM audit_events
             ORDER BY timestamp_ms, id",
        )?;
        let rows = stmt.query_map([], read_audit_event_row)?;
        collect_rows(rows)
    }

    pub(crate) fn process_node_rows(&self) -> ViewResult<Vec<ProcessNodeRow>> {
        let has_view_source = self.has_column("process_nodes", "view_source");
        let extra_cols = if has_view_source {
            ", view_source, confidence"
        } else {
            ""
        };
        let sql = format!(
            "SELECT id, pid, ppid, root_pid, start_timestamp_ms, end_timestamp_ms,
                    comm, command, argv_json, cwd, exit_code, status{extra_cols}
             FROM process_nodes
             ORDER BY COALESCE(start_timestamp_ms, end_timestamp_ms, 0), pid, id"
        );
        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map([], move |row| {
            let argv_json: String = row.get(8)?;
            Ok(ProcessNodeRow {
                id: row.get(0)?,
                pid: row.get::<_, i64>(1)? as u32,
                ppid: row.get::<_, Option<i64>>(2)?.map(|v| v as u32),
                root_pid: row.get::<_, Option<i64>>(3)?.map(|v| v as u32),
                start_timestamp_ms: row.get::<_, Option<i64>>(4)?.map(|v| v as u64),
                end_timestamp_ms: row.get::<_, Option<i64>>(5)?.map(|v| v as u64),
                comm: row.get(6)?,
                command: row.get(7)?,
                argv: serde_json::from_str(&argv_json).unwrap_or_default(),
                cwd: row.get(9)?,
                exit_code: row.get::<_, Option<i64>>(10)?.map(|v| v as i32),
                status: row.get(11)?,
                view_source: if has_view_source {
                    row.get::<_, Option<String>>(12)?
                        .unwrap_or_else(|| "view".to_string())
                } else {
                    "view".to_string()
                },
                confidence: if has_view_source { row.get(13)? } else { None },
            })
        })?;
        collect_rows(rows)
    }
}

impl ViewSink for SqliteStore {
    fn llm_call(&mut self, row: &LlmCallRow) -> ViewResult<()> {
        self.insert_llm_call(row)
    }

    fn token_usage(&mut self, row: &TokenUsageRow) -> ViewResult<()> {
        self.insert_token_usage(row)
    }

    fn audit_event(&mut self, row: &AuditEventRow) -> ViewResult<()> {
        self.insert_audit_event(row)
    }

    fn process_node(&mut self, row: &ProcessNodeRow) -> ViewResult<()> {
        self.upsert_process_node(row)
    }

    fn tool_call(&mut self, row: &ToolCallRow) -> ViewResult<()> {
        self.insert_tool_call(row)
    }

    fn network_target(&mut self, row: &NetworkTargetRow) -> ViewResult<()> {
        self.upsert_network_target(row)
    }

    fn resource_sample(&mut self, row: &ResourceSampleRow) -> ViewResult<()> {
        self.insert_resource_sample(row)
    }
}

fn read_llm_call_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<LlmCallRow> {
    let request_json: String = row.get(16)?;
    let response_json: String = row.get(17)?;
    Ok(LlmCallRow {
        id: row.get(0)?,
        session_id: row.get(1)?,
        conversation_id: row.get(2)?,
        call_kind: row.get(3)?,
        status: row
            .get::<_, Option<String>>(4)?
            .unwrap_or_else(|| "observed".to_string()),
        error_type: row.get(5)?,
        finish_reason: row.get(6)?,
        start_timestamp_ms: row.get::<_, i64>(7)? as u64,
        end_timestamp_ms: row.get::<_, Option<i64>>(8)?.map(|v| v as u64),
        pid: row.get::<_, Option<i64>>(9)?.map(|v| v as u32),
        comm: row.get(10)?,
        provider: row.get(11)?,
        model: row.get(12)?,
        host: row.get(13)?,
        path: row.get(14)?,
        status_code: row.get::<_, Option<i64>>(15)?.map(|v| v as u16),
        input_tokens: 0,
        output_tokens: 0,
        total_tokens: 0,
        request: parse_json_value(&request_json),
        response: parse_json_value(&response_json),
    })
}

fn read_audit_event_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<AuditEventRow> {
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
}

fn collect_rows<T, F>(rows: rusqlite::MappedRows<'_, F>) -> ViewResult<Vec<T>>
where
    F: FnMut(&rusqlite::Row<'_>) -> rusqlite::Result<T>,
{
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

fn network_target_id(target: &NetworkTargetRow) -> String {
    let path = target.path.as_deref().unwrap_or_default();
    format!(
        "net:{}:{}:{}:{}:{}",
        target.pid.unwrap_or_default(),
        target.host.len(),
        target.host,
        path.len(),
        path
    )
}

const SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS network_targets (
  id TEXT PRIMARY KEY,
  pid INTEGER,
  comm TEXT,
  host TEXT NOT NULL,
  path TEXT,
  count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  first_timestamp_ms INTEGER,
  last_timestamp_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_network_targets_host ON network_targets(host);
CREATE INDEX IF NOT EXISTS idx_network_targets_pid ON network_targets(pid);

CREATE TABLE IF NOT EXISTS llm_calls (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  conversation_id TEXT,
  start_timestamp_ms INTEGER NOT NULL,
  end_timestamp_ms INTEGER,
  pid INTEGER,
  comm TEXT,
  provider TEXT,
  model TEXT,
  call_kind TEXT,
  status TEXT NOT NULL DEFAULT 'observed',
  error_type TEXT,
  finish_reason TEXT,
  host TEXT,
  path TEXT,
  status_code INTEGER,
  request_body_json TEXT,
  response_body_json TEXT,
  view_source TEXT,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_time ON llm_calls(start_timestamp_ms);

CREATE TABLE IF NOT EXISTS token_usage (
  id TEXT PRIMARY KEY,
  llm_call_id TEXT,
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
  view_source TEXT,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_token_time ON token_usage(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_token_model_time ON token_usage(model, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_token_comm_time ON token_usage(comm, timestamp_ms);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS idx_audit_type_time ON audit_events(audit_type, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_audit_pid_time ON audit_events(pid, timestamp_ms);

CREATE TABLE IF NOT EXISTS process_nodes (
  id TEXT PRIMARY KEY,
  pid INTEGER NOT NULL,
  ppid INTEGER,
  root_pid INTEGER,
  start_timestamp_ms INTEGER,
  end_timestamp_ms INTEGER,
  comm TEXT,
  command TEXT,
  argv_json TEXT NOT NULL DEFAULT '[]',
  cwd TEXT,
  exit_code INTEGER,
  status TEXT,
  view_source TEXT NOT NULL,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_process_nodes_pid ON process_nodes(pid);
CREATE INDEX IF NOT EXISTS idx_process_nodes_parent ON process_nodes(ppid);

CREATE TABLE IF NOT EXISTS tool_calls (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  conversation_id TEXT,
  timestamp_ms INTEGER NOT NULL,
  start_timestamp_ms INTEGER,
  end_timestamp_ms INTEGER,
  duration_ms INTEGER,
  tool_name TEXT,
  tool_call_id TEXT,
  status TEXT,
  input_json TEXT,
  output_json TEXT,
  related_pid INTEGER,
  related_event_id TEXT,
  view_source TEXT NOT NULL,
  confidence REAL
);

CREATE INDEX IF NOT EXISTS idx_tool_time ON tool_calls(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_tool_name_time ON tool_calls(tool_name, timestamp_ms);

CREATE TABLE IF NOT EXISTS resource_samples (
  timestamp_ms INTEGER NOT NULL,
  pid INTEGER,
  comm TEXT,
  cpu_percent REAL,
  rss_mb INTEGER
);

"#;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn open_migrates_legacy_llm_calls_schema() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("legacy.db");
        {
            let conn = Connection::open(&db).unwrap();
            conn.execute_batch(
                r#"
                CREATE TABLE llm_calls (
                  id TEXT PRIMARY KEY,
                  start_timestamp_ms INTEGER NOT NULL,
                  end_timestamp_ms INTEGER,
                  pid INTEGER,
                  comm TEXT,
                  provider TEXT,
                  model TEXT,
                  host TEXT,
                  path TEXT,
                  status_code INTEGER,
                  request_body_json TEXT,
                  response_body_json TEXT,
                  view_source TEXT,
                  confidence REAL
                );
                INSERT INTO llm_calls (
                  id, start_timestamp_ms, end_timestamp_ms, pid, comm, provider, model,
                  host, path, status_code, request_body_json, response_body_json,
                  view_source, confidence
                ) VALUES (
                  'legacy-call', 1000, 1100, 42, 'agent', 'openai', 'gpt-test',
                  'api.openai.com', '/v1/chat/completions', 200, '{}', '{}',
                  'view', 0.75
                );
                "#,
            )
            .unwrap();
        }

        let store = SqliteStore::open(&db).unwrap();
        for column in [
            "session_id",
            "conversation_id",
            "call_kind",
            "status",
            "error_type",
            "finish_reason",
        ] {
            assert!(store.has_column("llm_calls", column), "{column}");
        }

        let calls = store.all_llm_call_rows().unwrap();
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].id, "legacy-call");
        assert_eq!(calls[0].status, "observed");
        assert_eq!(calls[0].session_id, None);
        assert_eq!(calls[0].conversation_id, None);
    }
}
