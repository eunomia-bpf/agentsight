// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process tracing probe - captures process creation and stdout output

use crate::config;
use anyhow::{Context, Result};
use libbpf_rs::{
    Link, MapHandle, RingBufferBuilder,
    skel::{OpenSkel, SkelBuilder},
};
use std::{
    mem::MaybeUninit,
    os::fd::{AsFd, AsRawFd},
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};

// ─── Generated skeleton ───────────────────────────────────────────────────────
mod bpf {
    include!(concat!(env!("OUT_DIR"), "/proctrace.skel.rs"));
    include!(concat!(env!("OUT_DIR"), "/proctrace.rs"));
}
use bpf::*;

// ─── Constants ────────────────────────────────────────────────────────────────
const POLL_TIMEOUT_MS: u64 = 100;

// Re-export types from generated bindings
pub type ProcEventHeader = bpf::proc_event_header;
pub type ProcExecData = bpf::proc_exec_data;
pub type ProcStdoutData = bpf::proc_stdout_data;
pub type ProcExitData = bpf::proc_exit_data;
pub type ProcEvent = bpf::proc_event_t;

// Event type constants
pub const PROCTRACE_EVENT_EXEC: u32 = 1;
pub const PROCTRACE_EVENT_STDOUT: u32 = 2;
pub const PROCTRACE_EVENT_EXIT: u32 = 3;

/// Variable-length event wrapper that parses data from ring buffer
#[derive(Debug)]
pub enum VariableEvent {
    Exec {
        header: ProcEventHeader,
        filename: String,
        args: String,
    },
    Stdout {
        header: ProcEventHeader,
        fd: u32,
        payload: Vec<u8>,
    },
    Exit {
        header: ProcEventHeader,
        exit_code: i32,
    },
    Unknown(u32),
}

impl VariableEvent {
    /// Parse a variable-length event from raw ring buffer data
    pub fn from_bytes(data: &[u8]) -> Option<Self> {
        if data.len() < std::mem::size_of::<ProcEventHeader>() {
            return None;
        }

        // SAFETY: BPF guarantees proper alignment and layout
        let raw_header = unsafe { &*(data.as_ptr() as *const ProcEventHeader) };
        
        // Convert ktime to Unix timestamp
        let mut header = *raw_header;
        header.timestamp_ns = config::ktime_to_unix_ns(raw_header.timestamp_ns);

        match header.event_type {
            PROCTRACE_EVENT_EXEC => Self::parse_exec(&header, data),
            PROCTRACE_EVENT_STDOUT => Self::parse_stdout(&header, data),
            PROCTRACE_EVENT_EXIT => Self::parse_exit(&header, data),
            other => Some(VariableEvent::Unknown(other)),
        }
    }

    fn parse_exec(header: &ProcEventHeader, data: &[u8]) -> Option<Self> {
        let header_size = std::mem::size_of::<ProcEventHeader>();
        let exec_data_size = std::mem::size_of::<ProcExecData>();

        if data.len() < header_size + exec_data_size {
            return None;
        }

        // SAFETY: Bounds checked above
        let exec_data = unsafe { &*(data.as_ptr().add(header_size) as *const ProcExecData) };

        // Parse filename (null-terminated)
        let filename = exec_data
            .filename
            .iter()
            .take_while(|&&c| c != 0)
            .map(|&c| c as u8)
            .collect::<Vec<u8>>();
        let filename = String::from_utf8_lossy(&filename).into_owned();

        // Parse variable-length args_buf
        let args_offset = header_size + exec_data_size;
        let args_size = exec_data.args_size as usize;
        let args_end = args_offset + args_size;

        let args = if args_size > 0 && data.len() >= args_end {
            let args_buf = &data[args_offset..args_end];
            Self::parse_args(args_buf, exec_data.args_count)
        } else {
            String::new()
        };

        Some(VariableEvent::Exec {
            header: *header,
            filename,
            args,
        })
    }

    fn parse_args(buf: &[u8], args_count: u32) -> String {
        let mut parts: Vec<&str> = Vec::new();
        let mut start = 0;

        while start < buf.len() {
            let end = buf[start..]
                .iter()
                .position(|&c| c == 0)
                .map(|p| start + p)
                .unwrap_or(buf.len());

            if let Ok(s) = std::str::from_utf8(&buf[start..end]) {
                if !s.is_empty() {
                    parts.push(s);
                }
            }
            start = end + 1;
        }

        if parts.is_empty() {
            return String::new();
        }

        let mut result = parts.join(" ");
        if args_count as usize > parts.len() {
            result.push_str(" ...");
        }
        result
    }

