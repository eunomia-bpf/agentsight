use crate::vis_scene::{
    ActionKind, AnimationFormat, FileAction, SceneInput, build_timeline, encode_animations,
    html_document, render_pixmap, svg_document,
};
use agent_session::{LongitudinalArtifact, LongitudinalOptions, build_longitudinal_artifact};
use chrono::Utc;
use std::collections::{BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

pub fn run_vis(
    requested_path: &Path,
    outputs: &[PathBuf],
    global: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let requested = requested_outputs(outputs)?;
    eprintln!(
        "[agentsight-vis 1/5] repository  {}",
        requested_path.display()
    );
    let repo = repository_root(requested_path)?;
    let since_ms = repository_birth_ms(&repo)?;
    let until_ms = Utc::now().timestamp_millis();

    eprintln!(
        "[agentsight-vis 2/5] sessions    Claude + Codex + Gemini{}",
        if global { " (global path scan)" } else { "" }
    );
    let artifact = build_longitudinal_artifact(&LongitudinalOptions {
        repo: repo.clone(),
        head: Some("HEAD".to_string()),
        since_ms,
        until_ms,
        session_paths: Vec::new(),
        include_git_history: true,
        include_git_details: false,
        include_global_events: global,
    })?;
    eprintln!(
        "[agentsight-vis 3/5] actions     {} sessions · {} tool/LLM events",
        artifact.sessions.len(),
        artifact.events.len()
    );

    let scene_input = scene_input(&artifact);
    drop(artifact);
    let file_action_count = scene_input.actions.len();
    let timeline = build_timeline(scene_input);
    eprintln!(
        "[agentsight-vis 4/5] projection  {file_action_count} file actions · {} coherent layout frames · no directory nodes",
        timeline.frame_count()
    );

    for output in &requested {
        if let Some(parent) = output
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        {
            fs::create_dir_all(parent)?;
        }
    }
    if requested.iter().any(|path| extension(path) == "html") {
        let html = html_document(&timeline)?;
        for output in requested.iter().filter(|path| extension(path) == "html") {
            fs::write(output, &html)?;
        }
    }
    if requested.iter().any(|path| extension(path) == "svg") {
        let svg = svg_document(&timeline);
        for output in requested.iter().filter(|path| extension(path) == "svg") {
            fs::write(output, &svg)?;
        }
    }
    if requested.iter().any(|path| extension(path) == "png") {
        let final_index = timeline.frame_count() - 1;
        let pixmap = render_pixmap(&timeline, timeline.final_frame(), final_index);
        for output in requested.iter().filter(|path| extension(path) == "png") {
            pixmap.save_png(output)?;
        }
    }
    let animations = requested
        .iter()
        .filter_map(|path| match extension(path).as_str() {
            "gif" => Some((path.clone(), AnimationFormat::Gif)),
            "mp4" => Some((path.clone(), AnimationFormat::Mp4)),
            _ => None,
        })
        .collect::<Vec<_>>();
    if !animations.is_empty() {
        eprintln!(
            "[agentsight-vis] rendering   {} frames once → {} animation output{}",
            timeline.frame_count(),
            animations.len(),
            if animations.len() == 1 { "" } else { "s" }
        );
        encode_animations(&timeline, &animations)?;
    }

    for output in &requested {
        eprintln!(
            "[agentsight-vis 5/5] output      {} · {} KiB",
            output.display(),
            fs::metadata(output)?.len().div_ceil(1024)
        );
    }
    Ok(())
}

fn requested_outputs(
    outputs: &[PathBuf],
) -> Result<Vec<PathBuf>, Box<dyn std::error::Error + Send + Sync>> {
    let mut requested = Vec::new();
    let mut seen = HashSet::new();
    for output in outputs {
        let format = extension(output);
        if !matches!(format.as_str(), "html" | "svg" | "png" | "gif" | "mp4") {
            return Err(format!(
                "unsupported output {}; extension must be .html, .svg, .png, .gif, or .mp4",
                output.display()
            )
            .into());
        }
        if seen.insert(output.clone()) {
            requested.push(output.clone());
        }
    }
    if requested.is_empty() {
        return Err("at least one --output is required".into());
    }
    Ok(requested)
}

fn extension(path: &Path) -> String {
    path.extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
}

#[derive(Clone)]
struct DurableChange {
    status: char,
    path: String,
    old_path: Option<String>,
}

fn scene_input(artifact: &LongitudinalArtifact) -> SceneInput {
    let changes = artifact
        .changes
        .iter()
        .map(|change| (change.id.as_str(), change))
        .collect::<HashMap<_, _>>();
    let mut durable_by_event: HashMap<&str, Vec<DurableChange>> = HashMap::new();
    let mut seen = HashSet::new();
    for association in &artifact.associations {
        if association.state != "unique_candidate" {
            continue;
        }
        let Some(candidate) = association.candidates.first() else {
            continue;
        };
        let Some(change) = changes.get(candidate.change_id.as_str()) else {
            continue;
        };
        let Some(status) = change
            .status
            .chars()
            .next()
            .filter(|status| matches!(status, 'A' | 'C' | 'D' | 'R'))
        else {
            continue;
        };
        let key = (
            association.event_id.as_str(),
            status,
            change.path.as_str(),
            change.old_path.as_deref(),
        );
        if seen.insert(key) {
            durable_by_event
                .entry(association.event_id.as_str())
                .or_default()
                .push(DurableChange {
                    status,
                    path: change.path.clone(),
                    old_path: change.old_path.clone(),
                });
        }
    }

    let mut actions = Vec::new();
    for event in artifact.events.iter().filter(|event| event.kind == "tool") {
        let mut handled = BTreeSet::new();
        let mut lifecycle = durable_by_event
            .get(event.id.as_str())
            .cloned()
            .unwrap_or_default();
        lifecycle.sort_by(|left, right| left.path.cmp(&right.path));
        for change in lifecycle {
            let kind = match change.status {
                'A' | 'C' => ActionKind::Create,
                'D' => ActionKind::Delete,
                'R' if change.old_path.is_some() => ActionKind::Rename,
                _ => continue,
            };
            handled.insert(change.path.clone());
            if let Some(old_path) = &change.old_path {
                handled.insert(old_path.clone());
            }
            actions.push(FileAction {
                event_id: event.id.clone(),
                session_id: event.session_id.clone(),
                vendor: event.vendor.clone(),
                timestamp_ms: event.ts_ms,
                kind,
                path: change.path,
                old_path: change.old_path,
            });
        }

        let mut writes = event.write_paths.iter().cloned().collect::<BTreeSet<_>>();
        if writes.is_empty() && event.effect == "write" {
            writes.extend(event.paths.iter().cloned());
        }
        for path in &writes {
            if handled.contains(path) {
                continue;
            }
            actions.push(FileAction {
                event_id: event.id.clone(),
                session_id: event.session_id.clone(),
                vendor: event.vendor.clone(),
                timestamp_ms: event.ts_ms,
                kind: ActionKind::Write,
                path: path.clone(),
                old_path: None,
            });
        }

        let mut reads = event.read_paths.iter().cloned().collect::<BTreeSet<_>>();
        if reads.is_empty()
            && (event.effect == "read"
                || ["read", "search", "glob", "grep"]
                    .iter()
                    .any(|needle| event.action.to_ascii_lowercase().contains(needle)))
        {
            reads.extend(
                event
                    .paths
                    .iter()
                    .filter(|path| !writes.contains(*path))
                    .cloned(),
            );
        }
        for path in reads {
            if handled.contains(&path) || writes.contains(&path) {
                continue;
            }
            actions.push(FileAction {
                event_id: event.id.clone(),
                session_id: event.session_id.clone(),
                vendor: event.vendor.clone(),
                timestamp_ms: event.ts_ms,
                kind: ActionKind::Read,
                path,
                old_path: None,
            });
        }
    }
    SceneInput {
        repository: artifact.repository.name.clone(),
        revision: artifact.repository.head.clone(),
        window_start_ms: artifact.window.since_ms,
        window_end_ms: artifact.window.until_ms,
        session_scope: if artifact.window.global {
            "global_tool_operations"
        } else {
            "repository_identity"
        }
        .to_string(),
        session_count: artifact.sessions.len(),
        actions,
        commit_times: artifact
            .commits
            .iter()
            .filter(|commit| {
                commit.committed_at_ms >= artifact.window.since_ms
                    && commit.committed_at_ms <= artifact.window.until_ms
            })
            .map(|commit| commit.committed_at_ms)
            .collect(),
    }
}

fn repository_root(path: &Path) -> Result<PathBuf, Box<dyn std::error::Error + Send + Sync>> {
    let path = path.canonicalize()?;
    let output = git(&path, &["rev-parse", "--show-toplevel"])?;
    Ok(PathBuf::from(output.trim()).canonicalize()?)
}

fn repository_birth_ms(repo: &Path) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
    let roots = git(repo, &["rev-list", "--max-parents=0", "HEAD"])?;
    roots
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|root| {
            git(repo, &["show", "-s", "--format=%ct", root.trim()])?
                .trim()
                .parse::<i64>()
                .map(|seconds| seconds * 1_000)
                .map_err(|error| error.into())
        })
        .collect::<Result<Vec<_>, Box<dyn std::error::Error + Send + Sync>>>()?
        .into_iter()
        .min()
        .ok_or_else(|| "repository has no root commit".into())
}

fn git(repo: &Path, args: &[&str]) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let output = Command::new("git").args(args).current_dir(repo).output()?;
    if !output.status.success() {
        return Err(format!(
            "git {} failed: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        )
        .into());
    }
    Ok(String::from_utf8(output.stdout)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repeated_outputs_are_deduplicated_and_formats_are_inferred() {
        let values = requested_outputs(&[
            "out/demo.html".into(),
            "out/demo.gif".into(),
            "out/demo.html".into(),
        ])
        .unwrap();
        assert_eq!(values.len(), 2);
        assert_eq!(extension(&values[0]), "html");
        assert_eq!(extension(&values[1]), "gif");
    }

    #[test]
    fn unsupported_output_extension_is_rejected() {
        assert!(requested_outputs(&["demo.json".into()]).is_err());
    }
}
