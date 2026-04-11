//! Token usage storage and querying
//!
//! Uses SQLite for persistent storage of token usage records.

use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use chrono::{Utc, Datelike};
use serde::{Deserialize, Serialize};
use rusqlite::{params, Connection};

use crate::analyzer::TokenRecord;
use super::connection::{create_connection, default_base_path, wal_checkpoint};

/// Time period for queries
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TimePeriod {
    Today,
    Yesterday,
    Week,
    LastWeek,
    Month,
    LastMonth,
}

impl std::fmt::Display for TimePeriod {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TimePeriod::Today => write!(f, "今天"),
            TimePeriod::Yesterday => write!(f, "昨天"),
            TimePeriod::Week => write!(f, "本周"),
            TimePeriod::LastWeek => write!(f, "上周"),
            TimePeriod::Month => write!(f, "本月"),
            TimePeriod::LastMonth => write!(f, "上月"),
        }
    }
}

impl TimePeriod {
    /// Get time range for this period (start_ns, end_ns)
    pub fn time_range(&self) -> (u64, u64) {
        let now = Utc::now();
        let now_naive = now.naive_utc();
        
        let (start, end) = match self {
            TimePeriod::Today => {
                let start = now_naive.date().and_hms_opt(0, 0, 0).unwrap();
                let end = now_naive.date().and_hms_opt(23, 59, 59).unwrap();
                (start, end)
            }
            TimePeriod::Yesterday => {
                let yesterday = now_naive.date() - chrono::Duration::days(1);
                let start = yesterday.and_hms_opt(0, 0, 0).unwrap();
                let end = yesterday.and_hms_opt(23, 59, 59).unwrap();
                (start, end)
            }
            TimePeriod::Week => {
                // Start from Monday of current week
                let weekday = now.weekday().num_days_from_monday();
                let monday = now_naive.date() - chrono::Duration::days(weekday as i64);
                let start = monday.and_hms_opt(0, 0, 0).unwrap();
                (start, now_naive)
            }
            TimePeriod::LastWeek => {
                let weekday = now.weekday().num_days_from_monday();
                let this_monday = now_naive.date() - chrono::Duration::days(weekday as i64);
                let last_monday = this_monday - chrono::Duration::weeks(1);
                let last_sunday = last_monday + chrono::Duration::days(6);
                let start = last_monday.and_hms_opt(0, 0, 0).unwrap();
                let end = last_sunday.and_hms_opt(23, 59, 59).unwrap();
                (start, end)
            }
            TimePeriod::Month => {
                let first_day = now_naive.date().with_day(1).unwrap();
                let start = first_day.and_hms_opt(0, 0, 0).unwrap();
                (start, now_naive)
            }
            TimePeriod::LastMonth => {
                let first_day_this_month = now_naive.date().with_day(1).unwrap();
                let last_day_last_month = first_day_this_month - chrono::Duration::days(1);
                let first_day_last_month = last_day_last_month.with_day(1).unwrap();
                let start = first_day_last_month.and_hms_opt(0, 0, 0).unwrap();
                let end = last_day_last_month.and_hms_opt(23, 59, 59).unwrap();
                (start, end)
            }
        };
        
        let start_ns = start.and_utc().timestamp_nanos_opt().unwrap_or(0) as u64;
        let end_ns = end.and_utc().timestamp_nanos_opt().unwrap_or(0) as u64;
        
        (start_ns, end_ns)
    }
    
    /// Get previous period for comparison
    pub fn previous_period(&self) -> TimePeriod {
        match self {
            TimePeriod::Today => TimePeriod::Yesterday,
            TimePeriod::Yesterday => TimePeriod::Today, // No previous for yesterday
            TimePeriod::Week => TimePeriod::LastWeek,
            TimePeriod::LastWeek => TimePeriod::Week,
            TimePeriod::Month => TimePeriod::LastMonth,
            TimePeriod::LastMonth => TimePeriod::Month,
        }
    }
}

/// Token usage breakdown by agent/task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenBreakdown {
    /// Agent/task name
    pub name: String,
    /// Total tokens
    pub total_tokens: u64,
    /// Input tokens
    pub input_tokens: u64,
    /// Output tokens
    pub output_tokens: u64,
    /// Number of requests
    pub request_count: u64,
    /// Percentage of total
    pub percentage: f64,
}

