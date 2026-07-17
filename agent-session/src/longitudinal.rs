// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-scoped longitudinal export across native agent sessions and Git.

use chrono::{DateTime, SecondsFormat, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fmt;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command;

use crate::{
    AgentSession, EditSummary, discover_session_files, parse_session_content, parse_session_file,
    parse_session_path, session_candidate_from_path, short_hash,
};

const RETRIEVAL_BEFORE_MS: i64 = 15 * 60 * 1_000;
const RETRIEVAL_AFTER_MS: i64 = 24 * 60 * 60 * 1_000;
const AUDIT_BEFORE_MS: i64 = 24 * 60 * 60 * 1_000;
const AUDIT_AFTER_MS: i64 = 7 * 24 * 60 * 60 * 1_000;

#[derive(Debug)]
pub struct ExportError(String);

impl ExportError {
    fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

impl fmt::Display for ExportError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for ExportError {}

#[derive(Debug, Clone)]
pub struct LongitudinalOptions {
    pub repo: PathBuf,
    pub head: Option<String>,
    pub since_ms: i64,
    pub until_ms: i64,
    pub session_paths: Vec<PathBuf>,
    pub include_git_history: bool,
    pub include_git_details: bool,
    pub include_global_events: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LongitudinalArtifact {
    pub schema: String,
    pub repository: RepositorySummary,
    pub window: ExportWindow,
    pub summary: ArtifactSummary,
    pub sessions: Vec<SessionSummary>,
    pub events: Vec<NormalizedEvent>,
    pub commits: Vec<GitCommit>,
    pub changes: Vec<GitChange>,
    pub file_lifetimes: Vec<FileLifetime>,
    pub associations: Vec<EventAssociation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositorySummary {
    pub name: String,
    pub head: String,
    pub root_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportWindow {
    pub since_ms: i64,
    pub until_ms: i64,
    pub since: String,
    pub until: String,
    pub audit_since_ms: i64,
    pub audit_until_ms: i64,
    pub retrieval_before_ms: i64,
    pub retrieval_after_ms: i64,
    #[serde(default)]
    pub global: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ArtifactSummary {
    pub session_count: usize,
    pub event_count: usize,
    pub path_resolvable_event_count: usize,
    pub write_event_path_count: usize,
    pub commit_count: usize,
    pub change_count: usize,
    pub lifetime_count: usize,
    pub surviving_lifetime_count: usize,
    pub association_none_count: usize,
    pub association_unique_count: usize,
    pub association_ambiguous_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionSummary {
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub conversation_id: Option<String>,
    pub vendor: String,
    pub model: Option<String>,
    pub started_at_ms: Option<i64>,
    pub ended_at_ms: Option<i64>,
    pub tool_events: usize,
    pub total_tokens: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NormalizedEvent {
    pub id: String,
    pub session_id: String,
    pub vendor: String,
    pub model: Option<String>,
    pub ts_ms: i64,
    pub kind: String,
    pub action: String,
    pub category: String,
    pub effect: String,
    pub status: String,
    pub prompt_index: usize,
    pub paths: Vec<String>,
    #[serde(default)]
    pub read_paths: Vec<String>,
    #[serde(default)]
    pub write_paths: Vec<String>,
    pub path_groups: Vec<String>,
    #[serde(default)]
    pub process_chain: Vec<String>,
    #[serde(default)]
    pub domains: Vec<String>,
    pub edit_summary: Option<EditSummary>,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_tokens: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitCommit {
    pub id: String,
    pub parents: Vec<String>,
    pub committed_at_ms: i64,
    pub author_label: String,
    pub is_merge: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HunkFingerprint {
    pub before_hash: Option<String>,
    pub after_hash: Option<String>,
    pub removed_lines: u64,
    pub added_lines: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitChange {
    pub id: String,
    pub commit_id: String,
    pub committed_at_ms: i64,
    pub status: String,
    pub old_path: Option<String>,
    pub path: String,
    pub additions: u64,
    pub deletions: u64,
    pub lifetime_id: String,
    pub is_merge: bool,
    pub hunks: Vec<HunkFingerprint>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileLifetime {
    pub id: String,
    pub paths: Vec<String>,
    pub birth_commit: String,
    pub birth_ms: i64,
    pub death_commit: Option<String>,
    pub death_ms: Option<i64>,
    pub current_path: Option<String>,
    pub current_bytes: Option<u64>,
    pub survives_to_head: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CandidateAssociation {
    pub change_id: String,
    pub commit_id: String,
    pub lifetime_id: String,
    pub rank: usize,
    pub delta_ms: i64,
    pub match_kind: String,
    pub exact_hunk_match: bool,
    pub evidence_bin: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventAssociation {
    pub id: String,
    pub event_id: String,
    pub path: String,
    pub state: String,
    pub candidates: Vec<CandidateAssociation>,
}

#[derive(Debug)]
struct CommitRecord {
    commit: GitCommit,
    all_changes: Vec<GitChange>,
}

#[derive(Debug)]
struct LifetimeBuilder {
    lifetime: FileLifetime,
}

#[derive(Debug)]
struct StatusChange {
    status: String,
    old_path: Option<String>,
    path: String,
}

pub fn build_longitudinal_artifact(
    options: &LongitudinalOptions,
) -> Result<LongitudinalArtifact, ExportError> {
    if options.until_ms <= options.since_ms {
        return Err(ExportError::new("--until must be after --since"));
    }
    let repo = options
        .repo
        .canonicalize()
        .map_err(|error| ExportError::new(format!("cannot resolve repository: {error}")))?;
    ensure_git_repo(&repo)?;
    let revision = options.head.as_deref().unwrap_or("HEAD");
    let head = git_text(&repo, &["rev-parse", "--verify", revision])?
        .trim()
        .to_string();
    let audit_since_ms = options.since_ms.saturating_sub(AUDIT_BEFORE_MS);
    let audit_until_ms = options.until_ms.saturating_add(AUDIT_AFTER_MS);

    let (commit_records, mut lifetimes) = if options.include_git_history {
        collect_git_history(
            &repo,
            &head,
            audit_since_ms,
            audit_until_ms,
            options.include_git_details,
        )?
    } else {
        (Vec::new(), Vec::new())
    };
    let mut commits = Vec::new();
    let mut changes = Vec::new();
    for record in commit_records {
        if (audit_since_ms..audit_until_ms).contains(&record.commit.committed_at_ms) {
            commits.push(record.commit);
            changes.extend(record.all_changes);
        }
    }
    if options.include_git_history {
        let current_sizes = current_blob_sizes(&repo, &head)?;
        for lifetime in &mut lifetimes {
            if let Some(path) = &lifetime.current_path {
                lifetime.current_bytes = current_sizes.get(path).copied();
                lifetime.survives_to_head = current_sizes.contains_key(path);
            }
        }
    }

    let sessions = load_sessions(options, &repo)?;
    let (session_summaries, mut events) = normalize_sessions(&repo, sessions, options);
    events.sort_by(|left, right| {
        left.ts_ms
            .cmp(&right.ts_ms)
            .then_with(|| left.id.cmp(&right.id))
    });
    let associations = associate_events(&events, &changes, &lifetimes);

    let mut summary = ArtifactSummary {
        session_count: session_summaries.len(),
        event_count: events.len(),
        path_resolvable_event_count: events
            .iter()
            .filter(|event| !event.paths.is_empty())
            .count(),
        write_event_path_count: associations.len(),
        commit_count: commits.len(),
        change_count: changes.len(),
        lifetime_count: lifetimes.len(),
        surviving_lifetime_count: lifetimes
            .iter()
            .filter(|lifetime| lifetime.survives_to_head)
            .count(),
        ..ArtifactSummary::default()
    };
    for association in &associations {
        match association.state.as_str() {
            "no_candidate" => summary.association_none_count += 1,
            "unique_candidate" => summary.association_unique_count += 1,
            "ambiguous_candidates" => summary.association_ambiguous_count += 1,
            _ => {}
        }
    }

    Ok(LongitudinalArtifact {
        schema: "agentsight.longitudinal.v1".to_string(),
        repository: RepositorySummary {
            name: repo
                .file_name()
                .and_then(|name| name.to_str())
                .unwrap_or("repository")
                .to_string(),
            head: head.clone(),
            root_id: short_hash(repo.to_string_lossy().as_ref(), 16),
        },
        window: ExportWindow {
            since_ms: options.since_ms,
            until_ms: options.until_ms,
            since: format_timestamp(options.since_ms),
            until: format_timestamp(options.until_ms),
            audit_since_ms,
            audit_until_ms,
            retrieval_before_ms: RETRIEVAL_BEFORE_MS,
            retrieval_after_ms: RETRIEVAL_AFTER_MS,
            global: options.include_global_events,
        },
        summary,
        sessions: session_summaries,
        events,
        commits,
        changes,
        file_lifetimes: lifetimes,
        associations,
    })
}

pub fn write_longitudinal_artifact(
    artifact: &LongitudinalArtifact,
    output: &Path,
) -> Result<(), ExportError> {
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            ExportError::new(format!("cannot create {}: {error}", parent.display()))
        })?;
    }
    let file_name = output
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("artifact.json");
    let temporary = output.with_file_name(format!(".{file_name}.tmp-{}", std::process::id()));
    let mut file = fs::File::create(&temporary).map_err(|error| {
        ExportError::new(format!("cannot create {}: {error}", temporary.display()))
    })?;
    serde_json::to_writer_pretty(&mut file, artifact)
        .map_err(|error| ExportError::new(format!("cannot serialize artifact: {error}")))?;
    file.write_all(b"\n")
        .and_then(|_| file.sync_all())
        .map_err(|error| ExportError::new(format!("cannot flush artifact: {error}")))?;
    fs::rename(&temporary, output).map_err(|error| {
        ExportError::new(format!(
            "cannot move {} to {}: {error}",
            temporary.display(),
            output.display()
        ))
    })
}

fn ensure_git_repo(repo: &Path) -> Result<(), ExportError> {
    let inside = git_text(repo, &["rev-parse", "--is-inside-work-tree"])?;
    if inside.trim() != "true" {
        return Err(ExportError::new(format!(
            "{} is not a Git worktree",
            repo.display()
        )));
    }
    Ok(())
}

fn collect_git_history(
    repo: &Path,
    head: &str,
    audit_since_ms: i64,
    audit_until_ms: i64,
    include_details: bool,
) -> Result<(Vec<CommitRecord>, Vec<FileLifetime>), ExportError> {
    let output = git_bytes(
        repo,
        &[
            "log",
            "--first-parent",
            "--reverse",
            "--format=%H%x1f%P%x1f%ct%x1f%an%x1e",
            head,
        ],
    )?;
    let mut records = Vec::new();
    let mut active = HashMap::<String, usize>::new();
    let mut lifetimes = Vec::<LifetimeBuilder>::new();
    let mut lifetime_counter = 0usize;

    for raw_record in output.split(|byte| *byte == 0x1e) {
        let raw_record = trim_ascii(raw_record);
        if raw_record.is_empty() {
            continue;
        }
        let fields = raw_record.split(|byte| *byte == 0x1f).collect::<Vec<_>>();
        if fields.len() < 4 {
            return Err(ExportError::new("unexpected git log record"));
        }
        let id = utf8(fields[0], "commit id")?.to_string();
        let parents = utf8(fields[1], "commit parents")?
            .split_whitespace()
            .map(str::to_string)
            .collect::<Vec<_>>();
        let committed_at_ms = utf8(fields[2], "commit timestamp")?
            .parse::<i64>()
            .map_err(|error| ExportError::new(format!("invalid commit timestamp: {error}")))?
            .saturating_mul(1_000);
        let author_label = utf8(fields[3], "commit author")?.trim().to_string();
        let is_merge = parents.len() > 1;
        let statuses = commit_statuses(repo, &id, parents.first().map(String::as_str))?;
        let numstats = if include_details {
            commit_numstats(repo, &id, parents.first().map(String::as_str))?
        } else {
            HashMap::new()
        };
        let mut all_changes = Vec::new();

        for (index, status) in statuses.into_iter().enumerate() {
            let lifetime_index = apply_lifetime_change(
                &mut active,
                &mut lifetimes,
                &mut lifetime_counter,
                &status,
                &id,
                committed_at_ms,
            );
            let (additions, deletions) = numstats
                .get(&status.path)
                .or_else(|| status.old_path.as_ref().and_then(|path| numstats.get(path)))
                .copied()
                .unwrap_or((0, 0));
            let change_id = format!("{}:{index}", short_hash(&id, 12));
            let hunks =
                if include_details && (audit_since_ms..audit_until_ms).contains(&committed_at_ms) {
                    commit_hunks(
                        repo,
                        &id,
                        parents.first().map(String::as_str),
                        status.old_path.as_deref(),
                        &status.path,
                    )?
                } else {
                    Vec::new()
                };
            all_changes.push(GitChange {
                id: change_id,
                commit_id: id.clone(),
                committed_at_ms,
                status: status.status,
                old_path: status.old_path,
                path: status.path,
                additions,
                deletions,
                lifetime_id: lifetimes[lifetime_index].lifetime.id.clone(),
                is_merge,
                hunks,
            });
        }

        records.push(CommitRecord {
            commit: GitCommit {
                id,
                parents,
                committed_at_ms,
                author_label,
                is_merge,
            },
            all_changes,
        });
    }

    Ok((
        records,
        lifetimes
            .into_iter()
            .map(|builder| builder.lifetime)
            .collect(),
    ))
}

fn apply_lifetime_change(
    active: &mut HashMap<String, usize>,
    lifetimes: &mut Vec<LifetimeBuilder>,
    lifetime_counter: &mut usize,
    change: &StatusChange,
    commit_id: &str,
    committed_at_ms: i64,
) -> usize {
    let status = change.status.chars().next().unwrap_or('M');
    if (status == 'R' || status == 'C')
        && let Some(old_path) = &change.old_path
        && let Some(index) = active.remove(old_path)
    {
        let lifetime = &mut lifetimes[index].lifetime;
        if !lifetime.paths.contains(&change.path) {
            lifetime.paths.push(change.path.clone());
        }
        lifetime.current_path = Some(change.path.clone());
        active.insert(change.path.clone(), index);
        return index;
    }
    if status == 'D'
        && let Some(index) = active.remove(&change.path)
    {
        let lifetime = &mut lifetimes[index].lifetime;
        lifetime.death_commit = Some(commit_id.to_string());
        lifetime.death_ms = Some(committed_at_ms);
        lifetime.current_path = None;
        return index;
    }
    if status != 'A'
        && let Some(index) = active.get(&change.path).copied()
    {
        return index;
    }

    *lifetime_counter += 1;
    let index = lifetimes.len();
    lifetimes.push(LifetimeBuilder {
        lifetime: FileLifetime {
            id: format!("file-{:06}", *lifetime_counter),
            paths: vec![change.path.clone()],
            birth_commit: commit_id.to_string(),
            birth_ms: committed_at_ms,
            death_commit: None,
            death_ms: None,
            current_path: Some(change.path.clone()),
            current_bytes: None,
            survives_to_head: false,
        },
    });
    active.insert(change.path.clone(), index);
    index
}

fn commit_statuses(
    repo: &Path,
    commit: &str,
    first_parent: Option<&str>,
) -> Result<Vec<StatusChange>, ExportError> {
    let output = if let Some(parent) = first_parent {
        git_bytes(
            repo,
            &[
                "diff",
                "--name-status",
                "-z",
                "-M50%",
                "--no-ext-diff",
                parent,
                commit,
                "--",
            ],
        )?
    } else {
        git_bytes(
            repo,
            &[
                "diff-tree",
                "--root",
                "--no-commit-id",
                "-r",
                "--name-status",
                "-z",
                "-M50%",
                commit,
            ],
        )?
    };
    let tokens = nul_tokens(&output);
    let mut changes = Vec::new();
    let mut index = 0usize;
    while index < tokens.len() {
        let status = tokens[index].clone();
        index += 1;
        let kind = status.chars().next().unwrap_or('M');
        if kind == 'R' || kind == 'C' {
            if index + 1 >= tokens.len() {
                return Err(ExportError::new("truncated rename status"));
            }
            changes.push(StatusChange {
                status,
                old_path: Some(tokens[index].clone()),
                path: tokens[index + 1].clone(),
            });
            index += 2;
        } else {
            let Some(path) = tokens.get(index) else {
                return Err(ExportError::new("truncated path status"));
            };
            changes.push(StatusChange {
                status,
                old_path: None,
                path: path.clone(),
            });
            index += 1;
        }
    }
    Ok(changes)
}

fn commit_numstats(
    repo: &Path,
    commit: &str,
    first_parent: Option<&str>,
) -> Result<HashMap<String, (u64, u64)>, ExportError> {
    let output = if let Some(parent) = first_parent {
        git_bytes(
            repo,
            &[
                "diff",
                "--numstat",
                "-z",
                "-M50%",
                "--no-ext-diff",
                parent,
                commit,
                "--",
            ],
        )?
    } else {
        git_bytes(
            repo,
            &[
                "diff-tree",
                "--root",
                "--no-commit-id",
                "-r",
                "--numstat",
                "-z",
                "-M50%",
                commit,
            ],
        )?
    };
    let tokens = nul_tokens(&output);
    let mut stats = HashMap::new();
    let mut index = 0usize;
    while index < tokens.len() {
        let header = &tokens[index];
        index += 1;
        let mut fields = header.splitn(3, '\t');
        let additions = parse_numstat(fields.next().unwrap_or("0"));
        let deletions = parse_numstat(fields.next().unwrap_or("0"));
        let path = fields.next().unwrap_or("");
        if path.is_empty() && index + 1 < tokens.len() {
            let old_path = tokens[index].clone();
            let new_path = tokens[index + 1].clone();
            index += 2;
            stats.insert(old_path, (additions, deletions));
            stats.insert(new_path, (additions, deletions));
        } else if !path.is_empty() {
            stats.insert(path.to_string(), (additions, deletions));
        }
    }
    Ok(stats)
}

fn commit_hunks(
    repo: &Path,
    commit: &str,
    first_parent: Option<&str>,
    old_path: Option<&str>,
    path: &str,
) -> Result<Vec<HunkFingerprint>, ExportError> {
    let mut command = Command::new("git");
    command.arg("-C").arg(repo);
    if let Some(parent) = first_parent {
        command.args(["diff", "--unified=0", "--no-ext-diff", parent, commit, "--"]);
    } else {
        command.args([
            "show",
            "--format=",
            "--unified=0",
            "--no-ext-diff",
            commit,
            "--",
        ]);
    }
    if let Some(old_path) = old_path {
        command.arg(old_path);
    }
    command.arg(path);
    let output = command
        .output()
        .map_err(|error| ExportError::new(format!("cannot run git diff: {error}")))?;
    if !output.status.success() {
        return Err(command_error("git diff hunks", &output));
    }
    let text = String::from_utf8_lossy(&output.stdout);
    Ok(parse_hunk_fingerprints(&text))
}

fn parse_hunk_fingerprints(patch: &str) -> Vec<HunkFingerprint> {
    let mut hunks = Vec::new();
    let mut before = Vec::new();
    let mut after = Vec::new();
    let mut in_hunk = false;
    let flush =
        |before: &mut Vec<String>, after: &mut Vec<String>, hunks: &mut Vec<HunkFingerprint>| {
            if before.is_empty() && after.is_empty() {
                return;
            }
            let before_text = before.join("\n");
            let after_text = after.join("\n");
            hunks.push(HunkFingerprint {
                before_hash: (!before.is_empty()).then(|| content_fingerprint(&before_text)),
                after_hash: (!after.is_empty()).then(|| content_fingerprint(&after_text)),
                removed_lines: before.len() as u64,
                added_lines: after.len() as u64,
            });
            before.clear();
            after.clear();
        };
    for line in patch.lines() {
        if line.starts_with("@@") {
            flush(&mut before, &mut after, &mut hunks);
            in_hunk = true;
        } else if in_hunk && line.starts_with('-') && !line.starts_with("---") {
            before.push(line[1..].to_string());
        } else if in_hunk && line.starts_with('+') && !line.starts_with("+++") {
            after.push(line[1..].to_string());
        }
    }
    flush(&mut before, &mut after, &mut hunks);
    hunks
}

fn load_sessions(
    options: &LongitudinalOptions,
    repo: &Path,
) -> Result<Vec<AgentSession>, ExportError> {
    let mut sessions = Vec::new();
    let roots = worktree_roots(repo);
    let remote = git_text(repo, &["config", "--get", "remote.origin.url"])
        .ok()
        .map(|value| normalize_repository_url(value.trim()));
    if options.session_paths.is_empty() {
        for candidate in discover_session_files() {
            let updated_ms = candidate
                .updated
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis() as i64;
            // A session may start in the requested window and be resumed weeks
            // later. Its file mtime then lies after the Git audit horizon, but
            // the earlier events remain part of the longitudinal trajectory.
            if !candidate_mtime_may_contain_window(updated_ms, options.since_ms) {
                continue;
            }
            if !candidate_may_match_repo(
                candidate.agent,
                &candidate.path,
                &roots,
                remote.as_deref(),
            ) {
                continue;
            }
            if let Some(session) = parse_session_file(&candidate)
                && session_matches_repo(&session, repo, options.include_global_events)
                && session_overlaps(&session, options.since_ms, options.until_ms)
            {
                sessions.push(session);
            }
        }
        if options.include_global_events {
            let existing = sessions
                .iter()
                .map(|session| session.path.clone())
                .collect::<BTreeSet<_>>();
            sessions.extend(
                behavior_sessions(repo)
                    .into_iter()
                    .filter(|session| !existing.contains(&session.path))
                    .filter(|session| session_matches_repo(session, repo, true))
                    .filter(|session| {
                        session_overlaps(session, options.since_ms, options.until_ms)
                    }),
            );
        }
    } else {
        let worker_count = std::thread::available_parallelism()
            .map(|value| value.get())
            .unwrap_or(1)
            .min(4)
            .min(options.session_paths.len().max(1));
        let chunk_size = options.session_paths.len().div_ceil(worker_count);
        let parsed = std::thread::scope(|scope| -> Result<Vec<_>, ExportError> {
            let handles = options
                .session_paths
                .chunks(chunk_size)
                .map(|chunk| {
                    scope.spawn(move || {
                        chunk
                            .iter()
                            .map(|path| (path.clone(), parse_session_path(path)))
                            .collect::<Vec<_>>()
                    })
                })
                .collect::<Vec<_>>();
            let mut parsed = Vec::new();
            for handle in handles {
                parsed.extend(handle.join().map_err(|_| {
                    ExportError::new("session parser worker terminated unexpectedly")
                })?);
            }
            Ok(parsed)
        })?;
        for (path, parsed_session) in parsed {
            let session = parsed_session.ok_or_else(|| {
                ExportError::new(format!("cannot parse session {}", path.display()))
            })?;
            if session_matches_repo(&session, repo, options.include_global_events)
                && session_overlaps(&session, options.since_ms, options.until_ms)
            {
                sessions.push(session);
            }
        }
    }
    sessions.sort_by(|left, right| {
        left.start_timestamp_ms
            .cmp(&right.start_timestamp_ms)
            .then_with(|| left.session_id.cmp(&right.session_id))
    });
    Ok(sessions)
}

/// Extract only repository-referencing tool rows from sessions whose cwd is
/// elsewhere. Ripgrep performs the 38+ GiB transcript scan; the normal parser
/// then validates the selected native tool records.
fn behavior_sessions(repo: &Path) -> Vec<AgentSession> {
    let Some(home) = dirs::home_dir() else {
        return Vec::new();
    };
    let search_roots = [
        home.join(".claude/projects"),
        home.join(".codex/sessions"),
        home.join(".codex/archived_sessions"),
    ];
    let terms = worktree_roots(repo)
        .into_iter()
        .filter_map(|path| path.file_name()?.to_str().map(regex_literal))
        .collect::<BTreeSet<_>>();
    let mut command = Command::new("rg");
    command.args(["--json", "--no-messages", "--glob", "*.jsonl"]);
    for term in terms {
        command.args(["-e", &format!(
            r#"^\{{[^\n]{{0,2000}}"type":"response_item".*"type":"(function_call|custom_tool_call)".*{term}"#,
        )]);
        command.args([
            "-e",
            &format!(r#"^\{{[^\n]{{0,2000}}"type":"assistant".*"type":"tool_use".*{term}"#,),
        ]);
    }
    command.args(search_roots.iter().filter(|path| path.exists()));
    let Ok(output) = command.output() else {
        return Vec::new();
    };
    if !output.status.success() && output.status.code() != Some(1) {
        return Vec::new();
    }
    let mut selected = HashMap::<PathBuf, BTreeMap<u64, String>>::new();
    for line in String::from_utf8_lossy(&output.stdout).lines() {
        let Ok(row) = serde_json::from_str::<serde_json::Value>(line) else {
            continue;
        };
        if row.get("type").and_then(|value| value.as_str()) != Some("match") {
            continue;
        }
        let Some(path) = row
            .pointer("/data/path/text")
            .and_then(|value| value.as_str())
        else {
            continue;
        };
        let Some(text) = row
            .pointer("/data/lines/text")
            .and_then(|value| value.as_str())
        else {
            continue;
        };
        let line_number = row
            .pointer("/data/line_number")
            .and_then(|value| value.as_u64())
            .unwrap_or_default();
        selected
            .entry(PathBuf::from(path))
            .or_default()
            .insert(line_number, text.trim_end().to_string());
    }
    selected
        .into_iter()
        .filter_map(|(path, lines)| {
            let candidate = session_candidate_from_path(&path)?;
            let mut content = session_header(&path);
            for line in lines.into_values() {
                content.push_str(&line);
                content.push('\n');
            }
            parse_session_content(candidate.agent, &path, candidate.updated, &content)
        })
        .collect()
}

fn session_header(path: &Path) -> String {
    let Ok(mut file) = fs::File::open(path) else {
        return String::new();
    };
    let mut prefix = vec![0u8; 256 * 1024];
    let Ok(count) = file.read(&mut prefix) else {
        return String::new();
    };
    prefix.truncate(count);
    let mut output = String::new();
    let mut have_meta = false;
    let mut have_context = false;
    for line in String::from_utf8_lossy(&prefix).lines() {
        let is_meta = !have_meta && line.contains(r#""type":"session_meta""#);
        let is_context = !have_context && line.contains(r#""type":"turn_context""#);
        if is_meta || is_context {
            output.push_str(line);
            output.push('\n');
            have_meta |= is_meta;
            have_context |= is_context;
        }
        if have_meta && have_context {
            break;
        }
    }
    output
}

fn regex_literal(value: &str) -> String {
    value.chars().fold(String::new(), |mut output, ch| {
        if r#"\.^$|?*+()[]{}"#.contains(ch) {
            output.push('\\');
        }
        output.push(ch);
        output
    })
}

fn candidate_mtime_may_contain_window(updated_ms: i64, since_ms: i64) -> bool {
    updated_ms >= since_ms.saturating_sub(AUDIT_BEFORE_MS)
}

fn candidate_may_match_repo(
    agent: &str,
    path: &Path,
    roots: &[PathBuf],
    repo_remote: Option<&str>,
) -> bool {
    match agent {
        crate::AGENT_CLAUDE => {
            let path = path.to_string_lossy();
            roots
                .iter()
                .any(|root| path.contains(&root.to_string_lossy().replace('/', "-")))
        }
        // Gemini's complete local history is small enough to validate every
        // session for cross-repository tool evidence.
        crate::AGENT_GEMINI => true,
        crate::AGENT_CODEX => codex_candidate_identity(path).is_some_and(|(cwd, remote)| {
            cwd.is_some_and(|cwd| roots.iter().any(|root| cwd.starts_with(root)))
                || remote.is_some_and(|candidate| {
                    repo_remote
                        .is_some_and(|repo_url| normalize_repository_url(&candidate) == repo_url)
                })
        }),
        _ => false,
    }
}

fn worktree_roots(repo: &Path) -> Vec<PathBuf> {
    let mut roots = vec![repo.canonicalize().unwrap_or_else(|_| repo.to_path_buf())];
    if let Ok(output) = git_text(repo, &["worktree", "list", "--porcelain"]) {
        roots.extend(output.lines().filter_map(|line| {
            line.strip_prefix("worktree ")
                .map(PathBuf::from)
                .map(|path| path.canonicalize().unwrap_or(path))
        }));
    }
    roots.sort();
    roots.dedup();
    roots
}

fn codex_candidate_identity(path: &Path) -> Option<(Option<PathBuf>, Option<String>)> {
    let mut file = fs::File::open(path).ok()?;
    let mut prefix = vec![0u8; 256 * 1024];
    let count = file.read(&mut prefix).ok()?;
    prefix.truncate(count);
    let text = String::from_utf8_lossy(&prefix);
    for line in text.lines() {
        let Ok(row) = serde_json::from_str::<serde_json::Value>(line) else {
            continue;
        };
        if row.get("type").and_then(|value| value.as_str()) != Some("session_meta") {
            continue;
        }
        let cwd = row
            .pointer("/payload/cwd")
            .and_then(|value| value.as_str())
            .map(PathBuf::from)
            .map(|value| value.canonicalize().unwrap_or(value));
        let remote = row
            .pointer("/payload/git/repository_url")
            .and_then(|value| value.as_str())
            .filter(|value| !value.is_empty())
            .map(ToString::to_string);
        return Some((cwd, remote));
    }
    None
}

fn session_matches_repo(session: &AgentSession, repo: &Path, include_global_events: bool) -> bool {
    mapped_session_cwd(session, repo).is_some()
        || include_global_events
            && session
                .events
                .tools
                .iter()
                .any(|tool| tool_repo_evidence(session.cwd.as_deref(), &tool.command, repo).0)
}

fn tool_repo_evidence(cwd: Option<&str>, command: &str, repo: &Path) -> (bool, BTreeSet<String>) {
    let roots = worktree_roots(repo);
    tool_repo_evidence_with_roots(cwd, command, &roots)
}

fn tool_repo_evidence_with_roots(
    cwd: Option<&str>,
    command: &str,
    roots: &[PathBuf],
) -> (bool, BTreeSet<String>) {
    let cwd = cwd.map(Path::new);
    let mut matched = false;
    let mut paths = BTreeSet::new();
    for raw in command.split(|ch: char| {
        ch.is_whitespace()
            || [
                '"', '\'', ';', '|', '&', '<', '>', '(', ')', '[', ']', '{', '}', ',',
            ]
            .contains(&ch)
    }) {
        let raw = raw
            .rsplit_once('=')
            .map_or(raw, |(_, value)| value)
            .trim_matches(|ch: char| ch == ':' || ch == '`');
        if raw.is_empty() || (!raw.contains('/') && !raw.starts_with('.')) {
            continue;
        }
        let path = Path::new(raw);
        let candidate = if path.is_absolute() {
            path.to_path_buf()
        } else if let Some(cwd) = cwd {
            cwd.join(path)
        } else {
            continue;
        };
        let candidate = lexical_path(&candidate);
        for root in roots {
            if !candidate.starts_with(root) {
                continue;
            }
            matched = true;
            if let Ok(relative) = candidate.strip_prefix(root)
                && let Some(path) = clean_relative_path(relative)
            {
                paths.insert(path);
            }
        }
    }
    (matched, paths)
}

fn lexical_path(path: &Path) -> PathBuf {
    let mut output = PathBuf::new();
    for component in path.components() {
        match component {
            std::path::Component::CurDir => {}
            std::path::Component::ParentDir => {
                output.pop();
            }
            _ => output.push(component.as_os_str()),
        }
    }
    output.canonicalize().unwrap_or(output)
}

fn clean_relative_path(path: &Path) -> Option<String> {
    let parts = path
        .components()
        .filter_map(|component| match component {
            std::path::Component::Normal(part) => part.to_str().map(ToString::to_string),
            _ => None,
        })
        .collect::<Vec<_>>();
    let joined = parts.join("/");
    let looks_like_phrase = parts.len() >= 3
        && parts.iter().all(|part| {
            part.chars().next().is_some_and(char::is_uppercase)
                && part.chars().all(char::is_alphabetic)
        });
    (!parts.is_empty()
        && !matches!(joined.chars().next(), Some('~' | '$'))
        && joined != "HEAD"
        && !joined.starts_with("HEAD.")
        && !joined.contains("...")
        && !looks_like_phrase
        && parts.iter().all(|part| part != ".git")
        && parts.first().is_none_or(|part| {
            !matches!(
                part.as_str(),
                "origin" | "refs" | "heads" | "tags" | "repos"
            )
        })
        && parts.iter().all(|part| {
            !part.contains(':')
                && !part.contains('\\')
                && !part.contains('`')
                && !matches!(part.as_str(), "AGENTS.md" | "CLAUDE.md")
                && !part.chars().any(|ch| {
                    ch.is_whitespace()
                        || [
                            '*', '?', '[', ']', '{', '}', '"', '#', '$', ',', ':', '@', '^', '!',
                        ]
                        .contains(&ch)
                })
        }))
    .then_some(joined)
}

fn mapped_session_cwd(session: &AgentSession, repo: &Path) -> Option<PathBuf> {
    let repo = repo.canonicalize().unwrap_or_else(|_| repo.to_path_buf());
    if let Some(cwd) = session.cwd.as_deref() {
        let cwd = Path::new(cwd);
        let canonical = cwd.canonicalize().unwrap_or_else(|_| cwd.to_path_buf());
        if canonical.starts_with(&repo) {
            return Some(canonical);
        }
        if let (Some(session_root), Some(repo_common), Some(session_common)) = (
            git_path(cwd, &["rev-parse", "--show-toplevel"]),
            git_path(&repo, &["rev-parse", "--git-common-dir"]),
            git_path(cwd, &["rev-parse", "--git-common-dir"]),
        ) && repo_common == session_common
        {
            let suffix = canonical
                .strip_prefix(session_root)
                .unwrap_or(Path::new(""));
            return Some(repo.join(suffix));
        }
    }
    let project_hash_matches = session.project_hash.as_deref()
        == Some(short_hash(repo.to_string_lossy().as_ref(), 64).as_str());
    let remote_matches = session
        .repository_url
        .as_deref()
        .is_some_and(|session_url| {
            git_text(&repo, &["config", "--get", "remote.origin.url"])
                .ok()
                .is_some_and(|repo_url| {
                    normalize_repository_url(session_url)
                        == normalize_repository_url(repo_url.trim())
                })
        });
    (project_hash_matches || remote_matches).then_some(repo)
}

fn git_path(repo: &Path, args: &[&str]) -> Option<PathBuf> {
    let value = git_text(repo, args).ok()?;
    let value = PathBuf::from(value.trim());
    let absolute = if value.is_absolute() {
        value
    } else {
        repo.join(value)
    };
    Some(absolute.canonicalize().unwrap_or(absolute))
}

fn normalize_repository_url(value: &str) -> String {
    let mut value = value
        .trim()
        .trim_end_matches('/')
        .trim_end_matches(".git")
        .to_ascii_lowercase();
    if let Some(rest) = value.strip_prefix("git@")
        && let Some((host, path)) = rest.split_once(':')
    {
        value = format!("https://{host}/{path}");
    }
    value
}

fn session_overlaps(session: &AgentSession, since_ms: i64, until_ms: i64) -> bool {
    let start = session.start_timestamp_ms.unwrap_or_default() as i64;
    let end = session.end_timestamp_ms.unwrap_or_default() as i64;
    start < until_ms && end >= since_ms
}

fn normalize_sessions(
    repo: &Path,
    sessions: Vec<AgentSession>,
    options: &LongitudinalOptions,
) -> (Vec<SessionSummary>, Vec<NormalizedEvent>) {
    let mut summaries = Vec::new();
    let mut events = Vec::new();
    let roots = worktree_roots(repo);
    for session in sessions {
        let stable_session_id = format!(
            "{}-{}",
            session.agent_type,
            short_hash(&session.session_id, 16)
        );
        let stable_conversation_id = session
            .conversation_id
            .as_deref()
            .map(|id| format!("conversation-{}", short_hash(id, 16)));
        let cwd = mapped_session_cwd(&session, repo);
        let identity_match = cwd.is_some();
        let first_event = events.len();
        for (index, tool) in session.events.tools.iter().enumerate() {
            let Some(ts_ms) = tool.ts_ms else {
                continue;
            };
            if !(options.since_ms..options.until_ms).contains(&ts_ms) {
                continue;
            }
            let behavior_paths = if identity_match {
                BTreeSet::new()
            } else if options.include_global_events {
                let (matched, paths) =
                    tool_repo_evidence_with_roots(session.cwd.as_deref(), &tool.command, &roots);
                if !matched {
                    continue;
                }
                paths
            } else {
                continue;
            };
            let mut normalized_refs = tool
                .path_refs
                .iter()
                .filter_map(|reference| {
                    cwd.as_deref().and_then(|cwd| {
                        repo_relative_session_path(repo, cwd, &reference.path)
                            .map(|path| (path, reference.access.clone()))
                    })
                })
                .collect::<BTreeSet<_>>();
            let behavior_access = if tool.effect == "write" {
                "write"
            } else if tool.effect == "read" {
                "read"
            } else {
                "reference"
            };
            normalized_refs.extend(
                behavior_paths
                    .into_iter()
                    .map(|path| (path, behavior_access.to_string())),
            );
            let paths = normalized_refs
                .iter()
                .map(|(path, _)| path.clone())
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();
            let write_paths = normalized_refs
                .iter()
                .filter(|(_, access)| *access == "write")
                .map(|(path, _)| path.clone())
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();
            let read_paths = normalized_refs
                .iter()
                .filter(|(_, access)| *access == "read")
                .map(|(path, _)| path.clone())
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();
            let path_groups = if identity_match {
                tool.path_groups.clone()
            } else {
                paths
                    .iter()
                    .map(|path| {
                        Path::new(path)
                            .parent()
                            .and_then(Path::to_str)
                            .filter(|value| !value.is_empty())
                            .unwrap_or("(root)")
                            .to_string()
                    })
                    .collect::<BTreeSet<_>>()
                    .into_iter()
                    .collect()
            };
            let id_source = format!(
                "{}:{}:{}:{}:{}",
                stable_session_id,
                ts_ms,
                tool.call_id.as_deref().unwrap_or("none"),
                tool.prompt_index,
                index
            );
            events.push(NormalizedEvent {
                id: format!("event-{}", short_hash(&id_source, 20)),
                session_id: stable_session_id.clone(),
                vendor: session.agent_type.clone(),
                model: session.model.clone(),
                ts_ms,
                kind: "tool".to_string(),
                action: tool.tool_name.clone(),
                category: tool.category.clone(),
                effect: tool.effect.clone(),
                status: tool.status.clone(),
                prompt_index: tool.prompt_index,
                paths,
                read_paths,
                write_paths,
                path_groups,
                process_chain: tool.process_chain.clone(),
                domains: tool.domains.clone(),
                edit_summary: tool.edit_summary.clone(),
                input_tokens: 0,
                output_tokens: 0,
                cache_tokens: 0,
            });
        }
        for (index, response) in session
            .events
            .llm_responses
            .iter()
            .enumerate()
            .filter(|_| identity_match)
        {
            let Some(ts_ms) = response.ts_ms else {
                continue;
            };
            if !(options.since_ms..options.until_ms).contains(&ts_ms) {
                continue;
            }
            let id_source = format!("{}:{ts_ms}:llm:{index}", stable_session_id);
            events.push(NormalizedEvent {
                id: format!("event-{}", short_hash(&id_source, 20)),
                session_id: stable_session_id.clone(),
                vendor: session.agent_type.clone(),
                model: Some(response.model.clone()),
                ts_ms,
                kind: "llm_response".to_string(),
                action: "model_response".to_string(),
                category: "model".to_string(),
                effect: "compute".to_string(),
                status: "observed".to_string(),
                prompt_index: response.prompt_index,
                paths: Vec::new(),
                read_paths: Vec::new(),
                write_paths: Vec::new(),
                path_groups: Vec::new(),
                process_chain: Vec::new(),
                domains: Vec::new(),
                edit_summary: None,
                input_tokens: response.input_tokens,
                output_tokens: response.output_tokens,
                cache_tokens: response.cache_tokens,
            });
        }
        if events.len() > first_event {
            summaries.push(SessionSummary {
                id: stable_session_id,
                conversation_id: stable_conversation_id,
                vendor: session.agent_type,
                model: session.model,
                started_at_ms: session.start_timestamp_ms.map(|value| value as i64),
                ended_at_ms: session.end_timestamp_ms.map(|value| value as i64),
                tool_events: events[first_event..]
                    .iter()
                    .filter(|event| event.kind == "tool")
                    .count(),
                total_tokens: session.usage.total_tokens,
            });
        }
    }
    (summaries, events)
}

fn repo_relative_session_path(repo: &Path, cwd: &Path, event_path: &str) -> Option<String> {
    let cwd = cwd.canonicalize().unwrap_or_else(|_| cwd.to_path_buf());
    let prefix = cwd.strip_prefix(repo).ok()?;
    let joined = prefix.join(event_path);
    let mut parts = Vec::new();
    for component in joined.components() {
        match component {
            std::path::Component::CurDir => {}
            std::path::Component::Normal(part) => parts.push(part.to_str()?.to_string()),
            std::path::Component::ParentDir => {
                parts.pop()?;
            }
            std::path::Component::RootDir | std::path::Component::Prefix(_) => return None,
        }
    }
    (!parts.is_empty()).then(|| parts.join("/"))
}

fn associate_events(
    events: &[NormalizedEvent],
    changes: &[GitChange],
    lifetimes: &[FileLifetime],
) -> Vec<EventAssociation> {
    let lifetime_paths = lifetimes
        .iter()
        .map(|lifetime| {
            (
                lifetime.id.as_str(),
                lifetime
                    .paths
                    .iter()
                    .map(String::as_str)
                    .collect::<BTreeSet<_>>(),
            )
        })
        .collect::<HashMap<_, _>>();
    let lifetime_intervals = lifetimes
        .iter()
        .map(|lifetime| (lifetime.id.as_str(), (lifetime.birth_ms, lifetime.death_ms)))
        .collect::<HashMap<_, _>>();
    let mut associations = Vec::new();
    // Mixed compound commands can retain a primary process/test effect while
    // still containing segment-local writes (for example `cargo build && cp
    // ...`). Eligibility is therefore defined by the normalized write-path
    // evidence, not by the lossy event-level effect label.
    for event in events.iter().filter(|event| !event.write_paths.is_empty()) {
        for path in &event.write_paths {
            let mut candidates = changes
                .iter()
                .filter(|change| !change.is_merge)
                .filter(|change| {
                    change.committed_at_ms >= event.ts_ms.saturating_sub(RETRIEVAL_BEFORE_MS)
                        && change.committed_at_ms <= event.ts_ms.saturating_add(RETRIEVAL_AFTER_MS)
                })
                .filter_map(|change| {
                    let direct = change.path == *path
                        || change.old_path.as_deref().is_some_and(|old| old == path);
                    let lifetime_match = lifetime_paths
                        .get(change.lifetime_id.as_str())
                        .is_some_and(|paths| paths.contains(path.as_str()));
                    let event_within_lifetime = lifetime_intervals
                        .get(change.lifetime_id.as_str())
                        .is_some_and(|(birth, death)| {
                            event.ts_ms >= *birth && death.is_none_or(|death| event.ts_ms < death)
                        });
                    let prebirth = change.status.starts_with('A')
                        && change.path == *path
                        && change.committed_at_ms >= event.ts_ms;
                    if !prebirth && (!event_within_lifetime || (!direct && !lifetime_match)) {
                        return None;
                    }
                    let exact_hunk_match = event.edit_summary.as_ref().is_some_and(|summary| {
                        change
                            .hunks
                            .iter()
                            .any(|hunk| edit_matches_hunk(summary, hunk))
                    });
                    let match_kind = if prebirth {
                        "prebirth"
                    } else if direct {
                        "direct_path"
                    } else {
                        "rename_lifetime"
                    };
                    Some((change, exact_hunk_match, match_kind))
                })
                .collect::<Vec<_>>();
            candidates.sort_by(|left, right| {
                let left_key = candidate_sort_key(event, left.0, left.1, left.2);
                let right_key = candidate_sort_key(event, right.0, right.1, right.2);
                left_key.cmp(&right_key)
            });
            let candidate_count = candidates.len();
            let top_distance_ms = candidates
                .first()
                .map(|candidate| (candidate.0.committed_at_ms - event.ts_ms).abs());
            let second_distance_ms = candidates
                .get(1)
                .map(|candidate| (candidate.0.committed_at_ms - event.ts_ms).abs());
            let mapped = candidates
                .into_iter()
                .enumerate()
                .map(
                    |(index, (change, exact_hunk_match, match_kind))| CandidateAssociation {
                        change_id: change.id.clone(),
                        commit_id: change.commit_id.clone(),
                        lifetime_id: change.lifetime_id.clone(),
                        rank: index + 1,
                        delta_ms: change.committed_at_ms - event.ts_ms,
                        match_kind: match_kind.to_string(),
                        exact_hunk_match,
                        evidence_bin: candidate_evidence_bin(
                            candidate_count,
                            index,
                            top_distance_ms,
                            second_distance_ms,
                            exact_hunk_match,
                            match_kind,
                        ),
                    },
                )
                .collect::<Vec<_>>();
            let state = match mapped.len() {
                0 => "no_candidate",
                1 => "unique_candidate",
                _ => "ambiguous_candidates",
            };
            let association_source = format!("{}:{path}", event.id);
            associations.push(EventAssociation {
                id: format!("assoc-{}", short_hash(&association_source, 20)),
                event_id: event.id.clone(),
                path: path.clone(),
                state: state.to_string(),
                candidates: mapped,
            });
        }
    }
    associations
}

fn candidate_sort_key(
    event: &NormalizedEvent,
    change: &GitChange,
    exact_hunk_match: bool,
    match_kind: &str,
) -> (u8, u8, u8, i64, String) {
    let direct_rank = match match_kind {
        "direct_path" => 0,
        "prebirth" => 1,
        "rename_lifetime" => 1,
        _ => 2,
    };
    let direction_rank = if change.committed_at_ms >= event.ts_ms {
        0
    } else {
        1
    };
    (
        u8::from(!exact_hunk_match),
        direct_rank,
        direction_rank,
        (change.committed_at_ms - event.ts_ms).abs(),
        change.commit_id.clone(),
    )
}

fn candidate_evidence_bin(
    candidate_count: usize,
    index: usize,
    top_distance_ms: Option<i64>,
    second_distance_ms: Option<i64>,
    exact_hunk_match: bool,
    match_kind: &str,
) -> String {
    if index == 0 && exact_hunk_match && candidate_count == 1 {
        "exact_hunk_unique"
    } else if candidate_count == 1 && match_kind == "direct_path" {
        "unique_direct_lifetime"
    } else if candidate_count == 1 {
        "unique_rename_or_prebirth"
    } else if index == 0
        && top_distance_ms
            .zip(second_distance_ms)
            .is_some_and(|(top, second)| top.saturating_mul(4) <= second)
    {
        "multi_close_top"
    } else {
        "multi_other"
    }
    .to_string()
}

fn edit_matches_hunk(edit: &EditSummary, hunk: &HunkFingerprint) -> bool {
    let before_matches = edit
        .before_hash
        .as_ref()
        .is_none_or(|hash| hunk.before_hash.as_ref() == Some(hash));
    let after_matches = edit
        .after_hash
        .as_ref()
        .is_none_or(|hash| hunk.after_hash.as_ref() == Some(hash));
    (edit.before_hash.is_some() || edit.after_hash.is_some()) && before_matches && after_matches
}

fn current_blob_sizes(repo: &Path, head: &str) -> Result<HashMap<String, u64>, ExportError> {
    let output = git_bytes(repo, &["ls-tree", "-r", "-l", "-z", head])?;
    let mut sizes = HashMap::new();
    for record in output.split(|byte| *byte == 0) {
        if record.is_empty() {
            continue;
        }
        let text = utf8(record, "ls-tree record")?;
        let Some((metadata, path)) = text.split_once('\t') else {
            continue;
        };
        let size = metadata
            .split_whitespace()
            .last()
            .and_then(|value| value.parse::<u64>().ok());
        if let Some(size) = size {
            sizes.insert(path.to_string(), size);
        }
    }
    Ok(sizes)
}

fn git_text(repo: &Path, args: &[&str]) -> Result<String, ExportError> {
    let output = git_bytes(repo, args)?;
    String::from_utf8(output)
        .map_err(|error| ExportError::new(format!("git returned invalid UTF-8: {error}")))
}

fn git_bytes(repo: &Path, args: &[&str]) -> Result<Vec<u8>, ExportError> {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()
        .map_err(|error| ExportError::new(format!("cannot run git: {error}")))?;
    if !output.status.success() {
        return Err(command_error(&format!("git {}", args.join(" ")), &output));
    }
    Ok(output.stdout)
}

fn command_error(label: &str, output: &std::process::Output) -> ExportError {
    ExportError::new(format!(
        "{label} failed with {}: {}",
        output.status,
        String::from_utf8_lossy(&output.stderr).trim()
    ))
}

fn nul_tokens(output: &[u8]) -> Vec<String> {
    output
        .split(|byte| *byte == 0)
        .filter(|token| !token.is_empty())
        .map(|token| String::from_utf8_lossy(token).into_owned())
        .collect()
}

fn parse_numstat(value: &str) -> u64 {
    value.parse().unwrap_or(0)
}

fn trim_ascii(mut value: &[u8]) -> &[u8] {
    while value.first().is_some_and(u8::is_ascii_whitespace) {
        value = &value[1..];
    }
    while value.last().is_some_and(u8::is_ascii_whitespace) {
        value = &value[..value.len() - 1];
    }
    value
}

fn utf8<'a>(value: &'a [u8], label: &str) -> Result<&'a str, ExportError> {
    std::str::from_utf8(value)
        .map_err(|error| ExportError::new(format!("invalid {label}: {error}")))
}

fn content_fingerprint(value: &str) -> String {
    let normalized = value.replace("\r\n", "\n");
    short_hash(normalized.trim_end_matches('\n'), 24)
}

fn format_timestamp(timestamp_ms: i64) -> String {
    DateTime::<Utc>::from_timestamp_millis(timestamp_ms)
        .map(|timestamp| timestamp.to_rfc3339_opts(SecondsFormat::Millis, true))
        .unwrap_or_else(|| timestamp_ms.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Stdio;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn git(repo: &Path, args: &[&str]) {
        let status = Command::new("git")
            .arg("-C")
            .arg(repo)
            .args(args)
            .stdout(Stdio::null())
            .status()
            .expect("run git");
        assert!(status.success(), "git {args:?}");
    }

    #[test]
    fn tool_evidence_can_match_a_repository_outside_session_cwd() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!("agent-session-cross-repo-{unique}"));
        let repo = root.join("target-repo");
        let elsewhere = root.join("other-repo");
        fs::create_dir_all(repo.join("src")).expect("repo");
        fs::create_dir_all(&elsewhere).expect("cwd");
        let command = format!("cat {}/src/lib.rs", repo.display());
        let (matched, paths) = tool_repo_evidence(elsewhere.to_str(), &command, &repo);
        assert!(matched);
        assert_eq!(paths, BTreeSet::from(["src/lib.rs".to_string()]));
        fs::remove_dir_all(root).expect("cleanup");
    }

    #[test]
    fn repository_paths_drop_shell_and_prose_fragments() {
        for path in [
            "^vis-gallery",
            "!docs/design.md",
            "HEAD..origin/main",
            "docs/tmp/.../raw",
            "Claude/Codex/Gemini",
            "repos/example/project",
            "~/.codex/sessions",
        ] {
            assert_eq!(clean_relative_path(Path::new(path)), None, "{path}");
        }
        assert_eq!(
            clean_relative_path(Path::new(".artifacts/sim/home/.codex/session.jsonl")),
            Some(".artifacts/sim/home/.codex/session.jsonl".to_string())
        );
    }

    #[test]
    fn hunk_fingerprints_match_normalized_edit_blocks() {
        let hunks = parse_hunk_fingerprints("@@ -1 +1 @@\n-old\n+new\n");
        assert_eq!(hunks.len(), 1);
        assert_eq!(hunks[0].before_hash, Some(content_fingerprint("old\n")));
        assert_eq!(hunks[0].after_hash, Some(content_fingerprint("new\n")));
    }

    #[test]
    fn resumed_long_running_sessions_are_not_cut_off_by_future_mtime() {
        let since_ms = 1_000_000;
        assert!(candidate_mtime_may_contain_window(
            since_ms + 90 * 24 * 60 * 60 * 1_000,
            since_ms,
        ));
        assert!(!candidate_mtime_may_contain_window(
            since_ms - AUDIT_BEFORE_MS - 1,
            since_ms,
        ));
    }

    #[test]
    fn delete_then_recreate_starts_a_new_lifetime() {
        let root = std::env::temp_dir().join(format!(
            "agent-session-longitudinal-{}-{}",
            std::process::id(),
            short_hash("delete-recreate", 8)
        ));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).expect("create fixture repo");
        git(&root, &["init", "-q"]);
        git(&root, &["config", "user.name", "Fixture"]);
        git(&root, &["config", "user.email", "fixture@example.test"]);
        fs::write(root.join("file.txt"), "one\n").expect("write file");
        git(&root, &["add", "file.txt"]);
        git(&root, &["commit", "-q", "-m", "add"]);
        fs::remove_file(root.join("file.txt")).expect("remove file");
        git(&root, &["add", "-u"]);
        git(&root, &["commit", "-q", "-m", "delete"]);
        fs::write(root.join("file.txt"), "two\n").expect("recreate file");
        git(&root, &["add", "file.txt"]);
        git(&root, &["commit", "-q", "-m", "recreate"]);

        let (_, lifetimes) = collect_git_history(&root, "HEAD", i64::MIN, i64::MAX, true)
            .expect("collect fixture history");
        let matching = lifetimes
            .iter()
            .filter(|lifetime| lifetime.paths == ["file.txt"])
            .collect::<Vec<_>>();
        assert_eq!(matching.len(), 2);
        assert!(matching[0].death_commit.is_some());
        assert!(matching[1].death_commit.is_none());
        fs::remove_dir_all(&root).expect("remove fixture repo");
    }

    #[test]
    fn write_in_deleted_path_gap_only_targets_next_add() {
        let event = NormalizedEvent {
            id: "event".to_string(),
            session_id: "session".to_string(),
            vendor: "fixture".to_string(),
            model: None,
            ts_ms: 150,
            kind: "tool".to_string(),
            action: "write".to_string(),
            category: "file".to_string(),
            effect: "write".to_string(),
            status: "ok".to_string(),
            prompt_index: 0,
            paths: vec!["file.txt".to_string()],
            read_paths: Vec::new(),
            write_paths: vec!["file.txt".to_string()],
            path_groups: Vec::new(),
            process_chain: Vec::new(),
            domains: Vec::new(),
            edit_summary: None,
            input_tokens: 0,
            output_tokens: 0,
            cache_tokens: 0,
        };
        let changes = vec![
            GitChange {
                id: "delete".to_string(),
                commit_id: "old-commit".to_string(),
                committed_at_ms: 100,
                status: "D".to_string(),
                old_path: None,
                path: "file.txt".to_string(),
                additions: 0,
                deletions: 1,
                lifetime_id: "old".to_string(),
                is_merge: false,
                hunks: Vec::new(),
            },
            GitChange {
                id: "add".to_string(),
                commit_id: "new-commit".to_string(),
                committed_at_ms: 200,
                status: "A".to_string(),
                old_path: None,
                path: "file.txt".to_string(),
                additions: 1,
                deletions: 0,
                lifetime_id: "new".to_string(),
                is_merge: false,
                hunks: Vec::new(),
            },
        ];
        let lifetimes = vec![
            FileLifetime {
                id: "old".to_string(),
                paths: vec!["file.txt".to_string()],
                birth_commit: "birth-old".to_string(),
                birth_ms: 0,
                death_commit: Some("old-commit".to_string()),
                death_ms: Some(100),
                current_path: None,
                current_bytes: None,
                survives_to_head: false,
            },
            FileLifetime {
                id: "new".to_string(),
                paths: vec!["file.txt".to_string()],
                birth_commit: "new-commit".to_string(),
                birth_ms: 200,
                death_commit: None,
                death_ms: None,
                current_path: Some("file.txt".to_string()),
                current_bytes: Some(4),
                survives_to_head: true,
            },
        ];

        let associations = associate_events(&[event], &changes, &lifetimes);
        assert_eq!(associations.len(), 1);
        assert_eq!(associations[0].state, "unique_candidate");
        assert_eq!(associations[0].candidates[0].commit_id, "new-commit");
        assert_eq!(associations[0].candidates[0].match_kind, "prebirth");
    }

    #[test]
    fn segment_local_write_is_eligible_even_when_primary_effect_is_process() {
        let event = NormalizedEvent {
            id: "event".to_string(),
            session_id: "session".to_string(),
            vendor: "fixture".to_string(),
            model: None,
            ts_ms: 100,
            kind: "tool".to_string(),
            action: "exec_command".to_string(),
            category: "shell".to_string(),
            effect: "process".to_string(),
            status: "ok".to_string(),
            prompt_index: 0,
            paths: vec!["file.txt".to_string()],
            read_paths: Vec::new(),
            write_paths: vec!["file.txt".to_string()],
            path_groups: Vec::new(),
            process_chain: Vec::new(),
            domains: Vec::new(),
            edit_summary: None,
            input_tokens: 0,
            output_tokens: 0,
            cache_tokens: 0,
        };
        let change = GitChange {
            id: "change".to_string(),
            commit_id: "commit".to_string(),
            committed_at_ms: 110,
            status: "M".to_string(),
            old_path: None,
            path: "file.txt".to_string(),
            additions: 1,
            deletions: 0,
            lifetime_id: "lifetime".to_string(),
            is_merge: false,
            hunks: Vec::new(),
        };
        let lifetime = FileLifetime {
            id: "lifetime".to_string(),
            paths: vec!["file.txt".to_string()],
            birth_commit: "birth".to_string(),
            birth_ms: 0,
            death_commit: None,
            death_ms: None,
            current_path: Some("file.txt".to_string()),
            current_bytes: Some(4),
            survives_to_head: true,
        };

        let associations = associate_events(&[event], &[change], &[lifetime]);
        assert_eq!(associations.len(), 1);
        assert_eq!(associations[0].path, "file.txt");
    }

    #[test]
    fn session_paths_can_resolve_from_a_repository_subdirectory() {
        let repo = Path::new("/repo");
        let cwd = Path::new("/repo/nested");
        assert_eq!(
            repo_relative_session_path(repo, cwd, "../src/lib.rs").as_deref(),
            Some("src/lib.rs")
        );
        assert!(repo_relative_session_path(repo, cwd, "../../outside.txt").is_none());
    }
}
