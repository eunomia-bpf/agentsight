//! Agent process scanner
//!
//! This module provides functionality to scan the system for running AI agent processes
//! by examining /proc filesystem entries and handling process lifecycle events.

use std::collections::HashMap;
use std::fs;
use std::path::Path;

use super::agent::{AgentInfo, DiscoveredAgent};
use super::matcher::{AgentMatcher, ProcessContext};
use super::registry::known_agents;

/// Scanner for discovering AI agent processes on the system
///
/// The scanner maintains a list of agent matchers and can scan the /proc filesystem
/// to find running processes that match these agents. It also handles process
/// lifecycle events (creation/exit) for dynamic tracking.
pub struct AgentScanner {
    matchers: Vec<Box<dyn AgentMatcher>>,
    /// Currently tracked agent processes: pid -> DiscoveredAgent
    tracked_agents: HashMap<u32, DiscoveredAgent>,
}

impl Default for AgentScanner {
    fn default() -> Self {
        Self::new()
    }
}

impl AgentScanner {
    /// Create a scanner with the built-in list of known agents
    pub fn new() -> Self {
        Self {
            matchers: known_agents(),
            tracked_agents: HashMap::new(),
        }
    }

    /// Create a scanner with a custom list of agent matchers
    pub fn with_matchers(matchers: Vec<Box<dyn AgentMatcher>>) -> Self {
        Self {
            matchers,
            tracked_agents: HashMap::new(),
        }
    }

    /// Scan the system for running AI agent processes
    ///
    /// This method iterates over /proc/[pid]/ directories and attempts to match
    /// each process against the known agent list based on process name.
    /// Discovered agents are automatically added to `tracked_agents`.
    ///
    /// # Returns
    ///
    /// A vector of `DiscoveredAgent` instances representing the found agent processes.
    pub fn scan(&mut self) -> Vec<DiscoveredAgent> {
        let mut discovered = Vec::new();

        // Read /proc directory
        let proc_path = Path::new("/proc");
        let entries = match fs::read_dir(proc_path) {
            Ok(e) => e,
            Err(_) => return discovered,
        };

        for entry in entries.flatten() {
            let file_name = entry.file_name();
            let name_str = file_name.to_string_lossy();

            // Only process numeric directory names (PIDs)
            let pid: u32 = match name_str.parse() {
                Ok(p) => p,
                Err(_) => continue,
            };

            // Try to read process info and match against known agents
            if let Some(discovered_agent) = self.try_match_process(pid) {
                self.tracked_agents.insert(discovered_agent.pid, discovered_agent.clone());
                discovered.push(discovered_agent);
            }
        }

        discovered
    }

    /// Handle process creation event
    ///
    /// Check if the new process matches a known agent and start tracking it.
    ///
    /// # Arguments
    /// * `pid` - Process ID
    /// * `comm` - Process command name (from BPF event, already updated at sys_exit_execve)
    ///
    /// # Returns
    ///
    /// `Some(DiscoveredAgent)` if the process is a known agent, `None` otherwise.
    pub fn on_process_create(&mut self, pid: u32, bpf_comm: &str) -> Option<&DiscoveredAgent> {
        // Use BPF comm as primary source (already updated at sys_exit_execve time).
        // Fallback to /proc/[pid]/comm only if BPF comm is empty or too short.
        let comm = if bpf_comm.len() >= 3 {
            bpf_comm.to_string()
        } else {
            // Fallback: read from /proc/[pid]/comm
            let comm_path = format!("/proc/{}/comm", pid);
            fs::read_to_string(&comm_path)
                .ok()
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .unwrap_or_else(|| bpf_comm.to_string())
        };
        
        // Read full command line from /proc/[pid]/cmdline
        let cmdline_args = read_cmdline(&format!("/proc/{}/cmdline", pid));
        log::debug!("Process created: pid={}, comm='{}', cmdline={:?}", pid, comm, cmdline_args);

        // Read executable path from /proc/[pid]/exe (symlink)
        let exe_path_str = format!("/proc/{}/exe", pid);
        let exe = fs::read_link(&exe_path_str)
            .map(|p| p.to_string_lossy().into_owned())
            .unwrap_or_default();

        let ctx = ProcessContext {
            comm,
            cmdline_args: cmdline_args.clone(),
            exe_path: exe.clone(),
        };

        // Find the first matching agent
        let matched_info = self.find_match(&ctx)?;

        let discovered = DiscoveredAgent {
            agent_info: matched_info,
            pid,
            cmdline_args,
            exe_path: exe,
        };

        self.tracked_agents.insert(pid, discovered);
        self.tracked_agents.get(&pid)
    }

    /// Handle process exit event
    ///
    /// Remove the process from tracking if it was a known agent.
    ///
    /// # Arguments
    /// * `pid` - Process ID
    ///
    /// # Returns
    ///
    /// `Some(DiscoveredAgent)` if the process was being tracked, `None` otherwise.
    pub fn on_process_exit(&mut self, pid: u32) -> Option<DiscoveredAgent> {
        log::debug!("Process exited: pid={}", pid);
        self.tracked_agents.remove(&pid)
    }

    /// Check if a PID is currently being tracked
    pub fn is_tracked(&self, pid: u32) -> bool {
        self.tracked_agents.contains_key(&pid)
    }

    /// Get a tracked agent by PID
    pub fn get_tracked(&self, pid: u32) -> Option<&DiscoveredAgent> {
        self.tracked_agents.get(&pid)
    }

