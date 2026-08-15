// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Golden vectors for bridge protocol v1.
//!
//! These fixtures are the cross-repo compatibility contract: an independent
//! implementation of the same wire types must produce byte-identical CBOR for
//! every entry. Regenerate with `BRIDGE_UPDATE_FIXTURES=1 cargo test -p
//! agentsight-protocol --features bridge --test bridge_golden`.

#![cfg(feature = "bridge")]

use agentsight_protocol::bridge::{
    AroAnnotation, AroAnnotationRow, AroCorrelationRow, AroEnforcementRow, AroPolicyDecisionRow,
    AroResourceDomainRow, BRIDGE_PROTOCOL_VERSION, BridgeAgreement, BridgeAuditEventRow,
    BridgeCapability, BridgeHealth, BridgeHello, BridgeLlmCallRow, BridgeMessage,
    BridgeNetworkTargetRow, BridgeProcessNodeRow, BridgeResourceSampleRow, BridgeSessionRow,
    BridgeTokenUsageRow, BridgeToolCallRow, DisclosureMode, HostSessionRow, MAX_FRAME_BYTES,
    MutationOperation, ResumeRequest, ScopeRegistration, TimestampBasis, ToolScopeRegistration,
    ViewMutation, ViewMutationEnvelope, capability_names, decode_body, encode_body,
};
use serde_json::{Value, json};
use std::path::PathBuf;

fn fixture_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/bridge-v1")
}

fn to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn from_hex(hex: &str) -> Vec<u8> {
    assert!(
        hex.len().is_multiple_of(2),
        "cbor_hex must have an even length"
    );
    (0..hex.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&hex[index..index + 2], 16).expect("hex digit"))
        .collect()
}

fn envelope(sequence: u64, operation: MutationOperation, mutation: ViewMutation) -> BridgeMessage {
    BridgeMessage::Mutation(ViewMutationEnvelope {
        protocol_version: BRIDGE_PROTOCOL_VERSION,
        node_id: "node_goldenvector0001".to_string(),
        boot_id: Some("2f8a1c6e-0000-4000-8000-00000000b007".to_string()),
        sequence,
        observed_wall_ms: Some(1_760_000_000_000),
        observed_monotonic_ns: Some(4_200_000_000),
        basis: TimestampBasis::EpochMilliseconds,
        source_component: "agentsight-capture".to_string(),
        source_version: "1.0.20".to_string(),
        scope_handle: Some("scope-0192f000-0000-7000-8000-000000000001".to_string()),
        operation,
        mutation,
    })
}

fn handshake_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "hello_metadata_only",
            BridgeMessage::Hello(BridgeHello {
                supported_versions: vec![BRIDGE_PROTOCOL_VERSION],
                product: "aro".to_string(),
                product_version: "0.1.0".to_string(),
                max_frame_bytes: MAX_FRAME_BYTES,
                disclosure: DisclosureMode::MetadataOnly,
            }),
        ),
        (
            "hello_incident_scoped",
            BridgeMessage::Hello(BridgeHello {
                supported_versions: vec![BRIDGE_PROTOCOL_VERSION],
                product: "aro".to_string(),
                product_version: "0.1.0".to_string(),
                max_frame_bytes: 262_144,
                disclosure: DisclosureMode::IncidentScoped {
                    approval_id: "approval-0001".to_string(),
                    field_allowlist: vec!["cwd".to_string(), "host".to_string()],
                    expires_at_ms: 1_760_000_600_000,
                },
            }),
        ),
        (
            "agreement",
            BridgeMessage::Agreement(BridgeAgreement {
                protocol_version: BRIDGE_PROTOCOL_VERSION,
                product: "agentsight".to_string(),
                product_version: "1.0.20".to_string(),
                build_commit: Some("f7d961f86d57073013a58a8f72ea0528e8e63c38".to_string()),
                binary_digest: None,
                node_id: "node_goldenvector0001".to_string(),
                boot_id: Some("2f8a1c6e-0000-4000-8000-00000000b007".to_string()),
                capabilities: capability_names::ALL
                    .iter()
                    .map(|name| BridgeCapability::new(*name, true, None))
                    .collect(),
                max_frame_bytes: MAX_FRAME_BYTES,
            }),
        ),
        (
            "hello_rejected",
            BridgeMessage::HelloRejected {
                reason: "no shared protocol version".to_string(),
            },
        ),
        (
            "heartbeat",
            BridgeMessage::Heartbeat {
                monotonic_ns: 4_200_000_000,
            },
        ),
        (
            "shutdown",
            BridgeMessage::Shutdown {
                reason: "collector stopping".to_string(),
            },
        ),
    ]
}

