// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Bridge protocol v1: the wire contract between an AgentSight collector
//! (server, listens on a Unix socket) and an external evidence consumer
//! (client, connects). The contract is transport-independent: this module only
//! defines the message types and the length-prefixed CBOR frame codec.
//!
//! Both sides of the bridge implement these types independently, so the field
//! names and serde attributes below are the compatibility contract. Golden
//! vectors in `tests/fixtures/bridge-v1/` pin the encoding byte-for-byte.

mod codec;
mod mutation;
mod rows;
mod types;

pub use codec::{BridgeCodecError, decode_body, encode_body, encode_frame, read_frame};
pub use mutation::{MutationOperation, TimestampBasis, ViewMutation, ViewMutationEnvelope};
pub use rows::{
    AuditContent, BridgeAuditEventRow, BridgeLlmCallRow, BridgeNetworkTargetRow,
    BridgeProcessNodeRow, BridgeResourceSampleRow, BridgeSessionRow, BridgeTokenUsageRow,
    BridgeToolCallRow, LlmContent, NetworkContent, ProcessContent, SessionContent, ToolContent,
};
pub use types::{
    BridgeAgreement, BridgeCapability, BridgeHealth, BridgeHello, DisclosureMode, ResumeRequest,
    ScopeRegistration, ToolScopeRegistration, capability_names,
};

use serde::{Deserialize, Serialize};

/// Bridge wire protocol version. Independent of [`crate::PROTOCOL_VERSION`],
/// which versions the HTTP Node API.
pub const BRIDGE_PROTOCOL_VERSION: u32 = 1;

/// Default maximum frame size (1 MiB). Negotiable downward via hello.
pub const MAX_FRAME_BYTES: u32 = 1_048_576;

/// Every message that can cross the bridge, in either direction.
///
/// The variant sizes are uneven because the wire contract fixes them; boxing
/// the mutation payload would change the Rust shape both implementations must
/// agree on for no encoding benefit.
#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "msg", content = "data", rename_all = "snake_case")]
pub enum BridgeMessage {
    /// client -> server: opening handshake.
    Hello(BridgeHello),
    /// server -> client: accepted handshake with negotiated terms.
    Agreement(BridgeAgreement),
    /// server -> client: handshake refused; the connection closes after this.
    HelloRejected { reason: String },
    /// client -> server: register a sandbox scope.
    RegisterScope(ScopeRegistration),
    /// client -> server: register a tool scope nested in a sandbox scope.
    RegisterToolScope(ToolScopeRegistration),
    /// server -> client: scope registered, with the capabilities it really got.
    ScopeAccepted {
        scope_handle: String,
        effective: Vec<BridgeCapability>,
    },
    /// server -> client: scope refused.
    ScopeRejected {
        scope_handle: String,
        reason: String,
    },
    /// client -> server: drop a scope registration.
    UnregisterScope { scope_handle: String },
    /// server -> client: scope dropped, with the last sequence flushed for it.
    ScopeUnregistered {
        scope_handle: String,
        flushed_through: Option<u64>,
    },
    /// server -> client: one materialized-view mutation.
    Mutation(ViewMutationEnvelope),
    /// client -> server: mutations up to and including this sequence are durable.
    Ack { through_sequence: u64 },
    /// client -> server: resume a previous stream after a reconnect.
    Resume(ResumeRequest),
    /// server -> client: the requested resume point fell out of the replay buffer.
    ResumeUnavailable { earliest_available: Option<u64> },
    /// client -> server: ask for a full reconstruction of current state.
    SnapshotRequest { scope_handle: Option<String> },
    /// server -> client: snapshot stream starts.
    SnapshotBegin { estimated: u64, reconstructed: bool },
    /// server -> client: snapshot stream ends.
    SnapshotEnd { through_sequence: u64 },
    /// server -> client: periodic and on-request health.
    Health(BridgeHealth),
    /// both directions: liveness probe.
    Heartbeat { monotonic_ns: u64 },
    /// either direction: orderly shutdown notice.
    Shutdown { reason: String },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hello_round_trips_through_cbor() {
        let message = BridgeMessage::Hello(BridgeHello {
            supported_versions: vec![BRIDGE_PROTOCOL_VERSION],
            product: "aro".to_string(),
            product_version: "0.1.0".to_string(),
            max_frame_bytes: MAX_FRAME_BYTES,
            disclosure: DisclosureMode::MetadataOnly,
        });
        let bytes = encode_body(&message).unwrap();
        assert_eq!(decode_body(&bytes).unwrap(), message);
    }

    #[test]
    fn message_tag_is_the_documented_snake_case_name() {
        let message = BridgeMessage::HelloRejected {
            reason: "version".to_string(),
        };
        let json = serde_json::to_value(&message).unwrap();
        assert_eq!(json["msg"], "hello_rejected");
        assert_eq!(json["data"]["reason"], "version");
    }

    #[test]
    fn unknown_message_tag_is_rejected() {
        let json = serde_json::json!({ "msg": "teleport", "data": {} });
        let error = serde_json::from_value::<BridgeMessage>(json).unwrap_err();
        assert!(error.to_string().contains("teleport"), "{error}");
    }
}
