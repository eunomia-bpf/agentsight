//! HTTP record storage
//!
//! Handles table creation, record insertion, and querying for HTTP request/response records.

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use std::path::Path;

use crate::analyzer::HttpRecord;
use super::connection::{create_connection, wal_checkpoint};

/// SQLite-based HTTP record store
pub struct HttpStore {
    conn: Connection,
    table_name: String,
}

impl HttpStore {
    /// Create a new HttpStore with default table name
    pub fn new(path: &Path) -> Result<Self> {
        Self::with_table(path, "http_records")
    }

    /// Create a new HttpStore with custom table name
    pub fn with_table(path: &Path, table_name: &str) -> Result<Self> {
        let conn = create_connection(path)?;
        let table_name = table_name.to_string();

        let create_table_sql = format!(
            "CREATE TABLE IF NOT EXISTS {} (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ns      INTEGER NOT NULL,
                pid               INTEGER NOT NULL,
                comm              TEXT NOT NULL,
                method            TEXT NOT NULL,
                path              TEXT NOT NULL,
                status_code       INTEGER NOT NULL DEFAULT 0,
                request_headers   TEXT,
                request_body      TEXT,
                response_headers  TEXT,
                response_body     TEXT,
                duration_ns       INTEGER NOT NULL DEFAULT 0,
                is_sse            INTEGER NOT NULL DEFAULT 0,
                sse_event_count   INTEGER NOT NULL DEFAULT 0
            );",
            table_name
        );
        let create_index_sql = format!(
            "CREATE INDEX IF NOT EXISTS idx_{}_ts ON {}(timestamp_ns);
             CREATE INDEX IF NOT EXISTS idx_{}_pid ON {}(pid);
             CREATE INDEX IF NOT EXISTS idx_{}_path ON {}(path);",
            table_name, table_name, table_name, table_name, table_name, table_name
        );
        conn.execute_batch(&format!("{}{}", create_table_sql, create_index_sql))?;

