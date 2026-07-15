// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

pub(crate) fn sessions_dir() -> Result<std::path::PathBuf, std::io::Error> {
    std::env::current_dir()
}

/// List AgentSight record DB files in the current directory, sorted newest-first.
pub(crate) fn sorted_session_dbs(dir: &std::path::Path) -> Vec<std::fs::DirEntry> {
    let mut entries: Vec<_> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|e| e.ok())
        .filter(|e| is_default_record_db(&e.path()))
        .collect();
    entries.sort_by_key(|e| std::cmp::Reverse(e.metadata().ok().and_then(|m| m.modified().ok())));
    entries
}

fn is_default_record_db(path: &std::path::Path) -> bool {
    path.extension().is_some_and(|ext| ext == "db")
        && path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.starts_with("agentsight-"))
}

pub(crate) fn latest_session_db() -> Option<String> {
    let dir = sessions_dir().ok()?;
    sorted_session_dbs(&dir)
        .first()
        .map(|e| e.path().to_string_lossy().to_string())
}

pub(crate) fn run_db_list() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let dir = sessions_dir()?;
    let entries = sorted_session_dbs(&dir);
    crate::output::print_session_list(&dir, &entries);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;

    #[test]
    fn session_db_listing_uses_agentsight_dbs_in_given_directory() {
        let temp = tempfile::tempdir().unwrap();
        File::create(temp.path().join("agentsight-20260616-120000.db")).unwrap();
        File::create(temp.path().join("other.db")).unwrap();
        File::create(temp.path().join("agentsight-note.txt")).unwrap();

        let entries = sorted_session_dbs(temp.path());
        assert_eq!(entries.len(), 1);
        assert_eq!(
            entries[0].file_name().to_string_lossy(),
            "agentsight-20260616-120000.db"
        );
    }
}
