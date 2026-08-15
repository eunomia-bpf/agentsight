// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-evolution projections and self-contained visual artifacts for
//! local AI-agent sessions.

mod export;
mod repository;

pub use export::{CompactRate, run_vis};
pub use repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
};

pub const DEFAULT_OUTPUT: &str = "output/agent-session-evolution.gif";
