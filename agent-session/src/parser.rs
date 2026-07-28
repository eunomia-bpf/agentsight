// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Session file parsing for Claude Code, Codex, and Gemini CLI.

use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::types::{
    AgentSession, LlmResponse, SessionCandidate, SessionDirStat, SessionEvents, TokenUsage,
    ToolEvent, UserPrompt,
};
use crate::{AGENT_CLAUDE, AGENT_CODEX, AGENT_GEMINI};

/// Discover all session files in the user's home directory.
pub fn discover_session_files() -> Vec<SessionCandidate> {
    user_home_dir()
        .as_deref()
        .map(discover_session_files_in_home)
        .unwrap_or_default()
}

/// Discover session files under a specific home directory.
pub fn discover_session_files_in_home(home: &Path) -> Vec<SessionCandidate> {
    let roots = [
        (AGENT_CLAUDE, home.join(".claude/projects")),
        (AGENT_CODEX, home.join(".codex/sessions")),
        (AGENT_GEMINI, home.join(".gemini/tmp")),
    ];
    let mut out = Vec::new();
    for (agent, dir) in roots {
        walk_agent_files(agent, &dir, &mut |path, meta| {
            out.push(SessionCandidate {
                agent,
                path: path.to_path_buf(),
                updated: meta.modified().unwrap_or(UNIX_EPOCH),
            });
        });
    }
    out
}

pub fn discover_session_files_in_dir(agent: &'static str, dir: &Path) -> Vec<SessionCandidate> {
    let mut out = Vec::new();
    walk_agent_files(agent, dir, &mut |path, meta| {
        out.push(SessionCandidate {
            agent,
            path: path.to_path_buf(),
            updated: meta.modified().unwrap_or(UNIX_EPOCH),
        });
    });
    out
}

/// Count sessions and bytes per agent directory.
pub fn count_session_dirs() -> Vec<SessionDirStat> {
    let Some(home) = user_home_dir() else {
        return Vec::new();
    };
    [
        (AGENT_CLAUDE, home.join(".claude/projects")),
        (AGENT_CODEX, home.join(".codex/sessions")),
        (AGENT_GEMINI, home.join(".gemini/tmp")),
    ]
    .into_iter()
    .filter_map(|(agent, dir)| {
        let (mut sessions, mut bytes) = (0usize, 0u64);
        walk_agent_files(agent, &dir, &mut |_, meta| {
            sessions += 1;
            bytes += meta.len();
        });
        (sessions > 0).then_some(SessionDirStat {
            agent,
            dir,
            sessions,
            bytes,
        })
    })
    .collect()
}

pub fn session_candidate_from_path(path: &Path) -> Option<SessionCandidate> {
    let agent = agent_source_for_path(path).or_else(|| loose_agent_source_for_path(path))?;
    let updated = fs::metadata(path)
        .and_then(|metadata| metadata.modified())
        .unwrap_or(UNIX_EPOCH);
    Some(SessionCandidate {
        agent,
        path: path.to_path_buf(),
        updated,
    })
}

/// Parse a session file from a candidate.
pub fn parse_session_file(candidate: &SessionCandidate) -> Option<AgentSession> {
    let content = fs::read_to_string(&candidate.path).ok()?;
    parse_session_content(
        candidate.agent,
        &candidate.path,
        candidate.updated,
        &content,
    )
}

/// Parse a session file by path, detecting the agent type automatically.
pub fn parse_session_path(path: &Path) -> Option<AgentSession> {
    parse_session_file(&session_candidate_from_path(path)?)
}

/// Parse session content given raw content string.
pub fn parse_session_content(
    agent: &str,
    path: &Path,
    updated: SystemTime,
    content: &str,
) -> Option<AgentSession> {
    parse_session_impl(agent, path, updated, content)
}

fn parse_session_impl(
    agent: &str,
    path: &Path,
    updated: SystemTime,
    content: &str,
) -> Option<AgentSession> {
    if agent == AGENT_GEMINI {
        parse_gemini_json(path, updated, content)
    } else {
        parse_jsonl(agent, path, updated, content)
    }
}

/// Extract a session log path from a string (e.g., from /proc/fd).
pub fn session_log_path_from_str(raw: &str) -> Option<PathBuf> {
    let trimmed = raw.trim().trim_end_matches(" (deleted)");
    if trimmed.is_empty() {
        return None;
    }
    let path = Path::new(trimmed);
    if !path.is_absolute() || !is_agent_session_file(path) {
        return None;
    }
    agent_source_for_path(path).map(|_| normalize_session_log_path(path))
}

/// Canonicalize a session log path.
pub fn normalize_session_log_path(path: &Path) -> PathBuf {
    fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf())
}

/// Detect which agent a session file belongs to based on its path.
pub fn agent_source_for_path(path: &Path) -> Option<&'static str> {
    let value = path.to_string_lossy();
    if value.contains("/.claude/") && path.extension().and_then(|ext| ext.to_str()) == Some("jsonl")
    {
        Some(AGENT_CLAUDE)
    } else if value.contains("/.codex/")
        && path.extension().and_then(|ext| ext.to_str()) == Some("jsonl")
    {
        Some(AGENT_CODEX)
    } else if value.contains("/.gemini/")
        && path.extension().and_then(|ext| ext.to_str()) == Some("json")
    {
        Some(AGENT_GEMINI)
    } else {
        None
    }
}

fn loose_agent_source_for_path(path: &Path) -> Option<&'static str> {
    let value = path.to_string_lossy();
    if value.contains("/codex/") && value.contains("sessions") {
        Some(AGENT_CODEX)
    } else if value.contains("/claude/") && value.contains("projects") {
        Some(AGENT_CLAUDE)
    } else {
        None
    }
}

/// Generate a fixture session path for testing.
pub fn fixture_session_path(agent: &str, home: &Path) -> Option<PathBuf> {
    match agent {
        AGENT_CLAUDE => Some(home.join(".claude/projects/test/session.jsonl")),
        AGENT_CODEX => Some(home.join(".codex/sessions/2026/06/02/session.jsonl")),
        AGENT_GEMINI => Some(home.join(".gemini/tmp/test/chats/session-test.json")),
        _ => None,
    }
}

/// Check if a target path is the Codex CLI entrypoint.
pub fn is_codex_cli_entrypoint(target: Option<&str>) -> bool {
    target.is_some_and(|target| {
        Path::new(target).file_name().and_then(|name| name.to_str()) == Some("codex")
            && !target.contains("/node_modules/")
    })
}

/// Extract the prompt from a Codex exec command.
pub fn codex_exec_prompt(command: &str) -> Option<String> {
    let mut args = command.split_once(" exec ")?.1.trim();
    while let Some(rest) = strip_codex_exec_option(args) {
        args = rest.trim_start();
    }
    (!args.starts_with('-'))
        .then(|| args.trim_matches(['"', '\'']))
        .and_then(clean_prompt_text)
}

// ---------------------------------------------------------------------------
// Internal parsing implementation
// ---------------------------------------------------------------------------

#[derive(Default)]
struct SemanticTaskStack {
    root: Option<String>,
    active_plan: Option<String>,
}

impl SemanticTaskStack {
    fn observe_user(&mut self, text: &str) {
        let label = semantic_task_label(text);
        if self.root.is_some() && is_continuation_prompt(&label) {
            return;
        }
        self.root = Some(label);
        self.active_plan = None;
    }

    fn observe_plan(&mut self, input: &Value) {
        let active = input
            .get("plan")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|item| {
                (item.get("status").and_then(Value::as_str) == Some("in_progress"))
                    .then(|| item.get("step").and_then(Value::as_str))
                    .flatten()
                    .map(semantic_task_label)
            })
            .collect::<Vec<_>>();
        self.active_plan = match active.as_slice() {
            [] => None,
            [only] => Some(only.clone()),
            many => self
                .active_plan
                .as_ref()
                .filter(|current| many.contains(current))
                .cloned()
                .or_else(|| many.first().cloned()),
        };
    }

    fn path(&self) -> Vec<String> {
        self.root
            .iter()
            .chain(self.active_plan.iter())
            .cloned()
            .collect()
    }

    fn path_for_tool(&self, name: &str, input: &Value) -> Vec<String> {
        let mut path = self.path();
        if name == "spawn_agent"
            && let Some(label) = input
                .get("task_name")
                .or_else(|| input.get("message"))
                .and_then(Value::as_str)
        {
            path.push(semantic_task_label(label));
        }
        path
    }
}

