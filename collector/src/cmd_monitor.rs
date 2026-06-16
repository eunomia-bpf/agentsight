// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::output::{AgentTopOutput, AgentTopRow, TopOptions, clear_screen, print_agent_top};
use crate::sources::proc::{self as procfs, ProcSnapshot};
use crate::view::live_top::{LiveMonitorSample, LiveView};
use crate::view::top::sort_agent_rows;
use chrono::{Datelike, Local, NaiveDate};
use rusqlite::{Connection, OpenFlags, params};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Write};
use std::net::{Ipv4Addr, Ipv6Addr};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const MONITOR_INTERVAL_SECS: u64 = 2;
const SESSION_SCAN_LIMIT: usize = 25;
const MONITOR_SERVICE_NAME: &str = "agentsight-monitor.service";
const DETAIL_EDGE_LIMIT: usize = 5;
const DETAIL_SAMPLE_INTERVAL_SECS: u64 = 30;

#[derive(Debug, Clone)]
struct MonitorSample {
    window_start_ms: u64,
    window_end_ms: u64,
    sessions: Vec<MonitorSessionSample>,
}

#[derive(Debug, Clone)]
struct MonitorSessionSample {
    session_id: String,
    display_id: String,
    agent_type: String,
    root_pid: u32,
    root_starttime_ticks: u64,
    match_evidence: String,
    match_confidence: f32,
    session_path: Option<String>,
    command: String,
    cwd: Option<String>,
    process_count: usize,
    cpu_ms: u64,
    rss_bytes: u64,
    read_bytes: u64,
    write_bytes: u64,
    file_targets: usize,
    network_targets: usize,
    process_samples: Vec<MonitorProcessSample>,
    file_samples: Vec<MonitorTargetSample>,
    network_samples: Vec<MonitorTargetSample>,
}

#[derive(Debug, Clone)]
struct MonitorProcessSample {
    rank_kind: &'static str,
    pid: u32,
    pid_starttime_ticks: u64,
    ppid: u32,
    depth: usize,
    comm: String,
    command: String,
    cwd: Option<String>,
    cpu_ms: u64,
    cpu_percent: f64,
    rss_bytes: u64,
    read_bytes: u64,
    write_bytes: u64,
}

#[derive(Debug, Clone)]
struct MonitorTargetSample {
    rank_kind: &'static str,
    target: String,
    count: usize,
}

#[derive(Debug, Default)]
struct MonitorWriteStats {
    sessions: usize,
    windows: usize,
}

#[derive(Debug, Default)]
struct MonitorIoState {
    previous: BTreeMap<procfs::ProcessKey, (u64, u64)>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct MonitorPidFile {
    pid: u32,
    db_path: PathBuf,
    started_ms: u64,
}

pub(crate) async fn run_monitor() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    if let Some(active) = active_monitor() {
        println!(
            "AgentSight monitor already running: pid {} -> {}",
            active.pid,
            active.db_path.display()
        );
        return Ok(());
    }

    let mut store = MonitorStore::open_default()?;
    let mut io_state = MonitorIoState::default();
    let pid_file = MonitorPidFile {
        pid: std::process::id(),
        db_path: store.path().to_path_buf(),
        started_ms: now_epoch_ms(),
    };
    write_monitor_pid_file(&pid_file)?;
    let _pid_guard = MonitorPidGuard {
        path: monitor_pid_path(),
        pid: pid_file.pid,
    };

    let mut live_view = LiveView::default();
    let interval = Duration::from_secs(MONITOR_INTERVAL_SECS);
    let shutdown = crate::shutdown_notify();

    println!(
        "Monitoring matched agent sessions every {}s",
        MONITOR_INTERVAL_SECS
    );
    println!("Writing to {}", store.path().display());
    println!("PID file {}", monitor_pid_path().display());

    loop {
        let live = live_view.refresh_monitor_sample(SESSION_SCAN_LIMIT)?;
        let sample = build_monitor_sample(&live, &mut io_state);
        let stats = store.insert_sample(&sample)?;
        print_monitor_tick(store.path(), &stats);
        io::stdout().flush()?;

        if crate::shutdown_requested() {
            break;
        }

        tokio::select! {
            _ = tokio::time::sleep(interval) => {}
            _ = shutdown.notified() => break,
        }
    }

    store.checkpoint()?;
    Ok(())
}

pub(crate) fn install_monitor_service() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    if !cfg!(target_os = "linux") {
        return Err(
            "monitor service install currently supports Linux systemd user services".into(),
        );
    }

    let exe = std::env::current_exe()?;
    let unit_dir = systemd_user_dir()?;
    std::fs::create_dir_all(&unit_dir)?;
    let unit_path = unit_dir.join(MONITOR_SERVICE_NAME);
    std::fs::write(&unit_path, monitor_service_unit(&exe)?)?;

    run_systemctl_user(["daemon-reload"])?;
    run_systemctl_user(["enable", MONITOR_SERVICE_NAME])?;
    run_systemctl_user(["restart", MONITOR_SERVICE_NAME]).map_err(|err| {
        io::Error::other(format!(
            "installed and enabled {MONITOR_SERVICE_NAME}, but failed to start it; \
             inspect with `systemctl --user status {MONITOR_SERVICE_NAME}`: {err}"
        ))
    })?;

    println!("Installed AgentSight monitor service");
    println!("Unit: {}", unit_path.display());
    println!("ExecStart: {} monitor", exe.display());
    println!("Status: systemctl --user status {MONITOR_SERVICE_NAME}");
    Ok(())
}

