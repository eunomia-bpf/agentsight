// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Source-store construction and deterministic workspace relations for the
//! Agent Nebula automatic-supervision experiment. This is deliberately a thin
//! adapter over agent-session, not a second production event model.

use agent_session::{AGENT_CODEX, ToolEvent, event_timestamp_ms, parse_session_content};
use base64::Engine;
use clap::Parser;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::ffi::OsString;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::sync::OnceLock;
use std::time::UNIX_EPOCH;

pub(crate) type AnyError = Box<dyn std::error::Error + Send + Sync>;

const STORE_SCHEMA: &str = "agent-nebula-source-store-v1";
const BINARY_PAGE_BYTES: usize = 48 * 1024;
const LEAK_TERMS: &[&str] = &[
    "perturbed",
    "repaired",
    "full-raw",
    "full_raw",
    "full-trajectory",
    "full_trajectory",
    "workspace trajectory retrieval",
    "raw retrieval condition",
    "treatment assignment",
    "pair identity",
];

#[derive(Debug, Parser)]
struct StoreArgs {
    /// Neutral captured checkpoint directory for one admitted workload.
    #[arg(long)]
    source: PathBuf,
    /// New source-store directory.
    #[arg(long)]
    output: PathBuf,
    /// Re-read every output and enforce hashes/references before success.
    #[arg(long)]
    verify: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct RawRecord {
    pub id: String,
    pub scope_id: String,
    pub source_type: String,
    pub source_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ts_ns: Option<i64>,
    pub payload: String,
    pub encoding: String,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
pub(crate) struct Effect {
    pub operation: String,
    pub path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub previous_path: Option<String>,
    pub evidence_ids: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Action {
    pub id: String,
    pub ts_ns: i64,
    pub end_ns: i64,
    pub scope_id: String,
    pub kind: String,
    pub status: String,
    pub closure: String,
    pub raw_ids: Vec<String>,
    pub effects: Vec<Effect>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
pub(crate) struct ManifestEntry {
    pub path: String,
    #[serde(rename = "type")]
    pub kind: String,
    #[serde(default)]
    pub mode: Option<u32>,
    #[serde(default)]
    pub mtime_ns: Option<i64>,
    #[serde(default)]
    pub sha256: Option<String>,
    #[serde(default)]
    pub size: Option<u64>,
    #[serde(default)]
    pub target: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct BoundaryEntry {
    #[serde(flatten)]
    pub entry: ManifestEntry,
    pub evidence_id: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Scope {
    pub id: String,
    pub goal_id: String,
    pub session_id: String,
    pub kind: String,
    pub start_ns: i64,
    pub end_ns: i64,
    pub goal: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct SourceFile {
    pub path: String,
    pub bytes: u64,
    pub sha256: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct StoreIndex {
    pub schema: String,
    pub episode_id: String,
    pub domain: String,
    pub source_store_sha256: String,
    pub raw_ids_sha256: String,
    pub raw_jsonl_sha256: String,
    pub actions_jsonl_sha256: String,
    pub records: usize,
    pub actions: usize,
    pub scopes: Vec<Scope>,
    pub boundaries: BTreeMap<String, Vec<BoundaryEntry>>,
    pub source_files: Vec<SourceFile>,
    pub unbound_workspace_effect_ids: Vec<String>,
}

#[derive(Debug)]
pub(crate) struct StoreData {
    pub index: StoreIndex,
    pub records: Vec<RawRecord>,
    pub actions: Vec<Action>,
    artifact_projection: OnceLock<ArtifactProjection>,
}

#[derive(Debug)]
struct ParsedSession {
    actions: Vec<Action>,
    raw: Vec<RawRecord>,
    source_files: Vec<SourceFile>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct HarnessCheckpoint {
    schema: String,
    episode_id: String,
    domain: String,
    next_prompt_file: String,
    rounds: Vec<HarnessRound>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct HarnessRound {
    scope_id: String,
    session_id: String,
    prompt_file: String,
    session_file: String,
    #[serde(default)]
    adapter_logs: Vec<String>,
    snapshot_manifest: String,
    snapshot_tree: String,
}

#[derive(Clone, Debug)]
struct TraceCall {
    pid: u32,
    ts_ns: i64,
    syscall: String,
    arguments: String,
    result: String,
    raw_ids: Vec<String>,
}

#[derive(Clone, Debug)]
struct TraceExec {
    pid: u32,
    ts_ns: i64,
    argv: Vec<String>,
    cwd: PathBuf,
}

#[derive(Debug, Default)]
struct TraceModel {
    effects: Vec<(u32, i64, Effect)>,
    execs: Vec<TraceExec>,
    children: HashMap<u32, Vec<(u32, i64)>>,
    exits: HashMap<u32, i64>,
}

pub fn run_research_store_from_args(
    args: impl IntoIterator<Item = OsString>,
) -> Result<(), AnyError> {
    let args = StoreArgs::parse_from(std::iter::once(OsString::from("research-store")).chain(args));
    if !args.verify {
        return Err("research-store requires --verify for the frozen preflight path".into());
    }
    build_store(&args.source, &args.output)?;
    let store = load_store(&args.output)?;
    verify_artifact_projection(&store)?;
    eprintln!(
        "[research-store] {}: {} records, {} actions, {} unresolved workspace effects -> {}",
        store.index.episode_id,
        store.records.len(),
        store.actions.len(),
        store.index.unbound_workspace_effect_ids.len(),
        args.output.display()
    );
    Ok(())
}

fn build_store(source: &Path, output: &Path) -> Result<(), AnyError> {
    let source = source.canonicalize()?;
    if source.join("checkpoint.json").is_file() {
        return build_harness_store(&source, output);
    }
    let episode_id = source
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or("capture directory has no UTF-8 basename")?
        .to_string();
    reject_leak(&episode_id, "episode ID")?;
    if output.exists() {
        return Err(format!("output already exists: {}", output.display()).into());
    }
    let summary: Value = serde_json::from_slice(&fs::read(source.join("summary.json"))?)?;
    let sessions = session_ids(&summary)?;
    let workload = source.join("native/workload");
    let prior_goal = fs::read_to_string(workload.join("prior-goal.txt"))?;
    let target_goal = fs::read_to_string(workload.join("target-goal.txt"))?;
    let domain = fs::read_to_string(workload.join("domain.txt"))?
        .trim()
        .to_string();

    let mut prior = parse_session(&source, 1, &sessions[0], "g1")?;
    let mut target = parse_session(&source, 2, &sessions[1], "g2")?;
    let mut unbound = Vec::new();
    attach_process_owned_effects(&source, 1, &mut prior, &mut unbound)?;
    attach_process_owned_effects(&source, 2, &mut target, &mut unbound)?;

    let mut records = Vec::new();
    let mut actions = Vec::new();
    let mut source_files = Vec::new();
    records.append(&mut prior.raw);
    records.append(&mut target.raw);
    actions.append(&mut prior.actions);
    actions.append(&mut target.actions);
    source_files.append(&mut prior.source_files);
    source_files.append(&mut target.source_files);

    let boundaries = read_boundaries(&source, &mut records, &mut source_files)?;
    let mut environment = parse_environment_action(&source)?;
    records.append(&mut environment.raw);
    actions.append(&mut environment.actions);
    source_files.append(&mut environment.source_files);

    add_remaining_sources(&source, &mut records, &mut source_files)?;
    reject_visible_leaks(&records, &prior_goal, &target_goal)?;

    records.sort_by(|left, right| {
        (left.ts_ns.unwrap_or(i64::MIN), &left.source_path, &left.id).cmp(&(
            right.ts_ns.unwrap_or(i64::MIN),
            &right.source_path,
            &right.id,
        ))
    });
    let raw_remap = records
        .iter_mut()
        .enumerate()
        .map(|(offset, record)| {
            let old = std::mem::replace(&mut record.id, format!("r{:09}", offset + 1));
            (old, record.id.clone())
        })
        .collect::<HashMap<_, _>>();

    for action in &mut actions {
        remap_ids(&mut action.raw_ids, &raw_remap)?;
        for effect in &mut action.effects {
            remap_ids(&mut effect.evidence_ids, &raw_remap)?;
        }
    }
    remap_ids(&mut unbound, &raw_remap)?;
    let mut boundaries = boundaries;
    for rows in boundaries.values_mut() {
        for row in rows {
            row.evidence_id = raw_remap
                .get(&row.evidence_id)
                .ok_or_else(|| format!("missing manifest evidence {}", row.evidence_id))?
                .clone();
        }
    }

    actions.sort_by(|left, right| (left.ts_ns, &left.id).cmp(&(right.ts_ns, &right.id)));
    for (offset, action) in actions.iter_mut().enumerate() {
        action.id = format!("a{:07}", offset + 1);
    }
    reclassify_creates(&mut actions, boundaries.get("h0").into_iter().flatten());
    verify_changed_paths(&actions, &boundaries)?;

    let scopes = make_scopes(&actions, prior_goal.trim(), target_goal.trim());
    source_files.sort_by(|left, right| left.path.cmp(&right.path));
    source_files.dedup_by(|left, right| left.path == right.path && left.sha256 == right.sha256);
    fs::create_dir_all(output)?;
    let raw_path = output.join("raw.jsonl");
    let actions_path = output.join("actions.jsonl");
    write_jsonl(&raw_path, &records)?;
    write_jsonl(&actions_path, &actions)?;
    let boundaries_bytes = serde_json::to_vec_pretty(&boundaries)?;
    fs::write(output.join("boundaries.json"), &boundaries_bytes)?;

    let raw_bytes = fs::read(&raw_path)?;
    let action_bytes = fs::read(&actions_path)?;
    let raw_ids_sha256 = sha256_bytes(
        records
            .iter()
            .flat_map(|record| record.id.bytes().chain(std::iter::once(b'\n')))
            .collect::<Vec<_>>()
            .as_slice(),
    );
    let raw_jsonl_sha256 = sha256_bytes(&raw_bytes);
    let actions_jsonl_sha256 = sha256_bytes(&action_bytes);
    let source_store_sha256 = sha256_parts(&[
        &raw_bytes,
        &action_bytes,
        &boundaries_bytes,
        &serde_json::to_vec(&scopes)?,
        &serde_json::to_vec(&source_files)?,
    ]);
    let index = StoreIndex {
        schema: STORE_SCHEMA.into(),
        episode_id,
        domain,
        source_store_sha256,
        raw_ids_sha256,
        raw_jsonl_sha256,
        actions_jsonl_sha256,
        records: records.len(),
        actions: actions.len(),
        scopes,
        boundaries,
        source_files,
        unbound_workspace_effect_ids: unbound,
    };
    fs::write(
        output.join("store.json"),
        serde_json::to_vec_pretty(&index)?,
    )?;
    Ok(())
}

fn build_harness_store(source: &Path, output: &Path) -> Result<(), AnyError> {
    let checkpoint_path = source.join("checkpoint.json");
    let checkpoint: HarnessCheckpoint = serde_json::from_slice(&fs::read(&checkpoint_path)?)?;
    if checkpoint.schema != "agent-nebula-harness-checkpoint-v1" {
        return Err(format!(
            "unsupported Harness checkpoint schema: {}",
            checkpoint.schema
        )
        .into());
    }
    if checkpoint.rounds.len() < 2 {
        return Err("Harness checkpoint requires at least two completed rounds".into());
    }
    reject_leak(&checkpoint.episode_id, "episode ID")?;
    if output.exists() {
        return Err(format!("output already exists: {}", output.display()).into());
    }

    let mut records = Vec::new();
    let mut actions = Vec::new();
    let mut source_files = vec![source_file(source, &checkpoint_path)?];
    let mut boundaries = BTreeMap::new();
    let mut scopes = Vec::new();
    let mut seen_scopes = HashSet::new();

    for (index, round) in checkpoint.rounds.iter().enumerate() {
        if !seen_scopes.insert(round.scope_id.clone()) {
            return Err(format!("duplicate Harness scope {}", round.scope_id).into());
        }
        let session_path = retained_relative_path(source, &round.session_file)?;
        let prompt_path = retained_relative_path(source, &round.prompt_file)?;
        let snapshot_manifest = retained_relative_path(source, &round.snapshot_manifest)?;
        let snapshot_tree = retained_relative_path(source, &round.snapshot_tree)?;
        if !snapshot_tree.is_dir() {
            return Err(format!(
                "snapshot tree is not a directory: {}",
                snapshot_tree.display()
            )
            .into());
        }

        let mut parsed = parse_harness_session(
            source,
            &session_path,
            index + 1,
            &round.session_id,
            &round.scope_id,
        )?;
        let prompt = fs::read_to_string(&prompt_path)?;
        records.append(&mut parsed.raw);
        actions.append(&mut parsed.actions);
        source_files.append(&mut parsed.source_files);
        add_whole_file_record(
            source,
            &prompt_path,
            &round.scope_id,
            "official_prompt",
            &mut records,
            &mut source_files,
        )?;
        for log in &round.adapter_logs {
            let log_path = retained_relative_path(source, log)?;
            add_line_file_records(
                source,
                &log_path,
                &round.scope_id,
                "adapter_log",
                &mut records,
                &mut source_files,
            )?;
        }
        let rows = add_snapshot_records(
            source,
            &snapshot_manifest,
            &snapshot_tree,
            &round.scope_id,
            &mut records,
            &mut source_files,
        )?;
        boundaries.insert(round.scope_id.clone(), rows);

        let start_ns = parsed
            .actions
            .iter()
            .map(|action| action.ts_ns)
            .min()
            .unwrap_or(index as i64);
        let end_ns = parsed
            .actions
            .iter()
            .map(|action| action.end_ns)
            .max()
            .unwrap_or(start_ns);
        scopes.push(Scope {
            id: round.scope_id.clone(),
            goal_id: round.scope_id.clone(),
            session_id: round.session_id.clone(),
            kind: "round".into(),
            start_ns,
            end_ns,
            goal: prompt,
        });
    }

    let next_prompt = retained_relative_path(source, &checkpoint.next_prompt_file)?;
    add_whole_file_record(
        source,
        &next_prompt,
        "current",
        "next_prompt",
        &mut records,
        &mut source_files,
    )?;
    add_whole_file_record(
        source,
        &checkpoint_path,
        "metadata",
        "checkpoint_metadata",
        &mut records,
        &mut source_files,
    )?;
    reject_visible_leaks(&records, "", "")?;

    records.sort_by(|left, right| {
        (left.ts_ns.unwrap_or(i64::MIN), &left.source_path, &left.id).cmp(&(
            right.ts_ns.unwrap_or(i64::MIN),
            &right.source_path,
            &right.id,
        ))
    });
    let raw_remap = records
        .iter_mut()
        .enumerate()
        .map(|(offset, record)| {
            let old = std::mem::replace(&mut record.id, format!("r{:09}", offset + 1));
            (old, record.id.clone())
        })
        .collect::<HashMap<_, _>>();
    for action in &mut actions {
        remap_ids(&mut action.raw_ids, &raw_remap)?;
        for effect in &mut action.effects {
            remap_ids(&mut effect.evidence_ids, &raw_remap)?;
        }
    }
    for rows in boundaries.values_mut() {
        for row in rows {
            row.evidence_id = raw_remap
                .get(&row.evidence_id)
                .ok_or_else(|| format!("missing snapshot Raw-ID remap for {}", row.entry.path))?
                .clone();
        }
    }
    actions.sort_by(|left, right| (left.ts_ns, &left.id).cmp(&(right.ts_ns, &right.id)));
    for (offset, action) in actions.iter_mut().enumerate() {
        action.id = format!("a{:07}", offset + 1);
    }

    source_files.sort_by(|left, right| left.path.cmp(&right.path));
    source_files.dedup_by(|left, right| left.path == right.path && left.sha256 == right.sha256);
    fs::create_dir_all(output)?;
    let raw_path = output.join("raw.jsonl");
    let actions_path = output.join("actions.jsonl");
    write_jsonl(&raw_path, &records)?;
    write_jsonl(&actions_path, &actions)?;
    let boundaries_bytes = serde_json::to_vec_pretty(&boundaries)?;
    fs::write(output.join("boundaries.json"), &boundaries_bytes)?;
    let raw_bytes = fs::read(&raw_path)?;
    let action_bytes = fs::read(&actions_path)?;
    let raw_ids_sha256 = sha256_bytes(
        records
            .iter()
            .flat_map(|record| record.id.bytes().chain(std::iter::once(b'\n')))
            .collect::<Vec<_>>()
            .as_slice(),
    );
    let raw_jsonl_sha256 = sha256_bytes(&raw_bytes);
    let actions_jsonl_sha256 = sha256_bytes(&action_bytes);
    let source_store_sha256 = sha256_parts(&[
        &raw_bytes,
        &action_bytes,
        &boundaries_bytes,
        &serde_json::to_vec(&scopes)?,
        &serde_json::to_vec(&source_files)?,
    ]);
    let index = StoreIndex {
        schema: STORE_SCHEMA.into(),
        episode_id: checkpoint.episode_id,
        domain: checkpoint.domain,
        source_store_sha256,
        raw_ids_sha256,
        raw_jsonl_sha256,
        actions_jsonl_sha256,
        records: records.len(),
        actions: actions.len(),
        scopes,
        boundaries,
        source_files,
        unbound_workspace_effect_ids: Vec::new(),
    };
    fs::write(
        output.join("store.json"),
        serde_json::to_vec_pretty(&index)?,
    )?;
    Ok(())
}

fn retained_relative_path(source: &Path, relative: &str) -> Result<PathBuf, AnyError> {
    let relative = Path::new(relative);
    if relative.is_absolute()
        || relative
            .components()
            .any(|part| !matches!(part, Component::Normal(_)))
    {
        return Err(
            format!("checkpoint path must be a normalized relative path: {relative:?}").into(),
        );
    }
    let path = source.join(relative);
    let canonical = path.canonicalize()?;
    if !canonical.starts_with(source) {
        return Err(format!("checkpoint path escapes source: {relative:?}").into());
    }
    Ok(canonical)
}

fn parse_harness_session(
    source: &Path,
    path: &Path,
    index: usize,
    session_id: &str,
    scope_id: &str,
) -> Result<ParsedSession, AnyError> {
    let text = fs::read_to_string(path)?;
    let relative = relative_source_path(source, path)?;
    let mut raw = Vec::new();
    let mut raw_ids_by_call = HashMap::<String, Vec<String>>::new();
    for (offset, line) in text.split_inclusive('\n').enumerate() {
        let payload = line.strip_suffix('\n').unwrap_or(line);
        let value: Value = serde_json::from_str(payload)?;
        let ts_ns = event_timestamp_ms(&value).map(|value| value.saturating_mul(1_000_000));
        let raw_id = format!("native:s{index}:l{:09}", offset + 1);
        if let Some(call_id) = value.pointer("/payload/call_id").and_then(Value::as_str) {
            raw_ids_by_call
                .entry(call_id.to_string())
                .or_default()
                .push(raw_id.clone());
        }
        raw.push(RawRecord {
            id: raw_id,
            scope_id: scope_id.into(),
            source_type: "agent_native".into(),
            source_path: relative.clone(),
            ts_ns,
            payload: payload.into(),
            encoding: "utf8".into(),
        });
    }
    let parsed = parse_session_content(AGENT_CODEX, path, UNIX_EPOCH, &text)
        .ok_or_else(|| format!("agent-session could not parse Harness session {session_id}"))?;
    let actions = parsed
        .events
        .tools
        .iter()
        .enumerate()
        .map(|(offset, tool)| action_from_tool(index, scope_id, offset, tool, &raw_ids_by_call))
        .collect();
    Ok(ParsedSession {
        actions,
        raw,
        source_files: vec![source_file(source, path)?],
    })
}

fn add_whole_file_record(
    source: &Path,
    path: &Path,
    scope_id: &str,
    source_type: &str,
    records: &mut Vec<RawRecord>,
    source_files: &mut Vec<SourceFile>,
) -> Result<(), AnyError> {
    let bytes = fs::read(path)?;
    let (payload, encoding) = match String::from_utf8(bytes.clone()) {
        Ok(text) => (text, "utf8"),
        Err(_) => (
            base64::engine::general_purpose::STANDARD.encode(bytes),
            "base64",
        ),
    };
    records.push(RawRecord {
        id: format!("file:{:09}", records.len() + 1),
        scope_id: scope_id.into(),
        source_type: source_type.into(),
        source_path: relative_source_path(source, path)?,
        ts_ns: None,
        payload,
        encoding: encoding.into(),
    });
    source_files.push(source_file(source, path)?);
    Ok(())
}

fn add_line_file_records(
    source: &Path,
    path: &Path,
    scope_id: &str,
    source_type: &str,
    records: &mut Vec<RawRecord>,
    source_files: &mut Vec<SourceFile>,
) -> Result<(), AnyError> {
    let text = fs::read_to_string(path)?;
    let relative = relative_source_path(source, path)?;
    for (offset, line) in text.lines().enumerate() {
        records.push(RawRecord {
            id: format!("log:{:09}:{offset:09}", records.len() + 1),
            scope_id: scope_id.into(),
            source_type: source_type.into(),
            source_path: relative.clone(),
            ts_ns: None,
            payload: line.into(),
            encoding: "utf8".into(),
        });
    }
    source_files.push(source_file(source, path)?);
    Ok(())
}

fn add_snapshot_records(
    source: &Path,
    manifest_path: &Path,
    tree: &Path,
    scope_id: &str,
    records: &mut Vec<RawRecord>,
    source_files: &mut Vec<SourceFile>,
) -> Result<Vec<BoundaryEntry>, AnyError> {
    let entries: Vec<ManifestEntry> = serde_json::from_slice(&fs::read(manifest_path)?)?;
    let mut previous = None;
    let mut rows = Vec::with_capacity(entries.len());
    for entry in entries {
        if entry.path.is_empty() || previous.as_ref().is_some_and(|value| value >= &entry.path) {
            return Err("snapshot manifest paths must be non-empty, unique, and sorted".into());
        }
        previous = Some(entry.path.clone());
        verify_snapshot_entry(tree, &entry)?;
        let evidence_id = format!("manifest:{scope_id}:{:09}", rows.len() + 1);
        records.push(RawRecord {
            id: evidence_id.clone(),
            scope_id: scope_id.into(),
            source_type: "snapshot_manifest_entry".into(),
            source_path: relative_source_path(source, manifest_path)?,
            ts_ns: None,
            payload: serde_json::to_string(&entry)?,
            encoding: "utf8".into(),
        });
        if entry.kind == "file" {
            let file_path = tree.join(&entry.path);
            add_whole_file_record(
                source,
                &file_path,
                scope_id,
                "snapshot_file",
                records,
                source_files,
            )?;
        }
        rows.push(BoundaryEntry { entry, evidence_id });
    }
    source_files.push(source_file(source, manifest_path)?);
    Ok(rows)
}

#[cfg(unix)]
fn verify_snapshot_entry(tree: &Path, entry: &ManifestEntry) -> Result<(), AnyError> {
    use std::os::unix::fs::{MetadataExt, PermissionsExt};
    let path = tree.join(&entry.path);
    let metadata = fs::symlink_metadata(&path)?;
    let kind = if metadata.file_type().is_symlink() {
        "symlink"
    } else if metadata.is_dir() {
        "directory"
    } else if metadata.is_file() {
        "file"
    } else {
        "other"
    };
    if kind != entry.kind {
        return Err(format!("snapshot type mismatch for {}", entry.path).into());
    }
    if entry.mode != Some(metadata.permissions().mode())
        || entry.mtime_ns
            != Some(
                metadata
                    .mtime()
                    .saturating_mul(1_000_000_000)
                    .saturating_add(metadata.mtime_nsec()),
            )
    {
        return Err(format!("snapshot metadata mismatch for {}", entry.path).into());
    }
    if entry.kind == "file" {
        let bytes = fs::read(&path)?;
        if entry.size != Some(bytes.len() as u64)
            || entry.sha256.as_deref() != Some(sha256_bytes(&bytes).as_str())
        {
            return Err(format!("snapshot file hash/size mismatch for {}", entry.path).into());
        }
    } else if entry.kind == "symlink"
        && entry.target.as_deref() != Some(fs::read_link(&path)?.to_string_lossy().as_ref())
    {
        return Err(format!("snapshot symlink target mismatch for {}", entry.path).into());
    }
    Ok(())
}

#[cfg(not(unix))]
fn verify_snapshot_entry(_tree: &Path, _entry: &ManifestEntry) -> Result<(), AnyError> {
    Err("Harness checkpoint verification currently requires Unix lstat metadata".into())
}

pub(crate) fn load_store(root: &Path) -> Result<StoreData, AnyError> {
    let root = root.canonicalize()?;
    let index: StoreIndex = serde_json::from_slice(&fs::read(root.join("store.json"))?)?;
    if index.schema != STORE_SCHEMA {
        return Err(format!("unsupported source-store schema: {}", index.schema).into());
    }
    let raw_bytes = fs::read(root.join("raw.jsonl"))?;
    let action_bytes = fs::read(root.join("actions.jsonl"))?;
    let boundary_bytes = fs::read(root.join("boundaries.json"))?;
    if sha256_bytes(&raw_bytes) != index.raw_jsonl_sha256
        || sha256_bytes(&action_bytes) != index.actions_jsonl_sha256
    {
        return Err("source-store JSONL hash mismatch".into());
    }
    let records: Vec<RawRecord> = parse_jsonl_bytes(&raw_bytes)?;
    let actions: Vec<Action> = parse_jsonl_bytes(&action_bytes)?;
    if records.len() != index.records || actions.len() != index.actions {
        return Err("source-store row-count mismatch".into());
    }
    validate_store_references(&records, &actions, &index.boundaries)?;
    let raw_ids_sha256 = sha256_bytes(
        records
            .iter()
            .flat_map(|record| record.id.bytes().chain(std::iter::once(b'\n')))
            .collect::<Vec<_>>()
            .as_slice(),
    );
    let source_store_sha256 = sha256_parts(&[
        &raw_bytes,
        &action_bytes,
        &boundary_bytes,
        &serde_json::to_vec(&index.scopes)?,
        &serde_json::to_vec(&index.source_files)?,
    ]);
    if raw_ids_sha256 != index.raw_ids_sha256 || source_store_sha256 != index.source_store_sha256 {
        return Err("source-store identity hash mismatch".into());
    }
    Ok(StoreData {
        index,
        records,
        actions,
        artifact_projection: OnceLock::new(),
    })
}

fn validate_store_references(
    records: &[RawRecord],
    actions: &[Action],
    boundaries: &BTreeMap<String, Vec<BoundaryEntry>>,
) -> Result<(), AnyError> {
    let ids = records
        .iter()
        .map(|record| record.id.as_str())
        .collect::<HashSet<_>>();
    if ids.len() != records.len() {
        return Err("source store contains duplicate Raw IDs".into());
    }
    let action_ids = actions
        .iter()
        .map(|action| action.id.as_str())
        .collect::<HashSet<_>>();
    if action_ids.len() != actions.len() {
        return Err("source store contains duplicate action IDs".into());
    }
    for action in actions {
        for raw_id in action.raw_ids.iter().chain(
            action
                .effects
                .iter()
                .flat_map(|effect| &effect.evidence_ids),
        ) {
            if !ids.contains(raw_id.as_str()) {
                return Err(format!("action {} cites missing Raw ID {raw_id}", action.id).into());
            }
        }
    }
    for (boundary, rows) in boundaries {
        for row in rows {
            if !ids.contains(row.evidence_id.as_str()) {
                return Err(format!(
                    "boundary {boundary} path {} cites missing Raw ID {}",
                    row.entry.path, row.evidence_id
                )
                .into());
            }
        }
    }
    Ok(())
}

fn parse_session(
    source: &Path,
    index: usize,
    session_id: &str,
    scope_id: &str,
) -> Result<ParsedSession, AnyError> {
    let path = find_retained_session(&source.join("native/sessions"), session_id)?
        .ok_or_else(|| format!("retained native session {session_id} was not found"))?;
    let text = fs::read_to_string(&path)?;
    let relative = relative_source_path(source, &path)?;
    let mut raw = Vec::new();
    let mut raw_ids_by_call = HashMap::<String, Vec<String>>::new();
    for (offset, line) in text.split_inclusive('\n').enumerate() {
        let payload = line.strip_suffix('\n').unwrap_or(line);
        let value: Value = serde_json::from_str(payload)?;
        let ts_ns = event_timestamp_ms(&value).map(|value| value.saturating_mul(1_000_000));
        let raw_id = format!("native:s{index}:l{:09}", offset + 1);
        if let Some(call_id) = value.pointer("/payload/call_id").and_then(Value::as_str) {
            raw_ids_by_call
                .entry(call_id.to_string())
                .or_default()
                .push(raw_id.clone());
        }
        raw.push(RawRecord {
            id: raw_id,
            scope_id: scope_id.into(),
            source_type: "agent_native".into(),
            source_path: relative.clone(),
            ts_ns,
            payload: payload.into(),
            encoding: "utf8".into(),
        });
    }
    let parsed = parse_session_content(AGENT_CODEX, &path, UNIX_EPOCH, &text)
        .ok_or_else(|| format!("agent-session could not parse {}", path.display()))?;
    let actions = parsed
        .events
        .tools
        .iter()
        .enumerate()
        .map(|(offset, tool)| action_from_tool(index, scope_id, offset, tool, &raw_ids_by_call))
        .collect();
    Ok(ParsedSession {
        actions,
        raw,
        source_files: vec![source_file(source, &path)?],
    })
}

fn action_from_tool(
    session_index: usize,
    scope_id: &str,
    offset: usize,
    tool: &ToolEvent,
    raw_ids_by_call: &HashMap<String, Vec<String>>,
) -> Action {
    let raw_ids = tool
        .call_id
        .as_ref()
        .and_then(|call_id| raw_ids_by_call.get(call_id))
        .cloned()
        .unwrap_or_default();
    let direct_file_tool = tool.category != "shell" || tool.command.contains("*** Begin Patch");
    let mut effects = Vec::new();
    if direct_file_tool && tool.status == "ok" {
        for path in &tool.paths {
            if path.access == "rename_from" {
                continue;
            }
            let Some(path_value) = normalize_workspace_path(&path.path) else {
                continue;
            };
            merge_effect(
                &mut effects,
                Effect {
                    operation: path.access.clone(),
                    path: path_value,
                    previous_path: path
                        .previous_path
                        .as_deref()
                        .and_then(normalize_workspace_path),
                    evidence_ids: raw_ids.clone(),
                },
            );
        }
    }
    let start_ms = tool.ts_ms.unwrap_or_default();
    let end_ms = tool.end_ts_ms.unwrap_or(start_ms);
    Action {
        id: tool
            .call_id
            .as_ref()
            .map(|value| format!("s{session_index}:{value}"))
            .unwrap_or_else(|| format!("s{session_index}:tool-{offset:06}")),
        ts_ns: start_ms.saturating_mul(1_000_000),
        end_ns: end_ms.saturating_mul(1_000_000),
        scope_id: scope_id.into(),
        kind: tool.tool_name.clone(),
        status: tool.status.clone(),
        closure: if effects.is_empty() {
            "unknown"
        } else {
            "observed"
        }
        .into(),
        raw_ids,
        effects,
    }
}

fn attach_process_owned_effects(
    source: &Path,
    session_index: usize,
    parsed: &mut ParsedSession,
    unbound: &mut Vec<String>,
) -> Result<(), AnyError> {
    let path = source.join(format!("native/session-{session_index}.strace"));
    let text = fs::read_to_string(&path)?;
    let scope_id = if session_index == 1 { "g1" } else { "g2" };
    let relative = relative_source_path(source, &path)?;
    for (offset, line) in text.split_inclusive('\n').enumerate() {
        parsed.raw.push(RawRecord {
            id: format!("system:s{session_index}:l{:09}", offset + 1),
            scope_id: scope_id.into(),
            source_type: "system_trace".into(),
            source_path: relative.clone(),
            ts_ns: trace_line_timestamp(line),
            payload: line.strip_suffix('\n').unwrap_or(line).into(),
            encoding: "utf8".into(),
        });
    }
    parsed.source_files.push(source_file(source, &path)?);
    let calls = stitch_trace(&text, session_index);
    let model = build_trace_model(&calls);
    let intervals = parsed
        .actions
        .iter()
        .filter(|action| action.ts_ns > 0 && action.end_ns >= action.ts_ns)
        .map(|action| (action.ts_ns, action.end_ns))
        .collect::<Vec<_>>();
    let raw_by_id = parsed
        .raw
        .iter()
        .map(|record| (record.id.clone(), record.payload.clone()))
        .collect::<HashMap<_, _>>();
    let mut owned_effect_ids = HashSet::new();

    for action in &mut parsed.actions {
        if action.closure == "observed" || action.ts_ns <= 0 || action.end_ns < action.ts_ns {
            continue;
        }
        let Some((command, workdir)) = parsed_tool_for_action(action, &raw_by_id) else {
            continue;
        };
        let Some(effects) = owned_process_effects(action, &command, &workdir, &intervals, &model)
        else {
            continue;
        };
        for effect in effects {
            for id in &effect.evidence_ids {
                owned_effect_ids.insert(id.clone());
            }
            merge_effect(&mut action.effects, effect);
        }
        action.closure = if action.effects.is_empty() {
            "no_effect"
        } else {
            "observed"
        }
        .into();
    }
    for (_, _, effect) in &model.effects {
        for id in &effect.evidence_ids {
            if !owned_effect_ids.contains(id) {
                unbound.push(id.clone());
            }
        }
    }
    Ok(())
}

fn owned_process_effects(
    action: &Action,
    command: &str,
    workdir: &str,
    intervals: &[(i64, i64)],
    model: &TraceModel,
) -> Option<Vec<Effect>> {
    let candidates = model
        .execs
        .iter()
        .filter(|exec| {
            action.ts_ns <= exec.ts_ns
                && exec.ts_ns <= action.end_ns
                && intervals
                    .iter()
                    .filter(|(start, end)| *start <= exec.ts_ns && exec.ts_ns <= *end)
                    .count()
                    == 1
                && command_matches(&exec.argv, command)
                && same_cwd(&exec.cwd, Path::new(workdir))
        })
        .collect::<Vec<_>>();
    if candidates.len() != 1 {
        return None;
    }
    let root = candidates[0];
    let subtree = process_subtree(root.pid, root.ts_ns, &model.children);
    if !subtree.iter().all(|pid| {
        model
            .exits
            .get(pid)
            .is_some_and(|exit| root.ts_ns <= *exit && *exit <= action.end_ns)
    }) {
        return None;
    }
    Some(
        model
            .effects
            .iter()
            .filter(|(pid, ts_ns, _)| {
                subtree.contains(pid)
                    && root.ts_ns <= *ts_ns
                    && *ts_ns <= action.end_ns
                    && model.exits.get(pid).is_some_and(|exit| *ts_ns <= *exit)
            })
            .map(|(_, _, effect)| effect.clone())
            .collect(),
    )
}

fn parsed_tool_for_action(
    action: &Action,
    raw_by_id: &HashMap<String, String>,
) -> Option<(String, String)> {
    for raw_id in &action.raw_ids {
        let value: Value = serde_json::from_str(raw_by_id.get(raw_id)?).ok()?;
        if value.pointer("/payload/type").and_then(Value::as_str) == Some("custom_tool_call") {
            let input = value.pointer("/payload/input").and_then(Value::as_str)?;
            if let Some(value) = nested_exec_command(input) {
                return Some(value);
            }
        }
    }
    None
}

fn nested_exec_command(input: &str) -> Option<(String, String)> {
    let marker = "tools.exec_command(";
    let start = input.find(marker)? + marker.len();
    let object_start = input[start..].find('{')? + start;
    let object_end = matching_json_object_end(input, object_start)?;
    let object = &input[object_start..object_end];
    if let Ok(value) = serde_json::from_str::<Value>(object) {
        return Some((
            value.get("cmd")?.as_str()?.to_string(),
            value
                .get("workdir")
                .or_else(|| value.get("cwd"))?
                .as_str()?
                .to_string(),
        ));
    }
    Some((
        js_object_string_field(object, "cmd")?,
        js_object_string_field(object, "workdir")
            .or_else(|| js_object_string_field(object, "cwd"))?,
    ))
}

fn js_object_string_field(object: &str, requested: &str) -> Option<String> {
    let body = object.strip_prefix('{')?.strip_suffix('}')?;
    for field in syscall_arguments(body) {
        let (name, value) = field.split_once(':')?;
        if name.trim().trim_matches(['"', '\'']) != requested {
            continue;
        }
        let value = value.trim();
        if !value.starts_with('"') {
            return None;
        }
        let mut escaped = false;
        for (offset, ch) in value[1..].char_indices() {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                return serde_json::from_str(&value[..offset + 2]).ok();
            }
        }
        return None;
    }
    None
}

fn matching_json_object_end(text: &str, start: usize) -> Option<usize> {
    let mut depth = 0usize;
    let mut quoted = false;
    let mut escaped = false;
    for (offset, ch) in text[start..].char_indices() {
        if escaped {
            escaped = false;
        } else if ch == '\\' && quoted {
            escaped = true;
        } else if ch == '"' {
            quoted = !quoted;
        } else if !quoted && ch == '{' {
            depth += 1;
        } else if !quoted && ch == '}' {
            depth = depth.checked_sub(1)?;
            if depth == 0 {
                return Some(start + offset + ch.len_utf8());
            }
        }
    }
    None
}

fn stitch_trace(text: &str, session_index: usize) -> Vec<TraceCall> {
    let mut pending = HashMap::<(u32, String), (i64, String, Vec<String>)>::new();
    let mut calls = Vec::new();
    for (offset, line) in text.lines().enumerate() {
        let raw_id = format!("system:s{session_index}:l{:09}", offset + 1);
        let Some((pid, ts_ns, body)) = trace_line_parts(line) else {
            continue;
        };
        if let Some(marker) = body.find(" <unfinished ...>") {
            let prefix = body[..marker].to_string();
            if let Some(syscall) = prefix.split_once('(').map(|value| value.0.to_string()) {
                pending.insert((pid, syscall), (ts_ns, prefix, vec![raw_id]));
            }
            continue;
        }
        if let Some(rest) = body.strip_prefix("<... ")
            && let Some((syscall, tail)) = rest.split_once(" resumed>")
            && let Some((start_ns, prefix, mut raw_ids)) =
                pending.remove(&(pid, syscall.to_string()))
        {
            raw_ids.push(raw_id);
            if let Some(call) = parse_trace_call(pid, start_ns, &format!("{prefix}{tail}"), raw_ids)
            {
                calls.push(call);
            }
            continue;
        }
        if let Some(call) = parse_trace_call(pid, ts_ns, body, vec![raw_id]) {
            calls.push(call);
        }
    }
    calls.sort_by_key(|call| call.ts_ns);
    calls
}

fn parse_trace_call(pid: u32, ts_ns: i64, body: &str, raw_ids: Vec<String>) -> Option<TraceCall> {
    if body.starts_with("+++") {
        return Some(TraceCall {
            pid,
            ts_ns,
            syscall: "process_exit".into(),
            arguments: body.into(),
            result: "0".into(),
            raw_ids,
        });
    }
    let open = body.find('(')?;
    let (left, result) = body.rsplit_once(" = ")?;
    let close = left.rfind(')')?;
    (close > open).then(|| TraceCall {
        pid,
        ts_ns,
        syscall: body[..open].trim().to_string(),
        arguments: body[open + 1..close].to_string(),
        result: result.trim().to_string(),
        raw_ids,
    })
}

fn build_trace_model(calls: &[TraceCall]) -> TraceModel {
    let mut model = TraceModel::default();
    let mut cwd = HashMap::<u32, PathBuf>::new();
    for call in calls {
        if let Some(path) = decoded_cwd(&call.arguments) {
            cwd.entry(call.pid).or_insert(path);
        }
        match call.syscall.as_str() {
            "clone" | "clone3" | "fork" | "vfork" if syscall_succeeded(&call.result) => {
                if let Some(child) = traced_child_pid(&call.result) {
                    model
                        .children
                        .entry(call.pid)
                        .or_default()
                        .push((child, call.ts_ns));
                    if let Some(parent_cwd) = cwd.get(&call.pid).cloned() {
                        cwd.entry(child).or_insert(parent_cwd);
                    }
                }
            }
            "chdir" if syscall_succeeded(&call.result) => {
                if let Some(value) = quoted_strings(&call.arguments).first() {
                    let next = if Path::new(value).is_absolute() {
                        PathBuf::from(value)
                    } else if let Some(base) = cwd.get(&call.pid) {
                        base.join(value)
                    } else {
                        continue;
                    };
                    if let Some(next) = lexical_absolute(next) {
                        cwd.insert(call.pid, next);
                    }
                }
            }
            "fchdir" if syscall_succeeded(&call.result) => {
                if let Some(path) = decoded_fd_path(&call.arguments) {
                    cwd.insert(call.pid, path);
                }
            }
            "execve" | "execveat" if syscall_succeeded(&call.result) => {
                if let (Some(argv), Some(process_cwd)) =
                    (exec_argv(&call.arguments), cwd.get(&call.pid).cloned())
                {
                    model.execs.push(TraceExec {
                        pid: call.pid,
                        ts_ns: call.ts_ns,
                        argv,
                        cwd: process_cwd,
                    });
                }
            }
            "exit" | "exit_group" | "process_exit" => {
                model.exits.insert(call.pid, call.ts_ns);
            }
            _ => {}
        }
        if syscall_succeeded(&call.result)
            && let Some(effect) = parse_trace_effect(call, &cwd)
        {
            model.effects.push((call.pid, call.ts_ns, effect));
        }
    }
    model
}

fn parse_trace_effect(call: &TraceCall, cwd: &HashMap<u32, PathBuf>) -> Option<Effect> {
    let quoted = quoted_strings(&call.arguments);
    let args = syscall_arguments(&call.arguments);
    let resolve = |quoted_index: usize, at_index: Option<usize>| {
        let value = quoted.get(quoted_index)?;
        resolve_syscall_path(
            value,
            at_index.and_then(|index| args.get(index).copied()),
            cwd.get(&call.pid),
        )
    };
    let (operation, path, previous_path) = match call.syscall.as_str() {
        "renameat" | "renameat2" => ("rename", resolve(1, Some(2))?, Some(resolve(0, Some(0))?)),
        "rename" => ("rename", resolve(1, None)?, Some(resolve(0, None)?)),
        "unlinkat" => ("delete", resolve(0, Some(0))?, None),
        "unlink" | "rmdir" => ("delete", resolve(0, None)?, None),
        "mkdirat" => ("create", resolve(0, Some(0))?, None),
        "symlinkat" => ("create", resolve(1, Some(1))?, None),
        "linkat" => ("create", resolve(1, Some(2))?, None),
        "mkdir" | "symlink" | "link" => {
            ("create", resolve(quoted.len().checked_sub(1)?, None)?, None)
        }
        "truncate" => ("write", resolve(0, None)?, None),
        "openat" | "openat2" => {
            let path = resolve(0, Some(0))?;
            let write = call.arguments.contains("O_WRONLY")
                || call.arguments.contains("O_RDWR")
                || call.arguments.contains("O_CREAT")
                || call.arguments.contains("O_TRUNC");
            (if write { "write" } else { "read" }, path, None)
        }
        "open" => {
            let path = resolve(0, None)?;
            let write = call.arguments.contains("O_WRONLY")
                || call.arguments.contains("O_RDWR")
                || call.arguments.contains("O_CREAT")
                || call.arguments.contains("O_TRUNC");
            (if write { "write" } else { "read" }, path, None)
        }
        _ => return None,
    };
    Some(Effect {
        operation: operation.into(),
        path,
        previous_path,
        evidence_ids: call.raw_ids.clone(),
    })
}

fn exec_argv(arguments: &str) -> Option<Vec<String>> {
    let args = syscall_arguments(arguments);
    let argv = args.get(1)?;
    let values = quoted_strings(argv);
    (!values.is_empty() && !argv.contains("...")).then_some(values)
}

fn command_matches(argv: &[String], command: &str) -> bool {
    argv.len() == 3
        && matches!(
            Path::new(&argv[0])
                .file_name()
                .and_then(|value| value.to_str()),
            Some("bash" | "sh" | "dash")
        )
        && argv[1] == "-c"
        && argv[2] == command
}

fn same_cwd(left: &Path, right: &Path) -> bool {
    lexical_absolute(left.to_path_buf()) == lexical_absolute(right.to_path_buf())
}

fn process_subtree(
    root: u32,
    root_exec_ns: i64,
    children: &HashMap<u32, Vec<(u32, i64)>>,
) -> HashSet<u32> {
    let mut result = HashSet::from([root]);
    let mut pending = vec![root];
    while let Some(parent) = pending.pop() {
        for (child, created_ns) in children.get(&parent).into_iter().flatten() {
            if *created_ns >= root_exec_ns && result.insert(*child) {
                pending.push(*child);
            }
        }
    }
    result
}

fn syscall_succeeded(result: &str) -> bool {
    leading_i64(result).is_some_and(|value| value >= 0)
}

fn leading_u32(result: &str) -> Option<u32> {
    leading_i64(result)?.try_into().ok()
}

fn traced_child_pid(result: &str) -> Option<u32> {
    result
        .split_once("/*")
        .and_then(|(_, comment)| comment.split_whitespace().next())
        .and_then(|value| value.parse().ok())
        .or_else(|| leading_u32(result))
}

fn leading_i64(result: &str) -> Option<i64> {
    let token = result.split_whitespace().next()?;
    let end = token
        .char_indices()
        .skip(usize::from(token.starts_with('-')))
        .find(|(_, ch)| !ch.is_ascii_digit())
        .map(|(index, _)| index)
        .unwrap_or(token.len());
    token.get(..end)?.parse().ok()
}

fn resolve_syscall_path(
    value: &str,
    at_arg: Option<&str>,
    cwd: Option<&PathBuf>,
) -> Option<String> {
    if Path::new(value).is_absolute() {
        return normalize_workspace_path(value);
    }
    let base = if let Some(argument) = at_arg {
        decoded_at_base(argument, cwd)?
    } else {
        cwd?.clone()
    };
    normalize_workspace_path(&base.join(value).to_string_lossy())
}

fn decoded_at_base(argument: &str, cwd: Option<&PathBuf>) -> Option<PathBuf> {
    if argument.trim().starts_with("AT_FDCWD") {
        if let Some(path) = decoded_angle_path(argument) {
            return Some(path);
        }
        return cwd.cloned();
    }
    decoded_angle_path(argument)
}

fn decoded_cwd(arguments: &str) -> Option<PathBuf> {
    syscall_arguments(arguments)
        .into_iter()
        .find(|argument| argument.trim().starts_with("AT_FDCWD<"))
        .and_then(decoded_angle_path)
}

fn decoded_fd_path(arguments: &str) -> Option<PathBuf> {
    syscall_arguments(arguments)
        .first()
        .and_then(|argument| decoded_angle_path(argument))
}

fn decoded_angle_path(argument: &str) -> Option<PathBuf> {
    let start = argument.find('<')? + 1;
    let end = argument[start..].find('>')? + start;
    let value = &argument[start..end];
    Path::new(value)
        .is_absolute()
        .then(|| lexical_absolute(PathBuf::from(value)))?
}

fn syscall_arguments(arguments: &str) -> Vec<&str> {
    let mut result = Vec::new();
    let mut start = 0usize;
    let mut quoted = false;
    let mut escaped = false;
    let mut nested = 0usize;
    for (index, byte) in arguments.as_bytes().iter().copied().enumerate() {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
            }
            continue;
        }
        match byte {
            b'"' => quoted = true,
            b'{' | b'[' | b'(' => nested += 1,
            b'}' | b']' | b')' => nested = nested.saturating_sub(1),
            b',' if nested == 0 => {
                result.push(&arguments[start..index]);
                start = index + 1;
            }
            _ => {}
        }
    }
    result.push(&arguments[start..]);
    result
}

fn quoted_strings(text: &str) -> Vec<String> {
    let mut result = Vec::new();
    let bytes = text.as_bytes();
    let mut start = None;
    let mut escaped = false;
    for (index, byte) in bytes.iter().copied().enumerate() {
        if let Some(begin) = start {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                if let Ok(value) = serde_json::from_str::<String>(&text[begin - 1..=index]) {
                    result.push(value);
                }
                start = None;
            }
        } else if byte == b'"' {
            start = Some(index + 1);
        }
    }
    result
}

fn trace_line_parts(line: &str) -> Option<(u32, i64, &str)> {
    let mut parts = line.splitn(3, char::is_whitespace);
    let pid = parts.next()?.parse().ok()?;
    let ts = parts.next()?.parse::<f64>().ok()?;
    let body = parts.next()?.trim_start();
    Some((pid, (ts * 1_000_000_000.0) as i64, body))
}

fn trace_line_timestamp(line: &str) -> Option<i64> {
    trace_line_parts(line).map(|value| value.1)
}

fn parse_environment_action(source: &Path) -> Result<ParsedSession, AnyError> {
    let path = source.join("target-start/source-effects.jsonl");
    let text = fs::read_to_string(&path)?;
    let relative = relative_source_path(source, &path)?;
    let mut raw = Vec::new();
    let mut started = None;
    let mut completed = None;
    for (offset, line) in text.lines().enumerate() {
        let value: Value = serde_json::from_str(line)?;
        let raw_id = format!("environment:l{:09}", offset + 1);
        let ts_ns = value["wall_time_ns"].as_i64();
        raw.push(RawRecord {
            id: raw_id.clone(),
            scope_id: "gsetup".into(),
            source_type: "environment_effect".into(),
            source_path: relative.clone(),
            ts_ns,
            payload: line.into(),
            encoding: "utf8".into(),
        });
        if value["action_id"].as_str() != Some("target-setup") {
            continue;
        }
        match value["phase"].as_str() {
            Some("started") => started = ts_ns.map(|ts| (ts, raw_id)),
            Some("completed") => completed = ts_ns.map(|ts| (ts, raw_id, value)),
            _ => {}
        }
    }
    let actions = match (started, completed) {
        (Some((start, start_id)), Some((end, end_id, value))) => {
            let effects = value["paths"]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .filter_map(normalize_workspace_path)
                .map(|path| Effect {
                    operation: "write".into(),
                    path,
                    previous_path: None,
                    evidence_ids: vec![end_id.clone()],
                })
                .collect::<Vec<_>>();
            vec![Action {
                id: "environment:target-setup".into(),
                ts_ns: start,
                end_ns: end,
                scope_id: "gsetup".into(),
                kind: "environment".into(),
                status: "completed".into(),
                closure: if effects.is_empty() {
                    "no_effect"
                } else {
                    "observed"
                }
                .into(),
                raw_ids: vec![start_id, end_id],
                effects,
            }]
        }
        (None, None) if text.is_empty() => Vec::new(),
        _ => return Err("target setup has an incomplete source-effect pair".into()),
    };
    Ok(ParsedSession {
        actions,
        raw,
        source_files: vec![source_file(source, &path)?],
    })
}

fn read_boundaries(
    source: &Path,
    records: &mut Vec<RawRecord>,
    source_files: &mut Vec<SourceFile>,
) -> Result<BTreeMap<String, Vec<BoundaryEntry>>, AnyError> {
    let mut result = BTreeMap::new();
    for (scope_id, name) in [
        ("g0", "h0"),
        ("g1", "prior-goal"),
        ("gsetup", "target-start"),
        ("g2", "target"),
    ] {
        let path = source.join(name).join("manifest.json");
        let entries: Vec<ManifestEntry> = serde_json::from_slice(&fs::read(&path)?)?;
        source_files.push(source_file(source, &path)?);
        let mut rows = Vec::new();
        for (offset, entry) in entries.into_iter().enumerate() {
            let id = format!("boundary:{name}:e{:09}", offset + 1);
            records.push(RawRecord {
                id: id.clone(),
                scope_id: scope_id.into(),
                source_type: "boundary_manifest_entry".into(),
                source_path: relative_source_path(source, &path)?,
                ts_ns: boundary_time(source, name),
                payload: serde_json::to_string(&entry)?,
                encoding: "utf8".into(),
            });
            rows.push(BoundaryEntry {
                entry,
                evidence_id: id,
            });
        }
        result.insert(name.into(), rows);
    }
    Ok(result)
}

fn add_remaining_sources(
    source: &Path,
    records: &mut Vec<RawRecord>,
    files: &mut Vec<SourceFile>,
) -> Result<(), AnyError> {
    let already = files
        .iter()
        .map(|file| file.path.clone())
        .collect::<HashSet<_>>();
    let mut paths = Vec::new();
    collect_files(source, source, &mut paths)?;
    paths.sort();
    for path in paths {
        let relative = relative_source_path(source, &path)?;
        if already.contains(&relative)
            || relative.starts_with("conditions/")
            || relative.starts_with("provenance/")
        {
            continue;
        }
        let scope_id = scope_for_source_path(&relative);
        let source_type = source_type_for_path(&relative);
        add_generic_file(source, &path, scope_id, source_type, records, files)?;
    }
    Ok(())
}

fn collect_files(root: &Path, current: &Path, output: &mut Vec<PathBuf>) -> Result<(), AnyError> {
    for entry in fs::read_dir(current)? {
        let path = entry?.path();
        let relative = path.strip_prefix(root)?;
        if relative.starts_with("conditions") || relative.starts_with("provenance") {
            continue;
        }
        if path.is_dir() {
            collect_files(root, &path, output)?;
        } else if path.is_file() {
            output.push(path);
        }
    }
    Ok(())
}

fn add_generic_file(
    source: &Path,
    path: &Path,
    scope_id: &str,
    source_type: &str,
    records: &mut Vec<RawRecord>,
    files: &mut Vec<SourceFile>,
) -> Result<(), AnyError> {
    let bytes = fs::read(path)?;
    let relative = relative_source_path(source, path)?;
    files.push(SourceFile {
        path: relative.clone(),
        bytes: bytes.len() as u64,
        sha256: sha256_bytes(&bytes),
    });
    if let Ok(text) = std::str::from_utf8(&bytes) {
        let mut count = 0usize;
        for (offset, line) in text.split_inclusive('\n').enumerate() {
            count += 1;
            records.push(RawRecord {
                id: format!("file:{relative}:l{:09}", offset + 1),
                scope_id: scope_id.into(),
                source_type: source_type.into(),
                source_path: relative.clone(),
                ts_ns: None,
                payload: line.strip_suffix('\n').unwrap_or(line).into(),
                encoding: "utf8".into(),
            });
        }
        if count == 0 {
            records.push(RawRecord {
                id: format!("file:{relative}:empty"),
                scope_id: scope_id.into(),
                source_type: source_type.into(),
                source_path: relative,
                ts_ns: None,
                payload: String::new(),
                encoding: "utf8".into(),
            });
        }
    } else {
        for (offset, page) in bytes.chunks(BINARY_PAGE_BYTES).enumerate() {
            records.push(RawRecord {
                id: format!("file:{relative}:p{:09}", offset + 1),
                scope_id: scope_id.into(),
                source_type: source_type.into(),
                source_path: relative.clone(),
                ts_ns: None,
                payload: json!({
                    "path": relative,
                    "offset_bytes": offset * BINARY_PAGE_BYTES,
                    "base64": base64::engine::general_purpose::STANDARD.encode(page),
                })
                .to_string(),
                encoding: "base64_page_json".into(),
            });
        }
    }
    Ok(())
}

fn source_type_for_path(path: &str) -> &'static str {
    if path.ends_with("workspace.tar") {
        "boundary_archive"
    } else if path.contains("/manifest") || path.ends_with("manifest.json") {
        "boundary_manifest"
    } else if path.starts_with("native/workload/") {
        "worker_visible_input"
    } else if path.starts_with("native/") {
        "capture_native"
    } else if path == "summary.json" {
        "capture_summary"
    } else {
        "boundary_proof"
    }
}

fn scope_for_source_path(path: &str) -> &'static str {
    if path.starts_with("prior-goal/") || path.contains("session-1") {
        "g1"
    } else if path.starts_with("target-start/") {
        "gsetup"
    } else if path.starts_with("target/") || path.contains("session-2") {
        "g2"
    } else {
        "g0"
    }
}

fn boundary_time(source: &Path, name: &str) -> Option<i64> {
    let value: Value =
        serde_json::from_slice(&fs::read(source.join(name).join("boundary.json")).ok()?).ok()?;
    value["wall_time_ns"].as_i64()
}

fn reclassify_creates<'a>(
    actions: &mut [Action],
    initial: impl Iterator<Item = &'a BoundaryEntry>,
) {
    let mut present = initial
        .filter(|row| row.entry.kind != "directory")
        .map(|row| row.entry.path.clone())
        .collect::<HashSet<_>>();
    for action in actions {
        for effect in &mut action.effects {
            match effect.operation.as_str() {
                "write" if !present.contains(&effect.path) => {
                    effect.operation = "create".into();
                    present.insert(effect.path.clone());
                }
                "write" | "create" => {
                    present.insert(effect.path.clone());
                }
                "delete" => {
                    present.remove(&effect.path);
                }
                "rename" => {
                    if let Some(previous) = &effect.previous_path {
                        present.remove(previous);
                    }
                    present.insert(effect.path.clone());
                }
                _ => {}
            }
        }
    }
}

fn verify_changed_paths(
    actions: &[Action],
    boundaries: &BTreeMap<String, Vec<BoundaryEntry>>,
) -> Result<(), AnyError> {
    let required = changed_paths(
        boundaries.get("h0").ok_or("missing h0")?,
        boundaries.get("prior-goal").ok_or("missing prior-goal")?,
    )
    .into_iter()
    .chain(changed_paths(
        boundaries
            .get("target-start")
            .ok_or("missing target-start")?,
        boundaries.get("target").ok_or("missing target")?,
    ))
    .collect::<BTreeSet<_>>();
    let observed = actions
        .iter()
        .flat_map(|action| &action.effects)
        .filter(|effect| effect.operation != "read")
        .flat_map(|effect| std::iter::once(effect.path.clone()).chain(effect.previous_path.clone()))
        .collect::<BTreeSet<_>>();
    let missing = required.difference(&observed).cloned().collect::<Vec<_>>();
    if !missing.is_empty() {
        return Err(format!(
            "changed workspace paths lack an exactly owned successful effect: {}",
            missing.join(", ")
        )
        .into());
    }
    Ok(())
}

fn changed_paths(before: &[BoundaryEntry], after: &[BoundaryEntry]) -> BTreeSet<String> {
    let before = boundary_map(before);
    let after = boundary_map(after);
    before
        .keys()
        .chain(after.keys())
        .filter(|path| before.get(*path) != after.get(*path))
        .cloned()
        .collect()
}

fn boundary_map(rows: &[BoundaryEntry]) -> BTreeMap<String, ManifestEntry> {
    rows.iter()
        .filter(|row| row.entry.kind != "directory")
        .map(|row| (row.entry.path.clone(), row.entry.clone()))
        .collect()
}

fn make_scopes(actions: &[Action], prior_goal: &str, target_goal: &str) -> Vec<Scope> {
    let span = |scope: &str| {
        let values = actions
            .iter()
            .filter(|action| action.scope_id == scope)
            .collect::<Vec<_>>();
        (
            values.iter().map(|action| action.ts_ns).min().unwrap_or(0),
            values.iter().map(|action| action.end_ns).max().unwrap_or(0),
        )
    };
    let (g1_start, g1_end) = span("g1");
    let (setup_start, setup_end) = span("gsetup");
    let (g2_start, g2_end) = span("g2");
    vec![
        Scope {
            id: "g1".into(),
            goal_id: "goal-1".into(),
            session_id: "session-1".into(),
            kind: "prior".into(),
            start_ns: g1_start,
            end_ns: g1_end,
            goal: prior_goal.into(),
        },
        Scope {
            id: "gsetup".into(),
            goal_id: "environment-transition".into(),
            session_id: "environment".into(),
            kind: "environment".into(),
            start_ns: setup_start,
            end_ns: setup_end,
            goal: "worker-visible transition between goals".into(),
        },
        Scope {
            id: "g2".into(),
            goal_id: "goal-2".into(),
            session_id: "session-2".into(),
            kind: "target".into(),
            start_ns: g2_start,
            end_ns: g2_end,
            goal: target_goal.into(),
        },
    ]
}

#[derive(Clone, Debug, Serialize)]
struct ArtifactEvent {
    action_id: Option<String>,
    scope_id: String,
    operation: String,
    path: String,
    previous_path: Option<String>,
    artifact_id: Option<String>,
    version_before: Option<u64>,
    version_after: Option<u64>,
    exists_after: Option<bool>,
    identity_status: String,
    raw_ids: Vec<String>,
}

#[derive(Clone, Debug)]
struct ActiveArtifact {
    id: String,
    version: u64,
    boundary_entry: Option<ManifestEntry>,
    mutated_since_boundary: bool,
}

#[derive(Debug, Default)]
struct ArtifactProjection {
    histories: BTreeMap<String, Vec<ArtifactEvent>>,
    artifacts_by_path: BTreeMap<String, BTreeSet<String>>,
    unresolved: Vec<ArtifactEvent>,
    boundary_issues: Vec<BoundaryIssue>,
}

#[derive(Clone, Debug, Serialize)]
struct BoundaryIssue {
    scope_id: String,
    boundary: String,
    path: String,
    kind: String,
    raw_ids: Vec<String>,
}

impl ArtifactProjection {
    fn push(&mut self, event: ArtifactEvent) {
        if let Some(artifact_id) = &event.artifact_id {
            self.artifacts_by_path
                .entry(event.path.clone())
                .or_default()
                .insert(artifact_id.clone());
            if let Some(previous) = &event.previous_path {
                self.artifacts_by_path
                    .entry(previous.clone())
                    .or_default()
                    .insert(artifact_id.clone());
            }
            self.histories
                .entry(artifact_id.clone())
                .or_default()
                .push(event);
        } else {
            self.unresolved.push(event);
        }
    }
}

fn allocate_artifact_id(next_id: &mut u64) -> String {
    let id = format!("f{next_id:08}");
    *next_id += 1;
    id
}

fn projected_event(
    action: Option<&Action>,
    effect: &Effect,
    artifact_id: Option<String>,
    version_before: Option<u64>,
    version_after: Option<u64>,
    exists_after: Option<bool>,
    identity_status: &str,
) -> ArtifactEvent {
    ArtifactEvent {
        action_id: action.map(|row| row.id.clone()),
        scope_id: action.map_or_else(|| "g0".into(), |row| row.scope_id.clone()),
        operation: effect.operation.clone(),
        path: effect.path.clone(),
        previous_path: effect.previous_path.clone(),
        artifact_id,
        version_before,
        version_after,
        exists_after,
        identity_status: identity_status.into(),
        raw_ids: effect.evidence_ids.clone(),
    }
}

fn boundary_event(
    scope_id: &str,
    effect: Effect,
    artifact_id: String,
    version_before: u64,
    version_after: u64,
    exists_after: bool,
    identity_status: &str,
) -> ArtifactEvent {
    ArtifactEvent {
        action_id: None,
        scope_id: scope_id.into(),
        operation: effect.operation,
        path: effect.path,
        previous_path: effect.previous_path,
        artifact_id: Some(artifact_id),
        version_before: Some(version_before),
        version_after: Some(version_after),
        exists_after: Some(exists_after),
        identity_status: identity_status.into(),
        raw_ids: effect.evidence_ids,
    }
}

fn boundary_after_scope(scope_id: &str) -> Option<&'static str> {
    match scope_id {
        "g1" => Some("prior-goal"),
        "gsetup" => Some("target-start"),
        "g2" => Some("target"),
        _ => None,
    }
}

fn known_directory_paths(store: &StoreData) -> HashSet<String> {
    store
        .index
        .boundaries
        .values()
        .flatten()
        .filter(|row| row.entry.kind == "directory")
        .map(|row| row.entry.path.clone())
        .collect()
}

fn boundary_proof_ids(store: &StoreData, boundary_name: &str) -> Vec<String> {
    let source_path = format!("{boundary_name}/boundary.json");
    store
        .records
        .iter()
        .filter(|record| {
            record.source_type == "boundary_proof"
                && record.source_path == source_path
                && (record.payload.contains("\"accepted\"")
                    || record.payload.contains("\"entries\"")
                    || record.payload.contains("\"manifest_sha256\""))
        })
        .map(|record| record.id.clone())
        .collect()
}

fn reconcile_boundary(
    scope_id: &str,
    boundary_name: &str,
    rows: &[BoundaryEntry],
    proof_ids: &[String],
    active: &mut BTreeMap<String, ActiveArtifact>,
    next_id: &mut u64,
    projection: &mut ArtifactProjection,
) {
    let expected = boundary_map(rows);
    let paths = active
        .keys()
        .chain(expected.keys())
        .cloned()
        .collect::<BTreeSet<_>>();
    for path in paths {
        let current = active.remove(&path);
        let observed = expected.get(&path);
        match (current, observed) {
            (Some(mut state), Some(entry)) => {
                let raw_ids = rows
                    .iter()
                    .filter(|row| row.entry.path == path)
                    .map(|row| row.evidence_id.clone())
                    .collect::<Vec<_>>();
                if !state.mutated_since_boundary
                    && state
                        .boundary_entry
                        .as_ref()
                        .is_some_and(|prior| prior != entry)
                {
                    let before = state.version;
                    state.version += 1;
                    projection.push(boundary_event(
                        scope_id,
                        Effect {
                            operation: "boundary_replacement".into(),
                            path: path.clone(),
                            previous_path: None,
                            evidence_ids: raw_ids.clone(),
                        },
                        state.id,
                        before,
                        state.version,
                        false,
                        "unknown_unattributed_boundary_replacement",
                    ));
                    let id = allocate_artifact_id(next_id);
                    projection.push(boundary_event(
                        scope_id,
                        Effect {
                            operation: "boundary_replacement".into(),
                            path: path.clone(),
                            previous_path: None,
                            evidence_ids: raw_ids.clone(),
                        },
                        id.clone(),
                        0,
                        0,
                        true,
                        "unknown_unattributed_boundary_replacement",
                    ));
                    projection.boundary_issues.push(BoundaryIssue {
                        scope_id: scope_id.into(),
                        boundary: boundary_name.into(),
                        path: path.clone(),
                        kind: "unattributed_replacement".into(),
                        raw_ids,
                    });
                    active.insert(
                        path,
                        ActiveArtifact {
                            id,
                            version: 0,
                            boundary_entry: Some(entry.clone()),
                            mutated_since_boundary: false,
                        },
                    );
                } else {
                    projection.push(boundary_event(
                        scope_id,
                        Effect {
                            operation: "boundary_state".into(),
                            path: path.clone(),
                            previous_path: None,
                            evidence_ids: raw_ids,
                        },
                        state.id.clone(),
                        state.version,
                        state.version,
                        true,
                        "observed_reconciled",
                    ));
                    state.boundary_entry = Some(entry.clone());
                    state.mutated_since_boundary = false;
                    active.insert(path, state);
                }
            }
            (None, Some(entry)) => {
                let raw_ids = rows
                    .iter()
                    .filter(|row| row.entry.path == path)
                    .map(|row| row.evidence_id.clone())
                    .collect::<Vec<_>>();
                let id = allocate_artifact_id(next_id);
                projection.push(boundary_event(
                    scope_id,
                    Effect {
                        operation: "boundary_create".into(),
                        path: path.clone(),
                        previous_path: None,
                        evidence_ids: raw_ids.clone(),
                    },
                    id.clone(),
                    0,
                    0,
                    true,
                    "unknown_missing_effect",
                ));
                projection.boundary_issues.push(BoundaryIssue {
                    scope_id: scope_id.into(),
                    boundary: boundary_name.into(),
                    path: path.clone(),
                    kind: "missing_create_effect".into(),
                    raw_ids,
                });
                active.insert(
                    path,
                    ActiveArtifact {
                        id,
                        version: 0,
                        boundary_entry: Some(entry.clone()),
                        mutated_since_boundary: false,
                    },
                );
            }
            (Some(mut state), None) => {
                let before = state.version;
                state.version += 1;
                projection.push(boundary_event(
                    scope_id,
                    Effect {
                        operation: "boundary_delete".into(),
                        path: path.clone(),
                        previous_path: None,
                        evidence_ids: proof_ids.to_vec(),
                    },
                    state.id,
                    before,
                    state.version,
                    false,
                    "unknown_missing_effect",
                ));
                projection.boundary_issues.push(BoundaryIssue {
                    scope_id: scope_id.into(),
                    boundary: boundary_name.into(),
                    path,
                    kind: "missing_delete_effect".into(),
                    raw_ids: proof_ids.to_vec(),
                });
            }
            (None, None) => unreachable!(),
        }
    }
}

fn build_artifact_projection(store: &StoreData) -> ArtifactProjection {
    let mut projection = ArtifactProjection::default();
    let mut active = BTreeMap::<String, ActiveArtifact>::new();
    let mut next_id = 1_u64;

    let mut initial = store
        .index
        .boundaries
        .get("h0")
        .into_iter()
        .flatten()
        .filter(|row| row.entry.kind != "directory")
        .collect::<Vec<_>>();
    initial.sort_by(|left, right| left.entry.path.cmp(&right.entry.path));
    for row in initial {
        let id = allocate_artifact_id(&mut next_id);
        active.insert(
            row.entry.path.clone(),
            ActiveArtifact {
                id: id.clone(),
                version: 0,
                boundary_entry: Some(row.entry.clone()),
                mutated_since_boundary: false,
            },
        );
        projection.push(ArtifactEvent {
            action_id: None,
            scope_id: "g0".into(),
            operation: "boundary_state".into(),
            path: row.entry.path.clone(),
            previous_path: None,
            artifact_id: Some(id),
            version_before: None,
            version_after: Some(0),
            exists_after: Some(true),
            identity_status: "observed".into(),
            raw_ids: vec![row.evidence_id.clone()],
        });
    }

    let directories = known_directory_paths(store);
    let mut actions = store.actions.iter().collect::<Vec<_>>();
    actions.sort_by(|left, right| {
        left.ts_ns
            .cmp(&right.ts_ns)
            .then_with(|| left.id.cmp(&right.id))
    });
    let mut scopes = store.index.scopes.iter().collect::<Vec<_>>();
    scopes.sort_by_key(|scope| (scope.start_ns, &scope.id));
    let scope_ids = if scopes.is_empty() {
        vec!["g1", "gsetup", "g2"]
    } else {
        scopes.iter().map(|scope| scope.id.as_str()).collect()
    };
    let ordered_scope_ids = scope_ids.iter().copied().collect::<HashSet<_>>();
    for scope_id in scope_ids.into_iter().chain(
        actions
            .iter()
            .map(|action| action.scope_id.as_str())
            .filter(|scope| !ordered_scope_ids.contains(scope)),
    ) {
        for action in actions
            .iter()
            .copied()
            .filter(|action| action.scope_id == scope_id)
        {
            for effect in &action.effects {
                if directories.contains(&effect.path)
                    || effect
                        .previous_path
                        .as_ref()
                        .is_some_and(|path| directories.contains(path))
                {
                    continue;
                }
                match effect.operation.as_str() {
                    "read" => {
                        if let Some(state) = active.get(&effect.path) {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                Some(state.id.clone()),
                                Some(state.version),
                                Some(state.version),
                                Some(true),
                                "observed",
                            ));
                        } else {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_missing_prior_state",
                            ));
                        }
                    }
                    "create" => {
                        if active.contains_key(&effect.path) {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_create_on_existing_path",
                            ));
                        } else {
                            let id = allocate_artifact_id(&mut next_id);
                            active.insert(
                                effect.path.clone(),
                                ActiveArtifact {
                                    id: id.clone(),
                                    version: 0,
                                    boundary_entry: None,
                                    mutated_since_boundary: true,
                                },
                            );
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                Some(id),
                                None,
                                Some(0),
                                Some(true),
                                "observed",
                            ));
                        }
                    }
                    "write" => {
                        if let Some(mut state) = active.get(&effect.path).cloned() {
                            let before = state.version;
                            state.version += 1;
                            state.boundary_entry = None;
                            state.mutated_since_boundary = true;
                            active.insert(effect.path.clone(), state.clone());
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                Some(state.id),
                                Some(before),
                                Some(state.version),
                                Some(true),
                                "observed",
                            ));
                        } else {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_missing_prior_state",
                            ));
                        }
                    }
                    "delete" => {
                        if let Some(mut state) = active.remove(&effect.path) {
                            let before = state.version;
                            state.version += 1;
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                Some(state.id),
                                Some(before),
                                Some(state.version),
                                Some(false),
                                "observed",
                            ));
                        } else {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_missing_prior_state",
                            ));
                        }
                    }
                    "rename" => {
                        let Some(previous) = effect.previous_path.as_ref() else {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_missing_previous_path",
                            ));
                            continue;
                        };
                        let Some(mut state) = active.remove(previous) else {
                            projection.push(projected_event(
                                Some(action),
                                effect,
                                None,
                                None,
                                None,
                                None,
                                "unknown_missing_prior_state",
                            ));
                            continue;
                        };
                        if let Some(mut overwritten) = active.remove(&effect.path) {
                            let before = overwritten.version;
                            overwritten.version += 1;
                            let overwrite = Effect {
                                operation: "delete".into(),
                                path: effect.path.clone(),
                                previous_path: None,
                                evidence_ids: effect.evidence_ids.clone(),
                            };
                            projection.push(projected_event(
                                Some(action),
                                &overwrite,
                                Some(overwritten.id),
                                Some(before),
                                Some(overwritten.version),
                                Some(false),
                                "observed_rename_overwrite",
                            ));
                        }
                        let before = state.version;
                        state.version += 1;
                        state.boundary_entry = None;
                        state.mutated_since_boundary = true;
                        active.insert(effect.path.clone(), state.clone());
                        projection.push(projected_event(
                            Some(action),
                            effect,
                            Some(state.id),
                            Some(before),
                            Some(state.version),
                            Some(true),
                            "observed",
                        ));
                    }
                    _ => projection.push(projected_event(
                        Some(action),
                        effect,
                        None,
                        None,
                        None,
                        None,
                        "unknown_operation",
                    )),
                }
            }
        }
        if let Some(boundary_name) = boundary_after_scope(scope_id)
            && let Some(rows) = store.index.boundaries.get(boundary_name)
        {
            let proof_ids = boundary_proof_ids(store, boundary_name);
            reconcile_boundary(
                scope_id,
                boundary_name,
                rows,
                &proof_ids,
                &mut active,
                &mut next_id,
                &mut projection,
            );
        }
    }
    projection
}

