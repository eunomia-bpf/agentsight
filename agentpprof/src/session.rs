use agent_session::{AGENT_CLAUDE, AGENT_CODEX, AgentSession, SessionCandidate};
use anyhow::{Result, anyhow};
use chrono::DateTime;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

#[derive(Debug, Clone)]
pub struct UserRequest {
    pub index: usize,
    pub ts_ms: Option<i64>,
    pub text_hash: String,
    pub preview: String,
    pub tag: String,
}

impl UserRequest {
    pub fn prompt_key(&self) -> String {
        format!("{}:{}", self.index, self.text_hash)
    }
}

#[derive(Debug, Clone)]
pub struct ToolEvent {
    pub ts_ms: Option<i64>,
    pub request_index: usize,
    pub tool_name: String,
    pub category: String,
    pub command: String,
    pub command_name: String,
    pub effect: String,
    pub process_chain: Vec<String>,
    pub status: String,
    pub path_groups: Vec<String>,
    pub domains: Vec<String>,
    pub call_id: Option<String>,
}

#[derive(Debug, Clone)]
pub struct LlmEvent {
    pub ts_ms: Option<i64>,
    pub request_index: usize,
    pub model: String,
    pub text_hash: String,
    pub preview: String,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_tokens: u64,
    pub estimated_tokens: u64,
    pub tag: String,
}

impl LlmEvent {
    pub fn token_components(&self) -> Vec<(&'static str, u64)> {
        const MAX_REPORTED_TOKEN_COMPONENT: u64 = 10_000_000;
        const MAX_ESTIMATED_TOKEN_COMPONENT: u64 = 2_000_000;
        let mut out = Vec::new();
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.input_tokens) {
            out.push(("input", self.input_tokens));
        }
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.output_tokens) {
            out.push(("output", self.output_tokens));
        }
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.cache_tokens) {
            out.push(("cache", self.cache_tokens));
        }
        if out.is_empty() && (1..=MAX_ESTIMATED_TOKEN_COMPONENT).contains(&self.estimated_tokens) {
            out.push(("estimate", self.estimated_tokens));
        }
        if out.is_empty() {
            out.push(("unknown", 1));
        }
        out
    }
}

#[derive(Debug, Clone)]
pub struct SessionRecord {
    pub source: String,
    pub path: PathBuf,
    pub session_id: String,
    pub cwd: String,
    pub agent_role: String,
    pub model: String,
    pub title: String,
    pub start_ts_ms: Option<i64>,
    pub user_requests: Vec<UserRequest>,
    pub tools: Vec<ToolEvent>,
    pub llm_calls: Vec<LlmEvent>,
    pub session_tag: String,
}

impl SessionRecord {
    pub fn request_by_index(&self, index: usize) -> &UserRequest {
        self.user_requests
            .get(index)
            .or_else(|| self.user_requests.last())
            .expect("session has bootstrap prompt")
    }

    pub fn ensure_prompt(&mut self) {
        if self.user_requests.is_empty() {
            self.user_requests.push(UserRequest {
                index: 0,
                ts_ms: self.start_ts_ms,
                text_hash: "bootstrap".to_string(),
                preview: "session bootstrap".to_string(),
                tag: String::new(),
            });
        }
    }
}

pub struct DiscoveryResult {
    pub sessions: Vec<SessionRecord>,
    pub warnings: Vec<String>,
}

pub fn discover_sessions(
    project_root: &Path,
    codex_root: &Path,
    claude_root: &Path,
    session_files: &[PathBuf],
    scan_files: usize,
    max_sessions: usize,
) -> Result<DiscoveryResult> {
    let explicit_files = !session_files.is_empty();
    let mut candidates = if explicit_files {
        session_files
            .iter()
            .filter_map(|path| candidate_from_path(path))
            .collect::<Vec<_>>()
    } else {
        let mut discovered = Vec::<SessionCandidate>::new();
        discovered.extend(
            find_jsonl(claude_root, scan_files)
                .into_iter()
                .filter_map(|path| candidate_from_path(&path)),
        );
        discovered.extend(
            find_jsonl(codex_root, scan_files)
                .into_iter()
                .filter_map(|path| candidate_from_path(&path)),
        );
        discovered
    };
    candidates.sort_by_key(|candidate| {
        std::cmp::Reverse(
            candidate
                .updated
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_millis())
                .unwrap_or(0),
        )
    });
    candidates.truncate(scan_files);
    let mut out = Vec::new();
    let mut warnings = Vec::new();
    for candidate in candidates {
        let path = candidate.path.clone();
        let summary = agent_session::parse_session_file(&candidate);
        if !explicit_files
            && !summary
                .as_ref()
                .map(|session| session_matches_project(session, project_root))
                .unwrap_or(false)
            && !raw_mentions_project(&path, project_root)
        {
            continue;
        }
        let mut session = if let Some(summary) = summary.as_ref() {
            record_from_agent_session(summary)
        } else if let Some(raw) = raw_session_minimal(&path, candidate.agent, project_root, false)?
        {
            raw
        } else {
            continue;
        };
        if let Err(error) = enrich_from_raw(&mut session, project_root) {
            warnings.push(format!(
                "skipped_session path={} error={error}",
                path.display()
            ));
            continue;
        }
        if let Some(summary) = summary.as_ref() {
            apply_agent_session_fallbacks(&mut session, summary);
        }
        session.ensure_prompt();
        if !session.user_requests.is_empty()
            || !session.tools.is_empty()
            || !session.llm_calls.is_empty()
        {
            out.push(session);
        }
        if out.len() >= max_sessions {
            break;
        }
    }
    Ok(DiscoveryResult {
        sessions: out,
        warnings,
    })
}

