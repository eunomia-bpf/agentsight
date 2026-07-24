// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Agent-readable process diagnosis over a persistent repository workspace.
//!
//! `agent-session` remains the source abstraction.  This module only computes
//! report-specific relations over [`RepositoryTrace`]; it is not another event
//! model and it does not ask an LLM to estimate counts from transcript text.

use crate::repository::{
    FileAction, RepositoryEvent, RepositoryTrace, RepositoryTraceOptions, build_repository_trace,
};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::ffi::OsString;
use std::fs;
use std::path::{Path, PathBuf};

type DynError = Box<dyn std::error::Error + Send + Sync>;

#[derive(Debug, Clone, Serialize)]
struct Brief {
    schema: &'static str,
    repository: String,
    revision: String,
    source_snapshot_id: String,
    observation_start_ms: i64,
    observation_end_ms: i64,
    coverage: Coverage,
    activity_by_kind: Vec<KindRow>,
    modules: Vec<ModuleRow>,
    sessions: Vec<SessionRow>,
    session_transitions: Vec<TransitionRow>,
    skills: Vec<SkillRow>,
    validation: ValidationSummary,
    cross_session_change_handoffs: Vec<CarryoverRow>,
    patterns: Vec<Pattern>,
}

#[derive(Debug, Clone, Serialize)]
struct Coverage {
    candidate_sessions: usize,
    parsed_sessions: usize,
    included_sessions: usize,
    workspace_sessions: usize,
    global_reference_sessions: usize,
    source_events: usize,
    tool_events: usize,
    file_actions: usize,
    confirmed_file_mutations: usize,
    attempted_or_unknown_file_mutations: usize,
    successful_validations: usize,
    failed_validations: usize,
}

#[derive(Debug, Clone, Serialize)]
struct KindRow {
    kind: String,
    reads: usize,
    confirmed_mutations: usize,
    artifacts: usize,
    sessions: usize,
}

#[derive(Debug, Clone, Default, Serialize)]
struct ModuleRow {
    module: String,
    reads: usize,
    confirmed_mutations: usize,
    attempted_or_unknown_mutations: usize,
    artifacts: usize,
    sessions: usize,
}

#[derive(Debug, Clone, Serialize)]
struct SessionRow {
    ordinal: usize,
    session_id: String,
    vendor: String,
    workspace_session: bool,
    start_ms: i64,
    end_ms: i64,
    tool_events: usize,
    file_reads: usize,
    confirmed_mutations: usize,
    attempted_or_unknown_mutations: usize,
    successful_validations: usize,
    failed_validations: usize,
    distinct_artifacts: usize,
    dominant_module: String,
    starts_after_all_prior_sessions_end: bool,
    read_tool_calls_before_first_confirmed_mutation: usize,
    reads_before_first_confirmed_mutation: usize,
    distinct_artifacts_before_first_mutation: usize,
    prior_artifact_reads_before_first_mutation: usize,
    distinct_modules_before_first_mutation: usize,
    wall_clock_span_before_first_mutation_ms: i64,
    source_file: String,
}

#[derive(Debug, Clone, Serialize)]
struct TransitionRow {
    from_session: String,
    to_session: String,
    from_dominant_module: String,
    to_dominant_module: String,
    module_js_divergence: f64,
    dominant_module_changed: bool,
    returned_module: String,
    return_gap_sessions: usize,
}

#[derive(Debug, Clone, Default, Serialize)]
struct SkillRow {
    skill: String,
    explicit_invocations: usize,
    attributed_events: usize,
    sessions: usize,
    repository_reads_in_those_sessions: usize,
    confirmed_mutations_in_those_sessions: usize,
    documentation_mutations_in_those_sessions: usize,
    validations_in_those_sessions: usize,
}

#[derive(Debug, Clone, Default, Serialize)]
struct ValidationSummary {
    #[serde(rename = "mutations_followed_by_successful_worktree_validation")]
    mutations_followed_by_successful_validation: usize,
    #[serde(rename = "mutations_with_later_session_worktree_validation")]
    mutations_validated_in_later_native_session: usize,
    #[serde(rename = "mutations_superseded_before_worktree_validation")]
    mutations_superseded_before_successful_validation: usize,
    mutations_superseded_in_later_native_session: usize,
    #[serde(rename = "mutations_without_later_worktree_validation")]
    mutations_without_later_successful_validation: usize,
    pending_mutations_at_native_session_end: usize,
    repeated_validation_calls_without_confirmed_mutation: usize,
    longest_validation_run_without_confirmed_mutation: usize,
}

#[derive(Debug, Clone, Serialize)]
struct CarryoverRow {
    artifact_id: String,
    path: String,
    mutation_session: String,
    mutation_event_id: String,
    mutation_source_call_id: String,
    mutation_timestamp_ms: i64,
    outcome: String,
    resolution_session: String,
    resolution_event_id: String,
    resolution_source_call_id: String,
    resolution_timestamp_ms: i64,
}

#[derive(Debug, Clone, Serialize)]
struct Pattern {
    kind: String,
    title: String,
    facts: BTreeMap<String, String>,
    why_it_matters: String,
    boundary: String,
    evidence: Vec<Evidence>,
}

#[derive(Debug, Clone, Serialize)]
struct Evidence {
    event_id: String,
    source_call_id: String,
    session_id: String,
    timestamp_ms: i64,
    source_file: String,
    operation: String,
    path: String,
    command: String,
    prompt_preview: String,
}

#[derive(Debug, Clone, Default)]
struct ArtifactAgg {
    path: String,
    kind: String,
    module: String,
    reads: usize,
    mutations: usize,
    attempted_mutations: usize,
    sessions: BTreeSet<String>,
    session_ordinals: BTreeSet<usize>,
    mutation_sessions: BTreeSet<String>,
    first_create: Option<usize>,
    first_mutation: Option<usize>,
    last_mutation: Option<usize>,
    last_access: Option<usize>,
    reads_after_first_mutation: usize,
    workspace_reads_after_first_mutation: usize,
    global_reads_after_first_mutation: usize,
    evidence: Vec<usize>,
    mutation_evidence: Vec<usize>,
}

#[derive(Debug, Clone, Default)]
struct SessionAgg {
    ordinal: usize,
    id: String,
    vendor: String,
    workspace_session: bool,
    start_ms: i64,
    end_ms: i64,
    tools: usize,
    reads: usize,
    mutations: usize,
    attempted_mutations: usize,
    tests_ok: usize,
    tests_fail: usize,
    docs_mutations: usize,
    artifacts: BTreeSet<String>,
    modules: BTreeMap<String, usize>,
    source_file: String,
    first_mutation_index: Option<usize>,
    starts_after_all_prior_sessions_end: bool,
    pre_mutation_read_calls: usize,
    pre_mutation_reads: usize,
    pre_mutation_prior_reads: usize,
    pre_mutation_artifacts: BTreeSet<String>,
    pre_mutation_modules: BTreeSet<String>,
}

#[derive(Debug, Clone)]
struct ReadSpan {
    session_id: String,
    tool_events: usize,
    read_tool_calls: usize,
    file_reads: usize,
    distinct_artifacts: usize,
    ended_by_mutation: bool,
    start: usize,
    end: usize,
}

#[derive(Debug, Clone)]
struct TestRun {
    calls: Vec<usize>,
}

pub fn run_diagnose_from_args<I, T>(args: I) -> Result<(), DynError>
where
    I: IntoIterator<Item = T>,
    T: Into<OsString>,
{
    let args = args.into_iter().map(Into::into).collect::<Vec<_>>();
    if args.iter().any(|arg| arg == "-h" || arg == "--help") {
        println!(
            "Usage: agentvis diagnose [PATH] [-o|--output FILE] [--global]\n\
             \nGenerate an Agent-readable workspace trajectory brief (Markdown by default; JSON when FILE ends in .json)."
        );
        return Ok(());
    }
    if args.iter().any(|arg| arg == "-V" || arg == "--version") {
        println!("agentvis {}", env!("CARGO_PKG_VERSION"));
        return Ok(());
    }
    let mut repo = PathBuf::from(".");
    let mut output = PathBuf::from("output/trajectory-brief.md");
    let mut global = false;
    let mut positional = false;
    let mut index = 0;
    while index < args.len() {
        if args[index] == "--global" {
            global = true;
        } else if args[index] == "--output" || args[index] == "-o" {
            index += 1;
            output = args
                .get(index)
                .map(PathBuf::from)
                .ok_or("diagnose --output requires a path")?;
        } else if args[index].to_string_lossy().starts_with('-') {
            return Err(
                format!("unknown diagnose option: {}", args[index].to_string_lossy()).into(),
            );
        } else if !positional {
            repo = PathBuf::from(&args[index]);
            positional = true;
        } else {
            return Err(format!(
                "unexpected diagnose argument: {}",
                args[index].to_string_lossy()
            )
            .into());
        }
        index += 1;
    }

    run_diagnose(&repo, &output, global)
}

pub fn run_diagnose(repo: &Path, output: &Path, global: bool) -> Result<(), DynError> {
    eprintln!("[diagnose 1/3] reconstructing native Agent actions");
    let trace = build_repository_trace(&RepositoryTraceOptions {
        repo: repo.to_path_buf(),
        global,
        end_ms: None,
    })?;
    eprintln!(
        "[diagnose 2/3] analysing {} sessions · {} tools · {} file actions",
        trace.session_count,
        trace.events.len(),
        trace.file_action_count
    );
    let brief = analyze(&trace);
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)?;
    }
    if output.extension().is_some_and(|value| value == "json") {
        fs::write(output, serde_json::to_vec_pretty(&brief)?)?;
    } else {
        fs::write(output, render_markdown(&brief))?;
    }
    eprintln!(
        "[diagnose 3/3] {} process signals -> {}",
        brief.patterns.len(),
        output.display()
    );
    Ok(())
}

