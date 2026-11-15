// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Attach-only Windows process lifecycle capture through the classic ETW
//! SystemTraceProvider. The runner never launches or terminates its target.

use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use async_trait::async_trait;
use std::collections::{BTreeMap, VecDeque};
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::task::{Context, Poll};
use std::time::Duration;
use tokio::sync::mpsc;

use payload::{
    EtwProcessPhase, ProcessEtwRecord, event_pointer_size, filetime_to_unix_millis,
    parse_process_end, parse_process_start, parse_process_terminate,
};
use runtime::{EtwLossSnapshot, EtwRuntime, RawEtwEvent, win32_error};
use tracker::{IngestOutcome, ProcessTracker};
use windows_sys::Win32::Foundation::{
    CloseHandle, ERROR_ACCESS_DENIED, ERROR_CANCELLED, GetLastError, WIN32_ERROR,
};
use windows_sys::Win32::Security::{
    GetTokenInformation, TOKEN_ELEVATION, TOKEN_QUERY, TokenElevation,
};
use windows_sys::Win32::System::Threading::{
    GetCurrentProcess, OpenProcess, OpenProcessToken, PROCESS_QUERY_LIMITED_INFORMATION,
};

mod payload;
mod runtime;
mod tracker;

pub const DEFAULT_ETW_QUEUE_CAPACITY: usize = 8_192;
const MAX_PENDING_ETW_EVENTS: usize = 4_096;
const MAX_PROVISIONAL_TERMINATES: usize = 4_096;
const MISSING_CONSUMER_STATUS: WIN32_ERROR = u32::MAX;
const STOP_SIGNAL_POLL_INTERVAL: Duration = Duration::from_millis(50);

/// Captures process lifecycle events for a running root process and its
/// descendants.
pub struct WindowsEtwProcessRunner {
    root_pid: u32,
    queue_capacity: usize,
    include_command_line: bool,
    stop_signal: Option<Arc<AtomicBool>>,
    analyzers: Vec<Box<dyn Analyzer>>,
}

impl WindowsEtwProcessRunner {
    pub fn new(root_pid: u32) -> Self {
        Self {
            root_pid,
            queue_capacity: DEFAULT_ETW_QUEUE_CAPACITY,
            include_command_line: false,
            stop_signal: None,
            analyzers: Vec::new(),
        }
    }

    pub fn with_queue_capacity(mut self, queue_capacity: usize) -> Self {
        self.queue_capacity = queue_capacity.max(1);
        self
    }

    pub fn with_command_line(mut self, include: bool) -> Self {
        self.include_command_line = include;
        self
    }

    pub fn with_stop_signal(mut self, stop_signal: Arc<AtomicBool>) -> Self {
        self.stop_signal = Some(stop_signal);
        self
    }
}

#[async_trait]
impl Runner for WindowsEtwProcessRunner {
    async fn run(&mut self) -> Result<EventStream, RunnerError> {
        validate_target_pid(self.root_pid)?;
        if !current_process_token_is_elevated()? {
            return Err(
                "Windows ETW process capture requires a process with an elevated token".into(),
            );
        }
        let (sender, receiver) = mpsc::channel(self.queue_capacity);
        let runtime = EtwRuntime::start(sender)?;
        let stream = WindowsEtwEventStream::new(
            receiver,
            runtime,
            self.root_pid,
            self.include_command_line,
            self.stop_signal.clone(),
        );
        super::common::AnalyzerProcessor::process_through_analyzers(
            Box::pin(stream),
            &mut self.analyzers,
        )
        .await
    }

    fn add_analyzer(mut self, analyzer: Box<dyn Analyzer>) -> Self {
        self.analyzers.push(analyzer);
        self
    }
}

