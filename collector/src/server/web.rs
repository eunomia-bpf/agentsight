// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{Snapshot, SnapshotOptions};
use crate::output::TopOptions;
use crate::server::assets::FrontendAssets;
use crate::server::capability::{
    CapabilityMintRequest, CapabilityStore, EVIDENCE_READ, NODE_INFO, SESSION_MESSAGE, SESSION_READ,
};
use crate::server::container_bridge::{ContainerBridgeError, ContainerBridges};
use crate::sources::agent_native::{self as agent_native_sessions, SessionCache};
use crate::sources::sqlite as sqlite_source;
use crate::view::SharedMaterializedView;
use crate::view::live_top::{LiveCaptureSnapshot, LiveView};
use agentsight_protocol::{
    PRODUCT, PROTOCOL_VERSION, SessionMessageRequest, session_detail_id, session_message_id,
};
use http_body_util::{BodyExt, Full, LengthLimitError, Limited};
use hyper::header::{AUTHORIZATION, CACHE_CONTROL, HeaderValue, ORIGIN};
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Method, Request, Response, StatusCode, body::Bytes};
use hyper_util::rt::TokioIo;
use serde::Serialize;
use serde_json::Value;
use std::collections::HashSet;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::net::TcpListener;

const MAX_CAPABILITY_BODY_BYTES: usize = 16 * 1024;
// SessionMessageRequest permits 65,536 decoded bytes. JSON escaping can expand
// control bytes to six source bytes, so preserve the public contract while
// still bounding authenticated request allocation.
const MAX_SESSION_MESSAGE_BODY_BYTES: usize = 512 * 1024;

enum BodyReadError {
    TooLarge,
    Failed(String),
}

#[derive(Clone)]
struct DirectAuth {
    bootstrap_token: String,
    node: NodeMetadata,
    allowed_origin: String,
}

#[derive(Clone, Serialize)]
pub struct NodeMetadata {
    pub id: String,
    pub name: String,
    pub version: String,
}

impl DirectAuth {
    fn new(bootstrap_token: String, node: NodeMetadata, allowed_origin: String) -> Self {
        Self {
            bootstrap_token,
            node,
            allowed_origin,
        }
    }

    fn bearer<'a>(&self, value: Option<&'a HeaderValue>) -> Option<&'a str> {
        value
            .and_then(|value| value.to_str().ok())
            .and_then(|value| value.strip_prefix("Bearer "))
    }

    fn is_root(&self, value: Option<&HeaderValue>) -> bool {
        self.bearer(value) == Some(self.bootstrap_token.as_str())
    }

    fn authorizes(
        &self,
        capabilities: &Arc<Mutex<CapabilityStore>>,
        value: Option<&HeaderValue>,
        action: &str,
        session_id: Option<&str>,
    ) -> bool {
        if self.is_root(value) {
            return true;
        }
        let Some(token) = self.bearer(value) else {
            return false;
        };
        capabilities
            .lock()
            .ok()
            .is_some_and(|mut store| store.authorizes(&self.node.id, token, action, session_id))
    }

    fn allows_origin(&self, origin: &str) -> bool {
        origin == self.allowed_origin
    }
}

pub struct WebServer {
    assets: Arc<FrontendAssets>,
    view: SharedMaterializedView,
    agent_native_sessions: Arc<Mutex<SessionCache>>,
    live_view: Arc<Mutex<LiveView>>,
    capabilities: Arc<Mutex<CapabilityStore>>,
    db_path: Option<String>,
    live_host: bool,
    direct_auth: Option<DirectAuth>,
    container_bridges: Option<ContainerBridges>,
}

impl WebServer {
    pub fn new_with_db_path(
        view: SharedMaterializedView,
        db_path: Option<String>,
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let assets = FrontendAssets::new()?;
        Ok(Self {
            assets: Arc::new(assets),
            view,
            agent_native_sessions: Arc::new(Mutex::new(SessionCache::new())),
            live_view: Arc::new(Mutex::new(LiveView::default())),
            capabilities: Arc::new(Mutex::new(CapabilityStore::default())),
            db_path,
            live_host: false,
            direct_auth: None,
            container_bridges: None,
        })
    }

    /// Mark this server as attached to an in-process live capture. A live
    /// capture can also have a SQLite sink; the database path alone does not
    /// distinguish it from a saved-capture reader.
    pub fn with_live_host(mut self) -> Self {
        self.live_host = true;
        self
    }

    #[cfg(test)]
    pub(crate) fn is_live_host(&self) -> bool {
        self.live_host
    }

    pub fn with_direct_access(
        mut self,
        access_token: String,
        node: NodeMetadata,
        allowed_origin: String,
    ) -> Self {
        self.direct_auth = Some(DirectAuth::new(access_token, node, allowed_origin));
        self
    }

    pub fn with_docker_containers(
        mut self,
        containers: &[String],
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let bridges = ContainerBridges::new(containers).map_err(std::io::Error::other)?;
        if !bridges.is_empty() {
            self.container_bridges = Some(bridges);
        }
        Ok(self)
    }

