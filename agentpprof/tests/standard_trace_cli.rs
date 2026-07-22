use serde_json::Value;
use std::fs;
use std::process::Command;

#[test]
fn cli_imports_standard_trace_into_one_pprof() {
    let tmp = tempfile::tempdir().unwrap();
    let trace_path = tmp.path().join("generic-chrome-trace.json");
    let output_path = tmp.path().join("standard-trace.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &trace_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "traceEvents": [{
                "name": "tool:execute",
                "cat": "tool;execute",
                "ph": "X",
                "ts": 1000,
                "dur": 500,
                "pid": 7,
                "tid": 9,
                "args": {"task":"verify","tool":"shell","status":"ok","custom":"visible"}
            }]
        }))
        .unwrap(),
    )
    .unwrap();

    let output = Command::new(binary)
        .args([
            "--standard-trace-file",
            trace_path.to_str().unwrap(),
            "--include-standard-trace-args",
            "--view",
            "operations",
            "--stack",
            "project,task,op,phase,tool,status,custom",
            "--output",
            output_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "import failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["status"], "ok");
    assert_eq!(status["format"], "pprof");
    assert_eq!(status["operations"], 1);
    assert_eq!(status["include_standard_trace_args"], true);
    let bytes = fs::read(output_path).unwrap();
    assert_eq!(&bytes[..2], &[0x1f, 0x8b]);
}

#[test]
fn trace_export_flags_are_rejected_as_alternative_artifacts() {
    let tmp = tempfile::tempdir().unwrap();
    let fixture = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl"
    );
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    for flag in ["--export-trace", "--export-standard-trace"] {
        let alternative = tmp.path().join("alternative.json");
        let output = Command::new(binary)
            .args([
                "--session-file",
                fixture,
                flag,
                alternative.to_str().unwrap(),
            ])
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains("unexpected argument"));
        assert!(!alternative.exists());
    }
}
