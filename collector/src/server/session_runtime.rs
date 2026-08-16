// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::AgentSession;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
#[cfg(target_os = "windows")]
use std::ffi::OsStr;
#[cfg(unix)]
use std::ffi::{CStr, OsString};
use std::fs::File;
use std::future::Future;
use std::io::{BufRead, BufReader as StdBufReader, Read};
#[cfg(unix)]
use std::os::unix::{
    ffi::OsStringExt,
    fs::{MetadataExt, PermissionsExt},
};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::{Arc, Mutex as StdMutex, OnceLock, Weak};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufRead, AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, Command};
use tokio::sync::{Mutex as AsyncMutex, oneshot};

use crate::sources::proc as procfs;
use crate::view::process_select;

type RuntimeSlot = Arc<AsyncMutex<Option<Runtime>>>;

static RUNTIMES: OnceLock<AsyncMutex<HashMap<String, RuntimeSlot>>> = OnceLock::new();
const PROVIDER_REQUEST_TIMEOUT: Duration = Duration::from_secs(20);
const MAX_PROVIDER_MESSAGE_BYTES: usize = 1024 * 1024;
const MAX_CODEX_MESSAGE_BYTES: usize = 16 * 1024 * 1024;
const SESSION_HEADER_SCAN_LIMIT: u64 = 64 * 1024;
const CODEX_BIN_ENV: &str = "AGENTSIGHT_CODEX_BIN";
const CLAUDE_BIN_ENV: &str = "AGENTSIGHT_CLAUDE_BIN";
const GEMINI_BIN_ENV: &str = "AGENTSIGHT_GEMINI_BIN";

type CodexResponse = Result<(), String>;
type PendingClaudeResponse = Arc<StdMutex<Option<oneshot::Sender<CodexResponse>>>>;
type PendingCodexResponses = Arc<StdMutex<HashMap<u64, oneshot::Sender<CodexResponse>>>>;
type SharedCodexStdin = Arc<AsyncMutex<Option<ChildStdin>>>;
type WeakCodexStdin = Weak<AsyncMutex<Option<ChildStdin>>>;

#[derive(Debug, Eq, PartialEq)]
enum ProviderLine {
    Complete,
    Oversized,
    Eof,
}

fn runtimes() -> &'static AsyncMutex<HashMap<String, RuntimeSlot>> {
    RUNTIMES.get_or_init(|| AsyncMutex::new(HashMap::new()))
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
        stdin: ChildStdin,
        state: Arc<StdMutex<ClaudeState>>,
        response: PendingClaudeResponse,
    },
    Codex {
        stdin: SharedCodexStdin,
        state: Arc<StdMutex<CodexState>>,
        responses: PendingCodexResponses,
        next_id: u64,
    },
}

struct ClaudeState {
    starting: bool,
    active: bool,
}

struct CodexState {
    thread_id: String,
    active_turn: Option<String>,
    starting: bool,
}

