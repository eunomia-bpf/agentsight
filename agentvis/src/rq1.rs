// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! RQ1 row export for the longitudinal Agent Nebula study.
//!
//! This is a thin, research-only analysis over [`RepositoryTrace`]. It writes
//! ordinary source-linked JSON and CSV; it is not another production event IR.

use crate::repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
    git_lines, repository_root, worktree_id, worktree_roots,
};
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{self, BufWriter, Write};
use std::path::{Path, PathBuf};

type DynError = Box<dyn std::error::Error + Send + Sync>;

#[derive(Debug, Clone, Serialize)]
struct ProjectCoverage {
    project: String,
    repository_root: String,
    revision: String,
    worktrees: usize,
    candidate_sessions: usize,
    parsed_sessions: usize,
    included_sessions: usize,
    attributed_sessions: usize,
    included_sessions_without_worktree: usize,
    excluded_unparsed: usize,
    excluded_without_timed_tools: usize,
    source_events: usize,
    tool_actions: usize,
    attributed_tool_actions: usize,
    file_actions: usize,
    observation_start_ms: i64,
    observation_end_ms: i64,
    observation_span_ms: i64,
    cutoff_ms: i64,
    candidate_sessions_by_vendor: BTreeMap<String, usize>,
    parsed_sessions_by_vendor: BTreeMap<String, usize>,
    included_sessions_by_vendor: BTreeMap<String, usize>,
    actions_by_vendor_effect_status: BTreeMap<String, usize>,
    file_actions_by_worktree: BTreeMap<String, usize>,
    actions_without_worktree: usize,
    final_state_worktrees_available: usize,
    final_state_worktrees_unavailable: usize,
    qualified_longitudinal: bool,
    qualified_validation: bool,
}

