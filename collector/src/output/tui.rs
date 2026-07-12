// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::output::{AgentTopOutput, AgentTopRow, TopOptions, TopSection};
use crate::text::truncate_text;
use ratatui::{
    Frame,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Cell, Clear, Paragraph, Row, Table, TableState, Wrap},
};

#[derive(Debug, Clone)]
pub(crate) enum TopRecordOverlay {
    Prompt {
        command: String,
        error: Option<String>,
    },
    Running {
        lines: Vec<String>,
    },
}

pub(crate) fn draw_live_top_tui(
    frame: &mut Frame<'_>,
    top: &AgentTopOutput<'_>,
    selected: usize,
    options: &TopOptions,
    paused: bool,
    show_help: bool,
    show_diagnostics: bool,
    interval_secs: u64,
    display_limit: usize,
    record_status: Option<&str>,
    record_overlay: Option<&TopRecordOverlay>,
) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(4),
            Constraint::Min(10),
            Constraint::Length(8),
            Constraint::Length(5),
        ])
        .split(frame.area());

    render_top_summary(
        frame,
        chunks[0],
        top,
        options,
        paused,
        interval_secs,
        display_limit,
    );
    render_session_table(frame, chunks[1], top, selected);
    render_session_detail(frame, chunks[2], top, selected, options);
    render_top_footer(frame, chunks[3], top, record_status);

    if let Some(record_overlay) = record_overlay {
        render_record_overlay(frame, record_overlay);
    } else if show_help {
        render_top_help(frame);
    } else if show_diagnostics {
        render_top_diagnostics(frame, top);
    }
}

pub(crate) fn next_view_key(current: &str) -> String {
    const VIEWS: [&str; 5] = ["all", "processes", "files", "network", "models"];
    let current = normalize_view_key(current);
    let idx = VIEWS
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    VIEWS[(idx + 1) % VIEWS.len()].to_string()
}

fn render_top_summary(
    frame: &mut Frame<'_>,
    area: Rect,
    top: &AgentTopOutput<'_>,
    options: &TopOptions,
    paused: bool,
    interval_secs: u64,
    display_limit: usize,
) {
    let state = if paused { "paused" } else { "running" };
    let filter = top_filter_label(options);
    let lines = vec![
        Line::from(vec![
            Span::styled(
                "AgentSight top",
                Style::default().add_modifier(Modifier::BOLD),
            ),
            Span::raw(format!(
                "  mode={}  state={}  refresh={}s  rows={}/{}",
                top.mode,
                state,
                interval_secs.max(1),
                top.rows.len(),
                display_limit
            )),
        ]),
        Line::from(vec![
            Span::styled("sort ", label_style()),
            Span::raw(options.sort.clone()),
            Span::raw("  "),
            Span::styled("view ", label_style()),
            Span::raw(options.view.clone()),
            Span::raw("  "),
            Span::styled("filter ", label_style()),
            Span::raw(filter),
            Span::raw("  "),
            Span::styled("session tokens ", label_style()),
            Span::raw(format_token_value(Some(top.total_tokens))),
        ]),
        Line::from(vec![
            Span::styled("evidence ", label_style()),
            Span::raw(evidence_summary(top)),
        ]),
    ];
    let block = Block::default().borders(Borders::ALL);
    frame.render_widget(Paragraph::new(lines).block(block), area);
}

fn render_session_table(
    frame: &mut Frame<'_>,
    area: Rect,
    top: &AgentTopOutput<'_>,
    selected: usize,
) {
    let header = Row::new(vec![
        Cell::from("AGENT"),
        Cell::from("STATE"),
        Cell::from("AGE"),
        Cell::from("LAST MSG"),
        Cell::from("TOKENS"),
        Cell::from("HEALTH"),
        Cell::from("ACTIVITY"),
    ])
    .style(
        Style::default()
            .fg(Color::Cyan)
            .add_modifier(Modifier::BOLD),
    )
    .bottom_margin(1);

    let rows = top.rows.iter().map(|row| {
        Row::new(vec![
            Cell::from(truncate_text(&row.agent, 10)),
            Cell::from(row.state_label()),
            Cell::from(row.age_label()),
            Cell::from(row.last_msg_relative_label()),
            Cell::from(row.token_label()),
            Cell::from(row.health_label()),
            Cell::from(truncate_text(&row.activity_label(), 48)),
        ])
        .style(row_style(row))
    });

    let widths = [
        Constraint::Length(10),
        Constraint::Length(7),
        Constraint::Length(6),
        Constraint::Length(8),
        Constraint::Length(9),
        Constraint::Length(12),
        Constraint::Min(12),
    ];
    let table = Table::new(rows, widths)
        .header(header)
        .block(Block::default().title("sessions").borders(Borders::ALL))
        .column_spacing(1)
        .row_highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .fg(Color::White)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("> ");
    let mut state = TableState::default();
    if !top.rows.is_empty() {
        state.select(Some(selected));
    }
    frame.render_stateful_widget(table, area, &mut state);
}

