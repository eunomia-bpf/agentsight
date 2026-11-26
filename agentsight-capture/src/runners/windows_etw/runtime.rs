// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::RunnerError;
use std::panic::{AssertUnwindSafe, catch_unwind};
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::task::{Context, Poll};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

use windows_sys::Win32::Foundation::{
    ERROR_ACCESS_DENIED, ERROR_ALREADY_EXISTS, ERROR_CANCELLED, ERROR_CTX_CLOSE_PENDING,
    ERROR_SUCCESS, GetLastError, WIN32_ERROR,
};
use windows_sys::Win32::System::Diagnostics::Etw::{
    CONTROLTRACE_HANDLE, CloseTrace, ControlTraceW, EVENT_RECORD, EVENT_TRACE_CONTROL_QUERY,
    EVENT_TRACE_CONTROL_STOP, EVENT_TRACE_FLAG_PROCESS, EVENT_TRACE_LOGFILEW,
    EVENT_TRACE_PROPERTIES, EVENT_TRACE_REAL_TIME_MODE, EVENT_TRACE_SYSTEM_LOGGER_MODE, OpenTraceW,
    PROCESS_TRACE_MODE_EVENT_RECORD, PROCESS_TRACE_MODE_REAL_TIME, PROCESSTRACE_HANDLE,
    ProcessTrace, StartTraceW, WNODE_FLAG_TRACED_GUID,
};

const INVALID_PROCESSTRACE_HANDLE_VALUE: u64 = u64::MAX;
const ETW_STARTUP_PROBE: Duration = Duration::from_millis(100);
const ETW_CONSUMER_JOIN_TIMEOUT: Duration = Duration::from_secs(2);
const NATIVE_LOSS_QUERY_INTERVAL: Duration = Duration::from_secs(1);
const SESSION_NAME: &str = "AgentSight Windows Process Capture";
const PROCESS_PROVIDER_GUID: windows_sys::core::GUID =
    windows_sys::core::GUID::from_u128(0x3d6fa8d0_fe05_11d0_9dda_00c04fd7ba7c);
const AGENTSIGHT_ETW_CONTROL_GUID: windows_sys::core::GUID =
    windows_sys::core::GUID::from_u128(0x58544ab7_41b7_4aa0_9143_19abf65f7e41);

#[derive(Debug, Clone)]
pub(super) struct RawEtwEvent {
    pub(super) sequence: u64,
    pub(super) timestamp: i64,
    pub(super) process_id: u32,
    #[allow(dead_code)]
    pub(super) thread_id: u32,
    pub(super) event_id: u16,
    pub(super) version: u8,
    pub(super) opcode: u8,
    pub(super) flags: u16,
    pub(super) user_data: Vec<u8>,
}

struct EtwCallbackState {
    sender: mpsc::Sender<RawEtwEvent>,
    stopped: AtomicBool,
    sequence: AtomicU64,
    dropped_records: AtomicU64,
    callback_errors: AtomicU64,
    stop_errors: AtomicU64,
}

#[derive(Debug, Clone, Copy, Default)]
pub(super) struct EtwLossSnapshot {
    pub(super) application_queue_dropped_records: u64,
    pub(super) callback_errors: u64,
    pub(super) stop_errors: u64,
    pub(super) native_events_lost: u64,
    pub(super) native_log_buffers_lost: u64,
    pub(super) native_realtime_buffers_lost: u64,
    pub(super) native_query_errors: u64,
}

impl EtwCallbackState {
    fn new(sender: mpsc::Sender<RawEtwEvent>) -> Self {
        Self {
            sender,
            stopped: AtomicBool::new(false),
            sequence: AtomicU64::new(0),
            dropped_records: AtomicU64::new(0),
            callback_errors: AtomicU64::new(0),
            stop_errors: AtomicU64::new(0),
        }
    }

