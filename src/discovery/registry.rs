//! Built-in registry of known AI agents
//!
//! This module provides the default list of AI coding assistants and agents
//! that can be automatically discovered on the system.

use super::agents::cosh::CoshMatcher;
use super::agents::openclaw::OpenClawMatcher;
use super::matcher::AgentMatcher;

/// Returns a list of known AI agent matchers
///
/// This function provides a built-in registry of common AI coding assistants
/// and agents that can be discovered on the system.
pub fn known_agents() -> Vec<Box<dyn AgentMatcher>> {
    vec![
        // OpenClaw (custom matcher: handles both direct binary and node startup)
        Box::new(OpenClawMatcher::new()),
        // Cosh (custom matcher: node + /usr/bin/co)
        Box::new(CoshMatcher::new()),
    ]
}
