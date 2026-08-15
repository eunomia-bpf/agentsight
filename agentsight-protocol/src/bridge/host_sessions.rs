// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Machine-wide live agent sessions: the `agentsight top` rows, projected for a
//! consumer that is not a terminal.
//!
//! The TUI shows an operator their own machine, so it may print a workspace path
//! and the full command line of an agent. This message crosses a process
//! boundary into a product surface, so it may not: every string here is either a
//! coarse class, a basename, or an opaque key. `workspace_class` carries the
//! path bucket and the workspace's own basename and nothing that led to it;
//! `context_class` carries the executable basename only, never the argument
//! vector the CONTEXT column displays.
//!
//! **A point query, not a stream.** The snapshot answers what the collector's
//! live session registry holds at `generated_ms`; there is no sequence, no
//! replay and no revision, because nothing here is a materialized-view row.
//! Missingness is explicit: every field the collector did not observe is
//! `None`, never a zero. A session with no live process reports no
//! `cpu_percent`, not `0.0`.

use serde::{Deserialize, Serialize};

/// One live agent session as the collector's session registry sees it.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HostSessionRow {
    /// Stable identity of the session: the agent's own transcript session id
    /// where the collector knows it, otherwise `proc:<pid>:<start_ticks>`, which
    /// survives pid reuse. Opaque to the consumer either way.
    pub session_key: String,
    /// `claude` | `codex` | `gemini` | whatever label the collector attributed.
    pub agent_kind: String,
    /// [`HostSessionRow::LIVE`], [`HostSessionRow::IDLE`], or
    /// [`HostSessionRow::STOPPED`].
    pub state: String,
    pub started_ms: Option<u64>,
    pub last_message_ms: Option<u64>,
    pub model: Option<String>,
    pub input_tokens: Option<i64>,
    pub output_tokens: Option<i64>,
    pub total_tokens: Option<i64>,
    /// Countable events the collector attributed to this session. Absent when
    /// no counting evidence source was attached to the row at all — a row with
    /// no transcript and no eBPF capture has an unknown count, not a zero one.
    pub activity_events: Option<u64>,
    /// Seconds `activity_events` covers. Absent when the collector cannot say
    /// what window it counted over.
    pub activity_window_s: Option<u64>,
    pub cpu_percent: Option<f64>,
    pub memory_bytes: Option<u64>,
    /// [`HostSessionRow::EVIDENCE_PROC`], [`HostSessionRow::EVIDENCE_TRANSCRIPT`]
    /// or [`HostSessionRow::EVIDENCE_EBPF`]: the strongest source behind the row.
    pub evidence_source: String,
    /// Path bucket plus the workspace's own basename, e.g. `repo:agentsight`.
    /// Never a path.
    pub workspace_class: Option<String>,
    /// Executable basename only, e.g. `claude`. Never an argument vector.
    pub context_class: Option<String>,
    pub pid: Option<u32>,
    /// Kernel process start time in clock ticks, the other half of the identity
    /// that survives pid reuse.
    pub start_ticks: Option<u64>,
}

impl HostSessionRow {
    /// A process is running and the session is doing something.
    pub const LIVE: &'static str = "live";
    /// A process is running and the session has been quiet.
    pub const IDLE: &'static str = "idle";
    /// No live process is attributed to the session.
    pub const STOPPED: &'static str = "stopped";

    /// The row is backed by a process observation.
    pub const EVIDENCE_PROC: &'static str = "proc";
    /// The row is backed by the agent's own session transcript.
    pub const EVIDENCE_TRANSCRIPT: &'static str = "transcript";
    /// The row is backed by kernel capture.
    pub const EVIDENCE_EBPF: &'static str = "ebpf";
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bridge::{BridgeMessage, decode_body, encode_body};

    fn row() -> HostSessionRow {
        HostSessionRow {
            session_key: "b8f0c3d2-0000-4000-8000-000000000001".to_string(),
            agent_kind: "claude".to_string(),
            state: HostSessionRow::LIVE.to_string(),
            started_ms: Some(1_760_000_000_000),
            last_message_ms: Some(1_760_000_060_000),
            model: Some("claude-sonnet-4".to_string()),
            input_tokens: Some(1200),
            output_tokens: Some(340),
            total_tokens: Some(1540),
            activity_events: Some(7),
            activity_window_s: Some(60),
            cpu_percent: Some(12.5),
            memory_bytes: Some(536_870_912),
            evidence_source: HostSessionRow::EVIDENCE_TRANSCRIPT.to_string(),
            workspace_class: Some("repo:agentsight".to_string()),
            context_class: Some("claude".to_string()),
            pid: Some(4242),
            start_ticks: Some(918_273),
        }
    }

    #[test]
    fn the_query_and_snapshot_round_trip_through_cbor() {
        for message in [
            BridgeMessage::HostSessionsQuery {},
            BridgeMessage::HostSessionsSnapshot {
                generated_ms: 1_760_000_100_000,
                sessions: vec![row()],
            },
        ] {
            let bytes = encode_body(&message).unwrap();
            assert_eq!(decode_body(&bytes).unwrap(), message);
        }
    }

    #[test]
    fn message_tags_are_the_documented_snake_case_names() {
        let json = serde_json::to_value(BridgeMessage::HostSessionsQuery {}).unwrap();
        assert_eq!(json["msg"], "host_sessions_query");

        let json = serde_json::to_value(BridgeMessage::HostSessionsSnapshot {
            generated_ms: 5,
            sessions: Vec::new(),
        })
        .unwrap();
        assert_eq!(json["msg"], "host_sessions_snapshot");
        assert_eq!(json["data"]["generated_ms"], 5);
        assert_eq!(json["data"]["sessions"], serde_json::json!([]));
    }

    /// Unobserved is `null` on the wire, never a zero that a reader would
    /// display as a measurement.
    #[test]
    fn unobserved_fields_serialize_as_null_rather_than_zero() {
        let row = HostSessionRow {
            started_ms: None,
            last_message_ms: None,
            model: None,
            input_tokens: None,
            output_tokens: None,
            total_tokens: None,
            activity_events: None,
            activity_window_s: None,
            cpu_percent: None,
            memory_bytes: None,
            workspace_class: None,
            context_class: None,
            pid: None,
            start_ticks: None,
            state: HostSessionRow::STOPPED.to_string(),
            ..row()
        };
        let json = serde_json::to_value(&row).unwrap();
        for field in [
            "started_ms",
            "last_message_ms",
            "model",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "activity_events",
            "activity_window_s",
            "cpu_percent",
            "memory_bytes",
            "workspace_class",
            "context_class",
            "pid",
            "start_ticks",
        ] {
            assert_eq!(json[field], serde_json::Value::Null, "{field} is not null");
        }
    }
}
