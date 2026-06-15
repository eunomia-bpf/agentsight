// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{AGENT_NATIVE_SOURCE, AuditEventRow, LlmCallRow, SnapshotOptions, TokenSummary};
use crate::output::{
    FileAccessSummary, PromptReportRow, SessionSummary, SummaryStats, print_audit_rows,
    print_exported_snapshot, print_json, print_prompt_report_rows, print_session_summary,
    print_token_summary, prompt_text_chars, sorted_top_counts,
};
use crate::sources::agent_native as agent_native_sessions;
use crate::sources::sqlite::{
    load_view as load_sqlite_view, load_view_with_observed_session_prompts,
    persist_observed_agent_envelopes,
};
use crate::text::{clean_prompt_text, extract_prompt_text};
use crate::view::MaterializedView;

#[cfg(test)]
use crate::sinks::sqlite::SqliteStore;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;

pub(crate) fn configured_db_path(cli_value: &Option<String>) -> Option<String> {
    cli_value
        .clone()
        .or_else(|| std::env::var("AGENTSIGHT_DB_PATH").ok())
}

pub(crate) fn load_agentsight_view(
    db: Option<&str>,
) -> Result<MaterializedView, Box<dyn std::error::Error + Send + Sync>> {
    match db {
        Some(db) => load_sqlite_view(db),
        None => {
            let mut view = MaterializedView::new();
            view.set_source(AGENT_NATIVE_SOURCE);
            agent_native_sessions::import_recent(&mut view, 25);
            Ok(view)
        }
    }
}

pub(crate) fn run_token_query(
    db: &str,
    group_by: &str,
    json: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = load_agentsight_view(Some(db))?;
    let rows = view.token_summary(group_by);
    if json {
        print_json(&rows)?;
    } else {
        print_token_summary(group_by, &rows);
    }
    Ok(())
}

pub(crate) fn run_audit_query(
    db: &str,
    audit_type: Option<&str>,
    limit: usize,
    json: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = load_agentsight_view(Some(db))?;
    let rows = view.audit_rows(audit_type, limit);
    if json {
        print_json(&rows)?;
    } else {
        print_audit_rows(&rows);
    }
    Ok(())
}

pub(crate) fn run_prompts_query(
    db: &str,
    limit: usize,
    json: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = load_view_with_observed_session_prompts(db)?;
    let rows = prompt_report_rows(&view, limit);
    if json {
        print_json(&rows)?;
    } else {
        print_prompt_report_rows(&rows);
    }
    Ok(())
}

pub(crate) fn run_export(
    db: &str,
    output: &str,
    audit_limit: usize,
    observed_projection: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = if observed_projection {
        load_view_with_observed_session_prompts(db)?
    } else {
        load_sqlite_view(db)?
    };
    let snapshot = view.export_snapshot(SnapshotOptions { audit_limit });
    let json = serde_json::to_vec_pretty(&snapshot)?;
    if output == "-" {
        let mut stdout = std::io::stdout().lock();
        stdout.write_all(&json)?;
        stdout.write_all(b"\n")?;
    } else {
        std::fs::write(output, json)?;
        print_exported_snapshot(output);
    }
    Ok(())
}

pub(crate) fn run_materialize_observed(
    db: &str,
    json: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let result = persist_observed_agent_envelopes(db)?;
    if json {
        print_json(&result)?;
    } else {
        println!(
            "Materialized observed agent envelopes: {} sessions, {} tool calls from {} local prompt rows into {}",
            result.sessions_written,
            result.tool_calls_written,
            result.observed_prompt_rows,
            result.db
        );
    }
    Ok(())
}

