use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};

fn run(binary: &str, args: &[&str]) -> Output {
    Command::new(binary).args(args).output().unwrap()
}

fn assert_pprof(output: &Output, path: &std::path::Path) -> Value {
    assert!(
        output.status.success(),
        "agentpprof failed: {}\nstdout: {}",
        String::from_utf8_lossy(&output.stderr),
        String::from_utf8_lossy(&output.stdout)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["status"], "ok");
    assert_eq!(status["format"], "pprof");
    let bytes = fs::read(path).unwrap();
    assert_eq!(&bytes[..2], &[0x1f, 0x8b]);
    status
}

fn recurrence_reference_jsonl() -> String {
    [("fill", 5), ("click", 4), ("fill", 3), ("click", 2)]
        .into_iter()
        .flat_map(|(action, count)| {
            std::iter::repeat_n(
                serde_json::json!({
                    "value": 1,
                    "fields": {"session": "reference", "action": action}
                })
                .to_string(),
                count,
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
        + "\n"
}

#[test]
fn profile_spec_composes_operation_fields_into_one_pprof() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let map_path = tmp.path().join("operation-map.txt");
    let spec_path = tmp.path().join("profile-spec.json");
    let output_path = tmp.path().join("semantic.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    fs::write(
        &ops_path,
        [
            r#"{"value":1,"fields":{"project":"fixture","action":"click","target":"login","status":"ok"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","action":"type","target":"email","status":"error"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","action":"click","target":"submit","status":"ok"}}"#,
            r#"{"value":1,"fields":{"project":"fixture","action":"click","target":"ad","status":"ok"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &map_path,
        "task:checkout=(target=login|target=email|target=submit)\nphase:input=(action=type)\n",
    )
    .unwrap();
    fs::write(
        &spec_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "output": output_path,
            "format": "pprof",
            "view": "operations",
            "operation_files": [ops_path],
            "op_map_files": [map_path],
            "where_rules": ["task=checkout"],
            "stack": "project,task,phase,action,status",
            "deterministic_output": true
        }))
        .unwrap(),
    )
    .unwrap();

    let output = run(binary, &["--profile-spec", spec_path.to_str().unwrap()]);
    let status = assert_pprof(&output, &output_path);
    assert_eq!(status["samples"], 3);
    assert_eq!(status["unique_stacks"], 2);
    assert_eq!(status["where_rules"], serde_json::json!(["task=checkout"]));
}

