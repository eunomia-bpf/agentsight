// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use clap::{Args, Subcommand};

use crate::analyzers::{SSEProcessor, TimestampNormalizer};
use crate::binary_extractor::BinaryExtractor;
use crate::binary_resolver::resolve_container_binary_arg;
use crate::cli_db::configured_db_path;
use crate::cmd_trace::{
    OtelConfig, TraceConfig, build_stdio_args, configure_ssl_runner, run_debug_runner, run_trace,
};
use crate::output::separator_line;
use crate::runners::{BinaryRunner, ProcessRunner, Runner, RunnerError, SystemRunner};

#[derive(Args)]
pub(crate) struct DebugCli {
    #[command(subcommand)]
    command: DebugCommand,
}

#[derive(Subcommand)]
enum DebugCommand {
    /// Print SSL traffic as raw/analyzed JSON.
    Ssl {
        #[arg(long)] sse_merge: bool,
        #[arg(long)] http_parser: bool,
        #[arg(long)] http_raw_data: bool,
        #[arg(long)] http_filter: Vec<String>,
        #[arg(long)] disable_auth_removal: bool,
        #[arg(long)] ssl_filter: Vec<String>,
        #[arg(short, long)] quiet: bool,
        #[arg(long)] server: bool,
        #[arg(long, default_value_t = 7395)] server_port: u16,
        #[arg(long)] binary_path: Option<String>,
        #[arg(last = true)] args: Vec<String>,
    },
    /// Print process runner events.
    Process {
        #[arg(short, long)] quiet: bool,
        #[arg(long)] server: bool,
        #[arg(long, default_value_t = 7395)] server_port: u16,
        #[arg(last = true)] args: Vec<String>,
    },
    /// Print local stdio payloads from a target process.
    Stdio {
        #[arg(short = 'p', long)] pid: u32,
        #[arg(short = 'u', long)] uid: Option<u32>,
        #[arg(short = 'c', long)] comm: Option<String>,
        #[arg(long)] all_fds: bool,
        #[arg(long, default_value_t = 8192)] max_bytes: u32,
        #[arg(short, long)] quiet: bool,
        #[arg(long)] server: bool,
        #[arg(long, default_value_t = 7395)] server_port: u16,
    },
    /// Combined SSL, process, stdio, resource, storage, and OTLP tracing.
    Trace {
        #[arg(long, action = clap::ArgAction::Set, default_value_t = true)] ssl: bool,
        #[arg(long)] ssl_uid: Option<u32>,
        #[arg(long)] ssl_filter: Vec<String>,
        #[arg(long)] ssl_handshake: bool,
        #[arg(long, action = clap::ArgAction::Set, default_value_t = true)] ssl_http: bool,
        #[arg(long)] ssl_raw_data: bool,
        #[arg(long, action = clap::ArgAction::Set, default_value_t = true)] process: bool,
        #[arg(long, requires = "pid")] stdio: bool,
        #[arg(long)] stdio_uid: Option<u32>,
        #[arg(long)] stdio_comm: Option<String>,
        #[arg(long)] stdio_all_fds: bool,
        #[arg(long, default_value_t = 8192)] stdio_max_bytes: u32,
        #[arg(short = 'c', long)] comm: Option<String>,
        #[arg(short = 'p', long)] pid: Option<u32>,
        #[arg(long)] duration: Option<u32>,
        #[arg(long)] mode: Option<u32>,
        #[arg(long)] system: bool,
        #[arg(long, default_value_t = 2)] system_interval: u64,
        #[arg(long)] http_filter: Vec<String>,
        #[arg(long)] disable_auth_removal: bool,
        #[arg(long)] otel: bool,
        #[arg(long)] otel_endpoint: Option<String>,
        #[arg(long)] otel_capture_content: bool,
        #[arg(long)] binary_path: Option<String>,
        #[arg(long)] db: Option<String>,
        #[arg(short, long)] quiet: bool,
        #[arg(long)] server: bool,
        #[arg(long, default_value_t = 7395)] server_port: u16,
    },
    /// Monitor system resources (CPU and memory).
    System {
        #[arg(short = 'i', long, default_value_t = 2)] interval: u64,
        #[arg(short = 'p', long)] pid: Option<u32>,
        #[arg(short = 'c', long)] comm: Option<String>,
        #[arg(long)] no_children: bool,
        #[arg(long)] cpu_threshold: Option<f64>,
        #[arg(long)] memory_threshold: Option<u64>,
        #[arg(short, long)] quiet: bool,
        #[arg(long)] server: bool,
        #[arg(long, default_value_t = 7395)] server_port: u16,
    },
}

