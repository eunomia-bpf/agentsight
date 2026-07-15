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
    AgentSession, EditSummary, LlmResponse, PathReference, SessionCandidate, SessionDirStat,
    SessionEvents, TokenUsage, ToolEvent, UserPrompt,
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
            if let Some(ts_ms) = iso_ms(ts) {
                let first_timestamp = acc.start_timestamp_ms.is_none();
                acc.start_timestamp_ms = Some(
                    acc.start_timestamp_ms
                        .map_or(ts_ms, |start| start.min(ts_ms)),
                );
                acc.end_timestamp_ms = Some(if first_timestamp {
                    ts_ms
                } else {
                    acc.end_timestamp_ms.map_or(ts_ms, |end| end.max(ts_ms))
                });
            }
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
                if ptype == "patch_apply_end" {
                    let call_id = payload
                        .get("call_id")
                        .and_then(Value::as_str)
                        .map(str::to_string);
                    let mut event = tool_event_from_input(
                        acc.cwd.as_deref(),
                        ts_ms_from_event(&obj),
                        current_prompt_index,
                        "apply_patch",
                        payload,
                        call_id,
                    );
                    event.status = if payload
                        .get("success")
                        .and_then(Value::as_bool)
                        .unwrap_or(false)
                    {
                        "success"
                    } else {
                        "fail"
                    }
                    .to_string();
                    if let Some(index) = event
                        .call_id
                        .as_deref()
                        .and_then(|call_id| call_index.get(call_id))
                        .copied()
                    {
                        if let Some(existing) = events.tools.get_mut(index) {
                            existing.status = event.status;
                            if existing.path_refs.is_empty() {
                                existing.path_refs = event.path_refs;
                            }
                            if existing.edit_summary.is_none() {
                                existing.edit_summary = event.edit_summary;
                            }
                        }
                    } else {
                        acc.add_tool("apply_patch");
                        if let Some(call_id) = event.call_id.clone() {
                            call_index.insert(call_id, events.tools.len());
                        }
                        events.tools.push(event);
                    }
                }
                if ptype == "token_count"
                    && let Some(usage) = payload.pointer("/info/total_token_usage")
                {
                    let name = if codex_model.is_empty() {
                        "unknown"
                    } else {
                        &codex_model
                    };
                    let raw_input = json_i64(usage, "input_tokens").max(0);
                    let output = json_i64(usage, "output_tokens").max(0);
                    let cache = json_i64(usage, "cached_input_tokens").max(0);
                    let input = codex_uncached_input(raw_input, cache);
                    acc.set_usage(name, input, output, 0, cache, input + output);
                }
                if matches!(ptype, "token_count" | "token_usage") {
                    let info = payload
                        .get("info")
                        .or_else(|| payload.get("usage"))
                        .unwrap_or(payload);
                    let total_usage = info.get("total_token_usage");
                    let token_usage = info.get("last_token_usage").or(total_usage).unwrap_or(info);
                    let is_cumulative_usage =
                        total_usage.is_some() && info.get("last_token_usage").is_none();
                    let raw_input_tokens = json_u64(token_usage, "input_tokens");
                    let output_tokens = json_u64(token_usage, "output_tokens");
                    let cache_tokens = json_u64(token_usage, "cached_input_tokens");
                    let uncached_input_tokens = raw_input_tokens.saturating_sub(cache_tokens);
                    let input_tokens = if is_cumulative_usage {
                        uncached_input_tokens
                    } else {
                        raw_input_tokens
                    };
                    let raw_total_tokens = json_u64(token_usage, "total_tokens")
                        .max(json_u64(info, "total_tokens"))
                        .max(json_u64(info, "tokens"));
                    let total_tokens = if is_cumulative_usage {
                        uncached_input_tokens + output_tokens
                    } else {
                        raw_total_tokens
                    };
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
                        if let Some(last_usage) =
                            events.llm_responses.iter_mut().rev().find(|response| {
                                response.prompt_index == current_prompt_index
                                    && response.tag == "usage"
                            })
                        {
                            last_usage.ts_ms = ts_ms_from_event(&obj);
                            last_usage.input_tokens = input_tokens;
                            last_usage.output_tokens = output_tokens;
                            last_usage.cache_tokens = cache_tokens;
                            last_usage.total_tokens = total_tokens;
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
                            tag: "usage".to_string(),
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

fn parse_gemini_json(path: &Path, updated: SystemTime, content: &str) -> Option<AgentSession> {
    let root: Value = serde_json::from_str(content).ok()?;
    let mut acc = SessionAccumulator::new(AGENT_GEMINI, path, updated);
    let mut events = SessionEvents::default();
    let mut current_prompt_index = 0usize;
    acc.project_hash = root
        .get("projectHash")
        .and_then(Value::as_str)
        .map(str::to_string);
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
                        let tool_input = call.get("args").unwrap_or(call);
                        let mut event = tool_event_from_input(
                            acc.cwd.as_deref(),
                            ts_ms,
                            current_prompt_index,
                            name,
                            tool_input,
                            call.get("id").and_then(Value::as_str).map(str::to_string),
                        );
                        if let Some(status) = call.get("status").and_then(Value::as_str) {
                            event.status = status.to_ascii_lowercase();
                        }
                        events.tools.push(event);
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
    project_hash: Option<String>,
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
            project_hash: None,
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
            project_hash: self.project_hash,
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
    let lower_name = name.to_ascii_lowercase();
    let effect = if lower_name == "apply_patch"
        || lower_name.contains("write")
        || lower_name.contains("edit")
        || lower_name.contains("replace")
        || command.contains("*** ")
    {
        "write".to_string()
    } else if lower_name.contains("read")
        || lower_name.contains("glob")
        || lower_name.contains("grep")
        || lower_name.contains("search")
    {
        "read".to_string()
    } else {
        command_effect(&command)
    };
    let cwd = cwd.unwrap_or("");
    let path_groups = extract_path_groups(Path::new(cwd), name, input, &command);
    let path_refs = extract_path_references(Path::new(cwd), name, input, &command, &effect);
    let edit_summary = edit_summary_from_input(name, input, &command, &effect, &path_refs);
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
        path_refs,
        edit_summary,
        domains,
        call_id,
    }
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
    } else if ["tee", "cp", "mv", "rm", "mkdir", "touch"].contains(&cmd.as_str())
        || (cmd == "sed" && (text.contains(" -i") || text.contains("--in-place")))
        || (["python", "python3", "node", "npm"].contains(&cmd.as_str())
            && (text.contains('>')
                || text.contains("--write")
                || text.contains("write_text")
                || text.contains("writefile")))
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

fn extract_path_references(
    project_root: &Path,
    name: &str,
    input: &Value,
    command: &str,
    effect: &str,
) -> Vec<PathReference> {
    let lower_name = name.to_ascii_lowercase();
    let default_access = if effect == "write" {
        "write"
    } else if lower_name.contains("read")
        || lower_name.contains("search")
        || lower_name.contains("glob")
        || lower_name.contains("grep")
    {
        "read"
    } else {
        "reference"
    };
    let mut refs = BTreeMap::<(String, String), String>::new();
    collect_input_path_references(input, project_root, default_access, 0, &mut refs);

    for (path, access) in patch_path_references(command) {
        if let Some(path) = repository_relative_path(project_root, &path) {
            refs.insert((path, access.to_string()), "patch".to_string());
        }
    }
    if let Some(patch) = find_string_field(input, &["patch", "input"], 0) {
        for (path, access) in patch_path_references(patch) {
            if let Some(path) = repository_relative_path(project_root, &path) {
                refs.insert((path, access.to_string()), "patch".to_string());
            }
        }
    }

    if lower_name.contains("bash") || lower_name.contains("exec") || lower_name.contains("shell") {
        for part in split_shell(command) {
            if plausible_path_token(&part)
                && let Some(path) = repository_relative_path(project_root, &part)
            {
                refs.entry((path, default_access.to_string()))
                    .or_insert_with(|| "command".to_string());
            }
        }
    }

    refs.into_iter()
        .map(|((path, access), source)| PathReference {
            path,
            access,
            source,
        })
        .collect()
}

fn collect_input_path_references(
    value: &Value,
    project_root: &Path,
    access: &str,
    depth: usize,
    out: &mut BTreeMap<(String, String), String>,
) {
    if depth > 4 {
        return;
    }
    match value {
        Value::Object(map) => {
            for (key, value) in map {
                let lower = key.to_ascii_lowercase();
                if [
                    "file_path",
                    "filepath",
                    "path",
                    "notebook_path",
                    "dir_path",
                    "directory",
                ]
                .contains(&lower.as_str())
                    && let Some(raw) = value.as_str()
                    && let Some(path) = repository_relative_path(project_root, raw)
                {
                    out.insert((path, access.to_string()), format!("input:{key}"));
                }
                if lower == "changes"
                    && let Some(changes) = value.as_object()
                {
                    for raw in changes.keys() {
                        if let Some(path) = repository_relative_path(project_root, raw) {
                            out.insert((path, "write".to_string()), "input:changes".to_string());
                        }
                    }
                }
                collect_input_path_references(value, project_root, access, depth + 1, out);
            }
        }
        Value::Array(values) => {
            for value in values {
                collect_input_path_references(value, project_root, access, depth + 1, out);
            }
        }
        _ => {}
    }
}

fn repository_relative_path(project_root: &Path, raw: &str) -> Option<String> {
    let raw = raw.trim().trim_matches(['"', '\'']);
    // A shell-relative token beginning with a home/environment expansion is
    // not relative to the repository, even though `Path` treats it as such.
    // Never serialize it as a repository path: apart from being semantically
    // wrong, native histories commonly expose private tool-state locations in
    // this form (for example `~/.claude/...`).
    if raw.is_empty() || raw.starts_with('~') || raw.starts_with('$') {
        return None;
    }
    let path = Path::new(raw);
    let relative = if path.is_absolute() {
        if project_root.as_os_str().is_empty() {
            return None;
        }
        path.strip_prefix(project_root).ok()?
    } else {
        path
    };
    let mut parts = Vec::new();
    for component in relative.components() {
        match component {
            std::path::Component::CurDir => {}
            std::path::Component::Normal(part) => {
                let part = part.to_str()?;
                if part.is_empty() {
                    return None;
                }
                parts.push(part);
            }
            std::path::Component::ParentDir
            | std::path::Component::RootDir
            | std::path::Component::Prefix(_) => return None,
        }
    }
    (!parts.is_empty()).then(|| parts.join("/"))
}

fn patch_path_references(text: &str) -> Vec<(String, &'static str)> {
    let mut refs = Vec::new();
    for line in text.lines() {
        for (prefix, access) in [
            ("*** Add File: ", "write"),
            ("*** Update File: ", "write"),
            ("*** Delete File: ", "write"),
            ("*** Move to: ", "write"),
        ] {
            if let Some(path) = line.trim().strip_prefix(prefix) {
                refs.push((path.trim().to_string(), access));
            }
        }
    }
    refs
}

fn edit_summary_from_input(
    name: &str,
    input: &Value,
    command: &str,
    effect: &str,
    path_refs: &[PathReference],
) -> Option<EditSummary> {
    if effect != "write" {
        return None;
    }
    let write_paths = path_refs
        .iter()
        .filter(|reference| reference.access == "write")
        .map(|reference| reference.path.as_str())
        .collect::<BTreeSet<_>>();
    // An event-level fingerprint can only be compared safely with a Git hunk
    // when it describes exactly one repository path. Multi-file patches keep
    // their path observations but deliberately carry no exact-hunk claim.
    if write_paths.len() != 1 {
        return None;
    }
    let before = find_string_field(input, &["old_string", "oldText", "before"], 0);
    let after = find_string_field(input, &["new_string", "newText", "content", "after"], 0);
    if before.is_some() || after.is_some() {
        return Some(EditSummary {
            before_bytes: before.map_or(0, |value| value.len() as u64),
            after_bytes: after.map_or(0, |value| value.len() as u64),
            removed_lines: before.map_or(0, line_count),
            added_lines: after.map_or(0, line_count),
            before_hash: before.map(content_fingerprint),
            after_hash: after.map(content_fingerprint),
            payload_kind: if before.is_some() {
                "replace".to_string()
            } else {
                "write".to_string()
            },
        });
    }

    let patch = find_string_field(input, &["patch", "input", "unified_diff"], 0)
        .filter(|value| value.contains("*** Begin Patch") || value.contains("@@"))
        .or_else(|| {
            (command.contains("*** Begin Patch") || command.contains("@@")).then_some(command)
        });
    if let Some(patch) = patch {
        let hunk_markers = patch.lines().filter(|line| line.starts_with("@@")).count();
        let file_markers = patch
            .lines()
            .filter(|line| {
                [
                    "*** Add File: ",
                    "*** Update File: ",
                    "*** Delete File: ",
                    "*** Move to: ",
                ]
                .iter()
                .any(|prefix| line.trim().starts_with(prefix))
            })
            .count();
        if hunk_markers > 1 || file_markers > 1 {
            return None;
        }
        let added = patch
            .lines()
            .filter(|line| line.starts_with('+') && !line.starts_with("+++"))
            .map(|line| &line[1..])
            .collect::<Vec<_>>();
        let removed = patch
            .lines()
            .filter(|line| line.starts_with('-') && !line.starts_with("---"))
            .map(|line| &line[1..])
            .collect::<Vec<_>>();
        let added_text = added.join("\n");
        let removed_text = removed.join("\n");
        return Some(EditSummary {
            before_bytes: removed_text.len() as u64,
            after_bytes: added_text.len() as u64,
            added_lines: added.len() as u64,
            removed_lines: removed.len() as u64,
            before_hash: (!removed.is_empty()).then(|| content_fingerprint(&removed_text)),
            after_hash: (!added.is_empty()).then(|| content_fingerprint(&added_text)),
            payload_kind: "patch".to_string(),
        });
    }

    Some(EditSummary {
        payload_kind: one_word(name, "write"),
        ..EditSummary::default()
    })
}

fn find_string_field<'a>(value: &'a Value, keys: &[&str], depth: usize) -> Option<&'a str> {
    if depth > 4 {
        return None;
    }
    match value {
        Value::Object(map) => {
            for key in keys {
                if let Some(value) = map.get(*key).and_then(Value::as_str) {
                    return Some(value);
                }
            }
            map.values()
                .find_map(|value| find_string_field(value, keys, depth + 1))
        }
        Value::Array(values) => values
            .iter()
            .find_map(|value| find_string_field(value, keys, depth + 1)),
        _ => None,
    }
}

