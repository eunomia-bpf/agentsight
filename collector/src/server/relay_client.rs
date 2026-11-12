// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::server::capability;
use futures::{SinkExt, StreamExt};
use http_body_util::{BodyExt, Full, Limited};
use hyper::body::Bytes;
use hyper::{Method, Request};
use hyper_util::client::legacy::Client;
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_util::rt::TokioExecutor;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::future::Future;
use std::time::Duration;
use tokio::task::JoinSet;
use tokio::time::MissedTickBehavior;
use tokio_tungstenite::connect_async;
use tokio_tungstenite::tungstenite::Message;
use tokio_tungstenite::tungstenite::client::IntoClientRequest;
use tokio_tungstenite::tungstenite::http::HeaderValue;
use url::Url;

const MAX_RELAY_RESPONSE_BYTES: usize = 16 * 1024 * 1024;
const RECONNECT_DELAY_SECS: u64 = 2;
const HEARTBEAT_INTERVAL_SECS: u64 = 20;
const RELAY_CAPABILITY_TTL_SECONDS: u64 = 60;
const RELAY_REQUEST_TIMEOUT: Duration = Duration::from_secs(24);
// A response may be as large as MAX_RELAY_RESPONSE_BYTES. Keeping this below
// the Controller's global pending cap bounds a single Node to 128 MiB of relay
// response buffers while still allowing slow provider requests and UI reads to
// make progress independently.
const MAX_IN_FLIGHT_RELAY_REQUESTS: usize = 8;
const NODE_VERSION_HEADER: &str = "x-agentsight-node-version";

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

#[derive(Deserialize)]
struct MintResponse {
    access_token: String,
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
    bootstrap_token: &str,
    local_endpoint: &str,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let mut request = relay_url.into_client_request()?;
    request.headers_mut().insert(
        "Authorization",
        HeaderValue::from_str(&format!("Bearer {bootstrap_token}"))?,
    );
    request
        .headers_mut()
        .insert("User-Agent", HeaderValue::from_static("AgentSight-Node"));
    request.headers_mut().insert(
        NODE_VERSION_HEADER,
        HeaderValue::from_static(env!("CARGO_PKG_VERSION")),
    );

    let (socket, _) = connect_async(request).await?;
    log::debug!("AgentSight Node relay connected");
    let (mut relay_writer, mut relay_reader) = socket.split();
    let mut requests = JoinSet::new();

    let mut heartbeat = tokio::time::interval(Duration::from_secs(HEARTBEAT_INTERVAL_SECS));
    heartbeat.set_missed_tick_behavior(MissedTickBehavior::Delay);
    heartbeat.tick().await;

    loop {
        tokio::select! {
            _ = heartbeat.tick() => {
                // The Durable Object handles this with WebSocket auto-response,
                // so the heartbeat does not wake a hibernating relay instance.
                relay_writer.send(Message::Text("ping".into())).await?;
            }
            response = requests.join_next(), if !requests.is_empty() => {
                let response = response
                    .ok_or("relay request task disappeared")?
                    .map_err(|error| format!("relay request task failed: {error}"))?;
                relay_writer
                    .send(Message::Text(serde_json::to_string(&response)?.into()))
                    .await?;
            }
            message = relay_reader.next() => {
                let Some(message) = message else { break };
                match message? {
                    Message::Text(text) if text.as_str() == "pong" => {}
                    Message::Text(text) => {
                        if requests.len() >= MAX_IN_FLIGHT_RELAY_REQUESTS {
                            let response = relay_overloaded_response(text.as_str());
                            relay_writer
                                .send(Message::Text(serde_json::to_string(&response)?.into()))
                                .await?;
                            continue;
                        }
                        let local_endpoint = local_endpoint.to_string();
                        let bootstrap_token = bootstrap_token.to_string();
                        requests.spawn(async move {
                            let id = relay_request_id(text.as_str());
                            timeout_relay_response(
                                id,
                                RELAY_REQUEST_TIMEOUT,
                                handle_request(text.as_str(), &local_endpoint, &bootstrap_token),
                            )
                            .await
                        });
                    }
                    Message::Ping(payload) => {
                        relay_writer.send(Message::Pong(payload)).await?;
                    }
                    Message::Close(_) => break,
                    _ => {}
                }
            }
        }
    }
    requests.abort_all();
    Ok(())
}

fn relay_overloaded_response(raw: &str) -> RelayResponseEnvelope {
    RelayResponseEnvelope {
        r#type: "response",
        id: relay_request_id(raw),
        status: 429,
        body: json_error("node_relay_busy"),
    }
}

