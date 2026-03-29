//! Core type definitions for AI agent discovery
//!
//! This module defines the data types used to describe AI agents
//! and represent discovered agent processes.

/// Describes a known AI Agent type
///
/// This struct contains metadata about a specific AI agent product,
/// including the process names that can be used to identify it.
#[derive(Debug, Clone)]
pub struct AgentInfo {
    /// Agent name (e.g., "Claude Code", "Aider", "GitHub Copilot")
    pub name: String,
    /// Process names used for matching (may have multiple variants)
    pub process_names: Vec<String>,
    /// Agent description
    pub description: String,
    /// Agent category (e.g., "coding-assistant", "chat", "cli")
    pub category: String,
}

impl AgentInfo {
    /// Create a new AgentInfo with the given parameters
    pub fn new(
        name: impl Into<String>,
        process_names: Vec<&str>,
        description: impl Into<String>,
        category: impl Into<String>,
    ) -> Self {
        Self {
            name: name.into(),
            process_names: process_names.into_iter().map(String::from).collect(),
            description: description.into(),
            category: category.into(),
        }
    }
}

/// A discovered agent process instance at runtime
///
/// This struct represents an actual running process that has been
/// identified as an AI agent based on matching against known agent types.
#[derive(Debug, Clone)]
pub struct DiscoveredAgent {
    /// The corresponding agent type information
    pub agent_info: AgentInfo,
    /// Process ID
    pub pid: u32,
    /// Parsed command line arguments (argv vector)
    pub cmdline_args: Vec<String>,
    /// Process executable file path
    pub exe_path: String,
}
