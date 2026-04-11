//! Custom agent matcher implementations
//!
//! This module hosts agents that need custom matching logic beyond
//! the default `process_names` matching approach.
//!
//! Each agent is defined in its own submodule and implements `AgentMatcher`.

pub mod cosh;
pub mod openclaw;