pub fn semantic_task_label(text: &str) -> String {
    let mut selected = text.trim();
    if let Some(start) = selected.rfind("## My request for Codex:") {
        selected = &selected[start + "## My request for Codex:".len()..];
    } else if let Some(start) = selected.find("<objective>")
        && let Some(end) = selected[start + "<objective>".len()..].find("</objective>")
    {
        selected = &selected[start + "<objective>".len()..start + "<objective>".len() + end];
    }
    let label = truncate_clean(selected.trim_matches(['\'', '"']), 120);
    if label.is_empty() {
        "unnamed task".to_string()
    } else {
        label
    }
}

fn is_continuation_prompt(text: &str) -> bool {
    let lowered = text.trim().to_lowercase();
    matches!(
        lowered.as_str(),
        "继续"
            | "继续做"
            | "去做"
            | "开始"
            | "嗯"
            | "好"
            | "好的"
            | "continue"
            | "go on"
            | "proceed"
            | "do it"
            | "ok"
            | "okay"
    )
}

fn parse_jsonl(
    agent: &str,
    path: &Path,
    updated: SystemTime,
    content: &str,
) -> Option<AgentSession> {
    let mut acc = SessionAccumulator::new(agent, path, updated);
    let mut codex_model = String::new();
    let mut claude_message_models = BTreeMap::<String, TokenUsage>::new();
    let mut claude_seen_usage = HashSet::new();
    let mut events = SessionEvents::default();
    let mut current_prompt_index = 0usize;
    let mut call_index = BTreeMap::<String, usize>::new();
    let mut task_stack = SemanticTaskStack::default();
    let mut codex_meta_seen = false;
    let mut codex_owns_events = true;
    let mut codex_session_started_at = 0.0_f64;

    for line in content.lines() {
        let Ok(obj) = serde_json::from_str::<Value>(line) else {
            continue;
        };
        let typ = obj.get("type").and_then(Value::as_str).unwrap_or("");
        if agent == AGENT_CODEX && typ == "session_meta" {
            if !codex_meta_seen {
                codex_meta_seen = true;
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                if let Some(id) = payload
                    .get("id")
                    .or_else(|| payload.get("session_id"))
                    .and_then(Value::as_str)
                {
                    acc.session_id = id.to_string();
                }
                acc.conversation_id = payload
                    .get("session_id")
                    .and_then(Value::as_str)
                    .map(str::to_string);
                let parent = payload
                    .get("parent_thread_id")
                    .or_else(|| payload.get("forked_from_id"))
                    .and_then(Value::as_str)
                    .or_else(|| {
                        payload
                            .pointer("/source/subagent/thread_spawn/parent_thread_id")
                            .and_then(Value::as_str)
                    });
                codex_owns_events = parent.is_none_or(str::is_empty);
                codex_session_started_at = payload
                    .get("timestamp")
                    .or_else(|| obj.get("timestamp"))
                    .and_then(Value::as_str)
                    .and_then(rfc3339_seconds)
                    .unwrap_or_default();
                if acc.cwd.is_none() {
                    acc.cwd = payload
                        .get("cwd")
                        .and_then(Value::as_str)
                        .filter(|cwd| !cwd.is_empty())
                        .map(str::to_string);
                }
            }
            continue;
        }
        if agent == AGENT_CODEX && !codex_owns_events {
            let payload = obj.get("payload").unwrap_or(&Value::Null);
            if typ == "event_msg"
                && payload.get("type").and_then(Value::as_str) == Some("task_started")
            {
                let source_start = payload
                    .get("started_at")
                    .and_then(Value::as_f64)
                    .filter(|value| *value > 0.0)
                    .or_else(|| {
                        payload
                            .get("turn_id")
                            .and_then(Value::as_str)
                            .and_then(uuid7_seconds)
                    })
                    .unwrap_or_default();
                if source_start > 0.0
                    && (codex_session_started_at == 0.0
                        || source_start >= codex_session_started_at.floor())
                {
                    codex_owns_events = true;
                }
            }
            continue;
        }
        let (session_id, conversation_id) = local_session_ids(&obj);
        if let Some(id) = session_id {
            acc.session_id = id;
        }
        if let Some(id) = conversation_id {
            acc.conversation_id = Some(id);
        }
        if acc.cwd.is_none() {
            acc.cwd = obj
                .get("cwd")
                .and_then(Value::as_str)
                .or_else(|| obj.pointer("/payload/cwd").and_then(Value::as_str))
                .filter(|s| !s.is_empty())
                .map(ToString::to_string);
        }
        if let Some(ts) = obj.get("timestamp").and_then(Value::as_str) {
            acc.last_message_at = Some(ts.to_string());
            acc.end_timestamp_ms = iso_ms(ts).or(acc.end_timestamp_ms);
        }
        match (agent, typ) {
            (AGENT_CLAUDE, "result") => {
                acc.duration_ms = json_u64(&obj, "duration_ms");
                if let Some(model_usage) = obj.get("modelUsage").and_then(Value::as_object) {
                    for (name, usage) in model_usage {
                        acc.model.get_or_insert_with(|| name.clone());
                        acc.add_usage(
                            name,
                            json_i64(usage, "inputTokens"),
                            json_i64(usage, "outputTokens"),
                            json_i64(usage, "cacheCreationInputTokens"),
                            json_i64(usage, "cacheReadInputTokens"),
                            0,
                        );
                    }
                }
            }
            (AGENT_CLAUDE, "assistant") => {
                if let Some(name) = obj.pointer("/message/model").and_then(Value::as_str) {
                    acc.model.get_or_insert_with(|| name.to_string());
                }
                let model = obj
                    .pointer("/message/model")
                    .and_then(Value::as_str)
                    .or(acc.model.as_deref())
                    .unwrap_or(AGENT_CLAUDE)
                    .to_string();
                if let Some(usage) = obj.pointer("/message/usage")
                    && claude_seen_usage.insert(claude_usage_key(&obj))
                {
                    let name = obj
                        .pointer("/message/model")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown");
                    add_usage(
                        &mut claude_message_models,
                        name,
                        json_i64(usage, "input_tokens"),
                        json_i64(usage, "output_tokens"),
                        json_i64(usage, "cache_creation_input_tokens"),
                        json_i64(usage, "cache_read_input_tokens"),
                        0,
                    );
                }
                let content = obj.pointer("/message/content").unwrap_or(&Value::Null);
                if let Some(items) = content.as_array() {
                    for item in items
                        .iter()
                        .filter(|item| item.get("type").and_then(Value::as_str) == Some("tool_use"))
                    {
                        let name = item.get("name").and_then(Value::as_str).unwrap_or("?");
                        acc.add_tool(name);
                        if let Some(fp) = item
                            .pointer("/input/file_path")
                            .and_then(Value::as_str)
                            .filter(|s| !is_noise_path(s))
                        {
                            acc.add_file(fp);
                        }
                        let call_id = item.get("id").and_then(Value::as_str).map(str::to_string);
                        let event = tool_event_from_input(
                            acc.cwd.as_deref(),
                            ts_ms_from_event(&obj),
                            current_prompt_index,
                            name,
                            item.get("input").unwrap_or(&Value::Null),
                            call_id.clone(),
                            task_stack
                                .path_for_tool(name, item.get("input").unwrap_or(&Value::Null)),
                        );
                        if let Some(id) = call_id {
                            call_index.insert(id, events.tools.len());
                        }
                        events.tools.push(event);
                    }
                }
                let text = content_to_text(content);
                let usage = obj.pointer("/message/usage").unwrap_or(&Value::Null);
                if !text.trim().is_empty() || usage.is_object() {
                    // Build preview: prefer text content, fall back to tool names
                    let preview_text = if !text.trim().is_empty() {
                        text.clone()
                    } else if let Some(items) = content.as_array() {
                        let tool_names: Vec<_> = items
                            .iter()
                            .filter_map(|item| {
                                if item.get("type").and_then(Value::as_str) == Some("tool_use") {
                                    item.get("name").and_then(Value::as_str)
                                } else {
                                    None
                                }
                            })
                            .collect();
                        if tool_names.is_empty() {
                            String::new()
                        } else {
                            format!("tool: {}", tool_names.join(", "))
                        }
                    } else {
                        String::new()
                    };
                    events.llm_responses.push(LlmResponse {
                        ts_ms: ts_ms_from_event(&obj),
                        prompt_index: current_prompt_index,
                        model,
                        text_hash: short_hash(&(text.clone() + &usage.to_string()), 12),
                        preview: truncate_clean(
                            if preview_text.is_empty() {
                                "token report"
                            } else {
                                &preview_text
                            },
                            140,
                        ),
                        input_tokens: json_u64(usage, "input_tokens"),
                        output_tokens: json_u64(usage, "output_tokens"),
                        cache_tokens: json_u64(usage, "cache_creation_input_tokens")
                            + json_u64(usage, "cache_read_input_tokens"),
                        total_tokens: 0,
                        tag: String::new(),
                        response_phase: if obj
                            .pointer("/message/stop_reason")
                            .and_then(Value::as_str)
                            == Some("end_turn")
                            && !text.trim().is_empty()
                        {
                            "final_answer".to_string()
                        } else {
                            "assistant_message".to_string()
                        },
                        task_path: task_stack.path(),
                    });
                }
            }
            (AGENT_CLAUDE, "queue-operation") if acc.prompt_preview.is_none() => {
                if obj.get("operation").and_then(Value::as_str) == Some("enqueue")
                    && let Some(text) = obj.get("content").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text.clone());
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CLAUDE, "last-prompt") if acc.prompt_preview.is_none() => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text.clone());
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CLAUDE, "user") => {
                let content = obj.pointer("/message/content").unwrap_or(&Value::Null);
                if claude_is_tool_result(content) || is_claude_tool_result(&obj) {
                    let is_error = obj
                        .get("toolUseResult")
                        .and_then(|v| v.get("is_error"))
                        .and_then(Value::as_bool)
                        .unwrap_or(false);
                    for id in claude_tool_result_ids(content) {
                        if let Some(index) = call_index.get(&id).copied()
                            && let Some(tool) = events.tools.get_mut(index)
                        {
                            tool.status = if is_error { "fail" } else { "ok" }.to_string();
                        }
                    }
                } else if let Some(text) = local_message_preview(content) {
                    if acc.prompt_preview.is_none() {
                        acc.prompt_preview = Some(text.clone());
                    }
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CLAUDE, "last-prompt") => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CODEX, "turn_context") => {
                if let Some(name) = obj.pointer("/payload/model").and_then(Value::as_str) {
                    codex_model = name.to_string();
                    acc.model = Some(name.to_string());
                }
            }
            (AGENT_CODEX, "event_msg") => {
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                let ptype = payload.get("type").and_then(Value::as_str).unwrap_or("");
                if ptype == "token_count"
                    && let Some(usage) = payload.pointer("/info/total_token_usage")
                {
                    let name = if codex_model.is_empty() {
                        "unknown"
                    } else {
                        &codex_model
                    };
                    acc.set_usage(
                        name,
                        json_i64(usage, "input_tokens"),
                        json_i64(usage, "output_tokens"),
                        0,
                        0,
                        json_i64(usage, "total_tokens"),
                    );
                }
                if matches!(ptype, "token_count" | "token_usage") {
                    let info = payload
                        .get("info")
                        .or_else(|| payload.get("usage"))
                        .unwrap_or(payload);
                    let token_usage = info
                        .get("last_token_usage")
                        .or_else(|| info.get("total_token_usage"))
                        .unwrap_or(info);
                    let input_tokens = json_u64(token_usage, "input_tokens");
                    let output_tokens = json_u64(token_usage, "output_tokens");
                    let cache_tokens = json_u64(token_usage, "cached_input_tokens");
                    let total_tokens = json_u64(token_usage, "total_tokens")
                        .max(json_u64(info, "total_tokens"))
                        .max(json_u64(info, "tokens"));
                    if total_tokens > 0
                        && let Some(last) = events.llm_responses.last_mut()
                        && last.total_tokens == 0
                    {
                        last.input_tokens = input_tokens;
                        last.output_tokens = output_tokens;
                        last.cache_tokens = cache_tokens;
                        last.total_tokens = total_tokens;
                    }
                }
                if ptype == "user_message" {
                    let text = payload
                        .get("message")
                        .or_else(|| payload.get("content"))
                        .and_then(Value::as_str)
                        .unwrap_or("");
                    if let Some(text) = clean_prompt_text(text) {
                        acc.prompt_preview = Some(text.clone());
                        task_stack.observe_user(&text);
                        current_prompt_index =
                            events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                    }
                }
                if ptype == "agent_message" {
                    let text = payload
                        .get("message")
                        .or_else(|| payload.get("content"))
                        .and_then(Value::as_str)
                        .unwrap_or("");
                    if let Some(text) = clean_prompt_text(text) {
                        events.llm_responses.push(LlmResponse {
                            ts_ms: ts_ms_from_event(&obj),
                            prompt_index: current_prompt_index,
                            model: if codex_model.is_empty() {
                                AGENT_CODEX.to_string()
                            } else {
                                codex_model.clone()
                            },
                            text_hash: short_hash(&text, 12),
                            preview: truncate_clean(&text, 180),
                            input_tokens: 0,
                            output_tokens: 0,
                            cache_tokens: 0,
                            total_tokens: 0,
                            tag: String::new(),
                            response_phase: payload
                                .get("phase")
                                .and_then(Value::as_str)
                                .unwrap_or("assistant_message")
                                .to_string(),
                            task_path: task_stack.path(),
                        });
                    }
                }
            }
            (AGENT_CODEX, "response_item")
                if obj.pointer("/payload/type").and_then(Value::as_str)
                    == Some("custom_tool_call") =>
            {
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                let outer_name = payload
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or("tool");
                let raw_input = payload.get("input").and_then(Value::as_str).unwrap_or("");
                let (name, args) = codex_custom_tool_input(outer_name, raw_input);
                acc.add_tool(&name);
                let call_id = payload
                    .get("call_id")
                    .and_then(Value::as_str)
                    .map(str::to_string);
                let event = tool_event_from_input(
                    acc.cwd.as_deref(),
                    ts_ms_from_event(&obj),
                    current_prompt_index,
                    &name,
                    &args,
                    call_id.clone(),
                    task_stack.path_for_tool(&name, &args),
                );
                if name == "update_plan" {
                    task_stack.observe_plan(&args);
                }
                if let Some(id) = call_id {
                    call_index.insert(id, events.tools.len());
                }
                events.tools.push(event);
            }
            (AGENT_CODEX, "response_item")
                if obj.pointer("/payload/type").and_then(Value::as_str)
                    == Some("custom_tool_call_output") =>
            {
                if let Some(call_id) = obj.pointer("/payload/call_id").and_then(Value::as_str)
                    && let Some(index) = call_index.get(call_id).copied()
                    && let Some(tool) = events.tools.get_mut(index)
                {
                    let output =
                        content_to_text(obj.pointer("/payload/output").unwrap_or(&Value::Null));
                    tool.status = status_from_output(&output).to_string();
                }
            }
            (AGENT_CODEX, "response_item")
                if obj.pointer("/payload/type").and_then(Value::as_str)
                    == Some("function_call") =>
            {
                let name = obj
                    .pointer("/payload/name")
                    .and_then(Value::as_str)
                    .unwrap_or("?");
                acc.add_tool(name);
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                let args = parse_tool_args(payload.get("arguments").unwrap_or(&Value::Null));
                let call_id = payload
                    .get("call_id")
                    .and_then(Value::as_str)
                    .map(str::to_string);
                let event = tool_event_from_input(
                    acc.cwd.as_deref(),
                    ts_ms_from_event(&obj),
                    current_prompt_index,
                    name,
                    &args,
                    call_id.clone(),
                    task_stack.path_for_tool(name, &args),
                );
                if name == "update_plan" {
                    task_stack.observe_plan(&args);
                }
                if let Some(id) = call_id {
                    call_index.insert(id, events.tools.len());
                }
                events.tools.push(event);
            }
            (AGENT_CODEX, "response_item")
                if obj.pointer("/payload/type").and_then(Value::as_str)
                    == Some("function_call_output") =>
            {
                if let Some(call_id) = obj.pointer("/payload/call_id").and_then(Value::as_str)
                    && let Some(index) = call_index.get(call_id).copied()
                    && let Some(tool) = events.tools.get_mut(index)
                {
                    let output = obj
                        .pointer("/payload/output")
                        .and_then(Value::as_str)
                        .unwrap_or("");
                    tool.status = status_from_output(output).to_string();
                }
            }
            (AGENT_CODEX, "response_item")
                if obj.pointer("/payload/type").and_then(Value::as_str) == Some("message") =>
            {
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                let text = payload
                    .get("message")
                    .and_then(Value::as_str)
                    .map(str::to_string)
                    .unwrap_or_else(|| {
                        content_to_text(payload.get("content").unwrap_or(&Value::Null))
                    });
                if let Some(text) = clean_prompt_text(&text) {
                    if payload.get("role").and_then(Value::as_str) == Some("user") {
                        acc.prompt_preview = Some(text.clone());
                        task_stack.observe_user(&text);
                        current_prompt_index =
                            events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                        continue;
                    }
                    let role = payload.get("role").and_then(Value::as_str);
                    let legacy_assistant = role.is_none()
                        && payload
                            .get("content")
                            .and_then(Value::as_array)
                            .is_some_and(|items| {
                                items.iter().any(|item| {
                                    item.get("type").and_then(Value::as_str) == Some("output_text")
                                })
                            });
                    if role != Some("assistant") && !legacy_assistant {
                        continue;
                    }
                    events.llm_responses.push(LlmResponse {
                        ts_ms: ts_ms_from_event(&obj),
                        prompt_index: current_prompt_index,
                        model: if codex_model.is_empty() {
                            AGENT_CODEX.to_string()
                        } else {
                            codex_model.clone()
                        },
                        text_hash: short_hash(&text, 12),
                        preview: truncate_clean(&text, 180),
                        input_tokens: 0,
                        output_tokens: 0,
                        cache_tokens: 0,
                        total_tokens: 0,
                        tag: String::new(),
                        response_phase: payload
                            .get("phase")
                            .and_then(Value::as_str)
                            .unwrap_or("assistant_message")
                            .to_string(),
                        task_path: task_stack.path(),
                    });
                }
            }
            (AGENT_CODEX, "message" | "input" | "user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text.clone());
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            _ if acc.prompt_preview.is_none() && typ.contains("user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text.clone());
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            _ => {}
        }
    }

    if acc.model_usage.is_empty() {
        acc.model_usage = claude_message_models;
    }
    deduplicate_llm_responses(&mut events);
    acc.finish_with_events(events)
}

