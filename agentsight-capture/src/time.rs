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

/// UNIX epoch minus CLOCK_MONOTONIC, in nanoseconds. The eBPF probes use
/// bpf_ktime_get_ns(), so their timestamps must be paired with this clock.
static MONOTONIC_EPOCH_OFFSET_NS: OnceLock<i128> = OnceLock::new();

#[cfg(unix)]
fn clock_ns(clock: libc::clockid_t) -> Option<i128> {
    let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };
    if unsafe { libc::clock_gettime(clock, &mut ts) } != 0 {
        return None;
    }
    Some(i128::from(ts.tv_sec) * 1_000_000_000 + i128::from(ts.tv_nsec))
}

/// Bracket the realtime read with monotonic reads, using the sample with the
/// shortest interval to minimize clock-read scheduling error.
#[cfg(unix)]
fn sample_monotonic_epoch_offset_ns() -> Option<i128> {
    let mut best: Option<(i128, i128)> = None;
    for _ in 0..5 {
        let before = clock_ns(libc::CLOCK_MONOTONIC)?;
        let realtime = clock_ns(libc::CLOCK_REALTIME)?;
        let after = clock_ns(libc::CLOCK_MONOTONIC)?;
        let span = after - before;
        if span < 0 {
            continue;
        }
        if best.is_none_or(|(best_span, _)| span < best_span) {
            best = Some((span, realtime - (before + span / 2)));
        }
    }
    best.map(|(_, offset)| offset)
}

fn epoch_ms_with_offset(ns_since_boot: u64, offset_ns: i128) -> u64 {
    (i128::from(ns_since_boot) + offset_ns)
        .div_euclid(1_000_000)
        .clamp(0, i128::from(u64::MAX)) as u64
}

/// Get the system boot time in seconds since UNIX epoch
///
/// This uses the platform process backend and caches the result.
pub fn get_boot_time_secs() -> i64 {
    *BOOT_TIME_SECS.get_or_init(|| {
        if let Ok(boot_time) = i64::try_from(sysinfo::System::boot_time())
            && boot_time > 0
        {
            return boot_time;
        }

        let now_secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;
        let uptime_secs = i64::try_from(sysinfo::System::uptime())
            .ok()
            .filter(|uptime| *uptime > 0)
            .unwrap_or(1);
        now_secs.saturating_sub(uptime_secs)
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
    let offset = *MONOTONIC_EPOCH_OFFSET_NS.get_or_init(|| {
        #[cfg(unix)]
        if let Some(offset) = sample_monotonic_epoch_offset_ns() {
            return offset;
        }
        // Preserve the existing cross-platform fallback if the clock API
        // is unavailable. This fallback has only whole-second precision.
        i128::from(get_boot_time_secs()) * 1_000_000_000
    });
    epoch_ms_with_offset(ns_since_boot, offset)
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
        assert!(boot_time > 1577836800); // 2020-01-01
    }

    #[test]
    fn test_boot_ns_to_epoch_ms_conversion() {
        // Test with a known timestamp: 1000 seconds after boot
        let ns_since_boot = 1_000_000_000_000u64; // 1000 seconds in nanoseconds
        let result_ms = boot_ns_to_epoch_ms(ns_since_boot);

        assert_eq!(boot_ns_to_epoch_ms(ns_since_boot + 1_000_000_000), result_ms + 1000);
    }

    #[test]
    fn test_subsecond_epoch_offset_is_preserved() {
        // 1.234567890 seconds after a boot at UNIX second 1700000000.123456789.
        assert_eq!(
            epoch_ms_with_offset(1_234_567_890, 1_700_000_000_123_456_789),
            1_700_000_001_358
        );
    }

    #[cfg(unix)]
    #[test]
    fn test_monotonic_epoch_conversion_matches_realtime() {
        let monotonic_ns = clock_ns(libc::CLOCK_MONOTONIC).unwrap();
        let realtime_ns = clock_ns(libc::CLOCK_REALTIME).unwrap();
        let converted_ms = boot_ns_to_epoch_ms(monotonic_ns as u64);
        let realtime_ms = realtime_ns / 1_000_000;
        assert!(
            (i128::from(converted_ms) - realtime_ms).abs() < 50,
            "timestamp differs from realtime by more than 50 ms"
        );
    }
}
