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
    pub task_stack_induction: Option<TaskStackInductionReport>,
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
            task_stack_induction: None,
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
    task_stack_induction: Option<TaskStackInductionConfig>,
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
            task_stack_induction: None,
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

    pub fn with_task_stack_induction(mut self, config: TaskStackInductionConfig) -> Self {
        self.task_stack_induction = Some(config);
        self
    }
}

#[derive(Clone, Debug)]
pub struct TaskStackInductionConfig {
    allow_session: bool,
    max_depth: usize,
    min_score: f64,
    min_second_child: u64,
    max_majority_fraction: f64,
    min_node_weight: u64,
    query_terms: Vec<String>,
}

impl TaskStackInductionConfig {
    pub fn new() -> Self {
        Self {
            allow_session: false,
            max_depth: 4,
            min_score: 0.055,
            min_second_child: 5,
            max_majority_fraction: 0.985,
            min_node_weight: 10,
            query_terms: Vec::new(),
        }
    }

    pub fn with_allow_session(mut self, allow_session: bool) -> Self {
        self.allow_session = allow_session;
        self
    }

    pub fn with_max_depth(mut self, max_depth: usize) -> Self {
        self.max_depth = max_depth.max(1);
        self
    }

    pub fn with_query_terms(mut self, terms: Vec<String>) -> Self {
        self.query_terms = terms
            .into_iter()
            .map(|term| term.trim().to_ascii_lowercase())
            .filter(|term| !term.is_empty())
            .collect();
        self
    }

    #[cfg(test)]
    fn with_min_score(mut self, min_score: f64) -> Self {
        self.min_score = min_score;
        self
    }

    #[cfg(test)]
    fn with_min_second_child(mut self, min_second_child: u64) -> Self {
        self.min_second_child = min_second_child;
        self
    }

    #[cfg(test)]
    fn with_min_node_weight(mut self, min_node_weight: u64) -> Self {
        self.min_node_weight = min_node_weight;
        self
    }
}

impl Default for TaskStackInductionConfig {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct TaskStackInductionReport {
    policy: &'static str,
    allow_session: bool,
    max_depth: usize,
    min_score: f64,
    min_second_child: u64,
    max_majority_fraction: f64,
    selected_source_fields: Vec<String>,
    excluded_oracle_fields: Vec<&'static str>,
    excluded_oracle_prefixes: Vec<&'static str>,
    excluded_oracle_suffixes: Vec<&'static str>,
    stop_reasons: BTreeMap<String, u64>,
    split_decisions: Vec<TaskStackSplitDecision>,
}

#[derive(Clone, Debug, Serialize)]
pub struct TaskStackSplitDecision {
    path: Vec<String>,
    source_field: String,
    node_weight: u64,
    selected_score: TaskStackSplitScore,
    candidate_scores: Vec<TaskStackSplitScore>,
}

#[derive(Clone, Debug, Serialize)]
pub struct TaskStackSplitScore {
    field: String,
    cut_after: usize,
    left_label: String,
    right_label: String,
    left_weight: u64,
    right_weight: u64,
    evidence_fields: Vec<String>,
    score: f64,
    structural_gain: f64,
    balance: f64,
    coverage: f64,
    query_bonus: f64,
    semantic_shift: f64,
    changed_field_fraction: f64,
    changed_fields: Vec<String>,
    cardinality_penalty: f64,
    small_child_penalty: f64,
    groups: BTreeMap<String, u64>,
}

#[derive(Clone, Debug)]
struct TaskBoundaryEvidence {
    changed_fields: Vec<String>,
    semantic_shift: f64,
    query_bonus: f64,
    changed_field_fraction: f64,
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
) -> Profile {
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
    let (samples, report) = maybe_induce_task_stack(samples, options);
    profile.task_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let stack = folded_stack_from_frames(&frames);
        profile.record_rank_operation_matches(&stack, &sample, sample.value);
        profile.sample(frames, sample.value);
    }
    profile
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
    Ok(build_profile_from_operations(&operations, view, options))
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
    Ok(build_profile_from_operations(&operations, view, options))
}

