// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::io;
use std::path::PathBuf;
use std::time::Instant;

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
        let page_size = page_size_bytes();
        let mut procs = BTreeMap::new();

        for entry in fs::read_dir("/proc")? {
            let Ok(entry) = entry else { continue };
            let file_name = entry.file_name();
            let Some(pid) = file_name.to_str().and_then(|name| name.parse::<u32>().ok()) else {
                continue;
            };
            let Some(proc_info) = read_proc_info(pid, page_size) else {
                continue;
            };
            procs.insert(pid, proc_info);
        }

        Ok(Self {
            at: Instant::now(),
            uptime_s: read_uptime_s().unwrap_or_default(),
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

fn read_proc_info(pid: u32, page_size: u64) -> Option<ProcInfo> {
    let proc_dir = format!("/proc/{pid}");
    let stat = fs::read_to_string(format!("{proc_dir}/stat")).ok()?;
    let (comm, ppid, session_id, ticks, starttime_ticks) = parse_proc_stat(&stat)?;
    let command = read_cmdline(pid).unwrap_or_else(|| comm.clone());
    let cwd = read_cwd(pid);
    let (rss_kb, rss_mb, vsz_kb) = read_statm(pid, page_size).unwrap_or_default();
    let threads = read_thread_count(pid);
    Some(ProcInfo {
        pid,
        ppid,
        session_id,
        comm,
        command,
        cwd,
        ticks,
        starttime_ticks,
        rss_kb,
        rss_mb,
        vsz_kb,
        threads,
    })
}

pub(crate) fn process_starttime_ticks(pid: u32) -> Option<u64> {
    let stat = fs::read_to_string(format!("/proc/{pid}/stat")).ok()?;
    parse_proc_stat(&stat).map(|(_, _, _, _, starttime_ticks)| starttime_ticks)
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

fn parse_proc_stat(stat: &str) -> Option<(String, u32, u32, u64, u64)> {
    let open = stat.find('(')?;
    let close = stat.rfind(')')?;
    let comm = stat[open + 1..close].to_string();
    let fields: Vec<&str> = stat[close + 1..].split_whitespace().collect();
    let ppid = fields.get(1)?.parse().ok()?;
    let session_id = fields.get(3)?.parse().ok()?;
    let utime: u64 = fields.get(11)?.parse().ok()?;
    let stime: u64 = fields.get(12)?.parse().ok()?;
    let starttime_ticks = fields.get(19)?.parse().ok()?;
    Some((
        comm,
        ppid,
        session_id,
        utime.saturating_add(stime),
        starttime_ticks,
    ))
}

fn read_cmdline(pid: u32) -> Option<String> {
    let bytes = fs::read(format!("/proc/{pid}/cmdline")).ok()?;
    let command = bytes
        .split(|byte| *byte == 0)
        .filter_map(|part| std::str::from_utf8(part).ok())
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join(" ");
    (!command.is_empty()).then_some(command)
}

fn read_cwd(pid: u32) -> Option<PathBuf> {
    fs::read_link(format!("/proc/{pid}/cwd")).ok()
}

fn read_statm(pid: u32, page_size: u64) -> Option<(u64, u64, u64)> {
    let statm = fs::read_to_string(format!("/proc/{pid}/statm")).ok()?;
    let mut fields = statm.split_whitespace();
    let vsz_pages: u64 = fields.next()?.parse().ok()?;
    let rss_pages: u64 = fields.next()?.parse().ok()?;
    let rss_bytes = rss_pages.saturating_mul(page_size);
    let vsz_bytes = vsz_pages.saturating_mul(page_size);
    Some((
        bytes_to_kb(rss_bytes),
        bytes_to_mb(rss_bytes),
        bytes_to_kb(vsz_bytes),
    ))
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

fn read_uptime_s() -> Option<f64> {
    fs::read_to_string("/proc/uptime")
        .ok()?
        .split_whitespace()
        .next()?
        .parse()
        .ok()
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

fn page_size_bytes() -> u64 {
    let value = unsafe { libc::sysconf(libc::_SC_PAGESIZE) };
    if value > 0 { value as u64 } else { 4096 }
}

fn ticks_per_second() -> f64 {
    let value = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
    if value > 0 { value as f64 } else { 100.0 }
}

fn read_thread_count(pid: u32) -> u32 {
    fs::read_dir(format!("/proc/{pid}/task"))
        .map(|entries| entries.count() as u32)
        .unwrap_or(1)
}

pub(crate) fn read_process_io_bytes(pid: u32) -> Option<(u64, u64)> {
    let io = fs::read_to_string(format!("/proc/{pid}/io")).ok()?;
    let mut read_bytes = 0;
    let mut write_bytes = 0;
    for line in io.lines() {
        if let Some(value) = line.strip_prefix("read_bytes:") {
            read_bytes = value.trim().parse().ok()?;
        } else if let Some(value) = line.strip_prefix("write_bytes:") {
            write_bytes = value.trim().parse().ok()?;
        }
    }
    Some((read_bytes, write_bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;

    #[test]
    fn proc_fd_scan_finds_open_file_path() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("fd-evidence.txt");
        let _file = File::create(&path).unwrap();

        let paths = scan_proc_fd_paths(std::process::id());
        assert!(paths.contains(&path));
    }
}
