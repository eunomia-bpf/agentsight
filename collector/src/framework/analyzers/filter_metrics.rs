// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Shared global-metrics machinery for the HTTP and SSL filter analyzers.
//!
//! Both filters publish cumulative `{total, filtered, passed}` counters to a
//! process-global slot so they can be printed after the run. They differ only
//! in *how* they publish: the HTTP filter overwrites the slot with its latest
//! cumulative snapshot inline ([`set`]), while the SSL filter adds its totals
//! once on `Drop` ([`add`]). Both semantics are preserved here.

use std::sync::{Arc, Mutex, OnceLock};

/// Cumulative filter counters published for end-of-run reporting.
#[derive(Default)]
pub(crate) struct FilterCounts {
    pub total: u64,
    pub filtered: u64,
    pub passed: u64,
}

/// A process-global metrics slot owned by each filter analyzer.
pub(crate) type MetricsSlot = OnceLock<Arc<Mutex<FilterCounts>>>;

fn counts(slot: &MetricsSlot) -> &Arc<Mutex<FilterCounts>> {
    slot.get_or_init(|| Arc::new(Mutex::new(FilterCounts::default())))
}

/// Overwrite the published counts with the latest cumulative snapshot.
pub(crate) fn set(slot: &MetricsSlot, total: u64, filtered: u64, passed: u64) {
    if let Ok(mut m) = counts(slot).lock() {
        m.total = total;
        m.filtered = filtered;
        m.passed = passed;
    }
}

/// Add the given counts to the published totals.
pub(crate) fn add(slot: &MetricsSlot, total: u64, filtered: u64, passed: u64) {
    if let Ok(mut m) = counts(slot).lock() {
        m.total += total;
        m.filtered += filtered;
        m.passed += passed;
    }
}

/// Print the published counts under the given label (e.g. "HTTPFilter").
pub(crate) fn print(label: &str, slot: &MetricsSlot) {
    match slot.get().and_then(|r| r.lock().ok()) {
        Some(m) => println!(
            "[{} Global Metrics] Total: {}, Filtered: {}, Passed: {}",
            label, m.total, m.filtered, m.passed
        ),
        None => println!("[{} Global Metrics] No metrics available", label),
    }
}
