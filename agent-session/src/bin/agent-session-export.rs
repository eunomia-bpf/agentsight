// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agent_session::{
    LongitudinalOptions, build_longitudinal_artifact, write_longitudinal_artifact,
};
use chrono::{DateTime, NaiveDate};
use std::env;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

const HELP: &str = r#"Export coding-agent events joined with Git history.

Usage:
  agent-session-export --repo PATH --since RFC3339 --until RFC3339 \
    --output FILE [--format FORMAT] [--head REV] [--session FILE ...]

Options:
  --repo PATH       Git worktree whose native sessions and history are joined
  --since TIME      Inclusive event start (RFC3339 or YYYY-MM-DD in UTC)
  --until TIME      Exclusive event end (RFC3339 or YYYY-MM-DD in UTC)
  --output FILE|-   Destination file, or JSON on stdout with -
  --format FORMAT   json (default), events-jsonl, perfetto, or gource
  --head REV        Freeze Git history and endpoint at this revision (default: HEAD)
  --session FILE    Parse only this native session file; may be repeated
                    By default discover Claude, Codex, and Gemini sessions
  --global          Also include Tool events from sessions outside the repository
                    when their command or path targets this repository
  --without-git-history
                    Export normalized sessions/events without mining per-commit diffs
  --git-lifetimes-only
                    Export first-parent add/delete/rename lifetimes without hunk/numstat mining
  -h, --help        Show this help

Perfetto and Gource outputs are explicitly lossy compatibility projections.
"#;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExportFormat {
    Json,
    EventsJsonl,
    Perfetto,
    Gource,
}

impl ExportFormat {
    fn parse(value: &str) -> Result<Self, String> {
        match value {
            "json" => Ok(Self::Json),
            "events-jsonl" => Ok(Self::EventsJsonl),
            "perfetto" => Ok(Self::Perfetto),
            "gource" => Ok(Self::Gource),
            _ => Err(format!(
                "unknown format {value}; use json, events-jsonl, perfetto, or gource"
            )),
        }
    }
}

#[derive(Debug)]
struct Args {
    repo: PathBuf,
    head: Option<String>,
    since_ms: i64,
    until_ms: i64,
    output: PathBuf,
    format: ExportFormat,
    session_paths: Vec<PathBuf>,
    include_git_history: bool,
    include_git_details: bool,
    include_global_events: bool,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("agent-session-export: {error}");
        std::process::exit(2);
    }
}

fn run() -> Result<(), String> {
    let Some(args) = parse_args(env::args().skip(1).collect())? else {
        print!("{HELP}");
        return Ok(());
    };
    if args.output == Path::new("-") && args.format != ExportFormat::Json {
        return Err("--output - is supported only for JSON".to_string());
    }
    let artifact = build_longitudinal_artifact(&LongitudinalOptions {
        repo: args.repo,
        head: args.head,
        since_ms: args.since_ms,
        until_ms: args.until_ms,
        session_paths: args.session_paths,
        include_git_history: args.include_git_history,
        include_git_details: args.include_git_details,
        include_global_events: args.include_global_events,
    })
    .map_err(|error| error.to_string())?;
    match args.format {
        ExportFormat::Json if args.output == Path::new("-") => {
            let mut writer = BufWriter::new(std::io::stdout().lock());
            serde_json::to_writer(&mut writer, &artifact).map_err(|error| error.to_string())?;
            writer.write_all(b"\n").map_err(|error| error.to_string())?;
        }
        ExportFormat::Json => write_longitudinal_artifact(&artifact, &args.output)
            .map_err(|error| error.to_string())?,
        ExportFormat::EventsJsonl => write_events_jsonl(&artifact, &args.output)?,
        ExportFormat::Perfetto => write_perfetto(&artifact, &args.output)?,
        ExportFormat::Gource => write_gource(&artifact, &args.output)?,
    }
    eprintln!(
        "exported {} sessions, {} events, {} Git changes, and {} candidate joins",
        artifact.summary.session_count,
        artifact.summary.event_count,
        artifact.summary.change_count,
        artifact.summary.write_event_path_count
    );
    Ok(())
}

