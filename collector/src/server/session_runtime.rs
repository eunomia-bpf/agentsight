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
    Claude(ChildStdin),
    Codex {
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
            Self::Claude(stdin) => {
                send_json(
                    stdin,
                    json!({
                        "type":"user",
                        "message":{"role":"user","content":[{"type":"text","text":message}]}
                    }),
                )
                .await?;
                Ok("claude-stream-json")
            }
            Self::Codex {
                stdin,
                state,
                next_id,
            } => {
                let (thread_id, active_turn, starting) = state
                    .lock()
                    .map(|s| (s.thread_id.clone(), s.active_turn.clone(), s.starting))
                    .map_err(|_| failed("Codex state lock poisoned"))?;
                if starting {
                    return Err(SubmitError::Conflict(
                        "Codex is accepting the previous message; retry after the turn starts".into(),
                    ));
                }
                *next_id += 1;
                let request = if let Some(turn_id) = active_turn {
                    json!({
                        "method":"turn/steer","id":*next_id,
                        "params":{"threadId":thread_id,"expectedTurnId":turn_id,
                            "input":[{"type":"text","text":message}]}
                    })
                } else {
                    state.lock().map_err(|_| failed("Codex state lock poisoned"))?.starting = true;
                    json!({
                        "method":"turn/start","id":*next_id,
                        "params":{"threadId":thread_id,
                            "input":[{"type":"text","text":message}]}
                    })
                };
                if let Err(error) = send_json(stdin, request).await {
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
            Err(SubmitError::Conflict(error)) => return Err(SubmitError::Conflict(error)),
            Err(SubmitError::Failed(_)) => {
                map.remove(&session.session_id);
            }
        }
    }

    if session_is_running(session) {
        return Err(SubmitError::Conflict(
            "session is already running outside AgentSight; this runtime cannot be attached safely"
                .into(),
        ));
    }

    let (runtime, transport) = match session.agent_type.as_str() {
        agent_session::AGENT_CLAUDE => {
            let mut runtime = start_claude(session)?;
            let transport = runtime.send(message).await?;
            (Some(runtime), transport)
        }
        agent_session::AGENT_CODEX => {
            let mut runtime = start_codex(session).await?;
            let transport = runtime.send(message).await?;
            (Some(runtime), transport)
        }
        agent_session::AGENT_GEMINI => {
            drop(map);
            resume_gemini(session, message)?;
            return Ok(SubmitResult {
                transport: "gemini-resume",
            });
        }
        other => return Err(failed(format!("messaging {other} sessions is not supported"))),
    };
    if let Some(runtime) = runtime {
        map.insert(session.session_id.clone(), runtime);
    }
    Ok(SubmitResult { transport })
}

fn start_claude(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = Command::new("claude");
    command.args([
        "-p",
        "--resume",
        &session.session_id,
        "--input-format=stream-json",
        "--output-format=stream-json",
        "--verbose",
    ]);
    configure(&mut command, session, true);
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to start Claude live session: {error}")))?;
    let stdin = child.stdin.take().ok_or_else(|| failed("Claude stdin unavailable"))?;
    let stdout = child.stdout.take().ok_or_else(|| failed("Claude stdout unavailable"))?;
    tokio::spawn(drain(stdout));
    reap(child, "claude", session.session_id.clone());
    Ok(Runtime::Claude(stdin))
}

async fn start_codex(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = Command::new("codex");
    command.args(["app-server", "--stdio"]);
    configure(&mut command, session, true);
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to start Codex app-server: {error}")))?;
    let mut stdin = child.stdin.take().ok_or_else(|| failed("Codex stdin unavailable"))?;
    let stdout = child.stdout.take().ok_or_else(|| failed("Codex stdout unavailable"))?;
    let mut reader = BufReader::new(stdout);

    send_json(
        &mut stdin,
        json!({"method":"initialize","id":1,"params":{"clientInfo":{
            "name":"agentsight","title":"AgentSight","version":env!("CARGO_PKG_VERSION")
        }}}),
    )
    .await?;
    wait_response(&mut reader, 1).await?;
    send_json(&mut stdin, json!({"method":"initialized","params":{}})).await?;
    send_json(
        &mut stdin,
        json!({"method":"thread/resume","id":2,"params":{
            "threadId":session.session_id,"approvalPolicy":"never"
        }}),
    )
    .await?;
    wait_response(&mut reader, 2).await?;

    let state = Arc::new(StdMutex::new(CodexState {
        thread_id: session.session_id.clone(),
        active_turn: None,
        starting: false,
    }));
    tokio::spawn(read_codex(reader, Arc::clone(&state)));
    reap(child, "codex", session.session_id.clone());
    Ok(Runtime::Codex {
        stdin,
        state,
        next_id: 2,
    })
}