fn build_profile_from_operations(
    operations: &[Operation],
    view: ProfileView,
    options: &OperationStackConfig,
) -> Profile {
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
    let (samples, report) = maybe_induce_task_stack(samples, options);
    profile.task_stack_induction = report;
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let stack = folded_stack_from_frames(&frames);
        profile.record_rank_operation_matches(&stack, &sample, sample.value);
        profile.sample(frames, sample.value);
    }
    profile
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

const TASK_STACK_POLICY: &str = "query-conditioned-recursive-boundary-task-stack-induction";
const MAX_TASK_STACK_BOUNDARY_CANDIDATES: usize = 512;
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
const TASK_STACK_METADATA_FIELDS: &[&str] = &[
    "agent",
    "analysis_task",
    "benchmark",
    "dataset",
    "environment",
    "experiment",
    "project",
    "query_family",
    "source",
    "source_operation_file",
];
const TASK_STACK_NOISY_FIELDS: &[&str] = &[
    "busted_retry",
    "input_tokens",
    "llm_retries",
    "output_tokens",
    "target",
    "turn",
];

fn maybe_induce_task_stack(
    samples: Vec<Operation>,
    options: &OperationStackConfig,
) -> (Vec<Operation>, Option<TaskStackInductionReport>) {
    let Some(config) = options.task_stack_induction.as_ref() else {
        return (samples, None);
    };
    let (samples, report) = induce_task_stack(samples, config);
    (samples, Some(report))
}

fn induce_task_stack(
    mut samples: Vec<Operation>,
    config: &TaskStackInductionConfig,
) -> (Vec<Operation>, TaskStackInductionReport) {
    let indices = (0..samples.len()).collect::<Vec<_>>();
    let mut task_paths = vec![Vec::<String>::new(); samples.len()];
    let mut stop_reasons = BTreeMap::new();
    let mut split_decisions = Vec::new();
    induce_task_stack_recursive(
        &samples,
        &indices,
        config,
        Vec::new(),
        0,
        &mut task_paths,
        &mut stop_reasons,
        &mut split_decisions,
    );
    for (sample, path) in samples.iter_mut().zip(task_paths) {
        sample.fields.insert("task".to_string(), path);
    }
    let mut selected_source_fields = BTreeSet::new();
    for decision in &split_decisions {
        if decision.selected_score.evidence_fields.is_empty() {
            selected_source_fields.insert(decision.source_field.clone());
        } else {
            selected_source_fields.extend(decision.selected_score.evidence_fields.iter().cloned());
        }
    }
    let selected_source_fields = selected_source_fields.into_iter().collect::<Vec<_>>();
    let report = TaskStackInductionReport {
        policy: TASK_STACK_POLICY,
        allow_session: config.allow_session,
        max_depth: config.max_depth,
        min_score: round6(config.min_score),
        min_second_child: config.min_second_child,
        max_majority_fraction: round6(config.max_majority_fraction),
        selected_source_fields,
        excluded_oracle_fields: ORACLE_OR_LABEL_FIELDS.to_vec(),
        excluded_oracle_prefixes: ORACLE_OR_LABEL_PREFIXES.to_vec(),
        excluded_oracle_suffixes: ORACLE_OR_LABEL_SUFFIXES.to_vec(),
        stop_reasons,
        split_decisions,
    };
    (samples, report)
}

