use anyhow::{Context, Result, bail};
use chrono::Utc;
use flate2::{Compression, write::GzEncoder};
use prost::Message;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use crate::session::{
    SessionRecord, collapse_project_path, contains_private_marker, path_component_strings,
    short_hash, truncate_clean,
};

pub type Counter = BTreeMap<String, u64>;
pub type OpId = usize;
type Frame = (String, String);

pub struct StackNode {
    pub parent: Option<OpId>,
    pub kind: String,
    pub name: String,
    pub value: u64,
}

pub struct Profile {
    pub view: &'static str,
    pub sample_type: &'static str,
    pub unit: &'static str,
    pub ops: Vec<StackNode>,
    pub operation_stack_induction: Option<OperationStackInductionReport>,
    rank_rules: Vec<StackRankRule>,
    rank_operation_rules: Vec<StackRankRule>,
    rank_operation_matches: BTreeMap<String, BTreeMap<String, u64>>,
    rank_mode: StackRankMode,
}

impl Profile {
    fn new(view: &'static str, sample_type: &'static str, unit: &'static str) -> Self {
        Self {
            view,
            sample_type,
            unit,
            ops: Vec::new(),
            operation_stack_induction: None,
            rank_rules: Vec::new(),
            rank_operation_rules: Vec::new(),
            rank_operation_matches: BTreeMap::new(),
            rank_mode: StackRankMode::WidthBoost,
        }
    }

    fn with_rank_rules(mut self, rules: Vec<StackRankRule>) -> Self {
        self.rank_rules = rules;
        self
    }

    fn with_rank_mode(mut self, mode: StackRankMode) -> Self {
        self.rank_mode = mode;
        self
    }

    fn with_rank_operation_rules(mut self, rules: Vec<StackRankRule>) -> Self {
        self.rank_operation_rules = rules;
        self
    }