#[test]
fn recurrence_induction_and_calibration_write_pprof() {
    let tmp = tempfile::tempdir().unwrap();
    let reference_path = tmp.path().join("reference.jsonl");
    let calibration_path = tmp.path().join("calibration.jsonl");
    let target_path = tmp.path().join("target.jsonl");
    let output_path = tmp.path().join("induced.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(&reference_path, recurrence_reference_jsonl()).unwrap();
    fs::write(
        &calibration_path,
        ["click", "click", "fill", "click"]
            .into_iter()
            .map(|action| {
                serde_json::json!({"value":1,"fields":{
                    "session":"calibration","action":action,"group":"one-operation"
                }})
                .to_string()
            })
            .collect::<Vec<_>>()
            .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &target_path,
        ["click", "click", "fill", "click"]
            .into_iter()
            .map(|action| {
                serde_json::json!({"value":1,"fields":{"session":"target","action":action}})
                    .to_string()
            })
            .collect::<Vec<_>>()
            .join("\n")
            + "\n",
    )
    .unwrap();

    let output = run(
        binary,
        &[
            "--operation-file",
            target_path.to_str().unwrap(),
            "--view",
            "operations",
            "--induce-operation-stack",
            "--induce-reference-operation-file",
            reference_path.to_str().unwrap(),
            "--induce-calibration-operation-file",
            calibration_path.to_str().unwrap(),
            "--deterministic-output",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    let status = assert_pprof(&output, &output_path);
    assert_eq!(status["stack"], "operation");
    assert_eq!(status["induced_stack_field"], "operation");
    assert_eq!(status["induce_operation_stack"], true);
    assert_eq!(status["samples"], 4);
}

#[test]
fn agent_operation_marks_create_shared_variable_depth_operation_stacks() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let marks_path = tmp.path().join("operation-marks.json");
    let output_path = tmp.path().join("marked.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        [
            r#"{"value":2,"fields":{"session_id":"s1","operation_id":"a","action":"read"}}"#,
            r#"{"value":3,"fields":{"session_id":"s1","operation_id":"b","action":"read"}}"#,
            r#"{"value":5,"fields":{"session_id":"s1","operation_id":"c","action":"test"}}"#,
            r#"{"value":7,"fields":{"session_id":"s2","operation_id":"a","action":"read"}}"#,
            r#"{"value":11,"fields":{"session_id":"s2","operation_id":"b","action":"edit"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &marks_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "sequence_field": "session_id",
            "id_field": "operation_id",
            "operation_names": {
                "review": "Review evidence",
                "fix": "Fix implementation",
                "test": "Test the fix"
            },
            "marks": [
                {"sequence":"s1","start_operation_id":"a","operation_ids":["review"]},
                {"sequence":"s1","start_operation_id":"c","operation_ids":["fix","test"]},
                {"sequence":"s2","start_operation_id":"a","operation_ids":["review"]},
                {"sequence":"s2","start_operation_id":"b","operation_ids":["fix"]}
            ]
        }))
        .unwrap(),
    )
    .unwrap();

    let output = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--view",
            "operations",
            "--deterministic-output",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    let status = assert_pprof(&output, &output_path);
    assert_eq!(
        status["stack"],
        "project,agent,source_session,prompt,operation,call,tool"
    );
    assert_eq!(status["induced_stack_field"], "operation");
    assert_eq!(status["samples"], 28);
    assert_eq!(status["unique_stacks"], 4);
    assert_eq!(status["operation_mark_file"], marks_path.to_str().unwrap());
}

#[test]
fn operation_marks_fail_closed_and_do_not_mix_with_induction() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let marks_path = tmp.path().join("operation-marks.json");
    let output_path = tmp.path().join("out.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        [
            r#"{"value":1,"fields":{"session":"s","id":"one","action":"read"}}"#,
            r#"{"value":1,"fields":{"session":"s","id":"two","action":"write"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &marks_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "sequence_field": "session",
            "id_field": "id",
            "operation_names": {"review": "Review evidence"},
            "marks": [
                {"sequence":"s","start_operation_id":"two","operation_ids":["review"]}
            ]
        }))
        .unwrap(),
    )
    .unwrap();

    let missing_first = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--view",
            "operations",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!missing_first.status.success());
    assert!(
        String::from_utf8_lossy(&missing_first.stderr)
            .contains("must start at first source operation ID")
    );

    let mixed = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--induce-operation-stack",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!mixed.status.success());
    assert!(
        String::from_utf8_lossy(&mixed.stderr)
            .contains("cannot be combined with --induce-operation-stack")
    );

    fs::write(
        &marks_path,
        r#"{
            "sequence_field":"session",
            "id_field":"id",
            "operation_names":{"review":"Review evidence"},
            "marks":[{"sequence":"s","start_operation_id":"one","operation_ids":["review"]}]
        }"#,
    )
    .unwrap();

    let token_view = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--view",
            "tokens",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    let token_status = assert_pprof(&token_view, &output_path);
    assert_eq!(token_status["view"], "tokens");
    assert_eq!(token_status["sample_type"], "tokens");
    assert_eq!(token_status["samples"], 2);

    let diff = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--diff-base-operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--view",
            "operations",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!diff.status.success());
    assert!(
        String::from_utf8_lossy(&diff.stderr)
            .contains("cannot currently be combined with --diff-base-operation-file")
    );
}

