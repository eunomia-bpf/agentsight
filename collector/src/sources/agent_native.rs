// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::{AgentSession, TokenUsage};
use serde_json::Value;
use std::cmp::Reverse;
use std::collections::{BTreeMap, HashSet};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

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
const CODEX_EXEC_DEDUPE_WINDOW_MS: u64 = 2_000;
const CODEX_FALLBACK_TIME_SLOP_MS: u64 = 30_000;

#[derive(Clone, Debug)]
struct ObservedCodexPrompt {
    prompt: String,
    timestamp_ms: u64,
    pid: Option<u32>,
    native_exec: bool,
}

pub(crate) fn snapshot(
    cache: &mut SessionCache,
    pid_filter: Option<u32>,
    text_filter: Option<&str>,
    limit: usize,
    max_age: Duration,
) -> Snapshot {
    let indexed_codex = codex_state_sessions(limit);
    let mut sessions = if indexed_codex.is_empty() {
        cache.discover_cached(limit, max_age)
    } else {
        let mut sessions = indexed_codex;
        sessions.extend(cache.discover_cached_excluding(
            limit,
            max_age,
            &[agent_session::AGENT_CODEX],
        ));
        sessions.sort_by_key(|session| Reverse(session.updated));
        sessions.truncate(limit.clamp(1, 25));
        sessions
    };
    let mut seen = HashSet::new();
    sessions.retain(|session| seen.insert(session.display_id.clone()));
    let filtered: Vec<LocalSession> = sessions
        .into_iter()
        .filter(|s| matches_filter(s, pid_filter, text_filter))
        .collect();
    materialized_view(&filtered).export_snapshot(SnapshotOptions { audit_limit: 0 })
}

fn codex_state_sessions(limit: usize) -> Vec<LocalSession> {
    user_home_dir()
        .as_deref()
        .map(|home| codex_state_sessions_in_home(home, limit))
        .unwrap_or_default()
}

fn codex_state_sessions_in_home(home: &Path, limit: usize) -> Vec<LocalSession> {
    let db_path = home.join(".codex/state_5.sqlite");
    let Ok(conn) =
        rusqlite::Connection::open_with_flags(db_path, rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY)
    else {
        return Vec::new();
    };
    let Ok(mut stmt) = conn.prepare(
        "SELECT id, rollout_path, model, tokens_used, preview, cwd, created_at_ms, updated_at_ms
         FROM threads
         ORDER BY updated_at_ms DESC
         LIMIT ?1",
    ) else {
        return Vec::new();
    };
    let Ok(rows) = stmt.query_map([limit.clamp(1, 25) as i64], |row| {
        let id: String = row.get(0)?;
        let rollout_path: String = row.get(1)?;
        let model: Option<String> = row.get(2)?;
        let tokens_used: i64 = row.get(3)?;
        let preview: Option<String> = row.get(4)?;
        let cwd: Option<String> = row.get(5)?;
        let created_at_ms: Option<i64> = row.get(6)?;
        let updated_at_ms: Option<i64> = row.get(7)?;
        Ok(codex_state_session(
            id,
            rollout_path,
            model,
            tokens_used,
            preview,
            cwd,
            created_at_ms,
            updated_at_ms,
        ))
    }) else {
        return Vec::new();
    };

    rows.filter_map(Result::ok).collect()
}

fn codex_state_session(
    id: String,
    rollout_path: String,
    model: Option<String>,
    tokens_used: i64,
    preview: Option<String>,
    cwd: Option<String>,
    created_at_ms: Option<i64>,
    updated_at_ms: Option<i64>,
) -> LocalSession {
    let updated_ms = updated_at_ms.and_then(non_negative_i64_to_u64);
    let created_ms = created_at_ms
        .and_then(non_negative_i64_to_u64)
        .or(updated_ms);
    let updated = updated_ms.map(system_time_from_ms).unwrap_or(UNIX_EPOCH);
    let usage = TokenUsage {
        total_tokens: tokens_used.max(0),
        ..Default::default()
    };
    let model = model.filter(|value| !value.is_empty());
    let mut model_usage = BTreeMap::new();
    if let Some(model) = model.as_deref() {
        model_usage.insert(model.to_string(), usage.clone());
    }
    let prompt_preview = preview
        .and_then(|text| clean_prompt_text(&text))
        .map(|text| truncate_text(&text, 180));
    let last_message_at = updated_ms.map(iso_utc_from_ms);

    LocalSession {
        agent_type: agent_session::AGENT_CODEX.to_string(),
        session_id: id.clone(),
        conversation_id: Some(id.clone()),
        display_id: format!("{}:{}", agent_session::AGENT_CODEX, short_session_id(&id)),
        path: PathBuf::from(rollout_path),
        updated,
        start_timestamp_ms: created_ms,
        end_timestamp_ms: updated_ms,
        model,
        usage,
        model_usage,
        tools: BTreeMap::new(),
        files: BTreeMap::new(),
        prompt_preview,
        duration_ms: created_ms
            .zip(updated_ms)
            .map(|(start, end)| end.saturating_sub(start))
            .unwrap_or_default(),
        cwd,
        last_message_at,
        events: Default::default(),
    }
}

