use agent_session::{AgentSession, SessionCandidate};
use anyhow::{Result, anyhow};
use rayon::prelude::*;
use std::path::{Path, PathBuf};

pub type UserRequest = agent_session::UserPrompt;
pub type ToolEvent = agent_session::ToolEvent;
pub type LlmEvent = agent_session::LlmResponse;

pub use agent_session::{
    collapse_project_path, contains_private_marker, path_component_strings, short_hash,
    truncate_clean,
};

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
            .filter_map(|path| agent_session::session_candidate_from_path(path))
            .collect::<Vec<_>>()
    } else {
        discover_configured_roots(codex_root, claude_root)
    };
    sort_candidates(&mut candidates);
    if scan_files > 0 {
        candidates.truncate(scan_files);
    }

    // Parse sessions in parallel
    let project_root_owned = project_root.to_path_buf();
    let parsed: Vec<_> = candidates
        .par_iter()
        .filter_map(|candidate| {
            let summary = agent_session::parse_session_file(candidate)?;
            if !explicit_files && !session_matches_project(&summary, &project_root_owned) {
                return None;
            }
            let mut session = record_from_agent_session(&summary);
            apply_agent_session_fallbacks(&mut session, &summary);
            session.ensure_prompt();
            if session.user_requests.is_empty()
                && session.tools.is_empty()
                && session.llm_calls.is_empty()
            {
                return None;
            }
            Some(session)
        })
        .collect();

    let sessions = if max_sessions > 0 {
        parsed.into_iter().take(max_sessions).collect()
    } else {
        parsed
    };

    Ok(DiscoveryResult {
        sessions,
        warnings: Vec::new(),
    })
}

fn discover_configured_roots(codex_root: &Path, claude_root: &Path) -> Vec<SessionCandidate> {
    let mut discovered = Vec::new();
    discovered.extend(agent_session::discover_session_files_in_dir(
        agent_session::AGENT_CLAUDE,
        claude_root,
    ));
    discovered.extend(agent_session::discover_session_files_in_dir(
        agent_session::AGENT_CODEX,
        codex_root,
    ));
    discovered
}

fn sort_candidates(candidates: &mut [SessionCandidate]) {
    candidates.sort_by_key(|candidate| {
        std::cmp::Reverse(
            candidate
                .updated
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_millis())
                .unwrap_or(0),
        )
    });
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
        user_requests: session.events.prompts.clone(),
        tools: session.events.tools.clone(),
        llm_calls: session.events.llm_responses.clone(),
        session_tag: String::new(),
    }
}

fn apply_agent_session_fallbacks(record: &mut SessionRecord, session: &AgentSession) {
    if record.user_requests.is_empty()
        && let Some(prompt) = session.prompt_preview.as_deref()
    {
        record.user_requests.push(UserRequest {
            index: 0,
            ts_ms: record.start_ts_ms,
            text_hash: short_hash(prompt, 12),
            preview: truncate_clean(prompt, 180),
            tag: String::new(),
        });
    }
    if record.tools.is_empty() {
        for (tool, count) in &session.tools {
            for _ in 0..*count {
                record.tools.push(ToolEvent {
                    ts_ms: record.start_ts_ms,
                    prompt_index: 0,
                    tool_name: tool.clone(),
                    category: agent_session::tool_category(tool, ""),
                    command: String::new(),
                    command_name: "none".to_string(),
                    effect: "process".to_string(),
                    process_chain: Vec::new(),
                    status: "observed".to_string(),
                    path_groups: session
                        .files
                        .keys()
                        .map(|path| agent_session::path_group(path, Path::new(&record.cwd)))
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
                prompt_index: 0,
                model: model.clone(),
                text_hash: short_hash(&format!("{}:{:?}", session.session_id, usage), 12),
                preview: "session token summary".to_string(),
                input_tokens: nonnegative_u64(usage.input_tokens),
                output_tokens: nonnegative_u64(usage.output_tokens),
                cache_tokens: nonnegative_u64(usage.cache_creation_tokens)
                    + nonnegative_u64(usage.cache_read_tokens),
                total_tokens: nonnegative_u64(usage.total_tokens),
                tag: String::new(),
            });
        }
    }
}

fn nonnegative_u64(value: i64) -> u64 {
    u64::try_from(value).unwrap_or(0)
}

pub fn default_claude_root(project_root: &Path) -> Result<PathBuf> {
    let _ = project_root;
    dirs::home_dir()
        .map(|home| home.join(".claude/projects"))
        .ok_or_else(|| anyhow!("cannot determine home directory"))
}
