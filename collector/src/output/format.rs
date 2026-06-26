// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::Serialize;
use serde_json::Value;
use std::collections::BTreeMap;
use std::path::Path;

use crate::analyzers::common;
use crate::event::Event;
use crate::model::{AuditEventRow, LlmCallRow, TokenSummary};
use crate::text::{extract_prompt_text, truncate_with_ellipsis as truncate};

#[derive(Debug, Default, Serialize)]
pub(crate) struct ResourcePeaks {
    pub(crate) max_cpu_percent: f64,
    pub(crate) max_rss_mb: u64,
    pub(crate) samples: usize,
}

pub(crate) type TopSection = (&'static str, &'static str, Vec<(String, i64)>);

pub(crate) fn sorted_top_counts<T>(counts: BTreeMap<String, T>, limit: usize) -> Vec<(String, T)>
where
    T: Ord,
{
    let mut rows: Vec<_> = counts.into_iter().collect();
    rows.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    rows.truncate(limit);
    rows
}

pub(crate) fn top_counts_from_iter(
    rows: impl IntoIterator<Item = String>,
    limit: usize,
) -> Vec<(String, i64)> {
    let mut counts = BTreeMap::new();
    for row in rows {
        *counts.entry(row).or_insert(0) += 1;
    }
    sorted_top_counts(counts, limit)
}

#[derive(Debug, Clone)]
pub(crate) struct TopOptions {
    pub(crate) pid: Option<u32>,
    pub(crate) comm: Option<String>,
    pub(crate) sort: String,
    pub(crate) view: String,
}

impl TopOptions {
    pub(crate) fn matches(
        &self,
        pid: Option<u32>,
        comm: Option<&str>,
        command: Option<&str>,
    ) -> bool {
        if let Some(wanted_pid) = self.pid {
            return pid == Some(wanted_pid);
        }
        if let Some(wanted_comm) = &self.comm {
            let wanted_comm = wanted_comm.to_ascii_lowercase();
            return comm
                .map(|comm| comm.to_ascii_lowercase().contains(&wanted_comm))
                .unwrap_or(false)
                || command
                    .map(|command| command.to_ascii_lowercase().contains(&wanted_comm))
                    .unwrap_or(false);
        }
        true
    }
}

#[derive(Debug, Clone, Default)]
pub(crate) struct AgentTopRow {
    pub(crate) session: String,
    pub(crate) agent: String,
    pub(crate) pid: Option<u32>,
    pub(crate) model: Option<String>,
    pub(crate) age_s: Option<f64>,
    pub(crate) cpu_percent: f64,
    pub(crate) rss_mb: u64,
    pub(crate) processes: usize,
    pub(crate) tokens: Option<i64>,
    pub(crate) tools: usize,
    pub(crate) execs: usize,
    pub(crate) failures: usize,
    pub(crate) files: usize,
    pub(crate) network: usize,
    pub(crate) unattributed: usize,
    pub(crate) trace: String,
    pub(crate) command: String,
    pub(crate) workspace: Option<String>,
    pub(crate) last_message_at: Option<String>,
    pub(crate) tool_breakdown: Vec<(String, i64)>,
    pub(crate) file_breakdown: Vec<(String, i64)>,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(crate) struct TopEvidence {
    pub(crate) agent_native: bool,
    pub(crate) local: bool,
    pub(crate) proc: bool,
    pub(crate) proc_fd: bool,
    pub(crate) sticky: bool,
    pub(crate) cwd_recent: bool,
    pub(crate) ebpf: bool,
    pub(crate) ebpf_file: bool,
    pub(crate) db: bool,
}

impl TopEvidence {
    pub(crate) fn from_trace(trace: &str) -> Self {
        let mut evidence = Self::default();
        for token in trace.split('+') {
            match token {
                "agent-native" => evidence.agent_native = true,
                "local" => evidence.local = true,
                "proc" => evidence.proc = true,
                "proc_fd" => {
                    evidence.proc = true;
                    evidence.proc_fd = true;
                }
                "sticky" => {
                    evidence.proc = true;
                    evidence.sticky = true;
                }
                "cwd_recent" => {
                    evidence.proc = true;
                    evidence.cwd_recent = true;
                }
                "ebpf" => evidence.ebpf = true,
                "ebpf_file" => {
                    evidence.ebpf = true;
                    evidence.ebpf_file = true;
                }
                "db" => evidence.db = true,
                _ => {}
            }
        }
        evidence
    }