fn deduplicate_llm_responses(events: &mut SessionEvents) {
    let mut unique: Vec<LlmResponse> = Vec::with_capacity(events.llm_responses.len());
    for response in events.llm_responses.drain(..) {
        let duplicate = unique.last_mut().filter(|previous| {
            previous.prompt_index == response.prompt_index
                && previous.text_hash == response.text_hash
                && previous
                    .ts_ms
                    .zip(response.ts_ms)
                    .is_some_and(|(left, right)| left.abs_diff(right) <= 1_000)
        });
        if let Some(previous) = duplicate {
            previous.input_tokens = previous.input_tokens.max(response.input_tokens);
            previous.output_tokens = previous.output_tokens.max(response.output_tokens);
            previous.cache_tokens = previous.cache_tokens.max(response.cache_tokens);
            previous.total_tokens = previous.total_tokens.max(response.total_tokens);
            if response_phase_priority(&response.response_phase)
                > response_phase_priority(&previous.response_phase)
            {
                previous.response_phase = response.response_phase;
            }
            continue;
        }
        unique.push(response);
    }
    events.llm_responses = unique;
}

fn response_phase_priority(phase: &str) -> u8 {
    match phase {
        "final_answer" => 3,
        "commentary" => 2,
        "assistant_message" => 1,
        _ => 0,
    }
}

