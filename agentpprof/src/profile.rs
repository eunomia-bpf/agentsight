use anyhow::{Context, Result, bail};
use chrono::Utc;
use flate2::{Compression, write::GzEncoder};
use prost::Message;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use crate::session::{
    SessionRecord, collapse_project_path, contains_private_marker, path_component_strings,
    semantic_task_label, short_hash,
};

pub type Counter = BTreeMap<String, u64>;
pub type SignedCounter = BTreeMap<String, i64>;
pub type OpId = usize;
pub(crate) type Frame = (String, String);

pub struct StackNode {
    pub parent: Option<OpId>,
    pub kind: String,
    pub name: String,
    pub value: u64,
}

struct PprofProfileSample {
    stack: String,
    value: u64,
    labels: Vec<(String, String)>,
}

pub struct Profile {
    pub view: &'static str,
    pub sample_type: &'static str,
    pub unit: &'static str,
    pub ops: Vec<StackNode>,
    pub operation_stack_induction: Option<OperationStackInductionReport>,
    pprof_samples: Vec<PprofProfileSample>,
}

impl Profile {
    pub(crate) fn new(view: &'static str, sample_type: &'static str, unit: &'static str) -> Self {
        Self {
            view,
            sample_type,
            unit,
            ops: Vec::new(),
            operation_stack_induction: None,
            pprof_samples: Vec::new(),
        }
    }

    pub(crate) fn sample(&mut self, frames: Vec<Frame>, value: u64, labels: Vec<(String, String)>) {
        self.pprof_samples.push(PprofProfileSample {
            stack: folded_stack_from_frames(&frames),
            value,
            labels,
        });
        let last = frames.len().saturating_sub(1);
        let mut parent = None;
        for (idx, (kind, name)) in frames.into_iter().enumerate() {
            let id = self.ops.len();
            self.ops.push(StackNode {
                parent,
                kind,
                name,
                value: if idx == last { value } else { 0 },
            });
            parent = Some(id);
        }
    }
}

#[derive(Clone, Debug)]
pub struct OperationStackSpec {
    frames: Vec<String>,
}

impl OperationStackSpec {
    fn default_for_view(view: ProfileView) -> Self {
        let raw = match view {
            ProfileView::Operations => "task,skill,phase,action,object,repeat,result,outcome",
            ProfileView::Tokens => "task,skill,phase,action,object,repeat,result,outcome,token",
            ProfileView::Files | ProfileView::Network | ProfileView::Time => {
                "task,skill,phase,action,object,repeat,result,outcome"
            }
        };
        parse_stack_spec(raw).expect("default stack spec is valid")
    }

    pub fn contains_frame(&self, frame: &str) -> bool {
        self.frames.iter().any(|candidate| candidate == frame)
    }
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperationMarkFile {
    sequence_field: String,
    id_field: String,
    operation_names: BTreeMap<String, String>,
    marks: Vec<OperationMark>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct OperationMark {
    sequence: String,
    start_operation_id: String,
    operation_ids: Vec<String>,
}

#[derive(Clone)]
pub struct OperationStackRule {
    frame: String,
    label: String,
    pattern: String,
    regex: Regex,
}

impl std::fmt::Debug for OperationStackRule {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("OperationStackRule")
            .field("frame", &self.frame)
            .field("label", &self.label)
            .field("pattern", &self.pattern)
            .finish()
    }
}

#[derive(Clone, Debug)]
pub struct OperationStackConfig {
    stack: OperationStackSpec,
    field_rules: Vec<OperationStackRule>,
    filters: Vec<OperationFilterRule>,
    rules: Vec<OperationStackRule>,
    operation_marks: Option<OperationMarkFile>,
    operation_stack_induction: Option<OperationStackInductionConfig>,
}

impl OperationStackConfig {
    pub fn for_view(view: ProfileView) -> Self {
        Self {
            stack: OperationStackSpec::default_for_view(view),
            field_rules: Vec::new(),
            filters: Vec::new(),
            rules: Vec::new(),
            operation_marks: None,
            operation_stack_induction: None,
        }
    }

    pub fn with_stack(mut self, stack: OperationStackSpec) -> Self {
        self.stack = stack;
        self
    }

    pub fn with_rules(mut self, rules: Vec<OperationStackRule>) -> Self {
        self.rules = rules;
        self
    }

    pub fn with_field_rules(mut self, rules: Vec<OperationStackRule>) -> Self {
        self.field_rules = rules;
        self
    }

    pub fn with_filters(mut self, filters: Vec<OperationFilterRule>) -> Self {
        self.filters = filters;
        self
    }

    pub fn with_operation_marks(mut self, marks: OperationMarkFile) -> Self {
        self.operation_marks = Some(marks);
        self
    }

    pub fn with_operation_stack_induction(mut self, config: OperationStackInductionConfig) -> Self {
        self.operation_stack_induction = Some(config);
        self
    }
}

pub fn parse_operation_mark_file(raw: &str) -> Result<OperationMarkFile> {
    let marks: OperationMarkFile =
        serde_json::from_str(raw).context("invalid operation mark JSON")?;
    validate_operation_mark_file(&marks)?;
    Ok(marks)
}

fn validate_operation_mark_file(mark_file: &OperationMarkFile) -> Result<()> {
    if mark_file.sequence_field.trim().is_empty() {
        bail!("operation mark sequence_field must not be empty");
    }
    if mark_file.id_field.trim().is_empty() {
        bail!("operation mark id_field must not be empty");
    }
    if mark_file.operation_names.is_empty() {
        bail!("operation mark operation_names must not be empty");
    }
    let mut display_names = BTreeSet::new();
    let mut pprof_frame_names = BTreeMap::new();
    for (operation_id, display_name) in &mark_file.operation_names {
        if operation_id.trim().is_empty() || display_name.trim().is_empty() {
            bail!("operation mark IDs and display names must not be empty");
        }
        if !display_names.insert(display_name) {
            bail!("operation display name {display_name:?} is assigned to multiple IDs");
        }
        let pprof_name = safe_frame(display_name, Some(OPERATION_STACK_DERIVED_FIELD));
        if let Some(previous_id) = pprof_frame_names.insert(pprof_name.clone(), operation_id) {
            bail!(
                "semantic operation IDs {previous_id:?} and {operation_id:?} normalize to the same pprof frame {pprof_name:?}"
            );
        }
    }
    if mark_file.marks.is_empty() {
        bail!("operation mark file must contain at least one mark");
    }
    for mark in &mark_file.marks {
        if mark.sequence.trim().is_empty() || mark.start_operation_id.trim().is_empty() {
            bail!("operation mark sequence and start_operation_id must not be empty");
        }
        if mark.operation_ids.is_empty() {
            bail!(
                "operation mark at {:?}/{:?} must contain a nonempty operation_ids path",
                mark.sequence,
                mark.start_operation_id
            );
        }
        for operation_id in &mark.operation_ids {
            if !mark_file.operation_names.contains_key(operation_id) {
                bail!(
                    "operation mark at {:?}/{:?} refers to unknown semantic operation ID {:?}",
                    mark.sequence,
                    mark.start_operation_id,
                    operation_id
                );
            }
        }
    }
    Ok(())
}

#[derive(Clone, Debug)]
pub struct OperationStackInductionConfig {
    derived_field: String,
    reference_operations: Option<Vec<Operation>>,
    calibration_operations: Option<Vec<Operation>>,
}

impl OperationStackInductionConfig {
    pub fn new() -> Self {
        Self {
            derived_field: OPERATION_STACK_DERIVED_FIELD.to_string(),
            reference_operations: None,
            calibration_operations: None,
        }
    }

    pub fn with_derived_field(mut self, derived_field: impl Into<String>) -> Self {
        self.derived_field = derived_field.into();
        self
    }

    pub fn with_reference_operation_records(mut self, records: &[Value]) -> Result<Self> {
        let mut operations = Vec::new();
        for (index, record) in records.iter().enumerate() {
            let record: OperationRecord =
                serde_json::from_value(record.clone()).map_err(|error| {
                    anyhow::anyhow!(
                        "invalid induction reference operation record {}: {error}",
                        index + 1
                    )
                })?;
            operations.push(operation_from_record(record).map_err(|error| {
                anyhow::anyhow!(
                    "invalid induction reference operation fields {}: {error}",
                    index + 1
                )
            })?);
        }
        if operations.is_empty() {
            bail!("induction reference operation input produced no samples");
        }
        self.reference_operations = Some(operations);
        Ok(self)
    }

    pub fn with_calibration_operation_records(mut self, records: &[Value]) -> Result<Self> {
        let mut operations = Vec::new();
        for (index, record) in records.iter().enumerate() {
            let record: OperationRecord =
                serde_json::from_value(record.clone()).map_err(|error| {
                    anyhow::anyhow!(
                        "invalid induction calibration operation record {}: {error}",
                        index + 1
                    )
                })?;
            operations.push(operation_from_record(record).map_err(|error| {
                anyhow::anyhow!(
                    "invalid induction calibration operation fields {}: {error}",
                    index + 1
                )
            })?);
        }
        if operations.is_empty() {
            bail!("induction calibration operation input produced no samples");
        }
        self.calibration_operations = Some(operations);
        Ok(self)
    }
}

impl Default for OperationStackInductionConfig {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct OperationStackInductionReport {
    policy: &'static str,
    objective: &'static str,
    derived_stack_field: String,
    sequence_field: &'static str,
    association_field: &'static str,
    transition_weighting: &'static str,
    reference_source: &'static str,
    reference_sessions: usize,
    reference_operations: usize,
    reference_transitions: usize,
    target_sessions: usize,
    target_operations: usize,
    same_action_reference_transitions: usize,
    action_change_reference_transitions: usize,
    cutoff: f64,
    low_center: f64,
    high_center: f64,
    low_occurrences: usize,
    high_occurrences: usize,
    two_means_iterations: usize,
    global_cutoff: f64,
    global_low_center: f64,
    global_high_center: f64,
    global_low_occurrences: usize,
    global_high_occurrences: usize,
    global_two_means_iterations: usize,
    cross_action_cutoff: f64,
    cross_action_applied_cutoff: f64,
    cross_action_low_center: f64,
    cross_action_high_center: f64,
    cross_action_low_occurrences: usize,
    cross_action_high_occurrences: usize,
    cross_action_two_means_iterations: usize,
    removed_current_boundaries: usize,
    added_current_boundaries: usize,
    unseen_target_transitions: usize,
    predicted_groups: usize,
    unique_motifs: usize,
    selected_evidence_fields: Vec<String>,
    selected_source_fields: Vec<String>,
    excluded_oracle_fields: Vec<&'static str>,
    excluded_oracle_prefixes: Vec<&'static str>,
    excluded_oracle_suffixes: Vec<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    supervised_calibration: Option<SupervisedRecurrenceCalibrationReport>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_recurrence: Option<OperationStackDetailRecurrenceReport>,
    boundary_decisions: Vec<OperationStackBoundaryDecision>,
    segments: Vec<OperationStackSegment>,
}

#[derive(Clone, Debug, Serialize)]
pub struct OperationStackDetailRecurrenceReport {
    association_field: &'static str,
    signature: &'static str,
    reference_transitions: usize,
    same_signature_reference_transitions: usize,
    signature_change_reference_transitions: usize,
    global_cutoff: f64,
    global_low_center: f64,
    global_high_center: f64,
    global_low_occurrences: usize,
    global_high_occurrences: usize,
    global_two_means_iterations: usize,
    signature_change_cutoff: f64,
    signature_change_applied_cutoff: f64,
    signature_change_low_center: f64,
    signature_change_high_center: f64,
    signature_change_low_occurrences: usize,
    signature_change_high_occurrences: usize,
    signature_change_two_means_iterations: usize,
    seen_target_transitions: usize,
    unseen_target_transitions: usize,
    rescued_coarse_boundaries: usize,
    added_coarse_boundaries: usize,
}

#[derive(Clone, Debug, Serialize)]
pub struct SupervisedRecurrenceCalibrationReport {
    policy: &'static str,
    objective: &'static str,
    group_field: &'static str,
    sessions: usize,
    operations: usize,
    transitions: usize,
    groups: usize,
    observed_transitions: usize,
    unseen_transitions: usize,
    distinct_scores: usize,
    candidate_cutoffs: usize,
    best_ties: usize,
    selected_cutoff: f64,
    selected_precision: f64,
    selected_recall: f64,
    selected_f1: f64,
}

#[derive(Clone, Debug, Serialize)]
pub struct OperationStackBoundaryDecision {
    session: String,
    position: usize,
    left_action: String,
    right_action: String,
    npmi: Option<f64>,
    unseen_in_reference: bool,
    calibration_population: &'static str,
    applied_cutoff: f64,
    current_boundary: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    label_free_applied_cutoff: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    label_free_boundary: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    left_action_detail: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    right_action_detail: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_npmi: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_unseen_in_reference: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_calibration_population: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_applied_cutoff: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_continuity: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    coarse_boundary: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail_rescued_coarse_boundary: Option<bool>,
    boundary: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct OperationStackSegment {
    session: String,
    start: usize,
    end: usize,
    motif: String,
}

#[derive(Clone)]
pub struct OperationFilterRule {
    field: String,
    pattern: String,
    negated: bool,
    regex: Regex,
}

impl std::fmt::Debug for OperationFilterRule {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("OperationFilterRule")
            .field("field", &self.field)
            .field("pattern", &self.pattern)
            .field("negated", &self.negated)
            .finish()
    }
}

#[derive(Clone, Debug)]
struct Operation {
    fields: BTreeMap<String, Vec<String>>,
    value: u64,
}

impl Operation {
    fn new(value: u64) -> Self {
        Self {
            fields: BTreeMap::new(),
            value,
        }
    }

    fn insert(&mut self, key: &str, value: impl Into<String>) {
        let value = value.into();
        if !value.is_empty() {
            self.fields.entry(key.to_string()).or_default().push(value);
        }
    }

    fn extend(&mut self, key: &str, values: impl IntoIterator<Item = String>) {
        for value in values {
            self.insert(key, value);
        }
    }

    fn values(&self, key: &str) -> &[String] {
        self.fields.get(key).map(Vec::as_slice).unwrap_or(&[])
    }

