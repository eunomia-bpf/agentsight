// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::{AuditCounters, SessionRow, Snapshot};
use crate::output::{AgentTopOutput, AgentTopRow, TopOptions};
use crate::sources::agent_native as agent_native_sessions;
use crate::sources::proc::{self as procfs, ProcSnapshot as LiveSample};
use crate::view::process_select;
use crate::view::session_process_match::{
    LiveProcessCandidate, SessionProcessMatch, SessionProcessMatcher, session_path_from_raw_path,
};
use crate::view::top::{recent_failures, sort_agent_rows, top_sections};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::io;
use std::path::{Path, PathBuf};
use std::time::Duration;

#[derive(Debug, Clone)]
pub(crate) struct LiveCaptureSnapshot {
    snapshot: Snapshot,
    parse_errors: u64,
}

impl Default for LiveCaptureSnapshot {
    fn default() -> Self {
        Self {
            snapshot: Snapshot::empty("live_capture"),
            parse_errors: 0,
        }
    }
}

impl LiveCaptureSnapshot {
    pub(crate) fn new(snapshot: Snapshot, parse_errors: u64) -> Self {
        Self {
            snapshot,
            parse_errors,
        }
    }
}

pub(crate) struct LiveView {
    previous: Option<LiveSample>,
    matcher: SessionProcessMatcher,
    session_cache: agent_native_sessions::SessionCache,
}

impl Default for LiveView {
    fn default() -> Self {
        Self {
            previous: None,
            matcher: SessionProcessMatcher::default(),
            session_cache: agent_native_sessions::SessionCache::new(),
        }
    }
}