fn user_home_dir() -> Option<PathBuf> {
    std::env::var("SUDO_USER")
        .ok()
        .and_then(|user| {
            std::fs::read_to_string("/etc/passwd")
                .ok()
                .and_then(|passwd| {
                    passwd
                        .lines()
                        .find(|line| line.starts_with(&format!("{user}:")))
                        .and_then(|line| line.split(':').nth(5))
                        .map(PathBuf::from)
                })
        })
        .or_else(dirs::home_dir)
}

fn non_negative_i64_to_u64(value: i64) -> Option<u64> {
    u64::try_from(value).ok()
}

fn system_time_from_ms(value: u64) -> SystemTime {
    UNIX_EPOCH + Duration::from_millis(value)
}

fn iso_utc_from_ms(value: u64) -> String {
    chrono::DateTime::<chrono::Utc>::from_timestamp_millis(value as i64)
        .map(|dt| dt.to_rfc3339_opts(chrono::SecondsFormat::Millis, true))
        .unwrap_or_default()
}

fn short_session_id(id: &str) -> String {
    let compact = id.rsplit(['/', '\\']).next().unwrap_or(id).trim();
    if compact.chars().count() <= 12 {
        return compact.to_string();
    }
    let head = compact.chars().take(6).collect::<String>();
    let tail = compact
        .chars()
        .rev()
        .take(5)
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<String>();
    format!("{head}.{tail}")
}

fn clean_prompt_text(text: &str) -> Option<String> {
    let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    (!text.trim().is_empty()).then(|| text.trim().to_string())
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
    let observed_exec_prompts = observed_codex_exec_prompts(audit_rows);
    let mut seen_exec_prompts: Vec<ObservedCodexPrompt> = Vec::new();
    for row in audit_rows {
        if row.audit_type == "process" && row.action.as_deref() == Some("exec") {
            let Some(prompt) = row
                .details
                .get("full_command")
                .and_then(Value::as_str)
                .and_then(codex_exec_prompt_from_command)
            else {
                continue;
            };
            if !observed_exec_prompts.iter().any(|observed| {
                observed.prompt == prompt
                    && observed.timestamp_ms == row.timestamp_ms
                    && observed.pid == row.pid
            }) {
                continue;
            }
            if seen_exec_prompts.iter().any(|seen| {
                seen.prompt == prompt
                    && timestamps_close(
                        seen.timestamp_ms,
                        row.timestamp_ms,
                        CODEX_EXEC_DEDUPE_WINDOW_MS,
                    )
                    && (!seen.native_exec || !looks_like_native_codex_exec(row))
            }) {
                continue;
            }
            seen_exec_prompts.push(ObservedCodexPrompt {
                prompt: prompt.clone(),
                timestamp_ms: row.timestamp_ms,
                pid: row.pid,
                native_exec: looks_like_native_codex_exec(row),
            });
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
    rows
}

pub(crate) fn observed_sessions_from_audit_rows(audit_rows: &[AuditEventRow]) -> Vec<LocalSession> {
    let mut direct_paths = HashSet::new();
    let mut codex_session_dirs = HashSet::new();
    let observed_codex_prompts = observed_codex_exec_prompts(audit_rows);
    let observed_codex_exec = observed_codex_exec_command(audit_rows);
    let observed_window = observed_audit_window_ms(audit_rows);

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
            candidates.push((candidate, false));
        }
    }
    for dir in codex_session_dirs {
        let dir_candidates =
            agent_session::discover_session_files_in_dir(agent_session::AGENT_CODEX, &dir);
        candidates.extend(
            dir_candidates
                .into_iter()
                .map(|candidate| (candidate, true)),
        );
    }
    candidates.sort_by_key(|(candidate, _)| Reverse(candidate.updated));

    let mut seen_paths = HashSet::new();
    let mut seen_sessions = HashSet::new();
    let mut sessions = Vec::new();
    for (candidate, is_codex_dir_fallback) in candidates.into_iter().take(75) {
        if !seen_paths.insert(candidate.path.clone()) {
            continue;
        }
        let Some(session) = agent_session::parse_session_file(&candidate) else {
            continue;
        };
        if is_codex_dir_fallback && !observed_codex_exec {
            continue;
        }
        if is_codex_dir_fallback
            && !observed_codex_prompts.is_empty()
            && !session_matches_observed_prompt(&session, &observed_codex_prompts)
        {
            continue;
        }
        if is_codex_dir_fallback && !session_is_in_observed_window(&session, observed_window) {
            continue;
        }
        if seen_sessions.insert(session.display_id.clone()) {
            sessions.push(session);
        }
    }
    sessions
}