fn artifact_projection(store: &StoreData) -> &ArtifactProjection {
    store
        .artifact_projection
        .get_or_init(|| build_artifact_projection(store))
}

pub(crate) fn artifact_history(store: &StoreData, requested: &str) -> Value {
    if is_harness_store(store) {
        let actions = store
            .actions
            .iter()
            .filter_map(|action| {
                let effects = action
                    .effects
                    .iter()
                    .filter(|effect| {
                        effect.path == requested
                            || effect.previous_path.as_deref() == Some(requested)
                    })
                    .collect::<Vec<_>>();
                (!effects.is_empty()).then(|| {
                    json!({
                        "kind": "action",
                        "action_id": action.id,
                        "scope_id": action.scope_id,
                        "ts_ns": action.ts_ns,
                        "end_ns": action.end_ns,
                        "status": action.status,
                        "closure": action.closure,
                        "effects": effects,
                        "raw_ids": action.raw_ids,
                    })
                })
            })
            .collect::<Vec<_>>();
        let snapshots = store
            .index
            .scopes
            .iter()
            .filter_map(|scope| {
                store.index.boundaries.get(&scope.id).and_then(|rows| {
                    rows.iter()
                        .find(|row| row.entry.path == requested)
                        .map(|row| {
                            json!({
                                "kind": "snapshot_state",
                                "scope_id": scope.id,
                                "entry": row.entry,
                                "raw_ids": [row.evidence_id.clone()],
                            })
                        })
                })
            })
            .collect::<Vec<_>>();
        return json!({
            "requested_path": requested,
            "actions": actions,
            "snapshot_states": snapshots,
        });
    }
    let projection = artifact_projection(store);
    let artifact_ids = projection
        .artifacts_by_path
        .get(requested)
        .cloned()
        .unwrap_or_default();
    let artifacts = artifact_ids
        .iter()
        .map(|artifact_id| {
            json!({
                "artifact_id": artifact_id,
                "history": projection.histories.get(artifact_id).cloned().unwrap_or_default(),
            })
        })
        .collect::<Vec<_>>();
    let unresolved = projection
        .unresolved
        .iter()
        .filter(|event| {
            event.path == requested || event.previous_path.as_deref() == Some(requested)
        })
        .cloned()
        .collect::<Vec<_>>();
    let boundary_issues = projection
        .boundary_issues
        .iter()
        .filter(|issue| issue.path == requested)
        .cloned()
        .collect::<Vec<_>>();
    json!({
        "requested_path": requested,
        "version_semantics": "ordered observed mutation revision; exact content state is anchored at boundary_state events",
        "path_reused": artifact_ids.len() > 1,
        "artifacts": artifacts,
        "unresolved": unresolved,
        "boundary_issues": boundary_issues,
    })
}