impl LiveView {
    pub(crate) fn refresh(
        &mut self,
        capture: Option<&LiveCaptureSnapshot>,
        limit: usize,
        options: &TopOptions,
    ) -> io::Result<AgentTopOutput<'static>> {
        let sample = LiveSample::collect()?;
        let session_snapshot = agent_native_sessions::snapshot(
            &mut self.session_cache,
            options.pid,
            options.comm.as_deref(),
            limit,
            Duration::from_secs(2),
        );
        let top = self.build_top(&sample, capture, &session_snapshot, options);
        self.previous = Some(sample);
        Ok(top)
    }

    fn build_top<'a>(
        &mut self,
        sample: &LiveSample,
        capture: Option<&LiveCaptureSnapshot>,
        session_snapshot: &Snapshot,
        options: &TopOptions,
    ) -> AgentTopOutput<'a> {
        let children = sample.children_by_ppid();
        let mut live_rows = live_process_rows(sample, self.previous.as_ref(), options, &children);
        sort_agent_rows(&mut live_rows, "cpu");
        let process_candidates = live_process_candidates(sample, &live_rows, &children);
        let process_trees = process_candidates
            .iter()
            .map(|candidate| candidate.tree.clone())
            .collect::<Vec<_>>();
        let fd_paths_by_process = procfs::collect_fd_paths(&process_trees);
        let ebpf_path_by_process = capture
            .map(|capture| ebpf_paths_by_process(capture, &process_trees))
            .unwrap_or_default();
        let matches = self.matcher.match_sessions(
            &session_snapshot.sessions,
            &process_candidates,
            &fd_paths_by_process,
            &ebpf_path_by_process,
            now_ms(),
        );
        let live_rows_by_pid = live_rows
            .iter()
            .filter_map(|row| row.pid.map(|pid| (pid, row)))
            .collect::<HashMap<_, _>>();
        let mut rows = Vec::new();

        for session in &session_snapshot.sessions {
            let session_path = session_attr(session, "path").map(PathBuf::from);
            let live = matches.by_session_id.get(&session.id).and_then(|matched| {
                live_rows_by_pid
                    .get(&matched.root_pid)
                    .map(|row| ((*row).clone(), matched))
            });
            if options.pid.is_some() && live.is_none() {
                continue;
            }
            let command = session_attr(session, "prompt_preview")
                .map(ToString::to_string)
                .or_else(|| live.as_ref().map(|(row, _)| row.command.clone()))
                .or_else(|| session_path.as_ref().map(|path| path.display().to_string()))
                .unwrap_or_else(|| session.id.clone());
            let trace = if let Some((_, matched)) = &live {
                session_process_trace(matched, &session.id)
            } else {
                "agent-native".to_string()
            };
            let age_s = live
                .as_ref()
                .and_then(|(row, _)| row.age_s)
                .or_else(|| session_age_s(session));
            let tools = session_snapshot
                .tool_calls
                .iter()
                .filter(|tool| tool.session_id.as_deref() == Some(session.id.as_str()))
                .count();
            let workspace = session_attr(session, "cwd")
                .map(ToString::to_string)
                .or_else(|| {
                    live.as_ref()
                        .and_then(|(row, _)| row.workspace.as_ref())
                        .cloned()
                });
            let tool_breakdown = {
                let mut counts = BTreeMap::new();
                for tool in session_snapshot
                    .tool_calls
                    .iter()
                    .filter(|t| t.session_id.as_deref() == Some(session.id.as_str()))
                {
                    if let Some(name) = &tool.tool_name {
                        *counts.entry(name.clone()).or_insert(0i64) += 1;
                    }
                }
                crate::output::sorted_top_counts(counts, 10)
            };
            let file_breakdown = session
                .attributes
                .get("files")
                .and_then(|v| v.as_object())
                .map(|m| {
                    let counts: BTreeMap<String, i64> = m
                        .iter()
                        .map(|(k, v)| (k.clone(), v.as_i64().unwrap_or(1)))
                        .collect();
                    crate::output::sorted_top_counts(counts, 10)
                })
                .unwrap_or_default();
            rows.push(AgentTopRow {
                session: session_attr(session, "display_id")
                    .unwrap_or(session.id.as_str())
                    .to_string(),
                agent: session.agent_type.clone(),
                pid: live.as_ref().and_then(|(row, _)| row.pid),
                model: session.model.clone(),
                age_s,
                cpu_percent: live
                    .as_ref()
                    .map(|(row, _)| row.cpu_percent)
                    .unwrap_or_default(),
                rss_mb: live.as_ref().map(|(row, _)| row.rss_mb).unwrap_or_default(),
                processes: live
                    .as_ref()
                    .map(|(row, _)| row.processes)
                    .unwrap_or_default(),
                tokens: (session.total_tokens > 0).then_some(session.total_tokens),
                tools,
                execs: 0,
                failures: 0,
                files: session
                    .attributes
                    .get("files")
                    .and_then(|v| v.as_object())
                    .map(|m| m.len())
                    .unwrap_or(0),
                network: 0,
                unattributed: 0,
                trace,
                command,
                workspace,
                last_message_at: session_attr(session, "last_message_at").map(ToString::to_string),
                tool_breakdown,
                file_breakdown,
            });
        }

        let remaining_live: Vec<_> = live_rows
            .into_iter()
            .filter(|row| {
                row.pid
                    .map(|pid| !matches.used_root_pids.contains(&pid))
                    .unwrap_or(true)
            })
            .collect();
        rows.extend(remaining_live);

        if let Some(capture) = capture {
            apply_live_capture(&mut rows, sample, capture, &children);
        }

        let local_summary = &session_snapshot.summary;
        let local_total_tokens = local_summary.total_tokens;
        let capture_summary = capture.map(|capture| &capture.snapshot.summary);
        let capture_total_tokens = capture
            .map(|capture| capture.snapshot.summary.total_tokens)
            .unwrap_or_default();
        let has_agent_native = rows.iter().any(|row| row.evidence().agent_native);
        let has_proc = rows.iter().any(|row| row.evidence().proc);
        let has_ebpf = rows.iter().any(|row| row.evidence().ebpf);
        let has_session_file_link = rows
            .iter()
            .any(|row| row.evidence().has_session_path_link());
        let mut notes = Vec::new();
        if has_agent_native {
            notes.push("agent-native sessions are the primary token/tool source".to_string());
        }
        if has_proc {
            notes.push("proc evidence uses /proc for CPU/RSS/process families".to_string());
        }
        if has_session_file_link {
            notes.push("agent-native sessions bind to live pids after the process touches the matching session path; binding stays until pid exits or a new session path is observed".to_string());
        }
        if has_ebpf {
            notes.push(
                "ebpf evidence is live process capture; SSL payload details still require record/stat"
                    .to_string(),
            );
        }
        if let Some(capture) = capture
            && capture.parse_errors > 0
        {
            notes.push(format!(
                "ebpf process capture had {} parse errors",
                capture.parse_errors
            ));
        }
        if rows.is_empty() {
            if options.pid.is_some() || options.comm.is_some() {
                notes.push(
                    "no active process or agent-native session matched the filter; try another -p/-c value or inspect a saved session with --db"
                        .to_string(),
                );
            } else {
                notes.push(
                    "no active known agent process or agent-native Claude/Codex/Gemini session found; use -c/-p, run an agent, or pass --db"
                        .to_string(),
                );
            }
        }

        let mut sections = top_sections(session_snapshot, rows.len().max(10), &options.view);
        if let Some(network_section) = capture
            .map(|capture| top_sections(&capture.snapshot, rows.len().max(10), &options.view))
            .into_iter()
            .flatten()
            .find(|(title, _, items)| *title == "Network" && !items.is_empty())
        {
            if let Some(position) = sections
                .iter()
                .position(|(title, _, _)| *title == "Network")
            {
                sections[position] = network_section;
            } else {
                sections.push(network_section);
            }
        }
        if !sections
            .iter()
            .any(|(t, _, items)| *t == "Processes" && !items.is_empty())
        {
            let proc_counts: Vec<_> = {
                let mut counts = BTreeMap::new();
                for row in &rows {
                    *counts.entry(row.agent.clone()).or_insert(0i64) += row.processes.max(1) as i64;
                }
                let mut sorted: Vec<_> = counts.into_iter().collect();
                sorted.sort_by_key(|b| std::cmp::Reverse(b.1));
                sorted
            };
            if !proc_counts.is_empty() {
                sections.retain(|(t, _, _)| *t != "Processes");
                sections.insert(0, ("Processes", "tree", proc_counts));
            }
        }
        let failures = recent_failures(session_snapshot, 5);

        AgentTopOutput {
            mode: "live sessions",
            db: None,
            duration_s: 0.0,
            view_events: local_summary.view_events
                + capture_summary
                    .map(|summary| summary.view_events)
                    .unwrap_or_default(),
            llm_calls: local_summary.llm_calls
                + capture_summary
                    .map(|summary| summary.llm_calls)
                    .unwrap_or_default(),
            total_tokens: local_total_tokens + capture_total_tokens,
            rows,
            sections,
            failures,
            notes,
        }
    }
}

