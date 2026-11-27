// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Attach-only Windows process lifecycle and TCP/UDP network capture through
//! classic ETW system providers. The runner never launches or terminates its
//! target.

use super::{EventStream, Runner, RunnerError};
use crate::analyzers::Analyzer;
use crate::event::Event;
use async_trait::async_trait;
use std::collections::{BTreeMap, HashMap, VecDeque};
use std::net::IpAddr;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::task::{Context, Poll};
use std::time::Duration;
use tokio::sync::mpsc;

use network::{EtwNetworkOp, EtwNetworkProvider, NetworkEtwRecord, parse_network_event};
use payload::{
    EtwProcessPhase, ProcessEtwRecord, event_pointer_size, filetime_to_unix_millis,
    parse_process_end, parse_process_start, parse_process_terminate,
};
use runtime::{EtwLossSnapshot, EtwProviderKind, EtwRuntime, RawEtwEvent, win32_error};
use tracker::{IngestOutcome, PidAttribution, ProcessTracker};
use windows_sys::Win32::Foundation::{
    CloseHandle, ERROR_ACCESS_DENIED, ERROR_CANCELLED, GetLastError, WIN32_ERROR,
};
use windows_sys::Win32::Security::{
    GetTokenInformation, TOKEN_ELEVATION, TOKEN_QUERY, TokenElevation,
};
use windows_sys::Win32::System::Threading::{
    GetCurrentProcess, OpenProcess, OpenProcessToken, PROCESS_QUERY_LIMITED_INFORMATION,
};

mod network;
mod payload;
mod runtime;
mod tracker;

pub const DEFAULT_ETW_QUEUE_CAPACITY: usize = 8_192;
pub const DEFAULT_ETW_NETWORK_QUEUE_CAPACITY: usize = 8_192;
const MAX_PENDING_ETW_EVENTS: usize = 4_096;
const MAX_PENDING_NETWORK_EVENTS: usize = 2_048;
const UDP_SEND_COALESCE_WINDOW_MS: u64 = 1_000;
const MAX_UDP_THROTTLE_KEYS: usize = 2_048;
const MAX_PROVISIONAL_TERMINATES: usize = 4_096;
const MISSING_CONSUMER_STATUS: WIN32_ERROR = u32::MAX;
const STOP_SIGNAL_POLL_INTERVAL: Duration = Duration::from_millis(50);

/// Captures process lifecycle events (and optionally TCP/UDP network events)
/// for a running root process and its descendants.
pub struct WindowsEtwProcessRunner {
    root_pid: u32,
    queue_capacity: usize,
    network_queue_capacity: usize,
    include_command_line: bool,
    include_network: bool,
    stop_signal: Option<Arc<AtomicBool>>,
    analyzers: Vec<Box<dyn Analyzer>>,
}

impl WindowsEtwProcessRunner {
    pub fn new(root_pid: u32) -> Self {
        Self {
            root_pid,
            queue_capacity: DEFAULT_ETW_QUEUE_CAPACITY,
            network_queue_capacity: DEFAULT_ETW_NETWORK_QUEUE_CAPACITY,
            include_command_line: false,
            include_network: false,
            stop_signal: None,
            analyzers: Vec::new(),
        }
    }

    pub fn with_queue_capacity(mut self, queue_capacity: usize) -> Self {
        self.queue_capacity = queue_capacity.max(1);
        self
    }

    pub fn with_network(mut self, include: bool) -> Self {
        self.include_network = include;
        self
    }

