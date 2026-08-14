// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Unix-socket server for bridge protocol v1.
//!
//! AgentSight listens; an external evidence consumer connects, negotiates a
//! protocol version and disclosure mode, registers scopes, and receives
//! materialized-view mutations. The server owns sequencing, the bounded replay
//! buffer, scope bookkeeping, and per-connection back-pressure; it never
//! interprets the consumer's identifiers.

use crate::view::SharedMaterializedView;
use agentsight_capture::bridge::{
    MutationEmitterConfig, MutationResult, MutationSink, SequenceAllocator,
};
use agentsight_protocol::bridge::{
    BRIDGE_PROTOCOL_VERSION, BridgeAgreement, BridgeCapability, BridgeHealth, BridgeMessage,
    DisclosureMode, MAX_FRAME_BYTES, MutationOperation, ScopeRegistration, TimestampBasis,
    ToolScopeRegistration, ViewMutation, ViewMutationEnvelope, capability_names, encode_frame,
    read_frame,
};
use std::collections::{HashMap, VecDeque};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{UnixListener, UnixStream};
use tokio::sync::Notify;

pub(crate) const DEFAULT_MAX_CONNECTIONS: usize = 4;
pub(crate) const DEFAULT_OUTBOUND_CAPACITY: usize = 4_096;
pub(crate) const DEFAULT_REPLAY_CAPACITY: usize = 8_192;
pub(crate) const DEFAULT_HEARTBEAT: Duration = Duration::from_secs(15);
pub(crate) const DEFAULT_IDLE_TIMEOUT: Duration = Duration::from_secs(90);
pub(crate) const DEFAULT_WRITE_TIMEOUT: Duration = Duration::from_secs(10);

pub(crate) type BridgeResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Everything the bridge server needs that is not derived from the view.
#[derive(Clone, Debug)]
pub(crate) struct BridgeServerConfig {
    pub(crate) socket_path: PathBuf,
    pub(crate) node_id: String,
    pub(crate) boot_id: Option<String>,
    pub(crate) product_version: String,
    pub(crate) build_commit: Option<String>,
    pub(crate) capabilities: Vec<BridgeCapability>,
    pub(crate) max_connections: usize,
    pub(crate) max_frame_bytes: u32,
    pub(crate) outbound_capacity: usize,
    pub(crate) replay_capacity: usize,
    pub(crate) heartbeat_interval: Duration,
    pub(crate) idle_timeout: Duration,
    pub(crate) write_timeout: Duration,
}

impl BridgeServerConfig {
    pub(crate) fn new(socket_path: PathBuf) -> Self {
        Self {
            socket_path,
            node_id: default_node_id(),
            boot_id: read_boot_id(),
            product_version: env!("CARGO_PKG_VERSION").to_string(),
            build_commit: option_env!("AGENTSIGHT_BUILD_COMMIT").map(str::to_string),
            capabilities: default_capabilities(),
            max_connections: DEFAULT_MAX_CONNECTIONS,
            max_frame_bytes: MAX_FRAME_BYTES,
            outbound_capacity: DEFAULT_OUTBOUND_CAPACITY,
            replay_capacity: DEFAULT_REPLAY_CAPACITY,
            heartbeat_interval: DEFAULT_HEARTBEAT,
            idle_timeout: DEFAULT_IDLE_TIMEOUT,
            write_timeout: DEFAULT_WRITE_TIMEOUT,
        }
    }
}

/// Capabilities this build can offer. eBPF-backed capture is Linux-only, so the
/// answer is honest per target rather than aspirational.
fn default_capabilities() -> Vec<BridgeCapability> {
    let ebpf = cfg!(target_os = "linux");
    let ebpf_detail = (!ebpf).then(|| "eBPF capture requires Linux".to_string());
    vec![
        BridgeCapability::new(capability_names::PROCESS_CAPTURE, ebpf, ebpf_detail.clone()),
        BridgeCapability::new(capability_names::FILE_CAPTURE, ebpf, ebpf_detail.clone()),
        BridgeCapability::new(capability_names::NETWORK_CAPTURE, ebpf, ebpf_detail.clone()),
        BridgeCapability::new(capability_names::TLS_CAPTURE, ebpf, ebpf_detail.clone()),
        BridgeCapability::new(capability_names::AGENT_NATIVE_SESSIONS, true, None),
        BridgeCapability::new(capability_names::RESOURCE_SAMPLES, true, None),
        BridgeCapability::new(capability_names::CGROUP_FILTER, ebpf, ebpf_detail),
        BridgeCapability::new(capability_names::SESSION_MUTATIONS, true, None),
    ]
}

/// Reuse the collector's persisted node identity when one exists.
fn default_node_id() -> String {
    crate::cmd_bind::persisted_node_id()
        .unwrap_or_else(|| format!("node_{}", uuid::Uuid::new_v4().simple()))
}

fn read_boot_id() -> Option<String> {
    #[cfg(target_os = "linux")]
    {
        std::fs::read_to_string("/proc/sys/kernel/random/boot_id")
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    }
    // No stable boot identifier is exposed off Linux; the field stays absent
    // rather than being filled with a per-process value that would look like
    // a reboot on every restart.
    #[cfg(not(target_os = "linux"))]
    None
}

/// Host monotonic clock in nanoseconds. Scope expiry is expressed in the same
/// clock on both sides because the bridge is same-host by construction.
pub(crate) fn monotonic_ns() -> u64 {
    let mut timespec = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    // SAFETY: clock_gettime writes only into the timespec we own.
    if unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut timespec) } != 0 {
        return 0;
    }
    (timespec.tv_sec as u64)
        .saturating_mul(1_000_000_000)
        .saturating_add(timespec.tv_nsec as u64)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ScopeKind {
    Sandbox,
    Tool,
}

#[derive(Debug, Clone)]
struct ScopeEntry {
    /// Recorded for diagnostics; auto-tagging counts every active scope.
    #[allow(dead_code)]
    kind: ScopeKind,
    expires_monotonic_ns: Option<u64>,
    last_sequence: u64,
}

impl ScopeEntry {
    fn is_active(&self, now_ns: u64) -> bool {
        self.expires_monotonic_ns
            .is_none_or(|expires| expires > now_ns)
    }
}

/// One message queued for a connection, plus the gap bookkeeping that overflow
/// creates.
#[derive(Default)]
struct QueueState {
    items: VecDeque<BridgeMessage>,
    closed: bool,
    /// Sequence range dropped since the client last heard about it.
    pending_gap: Option<(u64, u64)>,
    dropped: u64,
}

/// Bounded outbound queue: overflow drops the oldest message and remembers the
/// gap so the client is told rather than silently short-changed.
struct OutboundQueue {
    capacity: usize,
    state: Mutex<QueueState>,
    notify: Notify,
}