/// Token query result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenQueryResult {
    /// Time period description
    pub period: String,
    /// Total input tokens
    pub input_tokens: u64,
    /// Total output tokens
    pub output_tokens: u64,
    /// Total tokens
    pub total_tokens: u64,
    /// Number of requests
    pub request_count: u64,
    /// Comparison with previous period (if requested)
    pub comparison: Option<TokenComparison>,
    /// Breakdown by agent (if requested)
    pub breakdown: Vec<TokenBreakdown>,
}

impl TokenQueryResult {
    /// Format total tokens with K/M suffix
    pub fn formatted_total(&self) -> String {
        format_tokens(self.total_tokens)
    }
    
    /// Format input tokens with K/M suffix
    pub fn formatted_input(&self) -> String {
        format_tokens(self.input_tokens)
    }
    
    /// Format output tokens with K/M suffix
    pub fn formatted_output(&self) -> String {
        format_tokens(self.output_tokens)
    }
}

/// Comparison with previous period
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenComparison {
    /// Previous period total tokens
    pub previous_total: u64,
    /// Change amount (can be negative)
    pub change: i64,
    /// Change percentage
    pub change_percent: f64,
    /// Trend direction
    pub trend: Trend,
}

impl TokenComparison {
    /// Format the change with sign
    pub fn formatted_change(&self) -> String {
        let sign = if self.change >= 0 { "+" } else { "" };
        let change_formatted = format_tokens(self.change.unsigned_abs());
        let percent = format!("{:.0}%", self.change_percent.abs());
        
        if self.change >= 0 {
            format!("{}{} (+{}%)", sign, change_formatted, percent)
        } else {
            format!("-{} (-{}%)", change_formatted, percent)
        }
    }
}

/// Trend direction
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Trend {
    Up,
    Down,
    Flat,
}

/// Format token count with K/M suffix
pub fn format_tokens(count: u64) -> String {
    if count >= 1_000_000 {
        format!("{:.1}M", count as f64 / 1_000_000.0)
    } else if count >= 1_000 {
        format!("{:.1}K", count as f64 / 1_000.0)
    } else {
        format!("{}", count)
    }
}

