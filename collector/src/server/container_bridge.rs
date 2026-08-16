// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! JSONL bridge used by a host AgentSight Node to manage sessions in a Docker
//! container without copying the container's provider credentials to the host.

use crate::server::session_runtime::{SubmitError, submit_message};
use crate::sources::agent_native::{self as agent_native_sessions, SessionCache};
use agent_session::AgentSession;
use serde::{Deserialize, Serialize, de::DeserializeOwned};
use serde_json::{Value, json};
use std::process::Stdio;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncBufRead, AsyncBufReadExt, AsyncWrite, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, ChildStdout, Command};
use tokio::sync::Mutex;

const LIST_SESSIONS: &str = "sessions/list";
const GET_SESSION: &str = "session/get";
const MESSAGE_SESSION: &str = "session/message";
const MAX_BRIDGE_FRAME_BYTES: usize = 8 * 1024 * 1024;
const BRIDGE_OPERATION_TIMEOUT: Duration = Duration::from_secs(30);
const DOCKER_COMMAND_TIMEOUT: Duration = Duration::from_secs(10);

#[derive(Debug, Deserialize, Serialize)]
struct BridgeRequest {
    id: u64,
    method: String,
    #[serde(default)]
    params: Value,
}

#[derive(Debug, Deserialize, Serialize)]
struct BridgeResponse {
    id: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<BridgeError>,
}

