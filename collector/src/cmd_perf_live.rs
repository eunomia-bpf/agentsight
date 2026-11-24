// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

#[cfg(not(target_os = "windows"))]
use crate::analyzers::TimestampNormalizer;
#[cfg(not(target_os = "windows"))]
use crate::binary_extractor::BinaryExtractor;
#[cfg(target_os = "linux")]
use crate::cmd_exec::sudo_cached;
use crate::event::Event;
use crate::model::SnapshotOptions;
use crate::output::{TopOptions, clear_screen, print_agent_top};
#[cfg(not(target_os = "windows"))]
use crate::runners::ProcessRunner;
use crate::runners::Runner;
use crate::sources::proc as procfs;
#[cfg(any(test, not(target_os = "windows")))]
use crate::state::ensure_agentsight_state_dir;
use crate::view::MaterializedView;
use crate::view::live_top::{LiveCaptureSnapshot, LiveView};
#[cfg(not(target_os = "windows"))]
use crate::view::process_select;
use crate::view::top::sort_agent_rows;
#[cfg(target_os = "windows")]
use agentsight_capture_core::runners::{
    WindowsEtwProcessRunner, current_process_token_is_elevated,
};
use futures::StreamExt;
use std::io::{self, Write};
use std::sync::atomic::AtomicBool;
#[cfg(target_os = "windows")]
use std::sync::atomic::Ordering;
use std::sync::{Arc, Mutex};
use std::time::Duration;

#[cfg(any(test, target_os = "linux"))]
const LIVE_EBPF_ROOT_NOTE: &str = "live eBPF process capture enabled";
#[cfg(any(test, target_os = "linux"))]
const LIVE_EBPF_SUDO_NOTE: &str = "live eBPF process capture enabled via sudo";
#[cfg(any(test, target_os = "linux"))]
const LIVE_EBPF_UNAVAILABLE_NOTE: &str = "no eBPF: showing process snapshots and agent-native sessions only (run with sudo or configure passwordless sudo for kernel probes)";
#[cfg(all(not(target_os = "linux"), any(test, not(target_os = "windows"))))]
const LIVE_EBPF_UNSUPPORTED_NOTE: &str = "no eBPF: live kernel probes are Linux-only; showing process snapshots and agent-native sessions only";
#[cfg(target_os = "windows")]
const WINDOWS_ETW_REQUIRES_PID_NOTE: &str =
    "no Windows ETW: pass --pid <pid> from an elevated terminal to capture short-lived descendants";
#[cfg(target_os = "windows")]
const WINDOWS_ETW_REQUIRES_ELEVATION_NOTE: &str = "no Windows ETW: capture requires an already-elevated terminal; showing process snapshots and agent-native sessions only";

#[cfg(target_os = "windows")]
const LIVE_CAPTURE_BACKEND_LABEL: &str = "Windows ETW";
#[cfg(target_os = "windows")]
const LIVE_CAPTURE_TRACE_TOKEN: &str = "etw";
#[cfg(not(target_os = "windows"))]
const LIVE_CAPTURE_BACKEND_LABEL: &str = "eBPF";
#[cfg(not(target_os = "windows"))]
const LIVE_CAPTURE_TRACE_TOKEN: &str = "ebpf";

#[cfg(target_os = "windows")]
const ETW_CAPTURE_STOP_TIMEOUT: Duration = Duration::from_secs(10);

struct LiveCaptureState {
    view: MaterializedView,
    parse_errors: u64,
    diagnostic_count: u64,
    etw_decode_errors: u64,
    etw_records_drained: u64,
    etw_queue_dropped_records: u64,
    etw_callback_errors: u64,
    etw_stop_errors: u64,
    etw_native_events_lost: u64,
    etw_native_log_buffers_lost: u64,
    etw_native_realtime_buffers_lost: u64,
    etw_native_query_errors: u64,
    etw_pending_records_evicted: u64,
    etw_provisional_capacity_dropped: u64,
    etw_provisional_tracker_evicted: u64,
    etw_tracker_instances_evicted: u64,
    etw_tracker_ambiguous_parents_evicted: u64,
    etw_tracker_members_evicted_without_exit: u64,
    consumer_stopped: bool,
    consumer_status: Option<String>,
    consumer_stop_count: u64,
    backend_label: &'static str,
    trace_token: &'static str,
    root_pid: Option<u32>,
    root_start_identity: Option<u64>,
    root_comm: Option<String>,
    root_exited: bool,
}

