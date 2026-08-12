// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::AgentSession;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
#[cfg(target_os = "windows")]
use std::ffi::OsStr;
#[cfg(target_os = "windows")]
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::{Arc, Mutex as StdMutex, OnceLock};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::Mutex;

use crate::sources::proc as procfs;
use crate::view::process_select;

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
    let mut command = provider_command("claude");
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
    let mut command = provider_command("codex");
    command.args(["app-server", "--listen", "stdio://"]);
    configure(&mut command, session, true);
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to start Codex app-server: {error}")))?;
    let mut stdin = child.stdin.take().ok_or_else(|| failed("Codex stdin unavailable"))?;
    let stdout = child.stdout.take().ok_or_else(|| failed("Codex stdout unavailable"))?;
    let mut reader = BufReader::new(stdout);

    send_json(
        &mut stdin,
        json!({"method":"initialize","id":1,"params":{
            "clientInfo":{"name":"agentsight","title":"AgentSight","version":env!("CARGO_PKG_VERSION")},
            "capabilities":{"experimentalApi":true}
        }}),
    )
    .await?;
    wait_response(&mut reader, 1).await?;
    send_json(&mut stdin, json!({"method":"initialized","params":{}})).await?;
    send_json(
        &mut stdin,
        json!({"method":"thread/resume","id":2,"params":{"threadId":session.session_id}}),
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
    let Ok(sample) = procfs::ProcSnapshot::collect() else {
        return false;
    };
    let children = sample.children_by_ppid();
    let roots = process_select::live_root_pids(&sample, None, None);
    let root_set = roots.iter().copied().collect::<HashSet<_>>();
    let candidates = roots
        .into_iter()
        .filter_map(|root_pid| {
            let root = sample.procs.get(&root_pid)?;
            (process_select::known_agent_label(&root.comm, &root.command)
                == Some(session.agent_type.as_str()))
            .then(|| {
                let family = procfs::process_family_excluding(
                    root_pid,
                    &children,
                    &sample.procs,
                    &root_set,
                );
                let members = family
                    .into_iter()
                    .filter_map(|pid| sample.procs.get(&pid).map(procfs::ProcInfo::process_key))
                    .collect();
                agent_session::LiveProcessCandidate {
                    tree: agent_session::ProcessTree {
                        root: root.process_key(),
                        members,
                    },
                    agent: session.agent_type.clone(),
                    age_s: Some(procfs::process_age_s(root, &sample)),
                    cwd: root
                        .cwd
                        .as_ref()
                        .map(|path| path.to_string_lossy().to_string()),
                }
            })
        })
        .collect::<Vec<_>>();
    let trees = candidates.iter().map(|candidate| candidate.tree.clone()).collect::<Vec<_>>();
    let fd_paths = procfs::collect_fd_paths(&trees);
    let input = agent_session::SessionProcessInput {
        id: session.session_id.clone(),
        agent: session.agent_type.clone(),
        path: session.path.clone(),
        start_timestamp_ms: session.start_timestamp_ms,
        end_timestamp_ms: session.end_timestamp_ms,
        cwd: session.cwd.clone(),
    };
    let matches = agent_session::SessionProcessMatcher::default().match_sessions(
        &[input],
        &candidates,
        &fd_paths,
        &HashMap::new(),
        now_ms(),
    );
    matches.by_session_id.contains_key(&session.session_id)
}

fn resume_gemini(session: &AgentSession, message: &str) -> Result<(), SubmitError> {
    let mut command = provider_command("gemini");
    command.args(["--resume", &session.session_id, message]);
    configure(&mut command, session, false);
    let child = command
        .spawn()
        .map_err(|error| failed(format!("failed to resume Gemini session: {error}")))?;
    reap(child, "gemini", session.session_id.clone());
    Ok(())
}

fn provider_command(name: &str) -> Command {
    #[cfg(target_os = "windows")]
    let program = resolve_windows_program(
        Path::new(name),
        std::env::var_os("PATH").as_deref(),
        std::env::var_os("PATHEXT").as_deref(),
    )
    .unwrap_or_else(|| PathBuf::from(name));
    #[cfg(not(target_os = "windows"))]
    let program = name;
    Command::new(program)
}

#[cfg(target_os = "windows")]
fn resolve_windows_program(
    program: &Path,
    search_path: Option<&OsStr>,
    path_ext: Option<&OsStr>,
) -> Option<PathBuf> {
    if program.components().count() > 1 || program.extension().is_some() {
        return program.is_file().then(|| program.to_path_buf());
    }
    let extensions = path_ext
        .and_then(OsStr::to_str)
        .unwrap_or(".COM;.EXE;.BAT;.CMD")
        .split(';')
        .filter(|extension| !extension.is_empty());
    for directory in search_path.into_iter().flat_map(std::env::split_paths) {
        for extension in extensions.clone() {
            let mut candidate = directory.join(program).into_os_string();
            candidate.push(extension);
            let candidate = PathBuf::from(candidate);
            if candidate.is_file() {
                return Some(candidate);
            }
        }
    }
    None
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

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn failed(message: impl Into<String>) -> SubmitError {
    SubmitError::Failed(message.into())
}

#[cfg(all(test, target_os = "windows"))]
mod tests {
    use super::*;

    #[test]
    fn provider_resolution_accepts_cmd_shims() {
        let temp = tempfile::tempdir().unwrap();
        let shim = temp.path().join("codex.cmd");
        std::fs::write(&shim, "@echo off\r\n").unwrap();
        let path = std::env::join_paths([temp.path()]).unwrap();

        assert_eq!(
            resolve_windows_program(
                Path::new("codex"),
                Some(&path),
                Some(OsStr::new(".EXE;.CMD")),
            ),
            Some(shim)
        );
    }
}
