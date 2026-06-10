// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! OpenClaw gateway, usually containerized (`tini -s -- node openclaw.mjs
//! gateway`). Capture attaches via `--binary-path docker://<container>`,
//! which walks the container's process tree to the SSL-embedding process.

use super::{AgentAdapter, Attribution, Discover};

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "openclaw",
    exec_names: &["openclaw"],
    // Kernel comm truncates to 15 chars: "openclaw-gatewa".
    exec_name_prefixes: &["openclaw-"],
    package_path_markers: &[],
    discover: Some(Discover {
        id: "openclaw",
        display_name: "OpenClaw",
        command: "docker",
        recommended_capture: "agentsight record -c node --db record.db --binary-path docker://<container>",
    }),
    native_sessions: None,
    attribution: Attribution::ProcessOnly,
    decode_observations: None,
};