pub(crate) fn session_diff(store: &StoreData, from_session: &str, to_session: &str) -> Value {
    let Some(before_rows) = store.index.boundaries.get(from_session) else {
        return json!({"error": format!("unknown from_session {from_session}")});
    };
    let Some(after_rows) = store.index.boundaries.get(to_session) else {
        return json!({"error": format!("unknown to_session {to_session}")});
    };
    let before = boundary_map(before_rows);
    let after = boundary_map(after_rows);
    let changes = before
        .keys()
        .chain(after.keys())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .filter_map(|path| {
            let left = before.get(path);
            let right = after.get(path);
            (left != right).then(|| {
                let relation = match (left, right) {
                    (None, Some(_)) => "added",
                    (Some(_), None) => "removed",
                    _ => "changed",
                };
                let mut raw_ids = before_rows
                    .iter()
                    .chain(after_rows)
                    .filter(|row| row.entry.path == *path)
                    .map(|row| row.evidence_id.clone())
                    .collect::<Vec<_>>();
                raw_ids.sort();
                raw_ids.dedup();
                json!({
                    "path": path,
                    "relation": relation,
                    "before": left,
                    "after": right,
                    "raw_ids": raw_ids,
                })
            })
        })
        .collect::<Vec<_>>();
    json!({
        "from_session": from_session,
        "to_session": to_session,
        "changes": changes,
    })
}