pub(crate) fn active_monitor_db_path() -> Option<PathBuf> {
    active_monitor().map(|pid_file| pid_file.db_path)
}

pub(crate) async fn run_monitor_top_query(
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let active = active_monitor().ok_or("monitor is not running")?;
    let limit = limit.clamp(1, 100);
    let interval = Duration::from_secs(interval_secs.max(1));
    let shutdown = crate::shutdown_notify();
    let mut iterations = 0u32;
    let should_clear_screen = count != Some(1);

    loop {
        if should_clear_screen {
            clear_screen();
        }
        let mut top = build_monitor_top(&active.db_path, limit, options)?;
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        io::stdout().flush()?;

        iterations += 1;
        if count.is_some_and(|max| iterations >= max) || crate::shutdown_requested() {
            break;
        }
        tokio::select! {
            _ = tokio::time::sleep(interval) => {}
            _ = shutdown.notified() => break,
        }
    }

    Ok(())
}

fn print_monitor_tick(path: &Path, stats: &MonitorWriteStats) {
    println!(
        "saved {} sessions | {} windows -> {}",
        stats.sessions,
        stats.windows,
        path.display()
    );
}

fn build_monitor_top(
    db_path: &Path,
    limit: usize,
    options: &TopOptions,
) -> Result<AgentTopOutput<'static>, Box<dyn std::error::Error + Send + Sync>> {
    let rows = load_monitor_top_rows(db_path, options)?;
    let db_note = format!(
        "using background monitor data from {}; no live eBPF/probes started",
        db_path.display()
    );
    let mut process_counts = BTreeMap::new();
    for row in &rows {
        *process_counts.entry(row.agent.clone()).or_insert(0i64) += row.processes.max(1) as i64;
    }
    let mut sections = Vec::new();
    if !process_counts.is_empty() {
        let mut sorted = process_counts.into_iter().collect::<Vec<_>>();
        sorted.sort_by_key(|(_, count)| std::cmp::Reverse(*count));
        sorted.truncate(limit);
        sections.push(("Processes", "monitor", sorted));
    }

    Ok(AgentTopOutput {
        mode: "monitor",
        db: None,
        duration_s: 0.0,
        view_events: rows.len() as i64,
        llm_calls: 0,
        total_tokens: 0,
        rows,
        sections,
        failures: Vec::new(),
        notes: vec![db_note],
    })
}

fn load_monitor_top_rows(
    db_path: &Path,
    options: &TopOptions,
) -> rusqlite::Result<Vec<AgentTopRow>> {
    let conn = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    let network_targets_expr = if monitor_windows_has_network_targets_column(&conn)? {
        "w.network_targets"
    } else {
        "0"
    };
    let now_ms = now_epoch_ms();
    let sql = format!(
        "SELECT
            t.session_id, t.display_id, t.agent_type, t.root_pid, t.first_seen_ms,
            t.command, t.cwd, w.window_start_ms, w.window_end_ms, w.process_count,
            w.cpu_ms, w.rss_bytes, w.file_targets, {network_targets_expr}
         FROM monitor_windows w
         JOIN tracked_sessions t USING(session_id, root_pid, root_starttime_ticks)
         WHERE w.id IN (
            SELECT MAX(id)
            FROM monitor_windows
            GROUP BY session_id, root_pid, root_starttime_ticks
         )
         ORDER BY w.window_end_ms DESC"
    );
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map([], |row| {
        let session_id: String = row.get(0)?;
        let display_id: String = row.get(1)?;
        let agent_type: String = row.get(2)?;
        let root_pid: u32 = row.get::<_, i64>(3)? as u32;
        let first_seen_ms: u64 = row.get::<_, i64>(4)? as u64;
        let command: String = row.get(5)?;
        let cwd: Option<String> = row.get(6)?;
        let window_start_ms: u64 = row.get::<_, i64>(7)? as u64;
        let window_end_ms: u64 = row.get::<_, i64>(8)? as u64;
        let process_count: usize = row.get::<_, i64>(9)? as usize;
        let cpu_ms: u64 = row.get::<_, i64>(10)? as u64;
        let rss_bytes: u64 = row.get::<_, i64>(11)? as u64;
        let file_targets: usize = row.get::<_, i64>(12)? as usize;
        let network_targets: usize = row.get::<_, i64>(13)? as usize;
        let window_ms = window_end_ms.saturating_sub(window_start_ms).max(1);
        let cpu_percent = cpu_ms as f64 / window_ms as f64 * 100.0;
        Ok(AgentTopRow {
            session: if display_id.is_empty() {
                short_monitor_session_id(&session_id)
            } else {
                display_id
            },
            agent: agent_type,
            pid: Some(root_pid),
            model: None,
            age_s: Some(now_ms.saturating_sub(first_seen_ms) as f64 / 1000.0),
            cpu_percent,
            rss_mb: bytes_to_mb(rss_bytes),
            processes: process_count,
            tokens: None,
            tools: 0,
            execs: 0,
            failures: 0,
            files: file_targets,
            network: network_targets,
            unattributed: 0,
            trace: "proc+db".to_string(),
            command,
            workspace: cwd,
            last_message_at: None,
            tool_breakdown: Vec::new(),
            file_breakdown: Vec::new(),
        })
    })?;

    let mut out = Vec::new();
    for row in rows {
        let row = row?;
        if options.matches(row.pid, Some(&row.agent), Some(&row.command)) {
            out.push(row);
        }
    }
    Ok(out)
}