    pub(crate) fn has_history(self) -> bool {
        self.local || self.agent_native
    }

    pub(crate) fn has_session_path_link(self) -> bool {
        self.ebpf_file || self.proc_fd || self.sticky
    }
}

impl AgentTopRow {
    pub(crate) fn evidence(&self) -> TopEvidence {
        TopEvidence::from_trace(&self.trace)
    }

    pub(crate) fn add_trace(&mut self, token: &str) {
        if self.trace.split('+').any(|part| part == token) {
            return;
        }
        if !self.trace.is_empty() {
            self.trace.push('+');
        }
        self.trace.push_str(token);
    }

    pub(crate) fn state_label(&self) -> &'static str {
        let evidence = self.evidence();
        if evidence.proc {
            "live"
        } else if self.failures > 0 {
            "failed"
        } else if evidence.has_history() {
            "history"
        } else if evidence.db {
            "saved"
        } else {
            "-"
        }
    }

    pub(crate) fn age_label(&self) -> String {
        self.age_s
            .map(format_duration_compact)
            .unwrap_or_else(|| "-".to_string())
    }

    pub(crate) fn token_label(&self) -> String {
        self.tokens
            .map(format_count)
            .unwrap_or_else(|| "-".to_string())
    }

    pub(crate) fn last_msg_label(&self) -> String {
        self.last_message_at
            .as_deref()
            .and_then(format_iso_time_compact)
            .unwrap_or_else(|| "-".to_string())
    }

    pub(crate) fn last_msg_relative_label(&self) -> String {
        self.last_message_at
            .as_deref()
            .and_then(format_iso_time_relative)
            .unwrap_or_else(|| "-".to_string())
    }

    pub(crate) fn model_label(&self) -> String {
        self.model.clone().unwrap_or_else(|| "-".to_string())
    }

    pub(crate) fn activity_label(&self) -> String {
        let mut parts = Vec::new();
        if self.processes > 0 {
            parts.push(format!("{} proc", self.processes));
        }
        if self.tools > 0 {
            parts.push(format!("{} tool", self.tools));
        }
        if self.execs > 0 {
            parts.push(format!("{} exec", self.execs));
        }
        if self.failures > 0 {
            parts.push(format!("{} fail", self.failures));
        }
        if self.files > 0 {
            parts.push(format!("{} file", self.files));
        }
        if self.network > 0 {
            parts.push(format!("{} net", self.network));
        }
        if parts.is_empty() {
            "-".to_string()
        } else {
            parts.join(", ")
        }
    }

    pub(crate) fn health_label(&self) -> String {
        if self.cpu_percent == 0.0 && self.rss_mb == 0 {
            "-".to_string()
        } else {
            format!("{:.1}% {}", self.cpu_percent, format_mb(self.rss_mb))
        }
    }

    pub(crate) fn evidence_label(&self) -> String {
        let mut parts = Vec::new();
        let evidence = self.evidence();
        if evidence.has_history() {
            parts.push("logs");
        }
        if evidence.proc {
            parts.push("/proc");
        }
        if evidence.proc_fd {
            parts.push("fd");
        }
        if evidence.sticky {
            parts.push("linked");
        }
        if evidence.cwd_recent {
            parts.push("cwd");
        }
        if evidence.ebpf_file {
            parts.push("eBPF:file");
        } else if evidence.ebpf {
            parts.push("eBPF");
        }
        if evidence.db {
            parts.push("db");
        }
        if parts.is_empty() {
            self.trace.clone()
        } else {
            parts.join("+")
        }
    }
}

