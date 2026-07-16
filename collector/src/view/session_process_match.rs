// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::SessionRow;
use crate::sources::proc::ProcessKey;
use serde_json::Value;
use std::collections::{BTreeSet, HashMap};
use std::path::{Path, PathBuf};

pub(crate) use agent_session::{LiveProcessCandidate, SessionProcessMatch, SessionProcessMatches};

#[derive(Default)]
pub(crate) struct SessionProcessMatcher {
    inner: agent_session::SessionProcessMatcher,
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
        let inputs = sessions
            .iter()
            .filter_map(session_input)
            .collect::<Vec<_>>();
        self.inner.match_sessions(
            &inputs,
            processes,
            fd_paths_by_process,
            ebpf_path_by_process,
            now_ms,
        )
    }
}

pub(crate) fn session_path_from_raw_path(path: &Path) -> Option<PathBuf> {
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