#[allow(clippy::too_many_arguments)]
fn induce_task_stack_recursive(
    samples: &[Operation],
    indices: &[usize],
    config: &TaskStackInductionConfig,
    path: Vec<String>,
    depth: usize,
    task_paths: &mut [Vec<String>],
    stop_reasons: &mut BTreeMap<String, u64>,
    split_decisions: &mut Vec<TaskStackSplitDecision>,
) {
    let node_weight = index_weight(samples, indices);
    if depth >= config.max_depth {
        assign_task_path(indices, &path, task_paths);
        increment_stop(stop_reasons, "max_depth");
        return;
    }
    if node_weight < config.min_node_weight {
        assign_task_path(indices, &path, task_paths);
        increment_stop(stop_reasons, "small_node");
        return;
    }

    let (selected, candidates) = choose_task_split(samples, indices, config);
    let Some(selected) = selected else {
        assign_task_path(indices, &path, task_paths);
        increment_stop(stop_reasons, "no_material_split");
        return;
    };

    let source_field = selected.field.clone();
    let cut_after = selected.cut_after.min(indices.len().saturating_sub(1));
    let (left_indices, right_indices) = indices.split_at(cut_after);
    if left_indices.is_empty() || right_indices.is_empty() {
        assign_task_path(indices, &path, task_paths);
        increment_stop(stop_reasons, "empty_boundary_child");
        return;
    }
    let left_label = selected.left_label.clone();
    let right_label = selected.right_label.clone();
    split_decisions.push(TaskStackSplitDecision {
        path: path.clone(),
        source_field: source_field.clone(),
        node_weight,
        selected_score: selected,
        candidate_scores: candidates,
    });

    for (value, child_indices) in [(left_label, left_indices), (right_label, right_indices)] {
        let mut child_path = path.clone();
        push_task_path_label(&mut child_path, value);
        induce_task_stack_recursive(
            samples,
            &child_indices,
            config,
            child_path,
            depth + 1,
            task_paths,
            stop_reasons,
            split_decisions,
        );
    }
}

fn push_task_path_label(path: &mut Vec<String>, value: String) {
    if path.last() != Some(&value) {
        path.push(value);
    }
}

fn assign_task_path(indices: &[usize], path: &[String], task_paths: &mut [Vec<String>]) {
    let path = if path.is_empty() {
        vec!["all".to_string()]
    } else {
        path.to_vec()
    };
    for index in indices {
        task_paths[*index] = path.clone();
    }
}

fn increment_stop(stop_reasons: &mut BTreeMap<String, u64>, reason: &str) {
    *stop_reasons.entry(reason.to_string()).or_default() += 1;
}

fn choose_task_split(
    samples: &[Operation],
    indices: &[usize],
    config: &TaskStackInductionConfig,
) -> (Option<TaskStackSplitScore>, Vec<TaskStackSplitScore>) {
    let candidates = task_stack_candidate_fields(samples, indices, config);
    let boundary_cuts = task_stack_boundary_cuts(samples, indices, &candidates, config);
    let mut scores = boundary_cuts
        .into_iter()
        .filter_map(|cut_after| {
            score_task_boundary_split(samples, indices, cut_after, &candidates, config)
        })
        .collect::<Vec<_>>();
    scores.sort_by(|left, right| {
        right
            .score
            .partial_cmp(&left.score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| left.cut_after.cmp(&right.cut_after))
    });
    let selected = scores
        .first()
        .filter(|score| score.score >= round6(config.min_score))
        .cloned();
    scores.truncate(8);
    (selected, scores)
}

fn task_stack_boundary_cuts(
    samples: &[Operation],
    indices: &[usize],
    candidates: &[String],
    config: &TaskStackInductionConfig,
) -> Vec<usize> {
    if indices.len() <= 1 || candidates.is_empty() {
        return Vec::new();
    }
    let mut cuts = Vec::new();
    for cut_after in 1..indices.len() {
        if adjacent_boundary_evidence(samples, indices, cut_after, candidates, config).is_some() {
            cuts.push(cut_after);
        }
    }
    if cuts.len() <= MAX_TASK_STACK_BOUNDARY_CANDIDATES {
        return cuts;
    }
    let stride = cuts.len().div_ceil(MAX_TASK_STACK_BOUNDARY_CANDIDATES);
    cuts.into_iter()
        .enumerate()
        .filter_map(|(idx, cut)| (idx % stride == 0).then_some(cut))
        .take(MAX_TASK_STACK_BOUNDARY_CANDIDATES)
        .collect()
}

