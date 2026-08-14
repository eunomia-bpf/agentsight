// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.
//! Transport-independent AgentSight Node API contract.
use serde::{Deserialize, Serialize};

#[cfg(feature = "bridge")]
pub mod bridge;

pub const PROTOCOL_VERSION: u32 = 1;
pub const PRODUCT: &str = "agentsight";
const SESSION_PREFIX: &str = "/api/v1/sessions/";

#[derive(Debug, Serialize, Deserialize)]
pub struct SessionMessageRequest { pub message: String }

impl SessionMessageRequest {
    pub fn validate(&self) -> Result<&str, &'static str> {
        let message = self.message.trim();
        (!message.is_empty() && message.len() <= 65_536)
            .then_some(message).ok_or("message must contain 1-65536 bytes")
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn info_path() -> String { "/api/v1/info".into() }
#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn snapshot_path(limit: usize) -> String { format!("/api/v1/snapshot?audit_limit={limit}") }
#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn overview_path() -> String { "/api/v1/overview".into() }
#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_path(id: &str) -> String { format!("{SESSION_PREFIX}{id}") }
#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_messages_path(id: &str) -> String { format!("{SESSION_PREFIX}{id}/messages") }
#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_message_body(message: &str) -> String {
    serde_json::to_string(&SessionMessageRequest { message: message.into() }).unwrap()
}

pub fn session_detail_id(path: &str) -> Option<&str> {
    let id = path.strip_prefix(SESSION_PREFIX)?;
    (!id.is_empty() && !id.contains('/')).then_some(id)
}
pub fn session_message_id(path: &str) -> Option<&str> {
    let id = path.strip_prefix(SESSION_PREFIX)?.strip_suffix("/messages")?;
    (!id.is_empty() && !id.contains('/')).then_some(id)
}
