use anyhow::{Result, bail};
use chrono::Utc;
use flate2::{Compression, write::GzEncoder};
use prost::Message;
use regex::Regex;
use serde::Serialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::io::Write;
use std::path::Path;

use crate::session::{
    SessionRecord, collapse_project_path, contains_private_marker, path_component_strings,
    semantic_task_label, short_hash, truncate_clean,
};

pub type Counter = BTreeMap<String, u64>;
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
    pprof_samples: Vec<PprofProfileSample>,
}

impl Profile {
    pub(crate) fn new(view: &'static str, sample_type: &'static str, unit: &'static str) -> Self {
        Self {
            view,
            sample_type,
            unit,
            ops: Vec::new(),
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

#[derive(Clone)]
pub struct OperationFilterRule {
    field: String,
    pattern: String,
    regex: Regex,
    negated: bool,
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
pub struct OperationStackConfig {
    stack: OperationStackSpec,
    field_rules: Vec<OperationStackRule>,
    filters: Vec<OperationFilterRule>,
    rules: Vec<OperationStackRule>,
}

impl OperationStackConfig {
    pub fn for_view(view: ProfileView) -> Self {
        Self {
            stack: OperationStackSpec::default_for_view(view),
            field_rules: Vec::new(),
            filters: Vec::new(),
            rules: Vec::new(),
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
}

#[derive(Clone)]
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
    "project",
    "agent",
    "session",
    "source_kind",
    "evidence_id",
    "operation_start_id",
    "status",
    "response_phase",
    "outcome",
    "source_session",
    "call_id",
    "prompt_hash",
    "response_hash",
    "timestamp_ms",
    "skill",
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
    samples.retain(|sample| operation_matches_filters(sample, &options.filters));
    samples.retain(|sample| sample.value > 0);
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let labels = pprof_evidence_labels(&sample);
        profile.sample(frames, sample.value, labels);
    }
    Ok(profile)
}

#[cfg(test)]
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
    samples.retain(|sample| operation_matches_filters(sample, &options.filters));
    samples.retain(|sample| sample.value > 0);
    for sample in samples {
        let frames = stack_frames(&sample, options);
        let labels = pprof_evidence_labels(&sample);
        profile.sample(frames, sample.value, labels);
    }
    Ok(profile)
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

#[cfg(test)]
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
    // Declared --task-choice writes session.task_tag as a closed-set task label.
    // Prefer it over free-form source task_path so the taxonomy is observable.
    if !session.task_tag.is_empty() {
        return vec![session.task_tag.clone()];
    }
    if !request.task_path.is_empty() {
        return request.task_path.clone();
    }
    vec![semantic_task_label(&request.preview)]
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

pub fn summarize_counter(counter: &Counter, limit: usize) -> CounterSummary {
    let total_weight: u64 = counter.values().sum();
    let unique_stacks = counter.len();
    let max_stack_reuse = counter.values().copied().max().unwrap_or(0);
    let compression_ratio = if unique_stacks == 0 {
        0.0
    } else {
        total_weight as f64 / unique_stacks as f64
    };
    CounterSummary {
        total_weight,
        unique_stacks,
        compression_ratio,
        max_stack_reuse,
        top: top_stacks(counter, limit),
    }
}

fn top_stacks(counter: &Counter, limit: usize) -> Vec<WeightedStack> {
    let mut items: Vec<_> = counter
        .iter()
        .map(|(stack, weight)| WeightedStack {
            stack: stack.clone(),
            weight: *weight,
        })
        .collect();
    items.sort_by(|a, b| b.weight.cmp(&a.weight).then_with(|| a.stack.cmp(&b.stack)));
    items.truncate(limit);
    items
}

pub fn write_projection(
    projection: &Profile,
    format: OutputFormat,
    output: &Path,
    include_previews: bool,
    sessions: &[SessionRecord],
    svg_width: u32,
) -> Result<()> {
    ensure_parent_dir(output)?;
    let stacks = profile_to_stacks(projection);
    match format {
        OutputFormat::Pprof => write_pprof_projection(projection, output),
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
                "generated_at": now_iso(),
                "profile": {
                    "view": projection.view,
                    "sample_type": projection.sample_type,
                    "unit": projection.unit,
                    "summary": summarize_counter(&stacks, 20),
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

pub fn write_pprof_projection(projection: &Profile, output: &Path) -> Result<()> {
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
    )
}

fn write_pprof_samples<'a, I>(projection: &Profile, stacks: I, output: &Path) -> Result<()>
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
        time_nanos: Utc::now().timestamp_nanos_opt().unwrap_or(0),
        duration_nanos: 0,
        default_sample_type,
    };
    let bytes = profile.encode_to_vec();
    if output
        .extension()
        .and_then(|ext| ext.to_str())
        .is_some_and(|ext| ext == "gz")
        || output
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.ends_with(".pb.gz"))
    {
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
    Utc::now().to_rfc3339()
}

pub fn infer_output_format(requested: OutputFormat, output: &Path) -> OutputFormat {
    let name = output.file_name().and_then(|v| v.to_str()).unwrap_or("");
    if name.ends_with(".pb.gz") || name.ends_with(".pb") {
        OutputFormat::Pprof
    } else if name.ends_with(".folded") {
        OutputFormat::Folded
    } else if name.ends_with(".svg") {
        OutputFormat::Svg
    } else if name.ends_with(".json") {
        OutputFormat::Json
    } else {
        requested
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
            text: preview.to_string(),
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
            paths: Vec::new(),
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
            paths: Vec::new(),
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
            text: "answer".to_string(),
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

    fn operation_with(value: u64, fields: &[(&str, &str)]) -> Operation {
        let mut operation = Operation::new(value);
        for (key, value) in fields {
            operation.insert(key, (*value).to_string());
        }
        operation
    }

    #[test]
    fn operation_stack_rules_derive_task_and_phase_frames() {
        let operations = vec![
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "human-demo"),
                    ("dataset", "weblinx"),
                    ("demo", "d1"),
                    ("action", "click"),
                    ("op", "action"),
                    ("target", "login"),
                    ("status", "gold"),
                ],
            ),
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "human-demo"),
                    ("dataset", "weblinx"),
                    ("demo", "d1"),
                    ("action", "type"),
                    ("op", "action"),
                    ("target", "email"),
                    ("status", "gold"),
                ],
            ),
        ];
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
            build_profile_from_operations(&operations, ProfileView::Files, &options).unwrap();
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
        let operations = vec![
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "gold"),
                    ("dataset", "demo"),
                    ("op", "action"),
                    ("action", "click"),
                    ("target", "login"),
                    ("status", "gold"),
                ],
            ),
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "gold"),
                    ("dataset", "demo"),
                    ("op", "action"),
                    ("action", "type"),
                    ("target", "email"),
                    ("status", "gold"),
                ],
            ),
        ];
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
            build_profile_from_operations(&operations, ProfileView::Operations, &options).unwrap();
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
        let operations = vec![
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "gold"),
                    ("dataset", "demo"),
                    ("op", "action"),
                    ("action", "click"),
                    ("target", "login"),
                    ("status", "gold"),
                ],
            ),
            operation_with(
                1,
                &[
                    ("project", "external"),
                    ("agent", "gold"),
                    ("dataset", "demo"),
                    ("op", "action"),
                    ("action", "type"),
                    ("target", "email"),
                    ("status", "gold"),
                ],
            ),
        ];
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
            build_profile_from_operations(&operations, ProfileView::Operations, &options).unwrap();
        let stacks = profile_to_stacks(&profile);

        assert_eq!(stacks.len(), 1);
        assert_eq!(
            stacks.get("project:external;agent:gold;task:authenticate;phase:input;op:action;action:type;status:gold"),
            Some(&1)
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
        write_pprof_projection(&projection, &path).unwrap();

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
        write_pprof_projection(&profile, &path).unwrap();

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
            labels.contains(&("project", "agentsight"))
                && labels.contains(&("agent", "codex"))
                && labels.contains(&("session", "evidence"))
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
            write_pprof_projection(&profile, &path).unwrap();
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
    fn declared_task_tag_overrides_freeform_task_path() {
        let mut session = test_session(
            "codex",
            "rawsession",
            vec![prompt(0, 1000, "h1", "fix the flaky parser test", "debug")],
            vec![shell_tool(2000, 0, "ok", vec!["agent-session"])],
            vec![],
        );
        session.task_tag = "debug".to_string();
        session.user_requests[0].task_path = vec!["fix the flaky parser test".to_string()];
        let profile = build_profile_with_options(
            &[session],
            "agentsight",
            ProfileView::Operations,
            &OperationStackConfig::for_view(ProfileView::Operations),
        )
        .unwrap();
        let stacks = profile_to_stacks(&profile);
        assert!(
            stacks.keys().any(|stack| stack.contains("task:debug")),
            "expected declared task_tag in stacks, got {stacks:?}"
        );
        assert!(
            stacks
                .keys()
                .all(|stack| !stack.contains("task:fix_the_flaky")),
            "free-form task_path should not win over declared task_tag, got {stacks:?}"
        );
    }
}
