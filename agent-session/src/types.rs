// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Data types for agent session representation.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fmt;
use std::path::PathBuf;
use std::time::{Duration, Instant, SystemTime};

use crate::parser::{path_group, short_hash};
use crate::{discover_session_files, parse_session_file};

pub const AGENT_TRACE_SCHEMA: &str = "agentsight.agent-session.trace.v1";

/// Token usage statistics for a model or session.
#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct TokenUsage {
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_tokens: i64,
}

impl TokenUsage {
    pub(crate) fn add(
        &mut self,
        input: i64,
        output: i64,
        cache_creation: i64,
        cache_read: i64,
        total: i64,
    ) {
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
pub struct UserPrompt {
    pub index: usize,
    pub ts_ms: Option<i64>,
    pub text_hash: String,
    pub preview: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub tag: String,
    /// Source-visible semantic responsibility path after applying this prompt.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub task_path: Vec<String>,
}

impl UserPrompt {
    pub fn prompt_key(&self) -> String {
        format!("{}:{}", self.index, self.text_hash)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolEvent {
    pub ts_ms: Option<i64>,
    pub prompt_index: usize,
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
    /// Exact nonempty `input.skill` on a source-native Skill tool call.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub invoked_skill: String,
    /// Exact source-recorded skill scope active at this tool invocation.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub skill: String,
    /// Source-visible semantic responsibility path active at this operation.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub task_path: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LlmResponse {
    pub ts_ms: Option<i64>,
    pub prompt_index: usize,
    pub model: String,
    /// Source-native completion identity used to merge split JSONL records.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub source_id: String,
    pub text_hash: String,
    pub preview: String,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_tokens: u64,
    pub total_tokens: u64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub tag: String,
    /// Source-native response lifecycle when the agent records one explicitly.
    /// Examples are `commentary`, `final_answer`, and `assistant_message`.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub response_phase: String,
    /// Exact source-recorded skill scope active when this response began.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub skill: String,
    /// Source-visible semantic responsibility path active at this response.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub task_path: Vec<String>,
}

impl LlmResponse {
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
        if out.is_empty() && (1..=MAX_ESTIMATED_TOKEN_COMPONENT).contains(&self.total_tokens) {
            out.push(("estimate", self.total_tokens));
        }
        if out.is_empty() {
            out.push(("unknown", 1));
        }
        out
    }
}

/// Vendor-neutral interaction events extracted from an agent-native transcript.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SessionEvents {
    pub prompts: Vec<UserPrompt>,
    pub tools: Vec<ToolEvent>,
    pub llm_responses: Vec<LlmResponse>,
}

/// A parsed agent session with metadata, token usage, and tool invocations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSession {
    pub agent_type: String,
    pub session_id: String,
    pub conversation_id: Option<String>,
    pub display_id: String,
    pub path: PathBuf,
    pub updated: SystemTime,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub model: Option<String>,
    pub usage: TokenUsage,
    pub model_usage: BTreeMap<String, TokenUsage>,
    pub tools: BTreeMap<String, usize>,
    pub files: BTreeMap<String, usize>,
    pub prompt_preview: Option<String>,
    pub duration_ms: u64,
    pub cwd: Option<String>,
    pub last_message_at: Option<String>,
    /// Vendor-neutral interaction events extracted from agent-native transcripts.
    #[serde(default)]
    pub events: SessionEvents,
}

/// Portable JSON trace wrapper for exchanging parsed agent sessions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentTrace {
    pub schema: String,
    pub sessions: Vec<AgentSession>,
}

impl AgentTrace {
    pub fn new(sessions: Vec<AgentSession>) -> Self {
        Self {
            schema: AGENT_TRACE_SCHEMA.to_string(),
            sessions,
        }
    }

    /// Build a portable trace with host-local filesystem and tool-command
    /// fields normalized. Parsing a trace with `from_json_str` preserves the
    /// input rather than applying this normalization a second time.
    pub fn portable(sessions: Vec<AgentSession>) -> Self {
        Self {
            schema: AGENT_TRACE_SCHEMA.to_string(),
            sessions: sessions
                .into_iter()
                .map(sanitize_session_for_trace)
                .collect(),
        }
    }

