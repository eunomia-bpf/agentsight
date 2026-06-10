// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{Snapshot, SnapshotOptions};
use crate::server::assets::FrontendAssets;
use crate::sources::agent_native::{self as agent_native_sessions, SessionCache};
use crate::sources::sqlite as sqlite_source;
use crate::view::SharedMaterializedView;
use http_body_util::Full;
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

pub struct WebServer {
    assets: Arc<FrontendAssets>,
    view: SharedMaterializedView,
    agent_native_sessions: Arc<Mutex<SessionCache>>,
    db_path: Option<String>,
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
        })
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

            tokio::spawn(async move {
                let io = TokioIo::new(stream);
                let service = service_fn(move |req| {
                    handle_request(
                        req,
                        assets.clone(),
                        view.clone(),
                        agent_native_sessions.clone(),
                        db_path.clone(),
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
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let path = req.uri().path();
    let query = req.uri().query().map(str::to_string);

    log::info!("📨 {} {}", req.method(), path);

    let response = match (req.method(), path) {
        (&Method::GET, "/api/v1/snapshot") => {
            serve_snapshot_api(view, agent_native_sessions, db_path, query.as_deref()).await?
        }
        (&Method::GET, _) => serve_asset(assets, path).await?,
        _ => {
            log::info!("❌ 404 Not Found: {} {}", req.method(), path);
            plain_response(StatusCode::NOT_FOUND, "text/plain", b"Not Found".to_vec())
        }
    };

    Ok(response)
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

    let agent_native_rows = agent_native_sessions
        .lock()
        .map_err(|_| std::io::Error::other("agent-native session cache lock poisoned"))?
        .discover_cached(25, Duration::from_secs(2));
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
        .header("Access-Control-Allow-Origin", "*")
        .body(Full::new(Bytes::from(body)))
        .unwrap_or_else(|_| Response::new(Full::new(Bytes::new())))
}

fn json_response<T: Serialize>(status: StatusCode, value: &T) -> Response<Full<Bytes>> {
    let body = serde_json::to_vec(value).unwrap_or_else(|_| b"{}".to_vec());
    plain_response(status, "application/json", body)
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

    #[test]
    fn parses_api_query_parameters() {
        let query = Some("audit_limit=9&foo=bar");

        assert_eq!(query_param_usize(query, "audit_limit"), Some(9));
        assert_eq!(query_param_usize(query, "missing"), None);
    }

    fn llm_call(id: &str, pid: u32, comm: &str, timestamp_ms: u64, text: &str) -> LlmCallRow {
        LlmCallRow {
            id: id.to_string(),
            start_timestamp_ms: timestamp_ms,
            end_timestamp_ms: None,
            pid: Some(pid),
            comm: Some(comm.to_string()),
            provider: Some("anthropic".to_string()),
            model: Some("claude-opus-4-6".to_string()),
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
}
