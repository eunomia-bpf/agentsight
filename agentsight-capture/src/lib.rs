// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Reusable event capture and analysis pipeline used by the AgentSight CLI.

#![allow(clippy::too_many_arguments)]

pub mod analyzers;
pub mod binary_extractor;
pub mod binary_resolver;
pub mod event;
mod json;
pub mod model;
pub mod runners;
pub mod sinks;
pub mod sources;
pub mod text;
mod time;
pub mod view;

pub use binary_extractor::BinaryExtractor;
pub use event::Event;
pub use runners::{AgentRunner, EventStream, Runner, RunnerError};
pub use view::{MaterializedView, SharedMaterializedView};
