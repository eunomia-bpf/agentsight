// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! JSONL bridge used by a host AgentSight Node to manage sessions in a Docker
//! container without copying provider credentials to the host.

use crate::server::session_runtime::{
    ProviderLine, SubmitError, read_provider_line, submit_message,
};
use crate::sources::agent_native::{self as agent_native_sessions, SessionCache};
use agent_session::AgentSession;
use futures::future::join_all;
use serde::{Deserialize, Serialize, de::DeserializeOwned};
use serde_json::{Value, json};
use std::process::Stdio;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncWrite, AsyncWriteExt, BufReader};
use tokio::process::Command;

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
    let mut line = Vec::new();
    loop {
        match read_provider_line(&mut input, &mut line, MAX_BRIDGE_FRAME_BYTES).await? {
            ProviderLine::Eof => break,
            ProviderLine::Oversized => {
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
            ProviderLine::Complete => {}
        }
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
    agent_native_sessions::find_session(cache, session_id)
}

#[derive(Clone, Default)]
pub struct ContainerBridges {
    containers: Arc<Vec<String>>,
}

impl ContainerBridges {
    pub fn new(containers: &[String]) -> Result<Self, String> {
        for container in containers {
            validate_container_name(container)?;
        }
        Ok(Self {
            containers: Arc::new(containers.to_vec()),
        })
    }

    pub fn is_empty(&self) -> bool {
        self.containers.is_empty()
    }

    pub async fn list_sessions(&self, limit: usize) -> Vec<AgentSession> {
        let mut sessions = Vec::new();
        let calls = self.containers.iter().map(|container| async move {
            (container, list_container_sessions(container, limit).await)
        });
        for (container, result) in join_all(calls).await {
            match result {
                Ok(mut discovered) => sessions.append(&mut discovered),
                Err(error) => log::warn!(
                    "Docker container {} session discovery failed: {}",
                    container,
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
        let calls = self.containers.iter().map(|container| async move {
            (
                container,
                get_container_session(container, session_id).await,
            )
        });
        for (container, result) in join_all(calls).await {
            match result {
                Ok(Some(session)) => {
                    if found.is_some() {
                        return Err(ContainerBridgeError::Conflict(format!(
                            "session {session_id} exists in more than one configured container"
                        )));
                    }
                    found = Some((container.clone(), session));
                }
                Ok(None) => {}
                Err(error) => {
                    log::warn!(
                        "Docker container {} session lookup failed: {}",
                        container,
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
        if self
            .containers
            .iter()
            .any(|configured| configured == container)
        {
            return send_container_message(container, session_id, message).await;
        }
        Err(ContainerBridgeError::Failed(format!(
            "Docker container {container} is no longer configured"
        )))
    }
}

#[derive(Debug, Default, Eq, PartialEq)]
struct ContainerExecution {
    user: Option<String>,
    workdir: Option<String>,
    home: Option<String>,
}

async fn list_container_sessions(
    container: &str,
    limit: usize,
) -> Result<Vec<AgentSession>, ContainerBridgeError> {
    let result = call_container(container, LIST_SESSIONS, json!({ "limit": limit })).await?;
    serde_json::from_value(
        result
            .get("sessions")
            .cloned()
            .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted sessions".into()))?,
    )
    .map_err(|error| ContainerBridgeError::Failed(error.to_string()))
}

async fn get_container_session(
    container: &str,
    session_id: &str,
) -> Result<Option<AgentSession>, ContainerBridgeError> {
    match call_container(container, GET_SESSION, json!({ "session_id": session_id })).await {
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

async fn send_container_message(
    container: &str,
    session_id: &str,
    message: &str,
) -> Result<(String, String), ContainerBridgeError> {
    let result = call_container(
        container,
        MESSAGE_SESSION,
        json!({ "session_id": session_id, "message": message }),
    )
    .await?;
    let field = |name| {
        result
            .get(name)
            .and_then(Value::as_str)
            .ok_or_else(|| ContainerBridgeError::Failed(format!("bridge omitted {name}")))
    };
    Ok((
        field("agent_type")?.into(),
        format!("docker-exec/{}", field("transport")?),
    ))
}

async fn call_container(
    container: &str,
    method: &str,
    params: Value,
) -> Result<Value, ContainerBridgeError> {
    tokio::time::timeout(
        BRIDGE_OPERATION_TIMEOUT,
        call_container_with_deadline(container, method, params),
    )
    .await
    .map_err(|_| {
        ContainerBridgeError::Failed(format!(
            "Docker bridge operation timed out after {} seconds",
            BRIDGE_OPERATION_TIMEOUT.as_secs()
        ))
    })?
}

async fn call_container_with_deadline(
    container: &str,
    method: &str,
    params: Value,
) -> Result<Value, ContainerBridgeError> {
    let execution = inspect_container_execution(container).await?;
    let user = match (&execution.user, &execution.home) {
        (Some(user), _) => Some(user.clone()),
        (None, Some(home)) => Some(inspect_path_owner(container, home).await?),
        (None, None) => None,
    };
    let home = match (&execution.home, &user) {
        (Some(home), _) => Some(home.clone()),
        (None, Some(user)) => Some(inspect_user_home(container, user).await?),
        (None, None) => None,
    };
    let mut child = docker_bridge_command(
        container,
        user.as_deref(),
        execution.workdir.as_deref(),
        home.as_deref(),
    )?
    .stdin(Stdio::piped())
    .stdout(Stdio::piped())
    .stderr(Stdio::null())
    .spawn()
    .map_err(|error| {
        ContainerBridgeError::Failed(format!(
            "failed to start Docker bridge for {container}: {error}"
        ))
    })?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| ContainerBridgeError::Failed("Docker bridge stdin unavailable".into()))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| ContainerBridgeError::Failed("Docker bridge stdout unavailable".into()))?;
    let mut encoded = serde_json::to_vec(&BridgeRequest {
        id: 1,
        method: method.into(),
        params,
    })
    .map_err(|error| ContainerBridgeError::Failed(error.to_string()))?;
    encoded.push(b'\n');
    stdin.write_all(&encoded).await.map_err(|error| {
        ContainerBridgeError::Failed(format!("failed to write Docker bridge request: {error}"))
    })?;
    stdin.shutdown().await.map_err(|error| {
        ContainerBridgeError::Failed(format!("failed to close Docker bridge request: {error}"))
    })?;
    drop(stdin);

    let mut line = Vec::new();
    let mut stdout = BufReader::new(stdout);
    match read_provider_line(&mut stdout, &mut line, MAX_BRIDGE_FRAME_BYTES).await {
        Ok(ProviderLine::Complete) => {}
        Ok(ProviderLine::Eof) => {
            return Err(ContainerBridgeError::Failed(
                "Docker bridge closed its output".into(),
            ));
        }
        Ok(ProviderLine::Oversized) => {
            return Err(ContainerBridgeError::Failed(format!(
                "Docker bridge response exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"
            )));
        }
        Err(error) => {
            return Err(ContainerBridgeError::Failed(format!(
                "failed to read Docker bridge response: {error}"
            )));
        }
    }
    let status = child.wait().await.map_err(|error| {
        ContainerBridgeError::Failed(format!("failed to wait for Docker bridge: {error}"))
    })?;
    if !status.success() {
        return Err(ContainerBridgeError::Failed(format!(
            "Docker bridge exited with {status}"
        )));
    }
    let response: BridgeResponse = serde_json::from_slice(&line).map_err(|error| {
        ContainerBridgeError::Failed(format!("invalid Docker bridge response: {error}"))
    })?;
    if response.id != 1 {
        return Err(ContainerBridgeError::Failed(
            "Docker bridge returned a mismatched response ID".into(),
        ));
    }
    if let Some(error) = response.error {
        return Err(match error.code.as_str() {
            "not_found" => ContainerBridgeError::NotFound(error.message),
            "conflict" => ContainerBridgeError::Conflict(error.message),
            _ => ContainerBridgeError::Failed(error.message),
        });
    }
    response
        .result
        .ok_or_else(|| ContainerBridgeError::Failed("bridge omitted result".into()))
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
    let home = label("com.agentsight.home");
    for (name, path) in [
        ("com.agentsight.workspace", workdir.as_deref()),
        ("com.agentsight.home", home.as_deref()),
    ] {
        if let Some(path) = path {
            validate_container_path(name, path)?;
        }
    }
    Ok(ContainerExecution {
        user,
        workdir,
        home,
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

async fn inspect_user_home(container: &str, user: &str) -> Result<String, ContainerBridgeError> {
    let mut command = Command::new("docker");
    command
        .kill_on_drop(true)
        .args(["exec", container, "getent", "passwd", user]);
    let output = tokio::time::timeout(DOCKER_COMMAND_TIMEOUT, command.output())
        .await
        .map_err(|_| ContainerBridgeError::Failed("Docker user lookup timed out".into()))?
        .map_err(|error| {
            ContainerBridgeError::Failed(format!("Docker user lookup failed: {error}"))
        })?;
    let passwd = String::from_utf8_lossy(&output.stdout);
    let home = passwd
        .lines()
        .next()
        .and_then(|line| line.split(':').nth(5))
        .ok_or_else(|| {
            ContainerBridgeError::Failed(format!(
                "could not resolve home directory for user {user:?} in Docker container {container}"
            ))
        })?;
    validate_container_path("resolved user home", home)?;
    Ok(home.into())
}

fn docker_bridge_command(
    container: &str,
    user: Option<&str>,
    workdir: Option<&str>,
    home: Option<&str>,
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
    if let Some(home) = home {
        validate_container_path("home", home)?;
        command.args(["--env", &format!("HOME={home}")]);
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
                    "com.agentsight.home": "/home/vscode"
                }
            }
        }]);
        assert_eq!(
            parse_container_execution(&inspected).unwrap(),
            ContainerExecution {
                user: Some("vscode".into()),
                workdir: Some("/workspaces/ebpfos".into()),
                home: Some("/home/vscode".into()),
            }
        );
    }

    #[test]
    fn execution_falls_back_to_home_owner_but_rejects_relative_paths() {
        let inspected = json!([{
            "Config": {
                "User": "",
                "WorkingDir": "",
                "Labels": {"com.agentsight.home": "/home/vscode"}
            }
        }]);
        assert_eq!(
            parse_container_execution(&inspected).unwrap(),
            ContainerExecution {
                user: None,
                workdir: None,
                home: Some("/home/vscode".into()),
            }
        );
        let root_image = json!([{
            "Config": {
                "User": "root:root",
                "WorkingDir": "/",
                "Labels": {"com.agentsight.home": "/home/vscode"}
            }
        }]);
        assert_eq!(
            parse_container_execution(&root_image).unwrap().user,
            None,
            "a root image user must not override the agent home owner"
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
    fn bridge_command_propagates_agent_home() {
        let command = docker_bridge_command(
            "ebpfos-dev",
            Some("1001"),
            Some("/workspaces/ebpfos"),
            Some("/home/vscode"),
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
                "HOME=/home/vscode",
                "ebpfos-dev",
                "agentsight",
                "bridge",
            ]
        );
    }
}