/// Returns whether the current process token is elevated.
///
/// The Windows ETW SystemTraceProvider requires elevation. Callers should use
/// this check before attempting to open a session so a normal terminal can
/// stay on its existing snapshot path without an access-denied probe or UAC
/// request.
pub fn current_process_token_is_elevated() -> Result<bool, RunnerError> {
    let mut token = std::ptr::null_mut();
    if unsafe { OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) } == 0 {
        let error = unsafe { GetLastError() };
        return Err(win32_error("OpenProcessToken for current process", error));
    }

    let mut elevation = TOKEN_ELEVATION::default();
    let mut returned_size = 0;
    let status = unsafe {
        GetTokenInformation(
            token,
            TokenElevation,
            (&mut elevation as *mut TOKEN_ELEVATION).cast(),
            std::mem::size_of::<TOKEN_ELEVATION>() as u32,
            &mut returned_size,
        )
    };
    let query_error = (status == 0).then(|| unsafe { GetLastError() });
    let close_error = (unsafe { CloseHandle(token) } == 0).then(|| unsafe { GetLastError() });

    if let Some(error) = query_error {
        return Err(win32_error(
            "GetTokenInformation(TokenElevation) for current process",
            error,
        ));
    }
    if let Some(error) = close_error {
        return Err(win32_error("CloseHandle for current process token", error));
    }
    if returned_size < std::mem::size_of::<TOKEN_ELEVATION>() as u32 {
        return Err("GetTokenInformation(TokenElevation) returned a short payload".into());
    }
    Ok(elevation.TokenIsElevated != 0)
}

fn validate_target_pid(pid: u32) -> Result<(), RunnerError> {
    if pid == 0 {
        return Err("Windows ETW process capture requires a nonzero target PID".into());
    }
    let process = unsafe { OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid) };
    if process.is_null() {
        let error = unsafe { GetLastError() };
        return Err(win32_error(
            &format!("OpenProcess for target PID {pid}"),
            error,
        ));
    }
    if unsafe { CloseHandle(process) } == 0 {
        let error = unsafe { GetLastError() };
        return Err(win32_error(
            &format!("CloseHandle for target PID {pid}"),
            error,
        ));
    }
    Ok(())
}

struct WindowsEtwEventStream {
    receiver: mpsc::Receiver<RawEtwEvent>,
    ready_events: VecDeque<Event>,
    pending_events: VecDeque<RawEtwEvent>,
    provisional_terminates: ProvisionalTerminates,
    runtime: EtwRuntime,
    tracker: ProcessTracker,
    include_command_line: bool,
    last_loss: EtwLossSnapshot,
    filtered_events: u64,
    duplicate_events: u64,
    pending_evicted: u64,
    stop_signal: Option<Arc<AtomicBool>>,
    stop_poll: Option<tokio::time::Interval>,
    runtime_stopped: bool,
    stop_requested: bool,
    consumer_exit_status: Option<WIN32_ERROR>,
    terminal_diagnostic: Option<Event>,
    terminal_emitted: bool,
    queued_records_drained: u64,
}

enum ConvertOutcome {
    Event {
        event: Event,
        topology_changed: bool,
    },
    TopologyChanged,
    Deferred,
    Ignored,
}

#[derive(Debug)]
struct ProvisionalTerminate {
    instance_id: u64,
    raw: RawEtwEvent,
    record: ProcessEtwRecord,
    timestamp: u64,
}

#[derive(Debug)]
struct ProvisionalTerminates {
    capacity: usize,
    entries: BTreeMap<u64, ProvisionalTerminate>,
    capacity_dropped: u64,
    tracker_evicted: u64,
}

impl ProvisionalTerminates {
    fn new(capacity: usize) -> Self {
        Self {
            capacity: capacity.max(1),
            entries: BTreeMap::new(),
            capacity_dropped: 0,
            tracker_evicted: 0,
        }
    }

    fn hold(&mut self, terminate: ProvisionalTerminate) {
        if !self.entries.contains_key(&terminate.instance_id)
            && self.entries.len() >= self.capacity
            && self.entries.pop_first().is_some()
        {
            self.capacity_dropped = self.capacity_dropped.saturating_add(1);
        }
        self.entries.insert(terminate.instance_id, terminate);
    }

    fn remove(&mut self, instance_id: u64) -> Option<ProvisionalTerminate> {
        self.entries.remove(&instance_id)
    }

    fn discard_tracker_evictions(&mut self, instance_ids: &[u64]) {
        for instance_id in instance_ids {
            if self.entries.remove(instance_id).is_some() {
                self.tracker_evicted = self.tracker_evicted.saturating_add(1);
            }
        }
    }

    fn len(&self) -> usize {
        self.entries.len()
    }

    fn take_sorted(&mut self) -> Vec<ProvisionalTerminate> {
        let mut pending = std::mem::take(&mut self.entries)
            .into_values()
            .collect::<Vec<_>>();
        pending.sort_by_key(|terminate| terminate.raw.sequence);
        pending
    }
}