    fn searchable_text(&self) -> String {
        self.fields
            .iter()
            .flat_map(|(key, values)| values.iter().map(move |value| format!("{key}={value}")))
            .collect::<Vec<_>>()
            .join(" ")
    }
}

const PPROF_EVIDENCE_LABEL_FIELDS: &[&str] = &[
    "source_kind",
    "evidence_id",
    "operation_start_id",
    "agent",
    "status",
    "response_phase",
    "outcome",
    "source_session",
    "call_id",
    "prompt_hash",
    "response_hash",
    "timestamp_ms",
    "skill",
    "comparison_side",
];

fn pprof_evidence_labels(operation: &Operation) -> Vec<(String, String)> {
    PPROF_EVIDENCE_LABEL_FIELDS
        .iter()
        .flat_map(|field| {
            operation
                .values(field)
                .iter()
                .map(move |value| ((*field).to_string(), safe_frame(value, None)))
        })
        .collect()
}

#[derive(Clone, Deserialize)]
struct OperationRecord {
    #[serde(default)]
    value: Option<u64>,
    #[serde(default)]
    fields: BTreeMap<String, Value>,
    #[serde(flatten)]
    extra_fields: BTreeMap<String, Value>,
}

pub fn parse_stack_spec(raw: &str) -> Result<OperationStackSpec> {
    let mut frames = Vec::new();
    for part in raw.split([',', ';']) {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        validate_frame_name(part, "stack frame")?;
        frames.push(part.to_string());
    }
    if frames.is_empty() {
        bail!("stack spec cannot be empty");
    }
    Ok(OperationStackSpec { frames })
}

pub fn parse_stack_rules(raw_rules: &[String]) -> Result<Vec<OperationStackRule>> {
    parse_stack_rules_with_flag(raw_rules, "--stack-rule")
}

pub fn parse_stack_rules_with_flag(
    raw_rules: &[String],
    flag_name: &str,
) -> Result<Vec<OperationStackRule>> {
    raw_rules
        .iter()
        .map(|rule| parse_stack_rule(rule, flag_name))
        .collect()
}

fn parse_stack_rule(raw: &str, flag_name: &str) -> Result<OperationStackRule> {
    let (left, pattern) = raw.split_once('=').ok_or_else(|| {
        anyhow::anyhow!("invalid {flag_name} {raw:?}; expected FRAME:LABEL=REGEX")
    })?;
    let (frame, label) = left.split_once(':').ok_or_else(|| {
        anyhow::anyhow!("invalid {flag_name} {raw:?}; expected FRAME:LABEL=REGEX")
    })?;
    validate_frame_name(frame, "stack frame")?;
    validate_frame_name(label, "stack label")?;
    if pattern.is_empty() {
        bail!("invalid {flag_name} {raw:?}; regex pattern cannot be empty");
    }
    let regex = Regex::new(pattern)
        .map_err(|error| anyhow::anyhow!("invalid {flag_name} regex {pattern:?}: {error}"))?;
    Ok(OperationStackRule {
        frame: frame.to_string(),
        label: label.to_string(),
        pattern: pattern.to_string(),
        regex,
    })
}

pub fn parse_operation_filters(raw_filters: &[String]) -> Result<Vec<OperationFilterRule>> {
    parse_operation_filters_with_flag(raw_filters, "--where")
}

pub fn parse_operation_filters_with_flag(
    raw_filters: &[String],
    flag_name: &str,
) -> Result<Vec<OperationFilterRule>> {
    raw_filters
        .iter()
        .map(|rule| parse_operation_filter(rule, flag_name))
        .collect()
}

fn parse_operation_filter(raw: &str, flag_name: &str) -> Result<OperationFilterRule> {
    let (field, pattern, negated) = if let Some((field, pattern)) = raw.split_once("!=") {
        (field, pattern, true)
    } else if let Some((field, pattern)) = raw.split_once('=') {
        (field, pattern, false)
    } else {
        bail!("invalid {flag_name} {raw:?}; expected FIELD=REGEX or FIELD!=REGEX");
    };
    let field = field.trim();
    validate_frame_name(field, "operation filter field")?;
    if pattern.is_empty() {
        bail!("invalid {flag_name} {raw:?}; regex pattern cannot be empty");
    }
    let regex = Regex::new(pattern)
        .map_err(|error| anyhow::anyhow!("invalid {flag_name} regex {pattern:?}: {error}"))?;
    Ok(OperationFilterRule {
        field: field.to_string(),
        pattern: pattern.to_string(),
        negated,
        regex,
    })
}

fn validate_frame_name(value: &str, what: &str) -> Result<()> {
    if value.is_empty() {
        bail!("{what} cannot be empty");
    }
    if !value
        .chars()
        .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit() || ch == '_' || ch == '-')
    {
        bail!("{what} {value:?} must contain only lowercase letters, digits, '_' or '-'");
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProfileView {
    Operations,
    Tokens,
    Files,
    Network,
    Time,
}

#[derive(Clone, PartialEq, Message)]
struct PprofProfile {
    #[prost(message, repeated, tag = "1")]
    sample_type: Vec<PprofValueType>,
    #[prost(message, repeated, tag = "2")]
    sample: Vec<PprofSample>,
    #[prost(message, repeated, tag = "4")]
    location: Vec<PprofLocation>,
    #[prost(message, repeated, tag = "5")]
    function: Vec<PprofFunction>,
    #[prost(string, repeated, tag = "6")]
    string_table: Vec<String>,
    #[prost(int64, tag = "9")]
    time_nanos: i64,
    #[prost(int64, tag = "10")]
    duration_nanos: i64,
    #[prost(int64, tag = "15")]
    default_sample_type: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofValueType {
    #[prost(int64, tag = "1")]
    type_: i64,
    #[prost(int64, tag = "2")]
    unit: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofSample {
    #[prost(uint64, repeated, tag = "1")]
    location_id: Vec<u64>,
    #[prost(int64, repeated, tag = "2")]
    value: Vec<i64>,
    #[prost(message, repeated, tag = "3")]
    label: Vec<PprofLabel>,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLabel {
    #[prost(int64, tag = "1")]
    key: i64,
    #[prost(int64, tag = "2")]
    str_value: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLocation {
    #[prost(uint64, tag = "1")]
    id: u64,
    #[prost(message, repeated, tag = "4")]
    line: Vec<PprofLine>,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLine {
    #[prost(uint64, tag = "1")]
    function_id: u64,
    #[prost(int64, tag = "2")]
    line: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofFunction {
    #[prost(uint64, tag = "1")]
    id: u64,
    #[prost(int64, tag = "2")]
    name: i64,
    #[prost(int64, tag = "3")]
    system_name: i64,
    #[prost(int64, tag = "4")]
    filename: i64,
}

#[derive(Default)]
struct StringInterner {
    items: Vec<String>,
    index: BTreeMap<String, i64>,
}

impl StringInterner {
    fn with_pprof_root() -> Self {
        let mut out = Self::default();
        out.intern("");
        out
    }

    fn intern(&mut self, value: &str) -> i64 {
        if let Some(existing) = self.index.get(value) {
            return *existing;
        }
        let id = i64::try_from(self.items.len()).unwrap_or(i64::MAX);
        self.items.push(value.to_string());
        self.index.insert(value.to_string(), id);
        id
    }
}

pub fn build_profile_with_options(
    sessions: &[SessionRecord],
    project_name: &str,
    view: ProfileView,
    options: &OperationStackConfig,
) -> Result<Profile> {
    let (name, sample_type, unit) = view_metadata(view);
    let mut profile = Profile::new(name, sample_type, unit);
    let mut samples = Vec::new();
    for session in sessions {
        for sample in session_samples(session, project_name, view) {
            samples.push(apply_operation_field_rules(&sample, &options.field_rules));
        }
    }
    apply_operation_marks(&mut samples, options)?;
    samples.retain(|sample| operation_matches_filters(sample, &options.filters));
    let (mut samples, report) = maybe_induce_operation_stack(samples, options)?;
    samples.retain(|sample| sample.value > 0);
    profile.operation_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let labels = pprof_evidence_labels(&sample);
        profile.sample(frames, sample.value, labels);
    }
    Ok(profile)
}

#[cfg(test)]
pub fn build_profile_from_operation_files(
    paths: &[PathBuf],
    view: ProfileView,
    options: &OperationStackConfig,
) -> Result<Profile> {
    let mut operations = Vec::new();
    for path in paths {
        operations.extend(read_operation_jsonl(path)?);
    }
    if operations.is_empty() {
        bail!("operation input produced no samples");
    }
    build_profile_from_operations(&operations, view, options)
}

pub fn read_operation_record_values(paths: &[PathBuf]) -> Result<Vec<Value>> {
    let mut records = Vec::new();
    for path in paths {
        for record in read_operation_records_jsonl(path)? {
            operation_from_record(record.clone())
                .with_context(|| format!("invalid operation fields in {}", path.display()))?;
            records.push(operation_record_to_value(record));
        }
    }
    if records.is_empty() {
        bail!("operation input produced no samples");
    }
    Ok(records)
}

pub fn build_profile_from_operation_records(
    records: &[Value],
    view: ProfileView,
    options: &OperationStackConfig,
) -> Result<Profile> {
    let mut operations = Vec::new();
    for (index, record) in records.iter().enumerate() {
        let record: OperationRecord = serde_json::from_value(record.clone()).map_err(|error| {
            anyhow::anyhow!("invalid imported operation record {}: {error}", index + 1)
        })?;
        operations.push(operation_from_record(record).map_err(|error| {
            anyhow::anyhow!("invalid imported operation fields {}: {error}", index + 1)
        })?);
    }
    if operations.is_empty() {
        bail!("operation input produced no samples");
    }
    build_profile_from_operations(&operations, view, options)
}

fn build_profile_from_operations(
    operations: &[Operation],
    view: ProfileView,
    options: &OperationStackConfig,
) -> Result<Profile> {
    let (name, sample_type, unit) = view_metadata(view);
    let mut profile = Profile::new(name, sample_type, unit);
    let mut samples = operations
        .iter()
        .map(|sample| apply_operation_field_rules(sample, &options.field_rules))
        .collect::<Vec<_>>();
    apply_operation_marks(&mut samples, options)?;
    samples.retain(|sample| operation_matches_filters(sample, &options.filters));
    let (mut samples, report) = maybe_induce_operation_stack(samples, options)?;
    samples.retain(|sample| sample.value > 0);
    profile.operation_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let labels = pprof_evidence_labels(&sample);
        profile.sample(frames, sample.value, labels);
    }
    Ok(profile)
}

fn apply_operation_marks(samples: &mut [Operation], options: &OperationStackConfig) -> Result<()> {
    let Some(mark_file) = options.operation_marks.as_ref() else {
        return Ok(());
    };
    if options.operation_stack_induction.is_some() {
        bail!("operation marks cannot be combined with operation-stack induction");
    }

    let mut sequences: BTreeMap<String, Vec<usize>> = BTreeMap::new();
    let mut normalized_sequences: BTreeMap<String, String> = BTreeMap::new();
    let mut source_ids: BTreeMap<String, BTreeMap<String, usize>> = BTreeMap::new();
    let mut normalized_source_ids: BTreeMap<String, BTreeMap<String, String>> = BTreeMap::new();
    for (index, sample) in samples.iter().enumerate() {
        let sequence = operation_single_nonempty_value(
            sample,
            &mark_file.sequence_field,
            "operation mark input",
        )?;
        let source_id =
            operation_single_nonempty_value(sample, &mark_file.id_field, "operation mark input")?;
        if !sequences.contains_key(&sequence) {
            let normalized_sequence = safe_frame(&sequence, None);
            if let Some(previous_sequence) =
                normalized_sequences.insert(normalized_sequence.clone(), sequence.clone())
            {
                bail!(
                    "input sequences {previous_sequence:?} and {sequence:?} normalize to the same pprof source_session label {normalized_sequence:?}"
                );
            }
        }
        let sequence_positions = sequences.entry(sequence.clone()).or_default();
        let position = sequence_positions.len();
        sequence_positions.push(index);
        if source_ids
            .entry(sequence.clone())
            .or_default()
            .insert(source_id.clone(), position)
            .is_some()
        {
            bail!(
                "operation mark input has duplicate source operation ID {source_id:?} in sequence {sequence:?}"
            );
        }
        let normalized_source_id = safe_frame(&source_id, None);
        if let Some(previous_id) = normalized_source_ids
            .entry(sequence.clone())
            .or_default()
            .insert(normalized_source_id.clone(), source_id.clone())
        {
            bail!(
                "source operation IDs {previous_id:?} and {source_id:?} in sequence {sequence:?} normalize to the same pprof evidence label {normalized_source_id:?}"
            );
        }
    }

    let mut marks_by_sequence: BTreeMap<String, Vec<&OperationMark>> = BTreeMap::new();
    for mark in &mark_file.marks {
        marks_by_sequence
            .entry(mark.sequence.clone())
            .or_default()
            .push(mark);
    }
    if let Some(unused_sequence) = marks_by_sequence
        .keys()
        .find(|sequence| !sequences.contains_key(*sequence))
    {
        bail!("operation mark file refers to unknown input sequence {unused_sequence:?}");
    }

    for (sequence, indices) in sequences {
        let marks = marks_by_sequence.get(&sequence).ok_or_else(|| {
            anyhow::anyhow!("operation mark file has no marks for input sequence {sequence:?}")
        })?;
        let positions = &source_ids[&sequence];
        let first_source_id = operation_single_nonempty_value(
            &samples[indices[0]],
            &mark_file.id_field,
            "operation mark input",
        )?;
        if marks[0].start_operation_id != first_source_id {
            bail!(
                "first operation mark for sequence {sequence:?} must start at first source operation ID {first_source_id:?}"
            );
        }

        let mut previous_position = None;
        let mut resolved = Vec::with_capacity(marks.len());
        for mark in marks {
            let Some(position) = positions.get(&mark.start_operation_id).copied() else {
                bail!(
                    "operation mark for sequence {sequence:?} refers to unknown source operation ID {:?}",
                    mark.start_operation_id
                );
            };
            if previous_position.is_some_and(|previous| position <= previous) {
                bail!(
                    "operation marks for sequence {sequence:?} must be unique and ordered by source position"
                );
            }
            previous_position = Some(position);
            let operation_path = mark
                .operation_ids
                .iter()
                .map(|operation_id| mark_file.operation_names[operation_id].clone())
                .collect::<Vec<_>>();
            resolved.push((position, mark.start_operation_id.clone(), operation_path));
        }

        for (mark_index, (start, operation_start_id, operation_path)) in resolved.iter().enumerate()
        {
            let end = resolved
                .get(mark_index + 1)
                .map(|(position, _, _)| *position)
                .unwrap_or(indices.len());
            for source_index in indices.iter().take(end).skip(*start).copied() {
                let source_id = operation_single_nonempty_value(
                    &samples[source_index],
                    &mark_file.id_field,
                    "operation mark input",
                )?;
                samples[source_index]
                    .fields
                    .insert("source_session".to_string(), vec![sequence.clone()]);
                samples[source_index].fields.insert(
                    "operation_start_id".to_string(),
                    vec![operation_start_id.clone()],
                );
                samples[source_index]
                    .fields
                    .insert("evidence_id".to_string(), vec![source_id]);
                samples[source_index].fields.insert(
                    OPERATION_STACK_DERIVED_FIELD.to_string(),
                    operation_path.clone(),
                );
            }
        }
    }
    Ok(())
}

fn operation_single_nonempty_value(
    operation: &Operation,
    field: &str,
    context: &str,
) -> Result<String> {
    let values = operation.values(field);
    if values.len() != 1 || values[0].trim().is_empty() {
        bail!("{context} requires exactly one nonempty {field:?} value per source operation");
    }
    Ok(values[0].clone())
}

#[cfg(test)]
fn read_operation_jsonl(path: &Path) -> Result<Vec<Operation>> {
    read_operation_records_jsonl(path)?
        .into_iter()
        .enumerate()
        .map(|(index, record)| {
            operation_from_record(record).map_err(|error| {
                anyhow::anyhow!(
                    "invalid operation fields at {}:{}: {error}",
                    path.display(),
                    index + 1
                )
            })
        })
        .collect()
}

fn read_operation_records_jsonl(path: &Path) -> Result<Vec<OperationRecord>> {
    let file = fs::File::open(path)?;
    let mut records = Vec::new();
    for (line_number, line) in BufReader::new(file).lines().enumerate() {
        let line = line?;
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let record: OperationRecord = serde_json::from_str(line).map_err(|error| {
            anyhow::anyhow!(
                "invalid operation JSONL at {}:{}: {error}",
                path.display(),
                line_number + 1
            )
        })?;
        records.push(record);
    }
    Ok(records)
}

fn operation_record_to_value(record: OperationRecord) -> Value {
    let mut fields = record.fields;
    fields.extend(record.extra_fields);
    json!({
        "value": record.value.unwrap_or(1),
        "fields": fields,
    })
}

fn operation_from_record(record: OperationRecord) -> Result<Operation> {
    let mut operation = Operation::new(record.value.unwrap_or(1));
    for (key, value) in record.fields {
        insert_json_field(&mut operation, &key, value)?;
    }
    for (key, value) in record.extra_fields {
        insert_json_field(&mut operation, &key, value)?;
    }
    Ok(operation)
}

fn insert_json_field(operation: &mut Operation, key: &str, value: Value) -> Result<()> {
    match value {
        Value::Null => {}
        Value::Bool(value) => operation.insert(key, value.to_string()),
        Value::Number(value) => operation.insert(key, value.to_string()),
        Value::String(value) => operation.insert(key, value),
        Value::Array(values) => {
            for value in values {
                insert_json_field(operation, key, value)?;
            }
        }
        object @ Value::Object(_) => operation.insert(key, serde_json::to_string(&object)?),
    }
    Ok(())
}

fn view_metadata(view: ProfileView) -> (&'static str, &'static str, &'static str) {
    match view {
        ProfileView::Operations => ("operations", "operations", "count"),
        ProfileView::Tokens => ("tokens", "tokens", "count"),
        ProfileView::Files => ("files", "file_events", "count"),
        ProfileView::Network => ("network", "network_events", "count"),
        ProfileView::Time => ("time", "duration", "seconds"),
    }
}

fn frame(kind: &str, value: impl Into<String>) -> Frame {
    (kind.to_string(), value.into())
}

fn stack_frames(sample: &Operation, options: &OperationStackConfig) -> Vec<Frame> {
    let mut frames = Vec::new();
    for name in &options.stack.frames {
        let rules: &[OperationStackRule] =
            if options.operation_marks.is_some() && name == OPERATION_STACK_DERIVED_FIELD {
                &[]
            } else {
                &options.rules
            };
        for value in stack_frame_values(name, sample, rules) {
            frames.push(frame(name, value));
        }
    }
    frames
}

fn apply_operation_field_rules(sample: &Operation, rules: &[OperationStackRule]) -> Operation {
    if rules.is_empty() {
        return sample.clone();
    }
    let mut mapped = sample.clone();
    let mut claimed_fields = BTreeSet::new();
    for rule in rules {
        if claimed_fields.contains(&rule.frame) {
            continue;
        }
        if rule.regex.is_match(&mapped.searchable_text()) {
            mapped
                .fields
                .insert(rule.frame.clone(), vec![rule.label.clone()]);
            claimed_fields.insert(rule.frame.clone());
        }
    }
    mapped
}

const OPERATION_STACK_POLICY: &str =
    "cross-session-action-transition-npmi-operation-stack-induction";
const OPERATION_STACK_OBJECTIVE: &str =
    "recurring adjacent visible actions define operation continuity across sessions";
const OPERATION_STACK_DERIVED_FIELD: &str = "operation";
const OPERATION_STACK_SEQUENCE_FIELD: &str = "session";
const OPERATION_STACK_ASSOCIATION_FIELD: &str = "action";
const OPERATION_STACK_DETAIL_FIELD: &str = "action_detail";
const OPERATION_STACK_CALIBRATION_GROUP_FIELD: &str = "group";
const ORACLE_OR_LABEL_FIELDS: &[&str] = &[
    "annotator",
    "attack",
    "attack_type",
    "boundary_label",
    "boundary_positive",
    "correct",
    "expected_action",
    "gold",
    "gold_action",
    "group",
    "group_id",
    "group_pattern",
    "human_boundary",
    "human_group",
    "label",
    "looping",
    "optimality",
    "oracle",
    "problem_oracle",
    "problem_value",
    "redundant",
    "reference",
    "reference_action",
    "safe",
    "safety",
    "side_effect",
    "status",
    "step_correct",
    "step_optimal",
    "step_redundant",
    "step_success",
    "target_positive",
    "unsafe",
];
const ORACLE_OR_LABEL_PREFIXES: &[&str] = &[
    "gold_",
    "group_",
    "human_",
    "label_",
    "oracle_",
    "problem_",
    "reference_",
    "target_",
];
const ORACLE_OR_LABEL_SUFFIXES: &[&str] = &[
    "_answer",
    "_attack",
    "_correct",
    "_gold",
    "_ground_truth",
    "_label",
    "_oracle",
    "_positive",
    "_redundant",
    "_reference",
    "_safe",
    "_safety",
    "_target",
    "_unsafe",
];
fn maybe_induce_operation_stack(
    samples: Vec<Operation>,
    options: &OperationStackConfig,
) -> Result<(Vec<Operation>, Option<OperationStackInductionReport>)> {
    let Some(config) = options.operation_stack_induction.as_ref() else {
        return Ok((samples, None));
    };
    let (samples, report) = induce_operation_stack(samples, config)?;
    Ok((samples, Some(report)))
}

fn induce_operation_stack(
    mut samples: Vec<Operation>,
    config: &OperationStackInductionConfig,
) -> Result<(Vec<Operation>, OperationStackInductionReport)> {
    let reference_is_external = config.reference_operations.is_some();
    let reference = config.reference_operations.as_deref().unwrap_or(&samples);
    let reference_groups = recurrence_groups(reference, "induction reference")?;
    let model = recurrence_model(reference, &reference_groups, None)?;
    let reference_sessions = reference_groups.len();
    let reference_operations = reference.len();
    let target_groups = recurrence_groups(&samples, "induction target")?;
    let supervised_calibration = if let Some(calibration) = config.calibration_operations.as_deref()
    {
        let calibration_groups = recurrence_groups(calibration, "induction calibration")?;
        if let Some(overlap) = calibration_groups
            .keys()
            .find(|session| target_groups.contains_key(*session))
        {
            bail!("induction calibration session {overlap:?} overlaps the induction target");
        }
        Some(fit_supervised_recurrence_cutoff(
            calibration,
            &calibration_groups,
            &model,
        )?)
    } else {
        None
    };
    let detail_enabled = supervised_calibration.is_none()
        && recurrence_uniform_detail(reference, "induction reference")?
        && recurrence_uniform_detail(&samples, "induction target")?;
    let detail_model = detail_enabled
        .then(|| {
            recurrence_model(
                reference,
                &reference_groups,
                Some(OPERATION_STACK_DETAIL_FIELD),
            )
        })
        .transpose()?;

    let mut decisions = Vec::new();
    let mut pending_segments = Vec::new();
    for (session, indices) in &target_groups {
        let mut boundaries = vec![0];
        for position in 1..indices.len() {
            let left_action = operation_single_value(
                &samples[indices[position - 1]],
                OPERATION_STACK_ASSOCIATION_FIELD,
                "induction target",
            )?;
            let right_action = operation_single_value(
                &samples[indices[position]],
                OPERATION_STACK_ASSOCIATION_FIELD,
                "induction target",
            )?;
            let left_state =
                recurrence_state(&samples[indices[position - 1]], None, "induction target")?;
            let right_state =
                recurrence_state(&samples[indices[position]], None, "induction target")?;
            let npmi = model
                .association
                .get(&(left_state.clone(), right_state.clone()))
                .copied();
            let current_boundary = npmi.is_none_or(|score| score < model.global.cutoff);
            let label_free_applied_cutoff =
                recurrence_applied_cutoff(&model, &left_state, &right_state);
            let label_free_boundary = npmi.is_none_or(|score| score < label_free_applied_cutoff);
            let (calibration_population, applied_cutoff) =
                if let Some(calibration) = supervised_calibration.as_ref() {
                    ("reference-group-bcubed", calibration.selected_cutoff)
                } else if left_action == right_action {
                    ("all-transitions", model.global.cutoff)
                } else {
                    (
                        "monotone-action-changing-transitions",
                        label_free_applied_cutoff,
                    )
                };
            let coarse_boundary = npmi.is_none_or(|score| score < applied_cutoff);
            let (
                left_action_detail,
                right_action_detail,
                detail_npmi,
                detail_unseen_in_reference,
                detail_calibration_population,
                detail_applied_cutoff,
                detail_continuity,
            ) = if let Some(detail_model) = detail_model.as_ref() {
                let left_detail_state = recurrence_state(
                    &samples[indices[position - 1]],
                    Some(OPERATION_STACK_DETAIL_FIELD),
                    "induction target",
                )?;
                let right_detail_state = recurrence_state(
                    &samples[indices[position]],
                    Some(OPERATION_STACK_DETAIL_FIELD),
                    "induction target",
                )?;
                let score = detail_model
                    .association
                    .get(&(left_detail_state.clone(), right_detail_state.clone()))
                    .copied();
                let cutoff = recurrence_applied_cutoff(
                    detail_model,
                    &left_detail_state,
                    &right_detail_state,
                );
                let continuity = score.is_some_and(|value| value >= cutoff);
                let population = if left_detail_state == right_detail_state {
                    "all-detail-transitions"
                } else {
                    "monotone-detail-changing-transitions"
                };
                (
                    left_detail_state.detail,
                    right_detail_state.detail,
                    score,
                    Some(score.is_none()),
                    Some(population),
                    Some(cutoff),
                    Some(continuity),
                )
            } else {
                (None, None, None, None, None, None, None)
            };
            let boundary = coarse_boundary && !detail_continuity.unwrap_or(false);
            let detail_rescued_coarse_boundary =
                detail_enabled.then_some(coarse_boundary && !boundary);
            if boundary {
                boundaries.push(position);
            }
            decisions.push(OperationStackBoundaryDecision {
                session: session.clone(),
                position,
                left_action: left_action.to_string(),
                right_action: right_action.to_string(),
                npmi,
                unseen_in_reference: npmi.is_none(),
                calibration_population,
                applied_cutoff,
                current_boundary,
                label_free_applied_cutoff: supervised_calibration
                    .as_ref()
                    .map(|_| label_free_applied_cutoff),
                label_free_boundary: supervised_calibration.as_ref().map(|_| label_free_boundary),
                left_action_detail,
                right_action_detail,
                detail_npmi,
                detail_unseen_in_reference,
                detail_calibration_population,
                detail_applied_cutoff,
                detail_continuity,
                coarse_boundary: detail_enabled.then_some(coarse_boundary),
                detail_rescued_coarse_boundary,
                boundary,
            });
        }
        boundaries.push(indices.len());
        for pair in boundaries.windows(2) {
            let start = pair[0];
            let end = pair[1];
            let motif = recurrence_motif(&samples, &indices[start..end])?;
            pending_segments.push((
                session.clone(),
                start,
                end,
                motif,
                indices[start..end].to_vec(),
            ));
        }
    }

    let motif_labels = disambiguate_recurrence_motifs(
        pending_segments
            .iter()
            .map(|(_, _, _, motif, _)| motif.as_str()),
        &config.derived_field,
    );
    let mut segments = Vec::new();
    let mut unique_motifs = BTreeSet::new();
    for (session, start, end, raw_motif, indices) in pending_segments {
        let motif = motif_labels
            .get(&raw_motif)
            .cloned()
            .context("missing disambiguated recurrence motif")?;
        unique_motifs.insert(motif.clone());
        for index in indices {
            samples[index]
                .fields
                .insert(config.derived_field.clone(), vec![motif.clone()]);
        }
        segments.push(OperationStackSegment {
            session,
            start,
            end,
            motif,
        });
    }

    if decisions
        .iter()
        .any(|decision| decision.coarse_boundary == Some(false) && decision.boundary)
    {
        bail!("detail recurrence added a coarse-relative boundary");
    }
    let mut selected_evidence_fields = vec![OPERATION_STACK_ASSOCIATION_FIELD.to_string()];
    if detail_enabled {
        selected_evidence_fields.push(OPERATION_STACK_DETAIL_FIELD.to_string());
    }
    let detail_recurrence = detail_model.as_ref().map(|detail_model| {
        let seen_target_transitions = decisions
            .iter()
            .filter(|decision| decision.detail_unseen_in_reference == Some(false))
            .count();
        let unseen_target_transitions = decisions
            .iter()
            .filter(|decision| decision.detail_unseen_in_reference == Some(true))
            .count();
        let rescued_coarse_boundaries = decisions
            .iter()
            .filter(|decision| decision.detail_rescued_coarse_boundary == Some(true))
            .count();
        let added_coarse_boundaries = decisions
            .iter()
            .filter(|decision| decision.coarse_boundary == Some(false) && decision.boundary)
            .count();
        OperationStackDetailRecurrenceReport {
            association_field: OPERATION_STACK_DETAIL_FIELD,
            signature: "ordered (action, action_detail) pair",
            reference_transitions: detail_model.transition_count,
            same_signature_reference_transitions: detail_model.same_action_transitions,
            signature_change_reference_transitions: detail_model.action_change_transitions,
            global_cutoff: detail_model.global.cutoff,
            global_low_center: detail_model.global.low_center,
            global_high_center: detail_model.global.high_center,
            global_low_occurrences: detail_model.global.low_occurrences,
            global_high_occurrences: detail_model.global.high_occurrences,
            global_two_means_iterations: detail_model.global.iterations,
            signature_change_cutoff: detail_model.cross_action.cutoff,
            signature_change_applied_cutoff: detail_model
                .global
                .cutoff
                .min(detail_model.cross_action.cutoff),
            signature_change_low_center: detail_model.cross_action.low_center,
            signature_change_high_center: detail_model.cross_action.high_center,
            signature_change_low_occurrences: detail_model.cross_action.low_occurrences,
            signature_change_high_occurrences: detail_model.cross_action.high_occurrences,
            signature_change_two_means_iterations: detail_model.cross_action.iterations,
            seen_target_transitions,
            unseen_target_transitions,
            rescued_coarse_boundaries,
            added_coarse_boundaries,
        }
    });
    let report = OperationStackInductionReport {
        policy: OPERATION_STACK_POLICY,
        objective: OPERATION_STACK_OBJECTIVE,
        derived_stack_field: config.derived_field.clone(),
        sequence_field: OPERATION_STACK_SEQUENCE_FIELD,
        association_field: OPERATION_STACK_ASSOCIATION_FIELD,
        transition_weighting: "one count per adjacent occurrence; sample resource weight ignored",
        reference_source: if reference_is_external {
            "external-operation-records"
        } else {
            "current-selected-corpus"
        },
        reference_sessions,
        reference_operations,
        reference_transitions: model.transition_count,
        target_sessions: target_groups.len(),
        target_operations: samples.len(),
        same_action_reference_transitions: model.same_action_transitions,
        action_change_reference_transitions: model.action_change_transitions,
        cutoff: model.global.cutoff,
        low_center: model.global.low_center,
        high_center: model.global.high_center,
        low_occurrences: model.global.low_occurrences,
        high_occurrences: model.global.high_occurrences,
        two_means_iterations: model.global.iterations,
        global_cutoff: model.global.cutoff,
        global_low_center: model.global.low_center,
        global_high_center: model.global.high_center,
        global_low_occurrences: model.global.low_occurrences,
        global_high_occurrences: model.global.high_occurrences,
        global_two_means_iterations: model.global.iterations,
        cross_action_cutoff: model.cross_action.cutoff,
        cross_action_applied_cutoff: model.global.cutoff.min(model.cross_action.cutoff),
        cross_action_low_center: model.cross_action.low_center,
        cross_action_high_center: model.cross_action.high_center,
        cross_action_low_occurrences: model.cross_action.low_occurrences,
        cross_action_high_occurrences: model.cross_action.high_occurrences,
        cross_action_two_means_iterations: model.cross_action.iterations,
        removed_current_boundaries: decisions
            .iter()
            .filter(|decision| decision.current_boundary && !decision.boundary)
            .count(),
        added_current_boundaries: decisions
            .iter()
            .filter(|decision| !decision.current_boundary && decision.boundary)
            .count(),
        unseen_target_transitions: decisions
            .iter()
            .filter(|decision| decision.unseen_in_reference)
            .count(),
        predicted_groups: segments.len(),
        unique_motifs: unique_motifs.len(),
        selected_evidence_fields: selected_evidence_fields.clone(),
        selected_source_fields: selected_evidence_fields,
        excluded_oracle_fields: ORACLE_OR_LABEL_FIELDS.to_vec(),
        excluded_oracle_prefixes: ORACLE_OR_LABEL_PREFIXES.to_vec(),
        excluded_oracle_suffixes: ORACLE_OR_LABEL_SUFFIXES.to_vec(),
        supervised_calibration,
        detail_recurrence,
        boundary_decisions: decisions,
        segments,
    };
    Ok((samples, report))
}

#[derive(Debug)]
struct RecurrenceModel {
    association: BTreeMap<(RecurrenceState, RecurrenceState), f64>,
    transition_count: usize,
    same_action_transitions: usize,
    action_change_transitions: usize,
    global: RecurrenceCalibration,
    cross_action: RecurrenceCalibration,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct RecurrenceState {
    action: String,
    detail: Option<String>,
}

#[derive(Debug)]
struct RecurrenceCalibration {
    cutoff: f64,
    low_center: f64,
    high_center: f64,
    low_occurrences: usize,
    high_occurrences: usize,
    iterations: usize,
}

fn operation_single_value<'a>(
    operation: &'a Operation,
    field: &str,
    source: &str,
) -> Result<&'a str> {
    let values = operation.values(field);
    if values.len() != 1 || values[0].trim().is_empty() {
        bail!("{source} requires exactly one nonempty {field:?} value per operation");
    }
    Ok(values[0].as_str())
}

fn recurrence_uniform_detail(samples: &[Operation], source: &str) -> Result<bool> {
    let mut present = 0;
    for operation in samples {
        let values = operation.values(OPERATION_STACK_DETAIL_FIELD);
        match values {
            [] => {}
            [value] if !value.trim().is_empty() => present += 1,
            _ => {
                bail!(
                    "{source} requires at most one nonempty {:?} value per operation",
                    OPERATION_STACK_DETAIL_FIELD
                )
            }
        }
    }
    Ok(present == samples.len())
}

fn recurrence_state(
    operation: &Operation,
    detail_field: Option<&str>,
    source: &str,
) -> Result<RecurrenceState> {
    Ok(RecurrenceState {
        action: operation_single_value(operation, OPERATION_STACK_ASSOCIATION_FIELD, source)?
            .to_string(),
        detail: detail_field
            .map(|field| operation_single_value(operation, field, source).map(str::to_string))
            .transpose()?,
    })
}

fn recurrence_applied_cutoff(
    model: &RecurrenceModel,
    left: &RecurrenceState,
    right: &RecurrenceState,
) -> f64 {
    if left == right {
        model.global.cutoff
    } else {
        model.global.cutoff.min(model.cross_action.cutoff)
    }
}

fn recurrence_groups(samples: &[Operation], source: &str) -> Result<BTreeMap<String, Vec<usize>>> {
    let mut groups = BTreeMap::<String, Vec<usize>>::new();
    for (index, sample) in samples.iter().enumerate() {
        let session = operation_single_value(sample, OPERATION_STACK_SEQUENCE_FIELD, source)?;
        operation_single_value(sample, OPERATION_STACK_ASSOCIATION_FIELD, source)?;
        groups.entry(session.to_string()).or_default().push(index);
    }
    if groups.is_empty() {
        bail!("{source} produced no sessions");
    }
    Ok(groups)
}

fn recurrence_model(
    reference: &[Operation],
    groups: &BTreeMap<String, Vec<usize>>,
    detail_field: Option<&str>,
) -> Result<RecurrenceModel> {
    let mut left_counts = BTreeMap::<RecurrenceState, usize>::new();
    let mut right_counts = BTreeMap::<RecurrenceState, usize>::new();
    let mut pair_counts = BTreeMap::<(RecurrenceState, RecurrenceState), usize>::new();
    for indices in groups.values() {
        for pair in indices.windows(2) {
            let left = recurrence_state(&reference[pair[0]], detail_field, "induction reference")?;
            let right = recurrence_state(&reference[pair[1]], detail_field, "induction reference")?;
            *left_counts.entry(left.clone()).or_default() += 1;
            *right_counts.entry(right.clone()).or_default() += 1;
            *pair_counts.entry((left, right)).or_default() += 1;
        }
    }
    let transition_count = pair_counts.values().sum::<usize>();
    if transition_count == 0 {
        bail!("induction reference requires at least one adjacent transition");
    }
    let total = transition_count as f64;
    let mut association = BTreeMap::new();
    for ((left, right), count) in &pair_counts {
        let pair_probability = *count as f64 / total;
        let left_probability = left_counts[left] as f64 / total;
        let right_probability = right_counts[right] as f64 / total;
        let npmi = if pair_probability == 1.0 {
            1.0
        } else {
            (pair_probability / (left_probability * right_probability)).ln()
                / -pair_probability.ln()
        };
        if !npmi.is_finite() {
            bail!("induction reference produced non-finite NPMI for {left:?}->{right:?}");
        }
        association.insert((left.clone(), right.clone()), npmi);
    }
    let mut occurrence_scores = Vec::with_capacity(transition_count);
    let mut cross_action_scores = Vec::new();
    for (pair, count) in &pair_counts {
        occurrence_scores.extend(std::iter::repeat_n(association[pair], *count));
        if pair.0 != pair.1 {
            cross_action_scores.extend(std::iter::repeat_n(association[pair], *count));
        }
    }
    let global = recurrence_calibration(&occurrence_scores)?;
    let cross_action = recurrence_calibration(&cross_action_scores)?;
    let action_change_transitions = cross_action_scores.len();
    Ok(RecurrenceModel {
        association,
        transition_count,
        same_action_transitions: transition_count - action_change_transitions,
        action_change_transitions,
        global,
        cross_action,
    })
}

fn recurrence_calibration(scores: &[f64]) -> Result<RecurrenceCalibration> {
    let (low_center, high_center, low_occurrences, high_occurrences, iterations) =
        deterministic_recurrence_two_means(scores)?;
    Ok(RecurrenceCalibration {
        cutoff: (low_center + high_center) / 2.0,
        low_center,
        high_center,
        low_occurrences,
        high_occurrences,
        iterations,
    })
}

#[derive(Clone, Copy, Debug)]
struct CalibrationPartitionMetrics {
    precision: f64,
    recall: f64,
    f1: f64,
    oracle_groups: usize,
}

fn fit_supervised_recurrence_cutoff(
    calibration: &[Operation],
    groups: &BTreeMap<String, Vec<usize>>,
    model: &RecurrenceModel,
) -> Result<SupervisedRecurrenceCalibrationReport> {
    let mut observed_scores = Vec::new();
    let mut unseen_transitions = 0;
    let mut transitions = 0;
    for indices in groups.values() {
        for pair in indices.windows(2) {
            transitions += 1;
            let left = recurrence_state(&calibration[pair[0]], None, "induction calibration")?;
            let right = recurrence_state(&calibration[pair[1]], None, "induction calibration")?;
            if let Some(score) = model.association.get(&(left, right)) {
                observed_scores.push(*score);
            } else {
                unseen_transitions += 1;
            }
        }
    }
    observed_scores.sort_by(f64::total_cmp);
    observed_scores.dedup_by(|left, right| left.total_cmp(right).is_eq());
    let first = *observed_scores.first().context(
        "induction calibration requires at least one transition observed in the score reference",
    )?;
    let last = *observed_scores.last().context(
        "induction calibration requires at least one transition observed in the score reference",
    )?;
    let mut candidates = Vec::with_capacity(observed_scores.len() + 1);
    candidates.push(next_f64_down(first));
    for pair in observed_scores.windows(2) {
        let left = pair[0];
        let right = pair[1];
        let mut midpoint = (left + right) / 2.0;
        if midpoint <= left {
            midpoint = next_f64_up(left);
        }
        if !(left < midpoint && midpoint < right) {
            bail!("cannot construct a finite supervised recurrence cutoff");
        }
        candidates.push(midpoint);
    }
    candidates.push(next_f64_up(last));

    let mut selected: Option<(f64, CalibrationPartitionMetrics)> = None;
    let mut best_ties = 0;
    for cutoff in &candidates {
        let metrics =
            recurrence_calibration_partition_metrics(calibration, groups, model, *cutoff)?;
        match selected {
            None => {
                selected = Some((*cutoff, metrics));
                best_ties = 1;
            }
            Some((_, best)) if metrics.f1 > best.f1 => {
                selected = Some((*cutoff, metrics));
                best_ties = 1;
            }
            Some((best_cutoff, best)) if metrics.f1 == best.f1 => {
                best_ties += 1;
                if *cutoff < best_cutoff {
                    selected = Some((*cutoff, metrics));
                }
            }
            _ => {}
        }
    }
    let (selected_cutoff, selected_metrics) =
        selected.context("induction calibration produced no cutoff candidate")?;
    Ok(SupervisedRecurrenceCalibrationReport {
        policy: "reference-group-bcubed-scalar-calibration",
        objective: "maximize per-operation B-cubed partition F1 on grouped reference operations",
        group_field: OPERATION_STACK_CALIBRATION_GROUP_FIELD,
        sessions: groups.len(),
        operations: calibration.len(),
        transitions,
        groups: selected_metrics.oracle_groups,
        observed_transitions: transitions - unseen_transitions,
        unseen_transitions,
        distinct_scores: observed_scores.len(),
        candidate_cutoffs: candidates.len(),
        best_ties,
        selected_cutoff,
        selected_precision: selected_metrics.precision,
        selected_recall: selected_metrics.recall,
        selected_f1: selected_metrics.f1,
    })
}

fn recurrence_calibration_partition_metrics(
    calibration: &[Operation],
    groups: &BTreeMap<String, Vec<usize>>,
    model: &RecurrenceModel,
    cutoff: f64,
) -> Result<CalibrationPartitionMetrics> {
    type PredictedGroup = (String, usize);
    type OracleGroup = (String, String);
    let mut predicted_totals = BTreeMap::<PredictedGroup, usize>::new();
    let mut oracle_totals = BTreeMap::<OracleGroup, usize>::new();
    let mut overlaps = BTreeMap::<(PredictedGroup, OracleGroup), usize>::new();
    let mut items = Vec::<(PredictedGroup, OracleGroup)>::new();
    for (session, indices) in groups {
        let mut predicted_group = 0;
        for (position, index) in indices.iter().enumerate() {
            if position > 0 {
                let left = recurrence_state(
                    &calibration[indices[position - 1]],
                    None,
                    "induction calibration",
                )?;
                let right = recurrence_state(&calibration[*index], None, "induction calibration")?;
                let boundary = model
                    .association
                    .get(&(left, right))
                    .is_none_or(|score| *score < cutoff);
                if boundary {
                    predicted_group += 1;
                }
            }
            let group = operation_single_value(
                &calibration[*index],
                OPERATION_STACK_CALIBRATION_GROUP_FIELD,
                "induction calibration",
            )?;
            let predicted = (session.clone(), predicted_group);
            let oracle = (session.clone(), group.to_string());
            *predicted_totals.entry(predicted.clone()).or_default() += 1;
            *oracle_totals.entry(oracle.clone()).or_default() += 1;
            *overlaps
                .entry((predicted.clone(), oracle.clone()))
                .or_default() += 1;
            items.push((predicted, oracle));
        }
    }
    let operation_count = items.len();
    let mut precision_sum = 0.0;
    let mut recall_sum = 0.0;
    for (predicted, oracle) in &items {
        let overlap = overlaps[&(predicted.clone(), oracle.clone())] as f64;
        precision_sum += overlap / predicted_totals[predicted] as f64;
        recall_sum += overlap / oracle_totals[oracle] as f64;
    }
    let precision = precision_sum / operation_count as f64;
    let recall = recall_sum / operation_count as f64;
    let f1 = if precision + recall == 0.0 {
        0.0
    } else {
        2.0 * precision * recall / (precision + recall)
    };
    Ok(CalibrationPartitionMetrics {
        precision,
        recall,
        f1,
        oracle_groups: oracle_totals.len(),
    })
}

fn next_f64_up(value: f64) -> f64 {
    debug_assert!(value.is_finite());
    if value == -0.0 {
        return f64::from_bits(1);
    }
    let bits = value.to_bits();
    if value >= 0.0 {
        f64::from_bits(bits + 1)
    } else {
        f64::from_bits(bits - 1)
    }
}

fn next_f64_down(value: f64) -> f64 {
    debug_assert!(value.is_finite());
    if value == 0.0 {
        return f64::from_bits((1_u64 << 63) | 1);
    }
    let bits = value.to_bits();
    if value > 0.0 {
        f64::from_bits(bits - 1)
    } else {
        f64::from_bits(bits + 1)
    }
}

fn deterministic_recurrence_two_means(scores: &[f64]) -> Result<(f64, f64, usize, usize, usize)> {
    let mut low =
        scores.iter().copied().reduce(f64::min).context(
            "induction reference requires at least two distinct finite transition scores",
        )?;
    let mut high =
        scores.iter().copied().reduce(f64::max).context(
            "induction reference requires at least two distinct finite transition scores",
        )?;
    if !low.is_finite() || !high.is_finite() || low == high {
        bail!("induction reference requires at least two distinct finite transition scores");
    }
    for iteration in 1..=100 {
        let mut low_sum = 0.0;
        let mut high_sum = 0.0;
        let mut low_count = 0;
        let mut high_count = 0;
        for score in scores {
            if (*score - low).abs() <= (*score - high).abs() {
                low_sum += *score;
                low_count += 1;
            } else {
                high_sum += *score;
                high_count += 1;
            }
        }
        if low_count == 0 || high_count == 0 {
            bail!("induction reference two-means produced an empty cluster");
        }
        let next_low = low_sum / low_count as f64;
        let next_high = high_sum / high_count as f64;
        if next_low == low && next_high == high {
            return Ok((next_low, next_high, low_count, high_count, iteration));
        }
        low = next_low;
        high = next_high;
    }
    bail!("induction reference two-means did not converge within 100 iterations")
}

fn recurrence_motif(samples: &[Operation], indices: &[usize]) -> Result<String> {
    if indices.is_empty() {
        bail!("cannot name an empty recurrence segment");
    }
    let mut actions = Vec::<String>::new();
    for index in indices {
        let action = operation_single_value(
            &samples[*index],
            OPERATION_STACK_ASSOCIATION_FIELD,
            "induction target",
        )?;
        if actions.last().is_none_or(|previous| previous != action) {
            actions.push(action.to_string());
        }
    }
    Ok(format!("action={}", actions.join("-then-")))
}

fn disambiguate_recurrence_motifs<'a>(
    motifs: impl Iterator<Item = &'a str>,
    derived_field: &str,
) -> BTreeMap<String, String> {
    let motifs = motifs.map(str::to_string).collect::<BTreeSet<_>>();
    let mut collisions = BTreeMap::<String, BTreeSet<String>>::new();
    for motif in &motifs {
        collisions
            .entry(safe_frame(motif, Some(derived_field)))
            .or_default()
            .insert(motif.clone());
    }
    motifs
        .into_iter()
        .map(|motif| {
            let normalized = safe_frame(&motif, Some(derived_field));
            let label = if collisions[&normalized].len() == 1 {
                motif.clone()
            } else {
                format!("{motif}-{:016x}", recurrence_label_hash(&motif))
            };
            (motif, label)
        })
        .collect()
}

fn recurrence_label_hash(text: &str) -> u64 {
    let mut hash = 0xcbf29ce484222325_u64;
    for byte in text.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn operation_matches_filters(sample: &Operation, filters: &[OperationFilterRule]) -> bool {
    filters.iter().all(|filter| filter.matches(sample))
}

impl OperationFilterRule {
    fn matches(&self, sample: &Operation) -> bool {
        let matched = sample.values(&self.field).iter().any(|value| {
            self.regex.is_match(value) || self.regex.is_match(&format!("{}={value}", self.field))
        });
        if self.negated { !matched } else { matched }
    }
}

fn stack_frame_values(name: &str, sample: &Operation, rules: &[OperationStackRule]) -> Vec<String> {
    let searchable = sample.searchable_text();
    if let Some(rule) = rules
        .iter()
        .find(|rule| rule.frame == name && rule.regex.is_match(&searchable))
    {
        return vec![rule.label.clone()];
    }
    sample.values(name).to_vec()
}

fn tool_phase_label(event: &crate::session::ToolEvent) -> String {
    if !event.effect.is_empty() && event.effect != "process" {
        return event.effect.clone();
    }
    if !event.category.is_empty() && event.category != "tool" {
        return event.category.clone();
    }
    if !event.command_name.is_empty() && event.command_name != "none" {
        return event.command_name.clone();
    }
    event.tool_name.clone()
}

fn llm_phase_label(call: &crate::session::LlmEvent) -> String {
    if !call.tag.is_empty() && call.tag != "unmatched" {
        call.tag.clone()
    } else {
        "llm".to_string()
    }
}

fn session_samples(
    session: &SessionRecord,
    project_name: &str,
    view: ProfileView,
) -> Vec<Operation> {
    match view {
        ProfileView::Operations => operation_samples(session, project_name),
        ProfileView::Tokens => token_samples(session, project_name),
        ProfileView::Files => file_samples(session, project_name),
        ProfileView::Network => network_samples(session, project_name),
        ProfileView::Time => time_samples(session, project_name),
    }
}

pub fn source_sample_total(
    sessions: &[SessionRecord],
    project_name: &str,
    view: ProfileView,
) -> u64 {
    sessions
        .iter()
        .flat_map(|session| session_samples(session, project_name, view))
        .map(|sample| sample.value)
        .sum()
}

fn operation_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let terminal_paths = terminal_task_paths(session);
    let mut events = Vec::<(Option<i64>, u8, usize, Option<String>, Operation)>::new();
    for (idx, req) in session.user_requests.iter().enumerate() {
        let mut sample = base_sample(session, project_name, idx, 1);
        sample.insert("op", "prompt");
        sample.insert("phase", "prompt");
        sample.insert("action", "state task");
        sample.insert("object", "task request");
        sample.insert("result", "task received");
        sample.insert("status", "observed");
        sample.insert("source_kind", "prompt");
        sample.insert(
            "evidence_id",
            short_hash(
                &format!("{}:prompt:{}", session.session_id, req.text_hash),
                16,
            ),
        );
        sample.insert("prompt_hash", req.text_hash.clone());
        if let Some(ts) = req.ts_ms {
            sample.insert("timestamp_ms", ts.to_string());
        }
        insert_task_outcome(&mut sample, &terminal_paths);
        events.push((req.ts_ms, 0, idx, None, sample));
    }
    for (idx, event) in session.tools.iter().enumerate() {
        let mut sample = tool_sample(session, project_name, event, 1);
        insert_task_outcome(&mut sample, &terminal_paths);
        events.push((
            event.ts_ms,
            1,
            idx,
            Some(tool_repeat_signature(event, &sample)),
            sample,
        ));
    }
    for (idx, call) in session.llm_calls.iter().enumerate() {
        let mut sample = base_sample(session, project_name, call.prompt_index, 1);
        replace_task_path(&mut sample, &call.task_path);
        replace_skill_scope(&mut sample, &call.skill);
        sample.insert("op", "llm");
        sample.insert("phase", llm_phase_label(call));
        sample.insert("action", "reason or report");
        sample.insert("object", "current task");
        sample.insert("result", llm_result_label(call));
        sample.insert("call", format!("llm/{}", call.tag));
        sample.insert("llm", call.tag.clone());
        sample.insert("llm_preview", call.preview.clone());
        sample.insert("model", last_model_segment(&call.model));
        sample.insert("response_phase", call.response_phase.clone());
        sample.insert("response_hash", call.text_hash.clone());
        if let Some(ts) = call.ts_ms {
            sample.insert("timestamp_ms", ts.to_string());
        }
        sample.insert("status", "observed");
        sample.insert("source_kind", "llm");
        sample.insert(
            "evidence_id",
            short_hash(
                &format!("{}:llm:{}", session.session_id, call.text_hash),
                16,
            ),
        );
        insert_task_outcome(&mut sample, &terminal_paths);
        events.push((call.ts_ms, 2, idx, None, sample));
    }

    events.sort_by_key(|(ts, kind, ordinal, _, _)| {
        (ts.is_none(), ts.unwrap_or_default(), *kind, *ordinal)
    });
    let mut samples = Vec::with_capacity(events.len());
    let mut previous_tool: Option<(i64, String)> = None;
    for (ts, _, _, tool_signature, mut sample) in events {
        if let Some(signature) = tool_signature {
            if let Some(current_ts) = ts
                && previous_tool
                    .as_ref()
                    .is_some_and(|(previous_ts, previous)| {
                        *previous_ts < current_ts && previous == &signature
                    })
            {
                sample.insert("repeat", "consecutive exact repeat");
            }
            previous_tool = ts.map(|timestamp| (timestamp, signature));
        } else {
            previous_tool = None;
        }
        samples.push(sample);
    }
    samples
}

fn terminal_task_paths(session: &SessionRecord) -> BTreeSet<Vec<String>> {
    session
        .llm_calls
        .iter()
        .filter(|call| call.response_phase == "final_answer")
        .map(|call| {
            if call.task_path.is_empty() {
                request_task_path(session, call.prompt_index)
            } else {
                call.task_path.clone()
            }
        })
        .collect()
}

fn request_task_path(session: &SessionRecord, prompt_index: usize) -> Vec<String> {
    let request = session.request_by_index(prompt_index);
    if !request.task_path.is_empty() {
        request.task_path.clone()
    } else if !session.task_tag.is_empty() {
        vec![session.task_tag.clone()]
    } else {
        vec![semantic_task_label(&request.preview)]
    }
}

fn tool_repeat_signature(event: &crate::session::ToolEvent, sample: &Operation) -> String {
    [
        sample.values("task").join("\u{1f}"),
        event.tool_name.clone(),
        event.command.clone(),
        event.path_groups.join("\u{1f}"),
        event.domains.join("\u{1f}"),
        sample.values("action").join("\u{1f}"),
        sample.values("object").join("\u{1f}"),
    ]
    .join("\u{1e}")
}

fn insert_task_outcome(sample: &mut Operation, terminal_paths: &BTreeSet<Vec<String>>) {
    let task_path = sample.values("task");
    let exact = terminal_paths
        .iter()
        .any(|terminal| terminal.as_slice() == task_path);
    let related = terminal_paths.iter().any(|terminal| {
        terminal.as_slice().starts_with(task_path) || task_path.starts_with(terminal.as_slice())
    });
    sample.insert(
        "outcome",
        if exact {
            "source-visible terminal response at exact task"
        } else if related {
            "source-visible terminal response at related task"
        } else {
            "no source-visible terminal response for task"
        },
    );
}

fn llm_result_label(call: &crate::session::LlmEvent) -> &'static str {
    match call.response_phase.as_str() {
        "final_answer" => "terminal response reported",
        "commentary" => "progress reported",
        _ if call.preview == "token report" || call.preview == "session token summary" => {
            "token usage reported"
        }
        _ => "assistant response reported",
    }
}

fn token_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let terminal_paths = terminal_task_paths(session);
    let mut samples = Vec::new();
    for call in &session.llm_calls {
        for (kind, value) in call.token_components() {
            let mut sample = base_sample(session, project_name, call.prompt_index, value);
            replace_task_path(&mut sample, &call.task_path);
            replace_skill_scope(&mut sample, &call.skill);
            sample.insert("op", "llm");
            sample.insert("phase", llm_phase_label(call));
            sample.insert("action", "reason or report");
            sample.insert("object", "current task");
            sample.insert("result", llm_result_label(call));
            sample.insert("call", format!("llm/{}", call.tag));
            sample.insert("llm", call.tag.clone());
            sample.insert("llm_preview", call.preview.clone());
            sample.insert("model", last_model_segment(&call.model));
            sample.insert("response_phase", call.response_phase.clone());
            sample.insert("response_hash", call.text_hash.clone());
            if let Some(ts) = call.ts_ms {
                sample.insert("timestamp_ms", ts.to_string());
            }
            sample.insert("token", kind);
            sample.insert("source_kind", "llm");
            sample.insert(
                "evidence_id",
                short_hash(
                    &format!("{}:llm:{}", session.session_id, call.text_hash),
                    16,
                ),
            );
            insert_task_outcome(&mut sample, &terminal_paths);
            samples.push(sample);
        }
    }
    samples
}

fn file_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let terminal_paths = terminal_task_paths(session);
    let mut samples = Vec::new();
    for event in &session.tools {
        if event.path_groups.is_empty() {
            continue;
        }
        for group in &event.path_groups {
            let mut sample = tool_sample(session, project_name, event, 1);
            sample.insert("path", group.clone());
            sample
                .fields
                .insert("object".to_string(), vec![group.clone()]);
            insert_task_outcome(&mut sample, &terminal_paths);
            samples.push(sample);
        }
    }
    samples
}

fn network_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let terminal_paths = terminal_task_paths(session);
    let mut samples = Vec::new();
    for event in &session.tools {
        if event.effect != "network" && event.domains.is_empty() {
            continue;
        }
        let domains = if event.domains.is_empty() {
            vec!["unknown".to_string()]
        } else {
            event.domains.clone()
        };
        for domain in domains {
            let mut sample = tool_sample(session, project_name, event, 1);
            sample.insert("domain", domain.clone());
            sample.fields.insert("object".to_string(), vec![domain]);
            insert_task_outcome(&mut sample, &terminal_paths);
            samples.push(sample);
        }
    }
    samples
}

fn time_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let terminal_paths = terminal_task_paths(session);
    let mut events = Vec::new();
    let mut ordinal = 0usize;

