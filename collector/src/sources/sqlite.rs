// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{
    AuditEventRow, LlmCallRow, ProcessNodeRow, SessionRow, ToolCallRow, ViewResult, ViewSink,
};
use crate::sinks::sqlite::SqliteStore;
use crate::sources::agent_native;
use crate::text::{clean_prompt_text, extract_prompt_text, truncate_text};
use crate::view::MaterializedView;
use serde::Serialize;
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::path::Path;

const PROMPT_DEDUP_WINDOW_MS: u64 = 10_000;

#[derive(Debug, Clone, Serialize)]
pub(crate) struct ObservedEnvelopePersistResult {
    pub(crate) db: String,
    pub(crate) observed_prompt_rows: usize,
    pub(crate) envelopes: usize,
    pub(crate) sessions_written: usize,
    pub(crate) tool_calls_written: usize,
}
pub(crate) fn load_view(path: impl AsRef<Path>) -> ViewResult<MaterializedView> {
    load_view_inner(path, false)
}

pub(crate) fn load_view_with_observed_session_prompts(
    path: impl AsRef<Path>,
) -> ViewResult<MaterializedView> {
    load_view_inner(path, true)
}

fn load_view_inner(
    path: impl AsRef<Path>,
    include_observed_session_prompts: bool,
) -> ViewResult<MaterializedView> {
    let store = SqliteStore::open_readonly(path)?;
    let mut view = MaterializedView::new();
    view.set_source("sqlite");

    let mut llm_rows = Vec::new();
    if let Ok(rows) = store.all_llm_call_rows() {
        for row in &rows {
            view.apply_llm_call(row);
        }
        llm_rows = rows;
    }
    if let Ok(rows) = store.token_usage_rows() {
        for row in rows {
            view.apply_token_usage(&row);
        }
    }
    let mut audit_rows = Vec::new();
    if let Ok(rows) = store.all_audit_event_rows() {
        for row in &rows {
            if include_observed_session_prompts && is_reprojected_llm_request(row) {
                continue;
            }
            view.apply_audit_event(row);
        }
        audit_rows = rows;
    }
    let mut process_pids = BTreeSet::new();
    let mut process_rows = Vec::new();
    if let Ok(rows) = store.process_node_rows() {
        for row in &rows {
            process_pids.insert(row.pid);
            view.upsert_process_node(row);
        }
        process_rows = rows;
    }
    if let Ok(rows) = store.session_rows() {
        for row in rows {
            view.upsert_session(&row);
        }
    }
    if let Ok(rows) = store.tool_call_rows() {
        for row in rows {
            view.apply_tool_call(&row);
        }
    }
    if let Ok(rows) = store.network_target_rows() {
        for row in rows {
            view.upsert_network_target(&row);
        }
    }
    if let Ok(rows) = store.resource_sample_rows() {
        for row in rows {
            view.apply_resource_sample(&row);
        }
    }
    if include_observed_session_prompts {
        import_observed_process_nodes(&mut view, &llm_rows, &process_pids);
        let mut prompt_rows = llm_call_prompt_rows(&llm_rows);
        let local_prompt_rows = agent_native::observed_session_prompt_rows(&audit_rows);
        append_deduped_local_session_prompt_rows(&mut prompt_rows, local_prompt_rows.clone());
        for row in prompt_rows {
            view.apply_audit_event(&row);
        }
        import_observed_agent_envelopes(&mut view, &audit_rows, &process_rows, &local_prompt_rows);
    }

    Ok(view)
}

pub(crate) fn persist_observed_agent_envelopes(
    path: impl AsRef<Path>,
) -> ViewResult<ObservedEnvelopePersistResult> {
    let path = path.as_ref();
    let mut store = SqliteStore::open(path)?;
    let audit_rows = store.all_audit_event_rows()?;
    let process_rows = store.process_node_rows().unwrap_or_default();
    let local_prompt_rows = agent_native::observed_session_prompt_rows(&audit_rows);
    let envelopes = observed_agent_envelopes(&audit_rows, &process_rows, &local_prompt_rows);
    for (session, tool) in &envelopes {
        store.session(session)?;
        store.tool_call(tool)?;
    }
    Ok(ObservedEnvelopePersistResult {
        db: path.to_string_lossy().to_string(),
        observed_prompt_rows: local_prompt_rows.len(),
        envelopes: envelopes.len(),
        sessions_written: envelopes.len(),
        tool_calls_written: envelopes.len(),
    })
}