fn candidate_from_path(path: &Path) -> Option<SessionCandidate> {
    let agent = source_from_path(path)?;
    let updated = path
        .metadata()
        .and_then(|metadata| metadata.modified())
        .unwrap_or(std::time::UNIX_EPOCH);
    Some(SessionCandidate {
        agent,
        path: path.to_path_buf(),
        updated,
    })
}

fn find_jsonl(root: &Path, max_files: usize) -> Vec<PathBuf> {
    if !root.exists() {
        return Vec::new();
    }
    let mut files = WalkDir::new(root)
        .into_iter()
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| entry.into_path())
        .filter(|path| path.extension().and_then(|v| v.to_str()) == Some("jsonl"))
        .collect::<Vec<_>>();
    files.sort_by_key(|path| {
        std::cmp::Reverse(
            path.metadata()
                .and_then(|m| m.modified())
                .ok()
                .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                .map(|d| d.as_millis())
                .unwrap_or(0),
        )
    });
    files.truncate(max_files);
    files
}

fn source_from_path(path: &Path) -> Option<&'static str> {
    if let Some(agent) = agent_session::agent_source_for_path(path) {
        return Some(agent);
    }
    let text = path.to_string_lossy();
    if text.contains("/.codex/") {
        Some(AGENT_CODEX)
    } else if text.contains("/.claude/") {
        Some(AGENT_CLAUDE)
    } else if text.contains("/codex/") && text.contains("sessions") {
        Some(AGENT_CODEX)
    } else if text.contains("/claude/") && text.contains("projects") {
        Some(AGENT_CLAUDE)
    } else {
        None
    }
}

fn session_matches_project(session: &AgentSession, project_root: &Path) -> bool {
    session
        .cwd
        .as_deref()
        .map(|cwd| path_text_matches_project(cwd, project_root))
        .unwrap_or(false)
}

fn path_text_matches_project(raw: &str, project_root: &Path) -> bool {
    let raw = raw.trim();
    if raw.is_empty() {
        return false;
    }
    let project = project_root.to_string_lossy();
    if raw == project || raw.starts_with(&format!("{project}/")) {
        return true;
    }
    Path::new(raw)
        .canonicalize()
        .map(|path| path == project_root)
        .unwrap_or(false)
}

fn raw_mentions_project(path: &Path, project_root: &Path) -> bool {
    fs::read_to_string(path)
        .map(|text| text.contains(&project_root.to_string_lossy().to_string()))
        .unwrap_or(false)
}

fn record_from_agent_session(session: &AgentSession) -> SessionRecord {
    SessionRecord {
        source: session.agent_type.clone(),
        path: session.path.clone(),
        session_id: session.session_id.clone(),
        cwd: session.cwd.clone().unwrap_or_default(),
        agent_role: "agent".to_string(),
        model: session.model.clone().unwrap_or_default(),
        title: String::new(),
        start_ts_ms: session
            .start_timestamp_ms
            .and_then(|value| i64::try_from(value).ok()),
        user_requests: Vec::new(),
        tools: Vec::new(),
        llm_calls: Vec::new(),
        session_tag: String::new(),
    }
}

