// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

mod canonical;
pub(crate) mod llm;
pub mod process_select;
mod projection;
pub mod session_process_match;

pub(crate) use canonical::{CanonicalEvent, EventKind, normalize_event};
pub(crate) use llm::{
    body_json, extract_model, extract_token_usage, extract_token_usage_from_sse, provider_from_host,
};

use crate::bridge::annotations::AnnotationStore;
use crate::bridge::projection as bridge_projection;
use crate::bridge::{MutationEmitter, MutationEmitterConfig, MutationSink};
use crate::model::{
    AGENT_NATIVE_SOURCE, AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow,
    ResourceSampleRow, SessionRow, Snapshot, SnapshotOptions, SnapshotSummary, TokenSummary,
    TokenUsageRow, ToolCallRow, ViewResult, ViewSink,
};
use agentsight_protocol::bridge::{AroAnnotation, DisclosureMode, ViewMutation};
use chrono::{SecondsFormat, Utc};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet, HashMap, VecDeque};
use std::sync::{Arc, Mutex};

pub type SharedMaterializedView = Arc<Mutex<MaterializedView>>;

const MAX_AUDIT_EVENTS_IN_MEMORY: usize = 20_000;
const MAX_RESOURCE_SAMPLES_IN_MEMORY: usize = 10_000;

#[derive(Default)]
pub struct MaterializedView {
    source: String,
    llm_calls: BTreeMap<String, LlmCallRow>,
    token_usage: BTreeMap<String, TokenUsageRow>,
    audit_events: BTreeMap<String, AuditEventRow>,
    process_nodes: BTreeMap<String, ProcessNodeRow>,
    tool_calls: BTreeMap<String, ToolCallRow>,
    sessions: BTreeMap<String, SessionRow>,
    network_targets: BTreeMap<String, NetworkTargetRow>,
    resource_samples: Vec<ResourceSampleRow>,
    audit_order: VecDeque<String>,
    sinks: Vec<Box<dyn ViewSink>>,
    /// Bridge mutation fan-out. Created lazily by `add_mutation_sink`; a view
    /// with no bridge consumer never allocates a sequence.
    mutations: Option<MutationEmitter>,
    /// What a bridge client told the view about its own scopes. Read-only: it
    /// is served back out and never consulted by capture.
    aro_annotations: AnnotationStore,
    pending: HashMap<(u32, u64), VecDeque<PendingRequest>>,
    active_processes: HashMap<u32, String>,
    counts: ViewCounts,
    start_timestamp_ms: Option<u64>,
    end_timestamp_ms: Option<u64>,
    max_audit_events: Option<usize>,
    max_resource_samples: Option<usize>,
    next_seq: u64,
}

#[derive(Default, Clone)]
struct ViewCounts {
    llm_calls: i64,
    token_usage: i64,
    audit_events: i64,
    process_nodes: i64,
    tool_calls: i64,
    sessions: i64,
    network_targets: i64,
    resource_samples: i64,
}

#[derive(Debug, Clone)]
struct PendingRequest {
    event_id: String,
    timestamp_ms: u64,
    pid: u32,
    comm: String,
    provider: Option<String>,
    model: Option<String>,
    host: Option<String>,
    path: Option<String>,
    request_id: Option<String>,
    body_json: Option<Value>,
}

impl MaterializedView {
    pub fn new() -> Self {
        Self::default()
    }

    /// Copy the materialized rows without copying output sinks. Callers can
    /// merge read-only supplemental sources for one response without mutating
    /// the live capture view or publishing duplicate rows.
    pub fn detached_copy(&self) -> Self {
        Self {
            source: self.source.clone(),
            llm_calls: self.llm_calls.clone(),
            token_usage: self.token_usage.clone(),
            audit_events: self.audit_events.clone(),
            process_nodes: self.process_nodes.clone(),
            tool_calls: self.tool_calls.clone(),
            sessions: self.sessions.clone(),
            network_targets: self.network_targets.clone(),
            resource_samples: self.resource_samples.clone(),
            audit_order: self.audit_order.clone(),
            sinks: Vec::new(),
            mutations: None,
            aro_annotations: self.aro_annotations.clone(),
            pending: self.pending.clone(),
            active_processes: self.active_processes.clone(),
            counts: self.counts.clone(),
            start_timestamp_ms: self.start_timestamp_ms,
            end_timestamp_ms: self.end_timestamp_ms,
            max_audit_events: self.max_audit_events,
            max_resource_samples: self.max_resource_samples,
            next_seq: self.next_seq,
        }
    }

    pub fn bounded() -> Self {
        let mut view = Self::new();
        view.max_audit_events = Some(MAX_AUDIT_EVENTS_IN_MEMORY);
        view.max_resource_samples = Some(MAX_RESOURCE_SAMPLES_IN_MEMORY);
        view
    }

    pub fn shared_bounded() -> SharedMaterializedView {
        Arc::new(Mutex::new(Self::bounded()))
    }

    pub fn add_sink(&mut self, sink: Box<dyn ViewSink>) {
        self.sinks.push(sink);
    }

    /// Register a bridge mutation consumer. Creating the first sink also
    /// creates the mutation emitter with its default identity; call
    /// [`Self::configure_mutations`] to replace that identity.
    pub fn add_mutation_sink(&mut self, sink: Box<dyn MutationSink>) {
        self.mutations
            .get_or_insert_with(|| MutationEmitter::new(MutationEmitterConfig::default()))
            .add_sink(sink);
    }

    /// Set the node identity, disclosure mode, and sequence source used for
    /// every envelope this view emits.
    pub fn configure_mutations(&mut self, config: MutationEmitterConfig) {
        match self.mutations.as_mut() {
            Some(emitter) => emitter.set_config(config),
            None => self.mutations = Some(MutationEmitter::new(config)),
        }
    }

