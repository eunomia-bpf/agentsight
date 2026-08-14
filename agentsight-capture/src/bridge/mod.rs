// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Bridge emission: turns materialized-view rows into revisioned
//! [`ViewMutationEnvelope`]s and hands them to registered [`MutationSink`]s.
//!
//! The emitter is deliberately independent of any transport. `MaterializedView`
//! owns one and feeds it from every `emit_*` call; the collector's Unix-socket
//! server registers a sink on it.
//!
//! [`annotations::AnnotationStore`] is the exception that does not emit: it
//! receives the client's reverse annotations, which travel the other way.

pub mod annotations;
pub mod metadata;
pub mod projection;

use crate::model::{
    AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow, ResourceSampleRow, SessionRow,
    TokenUsageRow, ToolCallRow,
};
use agentsight_protocol::bridge::{
    BRIDGE_PROTOCOL_VERSION, DisclosureMode, MutationOperation, TimestampBasis, ViewMutation,
    ViewMutationEnvelope,
};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

pub type MutationResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Receiver of bridge mutations. Implementors must not block the capture
/// pipeline: the view holds its lock while calling this.
pub trait MutationSink: Send {
    fn mutation(&mut self, m: &ViewMutationEnvelope) -> MutationResult<()>;
}

/// Shared, monotonically increasing sequence source. Cloning shares the
/// counter, so the emitter and the server hand out sequences from one series
/// per (node_id, boot).
#[derive(Clone, Debug, Default)]
pub struct SequenceAllocator(Arc<AtomicU64>);

impl SequenceAllocator {
    pub fn new() -> Self {
        Self::default()
    }

    /// Allocate the next sequence. The first allocation returns 1.
    pub fn next_sequence(&self) -> u64 {
        self.0.fetch_add(1, Ordering::SeqCst) + 1
    }

    /// Highest sequence handed out so far; 0 before the first allocation.
    pub fn current(&self) -> u64 {
        self.0.load(Ordering::SeqCst)
    }
}

/// Identity and policy stamped onto every envelope this emitter produces.
#[derive(Clone, Debug)]
pub struct MutationEmitterConfig {
    pub node_id: String,
    pub boot_id: Option<String>,
    pub source_component: String,
    pub source_version: String,
    pub disclosure: DisclosureMode,
    pub sequence: SequenceAllocator,
}

impl Default for MutationEmitterConfig {
    fn default() -> Self {
        Self {
            node_id: "agentsight-local".to_string(),
            boot_id: None,
            source_component: "agentsight-capture".to_string(),
            source_version: env!("CARGO_PKG_VERSION").to_string(),
            disclosure: DisclosureMode::MetadataOnly,
            sequence: SequenceAllocator::new(),
        }
    }
}

#[derive(Debug, Clone)]
struct RevisionState {
    content_hash: String,
    revision: u64,
}

/// Builds envelopes with correct revisions and fans them out to sinks.
#[derive(Default)]
pub struct MutationEmitter {
    config: MutationEmitterConfig,
    sinks: Vec<Box<dyn MutationSink>>,
    revisions: HashMap<(&'static str, String), RevisionState>,
}

/// What the revision bookkeeping decided for one row emission.
struct RevisionDecision {
    revision: u64,
    operation: MutationOperation,
}

impl MutationEmitter {
    pub fn new(config: MutationEmitterConfig) -> Self {
        Self {
            config,
            sinks: Vec::new(),
            revisions: HashMap::new(),
        }
    }

    pub fn add_sink(&mut self, sink: Box<dyn MutationSink>) {
        self.sinks.push(sink);
    }

    pub fn set_config(&mut self, config: MutationEmitterConfig) {
        self.config = config;
    }

    pub fn config(&self) -> &MutationEmitterConfig {
        &self.config
    }

    pub fn disclosure(&self) -> &DisclosureMode {
        &self.config.disclosure
    }

    pub fn has_sinks(&self) -> bool {
        !self.sinks.is_empty()
    }

    /// Current revision of a tracked row, if it has been emitted before.
    pub fn revision_of(&self, row_kind: &'static str, row_id: &str) -> Option<u64> {
        self.revisions
            .get(&(row_kind, row_id.to_string()))
            .map(|state| state.revision)
    }

