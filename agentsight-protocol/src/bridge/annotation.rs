// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Reverse annotations: facts the client knows and the collector cannot observe.
//!
//! Everything else on the bridge flows server -> client. These rows flow the
//! other way. The client (ARO) is the side that created the resource domain,
//! wrote the limits into it, ran the policy decision and tore the domain down;
//! none of that is visible to an observer watching syscalls. `Annotation`
//! carries those facts across so the collector can show them beside its own
//! rows.
//!
//! **Read-only by contract.** An annotation is displayed and served, never acted
//! on: it does not steer capture, does not change scope registration, and never
//! feeds back into a mutation. A collector that ignored every annotation would
//! still be correct.
//!
//! **Metadata-shaped by construction.** No field here carries a raw filesystem
//! path, a command line, an argument vector or a target address. Where a raw
//! path would otherwise appear, the type carries a coarse class string instead
//! (`cgroup_path_class`, `tool_call_class`) — the same shape `path_class` has on
//! the capture rows. The client decides what to populate; the types make sure
//! that decision cannot include raw content, so annotations are unaffected by
//! [`super::DisclosureMode`] and carry no `content` struct.

use serde::{Deserialize, Serialize};

/// One annotation, bound to a scope the client already registered.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AroAnnotation {
    /// The scope this annotation is about. The server drops annotations for
    /// handles it does not know.
    pub scope_handle: String,
    /// Client-side sequence, monotone per client. Carried for idempotency and
    /// duplicate detection across a reconnect; it is *not* the server's mutation
    /// sequence and the two never interleave.
    pub sequence: u64,
    pub row: AroAnnotationRow,
}

/// The annotation payload itself.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "row", rename_all = "snake_case")]
pub enum AroAnnotationRow {
    ResourceDomain(AroResourceDomainRow),
    Enforcement(AroEnforcementRow),
    PolicyDecision(AroPolicyDecisionRow),
    Correlation(AroCorrelationRow),
}

impl AroAnnotationRow {
    /// Stable row-kind name, used as the first half of the store key.
    pub fn row_kind(&self) -> &'static str {
        match self {
            Self::ResourceDomain(_) => "resource_domain",
            Self::Enforcement(_) => "enforcement",
            Self::PolicyDecision(_) => "policy_decision",
            Self::Correlation(_) => "correlation",
        }
    }

    /// Client-assigned row id, stable across revisions of the same row.
    pub fn row_id(&self) -> &str {
        match self {
            Self::ResourceDomain(row) => &row.row_id,
            Self::Enforcement(row) => &row.row_id,
            Self::PolicyDecision(row) => &row.row_id,
            Self::Correlation(row) => &row.row_id,
        }
    }

    /// Client-assigned revision. Same rules as a mutation revision: 0 on first
    /// emit, incremented only when the row's state actually changed, so a
    /// receiver can drop anything it has already applied.
    pub fn revision(&self) -> u64 {
        match self {
            Self::ResourceDomain(row) => row.revision,
            Self::Enforcement(row) => row.revision,
            Self::PolicyDecision(row) => row.revision,
            Self::Correlation(row) => row.revision,
        }
    }

    /// The scope the row names, which the receiver checks against the
    /// annotation's own `scope_handle`.
    pub fn scope_handle(&self) -> &str {
        match self {
            Self::ResourceDomain(row) => &row.scope_handle,
            Self::Enforcement(row) => &row.scope_handle,
            Self::PolicyDecision(row) => &row.scope_handle,
            Self::Correlation(row) => &row.scope_handle,
        }
    }
}

/// The resource domain a sandbox scope was given, and the limits written into
/// it.
///
/// Metadata-only by construction: `cgroup_path_class` is a coarse class such as
/// `sandbox` or `tool`, never the cgroup path itself. The limit fields are the
/// values the client wrote, in the units the kernel interface uses.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AroResourceDomainRow {
    pub row_id: String,
    pub revision: u64,
    pub scope_handle: String,
    /// Coarse class of the domain's cgroup, never a path.
    pub cgroup_path_class: Option<String>,
    /// How the domain is contained, e.g. `cgroup_v2` or `container`.
    pub containment: Option<String>,
    /// How strongly the containment was verified, e.g. `verified` or `asserted`.
    pub assurance: Option<String>,
    pub memory_high_bytes: Option<u64>,
    pub memory_max_bytes: Option<u64>,
    /// CPU quota in parts per million of one core.
    pub cpu_quota_ppm: Option<u64>,
    pub cpu_weight: Option<u32>,
    pub pids_max: Option<u64>,
    /// Lease state of the domain, e.g. `held` or `released`.
    pub lease: Option<String>,
}

