// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
use crate::json::{i64_field as json_i64, parse_optional_value as parse_optional_json};
use crate::model::{
    AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow, ResourceSampleRow, TokenUsageRow,
    ToolCallRow, ViewResult,
};
use crate::text::sanitize_ascii_identifier as sanitize_id;
use crate::view::llm::TokenUsage;
use crate::view::{
    CanonicalEvent, EventKind, body_json, extract_model, extract_token_usage,
    extract_token_usage_from_sse, normalize_event, provider_from_host,
};
use crate::view::{MaterializedView, PendingRequest};
use serde_json::Value;

const PENDING_REQUEST_TTL_MS: u64 = 5 * 60 * 1000;
const MAX_PENDING_REQUESTS_PER_STREAM: usize = 16;

impl MaterializedView {
    pub(crate) fn ingest_event(&mut self, event: &Event) -> ViewResult<()> {
        self.next_seq += 1;
        let raw_id = format!(
            "event-{}-{}-{}-{}",
            event.timestamp,
            sanitize_id(&event.source),
            event.pid,
            self.next_seq
        );
        let canonical = normalize_event(event, raw_id);
        self.prune_pending(canonical.timestamp_ms);
        if let Some(sample) = resource_sample_from_event(&canonical) {
            self.emit_resource_sample(sample)?;
        }
        if let Some(target) = network_target_from_event(&canonical) {
            self.emit_network_target(target)?;
        }
        self.ingest(&canonical)
    }

    fn ingest(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        self.ingest_agent_specific_event(event)?;
        match event.kind {
            EventKind::LlmRequest => self.ingest_llm_request(event),
            EventKind::LlmResponse | EventKind::LlmError => self.ingest_llm_response(event),
            EventKind::ProcessExec => self.ingest_process_audit(event, "exec"),
            EventKind::ProcessExit => self.ingest_process_audit(event, "exit"),
            EventKind::FsOpen if is_writable_open(event) => self.ingest_file_audit(event),
            EventKind::FsWrite | EventKind::FsMutation => self.ingest_file_audit(event),
            EventKind::Unknown if is_process_summary_write_event(event) => {
                self.ingest_file_audit(event)
            }
            EventKind::Unknown if is_process_network_event(event) => {
                self.ingest_network_audit(event)
            }
            _ => Ok(()),
        }
    }

    fn ingest_llm_request(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        let (Some(pid), Some(tid)) = (event.pid, event.tid) else {
            return Ok(());
        };
        let req = PendingRequest {
            event_id: event.event_id.clone(),
            timestamp_ms: event.timestamp_ms,
            pid,
            comm: event.comm.clone().unwrap_or_default(),
            provider: event.provider.clone(),
            model: event.model.clone(),
            host: event.host.clone(),
            path: event.path.clone(),
            request_id: event.request_id.clone(),
            body_json: body_json(&event.attributes),
        };
        if req.body_json.is_none() && req.model.is_none() {
            return Ok(());
        }
        self.insert_orphan_llm_request(&req)?;
        let requests = self.pending.entry((pid, tid)).or_default();
        requests.push_back(req);
        while requests.len() > MAX_PENDING_REQUESTS_PER_STREAM {
            requests.pop_front();
        }
        Ok(())
    }

    fn ingest_llm_response(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        let Some(pid) = event.pid else {
            return Ok(());
        };
        if let Some(tid) = event.tid
            && let Some((req, confidence)) = self.take_matching_request(pid, tid, event)
        {
            return self.upsert_llm_pair(req, event, confidence);
        }
        self.insert_orphan_llm_response(event)
    }

    fn take_matching_request(
        &mut self,
        pid: u32,
        tid: u64,
        resp: &CanonicalEvent,
    ) -> Option<(PendingRequest, f32)> {
        let requests = self.pending.get_mut(&(pid, tid))?;
        let (req, confidence) = if let Some(resp_request_id) = resp.request_id.as_deref() {
            let pos = requests
                .iter()
                .position(|req| req.request_id.as_deref() == Some(resp_request_id))?;
            (requests.remove(pos)?, 0.95)
        } else if requests.len() == 1 {
            (requests.pop_front()?, 0.75)
        } else {
            let pos = {
                let mut candidates = requests
                    .iter()
                    .enumerate()
                    .filter(|(_, req)| req.body_json.is_some() || req.model.is_some())
                    .map(|(idx, _)| idx);
                let pos = candidates.next()?;
                if candidates.next().is_some() {
                    return None;
                }
                pos
            };
            (requests.remove(pos)?, 0.7)
        };
        if requests.is_empty() {
            self.pending.remove(&(pid, tid));
        }
        Some((req, confidence))
    }

