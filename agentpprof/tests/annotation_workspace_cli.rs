use flate2::read::GzDecoder;
use prost::Message;
use serde_json::Value;
use std::fs;
use std::io::Read;
use std::process::Command;

#[derive(Clone, PartialEq, Message)]
struct PprofProfile {
    #[prost(message, repeated, tag = "2")]
    sample: Vec<PprofSample>,
    #[prost(string, repeated, tag = "6")]
    string_table: Vec<String>,
}

#[derive(Clone, PartialEq, Message)]
struct PprofSample {
    #[prost(uint64, repeated, tag = "1")]
    location_id: Vec<u64>,
    #[prost(int64, repeated, tag = "2")]
    value: Vec<i64>,
}

fn run(binary: &str, args: &[&str]) -> std::process::Output {
    Command::new(binary).args(args).output().unwrap()
}

#[test]
fn annotation_workspace_updates_trace_and_folded_and_writes_pprof() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let annotations = workspace.join("annotation.json");
    let output = tmp.path().join("profile.pb.gz");
    fs::write(
        &trace,
        [
            r#"{"id":"s","parent":null,"kind":"session","data":{"name":"run-a","agent":"Codex"},"metrics":{},"path":[]}"#,
            r#"{"id":"p","parent":"s","kind":"prompt","data":{"name":"repair"},"metrics":{},"path":[]}"#,
            r#"{"id":"c1","parent":"p","kind":"llm","data":{},"metrics":{},"path":[]}"#,
            r#"{"id":"t1","parent":"c1","kind":"tool","data":{"tool":"shell"},"metrics":{"operations":1,"tokens":13},"path":[]}"#,
            r#"{"id":"c2","parent":"p","kind":"llm","data":{},"metrics":{},"path":[]}"#,
            r#"{"id":"t2","parent":"c2","kind":"tool","data":{"tool":"test"},"metrics":{"operations":1,"tokens":21},"path":[]}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &annotations,
        serde_json::to_vec_pretty(&serde_json::json!({
            "s": {"tag":"Repair regression","parent":null,"next":null},
            "p": {"tag":"Fix user-reported failure","parent":"s","next":null},
            "c1": {"tag":"Diagnose","parent":"p","next":"c2"},
            "t1": {"tag":"Run reproducer","parent":"c1","next":"c2"},
            "c2": {"tag":"Validate fix","parent":"p","next":null}
        }))
        .unwrap(),
    )
    .unwrap();

    let result = run(
        env!("CARGO_BIN_EXE_agentpprof"),
        &[
            "--annotation-file",
            annotations.to_str().unwrap(),
            "--view",
            "tokens",
            "--deterministic-output",
            "--output",
            output.to_str().unwrap(),
        ],
    );
    assert!(
        result.status.success(),
        "stdout={}\nstderr={}",
        String::from_utf8_lossy(&result.stdout),
        String::from_utf8_lossy(&result.stderr)
    );
    let status: Value = serde_json::from_slice(&result.stdout).unwrap();
    assert_eq!(status["samples"], 34);
    assert_eq!(status["max_semantic_depth"], 4);
    assert_eq!(status["warnings"].as_array().unwrap().len(), 1);
    assert!(
        status["warnings"][0]
            .as_str()
            .unwrap()
            .contains("degenerate unary refinement")
    );

    let rewritten = fs::read_to_string(&trace).unwrap();
    assert!(rewritten.contains(
        r#""path":["Repair regression","Fix user-reported failure","Diagnose","Run reproducer"]"#
    ));
    assert!(
        rewritten
            .contains(r#""path":["Repair regression","Fix user-reported failure","Validate fix"]"#)
    );
    let folded = fs::read_to_string(workspace.join("stacks.folded")).unwrap();
    assert!(
        folded.contains("agent:codex;operation:repair_regression;operation:fix_user-reported_failure;operation:diagnose;operation:run_reproducer"),
        "{folded}"
    );
    assert!(folded.contains(
        "agent:codex;operation:repair_regression;operation:fix_user-reported_failure;operation:validate_fix"
    ));
    assert!(!folded.contains("session:run_a"));
    assert!(!folded.contains("prompt:repair"));

    let mut decoder = GzDecoder::new(fs::File::open(output).unwrap());
    let mut decoded = Vec::new();
    decoder.read_to_end(&mut decoded).unwrap();
    let profile = PprofProfile::decode(decoded.as_slice()).unwrap();
    assert_eq!(
        profile
            .sample
            .iter()
            .map(|sample| sample.value[0])
            .sum::<i64>(),
        34
    );
}

#[test]
fn invalid_annotation_does_not_rewrite_workspace_files() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let folded = workspace.join("stacks.folded");
    let annotations = workspace.join("annotation.json");
    let output = tmp.path().join("profile.pb.gz");
    let original_trace = r#"{"id":"s","parent":null,"kind":"session","metrics":{"operations":1},"path":[]}
"#;
    fs::write(&trace, original_trace).unwrap();
    fs::write(&folded, "existing 1\n").unwrap();
    fs::write(
        &annotations,
        r#"{"missing":{"tag":"Unknown","parent":null,"next":null}}"#,
    )
    .unwrap();

    let result = run(
        env!("CARGO_BIN_EXE_agentpprof"),
        &[
            "--annotation-file",
            annotations.to_str().unwrap(),
            "--view",
            "operations",
            "--output",
            output.to_str().unwrap(),
        ],
    );
    assert!(!result.status.success());
    assert_eq!(fs::read_to_string(trace).unwrap(), original_trace);
    assert_eq!(fs::read_to_string(folded).unwrap(), "existing 1\n");
    assert!(!output.exists());
}
