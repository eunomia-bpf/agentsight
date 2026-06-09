// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// The trace/record path now uses the TraceConfig struct instead of ~28
// positional args. The remaining offenders are the raw `ssl`/`stdio`/`system`
// CLI handlers and HTTPEvent::new; collapsing those is a follow-up, so the lint
// stays allowed crate-wide until then.
#![allow(clippy::too_many_arguments)]

use clap::{Parser, Subcommand};
use std::collections::VecDeque;
use std::io::Write;
use std::sync::{
    Arc, Mutex, OnceLock,
    atomic::{AtomicBool, Ordering},
};
use tokio::signal;
use tokio::sync::Notify;

mod analyzers;
mod binary_extractor;
mod binary_resolver;
mod cli_db;
mod cli_discover;
mod cmd_debug;
mod cmd_exec;
mod cmd_perf;
mod cmd_perf_live;
mod cmd_perf_tui;
mod cmd_trace;
mod event;
mod json;
mod model;
mod output;
mod runners;
mod server;
mod sinks;
mod sources;
mod text;
mod time;
mod view;

use analyzers::{print_global_http_filter_metrics, print_global_ssl_filter_metrics};
use binary_extractor::BinaryExtractor;
use cli_db::{
    configured_db_path, run_audit_query, run_db_summary, run_export, run_prompts_query,
    run_token_query,
};
use cli_discover::run_discover;
use cmd_debug::{run_raw_process, run_raw_ssl, run_raw_stdio, run_system};
use cmd_exec::{default_session_db_path, print_session_summary, run_exec};
use cmd_perf::{run_stat_query, run_top_query};
use cmd_perf_live::run_live_top_query;
use cmd_perf_tui::run_live_top_tui;
use cmd_trace::{
    OtelConfig, TraceConfig, convert_runner_error, run_trace, start_web_server_if_enabled,
};
use output::TopOptions;
use output::print_record_session_db_error;
use sources::session_db::{resolve_db_or_latest, run_db_list};

static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);
static SHUTDOWN_NOTIFY: OnceLock<Arc<Notify>> = OnceLock::new();
static TUI_DIAGNOSTICS: OnceLock<Mutex<VecDeque<String>>> = OnceLock::new();

struct TuiDiagnosticWriter;

