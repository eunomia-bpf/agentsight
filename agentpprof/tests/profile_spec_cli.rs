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
    assert_eq!(status["induce_operation_stack"], true);
    assert_eq!(status["samples"], 4);
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
