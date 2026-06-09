// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{AuditEventRow, LlmCallRow, ProcessNodeRow, ViewResult};
use crate::sinks::sqlite::SqliteStore;
use crate::sources::agent_native;
use crate::view::MaterializedView;
use std::collections::BTreeSet;
use std::path::Path;

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
        import_llm_call_prompts(&mut view, &llm_rows);
        agent_native::import_observed_session_prompts(&mut view, &audit_rows);
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

fn import_llm_call_prompts(view: &mut MaterializedView, rows: &[LlmCallRow]) {
    for row in rows {
        if row.request.is_null() || row.request.as_object().is_some_and(|obj| obj.is_empty()) {
            continue;
        }
        view.apply_audit_event(&AuditEventRow {
            id: format!("audit-{}-request", row.id),
            timestamp_ms: row.start_timestamp_ms,
            audit_type: "llm".to_string(),
            pid: row.pid,
            comm: row.comm.clone(),
            subject: row.model.clone(),
            action: Some("request".to_string()),
            target: row.host.clone(),
            status: Some("observed".to_string()),
            summary: Some("LLM request".to_string()),
            details: row.request.clone(),
        });
    }
}