fn analyze(trace: &RepositoryTrace) -> Brief {
    let mut sessions = BTreeMap::<usize, SessionAgg>::new();
    let mut artifacts = BTreeMap::<String, ArtifactAgg>::new();
    let mut module_sessions = BTreeMap::<String, BTreeSet<String>>::new();
    let mut module_artifacts = BTreeMap::<String, BTreeSet<String>>::new();
    let mut modules = BTreeMap::<String, ModuleRow>::new();
    let mut kind_sessions = BTreeMap::<String, BTreeSet<String>>::new();
    let mut kind_artifacts = BTreeMap::<String, BTreeSet<String>>::new();
    let mut kind_reads = BTreeMap::<String, usize>::new();
    let mut kind_mutations = BTreeMap::<String, usize>::new();
    for (index, event) in trace.events.iter().enumerate() {
        let session = sessions
            .entry(event.session_ordinal)
            .or_insert_with(|| SessionAgg {
                ordinal: event.session_ordinal,
                id: event.native_session_id.clone(),
                vendor: event.vendor.clone(),
                workspace_session: event.workspace_session,
                start_ms: event.ts_ms,
                end_ms: event.ts_ms,
                source_file: event.source_file.clone(),
                ..SessionAgg::default()
            });
        session.start_ms = session.start_ms.min(event.ts_ms);
        session.end_ms = session.end_ms.max(event.ts_ms);
        session.tools += 1;
        session.tests_ok += usize::from(is_successful_validation(event));
        session.tests_fail += usize::from(event.effect == "test" && event.status == "fail");

        let confirmed_mutation_here = event
            .actions
            .iter()
            .any(|action| is_confirmed_mutation(event, action));
        if confirmed_mutation_here && session.first_mutation_index.is_none() {
            session.first_mutation_index = Some(index);
        }

        for action in event.actions.iter().filter(|action| !action.scope) {
            let module = module(&action.path);
            let kind = artifact_kind(&action.path);
            let artifact_id = artifact_key(action);
            session.artifacts.insert(artifact_id.clone());
            *session.modules.entry(module.clone()).or_default() += 1;
            module_sessions
                .entry(module.clone())
                .or_default()
                .insert(event.native_session_id.clone());
            module_artifacts
                .entry(module.clone())
                .or_default()
                .insert(artifact_id.clone());
            kind_sessions
                .entry(kind.clone())
                .or_default()
                .insert(event.native_session_id.clone());
            kind_artifacts
                .entry(kind.clone())
                .or_default()
                .insert(artifact_id.clone());

            let artifact = artifacts.entry(artifact_id.clone()).or_default();
            artifact.path = action.path.clone();
            artifact.kind = kind.clone();
            artifact.module = module.clone();
            artifact.sessions.insert(event.native_session_id.clone());
            artifact.session_ordinals.insert(event.session_ordinal);
            artifact.last_access = Some(index);
            if artifact.evidence.last() != Some(&index) {
                artifact.evidence.push(index);
            }
            if artifact.first_mutation.is_some() && action.access == "read" {
                artifact.reads_after_first_mutation += 1;
                if event.workspace_session {
                    artifact.workspace_reads_after_first_mutation += 1;
                } else {
                    artifact.global_reads_after_first_mutation += 1;
                }
            }

            if action.access == "read" && event.status != "fail" {
                session.reads += 1;
                artifact.reads += 1;
                *kind_reads.entry(kind.clone()).or_default() += 1;
                modules.entry(module.clone()).or_default().reads += 1;
            }
            if is_confirmed_mutation(event, action) {
                session.mutations += 1;
                session.docs_mutations += usize::from(kind == "documentation");
                artifact.mutations += 1;
                artifact
                    .mutation_sessions
                    .insert(event.native_session_id.clone());
                artifact.first_mutation.get_or_insert(index);
                artifact.last_mutation = Some(index);
                if action.access == "create" {
                    artifact.first_create.get_or_insert(index);
                }
                artifact.mutation_evidence.push(index);
                *kind_mutations.entry(kind.clone()).or_default() += 1;
                modules
                    .entry(module.clone())
                    .or_default()
                    .confirmed_mutations += 1;
            } else if is_mutation(action) {
                session.attempted_mutations += 1;
                artifact.attempted_mutations += 1;
                modules
                    .entry(module.clone())
                    .or_default()
                    .attempted_or_unknown_mutations += 1;
            }
        }
    }

    annotate_session_boundaries(&mut sessions);
    annotate_session_grounding(trace, &mut sessions);

    for (name, row) in &mut modules {
        row.module = name.clone();
        row.sessions = module_sessions.get(name).map_or(0, BTreeSet::len);
        row.artifacts = module_artifacts.get(name).map_or(0, BTreeSet::len);
    }
    let mut module_rows = modules.into_values().collect::<Vec<_>>();
    module_rows.sort_by_key(|row| {
        Reverse((
            row.confirmed_mutations + row.reads,
            row.confirmed_mutations,
            row.sessions,
        ))
    });

    let session_rows = sessions
        .values()
        .map(|row| SessionRow {
            ordinal: row.ordinal,
            session_id: row.id.clone(),
            vendor: row.vendor.clone(),
            workspace_session: row.workspace_session,
            start_ms: row.start_ms,
            end_ms: row.end_ms,
            tool_events: row.tools,
            file_reads: row.reads,
            confirmed_mutations: row.mutations,
            attempted_or_unknown_mutations: row.attempted_mutations,
            successful_validations: row.tests_ok,
            failed_validations: row.tests_fail,
            distinct_artifacts: row.artifacts.len(),
            dominant_module: dominant_module(&row.modules),
            starts_after_all_prior_sessions_end: row.starts_after_all_prior_sessions_end,
            read_tool_calls_before_first_confirmed_mutation: row.pre_mutation_read_calls,
            reads_before_first_confirmed_mutation: row.pre_mutation_reads,
            distinct_artifacts_before_first_mutation: row.pre_mutation_artifacts.len(),
            prior_artifact_reads_before_first_mutation: row.pre_mutation_prior_reads,
            distinct_modules_before_first_mutation: row.pre_mutation_modules.len(),
            wall_clock_span_before_first_mutation_ms: row.first_mutation_index.map_or(0, |index| {
                trace.events[index].ts_ms.saturating_sub(row.start_ms)
            }),
            source_file: row.source_file.clone(),
        })
        .collect::<Vec<_>>();
    let transitions = session_transitions(&session_rows, &sessions);
    let skills = skill_rows(trace, &sessions);
    let (validation, validation_evidence, test_runs, carryovers) = validation_summary(trace);
    let read_spans = read_spans(trace, &sessions);
    let mut patterns = patterns(
        trace,
        &sessions,
        &artifacts,
        &transitions,
        &skills,
        &validation,
        &validation_evidence,
        &test_runs,
        &read_spans,
    );
    patterns.sort_by_key(|pattern| pattern_priority(&pattern.kind));

    let kinds = [
        "code",
        "test",
        "documentation",
        "data/result",
        "generated/scratch",
        "configuration",
        "other",
    ]
    .into_iter()
    .map(|kind| KindRow {
        kind: kind.to_string(),
        reads: *kind_reads.get(kind).unwrap_or(&0),
        confirmed_mutations: *kind_mutations.get(kind).unwrap_or(&0),
        artifacts: kind_artifacts.get(kind).map_or(0, BTreeSet::len),
        sessions: kind_sessions.get(kind).map_or(0, BTreeSet::len),
    })
    .collect();
    let confirmed = artifacts.values().map(|row| row.mutations).sum();
    let attempted = artifacts.values().map(|row| row.attempted_mutations).sum();
    let tests_ok = trace
        .events
        .iter()
        .filter(|event| is_successful_validation(event))
        .count();
    let tests_fail = trace
        .events
        .iter()
        .filter(|event| event.effect == "test" && event.status == "fail")
        .count();
    let workspace_sessions = session_rows
        .iter()
        .filter(|session| session.workspace_session)
        .count();
    let global_reference_sessions = session_rows.len().saturating_sub(workspace_sessions);

    Brief {
        schema: "agent-nebula.workspace-trajectory-brief.v2",
        repository: trace.repository.clone(),
        revision: trace.revision.clone(),
        source_snapshot_id: source_snapshot_id(trace),
        observation_start_ms: trace.start_ms,
        observation_end_ms: trace.end_ms,
        coverage: Coverage {
            candidate_sessions: trace.candidate_session_count,
            parsed_sessions: trace.parsed_session_count,
            included_sessions: trace.session_count,
            workspace_sessions,
            global_reference_sessions,
            source_events: trace.source_event_count,
            tool_events: trace.events.len(),
            file_actions: trace.file_action_count,
            confirmed_file_mutations: confirmed,
            attempted_or_unknown_file_mutations: attempted,
            successful_validations: tests_ok,
            failed_validations: tests_fail,
        },
        activity_by_kind: kinds,
        modules: module_rows,
        sessions: session_rows,
        session_transitions: transitions,
        skills,
        validation,
        cross_session_change_handoffs: carryovers,
        patterns,
    }
}

fn annotate_session_boundaries(sessions: &mut BTreeMap<usize, SessionAgg>) {
    let mut prior_end = i64::MIN;
    let mut evolution_index = 0usize;
    for session in sessions.values_mut() {
        if !is_evolution_session_agg(session) {
            continue;
        }
        session.starts_after_all_prior_sessions_end =
            evolution_index > 0 && session.start_ms >= prior_end;
        prior_end = prior_end.max(session.end_ms);
        evolution_index += 1;
    }
}

fn annotate_session_grounding(trace: &RepositoryTrace, sessions: &mut BTreeMap<usize, SessionAgg>) {
    let mut prior_artifacts = HashSet::<String>::new();
    for (ordinal, session) in sessions.iter_mut() {
        if !is_evolution_session_agg(session) {
            continue;
        }
        let boundary = session.first_mutation_index.unwrap_or(usize::MAX);
        for (index, event) in trace.events.iter().enumerate() {
            if event.session_ordinal != *ordinal || index >= boundary {
                continue;
            }
            let reads = event
                .actions
                .iter()
                .filter(|action| !action.scope && action.access == "read" && event.status != "fail")
                .collect::<Vec<_>>();
            session.pre_mutation_read_calls += usize::from(!reads.is_empty());
            for action in reads {
                session.pre_mutation_reads += 1;
                session.pre_mutation_modules.insert(module(&action.path));
                session.pre_mutation_artifacts.insert(artifact_key(action));
                session.pre_mutation_prior_reads +=
                    usize::from(prior_artifacts.contains(&artifact_key(action)));
            }
        }
        prior_artifacts.extend(session.artifacts.iter().cloned());
    }
}

fn session_transitions(
    rows: &[SessionRow],
    sessions: &BTreeMap<usize, SessionAgg>,
) -> Vec<TransitionRow> {
    let active = rows
        .iter()
        .filter(|row| is_evolution_session(row) && row.dominant_module != "—")
        .collect::<Vec<_>>();
    let mut last_seen = HashMap::<String, usize>::new();
    let mut result = Vec::new();
    for (position, pair) in active.windows(2).enumerate() {
        let left = pair[0];
        let right = pair[1];
        let left_dist = &sessions[&left.ordinal].modules;
        let right_dist = &sessions[&right.ordinal].modules;
        for name in left_dist.keys() {
            last_seen.insert(name.clone(), position);
        }
        let returned = right_dist
            .keys()
            .filter_map(|name| {
                let previous = last_seen.get(name).copied()?;
                let gap = (position + 1).saturating_sub(previous + 1);
                (gap > 0).then(|| (name.clone(), gap))
            })
            .max_by_key(|(_, gap)| *gap);
        result.push(TransitionRow {
            from_session: left.session_id.clone(),
            to_session: right.session_id.clone(),
            from_dominant_module: left.dominant_module.clone(),
            to_dominant_module: right.dominant_module.clone(),
            module_js_divergence: js_divergence(left_dist, right_dist),
            dominant_module_changed: left.dominant_module != right.dominant_module,
            returned_module: returned.as_ref().map_or(String::new(), |row| row.0.clone()),
            return_gap_sessions: returned.map_or(0, |row| row.1),
        });
    }
    result
}

fn is_evolution_session(row: &SessionRow) -> bool {
    row.workspace_session || row.confirmed_mutations > 0
}

fn is_evolution_session_agg(row: &SessionAgg) -> bool {
    row.workspace_session || row.mutations > 0
}