fn relay_request_id(raw: &str) -> String {
    serde_json::from_str::<RelayRequestEnvelope>(raw)
        .ok()
        .filter(|request| request.r#type == "request")
        .map(|request| request.id)
        .unwrap_or_default()
}

async fn timeout_relay_response<F>(
    id: String,
    timeout: Duration,
    response: F,
) -> RelayResponseEnvelope
where
    F: Future<Output = RelayResponseEnvelope>,
{
    match tokio::time::timeout(timeout, response).await {
        Ok(response) => response,
        Err(_) => RelayResponseEnvelope {
            r#type: "response",
            id,
            status: 504,
            body: json_error("node_request_timeout"),
        },
    }
}

async fn handle_request(
    raw: &str,
    local_endpoint: &str,
    bootstrap_token: &str,
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

    // Capability minting is the only relay operation that uses the Node's
    // persistent bootstrap credential directly. All normal data/control
    // operations are translated into a short-lived local capability first.
    let credential = if request.method == "POST" && request.path == "/api/v1/capabilities" {
        bootstrap_token.to_string()
    } else {
        let Some((action, session_id)) =
            capability::action_for_request(&request.method, &request.path)
        else {
            return RelayResponseEnvelope {
                r#type: "response",
                id: request.id,
                status: 403,
                body: json_error("relay_path_not_allowed"),
            };
        };
        match mint_local_capability(
            local_endpoint,
            bootstrap_token,
            action,
            session_id.as_deref(),
        )
        .await
        {
            Ok(token) => token,
            Err(error) => {
                return RelayResponseEnvelope {
                    r#type: "response",
                    id: request.id,
                    status: 502,
                    body: serde_json::json!({
                        "error": "node_capability_failed",
                        "detail": error.to_string()
                    })
                    .to_string(),
                };
            }
        }
    };

    match forward_local(
        local_endpoint,
        &credential,
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
            body:
                serde_json::json!({ "error": "node_request_failed", "detail": error.to_string() })
                    .to_string(),
        },
    }
}

async fn mint_local_capability(
    endpoint: &str,
    bootstrap_token: &str,
    action: &str,
    session_id: Option<&str>,
) -> Result<String, Box<dyn Error + Send + Sync>> {
    let body = serde_json::json!({
        "actions": [action],
        "session_id": session_id,
        "ttl_seconds": RELAY_CAPABILITY_TTL_SECONDS,
    })
    .to_string();
    let (status, body) = forward_local(
        endpoint,
        bootstrap_token,
        "POST",
        "/api/v1/capabilities",
        Some(&body),
    )
    .await?;
    if status != 201 {
        return Err(format!("Node capability mint failed with HTTP {status}").into());
    }
    let response: MintResponse = serde_json::from_str(&body)?;
    if !response.access_token.starts_with("cap_") {
        return Err("Node returned an invalid capability".into());
    }
    Ok(response.access_token)
}