    /// Get all currently tracked agents
    pub fn tracked_agents(&self) -> &HashMap<u32, DiscoveredAgent> {
        &self.tracked_agents
    }

    /// Get list of tracked PIDs
    pub fn tracked_pids(&self) -> Vec<u32> {
        self.tracked_agents.keys().copied().collect()
    }

    /// Clear all tracked agents
    pub fn clear_tracked(&mut self) {
        self.tracked_agents.clear();
    }

    /// Attempt to match a process against known agents
    fn try_match_process(&self, pid: u32) -> Option<DiscoveredAgent> {
        let proc_dir = format!("/proc/{}", pid);

        // Read process name from /proc/[pid]/comm
        let comm_path = format!("{}/comm", proc_dir);
        let comm = fs::read_to_string(&comm_path).ok()?;
        let process_name = comm.trim().to_string();

        // Read full command line from /proc/[pid]/cmdline
        let cmdline_path = format!("{}/cmdline", proc_dir);
        let cmdline_args = read_cmdline(&cmdline_path);

        // Read executable path from /proc/[pid]/exe (symlink)
        let exe_path = format!("{}/exe", proc_dir);
        let exe = fs::read_link(&exe_path)
            .map(|p| p.to_string_lossy().into_owned())
            .unwrap_or_default();

        let ctx = ProcessContext {
            comm: process_name,
            cmdline_args: cmdline_args.clone(),
            exe_path: exe.clone(),
        };

        let matched_info = self.find_match(&ctx)?;

        Some(DiscoveredAgent {
            agent_info: matched_info,
            pid,
            cmdline_args,
            exe_path: exe,
        })
    }

    /// Find the first matching agent for a process context
    fn find_match(&self, ctx: &ProcessContext) -> Option<AgentInfo> {
        for matcher in &self.matchers {
            if matcher.matches(ctx) {
                return Some(matcher.info().clone());
            }
        }
        None
    }

    /// Get the number of registered agent matchers
    pub fn matcher_count(&self) -> usize {
        self.matchers.len()
    }
}

/// Read and parse cmdline file
///
/// The cmdline file contains arguments separated by null bytes.
/// Returns a vector of command line arguments.
fn read_cmdline(path: &str) -> Vec<String> {
    match fs::read(path) {
        Ok(data) => {
            // Split by null bytes and collect non-empty strings
            data.split(|&b| b == 0)
                .filter_map(|slice| {
                    if slice.is_empty() {
                        None
                    } else {
                        Some(String::from_utf8_lossy(slice).into_owned())
                    }
                })
                .collect()
        }
        Err(_) => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scanner_creation() {
        let scanner = AgentScanner::new();
        assert!(scanner.matcher_count() > 0);
    }

    #[test]
    fn test_scanner_with_custom_matchers() {
        let custom: Vec<Box<dyn AgentMatcher>> = vec![
            Box::new(AgentInfo::new("Test Agent", vec!["test"], "A test agent", "test")),
        ];
        let scanner = AgentScanner::with_matchers(custom);
        assert_eq!(scanner.matcher_count(), 1);
    }

    #[test]
    fn test_matches_case_insensitive() {
        let agent = AgentInfo::new("Claude Code", vec!["claude"], "desc", "cat");
        let ctx = ProcessContext { comm: "CLAUDE".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(agent.matches(&ctx));

        let ctx = ProcessContext { comm: "Claude".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(agent.matches(&ctx));

        let ctx = ProcessContext { comm: "claude".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(agent.matches(&ctx));
    }

    #[test]
    fn test_matches_version_suffix() {
        let agent = AgentInfo::new("Node Agent", vec!["node"], "desc", "cat");
        let ctx = ProcessContext { comm: "node-22".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(agent.matches(&ctx));

        let ctx = ProcessContext { comm: "node.18".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(agent.matches(&ctx));

        // Should NOT match: "nodejs" (alphanumeric continuation)
        let ctx = ProcessContext { comm: "nodejs".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(!agent.matches(&ctx));
    }

    #[test]
    fn test_matches_not_found() {
        let agent = AgentInfo::new("Claude Code", vec!["claude"], "desc", "cat");
        let ctx = ProcessContext { comm: "nonexistent".to_string(), cmdline_args: vec![], exe_path: String::new() };
        assert!(!agent.matches(&ctx));
    }

    #[test]
    fn test_process_lifecycle() {
        let mut scanner = AgentScanner::new();
        
        // Initially no tracked agents
        assert!(scanner.tracked_pids().is_empty());
        
        // Simulate process exit for non-tracked PID
        let result = scanner.on_process_exit(99999);
        assert!(result.is_none());
        
        // Check is_tracked
        assert!(!scanner.is_tracked(99999));
    }

    #[test]
    fn test_custom_matcher() {
        /// A custom matcher that matches by exe_path
        struct ExePathMatcher {
            info: AgentInfo,
            exe_keyword: String,
        }

        impl AgentMatcher for ExePathMatcher {
            fn info(&self) -> &AgentInfo {
                &self.info
            }

            fn matches(&self, ctx: &ProcessContext) -> bool {
                ctx.exe_path.contains(&self.exe_keyword)
            }
        }

        let custom: Vec<Box<dyn AgentMatcher>> = vec![
            Box::new(ExePathMatcher {
                info: AgentInfo::new("Special Agent", vec![], "custom", "custom"),
                exe_keyword: "special-agent".to_string(),
            }),
        ];
        let scanner = AgentScanner::with_matchers(custom);

        // Verify the custom matcher is registered
        assert_eq!(scanner.matcher_count(), 1);
    }
}
