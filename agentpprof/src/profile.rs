use anyhow::{Result, bail};
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
}

impl Profile {
    fn new(view: &'static str, sample_type: &'static str, unit: &'static str) -> Self {
        Self {
            view,
            sample_type,
            unit,
            ops: Vec::new(),
        }
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
    rules: Vec<OperationStackRule>,
}

impl OperationStackConfig {
    pub fn for_view(view: ProfileView) -> Self {
        Self {
            stack: OperationStackSpec::default_for_view(view),
            field_rules: Vec::new(),
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

#[derive(Deserialize)]
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
    let mut profile = Profile::new(name, sample_type, unit);
    for session in sessions {
        for sample in session_samples(session, project_name, view) {
            let sample = apply_operation_field_rules(&sample, &options.field_rules);
            let frames = stack_frames(&sample, options);
            profile.sample(frames, sample.value);
        }
    }
    profile
}

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
    let mut profile = Profile::new(name, sample_type, unit);
    for sample in operations {
        let sample = apply_operation_field_rules(sample, &options.field_rules);
        let frames = stack_frames(&sample, options);
        profile.sample(frames, sample.value);
    }
    profile
}

fn read_operation_jsonl(path: &Path) -> Result<Vec<Operation>> {
    let file = fs::File::open(path)?;
    let mut operations = Vec::new();
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
        operations.push(operation_from_record(record).map_err(|error| {
            anyhow::anyhow!(
                "invalid operation fields at {}:{}: {error}",
                path.display(),
                line_number + 1
            )
        })?);
    }
    Ok(operations)
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
    let stack = frames
        .into_iter()
        .map(normalize_folded_frame)
        .filter(|frame| !frame.is_empty())
        .collect::<Vec<_>>()
        .join(";");
    if !stack.is_empty() {
        *counter.entry(stack).or_default() += weight.max(1);
    }
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
) -> Result<()> {
    ensure_parent_dir(output)?;
    let stacks = profile_to_stacks(projection);
    match format {
        OutputFormat::Pprof => write_pprof_projection(projection, &stacks, output),
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

fn write_pprof_projection(projection: &Profile, stacks: &Counter, output: &Path) -> Result<()> {
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
        time_nanos: Utc::now().timestamp_nanos_opt().unwrap_or(0),
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
        write_pprof_projection(&projection, &stacks, &path).unwrap();

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