    fn parse_stdout(header: &ProcEventHeader, data: &[u8]) -> Option<Self> {
        let header_size = std::mem::size_of::<ProcEventHeader>();
        let stdout_data_size = std::mem::size_of::<ProcStdoutData>();

        if data.len() < header_size + stdout_data_size {
            return None;
        }

        // SAFETY: Bounds checked above
        let stdout_data = unsafe { &*(data.as_ptr().add(header_size) as *const ProcStdoutData) };

        // Parse variable-length payload
        let payload_offset = header_size + stdout_data_size;
        let payload_len = stdout_data.payload_len as usize;
        let payload_end = payload_offset + payload_len;

        let payload = if payload_len > 0 && data.len() >= payload_end {
            data[payload_offset..payload_end].to_vec()
        } else {
            Vec::new()
        };

        Some(VariableEvent::Stdout {
            header: *header,
            fd: stdout_data.fd,
            payload,
        })
    }

    fn parse_exit(header: &ProcEventHeader, data: &[u8]) -> Option<Self> {
        let header_size = std::mem::size_of::<ProcEventHeader>();
        let exit_data_size = std::mem::size_of::<ProcExitData>();

        if data.len() < header_size + exit_data_size {
            return None;
        }

        // SAFETY: Bounds checked above
        let exit_data = unsafe { &*(data.as_ptr().add(header_size) as *const ProcExitData) };

        Some(VariableEvent::Exit {
            header: *header,
            exit_code: exit_data.exit_code,
        })
    }

    /// Get event type as string
    pub fn event_type_str(&self) -> &'static str {
        match self {
            VariableEvent::Exec { .. } => "exec",
            VariableEvent::Stdout { .. } => "stdout",
            VariableEvent::Exit { .. } => "exit",
            VariableEvent::Unknown(_) => "unknown",
        }
    }

    /// Get process name as string
    pub fn comm_str(&self) -> String {
        let comm = match self {
            VariableEvent::Exec { header, .. } => &header.comm,
            VariableEvent::Stdout { header, .. } => &header.comm,
            VariableEvent::Exit { header, .. } => &header.comm,
            VariableEvent::Unknown(_) => return String::from("unknown"),
        };

        comm.iter()
            .take_while(|&&c| c != 0)
            .map(|&c| c as u8)
            .collect::<Vec<u8>>()
            .pipe(|v| String::from_utf8_lossy(&v).into_owned())
    }
}

// Helper trait for pipe syntax
trait Pipe<T> {
    fn pipe<F, R>(self, f: F) -> R
    where
        F: FnOnce(T) -> R;
}
impl<T> Pipe<T> for T {
    fn pipe<F, R>(self, f: F) -> R
    where
        F: FnOnce(T) -> R,
    {
        f(self)
    }
}

impl ProcEvent {
    /// Get the event type as a string
    pub fn event_type_str(&self) -> &'static str {
        match self.event_type {
            1 => "exec",
            2 => "stdout",
            3 => "exit",
            _ => "unknown",
        }
    }

    /// Get stdout payload as string (for STDOUT events)
    pub fn stdout_payload(&self) -> Option<&str> {
        if self.event_type != PROCTRACE_EVENT_STDOUT || self.buf_filled == 0 {
            return None;
        }
        std::str::from_utf8(&self.buf[..self.buf_size as usize]).ok()
    }

    /// Get command arguments (for EXEC events)
    /// args_buf stores each argument as a null-terminated string packed consecutively.
    /// Returns a single space-joined string, with "..." appended if args were truncated.
    pub fn args_str(&self) -> Option<String> {
        if self.event_type != PROCTRACE_EVENT_EXEC {
            return None;
        }
        let total = self.args_size as usize;
        if total == 0 {
            return None;
        }
        // args_buf is a flat array of null-terminated strings (i8 in generated bindings)
        let raw = &self.args_buf[..total.min(self.args_buf.len())];
        // SAFETY: reinterpret i8 slice as u8 slice for UTF-8 parsing
        let buf: &[u8] =
            unsafe { std::slice::from_raw_parts(raw.as_ptr() as *const u8, raw.len()) };
        let mut parts: Vec<&str> = Vec::new();
        let mut start = 0;
        while start < buf.len() {
            // Find the next null terminator
            let end = buf[start..]
                .iter()
                .position(|&c| c == 0)
                .map(|p| start + p)
                .unwrap_or(buf.len());
            if let Ok(s) = std::str::from_utf8(&buf[start..end]) {
                if !s.is_empty() {
                    parts.push(s);
                }
            }
            start = end + 1;
        }
        if parts.is_empty() {
            return None;
        }
        let mut result = parts.join(" ");
        // args_count > actual collected entries means there were more args
        if self.args_count as usize > parts.len() {
            result.push_str(" ...");
        }
        Some(result)
    }

    /// Get the executable filename (for EXEC events)
    pub fn filename_str(&self) -> Option<String> {
        if self.event_type != PROCTRACE_EVENT_EXEC {
            return None;
        }
        let len = self
            .filename
            .iter()
            .position(|&c| c == 0)
            .unwrap_or(self.filename.len());
        // SAFETY: reinterpret i8 slice as u8 for UTF-8 parsing
        let bytes: &[u8] =
            unsafe { std::slice::from_raw_parts(self.filename[..len].as_ptr() as *const u8, len) };
        std::str::from_utf8(bytes).ok().map(|s| s.to_string())
    }

    /// Get process name as string
    pub fn comm_str(&self) -> String {
        let bytes: Vec<u8> = self
            .comm
            .iter()
            .map(|&c| c as u8)
            .take_while(|&b| b != 0)
            .collect();
        String::from_utf8_lossy(&bytes).into_owned()
    }
}

