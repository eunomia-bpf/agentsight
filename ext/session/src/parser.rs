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
    AgentSession, LlmResponse, PlanStep, SessionCandidate, SessionDirStat, SessionEvents,
    TokenUsage, ToolEvent, ToolPath, UserPrompt,
};
use crate::{AGENT_CLAUDE, AGENT_CODEX, AGENT_CURSOR, AGENT_GEMINI};

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
        (AGENT_CURSOR, home.join(".cursor/projects")),
    ];
    let mut out = Vec::new();
    for (agent, dir) in roots {
        walk_agent_files(agent, &dir, &mut |path, meta| {
            out.push(SessionCandidate {
                agent,
                path: path.to_path_buf(),
                updated: candidate_updated(agent, path, meta),
            });
        });
    }
    dedupe_cursor_candidates(&mut out);
    out
}

pub fn discover_session_files_in_dir(agent: &'static str, dir: &Path) -> Vec<SessionCandidate> {
    let mut out = Vec::new();
    walk_agent_files(agent, dir, &mut |path, meta| {
        out.push(SessionCandidate {
            agent,
            path: path.to_path_buf(),
            updated: candidate_updated(agent, path, meta),
        });
    });
    dedupe_cursor_candidates(&mut out);
    out
}

fn candidate_updated(agent: &str, path: &Path, meta: &fs::Metadata) -> SystemTime {
    let updated = meta.modified().unwrap_or(UNIX_EPOCH);
    if agent == AGENT_CURSOR {
        cursor_candidate_updated(path, updated)
    } else {
        updated
    }
}

fn cursor_candidate_updated(path: &Path, parent_updated: SystemTime) -> SystemTime {
    let mut updated = parent_updated;
    let Some(subagents) = path.parent().map(|dir| dir.join("subagents")) else {
        return updated;
    };
    let Ok(entries) = fs::read_dir(subagents) else {
        return updated;
    };
    for entry in entries.flatten() {
        if entry.path().extension().and_then(|ext| ext.to_str()) == Some("jsonl")
            && let Ok(meta) = entry.metadata()
        {
            updated = updated.max(meta.modified().unwrap_or(UNIX_EPOCH));
        }
    }
    updated
}

fn dedupe_cursor_candidates(out: &mut Vec<SessionCandidate>) {
    let mut best: BTreeMap<String, (bool, SystemTime, usize)> = BTreeMap::new();
    let mut drop = vec![false; out.len()];
    for (idx, candidate) in out.iter().enumerate() {
        if candidate.agent != AGENT_CURSOR {
            continue;
        }
        let Some(stem) = candidate.path.file_stem().and_then(|stem| stem.to_str()) else {
            continue;
        };
        let rank = (
            !cursor_is_empty_window(&candidate.path),
            candidate.updated,
            idx,
        );
        match best.get_mut(stem) {
            None => {
                best.insert(stem.to_string(), rank);
            }
            Some(entry) => {
                if (rank.0, rank.1) > (entry.0, entry.1) {
                    drop[entry.2] = true;
                    *entry = rank;
                } else {
                    drop[idx] = true;
                }
            }
        }
    }
    let mut drop = drop.into_iter();
    out.retain(|_| !drop.next().unwrap_or_default());
}

fn cursor_is_empty_window(path: &Path) -> bool {
    let mut previous = None;
    for component in path.components() {
        let name = component.as_os_str();
        if name == "agent-transcripts" {
            return previous.is_some_and(|project| project == "empty-window");
        }
        previous = Some(name);
    }
    false
}

/// Count sessions and bytes per agent directory.
pub fn count_session_dirs() -> Vec<SessionDirStat> {
    user_home_dir()
        .as_deref()
        .map(count_session_dirs_in_home)
        .unwrap_or_default()
}

/// Count sessions and bytes per agent directory under a specific home directory.
pub fn count_session_dirs_in_home(home: &Path) -> Vec<SessionDirStat> {
    [
        (AGENT_CLAUDE, home.join(".claude/projects")),
        (AGENT_CODEX, home.join(".codex/sessions")),
        (AGENT_GEMINI, home.join(".gemini/tmp")),
        (AGENT_CURSOR, home.join(".cursor/projects")),
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
    let cursor_children = if candidate.agent == AGENT_CURSOR {
        read_cursor_subagents(&candidate.path)
    } else {
        Vec::new()
    };
    parse_session_impl(
        candidate.agent,
        &candidate.path,
        candidate.updated,
        &content,
        &cursor_children,
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
    parse_session_impl(agent, path, updated, content, &[])
}

fn parse_session_impl(
    agent: &str,
    path: &Path,
    updated: SystemTime,
    content: &str,
    cursor_children: &[(PathBuf, String)],
) -> Option<AgentSession> {
    if agent == AGENT_GEMINI {
        parse_gemini_json(path, updated, content)
    } else if agent == AGENT_CURSOR {
        parse_cursor_jsonl(path, updated, content, cursor_children)
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
    if !is_absolute_path_text(trimmed) || !is_agent_session_file(path) {
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
    let value = normalize_path_text(&path.to_string_lossy());
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
    } else if value.contains("/.cursor/") && is_cursor_transcript(path) {
        Some(AGENT_CURSOR)
    } else {
        None
    }
}

fn is_cursor_transcript(path: &Path) -> bool {
    path.extension().and_then(|ext| ext.to_str()) == Some("jsonl")
        && normalize_path_text(&path.to_string_lossy()).contains("/agent-transcripts/")
}

fn is_cursor_parent_transcript(path: &Path) -> bool {
    is_cursor_transcript(path)
        && path.file_stem().is_some_and(|stem| {
            path.parent()
                .and_then(|dir| dir.file_name())
                .is_some_and(|dir| dir == stem)
        })
}

fn loose_agent_source_for_path(path: &Path) -> Option<&'static str> {
    let value = normalize_path_text(&path.to_string_lossy());
    if value.contains("/codex/") && value.contains("sessions") {
        Some(AGENT_CODEX)
    } else if value.contains("/claude/") && value.contains("projects") {
        Some(AGENT_CLAUDE)
    } else if value.contains("/cursor/") && value.contains("agent-transcripts") {
        Some(AGENT_CURSOR)
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
        AGENT_CURSOR => {
            Some(home.join(".cursor/projects/test/agent-transcripts/session/session.jsonl"))
        }
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

// ---------------------------------------------------------------------------
// Internal parsing implementation
// ---------------------------------------------------------------------------

#[derive(Default)]
struct SemanticTaskStack {
    root: Option<String>,
    active_plan: Option<String>,
    plan: Vec<PlanStep>,
}

impl SemanticTaskStack {
    fn observe_user(&mut self, text: &str) {
        let label = semantic_task_label(text);
        if self.root.is_some() && is_continuation_prompt(&label) {
            return;
        }
        self.root = Some(label);
        self.active_plan = None;
        self.plan.clear();
    }

    fn observe_plan(&mut self, input: &Value) {
        let Some(items) = input
            .get("plan")
            .or_else(|| input.get("todos"))
            .and_then(Value::as_array)
        else {
            return;
        };
        self.plan = items
            .iter()
            .filter_map(|item| {
                let step = item
                    .get("step")
                    .or_else(|| item.get("content"))
                    .and_then(Value::as_str)
                    .map(semantic_task_label)?;
                let status = item
                    .get("status")
                    .and_then(Value::as_str)
                    .unwrap_or("pending")
                    .to_string();
                Some(PlanStep { step, status })
            })
            .collect::<Vec<_>>();
        let active = self
            .plan
            .iter()
            .filter(|item| item.status == "in_progress")
            .map(|item| item.step.clone())
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

fn is_plan_tool(name: &str) -> bool {
    matches!(
        name.to_ascii_lowercase().as_str(),
        "update_plan" | "todowrite" | "todo_write"
    )
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
    let mut active_skill: Option<String> = None;
    let mut claude_prompt_id: Option<String> = None;
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
                let response_skill = active_skill.clone().unwrap_or_default();
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
                        let input = item.get("input").unwrap_or(&Value::Null);
                        let invoked_skill = exact_claude_skill_invocation(name, input);
                        if let Some(skill) = invoked_skill.as_ref() {
                            active_skill = Some(skill.clone());
                        }
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
                            input,
                            call_id.clone(),
                            task_stack.path_for_tool(name, input),
                        );
                        let mut event = event;
                        event.invoked_skill = invoked_skill.unwrap_or_default();
                        event.skill = active_skill.clone().unwrap_or_default();
                        if is_plan_tool(name) {
                            task_stack.observe_plan(input);
                        }
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
                        source_id: claude_source_completion_id(&obj),
                        text_hash: short_hash(&(text.clone() + &usage.to_string()), 12),
                        text: bounded_detail_text(&text),
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
                        skill: response_skill,
                        task_path: task_stack.path(),
                    });
                }
            }
            (AGENT_CLAUDE, "queue-operation") if acc.prompt_preview.is_none() => {
                if obj.get("operation").and_then(Value::as_str) == Some("enqueue")
                    && let Some(text) = obj.get("content").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(truncate_clean(&text, 180));
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CLAUDE, "last-prompt") if acc.prompt_preview.is_none() => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(truncate_clean(&text, 180));
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            (AGENT_CLAUDE, "user") => {
                let content = obj.pointer("/message/content").unwrap_or(&Value::Null);
                if claude_is_tool_result(content) || is_claude_tool_result(&obj) {
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
                        }
                    }
                } else if let Some(text) = local_message_preview(content)
                    && claude_user_starts_prompt(&obj, content, &text, claude_prompt_id.as_deref())
                {
                    if acc.prompt_preview.is_none() {
                        acc.prompt_preview = Some(truncate_clean(&text, 180));
                    }
                    task_stack.observe_user(&text);
                    active_skill = None;
                    claude_prompt_id = obj
                        .get("promptId")
                        .and_then(Value::as_str)
                        .filter(|value| !value.is_empty())
                        .map(str::to_string);
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
                        acc.prompt_preview = Some(truncate_clean(&text, 180));
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
                            source_id: String::new(),
                            text_hash: short_hash(&text, 12),
                            text: bounded_detail_text(&text),
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
                            skill: String::new(),
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
                if is_plan_tool(&name) {
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
                if is_plan_tool(name) {
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
                        acc.prompt_preview = Some(truncate_clean(&text, 180));
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
                        source_id: String::new(),
                        text_hash: short_hash(&text, 12),
                        text: bounded_detail_text(&text),
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
                        skill: String::new(),
                        task_path: task_stack.path(),
                    });
                }
            }
            (AGENT_CODEX, "message" | "input" | "user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(truncate_clean(&text, 180));
                    task_stack.observe_user(&text);
                    current_prompt_index =
                        events.upsert_prompt(ts_ms_from_event(&obj), &text, task_stack.path());
                }
            }
            _ if acc.prompt_preview.is_none() && typ.contains("user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(truncate_clean(&text, 180));
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
    events.plan = task_stack.plan;
    deduplicate_llm_responses(&mut events);
    acc.finish_with_events(events)
}

