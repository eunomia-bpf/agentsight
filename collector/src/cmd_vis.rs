use agent_session::{LongitudinalOptions, build_longitudinal_artifact};
use chrono::Utc;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::{Duration, Instant};

const WIDTH: usize = 1200;
const HEIGHT: usize = 675;
const MAX_VISUAL_STEPS: usize = 360;
const RUNTIME: &str = include_str!("../vendor/vis/repository-nebula.iife.js");

pub fn run_vis(
    requested_path: &Path,
    output: &Path,
    global: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let format = output
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    if !matches!(format.as_str(), "html" | "svg" | "png" | "gif" | "mp4") {
        return Err("output extension must be .html, .svg, .png, .gif, or .mp4".into());
    }
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

    let payload = nebula_payload(&artifact);
    let file_event_count = payload["agent_events"].as_array().map_or(0, Vec::len);
    eprintln!(
        "[agentsight-vis 4/5] projection  {file_event_count} file-action events · no directory nodes"
    );
    let html = html_document(&payload)?;
    if let Some(parent) = output
        .parent()
        .filter(|value| !value.as_os_str().is_empty())
    {
        fs::create_dir_all(parent)?;
    }
    if format == "html" {
        fs::write(output, html)?;
    } else {
        render_media(&html, &payload, output, &format)?;
    }
    eprintln!(
        "[agentsight-vis 5/5] output      {} · {} KiB",
        output.display(),
        fs::metadata(output)?.len().div_ceil(1024)
    );
    Ok(())
}

fn render_media(
    html: &str,
    payload: &Value,
    output: &Path,
    format: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let temporary = tempfile::tempdir()?;
    let page = temporary.path().join("repository-nebula.html");
    fs::write(&page, html)?;
    let browser = browser_binary()?;
    let end = payload["meta"]["window_end_ms"]
        .as_i64()
        .unwrap_or_default();
    match format {
        "png" => browser_screenshot(&browser, &page, end, None, output)?,
        "svg" => {
            let dom = browser_dom(&browser, &page, end)?;
            let chart = dom
                .find("<div id=\"chart\"")
                .and_then(|offset| dom[offset..].find("<svg").map(|inner| offset + inner))
                .ok_or("rendered page did not contain the chart SVG")?;
            let end = dom[chart..]
                .find("</svg>")
                .map(|offset| chart + offset + "</svg>".len())
                .ok_or("rendered chart SVG was incomplete")?;
            fs::write(
                output,
                format!(
                    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n{}",
                    &dom[chart..end]
                ),
            )?;
        }
        "gif" | "mp4" => {
            let frames = temporary.path().join("frames");
            fs::create_dir(&frames)?;
            let cursors = animation_cursors(payload);
            eprintln!(
                "[agentsight-vis] rendering   {} layout snapshots (one frame each) with {}",
                cursors.len(),
                browser.display()
            );
            let workers = std::thread::available_parallelism()
                .map_or(1, usize::from)
                .min(4)
                .min(cursors.len());
            let next = AtomicUsize::new(0);
            let completed = AtomicUsize::new(0);
            std::thread::scope(
                |scope| -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
                    let mut handles = Vec::with_capacity(workers);
                    for _ in 0..workers {
                        handles.push(scope.spawn(
                            || -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
                                loop {
                                    let index = next.fetch_add(1, Ordering::Relaxed);
                                    let Some(cursor) = cursors.get(index) else {
                                        break;
                                    };
                                    browser_screenshot(
                                        &browser,
                                        &page,
                                        *cursor,
                                        Some(index),
                                        &frames.join(format!("frame-{index:04}.png")),
                                    )?;
                                    let done = completed.fetch_add(1, Ordering::Relaxed) + 1;
                                    if done % 12 == 0 || done == cursors.len() {
                                        eprintln!(
                                            "[agentsight-vis] frames      {done}/{}",
                                            cursors.len()
                                        );
                                    }
                                }
                                Ok(())
                            },
                        ));
                    }
                    for handle in handles {
                        handle
                            .join()
                            .map_err(|_| "Chromium render worker panicked")??;
                    }
                    Ok(())
                },
            )?;
            encode_animation(&frames, output, format)?;
        }
        _ => unreachable!(),
    }
    Ok(())
}

