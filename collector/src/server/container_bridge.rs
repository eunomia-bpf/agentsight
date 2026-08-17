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
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::process::Stdio;
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncWrite, AsyncWriteExt, BufReader};
use tokio::process::{Child, ChildStdin, ChildStdout, Command};
use tokio::sync::Mutex;

const MAX_BRIDGE_FRAME_BYTES: usize = 8 * 1024 * 1024;
const BRIDGE_OPERATION_TIMEOUT: Duration = Duration::from_secs(30);
const BRIDGE_LOCK_TIMEOUT: Duration = Duration::from_secs(1);
const DOCKER_COMMAND_TIMEOUT: Duration = Duration::from_secs(10);

#[derive(Debug, Deserialize, Serialize)]
struct BridgeRequest {
    #[serde(flatten)]
    operation: BridgeOperation,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(tag = "method", content = "params")]
enum BridgeOperation {
    #[serde(rename = "sessions/list")]
    List { limit: usize },
    #[serde(rename = "session/get")]
    Get { session_id: String },
    #[serde(rename = "session/message")]
    Message { session_id: String, message: String },
}

#[derive(Debug, Deserialize, Serialize)]
struct BridgeError {
    code: String,
    message: String,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(untagged)]
enum BridgeResult {
    Sessions {
        sessions: Vec<AgentSession>,
    },
    Session {
        session: Box<AgentSession>,
    },
    Submitted {
        agent_type: String,
        transport: String,
    },
}

type BridgeResponse = Result<BridgeResult, BridgeError>;

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
                    Err(bridge_error(
                        "request_too_large",
                        format!("bridge request exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"),
                    )),
                )
                .await?;
                continue;
            }
            ProviderLine::Complete => {}
        }
        let response = match serde_json::from_slice::<BridgeRequest>(&line) {
            Ok(request) => dispatch_bridge_request(request, &mut cache).await,
            Err(error) => Err(bridge_error(
                "invalid_request",
                format!("invalid bridge request: {error}"),
            )),
        };
        write_bridge_response(&mut output, response).await?;
    }
    Ok(())
}