pub(crate) async fn run(
    cli: &DebugCli,
    binary_extractor: &BinaryExtractor,
    listen: &str,
) -> Result<(), RunnerError> {
    match &cli.command {
        DebugCommand::Ssl {
            sse_merge, http_parser, http_raw_data, http_filter, disable_auth_removal,
            ssl_filter, quiet, server, server_port, binary_path, args,
        } => run_raw_ssl(
            binary_extractor, *sse_merge, *http_parser, *http_raw_data, http_filter,
            *disable_auth_removal, ssl_filter, *quiet, *server, listen, *server_port,
            binary_path.as_deref(), args,
        ).await,
        DebugCommand::Process { quiet, server, server_port, args } =>
            run_raw_process(binary_extractor, *quiet, *server, listen, *server_port, args).await,
        DebugCommand::Stdio { pid, uid, comm, all_fds, max_bytes, quiet, server, server_port } =>
            run_raw_stdio(
                binary_extractor, *pid, *uid, comm.as_deref(), *all_fds, *max_bytes,
                *quiet, *server, listen, *server_port,
            ).await,
        DebugCommand::Trace {
            ssl, ssl_uid, ssl_filter, ssl_handshake, ssl_http, ssl_raw_data, process,
            stdio, stdio_uid, stdio_comm, stdio_all_fds, stdio_max_bytes, comm, pid,
            duration, mode, system, system_interval, http_filter, disable_auth_removal,
            otel, otel_endpoint, otel_capture_content, binary_path, db, quiet, server,
            server_port,
        } => run_trace(binary_extractor, TraceConfig {
            ssl: *ssl,
            pid: *pid,
            ssl_uid: *ssl_uid,
            comm: comm.clone(),
            ssl_filter: ssl_filter.clone(),
            ssl_handshake: *ssl_handshake,
            ssl_http: *ssl_http,
            ssl_raw_data: *ssl_raw_data,
            process: *process,
            stdio: *stdio,
            stdio_uid: *stdio_uid,
            stdio_comm: stdio_comm.clone(),
            stdio_all_fds: *stdio_all_fds,
            stdio_max_bytes: *stdio_max_bytes,
            duration: *duration,
            mode: *mode,
            system: *system,
            system_interval: *system_interval,
            http_filter: http_filter.clone(),
            disable_auth_removal: *disable_auth_removal,
            otel: otel.then(|| OtelConfig {
                endpoint: otel_endpoint.clone(),
                capture_content: *otel_capture_content,
            }),
            binary_path: binary_path.clone(),
            db_path: configured_db_path(db),
            quiet: *quiet,
            server: *server,
            server_listen: Some(listen.to_string()),
            server_port: *server_port,
            ..Default::default()
        }).await,
        DebugCommand::System {
            interval, pid, comm, no_children, cpu_threshold, memory_threshold,
            quiet, server, server_port,
        } => run_system(
            *interval, *pid, comm.as_deref(), !*no_children, *cpu_threshold,
            *memory_threshold, *quiet, *server, listen, *server_port,
        ).await,
    }
}

async fn run_raw_ssl(
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
    let resolved = resolve_container_binary_arg(binary_path).map_err(RunnerError::from)?;
    let binary_path = resolved.as_ref().map(|(_, path)| path.as_str()).or(binary_path);
    let mut final_args = Vec::new();
    if let Some(path) = binary_path {
        final_args.extend(["--binary-path".to_string(), path.to_string()]);
    }
    final_args.extend_from_slice(args);
    if !final_args.is_empty() { ssl_runner = ssl_runner.with_args(&final_args); }
    ssl_runner = configure_ssl_runner(
        ssl_runner, ssl_filter_patterns, enable_http_parser, include_raw_data,
        http_filter_patterns, disable_auth_removal,
    );
    if enable_http_parser {
        println!("Starting SSL event stream with SSE processing + HTTP parsing (press Ctrl+C to stop):");
    } else if enable_chunk_merger {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
        println!("Starting SSL event stream with SSE processing (press Ctrl+C to stop):");
    } else {
        println!("Starting SSL event stream with raw JSON output (press Ctrl+C to stop):");
    }
    run_debug_runner(ssl_runner, quiet, enable_server, server_listen, server_port).await
}

async fn run_raw_process(
    binary_extractor: &BinaryExtractor,
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
    args: &[String],
) -> Result<(), RunnerError> {
    println!("Raw Process Events\n{}", separator_line());
    let mut runner = ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());
    if !args.is_empty() { runner = runner.with_args(args); }
    runner = runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    println!("Starting process event stream with raw JSON output (press Ctrl+C to stop):");
    run_debug_runner(runner, quiet, enable_server, server_listen, server_port).await
}

async fn run_raw_stdio(
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
    let args = build_stdio_args(pid, uid, comm, all_fds, max_bytes);
    let runner = BinaryRunner::stdio(binary_extractor.get_stdiocap_path()?)
        .with_args(&args)
        .add_analyzer(Box::new(TimestampNormalizer::new()));
    println!("Starting stdio event stream for PID {pid} (press Ctrl+C to stop):");
    run_debug_runner(runner, quiet, enable_server, server_listen, server_port).await
}

async fn run_system(
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
    let mut runner = SystemRunner::new().interval(interval).include_children(include_children);
    if let Some(pid) = pid { runner = runner.pid(pid); println!("Monitoring PID: {pid}"); }
    else if let Some(comm) = comm { runner = runner.comm(comm); println!("Monitoring process: {comm}"); }
    else { println!("Monitoring system-wide resources"); }
    if let Some(value) = cpu_threshold { runner = runner.cpu_threshold(value); println!("CPU alert threshold: {value}%"); }
    if let Some(value) = memory_threshold { runner = runner.memory_threshold(value); println!("Memory alert threshold: {value} MB"); }
    println!("Interval: {interval}s\nInclude children: {include_children}\n{}", separator_line());
    println!("Starting system monitoring (press Ctrl+C to stop):");
    runner = runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    run_debug_runner(runner, quiet, enable_server, server_listen, server_port).await
}
