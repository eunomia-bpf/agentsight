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
use crate::output::{
    SessionSummary, print_record_attribution_session, print_record_auto_binary_path,
    print_record_drop_user, print_record_header, print_record_kill_error, print_record_launch,
    print_record_monitoring_stream_ended, print_record_provided_binary_path,
    print_record_session_db_error, print_record_session_summary, print_record_shutdown,
    print_record_sudo_prompt, print_record_target_exited, print_record_target_shutdown_error,
    print_record_target_status_error, print_record_target_wait_error, print_record_web_ui,
};
use crate::runners::{Runner, RunnerError};
use crate::sources::session_db::sessions_dir;
use crate::view::MaterializedView;

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
    let dir = sessions_dir()
        .ok_or_else(|| RunnerError::from("cannot determine home directory for session DB"))?;
    std::fs::create_dir_all(&dir).map_err(|e| {
        RunnerError::from(format!(
            "failed to create session directory {}: {}",
            dir.display(),
            e
        ))
    })?;
    let ts = chrono::Local::now().format("%Y%m%d-%H%M%S");
    Ok(dir.join(format!("{}.db", ts)).to_string_lossy().to_string())
}

pub(crate) fn print_session_summary(db_path: &str) {
    let Ok(view) = load_agentsight_view(Some(db_path)) else {
        return;
    };
    if let Ok(summary) = SessionSummary::from_view(&view) {
        print_record_session_summary(&summary);
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
            Ok(p) => {
                crate::sources::session_db::cleanup_old_sessions();
                Some(p)
            }
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
    let mut cfg = TraceConfig {
        pid: Some(child_pid),
        session_id: Some(child_pid),
        stdio: true,
        binary_path: ssl_binary_path,
        db_path,
        server_listen: Some(server_listen.to_string()),
        ..TraceConfig::for_record()
    };

    prepare_process_seeds(&mut cfg)?;
    let live_view = MaterializedView::shared_bounded();
    let mut agent = build_trace_agent_with_view(binary_extractor, &cfg, live_view.clone())?;

    let server_handle =
        start_web_server_if_enabled(enable_server, server_listen, server_port, live_view, None)
            .await
            .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = match agent.run().await {
        Ok(stream) => stream,
        Err(e) => {
            stop_child(&mut child).await;
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
        return Err(e);
    }

    let shutdown = crate::shutdown_notify();
    let mut target_exited = false;
    // Consume events and watch for the child to exit, whichever happens.
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(event) => {
                        if let Some(error) = crate::runners::common::runner_error_from_event(&event) {
                            stop_child(&mut child).await;
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
                        print_record_target_exited(s);
                    }
                    Err(e) => print_record_target_wait_error(e),
                }
                target_exited = true;
                drain_stream_for(&mut stream, tokio::time::Duration::from_millis(5000)).await?;
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