    fn prune_pending(&mut self, now_ms: u64) {
        let cutoff = now_ms.saturating_sub(PENDING_REQUEST_TTL_MS);
        self.pending.retain(|_, requests| {
            while requests
                .front()
                .is_some_and(|req| req.timestamp_ms < cutoff)
            {
                requests.pop_front();
            }
            !requests.is_empty()
        });
    }

    fn upsert_llm_pair(
        &mut self,
        req: PendingRequest,
        resp: &CanonicalEvent,
        confidence: f32,
    ) -> ViewResult<()> {
        let response_body = response_body_json(resp);
        let model = req
            .model
            .clone()
            .or_else(|| response_body.as_ref().and_then(extract_model))
            .or_else(|| resp.model.clone())
            .unwrap_or_else(|| "unknown".to_string());
        let provider = req
            .provider
            .clone()
            .or_else(|| req.host.as_deref().map(provider_from_host));
        let llm_call_id = format!("llm-{}", req.event_id);
        let status_code = resp.status_code;
        let mut call_row = llm_call_row(
            &llm_call_id,
            req.timestamp_ms,
            Some(resp.timestamp_ms),
            req.pid,
            &req.comm,
            provider.as_deref(),
            Some(&model),
            req.host.as_deref(),
            req.path.as_deref(),
            status_code,
            req.body_json.as_ref(),
            response_body.as_ref(),
        );
        if let Some(usage) = self.ingest_response_usage_and_tools(
            resp,
            &llm_call_id,
            req.pid,
            &req.comm,
            provider.as_deref(),
            &model,
            response_body.as_ref(),
            confidence,
        )? {
            call_row.input_tokens = usage.input_tokens;
            call_row.output_tokens = usage.output_tokens;
            call_row.total_tokens = usage.total_tokens;
        }
        emit_llm_audit(
            self,
            &llm_call_id,
            resp.timestamp_ms,
            req.pid,
            &req.comm,
            Some(&model),
            "call",
            req.host.as_deref(),
            if status_code.map(|c| c >= 400).unwrap_or(false) {
                "failure"
            } else {
                "success"
            },
            "LLM call",
            response_body.as_ref(),
        )?;
        self.emit_llm_call(call_row)
    }

    fn insert_orphan_llm_request(&mut self, req: &PendingRequest) -> ViewResult<()> {
        let llm_call_id = format!("llm-{}", req.event_id);
        let provider = req
            .provider
            .clone()
            .or_else(|| req.host.as_deref().map(provider_from_host));
        let call_row = llm_call_row(
            &llm_call_id,
            req.timestamp_ms,
            None,
            req.pid,
            &req.comm,
            provider.as_deref(),
            req.model.as_deref(),
            req.host.as_deref(),
            req.path.as_deref(),
            None,
            req.body_json.as_ref(),
            None,
        );
        emit_llm_audit(
            self,
            &llm_call_id,
            req.timestamp_ms,
            req.pid,
            &req.comm,
            req.model.as_deref(),
            "request",
            req.host.as_deref(),
            "orphan_request",
            "LLM request",
            req.body_json.as_ref(),
        )?;
        self.emit_llm_call(call_row)
    }

