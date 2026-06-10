// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! OpenAI Codex CLI. Uses rustls, so SSL payload capture is not available;
//! the adapter still provides process/stdio tracking and run receipts from
//! native session logs under `~/.codex/sessions`.

use super::{AgentAdapter, Attribution, Discover, NativeSessions};

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "codex",
    exec_names: &["codex", "codex-cli"],
    exec_name_prefixes: &[],
    package_path_markers: &["@openai/codex", "/codex-linux-"],
    discover: Some(Discover {
        id: "codex-cli",
        display_name: "Codex CLI",
        command: "codex",
        recommended_capture: "agentsight record --db record.db -- codex exec 'hello'",
    }),
    native_sessions: Some(NativeSessions {
        dir_parts: [".codex", "sessions"],
        path_marker: "/.codex/",
    }),
    attribution: Attribution::NativeSessionFiles,
    decode_observations: None,
};
