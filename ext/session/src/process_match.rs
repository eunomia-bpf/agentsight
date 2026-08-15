// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Process-to-session matching logic.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};

use crate::parser::{normalize_session_log_path, session_log_path_from_str};
use crate::{
    SOURCE_SESSION_PROCESS_MATCH, TRACE_EBPF_FILE, TRACE_PROC_FD, TRACE_RECENT_CWD,
    TRACE_STICKY_BINDING,
};

const SESSION_PROCESS_START_SKEW_MS: u64 = 30_000;

/// Unique identifier for a process (pid + start time).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ProcessKey {
    pub pid: u32,
    pub starttime_ticks: u64,
}

/// A tree of related processes.
#[derive(Debug, Clone, Default)]
pub struct ProcessTree {
    pub root: ProcessKey,
    pub members: Vec<ProcessKey>,
}

/// A live process candidate for session matching.
#[derive(Debug, Clone, Default)]
pub struct LiveProcessCandidate {
    pub tree: ProcessTree,
    pub agent: String,
    pub age_s: Option<f64>,
    pub cwd: Option<String>,
}

/// Input for session-to-process matching.
#[derive(Debug, Clone)]
pub struct SessionProcessInput {
    pub id: String,
    pub agent: String,
    pub path: PathBuf,
    pub start_timestamp_ms: Option<u64>,
    pub end_timestamp_ms: Option<u64>,
    pub cwd: Option<String>,
}

/// A match between a session and a process.
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

/// Collection of session-to-process matches.
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

/// Stateful matcher for correlating sessions with live processes.
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
    if normalize_cwd(session_cwd) != normalize_cwd(process_cwd) {
        return None;
    }
    let process_start_ms = process_start_ms(process, now_ms)?;
    let session_end_ms = session_end_ms(session);
    (session_end_ms.saturating_add(SESSION_PROCESS_START_SKEW_MS) >= process_start_ms)
        .then_some(session_end_ms.abs_diff(process_start_ms))
}

fn normalize_cwd(cwd: &str) -> String {
    let path = Path::new(cwd);
    if !path.is_absolute() {
        return cwd.to_string();
    }
    std::fs::canonicalize(path)
        .map(|path| path.to_string_lossy().into_owned())
        .unwrap_or_else(|_| cwd.to_string())
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recent_cwd_match_uses_canonical_paths() {
        let raw =
            std::env::temp_dir().join(format!("agent-session-cwd-test-{}", std::process::id()));
        std::fs::create_dir_all(&raw).unwrap();
        let cwd = raw.canonicalize().unwrap();
        let session = SessionProcessInput {
            id: "session".to_string(),
            agent: "codex".to_string(),
            path: cwd.join(".codex/sessions/2026/07/12/session.jsonl"),
            start_timestamp_ms: Some(1_000),
            end_timestamp_ms: Some(10_000),
            cwd: Some(cwd.to_string_lossy().to_string()),
        };
        let process = LiveProcessCandidate {
            agent: "codex".to_string(),
            age_s: Some(5.0),
            cwd: Some(raw.to_string_lossy().to_string()),
            ..Default::default()
        };

        assert!(recent_cwd_distance_ms(&session, &process, 12_000).is_some());
        std::fs::remove_dir_all(&raw).unwrap();
    }
}