    fn insert_orphan_llm_response(&mut self, resp: &CanonicalEvent) -> ViewResult<()> {
        let response_body = response_body_json(resp);
        let model = resp
            .model
            .clone()
            .or_else(|| response_body.as_ref().and_then(extract_model))
            .unwrap_or_else(|| "unknown".to_string());
        let provider = resp
            .provider
            .clone()
            .or_else(|| resp.host.as_deref().map(provider_from_host));
        let pid = resp.pid.unwrap_or(0);
        let comm = resp.comm.clone().unwrap_or_default();
        let llm_call_id = format!("llm-orphan-{}", resp.event_id);
        let mut call_row = llm_call_row(
            &llm_call_id,
            resp.timestamp_ms,
            Some(resp.timestamp_ms),
            pid,
            &comm,
            provider.as_deref(),
            Some(&model),
            resp.host.as_deref(),
            resp.path.as_deref(),
            resp.status_code,
            None,
            response_body.as_ref(),
        );
        if let Some(usage) = self.ingest_response_usage_and_tools(
            resp,
            &llm_call_id,
            pid,
            &comm,
            provider.as_deref(),
            &model,
            response_body.as_ref(),
            0.35,
        )? {
            call_row.input_tokens = usage.input_tokens;
            call_row.output_tokens = usage.output_tokens;
            call_row.total_tokens = usage.total_tokens;
        }
        emit_llm_audit(
            self,
            &llm_call_id,
            resp.timestamp_ms,
            pid,
            &comm,
            Some(&model),
            "response",
            resp.host.as_deref(),
            "orphan_response",
            "LLM response",
            response_body.as_ref(),
        )?;
        self.emit_llm_call(call_row)
    }

    #[allow(clippy::too_many_arguments)]
    fn ingest_response_usage_and_tools(
        &mut self,
        resp: &CanonicalEvent,
        llm_call_id: &str,
        pid: u32,
        comm: &str,
        provider: Option<&str>,
        model: &str,
        response_body: Option<&Value>,
        confidence: f32,
    ) -> ViewResult<Option<TokenUsageRow>> {
        let usage = if resp.source == "sse_processor" {
            extract_token_usage_from_sse(&resp.attributes)
        } else {
            response_body.map(extract_token_usage).unwrap_or_default()
        };
        let mut usage_row = None;
        if !usage.is_empty() {
            let token_id = format!("token-{llm_call_id}");
            let row = token_usage_row(
                &token_id,
                llm_call_id,
                resp.timestamp_ms,
                pid,
                Some(comm),
                provider,
                Some(model),
                &usage,
                "response_usage",
                confidence,
            );
            self.emit_token_usage(row.clone())?;
            usage_row = Some(row);
        }
        self.ingest_sse_tools(resp, llm_call_id, pid, confidence)?;
        Ok(usage_row)
    }

    fn ingest_agent_specific_event(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        self.ingest_claude_telemetry(event)?;
        self.ingest_gemini_stdio_stats(event)
    }

    fn ingest_claude_telemetry(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        let host = event.host.as_deref().unwrap_or_default();
        if !host.contains("datadoghq.com") && event.source != "ssl" {
            return Ok(());
        }
        let body = body_json(&event.attributes).or_else(|| {
            event
                .attributes
                .get("data")
                .and_then(|v| v.as_str())
                .and_then(parse_json_str)
        });
        let Some(Value::Array(items)) = body else {
            return Ok(());
        };
        let pid = event.pid.unwrap_or(0);
        let comm = event.comm.as_deref().unwrap_or_default();
        for (idx, item) in items.iter().enumerate() {
            let message = item
                .get("message")
                .and_then(Value::as_str)
                .unwrap_or_default();
            if message == "tengu_api_success" {
                let input = json_i64(item, "input_tokens");
                let output = json_i64(item, "output_tokens");
                let cache = json_i64(item, "cached_input_tokens");
                let total = input + output + cache;
                if total <= 0 {
                    continue;
                }
                let model = item
                    .get("model")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown");
                let llm_call_id = format!("claude-telemetry-{}-{idx}", event.event_id);
                let usage = observed_token_usage(input, output, cache, total);
                self.emit_token_usage(token_usage_row(
                    &format!("token-{llm_call_id}"),
                    &llm_call_id,
                    event.timestamp_ms,
                    pid,
                    Some(comm),
                    Some("anthropic"),
                    Some(model),
                    &usage,
                    "claude_telemetry",
                    0.80,
                ))?;
            } else if message == "tengu_tool_use_success" {
                let tool_name = item.get("tool_name").and_then(Value::as_str).unwrap_or("?");
                let duration_ms = item
                    .get("duration_ms")
                    .and_then(Value::as_i64)
                    .map(|v| v as u64);
                let request_id = item.get("request_id").and_then(Value::as_str);
                self.emit_tool_call(ToolCallRow {
                    id: format!("claude-tool-telemetry-{}-{idx}", event.event_id),
                    session_id: None,
                    conversation_id: None,
                    timestamp_ms: event.timestamp_ms,
                    tool_name: Some(tool_name.to_string()),
                    tool_call_id: request_id.map(str::to_string),
                    start_timestamp_ms: duration_ms.and_then(|d| event.timestamp_ms.checked_sub(d)),
                    end_timestamp_ms: Some(event.timestamp_ms),
                    duration_ms,
                    status: Some("completed".to_string()),
                    input: serde_json::json!({}),
                    output: serde_json::json!({}),
                    related_pid: Some(pid),
                    related_event_id: Some(event.event_id.clone()),
                    view_source: "view".to_string(),
                    confidence: Some(0.75),
                })?;
            }
        }
        Ok(())
    }

