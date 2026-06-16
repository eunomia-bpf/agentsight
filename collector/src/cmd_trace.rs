// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use futures::stream::StreamExt;

use crate::analyzers::{
    AuthHeaderRemover, HTTPFilter, HTTPParser, MaterializingAnalyzer, SSEProcessor, SSLFilter,
    TimestampNormalizer,
};
use crate::binary_extractor::BinaryExtractor;
use crate::binary_resolver::{
    binary_embeds_ssl, resolve_binary_path, resolve_container_binary_arg,
};
use crate::output::{
    print_event_json, print_trace_container_binary_resolved, print_trace_header,
    print_trace_shutdown, print_trace_ssl_binary_discovered, print_trace_start,
    print_web_server_error, print_web_server_start,
};
use crate::runners::common::runner_error_from_event;
use crate::runners::{
    AgentRunner, BinaryRunner, EventStream, ProcessRunner, Runner, RunnerError, SystemRunner,
};
use crate::server::WebServer;
use crate::sinks::OtelExporter;
use crate::sinks::sqlite::SqliteStore;
use crate::sources::proc::{PidSeed, ProcSnapshot};
use crate::view::{MaterializedView, SharedMaterializedView, process_select};

pub(crate) const DEFAULT_SERVER_LISTEN: &str = "127.0.0.1";
pub(crate) const DEFAULT_RECORD_STDIO_MAX_BYTES: u32 = 65_536;

const DEFAULT_SSL_FILTER: &str = "data=0\\r\\n\\r\\n";
const DEFAULT_HTTP_FILTER: &str = "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=";

pub(crate) struct StartedWebServer {
    pub(crate) url: String,
    pub(crate) _handle: tokio::task::JoinHandle<()>,
}

/// Configuration for exporting GenAI spans to an OpenTelemetry Collector.
#[derive(Clone)]
pub(crate) struct OtelConfig {
    /// OTLP/HTTP base endpoint; `None` falls back to env vars / localhost.
    pub(crate) endpoint: Option<String>,
    /// Opt-in: include prompt/completion content in spans.
    pub(crate) capture_content: bool,
}

#[derive(Default)]
pub(crate) struct TraceConfig {
    pub(crate) ssl: bool,
    pub(crate) pid: Option<u32>,
    pub(crate) session_id: Option<u32>,
    pub(crate) ssl_uid: Option<u32>,
    pub(crate) comm: Option<String>,
    pub(crate) ssl_filter: Vec<String>,
    pub(crate) ssl_handshake: bool,
    pub(crate) ssl_http: bool,
    pub(crate) ssl_raw_data: bool,
    pub(crate) process: bool,
    pub(crate) process_seed_pids: Vec<PidSeed>,
    pub(crate) stdio: bool,
    pub(crate) stdio_uid: Option<u32>,
    pub(crate) stdio_comm: Option<String>,
    pub(crate) stdio_all_fds: bool,
    pub(crate) stdio_max_bytes: u32,
    pub(crate) duration: Option<u32>,
    pub(crate) mode: Option<u32>,
    pub(crate) system: bool,
    pub(crate) system_interval: u64,
    pub(crate) http_filter: Vec<String>,
    pub(crate) disable_auth_removal: bool,
    pub(crate) otel: Option<OtelConfig>,
    /// SSL binary path; may be a `docker://` ref that `run_trace` resolves in place.
    pub(crate) binary_path: Option<String>,
    pub(crate) db_path: Option<String>,
    pub(crate) quiet: bool,
    pub(crate) server: bool,
    pub(crate) server_listen: Option<String>,
    pub(crate) server_port: u16,
}

impl TraceConfig {
    pub(crate) fn for_record() -> Self {
        Self {
            ssl: true,
            ssl_filter: vec![DEFAULT_SSL_FILTER.to_string()],
            ssl_http: true,
            process: true,
            stdio_max_bytes: DEFAULT_RECORD_STDIO_MAX_BYTES,
            system: true,
            system_interval: 2,
            http_filter: vec![DEFAULT_HTTP_FILTER.to_string()],
            quiet: true,
            ..Default::default()
        }
    }
}