fn task_stack_candidate_fields(
    samples: &[Operation],
    indices: &[usize],
    config: &TaskStackInductionConfig,
) -> Vec<String> {
    let mut fields = BTreeSet::new();
    for index in indices {
        fields.extend(samples[*index].fields.keys().cloned());
    }
    fields
        .into_iter()
        .filter(|field| {
            !field.starts_with('_')
                && !is_task_stack_oracle_field(field)
                && !TASK_STACK_METADATA_FIELDS.contains(&field.as_str())
                && !TASK_STACK_NOISY_FIELDS.contains(&field.as_str())
                && (config.allow_session || field != "session")
                && task_stack_field_is_candidate(samples, indices, field)
        })
        .collect()
}

fn task_stack_field_is_candidate(samples: &[Operation], indices: &[usize], field: &str) -> bool {
    let counts = weighted_value_counts(samples, indices, field);
    if counts.len() <= 1 || counts.len() > std::cmp::max(40, indices.len() / 2) {
        return false;
    }
    let numeric = indices
        .iter()
        .filter(|index| is_numeric_value(&operation_field_value(&samples[**index], field)))
        .count();
    (numeric as f64 / indices.len().max(1) as f64) <= 0.8
}

fn adjacent_boundary_evidence(
    samples: &[Operation],
    indices: &[usize],
    cut_after: usize,
    candidates: &[String],
    config: &TaskStackInductionConfig,
) -> Option<TaskBoundaryEvidence> {
    if cut_after == 0 || cut_after >= indices.len() || candidates.is_empty() {
        return None;
    }
    let left = &samples[indices[cut_after - 1]];
    let right = &samples[indices[cut_after]];
    let changed_fields = candidates
        .iter()
        .filter(|field| operation_field_value(left, field) != operation_field_value(right, field))
        .cloned()
        .collect::<Vec<_>>();
    let left_tokens = visible_operation_tokens(left, candidates);
    let right_tokens = visible_operation_tokens(right, candidates);
    let semantic_shift = token_set_distance(&left_tokens, &right_tokens);
    if changed_fields.is_empty() && semantic_shift <= 0.0 {
        return None;
    }
    let query_bonus = query_bonus(
        "boundary",
        left_tokens.iter().chain(right_tokens.iter()),
        &config.query_terms,
    );
    Some(TaskBoundaryEvidence {
        changed_field_fraction: changed_fields.len() as f64 / candidates.len().max(1) as f64,
        changed_fields,
        semantic_shift,
        query_bonus,
    })
}

fn visible_operation_tokens(sample: &Operation, candidates: &[String]) -> BTreeSet<String> {
    let mut tokens = BTreeSet::new();
    for field in candidates {
        tokenize_visible_text(field, &mut tokens);
        for value in sample.values(field) {
            tokenize_visible_text(value, &mut tokens);
            tokens.insert(format!(
                "{}={}",
                normalize_token(field),
                normalize_token(value)
            ));
        }
    }
    tokens.retain(|token| !token.is_empty() && token != "unknown");
    tokens
}

fn tokenize_visible_text(text: &str, tokens: &mut BTreeSet<String>) {
    let mut current = String::new();
    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() {
            current.push(ch.to_ascii_lowercase());
        } else if !current.is_empty() {
            if current.len() >= 2 {
                tokens.insert(current.clone());
            }
            current.clear();
        }
    }
    if current.len() >= 2 {
        tokens.insert(current);
    }
}

fn normalize_token(text: &str) -> String {
    let mut out = String::new();
    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() {
            out.push(ch.to_ascii_lowercase());
        } else if !out.ends_with('_') {
            out.push('_');
        }
    }
    out.trim_matches('_').to_string()
}

fn token_set_distance(left: &BTreeSet<String>, right: &BTreeSet<String>) -> f64 {
    if left.is_empty() && right.is_empty() {
        return 0.0;
    }
    let intersection = left.intersection(right).count() as f64;
    let union = left.union(right).count().max(1) as f64;
    1.0 - intersection / union
}