    fn ingest_gemini_stdio_stats(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        if !matches!(event.kind, EventKind::StdioMessage | EventKind::StdioRpc) {
            return Ok(());
        }
        let Some(payload) = event.attributes.get("data").and_then(Value::as_str) else {
            return Ok(());
        };
        let Some(obj) = parse_json_str(payload) else {
            return Ok(());
        };
        let Some(models) = obj.pointer("/stats/models").and_then(Value::as_object) else {
            return Ok(());
        };
        let pid = event.pid.unwrap_or(0);
        let comm = event.comm.as_deref().unwrap_or("gemini");
        for (model, stats) in models {
            let tokens = stats.get("tokens").unwrap_or(stats);
            let input = json_i64(tokens, "prompt").max(json_i64(tokens, "input"));
            let output = json_i64(tokens, "candidates")
                + json_i64(tokens, "thoughts")
                + json_i64(tokens, "tool");
            let cache = json_i64(tokens, "cached");
            let total = json_i64(tokens, "total").max(input + output + cache);
            if total <= 0 {
                continue;
            }
            let llm_call_id = format!("gemini-stdout-{}-{}", event.event_id, sanitize_id(model));
            let usage = observed_token_usage(input, output, cache, total);
            self.emit_token_usage(token_usage_row(
                &format!("token-{llm_call_id}"),
                &llm_call_id,
                event.timestamp_ms,
                pid,
                Some(comm),
                Some("gcp.gen_ai"),
                Some(model),
                &usage,
                "gemini_cli_stdout_stats",
                0.85,
            ))?;
        }
        Ok(())
    }

    fn ingest_sse_tools(
        &mut self,
        event: &CanonicalEvent,
        llm_call_id: &str,
        pid: u32,
        confidence: f32,
    ) -> ViewResult<()> {
        let Some(events) = event.attributes.get("sse_events").and_then(Value::as_array) else {
            return Ok(());
        };
        for (idx, sse) in events.iter().enumerate() {
            let Some(block) = sse.pointer("/parsed_data/content_block") else {
                continue;
            };
            if block.get("type").and_then(Value::as_str) != Some("tool_use") {
                continue;
            }
            let name = block.get("name").and_then(Value::as_str).unwrap_or("?");
            let tool_call_id = block.get("id").and_then(Value::as_str);
            let input_json = block.get("input").map(Value::to_string);
            let tool_id = tool_call_id
                .map(str::to_string)
                .unwrap_or_else(|| format!("tool-{idx}"));
            self.emit_tool_call(ToolCallRow {
                id: format!("tool-{llm_call_id}-{tool_id}"),
                session_id: None,
                conversation_id: Some(format!("conv-{llm_call_id}")),
                timestamp_ms: event.timestamp_ms,
                tool_name: Some(name.to_string()),
                tool_call_id: tool_call_id.map(str::to_string),
                start_timestamp_ms: Some(event.timestamp_ms),
                end_timestamp_ms: None,
                duration_ms: None,
                status: Some("observed".to_string()),
                input: parse_optional_json(input_json.as_deref()),
                output: Value::Null,
                related_pid: Some(pid),
                related_event_id: Some(event.event_id.clone()),
                view_source: "view".to_string(),
                confidence: Some(confidence),
            })?;
        }
        Ok(())
    }

