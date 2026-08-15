// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Projection of the live top rows into bridge host-session rows.
//!
//! The rows themselves come from [`crate::view::live_top::LiveView`] — the same
//! registry `agentsight top` renders and the web overview serves — so nothing
//! here scans processes or reads transcripts on its own. What it does is decide
//! what a consumer outside this process is allowed to see, under the same
//! `as-redact/v1` rules the bridge mutations already follow: a workspace becomes
//! a class and a basename, a command becomes an executable basename, and
//! anything the collector did not observe stays absent instead of becoming zero.

use agentsight_capture::bridge::metadata;
use agentsight_protocol::bridge::HostSessionRow;
use std::collections::HashMap;

use crate::model::{SessionRow, Snapshot};
use crate::output::AgentTopRow;
use crate::sources::proc::{self as procfs, ProcSnapshot};

/// Upper bound on the sessions one snapshot describes. The answer is a single
/// bounded frame, not a stream, so the registry truncates rather than grow one.
/// The same bound the web overview refreshes with, because it is the same
/// registry doing the same transcript work.
pub(crate) const HOST_SESSION_LIMIT: usize = 25;

/// How recently a session must have spoken to count as `live` rather than
/// `idle` while its process is still running.
const LIVE_WITHIN_MS: u64 = 120_000;

/// Project one snapshot of top rows.
pub(crate) fn project_rows(
    rows: &[AgentTopRow],
    sessions: &Snapshot,
    sample: Option<&ProcSnapshot>,
    now_ms: u64,
) -> Vec<HostSessionRow> {
    let by_display = sessions
        .sessions
        .iter()
        .map(|session| (display_key(session), session))
        .collect::<HashMap<_, _>>();
    rows.iter()
        .take(HOST_SESSION_LIMIT)
        .map(|row| {
            project_row(
                row,
                by_display.get(row.session.as_str()).copied(),
                sample,
                now_ms,
            )
        })
        .collect()
}

/// The key `live_top` builds an [`AgentTopRow::session`] from, so a projected
/// row can find the session row it came from without re-deriving either.
fn display_key(session: &SessionRow) -> &str {
    session
        .attributes
        .get("display_id")
        .and_then(serde_json::Value::as_str)
        .filter(|value| !value.is_empty())
        .unwrap_or(session.id.as_str())
}

fn project_row(
    row: &AgentTopRow,
    session: Option<&SessionRow>,
    sample: Option<&ProcSnapshot>,
    now_ms: u64,
) -> HostSessionRow {
    let evidence = row.evidence();
    let start_ticks = row
        .pid
        .and_then(|pid| sample?.procs.get(&pid))
        .map(|proc_info| proc_info.starttime_ticks)
        .filter(|ticks| *ticks > 0);
    let last_message_ms = row
        .last_message_at
        .as_deref()
        .and_then(epoch_ms_from_rfc3339)
        .or_else(|| session.and_then(|session| session.end_timestamp_ms));
    // A row with no counting evidence source has an unknown count, and a
    // counted row that reached zero is indistinguishable here from a counter
    // that was never populated — so only a positive count is reported.
    let counted = evidence.agent_native || evidence.ebpf;
    let activity_events = counted
        .then(|| (row.tools + row.execs + row.files + row.network) as u64)
        .filter(|events| *events > 0);

    HostSessionRow {
        session_key: session_key(row, start_ticks),
        agent_kind: row.agent.clone(),
        state: state(row, last_message_ms, now_ms).to_string(),
        started_ms: session
            .map(|session| session.start_timestamp_ms)
            .or_else(|| start_ticks.and_then(procfs::process_start_timestamp_ms)),
        last_message_ms,
        model: row.model.clone(),
        input_tokens: session.map(|session| session.input_tokens).filter(positive),
        output_tokens: session
            .map(|session| session.output_tokens)
            .filter(positive),
        total_tokens: row.tokens,
        activity_events,
        // The counts are everything the collector attributed to the session
        // since it started observing it, so the window they cover is the row's
        // own age. Absent when the age is unknown: a count with no window is
        // still true, a count with a guessed window is not.
        activity_window_s: activity_events
            .and(row.age_s)
            .map(|age_s| age_s.max(0.0).round() as u64),
        cpu_percent: evidence.proc.then_some(row.cpu_percent),
        memory_bytes: evidence.proc.then(|| row.rss_mb.saturating_mul(1_048_576)),
        evidence_source: evidence_source(row).to_string(),
        workspace_class: row.workspace.as_deref().and_then(metadata::workspace_class),
        context_class: context_class(row),
        pid: row.pid,
        start_ticks,
    }
}

