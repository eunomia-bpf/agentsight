//! SQLite storage submodules
//!
//! Provides unified SQLite-based persistence for all record types:
//! - `audit`: Audit event persistence
//! - `token`: Token usage persistence and querying
//! - `token_consumption`: TokenConsumptionBreakdown persistence and querying
//! - `http`: HTTP request/response persistence
//! - `connection`: Shared connection management utilities

pub mod audit;
pub mod connection;
pub mod http;
pub mod token;
pub mod token_consumption;

// Re-export audit storage
pub use audit::{AuditStore, SqliteStore};

// Re-export token storage
pub use token::{
    TokenStore, TokenQuery,
    TimePeriod, TokenQueryResult, TokenBreakdown, TokenComparison, Trend,
    format_tokens, format_tokens_with_commas,
};

// Re-export token consumption storage
pub use token_consumption::{
    TokenConsumptionStore, TokenConsumptionRecord,
    TokenConsumptionFilter, TokenConsumptionQueryResult,
};

// Re-export HTTP storage
pub use http::HttpStore;

// Re-export connection utilities
pub use connection::{create_connection, default_base_path};