impl Default for LiveCaptureState {
    fn default() -> Self {
        Self {
            view: MaterializedView::bounded(),
            parse_errors: 0,
            diagnostic_count: 0,
            etw_decode_errors: 0,
            etw_records_drained: 0,
            etw_queue_dropped_records: 0,
            etw_callback_errors: 0,
            etw_stop_errors: 0,
            etw_native_events_lost: 0,
            etw_native_log_buffers_lost: 0,
            etw_native_realtime_buffers_lost: 0,
            etw_native_query_errors: 0,
            etw_pending_records_evicted: 0,
            etw_provisional_capacity_dropped: 0,
            etw_provisional_tracker_evicted: 0,
            etw_tracker_instances_evicted: 0,
            etw_tracker_ambiguous_parents_evicted: 0,
            etw_tracker_members_evicted_without_exit: 0,
            consumer_stopped: false,
            consumer_status: None,
            consumer_stop_count: 0,
            backend_label: LIVE_CAPTURE_BACKEND_LABEL,
            trace_token: LIVE_CAPTURE_TRACE_TOKEN,
            root_pid: None,
            root_start_identity: None,
            root_comm: None,
            root_exited: false,
        }
    }
}

pub(crate) struct LiveCapture {
    state: Arc<Mutex<LiveCaptureState>>,
    handle: tokio::task::JoinHandle<()>,
    start_note: Option<String>,
    #[cfg_attr(not(target_os = "windows"), allow(dead_code))]
    stop_signal: Option<Arc<AtomicBool>>,
}

fn idle_live_capture(note: impl Into<String>) -> LiveCapture {
    LiveCapture {
        state: Arc::new(Mutex::new(LiveCaptureState::default())),
        handle: tokio::spawn(async {}),
        start_note: Some(note.into()),
        stop_signal: None,
    }
}

impl LiveCapture {
    #[cfg(not(target_os = "windows"))]
    pub(crate) async fn stop(self) {
        self.handle.abort();
        if let Err(error) = self.handle.await
            && !error.is_cancelled()
        {
            log::error!("live capture task failed during shutdown: {error}");
        }
    }

    #[cfg(target_os = "windows")]
    pub(crate) async fn stop(self) {
        let LiveCapture {
            state,
            handle,
            stop_signal,
            ..
        } = self;
        if let Some(stop_signal) = &stop_signal {
            stop_signal.store(true, Ordering::Release);
        }
        match tokio::time::timeout(ETW_CAPTURE_STOP_TIMEOUT, handle).await {
            Ok(Ok(())) => {}
            Ok(Err(error)) => {
                set_etw_consumer_stop_status(&state, "consumer_task_failed");
                log::error!("live capture task failed during shutdown: {error}");
            }
            Err(_) => {
                set_etw_consumer_stop_status(&state, "stop_timeout");
                log::warn!(
                    "Windows ETW live capture did not finish shutdown within {} seconds",
                    ETW_CAPTURE_STOP_TIMEOUT.as_secs()
                );
            }
        }
    }

    pub(crate) fn snapshot(&self) -> LiveCaptureSnapshot {
        let Ok(state) = self.state.lock() else {
            return LiveCaptureSnapshot::default();
        };
        let snapshot = state.view.export_snapshot(SnapshotOptions {
            audit_limit: 10_000,
        });
        LiveCaptureSnapshot::with_backend(
            snapshot,
            state.parse_errors,
            state.backend_label,
            state.trace_token,
        )
        .with_root_identity(state.root_pid, state.root_start_identity)
        .with_root_evidence(state.root_comm.clone(), state.root_exited)
    }