pub(crate) struct AgentTopOutput<'a> {
    pub(crate) mode: &'a str,
    pub(crate) db: Option<&'a str>,
    pub(crate) duration_s: f64,
    pub(crate) view_events: i64,
    pub(crate) llm_calls: i64,
    pub(crate) total_tokens: i64,
    pub(crate) rows: Vec<AgentTopRow>,
    pub(crate) sections: Vec<TopSection>,
    pub(crate) failures: Vec<String>,
    pub(crate) notes: Vec<String>,
}

pub(crate) struct SessionSummary {
    pub(crate) source: String,
    pub(crate) duration_s: f64,
    pub(crate) first_llm_after_ms: Option<u64>,
    pub(crate) first_tool_after_ms: Option<u64>,
    pub(crate) prompt_chars: SummaryStats,
    pub(crate) llm_latency_ms: SummaryStats,
    pub(crate) models: Vec<(String, i64, i64, i64, i64)>,
    pub(crate) processes: BTreeMap<String, usize>,
    pub(crate) process_exits: BTreeMap<String, usize>,
    pub(crate) tool_calls: BTreeMap<String, usize>,
    pub(crate) tool_duration_ms: SummaryStats,
    pub(crate) files: Vec<String>,
    pub(crate) file_access: FileAccessSummary,
    pub(crate) network_events: usize,
    pub(crate) endpoints: Vec<String>,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct SummaryStats {
    pub(crate) count: usize,
    pub(crate) total: u64,
    pub(crate) max: u64,
}

impl SummaryStats {
    pub(crate) fn add(&mut self, value: u64) {
        self.count += 1;
        self.total += value;
        self.max = self.max.max(value);
    }

    fn avg(&self) -> Option<u64> {
        (self.count > 0).then(|| self.total / self.count as u64)
    }
}

#[derive(Debug, Clone, Default)]
pub(crate) struct FileAccessSummary {
    pub(crate) events: usize,
    pub(crate) first_after_ms: Option<u64>,
    pub(crate) last_after_ms: Option<u64>,
    pub(crate) actions: BTreeMap<String, usize>,
    pub(crate) directories: Vec<(String, usize)>,
}

pub(crate) fn print_json<T: Serialize>(value: &T) -> Result<(), serde_json::Error> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

pub(crate) fn print_event_json(event: &Event) {
    let mut value = serde_json::to_value(event).unwrap_or_else(|e| {
        serde_json::json!({"source":"diagnostic","data":{"error": format!("failed to serialize event: {}", e)}})
    });
    if let Some(data_obj) = value.get_mut("data")
        && let Some(data_field) = data_obj.get_mut("data")
    {
        *data_field = Value::String(common::data_to_string(data_field));
    }

    println!(
        "{}",
        serde_json::to_string(&value)
            .unwrap_or_else(|e| format!("{{\"error\":\"failed to render event: {}\"}}", e))
    );
    use std::io::Write;
    let _ = std::io::stdout().flush();
}

pub(crate) fn clear_screen() {
    print!("\x1b[2J\x1b[H");
}

pub(crate) fn separator_line() -> &'static str {
    "============================================================"
}

pub(crate) fn print_trace_header() {
    println!("Trace Monitoring\n{}", separator_line());
}

pub(crate) fn print_trace_ssl_binary_discovered(comm: &str, path: &str) {
    println!("✓ Auto-discovered statically-linked SSL binary for --comm '{comm}': {path}");
}

pub(crate) fn print_trace_container_binary_resolved(reference: &str, path: &str) {
    println!("✓ Resolved container '{reference}' to SSL attach target: {path}");
}