    pub fn mutation_disclosure(&self) -> DisclosureMode {
        self.mutations
            .as_ref()
            .map(|emitter| emitter.disclosure().clone())
            .unwrap_or_default()
    }

    pub fn set_source(&mut self, source: impl Into<String>) {
        self.source = source.into();
    }

    pub fn emit_llm_call(&mut self, row: LlmCallRow) -> ViewResult<()> {
        self.apply_llm_call(&row);
        let published = self.publish(|sink| sink.llm_call(&row));
        self.mutate(|emitter| emitter.llm_call(&row));
        published
    }

    pub fn emit_token_usage(&mut self, row: TokenUsageRow) -> ViewResult<()> {
        self.apply_token_usage(&row);
        let published = self.publish(|sink| sink.token_usage(&row));
        self.mutate(|emitter| emitter.token_usage(&row));
        published
    }

    pub fn emit_audit_event(&mut self, row: AuditEventRow) -> ViewResult<()> {
        self.apply_audit_event(&row);
        let published = self.publish(|sink| sink.audit_event(&row));
        self.mutate(|emitter| emitter.audit_event(&row));
        published
    }

    pub fn emit_process_node(&mut self, row: ProcessNodeRow) -> ViewResult<()> {
        self.upsert_process_node(&row);
        let published = self.publish(|sink| sink.process_node(&row));
        // Process nodes merge on upsert, so the mutation must describe the
        // merged state rather than the incoming fragment.
        if let Some(merged) = self.process_nodes.get(&row.id).cloned() {
            self.mutate(|emitter| emitter.process_node(&merged));
        }
        published
    }

    pub fn emit_tool_call(&mut self, row: ToolCallRow) -> ViewResult<()> {
        self.apply_tool_call(&row);
        let published = self.publish(|sink| sink.tool_call(&row));
        self.mutate(|emitter| emitter.tool_call(&row));
        published
    }

    pub fn emit_network_target(&mut self, row: NetworkTargetRow) -> ViewResult<()> {
        self.upsert_network_target(&row);
        let published = self.publish(|sink| sink.network_target(&row));
        // Network targets accumulate counts on upsert; emit the accumulated row.
        if let Some(merged) = self.network_targets.get(&network_target_key(&row)).cloned() {
            self.mutate(|emitter| emitter.network_target(&merged));
        }
        published
    }

    pub fn emit_resource_sample(&mut self, row: ResourceSampleRow) -> ViewResult<()> {
        self.apply_resource_sample(&row);
        let published = self.publish(|sink| sink.resource_sample(&row));
        self.mutate(|emitter| emitter.resource_sample(&row));
        published
    }

    /// Upsert a session and publish it as a bridge mutation. `ViewSink` has no
    /// session method, so this is the only fan-out sessions have.
    pub fn emit_session(&mut self, row: SessionRow) -> ViewResult<()> {
        self.upsert_session(&row);
        if let Some(merged) = self.sessions.get(&row.id).cloned() {
            self.mutate(|emitter| emitter.session(&merged));
        }
        Ok(())
    }

    /// Emit a mutation that does not come from a row, such as a capture gap or
    /// a capability change.
    pub fn emit_bridge_notice<F>(&mut self, notice: F)
    where
        F: FnOnce(&mut MutationEmitter) -> crate::bridge::MutationResult<()>,
    {
        self.mutate(notice);
    }

    /// Project the current view state as snapshot mutations. Used to answer a
    /// bridge snapshot request; the caller stamps `SnapshotReconstruction`.
    pub fn bridge_snapshot_mutations(&self, disclosure: &DisclosureMode) -> Vec<ViewMutation> {
        let revision = |kind: &'static str, row_id: &str| {
            self.mutations
                .as_ref()
                .and_then(|emitter| emitter.revision_of(kind, row_id))
                .unwrap_or_default()
        };
        let mut mutations = Vec::new();
        for row in self.sessions.values() {
            mutations.push(ViewMutation::SessionUpsert(bridge_projection::session(
                row,
                revision("session", &row.id),
                disclosure,
            )));
        }
        for row in self.llm_calls.values() {
            mutations.push(ViewMutation::LlmCallUpsert(bridge_projection::llm_call(
                row,
                revision("llm_call", &row.id),
                disclosure,
            )));
        }
        for row in self.token_usage.values() {
            mutations.push(ViewMutation::TokenUsageUpsert(
                bridge_projection::token_usage(row, revision("token_usage", &row.id)),
            ));
        }
        for row in self.tool_calls.values() {
            mutations.push(ViewMutation::ToolCallUpsert(bridge_projection::tool_call(
                row,
                revision("tool_call", &row.id),
                disclosure,
            )));
        }
        for row in self.process_nodes.values() {
            mutations.push(ViewMutation::ProcessNodeUpsert(
                bridge_projection::process_node(row, revision("process_node", &row.id), disclosure),
            ));
        }
        for row in self.network_targets.values() {
            let row_id = bridge_projection::network_target_row_id(row);
            mutations.push(ViewMutation::NetworkTargetUpsert(
                bridge_projection::network_target(
                    row,
                    revision("network_target", &row_id),
                    disclosure,
                ),
            ));
        }
        for row in self.audit_events.values() {
            mutations.push(ViewMutation::AuditEventInserted(
                bridge_projection::audit_event(row, disclosure),
            ));
        }
        for row in &self.resource_samples {
            mutations.push(ViewMutation::ResourceSampleInserted(
                bridge_projection::resource_sample(row),
            ));
        }
        mutations
    }

    /// Run a mutation emission. Bridge consumers are supplemental: a failing
    /// sink is logged, never propagated into the capture pipeline.
    fn mutate<F>(&mut self, emit: F)
    where
        F: FnOnce(&mut MutationEmitter) -> crate::bridge::MutationResult<()>,
    {
        let Some(emitter) = self.mutations.as_mut() else {
            return;
        };
        if let Err(error) = emit(emitter) {
            log::warn!("MaterializedView: bridge mutation sink failed: {error}");
        }
    }

    fn publish<F>(&mut self, mut publish: F) -> ViewResult<()>
    where
        F: FnMut(&mut dyn ViewSink) -> ViewResult<()>,
    {
        let mut first_error = None;
        for sink in &mut self.sinks {
            if let Err(error) = publish(sink.as_mut()) {
                log::warn!("MaterializedView: failed to publish view row: {}", error);
                first_error.get_or_insert_with(|| error.to_string());
            }
        }
        if let Some(error) = first_error {
            return Err(std::io::Error::other(error).into());
        }
        Ok(())
    }
}