fn positive(value: &i64) -> bool {
    *value > 0
}

/// The agent's own session id when the collector knows it, otherwise the
/// pid/start-ticks pair, which survives pid reuse. The display id is the last
/// resort: it is opaque (`codex:019f49.fd456`) and stable for a transcript that
/// never bound to a process.
fn session_key(row: &AgentTopRow, start_ticks: Option<u64>) -> String {
    if let Some(session_id) = row.session_id.as_deref().filter(|id| !id.is_empty()) {
        return session_id.to_string();
    }
    match (row.pid, start_ticks) {
        (Some(pid), Some(start_ticks)) => format!("proc:{pid}:{start_ticks}"),
        _ => row.session.clone(),
    }
}

fn state(row: &AgentTopRow, last_message_ms: Option<u64>, now_ms: u64) -> &'static str {
    if !row.evidence().proc {
        return HostSessionRow::STOPPED;
    }
    let spoke_recently =
        last_message_ms.is_some_and(|at_ms| now_ms.saturating_sub(at_ms) <= LIVE_WITHIN_MS);
    if spoke_recently || row.cpu_percent > 0.0 {
        HostSessionRow::LIVE
    } else {
        HostSessionRow::IDLE
    }
}

/// The strongest source behind the row, most specific first.
fn evidence_source(row: &AgentTopRow) -> &'static str {
    let evidence = row.evidence();
    if evidence.ebpf {
        HostSessionRow::EVIDENCE_EBPF
    } else if evidence.agent_native {
        HostSessionRow::EVIDENCE_TRANSCRIPT
    } else {
        HostSessionRow::EVIDENCE_PROC
    }
}

/// Executable basename of the process behind the row.
///
/// Deliberately not derived from [`AgentTopRow::command`]: for an agent-native
/// row that field is the session's prompt preview, which is the user's own text
/// and must never cross the bridge. The process rows carry the real executable,
/// and when there is no process there is no context to report.
fn context_class(row: &AgentTopRow) -> Option<String> {
    let process = row
        .process_details
        .iter()
        .find(|process| Some(process.pid) == row.pid)
        .or_else(|| row.process_details.first())?;
    metadata::executable_basename(&process.command)
        .or_else(|| metadata::executable_basename(&process.comm))
}