    fn enqueue(&self, event: RawEtwEvent) -> bool {
        if self.sender.try_send(event).is_ok() {
            true
        } else {
            self.dropped_records.fetch_add(1, Ordering::Relaxed);
            false
        }
    }

    fn loss_snapshot(&self) -> (u64, u64, u64) {
        (
            self.dropped_records.load(Ordering::Relaxed),
            self.callback_errors.load(Ordering::Relaxed),
            self.stop_errors.load(Ordering::Relaxed),
        )
    }
}

#[repr(C)]
struct EtwPropertiesBuffer {
    properties: EVENT_TRACE_PROPERTIES,
    logger_name: [u16; 128],
}

impl Default for EtwPropertiesBuffer {
    fn default() -> Self {
        Self {
            properties: EVENT_TRACE_PROPERTIES::default(),
            logger_name: [0; 128],
        }
    }
}

pub(super) struct EtwRuntime {
    state: Arc<EtwCallbackState>,
    session_name: Vec<u16>,
    properties: Box<EtwPropertiesBuffer>,
    trace_handle: PROCESSTRACE_HANDLE,
    consumer_thread: Option<std::thread::JoinHandle<()>>,
    consumer_status: mpsc::UnboundedReceiver<WIN32_ERROR>,
    consumer_exit_status: Option<WIN32_ERROR>,
    native_events_lost: u64,
    native_log_buffers_lost: u64,
    native_realtime_buffers_lost: u64,
    native_query_errors: u64,
    last_native_loss_query: Instant,
    cleanup_started: bool,
    trace_closed: bool,
    stopped: bool,
}

// ETW properties contain opaque Windows handles. They are used only on the
// thread that owns the runtime and are never dereferenced as Rust pointers.
unsafe impl Send for EtwRuntime {}

