// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Agent adapter registry: the single home of per-agent knowledge.
//!
//! Each supported agent CLI is described by one module exporting an
//! [`AgentAdapter`] descriptor: how to recognize its processes (exec names,
//! package paths), how to surface it in `agentsight discover`, and where its
//! native session files live. Consumers (process selection, discover, the
//! agent-native session source) query this registry instead of hard-coding
//! agent names.
//!
//! Adding an agent = adding one module + one registry entry. Agents without
//! TLS capture support (e.g. Codex uses rustls) still get process tracking,
//! stdio capture, and native-session receipts through their adapter.
//!
//! Session *file format* parsing lives in `crate::sources::agent_native`
//! (`parse_content`), keyed by the adapter `name`. Attach strategy is
//! mechanism-based, not per-agent: `record`/`debug trace` resolve the target
//! binary and adopt it when it embeds SSL (`binary_embeds_ssl`), with
//! `docker://` for containers — see `cmd_trace.rs`.

pub(crate) mod aider;
pub(crate) mod claude;
pub(crate) mod codex;
pub(crate) mod gemini;
pub(crate) mod goose;
pub(crate) mod openclaw;
pub(crate) mod opencode;

use crate::event::Event;
use crate::semantic::Observations;
use std::path::Path;

pub(crate) struct AgentAdapter {
    /// Canonical label used in rows, top output, and session ids.
    pub name: &'static str,
    /// Executable basenames that identify this agent.
    pub exec_names: &'static [&'static str],
    /// Basename prefixes (comm is truncated to 15 chars by the kernel).
    pub exec_name_prefixes: &'static [&'static str],
    /// Path fragments of known installations (npm packages, release dirs).
    pub package_path_markers: &'static [&'static str],
    /// Entry for `agentsight discover`; None for agents we only label.
    pub discover: Option<Discover>,
    /// Where the agent writes its own session logs, if it does.
    pub native_sessions: Option<NativeSessions>,
    /// How this agent's activity gets attributed to live pids/sessions.
    pub attribution: Attribution,
    /// Agent-reported telemetry decoder (token usage / tool calls the agent
    /// emits about itself, e.g. Claude telemetry batches, Gemini stdout
    /// stats). Called by `crate::decode` for every event; the hook does its
    /// own gating and pushes into `Observations`.
    pub decode_observations: Option<DecodeObservations>,
}

pub(crate) type DecodeObservations =
    fn(event: &Event, event_id: &str, host: Option<&str>, out: &mut Observations);

/// The attribution story per agent: how token usage and activity connect to
/// live processes. This drives session↔process matching eligibility and the
/// evidence notes shown in `top`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum Attribution {
    /// Writes session log files; live pids are matched to sessions via file
    /// evidence (eBPF file writes, /proc fd scans, cwd+recency) in
    /// `view::session_process_match`.
    NativeSessionFiles,
    /// Reports usage itself (stdio/telemetry); decoded `ObservedUsage` rows
    /// already carry the live pid, so no session-file matching is needed.
    SelfReported,
    /// Process-tree evidence only.
    ProcessOnly,
}

pub(crate) struct Discover {
    pub id: &'static str,
    pub display_name: &'static str,
    pub command: &'static str,
    pub recommended_capture: &'static str,
}

pub(crate) struct NativeSessions {
    /// Session directory relative to `$HOME`, e.g. `[".claude", "projects"]`.
    pub dir_parts: [&'static str; 2],
    /// Path fragment identifying this agent's session files anywhere on disk.
    pub path_marker: &'static str,
}

pub(crate) static AGENTS: &[&AgentAdapter] = &[
    &claude::ADAPTER,
    &codex::ADAPTER,
    &gemini::ADAPTER,
    &opencode::ADAPTER,
    &aider::ADAPTER,
    &goose::ADAPTER,
    &openclaw::ADAPTER,
];

/// Identify an agent from a process comm or an executable token
/// (basename and known package paths are both consulted).
pub(crate) fn label_from_exec_token(token: &str) -> Option<&'static str> {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    if token.is_empty() {
        return None;
    }

    let lower = token.to_ascii_lowercase();
    let basename = Path::new(&lower)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(lower.as_str());

    label_for_exec_name(basename).or_else(|| label_for_package_path(&lower))
}

/// Identify an agent from a comm plus full command line.
pub(crate) fn known_agent_label(comm: &str, command: &str) -> Option<&'static str> {
    label_from_exec_token(comm).or_else(|| label_from_command_argv(command))
}

/// Best-effort agent label for display: known agent, else comm, else argv0.
pub(crate) fn agent_label_from_command(comm: &str, command: &str) -> String {
    known_agent_label(comm, command)
        .map(str::to_string)
        .unwrap_or_else(|| {
            if !comm.is_empty() && comm != "unknown" {
                comm.to_string()
            } else {
                command
                    .split_whitespace()
                    .next()
                    .unwrap_or("agent")
                    .to_string()
            }
        })
}

