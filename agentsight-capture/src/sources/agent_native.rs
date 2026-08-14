// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::{AgentSession, TokenUsage};
use serde_json::Value;
use std::cmp::Reverse;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use std::fs;

use crate::model::{
    AGENT_NATIVE_SOURCE, AuditEventRow, LlmCallRow, SessionRow, Snapshot, SnapshotOptions,
    TokenUsageRow, ToolCallRow,
};
use crate::text::{sanitize_ascii_identifier as sanitize_id, truncate_text};
use crate::view::MaterializedView;

pub type LocalSession = AgentSession;
pub type SessionCache = agent_session::SessionCache;
const CODEX_EXEC_DEDUPE_WINDOW_MS: u64 = 2_000;
const CODEX_FALLBACK_TIME_SLOP_MS: u64 = 30_000;
const CODEX_ROLLOUT_TAIL_BYTES: u64 = 1024 * 1024;
// Local copy of agent_session::AGENT_CURSOR. cargo package verifies this crate
// against the published agent-session, which lags behind the workspace copy, so
// production code here cannot reference constants the registry version lacks.
const CURSOR_AGENT_TYPE: &str = "cursor";

#[derive(Clone, Debug)]
struct ObservedCodexPrompt {
    prompt: String,
    timestamp_ms: u64,
    pid: Option<u32>,
    native_exec: bool,
    comm: Option<String>,
    target: Option<String>,
}

pub fn snapshot(
    cache: &mut SessionCache,
    pid_filter: Option<u32>,
    text_filter: Option<&str>,
    limit: usize,
    max_age: Duration,
) -> Snapshot {
    let filtered = discover_sessions(cache, pid_filter, text_filter, limit, max_age);
    materialized_view(&filtered).export_snapshot(SnapshotOptions { audit_limit: 0 })
}

pub fn discover_sessions(
    cache: &mut SessionCache,
    pid_filter: Option<u32>,
    text_filter: Option<&str>,
    limit: usize,
    max_age: Duration,
) -> Vec<LocalSession> {
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
    enrich_cursor_sessions(&mut sessions);
    sessions
        .into_iter()
        .filter(|s| matches_filter(s, pid_filter, text_filter))
        .collect()
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
    let path = PathBuf::from(rollout_path);
    let (rollout_usage, plan, _) = codex_rollout_summary(&path);
    let usage = rollout_usage.unwrap_or(TokenUsage {
        total_tokens: tokens_used.max(0),
        ..Default::default()
    });
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
        path,
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
        events: agent_session::SessionEvents {
            plan,
            ..Default::default()
        },
    }
}

/// Expand a lightweight indexed session only when a caller needs transcript events.
/// Discovery remains bounded and cheap; the shared cache avoids reparsing unchanged files.
pub fn hydrate_session(cache: &mut SessionCache, mut indexed: LocalSession) -> LocalSession {
    if !indexed.events.prompts.is_empty()
        || !indexed.events.tools.is_empty()
        || !indexed.events.llm_responses.is_empty()
    {
        bound_session_detail(&mut indexed);
        return indexed;
    }
    let Some(mut parsed) = cache.parse_path_cached(&indexed.path) else {
        return indexed;
    };
    parsed.session_id = indexed.session_id;
    parsed.conversation_id = indexed.conversation_id;
    parsed.display_id = indexed.display_id;
    parsed.updated = indexed.updated;
    parsed.start_timestamp_ms = indexed.start_timestamp_ms.or(parsed.start_timestamp_ms);
    parsed.end_timestamp_ms = indexed.end_timestamp_ms.or(parsed.end_timestamp_ms);
    parsed.last_message_at = indexed.last_message_at.or(parsed.last_message_at);
    parsed.model = indexed.model.or(parsed.model);
    parsed.cwd = indexed.cwd.or(parsed.cwd);
    parsed.prompt_preview = indexed.prompt_preview.or(parsed.prompt_preview);
    if indexed.usage.total_tokens > 0 {
        parsed.usage = indexed.usage;
        parsed.model_usage = indexed.model_usage;
    }
    if let (Some(start), Some(end)) = (parsed.start_timestamp_ms, parsed.end_timestamp_ms) {
        parsed.duration_ms = end.saturating_sub(start);
    }
    bound_session_detail(&mut parsed);
    parsed
}

const MAX_DETAIL_PROMPTS: usize = 1_000;
const MAX_DETAIL_RESPONSES: usize = 2_000;
const MAX_DETAIL_TOOLS: usize = 2_000;
const MAX_DETAIL_TEXT_BYTES_PER_KIND: usize = 2 * 1024 * 1024;
const MAX_DETAIL_TOOL_COMMAND_BYTES: usize = 1024 * 1024;

fn retain_latest<T>(rows: &mut Vec<T>, limit: usize) {
    if rows.len() > limit {
        rows.drain(..rows.len() - limit);
    }
}

fn fit_text_budget<'a>(texts: impl DoubleEndedIterator<Item = &'a mut String>, budget: usize) {
    let mut remaining = budget;
    for text in texts.rev() {
        if text.len() <= remaining {
            remaining -= text.len();
            continue;
        }
        if remaining == 0 {
            text.clear();
            continue;
        }
        let mut end = remaining.min(text.len());
        while !text.is_char_boundary(end) {
            end -= 1;
        }
        text.truncate(end);
        remaining = 0;
    }
}

