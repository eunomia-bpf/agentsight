// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use rusqlite::Connection;
use std::process::{Command, Output, Stdio};
use std::time::Duration;

fn enabled(name: &str) -> bool {
    std::env::var(name)
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
}

fn command_exists(name: &str) -> bool {
    Command::new("sh")
        .arg("-lc")
        .arg(format!("command -v {}", name))
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

fn sudo_available() -> bool {
    Command::new("sudo")
        .args(["-n", "true"])
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

fn run_agentsight(args: &[&str]) -> Output {
    let path = std::env::var("PATH").unwrap_or_default();
    let home = std::env::var("HOME").unwrap_or_default();
    let mut command = Command::new("sudo");
    command
        .args(["-n", "env"])
        .arg(format!("PATH={}", path))
        .arg(format!("HOME={}", home));
    for key in [
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
    ] {
        if let Ok(value) = std::env::var(key) {
            command.arg(format!("{}={}", key, value));
        }
    }
    command
        .arg(env!("CARGO_BIN_EXE_agentsight"))
        .args(args)
        .output()
        .expect("agentsight command should run")
}

fn assert_agentsight_success(output: Output, label: &str) {
    assert!(
        output.status.success(),
        "{} failed\nstdout:\n{}\nstderr:\n{}",
        label,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

fn token_total(db: &std::path::Path, source: &str) -> i64 {
    let conn = Connection::open(db).expect("db should open");
    conn.query_row(
        "SELECT COALESCE(SUM(total_tokens), 0) FROM token_usage WHERE source = ?1",
        [source],
        |row| row.get(0),
    )
    .expect("token query should run")
}

fn positive_session_total(db: &std::path::Path, agent_type: &str) -> i64 {
    let conn = Connection::open(db).expect("db should open");
    conn.query_row(
        "SELECT COALESCE(SUM(total_tokens), 0)
         FROM agent_sessions
         WHERE agent_type = ?1 AND total_tokens > 0",
        [agent_type],
        |row| row.get(0),
    )
    .expect("session query should run")
}

fn tool_call_count(db: &std::path::Path, adapter_id: &str) -> i64 {
    let conn = Connection::open(db).expect("db should open");
    conn.query_row(
        "SELECT COUNT(*) FROM tool_calls WHERE adapter_id = ?1",
        [adapter_id],
        |row| row.get(0),
    )
    .expect("tool call query should run")
}

#[test]
#[ignore = "requires sudo and an authenticated Gemini CLI"]
fn real_gemini_cli_smoke_captures_stdout_tokens() {
    if !enabled("AGENTSIGHT_REAL_CLI_SMOKE") && !enabled("AGENTSIGHT_REAL_GEMINI_SMOKE") {
        eprintln!("skipping real Gemini smoke; set AGENTSIGHT_REAL_CLI_SMOKE=1");
        return;
    }
    if !sudo_available() || !command_exists("gemini") {
        eprintln!("skipping real Gemini smoke; sudo -n or gemini CLI unavailable");
        return;
    }

    let mut last_cli_total = 0;
    let mut last_response_total = 0;
    let mut last_session_total = 0;
    for attempt in 1..=3 {
        let temp = tempfile::tempdir().expect("tempdir");
        let db = temp.path().join("gemini.db");
        let log = temp.path().join("gemini.log");
        let prompt = format!(
            "Reply with exactly: agentsight-smoke-{}-{}",
            std::process::id(),
            attempt
        );
        let output = run_agentsight(&[
            "exec",
            "--no-server",
            "--db",
            db.to_str().expect("db path"),
            "--adapter",
            "auto",
            "-o",
            log.to_str().expect("log path"),
            "--",
            "gemini",
            "--model",
            "gemini-2.5-flash-lite",
            "-p",
            &prompt,
            "--output-format",
            "json",
        ]);
        assert_agentsight_success(output, "real Gemini smoke");

        last_cli_total = token_total(&db, "gemini_cli_stdout");
        last_response_total = token_total(&db, "response_usage");
        last_session_total = positive_session_total(&db, "gemini-cli");
        if last_cli_total > 0 && last_response_total > 0 && last_session_total > 0 {
            return;
        }
        eprintln!(
            "Gemini smoke attempt {} did not capture all signals: cli={}, response={}, session={}",
            attempt, last_cli_total, last_response_total, last_session_total
        );
    }

    assert!(last_cli_total > 0);
    assert!(
        last_response_total > 0,
        "Gemini response usage should be decoded from TLS/SSE capture"
    );
    assert!(last_session_total > 0);
}

#[test]
#[ignore = "requires sudo and an authenticated Claude Code CLI"]
fn real_claude_code_smoke_captures_stdout_tokens() {
    if !enabled("AGENTSIGHT_REAL_CLI_SMOKE") && !enabled("AGENTSIGHT_REAL_CLAUDE_SMOKE") {
        eprintln!("skipping real Claude Code smoke; set AGENTSIGHT_REAL_CLI_SMOKE=1");
        return;
    }
    if !sudo_available() || !command_exists("claude") {
        eprintln!("skipping real Claude Code smoke; sudo -n or claude CLI unavailable");
        return;
    }

    let temp = tempfile::tempdir().expect("tempdir");
    let db = temp.path().join("claude.db");
    let log = temp.path().join("claude.log");
    let output = run_agentsight(&[
        "exec",
        "--no-server",
        "--db",
        db.to_str().expect("db path"),
        "--adapter",
        "auto",
        "-o",
        log.to_str().expect("log path"),
        "--",
        "claude",
        "-p",
        "Reply with exactly: agentsight-smoke",
        "--output-format",
        "json",
    ]);
    assert_agentsight_success(output, "real Claude Code smoke");
    assert!(token_total(&db, "claude_code_stdout_model_usage") > 0);
    assert!(positive_session_total(&db, "claude-code") > 0);
}

#[test]
#[ignore = "requires sudo, an authenticated Claude Code CLI, and live tool use"]
fn real_claude_code_tool_use_smoke_captures_tool_calls() {
    if !enabled("AGENTSIGHT_REAL_CLAUDE_TOOL_SMOKE") {
        eprintln!("skipping real Claude tool-use smoke; set AGENTSIGHT_REAL_CLAUDE_TOOL_SMOKE=1");
        return;
    }
    if !sudo_available() || !command_exists("claude") {
        eprintln!("skipping real Claude tool-use smoke; sudo -n or claude CLI unavailable");
        return;
    }

    let temp = tempfile::tempdir().expect("tempdir");
    let db = temp.path().join("claude-tool.db");
    let log = temp.path().join("claude-tool.log");
    let output = run_agentsight(&[
        "exec",
        "--no-server",
        "--db",
        db.to_str().expect("db path"),
        "--adapter",
        "auto",
        "-o",
        log.to_str().expect("log path"),
        "--",
        "claude",
        "-p",
        "Use the Bash tool exactly once to run `printf agentsight-tool-smoke`; then reply with the output.",
        "--output-format",
        "json",
        "--allowedTools",
        "Bash",
    ]);
    assert_agentsight_success(output, "real Claude Code tool-use smoke");
    assert!(positive_session_total(&db, "claude-code") > 0);
    assert!(
        tool_call_count(&db, "claude-code") > 0,
        "Claude Code tool-use smoke should project at least one tool call"
    );
}

#[test]
#[ignore = "requires sudo, Docker, and real OpenClaw provider credentials"]
fn real_openclaw_provider_smoke_captures_http_tokens() {
    if !enabled("AGENTSIGHT_REAL_OPENCLAW_SMOKE") {
        eprintln!("skipping real OpenClaw smoke; set AGENTSIGHT_REAL_OPENCLAW_SMOKE=1");
        return;
    }
    if !sudo_available() || !command_exists("docker") {
        eprintln!("skipping real OpenClaw smoke; sudo -n or docker unavailable");
        return;
    }

    let api_key = std::env::var("OPENAI_API_KEY")
        .or_else(|_| std::env::var("OPENCLAW_LIVE_OPENAI_KEY"))
        .expect("OPENAI_API_KEY or OPENCLAW_LIVE_OPENAI_KEY is required");
    let image = std::env::var("OPENCLAW_SMOKE_IMAGE")
        .unwrap_or_else(|_| "ghcr.io/openclaw/openclaw:latest".to_string());
    let model =
        std::env::var("OPENCLAW_SMOKE_MODEL").unwrap_or_else(|_| "openai/gpt-4.1-mini".into());
    let container = format!("agentsight-openclaw-smoke-{}", std::process::id());
    let _ = Command::new("docker")
        .args(["rm", "-f", &container])
        .output();

    let start_script = r#"printf '%s\n' "$OPENAI_API_KEY" | node openclaw.mjs models auth paste-api-key --provider openai-codex >/tmp/openclaw-auth.log && exec node openclaw.mjs gateway run --allow-unconfigured --auth none --bind loopback --port 19001 --force --raw-stream --raw-stream-path /tmp/openclaw-raw.jsonl"#;
    let start = Command::new("docker")
        .env("OPENAI_API_KEY", api_key)
        .args([
            "run",
            "-d",
            "--name",
            &container,
            "-e",
            "OPENAI_API_KEY",
            &image,
            "sh",
            "-lc",
            start_script,
        ])
        .output()
        .expect("docker run should execute");
    assert_agentsight_success(start, "start OpenClaw container");

    std::thread::sleep(Duration::from_secs(8));
    let temp = tempfile::tempdir().expect("tempdir");
    let db = temp.path().join("openclaw.db");
    let log = temp.path().join("openclaw.log");
    let path = std::env::var("PATH").unwrap_or_default();
    let home = std::env::var("HOME").unwrap_or_default();
    let mut trace = Command::new("sudo")
        .args(["-n", "env"])
        .arg(format!("PATH={}", path))
        .arg(format!("HOME={}", home))
        .arg(env!("CARGO_BIN_EXE_agentsight"))
        .args([
            "trace",
            "-q",
            "-c",
            "node",
            "--binary-path",
            &format!("docker://{}", container),
            "--db",
            db.to_str().expect("db path"),
            "--adapter",
            "auto",
            "-o",
            log.to_str().expect("log path"),
        ])
        .spawn()
        .expect("agentsight trace should spawn");
    let trace_pid = trace.id();

    std::thread::sleep(Duration::from_secs(6));
    let trigger = Command::new("timeout")
        .arg("120s")
        .arg("docker")
        .args([
            "exec",
            &container,
            "node",
            "openclaw.mjs",
            "infer",
            "model",
            "run",
            "--local",
            "--json",
            "--model",
            &model,
            "--prompt",
            "OpenClaw gateway smoke. Reply with exactly: agentsight-smoke",
        ])
        .output()
        .expect("docker exec should run");

    let _ = Command::new("sudo")
        .args(["-n", "kill", "-INT", &trace_pid.to_string()])
        .output();
    let trace_status = trace.wait().expect("trace should finish");
    let _ = Command::new("docker")
        .args(["rm", "-f", &container])
        .output();

    assert_agentsight_success(trigger, "trigger OpenClaw inference");
    assert!(trace_status.success(), "agentsight trace failed");
    assert!(positive_session_total(&db, "openclaw") > 0);
}
