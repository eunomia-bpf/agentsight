// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use futures::stream::StreamExt;

use crate::analyzers::{print_global_http_filter_metrics, print_global_ssl_filter_metrics};
use crate::binary_extractor::BinaryExtractor;
use crate::binary_resolver::{binary_embeds_ssl, resolve_binary_path};
use crate::cli_db::load_agentsight_view;
use crate::cmd_trace::{
    TraceConfig, build_trace_agent_with_view, drain_stream_for, prepare_process_seeds,
    start_web_server_if_enabled,
};
use crate::model::{SessionRow, ToolCallRow, ViewResult, ViewSink};
use crate::output::{
    SessionSummary, print_record_attribution_session, print_record_auto_binary_path,
    print_record_drop_user, print_record_header, print_record_kill_error, print_record_launch,
    print_record_monitoring_stream_ended, print_record_provided_binary_path,
    print_record_session_db_error, print_record_session_summary, print_record_shutdown,
    print_record_sudo_prompt, print_record_target_exited, print_record_target_shutdown_error,
    print_record_target_status_error, print_record_target_wait_error, print_record_web_ui,
};
use crate::runners::{Runner, RunnerError};
use crate::sinks::sqlite::SqliteStore;
use crate::view::MaterializedView;
use serde_json::{Value, json};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

const RECORD_AGENT_ENVELOPE_SOURCE: &str = "record_capture_time_agent_envelope";

#[derive(Debug, Clone)]
struct RecordAgentEnvelope {
    session_id: String,
    tool_id: String,
    pid: u32,
    agent_type: String,
    command: Vec<String>,
    start_timestamp_ms: u64,
}

/// Launch a target command and automatically trace it with eBPF.
///
/// This is the zero-configuration entry point: it discovers the target's real
/// ELF binary (for SSL uprobe attachment), derives the process `--comm` filter
/// from the command name, starts SSL + process + system monitoring in the
/// background (quiet, so the child owns the terminal), then spawns the child.
/// Monitoring stops automatically when the child exits.
pub(crate) fn target_user_ids() -> Option<(libc::uid_t, libc::gid_t)> {
    if unsafe { libc::geteuid() } != 0 {
        return None;
    }
    let uid = std::env::var("SUDO_UID").ok()?.parse().ok()?;
    let gid = std::env::var("SUDO_GID").ok()?.parse().ok()?;
    Some((uid, gid))
}

