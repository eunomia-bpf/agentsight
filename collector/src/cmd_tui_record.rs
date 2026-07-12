// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::binary_extractor::BinaryExtractor;
use crate::cmd_trace::{TraceConfig, run_trace_silent_until_cancel};
use crate::output::AgentTopRow;
use chrono::Local;
use std::sync::{Arc, Mutex};
use tokio::sync::oneshot;
use tokio::task::JoinHandle;
use tokio::time::Duration;

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct TuiRecordCommand {
    pub(crate) pid: u32,
    pub(crate) binary_path: Option<String>,
    pub(crate) db_path: String,
    pub(crate) server: bool,
    pub(crate) server_port: u16,
}

impl TuiRecordCommand {
    pub(crate) fn display_command(&self) -> String {
        let mut parts = vec![
            "agentsight".to_string(),
            "record".to_string(),
            "-p".to_string(),
            self.pid.to_string(),
        ];
        if let Some(path) = &self.binary_path {
            parts.extend(["--binary-path".to_string(), path.clone()]);
        }
        parts.extend(["--db".to_string(), self.db_path.clone()]);
        if self.server {
            parts.extend(["--server-port".to_string(), self.server_port.to_string()]);
        } else {
            parts.push("--no-server".to_string());
        }
        parts.join(" ")
    }

