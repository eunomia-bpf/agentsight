// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Handshake, capability, scope, and health types for bridge protocol v1.

use serde::{Deserialize, Serialize};

/// Opening message from the connecting client.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeHello {
    /// Protocol versions the client can speak, most preferred first.
    pub supported_versions: Vec<u32>,
    pub product: String,
    pub product_version: String,
    /// Client-side frame ceiling; the server negotiates down, never up.
    pub max_frame_bytes: u32,
    /// How much of each row the client is allowed to receive.
    pub disclosure: DisclosureMode,
}

/// Server reply to an accepted hello.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeAgreement {
    pub protocol_version: u32,
    pub product: String,
    pub product_version: String,
    pub build_commit: Option<String>,
    pub binary_digest: Option<String>,
    /// Stable identity of the collector host; sequences are monotone per
    /// (node_id, boot_id).
    pub node_id: String,
    pub boot_id: Option<String>,
    pub capabilities: Vec<BridgeCapability>,
    pub max_frame_bytes: u32,
}

/// One named capture capability and whether it is actually available here.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeCapability {
    pub name: String,
    pub available: bool,
    pub detail: Option<String>,
}

impl BridgeCapability {
    pub fn new(name: impl Into<String>, available: bool, detail: Option<String>) -> Self {
        Self {
            name: name.into(),
            available,
            detail,
        }
    }
}

/// The capability names defined by bridge protocol v1.
pub mod capability_names {
    pub const PROCESS_CAPTURE: &str = "process_capture";
    pub const FILE_CAPTURE: &str = "file_capture";
    pub const NETWORK_CAPTURE: &str = "network_capture";
    pub const TLS_CAPTURE: &str = "tls_capture";
    pub const AGENT_NATIVE_SESSIONS: &str = "agent_native_sessions";
    pub const RESOURCE_SAMPLES: &str = "resource_samples";
    pub const CGROUP_FILTER: &str = "cgroup_filter";
    pub const SESSION_MUTATIONS: &str = "session_mutations";

    /// Every capability name in v1, in the order the spec lists them.
    pub const ALL: [&str; 8] = [
        PROCESS_CAPTURE,
        FILE_CAPTURE,
        NETWORK_CAPTURE,
        TLS_CAPTURE,
        AGENT_NATIVE_SESSIONS,
        RESOURCE_SAMPLES,
        CGROUP_FILTER,
        SESSION_MUTATIONS,
    ];
}

/// Periodic server health, also sent on request.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BridgeHealth {
    /// `ok` | `degraded` | `failing`.
    pub state: String,
    pub detail: Option<String>,
    pub capture_gaps: u64,
    pub dropped_mutations: u64,
    pub active_scopes: u32,
}

impl BridgeHealth {
    pub const OK: &'static str = "ok";
    pub const DEGRADED: &'static str = "degraded";
    pub const FAILING: &'static str = "failing";
}

/// How much of a row the receiver is entitled to see. Metadata-only is the
/// default and the only mode in which raw content fields stay unpopulated.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(tag = "mode", rename_all = "snake_case")]
pub enum DisclosureMode {
    /// The default everywhere: no raw content leaves the collector.
    #[default]
    MetadataOnly,
    ResearchFull,
    IncidentScoped {
        approval_id: String,
        /// Content field names the approval covers, e.g. `cwd`, `host`.
        field_allowlist: Vec<String>,
        expires_at_ms: u64,
    },
}

impl DisclosureMode {
    /// Whether a named content field may be populated under this mode.
    pub fn allows_content_field(&self, field: &str) -> bool {
        match self {
            Self::MetadataOnly => false,
            Self::ResearchFull => true,
            Self::IncidentScoped {
                field_allowlist, ..
            } => field_allowlist.iter().any(|allowed| allowed == field),
        }
    }

    /// Whether any content at all may be populated under this mode.
    pub fn allows_any_content(&self) -> bool {
        match self {
            Self::MetadataOnly => false,
            Self::ResearchFull => true,
            Self::IncidentScoped {
                field_allowlist, ..
            } => !field_allowlist.is_empty(),
        }
    }
}

/// A sandbox scope the client asks the server to observe. Deliberately carries
/// no tenant/run/task identifiers: the client keeps that mapping locally.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScopeRegistration {
    /// Opaque, client-generated handle.
    pub scope_handle: String,
    pub root_pid: Option<u32>,
    pub root_start_ticks: Option<u64>,
    pub sandbox_cgroup_path: Option<String>,
    pub sandbox_cgroup_id: Option<u64>,
    pub starts_monotonic_ns: Option<u64>,
    pub expires_monotonic_ns: Option<u64>,
    pub disclosure: DisclosureMode,
    pub required_capabilities: Vec<String>,
}

/// A tool-invocation scope nested inside an already-registered sandbox scope.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ToolScopeRegistration {
    pub parent_scope_handle: String,
    pub tool_scope_handle: String,
    pub tool_cgroup_path: Option<String>,
    pub tool_cgroup_id: Option<u64>,
    pub pid: Option<u32>,
    pub start_ticks: Option<u64>,
    pub starts_monotonic_ns: Option<u64>,
    pub expires_monotonic_ns: Option<u64>,
}

/// Reconnect request: continue the stream after `after_sequence`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResumeRequest {
    pub node_id: String,
    pub boot_id: Option<String>,
    pub after_sequence: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disclosure_mode_is_internally_tagged() {
        let json = serde_json::to_value(DisclosureMode::MetadataOnly).unwrap();
        assert_eq!(json, serde_json::json!({ "mode": "metadata_only" }));

        let scoped = DisclosureMode::IncidentScoped {
            approval_id: "ap-1".to_string(),
            field_allowlist: vec!["cwd".to_string()],
            expires_at_ms: 10,
        };
        let json = serde_json::to_value(&scoped).unwrap();
        assert_eq!(json["mode"], "incident_scoped");
        assert_eq!(json["approval_id"], "ap-1");
    }

    #[test]
    fn incident_scope_only_allows_listed_fields() {
        let scoped = DisclosureMode::IncidentScoped {
            approval_id: "ap-1".to_string(),
            field_allowlist: vec!["cwd".to_string()],
            expires_at_ms: 10,
        };
        assert!(scoped.allows_content_field("cwd"));
        assert!(!scoped.allows_content_field("request"));
        assert!(scoped.allows_any_content());
        assert!(!DisclosureMode::MetadataOnly.allows_content_field("cwd"));
        assert!(DisclosureMode::ResearchFull.allows_content_field("request"));
    }
}