fn apply_agent_session_fallbacks(record: &mut SessionRecord, session: &AgentSession) {
    if record.user_requests.is_empty() {
        if let Some(prompt) = session.prompt_preview.as_deref() {
            let ts_ms = record.start_ts_ms;
            upsert_prompt(record, ts_ms, prompt);
        }
    }
    if record.tools.is_empty() {
        for (tool, count) in &session.tools {
            for _ in 0..*count {
                record.tools.push(ToolEvent {
                    ts_ms: record.start_ts_ms,
                    request_index: 0,
                    tool_name: tool.clone(),
                    category: tool_category(tool, ""),
                    command: String::new(),
                    command_name: "none".to_string(),
                    effect: "process".to_string(),
                    process_chain: Vec::new(),
                    status: "observed".to_string(),
                    path_groups: session
                        .files
                        .keys()
                        .take(8)
                        .map(|path| path_group(path, Path::new(&record.cwd)))
                        .collect(),
                    domains: Vec::new(),
                    call_id: None,
                });
            }
        }
    }
    if record.llm_calls.is_empty() {
        for (model, usage) in &session.model_usage {
            if usage.total_tokens <= 0 {
                continue;
            }
            record.llm_calls.push(LlmEvent {
                ts_ms: record.start_ts_ms,
                request_index: 0,
                model: model.clone(),
                text_hash: short_hash(&format!("{}:{:?}", session.session_id, usage), 12),
                preview: "session token summary".to_string(),
                input_tokens: nonnegative_u64(usage.input_tokens),
                output_tokens: nonnegative_u64(usage.output_tokens),
                cache_tokens: nonnegative_u64(usage.cache_creation_tokens)
                    + nonnegative_u64(usage.cache_read_tokens),
                estimated_tokens: nonnegative_u64(usage.total_tokens),
                tag: String::new(),
            });
        }
    }
}

fn nonnegative_u64(value: i64) -> u64 {
    u64::try_from(value).unwrap_or(0)
}

fn raw_session_minimal(
    path: &Path,
    source: &str,
    project_root: &Path,
    enforce_project_filter: bool,
) -> Result<Option<SessionRecord>> {
    if enforce_project_filter && source == AGENT_CODEX && !raw_mentions_project(path, project_root)
    {
        return Ok(None);
    }
    Ok(Some(SessionRecord {
        source: source.to_string(),
        path: path.to_path_buf(),
        session_id: path
            .file_stem()
            .and_then(|v| v.to_str())
            .unwrap_or("session")
            .to_string(),
        cwd: String::new(),
        agent_role: "agent".to_string(),
        model: String::new(),
        title: String::new(),
        start_ts_ms: None,
        user_requests: Vec::new(),
        tools: Vec::new(),
        llm_calls: Vec::new(),
        session_tag: String::new(),
    }))
}

fn enrich_from_raw(record: &mut SessionRecord, project_root: &Path) -> Result<()> {
    let file = fs::File::open(&record.path)?;
    let reader = BufReader::new(file);
    let mut current_request = record.user_requests.len().saturating_sub(1);
    let mut call_index = HashMap::<String, usize>::new();
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let Ok(value) = serde_json::from_str::<Value>(&line) else {
            continue;
        };
        let ts_ms = value
            .get("timestamp")
            .and_then(Value::as_str)
            .and_then(parse_ts_ms);
        if record.start_ts_ms.is_none() {
            record.start_ts_ms = ts_ms;
        }
        if record.cwd.is_empty() {
            if let Some(cwd) = value
                .get("cwd")
                .and_then(Value::as_str)
                .or_else(|| value.pointer("/payload/cwd").and_then(Value::as_str))
            {
                record.cwd = cwd.to_string();
            }
        }
        if record.source.starts_with("codex") {
            enrich_codex(
                record,
                project_root,
                &value,
                ts_ms,
                &mut current_request,
                &mut call_index,
            );
        } else if record.source.starts_with("claude") {
            enrich_claude(
                record,
                project_root,
                &value,
                ts_ms,
                &mut current_request,
                &mut call_index,
            );
        }
    }
    if record.user_requests.is_empty() {
        record.ensure_prompt();
    }
    Ok(())
}