pub(crate) fn verify_artifact_projection(store: &StoreData) -> Result<(), AnyError> {
    if is_harness_store(store) {
        if store.index.scopes.len() < 2
            || store
                .index
                .scopes
                .iter()
                .any(|scope| !store.index.boundaries.contains_key(&scope.id))
        {
            return Err("Harness store lacks a complete snapshot for every prefix session".into());
        }
        for pair in store.index.scopes.windows(2) {
            let value = session_diff(store, &pair[0].id, &pair[1].id);
            if value.get("error").is_some() {
                return Err("Harness session_diff could not be recomputed".into());
            }
        }
        return Ok(());
    }
    let issues = &artifact_projection(store).boundary_issues;
    if issues.is_empty() {
        return Ok(());
    }
    let preview = issues
        .iter()
        .take(8)
        .map(|issue| format!("{}:{}:{}", issue.boundary, issue.kind, issue.path))
        .collect::<Vec<_>>()
        .join(", ");
    Err(format!(
        "artifact replay disagrees with exact boundaries at {} path(s): {preview}",
        issues.len()
    )
    .into())
}

pub(crate) fn action_effects(store: &StoreData, action_id: &str) -> Value {
    let Some(action) = store.actions.iter().find(|action| action.id == action_id) else {
        return json!({"error": format!("unknown action_id {action_id}")});
    };
    if is_harness_store(store) {
        return json!({
            "action_id": action.id,
            "scope_id": action.scope_id,
            "closure": action.closure,
            "effects": action.effects,
            "raw_ids": action.raw_ids,
        });
    }
    let projection = artifact_projection(store);
    let versioned_effects = projection
        .histories
        .values()
        .flatten()
        .chain(projection.unresolved.iter())
        .filter(|event| event.action_id.as_deref() == Some(action_id))
        .cloned()
        .collect::<Vec<_>>();
    let unknown_ids = store
        .index
        .unbound_workspace_effect_ids
        .iter()
        .collect::<HashSet<_>>();
    let unknown_candidates = if action.closure == "unknown" {
        store
            .records
            .iter()
            .filter(|record| {
                unknown_ids.contains(&record.id)
                    && record.scope_id == action.scope_id
                    && record
                        .ts_ns
                        .is_some_and(|ts| ts >= action.ts_ns && ts <= action.end_ns)
            })
            .map(|record| {
                json!({
                    "raw_id": record.id,
                    "ts_ns": record.ts_ns,
                    "source_type": record.source_type,
                    "attribution": "unknown",
                })
            })
            .collect::<Vec<_>>()
    } else {
        Vec::new()
    };
    json!({
        "action_id": action.id,
        "scope_id": action.scope_id,
        "closure": action.closure,
        "effects": action.effects,
        "versioned_effects": versioned_effects,
        "unknown_candidates": unknown_candidates,
        "raw_ids": action.raw_ids,
    })
}

