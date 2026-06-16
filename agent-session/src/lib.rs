// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Portable session IR, parsers, discovery, and process matching for local AI
//! coding-agent transcripts.
//!
//! The crate currently normalizes Claude Code, Codex, and Gemini CLI sessions.
//! It intentionally stops at session data and process/session correlation; UI,
//! database storage, eBPF collection, and OpenTelemetry export belong in
//! applications that consume this crate.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

pub const AGENT_CLAUDE: &str = "claude";
pub const AGENT_CODEX: &str = "codex";
pub const AGENT_GEMINI: &str = "gemini";

pub const TRACE_EBPF_FILE: &str = "ebpf_file";
pub const TRACE_PROC_FD: &str = "proc_fd";
pub const TRACE_STICKY_BINDING: &str = "sticky";
pub const TRACE_RECENT_CWD: &str = "cwd_recent";
pub const SOURCE_SESSION_PROCESS_MATCH: &str = "agent_session.process_match";

const SESSION_PROCESS_START_SKEW_MS: u64 = 30_000;

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct TokenUsage {
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_tokens: i64,
}

impl TokenUsage {
    fn add(&mut self, input: i64, output: i64, cache_creation: i64, cache_read: i64, total: i64) {
        self.input_tokens += input;
        self.output_tokens += output;
        self.cache_creation_tokens += cache_creation;
        self.cache_read_tokens += cache_read;
        self.total_tokens += if total > 0 {
            total
        } else {
            input + output + cache_creation + cache_read
        };
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSession {
    pub agent: String,
    pub session_id: String,
    pub display_id: String,
    pub path: PathBuf,
    pub updated: SystemTime,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub model: Option<String>,
    pub token_usage: TokenUsage,
    pub model_usage: BTreeMap<String, TokenUsage>,
    pub tools: BTreeMap<String, usize>,
    pub files: BTreeMap<String, usize>,
    pub prompt_preview: Option<String>,
    pub duration_ms: u64,
    pub cwd: Option<String>,
    pub last_message_at: Option<String>,
}

#[derive(Debug, Clone)]
pub struct SessionCandidate {
    pub agent: &'static str,
    pub path: PathBuf,
    pub updated: SystemTime,
}

#[derive(Debug, Clone)]
pub struct SessionDirStat {
    pub agent: &'static str,
    pub dir: PathBuf,
    pub sessions: usize,
    pub bytes: u64,
}

#[derive(Default)]
pub struct SessionCache {
    entries: HashMap<PathBuf, CacheEntry>,
    cached_sessions: Vec<AgentSession>,
    last_refresh: Option<Instant>,
    last_limit: usize,
}

struct CacheEntry {
    mtime: SystemTime,
    session: Option<AgentSession>,
}

impl SessionCache {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn discover_cached(&mut self, limit: usize, max_age: Duration) -> Vec<AgentSession> {
        let target = limit.clamp(1, 25);
        if self.last_limit < target
            || self
                .last_refresh
                .is_none_or(|last| last.elapsed() >= max_age)
        {
            self.refresh(target);
        }
        self.cached_sessions.iter().take(target).cloned().collect()
    }

    fn refresh(&mut self, limit: usize) {
        let mut candidates = discover_session_files();
        candidates.sort_by_key(|candidate| std::cmp::Reverse(candidate.updated));
        let target = limit.clamp(1, 25);
        let mut live_paths = HashSet::new();
        let mut sessions = Vec::new();
        let mut seen = HashSet::new();

        for candidate in candidates
            .into_iter()
            .take(target.saturating_mul(3).clamp(10, 75))
        {
            live_paths.insert(candidate.path.clone());
            let session = match self.entries.get(&candidate.path) {
                Some(entry) if entry.mtime == candidate.updated => entry.session.clone(),
                _ => {
                    let parsed = parse_session_file(&candidate);
                    self.entries.insert(
                        candidate.path.clone(),
                        CacheEntry {
                            mtime: candidate.updated,
                            session: parsed.clone(),
                        },
                    );
                    parsed
                }
            };
            if let Some(session) = session
                && seen.insert(session.display_id.clone())
            {
                sessions.push(session);
                if sessions.len() >= target {
                    break;
                }
            }
        }
        self.entries.retain(|path, _| live_paths.contains(path));
        self.cached_sessions = sessions;
        self.last_refresh = Some(Instant::now());
        self.last_limit = target;
    }
}

pub fn discover_session_files() -> Vec<SessionCandidate> {
    user_home_dir()
        .as_deref()
        .map(discover_session_files_in_home)
        .unwrap_or_default()
}

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

pub fn parse_session_file(candidate: &SessionCandidate) -> Option<AgentSession> {
    let content = fs::read_to_string(&candidate.path).ok()?;
    parse_session_content(
        candidate.agent,
        &candidate.path,
        candidate.updated,
        &content,
    )
}

pub fn parse_session_path(path: &Path) -> Option<AgentSession> {
    let agent = agent_source_for_path(path)?;
    let updated = fs::metadata(path)
        .and_then(|metadata| metadata.modified())
        .unwrap_or(UNIX_EPOCH);
    parse_session_file(&SessionCandidate {
        agent,
        path: path.to_path_buf(),
        updated,
    })
}

pub fn parse_session_content(
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

pub fn normalize_session_log_path(path: &Path) -> PathBuf {
    fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf())
}

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

pub fn fixture_session_path(agent: &str, home: &Path) -> Option<PathBuf> {
    match agent {
        AGENT_CLAUDE => Some(home.join(".claude/projects/test/session.jsonl")),
        AGENT_CODEX => Some(home.join(".codex/sessions/2026/06/02/session.jsonl")),
        AGENT_GEMINI => Some(home.join(".gemini/tmp/test/chats/session-test.json")),
        _ => None,
    }
}

pub fn is_codex_cli_entrypoint(target: Option<&str>) -> bool {
    target.is_some_and(|target| {
        Path::new(target).file_name().and_then(|name| name.to_str()) == Some("codex")
            && !target.contains("/node_modules/")
    })
}

pub fn codex_exec_prompt(command: &str) -> Option<String> {
    let mut args = command.split_once(" exec ")?.1.trim();
    while let Some(rest) = strip_codex_exec_option(args) {
        args = rest.trim_start();
    }
    (!args.starts_with('-'))
        .then(|| args.trim_matches(['"', '\'']))
        .and_then(clean_prompt_text)
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

    for line in content.lines() {
        let Ok(obj) = serde_json::from_str::<Value>(line) else {
            continue;
        };
        if let Some(id) = local_session_id(&obj) {
            acc.session_id = id;
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
                if let Some(items) = obj.pointer("/message/content").and_then(Value::as_array) {
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
                    }
                }
            }
            (AGENT_CLAUDE, "queue-operation") if acc.prompt_preview.is_none() => {
                if obj.get("operation").and_then(Value::as_str) == Some("enqueue")
                    && let Some(text) = obj.get("content").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text);
                }
            }
            (AGENT_CLAUDE, "last-prompt") if acc.prompt_preview.is_none() => {
                if let Some(text) = obj.get("lastPrompt").and_then(Value::as_str)
                    && let Some(text) = clean_prompt_text(text)
                {
                    acc.prompt_preview = Some(text);
                }
            }
            (AGENT_CLAUDE, "user") => {
                if acc.prompt_preview.is_none()
                    && !is_claude_tool_result(&obj)
                    && let Some(text) =
                        local_message_preview(obj.pointer("/message/content").unwrap_or(&obj))
                {
                    acc.prompt_preview = Some(text);
                }
            }
            (AGENT_CODEX, "turn_context") => {
                if let Some(name) = obj.pointer("/payload/model").and_then(Value::as_str) {
                    codex_model = name.to_string();
                    acc.model = Some(name.to_string());
                }
            }
            (AGENT_CODEX, "event_msg") => {
                if obj.pointer("/payload/type").and_then(Value::as_str) == Some("token_count")
                    && let Some(usage) = obj.pointer("/payload/info/total_token_usage")
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
            }
            (AGENT_CODEX, "message" | "input" | "user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text);
                }
            }
            _ if acc.prompt_preview.is_none() && typ.contains("user") => {
                if let Some(text) = local_message_preview(&obj) {
                    acc.prompt_preview = Some(text);
                }
            }
            _ => {}
        }
    }

    if acc.model_usage.is_empty() {
        acc.model_usage = claude_message_models;
    }
    acc.finish()
}