impl MaterializedView {
    pub fn apply_llm_call(&mut self, row: &LlmCallRow) {
        if !self.llm_calls.contains_key(&row.id) {
            self.counts.llm_calls += 1;
        }
        self.observe(Some(row.start_timestamp_ms));
        self.observe(row.end_timestamp_ms);
        self.llm_calls.insert(row.id.clone(), row.clone());
    }

    pub fn apply_token_usage(&mut self, row: &TokenUsageRow) {
        if !self.token_usage.contains_key(&row.id) {
            self.counts.token_usage += 1;
        }
        self.observe(Some(row.timestamp_ms));
        self.token_usage.insert(row.id.clone(), row.clone());
    }

    pub fn apply_audit_event(&mut self, row: &AuditEventRow) {
        if !self.audit_events.contains_key(&row.id) {
            self.counts.audit_events += 1;
            if self.max_audit_events.is_some() {
                self.audit_order.push_back(row.id.clone());
            }
        }
        self.observe(Some(row.timestamp_ms));
        self.audit_events.insert(row.id.clone(), row.clone());
        if let Some(max) = self.max_audit_events {
            while self.audit_events.len() > max {
                let Some(id) = self.audit_order.pop_front() else {
                    break;
                };
                self.audit_events.remove(&id);
            }
        }
    }

    pub fn apply_tool_call(&mut self, row: &ToolCallRow) {
        if !self.tool_calls.contains_key(&row.id) {
            self.counts.tool_calls += 1;
        }
        self.observe(Some(row.timestamp_ms));
        self.tool_calls.insert(row.id.clone(), row.clone());
    }

    pub fn apply_resource_sample(&mut self, row: &ResourceSampleRow) {
        self.counts.resource_samples += 1;
        self.observe(Some(row.timestamp_ms));
        self.resource_samples.push(row.clone());
        if let Some(max) = self.max_resource_samples {
            let overflow = self.resource_samples.len().saturating_sub(max);
            if overflow > 0 {
                self.resource_samples.drain(0..overflow);
            }
        }
    }

    /// Record one client annotation. Returns whether it changed the store: a
    /// duplicate or stale revision is a no-op, so a client replaying its stream
    /// after a reconnect changes nothing.
    ///
    /// Deliberately not an `emit_*`: annotations are inbound. They are never
    /// published to a view sink and never turned into a bridge mutation, so an
    /// annotation cannot become evidence the collector claims to have observed.
    pub fn apply_aro_annotation(&mut self, annotation: &AroAnnotation) -> bool {
        self.aro_annotations.upsert(annotation)
    }

    /// Every stored client annotation, grouped by kind then row id.
    pub fn aro_annotations(&self) -> Vec<AroAnnotation> {
        self.aro_annotations.rows().cloned().collect()
    }

    /// Annotations dropped to stay inside the store's bound. Non-zero means
    /// what [`Self::aro_annotations`] returns is incomplete.
    pub fn aro_annotations_evicted(&self) -> u64 {
        self.aro_annotations.evicted()
    }

    pub fn upsert_session(&mut self, row: &SessionRow) {
        self.observe(Some(row.start_timestamp_ms));
        self.observe(row.end_timestamp_ms);
        let Some(existing) = self.sessions.get_mut(&row.id) else {
            self.counts.sessions += 1;
            self.sessions.insert(row.id.clone(), row.clone());
            return;
        };

        existing.start_timestamp_ms = existing.start_timestamp_ms.min(row.start_timestamp_ms);
        existing.end_timestamp_ms = max_optional(existing.end_timestamp_ms, row.end_timestamp_ms);
        if row.model.as_deref().is_some_and(|model| model != "unknown") || existing.model.is_none()
        {
            existing.model = row.model.clone();
        }
        existing.input_tokens = existing.input_tokens.max(row.input_tokens);
        existing.output_tokens = existing.output_tokens.max(row.output_tokens);
        existing.total_tokens = existing.total_tokens.max(row.total_tokens);
        existing.confidence = max_optional(existing.confidence, row.confidence);
    }

    pub fn upsert_network_target(&mut self, row: &NetworkTargetRow) {
        self.observe(row.first_timestamp_ms);
        self.observe(row.last_timestamp_ms);
        let key = network_target_key(row);
        let Some(existing) = self.network_targets.get_mut(&key) else {
            self.counts.network_targets += 1;
            self.network_targets.insert(key, row.clone());
            return;
        };

        existing.count += row.count;
        existing.error_count += row.error_count;
        existing.first_timestamp_ms =
            min_optional(existing.first_timestamp_ms, row.first_timestamp_ms);
        existing.last_timestamp_ms =
            max_optional(existing.last_timestamp_ms, row.last_timestamp_ms);
    }

