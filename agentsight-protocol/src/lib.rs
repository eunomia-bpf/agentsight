// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.
//! Transport-independent AgentSight Node API contract.

use serde::{Deserialize, Serialize};

pub const PROTOCOL_VERSION: u32 = 1;
pub const PRODUCT: &str = "agentsight";
const SESSION_PREFIX: &str = "/api/v1/sessions/";

#[derive(Debug, Serialize, Deserialize)]
pub struct SessionMessageRequest {
    pub message: String,
}

impl SessionMessageRequest {
    pub fn validate(&self) -> Result<&str, &'static str> {
        let message = self.message.trim();
        (!message.is_empty() && message.len() <= 65_536)
            .then_some(message)
            .ok_or("message must contain 1-65536 bytes")
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn info_path() -> String {
    "/api/v1/info".into()
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn snapshot_path(limit: usize) -> String {
    format!("/api/v1/snapshot?audit_limit={limit}")
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn overview_path() -> String {
    "/api/v1/overview".into()
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_path(id: &str) -> String {
    format!("{SESSION_PREFIX}{id}")
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_messages_path(id: &str) -> String {
    format!("{SESSION_PREFIX}{id}/messages")
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen::prelude::wasm_bindgen)]
pub fn session_message_body(message: &str) -> String {
    serde_json::to_string(&SessionMessageRequest {
        message: message.into(),
    })
    .expect("serializing a string request cannot fail")
}

pub fn session_detail_id(path: &str) -> Option<&str> {
    let id = path.strip_prefix(SESSION_PREFIX)?;
    (!id.is_empty() && !id.contains('/')).then_some(id)
}

pub fn session_message_id(path: &str) -> Option<&str> {
    let id = path
        .strip_prefix(SESSION_PREFIX)?
        .strip_suffix("/messages")?;
    (!id.is_empty() && !id.contains('/')).then_some(id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_paths_preserve_the_node_contract() {
        assert_eq!(info_path(), "/api/v1/info");
        assert_eq!(snapshot_path(500), "/api/v1/snapshot?audit_limit=500");
        assert_eq!(overview_path(), "/api/v1/overview");
        assert_eq!(session_path("s-1"), "/api/v1/sessions/s-1");
        assert_eq!(
            session_messages_path("s-1"),
            "/api/v1/sessions/s-1/messages"
        );
        assert_eq!(session_detail_id("/api/v1/sessions/s-1"), Some("s-1"));
        assert_eq!(
            session_message_id("/api/v1/sessions/s-1/messages"),
            Some("s-1")
        );
        assert_eq!(session_detail_id("/api/v1/sessions/s-1/messages"), None);
    }

    #[test]
    fn message_validation_preserves_the_published_api() {
        let request = SessionMessageRequest {
            message: "  hello  ".into(),
        };
        assert_eq!(request.validate(), Ok("hello"));

        for message in ["".to_string(), " \n\t ".to_string(), "x".repeat(65_537)] {
            assert_eq!(
                SessionMessageRequest { message }.validate(),
                Err("message must contain 1-65536 bytes")
            );
        }
        assert!(
            SessionMessageRequest {
                message: "x".repeat(65_536)
            }
            .validate()
            .is_ok()
        );
    }
}
