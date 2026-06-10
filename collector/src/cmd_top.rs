// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! `top` / `stat` query surface. One module, three render modes over the
//! same snapshot data:
//!
//! - saved-DB queries (`run_top_query`) — no eBPF;
//! - live table (`run_live_top_query`) — /proc + agent-native sessions plus
//!   optional eBPF process capture;
//! - live TUI (`run_live_top_tui`) — interactive variant of the same view.

use crate::analyzers::TimestampNormalizer;
use crate::binary_extractor::BinaryExtractor;
use crate::cli_db::load_agentsight_view;
use crate::cmd_exec::sudo_cached;
use crate::event::Event;
use crate::model::{AuditCounters, SessionRow, Snapshot, SnapshotOptions, ViewResult};
use crate::output::{
    AgentTopOutput, AgentTopRow, ResourcePeaks, TopOptions, clear_screen, draw_live_top_tui,
    next_view_key, print_agent_top,
};
use crate::runners::{ProcessRunner, Runner};
use crate::sources::proc as procfs;
use crate::text::short_session_id;
use crate::view::MaterializedView;
use crate::view::live_top::{LiveCaptureSnapshot, LiveView};
use crate::view::process_select;
use crate::view::top::{normalize_sort_key, recent_failures, sort_agent_rows, top_sections};
use crossterm::{
    cursor::{Hide, Show},
    event::{self, Event as CrosstermEvent, KeyCode, KeyEventKind, KeyModifiers},
    execute,
    terminal::{self, EnterAlternateScreen, LeaveAlternateScreen},
};
use futures::StreamExt;
use ratatui::{Terminal, backend::CrosstermBackend};
use std::collections::BTreeSet;
use std::io::{self, Write};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

type CommandResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

/// Shared periodic-render loop for the non-TUI top modes.
fn run_refresh_loop(
    interval_secs: u64,
    count: Option<u32>,
    mut render: impl FnMut() -> CommandResult,
) -> CommandResult {
    let interval = Duration::from_secs(interval_secs.max(1));
    let mut iterations = 0u32;
    loop {
        render()?;
        io::stdout().flush()?;

        iterations += 1;
        if count.is_some_and(|max| iterations >= max) || crate::shutdown_requested() {
            break;
        }
        std::thread::sleep(interval);
    }
    Ok(())
}

// --- Saved-DB queries ---

