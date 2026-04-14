// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Unified probes manager - manages sslsniff and proctrace probes
// with shared traced_processes map and shared ring buffer for coordinated process tracing

use anyhow::{Context, Result};
use libbpf_rs::{MapHandle, RingBufferBuilder};
use std::{
    mem,
    sync::{Arc, atomic::{AtomicBool, Ordering}},
    thread,
    time::Duration,
};

use crate::event::Event;

use super::proctrace::{ProcTrace, VariableEvent, ProcEventHeader};
use super::sslsniff::SslSniff;
use super::sslsniff::bpf::probe_SSL_data_t as RawSslEvent;
use super::procmon::{ProcMon, ProcMonEvent};

const POLL_TIMEOUT_MS: u64 = 100;

// Event source constants matching common.h event_source_t
const EVENT_SOURCE_PROC: u32 = 1;
const EVENT_SOURCE_SSL: u32 = 2;
const EVENT_SOURCE_PROCMON: u32 = 3;

/// Unified probe manager that coordinates sslsniff and proctrace
/// 
/// This manager ensures both probes share the same traced_processes map
/// and the same ring buffer, allowing coordinated process tracing where:
/// - proctrace captures process creation events
/// - sslsniff captures SSL traffic from those processes
/// Both write to a single shared ring buffer to save memory.
pub struct Probes {
    /// Process trace probe (owns the traced_processes map and ring buffer)
    proctrace: ProcTrace,
    /// SSL sniff probe (reuses proctrace's traced_processes map and ring buffer)
    sslsniff: SslSniff,
    /// Process monitor probe (reuses ring buffer)
    procmon: ProcMon,
    /// Shared ring buffer handle (cloned from proctrace) for polling
    rb_handle: MapHandle,
    /// Unified event channel - events are converted to Event type inside the poller
    event_tx: crossbeam_channel::Sender<Event>,
    event_rx: crossbeam_channel::Receiver<Event>,
}

impl Probes {
    /// Create a new unified probe manager
    /// 
    /// # Arguments
    /// * `target_pids` - Initial PIDs to trace (empty means trace all matching UID)
    /// * `target_uid` - Optional UID filter
    pub fn new(target_pids: &[u32], target_uid: Option<u32>) -> Result<Self> {
        // Create proctrace first - it will own the traced_processes map and ring buffer
        let proctrace = ProcTrace::new_with_target(target_pids, target_uid)
            .context("failed to create proctrace")?;
        
        // Get handles to the shared maps for reuse
        let map_handle = proctrace.traced_processes_handle()
            .context("failed to get traced_processes handle")?;
        let rb_handle = proctrace.rb_handle()
            .context("failed to get rb handle")?;
        
        // Create sslsniff - it will reuse both the traced_processes map and ring buffer
        let sslsniff = SslSniff::new_with_traced_processes(Some(&map_handle), Some(&rb_handle))
            .context("failed to create sslsniff")?;

        // Create procmon - it reuses the ring buffer
        let procmon = ProcMon::new_with_rb(&rb_handle)
            .context("failed to create procmon")?;

        let (event_tx, event_rx) = crossbeam_channel::unbounded();
        
        Ok(Self {
            proctrace,
            sslsniff,
            procmon,
            rb_handle,
            event_tx,
            event_rx,
        })
    }

    /// Attach all probes
    pub fn attach(&mut self) -> Result<()> {
        // Attach procmon for process monitoring
        self.procmon.attach()
            .context("failed to attach procmon")?;
        self.proctrace.attach().context("failed to attach proctrace")?;
        // sslsniff uses uprobes attached per-process via attach_process()
        Ok(())
    }

    pub fn attach_process(&mut self, pid: i32) -> Result<()> {
        self.attach_ssl_to_process(pid)?;
        self.add_traced_pid(pid as u32)
    }

    /// Attach SSL probes to a specific process
    pub fn attach_ssl_to_process(&mut self, pid: i32) -> Result<()> {
        self.sslsniff.attach_process(pid)
            .context("failed to attach sslsniff to process")?;
        Ok(())
    }