fn parse_args(values: Vec<String>) -> Result<Option<Args>, String> {
    if values
        .iter()
        .any(|value| value == "-h" || value == "--help")
    {
        return Ok(None);
    }
    let mut repo = None;
    let mut since = None;
    let mut until = None;
    let mut output = None;
    let mut session_paths = Vec::new();
    let mut head = None;
    let mut format = ExportFormat::Json;
    let mut include_git_history = true;
    let mut include_git_details = true;
    let mut include_global_events = false;
    let mut index = 0usize;
    while index < values.len() {
        let flag = &values[index];
        index += 1;
        if flag == "--without-git-history" {
            include_git_history = false;
            include_git_details = false;
            continue;
        }
        if flag == "--git-lifetimes-only" {
            include_git_history = true;
            include_git_details = false;
            continue;
        }
        if flag == "--global" {
            include_global_events = true;
            continue;
        }
        let value = values
            .get(index)
            .ok_or_else(|| format!("missing value for {flag}"))?;
        index += 1;
        match flag.as_str() {
            "--repo" => repo = Some(PathBuf::from(value)),
            "--head" => head = Some(value.clone()),
            "--since" => since = Some(parse_timestamp(value)?),
            "--until" => until = Some(parse_timestamp(value)?),
            "--output" => output = Some(PathBuf::from(value)),
            "--format" => format = ExportFormat::parse(value)?,
            "--session" => session_paths.push(PathBuf::from(value)),
            _ => return Err(format!("unknown option {flag}\n\n{HELP}")),
        }
    }
    Ok(Some(Args {
        repo: repo.ok_or_else(|| "--repo is required".to_string())?,
        head,
        since_ms: since.ok_or_else(|| "--since is required".to_string())?,
        until_ms: until.ok_or_else(|| "--until is required".to_string())?,
        output: output.ok_or_else(|| "--output is required".to_string())?,
        format,
        session_paths,
        include_git_history,
        include_git_details,
        include_global_events,
    }))
}

fn output(path: &Path) -> Result<BufWriter<File>, String> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    File::create(path)
        .map(BufWriter::new)
        .map_err(|error| error.to_string())
}

fn write_events_jsonl(
    artifact: &agent_session::LongitudinalArtifact,
    path: &Path,
) -> Result<(), String> {
    let mut writer = output(path)?;
    for event in &artifact.events {
        serde_json::to_writer(&mut writer, event).map_err(|error| error.to_string())?;
        writer.write_all(b"\n").map_err(|error| error.to_string())?;
    }
    Ok(())
}

fn write_perfetto(
    artifact: &agent_session::LongitudinalArtifact,
    path: &Path,
) -> Result<(), String> {
    let trace_events = artifact
        .events
        .iter()
        .map(|event| {
            serde_json::json!({
                "name": event.action,
                "cat": format!("recorded-process,{}", event.effect),
                "ph": "i",
                "s": "t",
                "ts": event.ts_ms * 1_000,
                "pid": event.vendor,
                "tid": event.session_id,
                "args": {
                    "paths": event.paths,
                    "status": event.status,
                    "prompt_index": event.prompt_index,
                    "evidence_layer": "recorded_process"
                }
            })
        })
        .chain(artifact.commits.iter().map(|commit| {
            serde_json::json!({
                "name": "Git commit",
                "cat": "durable-git",
                "ph": "i",
                "s": "g",
                "ts": commit.committed_at_ms * 1_000,
                "pid": "git",
                "tid": "first-parent",
                "args": {
                    "commit": commit.id,
                    "merge": commit.is_merge,
                    "evidence_layer": "durable_git"
                }
            })
        }))
        .collect::<Vec<_>>();
    serde_json::to_writer(output(path)?, &serde_json::json!({
        "displayTimeUnit": "ms",
        "metadata": {
            "schema": "agentsight.perfetto.lossy.v1",
            "source_schema": artifact.schema,
            "caveat": "Lossy compatibility projection; temporal adjacency is not causality or attribution."
        },
        "traceEvents": trace_events
    }))
    .map_err(|error| error.to_string())
}