// ─── Main struct ──────────────────────────────────────────────────────────────
pub struct ProcTrace {
    _open_object: Box<MaybeUninit<libbpf_rs::OpenObject>>,
    skel: Box<ProctraceSkel<'static>>,
    _links: Vec<Link>,
    tx: crossbeam_channel::Sender<VariableEvent>,
    rx: crossbeam_channel::Receiver<VariableEvent>,
}

impl ProcTrace {
    /// Create a new ProcTrace with optional target PIDs and UID filter
    pub fn new_with_target(target_pids: &[u32], target_uid: Option<u32>) -> Result<Self> {
        Self::new_with_target_and_map(target_pids, target_uid, None, None)
    }

    /// Create a new ProcTrace with optional target PIDs, UID filter, and external traced_processes map
    ///
    /// # Arguments
    /// * `target_pids` - Initial PIDs to trace (empty means trace all)
    /// * `target_uid` - Optional UID filter
    /// * `traced_processes` - Optional external MapHandle for traced_processes (for map reuse)
    /// * `rb` - Optional external MapHandle for shared ring buffer (for map reuse)
    pub fn new_with_target_and_map(
        target_pids: &[u32],
        target_uid: Option<u32>,
        traced_processes: Option<&MapHandle>,
        rb: Option<&MapHandle>,
    ) -> Result<Self> {
        // Open + load skeleton
        let mut builder = ProctraceSkelBuilder::default();
        builder.obj_builder.debug(config::verbose());

        let open_object = Box::new(MaybeUninit::<libbpf_rs::OpenObject>::uninit());
        let mut open_skel = builder.open().context("failed to open BPF object")?;

        // Set rodata uid filter before loading
        if let Some(uid) = target_uid {
            open_skel.rodata_mut().targ_uid = uid;
        }

        // If external traced_processes map is provided, reuse its fd
        if let Some(map) = traced_processes {
            open_skel
                .maps_mut()
                .traced_processes()
                .reuse_fd(map.as_fd())
                .context("failed to reuse external traced_processes map")?;
        }

        // If external rb map is provided, reuse its fd
        if let Some(map) = rb {
            open_skel
                .maps_mut()
                .rb()
                .reuse_fd(map.as_fd())
                .context("failed to reuse external rb map")?;
        }

        let mut skel = open_skel.load().context("failed to load BPF object")?;

        // Populate traced_processes map with target PIDs (only if not reusing external map)
        // If target_pids is empty, all processes will be traced (BPF side skips filter)
        if traced_processes.is_none() {
            for &pid in target_pids {
                let key = pid.to_ne_bytes();
                let val = 1u32.to_ne_bytes();
                skel.maps_mut()
                    .traced_processes()
                    .update(&key, &val, libbpf_rs::MapFlags::ANY)
                    .with_context(|| format!("failed to add pid {} to traced_processes", pid))?;
            }
        }

        // SAFETY: skel borrows open_object which lives in a Box<MaybeUninit>
        // on the heap. We pin both together inside Self and never move either,
        // so the 'static lifetime cast is sound for the lifetime of Self.
        let skel =
            unsafe { Box::from_raw(Box::into_raw(Box::new(skel)) as *mut ProctraceSkel<'static>) };

        let (tx, rx) = crossbeam_channel::unbounded();
        Ok(Self {
            _open_object: open_object,
            skel,
            _links: Vec::new(),
            tx,
            rx,
        })
    }

    /// Create a new ProcTrace without any target filter (traces all processes)
    pub fn new() -> Result<Self> {
        Self::new_with_target(&[], None)
    }

    /// Add a PID to the traced_processes map at runtime
    pub fn add_traced_pid(&mut self, pid: u32) -> Result<()> {
        let key = pid.to_ne_bytes();
        let val = 1u32.to_ne_bytes();
        self.skel
            .maps_mut()
            .traced_processes()
            .update(&key, &val, libbpf_rs::MapFlags::ANY)
            .with_context(|| format!("failed to add pid {} to traced_processes", pid))
    }

    /// Remove a PID from the traced_processes map at runtime
    pub fn remove_traced_pid(&mut self, pid: u32) -> Result<()> {
        let key = pid.to_ne_bytes();
        self.skel
            .maps_mut()
            .traced_processes()
            .delete(&key)
            .with_context(|| format!("failed to remove pid {} from traced_processes", pid))
    }

    /// Create a MapHandle from the traced_processes map for external reuse
    ///
    /// Returns a MapHandle that can be passed to `new_with_target_and_map` in another instance.
    /// Note: The MapHandle remains valid as long as this ProcTrace instance is alive.
    pub fn traced_processes_handle(&self) -> Result<MapHandle> {
        // Get the map and create a MapHandle from its fd
        let binding = self.skel.maps();
        let map = binding.traced_processes();
        MapHandle::try_clone(map).context("failed to create MapHandle from traced_processes")
    }

    /// Create a MapHandle from the shared ring buffer map for external reuse
    ///
    /// Returns a MapHandle that can be passed to sslsniff for sharing the same ring buffer.
    pub fn rb_handle(&self) -> Result<MapHandle> {
        let binding = self.skel.maps();
        let map = binding.rb();
        MapHandle::try_clone(map).context("failed to create MapHandle from rb")
    }

    /// Attach tracepoints for process tracking
    pub fn attach(&mut self) -> Result<()> {
        let mut links = Vec::new();

        // Attach execve enter tracepoint
        let link = self
            .skel
            .progs_mut()
            .trace_execve_enter()
            .attach()
            .context("failed to attach execve enter tracepoint")?;
        links.push(link);

        // Attach execve exit tracepoint (for filtering failed execs)
        let link = self
            .skel
            .progs_mut()
            .trace_execve_exit()
            .attach()
            .context("failed to attach execve exit tracepoint")?;
        links.push(link);

        // Attach write tracepoint (for stdout capture)
        let link = self
            .skel
            .progs_mut()
            .trace_write_enter()
            .attach()
            .context("failed to attach write tracepoint")?;
        links.push(link);

        // Attach process exit tracepoint
        let link = self
            .skel
            .progs_mut()
            .trace_process_exit()
            .attach()
            .context("failed to attach process exit tracepoint")?;
        links.push(link);

        self._links = links;
        Ok(())
    }

    /// Spawn a background thread that polls the BPF ring buffer
    /// Uses variable-length event parsing for efficiency
    pub fn run(&self) -> Result<ProcPoller> {
        let min_sz = std::mem::size_of::<ProcEventHeader>();
        let tx = self.tx.clone();
        let stop_flag = Arc::new(AtomicBool::new(false));
        let stop_flag_inner = Arc::clone(&stop_flag);

        let mut rb_builder = RingBufferBuilder::new();
        let binding = self.skel.maps();
        rb_builder
            .add(&binding.rb(), move |data: &[u8]| {
                if data.len() < min_sz {
                    return 0;
                }
                // Parse variable-length event
                if let Some(event) = VariableEvent::from_bytes(data) {
                    let _ = tx.send(event);
                }
                0
            })
            .context("failed to add ring buffer")?;
        let rb = rb_builder.build().context("failed to build ring buffer")?;

        let handle = thread::Builder::new()
            .name("proctrace-poll".into())
            .spawn(move || {
                let timeout = Duration::from_millis(POLL_TIMEOUT_MS);
                loop {
                    if stop_flag_inner.load(Ordering::Relaxed) {
                        break;
                    }
                    match rb.poll(timeout) {
                        Ok(_) => {}
                        Err(e) if e.kind() == libbpf_rs::ErrorKind::Interrupted => break,
                        Err(e) => {
                            eprintln!("proctrace poll error: {e:#}");
                            break;
                        }
                    }
                }
            })
            .context("failed to spawn poll thread")?;

        Ok(ProcPoller {
            handle: Some(handle),
            stop_flag,
        })
    }

    /// Receive the next event from the background poll thread (blocking)
    pub fn recv(&self) -> Option<VariableEvent> {
        self.rx.recv().ok()
    }

    /// Non-blocking receive
    pub fn try_recv(&self) -> Option<VariableEvent> {
        self.rx.try_recv().ok()
    }
}

// ─── Poll thread handle ─────────────────────────────────────────────────────

pub struct ProcPoller {
    handle: Option<thread::JoinHandle<()>>,
    stop_flag: Arc<AtomicBool>,
}

impl ProcPoller {
    /// Signal the poll thread to stop and wait for it to finish
    pub fn stop(mut self) {
        self.stop_flag.store(true, Ordering::Relaxed);
        if let Some(h) = self.handle.take() {
            let _ = h.join();
        }
    }
}

impl Drop for ProcPoller {
    fn drop(&mut self) {
        self.stop_flag.store(true, Ordering::Relaxed);
        if let Some(h) = self.handle.take() {
            let _ = h.join();
        }
    }
}