#[derive(Debug, Clone)]
struct ArtifactState {
    id: String,
    worktree_id: String,
    birth_state: String,
    lineage_state: String,
    first_path: String,
    last_path: String,
    first_event_index: usize,
    last_event_index: usize,
    first_ts_ms: i64,
    last_ts_ms: i64,
    first_session: String,
    last_session: String,
    sessions: BTreeSet<String>,
    reads: usize,
    mutations: usize,
    renames: usize,
    deletes: usize,
    closed_reason: String,
    current_path: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct ArtifactRow {
    project: String,
    artifact_id: String,
    worktree_id: String,
    birth_state: String,
    lineage_state: String,
    first_path: String,
    final_path: String,
    first_event_index: usize,
    last_event_index: usize,
    first_ts_ms: i64,
    last_ts_ms: i64,
    first_session: String,
    last_session: String,
    session_count: usize,
    reads: usize,
    mutations: usize,
    renames: usize,
    deletes: usize,
    closed_reason: String,
    final_exists: bool,
    final_tracked: bool,
    final_state_known: bool,
    introduced_eligible: bool,
    content_durability: String,
}

#[derive(Debug, Clone)]
struct AccessRecord {
    event_index: usize,
    ts_ms: i64,
    session_id: String,
    operation: String,
}

#[derive(Debug, Clone)]
struct MutationTemp {
    project: String,
    event_id: String,
    source_call_id: String,
    session_id: String,
    vendor: String,
    event_index: usize,
    ts_ms: i64,
    artifact_index: usize,
    artifact_id: String,
    worktree_id: String,
    path: String,
    operation: String,
    birth_create: bool,
    history_index: usize,
}

#[derive(Debug, Clone, Serialize)]
struct MutationRow {
    project: String,
    event_id: String,
    source_call_id: String,
    session_id: String,
    vendor: String,
    event_index: usize,
    ts_ms: i64,
    artifact_id: String,
    worktree_id: String,
    path: String,
    operation: String,
    birth_create: bool,
    final_path: String,
    final_exists: bool,
    final_tracked: bool,
    final_state_known: bool,
    content_durability: String,
    reuse_outcome: String,
    reuse_duration_events: usize,
    reuse_duration_ms: i64,
    reuse_event_index: String,
    reuse_cross_session: bool,
    validation_outcome: String,
    validation_duration_events: usize,
    validation_duration_ms: i64,
    validation_event_index: String,
    global_validation_event_index: String,
    global_validation_duration_events: String,
    conjunction_observed: bool,
}

#[derive(Debug, Clone, Serialize)]
struct SummaryRow {
    project: String,
    revision: String,
    candidate_sessions: usize,
    parsed_sessions: usize,
    included_sessions: usize,
    attributed_sessions: usize,
    worktrees: usize,
    observation_span_ms: i64,
    cutoff_ms: i64,
    source_events: usize,
    tool_actions: usize,
    attributed_tool_actions: usize,
    file_actions: usize,
    confirmed_mutations: usize,
    recognized_successful_validations: usize,
    introduced_eligible: usize,
    introduced_persisted: usize,
    introduced_unknown_final: usize,
    reuse_eligible: usize,
    reuse_observed: usize,
    reuse_competing: usize,
    reuse_censored: usize,
    validation_eligible: usize,
    validation_observed: usize,
    validation_competing: usize,
    validation_censored: usize,
    conjunction_eligible: usize,
    conjunction_observed: usize,
    qualified_longitudinal: bool,
    qualified_validation: bool,
}

#[derive(Debug)]
struct FinalState {
    roots: HashMap<String, PathBuf>,
    tracked: HashMap<String, HashSet<String>>,
    unavailable: HashSet<String>,
}

pub fn run_rq1_from_args<I, T>(args: I) -> Result<(), DynError>
where
    I: IntoIterator<Item = T>,
    T: Into<OsString>,
{
    let args = args.into_iter().map(Into::into).collect::<Vec<_>>();
    let mut output = None;
    let mut cutoff_ms = None;
    let mut repositories = Vec::new();
    let mut index = 0;
    while index < args.len() {
        if args[index] == "--output" || args[index] == "-o" {
            index += 1;
            output = args.get(index).map(PathBuf::from);
        } else if args[index] == "--cutoff-ms" {
            index += 1;
            cutoff_ms = args
                .get(index)
                .and_then(|value| value.to_string_lossy().parse::<i64>().ok());
        } else {
            repositories.push(PathBuf::from(&args[index]));
        }
        index += 1;
    }
    let output = output.ok_or("research-rq1 requires --output <raw-directory>")?;
    if repositories.is_empty() {
        return Err("research-rq1 requires at least one repository root".into());
    }
    let cutoff_ms = cutoff_ms.ok_or("research-rq1 requires --cutoff-ms <epoch-ms>")?;
    run_rq1(&output, &repositories, cutoff_ms)
}

fn run_rq1(output: &Path, repositories: &[PathBuf], cutoff_ms: i64) -> Result<(), DynError> {
    fs::create_dir_all(output.join("events"))?;
    let mut coverages = Vec::new();
    let mut artifact_rows = Vec::new();
    let mut mutation_rows = Vec::new();
    let mut summaries = Vec::new();

    for repository in repositories {
        eprintln!("[rq1] extracting {}", repository.display());
        let trace = build_repository_trace(&RepositoryTraceOptions {
            repo: repository.clone(),
            global: false,
            end_ms: Some(cutoff_ms),
        })?;
        let root = repository_root(repository)?;
        let project = safe_name(&trace.repository);
        write_json(
            output.join("events").join(format!("{project}.json")),
            &trace,
        )?;
        let final_state = load_final_state(&root)?;
        let (coverage, artifacts, mutations, summary) =
            analyze_project(&root, &trace, &final_state, cutoff_ms);
        coverages.push(coverage);
        artifact_rows.extend(artifacts);
        mutation_rows.extend(mutations);
        summaries.push(summary);
    }

    write_json(output.join("projects.json"), &coverages)?;
    write_artifacts(output.join("rq1-artifacts.csv"), &artifact_rows)?;
    write_mutations(output.join("rq1-mutations.csv"), &mutation_rows)?;
    write_summaries(output.join("rq1-summary.csv"), &summaries)?;
    write_result(
        output.parent().unwrap_or(output).join("result.md"),
        &coverages,
        &summaries,
    )?;
    eprintln!(
        "[rq1] complete: {} projects, {} artifacts, {} confirmed mutations -> {}",
        summaries.len(),
        artifact_rows.len(),
        mutation_rows.len(),
        output.display()
    );
    Ok(())
}

fn analyze_project(
    root: &Path,
    trace: &RepositoryTrace,
    final_state: &FinalState,
    cutoff_ms: i64,
) -> (
    ProjectCoverage,
    Vec<ArtifactRow>,
    Vec<MutationRow>,
    SummaryRow,
) {
    let project = trace.repository.clone();
    let mut artifacts = Vec::<ArtifactState>::new();
    let mut live = HashMap::<(String, String), usize>::new();
    let mut histories = Vec::<Vec<AccessRecord>>::new();
    let mut mutations = Vec::<MutationTemp>::new();
    let mut validations = Vec::<(usize, i64, String, String)>::new();
    let mut cross = BTreeMap::<String, usize>::new();
    let mut actions_by_worktree = BTreeMap::<String, usize>::new();

    for (event_index, event) in trace.events.iter().enumerate() {
        *cross
            .entry(format!(
                "{}|{}|{}",
                event.vendor, event.effect, event.status
            ))
            .or_default() += 1;
        if event.effect == "test"
            && event.status == "ok"
            && let Some(worktree_id) = &event.worktree_id
        {
            validations.push((
                event_index,
                event.ts_ms,
                event.session_id.clone(),
                worktree_id.clone(),
            ));
        }
        for action in event.actions.iter().filter(|action| !action.scope) {
            *actions_by_worktree
                .entry(action.worktree_id.clone())
                .or_default() += 1;
            // RepositoryEvent records attempted references. Artifact
            // lifecycles and reuse/validation estimands admit confirmed
            // effects only.
            if event.status != "ok" {
                continue;
            }
            let artifact_index = apply_action(
                &project,
                event,
                event_index,
                action,
                &mut artifacts,
                &mut histories,
                &mut live,
            );
            let history_index = histories[artifact_index].len();
            histories[artifact_index].push(AccessRecord {
                event_index,
                ts_ms: event.ts_ms,
                session_id: event.session_id.clone(),
                operation: action.access.clone(),
            });
            update_artifact(&mut artifacts[artifact_index], event, event_index, action);
            if is_mutation(&action.access) {
                mutations.push(MutationTemp {
                    project: project.clone(),
                    event_id: event.id.clone(),
                    source_call_id: event.source_call_id.clone().unwrap_or_default(),
                    session_id: event.session_id.clone(),
                    vendor: event.vendor.clone(),
                    event_index,
                    ts_ms: event.ts_ms,
                    artifact_index,
                    artifact_id: artifacts[artifact_index].id.clone(),
                    worktree_id: action.worktree_id.clone(),
                    path: action.path.clone(),
                    operation: action.access.clone(),
                    birth_create: artifacts[artifact_index].birth_state == "confirmed_create"
                        && artifacts[artifact_index].first_event_index == event_index
                        && action.access == "create",
                    history_index,
                });
            }
        }
    }

    let artifact_rows = artifacts
        .iter()
        .map(|artifact| artifact_row(&project, artifact, final_state))
        .collect::<Vec<_>>();
    let artifact_final = artifact_rows
        .iter()
        .map(|row| (row.artifact_id.clone(), row.clone()))
        .collect::<HashMap<_, _>>();
    let mutation_rows = mutations
        .iter()
        .map(|mutation| {
            mutation_row(
                mutation,
                &histories[mutation.artifact_index],
                &validations,
                trace.events.len(),
                trace.end_ms,
                artifact_final
                    .get(&mutation.artifact_id)
                    .expect("artifact row exists"),
            )
        })
        .collect::<Vec<_>>();
    let recognized_validations = validations.len();
    let attributed_sessions = trace
        .events
        .iter()
        .filter(|event| event.worktree_id.is_some())
        .map(|event| &event.session_id)
        .collect::<HashSet<_>>()
        .len();
    let attributed_tool_actions = trace
        .events
        .iter()
        .filter(|event| event.worktree_id.is_some())
        .count();
    let qualified_longitudinal = attributed_sessions >= 2 && !mutation_rows.is_empty();
    let qualified_validation = qualified_longitudinal && recognized_validations > 0;
    let coverage = ProjectCoverage {
        project: project.clone(),
        repository_root: root.display().to_string(),
        revision: trace.revision.clone(),
        worktrees: trace.worktree_count,
        candidate_sessions: trace.candidate_session_count,
        parsed_sessions: trace.parsed_session_count,
        included_sessions: trace.session_count,
        attributed_sessions,
        included_sessions_without_worktree: trace.session_count.saturating_sub(attributed_sessions),
        excluded_unparsed: trace
            .candidate_session_count
            .saturating_sub(trace.parsed_session_count),
        excluded_without_timed_tools: trace
            .parsed_session_count
            .saturating_sub(trace.session_count),
        source_events: trace.source_event_count,
        tool_actions: trace.events.len(),
        attributed_tool_actions,
        file_actions: trace.file_action_count,
        observation_start_ms: trace.start_ms,
        observation_end_ms: trace.end_ms,
        observation_span_ms: trace.end_ms.saturating_sub(trace.start_ms),
        cutoff_ms,
        candidate_sessions_by_vendor: trace.candidate_sessions_by_vendor.clone(),
        parsed_sessions_by_vendor: trace.parsed_sessions_by_vendor.clone(),
        included_sessions_by_vendor: trace.included_sessions_by_vendor.clone(),
        actions_by_vendor_effect_status: cross,
        file_actions_by_worktree: actions_by_worktree,
        actions_without_worktree: trace
            .events
            .iter()
            .filter(|event| event.worktree_id.is_none())
            .count(),
        final_state_worktrees_available: final_state.roots.len(),
        final_state_worktrees_unavailable: final_state.unavailable.len(),
        qualified_longitudinal,
        qualified_validation,
    };
    let summary = summarize(
        trace,
        &artifact_rows,
        &mutation_rows,
        recognized_validations,
        attributed_sessions,
        attributed_tool_actions,
        cutoff_ms,
        qualified_longitudinal,
        qualified_validation,
    );
    (coverage, artifact_rows, mutation_rows, summary)
}

fn apply_action(
    project: &str,
    event: &RepositoryEvent,
    event_index: usize,
    action: &FileAction,
    artifacts: &mut Vec<ArtifactState>,
    histories: &mut Vec<Vec<AccessRecord>>,
    live: &mut HashMap<(String, String), usize>,
) -> usize {
    let key = (action.worktree_id.clone(), action.path.clone());
    if action.access == "rename" {
        if let Some(replaced) = live.remove(&key) {
            artifacts[replaced].closed_reason = "replaced_by_rename".into();
            artifacts[replaced].current_path = None;
        }
        let source = action
            .previous_path
            .as_ref()
            .zip(action.previous_worktree_id.as_ref())
            .filter(|(_, worktree)| *worktree == &action.worktree_id)
            .and_then(|(path, worktree)| live.remove(&(worktree.clone(), path.clone())));
        if let Some(index) = source {
            artifacts[index].last_path = action.path.clone();
            artifacts[index].current_path = Some(action.path.clone());
            live.insert(key, index);
            return index;
        }
        let index = new_artifact(
            project,
            event,
            event_index,
            action,
            "unknown_rename_source",
            "unknown",
            artifacts,
            histories,
        );
        live.insert(key, index);
        return index;
    }

    let index = live.get(&key).copied().unwrap_or_else(|| {
        let birth = if action.access == "create" {
            "confirmed_create"
        } else {
            "left_censored_existing"
        };
        let index = new_artifact(
            project,
            event,
            event_index,
            action,
            birth,
            "known",
            artifacts,
            histories,
        );
        live.insert(key.clone(), index);
        index
    });
    if action.access == "delete" {
        live.remove(&key);
        artifacts[index].current_path = None;
        artifacts[index].closed_reason = "confirmed_delete".into();
    }
    index
}

#[allow(clippy::too_many_arguments)]
fn new_artifact(
    project: &str,
    event: &RepositoryEvent,
    event_index: usize,
    action: &FileAction,
    birth_state: &str,
    lineage_state: &str,
    artifacts: &mut Vec<ArtifactState>,
    histories: &mut Vec<Vec<AccessRecord>>,
) -> usize {
    let index = artifacts.len();
    let id = format!("{}:a{:08}", safe_name(project), index + 1);
    artifacts.push(ArtifactState {
        id,
        worktree_id: action.worktree_id.clone(),
        birth_state: birth_state.into(),
        lineage_state: lineage_state.into(),
        first_path: action.path.clone(),
        last_path: action.path.clone(),
        first_event_index: event_index,
        last_event_index: event_index,
        first_ts_ms: event.ts_ms,
        last_ts_ms: event.ts_ms,
        first_session: event.session_id.clone(),
        last_session: event.session_id.clone(),
        sessions: BTreeSet::from([event.session_id.clone()]),
        reads: 0,
        mutations: 0,
        renames: 0,
        deletes: 0,
        closed_reason: String::new(),
        current_path: Some(action.path.clone()),
    });
    histories.push(Vec::new());
    index
}

fn update_artifact(
    artifact: &mut ArtifactState,
    event: &RepositoryEvent,
    event_index: usize,
    action: &FileAction,
) {
    artifact.last_event_index = event_index;
    artifact.last_ts_ms = event.ts_ms;
    artifact.last_session = event.session_id.clone();
    artifact.sessions.insert(event.session_id.clone());
    if action.access == "read" {
        artifact.reads += 1;
    }
    artifact.mutations += usize::from(is_mutation(&action.access));
    artifact.renames += usize::from(action.access == "rename");
    artifact.deletes += usize::from(action.access == "delete");
}

fn artifact_row(project: &str, artifact: &ArtifactState, state: &FinalState) -> ArtifactRow {
    let final_path = artifact.current_path.clone().unwrap_or_default();
    let root = state.roots.get(&artifact.worktree_id);
    let final_state_known = root.is_some();
    let final_exists = root
        .filter(|_| !final_path.is_empty())
        .is_some_and(|root| root.join(&final_path).exists());
    let final_tracked = state
        .tracked
        .get(&artifact.worktree_id)
        .is_some_and(|paths| paths.contains(&final_path));
    let introduced_eligible = artifact.birth_state == "confirmed_create";
    ArtifactRow {
        project: project.into(),
        artifact_id: artifact.id.clone(),
        worktree_id: artifact.worktree_id.clone(),
        birth_state: artifact.birth_state.clone(),
        lineage_state: artifact.lineage_state.clone(),
        first_path: artifact.first_path.clone(),
        final_path,
        first_event_index: artifact.first_event_index,
        last_event_index: artifact.last_event_index,
        first_ts_ms: artifact.first_ts_ms,
        last_ts_ms: artifact.last_ts_ms,
        first_session: artifact.first_session.clone(),
        last_session: artifact.last_session.clone(),
        session_count: artifact.sessions.len(),
        reads: artifact.reads,
        mutations: artifact.mutations,
        renames: artifact.renames,
        deletes: artifact.deletes,
        closed_reason: artifact.closed_reason.clone(),
        final_exists,
        final_tracked,
        final_state_known,
        introduced_eligible,
        content_durability: if introduced_eligible {
            "not_measured_for_create".into()
        } else {
            "unknown".into()
        },
    }
}

fn mutation_row(
    mutation: &MutationTemp,
    history: &[AccessRecord],
    validations: &[(usize, i64, String, String)],
    event_count: usize,
    end_ms: i64,
    artifact: &ArtifactRow,
) -> MutationRow {
    let later = history.iter().skip(mutation.history_index + 1).next();
    let (reuse_outcome, reuse_index, reuse_ts, reuse_cross_session) = match later {
        Some(row) if row.operation == "delete" => {
            ("competing_delete", Some(row.event_index), row.ts_ms, false)
        }
        Some(row) => (
            "observed_reuse",
            Some(row.event_index),
            row.ts_ms,
            row.session_id != mutation.session_id,
        ),
        None => ("censored_end", None, end_ms, false),
    };

    let supersede = history
        .iter()
        .skip(mutation.history_index + 1)
        .find(|row| is_mutation(&row.operation));
    let next_validation = validations.iter().find(|(index, _, _, worktree)| {
        *index > mutation.event_index && worktree == &mutation.worktree_id
    });
    let (validation_outcome, validation_index, validation_ts) = match (next_validation, supersede) {
        (Some(validation), Some(next)) if validation.0 < next.event_index => {
            ("observed_validation", Some(validation.0), validation.1)
        }
        (_, Some(next)) => ("competing_supersede", Some(next.event_index), next.ts_ms),
        (Some(validation), None) => ("observed_validation", Some(validation.0), validation.1),
        (None, None) => ("censored_end", None, end_ms),
    };
    let global_validation = validations.iter().find(|(index, _, _, worktree)| {
        *index > mutation.event_index && worktree == &mutation.worktree_id
    });
    let reuse_duration_events = duration_events(mutation.event_index, reuse_index, event_count);
    let validation_duration_events =
        duration_events(mutation.event_index, validation_index, event_count);
    let conjunction_observed = mutation.birth_create
        && artifact.final_state_known
        && artifact.final_exists
        && reuse_outcome == "observed_reuse"
        && validation_outcome == "observed_validation";
    MutationRow {
        project: mutation.project.clone(),
        event_id: mutation.event_id.clone(),
        source_call_id: mutation.source_call_id.clone(),
        session_id: mutation.session_id.clone(),
        vendor: mutation.vendor.clone(),
        event_index: mutation.event_index,
        ts_ms: mutation.ts_ms,
        artifact_id: mutation.artifact_id.clone(),
        worktree_id: mutation.worktree_id.clone(),
        path: mutation.path.clone(),
        operation: mutation.operation.clone(),
        birth_create: mutation.birth_create,
        final_path: artifact.final_path.clone(),
        final_exists: artifact.final_exists,
        final_tracked: artifact.final_tracked,
        final_state_known: artifact.final_state_known,
        content_durability: if mutation.birth_create {
            "not_measured_for_create".into()
        } else {
            "unknown".into()
        },
        reuse_outcome: reuse_outcome.into(),
        reuse_duration_events,
        reuse_duration_ms: reuse_ts.saturating_sub(mutation.ts_ms).max(0),
        reuse_event_index: reuse_index.map_or_else(String::new, |value| value.to_string()),
        reuse_cross_session,
        validation_outcome: validation_outcome.into(),
        validation_duration_events,
        validation_duration_ms: validation_ts.saturating_sub(mutation.ts_ms).max(0),
        validation_event_index: validation_index
            .map_or_else(String::new, |value| value.to_string()),
        global_validation_event_index: global_validation
            .map_or_else(String::new, |value| value.0.to_string()),
        global_validation_duration_events: global_validation.map_or_else(String::new, |value| {
            value
                .0
                .saturating_sub(mutation.event_index)
                .max(1)
                .to_string()
        }),
        conjunction_observed,
    }
}

fn duration_events(start: usize, endpoint: Option<usize>, event_count: usize) -> usize {
    endpoint
        .unwrap_or(event_count.saturating_sub(1))
        .saturating_sub(start)
        .max(1)
}

fn summarize(
    trace: &RepositoryTrace,
    artifacts: &[ArtifactRow],
    mutations: &[MutationRow],
    validations: usize,
    attributed_sessions: usize,
    attributed_tool_actions: usize,
    cutoff_ms: i64,
    qualified_longitudinal: bool,
    qualified_validation: bool,
) -> SummaryRow {
    let introductions_all = artifacts
        .iter()
        .filter(|row| row.introduced_eligible)
        .collect::<Vec<_>>();
    let introductions = introductions_all
        .iter()
        .copied()
        .filter(|row| row.final_state_known)
        .collect::<Vec<_>>();
    let non_delete = mutations
        .iter()
        .filter(|row| row.operation != "delete")
        .collect::<Vec<_>>();
    let conjunction = mutations
        .iter()
        .filter(|row| row.birth_create && row.final_state_known);
    let conjunction_eligible = conjunction.clone().count();
    let conjunction_observed = conjunction.filter(|row| row.conjunction_observed).count();
    SummaryRow {
        project: trace.repository.clone(),
        revision: trace.revision.clone(),
        candidate_sessions: trace.candidate_session_count,
        parsed_sessions: trace.parsed_session_count,
        included_sessions: trace.session_count,
        attributed_sessions,
        worktrees: trace.worktree_count,
        observation_span_ms: trace.end_ms.saturating_sub(trace.start_ms),
        cutoff_ms,
        source_events: trace.source_event_count,
        tool_actions: trace.events.len(),
        attributed_tool_actions,
        file_actions: trace.file_action_count,
        confirmed_mutations: mutations.len(),
        recognized_successful_validations: validations,
        introduced_eligible: introductions.len(),
        introduced_persisted: introductions.iter().filter(|row| row.final_exists).count(),
        introduced_unknown_final: introductions_all
            .iter()
            .filter(|row| !row.final_state_known)
            .count(),
        reuse_eligible: non_delete.len(),
        reuse_observed: non_delete
            .iter()
            .filter(|row| row.reuse_outcome == "observed_reuse")
            .count(),
        reuse_competing: non_delete
            .iter()
            .filter(|row| row.reuse_outcome.starts_with("competing"))
            .count(),
        reuse_censored: non_delete
            .iter()
            .filter(|row| row.reuse_outcome == "censored_end")
            .count(),
        validation_eligible: non_delete.len(),
        validation_observed: non_delete
            .iter()
            .filter(|row| row.validation_outcome == "observed_validation")
            .count(),
        validation_competing: non_delete
            .iter()
            .filter(|row| row.validation_outcome == "competing_supersede")
            .count(),
        validation_censored: non_delete
            .iter()
            .filter(|row| row.validation_outcome == "censored_end")
            .count(),
        conjunction_eligible,
        conjunction_observed,
        qualified_longitudinal,
        qualified_validation,
    }
}

fn load_final_state(root: &Path) -> io::Result<FinalState> {
    let mut roots = HashMap::new();
    let mut tracked = HashMap::new();
    let mut unavailable = HashSet::new();
    for worktree in worktree_roots(root) {
        let id = worktree_id(&worktree);
        let Ok(files) = git_lines(&worktree, &["ls-files"]) else {
            unavailable.insert(id);
            continue;
        };
        let files = files.into_iter().collect::<HashSet<_>>();
        roots.insert(id.clone(), worktree);
        tracked.insert(id, files);
    }
    Ok(FinalState {
        roots,
        tracked,
        unavailable,
    })
}

fn is_mutation(operation: &str) -> bool {
    matches!(operation, "create" | "write" | "rename" | "delete")
}

fn safe_name(value: &str) -> String {
    value
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() || matches!(character, '-' | '_') {
                character
            } else {
                '-'
            }
        })
        .collect()
}