fn enrich_codex(
    record: &mut SessionRecord,
    project_root: &Path,
    value: &Value,
    ts_ms: Option<i64>,
    current_request: &mut usize,
    call_index: &mut HashMap<String, usize>,
) {
    let typ = value.get("type").and_then(Value::as_str).unwrap_or("");
    let payload = value.get("payload").unwrap_or(&Value::Null);
    if typ == "session_meta" {
        if let Some(id) = payload
            .get("id")
            .or_else(|| payload.get("session_id"))
            .and_then(Value::as_str)
        {
            record.session_id = id.to_string();
        }
        if let Some(model) = payload.get("model").and_then(Value::as_str) {
            record.model = model.to_string();
        }
        if let Some(cwd) = payload.get("cwd").and_then(Value::as_str) {
            record.cwd = cwd.to_string();
        }
    }
    let ptype = payload.get("type").and_then(Value::as_str).unwrap_or("");
    match (typ, ptype) {
        ("event_msg", "user_message") => {
            let text = payload
                .get("message")
                .or_else(|| payload.get("content"))
                .and_then(Value::as_str)
                .unwrap_or("");
            if !text.trim().is_empty() {
                *current_request = upsert_prompt(record, ts_ms, text);
            }
        }
        ("response_item", "function_call") => {
            let name = payload
                .get("name")
                .or_else(|| payload.get("tool_name"))
                .and_then(Value::as_str)
                .unwrap_or("tool");
            let args = parse_tool_args(payload.get("arguments").unwrap_or(&Value::Null));
            let call_id = payload
                .get("call_id")
                .and_then(Value::as_str)
                .map(str::to_string);
            let event = tool_event_from_input(
                project_root,
                ts_ms,
                *current_request,
                name,
                &args,
                call_id.clone(),
            );
            if let Some(id) = call_id {
                call_index.insert(id, record.tools.len());
            }
            record.tools.push(event);
        }
        ("response_item", "function_call_output") => {
            if let Some(call_id) = payload.get("call_id").and_then(Value::as_str) {
                if let Some(index) = call_index.get(call_id).copied() {
                    let output = payload.get("output").and_then(Value::as_str).unwrap_or("");
                    record.tools[index].status = status_from_output(output).to_string();
                }
            }
        }
        ("response_item", "message") => {
            // Skip individual messages - use token_count events for accurate token data
        }
        ("event_msg", "token_count") | ("event_msg", "token_usage") => {
            let info = payload.get("info").or_else(|| payload.get("usage")).unwrap_or(payload);
            // Use last_token_usage (incremental) instead of total_token_usage (cumulative)
            let token_usage = info.get("last_token_usage")
                .or_else(|| info.get("total_token_usage"))
                .unwrap_or(info);
            let total = json_u64(token_usage, "total_tokens")
                .max(json_u64(info, "total_tokens"))
                .max(json_u64(info, "tokens"));
            if total > 0 {
                record.llm_calls.push(LlmEvent {
                    ts_ms,
                    request_index: *current_request,
                    model: if record.model.is_empty() {
                        "codex".to_string()
                    } else {
                        record.model.clone()
                    },
                    text_hash: short_hash(&token_usage.to_string(), 12),
                    preview: "codex token report".to_string(),
                    input_tokens: json_u64(token_usage, "input_tokens"),
                    output_tokens: json_u64(token_usage, "output_tokens"),
                    cache_tokens: json_u64(token_usage, "cached_input_tokens"),
                    estimated_tokens: total,
                    tag: String::new(),
                });
            }
        }
        _ => {}
    }
}

fn enrich_claude(
    record: &mut SessionRecord,
    project_root: &Path,
    value: &Value,
    ts_ms: Option<i64>,
    current_request: &mut usize,
    call_index: &mut HashMap<String, usize>,
) {
    let typ = value.get("type").and_then(Value::as_str).unwrap_or("");
    if let Some(id) = value.get("sessionId").and_then(Value::as_str) {
        record.session_id = id.to_string();
    }
    if let Some(title) = value.get("aiTitle").and_then(Value::as_str) {
        record.title = title.to_string();
    }
    match typ {
        "user" => {
            let content = value.pointer("/message/content").unwrap_or(&Value::Null);
            if claude_is_tool_result(content) {
                let is_error = value
                    .get("toolUseResult")
                    .and_then(|v| v.get("is_error"))
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                for id in claude_tool_result_ids(content) {
                    if let Some(index) = call_index.get(&id).copied() {
                        record.tools[index].status =
                            if is_error { "fail" } else { "ok" }.to_string();
                    }
                }
            } else {
                let text = content_to_text(content);
                if !text.trim().is_empty() {
                    *current_request = upsert_prompt(record, ts_ms, &text);
                }
            }
        }
        "assistant" => {
            if let Some(model) = value.pointer("/message/model").and_then(Value::as_str) {
                record.model = model.to_string();
            }
            let content = value.pointer("/message/content").unwrap_or(&Value::Null);
            if let Some(items) = content.as_array() {
                for item in items {
                    if item.get("type").and_then(Value::as_str) == Some("tool_use") {
                        let name = item.get("name").and_then(Value::as_str).unwrap_or("tool");
                        let input = item.get("input").unwrap_or(&Value::Null);
                        let id = item.get("id").and_then(Value::as_str).map(str::to_string);
                        let event = tool_event_from_input(
                            project_root,
                            ts_ms,
                            *current_request,
                            name,
                            input,
                            id.clone(),
                        );
                        if let Some(id) = id {
                            call_index.insert(id, record.tools.len());
                        }
                        record.tools.push(event);
                    }
                }
            }
            let text = content_to_text(content);
            let usage = value.pointer("/message/usage").unwrap_or(&Value::Null);
            if !text.trim().is_empty() || usage.is_object() {
                record.llm_calls.push(LlmEvent {
                    ts_ms,
                    request_index: *current_request,
                    model: if record.model.is_empty() {
                        "claude".to_string()
                    } else {
                        record.model.clone()
                    },
                    text_hash: short_hash(&(text.clone() + &usage.to_string()), 12),
                    preview: truncate_clean(
                        if text.trim().is_empty() {
                            "claude response"
                        } else {
                            &text
                        },
                        140,
                    ),
                    input_tokens: json_u64(usage, "input_tokens"),
                    output_tokens: json_u64(usage, "output_tokens"),
                    cache_tokens: json_u64(usage, "cache_creation_input_tokens")
                        + json_u64(usage, "cache_read_input_tokens"),
                    estimated_tokens: 0,
                    tag: String::new(),
                });
            }
        }
        "last-prompt" if record.user_requests.is_empty() => {
            if let Some(text) = value.get("lastPrompt").and_then(Value::as_str) {
                *current_request = upsert_prompt(record, ts_ms, text);
            }
        }
        _ => {}
    }
}