pub(crate) fn print_trace_start(runners: usize, analyzers: usize) {
    println!("{}", separator_line());
    println!(
        "Starting flexible trace monitoring with {runners} runners and {analyzers} global analyzers..."
    );
    println!("Press Ctrl+C to stop");
}

pub(crate) fn print_trace_shutdown() {
    println!("✓ Shutdown requested. Stopping monitoring.");
}

pub(crate) fn print_web_server_start(url: &str) {
    println!("Starting web server on {url}");
}

pub(crate) fn print_web_server_error(error: impl std::fmt::Display) {
    eprintln!("Web server error: {error}");
}

pub(crate) fn print_record_header() {
    println!("AgentSight record\n{}", separator_line());
}

pub(crate) fn print_record_session_db_error(error: impl std::fmt::Display) {
    eprintln!("⚠ Could not create session DB ({error}), continuing without it.");
}

pub(crate) fn print_record_provided_binary_path(path: &str) {
    println!("→ Using provided binary path: {path}");
}

pub(crate) fn print_record_auto_binary_path(path: &str) {
    println!("✓ Auto-discovered binary: {path}");
}

pub(crate) fn print_record_sudo_prompt() {
    println!("🔑 eBPF probes require root. Requesting sudo access...");
}

pub(crate) fn print_top_sudo_prompt() {
    eprintln!("top live eBPF capture requires sudo. Requesting sudo access...");
}

pub(crate) fn print_record_drop_user(uid: libc::uid_t, gid: libc::gid_t) {
    println!("✓ Dropping child to uid={uid} gid={gid}");
}

pub(crate) fn print_record_attribution_session(pid: u32) {
    println!("✓ Run attribution session: {pid}");
}

pub(crate) fn print_record_web_ui(url: &str) {
    println!("Web UI: {url}");
}

pub(crate) fn print_record_launch(command: &[String]) {
    println!("▶ Launching: {}", command.join(" "));
    println!("{}", separator_line());
}

pub(crate) fn print_record_monitoring_stream_ended() {
    println!("\n⚠ Monitoring stream ended before target exited. Stopping target.");
}

pub(crate) fn print_record_target_exited(status: impl std::fmt::Display) {
    println!(
        "\n{}\n✓ Target exited ({}). Stopping monitoring.",
        separator_line(),
        status
    );
}

pub(crate) fn print_record_target_wait_error(error: impl std::fmt::Display) {
    println!("\n⚠ Error waiting on target: {error}");
}

pub(crate) fn print_record_shutdown() {
    println!("\n✓ Shutdown requested. Stopping target and monitoring.");
}

pub(crate) fn print_record_session_summary(db_path: &str, summary: &SessionSummary) {
    let api_calls: i64 = summary.models.iter().map(|m| m.4).sum();
    let tokens: i64 = summary.models.iter().map(|m| m.3).sum();
    let execs: usize = summary.processes.values().sum();
    println!();
    println!(
        "Recorded {} to {}",
        format_duration_compact(summary.duration_s),
        db_path
    );
    println!(
        "{} API calls · {} tokens · {} execs · {} files · {} network endpoints",
        api_calls,
        format_count(tokens),
        execs,
        summary.files.len(),
        summary.endpoints.len()
    );
    println!("Run: {}", record_report_command(db_path));
}

fn record_report_command(db_path: &str) -> String {
    let path = Path::new(db_path);
    let Some(file_name) = path.file_name().and_then(|name| name.to_str()) else {
        return format!("agentsight report --db {}", shell_quote(db_path));
    };
    if !file_name.starts_with("agentsight-") || path.extension().is_none_or(|ext| ext != "db") {
        return format!("agentsight report --db {}", shell_quote(db_path));
    }
    if record_db_is_in_current_dir(path) {
        "agentsight report".to_string()
    } else {
        format!("agentsight report --db {}", shell_quote(db_path))
    }
}

