// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::cli_db::load_agentsight_view;
use crate::model::{
    AuditCounters, ResourceSampleRow, SessionRow, Snapshot, SnapshotOptions, ViewResult,
};
use crate::output::{
    AgentTopOutput, AgentTopRow, ResourcePeaks, TopOptions, clear_screen, print_agent_top,
};
use crate::text::short_session_id;
use crate::view::top::{recent_failures, sort_agent_rows, top_sections};
use std::collections::BTreeSet;
use std::io::{self, Write};
use std::time::Duration;

#[cfg(test)]
use crate::sources::agent_native as agent_native_sessions;

pub(crate) fn run_top_query(
    db: &str,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let limit = limit.clamp(1, 50);
    let interval = Duration::from_secs(interval_secs.max(1));
    let mut iterations = 0u32;
    let should_clear_screen = count != Some(1);

    loop {
        let (snapshot, resources) = load_snapshot_and_resources(db)?;
        if should_clear_screen {
            clear_screen();
        }
        let mut top = build_session_top(db, &snapshot, &resources, limit, options);
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        io::stdout().flush()?;

        iterations += 1;
        if count.is_some_and(|max| iterations >= max) || crate::shutdown_requested() {
            break;
        }
        std::thread::sleep(interval);
    }

    Ok(())
}

pub(crate) fn load_top_output<'a>(
    db: &'a str,
    limit: usize,
    options: &TopOptions,
) -> Result<AgentTopOutput<'a>, Box<dyn std::error::Error + Send + Sync>> {
    let (snapshot, resources) = load_snapshot_and_resources(db)?;
    Ok(build_session_top(db, &snapshot, &resources, limit.clamp(1, 50), options))
}

fn build_session_top<'a>(
    db: &'a str,
    snapshot: &Snapshot,
    resources: &ResourcePeaks,
    limit: usize,
    options: &TopOptions,
) -> AgentTopOutput<'a> {
    let rows = session_agent_rows(snapshot, resources, options);
    let sections = top_sections(snapshot, limit, &options.view);
    let mut notes =
        vec!["static session view; run without --db for live /proc agent process top".to_string()];
    if options.pid.is_some() || options.comm.is_some() {
        notes.push("filter applied to saved rows before aggregation".to_string());
    }
    AgentTopOutput {
        mode: "static session",
        db: Some(db),
        duration_s: snapshot.summary.duration_s(),
        view_events: snapshot.summary.view_events,
        llm_calls: snapshot.summary.llm_calls,
        total_tokens: snapshot.summary.total_tokens,
        rows,
        sections,
        failures: recent_failures(snapshot, 5),
        notes,
    }
}

fn session_agent_rows(
    snapshot: &Snapshot,
    resources: &ResourcePeaks,
    options: &TopOptions,
) -> Vec<AgentTopRow> {
    let top_model = dominant_model(snapshot);
    let db_age_s = snapshot_age_s(snapshot);
    let rows = snapshot
        .sessions
        .iter()
        .filter(|session| options.matches(None, Some(&session.agent_type), None))
        .map(|session| {
            let cwd = session
                .attributes
                .get("cwd")
                .and_then(|v| v.as_str())
                .filter(|s| !s.is_empty())
                .map(ToString::to_string);
            let last_msg = session
                .attributes
                .get("last_message_at")
                .and_then(|v| v.as_str())
                .filter(|s| !s.is_empty())
                .map(ToString::to_string);
            AgentTopRow {
                session: short_session_id(&session.id),
                agent: session.agent_type.clone(),
                pid: None,
                model: session.model.clone().or_else(|| top_model.clone()),
                age_s: session_age_s(session, snapshot),
                cpu_percent: resources.max_cpu_percent,
                rss_mb: resources.max_rss_mb,
                processes: 0,
                tokens: (session.total_tokens > 0).then_some(session.total_tokens),
                tools: tools_for_session(snapshot, &session.id),
                execs: 0,
                failures: 0,
                files: 0,
                network: 0,
                unattributed: 0,
                trace: "db".to_string(),
                command: session.agent_type.clone(),
                workspace: cwd,
                last_message_at: last_msg,
                tool_breakdown: Vec::new(),
                file_breakdown: Vec::new(),
            }
        })
        .collect::<Vec<_>>();
    if !rows.is_empty() {
        return rows;
    }

    saved_session_row(snapshot, resources, options, top_model, db_age_s)
        .into_iter()
        .collect()
}