    /// Start polling for events from the shared ring buffer
    ///
    /// A single background thread polls the shared ring buffer and dispatches
    /// events as unified Event type to the channel.
    pub fn run(&self) -> Result<ProbesPoller> {
        let proc_min_sz = mem::size_of::<ProcEventHeader>();
        let ssl_event_size = mem::size_of::<RawSslEvent>();
        let procmon_event_size = mem::size_of::<ProcMonEvent>();

        let event_tx = self.event_tx.clone();
        let stop_flag = Arc::new(AtomicBool::new(false));
        let stop_flag_inner = Arc::clone(&stop_flag);

        // Build ring buffer from the shared rb handle
        let mut rb_builder = RingBufferBuilder::new();
        rb_builder
            .add(&self.rb_handle, move |data: &[u8]| {
                // Read the first u32 to determine event source (common_event_hdr.source)
                if data.len() < 4 {
                    return 0;
                }
                let source = u32::from_ne_bytes([data[0], data[1], data[2], data[3]]);
                let event = match source {
                    EVENT_SOURCE_PROC => {
                        // Process event - variable size, starts with proc_event_header
                        if data.len() >= proc_min_sz {
                            VariableEvent::from_bytes(data).map(Event::Proc)
                        } else {
                            None
                        }
                    }
                    EVENT_SOURCE_SSL => {
                        // SSL event - convert raw BPF data to user-space SslEvent
                        if data.len() >= ssl_event_size {
                            // SAFETY: BPF guarantees layout and alignment
                            let raw = unsafe { &*(data.as_ptr() as *const RawSslEvent) };
                            let ssl_event = crate::probes::sslsniff::SslEvent::from_bpf(raw);
                            Some(Event::Ssl(ssl_event))
                        } else {
                            None
                        }
                    }
                    EVENT_SOURCE_PROCMON => {
                        // Process monitor event
                        if data.len() >= procmon_event_size {
                            super::procmon::Event::from_bytes(data).map(Event::ProcMon)
                        } else {
                            None
                        }
                    }
                    _ => {
                        // Unknown source - ignore
                        log::warn!("probes: unknown event source {source}");
                        None
                    }
                };
                
                if let Some(e) = event {
                    let _ = event_tx.send(e);
                }
                0
            })
            .context("failed to add shared ring buffer")?;
        let rb = rb_builder.build().context("failed to build ring buffer")?;

        let handle = thread::Builder::new()
            .name("probes-poll".into())
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
                            eprintln!("probes poll error: {e:#}");
                            break;
                        }
                    }
                }
            })
            .context("failed to spawn poll thread")?;

        Ok(ProbesPoller {
            handle: Some(handle),
            stop_flag,
        })
    }

    /// Receive the next event from any probe (blocking)
    pub fn recv(&self) -> Option<Event> {
        self.event_rx.recv().ok()
    }

    /// Try to receive an event from any probe (non-blocking)
    pub fn try_recv(&self) -> Option<Event> {
        self.event_rx.try_recv().ok()
    }

    /// Add a PID to the traced_processes map at runtime
    pub fn add_traced_pid(&mut self, pid: u32) -> Result<()> {
        self.proctrace.add_traced_pid(pid)
            .context("failed to add traced pid")
    }

    /// Remove a PID from the traced_processes map at runtime
    pub fn remove_traced_pid(&mut self, pid: u32) -> Result<()> {
        self.proctrace.remove_traced_pid(pid)
            .context("failed to remove traced pid")
    }

    /// Get a handle to the traced_processes map
    pub fn traced_processes_handle(&self) -> Result<MapHandle> {
        self.proctrace.traced_processes_handle()
    }
}

/// Poller handle for the unified ring buffer thread
pub struct ProbesPoller {
    handle: Option<thread::JoinHandle<()>>,
    stop_flag: Arc<AtomicBool>,
}

impl ProbesPoller {
    /// Stop the poller thread
    pub fn stop(&mut self) {
        self.stop_flag.store(true, Ordering::Relaxed);
        if let Some(h) = self.handle.take() {
            let _ = h.join();
        }
    }
}

impl Drop for ProbesPoller {
    fn drop(&mut self) {
        self.stop();
    }
}
