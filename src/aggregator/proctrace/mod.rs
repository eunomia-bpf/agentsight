//! Process trace aggregation module
//!
//! This module provides process event aggregation for correlating
//! process lifecycle events (exec, stdout, stderr, exit) into complete
//! process lifecycles.

mod aggregator;
mod process;

pub use aggregator::ProcessEventAggregator;
pub use process::AggregatedProcess;