fn build_monitor_sample(live: &LiveMonitorSample, io_state: &mut MonitorIoState) -> MonitorSample {
    let window_end_ms = live.at_ms;
    let window_start_ms = window_end_ms.saturating_sub(MONITOR_INTERVAL_SECS * 1000);
    let include_detail_samples = should_store_detail_samples(window_start_ms, window_end_ms);
    let mut sessions = Vec::new();
    let mut current_io = BTreeMap::new();

    for session in &live.sessions {
        let (file_target_counts, socket_inodes_by_pid) =
            collect_fd_target_counts(&session.family, &live.current);
        let network_target_counts = collect_network_target_counts(&socket_inodes_by_pid);
        let process_samples = collect_process_samples(
            &session.family,
            &live.current,
            live.previous.as_ref(),
            io_state,
            &mut current_io,
        );
        let (cpu_ms, rss_bytes, read_bytes, write_bytes) =
            aggregate_process_samples(&process_samples);

        sessions.push(MonitorSessionSample {
            session_id: session.session_id.clone(),
            display_id: session.display_id.clone(),
            agent_type: session.agent_type.clone(),
            root_pid: session.root_pid,
            root_starttime_ticks: session.root_starttime_ticks,
            match_evidence: session.evidence.to_string(),
            match_confidence: session.confidence,
            session_path: session
                .session_path
                .as_ref()
                .map(|path| path.to_string_lossy().to_string()),
            command: truncate_field(&session.command, 512),
            cwd: session.cwd.as_deref().map(|cwd| truncate_field(cwd, 512)),
            process_count: session.family.len(),
            cpu_ms,
            rss_bytes,
            read_bytes,
            write_bytes,
            file_targets: file_target_counts.len(),
            network_targets: network_target_counts.len(),
            process_samples: if include_detail_samples {
                bounded_process_samples(process_samples)
            } else {
                Vec::new()
            },
            file_samples: if include_detail_samples {
                bounded_target_samples(file_target_counts)
            } else {
                Vec::new()
            },
            network_samples: if include_detail_samples {
                bounded_target_samples(network_target_counts)
            } else {
                Vec::new()
            },
        });
    }
    io_state.previous = current_io;

    MonitorSample {
        window_start_ms,
        window_end_ms,
        sessions,
    }
}

fn should_store_detail_samples(window_start_ms: u64, window_end_ms: u64) -> bool {
    let interval_ms = DETAIL_SAMPLE_INTERVAL_SECS * 1000;
    window_start_ms / interval_ms != window_end_ms / interval_ms
}

fn collect_process_samples(
    family: &[u32],
    current: &ProcSnapshot,
    previous: Option<&ProcSnapshot>,
    io_state: &MonitorIoState,
    current_io: &mut BTreeMap<procfs::ProcessKey, (u64, u64)>,
) -> Vec<MonitorProcessSample> {
    let family_set = family.iter().copied().collect::<BTreeSet<_>>();
    let mut out = Vec::new();

    for proc_info in family.iter().filter_map(|pid| current.procs.get(pid)) {
        let cpu_ms = procfs::process_cpu_ms_delta(proc_info, previous);
        let rss_bytes = proc_info.rss_kb.saturating_mul(1024);
        let key = proc_info.process_key();
        let (read_bytes, write_bytes) = process_io_delta(proc_info.pid, key, io_state, current_io);
        out.push(MonitorProcessSample {
            rank_kind: "all",
            pid: proc_info.pid,
            pid_starttime_ticks: proc_info.starttime_ticks,
            ppid: proc_info.ppid,
            depth: process_depth(proc_info, current, &family_set),
            comm: truncate_field(&proc_info.comm, 128),
            command: truncate_field(&proc_info.command, 512),
            cwd: proc_info
                .cwd
                .as_ref()
                .map(|path| truncate_field(&path.to_string_lossy(), 512)),
            cpu_ms,
            cpu_percent: procfs::process_cpu_percent(proc_info, previous, current),
            rss_bytes,
            read_bytes,
            write_bytes,
        });
    }

    out
}

fn aggregate_process_samples(samples: &[MonitorProcessSample]) -> (u64, u64, u64, u64) {
    samples.iter().fold((0, 0, 0, 0), |acc, sample| {
        (
            acc.0.saturating_add(sample.cpu_ms),
            acc.1.saturating_add(sample.rss_bytes),
            acc.2.saturating_add(sample.read_bytes),
            acc.3.saturating_add(sample.write_bytes),
        )
    })
}

fn process_io_delta(
    pid: u32,
    key: procfs::ProcessKey,
    io_state: &MonitorIoState,
    current_io: &mut BTreeMap<procfs::ProcessKey, (u64, u64)>,
) -> (u64, u64) {
    let Some((current_read, current_write)) = procfs::read_process_io_bytes(pid) else {
        return (0, 0);
    };
    current_io.insert(key, (current_read, current_write));
    io_state
        .previous
        .get(&key)
        .map(|(previous_read, previous_write)| {
            (
                current_read.saturating_sub(*previous_read),
                current_write.saturating_sub(*previous_write),
            )
        })
        .unwrap_or((0, 0))
}

fn process_depth(
    proc_info: &procfs::ProcInfo,
    current: &ProcSnapshot,
    family_set: &BTreeSet<u32>,
) -> usize {
    let mut depth = 0;
    let mut parent_pid = proc_info.ppid;
    let mut seen = BTreeSet::new();
    while family_set.contains(&parent_pid) && seen.insert(parent_pid) {
        depth += 1;
        let Some(parent) = current.procs.get(&parent_pid) else {
            break;
        };
        parent_pid = parent.ppid;
    }
    depth
}

