//! SQLite connection management
//!
//! Provides unified database connection handling with common configuration.

use anyhow::{Context, Result};
use rusqlite::Connection;
use std::path::{Path, PathBuf};

/// Default base directory for SQLite databases
pub fn default_base_path() -> PathBuf {
    crate::config::default_base_path()
}

/// Create a new SQLite connection with common settings
///
/// This function:
/// - Creates parent directories if needed
/// - Opens the database connection
/// - Enables WAL mode for better concurrent read performance
pub fn create_connection(path: &Path) -> Result<Connection> {
    // Ensure parent directory exists
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)
            .with_context(|| format!("Failed to create directory: {:?}", parent))?;
    }

    let conn =
        Connection::open(path).with_context(|| format!("Failed to open SQLite: {:?}", path))?;

    // Enable WAL mode for better concurrent read performance
    conn.execute_batch("PRAGMA journal_mode=WAL;")?;

    Ok(conn)
}

/// Execute a WAL checkpoint on the given connection.
///
/// Uses `TRUNCATE` mode which:
/// 1. Writes all WAL frames back to the database
/// 2. Truncates the WAL file to zero bytes
/// 3. Clears the shared-memory index
///
/// This should be called during graceful shutdown to ensure
/// the `-wal` and `-shm` files are cleaned up.
pub fn wal_checkpoint(conn: &Connection) -> Result<()> {
    conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE);")
        .context("Failed to execute WAL checkpoint")?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn test_create_connection() {
        let test_path = PathBuf::from("/tmp/test_agentsight_connection.db");
        
        // Clean up if exists
        let _ = fs::remove_file(&test_path);
        
        let conn = create_connection(&test_path).unwrap();
        drop(conn);
        
        assert!(test_path.exists());
        
        // Cleanup
        fs::remove_file(&test_path).ok();
    }
}