    /// Decide the revision for a row whose full serialized form hashes to
    /// `content_hash`. First emit is revision 0 / `Insert`; an unchanged
    /// re-emit keeps the revision and reports `Update`; a real state change
    /// increments.
    fn decide(
        &mut self,
        row_kind: &'static str,
        row_id: &str,
        content_hash: String,
    ) -> RevisionDecision {
        let key = (row_kind, row_id.to_string());
        match self.revisions.get_mut(&key) {
            None => {
                self.revisions.insert(
                    key,
                    RevisionState {
                        content_hash,
                        revision: 0,
                    },
                );
                RevisionDecision {
                    revision: 0,
                    operation: MutationOperation::Insert,
                }
            }
            Some(state) if state.content_hash == content_hash => RevisionDecision {
                revision: state.revision,
                operation: MutationOperation::Update,
            },
            Some(state) => {
                state.content_hash = content_hash;
                state.revision += 1;
                RevisionDecision {
                    revision: state.revision,
                    operation: MutationOperation::Update,
                }
            }
        }
    }

    fn forget(&mut self, row_kind: &'static str, row_id: &str) {
        self.revisions.remove(&(row_kind, row_id.to_string()));
    }

    /// Wrap a mutation in an envelope with a freshly allocated sequence.
    pub fn envelope(
        &self,
        operation: MutationOperation,
        mutation: ViewMutation,
        observed_wall_ms: Option<u64>,
        basis: TimestampBasis,
    ) -> ViewMutationEnvelope {
        ViewMutationEnvelope {
            protocol_version: BRIDGE_PROTOCOL_VERSION,
            node_id: self.config.node_id.clone(),
            boot_id: self.config.boot_id.clone(),
            sequence: self.config.sequence.next_sequence(),
            observed_wall_ms,
            // The capture rows carry wall-clock milliseconds only; a monotonic
            // reading is never invented here.
            observed_monotonic_ns: None,
            basis,
            source_component: self.config.source_component.clone(),
            source_version: self.config.source_version.clone(),
            scope_handle: None,
            operation,
            mutation,
        }
    }

    /// Emit an already-built envelope to every sink, collecting the first error.
    pub fn publish(&mut self, envelope: &ViewMutationEnvelope) -> MutationResult<()> {
        let mut first_error = None;
        for sink in &mut self.sinks {
            if let Err(error) = sink.mutation(envelope) {
                log::warn!("MutationEmitter: failed to publish bridge mutation: {error}");
                first_error.get_or_insert_with(|| error.to_string());
            }
        }
        match first_error {
            Some(error) => Err(std::io::Error::other(error).into()),
            None => Ok(()),
        }
    }

    fn emit(
        &mut self,
        operation: MutationOperation,
        mutation: ViewMutation,
        observed_wall_ms: Option<u64>,
        basis: TimestampBasis,
    ) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let envelope = self.envelope(operation, mutation, observed_wall_ms, basis);
        self.publish(&envelope)
    }

    pub fn session(&mut self, row: &SessionRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let decision = self.decide("session", &row.id, hash_row(row));
        let projected = projection::session(row, decision.revision, self.disclosure());
        self.emit(
            decision.operation,
            ViewMutation::SessionUpsert(projected),
            Some(row.start_timestamp_ms),
            projection::basis_for_source(&row.view_source),
        )
    }

    pub fn llm_call(&mut self, row: &LlmCallRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let decision = self.decide("llm_call", &row.id, hash_row(row));
        let projected = projection::llm_call(row, decision.revision, self.disclosure());
        self.emit(
            decision.operation,
            ViewMutation::LlmCallUpsert(projected),
            Some(row.start_timestamp_ms),
            TimestampBasis::EpochMilliseconds,
        )
    }

    pub fn token_usage(&mut self, row: &TokenUsageRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let decision = self.decide("token_usage", &row.id, hash_row(row));
        let projected = projection::token_usage(row, decision.revision);
        self.emit(
            decision.operation,
            ViewMutation::TokenUsageUpsert(projected),
            Some(row.timestamp_ms),
            projection::basis_for_source(&row.view_source),
        )
    }