fn deduplicate_llm_responses(events: &mut SessionEvents) {
    let mut unique: Vec<LlmResponse> = Vec::with_capacity(events.llm_responses.len());
    let mut by_source_id = BTreeMap::<(usize, String), usize>::new();
    for response in events.llm_responses.drain(..) {
        let source_key = (!response.source_id.is_empty())
            .then(|| (response.prompt_index, response.source_id.clone()));
        let duplicate_index = source_key
            .as_ref()
            .and_then(|key| by_source_id.get(key).copied())
            .or_else(|| {
                unique.len().checked_sub(1).filter(|index| {
                    let previous = &unique[*index];
                    response.source_id.is_empty()
                        && previous.source_id.is_empty()
                        && previous.prompt_index == response.prompt_index
                        && previous.text_hash == response.text_hash
                        && previous
                            .ts_ms
                            .zip(response.ts_ms)
                            .is_some_and(|(left, right)| left.abs_diff(right) <= 1_000)
                })
            });
        if let Some(index) = duplicate_index {
            merge_llm_response(&mut unique[index], response);
            continue;
        }
        let index = unique.len();
        if let Some(key) = source_key {
            by_source_id.insert(key, index);
        }
        unique.push(response);
    }
    events.llm_responses = unique;
}

fn merge_llm_response(previous: &mut LlmResponse, response: LlmResponse) {
    previous.input_tokens = previous.input_tokens.max(response.input_tokens);
    previous.output_tokens = previous.output_tokens.max(response.output_tokens);
    previous.cache_tokens = previous.cache_tokens.max(response.cache_tokens);
    previous.total_tokens = previous.total_tokens.max(response.total_tokens);
    if response_phase_priority(&response.response_phase)
        > response_phase_priority(&previous.response_phase)
    {
        previous.response_phase = response.response_phase;
    }
    if previous.preview.starts_with("tool: ") && !response.preview.starts_with("tool: ") {
        previous.preview = response.preview;
        previous.text_hash = response.text_hash;
        previous.text = response.text;
    } else if previous.text.is_empty() && !response.text.is_empty() {
        previous.text = response.text;
    }
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
                    acc.prompt_preview = Some(truncate_clean(&text, 180));
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
                        let mut event = tool_event_from_input(
                            acc.cwd.as_deref(),
                            ts_ms,
                            current_prompt_index,
                            name,
                            call,
                            call.get("id").and_then(Value::as_str).map(str::to_string),
                            task_stack.path_for_tool(name, call),
                        );
                        if is_plan_tool(name) {
                            let plan_input = call
                                .get("args")
                                .or_else(|| call.get("arguments"))
                                .map(parse_tool_args)
                                .unwrap_or_else(|| call.clone());
                            task_stack.observe_plan(&plan_input);
                        }
                        if let Some(status) = call.get("status").and_then(Value::as_str) {
                            let lowered = status.to_ascii_lowercase();
                            event.status = if matches!(
                                lowered.as_str(),
                                "error" | "failed" | "fail" | "cancelled" | "canceled"
                            ) {
                                "fail".to_string()
                            } else if matches!(lowered.as_str(), "success" | "ok" | "completed") {
                                "ok".to_string()
                            } else {
                                status.to_string()
                            };
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
                        source_id: String::new(),
                        text_hash: short_hash(&(text.clone() + &tokens.to_string()), 12),
                        text: bounded_detail_text(&text),
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
                        skill: String::new(),
                        task_path: task_stack.path(),
                    });
                }
            }
            _ => {}
        }
    }
    events.plan = task_stack.plan;
    acc.finish_with_events(events)
}

fn read_cursor_subagents(path: &Path) -> Vec<(PathBuf, String)> {
    let Some(dir) = path.parent().map(|parent| parent.join("subagents")) else {
        return Vec::new();
    };
    let Ok(entries) = fs::read_dir(&dir) else {
        return Vec::new();
    };
    let mut out: Vec<(PathBuf, String)> = entries
        .flatten()
        .map(|entry| entry.path())
        .filter(|child| child.extension().and_then(|ext| ext.to_str()) == Some("jsonl"))
        .filter_map(|child| {
            let content = fs::read_to_string(&child).ok()?;
            Some((child, content))
        })
        .collect();
    // Directory order is arbitrary; keep parses deterministic across runs.
    out.sort_by(|left, right| left.0.cmp(&right.0));
    out
}

fn parse_cursor_jsonl(
    path: &Path,
    updated: SystemTime,
    content: &str,
    children: &[(PathBuf, String)],
) -> Option<AgentSession> {
    let mut acc = SessionAccumulator::new(AGENT_CURSOR, path, updated);
    acc.conversation_id = Some(acc.session_id.clone());
    let mut events = SessionEvents::default();
    let mut current_prompt_index = 0usize;

    // Resolve cwd before the walk so tool events group their paths against it.
    acc.cwd = cursor_session_cwd(content, children);

    let mut delegations = Vec::new();
    cursor_absorb_transcript(
        content,
        CursorScope::Parent,
        &mut acc,
        &mut events,
        &mut current_prompt_index,
        &mut delegations,
    );
    for (_, child_content) in children {
        // Attribute the child's work to the prompt that delegated it, not the last one.
        let mut index = cursor_delegating_prompt_index(child_content, &delegations)
            .unwrap_or(current_prompt_index);
        cursor_absorb_transcript(
            child_content,
            CursorScope::Subagent,
            &mut acc,
            &mut events,
            &mut index,
            &mut Vec::new(),
        );
    }

    acc.finish_with_events(events)
}

// A sub-agent's user records hold the generated Task prompt, not a human one.
#[derive(Clone, Copy, PartialEq, Eq)]
enum CursorScope {
    Parent,
    Subagent,
}

