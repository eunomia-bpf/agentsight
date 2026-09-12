// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

#![allow(clippy::too_many_arguments)]

use clap::{Parser, Subcommand};
use std::collections::VecDeque;
use std::io::{IsTerminal, Write};
use std::path::PathBuf;
use std::sync::{
    Arc, Mutex, OnceLock,
    atomic::{AtomicBool, Ordering},
};
use tokio::signal;
use tokio::sync::Notify;

pub(crate) use agentsight_capture::{
    analyzers, binary_extractor, binary_resolver, event, model, runners, sinks, text,
};

mod cli_db;
mod cmd_bind;
mod cmd_debug;
mod cmd_exec;
mod cmd_monitor;
mod cmd_perf_live;
mod cmd_perf_tui;
mod cmd_trace;
mod cmd_tui_record;
mod output;
mod server;
mod sources;
mod state;
mod view;

use analyzers::{print_global_http_filter_metrics, print_global_ssl_filter_metrics};
use binary_extractor::BinaryExtractor;
use cli_db::{
    configured_db_path, run_audit_query, run_db_summary, run_export, run_prompts_query,
    run_token_query,
};
use cmd_bind::run_bind;
use cmd_exec::{default_session_db_path, print_session_summary, run_exec};
use cmd_monitor::{install_monitor_service, run_monitor};
use cmd_perf_live::{run_live_top_query, start_live_ebpf_capture};
use cmd_perf_tui::run_live_top_tui;
use cmd_trace::{TraceConfig, convert_runner_error, run_trace, start_web_server_if_enabled};
use output::TopOptions;
use output::{print_record_session_db_error, print_report_local_sessions_warning};
use server::container_bridge::run_stdio_bridge;
use sources::session_db::{latest_session_db, run_db_list};

static SHUTDOWN_REQUESTED: AtomicBool = AtomicBool::new(false);
static SHUTDOWN_NOTIFY: OnceLock<Arc<Notify>> = OnceLock::new();
static TUI_DIAGNOSTICS: OnceLock<Mutex<VecDeque<String>>> = OnceLock::new();

struct TuiDiagnosticWriter;

