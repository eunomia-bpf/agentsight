use anyhow::{Context, Result, bail};
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::session::SessionRecord;

pub const CHROME_TRACE_FORMAT: &str = "chrome-trace-event-json";
const AGENTSIGHT_OPERATION_SCHEMA: &str = "agentsight.operation.v1";

struct OperationTraceRecord {
    fields: Map<String, Value>,
    value: u64,
    ts_ms: Option<i64>,
    pid: i64,
    tid: i64,
}

pub fn write_chrome_trace(
    path: &Path,
    sessions: &[SessionRecord],
    project_name: &str,
    include_previews: bool,
) -> Result<usize> {
    let payload = chrome_payload_from_sessions(sessions, project_name, include_previews);
    let events = payload
        .get("traceEvents")
        .and_then(Value::as_array)
        .map(Vec::len)
        .unwrap_or(0);
    if events == 0 {
        bail!("agent sessions produced zero Chrome trace events");
    }
    if let Some(parent) = path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create trace dir {}", parent.display()))?;
    }
    fs::write(path, serde_json::to_string_pretty(&payload)? + "\n")
        .with_context(|| format!("failed to write standard trace {}", path.display()))?;
    Ok(events)
}

pub fn chrome_payload_from_sessions(
    sessions: &[SessionRecord],
    project_name: &str,
    include_previews: bool,
) -> Value {
    let records = collect_operation_records(sessions, project_name, include_previews);
    let base_ms = records.iter().filter_map(|record| record.ts_ms).min();
    let events = records
        .iter()
        .enumerate()
        .map(|(idx, record)| {
            json!({
                "name": event_name(&record.fields),
                "cat": string_field(&record.fields, "op").unwrap_or_else(|| "operation".to_string()),
                "ph": "X",
                "ts": trace_timestamp_us(record.ts_ms, base_ms, idx),
                "dur": 1,
                "pid": record.pid,
                "tid": record.tid,
                "args": {
                    "agentsight.schema": AGENTSIGHT_OPERATION_SCHEMA,
                    "agentsight.value": record.value.max(1),
                    "agentsight.operation": record.fields,
                }
            })
        })
        .collect::<Vec<_>>();

    json!({
        "displayTimeUnit": "ms",
        "metadata": {
            "format": CHROME_TRACE_FORMAT,
            "source_schema": agent_session::AGENT_TRACE_SCHEMA,
            "operation_schema": AGENTSIGHT_OPERATION_SCHEMA,
            "project": project_name,
        },
        "traceEvents": events,
    })
}

pub fn operation_records_from_chrome_trace_files(
    paths: &[PathBuf],
    project_name: &str,
    include_args: bool,
) -> Result<Vec<Value>> {
    let mut rows = Vec::new();
    for path in paths {
        let contents = fs::read_to_string(path)
            .with_context(|| format!("failed to read --standard-trace-file {}", path.display()))?;
        let payload: Value = serde_json::from_str(&contents)
            .with_context(|| format!("invalid standard trace {}", path.display()))?;
        rows.extend(
            operation_records_from_chrome_trace_payload(&payload, project_name, include_args)
                .with_context(|| format!("invalid standard trace {}", path.display()))?,
        );
    }
    if rows.is_empty() {
        bail!("standard trace input produced no operations");
    }
    Ok(rows)
}

pub fn operation_records_from_chrome_trace_payload(
    payload: &Value,
    project_name: &str,
    include_args: bool,
) -> Result<Vec<Value>> {
    let raw_events = chrome_trace_events(payload)?;
    let completed = complete_events_in_trace_order(raw_events);
    Ok(completed
        .iter()
        .filter_map(|event| operation_record_from_chrome_event(event, project_name, include_args))
        .collect())
}

