// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use clap::{Parser, Subcommand};
use futures::stream::StreamExt;
use std::sync::atomic::{AtomicBool, Ordering};
use tokio::signal;
use tokio::sync::broadcast;

mod framework;
mod server;

use framework::{
    binary_extractor::BinaryExtractor,
    runners::{SslRunner, StdioRunner, ProcessRunner, AgentRunner, SystemRunner, RunnerError, Runner},
    analyzers::{OutputAnalyzer, FileLogger, SSEProcessor, HTTPParser, HTTPFilter, AuthHeaderRemover, SSLFilter, TimestampNormalizer, print_global_http_filter_metrics, print_global_ssl_filter_metrics}
};

use server::WebServer;

static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);

fn convert_runner_error(e: RunnerError) -> Box<dyn std::error::Error + Send + Sync> {
    Box::new(std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))
}

async fn setup_signal_handler() {
    let mut sigint = signal::unix::signal(signal::unix::SignalKind::interrupt())
        .expect("Failed to install SIGINT handler");
    
    tokio::spawn(async move {
        sigint.recv().await;
        println!("\n\nReceived SIGINT, shutting down...");
        
        // Print HTTP filter metrics using the global function
        print_global_http_filter_metrics();
        
        // Print SSL filter metrics using the global function
        print_global_ssl_filter_metrics();
        
        SHUTDOWN_REQUESTED.store(true, Ordering::Relaxed);
        std::process::exit(0);
    });
}

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Analyze SSL traffic with raw JSON output
    Ssl {
        /// Enable SSE processing for SSL traffic
        #[arg(long)]
        sse_merge: bool,
        /// Enable HTTP parsing (automatically enables SSE merge first)
        #[arg(long)]
        http_parser: bool,
        /// Include raw SSL data in HTTP parser events
        #[arg(long)]
        http_raw_data: bool,
        /// HTTP filter patterns to exclude events (can be used multiple times)
        #[arg(long)]
        http_filter: Vec<String>,
        /// Disable authorization header removal from HTTP traffic
        #[arg(long)]
        disable_auth_removal: bool,
        /// SSL filter patterns to exclude events (can be used multiple times)
        #[arg(long)]
        ssl_filter: Vec<String>,
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Enable log rotation
        #[arg(long)]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Log file to serve via API (used with --server)
        #[arg(long, default_value = "ssl.log")]
        log_file: String,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// Additional arguments to pass to the SSL binary
        #[arg(last = true)]
        args: Vec<String>,
    },
    /// Test process runner with embedded binary
    Process {
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Enable log rotation
        #[arg(long)]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Log file to serve via API (used with --server)
        #[arg(long, default_value = "process.log")]
        log_file: String,
        /// Additional arguments to pass to the process binary
        #[arg(last = true)]
        args: Vec<String>,
    },
    /// Capture local stdio payloads from a target process
    Stdio {
        /// Target PID (required)
        #[arg(short = 'p', long)]
        pid: u32,
        /// Filter by UID
        #[arg(short = 'u', long)]
        uid: Option<u32>,
        /// Filter by command name
        #[arg(short = 'c', long)]
        comm: Option<String>,
        /// Capture all FDs instead of only stdin/stdout/stderr
        #[arg(long)]
        all_fds: bool,
        /// Maximum bytes captured per event
        #[arg(long, default_value = "8192")]
        max_bytes: u32,
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Enable log rotation
        #[arg(long)]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Log file to serve via API (used with --server)
        #[arg(long, default_value = "stdio.log")]
        log_file: String,
    },
    /// Combined SSL and Process monitoring with configurable options
    Trace {
        /// Enable SSL monitoring
        #[arg(long, action = clap::ArgAction::Set, default_value = "true")]
        ssl: bool,
        /// SSL filter by UID
        #[arg(long)]
        ssl_uid: Option<u32>,
        /// SSL filter patterns (for analyzer-level filtering)
        #[arg(long)]
        ssl_filter: Vec<String>,
        /// Show SSL handshake events
        #[arg(long)]
        ssl_handshake: bool,
        /// Enable HTTP parsing for SSL
        #[arg(long, action = clap::ArgAction::Set, default_value = "true")]
        ssl_http: bool,
        /// Include raw SSL data in HTTP parser events
        #[arg(long)]
        ssl_raw_data: bool,

        /// Enable process monitoring
        #[arg(long, action = clap::ArgAction::Set, default_value = "true")]
        process: bool,
        /// Enable stdio payload monitoring (requires --pid)
        #[arg(long, requires = "pid")]
        stdio: bool,
        /// Stdio filter by UID
        #[arg(long)]
        stdio_uid: Option<u32>,
        /// Stdio filter by command name
        #[arg(long)]
        stdio_comm: Option<String>,
        /// Capture all FDs for stdio monitoring instead of only 0/1/2
        #[arg(long)]
        stdio_all_fds: bool,
        /// Maximum bytes captured per stdio event
        #[arg(long, default_value = "8192")]
        stdio_max_bytes: u32,
        /// Process command filter (comma-separated list)
        #[arg(short = 'c', long)]
        comm: Option<String>,
        /// Process PID filter
        #[arg(short = 'p', long)]
        pid: Option<u32>,
        /// Process duration filter (minimum duration in ms)
        #[arg(long)]
        duration: Option<u32>,
        /// Process filtering mode (0=all, 1=proc, 2=filter)
        #[arg(long)]
        mode: Option<u32>,

        /// Enable system resource monitoring (CPU and memory)
        #[arg(long)]
        system: bool,
        /// System monitoring interval in seconds
        #[arg(long, default_value = "2")]
        system_interval: u64,

        /// HTTP filters (applied to SSL runner after HTTP parsing)
        #[arg(long)]
        http_filter: Vec<String>,
        /// Disable authorization header removal from HTTP traffic
        #[arg(long)]
        disable_auth_removal: bool,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// Log file for output and server
        #[arg(short = 'o', long, default_value = "trace.log")]
        log_file: String,
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Enable log rotation
        #[arg(long)]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
    },
    /// Record agent activity with optimized filters and settings
    /// Equivalent to: trace -c claude --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\\r\\n\\r\\n|data.type=binary" -q --server-port 7395 --server -o record.log
    Record {
        /// Process command filter (defaults to "claude")
        #[arg(short = 'c', long)]
        comm: String,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// Log file for output and server
        #[arg(short = 'o', long, default_value = "record.log")]
        log_file: String,
        /// Enable log rotation
        #[arg(long, default_value = "true")]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Server port (used with --server, always enabled)
        #[arg(long, default_value = "7395")]
        server_port: u16,
    },
    /// Launch a command and automatically discover + trace it (zero config).
    /// Example: agentsight exec -- claude     (or)  agentsight exec -- python my_agent.py
    Exec {
        /// Override the auto-discovered SSL binary path (rarely needed)
        #[arg(long)]
        binary_path: Option<String>,
        /// Log file for output and server
        #[arg(short = 'o', long, default_value = "record.log")]
        log_file: String,
        /// Disable log rotation
        #[arg(long, default_value = "true")]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Disable the web server (enabled by default on --server-port)
        #[arg(long)]
        no_server: bool,
        /// Server port for the web UI
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// The command (and its arguments) to launch and trace
        #[arg(last = true, required = true)]
        command: Vec<String>,
    },
    /// Monitor system resources (CPU and memory)
    System {
        /// Monitoring interval in seconds
        #[arg(short = 'i', long, default_value = "2")]
        interval: u64,
        /// Process PID to monitor
        #[arg(short = 'p', long)]
        pid: Option<u32>,
        /// Process command name to monitor
        #[arg(short = 'c', long)]
        comm: Option<String>,
        /// Exclude children processes from aggregation
        #[arg(long)]
        no_children: bool,
        /// CPU usage threshold for alerts (%)
        #[arg(long)]
        cpu_threshold: Option<f64>,
        /// Memory usage threshold for alerts (MB)
        #[arg(long)]
        memory_threshold: Option<u64>,
        /// Log file for output and server
        #[arg(short = 'o', long, default_value = "system.log")]
        log_file: String,
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Enable log rotation
        #[arg(long)]
        rotate_logs: bool,
        /// Maximum log file size in MB (used with --rotate-logs)
        #[arg(long, default_value = "10")]
        max_log_size: u64,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Initialize env_logger with default log level of info
    env_logger::Builder::from_default_env()
        .filter_level(log::LevelFilter::Info)
        .init();
    
    let cli = Cli::parse();
    
    // Setup signal handler for graceful shutdown
    setup_signal_handler().await;
    
    // Create BinaryExtractor with embedded binaries
    let binary_extractor = BinaryExtractor::new().await?;
    
    match &cli.command {
        Commands::Ssl { sse_merge, http_parser, http_raw_data, http_filter, disable_auth_removal, ssl_filter, quiet, rotate_logs, max_log_size, server, server_port, log_file, binary_path, args } => run_raw_ssl(&binary_extractor, *sse_merge, *http_parser, *http_raw_data, http_filter, *disable_auth_removal, ssl_filter, *quiet, *rotate_logs, *max_log_size, *server, *server_port, log_file, binary_path.as_deref(), args).await.map_err(convert_runner_error)?,
        Commands::Process { quiet, rotate_logs, max_log_size, server, server_port, log_file, args } => run_raw_process(&binary_extractor, *quiet, *rotate_logs, *max_log_size, *server, *server_port, log_file, args).await.map_err(convert_runner_error)?,
        Commands::Stdio { pid, uid, comm, all_fds, max_bytes, quiet, rotate_logs, max_log_size, server, server_port, log_file } => run_raw_stdio(&binary_extractor, *pid, *uid, comm.as_deref(), *all_fds, *max_bytes, *quiet, *rotate_logs, *max_log_size, *server, *server_port, log_file).await.map_err(convert_runner_error)?,
        Commands::Trace { ssl, ssl_uid, pid, comm, ssl_filter, ssl_handshake, ssl_http, ssl_raw_data, process, stdio, stdio_uid, stdio_comm, stdio_all_fds, stdio_max_bytes, duration, mode, system, system_interval, http_filter, disable_auth_removal, binary_path, log_file, quiet, rotate_logs, max_log_size, server, server_port } => run_trace(&binary_extractor, *ssl, *pid, *ssl_uid, comm.as_deref(), ssl_filter, *ssl_handshake, *ssl_http, *ssl_raw_data, *process, *stdio, *stdio_uid, stdio_comm.as_deref(), *stdio_all_fds, *stdio_max_bytes, *duration, *mode, *system, *system_interval, http_filter, *disable_auth_removal, binary_path.as_deref(), log_file, *quiet, *rotate_logs, *max_log_size, *server, *server_port).await.map_err(convert_runner_error)?,
        Commands::Record { comm, binary_path, log_file, rotate_logs, max_log_size, server_port } => {
            // Predefined filter patterns optimized for agent monitoring
            let http_filter_patterns = vec![
                "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=".to_string(),
            ];
            let ssl_filter_patterns = vec![
                "data=0\\r\\n\\r\\n | data.type=binary".to_string(),
            ];

            // Enable system monitoring by default for record command
            run_trace(&binary_extractor, true, None, None, Some(comm), &ssl_filter_patterns, false, true, false, true, false, None, None, false, 8192, None, None, true, 2, &http_filter_patterns, false, binary_path.as_deref(), log_file, true, *rotate_logs, *max_log_size, true, *server_port).await.map_err(convert_runner_error)?
        },
        Commands::Exec { binary_path, log_file, rotate_logs, max_log_size, no_server, server_port, command } => {
            run_exec(&binary_extractor, command, binary_path.as_deref(), log_file, *rotate_logs, *max_log_size, !*no_server, *server_port).await.map_err(convert_runner_error)?
        },
        Commands::System { interval, pid, comm, no_children, cpu_threshold, memory_threshold, log_file, quiet, rotate_logs, max_log_size, server, server_port } => run_system(*interval, *pid, comm.as_deref(), !*no_children, *cpu_threshold, *memory_threshold, log_file, *quiet, *rotate_logs, *max_log_size, *server, *server_port).await.map_err(convert_runner_error)?,
    }
    
    Ok(())
}


