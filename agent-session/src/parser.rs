// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Session file parsing for Claude Code, Codex, and Gemini CLI.

use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashSet, VecDeque};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::types::{
    AgentSession, LlmResponse, SessionCandidate, SessionDirStat, SessionEvents, TokenUsage,
    ToolEvent, ToolPath, UserPrompt,
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
        (AGENT_CODEX, home.join(".codex/archived_sessions")),
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
        (AGENT_CODEX, home.join(".codex/archived_sessions")),
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

pub fn codex_total_token_usage(content: &str) -> Option<TokenUsage> {
    content.lines().rev().find_map(|line| {
        let obj: Value = serde_json::from_str(line).ok()?;
        let payload = obj.get("payload")?;
        if payload.get("type").and_then(Value::as_str) != Some("token_count") {
            return None;
        }
        payload
            .pointer("/info/total_token_usage")
            .map(codex_token_usage)
    })
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
    let args = shell_words(command.split_once(" exec ")?.1.trim())?;
    let mut index = 0usize;
    while index < args.len() {
        let arg = args[index].as_str();
        if arg == "--" {
            index += 1;
            break;
        }
        if !arg.starts_with('-') {
            break;
        }
        let consumed = codex_exec_option_arity(arg)?;
        index += consumed;
    }
    (index < args.len())
        .then(|| args[index..].join(" "))
        .and_then(|prompt| clean_prompt_text(&prompt))
}

// ---------------------------------------------------------------------------
// Internal parsing implementation
// ---------------------------------------------------------------------------

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

    for line in content.lines() {
        let Ok(obj) = serde_json::from_str::<Value>(line) else {
            continue;
        };
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
        let typ = obj.get("type").and_then(Value::as_str).unwrap_or("");
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
                    });
                }
            }
            (AGENT_CLAUDE, "queue-operation") if acc.prompt_preview.is_none() => {
                if obj.get("operation").and_then(Value::as_str) == Some("enqueue")
                    && let Some(text) = obj.get("content").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text.clone());
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
                }
            }
            (AGENT_CLAUDE, "last-prompt") if acc.prompt_preview.is_none() => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text.clone());
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
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
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
                }
            }
            (AGENT_CLAUDE, "last-prompt") => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
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
                    let usage = codex_token_usage(usage);
                    acc.set_usage(
                        name,
                        usage.input_tokens,
                        usage.output_tokens,
                        0,
                        usage.cache_read_tokens,
                        usage.total_tokens,
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
                    if total_tokens > 0 {
                        if let Some(last) = events.llm_responses.last_mut()
                            && last.total_tokens == 0
                        {
                            last.input_tokens = input_tokens;
                            last.output_tokens = output_tokens;
                            last.cache_tokens = cache_tokens;
                            last.total_tokens = total_tokens;
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
                            text_hash: short_hash(&token_usage.to_string(), 12),
                            preview: "token report".to_string(),
                            input_tokens,
                            output_tokens,
                            cache_tokens,
                            total_tokens,
                            tag: String::new(),
                        });
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
                        current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
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
                        });
                    }
                }
            }
            (AGENT_CODEX, "response_item")
                if matches!(
                    obj.pointer("/payload/type").and_then(Value::as_str),
                    Some("function_call" | "custom_tool_call")
                ) =>
            {
                let name = obj
                    .pointer("/payload/name")
                    .and_then(Value::as_str)
                    .unwrap_or("?");
                acc.add_tool(name);
                let payload = obj.get("payload").unwrap_or(&Value::Null);
                let args = parse_tool_args(
                    payload
                        .get("arguments")
                        .or_else(|| payload.get("input"))
                        .unwrap_or(&Value::Null),
                );
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
                );
                if let Some(id) = call_id {
                    call_index.insert(id, events.tools.len());
                }
                events.tools.push(event);
            }
            (AGENT_CODEX, "response_item")
                if matches!(
                    obj.pointer("/payload/type").and_then(Value::as_str),
                    Some("function_call_output" | "custom_tool_call_output")
                ) =>
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
                    });
                }
            }
            (AGENT_CODEX, "message" | "input" | "user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text.clone());
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
                }
            }
            _ if acc.prompt_preview.is_none() && typ.contains("user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text.clone());
                    current_prompt_index = events.upsert_prompt(ts_ms_from_event(&obj), &text);
                }
            }
            _ => {}
        }
    }

    if acc.model_usage.is_empty() {
        acc.model_usage = claude_message_models;
    }
    acc.finish_with_events(events)
}