impl WindowsEtwEventStream {
    fn new(
        receiver: mpsc::Receiver<RawEtwEvent>,
        runtime: EtwRuntime,
        root_pid: u32,
        include_command_line: bool,
        stop_signal: Option<Arc<AtomicBool>>,
    ) -> Self {
        let stop_poll = stop_signal.as_ref().map(|_| {
            let mut interval = tokio::time::interval(STOP_SIGNAL_POLL_INTERVAL);
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Delay);
            interval
        });
        Self {
            receiver,
            ready_events: VecDeque::new(),
            pending_events: VecDeque::new(),
            provisional_terminates: ProvisionalTerminates::new(MAX_PROVISIONAL_TERMINATES),
            runtime,
            tracker: ProcessTracker::new(root_pid),
            include_command_line,
            last_loss: EtwLossSnapshot::default(),
            filtered_events: 0,
            duplicate_events: 0,
            pending_evicted: 0,
            stop_signal,
            stop_poll,
            runtime_stopped: false,
            stop_requested: false,
            consumer_exit_status: None,
            terminal_diagnostic: None,
            terminal_emitted: false,
            queued_records_drained: 0,
        }
    }

    fn convert(&mut self, raw: RawEtwEvent) {
        match self.convert_once(raw.clone(), false) {
            ConvertOutcome::Event {
                event,
                topology_changed,
            } => {
                self.ready_events.push_back(event);
                if topology_changed {
                    self.replay_pending_events();
                }
            }
            ConvertOutcome::TopologyChanged => self.replay_pending_events(),
            ConvertOutcome::Deferred => self.defer(raw),
            ConvertOutcome::Ignored => {}
        }
    }

    fn convert_once(&mut self, raw: RawEtwEvent, replay: bool) -> ConvertOutcome {
        let phase = EtwProcessPhase::from_opcode(raw.opcode);
        if phase == EtwProcessPhase::Unknown {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "unsupported_process_opcode"),
                topology_changed: false,
            };
        }
        let Some(timestamp) = filetime_to_unix_millis(raw.timestamp) else {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "invalid_event_timestamp"),
                topology_changed: false,
            };
        };
        let pointer_size = event_pointer_size(raw.flags);
        let record = if phase.is_start() {
            parse_process_start(&raw.user_data, raw.version, pointer_size)
        } else if phase == EtwProcessPhase::Terminate {
            parse_process_terminate(&raw.user_data, raw.process_id)
        } else {
            parse_process_end(&raw.user_data, raw.version, pointer_size)
        };

        let Some(record) = record else {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "decode_process_payload_failed"),
                topology_changed: false,
            };
        };
        let outcome = self
            .tracker
            .ingest_at(record.clone(), phase, Some(raw.timestamp));
        let evicted_instances = self.tracker.take_evicted_instance_ids();
        self.provisional_terminates
            .discard_tracker_evictions(&evicted_instances);
        let accepted = match outcome {
            IngestOutcome::Accepted {
                instance_id,
                topology_changed,
                ..
            } => Some((instance_id, topology_changed)),
            IngestOutcome::Duplicate => {
                self.duplicate_events += 1;
                return ConvertOutcome::Ignored;
            }
            IngestOutcome::Filtered => None,
        };
        let (instance_id, topology_changed) = match accepted {
            Some(accepted) => accepted,
            None => {
                if !replay {
                    self.filtered_events += 1;
                }
                return ConvertOutcome::Deferred;
            }
        };
        if phase == EtwProcessPhase::Terminate {
            self.provisional_terminates.hold(ProvisionalTerminate {
                instance_id,
                raw,
                record,
                timestamp,
            });
            return if topology_changed {
                ConvertOutcome::TopologyChanged
            } else {
                ConvertOutcome::Ignored
            };
        }
        if phase == EtwProcessPhase::End {
            self.provisional_terminates.remove(instance_id);
        }
        ConvertOutcome::Event {
            event: self.process_event(&raw, &record, phase, timestamp, instance_id),
            topology_changed,
        }
    }

    fn process_event(
        &mut self,
        raw: &RawEtwEvent,
        record: &ProcessEtwRecord,
        phase: EtwProcessPhase,
        timestamp: u64,
        instance_id: u64,
    ) -> Event {
        let comm = record
            .image_file_name
            .clone()
            .unwrap_or_else(|| "process".to_string());
        let event_name = phase.event_name();
        let pointer_size = event_pointer_size(raw.flags);
        let loss = self.runtime.loss_snapshot();
        self.last_loss = loss;
        let tracker_stats = self.tracker.stats();

        let mut data = serde_json::json!({
            "event": event_name,
            "pid": record.pid,
            "ppid": record.ppid,
            "comm": comm,
            "filename": record.image_file_name.clone(),
            "command_line": self
                .include_command_line
                .then(|| record.command_line.clone())
                .flatten(),
            "exit_code": record.exit_status,
            "exit_status": record.exit_status,
            "session_id": record.session_id,
            "process_instance_id": instance_id,
            "capture_root_pid": self.tracker.root_pid(),
            "etw": {
                "provider": "SystemTraceProvider",
                "provider_guid": "3d6fa8d0-fe05-11d0-9dda-00c04fd7ba7c",
                "event_id": raw.event_id,
                "version": raw.version,
                "opcode": raw.opcode,
                "phase": phase.as_str(),
                "header_flags": raw.flags,
                "pointer_size": pointer_size,
                "existing": phase.is_existing(),
                "rundown": phase.is_existing(),
            },
            "capture": {
                "queue_dropped_records": loss.application_queue_dropped_records,
                "callback_errors": loss.callback_errors,
                "stop_errors": loss.stop_errors,
                "etw_events_lost": loss.native_events_lost,
                "etw_log_buffers_lost": loss.native_log_buffers_lost,
                "etw_realtime_buffers_lost": loss.native_realtime_buffers_lost,
                "native_query_errors": loss.native_query_errors,
                "pid_reuse_count": tracker_stats.pid_reuse_count,
                "unknown_parent_count": tracker_stats.unknown_parent_count,
                "tracker_evicted_instances": tracker_stats.evicted_instance_count,
                "tracker_evicted_ambiguous_parents": tracker_stats.evicted_ambiguous_parent_count,
                "tracker_evicted_members_without_exit": tracker_stats.evicted_member_instance_count,
                "filtered_events": self.filtered_events,
                "duplicate_events": self.duplicate_events,
                "pending_evicted": self.pending_evicted,
                "provisional_terminates_held": self.provisional_terminates.len(),
                "provisional_terminates_capacity_dropped":
                    self.provisional_terminates.capacity_dropped,
                "provisional_terminates_tracker_evicted":
                    self.provisional_terminates.tracker_evicted,
            },
        });
        if phase.is_start() {
            data["existing"] = phase.is_existing().into();
        }

        Event::new_with_timestamp(timestamp, "process".to_string(), record.pid, comm, data)
    }

    fn defer(&mut self, raw: RawEtwEvent) {
        if self.pending_events.len() >= MAX_PENDING_ETW_EVENTS {
            self.pending_events.pop_front();
            self.pending_evicted += 1;
        }
        self.pending_events.push_back(raw);
    }

    fn replay_pending_events(&mut self) {
        loop {
            if self.pending_events.is_empty() {
                break;
            }
            let pending = std::mem::take(&mut self.pending_events);
            let previous_len = pending.len();
            let mut topology_changed = false;
            for raw in pending {
                match self.convert_once(raw.clone(), true) {
                    ConvertOutcome::Event {
                        event,
                        topology_changed: changed,
                    } => {
                        topology_changed |= changed;
                        self.ready_events.push_back(event);
                    }
                    ConvertOutcome::TopologyChanged => topology_changed = true,
                    ConvertOutcome::Deferred => self.pending_events.push_back(raw),
                    ConvertOutcome::Ignored => {}
                }
            }
            if !topology_changed || self.pending_events.len() >= previous_len {
                break;
            }
        }
    }

    fn flush_provisional_terminates(&mut self) {
        for terminate in self.provisional_terminates.take_sorted() {
            let event = self.process_event(
                &terminate.raw,
                &terminate.record,
                EtwProcessPhase::Terminate,
                terminate.timestamp,
                terminate.instance_id,
            );
            self.ready_events.push_back(event);
        }
    }

    fn diagnostic(&mut self, raw: &RawEtwEvent, reason: &str) -> Event {
        let loss = self.runtime.loss_snapshot();
        self.last_loss = loss;
        Event::new_with_timestamp(
            current_unix_millis(),
            "diagnostic".to_string(),
            raw.process_id,
            "windows_etw".to_string(),
            serde_json::json!({
                "type": "runner_parse_error",
                "event": "ETW_DECODE_ERROR",
                "reason": reason,
                "sequence": raw.sequence,
                "event_id": raw.event_id,
                "version": raw.version,
                "opcode": raw.opcode,
                "header_flags": raw.flags,
                "payload_len": raw.user_data.len(),
                "queue_dropped_records": loss.application_queue_dropped_records,
                "callback_errors": loss.callback_errors,
                "stop_errors": loss.stop_errors,
                "etw_events_lost": loss.native_events_lost,
                "etw_log_buffers_lost": loss.native_log_buffers_lost,
                "etw_realtime_buffers_lost": loss.native_realtime_buffers_lost,
                "native_query_errors": loss.native_query_errors,
            }),
        )
    }

    fn consumer_stopped_diagnostic(&mut self, status: WIN32_ERROR, stop_requested: bool) -> Event {
        let loss = self.runtime.loss_snapshot();
        self.last_loss = loss;
        let tracker_stats = self.tracker.stats();
        let reason = if stop_requested {
            "stop_requested"
        } else {
            consumer_stop_reason(status)
        };
        Event::new_with_timestamp(
            current_unix_millis(),
            "diagnostic".to_string(),
            self.tracker.root_pid(),
            "windows_etw".to_string(),
            serde_json::json!({
                "type": "runner_consumer_stopped",
                "event": "ETW_CONSUMER_STOPPED",
                "reason": reason,
                "status_code": status,
                "stop_requested": stop_requested,
                "queued_records_drained": self.queued_records_drained,
                "pending_records": self.pending_events.len() + self.provisional_terminates.len(),
                "pending_evicted": self.pending_evicted,
                "provisional_terminates_held": self.provisional_terminates.len(),
                "provisional_terminates_capacity_dropped":
                    self.provisional_terminates.capacity_dropped,
                "provisional_terminates_tracker_evicted":
                    self.provisional_terminates.tracker_evicted,
                "tracker_evicted_instances": tracker_stats.evicted_instance_count,
                "tracker_evicted_ambiguous_parents": tracker_stats.evicted_ambiguous_parent_count,
                "tracker_evicted_members_without_exit":
                    tracker_stats.evicted_member_instance_count,
                "queue_dropped_records": loss.application_queue_dropped_records,
                "callback_errors": loss.callback_errors,
                "stop_errors": loss.stop_errors,
                "etw_events_lost": loss.native_events_lost,
                "etw_log_buffers_lost": loss.native_log_buffers_lost,
                "etw_realtime_buffers_lost": loss.native_realtime_buffers_lost,
                "native_query_errors": loss.native_query_errors,
            }),
        )
    }

    fn begin_runtime_stop(&mut self, stop_requested: bool, reported_status: Option<WIN32_ERROR>) {
        if self.runtime_stopped {
            return;
        }
        self.stop_requested = stop_requested;
        let stopped_status = self.runtime.stop();
        self.consumer_exit_status = reported_status.or(stopped_status);
        self.runtime_stopped = true;
        self.receiver.close();

        while let Ok(raw) = self.receiver.try_recv() {
            self.queued_records_drained += 1;
            self.convert(raw);
        }
        self.flush_provisional_terminates();

        let status = self.consumer_exit_status.unwrap_or(MISSING_CONSUMER_STATUS);
        self.terminal_diagnostic =
            Some(self.consumer_stopped_diagnostic(status, self.stop_requested));
    }
}

