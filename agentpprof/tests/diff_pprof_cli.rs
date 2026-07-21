use serde_json::Value;
use std::fs;
use std::process::Command;

#[test]
fn cli_writes_one_signed_pprof_for_candidate_minus_base() {
    let tmp = tempfile::tempdir().unwrap();
    let candidate_path = tmp.path().join("bad.jsonl");
    let base_path = tmp.path().join("good.jsonl");
    let output_path = tmp.path().join("difference.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    fs::write(
        &candidate_path,
        [
            r#"{"value":1,"fields":{"task":"checkout","subtask":"authenticate","action":"retry","result":"error"}}"#,
            r#"{"value":1,"fields":{"task":"checkout","subtask":"authenticate","action":"retry","result":"error"}}"#,
            r#"{"value":1,"fields":{"task":"checkout","subtask":"authenticate","action":"abort","result":"failed"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &base_path,
        [
            r#"{"value":1,"fields":{"task":"checkout","subtask":"authenticate","action":"retry","result":"error"}}"#,
            r#"{"value":1,"fields":{"task":"checkout","subtask":"authenticate","action":"submit","result":"done"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            candidate_path.to_str().unwrap(),
            "--diff-base-operation-file",
            base_path.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            "task,subtask,action,result",
            "--deterministic-output",
            "--output",
            output_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "difference profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&output.stderr),
        String::from_utf8_lossy(&output.stdout)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["status"], "ok");
    assert_eq!(status["format"], "pprof");
    assert_eq!(status["comparison"], "candidate-minus-base");
    assert_eq!(status["positive_difference"], 2);
    assert_eq!(status["negative_difference"], 1);
    assert_eq!(status["difference_unique_stacks"], 3);
    let bytes = fs::read(output_path).unwrap();
    assert_eq!(&bytes[..2], &[0x1f, 0x8b]);
}

#[test]
fn cli_rejects_non_pprof_difference_output() {
    let tmp = tempfile::tempdir().unwrap();
    let candidate_path = tmp.path().join("bad.jsonl");
    let base_path = tmp.path().join("good.jsonl");
    let output_path = tmp.path().join("difference.svg");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    let row = r#"{"value":1,"fields":{"task":"checkout","action":"retry"}}"#;
    fs::write(&candidate_path, format!("{row}\n")).unwrap();
    fs::write(&base_path, format!("{}\n", row.replace("retry", "finish"))).unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            candidate_path.to_str().unwrap(),
            "--diff-base-operation-file",
            base_path.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            "task,action",
            "--output",
            output_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("only writes standard pprof"));
    assert!(!output_path.exists());
}

#[test]
fn cli_writes_empty_pprof_when_candidate_matches_base() {
    let tmp = tempfile::tempdir().unwrap();
    let operations = tmp.path().join("same.jsonl");
    let output_path = tmp.path().join("no-difference.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &operations,
        "{\"value\":1,\"fields\":{\"task\":\"checkout\",\"action\":\"finish\"}}\n",
    )
    .unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            operations.to_str().unwrap(),
            "--diff-base-operation-file",
            operations.to_str().unwrap(),
            "--view",
            "operations",
            "--stack",
            "task,action",
            "--output",
            output_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "empty difference failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["difference_unique_stacks"], 0);
    assert_eq!(status["positive_difference"], 0);
    assert_eq!(status["negative_difference"], 0);
    assert!(output_path.is_file());
}