    for (idx, req) in session.user_requests.iter().enumerate() {
        if let Some(ts) = req.ts_ms {
            let mut sample = base_sample(session, project_name, idx, 0);
            sample.insert("op", "prompt");
            sample.insert("phase", "prompt");
            sample.insert("action", "state task");
            sample.insert("object", "task request");
            sample.insert("result", "task received");
            sample.insert("source_kind", "prompt");
            sample.insert(
                "evidence_id",
                short_hash(
                    &format!("{}:prompt:{}", session.session_id, req.text_hash),
                    16,
                ),
            );
            sample.insert("prompt_hash", req.text_hash.clone());
            sample.insert("timestamp_ms", ts.to_string());
            insert_task_outcome(&mut sample, &terminal_paths);
            events.push((ts, ordinal, sample));
            ordinal += 1;
        }
    }
    for event in &session.tools {
        if let Some(ts) = event.ts_ms {
            let mut sample = tool_sample(session, project_name, event, 0);
            insert_task_outcome(&mut sample, &terminal_paths);
            events.push((ts, ordinal, sample));
            ordinal += 1;
        }
    }
    for call in &session.llm_calls {
        if let Some(ts) = call.ts_ms {
            let mut sample = base_sample(session, project_name, call.prompt_index, 0);
            replace_task_path(&mut sample, &call.task_path);
            replace_skill_scope(&mut sample, &call.skill);
            sample.insert("op", "llm");
            sample.insert("phase", llm_phase_label(call));
            sample.insert("action", "reason or report");
            sample.insert("object", "current task");
            sample.insert("result", llm_result_label(call));
            sample.insert("call", format!("llm/{}", call.tag));
            sample.insert("llm", call.tag.clone());
            sample.insert("llm_preview", call.preview.clone());
            sample.insert("model", last_model_segment(&call.model));
            sample.insert("response_phase", call.response_phase.clone());
            sample.insert("response_hash", call.text_hash.clone());
            sample.insert("timestamp_ms", ts.to_string());
            sample.insert("source_kind", "llm");
            sample.insert(
                "evidence_id",
                short_hash(
                    &format!("{}:llm:{}", session.session_id, call.text_hash),
                    16,
                ),
            );
            insert_task_outcome(&mut sample, &terminal_paths);
            events.push((ts, ordinal, sample));
            ordinal += 1;
        }
    }

