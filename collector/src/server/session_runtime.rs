// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::AgentSession;
use serde_json::{Value, json};
use std::collections::HashMap;
use std::path::Path;
use std::process::Stdio;
use std::sync::{Arc, Mutex as StdMutex, OnceLock};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::Mutex;

use crate::view::live_top::LiveView;

static RUNTIMES: OnceLock<Mutex<HashMap<String, Runtime>>> = OnceLock::new();

fn runtimes() -> &'static Mutex<HashMap<String, Runtime>> {
    RUNTIMES.get_or_init(|| Mutex::new(HashMap::new()))
}

#[derive(Debug)]
pub enum SubmitError {
    Conflict(String),
    Failed(String),
}

pub struct SubmitResult {
    pub transport: &'static str,
}

enum Runtime {
    Claude {
        child: Child,
        stdin: ChildStdin,
    },
    Codex {
        child: Child,
        stdin: ChildStdin,
        state: Arc<StdMutex<CodexState>>,
        next_id: u64,
    },
}

struct CodexState {
    thread_id: String,
    active_turn: Option<String>,
    starting: bool,
}

impl Runtime {
    async fn send(&mut self, message: &str) -> Result<&'static str, SubmitError> {
        match self {
            Self::Claude { child, stdin } => {
                if child.try_wait().map_err(io_error)?.is_some() {
                    return Err(SubmitError::Failed("Claude live transport exited".to_string()));
                }
                write_json_line(
                    stdin,
                    &json!({
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": message}]
                        }
                    }),
                )
                .await?;
                Ok("claude-stream-json")
            }
            Self::Codex {
                child,
                stdin,
                state,
                next_id,
            } => {
                if child.try_wait().map_err(io_error)?.is_some() {
                    return Err(SubmitError::Failed("Codex app-server exited".to_string()));
                }
                let (thread_id, active_turn, starting) = state
                    .lock()
                    .map(|state| {
                        (
                            state.thread_id.clone(),
                            state.active_turn.clone(),
                            state.starting,
                        )
                    })
                    .map_err(|_| SubmitError::Failed("Codex state lock poisoned".to_string()))?;
                if starting {
                    return Err(SubmitError::Conflict(
                        "Codex is accepting the previous message; retry after the turn starts".to_string(),
                    ));
                }
                *next_id += 1;
                let id = *next_id;
                let request = if let Some(turn_id) = active_turn {
                    json!({
                        "method": "turn/steer",
                        "id": id,
                        "params": {
                            "threadId": thread_id,
                            "expectedTurnId": turn_id,
                            "input": [{"type": "text", "text": message}]
                        }
                    })
                } else {
                    state
                        .lock()
                        .map_err(|_| SubmitError::Failed("Codex state lock poisoned".to_string()))?
                        .starting = true;
                    json!({
                        "method": "turn/start",
                        "id": id,
                        "params": {
                            "threadId": thread_id,
                            "input": [{"type": "text", "text": message}]
                        }
                    })
                };
                if let Err(error) = write_json_line(stdin, &request).await {
                    if let Ok(mut state) = state.lock() {
                        state.starting = false;
                    }
                    return Err(error);
                }
                Ok("codex-app-server")
            }
        }
    }
}

pub async fn submit_message(
    session: &AgentSession,
    message: &str,
) -> Result<SubmitResult, SubmitError> {
    let mut map = runtimes().lock().await;
    if let Some(runtime) = map.get_mut(&session.session_id) {
        match runtime.send(message).await {
            Ok(transport) => return Ok(SubmitResult { transport }),
            Err(SubmitError::Failed(_)) => {
                map.remove(&session.session_id);
            }
            Err(error) => return Err(error),
        }
    }

    if session_is_running(session) {
        return Err(SubmitError::Conflict(
            "this session is already running outside AgentSight; live attachment is not available for that runtime"
                .to_string(),
        ));
    }

    match session.agent_type.as_str() {
        agent_session::AGENT_CLAUDE => {
            let mut runtime = start_claude(session).await?;
            let transport = runtime.send(message).await?;
            map.insert(session.session_id.clone(), runtime);
            Ok(SubmitResult { transport })
        }
        agent_session::AGENT_CODEX => {
            let mut runtime = start_codex(session).await?;
            let transport = runtime.send(message).await?;
            map.insert(session.session_id.clone(), runtime);
            Ok(SubmitResult { transport })
        }
        agent_session::AGENT_GEMINI => {
            drop(map);
            resume_gemini(session, message)?;
            Ok(SubmitResult {
                transport: "gemini-resume",
            })
        }
        other => Err(SubmitError::Failed(format!(
            "sending messages to {other} sessions is not supported yet"
        ))),
    }
}

async fn start_claude(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = Command::new("claude");
    command.args([
        "-p",
        "--resume",
        &session.session_id,
        "--input-format=stream-json",
        "--output-format=stream-json",
        "--verbose",
    ]);
    apply_cwd(&mut command, session);
    command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    let mut child = command
        .spawn()
        .map_err(|error| SubmitError::Failed(format!("failed to start Claude live session: {error}")))?;
    let stdin = child
        .stdin
        .take()
        .ok_or_else(|| SubmitError::Failed("Claude stdin was not available".to_string()))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| SubmitError::Failed("Claude stdout was not available".to_string()))?;
    tokio::spawn(drain_lines(stdout, "claude"));
    Ok(Runtime::Claude { child, stdin })
}