fn collect_operation_records(
    sessions: &[SessionRecord],
    project_name: &str,
    include_previews: bool,
) -> Vec<OperationTraceRecord> {
    let mut records = Vec::new();
    for session in sessions {
        let pid = stable_int(&session.session_id);
        for (prompt_ordinal, prompt) in session.user_requests.iter().enumerate() {
            let mut fields = base_fields(session, project_name, prompt_ordinal, include_previews);
            insert(&mut fields, "op", "prompt");
            insert(&mut fields, "phase", "prompt");
            insert(&mut fields, "status", "observed");
            insert(&mut fields, "prompt_hash", &prompt.text_hash);
            records.push(OperationTraceRecord {
                fields: clean_fields(fields),
                value: 1,
                ts_ms: prompt.ts_ms,
                pid,
                tid: prompt_ordinal as i64,
            });
        }
        for event in &session.tools {
            let mut fields =
                base_fields(session, project_name, event.prompt_index, include_previews);
            insert(&mut fields, "op", "tool");
            insert(&mut fields, "phase", tool_phase(event));
            insert(&mut fields, "tool", &event.tool_name);
            insert(&mut fields, "category", &event.category);
            insert(&mut fields, "command", command_preview(event));
            insert(&mut fields, "cmd", &event.command_name);
            insert(&mut fields, "effect", &event.effect);
            insert(&mut fields, "status", &event.status);
            insert_array(&mut fields, "path", &event.path_groups);
            insert_array(&mut fields, "domain", &event.domains);
            insert_array(&mut fields, "process", &event.process_chain);
            records.push(OperationTraceRecord {
                fields: clean_fields(fields),
                value: 1,
                ts_ms: event.ts_ms,
                pid,
                tid: event.prompt_index as i64,
            });
        }
        for call in &session.llm_calls {
            let mut fields =
                base_fields(session, project_name, call.prompt_index, include_previews);
            insert(&mut fields, "op", "llm");
            insert(&mut fields, "phase", llm_phase(call));
            insert(&mut fields, "call", format!("llm/{}", call.tag));
            insert(&mut fields, "llm", &call.tag);
            insert(&mut fields, "model", last_model_segment(&call.model));
            insert(&mut fields, "status", "observed");
            insert_u64(&mut fields, "input_tokens", call.input_tokens);
            insert_u64(&mut fields, "output_tokens", call.output_tokens);
            insert_u64(&mut fields, "cache_tokens", call.cache_tokens);
            insert_u64(&mut fields, "total_tokens", call.total_tokens);
            if include_previews {
                insert(&mut fields, "llm_preview", &call.preview);
            }
            records.push(OperationTraceRecord {
                fields: clean_fields(fields),
                value: 1,
                ts_ms: call.ts_ms,
                pid,
                tid: call.prompt_index as i64,
            });
        }
    }
    records
}

fn base_fields(
    session: &SessionRecord,
    project_name: &str,
    prompt_index: usize,
    include_previews: bool,
) -> Map<String, Value> {
    let prompt = session
        .user_requests
        .get(prompt_index)
        .or_else(|| session.user_requests.last());
    let mut fields = Map::new();
    insert(&mut fields, "project", project_name);
    insert(&mut fields, "agent", &session.source);
    insert(&mut fields, "session", &session.session_id);
    insert(&mut fields, "session_id", &session.session_id);
    fields.insert("prompt_index".to_string(), json!(prompt_index));
    if let Some(prompt) = prompt {
        insert(&mut fields, "prompt", &prompt.tag);
        insert(&mut fields, "prompt_hash", &prompt.text_hash);
        if include_previews {
            insert(&mut fields, "prompt_preview", &prompt.preview);
        }
    }
    fields
}

fn tool_phase(event: &crate::session::ToolEvent) -> String {
    if !event.effect.is_empty() && event.effect != "process" {
        return event.effect.clone();
    }
    if !event.category.is_empty() && event.category != "tool" {
        return event.category.clone();
    }
    if !event.command_name.is_empty() && event.command_name != "none" {
        return event.command_name.clone();
    }
    event.tool_name.clone()
}

fn command_preview(event: &crate::session::ToolEvent) -> &str {
    if !event.command_name.is_empty() && event.command_name != "none" {
        &event.command_name
    } else {
        ""
    }
}

fn llm_phase(call: &crate::session::LlmEvent) -> String {
    if !call.tag.is_empty() && call.tag != "unmatched" {
        call.tag.clone()
    } else {
        "llm".to_string()
    }
}

fn last_model_segment(model: &str) -> &str {
    model.rsplit('/').next().unwrap_or(model)
}

fn event_name(fields: &Map<String, Value>) -> String {
    let op = string_field(fields, "op").unwrap_or_else(|| "operation".to_string());
    for key in ["phase", "tool", "model", "action", "status"] {
        if let Some(value) = string_field(fields, key)
            && !value.is_empty()
        {
            return format!("{op}:{value}");
        }
    }
    op
}

fn trace_timestamp_us(ts_ms: Option<i64>, base_ms: Option<i64>, index: usize) -> i64 {
    if let (Some(ts_ms), Some(base_ms)) = (ts_ms, base_ms) {
        return ts_ms.saturating_sub(base_ms).max(0) * 1000 + index as i64;
    }
    index as i64 * 1000
}