    fn ingest_process_audit(&mut self, event: &CanonicalEvent, action: &str) -> ViewResult<()> {
        let target = event.attributes.get("filename").and_then(Value::as_str);
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "process".to_string(),
            pid: event.pid,
            comm: event.comm.clone(),
            subject: event.comm.clone(),
            action: Some(action.to_string()),
            target: target.map(str::to_string),
            status: Some(process_audit_status(action, &event.attributes).to_string()),
            summary: event.summary.clone(),
            details: event.attributes.clone(),
        })?;
        if let Some(row) = self
            .process_node_id(event, action)
            .and_then(|id| process_node_from_event(event, action, id))
        {
            self.emit_process_node(row)?;
        }
        Ok(())
    }

    fn process_node_id(&mut self, event: &CanonicalEvent, action: &str) -> Option<String> {
        let pid = event.pid?;
        match action {
            "exec" => {
                let id = self
                    .active_processes
                    .entry(pid)
                    .or_insert_with(|| format!("process-{pid}-{}", event.timestamp_ms));
                Some(id.clone())
            }
            "exit" => Some(
                self.active_processes
                    .remove(&pid)
                    .unwrap_or_else(|| format!("process-{pid}-{}", event.timestamp_ms)),
            ),
            _ => None,
        }
    }

    fn ingest_file_audit(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        let target = event
            .attributes
            .get("path")
            .or_else(|| event.attributes.get("filepath"))
            .and_then(Value::as_str);
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "file".to_string(),
            pid: event.pid,
            comm: event.comm.clone(),
            subject: event.comm.clone(),
            action: Some("write".to_string()),
            target: target.map(str::to_string),
            status: Some("observed".to_string()),
            summary: event.summary.clone(),
            details: event.attributes.clone(),
        })
    }

    fn ingest_network_audit(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        let target = event
            .attributes
            .get("detail")
            .or_else(|| event.attributes.get("host"))
            .and_then(Value::as_str);
        let action = process_network_action(&event.attributes).unwrap_or("network");
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "network".to_string(),
            pid: event.pid,
            comm: event.comm.clone(),
            subject: event.comm.clone(),
            action: Some(action.to_string()),
            target: target.map(str::to_string),
            status: Some("observed".to_string()),
            summary: event.summary.clone(),
            details: event.attributes.clone(),
        })
    }
}

#[allow(clippy::too_many_arguments)]
fn emit_llm_audit(
    view: &mut MaterializedView,
    llm_call_id: &str,
    timestamp_ms: u64,
    pid: u32,
    comm: &str,
    subject: Option<&str>,
    action: &str,
    target: Option<&str>,
    status: &str,
    summary: &str,
    details: Option<&Value>,
) -> ViewResult<()> {
    view.emit_audit_event(AuditEventRow {
        id: format!("audit-{llm_call_id}-{action}"),
        timestamp_ms,
        audit_type: "llm".to_string(),
        pid: Some(pid),
        comm: Some(comm.to_string()),
        subject: subject.map(str::to_string),
        action: Some(action.to_string()),
        target: target.map(str::to_string),
        status: Some(status.to_string()),
        summary: Some(summary.to_string()),
        details: details.cloned().unwrap_or_else(|| serde_json::json!({})),
    })
}

#[allow(clippy::too_many_arguments)]
fn token_usage_row(
    id: &str,
    llm_call_id: &str,
    timestamp_ms: u64,
    pid: u32,
    comm: Option<&str>,
    provider: Option<&str>,
    model: Option<&str>,
    usage: &TokenUsage,
    source: &str,
    confidence: f32,
) -> TokenUsageRow {
    TokenUsageRow {
        id: id.to_string(),
        llm_call_id: llm_call_id.to_string(),
        timestamp_ms,
        pid: Some(pid),
        comm: comm.map(str::to_string),
        provider: provider.map(str::to_string),
        model: model.map(str::to_string),
        input_tokens: usage.input_tokens,
        output_tokens: usage.output_tokens,
        cache_creation_tokens: usage.cache_creation_tokens,
        cache_read_tokens: usage.cache_read_tokens,
        total_tokens: usage.total_tokens(),
        source: source.to_string(),
        view_source: "view".to_string(),
        confidence: Some(confidence),
    }
}

fn observed_token_usage(input: i64, output: i64, cache_read: i64, total: i64) -> TokenUsage {
    TokenUsage {
        input_tokens: input,
        output_tokens: output,
        cache_read_tokens: cache_read,
        total_override: Some(total),
        ..Default::default()
    }
}

fn response_body_json(event: &CanonicalEvent) -> Option<Value> {
    body_json(&event.attributes)
        .or_else(|| (event.source == "sse_processor").then(|| event.attributes.clone()))
}

