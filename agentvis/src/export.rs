use crate::{RepositoryTraceOptions, build_repository_trace};
use base64::{Engine, engine::general_purpose::STANDARD};
use headless_chrome::{Browser, LaunchOptions, protocol::cdp::Emulation};
use serde_json::json;
use std::collections::HashSet;
use std::env;
use std::ffi::OsStr;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;
use std::time::{Duration, Instant};

const WIDTH: u32 = 1264;
const HEIGHT: u32 = 936;
const RUNTIME: &str = include_str!("../vendor/vis/repository-nebula.iife.js");

pub fn run_vis(
    repo: &Path,
    outputs: &[PathBuf],
    global: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let started = Instant::now();
    let outputs = requested_outputs(outputs)?;
    eprintln!("[agentvis 1/5] repository  {}", repo.display());
    eprintln!(
        "[agentvis 2/5] sessions    scanning Claude + Codex + Gemini{}",
        if global { " globally" } else { "" }
    );
    let scan = Instant::now();
    let trace = build_repository_trace(&RepositoryTraceOptions {
        repo: repo.into(),
        global,
    })?;
    eprintln!(
        "[agentvis 3/5] actions     {} sessions · {} source events · {} tool actions · {} file actions · {:.1}s",
        trace.session_count,
        trace.source_event_count,
        trace.events.len(),
        trace.file_action_count,
        scan.elapsed().as_secs_f32()
    );
    let payload = json!({
        "meta": {
            "repository": trace.repository,
            "endpoint_revision": trace.revision,
            "window_start_ms": trace.start_ms,
            "window_end_ms": trace.end_ms,
            "session_scope": if trace.global { "global_tool_operations" } else { "repository_identity" },
        },
        "events": trace.events,
        "commits": trace.commits_ms.into_iter().map(|committed_at_ms| json!({ "committed_at_ms": committed_at_ms })).collect::<Vec<_>>(),
    });
    let html = html_document(&payload)?;
    for output in &outputs {
        if let Some(parent) = output.parent().filter(|path| !path.as_os_str().is_empty()) {
            fs::create_dir_all(parent)?;
        }
    }
    for output in outputs.iter().filter(|path| extension(path) == "html") {
        fs::write(output, &html)?;
    }
    let media = outputs
        .iter()
        .filter(|path| extension(path) != "html")
        .cloned()
        .collect::<Vec<_>>();
    if !media.is_empty() {
        eprintln!("[agentvis 4/5] render      preparing deterministic layout and media");
        render_media(&html, &media)?;
    }
    for output in &outputs {
        eprintln!(
            "[agentvis 5/5] output      {} · {} KiB",
            output.display(),
            fs::metadata(output)?.len().div_ceil(1024)
        );
    }
    eprintln!(
        "[agentvis] complete    {:.1}s",
        started.elapsed().as_secs_f32()
    );
    Ok(())
}

fn requested_outputs(outputs: &[PathBuf]) -> Result<Vec<PathBuf>, String> {
    let mut seen = HashSet::new();
    let outputs = outputs
        .iter()
        .filter(|path| seen.insert((*path).clone()))
        .cloned()
        .collect::<Vec<_>>();
    if outputs.is_empty() {
        return Err("at least one --output is required".into());
    }
    for output in &outputs {
        if !matches!(
            extension(output).as_str(),
            "html" | "svg" | "png" | "gif" | "mp4"
        ) {
            return Err(format!(
                "unsupported output {}; use .html, .svg, .png, .gif, or .mp4",
                output.display()
            ));
        }
    }
    Ok(outputs)
}

fn extension(path: &Path) -> String {
    path.extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
}

