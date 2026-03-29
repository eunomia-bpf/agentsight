//! Unified Storage - high-level entry point for persistence
//!
//! This module provides a unified interface for storing and querying records.
//! It supports multiple storage backends with a common API.
//!
//! # Architecture
//!
//! ```text
//! storage/
//! ├── mod.rs           # Module declarations and re-exports
//! ├── unified.rs       # Unified Storage facade
//! ├── sqlite/          # SQLite implementation
//! │   ├── mod.rs
//! │   ├── audit.rs     # AuditStore implementation
//! │   ├── token.rs     # TokenStore implementation
//! │   └── connection.rs
//! └── sls/             # SLS implementation (planned)
//!     └── ...
//! ```
//!
//! # Example
//!
//! ```rust,ignore
//! use agentsight::storage::Storage;
//! use agentsight::analyzer::AnalysisResult;
//!
//! // Create default SQLite storage
//! let storage = Storage::sqlite()?;
//!
//! // Store analysis result (automatically routes to correct store)
//! storage.store(&analysis_result)?;
//!
//! // Or access specific stores directly
//! storage.audit().insert(&audit_record)?;
//! storage.token().add(token_record)?;
//! ```

use anyhow::Result;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::analyzer::AnalysisResult;
use super::sqlite::{AuditStore, TokenStore, HttpStore, TokenConsumptionStore};
use super::sqlite::connection::{default_base_path};

/// Storage backend type
#[derive(Debug, Clone, Default)]
pub enum StorageBackend {
    /// SQLite local storage
    #[default]
    Sqlite,
    /// Alibaba Cloud Log Service (planned)
    Sls {
        endpoint: String,
        project: String,
        logstore: String,
        access_key_id: String,
        access_key_secret: String,
    },
    // Future: other backends can be added here
}

/// Configuration for SQLite storage
#[derive(Debug, Clone)]
pub struct SqliteConfig {
    /// Base directory for database files
    pub base_path: PathBuf,
    /// Database filename (shared for all tables)
    pub db_name: String,
    /// Audit table name
    pub audit_table: String,
    /// Token table name
    pub token_table: String,
    /// HTTP table name
    pub http_table: String,
    /// Token consumption breakdown table name
    pub token_consumption_table: String,
    /// Data retention period in days (0 = no limit)
    pub retention_days: u64,
    /// Auto-purge check interval (every N inserts, 0 = disabled)
    pub purge_interval: u64,
}

impl Default for SqliteConfig {
    fn default() -> Self {
        Self {
            base_path: default_base_path(),
            db_name: "agentsight.db".to_string(),
            audit_table: "audit_events".to_string(),
            token_table: "token_records".to_string(),
            http_table: "http_records".to_string(),
            token_consumption_table: "token_consumption".to_string(),
            retention_days: 30,
            purge_interval: 100000,
        }
    }
}

impl SqliteConfig {
    /// Create a new SQLite config with custom base path
    pub fn new(base_path: PathBuf) -> Self {
        Self {
            base_path,
            ..Default::default()
        }
    }

    /// Get database path
    pub fn db_path(&self) -> PathBuf {
        self.base_path.join(&self.db_name)
    }
}

/// Unified storage facade that provides access to all storage types
///
/// This is the main entry point for storage operations, supporting:
/// - Audit record persistence
/// - Token usage persistence and querying
/// - HTTP request/response persistence
/// - Multiple backend support (SQLite, SLS, etc.)
pub struct Storage {
    backend: StorageBackend,
    audit_store: AuditStore,
    token_store: TokenStore,
    http_store: HttpStore,
    token_consumption_store: TokenConsumptionStore,
    /// Data retention period in days (0 = no limit)
    retention_days: u64,
    /// Auto-purge check interval (every N inserts, 0 = disabled)
    purge_interval: u64,
    /// Insert counter for auto-purge triggering
    insert_count: AtomicU64,
}

impl Storage {
    /// Create a new Storage with the specified backend
    pub fn new(backend: StorageBackend) -> Result<Self> {
        match &backend {
            StorageBackend::Sqlite => {
                let config = SqliteConfig::default();
                Self::with_sqlite_config(&config)
            }
            StorageBackend::Sls { .. } => {
                // TODO: Implement SLS storage
                anyhow::bail!("SLS storage backend is not yet implemented");
            }
        }
    }

    /// Create a new Storage with SQLite backend and custom config
    pub fn with_sqlite_config(config: &SqliteConfig) -> Result<Self> {
        let db_path = config.db_path();
        let audit_store = AuditStore::with_table(&db_path, &config.audit_table)?;
        let token_store = TokenStore::with_table(&db_path, &config.token_table);
        let http_store = HttpStore::with_table(&db_path, &config.http_table)?;
        let token_consumption_store =
            TokenConsumptionStore::with_table(&db_path, &config.token_consumption_table)?;

        Ok(Storage {
            backend: StorageBackend::Sqlite,
            audit_store,
            token_store,
            http_store,
            token_consumption_store,
            retention_days: config.retention_days,
            purge_interval: config.purge_interval,
            insert_count: AtomicU64::new(0),
        })
    }

    /// Create a new Storage with default SQLite config
    pub fn sqlite() -> Result<Self> {
        Self::new(StorageBackend::Sqlite)
    }

