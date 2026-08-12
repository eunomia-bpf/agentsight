// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::time::{SystemTime, UNIX_EPOCH};

pub const NODE_INFO: &str = "node.info";
pub const EVIDENCE_READ: &str = "evidence.read";
pub const SESSION_READ: &str = "session.read";
pub const SESSION_MESSAGE: &str = "session.message";

const TOKEN_PREFIX: &str = "cap_";
const DOMAIN: &[u8] = b"AgentSight.NodeCapability.v1\0";
const SIGNATURE_BYTES: usize = 32;
const MAX_TOKEN_BYTES: usize = 4096;
const MAX_TTL_SECONDS: u64 = 12 * 60 * 60;
const HMAC_BLOCK_BYTES: usize = 64;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
struct Claims {
    v: u8,
    node: String,
    actions: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    session_id: Option<String>,
    exp: u64,
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

pub fn mint(
    bootstrap_secret: &str,
    node_id: &str,
    request: &CapabilityMintRequest,
) -> Result<(String, u64), &'static str> {
    request.validate()?;
    if bootstrap_secret.is_empty() || node_id.is_empty() {
        return Err("capability issuer is not configured");
    }
    let expires_at = now_seconds().saturating_add(request.ttl_seconds);
    let claims = Claims {
        v: 1,
        node: node_id.to_string(),
        actions: request.actions.clone(),
        session_id: request.session_id.clone(),
        exp: expires_at,
    };
    let payload = serde_json::to_vec(&claims).map_err(|_| "could not encode capability")?;
    let signature = capability_signature(bootstrap_secret.as_bytes(), &payload);
    let mut token_bytes = Vec::with_capacity(payload.len() + SIGNATURE_BYTES);
    token_bytes.extend_from_slice(&payload);
    token_bytes.extend_from_slice(&signature);
    let token = format!("{TOKEN_PREFIX}{}", URL_SAFE_NO_PAD.encode(token_bytes));
    if token.len() > MAX_TOKEN_BYTES {
        return Err("capability is too large");
    }
    Ok((token, expires_at))
}

pub fn authorizes(
    bootstrap_secret: &str,
    node_id: &str,
    token: &str,
    action: &str,
    session_id: Option<&str>,
) -> bool {
    let Some(claims) = verify(bootstrap_secret, token) else {
        return false;
    };
    if claims.node != node_id || !claims.actions.iter().any(|candidate| candidate == action) {
        return false;
    }
    match claims.session_id.as_deref() {
        Some(expected) => session_id == Some(expected),
        None => true,
    }
}

fn verify(bootstrap_secret: &str, token: &str) -> Option<Claims> {
    if token.len() > MAX_TOKEN_BYTES || bootstrap_secret.is_empty() {
        return None;
    }
    let encoded = token.strip_prefix(TOKEN_PREFIX)?;
    let decoded = URL_SAFE_NO_PAD.decode(encoded).ok()?;
    if decoded.len() <= SIGNATURE_BYTES {
        return None;
    }
    let split = decoded.len() - SIGNATURE_BYTES;
    let (payload, supplied_signature) = decoded.split_at(split);
    let expected_signature = capability_signature(bootstrap_secret.as_bytes(), payload);
    if !constant_time_eq(&expected_signature, supplied_signature) {
        return None;
    }
    let claims: Claims = serde_json::from_slice(payload).ok()?;
    if claims.v != 1
        || claims.exp < now_seconds()
        || claims.actions.is_empty()
        || claims.actions.len() > 8
        || claims.actions.iter().any(|action| !known_action(action))
        || claims.session_id.as_deref().is_some_and(|value| !valid_session_id(value))
    {
        return None;
    }
    Some(claims)
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

fn capability_signature(key: &[u8], payload: &[u8]) -> [u8; SIGNATURE_BYTES] {
    let mut message = Vec::with_capacity(DOMAIN.len() + payload.len());
    message.extend_from_slice(DOMAIN);
    message.extend_from_slice(payload);
    hmac_sha256(key, &message)
}

fn hmac_sha256(key: &[u8], data: &[u8]) -> [u8; SIGNATURE_BYTES] {
    let mut normalized = [0u8; HMAC_BLOCK_BYTES];
    if key.len() > HMAC_BLOCK_BYTES {
        let digest = Sha256::digest(key);
        normalized[..digest.len()].copy_from_slice(&digest);
    } else {
        normalized[..key.len()].copy_from_slice(key);
    }

    let mut inner_pad = [0x36u8; HMAC_BLOCK_BYTES];
    let mut outer_pad = [0x5cu8; HMAC_BLOCK_BYTES];
    for index in 0..HMAC_BLOCK_BYTES {
        inner_pad[index] ^= normalized[index];
        outer_pad[index] ^= normalized[index];
    }

    let mut inner = Sha256::new();
    inner.update(inner_pad);
    inner.update(data);
    let inner_digest = inner.finalize();

    let mut outer = Sha256::new();
    outer.update(outer_pad);
    outer.update(inner_digest);
    outer.finalize().into()
}

fn constant_time_eq(expected: &[u8], supplied: &[u8]) -> bool {
    if expected.len() != supplied.len() {
        return false;
    }
    expected
        .iter()
        .zip(supplied)
        .fold(0u8, |difference, (left, right)| difference | (left ^ right))
        == 0
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
        let (token, _) = mint(
            "persistent-root",
            "node_test",
            &request(&[SESSION_READ], Some("session-1")),
        )
        .unwrap();
        assert!(authorizes(
            "persistent-root",
            "node_test",
            &token,
            SESSION_READ,
            Some("session-1"),
        ));
        assert!(!authorizes(
            "persistent-root",
            "node_test",
            &token,
            SESSION_MESSAGE,
            Some("session-1"),
        ));
        assert!(!authorizes(
            "persistent-root",
            "node_test",
            &token,
            SESSION_READ,
            Some("session-2"),
        ));
        assert!(!authorizes(
            "persistent-root",
            "node_other",
            &token,
            SESSION_READ,
            Some("session-1"),
        ));
    }

    #[test]
    fn capability_is_stateless_and_bound_to_the_persistent_root() {
        let (token, expires_at) = mint(
            "persistent-root",
            "node_test",
            &request(&[NODE_INFO, EVIDENCE_READ], None),
        )
        .unwrap();
        assert!(expires_at > now_seconds());
        assert!(token.starts_with(TOKEN_PREFIX));
        assert!(authorizes(
            "persistent-root",
            "node_test",
            &token,
            EVIDENCE_READ,
            None,
        ));
        assert!(!authorizes(
            "rotated-root",
            "node_test",
            &token,
            EVIDENCE_READ,
            None,
        ));

        let mut tampered = token.into_bytes();
        let last = tampered.last_mut().unwrap();
        *last = if *last == b'A' { b'B' } else { b'A' };
        assert!(!authorizes(
            "persistent-root",
            "node_test",
            std::str::from_utf8(&tampered).unwrap(),
            EVIDENCE_READ,
            None,
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
        let mut invalid = request(&["root"], None);
        assert!(mint("persistent-root", "node_test", &invalid).is_err());
        invalid.actions = vec![NODE_INFO.to_string()];
        invalid.ttl_seconds = MAX_TTL_SECONDS + 1;
        assert!(mint("persistent-root", "node_test", &invalid).is_err());
    }
}