    pub async fn start(
        &self,
        addr: SocketAddr,
    ) -> std::result::Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let listener = TcpListener::bind(addr)
            .await
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        log::info!("🚀 Frontend server running on http://{}", addr);

        let all_assets = self.assets.list_all_assets();
        log::info!(
            "📦 Embedded {} assets from frontend/dist:",
            all_assets.len()
        );
        for asset in all_assets.iter().take(10) {
            log::info!("   - {}", asset);
        }
        if all_assets.len() > 10 {
            log::info!("   ... and {} more", all_assets.len() - 10);
        }

        loop {
            let (stream, _) = listener
                .accept()
                .await
                .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
            let assets = Arc::clone(&self.assets);
            let view = Arc::clone(&self.view);
            let agent_native_sessions = Arc::clone(&self.agent_native_sessions);
            let live_view = Arc::clone(&self.live_view);
            let capabilities = Arc::clone(&self.capabilities);
            let db_path = self.db_path.clone();
            let live_host = self.live_host;
            let direct_auth = self.direct_auth.clone();
            let container_bridges = self.container_bridges.clone();

            tokio::spawn(async move {
                let io = TokioIo::new(stream);
                let service = service_fn(move |req| {
                    handle_request(
                        req,
                        assets.clone(),
                        view.clone(),
                        agent_native_sessions.clone(),
                        live_view.clone(),
                        capabilities.clone(),
                        db_path.clone(),
                        live_host,
                        direct_auth.clone(),
                        container_bridges.clone(),
                    )
                });

                if let Err(err) = http1::Builder::new().serve_connection(io, service).await {
                    log::error!("❌ Error serving connection: {:?}", err);
                }
            });
        }
    }
}

async fn handle_request(
    req: Request<hyper::body::Incoming>,
    assets: Arc<FrontendAssets>,
    view: SharedMaterializedView,
    agent_native_sessions: Arc<Mutex<SessionCache>>,
    live_view: Arc<Mutex<LiveView>>,
    capabilities: Arc<Mutex<CapabilityStore>>,
    db_path: Option<String>,
    live_host: bool,
    direct_auth: Option<DirectAuth>,
    container_bridges: Option<ContainerBridges>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let method = req.method().clone();
    let path = req.uri().path().to_string();
    let query = req.uri().query().map(str::to_string);
    let origin = req
        .headers()
        .get(ORIGIN)
        .and_then(|value| value.to_str().ok())
        .map(str::to_string);
    let authorization = req.headers().get(AUTHORIZATION).cloned();

    log::info!("📨 {} {}", method, path);

    if origin
        .as_deref()
        .is_some_and(|value| !allowed_origin(value, direct_auth.as_ref()))
    {
        return Ok(plain_response(
            StatusCode::FORBIDDEN,
            "text/plain",
            b"Origin not allowed".to_vec(),
        ));
    }

    if method == Method::OPTIONS && path.starts_with("/api/") {
        return Ok(cors_response(
            plain_response(StatusCode::NO_CONTENT, "text/plain", Vec::new()),
            origin.as_deref(),
            direct_auth.as_ref(),
        ));
    }

    let session_message_id = session_message_id(&path).map(str::to_string);
    let session_detail_id = session_detail_id(&path).map(str::to_string);
    let response = match (method, path.as_str()) {
        (Method::GET, "/api/v1/info") => {
            if !info_access_allowed(direct_auth.as_ref(), &capabilities, authorization.as_ref()) {
                json_error(StatusCode::UNAUTHORIZED, "valid Node capability required")
            } else {
                let node = info_node(direct_auth.as_ref(), &capabilities, authorization.as_ref());
                json_response(
                    StatusCode::OK,
                    &serde_json::json!({
                        "protocol_version": PROTOCOL_VERSION,
                        "product": PRODUCT,
                        "authorization_required": direct_auth.is_some(),
                        "capabilities": {
                            "scoped_authorization": direct_auth.is_some(),
                            "overview": live_host,
                            "session_detail": live_host,
                            "session_messages": direct_auth.is_some() && live_host,
                            "container_sessions": container_bridges.is_some(),
                        },
                        "node": node,
                    }),
                )
            }
        }
        (Method::POST, "/api/v1/capabilities") => {
            serve_capability_mint_api(
                req,
                direct_auth.as_ref(),
                &capabilities,
                authorization.as_ref(),
            )
            .await?
        }
        (Method::GET, "/api/v1/snapshot") => {
            if !protocol_access_allowed(
                direct_auth.as_ref(),
                &capabilities,
                authorization.as_ref(),
                EVIDENCE_READ,
                None,
                origin.as_deref(),
            ) {
                json_error(
                    StatusCode::UNAUTHORIZED,
                    "evidence.read capability required",
                )
            } else {
                serve_snapshot_api(
                    view,
                    agent_native_sessions,
                    container_bridges,
                    db_path,
                    query.as_deref(),
                )
                .await?
            }
        }
        (Method::GET, "/api/v1/overview") => {
            if !protocol_access_allowed(
                direct_auth.as_ref(),
                &capabilities,
                authorization.as_ref(),
                EVIDENCE_READ,
                None,
                origin.as_deref(),
            ) {
                json_error(
                    StatusCode::UNAUTHORIZED,
                    "evidence.read capability required",
                )
            } else if !live_host {
                json_error(
                    StatusCode::CONFLICT,
                    "saved captures do not expose live processes",
                )
            } else {
                serve_overview_api(view, live_view).await?
            }
        }
        (Method::GET, _) if session_detail_id.is_some() => {
            let session_id = session_detail_id.as_deref().unwrap_or_default();
            if !protocol_access_allowed(
                direct_auth.as_ref(),
                &capabilities,
                authorization.as_ref(),
                SESSION_READ,
                Some(session_id),
                origin.as_deref(),
            ) {
                json_error(StatusCode::UNAUTHORIZED, "session.read capability required")
            } else if !live_host {
                json_error(
                    StatusCode::CONFLICT,
                    "saved captures do not expose native session messages",
                )
            } else {
                serve_session_api(agent_native_sessions, container_bridges, session_id).await?
            }
        }
        (Method::POST, _) if session_message_id.is_some() => {
            let session_id = session_message_id.as_deref().unwrap_or_default();
            if !protocol_access_allowed(
                direct_auth.as_ref(),
                &capabilities,
                authorization.as_ref(),
                SESSION_MESSAGE,
                Some(session_id),
                origin.as_deref(),
            ) {
                json_error(
                    StatusCode::UNAUTHORIZED,
                    "session.message capability required",
                )
            } else if !live_host {
                json_error(StatusCode::CONFLICT, "saved captures are read-only")
            } else {
                serve_session_message_api(req, agent_native_sessions, container_bridges, session_id)
                    .await?
            }
        }
        (Method::GET, _) => serve_asset(assets, &path).await?,
        _ => {
            log::info!("❌ 404 Not Found: {} {}", req.method(), path);
            plain_response(StatusCode::NOT_FOUND, "text/plain", b"Not Found".to_vec())
        }
    };

    Ok(cors_response(
        response,
        origin.as_deref(),
        direct_auth.as_ref(),
    ))
}