fn codex_token_usage(value: &Value) -> TokenUsage {
    let input = json_i64(value, "input_tokens").max(0);
    let output = json_i64(value, "output_tokens").max(0);
    let cache = json_i64(value, "cached_input_tokens").max(0);
    let input = input.saturating_sub(cache);
    TokenUsage {
        input_tokens: input,
        output_tokens: output,
        cache_creation_tokens: 0,
        cache_read_tokens: cache,
        total_tokens: input + output + cache,
    }
}

fn parse_gemini_json(path: &Path, updated: SystemTime, content: &str) -> Option<AgentSession> {
    let root: Value = serde_json::from_str(content).ok()?;
    let mut acc = SessionAccumulator::new(AGENT_GEMINI, path, updated);
    let mut events = SessionEvents::default();
    let mut current_prompt_index = 0usize;
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
                    current_prompt_index = events.upsert_prompt(ts_ms, &text);
                }
            }
            Some("user") => {
                if let Some(text) = local_message_preview(msg.get("content").unwrap_or(msg)) {
                    current_prompt_index = events.upsert_prompt(ts_ms, &text);
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
    fn upsert_prompt(&mut self, ts_ms: Option<i64>, text: &str) -> usize {
        let hash = short_hash(text, 12);
        if let Some(existing) = self
            .prompts
            .iter()
            .position(|prompt| prompt.text_hash == hash)
        {
            return existing;
        }
        let index = self.prompts.len();
        self.prompts.push(UserPrompt {
            index,
            ts_ms,
            text_hash: hash,
            preview: truncate_clean(text, 180),
            tag: String::new(),
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
    let paths = extract_tool_paths(name, input, &command, &effect);
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
        paths,
        domains,
        call_id,
    }
}

fn extract_tool_paths(name: &str, input: &Value, command: &str, effect: &str) -> Vec<ToolPath> {
    let lower = name.to_ascii_lowercase();
    let is_shell = lower.contains("bash") || lower.contains("exec") || lower.contains("shell");
    let default_access = if lower.contains("read")
        || lower.contains("grep")
        || lower.contains("glob")
        || lower.contains("search")
    {
        "read"
    } else if lower.contains("write")
        || lower.contains("edit")
        || lower.contains("replace")
        || lower.contains("patch")
    {
        "write"
    } else if is_shell {
        if effect == "read" { "read" } else { "write" }
    } else {
        return Vec::new();
    };
    let mut rows = BTreeMap::<String, String>::new();
    if !is_shell {
        collect_path_fields(input, default_access, &mut rows);
    }

    let embedded_patch = embedded_json_string(command, "*** Begin Patch");
    let patch = input
        .get("patch")
        .or_else(|| input.get("input"))
        .or_else(|| input.get("text"))
        .and_then(Value::as_str)
        .filter(|value| value.contains("*** Begin Patch") && value.lines().count() > 1)
        .or(embedded_patch.as_deref())
        .or_else(|| {
            (command.contains("*** Begin Patch") && command.lines().count() > 1).then_some(command)
        });
    let mut has_patch = false;
    if let Some(patch) = patch {
        let mut pending_update = None;
        for line in patch.lines() {
            let marker = line.trim();
            for (prefix, access) in [
                ("*** Add File: ", "create"),
                ("*** Update File: ", "write"),
                ("*** Delete File: ", "delete"),
                ("*** Move to: ", "rename"),
            ] {
                if let Some(path) = marker.strip_prefix(prefix) {
                    let path = clean_path_token(path);
                    if !path.is_empty() {
                        has_patch = true;
                        if access == "write" {
                            pending_update = Some(path.clone());
                        } else if access == "rename"
                            && let Some(source) = pending_update.take()
                        {
                            rows.insert(source, "rename_from".to_string());
                        }
                        rows.insert(path, access.to_string());
                    }
                }
            }
        }
    }

    if is_shell && !has_patch {
        for (path, access) in shell_file_actions(command, input, 0) {
            rows.insert(path, access);
        }
        for nested in embedded_json_objects(command, "tools.exec_command(") {
            let nested_command = command_from_tool_input(&nested);
            for (path, access) in shell_file_actions(&nested_command, &nested, 0) {
                rows.insert(path, access);
            }
        }
    }
    rows.into_iter()
        .map(|(path, access)| ToolPath { path, access })
        .collect()
}

fn embedded_json_string(text: &str, needle: &str) -> Option<String> {
    let needle = text.find(needle)?;
    let start = text[..needle].rfind('"')?;
    let mut escaped = false;
    for (offset, ch) in text[start + 1..].char_indices() {
        if escaped {
            escaped = false;
        } else if ch == '\\' {
            escaped = true;
        } else if ch == '"' {
            return serde_json::from_str(&text[start..start + offset + 2]).ok();
        }
    }
    None
}

fn embedded_json_objects(text: &str, marker: &str) -> Vec<Value> {
    let mut rows = Vec::new();
    let mut offset = 0;
    while let Some(found) = text[offset..].find(marker) {
        let start = offset + found + marker.len();
        let Some(open) = text[start..].find('{').map(|value| start + value) else {
            break;
        };
        let mut depth = 0;
        let mut quote = false;
        let mut escaped = false;
        let mut end = None;
        for (index, ch) in text[open..].char_indices() {
            if escaped {
                escaped = false;
            } else if ch == '\\' && quote {
                escaped = true;
            } else if ch == '"' {
                quote = !quote;
            } else if !quote && ch == '{' {
                depth += 1;
            } else if !quote && ch == '}' {
                depth -= 1;
                if depth == 0 {
                    end = Some(open + index + 1);
                    break;
                }
            }
        }
        let Some(end) = end else { break };
        if let Ok(value) = serde_json::from_str(&text[open..end]) {
            rows.push(value);
        }
        offset = end;
    }
    rows
}

fn shell_file_actions(command: &str, input: &Value, depth: usize) -> Vec<(String, String)> {
    if depth > 2 {
        return Vec::new();
    }
    let mut cwd = ["workdir", "cwd"]
        .iter()
        .find_map(|key| input.get(*key).and_then(Value::as_str))
        .map(PathBuf::from);
    let mut rows = Vec::new();
    for parts in shell_segments(command) {
        let Some(command_index) = shell_command_index(&parts) else {
            continue;
        };
        let name = process_name_from_part(&parts[command_index]).unwrap_or_default();
        let operands = &parts[command_index + 1..];
        if name == "cd" {
            if let Some(path) = operands.iter().find(|value| !value.starts_with('-')) {
                let path = PathBuf::from(path);
                cwd = Some(if path.is_absolute() {
                    path
                } else {
                    cwd.take().unwrap_or_default().join(path)
                });
            }
            continue;
        }
        let mut actions = shell_segment_actions(&name, operands, input, depth);
        for (path, _) in &mut actions {
            if !path.starts_with(['~', '$'])
                && !Path::new(path).is_absolute()
                && let Some(base) = &cwd
            {
                *path = base.join(&*path).to_string_lossy().into_owned();
            }
            *path = clean_path_token(path);
        }
        rows.extend(actions.into_iter().filter(|(path, _)| !path.is_empty()));
    }
    rows
}

fn shell_segment_actions(
    name: &str,
    operands: &[String],
    input: &Value,
    depth: usize,
) -> Vec<(String, String)> {
    let mut rows = Vec::new();
    let mut values = Vec::new();
    let mut index = 0;
    while index < operands.len() {
        if is_redirection_token(&operands[index]) {
            if let Some(path) = operands.get(index + 1)
                && plausible_path_token(path)
            {
                let access = if [">", ">>", "&>", "&>>"].contains(&operands[index].as_str()) {
                    "write"
                } else if ["<", "<>"].contains(&operands[index].as_str()) {
                    "read"
                } else {
                    index += 2;
                    continue;
                };
                rows.push((path.clone(), access.into()));
            }
            index += 2;
            continue;
        }
        values.push(operands[index].clone());
        index += 1;
    }
    let paths = |items: &[String]| {
        items
            .iter()
            .filter(|value| !value.starts_with('-') && plausible_path_token(value))
            .cloned()
            .collect::<Vec<_>>()
    };
    match name {
        "bash" | "sh" | "zsh" => {
            for index in 0..values.len().saturating_sub(1) {
                if ["-c", "-lc", "-cl"].contains(&values[index].as_str()) {
                    rows.extend(shell_file_actions(&values[index + 1], input, depth + 1));
                    break;
                }
            }
        }
        "cp" => {
            let paths = paths(&values);
            if let Some((target, sources)) = paths.split_last() {
                rows.extend(sources.iter().cloned().map(|path| (path, "read".into())));
                rows.push((target.clone(), "create".into()));
            }
        }
        "mv" => {
            let paths = paths(&values);
            if let Some((target, sources)) = paths.split_last() {
                rows.extend(
                    sources
                        .iter()
                        .cloned()
                        .map(|path| (path, "rename_from".into())),
                );
                rows.push((target.clone(), "rename".into()));
            }
        }
        "rm" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "delete".into())),
        ),
        "touch" | "install" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "create".into())),
        ),
        "tee" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "write".into())),
        ),
        "cat" | "head" | "tail" | "nl" | "wc" | "source" | "." => {
            rows.extend(paths(&values).into_iter().map(|path| (path, "read".into())))
        }
        "sed" => {
            let in_place = values.iter().any(|value| {
                value == "-i" || value.starts_with("-i") || value.starts_with("--in-place")
            });
            let mut script_seen = false;
            for value in &values {
                if value.starts_with('-') {
                    continue;
                }
                if !script_seen {
                    script_seen = true;
                } else if plausible_path_token(value) {
                    rows.push((
                        value.clone(),
                        if in_place { "write" } else { "read" }.into(),
                    ));
                }
            }
        }
        "find" => rows.extend(
            values
                .iter()
                .take_while(|value| !value.starts_with('-') && value.as_str() != "!")
                .filter(|value| plausible_path_token(value))
                .cloned()
                .map(|path| (path, "read".into())),
        ),
        "rg" | "grep" | "jq" => {
            let mut expression_seen = values.iter().any(|value| value == "--files");
            for value in &values {
                if value.starts_with('-') {
                    continue;
                }
                if !expression_seen {
                    expression_seen = true;
                } else if plausible_path_token(value) {
                    rows.push((value.clone(), "read".into()));
                }
            }
        }
        _ => {}
    }
    rows
}