fn process_audit_status(action: &str, attributes: &Value) -> &'static str {
    if action != "exit" {
        return "observed";
    }
    match attributes.get("exit_code").and_then(Value::as_i64) {
        Some(0) => "success",
        Some(_) => "failure",
        None => "observed",
    }
}

fn process_node_from_event(
    event: &CanonicalEvent,
    action: &str,
    id: String,
) -> Option<ProcessNodeRow> {
    let pid = event.pid?;
    let status = process_audit_status(action, &event.attributes).to_string();
    let argv = process_argv(&event.attributes);
    Some(ProcessNodeRow {
        id,
        pid,
        ppid: event.ppid,
        root_pid: None,
        start_timestamp_ms: (action == "exec").then_some(event.timestamp_ms),
        end_timestamp_ms: (action == "exit").then_some(event.timestamp_ms),
        comm: event.comm.clone(),
        command: process_command(&event.attributes, &argv),
        argv,
        cwd: event
            .attributes
            .get("cwd")
            .and_then(Value::as_str)
            .map(str::to_string),
        exit_code: (action == "exit")
            .then(|| event.attributes.get("exit_code").and_then(Value::as_i64))
            .flatten()
            .map(|value| value as i32),
        status: Some(status),
        view_source: "view".to_string(),
        confidence: event.confidence,
    })
}

fn process_command(attributes: &Value, argv: &[String]) -> Option<String> {
    attributes
        .get("filename")
        .and_then(Value::as_str)
        .or_else(|| attributes.get("command").and_then(Value::as_str))
        .map(str::to_string)
        .or_else(|| argv.first().cloned())
}