fn write_json(path: PathBuf, value: &impl Serialize) -> io::Result<()> {
    let mut writer = BufWriter::new(File::create(path)?);
    serde_json::to_writer_pretty(&mut writer, value).map_err(io::Error::other)?;
    writer.write_all(b"\n")
}

fn csv(value: impl ToString) -> String {
    let value = value.to_string();
    if value.contains([',', '"', '\n', '\r']) {
        format!("\"{}\"", value.replace('"', "\"\""))
    } else {
        value
    }
}

fn write_csv(path: PathBuf, header: &[&str], rows: Vec<Vec<String>>) -> io::Result<()> {
    let mut writer = BufWriter::new(File::create(path)?);
    writeln!(writer, "{}", header.join(","))?;
    for row in rows {
        writeln!(
            writer,
            "{}",
            row.into_iter().map(csv).collect::<Vec<_>>().join(",")
        )?;
    }
    Ok(())
}

fn write_artifacts(path: PathBuf, rows: &[ArtifactRow]) -> io::Result<()> {
    let header = [
        "project",
        "artifact_id",
        "worktree_id",
        "birth_state",
        "lineage_state",
        "first_path",
        "final_path",
        "first_event_index",
        "last_event_index",
        "first_ts_ms",
        "last_ts_ms",
        "first_session",
        "last_session",
        "session_count",
        "reads",
        "mutations",
        "renames",
        "deletes",
        "closed_reason",
        "final_exists",
        "final_tracked",
        "final_state_known",
        "introduced_eligible",
        "content_durability",
    ];
    write_csv(
        path,
        &header,
        rows.iter()
            .map(|row| {
                vec![
                    row.project.clone(),
                    row.artifact_id.clone(),
                    row.worktree_id.clone(),
                    row.birth_state.clone(),
                    row.lineage_state.clone(),
                    row.first_path.clone(),
                    row.final_path.clone(),
                    row.first_event_index.to_string(),
                    row.last_event_index.to_string(),
                    row.first_ts_ms.to_string(),
                    row.last_ts_ms.to_string(),
                    row.first_session.clone(),
                    row.last_session.clone(),
                    row.session_count.to_string(),
                    row.reads.to_string(),
                    row.mutations.to_string(),
                    row.renames.to_string(),
                    row.deletes.to_string(),
                    row.closed_reason.clone(),
                    row.final_exists.to_string(),
                    row.final_tracked.to_string(),
                    row.final_state_known.to_string(),
                    row.introduced_eligible.to_string(),
                    row.content_durability.clone(),
                ]
            })
            .collect(),
    )
}