fn skill_rows(trace: &RepositoryTrace, sessions: &BTreeMap<usize, SessionAgg>) -> Vec<SkillRow> {
    let mut skill_sessions = BTreeMap::<String, BTreeSet<String>>::new();
    let mut explicit = BTreeMap::<String, usize>::new();
    let mut attributed = BTreeMap::<String, usize>::new();
    for event in &trace.events {
        if let Some(skill) = event
            .skill_name
            .as_deref()
            .filter(|value| !value.is_empty())
        {
            *explicit.entry(skill.to_string()).or_default() += 1;
            skill_sessions
                .entry(skill.to_string())
                .or_default()
                .insert(event.native_session_id.clone());
        }
        if let Some(skill) = event
            .attribution_skill
            .as_deref()
            .filter(|value| !value.is_empty())
        {
            *attributed.entry(skill.to_string()).or_default() += 1;
            skill_sessions
                .entry(skill.to_string())
                .or_default()
                .insert(event.native_session_id.clone());
        }
    }
    let by_id = sessions
        .values()
        .map(|row| (&row.id, row))
        .collect::<HashMap<_, _>>();
    let mut rows = skill_sessions
        .into_iter()
        .map(|(skill, ids)| {
            let selected = ids
                .iter()
                .filter_map(|id| by_id.get(id))
                .collect::<Vec<_>>();
            SkillRow {
                skill: skill.clone(),
                explicit_invocations: *explicit.get(&skill).unwrap_or(&0),
                attributed_events: *attributed.get(&skill).unwrap_or(&0),
                sessions: ids.len(),
                repository_reads_in_those_sessions: selected.iter().map(|row| row.reads).sum(),
                confirmed_mutations_in_those_sessions: selected
                    .iter()
                    .map(|row| row.mutations)
                    .sum(),
                documentation_mutations_in_those_sessions: selected
                    .iter()
                    .map(|row| row.docs_mutations)
                    .sum(),
                validations_in_those_sessions: selected.iter().map(|row| row.tests_ok).sum(),
            }
        })
        .collect::<Vec<_>>();
    rows.sort_by_key(|row| {
        Reverse((
            row.sessions,
            row.explicit_invocations + row.attributed_events,
        ))
    });
    rows
}

fn validation_summary(
    trace: &RepositoryTrace,
) -> (
    ValidationSummary,
    Vec<usize>,
    Vec<TestRun>,
    Vec<CarryoverRow>,
) {
    let mut pending = HashMap::<String, (String, usize, String)>::new();
    let mut crossed_session_end = HashSet::<usize>::new();
    let mut carryover_tuples = Vec::<(String, usize, Option<usize>, String)>::new();
    let mut since_mutation = HashMap::<String, Vec<usize>>::new();
    let mut all_runs = Vec::new();
    let mut summary = ValidationSummary::default();
    let mut evidence = Vec::new();
    let last_event = trace
        .events
        .iter()
        .enumerate()
        .map(|(index, event)| (event.native_session_id.clone(), index))
        .collect::<HashMap<_, _>>();

    for (index, event) in trace.events.iter().enumerate() {
        for action in event
            .actions
            .iter()
            .filter(|action| is_confirmed_mutation(event, action))
        {
            if let Some((_, previous, previous_session)) = pending.insert(
                artifact_key(action),
                (
                    action.worktree_id.clone(),
                    index,
                    event.native_session_id.clone(),
                ),
            ) {
                summary.mutations_superseded_before_successful_validation += 1;
                summary.mutations_superseded_in_later_native_session +=
                    usize::from(previous_session != event.native_session_id);
                if crossed_session_end.contains(&previous) {
                    carryover_tuples.push((
                        artifact_key(action),
                        previous,
                        Some(index),
                        "superseded".into(),
                    ));
                }
                evidence.push(previous);
                evidence.push(index);
            }
            if let Some(run) = since_mutation.remove(&action.worktree_id)
                && run.len() > 1
            {
                all_runs.push(TestRun { calls: run });
            }
        }
        if is_successful_validation(event) {
            let validated = event
                .worktree_id
                .as_ref()
                .map_or_else(Vec::new, |worktree| {
                    pending
                        .iter()
                        .filter(|(_, (candidate, _, _))| candidate == worktree)
                        .map(|(artifact, (_, mutation, session))| {
                            (artifact.clone(), *mutation, session.clone())
                        })
                        .collect::<Vec<_>>()
                });
            summary.mutations_followed_by_successful_validation += validated.len();
            for (artifact, mutation, session) in validated {
                pending.remove(&artifact);
                summary.mutations_validated_in_later_native_session +=
                    usize::from(session != event.native_session_id);
                if crossed_session_end.contains(&mutation) {
                    carryover_tuples.push((
                        artifact,
                        mutation,
                        Some(index),
                        "worktree-validation-observed".into(),
                    ));
                }
                evidence.push(mutation);
            }
        }
        if event.effect == "test" {
            let worktree = event
                .worktree_id
                .clone()
                .unwrap_or_else(|| format!("unknown:{}", event.native_session_id));
            since_mutation.entry(worktree).or_default().push(index);
        }
        if last_event.get(&event.native_session_id) == Some(&index) {
            let at_end = pending
                .values()
                .filter(|(_, _, session)| session == &event.native_session_id)
                .map(|(_, mutation, _)| *mutation)
                .collect::<Vec<_>>();
            summary.pending_mutations_at_native_session_end += at_end.len();
            crossed_session_end.extend(at_end);
        }
    }
    for run in since_mutation.into_values().filter(|run| run.len() > 1) {
        all_runs.push(TestRun { calls: run });
    }
    summary.mutations_without_later_successful_validation = pending.len();
    summary.repeated_validation_calls_without_confirmed_mutation =
        all_runs.iter().map(|run| run.calls.len() - 1).sum();
    summary.longest_validation_run_without_confirmed_mutation = all_runs
        .iter()
        .map(|run| run.calls.len())
        .max()
        .unwrap_or(0);
    for (artifact, (_, index, _)) in &pending {
        if crossed_session_end.contains(index) {
            carryover_tuples.push((artifact.clone(), *index, None, "open-at-cutoff".into()));
        }
        evidence.push(*index);
    }
    evidence.sort_unstable();
    evidence.dedup();
    let mut carryovers = carryover_tuples
        .into_iter()
        .map(|(artifact, mutation, resolution, outcome)| {
            carryover_row(trace, &artifact, mutation, resolution, &outcome)
        })
        .collect::<Vec<_>>();
    carryovers.sort_by_key(|row| {
        (
            row.outcome != "open-at-cutoff",
            Reverse(row.mutation_timestamp_ms),
        )
    });
    (summary, evidence, all_runs, carryovers)
}

fn carryover_row(
    trace: &RepositoryTrace,
    artifact: &str,
    mutation_index: usize,
    resolution_index: Option<usize>,
    outcome: &str,
) -> CarryoverRow {
    let mutation = &trace.events[mutation_index];
    let path = mutation
        .actions
        .iter()
        .find(|action| artifact_key(action) == artifact)
        .map_or_else(|| artifact.to_string(), |action| action.path.clone());
    let resolution = resolution_index.map(|index| &trace.events[index]);
    CarryoverRow {
        artifact_id: mutation
            .actions
            .iter()
            .find(|action| artifact_key(action) == artifact)
            .map_or_else(|| artifact.to_string(), |action| action.artifact_id.clone()),
        path,
        mutation_session: mutation.native_session_id.clone(),
        mutation_event_id: mutation.id.clone(),
        mutation_source_call_id: mutation
            .source_call_id
            .clone()
            .unwrap_or_else(|| "—".into()),
        mutation_timestamp_ms: mutation.ts_ms,
        outcome: outcome.to_string(),
        resolution_session: resolution
            .map_or_else(String::new, |event| event.native_session_id.clone()),
        resolution_event_id: resolution.map_or_else(String::new, |event| event.id.clone()),
        resolution_source_call_id: resolution.map_or_else(String::new, |event| {
            event.source_call_id.clone().unwrap_or_else(|| "—".into())
        }),
        resolution_timestamp_ms: resolution.map_or(0, |event| event.ts_ms),
    }
}

fn read_spans(trace: &RepositoryTrace, sessions: &BTreeMap<usize, SessionAgg>) -> Vec<ReadSpan> {
    let mut spans = Vec::new();
    let mut current =
        HashMap::<String, (usize, usize, usize, usize, usize, BTreeSet<String>)>::new();
    for (index, event) in trace.events.iter().enumerate() {
        if !sessions
            .get(&event.session_ordinal)
            .is_some_and(is_evolution_session_agg)
        {
            continue;
        }
        let entry = current.entry(event.native_session_id.clone()).or_insert((
            index,
            index,
            0,
            0,
            0,
            BTreeSet::new(),
        ));
        entry.1 = index;
        entry.2 += 1;
        let reads = event
            .actions
            .iter()
            .filter(|action| !action.scope && action.access == "read" && event.status != "fail")
            .collect::<Vec<_>>();
        entry.3 += usize::from(!reads.is_empty());
        entry.4 += reads.len();
        entry.5.extend(reads.into_iter().map(artifact_key));
        if event
            .actions
            .iter()
            .any(|action| is_confirmed_mutation(event, action))
        {
            let (start, end, tools, read_calls, file_reads, artifacts) = current
                .remove(&event.native_session_id)
                .expect("current span exists");
            if file_reads > 0 {
                spans.push(ReadSpan {
                    session_id: event.native_session_id.clone(),
                    tool_events: tools,
                    read_tool_calls: read_calls,
                    file_reads,
                    distinct_artifacts: artifacts.len(),
                    ended_by_mutation: true,
                    start,
                    end,
                });
            }
        }
    }
    for (session_id, (start, end, tools, read_calls, file_reads, artifacts)) in current {
        if file_reads > 0 {
            spans.push(ReadSpan {
                session_id,
                tool_events: tools,
                read_tool_calls: read_calls,
                file_reads,
                distinct_artifacts: artifacts.len(),
                ended_by_mutation: false,
                start,
                end,
            });
        }
    }
    spans.sort_by_key(|span| {
        Reverse((
            span.read_tool_calls,
            span.file_reads,
            span.distinct_artifacts,
            span.tool_events,
        ))
    });
    spans
}

