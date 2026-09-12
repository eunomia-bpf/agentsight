// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Repository-scoped file actions from native coding-agent sessions.

use agent_session::{
    AGENT_CLAUDE, AGENT_CODEX, AGENT_CURSOR, AGENT_GEMINI, AgentSession, SessionCandidate,
    discover_session_files, parse_session_content, parse_session_file, session_candidate_from_path,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, HashMap, HashSet};
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
    pub end_ms: i64,
    pub global: bool,
    pub session_count: usize,
    pub source_event_count: usize,
    pub file_action_count: usize,
    pub events: Vec<RepositoryEvent>,
    pub commits_ms: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryEvent {
    pub id: String,
    pub session_id: String,
    pub vendor: String,
    pub ts_ms: i64,
    pub tool_name: String,
    pub category: String,
    pub command_name: String,
    pub status: String,
    pub actions: Vec<FileAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct FileAction {
    pub path: String,
    pub access: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub previous_path: Option<String>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub scope: bool,
}

fn is_false(value: &bool) -> bool {
    !*value
}

pub fn build_repository_trace(options: &RepositoryTraceOptions) -> io::Result<RepositoryTrace> {
    let repo = repository_root(&options.repo)?;
    let roots = worktree_roots(&repo);
    let remote = git_text(&repo, &["remote", "get-url", "origin"])
        .ok()
        .map(|value| normalize_repository_url(&value));
    let mut candidates = discover_session_files()
        .into_iter()
        .filter(|candidate| candidate_may_match_repo(candidate, &roots, remote.as_deref()))
        .collect::<Vec<_>>();
    candidates.sort_by(|left, right| left.path.cmp(&right.path));
    let (mut events, source_event_count) = scan_sessions(&candidates, &roots, options.global)?;
    annotate_directory_scopes(&repo, &mut events)?;
    events.sort_by(|left, right| (left.ts_ms, &left.id).cmp(&(right.ts_ms, &right.id)));
    let session_count = events
        .iter()
        .map(|event| &event.session_id)
        .collect::<HashSet<_>>()
        .len();
    let mut commits_ms = git_lines(&repo, &["log", "--all", "--format=%ct"])?
        .into_iter()
        .filter_map(|value| value.parse::<i64>().ok().map(|seconds| seconds * 1_000))
        .collect::<Vec<_>>();
    commits_ms.sort_unstable();
    commits_ms.dedup();
    let start_ms = events.first().map_or(0, |event| event.ts_ms);
    let end_ms = events.last().map_or(start_ms, |event| event.ts_ms);
    let file_action_count = events.iter().map(|event| event.actions.len()).sum();
    Ok(RepositoryTrace {
        repository: repo
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or("repository")
            .into(),
        revision: git_text(&repo, &["rev-parse", "HEAD"])?.trim().into(),
        start_ms,
        end_ms,
        global: options.global,
        session_count,
        source_event_count,
        file_action_count,
        events,
        commits_ms,
    })
}

fn scan_sessions(
    candidates: &[SessionCandidate],
    roots: &[PathBuf],
    global: bool,
) -> io::Result<(Vec<RepositoryEvent>, usize)> {
    let mut result = (Vec::new(), 0usize);
    for (session, source_count) in parse_candidates(candidates) {
        append_session(&session, source_count, roots, true, &mut result);
    }
    if global {
        let direct = candidates
            .iter()
            .map(|row| row.path.clone())
            .collect::<HashSet<_>>();
        for (session, source_count) in behavior_sessions(roots, &direct)? {
            append_session(&session, source_count, roots, false, &mut result);
        }
    }
    Ok(result)
}

fn parse_candidates(candidates: &[SessionCandidate]) -> Vec<(AgentSession, usize)> {
    if candidates.is_empty() {
        return Vec::new();
    }
    let workers = std::thread::available_parallelism()
        .map_or(1, usize::from)
        .min(candidates.len());
    let chunk_size = candidates.len().div_ceil(workers);
    std::thread::scope(|scope| {
        let handles = candidates
            .chunks(chunk_size)
            .map(|chunk| {
                scope.spawn(move || {
                    chunk
                        .iter()
                        .filter_map(repository_session)
                        .collect::<Vec<_>>()
                })
            })
            .collect::<Vec<_>>();
        handles
            .into_iter()
            .flat_map(|handle| handle.join().unwrap_or_default())
            .collect()
    })
}

fn repository_session(candidate: &SessionCandidate) -> Option<(AgentSession, usize)> {
    // Cursor delegates work into sibling `subagents/*.jsonl` transcripts. The
    // file parser owns that aggregation; parsing only the parent content drops
    // the delegated file and tool events from repository traces.
    if candidate.agent == AGENT_CURSOR {
        let session = parse_session_file(candidate)?;
        let count = session.events.tools.len() + session.events.llm_responses.len();
        return Some((session, count));
    }
    // Read whole: the filter below keys on a top-level "type" neither writes.
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
        let result = (kind("user") && line.contains(r#""tool_result""#))
            || (response && (kind("function_call_output") || kind("custom_tool_call_output")));
        llm_count +=
            usize::from(assistant || kind("agent_message") || (response && kind("message")));
        if context || tool || result {
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
    repository_session: bool,
    batch: &mut (Vec<RepositoryEvent>, usize),
) {
    let cwd = session
        .cwd
        .as_deref()
        .map(PathBuf::from)
        .or_else(|| {
            repository_session
                .then(|| claude_project_name(&session.path))
                .flatten()
                .and_then(|project| {
                    roots
                        .iter()
                        .find(|root| encoded_claude_root(root) == project)
                        .cloned()
                })
        })
        .or_else(|| {
            gemini_project_hash(&session.path).and_then(|project| {
                roots
                    .iter()
                    .find(|root| repository_hash(root) == project)
                    .cloned()
            })
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
        let actions = if tool.status == "fail" {
            BTreeSet::new()
        } else {
            tool.paths
                .iter()
                .filter_map(|item| {
                    let path = resolve_path(&item.path, cwd.as_deref(), roots)?;
                    (!ignored_path(&path)).then_some(FileAction {
                        path,
                        access: item.access.clone(),
                        previous_path: item
                            .previous_path
                            .as_deref()
                            .and_then(|value| resolve_path(value, cwd.as_deref(), roots)),
                        scope: false,
                    })
                })
                .collect::<BTreeSet<_>>()
        };
        if !repository_session && actions.is_empty() {
            continue;
        }
        used = true;
        batch.0.push(RepositoryEvent {
            // Zero padded: ids compare as strings, so ties would sort 1, 10, 11, 2.
            id: format!("{session_id}:{ordinal:06}"),
            session_id: session_id.clone(),
            vendor: session.agent_type.clone(),
            ts_ms,
            tool_name: tool.tool_name.clone(),
            category: tool.category.clone(),
            command_name: tool.command_name.clone(),
            status: tool.status.clone(),
            actions: actions.into_iter().collect(),
        });
    }
    if used {
        batch.1 += source_count;
    }
}

fn annotate_directory_scopes(repo: &Path, events: &mut [RepositoryEvent]) -> io::Result<()> {
    let mut paths = git_lines(repo, &["ls-files"])?;
    paths.extend(events.iter().flat_map(|event| {
        event.actions.iter().flat_map(|action| {
            std::iter::once(action.path.clone()).chain(action.previous_path.clone())
        })
    }));
    let mut directories = directory_prefixes(&paths);
    for path in &paths {
        if repo.join(path).is_dir() {
            directories.insert(path.trim_end_matches('/').to_string());
        }
    }
    for action in events.iter_mut().flat_map(|event| &mut event.actions) {
        action.scope = directories.contains(action.path.trim_end_matches('/'))
            || action
                .previous_path
                .as_deref()
                .is_some_and(|path| directories.contains(path.trim_end_matches('/')));
    }
    Ok(())
}

fn directory_prefixes(paths: &[String]) -> HashSet<String> {
    let mut directories = HashSet::new();
    for path in paths {
        let parts = path
            .split('/')
            .filter(|part| !part.is_empty())
            .collect::<Vec<_>>();
        for depth in 1..parts.len() {
            directories.insert(parts[..depth].join("/"));
        }
    }
    directories
}

fn candidate_may_match_repo(
    candidate: &SessionCandidate,
    roots: &[PathBuf],
    remote: Option<&str>,
) -> bool {
    match candidate.agent {
        AGENT_CLAUDE => claude_project_name(&candidate.path).is_some_and(|project| {
            roots
                .iter()
                .any(|root| encoded_claude_root(root) == project)
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
        AGENT_GEMINI => gemini_project_hash(&candidate.path)
            .is_some_and(|project| roots.iter().any(|root| repository_hash(root) == project)),
        AGENT_CURSOR => cursor_project_name(&candidate.path).is_some_and(|project| {
            roots
                .iter()
                .any(|root| encoded_cursor_root(root) == project)
        }),
        _ => false,
    }
}

fn encoded_cursor_root(root: &Path) -> String {
    root.to_string_lossy()
        .replace('/', "-")
        .trim_start_matches('-')
        .to_string()
}

fn cursor_project_name(path: &Path) -> Option<String> {
    let mut components = path.components().peekable();
    while let Some(component) = components.next() {
        if component.as_os_str() == "projects"
            && let Some(project) = components.peek()
        {
            return Some(project.as_os_str().to_string_lossy().into_owned());
        }
    }
    None
}

fn encoded_claude_root(root: &Path) -> String {
    root.to_string_lossy().replace('/', "-")
}

fn claude_project_name(path: &Path) -> Option<String> {
    path.ancestors()
        .find(|ancestor| {
            ancestor
                .parent()
                .and_then(Path::file_name)
                .and_then(|v| v.to_str())
                == Some("projects")
        })?
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
}

fn gemini_project_hash(path: &Path) -> Option<String> {
    path.ancestors()
        .find(|ancestor| {
            ancestor
                .parent()
                .and_then(Path::file_name)
                .and_then(|v| v.to_str())
                == Some("tmp")
        })?
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
}

fn repository_hash(root: &Path) -> String {
    hex::encode(Sha256::digest(root.to_string_lossy().as_bytes()))
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

fn behavior_sessions(
    roots: &[PathBuf],
    excluded: &HashSet<PathBuf>,
) -> io::Result<Vec<(AgentSession, usize)>> {
    let Some(home) = dirs::home_dir() else {
        return Ok(Vec::new());
    };
    let search = [
        home.join(".claude/projects"),
        home.join(".codex/sessions"),
        home.join(".codex/archived_sessions"),
        home.join(".gemini/tmp"),
    ];
    let mut command = Command::new("rg");
    command.args([
        "--json",
        "--no-messages",
        "--no-config",
        "--mmap",
        "--fixed-strings",
        "--glob",
        "*.jsonl",
        "--glob",
        "*.json",
    ]);
    for term in roots.iter().filter_map(|root| root.to_str()) {
        command.args(["-e", term]);
    }
    command.args(search.iter().filter(|path| path.exists()));
    let mut child = command.stdout(Stdio::piped()).spawn().map_err(|error| {
        io::Error::new(
            error.kind(),
            format!("--global session scan needs ripgrep (`rg`): {error}"),
        )
    })?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| io::Error::other("ripgrep session scan returned no stdout"))?;
    let mut selected = HashMap::<PathBuf, Vec<String>>::new();
    for line in BufReader::new(stdout).lines() {
        let line = line?;
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
        if !tool_call && !path.contains("/.gemini/") {
            continue;
        }
        selected.entry(path.into()).or_default().push(text.into());
    }
    let status = child.wait()?;
    if !status.success() && status.code() != Some(1) {
        return Err(io::Error::other(format!(
            "ripgrep global session scan failed with {status}"
        )));
    }
    Ok(selected
        .into_iter()
        .filter(|(path, _)| !excluded.contains(path))
        .filter_map(|(path, lines)| {
            let candidate = session_candidate_from_path(&path)?;
            if candidate.agent == AGENT_GEMINI {
                return repository_session(&candidate);
            }
            let content = lines.concat();
            let session = parse_session_content(
                candidate.agent,
                &candidate.path,
                candidate.updated,
                &content,
            )?;
            let count = session.events.tools.len();
            Some((session, count))
        })
        .collect())
}

fn session_header(path: &Path) -> String {
    let Ok(mut file) = std::fs::File::open(path) else {
        return String::new();
    };
    let mut prefix = String::new();
    let Ok(_) = file.by_ref().take(256 * 1024).read_to_string(&mut prefix) else {
        return String::new();
    };
    prefix
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
    roots.sort_by(|left, right| {
        right
            .components()
            .count()
            .cmp(&left.components().count())
            .then_with(|| left.cmp(right))
    });
    roots.dedup();
    roots
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
        normalized.strip_prefix(lexical(root)).ok().map(|relative| {
            let value = relative.to_string_lossy().replace('\\', "/");
            if value.is_empty() { ".".into() } else { value }
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
    use agent_session::{SessionEvents, TokenUsage, ToolEvent, ToolPath};
    use std::collections::BTreeMap;
    use std::time::SystemTime;

    fn tool(ts_ms: i64, status: &str, paths: Vec<ToolPath>) -> ToolEvent {
        ToolEvent {
            ts_ms: Some(ts_ms),
            prompt_index: 0,
            tool_name: "Tool".into(),
            category: "file".into(),
            command: String::new(),
            command_name: String::new(),
            effect: String::new(),
            process_chain: Vec::new(),
            status: status.into(),
            path_groups: Vec::new(),
            paths,
            domains: Vec::new(),
            call_id: None,
            invoked_skill: String::new(),
            skill: String::new(),
            task_path: Vec::new(),
        }
    }

    fn session(tools: Vec<ToolEvent>) -> AgentSession {
        AgentSession {
            agent_type: AGENT_CODEX.into(),
            session_id: "session".into(),
            conversation_id: None,
            display_id: "session".into(),
            path: "/sessions/session.jsonl".into(),
            updated: SystemTime::UNIX_EPOCH,
            start_timestamp_ms: None,
            end_timestamp_ms: None,
            model: None,
            usage: TokenUsage::default(),
            model_usage: BTreeMap::new(),
            tools: BTreeMap::new(),
            files: BTreeMap::new(),
            prompt_preview: None,
            duration_ms: 0,
            cwd: Some("/repo".into()),
            last_message_at: None,
            events: SessionEvents {
                prompts: Vec::new(),
                tools,
                llm_responses: Vec::new(),
                plan: Vec::new(),
            },
        }
    }

    #[test]
    fn lexical_paths_cannot_escape_a_worktree() {
        let roots = vec![PathBuf::from("/repo")];
        assert_eq!(
            resolve_path("src/../lib.rs", Some(Path::new("/repo")), &roots),
            Some("lib.rs".into())
        );
        assert_eq!(
            resolve_path(".", Some(Path::new("/repo")), &roots),
            Some(".".into())
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

    #[test]
    fn path_prefixes_identify_directories_without_turning_files_into_scopes() {
        let paths = vec![
            "src/main.rs".into(),
            "src/model/lib.rs".into(),
            "README.md".into(),
        ];
        let directories = directory_prefixes(&paths);
        assert!(directories.contains("src"));
        assert!(directories.contains("src/model"));
        assert!(!directories.contains("src/main.rs"));
        assert!(!directories.contains("README.md"));
    }

    #[test]
    fn agent_project_directories_match_exact_repository_roots() {
        let root = Path::new("/home/user/repo");
        let hash = repository_hash(root);
        let gemini = PathBuf::from(format!(
            "/home/user/.gemini/tmp/{}/chats/session.json",
            hash
        ));
        assert_eq!(gemini_project_hash(&gemini).as_deref(), Some(hash.as_str()));

        let claude = Path::new("/home/user/.claude/projects/-home-user-repo/session.jsonl");
        let sibling = Path::new("/home/user/.claude/projects/-home-user-repo-x/session.jsonl");
        assert_eq!(
            claude_project_name(claude).as_deref(),
            Some("-home-user-repo")
        );
        assert_ne!(
            claude_project_name(sibling),
            Some(encoded_claude_root(root))
        );
    }

    #[test]
    fn cursor_project_directories_match_roots_by_encoding_not_inversion() {
        let root = Path::new("/home/user/my-repo");
        let transcript = Path::new(
            "/home/user/.cursor/projects/home-user-my-repo/agent-transcripts/abc/abc.jsonl",
        );
        assert_eq!(
            cursor_project_name(transcript).as_deref(),
            Some("home-user-my-repo")
        );
        assert_eq!(encoded_cursor_root(root), "home-user-my-repo");

        // The encoding cannot be inverted, so encode the root and compare instead.
        let sibling = Path::new(
            "/home/user/.cursor/projects/home-user-my-repo-x/agent-transcripts/abc/abc.jsonl",
        );
        assert_ne!(
            cursor_project_name(sibling),
            Some(encoded_cursor_root(root))
        );
        assert_eq!(
            cursor_project_name(Path::new("/home/user/.claude/projects/x/session.jsonl"))
                .as_deref(),
            Some("x"),
            "helper reads the segment after `projects`, callers gate on agent"
        );
    }

    #[test]
    fn cursor_candidates_reach_the_repository_matcher() {
        let root = PathBuf::from("/home/user/my-repo");
        let roots = vec![root.clone()];
        let candidate = |path: &str| SessionCandidate {
            agent: AGENT_CURSOR,
            path: PathBuf::from(path),
            updated: SystemTime::UNIX_EPOCH,
        };

        // Before this, Cursor fell through to the catch-all arm and every
        // candidate was discarded before it was ever parsed.
        assert!(candidate_may_match_repo(
            &candidate("/home/user/.cursor/projects/home-user-my-repo/agent-transcripts/a/a.jsonl"),
            &roots,
            None
        ));
        assert!(!candidate_may_match_repo(
            &candidate("/home/user/.cursor/projects/home-user-other/agent-transcripts/a/a.jsonl"),
            &roots,
            None
        ));
    }

    #[test]
    fn cursor_repository_session_includes_subagent_file_actions() {
        let temp = tempfile::tempdir().expect("tempdir");
        let parent_dir = temp.path().join("agent-transcripts/session");
        let child_dir = parent_dir.join("subagents");
        std::fs::create_dir_all(&child_dir).expect("create Cursor transcript directories");
        let parent = parent_dir.join("session.jsonl");
        std::fs::write(
            &parent,
            [
                r#"{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Friday, Aug 7, 2026, 10:12 PM (UTC-5)</timestamp>\n<user_query>\ncreate child\n</user_query>"}]}}"#,
                r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Task","input":{"description":"Create child","prompt":"make child","subagent_type":"generalPurpose"}}]}}"#,
                r#"{"type":"turn_ended","status":"success"}"#,
            ]
            .join("\n"),
        )
        .expect("write parent transcript");
        std::fs::write(
            child_dir.join("child.jsonl"),
            [
                r#"{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Friday, Aug 7, 2026, 10:12 PM (UTC-5)</timestamp>\n<user_query>\nmake child\n</user_query>"}]}}"#,
                r#"{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"/repo/from-child.rs","contents":"fn child() {}"}}]}}"#,
                r#"{"type":"turn_ended","status":"success"}"#,
            ]
            .join("\n"),
        )
        .expect("write child transcript");

        let candidate = SessionCandidate {
            agent: AGENT_CURSOR,
            path: parent,
            updated: SystemTime::UNIX_EPOCH,
        };
        let (session, source_count) = repository_session(&candidate).expect("repository session");

        assert_eq!(session.tools.get("Write"), Some(&1));
        assert!(session.events.tools.iter().any(|tool| {
            tool.paths
                .iter()
                .any(|path| path.path == "/repo/from-child.rs")
        }));
        assert!(source_count >= 2, "parent Task and child Write are counted");
    }

    #[test]
    fn tied_timestamps_keep_event_order() {
        // Minute-resolution clocks tie often, and ids compare as strings.
        let mut ids: Vec<String> = (0..12).map(|ordinal| format!("s:{ordinal:06}")).collect();
        let expected = ids.clone();
        ids.sort();
        assert_eq!(ids, expected);
    }

    #[test]
    fn nested_worktree_root_wins_over_parent_repository() {
        let roots = vec![
            PathBuf::from("/repo/.worktrees/feature"),
            PathBuf::from("/repo"),
        ];
        assert_eq!(
            relative_to_roots(Path::new("/repo/.worktrees/feature/src/lib.rs"), &roots),
            Some("src/lib.rs".into())
        );
    }

    #[test]
    fn repository_sessions_keep_every_timed_tool_action() {
        let value = session(vec![
            tool(
                1,
                "fail",
                vec![ToolPath {
                    path: "src/failed.rs".into(),
                    access: "write".into(),
                    previous_path: None,
                }],
            ),
            tool(2, "ok", Vec::new()),
            tool(
                3,
                "ok",
                vec![ToolPath {
                    path: "src/read.rs".into(),
                    access: "read".into(),
                    previous_path: None,
                }],
            ),
        ]);
        let mut batch = (Vec::new(), 0);
        append_session(&value, 7, &["/repo".into()], true, &mut batch);
        assert_eq!(batch.0.len(), 3);
        assert!(batch.0[0].actions.is_empty());
        assert!(batch.0[1].actions.is_empty());
        assert_eq!(batch.0[2].actions[0].path, "src/read.rs");
        assert_eq!(batch.1, 7);
    }

    #[test]
    fn external_sessions_keep_only_proven_repository_actions() {
        let value = session(vec![
            tool(1, "ok", Vec::new()),
            tool(
                2,
                "ok",
                vec![ToolPath {
                    path: "src/read.rs".into(),
                    access: "read".into(),
                    previous_path: None,
                }],
            ),
        ]);
        let mut batch = (Vec::new(), 0);
        append_session(&value, 2, &["/repo".into()], false, &mut batch);
        assert_eq!(batch.0.len(), 1);
        assert_eq!(batch.0[0].ts_ms, 2);
    }
}