impl Write for TuiDiagnosticWriter {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        for line in String::from_utf8_lossy(buf)
            .lines()
            .map(str::trim)
            .filter(|line| !line.is_empty())
        {
            push_tui_diagnostic(line);
        }
        Ok(buf.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

fn push_tui_diagnostic(message: &str) {
    const MAX: usize = 8;
    let diagnostics = TUI_DIAGNOSTICS.get_or_init(|| Mutex::new(VecDeque::new()));
    let Ok(mut diagnostics) = diagnostics.lock() else {
        return;
    };
    if diagnostics.back().is_some_and(|last| last == message) {
        return;
    }
    diagnostics.push_back(message.to_string());
    while diagnostics.len() > MAX {
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
    let mut out: Vec<_> = diagnostics.iter().rev().take(limit).cloned().collect();
    out.reverse();
    out
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
    std::io::stdin().is_terminal() && std::io::stdout().is_terminal()
}

fn top_uses_tui(plain: bool, interactive: bool) -> bool {
    !plain && interactive
}

fn command_uses_top_tui(cli: &Cli) -> bool {
    matches!(&cli.command, Commands::Top { plain, .. } if top_uses_tui(*plain, interactive_terminal_available()))
}

fn init_logging(suppress_terminal_output: bool) {
    let mut builder = env_logger::Builder::from_default_env();
    builder.filter_level(log::LevelFilter::Warn);
    builder.filter_module(
        "headless_chrome::browser::transport",
        log::LevelFilter::Error,
    );
    if suppress_terminal_output {
        builder.target(env_logger::Target::Pipe(Box::new(TuiDiagnosticWriter)));
    }
    let _ = builder.try_init();
}

#[cfg(unix)]
async fn setup_signal_handler(suppress_terminal_output: bool) {
    let mut sigint = signal::unix::signal(signal::unix::SignalKind::interrupt())
        .expect("Failed to install SIGINT handler");
    let mut sigterm = signal::unix::signal(signal::unix::SignalKind::terminate())
        .expect("Failed to install SIGTERM handler");
    tokio::spawn(async move {
        tokio::select! { _ = sigint.recv() => {}, _ = sigterm.recv() => {} }
        notify_shutdown(suppress_terminal_output);
    });
}

#[cfg(not(unix))]
async fn setup_signal_handler(suppress_terminal_output: bool) {
    tokio::spawn(async move {
        if signal::ctrl_c().await.is_ok() {
            notify_shutdown(suppress_terminal_output);
        }
    });
}

fn notify_shutdown(suppress_terminal_output: bool) {
    if !suppress_terminal_output {
        println!("\n\nReceived shutdown signal, shutting down...");
        print_global_http_filter_metrics();
        print_global_ssl_filter_metrics();
    }
    SHUTDOWN_REQUESTED.store(true, Ordering::Relaxed);
    shutdown_notify().notify_waiters();
}

#[derive(Parser)]
#[command(
    author,
    version,
    about = "AgentSight: top/record/report for AI agent runs.\n\n\
             Common flow:\n\
               sudo agentsight record -- claude\n\
               agentsight top\n\
               agentsight report\n\
               agentsight report prompts --json\n\n\
             top uses eBPF when available and falls back without sudo;\n\
             record keeps the monitored agent unprivileged while elevating only the probes."
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
    /// Render repository file evolution from local agent sessions.
    Vis {
        /// Git worktree to visualize.
        #[arg(default_value = ".")]
        path: PathBuf,
        /// Output path; repeat for HTML, SVG, PNG, GIF, and MP4.
        #[arg(short = 'o', long = "output", default_value = agentvis::DEFAULT_OUTPUT)]
        outputs: Vec<PathBuf>,
        /// Scan every local session and retain operations targeting this repository.
        #[arg(long)]
        global: bool,
        /// Compact GIF/MP4 uniformly by action to this duration, or use `full`.
        #[arg(long, default_value = "30s")]
        compact_rate: agentvis::CompactRate,
    },
    /// Bind this machine to the hosted AgentSight app.
    Bind {
        /// Print a QR code containing the binding URL.
        #[arg(long)]
        qr: bool,
        /// Print the binding URL without opening a browser.
        #[arg(long)]
        no_open: bool,
        /// Local API port used while this device is bound.
        #[arg(long, default_value_t = 7395)]
        server_port: u16,
        /// SQLite capture to serve instead of live agent sessions.
        #[arg(long)]
        db: Option<String>,
        /// Static AgentSight app to open (official hosted app by default).
        #[arg(long, default_value = "https://app.agentsight.us/")]
        app_url: String,
        /// Browser-reachable Node base URL (defaults to http://LISTEN:PORT).
        #[arg(long)]
        endpoint: Option<String>,
        /// Docker container whose local AgentSight bridge should be included.
        #[arg(long = "docker-container", value_name = "NAME")]
        docker_containers: Vec<String>,
    },
    /// Internal JSONL session bridge used through docker exec.
    #[command(hide = true)]
    Bridge,
    /// Show live agent sessions.
    Top {
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
        #[arg(short = 'i', long, default_value_t = 2)]
        interval: u64,
        /// Rows per section
        #[arg(short = 'n', long, default_value_t = 10)]
        limit: usize,
        /// Number of refreshes before exiting
        #[arg(long)]
        count: Option<u32>,
        /// Render one refresh and exit
        #[arg(long)]
        once: bool,
        /// Use plain table output instead of the interactive TUI
        #[arg(long)]
        plain: bool,
    },
    /// Long-running bounded trace monitor for matched local agent sessions.
    Monitor {
        #[command(subcommand)]
        command: Option<MonitorCommands>,
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
        /// Binary path or container ref to monitor (e.g., /usr/bin/node, docker://name, k8s://ns/pod/container)
        #[arg(long)]
        binary_path: Option<String>,
        /// SQLite database path for view snapshots
        #[arg(long)]
        db: Option<String>,
        /// Disable the web server
        #[arg(long)]
        no_server: bool,
        /// Server port for the web UI
        #[arg(long, default_value_t = 7395)]
        server_port: u16,
        /// Optional command to launch and trace. Use -c/--comm or -p/--pid instead to attach.
        #[arg(last = true)]
        command: Vec<String>,
    },
    /// Query and report on recorded sessions: summary, tokens, audit, prompts, export, list.
    /// Defaults to summary when no subcommand is given.
    Report {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Read agent-native Claude/Codex/Gemini sessions instead of a saved DB
        #[arg(long)]
        local: bool,
        #[command(subcommand)]
        sub: Option<ReportCommands>,
    },
    /// Low-level debugging tools: print raw streams and optionally serve a live view
    Debug(cmd_debug::DebugCli),
}

#[derive(Subcommand)]
enum ReportCommands {
    /// Session summary: what the agent did, tokens, processes, files
    Summary {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Read agent-native Claude/Codex/Gemini sessions
        #[arg(long)]
        local: bool,
    },
    /// Query token usage from a saved DB or local agent sessions
    Token {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Grouping key: model, provider, comm, pid, dir (aliases: cwd, directory)
        #[arg(long, default_value = "model")]
        group_by: String,
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Query audit events from a saved DB or local agent sessions
    Audit {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Audit type: llm, process, file
        #[arg(long)]
        audit_type: Option<String>,
        /// Maximum rows
        #[arg(long, default_value_t = 100)]
        limit: usize,
        /// Emit JSON output
        #[arg(long)]
        json: bool,
    },
    /// Show captured LLM prompts and responses when observable
    Prompts {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Maximum rows
        #[arg(long, default_value_t = 20)]
        limit: usize,
        /// Emit full request/response JSON
        #[arg(long)]
        json: bool,
    },
    /// Export a web/demo snapshot from a saved DB or local agent sessions
    Export {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Output snapshot path, or '-' for stdout
        #[arg(short, long)]
        output: String,
        /// Maximum audit events to include
        #[arg(long, default_value_t = 10_000)]
        audit_limit: usize,
    },
    /// Serve the web UI for a saved SQLite session or local agent sessions
    Serve {
        /// SQLite database path (defaults to latest agentsight-*.db, then local agent sessions)
        #[arg(long)]
        db: Option<String>,
        /// Server port for the web UI
        #[arg(long, default_value_t = 7395)]
        server_port: u16,
    },
    /// List session databases
    List,
}

#[derive(Subcommand)]
enum MonitorCommands {
    /// Install and start monitor as a systemd user service.
    InstallService,
}

#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        eprintln!("Error: {e}");
        std::process::exit(1);
    }
}

async fn run() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let cli = Cli::parse();
    let suppress_terminal_output = command_uses_top_tui(&cli);
    init_logging(suppress_terminal_output);
    if !matches!(&cli.command, Commands::Vis { .. }) {
        setup_signal_handler(suppress_terminal_output).await;
    }