impl OutboundQueue {
    fn new(capacity: usize) -> Self {
        Self {
            capacity: capacity.max(1),
            state: Mutex::new(QueueState::default()),
            notify: Notify::new(),
        }
    }

    /// Returns the number of mutations dropped to make room.
    fn push(&self, message: BridgeMessage) -> u64 {
        let mut dropped = 0;
        {
            let Ok(mut state) = self.state.lock() else {
                return 0;
            };
            if state.closed {
                return 0;
            }
            while state.items.len() >= self.capacity {
                let Some(evicted) = state.items.pop_front() else {
                    break;
                };
                dropped += 1;
                state.dropped += 1;
                if let BridgeMessage::Mutation(envelope) = evicted {
                    let range = state
                        .pending_gap
                        .map(|(from, to)| (from.min(envelope.sequence), to.max(envelope.sequence)))
                        .unwrap_or((envelope.sequence, envelope.sequence));
                    state.pending_gap = Some(range);
                }
            }
            state.items.push_back(message);
        }
        self.notify.notify_one();
        dropped
    }

    /// Stop accepting new messages but keep whatever is already queued so the
    /// writer can flush a final shutdown notice.
    fn close(&self) {
        if let Ok(mut state) = self.state.lock() {
            state.closed = true;
        }
        self.notify.notify_waiters();
        self.notify.notify_one();
    }

    fn is_closed(&self) -> bool {
        self.state.lock().map(|state| state.closed).unwrap_or(true)
    }

    fn take(&self) -> (Vec<BridgeMessage>, Option<(u64, u64)>) {
        let Ok(mut state) = self.state.lock() else {
            return (Vec::new(), None);
        };
        (state.items.drain(..).collect(), state.pending_gap.take())
    }

    #[cfg(test)]
    fn dropped(&self) -> u64 {
        self.state.lock().map(|state| state.dropped).unwrap_or(0)
    }
}

struct ConnectionEntry {
    id: u64,
    queue: Arc<OutboundQueue>,
    acked_through: Arc<AtomicU64>,
}

#[derive(Default)]
struct HubState {
    connections: Vec<ConnectionEntry>,
    scopes: HashMap<String, ScopeEntry>,
    replay: VecDeque<ViewMutationEnvelope>,
    capture_gaps: u64,
    dropped_mutations: u64,
    next_connection_id: u64,
}

/// Shared server state. Every method takes the lock briefly and never awaits
/// while holding it, because the capture pipeline calls in synchronously.
pub(crate) struct BridgeHub {
    config: BridgeServerConfig,
    sequence: SequenceAllocator,
    state: Mutex<HubState>,
}

impl BridgeHub {
    fn new(config: BridgeServerConfig, sequence: SequenceAllocator) -> Self {
        Self {
            config,
            sequence,
            state: Mutex::new(HubState::default()),
        }
    }

    fn register_connection(&self) -> Option<ConnectionEntry> {
        let mut state = self.state.lock().ok()?;
        if state.connections.len() >= self.config.max_connections {
            return None;
        }
        state.next_connection_id += 1;
        let entry = ConnectionEntry {
            id: state.next_connection_id,
            queue: Arc::new(OutboundQueue::new(self.config.outbound_capacity)),
            acked_through: Arc::new(AtomicU64::new(0)),
        };
        let handle = ConnectionEntry {
            id: entry.id,
            queue: entry.queue.clone(),
            acked_through: entry.acked_through.clone(),
        };
        state.connections.push(entry);
        Some(handle)
    }

    fn unregister_connection(&self, id: u64) {
        if let Ok(mut state) = self.state.lock() {
            state.connections.retain(|entry| entry.id != id);
        }
    }

    /// Attribute a mutation to the single active scope, when there is exactly
    /// one. With zero or several, the receiver correlates for itself.
    fn active_scope_handle(state: &HubState, now_ns: u64) -> Option<String> {
        let mut active = state
            .scopes
            .iter()
            .filter(|(_, entry)| entry.is_active(now_ns))
            .map(|(handle, _)| handle.clone());
        let first = active.next()?;
        active.next().is_none().then_some(first)
    }

    /// Stamp, buffer, and fan out one mutation envelope.
    fn broadcast(&self, mut envelope: ViewMutationEnvelope) {
        let Ok(mut state) = self.state.lock() else {
            return;
        };
        let now_ns = monotonic_ns();
        if envelope.scope_handle.is_none() && envelope.mutation.is_scope_taggable() {
            envelope.scope_handle = Self::active_scope_handle(&state, now_ns);
        }
        if let Some(handle) = envelope.scope_handle.as_ref() {
            if let Some(scope) = state.scopes.get_mut(handle) {
                scope.last_sequence = scope.last_sequence.max(envelope.sequence);
            }
        }

        let replay_capacity = self.config.replay_capacity;
        state.replay.push_back(envelope.clone());
        while state.replay.len() > replay_capacity {
            state.replay.pop_front();
        }

        let message = BridgeMessage::Mutation(envelope);
        let mut dropped = 0;
        for connection in &state.connections {
            dropped += connection.queue.push(message.clone());
        }
        if dropped > 0 {
            state.dropped_mutations += dropped;
            state.capture_gaps += 1;
        }
    }

    fn send_to(&self, id: u64, message: BridgeMessage) {
        let Ok(state) = self.state.lock() else {
            return;
        };
        if let Some(connection) = state.connections.iter().find(|entry| entry.id == id) {
            connection.queue.push(message);
        }
    }

    fn health(&self) -> BridgeHealth {
        let Ok(state) = self.state.lock() else {
            return BridgeHealth {
                state: BridgeHealth::FAILING.to_string(),
                detail: Some("bridge state poisoned".to_string()),
                capture_gaps: 0,
                dropped_mutations: 0,
                active_scopes: 0,
            };
        };
        let now_ns = monotonic_ns();
        let active_scopes = state
            .scopes
            .values()
            .filter(|entry| entry.is_active(now_ns))
            .count() as u32;
        let degraded = state.dropped_mutations > 0 || state.capture_gaps > 0;
        BridgeHealth {
            state: if degraded {
                BridgeHealth::DEGRADED.to_string()
            } else {
                BridgeHealth::OK.to_string()
            },
            detail: degraded.then(|| "outbound queue dropped mutations".to_string()),
            capture_gaps: state.capture_gaps,
            dropped_mutations: state.dropped_mutations,
            active_scopes,
        }
    }