fn parse_gemini_json(path: &Path, updated: SystemTime, content: &str) -> Option<AgentSession> {
    let root: Value = serde_json::from_str(content).ok()?;
    let mut acc = SessionAccumulator::new(AGENT_GEMINI, path, updated);
    if let Some(id) = root.get("sessionId").and_then(Value::as_str) {
        acc.session_id = id.to_string();
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
        return acc.finish();
    };
    for msg in messages {
        if let Some(ts) = msg.get("timestamp").and_then(Value::as_str) {
            acc.last_message_at = Some(ts.to_string());
        }
        match msg.get("type").and_then(Value::as_str) {
            Some("user") if acc.prompt_preview.is_none() => {
                if let Some(text) = local_message_preview(msg.get("content").unwrap_or(msg)) {
                    acc.prompt_preview = Some(text);
                }
            }
            Some("gemini") | Some("assistant") | Some("model") => {
                if let Some(model) = msg.get("model").and_then(Value::as_str) {
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
                    }
                }
            }
            _ => {}
        }
    }
    acc.finish()
}

struct SessionAccumulator {
    agent: String,
    session_id: String,
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
            agent: agent.to_string(),
            session_id,
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
        let display_id = format!("{}:{}", self.agent, short_session_id(&self.session_id));
        Some(AgentSession {
            agent: self.agent,
            session_id: self.session_id,
            display_id,
            path: self.path,
            updated: self.updated,
            start_timestamp_ms: self
                .start_timestamp_ms
                .or_else(|| Some(system_time_ms(self.updated).saturating_sub(self.duration_ms))),
            end_timestamp_ms: self.end_timestamp_ms,
            model: self.model,
            token_usage,
            model_usage: self.model_usage,
            tools: self.tools,
            files: self.files,
            prompt_preview: self.prompt_preview,
            duration_ms: self.duration_ms,
            cwd: self.cwd,
            last_message_at: self.last_message_at,
        })
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ProcessKey {
    pub pid: u32,
    pub starttime_ticks: u64,
}

#[derive(Debug, Clone, Default)]
pub struct ProcessTree {
    pub root: ProcessKey,
    pub members: Vec<ProcessKey>,
}

#[derive(Debug, Clone, Default)]
pub struct LiveProcessCandidate {
    pub tree: ProcessTree,
    pub agent: String,
    pub age_s: Option<f64>,
    pub cwd: Option<String>,
}

#[derive(Debug, Clone)]
pub struct SessionProcessInput {
    pub id: String,
    pub agent: String,
    pub path: PathBuf,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub cwd: Option<String>,
}

#[derive(Debug, Clone)]
pub struct SessionProcessMatch {
    pub session_id: String,
    pub root_pid: u32,
    pub matched_pids: Vec<u32>,
    pub pid_starttime_ticks: u64,
    pub source: &'static str,
    pub confidence: f32,
    pub evidence: &'static str,
}

#[derive(Debug, Default)]
pub struct SessionProcessMatches {
    pub by_session_id: HashMap<String, SessionProcessMatch>,
    pub by_pid: HashMap<u32, String>,
    pub used_root_pids: HashSet<u32>,
}

impl SessionProcessMatches {
    pub fn session_for_pid(&self, pid: u32) -> Option<&SessionProcessMatch> {
        self.by_pid
            .get(&pid)
            .and_then(|session_id| self.by_session_id.get(session_id))
    }
}

#[derive(Default)]
pub struct SessionProcessMatcher {
    bindings: HashMap<u32, LiveSessionBinding>,
}

struct LiveSessionBinding {
    starttime_ticks: u64,
    session_path: PathBuf,
}

impl SessionProcessMatcher {
    pub fn match_sessions(
        &mut self,
        sessions: &[SessionProcessInput],
        processes: &[LiveProcessCandidate],
        fd_paths_by_process: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
        observed_path_by_process: &HashMap<ProcessKey, PathBuf>,
        now_ms: u64,
    ) -> SessionProcessMatches {
        let path_evidence =
            collect_path_evidence(processes, fd_paths_by_process, observed_path_by_process);
        self.retain_live(processes);

        let mut out = SessionProcessMatches::default();
        for session in sessions {
            let Some((process, evidence)) = processes.iter().find_map(|process| {
                if out.used_root_pids.contains(&process.tree.root.pid)
                    || process.agent != session.agent
                    || !session_is_fresh_enough_for_process(session, process, now_ms)
                {
                    return None;
                }
                self.link_trace(&session.path, process, &path_evidence)
                    .map(|evidence| (process, evidence))
            }) else {
                continue;
            };
            record_match(&mut out, session, process, evidence);
        }

        let mut cwd_candidates = Vec::new();
        for (session_index, session) in sessions.iter().enumerate() {
            if out.by_session_id.contains_key(&session.id) {
                continue;
            }
            for (process_index, process) in processes.iter().enumerate() {
                if out.used_root_pids.contains(&process.tree.root.pid)
                    || process.agent != session.agent
                    || !self.can_use_cwd_trace(&session.path, process, &path_evidence)
                {
                    continue;
                }
                let Some(distance_ms) = recent_cwd_distance_ms(session, process, now_ms) else {
                    continue;
                };
                cwd_candidates.push((
                    distance_ms,
                    std::cmp::Reverse(session_end_ms(session)),
                    session_index,
                    process_index,
                ));
            }
        }
        cwd_candidates.sort_unstable();
        for (_, _, session_index, process_index) in cwd_candidates {
            let session = &sessions[session_index];
            let process = &processes[process_index];
            if out.by_session_id.contains_key(&session.id)
                || out.used_root_pids.contains(&process.tree.root.pid)
            {
                continue;
            }
            record_match(&mut out, session, process, TRACE_RECENT_CWD);
        }
        out
    }

