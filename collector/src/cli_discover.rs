// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::output::{print_discovery, print_json};
use crate::sources::agent_native;
use serde::Serialize;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize)]
pub(crate) struct DiscoveryRow {
    pub(crate) id: &'static str,
    pub(crate) name: &'static str,
    pub(crate) command: &'static str,
    pub(crate) available: bool,
    pub(crate) path: Option<String>,
    pub(crate) recommended_capture: &'static str,
}

pub(crate) fn run_discover(json: bool) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let rows = discover_rows();
    if json {
        print_json(&rows)?;
        return Ok(());
    }

    print_discovery(&rows, &agent_native::count_sessions());
    Ok(())
}

fn discover_rows() -> Vec<DiscoveryRow> {
    crate::agents::AGENTS
        .iter()
        .filter_map(|agent| agent.discover.as_ref())
        .map(|discover| {
            let path = find_on_path(discover.command);
            DiscoveryRow {
                id: discover.id,
                name: discover.display_name,
                command: discover.command,
                available: path.is_some(),
                path: path.map(|p| p.display().to_string()),
                recommended_capture: discover.recommended_capture,
            }
        })
        .collect()
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
    fn discovery_rows_include_supported_agent_views() {
        let rows = discover_rows();
        let ids: Vec<_> = rows.iter().map(|row| row.id).collect();
        assert!(ids.contains(&"claude-code"));
        assert!(ids.contains(&"gemini-cli"));
        assert!(ids.contains(&"openclaw"));
    }
}