fn prompt_report_rows(view: &MaterializedView, limit: usize) -> Vec<PromptReportRow> {
    let limit = limit.clamp(1, 10_000);
    let mut rows = Vec::new();
    let mut seen = BTreeSet::new();

    for row in view.llm_call_rows(10_000) {
        if is_noise_llm_call(&row) {
            continue;
        }
        let Some(prompt) = extract_prompt_text(&row.request) else {
            continue;
        };
        if !seen.insert(prompt_key(row.model.as_deref(), &prompt)) {
            continue;
        }
        rows.push(PromptReportRow {
            timestamp_ms: row.start_timestamp_ms,
            comm: row.comm.clone(),
            model: row.model.clone(),
            tokens: row.total_tokens,
            source: "http".to_string(),
            prompt,
            request: row.request.clone(),
            response: row.response.clone(),
        });
    }

    let model_tokens = single_call_model_tokens(view);
    for row in local_prompt_audit_rows(view) {
        let Some(prompt) = prompt_text_from_audit(&row) else {
            continue;
        };
        if !seen.insert(prompt_key(row.subject.as_deref(), &prompt)) {
            continue;
        }
        rows.push(PromptReportRow {
            timestamp_ms: row.timestamp_ms,
            comm: row.comm.clone(),
            model: row.subject.clone(),
            tokens: row
                .subject
                .as_deref()
                .and_then(|model| model_tokens.get(model))
                .copied()
                .unwrap_or(0),
            source: prompt_source(&row).unwrap_or("local").to_string(),
            prompt,
            request: Value::Null,
            response: Value::Null,
        });
    }

    rows.sort_by_key(|row| std::cmp::Reverse(row.timestamp_ms));
    rows.truncate(limit);
    rows
}

fn single_call_model_tokens(view: &MaterializedView) -> BTreeMap<String, i64> {
    view.token_summary("model")
        .into_iter()
        .filter(|row| row.calls == 1 && row.total_tokens > 0)
        .map(|row| (row.group, row.total_tokens))
        .collect()
}

fn local_prompt_audit_rows(view: &MaterializedView) -> Vec<AuditEventRow> {
    view.audit_rows(Some("llm"), 10_000)
        .into_iter()
        .filter(is_local_prompt_audit)
        .filter(|row| !is_noise_prompt_audit(row))
        .collect()
}

fn is_local_prompt_audit(row: &AuditEventRow) -> bool {
    is_prompt_audit(row) && prompt_source(row) == Some("local")
}

fn is_prompt_audit(row: &AuditEventRow) -> bool {
    row.audit_type == "llm"
        && row.action.as_deref() == Some("request")
        && prompt_text_from_audit(row).is_some()
}

fn prompt_source(row: &AuditEventRow) -> Option<&str> {
    row.details.get("prompt_source").and_then(Value::as_str)
}

fn prompt_text_from_audit(row: &AuditEventRow) -> Option<String> {
    row.details
        .get("text_content")
        .and_then(Value::as_str)
        .or_else(|| row.details.get("prompt").and_then(Value::as_str))
        .or(row.summary.as_deref())
        .and_then(clean_prompt_text)
}

fn prompt_key(model: Option<&str>, prompt: &str) -> (String, String) {
    (
        model.unwrap_or_default().to_ascii_lowercase(),
        prompt.to_ascii_lowercase(),
    )
}

fn is_noise_llm_call(row: &LlmCallRow) -> bool {
    if row.total_tokens > 0 {
        return false;
    }
    let Some(prompt) = extract_prompt_text(&row.request) else {
        return false;
    };
    let is_quota_prompt = prompt.trim().eq_ignore_ascii_case("quota");
    let max_tokens_one = row
        .request
        .get("max_tokens")
        .and_then(Value::as_i64)
        .is_some_and(|value| value <= 1);
    is_quota_prompt && max_tokens_one
}

fn is_noise_prompt_audit(row: &AuditEventRow) -> bool {
    let Some(prompt) = prompt_text_from_audit(row) else {
        return false;
    };
    if !prompt.trim().eq_ignore_ascii_case("quota") {
        return false;
    }
    let request = row.details.get("request").unwrap_or(&row.details);
    request
        .get("max_tokens")
        .and_then(Value::as_i64)
        .is_some_and(|value| value <= 1)
}

