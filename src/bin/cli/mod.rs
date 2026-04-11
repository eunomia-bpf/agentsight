//! CLI subcommand modules for agentsight binary
//!
//! This module provides subcommand implementations:
//! - `token`: Query token consumption data
//! - `trace`: Trace agent activity via eBPF
//! - `audit`: Query audit events
//! - `discover`: Discover running AI agents

pub mod token;
pub mod trace;
pub mod audit;
pub mod discover;
pub mod metrics;
#[cfg(feature = "server")]
pub mod serve;

/// Parse period string into TimePeriod
pub fn parse_period(s: &str) -> agentsight::TimePeriod {
    match s {
        "today" => agentsight::TimePeriod::Today,
        "yesterday" => agentsight::TimePeriod::Yesterday,
        "week" => agentsight::TimePeriod::Week,
        "last_week" => agentsight::TimePeriod::LastWeek,
        "month" => agentsight::TimePeriod::Month,
        "last_month" => agentsight::TimePeriod::LastMonth,
        _ => agentsight::TimePeriod::Today,
    }
}

/// Calculate nanosecond timestamp for N hours ago
pub fn hours_ago_ns(hours: u64) -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;
    now.saturating_sub(hours * 3600 * 1_000_000_000)
}