fn import_observed_process_nodes(
    view: &mut MaterializedView,
    llm_rows: &[LlmCallRow],
    existing_pids: &BTreeSet<u32>,
) {
    for row in llm_rows {
        let Some(pid) = row.pid else {
            continue;
        };
        if existing_pids.contains(&pid) {
            continue;
        }
        let comm = row.comm.clone();
        let command = comm.clone().unwrap_or_else(|| format!("pid {}", pid));
        view.upsert_process_node(&ProcessNodeRow {
            id: format!("process-{}-observed", pid),
            pid,
            ppid: None,
            root_pid: Some(pid),
            start_timestamp_ms: Some(row.start_timestamp_ms),
            end_timestamp_ms: None,
            comm,
            command: Some(command),
            argv: Vec::new(),
            cwd: None,
            exit_code: None,
            status: Some("observed".to_string()),
            view_source: "sqlite".to_string(),
            confidence: Some(0.5),
        });
    }
}

fn is_reprojected_llm_request(row: &AuditEventRow) -> bool {
    row.audit_type == "llm" && row.action.as_deref() == Some("request")
}

fn llm_call_prompt_rows(rows: &[LlmCallRow]) -> Vec<AuditEventRow> {
    let mut prompts = Vec::new();
    for row in rows {
        if row.request.is_null() || row.request.as_object().is_some_and(|obj| obj.is_empty()) {
            continue;
        }
        let Some(text) = extract_prompt_text(&row.request) else {
            continue;
        };
        prompts.push(AuditEventRow {
            id: format!("audit-{}-request", row.id),
            timestamp_ms: row.start_timestamp_ms,
            audit_type: "llm".to_string(),
            pid: row.pid,
            comm: row.comm.clone(),
            subject: row.model.clone(),
            action: Some("request".to_string()),
            target: row.host.clone(),
            status: Some("observed".to_string()),
            summary: Some(truncate_text(&text, 160)),
            details: json!({
                "text_content": text,
                "prompt_source": "ssl",
                "request": row.request,
                "provider": row.provider,
                "path": row.path,
            }),
        });
    }
    prompts
}

fn append_deduped_local_session_prompt_rows(
    ssl_rows: &mut Vec<AuditEventRow>,
    local_rows: Vec<AuditEventRow>,
) {
    for local in local_rows {
        let Some(local_text) = prompt_text_from_details(&local.details) else {
            ssl_rows.push(local);
            continue;
        };
        let duplicate = ssl_rows.iter().any(|ssl| {
            if ssl.details.get("prompt_source").and_then(Value::as_str) != Some("ssl") {
                return false;
            }
            if let (Some(local_pid), Some(ssl_pid)) = (local.pid, ssl.pid)
                && local_pid != ssl_pid
            {
                return false;
            }
            if local.timestamp_ms.abs_diff(ssl.timestamp_ms) > PROMPT_DEDUP_WINDOW_MS {
                return false;
            }
            let Some((local_model, ssl_model)) =
                local.subject.as_deref().zip(ssl.subject.as_deref())
            else {
                return false;
            };
            let Some(ssl_text) = prompt_text_from_details(&ssl.details) else {
                return false;
            };
            local_model == ssl_model && local_text.eq_ignore_ascii_case(&ssl_text)
        });
        if !duplicate {
            ssl_rows.push(local);
        }
    }
}

fn prompt_text_from_details(details: &Value) -> Option<String> {
    details
        .get("text_content")
        .and_then(Value::as_str)
        .or_else(|| details.get("prompt").and_then(Value::as_str))
        .and_then(clean_prompt_text)
}

