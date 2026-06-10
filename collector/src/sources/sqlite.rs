// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{AuditEventRow, LlmCallRow, ProcessNodeRow, ViewResult};
use crate::sinks::sqlite::SqliteStore;
use crate::sources::agent_native;
use crate::text::truncate_text;
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
        let Some(text) = prompt_text_from_request(&row.request) else {
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
                "prompt": text,
                "prompt_source": "ssl",
                "prompt_sources": ["ssl"],
                "source": "ssl",
                "request": row.request,
                "provider": row.provider,
                "host": row.host,
                "path": row.path,
                "model": row.model,
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
        if !ssl_rows
            .iter()
            .any(|ssl| local_prompt_duplicates_ssl(&local, ssl))
        {
            ssl_rows.push(local);
        }
    }
}

fn local_prompt_duplicates_ssl(local: &AuditEventRow, ssl: &AuditEventRow) -> bool {
    if prompt_source(ssl) != Some("ssl") {
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
    if !models_match(local.subject.as_deref(), ssl.subject.as_deref()) {
        return false;
    }
    let Some(local_text) = prompt_text_from_details(&local.details) else {
        return false;
    };
    let Some(ssl_text) = prompt_text_from_details(&ssl.details) else {
        return false;
    };
    normalize_prompt_text_for_match(&local_text) == normalize_prompt_text_for_match(&ssl_text)
}

fn models_match(local: Option<&str>, ssl: Option<&str>) -> bool {
    matches!((local, ssl), (Some(local), Some(ssl)) if local == ssl)
}

fn prompt_source(row: &AuditEventRow) -> Option<&str> {
    row.details.get("prompt_source").and_then(Value::as_str)
}

fn normalize_prompt_text_for_match(text: &str) -> String {
    text.split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .to_ascii_lowercase()
}

fn prompt_text_from_details(details: &Value) -> Option<String> {
    details
        .get("text_content")
        .and_then(Value::as_str)
        .or_else(|| details.get("prompt").and_then(Value::as_str))
        .and_then(clean_prompt_text)
}

fn prompt_text_from_request(value: &Value) -> Option<String> {
    if let Some(prompt) = value.get("prompt").and_then(Value::as_str) {
        return clean_prompt_text(prompt);
    }
    let mut parts = Vec::new();
    for key in ["messages", "contents"] {
        if let Some(items) = value.get(key).and_then(Value::as_array) {
            for item in items {
                collect_prompt_text(item.get("content").unwrap_or(item), &mut parts);
            }
        }
    }
    clean_prompt_text(&parts.join(" "))
}

fn collect_prompt_text(value: &Value, out: &mut Vec<String>) {
    match value {
        Value::String(text) => out.push(text.clone()),
        Value::Array(items) => {
            for item in items {
                collect_prompt_text(item, out);
            }
        }
        Value::Object(obj) => {
            for key in ["text", "content", "parts"] {
                if let Some(value) = obj.get(key) {
                    collect_prompt_text(value, out);
                }
            }
        }
        _ => {}
    }
}

fn clean_prompt_text(text: &str) -> Option<String> {
    let mut text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if let Some(inner) = text
        .strip_prefix("<session>")
        .and_then(|text| text.strip_suffix("</session>"))
    {
        text = inner.trim().to_string();
    }
    (!text.is_empty()).then_some(text)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn keeps_local_prompt_when_ssl_text_matches_but_model_differs() {
        let ssl_rows = [ssl_call_row(
            "claude-haiku-4-5",
            "<session>\nRun the command.\n</session>",
        )];
        let mut prompt_rows = llm_call_prompt_rows(&ssl_rows);
        let local = local_prompt_row(
            "local-prompt",
            1_500,
            Some("claude-opus-4-6"),
            "Run the command.",
        );

        append_deduped_local_session_prompt_rows(&mut prompt_rows, vec![local]);

        assert_eq!(prompt_rows.len(), 2);
        assert_eq!(
            prompt_rows[0]
                .details
                .get("prompt_source")
                .and_then(Value::as_str),
            Some("ssl")
        );
        assert_eq!(
            prompt_rows[1]
                .details
                .get("prompt_source")
                .and_then(Value::as_str),
            Some("local")
        );
    }

    #[test]
    fn dedupes_local_prompt_when_ssl_has_same_model_and_text() {
        let ssl_rows = [ssl_call_row("claude-opus-4-6", "Run the command.")];
        let mut prompt_rows = llm_call_prompt_rows(&ssl_rows);
        let local = local_prompt_row(
            "local-prompt",
            1_500,
            Some("claude-opus-4-6"),
            "Run the command.",
        );

        append_deduped_local_session_prompt_rows(&mut prompt_rows, vec![local]);

        assert_eq!(prompt_rows.len(), 1);
        assert_eq!(
            prompt_rows[0]
                .details
                .get("text_content")
                .and_then(Value::as_str),
            Some("Run the command.")
        );
        assert_eq!(
            prompt_rows[0]
                .details
                .get("prompt_source")
                .and_then(Value::as_str),
            Some("ssl")
        );
    }

    #[test]
    fn keeps_local_prompt_when_either_model_is_missing() {
        let ssl_rows = [ssl_call_row("claude-opus-4-6", "Run the command.")];
        let mut prompt_rows = llm_call_prompt_rows(&ssl_rows);
        let local = local_prompt_row("local-prompt", 1_500, None, "Run the command.");

        append_deduped_local_session_prompt_rows(&mut prompt_rows, vec![local]);

        assert_eq!(prompt_rows.len(), 2);
    }

    fn ssl_call_row(model: &str, text: &str) -> LlmCallRow {
        LlmCallRow {
            id: "ssl-call".to_string(),
            start_timestamp_ms: 1_000,
            end_timestamp_ms: None,
            pid: Some(42),
            comm: Some("HTTP Client".to_string()),
            provider: Some("anthropic".to_string()),
            model: Some(model.to_string()),
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
            target: Some("/home/user/.claude/session.jsonl".to_string()),
            status: Some("observed".to_string()),
            summary: Some(text.to_string()),
            details: json!({
                "text_content": text,
                "prompt": text,
                "prompt_source": "local",
                "prompt_sources": ["local"]
            }),
        }
    }
}