fn is_harness_store(store: &StoreData) -> bool {
    store.index.domain == "harness-bench"
}

fn reject_visible_leaks(records: &[RawRecord], prior: &str, target: &str) -> Result<(), AnyError> {
    reject_leak(prior, "prior goal")?;
    reject_leak(target, "target goal")?;
    for record in records {
        reject_leak(&record.source_path, &format!("source path {}", record.id))?;
        reject_leak(&record.payload, &format!("payload {}", record.id))?;
    }
    Ok(())
}

fn reject_leak(text: &str, location: &str) -> Result<(), AnyError> {
    let lowered = text.to_ascii_lowercase();
    if let Some(term) = LEAK_TERMS.iter().find(|term| lowered.contains(**term)) {
        return Err(format!("model-visible leakage term {term:?} in {location}").into());
    }
    Ok(())
}

fn remap_ids(ids: &mut Vec<String>, map: &HashMap<String, String>) -> Result<(), AnyError> {
    for id in ids.iter_mut() {
        *id = map
            .get(id)
            .ok_or_else(|| format!("missing Raw-ID remap for {id}"))?
            .clone();
    }
    ids.sort();
    ids.dedup();
    Ok(())
}

fn merge_effect(effects: &mut Vec<Effect>, incoming: Effect) {
    if let Some(existing) = effects.iter_mut().find(|effect| {
        effect.operation == incoming.operation
            && effect.path == incoming.path
            && effect.previous_path == incoming.previous_path
    }) {
        existing.evidence_ids.extend(incoming.evidence_ids);
        existing.evidence_ids.sort();
        existing.evidence_ids.dedup();
    } else {
        effects.push(incoming);
    }
}