pub(crate) fn sudo_cached() -> bool {
    std::process::Command::new("sudo")
        .args(["-n", "true"])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

pub(crate) fn default_session_db_path() -> Result<String, RunnerError> {
    let dir = std::env::current_dir()
        .map_err(|e| RunnerError::from(format!("cannot determine current directory: {e}")))?;
    let ts = chrono::Local::now().format("%Y%m%d-%H%M%S");
    Ok(session_db_path_for_dir(&dir, ts)
        .to_string_lossy()
        .to_string())
}

fn session_db_path_for_dir(
    dir: &std::path::Path,
    timestamp: impl std::fmt::Display,
) -> std::path::PathBuf {
    dir.join(format!("agentsight-{timestamp}.db"))
}

pub(crate) fn print_session_summary(db_path: &str) {
    let Ok(view) = load_agentsight_view(Some(db_path)) else {
        return;
    };
    if let Ok(summary) = SessionSummary::from_view(&view) {
        print_record_session_summary(db_path, &summary);
    }
}

pub(crate) async fn run_exec(
    binary_extractor: &BinaryExtractor,
    command: &[String],
    binary_path_override: Option<&str>,
    db_path: Option<String>,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
    print_summary: bool,
) -> Result<Option<String>, RunnerError> {
    let program = command.first().ok_or_else(|| {
        RunnerError::from("record requires a command to run, e.g. `agentsight record -- claude`")
    })?;
    let prog_args = &command[1..];

    // Auto-create a session database when the user didn't specify --db.
    let db_path = if db_path.is_some() {
        db_path
    } else {
        match default_session_db_path() {
            Ok(p) => Some(p),
            Err(e) => {
                print_record_session_db_error(e);
                None
            }
        }
    };

    print_record_header();

    let binary_path = match binary_path_override {
        Some(p) => {
            print_record_provided_binary_path(p);
            p.to_string()
        }
        None => {
            let p = resolve_binary_path(program).map_err(|e| {
                RunnerError::from(format!("failed to resolve '{}': {}", program, e))
            })?;
            print_record_auto_binary_path(&p);
            p
        }
    };
    let ssl_binary_path = if binary_path_override.is_some() || binary_embeds_ssl(&binary_path) {
        Some(binary_path)
    } else {
        None
    };

    // When not running as root, warm the sudo credential cache so the
    // user is prompted once (with a visible terminal) before eBPF binaries
    // are spawned with piped stdio.  Skip if passwordless sudo already works.
    if unsafe { libc::geteuid() } != 0 && !sudo_cached() {
        print_record_sudo_prompt();
        let ok = std::process::Command::new("sudo")
            .arg("true")
            .status()
            .map(|s| s.success())
            .unwrap_or(false);
        if !ok {
            return Err(RunnerError::from(
                "sudo authentication failed. Either run as root (`sudo -E agentsight record -- ...`) \
                 or grant your user passwordless sudo for the eBPF binaries.",
            ));
        }
    }

    let mut command_builder = tokio::process::Command::new("/bin/sh");
    command_builder
        .arg("-c")
        .arg("target=$1; shift; kill -STOP $$; exec \"$target\" \"$@\"")
        .arg("agentsight-target")
        .arg(program)
        .args(prog_args);
    let target_ids = target_user_ids();
    if let Some((uid, gid)) = target_ids {
        print_record_drop_user(uid, gid);
    }
    unsafe {
        command_builder.pre_exec(move || {
            if let Some((uid, gid)) = target_ids {
                if libc::setgid(gid) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                if libc::setuid(uid) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
            }
            if libc::setsid() < 0 {
                return Err(std::io::Error::last_os_error());
            }
            Ok(())
        });
    }

    let mut child = command_builder
        .spawn()
        .map_err(|e| RunnerError::from(format!("failed to launch '{}': {}", program, e)))?;
    let child_pid = child
        .id()
        .ok_or_else(|| RunnerError::from("failed to get target child PID"))?;
    print_record_attribution_session(child_pid);

    let db_path_for_summary = db_path.clone();
    let capture_envelope = db_path_for_summary.as_deref().and_then(|db| {
        match persist_record_agent_envelope_start(db, child_pid, command) {
            Ok(envelope) => Some(envelope),
            Err(error) => {
                log::warn!(
                    "failed to persist capture-time agent envelope to '{}': {}",
                    db,
                    error
                );
                None
            }
        }
    });
    let mut cfg = TraceConfig {
        pid: Some(child_pid),
        session_id: Some(child_pid),
        stdio: true,
        binary_path: ssl_binary_path,
        db_path,
        server_listen: Some(server_listen.to_string()),
        ..TraceConfig::for_record()
    };

    if let Err(error) = prepare_process_seeds(&mut cfg) {
        update_record_agent_envelope_status(
            db_path_for_summary.as_deref(),
            capture_envelope.as_ref(),
            "failed",
            None,
        );
        stop_child(&mut child).await;
        return Err(error);
    }
    let live_view = MaterializedView::shared_bounded();
    let mut agent = match build_trace_agent_with_view(binary_extractor, &cfg, live_view.clone()) {
        Ok(agent) => agent,
        Err(error) => {
            update_record_agent_envelope_status(
                db_path_for_summary.as_deref(),
                capture_envelope.as_ref(),
                "failed",
                None,
            );
            stop_child(&mut child).await;
            return Err(error);
        }
    };

    let server_handle = match start_web_server_if_enabled(
        enable_server,
        server_listen,
        server_port,
        live_view,
        None,
    )
    .await
    {
        Ok(handle) => handle,
        Err(error) => {
            update_record_agent_envelope_status(
                db_path_for_summary.as_deref(),
                capture_envelope.as_ref(),
                "failed",
                None,
            );
            stop_child(&mut child).await;
            return Err(RunnerError::from(format!(
                "Failed to start server: {}",
                error
            )));
        }
    };

    let mut stream = match agent.run().await {
        Ok(stream) => stream,
        Err(e) => {
            stop_child(&mut child).await;
            update_record_agent_envelope_status(
                db_path_for_summary.as_deref(),
                capture_envelope.as_ref(),
                "failed",
                None,
            );
            return Err(e);
        }
    };

    if let Some(server) = &server_handle {
        print_record_web_ui(&server.url);
    }
    print_record_launch(command);

    tokio::time::sleep(tokio::time::Duration::from_millis(250)).await;
    if let Err(e) = continue_child(child_pid) {
        stop_child(&mut child).await;
        update_record_agent_envelope_status(
            db_path_for_summary.as_deref(),
            capture_envelope.as_ref(),
            "failed",
            None,
        );
        return Err(e);
    }

    let shutdown = crate::shutdown_notify();
    let mut target_exited = false;
    let mut target_exit_code = None;
    // Consume events and watch for the child to exit, whichever happens.
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(event) => {
                        if let Some(error) = crate::runners::common::runner_error_from_event(&event) {
                            stop_child(&mut child).await;
                            update_record_agent_envelope_status(
                                db_path_for_summary.as_deref(),
                                capture_envelope.as_ref(),
                                "failed",
                                None,
                            );
                            return Err(error);
                        }
                    }
                    None => {
                        print_record_monitoring_stream_ended();
                        break;
                    }
                }
            }
            status = child.wait() => {
                match status {
                    Ok(s) => {
                        target_exit_code = s.code();
                        print_record_target_exited(s);
                    }
                    Err(e) => print_record_target_wait_error(e),
                }
                target_exited = true;
                if let Err(error) = drain_stream_for(&mut stream, tokio::time::Duration::from_millis(5000)).await {
                    update_record_agent_envelope_status(
                        db_path_for_summary.as_deref(),
                        capture_envelope.as_ref(),
                        "failed",
                        target_exit_code,
                    );
                    return Err(error);
                }
                break;
            }
            _ = shutdown.notified() => {
                print_record_shutdown();
                break;
            }
        }
    }
    if !target_exited {
        stop_child(&mut child).await;
    }
    drop(stream);
    drop(agent);

    let status = match (target_exited, target_exit_code) {
        (true, Some(0)) => "completed",
        (true, _) => "failed",
        (false, _) => "interrupted",
    };
    update_record_agent_envelope_status(
        db_path_for_summary.as_deref(),
        capture_envelope.as_ref(),
        status,
        target_exit_code,
    );

    print_global_http_filter_metrics();
    print_global_ssl_filter_metrics();
    if print_summary && let Some(ref db) = db_path_for_summary {
        print_session_summary(db);
    }

    Ok(db_path_for_summary)
}

