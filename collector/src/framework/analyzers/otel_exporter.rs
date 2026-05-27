// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! OpenTelemetry GenAI exporter.
//!
//! Maps the LLM HTTP request/response pairs reconstructed by [`HTTPParser`] onto
//! OpenTelemetry **GenAI semantic-convention** (`gen_ai.*`) spans and ships them
//! to an OpenTelemetry Collector via **OTLP/HTTP (JSON)** — the standard wire
//! format understood by the OTel Collector, Jaeger, Grafana Tempo, and the major
//! observability vendors. Because AgentSight captures the traffic at the kernel
//! (eBPF) level, this produces vendor-neutral GenAI telemetry for *any* agent
//! binary with **zero in-process instrumentation**.
//!
//! Spec: <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
//!
//! Each request/response pair becomes one `chat {model}` CLIENT span. Requests
//! and responses are correlated by `(pid, tid)`; the span's start/end times come
//! from the request and response event timestamps. Token usage, finish reasons,
//! and (opt-in) message content are parsed from the JSON bodies, tolerating the
//! OpenAI, OpenAI-Responses, and Anthropic payload shapes.
//!
//! [`HTTPParser`]: super::http_parser::HTTPParser

use super::{Analyzer, AnalyzerError};
use crate::framework::runners::EventStream;
use async_trait::async_trait;
use futures::stream::StreamExt;
use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper_util::client::legacy::Client;
use hyper_util::rt::TokioExecutor;
use serde_json::{Value, json};
use std::collections::HashMap;
use std::sync::Arc;

/// Default OTLP/HTTP receiver endpoint (OpenTelemetry Collector).
const DEFAULT_OTLP_ENDPOINT: &str = "http://localhost:4318";

/// Drop a pending request that never got a matching response after this long,
/// bounding the correlation map for dropped/aborted/never-answered requests.
const PENDING_REQUEST_TIMEOUT_NANOS: u128 = 5 * 60 * 1_000_000_000; // 5 minutes

/// A request that is waiting for its matching response so a full span can be
/// emitted. Keyed by `(pid, tid)` in the exporter's pending map.
#[derive(Clone)]
struct PendingRequest {
    start_unix_nano: u128,
    provider: String,
    server_address: String,
    model: Option<String>,
    max_tokens: Option<i64>,
    temperature: Option<f64>,
    top_p: Option<f64>,
    /// Opt-in: the request messages, captured only when content capture is on.
    input_messages: Option<String>,
}

/// Exports GenAI spans for LLM HTTP exchanges via OTLP/HTTP (JSON).
pub struct OtelExporter {
    /// Full traces URL, e.g. `http://localhost:4318/v1/traces`.
    traces_url: String,
    /// `service.name` reported on the OTLP Resource.
    service_name: String,
    /// Whether to attach prompt/completion content (`gen_ai.{input,output}.messages`).
    capture_content: bool,
}