fn render_session_detail(
    frame: &mut Frame<'_>,
    area: Rect,
    top: &AgentTopOutput<'_>,
    selected: usize,
    options: &TopOptions,
) {
    let title = format!("selected session - {}", normalize_view_key(&options.view));
    let lines = if let Some(row) = top.rows.get(selected) {
        session_detail_lines(row, top, options)
    } else {
        vec![
            Line::from("No active agent session matched this view."),
            Line::from("Run an agent, pass -c/-p, or inspect a saved session with top --db."),
        ]
    };
    let block = Block::default().title(title).borders(Borders::ALL);
    frame.render_widget(
        Paragraph::new(lines).block(block).wrap(Wrap { trim: true }),
        area,
    );
}

fn render_top_footer(
    frame: &mut Frame<'_>,
    area: Rect,
    top: &AgentTopOutput<'_>,
    record_status: Option<&str>,
) {
    let stop_hint = if record_status.is_some() {
        " | S stop record"
    } else {
        ""
    };
    let mut lines = vec![Line::from(vec![
        Span::styled("keys ", label_style()),
        Span::raw(format!(
            "q quit | up/down select | s sort{stop_hint} | v view | p pause | r refresh | R record PID | +/- rows | e errors | ? help",
        )),
    ])];
    lines.push(Line::from(vec![
        Span::styled("status ", label_style()),
        Span::raw(tui_status_line(top)),
    ]));
    if let Some(record_status) = record_status {
        lines.push(Line::from(vec![
            Span::styled("record ", label_style()),
            Span::raw(record_status.to_string()),
        ]));
    } else if let Some(message) = tui_diagnostic_lines(top, 1).into_iter().next() {
        lines.push(Line::from(vec![
            Span::styled("diagnostic ", label_style()),
            Span::raw(message),
        ]));
    }
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::default().title("status").borders(Borders::ALL))
            .wrap(Wrap { trim: true }),
        area,
    );
}

pub(crate) fn tui_status_line(top: &AgentTopOutput<'_>) -> String {
    let mut parts = Vec::new();
    if top.rows.iter().any(|row| row.evidence().agent_native) {
        parts.push("agent-native".to_string());
    }
    if top.rows.iter().any(|row| row.evidence().proc) {
        parts.push("/proc".to_string());
    }
    if top.rows.iter().any(|row| row.evidence().ebpf) {
        parts.push("eBPF".to_string());
    }
    if top
        .rows
        .iter()
        .any(|row| row.evidence().has_session_path_link())
    {
        parts.push("session path linked".to_string());
    }
    if top.total_tokens > 0 {
        parts.push(format!(
            "tokens {}",
            format_token_value(Some(top.total_tokens))
        ));
    }
    if parts.is_empty() {
        if top.rows.is_empty() {
            "no matching sessions".to_string()
        } else {
            "observing".to_string()
        }
    } else {
        parts.join(" | ")
    }
}

pub(crate) fn tui_diagnostic_lines(top: &AgentTopOutput<'_>, limit: usize) -> Vec<String> {
    if limit == 0 {
        return Vec::new();
    }
    let mut out = Vec::new();
    let recent = crate::recent_tui_diagnostics(limit);
    for message in top
        .notes
        .iter()
        .filter(|note| !is_tui_status_note(note))
        .chain(recent.iter())
    {
        if !out.contains(message) {
            out.push(message.clone());
        }
        if out.len() >= limit {
            break;
        }
    }
    out
}