    pub fn tool_call(&mut self, row: &ToolCallRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let decision = self.decide("tool_call", &row.id, hash_row(row));
        let projected = projection::tool_call(row, decision.revision, self.disclosure());
        self.emit(
            decision.operation,
            ViewMutation::ToolCallUpsert(projected),
            Some(row.timestamp_ms),
            projection::basis_for_source(&row.view_source),
        )
    }

    pub fn process_node(&mut self, row: &ProcessNodeRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let decision = self.decide("process_node", &row.id, hash_row(row));
        let projected = projection::process_node(row, decision.revision, self.disclosure());
        self.emit(
            decision.operation,
            ViewMutation::ProcessNodeUpsert(projected),
            row.start_timestamp_ms,
            TimestampBasis::EpochMilliseconds,
        )
    }

    /// Audit rows are insert-only: no revision is tracked for them.
    pub fn audit_event(&mut self, row: &AuditEventRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let projected = projection::audit_event(row, self.disclosure());
        self.emit(
            MutationOperation::Insert,
            ViewMutation::AuditEventInserted(projected),
            Some(row.timestamp_ms),
            TimestampBasis::EpochMilliseconds,
        )
    }

    pub fn network_target(&mut self, row: &NetworkTargetRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let row_id = projection::network_target_row_id(row);
        let decision = self.decide("network_target", &row_id, hash_row(row));
        let projected = projection::network_target(row, decision.revision, self.disclosure());
        self.emit(
            decision.operation,
            ViewMutation::NetworkTargetUpsert(projected),
            row.last_timestamp_ms,
            TimestampBasis::EpochMilliseconds,
        )
    }

    /// Resource samples are insert-only.
    pub fn resource_sample(&mut self, row: &ResourceSampleRow) -> MutationResult<()> {
        if self.sinks.is_empty() {
            return Ok(());
        }
        let projected = projection::resource_sample(row);
        self.emit(
            MutationOperation::Insert,
            ViewMutation::ResourceSampleInserted(projected),
            Some(row.timestamp_ms),
            TimestampBasis::EpochMilliseconds,
        )
    }

    /// Announce that a tracked row is gone; drops its revision bookkeeping.
    pub fn row_evicted(&mut self, row_kind: &'static str, row_id: &str) -> MutationResult<()> {
        self.forget(row_kind, row_id);
        if self.sinks.is_empty() {
            return Ok(());
        }
        self.emit(
            MutationOperation::Delete,
            ViewMutation::RowEvicted {
                row_kind: row_kind.to_string(),
                row_id: row_id.to_string(),
            },
            None,
            TimestampBasis::Unknown,
        )
    }

    pub fn capability_changed(
        &mut self,
        capability: &str,
        available: bool,
        detail: Option<String>,
    ) -> MutationResult<()> {
        self.emit(
            MutationOperation::Update,
            ViewMutation::CaptureCapabilityChanged {
                capability: capability.to_string(),
                available,
                detail,
            },
            None,
            TimestampBasis::Unknown,
        )
    }

    pub fn capture_gap(
        &mut self,
        from_sequence: u64,
        to_sequence: u64,
        reason: &str,
    ) -> MutationResult<()> {
        self.emit(
            MutationOperation::Insert,
            ViewMutation::CaptureGapObserved {
                from_sequence,
                to_sequence,
                reason: reason.to_string(),
            },
            None,
            TimestampBasis::Unknown,
        )
    }
}