    pub(crate) fn status_note(&self) -> Option<String> {
        let Ok(state) = self.state.lock() else {
            return self.start_note.clone();
        };
        live_capture_status_note(&state, self.start_note.as_deref())
    }
}

#[cfg(not(target_os = "windows"))]
pub(crate) async fn start_live_capture(options: &TopOptions) -> LiveCapture {
    let start_note = match prepare_live_ebpf_privileges() {
        Ok(note) => note,
        Err(note) => return idle_live_capture(note),
    };
    let binary_extractor = match BinaryExtractor::new().await {
        Ok(extractor) => extractor,
        Err(err) => {
            return idle_live_capture(format!("live eBPF capture did not start: {err}"));
        }
    };

    let mut args = Vec::new();
    if let Some(pid) = options.pid {
        args.extend(["-p".to_string(), pid.to_string()]);
    } else if let Some(comm) = &options.comm {
        args.extend(["-c".to_string(), comm.clone()]);
    } else {
        args.extend(["-m".to_string(), "1".to_string()]);
    }
    args.push("--trace-fs".to_string());
    args.push("--trace-net".to_string());

    let seed_snapshot = match procfs::ProcSnapshot::collect() {
        Ok(snapshot) => snapshot,
        Err(err) => return idle_live_capture(format!("live eBPF capture did not start: {err}")),
    };
    let seeds = process_select::process_seeds(
        &seed_snapshot,
        None,
        options.pid,
        options.comm.as_deref(),
        true,
    );

    let mut runner = ProcessRunner::from_binary_extractor(binary_extractor.get_process_path())
        .with_args(args.iter().map(String::as_str))
        .with_seed_pids(&seeds);
    runner = runner.add_analyzer(Box::new(TimestampNormalizer::new()));
    let state = Arc::new(Mutex::new(LiveCaptureState::default()));
    let state_for_task = Arc::clone(&state);

    let stream = match runner.run().await {
        Ok(stream) => stream,
        Err(err) => return idle_live_capture(format!("live eBPF capture did not start: {err}")),
    };

    let handle = tokio::spawn(async move {
        consume_live_capture_stream(stream, state_for_task).await;
    });

    LiveCapture {
        state,
        handle,
        start_note,
        stop_signal: None,
    }
}

#[cfg(target_os = "windows")]
pub(crate) async fn start_live_capture(options: &TopOptions) -> LiveCapture {
    let Some(pid) = options.pid else {
        return idle_live_capture(WINDOWS_ETW_REQUIRES_PID_NOTE);
    };
    match current_process_token_is_elevated() {
        Ok(true) => {}
        Ok(false) => return idle_live_capture(WINDOWS_ETW_REQUIRES_ELEVATION_NOTE),
        Err(error) => {
            return idle_live_capture(format!(
                "no Windows ETW: could not verify the current process token elevation ({error}); showing process snapshots and agent-native sessions only"
            ));
        }
    }
    let Some(root_start_identity) = procfs::process_start_identity(pid) else {
        return idle_live_capture(format!(
            "Windows ETW process capture did not start: could not read the start identity for PID {pid}"
        ));
    };

    let stop_signal = Arc::new(AtomicBool::new(false));
    let mut runner = WindowsEtwProcessRunner::new(pid).with_stop_signal(Arc::clone(&stop_signal));
    let stream = match runner.run().await {
        Ok(stream) => stream,
        Err(err) => {
            return idle_live_capture(format!(
                "Windows ETW process capture did not start: {err}; showing process snapshots and agent-native sessions only"
            ));
        }
    };
    if procfs::process_start_identity(pid) != Some(root_start_identity) {
        drop(stream);
        return idle_live_capture(format!(
            "Windows ETW process capture did not start: PID {pid} exited or was reused while the capture session started"
        ));
    }
    let capture_state = LiveCaptureState {
        root_pid: Some(pid),
        root_start_identity: Some(root_start_identity),
        consumer_status: Some("active".to_string()),
        ..LiveCaptureState::default()
    };
    let state = Arc::new(Mutex::new(capture_state));
    let state_for_task = Arc::clone(&state);
    let handle = tokio::spawn(async move {
        consume_live_capture_stream(stream, state_for_task).await;
    });

    LiveCapture {
        state,
        handle,
        start_note: Some(format!(
            "Windows ETW process capture enabled for PID {pid}; command lines are omitted"
        )),
        stop_signal: Some(stop_signal),
    }
}