fn render_media(
    html: &str,
    outputs: &[PathBuf],
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let temporary = tempfile::tempdir()?;
    let page = temporary.path().join("repository-nebula.html");
    fs::write(&page, html)?;
    let renderer = BrowserRenderer::open(&page)?;
    if outputs
        .iter()
        .any(|path| matches!(extension(path).as_str(), "gif" | "mp4"))
    {
        let mp4 = renderer.mp4()?;
        let mp4_path = temporary.path().join("repository-nebula.mp4");
        fs::write(&mp4_path, &mp4)?;
        write_copies(&mp4, outputs, "mp4")?;
        if outputs.iter().any(|path| extension(path) == "gif") {
            eprintln!("[agentvis] gif         building bounded-memory palette");
            let palette_path = temporary.path().join("repository-nebula-palette.png");
            let palette = Command::new("ffmpeg")
                .args(["-y", "-hide_banner", "-loglevel", "error", "-i"])
                .arg(&mp4_path)
                .args(["-vf", "fps=8,palettegen=max_colors=128", "-frames:v", "1"])
                .arg(&palette_path)
                .status()
                .map_err(|error| {
                    std::io::Error::new(
                        error.kind(),
                        format!("GIF export needs FFmpeg (`ffmpeg`): {error}"),
                    )
                })?;
            if !palette.success() {
                return Err("ffmpeg GIF palette generation failed".into());
            }
            eprintln!("[agentvis] gif         converting shared MP4");
            let gif_path = temporary.path().join("repository-nebula.gif");
            let status = Command::new("ffmpeg")
                .args(["-y", "-hide_banner", "-loglevel", "error", "-i"])
                .arg(&mp4_path)
                .arg("-i")
                .arg(&palette_path)
                .args([
                    "-lavfi",
                    "fps=8[x];[x][1:v]paletteuse=dither=sierra2_4a",
                    "-loop",
                    "0",
                ])
                .arg(&gif_path)
                .status()?;
            if !status.success() {
                return Err("ffmpeg GIF conversion failed".into());
            }
            write_copies(&fs::read(gif_path)?, outputs, "gif")?;
        }
    }
    if outputs.iter().any(|path| extension(path) == "png") {
        write_copies(
            &renderer.bytes("AgentVis.pngBase64()", false)?,
            outputs,
            "png",
        )?;
    }
    if outputs.iter().any(|path| extension(path) == "svg") {
        let svg = renderer.string("AgentVis.svg()", true)?;
        write_copies(
            format!("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n{svg}").as_bytes(),
            outputs,
            "svg",
        )?;
    }
    Ok(())
}

fn write_copies(bytes: &[u8], outputs: &[PathBuf], format: &str) -> std::io::Result<()> {
    for output in outputs.iter().filter(|path| extension(path) == format) {
        fs::write(output, bytes)?;
    }
    Ok(())
}

struct BrowserRenderer {
    tab: Arc<headless_chrome::Tab>,
    _browser: Browser,
    _profile: tempfile::TempDir,
}

impl BrowserRenderer {
    fn open(page: &Path) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let profile = tempfile::tempdir()?;
        let options = LaunchOptions::default_builder()
            .path(Some(browser_binary()?))
            .user_data_dir(Some(profile.path().into()))
            .headless(true)
            .sandbox(false)
            .window_size(Some((WIDTH, HEIGHT)))
            .idle_browser_timeout(Duration::from_secs(600))
            .args(vec![
                OsStr::new("--hide-scrollbars"),
                OsStr::new("--force-device-scale-factor=1"),
            ])
            .build()?;
        let browser = Browser::new(options)?;
        let tab = browser.new_tab()?;
        tab.call_method(Emulation::SetDeviceMetricsOverride {
            width: WIDTH,
            height: HEIGHT,
            device_scale_factor: 1.0,
            mobile: false,
            scale: None,
            screen_width: Some(WIDTH),
            screen_height: Some(HEIGHT),
            position_x: None,
            position_y: None,
            dont_set_visible_size: None,
            screen_orientation: None,
            viewport: None,
            display_feature: None,
            device_posture: None,
        })?;
        tab.navigate_to(&format!("file://{}?still=1", page.display()))?
            .wait_until_navigated()?;
        let started = Instant::now();
        while !tab
            .evaluate("window.__AGENTVIS_READY__ === true", false)
            .ok()
            .and_then(|object| object.value)
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            if started.elapsed() > Duration::from_secs(120) {
                return Err("visual renderer did not become ready".into());
            }
            std::thread::sleep(Duration::from_millis(20));
        }
        Ok(Self {
            tab,
            _browser: browser,
            _profile: profile,
        })
    }

    fn string(
        &self,
        script: &str,
        await_promise: bool,
    ) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        self.tab
            .evaluate(script, await_promise)?
            .value
            .and_then(|value| value.as_str().map(str::to_string))
            .ok_or_else(|| format!("renderer returned no string for {script}").into())
    }

    fn bytes(
        &self,
        script: &str,
        await_promise: bool,
    ) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        Ok(STANDARD.decode(self.string(script, await_promise)?)?)
    }

    fn mp4(&self) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let total = self
            .tab
            .evaluate("AgentVis.beginMp4()", true)?
            .value
            .and_then(|value| value.as_u64())
            .ok_or("MP4 encoder returned no frame count")?;
        eprintln!("[agentvis] frames      0/{total}");
        let mut done = 0;
        while done < total {
            let progress = serde_json::from_str::<Vec<u64>>(
                &self.string("AgentVis.encodeMp4Chunk(48).then(JSON.stringify)", true)?,
            )?;
            done = progress.first().copied().unwrap_or(done);
            eprintln!("[agentvis] frames      {done}/{total}");
        }
        self.bytes("AgentVis.finishMp4()", true)
    }
}