pub(crate) fn configure_ssl_runner(
    runner: BinaryRunner,
    ssl_filter: &[String],
    ssl_http: bool,
    ssl_raw_data: bool,
    http_filter: &[String],
    disable_auth_removal: bool,
) -> BinaryRunner {
    let mut runner = runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    if !ssl_filter.is_empty() {
        runner = runner.add_analyzer(Box::new(SSLFilter::with_patterns(ssl_filter.to_vec())));
    }
    if ssl_http {
        runner = add_http_analyzers(runner, ssl_raw_data, http_filter, disable_auth_removal);
    }
    runner
}

pub(crate) fn build_stdio_args(
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

pub(crate) fn prepare_process_seeds(cfg: &mut TraceConfig) -> Result<(), RunnerError> {
    if !cfg.process || !cfg.process_seed_pids.is_empty() {
        return Ok(());
    }

    let snapshot = ProcSnapshot::collect()
        .map_err(|e| RunnerError::from(format!("failed to collect /proc snapshot: {}", e)))?;
    cfg.process_seed_pids = process_select::process_seeds(
        &snapshot,
        cfg.session_id,
        cfg.pid,
        cfg.comm.as_deref(),
        cfg.mode.unwrap_or(1) == 1,
    );
    Ok(())
}

pub(crate) fn build_trace_agent_with_view(
    binary_extractor: &BinaryExtractor,
    cfg: &TraceConfig,
    view: SharedMaterializedView,
) -> Result<AgentRunner, RunnerError> {
    let mut agent = AgentRunner::new();

    if cfg.ssl {
        let mut ssl_runner = BinaryRunner::ssl(binary_extractor.get_sslsniff_path());
        let ssl_args = build_ssl_args(cfg);
        if !ssl_args.is_empty() {
            ssl_runner = ssl_runner.with_args(&ssl_args);
        }
        ssl_runner = configure_ssl_runner(
            ssl_runner,
            &cfg.ssl_filter,
            cfg.ssl_http,
            cfg.ssl_raw_data,
            &cfg.http_filter,
            cfg.disable_auth_removal,
        );
        agent = agent.add_runner(Box::new(ssl_runner));
    }

    if cfg.stdio {
        let pid_filter = cfg
            .pid
            .ok_or_else(|| RunnerError::from("stdio capture currently requires --pid"))?;
        let mut stdio_runner = BinaryRunner::stdio(binary_extractor.get_stdiocap_path()?);
        let mut stdio_args = build_stdio_args(
            pid_filter,
            cfg.stdio_uid,
            cfg.stdio_comm.as_deref(),
            cfg.stdio_all_fds,
            cfg.stdio_max_bytes,
        );
        if let Some(session_filter) = cfg.session_id {
            stdio_args.extend(["--session".to_string(), session_filter.to_string()]);
        }

        stdio_runner = stdio_runner.with_args(&stdio_args);
        stdio_runner = stdio_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(stdio_runner));
    }

    if cfg.process {
        let mut process_runner =
            ProcessRunner::from_binary_extractor(binary_extractor.get_process_path());

        let process_args = build_process_args(cfg);
        if !process_args.is_empty() {
            process_runner = process_runner.with_args(&process_args);
        }
        process_runner = process_runner.with_seed_pids(&cfg.process_seed_pids);
        process_runner = process_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(process_runner));
    }

    if cfg.system {
        let mut system_runner = SystemRunner::new().interval(cfg.system_interval);

        if let Some(comm_filter) = cfg.comm.as_deref() {
            system_runner = system_runner.comm(comm_filter);
        }
        if let Some(pid_filter) = cfg.pid {
            system_runner = system_runner.pid(pid_filter);
        }
        if let Some(session_filter) = cfg.session_id {
            system_runner = system_runner.session(session_filter);
        }
        system_runner = system_runner.add_analyzer(Box::new(TimestampNormalizer::new()));

        agent = agent.add_runner(Box::new(system_runner));
    }

    if !cfg.ssl && !cfg.process && !cfg.stdio && !cfg.system {
        return Err(
            "At least one monitoring type must be enabled (--ssl, --process, --stdio, or --system)"
                .into(),
        );
    }

    let mut materializer = MaterializingAnalyzer::with_view(view);
    if let Some(path) = cfg.db_path.as_deref() {
        materializer =
            materializer.add_view_sink(Box::new(SqliteStore::open(path).map_err(|e| {
                RunnerError::from(format!("failed to open SQLite database '{}': {}", path, e))
            })?));
    }
    if let Some(otel_config) = &cfg.otel {
        materializer = materializer.add_view_sink(Box::new(OtelExporter::new(
            otel_config.endpoint.clone(),
            otel_config.capture_content,
        )));
    }
    agent = agent.add_global_analyzer(Box::new(materializer));

    Ok(agent)
}

