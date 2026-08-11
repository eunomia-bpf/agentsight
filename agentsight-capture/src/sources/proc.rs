// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::io;
use std::path::PathBuf;
use std::sync::OnceLock;
use std::time::Instant;
use sysinfo::{Pid, Process, ProcessRefreshKind, ProcessesToUpdate, System, UpdateKind};

#[cfg(target_os = "linux")]
use std::fs;

pub use agent_session::{ProcessKey, ProcessTree};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PidSeed {
    pub pid: u32,
    pub ppid: u32,
}

impl PidSeed {
    pub fn arg_value(self) -> String {
        format!("{}:{}", self.pid, self.ppid)
    }
}

#[derive(Debug, Clone, Default)]
pub struct ProcInfo {
    pub pid: u32,
    pub ppid: u32,
    pub session_id: u32,
    pub comm: String,
    pub command: String,
    pub cwd: Option<PathBuf>,
    pub ticks: u64,
    pub starttime_ticks: u64,
    pub rss_kb: u64,
    pub rss_mb: u64,
    pub vsz_kb: u64,
    pub threads: u32,
    pub read_bytes: u64,
    pub write_bytes: u64,
}

impl ProcInfo {
    pub fn seed(&self) -> PidSeed {
        PidSeed {
            pid: self.pid,
            ppid: self.ppid,
        }
    }