    pub fn upsert_process_node(&mut self, row: &ProcessNodeRow) {
        self.observe(row.start_timestamp_ms);
        self.observe(row.end_timestamp_ms);
        let Some(existing) = self.process_nodes.get_mut(&row.id) else {
            self.counts.process_nodes += 1;
            self.process_nodes.insert(row.id.clone(), row.clone());
            return;
        };

        existing.start_timestamp_ms =
            min_optional(existing.start_timestamp_ms, row.start_timestamp_ms);
        existing.end_timestamp_ms = max_optional(existing.end_timestamp_ms, row.end_timestamp_ms);
        // Read once at exec and never revised: a later read of the same pid can
        // only be a different task, so the first value is the identity.
        if existing.start_ticks.is_none() {
            existing.start_ticks = row.start_ticks;
        }
        if row.ppid.is_some() {
            existing.ppid = row.ppid;
        }
        if row.root_pid.is_some() {
            existing.root_pid = row.root_pid;
        }
        if row.comm.is_some() {
            existing.comm = row.comm.clone();
        }
        if row.command.is_some() {
            existing.command = row.command.clone();
        }
        if existing.argv.is_empty() && !row.argv.is_empty() {
            existing.argv = row.argv.clone();
        }
        if row.cwd.is_some() {
            existing.cwd = row.cwd.clone();
        }
        if row.exit_code.is_some() {
            existing.exit_code = row.exit_code;
        }
        if row.status.is_some() {
            existing.status = row.status.clone();
        }
        existing.confidence = max_optional(existing.confidence, row.confidence);
    }