fn build_ssl_args(cfg: &TraceConfig) -> Vec<String> {
    let mut args = Vec::new();
    if cfg.session_id.is_none() {
        if let Some(pid) = cfg.pid {
            args.extend(["-p".to_string(), pid.to_string()]);
        }
    }
    if let Some(session) = cfg.session_id {
        args.extend(["--session".to_string(), session.to_string()]);
    }
    if let Some(uid) = cfg.ssl_uid {
        args.extend(["-u".to_string(), uid.to_string()]);
    }
    // Skip --comm for sslsniff when --binary-path is set: SSL traffic runs on
    // "HTTP Client" thread, not the process name, so comm filter drops everything.
    if cfg.binary_path.is_none() {
        if let Some(comm) = cfg.comm.as_deref() {
            args.extend(["-c".to_string(), comm.to_string()]);
        }
    }
    if cfg.ssl_handshake {
        args.push("--handshake".to_string());
    }
    if let Some(path) = cfg.binary_path.as_deref() {
        args.extend(["--binary-path".to_string(), path.to_string()]);
    }
    args
}

fn build_process_args(cfg: &TraceConfig) -> Vec<String> {
    let mut args = Vec::new();
    if let Some(pid) = cfg.pid {
        args.extend(["-p".to_string(), pid.to_string()]);
    }
    if let Some(session) = cfg.session_id {
        args.extend(["--session".to_string(), session.to_string()]);
    }
    if let Some(comm) = cfg.comm.as_deref() {
        args.extend(["-c".to_string(), comm.to_string()]);
    }
    if let Some(duration) = cfg.duration {
        args.extend(["-d".to_string(), duration.to_string()]);
    }
    if let Some(mode) = cfg.mode {
        args.extend(["-m".to_string(), mode.to_string()]);
    }
    args
}

/// Trace monitoring with configurable runners and analyzers
pub(crate) async fn run_trace(
    binary_extractor: &BinaryExtractor,
    mut cfg: TraceConfig,
) -> Result<(), RunnerError> {
    print_trace_header();

    // A `--binary-path docker://<container>` (or `docker:<container>`) reference
    // is translated in Rust to an explicit host-side SSL attach target. The C
    // sslsniff binary only consumes that path; it does not scan container
    // process maps itself.
    if let Some((reference, resolved)) =
        resolve_container_binary_arg(cfg.binary_path.as_deref()).map_err(RunnerError::from)?
    {
        print_trace_container_binary_resolved(&reference, &resolved);
        cfg.binary_path = Some(resolved);
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
            print_trace_ssl_binary_discovered(cfg.comm.as_deref().unwrap_or(""), &p);
            cfg.binary_path = Some(p);
        }
    }

    let enable_server = cfg.server;
    let server_listen = cfg
        .server_listen
        .as_deref()
        .unwrap_or(DEFAULT_SERVER_LISTEN)
        .to_string();
    let server_port = cfg.server_port;

    prepare_process_seeds(&mut cfg)?;
    let live_view = MaterializedView::shared_bounded();
    let mut agent = build_trace_agent_with_view(binary_extractor, &cfg, live_view.clone())?;

    print_trace_start(agent.runner_count(), agent.analyzer_count());

    // Start web server if enabled
    let _server_handle =
        start_web_server_if_enabled(enable_server, &server_listen, server_port, live_view, None)
            .await
            .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;

    let mut stream = agent.run().await?;

    // Drive the stream so the analyzer chain (file logging, storage, etc.) runs.
    drive_stream_until_shutdown(&mut stream, !cfg.quiet).await?;
    drop(stream);
    drop(agent);

    Ok(())
}