    match &cli.command {
        Commands::Vis {
            path,
            outputs,
            global,
            compact_rate,
        } => agentvis::run_vis(path, outputs, *global, *compact_rate)?,
        Commands::Bind {
            qr,
            no_open,
            server_port,
            db,
            app_url,
            endpoint,
            docker_containers,
        } => {
            run_bind(
                &cli.listen,
                *server_port,
                *no_open,
                *qr,
                configured_db_path(db),
                app_url,
                endpoint.as_deref(),
                docker_containers,
            )
            .await?
        }
        Commands::Bridge => run_stdio_bridge().await?,
        Commands::Report { db, local, sub } => run_report(db, *local, sub, &cli.listen).await?,
        Commands::Monitor { command } => match command {
            None => run_monitor().await?,
            Some(MonitorCommands::InstallService) => install_monitor_service()?,
        },
        Commands::Top {
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
            let options = TopOptions {
                pid: *pid,
                comm: comm.clone(),
                sort: sort.clone(),
                view: view.clone(),
            };
            let capture = start_live_ebpf_capture(&options).await;
            let count = if *once { Some(1) } else { *count };
            let result = if top_uses_tui(*plain, interactive_terminal_available()) {
                run_live_top_tui(Some(&capture), *interval, *limit, count, &options)
            } else {
                run_live_top_query(Some(&capture), *interval, *limit, count, &options)
            };
            capture.stop();
            result?;
        }
        _ => {
            let binary_extractor = BinaryExtractor::new().await?;
            run_with_extractor(&cli, &binary_extractor).await?;
        }
    }
    Ok(())
}

async fn run_report(
    db: &Option<String>,
    local: bool,
    sub: &Option<ReportCommands>,
    listen: &str,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    match sub {
        None | Some(ReportCommands::Summary { .. }) => {
            let (db, local) = match sub {
                Some(ReportCommands::Summary { db, local }) => (db, *local),
                _ => (db, local),
            };
            run_db_summary(report_db_or_local(db, local).as_deref())?;
        }
        Some(ReportCommands::Token {
            db: own,
            group_by,
            json,
        }) => {
            let db = own.as_ref().or(db.as_ref()).cloned();
            run_token_query(report_db_or_local(&db, local).as_deref(), group_by, *json)?;
        }
        Some(ReportCommands::Audit {
            db: own,
            audit_type,
            limit,
            json,
        }) => {
            let db = own.as_ref().or(db.as_ref()).cloned();
            run_audit_query(
                report_db_or_local(&db, local).as_deref(),
                audit_type.as_deref(),
                *limit,
                *json,
            )?;
        }
        Some(ReportCommands::Prompts {
            db: own,
            limit,
            json,
        }) => {
            let db = own.as_ref().or(db.as_ref()).cloned();
            run_prompts_query(report_db_or_local(&db, local).as_deref(), *limit, *json)?;
        }
        Some(ReportCommands::Export {
            db: own,
            output,
            audit_limit,
        }) => {
            let db = own.as_ref().or(db.as_ref()).cloned();
            run_export(
                report_db_or_local(&db, local).as_deref(),
                output,
                *audit_limit,
            )?;
        }
        Some(ReportCommands::Serve {
            db: own,
            server_port,
        }) => {
            let db = own.as_ref().or(db.as_ref()).cloned();
            run_report_serve(
                report_db_or_local(&db, local).as_deref(),
                listen,
                *server_port,
            )
            .await?;
        }
        Some(ReportCommands::List) => run_db_list()?,
    }
    Ok(())
}

