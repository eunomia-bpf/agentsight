// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// The trace/record/exec path now uses the TraceConfig struct instead of ~28
// positional args. The remaining offenders are the raw `ssl`/`stdio`/`system`
// CLI handlers and HTTPEvent::new; collapsing those is a follow-up, so the lint
// stays allowed crate-wide until then.
#![allow(clippy::too_many_arguments)]

use clap::{Parser, Subcommand};
use futures::stream::StreamExt;
use std::sync::{
    Arc, OnceLock,
    atomic::{AtomicBool, Ordering},
};
use tokio::signal;
use tokio::sync::Notify;

mod binary_resolver;
mod cli_db;
mod cli_discover;
mod framework;
mod server;

use binary_resolver::{
    binary_embeds_ssl, parse_container_ref, resolve_binary_path, resolve_container_binary_path,
};

use cli_db::{
    AdapterCommand, configured_db_path, run_adapters_command, run_audit_query,
    run_capture_adapters, run_export, run_replay, run_token_query,
};
use cli_discover::run_discover;
use framework::{
    analyzers::{
        AuthHeaderRemover, FileLogger, HTTPFilter, HTTPParser, OtelExporter, OutputAnalyzer,
        SSEProcessor, SSLFilter, TimestampNormalizer, print_global_http_filter_metrics,
        print_global_ssl_filter_metrics,
    },
    binary_extractor::BinaryExtractor,
    capture::cli_output::{
        CLI_OUTPUT_CAPTURE_MAX_BYTES, persist_cli_output_evidence, should_capture_cli_output,
        tee_child_stream,
    },
    runners::{
        AgentRunner, EventStream, ProcessRunner, Runner, RunnerError, SslRunner, StdioRunner,
        SystemRunner,
    },
    storage::StorageAnalyzer,
};

use server::WebServer;

/// Configuration for exporting GenAI spans to an OpenTelemetry Collector.
#[derive(Clone)]
struct OtelConfig {
    /// OTLP/HTTP base endpoint; `None` falls back to env vars / localhost.
    endpoint: Option<String>,
    /// Opt-in: include prompt/completion content in spans.
    capture_content: bool,
}

/// All options for a trace/record/exec monitoring session.
///
/// Collapses what used to be ~28 positional arguments threaded through
/// `run_trace` and `build_trace_agent`. The `Default` impl is the neutral
/// "nothing enabled" baseline; the `trace`, `record`, and `exec` handlers each
/// fill in only the fields they care about.
#[derive(Default)]
struct TraceConfig {
    /// Runner-set name passed to `AgentRunner::new` ("trace" or "exec").
    name: &'static str,
    ssl: bool,
    pid: Option<u32>,
    ssl_uid: Option<u32>,
    comm: Option<String>,
    ssl_filter: Vec<String>,
    ssl_handshake: bool,
    ssl_http: bool,
    ssl_raw_data: bool,
    process: bool,
    stdio: bool,
    stdio_uid: Option<u32>,
    stdio_comm: Option<String>,
    stdio_all_fds: bool,
    stdio_max_bytes: u32,
    duration: Option<u32>,
    mode: Option<u32>,
    system: bool,
    system_interval: u64,
    http_filter: Vec<String>,
    disable_auth_removal: bool,
    otel: Option<OtelConfig>,
    /// SSL binary path; may be a `docker://` ref that `run_trace` resolves in place.
    binary_path: Option<String>,
    log_file: String,
    db_path: Option<String>,
    adapter: Option<String>,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    server: bool,
    server_port: u16,
}

static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);
static SHUTDOWN_NOTIFY: OnceLock<Arc<Notify>> = OnceLock::new();

fn shutdown_notify() -> Arc<Notify> {
    SHUTDOWN_NOTIFY
        .get_or_init(|| Arc::new(Notify::new()))
        .clone()
}

