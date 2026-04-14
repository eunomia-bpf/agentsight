// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
// Copyright (c) 2025 AgentSight Project
//
// Process monitor probe - lightweight process creation and exit monitoring

use crate::config;
use anyhow::{Context, Result};
use libbpf_rs::{
    Link, MapHandle,
    skel::{OpenSkel, SkelBuilder},
};
use std::{
    mem::MaybeUninit,
    os::fd::AsFd,
};

// ─── Generated skeleton ───────────────────────────────────────────────────────
mod bpf {
    include!(concat!(env!("OUT_DIR"), "/procmon.skel.rs"));
    include!(concat!(env!("OUT_DIR"), "/procmon.rs"));
}
use bpf::*;

// Re-export type from generated bindings
pub type ProcMonEvent = bpf::procmon_event;

// Event type constants
pub const PROCMON_EVENT_EXEC: u32 = 1;
pub const PROCMON_EVENT_EXIT: u32 = 2;

/// Parsed event from ring buffer
#[derive(Debug)]
pub enum Event {
    Exec {
        pid: u32,
        tid: u32,
        ppid: u32,
        uid: u32,
        timestamp_ns: u64,
        comm: String,
    },
    Exit {
        pid: u32,
        tid: u32,
        uid: u32,
        timestamp_ns: u64,
        comm: String,
    },
}

impl Event {
    /// Parse event from raw ring buffer data
    pub fn from_bytes(data: &[u8]) -> Option<Self> {
        let event_size = std::mem::size_of::<ProcMonEvent>();
        if data.len() < event_size {
            return None;
        }

        // SAFETY: BPF guarantees proper alignment and layout
        let raw = unsafe { &*(data.as_ptr() as *const ProcMonEvent) };

        // Parse comm (null-terminated)
        let comm = raw.comm
            .iter()
            .take_while(|&&c| c != 0)
            .map(|&c| c as u8)
            .collect::<Vec<u8>>();
        let comm = String::from_utf8_lossy(&comm).into_owned();

        match raw.event_type {
            PROCMON_EVENT_EXEC => Some(Event::Exec {
                pid: raw.pid,
                tid: raw.tid,
                ppid: raw.ppid,
                uid: raw.uid,
                timestamp_ns: config::ktime_to_unix_ns(raw.timestamp_ns),
                comm,
            }),
            PROCMON_EVENT_EXIT => Some(Event::Exit {
                pid: raw.pid,
                tid: raw.tid,
                uid: raw.uid,
                timestamp_ns: config::ktime_to_unix_ns(raw.timestamp_ns),
                comm,
            }),
            _ => None,
        }
    }

    /// Get event type as string
    pub fn event_type_str(&self) -> &'static str {
        match self {
            Event::Exec { .. } => "exec",
            Event::Exit { .. } => "exit",
        }
    }

    /// Get process ID
    pub fn pid(&self) -> u32 {
        match self {
            Event::Exec { pid, .. } => *pid,
            Event::Exit { pid, .. } => *pid,
        }
    }

    /// Get process name
    pub fn comm(&self) -> &str {
        match self {
            Event::Exec { comm, .. } => comm,
            Event::Exit { comm, .. } => comm,
        }
    }
}

// ─── Main struct ──────────────────────────────────────────────────────────────
pub struct ProcMon {
    _open_object: Box<MaybeUninit<libbpf_rs::OpenObject>>,
    skel: Box<ProcmonSkel<'static>>,
    _links: Vec<Link>,
}

impl ProcMon {
    /// Create a new ProcMon that reuses an existing ring buffer
    ///
    /// # Arguments
    /// * `rb` - External ring buffer map handle to reuse
    pub fn new_with_rb(rb: &MapHandle) -> Result<Self> {
        // Open + load skeleton
        let mut builder = ProcmonSkelBuilder::default();
        builder.obj_builder.debug(config::verbose());

        let open_object = Box::new(MaybeUninit::<libbpf_rs::OpenObject>::uninit());
        let mut open_skel = builder.open().context("failed to open BPF object")?;

        // Reuse external rb map
        open_skel
            .maps_mut()
            .rb()
            .reuse_fd(rb.as_fd())
            .context("failed to reuse external rb map")?;

        let skel = open_skel.load().context("failed to load BPF object")?;

        // SAFETY: skel borrows open_object which lives in a Box<MaybeUninit>
        let skel =
            unsafe { Box::from_raw(Box::into_raw(Box::new(skel)) as *mut ProcmonSkel<'static>) };

        Ok(Self {
            _open_object: open_object,
            skel,
            _links: Vec::new(),
        })
    }

    /// Attach tracepoints for process monitoring
    pub fn attach(&mut self) -> Result<()> {
        let mut links = Vec::new();

        // Attach execve exit tracepoint (after execve completes)
        let link = self
            .skel
            .progs_mut()
            .trace_execve_exit()
            .attach()
            .context("failed to attach execve exit tracepoint")?;
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
}
