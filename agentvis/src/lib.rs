// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-evolution projections and self-contained visual artifacts for
//! local AI-agent sessions.

mod export;
mod repository;
mod research;
mod research_supervisor;
mod rq1;

pub use export::{CompactRate, run_vis};
pub use repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
};
pub use research::run_research_store_from_args;
pub use research_supervisor::run_research_supervisor_from_args;
pub use rq1::run_rq1_from_args;

pub const DEFAULT_OUTPUT: &str = "output/agent-nebula.gif";