fn scope_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "register_scope",
            BridgeMessage::RegisterScope(ScopeRegistration {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                root_pid: Some(4242),
                root_start_ticks: Some(918_273),
                sandbox_cgroup_path: Some("/sys/fs/cgroup/aro/cell-1".to_string()),
                sandbox_cgroup_id: Some(9_007_199_254_740_993),
                starts_monotonic_ns: Some(4_100_000_000),
                expires_monotonic_ns: Some(4_900_000_000),
                disclosure: DisclosureMode::MetadataOnly,
                required_capabilities: vec![
                    capability_names::PROCESS_CAPTURE.to_string(),
                    capability_names::CGROUP_FILTER.to_string(),
                ],
            }),
        ),
        (
            "register_tool_scope",
            BridgeMessage::RegisterToolScope(ToolScopeRegistration {
                parent_scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                tool_scope_handle: "scope-0192f000-0000-7000-8000-000000000002".to_string(),
                tool_cgroup_path: Some("/sys/fs/cgroup/aro/cell-1/tool-7".to_string()),
                tool_cgroup_id: Some(9_007_199_254_740_994),
                pid: Some(4310),
                start_ticks: Some(918_500),
                starts_monotonic_ns: Some(4_300_000_000),
                expires_monotonic_ns: None,
            }),
        ),
        (
            "scope_accepted",
            BridgeMessage::ScopeAccepted {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                effective: vec![
                    BridgeCapability::new(capability_names::PROCESS_CAPTURE, true, None),
                    BridgeCapability::new(
                        capability_names::CGROUP_FILTER,
                        false,
                        Some("no cgroup filter configured".to_string()),
                    ),
                ],
            },
        ),
        (
            "scope_rejected",
            BridgeMessage::ScopeRejected {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000003".to_string(),
                reason: "unknown parent scope".to_string(),
            },
        ),
        (
            "unregister_scope",
            BridgeMessage::UnregisterScope {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
            },
        ),
        (
            "scope_unregistered",
            BridgeMessage::ScopeUnregistered {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                flushed_through: Some(128),
            },
        ),
    ]
}

fn control_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "ack",
            BridgeMessage::Ack {
                through_sequence: 128,
            },
        ),
        (
            "resume",
            BridgeMessage::Resume(ResumeRequest {
                node_id: "node_goldenvector0001".to_string(),
                boot_id: Some("2f8a1c6e-0000-4000-8000-00000000b007".to_string()),
                after_sequence: 128,
            }),
        ),
        (
            "resume_unavailable",
            BridgeMessage::ResumeUnavailable {
                earliest_available: Some(4096),
            },
        ),
        (
            "snapshot_request",
            BridgeMessage::SnapshotRequest {
                scope_handle: Some("scope-0192f000-0000-7000-8000-000000000001".to_string()),
            },
        ),
        (
            "snapshot_begin",
            BridgeMessage::SnapshotBegin {
                estimated: 12,
                reconstructed: true,
            },
        ),
        (
            "snapshot_end",
            BridgeMessage::SnapshotEnd {
                through_sequence: 140,
            },
        ),
        (
            "health_ok",
            BridgeMessage::Health(BridgeHealth {
                state: BridgeHealth::OK.to_string(),
                detail: None,
                capture_gaps: 0,
                dropped_mutations: 0,
                active_scopes: 1,
                aro_annotations_evicted: Some(0),
            }),
        ),
        (
            "health_degraded",
            BridgeMessage::Health(BridgeHealth {
                state: BridgeHealth::DEGRADED.to_string(),
                detail: Some("outbound queue saturated".to_string()),
                capture_gaps: 2,
                dropped_mutations: 37,
                active_scopes: 1,
                // Annotation evictions are reported beside the capture counters
                // and never fold into them: a dropped annotation is the client's
                // own row going missing, not capture the collector lost.
                aro_annotations_evicted: Some(9),
            }),
        ),
    ]
}