fn is_task_stack_oracle_field(field: &str) -> bool {
    ORACLE_OR_LABEL_FIELDS.contains(&field)
        || ORACLE_OR_LABEL_PREFIXES
            .iter()
            .any(|prefix| field.starts_with(prefix))
        || ORACLE_OR_LABEL_SUFFIXES
            .iter()
            .any(|suffix| field.ends_with(suffix))
}

fn is_numeric_value(value: &str) -> bool {
    let mut seen_digit = false;
    let mut seen_dot = false;
    for (idx, ch) in value.chars().enumerate() {
        if idx == 0 && ch == '-' {
            continue;
        }
        if ch == '.' && !seen_dot {
            seen_dot = true;
            continue;
        }
        if ch.is_ascii_digit() {
            seen_digit = true;
            continue;
        }
        return false;
    }
    seen_digit
}

fn score_task_boundary_split(
    samples: &[Operation],
    indices: &[usize],
    cut_after: usize,
    candidates: &[String],
    config: &TaskStackInductionConfig,
) -> Option<TaskStackSplitScore> {
    if cut_after == 0 || cut_after >= indices.len() {
        return None;
    }
    let (left, right) = indices.split_at(cut_after);
    let boundary = adjacent_boundary_evidence(samples, indices, cut_after, candidates, config)?;
    let left_weight = index_weight(samples, left);
    let right_weight = index_weight(samples, right);
    let total = left_weight + right_weight;
    let majority_fraction = left_weight.max(right_weight) as f64 / total.max(1) as f64;
    if left_weight.min(right_weight) < config.min_second_child
        || majority_fraction > config.max_majority_fraction
    {
        return None;
    }

    let mut evidence_scores = candidates
        .iter()
        .filter_map(|field| {
            score_boundary_evidence_field(samples, indices, left, right, field, &config.query_terms)
        })
        .collect::<Vec<_>>();
    evidence_scores.sort_by(|left, right| {
        right
            .1
            .partial_cmp(&left.1)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| left.0.cmp(&right.0))
    });
    let primary_field = evidence_scores.first().map(|item| item.0.clone())?;
    let evidence_fields = evidence_scores
        .iter()
        .take(4)
        .map(|item| item.0.clone())
        .collect::<Vec<_>>();
    let structural_gain = if evidence_scores.is_empty() {
        0.0
    } else {
        evidence_scores
            .iter()
            .take(4)
            .map(|(_, score, _, _)| *score)
            .sum::<f64>()
            / evidence_scores.len().min(4) as f64
    };
    let query_bonus = evidence_scores
        .iter()
        .map(|(_, _, query, _)| *query)
        .fold(boundary.query_bonus, f64::max);
    let adjacent_change = evidence_scores
        .iter()
        .map(|(_, _, _, change)| *change)
        .fold(boundary.changed_field_fraction, f64::max);
    let child_counts = BTreeMap::from([
        ("left".to_string(), left_weight),
        ("right".to_string(), right_weight),
    ]);
    let balance = entropy(&child_counts);
    let coverage = 1.0 - majority_fraction;
    let cardinality_penalty = 1.0 / ((total + 1) as f64).log2().max(1.0);
    let small_child_penalty = if left_weight.min(right_weight) < config.min_second_child * 2 {
        0.5
    } else {
        0.0
    };
    let score = 0.46 * structural_gain
        + 0.20 * balance * coverage
        + 0.16 * query_bonus
        + 0.18 * boundary.semantic_shift
        + 0.12 * adjacent_change
        - 0.08 * cardinality_penalty
        - 0.20 * small_child_penalty;
    let left_label = task_stack_segment_label(samples, left, &evidence_fields, "left");
    let right_label = task_stack_segment_label(samples, right, &evidence_fields, "right");
    let groups = BTreeMap::from([
        (left_label.clone(), left_weight),
        (right_label.clone(), right_weight),
    ]);
    Some(TaskStackSplitScore {
        field: primary_field,
        cut_after,
        left_label,
        right_label,
        left_weight,
        right_weight,
        evidence_fields,
        score: round6(score),
        structural_gain: round6(structural_gain),
        balance: round6(balance),
        coverage: round6(coverage),
        query_bonus: round6(query_bonus),
        semantic_shift: round6(boundary.semantic_shift),
        changed_field_fraction: round6(boundary.changed_field_fraction),
        changed_fields: boundary.changed_fields,
        cardinality_penalty: round6(cardinality_penalty),
        small_child_penalty: round6(small_child_penalty),
        groups,
    })
}