    fn retain_live(&mut self, processes: &[LiveProcessCandidate]) {
        self.bindings.retain(|pid, binding| {
            processes.iter().any(|process| {
                process.tree.root.pid == *pid
                    && process.tree.root.starttime_ticks == binding.starttime_ticks
            })
        });
    }

    fn link_trace(
        &mut self,
        session_path: &Path,
        process: &LiveProcessCandidate,
        path_evidence: &HashMap<u32, BTreeMap<PathBuf, &'static str>>,
    ) -> Option<&'static str> {
        let pid = process.tree.root.pid;
        let path = normalize_session_log_path(session_path);
        if let Some(evidence) = path_evidence.get(&pid) {
            if let Some(trace) = evidence.get(&path).copied() {
                self.bindings.insert(
                    pid,
                    LiveSessionBinding {
                        starttime_ticks: process.tree.root.starttime_ticks,
                        session_path: path,
                    },
                );
                return Some(trace);
            }
            self.bindings.remove(&pid);
            return None;
        }
        self.bindings
            .get(&pid)
            .filter(|binding| {
                binding.starttime_ticks == process.tree.root.starttime_ticks
                    && binding.session_path == path
            })
            .map(|_| TRACE_STICKY_BINDING)
    }

    fn can_use_cwd_trace(
        &self,
        session_path: &Path,
        process: &LiveProcessCandidate,
        path_evidence: &HashMap<u32, BTreeMap<PathBuf, &'static str>>,
    ) -> bool {
        let pid = process.tree.root.pid;
        if path_evidence.contains_key(&pid) {
            return false;
        }
        let path = normalize_session_log_path(session_path);
        !self.bindings.get(&pid).is_some_and(|binding| {
            binding.starttime_ticks == process.tree.root.starttime_ticks
                && binding.session_path != path
        })
    }
}