fn continue_child(pid: u32) -> Result<(), RunnerError> {
    let result = unsafe { libc::kill(pid as libc::pid_t, libc::SIGCONT) };
    if result == 0 {
        Ok(())
    } else {
        Err(RunnerError::from(format!(
            "failed to continue target process {}: {}",
            pid,
            std::io::Error::last_os_error()
        )))
    }
}

pub(crate) async fn stop_child(child: &mut tokio::process::Child) {
    match child.try_wait() {
        Ok(Some(_)) => return,
        Ok(None) => {}
        Err(e) => {
            print_record_target_status_error(e);
            return;
        }
    }

    match tokio::time::timeout(tokio::time::Duration::from_secs(2), child.wait()).await {
        Ok(Ok(_)) => return,
        Ok(Err(e)) => {
            print_record_target_shutdown_error(e);
            return;
        }
        Err(_) => {}
    }

    if let Err(e) = child.kill().await {
        print_record_kill_error(e);
    }
}

fn persist_record_agent_envelope_start(
    path: impl AsRef<Path>,
    pid: u32,
    command: &[String],
) -> ViewResult<RecordAgentEnvelope> {
    let envelope = record_agent_envelope(pid, command, epoch_ms_now());
    let (session, tool) = record_agent_envelope_rows(&envelope, None, "running", Value::Null);
    let mut store = SqliteStore::open(path)?;
    ViewSink::session(&mut store, &session)?;
    ViewSink::tool_call(&mut store, &tool)?;
    Ok(envelope)
}

