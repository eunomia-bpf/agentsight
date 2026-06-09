// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::ViewResult;
use crate::sinks::sqlite::SqliteStore;
use crate::view::MaterializedView;
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
    if let Ok(rows) = store.all_audit_event_rows() {
        for row in rows {
            view.apply_audit_event(&row);
        }
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

    Ok(view)
}
