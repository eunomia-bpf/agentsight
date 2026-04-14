//! Agent matching trait and process context
//!
//! This module defines the `AgentMatcher` trait for identifying AI agent processes,
//! along with `ProcessContext` and helper matching functions.

use super::agent::AgentInfo;

/// Process context passed to agent matchers for identification
pub struct ProcessContext {
    /// Process name (from /proc/[pid]/comm or BPF event)
    pub comm: String,
    /// Parsed command line arguments (argv vector)
    pub cmdline_args: Vec<String>,
    /// Executable file path
    pub exe_path: String,
}

/// Trait for matching a process to an AI agent
///
/// Provides a default matching implementation based on `AgentInfo` fields.
/// Special agents can implement this trait on custom structs to override
/// the matching logic while reusing the same scanner infrastructure.
///
/// # Example: custom matcher
///
/// ```rust,ignore
/// struct MySpecialAgent {
///     info: AgentInfo,
/// }
///
/// impl AgentMatcher for MySpecialAgent {
///     fn info(&self) -> &AgentInfo { &self.info }
///
///     fn matches(&self, ctx: &ProcessContext) -> bool {
///         // custom logic: check env var, socket file, etc.
///         ctx.exe_path.contains("my-special-agent")
///     }
/// }
/// ```
pub trait AgentMatcher: Send + Sync {
    /// Return the agent metadata
    fn info(&self) -> &AgentInfo;

    /// Check if a process matches this agent
    ///
    /// Default implementation matches `comm` against `process_names`
    /// (case-insensitive, version-suffix tolerant).
    /// For complex matching logic (e.g., node + cmdline pattern),
    /// implement a custom matcher struct.
    fn matches(&self, ctx: &ProcessContext) -> bool {
        let info = self.info();
        let comm_lower = ctx.comm.to_lowercase();

        info.process_names.iter().any(|name| {
            match_name_with_version_suffix(&comm_lower, &name.to_lowercase())
        })
    }
}

/// Default `AgentMatcher` implementation for `AgentInfo`
///
/// Most agents use this — the default `matches()` logic from the trait.
impl AgentMatcher for AgentInfo {
    fn info(&self) -> &AgentInfo {
        self
    }
}

/// Match process name against a known name, allowing version suffixes
///
/// This is useful for matching runtime processes like "node-22", "python3.11",
/// "python3" where the version is part of the process name.
///
/// The separator must be a non-alphanumeric char (e.g., '-', '.', '_')
/// to avoid false positives like "codeium" matching "code".
///
/// # Examples
/// - "node-22" matches "node"
/// - "python3.11" matches "python3"
/// - "python3" matches "python3" (exact match)
/// - "nodejs" does NOT match "node" (alphanumeric continuation)
pub fn match_name_with_version_suffix(process_name: &str, known_name: &str) -> bool {
    if process_name == known_name {
        return true;
    }
    if let Some(rest) = process_name.strip_prefix(known_name) {
        rest.starts_with(|c: char| !c.is_alphanumeric())
    } else {
        false
    }
}
