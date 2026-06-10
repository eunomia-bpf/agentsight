// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::SessionRow;
use crate::sources::agent_native;
use crate::sources::proc::{ProcessKey, ProcessTree};
use serde_json::Value;
use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};

pub(crate) const TRACE_EBPF_FILE: &str = "ebpf_file";
pub(crate) const TRACE_PROC_FD: &str = "proc_fd";
pub(crate) const TRACE_STICKY_BINDING: &str = "sticky";
pub(crate) const TRACE_RECENT_CWD: &str = "cwd_recent";

const SOURCE_VIEW_MATCH: &str = "view.session_process_match";
const SESSION_PROCESS_START_SKEW_MS: u64 = 30_000;

#[derive(Debug, Clone, Default)]
pub(crate) struct LiveProcessCandidate {
    pub(crate) tree: ProcessTree,
    pub(crate) agent: String,
    pub(crate) age_s: Option<f64>,
    pub(crate) cwd: Option<String>,
}

#[derive(Debug, Clone)]
pub(crate) struct SessionProcessMatch {
    pub(crate) session_id: String,
    pub(crate) root_pid: u32,
    pub(crate) pid_starttime_ticks: u64,
    pub(crate) source: &'static str,
    pub(crate) confidence: f32,
    pub(crate) evidence: &'static str,
}

#[derive(Debug, Default)]
pub(crate) struct SessionProcessMatches {
    pub(crate) by_session_id: HashMap<String, SessionProcessMatch>,
    pub(crate) used_root_pids: HashSet<u32>,
}

#[derive(Default)]
pub(crate) struct SessionProcessMatcher {
    bindings: HashMap<u32, LiveSessionBinding>,
}

struct LiveSessionBinding {
    starttime_ticks: u64,
    session_path: PathBuf,
}