    fn register_scope(&self, registration: &ScopeRegistration) -> Result<(), String> {
        if registration.scope_handle.trim().is_empty() {
            return Err("scope_handle must not be empty".to_string());
        }
        let mut state = self
            .state
            .lock()
            .map_err(|_| "bridge state poisoned".to_string())?;
        state.scopes.insert(
            registration.scope_handle.clone(),
            ScopeEntry {
                kind: ScopeKind::Sandbox,
                expires_monotonic_ns: registration.expires_monotonic_ns,
                last_sequence: 0,
            },
        );
        Ok(())
    }

    fn register_tool_scope(&self, registration: &ToolScopeRegistration) -> Result<(), String> {
        if registration.tool_scope_handle.trim().is_empty() {
            return Err("tool_scope_handle must not be empty".to_string());
        }
        let mut state = self
            .state
            .lock()
            .map_err(|_| "bridge state poisoned".to_string())?;
        if !state.scopes.contains_key(&registration.parent_scope_handle) {
            return Err("unknown parent scope".to_string());
        }
        state.scopes.insert(
            registration.tool_scope_handle.clone(),
            ScopeEntry {
                kind: ScopeKind::Tool,
                expires_monotonic_ns: registration.expires_monotonic_ns,
                last_sequence: 0,
            },
        );
        Ok(())
    }

    fn unregister_scope(&self, handle: &str) -> Option<u64> {
        let mut state = self.state.lock().ok()?;
        let entry = state.scopes.remove(handle)?;
        (entry.last_sequence > 0).then_some(entry.last_sequence)
    }

    fn effective_capabilities(&self, required: &[String]) -> Vec<BridgeCapability> {
        if required.is_empty() {
            return self.config.capabilities.clone();
        }
        required
            .iter()
            .map(|name| {
                self.config
                    .capabilities
                    .iter()
                    .find(|capability| &capability.name == name)
                    .cloned()
                    .unwrap_or_else(|| {
                        BridgeCapability::new(
                            name.clone(),
                            false,
                            Some("unknown capability".to_string()),
                        )
                    })
            })
            .collect()
    }

    /// Replay everything after `after_sequence`, or report the earliest the
    /// buffer still holds when the request fell out of it.
    fn resume(&self, after_sequence: u64) -> Result<Vec<ViewMutationEnvelope>, Option<u64>> {
        let Ok(state) = self.state.lock() else {
            return Err(None);
        };
        let earliest = state.replay.front().map(|envelope| envelope.sequence);
        match earliest {
            // Nothing buffered: only a request for "everything since now" can
            // be honored.
            None if after_sequence <= self.sequence.current() => Ok(Vec::new()),
            None => Err(None),
            Some(earliest) if earliest > after_sequence + 1 => Err(Some(earliest)),
            Some(_) => Ok(state
                .replay
                .iter()
                .filter(|envelope| envelope.sequence > after_sequence)
                .cloned()
                .collect()),
        }
    }

    fn note_ack(&self, id: u64, through_sequence: u64) {
        let Ok(state) = self.state.lock() else {
            return;
        };
        if let Some(connection) = state.connections.iter().find(|entry| entry.id == id) {
            connection
                .acked_through
                .fetch_max(through_sequence, Ordering::SeqCst);
        }
    }

    fn envelope(
        &self,
        operation: MutationOperation,
        mutation: ViewMutation,
        scope_handle: Option<String>,
    ) -> ViewMutationEnvelope {
        ViewMutationEnvelope {
            protocol_version: BRIDGE_PROTOCOL_VERSION,
            node_id: self.config.node_id.clone(),
            boot_id: self.config.boot_id.clone(),
            sequence: self.sequence.next_sequence(),
            observed_wall_ms: None,
            observed_monotonic_ns: Some(monotonic_ns()),
            basis: TimestampBasis::BootMonotonic,
            source_component: "agentsight-collector".to_string(),
            source_version: self.config.product_version.clone(),
            scope_handle,
            operation,
            mutation,
        }
    }
}

/// The view-side handle: turns emitter output into bridge broadcasts.
struct HubSink {
    hub: Arc<BridgeHub>,
}

impl MutationSink for HubSink {
    fn mutation(&mut self, m: &ViewMutationEnvelope) -> MutationResult<()> {
        self.hub.broadcast(m.clone());
        Ok(())
    }
}

/// Running bridge server. Dropping the handle stops the listener and removes
/// the socket file.
pub(crate) struct BridgeServerHandle {
    socket_path: PathBuf,
    shutdown: Arc<Notify>,
    task: tokio::task::JoinHandle<()>,
    hub: Arc<BridgeHub>,
}

impl BridgeServerHandle {
    /// Tell connected clients the collector is stopping, then close.
    pub(crate) fn shutdown(&self, reason: &str) {
        if let Ok(state) = self.hub.state.lock() {
            for connection in &state.connections {
                connection.queue.push(BridgeMessage::Shutdown {
                    reason: reason.to_string(),
                });
            }
        }
        self.shutdown.notify_waiters();
    }
}

impl Drop for BridgeServerHandle {
    fn drop(&mut self) {
        self.shutdown.notify_waiters();
        self.task.abort();
        let _ = std::fs::remove_file(&self.socket_path);
    }
}

