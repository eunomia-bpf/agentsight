// SPDX-License-Identifier: MIT
//
// Windows stdio runner. Drives `agentsight-stdio-cap.exe` (ConPTY capture; see
// shim/win-stdio-cap). The producer emits the same `source = "stdio"` /
// `timestamp_field = "timestamp_ns"` JSONL the Linux `stdiocap` binary emits, so
// downstream handling is unchanged. Like the Linux `record -- <command>` model,
// Windows stdio capture must launch the command (ConPTY handles are set up
// before the child starts); attach-to-existing is not supported.
#![cfg(windows)]

use super::common::BinaryRunner;
use std::path::{Path, PathBuf};

pub struct WindowsStdioRunner {
    cap_exe: PathBuf,
    command: Vec<String>,
}

impl WindowsStdioRunner {
    pub fn new(cap_exe: impl AsRef<Path>, command: Vec<String>) -> Self {
        Self {
            cap_exe: cap_exe.as_ref().to_path_buf(),
            command,
        }
    }

    pub fn into_runner(self) -> BinaryRunner {
        let mut args: Vec<String> = vec!["--".to_string()];
        args.extend(self.command);
        BinaryRunner::new("Stdio", "stdio", "timestamp_ns", &self.cap_exe).with_args(args)
    }
}