fn convert_runner_error(e: RunnerError) -> Box<dyn std::error::Error + Send + Sync> {
    Box::new(std::io::Error::other(e.to_string()))
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
        shutdown_notify().notify_waiters();
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
        /// Export GenAI spans to an OpenTelemetry Collector via OTLP/HTTP
        #[arg(long)]
        otel: bool,
        /// OTLP/HTTP endpoint for --otel (default: $OTEL_EXPORTER_OTLP_ENDPOINT or http://localhost:4318)
        #[arg(long)]
        otel_endpoint: Option<String>,
        /// Include prompt/completion content in exported GenAI spans (opt-in; off by default for privacy)
        #[arg(long)]
        otel_capture_content: bool,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// Log file for output and server
        #[arg(short = 'o', long, default_value = "trace.log")]
        log_file: String,
        /// SQLite database path for production queries and adapters
        #[arg(long)]
        db: Option<String>,
        /// SQL adapter to run after capture when --db is set: auto, anthropic, claude-code, openclaw, gemini-cli
        #[arg(long, default_value = "auto")]
        adapter: String,
        /// Do not run SQL adapters after capture
        #[arg(long)]
        no_adapters: bool,
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
    /// Equivalent to: trace -c claude --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\\r\\n\\r\\n" -q --server-port 7395 --server -o record.log
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
        /// SQLite database path for production queries and adapters
        #[arg(long)]
        db: Option<String>,
        /// SQL adapter to run after capture when --db is set: auto, anthropic, claude-code, openclaw, gemini-cli
        #[arg(long, default_value = "auto")]
        adapter: String,
        /// Do not run SQL adapters after capture
        #[arg(long)]
        no_adapters: bool,
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
        /// SQLite database path for production queries and adapters
        #[arg(long)]
        db: Option<String>,
        /// SQL adapter to run after capture when --db is set: auto, anthropic, claude-code, openclaw, gemini-cli
        #[arg(long, default_value = "auto")]
        adapter: String,
        /// Do not run SQL adapters after capture
        #[arg(long)]
        no_adapters: bool,
        /// Enable log rotation
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
    /// Replay a JSONL capture into SQLite and run generic projections/adapters
    Replay {
        /// Input JSONL log file
        #[arg(short, long)]
        input: String,
        /// SQLite database path
        #[arg(long)]
        db: String,
        /// SQL adapter to run after replay: auto, anthropic, claude-code, openclaw, gemini-cli
        #[arg(long, default_value = "auto")]
        adapter: String,
        /// Do not run SQL adapters after replay
        #[arg(long)]
        no_adapters: bool,
    },
    /// Query token usage from a SQLite database
    Token {
        /// SQLite database path
        #[arg(long)]
        db: String,
        /// Grouping key: model, provider, comm, pid
        #[arg(long, default_value = "model")]
        group_by: String,
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Query audit events from a SQLite database
    Audit {
        /// SQLite database path
        #[arg(long)]
        db: String,
        /// Audit type: llm, process, file
        #[arg(long)]
        audit_type: Option<String>,
        /// Maximum rows
        #[arg(long, default_value = "100")]
        limit: usize,
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Export a web/demo snapshot from a SQLite database
    Export {
        /// SQLite database path
        #[arg(long)]
        db: String,
        /// Output snapshot path, or '-' for stdout
        #[arg(short, long)]
        output: String,
        /// Maximum canonical events to include
        #[arg(long, default_value = "10000")]
        event_limit: usize,
        /// Maximum audit events to include
        #[arg(long, default_value = "10000")]
        audit_limit: usize,
    },
    /// List or run built-in SQL adapters
    Adapters {
        /// Emit JSON output when listing adapters
        #[arg(long)]
        json: bool,
        #[command(subcommand)]
        command: Option<AdapterCommand>,
    },
    /// Discover supported local agent CLIs and recommended capture settings
    Discover {
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
}

#[tokio::main]
async fn main() {
    // Print errors as a clean one-line `Error: <message>` (Display) and exit 1,
    // instead of the default `-> Result` behavior which prints them via Debug.
    if let Err(e) = run().await {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}

async fn run() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Initialize env_logger with default log level of info
    env_logger::Builder::from_default_env()
        .filter_level(log::LevelFilter::Info)
        .init();

    let cli = Cli::parse();

    // Setup signal handler for graceful shutdown
    setup_signal_handler().await;

    match &cli.command {
        Commands::Replay {
            input,
            db,
            adapter,
            no_adapters,
        } => {
            run_replay(input, db, (!*no_adapters).then_some(adapter.as_str()))?;
            return Ok(());
        }
        Commands::Token { db, group_by, json } => {
            run_token_query(db, group_by, *json)?;
            return Ok(());
        }
        Commands::Audit {
            db,
            audit_type,
            limit,
            json,
        } => {
            run_audit_query(db, audit_type.as_deref(), *limit, *json)?;
            return Ok(());
        }
        Commands::Export {
            db,
            output,
            event_limit,
            audit_limit,
        } => {
            run_export(db, output, *event_limit, *audit_limit)?;
            return Ok(());
        }
        Commands::Adapters { json, command } => {
            run_adapters_command(*json, command)?;
            return Ok(());
        }
        Commands::Discover { json } => {
            run_discover(*json)?;
            return Ok(());
        }
        _ => {}
    }

    // Create BinaryExtractor with embedded binaries
    let binary_extractor = BinaryExtractor::new().await?;

    match &cli.command {
        Commands::Ssl {
            sse_merge,
            http_parser,
            http_raw_data,
            http_filter,
            disable_auth_removal,
            ssl_filter,
            quiet,
            rotate_logs,
            max_log_size,
            server,
            server_port,
            log_file,
            binary_path,
            args,
        } => run_raw_ssl(
            &binary_extractor,
            *sse_merge,
            *http_parser,
            *http_raw_data,
            http_filter,
            *disable_auth_removal,
            ssl_filter,
            *quiet,
            *rotate_logs,
            *max_log_size,
            *server,
            *server_port,
            log_file,
            binary_path.as_deref(),
            args,
        )
        .await
        .map_err(convert_runner_error)?,
        Commands::Process {
            quiet,
            rotate_logs,
            max_log_size,
            server,
            server_port,
            log_file,
            args,
        } => run_raw_process(
            &binary_extractor,
            *quiet,
            *rotate_logs,
            *max_log_size,
            *server,
            *server_port,
            log_file,
            args,
        )
        .await
        .map_err(convert_runner_error)?,
        Commands::Stdio {
            pid,
            uid,
            comm,
            all_fds,
            max_bytes,
            quiet,
            rotate_logs,
            max_log_size,
            server,
            server_port,
            log_file,
        } => run_raw_stdio(
            &binary_extractor,
            *pid,
            *uid,
            comm.as_deref(),
            *all_fds,
            *max_bytes,
            *quiet,
            *rotate_logs,
            *max_log_size,
            *server,
            *server_port,
            log_file,
        )
        .await
        .map_err(convert_runner_error)?,
        Commands::Trace {
            ssl,
            ssl_uid,
            pid,
            comm,
            ssl_filter,
            ssl_handshake,
            ssl_http,
            ssl_raw_data,
            process,
            stdio,
            stdio_uid,
            stdio_comm,
            stdio_all_fds,
            stdio_max_bytes,
            duration,
            mode,
            system,
            system_interval,
            http_filter,
            disable_auth_removal,
            otel,
            otel_endpoint,
            otel_capture_content,
            binary_path,
            log_file,
            db,
            adapter,
            no_adapters,
            quiet,
            rotate_logs,
            max_log_size,
            server,
            server_port,
        } => {
            let cfg = TraceConfig {
                name: "trace",
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
                log_file: log_file.clone(),
                db_path: configured_db_path(db),
                adapter: (!*no_adapters).then_some(adapter.clone()),
                quiet: *quiet,
                rotate_logs: *rotate_logs,
                max_log_size: *max_log_size,
                server: *server,
                server_port: *server_port,
            };
            run_trace(&binary_extractor, cfg)
                .await
                .map_err(convert_runner_error)?
        }
        Commands::Record {
            comm,
            binary_path,
            log_file,
            db,
            adapter,
            no_adapters,
            rotate_logs,
            max_log_size,
            server_port,
        } => {
            // Predefined filter patterns optimized for agent monitoring. Enables
            // SSL + process + system monitoring and the web server by default.
            let cfg = TraceConfig {
                name: "trace",
                ssl: true,
                comm: Some(comm.clone()),
                ssl_filter: vec!["data=0\\r\\n\\r\\n".to_string()],
                ssl_http: true,
                process: true,
                stdio_max_bytes: 8192,
                system: true,
                system_interval: 2,
                http_filter: vec!["request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=".to_string()],
                binary_path: binary_path.clone(),
                log_file: log_file.clone(),
                db_path: configured_db_path(db),
                adapter: (!*no_adapters).then_some(adapter.clone()),
                quiet: true,
                rotate_logs: *rotate_logs,
                max_log_size: *max_log_size,
                server: true,
                server_port: *server_port,
                ..Default::default()
            };
            run_trace(&binary_extractor, cfg)
                .await
                .map_err(convert_runner_error)?
        }
        Commands::Exec {
            binary_path,
            log_file,
            db,
            adapter,
            no_adapters,
            rotate_logs,
            max_log_size,
            no_server,
            server_port,
            command,
        } => run_exec(
            &binary_extractor,
            command,
            binary_path.as_deref(),
            log_file,
            configured_db_path(db),
            (!*no_adapters).then_some(adapter.as_str()),
            *rotate_logs,
            *max_log_size,
            !*no_server,
            *server_port,
        )
        .await
        .map_err(convert_runner_error)?,
        Commands::System {
            interval,
            pid,
            comm,
            no_children,
            cpu_threshold,
            memory_threshold,
            log_file,
            quiet,
            rotate_logs,
            max_log_size,
            server,
            server_port,
        } => run_system(
            *interval,
            *pid,
            comm.as_deref(),
            !*no_children,
            *cpu_threshold,
            *memory_threshold,
            log_file,
            *quiet,
            *rotate_logs,
            *max_log_size,
            *server,
            *server_port,
        )
        .await
        .map_err(convert_runner_error)?,
        Commands::Replay {
            input,
            db,
            adapter,
            no_adapters,
        } => run_replay(input, db, (!*no_adapters).then_some(adapter.as_str()))?,
        Commands::Token { db, group_by, json } => run_token_query(db, group_by, *json)?,
        Commands::Audit {
            db,
            audit_type,
            limit,
            json,
        } => run_audit_query(db, audit_type.as_deref(), *limit, *json)?,
        Commands::Export {
            db,
            output,
            event_limit,
            audit_limit,
        } => run_export(db, output, *event_limit, *audit_limit)?,
        Commands::Adapters { json, command } => run_adapters_command(*json, command)?,
        Commands::Discover { json } => run_discover(*json)?,
    }

    Ok(())
}

async fn drive_stream_until_shutdown(stream: &mut EventStream) {
    let shutdown = shutdown_notify();
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                if maybe_event.is_none() {
                    break;
                }
            }
            _ = shutdown.notified() => {
                println!("✓ Shutdown requested. Stopping monitoring.");
                break;
            }
        }
    }
}