fn action_strategy_pattern(
    trace: &RepositoryTrace,
    sessions: &BTreeMap<usize, SessionAgg>,
) -> Option<Pattern> {
    let mut by_session = BTreeMap::<usize, Vec<usize>>::new();
    for (index, event) in trace.events.iter().enumerate() {
        if sessions
            .get(&event.session_ordinal)
            .is_some_and(is_evolution_session_agg)
        {
            by_session
                .entry(event.session_ordinal)
                .or_default()
                .push(index);
        }
    }
    let mut mutating_sessions = 0usize;
    let mut validation_before_first_mutation = 0usize;
    let mut validation_only_after_first_mutation = 0usize;
    let mut no_validation = 0usize;
    let mut successful_validation_after_mutation = 0usize;
    let mut closed_mutation_bursts = Vec::<usize>::new();
    let mut open_mutation_bursts = 0usize;
    let mut transitions = BTreeMap::<String, usize>::new();
    let mut evidence_indices = Vec::<usize>::new();

    for indices in by_session.values() {
        let first_mutation = indices.iter().copied().find(|index| {
            trace.events[*index]
                .actions
                .iter()
                .any(|action| is_confirmed_mutation(&trace.events[*index], action))
        });
        let Some(first_mutation) = first_mutation else {
            continue;
        };
        mutating_sessions += 1;
        let validation_indices = indices
            .iter()
            .copied()
            .filter(|index| trace.events[*index].effect == "test")
            .collect::<Vec<_>>();
        if validation_indices.is_empty() {
            no_validation += 1;
        } else if validation_indices
            .iter()
            .any(|index| *index < first_mutation)
        {
            validation_before_first_mutation += 1;
        } else {
            validation_only_after_first_mutation += 1;
        }
        successful_validation_after_mutation +=
            usize::from(indices.iter().copied().any(|index| {
                index > first_mutation && is_successful_validation(&trace.events[index])
            }));

        let mut prior_state = None::<&'static str>;
        let mut mutation_events_since_validation = 0usize;
        for index in indices {
            let event = &trace.events[*index];
            let state = trajectory_state(event);
            if let Some(state) = state
                && prior_state != Some(state)
            {
                if let Some(prior) = prior_state {
                    *transitions
                        .entry(format!("{prior}_to_{state}"))
                        .or_default() += 1;
                    if matches!(
                        (prior, state),
                        ("inspection", "mutation")
                            | ("mutation", "validation")
                            | ("validation", "mutation")
                    ) && evidence_indices.len() < 12
                    {
                        evidence_indices.push(*index);
                    }
                }
                prior_state = Some(state);
            }
            if event
                .actions
                .iter()
                .any(|action| is_confirmed_mutation(event, action))
            {
                mutation_events_since_validation += 1;
            }
            if is_successful_validation(event) && mutation_events_since_validation > 0 {
                closed_mutation_bursts.push(mutation_events_since_validation);
                mutation_events_since_validation = 0;
            }
        }
        open_mutation_bursts += usize::from(mutation_events_since_validation > 0);
    }
    if mutating_sessions == 0 {
        return None;
    }

    let mut pattern_facts = BTreeMap::from([
        ("mutating_sessions".into(), mutating_sessions.to_string()),
        (
            "sessions_with_validation_before_first_mutation".into(),
            validation_before_first_mutation.to_string(),
        ),
        (
            "sessions_with_validation_only_after_first_mutation".into(),
            validation_only_after_first_mutation.to_string(),
        ),
        (
            "sessions_with_no_recognized_validation".into(),
            no_validation.to_string(),
        ),
        (
            "sessions_with_successful_validation_after_first_mutation".into(),
            successful_validation_after_mutation.to_string(),
        ),
        (
            "mutation_bursts_closed_by_successful_validation".into(),
            closed_mutation_bursts.len().to_string(),
        ),
        (
            "open_mutation_bursts_at_session_or_snapshot_end".into(),
            open_mutation_bursts.to_string(),
        ),
        (
            "median_mutation_events_per_closed_validation_cycle".into(),
            (!closed_mutation_bursts.is_empty())
                .then(|| median(&closed_mutation_bursts).to_string())
                .unwrap_or_else(|| "—".into()),
        ),
        (
            "maximum_mutation_events_per_closed_validation_cycle".into(),
            closed_mutation_bursts
                .iter()
                .max()
                .map_or_else(|| "—".into(), usize::to_string),
        ),
    ]);
    for name in [
        "inspection_to_mutation",
        "mutation_to_validation",
        "validation_to_mutation",
        "inspection_to_validation",
        "validation_to_inspection",
        "mutation_to_inspection",
    ] {
        pattern_facts.insert(
            format!("collapsed_transition_{name}"),
            transitions.get(name).copied().unwrap_or(0).to_string(),
        );
    }
    Some(Pattern {
        kind: "action-strategy".into(),
        title: "The action sequence exposes inspect–mutate–validate strategy".into(),
        facts: pattern_facts,
        why_it_matters:
            "This answers whether sessions test before changing artifacts, validate only afterwards, cycle between change and validation, or end with an open mutation burst."
                .into(),
        boundary:
            "Adjacent repeated states are collapsed before transition counting. States come from exact normalized Tool effects; recognized validation is a temporal marker, not proof that changed files were covered or correct."
                .into(),
        evidence: evidence_indices
            .into_iter()
            .take(8)
            .map(|index| evidence(trace, index, None))
            .collect(),
    })
}

fn trajectory_state(event: &RepositoryEvent) -> Option<&'static str> {
    if event.effect == "test" {
        Some("validation")
    } else if event
        .actions
        .iter()
        .any(|action| is_confirmed_mutation(event, action))
    {
        Some("mutation")
    } else if event.status != "fail"
        && event
            .actions
            .iter()
            .any(|action| !action.scope && action.access == "read")
    {
        Some("inspection")
    } else {
        None
    }
}