#[derive(Debug, Deserialize, Serialize)]
struct BridgeError {
    code: String,
    message: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct SessionParams {
    session_id: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct MessageParams {
    session_id: String,
    message: String,
}

#[derive(Debug)]
pub enum ContainerBridgeError {
    NotFound(String),
    Conflict(String),
    Failed(String),
}

impl ContainerBridgeError {
    pub fn message(&self) -> &str {
        match self {
            Self::NotFound(message) | Self::Conflict(message) | Self::Failed(message) => message,
        }
    }
}

pub async fn run_stdio_bridge() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let mut input = BufReader::new(tokio::io::stdin());
    let mut output = tokio::io::stdout();
    let mut cache = SessionCache::new();
    loop {
        let line = match read_bounded_line(&mut input, MAX_BRIDGE_FRAME_BYTES).await? {
            BoundedLine::Eof => break,
            BoundedLine::TooLarge => {
                write_bridge_response(
                    &mut output,
                    BridgeResponse {
                        id: 0,
                        result: None,
                        error: Some(BridgeError {
                            code: "request_too_large".into(),
                            message: format!(
                                "bridge request exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"
                            ),
                        }),
                    },
                )
                .await?;
                continue;
            }
            BoundedLine::Line(line) => line,
        };
        let response = match serde_json::from_slice::<BridgeRequest>(&line) {
            Ok(request) => dispatch_bridge_request(request, &mut cache).await,
            Err(error) => BridgeResponse {
                id: 0,
                result: None,
                error: Some(BridgeError {
                    code: "invalid_request".into(),
                    message: format!("invalid bridge request: {error}"),
                }),
            },
        };
        write_bridge_response(&mut output, response).await?;
    }
    Ok(())
}

enum BoundedLine {
    Eof,
    Line(Vec<u8>),
    TooLarge,
}

async fn read_bounded_line<R: AsyncBufRead + Unpin>(
    reader: &mut R,
    max_bytes: usize,
) -> std::io::Result<BoundedLine> {
    let mut line = Vec::new();
    let mut too_large = false;
    loop {
        let available = reader.fill_buf().await?;
        if available.is_empty() {
            return Ok(if line.is_empty() && !too_large {
                BoundedLine::Eof
            } else if too_large {
                BoundedLine::TooLarge
            } else {
                BoundedLine::Line(line)
            });
        }
        let newline = available.iter().position(|byte| *byte == b'\n');
        let consumed = newline.map_or(available.len(), |index| index + 1);
        if !too_large {
            if line.len().saturating_add(consumed) > max_bytes {
                too_large = true;
                line.clear();
            } else {
                line.extend_from_slice(&available[..consumed]);
            }
        }
        reader.consume(consumed);
        if newline.is_some() {
            return Ok(if too_large {
                BoundedLine::TooLarge
            } else {
                BoundedLine::Line(line)
            });
        }
    }
}

async fn write_bridge_response<W: AsyncWrite + Unpin>(
    output: &mut W,
    response: BridgeResponse,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let response_id = response.id;
    let mut encoded = serde_json::to_vec(&response)?;
    if encoded.len().saturating_add(1) > MAX_BRIDGE_FRAME_BYTES {
        encoded = serde_json::to_vec(&BridgeResponse {
            id: response_id,
            result: None,
            error: Some(BridgeError {
                code: "response_too_large".into(),
                message: format!("bridge response exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"),
            }),
        })?;
    }
    encoded.push(b'\n');
    output.write_all(&encoded).await?;
    output.flush().await?;
    Ok(())
}

async fn dispatch_bridge_request(
    request: BridgeRequest,
    cache: &mut SessionCache,
) -> BridgeResponse {
    let result = match request.method.as_str() {
        LIST_SESSIONS => {
            let limit = request
                .params
                .get("limit")
                .and_then(Value::as_u64)
                .unwrap_or(25) as usize;
            Ok(json!({ "sessions": discover_sessions(cache, limit) }))
        }
        GET_SESSION => parse_params::<SessionParams>(&request.params).and_then(|params| {
            find_native_session(cache, &params.session_id)
                .map(|session| json!({ "session": session }))
                .ok_or_else(|| bridge_error("not_found", "session not found"))
        }),
        MESSAGE_SESSION => match parse_params::<MessageParams>(&request.params) {
            Ok(params) if params.message.trim().is_empty() || params.message.len() > 65_536 => {
                Err(bridge_error(
                    "invalid_params",
                    "message must contain between 1 and 65536 bytes",
                ))
            }
            Ok(params) => match find_native_session(cache, &params.session_id) {
                Some(session) => match submit_message(&session, params.message.trim()).await {
                    Ok(result) => Ok(json!({
                        "agent_type": session.agent_type,
                        "transport": result.transport,
                    })),
                    Err(SubmitError::Conflict(message)) => Err(bridge_error("conflict", message)),
                    Err(SubmitError::Failed(message)) => Err(bridge_error("failed", message)),
                },
                None => Err(bridge_error("not_found", "session not found")),
            },
            Err(error) => Err(error),
        },
        _ => Err(bridge_error(
            "method_not_found",
            format!("unsupported bridge method: {}", request.method),
        )),
    };
    match result {
        Ok(result) => BridgeResponse {
            id: request.id,
            result: Some(result),
            error: None,
        },
        Err(error) => BridgeResponse {
            id: request.id,
            result: None,
            error: Some(error),
        },
    }
}

fn parse_params<T: DeserializeOwned>(value: &Value) -> Result<T, BridgeError> {
    serde_json::from_value(value.clone())
        .map_err(|error| bridge_error("invalid_params", error.to_string()))
}

fn bridge_error(code: &str, message: impl Into<String>) -> BridgeError {
    BridgeError {
        code: code.into(),
        message: message.into(),
    }
}

fn discover_sessions(cache: &mut SessionCache, limit: usize) -> Vec<AgentSession> {
    agent_native_sessions::discover_sessions(cache, None, None, limit, Duration::ZERO)
}

fn find_native_session(cache: &mut SessionCache, session_id: &str) -> Option<AgentSession> {
    agent_native_sessions::find_session_by_id(cache, session_id)
}

#[derive(Clone, Default)]
pub struct ContainerBridges {
    bridges: Arc<Vec<Arc<Mutex<DockerBridge>>>>,
}

impl ContainerBridges {
    pub fn new(containers: &[String]) -> Result<Self, String> {
        let bridges = containers
            .iter()
            .map(|container| {
                validate_container_name(container)?;
                Ok(Arc::new(Mutex::new(DockerBridge::new(container.clone()))))
            })
            .collect::<Result<Vec<_>, String>>()?;
        Ok(Self {
            bridges: Arc::new(bridges),
        })
    }

    pub fn is_empty(&self) -> bool {
        self.bridges.is_empty()
    }

    pub async fn list_sessions(&self, limit: usize) -> Vec<AgentSession> {
        let mut sessions = Vec::new();
        for bridge in self.bridges.iter() {
            let mut bridge = bridge.lock().await;
            match bridge.list_sessions(limit).await {
                Ok(mut discovered) => sessions.append(&mut discovered),
                Err(error) => log::warn!(
                    "Docker container {} session discovery failed: {}",
                    bridge.container,
                    error.message()
                ),
            }
        }
        sessions.sort_by_key(|session| std::cmp::Reverse(session.updated));
        sessions.truncate(limit.clamp(1, 25));
        sessions
    }