async fn start_codex(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = Command::new("codex");
    command.args(["app-server", "--stdio"]);
    apply_cwd(&mut command, session);
    command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    let mut child = command
        .spawn()
        .map_err(|error| SubmitError::Failed(format!("failed to start Codex app-server: {error}")))?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| SubmitError::Failed("Codex stdin was not available".to_string()))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| SubmitError::Failed("Codex stdout was not available".to_string()))?;
    let mut reader = BufReader::new(stdout);

    write_json_line(
        &mut stdin,
        &json!({
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {
                    "name": "agentsight",
                    "title": "AgentSight",
                    "version": env!("CARGO_PKG_VERSION")
                }
            }
        }),
    )
    .await?;
    wait_for_response(&mut reader, 1).await?;
    write_json_line(&mut stdin, &json!({"method": "initialized", "params": {}})).await?;
    write_json_line(
        &mut stdin,
        &json!({
            "method": "thread/resume",
            "id": 2,
            "params": {
                "threadId": session.session_id,
                "approvalPolicy": "never"
            }
        }),
    )
    .await?;
    wait_for_response(&mut reader, 2).await?;

    let state = Arc::new(StdMutex::new(CodexState {
        thread_id: session.session_id.clone(),
        active_turn: None,
        starting: false,
    }));
    let reader_state = Arc::clone(&state);
    tokio::spawn(async move {
        read_codex_events(reader, reader_state).await;
    });
    Ok(Runtime::Codex {
        child,
        stdin,
        state,
        next_id: 2,
    })
}

async fn read_codex_events<R>(mut reader: BufReader<R>, state: Arc<StdMutex<CodexState>>)
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = String::new();
    loop {
        line.clear();
        let Ok(bytes) = reader.read_line(&mut line).await else {
            break;
        };
        if bytes == 0 {
            break;
        }
        let Ok(value) = serde_json::from_str::<Value>(line.trim()) else {
            continue;
        };
        let method = value.get("method").and_then(Value::as_str);
        let turn_id = value
            .pointer("/params/turn/id")
            .or_else(|| value.pointer("/result/turn/id"))
            .and_then(Value::as_str)
            .map(str::to_string);
        if (method == Some("turn/started") || turn_id.is_some())
            && let Some(turn_id) = turn_id
            && let Ok(mut state) = state.lock()
        {
            state.active_turn = Some(turn_id);
            state.starting = false;
        }
        if method == Some("turn/completed")
            && let Ok(mut state) = state.lock()
        {
            state.active_turn = None;
            state.starting = false;
        }
    }
}

async fn wait_for_response<R>(reader: &mut BufReader<R>, expected_id: u64) -> Result<(), SubmitError>
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = String::new();
    loop {
        line.clear();
        let bytes = reader
            .read_line(&mut line)
            .await
            .map_err(|error| SubmitError::Failed(format!("failed to read provider response: {error}")))?;
        if bytes == 0 {
            return Err(SubmitError::Failed(
                "provider transport closed during initialization".to_string(),
            ));
        }
        let Ok(value) = serde_json::from_str::<Value>(line.trim()) else {
            continue;
        };
        if value.get("id").and_then(Value::as_u64) != Some(expected_id) {
            continue;
        }
        if let Some(error) = value.get("error") {
            return Err(SubmitError::Failed(format!("provider rejected request: {error}")));
        }
        return Ok(());
    }
}

fn session_is_running(session: &AgentSession) -> bool {
    let mut live = LiveView::default();
    let Ok(sample) = live.refresh_monitor_sample(50) else {
        return false;
    };
    let target = canonical(&session.path);
    sample
        .sessions
        .iter()
        .filter_map(|live| live.session_path.as_deref())
        .any(|path| canonical(path) == target)
}

fn canonical(path: &Path) -> std::path::PathBuf {
    std::fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf())
}

fn resume_gemini(session: &AgentSession, message: &str) -> Result<(), SubmitError> {
    let mut command = Command::new("gemini");
    command.args(["--resume", &session.session_id, message]);
    apply_cwd(&mut command, session);
    command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    let mut child = command
        .spawn()
        .map_err(|error| SubmitError::Failed(format!("failed to resume Gemini session: {error}")))?;
    let agent = session.agent_type.clone();
    let session_id = session.session_id.clone();
    tokio::spawn(async move {
        match child.wait().await {
            Ok(status) if status.success() => {}
            Ok(status) => log::warn!("{agent} session {session_id} exited with {status}"),
            Err(error) => log::warn!("{agent} session {session_id} wait failed: {error}"),
        }
    });
    Ok(())
}

fn apply_cwd(command: &mut Command, session: &AgentSession) {
    if let Some(cwd) = session.cwd.as_deref().filter(|cwd| !cwd.is_empty()) {
        command.current_dir(cwd);
    }
}

async fn write_json_line(stdin: &mut ChildStdin, value: &Value) -> Result<(), SubmitError> {
    let mut bytes = serde_json::to_vec(value)
        .map_err(|error| SubmitError::Failed(format!("failed to encode provider request: {error}")))?;
    bytes.push(b'\n');
    stdin
        .write_all(&bytes)
        .await
        .map_err(|error| SubmitError::Failed(format!("failed to write provider request: {error}")))?;
    stdin
        .flush()
        .await
        .map_err(|error| SubmitError::Failed(format!("failed to flush provider request: {error}")))
}

async fn drain_lines<R>(stdout: R, agent: &'static str)
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut lines = BufReader::new(stdout).lines();
    while let Ok(Some(line)) = lines.next_line().await {
        log::trace!("{agent} live session: {line}");
    }
}

fn io_error(error: std::io::Error) -> SubmitError {
    SubmitError::Failed(error.to_string())
}