fn session_age_s(session: &SessionRow) -> Option<f64> {
    let timestamp_ms = session
        .end_timestamp_ms
        .or(Some(session.start_timestamp_ms))?;
    now_ms()
        .checked_sub(timestamp_ms)
        .map(|age_ms| age_ms as f64 / 1000.0)
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_millis() as u64)
        .unwrap_or_default()
}

fn session_attr<'a>(session: &'a SessionRow, key: &str) -> Option<&'a str> {
    session
        .attributes
        .get(key)
        .and_then(serde_json::Value::as_str)
        .filter(|value| !value.is_empty())
}

fn apply_live_capture(
    rows: &mut [AgentTopRow],
    sample: &LiveSample,
    capture: &LiveCaptureSnapshot,
    children: &HashMap<u32, Vec<u32>>,
) {
    let by_pid = AuditCounters::by_pid(&capture.snapshot.audit_events);
    if by_pid.is_empty() {
        return;
    }

    let mut attributed = HashSet::new();
    for row in rows.iter_mut() {
        let Some(root_pid) = row.pid else {
            continue;
        };
        let family = procfs::process_family(root_pid, children, &sample.procs);
        let mut counters = AuditCounters::default();
        for pid in family {
            if let Some(pid_counters) = by_pid.get(&pid) {
                counters.process_execs += pid_counters.process_execs;
                counters.process_exit_failure += pid_counters.process_exit_failure;
                counters.file_events += pid_counters.file_events;
                counters.network_events += pid_counters.network_events;
                attributed.insert(pid);
            }
        }
        if counters.process_execs == 0
            && counters.process_exit_failure == 0
            && counters.file_events == 0
            && counters.network_events == 0
        {
            continue;
        }
        row.execs += counters.process_execs;
        row.failures += counters.process_exit_failure;
        row.files += counters.file_events;
        row.network += counters.network_events;
        row.add_trace("ebpf");
    }

    let unattributed = by_pid
        .iter()
        .filter(|(pid, counters)| {
            !attributed.contains(pid)
                && (counters.process_execs > 0
                    || counters.process_exit_failure > 0
                    || counters.file_events > 0
                    || counters.network_events > 0)
        })
        .count();
    if unattributed == 0 {
        return;
    }
    if let Some(row) = rows.iter_mut().find(|row| row.evidence().ebpf) {
        row.unattributed += unattributed;
    }
}