fn observed_codex_exec_prompts(audit_rows: &[AuditEventRow]) -> Vec<ObservedCodexPrompt> {
    let prompts = audit_rows
        .iter()
        .filter(|row| row.audit_type == "process" && row.action.as_deref() == Some("exec"))
        .filter_map(|row| {
            let prompt = row
                .details
                .get("full_command")
                .and_then(Value::as_str)
                .and_then(codex_exec_prompt_from_command)?;
            Some(ObservedCodexPrompt {
                prompt,
                timestamp_ms: row.timestamp_ms,
                pid: row.pid,
                native_exec: looks_like_native_codex_exec(row),
            })
        })
        .collect::<Vec<_>>();
    prompts
        .iter()
        .filter(|candidate| {
            !prompts
                .iter()
                .any(|other| is_nearby_longer_prefix(candidate, other))
        })
        .cloned()
        .collect()
}

fn observed_codex_exec_command(audit_rows: &[AuditEventRow]) -> bool {
    audit_rows
        .iter()
        .filter(|row| row.audit_type == "process" && row.action.as_deref() == Some("exec"))
        .filter_map(|row| row.details.get("full_command").and_then(Value::as_str))
        .any(|command| codex_exec_command_tail(command).is_some())
}

fn codex_exec_prompt_from_command(command: &str) -> Option<String> {
    agent_session::codex_exec_prompt(&codex_exec_command_tail(command)?)
}

fn codex_exec_command_tail(command: &str) -> Option<String> {
    let tokens = command.split_whitespace().collect::<Vec<_>>();
    let index = tokens.windows(2).enumerate().find_map(|(index, tokens)| {
        (is_codex_executable_token(tokens[0], index == 0) && tokens[1] == "exec").then_some(index)
    })?;
    Some(tokens[index..].join(" "))
}

fn looks_like_native_codex_exec(row: &AuditEventRow) -> bool {
    row.comm.as_deref() == Some("codex")
        && row
            .target
            .as_deref()
            .is_some_and(|target| is_codex_executable_token(target, true))
}

fn is_codex_executable_token(token: &str, allow_bare: bool) -> bool {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    (allow_bare && token == "codex")
        || token.contains('/')
            && Path::new(token).file_name().and_then(|name| name.to_str()) == Some("codex")
}

fn is_nearby_longer_prefix(candidate: &ObservedCodexPrompt, other: &ObservedCodexPrompt) -> bool {
    other.prompt.len() > candidate.prompt.len()
        && other.prompt.starts_with(candidate.prompt.as_str())
        && timestamps_close(
            candidate.timestamp_ms,
            other.timestamp_ms,
            CODEX_EXEC_DEDUPE_WINDOW_MS,
        )
        && (!candidate.native_exec || !other.native_exec)
}

fn timestamps_close(left: u64, right: u64, window_ms: u64) -> bool {
    left.abs_diff(right) <= window_ms
}

fn session_matches_observed_prompt(
    session: &LocalSession,
    prompts: &[ObservedCodexPrompt],
) -> bool {
    let Some(preview) = session.prompt_preview.as_deref() else {
        return false;
    };
    prompts.iter().any(|observed| {
        let prompt = observed.prompt.as_str();
        prompt_texts_overlap(prompt, preview)
    })
}

fn prompt_texts_overlap(left: &str, right: &str) -> bool {
    left == right || left.starts_with(right) || right.starts_with(left)
}

fn observed_audit_window_ms(audit_rows: &[AuditEventRow]) -> Option<(u64, u64)> {
    let min = audit_rows.iter().map(|row| row.timestamp_ms).min()?;
    let max = audit_rows.iter().map(|row| row.timestamp_ms).max()?;
    Some((
        min.saturating_sub(CODEX_FALLBACK_TIME_SLOP_MS),
        max.saturating_add(CODEX_FALLBACK_TIME_SLOP_MS),
    ))
}