async fn drain_stream_for(stream: &mut EventStream, duration: tokio::time::Duration) {
    let shutdown = shutdown_notify();
    let deadline = tokio::time::sleep(duration);
    tokio::pin!(deadline);
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                if maybe_event.is_none() {
                    break;
                }
            }
            _ = &mut deadline => {
                break;
            }
            _ = shutdown.notified() => {
                break;
            }
        }
    }
}

/// Show raw SSL events as JSON with optional chunk merging and HTTP parsing
async fn run_raw_ssl(
    binary_extractor: &BinaryExtractor,
    enable_chunk_merger: bool,
    enable_http_parser: bool,
    include_raw_data: bool,
    http_filter_patterns: &[String],
    disable_auth_removal: bool,
    ssl_filter_patterns: &[String],
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
    log_file: &str,
    binary_path: Option<&str>,
    args: &[String],
) -> Result<(), RunnerError> {
    println!("Raw SSL Events");
    println!("{}", "=".repeat(60));

    let mut ssl_runner = SslRunner::from_binary_extractor(binary_extractor.get_sslsniff_path());

    // Translate a `docker://<container>` binary path to the host /proc/<pid>/exe
    // of the container's SSL-embedding process (see resolve_container_binary_path).
    let container_resolved: Option<String> = match binary_path.and_then(parse_container_ref) {
        Some(reference) => {
            Some(resolve_container_binary_path(reference).map_err(RunnerError::from)?)
        }
        None => None,
    };
    let binary_path = container_resolved.as_deref().or(binary_path);

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
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSLFilter::with_patterns(
            ssl_filter_patterns.to_vec(),
        )));
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
            ssl_runner = ssl_runner.add_analyzer(Box::new(HTTPFilter::with_patterns(
                http_filter_patterns.to_vec(),
            )));
        }

        // Add authorization header remover by default (unless disabled)
        if !disable_auth_removal {
            ssl_runner = ssl_runner.add_analyzer(Box::new(AuthHeaderRemover::new()));
        }

        let raw_data_info = if include_raw_data {
            " (with raw data)"
        } else {
            ""
        };
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() {
            " with SSL filtering,"
        } else {
            ""
        };
        let http_filter_info = if !http_filter_patterns.is_empty() {
            " and HTTP filtering"
        } else {
            ""
        };
        println!(
            "Starting SSL event stream{} with SSE processing, HTTP parsing{}{} enabled (press Ctrl+C to stop):",
            ssl_filter_info, raw_data_info, http_filter_info
        );
    } else if enable_chunk_merger {
        ssl_runner = ssl_runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() {
            " with SSL filtering and"
        } else {
            " with"
        };
        println!(
            "Starting SSL event stream{} SSE processing enabled (press Ctrl+C to stop):",
            ssl_filter_info
        );
    } else {
        let ssl_filter_info = if !ssl_filter_patterns.is_empty() {
            " with SSL filtering and"
        } else {
            " with"
        };
        println!(
            "Starting SSL event stream{} raw JSON output (press Ctrl+C to stop):",
            ssl_filter_info
        );
    }

    ssl_runner = ssl_runner.add_analyzer(Box::new(make_file_logger(
        log_file,
        rotate_logs,
        max_log_size,
    )?));

    if !quiet {
        ssl_runner = ssl_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, log_file, None)
        .await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = ssl_runner.run().await?;
    drive_stream_until_shutdown(&mut stream).await;

    Ok(())
}