    events.sort_by_key(|(ts, ordinal, _)| (*ts, *ordinal));
    let mut samples = Vec::new();
    for i in 0..events.len() {
        let duration_sec = if i + 1 < events.len() {
            let next_ts = events[i + 1].0;
            ((next_ts - events[i].0) / 1000).max(1) as u64
        } else {
            1
        };
        let mut sample = events[i].2.clone();
        sample.value = duration_sec;
        samples.push(sample);
    }
    samples
}

fn base_sample(
    session: &SessionRecord,
    project_name: &str,
    prompt_index: usize,
    value: u64,
) -> Operation {
    let req = session.request_by_index(prompt_index);
    let mut sample = Operation::new(value);
    sample.insert("project", project_name);
    sample.insert("agent", session.source.clone());
    sample.insert("session", session.session_tag.clone());
    sample.insert("source_session", session.session_id.clone());
    sample.extend("task", request_task_path(session, prompt_index));
    sample.insert("skill", "unscoped");
    sample.insert("prompt", req.tag.clone());
    sample.insert("prompt_hash", req.text_hash.clone());
    sample.insert("prompt_preview", req.preview.clone());
    sample
}

fn replace_task_path(sample: &mut Operation, task_path: &[String]) {
    if task_path.is_empty() {
        return;
    }
    sample.fields.remove("task");
    sample.extend("task", task_path.iter().cloned());
}