    pub fn export_snapshot(&self, options: SnapshotOptions) -> Snapshot {
        Snapshot {
            schema_version: 1,
            generated_at: Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true),
            summary: self.snapshot_summary(options),
            token_summary: self.token_summary("model"),
            network_targets: self.network_targets(),
            process_nodes: self.process_nodes(),
            audit_events: self.audit_events(options.audit_limit),
            resource_samples: self.resource_sample_rows(),
            sessions: self.sessions(),
            tool_calls: self.tool_calls.values().cloned().collect(),
            aro_annotations: self.aro_annotations(),
        }
    }

    fn snapshot_summary(&self, options: SnapshotOptions) -> SnapshotSummary {
        let (input_tokens, output_tokens, total_tokens) =
            self.effective_tokens()
                .into_iter()
                .fold((0, 0, 0), |acc, token| {
                    (
                        acc.0 + token.input_tokens,
                        acc.1 + token.output_tokens,
                        acc.2 + token.total_tokens,
                    )
                });

        SnapshotSummary {
            source: if self.source.is_empty() {
                "materialized_view".to_string()
            } else {
                self.source.clone()
            },
            view_events: self.view_events(),
            llm_calls: self.counts.llm_calls,
            token_usage_rows: self.counts.token_usage,
            audit_events: self.counts.audit_events,
            sessions: self.counts.sessions,
            input_tokens,
            output_tokens,
            total_tokens,
            start_timestamp_ms: self.start_timestamp_ms,
            end_timestamp_ms: self.end_timestamp_ms,
            audit_limit: options.audit_limit,
        }
    }

    pub fn token_summary(&self, group_by: &str) -> Vec<TokenSummary> {
        let mut groups: BTreeMap<String, TokenSummaryGroup> = BTreeMap::new();
        for token in self.effective_tokens() {
            let group = self.token_group(token, group_by);
            let entry = groups
                .entry(group.clone())
                .or_insert_with(|| TokenSummaryGroup::new(group));
            entry.row.input_tokens += token.input_tokens;
            entry.row.output_tokens += token.output_tokens;
            entry.row.cache_creation_tokens += token.cache_creation_tokens;
            entry.row.cache_read_tokens += token.cache_read_tokens;
            entry.row.total_tokens += token.total_tokens;
            entry.row.calls += 1;
            if let Some(session_key) = self.token_session_key(token) {
                entry.sessions.insert(session_key);
            }
        }
        let mut rows = groups
            .into_values()
            .map(|mut group| {
                group.row.sessions = group.sessions.len() as i64;
                group.row
            })
            .collect::<Vec<_>>();
        sort_token_summary(&mut rows);
        rows
    }

    pub fn audit_rows(&self, audit_type: Option<&str>, limit: usize) -> Vec<AuditEventRow> {
        let mut rows = self
            .audit_events
            .values()
            .filter(|row| audit_type.is_none_or(|audit_type| row.audit_type == audit_type))
            .cloned()
            .collect::<Vec<_>>();
        rows.sort_by_key(|b| std::cmp::Reverse(b.timestamp_ms));
        rows.truncate(limit.clamp(1, 10_000));
        rows
    }

    pub fn llm_call_rows(&self, limit: usize) -> Vec<LlmCallRow> {
        let token_totals = self.effective_token_totals_by_call();
        let mut rows = self
            .llm_calls
            .values()
            .cloned()
            .map(|mut row| {
                if let Some((input, output, total)) = token_totals.get(&row.id) {
                    row.input_tokens = *input;
                    row.output_tokens = *output;
                    row.total_tokens = *total;
                }
                row
            })
            .collect::<Vec<_>>();
        rows.sort_by_key(|b| std::cmp::Reverse(b.start_timestamp_ms));
        rows.truncate(limit.clamp(1, 10_000));
        rows
    }

    fn resource_sample_rows(&self) -> Vec<ResourceSampleRow> {
        let mut rows = self.resource_samples.clone();
        rows.sort_by(|a, b| {
            a.timestamp_ms
                .cmp(&b.timestamp_ms)
                .then_with(|| a.pid.cmp(&b.pid))
                .then_with(|| a.comm.cmp(&b.comm))
        });
        rows
    }

    fn network_targets(&self) -> Vec<NetworkTargetRow> {
        let mut rows = self.network_targets.values().cloned().collect::<Vec<_>>();
        rows.sort_by(|a, b| {
            b.count
                .cmp(&a.count)
                .then_with(|| a.host.cmp(&b.host))
                .then_with(|| a.path.cmp(&b.path))
        });
        rows
    }

    fn audit_events(&self, limit: usize) -> Vec<AuditEventRow> {
        let mut rows = self.audit_events.values().cloned().collect::<Vec<_>>();
        rows.sort_by(|a, b| {
            a.timestamp_ms
                .cmp(&b.timestamp_ms)
                .then_with(|| a.id.cmp(&b.id))
        });
        let limit = limit.min(100_000);
        if rows.len() > limit {
            rows.drain(0..rows.len() - limit);
        }
        rows
    }

    fn process_nodes(&self) -> Vec<ProcessNodeRow> {
        let mut rows = self.process_nodes.values().cloned().collect::<Vec<_>>();
        rows.sort_by(|a, b| {
            a.start_timestamp_ms
                .cmp(&b.start_timestamp_ms)
                .then_with(|| a.pid.cmp(&b.pid))
                .then_with(|| a.id.cmp(&b.id))
        });
        rows
    }

    fn sessions(&self) -> Vec<SessionRow> {
        let mut rows = self.sessions.values().cloned().collect::<Vec<_>>();
        rows.sort_by(|a, b| {
            a.start_timestamp_ms
                .cmp(&b.start_timestamp_ms)
                .then_with(|| a.id.cmp(&b.id))
        });
        rows
    }

    fn view_events(&self) -> i64 {
        self.counts.llm_calls
            + self.counts.token_usage
            + self.counts.audit_events
            + self.counts.process_nodes
            + self.counts.tool_calls
            + self.counts.sessions
            + self.counts.network_targets
            + self.counts.resource_samples
    }

    fn effective_tokens(&self) -> Vec<&TokenUsageRow> {
        let mut selected: BTreeMap<String, &TokenUsageRow> = BTreeMap::new();
        let mut gemini_totals = BTreeMap::new();
        for token in self.token_usage.values() {
            let Some(key) = token.pid.zip(token.model.as_deref()) else {
                continue;
            };
            let totals = gemini_totals.entry(key).or_insert((0, 0));
            match token.source.as_str() {
                "response_usage" | "orphan_response_usage" => totals.0 += token.total_tokens,
                "gemini_cli_stdout_stats" => totals.1 = totals.1.max(token.total_tokens),
                _ => {}
            }
        }
        for token in self.token_usage.values() {
            if let Some((network, stdout)) = token
                .pid
                .zip(token.model.as_deref())
                .and_then(|key| gemini_totals.get(&key))
            {
                let network_source = matches!(
                    token.source.as_str(),
                    "response_usage" | "orphan_response_usage"
                );
                if (token.source == "gemini_cli_stdout_stats" && network >= stdout)
                    || (network_source && stdout > network)
                    || (token.source == "gemini_cli_stdout_stats" && token.total_tokens < *stdout)
                {
                    continue;
                }
            }
            let key = if token.source == "gemini_cli_stdout_stats" {
                token
                    .pid
                    .zip(token.model.as_deref())
                    .map(|(pid, model)| format!("gemini-stdout\0{pid}\0{model}"))
                    .unwrap_or_else(|| token.id.clone())
            } else if token.llm_call_id.is_empty() {
                token.id.clone()
            } else {
                token.llm_call_id.clone()
            };
            match selected.get(&key) {
                Some(current) if !token_has_higher_priority(token, current) => {}
                _ => {
                    selected.insert(key, token);
                }
            }
        }
        selected.into_values().collect()
    }

    fn effective_token_totals_by_call(&self) -> BTreeMap<String, (i64, i64, i64)> {
        let mut totals = BTreeMap::new();
        for token in self.effective_tokens() {
            totals.insert(
                token.llm_call_id.clone(),
                (token.input_tokens, token.output_tokens, token.total_tokens),
            );
        }
        totals
    }

    fn observe(&mut self, timestamp: Option<u64>) {
        observe_timestamp(
            &mut self.start_timestamp_ms,
            &mut self.end_timestamp_ms,
            timestamp,
        );
    }

    fn token_group(&self, token: &TokenUsageRow, group_by: &str) -> String {
        match group_by {
            "provider" => token.provider.clone(),
            "comm" => token.comm.clone(),
            "pid" => token.pid.map(|pid| pid.to_string()),
            "dir" | "cwd" | "directory" => self.token_working_dir(token),
            _ => token.model.clone(),
        }
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| "unknown".to_string())
    }

    fn token_working_dir(&self, token: &TokenUsageRow) -> Option<String> {
        self.token_session_key(token)
            .and_then(|session_id| self.sessions.get(&session_id).and_then(session_cwd))
            .or_else(|| self.token_process_cwd(token))
    }

    fn token_session_key(&self, token: &TokenUsageRow) -> Option<String> {
        if let Some(session_id) = self
            .llm_calls
            .get(&token.llm_call_id)
            .and_then(|row| row.session_id.as_ref())
            .filter(|session_id| !session_id.is_empty())
        {
            return Some(session_id.clone());
        }

        self.sessions
            .keys()
            .find(|session_id| {
                let session_id = session_id.as_str();
                token.llm_call_id == session_id
                    || token
                        .llm_call_id
                        .strip_prefix(session_id)
                        .is_some_and(|suffix| suffix.starts_with('-'))
            })
            .cloned()
    }

    fn token_process_cwd(&self, token: &TokenUsageRow) -> Option<String> {
        let pid = token.pid.or_else(|| {
            self.llm_calls
                .get(&token.llm_call_id)
                .and_then(|row| row.pid)
        })?;
        self.process_nodes
            .values()
            .find(|row| row.pid == pid && row.cwd.as_deref().is_some_and(|cwd| !cwd.is_empty()))
            .and_then(|row| row.cwd.clone())
    }
}