fn record_match(
    out: &mut SessionProcessMatches,
    session: &SessionProcessInput,
    process: &LiveProcessCandidate,
    evidence: &'static str,
) {
    let matched_pids = process
        .tree
        .members
        .iter()
        .map(|key| key.pid)
        .collect::<Vec<_>>();
    out.used_root_pids.insert(process.tree.root.pid);
    for pid in &matched_pids {
        out.by_pid.insert(*pid, session.id.clone());
    }
    out.by_session_id.insert(
        session.id.clone(),
        SessionProcessMatch {
            session_id: session.id.clone(),
            root_pid: process.tree.root.pid,
            matched_pids,
            pid_starttime_ticks: process.tree.root.starttime_ticks,
            source: SOURCE_SESSION_PROCESS_MATCH,
            confidence: confidence_for_evidence(evidence),
            evidence,
        },
    );
}

fn collect_path_evidence(
    processes: &[LiveProcessCandidate],
    fd_paths_by_process: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
    observed_path_by_process: &HashMap<ProcessKey, PathBuf>,
) -> HashMap<u32, BTreeMap<PathBuf, &'static str>> {
    let mut out = HashMap::new();
    for process in processes {
        let mut evidence = BTreeMap::new();
        for key in &process.tree.members {
            if let Some(paths) = fd_paths_by_process.get(key) {
                for path in paths {
                    if let Some(session_path) = session_log_path_from_str(&path.to_string_lossy()) {
                        evidence.entry(session_path).or_insert(TRACE_PROC_FD);
                    }
                }
            }
            if let Some(path) = observed_path_by_process.get(key)
                && let Some(session_path) = session_log_path_from_str(&path.to_string_lossy())
            {
                evidence.insert(session_path, TRACE_EBPF_FILE);
            }
        }
        if !evidence.is_empty() {
            out.insert(process.tree.root.pid, evidence);
        }
    }
    out
}

