// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::Deserialize;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

pub const NODE_INFO: &str = "node.info";
pub const EVIDENCE_READ: &str = "evidence.read";
pub const SESSION_READ: &str = "session.read";
pub const SESSION_MESSAGE: &str = "session.message";

const MAX_TTL_SECONDS: u64 = 12 * 60 * 60;

#[derive(Debug, Clone)]
struct Grant {
    node_id: String,
    actions: Vec<String>,
    session_id: Option<String>,
    expires_at: u64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CapabilityMintRequest {
    pub actions: Vec<String>,
    #[serde(default)]
    pub session_id: Option<String>,
    #[serde(default = "default_ttl_seconds")]
    pub ttl_seconds: u64,
}

impl CapabilityMintRequest {
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.actions.is_empty() || self.actions.len() > 8 {
            return Err("capability must contain between 1 and 8 actions");
        }
        if self.actions.iter().any(|action| !known_action(action)) {
            return Err("capability contains an unknown action");
        }
        if !(30..=MAX_TTL_SECONDS).contains(&self.ttl_seconds) {
            return Err("capability ttl must be between 30 seconds and 12 hours");
        }
        if self.session_id.as_deref().is_some_and(|value| !valid_session_id(value)) {
            return Err("invalid capability session scope");
        }
        Ok(())
    }
}

#[derive(Debug, Default)]
pub struct CapabilityStore {
    grants: HashMap<String, Grant>,
}

impl CapabilityStore {
    pub fn mint(
        &mut self,
        node_id: &str,
        request: &CapabilityMintRequest,
    ) -> Result<(String, u64), &'static str> {
        request.validate()?;
        let now = now_seconds();
        self.remove_expired(now);
        let token = format!(
            "cap_{}{}",
            uuid::Uuid::new_v4().simple(),
            uuid::Uuid::new_v4().simple()
        );
        let expires_at = now.saturating_add(request.ttl_seconds);
        self.grants.insert(
            token.clone(),
            Grant {
                node_id: node_id.to_string(),
                actions: request.actions.clone(),
                session_id: request.session_id.clone(),
                expires_at,
            },
        );
        Ok((token, expires_at))
    }

    pub fn authorizes(
        &mut self,
        node_id: &str,
        token: &str,
        action: &str,
        session_id: Option<&str>,
    ) -> bool {
        let now = now_seconds();
        self.remove_expired(now);
        let Some(grant) = self.grants.get(token) else {
            return false;
        };
        if grant.node_id != node_id || !grant.actions.iter().any(|candidate| candidate == action) {
            return false;
        }
        match grant.session_id.as_deref() {
            Some(expected) => session_id == Some(expected),
            None => true,
        }
    }

    fn remove_expired(&mut self, now: u64) {
        self.grants.retain(|_, grant| grant.expires_at >= now);
    }
}

pub fn action_for_request(method: &str, path: &str) -> Option<(&'static str, Option<String>)> {
    let path = path.split_once('?').map_or(path, |(path, _)| path);
    if method == "GET" && path == "/api/v1/info" {
        return Some((NODE_INFO, None));
    }
    if method == "GET" && path == "/api/v1/snapshot" {
        return Some((EVIDENCE_READ, None));
    }
    let session = path.strip_prefix("/api/v1/sessions/")?;
    let (session_id, messages) = session
        .strip_suffix("/messages")
        .map_or((session, false), |id| (id, true));
    if !valid_session_id(session_id) {
        return None;
    }
    if method == "GET" && !messages {
        return Some((SESSION_READ, Some(session_id.to_string())));
    }
    if method == "POST" && messages {
        return Some((SESSION_MESSAGE, Some(session_id.to_string())));
    }
    None
}

pub fn known_action(action: &str) -> bool {
    matches!(action, NODE_INFO | EVIDENCE_READ | SESSION_READ | SESSION_MESSAGE)
}

fn valid_session_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 768
        && !value.contains('/')
        && !value.contains('\\')
        && !value.contains("..")
}

fn default_ttl_seconds() -> u64 {
    300
}

fn now_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(actions: &[&str], session_id: Option<&str>) -> CapabilityMintRequest {
        CapabilityMintRequest {
            actions: actions.iter().map(|value| value.to_string()).collect(),
            session_id: session_id.map(str::to_string),
            ttl_seconds: 60,
        }
    }

    #[test]
    fn scoped_capability_authorizes_only_requested_action_and_session() {
        let mut store = CapabilityStore::default();
        let (token, _) = store
            .mint("node_test", &request(&[SESSION_READ], Some("session-1")))
            .unwrap();
        assert!(store.authorizes(
            "node_test",
            &token,
            SESSION_READ,
            Some("session-1"),
        ));
        assert!(!store.authorizes(
            "node_test",
            &token,
            SESSION_MESSAGE,
            Some("session-1"),
        ));
        assert!(!store.authorizes(
            "node_test",
            &token,
            SESSION_READ,
            Some("session-2"),
        ));
        assert!(!store.authorizes(
            "node_other",
            &token,
            SESSION_READ,
            Some("session-1"),
        ));
    }

    #[test]
    fn protocol_paths_map_to_semantic_actions() {
        assert_eq!(action_for_request("GET", "/api/v1/info"), Some((NODE_INFO, None)));
        assert_eq!(
            action_for_request("GET", "/api/v1/sessions/s-1"),
            Some((SESSION_READ, Some("s-1".to_string())))
        );
        assert_eq!(
            action_for_request("POST", "/api/v1/sessions/s-1/messages"),
            Some((SESSION_MESSAGE, Some("s-1".to_string())))
        );
        assert_eq!(action_for_request("GET", "/etc/passwd"), None);
    }

    #[test]
    fn mint_rejects_unknown_actions_and_excessive_ttl() {
        let mut store = CapabilityStore::default();
        let mut invalid = request(&["root"], None);
        assert!(store.mint("node_test", &invalid).is_err());
        invalid.actions = vec![NODE_INFO.to_string()];
        invalid.ttl_seconds = MAX_TTL_SECONDS + 1;
        assert!(store.mint("node_test", &invalid).is_err());
    }
}
