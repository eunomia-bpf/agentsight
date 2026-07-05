use serde_json::Value;
use std::fs;
use std::process::Command;

#[test]
fn profile_spec_composes_mapping_filter_ranking_and_stack_depth() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let map_path = tmp.path().join("operation-map.txt");
    let spec_path = tmp.path().join("profile-spec.json");
    let semantic_output = tmp.path().join("semantic.json");
    let coarse_output = tmp.path().join("coarse.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    fs::write(
        &ops_path,
        [
            r#"{"value":1,"fields":{"project":"fixture","dataset":"web","agent":"demo","op":"action","action":"click","target":"login","status":"ok"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","dataset":"web","agent":"demo","op":"action","action":"type","target":"email","status":"error"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","dataset":"web","agent":"demo","op":"action","action":"click","target":"submit","status":"ok"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","dataset":"web","agent":"demo","op":"action","action":"click","target":"ad","status":"ok"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();

    fs::write(
        &map_path,
        "\
# Derive task and intent fields before folding.
task:checkout=(target=login|target=email|target=submit)
intent:authenticate=(task=checkout)
phase:select=(action=click.*intent=authenticate.*target=login)
phase:input=(action=type.*intent=authenticate.*target=email)
phase:submit=(action=click.*intent=authenticate.*target=submit)
",
    )
    .unwrap();

    fs::write(
        &spec_path,
        format!(
            r#"{{
  "output": "{}",
  "format": "json",
  "view": "operations",
  "project_name": "operation-fixture",
  "operation_files": ["{}"],
  "op_map_files": ["{}"],
  "where_rules": ["intent=authenticate"],
  "stack": "project,dataset,intent,phase,op,action,status",
  "rank_op_rules": ["failure-density:4=status=error"],
  "rank_mode": "rule-score",
  "deterministic_output": true
}}"#,
            semantic_output.display(),
            ops_path.display(),
            map_path.display(),
        ),
    )
    .unwrap();

    let semantic = Command::new(binary)
        .args(["--profile-spec", spec_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(
        semantic.status.success(),
        "semantic profile failed: {}",
        String::from_utf8_lossy(&semantic.stderr)
    );
    let semantic_status: Value = serde_json::from_slice(&semantic.stdout).unwrap();
    assert_eq!(semantic_status["status"], "ok");
    assert_eq!(semantic_status["samples"], 3);
    assert_eq!(semantic_status["unique_stacks"], 3);
    assert_eq!(
        semantic_status["where_rules"],
        serde_json::json!(["intent=authenticate"])
    );

    let semantic_json: Value =
        serde_json::from_str(&fs::read_to_string(&semantic_output).unwrap()).unwrap();
    let stacks = semantic_json["profile"]["stacks"].as_object().unwrap();
    assert_eq!(stacks.len(), 3);
    assert!(
        stacks
            .keys()
            .all(|stack| { !stack.contains("session:") && !stack.contains("prompt:") })
    );
    assert_eq!(
        stacks["project:fixture;dataset:web;intent:authenticate;phase:input;op:action;action:type;status:error"],
        1
    );

    let ranking = semantic_json["profile"]["ranking"]["top"]
        .as_array()
        .unwrap();
    assert_eq!(
        ranking[0]["stack"],
        "project:fixture;dataset:web;intent:authenticate;phase:input;op:action;action:type;status:error"
    );
    assert_eq!(ranking[0]["rank_score"], 4.0);
    assert_eq!(
        ranking[0]["rank_operation_features"][0]["label"],
        "failure-density"
    );

    let coarse = Command::new(binary)
        .args([
            "--profile-spec",
            spec_path.to_str().unwrap(),
            "--stack",
            "project,dataset,intent",
            "--output",
            coarse_output.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        coarse.status.success(),
        "coarse profile failed: {}",
        String::from_utf8_lossy(&coarse.stderr)
    );
    let coarse_status: Value = serde_json::from_slice(&coarse.stdout).unwrap();
    assert_eq!(coarse_status["samples"], 3);
    assert_eq!(coarse_status["unique_stacks"], 1);

    let coarse_json: Value =
        serde_json::from_str(&fs::read_to_string(&coarse_output).unwrap()).unwrap();
    assert_eq!(
        coarse_json["profile"]["stacks"]["project:fixture;dataset:web;intent:authenticate"],
        3
    );
}
