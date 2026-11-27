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
        // A long-lived host (Codex Desktop's `app-server`, for example) keeps
        // every conversation's log open, so one process can link to several
        // sessions. Taking the first process in iteration order picked an
        // arbitrary one — the path-evidence map is keyed path-lexically — and
        // then marked that pid used, so an older conversation could hold the
        // binding while the current one looked idle. Rank the candidates and
        // let the freshest session win its process instead.
        let mut candidates = Vec::new();
        for (session_index, session) in sessions.iter().enumerate() {
            for (process_index, process) in processes.iter().enumerate() {
                if process.agent != session.agent
                    || !session_is_fresh_enough_for_process(session, process, now_ms)
                {
                    continue;
                }
                if let Some(evidence) = self.lookup_trace(&session.path, process, &path_evidence) {
                    candidates.push((
                        std::cmp::Reverse(session_end_ms(session)),
                        confidence_for_evidence(evidence),
                        session_index,
                        process_index,
                        evidence,
                    ));
                }
            }
        }
        candidates.sort_by(|left, right| {
            left.0
                .cmp(&right.0)
                .then_with(|| right.1.total_cmp(&left.1))
                .then_with(|| left.2.cmp(&right.2))
                .then_with(|| left.3.cmp(&right.3))
        });
        for (_, _, session_index, process_index, evidence) in candidates {
            let session = &sessions[session_index];
            let process = &processes[process_index];
            if out.by_session_id.contains_key(&session.id)
                || out.used_root_pids.contains(&process.tree.root.pid)
            {
                continue;
            }
            record_match(&mut out, session, process, evidence);
            self.bindings.insert(
                process.tree.root.pid,
                LiveSessionBinding {
                    starttime_ticks: process.tree.root.starttime_ticks,
                    session_path: normalize_session_log_path(&session.path),
                },
            );
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

    /// Evidence for linking this session path to this process, without
    /// recording a binding. `match_sessions` collects every candidate first
    /// and binds only the winners, so a lookup must not mutate the table.
    fn lookup_trace(
        &self,
        session_path: &Path,
        process: &LiveProcessCandidate,
        path_evidence: &HashMap<u32, BTreeMap<PathBuf, &'static str>>,
    ) -> Option<&'static str> {
        let pid = process.tree.root.pid;
        let path = normalize_session_log_path(session_path);
        if let Some(evidence) = path_evidence.get(&pid) {
            return evidence.get(&path).copied();
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

    fn codex_log_path(root: &Path, name: &str) -> PathBuf {
        let dir = root.join(".codex/sessions/2026/11/18");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join(name);
        std::fs::write(&path, "{}\n").unwrap();
        path
    }

    fn host_process(paths: &[PathBuf]) -> (LiveProcessCandidate, HashMap<ProcessKey, BTreeSet<PathBuf>>) {
        let root = ProcessKey {
            pid: 4242,
            starttime_ticks: 7,
        };
        let process = LiveProcessCandidate {
            tree: ProcessTree {
                root,
                members: vec![root],
            },
            agent: "codex".to_string(),
            age_s: Some(600.0),
            cwd: None,
        };
        let mut fd_paths = HashMap::new();
        fd_paths.insert(
            root,
            paths.iter().cloned().collect::<BTreeSet<_>>(),
        );
        (process, fd_paths)
    }

    #[test]
    fn shared_host_binds_the_freshest_session_not_the_lexically_first() {
        let root =
            std::env::temp_dir().join(format!("agent-session-bind-test-{}", std::process::id()));
        std::fs::create_dir_all(&root).unwrap();
        // The older conversation's file name sorts first, so a first-match
        // scan over the path-keyed evidence map picks it.
        let old_path = codex_log_path(&root, "a-old.jsonl");
        let new_path = codex_log_path(&root, "b-new.jsonl");
        let (process, fd_paths) = host_process(&[old_path.clone(), new_path.clone()]);
        let sessions = vec![
            SessionProcessInput {
                id: "old".to_string(),
                agent: "codex".to_string(),
                path: old_path.clone(),
                start_timestamp_ms: Some(1_000),
                end_timestamp_ms: Some(2_000),
                cwd: None,
            },
            SessionProcessInput {
                id: "new".to_string(),
                agent: "codex".to_string(),
                path: new_path.clone(),
                start_timestamp_ms: Some(3_000),
                end_timestamp_ms: Some(4_000),
                cwd: None,
            },
        ];

        let matches = SessionProcessMatcher::default().match_sessions(
            &sessions,
            &[process],
            &fd_paths,
            &HashMap::new(),
            5_000,
        );

        assert!(
            matches.by_session_id.contains_key("new"),
            "the current conversation must keep the host process"
        );
        assert!(
            !matches.by_session_id.contains_key("old"),
            "a finished conversation must not hold the live binding"
        );
        std::fs::remove_dir_all(&root).unwrap();
    }
}
