//! Background health check loop
//!
//! Periodically scans for agent processes, detects their listening ports,
//! and probes them via HTTP to determine health status.

use std::collections::HashSet;
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::{Duration, Instant};

use crate::discovery::AgentScanner;
use super::port_detector::detect_listening_ports;
use super::store::{AgentHealthState, AgentHealthStatus, HealthStore, now_ms};

/// Background health checker that periodically probes discovered agents
pub struct HealthChecker {
    store: Arc<RwLock<HealthStore>>,
    interval: Duration,
    http_timeout: Duration,
}

impl HealthChecker {
    /// Create a new HealthChecker.
    ///
    /// # Arguments
    /// * `store` - Shared health store for writing results
    /// * `interval` - Time between health check cycles
    pub fn new(store: Arc<RwLock<HealthStore>>, interval: Duration) -> Self {
        Self {
            store,
            interval,
            http_timeout: Duration::from_secs(5),
        }
    }

    /// Spawn the health check loop on a background thread.
    ///
    /// Returns the `JoinHandle` — the thread runs until the process exits.
    pub fn start(self) -> thread::JoinHandle<()> {
        thread::spawn(move || self.run())
    }

    /// Main health check loop (blocking).
    fn run(self) {
        log::info!(
            "Health checker started: interval={}s, http_timeout={}s",
            self.interval.as_secs(),
            self.http_timeout.as_secs(),
        );

        // Do an initial check immediately, then loop with interval
        loop {
            self.check_once();
            thread::sleep(self.interval);
        }
    }

    /// Perform a single health check cycle for all discovered agents.
    fn check_once(&self) {
        let mut scanner = AgentScanner::new();
        let agents = scanner.scan();

        let active_pids: HashSet<u32> = agents.iter().map(|a| a.pid).collect();

        // Mark gone processes as Offline (instead of deleting immediately)
        if let Ok(mut store) = self.store.write() {
            store.mark_stale_offline(&active_pids);
            store.last_scan_time = now_ms();
        }

        log::debug!("Health check: found {} agent(s)", agents.len());

        for agent in &agents {
            let ports = detect_listening_ports(agent.pid);
            // 构造重启命令：exe + 原始 cmdline args
            let restart_cmd = build_restart_cmd(&agent.exe_path, &agent.cmdline_args);
            let status = if ports.is_empty() {
                AgentHealthStatus {
                    pid: agent.pid,
                    agent_name: agent.agent_info.name.clone(),
                    category: agent.agent_info.category.clone(),
                    exe_path: agent.exe_path.clone(),
                    ports: vec![],
                    status: AgentHealthState::NoPort,
                    last_check_time: now_ms(),
                    latency_ms: None,
                    error_message: None,
                    restart_cmd: Some(restart_cmd),
                }
            } else {
                self.probe_agent(agent, &ports, restart_cmd)
            };

            if let Ok(mut store) = self.store.write() {
                store.update(agent.pid, status);
            }
        }
    }

    /// Probe an agent's ports via HTTP and return its health status.
    ///
    /// Tries each port in order.
    /// - 2xx/3xx/4xx/5xx response         → Healthy
    /// - Read timeout (process is hung)   → Hung
    /// - Connection refused / unreachable → Unhealthy
    fn probe_agent(
        &self,
        agent: &crate::discovery::DiscoveredAgent,
        ports: &[u16],
        restart_cmd: Vec<String>,
    ) -> AgentHealthStatus {
        let mut last_error = String::new();
        // 标记是否遇到了超时错误（区分 hung vs unreachable）
        let mut timed_out = false;

        for &port in ports {
            let url = format!("http://127.0.0.1:{}/", port);
            let start = Instant::now();

            let result = ureq::AgentBuilder::new()
                .timeout_connect(self.http_timeout)
                .timeout_read(self.http_timeout)
                .build()
                .get(&url)
                .call();

            let latency = start.elapsed().as_millis() as u64;

            match result {
                Ok(_) => {
                    return AgentHealthStatus {
                        pid: agent.pid,
                        agent_name: agent.agent_info.name.clone(),
                        category: agent.agent_info.category.clone(),
                        exe_path: agent.exe_path.clone(),
                        ports: ports.to_vec(),
                        status: AgentHealthState::Healthy,
                        last_check_time: now_ms(),
                        latency_ms: Some(latency),
                        error_message: None,
                        restart_cmd: Some(restart_cmd),
                    };
                }
                Err(ureq::Error::Status(_code, _resp)) => {
                    // 非 2xx 响应 — 进程仍在响应
                    return AgentHealthStatus {
                        pid: agent.pid,
                        agent_name: agent.agent_info.name.clone(),
                        category: agent.agent_info.category.clone(),
                        exe_path: agent.exe_path.clone(),
                        ports: ports.to_vec(),
                        status: AgentHealthState::Healthy,
                        last_check_time: now_ms(),
                        latency_ms: Some(latency),
                        error_message: None,
                        restart_cmd: Some(restart_cmd),
                    };
                }
                Err(ureq::Error::Transport(e)) => {
                    let msg = e.to_string();
                    // ureq 的读超时 / 写超时消息均包含 "timed out"
                    if msg.to_lowercase().contains("timed out") {
                        timed_out = true;
                        last_error = format!("响应超时 ({}ms): {}", latency, msg);
                    } else {
                        last_error = msg.clone();
                    }
                    log::debug!(
                        "Health probe failed for {} (pid={}) on port {}: {}",
                        agent.agent_info.name, agent.pid, port, msg
                    );
                }
            }
        }

        // 所有端口均失败 — 根据错误类型决定状态
        let status = if timed_out {
            AgentHealthState::Hung
        } else {
            AgentHealthState::Unhealthy
        };

        AgentHealthStatus {
            pid: agent.pid,
            agent_name: agent.agent_info.name.clone(),
            category: agent.agent_info.category.clone(),
            exe_path: agent.exe_path.clone(),
            ports: ports.to_vec(),
            status,
            last_check_time: now_ms(),
            latency_ms: None,
            error_message: Some(last_error),
            restart_cmd: Some(restart_cmd),
        }
    }
}

/// 构造重启命令向量：[exe, arg1, arg2, ...]
///
/// 过滤掉空字符串，保证命令有效。
fn build_restart_cmd(exe_path: &str, cmdline_args: &[String]) -> Vec<String> {
    let mut cmd = vec![exe_path.to_string()];
    // cmdline_args[0] 通常是 exe 本身（argv[0]），跳过以避免重复
    let args: Vec<_> = cmdline_args.iter()
        .skip(1)
        .filter(|a| !a.is_empty())
        .cloned()
        .collect();
    cmd.extend(args);
    cmd
}
