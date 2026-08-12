// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use futures::{SinkExt, StreamExt};
use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper::{Method, Request};
use hyper_util::client::legacy::Client;
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_util::rt::TokioExecutor;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::time::Duration;
use tokio::time::MissedTickBehavior;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::tungstenite::client::IntoClientRequest;
use tokio_tungstenite::tungstenite::http::HeaderValue;
use url::Url;

const MAX_RELAY_RESPONSE_BYTES: usize = 16 * 1024 * 1024;
const RECONNECT_DELAY_SECS: u64 = 2;
const HEARTBEAT_INTERVAL_SECS: u64 = 20;

fn install_tls_provider() -> Result<(), Box<dyn Error + Send + Sync>> {
    if rustls::crypto::CryptoProvider::get_default().is_some() {
        return Ok(());
    }
    rustls::crypto::ring::default_provider()
        .install_default()
        .map_err(|_| "could not install the AgentSight relay TLS provider".into())
}

#[derive(Debug, Deserialize)]
struct RelayRequestEnvelope {
    r#type: String,
    id: String,
    method: String,
    path: String,
    body: Option<String>,
}

#[derive(Serialize)]
struct RelayResponseEnvelope {
    r#type: &'static str,
    id: String,
    status: u16,
    body: String,
}

pub(crate) async fn run(
    controller_url: String,
    node_id: String,
    access_token: String,
    local_endpoint: String,
) {
    if let Err(error) = install_tls_provider() {
        log::warn!("AgentSight Controller relay disabled: {error}");
        return;
    }
    let relay_url = match relay_url(&controller_url, &node_id) {
        Ok(url) => url,
        Err(error) => {
            log::warn!("AgentSight Controller relay disabled: {error}");
            return;
        }
    };

    loop {
        if let Err(error) = connect_once(&relay_url, &access_token, &local_endpoint).await {
            log::debug!("AgentSight Controller relay disconnected: {error}");
        }
        tokio::time::sleep(Duration::from_secs(RECONNECT_DELAY_SECS)).await;
    }
}

async fn connect_once(
    relay_url: &str,
    access_token: &str,
    local_endpoint: &str,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let mut request = relay_url.into_client_request()?;
    request.headers_mut().insert(
        "Authorization",
        HeaderValue::from_str(&format!("Bearer {access_token}"))?,
    );
    request.headers_mut().insert(
        "User-Agent",
        HeaderValue::from_static("AgentSight-Node"),
    );

    let (mut socket, _) = connect_async(request).await?;
    log::debug!("AgentSight Node relay connected");

    let mut heartbeat = tokio::time::interval(Duration::from_secs(HEARTBEAT_INTERVAL_SECS));
    heartbeat.set_missed_tick_behavior(MissedTickBehavior::Delay);
    heartbeat.tick().await;

    loop {
        tokio::select! {
            _ = heartbeat.tick() => {
                // The Durable Object handles this with WebSocket auto-response,
                // so the heartbeat does not wake a hibernating relay instance.
                socket.send(Message::Text("ping".into())).await?;
            }
            message = socket.next() => {
                let Some(message) = message else { break };
                match message? {
                    Message::Text(text) if text.as_str() == "pong" => {}
                    Message::Text(text) => {
                        let response = handle_request(text.as_str(), local_endpoint, access_token).await;
                        socket.send(Message::Text(serde_json::to_string(&response)?.into())).await?;
                    }
                    Message::Ping(payload) => {
                        socket.send(Message::Pong(payload)).await?;
                    }
                    Message::Close(_) => break,
                    _ => {}
                }
            }
        }
    }
    Ok(())
}

async fn handle_request(
    raw: &str,
    local_endpoint: &str,
    access_token: &str,
) -> RelayResponseEnvelope {
    let request = match serde_json::from_str::<RelayRequestEnvelope>(raw) {
        Ok(request) if request.r#type == "request" && !request.id.is_empty() => request,
        _ => {
            return RelayResponseEnvelope {
                r#type: "response",
                id: String::new(),
                status: 400,
                body: json_error("invalid_relay_request"),
            };
        }
    };

    if !allowed_relay_path(&request.method, &request.path) {
        return RelayResponseEnvelope {
            r#type: "response",
            id: request.id,
            status: 403,
            body: json_error("relay_path_not_allowed"),
        };
    }

    match forward_local(
        local_endpoint,
        access_token,
        &request.method,
        &request.path,
        request.body.as_deref(),
    )
    .await
    {
        Ok((status, body)) => RelayResponseEnvelope {
            r#type: "response",
            id: request.id,
            status,
            body,
        },
        Err(error) => RelayResponseEnvelope {
            r#type: "response",
            id: request.id,
            status: 502,
            body: serde_json::json!({ "error": "node_request_failed", "detail": error.to_string() })
                .to_string(),
        },
    }
}