fn collect_path_fields(value: &Value, access: &str, out: &mut BTreeMap<String, String>) {
    match value {
        Value::Object(object) => {
            for (key, value) in object {
                let key = key.to_ascii_lowercase();
                if matches!(
                    key.as_str(),
                    "path" | "file_path" | "filepath" | "notebook_path" | "old_path" | "new_path"
                ) && let Some(path) = value.as_str()
                {
                    let path = clean_path_token(path);
                    if !path.is_empty() {
                        out.insert(path, access.to_string());
                    }
                } else if value.is_object() || value.is_array() {
                    collect_path_fields(value, access, out);
                }
            }
        }
        Value::Array(values) => {
            for value in values {
                collect_path_fields(value, access, out);
            }
        }
        _ => {}
    }
}

fn clean_path_token(value: &str) -> String {
    value
        .trim()
        .trim_matches(['"', '\'', '`', ',', ':'])
        .trim_start_matches("file://")
        .to_string()
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

/// Tokenize only the high-confidence shell subset needed for file evidence.
/// Heredoc bodies are data, so they are removed before splitting commands.
fn shell_segments(command: &str) -> Vec<Vec<String>> {
    fn flush_word(tokens: &mut Vec<String>, current: &mut String) {
        if !current.is_empty() {
            tokens.push(std::mem::take(current));
        }
    }
    fn flush_segment(segments: &mut Vec<Vec<String>>, tokens: &mut Vec<String>) {
        if !tokens.is_empty() {
            segments.push(std::mem::take(tokens));
        }
    }

    let command = strip_heredoc_bodies(command);
    let mut segments = Vec::new();
    let mut tokens = Vec::new();
    let mut current = String::new();
    let mut quote = None;
    let mut escaped = false;
    let mut chars = command.chars().peekable();
    while let Some(ch) = chars.next() {
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
        } else if ch == '#' && current.is_empty() {
            for next in chars.by_ref() {
                if next == '\n' {
                    flush_segment(&mut segments, &mut tokens);
                    break;
                }
            }
        } else if ch.is_whitespace() {
            flush_word(&mut tokens, &mut current);
            if ch == '\n' {
                flush_segment(&mut segments, &mut tokens);
            }
        } else if ch == '&' && chars.peek() == Some(&'>') {
            flush_word(&mut tokens, &mut current);
            chars.next();
            let operator = if chars.peek() == Some(&'>') {
                chars.next();
                "&>>"
            } else {
                "&>"
            };
            tokens.push(operator.into());
        } else if matches!(ch, ';' | '|' | '(' | ')') || ch == '&' {
            flush_word(&mut tokens, &mut current);
            if (ch == '|' || ch == '&') && chars.peek() == Some(&ch) {
                chars.next();
            }
            flush_segment(&mut segments, &mut tokens);
        } else if ch == '>' || ch == '<' {
            flush_word(&mut tokens, &mut current);
            let mut operator = ch.to_string();
            while chars.peek() == Some(&ch) && operator.len() < 3 {
                operator.push(chars.next().expect("peeked redirection"));
            }
            tokens.push(operator);
        } else {
            current.push(ch);
        }
    }
    flush_word(&mut tokens, &mut current);
    flush_segment(&mut segments, &mut tokens);
    segments
}

