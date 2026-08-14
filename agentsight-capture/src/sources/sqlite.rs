// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{AuditEventRow, LlmCallRow, ProcessNodeRow, ViewResult};
use crate::sinks::sqlite::SqliteStore;
use crate::sources::agent_native;
use crate::text::{clean_prompt_text, extract_prompt_text, truncate_text};
use crate::view::MaterializedView;
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::path::Path;

const PROMPT_DEDUP_WINDOW_MS: u64 = 10_000;
#[cfg_attr(not(test), allow(dead_code))]
pub fn load_view(path: impl AsRef<Path>) -> ViewResult<MaterializedView> {
    load_view_inner(path, false)
}

pub fn load_view_with_observed_session_prompts(
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
    if let Ok(rows) = store.process_node_rows() {
        for row in &rows {
            process_pids.insert(row.pid);
            view.upsert_process_node(row);
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
        let observed_sessions = agent_native::observed_sessions_from_audit_rows(&audit_rows);
        agent_native::import_into_view(&mut view, &observed_sessions);
        let current_llm_rows = view.llm_call_rows(usize::MAX);
        let mut prompt_rows = llm_call_prompt_rows(&current_llm_rows);
        let mut local_prompt_rows = agent_native::observed_session_prompt_rows(&audit_rows);
        local_prompt_rows.sort_by_key(|row| {
            row.details
                .get("session_id")
                .and_then(Value::as_str)
                .is_none()
        });
        append_deduped_local_session_prompt_rows(&mut prompt_rows, local_prompt_rows);
        for row in local_prompt_llm_call_rows(&prompt_rows) {
            view.apply_llm_call(&row);
        }
        for row in prompt_rows {
            view.apply_audit_event(&row);
        }
    }

    Ok(view)
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
            // Inferred from an LLM call's pid, never observed at exec.
            start_ticks: None,
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
        let is_agent_native = row.request.get("prompt_source").and_then(Value::as_str)
            == Some(crate::model::AGENT_NATIVE_SOURCE);
        let prompt_source = if is_agent_native { "local" } else { "ssl" };
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
                "prompt_source": prompt_source,
                "session_id": row.request.get("session_id").and_then(Value::as_str),
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
            let source = ssl.details.get("prompt_source").and_then(Value::as_str);
            let is_session_bound_local = source == Some("local")
                && ssl
                    .details
                    .get("session_id")
                    .and_then(Value::as_str)
                    .is_some();
            if source != Some("ssl") && !is_session_bound_local {
                return false;
            }
            if let (Some(local_pid), Some(ssl_pid)) = (local.pid, ssl.pid)
                && local_pid != ssl_pid
            {
                return false;
            }
            if !is_session_bound_local
                && local.timestamp_ms.abs_diff(ssl.timestamp_ms) > PROMPT_DEDUP_WINDOW_MS
            {
                return false;
            }
            if let (Some(local_model), Some(ssl_model)) =
                (local.subject.as_deref(), ssl.subject.as_deref())
                && local_model != ssl_model
            {
                return false;
            }
            let Some(ssl_text) = prompt_text_from_details(&ssl.details) else {
                return false;
            };
            prompt_texts_match_or_truncated(&local_text, &ssl_text)
        });
        if !duplicate {
            ssl_rows.push(local);
        }
    }
}

fn prompt_texts_match_or_truncated(left: &str, right: &str) -> bool {
    if left.eq_ignore_ascii_case(right) {
        return true;
    }
    let min_len = left.len().min(right.len());
    if min_len < 48 {
        return false;
    }
    let left_lower = left.to_ascii_lowercase();
    let right_lower = right.to_ascii_lowercase();
    left_lower.starts_with(&right_lower) || right_lower.starts_with(&left_lower)
}