#[cfg(all(not(target_os = "linux"), any(test, not(target_os = "windows"))))]
fn prepare_live_ebpf_privileges() -> Result<Option<String>, String> {
    if let Err(err) = ensure_agentsight_state_dir() {
        log::warn!("could not create ~/.agentsight: {err}");
    }
    Err(LIVE_EBPF_UNSUPPORTED_NOTE.to_string())
}

#[cfg(target_os = "linux")]
fn prepare_live_ebpf_privileges() -> Result<Option<String>, String> {
    let is_root = unsafe { libc::geteuid() } == 0;
    if !is_root {
        if let Err(err) = ensure_agentsight_state_dir() {
            log::warn!("could not create ~/.agentsight: {err}");
        }
    }
    prepare_live_ebpf_privileges_for(is_root, !is_root && sudo_cached())
}

#[cfg(any(test, target_os = "linux"))]
fn prepare_live_ebpf_privileges_for(
    is_root: bool,
    sudo_ready: bool,
) -> Result<Option<String>, String> {
    if is_root {
        Ok(Some(LIVE_EBPF_ROOT_NOTE.to_string()))
    } else if sudo_ready {
        Ok(Some(LIVE_EBPF_SUDO_NOTE.to_string()))
    } else {
        Err(LIVE_EBPF_UNAVAILABLE_NOTE.to_string())
    }
}

async fn consume_live_capture_stream(
    mut stream: crate::runners::EventStream,
    state: Arc<Mutex<LiveCaptureState>>,
) {
    while let Some(event) = stream.next().await {
        record_live_capture_event(&state, &event);
    }
}

fn live_capture_status_note(state: &LiveCaptureState, fallback: Option<&str>) -> Option<String> {
    let Some(root_pid) = state.root_pid else {
        return fallback.map(str::to_string);
    };
    let status = state
        .consumer_status
        .as_deref()
        .unwrap_or(if state.consumer_stopped {
            "stopped"
        } else {
            "active"
        });
    let loss_note = etw_loss_note(state);
    if state.consumer_stopped {
        Some(format!(
            "Windows ETW process capture stopped for PID {root_pid} ({status}; {} decode errors, {} queued records drained{loss_note}); showing process snapshots and agent-native sessions only",
            state.etw_decode_errors, state.etw_records_drained,
        ))
    } else {
        Some(format!(
            "Windows ETW process capture active for PID {root_pid}; command lines are omitted{loss_note}"
        ))
    }
}

fn etw_loss_note(state: &LiveCaptureState) -> String {
    let mut losses = Vec::new();
    for (label, value) in [
        ("queue drops", state.etw_queue_dropped_records),
        ("callback errors", state.etw_callback_errors),
        ("stop errors", state.etw_stop_errors),
        ("ETW events lost", state.etw_native_events_lost),
        ("ETW log buffers lost", state.etw_native_log_buffers_lost),
        (
            "ETW realtime buffers lost",
            state.etw_native_realtime_buffers_lost,
        ),
        ("native query errors", state.etw_native_query_errors),
        ("pending records evicted", state.etw_pending_records_evicted),
        (
            "provisional exit capacity drops",
            state.etw_provisional_capacity_dropped,
        ),
        (
            "provisional exits evicted with tracker state",
            state.etw_provisional_tracker_evicted,
        ),
        (
            "tracker instances evicted",
            state.etw_tracker_instances_evicted,
        ),
        (
            "tracker ambiguous parents evicted",
            state.etw_tracker_ambiguous_parents_evicted,
        ),
        (
            "tracker members evicted without exit",
            state.etw_tracker_members_evicted_without_exit,
        ),
    ] {
        if value > 0 {
            losses.push(format!("{label}: {value}"));
        }
    }
    if losses.is_empty() {
        String::new()
    } else {
        format!("; observed capture loss or errors ({})", losses.join(", "))
    }
}

