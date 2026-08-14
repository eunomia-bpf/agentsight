// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Canary suite for the metadata-only projection.
//!
//! Every sensitive field of every capture row is seeded with a unique marker.
//! Under `MetadataOnly` no marker may appear anywhere in the serialized
//! envelopes; under `ResearchFull` every marker must appear. The second half is
//! what proves the projection — not the test's own construction — is doing the
//! removal.

use agentsight_capture::bridge::{
    MutationEmitterConfig, MutationResult, MutationSink, SequenceAllocator,
};
use agentsight_capture::model::{
    AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow, ResourceSampleRow, SessionRow,
    TokenUsageRow, ToolCallRow,
};
use agentsight_capture::view::MaterializedView;
use agentsight_protocol::bridge::{DisclosureMode, ViewMutationEnvelope};
use serde_json::json;
use std::sync::{Arc, Mutex};

/// The 13 disclosure classes the bridge must never leak in metadata mode.
const CANARIES: [(&str, &str); 13] = [
    ("prompt_text", "CANARYzPROMPTzTEXT"),
    ("response_text", "CANARYzRESPONSEzTEXT"),
    ("api_key", "sk-live-CANARYzAPIzKEY"),
    ("bearer_token", "CANARYzBEARERzTOKEN"),
    ("password", "CANARYzPASSWORDzVALUE"),
    ("raw_command", "CANARYzRAWzCOMMAND"),
    ("raw_argv_item", "CANARYzRAWzARGV"),
    ("home_dir", "canaryzhomezuser"),
    ("repository_path", "canaryzrepozdir"),
    ("url_path", "canaryzurlzpath"),
    ("query_string", "canaryzquerystring"),
    ("auth_header", "CANARYzAUTHzHEADER"),
    ("high_entropy_secret", "CANARYzZQXVJWNTPLMKZ"),
];

fn canary(name: &str) -> &'static str {
    CANARIES
        .iter()
        .find(|(key, _)| *key == name)
        .map(|(_, value)| *value)
        .expect("known canary")
}

#[derive(Clone, Default)]
struct RecordingSink {
    envelopes: Arc<Mutex<Vec<ViewMutationEnvelope>>>,
}

impl MutationSink for RecordingSink {
    fn mutation(&mut self, m: &ViewMutationEnvelope) -> MutationResult<()> {
        self.envelopes.lock().unwrap().push(m.clone());
        Ok(())
    }
}

fn session_row() -> SessionRow {
    SessionRow {
        id: "local:claude:session-canary".to_string(),
        agent_type: "claude".to_string(),
        start_timestamp_ms: 1_000,
        end_timestamp_ms: Some(2_000),
        status: "observed".to_string(),
        model: Some("claude-sonnet-4".to_string()),
        input_tokens: 10,
        output_tokens: 5,
        total_tokens: 15,
        view_source: "agent_native_session".to_string(),
        confidence: Some(0.9),
        attributes: json!({ "cwd": format!("/Users/{}/work", canary("home_dir")) }),
    }
}

fn llm_call_row() -> LlmCallRow {
    LlmCallRow {
        id: "llm-canary".to_string(),
        session_id: Some("local:claude:session-canary".to_string()),
        conversation_id: None,
        start_timestamp_ms: 1_100,
        end_timestamp_ms: Some(1_400),
        pid: Some(42),
        comm: Some("claude".to_string()),
        provider: Some("anthropic".to_string()),
        model: Some("claude-sonnet-4".to_string()),
        call_kind: Some("messages".to_string()),
        status: "complete".to_string(),
        error_type: None,
        finish_reason: Some("end_turn".to_string()),
        host: Some("api.anthropic.com".to_string()),
        path: Some(format!(
            "/v1/{}?x={}",
            canary("url_path"),
            canary("query_string")
        )),
        status_code: Some(200),
        input_tokens: 10,
        output_tokens: 5,
        total_tokens: 15,
        request: json!({
            "messages": [{ "role": "user", "content": canary("prompt_text") }],
            "api_key": canary("api_key"),
        }),
        response: json!({ "content": [{ "text": canary("response_text") }] }),
    }
}