impl EtwRuntime {
    pub(super) fn start(sender: mpsc::Sender<RawEtwEvent>) -> Result<Self, RunnerError> {
        let state = Arc::new(EtwCallbackState::new(sender));
        // A non-SystemTraceControlGuid with SYSTEM_LOGGER_MODE can coexist with
        // the reserved NT Kernel Logger session.
        let mut name_utf16: Vec<u16> = SESSION_NAME.encode_utf16().collect();
        name_utf16.push(0);

        let mut buffer = Box::<EtwPropertiesBuffer>::default();
        buffer.properties.Wnode.BufferSize = size_of::<EtwPropertiesBuffer>() as u32;
        buffer.properties.Wnode.Flags = WNODE_FLAG_TRACED_GUID;
        buffer.properties.Wnode.ClientContext = 1;
        buffer.properties.Wnode.Guid = AGENTSIGHT_ETW_CONTROL_GUID;
        buffer.properties.BufferSize = 64;
        buffer.properties.MinimumBuffers = 16;
        buffer.properties.MaximumBuffers = 64;
        buffer.properties.FlushTimer = 1;
        buffer.properties.LogFileMode = EVENT_TRACE_REAL_TIME_MODE | EVENT_TRACE_SYSTEM_LOGGER_MODE;
        buffer.properties.EnableFlags = EVENT_TRACE_FLAG_PROCESS;
        buffer.properties.LoggerNameOffset = size_of::<EVENT_TRACE_PROPERTIES>() as u32;
        buffer.properties.LogFileNameOffset = 0;
        buffer.logger_name[..name_utf16.len()].copy_from_slice(&name_utf16);

        let mut session_handle = CONTROLTRACE_HANDLE { Value: 0 };
        let status = unsafe {
            StartTraceW(
                &mut session_handle as *mut _,
                name_utf16.as_ptr(),
                &mut buffer.properties,
            )
        };
        if status == ERROR_ALREADY_EXISTS {
            return Err(format!(
                "AgentSight ETW session {SESSION_NAME:?} already exists; refusing to stop another controller's session"
            )
            .into());
        }
        if status == ERROR_ACCESS_DENIED {
            return Err(
                "Windows ETW process capture requires an elevated administrator process or membership in Performance Log Users"
                    .into(),
            );
        }
        if status != ERROR_SUCCESS {
            return Err(win32_error(
                "StartTraceW (system trace capture requires an elevated terminal)",
                status,
            ));
        }

        let context = Arc::into_raw(state.clone()) as *mut core::ffi::c_void;
        let mut logfile = EVENT_TRACE_LOGFILEW {
            LoggerName: name_utf16.as_mut_ptr(),
            Anonymous1: windows_sys::Win32::System::Diagnostics::Etw::EVENT_TRACE_LOGFILEW_0 {
                ProcessTraceMode: PROCESS_TRACE_MODE_REAL_TIME | PROCESS_TRACE_MODE_EVENT_RECORD,
            },
            Anonymous2: windows_sys::Win32::System::Diagnostics::Etw::EVENT_TRACE_LOGFILEW_1 {
                EventRecordCallback: Some(etw_event_record_callback),
            },
            Context: context,
            ..Default::default()
        };

        let trace_handle = unsafe { OpenTraceW(&mut logfile) };
        if is_invalid_trace_handle(trace_handle) {
            let error = unsafe { GetLastError() };
            unsafe { drop(Arc::from_raw(context as *mut EtwCallbackState)) };
            record_cleanup_status(
                &state,
                "stop session after OpenTraceW failure",
                stop_session(&mut buffer, &name_utf16),
            );
            return Err(win32_error("OpenTraceW", error));
        }

        struct ConsumerContext {
            trace_handle: PROCESSTRACE_HANDLE,
            callback: usize,
        }
        // Both fields are opaque ETW values. The callback pointer is not
        // dereferenced as a Rust pointer; it is returned to the callback API.
        // Its raw integer form is sent to the dedicated consumer thread.

        let consumer_context = ConsumerContext {
            trace_handle,
            callback: context as usize,
        };
        let (startup_probe_tx, startup_probe_rx) = std::sync::mpsc::sync_channel(1);
        let (consumer_status_tx, consumer_status) = mpsc::unbounded_channel();
        let consumer_thread = std::thread::Builder::new()
            .name("agentsight-etw-consumer".to_string())
            .spawn(move || {
                let handles = [consumer_context.trace_handle];
                let status = unsafe {
                    ProcessTrace(handles.as_ptr(), 1, std::ptr::null(), std::ptr::null())
                };
                let _ = consumer_status_tx.send(status);
                let _ = startup_probe_tx.send(status);
                if status != ERROR_SUCCESS
                    && status != ERROR_CANCELLED
                    && let Some(state) =
                        unsafe { (consumer_context.callback as *const EtwCallbackState).as_ref() }
                {
                    state.stop_errors.fetch_add(1, Ordering::Relaxed);
                }
                unsafe {
                    drop(Arc::from_raw(
                        consumer_context.callback as *mut EtwCallbackState,
                    ))
                };
            })
            .map_err(|e| {
                let close_status = unsafe { CloseTrace(trace_handle) };
                record_cleanup_status(
                    &state,
                    "CloseTrace after consumer-thread spawn failure",
                    close_status,
                );
                unsafe { drop(Arc::from_raw(context as *mut EtwCallbackState)) };
                record_cleanup_status(
                    &state,
                    "stop session after consumer-thread spawn failure",
                    stop_session(&mut buffer, &name_utf16),
                );
                RunnerError::from(format!("failed to start ETW consumer thread: {e}"))
            })?;
        match startup_probe_rx.recv_timeout(ETW_STARTUP_PROBE) {
            Ok(status) => {
                record_cleanup_status(
                    &state,
                    "CloseTrace after ProcessTrace startup failure",
                    unsafe { CloseTrace(trace_handle) },
                );
                record_consumer_join_status(
                    &state,
                    "ProcessTrace startup failure",
                    consumer_thread,
                );
                record_cleanup_status(
                    &state,
                    "stop session after ProcessTrace startup failure",
                    stop_session(&mut buffer, &name_utf16),
                );
                return Err(win32_error("ProcessTrace startup", status));
            }
            Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
            Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => {
                record_cleanup_status(
                    &state,
                    "CloseTrace after consumer readiness channel closed",
                    unsafe { CloseTrace(trace_handle) },
                );
                record_consumer_join_status(
                    &state,
                    "consumer readiness channel closed",
                    consumer_thread,
                );
                record_cleanup_status(
                    &state,
                    "stop session after consumer readiness channel closed",
                    stop_session(&mut buffer, &name_utf16),
                );
                return Err("ETW consumer exited before ProcessTrace reported readiness".into());
            }
        }

        Ok(Self {
            state,
            session_name: name_utf16,
            properties: buffer,
            trace_handle,
            consumer_thread: Some(consumer_thread),
            consumer_status,
            consumer_exit_status: None,
            native_events_lost: 0,
            native_log_buffers_lost: 0,
            native_realtime_buffers_lost: 0,
            native_query_errors: 0,
            last_native_loss_query: Instant::now(),
            cleanup_started: false,
            trace_closed: false,
            stopped: false,
        })
    }