/// Show raw SSL events as JSON with optional chunk merging and HTTP parsing
async fn run_raw_ssl(binary_extractor: &BinaryExtractor, enable_chunk_merger: bool, enable_http_parser: bool, include_raw_data: bool, http_filter_patterns: &Vec<String>, disable_auth_removal: bool, ssl_filter_patterns: &Vec<String>, quiet: bool, rotate_logs: bool, max_log_size: u64, enable_server: bool, server_port: u16, log_file: &str, binary_path: Option<&str>, args: &Vec<String>) -> Result<(), RunnerError> {
    println!("Raw SSL Events");
    println!("{}", "=".repeat(60));
    
    let mut ssl_runner = SslRunner::from_binary_extractor(binary_extractor.get_sslsniff_path());

    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);

    // Build arguments list with binary_path if provided
    let mut final_args = Vec::new();
    if let Some(path) = binary_path {
        final_args.push("--binary-path".to_string());
        final_args.push(path.to_string());
    }
    final_args.extend_from_slice(args);

    // Add all arguments if we have any
    if !final_args.is_empty() {
        ssl_runner = ssl_runner.with_args(&final_args);
    }

    // Add TimestampNormalizer first to convert nanoseconds since boot to milliseconds since epoch
    ssl_runner = ssl_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    // Add SSL filter if patterns are provided
    if !ssl_filter_patterns.is_empty() {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSLFilter::with_patterns(ssl_filter_patterns.clone())));
    }
    
    // Add analyzers based on flags - when HTTP parser is enabled, always enable SSE merge first
    if enable_http_parser {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
        
        // Create HTTP parser with appropriate configuration
        let http_parser = if include_raw_data {
            HTTPParser::new()
        } else {
            HTTPParser::new().disable_raw_data()
        };
        ssl_runner = ssl_runner.add_analyzer(Box::new(http_parser));
        
        // Add HTTP filter if patterns are provided
        if !http_filter_patterns.is_empty() {
            ssl_runner = ssl_runner.add_analyzer(Box::new(HTTPFilter::with_patterns(http_filter_patterns.clone())));
        }
        
        // Add authorization header remover by default (unless disabled)
        if !disable_auth_removal {
            ssl_runner = ssl_runner.add_analyzer(Box::new(AuthHeaderRemover::new()));
        }
        
        let raw_data_info = if include_raw_data { " (with raw data)" } else { "" };
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() { " with SSL filtering," } else { "" };
        let http_filter_info = if !http_filter_patterns.is_empty() { " and HTTP filtering" } else { "" };
        println!("Starting SSL event stream{} with SSE processing, HTTP parsing{}{} enabled (press Ctrl+C to stop):", ssl_filter_info, raw_data_info, http_filter_info);
    } else if enable_chunk_merger {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() { " with SSL filtering and" } else { " with" };
        println!("Starting SSL event stream{} SSE processing enabled (press Ctrl+C to stop):", ssl_filter_info);
    } else {
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() { " with SSL filtering and" } else { " with" };
        println!("Starting SSL event stream{} raw JSON output (press Ctrl+C to stop):", ssl_filter_info);
    }
    
    ssl_runner = ssl_runner
        .add_analyzer(Box::new(
            if rotate_logs {
                FileLogger::with_max_size(log_file, max_log_size).unwrap()
            } else {
                FileLogger::new(log_file).unwrap()
            }
        ));
    
    if !quiet {
        ssl_runner = ssl_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }
    
    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, Some(log_file), event_sender.clone()).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = ssl_runner.run().await?;
    
    // Consume the stream to actually process events
    while let Some(event) = stream.next().await {
        // Forward events to web server if enabled
        if enable_server {
            let _ = event_sender.send(event);
        }
    }
    
    Ok(())
}