fn stable_int(value: &str) -> i64 {
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    let digest = hasher.finalize();
    let mut bytes = [0_u8; 8];
    bytes.copy_from_slice(&digest[..8]);
    (u64::from_be_bytes(bytes) % 2_147_483_647) as i64
}

fn chrome_trace_events(payload: &Value) -> Result<Vec<Map<String, Value>>> {
    let events = if let Some(object) = payload.as_object() {
        object.get("traceEvents")
    } else {
        Some(payload)
    };
    let events = events
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow::anyhow!("Chrome trace must be a list or contain traceEvents"))?;
    let mut out = Vec::new();
    for event in events {
        let event = event
            .as_object()
            .ok_or_else(|| anyhow::anyhow!("Chrome trace contains non-object events"))?;
        out.push(event.clone());
    }
    Ok(out)
}

fn complete_events_in_trace_order(events: Vec<Map<String, Value>>) -> Vec<Map<String, Value>> {
    let mut stacks: HashMap<String, Vec<Map<String, Value>>> = HashMap::new();
    let mut completed = Vec::new();
    for event in events {
        let phase = event.get("ph").and_then(Value::as_str).unwrap_or_default();
        if matches!(phase, "X" | "I" | "i") {
            completed.push(event);
            continue;
        }
        let key = trace_event_key(&event);
        if phase == "B" {
            stacks.entry(key).or_default().push(event);
            continue;
        }
        if phase != "E" {
            continue;
        }
        let Some(begin) = stacks.get_mut(&key).and_then(Vec::pop) else {
            continue;
        };
        let begin_ts = parse_i64(begin.get("ts")).unwrap_or(0);
        let end_ts = parse_i64(event.get("ts")).unwrap_or(begin_ts);
        let mut args = object_field(&begin, "args").cloned().unwrap_or_default();
        if let Some(end_args) = object_field(&event, "args") {
            args.extend(end_args.clone());
        }
        let mut complete = Map::new();
        complete.insert(
            "name".to_string(),
            begin
                .get("name")
                .cloned()
                .or_else(|| event.get("name").cloned())
                .unwrap_or_else(|| json!("event")),
        );
        complete.insert(
            "cat".to_string(),
            begin
                .get("cat")
                .cloned()
                .or_else(|| event.get("cat").cloned())
                .unwrap_or_else(|| json!("")),
        );
        complete.insert("ph".to_string(), json!("X"));
        complete.insert("ts".to_string(), json!(begin_ts));
        complete.insert(
            "dur".to_string(),
            json!(end_ts.saturating_sub(begin_ts).max(0)),
        );
        complete.insert(
            "pid".to_string(),
            begin
                .get("pid")
                .cloned()
                .or_else(|| event.get("pid").cloned())
                .unwrap_or_else(|| json!("")),
        );
        complete.insert(
            "tid".to_string(),
            begin
                .get("tid")
                .cloned()
                .or_else(|| event.get("tid").cloned())
                .unwrap_or_else(|| json!("")),
        );
        complete.insert("args".to_string(), Value::Object(args));
        completed.push(complete);
    }
    completed
}

fn trace_event_key(event: &Map<String, Value>) -> String {
    format!(
        "{}\u{1f}{}\u{1f}{}\u{1f}{}",
        value_key(event.get("pid")),
        value_key(event.get("tid")),
        value_key(event.get("name")),
        value_key(event.get("cat"))
    )
}

fn value_key(value: Option<&Value>) -> String {
    value
        .map(|value| match value {
            Value::String(text) => text.clone(),
            _ => value.to_string(),
        })
        .unwrap_or_default()
}