/// Show raw process events as JSON
async fn run_raw_process(
    binary_extractor: &BinaryExtractor,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
    log_file: &str,
    args: &Vec<String>,
) -> Result<(), RunnerError> {
    println!("Raw Process Events");
    println!("{}", "=".repeat(60));

    let mut process_runner =
        ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());

    // Add additional arguments if provided
    if !args.is_empty() {
        process_runner = process_runner.with_args(args);
    }

    // Add TimestampNormalizer first to convert nanoseconds since boot to milliseconds since epoch
    process_runner = process_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    if !quiet {
        process_runner = process_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    process_runner = process_runner.add_analyzer(Box::new(make_file_logger(
        log_file,
        rotate_logs,
        max_log_size,
    )?));

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, log_file, None)
        .await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    println!("Starting process event stream with raw JSON output (press Ctrl+C to stop):");
    let mut stream = process_runner.run().await?;
    drive_stream_until_shutdown(&mut stream).await;

    Ok(())
}

fn build_stdio_args(
    pid: u32,
    uid: Option<u32>,
    comm: Option<&str>,
    all_fds: bool,
    max_bytes: u32,
) -> Vec<String> {
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
async fn run_raw_stdio(
    binary_extractor: &BinaryExtractor,
    pid: u32,
    uid: Option<u32>,
    comm: Option<&str>,
    all_fds: bool,
    max_bytes: u32,
    quiet: bool,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
    log_file: &str,
) -> Result<(), RunnerError> {
    println!("Raw Stdio Events");
    println!("{}", "=".repeat(60));

    let mut stdio_runner =
        StdioRunner::from_binary_extractor(binary_extractor.get_stdiocap_path()?);

    let stdio_args = build_stdio_args(pid, uid, comm, all_fds, max_bytes);
    stdio_runner = stdio_runner.with_args(&stdio_args);

    // Add TimestampNormalizer first to convert nanoseconds since boot to milliseconds since epoch
    stdio_runner = stdio_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    if !quiet {
        stdio_runner = stdio_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    stdio_runner = stdio_runner.add_analyzer(Box::new(make_file_logger(
        log_file,
        rotate_logs,
        max_log_size,
    )?));

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, log_file, None)
        .await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    println!(
        "Starting stdio event stream for PID {} (press Ctrl+C to stop):",
        pid
    );
    let mut stream = stdio_runner.run().await?;
    drive_stream_until_shutdown(&mut stream).await;

    Ok(())
}

/// Build a configured AgentRunner from trace options without running it.
/// Shared by `run_trace` and `run_exec` so they configure runners identically.
/// Build a FileLogger, turning an open failure (missing dir, no permission, …)
/// into a clean RunnerError instead of an `.unwrap()` panic.
fn make_file_logger(
    log_file: &str,
    rotate_logs: bool,
    max_log_size: u64,
) -> Result<FileLogger, RunnerError> {
    let result = if rotate_logs {
        FileLogger::with_max_size(log_file, max_log_size)
    } else {
        FileLogger::new(log_file)
    };
    result.map_err(|e| RunnerError::from(format!("failed to open log file '{}': {}", log_file, e)))
}

fn build_trace_agent(
    binary_extractor: &BinaryExtractor,
    cfg: &TraceConfig,
) -> Result<AgentRunner, RunnerError> {
    // Bind config fields to the local names the body below uses.
    let name = cfg.name;
    let ssl_enabled = cfg.ssl;
    let pid = cfg.pid;
    let ssl_uid = cfg.ssl_uid;
    let comm = cfg.comm.as_deref();
    let ssl_filter = cfg.ssl_filter.as_slice();
    let ssl_handshake = cfg.ssl_handshake;
    let ssl_http = cfg.ssl_http;
    let ssl_raw_data = cfg.ssl_raw_data;
    let process_enabled = cfg.process;
    let stdio_enabled = cfg.stdio;
    let stdio_uid = cfg.stdio_uid;
    let stdio_comm = cfg.stdio_comm.as_deref();
    let stdio_all_fds = cfg.stdio_all_fds;
    let stdio_max_bytes = cfg.stdio_max_bytes;
    let duration = cfg.duration;
    let mode = cfg.mode;
    let system_enabled = cfg.system;
    let system_interval = cfg.system_interval;
    let http_filter = cfg.http_filter.as_slice();
    let disable_auth_removal = cfg.disable_auth_removal;
    let otel = &cfg.otel;
    let binary_path = cfg.binary_path.as_deref();
    let log_file = cfg.log_file.as_str();
    let db_path = cfg.db_path.as_deref();
    let quiet = cfg.quiet;
    let rotate_logs = cfg.rotate_logs;
    let max_log_size = cfg.max_log_size;

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
        if binary_path.is_none()
            && let Some(comm_filter) = comm
        {
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
            ssl_runner =
                ssl_runner.add_analyzer(Box::new(SSLFilter::with_patterns(ssl_filter.to_vec())));
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
                ssl_runner = ssl_runner
                    .add_analyzer(Box::new(HTTPFilter::with_patterns(http_filter.to_vec())));
            }

            // Add authorization header remover by default (unless disabled)
            if !disable_auth_removal {
                ssl_runner = ssl_runner.add_analyzer(Box::new(AuthHeaderRemover::new()));
            }

            // Export GenAI spans to an OpenTelemetry Collector if requested.
            // Placed last so it observes fully-parsed (and auth-scrubbed) events.
            if let Some(otel_config) = otel {
                ssl_runner = ssl_runner.add_analyzer(Box::new(OtelExporter::new(
                    otel_config.endpoint.clone(),
                    otel_config.capture_content,
                )));
                println!("✓ OpenTelemetry GenAI export enabled");
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
        let pid_filter =
            pid.ok_or_else(|| RunnerError::from("stdio capture currently requires --pid"))?;
        let mut stdio_runner =
            StdioRunner::from_binary_extractor(binary_extractor.get_stdiocap_path()?);
        let stdio_args = build_stdio_args(
            pid_filter,
            stdio_uid,
            stdio_comm,
            stdio_all_fds,
            stdio_max_bytes,
        );

        stdio_runner = stdio_runner.with_args(&stdio_args);
        stdio_runner = stdio_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(stdio_runner));
        println!("✓ Stdio monitoring enabled for PID {}", pid_filter);
    }

    // Add process runner if enabled
    if process_enabled {
        let mut process_runner =
            ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());

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
        let mut system_runner = SystemRunner::new().interval(system_interval);

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
        println!(
            "✓ System monitoring enabled (interval: {}s)",
            system_interval
        );
    }

    // Ensure at least one runner is enabled
    if !ssl_enabled && !process_enabled && !stdio_enabled && !system_enabled {
        return Err(
            "At least one monitoring type must be enabled (--ssl, --process, --stdio, or --system)"
                .into(),
        );
    }

    // Add global analyzers (HTTP filter is now added to SSL runner instead)

    agent = agent.add_global_analyzer(Box::new(make_file_logger(
        log_file,
        rotate_logs,
        max_log_size,
    )?));
    println!("✓ Logging to file: {}", log_file);

    if let Some(path) = db_path {
        let storage = StorageAnalyzer::new(path).map_err(|e| {
            RunnerError::from(format!("failed to open SQLite database '{}': {}", path, e))
        })?;
        agent = agent.add_global_analyzer(Box::new(storage));
        println!("✓ SQLite storage enabled: {}", path);
    }

    if !quiet {
        agent = agent.add_global_analyzer(Box::new(OutputAnalyzer::new()));
        println!("✓ Console output enabled");
    }

    Ok(agent)
}

