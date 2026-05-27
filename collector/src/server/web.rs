// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::framework::storage::{SnapshotOptions, SqliteStore};
use crate::server::assets::FrontendAssets;
use http_body_util::Full;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::{Method, Request, Response, StatusCode, body::Bytes};
use hyper_util::rt::TokioIo;
use serde::Serialize;
use serde_json::Value;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::net::TcpListener;

pub struct WebServer {
    assets: Arc<FrontendAssets>,
    log_file: String,
    db_path: Option<String>,
}

impl WebServer {
    pub fn new(
        log_file: &str,
        db_path: Option<&str>,
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let assets = FrontendAssets::new()?;
        Ok(Self {
            assets: Arc::new(assets),
            log_file: log_file.to_string(),
            db_path: db_path
                .map(str::to_string)
                .or_else(|| std::env::var("AGENTSIGHT_DB_PATH").ok()),
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
            let log_file = self.log_file.clone();
            let db_path = self.db_path.clone();

            tokio::spawn(async move {
                let io = TokioIo::new(stream);
                let service = service_fn(move |req| {
                    handle_request(req, assets.clone(), log_file.clone(), db_path.clone())
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
    log_file: String,
    db_path: Option<String>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let path = req.uri().path();
    let query = req.uri().query().map(str::to_string);

    log::info!("📨 {} {}", req.method(), path);

    match (req.method(), path) {
        // API endpoints first
        (&Method::GET, "/api/events") => serve_events_api(&log_file).await,
        (&Method::GET, "/api/assets") => serve_assets_list(assets).await,
        (&Method::GET, "/api/v1/snapshot") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Snapshot).await
        }
        (&Method::GET, "/api/v1/summary") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Summary).await
        }
        (&Method::GET, "/api/v1/token-summary") | (&Method::GET, "/api/v1/token/summary") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::TokenSummary).await
        }
        (&Method::GET, "/api/v1/events") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Events).await
        }
        (&Method::GET, "/api/v1/audit-events") | (&Method::GET, "/api/v1/audit/events") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::AuditEvents).await
        }
        (&Method::GET, "/api/v1/sessions") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Sessions).await
        }
        (&Method::GET, "/api/v1/agents") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Agents).await
        }
        (&Method::GET, "/api/v1/interruptions") => {
            serve_sqlite_api(db_path, query.as_deref(), ApiResource::Interruptions).await
        }

        // Serve static assets (catch-all for GET requests)
        (&Method::GET, _) => serve_asset(assets, path).await,

        // 404 for non-GET methods
        _ => {
            log::info!("❌ 404 Not Found: {} {}", req.method(), path);
            Ok(Response::builder()
                .status(StatusCode::NOT_FOUND)
                .header("Content-Type", "text/plain")
                .body(Full::new(Bytes::from("Not Found")))
                .unwrap())
        }
    }
}

async fn serve_asset(
    assets: Arc<FrontendAssets>,
    path: &str,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    if let Some(content) = assets.get(path) {
        let content_type = assets.get_content_type(path);
        log::info!("✅ Serving asset: {} ({})", path, content_type);
        Ok(Response::builder()
            .header("Content-Type", content_type)
            .header("Cache-Control", "public, max-age=31536000")
            .body(Full::new(Bytes::from(content.to_vec())))
            .unwrap())
    } else {
        log::info!("❌ Asset not found: {}", path);
        Ok(Response::builder()
            .status(StatusCode::NOT_FOUND)
            .header("Content-Type", "text/plain")
            .body(Full::new(Bytes::from("Asset not found")))
            .unwrap())
    }
}