    pub async fn get_session(
        &self,
        session_id: &str,
    ) -> Result<Option<(String, AgentSession)>, ContainerBridgeError> {
        let mut found = None;
        let mut first_error = None;
        for bridge in self.bridges.iter() {
            let mut bridge = bridge.lock().await;
            match bridge.get_session(session_id).await {
                Ok(Some(session)) => {
                    if found.is_some() {
                        return Err(ContainerBridgeError::Conflict(format!(
                            "session {session_id} exists in more than one configured container"
                        )));
                    }
                    found = Some((bridge.container.clone(), session));
                }
                Ok(None) => {}
                Err(error) => {
                    log::warn!(
                        "Docker container {} session lookup failed: {}",
                        bridge.container,
                        error.message()
                    );
                    if first_error.is_none() {
                        first_error = Some(error);
                    }
                }
            }
        }
        match (found, first_error) {
            (Some(found), _) => Ok(Some(found)),
            (None, Some(error)) => Err(error),
            (None, None) => Ok(None),
        }
    }

    pub async fn send_message(
        &self,
        container: &str,
        session_id: &str,
        message: &str,
    ) -> Result<(String, String), ContainerBridgeError> {
        for bridge in self.bridges.iter() {
            let mut bridge = bridge.lock().await;
            if bridge.container == container {
                return bridge.send_message(session_id, message).await;
            }
        }
        Err(ContainerBridgeError::Failed(format!(
            "Docker container {container} is no longer configured"
        )))
    }
}

struct DockerBridge {
    container: String,
    process: Option<BridgeProcess>,
    next_id: u64,
}

#[derive(Debug, Default, Eq, PartialEq)]
struct ContainerExecution {
    user: Option<String>,
    workdir: Option<String>,
    codex_home: Option<String>,
}

struct BridgeProcess {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

impl DockerBridge {
    fn new(container: String) -> Self {
        Self {
            container,
            process: None,
            next_id: 0,
        }
    }

    async fn list_sessions(
        &mut self,
        limit: usize,
    ) -> Result<Vec<AgentSession>, ContainerBridgeError> {
        let result = self.call(LIST_SESSIONS, json!({ "limit": limit })).await?;
        serde_json::from_value(
            result
                .get("sessions")
                .cloned()
                .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted sessions".into()))?,
        )
        .map_err(|error| ContainerBridgeError::Failed(error.to_string()))
    }

    async fn get_session(
        &mut self,
        session_id: &str,
    ) -> Result<Option<AgentSession>, ContainerBridgeError> {
        match self
            .call(GET_SESSION, json!({ "session_id": session_id }))
            .await
        {
            Ok(result) => serde_json::from_value(
                result
                    .get("session")
                    .cloned()
                    .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted session".into()))?,
            )
            .map(Some)
            .map_err(|error| ContainerBridgeError::Failed(error.to_string())),
            Err(ContainerBridgeError::NotFound(_)) => Ok(None),
            Err(error) => Err(error),
        }
    }

    async fn send_message(
        &mut self,
        session_id: &str,
        message: &str,
    ) -> Result<(String, String), ContainerBridgeError> {
        let result = self
            .call(
                MESSAGE_SESSION,
                json!({ "session_id": session_id, "message": message }),
            )
            .await?;
        let agent_type = result
            .get("agent_type")
            .and_then(Value::as_str)
            .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted agent_type".into()))?;
        let transport = result
            .get("transport")
            .and_then(Value::as_str)
            .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted transport".into()))?;
        Ok((agent_type.into(), format!("docker-exec/{transport}")))
    }

    async fn call(&mut self, method: &str, params: Value) -> Result<Value, ContainerBridgeError> {
        match tokio::time::timeout(
            BRIDGE_OPERATION_TIMEOUT,
            self.call_with_deadline(method, params),
        )
        .await
        {
            Ok(Ok(result)) => Ok(result),
            Ok(Err(error)) => {
                if matches!(error, ContainerBridgeError::Failed(_)) {
                    self.process = None;
                }
                Err(error)
            }
            Err(_) => {
                self.process = None;
                Err(ContainerBridgeError::Failed(format!(
                    "Docker bridge operation timed out after {} seconds",
                    BRIDGE_OPERATION_TIMEOUT.as_secs()
                )))
            }
        }
    }

