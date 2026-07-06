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

#[test]
fn cli_exports_operation_file_as_standard_trace() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let trace_path = tmp.path().join("ops-chrome-trace.json");
    let direct_folded_path = tmp.path().join("direct.folded");
    let imported_folded_path = tmp.path().join("imported.folded");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    fs::write(
        &ops_path,
        [
            r#"{"value":1,"fields":{"project":"fixture","agent":"external","dataset":"web","session":"s1","task":"checkout","phase":"select","op":"action","action":"click","status":"ok"}}"#,
            r#"{"value":2,"fields":{"project":"fixture","agent":"external","dataset":"web","session":"s1","task":"checkout","phase":"input","op":"action","action":"type","status":"error"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","agent":"external","dataset":"web","session":"s2","task":"search","phase":"submit","op":"action","action":"click","status":"ok"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();

    let export = Command::new(binary)
        .args([
            "--project-name",
            "operation-fixture",
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--export-standard-trace",
            trace_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        export.status.success(),
        "operation export failed: {}",
        String::from_utf8_lossy(&export.stderr)
    );
    let export_json: Value = serde_json::from_slice(&export.stdout).unwrap();
    assert_eq!(export_json["status"], "ok");
    assert_eq!(export_json["operations"], 3);
    assert_eq!(export_json["standard_trace_events"], 3);

    let stack = "project,agent,dataset,task,phase,op,action,status";
    let direct = Command::new(binary)
        .args([
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            stack,
            "--format",
            "folded",
            "-o",
            direct_folded_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        direct.status.success(),
        "direct operation profile failed: {}",
        String::from_utf8_lossy(&direct.stderr)
    );

    let imported = Command::new(binary)
        .args([
            "--standard-trace-file",
            trace_path.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            stack,
            "--format",
            "folded",
            "-o",
            imported_folded_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        imported.status.success(),
        "operation trace import failed: {}",
        String::from_utf8_lossy(&imported.stderr)
    );
    let imported_json: Value = serde_json::from_slice(&imported.stdout).unwrap();
    assert_eq!(imported_json["status"], "ok");
    assert_eq!(imported_json["operations"], 3);

    let trace: Value = serde_json::from_str(&fs::read_to_string(trace_path).unwrap()).unwrap();
    assert_eq!(
        trace["metadata"]["source_schema"],
        "agentsight.operation.v1"
    );
    assert_eq!(trace["traceEvents"].as_array().unwrap().len(), 3);
    assert_eq!(
        fs::read_to_string(direct_folded_path).unwrap(),
        fs::read_to_string(imported_folded_path).unwrap()
    );
}

#[test]
fn profile_spec_imports_standard_trace_with_effective_args_flag() {
    let tmp = tempfile::tempdir().unwrap();
    let trace_path = tmp.path().join("generic-chrome-trace.json");
    let spec_path = tmp.path().join("standard-trace-profile-spec.json");
    let output_path = tmp.path().join("standard-trace-profile.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let trace = serde_json::json!({
        "traceEvents": [{
            "name": "tool:execute",
            "cat": "tool;execute",
            "ph": "X",
            "ts": 0,
            "dur": 10,
            "pid": 1,
            "tid": 2,
            "args": {
                "project": "trace-fixture",
                "agent": "external-agent",
                "session": "s1",
                "op": "tool",
                "phase": "execute",
                "tool": "browser",
                "status": "ok",
                "protocol": "mcp"
            }
        }]
    });
    fs::write(&trace_path, serde_json::to_vec_pretty(&trace).unwrap()).unwrap();

    let spec = serde_json::json!({
        "output": output_path,
        "format": "json",
        "view": "operations",
        "project_name": "fallback-project",
        "standard_trace_files": [trace_path],
        "include_standard_trace_args": true,
        "stack": "project,agent,session,op,phase,tool,protocol,status",
        "deterministic_output": true
    });
    fs::write(&spec_path, serde_json::to_vec_pretty(&spec).unwrap()).unwrap();

    let import = Command::new(binary)
        .args(["--profile-spec", spec_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(
        import.status.success(),
        "profile-spec standard trace import failed: {}\nstdout: {}",
        String::from_utf8_lossy(&import.stderr),
        String::from_utf8_lossy(&import.stdout)
    );
    let import_json: Value = serde_json::from_slice(&import.stdout).unwrap();
    assert_eq!(import_json["status"], "ok");
    assert_eq!(import_json["operations"], 1);
    assert_eq!(import_json["include_standard_trace_args"], true);
    assert_eq!(
        import_json["standard_trace_files"],
        serde_json::json!([trace_path])
    );

    let profile_json: Value =
        serde_json::from_str(&fs::read_to_string(&output_path).unwrap()).unwrap();
    assert_eq!(
        profile_json["profile"]["stacks"]["project:trace-fixture;agent:external-agent;session:s1;op:tool;phase:execute;tool:browser;protocol:mcp;status:ok"],
        1
    );
}