fn line_count(value: &str) -> u64 {
    if value.is_empty() {
        0
    } else {
        value.lines().count() as u64
    }
}

fn content_fingerprint(value: &str) -> String {
    let normalized = value.replace("\r\n", "\n");
    short_hash(normalized.trim_end_matches('\n'), 24)
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

fn codex_uncached_input(input: i64, cache: i64) -> i64 {
    input.saturating_sub(cache)
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
    fn codex_token_count_uses_uncached_cumulative_totals() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5.6-sol","cwd":"/repo"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"user_message","message":"run tests"}}"#,
            "\n",
            r#"{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":2109758505,"output_tokens":5136738,"cached_input_tokens":2069213696,"total_tokens":2114895243}}}}"#,
        );

        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");

        assert_eq!(session.usage.input_tokens, 40_544_809);
        assert_eq!(session.usage.output_tokens, 5_136_738);
        assert_eq!(session.usage.cache_read_tokens, 2_069_213_696);
        assert_eq!(session.usage.total_tokens, 45_681_547);

        let response = &session.events.llm_responses[0];
        assert_eq!(response.input_tokens, 40_544_809);
        assert_eq!(response.output_tokens, 5_136_738);
        assert_eq!(response.cache_tokens, 2_069_213_696);
        assert_eq!(response.total_tokens, 45_681_547);
        assert_eq!(codex_uncached_input(99_000_000, 88_000_000), 11_000_000);
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
    fn common_shell_mutators_are_classified_as_writes() {
        for command in [
            "rm src/old.rs",
            "mv src/old.rs src/new.rs",
            "cp src/a.rs src/b.rs",
            "sed -i 's/a/b/' src/lib.rs",
            "sed --in-place=.bak 's/a/b/' src/lib.rs",
            "touch src/new.rs",
        ] {
            assert_eq!(command_effect(command), "write", "{command}");
        }
        assert_eq!(command_effect("sed -n '1,5p' src/lib.rs"), "read");
    }

    #[test]
    fn tool_events_preserve_private_body_free_path_and_edit_evidence() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(42),
            0,
            "Edit",
            &json!({
                "file_path": "/repo/src/lib.rs",
                "old_string": "fn old() {}\n",
                "new_string": "fn new() {}\n"
            }),
            Some("call-1".to_string()),
        );

        assert_eq!(event.effect, "write");
        assert_eq!(event.path_refs.len(), 1);
        assert_eq!(event.path_refs[0].path, "src/lib.rs");
        assert_eq!(event.path_refs[0].access, "write");
        let summary = event.edit_summary.expect("edit summary");
        assert_eq!(summary.payload_kind, "replace");
        assert_eq!(summary.removed_lines, 1);
        assert_eq!(summary.added_lines, 1);
        assert_ne!(summary.before_hash, summary.after_hash);

        let encoded = serde_json::to_string(&summary).expect("serialize summary");
        assert!(!encoded.contains("fn old"));
        assert!(!encoded.contains("fn new"));
    }

    #[test]
    fn patch_paths_keep_repository_scope_and_drop_external_paths() {
        let patch = concat!(
            "*** Begin Patch\n",
            "*** Update File: src/main.rs\n",
            "@@\n-old\n+new\n",
            "*** End Patch"
        );
        let event = tool_event_from_input(
            Some("/repo"),
            Some(42),
            0,
            "apply_patch",
            &json!({"input": patch, "path": "/outside/secret.txt"}),
            None,
        );

        assert_eq!(event.path_refs.len(), 1);
        assert_eq!(event.path_refs[0].path, "src/main.rs");
        assert_eq!(event.edit_summary.expect("patch summary").added_lines, 1);
    }

    #[test]
    fn repository_paths_reject_home_and_environment_relative_tokens() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(42),
            0,
            "Bash",
            &json!({
                "command": "rg needle ~/.claude/projects $HOME/.codex ~/workspace/other src/lib.rs"
            }),
            None,
        );

        assert_eq!(event.path_refs.len(), 1);
        assert_eq!(event.path_refs[0].path, "src/lib.rs");
        assert!(event.path_refs.iter().all(|reference| {
            !reference.path.starts_with('~') && !reference.path.starts_with('$')
        }));
    }

    #[test]
    fn multi_file_and_multi_hunk_patches_do_not_claim_one_exact_edit() {
        let multi_file = concat!(
            "*** Begin Patch\n",
            "*** Update File: src/a.rs\n",
            "@@\n-old-a\n+new-a\n",
            "*** Update File: src/b.rs\n",
            "@@\n-old-b\n+new-b\n",
            "*** End Patch"
        );
        let event = tool_event_from_input(
            Some("/repo"),
            Some(42),
            0,
            "apply_patch",
            &json!({"input": multi_file}),
            None,
        );
        assert_eq!(event.path_refs.len(), 2);
        assert!(event.edit_summary.is_none());

        let multi_hunk = concat!(
            "*** Begin Patch\n",
            "*** Update File: src/a.rs\n",
            "@@\n-old-a\n+new-a\n",
            "@@\n-old-b\n+new-b\n",
            "*** End Patch"
        );
        let event = tool_event_from_input(
            Some("/repo"),
            Some(42),
            0,
            "apply_patch",
            &json!({"input": multi_hunk}),
            None,
        );
        assert_eq!(event.path_refs.len(), 1);
        assert!(event.edit_summary.is_none());
    }

    #[test]
    fn gemini_project_hash_and_relative_paths_survive_normalization() {
        let content = r#"{
            "sessionId":"gemini-session",
            "projectHash":"abc123",
            "startTime":"2026-07-14T10:00:00Z",
            "lastUpdated":"2026-07-14T10:01:00Z",
            "messages":[{
                "type":"gemini",
                "timestamp":"2026-07-14T10:00:30Z",
                "model":"gemini-test",
                "content":"done",
                "toolCalls":[{
                    "id":"tool-1",
                    "name":"read_file",
                    "args":{"file_path":"src/lib.rs"},
                    "status":"success"
                }]
            }]
        }"#;
        let session = parse_session_content(
            AGENT_GEMINI,
            Path::new("/tmp/session-gemini.json"),
            UNIX_EPOCH,
            content,
        )
        .expect("gemini session");

        assert_eq!(session.project_hash.as_deref(), Some("abc123"));
        assert_eq!(session.events.tools[0].effect, "read");
        assert_eq!(session.events.tools[0].status, "success");
        assert_eq!(session.events.tools[0].path_refs[0].path, "src/lib.rs");
    }

    #[test]
    fn codex_usage_updates_coalesce_within_a_prompt() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5","cwd":"/repo"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:00Z","type":"event_msg","payload":{"type":"user_message","message":"work"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:01Z","type":"event_msg","payload":{"type":"token_count","info":{"last_token_usage":{"input_tokens":10,"output_tokens":2,"total_tokens":12}}}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:02Z","type":"event_msg","payload":{"type":"token_count","info":{"last_token_usage":{"input_tokens":20,"output_tokens":4,"total_tokens":24}}}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session-codex.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("codex session");

        assert_eq!(session.events.llm_responses.len(), 1);
        assert_eq!(session.events.llm_responses[0].total_tokens, 24);
        assert_eq!(session.events.llm_responses[0].tag, "usage");
    }

    #[test]
    fn codex_patch_apply_events_expose_write_paths_without_bodies() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5","cwd":"/repo"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:00Z","type":"event_msg","payload":{"type":"user_message","message":"edit"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:01Z","type":"event_msg","payload":{"type":"patch_apply_end","call_id":"patch-1","success":true,"changes":{"/repo/src/lib.rs":{"type":"update","unified_diff":"@@ -1 +1 @@\n-old\n+new"}}}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session-codex.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("codex session");

        let event = &session.events.tools[0];
        assert_eq!(event.effect, "write");
        assert_eq!(event.status, "success");
        assert_eq!(event.path_refs[0].path, "src/lib.rs");
        assert_eq!(event.edit_summary.as_ref().unwrap().payload_kind, "patch");
    }

    #[test]
    fn codex_patch_completion_updates_the_existing_tool_call() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"model":"gpt-5","cwd":"/repo"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:00Z","type":"response_item","payload":{"type":"custom_tool_call","name":"apply_patch","call_id":"patch-1","arguments":"{\"input\":\"*** Begin Patch\\n*** Update File: src/lib.rs\\n@@\\n-old\\n+new\\n*** End Patch\"}"}}"#,
            "\n",
            r#"{"timestamp":"2026-07-14T10:00:01Z","type":"event_msg","payload":{"type":"patch_apply_end","call_id":"patch-1","success":true,"changes":{"/repo/src/lib.rs":{"type":"update","unified_diff":"@@ -1 +1 @@\n-old\n+new"}}}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session-codex.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("codex session");

        assert_eq!(session.events.tools.len(), 1);
        assert_eq!(session.events.tools[0].call_id.as_deref(), Some("patch-1"));
        assert_eq!(session.events.tools[0].status, "success");
        assert_eq!(session.events.tools[0].path_refs[0].path, "src/lib.rs");
    }
}