fn mutation_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "session_upsert",
            envelope(
                1,
                MutationOperation::Insert,
                ViewMutation::SessionUpsert(BridgeSessionRow {
                    row_id: "local:claude:session-1".to_string(),
                    revision: 0,
                    agent_type: "claude".to_string(),
                    start_ts_ms: 1_760_000_000_000,
                    end_ts_ms: Some(1_760_000_060_000),
                    status: "observed".to_string(),
                    model: Some("claude-sonnet-4".to_string()),
                    input_tokens: 1200,
                    output_tokens: 340,
                    total_tokens: 1540,
                    view_source: "agent_native_session".to_string(),
                    confidence: Some(0.95),
                    cwd_class: Some("repo".to_string()),
                    content: None,
                }),
            ),
        ),
        (
            "llm_call_upsert",
            envelope(
                2,
                MutationOperation::Update,
                ViewMutation::LlmCallUpsert(BridgeLlmCallRow {
                    row_id: "llm-1".to_string(),
                    revision: 1,
                    session_row_id: Some("local:claude:session-1".to_string()),
                    start_ts_ms: 1_760_000_001_000,
                    end_ts_ms: Some(1_760_000_002_500),
                    pid: Some(4242),
                    comm: Some("claude".to_string()),
                    provider: Some("anthropic".to_string()),
                    model: Some("claude-sonnet-4".to_string()),
                    call_kind: Some("messages".to_string()),
                    status: "complete".to_string(),
                    error_type: None,
                    finish_reason: Some("end_turn".to_string()),
                    status_code: Some(200),
                    input_tokens: 1200,
                    output_tokens: 340,
                    total_tokens: 1540,
                    destination_class: Some("model_provider:anthropic".to_string()),
                    content: None,
                }),
            ),
        ),
        (
            "token_usage_upsert",
            envelope(
                3,
                MutationOperation::Insert,
                ViewMutation::TokenUsageUpsert(BridgeTokenUsageRow {
                    row_id: "token-1".to_string(),
                    revision: 0,
                    llm_call_row_id: Some("llm-1".to_string()),
                    ts_ms: 1_760_000_002_500,
                    pid: Some(4242),
                    comm: Some("claude".to_string()),
                    provider: Some("anthropic".to_string()),
                    model: Some("claude-sonnet-4".to_string()),
                    input_tokens: 1200,
                    output_tokens: 340,
                    cache_creation_tokens: 64,
                    cache_read_tokens: 128,
                    total_tokens: 1540,
                    source: "response_usage".to_string(),
                    view_source: "materialized_view".to_string(),
                    confidence: Some(1.0),
                }),
            ),
        ),
        (
            "tool_call_upsert",
            envelope(
                4,
                MutationOperation::Insert,
                ViewMutation::ToolCallUpsert(BridgeToolCallRow {
                    row_id: "tool-1".to_string(),
                    revision: 0,
                    session_row_id: Some("local:claude:session-1".to_string()),
                    ts_ms: 1_760_000_003_000,
                    tool_name: Some("Bash".to_string()),
                    semantic_category: Some("shell".to_string()),
                    native_tool_call_id: Some("toolu_01".to_string()),
                    start_ts_ms: Some(1_760_000_003_000),
                    end_ts_ms: Some(1_760_000_003_400),
                    duration_ms: Some(400),
                    status: Some("success".to_string()),
                    related_pid: Some(4310),
                    view_source: "agent_native_session".to_string(),
                    confidence: Some(0.9),
                    content: None,
                }),
            ),
        ),
        (
            "process_node_upsert",
            envelope(
                5,
                MutationOperation::Insert,
                ViewMutation::ProcessNodeUpsert(BridgeProcessNodeRow {
                    row_id: "pid:4310:start:918500".to_string(),
                    revision: 0,
                    pid: 4310,
                    start_ticks: Some(918_500),
                    ppid: Some(4242),
                    root_pid: Some(4242),
                    start_ts_ms: Some(1_760_000_003_000),
                    end_ts_ms: None,
                    comm: Some("bash".to_string()),
                    executable_basename: Some("bash".to_string()),
                    command_fingerprint: Some(
                        "1f0a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8"
                            .to_string(),
                    ),
                    argv_shape: Some("cmd <flag> <path>".to_string()),
                    cwd_class: Some("repo".to_string()),
                    exit_code: None,
                    status: Some("running".to_string()),
                    view_source: "process".to_string(),
                    confidence: Some(1.0),
                    content: None,
                }),
            ),
        ),
        (
            "audit_event_inserted",
            envelope(
                6,
                MutationOperation::Insert,
                ViewMutation::AuditEventInserted(BridgeAuditEventRow {
                    row_id: "audit-1".to_string(),
                    ts_ms: 1_760_000_003_100,
                    audit_type: "file".to_string(),
                    pid: Some(4310),
                    comm: Some("bash".to_string()),
                    action: Some("write".to_string()),
                    path_class: Some("repo".to_string()),
                    extension: Some("rs".to_string()),
                    destination_class: None,
                    port: None,
                    protocol: None,
                    bytes_or_count: Some(2048),
                    status: Some("observed".to_string()),
                    raw_target_digest: Some(
                        "9c1185a5c5e9fc54612808977ee8f548b2258d31111111111111111111111111"
                            .to_string(),
                    ),
                    content: None,
                }),
            ),
        ),
        (
            "network_target_upsert",
            envelope(
                7,
                MutationOperation::Update,
                ViewMutation::NetworkTargetUpsert(BridgeNetworkTargetRow {
                    row_id: "network:4242:3d1c5f7a9b2e4c60".to_string(),
                    revision: 3,
                    pid: Some(4242),
                    comm: Some("claude".to_string()),
                    destination_class: "model_provider:anthropic".to_string(),
                    port: Some(443),
                    count: 12,
                    error_count: 1,
                    first_ts_ms: Some(1_760_000_001_000),
                    last_ts_ms: Some(1_760_000_005_000),
                    raw_target_digest: Some(
                        "5f2b1a0c9d8e7f60514233445566778899aabbccddeeff0011223344556677aa"
                            .to_string(),
                    ),
                    content: None,
                }),
            ),
        ),
        (
            "resource_sample_inserted",
            envelope(
                8,
                MutationOperation::Insert,
                ViewMutation::ResourceSampleInserted(BridgeResourceSampleRow {
                    ts_ms: 1_760_000_004_000,
                    pid: Some(4242),
                    comm: Some("claude".to_string()),
                    cpu_percent: Some(37.5),
                    rss_mb: Some(512),
                }),
            ),
        ),
        (
            "capture_capability_changed",
            envelope(
                9,
                MutationOperation::Update,
                ViewMutation::CaptureCapabilityChanged {
                    capability: capability_names::TLS_CAPTURE.to_string(),
                    available: false,
                    detail: Some("sslsniff exited".to_string()),
                },
            ),
        ),
        (
            "capture_gap_observed",
            envelope(
                10,
                MutationOperation::Insert,
                ViewMutation::CaptureGapObserved {
                    from_sequence: 40,
                    to_sequence: 77,
                    reason: "outbound queue overflow".to_string(),
                },
            ),
        ),
        (
            "row_evicted",
            envelope(
                11,
                MutationOperation::Delete,
                ViewMutation::RowEvicted {
                    row_kind: "audit_event".to_string(),
                    row_id: "audit-1".to_string(),
                },
            ),
        ),
        (
            "session_upsert_research_full_content",
            envelope(
                12,
                MutationOperation::SnapshotReconstruction,
                ViewMutation::SessionUpsert(BridgeSessionRow {
                    row_id: "local:claude:session-1".to_string(),
                    revision: 2,
                    agent_type: "claude".to_string(),
                    start_ts_ms: 1_760_000_000_000,
                    end_ts_ms: None,
                    status: "observed".to_string(),
                    model: None,
                    input_tokens: 0,
                    output_tokens: 0,
                    total_tokens: 0,
                    view_source: "agent_native_session".to_string(),
                    confidence: None,
                    cwd_class: Some("repo".to_string()),
                    content: Some(agentsight_protocol::bridge::SessionContent {
                        cwd: Some("/repo/agentsight".to_string()),
                    }),
                }),
            ),
        ),
    ]
}