/// Bound the authorized detail payload without losing the newest interaction.
/// Previews remain available when older full text falls outside the budget.
fn bound_session_detail(session: &mut LocalSession) {
    retain_latest(&mut session.events.prompts, MAX_DETAIL_PROMPTS);
    retain_latest(&mut session.events.llm_responses, MAX_DETAIL_RESPONSES);
    retain_latest(&mut session.events.tools, MAX_DETAIL_TOOLS);
    fit_text_budget(
        session
            .events
            .prompts
            .iter_mut()
            .map(|event| &mut event.text),
        MAX_DETAIL_TEXT_BYTES_PER_KIND,
    );
    fit_text_budget(
        session
            .events
            .llm_responses
            .iter_mut()
            .map(|event| &mut event.text),
        MAX_DETAIL_TEXT_BYTES_PER_KIND,
    );
    fit_text_budget(
        session
            .events
            .tools
            .iter_mut()
            .map(|event| &mut event.command),
        MAX_DETAIL_TOOL_COMMAND_BYTES,
    );
    for event in &mut session.events.tools {
        event.process_chain.truncate(16);
        event.path_groups.truncate(32);
        event.paths.truncate(32);
        event.domains.truncate(32);
        event.task_path.truncate(16);
    }
}

type CodexRolloutSummary = (
    Option<TokenUsage>,
    Vec<agent_session::PlanStep>,
    Option<Value>,
);

#[derive(Clone)]
struct CachedCodexRolloutSummary {
    len: u64,
    modified: SystemTime,
    summary: CodexRolloutSummary,
}

fn codex_summary_cache() -> &'static Mutex<HashMap<PathBuf, CachedCodexRolloutSummary>> {
    static CACHE: OnceLock<Mutex<HashMap<PathBuf, CachedCodexRolloutSummary>>> = OnceLock::new();
    CACHE.get_or_init(|| Mutex::new(HashMap::new()))
}

fn codex_rollout_summary(path: &Path) -> CodexRolloutSummary {
    let Ok(metadata) = fs::metadata(path) else {
        return (None, Vec::new(), None);
    };
    let len = metadata.len();
    let modified = metadata.modified().unwrap_or(UNIX_EPOCH);
    if let Ok(cache) = codex_summary_cache().lock()
        && let Some(cached) = cache.get(path)
        && cached.len == len
        && cached.modified == modified
    {
        return cached.summary.clone();
    }
    let Ok(mut file) = File::open(path) else {
        return (None, Vec::new(), None);
    };
    let window = len.min(CODEX_ROLLOUT_TAIL_BYTES);
    if file.seek(SeekFrom::Start(len - window)).is_err() {
        return (None, Vec::new(), None);
    }
    let mut data = Vec::with_capacity(window as usize);
    if file.read_to_end(&mut data).is_err() {
        return (None, Vec::new(), None);
    }
    let content = String::from_utf8_lossy(&data);
    let usage = agent_session::codex_total_token_usage(&content);
    let plan = agent_session::codex_latest_plan(&content).unwrap_or_default();
    let subscription = codex_latest_subscription(&content);
    let summary = (usage, plan, subscription);
    if let Ok(mut cache) = codex_summary_cache().lock() {
        const MAX_CODEX_SUMMARY_CACHE: usize = 64;
        if cache.len() >= MAX_CODEX_SUMMARY_CACHE && !cache.contains_key(path) {
            cache.clear();
        }
        cache.insert(
            path.to_path_buf(),
            CachedCodexRolloutSummary {
                len,
                modified,
                summary: summary.clone(),
            },
        );
    }
    summary
}

fn codex_latest_subscription(content: &str) -> Option<Value> {
    content.lines().rev().find_map(|line| {
        let event: Value = serde_json::from_str(line).ok()?;
        let payload = event.get("payload")?;
        if payload.get("type").and_then(Value::as_str) != Some("token_count") {
            return None;
        }
        let limits = payload.get("rate_limits")?.as_object()?;
        let window = |name: &str| {
            let value = limits.get(name)?;
            Some(serde_json::json!({
                "used_percent": value.get("used_percent").and_then(Value::as_f64),
                "window_minutes": value.get("window_minutes").and_then(Value::as_u64),
                "resets_at": value.get("resets_at").and_then(Value::as_u64),
            }))
        };
        let credits = limits.get("credits");
        Some(serde_json::json!({
            "provider": "codex",
            "observed_at": event.get("timestamp").and_then(Value::as_str),
            "plan_type": limits.get("plan_type").and_then(Value::as_str),
            "limit_name": limits.get("limit_name").and_then(Value::as_str),
            "primary": window("primary"),
            "secondary": window("secondary"),
            "credits": {
                "unlimited": credits.and_then(|value| value.get("unlimited")).and_then(Value::as_bool),
            },
        }))
    })
}

const CURSOR_STATE_DB_CANDIDATES: [&str; 3] = [
    "Library/Application Support/Cursor/User/globalStorage/state.vscdb",
    ".config/Cursor/User/globalStorage/state.vscdb",
    "AppData/Roaming/Cursor/User/globalStorage/state.vscdb",
];

fn cursor_state_db_path(home: &Path) -> Option<PathBuf> {
    CURSOR_STATE_DB_CANDIDATES
        .iter()
        .map(|candidate| home.join(candidate))
        .find(|path| path.is_file())
}

fn open_cursor_state_db(path: &Path) -> Option<rusqlite::Connection> {
    rusqlite::Connection::open_with_flags(path, rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY).ok()
}

struct CursorComposerHeader {
    created_at_ms: Option<u64>,
    updated_at_ms: Option<u64>,
}

