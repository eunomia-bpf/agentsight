// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::model::Snapshot;
use crate::output::{AgentTopRow, TopSection, sorted_top_counts, top_counts_from_iter};
use std::collections::BTreeMap;

pub(crate) fn top_sections(snapshot: &Snapshot, limit: usize, view: &str) -> Vec<TopSection> {
    let audit = &snapshot.audit_events;
    let model_counts = snapshot
        .token_summary
        .iter()
        .map(|row| (row.group.clone(), row.total_tokens))
        .collect();
    let all = vec![
        (
            "Processes",
            "execs",
            top_counts_from_iter(
                audit
                    .iter()
                    .filter(|row| {
                        row.audit_type == "process" && row.action.as_deref() == Some("exec")
                    })
                    .map(|row| {
                        row.comm
                            .clone()
                            .or_else(|| row.target.clone())
                            .unwrap_or_else(|| "unknown".to_string())
                    }),
                limit,
            ),
        ),
        ("Files", "events", {
            let audit_files = top_counts_from_iter(
                audit
                    .iter()
                    .filter(|row| row.audit_type == "file")
                    .filter_map(|row| row.target.clone()),
                limit,
            );
            if audit_files.is_empty() {
                files_from_sessions(snapshot, limit)
            } else {
                audit_files
            }
        }),
        ("Network", "events", network_counts(snapshot, limit)),
        ("Models", "tokens", sorted_top_counts(model_counts, limit)),
        (
            "Tools",
            "calls",
            top_counts_from_iter(
                snapshot
                    .tool_calls
                    .iter()
                    .filter_map(|row| row.tool_name.clone()),
                limit,
            ),
        ),
    ];
    all.into_iter()
        .filter(|(title, _, _)| show_section(view, title))
        .collect()
}

fn show_section(view: &str, title: &str) -> bool {
    let view = view.to_ascii_lowercase();
    match view.as_str() {
        "all" => true,
        "process" | "processes" | "proc" => title == "Processes",
        "file" | "files" | "fs" => title == "Files",
        "network" | "net" => title == "Network",
        "model" | "models" | "tokens" => matches!(title, "Models" | "Tools"),
        "tool" | "tools" => title == "Tools",
        _ => true,
    }
}

fn network_counts(snapshot: &Snapshot, limit: usize) -> Vec<(String, i64)> {
    let counts = network_target_counts(snapshot);
    if counts.is_empty() {
        network_audit_counts(snapshot, limit)
    } else {
        sorted_top_counts(counts, limit)
    }
}

fn network_target_counts(snapshot: &Snapshot) -> BTreeMap<String, i64> {
    let mut counts = BTreeMap::new();
    for target in &snapshot.network_targets {
        *counts.entry(target.host.clone()).or_default() += target.count.max(0);
    }
    counts
}

fn network_audit_counts(snapshot: &Snapshot, limit: usize) -> Vec<(String, i64)> {
    top_counts_from_iter(
        snapshot
            .audit_events
            .iter()
            .filter(|row| row.audit_type == "network")
            .filter_map(|row| row.target.clone()),
        limit,
    )
}

fn files_from_sessions(snapshot: &Snapshot, limit: usize) -> Vec<(String, i64)> {
    let mut counts = BTreeMap::new();
    for session in &snapshot.sessions {
        if let Some(files) = session.attributes.get("files").and_then(|v| v.as_object()) {
            for (path, count) in files {
                let count = count
                    .as_i64()
                    .or_else(|| count.as_u64().map(|v| v as i64))
                    .unwrap_or(1);
                *counts.entry(path.clone()).or_insert(0i64) += count;
            }
        }
    }
    sorted_top_counts(counts, limit)
}

pub(crate) fn sort_agent_rows(rows: &mut [AgentTopRow], sort: &str) {
    let sort = normalize_sort_key(sort);
    rows.sort_by(|a, b| {
        let primary = match sort {
            "rss" => b.rss_mb.cmp(&a.rss_mb),
            "tokens" => b
                .tokens
                .unwrap_or_default()
                .cmp(&a.tokens.unwrap_or_default()),
            "execs" => b.execs.cmp(&a.execs),
            "fail" => b.failures.cmp(&a.failures),
            "files" => b.files.cmp(&a.files),
            "net" => b.network.cmp(&a.network),
            "agent" => a.agent.cmp(&b.agent),
            _ => b
                .cpu_percent
                .partial_cmp(&a.cpu_percent)
                .unwrap_or(std::cmp::Ordering::Equal),
        };
        primary
            .then_with(|| {
                b.cpu_percent
                    .partial_cmp(&a.cpu_percent)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .then_with(|| b.rss_mb.cmp(&a.rss_mb))
            .then_with(|| a.agent.cmp(&b.agent))
            .then_with(|| a.pid.cmp(&b.pid))
    });
}

pub(crate) fn normalize_sort_key(sort: &str) -> &'static str {
    match sort.to_ascii_lowercase().as_str() {
        "rss" | "mem" | "memory" => "rss",
        "tokens" | "token" => "tokens",
        "exec" | "execs" => "execs",
        "fail" | "fails" | "failure" | "failures" => "fail",
        "file" | "files" => "files",
        "net" | "network" => "net",
        "agent" | "name" | "command" => "agent",
        _ => "cpu",
    }
}

pub(crate) fn recent_failures(snapshot: &Snapshot, limit: usize) -> Vec<String> {
    snapshot
        .audit_events
        .iter()
        .rev()
        .filter(|row| row.status.as_deref() == Some("failure"))
        .take(limit)
        .map(|row| {
            row.summary
                .clone()
                .or_else(|| row.target.clone())
                .unwrap_or_else(|| "failure".to_string())
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::AuditEventRow;
    use serde_json::json;

    #[test]
    fn network_section_falls_back_to_network_audit_events() {
        let mut snapshot = Snapshot::empty("test");
        snapshot.audit_events.push(AuditEventRow {
            id: "audit-net-1".to_string(),
            timestamp_ms: 1,
            audit_type: "network".to_string(),
            pid: Some(42),
            comm: Some("codex".to_string()),
            subject: Some("codex".to_string()),
            action: Some("NET_CONNECT".to_string()),
            target: Some("127.0.0.1:7395".to_string()),
            status: Some("observed".to_string()),
            summary: None,
            details: json!({}),
            view_source: "view".to_string(),
            confidence: Some(0.75),
        });

        let sections = top_sections(&snapshot, 10, "network");
        assert_eq!(
            sections,
            vec![("Network", "events", vec![("127.0.0.1:7395".to_string(), 1)])]
        );
    }
}