fn token_usage_row() -> TokenUsageRow {
    TokenUsageRow {
        id: "token-canary".to_string(),
        llm_call_id: "llm-canary".to_string(),
        timestamp_ms: 1_400,
        pid: Some(42),
        comm: Some("claude".to_string()),
        provider: Some("anthropic".to_string()),
        model: Some("claude-sonnet-4".to_string()),
        input_tokens: 10,
        output_tokens: 5,
        cache_creation_tokens: 0,
        cache_read_tokens: 0,
        total_tokens: 15,
        source: "response_usage".to_string(),
        view_source: "materialized_view".to_string(),
        confidence: Some(1.0),
    }
}

fn tool_call_row() -> ToolCallRow {
    ToolCallRow {
        id: "tool-canary".to_string(),
        session_id: Some("local:claude:session-canary".to_string()),
        conversation_id: None,
        timestamp_ms: 1_500,
        tool_name: Some("Bash".to_string()),
        tool_call_id: Some("toolu_canary".to_string()),
        start_timestamp_ms: Some(1_500),
        end_timestamp_ms: Some(1_600),
        duration_ms: Some(100),
        status: Some("success".to_string()),
        input: json!({ "command": format!("login --password {}", canary("password")) }),
        output: json!({ "stdout": canary("high_entropy_secret") }),
        related_pid: Some(43),
        related_event_id: None,
        view_source: "agent_native_session".to_string(),
        confidence: Some(0.9),
    }
}

fn process_node_row() -> ProcessNodeRow {
    ProcessNodeRow {
        id: "pid:43:start:1500".to_string(),
        pid: 43,
        ppid: Some(42),
        root_pid: Some(42),
        start_timestamp_ms: Some(1_500),
        end_timestamp_ms: None,
        comm: Some("bash".to_string()),
        // The canary lives in the directory portion: the basename itself is
        // metadata the spec allows through.
        command: Some(format!("/opt/{}/agent-runner", canary("raw_command"))),
        argv: vec![
            "bash".to_string(),
            "-c".to_string(),
            canary("raw_argv_item").to_string(),
        ],
        cwd: Some(format!("/Users/dev/{}", canary("repository_path"))),
        exit_code: None,
        status: Some("running".to_string()),
        view_source: "process".to_string(),
        confidence: Some(1.0),
    }
}

fn audit_event_row() -> AuditEventRow {
    AuditEventRow {
        id: "audit-canary".to_string(),
        timestamp_ms: 1_550,
        audit_type: "file".to_string(),
        pid: Some(43),
        comm: Some("bash".to_string()),
        subject: Some(canary("raw_command").to_string()),
        action: Some("write".to_string()),
        target: Some(format!("/Users/dev/{}/notes.rs", canary("repository_path"))),
        status: Some("observed".to_string()),
        summary: Some(format!("wrote {}", canary("repository_path"))),
        details: json!({
            "bytes": 128,
            "headers": { "authorization": format!("Bearer {}", canary("auth_header")) },
            "token": canary("bearer_token"),
        }),
    }
}

fn network_target_row() -> NetworkTargetRow {
    NetworkTargetRow {
        pid: Some(42),
        comm: Some("claude".to_string()),
        host: "api.anthropic.com".to_string(),
        path: Some(format!(
            "/v1/{}?token={}",
            canary("url_path"),
            canary("query_string")
        )),
        count: 3,
        error_count: 0,
        first_timestamp_ms: Some(1_100),
        last_timestamp_ms: Some(1_400),
    }
}

fn resource_sample_row() -> ResourceSampleRow {
    ResourceSampleRow {
        timestamp_ms: 1_600,
        pid: Some(42),
        comm: Some("claude".to_string()),
        cpu_percent: Some(12.5),
        rss_mb: Some(256),
    }
}