/// Content hash over the serialized FULL source row, so any state change bumps
/// the revision and an identical re-emit does not.
fn hash_row<T: serde::Serialize>(row: &T) -> String {
    let serialized = serde_json::to_vec(row).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(&serialized);
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Mutex};

    #[derive(Clone, Default)]
    pub(crate) struct RecordingSink {
        pub(crate) envelopes: Arc<Mutex<Vec<ViewMutationEnvelope>>>,
    }

    impl MutationSink for RecordingSink {
        fn mutation(&mut self, m: &ViewMutationEnvelope) -> MutationResult<()> {
            self.envelopes.lock().unwrap().push(m.clone());
            Ok(())
        }
    }

    fn session(model: Option<&str>) -> SessionRow {
        SessionRow {
            id: "session-1".to_string(),
            agent_type: "claude".to_string(),
            start_timestamp_ms: 1_000,
            end_timestamp_ms: None,
            status: "observed".to_string(),
            model: model.map(str::to_string),
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            view_source: "agent_native_session".to_string(),
            confidence: None,
            attributes: serde_json::json!({}),
        }
    }

    fn emitter_with_sink() -> (MutationEmitter, RecordingSink) {
        let sink = RecordingSink::default();
        let mut emitter = MutationEmitter::new(MutationEmitterConfig::default());
        emitter.add_sink(Box::new(sink.clone()));
        (emitter, sink)
    }

    #[test]
    fn sequences_start_at_one_and_increase() {
        let (mut emitter, sink) = emitter_with_sink();
        emitter.session(&session(None)).unwrap();
        emitter.session(&session(Some("claude-sonnet-4"))).unwrap();
        let envelopes = sink.envelopes.lock().unwrap();
        assert_eq!(envelopes[0].sequence, 1);
        assert_eq!(envelopes[1].sequence, 2);
    }

    #[test]
    fn identical_re_emit_does_not_bump_the_revision() {
        let (mut emitter, sink) = emitter_with_sink();
        emitter.session(&session(None)).unwrap();
        emitter.session(&session(None)).unwrap();
        let envelopes = sink.envelopes.lock().unwrap();
        assert_eq!(envelopes.len(), 2);
        assert_eq!(envelopes[0].operation, MutationOperation::Insert);
        assert_eq!(envelopes[1].operation, MutationOperation::Update);
        for envelope in envelopes.iter() {
            match &envelope.mutation {
                ViewMutation::SessionUpsert(row) => assert_eq!(row.revision, 0),
                other => panic!("unexpected mutation {other:?}"),
            }
        }
    }

    #[test]
    fn changed_state_bumps_the_revision() {
        let (mut emitter, sink) = emitter_with_sink();
        emitter.session(&session(None)).unwrap();
        emitter.session(&session(Some("claude-sonnet-4"))).unwrap();
        emitter.session(&session(Some("claude-sonnet-4"))).unwrap();
        emitter.session(&session(Some("claude-opus-4"))).unwrap();
        let revisions = sink
            .envelopes
            .lock()
            .unwrap()
            .iter()
            .map(|envelope| match &envelope.mutation {
                ViewMutation::SessionUpsert(row) => row.revision,
                other => panic!("unexpected mutation {other:?}"),
            })
            .collect::<Vec<_>>();
        assert_eq!(revisions, vec![0, 1, 1, 2]);
    }

    #[test]
    fn eviction_forgets_the_revision_so_a_reinsert_restarts_at_zero() {
        let (mut emitter, sink) = emitter_with_sink();
        emitter.session(&session(None)).unwrap();
        emitter.session(&session(Some("m"))).unwrap();
        assert_eq!(emitter.revision_of("session", "session-1"), Some(1));
        emitter.row_evicted("session", "session-1").unwrap();
        assert_eq!(emitter.revision_of("session", "session-1"), None);
        emitter.session(&session(None)).unwrap();

        let envelopes = sink.envelopes.lock().unwrap();
        assert_eq!(envelopes[2].operation, MutationOperation::Delete);
        assert!(matches!(
            envelopes[2].mutation,
            ViewMutation::RowEvicted { .. }
        ));
        assert_eq!(envelopes[3].operation, MutationOperation::Insert);
    }

    #[test]
    fn insert_only_rows_never_track_revisions() {
        let (mut emitter, sink) = emitter_with_sink();
        let sample = ResourceSampleRow {
            timestamp_ms: 5,
            pid: Some(1),
            comm: Some("node".to_string()),
            cpu_percent: Some(1.0),
            rss_mb: Some(2),
        };
        emitter.resource_sample(&sample).unwrap();
        emitter.resource_sample(&sample).unwrap();
        let envelopes = sink.envelopes.lock().unwrap();
        assert_eq!(envelopes.len(), 2);
        assert!(
            envelopes
                .iter()
                .all(|envelope| envelope.operation == MutationOperation::Insert)
        );
        assert_eq!(emitter.revisions.len(), 0);
    }

    #[test]
    fn an_emitter_without_sinks_allocates_no_sequences() {
        let mut emitter = MutationEmitter::new(MutationEmitterConfig::default());
        emitter.session(&session(None)).unwrap();
        assert_eq!(emitter.config().sequence.current(), 0);
    }
}