#[allow(clippy::too_many_arguments)]
fn patterns(
    trace: &RepositoryTrace,
    sessions: &BTreeMap<usize, SessionAgg>,
    artifacts: &BTreeMap<String, ArtifactAgg>,
    transitions: &[TransitionRow],
    skills: &[SkillRow],
    validation: &ValidationSummary,
    validation_evidence: &[usize],
    test_runs: &[TestRun],
    read_spans: &[ReadSpan],
) -> Vec<Pattern> {
    let mut result = Vec::new();
    if let Some(pattern) = action_strategy_pattern(trace, sessions) {
        result.push(pattern);
    }
    let session_values = sessions.values().collect::<Vec<_>>();
    let grounding = session_values
        .iter()
        .skip(1)
        .filter(|row| row.first_mutation_index.is_some() && row.starts_after_all_prior_sessions_end)
        .map(|row| row.pre_mutation_read_calls)
        .collect::<Vec<_>>();
    if !grounding.is_empty() {
        let highest = session_values
            .iter()
            .skip(1)
            .filter(|row| {
                row.first_mutation_index.is_some() && row.starts_after_all_prior_sessions_end
            })
            .max_by_key(|row| row.pre_mutation_read_calls)
            .expect("nonempty");
        result.push(Pattern {
            kind: "pre-mutation-inspection".into(),
            title:
                "Some non-overlapping native roots inspect extensively before their first mutation"
                    .into(),
            facts: facts([
                ("boundaries", grounding.len().to_string()),
                (
                    "median_read_tool_calls_before_first_mutation",
                    median(&grounding).to_string(),
                ),
                (
                    "maximum_read_tool_calls_before_first_mutation",
                    highest.pre_mutation_read_calls.to_string(),
                ),
                (
                    "file_read_effects_in_maximum",
                    highest.pre_mutation_reads.to_string(),
                ),
                (
                    "distinct_artifacts_in_maximum",
                    highest.pre_mutation_artifacts.len().to_string(),
                ),
                (
                    "prior_artifact_read_effects_in_maximum",
                    highest.pre_mutation_prior_reads.to_string(),
                ),
                (
                    "wall_clock_span_to_first_mutation_ms",
                    highest.first_mutation_index.map_or(0, |index| {
                        trace.events[index].ts_ms.saturating_sub(highest.start_ms)
                    }).to_string(),
                ),
            ]),
            why_it_matters:
                "This locates roots that spend substantial observed file inspection before switching into workspace mutation, so an Agent can inspect whether the episode was review, learning, delayed execution, or unnecessary rediscovery."
                    .into(),
            boundary:
                "A native root may span many transcript files, compactions, delegated subagents, goals, and days. This is not a context-restart or re-grounding cost. The wall-clock span includes idle time; the primary count is read Tool calls."
                    .into(),
            evidence: grounding_endpoints(trace, highest)
                .into_iter()
                .map(|index| evidence(trace, index, None))
                .collect(),
        });
    }

    if !transitions.is_empty() {
        let max = transitions
            .iter()
            .max_by(|left, right| {
                left.module_js_divergence
                    .total_cmp(&right.module_js_divergence)
            })
            .expect("nonempty");
        let returned = transitions
            .iter()
            .filter(|row| !row.returned_module.is_empty())
            .count();
        result.push(Pattern {
            kind: "module-migration".into(),
            title: "Attention migrates between modules across native sessions".into(),
            facts: facts([
                ("session_transitions", transitions.len().to_string()),
                (
                    "dominant_module_changes",
                    transitions
                        .iter()
                        .filter(|row| row.dominant_module_changed)
                        .count()
                        .to_string(),
                ),
                ("returns_after_absence", returned.to_string()),
                (
                    "maximum_module_js_divergence",
                    format!("{:.3}", max.module_js_divergence),
                ),
                (
                    "largest_shift",
                    format!(
                        "{} → {}",
                        max.from_dominant_module, max.to_dominant_module
                    ),
                ),
            ]),
            why_it_matters:
                "This exposes project phases, resumed work, and abrupt focus shifts that aggregate action counts erase."
                    .into(),
            boundary:
                "Module is the first repository path component and divergence is descriptive; neither establishes goal progress."
                    .into(),
            evidence: first_event_for_session(trace, &max.to_session)
                .into_iter()
                .map(|index| evidence(trace, index, None))
                .collect(),
        });
    }

    if validation.mutations_superseded_before_successful_validation > 0
        || validation.mutations_without_later_successful_validation > 0
    {
        result.push(Pattern {
            kind: "validation-lag".into(),
            title: "Some artifact changes are superseded or lack a later observed worktree validation"
                .into(),
            facts: facts([
                (
                    "mutations_followed_by_worktree_validation",
                    validation
                        .mutations_followed_by_successful_validation
                        .to_string(),
                ),
                (
                    "superseded_before_worktree_validation",
                    validation
                        .mutations_superseded_before_successful_validation
                        .to_string(),
                ),
                (
                    "no_later_observed_worktree_validation",
                    validation
                        .mutations_without_later_successful_validation
                        .to_string(),
                ),
            ]),
            why_it_matters:
                "This distinguishes change volume from validation-aligned iteration and points to exact mutations needing review."
                    .into(),
            boundary:
                "This is temporal association, not proof that a command exercised a particular artifact. Only recognized successful test/build/check Tool calls count; missing or external validation is not observed."
                    .into(),
            evidence: validation_evidence
                .iter()
                .rev()
                .take(8)
                .map(|index| evidence(trace, *index, None))
                .collect(),
        });
    }

    if validation.pending_mutations_at_native_session_end > 0
        || validation.mutations_validated_in_later_native_session > 0
        || validation.mutations_superseded_in_later_native_session > 0
    {
        result.push(Pattern {
            kind: "cross-session-validation-carryover".into(),
            title: "Unresolved workspace changes cross native-session boundaries".into(),
            facts: facts([
                (
                    "pending_mutations_at_session_end",
                    validation
                        .pending_mutations_at_native_session_end
                        .to_string(),
                ),
                (
                    "later_session_worktree_validation_associations",
                    validation
                        .mutations_validated_in_later_native_session
                        .to_string(),
                ),
                (
                    "later_session_supersessions",
                    validation
                        .mutations_superseded_in_later_native_session
                        .to_string(),
                ),
            ]),
            why_it_matters:
                "This is persistent-workspace carryover: a later Agent context inherits changes whose validation state was not closed in the producing session."
                    .into(),
            boundary:
                "A recognized command is associated with every pending mutation in its worktree; it does not prove that each artifact was exercised. Validation may also occur outside the admitted native records."
                    .into(),
            evidence: validation_evidence
                .iter()
                .rev()
                .take(8)
                .map(|index| evidence(trace, *index, None))
                .collect(),
        });
    }

    if validation.repeated_validation_calls_without_confirmed_mutation > 0 {
        let longest = test_runs
            .iter()
            .max_by_key(|run| run.calls.len())
            .expect("repeated calls imply a run");
        let signatures = longest
            .calls
            .iter()
            .map(|index| test_signature(&trace.events[*index]))
            .collect::<BTreeSet<_>>();
        let outcome_transitions = longest
            .calls
            .windows(2)
            .filter(|pair| trace.events[pair[0]].status != trace.events[pair[1]].status)
            .count();
        let repeated = longest_identical_test_streak(trace, longest);
        result.push(Pattern {
            kind: "validation-repetition".into(),
            title: "Validation calls occur without an intervening confirmed repository mutation"
                .into(),
            facts: facts([
                (
                    "extra_validation_calls",
                    validation
                        .repeated_validation_calls_without_confirmed_mutation
                        .to_string(),
                ),
                (
                    "longest_run",
                    validation
                        .longest_validation_run_without_confirmed_mutation
                        .to_string(),
                ),
                (
                    "distinct_command_signatures_in_longest_run",
                    signatures.len().to_string(),
                ),
                (
                    "outcome_transitions_in_longest_run",
                    outcome_transitions.to_string(),
                ),
                (
                    "longest_identical_command_same_outcome_streak",
                    repeated.len().to_string(),
                ),
            ]),
            why_it_matters:
                "Command diversity and outcome transitions help separate environment diagnosis or a deliberate matrix from an identical-check treadmill."
                    .into(),
            boundary:
                "No confirmed source mutation is not no state change: generated files, caches, services, or external dependencies may change between calls."
                    .into(),
            evidence: repeated
                .iter()
                .take(8)
                .map(|index| evidence(trace, *index, None))
                .collect(),
        });
    }

    let mut cross_session = artifacts
        .iter()
        .filter(|(_, row)| row.mutation_sessions.len() > 1)
        .collect::<Vec<_>>();
    cross_session.sort_by_key(|(_, row)| Reverse((row.mutations, row.mutation_sessions.len())));
    if let Some((_, top)) = cross_session.first() {
        result.push(Pattern {
            kind: "cross-session-repeated-mutation".into(),
            title: "The same artifacts receive mutations across native sessions".into(),
            facts: facts([
                ("cross_session_artifacts", cross_session.len().to_string()),
                ("top_artifact", top.path.clone()),
                ("top_artifact_mutations", top.mutations.to_string()),
                (
                    "top_artifact_mutation_sessions",
                    top.mutation_sessions.len().to_string(),
                ),
            ]),
            why_it_matters:
                "Cross-session recurrence identifies durable hotspots and candidates for intentional refinement or rework more directly than commit frequency."
                    .into(),
            boundary:
                "Repeated mutation can be healthy incremental development. Intent and defect status require source inspection."
                    .into(),
            evidence: top
                .mutation_evidence
                .iter()
                .rev()
                .take(8)
                .map(|index| evidence(trace, *index, Some(&top.path)))
                .collect(),
        });
    }

    let evolution_positions = sessions
        .values()
        .filter(|session| is_evolution_session_agg(session))
        .enumerate()
        .map(|(position, session)| (session.ordinal, position))
        .collect::<HashMap<_, _>>();
    let mut revivals = artifacts
        .values()
        .filter_map(|row| {
            let ordinals = row
                .session_ordinals
                .iter()
                .copied()
                .filter_map(|ordinal| {
                    evolution_positions
                        .get(&ordinal)
                        .map(|position| (*position, ordinal))
                })
                .collect::<Vec<_>>();
            let pair = ordinals
                .windows(2)
                .map(|pair| {
                    (
                        pair[1].0.saturating_sub(pair[0].0 + 1),
                        pair[0].1,
                        pair[1].1,
                    )
                })
                .max_by_key(|(gap, _, _)| *gap)?;
            (pair.0 > 0).then_some((pair.0, pair.1, pair.2, row))
        })
        .collect::<Vec<_>>();
    revivals.sort_by_key(|(gap, _, _, row)| Reverse((*gap, row.mutations + row.reads)));
    if let Some((gap, before, after, top)) = revivals.first() {
        result.push(Pattern {
            kind: "artifact-reaccess-after-session-gap".into(),
            title: "Artifacts are accessed again after intervening native sessions"
                .into(),
            facts: facts([
                ("revived_artifacts", revivals.len().to_string()),
                ("longest_gap_sessions", gap.to_string()),
                ("longest_gap_artifact", top.path.clone()),
                (
                    "artifact_evolution_sessions",
                    top.session_ordinals
                        .iter()
                        .filter(|ordinal| evolution_positions.contains_key(ordinal))
                        .count()
                        .to_string(),
                ),
            ]),
            why_it_matters:
                "Artifact revival within workspace/evolution sessions reveals deferred work and long-range dependencies that per-session reports split apart."
                    .into(),
            boundary:
                "Read-only external consumer sessions are excluded here and reported separately. Absence means no observed repository file action in intervening evolution sessions; it does not mean the artifact was forgotten."
                    .into(),
            evidence: top
                .evidence
                .iter()
                .filter(|index| {
                    matches!(
                        trace.events[**index].session_ordinal,
                        ordinal if ordinal == *before || ordinal == *after
                    )
                })
                .copied()
                .fold(Vec::<usize>::new(), |mut selected, index| {
                    let ordinal = trace.events[index].session_ordinal;
                    if ordinal == *before {
                        if let Some(slot) = selected.first_mut() {
                            *slot = index;
                        } else {
                            selected.push(index);
                        }
                    } else if selected.len() < 2 {
                        selected.push(index);
                    }
                    selected
                })
                .into_iter()
                .map(|index| evidence(trace, index, Some(&top.path)))
                .collect(),
        });
    }

    let mut one_touch = artifacts
        .values()
        .filter(|row| {
            row.first_create.is_some()
                && row.mutations == 1
                && row.reads_after_first_mutation == 0
                && row.last_access == row.last_mutation
                && row.kind != "generated/scratch"
        })
        .collect::<Vec<_>>();
    one_touch.sort_by_key(|row| Reverse(row.last_mutation.unwrap_or(0)));
    if !one_touch.is_empty() {
        result.push(Pattern {
            kind: "unrevisited-created-artifacts".into(),
            title: "Some created artifacts are never observed again".into(),
            facts: facts([
                ("created_once_never_revisited", one_touch.len().to_string()),
                (
                    "documentation_artifacts",
                    one_touch
                        .iter()
                        .filter(|row| row.kind == "documentation")
                        .count()
                        .to_string(),
                ),
                (
                    "data_or_result_artifacts",
                    one_touch
                        .iter()
                        .filter(|row| row.kind == "data/result")
                        .count()
                        .to_string(),
                ),
            ]),
            why_it_matters:
                "One-touch outputs are candidates for generated clutter, abandoned branches, or final deliverables that deserve classification."
                    .into(),
            boundary:
                "No later Tool access does not mean unused: another process, a human, or an unobserved session may consume the artifact."
                    .into(),
            evidence: one_touch
                .iter()
                .take(8)
                .filter_map(|row| {
                    row.first_create
                        .map(|index| evidence(trace, index, Some(&row.path)))
                })
                .collect(),
        });
    }

    let mut documents = artifacts
        .values()
        .filter(|row| row.kind == "documentation" && row.mutations > 0)
        .collect::<Vec<_>>();
    documents.sort_by_key(|row| Reverse((row.mutations, row.sessions.len())));
    let doc_mutations = documents.iter().map(|row| row.mutations).sum::<usize>();
    let doc_reads_after = documents
        .iter()
        .map(|row| row.reads_after_first_mutation)
        .sum::<usize>();
    let doc_workspace_reads_after = documents
        .iter()
        .map(|row| row.workspace_reads_after_first_mutation)
        .sum::<usize>();
    let doc_global_reads_after = documents
        .iter()
        .map(|row| row.global_reads_after_first_mutation)
        .sum::<usize>();
    if doc_mutations > 0 {
        result.push(Pattern {
            kind: "documentation-reuse".into(),
            title: "Written documentation has a measurable later-reuse footprint".into(),
            facts: facts([
                ("touched_documents", documents.len().to_string()),
                ("confirmed_document_mutations", doc_mutations.to_string()),
                ("reads_after_first_mutation", doc_reads_after.to_string()),
                (
                    "workspace_reads_after_first_mutation",
                    doc_workspace_reads_after.to_string(),
                ),
                (
                    "external_reads_after_first_mutation",
                    doc_global_reads_after.to_string(),
                ),
                (
                    "documents_never_reread",
                    documents
                        .iter()
                        .filter(|row| row.reads_after_first_mutation == 0)
                        .count()
                        .to_string(),
                ),
            ]),
            why_it_matters:
                "This directly tests whether a documentation-heavy skill or harness creates workspace state the Agent later consults."
                    .into(),
            boundary:
                "A read is not proof of semantic use, and a final report may be valuable without being reread by the generating Agent."
                    .into(),
            evidence: documents
                .iter()
                .take(8)
                .filter_map(|row| {
                    row.last_mutation
                        .map(|index| evidence(trace, index, Some(&row.path)))
                })
                .collect(),
        });
    }

    let external_sessions = sessions
        .values()
        .filter(|session| !session.workspace_session)
        .collect::<Vec<_>>();
    if !external_sessions.is_empty() {
        let mut externally_reused = artifacts
            .iter()
            .filter(|(_, artifact)| artifact.global_reads_after_first_mutation > 0)
            .collect::<Vec<_>>();
        externally_reused.sort_by_key(|(_, artifact)| {
            Reverse((
                artifact.global_reads_after_first_mutation,
                artifact.mutations,
            ))
        });
        let top = externally_reused.first().copied();
        let top_external_read_indices = top
            .into_iter()
            .flat_map(|(artifact_id, artifact)| {
                artifact.evidence.iter().copied().filter(move |index| {
                    let event = &trace.events[*index];
                    !event.workspace_session
                        && *index > artifact.first_mutation.unwrap_or(usize::MAX)
                        && event.status != "fail"
                        && event.actions.iter().any(|action| {
                            !action.scope
                                && action.access == "read"
                                && artifact_key(action) == *artifact_id
                        })
                })
            })
            .collect::<Vec<_>>();
        let mut top_reads_by_session = BTreeMap::<String, usize>::new();
        let mut top_reader_source_files = BTreeSet::<String>::new();
        for index in &top_external_read_indices {
            let event = &trace.events[*index];
            *top_reads_by_session
                .entry(event.native_session_id.clone())
                .or_default() += 1;
            top_reader_source_files.insert(event.source_file.clone());
        }
        let top_session_read_counts = top_reads_by_session.values().copied().collect::<Vec<_>>();
        let all_external_reads = externally_reused
            .iter()
            .map(|(_, artifact)| artifact.global_reads_after_first_mutation)
            .sum::<usize>();
        result.push(Pattern {
            kind: "external-workspace-reuse".into(),
            title: "Global mode identifies root-external exact-path access".into(),
            facts: facts([
                ("external_reference_sessions", external_sessions.len().to_string()),
                (
                    "external_sessions_with_reads_and_no_observed_mutation_effect",
                    external_sessions
                        .iter()
                        .filter(|session| {
                            session.reads > 0
                                && session.mutations == 0
                                && session.attempted_mutations == 0
                        })
                        .count()
                        .to_string(),
                ),
                (
                    "external_sessions_with_observed_mutation_effects",
                    external_sessions
                        .iter()
                        .filter(|session| {
                            session.mutations > 0 || session.attempted_mutations > 0
                        })
                        .count()
                        .to_string(),
                ),
                (
                    "artifacts_reread_from_external_sessions",
                    externally_reused.len().to_string(),
                ),
                (
                    "most_externally_reread_artifact",
                    top.map_or("—".into(), |(_, artifact)| artifact.path.clone()),
                ),
                (
                    "external_read_actions_of_top_artifact",
                    top.map_or(0, |(_, artifact)| {
                        artifact.global_reads_after_first_mutation
                    })
                        .to_string(),
                ),
                (
                    "root_external_native_sessions_reading_top_artifact",
                    top_reads_by_session.len().to_string(),
                ),
                (
                    "native_source_files_reading_top_artifact",
                    top_reader_source_files.len().to_string(),
                ),
                (
                    "median_top_artifact_reads_per_root_external_session",
                    (!top_session_read_counts.is_empty())
                        .then(|| median(&top_session_read_counts).to_string())
                        .unwrap_or_else(|| "—".into()),
                ),
                (
                    "maximum_top_artifact_reads_in_one_root_external_session",
                    top_session_read_counts
                        .iter()
                        .max()
                        .map_or_else(|| "—".into(), usize::to_string),
                ),
                (
                    "top_artifact_share_of_external_read_actions",
                    if all_external_reads == 0 {
                        "—".into()
                    } else {
                        format!(
                            "{:.1}%",
                            top_external_read_indices.len() as f64 * 100.0
                                / all_external_reads as f64
                        )
                    },
                ),
            ]),
            why_it_matters:
                "This identifies skills, instructions, reports, and other workspace artifacts that later Agent sessions rooted elsewhere access or attempt to change. Read-only external roots stay out of the mutation-driven evolution sequence; roots that mutate the repository remain evolution evidence."
                    .into(),
            boundary:
                "Admission requires an exact repository-path match in a native Tool call. Root-external can include a delegated subagent intentionally editing this repository; it does not imply an independent consumer, semantic reuse, or influence. Status remains observed when the native adapter cannot pair a Tool result."
                    .into(),
            evidence: top_external_read_indices
                .into_iter()
                .take(8)
                .map(|index| {
                    evidence(
                        trace,
                        index,
                        top.map(|(_, artifact)| artifact.path.as_str()),
                    )
                })
                .collect(),
        });
    }

    if let Some(longest) = read_spans.iter().find(|span| span.ended_by_mutation) {
        result.push(Pattern {
            kind: "exploration-span".into(),
            title: "The longest observed read/search span before a confirmed mutation is identifiable"
                .into(),
            facts: facts([
                (
                    "mutation_closed_read_spans",
                    read_spans
                        .iter()
                        .filter(|span| span.ended_by_mutation)
                        .count()
                        .to_string(),
                ),
                ("longest_span_tool_events", longest.tool_events.to_string()),
                (
                    "longest_span_read_tool_calls",
                    longest.read_tool_calls.to_string(),
                ),
                ("longest_span_file_reads", longest.file_reads.to_string()),
                (
                    "longest_span_distinct_artifacts",
                    longest.distinct_artifacts.to_string(),
                ),
                ("session", longest.session_id.clone()),
            ]),
            why_it_matters:
                "This points to the exact exploration episode to inspect when deciding whether the Agent was learning, lost, or constrained by the harness."
                    .into(),
            boundary:
                "Spans are ranked by read Tool calls, then file effects and distinct artifacts. Total Tool events also includes non-read actions; the span is not labelled anomalous."
                    .into(),
            evidence: [longest.start, longest.end]
                .into_iter()
                .map(|index| evidence(trace, index, None))
                .collect(),
        });
    }
    if let Some(longest) = read_spans
        .iter()
        .filter(|span| !span.ended_by_mutation)
        .max_by_key(|span| {
            (
                span.read_tool_calls,
                span.file_reads,
                span.distinct_artifacts,
            )
        })
    {
        result.push(Pattern {
            kind: "open-exploration-span".into(),
            title: "An open read/search span remains at the observation cutoff".into(),
            facts: facts([
                (
                    "open_spans",
                    read_spans
                        .iter()
                        .filter(|span| !span.ended_by_mutation)
                        .count()
                        .to_string(),
                ),
                ("longest_open_read_tool_calls", longest.read_tool_calls.to_string()),
                ("longest_open_file_reads", longest.file_reads.to_string()),
                (
                    "longest_open_distinct_artifacts",
                    longest.distinct_artifacts.to_string(),
                ),
                ("session", longest.session_id.clone()),
            ]),
            why_it_matters:
                "This points to work that was still exploring, inspecting, or consuming the workspace when the available record ended."
                    .into(),
            boundary:
                "Open means no later confirmed mutation was observed before this source snapshot ended; it is not evidence of abandonment or failure."
                    .into(),
            evidence: [longest.start, longest.end]
                .into_iter()
                .map(|index| evidence(trace, index, None))
                .collect(),
        });
    }

    if !skills.is_empty() {
        let top = &skills[0];
        result.push(Pattern {
            kind: "skill-footprint".into(),
            title: "Explicit Skill use can be related to the work performed in the same sessions"
                .into(),
            facts: facts([
                ("skills_observed", skills.len().to_string()),
                ("most_observed_skill", top.skill.clone()),
                ("sessions", top.sessions.to_string()),
                (
                    "documentation_mutations_in_sessions",
                    top.documentation_mutations_in_those_sessions.to_string(),
                ),
                (
                    "confirmed_mutations_in_sessions",
                    top.confirmed_mutations_in_those_sessions.to_string(),
                ),
                (
                    "successful_validations_in_sessions",
                    top.validations_in_those_sessions.to_string(),
                ),
            ]),
            why_it_matters:
                "The footprint makes skill/harness overhead inspectable before any controlled causal experiment."
                    .into(),
            boundary:
                "Same-session association is not a causal effect and sessions can invoke several skills."
                    .into(),
            evidence: trace
                .events
                .iter()
                .enumerate()
                .filter(|(_, event)| {
                    event.skill_name.as_deref() == Some(&top.skill)
                        || event.attribution_skill.as_deref() == Some(&top.skill)
                })
                .take(8)
                .map(|(index, _)| evidence(trace, index, None))
                .collect(),
        });
    }
    result
}