/// Show raw process events as JSON
async fn run_raw_process(binary_extractor: &BinaryExtractor, quiet: bool, rotate_logs: bool, max_log_size: u64, enable_server: bool, server_port: u16, log_file: &str, args: &Vec<String>) -> Result<(), RunnerError> {
    println!("Raw Process Events");
    println!("{}", "=".repeat(60));
    
    let mut process_runner = ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());

    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);

    // Add additional arguments if provided
    if !args.is_empty() {
        process_runner = process_runner.with_args(args);
    }

    // Add TimestampNormalizer first to convert nanoseconds since boot to milliseconds since epoch
    process_runner = process_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    if !quiet {
        process_runner = process_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    process_runner = process_runner
        .add_analyzer(Box::new(
            if rotate_logs {
                FileLogger::with_max_size(log_file, max_log_size).unwrap()
            } else {
                FileLogger::new(log_file).unwrap()
            }
        ));

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, Some(log_file), event_sender.clone()).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;
    
    println!("Starting process event stream with raw JSON output (press Ctrl+C to stop):");
    let mut stream = process_runner.run().await?;

    // Consume the stream to actually process events
    while let Some(event) = stream.next().await {
        // Forward events to web server if enabled
        if enable_server {
            let _ = event_sender.send(event);
        }
    }

    Ok(())
}