fn record_db_is_in_current_dir(path: &Path) -> bool {
    match path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
    {
        None => true,
        Some(parent) if parent == Path::new(".") => true,
        Some(parent) => std::env::current_dir()
            .ok()
            .is_some_and(|current_dir| parent == current_dir),
    }
}

pub(crate) fn print_record_target_status_error(error: impl std::fmt::Display) {
    println!("⚠ Error checking target status: {error}");
}

pub(crate) fn print_record_target_shutdown_error(error: impl std::fmt::Display) {
    println!("⚠ Error waiting for target shutdown: {error}");
}

pub(crate) fn print_record_kill_error(error: impl std::fmt::Display) {
    println!("⚠ Failed to kill target process: {error}");
}

pub(crate) fn print_exported_snapshot(output: &str) {
    println!("Exported snapshot to {output}");
}

pub(crate) fn print_report_local_sessions_warning() {
    eprintln!(
        "Warning: No agentsight-*.db session database found in the current directory; using local agent sessions."
    );
}

pub(crate) fn print_token_summary(group_by: &str, rows: &[TokenSummary]) {
    println!("Token usage grouped by {group_by}");
    println!(
        "{:<32} {:>12} {:>12} {:>12} {:>12} {:>12} {:>8} {:>8}",
        "group", "input", "output", "cache_new", "cache_read", "total", "calls", "sessions"
    );
    for row in rows {
        println!(
            "{:<32} {:>12} {:>12} {:>12} {:>12} {:>12} {:>8} {:>8}",
            truncate(&row.group, 32),
            row.input_tokens,
            row.output_tokens,
            row.cache_creation_tokens,
            row.cache_read_tokens,
            row.total_tokens,
            row.calls,
            row.sessions
        );
    }
}

pub(crate) fn print_audit_rows(rows: &[AuditEventRow]) {
    println!("Audit events");
    println!(
        "{:<15} {:<10} {:<8} {:<16} {:<10} {:<28} summary",
        "timestamp_ms", "type", "pid", "comm", "status", "target"
    );
    for row in rows {
        println!(
            "{:<15} {:<10} {:<8} {:<16} {:<10} {:<28} {}",
            row.timestamp_ms,
            row.audit_type,
            row.pid
                .map(|v| v.to_string())
                .unwrap_or_else(|| "-".to_string()),
            truncate(row.comm.as_deref().unwrap_or("-"), 16),
            row.status.as_deref().unwrap_or("-"),
            truncate(row.target.as_deref().unwrap_or("-"), 28),
            row.summary.as_deref().unwrap_or("")
        );
    }
}

pub(crate) fn print_llm_prompts(rows: &[LlmCallRow]) {
    println!("LLM prompts");
    println!(
        "{:<15} {:<16} {:<28} {:>8} prompt",
        "timestamp_ms", "comm", "model", "tokens"
    );
    for row in rows {
        println!(
            "{:<15} {:<16} {:<28} {:>8} {}",
            row.start_timestamp_ms,
            truncate(row.comm.as_deref().unwrap_or("-"), 16),
            truncate(row.model.as_deref().unwrap_or("-"), 28),
            row.total_tokens,
            prompt_preview(&row.request, 96)
        );
    }
}