/// The reverse-annotation stream: client -> server, behind the
/// `aro_annotations` capability.
///
/// The agreement that advertises the capability is pinned here as well as in
/// `handshake_vectors` because this is the file a client reads to decide whether
/// to send an annotation at all: the gate is the advertised capability, not the
/// protocol version. The collector implements the arm, so the name is in
/// `capability_names::ALL` and the two agreements agree — a build that dropped
/// the arm would have to stop naming it, and this vector would be the thing that
/// no longer described it.
fn annotation_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "agreement_advertising_aro_annotations",
            BridgeMessage::Agreement(BridgeAgreement {
                protocol_version: BRIDGE_PROTOCOL_VERSION,
                product: "agentsight".to_string(),
                product_version: "1.0.20".to_string(),
                build_commit: Some("f7d961f86d57073013a58a8f72ea0528e8e63c38".to_string()),
                binary_digest: None,
                node_id: "node_goldenvector0001".to_string(),
                boot_id: Some("2f8a1c6e-0000-4000-8000-00000000b007".to_string()),
                capabilities: capability_names::ALL
                    .iter()
                    .map(|name| BridgeCapability::new(*name, true, None))
                    .collect(),
                max_frame_bytes: MAX_FRAME_BYTES,
            }),
        ),
        (
            "annotation_resource_domain",
            BridgeMessage::Annotation(AroAnnotation {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                sequence: 1,
                row: AroAnnotationRow::ResourceDomain(AroResourceDomainRow {
                    row_id: "domain-0192f000-0000-7000-8000-000000000001".to_string(),
                    revision: 0,
                    scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                    cgroup_path_class: Some("sandbox".to_string()),
                    containment: Some("cgroup_v2".to_string()),
                    assurance: Some("verified".to_string()),
                    memory_high_bytes: Some(536_870_912),
                    memory_max_bytes: Some(1_073_741_824),
                    cpu_quota_ppm: Some(500_000),
                    cpu_weight: Some(100),
                    pids_max: Some(256),
                    lease: Some("held".to_string()),
                }),
            }),
        ),
        (
            "annotation_enforcement",
            BridgeMessage::Annotation(AroAnnotation {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000002".to_string(),
                sequence: 2,
                row: AroAnnotationRow::Enforcement(AroEnforcementRow {
                    row_id: "enforcement-0192f000-0000-7000-8000-000000000002".to_string(),
                    revision: 1,
                    scope_handle: "scope-0192f000-0000-7000-8000-000000000002".to_string(),
                    tool_call_class: Some("shell".to_string()),
                    verified: true,
                    achieved: Some("within_limits".to_string()),
                    throttle_ms: Some(120),
                    frozen_ms: Some(0),
                    oom_kills: Some(0),
                    termination: Some("completed".to_string()),
                    cleanup_verified: Some(true),
                }),
            }),
        ),
        (
            "annotation_policy_decision",
            BridgeMessage::Annotation(AroAnnotation {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                sequence: 3,
                row: AroAnnotationRow::PolicyDecision(AroPolicyDecisionRow {
                    row_id: "policy-0192f000-0000-7000-8000-000000000003".to_string(),
                    revision: 0,
                    scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                    decision: "allow".to_string(),
                    mode: Some("enforce".to_string()),
                    outcome: Some("applied".to_string()),
                    rung: Some("rung-2".to_string()),
                }),
            }),
        ),
        (
            "annotation_correlation",
            BridgeMessage::Annotation(AroAnnotation {
                scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                sequence: 4,
                row: AroAnnotationRow::Correlation(AroCorrelationRow {
                    row_id: "correlation-0192f000-0000-7000-8000-000000000004".to_string(),
                    revision: 0,
                    scope_handle: "scope-0192f000-0000-7000-8000-000000000001".to_string(),
                    external_row_kind: "resource_sample".to_string(),
                    external_row_id: "sample-0192f000-0000-7000-8000-000000000005".to_string(),
                    basis: "cgroup_id".to_string(),
                    confidence: 0.87,
                }),
            }),
        ),
    ]
}

