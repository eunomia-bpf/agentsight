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
fn local_session_workspace_adapter_writes_stable_three_file_workspace() {
    let tmp = tempfile::tempdir().unwrap();
    let first = tmp.path().join("first");
    let second = tmp.path().join("second");
    let fixture = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl"
    );
    let binary = env!("CARGO_BIN_EXE_agentpprof");

    let initialize = |workspace: &std::path::Path| {
        run(
            binary,
            &[
                "--workspace-out",
                workspace.to_str().unwrap(),
                "--session-file",
                fixture,
            ],
        )
    };
    let output = initialize(&first);
    assert!(
        output.status.success(),
        "stdout={}\nstderr={}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    let status: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(status["sessions"], 1);
    assert_eq!(status["nodes"], 8);
    assert_eq!(status["node_kinds"]["session"], 1);
    assert_eq!(status["node_kinds"]["prompt"], 2);
    assert_eq!(status["node_kinds"]["llm"], 2);
    assert_eq!(status["node_kinds"]["tool"], 3);
    assert_eq!(status["operations"], 3);
    assert_eq!(status["tokens"], 166);
    assert_eq!(
        fs::read_to_string(first.join("annotation.json")).unwrap(),
        "{}\n"
    );
    assert_eq!(fs::read_to_string(first.join("stacks.folded")).unwrap(), "");

    let trace = fs::read_to_string(first.join("trace.jsonl")).unwrap();
    let rows = trace
        .lines()
        .map(|line| serde_json::from_str::<Value>(line).unwrap())
        .collect::<Vec<_>>();
    let mut seen = std::collections::HashMap::new();
    for row in &rows {
        let id = row["id"].as_str().unwrap();
        if let Some(parent) = row["parent"].as_str() {
            assert!(
                seen.contains_key(parent),
                "parent {parent:?} must precede {id:?}"
            );
        }
        seen.insert(id, row["kind"].as_str().unwrap());
    }
    let llm_rows = rows
        .iter()
        .filter(|row| row["kind"] == "llm")
        .collect::<Vec<_>>();
    assert_eq!(
        llm_rows
            .iter()
            .map(|row| row["metrics"]["tokens"].as_u64().unwrap())
            .sum::<u64>(),
        166
    );
    for row in llm_rows {
        assert!(row["data"]["text"].as_str().is_some());
    }
    for row in rows.iter().filter(|row| row["kind"] == "tool") {
        assert_eq!(row["metrics"]["operations"], 1);
        let parent = row["parent"].as_str().unwrap();
        assert_eq!(seen[parent], "llm");
        assert!(row["data"]["arguments_preview"].as_str().is_some());
        assert!(row["data"]["result_preview"].as_str().is_some());
    }

    let second_output = initialize(&second);
    assert!(
        second_output.status.success(),
        "stderr={}",
        String::from_utf8_lossy(&second_output.stderr)
    );
    assert_eq!(
        fs::read(first.join("trace.jsonl")).unwrap(),
        fs::read(second.join("trace.jsonl")).unwrap()
    );

    let overwrite = initialize(&first);
    assert!(!overwrite.status.success());
    assert!(
        String::from_utf8_lossy(&overwrite.stderr).contains("refusing to overwrite"),
        "{}",
        String::from_utf8_lossy(&overwrite.stderr)
    );
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
            "p": {"tag":"Fix reported failure","parent":"s","next":null},
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
        r#""path":["Repair regression","Fix reported failure","Diagnose","Run reproducer"]"#
    ));
    assert!(
        rewritten.contains(r#""path":["Repair regression","Fix reported failure","Validate fix"]"#)
    );
    let folded = fs::read_to_string(workspace.join("stacks.folded")).unwrap();
    assert!(
        folded.contains("agent:codex;operation:repair_regression;operation:fix_reported_failure;operation:diagnose;operation:run_reproducer"),
        "{folded}"
    );
    assert!(folded.contains(
        "agent:codex;operation:repair_regression;operation:fix_reported_failure;operation:validate_fix"
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

#[test]
fn broad_optional_leaf_emits_coarse_span_warning_without_blocking_profile() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let annotations = workspace.join("annotation.json");
    let output = tmp.path().join("profile.pb.gz");
    let mut rows = vec![
        r#"{"id":"s","parent":null,"kind":"session","data":{"agent":"Codex"},"metrics":{},"path":[]}"#
            .to_string(),
        r#"{"id":"p","parent":"s","kind":"prompt","data":{"name":"repair"},"metrics":{},"path":[]}"#
            .to_string(),
    ];
    for index in 0..8 {
        rows.push(format!(
            r#"{{"id":"c{index}","parent":"p","kind":"llm","data":{{"name":"step {index}"}},"metrics":{{}},"path":[]}}"#
        ));
        rows.push(format!(
            r#"{{"id":"t{index}","parent":"c{index}","kind":"tool","data":{{"name":"shell"}},"metrics":{{"operations":1}},"path":[]}}"#
        ));
    }
    rows.push(
        r#"{"id":"c8","parent":"p","kind":"llm","data":{"name":"report"},"metrics":{},"path":[]}"#
            .to_string(),
    );
    fs::write(&trace, rows.join("\n") + "\n").unwrap();
    fs::write(
        &annotations,
        serde_json::to_vec_pretty(&serde_json::json!({
            "s": {"tag":"Repair regression","parent":null,"next":null},
            "p": {"tag":"Fix user-reported failure","parent":"s","next":null},
            "c0": {"tag":"Recover interaction","parent":"p","next":"c8"}
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
            "operations",
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
    assert_eq!(status["samples"], 8);
    let warnings = status["warnings"].as_array().unwrap();
    assert_eq!(warnings.len(), 1);
    assert!(
        warnings[0]
            .as_str()
            .unwrap()
            .contains("coarse unrefined span")
    );
    assert_eq!(status["semantic_depth_mass"]["3"], 8);
    assert_eq!(status["issues"].as_array().unwrap().len(), 1);
    assert_eq!(status["issues"][0]["kind"], "coarse_span");
    assert_eq!(status["issues"][0]["start_node_id"], "c0");
    assert_eq!(status["issues"][0]["end_node_id"], "c8");
    assert_eq!(status["issues"][0]["session_id"], "s");
    assert_eq!(status["issues"][0]["covered_tool_calls"], 8);
    assert_eq!(
        status["issues"][0]["review_key"],
        "hierarchy:coarse_span:s:c0"
    );
    assert_eq!(
        status["issues"][0]["context_fingerprint"]
            .as_str()
            .unwrap()
            .len(),
        16
    );
}

#[test]
fn multi_session_workspace_reports_cross_session_tag_reuse() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let annotations = workspace.join("annotation.json");
    let output = tmp.path().join("profile.pb.gz");
    fs::write(
        &trace,
        [
            r#"{"id":"s1","parent":null,"kind":"session","data":{"agent":"Codex"},"metrics":{},"path":[]}"#,
            r#"{"id":"p1","parent":"s1","kind":"prompt","metrics":{},"path":[]}"#,
            r#"{"id":"c1","parent":"p1","kind":"llm","metrics":{"operations":1},"path":[]}"#,
            r#"{"id":"s2","parent":null,"kind":"session","data":{"agent":"Codex"},"metrics":{},"path":[]}"#,
            r#"{"id":"p2","parent":"s2","kind":"prompt","metrics":{},"path":[]}"#,
            r#"{"id":"c2","parent":"p2","kind":"llm","metrics":{"operations":1},"path":[]}"#,
            r#"{"id":"c3","parent":"p2","kind":"llm","metrics":{"operations":1},"path":[]}"#,
        ]
        .join("\n")
            + "\n",
    )
    .unwrap();
    fs::write(
        &annotations,
        serde_json::to_vec_pretty(&serde_json::json!({
            "s1": {"tag":"Repair regression","parent":null,"next":null},
            "p1": {"tag":"Fix failure","parent":"s1","next":null},
            "c1": {"tag":"Inspect code","parent":"p1","next":null},
            "s2": {"tag":"Repair regression","parent":null,"next":null},
            "p2": {"tag":"Fix failure","parent":"s2","next":null},
            "c2": {"tag":"Inspect code","parent":"p2","next":"c3"},
            "c3": {"tag":"Inspect codes","parent":"p2","next":null}
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
            "operations",
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
    assert_eq!(status["semantic_tags"], 2);
    assert_eq!(status["cross_session_tags"], 1);
    assert_eq!(status["singleton_tags"], 1);
    assert_eq!(status["min_semantic_depth"], 3);
    assert_eq!(status["max_semantic_depth"], 3);
    assert_eq!(status["semantic_depth_mass"]["3"], 3);
    let tag_reuse = status["tag_reuse"].as_array().unwrap();
    assert_eq!(tag_reuse.len(), 2);
    assert_eq!(tag_reuse[0]["tag"], "inspect code");
    assert_eq!(tag_reuse[0]["occurrences"], 2);
    assert_eq!(tag_reuse[0]["sessions"].as_array().unwrap().len(), 2);
    assert_eq!(tag_reuse[0]["review_key"], "tag:inspect code");
    assert_eq!(
        tag_reuse[0]["context_fingerprint"].as_str().unwrap().len(),
        16
    );
    assert_eq!(tag_reuse[1]["tag"], "inspect codes");
    assert_eq!(tag_reuse[1]["occurrences"], 1);
    assert_eq!(tag_reuse[1]["sessions"][0], "s2");
    let near_names = status["near_name_candidates"].as_array().unwrap();
    assert_eq!(near_names.len(), 1);
    assert_eq!(near_names[0]["left"], "inspect code");
    assert_eq!(near_names[0]["right"], "inspect codes");
    assert_eq!(
        near_names[0]["review_key"],
        "near-name:inspect code:inspect codes"
    );
    assert_eq!(
        near_names[0]["context_fingerprint"].as_str().unwrap().len(),
        16
    );
    assert!(
        status["warnings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|warning| warning
                .as_str()
                .unwrap()
                .contains("cross-session fragmentation"))
    );
}

#[test]
fn annotation_workspace_depth_mass_matches_every_profile_view() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let annotations = workspace.join("annotation.json");
    fs::write(
        &trace,
        r#"{"id":"s","parent":null,"kind":"session","data":{"agent":"Codex"},"metrics":{"operations":2,"tokens":3,"files":4,"network":5,"time_ns":6},"path":[]}
"#,
    )
    .unwrap();
    fs::write(
        &annotations,
        r#"{"s":{"tag":"Inspect","parent":null,"next":null}}
"#,
    )
    .unwrap();

    for (view, expected) in [
        ("operations", 2),
        ("tokens", 3),
        ("files", 4),
        ("network", 5),
        ("time", 6),
    ] {
        let output = tmp.path().join(format!("{view}.pb.gz"));
        let result = run(
            env!("CARGO_BIN_EXE_agentpprof"),
            &[
                "--annotation-file",
                annotations.to_str().unwrap(),
                "--view",
                view,
                "--output",
                output.to_str().unwrap(),
            ],
        );
        assert!(
            result.status.success(),
            "view={view}\nstdout={}\nstderr={}",
            String::from_utf8_lossy(&result.stdout),
            String::from_utf8_lossy(&result.stderr)
        );
        let status: Value = serde_json::from_slice(&result.stdout).unwrap();
        assert_eq!(status["samples"], expected);
        assert_eq!(status["semantic_depth_mass"]["1"], expected);
    }
}

#[test]
fn annotation_tag_over_three_words_is_rejected() {
    let tmp = tempfile::tempdir().unwrap();
    let workspace = tmp.path().join("workspace");
    fs::create_dir(&workspace).unwrap();
    let trace = workspace.join("trace.jsonl");
    let annotations = workspace.join("annotation.json");
    let output = tmp.path().join("profile.pb.gz");
    fs::write(
        &trace,
        r#"{"id":"s","parent":null,"kind":"session","metrics":{"operations":1},"path":[]}
"#,
    )
    .unwrap();
    fs::write(
        &annotations,
        r#"{"s":{"tag":"Diagnose rejected SSH password","parent":null,"next":null}}"#,
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
    assert!(
        String::from_utf8_lossy(&result.stderr)
            .contains("operation tags must contain 1 to 3 words")
    );
    assert!(!output.exists());
}
