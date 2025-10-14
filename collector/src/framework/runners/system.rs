use super::{Runner, EventStream, RunnerError};
use crate::framework::core::Event;
use crate::framework::analyzers::Analyzer;
use async_trait::async_trait;
use futures::stream::Stream;
use serde_json::json;
use std::collections::HashMap;
use std::fs;
use std::pin::Pin;
use std::time::Duration;
use tokio::time;

/// Configuration for system resource monitoring
#[derive(Debug, Clone)]
pub struct SystemConfig {
    /// Monitoring interval in seconds (default: 10)
    pub interval_secs: u64,
    /// Monitor specific PID (None = monitor all)
    pub pid: Option<u32>,
    /// Process name to monitor (None = monitor all)
    pub comm: Option<String>,
    /// Include child processes in aggregation
    pub include_children: bool,
    /// CPU usage threshold for alerts (%)
    pub cpu_threshold: Option<f64>,
    /// Memory usage threshold for alerts (MB)
    pub memory_threshold: Option<u64>,
}

impl Default for SystemConfig {
    fn default() -> Self {
        Self {
            interval_secs: 10,
            pid: None,
            comm: None,
            include_children: true,
            cpu_threshold: None,
            memory_threshold: None,
        }
    }
}

/// Runner for collecting system resource metrics (CPU and memory)
pub struct SystemRunner {
    config: SystemConfig,
    analyzers: Vec<Box<dyn Analyzer>>,
}

impl SystemRunner {
    /// Create a new system runner with default configuration
    pub fn new() -> Self {
        Self {
            config: SystemConfig::default(),
            analyzers: Vec::new(),
        }
    }

    /// Set the monitoring interval in seconds
    pub fn interval(mut self, secs: u64) -> Self {
        self.config.interval_secs = secs;
        self
    }

    /// Monitor a specific PID
    pub fn pid(mut self, pid: u32) -> Self {
        self.config.pid = Some(pid);
        self
    }

    /// Monitor processes by name
    pub fn comm(mut self, comm: impl Into<String>) -> Self {
        self.config.comm = Some(comm.into());
        self
    }

    /// Include child processes in metrics aggregation
    pub fn include_children(mut self, include: bool) -> Self {
        self.config.include_children = include;
        self
    }

    /// Set CPU usage threshold for alerts (%)
    pub fn cpu_threshold(mut self, threshold: f64) -> Self {
        self.config.cpu_threshold = Some(threshold);
        self
    }

    /// Set memory usage threshold for alerts (MB)
    pub fn memory_threshold(mut self, threshold: u64) -> Self {
        self.config.memory_threshold = Some(threshold);
        self
    }
}

impl Default for SystemRunner {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl Runner for SystemRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        let config = self.config.clone();

        // Create the event stream
        let stream = create_system_event_stream(config);

        // Process through analyzers
        let event_stream = super::common::AnalyzerProcessor::process_through_analyzers(
            Box::pin(stream),
            &mut self.analyzers,
        )
        .await?;

        Ok(event_stream)
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }

    fn name(&self) -> &str {
        "system"
    }

    fn id(&self) -> String {
        "system".to_string()
    }
}

/// Get nanoseconds since boot (matching bpf_ktime_get_ns() behavior)
fn get_boot_time_ns() -> u64 {
    // Read /proc/uptime to get seconds since boot
    if let Ok(uptime_str) = fs::read_to_string("/proc/uptime") {
        if let Some(uptime_secs) = uptime_str.split_whitespace().next() {
            if let Ok(secs) = uptime_secs.parse::<f64>() {
                return (secs * 1_000_000_000.0) as u64;
            }
        }
    }
    0
}

/// Create a stream of system monitoring events
fn create_system_event_stream(
    config: SystemConfig,
) -> Pin<Box<dyn Stream<Item = Event> + Send>> {
    Box::pin(async_stream::stream! {
        let mut interval = time::interval(Duration::from_secs(config.interval_secs));
        let mut previous_stats: HashMap<u32, ProcessStats> = HashMap::new();

        loop {
            interval.tick().await;

            let timestamp = get_boot_time_ns();

            // Find target PIDs to monitor
            let target_pids = find_target_pids(&config);

            if target_pids.is_empty() {
                // If monitoring by name/pid and nothing found, continue waiting
                if config.pid.is_some() || config.comm.is_some() {
                    continue;
                }
                // Otherwise, emit system-wide metrics
                if let Ok(system_metrics) = get_system_wide_metrics(timestamp) {
                    yield system_metrics;
                }
                continue;
            }

            // Collect metrics for each target PID
            for pid in target_pids {
                // Get all PIDs to monitor (including children if configured)
                let pids_to_monitor = if config.include_children {
                    let mut all_pids = vec![pid];
                    all_pids.extend(get_all_children(pid));
                    all_pids
                } else {
                    vec![pid]
                };

                // Aggregate metrics across all monitored PIDs
                if let Ok(event) = collect_process_metrics(
                    pid,
                    &pids_to_monitor,
                    timestamp,
                    &mut previous_stats,
                    &config,
                ) {
                    yield event;
                }
            }
        }
    })
}