impl OtelExporter {
    /// Create an exporter. `endpoint` is the OTLP/HTTP base (e.g.
    /// `http://collector:4318`); when `None`, `OTEL_EXPORTER_OTLP_ENDPOINT` is
    /// honored, falling back to `http://localhost:4318`. A full traces endpoint
    /// in `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` takes precedence and is used as-is.
    pub fn new(endpoint: Option<String>, capture_content: bool) -> Self {
        let traces_url = if let Ok(full) = std::env::var("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") {
            full
        } else {
            let base = endpoint
                .or_else(|| std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").ok())
                .unwrap_or_else(|| DEFAULT_OTLP_ENDPOINT.to_string());
            format!("{}/v1/traces", base.trim_end_matches('/'))
        };

        let service_name =
            std::env::var("OTEL_SERVICE_NAME").unwrap_or_else(|_| "agentsight".to_string());

        Self {
            traces_url,
            service_name,
            capture_content,
        }
    }
}

/// Map an LLM API host to a `gen_ai.provider.name` value (per the spec's
/// well-known provider list). Falls back to the host for unknown OpenAI-compatible
/// endpoints (e.g. self-hosted llama.cpp / vLLM), which keeps spans useful.
fn provider_from_host(host: &str) -> String {
    let h = host.to_ascii_lowercase();
    if h.contains("openai.azure.com") {
        "azure.ai.openai".to_string()
    } else if h.contains("openai") {
        "openai".to_string()
    } else if h.contains("anthropic") {
        "anthropic".to_string()
    } else if h.contains("generativelanguage") || h.contains("googleapis") {
        "gcp.gen_ai".to_string()
    } else if h.contains("bedrock") {
        "aws.bedrock".to_string()
    } else {
        host.to_string()
    }
}

/// True if a request path targets a chat/completions-style LLM endpoint. Matches
/// the OpenAI, OpenAI-Responses, Anthropic, and Gemini URL shapes.
fn is_llm_path(path: &str) -> bool {
    path.contains("/chat/completions")
        || path.contains("/v1/messages")
        || path.contains("/v1/responses")
        || path.ends_with("/v1/completions")
        || path.contains(":generateContent")
        || path.contains(":streamGenerateContent")
}

/// Pull an integer token count from a usage object, tolerating both the
/// OpenAI (`prompt_tokens`/`completion_tokens`) and Anthropic/Responses
/// (`input_tokens`/`output_tokens`) field names.
fn usage_int(usage: &Value, names: &[&str]) -> Option<i64> {
    names
        .iter()
        .find_map(|n| usage.get(*n).and_then(|v| v.as_i64()))
}

/// Extract finish/stop reasons from a response body across provider shapes.
fn finish_reasons(body: &Value) -> Vec<String> {
    // OpenAI chat/completions: choices[].finish_reason
    if let Some(choices) = body.get("choices").and_then(|c| c.as_array()) {
        let reasons: Vec<String> = choices
            .iter()
            .filter_map(|c| {
                c.get("finish_reason")
                    .and_then(|r| r.as_str())
                    .map(String::from)
            })
            .collect();
        if !reasons.is_empty() {
            return reasons;
        }
    }
    // Anthropic messages: stop_reason
    if let Some(stop) = body.get("stop_reason").and_then(|v| v.as_str()) {
        return vec![stop.to_string()];
    }
    Vec::new()
}

/// Build an OTLP AnyValue JSON object for a string.
fn av_str(s: &str) -> Value {
    json!({ "stringValue": s })
}

/// Build an OTLP key/value attribute with a string value.
fn attr_str(key: &str, s: &str) -> Value {
    json!({ "key": key, "value": av_str(s) })
}

/// Build an OTLP key/value attribute with an int value (int64 is JSON-encoded as
/// a string per the OTLP/JSON spec).
fn attr_int(key: &str, n: i64) -> Value {
    json!({ "key": key, "value": { "intValue": n.to_string() } })
}

/// Build an OTLP key/value attribute with a double value.
fn attr_double(key: &str, n: f64) -> Value {
    json!({ "key": key, "value": { "doubleValue": n } })
}

/// Build an OTLP key/value attribute holding an array of strings.
fn attr_str_array(key: &str, items: &[String]) -> Value {
    let values: Vec<Value> = items.iter().map(|s| av_str(s)).collect();
    json!({ "key": key, "value": { "arrayValue": { "values": values } } })
}

/// Construct the OTLP/HTTP JSON `ExportTraceServiceRequest` body for a single
/// span built from a request/response pair.
fn build_otlp_payload(
    service_name: &str,
    trace_id: &str,
    span_id: &str,
    req: &PendingRequest,
    end_unix_nano: u128,
    status_code: Option<u16>,
    response_body: Option<&Value>,
    capture_content: bool,
) -> Value {
    let model_name = req.model.as_deref().unwrap_or("unknown");

    let mut attributes = vec![
        attr_str("gen_ai.operation.name", "chat"),
        attr_str("gen_ai.provider.name", &req.provider),
        attr_str("server.address", &req.server_address),
    ];
    if let Some(model) = &req.model {
        attributes.push(attr_str("gen_ai.request.model", model));
    }
    if let Some(mt) = req.max_tokens {
        attributes.push(attr_int("gen_ai.request.max_tokens", mt));
    }
    if let Some(t) = req.temperature {
        attributes.push(attr_double("gen_ai.request.temperature", t));
    }
    if let Some(p) = req.top_p {
        attributes.push(attr_double("gen_ai.request.top_p", p));
    }

    // Response-derived attributes.
    let mut span_status = json!({ "code": 1 }); // STATUS_CODE_OK
    if let Some(body) = response_body {
        if let Some(rmodel) = body.get("model").and_then(|v| v.as_str()) {
            attributes.push(attr_str("gen_ai.response.model", rmodel));
        }
        if let Some(id) = body.get("id").and_then(|v| v.as_str()) {
            attributes.push(attr_str("gen_ai.response.id", id));
        }
        if let Some(usage) = body.get("usage") {
            if let Some(input) = usage_int(usage, &["input_tokens", "prompt_tokens"]) {
                attributes.push(attr_int("gen_ai.usage.input_tokens", input));
            }
            if let Some(output) = usage_int(usage, &["output_tokens", "completion_tokens"]) {
                attributes.push(attr_int("gen_ai.usage.output_tokens", output));
            }
        }
        let reasons = finish_reasons(body);
        if !reasons.is_empty() {
            attributes.push(attr_str_array("gen_ai.response.finish_reasons", &reasons));
        }
        if capture_content {
            attributes.push(attr_str("gen_ai.output.messages", &body.to_string()));
        }
    }

    // HTTP error status -> span ERROR.
    if let Some(code) = status_code {
        attributes.push(attr_int("http.response.status_code", code as i64));
        if code >= 400 {
            span_status = json!({ "code": 2, "message": format!("HTTP {}", code) });
        }
    }

    if capture_content && let Some(msgs) = &req.input_messages {
        attributes.push(attr_str("gen_ai.input.messages", msgs));
    }

    json!({
        "resourceSpans": [{
            "resource": {
                "attributes": [ attr_str("service.name", service_name) ]
            },
            "scopeSpans": [{
                "scope": { "name": "agentsight", "version": env!("CARGO_PKG_VERSION") },
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": format!("chat {}", model_name),
                    "kind": 3, // SPAN_KIND_CLIENT
                    "startTimeUnixNano": req.start_unix_nano.to_string(),
                    "endTimeUnixNano": end_unix_nano.to_string(),
                    "attributes": attributes,
                    "status": span_status
                }]
            }]
        }]
    })
}

