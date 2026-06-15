// SPDX-License-Identifier: MIT
//
// Windows eBPF runner.
//
// Drives the eBPF-for-Windows programs in `bpf/windows/` (process lifecycle +
// network connection telemetry). The actual eBPF load is done by a small native
// loader, `agentsight-ebpf-loader.exe`, which links `ebpfapi.dll` (the Windows
// libbpf surface), attaches the programs, polls their ring buffers, and
// serializes each record to the SAME JSONL the Linux `process` binary emits
// (`{"event":"EXEC"|"EXIT"|"CONNECT", "timestamp":..., "pid":..., ...}`).
//
// Keeping the eBPF load in a native helper (rather than binding `ebpfapi.dll`
// from Rust) mirrors the existing architecture: every producer is an external
// binary that streams JSONL, and `BinaryRunner` is the shared engine. The Rust
// side stays OS-portable and the libbpf/ebpfapi linkage lives where the Windows
// toolchain already is.
#![cfg(windows)]

use super::common::BinaryRunner;
use std::path::{Path, PathBuf};

/// Which Windows eBPF program set to load.
#[derive(Clone, Copy)]
pub enum WindowsEbpfProgram {
    /// process_win.o — EBPF_PROGRAM_TYPE_PROCESS (EXEC/EXIT).
    Process,
    /// sockaddr_win.o + sockops_win.o — connection telemetry (CONNECT/DISCONNECT).
    Network,
}

impl WindowsEbpfProgram {
    fn loader_arg(self) -> &'static str {
        match self {
            WindowsEbpfProgram::Process => "--process",
            WindowsEbpfProgram::Network => "--network",
        }
    }

    /// Event `source` name, matching the Linux runners.
    fn source(self) -> &'static str {
        match self {
            WindowsEbpfProgram::Process => "process",
            WindowsEbpfProgram::Network => "net",
        }
    }
}

/// Builds a [`BinaryRunner`] that drives `agentsight-ebpf-loader.exe` for the
/// chosen program set. Produces the same event stream shape as the Linux eBPF
/// runners, so downstream analyzers / the materialized view are unchanged.
pub struct WindowsEbpfRunner {
    loader_exe: PathBuf,
    object_dir: PathBuf,
    program: WindowsEbpfProgram,
    targ_pid: Option<u32>,
}

impl WindowsEbpfRunner {
    pub fn new(
        loader_exe: impl AsRef<Path>,
        object_dir: impl AsRef<Path>,
        program: WindowsEbpfProgram,
    ) -> Self {
        Self {
            loader_exe: loader_exe.as_ref().to_path_buf(),
            object_dir: object_dir.as_ref().to_path_buf(),
            program,
            targ_pid: None,
        }
    }

    /// Restrict to a single PID (sets the program's `targ_pid` constant).
    pub fn with_pid(mut self, pid: u32) -> Self {
        self.targ_pid = Some(pid);
        self
    }

    pub fn into_runner(self) -> BinaryRunner {
        let mut args: Vec<String> = vec![
            self.program.loader_arg().to_string(),
            "--object-dir".to_string(),
            self.object_dir.to_string_lossy().into_owned(),
        ];
        if let Some(pid) = self.targ_pid {
            args.push("--pid".to_string());
            args.push(pid.to_string());
        }
        // Process events use "timestamp"; net records also carry "timestamp".
        BinaryRunner::new("WinEbpf", self.program.source(), "timestamp", &self.loader_exe)
            .with_args(args)
    }
}