async fn serve_events_api(
    log_path: &str,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    match tokio::fs::read_to_string(log_path).await {
        Ok(content) => {
            log::info!(
                "📊 Serving log file: {} ({} bytes)",
                log_path,
                content.len()
            );
            Ok(Response::builder()
                .header("Content-Type", "text/plain")
                .header("Access-Control-Allow-Origin", "*")
                .body(Full::new(Bytes::from(content)))
                .unwrap())
        }
        Err(e) => {
            log::error!("❌ Failed to read log file {}: {}", log_path, e);
            Ok(Response::builder()
                .status(StatusCode::INTERNAL_SERVER_ERROR)
                .header("Content-Type", "text/plain")
                .header("Access-Control-Allow-Origin", "*")
                .body(Full::new(Bytes::from(format!(
                    "Failed to read log file: {}",
                    e
                ))))
                .unwrap())
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum ApiResource {
    Snapshot,
    Summary,
    TokenSummary,
    Events,
    AuditEvents,
    Sessions,
    Agents,
    Interruptions,
}

async fn serve_sqlite_api(
    db_path: Option<String>,
    query: Option<&str>,
    resource: ApiResource,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let Some(db_path) = db_path else {
        return Ok(json_error(
            StatusCode::NOT_FOUND,
            "sqlite database is not configured; pass --db or set AGENTSIGHT_DB_PATH",
        ));
    };
    let event_limit = query_param_usize(query, "event_limit").unwrap_or(10_000);
    let audit_limit = query_param_usize(query, "audit_limit").unwrap_or(10_000);
    let group_by = query_param(query, "group_by").unwrap_or_else(|| "model".to_string());

    let result = tokio::task::spawn_blocking(
        move || -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
            let store = SqliteStore::open(&db_path)?;
            let options = SnapshotOptions {
                event_limit,
                audit_limit,
            };
            let value = match resource {
                ApiResource::TokenSummary => serde_json::to_value(store.token_summary(&group_by)?)?,
                ApiResource::Snapshot => serde_json::to_value(store.export_snapshot(options)?)?,
                ApiResource::Summary => {
                    serde_json::to_value(store.export_snapshot(options)?.summary)?
                }
                ApiResource::Events => {
                    serde_json::to_value(store.export_snapshot(options)?.events)?
                }
                ApiResource::AuditEvents => {
                    serde_json::to_value(store.export_snapshot(options)?.audit_events)?
                }
                ApiResource::Sessions => {
                    serde_json::to_value(store.export_snapshot(options)?.sessions)?
                }
                ApiResource::Agents => {
                    serde_json::to_value(store.export_snapshot(options)?.agents)?
                }
                ApiResource::Interruptions => {
                    serde_json::to_value(store.export_snapshot(options)?.interruptions)?
                }
            };
            Ok(value)
        },
    )
    .await;

    match result {
        Ok(Ok(value)) => Ok(json_response(StatusCode::OK, &value)),
        Ok(Err(e)) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("failed to query SQLite database: {}", e),
        )),
        Err(e) => Ok(json_error(
            StatusCode::INTERNAL_SERVER_ERROR,
            &format!("SQLite query task failed: {}", e),
        )),
    }
}

async fn serve_assets_list(
    assets: Arc<FrontendAssets>,
) -> std::result::Result<Response<Full<Bytes>>, Infallible> {
    let all_assets = assets.list_all_assets();
    let response = serde_json::json!({
        "assets": all_assets,
        "total_count": all_assets.len()
    });

    log::info!("📋 Serving assets list ({} assets)", all_assets.len());
    Ok(Response::builder()
        .header("Content-Type", "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(Full::new(Bytes::from(response.to_string())))
        .unwrap())
}

fn json_response<T: Serialize>(status: StatusCode, value: &T) -> Response<Full<Bytes>> {
    let body = serde_json::to_vec(value).unwrap_or_else(|_| b"{}".to_vec());
    Response::builder()
        .status(status)
        .header("Content-Type", "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(Full::new(Bytes::from(body)))
        .unwrap()
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

    #[test]
    fn parses_api_query_parameters() {
        let query = Some("event_limit=25&audit_limit=9&group_by=provider");

        assert_eq!(query_param_usize(query, "event_limit"), Some(25));
        assert_eq!(query_param_usize(query, "audit_limit"), Some(9));
        assert_eq!(query_param(query, "group_by").as_deref(), Some("provider"));
        assert_eq!(query_param(query, "missing"), None);
    }
}