fn session_ids(summary: &Value) -> Result<[String; 2], AnyError> {
    let mut values = Vec::new();
    for index in 0..2 {
        let value = summary
            .pointer(&format!("/thread_ids_by_session/{index}/0"))
            .and_then(Value::as_str)
            .ok_or_else(|| format!("summary lacks session {index} thread ID"))?;
        values.push(value.to_string());
    }
    Ok([values.remove(0), values.remove(0)])
}

fn find_retained_session(root: &Path, session_id: &str) -> Result<Option<PathBuf>, AnyError> {
    if !root.exists() {
        return Ok(None);
    }
    for entry in fs::read_dir(root)? {
        let path = entry?.path();
        if path.is_dir() {
            if let Some(found) = find_retained_session(&path, session_id)? {
                return Ok(Some(found));
            }
        } else if path
            .file_name()
            .and_then(|value| value.to_str())
            .is_some_and(|value| value.ends_with(".jsonl") && value.contains(session_id))
        {
            return Ok(Some(path));
        }
    }
    Ok(None)
}

fn normalize_workspace_path(raw: &str) -> Option<String> {
    let marker = "/workspace/";
    let relative = if let Some((_, suffix)) = raw.rsplit_once(marker) {
        suffix
    } else if raw.ends_with("/workspace") || raw.starts_with('/') {
        return None;
    } else {
        raw
    };
    let mut output = PathBuf::new();
    for component in Path::new(relative).components() {
        match component {
            Component::Normal(value) => output.push(value),
            Component::CurDir => {}
            Component::ParentDir => {
                if !output.pop() {
                    return None;
                }
            }
            _ => return None,
        }
    }
    let value = output.to_string_lossy().replace('\\', "/");
    (!value.is_empty()).then_some(value)
}