fn import_observed_agent_envelopes(
    view: &mut MaterializedView,
    audit_rows: &[AuditEventRow],
    process_rows: &[ProcessNodeRow],
    prompt_rows: &[AuditEventRow],
) {
    for (session, tool) in observed_agent_envelopes(audit_rows, process_rows, prompt_rows) {
        view.upsert_session(&session);
        view.apply_tool_call(&tool);
    }
}

fn observed_agent_envelopes(
    audit_rows: &[AuditEventRow],
    process_rows: &[ProcessNodeRow],
    prompt_rows: &[AuditEventRow],
) -> Vec<(SessionRow, ToolCallRow)> {
    let mut envelopes = Vec::new();
    for prompt in prompt_rows {
        let Some(prompt_text) = prompt_text_from_details(&prompt.details) else {
            continue;
        };
        let Some(source_event) = source_event_for_prompt(prompt, audit_rows) else {
            continue;
        };
        let process = process_for_event(source_event, process_rows);
        let start = process
            .and_then(|row| row.start_timestamp_ms)
            .unwrap_or(prompt.timestamp_ms);
        let end = process.and_then(|row| row.end_timestamp_ms);
        let pid = source_event.pid.or(prompt.pid);
        let agent = prompt
            .details
            .get("agent")
            .and_then(Value::as_str)
            .map(ToString::to_string)
            .or_else(|| prompt.comm.clone())
            .unwrap_or_else(|| "agent".to_string());
        let session_id = prompt
            .details
            .get("session_id")
            .and_then(Value::as_str)
            .map(sanitize_observed_id)
            .unwrap_or_else(|| {
                format!(
                    "observed:{}:{}:{}",
                    sanitize_observed_id(&agent),
                    pid.unwrap_or(0),
                    prompt.timestamp_ms
                )
            });
        let tool_id = format!("{session_id}:agent-run");

        let session = SessionRow {
            id: session_id.clone(),
            agent_type: agent.clone(),
            start_timestamp_ms: start,
            end_timestamp_ms: end,
            status: "observed".to_string(),
            model: prompt.subject.clone(),
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            view_source: "sqlite_observed_agent_envelope".to_string(),
            confidence: Some(0.65),
            attributes: json!({
                "prompt_preview": truncate_text(&prompt_text, 160),
                "prompt_source": prompt.details.get("prompt_source").cloned().unwrap_or(Value::Null),
                "root_pid": pid,
                "source_event_id": source_event.id,
            }),
        };
        let tool = ToolCallRow {
            id: tool_id.clone(),
            session_id: Some(session_id),
            conversation_id: None,
            timestamp_ms: start,
            tool_name: Some("agent-run".to_string()),
            tool_call_id: Some(tool_id),
            start_timestamp_ms: Some(start),
            end_timestamp_ms: end,
            duration_ms: end.map(|end| end.saturating_sub(start)),
            status: Some("observed".to_string()),
            input: json!({
                "prompt_preview": truncate_text(&prompt_text, 160),
                "prompt_source": prompt.details.get("prompt_source").cloned().unwrap_or(Value::Null),
                "prompt_tag": "observed",
            }),
            output: json!({}),
            related_pid: pid,
            related_event_id: Some(source_event.id.clone()),
            view_source: "sqlite_observed_agent_envelope".to_string(),
            confidence: Some(0.65),
        };
        envelopes.push((session, tool));
    }
    envelopes
}

fn source_event_for_prompt<'a>(
    prompt: &AuditEventRow,
    audit_rows: &'a [AuditEventRow],
) -> Option<&'a AuditEventRow> {
    audit_rows.iter().find(|row| {
        row.timestamp_ms == prompt.timestamp_ms
            && row.pid == prompt.pid
            && row.target == prompt.target
            && matches!(
                (row.audit_type.as_str(), row.action.as_deref()),
                ("process", Some("exec")) | ("file", _)
            )
    })
}