fn cursor_composer_header(
    conn: &rusqlite::Connection,
    composer_id: &str,
) -> Option<CursorComposerHeader> {
    conn.query_row(
        "SELECT createdAt, lastUpdatedAt FROM composerHeaders WHERE composerId = ?1",
        [composer_id],
        |row| {
            let created: Option<i64> = row.get(0)?;
            let updated: Option<i64> = row.get(1)?;
            Ok(CursorComposerHeader {
                created_at_ms: created.and_then(non_negative_i64_to_u64),
                updated_at_ms: updated.and_then(non_negative_i64_to_u64),
            })
        },
    )
    .ok()
}

fn cursor_kv_bytes(value: rusqlite::types::Value) -> Option<Vec<u8>> {
    match value {
        rusqlite::types::Value::Blob(bytes) => Some(bytes),
        rusqlite::types::Value::Text(text) => Some(text.into_bytes()),
        _ => None,
    }
}

struct CursorComposerData {
    model: Option<String>,
    workspace_path: Option<String>,
}

fn cursor_composer_data(
    conn: &rusqlite::Connection,
    composer_id: &str,
) -> Option<CursorComposerData> {
    let raw: rusqlite::types::Value = conn
        .query_row(
            "SELECT value FROM cursorDiskKV WHERE key = ?1",
            [format!("composerData:{composer_id}")],
            |row| row.get(0),
        )
        .ok()?;
    let value: Value = serde_json::from_slice(&cursor_kv_bytes(raw)?).ok()?;
    let model = value
        .pointer("/modelConfig/modelName")
        .and_then(Value::as_str)
        .filter(|name| !name.is_empty() && *name != "default")
        .map(str::to_string);
    let workspace_path = value
        .pointer("/workspaceIdentifier/uri/fsPath")
        .and_then(Value::as_str)
        .filter(|path| !path.is_empty())
        .map(str::to_string);
    Some(CursorComposerData {
        model,
        workspace_path,
    })
}

fn cursor_bubble_tokens(conn: &rusqlite::Connection, composer_id: &str) -> TokenUsage {
    let mut usage = TokenUsage::default();
    let Ok(mut stmt) = conn.prepare("SELECT value FROM cursorDiskKV WHERE key >= ?1 AND key < ?2")
    else {
        return usage;
    };
    let lower = format!("bubbleId:{composer_id}:");
    let upper = format!("bubbleId:{composer_id};");
    let Ok(rows) = stmt.query_map([lower, upper], |row| {
        row.get::<_, rusqlite::types::Value>(0)
    }) else {
        return usage;
    };
    for raw in rows.filter_map(Result::ok).filter_map(cursor_kv_bytes) {
        let Ok(value) = serde_json::from_slice::<Value>(&raw) else {
            continue;
        };
        let input = value
            .pointer("/tokenCount/inputTokens")
            .and_then(Value::as_i64)
            .unwrap_or_default()
            .max(0);
        let output = value
            .pointer("/tokenCount/outputTokens")
            .and_then(Value::as_i64)
            .unwrap_or_default()
            .max(0);
        if input + output > 0 {
            usage.input_tokens += input;
            usage.output_tokens += output;
            usage.total_tokens += input + output;
        }
    }
    usage
}

fn cursor_subagent_ids(parent_transcript: &Path) -> Vec<String> {
    let Some(subagents) = parent_transcript.parent().map(|dir| dir.join("subagents")) else {
        return Vec::new();
    };
    let Ok(entries) = fs::read_dir(subagents) else {
        return Vec::new();
    };
    let mut ids: Vec<String> = entries
        .flatten()
        .map(|entry| entry.path())
        .filter(|path| path.extension().and_then(|ext| ext.to_str()) == Some("jsonl"))
        .filter_map(|path| {
            path.file_stem()
                .and_then(|stem| stem.to_str())
                .map(str::to_string)
        })
        .collect();
    ids.sort();
    ids
}

fn enrich_cursor_sessions(sessions: &mut [LocalSession]) {
    if !sessions
        .iter()
        .any(|session| session.agent_type == CURSOR_AGENT_TYPE)
    {
        return;
    }
    let Some(home) = user_home_dir() else {
        return;
    };
    enrich_cursor_sessions_in_home(&home, sessions);
}

fn enrich_cursor_sessions_in_home(home: &Path, sessions: &mut [LocalSession]) {
    let Some(db_path) = cursor_state_db_path(home) else {
        return;
    };
    let Some(conn) = open_cursor_state_db(&db_path) else {
        return;
    };
    for session in sessions
        .iter_mut()
        .filter(|session| session.agent_type == CURSOR_AGENT_TYPE)
    {
        enrich_cursor_session(&conn, session);
    }
}

