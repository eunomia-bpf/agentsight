//! Discovery module for AI agent process detection
//!
//! This module provides functionality to discover and identify AI agent processes
//! running on the system by scanning the /proc filesystem.
//!
//! # Overview
//!
//! The discovery module consists of:
//! - `agent`: Core types (`AgentInfo`, `DiscoveredAgent`)
//! - `matcher`: Matching trait (`AgentMatcher`, `ProcessContext`)
//! - `registry`: Built-in known agent list
//! - `scanner`: System scanner using /proc
//!
//! # Example
//!
//! ```rust,ignore
//! use agentsight::discovery::{AgentScanner, DiscoveredAgent};
//!
//! let scanner = AgentScanner::new();
//! let agents = scanner.scan();
//!
//! for agent in agents {
//!     println!("Found {} (PID: {})", agent.agent_info.name, agent.pid);
//! }
//! ```

pub mod agent;
pub mod agents;
pub mod matcher;
pub mod registry;
pub mod scanner;

pub use agent::{AgentInfo, DiscoveredAgent};
pub use matcher::{AgentMatcher, ProcessContext};
pub use registry::known_agents;
pub use scanner::AgentScanner;
