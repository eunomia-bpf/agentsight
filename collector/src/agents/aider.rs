// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Aider (Python). Python links system libssl, so plain `record -c python`
//! capture works. Labeled in process views; no discover entry yet.

use super::{AgentAdapter, Attribution};

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "aider",
    exec_names: &["aider"],
    exec_name_prefixes: &[],
    package_path_markers: &[],
    discover: None,
    native_sessions: None,
    attribution: Attribution::ProcessOnly,
    decode_observations: None,
};