    /// Parse an agent-session trace from JSON text.
    ///
    /// The preferred representation is a schema wrapper with a `sessions`
    /// array. For compatibility with small fixtures and one-off conversion
    /// scripts, this parser also accepts a bare session array or a single
    /// session object and wraps both in the schema object. It preserves session
    /// fields from the input trace.
    pub fn from_json_str(contents: &str) -> Result<Self, AgentTraceError> {
        let value: Value = serde_json::from_str(contents).map_err(AgentTraceError::Json)?;
        if let Some(sessions) = value.get("sessions") {
            let schema = value.get("schema").and_then(Value::as_str);
            if schema != Some(AGENT_TRACE_SCHEMA) {
                return Err(AgentTraceError::UnsupportedSchema(
                    schema.unwrap_or("<missing>").to_string(),
                ));
            }
            let sessions =
                serde_json::from_value(sessions.clone()).map_err(AgentTraceError::Json)?;
            return Ok(Self {
                schema: AGENT_TRACE_SCHEMA.to_string(),
                sessions,
            });
        }
        if value.is_array() {
            let sessions = serde_json::from_value(value).map_err(AgentTraceError::Json)?;
            return Ok(Self {
                schema: AGENT_TRACE_SCHEMA.to_string(),
                sessions,
            });
        }
        if value.is_object() {
            let session = serde_json::from_value(value).map_err(AgentTraceError::Json)?;
            return Ok(Self {
                schema: AGENT_TRACE_SCHEMA.to_string(),
                sessions: vec![session],
            });
        }
        Err(AgentTraceError::InvalidRoot)
    }

    pub fn to_pretty_json(&self) -> Result<String, AgentTraceError> {
        serde_json::to_string_pretty(self).map_err(AgentTraceError::Json)
    }
}

fn sanitize_session_for_trace(mut session: AgentSession) -> AgentSession {
    let original_cwd = session.cwd.clone();
    session.path = trace_session_path(&session);
    if session.cwd.as_deref().is_some_and(|cwd| !cwd.is_empty()) {
        session.cwd = Some("repo".to_string());
    }
    session.files = sanitize_file_counts(&session.files, original_cwd.as_deref());
    session.events.tools = session
        .events
        .tools
        .into_iter()
        .map(sanitize_tool_event_for_trace)
        .collect();
    session
}

fn trace_session_path(session: &AgentSession) -> PathBuf {
    let agent = sanitize_path_component(&session.agent_type, "agent");
    let key = if session.session_id.is_empty() {
        &session.display_id
    } else {
        &session.session_id
    };
    PathBuf::from("trace")
        .join(agent)
        .join(format!("{}.jsonl", short_hash(key, 12)))
}

fn sanitize_path_component(raw: &str, fallback: &str) -> String {
    let value = raw
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || ch == '-' || ch == '_' {
                ch
            } else {
                '-'
            }
        })
        .collect::<String>();
    let value = value.trim_matches('-');
    if value.is_empty() {
        fallback.to_string()
    } else {
        value.to_string()
    }
}

fn sanitize_file_counts(
    files: &BTreeMap<String, usize>,
    original_cwd: Option<&str>,
) -> BTreeMap<String, usize> {
    let project_root = original_cwd
        .filter(|cwd| !cwd.is_empty())
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));
    let mut sanitized = BTreeMap::new();
    for (path, count) in files {
        let group = path_group(path, &project_root);
        if group != "none" {
            *sanitized.entry(group).or_default() += *count;
        }
    }
    sanitized
}

fn sanitize_tool_event_for_trace(mut event: ToolEvent) -> ToolEvent {
    if !event.command_name.is_empty() && event.command_name != "none" {
        event.command = event.command_name.clone();
    } else if !event.tool_name.is_empty() {
        event.command.clear();
    }
    event.path_groups = event
        .path_groups
        .into_iter()
        .filter(|group| !group.is_empty() && group != "none")
        .collect();
    event
}

#[derive(Debug)]
pub enum AgentTraceError {
    Json(serde_json::Error),
    UnsupportedSchema(String),
    InvalidRoot,
}

impl fmt::Display for AgentTraceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Json(err) => write!(f, "{err}"),
            Self::UnsupportedSchema(schema) => {
                write!(f, "unsupported agent trace schema {schema}")
            }
            Self::InvalidRoot => write!(f, "agent trace JSON must be an object or array"),
        }
    }
}

impl std::error::Error for AgentTraceError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Json(err) => Some(err),
            Self::UnsupportedSchema(_) | Self::InvalidRoot => None,
        }
    }
}

/// A candidate session file discovered on disk.
#[derive(Debug, Clone)]
pub struct SessionCandidate {
    pub agent: &'static str,
    pub path: PathBuf,
    pub updated: SystemTime,
}

/// Statistics about a session directory.
#[derive(Debug, Clone)]
pub struct SessionDirStat {
    pub agent: &'static str,
    pub dir: PathBuf,
    pub sessions: usize,
    pub bytes: u64,
}