fn build_stdio_args(pid: u32, uid: Option<u32>, comm: Option<&str>, all_fds: bool, max_bytes: u32) -> Vec<String> {
    let mut args = vec!["-p".to_string(), pid.to_string()];

    if let Some(uid_filter) = uid {
        args.extend(["-u".to_string(), uid_filter.to_string()]);
    }
    if let Some(comm_filter) = comm {
        args.extend(["-c".to_string(), comm_filter.to_string()]);
    }
    if all_fds {
        args.push("--all-fds".to_string());
    }
    args.extend(["--max-bytes".to_string(), max_bytes.to_string()]);

    args
}

/// Show raw stdio events as JSON
async fn run_raw_stdio(binary_extractor: &BinaryExtractor, pid: u32, uid: Option<u32>, comm: Option<&str>, all_fds: bool, max_bytes: u32, quiet: bool, rotate_logs: bool, max_log_size: u64, enable_server: bool, server_port: u16, log_file: &str) -> Result<(), RunnerError> {
    println!("Raw Stdio Events");
    println!("{}", "=".repeat(60));

    let mut stdio_runner = StdioRunner::from_binary_extractor(binary_extractor.get_stdiocap_path()?);

    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);

    let stdio_args = build_stdio_args(pid, uid, comm, all_fds, max_bytes);
    stdio_runner = stdio_runner.with_args(&stdio_args);

    // Add TimestampNormalizer first to convert nanoseconds since boot to milliseconds since epoch
    stdio_runner = stdio_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    if !quiet {
        stdio_runner = stdio_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    stdio_runner = stdio_runner
        .add_analyzer(Box::new(
            if rotate_logs {
                FileLogger::with_max_size(log_file, max_log_size).unwrap()
            } else {
                FileLogger::new(log_file).unwrap()
            }
        ));

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, Some(log_file), event_sender.clone()).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    println!("Starting stdio event stream for PID {} (press Ctrl+C to stop):", pid);
    let mut stream = stdio_runner.run().await?;

    while let Some(event) = stream.next().await {
        if enable_server {
            let _ = event_sender.send(event);
        }
    }

    Ok(())
}