    pub fn with_network_queue_capacity(mut self, queue_capacity: usize) -> Self {
        self.network_queue_capacity = queue_capacity.max(1);
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
        let (network_sender, network_receiver) = if self.include_network {
            let (tx, rx) = mpsc::channel(self.network_queue_capacity);
            (Some(tx), Some(rx))
        } else {
            (None, None)
        };
        let runtime = EtwRuntime::start(sender, network_sender)?;
        let stream = WindowsEtwEventStream::new(
            receiver,
            network_receiver,
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

#[derive(Debug)]
struct UdpSendThrottle {
    window_ms: u64,
    capacity: usize,
    last_emitted_ms: HashMap<(u64, IpAddr, u16), u64>,
    order: VecDeque<(u64, IpAddr, u16)>,
    suppressed_count: u64,
    evicted_keys: u64,
}

impl UdpSendThrottle {
    fn new(window_ms: u64, capacity: usize) -> Self {
        Self {
            window_ms,
            capacity: capacity.max(1),
            last_emitted_ms: HashMap::new(),
            order: VecDeque::new(),
            suppressed_count: 0,
            evicted_keys: 0,
        }
    }

    fn should_emit(&mut self, key: (u64, IpAddr, u16), timestamp_ms: u64) -> bool {
        if let Some(prev_ms) = self.last_emitted_ms.get_mut(&key) {
            if timestamp_ms.abs_diff(*prev_ms) < self.window_ms {
                self.suppressed_count = self.suppressed_count.saturating_add(1);
                return false;
            }
            *prev_ms = (*prev_ms).max(timestamp_ms);
            return true;
        }

        while self.last_emitted_ms.len() >= self.capacity {
            let Some(oldest) = self.order.pop_front() else {
                break;
            };
            if self.last_emitted_ms.remove(&oldest).is_some() {
                self.evicted_keys = self.evicted_keys.saturating_add(1);
            }
        }
        self.last_emitted_ms.insert(key, timestamp_ms);
        self.order.push_back(key);
        true
    }
}

struct EtwEventProcessor {
    ready_events: VecDeque<Event>,
    pending_events: VecDeque<RawEtwEvent>,
    pending_network_events: VecDeque<RawEtwEvent>,
    max_pending_events: usize,
    max_pending_network_events: usize,
    udp_send_throttle: UdpSendThrottle,
    provisional_terminates: ProvisionalTerminates,
    tracker: ProcessTracker,
    include_command_line: bool,
    last_loss: EtwLossSnapshot,
    filtered_events: u64,
    duplicate_events: u64,
    pending_evicted: u64,
    network_filtered_events: u64,
    network_pending_evicted: u64,
    network_ambiguous_pid_dropped: u64,
    queued_records_drained: u64,
}

struct WindowsEtwEventStream {
    receiver: mpsc::Receiver<RawEtwEvent>,
    network_receiver: Option<mpsc::Receiver<RawEtwEvent>>,
    runtime: EtwRuntime,
    processor: EtwEventProcessor,
    stop_signal: Option<Arc<AtomicBool>>,
    stop_poll: Option<tokio::time::Interval>,
    runtime_stopped: bool,
    stop_requested: bool,
    consumer_exit_status: Option<WIN32_ERROR>,
    terminal_diagnostic: Option<Event>,
    terminal_emitted: bool,
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

impl EtwEventProcessor {
    fn new(root_pid: u32, include_command_line: bool) -> Self {
        Self::with_pending_limits(
            root_pid,
            include_command_line,
            MAX_PENDING_ETW_EVENTS,
            MAX_PENDING_NETWORK_EVENTS,
        )
    }

    fn with_pending_limits(
        root_pid: u32,
        include_command_line: bool,
        max_pending_events: usize,
        max_pending_network_events: usize,
    ) -> Self {
        Self {
            ready_events: VecDeque::new(),
            pending_events: VecDeque::new(),
            pending_network_events: VecDeque::new(),
            max_pending_events: max_pending_events.max(1),
            max_pending_network_events: max_pending_network_events.max(1),
            udp_send_throttle: UdpSendThrottle::new(
                UDP_SEND_COALESCE_WINDOW_MS,
                MAX_UDP_THROTTLE_KEYS,
            ),
            provisional_terminates: ProvisionalTerminates::new(MAX_PROVISIONAL_TERMINATES),
            tracker: ProcessTracker::new(root_pid),
            include_command_line,
            last_loss: EtwLossSnapshot::default(),
            filtered_events: 0,
            duplicate_events: 0,
            pending_evicted: 0,
            network_filtered_events: 0,
            network_pending_evicted: 0,
            network_ambiguous_pid_dropped: 0,
            queued_records_drained: 0,
        }
    }

    fn convert_process(&mut self, raw: RawEtwEvent, loss: EtwLossSnapshot) {
        self.last_loss = loss;
        match self.convert_process_once(raw.clone(), false, loss) {
            ConvertOutcome::Event {
                event,
                topology_changed,
            } => {
                self.ready_events.push_back(event);
                if topology_changed {
                    self.replay_pending_events(loss);
                    self.replay_pending_network_events(loss);
                }
            }
            ConvertOutcome::TopologyChanged => {
                self.replay_pending_events(loss);
                self.replay_pending_network_events(loss);
            }
            ConvertOutcome::Deferred => self.defer_process(raw),
            ConvertOutcome::Ignored => {}
        }
    }

    fn convert_network(&mut self, raw: RawEtwEvent, loss: EtwLossSnapshot) {
        self.last_loss = loss;
        match self.convert_network_once(raw.clone(), false, loss) {
            ConvertOutcome::Event { event, .. } => self.ready_events.push_back(event),
            ConvertOutcome::Deferred => self.defer_network(raw),
            ConvertOutcome::TopologyChanged | ConvertOutcome::Ignored => {}
        }
    }

    fn convert_process_once(
        &mut self,
        raw: RawEtwEvent,
        replay: bool,
        loss: EtwLossSnapshot,
    ) -> ConvertOutcome {
        let phase = EtwProcessPhase::from_opcode(raw.opcode);
        if phase == EtwProcessPhase::Unknown {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "unsupported_process_opcode", loss),
                topology_changed: false,
            };
        }
        let Some(timestamp) = filetime_to_unix_millis(raw.timestamp) else {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "invalid_event_timestamp", loss),
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
                event: self.diagnostic(&raw, "decode_process_payload_failed", loss),
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
            event: self.process_event(&raw, &record, phase, timestamp, instance_id, loss),
            topology_changed,
        }
    }

    fn convert_network_once(
        &mut self,
        raw: RawEtwEvent,
        replay: bool,
        loss: EtwLossSnapshot,
    ) -> ConvertOutcome {
        let provider = match raw.provider {
            EtwProviderKind::TcpIp => EtwNetworkProvider::TcpIp,
            EtwProviderKind::UdpIp => EtwNetworkProvider::UdpIp,
            EtwProviderKind::Process => return ConvertOutcome::Ignored,
        };
        let Some(timestamp) = filetime_to_unix_millis(raw.timestamp) else {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "invalid_event_timestamp", loss),
                topology_changed: false,
            };
        };
        let Some(record) = parse_network_event(provider, raw.opcode, raw.version, &raw.user_data)
        else {
            return ConvertOutcome::Event {
                event: self.diagnostic(&raw, "decode_network_payload_failed", loss),
                topology_changed: false,
            };
        };

