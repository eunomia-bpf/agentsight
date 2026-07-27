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
    let mut current_cwd: Option<String> = None;

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
        match agent {
            AGENT_CLAUDE => {
                if let Some(sidechain) = obj.get("isSidechain").and_then(Value::as_bool) {
                    acc.source_role = Some(if sidechain { "subagent" } else { "root" }.into());
                }
                if let Some(id) = obj.get("agentId").and_then(Value::as_str) {
                    acc.source_agent_id = Some(id.to_string());
                }
            }
            AGENT_CODEX if obj.get("type").and_then(Value::as_str) == Some("session_meta") => {
                if let Some(id) = codex_native_root_id(&obj) {
                    acc.session_id = id.to_string();
                }
                acc.source_role = obj
                    .pointer("/payload/thread_source")
                    .and_then(Value::as_str)
                    .map(ToString::to_string)
                    .or_else(|| {
                        obj.pointer("/payload/source/subagent")
                            .is_some()
                            .then(|| "subagent".to_string())
                    })
                    .or_else(|| Some("root".to_string()));
                acc.source_agent_id = obj
                    .pointer("/payload/agent_path")
                    .and_then(Value::as_str)
                    .or_else(|| {
                        obj.pointer("/payload/agent_nickname")
                            .and_then(Value::as_str)
                    })
                    .map(ToString::to_string);
            }
            _ => {}
        }
        if let Some(row_cwd) = obj
            .get("cwd")
            .and_then(Value::as_str)
            .or_else(|| obj.pointer("/payload/cwd").and_then(Value::as_str))
            .filter(|s| !s.is_empty())
        {
            if acc.cwd.is_none() {
                acc.cwd = Some(row_cwd.to_string());
            }
            // Per-record workdir: each native record may move the working
            // directory (e.g. Claude rows carry `cwd`). The most recent
            // record cwd overrides the session-initial cwd for tool events
            // that do not set an explicit input workdir.
            current_cwd = Some(row_cwd.to_string());
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
                        let mut event = tool_event_from_input(
                            current_cwd.as_deref().or(acc.cwd.as_deref()),
                            ts_ms_from_event(&obj),
                            current_prompt_index,
                            name,
                            item.get("input").unwrap_or(&Value::Null),
                            call_id.clone(),
                        );
                        annotate_tool_source(&mut event, &obj, &model);
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
            (AGENT_CLAUDE, "queue-operation") => {
                if obj.get("operation").and_then(Value::as_str) == Some("enqueue")
                    && let Some(text) = obj.get("content").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    if acc.prompt_preview.is_none() {
                        acc.prompt_preview = Some(text.clone());
                    }
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
                if is_claude_tool_result(&obj) {
                    let fallback = obj
                        .pointer("/toolUseResult/is_error")
                        .and_then(Value::as_bool)
                        .unwrap_or(false);
                    for result in content.as_array().into_iter().flatten() {
                        let Some(id) = result.get("tool_use_id").and_then(Value::as_str) else {
                            continue;
                        };
                        if let Some(index) = call_index.get(id).copied()
                            && let Some(tool) = events.tools.get_mut(index)
                        {
                            let failed = result
                                .get("is_error")
                                .and_then(Value::as_bool)
                                .unwrap_or(fallback);
                            tool.status = if failed { "fail" } else { "ok" }.to_string();
                            tool.end_ts_ms = ts_ms_from_event(&obj);
                        }
                    }
                } else if !obj.get("isMeta").and_then(Value::as_bool).unwrap_or(false)
                    && let Some(text) = local_message_preview(content)
                {
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
                let mut event = tool_event_from_input(
                    current_cwd.as_deref().or(acc.cwd.as_deref()),
                    ts_ms_from_event(&obj),
                    current_prompt_index,
                    name,
                    &args,
                    call_id.clone(),
                );
                annotate_tool_source(&mut event, &obj, &codex_model);
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
                    let value = obj.pointer("/payload/output").unwrap_or(&Value::Null);
                    let rendered;
                    let output = if let Some(text) = value.as_str() {
                        text
                    } else {
                        rendered = value.to_string();
                        &rendered
                    };
                    tool.status = status_from_output(output).to_string();
                    tool.end_ts_ms = ts_ms_from_event(&obj);
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
    acc.source_role = Some("root".to_string());
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
                        let mut event = tool_event_from_input(
                            acc.cwd.as_deref(),
                            ts_ms,
                            current_prompt_index,
                            name,
                            call,
                            call.get("id").and_then(Value::as_str).map(str::to_string),
                        );
                        annotate_tool_source(&mut event, call, &llm_model);
                        event.status = match call.get("status").and_then(Value::as_str) {
                            Some("success") => "ok",
                            Some("error") => "fail",
                            _ => "observed",
                        }
                        .into();
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
    source_role: Option<String>,
    source_agent_id: Option<String>,
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
            source_role: None,
            source_agent_id: None,
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
            source_role: self.source_role,
            source_agent_id: self.source_agent_id,
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
        if self
            .prompts
            .last()
            .is_some_and(|prompt| prompt.text_hash == hash)
        {
            return self.prompts.len();
        }
        let index = self.prompts.len();
        self.prompts.push(UserPrompt {
            index,
            ts_ms,
            text_hash: hash,
            preview: truncate_clean(text, 180),
            tag: String::new(),
        });
        index + 1
    }
}

fn annotate_tool_source(event: &mut ToolEvent, source: &Value, model: &str) {
    event.source_event_id = source
        .get("uuid")
        .and_then(Value::as_str)
        .or_else(|| source.get("id").and_then(Value::as_str))
        .or_else(|| source.pointer("/payload/id").and_then(Value::as_str))
        .map(ToString::to_string);
    event.parent_event_id = source
        .get("parentUuid")
        .and_then(Value::as_str)
        .or_else(|| source.pointer("/payload/parent_id").and_then(Value::as_str))
        .map(ToString::to_string);
    event.model = (!model.is_empty()).then(|| model.to_string());
    event.attribution_skill = source
        .get("attributionSkill")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string);
    event.attribution_agent = source
        .get("attributionAgent")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string);
}