fn score_boundary_evidence_field(
    samples: &[Operation],
    parent: &[usize],
    left: &[usize],
    right: &[usize],
    field: &str,
    query_terms: &[String],
) -> Option<(String, f64, f64, f64)> {
    let parent_counts = weighted_value_counts(samples, parent, field);
    if parent_counts.len() <= 1 {
        return None;
    }
    let parent_entropy = entropy(&parent_counts);
    if parent_entropy <= 0.0 {
        return None;
    }
    let left_counts = weighted_value_counts(samples, left, field);
    let right_counts = weighted_value_counts(samples, right, field);
    let left_dominant = dominant_value(&left_counts)?;
    let right_dominant = dominant_value(&right_counts)?;
    if left_dominant == right_dominant {
        return None;
    }
    let left_weight = index_weight(samples, left);
    let right_weight = index_weight(samples, right);
    let total = (left_weight + right_weight).max(1) as f64;
    let child_entropy = (left_weight as f64 / total) * entropy(&left_counts)
        + (right_weight as f64 / total) * entropy(&right_counts);
    let partition_gain = ((parent_entropy - child_entropy) / parent_entropy).max(0.0);
    let adjacent_change = if operation_field_value(&samples[*left.last()?], field)
        != operation_field_value(&samples[*right.first()?], field)
    {
        1.0
    } else {
        0.0
    };
    let query_bonus = query_bonus(
        field,
        left_counts.keys().chain(right_counts.keys()),
        query_terms,
    );
    let score = 0.72 * partition_gain + 0.28 * adjacent_change;
    Some((field.to_string(), score, query_bonus, adjacent_change))
}

fn task_stack_segment_label(
    samples: &[Operation],
    indices: &[usize],
    evidence_fields: &[String],
    fallback: &str,
) -> String {
    let mut parts = Vec::new();
    for field in evidence_fields.iter().take(3) {
        let counts = weighted_value_counts(samples, indices, field);
        let Some((value, share)) = dominant_value_with_share(&counts) else {
            continue;
        };
        if share >= 0.45 {
            parts.push(format!("{field}={value}"));
        }
    }
    if !parts.is_empty() {
        return parts.join("+");
    }
    format!("{fallback}-segment")
}

fn dominant_value_with_share(counts: &BTreeMap<String, u64>) -> Option<(String, f64)> {
    let total = counts.values().sum::<u64>().max(1) as f64;
    counts
        .iter()
        .filter(|(value, _)| value.as_str() != "unknown")
        .max_by(|left, right| left.1.cmp(right.1).then_with(|| right.0.cmp(left.0)))
        .map(|(value, weight)| (value.clone(), *weight as f64 / total))
}

fn dominant_value(counts: &BTreeMap<String, u64>) -> Option<String> {
    counts
        .iter()
        .filter(|(value, _)| value.as_str() != "unknown")
        .max_by(|left, right| left.1.cmp(right.1).then_with(|| right.0.cmp(left.0)))
        .map(|(value, _)| value.clone())
}

fn operation_field_value(sample: &Operation, field: &str) -> String {
    sample
        .values(field)
        .first()
        .cloned()
        .unwrap_or_else(|| "unknown".to_string())
}

fn weighted_value_counts(
    samples: &[Operation],
    indices: &[usize],
    field: &str,
) -> BTreeMap<String, u64> {
    let mut counts = BTreeMap::new();
    for index in indices {
        *counts
            .entry(operation_field_value(&samples[*index], field))
            .or_default() += samples[*index].value.max(1);
    }
    counts
}