/// Generate a 32-hex-char trace id and 16-hex-char span id.
fn new_ids() -> (String, String) {
    let trace = uuid::Uuid::new_v4().simple().to_string(); // 32 hex chars
    let span = uuid::Uuid::new_v4().simple().to_string()[..16].to_string();
    (trace, span)
}

/// Parse a JSON body string into a `Value`, returning `None` if it isn't valid
/// JSON (e.g. an SSE-streamed body that wasn't fully reassembled).
fn parse_body(data: &Value) -> Option<Value> {
    let body = data.get("body").and_then(|v| v.as_str())?;
    serde_json::from_str(body).ok()
}

#[async_trait]
impl Analyzer for OtelExporter {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let client: Arc<Client<_, Full<Bytes>>> =
            Arc::new(Client::builder(TokioExecutor::new()).build_http());
        let traces_url = self.traces_url.clone();
        let service_name = self.service_name.clone();
        let capture_content = self.capture_content;

        log::info!("OtelExporter: exporting GenAI spans to {}", traces_url);

        // Correlate requests with responses by (pid, tid). `.map` takes an
        // FnMut, so this map persists across the whole stream.
        let mut pending: HashMap<(u32, u64), PendingRequest> = HashMap::new();

        let processed = stream.map(move |event| {
            if event.source != "http_parser" {
                return event;
            }
            let data = &event.data;
            let tid = data.get("tid").and_then(|v| v.as_u64()).unwrap_or(0);
            let key = (event.pid, tid);
            let msg_type = data
                .get("message_type")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let unix_nano = (event.timestamp as u128) * 1_000_000; // ms -> ns

            // Evict requests that never got a matching response so `pending`
            // can't grow without bound (dropped connections, killed agents,
            // responses on a different tid, …).
            pending.retain(|_, req| {
                unix_nano.saturating_sub(req.start_unix_nano) <= PENDING_REQUEST_TIMEOUT_NANOS
            });

            match msg_type {
                "request" => {
                    let host = data
                        .get("headers")
                        .and_then(|h| h.get("host"))
                        .and_then(|v| v.as_str())
                        .unwrap_or("");
                    let path = data.get("path").and_then(|v| v.as_str()).unwrap_or("");
                    if is_llm_path(path) {
                        let body = parse_body(data);
                        let model = body
                            .as_ref()
                            .and_then(|b| b.get("model"))
                            .and_then(|v| v.as_str())
                            .map(String::from);
                        let max_tokens = body
                            .as_ref()
                            .and_then(|b| {
                                b.get("max_tokens").or_else(|| b.get("max_output_tokens"))
                            })
                            .and_then(|v| v.as_i64());
                        let temperature = body
                            .as_ref()
                            .and_then(|b| b.get("temperature"))
                            .and_then(|v| v.as_f64());
                        let top_p = body
                            .as_ref()
                            .and_then(|b| b.get("top_p"))
                            .and_then(|v| v.as_f64());
                        let input_messages = if capture_content {
                            body.as_ref().and_then(|b| {
                                b.get("messages")
                                    .or_else(|| b.get("input"))
                                    .map(|m| m.to_string())
                            })
                        } else {
                            None
                        };
                        pending.insert(
                            key,
                            PendingRequest {
                                start_unix_nano: unix_nano,
                                provider: provider_from_host(host),
                                server_address: host.to_string(),
                                model,
                                max_tokens,
                                temperature,
                                top_p,
                                input_messages,
                            },
                        );
                    }
                }
                "response" => {
                    if let Some(req) = pending.remove(&key) {
                        let status_code = data
                            .get("status_code")
                            .and_then(|v| v.as_u64())
                            .map(|c| c as u16);
                        let response_body = parse_body(data);
                        let (trace_id, span_id) = new_ids();
                        let payload = build_otlp_payload(
                            &service_name,
                            &trace_id,
                            &span_id,
                            &req,
                            unix_nano,
                            status_code,
                            response_body.as_ref(),
                            capture_content,
                        );

                        // Fire the OTLP POST without blocking the event stream.
                        let client = client.clone();
                        let url = traces_url.clone();
                        tokio::spawn(async move {
                            if let Err(e) = post_otlp(&client, &url, payload).await {
                                log::warn!("OtelExporter: failed to export span: {}", e);
                            }
                        });
                    }
                }
                _ => {}
            }
            event
        });