/// Format token count with commas
pub fn format_tokens_with_commas(count: u64) -> String {
    let s = count.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().enumerate() {
        if i > 0 && (s.len() - i) % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result
}

/// Token storage using SQLite
pub struct TokenStore {
    /// SQLite connection
    conn: Connection,
    /// Table name
    table_name: String,
}

impl TokenStore {
    /// Create a new token store with default table name
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self::with_table(path, "token_records")
    }

    /// Create a new token store with custom table name
    pub fn with_table(path: impl Into<PathBuf>, table_name: &str) -> Self {
        let path = path.into();
        let conn = create_connection(&path)
            .expect("Failed to open SQLite database for token store");
        let table_name = table_name.to_string();
        
        // Create table if not exists
        let create_table_sql = format!(
            "CREATE TABLE IF NOT EXISTS {} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ns INTEGER NOT NULL,
                pid INTEGER NOT NULL,
                comm TEXT NOT NULL,
                agent TEXT,
                model TEXT,
                provider TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cache_creation_tokens INTEGER,
                cache_read_tokens INTEGER,
                request_id TEXT,
                endpoint TEXT
            )",
            table_name
        );
        conn.execute(&create_table_sql, [])
            .expect("Failed to create token table");
        
        // Create index on timestamp for efficient range queries
        conn.execute(
            &format!("CREATE INDEX IF NOT EXISTS idx_{}_timestamp ON {}(timestamp_ns)", table_name, table_name),
            [],
        ).expect("Failed to create timestamp index");
        
        // Create index on agent for breakdown queries
        conn.execute(
            &format!("CREATE INDEX IF NOT EXISTS idx_{}_agent ON {}(agent)", table_name, table_name),
            [],
        ).expect("Failed to create agent index");
        
        TokenStore { conn, table_name }
    }
    
    /// Get default storage path
    pub fn default_path() -> PathBuf {
        default_base_path().join("tokens.db")
    }
    
    /// Insert a token record (unified interface, matches AuditStore)
    pub fn insert(&self, record: &TokenRecord) -> anyhow::Result<i64> {
        let timestamp_ns = record.timestamp_ns;
        
        let sql = format!(
            "INSERT INTO {} (
                timestamp_ns, pid, comm, agent, model, provider,
                input_tokens, output_tokens, cache_creation_tokens,
                cache_read_tokens, request_id, endpoint
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            self.table_name
        );
        self.conn.execute(
            &sql,
            params![
                timestamp_ns as i64,
                record.pid as i64,
                record.comm,
                record.agent,
                record.model,
                record.provider,
                record.input_tokens as i64,
                record.output_tokens as i64,
                record.cache_creation_tokens.map(|v| v as i64),
                record.cache_read_tokens.map(|v| v as i64),
                record.request_id,
                record.endpoint,
            ],
        ).map_err(|e| anyhow::anyhow!("Failed to insert token record: {}", e))?;
        
        Ok(self.conn.last_insert_rowid())
    }
    
    /// Add a token record (legacy method, kept for backward compatibility)
    pub fn add(&mut self, record: TokenRecord) -> Result<i64, rusqlite::Error> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0);
        
        let sql = format!(
            "INSERT INTO {} (
                timestamp_ns, pid, comm, agent, model, provider,
                input_tokens, output_tokens, cache_creation_tokens,
                cache_read_tokens, request_id, endpoint
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            self.table_name
        );
        self.conn.execute(
            &sql,
            params![
                now as i64,
                record.pid as i64,
                record.comm,
                record.agent,
                record.model,
                record.provider,
                record.input_tokens as i64,
                record.output_tokens as i64,
                record.cache_creation_tokens.map(|v| v as i64),
                record.cache_read_tokens.map(|v| v as i64),
                record.request_id,
                record.endpoint,
            ],
        )?;
        
        Ok(self.conn.last_insert_rowid())
    }
    
    /// Get all records (for compatibility, but not recommended for large datasets)
    pub fn all(&self) -> Vec<TokenRecord> {
        let sql = format!(
            "SELECT id, timestamp_ns, pid, comm, agent, model, provider,
                    input_tokens, output_tokens, cache_creation_tokens,
                    cache_read_tokens, request_id, endpoint
             FROM {} ORDER BY timestamp_ns DESC",
            self.table_name
        );
        let mut stmt = self.conn
            .prepare(&sql)
            .expect("Failed to prepare statement");
        
        stmt.query_map([], |row| {
            Ok(TokenRecord {
                id: row.get(0)?,
                timestamp_ns: row.get::<_, i64>(1)? as u64,
                pid: row.get::<_, i64>(2)? as u32,
                comm: row.get(3)?,
                agent: row.get(4)?,
                model: row.get(5)?,
                provider: row.get(6)?,
                input_tokens: row.get::<_, i64>(7)? as u64,
                output_tokens: row.get::<_, i64>(8)? as u64,
                cache_creation_tokens: row.get::<_, Option<i64>>(9)?.map(|v| v as u64),
                cache_read_tokens: row.get::<_, Option<i64>>(10)?.map(|v| v as u64),
                request_id: row.get(11)?,
                endpoint: row.get(12)?,
                tool_calls: Vec::new(),
                reasoning_content: None,
            })
        })
        .expect("Failed to query")
        .filter_map(|r| r.ok())
        .collect()
    }
    
    /// Get records in time range
    pub fn by_time_range(&self, start_ns: u64, end_ns: u64) -> Vec<TokenRecord> {
        self.by_time_range_owned(start_ns, end_ns)
    }
    
    /// Get owned records in time range
    pub fn by_time_range_owned(&self, start_ns: u64, end_ns: u64) -> Vec<TokenRecord> {
        let sql = format!(
            "SELECT id, timestamp_ns, pid, comm, agent, model, provider,
                    input_tokens, output_tokens, cache_creation_tokens,
                    cache_read_tokens, request_id, endpoint
             FROM {} 
             WHERE timestamp_ns >= ?1 AND timestamp_ns <= ?2
             ORDER BY timestamp_ns DESC",
            self.table_name
        );
        let mut stmt = self.conn
            .prepare(&sql)
            .expect("Failed to prepare statement");
        
        stmt.query_map(params![start_ns as i64, end_ns as i64], |row| {
            Ok(TokenRecord {
                id: row.get(0)?,
                timestamp_ns: row.get::<_, i64>(1)? as u64,
                pid: row.get::<_, i64>(2)? as u32,
                comm: row.get(3)?,
                agent: row.get(4)?,
                model: row.get(5)?,
                provider: row.get(6)?,
                input_tokens: row.get::<_, i64>(7)? as u64,
                output_tokens: row.get::<_, i64>(8)? as u64,
                cache_creation_tokens: row.get::<_, Option<i64>>(9)?.map(|v| v as u64),
                cache_read_tokens: row.get::<_, Option<i64>>(10)?.map(|v| v as u64),
                request_id: row.get(11)?,
                endpoint: row.get(12)?,
                tool_calls: Vec::new(),
                reasoning_content: None,
            })
        })
        .expect("Failed to query")
        .filter_map(|r| r.ok())
        .collect()
    }
    
    /// Get records for last N hours
    pub fn by_last_hours(&self, hours: u64) -> Vec<TokenRecord> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0);
        
        let hours_ns = hours * 3600 * 1_000_000_000;
        let start_ns = now.saturating_sub(hours_ns);
        
        self.by_time_range_owned(start_ns, now)
    }
    
    /// Clear all records
    pub fn clear(&mut self) -> Result<(), rusqlite::Error> {
        self.conn.execute(&format!("DELETE FROM {}", self.table_name), [])?;
        Ok(())
    }
    
    /// Get record count
    pub fn count(&self) -> u64 {
        self.conn
            .query_row(&format!("SELECT COUNT(*) FROM {}", self.table_name), [], |row| row.get::<_, i64>(0))
            .unwrap_or(0) as u64
    }

    /// Purge records older than the given timestamp
    ///
    /// Returns the number of deleted rows.
    pub fn purge_before(&self, cutoff_ns: u64) -> anyhow::Result<u64> {
        let sql = format!(
            "DELETE FROM {} WHERE timestamp_ns < ?1",
            self.table_name
        );
        let deleted = self.conn.execute(&sql, params![cutoff_ns as i64])
            .map_err(|e| anyhow::anyhow!("Failed to purge token records: {}", e))?;
        Ok(deleted as u64)
    }

    /// Execute WAL checkpoint to flush WAL data back to the main database file
    pub fn checkpoint(&self) -> anyhow::Result<()> {
        wal_checkpoint(&self.conn).map_err(Into::into)
    }
}