async fn serve_capability_mint_api(
    req: Request<hyper::body::Incoming>,
    direct_auth: Option<&DirectAuth>,
    capabilities: &Arc<Mutex<CapabilityStore>>,
    authorization: Option<&HeaderValue>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let Some(auth) = direct_auth else {
        return Ok(json_error(
            StatusCode::NOT_FOUND,
            "capability issuer unavailable",
        ));
    };
    if !auth.is_root(authorization) {
        return Ok(json_error(
            StatusCode::UNAUTHORIZED,
            "Node bootstrap credential required",
        ));
    }
    let body = match read_limited_body(req, MAX_CAPABILITY_BODY_BYTES).await {
        Ok(body) => body,
        Err(BodyReadError::TooLarge) => {
            return Ok(json_error(
                StatusCode::PAYLOAD_TOO_LARGE,
                "request too large",
            ));
        }
        Err(BodyReadError::Failed(error)) => {
            return Ok(json_error(
                StatusCode::BAD_REQUEST,
                &format!("failed to read request body: {error}"),
            ));
        }
    };
    let request: CapabilityMintRequest = match serde_json::from_slice(&body) {
        Ok(request) => request,
        Err(error) => {
            return Ok(json_error(
                StatusCode::BAD_REQUEST,
                &format!("invalid capability request: {error}"),
            ));
        }
    };
    if let Err(error) = request.validate() {
        return Ok(json_error(StatusCode::BAD_REQUEST, error));
    }
    let minted = capabilities
        .lock()
        .map_err(|_| ())
        .and_then(|mut store| store.mint(&auth.node.id, &request).map_err(|_| ()));
    let Ok((access_token, expires_at)) = minted else {
        return Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            "could not mint capability",
        ));
    };
    Ok(json_response(
        StatusCode::CREATED,
        &serde_json::json!({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "expires_in": request.ttl_seconds,
            "actions": request.actions,
            "session_id": request.session_id,
        }),
    ))
}

async fn serve_asset(
    assets: Arc<FrontendAssets>,
    path: &str,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    if let Some(content) = assets.get(path) {
        let content_type = assets.get_content_type(path);
        log::info!("✅ Serving asset: {} ({})", path, content_type);
        Ok(plain_response(
            StatusCode::OK,
            &content_type,
            content.to_vec(),
        ))
    } else if is_frontend_route(path) {
        let content = assets
            .get("/")
            .unwrap_or_else(|| Bytes::new().to_vec().into());
        log::info!("✅ Serving frontend route: {}", path);
        Ok(plain_response(
            StatusCode::OK,
            "text/html",
            content.to_vec(),
        ))
    } else {
        log::info!("❌ Asset not found: {}", path);
        Ok(plain_response(
            StatusCode::NOT_FOUND,
            "text/plain",
            b"Asset not found".to_vec(),
        ))
    }
}