async fn run_report_serve(
    db: Option<&str>,
    listen: &str,
    server_port: u16,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let view = view::MaterializedView::shared_bounded();
    let _server =
        start_web_server_if_enabled(true, listen, server_port, view, db.map(str::to_string))
            .await
            .map_err(|e| std::io::Error::other(e.to_string()))?;
    shutdown_notify().notified().await;
    Ok(())
}

fn report_db_or_local(db: &Option<String>, force_local: bool) -> Option<String> {
    if force_local {
        return None;
    }
    if let Some(db) = db {
        return Some(db.clone());
    }
    let latest = latest_session_db();
    if latest.is_none() {
        print_report_local_sessions_warning();
    }
    latest
}

async fn run_with_extractor(
    cli: &Cli,
    binary_extractor: &BinaryExtractor,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    match &cli.command {
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
                return Err("record requires either a command (`agentsight record -- claude`) or an attach target (`-c <comm>` / `-p <pid>`)".into());
            }
            let db_path = configured_db_path(db).or_else(|| match default_session_db_path() {
                Ok(path) => Some(path),
                Err(e) => {
                    print_record_session_db_error(e);
                    None
                }
            });
            let summary_db = db_path.clone();
            run_trace(
                binary_extractor,
                TraceConfig {
                    pid: *pid,
                    comm: comm.clone(),
                    stdio: pid.is_some(),
                    binary_path: binary_path.clone(),
                    db_path,
                    server: !*no_server,
                    server_listen: Some(cli.listen.clone()),
                    server_port: *server_port,
                    ..TraceConfig::for_record()
                },
            )
            .await
            .map_err(convert_runner_error)?;
            if let Some(db) = summary_db.as_deref() {
                print_session_summary(db);
            }
        }
        Commands::Debug(debug) => cmd_debug::run(debug, binary_extractor, &cli.listen)
            .await
            .map_err(convert_runner_error)?,
        _ => unreachable!("handled in run()"),
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{Cli, Commands, top_uses_tui};

    #[test]
    fn default_interactive_top_uses_tui() {
        assert!(top_uses_tui(false, true));
    }

    #[test]
    fn only_plain_or_non_tty_disable_tui() {
        assert!(!top_uses_tui(true, true));
        assert!(!top_uses_tui(false, false));
    }

    #[test]
    fn top_rejects_saved_db_mode() {
        assert!(
            <Cli as clap::Parser>::try_parse_from(["agentsight", "top", "--db", "run.db"]).is_err()
        );
    }

    #[test]
    fn bind_cli_keeps_existing_commands_unchanged() {
        let cli = <Cli as clap::Parser>::try_parse_from([
            "agentsight",
            "bind",
            "--qr",
            "--no-open",
            "--server-port",
            "7444",
            "--listen",
            "0.0.0.0",
            "--db",
            "capture.db",
            "--app-url",
            "https://console.example/ui/",
            "--endpoint",
            "https://node.example:7444",
            "--docker-container",
            "ebpfos-dev",
            "--docker-container",
            "research-agent",
        ])
        .unwrap();
        assert_eq!(cli.listen, "0.0.0.0");
        match cli.command {
            Commands::Bind {
                qr,
                no_open,
                server_port,
                db,
                app_url,
                endpoint,
                docker_containers,
            } => {
                assert!(qr && no_open);
                assert_eq!(server_port, 7444);
                assert_eq!(db.as_deref(), Some("capture.db"));
                assert_eq!(app_url, "https://console.example/ui/");
                assert_eq!(endpoint.as_deref(), Some("https://node.example:7444"));
                assert_eq!(docker_containers, ["ebpfos-dev", "research-agent"]);
            }
            _ => panic!("expected bind command"),
        }
    }
}
