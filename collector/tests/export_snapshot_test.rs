// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use rusqlite::Connection;
use serde_json::Value;
use std::process::Command;

fn run_agentsight(args: &[&str]) {
    let output = Command::new(env!("CARGO_BIN_EXE_agentsight"))
        .args(args)
        .output()
        .expect("agentsight command should run");
    assert!(
        output.status.success(),
        "agentsight {:?} failed\nstdout:\n{}\nstderr:\n{}",
        args,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn replay_no_adapters_skips_adapter_runs() {
    let temp = tempfile::tempdir().expect("tempdir");
    let db = temp.path().join("record.db");
    let fixture = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../docs/fixtures/sql-adapters/gemini-cli-basic/input.jsonl");

    run_agentsight(&[
        "db",
        "import",
        "--input",
        fixture.to_str().expect("fixture path"),
        "--db",
        db.to_str().expect("db path"),
        "--no-adapters",
    ]);

    let conn = Connection::open(db).expect("db should open");
    let adapter_runs: i64 = conn
        .query_row("SELECT COUNT(*) FROM adapter_runs", [], |row| row.get(0))
        .expect("adapter_runs query should work");
    let generic_tokens: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM token_usage",
            [],
            |row| row.get(0),
        )
        .expect("token query should work");

    assert_eq!(adapter_runs, 0);
    assert_eq!(generic_tokens, 15);
}

#[test]
fn replay_then_export_snapshot_for_static_web() {
    let temp = tempfile::tempdir().expect("tempdir");
    let db = temp.path().join("record.db");
    let snapshot = temp.path().join("trace.agentsight.json");
    let fixture = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../docs/fixtures/sql-adapters/gemini-cli-basic/input.jsonl");

    run_agentsight(&[
        "db",
        "import",
        "--input",
        fixture.to_str().expect("fixture path"),
        "--db",
        db.to_str().expect("db path"),
        "--adapter",
        "auto",
    ]);
    run_agentsight(&[
        "db",
        "export",
        "--db",
        db.to_str().expect("db path"),
        "--output",
        snapshot.to_str().expect("snapshot path"),
    ]);

    let data: Value =
        serde_json::from_slice(&std::fs::read(&snapshot).expect("snapshot should be written"))
            .expect("snapshot should be valid JSON");

    assert_eq!(data["schema_version"], 1);
    assert_eq!(data["summary"]["source"], "sqlite");
    assert_eq!(data["summary"]["total_tokens"], 15);
    assert_eq!(data["token_summary"][0]["group"], "gemini-2.5-pro");
    assert_eq!(data["token_summary"][0]["total_tokens"], 15);
    assert_eq!(data["events"].as_array().expect("events").len(), 2);
    assert_eq!(data["sessions"][0]["agent_type"], "gemini-cli");
    assert_eq!(data["sessions"][0]["total_tokens"], 15);
    assert_eq!(data["agents"][0]["agent_type"], "gemini-cli");
    assert!(
        data["interruptions"]
            .as_array()
            .expect("interruptions")
            .is_empty()
    );
}