fn persist_record_agent_envelope_end(
    path: impl AsRef<Path>,
    envelope: &RecordAgentEnvelope,
    end_timestamp_ms: u64,
    status: &str,
    exit_code: Option<i32>,
) -> ViewResult<()> {
    let output = json!({
        "exit_code": exit_code,
        "status": status,
    });
    let (session, tool) =
        record_agent_envelope_rows(envelope, Some(end_timestamp_ms), status, output);
    let mut store = SqliteStore::open(path)?;
    ViewSink::session(&mut store, &session)?;
    ViewSink::tool_call(&mut store, &tool)?;
    Ok(())
}

fn update_record_agent_envelope_status(
    db_path: Option<&str>,
    envelope: Option<&RecordAgentEnvelope>,
    status: &str,
    exit_code: Option<i32>,
) {
    let (Some(db), Some(envelope)) = (db_path, envelope) else {
        return;
    };
    if let Err(error) =
        persist_record_agent_envelope_end(db, envelope, epoch_ms_now(), status, exit_code)
    {
        log::warn!(
            "failed to update capture-time agent envelope in '{}': {}",
            db,
            error
        );
    }
}

fn record_agent_envelope(
    pid: u32,
    command: &[String],
    start_timestamp_ms: u64,
) -> RecordAgentEnvelope {
    let agent_type = command
        .first()
        .and_then(|program| {
            Path::new(program)
                .file_name()
                .and_then(|name| name.to_str())
                .map(ToString::to_string)
        })
        .filter(|name| !name.is_empty())
        .unwrap_or_else(|| "agent".to_string());
    let safe_agent = sanitize_record_id(&agent_type);
    let session_id = format!("record:{safe_agent}:{pid}:{start_timestamp_ms}");
    let tool_id = format!("{session_id}:agent-run");
    RecordAgentEnvelope {
        session_id,
        tool_id,
        pid,
        agent_type,
        command: command.to_vec(),
        start_timestamp_ms,
    }
}

fn record_agent_envelope_rows(
    envelope: &RecordAgentEnvelope,
    end_timestamp_ms: Option<u64>,
    status: &str,
    output: Value,
) -> (SessionRow, ToolCallRow) {
    let duration_ms = end_timestamp_ms.map(|end| end.saturating_sub(envelope.start_timestamp_ms));
    let command_string = shell_words(&envelope.command);
    let input = json!({
        "command": &command_string,
        "argv": &envelope.command,
        "capture_mode": "record_command",
        "prompt_tag": "record",
    });
    let attributes = json!({
        "root_pid": envelope.pid,
        "command": &command_string,
        "argv": &envelope.command,
        "capture_mode": "record_command",
        "session_tag": &envelope.agent_type,
        "cwd": std::env::current_dir()
            .ok()
            .map(|path| path.to_string_lossy().to_string()),
    });
    let session = SessionRow {
        id: envelope.session_id.clone(),
        agent_type: envelope.agent_type.clone(),
        start_timestamp_ms: envelope.start_timestamp_ms,
        end_timestamp_ms,
        status: status.to_string(),
        model: None,
        input_tokens: 0,
        output_tokens: 0,
        total_tokens: 0,
        view_source: RECORD_AGENT_ENVELOPE_SOURCE.to_string(),
        confidence: Some(0.95),
        attributes,
    };
    let tool = ToolCallRow {
        id: envelope.tool_id.clone(),
        session_id: Some(envelope.session_id.clone()),
        conversation_id: None,
        timestamp_ms: envelope.start_timestamp_ms,
        tool_name: Some("agent-run".to_string()),
        tool_call_id: Some(envelope.tool_id.clone()),
        start_timestamp_ms: Some(envelope.start_timestamp_ms),
        end_timestamp_ms,
        duration_ms,
        status: Some(status.to_string()),
        input,
        output,
        related_pid: Some(envelope.pid),
        related_event_id: None,
        view_source: RECORD_AGENT_ENVELOPE_SOURCE.to_string(),
        confidence: Some(0.95),
    };
    (session, tool)
}