async fn read_codex<R>(mut reader: BufReader<R>, state: Arc<StdMutex<CodexState>>)
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = String::new();
    loop {
        line.clear();
        if reader.read_line(&mut line).await.ok().filter(|n| *n > 0).is_none() {
            break;
        }
        let Ok(value) = serde_json::from_str::<Value>(line.trim()) else {
            continue;
        };
        let method = value.get("method").and_then(Value::as_str);
        let turn = value
            .pointer("/params/turn/id")
            .or_else(|| value.pointer("/result/turn/id"))
            .and_then(Value::as_str);
        if let Ok(mut state) = state.lock() {
            if method == Some("turn/completed") {
                state.active_turn = None;
                state.starting = false;
            } else if let Some(turn) = turn {
                state.active_turn = Some(turn.to_string());
                state.starting = false;
            } else if value.get("error").is_some() && value.get("id").is_some() {
                state.starting = false;
            }
        }
    }
}

async fn wait_response<R>(reader: &mut BufReader<R>, id: u64) -> Result<(), SubmitError>
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = String::new();
    loop {
        line.clear();
        if reader
            .read_line(&mut line)
            .await
            .map_err(|error| failed(error.to_string()))?
            == 0
        {
            return Err(failed("provider transport closed during initialization"));
        }
        let Ok(value) = serde_json::from_str::<Value>(line.trim()) else {
            continue;
        };
        if value.get("id").and_then(Value::as_u64) == Some(id) {
            return value
                .get("error")
                .map(|error| Err(failed(format!("provider rejected request: {error}"))))
                .unwrap_or(Ok(()));
        }
    }
}

fn session_is_running(session: &AgentSession) -> bool {
    let Ok(sample) = LiveView::default().refresh_monitor_sample(50) else {
        return false;
    };
    let target = canonical(&session.path);
    sample
        .sessions
        .iter()
        .filter_map(|live| live.session_path.as_deref())
        .any(|path| canonical(path) == target)
}

fn resume_gemini(session: &AgentSession, message: &str) -> Result<(), SubmitError> {
    let mut command = Command::new("gemini");
    command.args(["--resume", &session.session_id, message]);
    configure(&mut command, session, false);
    let child = command
        .spawn()
        .map_err(|error| failed(format!("failed to resume Gemini session: {error}")))?;
    reap(child, "gemini", session.session_id.clone());
    Ok(())
}

fn configure(command: &mut Command, session: &AgentSession, piped: bool) {
    if let Some(cwd) = session.cwd.as_deref().filter(|cwd| !cwd.is_empty()) {
        command.current_dir(cwd);
    }
    command.stdin(if piped { Stdio::piped() } else { Stdio::null() });
    command.stdout(if piped { Stdio::piped() } else { Stdio::null() });
    command.stderr(Stdio::null());
}

async fn send_json(stdin: &mut ChildStdin, value: Value) -> Result<(), SubmitError> {
    let mut data = serde_json::to_vec(&value).map_err(|error| failed(error.to_string()))?;
    data.push(b'\n');
    stdin
        .write_all(&data)
        .await
        .map_err(|error| failed(format!("provider transport write failed: {error}")))?;
    stdin
        .flush()
        .await
        .map_err(|error| failed(format!("provider transport flush failed: {error}")))
}

async fn drain<R: tokio::io::AsyncRead + Unpin>(stdout: R) {
    let mut lines = BufReader::new(stdout).lines();
    while let Ok(Some(_)) = lines.next_line().await {}
}

fn reap(mut child: Child, agent: &'static str, session_id: String) {
    tokio::spawn(async move {
        match child.wait().await {
            Ok(status) if status.success() => {}
            Ok(status) => log::warn!("{agent} session {session_id} exited with {status}"),
            Err(error) => log::warn!("{agent} session {session_id} wait failed: {error}"),
        }
    });
}

fn canonical(path: &Path) -> std::path::PathBuf {
    std::fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf())
}

fn failed(message: impl Into<String>) -> SubmitError {
    SubmitError::Failed(message.into())
}
