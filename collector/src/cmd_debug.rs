// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::analyzers::{SSEProcessor, TimestampNormalizer};
use crate::binary_extractor::BinaryExtractor;
use crate::binary_resolver::resolve_container_binary_arg;
use crate::cmd_trace::{build_stdio_args, configure_ssl_runner, run_debug_runner};
use crate::output::separator_line;
use crate::runners::{BinaryRunner, ProcessRunner, Runner, RunnerError, SystemRunner};

/// Show raw SSL events as JSON with optional chunk merging and HTTP parsing
pub(crate) async fn run_raw_ssl(
    binary_extractor: &BinaryExtractor,
    enable_chunk_merger: bool,
    enable_http_parser: bool,
    include_raw_data: bool,
    http_filter_patterns: &[String],
    disable_auth_removal: bool,
    ssl_filter_patterns: &[String],
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
    binary_path: Option<&str>,
    args: &[String],
) -> Result<(), RunnerError> {
    println!("Raw SSL Events\n{}", separator_line());

    let mut ssl_runner = BinaryRunner::ssl(binary_extractor.get_sslsniff_path());

    let container_resolved =
        resolve_container_binary_arg(binary_path).map_err(RunnerError::from)?;
    let binary_path = container_resolved
        .as_ref()
        .map(|(_, path)| path.as_str())
        .or(binary_path);

    let mut final_args = Vec::new();
    if let Some(path) = binary_path {
        final_args.push("--binary-path".to_string());
        final_args.push(path.to_string());
    }
    final_args.extend_from_slice(args);
    if !final_args.is_empty() {
        ssl_runner = ssl_runner.with_args(&final_args);
    }

    ssl_runner = configure_ssl_runner(
        ssl_runner,
        ssl_filter_patterns,
        enable_http_parser,
        include_raw_data,
        http_filter_patterns,
        disable_auth_removal,
    );

    if enable_http_parser {
        println!(
            "Starting SSL event stream with SSE processing + HTTP parsing (press Ctrl+C to stop):"
        );
    } else if enable_chunk_merger {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
        println!("Starting SSL event stream with SSE processing (press Ctrl+C to stop):");
    } else {
        println!("Starting SSL event stream with raw JSON output (press Ctrl+C to stop):");
    }

    run_debug_runner(ssl_runner, quiet, enable_server, server_listen, server_port).await
}

/// Show raw process events as JSON
pub(crate) async fn run_raw_process(
    binary_extractor: &BinaryExtractor,
    cgroup_filter: Option<&str>,
    cgroup_filter_children: bool,
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
    args: &Vec<String>,
) -> Result<(), RunnerError> {
    println!("Raw Process Events\n{}", separator_line());

    let mut process_runner =
        ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());
    if !args.is_empty() {
        process_runner = process_runner.with_args(args);
    }
    process_runner = process_runner.with_cgroup_filter(cgroup_filter, cgroup_filter_children);
    process_runner = process_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    println!("Starting process event stream with raw JSON output (press Ctrl+C to stop):");
    run_debug_runner(
        process_runner,
        quiet,
        enable_server,
        server_listen,
        server_port,
    )
    .await
}

/// Show raw stdio events as JSON
pub(crate) async fn run_raw_stdio(
    binary_extractor: &BinaryExtractor,
    pid: u32,
    uid: Option<u32>,
    comm: Option<&str>,
    all_fds: bool,
    max_bytes: u32,
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
) -> Result<(), RunnerError> {
    println!("Raw Stdio Events\n{}", separator_line());

    let stdio_args = build_stdio_args(pid, uid, comm, all_fds, max_bytes);
    let stdio_runner = BinaryRunner::stdio(binary_extractor.get_stdiocap_path()?)
        .with_args(&stdio_args)
        .add_analyzer(Box::new(TimestampNormalizer::new()));

    println!(
        "Starting stdio event stream for PID {} (press Ctrl+C to stop):",
        pid
    );
    run_debug_runner(
        stdio_runner,
        quiet,
        enable_server,
        server_listen,
        server_port,
    )
    .await
}

/// Monitor system resources (CPU and memory)
pub(crate) async fn run_system(
    interval: u64,
    pid: Option<u32>,
    comm: Option<&str>,
    include_children: bool,
    cpu_threshold: Option<f64>,
    memory_threshold: Option<u64>,
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
) -> Result<(), RunnerError> {
    println!("System Resource Monitoring\n{}", separator_line());

    let mut system_runner = SystemRunner::new().interval(interval);

    if let Some(pid) = pid {
        system_runner = system_runner.pid(pid);
        println!("Monitoring PID: {}", pid);
    } else if let Some(comm) = comm {
        system_runner = system_runner.comm(comm);
        println!("Monitoring process: {}", comm);
    } else {
        println!("Monitoring system-wide resources");
    }

    system_runner = system_runner.include_children(include_children);
    if let Some(threshold) = cpu_threshold {
        system_runner = system_runner.cpu_threshold(threshold);
        println!("CPU alert threshold: {}%", threshold);
    }
    if let Some(threshold) = memory_threshold {
        system_runner = system_runner.memory_threshold(threshold);
        println!("Memory alert threshold: {} MB", threshold);
    }

    println!("Interval: {}s", interval);
    println!("Include children: {}", include_children);
    println!("{}", separator_line());
    println!("Starting system monitoring (press Ctrl+C to stop):");

    system_runner = system_runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    run_debug_runner(
        system_runner,
        quiet,
        enable_server,
        server_listen,
        server_port,
    )
    .await
}