fn replace_skill_scope(sample: &mut Operation, skill: &str) {
    if skill.is_empty() {
        return;
    }
    sample
        .fields
        .insert("skill".to_string(), vec![skill.to_string()]);
}

fn tool_action_label(event: &crate::session::ToolEvent) -> String {
    let name = event.tool_name.to_ascii_lowercase();
    if name == "composite" {
        return "run composite source operation".to_string();
    }
    if name.contains("spawn_agent") {
        return "delegate subtask".to_string();
    }
    if name.contains("wait_agent") || name == "wait" || name.contains("list_agents") {
        return "observe subtask".to_string();
    }
    if name.contains("send_message") || name.contains("followup") {
        return "coordinate subtask".to_string();
    }
    if name.contains("interrupt_agent") {
        return "stop subtask".to_string();
    }
    match event.effect.as_str() {
        "read" => "read or search".to_string(),
        "write" => "edit artifact".to_string(),
        "test" => "run validation".to_string(),
        "network" => "collect external evidence".to_string(),
        "repo" => "record repository progress".to_string(),
        _ if event.category == "plan" => "update task plan".to_string(),
        _ if event.category == "subagent" => "coordinate subtask".to_string(),
        _ if !event.command_name.is_empty() && event.command_name != "none" => {
            format!("run {}", event.command_name)
        }
        _ => event.tool_name.replace('_', " "),
    }
}

fn tool_object_label(event: &crate::session::ToolEvent) -> String {
    event
        .path_groups
        .first()
        .or_else(|| event.domains.first())
        .cloned()
        .or_else(|| {
            (!event.command_name.is_empty() && event.command_name != "none")
                .then(|| event.command_name.clone())
        })
        .unwrap_or_else(|| event.tool_name.replace('_', " "))
}

fn tool_result_label(status: &str) -> &'static str {
    match status {
        "ok" | "success" => "completed",
        "fail" | "error" => "failed",
        _ => "machine outcome unobserved",
    }
}

fn tool_sample(
    session: &SessionRecord,
    project_name: &str,
    event: &crate::session::ToolEvent,
    value: u64,
) -> Operation {
    let mut sample = base_sample(session, project_name, event.prompt_index, value);
    replace_task_path(&mut sample, &event.task_path);
    replace_skill_scope(&mut sample, &event.skill);
    sample.insert("op", "tool");
    sample.insert("phase", tool_phase_label(event));
    sample.insert("action", tool_action_label(event));
    sample.insert("object", tool_object_label(event));
    sample.insert("result", tool_result_label(&event.status));
    sample.insert("tool", event.tool_name.clone());
    sample.insert("category", event.category.clone());
    sample.insert("command", event.command.clone());
    sample.insert("effect", event.effect.clone());
    sample.insert("status", event.status.clone());
    if let Some(call_id) = &event.call_id {
        sample.insert("call_id", call_id.clone());
    }
    if let Some(ts) = event.ts_ms {
        sample.insert("timestamp_ms", ts.to_string());
    }
    if event.category == "shell" && !event.command_name.is_empty() {
        sample.insert("cmd", event.command_name.clone());
    }
    sample.extend("process", event.process_chain.clone());
    sample.insert("source_kind", "tool");
    sample.insert(
        "evidence_id",
        short_hash(
            &format!(
                "{}:tool:{}:{}:{}",
                session.session_id,
                event.call_id.as_deref().unwrap_or("none"),
                event.ts_ms.unwrap_or_default(),
                event.tool_name
            ),
            16,
        ),
    );
    sample
}

pub fn profile_to_stacks(profile: &Profile) -> Counter {
    let mut out = Counter::new();
    for id in 0..profile.ops.len() {
        let value = profile.ops[id].value;
        if value == 0 {
            continue;
        }
        folded_add(&mut out, op_frames(profile, id), value);
    }
    out
}

fn op_frames(profile: &Profile, id: OpId) -> Vec<String> {
    let mut frames = Vec::new();
    let mut current = Some(id);
    while let Some(id) = current {
        let op = &profile.ops[id];
        frames.push(safe_frame(&op.name, Some(op.kind.as_str())));
        current = op.parent;
    }
    frames.reverse();
    frames
}

pub fn folded_add(counter: &mut Counter, frames: Vec<String>, weight: u64) {
    let stack = folded_stack_from_strings(frames);
    if !stack.is_empty() {
        *counter.entry(stack).or_default() += weight.max(1);
    }
}

fn folded_stack_from_frames(frames: &[Frame]) -> String {
    folded_stack_from_strings(
        frames
            .iter()
            .map(|(kind, name)| safe_frame(name, Some(kind.as_str())))
            .collect(),
    )
}

fn folded_stack_from_strings(frames: Vec<String>) -> String {
    frames
        .into_iter()
        .map(normalize_folded_frame)
        .filter(|frame| !frame.is_empty())
        .collect::<Vec<_>>()
        .join(";")
}

fn normalize_folded_frame(frame: String) -> String {
    if let Some(path) = frame.strip_prefix("path:") {
        safe_frame(path, Some("path"))
    } else {
        frame
    }
}

pub fn write_pprof_difference(
    candidate: &Profile,
    base: &Profile,
    output: &Path,
    deterministic_output: bool,
) -> Result<SignedCounter> {
    ensure_parent_dir(output)?;
    let candidate_stacks = profile_to_stacks(candidate);
    let base_stacks = profile_to_stacks(base);
    let mut difference = SignedCounter::new();
    for stack in candidate_stacks.keys().chain(base_stacks.keys()) {
        let candidate_weight = i128::from(candidate_stacks.get(stack).copied().unwrap_or(0));
        let base_weight = i128::from(base_stacks.get(stack).copied().unwrap_or(0));
        let value = (candidate_weight - base_weight)
            .clamp(i128::from(i64::MIN), i128::from(i64::MAX)) as i64;
        if value != 0 {
            difference.insert(stack.clone(), value);
        }
    }

    let mut signed_samples = Vec::<(String, i64, Vec<(String, String)>)>::new();
    for sample in &candidate.pprof_samples {
        let mut labels = sample.labels.clone();
        labels.push(("comparison_side".to_string(), "candidate".to_string()));
        signed_samples.push((
            sample.stack.clone(),
            i64::try_from(sample.value).unwrap_or(i64::MAX),
            labels,
        ));
    }
    for sample in &base.pprof_samples {
        let mut labels = sample.labels.clone();
        labels.push(("comparison_side".to_string(), "base".to_string()));
        labels.push(("pprof::base".to_string(), "true".to_string()));
        signed_samples.push((
            sample.stack.clone(),
            -i64::try_from(sample.value).unwrap_or(i64::MAX),
            labels,
        ));
    }
    write_pprof_samples(
        candidate,
        signed_samples
            .iter()
            .map(|(stack, weight, labels)| (stack.as_str(), *weight, labels.as_slice())),
        output,
        deterministic_output,
        Some("candidate-minus-base"),
    )?;
    Ok(difference)
}

fn ensure_parent_dir(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent)?;
    }
    Ok(())
}

pub fn write_pprof_projection(
    projection: &Profile,
    output: &Path,
    deterministic_output: bool,
) -> Result<()> {
    write_pprof_samples(
        projection,
        projection.pprof_samples.iter().map(|sample| {
            (
                sample.stack.as_str(),
                i64::try_from(sample.value).unwrap_or(i64::MAX),
                sample.labels.as_slice(),
            )
        }),
        output,
        deterministic_output,
        None,
    )
}