fn session_is_fresh_enough_for_process(
    session: &SessionProcessInput,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> bool {
    let Some(process_start_ms) = process_start_ms(process, now_ms) else {
        return true;
    };
    session_end_ms(session).saturating_add(SESSION_PROCESS_START_SKEW_MS) >= process_start_ms
}

fn recent_cwd_distance_ms(
    session: &SessionProcessInput,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> Option<u64> {
    let session_cwd = session.cwd.as_deref().filter(|value| !value.is_empty())?;
    let process_cwd = process.cwd.as_deref().filter(|value| !value.is_empty())?;
    if session_cwd != process_cwd {
        return None;
    }
    let process_start_ms = process_start_ms(process, now_ms)?;
    let session_end_ms = session_end_ms(session);
    (session_end_ms.saturating_add(SESSION_PROCESS_START_SKEW_MS) >= process_start_ms)
        .then_some(session_end_ms.abs_diff(process_start_ms))
}

fn process_start_ms(process: &LiveProcessCandidate, now_ms: u64) -> Option<u64> {
    process
        .age_s
        .map(|age_s| now_ms.saturating_sub((age_s.max(0.0) * 1000.0).round() as u64))
}

fn session_end_ms(session: &SessionProcessInput) -> u64 {
    session
        .end_timestamp_ms
        .or(session.start_timestamp_ms)
        .unwrap_or_default()
}

fn confidence_for_evidence(evidence: &str) -> f32 {
    match evidence {
        TRACE_EBPF_FILE => 0.95,
        TRACE_PROC_FD => 0.90,
        TRACE_STICKY_BINDING => 0.70,
        TRACE_RECENT_CWD => 0.55,
        _ => 0.50,
    }
}

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

fn user_home_dir() -> Option<PathBuf> {
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

fn local_session_id(obj: &Value) -> Option<String> {
    for key in ["sessionId", "session_id", "conversation_id"] {
        if let Some(value) = obj.get(key).and_then(Value::as_str)
            && !value.is_empty()
        {
            return Some(value.to_string());
        }
    }
    for pointer in ["/payload/session_id", "/payload/sessionId"] {
        if let Some(value) = obj.pointer(pointer).and_then(Value::as_str)
            && !value.is_empty()
        {
            return Some(value.to_string());
        }
    }
    None
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