    async fn call_with_deadline(
        &mut self,
        method: &str,
        params: Value,
    ) -> Result<Value, ContainerBridgeError> {
        self.ensure_process().await?;
        self.next_id += 1;
        let id = self.next_id;
        let request = BridgeRequest {
            id,
            method: method.into(),
            params,
        };
        let mut encoded = serde_json::to_vec(&request)
            .map_err(|error| ContainerBridgeError::Failed(error.to_string()))?;
        encoded.push(b'\n');
        let process = self.process.as_mut().expect("bridge process initialized");
        if let Err(error) = process.stdin.write_all(&encoded).await {
            self.process = None;
            return Err(ContainerBridgeError::Failed(format!(
                "failed to write Docker bridge request: {error}"
            )));
        }
        if let Err(error) = process.stdin.flush().await {
            self.process = None;
            return Err(ContainerBridgeError::Failed(format!(
                "failed to flush Docker bridge request: {error}"
            )));
        }

        loop {
            let line = match read_bounded_line(&mut process.stdout, MAX_BRIDGE_FRAME_BYTES).await {
                Ok(BoundedLine::Eof) => {
                    self.process = None;
                    return Err(ContainerBridgeError::Failed(
                        "Docker bridge closed its output".into(),
                    ));
                }
                Ok(BoundedLine::TooLarge) => {
                    self.process = None;
                    return Err(ContainerBridgeError::Failed(format!(
                        "Docker bridge response exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"
                    )));
                }
                Ok(BoundedLine::Line(line)) => line,
                Err(error) => {
                    self.process = None;
                    return Err(ContainerBridgeError::Failed(format!(
                        "failed to read Docker bridge response: {error}"
                    )));
                }
            };
            let response: BridgeResponse = serde_json::from_slice(&line).map_err(|error| {
                ContainerBridgeError::Failed(format!("invalid Docker bridge response: {error}"))
            })?;
            if response.id != id {
                continue;
            }
            if let Some(error) = response.error {
                return Err(match error.code.as_str() {
                    "not_found" => ContainerBridgeError::NotFound(error.message),
                    "conflict" => ContainerBridgeError::Conflict(error.message),
                    _ => ContainerBridgeError::Failed(error.message),
                });
            }
            return response
                .result
                .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted result".into()));
        }
    }