impl Write for TuiDiagnosticWriter {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        let text = String::from_utf8_lossy(buf);
        for line in text.lines().map(str::trim).filter(|line| !line.is_empty()) {
            push_tui_diagnostic(line);
        }
        Ok(buf.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

fn push_tui_diagnostic(message: &str) {
    const MAX_TUI_DIAGNOSTICS: usize = 8;
    let diagnostics = TUI_DIAGNOSTICS.get_or_init(|| Mutex::new(VecDeque::new()));
    let Ok(mut diagnostics) = diagnostics.lock() else {
        return;
    };
    if diagnostics.back().is_some_and(|last| last == message) {
        return;
    }
    diagnostics.push_back(message.to_string());
    while diagnostics.len() > MAX_TUI_DIAGNOSTICS {
        diagnostics.pop_front();
    }
}

pub(crate) fn recent_tui_diagnostics(limit: usize) -> Vec<String> {
    let Some(diagnostics) = TUI_DIAGNOSTICS.get() else {
        return Vec::new();
    };
    let Ok(diagnostics) = diagnostics.lock() else {
        return Vec::new();
    };
    diagnostics
        .iter()
        .rev()
        .take(limit)
        .cloned()
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect()
}

fn shutdown_notify() -> Arc<Notify> {
    SHUTDOWN_NOTIFY
        .get_or_init(|| Arc::new(Notify::new()))
        .clone()
}

pub(crate) fn shutdown_requested() -> bool {
    SHUTDOWN_REQUESTED.load(Ordering::Relaxed)
}

fn interactive_terminal_available() -> bool {
    unsafe { libc::isatty(libc::STDIN_FILENO) == 1 && libc::isatty(libc::STDOUT_FILENO) == 1 }
}

fn command_uses_live_top_tui(cli: &Cli) -> bool {
    matches!(
        &cli.command,
        Commands::Top {
            db: None,
            count: None,
            once: false,
            plain: false,
            ..
        } if interactive_terminal_available()
    )
}

fn init_logging(suppress_terminal_output: bool) {
    let mut builder = env_logger::Builder::from_default_env();
    builder.filter_level(log::LevelFilter::Warn);
    if suppress_terminal_output {
        builder.target(env_logger::Target::Pipe(Box::new(TuiDiagnosticWriter)));
    }
    let _ = builder.try_init();
}

async fn setup_signal_handler(suppress_terminal_output: bool) {
    let mut sigint = signal::unix::signal(signal::unix::SignalKind::interrupt())
        .expect("Failed to install SIGINT handler");

    tokio::spawn(async move {
        sigint.recv().await;
        if !suppress_terminal_output {
            println!("\n\nReceived SIGINT, shutting down...");

            // Print HTTP filter metrics using the global function
            print_global_http_filter_metrics();

            // Print SSL filter metrics using the global function
            print_global_ssl_filter_metrics();
        }

        SHUTDOWN_REQUESTED.store(true, Ordering::Relaxed);
        shutdown_notify().notify_waiters();
    });
}

#[derive(Parser)]
#[command(
    author,
    version,
    about = "AgentSight: stat/top/record/report for AI agent runs.\n\n\
             Common flow:\n\
               sudo agentsight stat -- claude\n\
               sudo agentsight record -- claude\n\
               sudo agentsight top\n\
               agentsight report\n\
               agentsight report prompts --json\n\n\
             eBPF probes require root. Use sudo for live capture commands;\n\
             AgentSight can auto-elevate if you forget, while your agent still\n\
             runs as your normal user."
)]
struct Cli {
    /// Web UI bind address when a command starts a server.
    #[arg(long, default_value = cmd_trace::DEFAULT_SERVER_LISTEN, global = true)]
    listen: String,
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Print counters for a recorded session, or run a command and print counters when it exits.
    /// Examples: agentsight stat --db run.db     (or)  sudo agentsight stat -- claude
    Stat {
        /// SQLite database path (defaults to latest session when no command is passed)
        #[arg(long)]
        db: Option<String>,
        /// Emit JSON output. For clean JSON, use this with --db instead of a live command.
        #[arg(long)]
        json: bool,
        /// Override the auto-discovered SSL binary path when tracing a command
        #[arg(long)]
        binary_path: Option<String>,
        /// Disable the web server while tracing a command
        #[arg(long)]
        no_server: bool,
        /// Server port for the web UI while tracing a command
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Optional command to launch and trace before printing counters
        #[arg(last = true)]
        command: Vec<String>,
    },
    /// Show live agent sessions, or a saved session with --db.
    Top {
        /// SQLite database path for saved session mode
        #[arg(long)]
        db: Option<String>,
        /// Process PID filter, similar to top -p
        #[arg(short = 'p', long, conflicts_with = "comm")]
        pid: Option<u32>,
        /// Process command/name filter, e.g. claude, codex, gemini
        #[arg(short = 'c', long, conflicts_with = "pid")]
        comm: Option<String>,
        /// Sort key: cpu, rss, tokens, execs, fail, files, net, agent
        #[arg(long, default_value = "cpu")]
        sort: String,
        /// Detail view: all, processes, files, network, models
        #[arg(long, default_value = "all")]
        view: String,
        /// Refresh interval in seconds
        #[arg(short = 'i', long, default_value = "2")]
        interval: u64,
        /// Rows per section
        #[arg(short = 'n', long, default_value = "10")]
        limit: usize,
        /// Number of refreshes before exiting
        #[arg(long)]
        count: Option<u32>,
        /// Print one snapshot and exit
        #[arg(long)]
        once: bool,
        /// Use plain table output instead of the interactive live TUI
        #[arg(long)]
        plain: bool,
    },
    /// Record a command, or attach to an already-running agent by command name or PID.
    /// Examples: sudo agentsight record -- claude     (or)  sudo agentsight record -c claude
    Record {
        /// Process command filter, e.g. claude, codex, node, python
        #[arg(short = 'c', long, conflicts_with = "pid")]
        comm: Option<String>,
        /// Process PID filter
        #[arg(short = 'p', long, conflicts_with = "comm")]
        pid: Option<u32>,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// SQLite database path for view snapshots
        #[arg(long)]
        db: Option<String>,
        /// Disable the web server
        #[arg(long)]
        no_server: bool,
        /// Server port for the web UI
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Optional command to launch and trace. Use -c/--comm or -p/--pid instead to attach.
        #[arg(last = true)]
        command: Vec<String>,
    },
    /// Discover supported local agent CLIs and recommended capture settings
    Discover {
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Query and report on recorded sessions: summary, tokens, audit, prompts, export, list.
    /// Defaults to summary when no subcommand is given.
    Report {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Read agent-native Claude/Codex sessions (for summary)
        #[arg(long)]
        local: bool,
        #[command(subcommand)]
        sub: Option<ReportCommands>,
    },
    /// Low-level debugging tools: print raw streams and optionally serve a live view
    #[command(subcommand)]
    Debug(DebugCommands),
}

#[derive(Subcommand)]
enum ReportCommands {
    /// Session summary: what the agent did, tokens, processes, files
    Summary {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Read agent-native Claude/Codex sessions
        #[arg(long)]
        local: bool,
    },
    /// Query token usage from a SQLite database
    Token {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Grouping key: model, provider, comm, pid
        #[arg(long, default_value = "model")]
        group_by: String,
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Query audit events from a SQLite database
    Audit {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
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
    /// Show captured LLM prompts and responses when observable
    Prompts {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Maximum rows
        #[arg(long, default_value = "20")]
        limit: usize,
        /// Emit full request/response JSON
        #[arg(long)]
        json: bool,
    },
    /// Export a web/demo snapshot from a SQLite database
    Export {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Output snapshot path, or '-' for stdout
        #[arg(short, long)]
        output: String,
        /// Maximum audit events to include
        #[arg(long, default_value = "10000")]
        audit_limit: usize,
    },
    /// Serve the web UI for a saved SQLite session
    Serve {
        /// SQLite database path (defaults to latest session)
        #[arg(long)]
        db: Option<String>,
        /// Server port for the web UI
        #[arg(long, default_value = "7395")]
        server_port: u16,
    },
    /// List session databases
    List,
}

#[derive(Subcommand)]
enum DebugCommands {
    /// Print SSL traffic as raw/analyzed JSON
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
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Path to the binary executable to monitor (e.g., ~/.nvm/versions/node/v20.0.0/bin/node)
        #[arg(long)]
        binary_path: Option<String>,
        /// Additional arguments to pass to the SSL binary
        #[arg(last = true)]
        args: Vec<String>,
    },
    /// Print process runner events
    Process {
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
        /// Additional arguments to pass to the process binary
        #[arg(last = true)]
        args: Vec<String>,
    },
    /// Print local stdio payloads from a target process
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
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
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
        /// SQLite database path for view snapshots
        #[arg(long)]
        db: Option<String>,
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
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
        /// Suppress console output
        #[arg(short, long)]
        quiet: bool,
        /// Start web server on port 7395
        #[arg(long)]
        server: bool,
        /// Server port (used with --server)
        #[arg(long, default_value = "7395")]
        server_port: u16,
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
    let cli = Cli::parse();
    let suppress_terminal_output = command_uses_live_top_tui(&cli);
    init_logging(suppress_terminal_output);

    // Setup signal handler for graceful shutdown
    setup_signal_handler(suppress_terminal_output).await;

    match &cli.command {
        Commands::Report { db, local, sub } => match sub {
            None | Some(ReportCommands::Summary { .. }) => {
                let (db_ref, local_ref) = match sub {
                    Some(ReportCommands::Summary { db: d, local: l }) => (d, l),
                    _ => (db, local),
                };
                let resolved = if *local_ref {
                    None
                } else {
                    resolve_db_or_latest(db_ref).ok()
                };
                run_db_summary(resolved.as_deref())?;
            }
            Some(ReportCommands::Token {
                db: d,
                group_by,
                json,
            }) => {
                let effective = d.as_ref().or(db.as_ref()).cloned();
                let db = resolve_db_or_latest(&effective)?;
                run_token_query(&db, group_by, *json)?;
            }
            Some(ReportCommands::Audit {
                db: d,
                audit_type,
                limit,
                json,
            }) => {
                let effective = d.as_ref().or(db.as_ref()).cloned();
                if let Ok(db) = resolve_db_or_latest(&effective) {
                    run_audit_query(&db, audit_type.as_deref(), *limit, *json)?;
                } else {
                    cli_db::run_agent_native_audit(*json)?;
                }
            }
            Some(ReportCommands::Prompts { db: d, limit, json }) => {
                let effective = d.as_ref().or(db.as_ref()).cloned();
                let db = resolve_db_or_latest(&effective)?;
                run_prompts_query(&db, *limit, *json)?;
            }
            Some(ReportCommands::Export {
                db: d,
                output,
                audit_limit,
            }) => {
                let effective = d.as_ref().or(db.as_ref()).cloned();
                let db = resolve_db_or_latest(&effective)?;
                run_export(&db, output, *audit_limit)?;
            }
            Some(ReportCommands::Serve { db: d, server_port }) => {
                let effective = d.as_ref().or(db.as_ref()).cloned();
                let db = resolve_db_or_latest(&effective)?;
                run_report_serve(&db, &cli.listen, *server_port).await?;
            }
            Some(ReportCommands::List) => run_db_list()?,
        },
        Commands::Stat {
            db, json, command, ..
        } if command.is_empty() => {
            let db = resolve_db_or_latest(db)?;
            run_stat_query(&db, *json)?;
        }
        Commands::Top {
            db: Some(db),
            pid,
            comm,
            sort,
            view,
            interval,
            limit,
            count,
            once,
            plain: _,
        } => {
            let count = if *once { Some(1) } else { *count };
            let options = TopOptions {
                pid: *pid,
                comm: comm.clone(),
                sort: sort.clone(),
                view: view.clone(),
            };
            run_top_query(db, *interval, *limit, count, &options)?;
        }
        Commands::Discover { json } => {
            run_discover(*json)?;
        }
        // All remaining commands need the binary extractor.
        _ => {
            let binary_extractor = BinaryExtractor::new().await?;
            run_with_extractor(&cli, &binary_extractor).await?;
        }
    }

    Ok(())
}

async fn run_report_serve(
    db: &str,
    listen: &str,
    server_port: u16,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = view::MaterializedView::shared_bounded();
    let _server_handle =
        start_web_server_if_enabled(true, listen, server_port, view, Some(db.to_string()))
            .await
            .map_err(|e| std::io::Error::other(e.to_string()))?;

    shutdown_notify().notified().await;
    Ok(())
}

async fn run_with_extractor(
    cli: &Cli,
    binary_extractor: &BinaryExtractor,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    match &cli.command {
        Commands::Stat {
            binary_path,
            db,
            json,
            no_server,
            server_port,
            command,
        } => {
            if command.is_empty() {
                unreachable!("stat without a command is handled before binary extraction");
            }
            if *json {
                return Err("stat --json currently requires --db for clean JSON output".into());
            }
            let recorded_db = run_exec(
                binary_extractor,
                command,
                binary_path.as_deref(),
                configured_db_path(db),
                !*no_server,
                &cli.listen,
                *server_port,
                false,
            )
            .await
            .map_err(convert_runner_error)?;
            let db = recorded_db
                .as_deref()
                .ok_or("stat command did not produce a SQLite session database")?;
            run_stat_query(db, false)?;
        }
        Commands::Record {
            comm,
            pid,
            binary_path,
            db,
            no_server,
            server_port,
            command,
        } => {
            if !command.is_empty() {
                if comm.is_some() || pid.is_some() {
                    return Err(
                        "record accepts either -- <command> or -c/--comm/-p/--pid, not both".into(),
                    );
                }
                run_exec(
                    binary_extractor,
                    command,
                    binary_path.as_deref(),
                    configured_db_path(db),
                    !*no_server,
                    &cli.listen,
                    *server_port,
                    true,
                )
                .await
                .map_err(convert_runner_error)?;
                return Ok(());
            }
            if comm.is_none() && pid.is_none() {
                return Err(
                    "record requires either a command (`agentsight record -- claude`) or an attach target (`-c <comm>` / `-p <pid>`)"
                        .into(),
                );
            }
            let db_path = match configured_db_path(db) {
                Some(path) => Some(path),
                None => match default_session_db_path() {
                    Ok(path) => {
                        sources::session_db::cleanup_old_sessions();
                        Some(path)
                    }
                    Err(e) => {
                        print_record_session_db_error(e);
                        None
                    }
                },
            };
            let db_path_for_summary = db_path.clone();
            let cfg = TraceConfig {
                pid: *pid,
                comm: comm.clone(),
                stdio: pid.is_some(),
                binary_path: binary_path.clone(),
                db_path,
                server: !*no_server,
                server_listen: Some(cli.listen.clone()),
                server_port: *server_port,
                ..TraceConfig::for_record()
            };
            run_trace(binary_extractor, cfg)
                .await
                .map_err(convert_runner_error)?;
            if let Some(ref db) = db_path_for_summary {
                print_session_summary(db);
            }
        }
        Commands::Top {
            db: None,
            pid,
            comm,
            sort,
            view,
            interval,
            limit,
            count,
            once,
            plain,
        } => {
            let count = if *once { Some(1) } else { *count };
            let options = TopOptions {
                pid: *pid,
                comm: comm.clone(),
                sort: sort.clone(),
                view: view.clone(),
            };
            if !*plain && count.is_none() && interactive_terminal_available() {
                run_live_top_tui(binary_extractor, *interval, *limit, &options).await?;
            } else {
                run_live_top_query(binary_extractor, *interval, *limit, count, &options).await?;
            }
        }
        Commands::Debug(cmd) => match cmd {
            DebugCommands::Ssl {
                sse_merge,
                http_parser,
                http_raw_data,
                http_filter,
                disable_auth_removal,
                ssl_filter,
                quiet,
                server,
                server_port,
                binary_path,
                args,
            } => run_raw_ssl(
                binary_extractor,
                *sse_merge,
                *http_parser,
                *http_raw_data,
                http_filter,
                *disable_auth_removal,
                ssl_filter,
                *quiet,
                *server,
                &cli.listen,
                *server_port,
                binary_path.as_deref(),
                args,
            )
            .await
            .map_err(convert_runner_error)?,
            DebugCommands::Process {
                quiet,
                server,
                server_port,
                args,
            } => run_raw_process(
                binary_extractor,
                *quiet,
                *server,
                &cli.listen,
                *server_port,
                args,
            )
            .await
            .map_err(convert_runner_error)?,
            DebugCommands::Stdio {
                pid,
                uid,
                comm,
                all_fds,
                max_bytes,
                quiet,
                server,
                server_port,
            } => run_raw_stdio(
                binary_extractor,
                *pid,
                *uid,
                comm.as_deref(),
                *all_fds,
                *max_bytes,
                *quiet,
                *server,
                &cli.listen,
                *server_port,
            )
            .await
            .map_err(convert_runner_error)?,
            DebugCommands::Trace {
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
                db,
                quiet,
                server,
                server_port,
            } => {
                let cfg = TraceConfig {
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
                    server_listen: Some(cli.listen.clone()),
                    server_port: *server_port,
                    ..Default::default()
                };
                run_trace(binary_extractor, cfg)
                    .await
                    .map_err(convert_runner_error)?
            }
            DebugCommands::System {
                interval,
                pid,
                comm,
                no_children,
                cpu_threshold,
                memory_threshold,
                quiet,
                server,
                server_port,
            } => run_system(
                *interval,
                *pid,
                comm.as_deref(),
                !*no_children,
                *cpu_threshold,
                *memory_threshold,
                *quiet,
                *server,
                &cli.listen,
                *server_port,
            )
            .await
            .map_err(convert_runner_error)?,
        },
        _ => unreachable!("handled in run()"),
    }
    Ok(())
}
