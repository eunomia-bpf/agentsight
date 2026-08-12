// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

pub const NODE_INFO: &str = "node.info";
pub const EVIDENCE_READ: &str = "evidence.read";
pub const SESSION_READ: &str = "session.read";
pub const SESSION_MESSAGE: &str = "session.message";

const MAX_TTL_SECONDS: u64 = 12 * 60 * 60;
const PERSIST_THRESHOLD_SECONDS: u64 = 10 * 60;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Grant {
    node_id: String,
    actions: Vec<String>,
    session_id: Option<String>,
    expires_at: u64,
    persistent: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct PersistedCapabilities {
    node_id: String,
    grants: HashMap<String, Grant>,
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
    node_id: Option<String>,
    persist_path: Option<PathBuf>,
    grants: HashMap<String, Grant>,
}

impl CapabilityStore {
    pub fn for_node(node_id: &str) -> Self {
        let persist_path = capability_path();
        let now = now_seconds();
        let grants = persist_path
            .as_ref()
            .and_then(|path| std::fs::read(path).ok())
            .and_then(|bytes| serde_json::from_slice::<PersistedCapabilities>(&bytes).ok())
            .filter(|saved| saved.node_id == node_id)
            .map(|saved| {
                saved
                    .grants
                    .into_iter()
                    .filter(|(_, grant)| grant.persistent && grant.expires_at >= now)
                    .collect()
            })
            .unwrap_or_default();
        Self {
            node_id: Some(node_id.to_string()),
            persist_path,
            grants,
        }
    }

    pub fn mint(
        &mut self,
        node_id: &str,
        request: &CapabilityMintRequest,
    ) -> Result<(String, u64), &'static str> {
        request.validate()?;
        if self.node_id.as_deref().is_some_and(|configured| configured != node_id) {
            return Err("capability store belongs to another Node");
        }
        if self.node_id.is_none() {
            self.node_id = Some(node_id.to_string());
        }
        let now = now_seconds();
        self.remove_expired(now);
        let token = format!(
            "cap_{}{}",
            uuid::Uuid::new_v4().simple(),
            uuid::Uuid::new_v4().simple()
        );
        let expires_at = now.saturating_add(request.ttl_seconds);
        let persistent = request.ttl_seconds > PERSIST_THRESHOLD_SECONDS;
        self.grants.insert(
            token.clone(),
            Grant {
                node_id: node_id.to_string(),
                actions: request.actions.clone(),
                session_id: request.session_id.clone(),
                expires_at,
                persistent,
            },
        );
        if persistent {
            self.persist().map_err(|_| "could not persist capability")?;
        }
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

    fn persist(&self) -> std::io::Result<()> {
        let (Some(node_id), Some(path)) = (self.node_id.as_deref(), self.persist_path.as_ref()) else {
            return Ok(());
        };
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let saved = PersistedCapabilities {
            node_id: node_id.to_string(),
            grants: self
                .grants
                .iter()
                .filter(|(_, grant)| grant.persistent)
                .map(|(token, grant)| (token.clone(), grant.clone()))
                .collect(),
        };
        let bytes = serde_json::to_vec(&saved).map_err(std::io::Error::other)?;
        let mut options = std::fs::OpenOptions::new();
        options.write(true).create(true).truncate(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        use std::io::Write;
        let mut file = options.open(path)?;
        file.write_all(&bytes)?;
        file.sync_all()?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600))?;
        }
        Ok(())
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

fn capability_path() -> Option<PathBuf> {
    dirs::config_dir().map(|dir| dir.join("agentsight").join("capabilities.json"))
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
    fn long_lived_capability_round_trips_through_persistent_state() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("capabilities.json");
        let mut store = CapabilityStore {
            node_id: Some("node_test".to_string()),
            persist_path: Some(path.clone()),
            grants: HashMap::new(),
        };
        let request = CapabilityMintRequest {
            actions: vec![NODE_INFO.to_string(), EVIDENCE_READ.to_string()],
            session_id: None,
            ttl_seconds: 3600,
        };
        let (token, _) = store.mint("node_test", &request).unwrap();
        let saved: PersistedCapabilities = serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
        let mut restarted = CapabilityStore {
            node_id: Some(saved.node_id),
            persist_path: None,
            grants: saved.grants,
        };
        assert!(restarted.authorizes("node_test", &token, EVIDENCE_READ, None));
        assert!(!restarted.authorizes("node_test", &token, SESSION_MESSAGE, None));
    }

    #[test]
    fn short_relay_capability_is_not_persisted() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("capabilities.json");
        let mut store = CapabilityStore {
            node_id: Some("node_test".to_string()),
            persist_path: Some(path.clone()),
            grants: HashMap::new(),
        };
        store.mint("node_test", &request(&[SESSION_READ], None)).unwrap();
        assert!(!path.exists());
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