    fn sample(&mut self, frames: Vec<Frame>, value: u64) {
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

    fn record_rank_operation_matches(&mut self, stack: &str, sample: &Operation, value: u64) {
        if self.rank_operation_rules.is_empty() {
            return;
        }
        for rule in &self.rank_operation_rules {
            if sample.matches_field_token(&rule.regex) {
                *self
                    .rank_operation_matches
                    .entry(stack.to_string())
                    .or_default()
                    .entry(rule.label.clone())
                    .or_default() += value.max(1);
            }
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
            ProfileView::Operations => {
                "project,agent,dataset,task,session,prompt,phase,op,tool,action,cmd,process,path,domain,status"
            }
            ProfileView::Tokens => "project,agent,session,prompt,phase,op,call,model,token",
            ProfileView::Files => {
                "project,agent,session,prompt,phase,op,tool,cmd,process,path,effect,status"
            }
            ProfileView::Network => {
                "project,agent,session,prompt,phase,op,tool,cmd,process,domain,status"
            }
            ProfileView::Time => {
                "project,agent,session,prompt,phase,op,tool,cmd,process,call,model"
            }
        };
        parse_stack_spec(raw).expect("default stack spec is valid")
    }
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
    rank_rules: Vec<StackRankRule>,
    rank_operation_rules: Vec<StackRankRule>,
    rank_mode: StackRankMode,
    operation_stack_induction: Option<OperationStackInductionConfig>,
}

impl OperationStackConfig {
    pub fn for_view(view: ProfileView) -> Self {
        Self {
            stack: OperationStackSpec::default_for_view(view),
            field_rules: Vec::new(),
            filters: Vec::new(),
            rules: Vec::new(),
            rank_rules: Vec::new(),
            rank_operation_rules: Vec::new(),
            rank_mode: StackRankMode::WidthBoost,
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

    pub fn with_rank_rules(mut self, rank_rules: Vec<StackRankRule>) -> Self {
        self.rank_rules = rank_rules;
        self
    }

    pub fn with_rank_operation_rules(mut self, rank_operation_rules: Vec<StackRankRule>) -> Self {
        self.rank_operation_rules = rank_operation_rules;
        self
    }

    pub fn with_rank_mode(mut self, rank_mode: StackRankMode) -> Self {
        self.rank_mode = rank_mode;
        self
    }

    pub fn with_operation_stack_induction(mut self, config: OperationStackInductionConfig) -> Self {
        self.operation_stack_induction = Some(config);
        self
    }
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

#[derive(Clone)]
pub struct StackRankRule {
    label: String,
    pattern: String,
    weight: f64,
    regex: Regex,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StackRankMode {
    WidthBoost,
    RuleScore,
}

impl StackRankMode {
    fn policy_name(self, has_stack_rules: bool, has_operation_rules: bool) -> &'static str {
        if !has_stack_rules && !has_operation_rules {
            return "width";
        }
        match (self, has_operation_rules) {
            (Self::WidthBoost, false) => "width_times_visible_rule_multiplier",
            (Self::RuleScore, false) => "visible_rule_score_then_width",
            (Self::WidthBoost, true) => "width_times_visible_operation_rule_multiplier",
            (Self::RuleScore, true) => "visible_operation_rule_score_then_width",
        }
    }
}

impl std::fmt::Debug for StackRankRule {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StackRankRule")
            .field("label", &self.label)
            .field("pattern", &self.pattern)
            .field("weight", &self.weight)
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

    fn matches_field_token(&self, regex: &Regex) -> bool {
        self.fields.iter().any(|(key, values)| {
            values
                .iter()
                .any(|value| regex.is_match(&format!("{key}={value}")))
        })
    }
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

pub fn parse_stack_rank_rules(raw_rules: &[String]) -> Result<Vec<StackRankRule>> {
    raw_rules
        .iter()
        .map(|rule| parse_rank_rule(rule, "--rank-rule", false))
        .collect()
}

pub fn parse_operation_rank_rules(raw_rules: &[String]) -> Result<Vec<StackRankRule>> {
    raw_rules
        .iter()
        .map(|rule| parse_rank_rule(rule, "--rank-op-rule", true))
        .collect()
}

fn parse_rank_rule(raw: &str, flag_name: &str, allow_negative: bool) -> Result<StackRankRule> {
    let (left, pattern) = raw.split_once('=').ok_or_else(|| {
        anyhow::anyhow!("invalid {flag_name} {raw:?}; expected LABEL:WEIGHT=REGEX")
    })?;
    let (label, weight) = left.split_once(':').ok_or_else(|| {
        anyhow::anyhow!("invalid {flag_name} {raw:?}; expected LABEL:WEIGHT=REGEX")
    })?;
    validate_frame_name(label, "rank rule label")?;
    let weight = weight
        .parse::<f64>()
        .map_err(|error| anyhow::anyhow!("invalid {flag_name} weight {weight:?}: {error}"))?;
    if !weight.is_finite()
        || (!allow_negative && weight <= 0.0)
        || (allow_negative && weight == 0.0)
    {
        if allow_negative {
            bail!("invalid {flag_name} {raw:?}; weight must be a non-zero finite number");
        } else {
            bail!("invalid {flag_name} {raw:?}; weight must be a positive finite number");
        }
    }
    if pattern.is_empty() {
        bail!("invalid {flag_name} {raw:?}; regex pattern cannot be empty");
    }
    let regex = Regex::new(pattern)
        .map_err(|error| anyhow::anyhow!("invalid {flag_name} regex {pattern:?}: {error}"))?;
    Ok(StackRankRule {
        label: label.to_string(),
        pattern: pattern.to_string(),
        weight,
        regex,
    })
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

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OutputFormat {
    Pprof,
    Folded,
    Svg,
    Json,
}

#[derive(Serialize)]
pub struct CounterSummary {
    total_weight: u64,
    unique_stacks: usize,
    compression_ratio: f64,
    max_stack_reuse: u64,
    top: Vec<WeightedStack>,
}

#[derive(Serialize)]
pub struct WeightedStack {
    stack: String,
    weight: u64,
}

#[derive(Serialize)]
pub struct StackRankingSummary {
    policy: &'static str,
    groups: usize,
    limit: usize,
    rank_rules: Vec<StackRankRuleSpec>,
    rank_operation_rules: Vec<StackRankRuleSpec>,
    top: Vec<RankedStack>,
}

#[derive(Serialize)]
pub struct StackRankRuleSpec {
    label: String,
    pattern: String,
    weight: f64,
}

#[derive(Serialize)]
pub struct RankedStack {
    stack: String,
    weight: u64,
    rank_score: f64,
    matched_rank_rules: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    rank_operation_features: Vec<StackRankFeature>,
}

#[derive(Serialize)]
pub struct StackRankFeature {
    label: String,
    matched_weight: u64,
    fraction: f64,
    weighted_score: f64,
}

#[derive(Default)]
struct FlameNode {
    value: u64,
    children: BTreeMap<String, FlameNode>,
}

#[derive(Default)]
struct FlameRenderStats {
    drawn: usize,
    hidden_tiny: usize,
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
    let mut profile = Profile::new(name, sample_type, unit)
        .with_rank_rules(options.rank_rules.clone())
        .with_rank_operation_rules(options.rank_operation_rules.clone())
        .with_rank_mode(options.rank_mode);
    let mut samples = Vec::new();
    for session in sessions {
        for sample in session_samples(session, project_name, view) {
            let sample = apply_operation_field_rules(&sample, &options.field_rules);
            if !operation_matches_filters(&sample, &options.filters) {
                continue;
            }
            samples.push(sample);
        }
    }
    let (samples, report) = maybe_induce_operation_stack(samples, options)?;
    profile.operation_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let stack = folded_stack_from_frames(&frames);
        profile.record_rank_operation_matches(&stack, &sample, sample.value);
        profile.sample(frames, sample.value);
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
    let mut profile = Profile::new(name, sample_type, unit)
        .with_rank_rules(options.rank_rules.clone())
        .with_rank_operation_rules(options.rank_operation_rules.clone())
        .with_rank_mode(options.rank_mode);
    let mut samples = Vec::new();
    for sample in operations {
        let sample = apply_operation_field_rules(sample, &options.field_rules);
        if !operation_matches_filters(&sample, &options.filters) {
            continue;
        }
        samples.push(sample);
    }
    let (samples, report) = maybe_induce_operation_stack(samples, options)?;
    profile.operation_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let stack = folded_stack_from_frames(&frames);
        profile.record_rank_operation_matches(&stack, &sample, sample.value);
        profile.sample(frames, sample.value);
    }
    Ok(profile)
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
        "value": record.value.unwrap_or(1).max(1),
        "fields": fields,
    })
}

fn operation_from_record(record: OperationRecord) -> Result<Operation> {
    let mut operation = Operation::new(record.value.unwrap_or(1).max(1));
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
        for value in stack_frame_values(name, sample, &options.rules) {
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

fn operation_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let mut samples = Vec::new();
    for (idx, req) in session.user_requests.iter().enumerate() {
        let mut sample = base_sample(session, project_name, idx, 1);
        sample.insert("op", "prompt");
        sample.insert("phase", "prompt");
        sample.insert("status", "observed");
        sample.insert("prompt_hash", req.text_hash.clone());
        samples.push(sample);
    }
    for event in &session.tools {
        samples.push(tool_sample(session, project_name, event, 1));
    }
    for call in &session.llm_calls {
        let mut sample = base_sample(session, project_name, call.prompt_index, 1);
        sample.insert("op", "llm");
        sample.insert("phase", llm_phase_label(call));
        sample.insert("call", format!("llm/{}", call.tag));
        sample.insert("llm", call.tag.clone());
        sample.insert("llm_preview", call.preview.clone());
        sample.insert("model", last_model_segment(&call.model));
        sample.insert("status", "observed");
        samples.push(sample);
    }
    samples
}

fn token_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let mut samples = Vec::new();
    for call in &session.llm_calls {
        for (kind, value) in call.token_components() {
            let mut sample = base_sample(session, project_name, call.prompt_index, value);
            sample.insert("op", "llm");
            sample.insert("phase", llm_phase_label(call));
            sample.insert("call", format!("llm/{}", call.tag));
            sample.insert("llm", call.tag.clone());
            sample.insert("llm_preview", call.preview.clone());
            sample.insert("model", last_model_segment(&call.model));
            sample.insert("token", kind);
            samples.push(sample);
        }
    }
    samples
}

fn file_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let mut samples = Vec::new();
    for event in &session.tools {
        if event.path_groups.is_empty() {
            continue;
        }
        for group in &event.path_groups {
            let mut sample = tool_sample(session, project_name, event, 1);
            sample.insert("path", group.clone());
            samples.push(sample);
        }
    }
    samples
}

fn network_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
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
            sample.insert("domain", domain);
            samples.push(sample);
        }
    }
    samples
}