fn parse_gemini_json(path: &Path, updated: SystemTime, content: &str) -> Option<AgentSession> {
    let root: Value = serde_json::from_str(content).ok()?;
    let mut acc = SessionAccumulator::new(AGENT_GEMINI, path, updated);
    let mut events = SessionEvents::default();
    let mut current_prompt_index = 0usize;
    let mut task_stack = SemanticTaskStack::default();
    if let Some(id) = root.get("sessionId").and_then(Value::as_str) {
        acc.session_id = id.to_string();
        acc.conversation_id = Some(id.to_string());
    }
    acc.start_timestamp_ms = root
        .get("startTime")
        .and_then(Value::as_str)
        .and_then(iso_ms);
    acc.end_timestamp_ms = root
        .get("lastUpdated")
        .and_then(Value::as_str)
        .and_then(iso_ms)
        .or(acc.start_timestamp_ms);
    acc.duration_ms = acc
        .start_timestamp_ms
        .zip(acc.end_timestamp_ms)
        .map(|(start, end)| end.saturating_sub(start))
        .unwrap_or_default();

    let Some(messages) = root.get("messages").and_then(Value::as_array) else {
        return acc.finish_with_events(events);
    };
    for msg in messages {
        if let Some(ts) = msg.get("timestamp").and_then(Value::as_str) {
            acc.last_message_at = Some(ts.to_string());
        }
        let ts_ms = msg
            .get("timestamp")
            .and_then(Value::as_str)
            .and_then(parse_ts_ms);
        match msg.get("type").and_then(Value::as_str) {
            Some("user") if acc.prompt_preview.is_none() => {
                if let Some(text) = local_message_preview(msg.get("content").unwrap_or(msg)) {
                    acc.prompt_preview = Some(text.clone());
                    task_stack.observe_user(&text);
                    current_prompt_index = events.upsert_prompt(ts_ms, &text, task_stack.path());
                }
            }
            Some("user") => {
                if let Some(text) = local_message_preview(msg.get("content").unwrap_or(msg)) {
                    task_stack.observe_user(&text);
                    current_prompt_index = events.upsert_prompt(ts_ms, &text, task_stack.path());
                }
            }
            Some("gemini") | Some("assistant") | Some("model") => {
                let mut llm_model = AGENT_GEMINI.to_string();
                if let Some(model) = msg.get("model").and_then(Value::as_str) {
                    llm_model = model.to_string();
                    acc.model.get_or_insert_with(|| model.to_string());
                    if let Some(tokens) = msg.get("tokens") {
                        acc.add_usage(
                            model,
                            json_i64(tokens, "input"),
                            json_i64(tokens, "output"),
                            0,
                            json_i64(tokens, "cached"),
                            json_i64(tokens, "total"),
                        );
                    }
                }
                if let Some(tool_calls) = msg.get("toolCalls").and_then(Value::as_array) {
                    for call in tool_calls {
                        let name = call.get("name").and_then(Value::as_str).unwrap_or("?");
                        acc.add_tool(name);
                        if let Some(path) = find_file_arg(call).filter(|path| !is_noise_path(path))
                        {
                            acc.add_file(path);
                        }
                        events.tools.push(tool_event_from_input(
                            acc.cwd.as_deref(),
                            ts_ms,
                            current_prompt_index,
                            name,
                            call,
                            call.get("id").and_then(Value::as_str).map(str::to_string),
                            task_stack.path_for_tool(name, call),
                        ));
                    }
                }
                let content = msg.get("content").unwrap_or(msg);
                let text = content_to_text(content);
                let tokens = msg.get("tokens").unwrap_or(&Value::Null);
                if !text.trim().is_empty() || tokens.is_object() {
                    events.llm_responses.push(LlmResponse {
                        ts_ms,
                        prompt_index: current_prompt_index,
                        model: llm_model,
                        text_hash: short_hash(&(text.clone() + &tokens.to_string()), 12),
                        preview: truncate_clean(
                            if text.trim().is_empty() {
                                "gemini response"
                            } else {
                                &text
                            },
                            140,
                        ),
                        input_tokens: json_u64(tokens, "input"),
                        output_tokens: json_u64(tokens, "output"),
                        cache_tokens: json_u64(tokens, "cached"),
                        total_tokens: json_u64(tokens, "total"),
                        tag: String::new(),
                        response_phase: if msg
                            .get("toolCalls")
                            .and_then(Value::as_array)
                            .is_some_and(|calls| !calls.is_empty())
                        {
                            "assistant_message".to_string()
                        } else {
                            "final_answer".to_string()
                        },
                        task_path: task_stack.path(),
                    });
                }
            }
            _ => {}
        }
    }
    acc.finish_with_events(events)
}

