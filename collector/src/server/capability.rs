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

const TOKEN_PREFIX: &str = "as1";
const HMAC_BLOCK_BYTES: usize = 64;
const MAX_TOKEN_BYTES: usize = 4096;
const MAX_TTL_SECONDS: u64 = 600;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CapabilityClaims {
    pub v: u8,
    pub node: String,
    pub actions: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
    pub exp: u64,
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
            return Err("capability ttl must be between 30 and 600 seconds");
        }
        if self.session_id.as_deref().is_some_and(|value| !valid_session_id(value)) {
            return Err("invalid capability session scope");
        }
        Ok(())
    }
}

pub fn mint(
    secret: &str,
    node_id: &str,
    request: &CapabilityMintRequest,
) -> Result<String, &'static str> {
    request.validate()?;
    mint_at(secret, node_id, request, now_seconds())
}

fn mint_at(
    secret: &str,
    node_id: &str,
    request: &CapabilityMintRequest,
    now: u64,
) -> Result<String, &'static str> {
    if secret.is_empty() || node_id.is_empty() {
        return Err("capability issuer is not configured");
    }
    let claims = CapabilityClaims {
        v: 1,
        node: node_id.to_string(),
        actions: request.actions.clone(),
        session_id: request.session_id.clone(),
        exp: now.saturating_add(request.ttl_seconds),
    };
    let payload = serde_json::to_vec(&claims).map_err(|_| "could not encode capability")?;
    let payload = URL_SAFE_NO_PAD.encode(payload);
    let signed = format!("{TOKEN_PREFIX}.{payload}");
    let signature = URL_SAFE_NO_PAD.encode(hmac_sha256(secret.as_bytes(), signed.as_bytes()));
    Ok(format!("{signed}.{signature}"))
}

pub fn authorizes(
    secret: &str,
    node_id: &str,
    token: &str,
    action: &str,
    session_id: Option<&str>,
) -> bool {
    authorizes_at(secret, node_id, token, action, session_id, now_seconds())
}

fn authorizes_at(
    secret: &str,
    node_id: &str,
    token: &str,
    action: &str,
    session_id: Option<&str>,
    now: u64,
) -> bool {
    let Some(claims) = verify_at(secret, token, now) else {
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

pub fn verify(secret: &str, token: &str) -> Option<CapabilityClaims> {
    verify_at(secret, token, now_seconds())
}

fn verify_at(secret: &str, token: &str, now: u64) -> Option<CapabilityClaims> {
    if token.len() > MAX_TOKEN_BYTES {
        return None;
    }
    let mut parts = token.split('.');
    if parts.next()? != TOKEN_PREFIX {
        return None;
    }
    let payload = parts.next()?;
    let signature = parts.next()?;
    if parts.next().is_some() {
        return None;
    }
    let signed = format!("{TOKEN_PREFIX}.{payload}");
    let expected = hmac_sha256(secret.as_bytes(), signed.as_bytes());
    let supplied = URL_SAFE_NO_PAD.decode(signature).ok()?;
    if !constant_time_eq(&expected, &supplied) {
        return None;
    }
    let claims: CapabilityClaims = serde_json::from_slice(&URL_SAFE_NO_PAD.decode(payload).ok()?).ok()?;
    if claims.v != 1 || claims.exp < now || claims.actions.is_empty()
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

fn default_ttl_seconds() -> u64 {
    300
}

fn now_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn hmac_sha256(key: &[u8], data: &[u8]) -> [u8; 32] {
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

#[cfg(test)]
mod tests {
    use super::*;

    fn request(actions: &[&str], session_id: Option<&str>, ttl_seconds: u64) -> CapabilityMintRequest {
        CapabilityMintRequest {
            actions: actions.iter().map(|value| value.to_string()).collect(),
            session_id: session_id.map(str::to_string),
            ttl_seconds,
        }
    }

    #[test]
    fn scoped_capability_authorizes_only_requested_action_and_session() {
        let token = mint_at(
            "root-secret",
            "node_test",
            &request(&[SESSION_READ], Some("session-1"), 60),
            1_000,
        )
        .unwrap();
        assert!(authorizes_at(
            "root-secret",
            "node_test",
            &token,
            SESSION_READ,
            Some("session-1"),
            1_001,
        ));
        assert!(!authorizes_at(
            "root-secret",
            "node_test",
            &token,
            SESSION_MESSAGE,
            Some("session-1"),
            1_001,
        ));
        assert!(!authorizes_at(
            "root-secret",
            "node_test",
            &token,
            SESSION_READ,
            Some("session-2"),
            1_001,
        ));
    }

    #[test]
    fn capability_rejects_tampering_expiry_and_wrong_node() {
        let token = mint_at(
            "root-secret",
            "node_test",
            &request(&[EVIDENCE_READ], None, 60),
            1_000,
        )
        .unwrap();
        assert!(verify_at("root-secret", &token, 1_060).is_some());
        assert!(verify_at("root-secret", &token, 1_061).is_none());
        assert!(!authorizes_at(
            "root-secret",
            "node_other",
            &token,
            EVIDENCE_READ,
            None,
            1_001,
        ));
        let tampered = token.replacen("as1.", "as1.A", 1);
        assert!(verify_at("root-secret", &tampered, 1_001).is_none());
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
}
