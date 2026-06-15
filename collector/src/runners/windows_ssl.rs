// SPDX-License-Identifier: MIT
//
// Windows TLS-plaintext runner.
//
// eBPF-for-Windows has no uprobe, so SSL capture is done by the Detours shim in
// `shim/win-ssl-shim` (see docs/windows-migration.md). That shim's launcher,
// `agentsight-ssl-shim.exe`, behaves exactly like the Linux `sslsniff` binary
// from the collector's point of view: it emits the same `{"function":...,
// "data":...}` JSONL on stdout. So this runner is a thin builder that points the
// existing `BinaryRunner` engine at the shim — the parse/analyzer path is shared.
#![cfg(windows)]

use super::common::BinaryRunner;
use std::path::{Path, PathBuf};

/// How to apply the TLS shim: launch a new command, or attach to a running PID.
pub enum WindowsSslTarget {
    /// Launch this command (argv) under the shim.
    Launch(Vec<String>),
    /// Inject into an already-running process.
    AttachPid(u32),
}

/// Builds a [`BinaryRunner`] that drives the Windows TLS shim. The resulting
/// runner produces the same `source = "ssl"` / `timestamp_field = "timestamp_ns"`
/// event stream the Linux SSL path produces, so `SSLFilter` / `HTTPParser` /
/// `SSEProcessor` attach unchanged.
pub struct WindowsSslRunner {
    /// Path to `agentsight-ssl-shim.exe`.
    shim_exe: PathBuf,
    /// Path to `ssl_shim.dll` (injected into the target).
    shim_dll: PathBuf,
    target: WindowsSslTarget,
}

impl WindowsSslRunner {
    pub fn new(
        shim_exe: impl AsRef<Path>,
        shim_dll: impl AsRef<Path>,
        target: WindowsSslTarget,
    ) -> Self {
        Self {
            shim_exe: shim_exe.as_ref().to_path_buf(),
            shim_dll: shim_dll.as_ref().to_path_buf(),
            target,
        }
    }

    /// Construct the configured [`BinaryRunner`]. Attach analyzers on the result
    /// with `.add_analyzer(...)` exactly as on Linux.
    pub fn into_runner(self) -> BinaryRunner {
        let mut args: Vec<String> = vec![
            "--dll".to_string(),
            self.shim_dll.to_string_lossy().into_owned(),
        ];
        match self.target {
            WindowsSslTarget::AttachPid(pid) => {
                args.push("--pid".to_string());
                args.push(pid.to_string());
            }
            WindowsSslTarget::Launch(cmd) => {
                args.push("--".to_string());
                args.extend(cmd);
            }
        }
        BinaryRunner::new("SSL", "ssl", "timestamp_ns", &self.shim_exe).with_args(args)
    }
}