fn browser_binary() -> Result<PathBuf, String> {
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
                let path = version.join(suffix);
                if path.is_file() {
                    return Ok(path);
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
            return Ok(name.into());
        }
    }
    Err("PNG/SVG/GIF/MP4 export needs Chromium; HTML has no browser dependency".into())
}

fn html_document(payload: &serde_json::Value) -> Result<String, serde_json::Error> {
    let payload = serde_json::to_string(payload)?
        .replace('<', "\\u003c")
        .replace('\u{2028}', "\\u2028")
        .replace('\u{2029}', "\\u2029");
    Ok(format!(
        r#"<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Repository Nebula · agentvis</title><style>
:root{{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#070b12;color:#dce8f7}}*{{box-sizing:border-box}}body{{margin:0;background:#070b12}}.artifact{{width:1264px;min-height:865px;padding:24px 32px;background:#070b12;transition:box-shadow .12s}}.artifact.commit-flash{{box-shadow:inset 0 0 0 2px #efd265,0 0 30px rgba(239,210,101,.42)}}.header{{display:flex;justify-content:space-between;gap:24px;border-bottom:1px solid rgba(135,160,190,.18);padding-bottom:14px}}.eyebrow,.mode{{font:10px ui-monospace,monospace;color:#61d7bf;letter-spacing:.12em;text-transform:uppercase}}.header h1{{font-size:24px;margin:6px 0}}.header p{{font-size:11px;color:#71839a;margin:0}}.mode{{color:#8c9bb0;border:1px solid rgba(135,160,190,.18);padding:7px 9px;border-radius:99px;align-self:flex-start}}.visual{{width:1200px;height:675px;margin-top:14px}}.timeline{{display:grid;grid-template-columns:42px 1fr 190px;gap:12px;align-items:center;border-top:1px solid rgba(135,160,190,.18);padding:14px 0 8px}}.timeline button{{width:36px;height:36px;border-radius:50%;border:1px solid rgba(97,215,191,.4);background:#10231f;color:#61d7bf}}.timeline input{{width:100%;accent-color:#61d7bf}}.timeline output{{font:9px ui-monospace,monospace;color:#9bacc0;text-align:right}}.legend{{display:flex;gap:18px;font:9px ui-monospace,monospace;color:#71839a}}.legend i{{display:inline-block;width:13px;height:3px;margin-right:5px;vertical-align:middle}}.footer{{margin-top:8px;color:#7c8ba0;font:9px ui-monospace,monospace}}
</style></head><body><main id="artifact" class="artifact"><header class="header"><div><span class="eyebrow">agentvis · repository evolution</span><h1 id="view-title"></h1><p id="view-note"></p></div><span class="mode">Agent event time</span></header><section class="visual"><div id="chart"></div></section><section class="timeline"><button id="play">▶</button><input id="timeline" type="range"><output id="cursor-label"></output></section><section class="legend"><span><i style="background:#f7ffff"></i>read attention</span><span><i style="background:#ff9678"></i>write ripple</span><span><i style="background:#75f0a9"></i>create</span><span><i style="background:#63dfff"></i>rename</span><span><i style="background:#ff647c"></i>delete</span><span><i style="background:#efd265"></i>commit frame</span></section><footer id="provenance" class="footer"></footer></main><script>{RUNTIME}</script><script>AgentVis.initialize({payload})</script></body></html>"#
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn output_formats_are_inferred_and_deduplicated() {
        let outputs =
            requested_outputs(&["x.html".into(), "x.gif".into(), "x.html".into()]).unwrap();
        assert_eq!(outputs.len(), 2);
        assert!(requested_outputs(&["x.pdf".into()]).is_err());
    }

    #[test]
    fn html_is_self_contained_and_script_safe() {
        let html = html_document(&json!({ "value": "</script>" })).unwrap();
        assert!(html.contains("AgentVis.initialize"));
        assert!(!html.contains("\"</script>\""));
    }
}