fn collect_fd_target_counts(
    family: &[u32],
    current: &ProcSnapshot,
) -> (BTreeMap<String, usize>, BTreeMap<u32, BTreeSet<u64>>) {
    let mut files = BTreeMap::new();
    let mut sockets_by_pid = BTreeMap::new();

    for pid in family {
        let Some(proc_info) = current.procs.get(pid) else {
            continue;
        };
        if procfs::process_starttime_ticks(*pid) != Some(proc_info.starttime_ticks) {
            continue;
        }
        let mut pid_files = BTreeSet::new();
        let mut pid_sockets = BTreeSet::new();
        for target in procfs::scan_proc_fd_paths(*pid) {
            let raw = target.to_string_lossy();
            if is_file_target(&raw) {
                pid_files.insert(truncate_field(&raw, 768));
            } else if let Some(inode) = socket_inode(&raw) {
                pid_sockets.insert(inode);
            }
        }
        if procfs::process_starttime_ticks(*pid) != Some(proc_info.starttime_ticks) {
            continue;
        }
        for target in pid_files {
            *files.entry(target).or_insert(0) += 1;
        }
        if !pid_sockets.is_empty() {
            sockets_by_pid.insert(*pid, pid_sockets);
        }
    }

    (files, sockets_by_pid)
}

fn is_file_target(target: &str) -> bool {
    target.starts_with('/') && !target.starts_with("/dev/null") && !target.starts_with("/dev/zero")
}

fn socket_inode(target: &str) -> Option<u64> {
    target
        .strip_prefix("socket:[")?
        .strip_suffix(']')?
        .parse()
        .ok()
}

fn collect_network_target_counts(
    sockets_by_pid: &BTreeMap<u32, BTreeSet<u64>>,
) -> BTreeMap<String, usize> {
    let mut targets = BTreeMap::new();
    for (pid, socket_inodes) in sockets_by_pid {
        for table in ["tcp", "tcp6"] {
            let Ok(text) = std::fs::read_to_string(format!("/proc/{pid}/net/{table}")) else {
                continue;
            };
            let is_ipv6 = table == "tcp6";
            for line in text.lines().skip(1) {
                let Some((inode, endpoint)) = parse_tcp_endpoint_line(line, is_ipv6) else {
                    continue;
                };
                if socket_inodes.contains(&inode) {
                    *targets.entry(endpoint).or_insert(0) += 1;
                }
            }
        }
    }
    targets
}

fn parse_tcp_endpoint_line(line: &str, is_ipv6: bool) -> Option<(u64, String)> {
    let fields = line.split_whitespace().collect::<Vec<_>>();
    let local = *fields.get(1)?;
    let remote = *fields.get(2)?;
    let inode = fields.get(9)?.parse().ok()?;
    let endpoint = parse_tcp_endpoint(remote, is_ipv6)
        .filter(|(_, port)| *port != 0)
        .or_else(|| parse_tcp_endpoint(local, is_ipv6).filter(|(_, port)| *port != 0))?;
    Some((inode, format!("{}:{}", endpoint.0, endpoint.1)))
}

fn parse_tcp_endpoint(value: &str, is_ipv6: bool) -> Option<(String, u16)> {
    let (addr_hex, port_hex) = value.split_once(':')?;
    let port = u16::from_str_radix(port_hex, 16).ok()?;
    if is_ipv6 {
        Some((parse_tcp6_addr(addr_hex)?, port))
    } else {
        Some((parse_tcp4_addr(addr_hex)?, port))
    }
}

fn parse_tcp4_addr(value: &str) -> Option<String> {
    let raw = u32::from_str_radix(value, 16).ok()?;
    Some(Ipv4Addr::from(raw.to_le_bytes()).to_string())
}

fn parse_tcp6_addr(value: &str) -> Option<String> {
    if value.len() != 32 {
        return None;
    }
    let mut bytes = [0u8; 16];
    for (index, chunk) in value.as_bytes().chunks(8).enumerate() {
        let chunk = std::str::from_utf8(chunk).ok()?;
        let raw = u32::from_str_radix(chunk, 16).ok()?;
        bytes[index * 4..index * 4 + 4].copy_from_slice(&raw.to_le_bytes());
    }
    Some(Ipv6Addr::from(bytes).to_string())
}

fn bounded_process_samples(samples: Vec<MonitorProcessSample>) -> Vec<MonitorProcessSample> {
    if samples.len() <= DETAIL_EDGE_LIMIT * 2 {
        return samples;
    }
    let mut selected = BTreeSet::new();
    let mut out = Vec::new();

    let mut top = samples.iter().enumerate().collect::<Vec<_>>();
    top.sort_by(|(left_index, left), (right_index, right)| {
        process_sample_score(right)
            .cmp(&process_sample_score(left))
            .then_with(|| left.pid.cmp(&right.pid))
            .then_with(|| left_index.cmp(right_index))
    });
    for (index, sample) in top.into_iter().take(DETAIL_EDGE_LIMIT) {
        selected.insert(index);
        let mut sample = sample.clone();
        sample.rank_kind = "top";
        out.push(sample);
    }

    let mut bottom = samples.iter().enumerate().collect::<Vec<_>>();
    bottom.sort_by(|(left_index, left), (right_index, right)| {
        process_sample_score(left)
            .cmp(&process_sample_score(right))
            .then_with(|| left.pid.cmp(&right.pid))
            .then_with(|| left_index.cmp(right_index))
    });
    for (index, sample) in bottom {
        if out.len() >= DETAIL_EDGE_LIMIT * 2 {
            break;
        }
        if selected.insert(index) {
            let mut sample = sample.clone();
            sample.rank_kind = "bottom";
            out.push(sample);
        }
    }
    out
}

