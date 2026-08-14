// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! The receiving half of the reverse-annotation stream.
//!
//! [`AnnotationStore`] holds what an external client told the collector about
//! its own scopes. It is a pure sink: nothing here steers capture, and the rows
//! are only ever read back out for display. Everything a client sends is
//! metadata-shaped by construction (see
//! [`agentsight_protocol::bridge::AroAnnotation`]), so the store applies no
//! disclosure filtering of its own.
//!
//! Two properties matter, because the client may reconnect and replay:
//!
//! * **Idempotent.** A row is keyed by `(kind, row_id)` and carries a
//!   client-assigned revision, exactly as bridge mutations do. A revision the
//!   store has already applied — or one older than it — is a no-op, so replaying
//!   a stream leaves the store where it was.
//! * **Bounded.** A remote peer decides how much to send, so the store is
//!   capped. When it overflows, the oldest row is dropped and counted: a
//!   truncated view that says so beats an unbounded one that does not.

use agentsight_protocol::bridge::AroAnnotation;
use std::collections::{BTreeMap, VecDeque};

/// Rows kept before the oldest is evicted.
pub const DEFAULT_MAX_ANNOTATION_ROWS: usize = 4096;

/// `(row_kind, row_id)` — the identity a client revises against.
type AnnotationKey = (String, String);

/// Bounded, revision-idempotent store of client annotations.
#[derive(Debug, Clone)]
pub struct AnnotationStore {
    /// Ordered by kind then row id, so readers get rows grouped per kind.
    rows: BTreeMap<AnnotationKey, AroAnnotation>,
    /// First-insert order, which is the order eviction consumes. A revision of
    /// an existing row does not move it: "oldest" means oldest known, not least
    /// recently updated.
    order: VecDeque<AnnotationKey>,
    max_rows: usize,
    evicted: u64,
    ignored: u64,
}

impl Default for AnnotationStore {
    fn default() -> Self {
        Self::new()
    }
}

impl AnnotationStore {
    /// A store bounded at [`DEFAULT_MAX_ANNOTATION_ROWS`].
    pub fn new() -> Self {
        Self::with_max_rows(DEFAULT_MAX_ANNOTATION_ROWS)
    }

    pub fn with_max_rows(max_rows: usize) -> Self {
        Self {
            rows: BTreeMap::new(),
            order: VecDeque::new(),
            max_rows,
            evicted: 0,
            ignored: 0,
        }
    }

    /// Apply one annotation. Returns whether it changed the store: a duplicate
    /// or stale revision is a no-op and returns `false`.
    pub fn upsert(&mut self, annotation: &AroAnnotation) -> bool {
        let key = (
            annotation.row.row_kind().to_string(),
            annotation.row.row_id().to_string(),
        );
        if let Some(existing) = self.rows.get(&key)
            && annotation.row.revision() <= existing.row.revision()
        {
            self.ignored += 1;
            return false;
        }
        if self.rows.insert(key.clone(), annotation.clone()).is_none() {
            self.order.push_back(key);
        }
        self.evict_overflow();
        true
    }

    fn evict_overflow(&mut self) {
        while self.rows.len() > self.max_rows {
            let Some(oldest) = self.order.pop_front() else {
                break;
            };
            if self.rows.remove(&oldest).is_some() {
                self.evicted += 1;
            }
        }
    }

    /// Every stored row, grouped by kind and then by row id.
    pub fn rows(&self) -> impl Iterator<Item = &AroAnnotation> {
        self.rows.values()
    }

    pub fn get(&self, row_kind: &str, row_id: &str) -> Option<&AroAnnotation> {
        self.rows.get(&(row_kind.to_string(), row_id.to_string()))
    }

    pub fn len(&self) -> usize {
        self.rows.len()
    }