fn browser_binary() -> Result<PathBuf, Box<dyn std::error::Error + Send + Sync>> {
    if let Some(path) = env::var_os("CHROME")
        .map(PathBuf::from)
        .filter(|path| path.is_file())
    {
        return Ok(path);
    }
    if let Some(home) = dirs::home_dir() {
        let cache = home.join(".cache/ms-playwright");
        let mut versions = fs::read_dir(cache)
            .into_iter()
            .flatten()
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .collect::<Vec<_>>();
        versions.sort();
        for version in versions.into_iter().rev() {
            for suffix in [
                "chrome-linux64/chrome",
                "chrome-linux/chrome",
                "chrome-headless-shell-linux64/headless_shell",
            ] {
                let candidate = version.join(suffix);
                if candidate.is_file() {
                    return Ok(candidate);
                }
            }
        }
    }
    for name in [
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
    ] {
        if Command::new(name)
            .arg("--version")
            .output()
            .is_ok_and(|output| output.status.success())
        {
            return Ok(PathBuf::from(name));
        }
    }
    Err("PNG/SVG/GIF/MP4 export needs Chromium; HTML export has no browser dependency".into())
}

fn browser_url(page: &Path, cursor: i64, layout_step: Option<usize>) -> String {
    let step = layout_step.map_or_else(String::new, |value| format!("&step={value}"));
    format!("file://{}?cursor={cursor}{step}&still=1", page.display())
}

fn browser_args(page: &Path, cursor: i64, layout_step: Option<usize>) -> Vec<String> {
    vec![
        "--headless".into(),
        "--no-sandbox".into(),
        "--disable-gpu".into(),
        "--hide-scrollbars".into(),
        "--run-all-compositor-stages-before-draw".into(),
        "--virtual-time-budget=1600".into(),
        "--force-device-scale-factor=1".into(),
        format!("--window-size={},{}", WIDTH + 64, HEIGHT + 260),
        browser_url(page, cursor, layout_step),
    ]
}