/// Build a configured AgentRunner from trace options without running it.
/// Shared by `run_trace` and `run_exec` so they configure runners identically.
fn build_trace_agent(
    binary_extractor: &BinaryExtractor,
    name: &str,
    ssl_enabled: bool,
    pid: Option<u32>,
    ssl_uid: Option<u32>,
    comm: Option<&str>,
    ssl_filter: &[String],
    ssl_handshake: bool,
    ssl_http: bool,
    ssl_raw_data: bool,
    process_enabled: bool,
    stdio_enabled: bool,
    stdio_uid: Option<u32>,
    stdio_comm: Option<&str>,
    stdio_all_fds: bool,
    stdio_max_bytes: u32,
    duration: Option<u32>,
    mode: Option<u32>,
    system_enabled: bool,
    system_interval: u64,
    http_filter: &[String],
    disable_auth_removal: bool,
    binary_path: Option<&str>,
    log_file: &str,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
) -> Result<AgentRunner, RunnerError> {
    let mut agent = AgentRunner::new(name);

    // Add SSL runner if enabled
    if ssl_enabled {
        let mut ssl_runner = SslRunner::from_binary_extractor(binary_extractor.get_sslsniff_path());

        // Configure SSL runner arguments (sslsniff supports -p, -u, -c, -h, -v, --binary-path)
        let mut ssl_args = Vec::new();
        if let Some(pid_filter) = pid {
            ssl_args.extend(["-p".to_string(), pid_filter.to_string()]);
        }
        if let Some(uid_filter) = ssl_uid {
            ssl_args.extend(["-u".to_string(), uid_filter.to_string()]);
        }
        // Note: when --binary-path is specified, we skip the --comm filter for sslsniff
        // because SSL traffic comes from "HTTP Client" thread (not the process name).
        // bpf_get_current_comm() returns thread name, so -c <process-name> would filter
        // out all SSL traffic. Instead, --binary-path alone provides sufficient targeting.
        if binary_path.is_none() {
            if let Some(comm_filter) = comm {
                ssl_args.extend(["-c".to_string(), comm_filter.to_string()]);
            }
        }
        if ssl_handshake {
            ssl_args.push("--handshake".to_string());
        }
        if let Some(path) = binary_path {
            ssl_args.extend(["--binary-path".to_string(), path.to_string()]);
        }
        if !ssl_args.is_empty() {
            ssl_runner = ssl_runner.with_args(&ssl_args);
        }

        // Add TimestampNormalizer first
        ssl_runner = ssl_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        // Add SSL-specific analyzers
        if !ssl_filter.is_empty() {
            ssl_runner = ssl_runner.add_analyzer(Box::new(SSLFilter::with_patterns(ssl_filter.to_vec())));
        }
        
        if ssl_http {
            ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
            
            let http_parser = if ssl_raw_data {
                HTTPParser::new()
            } else {
                HTTPParser::new().disable_raw_data()
            };
            ssl_runner = ssl_runner.add_analyzer(Box::new(http_parser));
            
            // Add HTTP filter to SSL runner if patterns are provided
            if !http_filter.is_empty() {
                ssl_runner = ssl_runner.add_analyzer(Box::new(HTTPFilter::with_patterns(http_filter.to_vec())));
            }
            
            // Add authorization header remover by default (unless disabled)
            if !disable_auth_removal {
                ssl_runner = ssl_runner.add_analyzer(Box::new(AuthHeaderRemover::new()));
            }
        }
        
        agent = agent.add_runner(Box::new(ssl_runner));
        let http_filter_info = if ssl_http && !http_filter.is_empty() { 
            format!(" with {} HTTP filter patterns", http_filter.len()) 
        } else { 
            String::new() 
        };
        println!("✓ SSL monitoring enabled{}", http_filter_info);
    }

    // Add stdio runner if enabled
    if stdio_enabled {
        let pid_filter = pid.ok_or_else(|| RunnerError::from("stdio capture currently requires --pid"))?;
        let mut stdio_runner = StdioRunner::from_binary_extractor(binary_extractor.get_stdiocap_path()?);
        let stdio_args = build_stdio_args(pid_filter, stdio_uid, stdio_comm, stdio_all_fds, stdio_max_bytes);

        stdio_runner = stdio_runner.with_args(&stdio_args);
        stdio_runner = stdio_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(stdio_runner));
        println!("✓ Stdio monitoring enabled for PID {}", pid_filter);
    }
    
    // Add process runner if enabled
    if process_enabled {
        let mut process_runner = ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());

        // Configure process runner arguments (process supports -c, -d, -m, -v)
        let mut process_args = Vec::new();
        if let Some(comm_filter) = comm {
            process_args.extend(["-c".to_string(), comm_filter.to_string()]);
        }
        if let Some(duration_filter) = duration {
            process_args.extend(["-d".to_string(), duration_filter.to_string()]);
        }
        if let Some(mode_filter) = mode {
            process_args.extend(["-m".to_string(), mode_filter.to_string()]);
        }
        if !process_args.is_empty() {
            process_runner = process_runner.with_args(&process_args);
        }

        // Add TimestampNormalizer first
        process_runner = process_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(process_runner));
        println!("✓ Process monitoring enabled");
    }
    
    // Add system resource runner if enabled
    if system_enabled {
        let mut system_runner = SystemRunner::new()
            .interval(system_interval);

        // Use same comm filter as other runners if provided
        if let Some(comm_filter) = comm {
            system_runner = system_runner.comm(comm_filter);
        }

        // Use same pid filter if provided
        if let Some(pid_filter) = pid {
            system_runner = system_runner.pid(pid_filter);
        }

        // Add TimestampNormalizer first
        system_runner = system_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(system_runner));
        println!("✓ System monitoring enabled (interval: {}s)", system_interval);
    }

    // Ensure at least one runner is enabled
    if !ssl_enabled && !process_enabled && !stdio_enabled && !system_enabled {
        return Err("At least one monitoring type must be enabled (--ssl, --process, --stdio, or --system)".into());
    }
    
    // Add global analyzers (HTTP filter is now added to SSL runner instead)

    agent = agent.add_global_analyzer(Box::new(
        if rotate_logs {
            FileLogger::with_max_size(log_file, max_log_size).unwrap()
        } else {
            FileLogger::new(log_file).unwrap()
        }
    ));
    println!("✓ Logging to file: {}", log_file);
    
    if !quiet {
        agent = agent.add_global_analyzer(Box::new(OutputAnalyzer::new()));
        println!("✓ Console output enabled");
    }

    Ok(agent)
}

