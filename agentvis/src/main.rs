// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use clap::Parser;
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    author,
    version,
    about = "Render repository evolution from local AI-agent sessions"
)]
struct Cli {
    /// Git worktree to visualize.
    #[arg(default_value = ".")]
    path: PathBuf,
    /// Output path; repeat for HTML, SVG, PNG, GIF, and MP4.
    #[arg(short = 'o', long = "output", default_value = agentvis::DEFAULT_OUTPUT)]
    outputs: Vec<PathBuf>,
    /// Scan every local session and retain operations targeting this repository.
    #[arg(long)]
    global: bool,
    /// Compact GIF/MP4 uniformly by action to this duration, or use `full`.
    #[arg(long, default_value = "30s")]
    compact_rate: agentvis::CompactRate,
}

fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let cli = Cli::parse();
    agentvis::run_vis(&cli.path, &cli.outputs, cli.global, cli.compact_rate)
}