fn is_frontend_route(path: &str) -> bool {
    !path.starts_with("/api/")
        && !path
            .rsplit('/')
            .next()
            .is_some_and(|name| name.contains('.'))
}

async fn serve_snapshot_api(
    view: SharedMaterializedView,
    agent_native_sessions: Arc<Mutex<SessionCache>>,
    container_bridges: Option<ContainerBridges>,
    db_path: Option<String>,
    query: Option<&str>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let audit_limit = query_param_usize(query, "audit_limit").unwrap_or(10_000);
    let container_sessions = if db_path.is_none() {
        match container_bridges {
            Some(bridges) => bridges.list_sessions(25).await,
            None => Vec::new(),
        }
    } else {
        Vec::new()
    };

    let result = tokio::task::spawn_blocking(
        move || -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
            let snapshot = snapshot_from_sources_with_extra(
                &view,
                &agent_native_sessions,
                db_path.as_deref(),
                audit_limit,
                &container_sessions,
            )?;
            Ok(serde_json::to_value(snapshot)?)
        },
    )
    .await;

    match result {
        Ok(Ok(value)) => Ok(json_response(StatusCode::OK, &value)),
        Ok(Err(e)) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("failed to query view data: {}", e),
        )),
        Err(e) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("view query task failed: {}", e),
        )),
    }
}

async fn serve_overview_api(
    view: SharedMaterializedView,
    live_view: Arc<Mutex<LiveView>>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let result = tokio::task::spawn_blocking(
        move || -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
            let capture = view
                .lock()
                .map_err(|_| std::io::Error::other("materialized view lock poisoned"))?
                .export_snapshot(SnapshotOptions {
                    audit_limit: 10_000,
                });
            let capture = LiveCaptureSnapshot::new(capture, 0);
            let options = TopOptions {
                pid: None,
                comm: None,
                sort: "cpu".to_string(),
                view: "all".to_string(),
            };
            let overview = live_view
                .lock()
                .map_err(|_| std::io::Error::other("live view lock poisoned"))?
                .refresh(Some(&capture), 25, &options)?;
            Ok(serde_json::to_value(overview)?)
        },
    )
    .await;

    match result {
        Ok(Ok(value)) => Ok(json_response(StatusCode::OK, &value)),
        Ok(Err(error)) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("failed to collect live overview: {error}"),
        )),
        Err(error) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("live overview task failed: {error}"),
        )),
    }
}

async fn serve_session_api(
    sessions: Arc<Mutex<SessionCache>>,
    container_bridges: Option<ContainerBridges>,
    session_id: &str,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    match resolve_session(sessions, container_bridges.as_ref(), session_id).await {
        Ok(Some(resolved)) => Ok(json_response(StatusCode::OK, resolved.session())),
        Ok(None) => Ok(json_error(StatusCode::NOT_FOUND, "session not found")),
        Err(response) => Ok(response),
    }
}

async fn serve_session_message_api(
    req: Request<hyper::body::Incoming>,
    sessions: Arc<Mutex<SessionCache>>,
    container_bridges: Option<ContainerBridges>,
    session_id: &str,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let body = match read_limited_body(req, MAX_SESSION_MESSAGE_BODY_BYTES).await {
        Ok(body) => body,
        Err(BodyReadError::TooLarge) => {
            return Ok(json_error(
                StatusCode::PAYLOAD_TOO_LARGE,
                "request too large",
            ));
        }
        Err(BodyReadError::Failed(error)) => {
            return Ok(json_error(
                StatusCode::BAD_REQUEST,
                &format!("failed to read request body: {error}"),
            ));
        }
    };
    let request: SessionMessageRequest = match serde_json::from_slice(&body) {
        Ok(request) => request,
        Err(error) => {
            return Ok(json_error(
                StatusCode::BAD_REQUEST,
                &format!("invalid JSON body: {error}"),
            ));
        }
    };
    let message = match request.validate() {
        Ok(message) => message.to_string(),
        Err(error) => return Ok(json_error(StatusCode::BAD_REQUEST, error)),
    };

    let resolved = match resolve_session(sessions, container_bridges.as_ref(), session_id).await {
        Ok(Some(resolved)) => resolved,
        Ok(None) => return Ok(json_error(StatusCode::NOT_FOUND, "session not found")),
        Err(response) => return Ok(response),
    };
    match resolved {
        ResolvedSession::Local(session) => {
            match crate::server::session_runtime::submit_message(&session, &message).await {
                Ok(result) => Ok(session_message_response(
                    &session.session_id,
                    &session.agent_type,
                    result.transport,
                )),
                Err(crate::server::session_runtime::SubmitError::Conflict(error)) => {
                    Ok(json_error(StatusCode::CONFLICT, &error))
                }
                Err(crate::server::session_runtime::SubmitError::Failed(error)) => {
                    Ok(json_error(StatusCode::BAD_GATEWAY, &error))
                }
            }
        }
        ResolvedSession::Container { container, session } => match container_bridges
            .as_ref()
            .expect("container session requires configured bridges")
            .send_message(&container, session_id, &message)
            .await
        {
            Ok((agent_type, transport)) => Ok(session_message_response(
                &session.session_id,
                &agent_type,
                &transport,
            )),
            Err(error) => Ok(container_bridge_error_response(error)),
        },
    }
}