/// Put takeover and audit entry points first. This affects presentation only;
/// every relation is still computed and emitted.
fn pattern_priority(kind: &str) -> usize {
    match kind {
        "action-strategy" => 0,
        "cross-session-validation-carryover" => 1,
        "cross-session-repeated-mutation" => 2,
        "validation-lag" => 3,
        "external-workspace-reuse" => 4,
        "validation-repetition" => 5,
        "module-migration" => 6,
        "pre-mutation-inspection" => 7,
        "artifact-reaccess-after-session-gap" => 8,
        "documentation-reuse" => 9,
        "unrevisited-created-artifacts" => 10,
        "exploration-span" => 11,
        "open-exploration-span" => 12,
        "skill-footprint" => 13,
        _ => usize::MAX,
    }
}

fn render_markdown(brief: &Brief) -> String {
    let mut out = String::new();
    out.push_str(&format!(
        "# Workspace trajectory brief: {}\n\n",
        brief.repository
    ));
    out.push_str(&format!(
        "Revision `{}`; source snapshot `{}`; Agent-action time `{}`–`{}` ms.\n\n",
        brief.revision,
        brief.source_snapshot_id,
        brief.observation_start_ms,
        brief.observation_end_ms
    ));
    out.push_str(
        "> Reader contract: counts and relations below are computed from normalized native Tool effects. Interpret the evidence; do not infer intent, causality, correctness, or waste from a signal alone. Every candidate pattern states its boundary.\n\n",
    );
    out.push_str(
        "> Agent workflow: start with the first candidate patterns, follow their cited transcript/Tool-call anchors, and report observed facts, source-supported interpretation, and remaining uncertainty separately.\n\n",
    );
    out.push_str("## Coverage\n\n");
    out.push_str(&format!(
        "{} included native sessions ({} workspace, {} external exact-path references under `--global`) / {} directly parsed transcript files / {} direct candidates; {} parsed native Tool/LLM records before copied-transcript dedup; {} unique retained Tool calls; {} file actions; {} confirmed mutations; {} attempted/unknown mutations; {} successful and {} failed recognized validations.\n\n",
        brief.coverage.included_sessions,
        brief.coverage.workspace_sessions,
        brief.coverage.global_reference_sessions,
        brief.coverage.parsed_sessions,
        brief.coverage.candidate_sessions,
        brief.coverage.source_events,
        brief.coverage.tool_events,
        brief.coverage.file_actions,
        brief.coverage.confirmed_file_mutations,
        brief.coverage.attempted_or_unknown_file_mutations,
        brief.coverage.successful_validations,
        brief.coverage.failed_validations,
    ));

    out.push_str("## Candidate process patterns\n\n");
    for pattern in &brief.patterns {
        out.push_str(&format!("### {}\n\n", pattern.title));
        out.push_str(&format!("Kind: `{}`\n\n", pattern.kind));
        for (key, value) in &pattern.facts {
            out.push_str(&format!("- `{key}`: {value}\n"));
        }
        out.push_str(&format!(
            "\nWhy inspect it: {}\n\nBoundary: {}\n\n",
            pattern.why_it_matters, pattern.boundary
        ));
        if !pattern.evidence.is_empty() {
            out.push_str("Evidence:\n\n");
            for item in &pattern.evidence {
                out.push_str(&format!(
                    "- `{}` `{}` session `{}` at `{}`: {}{}; source `{}`{}{}\n",
                    item.event_id,
                    item.source_call_id,
                    item.session_id,
                    item.timestamp_ms,
                    item.operation,
                    if item.path.is_empty() {
                        String::new()
                    } else {
                        format!(" `{}`", item.path)
                    },
                    item.source_file,
                    if item.command.is_empty() {
                        String::new()
                    } else {
                        format!("; command `{}`", markdown_cell(&item.command, 140))
                    },
                    if item.prompt_preview.is_empty() {
                        String::new()
                    } else {
                        format!(
                            "; user context “{}”",
                            markdown_cell(&item.prompt_preview, 180)
                        )
                    },
                ));
            }
            out.push('\n');
        }
    }

    if !brief.cross_session_change_handoffs.is_empty() {
        out.push_str("## Cross-session change handoff queue\n\n");
        out.push_str(&format!(
            "{} mutation generations crossed their producing native-session end; showing 20 open or most recent relations. A `worktree-validation-observed` outcome is a later temporal association, not file-level coverage proof. The JSON output retains every row.\n\n",
            brief.cross_session_change_handoffs.len()
        ));
        out.push_str("| Artifact | Mutation session/event | Outcome | Resolution session/event |\n|---|---|---|---|\n");
        for row in brief.cross_session_change_handoffs.iter().take(20) {
            out.push_str(&format!(
                "| `{}` | `{}` / `{}` | {} | {} |\n",
                markdown_cell(&row.path, 60),
                markdown_cell(&row.mutation_session, 30),
                row.mutation_event_id,
                row.outcome,
                if row.resolution_event_id.is_empty() {
                    "—".to_string()
                } else {
                    format!(
                        "`{}` / `{}`",
                        markdown_cell(&row.resolution_session, 30),
                        row.resolution_event_id
                    )
                }
            ));
        }
        out.push('\n');
    }

    out.push_str("## Activity by artifact kind\n\n");
    out.push_str("| Kind | Reads | Confirmed mutations | Artifacts | Sessions |\n|---|---:|---:|---:|---:|\n");
    for row in &brief.activity_by_kind {
        out.push_str(&format!(
            "| {} | {} | {} | {} | {} |\n",
            row.kind, row.reads, row.confirmed_mutations, row.artifacts, row.sessions
        ));
    }

    out.push_str("\n## Module attention\n\n");
    out.push_str(&format!(
        "Showing the 20 highest-activity modules out of {}. The JSON output retains every row.\n\n",
        brief.modules.len()
    ));
    out.push_str("| Module | Reads | Confirmed mutations | Attempted/unknown | Artifacts | Sessions |\n|---|---:|---:|---:|---:|---:|\n");
    for row in brief.modules.iter().take(20) {
        out.push_str(&format!(
            "| {} | {} | {} | {} | {} | {} |\n",
            markdown_cell(&row.module, 60),
            row.reads,
            row.confirmed_mutations,
            row.attempted_or_unknown_mutations,
            row.artifacts,
            row.sessions
        ));
    }

    out.push_str("\n## Native sessions\n\n");
    let notable = notable_sessions(&brief.sessions, 20);
    out.push_str(&format!(
        "Showing {} high-grounding or high-mutation sessions out of {}. The JSON output retains every row.\n\n",
        notable.len(),
        brief.sessions.len()
    ));
    out.push_str("| # | Origin | Vendor | Tools | Reads | Mutations | Tests ok/fail | Dominant module | Read calls/file effects before first mutation | Prior-artifact effects |\n|---:|---|---|---:|---:|---:|---:|---|---:|---:|\n");
    for row in notable {
        out.push_str(&format!(
            "| {} | {} | {} | {} | {} | {} | {}/{} | {} | {}/{} | {} |\n",
            row.ordinal,
            if row.workspace_session {
                "workspace"
            } else {
                "external mutation"
            },
            row.vendor,
            row.tool_events,
            row.file_reads,
            row.confirmed_mutations,
            row.successful_validations,
            row.failed_validations,
            markdown_cell(&row.dominant_module, 45),
            row.read_tool_calls_before_first_confirmed_mutation,
            row.reads_before_first_confirmed_mutation,
            row.prior_artifact_reads_before_first_mutation,
        ));
    }

    if !brief.session_transitions.is_empty() {
        out.push_str("\n## Cross-session module transitions\n\n");
        let mut transitions = brief.session_transitions.iter().collect::<Vec<_>>();
        transitions.sort_by(|left, right| {
            right
                .module_js_divergence
                .total_cmp(&left.module_js_divergence)
                .then_with(|| right.return_gap_sessions.cmp(&left.return_gap_sessions))
        });
        out.push_str(&format!(
            "Showing the 20 largest focus shifts out of {} file-active session transitions. The JSON output retains every row.\n\n",
            transitions.len()
        ));
        out.push_str(
            "| From → to | Dominant module | JSD | Return after gap |\n|---|---|---:|---|\n",
        );
        for row in transitions.into_iter().take(20) {
            out.push_str(&format!(
                "| `{}` → `{}` | {} → {} | {:.3} | {} |\n",
                markdown_cell(&row.from_session, 32),
                markdown_cell(&row.to_session, 32),
                markdown_cell(&row.from_dominant_module, 30),
                markdown_cell(&row.to_dominant_module, 30),
                row.module_js_divergence,
                if row.returned_module.is_empty() {
                    "—".to_string()
                } else {
                    format!(
                        "{} ({} sessions)",
                        row.returned_module, row.return_gap_sessions
                    )
                }
            ));
        }
    }

    if !brief.skills.is_empty() {
        out.push_str("\n## Skill-associated session footprint\n\n");
        out.push_str("| Skill | Explicit | Attributed | Sessions | Reads | Mutations | Doc mutations | Validations |\n|---|---:|---:|---:|---:|---:|---:|---:|\n");
        for row in &brief.skills {
            out.push_str(&format!(
                "| {} | {} | {} | {} | {} | {} | {} | {} |\n",
                markdown_cell(&row.skill, 50),
                row.explicit_invocations,
                row.attributed_events,
                row.sessions,
                row.repository_reads_in_those_sessions,
                row.confirmed_mutations_in_those_sessions,
                row.documentation_mutations_in_those_sessions,
                row.validations_in_those_sessions,
            ));
        }
    }

    out.push_str(
        "\n## Classification\n\n`documentation` includes Markdown, reStructuredText, LaTeX, bibliography, and paths under docs/paper/manuscript. `data/result` includes common data, image, log, metric, output, and result paths. `generated/scratch` includes build/cache/virtual-environment/scratch directories and compiled objects. `test` is path-based. Directory-scope shell arguments are excluded from file/artifact counts. A mutation is confirmed only when its native Tool result is `ok`; attempted or unknown effects are reported separately.\n",
    );
    out
}