#[cfg(target_os = "windows")]
fn set_etw_consumer_stop_status(state: &Arc<Mutex<LiveCaptureState>>, status: &str) {
    if let Ok(mut state) = state.lock() {
        state.consumer_stopped = true;
        state.consumer_status = Some(status.to_string());
    }
}

fn diagnostic_status(data: &serde_json::Value) -> String {
    let reason = data
        .get("reason")
        .and_then(|value| value.as_str())
        .unwrap_or("consumer_stopped");
    match data.get("status_code").and_then(|value| value.as_u64()) {
        Some(status) => format!("{reason}, status 0x{:08X}", status as u32),
        None => reason.to_string(),
    }
}

fn record_live_capture_event(state: &Arc<Mutex<LiveCaptureState>>, event: &Event) {
    let Ok(mut state) = state.lock() else {
        return;
    };
    if let Err(error) = state.view.ingest_event(event) {
        log::warn!("live capture failed to ingest view event: {}", error);
    }

    update_etw_loss_counters(&mut state, &event.data);
    if event.source != "diagnostic" {
        update_root_evidence(&mut state, event);
        return;
    }
    state.diagnostic_count += 1;
    let diagnostic_type = event.data.get("type").and_then(|value| value.as_str());
    let diagnostic_event = event.data.get("event").and_then(|value| value.as_str());
    if diagnostic_type == Some("runner_parse_error") || diagnostic_event == Some("ETW_DECODE_ERROR")
    {
        state.parse_errors += 1;
        if diagnostic_event == Some("ETW_DECODE_ERROR") {
            state.etw_decode_errors += 1;
        }
    }
    if diagnostic_type == Some("runner_consumer_stopped")
        || diagnostic_event == Some("ETW_CONSUMER_STOPPED")
    {
        state.consumer_stopped = true;
        state.consumer_stop_count += 1;
        state.consumer_status = Some(diagnostic_status(&event.data));
        state.etw_records_drained += event
            .data
            .get("queued_records_drained")
            .and_then(|value| value.as_u64())
            .unwrap_or(0);
    }
}

fn update_etw_loss_counters(state: &mut LiveCaptureState, data: &serde_json::Value) {
    let counter = |name: &str| {
        data.get("capture")
            .and_then(|capture| capture.get(name))
            .or_else(|| data.get(name))
            .and_then(serde_json::Value::as_u64)
    };
    if let Some(value) = counter("queue_dropped_records") {
        state.etw_queue_dropped_records = state.etw_queue_dropped_records.max(value);
    }
    if let Some(value) = counter("callback_errors") {
        state.etw_callback_errors = state.etw_callback_errors.max(value);
    }
    if let Some(value) = counter("stop_errors") {
        state.etw_stop_errors = state.etw_stop_errors.max(value);
    }
    if let Some(value) = counter("etw_events_lost") {
        state.etw_native_events_lost = state.etw_native_events_lost.max(value);
    }
    if let Some(value) = counter("etw_log_buffers_lost") {
        state.etw_native_log_buffers_lost = state.etw_native_log_buffers_lost.max(value);
    }
    if let Some(value) = counter("etw_realtime_buffers_lost") {
        state.etw_native_realtime_buffers_lost = state.etw_native_realtime_buffers_lost.max(value);
    }
    if let Some(value) = counter("native_query_errors") {
        state.etw_native_query_errors = state.etw_native_query_errors.max(value);
    }
    if let Some(value) = counter("pending_evicted") {
        state.etw_pending_records_evicted = state.etw_pending_records_evicted.max(value);
    }
    if let Some(value) = counter("provisional_terminates_capacity_dropped") {
        state.etw_provisional_capacity_dropped = state.etw_provisional_capacity_dropped.max(value);
    }
    if let Some(value) = counter("provisional_terminates_tracker_evicted") {
        state.etw_provisional_tracker_evicted = state.etw_provisional_tracker_evicted.max(value);
    }
    if let Some(value) = counter("tracker_evicted_instances") {
        state.etw_tracker_instances_evicted = state.etw_tracker_instances_evicted.max(value);
    }
    if let Some(value) = counter("tracker_evicted_ambiguous_parents") {
        state.etw_tracker_ambiguous_parents_evicted =
            state.etw_tracker_ambiguous_parents_evicted.max(value);
    }
    if let Some(value) = counter("tracker_evicted_members_without_exit") {
        state.etw_tracker_members_evicted_without_exit =
            state.etw_tracker_members_evicted_without_exit.max(value);
    }
}