struct SessionAccumulator {
    agent_type: String,
    session_id: String,
    conversation_id: Option<String>,
    path: PathBuf,
    updated: SystemTime,
    start_timestamp_ms: Option<u64>,
    end_timestamp_ms: Option<u64>,
    model: Option<String>,
    model_usage: BTreeMap<String, TokenUsage>,
    tools: BTreeMap<String, usize>,
    files: BTreeMap<String, usize>,
    prompt_preview: Option<String>,
    duration_ms: u64,
    cwd: Option<String>,
    last_message_at: Option<String>,
}

impl SessionAccumulator {
    fn new(agent: &str, path: &Path, updated: SystemTime) -> Self {
        let normalized = normalize_session_log_path(path);
        let session_id = path
            .file_stem()
            .and_then(|stem| stem.to_str())
            .unwrap_or("session")
            .to_string();
        Self {
            agent_type: agent.to_string(),
            session_id,
            conversation_id: None,
            path: normalized.clone(),
            updated,
            start_timestamp_ms: None,
            end_timestamp_ms: Some(system_time_ms(updated)),
            model: None,
            model_usage: BTreeMap::new(),
            tools: BTreeMap::new(),
            files: BTreeMap::new(),
            prompt_preview: None,
            duration_ms: 0,
            cwd: None,
            last_message_at: None,
        }
    }

    fn add_usage(
        &mut self,
        model: &str,
        input: i64,
        output: i64,
        cache_creation: i64,
        cache_read: i64,
        total: i64,
    ) {
        add_usage(
            &mut self.model_usage,
            model,
            input,
            output,
            cache_creation,
            cache_read,
            total,
        );
    }

    fn set_usage(
        &mut self,
        model: &str,
        input: i64,
        output: i64,
        cache_creation: i64,
        cache_read: i64,
        total: i64,
    ) {
        let mut usage = TokenUsage::default();
        usage.add(input, output, cache_creation, cache_read, total);
        self.model_usage.insert(model.to_string(), usage);
    }

    fn add_tool(&mut self, name: &str) {
        *self.tools.entry(name.to_string()).or_default() += 1;
    }

    fn add_file(&mut self, path: &str) {
        *self.files.entry(path.to_string()).or_default() += 1;
    }

    fn finish(self) -> Option<AgentSession> {
        let token_usage =
            self.model_usage
                .values()
                .fold(TokenUsage::default(), |mut total, usage| {
                    total.input_tokens += usage.input_tokens;
                    total.output_tokens += usage.output_tokens;
                    total.cache_creation_tokens += usage.cache_creation_tokens;
                    total.cache_read_tokens += usage.cache_read_tokens;
                    total.total_tokens += usage.total_tokens;
                    total
                });
        if token_usage.total_tokens == 0
            && self.tools.is_empty()
            && self.prompt_preview.is_none()
            && self.model.is_none()
        {
            return None;
        }
        let display_id = format!("{}:{}", self.agent_type, short_session_id(&self.session_id));
        Some(AgentSession {
            agent_type: self.agent_type,
            session_id: self.session_id,
            conversation_id: self.conversation_id,
            display_id,
            path: self.path,
            updated: self.updated,
            start_timestamp_ms: self
                .start_timestamp_ms
                .or_else(|| Some(system_time_ms(self.updated).saturating_sub(self.duration_ms))),
            end_timestamp_ms: self.end_timestamp_ms,
            model: self.model,
            usage: token_usage,
            model_usage: self.model_usage,
            tools: self.tools,
            files: self.files,
            prompt_preview: self.prompt_preview,
            duration_ms: self.duration_ms,
            cwd: self.cwd,
            last_message_at: self.last_message_at,
            events: SessionEvents::default(),
        })
    }

    fn finish_with_events(self, events: SessionEvents) -> Option<AgentSession> {
        self.finish().map(|mut session| {
            session.events = events;
            session
        })
    }
}

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

fn walk_agent_files(agent: &'static str, dir: &Path, f: &mut dyn FnMut(&Path, &fs::Metadata)) {
    let Ok(entries) = fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            walk_agent_files(agent, &path, f);
        } else if is_agent_file_for(agent, &path)
            && let Ok(meta) = path.metadata()
        {
            f(&path, &meta);
        }
    }
}

fn is_agent_session_file(path: &Path) -> bool {
    agent_source_for_path(path).is_some()
}

fn is_agent_file_for(agent: &str, path: &Path) -> bool {
    match agent {
        AGENT_CLAUDE | AGENT_CODEX => {
            path.extension().and_then(|ext| ext.to_str()) == Some("jsonl")
        }
        AGENT_GEMINI => {
            path.extension().and_then(|ext| ext.to_str()) == Some("json")
                && path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .is_some_and(|name| name.starts_with("session-"))
                && path.to_string_lossy().contains("/chats/")
        }
        _ => false,
    }
}

pub(crate) fn user_home_dir() -> Option<PathBuf> {
    std::env::var("SUDO_USER")
        .ok()
        .and_then(|user| {
            fs::read_to_string("/etc/passwd").ok().and_then(|passwd| {
                passwd
                    .lines()
                    .find(|line| line.starts_with(&format!("{user}:")))
                    .and_then(|line| line.split(':').nth(5))
                    .map(PathBuf::from)
            })
        })
        .or_else(dirs::home_dir)
}

fn add_usage(
    models: &mut BTreeMap<String, TokenUsage>,
    model: &str,
    input: i64,
    output: i64,
    cache_creation: i64,
    cache_read: i64,
    total: i64,
) {
    models.entry(model.to_string()).or_default().add(
        input,
        output,
        cache_creation,
        cache_read,
        total,
    );
}

impl SessionEvents {
    fn upsert_prompt(&mut self, ts_ms: Option<i64>, text: &str, task_path: Vec<String>) -> usize {
        let hash = short_hash(text, 12);
        if let Some(existing) = self.prompts.iter().rposition(|prompt| {
            prompt.text_hash == hash
                && match (prompt.ts_ms, ts_ms) {
                    (Some(left), Some(right)) => left.abs_diff(right) <= 1_000,
                    (None, None) => self
                        .prompts
                        .last()
                        .is_some_and(|last| last.index == prompt.index),
                    _ => false,
                }
        }) {
            return existing;
        }
        let index = self.prompts.len();
        self.prompts.push(UserPrompt {
            index,
            ts_ms,
            text_hash: hash,
            preview: truncate_clean(text, 180),
            tag: String::new(),
            task_path,
        });
        index
    }
}

fn tool_event_from_input(
    cwd: Option<&str>,
    ts_ms: Option<i64>,
    prompt_index: usize,
    name: &str,
    input: &Value,
    call_id: Option<String>,
    task_path: Vec<String>,
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
    let cwd = cwd.unwrap_or("");
    let path_groups = extract_path_groups(Path::new(cwd), name, input, &command);
    let process_chain = if category == "shell" {
        command_process_chain(&command)
    } else {
        Vec::new()
    };
    ToolEvent {
        ts_ms,
        prompt_index,
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
        task_path,
    }
}