fn is_mutation(action: &FileAction) -> bool {
    matches!(
        action.access.as_str(),
        "write" | "create" | "rename" | "delete"
    ) && !action.scope
}

fn artifact_key(action: &FileAction) -> String {
    format!("{}\u{1f}{}", action.worktree_id, action.artifact_id)
}

fn source_snapshot_id(trace: &RepositoryTrace) -> String {
    let mut digest = Sha256::new();
    hash_field(&mut digest, &trace.revision);
    hash_field(
        &mut digest,
        if trace.global { "global" } else { "workspace" },
    );
    for count in [
        trace.worktree_count,
        trace.candidate_session_count,
        trace.parsed_session_count,
        trace.session_count,
        trace.source_event_count,
        trace.file_action_count,
    ] {
        hash_field(&mut digest, &count.to_string());
    }
    for event in &trace.events {
        hash_field(&mut digest, &event.id);
        hash_field(&mut digest, &event.ts_ms.to_string());
        hash_field(&mut digest, &event.status);
        hash_field(&mut digest, &event.effect);
        hash_field(&mut digest, &event.command);
        for action in &event.actions {
            hash_field(&mut digest, &action.worktree_id);
            hash_field(&mut digest, &action.artifact_id);
            hash_field(&mut digest, &action.path);
            hash_field(&mut digest, &action.access);
            hash_field(&mut digest, if action.scope { "scope" } else { "artifact" });
        }
    }
    hex::encode(digest.finalize())[..16].to_string()
}

fn hash_field(digest: &mut Sha256, value: &str) {
    digest.update((value.len() as u64).to_le_bytes());
    digest.update(value.as_bytes());
}

fn is_confirmed_mutation(event: &RepositoryEvent, action: &FileAction) -> bool {
    event.status == "ok" && is_mutation(action)
}

fn is_successful_validation(event: &RepositoryEvent) -> bool {
    event.effect == "test" && event.status == "ok"
}

fn module(path: &str) -> String {
    path.split('/')
        .find(|part| !part.is_empty())
        .unwrap_or("(root files)")
        .to_string()
}

fn artifact_kind(path: &str) -> String {
    let lower = path.to_ascii_lowercase();
    let extension = Path::new(&lower)
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("");
    let parts = lower.split('/').collect::<Vec<_>>();
    if parts.iter().any(|part| {
        matches!(
            *part,
            "target"
                | "node_modules"
                | ".cache"
                | ".venv"
                | "__pycache__"
                | "dist"
                | "build"
                | "scratch"
                | "scratchpad"
        )
    }) || ["o", "a", "so", "dylib", "dll", "class", "pyc"].contains(&extension)
    {
        "generated/scratch"
    } else if parts
        .iter()
        .any(|part| matches!(*part, "test" | "tests" | "spec" | "specs"))
        || lower.contains("_test.")
        || lower.contains(".test.")
        || lower.contains(".spec.")
    {
        "test"
    } else if ["md", "mdx", "rst", "tex", "bib", "typ", "adoc"].contains(&extension)
        || parts
            .iter()
            .any(|part| matches!(*part, "docs" | "doc" | "paper" | "papers" | "manuscript"))
    {
        "documentation"
    } else if [
        "csv", "tsv", "jsonl", "parquet", "arrow", "png", "jpg", "jpeg", "gif", "svg", "pdf",
        "log", "out", "prof", "trace",
    ]
    .contains(&extension)
        || parts.iter().any(|part| {
            matches!(
                *part,
                "data" | "dataset" | "datasets" | "result" | "results" | "output" | "outputs"
            )
        })
    {
        "data/result"
    } else if [
        "rs", "c", "cc", "cpp", "h", "hpp", "py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "go",
        "java", "kt", "swift", "rb", "php", "sh", "bash", "zsh", "lua", "r",
    ]
    .contains(&extension)
    {
        "code"
    } else if [
        "toml", "yaml", "yml", "json", "ini", "cfg", "conf", "lock", "nix",
    ]
    .contains(&extension)
        || matches!(
            lower.rsplit('/').next().unwrap_or(""),
            "makefile" | "dockerfile" | ".gitignore" | ".gitattributes"
        )
    {
        "configuration"
    } else {
        "other"
    }
    .to_string()
}

fn dominant_module(modules: &BTreeMap<String, usize>) -> String {
    modules
        .iter()
        .max_by_key(|(name, count)| (**count, Reverse((*name).clone())))
        .map_or_else(|| "—".into(), |(name, _)| name.clone())
}

fn js_divergence(left: &BTreeMap<String, usize>, right: &BTreeMap<String, usize>) -> f64 {
    let keys = left.keys().chain(right.keys()).collect::<BTreeSet<_>>();
    let left_total = left.values().sum::<usize>() as f64;
    let right_total = right.values().sum::<usize>() as f64;
    if left_total == 0.0 || right_total == 0.0 {
        return 0.0;
    }
    keys.into_iter()
        .map(|key| {
            let p = *left.get(key).unwrap_or(&0) as f64 / left_total;
            let q = *right.get(key).unwrap_or(&0) as f64 / right_total;
            let m = (p + q) / 2.0;
            let term = |value: f64| {
                if value == 0.0 {
                    0.0
                } else {
                    value * (value / m).log2()
                }
            };
            (term(p) + term(q)) / 2.0
        })
        .sum()
}