/// Validate the socket's parent directory and clear a stale socket file.
///
/// The parent must be a real directory (not a symlink) with owner-only
/// permissions, because the socket itself is the only authentication boundary
/// on platforms without `SO_PEERCRED`.
pub(crate) fn prepare_socket_path(path: &Path) -> BridgeResult<()> {
    use std::os::unix::fs::{FileTypeExt, PermissionsExt};

    let parent = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .ok_or("--bridge-socket must include a parent directory")?;
    let metadata = std::fs::symlink_metadata(parent)
        .map_err(|error| format!("bridge socket directory {}: {error}", parent.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(format!(
            "bridge socket directory {} must be a real directory",
            parent.display()
        )
        .into());
    }
    if metadata.permissions().mode() & 0o077 != 0 {
        return Err(format!(
            "bridge socket directory {} must not be group- or world-accessible",
            parent.display()
        )
        .into());
    }

    match std::fs::symlink_metadata(path) {
        Ok(existing) if existing.file_type().is_socket() => std::fs::remove_file(path)
            .map_err(|error| format!("failed to remove stale bridge socket: {error}"))?,
        Ok(_) => {
            return Err(format!(
                "bridge socket path {} already exists and is not a socket",
                path.display()
            )
            .into());
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(error) => return Err(format!("bridge socket path {}: {error}", path.display()).into()),
    }
    Ok(())
}

/// v1 peer policy: same uid only.
///
/// `SO_PEERCRED` is Linux-specific. On other platforms the trust boundary is
/// the filesystem: the socket is mode 0600 inside an owner-only directory, so
/// only the owning uid can connect at all.
fn peer_is_same_uid(stream: &UnixStream) -> Result<(), String> {
    #[cfg(target_os = "linux")]
    {
        use std::os::fd::AsRawFd;
        let mut credentials = libc::ucred {
            pid: 0,
            uid: 0,
            gid: 0,
        };
        let mut length = std::mem::size_of::<libc::ucred>() as libc::socklen_t;
        // SAFETY: the fd is owned by `stream` for the duration of the call and
        // the output buffer matches the documented size for SO_PEERCRED.
        let result = unsafe {
            libc::getsockopt(
                stream.as_raw_fd(),
                libc::SOL_SOCKET,
                libc::SO_PEERCRED,
                (&raw mut credentials) as *mut libc::c_void,
                &mut length,
            )
        };
        if result != 0 {
            return Err("failed to read peer credentials".to_string());
        }
        // SAFETY: getuid is always safe.
        let server_uid = unsafe { libc::getuid() };
        if credentials.uid != server_uid {
            return Err("peer uid does not match the collector uid".to_string());
        }
        Ok(())
    }
    #[cfg(not(target_os = "linux"))]
    {
        let _ = stream;
        Ok(())
    }
}

/// Bind the socket, attach the mutation sink to the view, and start accepting.
pub(crate) async fn start_bridge_server(
    config: BridgeServerConfig,
    view: SharedMaterializedView,
    disclosure: DisclosureMode,
) -> BridgeResult<BridgeServerHandle> {
    use std::os::unix::fs::PermissionsExt;

    prepare_socket_path(&config.socket_path)?;
    let listener = UnixListener::bind(&config.socket_path)
        .map_err(|error| format!("failed to bind bridge socket: {error}"))?;
    std::fs::set_permissions(&config.socket_path, std::fs::Permissions::from_mode(0o600))
        .map_err(|error| format!("failed to restrict bridge socket permissions: {error}"))?;

    let sequence = SequenceAllocator::new();
    let hub = Arc::new(BridgeHub::new(config.clone(), sequence.clone()));

    {
        let mut guard = view
            .lock()
            .map_err(|_| "materialized view lock poisoned".to_string())?;
        guard.configure_mutations(MutationEmitterConfig {
            node_id: config.node_id.clone(),
            boot_id: config.boot_id.clone(),
            source_component: "agentsight-capture".to_string(),
            source_version: config.product_version.clone(),
            disclosure,
            sequence,
        });
        guard.add_mutation_sink(Box::new(HubSink { hub: hub.clone() }));
    }

    let shutdown = Arc::new(Notify::new());
    let task = tokio::spawn(accept_loop(listener, hub.clone(), view, shutdown.clone()));

    Ok(BridgeServerHandle {
        socket_path: config.socket_path,
        shutdown,
        task,
        hub,
    })
}

async fn accept_loop(
    listener: UnixListener,
    hub: Arc<BridgeHub>,
    view: SharedMaterializedView,
    shutdown: Arc<Notify>,
) {
    loop {
        tokio::select! {
            accepted = listener.accept() => {
                let Ok((stream, _addr)) = accepted else { continue };
                let hub = hub.clone();
                let view = view.clone();
                let shutdown = shutdown.clone();
                tokio::spawn(async move {
                    if let Err(error) = serve_connection(stream, hub, view, shutdown).await {
                        log::debug!("bridge connection ended: {error}");
                    }
                });
            }
            _ = shutdown.notified() => break,
        }
    }
}

async fn serve_connection(
    stream: UnixStream,
    hub: Arc<BridgeHub>,
    view: SharedMaterializedView,
    shutdown: Arc<Notify>,
) -> BridgeResult<()> {
    if let Err(reason) = peer_is_same_uid(&stream) {
        let (_reader, mut writer) = stream.into_split();
        let frame = encode_frame(
            &BridgeMessage::HelloRejected {
                reason: reason.clone(),
            },
            hub.config.max_frame_bytes,
        )?;
        let _ = writer.write_all(&frame).await;
        let _ = writer.shutdown().await;
        return Err(reason.into());
    }

    let Some(connection) = hub.register_connection() else {
        let (_reader, mut writer) = stream.into_split();
        let frame = encode_frame(
            &BridgeMessage::HelloRejected {
                reason: "too many bridge connections".to_string(),
            },
            hub.config.max_frame_bytes,
        )?;
        let _ = writer.write_all(&frame).await;
        let _ = writer.shutdown().await;
        return Err("bridge connection limit reached".into());
    };

    let connection_id = connection.id;
    let queue = connection.queue.clone();
    let (mut reader, writer) = stream.into_split();

    let writer_task = tokio::spawn(writer_loop(
        writer,
        queue.clone(),
        hub.clone(),
        shutdown.clone(),
    ));

    let result = reader_loop(&mut reader, &hub, &view, connection_id, &queue).await;

    queue.close();
    hub.unregister_connection(connection_id);
    // Give the writer a bounded chance to flush queued notices before the
    // connection goes away.
    let _ = tokio::time::timeout(Duration::from_millis(500), writer_task).await;
    result
}

async fn writer_loop(
    mut writer: tokio::net::unix::OwnedWriteHalf,
    queue: Arc<OutboundQueue>,
    hub: Arc<BridgeHub>,
    shutdown: Arc<Notify>,
) {
    loop {
        let (messages, pending_gap) = queue.take();
        if messages.is_empty() && pending_gap.is_none() {
            if queue.is_closed() {
                break;
            }
            let heartbeat = tokio::time::timeout(hub.config.heartbeat_interval, async {
                tokio::select! {
                    _ = queue.notify.notified() => {}
                    _ = shutdown.notified() => {}
                }
            })
            .await;
            if heartbeat.is_err() {
                let beat = BridgeMessage::Heartbeat {
                    monotonic_ns: monotonic_ns(),
                };
                if write_message(&mut writer, &beat, &hub).await.is_err() {
                    break;
                }
                if write_message(&mut writer, &BridgeMessage::Health(hub.health()), &hub)
                    .await
                    .is_err()
                {
                    break;
                }
            }
            continue;
        }

        if let Some((from, to)) = pending_gap {
            let gap = hub.envelope(
                MutationOperation::Insert,
                ViewMutation::CaptureGapObserved {
                    from_sequence: from,
                    to_sequence: to,
                    reason: "bridge outbound queue overflow".to_string(),
                },
                None,
            );
            if write_message(&mut writer, &BridgeMessage::Mutation(gap), &hub)
                .await
                .is_err()
            {
                break;
            }
        }

        for message in messages {
            if write_message(&mut writer, &message, &hub).await.is_err() {
                return;
            }
        }
    }
    let _ = writer.shutdown().await;
}

async fn write_message(
    writer: &mut tokio::net::unix::OwnedWriteHalf,
    message: &BridgeMessage,
    hub: &BridgeHub,
) -> BridgeResult<()> {
    let frame = encode_frame(message, hub.config.max_frame_bytes)?;
    tokio::time::timeout(hub.config.write_timeout, writer.write_all(&frame))
        .await
        .map_err(|_| "bridge write timed out")??;
    Ok(())
}

async fn reader_loop(
    reader: &mut tokio::net::unix::OwnedReadHalf,
    hub: &Arc<BridgeHub>,
    view: &SharedMaterializedView,
    connection_id: u64,
    queue: &Arc<OutboundQueue>,
) -> BridgeResult<()> {
    let mut buffer = Vec::new();
    let mut chunk = vec![0u8; 16 * 1024];
    let mut negotiated = false;

    loop {
        while let Some((message, consumed)) = read_frame(&buffer, hub.config.max_frame_bytes)? {
            buffer.drain(..consumed);
            match handle_message(message, hub, view, connection_id, &mut negotiated) {
                Flow::Continue => {}
                Flow::Close => return Ok(()),
            }
        }

        let read = tokio::time::timeout(hub.config.idle_timeout, reader.read(&mut chunk)).await;
        let read = match read {
            Ok(read) => read?,
            Err(_) => {
                queue.push(BridgeMessage::Shutdown {
                    reason: "bridge idle timeout".to_string(),
                });
                // Give the writer a moment to flush the notice before the
                // connection is torn down.
                tokio::time::sleep(Duration::from_millis(50)).await;
                return Ok(());
            }
        };
        if read == 0 {
            return Ok(());
        }
        buffer.extend_from_slice(&chunk[..read]);
        if buffer.len() > hub.config.max_frame_bytes as usize * 2 {
            return Err("bridge peer exceeded the frame buffer limit".into());
        }
    }
}

enum Flow {
    Continue,
    Close,
}

fn handle_message(
    message: BridgeMessage,
    hub: &Arc<BridgeHub>,
    view: &SharedMaterializedView,
    connection_id: u64,
    negotiated: &mut bool,
) -> Flow {
    if !*negotiated {
        let BridgeMessage::Hello(hello) = message else {
            hub.send_to(
                connection_id,
                BridgeMessage::HelloRejected {
                    reason: "first bridge frame must be hello".to_string(),
                },
            );
            return Flow::Close;
        };
        if !hello.supported_versions.contains(&BRIDGE_PROTOCOL_VERSION) {
            hub.send_to(
                connection_id,
                BridgeMessage::HelloRejected {
                    reason: format!(
                        "no shared protocol version; server speaks v{BRIDGE_PROTOCOL_VERSION}"
                    ),
                },
            );
            return Flow::Close;
        }
        let max_frame_bytes = hello
            .max_frame_bytes
            .min(hub.config.max_frame_bytes)
            .max(1_024);
        hub.send_to(
            connection_id,
            BridgeMessage::Agreement(BridgeAgreement {
                protocol_version: BRIDGE_PROTOCOL_VERSION,
                product: agentsight_protocol::PRODUCT.to_string(),
                product_version: hub.config.product_version.clone(),
                build_commit: hub.config.build_commit.clone(),
                binary_digest: None,
                node_id: hub.config.node_id.clone(),
                boot_id: hub.config.boot_id.clone(),
                capabilities: hub.config.capabilities.clone(),
                max_frame_bytes,
            }),
        );
        hub.send_to(connection_id, BridgeMessage::Health(hub.health()));
        *negotiated = true;
        return Flow::Continue;
    }

    match message {
        BridgeMessage::Hello(_) => hub.send_to(
            connection_id,
            BridgeMessage::HelloRejected {
                reason: "hello already negotiated".to_string(),
            },
        ),
        BridgeMessage::RegisterScope(registration) => {
            let handle = registration.scope_handle.clone();
            match hub.register_scope(&registration) {
                Ok(()) => hub.send_to(
                    connection_id,
                    BridgeMessage::ScopeAccepted {
                        scope_handle: handle,
                        effective: hub.effective_capabilities(&registration.required_capabilities),
                    },
                ),
                Err(reason) => hub.send_to(
                    connection_id,
                    BridgeMessage::ScopeRejected {
                        scope_handle: handle,
                        reason,
                    },
                ),
            }
        }
        BridgeMessage::RegisterToolScope(registration) => {
            let handle = registration.tool_scope_handle.clone();
            match hub.register_tool_scope(&registration) {
                Ok(()) => hub.send_to(
                    connection_id,
                    BridgeMessage::ScopeAccepted {
                        scope_handle: handle,
                        effective: hub.effective_capabilities(&[]),
                    },
                ),
                Err(reason) => hub.send_to(
                    connection_id,
                    BridgeMessage::ScopeRejected {
                        scope_handle: handle,
                        reason,
                    },
                ),
            }
        }
        BridgeMessage::UnregisterScope { scope_handle } => {
            let flushed_through = hub.unregister_scope(&scope_handle);
            hub.send_to(
                connection_id,
                BridgeMessage::ScopeUnregistered {
                    scope_handle,
                    flushed_through,
                },
            );
        }
        BridgeMessage::Ack { through_sequence } => hub.note_ack(connection_id, through_sequence),
        BridgeMessage::Resume(request) => match hub.resume(request.after_sequence) {
            Ok(envelopes) => {
                for envelope in envelopes {
                    hub.send_to(connection_id, BridgeMessage::Mutation(envelope));
                }
            }
            Err(earliest_available) => hub.send_to(
                connection_id,
                BridgeMessage::ResumeUnavailable { earliest_available },
            ),
        },
        BridgeMessage::SnapshotRequest { scope_handle } => {
            serve_snapshot(hub, view, connection_id, scope_handle)
        }
        BridgeMessage::Heartbeat { .. } => {}
        BridgeMessage::Shutdown { .. } => return Flow::Close,
        // Server-originated messages are not valid inbound traffic.
        other => {
            log::debug!("bridge: ignoring client message {:?}", other);
        }
    }
    Flow::Continue
}

/// Answer a snapshot request from current view state. Snapshot mutations are
/// explicitly reconstructions: their sequence range is synthetic and must not
/// be read as original ordering.
fn serve_snapshot(
    hub: &Arc<BridgeHub>,
    view: &SharedMaterializedView,
    connection_id: u64,
    scope_handle: Option<String>,
) {
    let mutations = {
        let Ok(guard) = view.lock() else {
            return;
        };
        let disclosure = guard.mutation_disclosure();
        guard.bridge_snapshot_mutations(&disclosure)
    };

    hub.send_to(
        connection_id,
        BridgeMessage::SnapshotBegin {
            estimated: mutations.len() as u64,
            reconstructed: true,
        },
    );
    let mut through_sequence = hub.sequence.current();
    for mutation in mutations {
        let envelope = hub.envelope(
            MutationOperation::SnapshotReconstruction,
            mutation,
            scope_handle.clone(),
        );
        through_sequence = envelope.sequence;
        hub.send_to(connection_id, BridgeMessage::Mutation(envelope));
    }
    hub.send_to(
        connection_id,
        BridgeMessage::SnapshotEnd { through_sequence },
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::view::MaterializedView;
    use agentsight_capture::model::AuditEventRow;
    use agentsight_protocol::bridge::{BridgeHello, ResumeRequest};

    const RECV_TIMEOUT: Duration = Duration::from_secs(3);

    /// Minimal in-test bridge client. Deliberately independent of the server's
    /// own framing helpers only in structure, not in codec: byte compatibility
    /// is proven by the protocol crate's golden vectors.
    struct TestClient {
        stream: UnixStream,
        buffer: Vec<u8>,
    }

    impl TestClient {
        async fn connect(path: &Path) -> Self {
            Self {
                stream: UnixStream::connect(path).await.expect("connect"),
                buffer: Vec::new(),
            }
        }

        async fn send(&mut self, message: &BridgeMessage) {
            let frame = encode_frame(message, MAX_FRAME_BYTES).expect("encode");
            self.stream.write_all(&frame).await.expect("write");
        }

        async fn recv(&mut self) -> Option<BridgeMessage> {
            loop {
                if let Some((message, consumed)) =
                    read_frame(&self.buffer, MAX_FRAME_BYTES).expect("frame")
                {
                    self.buffer.drain(..consumed);
                    return Some(message);
                }
                let mut chunk = vec![0u8; 8192];
                let read = tokio::time::timeout(RECV_TIMEOUT, self.stream.read(&mut chunk))
                    .await
                    .expect("read did not time out")
                    .expect("read");
                if read == 0 {
                    return None;
                }
                self.buffer.extend_from_slice(&chunk[..read]);
            }
        }

        async fn recv_matching<F>(&mut self, predicate: F) -> BridgeMessage
        where
            F: Fn(&BridgeMessage) -> bool,
        {
            for _ in 0..512 {
                let Some(message) = self.recv().await else {
                    panic!("connection closed before a matching message arrived");
                };
                if predicate(&message) {
                    return message;
                }
            }
            panic!("no matching message in 512 frames");
        }

        async fn handshake(&mut self) -> BridgeAgreement {
            self.send(&BridgeMessage::Hello(BridgeHello {
                supported_versions: vec![BRIDGE_PROTOCOL_VERSION],
                product: "test-client".to_string(),
                product_version: "0.0.1".to_string(),
                max_frame_bytes: MAX_FRAME_BYTES,
                disclosure: DisclosureMode::MetadataOnly,
            }))
            .await;
            match self.recv().await.expect("agreement") {
                BridgeMessage::Agreement(agreement) => agreement,
                other => panic!("expected agreement, got {other:?}"),
            }
        }
    }

    struct Fixture {
        _dir: tempfile::TempDir,
        socket_path: PathBuf,
        view: SharedMaterializedView,
        handle: BridgeServerHandle,
    }

    /// Temp dirs inherit the process umask, so the fixture applies the
    /// owner-only mode the bridge requires of a real deployment.
    fn owner_only_tempdir() -> tempfile::TempDir {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().expect("temp dir");
        std::fs::set_permissions(dir.path(), std::fs::Permissions::from_mode(0o700))
            .expect("owner-only temp dir");
        dir
    }

    async fn fixture(tweak: impl FnOnce(&mut BridgeServerConfig)) -> Fixture {
        let dir = owner_only_tempdir();
        let socket_path = dir.path().join("bridge.sock");
        let mut config = BridgeServerConfig::new(socket_path.clone());
        config.node_id = "node_test".to_string();
        config.boot_id = Some("boot-test".to_string());
        tweak(&mut config);
        let view = MaterializedView::shared_bounded();
        let handle = start_bridge_server(config, view.clone(), DisclosureMode::MetadataOnly)
            .await
            .expect("bridge server starts");
        Fixture {
            _dir: dir,
            socket_path,
            view,
            handle,
        }
    }

    fn audit_row(id: &str) -> AuditEventRow {
        AuditEventRow {
            id: id.to_string(),
            timestamp_ms: 1_000,
            audit_type: "file".to_string(),
            pid: Some(42),
            comm: Some("node".to_string()),
            subject: None,
            action: Some("write".to_string()),
            target: Some("/Users/dev/project/src/main.rs".to_string()),
            status: Some("observed".to_string()),
            summary: None,
            details: serde_json::json!({ "bytes": 4 }),
        }
    }

    fn emit_audit(view: &SharedMaterializedView, id: &str) {
        view.lock()
            .unwrap()
            .emit_audit_event(audit_row(id))
            .unwrap();
    }

    fn scope_registration(handle: &str) -> ScopeRegistration {
        ScopeRegistration {
            scope_handle: handle.to_string(),
            root_pid: Some(42),
            root_start_ticks: None,
            sandbox_cgroup_path: None,
            sandbox_cgroup_id: None,
            starts_monotonic_ns: Some(monotonic_ns()),
            expires_monotonic_ns: None,
            disclosure: DisclosureMode::MetadataOnly,
            required_capabilities: vec![capability_names::PROCESS_CAPTURE.to_string()],
        }
    }

    #[tokio::test]
    async fn hello_is_answered_with_an_agreement_and_health() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        let agreement = client.handshake().await;
        assert_eq!(agreement.protocol_version, BRIDGE_PROTOCOL_VERSION);
        assert_eq!(agreement.node_id, "node_test");
        assert_eq!(agreement.boot_id.as_deref(), Some("boot-test"));
        assert_eq!(agreement.capabilities.len(), capability_names::ALL.len());

        match client.recv().await.expect("health") {
            BridgeMessage::Health(health) => {
                assert_eq!(health.state, BridgeHealth::OK);
                assert_eq!(health.active_scopes, 0);
            }
            other => panic!("expected health, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn a_client_with_no_shared_version_is_rejected() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client
            .send(&BridgeMessage::Hello(BridgeHello {
                supported_versions: vec![99],
                product: "test-client".to_string(),
                product_version: "0.0.1".to_string(),
                max_frame_bytes: MAX_FRAME_BYTES,
                disclosure: DisclosureMode::MetadataOnly,
            }))
            .await;
        assert!(matches!(
            client.recv().await.expect("rejection"),
            BridgeMessage::HelloRejected { .. }
        ));
    }

    #[tokio::test]
    async fn a_non_hello_first_frame_is_rejected() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client
            .send(&BridgeMessage::Ack {
                through_sequence: 1,
            })
            .await;
        assert!(matches!(
            client.recv().await.expect("rejection"),
            BridgeMessage::HelloRejected { .. }
        ));
    }

    #[tokio::test]
    async fn a_single_registered_scope_tags_mutations() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;

        client
            .send(&BridgeMessage::RegisterScope(scope_registration("scope-1")))
            .await;
        match client
            .recv_matching(|message| matches!(message, BridgeMessage::ScopeAccepted { .. }))
            .await
        {
            BridgeMessage::ScopeAccepted {
                scope_handle,
                effective,
            } => {
                assert_eq!(scope_handle, "scope-1");
                assert_eq!(effective.len(), 1);
                assert_eq!(effective[0].name, capability_names::PROCESS_CAPTURE);
            }
            other => panic!("expected scope acceptance, got {other:?}"),
        }

        emit_audit(&fixture.view, "audit-1");
        let message = client
            .recv_matching(|message| matches!(message, BridgeMessage::Mutation(_)))
            .await;
        let BridgeMessage::Mutation(envelope) = message else {
            unreachable!()
        };
        assert_eq!(envelope.scope_handle.as_deref(), Some("scope-1"));
        assert_eq!(envelope.sequence, 1);
        assert!(matches!(
            envelope.mutation,
            ViewMutation::AuditEventInserted(_)
        ));

        client
            .send(&BridgeMessage::UnregisterScope {
                scope_handle: "scope-1".to_string(),
            })
            .await;
        match client
            .recv_matching(|message| matches!(message, BridgeMessage::ScopeUnregistered { .. }))
            .await
        {
            BridgeMessage::ScopeUnregistered {
                flushed_through, ..
            } => assert_eq!(flushed_through, Some(1)),
            other => panic!("expected scope unregistration, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn a_tool_scope_needs_a_registered_parent() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;
        client
            .send(&BridgeMessage::RegisterToolScope(ToolScopeRegistration {
                parent_scope_handle: "scope-missing".to_string(),
                tool_scope_handle: "scope-tool".to_string(),
                tool_cgroup_path: None,
                tool_cgroup_id: None,
                pid: None,
                start_ticks: None,
                starts_monotonic_ns: None,
                expires_monotonic_ns: None,
            }))
            .await;
        match client
            .recv_matching(|message| matches!(message, BridgeMessage::ScopeRejected { .. }))
            .await
        {
            BridgeMessage::ScopeRejected { reason, .. } => {
                assert!(reason.contains("parent"), "{reason}")
            }
            other => panic!("expected rejection, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn acks_are_recorded_per_connection() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;
        emit_audit(&fixture.view, "audit-1");
        client
            .recv_matching(|message| matches!(message, BridgeMessage::Mutation(_)))
            .await;

        client
            .send(&BridgeMessage::Ack {
                through_sequence: 1,
            })
            .await;
        // Give the reader a turn to process the ack.
        for _ in 0..50 {
            tokio::time::sleep(Duration::from_millis(10)).await;
            let acked = fixture
                .handle
                .hub
                .state
                .lock()
                .unwrap()
                .connections
                .first()
                .map(|connection| connection.acked_through.load(Ordering::SeqCst))
                .unwrap_or(0);
            if acked == 1 {
                return;
            }
        }
        panic!("ack was never recorded");
    }

    #[tokio::test]
    async fn a_reconnecting_client_resumes_from_the_replay_buffer() {
        let fixture = fixture(|_| {}).await;
        let mut first = TestClient::connect(&fixture.socket_path).await;
        first.handshake().await;
        for index in 0..3 {
            emit_audit(&fixture.view, &format!("audit-{index}"));
        }
        first
            .recv_matching(|message| matches!(message, BridgeMessage::Mutation(_)))
            .await;
        drop(first);

        let mut second = TestClient::connect(&fixture.socket_path).await;
        second.handshake().await;
        second
            .send(&BridgeMessage::Resume(ResumeRequest {
                node_id: "node_test".to_string(),
                boot_id: Some("boot-test".to_string()),
                after_sequence: 1,
            }))
            .await;

        let mut sequences = Vec::new();
        while sequences.len() < 2 {
            if let BridgeMessage::Mutation(envelope) = second
                .recv_matching(|message| matches!(message, BridgeMessage::Mutation(_)))
                .await
            {
                sequences.push(envelope.sequence);
            }
        }
        assert_eq!(sequences, vec![2, 3]);
    }

    #[tokio::test]
    async fn a_resume_past_the_buffer_reports_unavailable_and_a_snapshot_answers() {
        let fixture = fixture(|config| config.replay_capacity = 2).await;
        for index in 0..5 {
            emit_audit(&fixture.view, &format!("audit-{index}"));
        }

        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;
        client
            .send(&BridgeMessage::Resume(ResumeRequest {
                node_id: "node_test".to_string(),
                boot_id: Some("boot-test".to_string()),
                after_sequence: 1,
            }))
            .await;
        match client
            .recv_matching(|message| matches!(message, BridgeMessage::ResumeUnavailable { .. }))
            .await
        {
            BridgeMessage::ResumeUnavailable { earliest_available } => {
                assert_eq!(earliest_available, Some(4))
            }
            other => panic!("expected resume-unavailable, got {other:?}"),
        }

        client
            .send(&BridgeMessage::SnapshotRequest { scope_handle: None })
            .await;
        let estimated = match client
            .recv_matching(|message| matches!(message, BridgeMessage::SnapshotBegin { .. }))
            .await
        {
            BridgeMessage::SnapshotBegin {
                estimated,
                reconstructed,
            } => {
                assert!(reconstructed, "snapshots must declare reconstruction");
                estimated
            }
            other => panic!("expected snapshot begin, got {other:?}"),
        };
        assert_eq!(estimated, 5);

        let mut seen = 0;
        loop {
            match client.recv().await.expect("snapshot stream") {
                BridgeMessage::Mutation(envelope) => {
                    assert_eq!(
                        envelope.operation,
                        MutationOperation::SnapshotReconstruction,
                        "snapshot rows must not claim original ordering"
                    );
                    seen += 1;
                }
                BridgeMessage::SnapshotEnd { through_sequence } => {
                    assert_eq!(seen, 5);
                    assert!(through_sequence >= 5);
                    break;
                }
                _ => {}
            }
        }
    }

    #[tokio::test]
    async fn saturating_the_outbound_queue_reports_a_capture_gap() {
        let fixture = fixture(|config| config.outbound_capacity = 4).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;
        // Drain the handshake health frame so the queue starts empty.
        client
            .recv_matching(|message| matches!(message, BridgeMessage::Health(_)))
            .await;

        // No await inside the loop, so the writer task cannot drain: the queue
        // overflows deterministically.
        for index in 0..200 {
            emit_audit(&fixture.view, &format!("audit-{index}"));
        }

        let message = client
            .recv_matching(|message| {
                matches!(
                    message,
                    BridgeMessage::Mutation(envelope)
                        if matches!(envelope.mutation, ViewMutation::CaptureGapObserved { .. })
                )
            })
            .await;
        let BridgeMessage::Mutation(envelope) = message else {
            unreachable!()
        };
        let ViewMutation::CaptureGapObserved {
            from_sequence,
            to_sequence,
            ..
        } = envelope.mutation
        else {
            unreachable!()
        };
        assert!(from_sequence >= 1 && to_sequence >= from_sequence);

        let health = fixture.handle.hub.health();
        assert_eq!(health.state, BridgeHealth::DEGRADED);
        assert!(health.dropped_mutations > 0);
    }

    #[tokio::test]
    async fn an_idle_connection_is_closed_after_a_shutdown_notice() {
        let fixture = fixture(|config| {
            config.heartbeat_interval = Duration::from_millis(80);
            config.idle_timeout = Duration::from_millis(250);
        })
        .await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;

        assert!(matches!(
            client
                .recv_matching(|message| matches!(message, BridgeMessage::Heartbeat { .. }))
                .await,
            BridgeMessage::Heartbeat { .. }
        ));

        let shutdown = client
            .recv_matching(|message| matches!(message, BridgeMessage::Shutdown { .. }))
            .await;
        let BridgeMessage::Shutdown { reason } = shutdown else {
            unreachable!()
        };
        assert!(reason.contains("idle"), "{reason}");
        assert!(
            client.recv().await.is_none(),
            "server must close the socket"
        );
    }

    #[tokio::test]
    async fn the_connection_limit_is_enforced() {
        let fixture = fixture(|config| config.max_connections = 1).await;
        let mut first = TestClient::connect(&fixture.socket_path).await;
        first.handshake().await;

        let mut second = TestClient::connect(&fixture.socket_path).await;
        match second.recv().await.expect("rejection") {
            BridgeMessage::HelloRejected { reason } => {
                assert!(reason.contains("too many"), "{reason}")
            }
            other => panic!("expected rejection, got {other:?}"),
        }
    }

    #[tokio::test]
    async fn the_graceful_shutdown_notice_reaches_connected_clients() {
        let fixture = fixture(|_| {}).await;
        let mut client = TestClient::connect(&fixture.socket_path).await;
        client.handshake().await;
        fixture.handle.shutdown("collector stopping");
        let shutdown = client
            .recv_matching(|message| matches!(message, BridgeMessage::Shutdown { .. }))
            .await;
        let BridgeMessage::Shutdown { reason } = shutdown else {
            unreachable!()
        };
        assert_eq!(reason, "collector stopping");
    }

    /// The refusal path needs a second uid, which a unit test cannot create.
    /// This pins the accept side of the policy on Linux; CI covers refusal.
    #[cfg(target_os = "linux")]
    #[tokio::test]
    async fn a_same_uid_peer_passes_the_peer_credential_check() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("peer.sock");
        let listener = UnixListener::bind(&path).unwrap();
        let connect = tokio::spawn(async move { UnixStream::connect(&path).await.unwrap() });
        let (server_side, _) = listener.accept().await.unwrap();
        let _client_side = connect.await.unwrap();
        assert!(peer_is_same_uid(&server_side).is_ok());
    }

    #[test]
    fn outbound_queue_drops_oldest_and_records_the_gap() {
        let queue = OutboundQueue::new(2);
        let envelope = |sequence: u64| {
            BridgeMessage::Mutation(ViewMutationEnvelope {
                protocol_version: BRIDGE_PROTOCOL_VERSION,
                node_id: "node".to_string(),
                boot_id: None,
                sequence,
                observed_wall_ms: None,
                observed_monotonic_ns: None,
                basis: TimestampBasis::Unknown,
                source_component: "test".to_string(),
                source_version: "0".to_string(),
                scope_handle: None,
                operation: MutationOperation::Insert,
                mutation: ViewMutation::RowEvicted {
                    row_kind: "audit_event".to_string(),
                    row_id: format!("row-{sequence}"),
                },
            })
        };
        assert_eq!(queue.push(envelope(1)), 0);
        assert_eq!(queue.push(envelope(2)), 0);
        assert_eq!(queue.push(envelope(3)), 1);
        assert_eq!(queue.push(envelope(4)), 1);
        assert_eq!(queue.dropped(), 2);

        let (messages, gap) = queue.take();
        assert_eq!(messages.len(), 2);
        assert_eq!(gap, Some((1, 2)));
    }

    #[test]
    fn scope_expiry_is_evaluated_against_the_host_monotonic_clock() {
        let now = monotonic_ns();
        let live = ScopeEntry {
            kind: ScopeKind::Sandbox,
            expires_monotonic_ns: Some(now + 1_000_000_000),
            last_sequence: 0,
        };
        let expired = ScopeEntry {
            kind: ScopeKind::Tool,
            expires_monotonic_ns: Some(now.saturating_sub(1)),
            last_sequence: 0,
        };
        let forever = ScopeEntry {
            kind: ScopeKind::Sandbox,
            expires_monotonic_ns: None,
            last_sequence: 0,
        };
        assert!(live.is_active(now));
        assert!(!expired.is_active(now));
        assert!(forever.is_active(now));
    }

    #[test]
    fn a_single_active_scope_is_the_only_auto_tag() {
        let mut state = HubState::default();
        let now = monotonic_ns();
        assert_eq!(BridgeHub::active_scope_handle(&state, now), None);

        state.scopes.insert(
            "scope-a".to_string(),
            ScopeEntry {
                kind: ScopeKind::Sandbox,
                expires_monotonic_ns: None,
                last_sequence: 0,
            },
        );
        assert_eq!(
            BridgeHub::active_scope_handle(&state, now).as_deref(),
            Some("scope-a")
        );

        state.scopes.insert(
            "scope-b".to_string(),
            ScopeEntry {
                kind: ScopeKind::Tool,
                expires_monotonic_ns: None,
                last_sequence: 0,
            },
        );
        assert_eq!(BridgeHub::active_scope_handle(&state, now), None);
    }

    #[test]
    fn socket_parent_must_be_a_real_owner_only_directory() {
        use std::os::unix::fs::PermissionsExt;
        let dir = owner_only_tempdir();
        assert!(prepare_socket_path(&dir.path().join("bridge.sock")).is_ok());

        std::fs::set_permissions(dir.path(), std::fs::Permissions::from_mode(0o755)).unwrap();
        assert!(prepare_socket_path(&dir.path().join("bridge.sock")).is_err());
        std::fs::set_permissions(dir.path(), std::fs::Permissions::from_mode(0o700)).unwrap();

        let regular = dir.path().join("not-a-socket");
        std::fs::write(&regular, b"x").unwrap();
        assert!(prepare_socket_path(&regular).is_err());
    }
}