fn time_samples(session: &SessionRecord, project_name: &str) -> Vec<Operation> {
    let mut events = Vec::new();
    let mut ordinal = 0usize;

    for (idx, req) in session.user_requests.iter().enumerate() {
        if let Some(ts) = req.ts_ms {
            let mut sample = base_sample(session, project_name, idx, 0);
            sample.insert("op", "prompt");
            sample.insert("prompt_hash", req.text_hash.clone());
            events.push((ts, ordinal, sample));
            ordinal += 1;
        }
    }
    for event in &session.tools {
        if let Some(ts) = event.ts_ms {
            events.push((ts, ordinal, tool_sample(session, project_name, event, 0)));
            ordinal += 1;
        }
    }
    for call in &session.llm_calls {
        if let Some(ts) = call.ts_ms {
            let mut sample = base_sample(session, project_name, call.prompt_index, 0);
            sample.insert("op", "llm");
            sample.insert("phase", llm_phase_label(call));
            sample.insert("call", format!("llm/{}", call.tag));
            sample.insert("llm", call.tag.clone());
            sample.insert("llm_preview", call.preview.clone());
            sample.insert("model", last_model_segment(&call.model));
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
    if !session.task_tag.is_empty() {
        sample.insert("task", session.task_tag.clone());
    }
    sample.insert("prompt", req.tag.clone());
    sample.insert("prompt_hash", req.text_hash.clone());
    sample.insert("prompt_preview", req.preview.clone());
    sample
}

fn tool_sample(
    session: &SessionRecord,
    project_name: &str,
    event: &crate::session::ToolEvent,
    value: u64,
) -> Operation {
    let mut sample = base_sample(session, project_name, event.prompt_index, value);
    sample.insert("op", "tool");
    sample.insert("phase", tool_phase_label(event));
    sample.insert("tool", event.tool_name.clone());
    sample.insert("category", event.category.clone());
    sample.insert("command", event.command.clone());
    sample.insert("effect", event.effect.clone());
    sample.insert("status", event.status.clone());
    if event.category == "shell" && !event.command_name.is_empty() {
        sample.insert("cmd", event.command_name.clone());
    }
    sample.extend("process", event.process_chain.clone());
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

pub fn summarize_counter(counter: &Counter, limit: usize) -> CounterSummary {
    let total_weight = counter.values().sum::<u64>();
    let unique_stacks = counter.len();
    let max_stack_reuse = counter.values().copied().max().unwrap_or(0);
    CounterSummary {
        total_weight,
        unique_stacks,
        compression_ratio: if unique_stacks == 0 {
            0.0
        } else {
            round3(total_weight as f64 / unique_stacks as f64)
        },
        max_stack_reuse,
        top: top_stacks(counter, limit),
    }
}

pub fn summarize_ranked_counter(
    counter: &Counter,
    rules: &[StackRankRule],
    operation_rules: &[StackRankRule],
    operation_matches: &BTreeMap<String, BTreeMap<String, u64>>,
    mode: StackRankMode,
    limit: usize,
) -> StackRankingSummary {
    let mut rows = counter
        .iter()
        .map(|(stack, weight)| {
            rank_stack(
                stack,
                *weight,
                rules,
                operation_rules,
                operation_matches.get(stack),
                mode,
            )
        })
        .collect::<Vec<_>>();
    rows.sort_by(|left, right| {
        right
            .rank_score
            .partial_cmp(&left.rank_score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| right.weight.cmp(&left.weight))
            .then_with(|| left.stack.cmp(&right.stack))
    });
    rows.truncate(limit);

    StackRankingSummary {
        policy: mode.policy_name(!rules.is_empty(), !operation_rules.is_empty()),
        groups: counter.len(),
        limit,
        rank_rules: rules
            .iter()
            .map(|rule| StackRankRuleSpec {
                label: rule.label.clone(),
                pattern: rule.pattern.clone(),
                weight: round3(rule.weight),
            })
            .collect(),
        rank_operation_rules: operation_rules
            .iter()
            .map(|rule| StackRankRuleSpec {
                label: rule.label.clone(),
                pattern: rule.pattern.clone(),
                weight: round3(rule.weight),
            })
            .collect(),
        top: rows,
    }
}

fn rank_stack(
    stack: &str,
    weight: u64,
    rules: &[StackRankRule],
    operation_rules: &[StackRankRule],
    operation_matches: Option<&BTreeMap<String, u64>>,
    mode: StackRankMode,
) -> RankedStack {
    let mut matched_rank_rules = Vec::new();
    let mut stack_score = 0.0;
    for rule in rules {
        if rule.regex.is_match(stack) {
            stack_score += rule.weight;
            matched_rank_rules.push(rule.label.clone());
        }
    }
    let rank_operation_features =
        operation_rank_features(weight, operation_rules, operation_matches);
    let operation_score = rank_operation_features
        .iter()
        .map(|feature| feature.weighted_score)
        .sum::<f64>();
    let rule_score = stack_score + operation_score;
    RankedStack {
        stack: stack.to_string(),
        weight,
        rank_score: round3(match mode {
            StackRankMode::WidthBoost => weight as f64 * (1.0 + rule_score).max(0.0),
            StackRankMode::RuleScore => {
                if rules.is_empty() && operation_rules.is_empty() {
                    weight as f64
                } else {
                    rule_score
                }
            }
        }),
        matched_rank_rules,
        rank_operation_features,
    }
}

fn operation_rank_features(
    stack_weight: u64,
    rules: &[StackRankRule],
    matches: Option<&BTreeMap<String, u64>>,
) -> Vec<StackRankFeature> {
    if rules.is_empty() || stack_weight == 0 {
        return Vec::new();
    }
    let mut rows = Vec::new();
    for rule in rules {
        let matched_weight = matches
            .and_then(|matched| matched.get(&rule.label).copied())
            .unwrap_or(0);
        if matched_weight == 0 {
            continue;
        }
        let fraction = matched_weight as f64 / stack_weight as f64;
        rows.push(StackRankFeature {
            label: rule.label.clone(),
            matched_weight,
            fraction: round3(fraction),
            weighted_score: round3(fraction * rule.weight),
        });
    }
    rows
}

fn top_stacks(counter: &Counter, limit: usize) -> Vec<WeightedStack> {
    let mut rows = counter
        .iter()
        .map(|(stack, weight)| WeightedStack {
            stack: stack.clone(),
            weight: *weight,
        })
        .collect::<Vec<_>>();
    rows.sort_by_key(|row| (std::cmp::Reverse(row.weight), row.stack.clone()));
    rows.truncate(limit);
    rows
}

pub fn write_projection(
    projection: &Profile,
    format: OutputFormat,
    output: &Path,
    include_previews: bool,
    sessions: &[SessionRecord],
    svg_width: u32,
    deterministic_output: bool,
) -> Result<()> {
    ensure_parent_dir(output)?;
    let stacks = profile_to_stacks(projection);
    match format {
        OutputFormat::Pprof => write_pprof_projection(projection, &stacks, output, deterministic_output),
        OutputFormat::Folded => write_folded(output, &stacks),
        OutputFormat::Svg => fs::write(
            output,
            flamegraph_svg(
                &stacks,
                &format!("agentpprof {} profile", projection.view),
                projection.unit,
                svg_width,
            ),
        )
        .map_err(Into::into),
        OutputFormat::Json => fs::write(
            output,
            serde_json::to_vec_pretty(&json!({
                "schema_version": 1,
                "generated_at": if deterministic_output {
                    "1970-01-01T00:00:00Z".to_string()
                } else {
                    now_iso()
                },
                "profile": {
                    "view": projection.view,
                    "sample_type": projection.sample_type,
                    "unit": projection.unit,
                    "summary": summarize_counter(&stacks, 20),
                    "ranking": summarize_ranked_counter(
                        &stacks,
                        &projection.rank_rules,
                        &projection.rank_operation_rules,
                        &projection.rank_operation_matches,
                        projection.rank_mode,
                        stacks.len(),
                    ),
                    "operation_stack_induction": projection.operation_stack_induction,
                    "stacks": stacks,
                },
                "sessions": sessions.iter().map(|s| session_to_json(s, include_previews)).collect::<Vec<_>>(),
            }))?,
        )
        .map_err(Into::into),
    }
}

fn ensure_parent_dir(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent)?;
    }
    Ok(())
}

fn write_pprof_projection(
    projection: &Profile,
    stacks: &Counter,
    output: &Path,
    deterministic_output: bool,
) -> Result<()> {
    let mut strings = StringInterner::with_pprof_root();
    let sample_type = PprofValueType {
        type_: strings.intern(projection.sample_type),
        unit: strings.intern(projection.unit),
    };
    let label_view = strings.intern("view");
    let label_view_value = strings.intern(projection.view);
    let filename = strings.intern("agentpprof");
    let mut functions = Vec::new();
    let mut locations = Vec::new();
    let mut frame_locations = BTreeMap::<String, u64>::new();
    let mut samples = Vec::new();

    for (stack, weight) in stacks {
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
        samples.push(PprofSample {
            location_id: location_ids,
            value: vec![i64::try_from(*weight).unwrap_or(i64::MAX)],
            label: vec![PprofLabel {
                key: label_view,
                str_value: label_view_value,
            }],
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

fn write_folded(path: &Path, stacks: &Counter) -> Result<()> {
    let mut text = String::new();
    for (stack, weight) in stacks {
        text.push_str(stack);
        text.push(' ');
        text.push_str(&weight.to_string());
        text.push('\n');
    }
    fs::write(path, text)?;
    Ok(())
}

pub fn flamegraph_svg(stacks: &Counter, title: &str, metric: &str, svg_width: u32) -> String {
    let width = svg_width as f64;
    let total = stacks.values().sum::<u64>();
    if total == 0 {
        return format!(
            "<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='120'><text x='16' y='40'>{}</text></svg>",
            html_escape(title)
        );
    }
    let tree = build_flame_tree(stacks);
    let levels = flame_depth(&tree).max(1);
    let top = 72.0;
    let frame_h = 18.0;
    let gap = 2.0;
    let left = 16.0;
    let chart_width = width - 32.0;
    let height = top + levels as f64 * (frame_h + gap) + 30.0;
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{svg_width}' height='{height}' viewBox='0 0 {svg_width} {height}'>\
         <style>text{{font-family:ui-monospace,Menlo,monospace;font-size:11px;pointer-events:none}}.title{{font-family:system-ui,sans-serif;font-size:18px;font-weight:700}}.meta{{font-family:system-ui,sans-serif;font-size:12px;fill:#444}}rect:hover{{stroke:#111;stroke-width:1.2}}</style>\
         <rect width='{svg_width}' height='{height}' fill='#fbfbf7'/><text class='title' x='16' y='28'>{}</text>",
        html_escape(title),
    );
    let mut stats = FlameRenderStats::default();
    let mut path = Vec::new();
    render_flame_children(
        &mut svg,
        &tree,
        FlameRenderCtx {
            x: left,
            width: chart_width,
            depth: 0,
            max_depth: levels,
            total,
            top,
            frame_h,
            gap,
            metric,
        },
        &mut path,
        &mut stats,
    );
    svg.insert_str(
        svg.find("</text>").map(|pos| pos + "</text>".len()).unwrap_or(svg.len()),
        &format!(
            "<text class='meta' x='16' y='50'>prefix-merged flamegraph; width = {}; total = {}; drawn nodes = {}; hidden tiny nodes = {}; depth = {}</text>",
            html_escape(metric),
            total,
            stats.drawn,
            stats.hidden_tiny,
            levels
        ),
    );
    svg.push_str("</svg>");
    svg
}

fn build_flame_tree(stacks: &Counter) -> FlameNode {
    let mut root = FlameNode::default();
    for (stack, weight) in stacks {
        if *weight == 0 {
            continue;
        }
        root.value += *weight;
        let mut node = &mut root;
        for frame in stack.split(';').filter(|frame| !frame.is_empty()) {
            node = node.children.entry(frame.to_string()).or_default();
            node.value += *weight;
        }
    }
    root
}

fn flame_depth(node: &FlameNode) -> usize {
    node.children
        .values()
        .map(|child| 1 + flame_depth(child))
        .max()
        .unwrap_or(0)
}

struct FlameRenderCtx<'a> {
    x: f64,
    width: f64,
    depth: usize,
    max_depth: usize,
    total: u64,
    top: f64,
    frame_h: f64,
    gap: f64,
    metric: &'a str,
}

fn render_flame_children(
    svg: &mut String,
    node: &FlameNode,
    ctx: FlameRenderCtx<'_>,
    path: &mut Vec<String>,
    stats: &mut FlameRenderStats,
) {
    let mut cursor = ctx.x;
    let mut children = node.children.iter().collect::<Vec<_>>();
    children.sort_by(|(left_name, left), (right_name, right)| {
        right
            .value
            .cmp(&left.value)
            .then_with(|| left_name.cmp(right_name))
    });

    for (name, child) in children {
        let child_width = if node.value == 0 {
            0.0
        } else {
            ctx.width * child.value as f64 / node.value as f64
        };
        path.push(name.clone());
        render_flame_node(
            svg,
            name,
            child,
            FlameRenderCtx {
                x: cursor,
                width: child_width,
                depth: ctx.depth + 1,
                max_depth: ctx.max_depth,
                total: ctx.total,
                top: ctx.top,
                frame_h: ctx.frame_h,
                gap: ctx.gap,
                metric: ctx.metric,
            },
            path,
            stats,
        );
        path.pop();
        cursor += child_width;
    }
}

fn render_flame_node(
    svg: &mut String,
    name: &str,
    node: &FlameNode,
    ctx: FlameRenderCtx<'_>,
    path: &mut Vec<String>,
    stats: &mut FlameRenderStats,
) {
    const MIN_VISIBLE_WIDTH: f64 = 0.35;
    if ctx.width >= MIN_VISIBLE_WIDTH {
        stats.drawn += 1;
        let y = ctx.top + (ctx.max_depth - ctx.depth) as f64 * (ctx.frame_h + ctx.gap);
        let pct = if ctx.total == 0 {
            0.0
        } else {
            node.value as f64 * 100.0 / ctx.total as f64
        };
        let title = format!(
            "{} | {} {} ({pct:.2}%)",
            path.join(" ; "),
            node.value,
            ctx.metric
        );
        let color = color_for(name, ctx.depth);
        svg.push_str(&format!(
            "<g><title>{}</title><rect x='{:.3}' y='{:.3}' width='{:.3}' height='{:.0}' rx='2' ry='2' fill='{color}' stroke='#fff' stroke-width='.7'/>",
            html_escape(&title),
            ctx.x,
            y,
            ctx.width,
            ctx.frame_h
        ));
        if let Some(label) = label_for_width(name, ctx.width) {
            svg.push_str(&format!(
                "<text x='{:.3}' y='{:.3}' fill='#171717'>{}</text>",
                ctx.x + 4.0,
                y + ctx.frame_h - 4.0,
                html_escape(&label)
            ));
        }
        svg.push_str("</g>");
    } else {
        stats.hidden_tiny += 1;
    }

    if !node.children.is_empty() {
        render_flame_children(svg, node, ctx, path, stats);
    }
}

fn label_for_width(label: &str, width: f64) -> Option<String> {
    if width < 32.0 {
        return None;
    }
    let max_chars = ((width - 8.0) / 7.0).floor().max(3.0) as usize;
    Some(truncate_clean(label, max_chars))
}

fn prompt_index_status(count: usize) -> &'static str {
    if count <= 1 {
        "unique"
    } else {
        "duplicate_non_keyed"
    }
}

pub fn session_to_json(session: &SessionRecord, include_previews: bool) -> Value {
    let mut prompt_index_counts = HashMap::<usize, usize>::new();
    for req in &session.user_requests {
        *prompt_index_counts.entry(req.index).or_insert(0) += 1;
    }
    json!({
        "source": session.source,
        "session_id": session.session_id,
        "agent_sight_session_id": agent_sight_session_id(&session.source, &session.session_id),
        "session_file": session.path.file_name().and_then(|v| v.to_str()).unwrap_or("session"),
        "cwd_hash": if session.cwd.is_empty() { String::new() } else { short_hash(&session.cwd, 16) },
        "agent_role": session.agent_role,
        "model": session.model,
        "session_tag": session.session_tag,
        "task_tag": session.task_tag,
        "start_ts_ms": session.start_ts_ms,
        "prompt_count": session.user_requests.len(),
        "tool_count": session.tools.len(),
        "llm_count": session.llm_calls.len(),
        "prompts": session.user_requests.iter().enumerate().map(|(ordinal, req)| json!({
            "row_ordinal": ordinal,
            "index": req.index,
            "prompt_key": req.prompt_key(),
            "prompt_index_status": prompt_index_status(*prompt_index_counts.get(&req.index).unwrap_or(&0)),
            "ts_ms": req.ts_ms,
            "hash": req.text_hash,
            "tag": req.tag,
            "preview": if include_previews { req.preview.clone() } else { "redacted".to_string() },
        })).collect::<Vec<_>>(),
        "tool_events": session.tools.iter().map(|event| {
            let request = session.request_by_index(event.prompt_index);
            json!({
                "ts_ms": event.ts_ms,
                "prompt_index": request.index,
                "prompt_key": request.prompt_key(),
                "prompt_index_status": prompt_index_status(*prompt_index_counts.get(&request.index).unwrap_or(&0)),
                "prompt_tag": request.tag,
                "tool_name": event.tool_name,
                "category": event.category,
                "command_name": event.command_name,
                "command_hash": if event.command.is_empty() { String::new() } else { short_hash(&event.command, 16) },
                "command_preview": if include_previews { event.command.clone() } else { "redacted".to_string() },
                "process_chain": event.process_chain,
                "effect": event.effect,
                "status": event.status,
                "path_groups": event.path_groups,
                "domains": event.domains,
                "call_id_hash": event.call_id.as_ref().map(|id| short_hash(id, 16)),
            })
        }).collect::<Vec<_>>(),
        "llm_events": session.llm_calls.iter().map(|call| {
            let request = session.request_by_index(call.prompt_index);
            json!({
                "ts_ms": call.ts_ms,
                "prompt_index": request.index,
                "prompt_key": request.prompt_key(),
                "prompt_index_status": prompt_index_status(*prompt_index_counts.get(&request.index).unwrap_or(&0)),
                "prompt_tag": request.tag,
                "llm_tag": call.tag,
                "model": call.model,
                "hash": call.text_hash,
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "cache_tokens": call.cache_tokens,
                "estimated_tokens": call.total_tokens,
                "preview": if include_previews { call.preview.clone() } else { "redacted".to_string() },
            })
        }).collect::<Vec<_>>()
    })
}

pub fn safe_frame(text: &str, prefix: Option<&str>) -> String {
    let text = redact_private_frame_text(text, prefix);
    let text = normalize_frame_text(&text, prefix);
    let mut out = String::new();
    for ch in text.to_ascii_lowercase().chars() {
        if ch.is_ascii_alphanumeric() || "._:/+-".contains(ch) {
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

fn agent_family(source: &str) -> String {
    if source.starts_with("codex") {
        "codex".to_string()
    } else if source.starts_with("claude") {
        "claude".to_string()
    } else {
        source.to_string()
    }
}

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

fn agent_sight_session_id(source: &str, session_id: &str) -> String {
    let family = agent_family(source);
    format!("local:{family}:{family}:{}", short_session_id(session_id))
}

fn last_model_segment(model: &str) -> &str {
    model.rsplit('/').next().unwrap_or(model)
}

fn round3(value: f64) -> f64 {
    (value * 1000.0).round() / 1000.0
}

fn html_escape(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn color_for(text: &str, depth: usize) -> String {
    let digest = Sha256::digest(text.as_bytes());
    let hue = (digest[0] as usize + depth * 19) % 360;
    let sat = 48 + digest[1] % 20;
    let light = 62 + digest[2] % 12;
    format!("hsl({hue} {sat}% {light}%)")
}

fn now_iso() -> String {
    Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

pub fn infer_output_format(requested: OutputFormat, output: &Path) -> OutputFormat {
    if requested != OutputFormat::Pprof {
        return requested;
    }
    match output.extension().and_then(|ext| ext.to_str()) {
        Some("folded") | Some("foldedtxt") => OutputFormat::Folded,
        Some("svg") => OutputFormat::Svg,
        Some("json") => OutputFormat::Json,
        _ => OutputFormat::Pprof,
    }
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
        }
    }

    fn llm(ts_ms: i64, prompt_index: usize, model: &str, tag: &str) -> LlmEvent {
        LlmEvent {
            ts_ms: Some(ts_ms),
            prompt_index,
            model: model.to_string(),
            text_hash: "l0".to_string(),
            preview: "answer".to_string(),
            input_tokens: 1,
            output_tokens: 1,
            cache_tokens: 0,
            total_tokens: 0,
            tag: tag.to_string(),
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
            stacks.get("project:agentsight;agent:codex;session:rustfix;prompt:debug;op:prompt"),
            Some(&2)
        );
        // tool at 3000ms, llm at 8000ms -> 5 seconds (with tool name, cmd, and process chain)
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;session:rustfix;prompt:debug;phase:test;op:tool;tool:exec_command;cmd:cargo;process:cargo"),
            Some(&5)
        );
        // last event gets 1 second (with llm details)
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;session:rustfix;prompt:debug;phase:summarize;op:llm;call:llm/summarize;model:gpt-5"),
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
            stacks.get("project:agentsight;agent:codex;session:rustfix;prompt:debug;phase:read;op:tool;tool:read;path:src;effect:read;status:ok"),
            Some(&1)
        );
        assert_eq!(
            stacks.get("project:agentsight;agent:codex;session:rustfix;prompt:debug;phase:test;op:tool;tool:exec_command;cmd:cargo;process:cargo;path:tests;effect:test;status:ok"),
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
        let json = session_to_json(&session, false);
        assert_eq!(json["session_tag"], "shopping");
        assert_eq!(json["task_tag"], "webshop");
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
    fn stack_rank_rules_sort_json_groups_by_visible_frames() {
        let rules = parse_stack_rank_rules(&[
            "unsafe-risk:2=phase:execute|action:write".to_string(),
            "error-risk:1.5=status:error".to_string(),
        ])
        .unwrap();
        let stacks = BTreeMap::from([
            (
                "project:external;task:safety;phase:inspect;action:read;status:ok".to_string(),
                9_u64,
            ),
            (
                "project:external;task:safety;phase:execute;action:write;status:error".to_string(),
                3_u64,
            ),
        ]);

        let ranking = summarize_ranked_counter(
            &stacks,
            &rules,
            &[],
            &BTreeMap::new(),
            StackRankMode::WidthBoost,
            10,
        );

        assert_eq!(ranking.policy, "width_times_visible_rule_multiplier");
        assert_eq!(
            ranking.top[0].stack,
            "project:external;task:safety;phase:execute;action:write;status:error"
        );
        assert_eq!(ranking.top[0].weight, 3);
        assert_eq!(ranking.top[0].rank_score, 13.5);
        assert_eq!(
            ranking.top[0].matched_rank_rules,
            vec!["unsafe-risk".to_string(), "error-risk".to_string()]
        );
        assert_eq!(ranking.top[1].rank_score, 9.0);
    }

    #[test]
    fn rule_score_rank_mode_sorts_before_width_tiebreaker() {
        let rules = parse_stack_rank_rules(&["unsafe-risk:2=phase:execute".to_string()]).unwrap();
        let stacks = BTreeMap::from([
            (
                "project:external;task:safety;phase:inspect;action:read;status:ok".to_string(),
                100_u64,
            ),
            (
                "project:external;task:safety;phase:execute;action:write;status:error".to_string(),
                3_u64,
            ),
        ]);

        let ranking = summarize_ranked_counter(
            &stacks,
            &rules,
            &[],
            &BTreeMap::new(),
            StackRankMode::RuleScore,
            10,
        );

        assert_eq!(ranking.policy, "visible_rule_score_then_width");
        assert_eq!(
            ranking.top[0].stack,
            "project:external;task:safety;phase:execute;action:write;status:error"
        );
        assert_eq!(ranking.top[0].rank_score, 2.0);
        assert_eq!(ranking.top[1].rank_score, 0.0);
    }

    #[test]
    fn operation_rank_rules_score_density_inside_folded_stack() {
        let records = vec![
            json!({"value": 1, "fields": {"task": "wide", "status": "error"}}),
            json!({"value": 3, "fields": {"task": "wide", "status": "ok"}}),
            json!({"value": 1, "fields": {"task": "narrow", "status": "error"}}),
        ];
        let stack = parse_stack_spec("task").unwrap();
        let rank_operation_rules =
            parse_operation_rank_rules(&["failure:2=status=error".to_string()]).unwrap();
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(stack)
            .with_rank_operation_rules(rank_operation_rules)
            .with_rank_mode(StackRankMode::RuleScore);
        let profile =
            build_profile_from_operation_records(&records, ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);
        let ranking = summarize_ranked_counter(
            &stacks,
            &profile.rank_rules,
            &profile.rank_operation_rules,
            &profile.rank_operation_matches,
            profile.rank_mode,
            10,
        );

        assert_eq!(ranking.policy, "visible_operation_rule_score_then_width");
        assert_eq!(ranking.top[0].stack, "task:narrow");
        assert_eq!(ranking.top[0].rank_score, 2.0);
        assert_eq!(ranking.top[0].rank_operation_features[0].matched_weight, 1);
        assert_eq!(ranking.top[0].rank_operation_features[0].fraction, 1.0);
        assert_eq!(ranking.top[1].stack, "task:wide");
        assert_eq!(ranking.top[1].rank_score, 0.5);
        assert_eq!(ranking.top[1].rank_operation_features[0].matched_weight, 1);
        assert_eq!(ranking.top[1].rank_operation_features[0].fraction, 0.25);
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
    fn json_report_exports_prompt_keys_when_prompt_indexes_repeat() {
        let mut tool = shell_tool(3, 1, "ok", Vec::new());
        tool.tool_name = "Bash".to_string();
        tool.call_id = None;
        let session = test_session(
            "claude",
            "review",
            vec![
                prompt(0, 1, "h0", "first prompt", "review"),
                prompt(0, 2, "h1", "second prompt", "test"),
            ],
            vec![tool],
            vec![llm(4, 0, "claude", "answer")],
        );

        let payload = session_to_json(&session, false);
        let prompts = payload["prompts"].as_array().expect("prompts array");
        assert_eq!(prompts[0]["prompt_key"], "0:h0");
        assert_eq!(prompts[1]["prompt_key"], "0:h1");
        assert_eq!(prompts[0]["prompt_index_status"], "duplicate_non_keyed");
        assert_eq!(prompts[1]["prompt_index_status"], "duplicate_non_keyed");

        let tool = &payload["tool_events"].as_array().expect("tool events")[0];
        assert_eq!(tool["prompt_index"], 0);
        assert_eq!(tool["prompt_key"], "0:h1");
        assert_eq!(tool["prompt_tag"], "test");
        assert_eq!(tool["prompt_index_status"], "duplicate_non_keyed");

        let llm = &payload["llm_events"].as_array().expect("llm events")[0];
        assert_eq!(llm["prompt_index"], 0);
        assert_eq!(llm["prompt_key"], "0:h0");
        assert_eq!(llm["prompt_tag"], "review");
        assert_eq!(llm["prompt_index_status"], "duplicate_non_keyed");
    }

    #[test]
    fn pprof_writer_emits_gzip_profile() {
        use flate2::read::GzDecoder;
        use std::io::Read;

        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("profile.pb.gz");
        let projection = Profile::new("tokens", "tokens", "count");
        let stacks = BTreeMap::from([(
            "project:test;agent:codex;session:rustfix;prompt:review;op:llm;token:input".to_string(),
            7,
        )]);
        write_pprof_projection(&projection, &stacks, &path, false).unwrap();

        let bytes = fs::read(path).unwrap();
        let mut decoder = GzDecoder::new(&bytes[..]);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded).unwrap();
        let profile = PprofProfile::decode(&decoded[..]).unwrap();
        assert_eq!(profile.sample.len(), 1);
        assert_eq!(profile.sample[0].value, vec![7]);
    }

    #[test]
    fn svg_flamegraph_merges_common_prefixes() {
        let stacks = BTreeMap::from([
            ("project:test;agent:codex;prompt:debug".to_string(), 7_u64),
            ("project:test;agent:codex;prompt:review".to_string(), 3_u64),
        ]);
        let svg = flamegraph_svg(&stacks, "test", "count", 1800);
        assert!(svg.contains("prefix-merged flamegraph"));
        assert!(svg.contains("project:test | 10 count"));
        assert!(svg.contains("project:test ; agent:codex | 10 count"));
        assert!(!svg.contains("project:test | 7 count"));
        assert!(!svg.contains("project:test | 3 count"));
    }
}