fn local_prompt_llm_call_rows(prompt_rows: &[AuditEventRow]) -> Vec<LlmCallRow> {
    prompt_rows
        .iter()
        .filter(|row| {
            row.details.get("prompt_source").and_then(Value::as_str) == Some("local")
                && row
                    .details
                    .get("session_id")
                    .and_then(Value::as_str)
                    .is_none()
                && row.audit_type == "llm"
                && row.action.as_deref() == Some("request")
        })
        .filter_map(local_prompt_llm_call_row)
        .collect()
}

fn local_prompt_llm_call_row(row: &AuditEventRow) -> Option<LlmCallRow> {
    let text = prompt_text_from_details(&row.details)?;
    let session_id = row
        .details
        .get("session_id")
        .and_then(Value::as_str)
        .map(ToString::to_string);
    let conversation_id = row
        .details
        .get("conversation_id")
        .and_then(Value::as_str)
        .map(ToString::to_string);
    Some(LlmCallRow {
        id: format!("llm-{}", row.id),
        session_id,
        conversation_id,
        start_timestamp_ms: row.timestamp_ms,
        end_timestamp_ms: None,
        pid: row.pid,
        comm: row.comm.clone(),
        provider: None,
        model: row.subject.clone().or_else(|| row.comm.clone()),
        call_kind: Some("agent_native_prompt".to_string()),
        status: row.status.clone().unwrap_or_else(|| "observed".to_string()),
        error_type: None,
        finish_reason: None,
        host: None,
        path: row.target.clone(),
        status_code: None,
        input_tokens: 0,
        output_tokens: 0,
        total_tokens: 0,
        request: json!({
            "prompt": text,
            "prompt_source": "local",
            "target": row.target.as_deref(),
        }),
        response: Value::Null,
    })
}

