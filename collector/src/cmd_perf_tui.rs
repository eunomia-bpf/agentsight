// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::binary_extractor::BinaryExtractor;
use crate::cmd_perf::load_top_output;
use crate::cmd_perf_live::{LiveEbpfCapture, start_live_ebpf_capture};
use crate::cmd_tui_record::{
    TuiRecordStatus, TuiRecordTask, default_record_command_for_row, parse_tui_record_command,
};
use crate::output::{
    AgentTopOutput, TopOptions, TopRecordOverlay, draw_live_top_tui, next_view_key,
};
use crate::view::live_top::LiveView;
use crate::view::top::{normalize_sort_key, sort_agent_rows};
use crossterm::{
    cursor::{Hide, Show},
    event::{self, Event as CrosstermEvent, KeyCode, KeyEventKind, KeyModifiers},
    execute,
    terminal::{self, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{Terminal, backend::CrosstermBackend};
use std::io;
use std::time::{Duration, Instant};

pub(crate) async fn run_live_top_tui(
    binary_extractor: &BinaryExtractor,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let capture = start_live_ebpf_capture(binary_extractor, options).await;
    let mut live_view = LiveView::default();
    let result = run_top_tui_loop(
        interval_secs,
        limit,
        count,
        options,
        true,
        |display_limit, options| {
            let capture_snapshot = capture.as_ref().map(LiveEbpfCapture::snapshot);
            let mut top = live_view.refresh(capture_snapshot.as_ref(), display_limit, options)?;
            if let Some(note) = capture.as_ref().and_then(|capture| capture.start_note()) {
                top.notes.push(note.to_string());
            }
            Ok(top)
        },
    );
    if let Some(capture) = capture {
        capture.stop();
    }
    result
}

pub(crate) fn run_saved_top_tui(
    db: &str,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    run_top_tui_loop(
        interval_secs,
        limit,
        count,
        options,
        false,
        |display_limit, options| load_top_output(db, display_limit, options),
    )
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

fn run_top_tui_loop<'a, F>(
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
    allow_record: bool,
    mut refresh: F,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>>
where
    F: FnMut(
        usize,
        &TopOptions,
    ) -> Result<AgentTopOutput<'a>, Box<dyn std::error::Error + Send + Sync>>,
{
    let mut options = options.clone();
    let mut display_limit = limit.clamp(1, 100);
    let interval = Duration::from_secs(interval_secs.max(1));
    let _guard = LiveTopTerminalGuard::enter()?;
    let backend = CrosstermBackend::new(io::stdout());
    let mut terminal = Terminal::new(backend)?;
    terminal.clear()?;

    let mut current_top: Option<AgentTopOutput<'a>> = None;
    let mut selected = 0usize;
    let mut paused = false;
    let mut show_help = false;
    let mut show_diagnostics = false;
    let mut record_prompt: Option<RecordPrompt> = None;
    let mut record_task: Option<TuiRecordTask> = None;
    let mut last_refresh = Instant::now() - interval;
    let mut force_refresh = true;
    let mut refreshes = 0u32;

    loop {
        if force_refresh
            || (!paused && (current_top.is_none() || last_refresh.elapsed() >= interval))
        {
            let mut top = refresh(display_limit, &options)?;
            sort_agent_rows(&mut top.rows, &options.sort);
            top.rows.truncate(display_limit);
            clamp_selected(&mut selected, top.rows.len());
            current_top = Some(top);
            last_refresh = Instant::now();
            force_refresh = false;
            refreshes += 1;
        }

        let top = current_top
            .as_ref()
            .expect("live top TUI refreshes before first render");
        let record_status = record_task
            .as_ref()
            .map(|task| record_status_line(&task.status()));
        let record_overlay = record_overlay(&record_prompt, record_task.as_ref());
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
                record_status.as_deref(),
                record_overlay.as_ref(),
            );
        })?;

        if count.is_some_and(|max| refreshes >= max) || crate::shutdown_requested() {
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

        if let Some(prompt) = &mut record_prompt {
            if prompt.command.is_empty()
                && record_task.as_ref().is_some_and(|task| !task.is_finished())
            {
                match key.code {
                    KeyCode::Esc => record_prompt = None,
                    KeyCode::Char('s') => {
                        if let Some(task) = &mut record_task {
                            task.stop();
                            crate::push_tui_diagnostic("record stop requested");
                        }
                        record_prompt = None;
                    }
                    _ => {}
                }
                continue;
            }
            match key.code {
                KeyCode::Esc => record_prompt = None,
                KeyCode::Enter => match parse_tui_record_command(&prompt.command) {
                    Ok(command) => {
                        if record_task.as_ref().is_some_and(|task| !task.is_finished()) {
                            prompt.error = Some("a record task is already running".to_string());
                        } else {
                            crate::push_tui_diagnostic(&format!(
                                "record started: pid {} -> {}",
                                command.pid, command.db_path
                            ));
                            record_task = Some(TuiRecordTask::spawn(
                                command,
                                crate::cmd_trace::DEFAULT_SERVER_LISTEN.to_string(),
                            ));
                            record_prompt = None;
                        }
                    }
                    Err(error) => prompt.error = Some(error),
                },
                KeyCode::Backspace => {
                    prompt.command.pop();
                    prompt.error = None;
                }
                KeyCode::Char(ch) => {
                    if !key.modifiers.contains(KeyModifiers::CONTROL) {
                        prompt.command.push(ch);
                        prompt.error = None;
                    }
                }
                _ => {}
            }
            continue;
        }

        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => break,
            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => break,
            KeyCode::Char('?') => show_help = !show_help,
            KeyCode::Char('e') => show_diagnostics = !show_diagnostics,
            KeyCode::Char('p') => paused = !paused,
            KeyCode::Char('r') => force_refresh = true,
            KeyCode::Char('R') => {
                if !allow_record {
                    crate::push_tui_diagnostic(
                        "record from top is only available for live sessions",
                    );
                    continue;
                }
                if let Some(task) = &record_task
                    && !task.is_finished()
                {
                    show_help = false;
                    show_diagnostics = false;
                    record_prompt = Some(RecordPrompt {
                        command: String::new(),
                        error: Some(
                            "record already running; press s in this dialog to stop".to_string(),
                        ),
                    });
                    continue;
                }
                match current_top
                    .as_ref()
                    .and_then(|top| top.rows.get(selected))
                    .map(|row| default_record_command_for_row(Some(row), 7395))
                    .unwrap_or_else(|| default_record_command_for_row(None, 7395))
                {
                    Ok(command) => {
                        show_help = false;
                        show_diagnostics = false;
                        record_prompt = Some(RecordPrompt {
                            command: command.display_command(),
                            error: None,
                        });
                    }
                    Err(error) => crate::push_tui_diagnostic(&error),
                }
            }
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

    if let Some(mut task) = record_task {
        task.stop();
    }

    Ok(())
}

#[derive(Debug, Clone)]
struct RecordPrompt {
    command: String,
    error: Option<String>,
}

fn record_status_line(status: &TuiRecordStatus) -> String {
    let server = status
        .server_url
        .as_deref()
        .map(|url| format!("  server={url}"))
        .unwrap_or_default();
    format!(
        "{}  db={}  status={}{}",
        status.target, status.db_path, status.message, server
    )
}

fn record_overlay(
    prompt: &Option<RecordPrompt>,
    task: Option<&TuiRecordTask>,
) -> Option<TopRecordOverlay> {
    if let Some(prompt) = prompt {
        if prompt.command.is_empty()
            && let Some(task) = task
        {
            return Some(TopRecordOverlay::Running {
                lines: record_running_lines(&task.status()),
            });
        }
        return Some(TopRecordOverlay::Prompt {
            command: prompt.command.clone(),
            error: prompt.error.clone(),
        });
    }
    None
}

fn record_running_lines(status: &TuiRecordStatus) -> Vec<String> {
    let mut lines = vec![
        format!("target: {}", status.target),
        format!("db: {}", status.db_path),
        format!("status: {}", status.message),
    ];
    if let Some(url) = &status.server_url {
        lines.push(format!("server: {url}"));
    }
    lines
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
    use super::{RecordPrompt, record_running_lines, record_status_line};
    use crate::cmd_tui_record::TuiRecordStatus;
    use crate::output::tui::{tui_diagnostic_lines, tui_status_line};
    use crate::output::{AgentTopOutput, AgentTopRow};

    #[test]
    fn record_status_and_running_lines_include_target_db_and_server() {
        let status = TuiRecordStatus {
            target: "pid 42".to_string(),
            db_path: "agentsight-test.db".to_string(),
            server_url: Some("http://127.0.0.1:7395/".to_string()),
            message: "recording".to_string(),
            finished: false,
        };

        assert_eq!(
            record_status_line(&status),
            "pid 42  db=agentsight-test.db  status=recording  server=http://127.0.0.1:7395/"
        );
        assert_eq!(
            record_running_lines(&status),
            vec![
                "target: pid 42".to_string(),
                "db: agentsight-test.db".to_string(),
                "status: recording".to_string(),
                "server: http://127.0.0.1:7395/".to_string(),
            ]
        );

        let prompt = RecordPrompt {
            command: "agentsight record -p 42 --db agentsight-test.db --server-port 7395"
                .to_string(),
            error: None,
        };
        assert!(prompt.command.contains("record -p 42"));
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
                "agent-native sessions are the primary token/tool source".to_string(),
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