fn tool_event_from_input(
    cwd: Option<&str>,
    ts_ms: Option<i64>,
    prompt_index: usize,
    name: &str,
    input: &Value,
    call_id: Option<String>,
) -> ToolEvent {
    let wrapper_command = command_from_tool_input(input);
    let nested_inputs = if name.eq_ignore_ascii_case("exec") {
        embedded_json_objects(&wrapper_command, "tools.exec_command(")
    } else {
        Vec::new()
    };
    let effective_input = if nested_inputs.len() == 1 {
        &nested_inputs[0]
    } else {
        input
    };
    let command = command_from_tool_input(effective_input);
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
    let workdir = effective_input
        .get("workdir")
        .or_else(|| effective_input.get("cwd"))
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .unwrap_or(cwd)
        .to_string();
    let path_groups = extract_path_groups(Path::new(&workdir), name, effective_input, &command);
    let paths = extract_tool_paths(name, effective_input, &command, &effect);
    let process_chain = if category == "shell" {
        command_process_chain(&command)
    } else {
        Vec::new()
    };
    let skill_name = name
        .eq_ignore_ascii_case("skill")
        .then(|| input.get("skill").and_then(Value::as_str))
        .flatten()
        .filter(|value| !value.is_empty())
        .map(ToString::to_string);
    let skill_args = name
        .eq_ignore_ascii_case("skill")
        .then(|| input.get("args"))
        .flatten()
        .map(|value| {
            value
                .as_str()
                .map(ToString::to_string)
                .unwrap_or_else(|| value.to_string())
        });
    ToolEvent {
        ts_ms,
        end_ts_ms: None,
        prompt_index,
        tool_name: name.to_string(),
        source_event_id: None,
        parent_event_id: None,
        model: None,
        attribution_skill: None,
        attribution_agent: None,
        skill_name,
        skill_args,
        category,
        command,
        workdir: (!workdir.is_empty()).then_some(workdir),
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
    let is_shell = [
        "bash",
        "exec",
        "exec_command",
        "shell_command",
        "run_shell_command",
        "shell",
    ]
    .contains(&lower.as_str());
    let default_access = if ["read", "notebookread", "read_file"].contains(&lower.as_str()) {
        "read"
    } else if ["edit", "notebookedit", "multiedit"].contains(&lower.as_str()) {
        "write"
    } else if ["write", "write_file"].contains(&lower.as_str()) {
        "create"
    } else if lower == "apply_patch" {
        "write"
    } else if is_shell {
        if effect == "read" { "read" } else { "write" }
    } else {
        return Vec::new();
    };
    let mut rows = Vec::<ToolPath>::new();
    if !is_shell {
        collect_path_fields(input, default_access, &mut rows);
    }

    let embedded_patch = embedded_json_string(command, "*** Begin Patch");
    let patch = input
        .get("patch")
        .or_else(|| input.get("input"))
        .or_else(|| input.get("text"))
        .and_then(Value::as_str)
        .filter(|value| {
            value.lines().any(|line| {
                let line = line.trim();
                line.starts_with("*** Add File: ")
                    || line.starts_with("*** Update File: ")
                    || line.starts_with("*** Delete File: ")
            })
        })
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
                            rows.retain(|row| !(row.path == source && row.access == "write"));
                            rows.push(ToolPath {
                                path: source.clone(),
                                access: "rename_from".to_string(),
                                previous_path: None,
                            });
                            rows.push(ToolPath {
                                path: path.clone(),
                                access: "rename".to_string(),
                                previous_path: Some(source),
                            });
                            continue;
                        }
                        rows.push(ToolPath {
                            path,
                            access: access.to_string(),
                            previous_path: None,
                        });
                    }
                }
            }
        }
    }

    let wrapper_rejected =
        lower == "bash" && (command.starts_with("\\\n") || command.starts_with("\\\r\n"));
    if is_shell && !has_patch && !wrapper_rejected {
        for (path, access, previous_path) in shell_file_actions(command, input) {
            rows.push(ToolPath {
                path,
                access,
                previous_path,
            });
        }
        if lower == "exec" {
            for nested in embedded_json_objects(command, "tools.exec_command(") {
                let nested_command = command_from_tool_input(&nested);
                for (path, access, previous_path) in shell_file_actions(&nested_command, &nested) {
                    rows.push(ToolPath {
                        path,
                        access,
                        previous_path,
                    });
                }
            }
        }
    }
    canonicalize_tool_paths(&mut rows);
    rows
}

