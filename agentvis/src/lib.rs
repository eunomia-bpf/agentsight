// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-evolution projections and self-contained visual artifacts for
//! local AI-agent sessions.

mod export;
mod repository;

pub use export::run_vis;
pub use repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
};
