// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::io;
use std::path::PathBuf;
use std::time::Instant;
use sysinfo::{Pid, Process, ProcessRefreshKind, ProcessesToUpdate, System, UpdateKind};

pub(crate) use agent_session::{ProcessKey, ProcessTree};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct PidSeed {
    pub(crate) pid: u32,
    pub(crate) ppid: u32,
}

impl PidSeed {
    pub(crate) fn arg_value(self) -> String {
        format!("{}:{}", self.pid, self.ppid)
    }
}

#[derive(Debug, Clone, Default)]
pub(crate) struct ProcInfo {
    pub(crate) pid: u32,
    pub(crate) ppid: u32,
    pub(crate) session_id: u32,
    pub(crate) comm: String,
    pub(crate) command: String,
    pub(crate) cwd: Option<PathBuf>,
    pub(crate) ticks: u64,
    pub(crate) starttime_ticks: u64,
    pub(crate) rss_kb: u64,
    pub(crate) rss_mb: u64,
    pub(crate) vsz_kb: u64,
    pub(crate) threads: u32,
    pub(crate) read_bytes: u64,
    pub(crate) write_bytes: u64,
}

impl ProcInfo {
    pub(crate) fn seed(&self) -> PidSeed {
        PidSeed {
            pid: self.pid,
            ppid: self.ppid,
        }
    }

    pub(crate) fn process_key(&self) -> ProcessKey {
        ProcessKey {
            pid: self.pid,
            starttime_ticks: self.starttime_ticks,
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct ProcSnapshot {
    pub(crate) at: Instant,
    pub(crate) uptime_s: f64,
    pub(crate) procs: BTreeMap<u32, ProcInfo>,
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
    pub(crate) fn collect() -> io::Result<Self> {
        let mut system = System::new();
        system.refresh_processes_specifics(ProcessesToUpdate::All, true, process_refresh_kind());
        let boot_time_s = System::boot_time();
        let procs = system
            .processes()
            .values()
            .map(|process| {
                let info = proc_info_from_sysinfo(process, boot_time_s);
                (info.pid, info)
            })
            .collect();

        Ok(Self {
            at: Instant::now(),
            uptime_s: System::uptime() as f64,
            procs,
        })
    }

    pub(crate) fn children_by_ppid(&self) -> HashMap<u32, Vec<u32>> {
        children_by_ppid(&self.procs)
    }

    pub(crate) fn process_family(&self, root: u32) -> Vec<u32> {
        process_family(root, &self.children_by_ppid(), &self.procs)
    }

    pub(crate) fn seeds_for_all(&self) -> Vec<PidSeed> {
        self.procs.values().map(ProcInfo::seed).collect()
    }

    pub(crate) fn seeds_for_pid_family(&self, root: u32) -> Vec<PidSeed> {
        self.process_family(root)
            .into_iter()
            .filter_map(|pid| self.procs.get(&pid).map(ProcInfo::seed))
            .collect()
    }

    pub(crate) fn seeds_for_session(&self, session_id: u32) -> Vec<PidSeed> {
        self.procs
            .values()
            .filter(|proc_info| proc_info.session_id == session_id)
            .map(ProcInfo::seed)
            .collect()
    }

    pub(crate) fn pids_in_session(&self, session_id: u32) -> Vec<u32> {
        self.procs
            .values()
            .filter(|proc_info| proc_info.session_id == session_id)
            .map(|proc_info| proc_info.pid)
            .collect()
    }
}

pub(crate) fn collect_fd_paths(
    process_trees: &[ProcessTree],
) -> HashMap<ProcessKey, BTreeSet<PathBuf>> {
    let mut out = HashMap::new();

    for tree in process_trees {
        for key in &tree.members {
            if process_starttime_ticks(key.pid) != Some(key.starttime_ticks) {
                continue;
            }
            let paths = scan_proc_fd_paths(key.pid);
            if process_starttime_ticks(key.pid) != Some(key.starttime_ticks) {
                continue;
            }
            if !paths.is_empty() {
                out.insert(*key, paths);
            }
        }
    }

    out
}

pub(crate) fn children_by_ppid(procs: &BTreeMap<u32, ProcInfo>) -> HashMap<u32, Vec<u32>> {
    let mut children: HashMap<u32, Vec<u32>> = HashMap::new();
    for proc_info in procs.values() {
        children
            .entry(proc_info.ppid)
            .or_default()
            .push(proc_info.pid);
    }
    children
}

pub(crate) fn process_family(
    root: u32,
    children: &HashMap<u32, Vec<u32>>,
    procs: &BTreeMap<u32, ProcInfo>,
) -> Vec<u32> {
    process_family_excluding(root, children, procs, &HashSet::new())
}

pub(crate) fn process_family_excluding(
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

pub(crate) fn process_cpu_percent(
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

pub(crate) fn process_age_s(proc_info: &ProcInfo, sample: &ProcSnapshot) -> f64 {
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
        threads: process.tasks().map(|tasks| tasks.len() as u32).unwrap_or(1),
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

pub(crate) fn process_starttime_ticks(pid: u32) -> Option<u64> {
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

pub(crate) fn scan_proc_fd_paths(pid: u32) -> BTreeSet<PathBuf> {
    let mut out = BTreeSet::new();
    let Ok(entries) = fs::read_dir(format!("/proc/{pid}/fd")) else {
        return out;
    };
    for entry in entries.flatten() {
        let Ok(target) = fs::read_link(entry.path()) else {
            continue;
        };
        out.insert(target);
    }
    out
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
    ((start_time_s.saturating_sub(boot_time_s) as f64) * ticks_per_second()).round() as u64
}

pub(crate) fn process_start_timestamp_ms(starttime_ticks: u64) -> Option<u64> {
    let boot_ms = u64::try_from(crate::time::get_boot_time_secs().saturating_mul(1000)).ok()?;
    let process_offset_ms = ((starttime_ticks as f64 / ticks_per_second()) * 1000.0).round() as u64;
    Some(boot_ms.saturating_add(process_offset_ms))
}

pub(crate) fn process_cpu_ms_delta(proc_info: &ProcInfo, previous: Option<&ProcSnapshot>) -> u64 {
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
    let value = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
    if value > 0 { value as f64 } else { 100.0 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snapshot_collects_current_process() {
        let snapshot = ProcSnapshot::collect().unwrap();
        let current = snapshot.procs.get(&std::process::id()).unwrap();

        assert_eq!(current.pid, std::process::id());
        assert!(current.starttime_ticks > 0);
        assert!(current.threads > 0);
        assert!(!current.comm.is_empty() || !current.command.is_empty());
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
}