fn write_pprof_samples<'a, I>(
    projection: &Profile,
    stacks: I,
    output: &Path,
    deterministic_output: bool,
    comparison: Option<&str>,
) -> Result<()>
where
    I: IntoIterator<Item = (&'a str, i64, &'a [(String, String)])>,
{
    let mut strings = StringInterner::with_pprof_root();
    let sample_type = PprofValueType {
        type_: strings.intern(projection.sample_type),
        unit: strings.intern(projection.unit),
    };
    let label_view = strings.intern("view");
    let label_view_value = strings.intern(projection.view);
    let comparison_label =
        comparison.map(|value| (strings.intern("comparison"), strings.intern(value)));
    let filename = strings.intern("agentpprof");
    let mut functions = Vec::new();
    let mut locations = Vec::new();
    let mut frame_locations = BTreeMap::<String, u64>::new();
    let mut samples = Vec::new();

    for (stack, weight, evidence_labels) in stacks {
        let mut location_ids = Vec::new();
        for frame in stack.split(';').filter(|frame| !frame.is_empty()).rev() {
            let id = if let Some(id) = frame_locations.get(frame) {
                *id
            } else {
                let id = u64::try_from(frame_locations.len() + 1).unwrap_or(u64::MAX);
                let name = strings.intern(frame);
                functions.push(PprofFunction {
                    id,
                    name,
                    system_name: name,
                    filename,
                });
                locations.push(PprofLocation {
                    id,
                    line: vec![PprofLine {
                        function_id: id,
                        line: 0,
                    }],
                });
                frame_locations.insert(frame.to_string(), id);
                id
            };
            location_ids.push(id);
        }
        let mut labels = vec![PprofLabel {
            key: label_view,
            str_value: label_view_value,
        }];
        if let Some((key, str_value)) = comparison_label {
            labels.push(PprofLabel { key, str_value });
        }
        for (key, value) in evidence_labels {
            labels.push(PprofLabel {
                key: strings.intern(key),
                str_value: strings.intern(value),
            });
        }
        samples.push(PprofSample {
            location_id: location_ids,
            value: vec![weight],
            label: labels,
        });
    }

    let default_sample_type = sample_type.type_;
    let profile = PprofProfile {
        sample_type: vec![sample_type],
        sample: samples,
        location: locations,
        function: functions,
        string_table: strings.items,
        time_nanos: if deterministic_output {
            0
        } else {
            Utc::now().timestamp_nanos_opt().unwrap_or(0)
        },
        duration_nanos: 0,
        default_sample_type,
    };
    let bytes = profile.encode_to_vec();
    if output.extension().and_then(|ext| ext.to_str()) == Some("gz") {
        let file = fs::File::create(output)?;
        let mut encoder = GzEncoder::new(file, Compression::default());
        encoder.write_all(&bytes)?;
        encoder.finish()?;
    } else {
        fs::write(output, bytes)?;
    }
    Ok(())
}

pub fn safe_frame(text: &str, prefix: Option<&str>) -> String {
    let text = redact_private_frame_text(text, prefix);
    let text = normalize_frame_text(&text, prefix);
    let mut out = String::new();
    for ch in text.to_lowercase().chars() {
        if ch.is_alphanumeric() || "._:/+-".contains(ch) {
            out.push(ch);
        } else if !out.ends_with('_') {
            out.push('_');
        }
    }
    let trimmed = out.trim_matches(['_', ';']).to_string();
    let value = if trimmed.is_empty() {
        "unknown".to_string()
    } else {
        trimmed
    };
    match prefix {
        Some(prefix) => format!("{prefix}:{value}"),
        None => value,
    }
}

fn normalize_frame_text(text: &str, prefix: Option<&str>) -> String {
    if prefix != Some("path") {
        return text.to_string();
    }
    let text = text.trim();
    let text = text.strip_prefix("path:").unwrap_or(text).trim();
    if !text.starts_with('/') {
        return text.to_string();
    }
    let collapsed = collapse_project_path(path_component_strings(Path::new(text)));
    if collapsed == "repo" {
        "external/path".to_string()
    } else {
        collapsed
    }
}

fn redact_private_frame_text(text: &str, prefix: Option<&str>) -> String {
    if !contains_private_marker(text) {
        return text.to_string();
    }
    match prefix {
        Some("domain") => "private.domain".to_string(),
        Some("path") => "external/home".to_string(),
        Some("process") => "external".to_string(),
        _ => current_username()
            .map(|name| {
                text.to_ascii_lowercase()
                    .replace(&name.to_ascii_lowercase(), "user")
            })
            .unwrap_or_else(|| text.to_string()),
    }
}

fn current_username() -> Option<String> {
    dirs::home_dir()
        .and_then(|home| {
            home.file_name()
                .map(|part| part.to_string_lossy().to_string())
        })
        .filter(|name| !name.is_empty())
}

#[cfg(test)]
fn agent_family(source: &str) -> String {
    if source.starts_with("codex") {
        "codex".to_string()
    } else if source.starts_with("claude") {
        "claude".to_string()
    } else {
        source.to_string()
    }
}

#[cfg(test)]
fn short_session_id(session_id: &str) -> String {
    let compact = session_id
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or(session_id)
        .trim_end_matches(".jsonl");
    if compact.is_empty() {
        "session".to_string()
    } else if compact.chars().count() <= 12 {
        compact.to_string()
    } else {
        let head = compact.chars().take(6).collect::<String>();
        let tail = compact
            .chars()
            .rev()
            .take(5)
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect::<String>();
        format!("{head}.{tail}")
    }
}

#[cfg(test)]
fn agent_sight_session_id(source: &str, session_id: &str) -> String {
    let family = agent_family(source);
    format!("local:{family}:{family}:{}", short_session_id(session_id))
}