pub(crate) fn print_agent_top(top: &AgentTopOutput<'_>) {
    let generated_at = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
    let db = top.db.map(|db| format!(" · {db}")).unwrap_or_default();
    println!(
        "AgentSight top - {} sessions   {}   {}{db}   {:.0}s   events: {}   LLM: {}   session tokens: {}",
        top.rows.len(),
        top.mode,
        generated_at,
        top.duration_s,
        top.view_events,
        top.llm_calls,
        format_count(top.total_tokens)
    );
    println!();
    println!(
        "{:<18} {:<10} {:<8} {:>6} {:>9} {:<18} {:>8} {:<20} {:<12} {:<12} {:<24} CONTEXT",
        "SESSION",
        "AGENT",
        "STATE",
        "AGE",
        "LAST MSG",
        "MODEL",
        "TOKENS",
        "ACTIVITY",
        "HEALTH",
        "EVIDENCE",
        "WORKSPACE"
    );
    for row in &top.rows {
        println!(
            "{:<18} {:<10} {:<8} {:>6} {:>9} {:<18} {:>8} {:<20} {:<12} {:<12} {:<24} {}",
            truncate(&row.session, 18),
            truncate(&row.agent, 10),
            row.state_label(),
            row.age_label(),
            row.last_msg_label(),
            truncate(&row.model_label(), 18),
            row.token_label(),
            truncate(&row.activity_label(), 20),
            truncate(&row.health_label(), 12),
            truncate(&row.evidence_label(), 12),
            truncate(row.workspace.as_deref().unwrap_or("-"), 24),
            truncate(&row.command, 48),
        );
    }
    if top.rows.is_empty() {
        println!(
            "{:<18} {:<10} {:<8} {:>6} {:>9} {:<18} {:>8} {:<20} {:<12} {:<12} {:<24} -",
            "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"
        );
    }
    println!();

    for note in &top.notes {
        println!("note: {note}");
    }
    if !top.notes.is_empty() {
        println!();
    }

    if !top.sections.is_empty() {
        println!("Hot activity");
        for section in &top.sections {
            print_ranked(section);
        }
    }
    if !top.failures.is_empty() {
        println!("Recent Failures");
        for failure in &top.failures {
            println!("  {failure}");
        }
        println!();
    }
}

pub(crate) fn print_session_summary(summary: &SessionSummary) {
    let total_tokens: i64 = summary.models.iter().map(|m| m.3).sum();
    let total_calls: i64 = summary.models.iter().map(|m| m.4).sum();
    let has_tokens = summary
        .models
        .iter()
        .any(|(_, input, output, total, _)| *input > 0 || *output > 0 || *total > 0);

    print!("{} session", summary.source);
    if summary.duration_s > 0.0 {
        print!(" · {:.0}s", summary.duration_s);
    }
    if total_calls > 0 {
        print!(" · {total_calls} API calls");
    }
    if has_tokens {
        print!(" · {total_tokens} tokens");
    }
    println!("\n");

    print_session_timeline(summary);

    for (name, inp, out, total, calls) in &summary.models {
        if *inp == 0 && *out == 0 && *total == 0 {
            continue;
        }
        if *calls > 0 {
            println!("  {name} — {calls} calls, {total} tokens (in: {inp}, out: {out})");
        } else {
            println!("  {name} — {total} tokens (in: {inp}, out: {out})");
        }
    }

    print_count_map("processes spawned", &summary.processes);
    print_process_exits(&summary.process_exits);
    print_count_map("tool calls", &summary.tool_calls);
    if let Some(avg) = summary.tool_duration_ms.avg() {
        println!(
            "tool duration: avg {}, max {} ({} completed)",
            format_ms(avg),
            format_ms(summary.tool_duration_ms.max),
            summary.tool_duration_ms.count
        );
    } else if !summary.tool_calls.is_empty() {
        println!("tool duration: not captured");
    }

    if summary.file_access.events > 0 {
        let file_window = match (
            summary.file_access.first_after_ms,
            summary.file_access.last_after_ms,
        ) {
            (Some(first), Some(last)) if last > first => {
                format!(" · +{}..+{}", format_ms(first), format_ms(last))
            }
            (Some(first), _) => format!(" · +{}", format_ms(first)),
            _ => String::new(),
        };
        println!(
            "{} file events · {} unique files{}",
            summary.file_access.events,
            summary.files.len(),
            file_window
        );
        print_count_map("file actions", &summary.file_access.actions);
        if !summary.file_access.directories.is_empty() {
            let dirs = summary
                .file_access
                .directories
                .iter()
                .take(5)
                .map(|(dir, count)| format!("{}({})", truncate(dir, 64), count))
                .collect::<Vec<_>>()
                .join(", ");
            println!("file dirs: {dirs}");
        }
        let display: Vec<&str> = summary.files.iter().take(5).map(String::as_str).collect();
        let suffix = if summary.files.len() > 5 {
            format!(", ... (+{} more)", summary.files.len() - 5)
        } else {
            String::new()
        };
        println!("files accessed: {}{}", display.join(", "), suffix);
    }
    if summary.network_events > 0 {
        println!(
            "Network: {} events across {} endpoints: {}",
            summary.network_events,
            summary.endpoints.len(),
            summary.endpoints.join(", ")
        );
    }
}