fn prompt_text_from_details(details: &Value) -> Option<String> {
    details
        .get("text_content")
        .and_then(Value::as_str)
        .or_else(|| details.get("prompt").and_then(Value::as_str))
        .and_then(clean_prompt_text)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::ViewSink;
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
                1,
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
    fn prompt_text_dedupe_accepts_truncated_prefix() {
        assert!(prompt_texts_match_or_truncated(
            "Reply with exactly: agentsight-codex-ignore-user-c",
            "Reply with exactly: agentsight-codex-ignore-user-config",
        ));
        assert!(!prompt_texts_match_or_truncated(
            "Reply with exactly: agentsight-codex-",
            "Reply with exactly: agentsight-codex-real-smoke",
        ));
    }

    #[test]
    fn observed_codex_exec_prompt_reprojects_as_llm_call() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("codex.db");
        let store = SqliteStore::open(&db).unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES (
                    'audit-1', 1000, 'process', 42, 'codex', 'exec', '/tmp/tools/bin/codex',
                    'observed',
                    '{\"full_command\":\"/tmp/tools/bin/codex exec --skip-git-repo-check -c model=gpt agentsight local codex prompt\"}'
                 )",
                [],
            )
            .unwrap();

        let view = load_view_with_observed_session_prompts(&db).unwrap();
        let rows = view.llm_call_rows(10);

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].comm.as_deref(), Some("codex"));
        assert_eq!(
            rows[0].request.get("prompt").and_then(Value::as_str),
            Some("agentsight local codex prompt")
        );
    }

    #[test]
    fn codex_exec_prompt_dedupes_against_ssl_row_without_local_model() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("codex.db");
        let mut store = SqliteStore::open(&db).unwrap();
        store
            .llm_call(&ssl_call_row(
                "gpt-agentsight-mock",
                "agentsight local codex prompt",
            ))
            .unwrap();
        store
            .audit_event(&AuditEventRow {
                id: "audit-1".to_string(),
                timestamp_ms: 1_500,
                audit_type: "process".to_string(),
                pid: Some(42),
                comm: Some("codex".to_string()),
                subject: None,
                action: Some("exec".to_string()),
                target: Some("/tmp/tools/bin/codex".to_string()),
                status: Some("observed".to_string()),
                summary: None,
                details: json!({
                    "full_command": concat!(
                        "/tmp/tools/bin/codex exec --skip-git-repo-check ",
                        "-c model=gpt agentsight local codex prompt"
                    ),
                }),
            })
            .unwrap();
        drop(store);

        let view = load_view_with_observed_session_prompts(&db).unwrap();
        let rows = view.llm_call_rows(10);
        let prompts = view.audit_rows(Some("llm"), 10);

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].id, "ssl-call");
        assert_eq!(prompts.len(), 1);
        assert_eq!(
            prompts[0]
                .details
                .get("prompt_source")
                .and_then(Value::as_str),
            Some("ssl")
        );
    }

    #[test]
    fn observed_codex_home_reprojects_session_prompt_as_llm_call() {
        let temp = tempfile::tempdir().unwrap();
        let state_path = write_codex_home(temp.path(), "agentsight inferred codex home prompt");
        let db = temp.path().join("codex.db");
        let store = SqliteStore::open(&db).unwrap();
        insert_exec_event(
            &store,
            current_epoch_ms(),
            "/usr/bin/codex exec --skip-git-repo-check agentsight inferred codex home prompt",
        );
        insert_file_event(&store, current_epoch_ms() + 100, &state_path);

        let view = load_view_with_observed_session_prompts(&db).unwrap();
        let rows = view.llm_call_rows(10);
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 10 });

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].comm.as_deref(), Some("codex"));
        assert_eq!(
            rows[0].request.get("prompt").and_then(Value::as_str),
            Some("agentsight inferred codex home prompt")
        );
        assert_eq!(snapshot.sessions.len(), 1);
    }

    #[test]
    fn observed_codex_home_without_exec_prompt_does_not_import_sessions() {
        let temp = tempfile::tempdir().unwrap();
        let state_path = write_codex_home(temp.path(), "agentsight unrelated codex home prompt");
        let db = temp.path().join("codex.db");
        let store = SqliteStore::open(&db).unwrap();
        insert_file_event(&store, current_epoch_ms(), &state_path);

        let view = load_view_with_observed_session_prompts(&db).unwrap();

        assert!(view.llm_call_rows(10).is_empty());
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

    fn current_epoch_ms() -> u64 {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }

    fn write_codex_home(root: &std::path::Path, prompt: &str) -> std::path::PathBuf {
        let codex_home = root.join("codex-home");
        let session_dir = codex_home.join("sessions/2026/07/11");
        std::fs::create_dir_all(&session_dir).unwrap();
        std::fs::write(
            session_dir.join("rollout-2026-07-11T00-00-00.jsonl"),
            format!(
                "{{\"timestamp\":\"2026-07-11T00:00:00.000Z\",\
                 \"type\":\"event_msg\",\
                 \"payload\":{{\"type\":\"user_message\",\"message\":\"{prompt}\"}}}}\n"
            ),
        )
        .unwrap();
        let state_path = codex_home.join("stat");
        std::fs::write(&state_path, "").unwrap();
        state_path
    }

    fn insert_exec_event(store: &SqliteStore, timestamp_ms: u64, full_command: &str) {
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES (
                    'audit-exec-1', ?1, 'process', 42, 'codex', 'exec', '/usr/bin/codex',
                    'observed', ?2
                 )",
                rusqlite::params![
                    timestamp_ms,
                    json!({"full_command": full_command}).to_string()
                ],
            )
            .unwrap();
    }

    fn insert_file_event(store: &SqliteStore, timestamp_ms: u64, path: &std::path::Path) {
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES (
                    'audit-file-1', ?1, 'file', 42, 'codex', 'write', ?2, 'observed', ?3
                 )",
                rusqlite::params![
                    timestamp_ms,
                    path.to_string_lossy().as_ref(),
                    json!({"filepath": path.to_string_lossy()}).to_string(),
                ],
            )
            .unwrap();
    }
}