fn consumer_stop_reason(status: WIN32_ERROR) -> &'static str {
    if status == MISSING_CONSUMER_STATUS {
        "consumer_status_missing"
    } else if status == ERROR_ACCESS_DENIED {
        "access_denied"
    } else if status == ERROR_CANCELLED {
        "cancelled"
    } else {
        "process_trace_exited"
    }
}

impl futures::Stream for WindowsEtwEventStream {
    type Item = Event;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Event>> {
        let this = self.get_mut();
        if this.terminal_emitted {
            return Poll::Ready(None);
        }
        loop {
            if !this.runtime_stopped
                && this
                    .stop_signal
                    .as_ref()
                    .is_some_and(|stop_signal| stop_signal.load(Ordering::Acquire))
            {
                this.begin_runtime_stop(true, None);
                continue;
            }
            if let Some(event) = this.ready_events.pop_front() {
                return Poll::Ready(Some(event));
            }
            if let Some(event) = this.terminal_diagnostic.take() {
                this.terminal_emitted = true;
                return Poll::Ready(Some(event));
            }
            if this.runtime_stopped {
                this.terminal_emitted = true;
                return Poll::Ready(None);
            }
            if let Some(stop_poll) = &mut this.stop_poll {
                let _ = stop_poll.poll_tick(cx);
            }
            let records_closed = match this.receiver.poll_recv(cx) {
                Poll::Ready(Some(raw)) => {
                    this.convert(raw);
                    continue;
                }
                Poll::Ready(None) => true,
                Poll::Pending => false,
            };
            match this.runtime.poll_consumer_status(cx) {
                Poll::Ready(Some(status)) => {
                    this.begin_runtime_stop(false, Some(status));
                    continue;
                }
                Poll::Ready(None) => {
                    this.begin_runtime_stop(false, None);
                    continue;
                }
                Poll::Pending if records_closed => {
                    this.begin_runtime_stop(false, None);
                    continue;
                }
                Poll::Pending => return Poll::Pending,
            }
        }
    }
}

