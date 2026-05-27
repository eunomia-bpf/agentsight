// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::Serialize;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize)]
struct DiscoveryRow {
    id: &'static str,
    name: &'static str,
    adapter: &'static str,
    command: &'static str,
    available: bool,
    path: Option<String>,
    recommended_capture: &'static str,
}

pub(crate) fn run_discover(json: bool) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let rows = discover_rows();
    if json {
        println!("{}", serde_json::to_string_pretty(&rows)?);
        return Ok(());
    }

    println!(
        "{:<14} {:<10} {:<10} {:<9} recommended",
        "id", "adapter", "command", "available"
    );
    for row in rows {
        println!(
            "{:<14} {:<10} {:<10} {:<9} {}",
            row.id,
            row.adapter,
            row.command,
            if row.available { "yes" } else { "no" },
            row.recommended_capture
        );
    }
    Ok(())
}

fn discover_rows() -> Vec<DiscoveryRow> {
    vec![
        row(
            "claude-code",
            "Claude Code",
            "claude-code",
            "claude",
            "agentsight exec --db record.db --adapter claude-code -- claude -p 'hello' --output-format json",
        ),
        row(
            "gemini-cli",
            "Gemini CLI",
            "gemini-cli",
            "gemini",
            "agentsight exec --db record.db --adapter gemini-cli -- gemini --prompt 'hello' --json",
        ),
        row(
            "openclaw",
            "OpenClaw",
            "openclaw",
            "docker",
            "agentsight trace --db record.db --adapter openclaw --binary-path docker://<container>",
        ),
    ]
}

fn row(
    id: &'static str,
    name: &'static str,
    adapter: &'static str,
    command: &'static str,
    recommended_capture: &'static str,
) -> DiscoveryRow {
    let path = find_on_path(command);
    DiscoveryRow {
        id,
        name,
        adapter,
        command,
        available: path.is_some(),
        path: path.map(|p| p.display().to_string()),
        recommended_capture,
    }
}

fn find_on_path(command: &str) -> Option<PathBuf> {
    if command.contains(std::path::MAIN_SEPARATOR) {
        let path = PathBuf::from(command);
        return is_executable_file(&path).then_some(path);
    }
    let path_var = std::env::var_os("PATH")?;
    std::env::split_paths(&path_var)
        .map(|dir| dir.join(command))
        .find(|candidate| is_executable_file(candidate))
}

#[cfg(unix)]
fn is_executable_file(path: &Path) -> bool {
    use std::os::unix::fs::PermissionsExt;

    path.is_file()
        && path
            .metadata()
            .map(|m| m.permissions().mode() & 0o111 != 0)
            .unwrap_or(false)
}

#[cfg(not(unix))]
fn is_executable_file(path: &Path) -> bool {
    path.is_file()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn discovery_rows_include_supported_agent_adapters() {
        let rows = discover_rows();
        let ids: Vec<_> = rows.iter().map(|row| row.id).collect();
        assert!(ids.contains(&"claude-code"));
        assert!(ids.contains(&"gemini-cli"));
        assert!(ids.contains(&"openclaw"));
    }
}