fn test_signature(event: &RepositoryEvent) -> String {
    let value = if event.command.is_empty() {
        &event.command_name
    } else {
        &event.command
    };
    value.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn longest_identical_test_streak(trace: &RepositoryTrace, run: &TestRun) -> Vec<usize> {
    let mut best = Vec::new();
    let mut current = Vec::new();
    let mut previous = None::<(String, String)>;
    for index in &run.calls {
        let event = &trace.events[*index];
        let key = (test_signature(event), event.status.clone());
        if previous.as_ref() == Some(&key) {
            current.push(*index);
        } else {
            if current.len() > best.len() {
                best = current;
            }
            current = vec![*index];
            previous = Some(key);
        }
    }
    if current.len() > best.len() {
        best = current;
    }
    best
}

fn evidence(trace: &RepositoryTrace, index: usize, path: Option<&str>) -> Evidence {
    let event = &trace.events[index];
    let action = path
        .and_then(|path| event.actions.iter().find(|action| action.path == path))
        .or_else(|| {
            event
                .actions
                .iter()
                .find(|action| is_confirmed_mutation(event, action))
        })
        .or_else(|| event.actions.iter().find(|action| !action.scope));
    Evidence {
        event_id: event.id.clone(),
        source_call_id: event.source_call_id.clone().unwrap_or_else(|| "—".into()),
        session_id: event.native_session_id.clone(),
        timestamp_ms: event.ts_ms,
        source_file: event.source_file.clone(),
        operation: format!(
            "{}:{}:{}{}",
            event.tool_name,
            event.effect,
            event.status,
            action.map_or_else(String::new, |action| format!(" + {}", action.access))
        ),
        path: action.map_or_else(|| path.unwrap_or("").to_string(), |row| row.path.clone()),
        command: event.command.clone(),
        prompt_preview: event.prompt_preview.clone(),
    }
}

fn first_event_for_session(trace: &RepositoryTrace, session: &str) -> Option<usize> {
    trace
        .events
        .iter()
        .position(|event| event.native_session_id == session)
}

fn grounding_endpoints(trace: &RepositoryTrace, session: &SessionAgg) -> Vec<usize> {
    let boundary = session.first_mutation_index.unwrap_or(usize::MAX);
    let first_read = trace
        .events
        .iter()
        .enumerate()
        .find(|(index, event)| {
            *index < boundary
                && event.native_session_id == session.id
                && event.actions.iter().any(|action| {
                    !action.scope && action.access == "read" && event.status != "fail"
                })
        })
        .map(|(index, _)| index);
    first_read
        .into_iter()
        .chain(session.first_mutation_index)
        .collect()
}

fn facts<const N: usize>(items: [(&str, String); N]) -> BTreeMap<String, String> {
    items
        .into_iter()
        .map(|(key, value)| (key.to_string(), value))
        .collect()
}

fn notable_sessions(rows: &[SessionRow], limit: usize) -> Vec<&SessionRow> {
    let mut grounding = rows
        .iter()
        .filter(|row| is_evolution_session(row))
        .collect::<Vec<_>>();
    grounding.sort_by_key(|row| {
        Reverse((
            row.read_tool_calls_before_first_confirmed_mutation,
            row.reads_before_first_confirmed_mutation,
            row.prior_artifact_reads_before_first_mutation,
        ))
    });
    let mut mutation = rows
        .iter()
        .filter(|row| is_evolution_session(row))
        .collect::<Vec<_>>();
    mutation.sort_by_key(|row| Reverse((row.confirmed_mutations, row.tool_events)));
    let half = limit.div_ceil(2);
    let selected = grounding
        .into_iter()
        .take(half)
        .chain(mutation.into_iter().take(half))
        .map(|row| row.ordinal)
        .collect::<BTreeSet<_>>();
    let mut result = rows
        .iter()
        .filter(|row| selected.contains(&row.ordinal))
        .collect::<Vec<_>>();
    result.sort_by_key(|row| row.ordinal);
    result
}

fn median(values: &[usize]) -> usize {
    let mut sorted = values.to_vec();
    sorted.sort_unstable();
    sorted[sorted.len() / 2]
}

fn markdown_cell(value: &str, max: usize) -> String {
    let clean = value
        .replace(['\n', '\r'], " ")
        .replace('|', "\\|")
        .replace('`', "'");
    if clean.chars().count() <= max {
        clean
    } else {
        clean
            .chars()
            .take(max.saturating_sub(1))
            .collect::<String>()
            + "…"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn action(path: &str, artifact: &str, access: &str) -> FileAction {
        FileAction {
            worktree_id: "w".into(),
            path: path.into(),
            access: access.into(),
            previous_path: None,
            previous_worktree_id: None,
            scope: false,
            action_ordinal: 0,
            artifact_id: artifact.into(),
        }
    }

    fn event(
        index: usize,
        session: &str,
        ordinal: usize,
        effect: &str,
        status: &str,
        actions: Vec<FileAction>,
    ) -> RepositoryEvent {
        RepositoryEvent {
            id: format!("e{index}"),
            source_file: format!("{session}.jsonl"),
            source_call_id: Some(format!("call{index}")),
            native_session_id: session.into(),
            source_stream_id: session.into(),
            source_tool_ordinal: index,
            source_role: Some("root".into()),
            source_agent_id: None,
            session_id: session.into(),
            session_ordinal: ordinal,
            vendor: "codex".into(),
            workspace_session: true,
            ts_ms: index as i64 * 10,
            prompt_index: 0,
            prompt_preview: String::new(),
            source_event_id: None,
            parent_event_id: None,
            model: None,
            attribution_skill: None,
            attribution_agent: None,
            skill_name: None,
            skill_args: None,
            worktree_id: Some("w".into()),
            tool_name: "exec".into(),
            category: "shell".into(),
            command: effect.into(),
            command_name: effect.into(),
            effect: effect.into(),
            status: status.into(),
            source_paths: Vec::new(),
            actions,
        }
    }

    fn trace(events: Vec<RepositoryEvent>) -> RepositoryTrace {
        RepositoryTrace {
            repository: "fixture".into(),
            revision: "abc".into(),
            start_ms: 0,
            end_ms: 100,
            global: false,
            worktree_count: 1,
            candidate_session_count: 2,
            parsed_session_count: 2,
            session_count: 2,
            candidate_sessions_by_vendor: BTreeMap::new(),
            parsed_sessions_by_vendor: BTreeMap::new(),
            included_sessions_by_vendor: BTreeMap::new(),
            source_event_count: events.len(),
            file_action_count: events.iter().map(|event| event.actions.len()).sum(),
            events,
            commits_ms: Vec::new(),
        }
    }

    #[test]
    fn classifies_workspace_artifacts() {
        assert_eq!(artifact_kind("src/main.rs"), "code");
        assert_eq!(artifact_kind("tests/integration.rs"), "test");
        assert_eq!(artifact_kind("paper/main.tex"), "documentation");
        assert_eq!(artifact_kind("output/metrics.json"), "data/result");
        assert_eq!(artifact_kind("target/debug/app.o"), "generated/scratch");
        assert_eq!(artifact_kind("Cargo.toml"), "configuration");
    }

    #[test]
    fn js_divergence_preserves_identical_and_separates_disjoint_focus() {
        let a = BTreeMap::from([("src".into(), 2), ("tests".into(), 1)]);
        let b = a.clone();
        let c = BTreeMap::from([("docs".into(), 3)]);
        assert_eq!(js_divergence(&a, &b), 0.0);
        assert!((js_divergence(&a, &c) - 1.0).abs() < 1e-9);
    }

    #[test]
    fn markdown_cells_do_not_break_tables() {
        assert_eq!(markdown_cell("a|b\nc", 20), "a\\|b c");
    }

    #[test]
    fn actionable_takeover_patterns_are_presented_first() {
        assert!(pattern_priority("action-strategy") < pattern_priority("validation-lag"));
        assert!(
            pattern_priority("cross-session-validation-carryover")
                < pattern_priority("skill-footprint")
        );
    }

    #[test]
    fn validation_carryover_has_exact_mutation_and_resolution_endpoints() {
        let rows = vec![
            event(
                0,
                "s0",
                0,
                "write",
                "ok",
                vec![
                    action("src/a.rs", "a#0", "write"),
                    action("src/b.rs", "b#0", "write"),
                ],
            ),
            event(
                1,
                "s1",
                1,
                "write",
                "ok",
                vec![action("src/a.rs", "a#0", "write")],
            ),
            event(2, "s1", 1, "test", "ok", Vec::new()),
        ];
        let (summary, _, _, carryovers) = validation_summary(&trace(rows));
        assert_eq!(summary.pending_mutations_at_native_session_end, 2);
        assert_eq!(summary.mutations_superseded_in_later_native_session, 1);
        assert_eq!(summary.mutations_validated_in_later_native_session, 1);
        assert_eq!(carryovers.len(), 2);
        assert!(carryovers.iter().any(|row| {
            row.path == "src/a.rs"
                && row.outcome == "superseded"
                && row.mutation_event_id == "e0"
                && row.resolution_event_id == "e1"
        }));
        assert!(carryovers.iter().any(|row| {
            row.path == "src/b.rs"
                && row.outcome == "worktree-validation-observed"
                && row.mutation_event_id == "e0"
                && row.resolution_event_id == "e2"
        }));
    }

    #[test]
    fn external_read_only_sessions_do_not_distort_evolution_transitions() {
        let first = event(
            0,
            "workspace-a",
            0,
            "write",
            "ok",
            vec![action("src/a.rs", "a#0", "write")],
        );
        let mut consumer = event(
            1,
            "consumer",
            1,
            "read",
            "ok",
            vec![action("docs/guide.md", "guide#0", "read")],
        );
        consumer.workspace_session = false;
        let second = event(
            2,
            "workspace-b",
            2,
            "write",
            "ok",
            vec![action("tests/a.rs", "test#0", "write")],
        );
        let brief = analyze(&trace(vec![first, consumer, second]));
        assert_eq!(brief.coverage.workspace_sessions, 2);
        assert_eq!(brief.coverage.global_reference_sessions, 1);
        assert_eq!(brief.session_transitions.len(), 1);
        assert_eq!(brief.session_transitions[0].from_session, "workspace-a");
        assert_eq!(brief.session_transitions[0].to_session, "workspace-b");
    }

    #[test]
    fn worktrees_do_not_share_artifact_or_validation_identity() {
        let left = action("src/lib.rs", "src/lib.rs#0", "write");
        let mut right = left.clone();
        right.worktree_id = "other".into();
        let mut validation = event(2, "s1", 1, "test", "ok", Vec::new());
        validation.worktree_id = Some("other".into());
        let (summary, _, _, _) = validation_summary(&trace(vec![
            event(0, "s0", 0, "write", "ok", vec![left]),
            event(1, "s1", 1, "write", "ok", vec![right]),
            validation,
        ]));
        assert_eq!(summary.mutations_followed_by_successful_validation, 1);
        assert_eq!(summary.mutations_without_later_successful_validation, 1);
    }

    #[test]
    fn unknown_worktree_validations_do_not_form_cross_session_runs() {
        let mut first = event(0, "s0", 0, "test", "ok", Vec::new());
        first.worktree_id = None;
        let mut second = event(1, "s1", 1, "test", "ok", Vec::new());
        second.worktree_id = None;
        let (summary, _, runs, _) = validation_summary(&trace(vec![first, second]));
        assert_eq!(
            summary.repeated_validation_calls_without_confirmed_mutation,
            0
        );
        assert!(runs.is_empty());
    }

    #[test]
    fn source_snapshot_fingerprint_is_stable_and_content_sensitive() {
        let first = trace(vec![event(
            0,
            "s0",
            0,
            "write",
            "ok",
            vec![action("src/a.rs", "a#0", "write")],
        )]);
        let mut changed = first.clone();
        changed.events[0].status = "fail".into();
        assert_eq!(source_snapshot_id(&first), source_snapshot_id(&first));
        assert_ne!(source_snapshot_id(&first), source_snapshot_id(&changed));
    }

    #[test]
    fn strategy_profile_preserves_test_before_edit_and_edit_test_cycles() {
        let rows = vec![
            event(0, "s0", 0, "test", "ok", Vec::new()),
            event(
                1,
                "s0",
                0,
                "write",
                "ok",
                vec![action("src/a.rs", "a#0", "write")],
            ),
            event(2, "s0", 0, "test", "ok", Vec::new()),
            event(
                3,
                "s0",
                0,
                "write",
                "ok",
                vec![action("src/a.rs", "a#0", "write")],
            ),
        ];
        let brief = analyze(&trace(rows));
        let pattern = brief
            .patterns
            .iter()
            .find(|pattern| pattern.kind == "action-strategy")
            .expect("strategy pattern");
        assert_eq!(
            pattern.facts["sessions_with_validation_before_first_mutation"],
            "1"
        );
        assert_eq!(
            pattern.facts["collapsed_transition_mutation_to_validation"],
            "1"
        );
        assert_eq!(
            pattern.facts["collapsed_transition_validation_to_mutation"],
            "2"
        );
        assert_eq!(
            pattern.facts["open_mutation_bursts_at_session_or_snapshot_end"],
            "1"
        );
    }
}