        Ok(Box::pin(processed))
    }

    fn name(&self) -> &str {
        "OtelExporter"
    }
}

/// POST an OTLP/HTTP JSON trace payload to the collector.
async fn post_otlp(
    client: &Client<hyper_util::client::legacy::connect::HttpConnector, Full<Bytes>>,
    url: &str,
    payload: Value,
) -> Result<(), AnalyzerError> {
    let body = serde_json::to_vec(&payload)?;
    let req = hyper::Request::builder()
        .method(hyper::Method::POST)
        .uri(url)
        .header(hyper::header::CONTENT_TYPE, "application/json")
        .body(Full::new(Bytes::from(body)))?;

    let resp = client.request(req).await?;
    let status = resp.status();
    if !status.is_success() {
        let bytes = resp.into_body().collect().await?.to_bytes();
        let text = String::from_utf8_lossy(&bytes);
        return Err(format!("collector returned {}: {}", status, text.trim()).into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_llm_paths() {
        assert!(is_llm_path("/v1/chat/completions"));
        assert!(is_llm_path("/v1/messages"));
        assert!(is_llm_path("/v1/responses"));
        assert!(is_llm_path("/openai/deployments/gpt4/chat/completions"));
        assert!(is_llm_path("/v1beta/models/gemini-pro:generateContent"));
        assert!(!is_llm_path("/v1/rgstr"));
        assert!(!is_llm_path("/health"));
    }

    #[test]
    fn maps_providers() {
        assert_eq!(provider_from_host("api.openai.com"), "openai");
        assert_eq!(provider_from_host("api.anthropic.com"), "anthropic");
        assert_eq!(
            provider_from_host("generativelanguage.googleapis.com"),
            "gcp.gen_ai"
        );
        assert_eq!(
            provider_from_host("my-resource.openai.azure.com"),
            "azure.ai.openai"
        );
        // Unknown OpenAI-compatible host falls back to the host itself.
        assert_eq!(provider_from_host("localhost:8443"), "localhost:8443");
    }

    #[test]
    fn parses_usage_both_shapes() {
        let openai = json!({ "usage": { "prompt_tokens": 12, "completion_tokens": 7 } });
        assert_eq!(
            usage_int(&openai["usage"], &["input_tokens", "prompt_tokens"]),
            Some(12)
        );
        assert_eq!(
            usage_int(&openai["usage"], &["output_tokens", "completion_tokens"]),
            Some(7)
        );

        let anthropic = json!({ "usage": { "input_tokens": 30, "output_tokens": 15 } });
        assert_eq!(
            usage_int(&anthropic["usage"], &["input_tokens", "prompt_tokens"]),
            Some(30)
        );
    }

    #[test]
    fn extracts_finish_reasons() {
        let openai = json!({ "choices": [{ "finish_reason": "stop" }] });
        assert_eq!(finish_reasons(&openai), vec!["stop".to_string()]);
        let anthropic = json!({ "stop_reason": "end_turn" });
        assert_eq!(finish_reasons(&anthropic), vec!["end_turn".to_string()]);
        let none = json!({ "foo": 1 });
        assert!(finish_reasons(&none).is_empty());
    }

    #[test]
    fn builds_payload_with_gen_ai_attributes() {
        let req = PendingRequest {
            start_unix_nano: 1_000_000_000,
            provider: "openai".to_string(),
            server_address: "api.openai.com".to_string(),
            model: Some("gpt-4o".to_string()),
            max_tokens: Some(256),
            temperature: Some(0.7),
            top_p: None,
            input_messages: None,
        };
        let response = json!({
            "model": "gpt-4o-2024",
            "usage": { "prompt_tokens": 10, "completion_tokens": 5 },
            "choices": [{ "finish_reason": "stop" }]
        });
        let payload = build_otlp_payload(
            "agentsight",
            "0123456789abcdef0123456789abcdef",
            "0123456789abcdef",
            &req,
            2_000_000_000,
            Some(200),
            Some(&response),
            false,
        );

        let span = &payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0];
        assert_eq!(span["name"], "chat gpt-4o");
        assert_eq!(span["kind"], 3);
        assert_eq!(span["startTimeUnixNano"], "1000000000");
        assert_eq!(span["endTimeUnixNano"], "2000000000");

        let attrs = span["attributes"].as_array().unwrap();
        let find = |k: &str| attrs.iter().find(|a| a["key"] == k).cloned();
        assert_eq!(
            find("gen_ai.operation.name").unwrap()["value"]["stringValue"],
            "chat"
        );
        assert_eq!(
            find("gen_ai.provider.name").unwrap()["value"]["stringValue"],
            "openai"
        );
        assert_eq!(
            find("gen_ai.request.model").unwrap()["value"]["stringValue"],
            "gpt-4o"
        );
        assert_eq!(
            find("gen_ai.request.max_tokens").unwrap()["value"]["intValue"],
            "256"
        );
        assert_eq!(
            find("gen_ai.usage.input_tokens").unwrap()["value"]["intValue"],
            "10"
        );
        assert_eq!(
            find("gen_ai.usage.output_tokens").unwrap()["value"]["intValue"],
            "5"
        );
        assert_eq!(span["status"]["code"], 1);
        // Content not captured by default.
        assert!(find("gen_ai.input.messages").is_none());
    }

    #[test]
    fn error_status_marks_span_error() {
        let req = PendingRequest {
            start_unix_nano: 1,
            provider: "openai".to_string(),
            server_address: "api.openai.com".to_string(),
            model: Some("gpt-4o".to_string()),
            max_tokens: None,
            temperature: None,
            top_p: None,
            input_messages: None,
        };
        let payload = build_otlp_payload("agentsight", "t", "s", &req, 2, Some(429), None, false);
        let span = &payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0];
        assert_eq!(span["status"]["code"], 2);
    }
}