/// Token query interface
pub struct TokenQuery<'a> {
    store: &'a TokenStore,
}

impl<'a> TokenQuery<'a> {
    /// Create a new query
    pub fn new(store: &'a TokenStore) -> Self {
        TokenQuery { store }
    }
    
    /// Query by time period
    pub fn by_period(&self, period: TimePeriod) -> TokenQueryResult {
        let (start_ns, end_ns) = period.time_range();
        let records = self.store.by_time_range(start_ns, end_ns);
        self.build_result(records, period.to_string())
    }
    
    /// Query last N hours
    pub fn by_hours(&self, hours: u64) -> TokenQueryResult {
        let records = self.store.by_last_hours(hours);
        self.build_result(records, format!("最近 {} 小时", hours))
    }
    
    /// Query with comparison
    pub fn by_period_with_compare(&self, period: TimePeriod) -> TokenQueryResult {
        let mut result = self.by_period(period);
        
        // Get previous period data
        let prev_period = period.previous_period();
        let prev_result = self.by_period(prev_period);
        
        if prev_result.total_tokens > 0 {
            let change = result.total_tokens as i64 - prev_result.total_tokens as i64;
            let change_percent = if prev_result.total_tokens > 0 {
                (change as f64 / prev_result.total_tokens as f64) * 100.0
            } else {
                0.0
            };
            
            result.comparison = Some(TokenComparison {
                previous_total: prev_result.total_tokens,
                change,
                change_percent,
                trend: if change > 0 {
                    Trend::Up
                } else if change < 0 {
                    Trend::Down
                } else {
                    Trend::Flat
                },
            });
        }
        
        result
    }
    
    /// Query with breakdown by agent
    pub fn by_period_with_breakdown(&self, period: TimePeriod) -> TokenQueryResult {
        let mut result = self.by_period(period);
        result.breakdown = self.compute_breakdown(period);
        result
    }
    
    /// Query with comparison and breakdown
    pub fn full_query(&self, period: TimePeriod) -> TokenQueryResult {
        let mut result = self.by_period_with_compare(period);
        result.breakdown = self.compute_breakdown(period);
        result
    }
    
    /// Query hours with comparison
    pub fn by_hours_with_compare(&self, hours: u64) -> TokenQueryResult {
        let mut result = self.by_hours(hours);
        
        // Get previous period data
        let prev_records = self.store.by_last_hours(hours * 2);
        let prev_records: Vec<_> = prev_records.into_iter().filter(|r| {
            // Get records from the earlier half
            let now = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0);
            let hours_ns = hours * 3600 * 1_000_000_000;
            let start_ns = now.saturating_sub(hours_ns * 2);
            let mid_ns = now.saturating_sub(hours_ns);
            r.timestamp_ns >= start_ns && r.timestamp_ns < mid_ns
        }).collect();
        