fn strip_heredoc_bodies(command: &str) -> String {
    fn delimiters(line: &str) -> Vec<String> {
        let bytes = line.as_bytes();
        let mut output = Vec::new();
        let mut index = 0;
        while index + 1 < bytes.len() {
            if bytes[index] != b'<' || bytes[index + 1] != b'<' {
                index += 1;
                continue;
            }
            index += 2;
            if bytes.get(index) == Some(&b'<') {
                index += 1;
                continue;
            }
            if bytes.get(index) == Some(&b'-') {
                index += 1;
            }
            while bytes.get(index).is_some_and(u8::is_ascii_whitespace) {
                index += 1;
            }
            let quote = bytes
                .get(index)
                .copied()
                .filter(|value| *value == b'\'' || *value == b'"');
            if quote.is_some() {
                index += 1;
            }
            let start = index;
            while let Some(value) = bytes.get(index) {
                if quote.is_some_and(|quote| *value == quote)
                    || (quote.is_none()
                        && (value.is_ascii_whitespace() || b";|&><".contains(value)))
                {
                    break;
                }
                index += 1;
            }
            if start < index {
                output.push(line[start..index].to_string());
            }
        }
        output
    }

    let mut pending = VecDeque::<String>::new();
    let mut output = Vec::new();
    for line in command.lines() {
        if let Some(delimiter) = pending.front() {
            if line.trim_start_matches('\t').trim_end() == delimiter {
                pending.pop_front();
            }
            continue;
        }
        output.push(line);
        pending.extend(delimiters(line));
    }
    output.join("\n")
}