    pub(super) fn stop(&mut self) -> Option<WIN32_ERROR> {
        if self.stopped {
            if self.consumer_exit_status.is_none()
                && let Ok(status) = self.consumer_status.try_recv()
            {
                self.consumer_exit_status = Some(status);
            }
            return self.consumer_exit_status;
        }
        if !self.cleanup_started {
            self.cleanup_started = true;
            let stop_status = stop_session(&mut self.properties, &self.session_name);
            if stop_status == ERROR_SUCCESS {
                self.capture_native_losses();
            } else if stop_status != ERROR_CANCELLED {
                self.state.stop_errors.fetch_add(1, Ordering::Relaxed);
                log::warn!(
                    "failed to stop Windows ETW session {:?}: {} (0x{stop_status:08X})",
                    String::from_utf16_lossy(&self.session_name[..self.session_name.len() - 1]),
                    stop_status
                );
            }
        }

        // A successfully stopped real-time session should wake ProcessTrace.
        // If it does not, CloseTrace forces a blocked consumer to return.
        let mut consumer_joined =
            self.wait_for_consumer_without_dropping_handle(ETW_CONSUMER_JOIN_TIMEOUT);
        if !consumer_joined && !self.trace_closed {
            self.close_trace();
            consumer_joined =
                self.wait_for_consumer_without_dropping_handle(ETW_CONSUMER_JOIN_TIMEOUT);
        }
        if !consumer_joined {
            self.state.stop_errors.fetch_add(1, Ordering::Relaxed);
        }
        if !self.trace_closed {
            self.close_trace();
        }
        self.state.stopped.store(true, Ordering::Relaxed);
        self.stopped = consumer_joined;
        if let Ok(status) = self.consumer_status.try_recv() {
            self.consumer_exit_status = Some(status);
        }
        self.consumer_exit_status
    }

    fn close_trace(&mut self) {
        if self.trace_closed {
            return;
        }
        self.trace_closed = true;
        let close_status = unsafe { CloseTrace(self.trace_handle) };
        if close_status != ERROR_SUCCESS
            && close_status != ERROR_CANCELLED
            && close_status != ERROR_CTX_CLOSE_PENDING
        {
            self.state.stop_errors.fetch_add(1, Ordering::Relaxed);
        }
    }