fn operation_record_from_chrome_event(
    event: &Map<String, Value>,
    project_name: &str,
    include_args: bool,
) -> Option<Value> {
    let phase = event.get("ph").and_then(Value::as_str)?;
    if !matches!(phase, "X" | "I" | "i") {
        return None;
    }
    let args = object_field(event, "args").cloned().unwrap_or_default();
    if let Some(operation_fields) = args
        .get("agentsight.operation")
        .and_then(Value::as_object)
        .cloned()
    {
        return Some(json!({
            "value": operation_value(args.get("agentsight.value")),
            "fields": clean_fields(operation_fields),
        }));
    }

    let categories = split_categories(event.get("cat").and_then(Value::as_str));
    let raw_name = string_value(event.get("name")).unwrap_or_else(|| "event".to_string());
    let raw_op = string_value(args.get("op"))
        .or_else(|| string_value(args.get("operation")))
        .or_else(|| categories.first().cloned())
        .unwrap_or_else(|| raw_name.clone());
    let op = normalize_label(&raw_op, "event");
    let raw_phase = string_value(args.get("phase"))
        .or_else(|| categories.get(1).cloned())
        .unwrap_or_else(|| op.clone());
    let session = string_value(args.get("session"))
        .or_else(|| string_value(args.get("session_id")))
        .unwrap_or_else(|| format!("pid:{}", value_key(event.get("pid"))));
    let dur_us = parse_i64(event.get("dur")).unwrap_or(0).max(0);

    let mut fields = Map::new();
    insert(
        &mut fields,
        "project",
        string_value(args.get("project")).unwrap_or_else(|| project_name.to_string()),
    );
    insert(
        &mut fields,
        "agent",
        string_value(args.get("agent")).unwrap_or_else(|| "standard-trace".to_string()),
    );
    insert(&mut fields, "session", &session);
    insert(
        &mut fields,
        "session_id",
        string_value(args.get("session_id")).unwrap_or_else(|| session.clone()),
    );
    insert(&mut fields, "op", op);
    insert(&mut fields, "phase", normalize_label(&raw_phase, "event"));
    insert(
        &mut fields,
        "status",
        string_value(args.get("status")).unwrap_or_else(|| "observed".to_string()),
    );
    insert(&mut fields, "trace_name", raw_name);
    if let Some(cat) = event.get("cat") {
        fields.insert("trace_cat".to_string(), cat.clone());
    }
    if let Some(pid) = event.get("pid") {
        fields.insert("trace_pid".to_string(), pid.clone());
    }
    if let Some(tid) = event.get("tid") {
        fields.insert("trace_tid".to_string(), tid.clone());
    }
    fields.insert(
        "trace_ts_us".to_string(),
        json!(parse_i64(event.get("ts")).unwrap_or(0)),
    );
    fields.insert("trace_dur_us".to_string(), json!(dur_us));
    maybe_copy_trace_args(&mut fields, &args, include_args);
    Some(json!({"value": 1, "fields": clean_fields(fields)}))
}

fn maybe_copy_trace_args(
    fields: &mut Map<String, Value>,
    args: &Map<String, Value>,
    include_args: bool,
) {
    for (key, value) in args {
        if key.starts_with("agentsight.") || fields.contains_key(key) {
            continue;
        }
        if include_args || is_generic_arg_field(key) {
            fields.insert(key.clone(), value.clone());
        }
    }
}

fn is_generic_arg_field(key: &str) -> bool {
    matches!(
        key,
        "action"
            | "agent"
            | "category"
            | "cmd"
            | "command"
            | "dataset"
            | "domain"
            | "effect"
            | "model"
            | "op"
            | "operation"
            | "path"
            | "phase"
            | "process"
            | "project"
            | "session"
            | "session_id"
            | "status"
            | "target"
            | "task"
            | "tool"
    )
}

fn operation_value(value: Option<&Value>) -> u64 {
    parse_u64(value).unwrap_or(1).max(1)
}

fn parse_u64(value: Option<&Value>) -> Option<u64> {
    match value? {
        Value::Number(number) => number.as_u64(),
        Value::String(text) => text.parse().ok(),
        _ => None,
    }
}

fn parse_i64(value: Option<&Value>) -> Option<i64> {
    match value? {
        Value::Number(number) => number.as_i64(),
        Value::String(text) => text.parse().ok(),
        _ => None,
    }
}

fn object_field<'a>(object: &'a Map<String, Value>, key: &str) -> Option<&'a Map<String, Value>> {
    object.get(key).and_then(Value::as_object)
}

fn split_categories(value: Option<&str>) -> Vec<String> {
    value
        .unwrap_or_default()
        .split([',', ';'])
        .map(str::trim)
        .filter(|part| !part.is_empty())
        .map(ToString::to_string)
        .collect()
}

fn normalize_label(value: &str, fallback: &str) -> String {
    let normalized = value.trim().replace(' ', "_");
    if normalized.is_empty() {
        fallback.to_string()
    } else {
        normalized
    }
}

fn insert(fields: &mut Map<String, Value>, key: &str, value: impl Into<String>) {
    let value = value.into();
    if !value.is_empty() {
        fields.insert(key.to_string(), Value::String(value));
    }
}

fn insert_u64(fields: &mut Map<String, Value>, key: &str, value: u64) {
    if value > 0 {
        fields.insert(key.to_string(), json!(value));
    }
}

fn insert_array(fields: &mut Map<String, Value>, key: &str, values: &[String]) {
    let values = values
        .iter()
        .filter(|value| !value.is_empty())
        .cloned()
        .map(Value::String)
        .collect::<Vec<_>>();
    if !values.is_empty() {
        fields.insert(key.to_string(), Value::Array(values));
    }
}