fn canonicalize_tool_paths(rows: &mut Vec<ToolPath>) {
    let priority = |access: &str| match access {
        "rename_from" => 0,
        "rename" => 1,
        _ => 2,
    };
    rows.sort_by(|left, right| {
        (
            priority(&left.access),
            left.path.as_str(),
            left.access.as_str(),
            left.previous_path.as_deref().unwrap_or(""),
        )
            .cmp(&(
                priority(&right.access),
                right.path.as_str(),
                right.access.as_str(),
                right.previous_path.as_deref().unwrap_or(""),
            ))
    });
    rows.dedup_by(|left, right| {
        left.path == right.path
            && left.access == right.access
            && left.previous_path == right.previous_path
    });
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
        if let Some(value) = parse_json_or_js_object(&text[open..end]) {
            rows.push(value);
        }
        offset = end;
    }
    rows
}

fn parse_json_or_js_object(text: &str) -> Option<Value> {
    if let Ok(value) = serde_json::from_str(text) {
        return Some(value);
    }
    let body = text.strip_prefix('{')?.strip_suffix('}')?;
    let mut object = serde_json::Map::new();
    for field in top_level_fields(body) {
        let (name, value) = field.split_once(':')?;
        let name = name.trim().trim_matches(['"', '\'']);
        if name.is_empty()
            || !name
                .chars()
                .all(|ch| ch == '_' || ch == '-' || ch.is_ascii_alphanumeric())
        {
            return None;
        }
        object.insert(name.to_string(), serde_json::from_str(value.trim()).ok()?);
    }
    (!object.is_empty()).then_some(Value::Object(object))
}

fn top_level_fields(text: &str) -> Vec<&str> {
    let mut fields = Vec::new();
    let mut start = 0usize;
    let mut quoted = false;
    let mut escaped = false;
    let mut nested = 0usize;
    for (index, byte) in text.as_bytes().iter().copied().enumerate() {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
            }
            continue;
        }
        match byte {
            b'"' => quoted = true,
            b'{' | b'[' | b'(' => nested += 1,
            b'}' | b']' | b')' => nested = nested.saturating_sub(1),
            b',' if nested == 0 => {
                fields.push(&text[start..index]);
                start = index + 1;
            }
            _ => {}
        }
    }
    fields.push(&text[start..]);
    fields
}

fn shell_file_actions(command: &str, input: &Value) -> Vec<(String, String, Option<String>)> {
    let cwd = ["workdir", "cwd"]
        .iter()
        .find_map(|key| input.get(*key).and_then(Value::as_str))
        .map(PathBuf::from);
    let mut rows = Vec::new();
    for parts in shell_segments(command) {
        let Some(first) = parts.first() else {
            continue;
        };
        let name = process_name_from_part(first).unwrap_or_default();
        let operands = &parts[1..];
        let mut actions = shell_segment_actions(&name, operands);
        for (path, _, previous_path) in &mut actions {
            if let Some(relative) = path.strip_prefix("~/")
                && let Some(home) = user_home_dir()
            {
                *path = home.join(relative).to_string_lossy().into_owned();
            } else if !path.starts_with('$')
                && !Path::new(path).is_absolute()
                && let Some(base) = &cwd
            {
                *path = base.join(&*path).to_string_lossy().into_owned();
            }
            *path = clean_path_token(path);
            if let Some(previous) = previous_path {
                if let Some(relative) = previous.strip_prefix("~/")
                    && let Some(home) = user_home_dir()
                {
                    *previous = home.join(relative).to_string_lossy().into_owned();
                } else if !previous.starts_with('$')
                    && !Path::new(previous).is_absolute()
                    && let Some(base) = &cwd
                {
                    *previous = base.join(&*previous).to_string_lossy().into_owned();
                }
                *previous = clean_path_token(previous);
            }
        }
        rows.extend(actions.into_iter().filter(|(path, _, _)| !path.is_empty()));
    }
    rows
}

fn shell_segment_actions(name: &str, operands: &[String]) -> Vec<(String, String, Option<String>)> {
    let mut rows = Vec::new();
    let has_redirection = operands.iter().any(|value| is_redirection_token(value));
    if has_redirection && !matches!(name, "cp" | "mv") {
        return rows;
    }
    let operands = if has_redirection {
        strip_shell_redirections(operands)
    } else {
        operands.to_vec()
    };
    let values = shell_file_operands(name, &operands);
    let paths = |items: &[String]| {
        items
            .iter()
            .filter(|value| !value.is_empty())
            .cloned()
            .collect::<Vec<_>>()
    };
    match name {
        "git" if values.first().is_some_and(|value| value == "rm") => {
            rows.extend(shell_segment_actions("rm", &values[1..]));
        }
        "git" if values.first().is_some_and(|value| value == "mv") => {
            rows.extend(shell_segment_actions("mv", &values[1..]));
        }
        "cp" => {
            let paths = paths(&values);
            if paths.len() >= 2 {
                let target = paths[paths.len() - 1].clone();
                let sources = &paths[..paths.len() - 1];
                for source in sources {
                    rows.push((source.clone(), "read".into(), None));
                    let destination = if sources.len() == 1 {
                        target.clone()
                    } else {
                        Path::new(&target)
                            .join(
                                Path::new(source)
                                    .file_name()
                                    .unwrap_or_else(|| Path::new(source).as_os_str()),
                            )
                            .to_string_lossy()
                            .into_owned()
                    };
                    rows.push((destination, "create".into(), None));
                }
            }
        }
        "mv" => {
            let paths = paths(&values);
            if paths.len() >= 2 {
                let source = paths[paths.len() - 2].clone();
                let target = paths[paths.len() - 1].clone();
                rows.push((source.clone(), "rename_from".into(), None));
                rows.push((target, "rename".into(), Some(source)));
            }
        }
        "rm" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "delete".into(), None)),
        ),
        "touch" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "create".into(), None)),
        ),
        "cat" | "sed" | "head" | "tail" | "nl" | "less" | "more" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "read".into(), None)),
        ),
        _ => {}
    }
    rows
}