async fn write_bridge_response<W: AsyncWrite + Unpin>(
    output: &mut W,
    response: BridgeResponse,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let mut encoded = serde_json::to_vec(&response)?;
    if encoded.len().saturating_add(1) > MAX_BRIDGE_FRAME_BYTES {
        encoded = serde_json::to_vec(&BridgeResponse::Err(bridge_error(
            "response_too_large",
            format!("bridge response exceeds {MAX_BRIDGE_FRAME_BYTES} bytes"),
        )))?;
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
    match request.operation {
        BridgeOperation::List { limit } => Ok(BridgeResult::Sessions {
            sessions: agent_native_sessions::discover_sessions(
                cache,
                None,
                None,
                limit,
                Duration::ZERO,
            ),
        }),
        BridgeOperation::Get { session_id } => {
            agent_native_sessions::find_session(cache, &session_id)
                .map(|session| BridgeResult::Session {
                    session: Box::new(session),
                })
                .ok_or_else(|| bridge_error("not_found", "session not found"))
        }
        BridgeOperation::Message {
            session_id,
            message,
        } => {
            if message.trim().is_empty() || message.len() > 65_536 {
                Err(bridge_error(
                    "invalid_params",
                    "message must contain between 1 and 65536 bytes",
                ))
            } else {
                match agent_native_sessions::find_session(cache, &session_id) {
                    Some(session) => match submit_message(&session, message.trim()).await {
                        Ok(result) => Ok(BridgeResult::Submitted {
                            agent_type: session.agent_type,
                            transport: result.transport.into(),
                        }),
                        Err(SubmitError::Conflict(message)) => {
                            Err(bridge_error("conflict", message))
                        }
                        Err(SubmitError::Failed(message)) => Err(bridge_error("failed", message)),
                    },
                    None => Err(bridge_error("not_found", "session not found")),
                }
            }
        }
    }
}

fn bridge_error(code: &str, message: impl Into<String>) -> BridgeError {
    BridgeError {
        code: code.into(),
        message: message.into(),
    }
}

#[derive(Clone, Default)]
pub struct ContainerBridges {
    bridges: Arc<Vec<Arc<BridgeHandle>>>,
}

impl ContainerBridges {
    pub fn new(containers: &[String]) -> Result<Self, String> {
        let bridges = containers
            .iter()
            .map(|container| {
                validate_container_name(container)?;
                Ok(Arc::new(BridgeHandle {
                    container: container.clone(),
                    state: Mutex::new(DockerBridge::default()),
                }))
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
        let calls = self.bridges.iter().map(|bridge| async move {
            let result = match tokio::time::timeout(BRIDGE_LOCK_TIMEOUT, bridge.state.lock()).await
            {
                Ok(mut state) => state.list_sessions(&bridge.container, limit).await,
                Err(_) => Err(bridge_busy(&bridge.container)),
            };
            (&bridge.container, result)
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
        let calls = self.bridges.iter().map(|bridge| async move {
            let result = match tokio::time::timeout(BRIDGE_LOCK_TIMEOUT, bridge.state.lock()).await
            {
                Ok(mut state) => state.get_session(&bridge.container, session_id).await,
                Err(_) => Err(bridge_busy(&bridge.container)),
            };
            (&bridge.container, result)
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
        let Some(bridge) = self
            .bridges
            .iter()
            .find(|bridge| bridge.container == container)
        else {
            return Err(ContainerBridgeError::Failed(format!(
                "Docker container {container} is no longer configured"
            )));
        };
        let mut state = tokio::time::timeout(BRIDGE_LOCK_TIMEOUT, bridge.state.lock())
            .await
            .map_err(|_| bridge_busy(container))?;
        state.send_message(container, session_id, message).await
    }
}

fn bridge_busy(container: &str) -> ContainerBridgeError {
    ContainerBridgeError::Conflict(format!(
        "Docker container {container} bridge is busy; retry shortly"
    ))
}

struct BridgeHandle {
    container: String,
    state: Mutex<DockerBridge>,
}

#[derive(Default)]
struct DockerBridge {
    process: Option<BridgeProcess>,
}

#[derive(Debug, Default, Eq, PartialEq)]
struct ContainerExecution {
    user: Option<String>,
    workdir: Option<String>,
    home: Option<String>,
}

struct BridgeProcess {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

impl Drop for BridgeProcess {
    fn drop(&mut self) {
        let _ = self.child.start_kill();
    }
}

impl DockerBridge {
    async fn list_sessions(
        &mut self,
        container: &str,
        limit: usize,
    ) -> Result<Vec<AgentSession>, ContainerBridgeError> {
        match self
            .call(container, BridgeOperation::List { limit })
            .await?
        {
            BridgeResult::Sessions { sessions } => Ok(sessions),
            _ => Err(unexpected_bridge_result()),
        }
    }

    async fn get_session(
        &mut self,
        container: &str,
        session_id: &str,
    ) -> Result<Option<AgentSession>, ContainerBridgeError> {
        match self
            .call(
                container,
                BridgeOperation::Get {
                    session_id: session_id.into(),
                },
            )
            .await
        {
            Ok(BridgeResult::Session { session }) => Ok(Some(*session)),
            Ok(_) => Err(unexpected_bridge_result()),
            Err(ContainerBridgeError::NotFound(_)) => Ok(None),
            Err(error) => Err(error),
        }
    }

    async fn send_message(
        &mut self,
        container: &str,
        session_id: &str,
        message: &str,
    ) -> Result<(String, String), ContainerBridgeError> {
        match self
            .call(
                container,
                BridgeOperation::Message {
                    session_id: session_id.into(),
                    message: message.into(),
                },
            )
            .await?
        {
            BridgeResult::Submitted {
                agent_type,
                transport,
            } => Ok((agent_type, format!("docker-exec/{transport}"))),
            _ => Err(unexpected_bridge_result()),
        }
    }

    async fn call(
        &mut self,
        container: &str,
        operation: BridgeOperation,
    ) -> Result<BridgeResult, ContainerBridgeError> {
        match tokio::time::timeout(
            BRIDGE_OPERATION_TIMEOUT,
            self.call_with_deadline(container, operation),
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
        container: &str,
        operation: BridgeOperation,
    ) -> Result<BridgeResult, ContainerBridgeError> {
        self.ensure_process(container).await?;
        let mut encoded = serde_json::to_vec(&BridgeRequest { operation })
            .map_err(|error| ContainerBridgeError::Failed(error.to_string()))?;
        encoded.push(b'\n');
        let process = self.process.as_mut().expect("bridge process initialized");
        process.stdin.write_all(&encoded).await.map_err(|error| {
            ContainerBridgeError::Failed(format!("failed to write Docker bridge request: {error}"))
        })?;
        process.stdin.flush().await.map_err(|error| {
            ContainerBridgeError::Failed(format!("failed to flush Docker bridge request: {error}"))
        })?;

        let mut line = Vec::new();
        match read_provider_line(&mut process.stdout, &mut line, MAX_BRIDGE_FRAME_BYTES).await {
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
        serde_json::from_slice::<BridgeResponse>(&line)
            .map_err(|error| {
                ContainerBridgeError::Failed(format!("invalid Docker bridge response: {error}"))
            })?
            .map_err(|error| match error.code.as_str() {
                "not_found" => ContainerBridgeError::NotFound(error.message),
                "conflict" => ContainerBridgeError::Conflict(error.message),
                _ => ContainerBridgeError::Failed(error.message),
            })
    }

    async fn ensure_process(&mut self, container: &str) -> Result<(), ContainerBridgeError> {
        if let Some(process) = self.process.as_mut()
            && process.child.try_wait().ok().flatten().is_none()
        {
            return Ok(());
        }
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

fn unexpected_bridge_result() -> ContainerBridgeError {
    ContainerBridgeError::Failed("Docker bridge returned an unexpected result".into())
}

async fn inspect_container_execution(
    container: &str,
) -> Result<ContainerExecution, ContainerBridgeError> {
    validate_container_name(container).map_err(ContainerBridgeError::Failed)?;
    let operation = format!("Docker inspect for {container}");
    let output = run_docker(&["inspect", container], &operation).await?;
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
    let home = label("com.agentsight.home").or_else(|| {
        config
            .get("Env")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .find_map(|entry| entry.strip_prefix("HOME="))
            .filter(|home| home.starts_with('/'))
            .map(str::to_string)
    });
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
    let operation = format!("Docker owner lookup for {path} in {container}");
    let output = run_docker(&["exec", container, "stat", "-c", "%u", path], &operation).await?;
    let uid = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if uid.is_empty() || !uid.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ContainerBridgeError::Failed(format!(
            "invalid owner UID returned for {path} in Docker container {container}"
        )));
    }
    Ok(uid)
}

async fn inspect_user_home(container: &str, user: &str) -> Result<String, ContainerBridgeError> {
    let lookup = passwd_lookup_user(user);
    let operation = format!("Docker user lookup for {lookup:?} in {container}");
    let output = run_docker(&["exec", container, "getent", "passwd", lookup], &operation).await?;
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

fn passwd_lookup_user(user: &str) -> &str {
    user.split(':').next().unwrap_or(user)
}

async fn run_docker(
    args: &[&str],
    operation: &str,
) -> Result<std::process::Output, ContainerBridgeError> {
    let mut command = Command::new("docker");
    command.kill_on_drop(true).args(args);
    let output = tokio::time::timeout(DOCKER_COMMAND_TIMEOUT, command.output())
        .await
        .map_err(|_| {
            ContainerBridgeError::Failed(format!(
                "{operation} timed out after {} seconds",
                DOCKER_COMMAND_TIMEOUT.as_secs()
            ))
        })?
        .map_err(|error| ContainerBridgeError::Failed(format!("{operation} failed: {error}")))?;
    if output.status.success() {
        Ok(output)
    } else {
        Err(ContainerBridgeError::Failed(format!(
            "{operation} failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        )))
    }
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
    use serde_json::json;

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
            operation: BridgeOperation::Message {
                session_id: "s-1".into(),
                message: "continue".into(),
            },
        };
        let encoded = serde_json::to_string(&request).unwrap();
        let decoded: BridgeRequest = serde_json::from_str(&encoded).unwrap();
        assert!(matches!(
            decoded.operation,
            BridgeOperation::Message { message, .. } if message == "continue"
        ));
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
    fn execution_uses_absolute_environment_home_with_user_and_group() {
        let inspected = json!([{
            "Config": {
                "User": "1001:1001",
                "WorkingDir": "/workspace",
                "Env": ["PATH=/usr/bin", "HOME=/home/agent"],
                "Labels": {}
            }
        }]);

        assert_eq!(
            parse_container_execution(&inspected).unwrap(),
            ContainerExecution {
                user: Some("1001:1001".into()),
                workdir: Some("/workspace".into()),
                home: Some("/home/agent".into()),
            }
        );
        assert_eq!(passwd_lookup_user("vscode:vscode"), "vscode");
        assert_eq!(passwd_lookup_user("1001:1001"), "1001");
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

    #[cfg(target_os = "linux")]
    #[tokio::test]
    async fn dropping_a_bridge_reaps_its_child() {
        let mut child = Command::new("sh");
        child
            .kill_on_drop(true)
            .args(["-c", "read _"])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped());
        let mut child = child.spawn().unwrap();
        let pid = child.id().unwrap();
        let process = BridgeProcess {
            stdin: child.stdin.take().unwrap(),
            stdout: BufReader::new(child.stdout.take().unwrap()),
            child,
        };

        drop(process);
        for _ in 0..50 {
            if !std::path::Path::new(&format!("/proc/{pid}")).exists() {
                return;
            }
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
        panic!("bridge child {pid} survived handle drop");
    }

    #[tokio::test]
    async fn container_fanout_shares_the_one_second_lock_bound() {
        let bridges = ContainerBridges::new(&["first".into(), "second".into()]).unwrap();
        let _first = bridges.bridges[0].state.lock().await;
        let _second = bridges.bridges[1].state.lock().await;
        let started = tokio::time::Instant::now();

        assert!(bridges.list_sessions(25).await.is_empty());
        assert!(started.elapsed() < Duration::from_millis(1_800));
    }
}
