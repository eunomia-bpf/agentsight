// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Projection of materialized-view rows onto bridge wire rows.
//!
//! This is the only place where a capture row becomes something the bridge can
//! transmit. Under [`DisclosureMode::MetadataOnly`] the projection is what
//! removes prompts, argv, raw paths, and raw hosts — nothing downstream re-adds
//! them.

use super::metadata;
use crate::model::{
    AGENT_NATIVE_SOURCE, AuditEventRow, LlmCallRow, NetworkTargetRow, ProcessNodeRow,
    ResourceSampleRow, SessionRow, TokenUsageRow, ToolCallRow,
};
use agentsight_protocol::bridge::{
    AuditContent, BridgeAuditEventRow, BridgeLlmCallRow, BridgeNetworkTargetRow,
    BridgeProcessNodeRow, BridgeResourceSampleRow, BridgeSessionRow, BridgeTokenUsageRow,
    BridgeToolCallRow, DisclosureMode, LlmContent, NetworkContent, ProcessContent, SessionContent,
    TimestampBasis, ToolContent,
};
use serde_json::Value;

/// Content field names used with [`DisclosureMode::IncidentScoped`] allowlists.
pub mod content_fields {
    pub const CWD: &str = "cwd";
    pub const HOST: &str = "host";
    pub const PATH: &str = "path";
    pub const REQUEST: &str = "request";
    pub const RESPONSE: &str = "response";
    pub const INPUT: &str = "input";
    pub const OUTPUT: &str = "output";
    pub const COMMAND: &str = "command";
    pub const ARGV: &str = "argv";
    pub const SUBJECT: &str = "subject";
    pub const TARGET: &str = "target";
    pub const SUMMARY: &str = "summary";
    pub const DETAILS: &str = "details";
}

fn field(disclosure: &DisclosureMode, name: &str, value: Option<String>) -> Option<String> {
    if disclosure.allows_content_field(name) {
        value
    } else {
        None
    }
}

fn json_field(disclosure: &DisclosureMode, name: &str, value: &Value) -> Option<Value> {
    if !disclosure.allows_content_field(name) || value.is_null() {
        return None;
    }
    Some(value.clone())
}

fn non_empty(value: Option<&String>) -> Option<String> {
    value
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.to_string())
}

/// Timestamp basis implied by the row's `view_source`.
pub fn basis_for_source(view_source: &str) -> TimestampBasis {
    if view_source == AGENT_NATIVE_SOURCE {
        TimestampBasis::AgentNativeTimestamp
    } else {
        TimestampBasis::EpochMilliseconds
    }
}

/// Stable, content-free row id for a network target. The raw host and path are
/// part of the view's key, so the wire id is a digest of it.
pub fn network_target_row_id(row: &NetworkTargetRow) -> String {
    let digest = metadata::digest_hex(&format!(
        "{}\u{0}{}\u{0}{}",
        row.pid.unwrap_or_default(),
        row.host,
        row.path.as_deref().unwrap_or_default()
    ));
    format!("network:{}:{}", row.pid.unwrap_or_default(), &digest[..16])
}

/// Stable, content-free row id for a resource sample.
pub fn resource_sample_row_id(row: &ResourceSampleRow) -> String {
    format!(
        "resource:{}:{}",
        row.pid.unwrap_or_default(),
        row.timestamp_ms
    )
}

fn session_cwd(row: &SessionRow) -> Option<String> {
    row.attributes
        .get("cwd")
        .and_then(Value::as_str)
        .filter(|cwd| !cwd.is_empty())
        .map(str::to_string)
}

pub fn session(row: &SessionRow, revision: u64, disclosure: &DisclosureMode) -> BridgeSessionRow {
    let cwd = session_cwd(row);
    let content = disclosure.allows_any_content().then(|| SessionContent {
        cwd: field(disclosure, content_fields::CWD, cwd.clone()),
    });
    BridgeSessionRow {
        row_id: row.id.clone(),
        revision,
        agent_type: row.agent_type.clone(),
        start_ts_ms: row.start_timestamp_ms,
        end_ts_ms: row.end_timestamp_ms,
        status: row.status.clone(),
        model: non_empty(row.model.as_ref()),
        input_tokens: row.input_tokens,
        output_tokens: row.output_tokens,
        total_tokens: row.total_tokens,
        view_source: row.view_source.clone(),
        confidence: row.confidence,
        cwd_class: cwd.as_deref().and_then(metadata::cwd_class),
        content,
    }
}