fn write_gource(artifact: &agent_session::LongitudinalArtifact, path: &Path) -> Result<(), String> {
    let mut writer = output(path)?;
    for change in &artifact.changes {
        let Some(commit) = artifact
            .commits
            .iter()
            .find(|row| row.id == change.commit_id)
        else {
            continue;
        };
        for (action, path) in gource_actions(change) {
            writeln!(
                writer,
                "{}|{}|{}|/{}|#efd265",
                change.committed_at_ms / 1_000,
                commit.author_label,
                action,
                path
            )
            .map_err(|error| error.to_string())?;
        }
    }
    Ok(())
}

fn gource_actions(change: &agent_session::GitChange) -> Vec<(&'static str, &str)> {
    match change.status.chars().next().unwrap_or('M') {
        'R' => change
            .old_path
            .as_deref()
            .map(|old_path| vec![("D", old_path), ("A", change.path.as_str())])
            .unwrap_or_else(|| vec![("M", change.path.as_str())]),
        'C' => vec![("A", change.path.as_str())],
        'A' => vec![("A", change.path.as_str())],
        'D' => vec![("D", change.path.as_str())],
        _ => vec![("M", change.path.as_str())],
    }
}

fn parse_timestamp(value: &str) -> Result<i64, String> {
    if let Ok(timestamp) = DateTime::parse_from_rfc3339(value) {
        return Ok(timestamp.timestamp_millis());
    }
    if let Ok(date) = NaiveDate::parse_from_str(value, "%Y-%m-%d") {
        return date
            .and_hms_opt(0, 0, 0)
            .map(|timestamp| timestamp.and_utc().timestamp_millis())
            .ok_or_else(|| format!("invalid date {value}"));
    }
    Err(format!(
        "invalid timestamp {value}; use RFC3339 or YYYY-MM-DD"
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_required_arguments_and_repeated_sessions() {
        let args = parse_args(
            [
                "--repo",
                "/repo",
                "--since",
                "2026-07-14",
                "--until",
                "2026-07-15T00:00:00Z",
                "--output",
                "-",
                "--head",
                "deadbeef",
                "--session",
                "one.jsonl",
                "--session",
                "two.json",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )
        .expect("parse")
        .expect("not help");
        assert_eq!(args.session_paths.len(), 2);
        assert_eq!(args.head.as_deref(), Some("deadbeef"));
        assert_eq!(args.format, ExportFormat::Json);
        assert!(args.include_git_history);
        assert!(args.include_git_details);
        assert!(!args.include_global_events);
        assert_eq!(args.output, PathBuf::from("-"));
        assert!(args.until_ms > args.since_ms);
    }

    #[test]
    fn parses_session_only_export_without_git_history() {
        let args = parse_args(
            [
                "--repo",
                "/repo",
                "--since",
                "2026-07-14",
                "--until",
                "2026-07-15",
                "--output",
                "-",
                "--without-git-history",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )
        .expect("parse")
        .expect("not help");
        assert!(!args.include_git_history);
        assert!(!args.include_git_details);
    }

    #[test]
    fn parses_lifetime_only_git_export() {
        let args = parse_args(
            [
                "--repo",
                "/repo",
                "--since",
                "2026-07-14",
                "--until",
                "2026-07-15",
                "--output",
                "-",
                "--git-lifetimes-only",
                "--global",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )
        .expect("parse")
        .expect("not help");
        assert!(args.include_git_history);
        assert!(!args.include_git_details);
        assert!(args.include_global_events);
    }

    #[test]
    fn parses_lossy_compatibility_formats() {
        assert_eq!(
            ExportFormat::parse("perfetto").unwrap(),
            ExportFormat::Perfetto
        );
        assert!(ExportFormat::parse("unknown").is_err());
    }

    #[test]
    fn gource_rename_deletes_old_path_and_adds_new_path() {
        let change = agent_session::GitChange {
            id: "change".to_string(),
            commit_id: "commit".to_string(),
            committed_at_ms: 0,
            status: "R100".to_string(),
            old_path: Some("src/old.rs".to_string()),
            path: "src/new.rs".to_string(),
            additions: 0,
            deletions: 0,
            lifetime_id: "file-1".to_string(),
            is_merge: false,
            hunks: Vec::new(),
        };
        assert_eq!(
            gource_actions(&change),
            vec![("D", "src/old.rs"), ("A", "src/new.rs")]
        );
    }
}