fn last_model_segment(model: &str) -> &str {
    model.rsplit('/').next().unwrap_or(model)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::session::{LlmEvent, ToolEvent, UserRequest};
    use std::path::PathBuf;

    fn test_session(
        source: &str,
        session_tag: &str,
        prompts: Vec<UserRequest>,
        tools: Vec<ToolEvent>,
        llm_calls: Vec<LlmEvent>,
    ) -> SessionRecord {
        SessionRecord {
            source: source.to_string(),
            path: PathBuf::from("session.jsonl"),
            session_id: "s1".to_string(),
            cwd: "/repo".to_string(),
            agent_role: "agent".to_string(),
            model: source.to_string(),
            title: "test session".to_string(),
            start_ts_ms: prompts.first().and_then(|prompt| prompt.ts_ms),
            user_requests: prompts,
            tools,
            llm_calls,
            session_tag: session_tag.to_string(),
            task_tag: String::new(),
        }
    }

    fn prompt(index: usize, ts_ms: i64, hash: &str, preview: &str, tag: &str) -> UserRequest {
        UserRequest {
            index,
            ts_ms: Some(ts_ms),
            text_hash: hash.to_string(),
            preview: preview.to_string(),
            tag: tag.to_string(),
            task_path: Vec::new(),
        }
    }

    fn shell_tool(ts_ms: i64, prompt_index: usize, status: &str, paths: Vec<&str>) -> ToolEvent {
        ToolEvent {
            ts_ms: Some(ts_ms),
            prompt_index,
            tool_name: "exec_command".to_string(),
            category: "shell".to_string(),
            command: "cargo test".to_string(),
            command_name: "cargo".to_string(),
            effect: "test".to_string(),
            process_chain: vec!["cargo".to_string()],
            status: status.to_string(),
            path_groups: paths.into_iter().map(str::to_string).collect(),
            domains: Vec::new(),
            call_id: Some("call-1".to_string()),
            invoked_skill: String::new(),
            skill: String::new(),
            task_path: Vec::new(),
        }
    }

    fn read_tool(ts_ms: i64, prompt_index: usize, paths: Vec<&str>) -> ToolEvent {
        ToolEvent {
            ts_ms: Some(ts_ms),
            prompt_index,
            tool_name: "Read".to_string(),
            category: "read".to_string(),
            command: "src/lib.rs".to_string(),
            command_name: "Read".to_string(),
            effect: "read".to_string(),
            process_chain: Vec::new(),
            status: "ok".to_string(),
            path_groups: paths.into_iter().map(str::to_string).collect(),
            domains: Vec::new(),
            call_id: Some("call-read".to_string()),
            invoked_skill: String::new(),
            skill: String::new(),
            task_path: Vec::new(),
        }
    }

    fn llm(ts_ms: i64, prompt_index: usize, model: &str, tag: &str) -> LlmEvent {
        LlmEvent {
            ts_ms: Some(ts_ms),
            prompt_index,
            model: model.to_string(),
            source_id: String::new(),
            text_hash: "l0".to_string(),
            preview: "answer".to_string(),
            input_tokens: 1,
            output_tokens: 1,
            cache_tokens: 0,
            total_tokens: 0,
            tag: tag.to_string(),
            response_phase: "final_answer".to_string(),
            skill: String::new(),
            task_path: Vec::new(),
        }
    }

    #[test]
    fn path_frames_do_not_look_absolute() {
        assert_eq!(safe_frame("/.git", Some("path")), "path:.git");
        assert_eq!(safe_frame("path:/.git", Some("path")), "path:.git");
        assert_eq!(safe_frame("/target", Some("path")), "path:target");
        assert_eq!(safe_frame("/", Some("path")), "path:external/path");

        let mut stacks = Counter::new();
        folded_add(
            &mut stacks,
            vec!["project:agentsight".to_string(), "path:/.git".to_string()],
            1,
        );
        assert!(stacks.contains_key("project:agentsight;path:.git"));
    }

    #[test]
    fn semantic_frames_preserve_unicode_labels() {
        assert_eq!(safe_frame("写论文", Some("task")), "task:写论文");
        assert_eq!(
            safe_frame("撰写 Abstract", Some("subtask")),
            "subtask:撰写_abstract"
        );
    }

    #[test]
    fn agent_sight_session_id_matches_collector_shape() {
        assert_eq!(
            agent_sight_session_id("codex", "019ec561-a99a-7a81-a344-6d898f7615ab"),
            "local:codex:codex:019ec5.615ab"
        );
    }

    #[test]
    fn time_stacks_calculate_duration_between_events() {
        let session = test_session(
            "codex",
            "rustfix",
            vec![prompt(0, 1000, "h1", "fix rust tests", "debug")],
            vec![shell_tool(3000, 0, "ok", vec!["repo"])],
            vec![llm(8000, 0, "gpt-5", "summarize")],
        );
        let options = OperationStackConfig::for_view(ProfileView::Time);
        let profile =
            build_profile_with_options(&[session], "agentsight", ProfileView::Time, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);
        // prompt at 1000ms, tool at 3000ms -> 2 seconds
        assert_eq!(
            stacks.get("task:fix_rust_tests;skill:unscoped;phase:prompt;action:state_task;object:task_request;result:task_received;outcome:source-visible_terminal_response_at_exact_task"),
            Some(&2)
        );
        // tool at 3000ms, llm at 8000ms -> 5 seconds
        assert_eq!(
            stacks.get(
                "task:fix_rust_tests;skill:unscoped;phase:test;action:run_validation;object:repo;result:completed;outcome:source-visible_terminal_response_at_exact_task"
            ),
            Some(&5)
        );
        // last event gets 1 second
        assert_eq!(
            stacks.get("task:fix_rust_tests;skill:unscoped;phase:summarize;action:reason_or_report;object:current_task;result:terminal_response_reported;outcome:source-visible_terminal_response_at_exact_task"),
            Some(&1)
        );
    }

    #[test]
    fn file_stacks_detect_task_phases_inside_one_prompt() {
        let session = test_session(
            "codex",
            "rustfix",
            vec![prompt(0, 1000, "h1", "fix rust tests", "debug")],
            vec![
                read_tool(2000, 0, vec!["src"]),
                shell_tool(3000, 0, "ok", vec!["tests"]),
            ],
            Vec::new(),
        );
        let options = OperationStackConfig::for_view(ProfileView::Files);
        let profile =
            build_profile_with_options(&[session], "agentsight", ProfileView::Files, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get(
                "task:fix_rust_tests;skill:unscoped;phase:read;action:read_or_search;object:src;result:completed;outcome:no_source-visible_terminal_response_for_task"
            ),
            Some(&1)
        );
        assert_eq!(
            stacks.get(
                "task:fix_rust_tests;skill:unscoped;phase:test;action:run_validation;object:tests;result:completed;outcome:no_source-visible_terminal_response_for_task"
            ),
            Some(&1)
        );
    }

    #[test]
    fn operations_view_counts_prompts_tools_and_llm_calls() {
        let session = test_session(
            "codex",
            "rustfix",
            vec![prompt(0, 1000, "h1", "fix rust tests", "debug")],
            vec![read_tool(2000, 0, vec!["src"])],
            vec![llm(3000, 0, "gpt-5", "answer")],
        );
        let stack = parse_stack_spec("project,agent,op,phase,status").unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations).with_stack(stack);
        let profile =
            build_profile_with_options(&[session], "agentsight", ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("project:agentsight;agent:codex;op:prompt;phase:prompt;status:observed"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;op:tool;phase:read;status:ok"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;op:llm;phase:answer;status:observed"),
            Some(&1)
        );
    }

    #[test]
    fn default_profile_exposes_nested_tasks_and_repeated_work() {
        let mut first = read_tool(2000, 0, vec!["paper.tex"]);
        first.task_path = vec!["write a paper".to_string(), "write abstract".to_string()];
        let mut second = first.clone();
        second.ts_ms = Some(3000);
        second.call_id = Some("call-repeat".to_string());
        let session = test_session(
            "codex",
            "paper",
            vec![prompt(0, 1000, "h1", "write a paper", "writing")],
            vec![first, second],
            Vec::new(),
        );

        let options = OperationStackConfig::for_view(ProfileView::Operations);
        let profile =
            build_profile_with_options(&[session], "agentsight", ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("task:write_a_paper;task:write_abstract;skill:unscoped;phase:read;action:read_or_search;object:paper.tex;result:completed;outcome:no_source-visible_terminal_response_for_task"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("task:write_a_paper;task:write_abstract;skill:unscoped;phase:read;action:read_or_search;object:paper.tex;repeat:consecutive_exact_repeat;result:completed;outcome:no_source-visible_terminal_response_for_task"),
            Some(&1)
        );
    }

    #[test]
    fn repeated_work_requires_chronological_adjacency_without_progress() {
        let mut first = read_tool(2000, 0, vec!["paper.tex"]);
        first.task_path = vec!["write a paper".to_string(), "write abstract".to_string()];
        let mut second = first.clone();
        second.ts_ms = Some(4000);
        second.call_id = Some("call-after-progress".to_string());
        let mut progress = llm(3000, 0, "gpt-5", "commentary");
        progress.response_phase = "commentary".to_string();
        progress.task_path = first.task_path.clone();
        let session = test_session(
            "codex",
            "paper",
            vec![prompt(0, 1000, "h1", "write a paper", "writing")],
            vec![first, second],
            vec![progress],
        );

        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("task:write_a_paper;task:write_abstract;skill:unscoped;phase:read;action:read_or_search;object:paper.tex;result:completed;outcome:no_source-visible_terminal_response_for_task"),
            Some(&2)
        );
        assert!(
            !stacks
                .keys()
                .any(|stack| stack.contains("consecutive_exact_repeat"))
        );
    }

    #[test]
    fn different_source_commands_are_not_collapsed_as_repetition() {
        let mut first = shell_tool(2000, 0, "ok", vec!["repo"]);
        first.command = "rg parser agent-session".to_string();
        first.command_name = "rg".to_string();
        first.effect = "read".to_string();
        let mut second = first.clone();
        second.ts_ms = Some(3000);
        second.command = "rg profile agentpprof".to_string();
        second.call_id = Some("different-command".to_string());
        let session = test_session(
            "codex",
            "audit",
            vec![prompt(0, 1000, "h1", "audit profiler", "audit")],
            vec![first, second],
            Vec::new(),
        );

        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(
            !stacks
                .keys()
                .any(|stack| stack.contains("consecutive_exact_repeat"))
        );
    }

    #[test]
    fn ambiguous_same_timestamp_does_not_claim_a_repeat() {
        let first = read_tool(2000, 0, vec!["paper.tex"]);
        let mut second = first.clone();
        second.call_id = Some("same-millisecond".to_string());
        let session = test_session(
            "codex",
            "audit",
            vec![prompt(0, 1000, "h1", "audit profiler", "audit")],
            vec![first, second],
            Vec::new(),
        );
        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(
            !stacks
                .keys()
                .any(|stack| stack.contains("consecutive_exact_repeat"))
        );
    }

    #[test]
    fn terminal_outcome_is_scoped_to_the_matching_task_path() {
        let mut abstract_tool = read_tool(2000, 0, vec!["abstract.tex"]);
        abstract_tool.task_path = vec!["write a paper".to_string(), "write abstract".to_string()];
        let mut evaluation_tool = read_tool(3000, 0, vec!["evaluation.tex"]);
        evaluation_tool.task_path =
            vec!["write a paper".to_string(), "write evaluation".to_string()];
        let mut final_response = llm(4000, 0, "gpt-5", "final");
        final_response.task_path = evaluation_tool.task_path.clone();
        let session = test_session(
            "codex",
            "paper",
            vec![prompt(0, 1000, "h1", "write a paper", "writing")],
            vec![abstract_tool, evaluation_tool],
            vec![final_response],
        );
        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(stacks.keys().any(|stack| {
            stack.contains("task:write_abstract")
                && stack.contains("outcome:no_source-visible_terminal_response_for_task")
        }));
        assert!(stacks.keys().any(|stack| {
            stack.contains("task:write_evaluation")
                && stack.contains("outcome:source-visible_terminal_response_at_exact_task")
        }));
    }

    #[test]
    fn declared_task_tag_is_additional_to_raw_session_tag() {
        let mut session = test_session(
            "agentboard",
            "shopping",
            vec![prompt(0, 1000, "h1", "buy a mug", "shopping")],
            Vec::new(),
            Vec::new(),
        );
        session.task_tag = "webshop".to_string();
        let stack = parse_stack_spec("session,task,prompt").unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations).with_stack(stack);
        let profile = build_profile_with_options(
            &[session.clone()],
            "agentboard",
            ProfileView::Operations,
            &options,
        )
        .unwrap();

        assert_eq!(
            profile_to_stacks(&profile).get("session:shopping;task:webshop;prompt:shopping"),
            Some(&1)
        );
    }

    #[test]
    fn custom_operation_stack_rules_fold_recursively() {
        let session = test_session(
            "codex",
            "rustfix",
            vec![prompt(0, 1000, "h1", "fix rust tests", "debug")],
            vec![
                read_tool(2000, 0, vec!["src"]),
                shell_tool(3000, 0, "ok", vec!["tests"]),
            ],
            Vec::new(),
        );
        let stack = parse_stack_spec("project,agent,task,phase,op,tool,path,status").unwrap();
        let rules = parse_stack_rules(&[
            "task:verify=(effect=test|cmd=cargo|path=tests)".to_string(),
            "task:explore=(effect=read|path=src)".to_string(),
            "phase:inspect=(effect=read)".to_string(),
            "phase:execute=(effect=test)".to_string(),
        ])
        .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Files)
            .with_stack(stack)
            .with_rules(rules);
        let profile =
            build_profile_with_options(&[session], "agentsight", ProfileView::Files, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("project:agentsight;agent:codex;task:explore;phase:inspect;op:tool;tool:read;path:src;status:ok"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;task:verify;phase:execute;op:tool;tool:exec_command;path:tests;status:ok"),
            Some(&1)
        );
    }

    #[test]
    fn operation_jsonl_input_uses_same_operation_stack_model() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ops.jsonl");
        fs::write(
            &path,
            r#"{"value":1,"fields":{"project":"external","agent":"human-demo","dataset":"weblinx","demo":"d1","action":"click","op":"action","target":"login","status":"gold"}}"#
                .to_string()
                + "\n"
                + r#"{"value":1,"project":"external","agent":"human-demo","dataset":"weblinx","demo":"d1","action":"type","op":"action","target":"email","status":"gold"}"#
                + "\n",
        )
        .unwrap();
        let stack = parse_stack_spec("project,agent,task,phase,op,action,target,status").unwrap();
        let rules = parse_stack_rules(&[
            "task:authenticate=(target=login|target=email)".to_string(),
            "phase:select=(action=click)".to_string(),
            "phase:input=(action=type)".to_string(),
        ])
        .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Files)
            .with_stack(stack)
            .with_rules(rules);
        let profile =
            build_profile_from_operation_files(&[path], ProfileView::Files, &options).unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("project:external;agent:human-demo;task:authenticate;phase:select;op:action;action:click;target:login;status:gold"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:external;agent:human-demo;task:authenticate;phase:input;op:action;action:type;target:email;status:gold"),
            Some(&1)
        );
    }

    #[test]
    fn operation_marks_preserve_paths_across_filtering_and_pprof_evidence() {
        fn marked_operation(value: u64, session: &str, id: &str, action: &str) -> Operation {
            let mut operation = Operation::new(value);
            operation.insert("session_id", session);
            operation.insert("operation_id", id);
            operation.insert("action", action);
            operation
        }

        let operations = vec![
            marked_operation(2, "s1", "a", "drop"),
            marked_operation(3, "s1", "b", "keep"),
            marked_operation(5, "s1", "c", "keep"),
            marked_operation(7, "s2", "a", "keep"),
            marked_operation(11, "s2", "b", "keep"),
        ];
        let marks = parse_operation_mark_file(
            r#"{
                "sequence_field":"session_id",
                "id_field":"operation_id",
                "operation_names":{
                    "review":"Review evidence",
                    "fix":"Fix implementation",
                    "test":"Test the fix"
                },
                "marks":[
                    {"sequence":"s1","start_operation_id":"a","operation_ids":["review"]},
                    {"sequence":"s1","start_operation_id":"c","operation_ids":["fix","test"]},
                    {"sequence":"s2","start_operation_id":"a","operation_ids":["review"]},
                    {"sequence":"s2","start_operation_id":"b","operation_ids":["fix"]}
                ]
            }"#,
        )
        .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_filters(parse_operation_filters(&["action=keep".to_string()]).unwrap())
            .with_rules(
                parse_stack_rules(&["operation:regex-override=(action=keep)".to_string()]).unwrap(),
            )
            .with_operation_marks(marks);
        let profile =
            build_profile_from_operations(&operations, ProfileView::Operations, &options).unwrap();
        let stacks = profile_to_stacks(&profile);
        assert_eq!(stacks.get("operation:review_evidence"), Some(&10));
        assert_eq!(
            stacks.get("operation:fix_implementation;operation:test_the_fix"),
            Some(&5)
        );
        assert_eq!(stacks.get("operation:fix_implementation"), Some(&11));
        assert!(!stacks.keys().any(|stack| stack.contains("regex-override")));

        let labels = profile
            .pprof_samples
            .iter()
            .flat_map(|sample| sample.labels.iter())
            .cloned()
            .collect::<BTreeSet<_>>();
        assert!(labels.contains(&("source_session".to_string(), "s1".to_string())));
        assert!(labels.contains(&("source_session".to_string(), "s2".to_string())));
        assert!(labels.contains(&("evidence_id".to_string(), "b".to_string())));
        assert!(labels.contains(&("evidence_id".to_string(), "c".to_string())));
        assert!(labels.contains(&("operation_start_id".to_string(), "a".to_string())));
        assert!(labels.contains(&("operation_start_id".to_string(), "c".to_string())));
    }

    #[test]
    fn operation_marks_reject_pprof_name_collisions_and_unknown_sequences() {
        let collision = parse_operation_mark_file(
            r#"{
                "sequence_field":"session",
                "id_field":"id",
                "operation_names":{"one":"Review Evidence","two":"review_evidence"},
                "marks":[{"sequence":"s","start_operation_id":"a","operation_ids":["one"]}]
            }"#,
        )
        .unwrap_err();
        assert!(collision.to_string().contains("same pprof frame"));

        let marks = parse_operation_mark_file(
            r#"{
                "sequence_field":"session",
                "id_field":"id",
                "operation_names":{"review":"Review evidence"},
                "marks":[
                    {"sequence":"s1","start_operation_id":"a","operation_ids":["review"]},
                    {"sequence":"typo","start_operation_id":"x","operation_ids":["review"]}
                ]
            }"#,
        )
        .unwrap();
        let mut operation = Operation::new(1);
        operation.insert("session", "s1");
        operation.insert("id", "a");
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_marks(marks);
        let error =
            match build_profile_from_operations(&[operation], ProfileView::Operations, &options) {
                Ok(_) => panic!("unknown operation-mark sequence should fail"),
                Err(error) => error,
            };
        assert!(
            error
                .to_string()
                .contains("unknown input sequence \"typo\"")
        );

        let marks = parse_operation_mark_file(
            r#"{
                "sequence_field":"session",
                "id_field":"id",
                "operation_names":{"review":"Review evidence"},
                "marks":[
                    {"sequence":"session 1","start_operation_id":"a","operation_ids":["review"]},
                    {"sequence":"session_1","start_operation_id":"a","operation_ids":["review"]}
                ]
            }"#,
        )
        .unwrap();
        let operations = ["session 1", "session_1"]
            .into_iter()
            .map(|session| {
                let mut operation = Operation::new(1);
                operation.insert("session", session);
                operation.insert("id", "a");
                operation
            })
            .collect::<Vec<_>>();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_marks(marks);
        let error =
            match build_profile_from_operations(&operations, ProfileView::Operations, &options) {
                Ok(_) => panic!("colliding normalized source_session labels should fail"),
                Err(error) => error,
            };
        assert!(
            error
                .to_string()
                .contains("same pprof source_session label")
        );
    }

    #[test]
    fn operation_field_rules_map_fields_before_stacking() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ops.jsonl");
        fs::write(
            &path,
            r#"{"value":1,"fields":{"project":"external","agent":"gold","dataset":"demo","op":"action","action":"click","target":"login","status":"gold"}}"#
                .to_string()
                + "\n"
                + r#"{"value":1,"fields":{"project":"external","agent":"gold","dataset":"demo","op":"action","action":"type","target":"email","status":"gold"}}"#
                + "\n",
        )
        .unwrap();
        let stack = parse_stack_spec("project,agent,task,phase,op,action,status").unwrap();
        let field_rules = parse_stack_rules(&[
            "task:authenticate=(target=login|target=email)".to_string(),
            "phase:select=(action=click.*task=authenticate)".to_string(),
            "phase:input=(action=type.*task=authenticate)".to_string(),
        ])
        .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(stack)
            .with_field_rules(field_rules);
        let profile =
            build_profile_from_operation_files(&[path], ProfileView::Operations, &options).unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(
            stacks.get("project:external;agent:gold;task:authenticate;phase:select;op:action;action:click;status:gold"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:external;agent:gold;task:authenticate;phase:input;op:action;action:type;status:gold"),
            Some(&1)
        );
    }

    #[test]
    fn operation_filters_select_after_field_mapping() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ops.jsonl");
        fs::write(
            &path,
            r#"{"value":1,"fields":{"project":"external","agent":"gold","dataset":"demo","op":"action","action":"click","target":"login","status":"gold"}}"#
                .to_string()
                + "\n"
                + r#"{"value":1,"fields":{"project":"external","agent":"gold","dataset":"demo","op":"action","action":"type","target":"email","status":"gold"}}"#
                + "\n",
        )
        .unwrap();
        let stack = parse_stack_spec("project,agent,task,phase,op,action,status").unwrap();
        let field_rules = parse_stack_rules(&[
            "task:authenticate=(target=login|target=email)".to_string(),
            "phase:select=(action=click.*task=authenticate)".to_string(),
            "phase:input=(action=type.*task=authenticate)".to_string(),
        ])
        .unwrap();
        let filters = parse_operation_filters(&["phase=input".to_string()]).unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(stack)
            .with_field_rules(field_rules)
            .with_filters(filters);
        let profile =
            build_profile_from_operation_files(&[path], ProfileView::Operations, &options).unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(stacks.len(), 1);
        assert_eq!(
            stacks.get("project:external;agent:gold;task:authenticate;phase:input;op:action;action:type;status:gold"),
            Some(&1)
        );
    }

    #[test]
    fn operation_stack_induction_derives_operation_frames_without_oracle_fields() {
        let mut records = Vec::new();
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "agent-reward-bench",
                "analysis_task": "agentreward_looping",
                "session": "s0",
                "repeat_state": "single",
                "repeat_signal": "none",
                "action": "click",
                "looping": "no",
                "problem_value": "negative",
                "status": "failure",
                "step_correct": "false",
                "safety": "safe",
                "human_group": "g0",
                "group_pattern": "g0"
            }}));
        }
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "agent-reward-bench",
                "analysis_task": "agentreward_looping",
                "session": "s0",
                "repeat_state": "same-action-run",
                "repeat_signal": "loop-like",
                "action": "click",
                "looping": "yes",
                "problem_value": "positive",
                "status": "failure",
                "step_correct": "true",
                "safety": "unsafe",
                "human_group": "g1",
                "group_pattern": "g1"
            }}));
        }
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "agent-reward-bench",
                "analysis_task": "agentreward_looping",
                "session": "s0",
                "repeat_state": "same-action-run",
                "repeat_signal": "loop-like",
                "action": "fill",
                "looping": "yes",
                "problem_value": "positive",
                "status": "failure",
                "step_correct": "true",
                "safety": "unsafe",
                "human_group": "g2",
                "group_pattern": "g2"
            }}));
        }

        let reference = [("fill", 5), ("click", 4), ("fill", 3), ("click", 2)]
            .into_iter()
            .flat_map(|(action, count)| {
                std::iter::repeat_n(
                    json!({"value": 1, "fields": {"session": "reference", "action": action}}),
                    count,
                )
            })
            .collect::<Vec<_>>();
        let stack = parse_stack_spec("operation").unwrap();
        let induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(stack)
            .with_operation_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&records, ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(!stacks.is_empty());
        assert!(stacks.keys().all(|stack| {
            stack
                .split(';')
                .all(|frame| frame.starts_with("operation:"))
        }));
        assert!(stacks.keys().all(|stack| {
            !stack.contains("looping")
                && !stack.contains("problem_value")
                && !stack.contains("status:")
                && !stack.contains("step_correct")
                && !stack.contains("safety:")
                && !stack.contains("human_group")
                && !stack.contains("group_pattern")
        }));
        assert_eq!(stacks.values().sum::<u64>(), 18);
        assert_eq!(stacks.len(), 2);

        let report = profile
            .operation_stack_induction
            .as_ref()
            .expect("induction report");
        assert_eq!(report.policy, OPERATION_STACK_POLICY);
        assert_eq!(report.sequence_field, "session");
        assert_eq!(report.association_field, "action");
        assert_eq!(report.selected_source_fields, vec!["action"]);
        assert_eq!(report.reference_sessions, 1);
        assert_eq!(report.reference_operations, 14);
        assert_eq!(report.reference_transitions, 13);
        assert_eq!(report.target_sessions, 1);
        assert_eq!(report.target_operations, 18);
        assert_eq!(report.boundary_decisions.len(), 17);
        assert_eq!(report.added_current_boundaries, 0);
        assert!(
            report
                .boundary_decisions
                .iter()
                .all(|decision| !decision.boundary || decision.current_boundary)
        );
        assert_eq!(report.segments.len(), 2);
        assert_eq!(report.predicted_groups, 2);
        assert_eq!(report.unique_motifs, 2);
        assert_eq!(report.segments[0].motif, "action=click");
        assert_eq!(report.segments[1].motif, "action=fill");

        let second =
            build_profile_from_operation_records(&records, ProfileView::Operations, &options)
                .unwrap();
        assert_eq!(
            serde_json::to_value(report).unwrap(),
            serde_json::to_value(second.operation_stack_induction.as_ref().unwrap()).unwrap()
        );

        let mut hidden_mutation = records.clone();
        for (index, record) in hidden_mutation.iter_mut().enumerate() {
            record["fields"]["human_group"] = json!(format!("mutated-{index}"));
            record["fields"]["label"] = json!(format!("label-{index}"));
            record["fields"]["oracle_answer"] = json!(index % 2 == 0);
            record["fields"]["target_positive"] = json!(index % 3 == 0);
        }
        let mutated = build_profile_from_operation_records(
            &hidden_mutation,
            ProfileView::Operations,
            &options,
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(report).unwrap(),
            serde_json::to_value(mutated.operation_stack_induction.as_ref().unwrap()).unwrap()
        );
    }

    #[test]
    fn operation_stack_induction_fits_one_grouped_reference_cutoff() {
        let reference = [("fill", 5), ("click", 4), ("fill", 3), ("click", 2)]
            .into_iter()
            .flat_map(|(action, count)| {
                std::iter::repeat_n(
                    json!({"value": 1, "fields": {"session": "reference", "action": action}}),
                    count,
                )
            })
            .collect::<Vec<_>>();
        let calibration = ["click", "click", "fill", "click"]
            .into_iter()
            .enumerate()
            .map(|(index, action)| {
                json!({"value": index as u64 + 1, "fields": {
                    "session": "calibration", "action": action, "group": "one-operation"
                }})
            })
            .collect::<Vec<_>>();
        let target = ["click", "click", "fill", "click"]
            .into_iter()
            .map(|action| json!({"value": 1, "fields": {"session": "target", "action": action}}))
            .collect::<Vec<_>>();
        let induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap()
            .with_calibration_operation_records(&calibration)
            .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&target, ProfileView::Operations, &options)
                .unwrap();
        let report = profile.operation_stack_induction.unwrap();
        let unit_calibration = calibration
            .iter()
            .cloned()
            .map(|mut record| {
                record["value"] = json!(1);
                record
            })
            .collect::<Vec<_>>();
        let unit_induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap()
            .with_calibration_operation_records(&unit_calibration)
            .unwrap();
        let unit_options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(unit_induction);
        let unit_report =
            build_profile_from_operation_records(&target, ProfileView::Operations, &unit_options)
                .unwrap()
                .operation_stack_induction
                .unwrap();
        assert_eq!(
            serde_json::to_value(&report).unwrap(),
            serde_json::to_value(&unit_report).unwrap()
        );
        let calibration = report
            .supervised_calibration
            .expect("supervised calibration report");

        assert_eq!(
            calibration.policy,
            "reference-group-bcubed-scalar-calibration"
        );
        assert_eq!(calibration.sessions, 1);
        assert_eq!(calibration.operations, 4);
        assert_eq!(calibration.transitions, 3);
        assert_eq!(calibration.groups, 1);
        assert_eq!(calibration.selected_f1, 1.0);
        assert_eq!(calibration.best_ties, 1);
        assert!(calibration.candidate_cutoffs >= 2);
        assert!(
            report
                .boundary_decisions
                .iter()
                .all(|decision| !decision.boundary)
        );
        assert!(
            report
                .boundary_decisions
                .iter()
                .any(|decision| decision.label_free_boundary == Some(true))
        );
        assert!(report.boundary_decisions.iter().all(|decision| {
            decision.calibration_population == "reference-group-bcubed"
                && decision.label_free_applied_cutoff.is_some()
        }));
        assert_eq!(report.segments.len(), 1);
    }

    #[test]
    fn supervised_recurrence_calibration_resolves_exact_ties_to_smallest_cutoff() {
        let calibration_rows = [("a", "g0"), ("b", "g0"), ("c", "g1"), ("d", "g1")]
            .into_iter()
            .map(|(action, group)| {
                json!({"value": 1, "fields": {
                    "session": "calibration", "action": action, "group": group
                }})
            })
            .collect::<Vec<_>>();
        let calibration = OperationStackInductionConfig::new()
            .with_calibration_operation_records(&calibration_rows)
            .unwrap()
            .calibration_operations
            .unwrap();
        let groups = recurrence_groups(&calibration, "induction calibration").unwrap();
        let state = |action: &str| RecurrenceState {
            action: action.to_string(),
            detail: None,
        };
        let model = RecurrenceModel {
            association: BTreeMap::from([
                ((state("a"), state("b")), 0.0),
                ((state("b"), state("c")), 1.0),
                ((state("c"), state("d")), 0.0),
            ]),
            transition_count: 3,
            same_action_transitions: 0,
            action_change_transitions: 3,
            global: RecurrenceCalibration {
                cutoff: 0.5,
                low_center: 0.0,
                high_center: 1.0,
                low_occurrences: 2,
                high_occurrences: 1,
                iterations: 1,
            },
            cross_action: RecurrenceCalibration {
                cutoff: 0.5,
                low_center: 0.0,
                high_center: 1.0,
                low_occurrences: 2,
                high_occurrences: 1,
                iterations: 1,
            },
        };
        let result = fit_supervised_recurrence_cutoff(&calibration, &groups, &model).unwrap();

        assert_eq!(result.candidate_cutoffs, 3);
        assert_eq!(result.best_ties, 2);
        assert_eq!(result.selected_cutoff, next_f64_down(0.0));
        assert_eq!(result.selected_f1, 2.0 / 3.0);
    }

    #[test]
    fn operation_stack_induction_disambiguates_normalized_child_labels() {
        let mut records = Vec::new();
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "fixture", "session": "s0", "action": "A B"
            }}));
        }
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "fixture", "session": "s0", "action": "a_b"
            }}));
        }
        let reference = [("a_b", 5), ("A B", 4), ("a_b", 3), ("A B", 2)]
            .into_iter()
            .flat_map(|(action, count)| {
                std::iter::repeat_n(
                    json!({"value": 1, "fields": {"session": "reference", "action": action}}),
                    count,
                )
            })
            .collect::<Vec<_>>();
        let induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&records, ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert_eq!(stacks.len(), 2);
        assert_eq!(stacks.values().sum::<u64>(), 12);
        let segments = &profile.operation_stack_induction.as_ref().unwrap().segments;
        assert_eq!(segments.len(), 2);
        assert_ne!(segments[0].motif, segments[1].motif);
        assert_ne!(
            safe_frame(&segments[0].motif, Some("operation")),
            safe_frame(&segments[1].motif, Some("operation"))
        );
    }

    #[test]
    fn operation_stack_induction_only_removes_current_cross_action_boundaries() {
        let reference = [("fill", 5), ("click", 4), ("fill", 3), ("click", 2)]
            .into_iter()
            .flat_map(|(action, count)| {
                std::iter::repeat_n(
                    json!({"value": 1, "fields": {"session": "reference", "action": action}}),
                    count,
                )
            })
            .collect::<Vec<_>>();
        let target = ["fill", "click"]
            .into_iter()
            .map(|action| json!({"value": 1, "fields": {"session": "target", "action": action}}))
            .collect::<Vec<_>>();
        let induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&target, ProfileView::Operations, &options)
                .unwrap();
        let report = profile.operation_stack_induction.as_ref().unwrap();
        let decision = &report.boundary_decisions[0];

        assert!(report.cross_action_applied_cutoff < report.global_cutoff);
        assert!(decision.current_boundary);
        assert!(!decision.boundary);
        assert_eq!(report.removed_current_boundaries, 1);
        assert_eq!(report.added_current_boundaries, 0);
        assert_eq!(report.segments.len(), 1);
        assert_eq!(report.segments[0].motif, "action=fill-then-click");
    }

    #[test]
    fn operation_stack_induction_uses_recurrent_detail_only_to_rescue_continuity() {
        let mut reference = Vec::new();
        let mut session_id = 0;
        for ((left_action, left_detail), (right_action, right_detail), count) in [
            (("a", "x"), ("b", "y"), 10),
            (("a", "z"), ("c", "u"), 20),
            (("a", "z"), ("c", "v"), 20),
            (("d", "p"), ("b", "w"), 20),
            (("d", "q"), ("b", "w"), 20),
            (("e", "m"), ("f", "n"), 10),
        ] {
            for _ in 0..count {
                let session = format!("reference-{session_id:03}");
                session_id += 1;
                reference.push(json!({"value": 1, "fields": {
                    "session": session,
                    "action": left_action,
                    "action_detail": left_detail
                }}));
                reference.push(json!({"value": 1, "fields": {
                    "session": session,
                    "action": right_action,
                    "action_detail": right_detail
                }}));
            }
        }
        let target = vec![
            json!({"value": 1, "fields": {
                "session": "target", "action": "a", "action_detail": "x"
            }}),
            json!({"value": 1, "fields": {
                "session": "target", "action": "b", "action_detail": "y"
            }}),
        ];
        let induction = OperationStackInductionConfig::new()
            .with_reference_operation_records(&reference)
            .unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&target, ProfileView::Operations, &options)
                .unwrap();
        let report = profile.operation_stack_induction.as_ref().unwrap();
        let detail = report.detail_recurrence.as_ref().expect("detail report");
        let decision = &report.boundary_decisions[0];

        assert_eq!(
            report.selected_source_fields,
            vec!["action", "action_detail"]
        );
        assert_eq!(detail.association_field, "action_detail");
        assert_eq!(detail.rescued_coarse_boundaries, 1);
        assert_eq!(detail.added_coarse_boundaries, 0);
        assert_eq!(decision.left_action_detail.as_deref(), Some("x"));
        assert_eq!(decision.right_action_detail.as_deref(), Some("y"));
        assert_eq!(decision.coarse_boundary, Some(true));
        assert_eq!(decision.detail_continuity, Some(true));
        assert_eq!(decision.detail_rescued_coarse_boundary, Some(true));
        assert!(!decision.boundary);
        assert_eq!(report.segments.len(), 1);
        assert_eq!(report.segments[0].motif, "action=a-then-b");
    }

    #[test]
    fn operation_stack_induction_rejects_missing_and_degenerate_inputs() {
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(parse_stack_spec("operation").unwrap())
            .with_operation_stack_induction(OperationStackInductionConfig::new());
        let missing_session = vec![
            json!({"value": 1, "fields": {"action": "click"}}),
            json!({"value": 1, "fields": {"action": "fill"}}),
        ];
        let error = build_profile_from_operation_records(
            &missing_session,
            ProfileView::Operations,
            &options,
        )
        .err()
        .expect("missing session must fail");
        assert!(
            error
                .to_string()
                .contains("exactly one nonempty \"session\"")
        );

        let degenerate = vec![
            json!({"value": 1, "fields": {"session": "s0", "action": "click"}}),
            json!({"value": 1, "fields": {"session": "s0", "action": "click"}}),
            json!({"value": 1, "fields": {"session": "s0", "action": "click"}}),
        ];
        let error =
            build_profile_from_operation_records(&degenerate, ProfileView::Operations, &options)
                .err()
                .expect("one-score reference must fail");
        assert!(
            error
                .to_string()
                .contains("at least two distinct finite transition scores")
        );
    }

    #[test]
    fn pprof_writer_emits_gzip_profile() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("profile.pb.gz");
        let mut projection = Profile::new("tokens", "tokens", "count");
        projection.sample(
            vec![
                ("project".to_string(), "test".to_string()),
                ("agent".to_string(), "codex".to_string()),
                ("session".to_string(), "rustfix".to_string()),
                ("prompt".to_string(), "review".to_string()),
                ("op".to_string(), "llm".to_string()),
                ("token".to_string(), "input".to_string()),
            ],
            7,
            vec![
                ("source_kind".to_string(), "llm".to_string()),
                ("evidence_id".to_string(), "abc123".to_string()),
            ],
        );
        write_pprof_projection(&projection, &path, false).unwrap();

        let bytes = fs::read(path).unwrap();
        let mut decoder = GzDecoder::new(&bytes[..]);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).unwrap();
        let profile = PprofProfile::decode(&decoded[..]).unwrap();
        assert_eq!(profile.sample.len(), 1);
        assert_eq!(profile.sample[0].value, vec![7]);
        let labels = profile.sample[0]
            .label
            .iter()
            .map(|label| {
                (
                    profile.string_table[label.key as usize].as_str(),
                    profile.string_table[label.str_value as usize].as_str(),
                )
            })
            .collect::<BTreeSet<_>>();
        assert!(labels.contains(&("view", "tokens")));
        assert!(labels.contains(&("source_kind", "llm")));
        assert!(labels.contains(&("evidence_id", "abc123")));
    }

    #[test]
    fn product_pprof_keeps_reversible_source_evidence_labels() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let session = test_session(
            "codex",
            "evidence",
            vec![prompt(0, 1000, "prompt-hash", "inspect parser", "inspect")],
            vec![read_tool(2000, 0, vec!["agent-session/src/parser.rs"])],
            vec![llm(3000, 0, "gpt-5", "final")],
        );
        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("evidence.pb.gz");
        write_pprof_projection(&profile, &path, true).unwrap();

        let bytes = fs::read(path).unwrap();
        let mut decoder = GzDecoder::new(&bytes[..]);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).unwrap();
        let decoded = PprofProfile::decode(&decoded[..]).unwrap();
        let label_sets = decoded
            .sample
            .iter()
            .map(|sample| {
                sample
                    .label
                    .iter()
                    .map(|label| {
                        (
                            decoded.string_table[label.key as usize].as_str(),
                            decoded.string_table[label.str_value as usize].as_str(),
                        )
                    })
                    .collect::<BTreeSet<_>>()
            })
            .collect::<Vec<_>>();

        assert!(label_sets.iter().all(|labels| {
            labels.contains(&("source_session", "s1"))
                && labels.contains(&("prompt_hash", "prompt-hash"))
                && labels.iter().any(|(key, _)| *key == "timestamp_ms")
        }));
        assert!(label_sets.iter().any(|labels| {
            labels.contains(&("source_kind", "tool")) && labels.contains(&("call_id", "call-read"))
        }));
        assert!(label_sets.iter().any(|labels| {
            labels.contains(&("source_kind", "llm"))
                && labels.contains(&("response_hash", "l0"))
                && labels.contains(&("response_phase", "final_answer"))
        }));
    }

    #[test]
    fn skill_frames_and_labels_conserve_operation_and_token_totals() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let mut tool = shell_tool(2000, 0, "ok", vec!["repo"]);
        tool.skill = "check-paper-citations".to_string();
        let mut named_llm = llm(3000, 0, "gpt-5", "continue");
        named_llm.skill = "check-paper-citations".to_string();
        let unscoped_llm = llm(4000, 0, "gpt-5", "finish");
        let session = test_session(
            "claude",
            "skill-scope",
            vec![prompt(0, 1000, "prompt-hash", "check citations", "inspect")],
            vec![tool],
            vec![named_llm, unscoped_llm],
        );

        for view in [ProfileView::Operations, ProfileView::Tokens] {
            let options = OperationStackConfig::for_view(view).with_stack(
                parse_stack_spec("project,agent,task,skill,phase,op,tool,call,token").unwrap(),
            );
            let source_total =
                source_sample_total(std::slice::from_ref(&session), "agentsight", view);
            let profile = build_profile_with_options(
                std::slice::from_ref(&session),
                "agentsight",
                view,
                &options,
            )
            .unwrap();
            let folded_total = profile_to_stacks(&profile).values().sum::<u64>();
            assert_eq!(folded_total, source_total);
            assert!(profile_to_stacks(&profile).keys().any(|stack| {
                stack.contains(
                    "project:agentsight;agent:claude;task:check_citations;skill:check-paper-citations;phase:",
                )
            }));
            assert!(profile.pprof_samples.iter().any(|sample| {
                sample
                    .labels
                    .contains(&("skill".to_string(), "check-paper-citations".to_string()))
            }));
            assert!(profile.pprof_samples.iter().any(|sample| {
                sample
                    .labels
                    .contains(&("skill".to_string(), "unscoped".to_string()))
            }));

            let dir = tempfile::tempdir().unwrap();
            let view_name = match view {
                ProfileView::Operations => "operations",
                ProfileView::Tokens => "tokens",
                _ => unreachable!(),
            };
            let path = dir.path().join(format!("skill-{view_name}.pb.gz"));
            write_pprof_projection(&profile, &path, true).unwrap();
            let bytes = fs::read(path).unwrap();
            let mut decoder = GzDecoder::new(&bytes[..]);
            let mut decoded = Vec::new();
            decoder.read_to_end(&mut decoded).unwrap();
            let decoded = PprofProfile::decode(&decoded[..]).unwrap();
            let pprof_total = decoded
                .sample
                .iter()
                .map(|sample| sample.value.first().copied().unwrap_or_default())
                .sum::<i64>();
            assert_eq!(pprof_total, source_total as i64);
        }
    }

    #[test]
    fn pprof_difference_preserves_positive_and_negative_samples() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("difference.pb.gz");
        let mut candidate = Profile::new("operations", "operations", "count");
        candidate.sample(
            vec![
                ("task".to_string(), "checkout".to_string()),
                ("action".to_string(), "retry".to_string()),
                ("result".to_string(), "error".to_string()),
            ],
            3,
            vec![("evidence_id".to_string(), "c1".to_string())],
        );
        let mut base = Profile::new("operations", "operations", "count");
        base.sample(
            vec![
                ("task".to_string(), "checkout".to_string()),
                ("action".to_string(), "retry".to_string()),
                ("result".to_string(), "error".to_string()),
            ],
            1,
            vec![("evidence_id".to_string(), "b1".to_string())],
        );

        let difference = write_pprof_difference(&candidate, &base, &path, true).unwrap();
        assert_eq!(difference["task:checkout;action:retry;result:error"], 2);

        let bytes = fs::read(path).unwrap();
        let mut decoder = GzDecoder::new(&bytes[..]);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).unwrap();
        let profile = PprofProfile::decode(&decoded[..]).unwrap();
        let mut values = profile
            .sample
            .iter()
            .map(|sample| sample.value[0])
            .collect::<Vec<_>>();
        values.sort_unstable();
        assert_eq!(values, vec![-1, 3]);
        assert!(profile.sample.iter().all(|sample| {
            sample.label.iter().any(|label| {
                profile.string_table[label.key as usize] == "comparison"
                    && profile.string_table[label.str_value as usize] == "candidate-minus-base"
            })
        }));
        let labeled_sides = profile
            .sample
            .iter()
            .map(|sample| {
                sample
                    .label
                    .iter()
                    .map(|label| {
                        (
                            profile.string_table[label.key as usize].as_str(),
                            profile.string_table[label.str_value as usize].as_str(),
                        )
                    })
                    .collect::<BTreeSet<_>>()
            })
            .collect::<Vec<_>>();
        assert!(labeled_sides.iter().any(|labels| {
            labels.contains(&("comparison_side", "candidate"))
                && labels.contains(&("evidence_id", "c1"))
                && !labels.contains(&("pprof::base", "true"))
        }));
        assert!(labeled_sides.iter().any(|labels| {
            labels.contains(&("comparison_side", "base"))
                && labels.contains(&("pprof::base", "true"))
                && labels.contains(&("evidence_id", "b1"))
        }));
    }

    #[test]
    fn pprof_difference_emits_valid_empty_profile_for_identical_inputs() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("no-difference.pb.gz");
        let mut candidate = Profile::new("operations", "operations", "count");
        candidate.sample(
            vec![("task".to_string(), "checkout".to_string())],
            1,
            vec![("evidence_id".to_string(), "candidate".to_string())],
        );
        let mut base = Profile::new("operations", "operations", "count");
        base.sample(
            vec![("task".to_string(), "checkout".to_string())],
            1,
            vec![("evidence_id".to_string(), "base".to_string())],
        );

        let difference = write_pprof_difference(&candidate, &base, &path, true).unwrap();
        assert!(difference.is_empty());

        let bytes = fs::read(path).unwrap();
        let mut decoder = GzDecoder::new(&bytes[..]);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).unwrap();
        let profile = PprofProfile::decode(&decoded[..]).unwrap();
        assert_eq!(profile.sample.len(), 2);
        assert_eq!(
            profile
                .sample
                .iter()
                .map(|sample| sample.value[0])
                .sum::<i64>(),
            0
        );
        assert_eq!(profile.sample_type.len(), 1);
    }
}
