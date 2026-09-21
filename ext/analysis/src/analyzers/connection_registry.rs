// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
use std::collections::HashMap;
use uuid::Uuid;

const CONNECTION_IDLE_TIMEOUT_MS: u64 = 10 * 60 * 1_000;
const CONNECTION_SWEEP_INTERVAL_MS: u64 = 30 * 1_000;
const MAX_ACTIVE_CONNECTIONS: usize = 1_024;

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ConnectionIdentity {
    pub id: String,
    pub generation: u32,
    pub exact: bool,
    pub pid: u32,
    pub comm: String,
}

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
struct TransportKey {
    pid: u32,
    process_start_ns: u64,
    tls_library: String,
    transport_handle: String,
}

#[derive(Debug, Clone)]
struct ActiveConnection {
    identity: ConnectionIdentity,
    last_seen: u64,
}

/// Resolves process-local TLS object addresses into opaque capture-local IDs.
///
/// The raw pointer never becomes part of the public connection ID. A close
/// lifecycle event, or an idle gap, advances the generation before an address
/// can be reused.
pub(crate) struct ConnectionRegistry {
    capture_session_id: String,
    active: HashMap<TransportKey, ActiveConnection>,
    generations: HashMap<TransportKey, u32>,
    next_connection: u64,
    retired: Vec<(ConnectionIdentity, &'static str)>,
    last_sweep_ms: u64,
}

impl Default for ConnectionRegistry {
    fn default() -> Self {
        Self {
            capture_session_id: Uuid::new_v4().simple().to_string(),
            active: HashMap::new(),
            generations: HashMap::new(),
            next_connection: 0,
            retired: Vec::new(),
            last_sweep_ms: 0,
        }
    }
}

impl ConnectionRegistry {
    pub(crate) fn resolve(&mut self, event: &Event) -> ConnectionIdentity {
        let Some(key) = transport_key(event) else {
            let tid = event
                .data
                .get("tid")
                .and_then(|value| value.as_u64())
                .unwrap_or(0);
            return ConnectionIdentity {
                id: format!("legacy-{}-{tid}", event.pid),
                generation: 0,
                exact: false,
                pid: event.pid,
                comm: event.comm.clone(),
            };
        };

        let expired = self.active.get(&key).is_some_and(|connection| {
            event.timestamp.saturating_sub(connection.last_seen) > CONNECTION_IDLE_TIMEOUT_MS
        });
        if expired {
            if let Some(identity) = self.retire(&key) {
                self.retired.push((identity, "timeout"));
            }
        }

        if event.timestamp.saturating_sub(self.last_sweep_ms) >= CONNECTION_SWEEP_INTERVAL_MS {
            let expired_keys = self
                .active
                .iter()
                .filter(|(_, connection)| {
                    event.timestamp.saturating_sub(connection.last_seen)
                        > CONNECTION_IDLE_TIMEOUT_MS
                })
                .map(|(key, _)| key.clone())
                .collect::<Vec<_>>();
            for expired_key in expired_keys {
                if let Some(identity) = self.retire(&expired_key) {
                    self.retired.push((identity, "timeout"));
                }
            }
            self.last_sweep_ms = event.timestamp;
        }

        if let Some(connection) = self.active.get_mut(&key) {
            connection.last_seen = event.timestamp;
            return connection.identity.clone();
        }

        let generation = *self.generations.entry(key.clone()).or_insert(0);
        self.next_connection = self.next_connection.saturating_add(1);
        let identity = ConnectionIdentity {
            id: format!(
                "conn-{}-{}-g{}",
                self.capture_session_id, self.next_connection, generation
            ),
            generation,
            exact: true,
            pid: event.pid,
            comm: event.comm.clone(),
        };
        self.active.insert(
            key.clone(),
            ActiveConnection {
                identity: identity.clone(),
                last_seen: event.timestamp,
            },
        );
        while self.active.len() > MAX_ACTIVE_CONNECTIONS {
            let oldest = self
                .active
                .iter()
                .filter(|(candidate, _)| *candidate != &key)
                .min_by_key(|(_, connection)| connection.last_seen)
                .map(|(candidate, _)| candidate.clone());
            let Some(oldest) = oldest else {
                break;
            };
            if let Some(identity) = self.retire(&oldest) {
                self.retired.push((identity, "evicted"));
            }
        }
        identity
    }

    pub(crate) fn close(&mut self, event: &Event) -> Option<ConnectionIdentity> {
        let key = transport_key(event)?;
        if self.active.contains_key(&key) {
            self.retire(&key)
        } else {
            None
        }
    }

    pub(crate) fn take_retired(&mut self) -> Vec<(ConnectionIdentity, &'static str)> {
        std::mem::take(&mut self.retired)
    }

    pub(crate) fn active_identities(&self) -> Vec<ConnectionIdentity> {
        self.active
            .values()
            .map(|connection| connection.identity.clone())
            .collect()
    }