impl Drop for WindowsEtwEventStream {
    fn drop(&mut self) {
        let _ = self.runtime.stop();
    }
}

fn current_unix_millis() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn target_zero_is_rejected_before_starting_etw() {
        assert!(validate_target_pid(0).is_err());
    }

    #[test]
    fn current_token_elevation_can_be_queried_without_starting_etw() {
        assert!(current_process_token_is_elevated().is_ok());
    }

    #[test]
    fn command_lines_are_opt_in() {
        assert!(!WindowsEtwProcessRunner::new(100).include_command_line);
        assert!(
            WindowsEtwProcessRunner::new(100)
                .with_command_line(true)
                .include_command_line
        );
    }

    #[test]
    fn stop_signal_is_optional_and_preserves_the_smoke_runner_path() {
        let default_runner = WindowsEtwProcessRunner::new(100);
        assert!(default_runner.stop_signal.is_none());

        let stop_signal = Arc::new(AtomicBool::new(false));
        let controlled_runner =
            WindowsEtwProcessRunner::new(100).with_stop_signal(Arc::clone(&stop_signal));
        assert!(
            controlled_runner
                .stop_signal
                .as_ref()
                .is_some_and(|injected| Arc::ptr_eq(injected, &stop_signal))
        );
        stop_signal.store(true, Ordering::Release);
        assert!(
            controlled_runner
                .stop_signal
                .as_ref()
                .is_some_and(|injected| injected.load(Ordering::Acquire))
        );
    }

    #[test]
    fn consumer_stop_reason_is_classified_without_starting_etw() {
        assert_eq!(consumer_stop_reason(ERROR_ACCESS_DENIED), "access_denied");
        assert_eq!(consumer_stop_reason(ERROR_CANCELLED), "cancelled");
        assert_eq!(
            consumer_stop_reason(MISSING_CONSUMER_STATUS),
            "consumer_status_missing"
        );
        assert_eq!(consumer_stop_reason(12_345), "process_trace_exited");
    }

    #[test]
    fn provisional_terminate_buffer_is_bounded_and_reports_each_loss_reason() {
        let terminate = |instance_id, sequence| ProvisionalTerminate {
            instance_id,
            raw: RawEtwEvent {
                sequence,
                timestamp: 0,
                process_id: instance_id as u32,
                thread_id: 0,
                event_id: 1,
                version: 0,
                opcode: 0x0b,
                flags: 0,
                user_data: Vec::new(),
            },
            record: ProcessEtwRecord {
                pid: instance_id as u32,
                ppid: None,
                session_id: None,
                unique_process_key: Some(instance_id),
                image_file_name: None,
                command_line: None,
                exit_status: None,
            },
            timestamp: 0,
        };
        let mut buffer = ProvisionalTerminates::new(2);
        buffer.hold(terminate(1, 1));
        buffer.hold(terminate(2, 2));
        buffer.hold(terminate(2, 3));
        assert_eq!(buffer.len(), 2);
        assert_eq!(buffer.capacity_dropped, 0);

        buffer.hold(terminate(3, 4));
        assert_eq!(buffer.len(), 2);
        assert_eq!(buffer.capacity_dropped, 1);
        assert!(!buffer.entries.contains_key(&1));

        buffer.discard_tracker_evictions(&[2, 999]);
        assert_eq!(buffer.tracker_evicted, 1);
        assert_eq!(buffer.len(), 1);
        assert_eq!(buffer.take_sorted()[0].instance_id, 3);
        assert!(buffer.entries.is_empty());
    }
}
