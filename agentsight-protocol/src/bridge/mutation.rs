// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Mutation envelopes: the streaming half of bridge protocol v1.

use super::rows::{
    BridgeAuditEventRow, BridgeLlmCallRow, BridgeNetworkTargetRow, BridgeProcessNodeRow,
    BridgeResourceSampleRow, BridgeSessionRow, BridgeTokenUsageRow, BridgeToolCallRow,
};
use serde::{Deserialize, Serialize};

/// What the receiver should do with the row in the envelope.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MutationOperation {
    Insert,
    Update,
    Delete,
    /// Replayed state, not an original observation: ordering is synthetic.
    SnapshotReconstruction,
}

/// What the envelope's timestamps mean. Never guessed: `Unknown` is a real
/// answer when the source clock could not be characterized.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TimestampBasis {
    BootMonotonic,
    EpochMilliseconds,
    AgentNativeTimestamp,
    DerivedFromBootOffset,
    Unknown,
}

/// One mutation with everything the receiver needs to place it in time and
/// attribute it to a source.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ViewMutationEnvelope {
    pub protocol_version: u32,
    pub node_id: String,
    pub boot_id: Option<String>,
    /// Monotonically increasing from 1 per (node_id, boot).
    pub sequence: u64,
    pub observed_wall_ms: Option<u64>,
    pub observed_monotonic_ns: Option<u64>,
    pub basis: TimestampBasis,
    pub source_component: String,
    pub source_version: String,
    /// Set when the server could attribute the mutation to exactly one scope.
    pub scope_handle: Option<String>,
    pub operation: MutationOperation,
    pub mutation: ViewMutation,
}

/// The materialized-view change itself.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "row", rename_all = "snake_case")]
pub enum ViewMutation {
    SessionUpsert(BridgeSessionRow),
    LlmCallUpsert(BridgeLlmCallRow),
    TokenUsageUpsert(BridgeTokenUsageRow),
    ToolCallUpsert(BridgeToolCallRow),
    ProcessNodeUpsert(BridgeProcessNodeRow),
    AuditEventInserted(BridgeAuditEventRow),
    NetworkTargetUpsert(BridgeNetworkTargetRow),
    ResourceSampleInserted(BridgeResourceSampleRow),
    CaptureCapabilityChanged {
        capability: String,
        available: bool,
        detail: Option<String>,
    },
    CaptureGapObserved {
        from_sequence: u64,
        to_sequence: u64,
        reason: String,
    },
    RowEvicted {
        row_kind: String,
        row_id: String,
    },
}

impl ViewMutation {
    /// Stable row-kind name used for revision bookkeeping and eviction notices.
    pub fn row_kind(&self) -> &'static str {
        match self {
            Self::SessionUpsert(_) => "session",
            Self::LlmCallUpsert(_) => "llm_call",
            Self::TokenUsageUpsert(_) => "token_usage",
            Self::ToolCallUpsert(_) => "tool_call",
            Self::ProcessNodeUpsert(_) => "process_node",
            Self::AuditEventInserted(_) => "audit_event",
            Self::NetworkTargetUpsert(_) => "network_target",
            Self::ResourceSampleInserted(_) => "resource_sample",
            Self::CaptureCapabilityChanged { .. } => "capture_capability",
            Self::CaptureGapObserved { .. } => "capture_gap",
            Self::RowEvicted { .. } => "row_evicted",
        }
    }

    /// Source row id, when the mutation carries an identifiable row.
    pub fn row_id(&self) -> Option<&str> {
        match self {
            Self::SessionUpsert(row) => Some(&row.row_id),
            Self::LlmCallUpsert(row) => Some(&row.row_id),
            Self::TokenUsageUpsert(row) => Some(&row.row_id),
            Self::ToolCallUpsert(row) => Some(&row.row_id),
            Self::ProcessNodeUpsert(row) => Some(&row.row_id),
            Self::AuditEventInserted(row) => Some(&row.row_id),
            Self::NetworkTargetUpsert(row) => Some(&row.row_id),
            Self::RowEvicted { row_id, .. } => Some(row_id),
            Self::ResourceSampleInserted(_)
            | Self::CaptureCapabilityChanged { .. }
            | Self::CaptureGapObserved { .. } => None,
        }
    }

    /// Whether the mutation describes process/file/network activity that the
    /// server may auto-tag with a single active scope.
    pub fn is_scope_taggable(&self) -> bool {
        matches!(
            self,
            Self::ProcessNodeUpsert(_)
                | Self::AuditEventInserted(_)
                | Self::NetworkTargetUpsert(_)
                | Self::ResourceSampleInserted(_)
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mutation_is_adjacently_tagged_by_kind_and_row() {
        let mutation = ViewMutation::RowEvicted {
            row_kind: "audit_event".to_string(),
            row_id: "audit-1".to_string(),
        };
        let json = serde_json::to_value(&mutation).unwrap();
        assert_eq!(json["kind"], "row_evicted");
        assert_eq!(json["row"]["row_id"], "audit-1");
    }

    #[test]
    fn operation_and_basis_serialize_as_snake_case_strings() {
        assert_eq!(
            serde_json::to_value(MutationOperation::SnapshotReconstruction).unwrap(),
            serde_json::json!("snapshot_reconstruction")
        );
        assert_eq!(
            serde_json::to_value(TimestampBasis::DerivedFromBootOffset).unwrap(),
            serde_json::json!("derived_from_boot_offset")
        );
    }
}
