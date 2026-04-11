//! Agent health check module
//!
//! Provides periodic health checking of discovered AI agent processes by:
//! - Detecting their listening TCP ports via `/proc`
//! - Probing them with HTTP requests
//! - Storing results in a shared `HealthStore`

pub mod checker;
pub mod port_detector;
pub mod store;

pub use checker::HealthChecker;
pub use store::{AgentHealthState, AgentHealthStatus, HealthStore};