fn strip_shell_redirections(operands: &[String]) -> Vec<String> {
    let mut values = Vec::new();
    let mut index = 0;
    while index < operands.len() {
        let token = &operands[index];
        if is_redirection_token(token) {
            index += 1;
            if redirection_needs_operand(token) && index < operands.len() {
                index += 1;
            }
        } else {
            values.push(token.clone());
            index += 1;
        }
    }
    values
}

fn redirection_needs_operand(token: &str) -> bool {
    let operator = token.trim_start_matches(|ch: char| ch.is_ascii_digit());
    if operator.starts_with("&>") {
        return true;
    }
    if let Some(target) = operator
        .strip_prefix(">&")
        .or_else(|| operator.strip_prefix("<&"))
    {
        return target.is_empty();
    }
    true
}

fn shell_file_operands(name: &str, operands: &[String]) -> Vec<String> {
    let option_arity: &[&str] = match name {
        "head" => &["-n", "--lines", "-c", "--bytes"],
        "tail" => &[
            "-n",
            "--lines",
            "-c",
            "--bytes",
            "-s",
            "--sleep-interval",
            "--pid",
        ],
        "sed" => &["-e", "--expression", "-f", "--file"],
        "nl" => &[
            "-b",
            "--body-numbering",
            "-d",
            "--section-delimiter",
            "-f",
            "--footer-numbering",
            "-h",
            "--header-numbering",
            "-i",
            "--line-increment",
            "-l",
            "--join-blank-lines",
            "-n",
            "--number-format",
            "-s",
            "--number-separator",
            "-v",
            "--starting-line-number",
            "-w",
            "--number-width",
        ],
        _ => &[],
    };
    let mut values = Vec::new();
    let mut skip_next = false;
    let mut end_options = false;
    let mut explicit_sed_program = false;
    for token in operands {
        if skip_next {
            skip_next = false;
            continue;
        }
        if token == "--" {
            end_options = true;
            continue;
        }
        let option = token.split('=').next().unwrap_or(token);
        if !end_options && option_arity.contains(&option) {
            explicit_sed_program |=
                name == "sed" && ["-e", "--expression", "-f", "--file"].contains(&option);
            skip_next = !token.contains('=');
            continue;
        }
        if !end_options && token.starts_with('-') {
            continue;
        }
        values.push(token.clone());
    }
    if name == "sed" && !explicit_sed_program && !values.is_empty() {
        values.remove(0);
    }
    values
}