struct TokenSummaryGroup {
    row: TokenSummary,
    sessions: BTreeSet<String>,
}

impl TokenSummaryGroup {
    fn new(group: String) -> Self {
        Self {
            row: TokenSummary {
                group,
                input_tokens: 0,
                output_tokens: 0,
                cache_creation_tokens: 0,
                cache_read_tokens: 0,
                total_tokens: 0,
                calls: 0,
                sessions: 0,
            },
            sessions: BTreeSet::new(),
        }
    }
}

fn session_cwd(session: &SessionRow) -> Option<String> {
    session
        .attributes
        .get("cwd")
        .and_then(Value::as_str)
        .filter(|cwd| !cwd.is_empty())
        .map(str::to_string)
}

fn token_has_higher_priority(candidate: &TokenUsageRow, current: &TokenUsageRow) -> bool {
    let candidate_priority = token_source_priority(&candidate.source);
    let current_priority = token_source_priority(&current.source);
    candidate_priority
        .cmp(&current_priority)
        .then_with(|| {
            current
                .confidence
                .unwrap_or_default()
                .partial_cmp(&candidate.confidence.unwrap_or_default())
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .then_with(|| candidate.id.cmp(&current.id))
        .is_lt()
}

fn token_source_priority(source: &str) -> u8 {
    match source {
        // Network-observed response usage is the primary fact source. Native
        // session logs enrich or backfill when no network call was captured.
        "response_usage" => 0,
        "orphan_response_usage" => 1,
        "gemini_cli_stdout_stats" => 2,
        "claude_telemetry" => 3,
        AGENT_NATIVE_SOURCE => 4,
        _ => 5,
    }
}

fn network_target_key(row: &NetworkTargetRow) -> String {
    format!(
        "{}\0{}\0{}",
        row.pid.unwrap_or_default(),
        row.host,
        row.path.as_deref().unwrap_or_default()
    )
}

fn observe_timestamp(start: &mut Option<u64>, end: &mut Option<u64>, timestamp: Option<u64>) {
    let Some(timestamp) = timestamp else {
        return;
    };
    *start = Some(start.map_or(timestamp, |current| current.min(timestamp)));
    *end = Some(end.map_or(timestamp, |current| current.max(timestamp)));
}

fn sort_token_summary(rows: &mut [TokenSummary]) {
    rows.sort_by(|a, b| {
        b.total_tokens
            .cmp(&a.total_tokens)
            .then_with(|| a.group.cmp(&b.group))
    });
}

fn min_optional<T: PartialOrd>(left: Option<T>, right: Option<T>) -> Option<T> {
    match (left, right) {
        (Some(left), Some(right)) => Some(if left <= right { left } else { right }),
        (Some(value), None) | (None, Some(value)) => Some(value),
        (None, None) => None,
    }
}

fn max_optional<T: PartialOrd>(left: Option<T>, right: Option<T>) -> Option<T> {
    match (left, right) {
        (Some(left), Some(right)) => Some(if left >= right { left } else { right }),
        (Some(value), None) | (None, Some(value)) => Some(value),
        (None, None) => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn audit_row(timestamp_ms: u64) -> AuditEventRow {
        AuditEventRow {
            id: format!("audit-{timestamp_ms}"),
            timestamp_ms,
            audit_type: "file".to_string(),
            pid: Some(1),
            comm: Some("test".to_string()),
            subject: None,
            action: Some("write".to_string()),
            target: Some(format!("/tmp/{timestamp_ms}")),
            status: Some("observed".to_string()),
            summary: None,
            details: json!({}),
        }
    }

    fn session_row(id: &str, cwd: &str) -> SessionRow {
        SessionRow {
            id: id.to_string(),
            agent_type: "codex".to_string(),
            start_timestamp_ms: 1_000,
            end_timestamp_ms: Some(2_000),
            status: "observed".to_string(),
            model: Some("gpt-5".to_string()),
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            view_source: AGENT_NATIVE_SOURCE.to_string(),
            confidence: Some(0.95),
            attributes: json!({ "cwd": cwd }),
        }
    }

    fn token_row(
        id: &str,
        llm_call_id: &str,
        model: &str,
        input_tokens: i64,
        output_tokens: i64,
        cache_creation_tokens: i64,
        cache_read_tokens: i64,
        total_tokens: i64,
    ) -> TokenUsageRow {
        TokenUsageRow {
            id: id.to_string(),
            llm_call_id: llm_call_id.to_string(),
            timestamp_ms: 1_500,
            pid: None,
            comm: Some("codex".to_string()),
            provider: None,
            model: Some(model.to_string()),
            input_tokens,
            output_tokens,
            cache_creation_tokens,
            cache_read_tokens,
            total_tokens,
            source: AGENT_NATIVE_SOURCE.to_string(),
            view_source: AGENT_NATIVE_SOURCE.to_string(),
            confidence: Some(0.95),
        }
    }

    fn process_node(pid: u32, cwd: &str) -> ProcessNodeRow {
        ProcessNodeRow {
            id: format!("process-{pid}"),
            pid,
            start_ticks: None,
            ppid: None,
            root_pid: Some(pid),
            start_timestamp_ms: Some(1_000),
            end_timestamp_ms: None,
            comm: Some("agent".to_string()),
            command: Some("agent".to_string()),
            argv: Vec::new(),
            cwd: Some(cwd.to_string()),
            exit_code: None,
            status: Some("observed".to_string()),
            view_source: "process".to_string(),
            confidence: Some(0.8),
        }
    }

    fn llm_call_row(id: &str, pid: u32, session_id: Option<&str>) -> LlmCallRow {
        LlmCallRow {
            id: id.to_string(),
            session_id: session_id.map(str::to_string),
            conversation_id: None,
            start_timestamp_ms: 1_100,
            end_timestamp_ms: Some(1_400),
            pid: Some(pid),
            comm: Some("agent".to_string()),
            provider: Some("anthropic".to_string()),
            model: Some("claude-sonnet-4".to_string()),
            call_kind: Some("messages".to_string()),
            status: "ok".to_string(),
            error_type: None,
            finish_reason: None,
            host: Some("api.anthropic.com".to_string()),
            path: Some("/v1/messages".to_string()),
            status_code: Some(200),
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
            request: json!({}),
            response: json!({}),
        }
    }

    #[test]
    fn audit_retention_keeps_counters_and_recent_rows() {
        let mut view = MaterializedView::bounded();
        for timestamp_ms in 0..(MAX_AUDIT_EVENTS_IN_MEMORY as u64 + 5) {
            view.apply_audit_event(&audit_row(timestamp_ms));
        }

        let snapshot = view.export_snapshot(SnapshotOptions {
            audit_limit: MAX_AUDIT_EVENTS_IN_MEMORY + 10,
        });
        assert_eq!(
            snapshot.summary.audit_events,
            MAX_AUDIT_EVENTS_IN_MEMORY as i64 + 5
        );
        assert_eq!(snapshot.audit_events.len(), MAX_AUDIT_EVENTS_IN_MEMORY);
        assert_eq!(snapshot.audit_events[0].timestamp_ms, 5);
        assert_eq!(snapshot.summary.start_timestamp_ms, Some(0));
        assert_eq!(
            snapshot.summary.end_timestamp_ms,
            Some(MAX_AUDIT_EVENTS_IN_MEMORY as u64 + 4)
        );
    }

    #[test]
    fn resource_retention_keeps_counters() {
        let mut view = MaterializedView::bounded();
        for timestamp_ms in 0..(MAX_RESOURCE_SAMPLES_IN_MEMORY as u64 + 5) {
            view.apply_resource_sample(&ResourceSampleRow {
                timestamp_ms,
                pid: Some(1),
                comm: Some("test".to_string()),
                cpu_percent: Some(1.0),
                rss_mb: Some(2),
            });
        }

        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        assert_eq!(
            snapshot.summary.view_events,
            MAX_RESOURCE_SAMPLES_IN_MEMORY as i64 + 5
        );
        assert_eq!(
            snapshot.resource_samples.len(),
            MAX_RESOURCE_SAMPLES_IN_MEMORY
        );
        assert_eq!(snapshot.resource_samples[0].timestamp_ms, 5);
    }

    #[test]
    fn token_summary_groups_agent_native_tokens_by_session_dir() {
        let mut view = MaterializedView::new();
        view.upsert_session(&session_row("local:codex:session-1", "/repo/one"));
        view.apply_token_usage(&token_row(
            "token-1",
            "local:codex:session-1-gpt-5",
            "gpt-5",
            10,
            5,
            2,
            3,
            20,
        ));
        view.apply_token_usage(&token_row(
            "token-2",
            "local:codex:session-1-gpt-4",
            "gpt-4",
            7,
            2,
            0,
            1,
            10,
        ));

        let rows = view.token_summary("dir");

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].group, "/repo/one");
        assert_eq!(rows[0].input_tokens, 17);
        assert_eq!(rows[0].output_tokens, 7);
        assert_eq!(rows[0].cache_creation_tokens, 2);
        assert_eq!(rows[0].cache_read_tokens, 4);
        assert_eq!(rows[0].total_tokens, 30);
        assert_eq!(rows[0].calls, 2);
        assert_eq!(rows[0].sessions, 1);
    }

    #[test]
    fn token_summary_groups_saved_tokens_by_process_dir() {
        let mut view = MaterializedView::new();
        view.upsert_process_node(&process_node(42, "/repo/saved"));
        view.apply_llm_call(&llm_call_row("llm-1", 42, Some("session-1")));
        view.apply_token_usage(&TokenUsageRow {
            source: "response_usage".to_string(),
            view_source: "sqlite".to_string(),
            ..token_row("token-1", "llm-1", "claude-sonnet-4", 11, 13, 0, 0, 24)
        });

        let rows = view.token_summary("dir");

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].group, "/repo/saved");
        assert_eq!(rows[0].total_tokens, 24);
        assert_eq!(rows[0].sessions, 1);
    }

    #[test]
    fn gemini_stdout_tokens_are_fallback_for_network_usage() {
        let mut view = MaterializedView::new();
        view.apply_token_usage(&TokenUsageRow {
            pid: Some(42),
            comm: Some("node".to_string()),
            source: "response_usage".to_string(),
            ..token_row("token-network", "llm-network", "gemini", 11, 4, 0, 0, 15)
        });
        view.apply_token_usage(&TokenUsageRow {
            pid: Some(42),
            comm: Some("node".to_string()),
            source: "gemini_cli_stdout_stats".to_string(),
            ..token_row("token-stdout", "llm-stdout", "gemini", 11, 4, 0, 0, 15)
        });

        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.total_tokens, 15);
    }

    #[test]
    fn gemini_stdout_tokens_cover_partial_network_capture() {
        let mut view = MaterializedView::new();
        for (id, total) in [("one", 7), ("two", 8)] {
            view.apply_token_usage(&TokenUsageRow {
                pid: Some(42),
                source: "response_usage".to_string(),
                ..token_row(id, id, "gemini", total, 0, 0, 0, total)
            });
        }
        view.apply_token_usage(&TokenUsageRow {
            pid: Some(42),
            source: "gemini_cli_stdout_stats".to_string(),
            ..token_row("old-stdout", "old-stdout", "gemini", 15, 0, 0, 0, 15)
        });
        view.apply_token_usage(&TokenUsageRow {
            pid: Some(42),
            source: "gemini_cli_stdout_stats".to_string(),
            ..token_row("stdout", "stdout", "gemini", 30, 0, 0, 0, 30)
        });

        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.total_tokens, 30);
    }

    #[test]
    fn token_summary_groups_missing_dir_as_unknown() {
        let mut view = MaterializedView::new();
        view.apply_token_usage(&token_row("token-1", "llm-1", "gpt-5", 1, 2, 3, 4, 10));

        let rows = view.token_summary("dir");

        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].group, "unknown");
        assert_eq!(rows[0].total_tokens, 10);
        assert_eq!(rows[0].sessions, 0);
    }

    #[test]
    fn process_node_preserves_first_non_empty_argv() {
        let mut view = MaterializedView::new();
        let first = ProcessNodeRow {
            id: "pid:42:start:100".to_string(),
            pid: 42,
            start_ticks: Some(918_500),
            ppid: Some(1),
            root_pid: Some(42),
            start_timestamp_ms: Some(100),
            end_timestamp_ms: None,
            comm: Some("agent".to_string()),
            command: Some("agent".to_string()),
            argv: vec![
                "agent".to_string(),
                "--model".to_string(),
                "gpt-test".to_string(),
            ],
            cwd: Some("/tmp".to_string()),
            exit_code: None,
            status: Some("running".to_string()),
            view_source: "process".to_string(),
            confidence: Some(1.0),
        };
        let mut later = first.clone();
        later.end_timestamp_ms = Some(200);
        later.command = Some("agent-exit".to_string());
        later.argv = vec!["agent-exit".to_string()];
        later.exit_code = Some(0);
        later.status = Some("success".to_string());
        // The exit event has no task left to read ticks from.
        later.start_ticks = None;

        view.upsert_process_node(&first);
        view.upsert_process_node(&later);

        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        let row = snapshot.process_nodes.first().expect("process node");
        assert_eq!(row.argv, first.argv);
        assert_eq!(row.end_timestamp_ms, Some(200));
        assert_eq!(row.exit_code, Some(0));
        assert_eq!(row.start_ticks, Some(918_500));
    }

    fn annotation(revision: u64, decision: &str) -> AroAnnotation {
        AroAnnotation {
            scope_handle: "scope-1".to_string(),
            sequence: revision + 1,
            row: agentsight_protocol::bridge::AroAnnotationRow::PolicyDecision(
                agentsight_protocol::bridge::AroPolicyDecisionRow {
                    row_id: "policy-1".to_string(),
                    revision,
                    scope_handle: "scope-1".to_string(),
                    decision: decision.to_string(),
                    mode: Some("enforce".to_string()),
                    outcome: None,
                    rung: None,
                },
            ),
        }
    }

    #[test]
    fn annotations_are_stored_idempotently_and_read_back() {
        let mut view = MaterializedView::new();
        assert!(view.apply_aro_annotation(&annotation(0, "allow")));
        assert!(!view.apply_aro_annotation(&annotation(0, "deny")));
        assert!(view.apply_aro_annotation(&annotation(1, "deny")));

        let rows = view.aro_annotations();
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].row.revision(), 1);
        assert_eq!(view.aro_annotations_evicted(), 0);
    }

    #[test]
    fn annotations_never_become_mutations_or_observed_snapshot_rows() {
        let mut view = MaterializedView::new();
        view.apply_aro_annotation(&annotation(0, "allow"));
        assert!(
            view.bridge_snapshot_mutations(&DisclosureMode::MetadataOnly)
                .is_empty()
        );
        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.summary.audit_events, 0);
        assert!(snapshot.process_nodes.is_empty());
        // Served beside the observed rows, in their own field, counted in none
        // of the summary totals.
        assert_eq!(snapshot.aro_annotations.len(), 1);
        assert_eq!(snapshot.summary.view_events, 0);
    }

    /// The web API answers from a detached copy, so anything the copy drops is
    /// missing from every served snapshot.
    #[test]
    fn a_detached_copy_still_serves_the_annotations() {
        let mut view = MaterializedView::new();
        view.apply_aro_annotation(&annotation(0, "allow"));
        let snapshot = view
            .detached_copy()
            .export_snapshot(SnapshotOptions { audit_limit: 0 });
        assert_eq!(snapshot.aro_annotations.len(), 1);
    }

    #[test]
    fn a_snapshot_without_annotations_does_not_carry_the_field() {
        let view = MaterializedView::new();
        let snapshot = view.export_snapshot(SnapshotOptions { audit_limit: 0 });
        let json = serde_json::to_value(&snapshot).expect("snapshot serializes");
        assert!(json.get("aro_annotations").is_none());

        let mut annotated = MaterializedView::new();
        annotated.apply_aro_annotation(&annotation(0, "allow"));
        let json =
            serde_json::to_value(annotated.export_snapshot(SnapshotOptions { audit_limit: 0 }))
                .expect("snapshot serializes");
        assert_eq!(json["aro_annotations"][0]["row"]["kind"], "policy_decision");
    }
}
