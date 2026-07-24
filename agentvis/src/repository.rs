// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-scoped file actions from native coding-agent sessions.

use agent_session::{
    AGENT_CLAUDE, AGENT_CODEX, AGENT_GEMINI, AgentSession, SessionCandidate, ToolPath,
    discover_session_files, parse_session_content, session_candidate_from_path,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::io::{self, BufRead, BufReader, Read};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Debug, Clone)]
pub struct RepositoryTraceOptions {
    pub repo: PathBuf,
    pub global: bool,
    /// Optional research cutoff; product callers leave this unset.
    pub end_ms: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryTrace {
    pub repository: String,
    pub revision: String,
    pub start_ms: i64,
    pub end_ms: i64,
    pub global: bool,
    pub worktree_count: usize,
    pub candidate_session_count: usize,
    pub parsed_session_count: usize,
    pub session_count: usize,
    pub candidate_sessions_by_vendor: BTreeMap<String, usize>,
    pub parsed_sessions_by_vendor: BTreeMap<String, usize>,
    pub included_sessions_by_vendor: BTreeMap<String, usize>,
    pub source_event_count: usize,
    pub file_action_count: usize,
    pub events: Vec<RepositoryEvent>,
    pub commits_ms: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryEvent {
    pub id: String,
    /// Native transcript file retained so diagnostic evidence can be inspected
    /// without searching every local Agent history.
    #[serde(default)]
    pub source_file: String,
    /// Native tool-call identifier retained for source-evidence citations.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_call_id: Option<String>,
    /// Stable identity of the native root session. Subagent streams that share
    /// a native session id remain one independent longitudinal unit.
    pub native_session_id: String,
    /// Stable identity of the source transcript file/stream.
    pub source_stream_id: String,
    /// Tool-call appearance order within the source transcript.
    #[serde(default)]
    pub source_tool_ordinal: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_role: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_agent_id: Option<String>,
    pub session_id: String,
    /// Production-derived ordering of native root sessions.
    #[serde(default)]
    pub session_ordinal: usize,
    pub vendor: String,
    /// True when the native session itself belongs to this repository/worktree.
    /// False means `--global` admitted the Tool call through an exact path
    /// reference from a session rooted elsewhere.
    #[serde(default)]
    pub workspace_session: bool,
    pub ts_ms: i64,
    pub prompt_index: usize,
    /// Exact native user-prompt preview associated by `agent-session` with
    /// this Tool call. Kept as context for Agent readers; no semantic label is
    /// inferred here.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub prompt_preview: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_event_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_event_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub attribution_skill: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub attribution_agent: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub skill_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub skill_args: Option<String>,
    /// Worktree containing the Tool-level workdir/cwd, when resolvable.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub worktree_id: Option<String>,
    pub tool_name: String,
    pub category: String,
    /// Source-native command or Tool input display. Diagnostics may show this
    /// as evidence; measurements use normalized effects and file actions.
    #[serde(default)]
    pub command: String,
    pub command_name: String,
    /// Adapter-derived command effect such as read, write, test, or process.
    pub effect: String,
    pub status: String,
    /// Original source paths before repository scoping. Research analyses use
    /// these to distinguish instruction files from repository artifacts.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub source_paths: Vec<ToolPath>,
    pub actions: Vec<FileAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct FileAction {
    /// Stable, non-reversible identifier of the canonical Git worktree root.
    pub worktree_id: String,
    pub path: String,
    pub access: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub previous_path: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub previous_worktree_id: Option<String>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub scope: bool,
    /// Canonical order within one Tool call.
    #[serde(default)]
    pub action_ordinal: usize,
    /// Production-derived artifact generation identity.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub artifact_id: String,
}

fn is_false(value: &bool) -> bool {
    !*value
}

pub fn build_repository_trace(options: &RepositoryTraceOptions) -> io::Result<RepositoryTrace> {
    let repo = repository_root(&options.repo)?;
    let roots = worktree_roots(&repo);
    let mut candidates = discover_session_files()
        .into_iter()
        .filter(|candidate| candidate_may_match_repo(candidate, &roots))
        .collect::<Vec<_>>();
    candidates.sort_by(|left, right| left.path.cmp(&right.path));
    let candidate_sessions_by_vendor = count_candidates_by_vendor(&candidates);
    let parsed = parse_candidates(&candidates);
    let parsed_sessions_by_vendor = count_sessions_by_vendor(&parsed);
    let parsed_session_count = parsed.len();
    let (mut events, source_event_count) =
        scan_sessions(&candidates, parsed, &roots, options.global)?;
    deduplicate_native_tool_calls(&mut events);
    if let Some(end_ms) = options.end_ms {
        events.retain(|event| event.ts_ms <= end_ms);
    }
    annotate_directory_scopes(&mut events);
    events.sort_by(|left, right| {
        (
            left.ts_ms,
            &left.source_stream_id,
            left.source_tool_ordinal,
            &left.id,
        )
            .cmp(&(
                right.ts_ms,
                &right.source_stream_id,
                right.source_tool_ordinal,
                &right.id,
            ))
    });
    annotate_session_ordinals(&mut events);
    annotate_artifact_ids(&mut events);
    let session_count = events
        .iter()
        .map(|event| &event.native_session_id)
        .collect::<HashSet<_>>()
        .len();
    let included_sessions_by_vendor = count_included_sessions_by_vendor(&events);
    let mut commits_ms = git_lines(&repo, &["log", "--all", "--format=%ct"])?
        .into_iter()
        .filter_map(|value| value.parse::<i64>().ok().map(|seconds| seconds * 1_000))
        .collect::<Vec<_>>();
    if let Some(end_ms) = options.end_ms {
        commits_ms.retain(|timestamp| *timestamp <= end_ms);
    }
    commits_ms.sort_unstable();
    commits_ms.dedup();
    let start_ms = events.first().map_or(0, |event| event.ts_ms);
    let end_ms = events.last().map_or(start_ms, |event| event.ts_ms);
    let file_action_count = events.iter().map(|event| event.actions.len()).sum();
    Ok(RepositoryTrace {
        repository: repo
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("repository")
            .into(),
        revision: git_text(&repo, &["rev-parse", "HEAD"])?.trim().into(),
        start_ms,
        end_ms,
        global: options.global,
        worktree_count: roots.len(),
        candidate_session_count: candidates.len(),
        parsed_session_count,
        session_count,
        candidate_sessions_by_vendor,
        parsed_sessions_by_vendor,
        included_sessions_by_vendor,
        source_event_count,
        file_action_count,
        events,
        commits_ms,
    })
}

fn scan_sessions(
    candidates: &[SessionCandidate],
    parsed: Vec<(AgentSession, usize)>,
    roots: &[PathBuf],
    global: bool,
) -> io::Result<(Vec<RepositoryEvent>, usize)> {
    let mut result = (Vec::new(), 0usize);
    for (session, source_count) in parsed {
        append_session(&session, source_count, roots, true, &mut result);
    }
    if global {
        let direct = candidates
            .iter()
            .map(|row| row.path.clone())
            .collect::<HashSet<_>>();
        for (session, source_count) in behavior_sessions(roots, &direct)? {
            append_session(&session, source_count, roots, false, &mut result);
        }
    }
    Ok(result)
}

/// Native Agent histories may retain several physical transcript files for one
/// logical root session (for example, a continued Codex rollout copied into a
/// later archive).  A Tool call is one observation even when that observation
/// occurs in several of those files.
///
/// Prefer source-native call/event identifiers.  The fallback deliberately
/// includes the timestamp, command, and normalized source paths: it removes
/// byte-equivalent transcript copies without collapsing two ordinary repeated
/// commands in the same native session.
fn deduplicate_native_tool_calls(events: &mut Vec<RepositoryEvent>) {
    let mut unique = BTreeMap::<String, RepositoryEvent>::new();
    for mut event in std::mem::take(events) {
        let identity = native_tool_identity(&event);
        event.id = stable_identity("tool", &identity);
        match unique.entry(identity) {
            std::collections::btree_map::Entry::Vacant(entry) => {
                entry.insert(event);
            }
            std::collections::btree_map::Entry::Occupied(mut entry) => {
                merge_duplicate_event(entry.get_mut(), event);
            }
        }
    }
    *events = unique.into_values().collect();
}

fn native_tool_identity(event: &RepositoryEvent) -> String {
    let mut identity = format!("{}\u{1f}", event.native_session_id);
    let has_native_id = if let Some(call_id) = event
        .source_call_id
        .as_deref()
        .filter(|value| !value.is_empty())
    {
        identity.push_str("call\u{1f}");
        identity.push_str(call_id);
        true
    } else if let Some(source_event_id) = event
        .source_event_id
        .as_deref()
        .filter(|value| !value.is_empty())
    {
        identity.push_str("event\u{1f}");
        identity.push_str(source_event_id);
        true
    } else {
        identity.push_str("fallback");
        false
    };

    // Keep a source-native ID collision from merging two different subagent
    // calls. A continued/archive copy can rewrite its envelope timestamp, so a
    // native ID is joined with the Agent stream and command, not the timestamp.
    // Status and extracted actions are omitted because a later copy can contain
    // the completed result and richer paths.
    for field in [
        event.source_agent_id.as_deref().unwrap_or_default(),
        &event.tool_name,
        &event.command,
    ] {
        identity.push('\u{1f}');
        identity.push_str(field);
    }
    if !has_native_id {
        identity.push('\u{1f}');
        identity.push_str(&event.ts_ms.to_string());
        for path in &event.source_paths {
            identity.push('\u{1e}');
            identity.push_str(&path.path);
            identity.push('\u{1f}');
            identity.push_str(&path.access);
            identity.push('\u{1f}');
            identity.push_str(path.previous_path.as_deref().unwrap_or_default());
        }
    }
    identity
}

fn stable_identity(namespace: &str, identity: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(namespace.as_bytes());
    digest.update([0]);
    digest.update(identity.as_bytes());
    hex::encode(digest.finalize())[..16].to_string()
}

fn merge_duplicate_event(existing: &mut RepositoryEvent, duplicate: RepositoryEvent) {
    existing.workspace_session |= duplicate.workspace_session;
    if duplicate_event_score(&duplicate) > duplicate_event_score(existing) {
        let workspace_session = existing.workspace_session;
        let mut preferred = duplicate;
        preferred.workspace_session = workspace_session;
        std::mem::swap(existing, &mut preferred);
        merge_duplicate_event(existing, preferred);
        return;
    }

    if existing.prompt_preview.is_empty() {
        existing.prompt_preview = duplicate.prompt_preview;
    }
    if existing.model.is_none() {
        existing.model = duplicate.model;
    }
    if existing.worktree_id.is_none() {
        existing.worktree_id = duplicate.worktree_id;
    }
    if existing.attribution_skill.is_none() {
        existing.attribution_skill = duplicate.attribution_skill;
    }
    if existing.attribution_agent.is_none() {
        existing.attribution_agent = duplicate.attribution_agent;
    }
    if existing.skill_name.is_none() {
        existing.skill_name = duplicate.skill_name;
    }
    if existing.skill_args.is_none() {
        existing.skill_args = duplicate.skill_args;
    }
    for path in duplicate.source_paths {
        if !existing.source_paths.contains(&path) {
            existing.source_paths.push(path);
        }
    }
    for action in duplicate.actions {
        if !existing.actions.iter().any(|current| {
            current.worktree_id == action.worktree_id
                && current.path == action.path
                && current.access == action.access
                && current.previous_path == action.previous_path
                && current.previous_worktree_id == action.previous_worktree_id
        }) {
            existing.actions.push(action);
        }
    }
    existing
        .actions
        .sort_by(|left, right| action_order_key(left).cmp(&action_order_key(right)));
    for (ordinal, action) in existing.actions.iter_mut().enumerate() {
        action.action_ordinal = ordinal;
    }
}

fn duplicate_event_score(event: &RepositoryEvent) -> usize {
    usize::from(event.status != "unknown") * 100
        + event.actions.len() * 10
        + usize::from(!event.prompt_preview.is_empty()) * 4
        + usize::from(event.model.is_some()) * 2
        + usize::from(event.workspace_session)
}

fn parse_candidates(candidates: &[SessionCandidate]) -> Vec<(AgentSession, usize)> {
    if candidates.is_empty() {
        return Vec::new();
    }
    let workers = std::thread::available_parallelism()
        .map_or(1, usize::from)
        .min(candidates.len());
    let chunk_size = candidates.len().div_ceil(workers);
    std::thread::scope(|scope| {
        let handles = candidates
            .chunks(chunk_size)
            .map(|chunk| {
                scope.spawn(move || {
                    chunk
                        .iter()
                        .filter_map(repository_session)
                        .collect::<Vec<_>>()
                })
            })
            .collect::<Vec<_>>();
        handles
            .into_iter()
            .flat_map(|handle| handle.join().unwrap_or_default())
            .collect()
    })
}

fn count_candidates_by_vendor(candidates: &[SessionCandidate]) -> BTreeMap<String, usize> {
    let mut counts = BTreeMap::new();
    for candidate in candidates {
        *counts.entry(candidate.agent.to_string()).or_default() += 1;
    }
    counts
}

fn count_sessions_by_vendor(sessions: &[(AgentSession, usize)]) -> BTreeMap<String, usize> {
    let mut counts = BTreeMap::new();
    for (session, _) in sessions {
        *counts.entry(session.agent_type.clone()).or_default() += 1;
    }
    counts
}

fn count_included_sessions_by_vendor(events: &[RepositoryEvent]) -> BTreeMap<String, usize> {
    let mut sessions = BTreeMap::<String, BTreeSet<String>>::new();
    for event in events {
        sessions
            .entry(event.vendor.clone())
            .or_default()
            .insert(event.native_session_id.clone());
    }
    sessions
        .into_iter()
        .map(|(vendor, sessions)| (vendor, sessions.len()))
        .collect()
}

fn repository_session(candidate: &SessionCandidate) -> Option<(AgentSession, usize)> {
    if candidate.agent == AGENT_GEMINI {
        let content = std::fs::read_to_string(&candidate.path).ok()?;
        let session = parse_session_content(
            candidate.agent,
            &candidate.path,
            candidate.updated,
            &content,
        )?;
        let count = session.events.tools.len() + session.events.llm_responses.len();
        return Some((session, count));
    }
    let mut reader = BufReader::new(std::fs::File::open(&candidate.path).ok()?);
    let mut line = String::new();
    let mut content = String::new();
    let mut llm_count = 0;
    let mut have_context = false;
    while reader.read_line(&mut line).ok()? > 0 {
        let kind = |value| json_type(&line, value);
        let assistant = kind("assistant");
        let response = kind("response_item");
        let context = kind("session_meta") || (!have_context && kind("turn_context"));
        let tool = (assistant && line.contains(r#""tool_use""#))
            || (response && (kind("function_call") || kind("custom_tool_call")));
        let result = (kind("user") && line.contains(r#""tool_result""#))
            || (response && (kind("function_call_output") || kind("custom_tool_call_output")));
        let prompt = (kind("user") && !line.contains(r#""tool_result""#))
            || (kind("event_msg") && line.contains(r#""user_message""#))
            || kind("queue-operation")
            || kind("last-prompt")
            || kind("message")
            || kind("input");
        llm_count +=
            usize::from(assistant || kind("agent_message") || (response && kind("message")));
        if context || tool || result || prompt {
            content.push_str(&line);
            have_context |= kind("turn_context");
        }
        line.clear();
    }
    let session = parse_session_content(
        candidate.agent,
        &candidate.path,
        candidate.updated,
        &content,
    )?;
    let count = session.events.tools.len() + llm_count;
    Some((session, count))
}

fn json_type(line: &str, value: &str) -> bool {
    line.match_indices(value).any(|(index, _)| {
        let prefix = &line[..index];
        let suffix = &line[index + value.len()..];
        (prefix.ends_with(r#""type":""#) || prefix.ends_with(r#""type": ""#))
            && suffix.starts_with('"')
    })
}

fn append_session(
    session: &AgentSession,
    source_count: usize,
    roots: &[PathBuf],
    repository_session: bool,
    batch: &mut (Vec<RepositoryEvent>, usize),
) {
    let cwd = session
        .cwd
        .as_deref()
        .map(PathBuf::from)
        .or_else(|| {
            repository_session
                .then(|| claude_project_name(&session.path))
                .flatten()
                .and_then(|project| {
                    roots
                        .iter()
                        .find(|root| encoded_claude_root(root) == project)
                        .cloned()
                })
        })
        .or_else(|| {
            gemini_project_hash(&session.path).and_then(|project| {
                roots
                    .iter()
                    .find(|root| repository_hash(root) == project)
                    .cloned()
            })
        });
    let native_session_id = format!("{}:{}", session.agent_type, session.session_id);
    let source_stem = session
        .path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or(&session.session_id);
    let source_stream_id = source_stream_id(&session.agent_type, &session.session_id, source_stem);
    let mut used = false;
    for (ordinal, tool) in session.events.tools.iter().enumerate() {
        let Some(ts_ms) = tool.ts_ms else { continue };
        if is_standalone_workspace_diagnose_command(&tool.command) {
            continue;
        }
        let explicit_cwd = effective_tool_cwd(cwd.as_deref(), tool.workdir.as_deref());
        let (tool_cwd, require_literal_absolute_path, rebase_preabsolutized_path) =
            match inline_shell_cwd(&tool.command, explicit_cwd.as_deref()) {
                InlineShellCwd::Absent => (explicit_cwd.clone(), false, false),
                InlineShellCwd::Known(path) => (Some(path), false, true),
                // A dynamic leading `cd "$tmpdir"` is evidence that the explicit
                // session cwd is no longer valid, but not enough evidence to
                // resolve relative operands. Only absolute operands literally
                // present in the shell command remain admissible.
                InlineShellCwd::Unknown => (None, true, false),
            };
        let event_worktree_id = tool_cwd
            .as_deref()
            .and_then(|path| relative_to_roots(path, roots))
            .map(|path| path.worktree_id);
        let mut actions = tool
            .paths
            .iter()
            .filter_map(|item| {
                if require_literal_absolute_path
                    && (!Path::new(&item.path).is_absolute() || !tool.command.contains(&item.path))
                {
                    return None;
                }
                let path = resolve_tool_path(
                    &item.path,
                    cwd.as_deref(),
                    explicit_cwd.as_deref(),
                    tool_cwd.as_deref(),
                    &tool.command,
                    rebase_preabsolutized_path,
                    roots,
                )?;
                Some(FileAction {
                    worktree_id: path.worktree_id,
                    path: path.path,
                    access: item.access.clone(),
                    previous_worktree_id: item
                        .previous_path
                        .as_deref()
                        .and_then(|value| {
                            resolve_tool_path(
                                value,
                                cwd.as_deref(),
                                explicit_cwd.as_deref(),
                                tool_cwd.as_deref(),
                                &tool.command,
                                rebase_preabsolutized_path,
                                roots,
                            )
                        })
                        .map(|value| value.worktree_id),
                    previous_path: item
                        .previous_path
                        .as_deref()
                        .and_then(|value| {
                            resolve_tool_path(
                                value,
                                cwd.as_deref(),
                                explicit_cwd.as_deref(),
                                tool_cwd.as_deref(),
                                &tool.command,
                                rebase_preabsolutized_path,
                                roots,
                            )
                        })
                        .map(|value| value.path),
                    scope: false,
                    action_ordinal: 0,
                    artifact_id: String::new(),
                })
            })
            .collect::<Vec<_>>();
        actions.sort_by(|left, right| action_order_key(left).cmp(&action_order_key(right)));
        actions.dedup_by(|left, right| {
            left.worktree_id == right.worktree_id
                && left.path == right.path
                && left.access == right.access
                && left.previous_path == right.previous_path
                && left.previous_worktree_id == right.previous_worktree_id
        });
        for (action_ordinal, action) in actions.iter_mut().enumerate() {
            action.action_ordinal = action_ordinal;
        }
        if !repository_session && actions.is_empty() {
            continue;
        }
        used = true;
        batch.0.push(RepositoryEvent {
            id: format!("{source_stream_id}:{ordinal}"),
            source_file: session.path.to_string_lossy().into_owned(),
            source_call_id: tool.call_id.clone(),
            native_session_id: native_session_id.clone(),
            source_stream_id: source_stream_id.clone(),
            source_tool_ordinal: ordinal,
            source_role: session.source_role.clone(),
            source_agent_id: session.source_agent_id.clone(),
            session_id: native_session_id.clone(),
            session_ordinal: 0,
            vendor: session.agent_type.clone(),
            workspace_session: repository_session,
            ts_ms,
            prompt_index: tool.prompt_index,
            prompt_preview: tool
                .prompt_index
                .checked_sub(1)
                .and_then(|index| session.events.prompts.get(index))
                .map_or_else(String::new, |prompt| prompt.preview.clone()),
            source_event_id: tool.source_event_id.clone(),
            parent_event_id: tool.parent_event_id.clone(),
            model: tool.model.clone().or_else(|| session.model.clone()),
            attribution_skill: tool.attribution_skill.clone(),
            attribution_agent: tool.attribution_agent.clone(),
            skill_name: tool.skill_name.clone(),
            skill_args: tool.skill_args.clone(),
            worktree_id: event_worktree_id,
            tool_name: tool.tool_name.clone(),
            category: tool.category.clone(),
            command: tool.command.clone(),
            command_name: tool.command_name.clone(),
            effect: tool.effect.clone(),
            status: tool.status.clone(),
            source_paths: tool.paths.clone(),
            actions,
        });
    }
    if used {
        batch.1 += source_count;
    }
}

fn is_standalone_workspace_diagnose_command(command: &str) -> bool {
    let clauses = command
        .split("&&")
        .flat_map(|part| part.split([';', '\n']))
        .map(str::trim)
        .filter(|clause| {
            !clause.is_empty() && !clause.starts_with("set ") && !shell_assignment_clause(clause)
        })
        .collect::<Vec<_>>();
    !clauses.is_empty()
        && clauses.into_iter().all(|clause| {
            let words = clause
                .split_whitespace()
                .map(|word| word.trim_matches(['\'', '"']))
                .collect::<Vec<_>>();
            let position = usize::from(words.first().is_some_and(|word| *word == "sudo"));
            words.get(position + 1) == Some(&"diagnose")
                && words
                    .get(position)
                    .and_then(|word| word.rsplit('/').next())
                    .is_some_and(|binary| binary == "agentvis" || binary == "agentsight")
        })
}

fn action_order_key(action: &FileAction) -> (u8, &str, &str, &str) {
    let priority = match action.access.as_str() {
        "rename_from" => 0,
        "rename" => 1,
        _ => 2,
    };
    (
        priority,
        action.path.as_str(),
        action.access.as_str(),
        action.previous_path.as_deref().unwrap_or(""),
    )
}

#[derive(Debug, PartialEq, Eq)]
enum InlineShellCwd {
    Absent,
    Known(PathBuf),
    Unknown,
}

fn inline_shell_cwd(command: &str, current: Option<&Path>) -> InlineShellCwd {
    let clauses = command
        .split("&&")
        .flat_map(|part| part.split([';', '\n']))
        .map(str::trim)
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();
    let mut resolved = None;
    let mut prior_command = false;
    for clause in clauses {
        if clause.starts_with("set ") || shell_assignment_clause(clause) {
            continue;
        }
        if clause == "popd" || clause.starts_with("popd ") || clause.starts_with("pushd ") {
            return InlineShellCwd::Unknown;
        }
        let Some(target) = clause.strip_prefix("cd ") else {
            prior_command = true;
            continue;
        };
        if prior_command || resolved.is_some() {
            // One Tool call crossed cwd boundaries. ToolPath currently has no
            // per-shell-segment ownership, so resolving every relative operand
            // against either side would fabricate at least one association.
            return InlineShellCwd::Unknown;
        }
        let Some(target) = shell_word(target.trim()) else {
            return InlineShellCwd::Unknown;
        };
        if target.contains('$') || target.contains('`') || target == "-" {
            return InlineShellCwd::Unknown;
        }
        let target = if target == "~" {
            let Some(home) = dirs::home_dir() else {
                return InlineShellCwd::Unknown;
            };
            home
        } else if let Some(suffix) = target.strip_prefix("~/") {
            let Some(home) = dirs::home_dir() else {
                return InlineShellCwd::Unknown;
            };
            home.join(suffix)
        } else {
            PathBuf::from(target)
        };
        resolved = Some(if target.is_absolute() {
            lexical(&target)
        } else {
            let Some(current) = current else {
                return InlineShellCwd::Unknown;
            };
            lexical(&current.join(target))
        });
    }
    resolved.map_or(InlineShellCwd::Absent, InlineShellCwd::Known)
}

fn shell_assignment_clause(clause: &str) -> bool {
    let Some((name, _)) = clause.split_once('=') else {
        return false;
    };
    !name.is_empty()
        && name.chars().enumerate().all(|(index, ch)| {
            ch == '_' || ch.is_ascii_alphabetic() || (index > 0 && ch.is_ascii_digit())
        })
}

fn shell_word(value: &str) -> Option<&str> {
    let value = value.trim_start();
    let first = value.as_bytes().first().copied()?;
    if first == b'\'' || first == b'"' {
        let quote = first as char;
        let rest = &value[1..];
        let end = rest.find(quote)?;
        Some(&rest[..end])
    } else {
        value.split_whitespace().next()
    }
}

fn annotate_session_ordinals(events: &mut [RepositoryEvent]) {
    let mut first = BTreeMap::<String, i64>::new();
    for event in events.iter() {
        first
            .entry(event.native_session_id.clone())
            .and_modify(|value| *value = (*value).min(event.ts_ms))
            .or_insert(event.ts_ms);
    }
    let mut sessions = first.into_iter().collect::<Vec<_>>();
    sessions.sort_by(|left, right| (left.1, &left.0).cmp(&(right.1, &right.0)));
    let ordinals = sessions
        .into_iter()
        .enumerate()
        .map(|(ordinal, (session, _))| (session, ordinal))
        .collect::<HashMap<_, _>>();
    for event in events {
        event.session_ordinal = ordinals[&event.native_session_id];
    }
}

#[derive(Default)]
struct ArtifactIds {
    current: HashMap<(String, String), String>,
    attempted: HashMap<(String, String), String>,
    generations: HashMap<(String, String), usize>,
}

impl ArtifactIds {
    fn new_id(&mut self, worktree: &str, path: &str) -> String {
        let key = (worktree.to_string(), path.to_string());
        let generation = self.generations.entry(key).or_default();
        let identity = format!("{path}#{generation}");
        *generation += 1;
        identity
    }

    fn resolve(&mut self, action: &FileAction, confirmed: bool) -> String {
        let key = (action.worktree_id.clone(), action.path.clone());
        if action.access == "rename"
            && confirmed
            && let Some(previous) = &action.previous_path
        {
            let previous_worktree = action
                .previous_worktree_id
                .as_deref()
                .unwrap_or(&action.worktree_id);
            if previous_worktree == action.worktree_id {
                let previous_key = (previous_worktree.to_string(), previous.clone());
                let identity = self
                    .current
                    .remove(&previous_key)
                    .or_else(|| self.attempted.remove(&previous_key))
                    .unwrap_or_else(|| self.new_id(previous_worktree, previous));
                self.current.insert(key.clone(), identity.clone());
                self.attempted.remove(&key);
                return identity;
            }
        }
        if !confirmed {
            if let Some(identity) = self.current.get(&key) {
                return identity.clone();
            }
            if let Some(identity) = self.attempted.get(&key) {
                return identity.clone();
            }
            let identity = self.new_id(&action.worktree_id, &action.path);
            self.attempted.insert(key, identity.clone());
            return identity;
        }
        let identity = if let Some(identity) = self.current.get(&key) {
            identity.clone()
        } else {
            let identity = if action.access == "create" {
                self.new_id(&action.worktree_id, &action.path)
            } else {
                self.attempted
                    .remove(&key)
                    .unwrap_or_else(|| self.new_id(&action.worktree_id, &action.path))
            };
            self.current.insert(key.clone(), identity.clone());
            identity
        };
        // A confirmed effect supersedes any identity that existed only as a
        // failed/unknown attempt.  Otherwise a later delete could expose and
        // incorrectly revive that stale attempted generation.
        self.attempted.remove(&key);
        if action.access == "delete" {
            self.current.remove(&key);
        }
        identity
    }
}

fn annotate_artifact_ids(events: &mut [RepositoryEvent]) {
    let mut tracker = ArtifactIds::default();
    for event in events {
        for action in &mut event.actions {
            action.artifact_id = tracker.resolve(action, event.status == "ok");
        }
    }
}

fn source_stream_id(vendor: &str, native_session_id: &str, source_stem: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(vendor.as_bytes());
    digest.update([0]);
    digest.update(native_session_id.as_bytes());
    digest.update([0]);
    digest.update(source_stem.as_bytes());
    hex::encode(digest.finalize())[..16].to_string()
}

fn annotate_directory_scopes(events: &mut [RepositoryEvent]) {
    let mut directories = HashSet::<(String, String)>::new();
    for event in events {
        for action in &event.actions {
            for prefix in directory_prefixes(std::slice::from_ref(&action.path)) {
                directories.insert((action.worktree_id.clone(), prefix));
            }
            if let Some(previous) = &action.previous_path {
                let worktree = action
                    .previous_worktree_id
                    .as_deref()
                    .unwrap_or(&action.worktree_id);
                for prefix in directory_prefixes(std::slice::from_ref(previous)) {
                    directories.insert((worktree.to_string(), prefix));
                }
            }
        }
        let exact_file_tool = exact_file_tool(event);
        let directory_tool = directory_tool(event);
        for action in &mut event.actions {
            let key = (
                action.worktree_id.clone(),
                action.path.trim_end_matches('/').to_string(),
            );
            if exact_file_tool {
                directories.remove(&key);
            }
            let previous_is_directory = action.previous_path.as_deref().is_some_and(|path| {
                directories.contains(&(
                    action
                        .previous_worktree_id
                        .clone()
                        .unwrap_or_else(|| action.worktree_id.clone()),
                    path.trim_end_matches('/').to_string(),
                ))
            });
            action.scope = !exact_file_tool
                && (directory_tool || directories.contains(&key) || previous_is_directory);
            if action.scope && action.access == "delete" {
                directories.retain(|(worktree, path)| {
                    worktree != &key.0
                        || (path != &key.1 && !path.starts_with(&format!("{}/", key.1)))
                });
            }
        }
    }
}

fn exact_file_tool(event: &RepositoryEvent) -> bool {
    let name = event.tool_name.to_ascii_lowercase();
    event.category == "edit"
        || matches!(
            name.as_str(),
            "read" | "edit" | "write" | "multiedit" | "notebookedit" | "apply_patch"
        )
        || matches!(
            event.command_name.as_str(),
            "cat" | "sed" | "head" | "tail" | "touch" | "truncate"
        )
}

fn directory_tool(event: &RepositoryEvent) -> bool {
    matches!(
        event.command_name.as_str(),
        "ls" | "find" | "fd" | "tree" | "mkdir" | "rmdir"
    )
}

fn directory_prefixes(paths: &[String]) -> HashSet<String> {
    let mut directories = HashSet::new();
    for path in paths {
        let parts = path
            .split('/')
            .filter(|part| !part.is_empty())
            .collect::<Vec<_>>();
        for depth in 1..parts.len() {
            directories.insert(parts[..depth].join("/"));
        }
    }
    directories
}

fn candidate_may_match_repo(candidate: &SessionCandidate, roots: &[PathBuf]) -> bool {
    match candidate.agent {
        AGENT_CLAUDE => {
            candidate_cwd_matches(&candidate.path, roots)
                || claude_project_name(&candidate.path).is_some_and(|project| {
                    roots
                        .iter()
                        .any(|root| encoded_claude_root(root) == project)
                })
        }
        AGENT_CODEX => session_header(&candidate.path).lines().any(|line| {
            let Some(row) = serde_json::from_str::<serde_json::Value>(line).ok() else {
                return false;
            };
            row.pointer("/payload/cwd")
                .and_then(|value| value.as_str())
                .map(PathBuf::from)
                .is_some_and(|cwd| roots.iter().any(|root| cwd.starts_with(root)))
        }),
        AGENT_GEMINI => gemini_project_hash(&candidate.path)
            .is_some_and(|project| roots.iter().any(|root| repository_hash(root) == project)),
        _ => false,
    }
}

fn candidate_cwd_matches(path: &Path, roots: &[PathBuf]) -> bool {
    let Ok(file) = std::fs::File::open(path) else {
        return false;
    };
    let mut reader = BufReader::new(file);
    let mut line = String::new();
    let mut bytes = 0usize;
    while bytes < 256 * 1024 && reader.read_line(&mut line).is_ok_and(|read| read > 0) {
        bytes += line.len();
        let matched = serde_json::from_str::<serde_json::Value>(&line)
            .ok()
            .and_then(|row| {
                row.get("cwd")
                    .or_else(|| row.pointer("/payload/cwd"))
                    .and_then(|value| value.as_str())
                    .map(PathBuf::from)
            })
            .is_some_and(|cwd| roots.iter().any(|root| cwd.starts_with(root)));
        if matched {
            return true;
        }
        line.clear();
    }
    false
}

fn encoded_claude_root(root: &Path) -> String {
    root.to_string_lossy().replace('/', "-")
}

fn claude_project_name(path: &Path) -> Option<String> {
    path.ancestors()
        .find(|ancestor| {
            ancestor
                .parent()
                .and_then(Path::file_name)
                .and_then(|v| v.to_str())
                == Some("projects")
        })?
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
}

fn gemini_project_hash(path: &Path) -> Option<String> {
    path.ancestors()
        .find(|ancestor| {
            ancestor
                .parent()
                .and_then(Path::file_name)
                .and_then(|v| v.to_str())
                == Some("tmp")
        })?
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
}

fn repository_hash(root: &Path) -> String {
    hex::encode(Sha256::digest(root.to_string_lossy().as_bytes()))
}

fn behavior_sessions(
    roots: &[PathBuf],
    excluded: &HashSet<PathBuf>,
) -> io::Result<Vec<(AgentSession, usize)>> {
    let Some(home) = dirs::home_dir() else {
        return Ok(Vec::new());
    };
    let search = [
        home.join(".claude/projects"),
        home.join(".codex/sessions"),
        home.join(".codex/archived_sessions"),
        home.join(".gemini/tmp"),
    ];
    let mut command = Command::new("rg");
    command.args([
        "--json",
        "--no-messages",
        "--no-config",
        "--mmap",
        "--fixed-strings",
        "--glob",
        "*.jsonl",
        "--glob",
        "*.json",
    ]);
    for term in roots.iter().filter_map(|root| root.to_str()) {
        command.args(["-e", term]);
    }
    command.args(search.iter().filter(|path| path.exists()));
    let mut child = command.stdout(Stdio::piped()).spawn().map_err(|error| {
        io::Error::new(
            error.kind(),
            format!("--global session scan needs ripgrep (`rg`): {error}"),
        )
    })?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| io::Error::other("ripgrep session scan returned no stdout"))?;
    let mut selected = HashSet::<PathBuf>::new();
    for line in BufReader::new(stdout).lines() {
        let line = line?;
        let Ok(row) = serde_json::from_str::<serde_json::Value>(&line) else {
            continue;
        };
        if row.get("type").and_then(|value| value.as_str()) != Some("match") {
            continue;
        }
        let (Some(path), Some(text)) = (
            row.pointer("/data/path/text").and_then(|v| v.as_str()),
            row.pointer("/data/lines/text").and_then(|v| v.as_str()),
        ) else {
            continue;
        };
        let tool_call = (json_type(text, "assistant") && text.contains(r#""tool_use""#))
            || (json_type(text, "response_item")
                && (json_type(text, "function_call") || json_type(text, "custom_tool_call")));
        if !tool_call && !path.contains("/.gemini/") {
            continue;
        }
        selected.insert(path.into());
    }
    let status = child.wait()?;
    if !status.success() && status.code() != Some(1) {
        return Err(io::Error::other(format!(
            "ripgrep global session scan failed with {status}"
        )));
    }
    let mut candidates = selected
        .into_iter()
        .filter(|path| !excluded.contains(path))
        .filter_map(|path| session_candidate_from_path(&path))
        .collect::<Vec<_>>();
    candidates.sort_by(|left, right| left.path.cmp(&right.path));
    Ok(parse_candidates(&candidates))
}

fn session_header(path: &Path) -> String {
    let Ok(mut file) = std::fs::File::open(path) else {
        return String::new();
    };
    let mut prefix = String::new();
    let Ok(_) = file.by_ref().take(256 * 1024).read_to_string(&mut prefix) else {
        return String::new();
    };
    prefix
        .lines()
        .filter(|line| json_type(line, "session_meta") || json_type(line, "turn_context"))
        .take(2)
        .map(|line| format!("{line}\n"))
        .collect()
}

pub(crate) fn repository_root(path: &Path) -> io::Result<PathBuf> {
    let path = path.canonicalize()?;
    Ok(PathBuf::from(
        git_text(&path, &["rev-parse", "--show-toplevel"])?.trim(),
    ))
}

pub(crate) fn worktree_roots(repo: &Path) -> Vec<PathBuf> {
    let mut roots = git_text(repo, &["worktree", "list", "--porcelain"])
        .unwrap_or_default()
        .lines()
        .filter_map(|line| line.strip_prefix("worktree "))
        .map(PathBuf::from)
        .collect::<Vec<_>>();
    roots.push(repo.to_path_buf());
    roots.sort_by(|left, right| {
        right
            .components()
            .count()
            .cmp(&left.components().count())
            .then_with(|| left.cmp(right))
    });
    roots.dedup();
    roots
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct ResolvedPath {
    worktree_id: String,
    path: String,
}

fn effective_tool_cwd(session_cwd: Option<&Path>, tool_workdir: Option<&str>) -> Option<PathBuf> {
    let Some(workdir) = tool_workdir.map(Path::new) else {
        return session_cwd.map(lexical);
    };
    if workdir.is_absolute() {
        return Some(lexical(workdir));
    }
    Some(lexical(&session_cwd?.join(workdir)))
}

fn resolve_tool_path(
    raw: &str,
    session_cwd: Option<&Path>,
    explicit_cwd: Option<&Path>,
    tool_cwd: Option<&Path>,
    command: &str,
    rebase_preabsolutized: bool,
    roots: &[PathBuf],
) -> Option<ResolvedPath> {
    let path = Path::new(raw.trim().trim_matches(['"', '\'', '`']));
    if rebase_preabsolutized
        && path.is_absolute()
        && !command.contains(raw)
        && let (Some(explicit), Some(scoped)) = (explicit_cwd, tool_cwd)
        && let Ok(relative) = path.strip_prefix(explicit)
    {
        return relative_to_roots(&scoped.join(relative), roots);
    }
    if rebase_preabsolutized
        && path.is_relative()
        && !command.contains(raw)
        && let (Some(session), Some(explicit), Some(scoped)) = (session_cwd, explicit_cwd, tool_cwd)
        && let Ok(prefix) = explicit.strip_prefix(session)
        && !prefix.as_os_str().is_empty()
        && let Ok(relative) = path.strip_prefix(prefix)
    {
        return relative_to_roots(&scoped.join(relative), roots);
    }
    resolve_path(raw, tool_cwd, roots)
}

fn resolve_path(raw: &str, cwd: Option<&Path>, roots: &[PathBuf]) -> Option<ResolvedPath> {
    let raw = raw.trim().trim_matches(['"', '\'', '`']);
    if raw.is_empty()
        || raw
            .chars()
            .any(|character| "$*?[]{}<>\n\r".contains(character))
    {
        return None;
    }
    let path = Path::new(raw);
    if path.is_absolute() {
        return relative_to_roots(path, roots);
    }
    relative_to_roots(&cwd?.join(path), roots)
}

fn relative_to_roots(path: &Path, roots: &[PathBuf]) -> Option<ResolvedPath> {
    let normalized = lexical(path);
    roots.iter().find_map(|root| {
        normalized.strip_prefix(lexical(root)).ok().map(|relative| {
            let value = relative.to_string_lossy().replace('\\', "/");
            ResolvedPath {
                worktree_id: worktree_id(root),
                path: if value.is_empty() { ".".into() } else { value },
            }
        })
    })
}

pub(crate) fn worktree_id(root: &Path) -> String {
    repository_hash(root).chars().take(12).collect()
}

fn lexical(path: &Path) -> PathBuf {
    let mut output = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                output.pop();
            }
            other => output.push(other.as_os_str()),
        }
    }
    output
}

pub(crate) fn git_lines(repo: &Path, args: &[&str]) -> io::Result<Vec<String>> {
    Ok(git_text(repo, args)?
        .lines()
        .map(|line| line.trim().to_string())
        .collect())
}

fn git_text(repo: &Path, args: &[&str]) -> io::Result<String> {
    let output = Command::new("git").args(args).current_dir(repo).output()?;
    if !output.status.success() {
        return Err(io::Error::other(format!(
            "git {} failed: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    String::from_utf8(output.stdout).map_err(io::Error::other)
}

#[cfg(test)]
mod tests {
    use super::*;
    use agent_session::{SessionEvents, TokenUsage, ToolEvent, ToolPath};
    use std::collections::BTreeMap;
    use std::time::SystemTime;

    fn tool(ts_ms: i64, status: &str, paths: Vec<ToolPath>) -> ToolEvent {
        ToolEvent {
            ts_ms: Some(ts_ms),
            end_ts_ms: None,
            prompt_index: 0,
            tool_name: "Tool".into(),
            source_event_id: None,
            parent_event_id: None,
            model: None,
            attribution_skill: None,
            attribution_agent: None,
            skill_name: None,
            skill_args: None,
            category: "file".into(),
            command: String::new(),
            workdir: None,
            command_name: String::new(),
            effect: String::new(),
            process_chain: Vec::new(),
            status: status.into(),
            path_groups: Vec::new(),
            paths,
            domains: Vec::new(),
            call_id: None,
        }
    }

    fn session(tools: Vec<ToolEvent>) -> AgentSession {
        AgentSession {
            agent_type: AGENT_CODEX.into(),
            session_id: "session".into(),
            conversation_id: None,
            source_role: Some("root".into()),
            source_agent_id: None,
            display_id: "session".into(),
            path: "/sessions/session.jsonl".into(),
            updated: SystemTime::UNIX_EPOCH,
            start_timestamp_ms: None,
            end_timestamp_ms: None,
            model: None,
            usage: TokenUsage::default(),
            model_usage: BTreeMap::new(),
            tools: BTreeMap::new(),
            files: BTreeMap::new(),
            prompt_preview: None,
            duration_ms: 0,
            cwd: Some("/repo".into()),
            last_message_at: None,
            events: SessionEvents {
                prompts: Vec::new(),
                tools,
                llm_responses: Vec::new(),
            },
        }
    }

    #[test]
    fn lexical_paths_cannot_escape_a_worktree() {
        let roots = vec![PathBuf::from("/repo")];
        assert_eq!(
            resolve_path("src/../lib.rs", Some(Path::new("/repo")), &roots).map(|value| value.path),
            Some("lib.rs".into())
        );
        assert_eq!(
            resolve_path(".", Some(Path::new("/repo")), &roots).map(|value| value.path),
            Some(".".into())
        );
        assert_eq!(
            resolve_path("../../secret", Some(Path::new("/repo")), &roots),
            None
        );
    }

    #[test]
    fn path_prefixes_identify_directories_without_turning_files_into_scopes() {
        let paths = vec![
            "src/main.rs".into(),
            "src/model/lib.rs".into(),
            "README.md".into(),
        ];
        let directories = directory_prefixes(&paths);
        assert!(directories.contains("src"));
        assert!(directories.contains("src/model"));
        assert!(!directories.contains("src/main.rs"));
        assert!(!directories.contains("README.md"));
    }

    #[test]
    fn agent_project_directories_match_exact_repository_roots() {
        let root = Path::new("/home/user/repo");
        let hash = repository_hash(root);
        let gemini = PathBuf::from(format!(
            "/home/user/.gemini/tmp/{}/chats/session.json",
            hash
        ));
        assert_eq!(gemini_project_hash(&gemini).as_deref(), Some(hash.as_str()));

        let claude = Path::new("/home/user/.claude/projects/-home-user-repo/session.jsonl");
        let sibling = Path::new("/home/user/.claude/projects/-home-user-repo-x/session.jsonl");
        assert_eq!(
            claude_project_name(claude).as_deref(),
            Some("-home-user-repo")
        );
        assert_ne!(
            claude_project_name(sibling),
            Some(encoded_claude_root(root))
        );
    }

    #[test]
    fn claude_candidate_cwd_handles_dotted_repository_names() {
        let path = std::env::temp_dir().join(format!(
            "agentsight-claude-cwd-{}.jsonl",
            std::process::id()
        ));
        std::fs::write(
            &path,
            r#"{"type":"user","cwd":"/home/user/eunomia.dev","sessionId":"s"}"#,
        )
        .expect("write fixture");
        assert!(candidate_cwd_matches(
            &path,
            &[PathBuf::from("/home/user/eunomia.dev")]
        ));
        std::fs::remove_file(path).expect("remove fixture");
    }

    #[test]
    fn source_stream_identity_is_archive_location_independent() {
        assert_eq!(
            source_stream_id("claude", "abc", "file"),
            "9e5577cec53a8c58"
        );
    }

    #[test]
    fn copied_native_transcripts_do_not_duplicate_tool_calls() {
        let mut first_tool = tool(
            1,
            "unknown",
            vec![ToolPath {
                path: "src/lib.rs".into(),
                access: "write".into(),
                previous_path: None,
            }],
        );
        first_tool.call_id = Some("call-shared".into());
        let mut first = session(vec![first_tool]);
        first.path = "/sessions/rollout-one.jsonl".into();

        let mut complete_tool = tool(
            2,
            "ok",
            vec![ToolPath {
                path: "src/lib.rs".into(),
                access: "write".into(),
                previous_path: None,
            }],
        );
        complete_tool.call_id = Some("call-shared".into());
        let mut complete = session(vec![complete_tool]);
        complete.path = "/sessions/rollout-two.jsonl".into();

        let mut batch = (Vec::new(), 0);
        append_session(&first, 1, &["/repo".into()], true, &mut batch);
        append_session(&complete, 1, &["/repo".into()], true, &mut batch);
        deduplicate_native_tool_calls(&mut batch.0);

        assert_eq!(batch.0.len(), 1);
        assert_eq!(batch.0[0].status, "ok");
        assert_eq!(batch.0[0].source_call_id.as_deref(), Some("call-shared"));
        assert_eq!(batch.0[0].actions.len(), 1);
        assert_eq!(batch.0[0].id.len(), 16);
    }

    #[test]
    fn nested_worktree_root_wins_over_parent_repository() {
        let roots = vec![
            PathBuf::from("/repo/.worktrees/feature"),
            PathBuf::from("/repo"),
        ];
        assert_eq!(
            relative_to_roots(Path::new("/repo/.worktrees/feature/src/lib.rs"), &roots)
                .map(|value| value.path),
            Some("src/lib.rs".into())
        );
    }

    #[test]
    fn tool_workdir_takes_precedence_over_session_cwd() {
        assert_eq!(
            effective_tool_cwd(Some(Path::new("/repo")), Some("nested")),
            Some(PathBuf::from("/repo/nested"))
        );
        assert_eq!(
            effective_tool_cwd(Some(Path::new("/repo")), Some("/repo/other")),
            Some(PathBuf::from("/repo/other"))
        );
        assert_eq!(
            effective_tool_cwd(Some(Path::new("/repo")), None),
            Some(PathBuf::from("/repo"))
        );
    }

    #[test]
    fn leading_shell_cd_scopes_relative_paths_before_repository_projection() {
        assert_eq!(
            inline_shell_cwd(
                "cd /tmp/scratch && mkdir -p fake/docs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Known(PathBuf::from("/tmp/scratch"))
        );
        assert_eq!(
            inline_shell_cwd("set -e\ncd nested && cargo test", Some(Path::new("/repo"))),
            InlineShellCwd::Known(PathBuf::from("/repo/nested"))
        );
        assert_eq!(
            inline_shell_cwd("cd \"$tmpdir\" && touch fake.rs", Some(Path::new("/repo"))),
            InlineShellCwd::Unknown
        );
        assert_eq!(
            inline_shell_cwd(
                "tmpdir=$(mktemp -d); cd \"$tmpdir\"; touch fake.rs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Unknown
        );
        assert_eq!(
            inline_shell_cwd(
                "label=fixture; cd /tmp/scratch; touch fake.rs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Known(PathBuf::from("/tmp/scratch"))
        );
        assert_eq!(
            inline_shell_cwd(
                "echo preparing; cd /tmp/scratch; touch fake.rs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Unknown
        );
        assert_eq!(
            inline_shell_cwd(
                "cd /tmp/first; cd /tmp/second; touch fake.rs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Unknown
        );
        assert_eq!(
            inline_shell_cwd(
                "pushd /tmp/scratch; touch fake.rs",
                Some(Path::new("/repo"))
            ),
            InlineShellCwd::Unknown
        );
        assert_eq!(
            inline_shell_cwd("cargo test", Some(Path::new("/repo"))),
            InlineShellCwd::Absent
        );

        let mut outside = tool(
            1,
            "ok",
            vec![ToolPath {
                path: "fake/docs/output.md".into(),
                access: "create".into(),
                previous_path: None,
            }],
        );
        outside.command = "cd /tmp/scratch && mkdir -p fake/docs".into();
        let mut dynamic = tool(
            2,
            "ok",
            vec![ToolPath {
                path: "fake.rs".into(),
                access: "create".into(),
                previous_path: None,
            }],
        );
        dynamic.command = "cd \"$tmpdir\" && touch fake.rs".into();
        let mut preabsolutized_dynamic = tool(
            3,
            "ok",
            vec![ToolPath {
                path: "/repo/fake.rs".into(),
                access: "create".into(),
                previous_path: None,
            }],
        );
        preabsolutized_dynamic.command = "cd \"$tmpdir\" && touch fake.rs".into();
        let mut inside = tool(
            4,
            "ok",
            vec![ToolPath {
                // `agent-session` may already have joined this relative shell
                // operand to Tool workdir; repository scoping must still
                // apply the literal leading `cd nested`.
                path: "/repo/src/lib.rs".into(),
                access: "read".into(),
                previous_path: None,
            }],
        );
        inside.command = "cd nested && sed -n 1,20p src/lib.rs".into();
        let mut relative_workdir = tool(
            5,
            "ok",
            vec![ToolPath {
                path: "nested/src/lib.rs".into(),
                access: "read".into(),
                previous_path: None,
            }],
        );
        relative_workdir.workdir = Some("nested".into());
        relative_workdir.command = "cd sub && cat src/lib.rs".into();
        let mut batch = (Vec::new(), 0);
        append_session(
            &session(vec![
                outside,
                dynamic,
                preabsolutized_dynamic,
                inside,
                relative_workdir,
            ]),
            5,
            &["/repo".into()],
            true,
            &mut batch,
        );
        assert!(batch.0[0].actions.is_empty());
        assert!(batch.0[1].actions.is_empty());
        assert!(batch.0[2].actions.is_empty());
        assert_eq!(batch.0[3].actions[0].path, "nested/src/lib.rs");
        assert_eq!(batch.0[4].actions[0].path, "nested/sub/src/lib.rs");
    }

    #[test]
    fn directory_scope_is_action_time_local_across_file_directory_conversion() {
        let mut file_before = tool(
            1,
            "ok",
            vec![ToolPath {
                path: "node".into(),
                access: "write".into(),
                previous_path: None,
            }],
        );
        file_before.tool_name = "Write".into();
        file_before.category = "edit".into();
        let mut child = tool(
            2,
            "ok",
            vec![ToolPath {
                path: "node/child.rs".into(),
                access: "read".into(),
                previous_path: None,
            }],
        );
        child.tool_name = "Read".into();
        let mut file_after = tool(
            3,
            "ok",
            vec![ToolPath {
                path: "node".into(),
                access: "write".into(),
                previous_path: None,
            }],
        );
        file_after.tool_name = "Write".into();
        file_after.category = "edit".into();
        let mut batch = (Vec::new(), 0);
        append_session(
            &session(vec![file_before, child, file_after]),
            3,
            &["/repo".into()],
            true,
            &mut batch,
        );
        annotate_directory_scopes(&mut batch.0);
        assert!(!batch.0[0].actions[0].scope);
        assert!(!batch.0[1].actions[0].scope);
        assert!(!batch.0[2].actions[0].scope);
    }

    #[test]
    fn diagnose_invocation_does_not_observe_itself() {
        assert!(is_standalone_workspace_diagnose_command(
            "/tmp/target/release/agentvis diagnose /repo --global"
        ));
        assert!(is_standalone_workspace_diagnose_command(
            "./agentsight diagnose . -o output/brief.md"
        ));
        assert!(!is_standalone_workspace_diagnose_command(
            "rg -n 'agentsight diagnose' docs/usage.md"
        ));
        assert!(!is_standalone_workspace_diagnose_command(
            "cargo test && ./agentsight diagnose ."
        ));
    }

    #[test]
    fn repository_sessions_keep_every_timed_tool_action() {
        let mut cited = tool(
            3,
            "ok",
            vec![ToolPath {
                path: "src/read.rs".into(),
                access: "read".into(),
                previous_path: None,
            }],
        );
        cited.call_id = Some("toolu_source".into());
        let value = session(vec![
            tool(
                1,
                "fail",
                vec![ToolPath {
                    path: "src/failed.rs".into(),
                    access: "write".into(),
                    previous_path: None,
                }],
            ),
            tool(2, "ok", Vec::new()),
            cited,
        ]);
        let mut batch = (Vec::new(), 0);
        append_session(&value, 7, &["/repo".into()], true, &mut batch);
        assert_eq!(batch.0.len(), 3);
        assert_eq!(batch.0[0].status, "fail");
        assert_eq!(batch.0[0].actions[0].path, "src/failed.rs");
        assert!(batch.0[1].actions.is_empty());
        assert_eq!(batch.0[2].actions[0].path, "src/read.rs");
        assert_eq!(batch.0[2].source_call_id.as_deref(), Some("toolu_source"));
        assert_eq!(batch.0[2].source_tool_ordinal, 2);
        assert_eq!(batch.1, 7);
    }

    #[test]
    fn rename_actions_have_canonical_order_and_one_artifact_identity() {
        let value = session(vec![tool(
            1,
            "ok",
            vec![
                ToolPath {
                    path: "aaa-new.rs".into(),
                    access: "rename".into(),
                    previous_path: Some("zzz-old.rs".into()),
                },
                ToolPath {
                    path: "zzz-old.rs".into(),
                    access: "rename_from".into(),
                    previous_path: None,
                },
            ],
        )]);
        let mut batch = (Vec::new(), 0);
        append_session(&value, 1, &["/repo".into()], true, &mut batch);
        annotate_session_ordinals(&mut batch.0);
        annotate_artifact_ids(&mut batch.0);
        let actions = &batch.0[0].actions;
        assert_eq!(actions[0].access, "rename_from");
        assert_eq!(actions[0].action_ordinal, 0);
        assert_eq!(actions[1].access, "rename");
        assert_eq!(actions[1].action_ordinal, 1);
        assert_eq!(actions[0].artifact_id, actions[1].artifact_id);
    }

    #[test]
    fn artifact_identity_matches_shared_lifecycle_fixture() {
        let path = std::env::var("RQ7_LIFECYCLE_FIXTURES").ok();
        let text = path.as_deref().map_or_else(
            || include_str!("../tests/fixtures/strict-lifecycle.json").to_string(),
            |path| std::fs::read_to_string(path).expect("read lifecycle fixture"),
        );
        let fixtures: Vec<serde_json::Value> =
            serde_json::from_str(&text).expect("parse lifecycle fixture");
        for fixture in fixtures {
            let mut tracker = ArtifactIds::default();
            for step in fixture["steps"].as_array().expect("fixture steps") {
                let worktree = step["worktree"].as_str().unwrap_or("w");
                let action = FileAction {
                    worktree_id: worktree.into(),
                    path: step["path"].as_str().expect("path").into(),
                    access: step["access"].as_str().expect("access").into(),
                    previous_path: step["previous_path"].as_str().map(str::to_string),
                    previous_worktree_id: step["previous_worktree"].as_str().map(str::to_string),
                    scope: false,
                    action_ordinal: 0,
                    artifact_id: String::new(),
                };
                assert_eq!(
                    tracker.resolve(&action, step["confirmed"].as_bool().expect("confirmed")),
                    step["artifact_id"].as_str().expect("artifact id"),
                    "fixture {}",
                    fixture["name"].as_str().expect("fixture name"),
                );
            }
        }
    }

    #[test]
    fn external_sessions_keep_only_proven_repository_actions() {
        let value = session(vec![
            tool(1, "ok", Vec::new()),
            tool(
                2,
                "ok",
                vec![ToolPath {
                    path: "src/read.rs".into(),
                    access: "read".into(),
                    previous_path: None,
                }],
            ),
        ]);
        let mut batch = (Vec::new(), 0);
        append_session(&value, 2, &["/repo".into()], false, &mut batch);
        assert_eq!(batch.0.len(), 1);
        assert_eq!(batch.0[0].ts_ms, 2);
        assert!(!batch.0[0].workspace_session);
    }
}