fn write_mutations(path: PathBuf, rows: &[MutationRow]) -> io::Result<()> {
    let header = [
        "project",
        "event_id",
        "source_call_id",
        "session_id",
        "vendor",
        "event_index",
        "ts_ms",
        "artifact_id",
        "worktree_id",
        "path",
        "operation",
        "birth_create",
        "final_path",
        "final_exists",
        "final_tracked",
        "final_state_known",
        "content_durability",
        "reuse_outcome",
        "reuse_duration_events",
        "reuse_duration_ms",
        "reuse_event_index",
        "reuse_cross_session",
        "validation_outcome",
        "validation_duration_events",
        "validation_duration_ms",
        "validation_event_index",
        "global_validation_event_index",
        "global_validation_duration_events",
        "conjunction_observed",
    ];
    write_csv(
        path,
        &header,
        rows.iter()
            .map(|row| {
                vec![
                    row.project.clone(),
                    row.event_id.clone(),
                    row.source_call_id.clone(),
                    row.session_id.clone(),
                    row.vendor.clone(),
                    row.event_index.to_string(),
                    row.ts_ms.to_string(),
                    row.artifact_id.clone(),
                    row.worktree_id.clone(),
                    row.path.clone(),
                    row.operation.clone(),
                    row.birth_create.to_string(),
                    row.final_path.clone(),
                    row.final_exists.to_string(),
                    row.final_tracked.to_string(),
                    row.final_state_known.to_string(),
                    row.content_durability.clone(),
                    row.reuse_outcome.clone(),
                    row.reuse_duration_events.to_string(),
                    row.reuse_duration_ms.to_string(),
                    row.reuse_event_index.clone(),
                    row.reuse_cross_session.to_string(),
                    row.validation_outcome.clone(),
                    row.validation_duration_events.to_string(),
                    row.validation_duration_ms.to_string(),
                    row.validation_event_index.clone(),
                    row.global_validation_event_index.clone(),
                    row.global_validation_duration_events.clone(),
                    row.conjunction_observed.to_string(),
                ]
            })
            .collect(),
    )
}