fn clean_fields(fields: Map<String, Value>) -> Map<String, Value> {
    fields
        .into_iter()
        .filter(|(_, value)| match value {
            Value::Null => false,
            Value::String(value) => !value.is_empty(),
            Value::Array(values) => !values.is_empty(),
            Value::Object(values) => !values.is_empty(),
            Value::Bool(_) | Value::Number(_) => true,
        })
        .collect()
}

fn string_field(fields: &Map<String, Value>, key: &str) -> Option<String> {
    string_value(fields.get(key))
}

fn string_value(value: Option<&Value>) -> Option<String> {
    match value? {
        Value::String(value) if !value.is_empty() => Some(value.clone()),
        Value::Number(value) => Some(value.to_string()),
        Value::Bool(value) => Some(value.to_string()),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::session::{LlmEvent, ToolEvent, UserRequest};

    fn sample_session() -> SessionRecord {
        SessionRecord {
            source: "codex".to_string(),
            path: PathBuf::from("session.jsonl"),
            session_id: "s1".to_string(),
            cwd: "repo".to_string(),
            agent_role: "agent".to_string(),
            model: "gpt-test".to_string(),
            title: String::new(),
            start_ts_ms: Some(1000),
            user_requests: vec![UserRequest {
                index: 0,
                ts_ms: Some(1000),
                text_hash: "h1".to_string(),
                preview: "review this change".to_string(),
                tag: "review".to_string(),
            }],
            tools: vec![ToolEvent {
                ts_ms: Some(1010),
                prompt_index: 0,
                tool_name: "bash".to_string(),
                category: "shell".to_string(),
                command: "rg".to_string(),
                command_name: "rg".to_string(),
                effect: "read".to_string(),
                process_chain: vec!["rg".to_string()],
                status: "ok".to_string(),
                path_groups: vec!["docs/design.md".to_string()],
                domains: Vec::new(),
                call_id: None,
            }],
            llm_calls: vec![LlmEvent {
                ts_ms: Some(1020),
                prompt_index: 0,
                model: "openai/gpt-test".to_string(),
                text_hash: "h2".to_string(),
                preview: "looks fine".to_string(),
                input_tokens: 11,
                output_tokens: 7,
                cache_tokens: 0,
                total_tokens: 18,
                tag: "review".to_string(),
            }],
            session_tag: String::new(),
        }
    }

    #[test]
    fn agent_session_exports_and_imports_chrome_operation_trace() {
        let payload = chrome_payload_from_sessions(&[sample_session()], "agentsight", false);
        let events = payload
            .get("traceEvents")
            .and_then(Value::as_array)
            .unwrap();
        let operations =
            operation_records_from_chrome_trace_payload(&payload, "agentsight", false).unwrap();

        assert_eq!(events.len(), 3);
        assert_eq!(operations.len(), 3);
        let fields = operations[1]
            .get("fields")
            .and_then(Value::as_object)
            .unwrap();
        assert_eq!(fields.get("op").and_then(Value::as_str), Some("tool"));
        assert_eq!(fields.get("command").and_then(Value::as_str), Some("rg"));
        assert!(
            !serde_json::to_string(&payload)
                .unwrap()
                .contains("review this change")
        );
    }

    #[test]
    fn generic_begin_end_trace_imports_as_one_operation() {
        let payload = json!({
            "traceEvents": [
                {"name": "tool.exec", "cat": "tool;shell", "ph": "B", "ts": 100, "pid": 3, "tid": 0, "args": {"tool": "bash"}},
                {"name": "tool.exec", "cat": "tool;shell", "ph": "E", "ts": 160, "pid": 3, "tid": 0, "args": {"status": "ok"}}
            ]
        });
        let operations =
            operation_records_from_chrome_trace_payload(&payload, "external-trace", false).unwrap();
        let fields = operations[0]
            .get("fields")
            .and_then(Value::as_object)
            .unwrap();

        assert_eq!(operations.len(), 1);
        assert_eq!(fields.get("op").and_then(Value::as_str), Some("tool"));
        assert_eq!(fields.get("phase").and_then(Value::as_str), Some("shell"));
        assert_eq!(fields.get("tool").and_then(Value::as_str), Some("bash"));
        assert_eq!(fields.get("status").and_then(Value::as_str), Some("ok"));
        assert_eq!(fields.get("trace_dur_us").and_then(Value::as_i64), Some(60));
    }
}