    fn wait_for_consumer_without_dropping_handle(&mut self, timeout: Duration) -> bool {
        let deadline = Instant::now() + timeout;
        loop {
            let Some(thread) = self.consumer_thread.as_ref() else {
                return true;
            };
            if thread.is_finished() {
                let thread = self
                    .consumer_thread
                    .take()
                    .expect("finished consumer handle is present");
                return thread.join().is_ok();
            }
            if Instant::now() >= deadline {
                return false;
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }

    pub(super) fn loss_snapshot(&mut self) -> EtwLossSnapshot {
        if !self.stopped && self.last_native_loss_query.elapsed() >= NATIVE_LOSS_QUERY_INTERVAL {
            self.last_native_loss_query = Instant::now();
            let status = unsafe {
                ControlTraceW(
                    CONTROLTRACE_HANDLE::default(),
                    self.session_name.as_ptr(),
                    &mut self.properties.properties,
                    EVENT_TRACE_CONTROL_QUERY,
                )
            };
            if status == ERROR_SUCCESS {
                self.capture_native_losses();
            } else {
                self.native_query_errors += 1;
            }
        }
        let (application_queue_dropped_records, callback_errors, stop_errors) =
            self.state.loss_snapshot();
        EtwLossSnapshot {
            application_queue_dropped_records,
            callback_errors,
            stop_errors,
            native_events_lost: self.native_events_lost,
            native_log_buffers_lost: self.native_log_buffers_lost,
            native_realtime_buffers_lost: self.native_realtime_buffers_lost,
            native_query_errors: self.native_query_errors,
        }
    }

    fn capture_native_losses(&mut self) {
        self.native_events_lost = u64::from(self.properties.properties.EventsLost);
        self.native_log_buffers_lost = u64::from(self.properties.properties.LogBuffersLost);
        self.native_realtime_buffers_lost =
            u64::from(self.properties.properties.RealTimeBuffersLost);
    }

    pub(super) fn poll_consumer_status(
        &mut self,
        cx: &mut Context<'_>,
    ) -> Poll<Option<WIN32_ERROR>> {
        match self.consumer_status.poll_recv(cx) {
            Poll::Ready(Some(status)) => {
                self.consumer_exit_status = Some(status);
                Poll::Ready(Some(status))
            }
            other => other,
        }
    }
}

impl Drop for EtwRuntime {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

fn stop_session(buffer: &mut EtwPropertiesBuffer, name: &[u16]) -> WIN32_ERROR {
    unsafe {
        ControlTraceW(
            CONTROLTRACE_HANDLE::default(),
            name.as_ptr(),
            &mut buffer.properties,
            EVENT_TRACE_CONTROL_STOP,
        )
    }
}

fn record_cleanup_status(state: &EtwCallbackState, operation: &str, status: WIN32_ERROR) {
    if status != ERROR_SUCCESS && status != ERROR_CANCELLED {
        state.stop_errors.fetch_add(1, Ordering::Relaxed);
        log::warn!("{operation} failed with Windows error {status} (0x{status:08X})");
    }
}

fn record_consumer_join_status(
    state: &EtwCallbackState,
    operation: &str,
    thread: std::thread::JoinHandle<()>,
) {
    if thread.join().is_err() {
        state.stop_errors.fetch_add(1, Ordering::Relaxed);
        log::warn!("ETW consumer thread panicked during {operation}");
    }
}

fn is_invalid_trace_handle(handle: PROCESSTRACE_HANDLE) -> bool {
    handle.Value == INVALID_PROCESSTRACE_HANDLE_VALUE
}

pub(super) fn win32_error(operation: &str, code: WIN32_ERROR) -> RunnerError {
    RunnerError::from(format!(
        "{operation} failed with Windows error {code} (0x{code:08X})"
    ))
}

unsafe extern "system" fn etw_event_record_callback(record: *mut EVENT_RECORD) {
    let result = catch_unwind(AssertUnwindSafe(|| {
        let Some(record) = (unsafe { (record as *const EVENT_RECORD).as_ref() }) else {
            return;
        };
        let state = unsafe { &*(record.UserContext as *const EtwCallbackState) };
        if state.stopped.load(Ordering::Relaxed)
            || !guids_equal(&record.EventHeader.ProviderId, &PROCESS_PROVIDER_GUID)
        {
            return;
        }

        let user_data = if record.UserDataLength == 0 {
            Vec::new()
        } else {
            match unsafe {
                (record.UserData as *const u8)
                    .as_ref()
                    .map(|ptr| std::slice::from_raw_parts(ptr, record.UserDataLength as usize))
            } {
                Some(slice) => slice.to_vec(),
                None => {
                    state.dropped_records.fetch_add(1, Ordering::Relaxed);
                    return;
                }
            }
        };

        let event = RawEtwEvent {
            sequence: state.sequence.fetch_add(1, Ordering::Relaxed),
            timestamp: record.EventHeader.TimeStamp,
            process_id: record.EventHeader.ProcessId,
            thread_id: record.EventHeader.ThreadId,
            event_id: record.EventHeader.EventDescriptor.Id,
            version: record.EventHeader.EventDescriptor.Version,
            opcode: record.EventHeader.EventDescriptor.Opcode,
            flags: record.EventHeader.Flags,
            user_data,
        };
        state.enqueue(event);
    }));

    if result.is_err()
        && let Some(record) = unsafe { (record as *const EVENT_RECORD).as_ref() }
        && let Some(state) = unsafe { (record.UserContext as *const EtwCallbackState).as_ref() }
    {
        state.callback_errors.fetch_add(1, Ordering::Relaxed);
    }
}

fn guids_equal(left: &windows_sys::core::GUID, right: &windows_sys::core::GUID) -> bool {
    left.data1 == right.data1
        && left.data2 == right.data2
        && left.data3 == right.data3
        && left.data4 == right.data4
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::sync::mpsc;

    #[test]
    fn invalid_trace_handle_matches_the_etw_sentinel() {
        assert!(is_invalid_trace_handle(PROCESSTRACE_HANDLE {
            Value: INVALID_PROCESSTRACE_HANDLE_VALUE
        }));
        assert!(!is_invalid_trace_handle(PROCESSTRACE_HANDLE { Value: 0 }));
        assert!(!is_invalid_trace_handle(PROCESSTRACE_HANDLE { Value: 42 }));
    }

    #[tokio::test]
    async fn bounded_queue_loss_is_explicit() {
        let (sender, mut receiver) = mpsc::channel(1);
        let state = EtwCallbackState::new(sender);
        let event = RawEtwEvent {
            sequence: 0,
            timestamp: 0,
            process_id: 1,
            thread_id: 1,
            event_id: 1,
            version: 3,
            opcode: 1,
            flags: 0,
            user_data: Vec::new(),
        };
        assert!(state.enqueue(event.clone()));
        assert!(!state.enqueue(event));
        assert_eq!(state.loss_snapshot().0, 1);
        assert!(receiver.try_recv().is_ok());
    }

    #[test]
    fn consumer_status_does_not_depend_on_record_queue_capacity() {
        let (record_sender, mut record_receiver) = mpsc::channel(1);
        assert!(
            record_sender
                .try_send(RawEtwEvent {
                    sequence: 0,
                    timestamp: 0,
                    process_id: 1,
                    thread_id: 1,
                    event_id: 1,
                    version: 3,
                    opcode: 1,
                    flags: 0,
                    user_data: Vec::new(),
                })
                .is_ok()
        );
        assert!(
            record_sender
                .try_send(RawEtwEvent {
                    sequence: 1,
                    timestamp: 0,
                    process_id: 1,
                    thread_id: 1,
                    event_id: 1,
                    version: 3,
                    opcode: 1,
                    flags: 0,
                    user_data: Vec::new(),
                })
                .is_err()
        );

        let (status_sender, mut status_receiver) = mpsc::unbounded_channel();
        assert!(status_sender.send(ERROR_ACCESS_DENIED).is_ok());
        assert_eq!(status_receiver.try_recv(), Ok(ERROR_ACCESS_DENIED));
        assert!(record_receiver.try_recv().is_ok());
    }
}