pub fn upsert_prompt(record: &mut SessionRecord, ts_ms: Option<i64>, text: &str) -> usize {
    let hash = short_hash(text, 12);
    if let Some(existing) = record
        .user_requests
        .iter()
        .position(|req| req.text_hash == hash)
    {
        return existing;
    }
    let index = record.user_requests.len();
    record.user_requests.push(UserRequest {
        index,
        ts_ms,
        text_hash: hash,
        preview: truncate_clean(text, 180),
        tag: String::new(),
    });
    index
}

fn tool_event_from_input(
    project_root: &Path,
    ts_ms: Option<i64>,
    request_index: usize,
    name: &str,
    input: &Value,
    call_id: Option<String>,
) -> ToolEvent {
    let command = command_from_tool_input(input);
    let category = tool_category(name, &command);
    let domains = extract_domains(&command);
    let command_name = if category == "shell" {
        basename_from_command(&command)
    } else if category == "network" && !domains.is_empty() {
        domains[0]
            .split(':')
            .next()
            .unwrap_or("network")
            .to_string()
    } else {
        one_word(name, "tool")
    };
    let effect = if name == "apply_patch" || command.contains("*** ") {
        "write".to_string()
    } else {
        command_effect(&command)
    };
    let path_groups = extract_path_groups(project_root, name, input, &command);
    let process_chain = if category == "shell" {
        command_process_chain(&command)
    } else {
        Vec::new()
    };
    ToolEvent {
        ts_ms,
        request_index,
        tool_name: name.to_string(),
        category,
        command,
        command_name,
        effect,
        process_chain,
        status: "observed".to_string(),
        path_groups,
        domains,
        call_id,
    }
}

fn command_from_tool_input(input: &Value) -> String {
    for key in ["cmd", "command", "pattern", "file_path", "path", "text"] {
        if let Some(value) = input.get(key).and_then(Value::as_str) {
            if !value.is_empty() {
                return if key == "pattern" {
                    format!("search {value}")
                } else {
                    value.to_string()
                };
            }
        }
    }
    if input.is_null() {
        String::new()
    } else {
        truncate_clean(&input.to_string(), 300)
    }
}

fn parse_tool_args(value: &Value) -> Value {
    if let Some(text) = value.as_str() {
        serde_json::from_str(text).unwrap_or_else(|_| serde_json::json!({ "text": text }))
    } else {
        value.clone()
    }
}

fn status_from_output(output: &str) -> &'static str {
    let lowered = output.to_ascii_lowercase();
    if lowered.contains("process exited with code 0") || lowered.contains("\"is_error\":false") {
        "ok"
    } else if lowered.contains("process exited with code")
        || lowered.contains("\"is_error\":true")
        || lowered.contains("error")
    {
        "fail"
    } else {
        "observed"
    }
}

pub fn tool_category(name: &str, command: &str) -> String {
    let n = name.to_ascii_lowercase();
    if n.ends_with("exec_command") || n == "bash" {
        "shell"
    } else if ["apply_patch", "edit", "write", "multiedit", "notebookedit"].contains(&n.as_str()) {
        "edit"
    } else if ["read", "grep", "glob", "ls"].contains(&n.as_str()) {
        "read"
    } else if n.contains("web")
        || n.contains("browser")
        || n.contains("search")
        || command.contains("http")
    {
        "network"
    } else if n.contains("plan") || n.contains("todo") {
        "plan"
    } else if n.contains("task") || n.contains("agent") {
        "subagent"
    } else {
        "tool"
    }
    .to_string()
}