fn cursor_absorb_transcript(
    content: &str,
    scope: CursorScope,
    acc: &mut SessionAccumulator,
    events: &mut SessionEvents,
    current_prompt_index: &mut usize,
    delegations: &mut Vec<(usize, String)>,
) {
    // Tools recorded since the last turn marker, so a failed turn can mark them.
    let mut turn_start = events.tools.len();
    // Clock carried forward from the most recent user message wrapper.
    let mut current_ts_ms: Option<i64> = None;
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        // Cursor appends while a session runs, so a torn final line is expected
        // rather than exceptional. Skip it and keep the records we already have.
        let Ok(record) = serde_json::from_str::<Value>(line) else {
            continue;
        };

        // Cursor writes no tool_result, so a failed turn is the only outcome signal.
        if record.get("type").and_then(Value::as_str) == Some("turn_ended") {
            let failed = record
                .get("status")
                .and_then(Value::as_str)
                .is_some_and(|status| {
                    matches!(
                        status,
                        "error" | "failed" | "fail" | "cancelled" | "canceled"
                    )
                });
            if failed {
                for tool in events.tools.iter_mut().skip(turn_start) {
                    tool.status = "fail".to_string();
                }
            }
            turn_start = events.tools.len();
            continue;
        }

        match record.get("role").and_then(Value::as_str) {
            Some("user") => {
                let raw = cursor_text_of(&record);
                // The only clock a transcript has, and children carry one too.
                if let Some(ts) = cursor_wrapper_ts_ms(&raw) {
                    current_ts_ms = Some(ts);
                }
                if scope == CursorScope::Parent {
                    let text = cursor_user_query(&raw);
                    if !text.is_empty() {
                        *current_prompt_index =
                            events.upsert_prompt(current_ts_ms, &text, Vec::new());
                        if acc.prompt_preview.is_none() {
                            acc.prompt_preview = Some(truncate_clean(&text, 180));
                        }
                    }
                }
            }
            Some("assistant") => {
                for part in cursor_tool_uses(&record) {
                    if scope == CursorScope::Parent
                        && part.get("name").and_then(Value::as_str) == Some("Task")
                        && let Some(prompt) = part
                            .get("input")
                            .and_then(|input| input.get("prompt"))
                            .and_then(Value::as_str)
                            .filter(|prompt| !prompt.trim().is_empty())
                    {
                        delegations.push((*current_prompt_index, prompt.trim().to_string()));
                    }
                    cursor_push_tool_event(part, acc, events, *current_prompt_index, current_ts_ms);
                }
                let text = cursor_text_of(&record);
                if !text.is_empty() {
                    events.llm_responses.push(LlmResponse {
                        ts_ms: current_ts_ms,
                        prompt_index: *current_prompt_index,
                        // Model, tokens, and timestamps live in state.vscdb, not
                        // the transcript. The SQLite enrichment fills them in.
                        model: String::new(),
                        source_id: String::new(),
                        text_hash: short_hash(&text, 12),
                        text: bounded_detail_text(&text),
                        preview: truncate_clean(&text, 140),
                        input_tokens: 0,
                        output_tokens: 0,
                        cache_tokens: 0,
                        total_tokens: 0,
                        tag: String::new(),
                        response_phase: String::new(),
                        skill: String::new(),
                        task_path: Vec::new(),
                    });
                }
            }
            _ => {}
        }
    }
}

fn cursor_session_cwd(content: &str, children: &[(PathBuf, String)]) -> Option<String> {
    let mut absolute = Vec::new();
    for transcript in std::iter::once(content).chain(children.iter().map(|(_, body)| body.as_str()))
    {
        for line in transcript.lines() {
            let Ok(record) = serde_json::from_str::<Value>(line.trim()) else {
                continue;
            };
            for part in cursor_tool_uses(&record) {
                let Some(input) = part.get("input") else {
                    continue;
                };
                if let Some(dir) = input.get("working_directory").and_then(Value::as_str)
                    && is_absolute_path_text(dir)
                {
                    return Some(normalize_path_text(dir));
                }
                for key in ["path", "paths"] {
                    match input.get(key) {
                        Some(Value::String(value)) => absolute.push(value.clone()),
                        Some(Value::Array(values)) => absolute
                            .extend(values.iter().filter_map(Value::as_str).map(str::to_string)),
                        _ => {}
                    }
                }
            }
        }
    }
    common_parent_dir(&absolute)
}

fn common_parent_dir(paths: &[String]) -> Option<String> {
    let mut dirs = paths
        .iter()
        .filter(|path| is_absolute_path_text(path))
        .map(|path| normalize_path_text(path))
        .map(|path| {
            let (root, remainder) = path_root(&path);
            let mut parts = remainder
                .split('/')
                .filter(|part| !part.is_empty())
                .map(str::to_string)
                .collect::<Vec<_>>();
            parts.pop();
            (root.to_string(), parts)
        });
    let (root, mut shared) = dirs.next()?;
    for (candidate_root, candidate) in dirs {
        if candidate_root != root {
            return None;
        }
        let keep = shared
            .iter()
            .zip(candidate.iter())
            .take_while(|(left, right)| left == right)
            .count();
        shared.truncate(keep);
    }
    if root == "//" && shared.len() < 2 {
        return None;
    }
    if shared.is_empty() {
        return (root != "/").then_some(root);
    }
    Some(format!("{root}{}", shared.join("/")))
}

fn path_root(path: &str) -> (&str, &str) {
    if let Some(remainder) = path.strip_prefix("//") {
        ("//", remainder)
    } else if path.as_bytes().get(1) == Some(&b':') && path.as_bytes().get(2) == Some(&b'/') {
        (&path[..3], &path[3..])
    } else if let Some(remainder) = path.strip_prefix('/') {
        ("/", remainder)
    } else {
        ("", path)
    }
}

fn cursor_delegating_prompt_index(
    child_content: &str,
    delegations: &[(usize, String)],
) -> Option<usize> {
    if delegations.is_empty() {
        return None;
    }
    let opening = cursor_first_user_text(child_content)?;
    delegations
        .iter()
        .find(|(_, prompt)| opening.contains(prompt.as_str()))
        .map(|(index, _)| *index)
}

fn cursor_wrapper_ts_ms(text: &str) -> Option<i64> {
    const OPEN: &str = "<timestamp>";
    const CLOSE: &str = "</timestamp>";
    let start = text.find(OPEN)? + OPEN.len();
    let rest = &text[start..];
    let raw = rest[..rest.find(CLOSE)?].trim();

    // Trailing "(UTC-5)" gives the offset the local time was written in.
    let (stamp, offset_hours) = match raw.rfind("(UTC") {
        Some(index) => {
            let hours = raw[index + 4..]
                .trim_end_matches(')')
                .trim()
                .parse::<i64>()
                .unwrap_or(0);
            (raw[..index].trim(), hours)
        }
        None => (raw, 0),
    };
    let naive = chrono::NaiveDateTime::parse_from_str(stamp, "%A, %b %d, %Y, %I:%M %p").ok()?;
    Some(naive.and_utc().timestamp_millis() - offset_hours * 3_600_000)
}

fn cursor_user_query(text: &str) -> String {
    const OPEN: &str = "<user_query>";
    const CLOSE: &str = "</user_query>";
    let Some(start) = text.find(OPEN) else {
        return text.trim().to_string();
    };
    let rest = &text[start + OPEN.len()..];
    let inner = match rest.find(CLOSE) {
        Some(end) => &rest[..end],
        // A torn final line can cut the closing tag off.
        None => rest,
    };
    inner.trim().to_string()
}

fn cursor_first_user_text(content: &str) -> Option<String> {
    content.lines().find_map(|line| {
        let record = serde_json::from_str::<Value>(line.trim()).ok()?;
        (record.get("role").and_then(Value::as_str) == Some("user"))
            .then(|| cursor_text_of(&record))
            .filter(|text| !text.is_empty())
    })
}

fn cursor_tool_uses(record: &Value) -> Vec<&Value> {
    record
        .get("message")
        .and_then(|message| message.get("content"))
        .and_then(Value::as_array)
        .map(|parts| {
            parts
                .iter()
                .filter(|part| part.get("type").and_then(Value::as_str) == Some("tool_use"))
                .collect()
        })
        .unwrap_or_default()
}

fn cursor_push_tool_event(
    part: &Value,
    acc: &mut SessionAccumulator,
    events: &mut SessionEvents,
    prompt_index: usize,
    ts_ms: Option<i64>,
) {
    let Some(name) = part
        .get("name")
        .and_then(Value::as_str)
        .filter(|n| !n.is_empty())
    else {
        return;
    };
    let input = part.get("input").cloned().unwrap_or(Value::Null);

    acc.add_tool(name);
    let event = tool_event_from_input(
        acc.cwd.as_deref(),
        // Inherited from the turn's wrapper. Cursor records no call id.
        ts_ms,
        prompt_index,
        name,
        &input,
        None,
        Vec::new(),
    );
    for path in &event.paths {
        acc.add_file(&path.path);
    }
    events.tools.push(event);
}

fn cursor_text_of(record: &Value) -> String {
    let Some(parts) = record
        .get("message")
        .and_then(|message| message.get("content"))
        .and_then(Value::as_array)
    else {
        return String::new();
    };
    parts
        .iter()
        .filter(|part| part.get("type").and_then(Value::as_str) == Some("text"))
        .filter_map(|part| part.get("text").and_then(Value::as_str))
        .collect::<Vec<_>>()
        .join("\n")
        .trim()
        .to_string()
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
            let normalized = normalize_path_text(&path.to_string_lossy());
            normalized.ends_with(".json")
                && normalized
                    .rsplit('/')
                    .next()
                    .is_some_and(|name| name.starts_with("session-"))
                && normalized.contains("/chats/")
        }
        AGENT_CURSOR => is_cursor_parent_transcript(path),
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
        .or_else(|| {
            std::env::var_os("HOME")
                .map(PathBuf::from)
                .filter(|home| home.is_absolute())
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
            text: bounded_detail_text(text),
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
        invoked_skill: String::new(),
        skill: String::new(),
        task_path,
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
    } else if lower.contains("delete") {
        // Cursor deletes files through a dedicated Delete tool rather than a
        // patch or a shell rm, so without this the deletion records no path.
        "delete"
    } else if is_shell {
        if effect == "read" { "read" } else { "write" }
    } else {
        return Vec::new();
    };
    let mut rows = BTreeMap::<String, (String, Option<String>)>::new();
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
                            rows.remove(&source);
                            rows.insert(path.clone(), ("rename".to_string(), Some(source)));
                            continue;
                        }
                        rows.insert(path, (access.to_string(), None));
                    }
                }
            }
        }
    }

    if is_shell && !has_patch {
        for (path, access, previous_path) in shell_file_actions(command, input, 0) {
            rows.insert(path, (access, previous_path));
        }
        for nested in embedded_json_objects(command, "tools.exec_command(") {
            let nested_command = command_from_tool_input(&nested);
            for (path, access, previous_path) in shell_file_actions(&nested_command, &nested, 0) {
                rows.insert(path, (access, previous_path));
            }
        }
    }
    rows.into_iter()
        .map(|(path, (access, previous_path))| ToolPath {
            path,
            access,
            previous_path,
        })
        .collect()
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