fn codex_custom_tool_input(outer_name: &str, raw: &str) -> (String, Value) {
    let nested_calls = codex_custom_tool_calls(raw);
    let nested_name = if raw.contains("Promise.all") || nested_calls.len() > 1 {
        "composite".to_string()
    } else {
        nested_calls
            .first()
            .cloned()
            .unwrap_or_else(|| outer_name.to_string())
    };

    let commands = extract_js_string_fields(raw, &["command", "cmd"]);
    let paths = extract_js_string_fields(raw, &["file_path", "path"]);
    let workdirs = extract_js_string_fields(raw, &["workdir"]);
    let mut input = serde_json::Map::new();
    if !commands.is_empty() {
        input.insert("command".to_string(), Value::String(commands.join("\n")));
    } else if !raw.trim().is_empty() {
        input.insert("text".to_string(), Value::String(truncate_clean(raw, 600)));
    }
    if let Some(path) = paths.first() {
        input.insert("path".to_string(), Value::String(path.clone()));
    }
    if let Some(workdir) = workdirs.first() {
        input.insert("workdir".to_string(), Value::String(workdir.clone()));
    }
    for key in ["task_name", "target", "message"] {
        if let Some(value) = extract_js_string_fields(raw, &[key]).first() {
            input.insert(key.to_string(), Value::String(value.clone()));
        }
    }
    if nested_name == "update_plan" {
        let steps = extract_js_string_fields(raw, &["step"]);
        let statuses = extract_js_string_fields(raw, &["status"]);
        let plan = steps
            .into_iter()
            .enumerate()
            .map(|(index, step)| {
                serde_json::json!({
                    "step": step,
                    "status": statuses.get(index).map(String::as_str).unwrap_or("pending")
                })
            })
            .collect::<Vec<_>>();
        input.insert("plan".to_string(), Value::Array(plan));
    }
    (nested_name, Value::Object(input))
}

fn codex_custom_tool_calls(raw: &str) -> Vec<String> {
    let mut calls = Vec::new();
    let mut offset = 0usize;
    while let Some(relative) = raw[offset..].find("tools.") {
        let start = offset + relative + "tools.".len();
        let tail = &raw[start..];
        let name = tail
            .chars()
            .take_while(|ch| ch.is_ascii_alphanumeric() || *ch == '_')
            .collect::<String>();
        let name_len = name.len();
        let after_name = tail[name.len()..].trim_start();
        if !name.is_empty() && after_name.starts_with('(') {
            calls.push(name);
        }
        offset = if name_len > 0 {
            start + name_len
        } else {
            // "tools." was not followed by an identifier. Step past one
            // character rather than one byte, so multibyte text in the
            // surrounding source cannot leave offset inside a char.
            raw[start..]
                .chars()
                .next()
                .map_or(raw.len(), |ch| start + ch.len_utf8())
        };
    }
    calls
}

fn extract_js_string_fields(raw: &str, keys: &[&str]) -> Vec<String> {
    let mut values = Vec::new();
    for key in keys {
        let mut offset = 0usize;
        while let Some(relative) = raw[offset..].find(key) {
            let start = offset + relative;
            let before = raw[..start].chars().next_back();
            let after = raw[start + key.len()..].chars().next();
            if before.is_some_and(|ch| ch.is_ascii_alphanumeric() || ch == '_')
                || after.is_some_and(|ch| ch.is_ascii_alphanumeric() || ch == '_')
            {
                offset = start + key.len();
                continue;
            }
            let tail = &raw[start + key.len()..];
            let Some(colon) = tail.find(':').filter(|index| *index <= 4) else {
                offset = start + key.len();
                continue;
            };
            let value = tail[colon + 1..].trim_start();
            let Some(quote) = value
                .chars()
                .next()
                .filter(|ch| ['\'', '"', '`'].contains(ch))
            else {
                offset = start + key.len();
                continue;
            };
            if let Some((decoded, consumed)) = parse_js_string(&value[quote.len_utf8()..], quote) {
                if !decoded.is_empty() && !values.contains(&decoded) {
                    values.push(decoded);
                }
                offset = start + key.len() + colon + 1 + consumed;
            } else {
                offset = start + key.len();
            }
        }
    }
    values
}

fn parse_js_string(raw: &str, quote: char) -> Option<(String, usize)> {
    let mut decoded = String::new();
    let mut escaped = false;
    for (index, ch) in raw.char_indices() {
        if escaped {
            decoded.push(match ch {
                'n' => '\n',
                'r' => '\r',
                't' => '\t',
                other => other,
            });
            escaped = false;
        } else if ch == '\\' {
            escaped = true;
        } else if ch == quote {
            return Some((decoded, index + ch.len_utf8() + quote.len_utf8()));
        } else {
            decoded.push(ch);
        }
    }
    None
}

