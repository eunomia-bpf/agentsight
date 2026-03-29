//! FFI interface for AgentSight - C API for other languages
//!
//! This module provides C-compatible functions to use AgentSight from other languages.

use crate::unified::AgentSight;
use crate::config::AgentsightConfig;
use std::ffi::{CStr, CString, c_char, c_int, c_uint, c_void};
use std::ptr;
use std::sync::atomic::{AtomicBool, Ordering};

/// Run AgentSight in current thread (blocking)
///
/// This function creates an AgentSight instance internally and runs it.
/// It blocks until agentsight_stop() is called from another thread.
///
/// # Arguments
/// - target_pids: Array of PIDs to trace (null for auto-discover)
/// - pid_count: Number of PIDs in array
/// - verbose: Enable verbose logging (0=false, 1=true)
///
/// # Returns
/// 0 on success, -1 on error
#[unsafe(no_mangle)]
pub extern "C" fn agentsight_run() {
    std::thread::spawn(|| {
        agent_run();
    });
}

fn agent_run() {
    // Build AgentSight with default settings (auto-attaches and starts polling)
    let config = AgentsightConfig::new();
    let mut sight = match AgentSight::new(config) {
        Ok(s) => s,
        Err(e) => {
            log::error!("agentsight_run failed: {}", e);
            return;
        }
    };

    let _ = sight.run();
}