fn shell_file_actions(
    command: &str,
    input: &Value,
    depth: usize,
) -> Vec<(String, String, Option<String>)> {
    if depth > 2 {
        return Vec::new();
    }
    // Cursor's Shell tool names this working_directory rather than workdir or
    // cwd, and it is the only cwd signal on a command that has no leading cd.
    let mut cwd = ["workdir", "cwd", "working_directory"]
        .iter()
        .find_map(|key| input.get(*key).and_then(Value::as_str))
        .map(normalize_path_text);
    let mut rows = Vec::new();
    for parts in shell_segments(command) {
        let Some(command_index) = shell_command_index(&parts) else {
            continue;
        };
        let name = process_name_from_part(&parts[command_index]).unwrap_or_default();
        let operands = &parts[command_index + 1..];
        if name == "cd" {
            if let Some(path) = operands.iter().find(|value| !value.starts_with('-')) {
                cwd = Some(if is_absolute_path_text(path) {
                    normalize_path_text(path)
                } else {
                    join_path_text(cwd.as_deref().unwrap_or_default(), path)
                });
            }
            continue;
        }
        let mut actions = shell_segment_actions(&name, operands, input, depth);
        for (path, _, previous_path) in &mut actions {
            if !path.starts_with(['~', '$'])
                && !is_absolute_path_text(path)
                && let Some(base) = &cwd
            {
                *path = join_path_text(base, path);
            }
            *path = clean_path_token(path);
            if let Some(previous) = previous_path {
                if !previous.starts_with(['~', '$'])
                    && !is_absolute_path_text(previous)
                    && let Some(base) = &cwd
                {
                    *previous = join_path_text(base, previous);
                }
                *previous = clean_path_token(previous);
            }
        }
        rows.extend(actions.into_iter().filter(|(path, _, _)| !path.is_empty()));
    }
    rows
}

fn shell_segment_actions(
    name: &str,
    operands: &[String],
    input: &Value,
    depth: usize,
) -> Vec<(String, String, Option<String>)> {
    let mut rows = Vec::new();
    let mut values = Vec::new();
    let mut index = 0;
    while index < operands.len() {
        if is_redirection_token(&operands[index]) {
            if let Some(path) = operands.get(index + 1)
                && plausible_path_operand(path)
            {
                let access = if [">", ">>", "&>", "&>>"].contains(&operands[index].as_str()) {
                    "write"
                } else if ["<", "<>"].contains(&operands[index].as_str()) {
                    "read"
                } else {
                    index += 2;
                    continue;
                };
                rows.push((path.clone(), access.into(), None));
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
            .filter(|value| !value.starts_with('-') && plausible_path_operand(value))
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
                for source in sources {
                    rows.push((source.clone(), "read".into(), None));
                    let destination = destination_path(target, source, sources.len() > 1);
                    rows.push((destination, "create".into(), None));
                }
            }
        }
        "mv" => {
            let paths = paths(&values);
            if let Some((target, sources)) = paths.split_last() {
                for source in sources {
                    rows.push((
                        destination_path(target, source, sources.len() > 1),
                        "rename".into(),
                        Some(source.clone()),
                    ));
                }
            }
        }
        "rm" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "delete".into(), None)),
        ),
        "touch" | "install" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "create".into(), None)),
        ),
        "tee" => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "write".into(), None)),
        ),
        "cat" | "head" | "tail" | "nl" | "wc" | "source" | "." => rows.extend(
            paths(&values)
                .into_iter()
                .map(|path| (path, "read".into(), None)),
        ),
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
                } else if plausible_path_operand(value) {
                    rows.push((
                        value.clone(),
                        if in_place { "write" } else { "read" }.into(),
                        None,
                    ));
                }
            }
        }
        "find" => rows.extend(
            values
                .iter()
                .take_while(|value| !value.starts_with('-') && value.as_str() != "!")
                .filter(|value| plausible_path_operand(value))
                .cloned()
                .map(|path| (path, "read".into(), None)),
        ),
        "rg" | "grep" | "jq" => {
            let mut expression_seen = values.iter().any(|value| value == "--files");
            for value in &values {
                if value.starts_with('-') {
                    continue;
                }
                if !expression_seen {
                    expression_seen = true;
                } else if plausible_path_operand(value) {
                    rows.push((value.clone(), "read".into(), None));
                }
            }
        }
        _ => {}
    }
    rows
}

fn destination_path(target: &str, source: &str, multiple: bool) -> String {
    if multiple || target.ends_with(['/', '\\']) {
        join_path_text(target, path_basename(source))
    } else {
        normalize_path_text(target)
    }
}

fn normalize_path_text(path: &str) -> String {
    path.replace('\\', "/")
}

fn is_absolute_path_text(path: &str) -> bool {
    let path = normalize_path_text(path);
    path.starts_with('/')
        || path.as_bytes().get(1) == Some(&b':') && path.as_bytes().get(2) == Some(&b'/')
}

fn join_path_text(base: &str, child: &str) -> String {
    let base = normalize_path_text(base);
    let child = normalize_path_text(child);
    if base.is_empty() || is_absolute_path_text(&child) {
        child
    } else {
        format!(
            "{}/{}",
            base.trim_end_matches('/'),
            child.trim_start_matches('/')
        )
    }
}

fn path_basename(path: &str) -> &str {
    path.rsplit(['/', '\\']).next().unwrap_or(path)
}

