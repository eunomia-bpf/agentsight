// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::{AgentSession, TokenUsage};
use serde_json::Value;
use std::cmp::Reverse;
use std::collections::HashSet;
use std::path::{Path, PathBuf};
use std::time::{Duration, UNIX_EPOCH};

#[cfg(test)]
use std::fs;

use crate::model::{
    AGENT_NATIVE_SOURCE, AuditEventRow, LlmCallRow, SessionRow, Snapshot, SnapshotOptions,
    TokenUsageRow, ToolCallRow,
};
use crate::text::{sanitize_ascii_identifier as sanitize_id, truncate_text};
use crate::view::MaterializedView;

pub(crate) type LocalSession = AgentSession;
pub(crate) type SessionCache = agent_session::SessionCache;

pub(crate) fn snapshot(
    cache: &mut SessionCache,
    pid_filter: Option<u32>,
    text_filter: Option<&str>,
    limit: usize,
    max_age: Duration,
) -> Snapshot {
    let filtered: Vec<LocalSession> = cache
        .discover_cached(limit, max_age)
        .into_iter()
        .filter(|s| matches_filter(s, pid_filter, text_filter))
        .collect();
    materialized_view(&filtered).export_snapshot(SnapshotOptions { audit_limit: 0 })
}

fn view_id(session: &LocalSession) -> String {
    format!("local:{}:{}", session.agent_type, session.display_id)
}

pub(crate) fn materialized_view(sessions: &[LocalSession]) -> MaterializedView {
    let mut view = MaterializedView::new();
    view.set_source(AGENT_NATIVE_SOURCE);
    import_into_view(&mut view, sessions);
    view
}

pub(crate) fn import_recent(view: &mut MaterializedView, limit: usize) {
    let sessions = SessionCache::new().discover_cached(limit, Duration::ZERO);
    import_into_view(view, &sessions);
}

pub(crate) fn import_into_view(view: &mut MaterializedView, sessions: &[LocalSession]) {
    for session in sessions {
        view.upsert_session(&session_row(session));
        for row in llm_rows(session) {
            view.apply_llm_call(&row);
        }
        for row in token_rows(session) {
            view.apply_token_usage(&row);
        }
        for row in tool_rows(session) {
            view.apply_tool_call(&row);
        }
    }
}

fn llm_rows(session: &LocalSession) -> Vec<LlmCallRow> {
    let Some(prompt) = session.prompt_preview.as_ref() else {
        return Vec::new();
    };
    let session_id = view_id(session);
    let timestamp_ms = session
        .events
        .prompts
        .first()
        .and_then(|prompt| prompt.ts_ms)
        .and_then(|ts| u64::try_from(ts).ok())
        .or(session.start_timestamp_ms)
        .unwrap_or_else(|| updated_ms(session));
    let request = serde_json::json!({
        "prompt": prompt,
        "prompt_source": AGENT_NATIVE_SOURCE,
        "session_id": session_id,
        "agent_type": session.agent_type.as_str(),
        "path": session.path.to_string_lossy(),
    });

    if session.model_usage.is_empty() {
        let model = session
            .model
            .clone()
            .unwrap_or_else(|| session.agent_type.clone());
        return vec![llm_row_for_session(
            &format!("{session_id}-{}", sanitize_id(&model)),
            session,
            &session_id,
            timestamp_ms,
            Some(model),
            &session.usage,
            request,
        )];
    }

    session
        .model_usage
        .iter()
        .map(|(model, usage)| {
            llm_row_for_session(
                &format!("{session_id}-{model}"),
                session,
                &session_id,
                timestamp_ms,
                Some(model.clone()),
                usage,
                request.clone(),
            )
        })
        .collect()
}

fn llm_row_for_session(
    id: &str,
    session: &LocalSession,
    session_id: &str,
    timestamp_ms: u64,
    model: Option<String>,
    usage: &TokenUsage,
    request: Value,
) -> LlmCallRow {
    LlmCallRow {
        id: id.to_string(),
        session_id: Some(session_id.to_string()),
        conversation_id: session.conversation_id.clone(),
        start_timestamp_ms: timestamp_ms,
        end_timestamp_ms: session.end_timestamp_ms,
        pid: None,
        comm: Some(session.agent_type.clone()),
        provider: None,
        model,
        call_kind: Some("agent_native_prompt".to_string()),
        status: "observed".to_string(),
        error_type: None,
        finish_reason: None,
        host: None,
        path: Some(session.path.to_string_lossy().to_string()),
        status_code: None,
        input_tokens: usage.input_tokens,
        output_tokens: usage.output_tokens,
        total_tokens: usage.total_tokens,
        request,
        response: Value::Null,
    }
}