    async fn ensure_process(&mut self) -> Result<(), ContainerBridgeError> {
        if let Some(process) = self.process.as_mut()
            && process.child.try_wait().ok().flatten().is_none()
        {
            return Ok(());
        }
        let execution = inspect_container_execution(&self.container).await?;
        let user = match (&execution.user, &execution.codex_home) {
            (Some(user), _) => Some(user.clone()),
            (None, Some(codex_home)) => {
                Some(inspect_path_owner(&self.container, codex_home).await?)
            }
            (None, None) => None,
        };
        let mut command = docker_bridge_command(
            &self.container,
            user.as_deref(),
            execution.workdir.as_deref(),
            execution.codex_home.as_deref(),
        )?;
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|error| {
                ContainerBridgeError::Failed(format!(
                    "failed to start Docker bridge for {}: {error}",
                    self.container
                ))
            })?;
        let stdin = child.stdin.take().ok_or_else(|| {
            ContainerBridgeError::Failed("Docker bridge stdin unavailable".into())
        })?;
        let stdout = child.stdout.take().ok_or_else(|| {
            ContainerBridgeError::Failed("Docker bridge stdout unavailable".into())
        })?;
        self.process = Some(BridgeProcess {
            child,
            stdin,
            stdout: BufReader::new(stdout),
        });
        Ok(())
    }
}

async fn inspect_container_execution(
    container: &str,
) -> Result<ContainerExecution, ContainerBridgeError> {
    validate_container_name(container).map_err(ContainerBridgeError::Failed)?;
    let mut command = Command::new("docker");
    command.kill_on_drop(true).args(["inspect", container]);
    let output = tokio::time::timeout(DOCKER_COMMAND_TIMEOUT, command.output())
        .await
        .map_err(|_| {
            ContainerBridgeError::Failed(format!(
                "Docker inspect for {container} timed out after {} seconds",
                DOCKER_COMMAND_TIMEOUT.as_secs()
            ))
        })?
        .map_err(|error| {
            ContainerBridgeError::Failed(format!(
                "failed to inspect Docker container {container}: {error}"
            ))
        })?;
    if !output.status.success() {
        return Err(ContainerBridgeError::Failed(format!(
            "Docker container {container} is unavailable: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    let inspected: Value = serde_json::from_slice(&output.stdout).map_err(|error| {
        ContainerBridgeError::Failed(format!("invalid docker inspect response: {error}"))
    })?;
    parse_container_execution(&inspected)
}

fn parse_container_execution(value: &Value) -> Result<ContainerExecution, ContainerBridgeError> {
    let inspected = value
        .as_array()
        .and_then(|items| items.first())
        .ok_or_else(|| {
            ContainerBridgeError::Failed("docker inspect returned no container".into())
        })?;
    let config = inspected
        .get("Config")
        .ok_or_else(|| ContainerBridgeError::Failed("docker inspect omitted Config".into()))?;
    let labels = config.get("Labels").and_then(Value::as_object);
    let label = |name: &str| {
        labels
            .and_then(|labels| labels.get(name))
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(str::to_string)
    };
    let configured_user = config
        .get("User")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty());
    let user = label("com.agentsight.user").or_else(|| {
        configured_user
            .filter(|value| !is_root_container_user(value))
            .map(str::to_string)
    });
    let workdir = label("com.agentsight.workspace").or_else(|| {
        config
            .get("WorkingDir")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(str::to_string)
    });
    let codex_home = label("com.agentsight.codex-home");
    for (name, path) in [
        ("com.agentsight.workspace", workdir.as_deref()),
        ("com.agentsight.codex-home", codex_home.as_deref()),
    ] {
        if let Some(path) = path {
            validate_container_path(name, path)?;
        }
    }
    Ok(ContainerExecution {
        user,
        workdir,
        codex_home,
    })
}

fn is_root_container_user(value: &str) -> bool {
    matches!(value.split(':').next(), Some("root" | "0"))
}

async fn inspect_path_owner(container: &str, path: &str) -> Result<String, ContainerBridgeError> {
    let mut command = Command::new("docker");
    command
        .kill_on_drop(true)
        .args(["exec", container, "stat", "-c", "%u", path]);
    let output = tokio::time::timeout(DOCKER_COMMAND_TIMEOUT, command.output())
        .await
        .map_err(|_| {
            ContainerBridgeError::Failed(format!(
                "Docker owner lookup for {path} in {container} timed out after {} seconds",
                DOCKER_COMMAND_TIMEOUT.as_secs()
            ))
        })?
        .map_err(|error| {
            ContainerBridgeError::Failed(format!(
                "failed to inspect {path} owner in Docker container {container}: {error}"
            ))
        })?;
    if !output.status.success() {
        return Err(ContainerBridgeError::Failed(format!(
            "could not resolve the agent user from {path} in Docker container {container}: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    let uid = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if uid.is_empty() || !uid.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ContainerBridgeError::Failed(format!(
            "invalid owner UID returned for {path} in Docker container {container}"
        )));
    }
    Ok(uid)
}

fn docker_bridge_command(
    container: &str,
    user: Option<&str>,
    workdir: Option<&str>,
    codex_home: Option<&str>,
) -> Result<Command, ContainerBridgeError> {
    validate_container_name(container).map_err(ContainerBridgeError::Failed)?;
    let mut command = Command::new("docker");
    command.kill_on_drop(true);
    command.args(["exec", "-i"]);
    if let Some(user) = user {
        command.args(["--user", user]);
    }
    if let Some(workdir) = workdir {
        validate_container_path("workdir", workdir)?;
        command.args(["--workdir", workdir]);
    }
    if let Some(codex_home) = codex_home {
        validate_container_path("codex-home", codex_home)?;
        command.args(["--env", &format!("CODEX_HOME={codex_home}")]);
        if let Some(home) = codex_home.strip_suffix("/.codex") {
            command.args(["--env", &format!("HOME={home}")]);
        }
    }
    command.args([container, "agentsight", "bridge"]);
    Ok(command)
}

fn validate_container_path(name: &str, path: &str) -> Result<(), ContainerBridgeError> {
    let normalized = !path
        .split('/')
        .any(|component| matches!(component, "." | ".."));
    if path.starts_with('/') && path.len() <= 4096 && !path.contains('\0') && normalized {
        Ok(())
    } else {
        Err(ContainerBridgeError::Failed(format!(
            "invalid absolute container path in {name}: {path:?}"
        )))
    }
}

fn validate_container_name(container: &str) -> Result<(), String> {
    let valid = !container.is_empty()
        && container.len() <= 128
        && container
            .bytes()
            .enumerate()
            .all(|(index, byte)| match byte {
                b'a'..=b'z' | b'A'..=b'Z' | b'0'..=b'9' => true,
                b'_' | b'.' | b'-' => index > 0,
                _ => false,
            });
    valid
        .then_some(())
        .ok_or_else(|| format!("invalid Docker container name or ID: {container:?}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn container_names_are_data_not_docker_options() {
        for valid in ["ebpfos-devcontainer-dev-1", "a.b_c", &"a".repeat(64)] {
            assert!(validate_container_name(valid).is_ok());
        }
        for invalid in ["", "--privileged", "name/child", "name child"] {
            assert!(validate_container_name(invalid).is_err());
        }
    }

    #[test]
    fn bridge_protocol_round_trips_without_provider_credentials() {
        let request = BridgeRequest {
            id: 7,
            method: MESSAGE_SESSION.into(),
            params: json!({"session_id":"s-1","message":"continue"}),
        };
        let encoded = serde_json::to_string(&request).unwrap();
        let decoded: BridgeRequest = serde_json::from_str(&encoded).unwrap();
        assert_eq!(decoded.id, 7);
        assert_eq!(decoded.params["message"], "continue");
        assert!(!encoded.contains("auth"));
    }

    #[test]
    fn execution_uses_agentsight_labels_and_valid_absolute_paths() {
        let inspected = json!([{
            "Config": {
                "User": "root",
                "WorkingDir": "/",
                "Labels": {
                    "com.agentsight.user": "vscode",
                    "com.agentsight.workspace": "/workspaces/ebpfos",
                    "com.agentsight.codex-home": "/home/vscode/.codex"
                }
            }
        }]);
        assert_eq!(
            parse_container_execution(&inspected).unwrap(),
            ContainerExecution {
                user: Some("vscode".into()),
                workdir: Some("/workspaces/ebpfos".into()),
                codex_home: Some("/home/vscode/.codex".into()),
            }
        );
    }

    #[test]
    fn execution_falls_back_to_codex_home_owner_but_rejects_relative_paths() {
        let inspected = json!([{
            "Config": {
                "User": "",
                "WorkingDir": "",
                "Labels": {"com.agentsight.codex-home": "/home/vscode/.codex"}
            }
        }]);
        assert_eq!(
            parse_container_execution(&inspected).unwrap(),
            ContainerExecution {
                user: None,
                workdir: None,
                codex_home: Some("/home/vscode/.codex".into()),
            }
        );
        let root_image = json!([{
            "Config": {
                "User": "root:root",
                "WorkingDir": "/",
                "Labels": {"com.agentsight.codex-home": "/home/vscode/.codex"}
            }
        }]);
        assert_eq!(
            parse_container_execution(&root_image).unwrap().user,
            None,
            "a root image user must not override the Codex home owner"
        );
        let invalid = json!([{
            "Config": {
                "Labels": {"com.agentsight.workspace": "../../host"}
            }
        }]);
        assert!(parse_container_execution(&invalid).is_err());
        assert!(validate_container_path("workspace", "/workspaces/../host").is_err());
    }

    #[test]
    fn bridge_command_propagates_codex_and_unix_home() {
        let command = docker_bridge_command(
            "ebpfos-dev",
            Some("1001"),
            Some("/workspaces/ebpfos"),
            Some("/home/vscode/.codex"),
        )
        .unwrap();
        let args = command
            .as_std()
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        assert_eq!(
            args,
            [
                "exec",
                "-i",
                "--user",
                "1001",
                "--workdir",
                "/workspaces/ebpfos",
                "--env",
                "CODEX_HOME=/home/vscode/.codex",
                "--env",
                "HOME=/home/vscode",
                "ebpfos-dev",
                "agentsight",
                "bridge",
            ]
        );
    }

    #[tokio::test]
    async fn bridge_frames_are_bounded_and_recover_at_newline() {
        let (mut writer, reader) = tokio::io::duplex(64);
        let write = tokio::spawn(async move {
            writer.write_all(b"123456789\nok\n").await.unwrap();
        });
        let mut reader = BufReader::new(reader);
        assert!(matches!(
            read_bounded_line(&mut reader, 8).await.unwrap(),
            BoundedLine::TooLarge
        ));
        match read_bounded_line(&mut reader, 8).await.unwrap() {
            BoundedLine::Line(line) => assert_eq!(line, b"ok\n"),
            _ => panic!("expected the next bounded frame"),
        }
        write.await.unwrap();
    }
}