    fn retire(&mut self, key: &TransportKey) -> Option<ConnectionIdentity> {
        let identity = self
            .active
            .remove(key)
            .map(|connection| connection.identity);
        let generation = self.generations.entry(key.clone()).or_insert(0);
        *generation = generation.saturating_add(1);
        // Retained generations are only a diagnostic. The session-wide monotonic
        // connection number keeps IDs unique even after a tombstone is evicted.
        if self.generations.len() > MAX_ACTIVE_CONNECTIONS * 2 {
            let victim = self
                .generations
                .keys()
                .find(|candidate| *candidate != key && !self.active.contains_key(*candidate))
                .cloned();
            if let Some(victim) = victim {
                self.generations.remove(&victim);
            }
        }
        identity
    }
}

#[cfg(test)]
fn has_transport_handle(event: &Event) -> bool {
    normalized_transport_handle(event).is_some()
}

pub(crate) fn has_transport_identity(event: &Event) -> bool {
    transport_key(event).is_some()
}

fn normalized_transport_handle(event: &Event) -> Option<String> {
    let handle = event.data.get("transport_handle")?;
    let numeric = match handle {
        serde_json::Value::String(value) if !value.is_empty() => {
            let parsed = value
                .strip_prefix("0x")
                .or_else(|| value.strip_prefix("0X"))
                .map(|hex| u64::from_str_radix(hex, 16))
                .unwrap_or_else(|| value.parse());
            match parsed {
                Ok(number) => number,
                Err(_) => return Some(value.clone()),
            }
        }
        serde_json::Value::Number(value) => value.as_u64()?,
        _ => return None,
    };
    (numeric != 0).then(|| format!("0x{numeric:x}"))
}

fn transport_key(event: &Event) -> Option<TransportKey> {
    let transport_handle = normalized_transport_handle(event)?;
    let tls_library = event
        .data
        .get("tls_library")
        .and_then(|value| value.as_str())
        .filter(|library| !library.is_empty() && *library != "unknown")?
        .to_string();
    Some(TransportKey {
        pid: event.pid,
        process_start_ns: event
            .data
            .get("process_start_ns")
            .and_then(|value| value.as_u64())
            .filter(|start| *start != 0)?,
        tls_library,
        transport_handle,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn event(timestamp: u64, tid: u64, handle: Option<&str>) -> Event {
        Event::new_with_timestamp(
            timestamp,
            "ssl".to_string(),
            42,
            "agent".to_string(),
            json!({
                "tid": tid,
                "transport_handle": handle,
                "process_start_ns": 12345,
                "tls_library": "openssl"
            }),
        )
    }

    #[test]
    fn follows_handle_across_threads_and_separates_handles() {
        let mut registry = ConnectionRegistry::default();
        let first = registry.resolve(&event(1, 10, Some("0x100")));
        let other_thread = registry.resolve(&event(2, 11, Some("0x100")));
        let other_handle = registry.resolve(&event(3, 10, Some("0x200")));

        assert_eq!(first, other_thread);
        assert_ne!(first.id, other_handle.id);
        assert!(first.exact);
    }

    #[test]
    fn close_advances_generation_before_address_reuse() {
        let mut registry = ConnectionRegistry::default();
        let first_event = event(1, 10, Some("0x100"));
        let first = registry.resolve(&first_event);
        registry.close(&first_event);
        let reused = registry.resolve(&event(2, 11, Some("0x100")));

        assert_ne!(first.id, reused.id);
        assert_eq!(reused.generation, 1);
    }

    #[test]
    fn idle_timeout_advances_generation_before_address_reuse() {
        let mut registry = ConnectionRegistry::default();
        let first = registry.resolve(&event(1, 10, Some("0x100")));
        let reused = registry.resolve(&event(CONNECTION_IDLE_TIMEOUT_MS + 2, 11, Some("0x100")));

        assert_ne!(first.id, reused.id);
        assert_eq!(reused.generation, 1);
    }

    #[test]
    fn sweep_reports_unrelated_idle_connections() {
        let mut registry = ConnectionRegistry::default();
        let first = registry.resolve(&event(1, 10, Some("0x100")));
        registry.resolve(&event(CONNECTION_IDLE_TIMEOUT_MS + 2, 11, Some("0x200")));

        let retired = registry.take_retired();
        assert_eq!(retired, vec![(first, "timeout")]);
    }

    #[test]
    fn missing_handle_uses_legacy_thread_key() {
        let mut registry = ConnectionRegistry::default();
        let identity = registry.resolve(&event(1, 10, None));
        assert_eq!(identity.id, "legacy-42-10");
        assert!(!identity.exact);
    }

    #[test]
    fn zero_handles_are_not_transport_identity() {
        let string_zero = event(1, 10, Some("0x0"));
        assert!(!has_transport_handle(&string_zero));
        assert!(!ConnectionRegistry::default().resolve(&string_zero).exact);

        let mut numeric_zero = event(2, 11, None);
        numeric_zero.data["transport_handle"] = serde_json::json!(0);
        assert!(!has_transport_handle(&numeric_zero));
        assert!(!ConnectionRegistry::default().resolve(&numeric_zero).exact);
    }

    #[test]
    fn pid_reuse_is_separated_by_process_start_time() {
        let mut registry = ConnectionRegistry::default();
        let mut first_event = event(1, 10, Some("0x100"));
        first_event.data["process_start_ns"] = serde_json::json!(100);
        let mut reused_pid_event = event(2, 11, Some("0x100"));
        reused_pid_event.data["process_start_ns"] = serde_json::json!(200);

        let first = registry.resolve(&first_event);
        let reused = registry.resolve(&reused_pid_event);
        assert_ne!(first.id, reused.id);
    }

    #[test]
    fn unknown_identity_is_legacy_and_numeric_handles_are_normalized() {
        let mut registry = ConnectionRegistry::default();
        let known = event(1, 10, Some("0x0100"));
        let mut numeric = known.clone();
        numeric.data["transport_handle"] = json!(256);
        assert_eq!(registry.resolve(&known), registry.resolve(&numeric));
        numeric.data["process_start_ns"] = json!(0);
        assert!(!registry.resolve(&numeric).exact);
        numeric.data["process_start_ns"] = json!(12345);
        numeric.data["tls_library"] = json!("unknown");
        assert!(!registry.resolve(&numeric).exact);
    }
}