pub fn llm_call(row: &LlmCallRow, revision: u64, disclosure: &DisclosureMode) -> BridgeLlmCallRow {
    let content = disclosure.allows_any_content().then(|| LlmContent {
        host: field(disclosure, content_fields::HOST, row.host.clone()),
        path: field(disclosure, content_fields::PATH, row.path.clone()),
        request: json_field(disclosure, content_fields::REQUEST, &row.request),
        response: json_field(disclosure, content_fields::RESPONSE, &row.response),
    });
    BridgeLlmCallRow {
        row_id: row.id.clone(),
        revision,
        session_row_id: non_empty(row.session_id.as_ref()),
        start_ts_ms: row.start_timestamp_ms,
        end_ts_ms: row.end_timestamp_ms,
        pid: row.pid,
        comm: non_empty(row.comm.as_ref()),
        provider: non_empty(row.provider.as_ref()),
        model: non_empty(row.model.as_ref()),
        call_kind: non_empty(row.call_kind.as_ref()),
        status: row.status.clone(),
        error_type: non_empty(row.error_type.as_ref()),
        finish_reason: non_empty(row.finish_reason.as_ref()),
        status_code: row.status_code,
        input_tokens: row.input_tokens,
        output_tokens: row.output_tokens,
        total_tokens: row.total_tokens,
        destination_class: row
            .host
            .as_deref()
            .and_then(|host| metadata::destination_class(host, row.provider.as_deref())),
        content,
    }
}

pub fn token_usage(row: &TokenUsageRow, revision: u64) -> BridgeTokenUsageRow {
    BridgeTokenUsageRow {
        row_id: row.id.clone(),
        revision,
        llm_call_row_id: (!row.llm_call_id.is_empty()).then(|| row.llm_call_id.clone()),
        ts_ms: row.timestamp_ms,
        pid: row.pid,
        comm: non_empty(row.comm.as_ref()),
        provider: non_empty(row.provider.as_ref()),
        model: non_empty(row.model.as_ref()),
        input_tokens: row.input_tokens,
        output_tokens: row.output_tokens,
        cache_creation_tokens: row.cache_creation_tokens,
        cache_read_tokens: row.cache_read_tokens,
        total_tokens: row.total_tokens,
        source: row.source.clone(),
        view_source: row.view_source.clone(),
        confidence: row.confidence,
    }
}

/// Coarse semantic category for a framework tool name.
pub fn semantic_category(tool_name: Option<&str>) -> Option<String> {
    let name = tool_name?.trim();
    if name.is_empty() {
        return None;
    }
    let lower = name.to_ascii_lowercase();
    let category = match lower.as_str() {
        "read" | "write" | "edit" | "multiedit" | "notebookedit" | "notebookread" => "file",
        "bash" | "bashoutput" | "killshell" | "shell" | "run_shell_command" | "execute_command" => {
            "shell"
        }
        "grep" | "glob" | "ls" | "search_file_content" | "list_directory" => "search",
        "webfetch" | "websearch" | "web_fetch" | "google_web_search" => "network",
        "task" | "agent" => "agent",
        "todowrite" | "exitplanmode" | "plan" => "planning",
        _ => "other",
    };
    Some(category.to_string())
}

pub fn tool_call(
    row: &ToolCallRow,
    revision: u64,
    disclosure: &DisclosureMode,
) -> BridgeToolCallRow {
    let content = disclosure.allows_any_content().then(|| ToolContent {
        input: json_field(disclosure, content_fields::INPUT, &row.input),
        output: json_field(disclosure, content_fields::OUTPUT, &row.output),
    });
    BridgeToolCallRow {
        row_id: row.id.clone(),
        revision,
        session_row_id: non_empty(row.session_id.as_ref()),
        ts_ms: row.timestamp_ms,
        tool_name: non_empty(row.tool_name.as_ref()),
        semantic_category: semantic_category(row.tool_name.as_deref()),
        native_tool_call_id: non_empty(row.tool_call_id.as_ref()),
        start_ts_ms: row.start_timestamp_ms,
        end_ts_ms: row.end_timestamp_ms,
        duration_ms: row.duration_ms,
        status: non_empty(row.status.as_ref()),
        related_pid: row.related_pid,
        view_source: row.view_source.clone(),
        confidence: row.confidence,
        content,
    }
}