fn process_for_event<'a>(
    event: &AuditEventRow,
    process_rows: &'a [ProcessNodeRow],
) -> Option<&'a ProcessNodeRow> {
    let pid = event.pid?;
    process_rows.iter().find(|process| {
        process.pid == pid
            && process
                .start_timestamp_ms
                .map_or(true, |start| event.timestamp_ms >= start)
            && process
                .end_timestamp_ms
                .map_or(true, |end| event.timestamp_ms <= end)
    })
}

fn sanitize_observed_id(value: &str) -> String {
    let value = value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || matches!(ch, ':' | '-' | '_' | '.') {
                ch
            } else {
                '-'
            }
        })
        .collect::<String>()
        .trim_matches('-')
        .to_string();
    if value.is_empty() {
        "unknown".to_string()
    } else {
        value
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn dedupes_local_prompt_only_when_ssl_matches_model_and_text() {
        for (name, local_model, local_details, expected_rows) in [
            (
                "same model and text",
                Some("claude-opus-4-6"),
                json!({"text_content": "Run the command.", "prompt_source": "local"}),
                1,
            ),
            (
                "legacy prompt field",
                Some("claude-opus-4-6"),
                json!({"prompt": "Run the command.", "prompt_source": "local"}),
                1,
            ),
            (
                "different model",
                Some("claude-haiku-4-5"),
                json!({"text_content": "Run the command.", "prompt_source": "local"}),
                2,
            ),
            (
                "missing model",
                None,
                json!({"text_content": "Run the command.", "prompt_source": "local"}),
                2,
            ),
        ] {
            let ssl_rows = [ssl_call_row("claude-opus-4-6", "Run the command.")];
            let mut prompt_rows = llm_call_prompt_rows(&ssl_rows);
            let mut local =
                local_prompt_row("local-prompt", 1_500, local_model, "Run the command.");
            local.details = local_details;

            append_deduped_local_session_prompt_rows(&mut prompt_rows, vec![local]);

            assert_eq!(prompt_rows.len(), expected_rows, "{name}");
        }
    }

    #[test]
    fn observed_local_prompt_exports_agent_run_envelope() {
        let mut view = MaterializedView::new();
        let audit_rows = vec![AuditEventRow {
            id: "exec-codex".to_string(),
            timestamp_ms: 1_000,
            audit_type: "process".to_string(),
            pid: Some(42),
            comm: Some("codex".to_string()),
            subject: None,
            action: Some("exec".to_string()),
            target: Some("/usr/bin/codex".to_string()),
            status: Some("observed".to_string()),
            summary: Some("codex exec Fix tests".to_string()),
            details: json!({"full_command": "codex exec Fix tests"}),
        }];
        let process_rows = vec![ProcessNodeRow {
            id: "process-42".to_string(),
            pid: 42,
            ppid: None,
            root_pid: Some(42),
            start_timestamp_ms: Some(900),
            end_timestamp_ms: Some(2_000),
            comm: Some("codex".to_string()),
            command: Some("codex exec Fix tests".to_string()),
            argv: Vec::new(),
            cwd: None,
            exit_code: None,
            status: Some("observed".to_string()),
            view_source: "sqlite".to_string(),
            confidence: Some(1.0),
        }];
        let prompt_rows = vec![AuditEventRow {
            id: "audit-codex-exec-prompt-1000-42".to_string(),
            timestamp_ms: 1_000,
            audit_type: "llm".to_string(),
            pid: Some(42),
            comm: Some("codex".to_string()),
            subject: Some("local".to_string()),
            action: Some("request".to_string()),
            target: Some("/usr/bin/codex".to_string()),
            status: Some("observed".to_string()),
            summary: Some("Fix tests".to_string()),
            details: json!({
                "text_content": "Fix tests",
                "prompt_source": "local",
            }),
        }];

        import_observed_agent_envelopes(&mut view, &audit_rows, &process_rows, &prompt_rows);
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 10 });

        assert_eq!(snapshot.sessions.len(), 1);
        assert_eq!(snapshot.sessions[0].agent_type, "codex");
        assert_eq!(snapshot.sessions[0].start_timestamp_ms, 900);
        assert_eq!(snapshot.sessions[0].end_timestamp_ms, Some(2_000));
        assert_eq!(snapshot.tool_calls.len(), 1);
        assert_eq!(
            snapshot.tool_calls[0].session_id,
            Some(snapshot.sessions[0].id.clone())
        );
        assert_eq!(
            snapshot.tool_calls[0].tool_name.as_deref(),
            Some("agent-run")
        );
        assert_eq!(snapshot.tool_calls[0].related_pid, Some(42));
        assert_eq!(
            snapshot.tool_calls[0].related_event_id.as_deref(),
            Some("exec-codex")
        );
        assert_eq!(
            snapshot.tool_calls[0]
                .input
                .get("prompt_tag")
                .and_then(Value::as_str),
            Some("observed")
        );
    }

    #[test]
    fn persist_observed_agent_envelopes_writes_session_rows_to_sqlite() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("observed-envelope.db");
        let store = SqliteStore::open(&db).unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, subject, action, target, status, summary, details_json
                 ) VALUES (
                    'exec-codex', 1000, 'process', 42, 'codex', NULL, 'exec',
                    '/usr/bin/codex', 'observed', 'codex exec Fix tests',
                    '{\"full_command\":\"codex exec Fix tests\"}'
                 )",
                [],
            )
            .unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO process_nodes (
                    id, pid, ppid, root_pid, start_timestamp_ms, end_timestamp_ms,
                    comm, command, argv_json, cwd, exit_code, status, view_source, confidence
                 ) VALUES (
                    'process-42', 42, NULL, 42, 900, 2000,
                    'codex', 'codex exec Fix tests', '[]', NULL, NULL,
                    'observed', 'test', 1.0
                 )",
                [],
            )
            .unwrap();
        drop(store);

        let result = persist_observed_agent_envelopes(&db).unwrap();
        assert_eq!(result.observed_prompt_rows, 1);
        assert_eq!(result.sessions_written, 1);
        assert_eq!(result.tool_calls_written, 1);

        let store = SqliteStore::open_readonly(&db).unwrap();
        let sessions = store.session_rows().unwrap();
        let tools = store.tool_call_rows().unwrap();
        assert_eq!(sessions.len(), 1);
        assert_eq!(sessions[0].id, "observed:codex:42:1000");
        assert_eq!(sessions[0].view_source, "sqlite_observed_agent_envelope");
        assert_eq!(tools.len(), 1);
        assert_eq!(
            tools[0].session_id.as_deref(),
            Some(sessions[0].id.as_str())
        );
        assert_eq!(tools[0].related_event_id.as_deref(), Some("exec-codex"));
    }

    fn ssl_call_row(model: &str, text: &str) -> LlmCallRow {
        LlmCallRow {
            id: "ssl-call".to_string(),
            session_id: None,
            conversation_id: None,
            start_timestamp_ms: 1_000,
            end_timestamp_ms: None,
            pid: Some(42),
            comm: Some("HTTP Client".to_string()),
            provider: Some("anthropic".to_string()),
            model: Some(model.to_string()),
            call_kind: Some("messages".to_string()),
            status: "pending".to_string(),
            error_type: None,
            finish_reason: None,
            host: Some("api.anthropic.com".to_string()),
            path: Some("/v1/messages".to_string()),
            status_code: None,
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            request: json!({
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text
                            }
                        ]
                    }
                ]
            }),
            response: Value::Null,
        }
    }

    fn local_prompt_row(
        id: &str,
        timestamp_ms: u64,
        model: Option<&str>,
        text: &str,
    ) -> AuditEventRow {
        AuditEventRow {
            id: id.to_string(),
            timestamp_ms,
            audit_type: "llm".to_string(),
            pid: Some(42),
            comm: Some("claude".to_string()),
            subject: model.map(ToString::to_string),
            action: Some("request".to_string()),
            target: agent_session::fixture_session_path(
                agent_session::AGENT_CLAUDE,
                std::path::Path::new("/home/user"),
            )
            .map(|path| path.to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: Some(text.to_string()),
            details: json!({
                "text_content": text,
                "prompt_source": "local"
            }),
        }
    }
}