        let prev_total: u64 = prev_records.iter().map(|r| r.total_tokens()).sum();
        
        if prev_total > 0 {
            let change = result.total_tokens as i64 - prev_total as i64;
            let change_percent = if prev_total > 0 {
                (change as f64 / prev_total as f64) * 100.0
            } else {
                0.0
            };
            
            result.comparison = Some(TokenComparison {
                previous_total: prev_total,
                change,
                change_percent,
                trend: if change > 0 {
                    Trend::Up
                } else if change < 0 {
                    Trend::Down
                } else {
                    Trend::Flat
                },
            });
        }
        
        result
    }
    
    /// Build result from records
    fn build_result(&self, records: Vec<TokenRecord>, period: String) -> TokenQueryResult {
        let input_tokens: u64 = records.iter().map(|r| r.input_tokens).sum();
        let output_tokens: u64 = records.iter().map(|r| r.output_tokens).sum();
        let total_tokens = input_tokens + output_tokens;
        let request_count = records.len() as u64;
        
        TokenQueryResult {
            period,
            input_tokens,
            output_tokens,
            total_tokens,
            request_count,
            comparison: None,
            breakdown: Vec::new(),
        }
    }
    
    /// Compute breakdown by agent
    fn compute_breakdown(&self, period: TimePeriod) -> Vec<TokenBreakdown> {
        let (start_ns, end_ns) = period.time_range();
        let records = self.store.by_time_range(start_ns, end_ns);
        
        let total_tokens: u64 = records.iter().map(|r| r.total_tokens()).sum();
        
        // Group by agent name (or comm if no agent)
        let mut agent_totals: std::collections::HashMap<String, (u64, u64, u64, u64)> = 
            std::collections::HashMap::new();
        
        for record in records {
            let name = record.agent.as_ref()
                .unwrap_or(&record.comm)
                .clone();
            
            let entry = agent_totals.entry(name).or_insert((0, 0, 0, 0));
            entry.0 += record.total_tokens();
            entry.1 += record.input_tokens;
            entry.2 += record.output_tokens;
            entry.3 += 1;
        }
        
        // Convert to breakdown
        let mut breakdown: Vec<TokenBreakdown> = agent_totals
            .into_iter()
            .map(|(name, (total, input, output, count))| {
                let percentage = if total_tokens > 0 {
                    (total as f64 / total_tokens as f64) * 100.0
                } else {
                    0.0
                };
                
                TokenBreakdown {
                    name,
                    total_tokens: total,
                    input_tokens: input,
                    output_tokens: output,
                    request_count: count,
                    percentage,
                }
            })
            .collect();
        
        // Sort by total tokens descending
        breakdown.sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
        breakdown
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_time_period_range() {
        let (start, end) = TimePeriod::Today.time_range();
        assert!(start < end);
        assert!(end > 0);
    }
    
    #[test]
    fn test_format_tokens() {
        assert_eq!(format_tokens(500), "500");
        assert_eq!(format_tokens(1500), "1.5K");
        assert_eq!(format_tokens(1_500_000), "1.5M");
    }
    
    #[test]
    fn test_format_tokens_with_commas() {
        assert_eq!(format_tokens_with_commas(1000), "1,000");
        assert_eq!(format_tokens_with_commas(125000), "125,000");
    }
    
    #[test]
    fn test_token_store() {
        let mut store = TokenStore::new("/tmp/test_tokens.db");
        
        let record = TokenRecord::new(1234, "python".to_string(), "openai".to_string(), 100, 50);
        let id = store.add(record).unwrap();
        assert!(id > 0);
        
        let records = store.all();
        assert!(!records.is_empty());
        
        // Cleanup
        std::fs::remove_file("/tmp/test_tokens.db").ok();
    }
    
    #[test]
    fn test_token_query() {
        let mut store = TokenStore::new("/tmp/test_tokens_query.db");
        
        // Add some records
        store.add(TokenRecord::new(1234, "python".to_string(), "openai".to_string(), 100, 50)).unwrap();
        store.add(TokenRecord::new(1234, "python".to_string(), "anthropic".to_string(), 200, 100)).unwrap();
        
        let query = TokenQuery::new(&store);
        let result = query.by_period(TimePeriod::Today);
        
        assert!(result.total_tokens > 0);
        
        // Cleanup
        std::fs::remove_file("/tmp/test_tokens_query.db").ok();
    }
}
