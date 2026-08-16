// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Native, cross-platform capture substrate for AgentSight.
//!
//! Product analysis, materialization, storage, and presentation live under
//! `ext/`; this crate keeps the existing Event/Runner/Analyzer boundary and
//! platform collectors.

#![allow(clippy::too_many_arguments)]

pub mod analyzers;
pub mod binary_extractor;
pub mod binary_resolver;
pub mod event;
pub mod runners;
pub mod sources;
pub mod time;

pub use binary_extractor::BinaryExtractor;
pub use event::Event;
pub use runners::{AgentRunner, EventStream, Runner, RunnerError};