enum ResolvedSession {
    Local(agent_session::AgentSession),
    Container {
        container: String,
        session: agent_session::AgentSession,
    },
}

impl ResolvedSession {
    fn session(&self) -> &agent_session::AgentSession {
        match self {
            Self::Local(session) | Self::Container { session, .. } => session,
        }
    }
}

async fn resolve_session(
    sessions: Arc<Mutex<SessionCache>>,
    container_bridges: Option<&ContainerBridges>,
    session_id: &str,
) -> Result<Option<ResolvedSession>, Response<Full<Bytes>>> {
    let local_id = session_id.to_string();
    let local = tokio::task::spawn_blocking(move || {
        sessions
            .lock()
            .map_err(|_| std::io::Error::other("agent-native session cache lock poisoned"))
            .map(|mut cache| agent_native_sessions::find_session(&mut cache, &local_id))
    })
    .await
    .map_err(|error| {
        json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("session query task failed: {error}"),
        )
    })?
    .map_err(|error| {
        json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("failed to load session: {error}"),
        )
    })?;
    let remote = match container_bridges {
        Some(bridges) => bridges
            .get_session(session_id)
            .await
            .map_err(container_bridge_error_response)?,
        None => None,
    };
    match (local, remote) {
        (Some(_), Some((container, _))) => Err(json_error(
            StatusCode::CONFLICT,
            &format!(
                "session {session_id} exists both locally and in Docker container {container}"
            ),
        )),
        (Some(session), None) => Ok(Some(ResolvedSession::Local(session))),
        (None, Some((container, session))) => {
            Ok(Some(ResolvedSession::Container { container, session }))
        }
        (None, None) => Ok(None),
    }
}

fn session_message_response(
    session_id: &str,
    agent_type: &str,
    transport: &str,
) -> Response<Full<Bytes>> {
    json_response(
        StatusCode::ACCEPTED,
        &serde_json::json!({
            "session_id": session_id,
            "agent_type": agent_type,
            "status": "submitted",
            "transport": transport,
        }),
    )
}

fn container_bridge_error_response(error: ContainerBridgeError) -> Response<Full<Bytes>> {
    match error {
        ContainerBridgeError::NotFound(message) => json_error(StatusCode::NOT_FOUND, &message),
        ContainerBridgeError::Conflict(message) => json_error(StatusCode::CONFLICT, &message),
        ContainerBridgeError::Failed(message) => json_error(StatusCode::BAD_GATEWAY, &message),
    }
}

async fn read_limited_body(
    req: Request<hyper::body::Incoming>,
    max_bytes: usize,
) -> Result<Bytes, BodyReadError> {
    collect_limited_body(req.into_body(), max_bytes).await
}

async fn collect_limited_body<B>(body: B, max_bytes: usize) -> Result<Bytes, BodyReadError>
where
    B: hyper::body::Body<Data = Bytes>,
    B::Error: Into<Box<dyn std::error::Error + Send + Sync>>,
{
    match Limited::new(body, max_bytes).collect().await {
        Ok(body) => Ok(body.to_bytes()),
        Err(error) if error.downcast_ref::<LengthLimitError>().is_some() => {
            Err(BodyReadError::TooLarge)
        }
        Err(error) => Err(BodyReadError::Failed(error.to_string())),
    }
}

#[cfg(test)]
fn snapshot_from_sources(
    view: &SharedMaterializedView,
    agent_native_sessions: &Arc<Mutex<SessionCache>>,
    db_path: Option<&str>,
    audit_limit: usize,
) -> Result<Snapshot, Box<dyn std::error::Error + Send + Sync>> {
    snapshot_from_sources_with_extra(view, agent_native_sessions, db_path, audit_limit, &[])
}

fn snapshot_from_sources_with_extra(
    view: &SharedMaterializedView,
    agent_native_sessions: &Arc<Mutex<SessionCache>>,
    db_path: Option<&str>,
    audit_limit: usize,
    extra_sessions: &[agent_session::AgentSession],
) -> Result<Snapshot, Box<dyn std::error::Error + Send + Sync>> {
    if let Some(db_path) = db_path {
        let view = sqlite_source::load_view_with_observed_session_prompts(db_path)?;
        return Ok(view.export_snapshot(SnapshotOptions { audit_limit }));
    }

    let mut agent_native_rows = {
        let mut session_cache = agent_native_sessions
            .lock()
            .map_err(|_| std::io::Error::other("agent-native session cache lock poisoned"))?;
        agent_native_sessions::discover_sessions(
            &mut session_cache,
            None,
            None,
            25,
            Duration::from_secs(2),
        )
    };
    let mut session_ids = agent_native_rows
        .iter()
        .map(|session| session.session_id.clone())
        .collect::<HashSet<_>>();
    agent_native_rows.extend(
        extra_sessions
            .iter()
            .filter(|session| session_ids.insert(session.session_id.clone()))
            .cloned(),
    );
    let mut merged = view
        .lock()
        .map_err(|_| std::io::Error::other("live view lock poisoned"))?
        .detached_copy();
    agent_native_sessions::import_into_view(&mut merged, &agent_native_rows);
    Ok(merged.export_snapshot(SnapshotOptions { audit_limit }))
}