/// Trace monitoring with configurable runners and analyzers
async fn run_trace(
    binary_extractor: &BinaryExtractor,
    ssl_enabled: bool,
    pid: Option<u32>,
    ssl_uid: Option<u32>,
    comm: Option<&str>,
    ssl_filter: &[String],
    ssl_handshake: bool,
    ssl_http: bool,
    ssl_raw_data: bool,
    process_enabled: bool,
    stdio_enabled: bool,
    stdio_uid: Option<u32>,
    stdio_comm: Option<&str>,
    stdio_all_fds: bool,
    stdio_max_bytes: u32,
    duration: Option<u32>,
    mode: Option<u32>,
    system_enabled: bool,
    system_interval: u64,
    http_filter: &[String],
    disable_auth_removal: bool,
    binary_path: Option<&str>,
    log_file: &str,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
) -> Result<(), RunnerError> {
    println!("Trace Monitoring");
    println!("{}", "=".repeat(60));

    // When the user enabled SSL but didn't pin a --binary-path, try to discover
    // one from --comm. This fixes the common "record -c node" case: Node (and
    // gemini-cli, which runs on Node) statically links OpenSSL, so there is no
    // system libssl.so to hook. Only adopt the resolved binary if it actually
    // embeds SSL, so dynamically-linked runtimes like Python are left to
    // sslsniff's system-libssl path with comm filtering intact.
    let auto_resolved: Option<String> = if ssl_enabled && binary_path.is_none() {
        comm.filter(|c| !c.contains(','))
            .and_then(|c| resolve_binary_path(c).ok())
            .filter(|p| binary_embeds_ssl(p))
            .map(|p| {
                println!("✓ Auto-discovered statically-linked SSL binary for --comm '{}': {}",
                         comm.unwrap_or(""), p);
                p
            })
    } else {
        None
    };
    let binary_path = binary_path.or(auto_resolved.as_deref());

    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);

    let mut agent = build_trace_agent(
        binary_extractor, "trace", ssl_enabled, pid, ssl_uid, comm, ssl_filter,
        ssl_handshake, ssl_http, ssl_raw_data, process_enabled, stdio_enabled,
        stdio_uid, stdio_comm, stdio_all_fds, stdio_max_bytes, duration, mode,
        system_enabled, system_interval, http_filter, disable_auth_removal,
        binary_path, log_file, quiet, rotate_logs, max_log_size,
    )?;

    println!("{}", "=".repeat(60));
    println!("Starting flexible trace monitoring with {} runners and {} global analyzers...",
             agent.runner_count(), agent.analyzer_count());
    println!("Press Ctrl+C to stop");

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, Some(log_file), event_sender.clone()).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = agent.run().await?;

    // Consume the stream to actually process events
    while let Some(event) = stream.next().await {
        // Forward events to web server if enabled
        if enable_server {
            let _ = event_sender.send(event);
        }
    }

    Ok(())
}


/// Resolve a command name/path to the real ELF binary that should be passed
/// to sslsniff as `--binary-path`.
///
/// Handles three cases automatically:
///   1. A command on `$PATH` (e.g. `claude`, `node`) -> located via PATH search.
///   2. A symlink (e.g. `~/.local/bin/claude` -> `.../versions/2.1.150`) -> followed.
///   3. A shebang wrapper script (`#!/usr/bin/env node`) -> the interpreter ELF.
///
/// Returns the canonical path of the underlying ELF executable, or an error
/// describing why discovery failed.
fn resolve_binary_path(command: &str) -> Result<String, String> {
    // Limit shebang chasing so a pathological wrapper chain cannot loop forever.
    resolve_binary_path_inner(command, 0)
}

fn resolve_binary_path_inner(command: &str, depth: u8) -> Result<String, String> {
    if depth > 5 {
        return Err(format!("too many nested shebang wrappers resolving '{}'", command));
    }

    // 1. Locate the file: an explicit path is used as-is, otherwise search $PATH.
    let candidate = if command.contains('/') {
        std::path::PathBuf::from(command)
    } else {
        find_in_path(command)
            .ok_or_else(|| format!("'{}' not found in $PATH", command))?
    };

    // 2. Follow symlinks to the real file (e.g. claude -> versions/2.1.150).
    let resolved = std::fs::canonicalize(&candidate)
        .map_err(|e| format!("cannot resolve '{}': {}", candidate.display(), e))?;

    // 3. Inspect the file header: ELF magic vs. shebang.
    let mut header = [0u8; 256];
    let n = {
        use std::io::Read;
        let mut f = std::fs::File::open(&resolved)
            .map_err(|e| format!("cannot open '{}': {}", resolved.display(), e))?;
        f.read(&mut header).map_err(|e| format!("cannot read '{}': {}", resolved.display(), e))?
    };
    let header = &header[..n];

    if header.starts_with(b"\x7fELF") {
        return Ok(resolved.to_string_lossy().into_owned());
    }

    if header.starts_with(b"#!") {
        // Parse the shebang line: `#!/usr/bin/env node` or `#!/usr/bin/python3`.
        let line_end = header.iter().position(|&b| b == b'\n').unwrap_or(header.len());
        let line = String::from_utf8_lossy(&header[2..line_end]);
        let mut parts = line.split_whitespace();
        let interp = parts.next()
            .ok_or_else(|| format!("'{}' has an empty shebang", resolved.display()))?;
        // `/usr/bin/env foo` -> resolve `foo` on PATH instead of `env` itself.
        let next = if interp.ends_with("/env") || interp == "env" {
            parts.next().ok_or_else(|| format!("'{}' uses env with no interpreter", resolved.display()))?
        } else {
            interp
        };
        return resolve_binary_path_inner(next, depth + 1);
    }

    Err(format!(
        "'{}' is neither an ELF binary nor a shebang script; specify --binary-path explicitly",
        resolved.display()
    ))
}

