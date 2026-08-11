// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{Snapshot, SnapshotOptions};
use crate::server::assets::FrontendAssets;
use crate::sources::agent_native::{self as agent_native_sessions, SessionCache};
use crate::sources::sqlite as sqlite_source;
use crate::view::SharedMaterializedView;
use http_body_util::Full;
use hyper::header::{AUTHORIZATION, CACHE_CONTROL, HeaderValue, ORIGIN};
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Method, Request, Response, StatusCode, body::Bytes};
use hyper_util::rt::TokioIo;
use serde::Serialize;
use serde_json::Value;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::net::TcpListener;

#[derive(Clone)]
struct DirectAuth {
    access_token: String,
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
    fn new(access_token: String, node: NodeMetadata, allowed_origin: String) -> Self {
        Self {
            access_token,
            node,
            allowed_origin,
        }
    }

    fn authorizes(&self, value: Option<&HeaderValue>) -> bool {
        let Some(token) = value
            .and_then(|value| value.to_str().ok())
            .and_then(|value| value.strip_prefix("Bearer "))
        else {
            return false;
        };
        token == self.access_token
    }

    fn allows_origin(&self, origin: &str) -> bool {
        origin == self.allowed_origin
    }
}

pub struct WebServer {
    assets: Arc<FrontendAssets>,
    view: SharedMaterializedView,
    agent_native_sessions: Arc<Mutex<SessionCache>>,
    db_path: Option<String>,
    direct_auth: Option<DirectAuth>,
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
            db_path,
            direct_auth: None,
        })
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

    pub async fn start(
        &self,
        addr: SocketAddr,
    ) -> std::result::Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let listener = TcpListener::bind(addr)
            .await
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        log::info!("🚀 Frontend server running on http://{}", addr);

        // List embedded assets for debugging
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
            let db_path = self.db_path.clone();
            let direct_auth = self.direct_auth.clone();

            tokio::spawn(async move {
                let io = TokioIo::new(stream);
                let service = service_fn(move |req| {
                    handle_request(
                        req,
                        assets.clone(),
                        view.clone(),
                        agent_native_sessions.clone(),
                        db_path.clone(),
                        direct_auth.clone(),
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
    db_path: Option<String>,
    direct_auth: Option<DirectAuth>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let path = req.uri().path().to_string();
    let query = req.uri().query().map(str::to_string);
    let origin = req
        .headers()
        .get(ORIGIN)
        .and_then(|value| value.to_str().ok())
        .map(str::to_string);

    log::info!("📨 {} {}", req.method(), path);

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

    if req.method() == Method::OPTIONS && path.starts_with("/api/") {
        return Ok(cors_response(
            plain_response(StatusCode::NO_CONTENT, "text/plain", Vec::new()),
            origin.as_deref(),
            direct_auth.as_ref(),
        ));
    }

    let response = match (req.method(), path.as_str()) {
        (&Method::GET, "/api/v1/info") => {
            if !info_access_allowed(direct_auth.as_ref(), req.headers().get(AUTHORIZATION)) {
                json_error(StatusCode::UNAUTHORIZED, "valid binding token required")
            } else {
                json_response(
                    StatusCode::OK,
                    &serde_json::json!({
                        "protocol_version": 1,
                        "product": "agentsight",
                        "authorization_required": direct_auth.is_some(),
                        "node": direct_auth.as_ref().map(|auth| auth.node.clone()),
                    }),
                )
            }
        }
        (&Method::GET, "/api/v1/snapshot") => {
            if !snapshot_access_allowed(
                direct_auth.as_ref(),
                req.headers().get(AUTHORIZATION),
                origin.as_deref(),
            ) {
                json_error(StatusCode::UNAUTHORIZED, "valid binding token required")
            } else {
                serve_snapshot_api(view, agent_native_sessions, db_path, query.as_deref()).await?
            }
        }
        (&Method::GET, _) => serve_asset(assets, &path).await?,
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
    db_path: Option<String>,
    query: Option<&str>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let audit_limit = query_param_usize(query, "audit_limit").unwrap_or(10_000);

    let result = tokio::task::spawn_blocking(
        move || -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
            let snapshot = snapshot_from_sources(
                &view,
                &agent_native_sessions,
                db_path.as_deref(),
                audit_limit,
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

fn snapshot_from_sources(
    view: &SharedMaterializedView,
    agent_native_sessions: &Arc<Mutex<SessionCache>>,
    db_path: Option<&str>,
    audit_limit: usize,
) -> Result<Snapshot, Box<dyn std::error::Error + Send + Sync>> {
    if let Some(db_path) = db_path {
        let view = sqlite_source::load_view_with_observed_session_prompts(db_path)?;
        return Ok(view.export_snapshot(SnapshotOptions { audit_limit }));
    }

    let agent_native_rows = {
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
    let mut view = view
        .lock()
        .map_err(|_| std::io::Error::other("live view lock poisoned"))?;
    agent_native_sessions::import_into_view(&mut view, &agent_native_rows);
    Ok(view.export_snapshot(SnapshotOptions { audit_limit }))
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

fn snapshot_access_allowed(
    direct_auth: Option<&DirectAuth>,
    authorization: Option<&HeaderValue>,
    origin: Option<&str>,
) -> bool {
    match direct_auth {
        Some(auth) => auth.authorizes(authorization),
        None => origin.is_none(),
    }
}

fn info_access_allowed(
    direct_auth: Option<&DirectAuth>,
    authorization: Option<&HeaderValue>,
) -> bool {
    match (direct_auth, authorization) {
        (Some(auth), Some(value)) => auth.authorizes(Some(value)),
        _ => true,
    }
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
        HeaderValue::from_static("GET, OPTIONS"),
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
    fn direct_access_key_authorizes() {
        let auth = DirectAuth::new(
            "process-lifetime-key".to_string(),
            NodeMetadata {
                id: "node_test".to_string(),
                name: "test".to_string(),
                version: "1".to_string(),
            },
            "https://console.example".to_string(),
        );
        let header = HeaderValue::from_static("Bearer process-lifetime-key");
        assert!(auth.authorizes(Some(&header)));
        assert!(!auth.authorizes(Some(&HeaderValue::from_static("Bearer wrong"))));
        assert!(!auth.authorizes(None));
        assert!(info_access_allowed(Some(&auth), None));
        assert!(info_access_allowed(Some(&auth), Some(&header)));
        assert!(!info_access_allowed(
            Some(&auth),
            Some(&HeaderValue::from_static("Bearer wrong"))
        ));
    }

    #[test]
    fn cors_uses_the_configured_app_origin() {
        let auth = DirectAuth::new(
            "key".to_string(),
            NodeMetadata {
                id: "node_test".to_string(),
                name: "test".to_string(),
                version: "1".to_string(),
            },
            "https://console.example".to_string(),
        );
        assert!(allowed_origin("https://console.example", Some(&auth)));
        assert!(!allowed_origin("https://app.agentsight.us", Some(&auth)));
        assert!(!allowed_origin("https://evil.example", Some(&auth)));
    }

    #[test]
    fn hosted_origin_cannot_reuse_token_against_an_unpaired_server() {
        assert!(snapshot_access_allowed(None, None, None));
        assert!(!snapshot_access_allowed(
            None,
            None,
            Some("https://console.example")
        ));
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
    fn snapshot_uses_agent_native_indexed_codex_sessions() {
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
            let snapshot = snapshot_from_sources(&live_view, &sessions, None, 100).unwrap();

            assert_eq!(snapshot.summary.total_tokens, 33);
            assert_eq!(snapshot.sessions.len(), 1);
            let session = &snapshot.sessions[0];
            assert_eq!(session.agent_type, "codex");
            assert_eq!(session.model.as_deref(), Some("gpt-web-ci"));
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