/// Trace monitoring with configurable runners and analyzers
async fn run_trace(
    binary_extractor: &BinaryExtractor,
    mut cfg: TraceConfig,
) -> Result<(), RunnerError> {
    println!("Trace Monitoring");
    println!("{}", "=".repeat(60));

    // A `--binary-path docker://<container>` (or `docker:<container>`) reference
    // is translated to the host-side /proc/<host-pid>/exe of the container's
    // main process. This is the out-of-the-box path for containerized agents
    // such as OpenClaw, which is Node.js with a statically-linked OpenSSL — so
    // there is no in-container libssl.so to scan, and sslsniff must attach its
    // uprobe directly to the node binary via /proc/<pid>/exe.
    if let Some(reference) = cfg.binary_path.as_deref().and_then(parse_container_ref) {
        cfg.binary_path =
            Some(resolve_container_binary_path(reference).map_err(RunnerError::from)?);
    }

    // When the user enabled SSL but didn't pin a --binary-path, try to discover
    // one from --comm. This fixes the common "record -c node" case: Node (and
    // gemini-cli, which runs on Node) statically links OpenSSL, so there is no
    // system libssl.so to hook. Only adopt the resolved binary if it actually
    // embeds SSL, so dynamically-linked runtimes like Python are left to
    // sslsniff's system-libssl path with comm filtering intact.
    if cfg.ssl && cfg.binary_path.is_none() {
        let resolved = cfg
            .comm
            .as_deref()
            .filter(|c| !c.contains(','))
            .and_then(|c| resolve_binary_path(c).ok())
            .filter(|p| binary_embeds_ssl(p));
        if let Some(p) = resolved {
            println!(
                "✓ Auto-discovered statically-linked SSL binary for --comm '{}': {}",
                cfg.comm.as_deref().unwrap_or(""),
                p
            );
            cfg.binary_path = Some(p);
        }
    }

    let enable_server = cfg.server;
    let server_port = cfg.server_port;
    let log_file = cfg.log_file.clone();
    let db_path = cfg.db_path.clone();
    let adapter = cfg.adapter.clone();

    let mut agent = build_trace_agent(binary_extractor, &cfg)?;

    println!("{}", "=".repeat(60));
    println!(
        "Starting flexible trace monitoring with {} runners and {} global analyzers...",
        agent.runner_count(),
        agent.analyzer_count()
    );
    println!("Press Ctrl+C to stop");

    // Start web server if enabled
    let _server_handle =
        start_web_server_if_enabled(enable_server, server_port, &log_file, db_path.as_deref())
            .await
            .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = agent.run().await?;

    // Drive the stream so the analyzer chain (file logging, storage, etc.) runs.
    drive_stream_until_shutdown(&mut stream).await;
    drop(stream);
    drop(agent);

    run_capture_adapters(db_path.as_deref(), adapter.as_deref())?;

    Ok(())
}