fn ebpf_paths_by_process(
    capture: &LiveCaptureSnapshot,
    process_trees: &[procfs::ProcessTree],
) -> HashMap<procfs::ProcessKey, PathBuf> {
    let mut keys_by_pid = HashMap::new();
    for tree in process_trees {
        for key in &tree.members {
            if let Some(start_ms) = procfs::process_start_timestamp_ms(key.starttime_ticks) {
                keys_by_pid.insert(key.pid, (*key, start_ms));
            }
        }
    }

    let mut latest = HashMap::new();
    for row in capture
        .snapshot
        .audit_events
        .iter()
        .filter(|row| row.audit_type == "file")
    {
        let Some(pid) = row.pid else { continue };
        let Some((key, start_ms)) = keys_by_pid.get(&pid) else {
            continue;
        };
        if row.timestamp_ms < *start_ms {
            continue;
        }
        let Some(target) = row.target.as_ref().filter(|target| !target.is_empty()) else {
            continue;
        };
        let Some(session_path) = session_path_from_raw_path(Path::new(target)) else {
            continue;
        };
        let entry = latest
            .entry(*key)
            .or_insert_with(|| (row.timestamp_ms, session_path.clone()));
        if row.timestamp_ms >= entry.0 {
            *entry = (row.timestamp_ms, session_path);
        }
    }

    latest
        .into_iter()
        .map(|(key, (_, path))| (key, path))
        .collect()
}

fn live_process_candidates(
    sample: &LiveSample,
    live_rows: &[AgentTopRow],
    children: &HashMap<u32, Vec<u32>>,
) -> Vec<LiveProcessCandidate> {
    live_rows
        .iter()
        .filter_map(|row| {
            let root_pid = row.pid?;
            let tree = sample.process_tree(root_pid, children)?;
            Some(LiveProcessCandidate {
                tree,
                agent: row.agent.clone(),
                age_s: row.age_s,
                cwd: row.workspace.clone(),
            })
        })
        .collect()
}

fn session_process_trace(matched: &SessionProcessMatch, session_id: &str) -> String {
    debug_assert_eq!(matched.session_id, session_id);
    debug_assert!(matched.pid_starttime_ticks > 0);
    debug_assert_eq!(matched.source, agent_session::SOURCE_SESSION_PROCESS_MATCH);
    debug_assert!(matched.confidence > 0.0);
    format!("agent-native+proc+{}", matched.evidence)
}