/// The machine-wide live session answer: client -> server query, server ->
/// client snapshot, behind the `host_sessions` capability.
///
/// Pinned here for the same reason the annotation pair is: the gate is the
/// advertised capability, so the agreement that advertises it is part of the
/// contract a client reads before it sends the query. The two snapshots are the
/// two shapes a consumer must handle — a fully observed row, and a row the
/// collector could say almost nothing about, where absent stays absent instead
/// of becoming zero.
fn host_session_vectors() -> Vec<(&'static str, BridgeMessage)> {
    vec![
        (
            "agreement_advertising_host_sessions",
            BridgeMessage::Agreement(BridgeAgreement {
                protocol_version: BRIDGE_PROTOCOL_VERSION,
                product: "agentsight".to_string(),
                product_version: "1.0.20".to_string(),
                build_commit: Some("f7d961f86d57073013a58a8f72ea0528e8e63c38".to_string()),
                binary_digest: None,
                node_id: "node_goldenvector0001".to_string(),
                boot_id: Some("2f8a1c6e-0000-4000-8000-00000000b007".to_string()),
                capabilities: capability_names::ALL
                    .iter()
                    .map(|name| BridgeCapability::new(*name, true, None))
                    .collect(),
                max_frame_bytes: MAX_FRAME_BYTES,
            }),
        ),
        ("host_sessions_query", BridgeMessage::HostSessionsQuery {}),
        (
            "host_sessions_snapshot",
            BridgeMessage::HostSessionsSnapshot {
                generated_ms: 1_760_000_100_000,
                sessions: vec![
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
                        activity_window_s: Some(100),
                        cpu_percent: Some(12.5),
                        memory_bytes: Some(536_870_912),
                        evidence_source: HostSessionRow::EVIDENCE_TRANSCRIPT.to_string(),
                        workspace_class: Some("repo:agentsight".to_string()),
                        context_class: Some("claude".to_string()),
                        pid: Some(4242),
                        start_ticks: Some(918_273),
                    },
                    HostSessionRow {
                        session_key: "proc:4310:918500".to_string(),
                        agent_kind: "codex".to_string(),
                        state: HostSessionRow::IDLE.to_string(),
                        started_ms: Some(1_760_000_003_000),
                        last_message_ms: None,
                        model: None,
                        input_tokens: None,
                        output_tokens: None,
                        total_tokens: None,
                        activity_events: None,
                        activity_window_s: None,
                        cpu_percent: Some(0.0),
                        memory_bytes: Some(67_108_864),
                        evidence_source: HostSessionRow::EVIDENCE_PROC.to_string(),
                        workspace_class: Some("repo:agentsight".to_string()),
                        context_class: Some("codex".to_string()),
                        pid: Some(4310),
                        start_ticks: Some(918_500),
                    },
                ],
            },
        ),
        (
            "host_sessions_snapshot_empty",
            BridgeMessage::HostSessionsSnapshot {
                generated_ms: 1_760_000_100_000,
                sessions: Vec::new(),
            },
        ),
    ]
}

