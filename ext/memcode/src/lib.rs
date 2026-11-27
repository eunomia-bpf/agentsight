// SPDX-License-Identifier: MIT
//! External correlation recipe. No capture hook, payload ingestion, or OTEL exporter.

use std::collections::{BTreeSet, HashMap};
use std::path::PathBuf;
use std::time::Duration;

use agent_session::{
    AgentSession, LiveProcessCandidate, ProcessKey, SessionCache, SessionProcessInput,
    SessionProcessMatcher,
};
use rusqlite::{Connection, params};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Operation {
    Save,
    Recall,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Ok,
    Error,
    Timeout,
    Cancelled,
}

/// The MemCode emitter must generate request_id randomly, independently of content.
/// starttime_ticks anchors PID reuse to the same live process instance.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MemoryEvent {
    pub operation: Operation,
    pub duration_ms: u64,
    pub status: Status,
    pub request_id: String,
    pub pid: u32,
    pub starttime_ticks: u64,
}

impl MemoryEvent {
    pub fn parse(line: &str) -> Result<Self, &'static str> {
        if line.len() > 4096 {
            return Err("event exceeds 4 KiB");
        }
        let event: Self = serde_json::from_str(line).map_err(|_| "invalid content-free event")?;
        if event.request_id.len() != 32
            || !event.request_id.bytes().all(|b| b.is_ascii_hexdigit())
            || event.pid == 0
            || event.starttime_ticks == 0
            || event.duration_ms > 3_600_000
        {
            return Err("invalid event metadata");
        }
        Ok(event)
    }
}

/// Only this projection reaches sinks. No transcript, path, cwd, identity or payload fields.
#[derive(Debug, Clone, Serialize)]
pub struct CorrelatedEvent {
    pub operation: Operation,
    pub duration_ms: u64,
    pub status: Status,
    pub request_id: String,
    pub session_key: String,
    pub root_pid: u32,
}

pub fn discover_and_correlate(
    cache: &mut SessionCache,
    matcher: &mut SessionProcessMatcher,
    events: &[MemoryEvent],
    processes: &[LiveProcessCandidate],
    fd_paths: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
    observed_paths: &HashMap<ProcessKey, PathBuf>,
    now_ms: u64,
) -> Vec<CorrelatedEvent> {
    let sessions = cache.discover_cached(25, Duration::from_secs(2));
    correlate(
        matcher,
        events,
        &sessions,
        processes,
        fd_paths,
        observed_paths,
        now_ms,
    )
}

pub fn correlate(
    matcher: &mut SessionProcessMatcher,
    events: &[MemoryEvent],
    sessions: &[AgentSession],
    processes: &[LiveProcessCandidate],
    fd_paths: &HashMap<ProcessKey, BTreeSet<PathBuf>>,
    observed_paths: &HashMap<ProcessKey, PathBuf>,
    now_ms: u64,
) -> Vec<CorrelatedEvent> {
    let inputs: Vec<_> = sessions
        .iter()
        .map(|s| SessionProcessInput {
            id: s.session_id.clone(),
            agent: s.agent_type.clone(),
            path: s.path.clone(),
            start_timestamp_ms: s.start_timestamp_ms,
            end_timestamp_ms: s.end_timestamp_ms,
            cwd: s.cwd.clone(),
        })
        .collect();
    let matches = matcher.match_sessions(&inputs, processes, fd_paths, observed_paths, now_ms);
    events
        .iter()
        .filter_map(|event| {
            // Validate even if an embedding application constructs the struct directly.
            if event.request_id.len() != 32
                || !event.request_id.bytes().all(|b| b.is_ascii_hexdigit())
                || event.duration_ms > 3_600_000
                || event.pid == 0
                || event.starttime_ticks == 0
            {
                return None;
            }
            let key = ProcessKey {
                pid: event.pid,
                starttime_ticks: event.starttime_ticks,
            };
            let process = processes
                .iter()
                .find(|p| p.tree.root == key || p.tree.members.contains(&key))?;
            let matched = matches.session_for_pid(event.pid)?;
            if matched.root_pid != process.tree.root.pid
                || matched.pid_starttime_ticks != process.tree.root.starttime_ticks
            {
                return None;
            }
            Some(CorrelatedEvent {
                operation: event.operation.clone(),
                duration_ms: event.duration_ms,
                status: event.status.clone(),
                request_id: event.request_id.clone(),
                session_key: hex::encode(Sha256::digest(matched.session_id.as_bytes())),
                root_pid: matched.root_pid,
            })
        })
        .collect()
}

/// Sample side table for joining opaque IDs alongside an ext/analysis SQLite sink.
pub fn write_sqlite(
    connection: &mut Connection,
    events: &[CorrelatedEvent],
) -> rusqlite::Result<()> {
    connection.execute_batch(
        "CREATE TABLE IF NOT EXISTS memcode_operations (
        request_id TEXT PRIMARY KEY, operation TEXT NOT NULL, duration_ms INTEGER NOT NULL,
        status TEXT NOT NULL, session_key TEXT NOT NULL, root_pid INTEGER NOT NULL);",
    )?;
    let tx = connection.transaction()?;
    for event in events {
        tx.execute(
            "INSERT OR IGNORE INTO memcode_operations VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                event.request_id,
                enum_string(&event.operation),
                event.duration_ms,
                enum_string(&event.status),
                event.session_key,
                event.root_pid
            ],
        )?;
    }
    tx.commit()
}

/// Attribute projection for an application's existing ext/analysis OTEL sink.
/// This crate intentionally does not own an OTEL exporter or change agent-session.
pub fn otel_attributes(event: &CorrelatedEvent) -> serde_json::Value {
    serde_json::json!({
        "memcode.operation": enum_string(&event.operation),
        "memcode.duration_ms": event.duration_ms,
        "memcode.status": enum_string(&event.status),
        "memcode.request_id": event.request_id,
        "agent.session_key": event.session_key,
        "process.pid": event.root_pid,
    })
}

fn enum_string(value: &impl Serialize) -> String {
    serde_json::to_value(value)
        .expect("enum serializes")
        .as_str()
        .expect("string enum")
        .to_owned()
}