fn write_summaries(path: PathBuf, rows: &[SummaryRow]) -> io::Result<()> {
    let header = [
        "project",
        "revision",
        "candidate_sessions",
        "parsed_sessions",
        "included_sessions",
        "attributed_sessions",
        "worktrees",
        "observation_span_ms",
        "cutoff_ms",
        "source_events",
        "tool_actions",
        "attributed_tool_actions",
        "file_actions",
        "confirmed_mutations",
        "recognized_successful_validations",
        "introduced_eligible",
        "introduced_persisted",
        "introduced_unknown_final",
        "reuse_eligible",
        "reuse_observed",
        "reuse_competing",
        "reuse_censored",
        "validation_eligible",
        "validation_observed",
        "validation_competing",
        "validation_censored",
        "conjunction_eligible",
        "conjunction_observed",
        "qualified_longitudinal",
        "qualified_validation",
    ];
    write_csv(
        path,
        &header,
        rows.iter()
            .map(|row| {
                vec![
                    row.project.clone(),
                    row.revision.clone(),
                    row.candidate_sessions.to_string(),
                    row.parsed_sessions.to_string(),
                    row.included_sessions.to_string(),
                    row.attributed_sessions.to_string(),
                    row.worktrees.to_string(),
                    row.observation_span_ms.to_string(),
                    row.cutoff_ms.to_string(),
                    row.source_events.to_string(),
                    row.tool_actions.to_string(),
                    row.attributed_tool_actions.to_string(),
                    row.file_actions.to_string(),
                    row.confirmed_mutations.to_string(),
                    row.recognized_successful_validations.to_string(),
                    row.introduced_eligible.to_string(),
                    row.introduced_persisted.to_string(),
                    row.introduced_unknown_final.to_string(),
                    row.reuse_eligible.to_string(),
                    row.reuse_observed.to_string(),
                    row.reuse_competing.to_string(),
                    row.reuse_censored.to_string(),
                    row.validation_eligible.to_string(),
                    row.validation_observed.to_string(),
                    row.validation_competing.to_string(),
                    row.validation_censored.to_string(),
                    row.conjunction_eligible.to_string(),
                    row.conjunction_observed.to_string(),
                    row.qualified_longitudinal.to_string(),
                    row.qualified_validation.to_string(),
                ]
            })
            .collect(),
    )
}