fn categories() -> Vec<(&'static str, Vec<(&'static str, BridgeMessage)>)> {
    vec![
        ("handshake", handshake_vectors()),
        ("scope", scope_vectors()),
        ("control", control_vectors()),
        ("mutation", mutation_vectors()),
        ("annotations", annotation_vectors()),
        ("host_sessions", host_session_vectors()),
    ]
}

fn entry_json(name: &str, message: &BridgeMessage) -> Value {
    json!({
        "name": name,
        "message": serde_json::to_value(message).expect("message serializes to JSON"),
        "cbor_hex": to_hex(&encode_body(message).expect("message encodes to CBOR")),
    })
}

fn write_fixtures() {
    let dir = fixture_dir();
    std::fs::create_dir_all(&dir).expect("fixture directory");
    for (category, vectors) in categories() {
        let entries = vectors
            .iter()
            .map(|(name, message)| entry_json(name, message))
            .collect::<Vec<_>>();
        let mut body = serde_json::to_string_pretty(&Value::Array(entries)).expect("fixture json");
        body.push('\n');
        std::fs::write(dir.join(format!("{category}.json")), body).expect("write fixture");
    }
}

#[test]
fn golden_vectors_match_the_current_encoding() {
    if std::env::var_os("BRIDGE_UPDATE_FIXTURES").is_some() {
        write_fixtures();
    }

    for (category, vectors) in categories() {
        let path = fixture_dir().join(format!("{category}.json"));
        let raw = std::fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("missing fixture {}: {error}", path.display()));
        let entries: Vec<Value> = serde_json::from_str(&raw).expect("fixture parses as JSON array");
        assert_eq!(
            entries.len(),
            vectors.len(),
            "{category}: fixture entry count drifted from the in-code vectors"
        );

        for (entry, (name, message)) in entries.iter().zip(vectors.iter()) {
            assert_eq!(entry["name"], json!(name), "{category}: entry name drifted");

            // The fixture's JSON form must deserialize to the same message the
            // code builds, and re-encode to exactly the recorded bytes.
            let decoded_from_json: BridgeMessage = serde_json::from_value(entry["message"].clone())
                .unwrap_or_else(|error| panic!("{category}/{name}: json decode: {error}"));
            assert_eq!(&decoded_from_json, message, "{category}/{name}: json form");

            let cbor_hex = entry["cbor_hex"].as_str().expect("cbor_hex is a string");
            assert_eq!(
                to_hex(&encode_body(&decoded_from_json).expect("encode")),
                cbor_hex,
                "{category}/{name}: CBOR bytes drifted"
            );

            let decoded_from_cbor = decode_body(&from_hex(cbor_hex))
                .unwrap_or_else(|error| panic!("{category}/{name}: cbor decode: {error}"));
            assert_eq!(&decoded_from_cbor, message, "{category}/{name}: cbor form");
            assert_eq!(
                serde_json::to_value(&decoded_from_cbor).expect("re-serialize"),
                entry["message"],
                "{category}/{name}: JSON form is not stable through CBOR"
            );
        }
    }
}

