//! AuditAnalyzer - extracts audit records from aggregated results
//!
//! Pure logic layer, no IO. Converts `AggregatedResult` into `AuditRecord`.

use crate::aggregator::HttpPair;
use crate::aggregator::AggregatedProcess;
use crate::aggregator::AggregatedResult;
use super::record::{AuditEventType, AuditExtra, AuditRecord};

/// Analyzes aggregated results and extracts audit records
pub struct AuditAnalyzer;

impl AuditAnalyzer {
    /// Create a new AuditAnalyzer
    pub fn new() -> Self {
        AuditAnalyzer
    }

    /// Analyze an aggregated result and extract an audit record if applicable
    pub fn analyze(&self, result: &AggregatedResult) -> Option<AuditRecord> {
        match result {
            AggregatedResult::HttpComplete(pair) => Some(self.extract_llm_call(pair, false)),
            AggregatedResult::SseComplete(pair) => Some(self.extract_llm_call(pair, true)),
            AggregatedResult::ProcessComplete(process) => {
                Some(self.extract_process_action(process))
            }
            _ => None,
        }
    }

    /// Extract an LLM call audit record from an HTTP pair
    fn extract_llm_call(&self, pair: &HttpPair, is_sse: bool) -> AuditRecord {
        let request = &pair.request;
        let pid = request.source_event.pid;
        let comm = request.source_event.comm_str();

        // Extract request info
        let request_method = Some(request.method.clone());
        let request_path = Some(request.path.clone());
        let request_ts = request.source_event.timestamp_ns;

        // Extract response info
        let response_status = Some(pair.response.parsed.status_code);

        // Detect provider from request path/headers
        let provider = detect_provider(&request.path, &request.headers);
        let model = detect_model_from_request(pair);

        // Calculate duration
        let response_end_ts = pair.response.end_timestamp_ns();
        let duration_ns = response_end_ts.saturating_sub(request_ts);

        AuditRecord {
            id: None,
            event_type: AuditEventType::LlmCall,
            timestamp_ns: request_ts,
            pid,
            ppid: None,
            comm,
            duration_ns,
            extra: AuditExtra::LlmCall {
                provider,
                model,
                request_method,
                request_path,
                response_status,
                input_tokens: 0,
                output_tokens: 0,
                cache_creation_tokens: 0,
                cache_read_tokens: 0,
                is_sse,
            },
        }
    }

    /// Extract a process action audit record from an aggregated process
    fn extract_process_action(&self, process: &AggregatedProcess) -> AuditRecord {
        AuditRecord {
            id: None,
            event_type: AuditEventType::ProcessAction,
            timestamp_ns: process.start_timestamp_ns,
            pid: process.pid,
            ppid: Some(process.ppid),
            comm: process.comm.clone(),
            duration_ns: process.duration_ns(),
            extra: AuditExtra::ProcessAction {
                filename: process.filename.clone(),
                args: process.args.clone(),
                exit_code: None, // AggregatedProcess doesn't have exit_code yet
            },
        }
    }
}

impl Default for AuditAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

/// Detect LLM provider from request path and headers
fn detect_provider(
    path: &str,
    headers: &std::collections::HashMap<String, String>,
) -> Option<String> {
    // Check by path patterns
    if path.contains("/v1/messages") {
        return Some("Anthropic".to_string());
    }
    if path.contains("/v1/chat/completions") || path.contains("/v1/completions") {
        return Some("OpenAI".to_string());
    }
    if path.contains("generateContent") || path.contains("streamGenerateContent") {
        return Some("Google".to_string());
    }

    // Check by Host header
    if let Some(host) = headers.get("host").or_else(|| headers.get("Host")) {
        if host.contains("anthropic.com") {
            return Some("Anthropic".to_string());
        }
        if host.contains("openai.com") {
            return Some("OpenAI".to_string());
        }
        if host.contains("googleapis.com") || host.contains("gemini") {
            return Some("Google".to_string());
        }
    }

    None
}

/// Try to detect model from request body JSON
fn detect_model_from_request(pair: &HttpPair) -> Option<String> {
    let body = pair.request.body();
    if body.is_empty() {
        return None;
    }
    let json: serde_json::Value = serde_json::from_slice(body).ok()?;
    json.get("model")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
}
