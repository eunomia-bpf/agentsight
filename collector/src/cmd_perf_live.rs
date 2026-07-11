// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::analyzers::TimestampNormalizer;
use crate::binary_extractor::BinaryExtractor;
use crate::cmd_exec::sudo_cached;
use crate::event::Event;
use crate::model::SnapshotOptions;
use crate::output::{TopOptions, clear_screen, print_agent_top};
use crate::runners::{ProcessRunner, Runner};
use crate::sources::proc as procfs;
use crate::state::ensure_agentsight_state_dir;
use crate::view::MaterializedView;
use crate::view::live_top::{LiveCaptureSnapshot, LiveView};
use crate::view::process_select;
use crate::view::top::sort_agent_rows;
use futures::StreamExt;
use std::io::{self, Write};
use std::sync::{Arc, Mutex};
use std::time::Duration;

const LIVE_EBPF_ROOT_NOTE: &str = "live eBPF process capture enabled";
const LIVE_EBPF_SUDO_NOTE: &str = "live eBPF process capture enabled via sudo";
const LIVE_EBPF_UNAVAILABLE_NOTE: &str = "no eBPF: showing process snapshots and agent-native sessions only (run with sudo or configure passwordless sudo for kernel probes)";

struct LiveCaptureState {
    view: MaterializedView,
    parse_errors: u64,
}

impl Default for LiveCaptureState {
    fn default() -> Self {
        Self {
            view: MaterializedView::bounded(),
            parse_errors: 0,
        }
    }
}

pub(crate) struct LiveEbpfCapture {
    state: Arc<Mutex<LiveCaptureState>>,
    handle: tokio::task::JoinHandle<()>,
    start_note: Option<String>,
}

impl LiveEbpfCapture {
    pub(crate) fn stop(self) {
        self.handle.abort();
    }

    pub(crate) fn snapshot(&self) -> LiveCaptureSnapshot {
        let Ok(state) = self.state.lock() else {
            return LiveCaptureSnapshot::default();
        };
        let snapshot = state.view.export_snapshot(SnapshotOptions {
            audit_limit: 10_000,
        });
        LiveCaptureSnapshot::new(snapshot, state.parse_errors)
    }

    pub(crate) fn start_note(&self) -> Option<&str> {
        self.start_note.as_deref()
    }
}

pub(crate) async fn start_live_ebpf_capture(
    binary_extractor: &BinaryExtractor,
    options: &TopOptions,
) -> Option<LiveEbpfCapture> {
    let start_note = match prepare_live_ebpf_privileges() {
        Ok(note) => note,
        Err(note) => {
            return Some(LiveEbpfCapture {
                state: Arc::new(Mutex::new(LiveCaptureState::default())),
                handle: tokio::spawn(async {}),
                start_note: Some(note),
            });
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
        Err(err) => {
            return Some(LiveEbpfCapture {
                state: Arc::new(Mutex::new(LiveCaptureState::default())),
                handle: tokio::spawn(async {}),
                start_note: Some(format!("live eBPF capture did not start: {err}")),
            });
        }
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
        Err(err) => {
            return Some(LiveEbpfCapture {
                state,
                handle: tokio::spawn(async {}),
                start_note: Some(format!("live eBPF capture did not start: {err}")),
            });
        }
    };

    let handle = tokio::spawn(async move {
        consume_live_ebpf_stream(stream, state_for_task).await;
    });

    Some(LiveEbpfCapture {
        state,
        handle,
        start_note,
    })
}

fn prepare_live_ebpf_privileges() -> Result<Option<String>, String> {
    let is_root = unsafe { libc::geteuid() } == 0;
    if !is_root {
        if let Err(err) = ensure_agentsight_state_dir() {
            log::warn!("could not create ~/.agentsight: {err}");
        }
    }
    prepare_live_ebpf_privileges_for(is_root, !is_root && sudo_cached())
}

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

async fn consume_live_ebpf_stream(
    mut stream: crate::runners::EventStream,
    state: Arc<Mutex<LiveCaptureState>>,
) {
    while let Some(event) = stream.next().await {
        record_live_ebpf_event(&state, &event);
    }
}

fn record_live_ebpf_event(state: &Arc<Mutex<LiveCaptureState>>, event: &Event) {
    let Ok(mut state) = state.lock() else {
        return;
    };
    if let Err(error) = state.view.ingest_event(event) {
        log::warn!("live eBPF capture failed to ingest view event: {}", error);
    }

    if event.source == "diagnostic"
        && event.data.get("type").and_then(|value| value.as_str()) == Some("runner_parse_error")
    {
        state.parse_errors += 1;
    }
}

pub(crate) async fn run_live_top_query(
    binary_extractor: &BinaryExtractor,
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
    let capture = start_live_ebpf_capture(binary_extractor, options).await;

    loop {
        if should_clear_screen {
            clear_screen();
        }
        let capture_snapshot = capture.as_ref().map(LiveEbpfCapture::snapshot);
        let mut top = live_view.refresh(capture_snapshot.as_ref(), limit, options)?;
        if let Some(note) = capture.as_ref().and_then(|capture| capture.start_note()) {
            top.notes.push(note.to_string());
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

    if let Some(capture) = capture {
        capture.stop();
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

    #[test]
    fn record_live_ebpf_event_ingests_process_file_and_network_events() {
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
            record_live_ebpf_event(
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
