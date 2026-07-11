// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

pub(crate) fn agentsight_state_dir_for_home(home: &Path) -> PathBuf {
    home.join(".agentsight")
}

pub(crate) fn ensure_agentsight_state_dir() -> io::Result<Option<PathBuf>> {
    let Some(home) = dirs::home_dir() else {
        return Ok(None);
    };
    ensure_agentsight_state_dir_for_home(&home).map(Some)
}

pub(crate) fn ensure_agentsight_state_dir_for_home(home: &Path) -> io::Result<PathBuf> {
    let dir = agentsight_state_dir_for_home(home);
    fs::create_dir_all(&dir)?;
    restrict_state_dir_permissions(&dir)?;
    Ok(dir)
}

#[cfg(unix)]
fn restrict_state_dir_permissions(dir: &Path) -> io::Result<()> {
    use std::os::unix::fs::PermissionsExt;

    let permissions = fs::Permissions::from_mode(0o700);
    fs::set_permissions(dir, permissions)
}

#[cfg(not(unix))]
fn restrict_state_dir_permissions(_dir: &Path) -> io::Result<()> {
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn agentsight_state_dir_is_home_relative() {
        assert_eq!(
            agentsight_state_dir_for_home(Path::new("/tmp/agentsight-home")),
            PathBuf::from("/tmp/agentsight-home/.agentsight")
        );
    }

    #[cfg(unix)]
    #[test]
    fn ensure_agentsight_state_dir_sets_user_only_mode() {
        use std::os::unix::fs::PermissionsExt;

        let temp = tempfile::tempdir().unwrap();
        let dir = temp.path().join(".agentsight");
        fs::create_dir(&dir).unwrap();
        fs::set_permissions(&dir, fs::Permissions::from_mode(0o777)).unwrap();

        ensure_agentsight_state_dir_for_home(temp.path()).unwrap();

        let mode = fs::metadata(&dir).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o700);
    }
}