pub(crate) async fn start_web_server_if_enabled(
    enable_server: bool,
    listen: &str,
    port: u16,
    view: SharedMaterializedView,
    db_path: Option<String>,
) -> Result<Option<StartedWebServer>, Box<dyn std::error::Error>> {
    if !enable_server {
        return Ok(None);
    }

    let listen = if listen.trim().is_empty() {
        DEFAULT_SERVER_LISTEN
    } else {
        listen.trim()
    };
    let addr = format!("{}:{}", listen, port)
        .parse()
        .map_err(|e| format!("Invalid server address: {}", e))?;
    let web_server = WebServer::new_with_db_path(view, db_path)
        .map_err(|e| format!("Failed to create web server: {}", e))?;

    let host = if listen == "0.0.0.0" || listen == "::" {
        "127.0.0.1"
    } else {
        listen
    };
    let url = format!("http://{}:{}/", host, port);
    print_web_server_start(&url);

    let server_handle = tokio::spawn(async move {
        if let Err(e) = web_server.start(addr).await {
            print_web_server_error(e);
        }
    });

    // Give the server a moment to start
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    if server_handle.is_finished() {
        return Err(Box::new(std::io::Error::other(
            "web server exited during startup",
        )));
    }

    Ok(Some(StartedWebServer {
        url,
        _handle: server_handle,
    }))
}

pub(crate) async fn drive_stream_until_shutdown(
    stream: &mut EventStream,
    print_events: bool,
) -> Result<(), RunnerError> {
    let shutdown = crate::shutdown_notify();
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(event) => {
                        if let Some(error) = runner_error_from_event(&event) {
                            return Err(error);
                        }
                        if print_events {
                            print_event_json(&event);
                        }
                    }
                    None => break,
                }
            }
            _ = shutdown.notified() => {
                print_trace_shutdown();
                break;
            }
        }
    }
    Ok(())
}

pub(crate) async fn drain_stream_for(
    stream: &mut EventStream,
    duration: tokio::time::Duration,
) -> Result<(), RunnerError> {
    let shutdown = crate::shutdown_notify();
    let deadline = tokio::time::sleep(duration);
    tokio::pin!(deadline);
    loop {
        tokio::select! {
            maybe_event = stream.next() => {
                match maybe_event {
                    Some(event) => {
                        if let Some(error) = runner_error_from_event(&event) {
                            return Err(error);
                        }
                    }
                    None => break,
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
    Ok(())
}

pub(crate) fn convert_runner_error(e: RunnerError) -> Box<dyn std::error::Error + Send + Sync> {
    Box::new(std::io::Error::other(e.to_string()))
}

pub(crate) fn add_http_analyzers(
    runner: BinaryRunner,
    include_raw_data: bool,
    http_filter: &[String],
    disable_auth_removal: bool,
) -> BinaryRunner {
    let mut runner = runner.add_analyzer(Box::new(SSEProcessor::new_with_timeout(30000)));
    let parser = if include_raw_data {
        HTTPParser::new()
    } else {
        HTTPParser::new().disable_raw_data()
    };
    runner = runner.add_analyzer(Box::new(parser));
    if !http_filter.is_empty() {
        runner = runner.add_analyzer(Box::new(HTTPFilter::with_patterns(http_filter.to_vec())));
    }
    if !disable_auth_removal {
        runner = runner.add_analyzer(Box::new(AuthHeaderRemover::new()));
    }
    runner
}

pub(crate) async fn run_debug_runner<R: Runner>(
    runner: R,
    quiet: bool,
    enable_server: bool,
    server_listen: &str,
    server_port: u16,
) -> Result<(), RunnerError> {
    let live_view = MaterializedView::shared_bounded();
    let mut runner = runner.add_analyzer(Box::new(MaterializingAnalyzer::with_view(
        live_view.clone(),
    )));
    let _server_handle =
        start_web_server_if_enabled(enable_server, server_listen, server_port, live_view, None)
            .await
            .map_err(|e| RunnerError::from(format!("Failed to start server: {}", e)))?;
    let mut stream = runner.run().await?;
    drive_stream_until_shutdown(&mut stream, !quiet).await?;
    Ok(())
}