    pub fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }

    /// Rows dropped to stay inside the bound. Non-zero means the served view is
    /// incomplete.
    pub fn evicted(&self) -> u64 {
        self.evicted
    }

    /// Annotations discarded as duplicate or stale revisions.
    pub fn ignored(&self) -> u64 {
        self.ignored
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use agentsight_protocol::bridge::{
        AroAnnotationRow, AroCorrelationRow, AroEnforcementRow, AroPolicyDecisionRow,
        AroResourceDomainRow,
    };

    fn domain(row_id: &str, revision: u64, lease: Option<&str>) -> AroAnnotation {
        AroAnnotation {
            scope_handle: "scope-1".to_string(),
            sequence: revision + 1,
            row: AroAnnotationRow::ResourceDomain(AroResourceDomainRow {
                row_id: row_id.to_string(),
                revision,
                scope_handle: "scope-1".to_string(),
                cgroup_path_class: Some("sandbox".to_string()),
                containment: Some("cgroup_v2".to_string()),
                assurance: Some("verified".to_string()),
                memory_high_bytes: Some(512 * 1024 * 1024),
                memory_max_bytes: Some(1024 * 1024 * 1024),
                cpu_quota_ppm: Some(500_000),
                cpu_weight: Some(100),
                pids_max: Some(256),
                lease: lease.map(str::to_string),
            }),
        }
    }

    fn enforcement(row_id: &str, revision: u64) -> AroAnnotation {
        AroAnnotation {
            scope_handle: "scope-1".to_string(),
            sequence: 100 + revision,
            row: AroAnnotationRow::Enforcement(AroEnforcementRow {
                row_id: row_id.to_string(),
                revision,
                scope_handle: "scope-1".to_string(),
                tool_call_class: Some("shell".to_string()),
                verified: true,
                achieved: Some("within_limits".to_string()),
                throttle_ms: Some(0),
                frozen_ms: None,
                oom_kills: Some(0),
                termination: Some("completed".to_string()),
                cleanup_verified: Some(true),
            }),
        }
    }

    fn policy(row_id: &str, revision: u64) -> AroAnnotation {
        AroAnnotation {
            scope_handle: "scope-1".to_string(),
            sequence: 200 + revision,
            row: AroAnnotationRow::PolicyDecision(AroPolicyDecisionRow {
                row_id: row_id.to_string(),
                revision,
                scope_handle: "scope-1".to_string(),
                decision: "allow".to_string(),
                mode: Some("enforce".to_string()),
                outcome: Some("applied".to_string()),
                rung: Some("rung-1".to_string()),
            }),
        }
    }

    fn correlation(row_id: &str, revision: u64) -> AroAnnotation {
        AroAnnotation {
            scope_handle: "scope-1".to_string(),
            sequence: 300 + revision,
            row: AroAnnotationRow::Correlation(AroCorrelationRow {
                row_id: row_id.to_string(),
                revision,
                scope_handle: "scope-1".to_string(),
                external_row_kind: "resource_sample".to_string(),
                external_row_id: "sample-1".to_string(),
                basis: "cgroup_id".to_string(),
                confidence: 0.9,
            }),
        }
    }

    fn lease_of(annotation: &AroAnnotation) -> Option<String> {
        match &annotation.row {
            AroAnnotationRow::ResourceDomain(row) => row.lease.clone(),
            other => panic!("expected a resource domain row, got {other:?}"),
        }
    }

    #[test]
    fn a_new_row_is_stored_and_a_higher_revision_replaces_it() {
        let mut store = AnnotationStore::new();
        assert!(store.upsert(&domain("domain-1", 0, Some("held"))));
        assert!(store.upsert(&domain("domain-1", 1, Some("released"))));
        assert_eq!(store.len(), 1);
        let stored = store.get("resource_domain", "domain-1").expect("stored");
        assert_eq!(stored.row.revision(), 1);
        assert_eq!(lease_of(stored).as_deref(), Some("released"));
    }

    #[test]
    fn replaying_the_same_revision_is_a_no_op() {
        let mut store = AnnotationStore::new();
        store.upsert(&domain("domain-1", 2, Some("held")));
        // Same revision, different payload: the client says nothing changed, so
        // the store must not take the new body either.
        assert!(!store.upsert(&domain("domain-1", 2, Some("released"))));
        assert!(!store.upsert(&domain("domain-1", 2, Some("released"))));
        assert_eq!(store.len(), 1);
        assert_eq!(store.ignored(), 2);
        let stored = store.get("resource_domain", "domain-1").expect("stored");
        assert_eq!(lease_of(stored).as_deref(), Some("held"));
    }

    #[test]
    fn a_stale_revision_never_overwrites_a_newer_one() {
        let mut store = AnnotationStore::new();
        store.upsert(&domain("domain-1", 5, Some("released")));
        assert!(!store.upsert(&domain("domain-1", 4, Some("held"))));
        assert!(!store.upsert(&domain("domain-1", 0, None)));
        let stored = store.get("resource_domain", "domain-1").expect("stored");
        assert_eq!(stored.row.revision(), 5);
        assert_eq!(store.ignored(), 2);
        assert_eq!(store.evicted(), 0);
    }

    #[test]
    fn overflow_drops_the_oldest_row_and_counts_it() {
        let mut store = AnnotationStore::with_max_rows(3);
        for index in 0..5 {
            store.upsert(&domain(&format!("domain-{index}"), 0, None));
        }
        assert_eq!(store.len(), 3);
        assert_eq!(store.evicted(), 2);
        assert!(store.get("resource_domain", "domain-0").is_none());
        assert!(store.get("resource_domain", "domain-1").is_none());
        assert!(store.get("resource_domain", "domain-4").is_some());
    }

    #[test]
    fn revising_a_row_does_not_make_it_newer_for_eviction() {
        let mut store = AnnotationStore::with_max_rows(2);
        store.upsert(&domain("domain-0", 0, None));
        store.upsert(&domain("domain-1", 0, None));
        store.upsert(&domain("domain-0", 1, Some("held")));
        store.upsert(&domain("domain-2", 0, None));
        // domain-0 was seen first, so it goes first even though it was revised
        // most recently.
        assert!(store.get("resource_domain", "domain-0").is_none());
        assert_eq!(store.evicted(), 1);
        assert_eq!(store.len(), 2);
    }

    #[test]
    fn the_same_row_id_in_two_kinds_is_two_rows() {
        let mut store = AnnotationStore::new();
        assert!(store.upsert(&domain("row-1", 0, None)));
        assert!(store.upsert(&enforcement("row-1", 0)));
        assert!(store.upsert(&policy("row-1", 0)));
        assert!(store.upsert(&correlation("row-1", 0)));
        assert_eq!(store.len(), 4);
        assert_eq!(store.ignored(), 0);

        // A revision in one kind leaves the others untouched.
        store.upsert(&enforcement("row-1", 1));
        assert_eq!(store.get("enforcement", "row-1").unwrap().row.revision(), 1);
        assert_eq!(
            store
                .get("resource_domain", "row-1")
                .unwrap()
                .row
                .revision(),
            0
        );

        let kinds = store
            .rows()
            .map(|annotation| annotation.row.row_kind())
            .collect::<Vec<_>>();
        assert_eq!(
            kinds,
            vec![
                "correlation",
                "enforcement",
                "policy_decision",
                "resource_domain"
            ]
        );
    }
}
