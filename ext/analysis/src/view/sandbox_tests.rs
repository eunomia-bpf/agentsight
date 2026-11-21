// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.
use super::*;
use crate::event::Event;
use crate::sinks::sqlite::SqliteStore;
use serde_json::json;

#[test]
fn sandbox_capture_snapshot_and_sqlite_export_agree() {
    let temp = tempfile::tempdir().unwrap();
    let db = temp.path().join("capture.db");
    let mut view = MaterializedView::new();
    view.add_sink(Box::new(SqliteStore::open(&db).unwrap()));
    let identity = json!({"id":"cgroup:42:pidns:100", "cgroup_id":42,
        "cgroup_path":"/tasks/build.scope", "pidns":100, "name":"build",
        "runtime":null,"image":null,"container_id":null});
    let mut send = |timestamp, pid, source: &str, mut data: Value| {
        data["timestamp"] = json!(timestamp);
        if source == "process" {
            data["sandbox"] = identity.clone();
        }
        view.ingest_event(&Event::new_with_timestamp(
            timestamp,
            source.to_string(),
            pid,
            "sh".to_string(),
            data,
        ))
        .unwrap();
    };
    send(
        1_000_000_000,
        42,
        "process",
        json!({"event":"EXEC", "pidns_pid":1, "full_command":"sh task", "filename":"sh"}),
    );
    send(
        1_100_000_000,
        43,
        "process",
        json!({"event":"EXEC", "pidns_pid":2, "ppid":42,"filename":"curl"}),
    );
    send(
        1_200_000_000,
        43,
        "process",
        json!({"event":"SUMMARY", "type":"NET_CONNECT", "detail":"127.0.0.1:443"}),
    );
    send(
        1_300_000_000,
        43,
        "http_parser",
        json!({"message_type":"request","method":"GET","host":"example.org","path":"/status","tid":43}),
    );
    send(
        1_400_000_000,
        43,
        "process",
        json!({"event":"EXIT", "pidns_pid":2,"exit_code":7}),
    );
    let before_exit = view.export_snapshot(SnapshotOptions { audit_limit: 100 });
    assert_eq!(before_exit.sandboxes.len(), 1);
    assert_eq!(
        before_exit.sandboxes[0].exit_code, None,
        "child exit must not end sandbox"
    );
    view.ingest_event(&Event::new_with_timestamp(
        2_000_000_000,
        "process".into(),
        42,
        "sh".into(),
        json!({"event":"EXIT","sandbox":identity,"pidns_pid":1,"exit_code":0}),
    ))
    .unwrap();
    let live = view.export_snapshot(SnapshotOptions { audit_limit: 100 });
    assert_eq!(live.schema_version, 1);
    assert_eq!(live.sandboxes[0].exit_code, Some(0));
    assert!(live.sandboxes[0].end_timestamp_ms.is_some());
    assert!(
        live.process_nodes
            .iter()
            .all(|p| p.sandbox_id.as_deref() == Some("cgroup:42:pidns:100"))
    );
    assert!(
        live.audit_events
            .iter()
            .filter(|e| e.audit_type == "network")
            .all(|e| e.sandbox_id.is_some())
    );
    assert_eq!(live.network_targets.len(), 1);
    assert!(
        live.audit_events
            .iter()
            .any(|e| e.action.as_deref() == Some("http_request"))
    );
    assert_eq!(
        live.network_targets[0].sandbox_id.as_deref(),
        Some("cgroup:42:pidns:100")
    );
    drop(view);
    let saved = crate::sources::sqlite::load_view(&db)
        .unwrap()
        .export_snapshot(SnapshotOptions { audit_limit: 100 });
    for (left, right) in [
        (json!(live.sandboxes), json!(saved.sandboxes)),
        (json!(live.process_nodes), json!(saved.process_nodes)),
        (json!(live.network_targets), json!(saved.network_targets)),
        (json!(live.audit_events), json!(saved.audit_events)),
    ] {
        assert_eq!(left, right);
    }
}

#[test]
fn old_recordings_read_without_sandbox_columns_and_upgrade_on_write() {
    let temp = tempfile::tempdir().unwrap();
    let db = temp.path().join("old.db");
    let store = SqliteStore::open(&db).unwrap();
    store
        .connection()
        .execute_batch(
            "DROP TABLE sandboxes;
        ALTER TABLE process_nodes DROP COLUMN sandbox_id;
        ALTER TABLE audit_events DROP COLUMN sandbox_id;
        ALTER TABLE network_targets DROP COLUMN sandbox_id;",
        )
        .unwrap();
    drop(store);
    let old = crate::sources::sqlite::load_view(&db)
        .unwrap()
        .export_snapshot(SnapshotOptions { audit_limit: 10 });
    assert!(old.sandboxes.is_empty());
    let upgraded = SqliteStore::open(&db).unwrap();
    assert!(upgraded.sandbox_rows().unwrap().is_empty());
    assert!(upgraded.process_node_rows().unwrap().is_empty());
    assert!(upgraded.network_target_rows().unwrap().is_empty());
    assert!(upgraded.all_audit_event_rows().unwrap().is_empty());
}

#[test]
fn summary_first_seen_and_http_last_seen_are_persisted() {
    let temp = tempfile::tempdir().unwrap();
    let db = temp.path().join("http.db");
    let mut view = MaterializedView::new();
    view.add_sink(Box::new(SqliteStore::open(&db).unwrap()));
    view.ingest_event(&Event::new_with_timestamp(
        5_000,
        "process".into(),
        42,
        "curl".into(),
        json!({
            "event":"SUMMARY", "type":"NET_CONNECT", "detail":"example.org:443",
            "timestamp":2_000_000, "first_timestamp":1_000_000,
            "sandbox":{"id":"test", "cgroup_id":42, "pidns":100}
        }),
    ))
    .unwrap();
    for (timestamp, message_type, status) in
        [(5_010, "request", None), (5_050, "response", Some(200))]
    {
        view.ingest_event(&Event::new_with_timestamp(timestamp, "http_parser".into(), 42, "curl".into(), json!({
            "message_type":message_type, "method":"GET", "host":"example.org", "path":"/health", "status_code":status
        }))).unwrap();
    }
    let live = view.export_snapshot(SnapshotOptions { audit_limit: 100 });
    assert_eq!(live.sandboxes[0].first_seen_ms, 4_999);
    assert_eq!(live.sandboxes[0].last_seen_ms, 5_050);
    let response = live
        .audit_events
        .iter()
        .find(|e| e.action.as_deref() == Some("http_response"))
        .unwrap();
    assert_eq!(response.status.as_deref(), Some("success"));
    assert_eq!(response.sandbox_id.as_deref(), Some("test"));
    drop(view);
    let saved = crate::sources::sqlite::load_view(&db)
        .unwrap()
        .export_snapshot(SnapshotOptions { audit_limit: 100 });
    assert_eq!(json!(live.sandboxes), json!(saved.sandboxes));
}
