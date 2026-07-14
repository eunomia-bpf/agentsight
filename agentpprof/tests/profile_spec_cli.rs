use serde_json::Value;
use std::fs;
use std::path::PathBuf;
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

    let spec = serde_json::json!({
        "output": semantic_output,
        "format": "json",
        "view": "operations",
        "project_name": "operation-fixture",
        "operation_files": [ops_path],
        "op_map_files": [map_path],
        "where_rules": ["intent=authenticate"],
        "stack": "project,dataset,intent,phase,op,action,status",
        "rank_op_rules": ["failure-density:4=status=error"],
        "rank_mode": "rule-score",
        "deterministic_output": true
    });
    fs::write(&spec_path, serde_json::to_vec_pretty(&spec).unwrap()).unwrap();

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

#[test]
fn cli_induces_operation_stack_without_user_field_order() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let output_path = tmp.path().join("induced.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let mut rows = Vec::new();
    for _ in 0..6 {
        rows.push(r#"{"value":1,"fields":{"dataset":"agent-reward-bench","analysis_task":"agentreward_looping","repeat_state":"single","repeat_signal":"none","action":"click","looping":"no","problem_value":"negative","status":"failure","step_correct":"false","safety":"safe","human_group":"g0","group_pattern":"g0"}}"#);
    }
    for _ in 0..6 {
        rows.push(r#"{"value":1,"fields":{"dataset":"agent-reward-bench","analysis_task":"agentreward_looping","repeat_state":"same-action-run","repeat_signal":"loop-like","action":"click","looping":"yes","problem_value":"positive","status":"failure","step_correct":"true","safety":"unsafe","human_group":"g1","group_pattern":"g1"}}"#);
    }
    for _ in 0..6 {
        rows.push(r#"{"value":1,"fields":{"dataset":"agent-reward-bench","analysis_task":"agentreward_looping","repeat_state":"same-action-run","repeat_signal":"loop-like","action":"fill","looping":"yes","problem_value":"positive","status":"failure","step_correct":"true","safety":"unsafe","human_group":"g2","group_pattern":"g2"}}"#);
    }
    fs::write(&ops_path, rows.join("\n") + "\n").unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            output_path.to_str().unwrap(),
            "--where",
            "dataset=agent-reward-bench",
            "--where",
            "analysis_task=agentreward_looping",
            "--induce-operation-stack",
            "--induce-query-term",
            "loop",
            "--deterministic-output",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "induced CLI profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&output.stderr),
        String::from_utf8_lossy(&output.stdout)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["status"], "ok");
    assert_eq!(status["stack"], "operation");
    assert_eq!(status["induce_operation_stack"], true);
    assert_eq!(status["induce_task_stack"], true);
    assert_eq!(status["induced_stack_field"], "operation");
    assert_eq!(status["samples"], 18);

    let profile_json: Value =
        serde_json::from_str(&fs::read_to_string(&output_path).unwrap()).unwrap();
    let stacks = profile_json["profile"]["stacks"].as_object().unwrap();
    assert!(!stacks.is_empty());
    assert!(stacks.keys().all(|stack| stack.split(';').count() <= 4));
    assert_eq!(
        stacks
            .values()
            .map(|weight| weight.as_u64().unwrap())
            .sum::<u64>(),
        18
    );
    assert!(stacks.keys().all(|stack| {
        stack
            .split(';')
            .all(|frame| frame.starts_with("operation:"))
    }));
    assert!(stacks.keys().all(|stack| {
        !stack.contains("looping")
            && !stack.contains("problem_value")
            && !stack.contains("status:")
            && !stack.contains("step_correct")
            && !stack.contains("safety:")
            && !stack.contains("human_group")
            && !stack.contains("group_pattern")
    }));
    assert!(profile_json["profile"]["task_stack_induction"].is_null());
    let report = &profile_json["profile"]["operation_stack_induction"];
    assert_eq!(
        report["policy"],
        "recursive-information-gain-operation-stack-induction"
    );
    assert_eq!(
        report["objective"],
        "mean resource-weighted normalized information gain minus a fixed complexity penalty"
    );
    assert_eq!(
        report["complexity_penalty"],
        "ln(node_operation_count)/(2*node_operation_count)"
    );
    assert_eq!(report["derived_stack_field"], "operation");
    assert!(
        report["split_decisions"]
            .as_array()
            .unwrap()
            .iter()
            .all(|decision| decision["selected_score"]["cut_after"].as_u64().unwrap() > 0)
    );
    assert!(
        report["split_decisions"]
            .as_array()
            .unwrap()
            .iter()
            .all(
                |decision| decision["selected_score"]["normalized_information_gain"]
                    .as_f64()
                    .unwrap()
                    > 0.0
                    && decision["selected_score"]["score"].as_f64().unwrap()
                        > decision["selected_score"]["complexity_penalty"]
                            .as_f64()
                            .unwrap()
                    && decision["selected_score"]["accepted_margin"]
                        .as_f64()
                        .unwrap()
                        > 0.0
                    && decision["selected_score"]["left_label"]
                        != decision["selected_score"]["right_label"]
                    && !decision["selected_score"]["changed_fields"]
                        .as_array()
                        .unwrap()
                        .is_empty()
            )
    );
    let selected = report["selected_source_fields"].as_array().unwrap();
    assert_eq!(
        selected,
        report["selected_evidence_fields"].as_array().unwrap()
    );
    assert!(selected.iter().any(|field| {
        matches!(
            field.as_str().unwrap(),
            "repeat_state" | "repeat_signal" | "action"
        )
    }));
    assert!(selected.iter().all(|field| {
        !matches!(
            field.as_str().unwrap(),
            "looping"
                | "problem_value"
                | "status"
                | "step_correct"
                | "safety"
                | "human_group"
                | "group_pattern"
        )
    }));
    assert!(
        report["split_decisions"]
            .as_array()
            .unwrap()
            .iter()
            .all(|decision| {
                decision["selected_score"]["left_label"]
                    .as_str()
                    .unwrap()
                    .contains('=')
                    && decision["selected_score"]["right_label"]
                        .as_str()
                        .unwrap()
                        .contains('=')
            })
    );
    assert!(
        report["split_decisions"].as_array().unwrap().iter().all(
            |decision| decision["boundary_id"].as_str().unwrap().starts_with('b')
                && decision["primary_evidence_field"].as_str().is_some()
                && !decision["evidence_fields"].as_array().unwrap().is_empty()
        )
    );
}

#[test]
fn cli_legacy_task_stack_alias_ignores_hidden_oracle_only_boundaries() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let output_path = tmp.path().join("induced.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let mut rows = Vec::new();
    for _ in 0..6 {
        rows.push(r#"{"value":1,"fields":{"dataset":"fixture","analysis_task":"hidden_boundary","action":"click","step_correct":"false","safety":"safe","human_group":"g0","group_pattern":"g0","target_positive":"no"}}"#);
    }
    for _ in 0..6 {
        rows.push(r#"{"value":1,"fields":{"dataset":"fixture","analysis_task":"hidden_boundary","action":"click","step_correct":"true","safety":"unsafe","human_group":"g1","group_pattern":"g1","target_positive":"yes"}}"#);
    }
    fs::write(&ops_path, rows.join("\n") + "\n").unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            output_path.to_str().unwrap(),
            "--induce-task-stack",
            "--induce-query-term",
            "correct",
            "--deterministic-output",
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "induced CLI profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&output.stderr),
        String::from_utf8_lossy(&output.stdout)
    );

    let profile_json: Value =
        serde_json::from_str(&fs::read_to_string(&output_path).unwrap()).unwrap();
    let stacks = profile_json["profile"]["stacks"].as_object().unwrap();
    assert_eq!(stacks.len(), 1);
    assert_eq!(stacks["task:all"], 12);
    assert!(profile_json["profile"]["task_stack_induction"].is_null());
    let report = &profile_json["profile"]["operation_stack_induction"];
    assert!(
        report["selected_source_fields"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    assert!(report["split_decisions"].as_array().unwrap().is_empty());
}

#[test]
fn cli_legacy_task_stack_alias_rejects_non_task_stack_override() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let output_path = tmp.path().join("induced.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    fs::write(
        &ops_path,
        [
            r#"{"value":1,"fields":{"dataset":"agent-reward-bench","analysis_task":"agentreward_looping","repeat_state":"single","action":"click"}}"#,
            r#"{"value":1,"fields":{"dataset":"agent-reward-bench","analysis_task":"agentreward_looping","repeat_state":"same-action-run","action":"fill"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();

    let output = Command::new(binary)
        .args([
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--view",
            "operations",
            "--format",
            "json",
            "--output",
            output_path.to_str().unwrap(),
            "--induce-task-stack",
            "--stack",
            "action",
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("--induce-operation-stack derives a recursive operation-stack path"),
        "unexpected stderr: {stderr}"
    );
}

#[test]
fn profile_spec_replays_local_session_inputs_and_tag_rules() {
    let tmp = tempfile::tempdir().unwrap();
    let session_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl");
    let spec_path = tmp.path().join("session-profile-spec.json");
    let semantic_output = tmp.path().join("session-semantic.json");
    let coarse_output = tmp.path().join("session-coarse.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let spec = serde_json::json!({
        "output": semantic_output,
        "format": "json",
        "view": "operations",
        "project_name": "session-fixture",
        "session_files": [session_path],
        "tagger": "regex",
        "tag_rules": [
            "session:fixture=(?i)profile|agentpprof|agentsight-public-fixture",
            "prompt:inspect=(?i)profile the repository|find repeated",
            "prompt:verify=(?i)compare the test command|pprof outputs",
            "llm:summary=(?i)generated|profile"
        ],
        "where_rules": ["prompt=verify"],
        "stack": "project,agent,session,prompt,phase,op,tool,cmd,status",
        "rank_op_rules": ["test-density:3=cmd=cargo|effect=test|status=success"],
        "rank_mode": "rule-score",
        "deterministic_output": true
    });
    fs::write(&spec_path, serde_json::to_vec_pretty(&spec).unwrap()).unwrap();

    let semantic = Command::new(binary)
        .args(["--profile-spec", spec_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(
        semantic.status.success(),
        "session profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&semantic.stderr),
        String::from_utf8_lossy(&semantic.stdout)
    );
    let semantic_status: Value = serde_json::from_slice(&semantic.stdout).unwrap();
    assert_eq!(semantic_status["status"], "ok");
    assert_eq!(semantic_status["samples"], 4);
    assert_eq!(semantic_status["unique_stacks"], 4);
    assert_eq!(
        semantic_status["session_files"],
        serde_json::json!([session_path])
    );
    assert_eq!(
        semantic_status["where_rules"],
        serde_json::json!(["prompt=verify"])
    );
    assert_eq!(semantic_status["tagging"]["prompts"]["matched"], 2);
    assert_eq!(semantic_status["tagging"]["sessions"]["matched"], 1);

    let semantic_json: Value =
        serde_json::from_str(&fs::read_to_string(&semantic_output).unwrap()).unwrap();
    let stacks = semantic_json["profile"]["stacks"].as_object().unwrap();
    assert_eq!(stacks.len(), 4);
    assert!(
        stacks
            .keys()
            .all(|stack| stack.contains("prompt:verify") && !stack.contains("prompt:inspect"))
    );

    let ranking = semantic_json["profile"]["ranking"]["top"]
        .as_array()
        .unwrap();
    assert_eq!(
        ranking[0]["rank_operation_features"][0]["label"],
        "test-density"
    );
    assert!(ranking[0]["stack"].as_str().unwrap().contains("cmd:cargo"));

    let coarse = Command::new(binary)
        .args([
            "--profile-spec",
            spec_path.to_str().unwrap(),
            "--stack",
            "project,agent,session,prompt",
            "--output",
            coarse_output.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        coarse.status.success(),
        "coarse session profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&coarse.stderr),
        String::from_utf8_lossy(&coarse.stdout)
    );
    let coarse_status: Value = serde_json::from_slice(&coarse.stdout).unwrap();
    assert_eq!(coarse_status["samples"], 4);
    assert_eq!(coarse_status["unique_stacks"], 1);

    let coarse_json: Value =
        serde_json::from_str(&fs::read_to_string(&coarse_output).unwrap()).unwrap();
    assert_eq!(
        coarse_json["profile"]["stacks"]["project:session-fixture;agent:codex;session:fixture;prompt:verify"],
        4
    );
}

#[test]
fn profile_spec_replays_agent_trace_inputs_and_tag_rules() {
    let tmp = tempfile::tempdir().unwrap();
    let session_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl");
    let trace_path = tmp.path().join("fixture-agent-trace.json");
    let spec_path = tmp.path().join("trace-profile-spec.json");
    let output_path = tmp.path().join("trace-semantic.json");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let export = Command::new(binary)
        .args([
            "--project-root",
            env!("CARGO_MANIFEST_DIR"),
            "--session-file",
            session_path.to_str().unwrap(),
            "--export-trace",
            trace_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        export.status.success(),
        "agent trace export failed: {}\nstdout: {}",
        String::from_utf8_lossy(&export.stderr),
        String::from_utf8_lossy(&export.stdout)
    );
    let export_status: Value = serde_json::from_slice(&export.stdout).unwrap();
    assert_eq!(export_status["status"], "ok");
    assert_eq!(export_status["sessions"], 1);

    let spec = serde_json::json!({
        "output": output_path,
        "format": "json",
        "view": "operations",
        "project_name": "trace-fixture",
        "trace_files": [trace_path],
        "tagger": "regex",
        "tag_rules": [
            "session:fixture=(?i)profile|agentpprof|repo",
            "prompt:inspect=(?i)profile the repository|find repeated",
            "prompt:verify=(?i)compare the test command|pprof outputs",
            "llm:summary=(?i)generated|profile"
        ],
        "where_rules": ["prompt=verify"],
        "stack": "project,agent,session,prompt,phase,op,tool,cmd,status",
        "rank_op_rules": ["test-density:3=cmd=cargo|effect=test|status=success"],
        "rank_mode": "rule-score",
        "deterministic_output": true
    });
    fs::write(&spec_path, serde_json::to_vec_pretty(&spec).unwrap()).unwrap();

    let semantic = Command::new(binary)
        .args(["--profile-spec", spec_path.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(
        semantic.status.success(),
        "agent trace profile failed: {}\nstdout: {}",
        String::from_utf8_lossy(&semantic.stderr),
        String::from_utf8_lossy(&semantic.stdout)
    );
    let semantic_status: Value = serde_json::from_slice(&semantic.stdout).unwrap();
    assert_eq!(semantic_status["status"], "ok");
    assert_eq!(semantic_status["samples"], 4);
    assert_eq!(semantic_status["unique_stacks"], 4);
    assert_eq!(
        semantic_status["trace_files"],
        serde_json::json!([trace_path])
    );
    assert_eq!(semantic_status["tagging"]["prompts"]["matched"], 2);

    let profile_json: Value =
        serde_json::from_str(&fs::read_to_string(&output_path).unwrap()).unwrap();
    let stacks = profile_json["profile"]["stacks"].as_object().unwrap();
    assert_eq!(stacks.len(), 4);
    assert!(
        stacks
            .keys()
            .all(|stack| stack.contains("prompt:verify") && !stack.contains("prompt:inspect"))
    );
}