/// A command-line token that plausibly names an executable (not a flag or a
/// data argument): argv0, or any path-looking token.
pub(crate) fn looks_like_exec_path(token: &str) -> bool {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    token.contains('/')
}

fn label_from_command_argv(command: &str) -> Option<&'static str> {
    let mut args = command.split_whitespace();
    let argv0 = args.next()?;
    if let Some(label) = label_from_exec_token(argv0) {
        return Some(label);
    }

    args.filter(|arg| looks_like_exec_path(arg))
        .find_map(label_from_exec_token)
}

fn label_for_exec_name(name: &str) -> Option<&'static str> {
    AGENTS.iter().find_map(|agent| {
        (agent.exec_names.contains(&name)
            || agent
                .exec_name_prefixes
                .iter()
                .any(|prefix| name.starts_with(prefix)))
        .then_some(agent.name)
    })
}

fn label_for_package_path(path: &str) -> Option<&'static str> {
    AGENTS.iter().find_map(|agent| {
        agent
            .package_path_markers
            .iter()
            .any(|marker| path.contains(marker))
            .then_some(agent.name)
    })
}

/// Agents that write native session logs, with their `$HOME`-relative dirs.
pub(crate) fn native_session_agents() -> impl Iterator<Item = (&'static str, [&'static str; 2])> {
    AGENTS.iter().filter_map(|agent| {
        agent
            .native_sessions
            .as_ref()
            .map(|sessions| (agent.name, sessions.dir_parts))
    })
}

/// Attribution story for an agent label (defaults to process-only for
/// unknown agents).
pub(crate) fn attribution(agent: &str) -> Attribution {
    AGENTS
        .iter()
        .find(|adapter| adapter.name == agent)
        .map(|adapter| adapter.attribution)
        .unwrap_or(Attribution::ProcessOnly)
}

/// Run every adapter's observation decoder against one event.
pub(crate) fn decode_observations(
    event: &Event,
    event_id: &str,
    host: Option<&str>,
    out: &mut Observations,
) {
    for agent in AGENTS {
        if let Some(decode) = agent.decode_observations {
            decode(event, event_id, host, out);
        }
    }
}

/// Which agent owns a session file at this path, if any.
pub(crate) fn native_session_source(path: &Path) -> Option<&'static str> {
    let path = path.to_string_lossy();
    AGENTS.iter().find_map(|agent| {
        agent
            .native_sessions
            .as_ref()
            .filter(|sessions| path.contains(sessions.path_marker))
            .map(|_| agent.name)
    })
}

#[cfg(test)]
pub(crate) fn native_session_dir_parts(agent: &str) -> Option<[&'static str; 2]> {
    AGENTS
        .iter()
        .find(|adapter| adapter.name == agent)
        .and_then(|adapter| adapter.native_sessions.as_ref())
        .map(|sessions| sessions.dir_parts)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn known_agent_label_uses_executable_not_model_argument() {
        assert_eq!(
            known_agent_label(
                "agentsight",
                "agentsight top -s tokens -v all -c claude --model claude-sonnet"
            ),
            None
        );
        assert_eq!(
            known_agent_label(
                "python",
                "python benchmark_runner.py --model claude-sonnet-4-5-20250929"
            ),
            None
        );
        assert_eq!(
            known_agent_label(
                "docker",
                "docker run image bash -c claude --model claude-sonnet-4"
            ),
            None
        );
        assert_eq!(
            known_agent_label("node", "node /opt/npm/bin/codex --model gpt-5"),
            Some("codex")
        );
        assert_eq!(
            known_agent_label("node", "node /home/user/.local/bin/claude"),
            Some("claude")
        );
        assert_eq!(known_agent_label("claude", "claude"), Some("claude"));
        assert_eq!(known_agent_label("openclaw-gatewa", ""), Some("openclaw"));
    }

    #[test]
    fn native_session_sources_resolve_by_path_marker() {
        assert_eq!(
            native_session_source(Path::new("/home/u/.claude/projects/x/session.jsonl")),
            Some("claude")
        );
        assert_eq!(
            native_session_source(Path::new("/home/u/.codex/sessions/2026/x.jsonl")),
            Some("codex")
        );
        assert_eq!(native_session_source(Path::new("/tmp/other.jsonl")), None);
    }

    #[test]
    fn registry_has_unique_names_and_discover_ids() {
        let mut names: Vec<_> = AGENTS.iter().map(|agent| agent.name).collect();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), AGENTS.len());

        let mut ids: Vec<_> = AGENTS
            .iter()
            .filter_map(|agent| agent.discover.as_ref().map(|discover| discover.id))
            .collect();
        ids.sort_unstable();
        ids.dedup();
        assert_eq!(
            ids.len(),
            AGENTS
                .iter()
                .filter(|agent| agent.discover.is_some())
                .count()
        );
    }
}
