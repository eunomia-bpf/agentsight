// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! OpenTelemetry GenAI exporter.
//!
//! Maps completed materialized `llm_call` rows onto
//! OpenTelemetry **GenAI semantic-convention** (`gen_ai.*`) spans and ships them
//! to an OpenTelemetry Collector via **OTLP/HTTP (JSON)** — the standard wire
//! format understood by the OTel Collector, Jaeger, Grafana Tempo, and the major
//! observability vendors. Because AgentSight captures the traffic at the kernel
//! (eBPF) level, this produces vendor-neutral GenAI telemetry for *any* agent
//! binary with **zero in-process instrumentation**.
//!
//! Spec: <https://opentelemetry.io/docs/specs/semconv/gen-ai/>
//!
//! Each completed call becomes one `chat {model}` CLIENT span. Correlation and
//! token extraction happen before this sink sees the row; this sink only maps
//! stable view data to OTLP.
//!
use crate::analyzers::AnalyzerError;
use crate::model::{LlmCallRow, ViewResult, ViewSink};
use crate::view::llm::provider_from_host;
use http_body_util::{BodyExt, Full};
use hyper::body::Bytes;
use hyper_util::client::legacy::Client;
use hyper_util::rt::TokioExecutor;
use serde_json::{Value, json};
use std::sync::Arc;

/// Default OTLP/HTTP receiver endpoint (OpenTelemetry Collector).
const DEFAULT_OTLP_ENDPOINT: &str = "http://localhost:4318";

#[derive(Clone)]
struct SpanInput {
    start_unix_nano: u128,
    provider: String,
    server_address: String,
    model: Option<String>,
    conversation_id: Option<String>,
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
    client: Arc<Client<hyper_util::client::legacy::connect::HttpConnector, Full<Bytes>>>,
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
            client: Arc::new(Client::builder(TokioExecutor::new()).build_http()),
        }
    }
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
    req: &SpanInput,
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
    if let Some(conversation_id) = &req.conversation_id {
        attributes.push(attr_str("gen_ai.conversation.id", conversation_id));
    }
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

impl SpanInput {
    fn from_call(call: &LlmCallRow, capture_content: bool) -> Self {
        let request = &call.request;
        let host = call.host.as_deref().unwrap_or_default();
        Self {
            start_unix_nano: (call.start_timestamp_ms as u128) * 1_000_000,
            provider: call
                .provider
                .clone()
                .unwrap_or_else(|| provider_from_host(host)),
            server_address: host.to_string(),
            conversation_id: conversation_id_from_request(request),
            model: call.model.clone().or_else(|| {
                request
                    .get("model")
                    .and_then(Value::as_str)
                    .map(String::from)
            }),
            max_tokens: request
                .get("max_tokens")
                .or_else(|| request.get("max_output_tokens"))
                .and_then(Value::as_i64),
            temperature: request.get("temperature").and_then(Value::as_f64),
            top_p: request.get("top_p").and_then(Value::as_f64),
            input_messages: capture_content
                .then(|| {
                    request
                        .get("messages")
                        .or_else(|| request.get("input"))
                        .map(Value::to_string)
                })
                .flatten(),
        }
    }
}

impl ViewSink for OtelExporter {
    fn llm_call(&mut self, call: &LlmCallRow) -> ViewResult<()> {
        let Some(end_ms) = call.end_timestamp_ms else {
            return Ok(());
        };
        let span_input = SpanInput::from_call(call, self.capture_content);
        let (trace_id, span_id) = new_ids();
        let payload = build_otlp_payload(
            &self.service_name,
            &trace_id,
            &span_id,
            &span_input,
            (end_ms as u128) * 1_000_000,
            call.status_code,
            Some(&call.response),
            self.capture_content,
        );
        let client = self.client.clone();
        let url = self.traces_url.clone();
        tokio::spawn(async move {
            if let Err(e) = post_otlp(&client, &url, payload).await {
                log::warn!("OtelExporter: failed to export span: {}", e);
            }
        });
        Ok(())
    }
}

fn conversation_id_from_request(request: &Value) -> Option<String> {
    ["conversation_id", "conversationId", "thread_id", "threadId"]
        .iter()
        .filter_map(|key| request.get(*key).and_then(Value::as_str))
        .find(|value| !value.is_empty())
        .or_else(|| request.pointer("/conversation/id").and_then(Value::as_str))
        .filter(|value| !value.is_empty())
        .map(str::to_string)
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
        // Unknown OpenAI-compatible host is reported as the host itself.
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
        let req = SpanInput {
            start_unix_nano: 1_000_000_000,
            provider: "openai".to_string(),
            server_address: "api.openai.com".to_string(),
            model: Some("gpt-4o".to_string()),
            conversation_id: Some("conv_123".to_string()),
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
            find("gen_ai.conversation.id").unwrap()["value"]["stringValue"],
            "conv_123"
        );
        assert_eq!(
            conversation_id_from_request(&json!({ "conversation": { "id": "conv_123" } }))
                .as_deref(),
            Some("conv_123")
        );
        assert_eq!(
            conversation_id_from_request(&json!({ "session_id": "sid_123" })),
            None
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
        let req = SpanInput {
            start_unix_nano: 1,
            provider: "openai".to_string(),
            server_address: "api.openai.com".to_string(),
            model: Some("gpt-4o".to_string()),
            conversation_id: None,
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
