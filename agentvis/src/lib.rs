// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-evolution projections and self-contained visual artifacts for
//! local AI-agent sessions.

mod export;
mod layout;
mod repository;

pub use export::{CompactRate, run_vis};
pub use layout::{
    DEFAULT_MAX_FRAMES, DEFAULT_MAX_STARS, NebulaActive, NebulaArea, NebulaDocument,
    NebulaFileAction, NebulaFrame, NebulaLayoutOptions, NebulaMeta, NebulaStar,
    build_nebula_document, resting_symbol_size,
};
pub use repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
};

pub const DEFAULT_OUTPUT: &str = "output/agent-nebula.gif";