/// Minimal `which`: find an executable file named `cmd` in the `$PATH` dirs.
///
/// When invoked under `sudo`, the inherited `$PATH` is root's secure path, which
/// usually misses user-local installs like `~/.local/bin/claude`. To make
/// `sudo agentsight exec -- claude` find the *invoking user's* tools, we search
/// that user's common bin dirs first (derived from `$SUDO_USER`).
fn find_in_path(cmd: &str) -> Option<std::path::PathBuf> {
    let mut dirs: Vec<std::path::PathBuf> = Vec::new();

    if let Some(user) = std::env::var_os("SUDO_USER") {
        if let Some(home) = sudo_user_home(&user) {
            dirs.push(home.join(".local/bin"));
            dirs.push(home.join("bin"));
            // NVM keeps node under ~/.nvm/versions/node/<ver>/bin; pick the newest.
            if let Some(nvm_bin) = newest_nvm_bin(&home) {
                dirs.push(nvm_bin);
            }
        }
    }

    if let Some(path) = std::env::var_os("PATH") {
        dirs.extend(std::env::split_paths(&path));
    }

    for dir in dirs {
        let full = dir.join(cmd);
        if let Ok(meta) = std::fs::metadata(&full) {
            if meta.is_file() {
                return Some(full);
            }
        }
    }
    None
}

/// Resolve the home directory of the `$SUDO_USER` by reading `/etc/passwd`.
fn sudo_user_home(user: &std::ffi::OsStr) -> Option<std::path::PathBuf> {
    let user = user.to_str()?;
    let passwd = std::fs::read_to_string("/etc/passwd").ok()?;
    for line in passwd.lines() {
        let mut fields = line.split(':');
        if fields.next() == Some(user) {
            // username:x:uid:gid:gecos:home:shell -> home is field index 5.
            return fields.nth(4).map(std::path::PathBuf::from);
        }
    }
    None
}

/// Find the newest NVM-installed node bin dir under a user's home, if any.
fn newest_nvm_bin(home: &std::path::Path) -> Option<std::path::PathBuf> {
    let versions = home.join(".nvm/versions/node");
    let mut entries: Vec<_> = std::fs::read_dir(&versions).ok()?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .collect();
    entries.sort();
    entries.last().map(|p| p.join("bin"))
}

/// Heuristic: does this ELF statically embed its own SSL implementation?
///
/// Node.js bundles OpenSSL directly into the `node` binary, so there is no
/// system `libssl.so` for sslsniff to hook — it must attach to the binary
/// itself. We detect this by scanning for the `SSL_write` symbol-name string
/// in the file. Dynamically-linked runtimes like CPython call into a separate
/// `libssl.so` (via `_ssl.so`) and do NOT contain this string, so they keep
/// using sslsniff's system-libssl attachment with comm filtering intact.
fn binary_embeds_ssl(path: &str) -> bool {
    use std::io::Read;
    const NEEDLE: &[u8] = b"SSL_write";
    let mut f = match std::fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return false,
    };
    let mut buf = vec![0u8; 1 << 20]; // 1 MiB chunks
    // Carry the tail of each chunk so a match spanning a boundary isn't missed.
    let mut carry: Vec<u8> = Vec::new();
    loop {
        let n = match f.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => n,
            Err(_) => return false,
        };
        carry.extend_from_slice(&buf[..n]);
        if carry.windows(NEEDLE.len()).any(|w| w == NEEDLE) {
            return true;
        }
        let keep = NEEDLE.len() - 1;
        if carry.len() > keep {
            carry.drain(..carry.len() - keep);
        }
    }
    false
}

