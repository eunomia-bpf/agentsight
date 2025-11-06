use clap::{Parser, Subcommand};
use futures::stream::StreamExt;
use std::sync::atomic::{AtomicBool, Ordering};
use tokio::signal;
use tokio::sync::broadcast;

mod framework;
mod server;

use framework::{
    binary_extractor::BinaryExtractor,
    runners::{SslRunner, ProcessRunner, AgentRunner, SystemRunner, RunnerError, Runner},
    analyzers::{OutputAnalyzer, FileLogger, SSEProcessor, SSLMerger, HTTPParser, HTTPDecompressor, HTTPFilter, AuthHeaderRemover, SSLFilter, TimestampNormalizer, print_global_http_filter_metrics, print_global_ssl_filter_metrics}
};

use server::WebServer;

static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);

fn convert_runner_error(e: RunnerError) -> Box<dyn std::error::Error> {
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
async fn main() -> Result<(), Box<dyn std::error::Error>> {
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
        Commands::Trace { ssl, ssl_uid, pid, comm, ssl_filter, ssl_handshake, ssl_http, ssl_raw_data, process, duration, mode, system, system_interval, http_filter, disable_auth_removal, binary_path, log_file, quiet, rotate_logs, max_log_size, server, server_port } => run_trace(&binary_extractor, *ssl, *pid, *ssl_uid, comm.as_deref(), ssl_filter, *ssl_handshake, *ssl_http, *ssl_raw_data, *process, *duration, *mode, *system, *system_interval, http_filter, *disable_auth_removal, binary_path.as_deref(), log_file, *quiet, *rotate_logs, *max_log_size, *server, *server_port).await.map_err(convert_runner_error)?,
        Commands::Record { comm, binary_path, log_file, rotate_logs, max_log_size, server_port } => {
            // Predefined filter patterns optimized for agent monitoring
            let http_filter_patterns = vec![
                "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=".to_string(),
            ];
            let ssl_filter_patterns = vec![
                "data=0\\r\\n\\r\\n | data.type=binary".to_string(),
            ];

            // Enable system monitoring by default for record command
            run_trace(&binary_extractor, true, None, None, Some(comm), &ssl_filter_patterns, false, true, false, true, None, None, true, 2, &http_filter_patterns, false, binary_path.as_deref(), log_file, true, *rotate_logs, *max_log_size, true, *server_port).await.map_err(convert_runner_error)?
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

        // Add HTTP decompressor to decompress gzip/deflate responses
        ssl_runner = ssl_runner.add_analyzer(Box::new(HTTPDecompressor::new()));

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
    
    // Set up event broadcasting for server if enabled
    let (event_sender, _event_receiver) = broadcast::channel(1000);
    
    let mut agent = AgentRunner::new("trace");
    
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
        if let Some(comm_filter) = comm {
            ssl_args.extend(["-c".to_string(), comm_filter.to_string()]);
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
            // Add SSL merger FIRST to combine consecutive READ events into complete HTTP messages
            ssl_runner = ssl_runner.add_analyzer(Box::new(SSLMerger::new()));

            ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));

            let http_parser = if ssl_raw_data {
                HTTPParser::new()
            } else {
                HTTPParser::new().disable_raw_data()
            };
            ssl_runner = ssl_runner.add_analyzer(Box::new(http_parser));

            // Add HTTP decompressor after HTTP parser to decompress gzip/deflate responses
            ssl_runner = ssl_runner.add_analyzer(Box::new(HTTPDecompressor::new()));

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
    if !ssl_enabled && !process_enabled && !system_enabled {
        return Err("At least one monitoring type must be enabled (--ssl, --process, or --system)".into());
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

    let addr = format!("127.0.0.1:{}", port).parse()
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
