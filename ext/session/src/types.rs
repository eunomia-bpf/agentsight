// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Data types for agent session representation.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};

use crate::{discover_session_files, parse_session_file};

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
    /// Full source-visible prompt text for the authorized session detail API.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub text: String,
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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ToolPath {
    /// Path as recorded by the native agent. Consumers resolve relative paths
    /// against the session cwd and must reject paths outside their scope.
    pub path: String,
    /// One of read, write, create, delete, rename_from, or rename.
    pub access: String,
    /// Source path for a rename. Kept on the destination so one tool event can
    /// carry several independent rename pairs without positional guessing.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub previous_path: Option<String>,
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
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub paths: Vec<ToolPath>,
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
    /// Full source-visible response text for the authorized session detail API.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub text: String,
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

/// Latest source-recorded coding plan entry.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PlanStep {
    pub step: String,
    pub status: String,
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
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub plan: Vec<PlanStep>,
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
    last_excluded_agents: Vec<String>,
}

struct CacheEntry {
    mtime: SystemTime,
    session: Option<AgentSession>,
    pinned: bool,
}

impl SessionCache {
    pub fn new() -> Self {
        Self::default()
    }

    /// Parse one known transcript without widening the bounded discovery scan.
    /// The parsed session is reused until the file's modification time changes.
    pub fn parse_path_cached(&mut self, path: &Path) -> Option<AgentSession> {
        let Some(candidate) = crate::session_candidate_from_path(path) else {
            self.entries.remove(path);
            return None;
        };
        if let Some(entry) = self.entries.get_mut(path)
            && entry.mtime == candidate.updated
        {
            entry.pinned = true;
            let session = entry.session.clone();
            self.trim_pinned_details();
            return session;
        }
        let parsed = parse_session_file(&candidate);
        self.entries.insert(
            path.to_path_buf(),
            CacheEntry {
                mtime: candidate.updated,
                session: parsed.clone(),
                pinned: true,
            },
        );
        self.trim_pinned_details();
        parsed
    }

    fn trim_pinned_details(&mut self) {
        const MAX_PINNED_DETAILS: usize = 8;
        let mut pinned = self
            .entries
            .iter()
            .filter(|(_, entry)| entry.pinned)
            .map(|(path, entry)| (path.clone(), entry.mtime))
            .collect::<Vec<_>>();
        if pinned.len() <= MAX_PINNED_DETAILS {
            return;
        }
        let overflow = pinned.len() - MAX_PINNED_DETAILS;
        pinned.sort_by_key(|(_, mtime)| *mtime);
        for (path, _) in pinned.into_iter().take(overflow) {
            self.entries.remove(&path);
        }
    }

    pub fn discover_cached(&mut self, limit: usize, max_age: Duration) -> Vec<AgentSession> {
        self.discover_cached_excluding(limit, max_age, &[])
    }

    pub fn discover_cached_excluding(
        &mut self,
        limit: usize,
        max_age: Duration,
        excluded_agents: &[&str],
    ) -> Vec<AgentSession> {
        let target = limit.clamp(1, 25);
        let mut excluded_agents = excluded_agents
            .iter()
            .map(|agent| (*agent).to_string())
            .collect::<Vec<_>>();
        excluded_agents.sort();
        if self.last_limit < target
            || self.last_excluded_agents != excluded_agents
            || self
                .last_refresh
                .is_none_or(|last| last.elapsed() >= max_age)
        {
            self.refresh(target, &excluded_agents);
        }
        self.cached_sessions.iter().take(target).cloned().collect()
    }

    fn refresh(&mut self, limit: usize, excluded_agents: &[String]) {
        let mut candidates = discover_session_files();
        candidates
            .retain(|candidate| !excluded_agents.iter().any(|agent| agent == candidate.agent));
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
                            pinned: false,
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
        self.entries
            .retain(|path, entry| live_paths.contains(path) || (entry.pinned && path.is_file()));
        self.cached_sessions = sessions;
        self.last_refresh = Some(Instant::now());
        self.last_limit = target;
        self.last_excluded_agents = excluded_agents.to_vec();
    }
}
