//! Audit analysis module
//!
//! Provides `AuditAnalyzer` for extracting audit records from aggregated results.

mod analyzer;
mod record;

pub use analyzer::AuditAnalyzer;
pub use record::{AuditEventType, AuditExtra, AuditRecord, AuditSummary};
