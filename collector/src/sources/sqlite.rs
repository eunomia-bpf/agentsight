// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::ViewResult;
use crate::sinks::sqlite::SqliteStore;
use crate::sources::agent_native;
use crate::view::MaterializedView;
use crate::view::llm::extract_prompt_text;
use serde_json::Value;
use std::path::Path;

pub(crate) fn load_view(path: impl AsRef<Path>) -> ViewResult<MaterializedView> {
    let store = SqliteStore::open_readonly(path)?;
    let mut view = MaterializedView::new();
    view.set_source("sqlite");

    if let Ok(rows) = store.all_llm_call_rows() {
        for row in rows {
            view.apply_llm_call(&row);
        }
    }
    if let Ok(rows) = store.token_usage_rows() {
        for row in rows {
            view.apply_token_usage(&row);
        }
    }
    let mut audit_rows = Vec::new();
    if let Ok(rows) = store.all_audit_event_rows() {
        let rows = rows
            .into_iter()
            .map(normalize_loaded_audit_event)
            .collect::<Vec<_>>();
        for row in &rows {
            view.apply_audit_event(row);
        }
        audit_rows = rows;
    }
    if let Ok(rows) = store.process_node_rows() {
        for row in rows {
            view.upsert_process_node(&row);
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
    agent_native::import_observed_session_logs(&mut view, &audit_rows);

    Ok(view)
}

fn normalize_loaded_audit_event(
    mut row: crate::model::AuditEventRow,
) -> crate::model::AuditEventRow {
    if row.audit_type == "llm" && row.action.as_deref() == Some("request") {
        if !row.details.is_object() {
            row.details = serde_json::json!({ "body": row.details });
        }
        let is_local = row.details.get("source").and_then(Value::as_str)
            == Some(crate::model::AGENT_NATIVE_SOURCE)
            || row.details.get("prompt_source").and_then(Value::as_str) == Some("local");
        if !is_local
            && row.details.get("prompt_source").is_none()
            && let Value::Object(map) = &mut row.details
        {
            map.insert(
                "prompt_source".to_string(),
                Value::String("ssl".to_string()),
            );
        }
        if row.details.get("text_content").is_none()
            && let Some(text) = extract_prompt_text(&row.details)
            && let Value::Object(map) = &mut row.details
        {
            map.insert("text_content".to_string(), Value::String(text));
        }
    }
    row
}
