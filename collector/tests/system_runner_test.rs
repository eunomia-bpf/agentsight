// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// Standalone test for system runner functionality
// This can be run independently to verify the system monitoring logic

use std::fs;

#[test]
fn test_proc_parsing() {
    // Test /proc/meminfo parsing
    let current_pid = std::process::id();

    // Check if we can read process stats
    let stat_path = format!("/proc/{}/stat", current_pid);
    if let Ok(stat_content) = fs::read_to_string(&stat_path) {
        let fields: Vec<&str> = stat_content.split_whitespace().collect();
        assert!(
            fields.len() >= 15,
            "Stat file should have at least 15 fields"
        );

        // Parse utime and stime
        let utime: u64 = fields[13].parse().expect("Failed to parse utime");
        let stime: u64 = fields[14].parse().expect("Failed to parse stime");

        println!(
            "✓ Successfully parsed CPU stats for PID {}: utime={}, stime={}",
            current_pid, utime, stime
        );
    }

    // Check if we can read memory stats
    let statm_path = format!("/proc/{}/statm", current_pid);
    if let Ok(statm_content) = fs::read_to_string(&statm_path) {
        let fields: Vec<&str> = statm_content.split_whitespace().collect();
        assert!(
            fields.len() >= 2,
            "Statm file should have at least 2 fields"
        );

        let vsz_pages: u64 = fields[0].parse().expect("Failed to parse VSZ");
        let rss_pages: u64 = fields[1].parse().expect("Failed to parse RSS");

        let page_size = 4u64; // 4KB
        let vsz_kb = vsz_pages * page_size;
        let rss_kb = rss_pages * page_size;

        println!(
            "✓ Successfully parsed memory stats for PID {}: VSZ={}KB, RSS={}KB",
            current_pid, vsz_kb, rss_kb
        );
    }

    // Check system-wide metrics
    if let Ok(meminfo) = fs::read_to_string("/proc/meminfo") {
        let mut total_kb = None;
        let mut free_kb = None;

        for line in meminfo.lines() {
            if line.starts_with("MemTotal:") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                total_kb = Some(parts[1].parse::<u64>().expect("Failed to parse MemTotal"));
            } else if line.starts_with("MemFree:") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                free_kb = Some(parts[1].parse::<u64>().expect("Failed to parse MemFree"));
            }
        }

        assert!(
            total_kb.is_some() && free_kb.is_some(),
            "Should parse memory info"
        );
        println!(
            "✓ Successfully parsed system memory: Total={}MB, Free={}MB",
            total_kb.unwrap() / 1024,
            free_kb.unwrap() / 1024
        );
    }

    // Check load average
    if let Ok(loadavg) = fs::read_to_string("/proc/loadavg") {
        let fields: Vec<&str> = loadavg.split_whitespace().collect();
        assert!(
            fields.len() >= 3,
            "Load average should have at least 3 fields"
        );

        let load1: f64 = fields[0].parse().expect("Failed to parse load1");
        let load5: f64 = fields[1].parse().expect("Failed to parse load5");
        let load15: f64 = fields[2].parse().expect("Failed to parse load15");

        println!(
            "✓ Successfully parsed load average: {}, {}, {}",
            load1, load5, load15
        );
    }

    println!("\n✅ All /proc parsing tests passed!");
}

#[test]
fn test_process_discovery() {
    let current_pid = std::process::id();

    // Test finding self by PID
    let stat_path = format!("/proc/{}/stat", current_pid);
    assert!(fs::metadata(&stat_path).is_ok(), "Should find own process");

    // Test reading comm
    let comm_path = format!("/proc/{}/comm", current_pid);
    if let Ok(comm) = fs::read_to_string(&comm_path) {
        println!(
            "✓ Found own process: {} (PID: {})",
            comm.trim(),
            current_pid
        );
    }

    // Test finding processes by name pattern
    let mut found_processes = Vec::new();
    if let Ok(entries) = fs::read_dir("/proc") {
        for entry in entries.flatten() {
            if let Ok(file_name) = entry.file_name().into_string()
                && let Ok(pid) = file_name.parse::<u32>()
                && let Ok(comm) = fs::read_to_string(format!("/proc/{}/comm", pid))
                && (comm.contains("test") || comm.contains("cargo"))
            {
                found_processes.push((pid, comm.trim().to_string()));
            }
        }
    }

    println!(
        "✓ Found {} test/cargo-related processes",
        found_processes.len()
    );
    for (pid, comm) in found_processes.iter().take(5) {
        println!("  - PID {} : {}", pid, comm);
    }

    println!("\n✅ Process discovery tests passed!");
}

#[test]
fn test_thread_count() {
    let current_pid = std::process::id();
    let task_dir = format!("/proc/{}/task", current_pid);

    if let Ok(entries) = fs::read_dir(&task_dir) {
        let thread_count = entries.count();
        println!("✓ Current process has {} threads", thread_count);
        assert!(thread_count >= 1, "Should have at least 1 thread");
    }

    println!("\n✅ Thread count test passed!");
}
