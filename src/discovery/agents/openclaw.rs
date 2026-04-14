//! OpenClaw agent matcher
//!
//! OpenClaw can be started in two ways:
//! 1. Direct binary: process name is "openclaw-gateway" (truncated to 15 chars)
//! 2. Via node: process name is "node" with "openclaw" in cmdline args
//!
//! This matcher handles both scenarios.
//! Note: Only matches the gateway process, not openclaw or openclaw-tui.

use crate::discovery::agent::AgentInfo;
use crate::discovery::matcher::{AgentMatcher, ProcessContext, match_name_with_version_suffix};

/// Custom matcher for OpenClaw Gateway
///
/// Matches by either:
/// - Process name starts with "openclaw-gatewa" (direct binary, truncated to 15 chars)
/// - Node runtime with "openclaw" and "gateway" in cmdline args
pub struct OpenClawMatcher {
    info: AgentInfo,
}

impl OpenClawMatcher {
    pub fn new() -> Self {
        Self {
            info: AgentInfo::new(
                "OpenClaw",
                vec!["openclaw-gatewa", "node"],
                "OpenClaw - open-source AI personal assistant",
                "personal-assistant",
            ),
        }
    }
}

impl AgentMatcher for OpenClawMatcher {
    fn info(&self) -> &AgentInfo {
        &self.info
    }

    fn matches(&self, ctx: &ProcessContext) -> bool {
        let comm_lower = ctx.comm.to_lowercase();

        // Case 1: Direct binary - process name is "openclaw-gatewa" (truncated to 15 chars)
        // Note: This matches only the gateway, not "openclaw" or "openclaw-tui"
        if comm_lower.starts_with("openclaw-gatewa") {
            return true;
        }

        // Case 2: Node runtime with "openclaw" and "gateway" in cmdline args
        let is_node = match_name_with_version_suffix(&comm_lower, "node");
        if is_node {
            let has_openclaw = ctx.cmdline_args.iter().any(|arg| {
                arg.to_lowercase().contains("openclaw")
            });
            let has_gateway = ctx.cmdline_args.iter().any(|arg| {
                arg.to_lowercase() == "gateway"
            });
            if has_openclaw && has_gateway {
                return true;
            }
        }

        false
    }
}