        match self.tracker.attribute_pid(record.pid, Some(raw.timestamp)) {
            PidAttribution::Member { instance_id, comm } => {
                if record.operation == EtwNetworkOp::UdpSend
                    && !self
                        .udp_send_throttle
                        .should_emit((instance_id, record.daddr, record.dport), timestamp)
                {
                    return ConvertOutcome::Ignored;
                }
                ConvertOutcome::Event {
                    event: self.network_event(&raw, &record, timestamp, instance_id, comm, loss),
                    topology_changed: false,
                }
            }
            PidAttribution::Filtered => {
                if !replay {
                    self.network_filtered_events += 1;
                }
                ConvertOutcome::Ignored
            }
            PidAttribution::Ambiguous => {
                self.network_ambiguous_pid_dropped += 1;
                ConvertOutcome::Ignored
            }
            PidAttribution::Unresolved => ConvertOutcome::Deferred,
        }
    }

    fn capture_json(&self, loss: EtwLossSnapshot) -> serde_json::Value {
        let tracker_stats = self.tracker.stats();
        serde_json::json!({
            "queue_dropped_records": loss.application_queue_dropped_records,
            "network_queue_dropped_records": loss.network_queue_dropped_records,
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
            "network_filtered_events": self.network_filtered_events,
            "network_pending_evicted": self.network_pending_evicted,
            "network_ambiguous_pid_dropped": self.network_ambiguous_pid_dropped,
            "network_udp_throttled": self.udp_send_throttle.suppressed_count,
            "network_udp_throttle_evicted_keys": self.udp_send_throttle.evicted_keys,
            "provisional_terminates_held": self.provisional_terminates.len(),
            "provisional_terminates_capacity_dropped":
                self.provisional_terminates.capacity_dropped,
            "provisional_terminates_tracker_evicted":
                self.provisional_terminates.tracker_evicted,
        })
    }

    fn process_event(
        &mut self,
        raw: &RawEtwEvent,
        record: &ProcessEtwRecord,
        phase: EtwProcessPhase,
        timestamp: u64,
        instance_id: u64,
        loss: EtwLossSnapshot,
    ) -> Event {
        let comm = record
            .image_file_name
            .clone()
            .unwrap_or_else(|| "process".to_string());
        let event_name = phase.event_name();
        let pointer_size = event_pointer_size(raw.flags);
        self.last_loss = loss;

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
            "capture": self.capture_json(loss),
        });
        if phase.is_start() {
            data["existing"] = phase.is_existing().into();
        }

        Event::new_with_timestamp(timestamp, "process".to_string(), record.pid, comm, data)
    }

    fn network_event(
        &mut self,
        raw: &RawEtwEvent,
        record: &NetworkEtwRecord,
        timestamp: u64,
        instance_id: u64,
        comm: Option<String>,
        loss: EtwLossSnapshot,
    ) -> Event {
        let comm = comm.unwrap_or_else(|| "process".to_string());
        let peer_endpoint = record.peer_endpoint();
        let local_endpoint = record.local_endpoint();
        self.last_loss = loss;

        // Deliberately omit `host` so raw socket endpoints never fabricate
        // HTTP/TLS/LLM targets in canonicalization or projection.
        let data = serde_json::json!({
            "event": record.operation.event_name(),
            "pid": record.pid,
            "comm": comm,
            "detail": peer_endpoint,
            "protocol": record.provider.protocol(),
            "ip_version": record.ip_version,
            "port": record.primary_port(),
            "local_endpoint": local_endpoint,
            "peer_endpoint": peer_endpoint,
            "size": record.size,
            "conn_id": record.conn_id,
            "process_instance_id": instance_id,
            "capture_root_pid": self.tracker.root_pid(),
            "etw": {
                "provider": record.provider.as_str(),
                "provider_guid": record.provider.guid_str(),
                "event_id": raw.event_id,
                "version": raw.version,
                "opcode": raw.opcode,
                "operation": record.operation.operation_name(record.ip_version),
                "header_flags": raw.flags,
                "saddr": record.saddr.to_string(),
                "sport": record.sport,
                "daddr": record.daddr.to_string(),
                "dport": record.dport,
                "seqnum": record.seqnum,
            },
            "capture": self.capture_json(loss),
        });

        Event::new_with_timestamp(timestamp, "process".to_string(), record.pid, comm, data)
    }

    fn defer_process(&mut self, raw: RawEtwEvent) {
        if self.pending_events.len() >= self.max_pending_events {
            self.pending_events.pop_front();
            self.pending_evicted += 1;
        }
        self.pending_events.push_back(raw);
    }

    fn defer_network(&mut self, raw: RawEtwEvent) {
        if self.pending_network_events.len() >= self.max_pending_network_events {
            self.pending_network_events.pop_front();
            self.network_pending_evicted += 1;
        }
        self.pending_network_events.push_back(raw);
    }

    fn replay_pending_events(&mut self, loss: EtwLossSnapshot) {
        loop {
            if self.pending_events.is_empty() {
                break;
            }
            let pending = std::mem::take(&mut self.pending_events);
            let previous_len = pending.len();
            let mut topology_changed = false;
            for raw in pending {
                match self.convert_process_once(raw.clone(), true, loss) {
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

    fn replay_pending_network_events(&mut self, loss: EtwLossSnapshot) {
        if self.pending_network_events.is_empty() {
            return;
        }
        let pending = std::mem::take(&mut self.pending_network_events);
        for raw in pending {
            match self.convert_network_once(raw.clone(), true, loss) {
                ConvertOutcome::Event { event, .. } => self.ready_events.push_back(event),
                ConvertOutcome::Deferred => self.pending_network_events.push_back(raw),
                ConvertOutcome::TopologyChanged | ConvertOutcome::Ignored => {}
            }
        }
    }

    fn flush_provisional_terminates(&mut self, loss: EtwLossSnapshot) {
        for terminate in self.provisional_terminates.take_sorted() {
            let event = self.process_event(
                &terminate.raw,
                &terminate.record,
                EtwProcessPhase::Terminate,
                terminate.timestamp,
                terminate.instance_id,
                loss,
            );
            self.ready_events.push_back(event);
        }
    }

    fn diagnostic(&mut self, raw: &RawEtwEvent, reason: &str, loss: EtwLossSnapshot) -> Event {
        self.last_loss = loss;
        let provider = match raw.provider {
            EtwProviderKind::Process => "SystemTraceProvider",
            EtwProviderKind::TcpIp => "TcpIp",
            EtwProviderKind::UdpIp => "UdpIp",
        };
        Event::new_with_timestamp(
            current_unix_millis(),
            "diagnostic".to_string(),
            raw.process_id,
            "windows_etw".to_string(),
            serde_json::json!({
                "type": "runner_parse_error",
                "event": "ETW_DECODE_ERROR",
                "reason": reason,
                "provider": provider,
                "sequence": raw.sequence,
                "event_id": raw.event_id,
                "version": raw.version,
                "opcode": raw.opcode,
                "header_flags": raw.flags,
                "payload_len": raw.user_data.len(),
                "queue_dropped_records": loss.application_queue_dropped_records,
                "network_queue_dropped_records": loss.network_queue_dropped_records,
                "callback_errors": loss.callback_errors,
                "stop_errors": loss.stop_errors,
                "etw_events_lost": loss.native_events_lost,
                "etw_log_buffers_lost": loss.native_log_buffers_lost,
                "etw_realtime_buffers_lost": loss.native_realtime_buffers_lost,
                "native_query_errors": loss.native_query_errors,
            }),
        )
    }

    fn consumer_stopped_diagnostic(
        &mut self,
        status: WIN32_ERROR,
        stop_requested: bool,
        loss: EtwLossSnapshot,
    ) -> Event {
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
                "pending_network_records": self.pending_network_events.len(),
                "pending_evicted": self.pending_evicted,
                "network_filtered_events": self.network_filtered_events,
                "network_pending_evicted": self.network_pending_evicted,
                "network_ambiguous_pid_dropped": self.network_ambiguous_pid_dropped,
                "network_udp_throttled": self.udp_send_throttle.suppressed_count,
                "network_udp_throttle_evicted_keys": self.udp_send_throttle.evicted_keys,
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
                "network_queue_dropped_records": loss.network_queue_dropped_records,
                "callback_errors": loss.callback_errors,
                "stop_errors": loss.stop_errors,
                "etw_events_lost": loss.native_events_lost,
                "etw_log_buffers_lost": loss.native_log_buffers_lost,
                "etw_realtime_buffers_lost": loss.native_realtime_buffers_lost,
                "native_query_errors": loss.native_query_errors,
            }),
        )
    }
}