fn index_weight(samples: &[Operation], indices: &[usize]) -> u64 {
    indices
        .iter()
        .map(|index| samples[*index].value.max(1))
        .sum()
}

fn entropy(counts: &BTreeMap<String, u64>) -> f64 {
    let total = counts.values().sum::<u64>();
    if total == 0 {
        return 0.0;
    }
    counts
        .values()
        .filter(|count| **count > 0)
        .map(|count| {
            let probability = *count as f64 / total as f64;
            -probability * probability.log2()
        })
        .sum()
}

fn query_bonus<'a>(
    field: &str,
    values: impl Iterator<Item = &'a String>,
    query_terms: &[String],
) -> f64 {
    if query_terms.is_empty() {
        return 0.0;
    }
    let haystack = std::iter::once(field.to_ascii_lowercase())
        .chain(values.map(|value| value.to_ascii_lowercase()))
        .collect::<Vec<_>>()
        .join(" ");
    query_terms
        .iter()
        .filter(|term| haystack.contains(term.as_str()))
        .count() as f64
        / query_terms.len() as f64
}

fn round6(value: f64) -> f64 {
    (value * 1_000_000.0).round() / 1_000_000.0
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
                    "task_stack_induction": projection.task_stack_induction,
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
            build_profile_with_options(&[session], "agentsight", ProfileView::Time, &options);
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
            build_profile_with_options(&[session], "agentsight", ProfileView::Files, &options);
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
            build_profile_with_options(&[session], "agentsight", ProfileView::Operations, &options);
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
            build_profile_with_options(&[session], "agentsight", ProfileView::Files, &options);
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
    fn operation_jsonl_input_uses_same_recursive_stack_model() {
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
    fn task_stack_induction_derives_task_frames_without_oracle_fields() {
        let mut records = Vec::new();
        for _ in 0..6 {
            records.push(json!({"value": 1, "fields": {
                "dataset": "agent-reward-bench",
                "analysis_task": "agentreward_looping",
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

        let stack = parse_stack_spec("task").unwrap();
        let induction = TaskStackInductionConfig::new()
            .with_query_terms(vec!["loop".to_string(), "repeat".to_string()])
            .with_min_score(0.0)
            .with_min_second_child(2)
            .with_min_node_weight(2);
        let options = OperationStackConfig::for_view(ProfileView::Operations)
            .with_stack(stack)
            .with_task_stack_induction(induction);
        let profile =
            build_profile_from_operation_records(&records, ProfileView::Operations, &options)
                .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(!stacks.is_empty());
        assert!(
            stacks
                .keys()
                .all(|stack| stack.split(';').all(|frame| frame.starts_with("task:")))
        );
        assert!(stacks.keys().all(|stack| {
            !stack.contains("looping")
                && !stack.contains("problem_value")
                && !stack.contains("status:")
                && !stack.contains("step_correct")
                && !stack.contains("safety:")
                && !stack.contains("human_group")
                && !stack.contains("group_pattern")
        }));
        let depths = stacks
            .keys()
            .map(|stack| stack.split(';').count())
            .collect::<BTreeSet<_>>();
        assert!(
            depths.len() > 1,
            "expected variable-depth task stacks: {stacks:?}"
        );

        let report = profile
            .task_stack_induction
            .as_ref()
            .expect("induction report");
        assert_eq!(report.policy, TASK_STACK_POLICY);
        assert!(
            report
                .selected_source_fields
                .iter()
                .any(|field| matches!(field.as_str(), "repeat_state" | "repeat_signal" | "action"))
        );
        assert!(report.split_decisions.iter().all(|decision| {
            decision.selected_score.semantic_shift > 0.0
                && !decision.selected_score.changed_fields.is_empty()
        }));
        assert!(
            report
                .selected_source_fields
                .iter()
                .all(|field| !is_task_stack_oracle_field(field))
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
