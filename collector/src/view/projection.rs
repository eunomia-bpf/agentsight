// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Projection: folds typed [`SemanticEvent`]s into view rows. This module
//! performs matching and aggregation only — all payload parsing happens
//! once, in [`crate::decode`].

use crate::decode::decode_event;
use crate::event::Event;
use crate::json::parse_optional_value as parse_optional_json;
use crate::model::{
    AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow, ResourceSampleRow, TokenUsageRow,
    ToolCallRow, ViewResult,
};
use crate::semantic::{
    HttpInfo, LlmRequest, LlmResponse, ProcessInfo, SemanticBody, SemanticEvent, TokenUsage,
};
use crate::text::sanitize_ascii_identifier as sanitize_id;
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
        let semantic = decode_event(event, raw_id);
        self.prune_pending(semantic.timestamp_ms);
        if let Some(sample) = resource_sample_row(&semantic) {
            self.emit_resource_sample(sample)?;
        }
        if let Some(target) = network_target_row(&semantic) {
            self.emit_network_target(target)?;
        }
        self.ingest(&semantic)
    }

    fn ingest(&mut self, event: &SemanticEvent) -> ViewResult<()> {
        self.ingest_observations(event)?;
        match &event.body {
            SemanticBody::LlmRequest(req) => self.ingest_llm_request(event, req),
            SemanticBody::LlmResponse(resp) => self.ingest_llm_response(event, resp),
            SemanticBody::ProcessExec(info) => self.ingest_process_audit(event, info, "exec"),
            SemanticBody::ProcessExit(info) => self.ingest_process_audit(event, info, "exit"),
            SemanticBody::FileWrite(write) => self.ingest_file_audit(event, write.path.as_deref()),
            SemanticBody::NetworkOp(op) => self.ingest_network_audit(event, &op.action, op.target.as_deref()),
            _ => Ok(()),
        }
    }

    fn ingest_llm_request(&mut self, event: &SemanticEvent, req: &LlmRequest) -> ViewResult<()> {
        let Some(tid) = event.tid else {
            return Ok(());
        };
        let pending = PendingRequest {
            event_id: event.event_id.clone(),
            timestamp_ms: event.timestamp_ms,
            pid: event.pid,
            comm: event.comm.clone(),
            provider: req.provider.clone(),
            model: req.model.clone(),
            host: req.host.clone(),
            path: req.path.clone(),
            request_id: req.request_id.clone(),
            body_json: req.body.clone(),
        };
        self.insert_orphan_llm_request(&pending)?;
        let requests = self.pending.entry((event.pid, tid)).or_default();
        requests.push_back(pending);
        while requests.len() > MAX_PENDING_REQUESTS_PER_STREAM {
            requests.pop_front();
        }
        Ok(())
    }

    fn ingest_llm_response(&mut self, event: &SemanticEvent, resp: &LlmResponse) -> ViewResult<()> {
        if let Some(tid) = event.tid
            && let Some((req, confidence)) = self.take_matching_request(event.pid, tid, resp)
        {
            return self.upsert_llm_pair(req, event, resp, confidence);
        }
        self.insert_orphan_llm_response(event, resp)
    }

    fn take_matching_request(
        &mut self,
        pid: u32,
        tid: u64,
        resp: &LlmResponse,
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
            return None;
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
        event: &SemanticEvent,
        resp: &LlmResponse,
        confidence: f32,
    ) -> ViewResult<()> {
        let model = req
            .model
            .clone()
            .or_else(|| resp.model.clone())
            .unwrap_or_else(|| "unknown".to_string());
        let provider = req.provider.clone();
        let llm_call_id = format!("llm-{}", req.event_id);
        let mut call_row = llm_call_row(
            &llm_call_id,
            req.timestamp_ms,
            Some(event.timestamp_ms),
            req.pid,
            &req.comm,
            provider.as_deref(),
            Some(&model),
            req.host.as_deref(),
            req.path.as_deref(),
            resp.status_code,
            req.body_json.as_ref(),
            resp.body.as_ref(),
        );
        if let Some(usage) = self.ingest_response_usage_and_tools(
            event,
            resp,
            &llm_call_id,
            req.pid,
            &req.comm,
            provider.as_deref(),
            &model,
            confidence,
        )? {
            call_row.input_tokens = usage.input_tokens;
            call_row.output_tokens = usage.output_tokens;
            call_row.total_tokens = usage.total_tokens;
        }
        emit_llm_audit(
            self,
            &llm_call_id,
            event.timestamp_ms,
            req.pid,
            &req.comm,
            Some(&model),
            "call",
            req.host.as_deref(),
            if resp.is_error { "failure" } else { "success" },
            "LLM call",
            resp.body.as_ref(),
        )?;
        self.emit_llm_call(call_row)
    }

    fn insert_orphan_llm_request(&mut self, req: &PendingRequest) -> ViewResult<()> {
        let llm_call_id = format!("llm-{}", req.event_id);
        let call_row = llm_call_row(
            &llm_call_id,
            req.timestamp_ms,
            None,
            req.pid,
            &req.comm,
            req.provider.as_deref(),
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

    fn insert_orphan_llm_response(
        &mut self,
        event: &SemanticEvent,
        resp: &LlmResponse,
    ) -> ViewResult<()> {
        let model = resp.model.clone().unwrap_or_else(|| "unknown".to_string());
        let llm_call_id = format!("llm-orphan-{}", event.event_id);
        let mut call_row = llm_call_row(
            &llm_call_id,
            event.timestamp_ms,
            Some(event.timestamp_ms),
            event.pid,
            &event.comm,
            resp.provider.as_deref(),
            Some(&model),
            resp.host.as_deref(),
            resp.path.as_deref(),
            resp.status_code,
            None,
            resp.body.as_ref(),
        );
        if let Some(usage) = self.ingest_response_usage_and_tools(
            event,
            resp,
            &llm_call_id,
            event.pid,
            &event.comm,
            resp.provider.as_deref(),
            &model,
            0.35,
        )? {
            call_row.input_tokens = usage.input_tokens;
            call_row.output_tokens = usage.output_tokens;
            call_row.total_tokens = usage.total_tokens;
        }
        emit_llm_audit(
            self,
            &llm_call_id,
            event.timestamp_ms,
            event.pid,
            &event.comm,
            Some(&model),
            "response",
            resp.host.as_deref(),
            "orphan_response",
            "LLM response",
            resp.body.as_ref(),
        )?;
        self.emit_llm_call(call_row)
    }

    #[allow(clippy::too_many_arguments)]
    fn ingest_response_usage_and_tools(
        &mut self,
        event: &SemanticEvent,
        resp: &LlmResponse,
        llm_call_id: &str,
        pid: u32,
        comm: &str,
        provider: Option<&str>,
        model: &str,
        confidence: f32,
    ) -> ViewResult<Option<TokenUsageRow>> {
        let mut usage_row = None;
        if !resp.usage.is_empty() {
            let token_id = format!("token-{llm_call_id}");
            let row = token_usage_row(
                &token_id,
                llm_call_id,
                event.timestamp_ms,
                pid,
                Some(comm),
                provider,
                Some(model),
                &resp.usage,
                "response_usage",
                confidence,
            );
            self.emit_token_usage(row.clone())?;
            usage_row = Some(row);
        }
        for tool_use in &resp.tool_uses {
            let tool_id = tool_use
                .tool_call_id
                .clone()
                .unwrap_or_else(|| format!("tool-{}", tool_use.index));
            self.emit_tool_call(ToolCallRow {
                id: format!("tool-{llm_call_id}-{tool_id}"),
                session_id: None,
                conversation_id: Some(format!("conv-{llm_call_id}")),
                timestamp_ms: event.timestamp_ms,
                tool_name: Some(tool_use.name.clone()),
                tool_call_id: tool_use.tool_call_id.clone(),
                start_timestamp_ms: Some(event.timestamp_ms),
                end_timestamp_ms: None,
                duration_ms: None,
                status: Some("observed".to_string()),
                input: parse_optional_json(tool_use.input_json.as_deref()),
                output: Value::Null,
                related_pid: Some(pid),
                related_event_id: Some(event.event_id.clone()),
                view_source: "view".to_string(),
                confidence: Some(confidence),
            })?;
        }
        Ok(usage_row)
    }

    /// Agent-reported telemetry (decoded once in `crate::decode`) becomes
    /// token usage and tool call rows independent of captured HTTP pairs.
    fn ingest_observations(&mut self, event: &SemanticEvent) -> ViewResult<()> {
        for observed in &event.observations.token_usage {
            self.emit_token_usage(token_usage_row(
                &format!("token-{}", observed.llm_call_id),
                &observed.llm_call_id,
                event.timestamp_ms,
                event.pid,
                Some(&event.comm),
                Some(observed.provider),
                Some(&observed.model),
                &observed.usage,
                observed.source,
                observed.confidence,
            ))?;
        }
        for observed in &event.observations.tool_calls {
            self.emit_tool_call(ToolCallRow {
                id: observed.id.clone(),
                session_id: None,
                conversation_id: None,
                timestamp_ms: event.timestamp_ms,
                tool_name: Some(observed.tool_name.clone()),
                tool_call_id: observed.tool_call_id.clone(),
                start_timestamp_ms: observed
                    .duration_ms
                    .and_then(|d| event.timestamp_ms.checked_sub(d)),
                end_timestamp_ms: Some(event.timestamp_ms),
                duration_ms: observed.duration_ms,
                status: Some("completed".to_string()),
                input: serde_json::json!({}),
                output: serde_json::json!({}),
                related_pid: Some(event.pid),
                related_event_id: Some(event.event_id.clone()),
                view_source: "view".to_string(),
                confidence: Some(observed.confidence),
            })?;
        }
        Ok(())
    }

    fn ingest_process_audit(
        &mut self,
        event: &SemanticEvent,
        info: &ProcessInfo,
        action: &str,
    ) -> ViewResult<()> {
        let status = process_audit_status(action, info);
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "process".to_string(),
            pid: Some(event.pid),
            comm: Some(event.comm.clone()),
            subject: Some(event.comm.clone()),
            action: Some(action.to_string()),
            target: info.filename.clone(),
            status: Some(status.to_string()),
            summary: event.summary.clone(),
            details: event.raw.clone(),
        })?;
        if let Some(id) = self.process_node_id(event.pid, event.timestamp_ms, action) {
            self.emit_process_node(process_node_row(event, info, action, id, status))?;
        }
        Ok(())
    }

    fn process_node_id(&mut self, pid: u32, timestamp_ms: u64, action: &str) -> Option<String> {
        match action {
            "exec" => {
                let id = self
                    .active_processes
                    .entry(pid)
                    .or_insert_with(|| format!("process-{pid}-{}", timestamp_ms));
                Some(id.clone())
            }
            "exit" => Some(
                self.active_processes
                    .remove(&pid)
                    .unwrap_or_else(|| format!("process-{pid}-{}", timestamp_ms)),
            ),
            _ => None,
        }
    }

    fn ingest_file_audit(&mut self, event: &SemanticEvent, path: Option<&str>) -> ViewResult<()> {
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "file".to_string(),
            pid: Some(event.pid),
            comm: Some(event.comm.clone()),
            subject: Some(event.comm.clone()),
            action: Some("write".to_string()),
            target: path.map(str::to_string),
            status: Some("observed".to_string()),
            summary: event.summary.clone(),
            details: event.raw.clone(),
        })
    }

    fn ingest_network_audit(
        &mut self,
        event: &SemanticEvent,
        action: &str,
        target: Option<&str>,
    ) -> ViewResult<()> {
        self.emit_audit_event(AuditEventRow {
            id: format!("audit-{}", event.event_id),
            timestamp_ms: event.timestamp_ms,
            audit_type: "network".to_string(),
            pid: Some(event.pid),
            comm: Some(event.comm.clone()),
            subject: Some(event.comm.clone()),
            action: Some(action.to_string()),
            target: target.map(str::to_string),
            status: Some("observed".to_string()),
            summary: event.summary.clone(),
            details: event.raw.clone(),
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

fn process_audit_status(action: &str, info: &ProcessInfo) -> &'static str {
    if action != "exit" {
        return "observed";
    }
    match info.exit_code {
        Some(0) => "success",
        Some(_) => "failure",
        None => "observed",
    }
}

fn process_node_row(
    event: &SemanticEvent,
    info: &ProcessInfo,
    action: &str,
    id: String,
    status: &str,
) -> ProcessNodeRow {
    ProcessNodeRow {
        id,
        pid: event.pid,
        ppid: event.ppid,
        root_pid: None,
        start_timestamp_ms: (action == "exec").then_some(event.timestamp_ms),
        end_timestamp_ms: (action == "exit").then_some(event.timestamp_ms),
        comm: Some(event.comm.clone()),
        command: info.command.clone(),
        argv: info.argv.clone(),
        cwd: info.cwd.clone(),
        exit_code: (action == "exit")
            .then_some(info.exit_code)
            .flatten()
            .map(|value| value as i32),
        status: Some(status.to_string()),
        view_source: "view".to_string(),
        confidence: Some(0.75),
    }
}

type HttpTarget<'a> = (&'a Option<String>, &'a Option<String>, Option<u16>, bool);

fn http_info(body: &SemanticBody) -> Option<HttpTarget<'_>> {
    match body {
        SemanticBody::LlmRequest(req) => Some((&req.host, &req.path, None, false)),
        SemanticBody::LlmResponse(resp) => {
            Some((&resp.host, &resp.path, resp.status_code, resp.is_error))
        }
        SemanticBody::HttpRequest(HttpInfo {
            host,
            path,
            status_code,
        })
        | SemanticBody::HttpResponse(HttpInfo {
            host,
            path,
            status_code,
        }) => Some((host, path, *status_code, false)),
        _ => None,
    }
}

fn network_target_row(event: &SemanticEvent) -> Option<NetworkTargetRow> {
    let (host, path, status_code, is_error) = http_info(&event.body)?;
    let host = host.as_deref().filter(|host| !host.is_empty())?;
    let path = path.as_deref().filter(|path| !path.is_empty());
    let error_count = i64::from(is_error || status_code.map(|code| code >= 400).unwrap_or(false));
    Some(NetworkTargetRow {
        pid: Some(event.pid),
        comm: Some(event.comm.clone()),
        host: host.to_string(),
        path: path.map(str::to_string),
        count: 1,
        error_count,
        first_timestamp_ms: Some(event.timestamp_ms),
        last_timestamp_ms: Some(event.timestamp_ms),
    })
}

fn resource_sample_row(event: &SemanticEvent) -> Option<ResourceSampleRow> {
    let SemanticBody::ResourceSample(sample) = &event.body else {
        return None;
    };
    Some(ResourceSampleRow {
        timestamp_ms: event.timestamp_ms,
        pid: Some(event.pid),
        comm: Some(event.comm.clone()),
        cpu_percent: sample.cpu_percent,
        rss_mb: sample.rss_mb.map(|v| v.max(0.0) as i64),
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