fn is_tui_status_note(note: &str) -> bool {
    note.starts_with("agent-native sessions are")
        || note.starts_with("proc evidence uses")
        || note.starts_with("agent-native sessions bind")
        || note.starts_with("ebpf evidence is")
}

fn render_top_help(frame: &mut Frame<'_>) {
    let area = centered_rect(62, 52, frame.area());
    frame.render_widget(Clear, area);
    let lines = vec![
        Line::from(vec![Span::styled(
            "AgentSight top keys",
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(""),
        Line::from("q or Esc       exit"),
        Line::from("up/down, k/j   select a session"),
        Line::from("s              cycle sort: cpu, rss, tokens, execs, fail, files, net, agent"),
        Line::from("S              when recording, prompt stop record"),
        Line::from("v              cycle detail view: all, processes, files, network, models"),
        Line::from("p              pause or resume refresh"),
        Line::from("r              refresh now"),
        Line::from("R              record selected PID"),
        Line::from("+/-            change row limit"),
        Line::from("?              close this help"),
    ];
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::default().title("help").borders(Borders::ALL))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn render_record_overlay(frame: &mut Frame<'_>, overlay: &TopRecordOverlay) {
    let area = centered_rect(76, 34, frame.area());
    frame.render_widget(Clear, area);
    let (title, lines) = match overlay {
        TopRecordOverlay::Prompt { command, error } => {
            let mut lines = vec![
                Line::from(vec![Span::styled(
                    "Record selected PID",
                    Style::default()
                        .fg(Color::Cyan)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(""),
                Line::from("Attach options only; values are split on spaces."),
                Line::from(""),
                Line::from(command.clone()),
                Line::from(""),
                Line::from("Enter start | Esc cancel | Backspace edit"),
            ];
            if let Some(error) = error {
                lines.push(Line::from(""));
                lines.push(Line::from(vec![
                    Span::styled("error ", Style::default().fg(Color::Red)),
                    Span::raw(error.clone()),
                ]));
            }
            ("record", lines)
        }
        TopRecordOverlay::Running { lines } => {
            let mut rendered = vec![
                Line::from(vec![Span::styled(
                    "Record already running",
                    Style::default()
                        .fg(Color::Yellow)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(""),
            ];
            rendered.extend(lines.iter().cloned().map(Line::from));
            rendered.push(Line::from(""));
            rendered.push(Line::from("Enter/S stop | Esc cancel"));
            ("record", rendered)
        }
    };
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::default().title(title).borders(Borders::ALL))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn render_top_diagnostics(frame: &mut Frame<'_>, top: &AgentTopOutput<'_>) {
    let area = centered_rect(76, 48, frame.area());
    frame.render_widget(Clear, area);
    let messages = tui_diagnostic_lines(top, 8);
    let mut lines = vec![
        Line::from(vec![Span::styled(
            "Diagnostics",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(""),
    ];
    if messages.is_empty() {
        lines.push(Line::from("No warnings or errors captured."));
    } else {
        for message in messages {
            lines.push(Line::from(message));
        }
    }
    lines.push(Line::from(""));
    lines.push(Line::from("e close | ? help | q quit"));
    frame.render_widget(
        Paragraph::new(lines)
            .block(Block::default().title("diagnostics").borders(Borders::ALL))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn session_detail_lines(
    row: &AgentTopRow,
    top: &AgentTopOutput<'_>,
    options: &TopOptions,
) -> Vec<Line<'static>> {
    let view = normalize_view_key(&options.view);
    let header = format!(
        "{}  model={}  trace={}",
        row.session,
        row.model_label(),
        row.trace,
    );
    let tools = if !row.tool_breakdown.is_empty() {
        &row.tool_breakdown
    } else {
        find_section(&top.sections, "Tools")
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    };
    let files = if !row.file_breakdown.is_empty() {
        &row.file_breakdown
    } else {
        find_section(&top.sections, "Files")
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    };

    match view.as_str() {
        "processes" => {
            let mut lines = vec![
                detail_line("session", header),
                detail_line(
                    "resources",
                    format!(
                        "pid={}  cpu={:.1}%  rss={} MB  tree={}",
                        row.pid
                            .map(|p| p.to_string())
                            .unwrap_or_else(|| "-".to_string()),
                        row.cpu_percent,
                        row.rss_mb,
                        row.processes
                    ),
                ),
                detail_line(
                    "workspace",
                    row.workspace.as_deref().unwrap_or("-").to_string(),
                ),
            ];
            if let Some(items) = find_section(&top.sections, "Processes") {
                lines.push(detail_line("top execs", format_top_items(items, 8)));
            }
            if !tools.is_empty() {
                lines.push(detail_line("top tools", format_top_items(tools, 6)));
            }
            lines
        }
        "files" => {
            let mut lines = vec![
                detail_line("session", header),
                detail_line(
                    "workspace",
                    row.workspace.as_deref().unwrap_or("-").to_string(),
                ),
            ];
            if !files.is_empty() {
                let dirs = aggregate_to_dirs(files);
                lines.push(detail_line("top dirs", format_top_paths(&dirs, 5)));
                lines.push(detail_line("top files", format_top_paths(files, 5)));
            } else {
                lines.push(detail_line(
                    "files",
                    format!("{} unique (use `record` for file-level detail)", row.files),
                ));
            }
            if !tools.is_empty() {
                lines.push(detail_line("top tools", format_top_items(tools, 6)));
            }
            lines
        }
        "network" => {
            let mut lines = vec![
                detail_line("session", header),
                detail_line(
                    "workspace",
                    row.workspace.as_deref().unwrap_or("-").to_string(),
                ),
            ];
            if let Some(items) = find_section(&top.sections, "Network") {
                lines.push(detail_line("top hosts", format_top_items(items, 3)));
            } else {
                lines.push(detail_line(
                    "network",
                    format!("{} hosts (use `record` for network detail)", row.network),
                ));
            }
            if let Some(items) = find_section(&top.sections, "Models") {
                lines.push(detail_line("models", format_top_items(items, 5)));
            }
            lines
        }
        "models" => {
            let mut lines = vec![
                detail_line("session", header),
                detail_line(
                    "workspace",
                    row.workspace.as_deref().unwrap_or("-").to_string(),
                ),
            ];
            if let Some(items) = find_section(&top.sections, "Models") {
                lines.push(detail_line("models", format_top_items(items, 5)));
            }
            if !tools.is_empty() {
                lines.push(detail_line("top tools", format_top_items(tools, 6)));
            }
            lines
        }
        _ => {
            let mut lines = vec![
                detail_line("session", header),
                detail_line(
                    "model",
                    format!(
                        "{}  tokens={}  tools={}  last_msg={}",
                        row.model_label(),
                        row.token_label(),
                        row.tools,
                        row.last_msg_label(),
                    ),
                ),
                detail_line(
                    "workspace",
                    row.workspace.as_deref().unwrap_or("-").to_string(),
                ),
                detail_line(
                    "resources",
                    format!(
                        "cpu={:.1}%  rss={} MB  processes={}",
                        row.cpu_percent, row.rss_mb, row.processes
                    ),
                ),
            ];
            if !tools.is_empty() {
                lines.push(detail_line("top tools", format_top_items(tools, 6)));
            }
            if !files.is_empty() {
                lines.push(detail_line("top files", format_top_paths(files, 5)));
            }
            lines
        }
    }
}

fn find_section<'a>(sections: &'a [TopSection], title: &str) -> Option<&'a Vec<(String, i64)>> {
    sections
        .iter()
        .find(|(t, _, _)| *t == title)
        .map(|(_, _, items)| items)
        .filter(|items| !items.is_empty())
}

fn format_top_items(items: &[(String, i64)], limit: usize) -> String {
    format_top_items_with(items, limit, |name| {
        crate::text::truncate_with_ellipsis(name, 28)
    })
}

fn format_top_paths(items: &[(String, i64)], limit: usize) -> String {
    format_top_items_with(items, limit, |name| truncate_path(name, 32))
}

fn format_top_items_with(
    items: &[(String, i64)],
    limit: usize,
    shorten: impl Fn(&str) -> String,
) -> String {
    let parts: Vec<_> = items
        .iter()
        .take(limit)
        .map(|(name, count)| {
            let short = shorten(name);
            format!("{short}({count})")
        })
        .collect();
    if parts.is_empty() {
        "-".to_string()
    } else {
        parts.join("  ")
    }
}

fn truncate_path(path: &str, max: usize) -> String {
    if path.len() <= max {
        return path.to_string();
    }
    let mut components: Vec<&str> = path.split('/').filter(|s| !s.is_empty()).collect();
    if components.len() <= 2 {
        return format!("...{}", &path[path.len().saturating_sub(max - 3)..]);
    }
    let tail = components.split_off(components.len().saturating_sub(2));
    let suffix = tail.join("/");
    if suffix.len() + 4 >= max {
        return format!(".../{suffix}");
    }
    let budget = max - suffix.len() - 4;
    let head = components.first().copied().unwrap_or("");
    if head.len() <= budget {
        format!("{head}/.../{suffix}")
    } else {
        format!(".../{suffix}")
    }
}

fn aggregate_to_dirs(items: &[(String, i64)]) -> Vec<(String, i64)> {
    let mut dir_counts = std::collections::BTreeMap::new();
    for (path, count) in items {
        let dir = match path.rfind('/') {
            Some(pos) if pos > 0 => &path[..pos],
            _ => path.as_str(),
        };
        *dir_counts.entry(dir.to_string()).or_insert(0i64) += count;
    }
    let mut sorted: Vec<_> = dir_counts.into_iter().collect();
    sorted.sort_by_key(|b| std::cmp::Reverse(b.1));
    sorted.truncate(5);
    sorted
}

fn detail_line(label: &'static str, value: String) -> Line<'static> {
    Line::from(vec![
        Span::styled(format!("{label}: "), label_style()),
        Span::raw(value),
    ])
}

fn centered_rect(percent_x: u16, percent_y: u16, area: Rect) -> Rect {
    let vertical = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(area);
    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(vertical[1])[1]
}

fn label_style() -> Style {
    Style::default()
        .fg(Color::Cyan)
        .add_modifier(Modifier::BOLD)
}

fn row_style(row: &AgentTopRow) -> Style {
    let evidence = row.evidence();
    if row.failures > 0 {
        Style::default().fg(Color::Red)
    } else if evidence.ebpf {
        Style::default().fg(Color::Green)
    } else if evidence.has_history() {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default()
    }
}

fn evidence_summary(top: &AgentTopOutput<'_>) -> String {
    let local = top
        .rows
        .iter()
        .filter(|row| row.evidence().has_history())
        .count();
    let proc_rows = top.rows.iter().filter(|row| row.evidence().proc).count();
    let ebpf = top.rows.iter().filter(|row| row.evidence().ebpf).count();
    let ebpf_file = top
        .rows
        .iter()
        .filter(|row| row.evidence().ebpf_file)
        .count();
    let proc_fd = top.rows.iter().filter(|row| row.evidence().proc_fd).count();
    let sticky = top.rows.iter().filter(|row| row.evidence().sticky).count();
    let mut parts = Vec::new();
    if local > 0 {
        parts.push(format!("local={local}"));
    }
    if proc_rows > 0 {
        parts.push(format!("proc={proc_rows}"));
    }
    if proc_fd > 0 {
        parts.push(format!("fd={proc_fd}"));
    }
    if sticky > 0 {
        parts.push(format!("sticky={sticky}"));
    }
    if ebpf_file > 0 {
        parts.push(format!("ebpf_file={ebpf_file}"));
    }
    if ebpf > 0 {
        parts.push(format!("ebpf={ebpf}"));
    }
    if parts.is_empty() {
        "none yet".to_string()
    } else {
        parts.join(" ")
    }
}

fn top_filter_label(options: &TopOptions) -> String {
    if let Some(pid) = options.pid {
        format!("pid={pid}")
    } else if let Some(comm) = &options.comm {
        format!("comm={comm}")
    } else {
        "known agents".to_string()
    }
}

fn normalize_view_key(view: &str) -> String {
    match view.to_ascii_lowercase().as_str() {
        "process" | "proc" => "processes".to_string(),
        "file" | "fs" => "files".to_string(),
        "net" => "network".to_string(),
        "model" | "tokens" => "models".to_string(),
        "processes" | "files" | "network" | "models" => view.to_ascii_lowercase(),
        _ => "all".to_string(),
    }
}

fn format_token_value(value: Option<i64>) -> String {
    value
        .map(super::format::format_count)
        .unwrap_or_else(|| "-".to_string())
}