fn collect_path_fields(value: &Value, access: &str, out: &mut Vec<ToolPath>) {
    match value {
        Value::Object(object) => {
            for (key, value) in object {
                let key = key.to_ascii_lowercase();
                if matches!(
                    key.as_str(),
                    "path"
                        | "file_path"
                        | "filepath"
                        | "absolute_path"
                        | "target_file"
                        | "notebook_path"
                        | "old_path"
                        | "new_path"
                ) && let Some(path) = value.as_str()
                {
                    let path = clean_path_token(path);
                    if !path.is_empty() {
                        out.push(ToolPath {
                            path,
                            access: access.to_string(),
                            previous_path: None,
                        });
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
    if lowered.contains("process exited with code 0")
        || lowered.contains("script completed")
        || lowered.contains("command completed")
        || lowered.contains("\"is_error\":false")
    {
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
    if n.ends_with("exec_command") || n == "exec" || n == "bash" {
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
    let validator_script = ["python", "python3", "node", "bash", "sh"].contains(&cmd.as_str())
        && text.split_whitespace().any(|word| {
            let name = word
                .trim_matches(|ch: char| !ch.is_ascii_alphanumeric() && !"._-/".contains(ch))
                .rsplit('/')
                .next()
                .unwrap_or("");
            ["test", "check", "verify", "validate", "lint", "smoke"]
                .iter()
                .any(|marker| {
                    Path::new(name)
                        .file_stem()
                        .and_then(|value| value.to_str())
                        .unwrap_or(name)
                        .split(|ch: char| !ch.is_ascii_alphanumeric())
                        .any(|part| part == *marker)
                })
        });
    let validator_executable =
        ["test", "check", "verify", "validate", "lint"]
            .iter()
            .any(|marker| {
                cmd == *marker
                    || cmd.starts_with(&format!("{marker}-"))
                    || cmd.starts_with(&format!("{marker}_"))
            });
    if (["cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"].contains(&cmd.as_str())
        && any_word(&text, &["test", "check", "build", "clippy"]))
        || validator_script
        || validator_executable
    {
        "test"
    } else if cmd == "git" && any_word(&text, &["rm", "mv"]) {
        "write"
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

    // A backslash-newline is a POSIX shell line continuation once a command
    // reaches the shell. Wrapper-specific pre-launch rejection is handled by
    // the caller before this generic tokenizer.
    let continued = command.replace("\\\r\n", "").replace("\\\n", "");
    let command = strip_heredoc_bodies(&continued);
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
            let mut operator =
                if !current.is_empty() && current.chars().all(|value| value.is_ascii_digit()) {
                    std::mem::take(&mut current)
                } else {
                    flush_word(&mut tokens, &mut current);
                    String::new()
                };
            operator.push(ch);
            while chars.peek() == Some(&ch) && operator.len() < 3 {
                operator.push(chars.next().expect("peeked redirection"));
            }
            if chars.peek() == Some(&'&') {
                operator.push(chars.next().expect("peeked fd duplication"));
                while chars.peek().is_some_and(|value| value.is_ascii_digit()) {
                    operator.push(chars.next().expect("peeked fd"));
                }
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
    let operator = token.trim_start_matches(|ch: char| ch.is_ascii_digit());
    operator.starts_with('>') || operator.starts_with('<') || operator.starts_with("&>")
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

fn codex_native_root_id(obj: &Value) -> Option<&str> {
    [
        "/payload/session_id",
        "/payload/parent_thread_id",
        "/payload/thread_id",
        "/payload/id",
    ]
    .into_iter()
    .find_map(|pointer| {
        obj.pointer(pointer)
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
    })
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

/// Return the source-native RFC3339 timestamp of a transcript record.
/// Consumers that correlate external evidence should use this timestamp rather
/// than the time at which a copied/streamed record reached their process.
pub fn event_timestamp_ms(value: &Value) -> Option<i64> {
    ts_ms_from_event(value)
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

    #[test]
    fn repository_specific_validator_scripts_are_test_effects() {
        assert_eq!(
            command_effect("python scripts/check_progress.py --repo fixture"),
            "test"
        );
        assert_eq!(command_effect("bash tests/smoke_agent.sh"), "test");
        assert_eq!(command_effect("./verify-package"), "test");
        assert_eq!(
            command_effect("python scripts/generate_report.py"),
            "process"
        );
        assert_eq!(command_effect("python latest_results.py"), "process");
    }

    #[test]
    fn git_rm_is_a_confirmed_workspace_mutation_in_compound_shell() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"cwd":"/repo"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:01Z","type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"git rm -f bpf/process bpf/test_taint\\nrm -f bpf/process_new\"}"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:03Z","type":"response_item","payload":{"type":"function_call_output","call_id":"c1","output":"Process exited with code 0"}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");
        let event = &session.events.tools[0];
        assert_eq!(event.effect, "write");
        assert_eq!(event.status, "ok");
        assert_eq!(
            event
                .paths
                .iter()
                .map(|row| (row.path.as_str(), row.access.as_str()))
                .collect::<Vec<_>>(),
            vec![
                ("bpf/process", "delete"),
                ("bpf/process_new", "delete"),
                ("bpf/test_taint", "delete"),
            ]
        );
    }
    use serde_json::json;
    use std::time::UNIX_EPOCH;

    #[test]
    fn claude_event_workdir_overrides_session_cwd_for_relative_paths() {
        // Frozen question spec: "Event workdir overrides session cwd." A record
        // carrying a new cwd must move relative path resolution; the
        // session-initial cwd applies only when the record has none, and an
        // explicit input workdir beats both.
        let content = concat!(
            r#"{"type":"user","cwd":"/repo","sessionId":"s","message":{"content":"go"}}"#,
            "\n",
            r#"{"type":"assistant","cwd":"/repo","timestamp":"2026-01-01T00:00:00Z","message":{"content":[{"type":"tool_use","id":"t0","name":"Bash","input":{"command":"cat README.md"}}]}}"#,
            "\n",
            r#"{"type":"assistant","cwd":"/repo/collector","timestamp":"2026-01-01T00:00:01Z","message":{"content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"cat -n collector/src/view/mod.rs"}}]}}"#,
            "\n",
            r#"{"type":"assistant","cwd":"/repo/collector","timestamp":"2026-01-01T00:00:02Z","message":{"content":[{"type":"tool_use","id":"t2","name":"Bash","input":{"command":"cat src/lib.rs","workdir":"/repo"}}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CLAUDE,
            Path::new("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");
        let tools = &session.events.tools;
        assert_eq!(tools.len(), 3);
        // Session cwd used while records keep the initial cwd.
        assert_eq!(tools[0].workdir.as_deref(), Some("/repo"));
        assert_eq!(tools[0].paths[0].path, "README.md");
        // Event workdir overrides the session-initial cwd; relative operands
        // stay relative here and are joined against this workdir downstream
        // (agentvis repository::resolve_path).
        assert_eq!(tools[1].workdir.as_deref(), Some("/repo/collector"));
        assert_eq!(tools[1].paths[0].path, "collector/src/view/mod.rs");
        // Explicit input workdir overrides the event cwd.
        assert_eq!(tools[2].workdir.as_deref(), Some("/repo"));
        assert_eq!(tools[2].paths[0].path, "/repo/src/lib.rs");
    }

    #[test]
    fn codex_turn_context_event_workdir_overrides_session_cwd() {
        let content = concat!(
            r#"{"type":"session_meta","payload":{"id":"s","cwd":"/repo"}}"#,
            "\n",
            r#"{"type":"turn_context","payload":{"cwd":"/repo/collector"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:01Z","type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"cat -n collector/src/view/mod.rs\"}"}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");
        let event = &session.events.tools[0];
        assert_eq!(event.workdir.as_deref(), Some("/repo/collector"));
        assert_eq!(event.paths[0].path, "collector/src/view/mod.rs");
    }

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
    fn claude_skill_source_fields_preserve_exact_long_arguments() {
        let long_args = "context ".repeat(80);
        let content = serde_json::json!({
            "type": "assistant",
            "uuid": "event-1",
            "parentUuid": "event-0",
            "sessionId": "root-session",
            "isSidechain": true,
            "agentId": "worker-a",
            "attributionSkill": "research-experiment-design",
            "attributionAgent": "researcher",
            "message": {
                "model": "claude-opus",
                "content": [{
                    "type": "tool_use",
                    "id": "call-1",
                    "name": "Skill",
                    "input": {
                        "skill": "research-experiment-design",
                        "args": long_args
                    }
                }],
                "usage": {"input_tokens": 1, "output_tokens": 1}
            }
        })
        .to_string();
        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/subagent.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");
        let tool = &session.events.tools[0];

        assert_eq!(session.session_id, "root-session");
        assert_eq!(session.source_role.as_deref(), Some("subagent"));
        assert_eq!(session.source_agent_id.as_deref(), Some("worker-a"));
        assert_eq!(tool.source_event_id.as_deref(), Some("event-1"));
        assert_eq!(tool.parent_event_id.as_deref(), Some("event-0"));
        assert_eq!(tool.model.as_deref(), Some("claude-opus"));
        assert_eq!(
            tool.attribution_skill.as_deref(),
            Some("research-experiment-design")
        );
        assert_eq!(tool.attribution_agent.as_deref(), Some("researcher"));
        assert_eq!(
            tool.skill_name.as_deref(),
            Some("research-experiment-design")
        );
        assert_eq!(tool.skill_args.as_deref(), Some(long_args.as_str()));
        assert!(tool.command.len() < long_args.len());
    }

    #[test]
    fn claude_source_files_with_one_native_id_share_the_root_unit() {
        let root = concat!(
            r#"{"type":"user","sessionId":"shared","isSidechain":false,"message":{"content":"root"}}"#,
            "\n",
            r#"{"type":"assistant","sessionId":"shared","isSidechain":false,"message":{"model":"claude","content":[{"type":"tool_use","id":"r1","name":"Read","input":{"file_path":"src/lib.rs"}}]}}"#,
        );
        let child = r#"{"type":"assistant","sessionId":"shared","isSidechain":true,"agentId":"child","message":{"model":"claude","content":[{"type":"tool_use","id":"c1","name":"Read","input":{"file_path":"src/main.rs"}}]}}"#;

        let root = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/root.jsonl"),
            UNIX_EPOCH,
            root,
        )
        .expect("root");
        let child = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/child.jsonl"),
            UNIX_EPOCH,
            child,
        )
        .expect("child");

        assert_eq!(root.session_id, child.session_id);
        assert_eq!(root.source_role.as_deref(), Some("root"));
        assert_eq!(child.source_role.as_deref(), Some("subagent"));
        assert_eq!(child.source_agent_id.as_deref(), Some("child"));
    }

    #[test]
    fn repeated_prompt_text_after_another_turn_is_a_new_boundary() {
        let content = concat!(
            r#"{"type":"user","sessionId":"root","message":{"content":"same"}}"#,
            "\n",
            r#"{"type":"assistant","sessionId":"root","message":{"model":"claude","content":[{"type":"tool_use","id":"a","name":"Read","input":{"file_path":"a.rs"}}]}}"#,
            "\n",
            r#"{"type":"user","sessionId":"root","message":{"content":"different"}}"#,
            "\n",
            r#"{"type":"assistant","sessionId":"root","message":{"model":"claude","content":[{"type":"tool_use","id":"b","name":"Read","input":{"file_path":"b.rs"}}]}}"#,
            "\n",
            r#"{"type":"user","sessionId":"root","message":{"content":"same"}}"#,
            "\n",
            r#"{"type":"assistant","sessionId":"root","message":{"model":"claude","content":[{"type":"tool_use","id":"c","name":"Read","input":{"file_path":"c.rs"}}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/repeated-prompt.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");

        assert_eq!(session.events.prompts.len(), 3);
        assert_eq!(
            session
                .events
                .tools
                .iter()
                .map(|tool| tool.prompt_index)
                .collect::<Vec<_>>(),
            vec![1, 2, 3]
        );
    }

    #[test]
    fn claude_meta_skill_injection_is_not_a_human_prompt_boundary() {
        let content = concat!(
            r#"{"type":"assistant","sessionId":"root","message":{"model":"claude","content":[{"type":"tool_use","id":"skill","name":"Skill","input":{"skill":"example"}}]}}"#,
            "\n",
            r#"{"type":"user","sessionId":"root","isMeta":true,"sourceToolUseID":"skill","message":{"content":[{"type":"text","text":"injected skill body"}]}}"#,
            "\n",
            r#"{"type":"assistant","sessionId":"root","message":{"model":"claude","content":[{"type":"tool_use","id":"read","name":"Read","input":{"file_path":"a.rs"}}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/meta-skill.jsonl"),
            UNIX_EPOCH,
            content,
        )
        .expect("session");

        assert!(session.events.prompts.is_empty());
        assert_eq!(
            session.events.tools[0].prompt_index,
            session.events.tools[1].prompt_index
        );
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
    fn codex_session_meta_uses_native_root_id_for_root_and_subagent() {
        let root = concat!(
            r#"{"type":"session_meta","payload":{"id":"root-id","thread_source":"user"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"r","arguments":"{\"cmd\":\"pwd\"}"}}"#,
        );
        let child = concat!(
            r#"{"type":"session_meta","payload":{"id":"child-id","session_id":"root-id","thread_source":"subagent","agent_path":"/root/check"}}"#,
            "\n",
            r#"{"type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c","arguments":"{\"cmd\":\"pwd\"}"}}"#,
        );
        for (path, content, role, agent) in [
            ("/tmp/root.jsonl", root, "user", None),
            ("/tmp/child.jsonl", child, "subagent", Some("/root/check")),
        ] {
            let session =
                parse_session_content(AGENT_CODEX, &PathBuf::from(path), UNIX_EPOCH, content)
                    .expect("session");
            assert_eq!(session.session_id, "root-id");
            assert_eq!(session.source_role.as_deref(), Some(role));
            assert_eq!(session.source_agent_id.as_deref(), agent);
        }
    }

    #[test]
    fn codex_native_root_matches_shared_fixture() {
        let path = std::env::var("RQ7_SESSION_FIXTURES").ok();
        let text = path.as_deref().map_or_else(
            || include_str!("../tests/fixtures/native-root-identity.json").to_string(),
            |path| std::fs::read_to_string(path).expect("read shared fixture"),
        );
        let fixtures: Vec<Value> = serde_json::from_str(&text).expect("parse shared fixture");
        for fixture in fixtures {
            let name = fixture["name"].as_str().expect("fixture name");
            let obj = json!({"payload": fixture["payload"]});
            assert_eq!(
                codex_native_root_id(&obj),
                fixture["expected"].as_str(),
                "fixture {name}"
            );
        }
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
                previous_path: None,
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
        for wrapper in [
            r#"const r = await tools.exec_command({"cmd":"cat src/lib.rs && sed -i 's/a/b/' src/main.rs","workdir":"/repo"});"#,
            r#"const r = await tools.exec_command({cmd:"cat src/lib.rs && sed -i 's/a/b/' src/main.rs",workdir:"/repo"});"#,
        ] {
            let event = tool_event_from_input(
                Some("/repo"),
                Some(1),
                0,
                "exec",
                &json!({"text": wrapper}),
                None,
            );
            assert_eq!(
                event
                    .paths
                    .iter()
                    .map(|path| (path.path.as_str(), path.access.as_str()))
                    .collect::<Vec<_>>(),
                vec![("/repo/src/lib.rs", "read"), ("/repo/src/main.rs", "read")]
            );
            assert_eq!(
                event.command,
                "cat src/lib.rs && sed -i 's/a/b/' src/main.rs"
            );
            assert_eq!(event.workdir.as_deref(), Some("/repo"));
        }
    }

    #[test]
    fn ambiguous_inspection_commands_do_not_claim_exact_file_reads() {
        for command in [
            "git diff -- skills/example/SKILL.md",
            "stat -c '%n' AGENTS.md",
            "cmp CLAUDE.md backup/CLAUDE.md",
            "rg TODO src/lib.rs",
            "grep -n TODO src/main.rs",
            "find docs -name '*.md'",
        ] {
            let event = tool_event_from_input(
                Some("/repo"),
                Some(1),
                0,
                "exec_command",
                &json!({"cmd": command}),
                None,
            );
            assert!(
                event.paths.is_empty(),
                "unexpected exact paths for {command}"
            );
        }
    }

    #[test]
    fn strict_shell_file_operands_exclude_options_programs_and_redirections() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec_command",
            &json!({"cmd": "cat README; head -n 20 src/a.rs; sed -e 's/a/b/' src/b.rs; cat src/c.rs > out.txt; sudo cat LICENSE; bash -c 'cat Makefile'; cd src && cat local.rs"}),
            None,
        );
        assert_eq!(
            event
                .paths
                .iter()
                .map(|path| (path.path.as_str(), path.access.as_str()))
                .collect::<Vec<_>>(),
            vec![
                ("README", "read"),
                ("local.rs", "read"),
                ("src/a.rs", "read"),
                ("src/b.rs", "read")
            ]
        );
    }

    #[test]
    fn strict_action_grammar_matches_shared_fixture() {
        let path = std::env::var("RQ7_ACTION_FIXTURES").ok();
        let text = path.as_deref().map_or_else(
            || include_str!("../tests/fixtures/strict-action-grammar.json").to_string(),
            |path| std::fs::read_to_string(path).expect("read shared fixture"),
        );
        let fixtures: Vec<Value> = serde_json::from_str(&text).expect("parse shared fixture");
        for fixture in fixtures {
            let name = fixture["name"].as_str().expect("fixture name");
            let tool = fixture["tool"].as_str().expect("fixture tool");
            let args = &fixture["args"];
            let expected: Vec<ToolPath> = serde_json::from_value(
                fixture
                    .get("production_actions")
                    .unwrap_or(&fixture["actions"])
                    .clone(),
            )
            .expect("fixture actions");
            let event = tool_event_from_input(Some("/repo"), Some(1), 0, tool, args, None);
            assert_eq!(event.paths, expected, "fixture {name}");
        }
    }

    #[test]
    fn codex_custom_apply_patch_pairs_result_and_extracts_workspace_path() {
        let input = r#"const patch = "*** Begin Patch\n*** Update File: /workspace/testing/logging/test_fixture.py\n@@\n-old\n+new\n*** End Patch"; tools.apply_patch(patch)"#;
        assert!(
            embedded_json_string(input, "*** Begin Patch").is_some_and(|patch| patch
                .contains("*** Update File: /workspace/testing/logging/test_fixture.py"))
        );
        let content = format!(
            "{}\n{}\n{}\n",
            serde_json::json!({
                "timestamp": "2026-07-20T10:10:15Z",
                "type": "session_meta",
                "payload": {"cwd": "/workspace"}
            }),
            serde_json::json!({
                "timestamp": "2026-07-20T10:10:52Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "patch-call",
                    "input": input
                }
            }),
            serde_json::json!({
                "timestamp": "2026-07-20T10:10:53Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call_output",
                    "call_id": "patch-call",
                    "output": [{"type": "input_text", "text": "Script completed\nOutput:\n{}"}]
                }
            })
        );
        let session = parse_session_content(
            AGENT_CODEX,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");
        let tool = &session.events.tools[0];
        assert_eq!(tool.status, "ok");
        assert_eq!(tool.end_ts_ms, Some(1_784_542_253_000));
        assert_eq!(
            tool.paths,
            vec![ToolPath {
                path: "/workspace/testing/logging/test_fixture.py".into(),
                access: "write".into(),
                previous_path: None,
            }]
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
        assert_eq!(write.paths[0].access, "create");

        let grep = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "Grep",
            &json!({"path": "src", "pattern": "needle"}),
            None,
        );
        assert!(grep.paths.is_empty());

        let absolute = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "Read",
            &json!({"absolute_path": "/repo/README", "target_file": "/repo/Makefile"}),
            None,
        );
        assert_eq!(absolute.paths.len(), 2);
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
            path: "src/b.rs".into(),
            access: "rename".into(),
            previous_path: Some("src/a.rs".into()),
        }));
        assert!(event.paths.contains(&ToolPath {
            path: "src/c.rs".into(),
            access: "write".into(),
            previous_path: None,
        }));

        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "apply_patch",
            &json!({"patch": "*** Begin Patch\n*** Update File: a.rs\n*** Move to: x.rs\n*** Update File: b.rs\n*** Move to: y.rs\n*** End Patch"}),
            None,
        );
        assert_eq!(
            event
                .paths
                .iter()
                .map(|row| (row.path.as_str(), row.previous_path.as_deref()))
                .collect::<Vec<_>>(),
            vec![
                ("a.rs", None),
                ("b.rs", None),
                ("x.rs", Some("a.rs")),
                ("y.rs", Some("b.rs"))
            ]
        );
    }

    #[test]
    fn tool_outputs_mark_failed_file_actions() {
        let content = concat!(
            r#"{"type":"turn_context","payload":{"cwd":"/repo"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:01Z","type":"response_item","payload":{"type":"function_call","name":"exec_command","call_id":"c1","arguments":"{\"cmd\":\"rm src/lib.rs\"}"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:03Z","type":"response_item","payload":{"type":"function_call_output","call_id":"c1","output":"Process exited with code 1"}}"#,
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
        assert_eq!(session.events.tools[0].ts_ms, Some(1_767_225_601_000));
        assert_eq!(session.events.tools[0].end_ts_ms, Some(1_767_225_603_000));

        let claude = concat!(
            r#"{"timestamp":"2026-01-01T00:00:05Z","type":"assistant","message":{"content":[{"type":"tool_use","id":"t0","name":"Read","input":{"file_path":"src/main.rs"}},{"type":"tool_use","id":"t1","name":"Edit","input":{"file_path":"src/lib.rs"}}]}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:08Z","type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t0","is_error":false,"content":"ok"},{"type":"tool_result","tool_use_id":"t1","is_error":true,"content":"failed"}]}}"#,
        );
        let gemini = r#"{"messages":[{"type":"gemini","timestamp":"2026-01-01T00:00:00Z","toolCalls":[{"id":"t1","name":"write_file","args":{"file_path":"src/lib.rs"},"status":"error"}]}]}"#;
        for (agent, content, expected) in [
            (AGENT_CLAUDE, claude, &["ok", "fail"][..]),
            (AGENT_GEMINI, gemini, &["fail"][..]),
        ] {
            let session =
                parse_session_content(agent, Path::new("/tmp/session.jsonl"), UNIX_EPOCH, content)
                    .unwrap();
            let statuses = session
                .events
                .tools
                .iter()
                .map(|row| row.status.as_str())
                .collect::<Vec<_>>();
            assert_eq!(statuses, expected);
            if agent == AGENT_CLAUDE {
                assert_eq!(session.events.tools[0].end_ts_ms, Some(1_767_225_608_000));
                assert_eq!(session.events.tools[1].end_ts_ms, Some(1_767_225_608_000));
            }
        }

        let codex_array_output = concat!(
            r#"{"timestamp":"2026-01-01T00:00:10Z","type":"response_item","payload":{"type":"custom_tool_call","name":"exec","call_id":"c2","input":"{}"}}"#,
            "\n",
            r#"{"timestamp":"2026-01-01T00:00:11Z","type":"response_item","payload":{"type":"custom_tool_call_output","call_id":"c2","output":[{"type":"input_text","text":"Script completed\nOutput:\n"}]}}"#,
        );
        let session = parse_session_content(
            AGENT_CODEX,
            Path::new("/tmp/session.jsonl"),
            UNIX_EPOCH,
            codex_array_output,
        )
        .unwrap();
        assert_eq!(session.events.tools[0].status, "ok");
        assert_eq!(session.events.tools[0].category, "shell");
        assert_eq!(session.events.tools[0].end_ts_ms, Some(1_767_225_611_000));
    }
}