/// What enforcement actually did to a scope: what the limits achieved, what the
/// kernel did about them, and how the domain ended.
///
/// Metadata-only by construction: `tool_call_class` is a coarse class such as
/// `shell` or `network`, never a command line.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AroEnforcementRow {
    pub row_id: String,
    pub revision: u64,
    pub scope_handle: String,
    /// Coarse class of the tool call this enforcement covered.
    pub tool_call_class: Option<String>,
    /// Whether the client read the limits back and confirmed them.
    pub verified: bool,
    /// What the domain achieved against its limits, e.g. `within_limits`.
    pub achieved: Option<String>,
    pub throttle_ms: Option<u64>,
    pub frozen_ms: Option<u64>,
    pub oom_kills: Option<u32>,
    /// How the domain ended, e.g. `completed`, `killed`, `timeout`.
    pub termination: Option<String>,
    /// Whether teardown was confirmed rather than assumed.
    pub cleanup_verified: Option<bool>,
}

/// One policy decision the client made about a scope.
///
/// Metadata-only by construction: the decision is named, never the input that
/// produced it.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AroPolicyDecisionRow {
    pub row_id: String,
    pub revision: u64,
    pub scope_handle: String,
    /// The decision itself, e.g. `allow`, `deny`, `throttle`.
    pub decision: String,
    /// The mode the engine was running in, e.g. `enforce` or `observe`.
    pub mode: Option<String>,
    /// What the decision led to, e.g. `applied` or `not_applied`.
    pub outcome: Option<String>,
    /// The escalation rung the decision sat on.
    pub rung: Option<String>,
}

/// A correlation the client drew between a scope and a row in its own store.
///
/// Metadata-only by construction: the external row is named by kind and id, and
/// the id is the client's own — the collector never dereferences it.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AroCorrelationRow {
    pub row_id: String,
    pub revision: u64,
    pub scope_handle: String,
    /// The client-side row kind this correlates to.
    pub external_row_kind: String,
    /// The client-side row id, opaque to the collector.
    pub external_row_id: String,
    /// How the correlation was established, e.g. `cgroup_id` or `pid_start`.
    pub basis: String,
    /// Client-assigned confidence in the correlation, 0.0 to 1.0.
    pub confidence: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn resource_domain() -> AroAnnotationRow {
        AroAnnotationRow::ResourceDomain(AroResourceDomainRow {
            row_id: "domain-1".to_string(),
            revision: 3,
            scope_handle: "scope-1".to_string(),
            cgroup_path_class: Some("sandbox".to_string()),
            containment: Some("cgroup_v2".to_string()),
            assurance: Some("verified".to_string()),
            memory_high_bytes: Some(1024),
            memory_max_bytes: None,
            cpu_quota_ppm: None,
            cpu_weight: None,
            pids_max: None,
            lease: None,
        })
    }

    #[test]
    fn row_is_adjacently_tagged_by_kind_and_row() {
        let json = serde_json::to_value(resource_domain()).unwrap();
        assert_eq!(json["kind"], "resource_domain");
        assert_eq!(json["row"]["row_id"], "domain-1");
    }

    #[test]
    fn accessors_read_through_to_the_wrapped_row() {
        let row = resource_domain();
        assert_eq!(row.row_kind(), "resource_domain");
        assert_eq!(row.row_id(), "domain-1");
        assert_eq!(row.revision(), 3);
        assert_eq!(row.scope_handle(), "scope-1");
    }

    #[test]
    fn every_kind_tag_is_the_documented_snake_case_name() {
        let kinds = [
            AroAnnotationRow::Enforcement(AroEnforcementRow {
                row_id: "e-1".to_string(),
                revision: 0,
                scope_handle: "scope-1".to_string(),
                tool_call_class: None,
                verified: true,
                achieved: None,
                throttle_ms: None,
                frozen_ms: None,
                oom_kills: None,
                termination: None,
                cleanup_verified: None,
            }),
            AroAnnotationRow::PolicyDecision(AroPolicyDecisionRow {
                row_id: "p-1".to_string(),
                revision: 0,
                scope_handle: "scope-1".to_string(),
                decision: "allow".to_string(),
                mode: None,
                outcome: None,
                rung: None,
            }),
            AroAnnotationRow::Correlation(AroCorrelationRow {
                row_id: "c-1".to_string(),
                revision: 0,
                scope_handle: "scope-1".to_string(),
                external_row_kind: "resource_sample".to_string(),
                external_row_id: "sample-1".to_string(),
                basis: "cgroup_id".to_string(),
                confidence: 0.75,
            }),
        ];
        let tags = kinds
            .iter()
            .map(|row| serde_json::to_value(row).unwrap()["kind"].clone())
            .collect::<Vec<_>>();
        assert_eq!(
            tags,
            vec!["enforcement", "policy_decision", "correlation"]
                .into_iter()
                .map(serde_json::Value::from)
                .collect::<Vec<_>>()
        );
    }
}