        Ok(HttpStore { conn, table_name })
    }

    /// Insert an HTTP record, returns the row ID
    pub fn insert(&self, record: &HttpRecord) -> Result<i64> {
        let sql = format!(
            "INSERT INTO {} (timestamp_ns, pid, comm, method, path, status_code,
             request_headers, request_body, response_headers, response_body,
             duration_ns, is_sse, sse_event_count)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
            self.table_name
        );
        self.conn.execute(
            &sql,
            params![
                record.timestamp_ns as i64,
                record.pid,
                record.comm,
                record.method,
                record.path,
                record.status_code,
                record.request_headers,
                record.request_body,
                record.response_headers,
                record.response_body,
                record.duration_ns as i64,
                record.is_sse as i32,
                record.sse_event_count as i64,
            ],
        )?;

        Ok(self.conn.last_insert_rowid())
    }

    /// Query HTTP records since a given timestamp
    pub fn query_since(&self, since_ns: u64) -> Result<Vec<HttpRecord>> {
        let sql = format!(
            "SELECT timestamp_ns, pid, comm, method, path, status_code,
                    request_headers, request_body, response_headers, response_body,
                    duration_ns, is_sse, sse_event_count
             FROM {} WHERE timestamp_ns >= ?1
             ORDER BY timestamp_ns ASC",
            self.table_name
        );

        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map(params![since_ns as i64], |row| {
            Ok(row_to_record(row))
        })?;

        let mut records = Vec::new();
        for row in rows {
            match row {
                Ok(Ok(record)) => records.push(record),
                Ok(Err(e)) => log::warn!("Failed to parse HTTP record: {}", e),
                Err(e) => log::warn!("Failed to read row: {}", e),
            }
        }

        Ok(records)
    }

    /// Query HTTP records by PID
    pub fn query_by_pid(&self, pid: u32) -> Result<Vec<HttpRecord>> {
        let sql = format!(
            "SELECT timestamp_ns, pid, comm, method, path, status_code,
                    request_headers, request_body, response_headers, response_body,
                    duration_ns, is_sse, sse_event_count
             FROM {} WHERE pid = ?1
             ORDER BY timestamp_ns ASC",
            self.table_name
        );

        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map(params![pid], |row| {
            Ok(row_to_record(row))
        })?;

        let mut records = Vec::new();
        for row in rows {
            match row {
                Ok(Ok(record)) => records.push(record),
                Ok(Err(e)) => log::warn!("Failed to parse HTTP record: {}", e),
                Err(e) => log::warn!("Failed to read row: {}", e),
            }
        }

        Ok(records)
    }

    /// Query HTTP records by path pattern
    pub fn query_by_path(&self, path_pattern: &str) -> Result<Vec<HttpRecord>> {
        let sql = format!(
            "SELECT timestamp_ns, pid, comm, method, path, status_code,
                    request_headers, request_body, response_headers, response_body,
                    duration_ns, is_sse, sse_event_count
             FROM {} WHERE path LIKE ?1
             ORDER BY timestamp_ns ASC",
            self.table_name
        );

        let mut stmt = self.conn.prepare(&sql)?;
        let rows = stmt.query_map(params![path_pattern], |row| {
            Ok(row_to_record(row))
        })?;

        let mut records = Vec::new();
        for row in rows {
            match row {
                Ok(Ok(record)) => records.push(record),
                Ok(Err(e)) => log::warn!("Failed to parse HTTP record: {}", e),
                Err(e) => log::warn!("Failed to read row: {}", e),
            }
        }

        Ok(records)
    }

    /// Get total count of HTTP records
    pub fn count(&self) -> Result<u64> {
        let sql = format!("SELECT COUNT(*) FROM {}", self.table_name);
        let count: u64 = self.conn.query_row(&sql, [], |row| row.get(0))?;
        Ok(count)
    }

    /// Purge records older than the given timestamp
    ///
    /// Returns the number of deleted rows.
    pub fn purge_before(&self, cutoff_ns: u64) -> Result<u64> {
        let sql = format!(
            "DELETE FROM {} WHERE timestamp_ns < ?1",
            self.table_name
        );
        let deleted = self.conn.execute(&sql, params![cutoff_ns as i64])?;
        Ok(deleted as u64)
    }

    /// Execute WAL checkpoint to flush WAL data back to the main database file
    pub fn checkpoint(&self) -> Result<()> {
        wal_checkpoint(&self.conn)
    }
}