/// Launch a target command and automatically trace it with eBPF.
///
/// This is the zero-configuration entry point: it discovers the target's real
/// ELF binary (for SSL uprobe attachment), derives the process `--comm` filter
/// from the command name, starts SSL + process + system monitoring in the
/// background (quiet, so the child owns the terminal), then spawns the child.
/// Monitoring stops automatically when the child exits.
async fn run_exec(
    binary_extractor: &BinaryExtractor,
    command: &[String],
    binary_path_override: Option<&str>,
    log_file: &str,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
) -> Result<(), RunnerError> {
    let program = command.first()
        .ok_or_else(|| RunnerError::from("exec requires a command to run, e.g. `agentsight exec -- claude`"))?;
    let prog_args = &command[1..];

    println!("AgentSight exec");
    println!("{}", "=".repeat(60));

    // Derive the process comm filter from the command's base name. The kernel
    // truncates comm to 15 chars (TASK_COMM_LEN - 1), so match that here.
    let base = std::path::Path::new(program)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or(program);
    let comm: String = base.chars().take(15).collect();

    // Auto-discover the SSL binary unless the user pinned it explicitly.
    let binary_path = match binary_path_override {
        Some(p) => {
            println!("→ Using provided binary path: {}", p);
            Some(p.to_string())
        }
        None => match resolve_binary_path(program) {
            Ok(p) => {
                println!("✓ Auto-discovered binary: {}", p);
                Some(p)
            }
            Err(e) => {
                // Non-fatal: process/system monitoring still works without SSL.
                println!("⚠ Could not auto-discover binary for SSL capture: {}", e);
                println!("  SSL traffic may not be captured. Pass --binary-path to override.");
                None
            }
        },
    };
    println!("✓ Process filter (--comm): {}", comm);

    // Same optimized filters as the `record` command.
    let http_filter_patterns = vec![
        "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=".to_string(),
    ];
    let ssl_filter_patterns = vec![
        "data=0\\r\\n\\r\\n | data.type=binary".to_string(),
    ];

    let (event_sender, _event_receiver) = broadcast::channel(1000);

    let mut agent = build_trace_agent(
        binary_extractor, "exec",
        /* ssl */ true, /* pid */ None, /* ssl_uid */ None, Some(&comm),
        &ssl_filter_patterns, /* ssl_handshake */ false, /* ssl_http */ true,
        /* ssl_raw_data */ false, /* process */ true, /* stdio */ false,
        None, None, false, 8192, None, None,
        /* system */ true, /* system_interval */ 2,
        &http_filter_patterns, /* disable_auth_removal */ false,
        binary_path.as_deref(), log_file,
        /* quiet */ true, rotate_logs, max_log_size,
    )?;

    // Start web server before launching the child so the UI is ready immediately.
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, Some(log_file), event_sender.clone()).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    // Attach eBPF first (uprobes bind to the binary file, so they catch the
    // child even though it starts a moment later).
    let mut stream = agent.run().await?;

    if enable_server {
        println!("🌐 Web UI: http://127.0.0.1:{}", server_port);
    }
    println!("▶ Launching: {}", command.join(" "));
    println!("{}", "=".repeat(60));

    // Spawn the target with inherited stdio so its TUI works normally.
    let mut child = tokio::process::Command::new(program)
        .args(prog_args)
        .spawn()
        .map_err(|e| RunnerError::from(format!("failed to launch '{}': {}", program, e)))?;

    // Consume events and watch for the child to exit, whichever happens.
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(event) => {
                        if enable_server {
                            let _ = event_sender.send(event);
                        }
                    }
                    None => break, // event stream ended
                }
            }
            status = child.wait() => {
                match status {
                    Ok(s) => println!("\n{}\n✓ Target exited ({}). Stopping monitoring.", "=".repeat(60), s),
                    Err(e) => println!("\n⚠ Error waiting on target: {}", e),
                }
                break;
            }
        }
    }

    print_global_http_filter_metrics();
    print_global_ssl_filter_metrics();
    if enable_server {
        println!("Recorded data remains viewable at http://127.0.0.1:{} (log: {})", server_port, log_file);
    }

    Ok(())
}

// Shared server management function
/// Monitor system resources (CPU and memory)
async fn run_system(
    interval: u64,
    pid: Option<u32>,
    comm: Option<&str>,
    include_children: bool,
    cpu_threshold: Option<f64>,
    memory_threshold: Option<u64>,
    log_file: &str,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
) -> Result<(), RunnerError> {
    println!("System Resource Monitoring");
    println!("{}", "=".repeat(60));

    let mut system_runner = SystemRunner::new()
        .interval(interval);

    // Configure monitoring target
    if let Some(pid) = pid {
        system_runner = system_runner.pid(pid);
        println!("Monitoring PID: {}", pid);
    } else if let Some(comm) = comm {
        system_runner = system_runner.comm(comm);
        println!("Monitoring process: {}", comm);
    } else {
        println!("Monitoring system-wide resources");
    }

    // Configure options
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
    println!("{}", "=".repeat(60));
    println!("Starting system monitoring (press Ctrl+C to stop):");

    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);

    // Add TimestampNormalizer first
    system_runner = system_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    // Add file logger
    system_runner = system_runner
        .add_analyzer(Box::new(
            if rotate_logs {
                FileLogger::with_max_size(log_file, max_log_size).unwrap()
            } else {
                FileLogger::new(log_file).unwrap()
            }
        ));

    // Add console output unless quiet
    if !quiet {
        system_runner = system_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(
        enable_server,
        server_port,
        Some(log_file),
        event_sender.clone()
    ).await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = system_runner.run().await?;

    // Consume the stream to actually process events
    while let Some(event) = stream.next().await {
        // Forward events to web server if enabled
        if enable_server {
            let _ = event_sender.send(event);
        }
    }

    Ok(())
}

async fn start_web_server_if_enabled(
    enable_server: bool,
    port: u16,
    log_file: Option<&str>,
    event_sender: broadcast::Sender<crate::framework::core::Event>,
) -> Result<Option<tokio::task::JoinHandle<()>>, Box<dyn std::error::Error>> {
    if !enable_server {
        return Ok(None);
    }

    let addr = format!("0.0.0.0:{}", port).parse()
        .map_err(|e| format!("Invalid server address: {}", e))?;

    let web_server = WebServer::new(event_sender, log_file).map_err(|e| format!("Failed to create web server: {}", e))?;

    println!("🌐 Starting web server on http://{}", addr);
    println!("   Frontend will be available once the server starts");

    let server_handle = tokio::spawn(async move {
        if let Err(e) = web_server.start(addr).await {
            eprintln!("❌ Web server error: {}", e);
        }
    });

    // Give the server a moment to start
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    Ok(Some(server_handle))
}