fn command_from_tool_input(input: &Value) -> String {
    for key in ["cmd", "command", "pattern", "file_path", "path", "text"] {
        if let Some(value) = input.get(key).and_then(Value::as_str)
            && !value.is_empty()
        {
            return if key == "pattern" {
                format!("search {value}")
            } else {
                value.to_string()
            };
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
    let exit_codes = explicit_exit_codes(&lowered);
    if exit_codes.iter().any(|code| *code != 0) {
        return "fail";
    }
    if !exit_codes.is_empty() {
        return "ok";
    }
    if lowered.contains("\"is_error\":false") || lowered.contains("\"success\":true") {
        return "ok";
    }
    if lowered.contains("\"is_error\":true") || lowered.contains("\"success\":false") {
        return "fail";
    }
    if lowered.lines().any(|line| line.trim() == "script failed") {
        return "fail";
    }
    if lowered
        .lines()
        .any(|line| line.trim() == "script completed")
    {
        return "ok";
    }
    "observed"
}

fn explicit_exit_codes(output: &str) -> Vec<i32> {
    output
        .lines()
        .filter_map(|line| {
            let line = line.trim();
            let value = if let Some(rest) = line.strip_prefix("exit code:") {
                rest
            } else if let Some((_, rest)) = line.split_once("process exited with code") {
                rest.strip_prefix(':').unwrap_or(rest)
            } else {
                return None;
            };
            let digits = value
                .trim_start()
                .chars()
                .take_while(|ch| ch.is_ascii_digit() || *ch == '-')
                .collect::<String>();
            digits.parse().ok()
        })
        .collect()
}

pub fn tool_category(name: &str, command: &str) -> String {
    let n = name.to_ascii_lowercase();
    if n.ends_with("exec_command") || n.ends_with("shell_command") || n == "bash" {
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
    let mut parts = Vec::new();
    let mut current = String::new();
    let mut quote = None;
    let mut escaped = false;
    for ch in command.chars() {
        if escaped {
            current.push(ch);
            escaped = false;
        } else if ch == '\\' {
            escaped = true;
        } else if quote == Some(ch) {
            quote = None;
        } else if quote.is_some() {
            current.push(ch);
        } else if ch == '\'' || ch == '"' {
            quote = Some(ch);
        } else if ch.is_whitespace() {
            if !current.is_empty() {
                parts.push(std::mem::take(&mut current));
            }
        } else {
            current.push(ch);
        }
    }
    if !current.is_empty() {
        parts.push(current);
    }
    parts
}

fn extract_domains(text: &str) -> Vec<String> {
    let mut domains = BTreeSet::new();
    for part in text.split(|c: char| c.is_whitespace() || ['"', '\'', ')', '('].contains(&c)) {
        let stripped = part
            .strip_prefix("https://")
            .or_else(|| part.strip_prefix("http://"));
        if let Some(rest) = stripped
            && let Some(domain) = rest.split('/').next()
            && !domain.is_empty()
        {
            domains.insert(domain.to_ascii_lowercase());
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
    domains.into_iter().collect()
}

fn extract_path_groups(
    project_root: &Path,
    name: &str,
    input: &Value,
    command: &str,
) -> Vec<String> {
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
    groups.into_iter().filter(|v| v != "none").collect()
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
    } else if [
        "collector",
        "frontend",
        "docs",
        "bpf",
        "agentpprof",
        "agent-session",
    ]
    .contains(&parts[0].as_str())
    {
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
                if typ == "tool_result" || typ == "tool_use" || typ == "function_call" {
                    return None;
                }
                // For thinking blocks, extract the thinking field
                if typ == "thinking" {
                    return item
                        .get("thinking")
                        .and_then(Value::as_str)
                        .filter(|s| !s.is_empty())
                        .map(str::to_string);
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

fn local_session_ids(obj: &Value) -> (Option<String>, Option<String>) {
    let session_id = first_json_string(
        obj,
        &["sessionId", "session_id"],
        &["/payload/session_id", "/payload/sessionId"],
    );
    let conversation_id = first_json_string(
        obj,
        &["conversation_id", "conversationId", "thread_id", "threadId"],
        &[
            "/payload/conversation_id",
            "/payload/conversationId",
            "/payload/thread_id",
            "/payload/threadId",
        ],
    )
    .or_else(|| session_id.clone());
    (
        session_id.or_else(|| conversation_id.clone()),
        conversation_id,
    )
}

fn first_json_string(obj: &Value, keys: &[&str], pointers: &[&str]) -> Option<String> {
    keys.iter()
        .filter_map(|key| obj.get(*key).and_then(Value::as_str))
        .chain(
            pointers
                .iter()
                .filter_map(|pointer| obj.pointer(pointer).and_then(Value::as_str)),
        )
        .find(|value| !value.is_empty())
        .map(str::to_string)
}

fn strip_codex_exec_option(args: &str) -> Option<&str> {
    let (head, rest) = args.split_once(char::is_whitespace).unwrap_or((args, ""));
    match head {
        "--json" | "--skip-git-repo-check" | "--ephemeral" => Some(rest),
        "-C" | "-a" | "-s" | "-m" | "-c" | "-p" => rest
            .trim_start()
            .split_once(char::is_whitespace)
            .map(|(_, rest)| rest),
        _ => None,
    }
}

fn claude_usage_key(obj: &Value) -> String {
    obj.get("requestId")
        .or_else(|| obj.pointer("/message/id"))
        .or_else(|| obj.get("uuid"))
        .and_then(Value::as_str)
        .unwrap_or("usage")
        .to_string()
}

fn local_message_preview(value: &Value) -> Option<String> {
    let mut parts = Vec::new();
    collect_local_text(value, &mut parts);
    clean_prompt_text(&parts.join(" "))
}

fn collect_local_text(value: &Value, out: &mut Vec<String>) {
    match value {
        Value::String(text) => out.push(text.clone()),
        Value::Array(items) => {
            for item in items {
                collect_local_text(item, out);
            }
        }
        Value::Object(obj) => {
            if obj.get("type").and_then(Value::as_str).is_some_and(|typ| {
                typ == "tool_use" || typ == "function_call" || typ == "tool_result"
            }) {
                return;
            }
            for key in ["text", "content", "message", "input", "prompt"] {
                if let Some(value) = obj.get(key) {
                    collect_local_text(value, out);
                }
            }
        }
        _ => {}
    }
}

fn is_claude_tool_result(obj: &Value) -> bool {
    obj.get("toolUseResult").is_some()
        || obj.get("tool_use_result").is_some()
        || obj
            .pointer("/message/content")
            .and_then(Value::as_array)
            .is_some_and(|items| {
                items
                    .iter()
                    .any(|item| item.get("type").and_then(Value::as_str) == Some("tool_result"))
            })
}

fn find_file_arg(value: &Value) -> Option<&str> {
    match value {
        Value::Object(obj) => {
            for key in ["file_path", "path", "filepath"] {
                if let Some(path) = obj.get(key).and_then(Value::as_str) {
                    return Some(path);
                }
            }
            obj.values().find_map(find_file_arg)
        }
        Value::Array(items) => items.iter().find_map(find_file_arg),
        _ => None,
    }
}

fn is_noise_path(path: &str) -> bool {
    const NOISE: &[&str] = &[
        "/.claude/",
        "/.codex/",
        "/.gemini/",
        "/.git/",
        "/node_modules/",
        "/.npm/",
        "/.cache/",
        "CLAUDE.md",
        "AGENTS.md",
    ];
    NOISE.iter().any(|pat| path.contains(pat))
}

fn clean_prompt_text(text: &str) -> Option<String> {
    let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let text = text
        .strip_prefix("<session>")
        .and_then(|text| text.strip_suffix("</session>"))
        .unwrap_or(&text)
        .trim();
    (!text.is_empty()).then(|| text.to_string())
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

fn short_session_id(id: &str) -> String {
    let id = id.trim();
    if id.is_empty() {
        return "session".to_string();
    }
    let compact = id
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or(id)
        .trim_end_matches(".jsonl");
    const MAX_SESSION_ID_CHARS: usize = 12;
    if compact.chars().count() <= MAX_SESSION_ID_CHARS {
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

fn json_i64(value: &Value, key: &str) -> i64 {
    value.get(key).and_then(Value::as_i64).unwrap_or(0)
}

fn json_u64(value: &Value, key: &str) -> u64 {
    value.get(key).and_then(Value::as_u64).unwrap_or(0)
}

fn ts_ms_from_event(value: &Value) -> Option<i64> {
    value
        .get("timestamp")
        .and_then(Value::as_str)
        .and_then(parse_ts_ms)
}

fn parse_ts_ms(value: &str) -> Option<i64> {
    chrono::DateTime::parse_from_rfc3339(value)
        .ok()
        .map(|ts| ts.timestamp_millis())
}

fn rfc3339_seconds(value: &str) -> Option<f64> {
    chrono::DateTime::parse_from_rfc3339(value)
        .ok()
        .map(|ts| ts.timestamp_millis() as f64 / 1000.0)
}

fn uuid7_seconds(value: &str) -> Option<f64> {
    let mut parts = value.split('-');
    let high = parts.next()?;
    let low = parts.next()?;
    let version = parts.next()?;
    if !version.starts_with('7') {
        return None;
    }
    u64::from_str_radix(&format!("{high}{low}"), 16)
        .ok()
        .map(|milliseconds| milliseconds as f64 / 1000.0)
}

fn iso_ms(value: &str) -> Option<u64> {
    chrono::DateTime::parse_from_rfc3339(value)
        .ok()
        .and_then(|ts| u64::try_from(ts.timestamp_millis()).ok())
}

fn system_time_ms(value: SystemTime) -> u64 {
    value
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::time::UNIX_EPOCH;

    #[test]
    fn local_session_ids_keep_distinct_conversation_id() {
        assert_eq!(
            local_session_ids(&json!({"sessionId": "run", "conversation_id": "conv"})),
            (Some("run".to_string()), Some("conv".to_string()))
        );
        assert_eq!(
            local_session_ids(&json!({"payload": {"thread_id": "thread"}})),
            (Some("thread".to_string()), Some("thread".to_string()))
        );
        assert_eq!(
            local_session_ids(&json!({"payload": {"model": "gpt"}})),
            (None, None)
        );
    }

    #[test]
    fn agent_jsonl_events_share_one_ir() {
        let codex = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5","cwd":"/repo"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"user_message","message":"run tests"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"cargo test\"}"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"agent_message","message":"tests passed"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"token_count","info":{"last_token_usage":{"input_tokens":10,"output_tokens":5,"total_tokens":15}}}}"#,
        );
        let claude = concat!(
            r#"{"type":"user","message":{"content":"check build"}}"#,
            "\n",
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"cmd":"cargo check"}},{"type":"text","text":"checking"}],"usage":{"input_tokens":7,"cache_creation_input_tokens":2,"output_tokens":3}}}"#,
        );

        for (agent, content, tool, model, tokens) in [
            (AGENT_CODEX, codex, "exec_command", "gpt-5", 15),
            (AGENT_CLAUDE, claude, "Bash", "claude-opus", 12),
        ] {
            let session = parse_session_content(
                agent,
                &PathBuf::from("/tmp/session.jsonl"),
                UNIX_EPOCH,
                content,
            )
            .expect("session");
            assert_eq!(session.events.tools[0].tool_name, tool);
            assert_eq!(session.events.tools[0].category, "shell");
            assert_eq!(session.events.llm_responses[0].model, model);
            let usage = &session.events.llm_responses[0];
            let total = usage
                .total_tokens
                .max(usage.input_tokens + usage.output_tokens + usage.cache_tokens);
            assert_eq!(total, tokens);
        }
    }

    #[test]
    fn codex_source_controls_build_sparse_semantic_task_paths() {
        let codex = concat!(
            r#"{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"write a paper"}]}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"update_plan","call_id":"p1","arguments":"{\"plan\":[{\"step\":\"write abstract\",\"status\":\"in_progress\"}]}"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"sed -n 1,80p paper.tex\"}"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call_output","call_id":"c1","output":"Process exited with code 0\n0 tests failed"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"继续"}]}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c2","arguments":"{\"cmd\":\"rg error paper.tex\"}"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call_output","call_id":"c2","output":"review error handling documentation"}}"#,
        );

        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            codex,
        )
        .expect("session");

        assert_eq!(session.events.prompts.len(), 2);
        assert!(session.events.llm_responses.is_empty());
        assert_eq!(session.events.tools[0].task_path, vec!["write a paper"]);
        assert_eq!(
            session.events.tools[1].task_path,
            vec!["write a paper", "write abstract"]
        );
        assert_eq!(
            session.events.tools[2].task_path,
            session.events.tools[1].task_path
        );
        assert_eq!(session.events.tools[1].status, "ok");
        assert_eq!(session.events.tools[2].status, "observed");
    }

    #[test]
    fn codex_custom_exec_is_a_real_source_tool_event() {
        let codex = [
            json!({
                "timestamp": "2026-07-21T00:00:00.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "test the parser"}]
                }
            }),
            json!({
                "timestamp": "2026-07-21T00:00:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "custom-1",
                    "input": "const r = await tools.shell_command({command:\"cargo test\",workdir:\"/repo\"}); text(r);"
                }
            }),
            json!({
                "timestamp": "2026-07-21T00:00:02.000Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call_output",
                    "call_id": "custom-1",
                    "output": [{"type": "input_text", "text": "Script completed\nExit code: 0\nOutput:\nall tests passed"}]
                }
            }),
        ]
        .into_iter()
        .map(|line| line.to_string())
        .collect::<Vec<_>>()
        .join("\n");

        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &codex,
        )
        .expect("session");

        assert_eq!(session.events.tools.len(), 1);
        let event = &session.events.tools[0];
        assert_eq!(event.tool_name, "shell_command");
        assert_eq!(event.category, "shell");
        assert_eq!(event.effect, "test");
        assert_eq!(event.command, "cargo test");
        assert_eq!(event.status, "ok");
        assert_eq!(event.task_path, vec!["test the parser"]);
    }

    #[test]
    fn custom_update_plan_changes_only_later_operation_paths() {
        let codex = [
            json!({
                "timestamp": "2026-07-21T00:00:00.000Z",
                "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "write a paper"}]}
            }),
            json!({
                "timestamp": "2026-07-21T00:00:01.000Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "plan-1",
                    "input": "const r = await tools.update_plan({plan:[{step:\"write abstract\",status:\"in_progress\"},{step:\"write evaluation\",status:\"pending\"}]}); text(r);"
                }
            }),
            json!({
                "timestamp": "2026-07-21T00:00:02.000Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "shell-1",
                    "input": "const r = await tools.shell_command({command:\"sed -n 1,80p paper.tex\",workdir:\"/repo\"}); text(r);"
                }
            }),
        ]
        .into_iter()
        .map(|line| line.to_string())
        .collect::<Vec<_>>()
        .join("\n");
        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &codex,
        )
        .expect("session");

        assert_eq!(session.events.tools.len(), 2);
        assert_eq!(session.events.tools[0].tool_name, "update_plan");
        assert_eq!(session.events.tools[0].task_path, vec!["write a paper"]);
        assert_eq!(
            session.events.tools[1].task_path,
            vec!["write a paper", "write abstract"]
        );
    }

    #[test]
    fn prompt_dedup_is_local_and_continuations_keep_the_current_task() {
        let codex = [
            ("2026-07-21T00:00:00.000Z", "write a paper"),
            ("2026-07-21T00:00:00.500Z", "write a paper"),
            ("2026-07-21T00:00:03.000Z", "write a paper"),
            ("2026-07-21T00:00:06.000Z", "继续"),
        ]
        .into_iter()
        .map(|(timestamp, text)| {
            json!({
                "timestamp": timestamp,
                "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}
            })
            .to_string()
        })
        .collect::<Vec<_>>()
        .join("\n");
        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &codex,
        )
        .expect("session");

        assert_eq!(session.events.prompts.len(), 3);
        assert_eq!(session.events.prompts[2].preview, "继续");
        assert_eq!(session.events.prompts[2].task_path, vec!["write a paper"]);
    }

    #[test]
    fn developer_messages_are_not_agent_responses() {
        let codex = concat!(
            r#"{"timestamp":"2026-07-21T00:00:00.000Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"review"}]}}"#,
            "\n",
            r#"{"timestamp":"2026-07-21T00:00:01.000Z","type":"response_item","payload":{"type":"message","role":"developer","content":[{"type":"input_text","text":"internal instruction"}]}}"#,
            "\n",
            r#"{"timestamp":"2026-07-21T00:00:02.000Z","type":"response_item","payload":{"type":"message","role":"assistant","phase":"final_answer","content":[{"type":"output_text","text":"review complete"}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            codex,
        )
        .expect("session");
        assert_eq!(session.events.llm_responses.len(), 1);
        assert_eq!(session.events.llm_responses[0].preview, "review complete");
    }

    #[test]
    fn mixed_batch_exit_codes_fail_if_any_command_failed() {
        assert_eq!(
            status_from_output("Script completed\nExit code: 0\nExit code: 7"),
            "fail"
        );
        assert_eq!(
            status_from_output(
                "Process exited with code 0\nProcess exited with code 0\n0 tests failed"
            ),
            "ok"
        );
    }

    #[test]
    fn codex_preserves_commentary_and_final_response_phases() {
        let codex = concat!(
            r#"{"timestamp":"2026-07-21T00:00:00.000Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"review the code"}]}}"#,
            "\n",
            r#"{"timestamp":"2026-07-21T00:00:01.000Z","type":"response_item","payload":{"type":"message","role":"assistant","phase":"commentary","content":[{"type":"output_text","text":"I am checking it"}]}}"#,
            "\n",
            r#"{"timestamp":"2026-07-21T00:00:02.000Z","type":"response_item","payload":{"type":"message","role":"assistant","phase":"final_answer","content":[{"type":"output_text","text":"The code is correct"}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            codex,
        )
        .expect("session");

        assert_eq!(session.events.llm_responses.len(), 2);
        assert_eq!(session.events.llm_responses[0].response_phase, "commentary");
        assert_eq!(
            session.events.llm_responses[1].response_phase,
            "final_answer"
        );
    }

    #[test]
    fn semantic_task_label_prefers_explicit_goal_payload() {
        let raw = "prefix <objective>write a paper and evaluate it</objective> suffix";
        assert_eq!(semantic_task_label(raw), "write a paper and evaluate it");
    }

    #[test]
    fn codex_fork_excludes_copied_parent_history_before_ownership_boundary() {
        let codex = concat!(
            r#"{"timestamp":"1970-01-01T00:00:01Z","type":"session_meta","payload":{"id":"child","session_id":"parent","parent_thread_id":"parent","timestamp":"1970-01-01T00:00:01Z","cwd":"/repo"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"user_message","message":"copied parent task"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"copied","arguments":"{\"cmd\":\"false\"}"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"task_started","started_at":2.0}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"user_message","message":"review child result"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"owned","arguments":"{\"cmd\":\"cargo test\"}"}}"#,
        );

        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/child.jsonl"),
            UNIX_EPOCH,
            codex,
        )
        .expect("child session");

        assert_eq!(session.session_id, "child");
        assert_eq!(session.conversation_id.as_deref(), Some("parent"));
        assert_eq!(session.events.prompts.len(), 1);
        assert_eq!(session.events.prompts[0].preview, "review child result");
        assert_eq!(session.events.tools.len(), 1);
        assert_eq!(session.events.tools[0].call_id.as_deref(), Some("owned"));
    }
}
