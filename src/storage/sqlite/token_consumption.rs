//! Token consumption breakdown storage and querying
//!
//! Stores `TokenConsumptionBreakdown` records in SQLite.
//! Fields `per_message` and `output_per_block` are intentionally excluded.

use std::collections::HashMap;
use std::path::PathBuf;

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

use crate::analyzer::TokenConsumptionBreakdown;
use super::connection::{create_connection, default_base_path, wal_checkpoint};

/// A row stored in the token_consumption table (excludes per_message and output_per_block)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenConsumptionRecord {
    /// Row id (set after retrieval)
    pub id: Option<i64>,
    /// Timestamp in nanoseconds since Unix epoch
    pub timestamp_ns: u64,
    /// Process ID
    pub pid: u32,
    /// Process command name
    pub comm: String,
    /// LLM provider (e.g., "openai", "anthropic")
    pub provider: String,
    /// Model name
    pub model: String,
    /// Total input tokens
    pub total_input_tokens: usize,
    /// Total output tokens
    pub total_output_tokens: usize,
    /// Tool definitions token count
    pub tools_tokens: usize,
    /// System prompt token count
    pub system_prompt_tokens: usize,
    /// Token count by role, stored as JSON (e.g. {"user":100,"assistant":50})
    pub by_role_json: String,
    /// Output token count by content type, stored as JSON
    pub output_by_type_json: String,
}

impl TokenConsumptionRecord {
    /// Total tokens (input + output)
    pub fn total_tokens(&self) -> usize {
        self.total_input_tokens + self.total_output_tokens
    }

    /// Deserialise `by_role_json` into a HashMap
    pub fn by_role(&self) -> HashMap<String, usize> {
        serde_json::from_str(&self.by_role_json).unwrap_or_default()
    }

    /// Deserialise `output_by_type_json` into a HashMap
    pub fn output_by_type(&self) -> HashMap<String, usize> {
        serde_json::from_str(&self.output_by_type_json).unwrap_or_default()
    }
}

/// Query filter for token consumption records
#[derive(Debug, Clone, Default)]
pub struct TokenConsumptionFilter {
    /// Optional start timestamp (ns)
    pub start_ns: Option<u64>,
    /// Optional end timestamp (ns)
    pub end_ns: Option<u64>,
    /// Optional provider filter
    pub provider: Option<String>,
    /// Optional model filter
    pub model: Option<String>,
    /// Max number of rows to return (0 = no limit)
    pub limit: usize,
}

/// Aggregated query result for token consumption
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenConsumptionQueryResult {
    /// Human-readable period label
    pub period: String,
    /// Number of records
    pub record_count: u64,
    /// Total input tokens
    pub total_input_tokens: u64,
    /// Total output tokens
    pub total_output_tokens: u64,
    /// Total tokens
    pub total_tokens: u64,
    /// Aggregated by-role totals
    pub by_role: HashMap<String, u64>,
    /// Aggregated output-by-type totals
    pub output_by_type: HashMap<String, u64>,
    /// Total tools tokens
    pub tools_tokens: u64,
    /// Total system prompt tokens
    pub system_prompt_tokens: u64,
    /// Individual records (only populated when `include_records` is true)
    pub records: Vec<TokenConsumptionRecord>,
}

/// SQLite-backed store for `TokenConsumptionBreakdown`
pub struct TokenConsumptionStore {
    conn: Connection,
    table_name: String,
}

impl TokenConsumptionStore {
    /// Create store with default table name
    pub fn new(path: impl Into<PathBuf>) -> anyhow::Result<Self> {
        Self::with_table(path, "token_consumption")
    }

    /// Create store with custom table name
    pub fn with_table(path: impl Into<PathBuf>, table_name: &str) -> anyhow::Result<Self> {
        let path = path.into();
        let conn = create_connection(&path)?;
        let table_name = table_name.to_string();

        conn.execute_batch(&format!(
            "CREATE TABLE IF NOT EXISTS {table} (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ns         INTEGER NOT NULL,
                pid                  INTEGER NOT NULL DEFAULT 0,
                comm                 TEXT    NOT NULL DEFAULT '',
                provider             TEXT    NOT NULL,
                model                TEXT    NOT NULL,
                total_input_tokens   INTEGER NOT NULL,
                total_output_tokens  INTEGER NOT NULL,
                tools_tokens         INTEGER NOT NULL DEFAULT 0,
                system_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                by_role_json         TEXT    NOT NULL DEFAULT '{{}}',
                output_by_type_json  TEXT    NOT NULL DEFAULT '{{}}'
            );
            CREATE INDEX IF NOT EXISTS idx_{table}_ts   ON {table}(timestamp_ns);
            CREATE INDEX IF NOT EXISTS idx_{table}_prov ON {table}(provider);
            CREATE INDEX IF NOT EXISTS idx_{table}_model ON {table}(model);",
            table = table_name,
        ))?;