/// Process statistics for CPU calculation
#[derive(Debug, Clone)]
struct ProcessStats {
    utime: u64,
    stime: u64,
    timestamp: u64,
}

/// Find PIDs that match the monitoring criteria
fn find_target_pids(config: &SystemConfig) -> Vec<u32> {
    if let Some(pid) = config.pid {
        // Monitor specific PID
        if process_exists(pid) {
            vec![pid]
        } else {
            vec![]
        }
    } else if let Some(ref comm_pattern) = config.comm {
        // Find PIDs by process name
        find_pids_by_name(comm_pattern)
    } else {
        // No specific target - caller should handle system-wide monitoring
        vec![]
    }
}

/// Check if a process exists
fn process_exists(pid: u32) -> bool {
    fs::metadata(format!("/proc/{}", pid)).is_ok()
}

/// Find all PIDs matching a process name pattern
fn find_pids_by_name(pattern: &str) -> Vec<u32> {
    let mut matching_pids = Vec::new();

    if let Ok(entries) = fs::read_dir("/proc") {
        for entry in entries.flatten() {
            if let Ok(file_name) = entry.file_name().into_string() {
                if let Ok(pid) = file_name.parse::<u32>() {
                    if let Ok(comm) = fs::read_to_string(format!("/proc/{}/comm", pid)) {
                        if comm.trim().contains(pattern) {
                            matching_pids.push(pid);
                        }
                    }
                }
            }
        }
    }

    matching_pids
}

