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
        let mut prompt_rows = llm_call_prompt_rows(&llm_rows);
        append_deduped_local_session_prompt_rows(
            &mut prompt_rows,
            agent_native::observed_session_prompt_rows(&audit_rows),
        );
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