pub(crate) fn observed_session_prompt_rows(audit_rows: &[AuditEventRow]) -> Vec<AuditEventRow> {
    let mut rows = Vec::new();
    let mut seen = HashSet::new();
    let mut seen_sessions = HashSet::new();
    for row in audit_rows {
        if row.audit_type == "process"
            && row.action.as_deref() == Some("exec")
            && agent_session::is_codex_cli_entrypoint(row.target.as_deref())
        {
            let Some(prompt) = row
                .details
                .get("full_command")
                .and_then(Value::as_str)
                .and_then(agent_session::codex_exec_prompt)
            else {
                continue;
            };
            rows.push(AuditEventRow {
                id: format!(
                    "audit-codex-exec-prompt-{}-{}",
                    row.timestamp_ms,
                    row.pid.unwrap_or(0)
                ),
                timestamp_ms: row.timestamp_ms,
                audit_type: "llm".to_string(),
                pid: row.pid,
                comm: row.comm.clone().or_else(|| Some("codex".to_string())),
                subject: None,
                action: Some("request".to_string()),
                target: row.target.clone(),
                status: Some("observed".to_string()),
                summary: Some(truncate_text(&prompt, 160)),
                details: serde_json::json!({
                    "text_content": prompt,
                    "prompt_source": "local",
                }),
            });
            continue;
        }
        if row.audit_type != "file" {
            continue;
        }
        let Some(pid) = row.pid else {
            continue;
        };
        let Some(path) = audit_session_path(row) else {
            continue;
        };
        if !seen.insert((path.clone(), pid)) {
            continue;
        };
        let Some(session) = agent_session::parse_session_path(&path) else {
            continue;
        };
        let Some(prompt) = session.prompt_preview.as_ref() else {
            continue;
        };
        seen_sessions.insert(view_id(&session));

        rows.push(AuditEventRow {
            id: format!(
                "audit-agent-native-prompt-{}-{pid}",
                sanitize_id(&session.display_id)
            ),
            timestamp_ms: row.timestamp_ms,
            audit_type: "llm".to_string(),
            pid: Some(pid),
            comm: row
                .comm
                .clone()
                .or_else(|| Some(session.agent_type.clone())),
            subject: session.model.clone(),
            action: Some("request".to_string()),
            target: Some(path.to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: Some(truncate_text(prompt, 160)),
            details: serde_json::json!({
                "text_content": prompt,
                "prompt_source": "local",
                "session_id": view_id(&session),
                "conversation_id": session.conversation_id.as_deref(),
                "agent_type": session.agent_type,
            }),
        });
    }
    for session in observed_sessions_from_audit_rows(audit_rows) {
        if !seen_sessions.insert(view_id(&session)) {
            continue;
        }
        let Some(prompt) = session.prompt_preview.as_ref() else {
            continue;
        };
        rows.push(AuditEventRow {
            id: format!(
                "audit-agent-native-prompt-{}-observed",
                sanitize_id(&session.display_id)
            ),
            timestamp_ms: session_prompt_timestamp_ms(&session),
            audit_type: "llm".to_string(),
            pid: None,
            comm: Some(session.agent_type.clone()),
            subject: session.model.clone(),
            action: Some("request".to_string()),
            target: Some(session.path.to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: Some(truncate_text(prompt, 160)),
            details: serde_json::json!({
                "text_content": prompt,
                "prompt_source": "local",
                "session_id": view_id(&session),
                "conversation_id": session.conversation_id.as_deref(),
                "agent_type": session.agent_type,
            }),
        });
    }
    rows
}

pub(crate) fn observed_sessions_from_audit_rows(audit_rows: &[AuditEventRow]) -> Vec<LocalSession> {
    let mut direct_paths = HashSet::new();
    let mut codex_session_dirs = HashSet::new();

    for row in audit_rows.iter().filter(|row| row.audit_type == "file") {
        for path in audit_file_paths(row) {
            if let Some(session_path) =
                agent_session::session_log_path_from_str(path.to_string_lossy().as_ref())
            {
                direct_paths.insert(session_path);
            }
            if let Some(dir) = observed_codex_sessions_dir(&path) {
                codex_session_dirs.insert(dir);
            }
        }
    }

    let mut candidates = Vec::new();
    for path in direct_paths {
        if let Some(candidate) = agent_session::session_candidate_from_path(&path) {
            candidates.push(candidate);
        }
    }
    for dir in codex_session_dirs {
        candidates.extend(agent_session::discover_session_files_in_dir(
            agent_session::AGENT_CODEX,
            &dir,
        ));
    }
    candidates.sort_by_key(|candidate| Reverse(candidate.updated));

    let mut seen_paths = HashSet::new();
    let mut seen_sessions = HashSet::new();
    let mut sessions = Vec::new();
    for candidate in candidates.into_iter().take(75) {
        if !seen_paths.insert(candidate.path.clone()) {
            continue;
        }
        let Some(session) = agent_session::parse_session_file(&candidate) else {
            continue;
        };
        if seen_sessions.insert(session.display_id.clone()) {
            sessions.push(session);
        }
    }
    sessions
}

fn audit_session_path(row: &AuditEventRow) -> Option<PathBuf> {
    row.target
        .as_deref()
        .and_then(agent_session::session_log_path_from_str)
        .or_else(|| {
            row.details
                .get("filepath")
                .and_then(Value::as_str)
                .and_then(agent_session::session_log_path_from_str)
        })
        .or_else(|| {
            row.details
                .get("path")
                .and_then(Value::as_str)
                .and_then(agent_session::session_log_path_from_str)
        })
}

fn audit_file_paths(row: &AuditEventRow) -> Vec<PathBuf> {
    [
        row.target.as_deref(),
        row.details.get("filepath").and_then(Value::as_str),
        row.details.get("path").and_then(Value::as_str),
        row.details.get("fd_target").and_then(Value::as_str),
    ]
    .into_iter()
    .flatten()
    .filter_map(|raw| {
        let path = PathBuf::from(raw.trim().trim_end_matches(" (deleted)"));
        path.is_absolute().then_some(path)
    })
    .collect()
}

fn observed_codex_sessions_dir(path: &Path) -> Option<PathBuf> {
    if !looks_like_codex_home_file(path) {
        return None;
    }
    let home = path.parent()?;
    let sessions = home.join("sessions");
    sessions.is_dir().then_some(sessions)
}

fn looks_like_codex_home_file(path: &Path) -> bool {
    let Some(name) = path.file_name().and_then(|name| name.to_str()) else {
        return false;
    };
    (name.starts_with("state_")
        || name.starts_with("logs_")
        || matches!(name, "config.toml" | "auth.json"))
        && path
            .parent()
            .is_some_and(|parent| parent.join("sessions").is_dir())
}

fn session_prompt_timestamp_ms(session: &LocalSession) -> u64 {
    session
        .events
        .prompts
        .first()
        .and_then(|prompt| prompt.ts_ms)
        .and_then(|ts| u64::try_from(ts).ok())
        .or(session.start_timestamp_ms)
        .unwrap_or_else(|| updated_ms(session))
}

fn session_row(session: &LocalSession) -> SessionRow {
    let updated_ms = updated_ms(session);
    SessionRow {
        id: view_id(session),
        agent_type: session.agent_type.clone(),
        start_timestamp_ms: session
            .start_timestamp_ms
            .unwrap_or_else(|| updated_ms.saturating_sub(session.duration_ms)),
        end_timestamp_ms: session.end_timestamp_ms.or(Some(updated_ms)),
        status: "observed".to_string(),
        model: session.model.clone(),
        input_tokens: session.usage.input_tokens,
        output_tokens: session.usage.output_tokens,
        total_tokens: session.usage.total_tokens,
        view_source: AGENT_NATIVE_SOURCE.to_string(),
        confidence: Some(0.95),
        attributes: serde_json::json!({
            "session_id": session.session_id.clone(),
            "conversation_id": session.conversation_id.as_deref(),
            "path": session.path.to_string_lossy(),
            "display_id": session.display_id,
            "prompt_preview": session.prompt_preview.clone(),
            "cwd": session.cwd.clone(),
            "last_message_at": session.last_message_at.clone(),
            "files": session.files,
        }),
    }
}

fn token_rows(session: &LocalSession) -> Vec<TokenUsageRow> {
    let session_id = view_id(session);
    session
        .model_usage
        .iter()
        .filter(|(_, usage)| usage.total_tokens > 0)
        .map(|(model, usage)| TokenUsageRow {
            id: format!("token-{session_id}-{}", sanitize_id(model)),
            llm_call_id: format!("{session_id}-{model}"),
            timestamp_ms: updated_ms(session),
            pid: None,
            comm: Some(session.agent_type.clone()),
            provider: None,
            model: Some(model.clone()),
            input_tokens: usage.input_tokens,
            output_tokens: usage.output_tokens,
            cache_creation_tokens: usage.cache_creation_tokens,
            cache_read_tokens: usage.cache_read_tokens,
            total_tokens: usage.total_tokens,
            source: AGENT_NATIVE_SOURCE.to_string(),
            view_source: AGENT_NATIVE_SOURCE.to_string(),
            confidence: Some(0.95),
        })
        .collect()
}

fn tool_rows(session: &LocalSession) -> Vec<ToolCallRow> {
    let session_id = view_id(session);
    let timestamp_ms = updated_ms(session);
    let mut rows = Vec::new();
    for (tool, count) in &session.tools {
        for index in 0..*count {
            rows.push(ToolCallRow {
                id: format!("tool-{session_id}-{}-{index}", sanitize_id(tool)),
                session_id: Some(session_id.clone()),
                conversation_id: session.conversation_id.clone(),
                timestamp_ms,
                tool_name: Some(tool.clone()),
                tool_call_id: None,
                start_timestamp_ms: Some(timestamp_ms),
                end_timestamp_ms: Some(timestamp_ms),
                duration_ms: None,
                status: Some("observed".to_string()),
                input: serde_json::json!({}),
                output: serde_json::json!({}),
                related_pid: None,
                related_event_id: None,
                view_source: AGENT_NATIVE_SOURCE.to_string(),
                confidence: Some(0.95),
            });
        }
    }
    rows
}

fn updated_ms(session: &LocalSession) -> u64 {
    session
        .updated
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn matches_filter(
    session: &LocalSession,
    pid_filter: Option<u32>,
    text_filter: Option<&str>,
) -> bool {
    if pid_filter.is_some() {
        return true;
    }
    let Some(filter) = text_filter else {
        return true;
    };
    let filter = filter.to_ascii_lowercase();
    session.agent_type.to_ascii_lowercase().contains(&filter)
        || session
            .prompt_preview
            .as_ref()
            .is_some_and(|prompt| prompt.to_ascii_lowercase().contains(&filter))
        || session
            .model
            .as_ref()
            .is_some_and(|model| model.to_ascii_lowercase().contains(&filter))
        || session
            .path
            .to_string_lossy()
            .to_ascii_lowercase()
            .contains(&filter)
}

#[cfg(test)]
pub(crate) fn create_temp_session_path(agent: &str) -> (tempfile::TempDir, PathBuf) {
    let temp = tempfile::tempdir().unwrap();
    let path = agent_session::fixture_session_path(agent, temp.path()).unwrap();
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(&path, "{}\n").unwrap();
    (temp, path)
}

#[cfg(test)]
pub(crate) fn parse_content_for_test(
    agent: &str,
    path: &std::path::Path,
    updated: std::time::SystemTime,
    content: &str,
) -> Option<LocalSession> {
    agent_session::parse_session_content(agent, path, updated, content)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn agent_native_prompt_produces_llm_call_row() {
        let (_temp, path) = create_temp_session_path(agent_session::AGENT_CODEX);
        let session = parse_content_for_test(
            agent_session::AGENT_CODEX,
            &path,
            UNIX_EPOCH,
            "{\"type\":\"message\",\"content\":\"agentsight local codex prompt\"}\n",
        )
        .unwrap();

        let view = materialized_view(&[session]);
        let rows = view.llm_call_rows(10);

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].comm.as_deref(), Some(agent_session::AGENT_CODEX));
        assert_eq!(
            rows[0].request.get("prompt").and_then(Value::as_str),
            Some("agentsight local codex prompt")
        );
    }
}