/// Get all child PIDs recursively
fn get_all_children(parent_pid: u32) -> Vec<u32> {
    let mut children = Vec::new();

    if let Ok(entries) = fs::read_dir("/proc") {
        for entry in entries.flatten() {
            if let Ok(file_name) = entry.file_name().into_string() {
                if let Ok(pid) = file_name.parse::<u32>() {
                    if let Ok(stat) = fs::read_to_string(format!("/proc/{}/stat", pid)) {
                        // Extract PPID from stat file
                        let fields: Vec<&str> = stat.split_whitespace().collect();
                        if fields.len() > 3 {
                            if let Ok(ppid) = fields[3].parse::<u32>() {
                                if ppid == parent_pid {
                                    children.push(pid);
                                    // Recursively get grandchildren
                                    children.extend(get_all_children(pid));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    children
}

/// Collect metrics for a process and its children
fn collect_process_metrics(
    main_pid: u32,
    all_pids: &[u32],
    timestamp: u64,
    previous_stats: &mut HashMap<u32, ProcessStats>,
    config: &SystemConfig,
) -> Result<Event, Box<dyn std::error::Error + Send + Sync>> {
    let mut total_rss_kb = 0u64;
    let mut total_vsz_kb = 0u64;
    let mut total_cpu_percent = 0.0f64;
    let mut thread_count = 0u32;
    let mut process_name = String::from("unknown");

    // Get main process name
    if let Ok(comm) = fs::read_to_string(format!("/proc/{}/comm", main_pid)) {
        process_name = comm.trim().to_string();
    }

    // Aggregate metrics across all PIDs
    for &pid in all_pids {
        if !process_exists(pid) {
            continue;
        }

        // Get memory info
        if let Ok((rss, vsz)) = get_process_memory(pid) {
            total_rss_kb += rss;
            total_vsz_kb += vsz;
        }

        // Get CPU usage
        if let Ok(stats) = get_process_cpu_stats(pid) {
            let cpu_percent = calculate_cpu_percentage(
                pid,
                &stats,
                previous_stats,
                timestamp,
            );
            total_cpu_percent += cpu_percent;
        }

        // Count threads (only for main process)
        if pid == main_pid {
            thread_count = get_thread_count(pid);
        }
    }

    let children_count = all_pids.len() - 1; // Exclude main process

    // Check thresholds for alerts
    let mut alert = false;
    if let Some(cpu_threshold) = config.cpu_threshold {
        if total_cpu_percent >= cpu_threshold {
            alert = true;
        }
    }
    if let Some(memory_threshold) = config.memory_threshold {
        if total_rss_kb / 1024 >= memory_threshold {
            alert = true;
        }
    }

    // Build JSON payload
    let payload = json!({
        "type": "system_metrics",
        "pid": main_pid,
        "comm": process_name,
        "timestamp": timestamp,
        "cpu": {
            "percent": format!("{:.2}", total_cpu_percent),
            "cores": num_cpus::get(),
        },
        "memory": {
            "rss_kb": total_rss_kb,
            "rss_mb": total_rss_kb / 1024,
            "vsz_kb": total_vsz_kb,
            "vsz_mb": total_vsz_kb / 1024,
        },
        "process": {
            "threads": thread_count,
            "children": children_count,
        },
        "alert": alert,
    });

    Ok(Event::new_with_timestamp(
        timestamp,
        "system".to_string(),
        main_pid,
        process_name,
        payload,
    ))
}

/// Get system-wide metrics when no specific process is targeted
fn get_system_wide_metrics(timestamp: u64) -> Result<Event, Box<dyn std::error::Error + Send + Sync>> {
    // Read system-wide CPU and memory info
    let cpu_cores = num_cpus::get();

    // Get load average
    let load_avg = get_load_average()?;

    // Get total memory info
    let (total_mem_kb, free_mem_kb, available_mem_kb) = get_system_memory()?;
    let used_mem_kb = total_mem_kb - available_mem_kb;
    let used_percent = (used_mem_kb as f64 / total_mem_kb as f64) * 100.0;

    let payload = json!({
        "type": "system_wide",
        "timestamp": timestamp,
        "cpu": {
            "cores": cpu_cores,
            "load_avg_1min": load_avg.0,
            "load_avg_5min": load_avg.1,
            "load_avg_15min": load_avg.2,
        },
        "memory": {
            "total_kb": total_mem_kb,
            "total_mb": total_mem_kb / 1024,
            "used_kb": used_mem_kb,
            "used_mb": used_mem_kb / 1024,
            "free_kb": free_mem_kb,
            "available_kb": available_mem_kb,
            "used_percent": format!("{:.2}", used_percent),
        },
    });

    Ok(Event::new_with_timestamp(
        timestamp,
        "system".to_string(),
        0, // No specific PID for system-wide metrics
        "system".to_string(),
        payload,
    ))
}

/// Get process memory usage (RSS and VSZ in KB)
fn get_process_memory(pid: u32) -> Result<(u64, u64), Box<dyn std::error::Error + Send + Sync>> {
    let statm = fs::read_to_string(format!("/proc/{}/statm", pid))?;
    let fields: Vec<&str> = statm.split_whitespace().collect();

    if fields.len() < 2 {
        return Err("Invalid statm format".into());
    }

    // VSZ (virtual size) and RSS (resident set size) in pages
    let page_size = 4u64; // 4KB page size on most systems
    let vsz_pages: u64 = fields[0].parse()?;
    let rss_pages: u64 = fields[1].parse()?;

    Ok((rss_pages * page_size, vsz_pages * page_size))
}

/// Get process CPU statistics from /proc/[pid]/stat
fn get_process_cpu_stats(pid: u32) -> Result<ProcessStats, Box<dyn std::error::Error + Send + Sync>> {
    let stat = fs::read_to_string(format!("/proc/{}/stat", pid))?;
    let fields: Vec<&str> = stat.split_whitespace().collect();

    if fields.len() < 15 {
        return Err("Invalid stat format".into());
    }

    let utime: u64 = fields[13].parse()?;
    let stime: u64 = fields[14].parse()?;
    let timestamp = get_boot_time_ns();

    Ok(ProcessStats {
        utime,
        stime,
        timestamp,
    })
}

/// Calculate CPU percentage based on previous stats
fn calculate_cpu_percentage(
    pid: u32,
    current: &ProcessStats,
    previous_stats: &mut HashMap<u32, ProcessStats>,
    timestamp: u64,
) -> f64 {
    let cpu_percent = if let Some(prev) = previous_stats.get(&pid) {
        let time_delta = (timestamp - prev.timestamp) as f64 / 1_000_000_000.0; // Convert nanoseconds to seconds
        let cpu_delta = (current.utime + current.stime) - (prev.utime + prev.stime);

        // CPU ticks to percentage (assumes USER_HZ = 100)
        let user_hz = 100.0;
        if time_delta > 0.0 {
            (cpu_delta as f64 / user_hz / time_delta) * 100.0
        } else {
            0.0
        }
    } else {
        0.0 // First measurement, no previous data
    };

    // Update previous stats
    previous_stats.insert(pid, current.clone());

    cpu_percent
}

/// Get thread count for a process
fn get_thread_count(pid: u32) -> u32 {
    fs::read_dir(format!("/proc/{}/task", pid))
        .map(|entries| entries.count() as u32)
        .unwrap_or(1)
}

/// Get system load average
fn get_load_average() -> Result<(f64, f64, f64), Box<dyn std::error::Error + Send + Sync>> {
    let loadavg = fs::read_to_string("/proc/loadavg")?;
    let fields: Vec<&str> = loadavg.split_whitespace().collect();

    if fields.len() < 3 {
        return Err("Invalid loadavg format".into());
    }

    Ok((
        fields[0].parse()?,
        fields[1].parse()?,
        fields[2].parse()?,
    ))
}

/// Get system memory information from /proc/meminfo
fn get_system_memory() -> Result<(u64, u64, u64), Box<dyn std::error::Error + Send + Sync>> {
    let meminfo = fs::read_to_string("/proc/meminfo")?;
    let mut total_kb = 0u64;
    let mut free_kb = 0u64;
    let mut available_kb = 0u64;

    for line in meminfo.lines() {
        if line.starts_with("MemTotal:") {
            total_kb = parse_meminfo_line(line)?;
        } else if line.starts_with("MemFree:") {
            free_kb = parse_meminfo_line(line)?;
        } else if line.starts_with("MemAvailable:") {
            available_kb = parse_meminfo_line(line)?;
        }
    }

    Ok((total_kb, free_kb, available_kb))
}

/// Parse a single line from /proc/meminfo
fn parse_meminfo_line(line: &str) -> Result<u64, Box<dyn std::error::Error + Send + Sync>> {
    let parts: Vec<&str> = line.split_whitespace().collect();
    if parts.len() < 2 {
        return Err("Invalid meminfo line".into());
    }
    Ok(parts[1].parse()?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_system_runner_creation() {
        let runner = SystemRunner::new();
        assert_eq!(runner.name(), "system");
        assert_eq!(runner.id(), "system");
        assert_eq!(runner.config.interval_secs, 10);
    }

    #[test]
    fn test_system_runner_with_config() {
        let runner = SystemRunner::new()
            .interval(5)
            .pid(1234)
            .include_children(false)
            .cpu_threshold(80.0)
            .memory_threshold(500);

        assert_eq!(runner.config.interval_secs, 5);
        assert_eq!(runner.config.pid, Some(1234));
        assert!(!runner.config.include_children);
        assert_eq!(runner.config.cpu_threshold, Some(80.0));
        assert_eq!(runner.config.memory_threshold, Some(500));
    }

    #[tokio::test]
    async fn test_system_runner_stream() {
        use futures::StreamExt;
        use tokio::time::{timeout, Duration};

        // Create a runner that monitors the test process itself
        let current_pid = std::process::id();
        let mut runner = SystemRunner::new()
            .interval(1)
            .pid(current_pid)
            .add_analyzer(Box::new(crate::framework::analyzers::OutputAnalyzer::new()));

        match runner.run().await {
            Ok(mut stream) => {
                // Collect events for 3 seconds
                let result = timeout(Duration::from_secs(3), async {
                    let mut count = 0;
                    while let Some(event) = stream.next().await {
                        count += 1;
                        assert_eq!(event.source, "system");
                        assert_eq!(event.pid, current_pid);

                        // Verify payload structure
                        let payload = &event.data;
                        assert!(payload.get("cpu").is_some());
                        assert!(payload.get("memory").is_some());
                        assert!(payload.get("process").is_some());

                        if count >= 2 {
                            break;
                        }
                    }
                    count
                }).await;

                match result {
                    Ok(count) => assert!(count >= 2, "Should collect at least 2 events"),
                    Err(_) => panic!("Timeout waiting for events"),
                }
            }
            Err(e) => panic!("Failed to run SystemRunner: {}", e),
        }
    }
}