fn epoch_ms_from_rfc3339(value: &str) -> Option<u64> {
    let parsed = chrono::DateTime::parse_from_rfc3339(value).ok()?;
    u64::try_from(parsed.timestamp_millis()).ok()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::output::AgentProcessRow;

    fn top_row() -> AgentTopRow {
        AgentTopRow {
            session_id: Some("6c3f1f2e-0000-4000-8000-000000000001".to_string()),
            session: "claude:6c3f1f".to_string(),
            agent: "claude".to_string(),
            pid: Some(4242),
            model: Some("claude-opus-4".to_string()),
            age_s: Some(90.4),
            cpu_percent: 12.5,
            rss_mb: 512,
            processes: 2,
            tokens: Some(1540),
            tools: 3,
            trace: "agent-native+proc+proc_fd".to_string(),
            command: "Fix the auth bug in /Users/redacteduser/secret-project/src/main.rs"
                .to_string(),
            workspace: Some("/Users/redacteduser/secret-project".to_string()),
            process_details: vec![AgentProcessRow {
                pid: 4242,
                ppid: 1,
                comm: "claude".to_string(),
                command: "/usr/local/bin/claude --api-key=sk-canary --model opus".to_string(),
                cwd: Some("/Users/redacteduser/secret-project".to_string()),
                ..AgentProcessRow::default()
            }],
            ..AgentTopRow::default()
        }
    }

    /// The planted canaries: a workspace under a named home directory, and an
    /// argument vector carrying a secret. Neither may appear on the wire in any
    /// form beyond a class and an executable basename.
    #[test]
    fn a_projected_row_carries_no_path_and_no_argument_beyond_the_executable() {
        let projected = project_row(&top_row(), None, None, 1_760_000_100_000);

        assert_eq!(
            projected.workspace_class.as_deref(),
            Some("repo:secret-project")
        );
        assert_eq!(projected.context_class.as_deref(), Some("claude"));

        let json = serde_json::to_string(&projected).expect("row serializes");
        for leaked in [
            "sk-canary",
            "api-key",
            "redacteduser",
            "/Users/",
            "/usr/local/bin",
            "--model",
            "Fix the auth bug",
        ] {
            assert!(!json.contains(leaked), "{leaked} leaked into {json}");
        }
    }

    #[test]
    fn a_transcript_backed_row_keeps_the_session_id_as_its_key() {
        let projected = project_row(&top_row(), None, None, 1_760_000_100_000);
        assert_eq!(
            projected.session_key,
            "6c3f1f2e-0000-4000-8000-000000000001"
        );
        assert_eq!(
            projected.evidence_source,
            HostSessionRow::EVIDENCE_TRANSCRIPT
        );
    }

    #[test]
    fn a_process_only_row_is_keyed_by_pid_and_start_ticks() {
        let row = AgentTopRow {
            session_id: None,
            session: "proc:4310".to_string(),
            agent: "codex".to_string(),
            pid: Some(4310),
            trace: "proc".to_string(),
            ..AgentTopRow::default()
        };
        let sample = ProcSnapshot {
            procs: std::collections::BTreeMap::from([(
                4310,
                procfs::ProcInfo {
                    pid: 4310,
                    starttime_ticks: 918_500,
                    ..Default::default()
                },
            )]),
            ..Default::default()
        };

        let projected = project_row(&row, None, Some(&sample), 1_760_000_100_000);

        assert_eq!(projected.session_key, "proc:4310:918500");
        assert_eq!(projected.start_ticks, Some(918_500));
        assert_eq!(projected.evidence_source, HostSessionRow::EVIDENCE_PROC);
        // No transcript and no kernel capture behind the row: the event count is
        // unknown, and unknown is absent rather than zero.
        assert_eq!(projected.activity_events, None);
        assert_eq!(projected.activity_window_s, None);
        assert_eq!(projected.total_tokens, None);
    }

    #[test]
    fn a_row_without_a_live_process_reports_no_measurement() {
        let row = AgentTopRow {
            trace: "agent-native".to_string(),
            cpu_percent: 0.0,
            rss_mb: 0,
            ..top_row()
        };
        let projected = project_row(&row, None, None, 1_760_000_100_000);

        assert_eq!(projected.state, HostSessionRow::STOPPED);
        assert_eq!(projected.cpu_percent, None);
        assert_eq!(projected.memory_bytes, None);
    }

    #[test]
    fn state_separates_a_quiet_process_from_a_speaking_one() {
        let now_ms = 1_760_000_100_000;
        let quiet = AgentTopRow {
            cpu_percent: 0.0,
            last_message_at: None,
            ..top_row()
        };
        assert_eq!(
            project_row(&quiet, None, None, now_ms).state,
            HostSessionRow::IDLE
        );

        // A minute before `now_ms`: inside the live window.
        let speaking = AgentTopRow {
            cpu_percent: 0.0,
            last_message_at: Some("2025-10-09T08:54:00Z".to_string()),
            ..top_row()
        };
        let projected = project_row(&speaking, None, None, now_ms);
        assert_eq!(projected.last_message_ms, Some(1_760_000_040_000));
        assert_eq!(projected.state, HostSessionRow::LIVE);

        // Ten minutes before it: outside the window, so the process is idle.
        let stale = AgentTopRow {
            cpu_percent: 0.0,
            last_message_at: Some("2025-10-09T08:45:00Z".to_string()),
            ..top_row()
        };
        assert_eq!(
            project_row(&stale, None, None, now_ms).state,
            HostSessionRow::IDLE
        );
    }

    #[test]
    fn session_counters_come_from_the_session_row_and_skip_unobserved_zeros() {
        let session = SessionRow {
            id: "local:claude:claude:6c3f1f".to_string(),
            agent_type: "claude".to_string(),
            start_timestamp_ms: 1_760_000_000_000,
            input_tokens: 1200,
            output_tokens: 0,
            total_tokens: 1200,
            attributes: serde_json::json!({ "display_id": "claude:6c3f1f" }),
            ..Default::default()
        };
        let rows = vec![top_row()];
        let snapshot = Snapshot {
            sessions: vec![session],
            ..Snapshot::empty("test")
        };

        let projected = project_rows(&rows, &snapshot, None, 1_760_000_100_000);

        assert_eq!(projected.len(), 1);
        assert_eq!(projected[0].input_tokens, Some(1200));
        assert_eq!(projected[0].output_tokens, None);
        assert_eq!(projected[0].started_ms, Some(1_760_000_000_000));
        assert_eq!(projected[0].activity_events, Some(3));
        assert_eq!(projected[0].activity_window_s, Some(90));
    }
}