fn write_result(
    path: PathBuf,
    coverages: &[ProjectCoverage],
    rows: &[SummaryRow],
) -> io::Result<()> {
    let mut writer = BufWriter::new(File::create(path)?);
    writeln!(writer, "# RQ1 Real-Run Summary\n")?;
    writeln!(
        writer,
        "Generated deterministically from source-linked native-session rows.\n"
    )?;
    writeln!(
        writer,
        "| Project | Attributed/all sessions | Attributed/all actions | Mutations | Creates kept | Reuse | Validation before supersession |"
    )?;
    writeln!(writer, "|---|---:|---:|---:|---:|---:|---:|")?;
    for row in rows {
        let creates = (row.introduced_eligible > 0)
            .then(|| format!("{}/{}", row.introduced_persisted, row.introduced_eligible))
            .unwrap_or_else(|| "N/A".into());
        let validation = row
            .qualified_validation
            .then(|| format!("{}/{}", row.validation_observed, row.validation_eligible))
            .unwrap_or_else(|| "N/A (coverage)".into());
        writeln!(
            writer,
            "| {} | {}/{} | {}/{} | {} | {} | {}/{} | {} |",
            row.project,
            row.attributed_sessions,
            row.included_sessions,
            row.attributed_tool_actions,
            row.tool_actions,
            row.confirmed_mutations,
            creates,
            row.reuse_observed,
            row.reuse_eligible,
            validation,
        )?;
    }
    let qualified = rows.iter().filter(|row| row.qualified_longitudinal).count();
    let persistence = rows
        .iter()
        .filter(|row| row.introduced_eligible > 0)
        .count();
    let validation = rows.iter().filter(|row| row.qualified_validation).count();
    writeln!(
        writer,
        "\n- Longitudinal-qualified projects: {qualified}/{}",
        rows.len()
    )?;
    writeln!(
        writer,
        "- Persistence-qualified projects: {persistence}/{}",
        rows.len()
    )?;
    writeln!(
        writer,
        "- Validation-qualified projects: {validation}/{}",
        rows.len()
    )?;
    writeln!(writer, "- Coverage rows: {}", coverages.len())?;
    writeln!(
        writer,
        "- Existing-file write content durability: unknown by design."
    )?;
    writeln!(
        writer,
        "- Recognized validation: adapter-derived `effect=test,status=ok` only."
    )?;
    if persistence < 4 {
        writeln!(
            writer,
            "- Persistence is coverage-only: fewer than four cases have an eligible confirmed create."
        )?;
    }
    if validation < 4 {
        writeln!(
            writer,
            "- Validation is coverage-only: fewer than four cases expose recognized successful validation."
        )?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn event(index: usize, session: &str, status: &str, effect: &str) -> RepositoryEvent {
        RepositoryEvent {
            id: format!("e{index}"),
            source_call_id: Some(format!("call{index}")),
            native_session_id: session.into(),
            source_stream_id: session.into(),
            source_tool_ordinal: index,
            source_role: Some("root".into()),
            source_agent_id: None,
            session_id: session.into(),
            session_ordinal: 0,
            vendor: "codex".into(),
            ts_ms: index as i64 * 10,
            prompt_index: 0,
            source_event_id: None,
            parent_event_id: None,
            model: None,
            attribution_skill: None,
            attribution_agent: None,
            skill_name: None,
            skill_args: None,
            worktree_id: Some("w1".into()),
            tool_name: "tool".into(),
            category: "file".into(),
            command_name: "tool".into(),
            effect: effect.into(),
            status: status.into(),
            source_paths: Vec::new(),
            actions: Vec::new(),
        }
    }

    fn action(worktree: &str, path: &str, access: &str) -> FileAction {
        FileAction {
            worktree_id: worktree.into(),
            path: path.into(),
            access: access.into(),
            previous_path: None,
            previous_worktree_id: None,
            scope: false,
            action_ordinal: 0,
            artifact_id: String::new(),
        }
    }

    fn trace(events: Vec<RepositoryEvent>) -> RepositoryTrace {
        RepositoryTrace {
            repository: "p".into(),
            revision: "r".into(),
            start_ms: events.first().map_or(0, |event| event.ts_ms),
            end_ms: events.last().map_or(0, |event| event.ts_ms),
            global: false,
            worktree_count: 1,
            candidate_session_count: 1,
            parsed_session_count: 1,
            session_count: 1,
            candidate_sessions_by_vendor: BTreeMap::from([("codex".into(), 1)]),
            parsed_sessions_by_vendor: BTreeMap::from([("codex".into(), 1)]),
            included_sessions_by_vendor: BTreeMap::from([("codex".into(), 1)]),
            source_event_count: events.len(),
            file_action_count: events.iter().map(|event| event.actions.len()).sum(),
            events,
            commits_ms: Vec::new(),
        }
    }

    #[test]
    fn failed_and_observed_mutations_do_not_create_artifact_lifecycle() {
        let mut failed = event(0, "s1", "fail", "write");
        failed.actions.push(action("w1", "failed.rs", "create"));
        let mut observed = event(1, "s1", "observed", "write");
        observed.actions.push(action("w1", "observed.rs", "rename"));
        let trace = trace(vec![failed, observed]);
        let state = FinalState {
            roots: HashMap::new(),
            tracked: HashMap::new(),
            unavailable: HashSet::new(),
        };
        let (_, artifacts, mutations, _) =
            analyze_project(Path::new("/unused"), &trace, &state, trace.end_ms);
        assert!(artifacts.is_empty());
        assert!(mutations.is_empty());
    }

    #[test]
    fn confirmed_create_is_birth_but_left_censored_rename_is_not() {
        let mut artifacts = Vec::new();
        let mut histories = Vec::new();
        let mut live = HashMap::new();
        let first = event(0, "s1", "ok", "write");
        let source = action("w1", "old", "write");
        let old = apply_action(
            "p",
            &first,
            0,
            &source,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        let mut rename = action("w1", "new", "rename");
        rename.previous_path = Some("old".into());
        rename.previous_worktree_id = Some("w1".into());
        let moved = apply_action(
            "p",
            &event(1, "s1", "ok", "write"),
            1,
            &rename,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        assert_eq!(old, moved);
        assert_eq!(artifacts[moved].birth_state, "left_censored_existing");
        let create = action("w1", "born", "create");
        let born = apply_action(
            "p",
            &event(2, "s1", "ok", "write"),
            2,
            &create,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        assert_eq!(artifacts[born].birth_state, "confirmed_create");
    }

    #[test]
    fn cross_worktree_rename_does_not_transfer_artifact_identity() {
        let mut artifacts = Vec::new();
        let mut histories = Vec::new();
        let mut live = HashMap::new();
        let source = action("w1", "old", "create");
        let old = apply_action(
            "p",
            &event(0, "s1", "ok", "write"),
            0,
            &source,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        let mut rename = action("w2", "new", "rename");
        rename.previous_path = Some("old".into());
        rename.previous_worktree_id = Some("w1".into());
        let new = apply_action(
            "p",
            &event(1, "s1", "ok", "write"),
            1,
            &rename,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        assert_ne!(old, new);
        assert_eq!(artifacts[new].birth_state, "unknown_rename_source");
        assert!(live.contains_key(&("w1".into(), "old".into())));
        assert!(live.contains_key(&("w2".into(), "new".into())));
    }

    #[test]
    fn worktrees_and_delete_recreate_keep_distinct_identities() {
        let mut artifacts = Vec::new();
        let mut histories = Vec::new();
        let mut live = HashMap::new();
        let create1 = action("w1", "same", "create");
        let create2 = action("w2", "same", "create");
        let first = apply_action(
            "p",
            &event(0, "s1", "ok", "write"),
            0,
            &create1,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        let other = apply_action(
            "p",
            &event(1, "s1", "ok", "write"),
            1,
            &create2,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        assert_ne!(first, other);
        let deleted = action("w1", "same", "delete");
        apply_action(
            "p",
            &event(2, "s1", "ok", "write"),
            2,
            &deleted,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        let recreated = apply_action(
            "p",
            &event(3, "s2", "ok", "write"),
            3,
            &create1,
            &mut artifacts,
            &mut histories,
            &mut live,
        );
        assert_ne!(first, recreated);
    }

    #[test]
    fn validation_must_precede_superseding_mutation() {
        let artifact = ArtifactRow {
            project: "p".into(),
            artifact_id: "a".into(),
            worktree_id: "w".into(),
            birth_state: "left_censored_existing".into(),
            lineage_state: "known".into(),
            first_path: "f".into(),
            final_path: "f".into(),
            first_event_index: 0,
            last_event_index: 3,
            first_ts_ms: 0,
            last_ts_ms: 30,
            first_session: "s1".into(),
            last_session: "s2".into(),
            session_count: 2,
            reads: 0,
            mutations: 2,
            renames: 0,
            deletes: 0,
            closed_reason: String::new(),
            final_exists: true,
            final_tracked: true,
            final_state_known: true,
            introduced_eligible: false,
            content_durability: "unknown".into(),
        };
        let mutation = MutationTemp {
            project: "p".into(),
            event_id: "e0".into(),
            source_call_id: "c0".into(),
            session_id: "s1".into(),
            vendor: "codex".into(),
            event_index: 0,
            ts_ms: 0,
            artifact_index: 0,
            artifact_id: "a".into(),
            worktree_id: "w".into(),
            path: "f".into(),
            operation: "write".into(),
            birth_create: false,
            history_index: 0,
        };
        let history = vec![
            AccessRecord {
                event_index: 0,
                ts_ms: 0,
                session_id: "s1".into(),
                operation: "write".into(),
            },
            AccessRecord {
                event_index: 2,
                ts_ms: 20,
                session_id: "s2".into(),
                operation: "write".into(),
            },
        ];
        let row = mutation_row(
            &mutation,
            &history,
            &[
                (1, 10, "s1".into(), "other-worktree".into()),
                (3, 30, "s2".into(), "w".into()),
            ],
            4,
            30,
            &artifact,
        );
        assert_eq!(row.validation_outcome, "competing_supersede");
        assert!(row.reuse_cross_session);
    }
}
