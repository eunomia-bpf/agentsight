//! Shared health state for agent health check results
//!
//! This module provides the `HealthStore` type that holds the latest health
//! status of all discovered agent processes, shared between the background
//! health checker thread and the API handler via `Arc<RwLock<...>>`.

use std::collections::{HashMap, HashSet};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::Serialize;

/// Health state of an agent process
#[derive(Debug, Clone, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum AgentHealthState {
    /// HTTP probe returned a response (any status code)
    Healthy,
    /// HTTP probe failed (connection refused, etc.) — port unreachable
    Unhealthy,
    /// HTTP probe connected but timed out waiting for a response — process is hung
    Hung,
    /// Not yet checked
    Unknown,
    /// Process is alive but has no listening TCP port
    NoPort,
    /// Process has exited — kept for user acknowledgement
    Offline,
}

/// Health status of a single agent process
#[derive(Debug, Clone, Serialize)]
pub struct AgentHealthStatus {
    pub pid: u32,
    pub agent_name: String,
    pub category: String,
    pub exe_path: String,
    /// Detected listening TCP ports
    pub ports: Vec<u16>,
    pub status: AgentHealthState,
    /// Unix timestamp in milliseconds of the last check
    pub last_check_time: u64,
    /// HTTP response latency in milliseconds (if healthy)
    pub latency_ms: Option<u64>,
    /// Error description (if unhealthy)
    pub error_message: Option<String>,
    /// 用于重启的完整命令行（exe + args），None 表示不支持重启
    #[serde(skip_serializing_if = "Option::is_none")]
    pub restart_cmd: Option<Vec<String>>,
}

/// Stores the latest health check results for all tracked agents
pub struct HealthStore {
    agents: HashMap<u32, AgentHealthStatus>,
    /// Unix timestamp in milliseconds of the last full scan
    pub last_scan_time: u64,
}

impl HealthStore {
    pub fn new() -> Self {
        Self {
            agents: HashMap::new(),
            last_scan_time: 0,
        }
    }

    /// Update or insert the health status for a given PID
    pub fn update(&mut self, pid: u32, status: AgentHealthStatus) {
        self.agents.insert(pid, status);
    }

    /// Mark stale PIDs as Offline instead of removing them outright.
    /// Already-offline entries are left untouched (preserve offline_since time).
    pub fn mark_stale_offline(&mut self, active_pids: &HashSet<u32>) -> Vec<AgentHealthStatus> {
        let mut newly_offline = Vec::new();
        for (pid, entry) in self.agents.iter_mut() {
            if !active_pids.contains(pid) && entry.status != AgentHealthState::Offline {
                entry.status = AgentHealthState::Offline;
                entry.last_check_time = now_ms();
                entry.latency_ms = None;
                entry.error_message = Some("进程已退出".to_string());
                newly_offline.push(entry.clone());
            }
        }
        newly_offline
    }

    /// Remove a specific PID (user-acknowledged deletion)
    pub fn remove_by_pid(&mut self, pid: u32) -> bool {
        self.agents.remove(&pid).is_some()
    }

    /// Return a snapshot of all agent health statuses
    pub fn all_agents(&self) -> Vec<AgentHealthStatus> {
        self.agents.values().cloned().collect()
    }
}

/// Current time in Unix milliseconds
pub fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis() as u64
}