pub(crate) fn run_top_query(
    db: &str,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> CommandResult {
    let limit = limit.clamp(1, 50);
    let should_clear_screen = count != Some(1);

    run_refresh_loop(interval_secs, count, || {
        let (snapshot, resources) = load_snapshot_and_resources(db)?;
        if should_clear_screen {
            clear_screen();
        }
        let mut top = build_session_top(db, &snapshot, &resources, limit, options);
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        Ok(())
    })
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
    let resources = ResourcePeaks::from_samples(&snapshot.resource_samples);
    Ok((snapshot, resources))
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

// --- Live eBPF capture (shared by table and TUI modes) ---

struct LiveCaptureState {
    view: MaterializedView,
    parse_errors: u64,
}

impl Default for LiveCaptureState {
    fn default() -> Self {
        Self {
            view: MaterializedView::bounded(),
            parse_errors: 0,
        }
    }
}

pub(crate) struct LiveEbpfCapture {
    state: Arc<Mutex<LiveCaptureState>>,
    handle: tokio::task::JoinHandle<()>,
    start_note: Option<String>,
}

impl LiveEbpfCapture {
    pub(crate) fn stop(self) {
        self.handle.abort();
    }

    pub(crate) fn snapshot(&self) -> LiveCaptureSnapshot {
        let Ok(state) = self.state.lock() else {
            return LiveCaptureSnapshot::default();
        };
        let snapshot = state.view.export_snapshot(SnapshotOptions {
            audit_limit: 10_000,
        });
        LiveCaptureSnapshot::new(snapshot, state.parse_errors)
    }

    pub(crate) fn start_note(&self) -> Option<&str> {
        self.start_note.as_deref()
    }
}

pub(crate) async fn start_live_ebpf_capture(
    binary_extractor: &BinaryExtractor,
    options: &TopOptions,
) -> Option<LiveEbpfCapture> {
    let start_note = match prepare_live_ebpf_privileges() {
        Ok(note) => note,
        Err(note) => {
            return Some(LiveEbpfCapture {
                state: Arc::new(Mutex::new(LiveCaptureState::default())),
                handle: tokio::spawn(async {}),
                start_note: Some(note),
            });
        }
    };

    let mut args = Vec::new();
    if let Some(pid) = options.pid {
        args.extend(["-p".to_string(), pid.to_string()]);
    } else if let Some(comm) = &options.comm {
        args.extend(["-c".to_string(), comm.clone()]);
    } else {
        args.extend(["-m".to_string(), "1".to_string()]);
    }
    args.push("--trace-fs".to_string());
    args.push("--trace-net".to_string());

    let seed_snapshot = match procfs::ProcSnapshot::collect() {
        Ok(snapshot) => snapshot,
        Err(err) => {
            return Some(LiveEbpfCapture {
                state: Arc::new(Mutex::new(LiveCaptureState::default())),
                handle: tokio::spawn(async {}),
                start_note: Some(format!("live eBPF capture did not start: {err}")),
            });
        }
    };
    let seeds = process_select::process_seeds(
        &seed_snapshot,
        None,
        options.pid,
        options.comm.as_deref(),
        true,
    );

    let mut runner = ProcessRunner::from_binary_extractor(binary_extractor.get_process_path())
        .with_args(args.iter().map(String::as_str))
        .with_seed_pids(&seeds);
    runner = runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    let state = Arc::new(Mutex::new(LiveCaptureState::default()));
    let state_for_task = Arc::clone(&state);

    let stream = match runner.run().await {
        Ok(stream) => stream,
        Err(err) => {
            return Some(LiveEbpfCapture {
                state,
                handle: tokio::spawn(async {}),
                start_note: Some(format!("live eBPF capture did not start: {err}")),
            });
        }
    };

    let handle = tokio::spawn(async move {
        consume_live_ebpf_stream(stream, state_for_task).await;
    });

    Some(LiveEbpfCapture {
        state,
        handle,
        start_note,
    })
}

fn prepare_live_ebpf_privileges() -> Result<Option<String>, String> {
    if unsafe { libc::geteuid() } == 0 {
        return Ok(Some("live eBPF process capture enabled".to_string()));
    }

    if sudo_cached() {
        return Ok(Some(
            "live eBPF process capture enabled via cached sudo".to_string(),
        ));
    }

    let interactive = unsafe { libc::isatty(libc::STDIN_FILENO) == 1 };
    if !interactive {
        return Err("live eBPF capture requires sudo; non-interactive top is showing /proc + agent-native sessions only".to_string());
    }

    eprintln!("top live eBPF capture requires sudo. Requesting sudo access...");
    let ok = std::process::Command::new("sudo")
        .arg("-v")
        .status()
        .map(|status| status.success())
        .unwrap_or(false);
    if ok {
        Ok(Some("live eBPF process capture enabled".to_string()))
    } else {
        Err("live eBPF capture did not start: sudo authentication failed".to_string())
    }
}

async fn consume_live_ebpf_stream(
    mut stream: crate::runners::EventStream,
    state: Arc<Mutex<LiveCaptureState>>,
) {
    while let Some(event) = stream.next().await {
        record_live_ebpf_event(&state, &event);
    }
}

fn record_live_ebpf_event(state: &Arc<Mutex<LiveCaptureState>>, event: &Event) {
    let Ok(mut state) = state.lock() else {
        return;
    };
    if let Err(error) = state.view.ingest_event(event) {
        log::warn!("live eBPF capture failed to ingest view event: {}", error);
    }

    if event.source == "diagnostic"
        && event.data.get("type").and_then(|value| value.as_str()) == Some("runner_parse_error")
    {
        state.parse_errors += 1;
    }
}

// --- Live table mode ---

pub(crate) async fn run_live_top_query(
    binary_extractor: &BinaryExtractor,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> CommandResult {
    let limit = limit.clamp(1, 100);
    let should_clear_screen = count != Some(1);
    let mut live_view = LiveView::default();
    let capture = start_live_ebpf_capture(binary_extractor, options).await;

    let result = run_refresh_loop(interval_secs, count, || {
        if should_clear_screen {
            clear_screen();
        }
        let capture_snapshot = capture.as_ref().map(LiveEbpfCapture::snapshot);
        let mut top = live_view.refresh(capture_snapshot.as_ref(), limit, options)?;
        if let Some(note) = capture.as_ref().and_then(|capture| capture.start_note()) {
            top.notes.push(note.to_string());
        }
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        Ok(())
    });

    if let Some(capture) = capture {
        capture.stop();
    }

    result
}

// --- Live TUI mode ---

pub(crate) async fn run_live_top_tui(
    binary_extractor: &BinaryExtractor,
    interval_secs: u64,
    limit: usize,
    options: &TopOptions,
) -> CommandResult {
    let capture = start_live_ebpf_capture(binary_extractor, options).await;
    let result = run_live_top_tui_loop(interval_secs, limit, options, capture.as_ref());
    if let Some(capture) = capture {
        capture.stop();
    }
    result
}

struct LiveTopTerminalGuard;

impl LiveTopTerminalGuard {
    fn enter() -> io::Result<Self> {
        terminal::enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen, Hide)?;
        Ok(Self)
    }
}

impl Drop for LiveTopTerminalGuard {
    fn drop(&mut self) {
        let _ = terminal::disable_raw_mode();
        let mut stdout = io::stdout();
        let _ = execute!(stdout, Show, LeaveAlternateScreen);
    }
}

fn run_live_top_tui_loop(
    interval_secs: u64,
    limit: usize,
    options: &TopOptions,
    capture: Option<&LiveEbpfCapture>,
) -> CommandResult {
    let mut options = options.clone();
    let mut display_limit = limit.clamp(1, 100);
    let interval = Duration::from_secs(interval_secs.max(1));
    let _guard = LiveTopTerminalGuard::enter()?;
    let backend = CrosstermBackend::new(io::stdout());
    let mut terminal = Terminal::new(backend)?;
    terminal.clear()?;

    let mut live_view = LiveView::default();
    let mut current_top: Option<AgentTopOutput<'static>> = None;
    let mut selected = 0usize;
    let mut paused = false;
    let mut show_help = false;
    let mut show_diagnostics = false;
    let mut last_refresh = Instant::now() - interval;
    let mut force_refresh = true;

    loop {
        if force_refresh
            || (!paused && (current_top.is_none() || last_refresh.elapsed() >= interval))
        {
            let capture_snapshot = capture.map(LiveEbpfCapture::snapshot);
            let mut top = live_view.refresh(capture_snapshot.as_ref(), display_limit, &options)?;
            if let Some(note) = capture.and_then(LiveEbpfCapture::start_note) {
                top.notes.push(note.to_string());
            }
            sort_agent_rows(&mut top.rows, &options.sort);
            top.rows.truncate(display_limit);
            clamp_selected(&mut selected, top.rows.len());
            current_top = Some(top);
            last_refresh = Instant::now();
            force_refresh = false;
        }

        let top = current_top
            .as_ref()
            .expect("live top TUI refreshes before first render");
        terminal.draw(|frame| {
            draw_live_top_tui(
                frame,
                top,
                selected,
                &options,
                paused,
                show_help,
                show_diagnostics,
                interval_secs,
                display_limit,
            );
        })?;

        if crate::shutdown_requested() {
            break;
        }

        let wait = if paused {
            Duration::from_millis(250)
        } else {
            interval
                .checked_sub(last_refresh.elapsed())
                .unwrap_or(Duration::ZERO)
                .min(Duration::from_millis(250))
        };
        if !event::poll(wait)? {
            continue;
        }
        let CrosstermEvent::Key(key) = event::read()? else {
            continue;
        };
        if key.kind == KeyEventKind::Release {
            continue;
        }

        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => break,
            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => break,
            KeyCode::Char('?') => show_help = !show_help,
            KeyCode::Char('e') => show_diagnostics = !show_diagnostics,
            KeyCode::Char('p') => paused = !paused,
            KeyCode::Char('r') => force_refresh = true,
            KeyCode::Char('s') => {
                options.sort = next_sort_key(&options.sort);
                if let Some(top) = &mut current_top {
                    sort_agent_rows(&mut top.rows, &options.sort);
                    top.rows.truncate(display_limit);
                    clamp_selected(&mut selected, top.rows.len());
                }
            }
            KeyCode::Char('v') => options.view = next_view_key(&options.view),
            KeyCode::Char('+') | KeyCode::Char('=') => {
                display_limit = (display_limit + 1).min(100);
                force_refresh = true;
            }
            KeyCode::Char('-') => {
                display_limit = display_limit.saturating_sub(1).max(1);
                if let Some(top) = &mut current_top {
                    top.rows.truncate(display_limit);
                    clamp_selected(&mut selected, top.rows.len());
                }
            }
            KeyCode::Down | KeyCode::Char('j') => {
                if let Some(top) = &current_top
                    && selected + 1 < top.rows.len()
                {
                    selected += 1;
                }
            }
            KeyCode::Up | KeyCode::Char('k') => {
                selected = selected.saturating_sub(1);
            }
            KeyCode::Home => selected = 0,
            KeyCode::End => {
                if let Some(top) = &current_top {
                    selected = top.rows.len().saturating_sub(1);
                }
            }
            _ => {}
        }
    }

    Ok(())
}

fn clamp_selected(selected: &mut usize, rows: usize) {
    if rows == 0 {
        *selected = 0;
    } else if *selected >= rows {
        *selected = rows - 1;
    }
}

fn next_sort_key(current: &str) -> String {
    const SORTS: [&str; 8] = [
        "cpu", "rss", "tokens", "execs", "fail", "files", "net", "agent",
    ];
    let current = normalize_sort_key(current);
    let idx = SORTS
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    SORTS[(idx + 1) % SORTS.len()].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::output::tui::{tui_diagnostic_lines, tui_status_line};
    use serde_json::json;

    // The "touched local log without usage must not override DB tokens" guard now
    // lives in `cli_db::tests::sqlite_summary_uses_db_tokens_without_local_log_overlay`,
    // exercising the merged `SessionSummary` path that replaced `load_stat`.

    #[test]
    fn record_live_ebpf_event_ingests_process_file_and_network_events() {
        let temp = tempfile::tempdir().unwrap();
        let claude_path = temp.path().join("claude-path.jsonl");
        let codex_path = temp.path().join("codex-path.jsonl");
        let state = Arc::new(Mutex::new(LiveCaptureState::default()));
        let pid = std::process::id();

        for (comm, data) in [
            (
                "claude",
                json!({
                    "timestamp": 1,
                    "event": "FILE_OPEN",
                    "comm": "claude",
                    "pid": pid,
                    "filepath": claude_path,
                    "flags": 1
                }),
            ),
            (
                "codex",
                json!({
                    "timestamp": 1,
                    "event": "SUMMARY",
                    "comm": "codex",
                    "pid": pid,
                    "type": "WRITE",
                    "detail": codex_path,
                    "path_resolved": true,
                    "count": 3
                }),
            ),
            (
                "codex",
                json!({
                "timestamp": 1,
                "event": "SUMMARY",
                "comm": "codex",
                "pid": pid,
                "type": "WRITE",
                "detail": "fd=3",
                "path_resolved": false,
                "count": 1
                }),
            ),
            (
                "codex",
                json!({
                    "timestamp": 1,
                    "event": "SUMMARY",
                    "comm": "codex",
                    "pid": pid,
                    "type": "NET_CONNECT",
                    "detail": "127.0.0.1:7395",
                    "count": 2
                }),
            ),
        ] {
            record_live_ebpf_event(
                &state,
                &Event::new("process".to_string(), pid, comm.to_string(), data),
            );
        }

        let snapshot = state.lock().unwrap();
        let view_snapshot = snapshot.view.export_snapshot(SnapshotOptions {
            audit_limit: 10_000,
        });
        let counters = crate::model::AuditCounters::by_pid(&view_snapshot.audit_events);
        let counters = counters.get(&pid).unwrap();
        assert_eq!(counters.file_events, 3);
        assert_eq!(counters.network_events, 1);
    }

    #[test]
    fn tui_status_compacts_source_notes() {
        let top = AgentTopOutput {
            mode: "live sessions",
            db: None,
            duration_s: 0.0,
            view_events: 0,
            llm_calls: 0,
            total_tokens: 15,
            rows: vec![AgentTopRow {
                session: "codex:test".to_string(),
                agent: "codex".to_string(),
                pid: Some(42),
                model: Some("gpt-smoke".to_string()),
                age_s: Some(1.0),
                cpu_percent: 0.0,
                rss_mb: 0,
                processes: 1,
                tokens: Some(15),
                tools: 1,
                execs: 0,
                failures: 0,
                files: 0,
                network: 0,
                unattributed: 0,
                trace: "agent-native+proc+ebpf_file".to_string(),
                command: "codex".to_string(),
                workspace: None,
                last_message_at: None,
                tool_breakdown: Vec::new(),
                file_breakdown: Vec::new(),
            }],
            sections: Vec::new(),
            failures: Vec::new(),
            notes: vec![
                "agent-native sessions are the primary token/tool source (~/.claude, ~/.codex)"
                    .to_string(),
                "proc evidence uses /proc for CPU/RSS/process families".to_string(),
                "live eBPF capture did not start: sudo unavailable".to_string(),
            ],
        };

        assert_eq!(
            tui_status_line(&top),
            "agent-native | /proc | eBPF | session path linked | tokens 15"
        );
        assert_eq!(
            tui_diagnostic_lines(&top, 1),
            vec!["live eBPF capture did not start: sudo unavailable".to_string()]
        );
    }
}