fn print_session_timeline(summary: &SessionSummary) {
    let has_timeline = summary.first_llm_after_ms.is_some()
        || summary.first_tool_after_ms.is_some()
        || summary.prompt_chars.count > 0
        || summary.llm_latency_ms.count > 0;
    if !has_timeline {
        return;
    }

    println!("Timeline");
    if let Some(ms) = summary.first_llm_after_ms {
        println!("  first LLM call: +{}", format_ms(ms));
    }
    if let Some(ms) = summary.first_tool_after_ms {
        println!("  first tool call: +{}", format_ms(ms));
    }
    if let Some(avg) = summary.llm_latency_ms.avg() {
        println!(
            "  LLM latency: avg {}, max {} ({} completed)",
            format_ms(avg),
            format_ms(summary.llm_latency_ms.max),
            summary.llm_latency_ms.count
        );
    }
    if let Some(avg) = summary.prompt_chars.avg() {
        println!(
            "  prompt length: avg {} chars, max {} chars ({} captured)",
            avg, summary.prompt_chars.max, summary.prompt_chars.count
        );
    }
    println!();
}

pub(crate) fn print_session_list(dir: &Path, entries: &[std::fs::DirEntry]) {
    if entries.is_empty() {
        println!("No session databases found in {}", dir.display());
        return;
    }
    println!("Session databases in {}:", dir.display());
    for entry in entries {
        let modified = entry
            .metadata()
            .ok()
            .and_then(|m| m.modified().ok())
            .map(|t| {
                chrono::DateTime::<chrono::Local>::from(t)
                    .format("%Y-%m-%d %H:%M:%S")
                    .to_string()
            })
            .unwrap_or_default();
        let size = entry.metadata().ok().map(|m| m.len()).unwrap_or(0);
        println!(
            "  {} ({} KB, {})",
            entry.path().display(),
            size / 1024,
            modified
        );
    }
}

fn print_count_map(label: &str, counts: &BTreeMap<String, usize>) {
    if counts.is_empty() {
        return;
    }
    let mut sorted: Vec<_> = counts.iter().collect();
    sorted.sort_by_key(|b| std::cmp::Reverse(b.1));
    let total: usize = sorted.iter().map(|(_, c)| *c).sum();
    let top = sorted
        .iter()
        .take(8)
        .map(|(name, count)| format!("{name}({count})"))
        .collect::<Vec<_>>()
        .join(", ");
    println!("\n{total} {label}: {top}");
}

fn shell_quote(value: &str) -> String {
    if value
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || matches!(c, '/' | '.' | '-' | '_' | ':' | '+'))
    {
        value.to_string()
    } else {
        format!("'{}'", value.replace('\'', "'\\''"))
    }
}

fn print_process_exits(counts: &BTreeMap<String, usize>) {
    if counts.is_empty() {
        return;
    }
    let ordered = ["failure", "success", "observed"];
    let mut parts = ordered
        .iter()
        .filter_map(|status| {
            counts
                .get(*status)
                .map(|count| format!("{status}({count})"))
        })
        .collect::<Vec<_>>();
    parts.extend(
        counts
            .iter()
            .filter(|(status, _)| !ordered.contains(&status.as_str()))
            .map(|(status, count)| format!("{status}({count})")),
    );
    println!(
        "{} process exits: {}",
        counts.values().sum::<usize>(),
        parts.join(", ")
    );
}

