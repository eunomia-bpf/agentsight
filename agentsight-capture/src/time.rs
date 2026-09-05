// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Timestamp conversion utilities
//!
//! All timestamps in the system are standardized to milliseconds since UNIX epoch
//! for consistency and ease of use in the frontend.

use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

/// Cached boot time in seconds since UNIX epoch
static BOOT_TIME_SECS: OnceLock<i64> = OnceLock::new();

/// Earliest plausible boot timestamp accepted by the conversion helpers.
const MIN_BOOT_TIME_SECS: i64 = 1_577_836_800; // 2020-01-01 00:00:00 UTC

fn is_plausible_boot_time(candidate: i64, now_secs: i64) -> bool {
    candidate > MIN_BOOT_TIME_SECS && candidate < now_secs
}

fn select_boot_time_secs(
    reported_boot_time_secs: Option<i64>,
    uptime_secs: Option<i64>,
    now_secs: i64,
) -> i64 {
    if let Some(boot_time) = reported_boot_time_secs
        && is_plausible_boot_time(boot_time, now_secs)
    {
        return boot_time;
    }

    if let Some(uptime) = uptime_secs.filter(|uptime| *uptime > 0 && *uptime < now_secs) {
        let derived_boot_time = now_secs.saturating_sub(uptime);
        if is_plausible_boot_time(derived_boot_time, now_secs) {
            return derived_boot_time;
        }
    }

    now_secs.saturating_sub(1)
}

/// Get the system boot time in seconds since UNIX epoch
///
/// This uses the platform process backend and caches the result.
pub fn get_boot_time_secs() -> i64 {
    *BOOT_TIME_SECS.get_or_init(|| {
        let now_secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;

        let reported_boot_time_secs = i64::try_from(sysinfo::System::boot_time()).ok();
        let uptime_secs = i64::try_from(sysinfo::System::uptime()).ok();
        select_boot_time_secs(reported_boot_time_secs, uptime_secs, now_secs)
    })
}

/// Convert nanoseconds since boot to milliseconds since UNIX epoch
///
/// This is used to convert eBPF timestamps (from bpf_ktime_get_ns()) to standard UNIX timestamps.
///
/// # Arguments
/// * `ns_since_boot` - Nanoseconds since system boot (from bpf_ktime_get_ns())
///
/// # Returns
/// Milliseconds since UNIX epoch (1970-01-01 00:00:00 UTC)
pub fn boot_ns_to_epoch_ms(ns_since_boot: u64) -> u64 {
    let boot_time_secs = get_boot_time_secs();
    let boot_time_ms = boot_time_secs * 1000;
    let offset_ms = (ns_since_boot / 1_000_000) as i64;
    (boot_time_ms + offset_ms) as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_boot_time_is_reasonable() {
        let boot_time = get_boot_time_secs();
        // Boot time should be in the past (less than current time)
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;
        assert!(boot_time < now);
        // Boot time should be reasonable (after year 2020)
        assert!(boot_time > MIN_BOOT_TIME_SECS);
    }

    #[test]
    fn select_boot_time_rejects_invalid_positive_reported_time() {
        let now = 1_800_000_000;
        let invalid_boot_time = 1;

        let boot_time = select_boot_time_secs(Some(invalid_boot_time), None, now);

        assert_eq!(boot_time, now - 1);
    }

    #[test]
    fn select_boot_time_rejects_future_reported_time() {
        let now = 1_800_000_000;
        let valid_uptime = 600;

        let boot_time = select_boot_time_secs(Some(now + 60), Some(valid_uptime), now);

        assert_eq!(boot_time, now - valid_uptime);
    }

    #[test]
    fn select_boot_time_rejects_derived_invalid_reported_time() {
        let now = 1_800_000_000;
        let invalid_boot_time = 1;
        let circular_uptime = now - invalid_boot_time;

        let boot_time = select_boot_time_secs(Some(invalid_boot_time), Some(circular_uptime), now);

        assert_eq!(boot_time, now - 1);
    }

    #[test]
    fn test_boot_ns_to_epoch_ms_conversion() {
        // Test with a known timestamp: 1000 seconds after boot
        let ns_since_boot = 1_000_000_000_000u64; // 1000 seconds in nanoseconds
        let result_ms = boot_ns_to_epoch_ms(ns_since_boot);

        let boot_time = get_boot_time_secs();
        let expected_ms = (boot_time + 1000) * 1000;

        assert_eq!(result_ms, expected_ms as u64);
    }
}