pub fn process_node(
    row: &ProcessNodeRow,
    revision: u64,
    disclosure: &DisclosureMode,
) -> BridgeProcessNodeRow {
    let basename = row
        .command
        .as_deref()
        .and_then(metadata::executable_basename)
        .or_else(|| {
            row.argv
                .first()
                .map(String::as_str)
                .and_then(metadata::executable_basename)
        });
    let shape = metadata::argv_shape(&row.argv);
    let content = disclosure.allows_any_content().then(|| ProcessContent {
        command: field(disclosure, content_fields::COMMAND, row.command.clone()),
        argv: if disclosure.allows_content_field(content_fields::ARGV) {
            row.argv.clone()
        } else {
            Vec::new()
        },
        cwd: field(disclosure, content_fields::CWD, row.cwd.clone()),
    });
    BridgeProcessNodeRow {
        row_id: row.id.clone(),
        revision,
        pid: row.pid,
        // Carried straight through from the view row, which took it from
        // /proc/<pid>/stat at event arrival. None off Linux and when the read
        // lost the race with process exit; never derived from a timestamp.
        start_ticks: row.start_ticks,
        ppid: row.ppid,
        root_pid: row.root_pid,
        start_ts_ms: row.start_timestamp_ms,
        end_ts_ms: row.end_timestamp_ms,
        comm: non_empty(row.comm.as_ref()),
        command_fingerprint: metadata::command_fingerprint(basename.as_deref(), shape.as_deref()),
        executable_basename: basename,
        argv_shape: shape,
        cwd_class: row.cwd.as_deref().and_then(metadata::cwd_class),
        exit_code: row.exit_code,
        status: non_empty(row.status.as_ref()),
        view_source: row.view_source.clone(),
        confidence: row.confidence,
        content,
    }
}

fn audit_bytes_or_count(row: &AuditEventRow) -> Option<i64> {
    ["bytes", "size", "count", "len", "length"]
        .iter()
        .find_map(|key| row.details.get(*key).and_then(Value::as_i64))
}

pub fn audit_event(row: &AuditEventRow, disclosure: &DisclosureMode) -> BridgeAuditEventRow {
    let target = row.target.as_deref().filter(|target| !target.is_empty());
    let is_network = row.audit_type == "network" || row.audit_type == "llm";
    let content = disclosure.allows_any_content().then(|| AuditContent {
        subject: field(disclosure, content_fields::SUBJECT, row.subject.clone()),
        target: field(disclosure, content_fields::TARGET, row.target.clone()),
        summary: field(disclosure, content_fields::SUMMARY, row.summary.clone()),
        details: json_field(disclosure, content_fields::DETAILS, &row.details),
    });
    BridgeAuditEventRow {
        row_id: row.id.clone(),
        ts_ms: row.timestamp_ms,
        audit_type: row.audit_type.clone(),
        pid: row.pid,
        comm: non_empty(row.comm.as_ref()),
        action: non_empty(row.action.as_ref()),
        path_class: (!is_network)
            .then(|| target.and_then(metadata::path_class))
            .flatten(),
        extension: (!is_network)
            .then(|| target.and_then(metadata::extension))
            .flatten(),
        destination_class: is_network
            .then(|| target.and_then(|target| metadata::destination_class(target, None)))
            .flatten(),
        port: is_network
            .then(|| target.and_then(metadata::destination_port))
            .flatten(),
        protocol: is_network
            .then(|| {
                target
                    .and_then(|target| target.split_once("://"))
                    .map(|(scheme, _)| scheme.to_ascii_lowercase())
            })
            .flatten(),
        bytes_or_count: audit_bytes_or_count(row),
        status: non_empty(row.status.as_ref()),
        raw_target_digest: target.map(metadata::digest_hex),
        content,
    }
}

pub fn network_target(
    row: &NetworkTargetRow,
    revision: u64,
    disclosure: &DisclosureMode,
) -> BridgeNetworkTargetRow {
    let content = disclosure.allows_any_content().then(|| NetworkContent {
        host: field(disclosure, content_fields::HOST, Some(row.host.clone())),
        path: field(disclosure, content_fields::PATH, row.path.clone()),
    });
    BridgeNetworkTargetRow {
        row_id: network_target_row_id(row),
        revision,
        pid: row.pid,
        comm: non_empty(row.comm.as_ref()),
        destination_class: metadata::destination_class(&row.host, None)
            .unwrap_or_else(|| "other".to_string()),
        port: metadata::destination_port(&row.host),
        count: row.count,
        error_count: row.error_count,
        first_ts_ms: row.first_timestamp_ms,
        last_ts_ms: row.last_timestamp_ms,
        raw_target_digest: Some(metadata::digest_hex(&format!(
            "{}{}",
            row.host,
            row.path.as_deref().unwrap_or_default()
        ))),
        content,
    }
}

