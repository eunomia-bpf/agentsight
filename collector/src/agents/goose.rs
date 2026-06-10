// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Goose CLI. Labeled in process views; no discover entry or native session
//! support yet.

use super::{AgentAdapter, Attribution};

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "goose",
    exec_names: &["goose"],
    exec_name_prefixes: &[],
    package_path_markers: &[],
    discover: None,
    native_sessions: None,
    attribution: Attribution::ProcessOnly,
    decode_observations: None,
};