/// Drive one full row of every kind through a view configured with the given
/// disclosure and return the serialized envelopes as (json, cbor_hex).
fn envelopes_for(disclosure: DisclosureMode) -> Vec<(String, String)> {
    let sink = RecordingSink::default();
    let mut view = MaterializedView::new();
    view.configure_mutations(MutationEmitterConfig {
        node_id: "node_canary".to_string(),
        boot_id: None,
        source_component: "agentsight-capture".to_string(),
        source_version: "1.0.20".to_string(),
        disclosure,
        sequence: SequenceAllocator::new(),
    });
    view.add_mutation_sink(Box::new(sink.clone()));

    view.emit_session(session_row()).unwrap();
    view.emit_llm_call(llm_call_row()).unwrap();
    view.emit_token_usage(token_usage_row()).unwrap();
    view.emit_tool_call(tool_call_row()).unwrap();
    view.emit_process_node(process_node_row()).unwrap();
    view.emit_audit_event(audit_event_row()).unwrap();
    view.emit_network_target(network_target_row()).unwrap();
    view.emit_resource_sample(resource_sample_row()).unwrap();

    let envelopes = sink.envelopes.lock().unwrap().clone();
    assert_eq!(envelopes.len(), 8, "every row kind must produce a mutation");
    envelopes
        .iter()
        .map(|envelope| {
            let message = agentsight_protocol::bridge::BridgeMessage::Mutation(envelope.clone());
            let cbor = agentsight_protocol::bridge::encode_body(&message).expect("encode");
            (
                serde_json::to_string(&message).expect("json"),
                String::from_utf8_lossy(&cbor).into_owned(),
            )
        })
        .collect()
}

#[test]
fn metadata_only_envelopes_contain_no_canary() {
    let serialized = envelopes_for(DisclosureMode::MetadataOnly);
    for (name, value) in CANARIES {
        for (index, (json, cbor)) in serialized.iter().enumerate() {
            assert!(
                !json.contains(value),
                "canary {name} leaked into metadata-only envelope {index}: {json}"
            );
            assert!(
                !cbor.contains(value),
                "canary {name} leaked into metadata-only CBOR body {index}"
            );
        }
    }
}

#[test]
fn research_full_envelopes_contain_every_canary() {
    let serialized = envelopes_for(DisclosureMode::ResearchFull);
    let combined = serialized
        .iter()
        .map(|(json, _)| json.as_str())
        .collect::<Vec<_>>()
        .join("\n");
    for (name, value) in CANARIES {
        assert!(
            combined.contains(value),
            "canary {name} was not present under ResearchFull, so the \
             metadata-only assertion proves nothing"
        );
    }
}

#[test]
fn incident_scope_releases_only_the_allowlisted_field() {
    let serialized = envelopes_for(DisclosureMode::IncidentScoped {
        approval_id: "approval-canary".to_string(),
        field_allowlist: vec!["cwd".to_string()],
        expires_at_ms: 9_999,
    });
    let combined = serialized
        .iter()
        .map(|(json, _)| json.as_str())
        .collect::<Vec<_>>()
        .join("\n");

    // `cwd` is allowlisted, so the home and repository markers are released.
    assert!(combined.contains(canary("home_dir")));
    assert!(combined.contains(canary("repository_path")));
    // Nothing else is.
    for (name, value) in CANARIES {
        if matches!(name, "home_dir" | "repository_path") {
            continue;
        }
        assert!(
            !combined.contains(value),
            "canary {name} leaked under an allowlist that did not cover it"
        );
    }
}

#[test]
fn metadata_only_still_carries_the_derived_classes() {
    let sink = RecordingSink::default();
    let mut view = MaterializedView::new();
    view.add_mutation_sink(Box::new(sink.clone()));
    view.emit_process_node(process_node_row()).unwrap();
    view.emit_audit_event(audit_event_row()).unwrap();
    view.emit_network_target(network_target_row()).unwrap();

    let envelopes = sink.envelopes.lock().unwrap().clone();
    let json = serde_json::to_string(&envelopes).unwrap();
    // Redaction must not degenerate into emitting nothing useful.
    assert!(json.contains("\"cwd_class\":\"repo\""), "{json}");
    assert!(json.contains("\"path_class\":\"repo\""), "{json}");
    assert!(json.contains("\"extension\":\"rs\""), "{json}");
    assert!(
        json.contains("\"destination_class\":\"model_provider:anthropic\""),
        "{json}"
    );
    assert!(
        json.contains("\"argv_shape\":\"cmd <flag> <arg>\""),
        "{json}"
    );
}