fn lexical_absolute(path: PathBuf) -> Option<PathBuf> {
    let mut output = PathBuf::from("/");
    for component in path.components() {
        match component {
            Component::RootDir => output = PathBuf::from("/"),
            Component::Normal(value) => output.push(value),
            Component::CurDir => {}
            Component::ParentDir => {
                if !output.pop() {
                    return None;
                }
            }
            _ => return None,
        }
    }
    Some(output)
}

fn relative_source_path(source: &Path, path: &Path) -> Result<String, AnyError> {
    Ok(path
        .strip_prefix(source)?
        .to_string_lossy()
        .replace('\\', "/"))
}

fn source_file(source: &Path, path: &Path) -> Result<SourceFile, AnyError> {
    let bytes = fs::read(path)?;
    Ok(SourceFile {
        path: relative_source_path(source, path)?,
        bytes: bytes.len() as u64,
        sha256: sha256_bytes(&bytes),
    })
}

fn write_jsonl<T: Serialize>(path: &Path, rows: &[T]) -> Result<(), AnyError> {
    let mut bytes = Vec::new();
    for row in rows {
        serde_json::to_writer(&mut bytes, row)?;
        bytes.push(b'\n');
    }
    fs::write(path, bytes)?;
    Ok(())
}

fn parse_jsonl_bytes<T: for<'de> Deserialize<'de>>(bytes: &[u8]) -> Result<Vec<T>, AnyError> {
    bytes
        .split(|byte| *byte == b'\n')
        .filter(|line| !line.is_empty())
        .map(|line| Ok(serde_json::from_slice(line)?))
        .collect()
}