        Ok(TokenConsumptionStore { conn, table_name })
    }

    /// Default storage path
    pub fn default_path() -> PathBuf {
        default_base_path().join("agentsight.db")
    }

    /// Insert a `TokenConsumptionBreakdown` record.
    ///
    /// Callers should supply `timestamp_ns`, `pid`, and `comm` from the
    /// surrounding HTTP context; they are not part of the breakdown itself.
    pub fn insert(
        &self,
        breakdown: &TokenConsumptionBreakdown,
        timestamp_ns: u64,
        pid: u32,
        comm: &str,
    ) -> anyhow::Result<i64> {
        let by_role_json = serde_json::to_string(&breakdown.by_role)
            .unwrap_or_else(|_| "{}".to_string());
        let output_by_type_json = serde_json::to_string(&breakdown.output_by_type)
            .unwrap_or_else(|_| "{}".to_string());

        let sql = format!(
            "INSERT INTO {} (
                timestamp_ns, pid, comm, provider, model,
                total_input_tokens, total_output_tokens,
                tools_tokens, system_prompt_tokens,
                by_role_json, output_by_type_json
             ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)",
            self.table_name
        );

        self.conn.execute(
            &sql,
            params![
                timestamp_ns as i64,
                pid as i64,
                comm,
                breakdown.provider,
                breakdown.model,
                breakdown.total_input_tokens as i64,
                breakdown.total_output_tokens as i64,
                breakdown.tools_tokens as i64,
                breakdown.system_prompt_tokens as i64,
                by_role_json,
                output_by_type_json,
            ],
        )
        .map_err(|e| anyhow::anyhow!("Failed to insert token_consumption record: {}", e))?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Query records with the given filter.
    ///
    /// Returns individual rows sorted by timestamp descending.
    pub fn query(&self, filter: &TokenConsumptionFilter) -> anyhow::Result<Vec<TokenConsumptionRecord>> {
        let mut conditions: Vec<String> = Vec::new();
        let mut bind_idx = 1usize;

        if filter.start_ns.is_some() {
            conditions.push(format!("timestamp_ns >= ?{}", bind_idx));
            bind_idx += 1;
        }
        if filter.end_ns.is_some() {
            conditions.push(format!("timestamp_ns <= ?{}", bind_idx));
            bind_idx += 1;
        }
        if filter.provider.is_some() {
            conditions.push(format!("provider = ?{}", bind_idx));
            bind_idx += 1;
        }
        if filter.model.is_some() {
            conditions.push(format!("model = ?{}", bind_idx));
            bind_idx += 1;
        }

        let where_clause = if conditions.is_empty() {
            String::new()
        } else {
            format!("WHERE {}", conditions.join(" AND "))
        };

        let limit_clause = if filter.limit > 0 {
            format!("LIMIT {}", filter.limit)
        } else {
            String::new()
        };

        let sql = format!(
            "SELECT id, timestamp_ns, pid, comm, provider, model,
                    total_input_tokens, total_output_tokens,
                    tools_tokens, system_prompt_tokens,
                    by_role_json, output_by_type_json
             FROM {} {} ORDER BY timestamp_ns DESC {}",
            self.table_name, where_clause, limit_clause
        );

        let mut stmt = self.conn.prepare(&sql)?;

        // Bind parameters positionally
        let mut param_values: Vec<rusqlite::types::Value> = Vec::new();
        if let Some(v) = filter.start_ns {
            param_values.push(rusqlite::types::Value::Integer(v as i64));
        }
        if let Some(v) = filter.end_ns {
            param_values.push(rusqlite::types::Value::Integer(v as i64));
        }
        if let Some(ref v) = filter.provider {
            param_values.push(rusqlite::types::Value::Text(v.clone()));
        }
        if let Some(ref v) = filter.model {
            param_values.push(rusqlite::types::Value::Text(v.clone()));
        }

        let params_ref: Vec<&dyn rusqlite::ToSql> = param_values
            .iter()
            .map(|v| v as &dyn rusqlite::ToSql)
            .collect();

        let records = stmt
            .query_map(params_ref.as_slice(), |row| {
                Ok(TokenConsumptionRecord {
                    id: Some(row.get::<_, i64>(0)?),
                    timestamp_ns: row.get::<_, i64>(1)? as u64,
                    pid: row.get::<_, i64>(2)? as u32,
                    comm: row.get(3)?,
                    provider: row.get(4)?,
                    model: row.get(5)?,
                    total_input_tokens: row.get::<_, i64>(6)? as usize,
                    total_output_tokens: row.get::<_, i64>(7)? as usize,
                    tools_tokens: row.get::<_, i64>(8)? as usize,
                    system_prompt_tokens: row.get::<_, i64>(9)? as usize,
                    by_role_json: row.get(10)?,
                    output_by_type_json: row.get(11)?,
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(records)
    }

    /// Aggregate records with the given filter into a summary result.
    pub fn aggregate(
        &self,
        filter: &TokenConsumptionFilter,
        period_label: impl Into<String>,
        include_records: bool,
    ) -> anyhow::Result<TokenConsumptionQueryResult> {
        let records = self.query(filter)?;

        let record_count = records.len() as u64;
        let total_input_tokens: u64 = records.iter().map(|r| r.total_input_tokens as u64).sum();
        let total_output_tokens: u64 = records.iter().map(|r| r.total_output_tokens as u64).sum();
        let total_tokens = total_input_tokens + total_output_tokens;
        let tools_tokens: u64 = records.iter().map(|r| r.tools_tokens as u64).sum();
        let system_prompt_tokens: u64 = records.iter().map(|r| r.system_prompt_tokens as u64).sum();

        // Aggregate by_role and output_by_type across all records
        let mut by_role: HashMap<String, u64> = HashMap::new();
        let mut output_by_type: HashMap<String, u64> = HashMap::new();

        for rec in &records {
            for (role, cnt) in rec.by_role() {
                *by_role.entry(role).or_insert(0) += cnt as u64;
            }
            for (typ, cnt) in rec.output_by_type() {
                *output_by_type.entry(typ).or_insert(0) += cnt as u64;
            }
        }

        let rows = if include_records { records } else { Vec::new() };

        Ok(TokenConsumptionQueryResult {
            period: period_label.into(),
            record_count,
            total_input_tokens,
            total_output_tokens,
            total_tokens,
            by_role,
            output_by_type,
            tools_tokens,
            system_prompt_tokens,
            records: rows,
        })
    }

    /// Query records in a time range
    pub fn by_time_range(&self, start_ns: u64, end_ns: u64) -> anyhow::Result<Vec<TokenConsumptionRecord>> {
        self.query(&TokenConsumptionFilter {
            start_ns: Some(start_ns),
            end_ns: Some(end_ns),
            ..Default::default()
        })
    }

    /// Purge records older than the given timestamp
    pub fn purge_before(&self, cutoff_ns: u64) -> anyhow::Result<u64> {
        let deleted = self.conn.execute(
            &format!("DELETE FROM {} WHERE timestamp_ns < ?1", self.table_name),
            params![cutoff_ns as i64],
        )?;
        Ok(deleted as u64)
    }

    /// Execute WAL checkpoint to flush WAL data back to the main database file
    pub fn checkpoint(&self) -> anyhow::Result<()> {
        wal_checkpoint(&self.conn).map_err(Into::into)
    }

    /// Number of stored records
    pub fn count(&self) -> u64 {
        self.conn
            .query_row(
                &format!("SELECT COUNT(*) FROM {}", self.table_name),
                [],
                |row| row.get::<_, i64>(0),
            )
            .unwrap_or(0) as u64
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn make_breakdown(provider: &str, model: &str) -> TokenConsumptionBreakdown {
        let mut by_role = HashMap::new();
        by_role.insert("user".to_string(), 100usize);
        by_role.insert("assistant".to_string(), 50usize);

        let mut output_by_type = HashMap::new();
        output_by_type.insert("text".to_string(), 80usize);

        TokenConsumptionBreakdown {
            timestamp_ns: 1_000_000_000,
            pid: 123,
            comm: "python".to_string(),
            provider: provider.to_string(),
            model: model.to_string(),
            total_input_tokens: 150,
            total_output_tokens: 80,
            by_role,
            per_message: vec![],
            tools_tokens: 20,
            system_prompt_tokens: 10,
            output_by_type,
            output_per_block: vec![],
        }
    }

    #[test]
    fn test_insert_and_query() {
        let path = "/tmp/test_token_consumption.db";
        let store = TokenConsumptionStore::new(path).unwrap();

        let bd = make_breakdown("openai", "gpt-4o");
        let id = store.insert(&bd, 1_000_000_000, 123, "python").unwrap();
        assert!(id > 0);

        let records = store.query(&TokenConsumptionFilter::default()).unwrap();
        assert!(!records.is_empty());
        let rec = &records[0];
        assert_eq!(rec.provider, "openai");
        assert_eq!(rec.model, "gpt-4o");
        assert_eq!(rec.total_input_tokens, 150);
        assert_eq!(rec.total_output_tokens, 80);
        assert_eq!(rec.by_role().get("user"), Some(&100));

        std::fs::remove_file(path).ok();
    }

    #[test]
    fn test_aggregate() {
        let path = "/tmp/test_token_consumption_agg.db";
        let store = TokenConsumptionStore::new(path).unwrap();

        let bd = make_breakdown("anthropic", "claude-3-5-sonnet");
        store.insert(&bd, 2_000_000_000, 1, "claude").unwrap();
        store.insert(&bd, 3_000_000_000, 1, "claude").unwrap();

        let result = store
            .aggregate(&TokenConsumptionFilter::default(), "测试", false)
            .unwrap();
        assert_eq!(result.record_count, 2);
        assert_eq!(result.total_input_tokens, 300);
        assert_eq!(result.by_role.get("user"), Some(&200));

        std::fs::remove_file(path).ok();
    }
}
