/// Timestamp conversion utilities
///
/// All timestamps in the system are standardized to milliseconds since UNIX epoch
/// for consistency and ease of use in the frontend.

use std::fs;
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

/// Cached boot time in seconds since UNIX epoch
static BOOT_TIME_SECS: OnceLock<i64> = OnceLock::new();

/// Get the system boot time in seconds since UNIX epoch
///
/// This reads from /proc/stat (btime field) and caches the result.
/// Falls back to calculating from /proc/uptime if btime is not available.
pub fn get_boot_time_secs() -> i64 {
    *BOOT_TIME_SECS.get_or_init(|| {
        // Try to read from /proc/stat (most reliable)
        if let Ok(content) = fs::read_to_string("/proc/stat") {
            for line in content.lines() {
                if line.starts_with("btime ") {
                    if let Some(btime_str) = line.split_whitespace().nth(1) {
                        if let Ok(btime) = btime_str.parse::<i64>() {
                            return btime;
                        }
                    }
                }
            }
        }

        // Fallback: calculate from uptime
        if let Ok(uptime_str) = fs::read_to_string("/proc/uptime") {
            if let Some(uptime_secs_str) = uptime_str.split_whitespace().next() {
                if let Ok(uptime_secs) = uptime_secs_str.parse::<f64>() {
                    let now_secs = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap()
                        .as_secs() as i64;
                    return now_secs - uptime_secs as i64;
                }
            }
        }

        // Last resort: return current time (will be incorrect but won't crash)
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64
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
        assert!(boot_time > 1577836800); // 2020-01-01
    }

    #[test]
    fn test_boot_ns_to_epoch_ms_conversion() {
        // Test with a known timestamp: 1000 seconds after boot
        let ns_since_boot = 1000_000_000_000u64; // 1000 seconds in nanoseconds
        let result_ms = boot_ns_to_epoch_ms(ns_since_boot);

        let boot_time = get_boot_time_secs();
        let expected_ms = (boot_time + 1000) * 1000;

        assert_eq!(result_ms, expected_ms as u64);
    }

}