fn command_effect(command: &str) -> String {
    let cmd = basename_from_command(command);
    let text = command.to_ascii_lowercase();
    if ["cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"].contains(&cmd.as_str())
        && any_word(&text, &["test", "check", "build", "clippy"])
    {
        "test"
    } else if cmd == "git"
        && any_word(
            &text,
            &["commit", "push", "add", "checkout", "merge", "rebase"],
        )
    {
        "repo"
    } else if ["curl", "wget", "ssh", "scp", "git"].contains(&cmd.as_str())
        && (any_word(
            &text,
            &["clone", "fetch", "pull", "push", "curl", "wget", "ssh"],
        ) || text.contains("http://")
            || text.contains("https://"))
    {
        "network"
    } else if [
        "tee", "cp", "mv", "rm", "mkdir", "touch", "python", "python3", "node", "npm",
    ]
    .contains(&cmd.as_str())
        && (text.contains('>')
            || text.contains("--write")
            || text.contains(" rm ")
            || text.contains(" mkdir ")
            || text.contains(" touch ")
            || text.contains(" cp ")
            || text.contains(" mv "))
    {
        "write"
    } else if [
        "rg", "grep", "sed", "cat", "head", "tail", "find", "ls", "nl", "wc", "jq", "git",
    ]
    .contains(&cmd.as_str())
    {
        "read"
    } else if text.contains("http://")
        || text.contains("https://")
        || text.contains("crates.io")
        || text.contains("github.com")
    {
        "network"
    } else {
        "process"
    }
    .to_string()
}

fn any_word(text: &str, words: &[&str]) -> bool {
    text.split(|c: char| !c.is_ascii_alphanumeric() && c != '_')
        .any(|part| words.contains(&part))
}

fn basename_from_command(command: &str) -> String {
    let parts = split_shell(command);
    let mut idx = 0;
    while idx < parts.len()
        && ["sudo", "env", "command", "time", "timeout", "nice", "nohup"].contains(
            &Path::new(&parts[idx])
                .file_name()
                .and_then(|v| v.to_str())
                .unwrap_or(""),
        )
    {
        idx += 1;
        if idx < parts.len() && parts[idx].starts_with('-') {
            idx += 1;
        }
    }
    parts
        .get(idx)
        .and_then(|part| process_name_from_part(part))
        .unwrap_or_else(|| "none".to_string())
}

pub fn command_process_chain(command: &str) -> Vec<String> {
    process_chain_from_parts(&split_shell(command))
}

fn process_chain_from_parts(parts: &[String]) -> Vec<String> {
    if parts.is_empty() {
        return Vec::new();
    }
    let mut idx = 0;
    while idx < parts.len()
        && ["sudo", "env", "command", "time", "timeout", "nice", "nohup"].contains(
            &Path::new(&parts[idx])
                .file_name()
                .and_then(|v| v.to_str())
                .unwrap_or(""),
        )
    {
        idx += 1;
        if idx < parts.len() && parts[idx].starts_with('-') {
            idx += 1;
        }
    }
    let Some(proc_name) = parts.get(idx).and_then(|part| process_name_from_part(part)) else {
        return Vec::new();
    };
    let mut chain = vec![proc_name.clone()];
    if ["bash", "sh", "zsh"].contains(&proc_name.as_str()) {
        for flag_idx in idx + 1..parts.len().saturating_sub(1) {
            if ["-c", "-lc", "-cl"].contains(&parts[flag_idx].as_str()) {
                chain.extend(command_process_chain(&parts[flag_idx + 1]));
                break;
            }
        }
    }
    chain.truncate(6);
    chain
}

fn process_name_from_part(part: &str) -> Option<String> {
    let raw = part.trim_matches(['"', '\'']);
    if raw.is_empty() {
        return None;
    }
    let path = Path::new(raw);
    let file_name = path.file_name().and_then(|v| v.to_str()).unwrap_or(raw);
    let parts = path_component_strings(path);
    if looks_like_home_directory(&parts) && parts.len() <= 2 {
        return Some("external".to_string());
    }
    if contains_private_marker(file_name) {
        return Some("external".to_string());
    }
    Some(file_name.to_string())
}

fn split_shell(command: &str) -> Vec<String> {
    shell_words::split(command)
        .unwrap_or_else(|_| command.split_whitespace().map(str::to_string).collect())
}

fn extract_domains(text: &str) -> Vec<String> {
    use std::collections::BTreeSet;
    let mut domains = BTreeSet::new();
    for part in text.split(|c: char| c.is_whitespace() || ['"', '\'', ')', '('].contains(&c)) {
        let stripped = part
            .strip_prefix("https://")
            .or_else(|| part.strip_prefix("http://"));
        if let Some(rest) = stripped {
            if let Some(domain) = rest.split('/').next() {
                if !domain.is_empty() {
                    domains.insert(domain.to_ascii_lowercase());
                }
            }
        }
        for known in [
            "github.com",
            "crates.io",
            "huggingface.co",
            "hf.co",
            "openai.com",
            "anthropic.com",
        ] {
            if part.contains(known) {
                domains.insert(known.to_string());
            }
        }
    }
    domains.into_iter().take(8).collect()
}