    fn trace_config(&self, listen: &str) -> TraceConfig {
        TraceConfig {
            pid: Some(self.pid),
            stdio: true,
            binary_path: self.binary_path.clone(),
            db_path: Some(self.db_path.clone()),
            server: self.server,
            server_listen: Some(listen.to_string()),
            server_port: self.server_port,
            ..TraceConfig::for_record()
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct TuiRecordStatus {
    pub(crate) target: String,
    pub(crate) db_path: String,
    pub(crate) server_url: Option<String>,
    pub(crate) message: String,
    pub(crate) finished: bool,
}

pub(crate) struct TuiRecordTask {
    status: Arc<Mutex<TuiRecordStatus>>,
    cancel: Option<oneshot::Sender<()>>,
    handle: Option<JoinHandle<()>>,
}

impl TuiRecordTask {
    pub(crate) fn spawn(command: TuiRecordCommand, listen: String) -> Self {
        let status = Arc::new(Mutex::new(TuiRecordStatus {
            target: format!("pid {}", command.pid),
            db_path: command.db_path.clone(),
            server_url: None,
            message: "starting".to_string(),
            finished: false,
        }));
        let task_status = status.clone();
        let (cancel_tx, cancel_rx) = oneshot::channel();
        if command.server {
            set_status(&status, |status| {
                status.server_url = Some(default_server_url(&listen, command.server_port));
            });
        }
        let handle = tokio::spawn(async move {
            let result = async {
                let extractor = BinaryExtractor::new()
                    .await
                    .map_err(|e| format!("failed to extract eBPF binaries: {e}"))?;
                set_status(&task_status, |status| {
                    status.message = "recording".to_string()
                });
                run_trace_silent_until_cancel(&extractor, command.trace_config(&listen), cancel_rx)
                    .await
                    .map_err(|e| e.to_string())
            }
            .await;

            match result {
                Ok(server_url) => set_status(&task_status, |status| {
                    if server_url.is_some() {
                        status.server_url = server_url;
                    }
                    status.message = "stopped".to_string();
                    status.finished = true;
                }),
                Err(error) => set_status(&task_status, |status| {
                    status.message = format!("error: {error}");
                    status.finished = true;
                }),
            }
        });

        Self {
            status,
            cancel: Some(cancel_tx),
            handle: Some(handle),
        }
    }

    pub(crate) fn status(&self) -> TuiRecordStatus {
        self.status
            .lock()
            .map(|status| status.clone())
            .unwrap_or_else(|_| TuiRecordStatus {
                target: "record".to_string(),
                db_path: "-".to_string(),
                server_url: None,
                message: "status unavailable".to_string(),
                finished: true,
            })
    }

    pub(crate) fn stop(&mut self) {
        if let Some(cancel) = self.cancel.take() {
            let _ = cancel.send(());
        }
        set_status(&self.status, |status| {
            if !status.finished {
                status.message = "stopping".to_string();
            }
        });
    }

    pub(crate) async fn shutdown(mut self, wait: Duration) {
        self.stop();
        let Some(mut handle) = self.handle.take() else {
            return;
        };
        if handle.is_finished() {
            let _ = handle.await;
            return;
        }
        let wait = tokio::time::sleep(wait);
        tokio::pin!(wait);
        tokio::select! {
            join_result = &mut handle => {
                let _ = join_result;
            }
            _ = &mut wait => {
                // The trace task should normally exit after cancellation. Abort on
                // timeout so top does not leave an orphaned background capture.
                handle.abort();
                let _ = handle.await;
                set_status(&self.status, |status| {
                    if !status.finished {
                        status.message = "stopped".to_string();
                        status.finished = true;
                    }
                });
            }
        }
    }

    pub(crate) fn shutdown_blocking(self, wait: Duration) {
        if let Ok(handle) = tokio::runtime::Handle::try_current() {
            tokio::task::block_in_place(|| handle.block_on(self.shutdown(wait)));
        } else if let Ok(runtime) = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
        {
            runtime.block_on(self.shutdown(wait));
        }
    }

    pub(crate) fn is_finished(&self) -> bool {
        self.handle
            .as_ref()
            .is_none_or(|handle| handle.is_finished())
            || self.status().finished
    }
}

impl Drop for TuiRecordTask {
    fn drop(&mut self) {
        self.stop();
    }
}

fn default_server_url(listen: &str, port: u16) -> String {
    let listen = if listen.trim().is_empty() {
        crate::cmd_trace::DEFAULT_SERVER_LISTEN
    } else {
        listen.trim()
    };
    let host = if listen == "0.0.0.0" || listen == "::" {
        "127.0.0.1"
    } else {
        listen
    };
    format!("http://{}:{}/", host, port)
}

fn set_status(status: &Arc<Mutex<TuiRecordStatus>>, update: impl FnOnce(&mut TuiRecordStatus)) {
    if let Ok(mut status) = status.lock() {
        update(&mut status);
    }
}

pub(crate) fn default_record_command_for_row(
    row: Option<&AgentTopRow>,
    server_port: u16,
) -> Result<TuiRecordCommand, String> {
    let row = row.ok_or_else(|| "no selected session to record".to_string())?;
    let pid = row
        .pid
        .ok_or_else(|| "selected session has no PID; record requires a live process".to_string())?;
    Ok(TuiRecordCommand {
        pid,
        binary_path: None,
        db_path: default_tui_record_db_path(),
        server: true,
        server_port,
    })
}

fn default_tui_record_db_path() -> String {
    format!("agentsight-{}.db", Local::now().format("%Y%m%d-%H%M%S"))
}

pub(crate) fn parse_tui_record_command(input: &str) -> Result<TuiRecordCommand, String> {
    let mut tokens: Vec<&str> = input.split_whitespace().collect();
    if tokens.first() == Some(&"agentsight") {
        tokens.remove(0);
    }
    if tokens.first() == Some(&"record") {
        tokens.remove(0);
    }
    if tokens.contains(&"--") {
        return Err(
            "TUI record accepts space-separated attach options only, not `record -- <command>`"
                .to_string(),
        );
    }

    let mut pid = None;
    let mut binary_path = None;
    let mut db_path = None;
    let mut server = true;
    let mut server_port = 7395u16;
    let mut i = 0usize;
    while i < tokens.len() {
        match tokens[i] {
            "-p" | "--pid" => {
                i += 1;
                let value = tokens
                    .get(i)
                    .ok_or_else(|| "missing value for --pid".to_string())?;
                pid = Some(
                    value
                        .parse::<u32>()
                        .map_err(|_| format!("invalid pid: {value}"))?,
                );
            }
            "--binary-path" => {
                i += 1;
                let value = tokens
                    .get(i)
                    .ok_or_else(|| "missing value for --binary-path".to_string())?;
                binary_path = Some((*value).to_string());
            }
            "--db" => {
                i += 1;
                let value = tokens
                    .get(i)
                    .ok_or_else(|| "missing value for --db".to_string())?;
                db_path = Some((*value).to_string());
            }
            "--no-server" => server = false,
            "--server-port" => {
                i += 1;
                let value = tokens
                    .get(i)
                    .ok_or_else(|| "missing value for --server-port".to_string())?;
                server_port = value
                    .parse::<u16>()
                    .map_err(|_| format!("invalid server port: {value}"))?;
            }
            "-c" | "--comm" => {
                return Err(
                    "TUI record accepts PID attach options only; use record -c outside top"
                        .to_string(),
                );
            }
            other => return Err(format!("unsupported attach option: {other}")),
        }
        i += 1;
    }

    Ok(TuiRecordCommand {
        pid: pid.ok_or_else(|| "record command requires -p/--pid".to_string())?,
        binary_path,
        db_path: db_path.ok_or_else(|| "record command requires --db".to_string())?,
        server,
        server_port,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::output::AgentTopRow;
    use tokio::time::Duration;

    fn row(pid: Option<u32>) -> AgentTopRow {
        AgentTopRow {
            pid,
            ..AgentTopRow::default()
        }
    }

    #[test]
    fn default_record_command_uses_selected_pid() {
        let command = default_record_command_for_row(Some(&row(Some(42))), 7395).unwrap();
        assert_eq!(command.pid, 42);
        assert!(command.display_command().contains("record -p 42"));
    }

    #[test]
    fn default_record_command_rejects_missing_pid() {
        let error = default_record_command_for_row(Some(&row(None)), 7395).unwrap_err();
        assert!(error.contains("no PID"));
    }

    #[test]
    fn parse_allowed_attach_options() {
        let command = parse_tui_record_command(
            "agentsight record -p 42 --binary-path /bin/node --db out.db --no-server --server-port 7400",
        )
        .unwrap();
        assert_eq!(command.pid, 42);
        assert_eq!(command.binary_path.as_deref(), Some("/bin/node"));
        assert_eq!(command.db_path, "out.db");
        assert!(!command.server);
        assert_eq!(command.server_port, 7400);
    }

    #[test]
    fn parse_rejects_comm_and_launch_command() {
        assert!(parse_tui_record_command("record -c claude --db out.db").is_err());
        assert!(parse_tui_record_command("record -p 1 --db out.db -- claude").is_err());
    }

    #[test]
    fn parse_rejects_missing_values_unknown_options_and_missing_pid() {
        assert!(parse_tui_record_command("record -p --db out.db").is_err());
        assert!(parse_tui_record_command("record -p 1 --bogus --db out.db").is_err());
        assert!(parse_tui_record_command("record --db out.db").is_err());
    }

    #[tokio::test]
    async fn shutdown_sends_cancel_and_marks_stopping() {
        let status = Arc::new(Mutex::new(TuiRecordStatus {
            target: "pid 42".to_string(),
            db_path: "out.db".to_string(),
            server_url: None,
            message: "recording".to_string(),
            finished: false,
        }));
        let (cancel_tx, cancel_rx) = oneshot::channel();
        let task_status = status.clone();
        let handle = tokio::spawn(async move {
            let _ = cancel_rx.await;
            set_status(&task_status, |status| {
                status.finished = true;
            });
        });
        let task = TuiRecordTask {
            status: status.clone(),
            cancel: Some(cancel_tx),
            handle: Some(handle),
        };

        task.shutdown(Duration::from_millis(100)).await;

        let status = status.lock().unwrap().clone();
        assert!(status.finished);
        assert!(matches!(status.message.as_str(), "stopping" | "stopped"));
    }
}