impl SessionSummary {
    pub(crate) fn from_view(
        view: &MaterializedView,
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let snap = view.export_snapshot(SnapshotOptions {
            audit_limit: 50_000,
        });
        let s = &snap.summary;
        let llm_rows = view
            .llm_call_rows(50_000)
            .into_iter()
            .filter(|row| !is_noise_llm_call(row))
            .collect::<Vec<_>>();
        let token_rows = view.token_usage_rows(50_000);
        let local_prompt_rows = local_prompt_audit_rows(view);
        let first_llm_after_ms = s.start_timestamp_ms.and_then(|start| {
            llm_rows
                .iter()
                .map(|row| row.start_timestamp_ms)
                .chain(token_rows.iter().map(|row| row.timestamp_ms))
                .min()
                .and_then(|ts| ts.checked_sub(start))
        });
        let mut prompt_chars = SummaryStats::default();
        let mut llm_latency_ms = SummaryStats::default();
        for row in &llm_rows {
            if let Some(chars) = prompt_text_chars(&row.request) {
                prompt_chars.add(chars as u64);
            }
            if let Some(delta) = row
                .end_timestamp_ms
                .and_then(|end| end.checked_sub(row.start_timestamp_ms))
            {
                llm_latency_ms.add(delta);
            }
        }
        let mut seen_prompts = llm_rows
            .iter()
            .filter_map(|row| {
                extract_prompt_text(&row.request)
                    .map(|prompt| prompt_key(row.model.as_deref(), &prompt))
            })
            .collect::<BTreeSet<_>>();
        for row in &local_prompt_rows {
            let Some(prompt) = prompt_text_from_audit(row) else {
                continue;
            };
            if seen_prompts.insert(prompt_key(row.subject.as_deref(), &prompt)) {
                prompt_chars.add(prompt.chars().count() as u64);
            }
        }
        let models = token_summary_tuples(&snap.token_summary);
        let mut processes = BTreeMap::new();
        let mut process_exits = BTreeMap::new();
        for row in snap
            .audit_events
            .iter()
            .filter(|row| row.audit_type == "process")
        {
            match row.action.as_deref() {
                Some("exec") => {
                    *processes
                        .entry(row.comm.clone().unwrap_or_default())
                        .or_default() += 1;
                }
                Some("exit") => {
                    let status = row.status.as_deref().unwrap_or("observed").to_string();
                    *process_exits.entry(status).or_default() += 1;
                }
                _ => {}
            }
        }
        let mut seen_files = BTreeSet::new();
        let mut files = Vec::new();
        let mut file_access = FileAccessSummary::default();
        let mut file_dirs = BTreeMap::new();
        for row in &snap.audit_events {
            if row.audit_type != "file" {
                continue;
            }
            file_access.events += 1;
            let action = row.action.as_deref().unwrap_or("observed").to_string();
            *file_access.actions.entry(action).or_default() += 1;
            if let Some(delta) = after_start(s.start_timestamp_ms, row.timestamp_ms) {
                file_access.first_after_ms = Some(
                    file_access
                        .first_after_ms
                        .map_or(delta, |current| current.min(delta)),
                );
                file_access.last_after_ms = Some(
                    file_access
                        .last_after_ms
                        .map_or(delta, |current| current.max(delta)),
                );
            }
            if let Some(target) = row.target.as_ref() {
                if seen_files.insert(target.clone()) {
                    files.push(target.clone());
                }
                *file_dirs.entry(file_directory(target)).or_default() += 1;
            }
        }
        file_access.directories = sorted_top_counts(file_dirs, 8);

        let mut endpoint_counts = BTreeMap::<String, usize>::new();
        let mut network_events = 0usize;
        for target in &snap.network_targets {
            network_events += target.count.max(0) as usize;
            let endpoint = target
                .path
                .as_ref()
                .filter(|path| !path.is_empty())
                .map(|path| format!("{}{}", target.host, path))
                .unwrap_or_else(|| target.host.clone());
            *endpoint_counts.entry(endpoint).or_default() += target.count.max(0) as usize;
        }
        let endpoints = sorted_top_counts(endpoint_counts, 8)
            .into_iter()
            .map(|(endpoint, count)| format!("{endpoint}({count})"))
            .collect();
        let first_tool_after_ms = snap
            .tool_calls
            .iter()
            .map(|row| row.timestamp_ms)
            .min()
            .and_then(|ts| after_start(s.start_timestamp_ms, ts));
        let mut tool_calls = BTreeMap::new();
        let mut tool_duration_ms = SummaryStats::default();
        for row in &snap.tool_calls {
            *tool_calls
                .entry(row.tool_name.clone().unwrap_or_else(|| "?".to_string()))
                .or_default() += 1;
            if let Some(duration_ms) = row.duration_ms {
                tool_duration_ms.add(duration_ms);
            }
        }
        Ok(Self {
            source: s.source.clone(),
            duration_s: s.duration_s(),
            first_llm_after_ms,
            first_tool_after_ms,
            prompt_chars,
            llm_latency_ms,
            models,
            processes,
            process_exits,
            tool_calls,
            tool_duration_ms,
            files,
            file_access,
            network_events,
            endpoints,
        })
    }
}

