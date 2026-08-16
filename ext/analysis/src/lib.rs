// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! AgentSight post-capture extension set.
//!
//! Existing analysis, materialization, storage, and agent/session projection
//! live here. The native capture crate stays the stable platform boundary.

#![allow(clippy::too_many_arguments)]

pub use agentsight_capture_core::{binary_extractor, binary_resolver, event, time};
pub use agentsight_capture_core::{BinaryExtractor, Event, EventStream, Runner, RunnerError};

mod json;
pub mod analyzers;
pub mod model;
pub mod runners;
pub mod sinks;
pub mod sources;
pub mod text;
pub mod view;

pub use view::{MaterializedView, SharedMaterializedView};
