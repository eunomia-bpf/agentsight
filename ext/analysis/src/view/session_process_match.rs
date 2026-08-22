// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::SessionRow;
use crate::sources::proc::{ProcessKey, ProcessTree};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};

const SESSION_PROCESS_START_SKEW_MS: u64 = 30_000;
const TRACE_EBPF_FILE: &str = "ebpf_file";
const TRACE_PROC_FD: &str = "proc_fd";
const TRACE_STICKY_BINDING: &str = "sticky";
const TRACE_RECENT_CWD: &str = "cwd_recent";

#[derive(Debug, Clone, Default)]
pub struct LiveProcessCandidate {
    pub tree: ProcessTree,
    pub agent: String,
    pub age_s: Option<f64>,
    pub cwd: Option<String>,
}

#[derive(Debug, Clone)]
pub struct SessionProcessMatch {
    pub session_id: String,
    pub root_pid: u32,
    pub matched_pids: Vec<u32>,
    pub pid_starttime_ticks: u64,
    pub confidence: f32,
    pub evidence: &'static str,
}

#[derive(Debug, Default)]
pub struct SessionProcessMatches {
    pub by_session_id: HashMap<String, SessionProcessMatch>,
    pub used_root_pids: HashSet<u32>,
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
        sessions: &[SessionRow],
        processes: &[LiveProcessCandidate],
        fd_paths_by_process: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
        ebpf_path_by_process: &HashMap<ProcessKey, PathBuf>,
        now_ms: u64,
    ) -> SessionProcessMatches {
        let path_evidence =
            collect_path_evidence(processes, fd_paths_by_process, ebpf_path_by_process);
        self.bindings.retain(|pid, binding| {
            processes.iter().any(|process| {
                process.tree.root.pid == *pid
                    && process.tree.root.starttime_ticks == binding.starttime_ticks
            })
        });

        let mut out = SessionProcessMatches::default();
        for session in sessions {
            let Some(path) = session_path(session) else {
                continue;
            };
            let Some((process, evidence)) = processes.iter().find_map(|process| {
                if out.used_root_pids.contains(&process.tree.root.pid)
                    || process.agent != session.agent_type
                    || !session_is_fresh_enough_for_process(session, process, now_ms)
                {
                    return None;
                }
                self.link_trace(path, process, &path_evidence)
                    .map(|evidence| (process, evidence))
            }) else {
                continue;
            };
            record_match(&mut out, session, process, evidence);
        }

        let mut cwd_candidates = sessions
            .iter()
            .enumerate()
            .filter(|(_, session)| !out.by_session_id.contains_key(&session.id))
            .flat_map(|(session_index, session)| {
                let path = session_path(session);
                processes
                    .iter()
                    .enumerate()
                    .filter_map(move |(process_index, process)| {
                        let path = path?;
                        if out.used_root_pids.contains(&process.tree.root.pid)
                            || process.agent != session.agent_type
                            || !self.can_use_cwd_trace(path, process, &path_evidence)
                        {
                            return None;
                        }
                        recent_cwd_distance_ms(session, process, now_ms).map(|distance_ms| {
                            (
                                distance_ms,
                                std::cmp::Reverse(session_end_ms(session)),
                                session_index,
                                process_index,
                            )
                        })
                    })
            })
            .collect::<Vec<_>>();
        cwd_candidates.sort_unstable();
        for (_, _, session_index, process_index) in cwd_candidates {
            let session = &sessions[session_index];
            let process = &processes[process_index];
            if !out.by_session_id.contains_key(&session.id)
                && !out.used_root_pids.contains(&process.tree.root.pid)
            {
                record_match(&mut out, session, process, TRACE_RECENT_CWD);
            }
        }
        out
    }

    fn link_trace(
        &mut self,
        session_path: &Path,
        process: &LiveProcessCandidate,
        path_evidence: &HashMap<u32, BTreeMap<PathBuf, &'static str>>,
    ) -> Option<&'static str> {
        let pid = process.tree.root.pid;
        let path = agent_session::normalize_session_log_path(session_path);
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
        let path = agent_session::normalize_session_log_path(session_path);
        !self.bindings.get(&pid).is_some_and(|binding| {
            binding.starttime_ticks == process.tree.root.starttime_ticks
                && binding.session_path != path
        })
    }
}

pub fn session_path_from_raw_path(path: &Path) -> Option<PathBuf> {
    agent_session::session_log_path_from_str(&path.to_string_lossy())
}

fn session_path(session: &SessionRow) -> Option<&Path> {
    session_attr(session, "path").map(Path::new)
}

fn session_attr<'a>(session: &'a SessionRow, name: &str) -> Option<&'a str> {
    session
        .attributes
        .get(name)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
}

fn record_match(
    out: &mut SessionProcessMatches,
    session: &SessionRow,
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
    out.by_session_id.insert(
        session.id.clone(),
        SessionProcessMatch {
            session_id: session.id.clone(),
            root_pid: process.tree.root.pid,
            matched_pids,
            pid_starttime_ticks: process.tree.root.starttime_ticks,
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
    processes
        .iter()
        .filter_map(|process| {
            let mut evidence = BTreeMap::new();
            for key in &process.tree.members {
                if let Some(paths) = fd_paths_by_process.get(key) {
                    for path in paths {
                        if let Some(path) = session_path_from_raw_path(path) {
                            evidence.entry(path).or_insert(TRACE_PROC_FD);
                        }
                    }
                }
                if let Some(path) = observed_path_by_process
                    .get(key)
                    .and_then(|path| session_path_from_raw_path(path))
                {
                    evidence.insert(path, TRACE_EBPF_FILE);
                }
            }
            (!evidence.is_empty()).then_some((process.tree.root.pid, evidence))
        })
        .collect()
}

fn session_is_fresh_enough_for_process(
    session: &SessionRow,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> bool {
    process_start_ms(process, now_ms).is_none_or(|process_start_ms| {
        session_end_ms(session).saturating_add(SESSION_PROCESS_START_SKEW_MS) >= process_start_ms
    })
}

fn recent_cwd_distance_ms(
    session: &SessionRow,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> Option<u64> {
    let session_cwd = session_attr(session, "cwd")?;
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

fn session_end_ms(session: &SessionRow) -> u64 {
    session.end_timestamp_ms.unwrap_or(session.start_timestamp_ms)
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
    use serde_json::json;

    #[test]
    fn recent_cwd_match_uses_canonical_paths() {
        let raw =
            std::env::temp_dir().join(format!("agentsight-cwd-test-{}", std::process::id()));
        std::fs::create_dir_all(&raw).unwrap();
        let cwd = raw.canonicalize().unwrap();
        let cwd_text = cwd.to_string_lossy().into_owned();
        let session = SessionRow {
            id: "session".to_string(),
            agent_type: "codex".to_string(),
            start_timestamp_ms: 1_000,
            end_timestamp_ms: Some(10_000),
            attributes: json!({
                "cwd": cwd_text,
                "path": cwd.join(".codex/sessions/2026/07/12/session.jsonl")
            }),
            ..Default::default()
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