/// Launch a target command and automatically trace it with eBPF.
///
/// This is the zero-configuration entry point: it discovers the target's real
/// ELF binary (for SSL uprobe attachment), derives the process `--comm` filter
/// from the command name, starts SSL + process + system monitoring in the
/// background (quiet, so the child owns the terminal), then spawns the child.
/// Monitoring stops automatically when the child exits.
fn target_user_ids() -> Option<(libc::uid_t, libc::gid_t)> {
    if unsafe { libc::geteuid() } != 0 {
        return None;
    }
    let uid = std::env::var("SUDO_UID").ok()?.parse().ok()?;
    let gid = std::env::var("SUDO_GID").ok()?.parse().ok()?;
    Some((uid, gid))
}

fn default_session_db_path() -> Result<String, RunnerError> {
    // Under sudo, resolve the real user's home directory so the DB is
    // accessible without sudo afterward. Falls back to dirs::data_local_dir.
    let base = std::env::var("SUDO_USER")
        .ok()
        .and_then(|user| {
            std::fs::read_to_string("/etc/passwd").ok().and_then(|passwd| {
                passwd
                    .lines()
                    .find(|l| l.starts_with(&format!("{}:", user)))
                    .and_then(|l| l.split(':').nth(5))
                    .map(|home| std::path::PathBuf::from(home).join(".local/share"))
            })
        })
        .or_else(dirs::data_local_dir)
        .or_else(|| dirs::home_dir().map(|h| h.join(".local/share")))
        .ok_or_else(|| RunnerError::from("cannot determine home directory for session DB"))?;
    let dir = base.join("agentsight").join("sessions");
    std::fs::create_dir_all(&dir).map_err(|e| {
        RunnerError::from(format!(
            "failed to create session directory {}: {}",
            dir.display(),
            e
        ))
    })?;
    let ts = chrono::Local::now().format("%Y%m%d-%H%M%S");
    Ok(dir.join(format!("{}.db", ts)).to_string_lossy().to_string())
}