fn plain_response(status: StatusCode, content_type: &str, body: Vec<u8>) -> Response<Full<Bytes>> {
    Response::builder()
        .status(status)
        .header("Content-Type", content_type)
        .header("X-Content-Type-Options", "nosniff")
        .body(Full::new(Bytes::from(body)))
        .unwrap_or_else(|_| Response::new(Full::new(Bytes::new())))
}

fn allowed_origin(origin: &str, direct_auth: Option<&DirectAuth>) -> bool {
    direct_auth.is_some_and(|auth| auth.allows_origin(origin))
        || option_env!("AGENTSIGHT_DEV_APP_ORIGIN").is_some_and(|allowed| origin == allowed)
}

fn protocol_access_allowed(
    direct_auth: Option<&DirectAuth>,
    capabilities: &Arc<Mutex<CapabilityStore>>,
    authorization: Option<&HeaderValue>,
    action: &str,
    session_id: Option<&str>,
    origin: Option<&str>,
) -> bool {
    match direct_auth {
        Some(auth) => auth.authorizes(capabilities, authorization, action, session_id),
        None => origin.is_none(),
    }
}

fn info_access_allowed(
    direct_auth: Option<&DirectAuth>,
    capabilities: &Arc<Mutex<CapabilityStore>>,
    authorization: Option<&HeaderValue>,
) -> bool {
    match (direct_auth, authorization) {
        (Some(auth), Some(value)) => auth.authorizes(capabilities, Some(value), NODE_INFO, None),
        _ => true,
    }
}

fn info_node(
    direct_auth: Option<&DirectAuth>,
    capabilities: &Arc<Mutex<CapabilityStore>>,
    authorization: Option<&HeaderValue>,
) -> Option<NodeMetadata> {
    direct_auth.and_then(|auth| {
        auth.authorizes(capabilities, authorization, NODE_INFO, None)
            .then(|| auth.node.clone())
    })
}

fn cors_response(
    mut response: Response<Full<Bytes>>,
    origin: Option<&str>,
    direct_auth: Option<&DirectAuth>,
) -> Response<Full<Bytes>> {
    let Some(origin) = origin.filter(|origin| allowed_origin(origin, direct_auth)) else {
        return response;
    };
    if let Ok(value) = HeaderValue::from_str(origin) {
        response
            .headers_mut()
            .insert("Access-Control-Allow-Origin", value);
    }
    response.headers_mut().insert(
        "Access-Control-Allow-Methods",
        HeaderValue::from_static("GET, POST, OPTIONS"),
    );
    response.headers_mut().insert(
        "Access-Control-Allow-Headers",
        HeaderValue::from_static("Authorization, Content-Type"),
    );
    response.headers_mut().insert(
        "Access-Control-Allow-Private-Network",
        HeaderValue::from_static("true"),
    );
    response
        .headers_mut()
        .insert("Vary", HeaderValue::from_static("Origin"));
    response
}