#[test]
fn operation_marks_propagate_across_zero_weight_resource_operations() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let marks_path = tmp.path().join("operation-marks.json");
    let output_path = tmp.path().join("files.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        [
            r#"{"value":0,"fields":{"sequence":"s","id":"a"}}"#,
            r#"{"value":4,"fields":{"sequence":"s","id":"b"}}"#,
            r#"{"value":0,"fields":{"sequence":"s","id":"c"}}"#,
            r#"{"value":5,"fields":{"sequence":"s","id":"d"}}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &marks_path,
        r#"{
            "sequence_field":"sequence",
            "id_field":"id",
            "operation_names":{"review":"Review evidence","fix":"Fix implementation"},
            "marks":[
                {"sequence":"s","start_operation_id":"a","operation_ids":["review"]},
                {"sequence":"s","start_operation_id":"c","operation_ids":["fix"]}
            ]
        }"#,
    )
    .unwrap();

    let output = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--operation-mark-file",
            marks_path.to_str().unwrap(),
            "--view",
            "files",
            "--deterministic-output",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    let status = assert_pprof(&output, &output_path);
    assert_eq!(status["sample_type"], "file_events");
    assert_eq!(status["operations"], 4);
    assert_eq!(status["samples"], 9);
    assert_eq!(status["unique_stacks"], 2);
}

#[test]
fn profile_spec_resolves_relative_operation_mark_file() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let marks_path = tmp.path().join("marks.json");
    let spec_path = tmp.path().join("profile.json");
    let output_path = tmp.path().join("marked.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        "{\"value\":1,\"fields\":{\"session\":\"s\",\"id\":\"one\"}}\n",
    )
    .unwrap();
    fs::write(
        &marks_path,
        r#"{
            "sequence_field":"session",
            "id_field":"id",
            "operation_names":{"review":"Review evidence"},
            "marks":[{"sequence":"s","start_operation_id":"one","operation_ids":["review"]}]
        }"#,
    )
    .unwrap();
    fs::write(
        &spec_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "output": "marked.pb.gz",
            "view": "operations",
            "operation_files": ["ops.jsonl"],
            "operation_mark_file": "marks.json",
            "deterministic_output": true
        }))
        .unwrap(),
    )
    .unwrap();

    let output = run(binary, &["--profile-spec", spec_path.to_str().unwrap()]);
    let status = assert_pprof(&output, &output_path);
    assert_eq!(
        status["stack"],
        "project,agent,source_session,prompt,operation,call,tool"
    );
    assert_eq!(status["samples"], 1);
    assert_eq!(status["operation_mark_file"], marks_path.to_str().unwrap());
}

#[test]
fn recurrence_options_reject_invalid_inputs() {
    let tmp = tempfile::tempdir().unwrap();
    let target_path = tmp.path().join("target.jsonl");
    let reference_path = tmp.path().join("reference.jsonl");
    let calibration_path = tmp.path().join("calibration.jsonl");
    let output_path = tmp.path().join("out.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &target_path,
        "{\"value\":1,\"fields\":{\"session\":\"s\",\"action\":\"click\"}}\n",
    )
    .unwrap();
    fs::write(&reference_path, recurrence_reference_jsonl()).unwrap();
    fs::write(
        &calibration_path,
        "{\"value\":1,\"fields\":{\"session\":\"c\",\"action\":\"click\",\"group\":\"g\"}}\n",
    )
    .unwrap();

    let without_induction = run(
        binary,
        &[
            "--operation-file",
            target_path.to_str().unwrap(),
            "--induce-calibration-operation-file",
            calibration_path.to_str().unwrap(),
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!without_induction.status.success());
    assert!(
        String::from_utf8_lossy(&without_induction.stderr)
            .contains("requires --induce-operation-stack")
    );

    let without_reference = run(
        binary,
        &[
            "--operation-file",
            target_path.to_str().unwrap(),
            "--induce-operation-stack",
            "--induce-calibration-operation-file",
            calibration_path.to_str().unwrap(),
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!without_reference.status.success());
    assert!(
        String::from_utf8_lossy(&without_reference.stderr)
            .contains("requires --induce-reference-operation-file")
    );

    let legacy_knob = run(
        binary,
        &[
            "--operation-file",
            target_path.to_str().unwrap(),
            "--induce-operation-stack",
            "--induce-reference-operation-file",
            reference_path.to_str().unwrap(),
            "--induce-max-depth",
            "2",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!legacy_knob.status.success());
    assert!(
        String::from_utf8_lossy(&legacy_knob.stderr)
            .contains("does not accept --induce-allow-session")
    );
}

#[test]
fn legacy_task_stack_alias_is_pprof_only_and_rejects_non_task_stack() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let reference_path = tmp.path().join("reference.jsonl");
    let output_path = tmp.path().join("alias.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        ["click", "click", "fill"]
            .into_iter()
            .map(|action| {
                serde_json::json!({"value":1,"fields":{"session":"s","action":action}}).to_string()
            })
            .collect::<Vec<_>>()
            .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(&reference_path, recurrence_reference_jsonl()).unwrap();

    let valid = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--view",
            "operations",
            "--induce-task-stack",
            "--induce-reference-operation-file",
            reference_path.to_str().unwrap(),
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    let status = assert_pprof(&valid, &output_path);
    assert_eq!(status["stack"], "task");

    let invalid = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--induce-task-stack",
            "--induce-reference-operation-file",
            reference_path.to_str().unwrap(),
            "--stack",
            "action",
            "--output",
            output_path.to_str().unwrap(),
        ],
    );
    assert!(!invalid.status.success());
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("omit --stack or use --stack task"));
}