fn live_process_rows(
    sample: &LiveSample,
    previous: Option<&LiveSample>,
    options: &TopOptions,
    children: &HashMap<u32, Vec<u32>>,
) -> Vec<AgentTopRow> {
    let roots = process_select::live_root_pids(sample, options.pid, options.comm.as_deref());
    let mut rows = Vec::new();

    for root_pid in roots {
        let family = procfs::process_family(root_pid, children, &sample.procs);
        if family.is_empty() {
            continue;
        }
        let root = sample.procs.get(&root_pid);
        let cpu_percent = family
            .iter()
            .filter_map(|pid| sample.procs.get(pid))
            .map(|proc_info| procfs::process_cpu_percent(proc_info, previous, sample))
            .sum();
        let rss_mb = family
            .iter()
            .filter_map(|pid| sample.procs.get(pid).map(|proc_info| proc_info.rss_mb))
            .sum();
        let agent = root
            .map(|proc_info| {
                process_select::agent_label_from_command(&proc_info.comm, &proc_info.command)
            })
            .unwrap_or_else(|| "agent".to_string());

        rows.push(AgentTopRow {
            session: format!("proc:{root_pid}"),
            agent,
            pid: Some(root_pid),
            model: None,
            age_s: root.map(|proc_info| procfs::process_age_s(proc_info, sample)),
            cpu_percent,
            rss_mb,
            processes: family.len(),
            tokens: None,
            tools: 0,
            execs: 0,
            failures: 0,
            files: 0,
            network: 0,
            unattributed: 0,
            trace: "proc".to_string(),
            command: root
                .map(|proc_info| proc_info.command.clone())
                .unwrap_or_else(|| "unknown".to_string()),
            workspace: root
                .and_then(|proc_info| proc_info.cwd.as_ref())
                .map(|path| path.to_string_lossy().to_string()),
            last_message_at: None,
            tool_breakdown: Vec::new(),
            file_breakdown: Vec::new(),
        });
    }

    rows
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::SnapshotOptions;
    use crate::sources::proc::ProcInfo;
    use serde_json::json;

    #[test]
    fn pid_filter_does_not_show_unbound_agent_native_sessions() {
        let (_temp, path) = agent_native_sessions::create_temp_session_path("claude");
        let session = agent_native_sessions::parse_content_for_test(
            "claude",
            &path,
            std::time::UNIX_EPOCH,
            "{\"type\":\"result\",\"modelUsage\":{\"claude-opus\":{\"inputTokens\":3,\"outputTokens\":4}}}\n",
        )
        .unwrap();
        let agent_native_sessions = vec![session];
        let session_snapshot = agent_native_sessions::materialized_view(&agent_native_sessions)
            .export_snapshot(SnapshotOptions { audit_limit: 10 });
        let options = TopOptions {
            pid: Some(1),
            comm: None,
            sort: "cpu".to_string(),
            view: "all".to_string(),
        };

        let mut live_view = LiveView::default();
        let sample = LiveSample {
            procs: BTreeMap::from([(
                1,
                ProcInfo {
                    pid: 1,
                    comm: "claude".to_string(),
                    starttime_ticks: 10,
                    ..Default::default()
                },
            )]),
            ..Default::default()
        };
        let top = live_view.build_top(&sample, None, &session_snapshot, &options);

        assert_eq!(top.rows.len(), 1);
        assert_eq!(top.rows[0].pid, Some(1));
        assert_eq!(top.rows[0].trace, "proc");
    }

    #[test]
    fn live_view_merges_recent_same_cwd_session_without_path_evidence() {
        let (_temp, path) = agent_native_sessions::create_temp_session_path("claude");
        let session = SessionRow {
            id: "local:claude:cwd".to_string(),
            agent_type: "claude".to_string(),
            start_timestamp_ms: now_ms().saturating_sub(10_000),
            end_timestamp_ms: Some(now_ms().saturating_sub(5_000)),
            attributes: json!({
                "path": path.to_string_lossy(),
                "display_id": "claude:cwd",
                "cwd": "/work",
            }),
            ..Default::default()
        };
        let session_snapshot = Snapshot {
            sessions: vec![session],
            ..Snapshot::empty("test")
        };
        let options = TopOptions {
            pid: None,
            comm: None,
            sort: "cpu".to_string(),
            view: "all".to_string(),
        };

        let mut live_view = LiveView::default();
        let sample = LiveSample {
            procs: BTreeMap::from([(
                42,
                ProcInfo {
                    pid: 42,
                    comm: "claude".to_string(),
                    cwd: Some(PathBuf::from("/work")),
                    starttime_ticks: u64::MAX,
                    ..Default::default()
                },
            )]),
            ..Default::default()
        };
        let top = live_view.build_top(&sample, None, &session_snapshot, &options);

        assert_eq!(top.rows.len(), 1);
        assert_eq!(top.rows[0].session, "claude:cwd");
        assert_eq!(top.rows[0].pid, Some(42));
        assert_eq!(top.rows[0].trace, "agent-native+proc+cwd_recent");
    }

    #[test]
    fn live_capture_snapshot_counts_events_by_pid() {
        let snapshot = Snapshot {
            audit_events: vec![crate::model::AuditEventRow {
                id: "a".to_string(),
                timestamp_ms: 1,
                audit_type: "file".to_string(),
                pid: Some(42),
                comm: Some("codex".to_string()),
                subject: Some("/tmp/x".to_string()),
                action: Some("open".to_string()),
                target: None,
                status: Some("ok".to_string()),
                summary: None,
                details: json!({}),
            }],
            ..Snapshot::empty("test")
        };

        let capture = LiveCaptureSnapshot::new(snapshot, 0);

        let by_pid = AuditCounters::by_pid(&capture.snapshot.audit_events);
        assert_eq!(by_pid.get(&42).unwrap().file_events, 1);
    }

    #[test]
    fn live_view_includes_capture_network_section() {
        let options = TopOptions {
            pid: None,
            comm: None,
            sort: "cpu".to_string(),
            view: "network".to_string(),
        };
        let sample = LiveSample {
            procs: BTreeMap::from([(
                42,
                ProcInfo {
                    pid: 42,
                    comm: "codex".to_string(),
                    starttime_ticks: 10,
                    ..Default::default()
                },
            )]),
            ..Default::default()
        };
        let capture = LiveCaptureSnapshot::new(
            Snapshot {
                audit_events: vec![crate::model::AuditEventRow {
                    id: "net-1".to_string(),
                    timestamp_ms: 1,
                    audit_type: "network".to_string(),
                    pid: Some(42),
                    comm: Some("codex".to_string()),
                    subject: Some("codex".to_string()),
                    action: Some("NET_CONNECT".to_string()),
                    target: Some("api.example.test:443".to_string()),
                    status: Some("observed".to_string()),
                    summary: None,
                    details: json!({}),
                }],
                ..Snapshot::empty("capture")
            },
            0,
        );

        let mut live_view = LiveView::default();
        let top = live_view.build_top(&sample, Some(&capture), &Snapshot::empty("local"), &options);

        assert_eq!(top.rows[0].network, 1);
        let network = top
            .sections
            .iter()
            .find(|(title, _, _)| *title == "Network")
            .unwrap();
        assert_eq!(network.2, vec![("api.example.test:443".to_string(), 1)]);
    }

    #[test]
    fn ebpf_paths_use_latest_current_process_session_file_audit() {
        let pid = std::process::id();
        let starttime_ticks = procfs::process_starttime_ticks(pid).unwrap();
        let key = procfs::ProcessKey {
            pid,
            starttime_ticks,
        };
        let start_ms = procfs::process_start_timestamp_ms(starttime_ticks).unwrap();
        let (_temp_first, first_path) = agent_native_sessions::create_temp_session_path("codex");
        let (_temp_latest, latest_path) = agent_native_sessions::create_temp_session_path("codex");
        let first_path = agent_session::normalize_session_log_path(&first_path);
        let latest_path = agent_session::normalize_session_log_path(&latest_path);
        let capture = LiveCaptureSnapshot::new(
            Snapshot {
                audit_events: vec![
                    audit_file(pid, start_ms.saturating_sub(1), &latest_path),
                    audit_file(pid, start_ms, &first_path),
                    audit_file(pid, start_ms + 1, "/tmp/project.rs"),
                    audit_file(pid, start_ms + 2, &latest_path),
                    audit_file(pid, start_ms + 3, "/tmp/project-later.rs"),
                ],
                ..Snapshot::empty("test")
            },
            0,
        );
        let tree = procfs::ProcessTree {
            root: key,
            members: vec![key],
        };

        let paths = ebpf_paths_by_process(&capture, &[tree]);

        assert_eq!(paths.get(&key).unwrap(), &latest_path);
    }

    fn audit_file(
        pid: u32,
        timestamp_ms: u64,
        target: impl AsRef<std::path::Path>,
    ) -> crate::model::AuditEventRow {
        crate::model::AuditEventRow {
            id: format!("audit-{timestamp_ms}"),
            timestamp_ms,
            audit_type: "file".to_string(),
            pid: Some(pid),
            comm: Some("codex".to_string()),
            subject: Some("codex".to_string()),
            action: Some("write".to_string()),
            target: Some(target.as_ref().to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: None,
            details: json!({}),
        }
    }
}