fn extract_path_groups(
    project_root: &Path,
    name: &str,
    input: &Value,
    command: &str,
) -> Vec<String> {
    use std::collections::BTreeSet;
    let mut groups = BTreeSet::new();
    if ["write", "edit", "multiedit", "notebookedit", "read"]
        .contains(&name.to_ascii_lowercase().as_str())
    {
        for key in ["file_path", "path"] {
            if let Some(path) = input.get(key).and_then(Value::as_str) {
                groups.insert(path_group(path, project_root));
            }
        }
    }
    for part in split_shell(command) {
        if plausible_path_token(&part) {
            groups.insert(path_group(&part, project_root));
        }
    }
    groups.into_iter().filter(|v| v != "none").take(8).collect()
}

fn plausible_path_token(part: &str) -> bool {
    let part = part.trim_matches(['"', '\'']);
    if part.is_empty()
        || part.starts_with('-')
        || part.starts_with('$')
        || part.starts_with("http://")
        || part.starts_with("https://")
        || part.len() > 140
        || part.chars().any(|c| "{}()=;<>|`".contains(c))
    {
        return false;
    }
    let suffix = Path::new(part)
        .extension()
        .and_then(|v| v.to_str())
        .unwrap_or("");
    part.contains('/')
        || [
            "rs", "py", "md", "json", "ts", "tsx", "toml", "lock", "js", "c", "h", "svg", "html",
            "css",
        ]
        .contains(&suffix)
}

pub fn path_group(path: &str, project_root: &Path) -> String {
    let path = path.trim_matches(['"', '\'']);
    if path.is_empty() {
        return "none".to_string();
    }
    let p = Path::new(path);
    let parts = if p.is_absolute() {
        if let Ok(rel) = p.strip_prefix(project_root) {
            path_component_strings(rel)
        } else {
            return external_path_group(path, &path_component_strings(p));
        }
    } else {
        let parts = path_component_strings(p);
        if let Some(group) = sensitive_relative_path_group(path, &parts) {
            return group;
        }
        parts
    };
    collapse_project_path(parts)
}

pub fn path_component_strings(path: &Path) -> Vec<String> {
    path.components()
        .filter_map(|c| {
            let part = c.as_os_str().to_string_lossy();
            let part = part.as_ref();
            if part == "." || part == "/" || part.is_empty() {
                None
            } else {
                Some(part.to_string())
            }
        })
        .collect()
}

pub fn collapse_project_path(parts: Vec<String>) -> String {
    let parts = parts
        .into_iter()
        .filter(|part| part != "." && !part.is_empty())
        .map(|part| truncate_path_component(&part))
        .collect::<Vec<_>>();
    if parts.is_empty() {
        "repo".to_string()
    } else if ["collector", "frontend", "docs", "bpf", "agentpprof"].contains(&parts[0].as_str()) {
        parts.into_iter().take(3).collect::<Vec<_>>().join("/")
    } else {
        parts.into_iter().take(2).collect::<Vec<_>>().join("/")
    }
}

fn truncate_path_component(part: &str) -> String {
    if part.chars().count() > 48 {
        format!("{}...", part.chars().take(45).collect::<String>())
    } else {
        part.to_string()
    }
}

fn external_path_group(raw: &str, parts: &[String]) -> String {
    sensitive_relative_path_group(raw, parts).unwrap_or_else(|| "external/path".to_string())
}

fn sensitive_relative_path_group(raw: &str, parts: &[String]) -> Option<String> {
    let lowered = raw.to_ascii_lowercase();
    let lower_parts = parts
        .iter()
        .map(|part| part.to_ascii_lowercase())
        .collect::<Vec<_>>();
    if lower_parts.iter().any(|part| part == ".codex") {
        Some("external/codex".to_string())
    } else if lower_parts.iter().any(|part| part == ".claude") {
        Some("external/claude".to_string())
    } else if lower_parts.first().is_some_and(|part| part == "tmp")
        || lowered.contains("/tmp")
        || lowered.contains("_/tmp")
        || lower_parts
            .windows(2)
            .any(|window| window[0] == "var" && window[1] == "tmp")
    {
        Some("external/tmp".to_string())
    } else if lowered.starts_with("~/")
        || lowered == "~"
        || lowered.contains("/home")
        || lowered.contains("_/home")
        || lowered.contains("-home-")
        || lowered.contains("/users")
        || lowered.contains("_/users")
        || looks_like_home_directory(&lower_parts)
        || contains_private_marker(&lowered)
    {
        Some("external/home".to_string())
    } else {
        None
    }
}

pub fn looks_like_home_directory(parts: &[String]) -> bool {
    parts
        .first()
        .is_some_and(|part| part == "home" || part == "users")
}