fn after_start(start_timestamp_ms: Option<u64>, timestamp_ms: u64) -> Option<u64> {
    start_timestamp_ms.and_then(|start| timestamp_ms.checked_sub(start))
}

fn token_summary_tuples(rows: &[TokenSummary]) -> Vec<(String, i64, i64, i64, i64)> {
    rows.iter()
        .filter(|row| row.input_tokens != 0 || row.output_tokens != 0 || row.total_tokens != 0)
        .map(|row| {
            (
                row.group.clone(),
                row.input_tokens,
                row.output_tokens,
                row.total_tokens,
                row.calls,
            )
        })
        .collect()
}

fn file_directory(path: &str) -> String {
    std::path::Path::new(path)
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .map(|parent| parent.to_string_lossy().to_string())
        .unwrap_or_else(|| ".".to_string())
}

pub(crate) fn run_db_summary(
    db: Option<&str>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = match db {
        Some(db) => load_view_with_observed_session_prompts(db)?,
        None => load_agentsight_view(None)?,
    };
    print_session_summary(&SessionSummary::from_view(&view)?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::Event;
    use serde_json::json;

    fn sqlite_summary(db: &std::path::Path) -> SessionSummary {
        let view = load_sqlite_view(db).unwrap();
        SessionSummary::from_view(&view).unwrap()
    }

    #[test]
    fn sqlite_load_view_does_not_create_missing_db() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("missing.db");

        assert!(load_sqlite_view(&db).is_err());
        assert!(!db.exists());
    }

    #[test]
    fn token_queries_use_highest_priority_source_per_llm_call() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("token-priority.db");
        let store = SqliteStore::open(&db).unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO llm_calls (
                    id, start_timestamp_ms, end_timestamp_ms, pid, comm, model, view_source
                 ) VALUES ('llm-1', 1000, 1200, 42, 'claude', 'claude-sonnet-4', 'view')",
                [],
            )
            .unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO token_usage (
                    id, llm_call_id, timestamp_ms, pid, comm, model,
                    input_tokens, output_tokens, total_tokens, source, confidence
                 ) VALUES
                 ('token-response', 'llm-1', 1200, 42, 'claude', 'claude-sonnet-4',
                    10, 5, 15, 'response_usage', 0.95),
                 ('token-native', 'llm-1', 1201, 42, 'claude', 'claude-sonnet-4',
                    100, 50, 150, 'agent_native_session', 0.80)",
                [],
            )
            .unwrap();

        let view = load_sqlite_view(&db).unwrap();
        let tokens = view.token_summary("model");
        assert_eq!(tokens[0].group, "claude-sonnet-4");
        // agent-native session tokens are preferred over SSL-captured response usage.
        assert_eq!(tokens[0].total_tokens, 150);
        assert_eq!(tokens[0].calls, 1);

        let calls = view.llm_call_rows(10);
        assert_eq!(calls[0].total_tokens, 150);
    }

    #[test]
    fn prompts_hide_quota_probe_when_tokens_come_from_telemetry() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("quota-probe.db");
        let store = SqliteStore::open(&db).unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO llm_calls (
                    id, start_timestamp_ms, pid, comm, provider, model, host, path,
                    request_body_json, response_body_json, view_source, confidence
                 ) VALUES (
                    'llm-quota', 1000, 42, 'HTTP Client', 'anthropic',
                    'claude-haiku-4-5-20251001', 'api.anthropic.com',
                    '/v1/messages?beta=true',
                    '{\"model\":\"claude-haiku-4-5-20251001\",\"max_tokens\":1,\"messages\":[{\"role\":\"user\",\"content\":\"quota\"}]}',
                    'null', 'view', 1.0
                 )",
                [],
            )
            .unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO token_usage (
                    id, llm_call_id, timestamp_ms, pid, comm, provider, model,
                    input_tokens, output_tokens, total_tokens, source
                 ) VALUES (
                    'token-telemetry', 'claude-telemetry-1', 1500, 42,
                    'HTTP Client', 'anthropic', 'claude-opus-4-6',
                    3, 25, 28, 'claude_telemetry'
                 )",
                [],
            )
            .unwrap();

        let view = load_view_with_observed_session_prompts(&db).unwrap();
        assert!(prompt_report_rows(&view, 10).is_empty());

        let summary = SessionSummary::from_view(&view).unwrap();
        assert_eq!(
            summary.models,
            vec![("claude-opus-4-6".to_string(), 3, 25, 28, 1)]
        );
        assert_eq!(summary.first_llm_after_ms, Some(500));
        assert_eq!(summary.prompt_chars.count, 0);
    }

    #[test]
    fn prompts_include_observed_local_session_prompt() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("local-prompt.db");
        let store = SqliteStore::open(&db).unwrap();
        let (_session_temp, session_path) =
            agent_native_sessions::create_temp_session_path("claude");
        std::fs::write(
            &session_path,
            concat!(
                r#"{"type":"user","message":{"role":"user","content":"Run regression test."},"sessionId":"session-1"}"#,
                "\n",
                r#"{"type":"assistant","message":{"model":"claude-opus-4-6","content":[{"type":"text","text":"ok"}],"usage":{"input_tokens":3,"output_tokens":25}},"requestId":"req-1","sessionId":"session-1"}"#,
                "\n",
            ),
        )
        .unwrap();
        let session_path_string = session_path.to_string_lossy().to_string();
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES ('audit-file', 1000, 'file', 42, 'claude', 'write', ?1, 'observed', '{}')",
                [session_path_string.as_str()],
            )
            .unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO token_usage (
                    id, llm_call_id, timestamp_ms, pid, comm, provider, model,
                    input_tokens, output_tokens, total_tokens, source
                 ) VALUES (
                    'token-telemetry', 'claude-telemetry-1', 1300, 42,
                    'HTTP Client', 'anthropic', 'claude-opus-4-6',
                    3, 25, 28, 'claude_telemetry'
                 )",
                [],
            )
            .unwrap();

        let view = load_view_with_observed_session_prompts(&db).unwrap();
        let rows = prompt_report_rows(&view, 10);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].model.as_deref(), Some("claude-opus-4-6"));
        assert_eq!(rows[0].tokens, 28);
        assert_eq!(rows[0].source, "local");
        assert_eq!(rows[0].prompt, "Run regression test.");

        let summary = SessionSummary::from_view(&view).unwrap();
        assert_eq!(summary.prompt_chars.count, 1);
        assert_eq!(
            summary.prompt_chars.total,
            "Run regression test.".chars().count() as u64
        );
    }

    #[test]
    fn sqlite_summary_reports_timeline_prompt_and_access_scope() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("summary.db");
        let mut view = MaterializedView::new();
        view.add_sink(Box::new(SqliteStore::open(&db).unwrap()));

        for event in [
            Event::new_with_timestamp(
                1_000,
                "process".to_string(),
                42,
                "claude".to_string(),
                json!({"event": "EXEC", "filename": "/usr/bin/claude"}),
            ),
            Event::new_with_timestamp(
                1_200,
                "http_parser".to_string(),
                42,
                "claude".to_string(),
                json!({
                    "tid": 7,
                    "message_type": "request",
                    "method": "POST",
                    "path": "/v1/messages",
                    "headers": {"host": "api.anthropic.com"},
                    "body": "{\"model\":\"claude-sonnet-4\",\"messages\":[{\"role\":\"user\",\"content\":\"hello summary\"}]}"
                }),
            ),
            Event::new_with_timestamp(
                1_700,
                "http_parser".to_string(),
                42,
                "claude".to_string(),
                json!({
                    "tid": 7,
                    "message_type": "response",
                    "path": "/v1/messages",
                    "headers": {"host": "api.anthropic.com"},
                    "status_code": 200,
                    "body": "{\"model\":\"claude-sonnet-4\",\"usage\":{\"input_tokens\":10,\"output_tokens\":5}}"
                }),
            ),
            Event::new_with_timestamp(
                1_800,
                "process".to_string(),
                42,
                "claude".to_string(),
                json!({"event": "FILE_WRITE", "path": "/tmp/agentsight-summary/a.txt"}),
            ),
            Event::new_with_timestamp(
                1_900,
                "process".to_string(),
                42,
                "claude".to_string(),
                json!({"event": "FILE_WRITE", "path": "/tmp/agentsight-summary/sub/b.txt"}),
            ),
        ] {
            view.ingest_event(&event).unwrap();
        }

        view.emit_tool_call(crate::model::ToolCallRow {
            id: "tool-1".to_string(),
            session_id: None,
            conversation_id: None,
            timestamp_ms: 1_500,
            tool_name: Some("Bash".to_string()),
            tool_call_id: None,
            start_timestamp_ms: Some(1_500),
            end_timestamp_ms: Some(1_650),
            duration_ms: Some(150),
            status: None,
            input: json!({}),
            output: json!({}),
            related_pid: None,
            related_event_id: None,
            view_source: "claude-code".to_string(),
            confidence: None,
        })
        .unwrap();

        let summary = sqlite_summary(&db);
        assert_eq!(summary.duration_s, 0.9);
        assert_eq!(summary.first_llm_after_ms, Some(200));
        assert_eq!(summary.first_tool_after_ms, Some(500));
        assert_eq!(summary.prompt_chars.count, 1);
        assert_eq!(summary.prompt_chars.total, 13);
        assert_eq!(summary.llm_latency_ms.count, 1);
        assert_eq!(summary.llm_latency_ms.total, 500);
        assert_eq!(summary.tool_calls.get("Bash"), Some(&1));
        assert_eq!(summary.tool_duration_ms.count, 1);
        assert_eq!(summary.tool_duration_ms.total, 150);
        assert_eq!(summary.file_access.events, 2);
        assert_eq!(summary.file_access.actions.get("write"), Some(&2));
        assert_eq!(summary.files.len(), 2);
        assert_eq!(summary.network_events, 2);
        assert!(
            summary
                .endpoints
                .contains(&"api.anthropic.com/v1/messages(2)".to_string())
        );
    }

    #[test]
    fn sqlite_summary_does_not_read_touched_local_claude_log_without_projection() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("local-log.db");
        let session_path =
            agent_session::fixture_session_path(agent_session::AGENT_CLAUDE, temp.path()).unwrap();
        std::fs::create_dir_all(session_path.parent().unwrap()).unwrap();
        std::fs::write(
            &session_path,
            concat!(
                "{\"type\":\"assistant\",\"requestId\":\"req_1\",\"message\":{\"model\":\"claude-opus-4-6\",\"content\":[{\"type\":\"tool_use\",\"name\":\"Bash\"}],\"usage\":{\"input_tokens\":3,\"cache_creation_input_tokens\":5,\"cache_read_input_tokens\":7,\"output_tokens\":11}}}\n",
                "{\"type\":\"result\",\"duration_ms\":1200,\"usage\":{\"input_tokens\":3,\"cache_creation_input_tokens\":5,\"cache_read_input_tokens\":7,\"output_tokens\":11},\"modelUsage\":{\"claude-opus-4-6\":{\"inputTokens\":3,\"outputTokens\":11,\"cacheCreationInputTokens\":5,\"cacheReadInputTokens\":7}}}\n",
            ),
        )
        .unwrap();

        let store = SqliteStore::open(&db).unwrap();
        let session_path_string = session_path.to_string_lossy().to_string();
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES ('audit-1', 1000, 'file', 42, 'claude', 'write', ?1, 'observed', '{}')",
                [session_path_string.as_str()],
            )
            .unwrap();

        let summary = sqlite_summary(&db);
        assert!(summary.models.is_empty());
        assert!(summary.tool_calls.is_empty());

        let token_rows: i64 = store
            .connection()
            .query_row("SELECT COUNT(*) FROM token_usage", [], |row| row.get(0))
            .unwrap();
        assert_eq!(token_rows, 0);
    }

    #[test]
    fn sqlite_summary_uses_db_tokens_without_local_log_overlay() {
        let temp = tempfile::tempdir().unwrap();
        let db = temp.path().join("local-log-no-usage.db");
        let session_path =
            agent_session::fixture_session_path(agent_session::AGENT_CLAUDE, temp.path()).unwrap();
        std::fs::create_dir_all(session_path.parent().unwrap()).unwrap();
        std::fs::write(
            &session_path,
            "{\"type\":\"user\",\"message\":{\"content\":\"local prompt only\"}}\n",
        )
        .unwrap();

        let store = SqliteStore::open(&db).unwrap();
        let session_path_string = session_path.to_string_lossy().to_string();
        store
            .connection()
            .execute(
                "INSERT INTO audit_events (
                    id, timestamp_ms, audit_type, pid, comm, action, target, status, details_json
                 ) VALUES ('audit-1', 1000, 'file', 42, 'claude', 'write', ?1, 'observed', '{}')",
                [session_path_string.as_str()],
            )
            .unwrap();
        store
            .connection()
            .execute(
                "INSERT INTO token_usage (
                    id, timestamp_ms, model, input_tokens, output_tokens, total_tokens, source
                 ) VALUES ('token-1', 1200, 'ssl-model', 8, 5, 13, 'response_usage')",
                [],
            )
            .unwrap();

        let summary = sqlite_summary(&db);
        assert_eq!(summary.models, vec![("ssl-model".to_string(), 8, 5, 13, 1)]);
        assert_eq!(summary.prompt_chars.total, 0);
    }

    #[test]
    fn local_claude_summary_reads_active_message_usage() {
        let temp = tempfile::tempdir().unwrap();
        let path =
            agent_session::fixture_session_path(agent_session::AGENT_CLAUDE, temp.path()).unwrap();
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        let session = agent_native_sessions::parse_content_for_test(
            "claude",
            &path,
            std::time::UNIX_EPOCH,
            concat!(
                "{\"type\":\"assistant\",\"requestId\":\"req_1\",\"message\":{\"model\":\"claude-opus-4-6\",\"content\":[{\"type\":\"tool_use\",\"name\":\"Bash\"}],\"usage\":{\"input_tokens\":3,\"cache_creation_input_tokens\":5,\"cache_read_input_tokens\":7,\"output_tokens\":11}}}\n",
                "{\"type\":\"assistant\",\"requestId\":\"req_1\",\"message\":{\"model\":\"claude-opus-4-6\",\"content\":[{\"type\":\"text\",\"text\":\"done\"}],\"usage\":{\"input_tokens\":3,\"cache_creation_input_tokens\":5,\"cache_read_input_tokens\":7,\"output_tokens\":11}}}\n",
            ),
        )
        .unwrap();
        let view = agent_native_sessions::materialized_view(&[session]);
        let summary = SessionSummary::from_view(&view).unwrap();
        assert_eq!(
            summary.models,
            vec![("claude-opus-4-6".to_string(), 3, 11, 26, 1)]
        );
        assert_eq!(summary.tool_calls.get("Bash"), Some(&1));
    }
}
