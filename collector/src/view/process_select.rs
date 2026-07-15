// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::sources::proc::{PidSeed, ProcInfo, ProcSnapshot};
use std::collections::HashSet;
use std::path::Path;

pub(crate) fn live_root_pids(
    snapshot: &ProcSnapshot,
    pid: Option<u32>,
    comm: Option<&str>,
) -> Vec<u32> {
    if let Some(pid) = pid {
        return snapshot
            .procs
            .contains_key(&pid)
            .then_some(vec![pid])
            .unwrap_or_default();
    }

    if let Some(comm) = comm {
        return root_pids_matching_comm(snapshot, comm);
    }

    root_pids_for_known_agents(snapshot)
}

pub(crate) fn seeds_for_comm(snapshot: &ProcSnapshot, comm: &str) -> Vec<PidSeed> {
    seeds_for_roots(snapshot, root_pids_matching_comm(snapshot, comm))
}

pub(crate) fn process_seeds(
    snapshot: &ProcSnapshot,
    session_id: Option<u32>,
    pid: Option<u32>,
    comm: Option<&str>,
    include_all: bool,
) -> Vec<PidSeed> {
    if let Some(session_id) = session_id {
        snapshot.seeds_for_session(session_id)
    } else if let Some(pid) = pid {
        snapshot.seeds_for_pid_family(pid)
    } else if let Some(comm) = comm {
        seeds_for_comm(snapshot, comm)
    } else if include_all {
        snapshot.seeds_for_all()
    } else {
        Vec::new()
    }
}

pub(crate) fn pids_matching_comm(snapshot: &ProcSnapshot, comm: &str) -> Vec<u32> {
    snapshot
        .procs
        .values()
        .filter(|proc_info| process_matches_comm(proc_info, comm))
        .map(|proc_info| proc_info.pid)
        .collect()
}

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

pub(crate) fn known_agent_label(comm: &str, command: &str) -> Option<&'static str> {
    label_from_exec_token(comm).or_else(|| label_from_command_argv(command))
}

fn root_pids_matching_comm(snapshot: &ProcSnapshot, comm: &str) -> Vec<u32> {
    sorted_root_pids(snapshot, |proc_info| process_matches_comm(proc_info, comm))
}

fn root_pids_for_known_agents(snapshot: &ProcSnapshot) -> Vec<u32> {
    let mut roots = Vec::new();
    for proc_info in snapshot.procs.values() {
        let Some(label) = known_agent_label(&proc_info.comm, &proc_info.command) else {
            continue;
        };
        let nested_codex_exec = label == "codex" && is_codex_exec_invocation(proc_info);
        if has_matching_ancestor(snapshot, proc_info, |parent| {
            known_agent_label(&parent.comm, &parent.command) == Some(label)
                && (!nested_codex_exec || is_codex_exec_invocation(parent))
        }) {
            continue;
        }
        roots.push(proc_info.pid);
    }
    roots
}

fn sorted_root_pids(
    snapshot: &ProcSnapshot,
    matches: impl Fn(&ProcInfo) -> bool + Copy,
) -> Vec<u32> {
    let mut roots = Vec::new();
    for proc_info in snapshot.procs.values() {
        if !matches(proc_info) {
            continue;
        }
        if has_matching_ancestor(snapshot, proc_info, matches) {
            continue;
        }
        roots.push(proc_info.pid);
    }
    roots.sort_unstable();
    roots
}

fn seeds_for_roots(snapshot: &ProcSnapshot, roots: Vec<u32>) -> Vec<PidSeed> {
    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for pid in roots {
        for family_pid in snapshot.process_family(pid) {
            if seen.insert(family_pid)
                && let Some(proc_info) = snapshot.procs.get(&family_pid)
            {
                out.push(proc_info.seed());
            }
        }
    }
    out
}

fn has_matching_ancestor(
    snapshot: &ProcSnapshot,
    proc_info: &ProcInfo,
    matches: impl Fn(&ProcInfo) -> bool,
) -> bool {
    let mut parent_pid = proc_info.ppid;
    let mut seen = HashSet::new();
    while parent_pid > 0 && seen.insert(parent_pid) {
        let Some(parent) = snapshot.procs.get(&parent_pid) else {
            break;
        };
        if matches(parent) {
            return true;
        }
        parent_pid = parent.ppid;
    }
    false
}

fn process_matches_comm(proc_info: &ProcInfo, wanted: &str) -> bool {
    let wanted = wanted.to_ascii_lowercase();
    if proc_info.comm.to_ascii_lowercase().contains(&wanted) {
        return true;
    }
    executable_tokens(&proc_info.command).any(|token| executable_token_matches(token, &wanted))
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

fn executable_tokens(command: &str) -> impl Iterator<Item = &str> {
    let mut first = true;
    command.split_whitespace().filter(move |arg| {
        let keep = first || looks_like_exec_path(arg);
        first = false;
        keep
    })
}

fn looks_like_exec_path(token: &str) -> bool {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    token.contains('/')
}

fn executable_token_matches(token: &str, wanted: &str) -> bool {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    if token.is_empty() {
        return false;
    }

    let lower = token.to_ascii_lowercase();
    if label_from_exec_token(&lower).is_some_and(|label| label.contains(wanted)) {
        return true;
    }
    let basename = Path::new(&lower)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(lower.as_str());
    !basename.contains('.') && basename.contains(wanted)
}

fn label_from_exec_token(token: &str) -> Option<&'static str> {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    if token.is_empty() {
        return None;
    }

    let lower = token.to_ascii_lowercase();
    let basename = Path::new(&lower)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(lower.as_str());

    label_from_exec_name(basename).or_else(|| label_from_known_package_path(&lower))
}