fn browser_screenshot(
    browser: &Path,
    page: &Path,
    cursor: i64,
    layout_step: Option<usize>,
    output: &Path,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    for attempt in 1..=3 {
        let mut args = browser_args(page, cursor, layout_step);
        args.insert(args.len() - 1, format!("--screenshot={}", output.display()));
        let _ = fs::remove_file(output);
        let mut child = Command::new(browser)
            .args(args)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?;
        let started = Instant::now();
        loop {
            if let Some(status) = child.try_wait()? {
                if status.success() && output.is_file() {
                    return Ok(());
                }
                break;
            }
            if started.elapsed() >= Duration::from_secs(30) {
                let _ = child.kill();
                let _ = child.wait();
                break;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
        if attempt < 3 {
            eprintln!(
                "[agentsight-vis] retry       frame {} ({attempt}/3)",
                layout_step.unwrap_or_default()
            );
        }
    }
    Err(format!(
        "Chromium screenshot failed after 3 attempts: {}",
        output.display()
    )
    .into())
}

fn browser_dom(
    browser: &Path,
    page: &Path,
    cursor: i64,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let mut args = browser_args(page, cursor, None);
    args.insert(args.len() - 1, "--dump-dom".into());
    let result = Command::new(browser).args(args).output()?;
    if !result.status.success() {
        return Err(format!(
            "Chromium SVG render failed: {}",
            String::from_utf8_lossy(&result.stderr).trim()
        )
        .into());
    }
    Ok(String::from_utf8(result.stdout)?)
}

fn animation_cursors(payload: &Value) -> Vec<i64> {
    let start = payload["meta"]["window_start_ms"]
        .as_i64()
        .unwrap_or_default();
    let end = payload["meta"]["window_end_ms"].as_i64().unwrap_or(start);
    let mut events = payload["agent_events"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|event| {
            event["ts_ms"].as_i64().map(|timestamp| {
                (
                    timestamp,
                    event["id"].as_str().unwrap_or_default().to_string(),
                )
            })
        })
        .filter(|(timestamp, _)| *timestamp >= start && *timestamp <= end)
        .collect::<Vec<_>>();
    events.sort_unstable();
    if events.is_empty() {
        return vec![end];
    }

    let step_count = events.len().min(MAX_VISUAL_STEPS);
    let mut visual_steps = vec![start; step_count];
    for (index, (timestamp, _)) in events.iter().enumerate() {
        let bucket = (index * step_count / events.len()).min(step_count.saturating_sub(1));
        visual_steps[bucket] = *timestamp;
    }
    visual_steps
}

fn encode_animation(
    frames: &Path,
    output: &Path,
    format: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let input = frames.join("frame-%04d.png");
    let mut command = Command::new("ffmpeg");
    command
        .args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            "8",
            "-i",
        ])
        .arg(input);
    if format == "gif" {
        command.args(["-vf", "fps=8,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a"]);
    } else {
        command.args([
            "-c:v",
            "libx264",
            "-vf",
            "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]);
    }
    let result = command.arg(output).output()?;
    if !result.status.success() {
        return Err(format!(
            "ffmpeg failed: {}",
            String::from_utf8_lossy(&result.stderr).trim()
        )
        .into());
    }
    Ok(())
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

fn nebula_payload(artifact: &agent_session::LongitudinalArtifact) -> Value {
    let changes = artifact
        .changes
        .iter()
        .map(|change| (change.id.as_str(), change))
        .collect::<HashMap<_, _>>();
    let mut durable_by_event: HashMap<&str, Vec<Value>> = HashMap::new();
    let mut seen = HashSet::new();
    for association in &artifact.associations {
        let Some(candidate) = association.candidates.first() else {
            continue;
        };
        let Some(change) = changes.get(candidate.change_id.as_str()) else {
            continue;
        };
        if !matches!(change.status.chars().next(), Some('A' | 'C' | 'D' | 'R')) {
            continue;
        }
        let key = (
            association.event_id.as_str(),
            change.status.as_str(),
            change.path.as_str(),
            change.old_path.as_deref(),
        );
        if !seen.insert(key) {
            continue;
        }
        durable_by_event
            .entry(association.event_id.as_str())
            .or_default()
            .push(json!({
                "status": change.status,
                "path": change.path,
                "old_path": change.old_path,
            }));
    }

    let events = artifact
        .events
        .iter()
        .filter_map(|event| {
            let durable = durable_by_event
                .get(event.id.as_str())
                .cloned()
                .unwrap_or_default();
            let has_file_action = !event.read_paths.is_empty()
                || !event.write_paths.is_empty()
                || (!event.paths.is_empty() && matches!(event.effect.as_str(), "read" | "write"))
                || !durable.is_empty();
            if event.kind != "tool" || !has_file_action {
                return None;
            }
            Some(json!({
                "id": event.id,
                "session_id": event.session_id,
                "vendor": event.vendor,
                "ts_ms": event.ts_ms,
                "kind": event.kind,
                "action": event.action,
                "category": event.category,
                "effect": event.effect,
                "paths": event.paths,
                "read_paths": event.read_paths,
                "write_paths": event.write_paths,
                "durable_changes": durable,
            }))
        })
        .collect::<Vec<_>>();
    let commits = artifact
        .commits
        .iter()
        .filter(|commit| {
            commit.committed_at_ms >= artifact.window.since_ms
                && commit.committed_at_ms <= artifact.window.until_ms
        })
        .map(|commit| json!({ "committed_at_ms": commit.committed_at_ms }))
        .collect::<Vec<_>>();
    json!({
        "meta": {
            "repository": artifact.repository.name,
            "endpoint_revision": artifact.repository.head,
            "window_start_ms": artifact.window.since_ms,
            "window_end_ms": artifact.window.until_ms,
            "session_scope": if artifact.window.global {
                "global_tool_operations"
            } else {
                "repository_identity"
            },
        },
        "agent_events": events,
        "commits": commits,
    })
}

fn html_document(payload: &Value) -> Result<String, serde_json::Error> {
    let payload = serde_json::to_string(payload)?
        .replace('<', "\\u003c")
        .replace('\u{2028}', "\\u2028")
        .replace('\u{2029}', "\\u2029");
    Ok(format!(
        r#"<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="agentsight-vis 0.1"><title>Repository Nebula · AgentSight</title><style>
:root{{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#070b12;color:#dce8f7}}*{{box-sizing:border-box}}body{{margin:0;background:#070b12}}.artifact{{width:{artifact_width}px;min-height:{artifact_height}px;padding:24px 32px;background:#070b12;transition:box-shadow .12s}}.artifact.commit-flash{{box-shadow:inset 0 0 0 2px #efd265,0 0 30px rgba(239,210,101,.42)}}.header{{display:flex;justify-content:space-between;gap:24px;border-bottom:1px solid rgba(135,160,190,.18);padding-bottom:14px}}.eyebrow,.mode{{font:10px ui-monospace,monospace;color:#61d7bf;letter-spacing:.12em;text-transform:uppercase}}.header h1{{font-size:24px;margin:6px 0}}.header p{{font-size:11px;color:#71839a;margin:0}}.mode{{color:#8c9bb0;border:1px solid rgba(135,160,190,.18);padding:7px 9px;border-radius:99px;align-self:flex-start}}.visual{{width:{width}px;height:{height}px;margin-top:14px}}.timeline{{display:grid;grid-template-columns:42px 1fr 190px;gap:12px;align-items:center;border-top:1px solid rgba(135,160,190,.18);padding:14px 0 8px}}.timeline button{{width:36px;height:36px;border-radius:50%;border:1px solid rgba(97,215,191,.4);background:#10231f;color:#61d7bf;cursor:pointer}}.timeline input{{width:100%;accent-color:#61d7bf}}.timeline output{{font:9px ui-monospace,monospace;color:#9bacc0;text-align:right}}.legend{{display:flex;gap:18px;font:9px ui-monospace,monospace;color:#71839a}}.legend i{{display:inline-block;width:13px;height:3px;margin-right:5px;vertical-align:middle}}.footer{{margin-top:8px;color:#7c8ba0;font:9px ui-monospace,monospace}}
</style></head><body><main id="artifact" class="artifact"><header class="header"><div><span class="eyebrow">AgentSight · repository evolution</span><h1 id="view-title"></h1><p id="view-note"></p></div><span id="time-mode" class="mode"></span></header><section class="visual"><div id="chart"></div></section><section class="timeline"><button id="play" aria-label="Play history">▶</button><input id="timeline" type="range"><output id="cursor-label"></output></section><section class="legend"><span><i style="background:#f7ffff"></i>read attention</span><span><i style="background:#ff9678"></i>write ripple</span><span><i style="background:#75f0a9"></i>create</span><span><i style="background:#63dfff"></i>rename</span><span><i style="background:#ff647c"></i>delete</span><span><i style="background:#efd265"></i>commit frame</span></section><footer id="provenance" class="footer"></footer></main>
<script>{runtime}</script><script>const q=new URLSearchParams(location.search);const requested=Number(q.get("cursor"));const payload={payload};if(q.has("step"))payload.meta.render_layout_step=Number(q.get("step"));AgentSightSingle.initialize(payload,"workspace-constellation",{{renderer:"svg",cursorMs:Number.isFinite(requested)&&requested>0?requested:{until},width:{width},height:{height},reducedMotion:q.get("still")==="1"}})</script></body></html>"#,
        artifact_width = WIDTH + 64,
        artifact_height = HEIGHT + 190,
        width = WIDTH,
        height = HEIGHT,
        runtime = RUNTIME,
        payload = payload,
        until = payload_window_end(&payload),
    ))
}

fn payload_window_end(payload: &str) -> i64 {
    serde_json::from_str::<Value>(payload)
        .ok()
        .and_then(|value| value["meta"]["window_end_ms"].as_i64())
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_runtime_is_present() {
        assert!(RUNTIME.contains("AgentSightSingle"));
        assert!(RUNTIME.len() > 100_000);
    }

    #[test]
    fn html_escapes_script_terminators() {
        let html = html_document(&json!({
            "meta": { "window_end_ms": 1 },
            "value": "</script>",
        }))
        .unwrap();
        assert!(html.contains("\\u003c/script>"));
        assert!(!html.contains("\"</script>\""));
    }

    #[test]
    fn animation_cursors_match_every_layout_snapshot_without_sampling() {
        let events = (0..1_000)
            .map(|index| json!({ "id": format!("event-{index:04}"), "ts_ms": 1_000 + index }))
            .collect::<Vec<_>>();
        let payload = json!({
            "meta": { "window_start_ms": 100, "window_end_ms": 3_000 },
            "agent_events": events,
            "commits": [
                { "committed_at_ms": 500 },
                { "committed_at_ms": 1_500 },
                { "committed_at_ms": 2_500 },
            ],
        });
        let cursors = animation_cursors(&payload);

        assert_eq!(cursors.len(), MAX_VISUAL_STEPS);
        assert_eq!(cursors.first(), Some(&1_002));
        assert_eq!(cursors.last(), Some(&1_999));
        assert!(cursors.windows(2).all(|pair| pair[0] <= pair[1]));
        assert!(!cursors.contains(&500));
        assert!(!cursors.contains(&2_500));
    }

    #[test]
    fn duplicate_timestamps_still_keep_distinct_layout_frames() {
        let payload = json!({
            "meta": { "window_start_ms": 100, "window_end_ms": 3_000 },
            "agent_events": [
                { "id": "one", "ts_ms": 1_000 },
                { "id": "two", "ts_ms": 1_000 },
            ],
        });
        assert_eq!(animation_cursors(&payload), vec![1_000, 1_000]);
    }

    #[test]
    fn empty_animation_uses_one_endpoint_frame() {
        let payload = json!({
            "meta": { "window_start_ms": 100, "window_end_ms": 3_000 },
            "agent_events": [],
            "commits": [],
        });
        assert_eq!(animation_cursors(&payload), vec![3_000]);
    }
}