    /// Get the backend type
    pub fn backend(&self) -> &StorageBackend {
        &self.backend
    }

    /// Get audit storage
    pub fn audit(&self) -> &AuditStore {
        &self.audit_store
    }

    /// Get token storage
    pub fn token(&self) -> &TokenStore {
        &self.token_store
    }

    /// Get HTTP storage
    pub fn http(&self) -> &HttpStore {
        &self.http_store
    }

    /// Get token consumption breakdown storage
    pub fn token_consumption(&self) -> &TokenConsumptionStore {
        &self.token_consumption_store
    }

    /// Store an analysis result (automatically routes to correct store)
    ///
    /// This is the primary method for persisting analysis results.
    /// It automatically dispatches to the appropriate store based on the result type.
    /// Periodically triggers data purge based on `purge_interval` configuration.
    pub fn store(&self, result: &AnalysisResult) -> Result<i64> {
        if let AnalysisResult::Http(_) = result {
            return Ok(0);
        }
        log::debug!("Storing analysis result: {:?}", result);
        let id = match result {
            AnalysisResult::Audit(record) => self.audit_store.insert(record),
            AnalysisResult::Token(record) => self.token_store.insert(record),
            AnalysisResult::Message(_msg) => {
                log::trace!("Message storage not implemented, skipping");
                Ok(0)
            }
            AnalysisResult::PromptTokens(_count) => {
                log::trace!("Prompt token count storage not implemented, skipping");
                Ok(0)
            }
            AnalysisResult::Http(record) => self.http_store.insert(record),
            AnalysisResult::TokenConsumption(breakdown) => {
                self.token_consumption_store.insert(
                    breakdown,
                    breakdown.timestamp_ns,
                    breakdown.pid,
                    &breakdown.comm,
                )
            }
        }?;

        // Auto-purge check: trigger every `purge_interval` inserts
        if self.purge_interval > 0 && self.retention_days > 0 {
            let count = self.insert_count.fetch_add(1, Ordering::Relaxed) + 1;
            if count % self.purge_interval == 0 {
                if let Err(e) = self.purge_expired() {
                    log::warn!("Auto-purge failed: {}", e);
                }
            }
        }

        Ok(id)
    }

    /// Purge records older than the configured retention period
    ///
    /// Deletes rows from all tables where `timestamp_ns` is older than
    /// `now - retention_days`. Returns the total number of deleted rows.
    ///
    /// This is called automatically by `store()` every `purge_interval` inserts,
    /// but can also be called manually.
    pub fn purge_expired(&self) -> Result<u64> {
        if self.retention_days == 0 {
            return Ok(0);
        }

        let cutoff_ns = Self::retention_cutoff_ns(self.retention_days);
        let mut total_deleted = 0u64;

        let audit_deleted = self.audit_store.purge_before(cutoff_ns)?;
        total_deleted += audit_deleted;

        let token_deleted = self.token_store.purge_before(cutoff_ns)?;
        total_deleted += token_deleted;

        let http_deleted = self.http_store.purge_before(cutoff_ns)?;
        total_deleted += http_deleted;

        let consumption_deleted = self.token_consumption_store.purge_before(cutoff_ns)?;
        total_deleted += consumption_deleted;

        if total_deleted > 0 {
            log::info!(
                "Purged {} expired records (retention={}d, audit={}, token={}, http={}, consumption={})",
                total_deleted, self.retention_days,
                audit_deleted, token_deleted, http_deleted, consumption_deleted,
            );
        }

        Ok(total_deleted)
    }

    /// Compute the cutoff timestamp for retention
    fn retention_cutoff_ns(retention_days: u64) -> u64 {
        let now_ns = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0);
        let retention_ns = retention_days * 24 * 3600 * 1_000_000_000;
        now_ns.saturating_sub(retention_ns)
    }

    /// Store multiple analysis results
    ///
    /// Returns the number of successfully stored records.
    pub fn store_all(&self, results: &[AnalysisResult]) -> Result<usize> {
        let mut count = 0;
        for result in results {
            self.store(result)?;
            count += 1;
        }
        Ok(count)
    }

    /// Execute WAL checkpoint on all store connections.
    ///
    /// Flushes WAL data back to the main database file and truncates the
    /// `-wal` / `-shm` files. Should be called during graceful shutdown.
    ///
    /// Since all stores share the same database file, a successful checkpoint
    /// on any one connection covers the entire database. We try all connections
    /// and report the first error (if any).
    pub fn checkpoint(&self) -> Result<()> {
        // Only need one successful checkpoint since all stores share the same db,
        // but we try on audit_store first and fall through if it fails.
        if let Err(e) = self.audit_store.checkpoint() {
            log::warn!("Audit store checkpoint failed: {}, trying token store", e);
            if let Err(e2) = self.token_store.checkpoint() {
                log::warn!("Token store checkpoint failed: {}, trying http store", e2);
                self.http_store.checkpoint()?;
            }
        }
        log::info!("WAL checkpoint completed");
        Ok(())
    }
}

impl Drop for Storage {
    fn drop(&mut self) {
        if let Err(e) = self.checkpoint() {
            log::warn!("WAL checkpoint during Storage drop failed: {}", e);
        }
    }
}
