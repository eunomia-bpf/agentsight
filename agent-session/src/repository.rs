// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-scoped file actions from native coding-agent sessions.

use crate::{
    AGENT_CLAUDE, AGENT_CODEX, AGENT_GEMINI, AgentSession, SessionCandidate,
    discover_session_files, parse_session_content, session_candidate_from_path,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::io::{self, BufRead, BufReader, Read};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Debug, Clone)]
pub struct RepositoryTraceOptions {
    pub repo: PathBuf,
    pub global: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryTrace {
    pub repository: String,
    pub revision: String,
    pub start_ms: i64,
    pub global: bool,
    pub session_count: usize,
    pub source_event_count: usize,
    pub events: Vec<RepositoryEvent>,
    pub commits_ms: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryEvent {
    pub id: String,
    pub session_id: String,
    pub vendor: String,
    pub ts_ms: i64,
    pub actions: Vec<FileAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct FileAction {
    pub path: String,
    pub access: String,
}

pub fn build_repository_trace(options: &RepositoryTraceOptions) -> io::Result<RepositoryTrace> {
    let repo = repository_root(&options.repo)?;
    let roots = worktree_roots(&repo);
    let known = known_git_paths(&repo)?;
    let remote = git_text(&repo, &["remote", "get-url", "origin"])
        .ok()
        .map(|value| normalize_repository_url(&value));
    let mut candidates = discover_session_files()
        .into_iter()
        .filter(|candidate| candidate_may_match_repo(candidate, &roots, remote.as_deref()))
        .collect::<Vec<_>>();
    candidates.sort_by(|left, right| left.path.cmp(&right.path));
    let (mut events, source_event_count) =
        scan_sessions(&candidates, &roots, &known, options.global);
    events.sort_by(|left, right| (left.ts_ms, &left.id).cmp(&(right.ts_ms, &right.id)));
    let session_count = events
        .iter()
        .map(|event| &event.session_id)
        .collect::<HashSet<_>>()
        .len();
    let commits_ms = git_lines(&repo, &["log", "--all", "--format=%ct"])?
        .into_iter()
        .filter_map(|value| value.parse::<i64>().ok().map(|seconds| seconds * 1_000))
        .collect::<Vec<_>>();
    let start_ms = commits_ms
        .iter()
        .copied()
        .min()
        .unwrap_or_else(|| events.first().map_or(0, |event| event.ts_ms));
    Ok(RepositoryTrace {
        repository: repo
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("repository")
            .into(),
        revision: git_text(&repo, &["rev-parse", "HEAD"])?.trim().into(),
        start_ms,
        global: options.global,
        session_count,
        source_event_count,
        events,
        commits_ms,
    })
}

fn scan_sessions(
    candidates: &[SessionCandidate],
    roots: &[PathBuf],
    known: &HashSet<String>,
    global: bool,
) -> (Vec<RepositoryEvent>, usize) {
    let mut result = (Vec::new(), 0usize);
    for candidate in candidates {
        let Some((session, source_count)) = repository_session(candidate) else {
            continue;
        };
        append_session(&session, source_count, roots, known, true, &mut result);
    }
    if global {
        let direct = candidates
            .iter()
            .map(|row| &row.path)
            .collect::<HashSet<_>>();
        for session in behavior_sessions(roots) {
            if !direct.contains(&session.path) {
                let source_count = session.events.tools.len() + session.events.llm_responses.len();
                append_session(&session, source_count, roots, known, false, &mut result);
            }
        }
    }
    result
}

fn repository_session(candidate: &SessionCandidate) -> Option<(AgentSession, usize)> {
    if candidate.agent == AGENT_GEMINI {
        let content = std::fs::read_to_string(&candidate.path).ok()?;
        let session = parse_session_content(
            candidate.agent,
            &candidate.path,
            candidate.updated,
            &content,
        )?;
        let count = session.events.tools.len() + session.events.llm_responses.len();
        return Some((session, count));
    }
    let mut reader = BufReader::new(std::fs::File::open(&candidate.path).ok()?);
    let mut line = String::new();
    let mut content = String::new();
    let mut llm_count = 0;
    let mut have_context = false;
    while reader.read_line(&mut line).ok()? > 0 {
        let kind = |value| json_type(&line, value);
        let assistant = kind("assistant");
        let response = kind("response_item");
        let context = kind("session_meta") || (!have_context && kind("turn_context"));
        let tool = (assistant && line.contains(r#""tool_use""#))
            || (response && (kind("function_call") || kind("custom_tool_call")));
        llm_count +=
            usize::from(assistant || kind("agent_message") || (response && kind("message")));
        if context || tool {
            content.push_str(&line);
            have_context |= kind("turn_context");
        }
        line.clear();
    }
    let session = parse_session_content(
        candidate.agent,
        &candidate.path,
        candidate.updated,
        &content,
    )?;
    let count = session.events.tools.len() + llm_count;
    Some((session, count))
}

fn json_type(line: &str, value: &str) -> bool {
    line.match_indices(value).any(|(index, _)| {
        let prefix = &line[..index];
        let suffix = &line[index + value.len()..];
        (prefix.ends_with(r#""type":""#) || prefix.ends_with(r#""type": ""#))
            && suffix.starts_with('"')
    })
}

fn append_session(
    session: &AgentSession,
    source_count: usize,
    roots: &[PathBuf],
    known: &HashSet<String>,
    repository_session: bool,
    batch: &mut (Vec<RepositoryEvent>, usize),
) {
    let cwd = session.cwd.as_deref().map(PathBuf::from).or_else(|| {
        let source = repository_session.then(|| session.path.to_string_lossy())?;
        roots
            .iter()
            .find(|root| source.contains(&root.to_string_lossy().replace('/', "-")))
            .cloned()
    });
    let session_id = format!(
        "{}:{}",
        session.agent_type,
        session
            .path
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or(&session.session_id)
    );
    let mut used = false;
    for (ordinal, tool) in session.events.tools.iter().enumerate() {
        let Some(ts_ms) = tool.ts_ms else { continue };
        let actions = tool
            .paths
            .iter()
            .filter_map(|item| {
                let path = resolve_path(&item.path, cwd.as_deref(), roots)?;
                (!ignored_path(&path) && (item.access != "read" || known.contains(&path)))
                    .then_some(FileAction {
                        path,
                        access: item.access.clone(),
                    })
            })
            .collect::<BTreeSet<_>>();
        if actions.is_empty() {
            continue;
        }
        used = true;
        batch.0.push(RepositoryEvent {
            id: format!("{session_id}:{ordinal}"),
            session_id: session_id.clone(),
            vendor: session.agent_type.clone(),
            ts_ms,
            actions: actions.into_iter().collect(),
        });
    }
    if used {
        batch.1 += source_count;
    }
}

fn candidate_may_match_repo(
    candidate: &SessionCandidate,
    roots: &[PathBuf],
    remote: Option<&str>,
) -> bool {
    match candidate.agent {
        AGENT_CLAUDE => roots.iter().any(|root| {
            candidate
                .path
                .to_string_lossy()
                .contains(&root.to_string_lossy().replace('/', "-"))
        }),
        AGENT_CODEX => session_header(&candidate.path).lines().any(|line| {
            let Some(row) = serde_json::from_str::<serde_json::Value>(line).ok() else {
                return false;
            };
            let cwd_matches = row
                .pointer("/payload/cwd")
                .and_then(|value| value.as_str())
                .map(PathBuf::from)
                .is_some_and(|cwd| roots.iter().any(|root| cwd.starts_with(root)));
            let remote_matches = remote.is_some_and(|expected| {
                row.pointer("/payload/git/repository_url")
                    .and_then(|value| value.as_str())
                    .is_some_and(|value| normalize_repository_url(value) == expected)
            });
            cwd_matches || remote_matches
        }),
        AGENT_GEMINI => true,
        _ => false,
    }
}

fn normalize_repository_url(value: &str) -> String {
    let value = value
        .trim()
        .trim_end_matches('/')
        .trim_end_matches(".git")
        .to_ascii_lowercase();
    value
        .strip_prefix("git@")
        .and_then(|rest| rest.split_once(':'))
        .map_or(value.clone(), |(host, path)| {
            format!("https://{host}/{path}")
        })
}

fn behavior_sessions(roots: &[PathBuf]) -> Vec<AgentSession> {
    let Some(home) = dirs::home_dir() else {
        return Vec::new();
    };
    let search = [
        home.join(".claude/projects"),
        home.join(".codex/sessions"),
        home.join(".codex/archived_sessions"),
    ];
    let mut command = Command::new("rg");
    command.args([
        "--json",
        "--no-messages",
        "--fixed-strings",
        "--glob",
        "*.jsonl",
    ]);
    for term in roots.iter().filter_map(|root| root.to_str()) {
        command.args(["-e", term]);
    }
    command.args(search.iter().filter(|path| path.exists()));
    let Ok(mut child) = command.stdout(Stdio::piped()).spawn() else {
        return Vec::new();
    };
    let Some(stdout) = child.stdout.take() else {
        return Vec::new();
    };
    let mut selected = HashMap::<PathBuf, BTreeMap<u64, String>>::new();
    for line in BufReader::new(stdout).lines().map_while(Result::ok) {
        let Ok(row) = serde_json::from_str::<serde_json::Value>(&line) else {
            continue;
        };
        if row.get("type").and_then(|value| value.as_str()) != Some("match") {
            continue;
        }
        let (Some(path), Some(text)) = (
            row.pointer("/data/path/text").and_then(|v| v.as_str()),
            row.pointer("/data/lines/text").and_then(|v| v.as_str()),
        ) else {
            continue;
        };
        let tool_call = (json_type(text, "assistant") && text.contains(r#""tool_use""#))
            || (json_type(text, "response_item")
                && (json_type(text, "function_call") || json_type(text, "custom_tool_call")));
        if !tool_call {
            continue;
        }
        let number = row
            .pointer("/data/line_number")
            .and_then(|v| v.as_u64())
            .unwrap_or_default();
        selected
            .entry(path.into())
            .or_default()
            .insert(number, text.trim_end().into());
    }
    let Ok(status) = child.wait() else {
        return Vec::new();
    };
    if !status.success() && status.code() != Some(1) {
        return Vec::new();
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
    let Ok(mut file) = std::fs::File::open(path) else {
        return String::new();
    };
    let mut prefix = vec![0; 256 * 1024];
    let Ok(size) = file.read(&mut prefix) else {
        return String::new();
    };
    String::from_utf8_lossy(&prefix[..size])
        .lines()
        .filter(|line| json_type(line, "session_meta") || json_type(line, "turn_context"))
        .take(2)
        .map(|line| format!("{line}\n"))
        .collect()
}

fn repository_root(path: &Path) -> io::Result<PathBuf> {
    let path = path.canonicalize()?;
    Ok(PathBuf::from(
        git_text(&path, &["rev-parse", "--show-toplevel"])?.trim(),
    ))
}

fn worktree_roots(repo: &Path) -> Vec<PathBuf> {
    let mut roots = git_text(repo, &["worktree", "list", "--porcelain"])
        .unwrap_or_default()
        .lines()
        .filter_map(|line| line.strip_prefix("worktree "))
        .map(PathBuf::from)
        .collect::<Vec<_>>();
    roots.push(repo.to_path_buf());
    roots.sort();
    roots.dedup();
    roots
}

fn known_git_paths(repo: &Path) -> io::Result<HashSet<String>> {
    let mut paths = git_lines(repo, &["log", "--all", "--format=", "--name-only"])?
        .into_iter()
        .filter(|value| !value.is_empty())
        .collect::<HashSet<_>>();
    paths.extend(
        git_lines(
            repo,
            &["ls-files", "--cached", "--others", "--exclude-standard"],
        )?
        .into_iter()
        .filter(|value| !value.is_empty()),
    );
    Ok(paths)
}

fn resolve_path(raw: &str, cwd: Option<&Path>, roots: &[PathBuf]) -> Option<String> {
    let raw = raw.trim().trim_matches(['"', '\'', '`']);
    if raw.is_empty() || raw.contains(['*', '$', '\n', '\r']) {
        return None;
    }
    let path = Path::new(raw);
    if path.is_absolute() {
        return relative_to_roots(path, roots);
    }
    relative_to_roots(&cwd?.join(path), roots)
}

fn relative_to_roots(path: &Path, roots: &[PathBuf]) -> Option<String> {
    let normalized = lexical(path);
    roots.iter().find_map(|root| {
        normalized
            .strip_prefix(lexical(root))
            .ok()
            .and_then(|relative| {
                let value = relative.to_string_lossy().replace('\\', "/");
                (!value.is_empty()).then_some(value)
            })
    })
}

fn lexical(path: &Path) -> PathBuf {
    let mut output = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                output.pop();
            }
            other => output.push(other.as_os_str()),
        }
    }
    output
}

fn ignored_path(path: &str) -> bool {
    path.split('/')
        .any(|part| matches!(part, ".git" | "node_modules" | "target" | ".cache"))
}

fn git_lines(repo: &Path, args: &[&str]) -> io::Result<Vec<String>> {
    Ok(git_text(repo, args)?
        .lines()
        .map(|line| line.trim().to_string())
        .collect())
}

fn git_text(repo: &Path, args: &[&str]) -> io::Result<String> {
    let output = Command::new("git").args(args).current_dir(repo).output()?;
    if !output.status.success() {
        return Err(io::Error::other(format!(
            "git {} failed: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    String::from_utf8(output.stdout).map_err(io::Error::other)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lexical_paths_cannot_escape_a_worktree() {
        let roots = vec![PathBuf::from("/repo")];
        assert_eq!(
            resolve_path("src/../lib.rs", Some(Path::new("/repo")), &roots),
            Some("lib.rs".into())
        );
        assert_eq!(
            resolve_path("../../secret", Some(Path::new("/repo")), &roots),
            None
        );
    }

    #[test]
    fn ignored_dependencies_do_not_become_stars() {
        assert!(ignored_path("frontend/node_modules/a.js"));
        assert!(!ignored_path("collector/src/main.rs"));
    }
}