fn process_sample_score(sample: &MonitorProcessSample) -> (u64, u64, u64) {
    (
        sample.cpu_ms,
        sample.rss_bytes,
        sample.read_bytes.saturating_add(sample.write_bytes),
    )
}

fn bounded_target_samples(counts: BTreeMap<String, usize>) -> Vec<MonitorTargetSample> {
    let rows = counts.into_iter().collect::<Vec<_>>();
    if rows.len() <= DETAIL_EDGE_LIMIT * 2 {
        return rows
            .into_iter()
            .map(|(target, count)| MonitorTargetSample {
                rank_kind: "all",
                target,
                count,
            })
            .collect();
    }

    let mut selected = BTreeSet::new();
    let mut out = Vec::new();
    let mut top = rows.iter().enumerate().collect::<Vec<_>>();
    top.sort_by(
        |(left_index, (left_target, left_count)), (right_index, (right_target, right_count))| {
            right_count
                .cmp(left_count)
                .then_with(|| left_target.cmp(right_target))
                .then_with(|| left_index.cmp(right_index))
        },
    );
    for (index, (target, count)) in top.into_iter().take(DETAIL_EDGE_LIMIT) {
        selected.insert(index);
        out.push(MonitorTargetSample {
            rank_kind: "top",
            target: target.clone(),
            count: *count,
        });
    }

    let mut bottom = rows.iter().enumerate().collect::<Vec<_>>();
    bottom.sort_by(
        |(left_index, (left_target, left_count)), (right_index, (right_target, right_count))| {
            left_count
                .cmp(right_count)
                .then_with(|| left_target.cmp(right_target))
                .then_with(|| left_index.cmp(right_index))
        },
    );
    for (index, (target, count)) in bottom {
        if out.len() >= DETAIL_EDGE_LIMIT * 2 {
            break;
        }
        if selected.insert(index) {
            out.push(MonitorTargetSample {
                rank_kind: "bottom",
                target: target.clone(),
                count: *count,
            });
        }
    }
    out
}

fn truncate_field(value: &str, max: usize) -> String {
    if value.len() <= max {
        return value.to_string();
    }
    let mut end = max.saturating_sub(3);
    while !value.is_char_boundary(end) {
        end = end.saturating_sub(1);
    }
    format!("{}...", &value[..end])
}

fn active_monitor() -> Option<MonitorPidFile> {
    let path = monitor_pid_path();
    let text = std::fs::read_to_string(&path).ok()?;
    let pid_file: MonitorPidFile = serde_json::from_str(&text).ok()?;
    if pid_is_alive(pid_file.pid) && pid_file.db_path.exists() {
        Some(pid_file)
    } else {
        let _ = std::fs::remove_file(path);
        None
    }
}

fn write_monitor_pid_file(pid_file: &MonitorPidFile) -> io::Result<()> {
    let path = monitor_pid_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let json = serde_json::to_vec(pid_file).map_err(io::Error::other)?;
    std::fs::write(path, json)
}

fn pid_is_alive(pid: u32) -> bool {
    if pid == 0 {
        return false;
    }
    let result = unsafe { libc::kill(pid as libc::pid_t, 0) };
    result == 0 || io::Error::last_os_error().raw_os_error() == Some(libc::EPERM)
}

struct MonitorPidGuard {
    path: PathBuf,
    pid: u32,
}

impl Drop for MonitorPidGuard {
    fn drop(&mut self) {
        let Ok(text) = std::fs::read_to_string(&self.path) else {
            return;
        };
        let Ok(pid_file) = serde_json::from_str::<MonitorPidFile>(&text) else {
            return;
        };
        if pid_file.pid == self.pid {
            let _ = std::fs::remove_file(&self.path);
        }
    }
}

fn now_epoch_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_millis() as u64)
        .unwrap_or_default()
}

fn bytes_to_mb(bytes: u64) -> u64 {
    if bytes == 0 {
        0
    } else {
        bytes.div_ceil(1_048_576)
    }
}

fn short_monitor_session_id(session_id: &str) -> String {
    session_id
        .rsplit(':')
        .next()
        .filter(|value| !value.is_empty())
        .unwrap_or(session_id)
        .to_string()
}

fn systemd_user_dir() -> io::Result<PathBuf> {
    if let Some(config_home) = std::env::var_os("XDG_CONFIG_HOME")
        && !config_home.is_empty()
    {
        return Ok(PathBuf::from(config_home).join("systemd").join("user"));
    }
    let home = dirs::home_dir()
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "home directory not found"))?;
    Ok(home.join(".config").join("systemd").join("user"))
}

fn monitor_service_unit(exe: &Path) -> io::Result<String> {
    let exe = exe.to_str().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            "agentsight binary path is not valid UTF-8",
        )
    })?;
    Ok(monitor_service_unit_for_exe(exe))
}

fn monitor_service_unit_for_exe(exe: &str) -> String {
    format!(
        "\
[Unit]
Description=AgentSight background monitor
Documentation=https://github.com/eunomia-bpf/agentsight
After=default.target

[Service]
Type=simple
ExecStart={} monitor
Restart=on-failure
RestartSec=5
KillSignal=SIGTERM

[Install]
WantedBy=default.target
",
        systemd_quote(exe)
    )
}

fn systemd_quote(value: &str) -> String {
    let escaped = value
        .replace('%', "%%")
        .replace('\\', "\\\\")
        .replace('"', "\\\"");
    format!("\"{escaped}\"")
}