fn is_redirection_token(token: &str) -> bool {
    [">", ">>", "&>", "&>>", "<", "<<", "<<<", "<>"].contains(&token)
}

fn shell_command_index(parts: &[String]) -> Option<usize> {
    let mut index = 0;
    while index < parts.len() {
        let part = parts[index].as_str();
        if ["then", "do", "else"].contains(&part)
            || part.split_once('=').is_some_and(|(name, _)| {
                !name.is_empty()
                    && name
                        .chars()
                        .all(|ch| ch == '_' || ch.is_ascii_alphanumeric())
            })
        {
            index += 1;
            continue;
        }
        if ["sudo", "env", "command", "time", "timeout", "nice", "nohup"].contains(&part) {
            index += 1;
            while index < parts.len() && parts[index].starts_with('-') {
                index += 1;
            }
            continue;
        }
        return Some(index);
    }
    None
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
    let lower = part.to_ascii_lowercase();
    let components = part.split('/').collect::<Vec<_>>();
    let looks_like_sed_expression = part.starts_with("s/")
        && part.rsplit('/').next().is_some_and(|flags| {
            flags.is_empty() || flags.chars().all(|flag| "gimpe".contains(flag))
        });
    let looks_like_slash_separated_phrase = components.len() >= 3
        && components.iter().all(|component| {
            component.chars().all(char::is_alphabetic)
                && component.chars().next().is_some_and(char::is_uppercase)
        });
    if part.is_empty()
        || part.starts_with('-')
        || part.starts_with('$')
        || part.starts_with('~')
        || part.starts_with("http://")
        || part.starts_with("https://")
        || lower.starts_with("origin/")
        || lower.starts_with("refs/")
        || lower.starts_with("repos/")
        || part == "HEAD"
        || part.starts_with("HEAD.")
        || part.contains("...")
        || looks_like_slash_separated_phrase
        || looks_like_sed_expression
        || part.len() > 140
        || part.chars().any(char::is_whitespace)
        || part.chars().any(|c| "{}()=;<>|`*?[]\"#$,:@^!".contains(c))
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

fn codex_exec_option_arity(arg: &str) -> Option<usize> {
    if arg.contains('=') && arg.starts_with("--") {
        return Some(1);
    }

    match arg {
        "--json"
        | "--skip-git-repo-check"
        | "--ephemeral"
        | "--ignore-user-config"
        | "--full-auto"
        | "--dangerously-bypass-approvals-and-sandbox" => Some(1),
        "-C" | "-a" | "-s" | "-m" | "-c" | "-p" | "--cd" | "--model" | "--sandbox"
        | "--profile" | "--config" | "--ask-for-approval" | "--approval-policy"
        | "--output-format" | "--color" => Some(2),
        _ => None,
    }
}

fn shell_words(input: &str) -> Option<Vec<String>> {
    let mut words = Vec::new();
    let mut current = String::new();
    let mut quote = None::<char>;
    let mut chars = input.chars().peekable();

    while let Some(ch) = chars.next() {
        match (quote, ch) {
            (None, c) if c.is_whitespace() => {
                if !current.is_empty() {
                    words.push(std::mem::take(&mut current));
                }
            }
            (None, '\'' | '"') => quote = Some(ch),
            (Some(q), c) if c == q => quote = None,
            (_, '\\') => {
                if let Some(next) = chars.next() {
                    current.push(next);
                }
            }
            _ => current.push(ch),
        }
    }
    if quote.is_some() {
        return None;
    }
    if !current.is_empty() {
        words.push(current);
    }
    Some(words)
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
    fn codex_cumulative_usage_separates_cached_input() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5.6-sol"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":19184,"cached_input_tokens":9984,"output_tokens":11,"total_tokens":19195}}}}"#,
        );

        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");

        assert_eq!(session.usage.input_tokens, 9_200);
        assert_eq!(session.usage.cache_read_tokens, 9_984);
        assert_eq!(session.usage.output_tokens, 11);
        assert_eq!(session.usage.total_tokens, 19_195);
    }

    #[test]
    fn codex_exec_prompt_handles_latest_cli_options() {
        let command = concat!(
            "/tmp/tools/bin/codex exec --skip-git-repo-check --ignore-user-config ",
            "-c model_provider=\"agentsight-mock\" ",
            "-c model_providers.agentsight-mock.name=\"AgentSight Mock\" ",
            "--sandbox read-only --model gpt-agentsight-mock ",
            "agentsight mock prompt collect this exact text"
        );

        assert_eq!(
            codex_exec_prompt(command).as_deref(),
            Some("agentsight mock prompt collect this exact text")
        );
    }

    #[test]
    fn file_actions_ignore_patch_and_heredoc_bodies() {
        let patch = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec",
            &json!({"text": r#"const patch = "*** Begin Patch\n*** Update File: src/lib.rs\n+#!/bin/sh\n+docs/not-a-file.md\n*** End Patch"; tools.apply_patch(patch)"#}),
            None,
        );
        assert_eq!(
            patch.paths,
            vec![ToolPath {
                path: "src/lib.rs".into(),
                access: "write".into(),
            }]
        );

        let heredoc = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec_command",
            &json!({"cmd": "cat <<'EOF'\n#!/bin/sh\nsrc/not-a-file.rs\nEOF\ncat src/real.rs"}),
            None,
        );
        assert_eq!(heredoc.paths.len(), 1);
        assert_eq!(heredoc.paths[0].path, "src/real.rs");
    }

    #[test]
    fn codex_exec_wrapper_projects_nested_shell_actions() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec",
            &json!({"text": r#"const r = await tools.exec_command({"cmd":"cat src/lib.rs && sed -i 's/a/b/' src/main.rs","workdir":"/repo"});"#}),
            None,
        );
        assert_eq!(
            event
                .paths
                .iter()
                .map(|path| (path.path.as_str(), path.access.as_str()))
                .collect::<Vec<_>>(),
            vec![("/repo/src/lib.rs", "read"), ("/repo/src/main.rs", "write")]
        );
    }

    #[test]
    fn file_actions_are_conservative_for_unknown_and_write_tools() {
        let unknown = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "mcp_resource",
            &json!({"path": "src/not-a-file.rs"}),
            None,
        );
        assert!(unknown.paths.is_empty());

        let write = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "Write",
            &json!({"file_path": "src/existing.rs", "content": "changed"}),
            None,
        );
        assert_eq!(write.paths[0].access, "write");
    }

    #[test]
    fn patch_move_keeps_the_immediately_preceding_source() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "apply_patch",
            &json!({"patch": "*** Begin Patch\n*** Update File: src/a.rs\n*** Move to: src/b.rs\n*** Update File: src/c.rs\n*** End Patch"}),
            None,
        );
        assert!(event.paths.contains(&ToolPath {
            path: "src/a.rs".into(),
            access: "rename_from".into(),
        }));
        assert!(event.paths.contains(&ToolPath {
            path: "src/b.rs".into(),
            access: "rename".into(),
        }));
        assert!(event.paths.contains(&ToolPath {
            path: "src/c.rs".into(),
            access: "write".into(),
        }));
    }

    #[test]
    fn tool_outputs_mark_failed_file_actions() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"cwd":"/repo"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"rm src/lib.rs\"}"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call_output","call_id":"c1","output":"Process exited with code 1"}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");
        assert_eq!(session.events.tools[0].status, "fail");
        assert_eq!(session.events.tools[0].paths[0].access, "delete");
    }
}