fn shell_words(command: &[String]) -> String {
    command.join(" ")
}

fn sanitize_record_id(value: &str) -> String {
    let safe = value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || matches!(ch, ':' | '-' | '_' | '.') {
                ch
            } else {
                '_'
            }
        })
        .collect::<String>()
        .trim_matches('_')
        .to_string();
    if safe.is_empty() {
        "agent".to_string()
    } else {
        safe
    }
}

fn epoch_ms_now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sources::sqlite::load_view;

    #[test]
    fn default_record_db_path_uses_current_directory_style_name() {
        let path =
            session_db_path_for_dir(std::path::Path::new("/work/project"), "20260616-161500");
        assert_eq!(
            path,
            std::path::PathBuf::from("/work/project/agentsight-20260616-161500.db")
        );
    }

    #[test]
    fn record_agent_envelope_start_and_end_persist_to_sqlite() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("record-envelope.db");
        let command = vec![
            "/usr/bin/codex".to_string(),
            "exec".to_string(),
            "fix tests".to_string(),
        ];

        let envelope = persist_record_agent_envelope_start(&db, 4242, &command).unwrap();
        persist_record_agent_envelope_end(
            &db,
            &envelope,
            envelope.start_timestamp_ms + 1_250,
            "completed",
            Some(0),
        )
        .unwrap();

        let view = load_view(&db).unwrap();
        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 100 });
        assert_eq!(snapshot.sessions.len(), 1);
        assert_eq!(snapshot.sessions[0].id, envelope.session_id);
        assert_eq!(snapshot.sessions[0].agent_type, "codex");
        assert_eq!(snapshot.sessions[0].status, "completed");
        assert_eq!(
            snapshot.sessions[0].view_source,
            RECORD_AGENT_ENVELOPE_SOURCE
        );
        assert_eq!(
            snapshot.sessions[0]
                .attributes
                .get("root_pid")
                .and_then(Value::as_u64),
            Some(4242)
        );

        assert_eq!(snapshot.tool_calls.len(), 1);
        let tool = &snapshot.tool_calls[0];
        assert_eq!(
            tool.session_id.as_deref(),
            Some(snapshot.sessions[0].id.as_str())
        );
        assert_eq!(tool.related_pid, Some(4242));
        assert_eq!(tool.status.as_deref(), Some("completed"));
        assert_eq!(tool.duration_ms, Some(1_250));
        assert_eq!(
            tool.input.get("prompt_tag").and_then(Value::as_str),
            Some("record")
        );
        assert_eq!(
            tool.output.get("exit_code").and_then(Value::as_i64),
            Some(0)
        );
    }

    #[test]
    fn record_agent_envelope_sanitizes_program_name() {
        let envelope =
            record_agent_envelope(7, &["/tmp/my agent".to_string(), "--flag".to_string()], 123);
        assert_eq!(envelope.agent_type, "my agent");
        assert_eq!(envelope.session_id, "record:my_agent:7:123");
    }
}