/// Parse a database row into an HttpRecord
fn row_to_record(row: &rusqlite::Row) -> Result<HttpRecord> {
    let timestamp_ns: i64 = row.get(0).map_err(|e| anyhow::anyhow!("{}", e))?;
    let pid: u32 = row.get(1).map_err(|e| anyhow::anyhow!("{}", e))?;
    let comm: String = row.get(2).map_err(|e| anyhow::anyhow!("{}", e))?;
    let method: String = row.get(3).map_err(|e| anyhow::anyhow!("{}", e))?;
    let path: String = row.get(4).map_err(|e| anyhow::anyhow!("{}", e))?;
    let status_code: u16 = row.get(5).map_err(|e| anyhow::anyhow!("{}", e))?;
    let request_headers: String = row.get(6).map_err(|e| anyhow::anyhow!("{}", e))?;
    let request_body: Option<String> = row.get(7).map_err(|e| anyhow::anyhow!("{}", e))?;
    let response_headers: String = row.get(8).map_err(|e| anyhow::anyhow!("{}", e))?;
    let response_body: Option<String> = row.get(9).map_err(|e| anyhow::anyhow!("{}", e))?;
    let duration_ns: i64 = row.get(10).map_err(|e| anyhow::anyhow!("{}", e))?;
    let is_sse_int: i32 = row.get(11).map_err(|e| anyhow::anyhow!("{}", e))?;
    let sse_event_count: i64 = row.get(12).map_err(|e| anyhow::anyhow!("{}", e))?;

    Ok(HttpRecord {
        timestamp_ns: timestamp_ns as u64,
        pid,
        comm,
        method,
        path,
        status_code,
        request_headers,
        request_body,
        response_headers,
        response_body,
        duration_ns: duration_ns as u64,
        is_sse: is_sse_int != 0,
        sse_event_count: sse_event_count as usize,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;

    fn test_db_path(name: &str) -> PathBuf {
        PathBuf::from(format!("/tmp/test_agentsight_http_{}.db", name))
    }

    #[test]
    fn test_insert_and_query() {
        let path = test_db_path("insert_query");
        let _ = fs::remove_file(&path);

        let store = HttpStore::new(&path).unwrap();

        let record = HttpRecord {
            timestamp_ns: 1000000000,
            pid: 1234,
            comm: "python".to_string(),
            method: "POST".to_string(),
            path: "/v1/chat/completions".to_string(),
            status_code: 200,
            request_headers: r#"{"content-type":"application/json"}"#.to_string(),
            request_body: Some(r#"{"model":"gpt-4","messages":[]}"#.to_string()),
            response_headers: r#"{"content-type":"application/json"}"#.to_string(),
            response_body: Some(r#"{"choices":[]}"#.to_string()),
            duration_ns: 500000000,
            is_sse: false,
            sse_event_count: 0,
        };

        let id = store.insert(&record).unwrap();
        assert!(id > 0);

        let records = store.query_since(0).unwrap();
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].method, "POST");
        assert_eq!(records[0].path, "/v1/chat/completions");
        assert_eq!(records[0].status_code, 200);
        assert_eq!(records[0].pid, 1234);

        let count = store.count().unwrap();
        assert_eq!(count, 1);

        fs::remove_file(&path).ok();
    }

    #[test]
    fn test_query_by_pid() {
        let path = test_db_path("query_pid");
        let _ = fs::remove_file(&path);

        let store = HttpStore::new(&path).unwrap();

        let record = HttpRecord {
            timestamp_ns: 1000000000,
            pid: 5678,
            comm: "node".to_string(),
            method: "POST".to_string(),
            path: "/v1/messages".to_string(),
            status_code: 200,
            request_headers: "{}".to_string(),
            request_body: None,
            response_headers: "{}".to_string(),
            response_body: None,
            duration_ns: 0,
            is_sse: true,
            sse_event_count: 10,
        };

        store.insert(&record).unwrap();

        let records = store.query_by_pid(5678).unwrap();
        assert_eq!(records.len(), 1);
        assert!(records[0].is_sse);
        assert_eq!(records[0].sse_event_count, 10);

        let empty = store.query_by_pid(9999).unwrap();
        assert!(empty.is_empty());

        fs::remove_file(&path).ok();
    }

    #[test]
    fn test_query_by_path() {
        let path = test_db_path("query_path");
        let _ = fs::remove_file(&path);

        let store = HttpStore::new(&path).unwrap();

        for p in &["/v1/chat/completions", "/v1/messages", "/v1/embeddings"] {
            let record = HttpRecord {
                timestamp_ns: 1000000000,
                pid: 1000,
                comm: "test".to_string(),
                method: "POST".to_string(),
                path: p.to_string(),
                status_code: 200,
                request_headers: "{}".to_string(),
                request_body: None,
                response_headers: "{}".to_string(),
                response_body: None,
                duration_ns: 0,
                is_sse: false,
                sse_event_count: 0,
            };
            store.insert(&record).unwrap();
        }

        let chat_records = store.query_by_path("%chat%").unwrap();
        assert_eq!(chat_records.len(), 1);

        let v1_records = store.query_by_path("/v1/%").unwrap();
        assert_eq!(v1_records.len(), 3);

        fs::remove_file(&path).ok();
    }
}