fn print_session_summary(db_path: &str) {
    let store = match framework::storage::SqliteStore::open(db_path) {
        Ok(s) => s,
        Err(_) => return,
    };
    let token_rows = store.token_summary("model").unwrap_or_default();
    let audit_rows = store.audit_rows(None, 10_000).unwrap_or_default();

    if token_rows.is_empty() && audit_rows.is_empty() {
        return;
    }

    println!("\n{}", "─".repeat(60));
    println!("📊 Session Summary");
    println!("{}", "─".repeat(60));

    // --- Token usage (LLM calls) ---
    if !token_rows.is_empty() {
        let mut total_calls: i64 = 0;
        let mut total_tokens: i64 = 0;
        for row in &token_rows {
            total_calls += row.calls;
            total_tokens += row.total_tokens;
            println!(
                "  🤖 {} — {} calls, {} tokens (in: {}, out: {})",
                row.group, row.calls, row.total_tokens, row.input_tokens, row.output_tokens
            );
        }
        if token_rows.len() > 1 {
            println!(
                "     Total: {} API calls, {} tokens",
                total_calls, total_tokens
            );
        }
    }

    // --- System behavior (what the agent actually did) ---
    if !audit_rows.is_empty() {
        let mut exec_count: usize = 0;
        let mut programs: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
        for row in &audit_rows {
            if row.action.as_deref() == Some("exec") {
                exec_count += 1;
                if let Some(comm) = &row.comm {
                    programs.insert(comm.clone());
                }
            }
        }
        if exec_count > 0 {
            let progs: Vec<&str> = programs.iter().map(|s| s.as_str()).collect();
            println!(
                "  🔍 {} processes spawned: {}",
                exec_count,
                if progs.len() <= 8 {
                    progs.join(", ")
                } else {
                    format!("{}, ... ({} total)", progs[..6].join(", "), progs.len())
                }
            );
        }
        println!("  📋 {} system events captured", audit_rows.len());
    }

    println!();
    println!("  Database: {}", db_path);
    println!("  Token details:  agentsight token --db {}", db_path);
    println!("  Full audit:     agentsight audit --db {}", db_path);
    println!("{}", "─".repeat(60));
}

async fn run_exec(
    binary_extractor: &BinaryExtractor,
    command: &[String],
    binary_path_override: Option<&str>,
    log_file: &str,
    db_path: Option<String>,
    adapter: Option<&str>,
    rotate_logs: bool,
    max_log_size: u64,
    enable_server: bool,
    server_port: u16,
) -> Result<(), RunnerError> {
    let program = command.first().ok_or_else(|| {
        RunnerError::from("exec requires a command to run, e.g. `agentsight exec -- claude`")
    })?;
    let prog_args = &command[1..];

    // Auto-create a session database when the user didn't specify --db.
    let (db_path, adapter) = if db_path.is_some() {
        (db_path, adapter)
    } else {
        match default_session_db_path() {
            Ok(p) => (Some(p), Some(adapter.unwrap_or("auto"))),
            Err(e) => {
                eprintln!("⚠ Could not create session DB ({}), continuing without it.", e);
                (None, adapter)
            }
        }
    };

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
    let db_path_for_adapters = db_path.clone();
    let cfg = TraceConfig {
        name: "exec",
        ssl: true,
        comm: Some(comm.clone()),
        ssl_filter: vec!["data=0\\r\\n\\r\\n".to_string()],
        ssl_http: true,
        process: true,
        stdio_max_bytes: 8192,
        system: true,
        system_interval: 2,
        http_filter: vec!["request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=".to_string()],
        binary_path,
        log_file: log_file.to_string(),
        db_path,
        adapter: adapter.map(str::to_string),
        quiet: true,
        rotate_logs,
        max_log_size,
        ..Default::default()
    };

    // When not running as root, warm the sudo credential cache so the
    // user is prompted once (with a visible terminal) before eBPF binaries
    // are spawned with piped stdio.  Skip if passwordless sudo already works.
    if unsafe { libc::geteuid() } != 0 {
        let has_cached = std::process::Command::new("sudo")
            .args(["-n", "true"])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false);
        if !has_cached {
            println!("🔑 eBPF probes require root. Requesting sudo access...");
            let ok = std::process::Command::new("sudo")
                .arg("true")
                .status()
                .map(|s| s.success())
                .unwrap_or(false);
            if !ok {
                return Err(RunnerError::from(
                    "sudo authentication failed. Either run as root (`sudo -E agentsight exec -- ...`) \
                     or grant your user passwordless sudo for the eBPF binaries."
                ));
            }
        }
    }

    let mut agent = build_trace_agent(binary_extractor, &cfg)?;

    // Start web server before launching the child so the UI is ready immediately.
    let _server_handle = start_web_server_if_enabled(
        enable_server,
        server_port,
        log_file,
        db_path_for_adapters.as_deref(),
    )
    .await
    .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    // Attach eBPF first (uprobes bind to the binary file, so they catch the
    // child even though it starts a moment later).
    let mut stream = agent.run().await?;

    if enable_server {
        println!("🌐 Web UI: http://127.0.0.1:{}", server_port);
    }
    println!("▶ Launching: {}", command.join(" "));
    println!("{}", "=".repeat(60));

    // Keep interactive tools on inherited stdio. For known headless JSON runs,
    // tee stdout/stderr so CLI-native usage summaries can be stored as evidence.
    let capture_cli_output =
        should_capture_cli_output(program, prog_args, db_path_for_adapters.as_deref());
    if capture_cli_output {
        println!("✓ CLI output evidence capture enabled");
    }

    let mut command_builder = tokio::process::Command::new(program);
    command_builder.args(prog_args);
    if capture_cli_output {
        command_builder
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());
    }
    // When running as root (via sudo), drop the child back to the real user
    // so the agent doesn't have elevated privileges.
    if let Some((uid, gid)) = target_user_ids() {
        println!("✓ Dropping child to uid={} gid={}", uid, gid);
        unsafe {
            command_builder.pre_exec(move || {
                if libc::setgid(gid) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                if libc::setuid(uid) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                Ok(())
            });
        }
    }
    let mut child = command_builder
        .spawn()
        .map_err(|e| RunnerError::from(format!("failed to launch '{}': {}", program, e)))?;
    let child_pid = child.id().unwrap_or_default();
    let stdout_task = if capture_cli_output {
        child.stdout.take().map(|stdout| {
            tokio::spawn(tee_child_stream(
                stdout,
                "stdout",
                CLI_OUTPUT_CAPTURE_MAX_BYTES,
            ))
        })
    } else {
        None
    };
    let stderr_task = if capture_cli_output {
        child.stderr.take().map(|stderr| {
            tokio::spawn(tee_child_stream(
                stderr,
                "stderr",
                CLI_OUTPUT_CAPTURE_MAX_BYTES,
            ))
        })
    } else {
        None
    };

    let shutdown = shutdown_notify();
    let mut target_exited = false;
    let mut exit_status = None;
    // Consume events and watch for the child to exit, whichever happens.
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(_event) => {} // drive the stream; events are persisted via the file logger
                    None => {
                        println!("\n⚠ Monitoring stream ended before target exited. Stopping target.");
                        break;
                    }
                }
            }
            status = child.wait() => {
                match status {
                    Ok(s) => {
                        println!("\n{}\n✓ Target exited ({}). Stopping monitoring.", "=".repeat(60), s);
                        exit_status = Some(s);
                    }
                    Err(e) => println!("\n⚠ Error waiting on target: {}", e),
                }
                target_exited = true;
                drain_stream_for(&mut stream, tokio::time::Duration::from_millis(5000)).await;
                break;
            }
            _ = shutdown.notified() => {
                println!("\n✓ Shutdown requested. Stopping target and monitoring.");
                break;
            }
        }
    }
    if !target_exited {
        stop_child(&mut child).await;
    }
    drop(stream);
    drop(agent);

    let stdout_capture = match stdout_task {
        Some(task) => match task.await {
            Ok(Ok(bytes)) => bytes,
            Ok(Err(e)) => {
                println!("⚠ Error capturing child stdout: {}", e);
                Vec::new()
            }
            Err(e) => {
                println!("⚠ Child stdout capture task failed: {}", e);
                Vec::new()
            }
        },
        None => Vec::new(),
    };
    let stderr_capture = match stderr_task {
        Some(task) => match task.await {
            Ok(Ok(bytes)) => bytes,
            Ok(Err(e)) => {
                println!("⚠ Error capturing child stderr: {}", e);
                Vec::new()
            }
            Err(e) => {
                println!("⚠ Child stderr capture task failed: {}", e);
                Vec::new()
            }
        },
        None => Vec::new(),
    };
    if capture_cli_output {
        persist_cli_output_evidence(
            db_path_for_adapters.as_deref(),
            log_file,
            program,
            prog_args,
            child_pid,
            &comm,
            exit_status,
            &stdout_capture,
            &stderr_capture,
        )?;
    }

    print_global_http_filter_metrics();
    print_global_ssl_filter_metrics();
    run_capture_adapters(db_path_for_adapters.as_deref(), adapter)?;

    if let Some(ref db) = db_path_for_adapters {
        print_session_summary(db);
    }

    if enable_server {
        println!(
            "Recorded data remains viewable at http://127.0.0.1:{} (log: {})",
            server_port, log_file
        );
    }

    Ok(())
}