fn saved_session_row(
    snapshot: &Snapshot,
    resources: &ResourcePeaks,
    options: &TopOptions,
    top_model: Option<String>,
    db_age_s: Option<f64>,
) -> Option<AgentTopRow> {
    let mut pids = BTreeSet::new();
    let audit = AuditCounters::from_rows(
        snapshot
            .audit_events
            .iter()
            .filter(|row| options.matches(row.pid, row.comm.as_deref(), row.target.as_deref())),
    );
    pids.extend(audit.pids.iter().copied());

    let network = snapshot
        .network_targets
        .iter()
        .filter(|target| options.matches(target.pid, target.comm.as_deref(), Some(&target.host)))
        .filter_map(|target| {
            if let Some(pid) = target.pid {
                pids.insert(pid);
            }
            (target.count > 0).then_some(target.host.clone())
        })
        .collect::<BTreeSet<_>>()
        .len();
    let total_tokens = snapshot.summary.total_tokens;
    if audit.process_execs == 0
        && audit.process_exit_failure == 0
        && audit.unique_files.is_empty()
        && network == 0
        && total_tokens == 0
        && resources.samples == 0
    {
        return None;
    }

    Some(AgentTopRow {
        session: "db".to_string(),
        agent: snapshot
            .sessions
            .first()
            .map(|session| session.agent_type.clone())
            .unwrap_or_else(|| "saved".to_string()),
        pid: (pids.len() == 1).then(|| *pids.iter().next().unwrap()),
        model: top_model,
        age_s: db_age_s,
        cpu_percent: resources.max_cpu_percent,
        rss_mb: resources.max_rss_mb,
        processes: pids.len(),
        tokens: (total_tokens > 0).then_some(total_tokens),
        tools: snapshot.tool_calls.len(),
        execs: audit.process_execs,
        failures: audit.process_exit_failure,
        files: audit.unique_files.len(),
        network,
        unattributed: 0,
        trace: "db".to_string(),
        command: "saved session".to_string(),
        workspace: None,
        last_message_at: None,
        tool_breakdown: Vec::new(),
        file_breakdown: Vec::new(),
    })
}

fn tools_for_session(snapshot: &Snapshot, session_id: &str) -> usize {
    snapshot
        .tool_calls
        .iter()
        .filter(|tool| tool.session_id.as_deref() == Some(session_id))
        .count()
}

fn load_snapshot_and_resources(db: &str) -> ViewResult<(Snapshot, ResourcePeaks)> {
    let view = load_agentsight_view(Some(db))?;
    let snapshot = view.export_snapshot(SnapshotOptions {
        audit_limit: 50_000,
    });
    let resources = resource_peaks_from_samples(&snapshot.resource_samples);
    Ok((snapshot, resources))
}

fn resource_peaks_from_samples(samples: &[ResourceSampleRow]) -> ResourcePeaks {
    let mut peaks = ResourcePeaks::default();
    for sample in samples {
        if let Some(cpu) = sample.cpu_percent
            && cpu >= peaks.max_cpu_percent
        {
            peaks.max_cpu_percent = cpu;
        }
        if let Some(rss_mb) = sample.rss_mb.map(|v| v.max(0) as u64)
            && rss_mb >= peaks.max_rss_mb
        {
            peaks.max_rss_mb = rss_mb;
        }
        peaks.samples += 1;
    }

    peaks
}

fn snapshot_age_s(snapshot: &Snapshot) -> Option<f64> {
    let duration = snapshot.summary.duration_s();
    (duration > 0.0).then_some(duration)
}

fn session_age_s(session: &SessionRow, snapshot: &Snapshot) -> Option<f64> {
    let end = session
        .end_timestamp_ms
        .or(snapshot.summary.end_timestamp_ms)
        .unwrap_or(session.start_timestamp_ms);
    (end > session.start_timestamp_ms).then(|| (end - session.start_timestamp_ms) as f64 / 1000.0)
}

fn dominant_model(snapshot: &Snapshot) -> Option<String> {
    snapshot
        .token_summary
        .iter()
        .find(|row| row.group != "unknown" && row.total_tokens > 0)
        .map(|row| row.group.clone())
        .or_else(|| {
            snapshot
                .sessions
                .iter()
                .find_map(|session| session.model.clone())
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::AuditEventRow;

    #[test]
    fn session_tokens_ignore_touched_local_log_without_usage() {
        let (_temp, path) = agent_native_sessions::create_temp_session_path("claude");
        std::fs::write(
            &path,
            "{\"type\":\"user\",\"message\":{\"content\":\"local prompt only\"}}\n",
        )
        .unwrap();

        let mut snapshot = Snapshot::empty("sqlite");
        snapshot.summary.llm_calls = 1;
        snapshot.summary.token_usage_rows = 1;
        snapshot.summary.audit_events = 1;
        snapshot.summary.input_tokens = 8;
        snapshot.summary.output_tokens = 5;
        snapshot.summary.total_tokens = 13;
        snapshot.audit_events = vec![AuditEventRow {
            id: "audit-1".to_string(),
            timestamp_ms: 1_000,
            audit_type: "file".to_string(),
            pid: Some(42),
            comm: Some("claude".to_string()),
            subject: None,
            action: Some("write".to_string()),
            target: Some(path.to_string_lossy().to_string()),
            status: Some("observed".to_string()),
            summary: None,
            details: serde_json::json!({}),
        }];

        assert_eq!(snapshot.summary.input_tokens, 8);
        assert_eq!(snapshot.summary.output_tokens, 5);
        assert_eq!(snapshot.summary.total_tokens, 13);
    }
}
