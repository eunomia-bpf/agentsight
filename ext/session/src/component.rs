// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::path::Path;
use std::time::{Duration, UNIX_EPOCH};

wit_bindgen::generate!({ world: "session-ext" });

struct SessionExt;

impl Guest for SessionExt {
    fn parse(agent: String, path: String, updated_ms: u64, content: String) -> Option<String> {
        let updated = UNIX_EPOCH + Duration::from_millis(updated_ms);
        // Components execute under WASI, whose `Path` only recognizes `/` as a
        // separator. Normalize host-provided Windows paths before deriving IDs.
        let normalized_path = path.replace('\\', "/");
        crate::parse_session_content(&agent, Path::new(&normalized_path), updated, &content)
            .and_then(|session| serde_json::to_string(&session).ok())
    }
}

export!(SessionExt);
