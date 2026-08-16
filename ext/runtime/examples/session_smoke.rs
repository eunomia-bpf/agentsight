// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use agentsight_ext_runtime::ExtRuntime;
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let component = std::env::args()
        .nth(1)
        .ok_or("usage: session_smoke <component.wasm>")?;
    let bytes = fs::read(component)?;
    let content = r#"{"timestamp":"2026-08-14T00:00:00Z","type":"session_meta","payload":{"id":"smoke","cwd":"/tmp/project"}}
{"timestamp":"2026-08-14T00:00:01Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"inspect this repository"}]}}
"#;
    let parsed = ExtRuntime::new()?.session_parse(
        &bytes,
        "codex",
        "/tmp/.codex/sessions/2026/08/14/smoke.jsonl",
        1_786_665_600_000,
        content,
    )?;
    let parsed = parsed.ok_or("session component returned no session")?;
    if !parsed.contains("smoke") || !parsed.contains("inspect this repository") {
        return Err("session component returned unexpected output".into());
    }

    let windows_content = r#"{"timestamp":"2026-08-14T00:00:00Z","type":"user","message":{"role":"user","content":"inspect the Windows checkout"}}
"#;
    let windows = ExtRuntime::new()?
        .session_parse(
            &bytes,
            "claude",
            r"C:\Users\agent\.claude\projects\repo\windows-session.jsonl",
            1_786_665_600_000,
            windows_content,
        )?
        .ok_or("session component returned no Windows session")?;
    if !windows.contains(r#""session_id":"windows-session""#) {
        return Err("session component did not normalize the Windows path".into());
    }
    println!("{parsed}");
    Ok(())
}