async fn forward_local(
    endpoint: &str,
    access_token: &str,
    method: &str,
    path: &str,
    body: Option<&str>,
) -> Result<(u16, String), Box<dyn Error + Send + Sync>> {
    let client: Client<HttpConnector, Full<Bytes>> =
        Client::builder(TokioExecutor::new()).build_http();
    let method = match method {
        "GET" => Method::GET,
        "POST" => Method::POST,
        _ => return Err("relay method not allowed".into()),
    };
    let mut builder = Request::builder()
        .method(method)
        .uri(format!("{endpoint}{path}"))
        .header("Authorization", format!("Bearer {access_token}"));
    if body.is_some() {
        builder = builder.header("Content-Type", "application/json");
    }
    let request = builder.body(Full::new(Bytes::from(body.unwrap_or_default().to_owned())))?;
    let response = client.request(request).await?;
    let status = response.status().as_u16();
    let bytes = response.into_body().collect().await?.to_bytes();
    if bytes.len() > MAX_RELAY_RESPONSE_BYTES {
        return Err("Node response exceeded relay limit".into());
    }
    Ok((status, String::from_utf8_lossy(&bytes).into_owned()))
}

fn relay_url(controller_url: &str, node_id: &str) -> Result<String, Box<dyn Error + Send + Sync>> {
    let mut url = Url::parse(controller_url)?;
    let scheme = match url.scheme() {
        "https" => "wss",
        "http" => "ws",
        _ => return Err("Controller URL must use http or https".into()),
    };
    url.set_scheme(scheme)
        .map_err(|_| "could not set Controller WebSocket scheme")?;
    url.set_path(&format!("/v1/relay/nodes/{node_id}"));
    url.set_query(None);
    url.set_fragment(None);
    Ok(url.into())
}

fn allowed_relay_path(method: &str, value: &str) -> bool {
    let (path, query) = value.split_once('?').map_or((value, None), |(path, query)| {
        (path, Some(query))
    });
    if method == "GET" && path == "/api/v1/snapshot" {
        return query.is_none_or(|query| {
            query.strip_prefix("audit_limit=")
                .is_some_and(|value| !value.is_empty() && value.len() <= 6 && value.bytes().all(|b| b.is_ascii_digit()))
        });
    }
    if query.is_some() {
        return false;
    }
    let Some(session) = path.strip_prefix("/api/v1/sessions/") else {
        return false;
    };
    let (session_id, messages) = session
        .strip_suffix("/messages")
        .map_or((session, false), |id| (id, true));
    if session_id.is_empty()
        || session_id.len() > 768
        || session_id.contains('/')
        || session_id.contains('\\')
        || session_id.contains("..")
    {
        return false;
    }
    (method == "GET" && !messages) || (method == "POST" && messages)
}

fn json_error(error: &str) -> String {
    serde_json::json!({ "error": error }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn relay_url_maps_https_to_wss() {
        assert_eq!(
            relay_url("https://controller.example/", "node_abc").unwrap(),
            "wss://controller.example/v1/relay/nodes/node_abc"
        );
    }

    #[test]
    fn relay_only_accepts_the_node_protocol_surface() {
        assert!(allowed_relay_path("GET", "/api/v1/snapshot?audit_limit=50000"));
        assert!(allowed_relay_path("GET", "/api/v1/sessions/session-123"));
        assert!(allowed_relay_path("POST", "/api/v1/sessions/session-123/messages"));
        assert!(!allowed_relay_path("POST", "/api/v1/snapshot"));
        assert!(!allowed_relay_path("GET", "/etc/passwd"));
        assert!(!allowed_relay_path("GET", "/api/v1/sessions/../secret"));
    }

    #[test]
    fn relay_installs_a_tls_provider() {
        install_tls_provider().unwrap();
        assert!(rustls::crypto::CryptoProvider::get_default().is_some());
    }
}