    pub fn process_key(&self) -> ProcessKey {
        ProcessKey {
            pid: self.pid,
            starttime_ticks: self.starttime_ticks,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProcSnapshot {
    pub at: Instant,
    pub uptime_s: f64,
    pub procs: BTreeMap<u32, ProcInfo>,
}

impl Default for ProcSnapshot {
    fn default() -> Self {
        Self {
            at: Instant::now(),
            uptime_s: 0.0,
            procs: BTreeMap::new(),
        }
    }
}

impl ProcSnapshot {
    pub fn collect() -> io::Result<Self> {
        let mut system = System::new();
        system.refresh_processes_specifics(ProcessesToUpdate::All, true, process_refresh_kind());
        let boot_time_s = System::boot_time();
        let procs = system
            .processes()
            .values()
            .filter(|process| process.thread_kind() != Some(sysinfo::ThreadKind::Userland))
            .map(|process| proc_info_from_sysinfo(process, boot_time_s))
            .map(|info| (info.pid, info))
            .collect();

        Ok(Self {
            at: Instant::now(),
            uptime_s: System::uptime() as f64,
            procs,
        })
    }

    pub fn children_by_ppid(&self) -> HashMap<u32, Vec<u32>> {
        children_by_ppid(&self.procs)
    }

    pub fn process_family(&self, root: u32) -> Vec<u32> {
        process_family(root, &self.children_by_ppid(), &self.procs)
    }

    pub fn seeds_for_all(&self) -> Vec<PidSeed> {
        self.procs.values().map(ProcInfo::seed).collect()
    }

    pub fn seeds_for_pid_family(&self, root: u32) -> Vec<PidSeed> {
        self.process_family(root)
            .into_iter()
            .filter_map(|pid| self.procs.get(&pid).map(ProcInfo::seed))
            .collect()
    }

    pub fn seeds_for_session(&self, session_id: u32) -> Vec<PidSeed> {
        self.procs
            .values()
            .filter(|proc_info| proc_info.session_id == session_id)
            .map(ProcInfo::seed)
            .collect()
    }

    pub fn pids_in_session(&self, session_id: u32) -> Vec<u32> {
        self.procs
            .values()
            .filter(|proc_info| proc_info.session_id == session_id)
            .map(|proc_info| proc_info.pid)
            .collect()
    }
}

pub fn collect_fd_paths(process_trees: &[ProcessTree]) -> HashMap<ProcessKey, BTreeSet<PathBuf>> {
    let mut out = HashMap::new();

    for tree in process_trees {
        for key in &tree.members {
            if !process_key_is_current(*key) {
                continue;
            }
            let paths = scan_proc_fd_paths(key.pid);
            if !process_key_is_current(*key) {
                continue;
            }
            if !paths.is_empty() {
                out.insert(*key, paths);
            }
        }
    }

    out
}

fn process_key_is_current(key: ProcessKey) -> bool {
    process_key_is_current_impl(key)
}

#[cfg(target_os = "linux")]
fn process_key_is_current_impl(key: ProcessKey) -> bool {
    process_starttime_ticks(key.pid) == Some(key.starttime_ticks)
}

#[cfg(not(target_os = "linux"))]
fn process_key_is_current_impl(_key: ProcessKey) -> bool {
    true
}

pub fn children_by_ppid(procs: &BTreeMap<u32, ProcInfo>) -> HashMap<u32, Vec<u32>> {
    let mut children: HashMap<u32, Vec<u32>> = HashMap::new();
    for proc_info in procs.values() {
        children
            .entry(proc_info.ppid)
            .or_default()
            .push(proc_info.pid);
    }
    children
}

pub fn process_family(
    root: u32,
    children: &HashMap<u32, Vec<u32>>,
    procs: &BTreeMap<u32, ProcInfo>,
) -> Vec<u32> {
    process_family_excluding(root, children, procs, &HashSet::new())
}

pub fn process_family_excluding(
    root: u32,
    children: &HashMap<u32, Vec<u32>>,
    procs: &BTreeMap<u32, ProcInfo>,
    excluded_roots: &HashSet<u32>,
) -> Vec<u32> {
    let mut out = Vec::new();
    let mut stack = vec![root];
    let mut seen = HashSet::new();
    while let Some(pid) = stack.pop() {
        if !seen.insert(pid) || !procs.contains_key(&pid) {
            continue;
        }
        out.push(pid);
        if let Some(child_pids) = children.get(&pid) {
            stack.extend(
                child_pids
                    .iter()
                    .copied()
                    .filter(|child_pid| !excluded_roots.contains(child_pid)),
            );
        }
    }
    out
}

pub fn process_cpu_percent(
    proc_info: &ProcInfo,
    previous: Option<&ProcSnapshot>,
    sample: &ProcSnapshot,
) -> f64 {
    let ticks_per_second = ticks_per_second();
    if let Some(previous) = previous
        && let Some(prev_proc) = previous.procs.get(&proc_info.pid)
    {
        let delta_ticks = proc_info.ticks.saturating_sub(prev_proc.ticks);
        let delta_wall = sample.at.duration_since(previous.at).as_secs_f64();
        if delta_wall > 0.0 {
            return (delta_ticks as f64 / ticks_per_second) / delta_wall * 100.0;
        }
    }

    let process_start_s = proc_info.starttime_ticks as f64 / ticks_per_second;
    let elapsed_s = (sample.uptime_s - process_start_s).max(0.001);
    (proc_info.ticks as f64 / ticks_per_second) / elapsed_s * 100.0
}

pub fn process_age_s(proc_info: &ProcInfo, sample: &ProcSnapshot) -> f64 {
    let process_start_s = proc_info.starttime_ticks as f64 / ticks_per_second();
    (sample.uptime_s - process_start_s).max(0.0)
}

fn proc_info_from_sysinfo(process: &Process, boot_time_s: u64) -> ProcInfo {
    let pid = process.pid().as_u32();
    let comm = process.name().to_string_lossy().into_owned();
    let command = process_command(process, &comm);
    let rss_bytes = process.memory();
    let disk = process.disk_usage();
    ProcInfo {
        pid,
        ppid: process.parent().map(pid_to_u32).unwrap_or_default(),
        session_id: process.session_id().map(pid_to_u32).unwrap_or_default(),
        comm,
        command,
        cwd: process.cwd().map(PathBuf::from),
        ticks: cpu_ms_to_ticks(process.accumulated_cpu_time()),
        starttime_ticks: platform_starttime_ticks(pid)
            .unwrap_or_else(|| starttime_ticks_from_epoch(process.start_time(), boot_time_s)),
        rss_kb: bytes_to_kb(rss_bytes),
        rss_mb: bytes_to_mb(rss_bytes),
        vsz_kb: bytes_to_kb(process.virtual_memory()),
        threads: process
            .tasks()
            .map(|tasks| (tasks.len() as u32).saturating_add(1))
            .unwrap_or(1),
        read_bytes: disk.total_read_bytes,
        write_bytes: disk.total_written_bytes,
    }
}

fn process_refresh_kind() -> ProcessRefreshKind {
    ProcessRefreshKind::nothing()
        .with_memory()
        .with_cpu()
        .with_disk_usage()
        .with_cmd(UpdateKind::Always)
        .with_cwd(UpdateKind::Always)
        .with_tasks()
}

fn process_command(process: &Process, fallback: &str) -> String {
    let command = process
        .cmd()
        .iter()
        .map(|arg| arg.to_string_lossy())
        .collect::<Vec<_>>()
        .join(" ");
    if command.is_empty() {
        fallback.to_string()
    } else {
        command
    }
}

pub fn process_starttime_ticks(pid: u32) -> Option<u64> {
    platform_starttime_ticks(pid).or_else(|| {
        let sys_pid = Pid::from_u32(pid);
        let mut system = System::new();
        system.refresh_processes_specifics(
            ProcessesToUpdate::Some(&[sys_pid]),
            true,
            ProcessRefreshKind::nothing(),
        );
        system
            .process(sys_pid)
            .map(|process| starttime_ticks_from_epoch(process.start_time(), System::boot_time()))
    })
}

pub fn scan_proc_fd_paths(pid: u32) -> BTreeSet<PathBuf> {
    let mut out = BTreeSet::new();
    scan_proc_fd_paths_into(pid, &mut out);
    out
}

#[cfg(target_os = "linux")]
fn scan_proc_fd_paths_into(pid: u32, out: &mut BTreeSet<PathBuf>) {
    let Ok(entries) = fs::read_dir(format!("/proc/{pid}/fd")) else {
        return;
    };
    for entry in entries.flatten() {
        let Ok(target) = fs::read_link(entry.path()) else {
            continue;
        };
        out.insert(target);
    }
}

#[cfg(target_os = "macos")]
fn scan_proc_fd_paths_into(pid: u32, out: &mut BTreeSet<PathBuf>) {
    let Ok(output) = std::process::Command::new(lsof_path())
        .args(["-nP", "-Fn", "-p", &pid.to_string()])
        .output()
    else {
        return;
    };
    if !output.status.success() {
        return;
    }
    parse_lsof_file_names(&String::from_utf8_lossy(&output.stdout), out);
}

#[cfg(target_os = "macos")]
fn lsof_path() -> &'static str {
    if std::path::Path::new("/usr/sbin/lsof").is_file() {
        "/usr/sbin/lsof"
    } else {
        "lsof"
    }
}

#[cfg(not(any(target_os = "linux", target_os = "macos")))]
fn scan_proc_fd_paths_into(_pid: u32, _out: &mut BTreeSet<PathBuf>) {}

#[cfg(any(test, target_os = "macos"))]
fn parse_lsof_file_names(output: &str, out: &mut BTreeSet<PathBuf>) {
    for line in output.lines() {
        let Some(path) = line.strip_prefix('n') else {
            continue;
        };
        let path = path.trim().trim_end_matches(" (deleted)");
        if path.starts_with('/') {
            out.insert(PathBuf::from(path));
        }
    }
}

#[cfg(target_os = "linux")]
fn platform_starttime_ticks(pid: u32) -> Option<u64> {
    let stat = fs::read_to_string(format!("/proc/{pid}/stat")).ok()?;
    parse_proc_starttime_ticks(&stat)
}

#[cfg(not(target_os = "linux"))]
fn platform_starttime_ticks(_pid: u32) -> Option<u64> {
    None
}

#[cfg(target_os = "linux")]
fn parse_proc_starttime_ticks(stat: &str) -> Option<u64> {
    let close = stat.rfind(')')?;
    stat[close + 1..].split_whitespace().nth(19)?.parse().ok()
}

fn bytes_to_kb(bytes: u64) -> u64 {
    bytes / 1024
}

fn bytes_to_mb(bytes: u64) -> u64 {
    if bytes == 0 {
        0
    } else {
        bytes.div_ceil(1_048_576)
    }
}

fn cpu_ms_to_ticks(cpu_ms: u64) -> u64 {
    ((cpu_ms as f64 / 1000.0) * ticks_per_second()).round() as u64
}

fn pid_to_u32(pid: Pid) -> u32 {
    pid.as_u32()
}

fn starttime_ticks_from_epoch(start_time_s: u64, boot_time_s: u64) -> u64 {
    let since_boot_s = if start_time_s >= boot_time_s {
        start_time_s - boot_time_s
    } else {
        start_time_s
    };
    ((since_boot_s as f64) * ticks_per_second()).round() as u64
}

pub fn process_start_timestamp_ms(starttime_ticks: u64) -> Option<u64> {
    let boot_ms = u64::try_from(crate::time::get_boot_time_secs().saturating_mul(1000)).ok()?;
    let process_offset_ms = ((starttime_ticks as f64 / ticks_per_second()) * 1000.0).round() as u64;
    Some(boot_ms.saturating_add(process_offset_ms))
}

pub fn process_cpu_ms_delta(proc_info: &ProcInfo, previous: Option<&ProcSnapshot>) -> u64 {
    let Some(previous) = previous else {
        return 0;
    };
    let Some(prev_proc) = previous.procs.get(&proc_info.pid) else {
        return 0;
    };
    if prev_proc.starttime_ticks != proc_info.starttime_ticks {
        return 0;
    }
    let delta_ticks = proc_info.ticks.saturating_sub(prev_proc.ticks);
    ((delta_ticks as f64 / ticks_per_second()) * 1000.0).round() as u64
}

fn ticks_per_second() -> f64 {
    static TICKS_PER_SECOND: OnceLock<f64> = OnceLock::new();
    *TICKS_PER_SECOND.get_or_init(|| {
        let value = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
        if value > 0 { value as f64 } else { 100.0 }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;

    #[test]
    fn snapshot_collects_current_process() {
        let snapshot = ProcSnapshot::collect().unwrap();
        let current = snapshot.procs.get(&std::process::id()).unwrap();

        assert_eq!(current.pid, std::process::id());
        #[cfg(target_os = "linux")]
        let tid = unsafe { libc::gettid() } as u32;
        #[cfg(target_os = "linux")]
        assert!(!snapshot.procs.contains_key(&tid));
        assert!(current.starttime_ticks > 0);
        assert!(current.threads > if cfg!(target_os = "linux") { 1 } else { 0 });
        assert!(!current.comm.is_empty() || !current.command.is_empty());
    }

    #[cfg(unix)]
    #[test]
    fn snapshot_counts_single_thread_process() {
        let mut child = Command::new("sleep").arg("5").spawn().unwrap();
        let snapshot = ProcSnapshot::collect().unwrap();
        let threads = snapshot.procs.get(&child.id()).map(|p| p.threads);
        let _ = child.kill();
        let _ = child.wait();

        assert_eq!(threads, Some(1));
    }

    #[test]
    fn starttime_ticks_accepts_epoch_or_boot_relative_seconds() {
        let ticks = ticks_per_second().round() as u64;

        assert_eq!(starttime_ticks_from_epoch(125, 100), 25 * ticks);
        assert_eq!(starttime_ticks_from_epoch(25, 100), 25 * ticks);
    }

    #[cfg(target_os = "linux")]
    #[test]
    fn proc_fd_scan_finds_open_file_path() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("fd-evidence.txt");
        let _file = std::fs::File::create(&path).unwrap();

        let paths = scan_proc_fd_paths(std::process::id());
        assert!(paths.contains(&path));
    }

    #[test]
    fn lsof_parser_keeps_absolute_file_names() {
        let mut out = BTreeSet::new();

        parse_lsof_file_names(
            "p123\nn/private/tmp/session.jsonl\nnlocalhost:1234\nn\n",
            &mut out,
        );

        assert!(out.contains(&PathBuf::from("/private/tmp/session.jsonl")));
        assert_eq!(out.len(), 1);
    }
}