#[test]
fn local_session_profile_spec_writes_one_pprof() {
    let tmp = tempfile::tempdir().unwrap();
    let session_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl");
    let spec_path = tmp.path().join("session-profile-spec.json");
    let output_path = tmp.path().join("session.pb.gz");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &spec_path,
        serde_json::to_vec_pretty(&serde_json::json!({
            "output": output_path,
            "format": "pprof",
            "view": "operations",
            "project_name": "session-fixture",
            "session_files": [session_path],
            "tagger": "regex",
            "tag_rules": [
                "session:fixture=(?i)profile|agentpprof|agentsight-public-fixture",
                "prompt:verify=(?i)compare the test command|pprof outputs"
            ],
            "where_rules": ["prompt=verify"],
            "stack": "project,agent,session,prompt,phase,op,tool,cmd,status",
            "deterministic_output": true
        }))
        .unwrap(),
    )
    .unwrap();

    let output = run(binary, &["--profile-spec", spec_path.to_str().unwrap()]);
    let status = assert_pprof(&output, &output_path);
    assert_eq!(status["samples"], 4);
    assert_eq!(status["tagging"]["sessions"]["matched"], 1);
    assert_eq!(status["tagging"]["prompts"]["matched"], 1);
}

#[test]
fn public_cli_rejects_every_alternative_product_artifact() {
    let tmp = tempfile::tempdir().unwrap();
    let ops_path = tmp.path().join("ops.jsonl");
    let binary = env!("CARGO_BIN_EXE_agentpprof");
    fs::write(
        &ops_path,
        "{\"value\":1,\"fields\":{\"task\":\"verify\",\"action\":\"test\"}}\n",
    )
    .unwrap();

    for (format, name) in [
        ("json", "out.json"),
        ("svg", "out.svg"),
        ("folded", "out.folded"),
    ] {
        let path = tmp.path().join(name);
        let output = run(
            binary,
            &[
                "--operation-file",
                ops_path.to_str().unwrap(),
                "--format",
                format,
                "--output",
                path.to_str().unwrap(),
            ],
        );
        assert!(!output.status.success());
        assert!(String::from_utf8_lossy(&output.stderr).contains("invalid value"));
        assert!(!path.exists());
    }

    let wrong_extension = tmp.path().join("out.data");
    let output = run(
        binary,
        &[
            "--operation-file",
            ops_path.to_str().unwrap(),
            "--output",
            wrong_extension.to_str().unwrap(),
        ],
    );
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains(".pb or .pb.gz"));
    assert!(!wrong_extension.exists());
}