#[test]
fn every_mutation_kind_has_a_golden_vector() {
    let kinds = mutation_vectors()
        .iter()
        .filter_map(|(_, message)| match message {
            BridgeMessage::Mutation(envelope) => {
                Some(serde_json::to_value(&envelope.mutation).unwrap()["kind"].clone())
            }
            _ => None,
        })
        .collect::<Vec<_>>();
    for kind in [
        "session_upsert",
        "llm_call_upsert",
        "token_usage_upsert",
        "tool_call_upsert",
        "process_node_upsert",
        "audit_event_inserted",
        "network_target_upsert",
        "resource_sample_inserted",
        "capture_capability_changed",
        "capture_gap_observed",
        "row_evicted",
    ] {
        assert!(kinds.contains(&json!(kind)), "no golden vector for {kind}");
    }
}

#[test]
fn every_annotation_row_kind_has_a_golden_vector() {
    let kinds = annotation_vectors()
        .iter()
        .filter_map(|(_, message)| match message {
            BridgeMessage::Annotation(annotation) => Some(annotation.row.row_kind()),
            _ => None,
        })
        .collect::<Vec<_>>();
    for kind in [
        "resource_domain",
        "enforcement",
        "policy_decision",
        "correlation",
    ] {
        assert!(kinds.contains(&kind), "no golden vector for {kind}");
    }
}

/// Same rule as the annotation pair: the gate is the advertised capability, so
/// the fixture a client reads must carry it.
#[test]
fn the_host_sessions_capability_is_advertised_by_a_pinned_agreement() {
    let advertised = host_session_vectors()
        .iter()
        .filter_map(|(_, message)| match message {
            BridgeMessage::Agreement(agreement) => Some(agreement.capabilities.clone()),
            _ => None,
        })
        .flatten()
        .any(|capability| {
            capability.name == capability_names::HOST_SESSIONS && capability.available
        });
    assert!(advertised, "no pinned agreement advertises host_sessions");
    assert!(
        capability_names::ALL.contains(&capability_names::HOST_SESSIONS),
        "the collector answers the query, so the name it enumerates must include it"
    );
}

/// The corpus is where a privacy regression would show up first: a host session
/// row that started carrying a path or an argument vector would have to change
/// these bytes to do it.
#[test]
fn no_pinned_host_session_row_carries_a_path_or_an_argument() {
    for (name, message) in host_session_vectors() {
        let BridgeMessage::HostSessionsSnapshot { sessions, .. } = message else {
            continue;
        };
        for row in sessions {
            for (field, value) in [
                ("workspace_class", row.workspace_class.clone()),
                ("context_class", row.context_class.clone()),
            ] {
                let Some(value) = value else { continue };
                assert!(
                    !value.contains('/') && !value.contains('=') && !value.contains(' '),
                    "{name}: {field} looks like a path or an argument: {value}"
                );
            }
        }
    }
}

/// The capability the annotation message is gated behind must be pinned on the
/// wire, not just named in Rust: ARO reads the fixture, not this crate.
#[test]
fn the_annotation_capability_is_advertised_by_a_pinned_agreement() {
    let advertised = annotation_vectors()
        .iter()
        .filter_map(|(_, message)| match message {
            BridgeMessage::Agreement(agreement) => Some(agreement.capabilities.clone()),
            _ => None,
        })
        .flatten()
        .any(|capability| {
            capability.name == capability_names::ARO_ANNOTATIONS && capability.available
        });
    assert!(advertised, "no pinned agreement advertises aro_annotations");
    assert!(
        capability_names::ALL.contains(&capability_names::ARO_ANNOTATIONS),
        "the collector implements the annotation arm, so the name it enumerates must include it"
    );
}