fn sha256_bytes(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn sha256_parts(parts: &[&[u8]]) -> String {
    let mut hash = Sha256::new();
    for part in parts {
        hash.update((part.len() as u64).to_le_bytes());
        hash.update(part);
    }
    hex::encode(hash.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn boundary(path: &str, hash: &str, evidence_id: &str) -> BoundaryEntry {
        BoundaryEntry {
            entry: ManifestEntry {
                path: path.into(),
                kind: "file".into(),
                mode: None,
                mtime_ns: None,
                sha256: Some(hash.into()),
                size: Some(1),
                target: None,
            },
            evidence_id: evidence_id.into(),
        }
    }

    fn test_store(
        actions: Vec<Action>,
        boundaries: BTreeMap<String, Vec<BoundaryEntry>>,
        records: Vec<RawRecord>,
        unbound: Vec<String>,
    ) -> StoreData {
        StoreData {
            index: StoreIndex {
                schema: STORE_SCHEMA.into(),
                episode_id: "episode".into(),
                domain: "test".into(),
                source_store_sha256: "store".into(),
                raw_ids_sha256: "raw-ids".into(),
                raw_jsonl_sha256: "raw".into(),
                actions_jsonl_sha256: "actions".into(),
                records: records.len(),
                actions: actions.len(),
                scopes: vec![],
                boundaries,
                source_files: vec![],
                unbound_workspace_effect_ids: unbound,
            },
            records,
            actions,
            artifact_projection: OnceLock::new(),
        }
    }

    #[test]
    fn stitches_unfinished_trace_rows_and_keeps_both_raw_ids() {
        let text = concat!(
            "7 1780000000.100000 openat(AT_FDCWD</x/workspace>, \"a\", O_RDONLY <unfinished ...>\n",
            "7 1780000000.200000 <... openat resumed>) = 3</x/workspace/a>\n",
        );
        let calls = stitch_trace(text, 1);
        assert_eq!(calls.len(), 1);
        assert_eq!(calls[0].raw_ids.len(), 2);
        assert_eq!(calls[0].syscall, "openat");
        assert!(syscall_succeeded(&calls[0].result));
    }

    #[test]
    fn decoded_numeric_dirfd_never_falls_back_to_cwd() {
        assert_eq!(
            decoded_at_base("5</x/workspace/src>", Some(&PathBuf::from("/wrong"))),
            Some(PathBuf::from("/x/workspace/src"))
        );
        assert_eq!(decoded_at_base("5", Some(&PathBuf::from("/wrong"))), None);
    }

    #[test]
    fn exact_shell_command_and_cwd_are_required() {
        let argv = vec!["/usr/bin/bash".into(), "-c".into(), "rg x".into()];
        assert!(command_matches(&argv, "rg x"));
        assert!(!command_matches(&argv, "rg y"));
        assert!(same_cwd(Path::new("/a/../b"), Path::new("/b")));
    }

    #[test]
    fn artifact_versions_preserve_rename_and_split_path_reuse() {
        let actions = vec![
            Action {
                id: "a1".into(),
                ts_ns: 1,
                end_ns: 2,
                scope_id: "g1".into(),
                kind: "rename".into(),
                status: "ok".into(),
                closure: "observed".into(),
                raw_ids: vec!["r1".into()],
                effects: vec![Effect {
                    operation: "rename".into(),
                    path: "new".into(),
                    previous_path: Some("old".into()),
                    evidence_ids: vec!["r1".into()],
                }],
            },
            Action {
                id: "a2".into(),
                ts_ns: 3,
                end_ns: 4,
                scope_id: "g2".into(),
                kind: "write".into(),
                status: "ok".into(),
                closure: "observed".into(),
                raw_ids: vec!["r2".into()],
                effects: vec![Effect {
                    operation: "create".into(),
                    path: "old".into(),
                    previous_path: None,
                    evidence_ids: vec!["r2".into()],
                }],
            },
        ];
        let store = test_store(
            actions,
            BTreeMap::from([("h0".into(), vec![boundary("old", "h0", "r0")])]),
            vec![],
            vec![],
        );
        let old = artifact_history(&store, "old");
        let new = artifact_history(&store, "new");
        assert_eq!(old["path_reused"], true);
        assert_eq!(old["artifacts"].as_array().unwrap().len(), 2);
        assert_eq!(new["artifacts"].as_array().unwrap().len(), 1);
        assert_eq!(
            old["artifacts"][0]["artifact_id"],
            new["artifacts"][0]["artifact_id"]
        );
        assert_eq!(new["artifacts"][0]["history"][1]["version_before"], 0);
        assert_eq!(new["artifacts"][0]["history"][1]["version_after"], 1);
    }

    #[test]
    fn exact_boundaries_anchor_an_observed_mutation_without_advancing_it_twice() {
        let action = Action {
            id: "a1".into(),
            ts_ns: 1,
            end_ns: 2,
            scope_id: "g1".into(),
            kind: "write".into(),
            status: "ok".into(),
            closure: "observed".into(),
            raw_ids: vec!["r1".into()],
            effects: vec![Effect {
                operation: "write".into(),
                path: "file".into(),
                previous_path: None,
                evidence_ids: vec!["r1".into()],
            }],
        };
        let boundaries = BTreeMap::from([
            ("h0".into(), vec![boundary("file", "h0", "b0")]),
            ("prior-goal".into(), vec![boundary("file", "changed", "b1")]),
            (
                "target-start".into(),
                vec![boundary("file", "changed", "b2")],
            ),
            ("target".into(), vec![boundary("file", "changed", "b3")]),
        ]);
        let store = test_store(vec![action], boundaries, vec![], vec![]);
        verify_artifact_projection(&store).unwrap();
        let history = artifact_history(&store, "file");
        assert_eq!(history["artifacts"].as_array().unwrap().len(), 1);
        let events = history["artifacts"][0]["history"].as_array().unwrap();
        assert_eq!(events[1]["operation"], "write");
        assert_eq!(events[1]["version_after"], 1);
        assert_eq!(events[2]["operation"], "boundary_state");
        assert_eq!(events[2]["version_after"], 1);
        assert_eq!(history["boundary_issues"].as_array().unwrap().len(), 0);
    }

    #[test]
    fn unexplained_boundary_replacement_splits_identity_and_blocks_preflight() {
        let boundaries = BTreeMap::from([
            ("h0".into(), vec![boundary("file", "h0", "b0")]),
            ("prior-goal".into(), vec![boundary("file", "changed", "b1")]),
            (
                "target-start".into(),
                vec![boundary("file", "changed", "b2")],
            ),
            ("target".into(), vec![boundary("file", "changed", "b3")]),
        ]);
        let store = test_store(vec![], boundaries, vec![], vec![]);
        let error = verify_artifact_projection(&store).unwrap_err().to_string();
        assert!(error.contains("unattributed_replacement:file"));
        let history = artifact_history(&store, "file");
        assert_eq!(history["path_reused"], true);
        assert_eq!(history["artifacts"].as_array().unwrap().len(), 2);
        assert_eq!(history["boundary_issues"].as_array().unwrap().len(), 1);
    }

    #[test]
    fn unknown_action_returns_only_temporally_overlapping_unbound_candidates() {
        let action = Action {
            id: "a1".into(),
            ts_ns: 10,
            end_ns: 20,
            scope_id: "g2".into(),
            kind: "exec".into(),
            status: "ok".into(),
            closure: "unknown".into(),
            raw_ids: vec!["native".into()],
            effects: vec![],
        };
        let records = vec![
            RawRecord {
                id: "candidate".into(),
                scope_id: "g2".into(),
                source_type: "system_trace".into(),
                source_path: "trace".into(),
                ts_ns: Some(15),
                payload: "effect".into(),
                encoding: "utf8".into(),
            },
            RawRecord {
                id: "outside".into(),
                scope_id: "g2".into(),
                source_type: "system_trace".into(),
                source_path: "trace".into(),
                ts_ns: Some(25),
                payload: "effect".into(),
                encoding: "utf8".into(),
            },
        ];
        let result = action_effects(
            &test_store(
                vec![action],
                BTreeMap::new(),
                records,
                vec!["candidate".into(), "outside".into()],
            ),
            "a1",
        );
        assert_eq!(result["unknown_candidates"].as_array().unwrap().len(), 1);
        assert_eq!(result["unknown_candidates"][0]["raw_id"], "candidate");
    }

    #[test]
    fn store_reference_validation_covers_actions_boundaries_and_unique_ids() {
        let record = RawRecord {
            id: "r1".into(),
            scope_id: "g2".into(),
            source_type: "agent_native".into(),
            source_path: "session.jsonl".into(),
            ts_ns: Some(1),
            payload: "{}".into(),
            encoding: "utf8".into(),
        };
        let action = Action {
            id: "a1".into(),
            ts_ns: 1,
            end_ns: 2,
            scope_id: "g2".into(),
            kind: "write".into(),
            status: "ok".into(),
            closure: "observed".into(),
            raw_ids: vec!["r1".into()],
            effects: vec![],
        };
        let boundary = BoundaryEntry {
            entry: ManifestEntry {
                path: "result.json".into(),
                kind: "file".into(),
                mode: None,
                mtime_ns: None,
                sha256: Some("hash".into()),
                size: Some(2),
                target: None,
            },
            evidence_id: "r1".into(),
        };
        let boundaries = BTreeMap::from([("target".into(), vec![boundary.clone()])]);
        assert!(
            validate_store_references(
                std::slice::from_ref(&record),
                std::slice::from_ref(&action),
                &boundaries,
            )
            .is_ok()
        );

        let duplicate_records = vec![record.clone(), record];
        assert!(
            validate_store_references(
                &duplicate_records,
                std::slice::from_ref(&action),
                &boundaries
            )
            .unwrap_err()
            .to_string()
            .contains("duplicate Raw IDs")
        );

        let missing_boundary = BTreeMap::from([(
            "target".into(),
            vec![BoundaryEntry {
                evidence_id: "missing".into(),
                ..boundary
            }],
        )]);
        assert!(
            validate_store_references(&[], &[], &missing_boundary)
                .unwrap_err()
                .to_string()
                .contains("cites missing Raw ID")
        );
    }

    fn shell_action() -> Action {
        Action {
            id: "source-call".into(),
            ts_ns: 100,
            end_ns: 300,
            scope_id: "g2".into(),
            kind: "exec".into(),
            status: "ok".into(),
            closure: "unknown".into(),
            raw_ids: vec![],
            effects: vec![],
        }
    }

    fn complete_trace_model() -> TraceModel {
        TraceModel {
            execs: vec![TraceExec {
                pid: 10,
                ts_ns: 150,
                argv: vec!["/usr/bin/bash".into(), "-c".into(), "rg x".into()],
                cwd: PathBuf::from("/workspace"),
            }],
            children: HashMap::from([(10, vec![(11, 160)])]),
            exits: HashMap::from([(10, 250), (11, 240)]),
            effects: vec![(
                11,
                200,
                Effect {
                    operation: "read".into(),
                    path: "src/lib.rs".into(),
                    previous_path: None,
                    evidence_ids: vec!["r1".into()],
                },
            )],
        }
    }

    #[test]
    fn pid_namespace_decode_and_clone_time_define_the_real_subtree() {
        assert_eq!(
            traced_child_pid("2 /* 1673553 in strace's PID NS */"),
            Some(1_673_553)
        );
        assert_eq!(traced_child_pid("1673552"), Some(1_673_552));
        let children = HashMap::from([(10, vec![(9, 140), (11, 160)])]);
        assert_eq!(process_subtree(10, 150, &children), HashSet::from([10, 11]));
    }

    #[test]
    fn complete_unique_process_subtree_owns_descendant_effects() {
        let effects = owned_process_effects(
            &shell_action(),
            "rg x",
            "/workspace",
            &[(100, 300)],
            &complete_trace_model(),
        )
        .expect("owned subtree");
        assert_eq!(effects.len(), 1);
        assert_eq!(effects[0].evidence_ids, ["r1"]);
    }

    #[test]
    fn missing_exit_detached_child_and_overlapping_call_stay_unknown() {
        let mut missing = complete_trace_model();
        missing.exits.remove(&11);
        assert!(
            owned_process_effects(
                &shell_action(),
                "rg x",
                "/workspace",
                &[(100, 300)],
                &missing
            )
            .is_none()
        );

        let mut detached = complete_trace_model();
        detached.exits.insert(11, 301);
        assert!(
            owned_process_effects(
                &shell_action(),
                "rg x",
                "/workspace",
                &[(100, 300)],
                &detached
            )
            .is_none()
        );

        assert!(
            owned_process_effects(
                &shell_action(),
                "rg x",
                "/workspace",
                &[(100, 300), (140, 170)],
                &complete_trace_model()
            )
            .is_none()
        );
    }

    #[test]
    fn wrong_command_or_cwd_never_gets_temporal_ownership() {
        assert!(
            owned_process_effects(
                &shell_action(),
                "rg y",
                "/workspace",
                &[(100, 300)],
                &complete_trace_model()
            )
            .is_none()
        );
        assert!(
            owned_process_effects(
                &shell_action(),
                "rg x",
                "/other",
                &[(100, 300)],
                &complete_trace_model()
            )
            .is_none()
        );
    }
}