impl WindowsEtwEventStream {
    fn new(
        receiver: mpsc::Receiver<RawEtwEvent>,
        network_receiver: Option<mpsc::Receiver<RawEtwEvent>>,
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
            network_receiver,
            runtime,
            processor: EtwEventProcessor::new(root_pid, include_command_line),
            stop_signal,
            stop_poll,
            runtime_stopped: false,
            stop_requested: false,
            consumer_exit_status: None,
            terminal_diagnostic: None,
            terminal_emitted: false,
        }
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
        if let Some(net_rx) = &mut self.network_receiver {
            net_rx.close();
        }

        let loss = self.runtime.loss_snapshot();
        while let Ok(raw) = self.receiver.try_recv() {
            self.processor.queued_records_drained += 1;
            self.processor.convert_process(raw, loss);
        }
        if let Some(net_rx) = &mut self.network_receiver {
            while let Ok(raw) = net_rx.try_recv() {
                self.processor.queued_records_drained += 1;
                self.processor.convert_network(raw, loss);
            }
        }
        self.processor.flush_provisional_terminates(loss);

        let status = self.consumer_exit_status.unwrap_or(MISSING_CONSUMER_STATUS);
        self.terminal_diagnostic = Some(self.processor.consumer_stopped_diagnostic(
            status,
            self.stop_requested,
            loss,
        ));
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
            if let Some(event) = this.processor.ready_events.pop_front() {
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
            // Drain process lifecycle events before network records so
            // ProcessTracker has the newest PID membership before attribution.
            let process_closed = match this.receiver.poll_recv(cx) {
                Poll::Ready(Some(raw)) => {
                    let loss = this.runtime.loss_snapshot();
                    this.processor.convert_process(raw, loss);
                    continue;
                }
                Poll::Ready(None) => true,
                Poll::Pending => false,
            };
            let network_closed = match this.network_receiver.as_mut() {
                Some(net_rx) => match net_rx.poll_recv(cx) {
                    Poll::Ready(Some(raw)) => {
                        let loss = this.runtime.loss_snapshot();
                        this.processor.convert_network(raw, loss);
                        continue;
                    }
                    Poll::Ready(None) => true,
                    Poll::Pending => false,
                },
                None => true,
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
                Poll::Pending if process_closed && network_closed => {
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
    use super::network::tcpip_opcode;
    use super::network::tests::{build_tcpip_v2_payload, build_udpip_v2_payload};
    use super::network::udpip_opcode;
    use super::*;
    use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};
    use windows_sys::Win32::System::Diagnostics::Etw::EVENT_HEADER_FLAG_64_BIT_HEADER;

    const WINDOWS_EPOCH_DELTA_100NS: i64 = 116_444_736_000_000_000;

    fn process_start_v4_payload(pid: u32, ppid: u32, key: u64, image: &str) -> Vec<u8> {
        let mut data = Vec::new();
        data.extend(key.to_le_bytes());
        data.extend(pid.to_le_bytes());
        data.extend(ppid.to_le_bytes());
        data.extend(1_u32.to_le_bytes()); // session_id
        data.extend(0_i32.to_le_bytes()); // exit_status
        data.extend(0_u64.to_le_bytes()); // dir table base / unknown pointer
        data.extend(0_u32.to_le_bytes()); // flags
        data.extend(0_u32.to_le_bytes()); // null SID
        data.extend(image.as_bytes());
        data.push(0);
        data.extend([0_u8, 0_u8]); // empty UTF-16 command line
        data
    }

    fn raw_process_start(
        seq: u64,
        ts_ms: i64,
        pid: u32,
        ppid: u32,
        key: u64,
        image: &str,
    ) -> RawEtwEvent {
        RawEtwEvent {
            provider: EtwProviderKind::Process,
            sequence: seq,
            timestamp: WINDOWS_EPOCH_DELTA_100NS + ts_ms * 10_000,
            process_id: ppid,
            thread_id: 1,
            event_id: 1,
            version: 4,
            opcode: 1,
            flags: EVENT_HEADER_FLAG_64_BIT_HEADER as u16,
            user_data: process_start_v4_payload(pid, ppid, key, image),
        }
    }

    fn raw_network_event(
        provider: EtwProviderKind,
        seq: u64,
        ts_ms: i64,
        opcode: u8,
        version: u8,
        user_data: Vec<u8>,
    ) -> RawEtwEvent {
        RawEtwEvent {
            provider,
            sequence: seq,
            timestamp: WINDOWS_EPOCH_DELTA_100NS + ts_ms * 10_000,
            process_id: 0,
            thread_id: 1,
            event_id: u16::from(opcode),
            version,
            opcode,
            flags: EVENT_HEADER_FLAG_64_BIT_HEADER as u16,
            user_data,
        }
    }

    #[test]
    fn target_zero_is_rejected_before_starting_etw() {
        assert!(validate_target_pid(0).is_err());
    }

    #[test]
    fn current_token_elevation_can_be_queried_without_starting_etw() {
        assert!(current_process_token_is_elevated().is_ok());
    }

    #[test]
    fn command_lines_and_network_capture_are_opt_in() {
        let default_runner = WindowsEtwProcessRunner::new(100);
        assert!(!default_runner.include_command_line);
        assert!(!default_runner.include_network);
        assert_eq!(
            default_runner.network_queue_capacity,
            DEFAULT_ETW_NETWORK_QUEUE_CAPACITY
        );

        let configured = WindowsEtwProcessRunner::new(100)
            .with_command_line(true)
            .with_network(true)
            .with_network_queue_capacity(512);
        assert!(configured.include_command_line);
        assert!(configured.include_network);
        assert_eq!(configured.network_queue_capacity, 512);
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
                provider: EtwProviderKind::Process,
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

    #[test]
    fn converts_tcp_and_udp_events_without_fabricating_host() {
        let mut processor = EtwEventProcessor::new(100, false);
        let loss = EtwLossSnapshot::default();

        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                1,
                1_000,
                tcpip_opcode::CONNECT_IPV4,
                2,
                build_tcpip_v2_payload(
                    100,
                    0,
                    IpAddr::V4(Ipv4Addr::new(93, 184, 216, 34)),
                    IpAddr::V4(Ipv4Addr::new(192, 168, 1, 10)),
                    443,
                    51234,
                    16,
                    11,
                    0x1001,
                ),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                2,
                1_010,
                tcpip_opcode::ACCEPT_IPV6,
                2,
                build_tcpip_v2_payload(
                    100,
                    0,
                    IpAddr::V6("2001:4860:4860::8888".parse().unwrap()),
                    IpAddr::V6(Ipv6Addr::LOCALHOST),
                    55555,
                    8080,
                    16,
                    12,
                    0x1002,
                ),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                3,
                1_020,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(
                    100,
                    48,
                    IpAddr::V4(Ipv4Addr::new(8, 8, 8, 8)),
                    IpAddr::V4(Ipv4Addr::new(192, 168, 1, 10)),
                    53,
                    54000,
                    13,
                    0x1003,
                ),
            ),
            loss,
        );

        assert_eq!(processor.ready_events.len(), 3);
        let connect = processor.ready_events.pop_front().unwrap();
        assert_eq!(connect.source, "process");
        assert_eq!(connect.pid, 100);
        assert_eq!(connect.timestamp, 1_000);
        assert_eq!(connect.data["event"], "NET_CONNECT");
        assert_eq!(connect.data["protocol"], "tcp");
        assert_eq!(connect.data["detail"], "93.184.216.34:443");
        assert_eq!(connect.data["local_endpoint"], "192.168.1.10:51234");
        assert_eq!(connect.data["peer_endpoint"], "93.184.216.34:443");
        assert_eq!(connect.data["capture_root_pid"], 100);
        assert_eq!(connect.data["process_instance_id"], 0);
        assert!(connect.data.get("host").is_none());

        let accept = processor.ready_events.pop_front().unwrap();
        assert_eq!(accept.data["event"], "NET_ACCEPT");
        assert_eq!(accept.data["ip_version"], 6);
        assert_eq!(accept.data["port"], 8080);
        assert_eq!(accept.data["local_endpoint"], "[::1]:8080");
        assert_eq!(accept.data["peer_endpoint"], "[2001:4860:4860::8888]:55555");
        assert!(accept.data.get("host").is_none());

        let udp = processor.ready_events.pop_front().unwrap();
        assert_eq!(udp.data["event"], "NET_UDP_SEND");
        assert_eq!(udp.data["protocol"], "udp");
        assert_eq!(udp.data["detail"], "8.8.8.8:53");
        assert!(udp.data.get("host").is_none());
    }

    #[test]
    fn reordered_child_network_event_replays_once_when_child_starts() {
        let mut processor = EtwEventProcessor::new(100, false);
        let loss = EtwLossSnapshot::default();

        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                1,
                1_050,
                tcpip_opcode::CONNECT_IPV4,
                2,
                build_tcpip_v2_payload(
                    200,
                    0,
                    IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
                    IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
                    7395,
                    51000,
                    16,
                    1,
                    2,
                ),
            ),
            loss,
        );
        assert!(processor.ready_events.is_empty());
        assert_eq!(processor.pending_network_events.len(), 1);