fn collect_path_fields(
    value: &Value,
    access: &str,
    out: &mut BTreeMap<String, (String, Option<String>)>,
) {
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
                        out.insert(path, (access.to_string(), None));
                    }
                } else if matches!(key.as_str(), "paths" | "file_paths" | "filepaths")
                    && let Some(items) = value.as_array()
                {
                    // Cursor's ReadLints takes a list rather than a single path.
                    // Generic array recursion below never reaches bare strings.
                    for item in items.iter().filter_map(Value::as_str) {
                        let path = clean_path_token(item);
                        if !path.is_empty() {
                            out.insert(path, (access.to_string(), None));
                        }
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

/// Read the newest plan update from a bounded Codex rollout tail.
pub fn codex_latest_plan(content: &str) -> Option<Vec<PlanStep>> {
    content.lines().rev().find_map(|line| {
        let obj: Value = serde_json::from_str(line).ok()?;
        let payload = obj.get("payload")?;
        let payload_type = payload.get("type").and_then(Value::as_str)?;
        let (name, input) = match payload_type {
            "function_call" => {
                let name = payload.get("name").and_then(Value::as_str)?.to_string();
                let input = payload
                    .get("arguments")
                    .and_then(Value::as_str)
                    .and_then(|raw| serde_json::from_str(raw).ok())
                    .unwrap_or(Value::Null);
                (name, input)
            }
            "custom_tool_call" => codex_custom_tool_input(
                payload
                    .get("name")
                    .and_then(Value::as_str)
                    .unwrap_or("custom"),
                payload
                    .get("input")
                    .and_then(Value::as_str)
                    .unwrap_or_default(),
            ),
            _ => return None,
        };
        if !is_plan_tool(&name) {
            return None;
        }
        let mut stack = SemanticTaskStack::default();
        stack.observe_plan(&input);
        Some(stack.plan)
    })
}

fn exact_claude_skill_invocation(name: &str, input: &Value) -> Option<String> {
    (name == "Skill")
        .then(|| input.get("skill").and_then(Value::as_str))
        .flatten()
        .map(str::trim)
        .filter(|skill| !skill.is_empty())
        .map(str::to_string)
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
    if n.ends_with("exec_command") || n.ends_with("shell_command") || n == "bash" || n == "shell" {
        "shell"
    } else if [
        "apply_patch",
        "edit",
        "write",
        "multiedit",
        "notebookedit",
        "strreplace",
        "delete",
    ]
    .contains(&n.as_str())
    {
        "edit"
    } else if ["read", "grep", "glob", "ls", "readlints"].contains(&n.as_str()) {
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

fn plausible_path_operand(part: &str) -> bool {
    let part = part.trim_matches(['"', '\'']);
    // A bare number here is a file descriptor: `cat x 2>&1` splits out a lone `2`.
    !part.is_empty() && !part.chars().all(|c| c.is_ascii_digit()) && !definitely_not_a_path(part)
}

fn plausible_path_token(part: &str) -> bool {
    let part = part.trim_matches(['"', '\'']);
    if definitely_not_a_path(part) {
        return false;
    }
    let suffix = Path::new(part)
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("");
    part.contains('/')
        || [
            "rs", "py", "md", "json", "ts", "tsx", "toml", "lock", "js", "c", "h", "svg", "html",
            "css",
        ]
        .contains(&suffix)
}

fn definitely_not_a_path(part: &str) -> bool {
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
        return true;
    }
    false
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

fn claude_usage_key(obj: &Value) -> String {
    obj.get("requestId")
        .or_else(|| obj.pointer("/message/id"))
        .or_else(|| obj.get("uuid"))
        .and_then(Value::as_str)
        .unwrap_or("usage")
        .to_string()
}

fn claude_source_completion_id(obj: &Value) -> String {
    obj.pointer("/message/id")
        .or_else(|| obj.get("requestId"))
        .or_else(|| obj.get("uuid"))
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string()
}

fn claude_user_starts_prompt(
    obj: &Value,
    content: &Value,
    text: &str,
    active_prompt_id: Option<&str>,
) -> bool {
    if obj.get("isMeta").and_then(Value::as_bool) == Some(true)
        || obj.get("sourceToolUseID").is_some()
        || obj.get("sourceToolAssistantUUID").is_some()
        || ["attachment", "attachments", "image", "images"]
            .iter()
            .any(|key| obj.get(*key).is_some())
        || content.as_array().is_some_and(|items| {
            !items.is_empty()
                && items.iter().all(|item| {
                    matches!(
                        item.get("type").and_then(Value::as_str),
                        Some("attachment" | "document" | "file" | "image")
                    )
                })
        })
        || [
            "<local-command-caveat>",
            "<local-command-stdout>",
            "<system-reminder>",
            "<ide_opened_file>",
            "<ide_selection>",
        ]
        .iter()
        .any(|prefix| text.starts_with(prefix))
    {
        return false;
    }
    match obj
        .get("promptId")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
    {
        Some(prompt_id) => active_prompt_id != Some(prompt_id),
        None => active_prompt_id.is_none(),
    }
}

fn local_message_preview(value: &Value) -> Option<String> {
    let mut parts = Vec::new();
    collect_local_text(value, &mut parts);
    clean_prompt_text(&parts.join("\n"))
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
    let mut text = text.trim();
    text = text
        .strip_prefix("<session>")
        .and_then(|text| text.strip_suffix("</session>"))
        .unwrap_or(text)
        .trim();
    if text.starts_with("<in-app-browser-context") {
        text = text.rsplit_once("## My request:")?.1.trim();
    }
    const HOST_CONTEXT_PREFIXES: &[&str] = &[
        "<environment_context",
        "<recommended_plugins",
        "<app-context",
        "<skills_instructions",
        "<permissions instructions",
        "<collaboration_mode",
        "<subagent_notification",
    ];
    if HOST_CONTEXT_PREFIXES
        .iter()
        .any(|prefix| text.starts_with(prefix))
    {
        return None;
    }
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

const MAX_DETAIL_TEXT_BYTES: usize = 64 * 1024;

/// Preserve source-visible transcript text while bounding one serialized
/// message. Session-detail APIs apply a second aggregate budget.
fn bounded_detail_text(text: &str) -> String {
    if text.len() <= MAX_DETAIL_TEXT_BYTES {
        return text.to_string();
    }
    let mut end = MAX_DETAIL_TEXT_BYTES;
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    format!("{}\n[… message truncated by AgentSight …]", &text[..end])
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
    use std::time::{SystemTime, UNIX_EPOCH};

    // A parent transcript that both delegates and works directly, since Cursor mixes both.
    fn cursor_parent_fixture() -> String {
        [
            // Cursor wraps every user message, parent and child alike.
            r#"{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Friday, Aug 7, 2026, 10:12 PM (UTC-5)</timestamp>\n<user_query>\ncreate hello.py\n</user_query>"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"text","text":"delegating"},{"type":"tool_use","name":"Task","input":{"description":"Create hello.py","prompt":"make it","subagent_type":"generalPurpose"}}]}}"#,
            r#"{"type":"turn_ended","status":"success"}"#,
            r#"{"role":"user","message":{"content":[{"type":"text","text":"now delete it"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Delete","input":{"path":"/repo/hello.py"}},{"type":"text","text":"deleted"}]}}"#,
            r#"{"type":"turn_ended","status":"success"}"#,
        ]
        .join("\n")
    }

    // The child spawned by the Task call above; all of that turn's real work is here.
    fn cursor_subagent_fixture() -> String {
        [
            // The Task prompt in the child's first message is the only link to the parent.
            r#"{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Friday, Aug 7, 2026, 10:12 PM (UTC-5)</timestamp>\n<user_query>\nmake it\n</user_query>"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"/repo/hello.py","contents":"print(1)\n"}},{"type":"text","text":"written"}]}}"#,
            r#"{"type":"turn_ended","status":"success"}"#,
        ]
        .join("\n")
    }

    #[test]
    fn cursor_transcript_counts_prompts_and_responses() {
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &cursor_parent_fixture(),
        )
        .expect("session");

        assert_eq!(session.agent_type, AGENT_CURSOR);
        assert_eq!(session.events.prompts.len(), 2);
        assert_eq!(session.events.llm_responses.len(), 2);
        // The <timestamp>/<user_query> wrapper is stripped, so previews show
        // what the person typed rather than Cursor's header.
        assert_eq!(session.events.prompts[0].preview, "create hello.py");
        assert_eq!(session.events.prompts[1].preview, "now delete it");
        assert_eq!(session.events.prompts[1].index, 1);
        assert_eq!(session.events.llm_responses[1].prompt_index, 1);
        assert_eq!(session.prompt_preview.as_deref(), Some("create hello.py"));
    }

    #[test]
    fn cursor_file_discovery_aggregates_children_but_content_parsing_stays_pure() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "agentsight-cursor-parser-{}-{unique}",
            std::process::id()
        ));
        let parent_dir = root.join("session");
        let child_dir = parent_dir.join("subagents");
        fs::create_dir_all(&child_dir).expect("create fixture directories");
        let parent = parent_dir.join("session.jsonl");
        let parent_content = cursor_parent_fixture();
        fs::write(&parent, &parent_content).expect("write parent transcript");
        fs::write(child_dir.join("child.jsonl"), cursor_subagent_fixture())
            .expect("write child transcript");

        let candidate = SessionCandidate {
            agent: AGENT_CURSOR,
            path: parent.clone(),
            updated: UNIX_EPOCH,
        };
        let from_file = parse_session_file(&candidate).expect("file session");
        let from_content =
            parse_session_content(AGENT_CURSOR, &parent, UNIX_EPOCH, &parent_content)
                .expect("content session");

        assert_eq!(from_file.tools.get("Write"), Some(&1));
        assert_eq!(from_content.tools.get("Write"), None);
        fs::remove_dir_all(root).expect("remove fixture directories");
    }

    #[test]
    fn cursor_tool_uses_become_events_and_unknown_names_are_kept() {
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"do work"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"cargo test","description":"run tests"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"StrReplace","input":{"path":"/repo/a.rs","old_string":"x","new_string":"y"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"ReadLints","input":{"paths":["/repo/a.rs"]}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"SomeToolWeHaveNeverSeen","input":{"whatever":1}}]}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        let named = |name: &str| {
            session
                .events
                .tools
                .iter()
                .find(|tool| tool.tool_name == name)
                .unwrap_or_else(|| panic!("{name} missing"))
        };
        assert_eq!(session.events.tools.len(), 4);
        assert_eq!(named("Shell").category, "shell");
        assert_eq!(named("Shell").command, "cargo test");
        assert_eq!(named("Shell").command_name, "cargo");
        assert_eq!(named("StrReplace").category, "edit");
        assert_eq!(named("ReadLints").category, "read");
        // An unfamiliar name still produces an event, in the catch-all category.
        assert_eq!(named("SomeToolWeHaveNeverSeen").category, "tool");
        // Cursor has no tool call ids, and no tool_result records to upgrade a
        // call's status, so every Cursor tool event stays "observed".
        assert!(named("Shell").call_id.is_none());
        assert_eq!(named("Shell").status, "observed");
        assert_eq!(session.tools.get("Shell"), Some(&1));
    }

    #[test]
    fn cursor_file_tools_map_to_access_kinds() {
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"work"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/repo/a.rs"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"/repo/b.rs","contents":"fn main() {}"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"StrReplace","input":{"path":"/repo/c.rs","old_string":"x","new_string":"y"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Delete","input":{"path":"/repo/d.rs"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"ReadLints","input":{"paths":["/repo/e.rs","/repo/f.rs"]}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Grep","input":{"pattern":"timeout","path":"/repo","-i":true}}]}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        let access_of = |path: &str| {
            session
                .events
                .tools
                .iter()
                .flat_map(|tool| tool.paths.iter())
                .find(|candidate| candidate.path == path)
                .unwrap_or_else(|| panic!("{path} missing"))
                .access
                .clone()
        };
        assert_eq!(access_of("/repo/a.rs"), "read");
        assert_eq!(access_of("/repo/b.rs"), "write");
        assert_eq!(access_of("/repo/c.rs"), "write");
        assert_eq!(access_of("/repo/d.rs"), "delete");
        // ReadLints takes a list, not a single path.
        assert_eq!(access_of("/repo/e.rs"), "read");
        assert_eq!(access_of("/repo/f.rs"), "read");
        // Flag-shaped keys such as "-i" are not paths.
        assert_eq!(access_of("/repo"), "read");
        assert_eq!(session.files.get("/repo/d.rs"), Some(&1));
    }

    #[test]
    fn cursor_shell_mv_yields_rename_with_previous_path() {
        // Rename never arrives as a dedicated Cursor tool. It only ever comes
        // through Shell, and Cursor emits it as a compound command with a cd.
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"tidy up"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"cd /repo && mv hello.py greet.py","description":"rename it"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"rm /repo/stale.txt","description":"drop it"}}]}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        let all: Vec<&ToolPath> = session
            .events
            .tools
            .iter()
            .flat_map(|tool| tool.paths.iter())
            .collect();
        let renamed = all
            .iter()
            .find(|path| path.access == "rename")
            .expect("rename");
        assert_eq!(renamed.path, "/repo/greet.py");
        assert_eq!(renamed.previous_path.as_deref(), Some("/repo/hello.py"));
        assert!(
            all.iter()
                .any(|path| path.access == "delete" && path.path == "/repo/stale.txt")
        );
        assert_eq!(session.events.tools[0].category, "shell");
        assert_eq!(
            session.events.tools[0].command,
            "cd /repo && mv hello.py greet.py"
        );
        // command_name is the first token of a compound command, so `cd` wins here.
        assert_eq!(session.events.tools[0].command_name, "cd");
        assert!(
            !session.events.tools[0].process_chain.is_empty(),
            "Shell events must carry a process chain"
        );
    }

    #[test]
    fn cursor_shell_working_directory_resolves_relative_paths() {
        // Cursor names this working_directory where Claude and Codex use workdir.
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"move it"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"mv hello.py archive/greet.py","working_directory":"/repo","description":"move"}}]}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        let renamed = session.events.tools[0]
            .paths
            .iter()
            .find(|path| path.access == "rename")
            .expect("rename");
        assert_eq!(renamed.path, "/repo/archive/greet.py");
        assert_eq!(renamed.previous_path.as_deref(), Some("/repo/hello.py"));
    }

    #[test]
    fn cursor_subagent_work_folds_into_the_delegating_prompt() {
        let children = vec![(
            PathBuf::from("/tmp/subagents/child.jsonl"),
            cursor_subagent_fixture(),
        )];
        let session = parse_cursor_jsonl(
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &cursor_parent_fixture(),
            &children,
        )
        .expect("session");

        // Counts span parent and children. Reading the parent alone would miss
        // the Write entirely, since that turn only issued a Task.
        assert_eq!(session.tools.get("Task"), Some(&1));
        assert_eq!(session.tools.get("Delete"), Some(&1));
        assert_eq!(session.tools.get("Write"), Some(&1));
        // Exactly once: two calls in the parent, one in the child, no more.
        assert_eq!(session.events.tools.len(), 3);
        assert_eq!(session.tools.values().sum::<usize>(), 3);
        assert_eq!(session.files.get("/repo/hello.py"), Some(&2));

        let tool_at = |name: &str| {
            session
                .events
                .tools
                .iter()
                .find(|tool| tool.tool_name == name)
                .unwrap_or_else(|| panic!("{name} missing"))
                .prompt_index
        };
        // The child ran under prompt 0, which delegated. Without the Task
        // prompt match its work would land on prompt 1, the last one seen.
        assert_eq!(tool_at("Write"), 0);
        assert_eq!(tool_at("Delete"), 1);
    }

    #[test]
    fn cursor_cwd_prefers_working_directory_then_common_path_prefix() {
        let with_dir = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"go"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"ls","working_directory":"/repo/app"}}]}}"#,
        ]
        .join("\n");
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &with_dir,
        )
        .expect("session");
        assert_eq!(session.cwd.as_deref(), Some("/repo/app"));

        // With no working_directory anywhere, fall back to the directory that
        // contains every absolute path the tools touched.
        let paths_only = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"go"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"/repo/app/src/main.rs","contents":"x"}}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/repo/app/README.md"}}]}}"#,
        ]
        .join("\n");
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &paths_only,
        )
        .expect("session");
        assert_eq!(session.cwd.as_deref(), Some("/repo/app"));

        // Nothing to go on leaves cwd unset rather than guessed. The project
        // directory name is a lossy encoding and inverting it invents paths.
        let bare = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"hello"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}"#,
        ]
        .join("\n");
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/projects/Users-user-cursor-test/agent-transcripts/a/a.jsonl"),
            UNIX_EPOCH,
            &bare,
        )
        .expect("session");
        assert_eq!(session.cwd, None);
    }

    #[test]
    fn cursor_cwd_preserves_windows_drive_and_unc_roots() {
        assert_eq!(
            common_parent_dir(&[r"C:\file.rs".to_string()]).as_deref(),
            Some("C:/")
        );
        assert_eq!(
            common_parent_dir(&[r"\\server\share\file.rs".to_string()]).as_deref(),
            Some("//server/share")
        );
        assert_eq!(
            common_parent_dir(&[
                r"C:\repo\src\main.rs".to_string(),
                r"C:\repo\README.md".to_string(),
            ])
            .as_deref(),
            Some("C:/repo")
        );
        assert_eq!(
            common_parent_dir(&[
                r"\\server\share-a\file.rs".to_string(),
                r"\\server\share-b\file.rs".to_string(),
            ]),
            None
        );
    }

    #[test]
    fn cursor_truncated_and_empty_transcripts_degrade_without_error() {
        // Cursor appends while a session runs, so the last line can be torn.
        // Everything before it must still parse.
        let torn = concat!(
            r#"{"role":"user","message":{"content":[{"type":"text","text":"start"}]}}"#,
            "\n",
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/repo/a.rs"}}]}}"#,
            "\n",
            r#"{"role":"assistant","message":{"content":[{"type":"tool_"#,
        );
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            torn,
        )
        .expect("session");
        assert_eq!(session.events.prompts.len(), 1);
        assert_eq!(session.tools.get("Read"), Some(&1));

        // A single record with no tool calls is still a real session and comes
        // back valid, just with nothing in it.
        let one_prompt =
            r#"{"role":"user","message":{"content":[{"type":"text","text":"just asking"}]}}"#;
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            one_prompt,
        )
        .expect("a lone prompt is still a session");
        assert!(session.events.tools.is_empty());
        assert_eq!(session.prompt_preview.as_deref(), Some("just asking"));

        // A fragment with no user message at all is a different thing: nothing
        // was asked, so there is no session to report. Same treatment every
        // other agent gets, and it keeps blank rows out of `top`.
        for empty in [
            "",
            "\n\n",
            r#"{"type":"turn_ended","status":"error","error":"aborted"}"#,
            "not json at all",
        ] {
            assert!(
                parse_session_content(
                    AGENT_CURSOR,
                    &PathBuf::from("/tmp/session.jsonl"),
                    UNIX_EPOCH,
                    empty,
                )
                .is_none(),
                "expected no session for {empty:?}"
            );
        }

        // A child whose Task prompt no longer matches still contributes its
        // work, attributed to the last prompt rather than dropped.
        let orphan = vec![(
            PathBuf::from("/tmp/subagents/orphan.jsonl"),
            [
                r#"{"role":"user","message":{"content":[{"type":"text","text":"unrelated wording"}]}}"#,
                r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"/repo/z.rs","contents":"x"}}]}}"#,
            ]
            .join("\n"),
        )];
        let session = parse_cursor_jsonl(
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &cursor_parent_fixture(),
            &orphan,
        )
        .expect("session");
        assert_eq!(session.tools.get("Write"), Some(&1));
    }

    #[test]
    fn cursor_failed_turn_marks_its_tool_calls() {
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"first"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/repo/ok.rs"}}]}}"#,
            r#"{"type":"turn_ended","status":"success"}"#,
            r#"{"role":"user","message":{"content":[{"type":"text","text":"second"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"cat /repo/missing.rs"}}]}}"#,
            r#"{"type":"turn_ended","status":"error","error":"command failed"}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        let status_of = |name: &str| {
            session
                .events
                .tools
                .iter()
                .find(|tool| tool.tool_name == name)
                .unwrap_or_else(|| panic!("{name} missing"))
                .status
                .clone()
        };
        // Cursor has no per-tool results, so a failed turn is the only outcome
        // signal there is, and it applies to that turn's calls only.
        assert_eq!(status_of("Read"), "observed");
        assert_eq!(status_of("Shell"), "fail");
    }

    #[test]
    fn cursor_wrapper_timestamp_becomes_the_event_clock() {
        // Cursor writes no timestamp fields anywhere. The wrapper on each user
        // message is the only clock, and without it every consumer that
        // requires ts_ms drops all Cursor events. agentvis is one of those.
        let content = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Friday, Aug 7, 2026, 10:12 PM (UTC-5)</timestamp>\n<user_query>\ngo\n</user_query>"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"text","text":"reading it"},{"type":"tool_use","name":"Read","input":{"path":"/repo/a.rs"}}]}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &content,
        )
        .expect("session");

        // 10:12 PM at UTC-5 is 03:12 UTC the next day. Cross-checked against
        // state.vscdb, where the matching bubble records 03:11:58.512Z, so the
        // value is correct and simply rounded to the minute.
        const EXPECTED_MS: i64 = 1_786_158_720_000;
        assert_eq!(session.events.prompts[0].ts_ms, Some(EXPECTED_MS));
        assert_eq!(session.events.tools[0].ts_ms, Some(EXPECTED_MS));
        assert_eq!(session.events.llm_responses[0].ts_ms, Some(EXPECTED_MS));

        // A message with no wrapper leaves the clock unset rather than guessing.
        let bare = [
            r#"{"role":"user","message":{"content":[{"type":"text","text":"no wrapper here"}]}}"#,
            r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"/repo/b.rs"}}]}}"#,
        ]
        .join("\n");
        let session = parse_session_content(
            AGENT_CURSOR,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &bare,
        )
        .expect("session");
        assert_eq!(session.events.tools[0].ts_ms, None);
    }

    #[test]
    fn cursor_subagent_prompts_are_not_user_prompts() {
        let children = vec![(
            PathBuf::from("/tmp/subagents/child.jsonl"),
            cursor_subagent_fixture(),
        )];
        let session = parse_cursor_jsonl(
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &cursor_parent_fixture(),
            &children,
        )
        .expect("session");

        // The child's own "user" record holds the Task prompt Cursor generated,
        // so folding it in must not invent a third human prompt.
        assert_eq!(session.events.prompts.len(), 2);
        assert_eq!(session.events.llm_responses.len(), 3);
    }

    #[test]
    fn cursor_paths_classify_but_only_parents_discover() {
        let home = PathBuf::from("/home/dev");
        let parent = home.join(".cursor/projects/repo/agent-transcripts/abc/abc.jsonl");
        let subagent = home.join(".cursor/projects/repo/agent-transcripts/abc/subagents/def.jsonl");
        let vendored = home.join(".cursor/projects/repo/canvases/node_modules/pkg/data.jsonl");

        // Classification accepts any transcript path: process matching hands
        // it arbitrary fd paths, children included.
        assert_eq!(agent_source_for_path(&parent), Some(AGENT_CURSOR));
        assert_eq!(agent_source_for_path(&subagent), Some(AGENT_CURSOR));
        assert_eq!(agent_source_for_path(&vendored), None);

        // Discovery emits parents only: stem must equal the directory name.
        assert!(is_agent_file_for(AGENT_CURSOR, &parent));
        assert!(!is_agent_file_for(AGENT_CURSOR, &subagent));
        assert!(!is_agent_file_for(AGENT_CURSOR, &vendored));
        assert!(!is_agent_file_for(
            AGENT_CURSOR,
            &home.join(".cursor/projects/repo/agent-transcripts/abc/other.jsonl")
        ));

        assert!(cursor_is_empty_window(&home.join(
            ".cursor/projects/empty-window/agent-transcripts/abc/abc.jsonl"
        )));
        assert!(!cursor_is_empty_window(&parent));

        let fixture = fixture_session_path(AGENT_CURSOR, &home).expect("fixture");
        assert!(is_agent_file_for(AGENT_CURSOR, &fixture));
    }

    #[test]
    fn native_windows_session_paths_classify() {
        assert_eq!(
            agent_source_for_path(Path::new(
                r"C:\Users\dev\.codex\sessions\2026\08\12\session.jsonl"
            )),
            Some(AGENT_CODEX)
        );
        assert_eq!(
            agent_source_for_path(Path::new(
                r"C:\Users\dev\.claude\projects\repo\session.jsonl"
            )),
            Some(AGENT_CLAUDE)
        );
        assert_eq!(
            agent_source_for_path(Path::new(
                r"C:\Users\dev\.cursor\projects\repo\agent-transcripts\id\id.jsonl"
            )),
            Some(AGENT_CURSOR)
        );
        let gemini =
            Path::new(r"C:\Users\dev\.gemini\tmp\repo\chats\session-2026-08-12T00-00-id.json");
        assert_eq!(agent_source_for_path(gemini), Some(AGENT_GEMINI));
        assert!(is_agent_file_for(AGENT_GEMINI, gemini));
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
    fn claude_exact_skill_calls_create_prompt_bounded_latest_wins_scopes() {
        let claude = [
            r#"{"type":"system","skill_listing":["availability only"]}"#,
            r#"{"type":"user","message":{"content":"review the paper"}}"#,
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"s1","name":"Skill","input":{"skill":"check-paper-citations","args":""}}],"usage":{"input_tokens":10,"output_tokens":1}}}"#,
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"b1","name":"Bash","input":{"cmd":"rg citation paper.tex"}}],"usage":{"input_tokens":20,"output_tokens":2}}}"#,
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"s2","name":"Skill","input":{"skill":"iter-refine-writing","args":""}}],"usage":{"input_tokens":30,"output_tokens":3}}}"#,
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"r1","name":"Read","input":{"file_path":"paper.tex"}}],"usage":{"input_tokens":40,"output_tokens":4}}}"#,
            r#"{"type":"user","message":{"content":"now summarize"}}"#,
            r#"{"type":"assistant","message":{"model":"claude-opus","content":[{"type":"text","text":"summary"}],"usage":{"input_tokens":50,"output_tokens":5}}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &claude,
        )
        .expect("session");

        assert_eq!(
            session
                .events
                .tools
                .iter()
                .map(|tool| (tool.tool_name.as_str(), tool.skill.as_str()))
                .collect::<Vec<_>>(),
            [
                ("Skill", "check-paper-citations"),
                ("Bash", "check-paper-citations"),
                ("Skill", "iter-refine-writing"),
                ("Read", "iter-refine-writing"),
            ]
        );
        assert_eq!(
            session
                .events
                .tools
                .iter()
                .map(|tool| tool.invoked_skill.as_str())
                .collect::<Vec<_>>(),
            ["check-paper-citations", "", "iter-refine-writing", ""]
        );
        assert_eq!(
            session
                .events
                .llm_responses
                .iter()
                .map(|response| response.skill.as_str())
                .collect::<Vec<_>>(),
            [
                "",
                "check-paper-citations",
                "check-paper-citations",
                "iter-refine-writing",
                "",
            ]
        );
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
            session.events.plan,
            vec![PlanStep {
                step: "write abstract".to_string(),
                status: "in_progress".to_string(),
            }]
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
        assert_eq!(
            session.events.plan,
            vec![
                PlanStep {
                    step: "write abstract".to_string(),
                    status: "in_progress".to_string(),
                },
                PlanStep {
                    step: "write evaluation".to_string(),
                    status: "pending".to_string(),
                },
            ]
        );
        assert_eq!(codex_latest_plan(&codex), Some(session.events.plan.clone()));
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
        assert_eq!(session.events.prompts[0].text, "review");
        assert_eq!(session.events.llm_responses[0].text, "review complete");
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

    #[test]
    fn file_actions_ignore_patch_and_heredoc_bodies() {
        let patch = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec",
            &json!({"text": r#"const patch = "*** Begin Patch\n*** Update File: src/lib.rs\n+#!/bin/sh\n+docs/not-a-file.md\n*** End Patch"; tools.apply_patch(patch)"#}),
            None,
            Vec::new(),
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
            Vec::new(),
        );
        assert_eq!(heredoc.paths.len(), 1);
        assert_eq!(heredoc.paths[0].path, "src/real.rs");
    }

    #[test]
    fn shell_path_operands_are_not_limited_to_known_extensions() {
        let paths_of = |command: &str| {
            shell_file_actions(command, &json!({"cwd": "/repo"}), 0)
                .into_iter()
                .map(|(path, access, _)| (path, access))
                .collect::<Vec<_>>()
        };

        // A path operand is a path whatever it is called. Before this, only the
        // fourteen extensions the list happened to name were recorded, so a Go,
        // shell or SQL project got no file activity from its shell commands.
        for (command, expected, access) in [
            ("rm build.sh", "/repo/build.sh", "delete"),
            ("rm main.go", "/repo/main.go", "delete"),
            ("rm Dockerfile", "/repo/Dockerfile", "delete"),
            ("mv notes.txt archive.txt", "/repo/archive.txt", "rename"),
            (
                "mv conf.yaml conf.bak.yaml",
                "/repo/conf.bak.yaml",
                "rename",
            ),
            ("touch schema.sql", "/repo/schema.sql", "create"),
        ] {
            assert!(
                paths_of(command)
                    .iter()
                    .any(|(path, kind)| path == expected && kind == access),
                "{command} should record {expected} as {access}, got {:?}",
                paths_of(command)
            );
        }

        // The shared rejections still hold, so refs, ranges, globs, URLs and
        // sed expressions do not become files.
        for command in [
            "rm origin/main",
            "rm HEAD",
            "rm *.log",
            "rm https://example.com/x",
            "rm s/foo/bar/g",
            "rm $TARGET",
            "rm -rf",
        ] {
            assert!(
                paths_of(command).is_empty(),
                "{command} should record nothing, got {:?}",
                paths_of(command)
            );
        }

        // A redirected command splits into a bare file descriptor. Without the
        // numeric guard, every `2>&1` recorded a read of a file called "2".
        let redirected = paths_of("cat notes.txt 2>&1");
        assert!(
            redirected.iter().any(|(path, _)| path == "/repo/notes.txt"),
            "the real file should still be recorded, got {redirected:?}"
        );
        assert!(
            !redirected.iter().any(|(path, _)| path.ends_with("/2")),
            "a file descriptor is not a file, got {redirected:?}"
        );

        for command in ["rm 2", "cat 1"] {
            assert!(
                paths_of(command).is_empty(),
                "{command} should record nothing, got {:?}",
                paths_of(command)
            );
        }
    }

    #[test]
    fn scanned_command_tokens_still_need_evidence_of_being_a_path() {
        // extract_path_groups walks every token of a command rather than a known
        // path position, so there the extension check still earns its place. A
        // bare hostname or version must not become a file.
        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec_command",
            &json!({"cmd": "curl example.com && echo 1.2.3"}),
            None,
            Vec::new(),
        );
        assert!(
            event.path_groups.is_empty(),
            "hostname and version should not become path groups, got {:?}",
            event.path_groups
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
            Vec::new(),
        );
        assert!(unknown.paths.is_empty());

        let write = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "Write",
            &json!({"file_path": "src/existing.rs", "content": "changed"}),
            None,
            Vec::new(),
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
            Vec::new(),
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
            Vec::new(),
        );
        assert_eq!(
            event
                .paths
                .iter()
                .map(|row| (row.path.as_str(), row.previous_path.as_deref()))
                .collect::<Vec<_>>(),
            vec![("x.rs", Some("a.rs")), ("y.rs", Some("b.rs"))]
        );
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

        let claude = concat!(
            r#"{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t0","name":"Read","input":{"file_path":"src/main.rs"}},{"type":"tool_use","id":"t1","name":"Edit","input":{"file_path":"src/lib.rs"}}]}}"#,
            "\n",
            r#"{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"t0","is_error":false,"content":"ok"},{"type":"tool_result","tool_use_id":"t1","is_error":true,"content":"failed"}]}}"#,
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
    fn codex_exec_wrapper_projects_nested_shell_actions() {
        let event = tool_event_from_input(
            Some("/repo"),
            Some(1),
            0,
            "exec",
            &json!({"text": r#"const r = await tools.exec_command({"cmd":"cat src/lib.rs && sed -i 's/a/b/' src/main.rs","workdir":"/repo"});"#}),
            None,
            Vec::new(),
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
    fn claude_uuid_only_fragments_share_one_completion_identity() {
        let claude = [
            r#"{"type":"user","promptId":"p1","message":{"content":"review the paper"}}"#,
            r#"{"type":"assistant","uuid":"completion-1","message":{"model":"claude-opus","content":[{"type":"text","text":"I will use a skill."}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
            r#"{"type":"system","subtype":"internal-marker"}"#,
            r#"{"type":"assistant","uuid":"completion-1","message":{"model":"claude-opus","content":[{"type":"tool_use","id":"s1","name":"Skill","input":{"skill":"paper-writing-style","args":""}}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
            r#"{"type":"assistant","uuid":"completion-1","message":{"model":"claude-opus","content":[{"type":"text","text":"later fragment"}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &claude,
        )
        .expect("session");

        assert_eq!(session.events.llm_responses.len(), 1);
        assert_eq!(session.events.llm_responses[0].source_id, "completion-1");
        assert_eq!(session.events.llm_responses[0].skill, "");
        assert_eq!(
            session.events.llm_responses[0]
                .token_components()
                .into_iter()
                .map(|(_, value)| value)
                .sum::<u64>(),
            113
        );
        assert_eq!(session.events.tools[0].skill, "paper-writing-style");
        assert_eq!(session.events.tools[0].invoked_skill, "paper-writing-style");
    }

    #[test]
    fn claude_skill_scope_ignores_metadata_and_deduplicates_split_completion() {
        let claude = [
            r#"{"type":"system","skill_listing":["availability only"]}"#,
            r#"{"type":"user","promptId":"p1","message":{"content":"review the paper"}}"#,
            r#"{"type":"assistant","requestId":"req-1","message":{"id":"msg-1","model":"claude-opus","content":[{"type":"text","text":"I will apply the citation skill."}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
            r#"{"type":"assistant","requestId":"req-1","message":{"id":"msg-1","model":"claude-opus","content":[{"type":"tool_use","id":"s1","name":"Skill","input":{"skill":"check-paper-citations","args":""}}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
            r#"{"type":"assistant","requestId":"req-1","message":{"id":"msg-1","model":"claude-opus","content":[{"type":"text","text":"same completion after emitting Skill"}],"usage":{"input_tokens":1,"cache_read_input_tokens":100,"output_tokens":12}}}"#,
            r#"{"type":"user","promptId":"p1","isMeta":true,"sourceToolUseID":"s1","message":{"content":[{"type":"text","text":"skill payload"}]}}"#,
            r#"{"type":"last-prompt","lastPrompt":"review the paper"}"#,
            r#"{"type":"user","message":{"content":"<local-command-stdout>metadata</local-command-stdout>"}}"#,
            r#"{"type":"user","promptId":"attachment-only","attachments":[{"file_name":"paper.pdf"}],"message":{"content":"attached context"}}"#,
            r#"{"type":"assistant","requestId":"req-2","message":{"id":"msg-2","model":"claude-opus","content":[{"type":"tool_use","id":"b1","name":"Bash","input":{"cmd":"rg citation paper.tex"}}],"usage":{"input_tokens":2,"cache_read_input_tokens":200,"output_tokens":20}}}"#,
            r#"{"type":"user","promptId":"p1","sourceToolAssistantUUID":"assistant-2","message":{"content":[{"type":"tool_result","tool_use_id":"b1","content":"ok"}]}}"#,
            r#"{"type":"assistant","requestId":"req-3","message":{"id":"msg-3","model":"claude-opus","content":[{"type":"tool_use","id":"r1","name":"Read","input":{"file_path":"paper.tex"}}],"usage":{"input_tokens":3,"cache_read_input_tokens":300,"output_tokens":30}}}"#,
            r#"{"type":"user","promptId":"p2","message":{"content":"now summarize"}}"#,
            r#"{"type":"assistant","requestId":"req-4","message":{"id":"msg-4","model":"claude-opus","content":[{"type":"text","text":"summary"}],"usage":{"input_tokens":4,"cache_read_input_tokens":400,"output_tokens":40}}}"#,
        ]
        .join("\n");

        let session = parse_session_content(
            AGENT_CLAUDE,
            &PathBuf::from("/tmp/session.jsonl"),
            UNIX_EPOCH,
            &claude,
        )
        .expect("session");

        assert_eq!(session.events.prompts.len(), 2);
        assert_eq!(session.events.llm_responses.len(), 4);
        assert_eq!(session.events.llm_responses[0].source_id, "msg-1");
        assert_eq!(
            session.events.llm_responses[0]
                .token_components()
                .into_iter()
                .map(|(_, value)| value)
                .sum::<u64>(),
            113
        );
        assert_eq!(
            session
                .events
                .tools
                .iter()
                .map(|tool| (tool.tool_name.as_str(), tool.skill.as_str()))
                .collect::<Vec<_>>(),
            [
                ("Skill", "check-paper-citations"),
                ("Bash", "check-paper-citations"),
                ("Read", "check-paper-citations"),
            ]
        );
        assert_eq!(
            session
                .events
                .llm_responses
                .iter()
                .map(|response| response.skill.as_str())
                .collect::<Vec<_>>(),
            ["", "check-paper-citations", "check-paper-citations", ""]
        );
    }

    #[test]
    fn invalid_plan_payload_does_not_erase_the_latest_plan() {
        let mut stack = SemanticTaskStack::default();
        stack.observe_plan(&json!({
            "plan": [{"step": "ship the overview", "status": "in_progress"}]
        }));
        stack.observe_plan(&Value::Null);

        assert_eq!(stack.plan.len(), 1);
        assert_eq!(stack.plan[0].step, "ship the overview");
    }

    #[test]
    fn detail_text_is_utf8_safe_and_bounded() {
        let text = "数".repeat(MAX_DETAIL_TEXT_BYTES);
        let bounded = bounded_detail_text(&text);

        assert!(bounded.is_char_boundary(bounded.len()));
        assert!(bounded.len() < text.len());
        assert!(bounded.contains("message truncated"));
    }

    #[test]
    fn hosted_context_is_hidden_but_ambient_request_is_preserved() {
        assert!(clean_prompt_text("<environment_context>secret</environment_context>").is_none());
        assert!(clean_prompt_text("<recommended_plugins>internal</recommended_plugins>").is_none());
        assert_eq!(
            clean_prompt_text(
                "<in-app-browser-context>internal browser state</in-app-browser-context>\n\n## My request:\n修复界面"
            )
            .as_deref(),
            Some("修复界面")
        );
    }

    #[test]
    fn prompt_detail_preserves_source_line_breaks() {
        assert_eq!(
            clean_prompt_text("first line\nsecond line").as_deref(),
            Some("first line\nsecond line")
        );
    }
}