fn format_ms(ms: u64) -> String {
    if ms >= 1000 {
        format!("{:.1}s", ms as f64 / 1000.0)
    } else {
        format!("{ms}ms")
    }
}

fn print_ranked((title, unit, rows): &TopSection) {
    if rows.is_empty() {
        return;
    }
    println!("{title}");
    for (name, value) in rows {
        println!("  {value:>8} {unit:<8} {}", truncate(name, 96));
    }
    println!();
}

pub(crate) fn format_count(value: i64) -> String {
    let abs = value.abs();
    if abs >= 1_000_000 {
        format!("{:.1}M", value as f64 / 1_000_000.0)
    } else if abs >= 1_000 {
        format!("{:.1}k", value as f64 / 1_000.0)
    } else {
        value.to_string()
    }
}

fn format_mb(value: u64) -> String {
    if value >= 1024 {
        format!("{:.1}G", value as f64 / 1024.0)
    } else {
        format!("{value}M")
    }
}

fn format_duration_compact(seconds: f64) -> String {
    let seconds = seconds.max(0.0).round() as u64;
    if seconds < 60 {
        format!("{seconds}s")
    } else if seconds < 3_600 {
        format!("{}m", seconds / 60)
    } else if seconds < 86_400 {
        format!("{}h", seconds / 3_600)
    } else {
        format!("{}d", seconds / 86_400)
    }
}

fn format_iso_time_relative(iso: &str) -> Option<String> {
    let dt = chrono::DateTime::parse_from_rfc3339(iso).ok()?;
    let ago = chrono::Utc::now().signed_duration_since(dt);
    let secs = ago.num_seconds().max(0) as f64;
    Some(format_duration_compact(secs))
}

fn format_iso_time_compact(iso: &str) -> Option<String> {
    let dt = chrono::DateTime::parse_from_rfc3339(iso).ok()?;
    let local = dt.with_timezone(&chrono::Local);
    Some(local.format("%H:%M:%S").to_string())
}

fn prompt_preview(value: &Value, max: usize) -> String {
    let text = extract_prompt_text(value).unwrap_or_else(|| value.to_string());
    truncate(&text.split_whitespace().collect::<Vec<_>>().join(" "), max)
}

pub(crate) fn prompt_text_chars(value: &Value) -> Option<usize> {
    extract_prompt_text(value).map(|text| text.chars().count())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_report_command_uses_default_for_current_directory_record_db() {
        assert_eq!(
            record_report_command("agentsight-20260616-161500.db"),
            "agentsight report"
        );
        assert_eq!(
            record_report_command("./agentsight-20260616-161500.db"),
            "agentsight report"
        );

        let path = std::env::current_dir()
            .unwrap()
            .join("agentsight-20260616-161500.db");
        let path = path.to_string_lossy();
        assert_eq!(record_report_command(path.as_ref()), "agentsight report");
    }

    #[test]
    fn record_report_command_keeps_db_flag_for_non_current_directory_db() {
        let path = std::env::temp_dir()
            .join("agentsight-other-dir")
            .join("agentsight-20260616-161500.db");
        let path = path.to_string_lossy();
        assert_eq!(
            record_report_command(path.as_ref()),
            format!("agentsight report --db {}", shell_quote(path.as_ref()))
        );
        assert_eq!(
            record_report_command("custom.db"),
            "agentsight report --db custom.db"
        );
    }

    #[test]
    fn live_top_row_stays_live_when_child_process_failed() {
        let mut row = AgentTopRow {
            failures: 1,
            ..Default::default()
        };

        row.trace = "agent-native+proc+ebpf".to_string();
        assert_eq!(row.state_label(), "live");

        row.trace = "db".to_string();
        assert_eq!(row.state_label(), "failed");
    }
}