fn run_systemctl_user<const N: usize>(args: [&str; N]) -> io::Result<()> {
    let output = Command::new("systemctl")
        .arg("--user")
        .args(args)
        .output()?;
    if output.status.success() {
        return Ok(());
    }

    let stderr = String::from_utf8_lossy(&output.stderr);
    let stdout = String::from_utf8_lossy(&output.stdout);
    Err(io::Error::other(format!(
        "systemctl --user failed with status {}: {}{}",
        output.status, stdout, stderr
    )))
}

struct MonitorStore {
    path: PathBuf,
    conn: Connection,
}

impl MonitorStore {
    fn open_default() -> rusqlite::Result<Self> {
        Self::open_path(default_monitor_db_path())
    }

    fn open_path(path: PathBuf) -> rusqlite::Result<Self> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|err| rusqlite::Error::ToSqlConversionFailure(Box::new(err)))?;
        }
        let conn = Connection::open(&path)?;
        conn.pragma_update(None, "journal_mode", "WAL").ok();
        conn.pragma_update(None, "foreign_keys", "ON")?;
        conn.execute_batch(MONITOR_SCHEMA)?;
        ensure_monitor_schema(&conn)?;
        Ok(Self { path, conn })
    }

    fn path(&self) -> &Path {
        &self.path
    }

    fn insert_sample(&mut self, sample: &MonitorSample) -> rusqlite::Result<MonitorWriteStats> {
        let tx = self.conn.transaction()?;
        let mut stats = MonitorWriteStats::default();

        for session in &sample.sessions {
            tx.execute(
                "INSERT INTO tracked_sessions (
                    session_id, display_id, agent_type, root_pid, root_starttime_ticks,
                    first_seen_ms, last_seen_ms, match_evidence, match_confidence,
                    session_path, command, cwd, status
                 ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, 'running')
                 ON CONFLICT(session_id, root_pid, root_starttime_ticks) DO UPDATE SET
                    display_id = excluded.display_id,
                    agent_type = excluded.agent_type,
                    last_seen_ms = excluded.last_seen_ms,
                    match_evidence = excluded.match_evidence,
                    match_confidence = excluded.match_confidence,
                    session_path = COALESCE(excluded.session_path, session_path),
                    command = excluded.command,
                    cwd = COALESCE(excluded.cwd, cwd),
                    status = 'running'",
                params![
                    session.session_id,
                    session.display_id,
                    session.agent_type,
                    session.root_pid as i64,
                    session.root_starttime_ticks as i64,
                    sample.window_start_ms as i64,
                    sample.window_end_ms as i64,
                    session.match_evidence,
                    session.match_confidence,
                    session.session_path.as_deref(),
                    session.command,
                    session.cwd.as_deref(),
                ],
            )?;

            tx.execute(
                "INSERT INTO monitor_windows (
                    session_id, root_pid, root_starttime_ticks, window_start_ms, window_end_ms,
                    process_count, cpu_ms, rss_bytes, read_bytes, write_bytes,
                    file_targets, network_targets
                 ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
                params![
                    session.session_id,
                    session.root_pid as i64,
                    session.root_starttime_ticks as i64,
                    sample.window_start_ms as i64,
                    sample.window_end_ms as i64,
                    session.process_count as i64,
                    session.cpu_ms as i64,
                    session.rss_bytes as i64,
                    session.read_bytes as i64,
                    session.write_bytes as i64,
                    session.file_targets as i64,
                    session.network_targets as i64,
                ],
            )?;
            let window_id = tx.last_insert_rowid();
            insert_detail_samples(&tx, window_id, session)?;

            stats.sessions += 1;
            stats.windows += usize::from(window_id > 0);
        }

        tx.commit()?;
        Ok(stats)
    }

    fn checkpoint(&self) -> rusqlite::Result<()> {
        self.conn
            .execute_batch("PRAGMA wal_checkpoint(TRUNCATE);")
            .map(|_| ())
    }
}

fn insert_detail_samples(
    tx: &rusqlite::Transaction<'_>,
    window_id: i64,
    session: &MonitorSessionSample,
) -> rusqlite::Result<()> {
    for (rank, sample) in session.process_samples.iter().enumerate() {
        tx.execute(
            "INSERT INTO process_samples (
                window_id, rank, rank_kind, pid, pid_starttime_ticks, ppid, depth,
                comm, command, cwd, cpu_ms, cpu_percent, rss_bytes, read_bytes,
                write_bytes, live_count
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, 1)",
            params![
                window_id,
                rank as i64,
                sample.rank_kind,
                sample.pid as i64,
                sample.pid_starttime_ticks as i64,
                sample.ppid as i64,
                sample.depth as i64,
                sample.comm,
                sample.command,
                sample.cwd.as_deref(),
                sample.cpu_ms as i64,
                sample.cpu_percent,
                sample.rss_bytes as i64,
                sample.read_bytes as i64,
                sample.write_bytes as i64,
            ],
        )?;
    }

    insert_target_samples(tx, "file_samples", window_id, &session.file_samples)?;
    insert_target_samples(tx, "network_samples", window_id, &session.network_samples)?;
    Ok(())
}

fn insert_target_samples(
    tx: &rusqlite::Transaction<'_>,
    table: &str,
    window_id: i64,
    samples: &[MonitorTargetSample],
) -> rusqlite::Result<()> {
    let sql = format!(
        "INSERT INTO {table} (window_id, rank, rank_kind, target, count)
         VALUES (?1, ?2, ?3, ?4, ?5)"
    );
    for (rank, sample) in samples.iter().enumerate() {
        tx.execute(
            &sql,
            params![
                window_id,
                rank as i64,
                sample.rank_kind,
                sample.target,
                sample.count as i64,
            ],
        )?;
    }
    Ok(())
}

