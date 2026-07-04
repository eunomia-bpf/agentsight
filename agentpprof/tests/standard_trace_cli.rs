use serde_json::Value;
use std::fs;
use std::process::Command;

#[test]
fn cli_exports_and_imports_standard_trace() {
    let tmp = tempfile::tempdir().unwrap();
    let trace_path = tmp.path().join("fixture-chrome-trace.json");
    let folded_path = tmp.path().join("fixture.folded");
    let fixture = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl"
    );
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let export = Command::new(binary)
        .args([
            "--project-root",
            env!("CARGO_MANIFEST_DIR"),
            "--project-name",
            "agentsight-public-fixture",
            "--session-file",
            fixture,
            "--export-standard-trace",
            trace_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        export.status.success(),
        "export failed: {}",
        String::from_utf8_lossy(&export.stderr)
    );
    let export_json: Value = serde_json::from_slice(&export.stdout).unwrap();
    assert_eq!(export_json["status"], "ok");
    assert_eq!(export_json["standard_trace_events"], 6);

    let import = Command::new(binary)
        .args([
            "--standard-trace-file",
            trace_path.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            "project,agent,op,phase,tool,status",
            "--format",
            "folded",
            "-o",
            folded_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        import.status.success(),
        "import failed: {}",
        String::from_utf8_lossy(&import.stderr)
    );
    let import_json: Value = serde_json::from_slice(&import.stdout).unwrap();
    assert_eq!(import_json["status"], "ok");
    assert_eq!(import_json["operations"], 6);

    let trace: Value = serde_json::from_str(&fs::read_to_string(trace_path).unwrap()).unwrap();
    assert_eq!(trace["metadata"]["format"], "chrome-trace-event-json");
    assert_eq!(trace["traceEvents"].as_array().unwrap().len(), 6);
    assert!(!fs::read_to_string(folded_path).unwrap().trim().is_empty());
}