async fn stop_child(child: &mut tokio::process::Child) {
    match child.try_wait() {
        Ok(Some(_)) => return,
        Ok(None) => {}
        Err(e) => {
            println!("⚠ Error checking target status: {}", e);
            return;
        }
    }

    match tokio::time::timeout(tokio::time::Duration::from_secs(2), child.wait()).await {
        Ok(Ok(_)) => return,
        Ok(Err(e)) => {
            println!("⚠ Error waiting for target shutdown: {}", e);
            return;
        }
        Err(_) => {}
    }

    if let Err(e) = child.kill().await {
        println!("⚠ Failed to kill target process: {}", e);
    }
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

    let mut system_runner = SystemRunner::new().interval(interval);

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

    // Add TimestampNormalizer first
    system_runner = system_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

    // Add file logger
    system_runner = system_runner.add_analyzer(Box::new(make_file_logger(
        log_file,
        rotate_logs,
        max_log_size,
    )?));

    // Add console output unless quiet
    if !quiet {
        system_runner = system_runner.add_analyzer(Box::new(OutputAnalyzer::new()));
    }

    // Start web server if enabled
    let _server_handle = start_web_server_if_enabled(enable_server, server_port, log_file, None)
        .await
        .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = system_runner.run().await?;
    drive_stream_until_shutdown(&mut stream).await;

    Ok(())
}

async fn start_web_server_if_enabled(
    enable_server: bool,
    port: u16,
    log_file: &str,
    db_path: Option<&str>,
) -> Result<Option<tokio::task::JoinHandle<()>>, Box<dyn std::error::Error>> {
    if !enable_server {
        return Ok(None);
    }

    let addr = format!("0.0.0.0:{}", port)
        .parse()
        .map_err(|e| format!("Invalid server address: {}", e))?;

    let web_server = WebServer::new(log_file, db_path)
        .map_err(|e| format!("Failed to create web server: {}", e))?;

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