fn enrich_cursor_session(conn: &rusqlite::Connection, session: &mut LocalSession) {
    let composer_id = session.session_id.clone();
    if let Some(header) = cursor_composer_header(conn, &composer_id) {
        if header.created_at_ms.is_some() {
            session.start_timestamp_ms = header.created_at_ms;
        }
        if let Some(updated_ms) = header.updated_at_ms {
            session.end_timestamp_ms = Some(updated_ms);
            session.last_message_at = Some(iso_utc_from_ms(updated_ms));
        }
        if let (Some(start), Some(end)) = (session.start_timestamp_ms, session.end_timestamp_ms) {
            session.duration_ms = end.saturating_sub(start);
        }
    }
    if let Some(data) = cursor_composer_data(conn, &composer_id) {
        if data.model.is_some() {
            session.model = data.model;
        }
        if data.workspace_path.is_some() {
            session.cwd = data.workspace_path;
        }
    }
    // Roll up across delegated runs, or the sessions that delegated most under-report.
    let mut usage = cursor_bubble_tokens(conn, &composer_id);
    for child_id in cursor_subagent_ids(&session.path) {
        let child = cursor_bubble_tokens(conn, &child_id);
        usage.input_tokens += child.input_tokens;
        usage.output_tokens += child.output_tokens;
        usage.total_tokens += child.total_tokens;
    }
    if usage.total_tokens > 0 {
        if let Some(model) = session.model.as_deref() {
            session.model_usage.insert(model.to_string(), usage.clone());
        }
        session.usage = usage;
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
        .or_else(|| {
            std::env::var_os("HOME")
                .map(PathBuf::from)
                .filter(|home| home.is_absolute())
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

pub fn materialized_view(sessions: &[LocalSession]) -> MaterializedView {
    let mut view = MaterializedView::new();
    view.set_source(AGENT_NATIVE_SOURCE);
    import_into_view(&mut view, sessions);
    view
}

pub fn import_recent(view: &mut MaterializedView, limit: usize) {
    let mut sessions = SessionCache::new().discover_cached(limit, Duration::ZERO);
    // `discover_sessions` enriches on its way out, but this is a second entry
    // point into the same data and every `report` subcommand without a --db
    // goes through here, as does the snapshot the frontend renders.
    enrich_cursor_sessions(&mut sessions);
    import_into_view(view, &sessions);
}

pub fn import_into_view(view: &mut MaterializedView, sessions: &[LocalSession]) {
    for session in sessions {
        // Sessions flow to bridge consumers as mutations, so this goes through
        // `emit_session` rather than a bare upsert.
        let _ = view.emit_session(session_row(session));
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

pub fn observed_session_prompt_rows(audit_rows: &[AuditEventRow]) -> Vec<AuditEventRow> {
    let mut rows = Vec::new();
    let mut seen = HashSet::new();
    let observed_exec_prompts = observed_codex_exec_prompts(audit_rows);
    let mut seen_exec_prompts: Vec<ObservedCodexPrompt> = Vec::new();
    for observed in observed_exec_prompts {
        if seen_exec_prompts.iter().any(|seen| {
            seen.prompt == observed.prompt
                && timestamps_close(
                    seen.timestamp_ms,
                    observed.timestamp_ms,
                    CODEX_EXEC_DEDUPE_WINDOW_MS,
                )
                && (!seen.native_exec || !observed.native_exec)
        }) {
            continue;
        }
        seen_exec_prompts.push(observed.clone());
        rows.push(AuditEventRow {
            id: format!(
                "audit-codex-exec-prompt-{}-{}",
                observed.timestamp_ms,
                observed.pid.unwrap_or(0)
            ),
            timestamp_ms: observed.timestamp_ms,
            audit_type: "llm".to_string(),
            pid: observed.pid,
            comm: observed.comm.or_else(|| Some("codex".to_string())),
            subject: None,
            action: Some("request".to_string()),
            target: observed.target,
            status: Some("observed".to_string()),
            summary: Some(truncate_text(&observed.prompt, 160)),
            details: serde_json::json!({
                "text_content": observed.prompt,
                "prompt_source": "local",
            }),
        });
    }
    for row in audit_rows {
        if row.audit_type == "process" && row.action.as_deref() == Some("exec") {
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

pub fn observed_sessions_from_audit_rows(audit_rows: &[AuditEventRow]) -> Vec<LocalSession> {
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
                comm: row.comm.clone(),
                target: row.target.clone(),
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
    let subscription = (session.agent_type == agent_session::AGENT_CODEX)
        .then(|| codex_rollout_summary(&session.path).2)
        .flatten();
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
            "plan": session.events.plan,
            "usage": session.usage,
            "subscription": subscription,
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

#[cfg(any(test, feature = "test-support"))]
pub fn create_temp_session_path(agent: &str) -> (tempfile::TempDir, PathBuf) {
    let temp = tempfile::tempdir().unwrap();
    let path = agent_session::fixture_session_path(agent, temp.path()).unwrap();
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(&path, "{}\n").unwrap();
    (temp, path)
}

#[cfg(any(test, feature = "test-support"))]
pub fn parse_content_for_test(
    agent: &str,
    path: &std::path::Path,
    updated: std::time::SystemTime,
    content: &str,
) -> Option<LocalSession> {
    agent_session::parse_session_content(agent, path, updated, content)
}

/// Fixture mirroring Cursor's `state.vscdb` on 3.15.6: one parent composer
/// with model, workspace, and legacy token bubbles, one subagent composer with
/// a NULL `lastUpdatedAt`, and one composer left on the "default" model.
#[cfg(any(test, feature = "test-support"))]
pub fn write_cursor_state_db_for_test(home: &Path) {
    let db_dir = home.join("Library/Application Support/Cursor/User/globalStorage");
    fs::create_dir_all(&db_dir).unwrap();
    let conn = rusqlite::Connection::open(db_dir.join("state.vscdb")).unwrap();
    // Real installs run WAL, which is what lets a read-only connection work
    // while Cursor holds a write transaction.
    conn.pragma_update(None, "journal_mode", "WAL").unwrap();
    conn.execute_batch(
        r#"CREATE TABLE composerHeaders (composerId TEXT PRIMARY KEY, workspaceId TEXT,
            createdAt INTEGER, lastUpdatedAt INTEGER, isArchived INTEGER,
            isSubagent INTEGER, recency INTEGER, checkpointAt INTEGER, value TEXT);
        CREATE TABLE cursorDiskKV (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB);
        INSERT INTO composerHeaders (composerId, workspaceId, createdAt, lastUpdatedAt, isSubagent)
        VALUES
        ('abc00000-0000-0000-0000-000000000abc', 'ws1', 1700000, 1900000, 0),
        ('def00000-0000-0000-0000-000000000def', 'ws1', 1750000, NULL, 1),
        ('aaa00000-0000-0000-0000-000000000aaa', 'ws2', 1600000, 1650000, 0);
        INSERT INTO cursorDiskKV (key, value) VALUES
        ('composerData:bbb00000-0000-0000-0000-000000000bbb',
         '{"composerId":"bbb00000-0000-0000-0000-000000000bbb","modelConfig":{"modelName":"claude-4.6-sonnet-medium-thinking","maxMode":false}}'),
        ('composerData:abc00000-0000-0000-0000-000000000abc',
         '{"composerId":"abc00000-0000-0000-0000-000000000abc","modelConfig":{"modelName":"claude-sonnet-4-6","maxMode":false},"workspaceIdentifier":{"uri":{"fsPath":"/work/repo"}}}'),
        ('composerData:aaa00000-0000-0000-0000-000000000aaa',
         '{"composerId":"aaa00000-0000-0000-0000-000000000aaa","modelConfig":{"modelName":"default","maxMode":false}}'),
        ('bubbleId:abc00000-0000-0000-0000-000000000abc:b1',
         '{"tokenCount":{"inputTokens":100,"outputTokens":40}}'),
        ('bubbleId:abc00000-0000-0000-0000-000000000abc:b2',
         '{"tokenCount":{"inputTokens":0,"outputTokens":0}}'),
        ('bubbleId:def00000-0000-0000-0000-000000000def:b1',
         '{"tokenCount":{"inputTokens":7,"outputTokens":3}}');"#,
    )
    .unwrap();
}

#[cfg(any(test, feature = "test-support"))]
pub fn write_codex_state_db_for_test(home: &Path) {
    let codex_dir = home.join(".codex");
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
        );
        INSERT INTO threads
        (id, rollout_path, model, tokens_used, preview, cwd, created_at_ms, updated_at_ms)
        VALUES
        ('019f49ca-54e7-7a91-82e7-a52b53cfd456', '/tmp/session.jsonl', 'gpt-web-ci', 33, 'web state prompt', '/work/repo', 1800000, 1900000);",
    )
    .unwrap();
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
        write_codex_state_db_for_test(temp.path());

        let sessions = codex_state_sessions_in_home(temp.path(), 5);

        assert_eq!(sessions.len(), 1);
        assert_eq!(sessions[0].display_id, "codex:019f49.fd456");
        assert_eq!(sessions[0].model.as_deref(), Some("gpt-web-ci"));
        assert_eq!(sessions[0].usage.total_tokens, 33);
        assert_eq!(
            sessions[0].prompt_preview.as_deref(),
            Some("web state prompt")
        );
        assert_eq!(sessions[0].cwd.as_deref(), Some("/work/repo"));
        assert_eq!(
            sessions[0].last_message_at.as_deref(),
            Some("1970-01-01T00:31:40.000Z")
        );
    }

    #[test]
    fn codex_rollout_summary_cache_tracks_file_metadata() {
        let temp = tempfile::tempdir().unwrap();
        let rollout = temp.path().join("rollout.jsonl");
        fs::write(
            &rollout,
            concat!(
                r#"{"timestamp":"2026-08-13T10:00:00Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":3,"output_tokens":4,"total_tokens":7}},"rate_limits":{"plan_type":"pro","primary":{"used_percent":75.0,"window_minutes":300,"resets_at":1234},"secondary":null,"credits":{"unlimited":false,"balance":"10"},"private_field":"drop"}}}"#,
                "\n",
                r#"{"type":"response_item","payload":{"type":"function_call","name":"update_plan","arguments":"{\"plan\":[{\"step\":\"cached plan\",\"status\":\"in_progress\"}]}"}}"#,
                "\n",
            ),
        )
        .unwrap();

        let first = codex_rollout_summary(&rollout);
        let second = codex_rollout_summary(&rollout);
        assert_eq!(first, second);
        assert_eq!(first.0.unwrap().total_tokens, 7);
        assert_eq!(first.1[0].step, "cached plan");
        assert_eq!(first.2.as_ref().unwrap()["provider"], "codex");
        assert_eq!(
            first.2.as_ref().unwrap()["observed_at"],
            "2026-08-13T10:00:00Z"
        );
        assert_eq!(first.2.as_ref().unwrap()["primary"]["used_percent"], 75.0);
        assert!(
            first.2.as_ref().unwrap()["credits"]
                .get("balance")
                .is_none()
        );
        assert!(first.2.as_ref().unwrap().get("private_field").is_none());
        let session = codex_state_session(
            "session-id".to_string(),
            rollout.to_string_lossy().to_string(),
            Some("gpt-test".to_string()),
            7,
            None,
            None,
            Some(1_000),
            Some(2_000),
        );
        assert_eq!(
            session_row(&session).attributes["subscription"]["provider"],
            "codex"
        );
        assert_eq!(session_row(&session).attributes["usage"]["total_tokens"], 7);
        assert!(codex_summary_cache().lock().unwrap().contains_key(&rollout));

        fs::write(&rollout, "{}\n").unwrap();
        let changed = codex_rollout_summary(&rollout);
        assert!(changed.0.is_none());
        assert!(changed.1.is_empty());
        assert!(changed.2.is_none());
    }

    #[test]
    fn indexed_codex_session_is_hydrated_on_detail_access() {
        let temp = tempfile::tempdir().unwrap();
        let rollout =
            agent_session::fixture_session_path(agent_session::AGENT_CODEX, temp.path()).unwrap();
        fs::create_dir_all(rollout.parent().unwrap()).unwrap();
        fs::write(
            &rollout,
            concat!(
                r#"{"type":"session_meta","payload":{"id":"state-id","cwd":"/parsed"}}"#,
                "\n",
                r#"{"timestamp":"2026-08-13T00:00:00Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"show the full conversation"}]}}"#,
                "\n",
                r#"{"type":"response_item","payload":{"type":"function_call","name":"update_plan","call_id":"p1","arguments":"{\"plan\":[{\"step\":\"render session detail\",\"status\":\"in_progress\"}]}"}}"#,
                "\n",
                r#"{"timestamp":"2026-08-13T00:00:01Z","type":"response_item","payload":{"type":"message","role":"assistant","phase":"final_answer","content":[{"type":"output_text","text":"conversation rendered"}]}}"#,
                "\n",
            ),
        )
        .unwrap();
        let indexed = codex_state_session(
            "state-id".to_string(),
            rollout.to_string_lossy().to_string(),
            Some("gpt-indexed".to_string()),
            42,
            Some("indexed preview".to_string()),
            Some("/indexed".to_string()),
            Some(1_000),
            Some(2_000),
        );
        assert_eq!(indexed.events.plan[0].step, "render session detail");

        let hydrated = hydrate_session(&mut SessionCache::new(), indexed);

        assert_eq!(
            hydrated.events.prompts[0].text,
            "show the full conversation"
        );
        assert_eq!(
            hydrated.events.llm_responses[0].text,
            "conversation rendered"
        );
        assert_eq!(hydrated.events.plan[0].step, "render session detail");
        assert_eq!(hydrated.model.as_deref(), Some("gpt-indexed"));
        assert_eq!(hydrated.cwd.as_deref(), Some("/indexed"));
    }

    #[test]
    fn cursor_state_db_path_checks_platform_layouts() {
        let temp = tempfile::tempdir().unwrap();
        assert!(cursor_state_db_path(temp.path()).is_none());
        write_cursor_state_db_for_test(temp.path());
        let path = cursor_state_db_path(temp.path()).unwrap();
        assert!(path.ends_with("Cursor/User/globalStorage/state.vscdb"));
    }

    #[test]
    fn cursor_state_db_open_is_read_only_and_fails_closed() {
        let temp = tempfile::tempdir().unwrap();
        assert!(open_cursor_state_db(&temp.path().join("missing.vscdb")).is_none());
        write_cursor_state_db_for_test(temp.path());
        let conn = open_cursor_state_db(&cursor_state_db_path(temp.path()).unwrap()).unwrap();
        let denied = conn.execute(
            "INSERT INTO cursorDiskKV (key, value) VALUES ('x', 'y')",
            [],
        );
        assert!(denied.is_err());
    }

    fn cursor_fixture_transcripts(home: &Path) -> PathBuf {
        let transcripts = home
            .join(".cursor/projects/repo/agent-transcripts/abc00000-0000-0000-0000-000000000abc");
        fs::create_dir_all(transcripts.join("subagents")).unwrap();
        let parent = transcripts.join("abc00000-0000-0000-0000-000000000abc.jsonl");
        fs::write(
            &parent,
            r#"{"role":"user","message":{"content":[{"type":"text","text":"check the build"}]}}"#,
        )
        .unwrap();
        fs::write(
            transcripts.join("subagents/def00000-0000-0000-0000-000000000def.jsonl"),
            "{}\n",
        )
        .unwrap();
        parent
    }

    #[test]
    fn cursor_enrichment_fills_metadata_and_rolls_up_subagents() {
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let parent = cursor_fixture_transcripts(temp.path());

        let mut sessions = vec![agent_session::parse_session_path(&parent).expect("parsed")];
        enrich_cursor_sessions_in_home(temp.path(), &mut sessions);

        let session = &sessions[0];
        assert_eq!(session.model.as_deref(), Some("claude-sonnet-4-6"));
        assert_eq!(session.start_timestamp_ms, Some(1_700_000));
        assert_eq!(session.end_timestamp_ms, Some(1_900_000));
        assert_eq!(session.duration_ms, 200_000);
        assert_eq!(session.cwd.as_deref(), Some("/work/repo"));
        assert_eq!(
            session.last_message_at.as_deref(),
            Some("1970-01-01T00:31:40.000Z")
        );
        // 140 from the parent's bubbles plus 10 from the delegated run.
        assert_eq!(session.usage.total_tokens, 150);
        assert_eq!(
            session
                .model_usage
                .get("claude-sonnet-4-6")
                .map(|usage| usage.total_tokens),
            Some(150)
        );
    }

    #[test]
    fn cursor_enrichment_reads_model_when_header_row_is_missing() {
        // Real installs have composerData with no composerHeaders row.
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let transcripts = temp
            .path()
            .join(".cursor/projects/repo/agent-transcripts/bbb00000-0000-0000-0000-000000000bbb");
        fs::create_dir_all(&transcripts).unwrap();
        let parent = transcripts.join("bbb00000-0000-0000-0000-000000000bbb.jsonl");
        fs::write(
            &parent,
            r#"{"role":"user","message":{"content":[{"type":"text","text":"check the build"}]}}"#,
        )
        .unwrap();

        let parsed = agent_session::parse_session_path(&parent).expect("parsed");
        let mut sessions = vec![parsed.clone()];
        enrich_cursor_sessions_in_home(temp.path(), &mut sessions);

        assert_eq!(
            sessions[0].model.as_deref(),
            Some("claude-4.6-sonnet-medium-thinking")
        );
        assert_eq!(sessions[0].start_timestamp_ms, parsed.start_timestamp_ms);
        assert_eq!(sessions[0].end_timestamp_ms, parsed.end_timestamp_ms);
        assert_eq!(sessions[0].last_message_at, parsed.last_message_at);
        assert_eq!(sessions[0].usage.total_tokens, parsed.usage.total_tokens);
    }

    #[test]
    fn cursor_enrichment_missing_db_changes_nothing() {
        let temp = tempfile::tempdir().unwrap();
        let parent = cursor_fixture_transcripts(temp.path());

        let parsed = agent_session::parse_session_path(&parent).expect("parsed");
        let mut sessions = vec![parsed.clone()];
        enrich_cursor_sessions_in_home(temp.path(), &mut sessions);

        assert_eq!(sessions[0].model, parsed.model);
        assert_eq!(sessions[0].usage.total_tokens, parsed.usage.total_tokens);
        assert_eq!(sessions[0].cwd, parsed.cwd);
        assert_eq!(sessions[0].start_timestamp_ms, parsed.start_timestamp_ms);
    }

    #[test]
    fn cursor_enrichment_reads_while_writer_holds_wal() {
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let parent = cursor_fixture_transcripts(temp.path());

        let writer =
            rusqlite::Connection::open(cursor_state_db_path(temp.path()).unwrap()).unwrap();
        writer.execute_batch("BEGIN IMMEDIATE;").unwrap();
        writer
            .execute(
                "INSERT INTO cursorDiskKV (key, value) VALUES ('agentKv:x', 'held open')",
                [],
            )
            .unwrap();

        let mut sessions = vec![agent_session::parse_session_path(&parent).expect("parsed")];
        enrich_cursor_sessions_in_home(temp.path(), &mut sessions);
        writer.execute_batch("ROLLBACK;").unwrap();

        assert_eq!(sessions[0].model.as_deref(), Some("claude-sonnet-4-6"));
        assert_eq!(sessions[0].usage.total_tokens, 150);
    }

    #[test]
    fn cursor_composer_data_reads_model_and_workspace() {
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let conn = open_cursor_state_db(&cursor_state_db_path(temp.path()).unwrap()).unwrap();

        let pinned = cursor_composer_data(&conn, "abc00000-0000-0000-0000-000000000abc")
            .expect("pinned composer");
        assert_eq!(pinned.model.as_deref(), Some("claude-sonnet-4-6"));
        assert_eq!(pinned.workspace_path.as_deref(), Some("/work/repo"));

        let unpinned = cursor_composer_data(&conn, "aaa00000-0000-0000-0000-000000000aaa")
            .expect("default composer");
        assert_eq!(unpinned.model, None);
        assert_eq!(unpinned.workspace_path, None);

        assert!(cursor_composer_data(&conn, "not-a-composer").is_none());
    }

    #[test]
    fn cursor_bubble_tokens_sums_by_bounded_range() {
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let conn = open_cursor_state_db(&cursor_state_db_path(temp.path()).unwrap()).unwrap();

        let parent = cursor_bubble_tokens(&conn, "abc00000-0000-0000-0000-000000000abc");
        assert_eq!(parent.input_tokens, 100);
        assert_eq!(parent.output_tokens, 40);
        assert_eq!(parent.total_tokens, 140);

        let child = cursor_bubble_tokens(&conn, "def00000-0000-0000-0000-000000000def");
        assert_eq!(child.total_tokens, 10);

        let none = cursor_bubble_tokens(&conn, "aaa00000-0000-0000-0000-000000000aaa");
        assert_eq!(none.total_tokens, 0);
    }

    #[test]
    fn cursor_subagent_ids_come_from_directory_layout() {
        let temp = tempfile::tempdir().unwrap();
        let transcripts = temp
            .path()
            .join(".cursor/projects/repo/agent-transcripts/abc");
        fs::create_dir_all(transcripts.join("subagents")).unwrap();
        let parent = transcripts.join("abc.jsonl");
        fs::write(&parent, "{}\n").unwrap();
        fs::write(transcripts.join("subagents/def.jsonl"), "{}\n").unwrap();
        fs::write(transcripts.join("subagents/aaa.jsonl"), "{}\n").unwrap();
        fs::write(transcripts.join("subagents/notes.txt"), "x").unwrap();

        assert_eq!(cursor_subagent_ids(&parent), vec!["aaa", "def"]);
        let no_subagents = temp.path().join("elsewhere/abc.jsonl");
        assert!(cursor_subagent_ids(&no_subagents).is_empty());
    }

    #[test]
    fn cursor_composer_header_reads_parent_and_subagent_rows() {
        let temp = tempfile::tempdir().unwrap();
        write_cursor_state_db_for_test(temp.path());
        let conn = open_cursor_state_db(&cursor_state_db_path(temp.path()).unwrap()).unwrap();

        let parent = cursor_composer_header(&conn, "abc00000-0000-0000-0000-000000000abc")
            .expect("parent header");
        assert_eq!(parent.created_at_ms, Some(1_700_000));
        assert_eq!(parent.updated_at_ms, Some(1_900_000));

        let child = cursor_composer_header(&conn, "def00000-0000-0000-0000-000000000def")
            .expect("subagent header");
        assert_eq!(child.created_at_ms, Some(1_750_000));
        assert_eq!(child.updated_at_ms, None);

        assert!(cursor_composer_header(&conn, "not-a-composer").is_none());
    }

    #[test]
    fn count_session_dirs_reports_cursor_root() {
        let temp = tempfile::tempdir().unwrap();
        assert!(agent_session::count_session_dirs_in_home(temp.path()).is_empty());

        let transcripts = temp
            .path()
            .join(".cursor/projects/repo/agent-transcripts/abc");
        fs::create_dir_all(transcripts.join("subagents")).unwrap();
        fs::write(transcripts.join("abc.jsonl"), "{}\n").unwrap();
        fs::write(transcripts.join("subagents/def.jsonl"), "{}\n").unwrap();

        let stats = agent_session::count_session_dirs_in_home(temp.path());
        assert_eq!(stats.len(), 1);
        assert_eq!(stats[0].agent, agent_session::AGENT_CURSOR);
        assert!(stats[0].dir.ends_with(".cursor/projects"));
        // Parents only: the subagent file folds into its parent session, so it
        // adds neither a session nor bytes.
        assert_eq!(stats[0].sessions, 1);
        assert_eq!(stats[0].bytes, 3);
    }

    #[test]
    fn cursor_discovery_emits_parent_candidates_only() {
        let temp = tempfile::tempdir().unwrap();
        let project = temp.path().join(".cursor/projects/repo");
        let transcripts = project.join("agent-transcripts/abc");
        fs::create_dir_all(transcripts.join("subagents")).unwrap();
        fs::create_dir_all(project.join("canvases/node_modules/pkg")).unwrap();
        fs::write(transcripts.join("abc.jsonl"), "{}\n").unwrap();
        fs::write(transcripts.join("subagents/def.jsonl"), "{}\n").unwrap();
        fs::write(project.join("canvases/node_modules/pkg/data.jsonl"), "{}\n").unwrap();

        let candidates: Vec<_> = agent_session::discover_session_files_in_home(temp.path())
            .into_iter()
            .filter(|candidate| candidate.agent == agent_session::AGENT_CURSOR)
            .collect();

        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].path, transcripts.join("abc.jsonl"));
    }

    #[test]
    fn cursor_candidate_updated_tracks_subagent_writes() {
        let temp = tempfile::tempdir().unwrap();
        let transcripts = temp
            .path()
            .join(".cursor/projects/repo/agent-transcripts/abc");
        fs::create_dir_all(transcripts.join("subagents")).unwrap();
        fs::write(transcripts.join("abc.jsonl"), "{}\n").unwrap();
        let child = transcripts.join("subagents/def.jsonl");
        fs::write(&child, "{}\n").unwrap();

        // Bump only the child's mtime well past the parent's.
        let bumped = std::time::SystemTime::now() + std::time::Duration::from_secs(120);
        let handle = fs::File::options().write(true).open(&child).unwrap();
        handle.set_modified(bumped).unwrap();

        let candidates: Vec<_> = agent_session::discover_session_files_in_home(temp.path())
            .into_iter()
            .filter(|candidate| candidate.agent == agent_session::AGENT_CURSOR)
            .collect();

        assert_eq!(candidates.len(), 1);
        let parent_mtime = fs::metadata(transcripts.join("abc.jsonl"))
            .unwrap()
            .modified()
            .unwrap();
        assert!(candidates[0].updated > parent_mtime);
    }

    #[test]
    fn cursor_duplicate_composer_prefers_real_workspace() {
        let temp = tempfile::tempdir().unwrap();
        let real = temp
            .path()
            .join(".cursor/projects/repo/agent-transcripts/abc");
        let stale = temp
            .path()
            .join(".cursor/projects/empty-window/agent-transcripts/abc");
        fs::create_dir_all(&real).unwrap();
        fs::create_dir_all(&stale).unwrap();
        fs::write(real.join("abc.jsonl"), "{}\n").unwrap();
        fs::write(stale.join("abc.jsonl"), "{}\n{}\n").unwrap();

        let candidates: Vec<_> = agent_session::discover_session_files_in_home(temp.path())
            .into_iter()
            .filter(|candidate| candidate.agent == agent_session::AGENT_CURSOR)
            .collect();

        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].path, real.join("abc.jsonl"));
    }

    #[test]
    fn codex_state_db_uses_rollout_token_usage() {
        let temp = tempfile::tempdir().unwrap();
        write_codex_state_db_for_test(temp.path());
        let rollout = temp.path().join("session.jsonl");
        let mut content = "{}\n".repeat(CODEX_ROLLOUT_TAIL_BYTES as usize / 3 + 1);
        content.push_str(concat!(
            r#"{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":19184,"cached_input_tokens":9984,"output_tokens":11,"total_tokens":19195}}}}"#,
            "\n"
        ));
        fs::write(&rollout, content).unwrap();
        let conn = rusqlite::Connection::open(temp.path().join(".codex/state_5.sqlite")).unwrap();
        conn.execute(
            "UPDATE threads SET rollout_path = ?1, tokens_used = 999999999",
            [rollout.to_string_lossy().as_ref()],
        )
        .unwrap();

        let sessions = codex_state_sessions_in_home(temp.path(), 5);

        assert_eq!(sessions[0].usage.input_tokens, 9_200);
        assert_eq!(sessions[0].usage.cache_read_tokens, 9_984);
        assert_eq!(sessions[0].usage.output_tokens, 11);
        assert_eq!(sessions[0].usage.total_tokens, 19_195);
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

        let projected = observed_session_prompt_rows(&rows);
        assert_eq!(projected[0].comm.as_deref(), Some("node"));
        assert_eq!(projected[0].target.as_deref(), Some("/usr/bin/node"));
        let prompts = projected
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
                comm: Some("codex".to_string()),
                target: Some("/usr/bin/codex".to_string()),
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