impl SessionProcessMatcher {
    pub(crate) fn match_sessions(
        &mut self,
        sessions: &[SessionRow],
        processes: &[LiveProcessCandidate],
        fd_paths_by_process: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
        ebpf_path_by_process: &HashMap<ProcessKey, PathBuf>,
        now_ms: u64,
    ) -> SessionProcessMatches {
        let path_evidence =
            collect_path_evidence(processes, fd_paths_by_process, ebpf_path_by_process);
        self.retain_live(processes);

        let mut out = SessionProcessMatches::default();
        for session in sessions {
            // Only agents whose attribution story is session-file based are
            // eligible for path-evidence matching; self-reported agents
            // (e.g. Gemini stdout stats) already carry live pids.
            if crate::agents::attribution(&session.agent_type)
                != crate::agents::Attribution::NativeSessionFiles
            {
                continue;
            }
            let Some(session_path) = session_path(session) else {
                continue;
            };
            let Some((process, evidence)) = processes.iter().find_map(|process| {
                if out.used_root_pids.contains(&process.tree.root.pid)
                    || process.agent != session.agent_type
                    || !session_is_fresh_enough_for_process(session, process, now_ms)
                {
                    return None;
                }
                self.link_trace(session_path, process, &path_evidence)
                    .map(|evidence| (process, evidence))
            }) else {
                continue;
            };

            record_match(&mut out, session, process, evidence);
        }

        let mut cwd_candidates = Vec::new();
        for (session_index, session) in sessions.iter().enumerate() {
            if out.by_session_id.contains_key(&session.id)
                || crate::agents::attribution(&session.agent_type)
                    != crate::agents::Attribution::NativeSessionFiles
            {
                continue;
            }
            let Some(session_path) = session_path(session) else {
                continue;
            };
            for (process_index, process) in processes.iter().enumerate() {
                if out.used_root_pids.contains(&process.tree.root.pid)
                    || process.agent != session.agent_type
                    || !self.can_use_cwd_trace(session_path, process, &path_evidence)
                {
                    continue;
                }
                let Some(distance_ms) = recent_cwd_distance_ms(session, process, now_ms) else {
                    continue;
                };
                cwd_candidates.push((
                    distance_ms,
                    Reverse(session_end_ms(session)),
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
        let path = agent_native::normalize_session_log_path(session_path);

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
        let path = agent_native::normalize_session_log_path(session_path);
        !self.bindings.get(&pid).is_some_and(|binding| {
            binding.starttime_ticks == process.tree.root.starttime_ticks
                && binding.session_path != path
        })
    }
}

fn record_match(
    out: &mut SessionProcessMatches,
    session: &SessionRow,
    process: &LiveProcessCandidate,
    evidence: &'static str,
) {
    out.used_root_pids.insert(process.tree.root.pid);
    out.by_session_id.insert(
        session.id.clone(),
        SessionProcessMatch {
            session_id: session.id.clone(),
            root_pid: process.tree.root.pid,
            pid_starttime_ticks: process.tree.root.starttime_ticks,
            source: SOURCE_VIEW_MATCH,
            confidence: confidence_for_evidence(evidence),
            evidence,
        },
    );
}

fn collect_path_evidence(
    processes: &[LiveProcessCandidate],
    fd_paths_by_process: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
    ebpf_path_by_process: &HashMap<ProcessKey, PathBuf>,
) -> HashMap<u32, BTreeMap<PathBuf, &'static str>> {
    let mut out = HashMap::new();

    for process in processes {
        let mut evidence = BTreeMap::new();
        for key in &process.tree.members {
            if let Some(paths) = fd_paths_by_process.get(key) {
                for path in paths {
                    if let Some(session_path) = session_path_from_raw_path(path) {
                        evidence.entry(session_path).or_insert(TRACE_PROC_FD);
                    }
                }
            }
            if let Some(path) = ebpf_path_by_process.get(key) {
                if let Some(session_path) = session_path_from_raw_path(path) {
                    evidence.insert(session_path, TRACE_EBPF_FILE);
                }
            }
        }
        if !evidence.is_empty() {
            out.insert(process.tree.root.pid, evidence);
        }
    }

    out
}

pub(crate) fn session_path_from_raw_path(path: &Path) -> Option<PathBuf> {
    agent_native::session_log_path_from_str(&path.to_string_lossy())
}

fn session_path(session: &SessionRow) -> Option<&Path> {
    session
        .attributes
        .get("path")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .map(Path::new)
}

fn session_is_fresh_enough_for_process(
    session: &SessionRow,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> bool {
    let Some(process_start_ms) = process_start_ms(process, now_ms) else {
        return true;
    };
    session_end_ms(session).saturating_add(SESSION_PROCESS_START_SKEW_MS) >= process_start_ms
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

fn recent_cwd_distance_ms(
    session: &SessionRow,
    process: &LiveProcessCandidate,
    now_ms: u64,
) -> Option<u64> {
    let session_cwd = session
        .attributes
        .get("cwd")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())?;
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
    let age_s = process.age_s?;
    Some(now_ms.saturating_sub((age_s.max(0.0) * 1000.0).round() as u64))
}

fn session_end_ms(session: &SessionRow) -> u64 {
    session
        .end_timestamp_ms
        .unwrap_or(session.start_timestamp_ms)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn session(id: &str, agent: &str, path: &Path, end_ms: u64) -> SessionRow {
        SessionRow {
            id: id.to_string(),
            agent_type: agent.to_string(),
            start_timestamp_ms: end_ms.saturating_sub(1000),
            end_timestamp_ms: Some(end_ms),
            attributes: json!({ "path": path.to_string_lossy(), "cwd": "/work" }),
            ..Default::default()
        }
    }

    fn process(pid: u32, starttime_ticks: u64, agent: &str, age_s: f64) -> LiveProcessCandidate {
        let key = ProcessKey {
            pid,
            starttime_ticks,
        };
        LiveProcessCandidate {
            tree: ProcessTree {
                root: key,
                members: vec![key],
            },
            agent: agent.to_string(),
            age_s: Some(age_s),
            cwd: Some("/work".to_string()),
        }
    }

    #[test]
    fn matches_session_to_process_with_fd_path_evidence() {
        let (_temp, path) = agent_native::create_temp_session_path("claude");
        let path = agent_native::normalize_session_log_path(&path);
        let process = process(42, 10, "claude", 60.0);
        let session = session("local:claude:one", "claude", &path, 990_000);
        let mut matcher = SessionProcessMatcher::default();
        let fd = HashMap::from([(process.tree.root, BTreeSet::from([path.clone()]))]);

        let matches =
            matcher.match_sessions(&[session], &[process], &fd, &HashMap::new(), 1_000_000);

        let matched = matches.by_session_id.get("local:claude:one").unwrap();
        assert_eq!(matched.root_pid, 42);
        assert_eq!(matched.pid_starttime_ticks, 10);
        assert_eq!(matched.evidence, TRACE_PROC_FD);
        assert_eq!(matched.source, SOURCE_VIEW_MATCH);
        assert!(matched.confidence >= 0.9);
    }

    #[test]
    fn does_not_bind_session_older_than_process_start() {
        let (_temp, path) = agent_native::create_temp_session_path("codex");
        let path = agent_native::normalize_session_log_path(&path);
        let process = process(7, 20, "codex", 60.0);
        let stale_session = session("local:codex:old", "codex", &path, 100_000);
        let mut matcher = SessionProcessMatcher::default();
        let fd = HashMap::from([(process.tree.root, BTreeSet::from([path]))]);

        let matches = matcher.match_sessions(
            &[stale_session],
            &[process],
            &fd,
            &HashMap::new(),
            1_000_000,
        );

        assert!(matches.by_session_id.is_empty());
        assert!(matches.used_root_pids.is_empty());
    }

    #[test]
    fn binding_sticks_only_for_same_pid_starttime_and_path() {
        let (_temp, path) = agent_native::create_temp_session_path("claude");
        let path = agent_native::normalize_session_log_path(&path);
        let first_process = process(1, 10, "claude", 60.0);
        let session = session("local:claude:one", "claude", &path, 990_000);
        let mut matcher = SessionProcessMatcher::default();
        let fd = HashMap::from([(first_process.tree.root, BTreeSet::from([path]))]);

        assert!(
            matcher
                .match_sessions(
                    std::slice::from_ref(&session),
                    std::slice::from_ref(&first_process),
                    &fd,
                    &HashMap::new(),
                    1_000_000,
                )
                .by_session_id
                .contains_key("local:claude:one")
        );

        let sticky = matcher.match_sessions(
            std::slice::from_ref(&session),
            std::slice::from_ref(&first_process),
            &HashMap::new(),
            &HashMap::new(),
            1_000_000,
        );
        assert_eq!(
            sticky.by_session_id["local:claude:one"].evidence,
            TRACE_STICKY_BINDING
        );

        let mut restarted_process = process(1, 11, "claude", 60.0);
        restarted_process.cwd = Some("/other".to_string());
        let restarted = matcher.match_sessions(
            &[session],
            &[restarted_process],
            &HashMap::new(),
            &HashMap::new(),
            1_000_000,
        );
        assert!(restarted.by_session_id.is_empty());
    }

    #[test]
    fn ignores_raw_paths_that_are_not_agent_session_logs() {
        let (_temp, path) = agent_native::create_temp_session_path("codex");
        let mut process = process(7, 20, "codex", 60.0);
        process.cwd = Some("/other".to_string());
        let session = session("local:codex:one", "codex", &path, 990_000);
        let mut matcher = SessionProcessMatcher::default();
        let fd = HashMap::from([(process.tree.root, BTreeSet::from([PathBuf::from("/tmp/x")]))]);

        let matches =
            matcher.match_sessions(&[session], &[process], &fd, &HashMap::new(), 1_000_000);

        assert!(matches.by_session_id.is_empty());
    }

    #[test]
    fn matches_recent_session_to_process_with_same_cwd_without_path_evidence() {
        let (_temp, path) = agent_native::create_temp_session_path("claude");
        let process = process(9, 30, "claude", 20.0);
        let session = session("local:claude:cwd", "claude", &path, 990_000);
        let mut matcher = SessionProcessMatcher::default();

        let matches = matcher.match_sessions(
            &[session],
            &[process],
            &HashMap::new(),
            &HashMap::new(),
            1_000_000,
        );

        let matched = matches.by_session_id.get("local:claude:cwd").unwrap();
        assert_eq!(matched.root_pid, 9);
        assert_eq!(matched.evidence, TRACE_RECENT_CWD);
        assert!(matched.confidence < 0.7);
    }

    #[test]
    fn path_evidence_wins_over_cwd_fallback_for_same_process() {
        let (_temp_a, path_a) = agent_native::create_temp_session_path("claude");
        let (_temp_b, path_b) = agent_native::create_temp_session_path("claude");
        let path_a = agent_native::normalize_session_log_path(&path_a);
        let path_b = agent_native::normalize_session_log_path(&path_b);
        let process = process(11, 40, "claude", 20.0);
        let session_a = session("local:claude:a", "claude", &path_a, 990_000);
        let session_b = session("local:claude:b", "claude", &path_b, 990_000);
        let mut matcher = SessionProcessMatcher::default();
        let fd = HashMap::from([(process.tree.root, BTreeSet::from([path_b]))]);

        let matches = matcher.match_sessions(
            &[session_a, session_b],
            &[process],
            &fd,
            &HashMap::new(),
            1_000_000,
        );

        assert!(!matches.by_session_id.contains_key("local:claude:a"));
        assert_eq!(
            matches.by_session_id["local:claude:b"].evidence,
            TRACE_PROC_FD
        );
    }
}