async fn forward_local(
    endpoint: &str,
    credential: &str,
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
        .header("Authorization", format!("Bearer {credential}"));
    if body.is_some() {
        builder = builder.header("Content-Type", "application/json");
    }
    let request = builder.body(Full::new(Bytes::from(body.unwrap_or_default().to_owned())))?;
    let response = client.request(request).await?;
    let status = response.status().as_u16();
    let bytes = Limited::new(response.into_body(), MAX_RELAY_RESPONSE_BYTES)
        .collect()
        .await
        .map_err(|error| format!("Node response exceeded relay limit: {error}"))?
        .to_bytes();
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
    let (path, query) = value
        .split_once('?')
        .map_or((value, None), |(path, query)| (path, Some(query)));
    if method == "POST" && path == "/api/v1/capabilities" && query.is_none() {
        return true;
    }
    if method == "GET" && path == "/api/v1/snapshot" {
        return query.is_none_or(|query| {
            query.strip_prefix("audit_limit=").is_some_and(|value| {
                !value.is_empty() && value.len() <= 6 && value.bytes().all(|b| b.is_ascii_digit())
            })
        });
    }
    if method == "GET" && path == "/api/v1/overview" {
        return query.is_none();
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
    use hyper::Response;
    use hyper::server::conn::http1;
    use hyper::service::service_fn;
    use hyper_util::rt::TokioIo;
    use std::convert::Infallible;
    use std::sync::Arc;
    use tokio::net::TcpListener;
    use tokio::sync::Barrier;
    use tokio_tungstenite::accept_async;

    #[test]
    fn relay_url_maps_https_to_wss() {
        assert_eq!(
            relay_url("https://controller.example/", "node_abc").unwrap(),
            "wss://controller.example/v1/relay/nodes/node_abc"
        );
    }

    #[test]
    fn relay_only_accepts_the_node_protocol_and_internal_mint_surface() {
        assert!(allowed_relay_path("POST", "/api/v1/capabilities"));
        assert!(allowed_relay_path(
            "GET",
            "/api/v1/snapshot?audit_limit=50000"
        ));
        assert!(allowed_relay_path("GET", "/api/v1/overview"));
        assert!(allowed_relay_path("GET", "/api/v1/sessions/session-123"));
        assert!(allowed_relay_path(
            "POST",
            "/api/v1/sessions/session-123/messages"
        ));
        assert!(!allowed_relay_path("POST", "/api/v1/snapshot"));
        assert!(!allowed_relay_path("GET", "/etc/passwd"));
        assert!(!allowed_relay_path("GET", "/api/v1/sessions/../secret"));
    }

    #[test]
    fn relay_installs_a_tls_provider() {
        install_tls_provider().unwrap();
        assert!(rustls::crypto::CryptoProvider::get_default().is_some());
    }

    #[test]
    fn overloaded_relay_response_preserves_the_request_id() {
        let response = relay_overloaded_response(
            r#"{"type":"request","id":"request-7","method":"GET","path":"/api/v1/overview"}"#,
        );
        assert_eq!(response.id, "request-7");
        assert_eq!(response.status, 429);
        assert_eq!(response.body, r#"{"error":"node_relay_busy"}"#);
    }

    #[tokio::test]
    async fn timed_out_relay_request_releases_its_slot_with_the_same_id() {
        let response = timeout_relay_response(
            "request-8".into(),
            Duration::from_millis(10),
            std::future::pending(),
        )
        .await;

        assert_eq!(response.id, "request-8");
        assert_eq!(response.status, 504);
        assert_eq!(response.body, r#"{"error":"node_request_timeout"}"#);
    }

    #[tokio::test]
    async fn relay_forwards_independent_requests_concurrently() {
        let node_listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let node_address = node_listener.local_addr().unwrap();
        let concurrent_requests = Arc::new(Barrier::new(2));
        let node = tokio::spawn(async move {
            loop {
                let Ok((stream, _)) = node_listener.accept().await else {
                    break;
                };
                let concurrent_requests = Arc::clone(&concurrent_requests);
                tokio::spawn(async move {
                    let service = service_fn(move |request: Request<hyper::body::Incoming>| {
                        let concurrent_requests = Arc::clone(&concurrent_requests);
                        async move {
                            let (status, body) = if request.uri().path() == "/api/v1/capabilities" {
                                (201, r#"{"access_token":"cap_test"}"#)
                            } else {
                                concurrent_requests.wait().await;
                                (200, "{}")
                            };
                            Ok::<_, Infallible>(
                                Response::builder()
                                    .status(status)
                                    .body(Full::new(Bytes::from(body)))
                                    .unwrap(),
                            )
                        }
                    });
                    let _ = http1::Builder::new()
                        .serve_connection(TokioIo::new(stream), service)
                        .await;
                });
            }
        });

        let relay_listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let relay_address = relay_listener.local_addr().unwrap();
        let controller = tokio::spawn(async move {
            let (stream, _) = relay_listener.accept().await.unwrap();
            let mut socket = accept_async(stream).await.unwrap();
            for id in ["request-1", "request-2"] {
                socket
                    .send(Message::Text(
                        serde_json::json!({
                            "type":"request",
                            "id":id,
                            "method":"GET",
                            "path":"/api/v1/overview"
                        })
                        .to_string()
                        .into(),
                    ))
                    .await
                    .unwrap();
            }
            let mut responses = Vec::new();
            while responses.len() < 2 {
                let Some(Ok(Message::Text(text))) = socket.next().await else {
                    continue;
                };
                let value: serde_json::Value = serde_json::from_str(text.as_str()).unwrap();
                responses.push(value["id"].as_str().unwrap().to_string());
            }
            responses.sort();
            assert_eq!(responses, ["request-1", "request-2"]);
            socket.close(None).await.unwrap();
        });

        let result = tokio::time::timeout(
            Duration::from_secs(3),
            connect_once(
                &format!("ws://{relay_address}"),
                "bootstrap",
                &format!("http://{node_address}"),
            ),
        )
        .await
        .unwrap();
        result.unwrap();
        controller.await.unwrap();
        node.abort();
    }
}