fn ensure_monitor_schema(conn: &Connection) -> rusqlite::Result<()> {
    if !monitor_windows_has_network_targets_column(conn)? {
        conn.execute_batch(
            "ALTER TABLE monitor_windows
             ADD COLUMN network_targets INTEGER NOT NULL DEFAULT 0;",
        )?;
    }
    Ok(())
}

fn monitor_windows_has_network_targets_column(conn: &Connection) -> rusqlite::Result<bool> {
    let mut stmt = conn.prepare("PRAGMA table_info(monitor_windows)")?;
    let rows = stmt.query_map([], |row| row.get::<_, String>(1))?;
    for row in rows {
        if row? == "network_targets" {
            return Ok(true);
        }
    }
    Ok(false)
}

fn default_monitor_db_path() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    monitor_db_path_for_home(&home, Local::now().date_naive())
}

fn monitor_pid_path() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    monitor_dir_for_home(&home).join("monitor.pid")
}

fn monitor_dir_for_home(home: &Path) -> PathBuf {
    home.join(".agentsight").join("monitor")
}

fn monitor_db_path_for_home(home: &Path, date: NaiveDate) -> PathBuf {
    let week = date.iso_week();
    monitor_dir_for_home(home).join(format!("monitor-{:04}-W{:02}.db", week.year(), week.week()))
}

const MONITOR_SCHEMA: &str = r#"
CREATE TABLE IF NOT EXISTS tracked_sessions (
    session_id TEXT NOT NULL,
    display_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    root_pid INTEGER NOT NULL,
    root_starttime_ticks INTEGER NOT NULL,
    first_seen_ms INTEGER NOT NULL,
    last_seen_ms INTEGER NOT NULL,
    match_evidence TEXT NOT NULL,
    match_confidence REAL NOT NULL,
    session_path TEXT,
    command TEXT NOT NULL,
    cwd TEXT,
    status TEXT NOT NULL,
    PRIMARY KEY (session_id, root_pid, root_starttime_ticks)
);

CREATE TABLE IF NOT EXISTS monitor_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    root_pid INTEGER NOT NULL,
    root_starttime_ticks INTEGER NOT NULL,
    window_start_ms INTEGER NOT NULL,
    window_end_ms INTEGER NOT NULL,
    process_count INTEGER NOT NULL,
    cpu_ms INTEGER NOT NULL,
    rss_bytes INTEGER NOT NULL,
    read_bytes INTEGER NOT NULL,
    write_bytes INTEGER NOT NULL,
    file_targets INTEGER NOT NULL,
    network_targets INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_monitor_windows_session_time
    ON monitor_windows(session_id, window_start_ms);

