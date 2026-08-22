// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::SessionRow;
use crate::sources::proc::{self as procfs, ProcessKey, ProcessTree};
use crate::view::process_select;
use agent_session::AgentSession;
use serde_json::Value;
use std::collections::{BTreeSet, HashMap, HashSet};
use std::path::{Path, PathBuf};

pub use agent_session::{SessionProcessMatch, SessionProcessMatches};

#[derive(Debug, Clone, Default)]
pub struct LiveProcessCandidate {
    pub tree: ProcessTree,
    pub agent: String,
    pub age_s: Option<f64>,
    pub cwd: Option<String>,
}

#[derive(Default)]
pub struct SessionProcessMatcher {
    inner: agent_session::SessionProcessMatcher,
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
        let sessions = sessions.iter().filter_map(session_input).collect::<Vec<_>>();
        let processes = processes
            .iter()
            .map(|process| agent_session::LiveProcessCandidate {
                tree: session_tree(&process.tree),
                agent: process.agent.clone(),
                age_s: process.age_s,
                cwd: process.cwd.clone(),
            })
            .collect::<Vec<_>>();
        self.inner.match_sessions(
            &sessions,
            &processes,
            &session_keyed(fd_paths_by_process),
            &session_keyed(ebpf_path_by_process),
            now_ms,
        )
    }
}

/// Check whether provider control is about to resume a session that is already live.
pub fn session_is_running(session: &AgentSession) -> bool {
    let Ok(sample) = procfs::ProcSnapshot::collect() else {
        return false;
    };
    let children = sample.children_by_ppid();
    let roots = process_select::live_root_pids(&sample, None, None);
    let root_set = roots.iter().copied().collect::<HashSet<_>>();
    let processes = roots
        .into_iter()
        .filter_map(|root_pid| {
            let root = sample.procs.get(&root_pid)?;
            (process_select::known_agent_label(&root.comm, &root.command)
                == Some(session.agent_type.as_str()))
            .then(|| LiveProcessCandidate {
                tree: ProcessTree {
                    root: root.process_key(),
                    members: procfs::process_family_excluding(
                        root_pid,
                        &children,
                        &sample.procs,
                        &root_set,
                    )
                    .into_iter()
                    .filter_map(|pid| sample.procs.get(&pid).map(procfs::ProcInfo::process_key))
                    .collect(),
                },
                agent: session.agent_type.clone(),
                age_s: Some(procfs::process_age_s(root, &sample)),
                cwd: root.cwd.as_ref().map(|path| path.to_string_lossy().to_string()),
            })
        })
        .collect::<Vec<_>>();
    let trees = processes.iter().map(|process| process.tree.clone()).collect::<Vec<_>>();
    let row = SessionRow {
        id: session.session_id.clone(),
        agent_type: session.agent_type.clone(),
        start_timestamp_ms: session.start_timestamp_ms.unwrap_or_default(),
        end_timestamp_ms: session.end_timestamp_ms,
        attributes: serde_json::json!({
            "path": session.path.to_string_lossy(),
            "cwd": session.cwd.as_deref(),
        }),
        ..Default::default()
    };
    SessionProcessMatcher::default()
        .match_sessions(
            &[row],
            &processes,
            &procfs::collect_fd_paths(&trees),
            &HashMap::new(),
            now_ms(),
        )
        .by_session_id
        .contains_key(&session.session_id)
}

pub fn session_path_from_raw_path(path: &Path) -> Option<PathBuf> {
    agent_session::session_log_path_from_str(&path.to_string_lossy())
}

fn session_input(session: &SessionRow) -> Option<agent_session::SessionProcessInput> {
    Some(agent_session::SessionProcessInput {
        id: session.id.clone(),
        agent: session.agent_type.clone(),
        path: session_path(session)?.to_path_buf(),
        start_timestamp_ms: Some(session.start_timestamp_ms),
        end_timestamp_ms: session.end_timestamp_ms,
        cwd: session
            .attributes
            .get("cwd")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(ToString::to_string),
    })
}

fn session_path(session: &SessionRow) -> Option<&Path> {
    session
        .attributes
        .get("path")
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .map(Path::new)
}

fn session_tree(tree: &ProcessTree) -> agent_session::ProcessTree {
    agent_session::ProcessTree {
        root: session_key(tree.root),
        members: tree.members.iter().copied().map(session_key).collect(),
    }
}

fn session_key(key: ProcessKey) -> agent_session::ProcessKey {
    agent_session::ProcessKey {
        pid: key.pid,
        starttime_ticks: key.starttime_ticks,
    }
}

fn session_keyed<T: Clone>(map: &HashMap<ProcessKey, T>) -> HashMap<agent_session::ProcessKey, T> {
    map.iter().map(|(key, value)| (session_key(*key), value.clone())).collect()
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
