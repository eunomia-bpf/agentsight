//! Storage module - unified persistence layer
//!
//! This module provides storage abstraction with multiple backend support:
//! - SQLite: Local file-based storage (current implementation)
//! - SLS: Alibaba Cloud Log Service (planned)
//!
//! Use `Storage` for a unified interface that combines all storage types.

pub mod sqlite;
mod unified;

// Re-export from sqlite module
pub use sqlite::{
    // Audit storage
    AuditStore, SqliteStore,
    // Token storage
    TokenStore, TokenQuery,
    TimePeriod, TokenQueryResult, TokenBreakdown, TokenComparison, Trend,
    format_tokens, format_tokens_with_commas,
    // Token consumption storage
    TokenConsumptionStore, TokenConsumptionRecord,
    TokenConsumptionFilter, TokenConsumptionQueryResult,
    // HTTP storage
    HttpStore,
    // Connection utilities
    create_connection, default_base_path,
};

// Re-export unified storage
pub use unified::{Storage, StorageBackend, SqliteConfig};