fn session_is_in_observed_window(session: &LocalSession, window: Option<(u64, u64)>) -> bool {
    let Some((min, max)) = window else {
        return true;
    };
    let updated = updated_ms(session);
    updated >= min && updated <= max
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
        || matches!(name, "config.toml" | "auth.json" | "stat"))
        && path
            .parent()
            .is_some_and(|parent| parent.join("sessions").is_dir())
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

    const CODEX: &str = "/usr/bin/codex exec --skip-git-repo-check ";

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

    #[test]
    fn codex_state_db_produces_indexed_session_metadata() {
        let temp = tempfile::tempdir().unwrap();
        let codex_dir = temp.path().join(".codex");
        fs::create_dir_all(&codex_dir).unwrap();
        let conn = rusqlite::Connection::open(codex_dir.join("state_5.sqlite")).unwrap();
        conn.execute_batch(
            "CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                rollout_path TEXT,
                model TEXT,
                tokens_used INTEGER NOT NULL DEFAULT 0,
                preview TEXT,
                cwd TEXT,
                created_at_ms INTEGER,
                updated_at_ms INTEGER
            );",
        )
        .unwrap();
        conn.execute(
            "INSERT INTO threads
             (id, rollout_path, model, tokens_used, preview, cwd, created_at_ms, updated_at_ms)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            rusqlite::params![
                "019f49ca-54e7-7a91-82e7-a52b53cfd456",
                temp.path()
                    .join(".codex/sessions/session.jsonl")
                    .to_string_lossy(),
                "gpt-5.5",
                12345i64,
                "hello from state",
                "/work/repo",
                1_800_000i64,
                1_900_000i64,
            ],
        )
        .unwrap();

        let sessions = codex_state_sessions_in_home(temp.path(), 5);

        assert_eq!(sessions.len(), 1);
        assert_eq!(sessions[0].display_id, "codex:019f49.fd456");
        assert_eq!(sessions[0].model.as_deref(), Some("gpt-5.5"));
        assert_eq!(sessions[0].usage.total_tokens, 12345);
        assert_eq!(
            sessions[0].prompt_preview.as_deref(),
            Some("hello from state")
        );
        assert_eq!(sessions[0].cwd.as_deref(), Some("/work/repo"));
        assert_eq!(
            sessions[0].last_message_at.as_deref(),
            Some("1970-01-01T00:31:40.000Z")
        );
    }

    #[test]
    fn codex_state_db_errors_return_empty_for_jsonl_fallback() {
        let temp = tempfile::tempdir().unwrap();
        fs::create_dir_all(temp.path().join(".codex")).unwrap();
        fs::write(temp.path().join(".codex/state_5.sqlite"), "not sqlite").unwrap();

        assert!(codex_state_sessions_in_home(temp.path(), 5).is_empty());
    }

    #[test]
    fn crowded_codex_home_fallback_keeps_only_observed_exec_prompt() {
        let temp = tempfile::tempdir().unwrap();
        let state_path = write_codex_home(
            temp.path(),
            &[
                "unrelated historical prompt",
                "unrelated historical prompt",
                "unrelated historical prompt",
                "agentsight current run prompt",
                "agentsight current run historical prompt",
                "unrelated historical prompt",
                "unrelated historical prompt",
                "unrelated historical prompt",
            ],
        );
        let now = current_epoch_ms();

        let rows = vec![
            exec_row(
                "audit-exec",
                now,
                "codex",
                &format!("{CODEX}agentsight current run prompt"),
            ),
            exec_row(
                "audit-exec-truncated",
                now + 1,
                "node",
                &format!("{CODEX}agentsight current run"),
            ),
            file_row("audit-file", now + 100, &state_path),
        ];

        let sessions = observed_sessions_from_audit_rows(&rows);

        assert_eq!(sessions.len(), 1);
        assert_eq!(
            sessions[0].prompt_preview.as_deref(),
            Some("agentsight current run prompt")
        );
    }

    #[test]
    fn codex_home_fallback_accepts_time_window_when_exec_prompt_is_truncated() {
        let temp = tempfile::tempdir().unwrap();
        let state_path = write_codex_home(temp.path(), &["agentsight truncated command prompt"]);
        let now = current_epoch_ms();

        let sessions = observed_sessions_from_audit_rows(&[
            exec_row(
                "audit-exec",
                now,
                "codex",
                &format!("{CODEX}-c model_provider=\"agentsight-mock"),
            ),
            file_row("audit-file", now + 100, &state_path),
        ]);

        assert_eq!(sessions.len(), 1);
        assert_eq!(
            sessions[0].prompt_preview.as_deref(),
            Some("agentsight truncated command prompt")
        );
    }

    #[test]
    fn codex_exec_prompt_rows_filter_only_wrapper_duplicates() {
        let rows = [
            (1_000, "node", "/usr/bin/node /opt/codex/bin/codex exec --skip-git-repo-check agentsight dedupe prompt"),
            (1_001, "codex", "/opt/codex/bin/codex exec --skip-git-repo-check agentsight dedupe prompt"),
            (2_000, "codex", "/usr/bin/codex exec --skip-git-repo-check agentsight short prompt"),
            (3_000, "codex", "/usr/bin/codex exec --skip-git-repo-check agentsight much longer unrelated prompt"),
            (10_000, "codex", "/usr/bin/codex exec --skip-git-repo-check agentsight repeated prompt"),
            (11_000, "codex", "/usr/bin/codex exec --skip-git-repo-check agentsight repeated prompt"),
            (20_000, "codex", "/usr/bin/codex exec --skip-git-repo-check agentsight repeated prompt"),
            (21_000, "docker", "docker exec codex exec agentsight should not parse"),
            (22_000, "docker", "docker exec container /usr/local/bin/codex exec agentsight should parse once"),
        ]
        .into_iter()
        .enumerate()
        .map(|(index, (ts, comm, command))| exec_row(&format!("audit-{index}"), ts, comm, command))
        .collect::<Vec<_>>();

        let prompts = observed_session_prompt_rows(&rows)
            .into_iter()
            .map(|row| row.summary)
            .collect::<Vec<_>>();

        assert_eq!(
            prompts,
            vec![
                Some("agentsight dedupe prompt".to_string()),
                Some("agentsight short prompt".to_string()),
                Some("agentsight much longer unrelated prompt".to_string()),
                Some("agentsight repeated prompt".to_string()),
                Some("agentsight repeated prompt".to_string()),
                Some("agentsight repeated prompt".to_string()),
                Some("agentsight should parse once".to_string()),
            ]
        );
    }

    #[test]
    fn codex_fallback_time_window_rejects_stale_matching_session() {
        let (_temp, path) = create_temp_session_path(agent_session::AGENT_CODEX);
        let session = parse_content_for_test(
            agent_session::AGENT_CODEX,
            &path,
            UNIX_EPOCH,
            "{\"type\":\"message\",\"content\":\"agentsight repeated prompt\"}\n",
        )
        .unwrap();

        assert!(session_matches_observed_prompt(
            &session,
            &[ObservedCodexPrompt {
                prompt: "agentsight repeated prompt".to_string(),
                timestamp_ms: current_epoch_ms(),
                pid: Some(42),
                native_exec: true,
            }]
        ));
        assert!(!session_is_in_observed_window(
            &session,
            Some((current_epoch_ms() - 1_000, current_epoch_ms() + 1_000))
        ));
    }

    fn exec_row(id: &str, timestamp_ms: u64, comm: &str, full_command: &str) -> AuditEventRow {
        AuditEventRow {
            id: id.to_string(),
            timestamp_ms,
            audit_type: "process".to_string(),
            pid: Some(42),
            comm: Some(comm.to_string()),
            subject: None,
            action: Some("exec".to_string()),
            target: Some(format!("/usr/bin/{comm}")),
            status: Some("observed".to_string()),
            summary: None,
            details: serde_json::json!({ "full_command": full_command }),
        }
    }

    fn file_row(id: &str, timestamp_ms: u64, path: &Path) -> AuditEventRow {
        AuditEventRow {
            id: id.to_string(),
            timestamp_ms,
            audit_type: "file".to_string(),
            pid: Some(42),
            comm: Some("codex".to_string()),
            subject: None,
            action: Some("write".to_string()),
            target: Some(path.to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: None,
            details: serde_json::json!({ "filepath": path.to_string_lossy() }),
        }
    }

    fn current_epoch_ms() -> u64 {
        std::time::SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }

    fn write_codex_home(root: &Path, prompts: &[&str]) -> PathBuf {
        let codex_home = root.join("codex-home");
        let sessions_dir = codex_home.join("sessions/2026/07/14");
        fs::create_dir_all(&sessions_dir).unwrap();
        for (index, prompt) in prompts.iter().enumerate() {
            fs::write(
                sessions_dir.join(format!(
                    "rollout-2026-07-14T00-00-{index:02}-session-{index}.jsonl"
                )),
                format!(
                    "{{\"timestamp\":\"2026-07-14T00:00:{index:02}.000Z\",\
                     \"type\":\"event_msg\",\
                     \"payload\":{{\"type\":\"user_message\",\"message\":\"{prompt}\"}}}}\n"
                ),
            )
            .unwrap();
        }
        let state_path = codex_home.join("stat");
        fs::write(&state_path, "").unwrap();
        state_path
    }
}