/// Cache for discovered and parsed sessions.
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::UNIX_EPOCH;

    fn sample_session(id: &str) -> AgentSession {
        AgentSession {
            agent_type: "codex".to_string(),
            session_id: id.to_string(),
            conversation_id: None,
            display_id: id.to_string(),
            path: PathBuf::from("session.jsonl"),
            updated: UNIX_EPOCH,
            start_timestamp_ms: Some(1),
            end_timestamp_ms: Some(2),
            model: Some("model".to_string()),
            usage: TokenUsage::default(),
            model_usage: BTreeMap::new(),
            tools: BTreeMap::new(),
            files: BTreeMap::new(),
            prompt_preview: Some("hello".to_string()),
            duration_ms: 1,
            cwd: Some("/repo".to_string()),
            last_message_at: None,
            events: SessionEvents::default(),
        }
    }

    #[test]
    fn agent_trace_round_trips_schema_wrapper() {
        let trace = AgentTrace::new(vec![sample_session("s1")]);
        let payload = trace.to_pretty_json().unwrap();
        let parsed = AgentTrace::from_json_str(&payload).unwrap();

        assert_eq!(parsed.schema, AGENT_TRACE_SCHEMA);
        assert_eq!(parsed.sessions.len(), 1);
        assert_eq!(parsed.sessions[0].session_id, "s1");
    }

    #[test]
    fn agent_trace_accepts_bare_session_array_and_single_session() {
        let sessions = vec![sample_session("s1"), sample_session("s2")];
        let array_payload = serde_json::to_string(&sessions).unwrap();
        let single_payload = serde_json::to_string(&sessions[0]).unwrap();

        let parsed_array = AgentTrace::from_json_str(&array_payload).unwrap();
        let parsed_single = AgentTrace::from_json_str(&single_payload).unwrap();

        assert_eq!(parsed_array.sessions.len(), 2);
        assert_eq!(parsed_single.sessions.len(), 1);
        assert_eq!(parsed_single.sessions[0].session_id, "s1");
    }

    #[test]
    fn agent_trace_rejects_wrong_schema() {
        let payload = r#"{"schema":"agentsight.agent-session.trace.v0","sessions":[]}"#;
        let err = AgentTrace::from_json_str(payload).unwrap_err().to_string();

        assert!(err.contains("unsupported agent trace schema"));
    }

    #[test]
    fn agent_trace_parse_preserves_input_fields() {
        let mut session = sample_session("s1");
        session.path = PathBuf::from("/home/alice/.codex/sessions/s1.jsonl");
        session.cwd = Some("/home/alice/work/agentsight".to_string());
        session
            .files
            .insert("/home/alice/private/secret.txt".to_string(), 1);
        session.events.tools.push(ToolEvent {
            ts_ms: Some(1),
            prompt_index: 0,
            tool_name: "bash".to_string(),
            category: "shell".to_string(),
            command: "git status --short".to_string(),
            command_name: "git".to_string(),
            effect: "repo".to_string(),
            process_chain: vec!["git".to_string()],
            status: "ok".to_string(),
            path_groups: Vec::new(),
            domains: Vec::new(),
            call_id: None,
            invoked_skill: String::new(),
            skill: String::new(),
            task_path: Vec::new(),
        });

        let payload = AgentTrace::new(vec![session]).to_pretty_json().unwrap();
        let parsed = AgentTrace::from_json_str(&payload).unwrap();
        let imported = &parsed.sessions[0];

        assert_eq!(
            imported.path,
            PathBuf::from("/home/alice/.codex/sessions/s1.jsonl")
        );
        assert_eq!(imported.cwd.as_deref(), Some("/home/alice/work/agentsight"));
        assert_eq!(
            imported.files.get("/home/alice/private/secret.txt"),
            Some(&1)
        );
        assert_eq!(imported.events.tools[0].command, "git status --short");
    }

    #[test]
    fn portable_agent_trace_sanitizes_host_paths() {
        let mut session = sample_session("s1");
        session.path = PathBuf::from("/home/alice/.codex/sessions/s1.jsonl");
        session.cwd = Some("/home/alice/work/agentsight".to_string());
        session.files.insert(
            "/home/alice/work/agentsight/collector/src/main.rs".to_string(),
            2,
        );
        session
            .files
            .insert("/home/alice/private/secret.txt".to_string(), 1);
        session.events.tools.push(ToolEvent {
            ts_ms: Some(1),
            prompt_index: 0,
            tool_name: "bash".to_string(),
            category: "shell".to_string(),
            command: "cat /home/alice/private/secret.txt".to_string(),
            command_name: "cat".to_string(),
            effect: "read".to_string(),
            process_chain: vec!["cat".to_string()],
            status: "ok".to_string(),
            path_groups: vec![
                "collector/src/main.rs".to_string(),
                "external/home".to_string(),
            ],
            domains: Vec::new(),
            call_id: None,
            invoked_skill: String::new(),
            skill: String::new(),
            task_path: Vec::new(),
        });

        let payload = AgentTrace::portable(vec![session])
            .to_pretty_json()
            .unwrap();
        assert!(!payload.contains("/home/alice"));
        assert!(!payload.contains("secret.txt"));

        let parsed = AgentTrace::from_json_str(&payload).unwrap();
        let exported = &parsed.sessions[0];
        assert_eq!(
            exported.path,
            PathBuf::from("trace/codex/e8bc163c82ee.jsonl")
        );
        assert_eq!(exported.cwd.as_deref(), Some("repo"));
        assert_eq!(exported.files.get("collector/src/main.rs"), Some(&2));
        assert_eq!(exported.files.get("external/home"), Some(&1));
        assert_eq!(exported.events.tools[0].command, "cat");
    }
}