        processor.convert_process(raw_process_start(2, 1_000, 200, 100, 20, "curl.exe"), loss);
        assert!(processor.pending_network_events.is_empty());
        assert_eq!(processor.ready_events.len(), 2);

        let proc_event = processor.ready_events.pop_front().unwrap();
        assert_eq!(proc_event.data["event"], "EXEC");
        let net_event = processor.ready_events.pop_front().unwrap();
        assert_eq!(net_event.data["event"], "NET_CONNECT");
        assert_eq!(net_event.pid, 200);
        assert_eq!(net_event.comm, "curl.exe");
        assert_eq!(net_event.data["capture_root_pid"], 100);
        assert_eq!(
            net_event.data["process_instance_id"],
            proc_event.data["process_instance_id"]
        );
    }

    #[test]
    fn bounded_pending_network_evictions_and_ambiguous_pids_are_counted_separately() {
        let mut processor = EtwEventProcessor::with_pending_limits(100, false, 4, 2);
        let loss = EtwLossSnapshot::default();

        for (seq, port) in [(1, 8001), (2, 8002), (3, 8003)] {
            processor.convert_network(
                raw_network_event(
                    EtwProviderKind::TcpIp,
                    seq,
                    1_000 + seq as i64,
                    tcpip_opcode::CONNECT_IPV4,
                    2,
                    build_tcpip_v2_payload(
                        900,
                        0,
                        IpAddr::V4(Ipv4Addr::LOCALHOST),
                        IpAddr::V4(Ipv4Addr::LOCALHOST),
                        port,
                        50000,
                        16,
                        1,
                        seq as u32,
                    ),
                ),
                loss,
            );
        }
        assert_eq!(processor.pending_network_events.len(), 2);
        assert_eq!(processor.network_pending_evicted, 1);
        assert_eq!(processor.pending_evicted, 0);

        // Create an ambiguous live generation for PID 300.
        processor.convert_process(raw_process_start(4, 2_000, 300, 100, 30, "a.exe"), loss);
        processor.convert_process(raw_process_start(5, 2_010, 300, 100, 31, "b.exe"), loss);
        processor.ready_events.clear();

        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                6,
                2_020,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(
                    300,
                    32,
                    IpAddr::V4(Ipv4Addr::new(8, 8, 8, 8)),
                    IpAddr::V4(Ipv4Addr::LOCALHOST),
                    53,
                    50001,
                    1,
                    2,
                ),
            ),
            loss,
        );
        assert!(processor.ready_events.is_empty());
        assert_eq!(processor.network_ambiguous_pid_dropped, 1);
    }

    #[test]
    fn malformed_network_payload_emits_decode_error_diagnostic() {
        let mut processor = EtwEventProcessor::new(100, false);
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                1,
                1_000,
                tcpip_opcode::CONNECT_IPV4,
                2,
                vec![1, 2, 3],
            ),
            EtwLossSnapshot::default(),
        );
        assert_eq!(processor.ready_events.len(), 1);
        let diag = processor.ready_events.pop_front().unwrap();
        assert_eq!(diag.source, "diagnostic");
        assert_eq!(diag.data["type"], "runner_parse_error");
        assert_eq!(diag.data["event"], "ETW_DECODE_ERROR");
        assert_eq!(diag.data["reason"], "decode_network_payload_failed");
        assert_eq!(diag.data["provider"], "TcpIp");
    }

    #[test]
    fn udp_send_coalesces_per_instance_and_destination_within_window_without_throttling_tcp() {
        let mut processor = EtwEventProcessor::new(100, false);
        let loss = EtwLossSnapshot::default();
        processor.convert_process(raw_process_start(1, 900, 200, 100, 20, "worker.exe"), loss);
        processor.ready_events.clear();

        let daddr = IpAddr::V4(Ipv4Addr::new(38, 34, 29, 138));
        let saddr = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 10));

        // Repeated UDP sends to the same destination within <1s coalesce even across ephemeral sports.
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                2,
                1_000,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(100, 40, daddr, saddr, 38698, 50001, 1, 10),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                3,
                1_500,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(100, 40, daddr, saddr, 38698, 50002, 2, 11),
            ),
            loss,
        );
        // Same destination once the 1,000ms window elapses is emitted again.
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                4,
                2_000,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(100, 40, daddr, saddr, 38698, 50003, 3, 12),
            ),
            loss,
        );
        // Different destination port and different process_instance_id bypass the first key's window.
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                5,
                1_100,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(100, 40, daddr, saddr, 443, 50004, 4, 13),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::UdpIp,
                6,
                1_200,
                udpip_opcode::SEND_IPV4,
                2,
                build_udpip_v2_payload(200, 40, daddr, saddr, 38698, 50005, 5, 14),
            ),
            loss,
        );

        // Repeated TCP lifecycle events to the exact same destination are never throttled.
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                7,
                1_000,
                tcpip_opcode::CONNECT_IPV4,
                2,
                build_tcpip_v2_payload(100, 0, daddr, saddr, 38698, 51000, 16, 1, 20),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                8,
                1_050,
                tcpip_opcode::DISCONNECT_IPV4,
                2,
                build_tcpip_v2_payload(100, 0, daddr, saddr, 38698, 51000, 0, 2, 20),
            ),
            loss,
        );
        processor.convert_network(
            raw_network_event(
                EtwProviderKind::TcpIp,
                9,
                1_100,
                tcpip_opcode::CONNECT_IPV4,
                2,
                build_tcpip_v2_payload(100, 0, daddr, saddr, 38698, 51001, 16, 3, 21),
            ),
            loss,
        );

        assert_eq!(processor.udp_send_throttle.suppressed_count, 1);
        assert_eq!(processor.ready_events.len(), 7);
        let emitted: Vec<&str> = processor
            .ready_events
            .iter()
            .map(|ev| ev.data["event"].as_str().unwrap())
            .collect();
        assert_eq!(
            emitted,
            vec![
                "NET_UDP_SEND",
                "NET_UDP_SEND",
                "NET_UDP_SEND",
                "NET_UDP_SEND",
                "NET_CONNECT",
                "NET_DISCONNECT",
                "NET_CONNECT",
            ]
        );
        assert_eq!(processor.ready_events.back().unwrap().data["capture"]["network_udp_throttled"], 1);
    }

    #[test]
    fn udp_send_throttle_evicts_oldest_keys_when_capacity_is_reached() {
        let mut throttle = UdpSendThrottle::new(1_000, 2);
        let ip = IpAddr::V4(Ipv4Addr::new(8, 8, 8, 8));

        assert!(throttle.should_emit((0, ip, 53), 100));
        assert!(throttle.should_emit((0, ip, 443), 200));
        assert_eq!(throttle.evicted_keys, 0);

        assert!(throttle.should_emit((0, ip, 8080), 300));
        assert_eq!(throttle.evicted_keys, 1);
        assert_eq!(throttle.last_emitted_ms.len(), 2);
        assert_eq!(throttle.order.len(), 2);
        assert!(!throttle.last_emitted_ms.contains_key(&(0, ip, 53)));
        assert!(throttle.should_emit((0, ip, 53), 350));
        assert_eq!(throttle.evicted_keys, 2);
    }
}