fn current_username() -> Option<String> {
    dirs::home_dir()
        .and_then(|home| {
            home.file_name()
                .map(|part| part.to_string_lossy().to_string())
        })
        .filter(|name| !name.is_empty())
}

pub fn contains_private_marker(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    current_username()
        .map(|name| lowered.contains(&name.to_ascii_lowercase()))
        .unwrap_or(false)
}

fn content_to_text(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Array(items) => items
            .iter()
            .filter_map(|item| {
                if let Some(text) = item.as_str() {
                    return Some(text.to_string());
                }
                let typ = item.get("type").and_then(Value::as_str).unwrap_or("");
                if typ == "tool_result" {
                    return None;
                }
                item.get("text")
                    .or_else(|| item.get("content"))
                    .and_then(Value::as_str)
                    .map(str::to_string)
            })
            .collect::<Vec<_>>()
            .join("\n"),
        Value::Object(_) => value
            .get("text")
            .or_else(|| value.get("content"))
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string(),
        _ => String::new(),
    }
}

fn claude_is_tool_result(content: &Value) -> bool {
    content.as_array().is_some_and(|items| {
        !items.is_empty()
            && items
                .iter()
                .all(|item| item.get("type").and_then(Value::as_str) == Some("tool_result"))
    })
}

fn claude_tool_result_ids(content: &Value) -> Vec<String> {
    content
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|item| {
            item.get("tool_use_id")
                .and_then(Value::as_str)
                .map(str::to_string)
        })
        .collect()
}

pub fn default_claude_root(project_root: &Path) -> Result<PathBuf> {
    let _ = project_root;
    dirs::home_dir()
        .map(|home| home.join(".claude/projects"))
        .ok_or_else(|| anyhow!("cannot determine home directory"))
}

fn json_u64(value: &Value, key: &str) -> u64 {
    value.get(key).and_then(Value::as_u64).unwrap_or(0)
}

fn parse_ts_ms(value: &str) -> Option<i64> {
    DateTime::parse_from_rfc3339(value)
        .ok()
        .map(|dt| dt.timestamp_millis())
}

pub fn short_hash(text: &str, n: usize) -> String {
    let digest = Sha256::digest(text.as_bytes());
    hex::encode(digest).chars().take(n).collect()
}

pub fn truncate_clean(text: &str, limit: usize) -> String {
    let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if text.chars().count() <= limit {
        return text;
    }
    text.chars()
        .take(limit.saturating_sub(1))
        .collect::<String>()
        + "."
}

pub fn one_word(text: &str, default: &str) -> String {
    let mut cur = String::new();
    for ch in text.to_ascii_lowercase().chars() {
        if ch.is_ascii_alphanumeric() {
            cur.push(ch);
        } else if cur.len() >= 2 {
            break;
        } else {
            cur.clear();
        }
    }
    if cur.len() >= 2 {
        cur
    } else {
        default.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn command_process_chain_keeps_shell_wrapper_nesting() {
        assert_eq!(
            command_process_chain("bash -lc 'cargo test --manifest-path collector/Cargo.toml'"),
            vec!["bash".to_string(), "cargo".to_string()]
        );
    }

    #[test]
    fn external_paths_are_redacted_to_stable_groups() {
        let root = Path::new("/repo");
        assert_eq!(
            path_group("/repo/docs/flamegraph/README.md", root),
            "docs/flamegraph/README.md"
        );
        assert_eq!(
            path_group("/home/someone/.codex/sessions/session.jsonl", root),
            "external/codex"
        );
        assert_eq!(
            path_group("/Users/someone/.claude/projects/run.jsonl", root),
            "external/claude"
        );
        assert_eq!(
            path_group("/tmp/agentsight-run/out.json", root),
            "external/tmp"
        );
        assert_eq!(path_group("~/workspace/private.txt", root), "external/home");
    }

    #[test]
    fn process_names_do_not_expose_home_directory_components() {
        assert_eq!(
            process_name_from_part("/home/someone/.local/bin/claude"),
            Some("claude".to_string())
        );
        assert_eq!(
            process_name_from_part("/home/someone"),
            Some("external".to_string())
        );
    }

    #[test]
    fn token_components_do_not_stack_estimates_on_reported_tokens() {
        let mut call = LlmEvent {
            ts_ms: None,
            request_index: 0,
            model: "model".to_string(),
            text_hash: "h".to_string(),
            preview: "preview".to_string(),
            input_tokens: 10,
            output_tokens: 5,
            cache_tokens: 0,
            estimated_tokens: 1_000,
            tag: "answer".to_string(),
        };
        assert_eq!(call.token_components(), vec![("input", 10), ("output", 5)]);

        call.input_tokens = 0;
        call.output_tokens = 0;
        call.estimated_tokens = 5_000_000;
        assert_eq!(call.token_components(), vec![("unknown", 1)]);
    }
}