pub fn resource_sample(row: &ResourceSampleRow) -> BridgeResourceSampleRow {
    BridgeResourceSampleRow {
        ts_ms: row.timestamp_ms,
        pid: row.pid,
        comm: non_empty(row.comm.as_ref()),
        cpu_percent: row.cpu_percent,
        rss_mb: row.rss_mb,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn process_row() -> ProcessNodeRow {
        ProcessNodeRow {
            id: "pid:42:start:100".to_string(),
            pid: 42,
            start_ticks: Some(918_500),
            ppid: Some(1),
            root_pid: Some(42),
            start_timestamp_ms: Some(100),
            end_timestamp_ms: None,
            comm: Some("git".to_string()),
            command: Some("/usr/bin/git".to_string()),
            argv: vec!["git".to_string(), "--no-pager".to_string()],
            cwd: Some("/Users/dev/project".to_string()),
            exit_code: None,
            status: Some("running".to_string()),
            view_source: "process".to_string(),
            confidence: Some(1.0),
        }
    }

    #[test]
    fn metadata_only_process_projection_drops_content() {
        let projected = process_node(&process_row(), 0, &DisclosureMode::MetadataOnly);
        assert!(projected.content.is_none());
        // The kernel ticks the runner read at arrival, carried through unchanged.
        assert_eq!(projected.start_ticks, Some(918_500));
        assert_eq!(projected.executable_basename.as_deref(), Some("git"));
        assert_eq!(projected.argv_shape.as_deref(), Some("cmd <flag>"));
        assert_eq!(projected.cwd_class.as_deref(), Some("repo"));
        assert!(projected.command_fingerprint.is_some());
    }

    #[test]
    fn research_full_process_projection_keeps_content() {
        let projected = process_node(&process_row(), 0, &DisclosureMode::ResearchFull);
        let content = projected.content.expect("content");
        assert_eq!(content.command.as_deref(), Some("/usr/bin/git"));
        assert_eq!(content.argv.len(), 2);
        assert_eq!(content.cwd.as_deref(), Some("/Users/dev/project"));
    }

    #[test]
    fn incident_scope_populates_only_allowlisted_fields() {
        let disclosure = DisclosureMode::IncidentScoped {
            approval_id: "ap-1".to_string(),
            field_allowlist: vec![content_fields::CWD.to_string()],
            expires_at_ms: 0,
        };
        let projected = process_node(&process_row(), 0, &disclosure);
        let content = projected.content.expect("content");
        assert_eq!(content.cwd.as_deref(), Some("/Users/dev/project"));
        assert_eq!(content.command, None);
        assert!(content.argv.is_empty());
    }

    #[test]
    fn network_row_id_and_class_hide_the_raw_host() {
        let row = NetworkTargetRow {
            pid: Some(7),
            comm: Some("node".to_string()),
            host: "secret-internal.example.com".to_string(),
            path: Some("/private/path?token=abc".to_string()),
            count: 3,
            error_count: 0,
            first_timestamp_ms: Some(1),
            last_timestamp_ms: Some(2),
        };
        let projected = network_target(&row, 0, &DisclosureMode::MetadataOnly);
        assert!(!projected.row_id.contains("secret-internal"));
        assert_eq!(projected.destination_class, "public:example.com");
        assert_eq!(projected.raw_target_digest.as_ref().unwrap().len(), 64);
        assert!(projected.content.is_none());
    }

    #[test]
    fn file_audit_rows_carry_class_not_path() {
        let row = AuditEventRow {
            id: "audit-1".to_string(),
            timestamp_ms: 5,
            audit_type: "file".to_string(),
            pid: Some(9),
            comm: Some("node".to_string()),
            subject: Some("node".to_string()),
            action: Some("write".to_string()),
            target: Some("/Users/dev/project/src/secret_notes.rs".to_string()),
            status: Some("observed".to_string()),
            summary: Some("wrote file".to_string()),
            details: json!({ "bytes": 128 }),
        };
        let projected = audit_event(&row, &DisclosureMode::MetadataOnly);
        assert_eq!(projected.path_class.as_deref(), Some("repo"));
        assert_eq!(projected.extension.as_deref(), Some("rs"));
        assert_eq!(projected.bytes_or_count, Some(128));
        assert_eq!(projected.destination_class, None);
        assert!(projected.content.is_none());
    }

    #[test]
    fn semantic_categories_cover_the_common_tools() {
        assert_eq!(semantic_category(Some("Bash")).as_deref(), Some("shell"));
        assert_eq!(semantic_category(Some("Read")).as_deref(), Some("file"));
        assert_eq!(semantic_category(Some("Zzz")).as_deref(), Some("other"));
        assert_eq!(semantic_category(None), None);
    }
}