impl Runtime {
    async fn send(&mut self, message: &str) -> Result<&'static str, SubmitError> {
        match self {
            Self::Claude {
                stdin,
                state,
                response,
            } => {
                {
                    let mut state = state
                        .lock()
                        .map_err(|_| failed("Claude state lock poisoned"))?;
                    if state.starting || state.active {
                        return Err(SubmitError::Conflict(
                            "Claude is still handling the previous message".into(),
                        ));
                    }
                    state.starting = true;
                }
                let (response_tx, response_rx) = oneshot::channel();
                *response
                    .lock()
                    .map_err(|_| failed("Claude response lock poisoned"))? = Some(response_tx);
                if let Err(error) = send_json(
                    stdin,
                    json!({
                        "type":"user",
                        "message":{"role":"user","content":[{"type":"text","text":message}]}
                    }),
                )
                .await
                {
                    if let Ok(mut pending) = response.lock() {
                        pending.take();
                    }
                    if let Ok(mut state) = state.lock() {
                        state.starting = false;
                    }
                    return Err(error);
                }
                match tokio::time::timeout(PROVIDER_REQUEST_TIMEOUT, response_rx).await {
                    Ok(Ok(Ok(()))) => Ok("claude-stream-json"),
                    Ok(Ok(Err(error))) => Err(failed(error)),
                    Ok(Err(_)) => Err(failed("Claude response channel closed")),
                    Err(_) => {
                        if let Ok(mut pending) = response.lock() {
                            pending.take();
                        }
                        Err(failed("Claude did not produce output within 20 seconds"))
                    }
                }
            }
            Self::Codex {
                stdin,
                state,
                responses,
                next_id,
            } => {
                let (thread_id, active_turn, starting) = state
                    .lock()
                    .map(|s| (s.thread_id.clone(), s.active_turn.clone(), s.starting))
                    .map_err(|_| failed("Codex state lock poisoned"))?;
                if starting {
                    return Err(SubmitError::Conflict(
                        "Codex is accepting the previous message; retry after the turn starts"
                            .into(),
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
                    state
                        .lock()
                        .map_err(|_| failed("Codex state lock poisoned"))?
                        .starting = true;
                    json!({
                        "method":"turn/start","id":*next_id,
                        "params":{"threadId":thread_id,
                            "input":[{"type":"text","text":message}]}
                    })
                };
                let request_id = *next_id;
                let (response_tx, response_rx) = oneshot::channel();
                responses
                    .lock()
                    .map_err(|_| failed("Codex response lock poisoned"))?
                    .insert(request_id, response_tx);
                let send_result = {
                    let mut stdin = stdin.lock().await;
                    match stdin.as_mut() {
                        Some(stdin) => send_json(stdin, request).await,
                        None => Err(failed("Codex transport is closed")),
                    }
                };
                if let Err(error) = send_result {
                    if let Ok(mut pending) = responses.lock() {
                        pending.remove(&request_id);
                    }
                    if let Ok(mut state) = state.lock() {
                        state.starting = false;
                    }
                    return Err(error);
                }
                let response = tokio::time::timeout(PROVIDER_REQUEST_TIMEOUT, response_rx).await;
                let result = match response {
                    Ok(Ok(Ok(()))) => Ok("codex-app-server"),
                    Ok(Ok(Err(error))) => Err(failed(error)),
                    Ok(Err(_)) => Err(failed("Codex response channel closed")),
                    Err(_) => {
                        if let Ok(mut pending) = responses.lock() {
                            pending.remove(&request_id);
                        }
                        Err(failed(
                            "Codex did not acknowledge the message within 20 seconds",
                        ))
                    }
                };
                if result.is_err()
                    && let Ok(mut state) = state.lock()
                {
                    state.starting = false;
                }
                result
            }
        }
    }
}

pub async fn submit_message(
    session: &AgentSession,
    message: &str,
) -> Result<SubmitResult, SubmitError> {
    let slot = {
        let mut map = runtimes().lock().await;
        Arc::clone(
            map.entry(session.session_id.clone())
                .or_insert_with(|| Arc::new(AsyncMutex::new(None))),
        )
    };
    let mut runtime_slot = slot.try_lock().map_err(|_| {
        SubmitError::Conflict(
            "this session is already accepting another message; retry after it is acknowledged"
                .into(),
        )
    })?;
    if let Some(runtime) = runtime_slot.as_mut() {
        match timeout_provider_operation(PROVIDER_REQUEST_TIMEOUT, runtime.send(message)).await {
            Ok(transport) => return Ok(SubmitResult { transport }),
            Err(SubmitError::Conflict(error)) => return Err(SubmitError::Conflict(error)),
            Err(SubmitError::Failed(error)) => {
                *runtime_slot = None;
                drop(runtime_slot);
                remove_empty_runtime_slot(&session.session_id, &slot).await;
                return Err(SubmitError::Failed(error));
            }
        }
    }

    if session_is_running(session) {
        drop(runtime_slot);
        remove_empty_runtime_slot(&session.session_id, &slot).await;
        return Err(SubmitError::Conflict(
            "session is already running outside AgentSight; this runtime cannot be attached safely"
                .into(),
        ));
    }

    let started = timeout_provider_operation(PROVIDER_REQUEST_TIMEOUT, async {
        match session.agent_type.as_str() {
            agent_session::AGENT_CLAUDE => {
                let mut runtime = start_claude(session)?;
                let transport = runtime.send(message).await?;
                Ok((Some(runtime), transport))
            }
            agent_session::AGENT_CODEX => {
                let mut runtime = start_codex(session).await?;
                let transport = runtime.send(message).await?;
                Ok((Some(runtime), transport))
            }
            agent_session::AGENT_GEMINI => {
                resume_gemini(session, message).await?;
                Ok((None, "gemini-resume"))
            }
            other => Err(failed(format!(
                "messaging {other} sessions is not supported"
            ))),
        }
    })
    .await;
    let (runtime, transport) = match started {
        Ok(started) => started,
        Err(error) => {
            drop(runtime_slot);
            remove_empty_runtime_slot(&session.session_id, &slot).await;
            return Err(error);
        }
    };
    if let Some(runtime) = runtime {
        *runtime_slot = Some(runtime);
    } else {
        drop(runtime_slot);
        remove_empty_runtime_slot(&session.session_id, &slot).await;
    }
    Ok(SubmitResult { transport })
}

async fn timeout_provider_operation<T, F>(timeout: Duration, operation: F) -> Result<T, SubmitError>
where
    F: Future<Output = Result<T, SubmitError>>,
{
    tokio::time::timeout(timeout, operation)
        .await
        .map_err(|_| failed("provider did not accept the message within 20 seconds"))?
}

async fn remove_empty_runtime_slot(session_id: &str, slot: &RuntimeSlot) {
    let mut map = runtimes().lock().await;
    if map
        .get(session_id)
        .is_some_and(|candidate| Arc::ptr_eq(candidate, slot))
        // The map and this function must be the only owners. A cloned slot
        // represents a waiter that may initialize it after we release the map.
        && Arc::strong_count(slot) == 2
        && slot.try_lock().is_ok_and(|runtime| runtime.is_none())
    {
        map.remove(session_id);
    }
}

fn start_claude(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = provider_command_with_override("claude", CLAUDE_BIN_ENV);
    command.args([
        "-p",
        "--resume",
        &session.session_id,
        "--input-format=stream-json",
        "--output-format=stream-json",
        "--verbose",
    ]);
    configure(&mut command, session, true)?;
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to start Claude live session: {error}")))?;
    let stdin = child
        .stdin
        .take()
        .ok_or_else(|| failed("Claude stdin unavailable"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| failed("Claude stdout unavailable"))?;
    let state = Arc::new(StdMutex::new(ClaudeState {
        starting: false,
        active: false,
    }));
    let response = Arc::new(StdMutex::new(None));
    tokio::spawn(read_claude(
        BufReader::new(stdout),
        Arc::clone(&state),
        Arc::clone(&response),
    ));
    reap(child, "claude", session.session_id.clone());
    Ok(Runtime::Claude {
        stdin,
        state,
        response,
    })
}

async fn read_claude<R>(
    mut reader: BufReader<R>,
    state: Arc<StdMutex<ClaudeState>>,
    response: PendingClaudeResponse,
) where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = Vec::new();
    loop {
        match read_provider_line(&mut reader, &mut line, MAX_PROVIDER_MESSAGE_BYTES).await {
            Ok(ProviderLine::Complete) => {}
            Ok(ProviderLine::Oversized) => continue,
            Ok(ProviderLine::Eof) | Err(_) => break,
        }
        let Ok(value) = serde_json::from_slice::<Value>(&line) else {
            continue;
        };
        let event_type = value.get("type").and_then(Value::as_str);
        if matches!(event_type, Some("user" | "assistant")) {
            complete_claude_response(&response, Ok(()));
            if let Ok(mut state) = state.lock() {
                state.starting = false;
                state.active = true;
            }
        } else if event_type == Some("result") {
            let is_error = value.get("is_error").and_then(Value::as_bool) == Some(true)
                || value
                    .get("subtype")
                    .and_then(Value::as_str)
                    .is_some_and(|subtype| subtype.contains("error"));
            if is_error {
                complete_claude_response(&response, Err(claude_error_message(&value)));
            } else {
                complete_claude_response(&response, Ok(()));
            }
            if let Ok(mut state) = state.lock() {
                state.starting = false;
                state.active = false;
            }
        } else if event_type == Some("error") {
            complete_claude_response(&response, Err(claude_error_message(&value)));
            if let Ok(mut state) = state.lock() {
                state.starting = false;
                state.active = false;
            }
        }
    }
    complete_claude_response(
        &response,
        Err("Claude transport closed before producing output".into()),
    );
    if let Ok(mut state) = state.lock() {
        state.starting = false;
        state.active = false;
    }
}

fn complete_claude_response(response: &PendingClaudeResponse, result: CodexResponse) {
    let pending = response.lock().ok().and_then(|mut pending| pending.take());
    if let Some(pending) = pending {
        let _ = pending.send(result);
    }
}

fn claude_error_message(value: &Value) -> String {
    value
        .get("error")
        .or_else(|| value.get("result"))
        .or_else(|| value.get("message"))
        .and_then(Value::as_str)
        .filter(|message| !message.is_empty())
        .map(|message| format!("Claude rejected the request: {message}"))
        .unwrap_or_else(|| "Claude rejected the request".into())
}

async fn start_codex(session: &AgentSession) -> Result<Runtime, SubmitError> {
    let mut command = codex_command(session);
    command.args(["app-server", "--listen", "stdio://"]);
    configure(&mut command, session, true)?;
    command.kill_on_drop(true);
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to start Codex app-server: {error}")))?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| failed("Codex stdin unavailable"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| failed("Codex stdout unavailable"))?;
    let mut reader = BufReader::new(stdout);

    send_json(
        &mut stdin,
        json!({"method":"initialize","id":1,"params":{
            "clientInfo":{"name":"agentsight","title":"AgentSight","version":env!("CARGO_PKG_VERSION")},
            "capabilities":{
                "experimentalApi":true,
                "optOutNotificationMethods":[
                    "item/started",
                    "item/completed",
                    "item/agentMessage/delta",
                    "item/commandExecution/outputDelta",
                    "item/reasoning/summaryTextDelta",
                    "item/reasoning/textDelta",
                    "item/plan/delta",
                    "turn/diff/updated"
                ]
            }
        }}),
    )
    .await?;
    wait_response(&mut reader, &mut stdin, 1, "initialize").await?;
    send_json(&mut stdin, json!({"method":"initialized","params":{}})).await?;
    send_json(&mut stdin, codex_resume_request(&session.session_id)).await?;
    wait_response(&mut reader, &mut stdin, 2, "resume the thread").await?;

    let state = Arc::new(StdMutex::new(CodexState {
        thread_id: session.session_id.clone(),
        active_turn: None,
        starting: false,
    }));
    let responses = Arc::new(StdMutex::new(HashMap::new()));
    let stdin = Arc::new(AsyncMutex::new(Some(stdin)));
    tokio::spawn(read_codex(
        reader,
        Arc::clone(&state),
        Arc::clone(&responses),
        Arc::downgrade(&stdin),
    ));
    reap(child, "codex", session.session_id.clone());
    Ok(Runtime::Codex {
        stdin,
        state,
        responses,
        next_id: 2,
    })
}

fn codex_resume_request(thread_id: &str) -> Value {
    json!({"method":"thread/resume","id":2,"params":{
        "threadId":thread_id,
        "excludeTurns":true
    }})
}

async fn read_codex<R>(
    mut reader: BufReader<R>,
    state: Arc<StdMutex<CodexState>>,
    responses: PendingCodexResponses,
    stdin: WeakCodexStdin,
) where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = Vec::new();
    loop {
        match read_provider_line(&mut reader, &mut line, MAX_CODEX_MESSAGE_BYTES).await {
            Ok(ProviderLine::Complete) => {}
            Ok(ProviderLine::Oversized) => {
                fail_oversized_codex_transport(&state, &responses, &stdin).await;
                break;
            }
            Ok(ProviderLine::Eof) | Err(_) => break,
        }
        let Ok(value) = serde_json::from_slice::<Value>(&line) else {
            continue;
        };
        if let Some(rejection) = codex_server_request_rejection(&value) {
            let Some(stdin) = stdin.upgrade() else {
                break;
            };
            let result = {
                let mut stdin = stdin.lock().await;
                match stdin.as_mut() {
                    Some(stdin) => send_json(stdin, rejection).await,
                    None => break,
                }
            };
            if let Err(error) = result {
                fail_codex_responses(&responses, submit_error_message(error));
                break;
            }
            continue;
        }
        complete_codex_response(&value, &responses);
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
    fail_codex_responses(
        &responses,
        "Codex transport closed before acknowledging the request".into(),
    );
}

async fn fail_oversized_codex_transport(
    state: &Arc<StdMutex<CodexState>>,
    responses: &PendingCodexResponses,
    stdin: &WeakCodexStdin,
) {
    if let Ok(mut state) = state.lock() {
        state.active_turn = None;
        state.starting = false;
    }
    fail_codex_responses(
        responses,
        format!(
            "Codex message exceeded the {} byte transport limit",
            MAX_CODEX_MESSAGE_BYTES
        ),
    );
    if let Some(stdin) = stdin.upgrade() {
        // ChildStdin::shutdown is a no-op on Unix. Removing and dropping the
        // handle is what actually closes the provider pipe and lets it exit.
        stdin.lock().await.take();
    }
}

fn complete_codex_response(value: &Value, responses: &PendingCodexResponses) {
    let Some(id) = value.get("id").and_then(Value::as_u64) else {
        return;
    };
    let Some(result) = codex_response(value) else {
        return;
    };
    let response = responses
        .lock()
        .ok()
        .and_then(|mut pending| pending.remove(&id));
    if let Some(response) = response {
        let _ = response.send(result);
    }
}

fn codex_response(value: &Value) -> Option<CodexResponse> {
    if value.get("method").is_some() {
        return None;
    }
    if let Some(error) = value.get("error") {
        return Some(Err(format!("Codex rejected the request: {error}")));
    }
    value.get("result").map(|_| Ok(()))
}

fn codex_server_request_rejection(value: &Value) -> Option<Value> {
    let id = value.get("id")?;
    value.get("method").and_then(Value::as_str)?;
    Some(json!({
        "id": id,
        "error": {
            "code": -32601,
            "message": "AgentSight does not support Codex server requests"
        }
    }))
}

fn fail_codex_responses(responses: &PendingCodexResponses, message: String) {
    if let Ok(mut pending) = responses.lock() {
        for (_, response) in pending.drain() {
            let _ = response.send(Err(message.clone()));
        }
    }
}

fn submit_error_message(error: SubmitError) -> String {
    match error {
        SubmitError::Conflict(message) | SubmitError::Failed(message) => message,
    }
}

async fn wait_response<R>(
    reader: &mut BufReader<R>,
    stdin: &mut ChildStdin,
    id: u64,
    operation: &str,
) -> Result<(), SubmitError>
where
    R: tokio::io::AsyncRead + Unpin,
{
    tokio::time::timeout(
        PROVIDER_REQUEST_TIMEOUT,
        wait_response_inner(reader, stdin, id),
    )
    .await
    .map_err(|_| failed(format!("Codex timed out while trying to {operation}")))?
}

async fn wait_response_inner<R>(
    reader: &mut BufReader<R>,
    stdin: &mut ChildStdin,
    id: u64,
) -> Result<(), SubmitError>
where
    R: tokio::io::AsyncRead + Unpin,
{
    let mut line = Vec::new();
    loop {
        match read_provider_line(reader, &mut line, MAX_CODEX_MESSAGE_BYTES)
            .await
            .map_err(|error| failed(error.to_string()))?
        {
            ProviderLine::Complete => {}
            ProviderLine::Oversized => {
                return Err(failed(format!(
                    "Codex message exceeded the {} byte transport limit during initialization",
                    MAX_CODEX_MESSAGE_BYTES
                )));
            }
            ProviderLine::Eof => {
                return Err(failed("provider transport closed during initialization"));
            }
        }
        let Ok(value) = serde_json::from_slice::<Value>(&line) else {
            continue;
        };
        if let Some(rejection) = codex_server_request_rejection(&value) {
            send_json(stdin, rejection).await?;
            continue;
        }
        if value.get("id").and_then(Value::as_u64) == Some(id) {
            if let Some(response) = codex_response(&value) {
                return response.map_err(failed);
            }
        }
    }
}

async fn read_provider_line<R>(
    reader: &mut R,
    line: &mut Vec<u8>,
    max_bytes: usize,
) -> std::io::Result<ProviderLine>
where
    R: AsyncBufRead + Unpin,
{
    line.clear();
    let mut oversized = false;
    let mut saw_data = false;
    loop {
        let buffer = reader.fill_buf().await?;
        if buffer.is_empty() {
            return Ok(if !saw_data {
                ProviderLine::Eof
            } else if oversized {
                ProviderLine::Oversized
            } else {
                ProviderLine::Complete
            });
        }
        saw_data = true;
        let consumed = buffer
            .iter()
            .position(|byte| *byte == b'\n')
            .map_or(buffer.len(), |index| index + 1);
        let complete = buffer.get(consumed.saturating_sub(1)) == Some(&b'\n');
        if !oversized {
            let remaining = max_bytes.saturating_sub(line.len());
            let copied = consumed.min(remaining);
            line.extend_from_slice(&buffer[..copied]);
            oversized = copied < consumed;
        }
        reader.consume(consumed);
        if complete {
            return Ok(if oversized {
                ProviderLine::Oversized
            } else {
                ProviderLine::Complete
            });
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
                let family =
                    procfs::process_family_excluding(root_pid, &children, &sample.procs, &root_set);
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
    let trees = candidates
        .iter()
        .map(|candidate| candidate.tree.clone())
        .collect::<Vec<_>>();
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

async fn resume_gemini(session: &AgentSession, message: &str) -> Result<(), SubmitError> {
    let mut command = provider_command_with_override("gemini", GEMINI_BIN_ENV);
    command.args(gemini_resume_args(&session.session_id));
    configure(&mut command, session, false)?;
    command.stdin(Stdio::piped()).kill_on_drop(true);
    let mut child = command
        .spawn()
        .map_err(|error| failed(format!("failed to resume Gemini session: {error}")))?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| failed("Gemini stdin unavailable"))?;
    stdin
        .write_all(message.as_bytes())
        .await
        .map_err(|error| failed(format!("failed to send the Gemini message: {error}")))?;
    stdin
        .shutdown()
        .await
        .map_err(|error| failed(format!("failed to finish the Gemini message: {error}")))?;
    tokio::time::sleep(Duration::from_millis(300)).await;
    if let Some(status) = child
        .try_wait()
        .map_err(|error| failed(format!("failed to inspect Gemini session: {error}")))?
    {
        return status.success().then_some(()).ok_or_else(|| {
            failed(format!(
                "Gemini exited before accepting the message: {status}"
            ))
        });
    }
    reap(child, "gemini", session.session_id.clone());
    Ok(())
}

fn gemini_resume_args(session_id: &str) -> [&str; 2] {
    ["--resume", session_id]
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

fn provider_command_with_override(name: &str, variable: &str) -> Command {
    std::env::var_os(variable)
        .filter(|value| !value.is_empty())
        .map(Command::new)
        .unwrap_or_else(|| provider_command(name))
}

fn codex_command(session: &AgentSession) -> Command {
    if let Some(program) = std::env::var_os(CODEX_BIN_ENV).filter(|value| !value.is_empty()) {
        return Command::new(program);
    }
    if let Some(version) = codex_cli_version(&session.path)
        && let Some(home) = codex_install_home(&session.path)
        && let Some(program) = standalone_codex_binary(&home, &version)
    {
        return Command::new(program);
    }
    provider_command("codex")
}

fn codex_cli_version(path: &Path) -> Option<String> {
    let reader = StdBufReader::new(File::open(path).ok()?.take(SESSION_HEADER_SCAN_LIMIT));
    for line in reader.lines().take(32) {
        let Ok(line) = line else {
            break;
        };
        let Ok(value) = serde_json::from_str::<Value>(&line) else {
            continue;
        };
        if value.get("type").and_then(Value::as_str) != Some("session_meta") {
            continue;
        }
        let Some(version) = value
            .pointer("/payload/cli_version")
            .or_else(|| value.pointer("/payload/cliVersion"))
            .and_then(Value::as_str)
        else {
            continue;
        };
        if valid_provider_version(version) {
            return Some(version.to_string());
        }
    }
    None
}

fn codex_install_home(session_path: &Path) -> Option<PathBuf> {
    let mut directory = session_path.parent();
    while let Some(candidate) = directory {
        if candidate
            .file_name()
            .is_some_and(|name| name.to_string_lossy().eq_ignore_ascii_case(".codex"))
        {
            return candidate.parent().map(Path::to_path_buf);
        }
        directory = candidate.parent();
    }
    dirs::home_dir()
}

fn valid_provider_version(version: &str) -> bool {
    !version.is_empty()
        && version.len() <= 64
        && version.starts_with(|character: char| character.is_ascii_digit())
        && version
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'+'))
}

fn standalone_codex_binary(home: &Path, version: &str) -> Option<PathBuf> {
    if !valid_provider_version(version) {
        return None;
    }
    let releases = home.join(".codex/packages/standalone/releases");
    let prefix = format!("{version}-");
    let executable = format!("codex{}", std::env::consts::EXE_SUFFIX);
    let mut best: Option<(bool, PathBuf)> = None;
    for entry in std::fs::read_dir(releases).ok()?.filter_map(Result::ok) {
        let Some(name) = entry.file_name().to_str().map(str::to_string) else {
            continue;
        };
        if !standalone_release_matches_platform(&name, version, &prefix) {
            continue;
        }
        let path = entry.path().join("bin").join(&executable);
        if !provider_binary_is_executable(&path) {
            continue;
        }
        let candidate = (!name.contains(std::env::consts::ARCH), path);
        if best.as_ref().is_none_or(|current| candidate < *current) {
            best = Some(candidate);
        }
    }
    best.map(|(_, path)| path)
}

fn standalone_release_matches_platform(name: &str, version: &str, prefix: &str) -> bool {
    if name == version {
        return true;
    }
    name.starts_with(prefix)
        && name.contains(std::env::consts::ARCH)
        && name.contains(standalone_target_marker())
}

#[cfg(target_os = "linux")]
fn standalone_target_marker() -> &'static str {
    "unknown-linux"
}

#[cfg(target_os = "macos")]
fn standalone_target_marker() -> &'static str {
    "apple-darwin"
}