fn update_root_evidence(state: &mut LiveCaptureState, event: &Event) {
    let Some(root_pid) = state.root_pid else {
        return;
    };
    if event.source != "process"
        || event.pid != root_pid
        || event
            .data
            .get("capture_root_pid")
            .and_then(serde_json::Value::as_u64)
            != Some(u64::from(root_pid))
    {
        return;
    }
    match event.data.get("event").and_then(serde_json::Value::as_str) {
        Some("EXEC" | "PROCESS_PRESENT") => {
            state.root_comm = event
                .data
                .get("comm")
                .and_then(serde_json::Value::as_str)
                .filter(|comm| !comm.is_empty())
                .map(str::to_string)
                .or_else(|| Some(event.comm.clone()));
        }
        Some("EXIT") => state.root_exited = true,
        _ => {}
    }
}

pub(crate) fn run_live_top_query(
    capture: Option<&LiveCapture>,
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let limit = limit.clamp(1, 100);
    let interval = Duration::from_secs(interval_secs.max(1));
    let mut iterations = 0u32;
    let should_clear_screen = count != Some(1);
    let mut live_view = LiveView::default();

    loop {
        if should_clear_screen {
            clear_screen();
        }
        let capture_snapshot = capture.map(LiveCapture::snapshot);
        let mut top = live_view.refresh(capture_snapshot.as_ref(), limit, options)?;
        if let Some(note) = capture.and_then(LiveCapture::status_note) {
            top.notes.push(note);
        }
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        io::stdout().flush()?;

        iterations += 1;
        if count.is_some_and(|max| iterations >= max) || crate::shutdown_requested() {
            break;
        }
        std::thread::sleep(interval);
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn live_ebpf_privileges_enable_for_root() {
        assert_eq!(
            prepare_live_ebpf_privileges_for(true, false).unwrap(),
            Some(LIVE_EBPF_ROOT_NOTE.to_string())
        );
    }

    #[test]
    fn live_ebpf_privileges_enable_for_ready_sudo() {
        assert_eq!(
            prepare_live_ebpf_privileges_for(false, true).unwrap(),
            Some(LIVE_EBPF_SUDO_NOTE.to_string())
        );
    }

    #[test]
    fn live_ebpf_privileges_degrade_without_sudo() {
        assert_eq!(
            prepare_live_ebpf_privileges_for(false, false).unwrap_err(),
            LIVE_EBPF_UNAVAILABLE_NOTE.to_string()
        );
    }

    #[cfg(not(target_os = "linux"))]
    #[test]
    fn live_ebpf_privileges_degrade_on_non_linux() {
        assert_eq!(
            prepare_live_ebpf_privileges().unwrap_err(),
            LIVE_EBPF_UNSUPPORTED_NOTE.to_string()
        );
    }

    #[cfg(target_os = "windows")]
    #[tokio::test]
    async fn windows_live_capture_requires_pid_without_starting_etw() {
        let capture = start_live_capture(&TopOptions {
            pid: None,
            comm: None,
            sort: "cpu".to_string(),
            view: "all".to_string(),
        })
        .await;
        assert_eq!(
            capture.status_note().as_deref(),
            Some(WINDOWS_ETW_REQUIRES_PID_NOTE)
        );
        capture.stop().await;
    }

    #[test]
    fn etw_diagnostics_update_status_without_starting_etw() {
        let state = Arc::new(Mutex::new(LiveCaptureState {
            root_pid: Some(4242),
            consumer_status: Some("active".to_string()),
            ..LiveCaptureState::default()
        }));
        let active_note = {
            let state = state.lock().unwrap();
            live_capture_status_note(&state, None).unwrap()
        };
        assert!(active_note.contains("active for PID 4242"));

        for data in [
            json!({
                "event": "ETW_DECODE_ERROR",
                "reason": "decode_process_payload_failed"
            }),
            json!({
                "type": "runner_parse_error",
                "runner": "windows_etw",
                "reason": "invalid_event_timestamp"
            }),
            json!({
                "type": "runner_consumer_stopped",
                "event": "ETW_CONSUMER_STOPPED",
                "reason": "stop_requested",
                "status_code": 0,
                "queued_records_drained": 17,
                "queue_dropped_records": 2,
                "etw_events_lost": 3,
                "callback_errors": 1,
                "pending_evicted": 4,
                "provisional_terminates_capacity_dropped": 5,
                "provisional_terminates_tracker_evicted": 6,
                "tracker_evicted_instances": 7,
                "tracker_evicted_ambiguous_parents": 8,
                "tracker_evicted_members_without_exit": 9
            }),
        ] {
            record_live_capture_event(
                &state,
                &Event::new(
                    "diagnostic".to_string(),
                    4242,
                    "windows_etw".to_string(),
                    data,
                ),
            );
        }

        let state = state.lock().unwrap();
        assert_eq!(state.parse_errors, 2);
        assert_eq!(state.diagnostic_count, 3);
        assert_eq!(state.etw_decode_errors, 1);
        assert_eq!(state.consumer_stop_count, 1);
        assert_eq!(state.etw_records_drained, 17);
        assert_eq!(state.etw_queue_dropped_records, 2);
        assert_eq!(state.etw_native_events_lost, 3);
        assert_eq!(state.etw_callback_errors, 1);
        assert_eq!(state.etw_pending_records_evicted, 4);
        assert_eq!(state.etw_provisional_capacity_dropped, 5);
        assert_eq!(state.etw_provisional_tracker_evicted, 6);
        assert_eq!(state.etw_tracker_instances_evicted, 7);
        assert_eq!(state.etw_tracker_ambiguous_parents_evicted, 8);
        assert_eq!(state.etw_tracker_members_evicted_without_exit, 9);
        assert!(state.consumer_stopped);
        assert_eq!(
            state.consumer_status.as_deref(),
            Some("stop_requested, status 0x00000000")
        );
        let stopped_note = live_capture_status_note(&state, None).unwrap();
        assert!(stopped_note.contains("stopped for PID 4242"));
        assert!(stopped_note.contains("17 queued records drained"));
        assert!(stopped_note.contains("queue drops: 2"));
        assert!(stopped_note.contains("ETW events lost: 3"));
        assert!(stopped_note.contains("pending records evicted: 4"));
        assert!(stopped_note.contains("tracker instances evicted: 7"));
        assert!(!stopped_note.contains("enabled"));
    }

    #[test]
    fn etw_root_evidence_is_retained_before_projection() {
        let state = Arc::new(Mutex::new(LiveCaptureState {
            root_pid: Some(4242),
            root_start_identity: Some(77),
            ..LiveCaptureState::default()
        }));
        for data in [
            json!({
                "event": "PROCESS_PRESENT",
                "capture_root_pid": 4242,
                "comm": "codex.exe"
            }),
            json!({
                "event": "EXIT",
                "capture_root_pid": 4242,
                "comm": "codex.exe"
            }),
        ] {
            record_live_capture_event(
                &state,
                &Event::new("process".to_string(), 4242, "codex.exe".to_string(), data),
            );
        }
        let state = state.lock().unwrap();
        assert_eq!(state.root_comm.as_deref(), Some("codex.exe"));
        assert!(state.root_exited);
    }

    #[test]
    fn etw_process_events_retain_cumulative_capture_losses() {
        let state = Arc::new(Mutex::new(LiveCaptureState {
            root_pid: Some(4242),
            consumer_status: Some("active".to_string()),
            ..LiveCaptureState::default()
        }));
        for (queue_drops, native_events, pending_evicted) in [(2, 3, 1), (5, 8, 4)] {
            record_live_capture_event(
                &state,
                &Event::new(
                    "process".to_string(),
                    4242,
                    "codex.exe".to_string(),
                    json!({
                        "event": "EXEC",
                        "capture_root_pid": 4242,
                        "comm": "codex.exe",
                        "capture": {
                            "queue_dropped_records": queue_drops,
                            "etw_events_lost": native_events,
                            "pending_evicted": pending_evicted,
                            "provisional_terminates_capacity_dropped": pending_evicted + 1,
                            "provisional_terminates_tracker_evicted": pending_evicted + 2,
                            "tracker_evicted_instances": pending_evicted + 3,
                            "tracker_evicted_ambiguous_parents": pending_evicted + 4,
                            "tracker_evicted_members_without_exit": pending_evicted + 5
                        }
                    }),
                ),
            );
        }

        let state = state.lock().unwrap();
        assert_eq!(state.etw_queue_dropped_records, 5);
        assert_eq!(state.etw_native_events_lost, 8);
        assert_eq!(state.etw_pending_records_evicted, 4);
        assert_eq!(state.etw_provisional_capacity_dropped, 5);
        assert_eq!(state.etw_provisional_tracker_evicted, 6);
        assert_eq!(state.etw_tracker_instances_evicted, 7);
        assert_eq!(state.etw_tracker_ambiguous_parents_evicted, 8);
        assert_eq!(state.etw_tracker_members_evicted_without_exit, 9);
        let note = live_capture_status_note(&state, None).unwrap();
        assert!(note.contains("queue drops: 5"));
        assert!(note.contains("ETW events lost: 8"));
        assert!(note.contains("pending records evicted: 4"));
        assert!(note.contains("tracker members evicted without exit: 9"));
    }

    #[test]
    fn record_live_capture_event_ingests_process_file_and_network_events() {
        let temp = tempfile::tempdir().unwrap();
        let claude_path = temp.path().join("claude-path.jsonl");
        let codex_path = temp.path().join("codex-path.jsonl");
        let state = Arc::new(Mutex::new(LiveCaptureState::default()));
        let pid = std::process::id();

        for (comm, data) in [
            (
                "claude",
                json!({
                    "timestamp": 1,
                    "event": "FILE_OPEN",
                    "comm": "claude",
                    "pid": pid,
                    "filepath": claude_path,
                    "flags": 1
                }),
            ),
            (
                "codex",
                json!({
                    "timestamp": 1,
                    "event": "SUMMARY",
                    "comm": "codex",
                    "pid": pid,
                    "type": "WRITE",
                    "detail": codex_path,
                    "path_resolved": true,
                    "count": 3
                }),
            ),
            (
                "codex",
                json!({
                "timestamp": 1,
                "event": "SUMMARY",
                "comm": "codex",
                "pid": pid,
                "type": "WRITE",
                "detail": "fd=3",
                "path_resolved": false,
                "count": 1
                }),
            ),
            (
                "codex",
                json!({
                    "timestamp": 1,
                    "event": "SUMMARY",
                    "comm": "codex",
                    "pid": pid,
                    "type": "NET_CONNECT",
                    "detail": "127.0.0.1:7395",
                    "count": 2
                }),
            ),
        ] {
            record_live_capture_event(
                &state,
                &Event::new("process".to_string(), pid, comm.to_string(), data),
            );
        }

        let snapshot = state.lock().unwrap();
        let view_snapshot = snapshot.view.export_snapshot(SnapshotOptions {
            audit_limit: 10_000,
        });
        let counters = crate::model::AuditCounters::by_pid(&view_snapshot.audit_events);
        let counters = counters.get(&pid).unwrap();
        assert_eq!(counters.file_events, 3);
        assert_eq!(counters.network_events, 1);
    }
}