fn label_from_exec_name(name: &str) -> Option<&'static str> {
    match name {
        "claude" | "claude-code" => Some("claude"),
        "codex" | "codex-cli" => Some("codex"),
        "gemini" | "gemini-cli" => Some("gemini"),
        "opencode" => Some("opencode"),
        "aider" => Some("aider"),
        "goose" => Some("goose"),
        "openclaw" => Some("openclaw"),
        name if name.starts_with("openclaw-") => Some("openclaw"),
        _ => None,
    }
}

fn label_from_known_package_path(path: &str) -> Option<&'static str> {
    if path.contains("@anthropic-ai/claude-code") || path.contains("/claude-code/") {
        Some("claude")
    } else if path.contains("@openai/codex") || path.contains("/codex-linux-") {
        Some("codex")
    } else if path.contains("@google/gemini-cli") || path.contains("/gemini-cli/") {
        Some("gemini")
    } else {
        None
    }
}

pub(crate) fn is_codex_exec_invocation(proc_info: &ProcInfo) -> bool {
    known_agent_label(&proc_info.comm, &proc_info.command) == Some("codex")
        && has_codex_exec_subcommand(&proc_info.command)
}

fn has_codex_exec_subcommand(command: &str) -> bool {
    let mut previous = "";
    for token in command.split_whitespace() {
        if is_codex_executable_token(previous) && token == "exec" {
            return true;
        }
        previous = token;
    }
    false
}

fn is_codex_executable_token(token: &str) -> bool {
    let token = token.trim_matches(|ch| matches!(ch, '"' | '\''));
    if token.is_empty() {
        return false;
    }
    let lower = token.to_ascii_lowercase();
    let basename = Path::new(&lower)
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or(lower.as_str());
    matches!(basename, "codex" | "codex-cli")
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
    fn process_comm_matching_uses_comm_and_executable_tokens_only() {
        let proc_info = ProcInfo {
            comm: "agentsight".to_string(),
            command: "agentsight top -c claude --model claude-sonnet".to_string(),
            ..Default::default()
        };
        assert!(!process_matches_comm(&proc_info, "claude"));
        assert!(process_matches_comm(&proc_info, "agentsight"));
    }

    #[test]
    fn process_comm_matching_ignores_agent_names_in_data_paths_and_shell_args() {
        let proc_info = ProcInfo {
            comm: "docker".to_string(),
            command: "docker run image bash -c claude --settings /root/config/claude/settings.json"
                .to_string(),
            ..Default::default()
        };

        assert!(!process_matches_comm(&proc_info, "claude"));
        assert!(process_matches_comm(&proc_info, "docker"));
    }

    #[test]
    fn live_roots_suppress_known_agent_children_with_same_label() {
        let procs = [
            ProcInfo {
                pid: 1,
                comm: "node".to_string(),
                command: "node /opt/npm/bin/codex".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 2,
                ppid: 1,
                comm: "codex".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 3,
                comm: "claude".to_string(),
                ..Default::default()
            },
        ];
        let snapshot = ProcSnapshot {
            procs: procs
                .into_iter()
                .map(|proc_info| (proc_info.pid, proc_info))
                .collect(),
            ..Default::default()
        };

        assert_eq!(live_root_pids(&snapshot, None, None), vec![1, 3]);
    }

    #[test]
    fn live_roots_keep_nested_codex_exec_under_app_server() {
        let procs = [
            ProcInfo {
                pid: 1,
                comm: "node".to_string(),
                command: "node /opt/node/bin/codex app-server --listen sock".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 2,
                ppid: 1,
                comm: "node".to_string(),
                command: "node /opt/node/bin/codex exec -C /work hello".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 3,
                ppid: 2,
                comm: "codex".to_string(),
                command: "/opt/node_modules/@openai/codex-linux-x64/bin/codex exec -C /work hello"
                    .to_string(),
                ..Default::default()
            },
        ];
        let snapshot = ProcSnapshot {
            procs: procs
                .into_iter()
                .map(|proc_info| (proc_info.pid, proc_info))
                .collect(),
            ..Default::default()
        };

        assert_eq!(live_root_pids(&snapshot, None, None), vec![1, 2]);
    }

    #[test]
    fn comm_seeds_use_the_same_root_selection_as_live_roots() {
        let procs = [
            ProcInfo {
                pid: 1,
                comm: "node".to_string(),
                command: "node /opt/npm/bin/codex".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 2,
                ppid: 1,
                comm: "codex".to_string(),
                ..Default::default()
            },
            ProcInfo {
                pid: 3,
                comm: "codex".to_string(),
                ..Default::default()
            },
        ];
        let snapshot = ProcSnapshot {
            procs: procs
                .into_iter()
                .map(|proc_info| (proc_info.pid, proc_info))
                .collect(),
            ..Default::default()
        };

        let roots = live_root_pids(&snapshot, None, Some("codex"));
        let seeds = seeds_for_comm(&snapshot, "codex");

        assert_eq!(roots, vec![1, 3]);
        assert_eq!(
            seeds.into_iter().map(|seed| seed.pid).collect::<Vec<_>>(),
            vec![1, 2, 3]
        );
    }
}