#[cfg(target_os = "windows")]
fn standalone_target_marker() -> &'static str {
    "pc-windows"
}

#[cfg(not(any(target_os = "linux", target_os = "macos", target_os = "windows")))]
fn standalone_target_marker() -> &'static str {
    std::env::consts::OS
}

#[cfg(unix)]
fn provider_binary_is_executable(path: &Path) -> bool {
    std::fs::metadata(path)
        .is_ok_and(|metadata| metadata.is_file() && metadata.permissions().mode() & 0o111 != 0)
}

#[cfg(not(unix))]
fn provider_binary_is_executable(path: &Path) -> bool {
    path.is_file()
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

fn configure(
    command: &mut Command,
    session: &AgentSession,
    piped: bool,
) -> Result<(), SubmitError> {
    if let Some(cwd) = session.cwd.as_deref().filter(|cwd| !cwd.is_empty()) {
        command.current_dir(cwd);
    }
    command.stdin(if piped { Stdio::piped() } else { Stdio::null() });
    command.stdout(if piped { Stdio::piped() } else { Stdio::null() });
    command.stderr(Stdio::null());
    configure_provider_identity(command, &session.path)?;
    Ok(())
}

#[cfg(unix)]
fn configure_provider_identity(
    command: &mut Command,
    session_path: &Path,
) -> Result<(), SubmitError> {
    let metadata = std::fs::metadata(session_path).map_err(|error| {
        failed(format!(
            "cannot identify the provider session owner for {}: {error}",
            session_path.display()
        ))
    })?;
    let effective_uid = unsafe { libc::geteuid() } as u32;
    if effective_uid != 0 {
        if metadata.uid() != effective_uid {
            return Err(failed(format!(
                "refusing to run a provider for a session owned by uid {} as uid {effective_uid}",
                metadata.uid()
            )));
        }
        return Ok(());
    }
    let (uid, gid) = provider_user_ids(
        (metadata.uid(), metadata.gid()),
        crate::cmd_exec::target_user_ids(),
    )?;
    let account = provider_account(uid)?;
    let provider_home = provider_session_home(session_path).unwrap_or(account.home);
    let preserved_environment = std::env::vars_os()
        .filter(|(key, _)| provider_environment_allowed(key))
        .collect::<Vec<_>>();
    command.env_clear();
    command
        .envs(preserved_environment)
        .env("HOME", provider_home)
        .env("USER", &account.name)
        .env("LOGNAME", &account.name);
    unsafe {
        command.pre_exec(move || {
            if libc::setgroups(0, std::ptr::null()) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            if libc::setgid(gid as libc::gid_t) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            if libc::setuid(uid as libc::uid_t) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            Ok(())
        });
    }
    Ok(())
}

#[cfg(unix)]
fn provider_environment_allowed(key: &std::ffi::OsStr) -> bool {
    let key = key.to_string_lossy();
    key.starts_with("LC_")
        || matches!(
            key.as_ref(),
            "PATH"
                | "LANG"
                | "TZ"
                | "TERM"
                | "COLORTERM"
                | "NO_COLOR"
                | "SSL_CERT_FILE"
                | "SSL_CERT_DIR"
        )
}

#[cfg(target_os = "windows")]
fn configure_provider_identity(
    _command: &mut Command,
    session_path: &Path,
) -> Result<(), SubmitError> {
    let provider_homes = ["HOME", "USERPROFILE"]
        .into_iter()
        .filter_map(std::env::var_os)
        .filter(|home| !home.is_empty())
        .map(PathBuf::from)
        .collect::<Vec<_>>();
    if provider_homes.is_empty() {
        return Err(failed(
            "refusing to run a Windows session provider because the current user profile is unknown",
        ));
    }
    validate_windows_provider_context(windows_process_is_elevated(), session_path, &provider_homes)
}

#[cfg(target_os = "windows")]
fn validate_windows_provider_context(
    elevated: bool,
    session_path: &Path,
    provider_homes: &[PathBuf],
) -> Result<(), SubmitError> {
    if elevated {
        return Err(failed(
            "refusing to run a session provider from an elevated Windows process; run AgentSight as the transcript owner",
        ));
    }
    let session_path = session_path.canonicalize().map_err(|error| {
        failed(format!(
            "cannot validate the Windows provider session path {}: {error}",
            session_path.display()
        ))
    })?;
    let provider_homes = provider_homes
        .iter()
        .filter_map(|home| home.canonicalize().ok())
        .collect::<Vec<_>>();
    if provider_homes.is_empty() {
        return Err(failed(
            "refusing to run a Windows session provider because no current user profile path is usable",
        ));
    }
    if !provider_homes
        .iter()
        .any(|provider_home| session_path.starts_with(provider_home))
    {
        return Err(failed(format!(
            "refusing to run a provider for a Windows session outside the current user profile: {}",
            session_path.display()
        )));
    }
    Ok(())
}

#[cfg(target_os = "windows")]
fn windows_process_is_elevated() -> bool {
    #[link(name = "shell32")]
    unsafe extern "system" {
        fn IsUserAnAdmin() -> i32;
    }

    unsafe { IsUserAnAdmin() != 0 }
}

#[cfg(not(any(unix, target_os = "windows")))]
fn configure_provider_identity(
    _command: &mut Command,
    _session_path: &Path,
) -> Result<(), SubmitError> {
    Err(failed(
        "session provider execution is unsupported on this platform",
    ))
}

#[cfg(unix)]
fn provider_user_ids(
    session_owner: (u32, u32),
    sudo_user: Option<(u32, u32)>,
) -> Result<(u32, u32), SubmitError> {
    [Some(session_owner), sudo_user]
        .into_iter()
        .flatten()
        .find(|(uid, gid)| *uid != 0 && *gid != 0)
        .ok_or_else(|| {
            failed("refusing to run a session provider as root because no non-root owner is known")
        })
}

#[cfg(unix)]
struct ProviderAccount {
    name: OsString,
    home: PathBuf,
}

#[cfg(unix)]
fn provider_account(uid: u32) -> Result<ProviderAccount, SubmitError> {
    let configured_size = unsafe { libc::sysconf(libc::_SC_GETPW_R_SIZE_MAX) };
    let buffer_size = if configured_size > 0 {
        configured_size as usize
    } else {
        16 * 1024
    }
    .clamp(1024, 1024 * 1024);
    let mut buffer = vec![0_u8; buffer_size];
    let mut passwd = unsafe { std::mem::zeroed::<libc::passwd>() };
    let mut result = std::ptr::null_mut();
    let status = unsafe {
        libc::getpwuid_r(
            uid as libc::uid_t,
            &mut passwd,
            buffer.as_mut_ptr().cast(),
            buffer.len(),
            &mut result,
        )
    };
    if status != 0 || result.is_null() || passwd.pw_name.is_null() || passwd.pw_dir.is_null() {
        return Err(failed(format!(
            "refusing to run a session provider because uid {uid} has no usable account"
        )));
    }
    let name = unsafe { CStr::from_ptr(passwd.pw_name) }.to_bytes();
    let home = unsafe { CStr::from_ptr(passwd.pw_dir) }.to_bytes();
    if name.is_empty() || home.is_empty() {
        return Err(failed(format!(
            "refusing to run a session provider because uid {uid} has no usable account"
        )));
    }
    Ok(ProviderAccount {
        name: OsString::from_vec(name.to_vec()),
        home: PathBuf::from(OsString::from_vec(home.to_vec())),
    })
}

#[cfg(any(unix, test))]
fn provider_session_home(session_path: &Path) -> Option<PathBuf> {
    let mut directory = session_path.parent();
    while let Some(candidate) = directory {
        if candidate.file_name().is_some_and(|name| {
            [".claude", ".codex", ".gemini"]
                .iter()
                .any(|marker| name.to_string_lossy().eq_ignore_ascii_case(marker))
        }) {
            return candidate.parent().map(Path::to_path_buf);
        }
        directory = candidate.parent();
    }
    None
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

#[cfg(test)]
mod tests {
    use super::*;

    #[cfg(unix)]
    static PROVIDER_ENV_LOCK: OnceLock<AsyncMutex<()>> = OnceLock::new();

    #[cfg(unix)]
    fn provider_env_lock() -> &'static AsyncMutex<()> {
        PROVIDER_ENV_LOCK.get_or_init(|| AsyncMutex::new(()))
    }

    fn test_session(session_id: &str, agent_type: &str) -> AgentSession {
        AgentSession {
            agent_type: agent_type.into(),
            session_id: session_id.into(),
            conversation_id: None,
            display_id: session_id.into(),
            path: PathBuf::from(format!("{session_id}.jsonl")),
            updated: SystemTime::now(),
            start_timestamp_ms: None,
            end_timestamp_ms: None,
            model: None,
            usage: Default::default(),
            model_usage: Default::default(),
            tools: Default::default(),
            files: Default::default(),
            prompt_preview: None,
            duration_ms: 0,
            cwd: None,
            last_message_at: None,
            events: Default::default(),
        }
    }

    #[cfg(target_os = "windows")]
    #[test]
    fn provider_resolution_accepts_cmd_shims() {
        let temp = tempfile::tempdir().unwrap();
        let shim = temp.path().join("codex.cmd");
        std::fs::write(&shim, "@echo off\r\n").unwrap();
        let path = std::env::join_paths([temp.path()]).unwrap();

        let resolved = resolve_windows_program(
            Path::new("codex"),
            Some(&path),
            Some(OsStr::new(".EXE;.CMD")),
        )
        .unwrap();
        assert_eq!(
            resolved.canonicalize().unwrap(),
            shim.canonicalize().unwrap()
        );
    }

    #[cfg(target_os = "windows")]
    #[test]
    fn windows_provider_execution_is_limited_to_a_non_elevated_profile() {
        let profile = tempfile::tempdir().unwrap();
        let alternate_profile = tempfile::tempdir().unwrap();
        let session = profile.path().join(".codex/sessions/session.jsonl");
        std::fs::create_dir_all(session.parent().unwrap()).unwrap();
        std::fs::write(&session, b"{}\n").unwrap();
        let profiles = [
            alternate_profile.path().to_path_buf(),
            profile.path().to_path_buf(),
        ];

        assert!(validate_windows_provider_context(false, &session, &profiles).is_ok());
        assert!(matches!(
            validate_windows_provider_context(true, &session, &profiles),
            Err(SubmitError::Failed(message)) if message.contains("elevated Windows")
        ));

        let outside = tempfile::NamedTempFile::new().unwrap();
        assert!(matches!(
            validate_windows_provider_context(false, outside.path(), &profiles),
            Err(SubmitError::Failed(message)) if message.contains("outside the current user profile")
        ));
    }

    #[test]
    fn codex_session_version_selects_the_matching_standalone_binary() {
        let temp = tempfile::tempdir().unwrap();
        let session = temp.path().join("session.jsonl");
        std::fs::write(
            &session,
            concat!(
                "{\"type\":\"session_meta\",\"payload\":{",
                "\"id\":\"thread-1\",\"cli_version\":\"0.147.0\"}}\n",
                "{\"type\":\"event_msg\",\"payload\":{}}\n",
            ),
        )
        .unwrap();
        let wrong_arch = temp
            .path()
            .join(format!(
                ".codex/packages/standalone/releases/0.147.0-aaa-{}/bin",
                standalone_target_marker()
            ))
            .join(format!("codex{}", std::env::consts::EXE_SUFFIX));
        let wrong_os = temp
            .path()
            .join(format!(
                ".codex/packages/standalone/releases/0.147.0-{}-wrong-platform/bin",
                std::env::consts::ARCH
            ))
            .join(format!("codex{}", std::env::consts::EXE_SUFFIX));
        let executable = temp
            .path()
            .join(format!(
                ".codex/packages/standalone/releases/0.147.0-{}-{}/bin",
                std::env::consts::ARCH,
                standalone_target_marker()
            ))
            .join(format!("codex{}", std::env::consts::EXE_SUFFIX));
        std::fs::create_dir_all(wrong_arch.parent().unwrap()).unwrap();
        std::fs::write(&wrong_arch, b"wrong architecture").unwrap();
        #[cfg(unix)]
        std::fs::set_permissions(&wrong_arch, std::fs::Permissions::from_mode(0o755)).unwrap();
        std::fs::create_dir_all(wrong_os.parent().unwrap()).unwrap();
        std::fs::write(&wrong_os, b"wrong operating system").unwrap();
        #[cfg(unix)]
        std::fs::set_permissions(&wrong_os, std::fs::Permissions::from_mode(0o755)).unwrap();
        std::fs::create_dir_all(executable.parent().unwrap()).unwrap();
        std::fs::write(&executable, b"probe").unwrap();
        #[cfg(unix)]
        std::fs::set_permissions(&executable, std::fs::Permissions::from_mode(0o755)).unwrap();

        assert_eq!(codex_cli_version(&session).as_deref(), Some("0.147.0"));
        assert_eq!(
            standalone_codex_binary(temp.path(), "0.147.0"),
            Some(executable)
        );
    }

    #[test]
    fn codex_session_version_rejects_a_wrong_platform_only_release() {
        let temp = tempfile::tempdir().unwrap();
        let executable = temp
            .path()
            .join(format!(
                ".codex/packages/standalone/releases/0.147.0-{}-wrong-platform/bin",
                std::env::consts::ARCH
            ))
            .join(format!("codex{}", std::env::consts::EXE_SUFFIX));
        std::fs::create_dir_all(executable.parent().unwrap()).unwrap();
        std::fs::write(&executable, b"wrong operating system").unwrap();
        #[cfg(unix)]
        std::fs::set_permissions(&executable, std::fs::Permissions::from_mode(0o755)).unwrap();

        assert_eq!(standalone_codex_binary(temp.path(), "0.147.0"), None);
    }

    #[test]
    fn gemini_resume_command_never_places_the_message_in_process_arguments() {
        assert_eq!(gemini_resume_args("session-1"), ["--resume", "session-1"]);
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn gemini_resume_streams_the_full_public_message_over_stdin() {
        let _environment_guard = provider_env_lock().lock().await;
        let temp = tempfile::tempdir().unwrap();
        let program = temp.path().join("gemini-probe");
        let arguments = temp.path().join("arguments");
        let input = temp.path().join("input");
        std::fs::write(
            &program,
            format!(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > '{}'\ncat > '{}'\n",
                arguments.display(),
                input.display()
            ),
        )
        .unwrap();
        std::fs::set_permissions(&program, std::fs::Permissions::from_mode(0o755)).unwrap();
        let mut session = test_session("gemini-session", agent_session::AGENT_GEMINI);
        session.path = temp.path().join("session.json");
        session.cwd = Some(temp.path().to_string_lossy().to_string());
        std::fs::write(&session.path, b"{}\n").unwrap();
        let previous_program = std::env::var_os(GEMINI_BIN_ENV);
        unsafe {
            std::env::set_var(GEMINI_BIN_ENV, &program);
        }
        let message = "x".repeat(65_536);

        let result = resume_gemini(&session, &message).await;

        unsafe {
            match previous_program {
                Some(value) => std::env::set_var(GEMINI_BIN_ENV, value),
                None => std::env::remove_var(GEMINI_BIN_ENV),
            }
        }
        result.unwrap();
        assert_eq!(
            std::fs::read_to_string(arguments).unwrap(),
            "--resume\ngemini-session\n"
        );
        assert_eq!(std::fs::read_to_string(input).unwrap(), message);
    }

    #[test]
    fn codex_session_version_rejects_path_injection() {
        let temp = tempfile::tempdir().unwrap();
        let session = temp.path().join("session.jsonl");
        std::fs::write(
            &session,
            "{\"type\":\"session_meta\",\"payload\":{\"cli_version\":\"../../bin/sh\"}}\n",
        )
        .unwrap();

        assert_eq!(codex_cli_version(&session), None);
        assert_eq!(standalone_codex_binary(temp.path(), "../../bin/sh"), None);
    }

    #[cfg(unix)]
    #[test]
    fn codex_session_version_skips_non_executable_standalone_binary() {
        let temp = tempfile::tempdir().unwrap();
        let executable = temp.path().join(format!(
            ".codex/packages/standalone/releases/0.147.0-{}-{}/bin/codex",
            std::env::consts::ARCH,
            standalone_target_marker()
        ));
        std::fs::create_dir_all(executable.parent().unwrap()).unwrap();
        std::fs::write(&executable, b"not executable").unwrap();

        assert_eq!(standalone_codex_binary(temp.path(), "0.147.0"), None);
    }

    #[test]
    fn codex_session_version_skips_malformed_prefix_lines() {
        let temp = tempfile::tempdir().unwrap();
        let session = temp.path().join("session.jsonl");
        std::fs::write(
            &session,
            concat!(
                "not-json\n",
                "{\"type\":\"event_msg\",\"payload\":{}}\n",
                "{\"type\":\"session_meta\",\"payload\":{\"cliVersion\":\"0.147.0\"}}\n",
            ),
        )
        .unwrap();

        assert_eq!(codex_cli_version(&session).as_deref(), Some("0.147.0"));
    }

    #[test]
    fn codex_install_home_follows_the_transcript_instead_of_the_service_user() {
        let expected = PathBuf::from("service-user");
        let path = expected.join(".CoDeX/sessions/2026/08/16/session.jsonl");

        assert_eq!(codex_install_home(&path), Some(expected.clone()));
        assert_eq!(provider_session_home(&path), Some(expected));
        assert_eq!(
            provider_session_home(Path::new(
                "service-user/.claude/projects/repo/session.jsonl"
            )),
            Some(PathBuf::from("service-user"))
        );
        assert_eq!(
            provider_session_home(Path::new(
                "service-user/.gemini/tmp/repo/chats/session.json"
            )),
            Some(PathBuf::from("service-user"))
        );
    }

    #[cfg(unix)]
    #[test]
    fn root_provider_execution_uses_a_non_root_session_identity() {
        assert_eq!(
            provider_user_ids((1001, 1002), Some((2001, 2002))).unwrap(),
            (1001, 1002)
        );
        assert_eq!(
            provider_user_ids((0, 0), Some((2001, 2002))).unwrap(),
            (2001, 2002)
        );
        assert!(matches!(
            provider_user_ids((0, 0), None),
            Err(SubmitError::Failed(_))
        ));
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn provider_child_drops_root_before_exec() {
        if unsafe { libc::geteuid() } != 0 {
            return;
        }
        let _environment_guard = provider_env_lock().lock().await;
        let Some((expected_uid, expected_gid)) = crate::cmd_exec::target_user_ids() else {
            return;
        };
        let previous_sentinel = std::env::var_os("AGENTSIGHT_TEST_PARENT_SECRET");
        unsafe {
            std::env::set_var(
                "AGENTSIGHT_TEST_PARENT_SECRET",
                "must-not-cross-uid-boundary",
            );
        }
        let temp = tempfile::tempdir().unwrap();
        let session_path = temp.path().join(".claude/projects/test/session.jsonl");
        std::fs::create_dir_all(session_path.parent().unwrap()).unwrap();
        std::fs::write(&session_path, b"{}\n").unwrap();
        let account = provider_account(expected_uid).unwrap();
        let mut command = Command::new("sh");
        command
            .args([
                "-c",
                "printf '%s\\n' \"$(id -u)\" \"$(id -g)\" \"$(id -G)\" \"$HOME\" \"$USER\" \"$LOGNAME\" \"${AGENTSIGHT_TEST_PARENT_SECRET+present}\"",
            ])
            .stdout(Stdio::piped());
        configure_provider_identity(&mut command, &session_path).unwrap();

        let output = command.output().await.unwrap();
        assert!(output.status.success());
        let output = String::from_utf8(output.stdout).unwrap();
        let lines = output.lines().collect::<Vec<_>>();
        assert_eq!(lines[0], expected_uid.to_string());
        assert_eq!(lines[1], expected_gid.to_string());
        assert_eq!(lines[2], expected_gid.to_string());
        assert_eq!(Path::new(lines[3]), temp.path());
        assert_eq!(lines[4], account.name.to_string_lossy());
        assert_eq!(lines[5], account.name.to_string_lossy());
        assert_eq!(lines[6], "");
        unsafe {
            match previous_sentinel {
                Some(value) => std::env::set_var("AGENTSIGHT_TEST_PARENT_SECRET", value),
                None => std::env::remove_var("AGENTSIGHT_TEST_PARENT_SECRET"),
            }
        }
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn dropping_the_runtime_closes_the_codex_reader_stdin_handle() {
        let mut child = Command::new("sh")
            .args(["-c", "cat >/dev/null"])
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let stdin = Arc::new(AsyncMutex::new(Some(child.stdin.take().unwrap())));
        let reader_handle = Arc::downgrade(&stdin);

        drop(stdin);

        assert!(reader_handle.upgrade().is_none());
        let status = tokio::time::timeout(Duration::from_secs(2), child.wait())
            .await
            .expect("closing the last stdin owner should stop the provider")
            .unwrap();
        assert!(status.success());
    }

    #[tokio::test]
    async fn runtime_slot_cleanup_does_not_remove_a_slot_held_by_a_waiter() {
        let session_id = format!("cleanup-waiter-{}", now_ms());
        let slot: RuntimeSlot = Arc::new(AsyncMutex::new(None));
        runtimes()
            .lock()
            .await
            .insert(session_id.clone(), Arc::clone(&slot));
        let waiter = Arc::clone(&slot);

        remove_empty_runtime_slot(&session_id, &slot).await;
        assert!(runtimes().lock().await.contains_key(&session_id));

        drop(waiter);
        remove_empty_runtime_slot(&session_id, &slot).await;
        assert!(!runtimes().lock().await.contains_key(&session_id));
    }

    #[tokio::test]
    async fn runtime_slot_rejects_a_concurrent_message_without_waiting() {
        let session_id = format!("concurrent-message-{}", now_ms());
        let session = test_session(&session_id, "unsupported");
        let slot: RuntimeSlot = Arc::new(AsyncMutex::new(None));
        runtimes()
            .lock()
            .await
            .insert(session_id.clone(), Arc::clone(&slot));
        let active_request = slot.lock().await;

        let result = tokio::time::timeout(
            Duration::from_millis(100),
            submit_message(&session, "must not wait"),
        )
        .await
        .expect("a concurrent submit must fail without waiting");

        assert!(matches!(result, Err(SubmitError::Conflict(_))));
        drop(active_request);
        runtimes().lock().await.remove(&session_id);
    }

    #[tokio::test]
    async fn new_provider_start_and_first_send_share_one_deadline() {
        let result = timeout_provider_operation(
            Duration::from_millis(10),
            std::future::pending::<Result<(Option<Runtime>, &'static str), SubmitError>>(),
        )
        .await;

        assert!(
            matches!(result, Err(SubmitError::Failed(message)) if message.contains("within 20 seconds"))
        );
    }

    #[tokio::test]
    async fn failed_runtime_start_does_not_leave_an_empty_slot() {
        let session_id = format!("failed-runtime-start-{}", now_ms());
        let session = test_session(&session_id, "unsupported");

        assert!(matches!(
            submit_message(&session, "unsupported").await,
            Err(SubmitError::Failed(_))
        ));
        assert!(!runtimes().lock().await.contains_key(&session_id));
    }

    #[tokio::test]
    async fn oversized_provider_line_is_discarded_without_losing_the_next_message() {
        let (mut writer, reader) = tokio::io::duplex(64 * 1024);
        let task = tokio::spawn(async move {
            writer
                .write_all(&vec![b'x'; MAX_PROVIDER_MESSAGE_BYTES + 1])
                .await
                .unwrap();
            writer
                .write_all(b"\n{\"id\":7,\"result\":{}}\n")
                .await
                .unwrap();
        });
        let mut reader = BufReader::new(reader);
        let mut line = Vec::new();

        assert_eq!(
            read_provider_line(&mut reader, &mut line, MAX_PROVIDER_MESSAGE_BYTES)
                .await
                .unwrap(),
            ProviderLine::Oversized
        );
        assert!(line.len() <= MAX_PROVIDER_MESSAGE_BYTES);
        assert_eq!(
            read_provider_line(&mut reader, &mut line, MAX_PROVIDER_MESSAGE_BYTES)
                .await
                .unwrap(),
            ProviderLine::Complete
        );
        assert_eq!(
            serde_json::from_slice::<Value>(&line).unwrap(),
            json!({"id":7,"result":{}})
        );
        task.await.unwrap();
    }

    #[tokio::test]
    async fn codex_reader_accepts_a_bounded_turn_completion_above_one_megabyte() {
        let payload = format!(
            "{{\"method\":\"turn/completed\",\"params\":{{\"turn\":{{\"id\":\"turn-1\",\"status\":\"completed\",\"items\":[{{\"type\":\"agentMessage\",\"text\":\"{}\"}}]}}}}}}\n",
            "x".repeat(MAX_PROVIDER_MESSAGE_BYTES + 1)
        );
        let mut reader = BufReader::new(payload.as_bytes());
        let mut line = Vec::new();

        assert_eq!(
            read_provider_line(&mut reader, &mut line, MAX_CODEX_MESSAGE_BYTES)
                .await
                .unwrap(),
            ProviderLine::Complete
        );
        assert!(line.len() > MAX_PROVIDER_MESSAGE_BYTES);
        assert_eq!(
            serde_json::from_slice::<Value>(&line).unwrap()["method"],
            json!("turn/completed")
        );
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn oversized_codex_message_closes_transport_and_clears_state() {
        let mut child = Command::new("sh")
            .args(["-c", "cat >/dev/null"])
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let stdin = Arc::new(AsyncMutex::new(Some(child.stdin.take().unwrap())));
        let state = Arc::new(StdMutex::new(CodexState {
            thread_id: "thread-1".into(),
            active_turn: Some("turn-1".into()),
            starting: true,
        }));
        let responses = Arc::new(StdMutex::new(HashMap::new()));
        let (response_tx, response_rx) = oneshot::channel();
        responses.lock().unwrap().insert(7, response_tx);

        fail_oversized_codex_transport(&state, &responses, &Arc::downgrade(&stdin)).await;

        let error = response_rx.await.unwrap().unwrap_err();
        assert!(error.contains("transport limit"));
        assert!(responses.lock().unwrap().is_empty());
        {
            let state = state.lock().unwrap();
            assert!(!state.starting);
            assert!(state.active_turn.is_none());
        }
        let status = tokio::time::timeout(Duration::from_secs(2), child.wait())
            .await
            .expect("closing an oversized transport should stop the provider")
            .unwrap();
        assert!(status.success());
    }

    #[test]
    fn codex_resume_omits_reconstructed_turn_history() {
        assert_eq!(
            codex_resume_request("thread-1"),
            json!({"method":"thread/resume","id":2,"params":{
                "threadId":"thread-1","excludeTurns":true
            }})
        );
    }

    #[tokio::test]
    async fn codex_request_errors_are_returned_to_the_submitter() {
        let pending = Arc::new(StdMutex::new(HashMap::new()));
        let (response_tx, response_rx) = oneshot::channel();
        pending.lock().unwrap().insert(7, response_tx);

        complete_codex_response(
            &json!({"id":7,"error":{"code":-32602,"message":"unsupported input"}}),
            &pending,
        );

        let error = response_rx.await.unwrap().unwrap_err();
        assert!(error.contains("unsupported input"));
        assert!(pending.lock().unwrap().is_empty());
    }

    #[tokio::test]
    async fn codex_server_request_id_collision_does_not_complete_client_request() {
        let pending = Arc::new(StdMutex::new(HashMap::new()));
        let (response_tx, response_rx) = oneshot::channel();
        pending.lock().unwrap().insert(7, response_tx);

        let server_request =
            json!({"id":7,"method":"item/commandExecution/requestApproval","params":{}});
        complete_codex_response(&server_request, &pending);
        assert!(pending.lock().unwrap().contains_key(&7));
        assert_eq!(
            codex_server_request_rejection(&server_request),
            Some(json!({"id":7,"error":{
                "code":-32601,
                "message":"AgentSight does not support Codex server requests"
            }}))
        );

        complete_codex_response(&json!({"id":7,"result":{}}), &pending);
        assert!(response_rx.await.unwrap().is_ok());
        assert!(pending.lock().unwrap().is_empty());
    }

    #[tokio::test]
    async fn claude_assistant_output_acknowledges_then_completes_the_turn() {
        let (mut writer, reader) = tokio::io::duplex(1024);
        let state = Arc::new(StdMutex::new(ClaudeState {
            starting: true,
            active: false,
        }));
        let response = Arc::new(StdMutex::new(None));
        let (response_tx, response_rx) = oneshot::channel();
        *response.lock().unwrap() = Some(response_tx);
        let task = tokio::spawn(read_claude(
            BufReader::new(reader),
            Arc::clone(&state),
            Arc::clone(&response),
        ));

        writer
            .write_all(b"{\"type\":\"assistant\",\"message\":{}}\n")
            .await
            .unwrap();
        assert!(response_rx.await.unwrap().is_ok());
        assert!(state.lock().unwrap().active);

        writer
            .write_all(b"{\"type\":\"result\",\"subtype\":\"success\"}\n")
            .await
            .unwrap();
        writer.shutdown().await.unwrap();
        task.await.unwrap();
        let state = state.lock().unwrap();
        assert!(!state.starting);
        assert!(!state.active);
    }

    #[tokio::test]
    async fn claude_user_echo_acknowledges_message_acceptance() {
        let (mut writer, reader) = tokio::io::duplex(1024);
        let state = Arc::new(StdMutex::new(ClaudeState {
            starting: true,
            active: false,
        }));
        let response = Arc::new(StdMutex::new(None));
        let (response_tx, response_rx) = oneshot::channel();
        *response.lock().unwrap() = Some(response_tx);
        let task = tokio::spawn(read_claude(
            BufReader::new(reader),
            Arc::clone(&state),
            Arc::clone(&response),
        ));

        writer
            .write_all(b"{\"type\":\"user\",\"message\":{}}\n")
            .await
            .unwrap();
        assert!(response_rx.await.unwrap().is_ok());
        assert!(state.lock().unwrap().active);

        writer
            .write_all(b"{\"type\":\"result\",\"subtype\":\"success\"}\n")
            .await
            .unwrap();
        writer.shutdown().await.unwrap();
        task.await.unwrap();
        assert!(!state.lock().unwrap().active);
    }

    #[tokio::test]
    async fn claude_result_errors_are_returned_to_the_submitter() {
        let (mut writer, reader) = tokio::io::duplex(1024);
        let state = Arc::new(StdMutex::new(ClaudeState {
            starting: true,
            active: false,
        }));
        let response = Arc::new(StdMutex::new(None));
        let (response_tx, response_rx) = oneshot::channel();
        *response.lock().unwrap() = Some(response_tx);
        let task = tokio::spawn(read_claude(
            BufReader::new(reader),
            Arc::clone(&state),
            Arc::clone(&response),
        ));

        writer
            .write_all(
                b"{\"type\":\"result\",\"subtype\":\"error_during_execution\",\"error\":\"authentication required\"}\n",
            )
            .await
            .unwrap();
        let error = response_rx.await.unwrap().unwrap_err();
        assert!(error.contains("authentication required"));

        writer.shutdown().await.unwrap();
        task.await.unwrap();
        let state = state.lock().unwrap();
        assert!(!state.starting);
        assert!(!state.active);
    }
}