fn process_argv(attributes: &Value) -> Vec<String> {
    attributes
        .get("argv")
        .and_then(Value::as_array)
        .map(|argv| {
            argv.iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

fn is_writable_open(event: &CanonicalEvent) -> bool {
    let flags = event
        .attributes
        .get("flags")
        .and_then(Value::as_i64)
        .unwrap_or(0);
    const O_ACCMODE: i64 = 0o3;
    const O_CREAT: i64 = 0o100;
    const O_TRUNC: i64 = 0o1000;
    const O_APPEND: i64 = 0o2000;
    (flags & O_ACCMODE) != 0 || (flags & (O_CREAT | O_TRUNC | O_APPEND)) != 0
}

fn is_process_summary_write_event(event: &CanonicalEvent) -> bool {
    event.source == "process"
        && process_event_name(&event.attributes) == Some("SUMMARY")
        && event.attributes.get("type").and_then(Value::as_str) == Some("WRITE")
}

fn is_process_network_event(event: &CanonicalEvent) -> bool {
    event.source == "process"
        && process_network_action(&event.attributes).is_some_and(|name| name.starts_with("NET_"))
}

fn process_event_name(attributes: &Value) -> Option<&str> {
    attributes.get("event").and_then(Value::as_str)
}

fn process_network_action(attributes: &Value) -> Option<&str> {
    let event = process_event_name(attributes)?;
    if event == "SUMMARY" {
        attributes.get("type").and_then(Value::as_str)
    } else {
        Some(event)
    }
}

fn parse_json_str(text: &str) -> Option<Value> {
    serde_json::from_str(text).ok()
}

fn number_or_string(value: Option<&Value>) -> Option<f64> {
    value.and_then(|v| {
        v.as_f64()
            .or_else(|| v.as_str().and_then(|s| s.parse::<f64>().ok()))
    })
}

fn network_target_from_event(event: &CanonicalEvent) -> Option<NetworkTargetRow> {
    let host = event.host.as_deref().filter(|host| !host.is_empty())?;
    let path = event.path.as_deref().filter(|path| !path.is_empty());
    let error_count = i64::from(
        event.kind == EventKind::LlmError
            || event.status_code.map(|code| code >= 400).unwrap_or(false),
    );
    Some(NetworkTargetRow {
        pid: event.pid,
        comm: event.comm.clone(),
        host: host.to_string(),
        path: path.map(str::to_string),
        count: 1,
        error_count,
        first_timestamp_ms: Some(event.timestamp_ms),
        last_timestamp_ms: Some(event.timestamp_ms),
    })
}

fn resource_sample_from_event(event: &CanonicalEvent) -> Option<ResourceSampleRow> {
    if event.kind != EventKind::ResourceSample {
        return None;
    }
    let cpu = number_or_string(event.attributes.get("cpu").and_then(|v| v.get("percent")));
    let rss_mb = number_or_string(event.attributes.get("memory").and_then(|v| v.get("rss_mb")));
    Some(ResourceSampleRow {
        timestamp_ms: event.timestamp_ms,
        pid: event.pid,
        comm: event.comm.clone(),
        cpu_percent: cpu,
        rss_mb: rss_mb.map(|v| v.max(0.0) as i64),
    })
}

#[allow(clippy::too_many_arguments)]
fn llm_call_row(
    id: &str,
    start_timestamp_ms: u64,
    end_timestamp_ms: Option<u64>,
    pid: u32,
    comm: &str,
    provider: Option<&str>,
    model: Option<&str>,
    host: Option<&str>,
    path: Option<&str>,
    status_code: Option<u16>,
    request_body: Option<&Value>,
    response_body: Option<&Value>,
) -> LlmCallRow {
    LlmCallRow {
        id: id.to_string(),
        start_timestamp_ms,
        end_timestamp_ms,
        pid: Some(pid),
        comm: Some(comm.to_string()),
        provider: provider.map(str::to_string),
        model: model.map(str::to_string),
        host: host.map(str::to_string),
        path: path.map(str::to_string),
        status_code,
        input_tokens: 0,
        output_tokens: 0,
        total_tokens: 0,
        request: request_body.cloned().unwrap_or(Value::Null),
        response: response_body.cloned().unwrap_or(Value::Null),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn process_node_id(
        view: &mut MaterializedView,
        timestamp: u64,
        event: &str,
        exit_code: Option<i32>,
    ) -> String {
        let mut data = json!({"event": event, "filename": format!("cmd-{timestamp}")});
        if let Some(code) = exit_code {
            data["exit_code"] = json!(code);
        }
        let event = Event::new_with_timestamp(
            timestamp,
            "process".to_string(),
            42,
            "cmd".to_string(),
            data,
        );
        view.ingest_event(&event).expect("ingest process event");
        view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 100 })
            .process_nodes
            .into_iter()
            .find(|row| {
                row.command.as_deref() == Some(&format!("cmd-{timestamp}"))
                    || row.end_timestamp_ms == Some(timestamp)
            })
            .map(|row| row.id)
            .expect("process node update")
    }

    #[test]
    fn process_node_id_survives_pid_reuse() {
        let mut view = MaterializedView::new();
        let first_exec = process_node_id(&mut view, 1_000, "EXEC", None);
        let second_execve = process_node_id(&mut view, 1_500, "EXEC", None);
        let first_exit = process_node_id(&mut view, 2_000, "EXIT", Some(0));
        let second_exec = process_node_id(&mut view, 3_000, "EXEC", None);
        let second_exit = process_node_id(&mut view, 4_000, "EXIT", Some(1));

        assert_eq!(first_exec, second_execve);
        assert_eq!(first_exec, first_exit);
        assert_eq!(second_exec, second_exit);
        assert_ne!(first_exec, second_exec);
    }

    #[test]
    fn llm_request_audit_survives_response_pairing() {
        let mut view = MaterializedView::new();
        let req = Event::new_with_timestamp(
            1_000,
            "http_parser".to_string(),
            42,
            "agent".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"model\":\"claude-sonnet\"}"
            }),
        );
        let resp = Event::new_with_timestamp(
            2_000,
            "http_parser".to_string(),
            42,
            "agent".to_string(),
            json!({
                "tid": 7,
                "message_type": "response",
                "status_code": 200,
                "headers": { "host": "api.anthropic.com" },
                "body": "{\"usage\":{\"input_tokens\":1,\"output_tokens\":2}}"
            }),
        );

        view.ingest_event(&req).expect("ingest request");
        view.ingest_event(&resp).expect("ingest response");

        let snapshot = view.export_snapshot(crate::model::SnapshotOptions { audit_limit: 100 });
        let llm_actions = snapshot
            .audit_events
            .iter()
            .filter(|row| row.audit_type == "llm")
            .filter_map(|row| row.action.as_deref())
            .collect::<Vec<_>>();
        assert!(llm_actions.contains(&"request"));
        assert!(llm_actions.contains(&"call"));
    }
}