fn json_response<T: Serialize>(status: StatusCode, value: &T) -> Response<Full<Bytes>> {
    let body = serde_json::to_vec(value).unwrap_or_else(|_| b"{}".to_vec());
    let mut response = plain_response(status, "application/json", body);
    response
        .headers_mut()
        .insert(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    response
}

fn json_error(status: StatusCode, message: &str) -> Response<Full<Bytes>> {
    json_response(status, &serde_json::json!({ "error": message }))
}

fn query_param(query: Option<&str>, name: &str) -> Option<String> {
    query?
        .split('&')
        .filter_map(|pair| pair.split_once('='))
        .find_map(|(key, value)| (key == name).then(|| value.to_string()))
}

fn query_param_usize(query: Option<&str>, name: &str) -> Option<usize> {
    query_param(query, name).and_then(|value| value.parse::<usize>().ok())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::{LlmCallRow, ProcessNodeRow, ViewSink};
    use crate::sinks::sqlite::SqliteStore;
    use crate::view::MaterializedView;

    static ENV_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

    #[test]
    fn parses_api_query_parameters() {
        let query = Some("audit_limit=9&foo=bar");

        assert_eq!(query_param_usize(query, "audit_limit"), Some(9));
        assert_eq!(query_param_usize(query, "missing"), None);
    }

    #[test]
    fn parses_session_routes() {
        assert_eq!(
            session_detail_id("/api/v1/sessions/session-1"),
            Some("session-1")
        );
        assert_eq!(
            session_message_id("/api/v1/sessions/session-1/messages"),
            Some("session-1")
        );
        assert_eq!(
            session_detail_id("/api/v1/sessions/session-1/messages"),
            None
        );
    }

    #[tokio::test]
    async fn authenticated_request_bodies_are_bounded_while_reading() {
        let accepted = collect_limited_body(Full::new(Bytes::from_static(b"1234")), 4)
            .await
            .unwrap_or_else(|_| panic!("body at the limit should be accepted"));
        assert_eq!(accepted, Bytes::from_static(b"1234"));

        let rejected = collect_limited_body(Full::new(Bytes::from_static(b"12345")), 4).await;
        assert!(matches!(rejected, Err(BodyReadError::TooLarge)));
    }

    fn test_auth() -> DirectAuth {
        DirectAuth::new(
            "process-lifetime-key".to_string(),
            NodeMetadata {
                id: "node_test".to_string(),
                name: "test".to_string(),
                version: "1".to_string(),
            },
            "https://console.example".to_string(),
        )
    }

    #[test]
    fn bootstrap_key_is_root_and_scoped_capability_is_narrow() {
        let auth = test_auth();
        let root = HeaderValue::from_static("Bearer process-lifetime-key");
        let store = Arc::new(Mutex::new(CapabilityStore::default()));
        assert!(auth.is_root(Some(&root)));
        assert!(!auth.is_root(Some(&HeaderValue::from_static("Bearer wrong"))));
        assert!(auth.authorizes(&store, Some(&root), SESSION_MESSAGE, Some("session-1")));

        let request = CapabilityMintRequest {
            actions: vec![SESSION_READ.to_string()],
            session_id: Some("session-1".to_string()),
            ttl_seconds: 60,
        };
        let (token, _) = store.lock().unwrap().mint("node_test", &request).unwrap();
        let scoped = HeaderValue::from_str(&format!("Bearer {token}")).unwrap();
        assert!(auth.authorizes(&store, Some(&scoped), SESSION_READ, Some("session-1")));
        assert!(!auth.authorizes(&store, Some(&scoped), SESSION_MESSAGE, Some("session-1")));
        assert!(!auth.authorizes(&store, Some(&scoped), SESSION_READ, Some("session-2")));
        assert!(info_access_allowed(Some(&auth), &store, None));
        assert!(info_access_allowed(Some(&auth), &store, Some(&root)));
        assert!(info_node(Some(&auth), &store, None).is_none());
        assert_eq!(
            info_node(Some(&auth), &store, Some(&root)).unwrap().id,
            "node_test"
        );
    }

    #[test]
    fn cors_uses_the_configured_app_origin() {
        let auth = test_auth();
        assert!(allowed_origin("https://console.example", Some(&auth)));
        assert!(!allowed_origin("https://app.agentsight.us", Some(&auth)));
        assert!(!allowed_origin("https://evil.example", Some(&auth)));
    }

    #[test]
    fn hosted_origin_cannot_reuse_token_against_an_unpaired_server() {
        let store = Arc::new(Mutex::new(CapabilityStore::default()));
        assert!(protocol_access_allowed(
            None,
            &store,
            None,
            EVIDENCE_READ,
            None,
            None
        ));
        assert!(!protocol_access_allowed(
            None,
            &store,
            None,
            EVIDENCE_READ,
            None,
            Some("https://console.example")
        ));
    }

    #[test]
    fn semantic_protocol_mapping_matches_web_routes() {
        assert_eq!(
            crate::server::capability::action_for_request("GET", "/api/v1/snapshot?audit_limit=42"),
            Some((EVIDENCE_READ, None))
        );
        assert_eq!(
            crate::server::capability::action_for_request("GET", "/api/v1/overview"),
            Some((EVIDENCE_READ, None))
        );
        assert_eq!(
            crate::server::capability::action_for_request("POST", "/api/v1/sessions/s-1/messages"),
            Some((SESSION_MESSAGE, Some("s-1".to_string())))
        );
    }

    fn llm_call(id: &str, pid: u32, comm: &str, timestamp_ms: u64, text: &str) -> LlmCallRow {
        LlmCallRow {
            id: id.to_string(),
            session_id: None,
            conversation_id: None,
            start_timestamp_ms: timestamp_ms,
            end_timestamp_ms: None,
            pid: Some(pid),
            comm: Some(comm.to_string()),
            provider: Some("anthropic".to_string()),
            model: Some("claude-opus-4-6".to_string()),
            call_kind: Some("messages".to_string()),
            status: "pending".to_string(),
            error_type: None,
            finish_reason: None,
            host: Some("api.anthropic.com".to_string()),
            path: Some("/v1/messages".to_string()),
            status_code: None,
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            request: serde_json::json!({
                "model": "claude-opus-4-6",
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": text}]}
                ]
            }),
            response: serde_json::json!({}),
        }
    }

    #[test]
    fn snapshot_uses_sqlite_when_db_path_is_configured() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("session.db");
        let mut store = SqliteStore::open(&db).unwrap();
        store
            .process_node(&ProcessNodeRow {
                id: "db-process".to_string(),
                pid: 42,
                ppid: None,
                root_pid: None,
                start_timestamp_ms: Some(1_000),
                end_timestamp_ms: None,
                comm: Some("claude".to_string()),
                command: Some("claude".to_string()),
                argv: Vec::new(),
                cwd: None,
                exit_code: None,
                status: Some("observed".to_string()),
                view_source: "view".to_string(),
                confidence: Some(1.0),
            })
            .unwrap();
        store
            .llm_call(&llm_call("db-llm", 42, "claude", 1_100, "db prompt"))
            .unwrap();
        store
            .llm_call(&llm_call(
                "ssl-only-llm",
                84,
                "HTTP Client",
                1_200,
                "ssl prompt",
            ))
            .unwrap();

        let live_view = MaterializedView::shared_bounded();
        {
            let mut view = live_view.lock().unwrap();
            view.upsert_process_node(&ProcessNodeRow {
                id: "live-process".to_string(),
                pid: 7,
                ppid: None,
                root_pid: None,
                start_timestamp_ms: Some(2_000),
                end_timestamp_ms: None,
                comm: Some("live".to_string()),
                command: Some("live".to_string()),
                argv: Vec::new(),
                cwd: None,
                exit_code: None,
                status: Some("observed".to_string()),
                view_source: "view".to_string(),
                confidence: Some(1.0),
            });
        }
        let sessions = Arc::new(Mutex::new(SessionCache::new()));

        let snapshot =
            snapshot_from_sources(&live_view, &sessions, Some(db.to_str().unwrap()), 100).unwrap();

        assert_eq!(snapshot.summary.source, "sqlite");
        assert_eq!(snapshot.process_nodes.len(), 2);
        assert_eq!(snapshot.process_nodes[0].id, "db-process");
        assert_eq!(snapshot.process_nodes[1].id, "process-84-observed");
        let prompt = snapshot
            .audit_events
            .iter()
            .find(|row| row.id == "audit-db-llm-request")
            .expect("projected llm prompt audit");
        assert_eq!(prompt.audit_type, "llm");
        assert_eq!(prompt.action.as_deref(), Some("request"));
        assert_eq!(
            prompt
                .details
                .get("text_content")
                .and_then(|value| value.as_str()),
            Some("db prompt")
        );
        assert_eq!(
            prompt
                .details
                .pointer("/request/messages/0/content/0/text")
                .and_then(|value| value.as_str()),
            Some("db prompt")
        );
    }

    #[test]
    fn snapshot_deduplicates_local_and_container_session_ids() {
        let _guard = ENV_LOCK.lock().unwrap();
        let old_home = std::env::var_os("HOME");
        let old_sudo_user = std::env::var_os("SUDO_USER");
        let temp = tempfile::tempdir().unwrap();
        unsafe {
            std::env::set_var("HOME", temp.path());
            std::env::remove_var("SUDO_USER");
        }

        let result = std::panic::catch_unwind(|| {
            agent_native_sessions::write_codex_state_db_for_test(temp.path());

            let live_view = MaterializedView::shared_bounded();
            let sessions = Arc::new(Mutex::new(SessionCache::new()));
            let container_session = agent_native_sessions::parse_content_for_test(
                agent_session::AGENT_CODEX,
                &temp.path().join("container-session.jsonl"),
                std::time::UNIX_EPOCH,
                concat!(
                    r#"{"type":"session_meta","payload":{"id":"019f49ca-54e7-7a91-82e7-a52b53cfd456","cwd":"/container"}}"#,
                    "\n",
                    r#"{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"duplicate container session"}]}}"#,
                    "\n",
                ),
            )
            .unwrap();
            let snapshot = snapshot_from_sources_with_extra(
                &live_view,
                &sessions,
                None,
                100,
                &[container_session],
            )
            .unwrap();

            assert_eq!(snapshot.summary.total_tokens, 33);
            assert_eq!(snapshot.sessions.len(), 1);
            let session = &snapshot.sessions[0];
            assert_eq!(session.agent_type, "codex");
            assert_eq!(session.model.as_deref(), Some("gpt-web-ci"));
            let capture_only = live_view
                .lock()
                .unwrap()
                .export_snapshot(SnapshotOptions { audit_limit: 100 });
            assert_eq!(capture_only.summary.total_tokens, 0);
            assert!(capture_only.sessions.is_empty());
        });

        unsafe {
            match old_home {
                Some(value) => std::env::set_var("HOME", value),
                None => std::env::remove_var("HOME"),
            }
            match old_sudo_user {
                Some(value) => std::env::set_var("SUDO_USER", value),
                None => std::env::remove_var("SUDO_USER"),
            }
        }
        assert!(result.is_ok());
    }
}