CREATE TABLE IF NOT EXISTS process_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_id INTEGER NOT NULL REFERENCES monitor_windows(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    rank_kind TEXT NOT NULL,
    pid INTEGER,
    pid_starttime_ticks INTEGER,
    ppid INTEGER,
    depth INTEGER NOT NULL,
    comm TEXT NOT NULL,
    command TEXT NOT NULL,
    cwd TEXT,
    cpu_ms INTEGER NOT NULL,
    cpu_percent REAL NOT NULL,
    rss_bytes INTEGER NOT NULL,
    read_bytes INTEGER NOT NULL,
    write_bytes INTEGER NOT NULL,
    live_count INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_process_samples_window
    ON process_samples(window_id);

CREATE TABLE IF NOT EXISTS file_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_id INTEGER NOT NULL REFERENCES monitor_windows(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    rank_kind TEXT NOT NULL,
    target TEXT NOT NULL,
    count INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_file_samples_window
    ON file_samples(window_id);

CREATE TABLE IF NOT EXISTS network_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_id INTEGER NOT NULL REFERENCES monitor_windows(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    rank_kind TEXT NOT NULL,
    target TEXT NOT NULL,
    count INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_network_samples_window
    ON network_samples(window_id);
"#;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn monitor_db_path_uses_home_agentsight_monitor_weekly_db() {
        let path = monitor_db_path_for_home(
            Path::new("/home/user"),
            NaiveDate::from_ymd_opt(2026, 6, 16).unwrap(),
        );
        assert_eq!(
            path,
            PathBuf::from("/home/user/.agentsight/monitor/monitor-2026-W25.db")
        );
    }

    #[test]
    fn monitor_service_unit_runs_monitor_subcommand() {
        let unit = monitor_service_unit(Path::new("/home/user/bin/agentsight")).unwrap();
        assert!(unit.contains("ExecStart=\"/home/user/bin/agentsight\" monitor"));
        assert!(unit.contains("Restart=on-failure"));
        assert!(unit.contains("WantedBy=default.target"));
    }

    #[test]
    fn systemd_quote_escapes_special_chars() {
        assert_eq!(
            systemd_quote("/tmp/a \"quoted\" path/%agentsight"),
            "\"/tmp/a \\\"quoted\\\" path/%%agentsight\""
        );
    }

    #[cfg(unix)]
    #[test]
    fn monitor_service_unit_rejects_non_utf8_path() {
        use std::ffi::OsStr;
        use std::os::unix::ffi::OsStrExt;

        let path = Path::new(OsStr::from_bytes(b"/tmp/agentsight-\xff"));
        let err = monitor_service_unit(path).unwrap_err();
        assert_eq!(err.kind(), io::ErrorKind::InvalidInput);
    }

    #[test]
    fn monitor_store_persists_session_window() {
        let temp = tempfile::tempdir().unwrap();
        let mut store = MonitorStore::open_path(temp.path().join("monitor.db")).unwrap();
        let sample = MonitorSample {
            window_start_ms: 29_000,
            window_end_ms: 31_000,
            sessions: vec![MonitorSessionSample {
                session_id: "local:codex:test".to_string(),
                display_id: "codex:test".to_string(),
                agent_type: "codex".to_string(),
                root_pid: 42,
                root_starttime_ticks: 100,
                match_evidence: "proc_fd".to_string(),
                match_confidence: 0.9,
                session_path: Some("/tmp/session.jsonl".to_string()),
                command: "codex".to_string(),
                cwd: Some("/tmp".to_string()),
                process_count: 1,
                cpu_ms: 7,
                rss_bytes: 4096,
                read_bytes: 11,
                write_bytes: 13,
                file_targets: 2,
                network_targets: 1,
                process_samples: vec![MonitorProcessSample {
                    rank_kind: "all",
                    pid: 42,
                    pid_starttime_ticks: 100,
                    ppid: 1,
                    depth: 0,
                    comm: "codex".to_string(),
                    command: "codex exec".to_string(),
                    cwd: Some("/tmp".to_string()),
                    cpu_ms: 7,
                    cpu_percent: 3.5,
                    rss_bytes: 4096,
                    read_bytes: 11,
                    write_bytes: 13,
                }],
                file_samples: vec![MonitorTargetSample {
                    rank_kind: "all",
                    target: "/tmp/session.jsonl".to_string(),
                    count: 1,
                }],
                network_samples: vec![MonitorTargetSample {
                    rank_kind: "all",
                    target: "203.0.113.10:443".to_string(),
                    count: 1,
                }],
            }],
        };

        let stats = store.insert_sample(&sample).unwrap();
        let windows: i64 = store
            .conn
            .query_row("SELECT COUNT(*) FROM monitor_windows", [], |row| row.get(0))
            .unwrap();
        let file_targets: i64 = store
            .conn
            .query_row(
                "SELECT file_targets + network_targets FROM monitor_windows",
                [],
                |row| row.get(0),
            )
            .unwrap();
        let process_samples: i64 = store
            .conn
            .query_row("SELECT COUNT(*) FROM process_samples", [], |row| row.get(0))
            .unwrap();
        let file_samples: i64 = store
            .conn
            .query_row("SELECT COUNT(*) FROM file_samples", [], |row| row.get(0))
            .unwrap();
        let network_samples: i64 = store
            .conn
            .query_row("SELECT COUNT(*) FROM network_samples", [], |row| row.get(0))
            .unwrap();
        let top = build_monitor_top(
            store.path(),
            10,
            &TopOptions {
                pid: None,
                comm: None,
                sort: "cpu".to_string(),
                view: "all".to_string(),
            },
        )
        .unwrap();

        assert_eq!(stats.sessions, 1);
        assert_eq!(stats.windows, 1);
        assert_eq!((windows, file_targets), (1, 3));
        assert_eq!((process_samples, file_samples, network_samples), (1, 1, 1));
        assert_eq!(top.rows.len(), 1);
        assert_eq!(top.rows[0].files, 2);
        assert_eq!(top.rows[0].network, 1);
    }

    #[test]
    fn detail_sampling_only_crosses_interval_boundary() {
        assert!(!should_store_detail_samples(10_000, 12_000));
        assert!(should_store_detail_samples(29_000, 31_000));
    }

    #[test]
    fn tcp_endpoint_parser_decodes_proc_net_tcp_ipv4() {
        let line = "0: 0100007F:9C4C 0A7100CB:01BB 01 00000000:00000000 00:00000000 00000000 1000 0 12345 1";
        assert_eq!(
            parse_tcp_endpoint_line(line, false),
            Some((12345, "203.0.113.10:443".to_string()))
        );
        assert_eq!(socket_inode("socket:[12345]"), Some(12345));
    }

    #[test]
    fn bounded_samples_keep_top_and_bottom_edges() {
        let targets = (0..12)
            .map(|index| (format!("/tmp/file-{index}"), index + 1))
            .collect::<BTreeMap<_, _>>();
        let samples = bounded_target_samples(targets);
        assert_eq!(samples.len(), 10);
        assert_eq!(samples[0].rank_kind, "top");
        assert_eq!(samples[0].count, 12);
        assert!(samples.iter().any(|sample| sample.rank_kind == "bottom"));

        let processes = (0..12)
            .map(|index| MonitorProcessSample {
                rank_kind: "all",
                pid: index,
                pid_starttime_ticks: 100 + index as u64,
                ppid: 0,
                depth: 0,
                comm: "test".to_string(),
                command: "test".to_string(),
                cwd: None,
                cpu_ms: index as u64,
                cpu_percent: index as f64,
                rss_bytes: 0,
                read_bytes: 0,
                write_bytes: 0,
            })
            .collect::<Vec<_>>();
        let samples = bounded_process_samples(processes);
        assert_eq!(samples.len(), 10);
        assert_eq!(samples[0].rank_kind, "top");
        assert_eq!(samples[0].pid, 11);
        assert!(samples.iter().any(|sample| sample.rank_kind == "bottom"));
    }

    #[test]
    fn current_pid_is_alive_for_monitor_pid_file() {
        assert!(pid_is_alive(std::process::id()));
        assert!(!pid_is_alive(0));
    }
}
