// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Equal-budget Raw/Trajectory query broker for the frozen RQ1 preflight.

use crate::research::{
    AnyError, StoreData, action_effects, artifact_history, load_store, session_diff,
    verify_artifact_projection,
};
use clap::{Parser, ValueEnum};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::ffi::OsString;
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

const PINNED_MODEL_SHA256: &str =
    "f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9";

#[derive(Clone, Copy, Debug, Serialize, ValueEnum)]
#[serde(rename_all = "snake_case")]
enum Condition {
    Generic,
    Raw,
    Trajectory,
}

#[derive(Debug, Default, Serialize)]
struct ToolEngagement {
    current_workspace_tool_calls: usize,
    raw_history_tool_calls: usize,
    trajectory_relation_tool_calls: usize,
}

impl ToolEngagement {
    fn record_success(&mut self, name: &str, exposed_registered_source: bool) {
        if !exposed_registered_source {
            return;
        }
        match name {
            "list_current" | "search_current" | "read_current" => {
                self.current_workspace_tool_calls += 1;
            }
            "list_sources" | "search" | "read_record" | "read_range" => {
                self.raw_history_tool_calls += 1;
            }
            "artifact_history" | "session_diff" | "effects" => {
                self.trajectory_relation_tool_calls += 1;
            }
            _ => {}
        }
    }
}

fn validate_tool_engagement(
    condition: Condition,
    engagement: &ToolEngagement,
) -> Result<(), AnyError> {
    let valid = match condition {
        Condition::Generic => engagement.current_workspace_tool_calls > 0,
        Condition::Raw => engagement.raw_history_tool_calls > 0,
        Condition::Trajectory => engagement.trajectory_relation_tool_calls > 0,
    };
    if valid {
        Ok(())
    } else {
        Err(format!(
            "{condition:?} supervisor did not engage its required evidence interface: current={}, raw_history={}, trajectory_relation={}",
            engagement.current_workspace_tool_calls,
            engagement.raw_history_tool_calls,
            engagement.trajectory_relation_tool_calls,
        )
        .into())
    }
}

#[derive(Debug, Parser)]
struct SupervisorArgs {
    #[arg(long)]
    store: PathBuf,
    #[arg(long, value_enum)]
    condition: Condition,
    #[arg(long)]
    base_url: String,
    #[arg(long)]
    model: PathBuf,
    /// SHA-256 computed once by the trusted experiment driver and shared by conditions.
    #[arg(long)]
    model_sha256: Option<String>,
    #[arg(long)]
    seed: u64,
    #[arg(long)]
    context_tokens: usize,
    #[arg(long)]
    reserve_output_tokens: usize,
    #[arg(long)]
    evidence_tokens: usize,
    #[arg(long)]
    evidence_bytes: usize,
    #[arg(long)]
    response_tokens: usize,
    #[arg(long)]
    response_bytes: usize,
    #[arg(long)]
    max_tool_calls: usize,
    #[arg(long)]
    timeout_seconds: u64,
    #[arg(long)]
    output: PathBuf,
    /// Validate the complete broker/store contract without contacting a model server.
    #[arg(long)]
    verify_only: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Intervention {
    pub decision: String,
    pub message: String,
    pub source_ids: Vec<String>,
}

#[derive(Debug, Serialize)]
struct Ledger {
    condition: Condition,
    source_store_sha256: String,
    raw_ids_sha256: String,
    model_sha256: String,
    rendered_request_tokens: Vec<usize>,
    server_prompt_tokens: Vec<usize>,
    tool_calls: usize,
    current_workspace_tool_calls: usize,
    raw_history_tool_calls: usize,
    trajectory_relation_tool_calls: usize,
    tool_response_tokens: usize,
    tool_response_bytes: usize,
    exposed_source_ids: Vec<String>,
    elapsed_ms: u128,
    completed: bool,
}

struct Broker {
    args: SupervisorArgs,
    store: StoreData,
    http: ureq::Agent,
    native_base: String,
    messages: Vec<Value>,
    tools: Vec<Value>,
    transcript: Vec<Value>,
    rendered_request_tokens: Vec<usize>,
    server_prompt_tokens: Vec<usize>,
    tool_calls: usize,
    tool_engagement: ToolEngagement,
    evidence_tokens: usize,
    evidence_bytes: usize,
    exposed_source_ids: BTreeSet<String>,
    started: Instant,
}

pub fn run_research_supervisor_from_args(
    args: impl IntoIterator<Item = OsString>,
) -> Result<(), AnyError> {
    let args = SupervisorArgs::parse_from(
        std::iter::once(OsString::from("research-supervisor")).chain(args),
    );
    validate_frozen_args(&args)?;
    if args.output.exists() {
        return Err(format!("output already exists: {}", args.output.display()).into());
    }
    let model_sha256 = if let Some(value) = args.model_sha256.clone() {
        value
    } else {
        sha256_file(&args.model)?
    };
    if model_sha256 != PINNED_MODEL_SHA256 {
        return Err(format!(
            "model SHA-256 mismatch: expected {PINNED_MODEL_SHA256}, got {model_sha256}"
        )
        .into());
    }
    let store = load_store(&args.store)?;
    verify_artifact_projection(&store)?;
    fs::create_dir_all(&args.output)?;
    if args.verify_only {
        return verify_broker_configuration(args, store, model_sha256);
    }
    let timeout = Duration::from_secs(args.timeout_seconds);
    let http = ureq::AgentBuilder::new()
        .timeout_connect(Duration::from_secs(10))
        .timeout_read(timeout)
        .timeout_write(timeout)
        .build();
    let native_base = args
        .base_url
        .trim_end_matches('/')
        .strip_suffix("/v1")
        .unwrap_or(args.base_url.trim_end_matches('/'))
        .to_string();
    let tools = tool_schemas(args.condition);
    let messages = initial_messages(&store);
    let mut broker = Broker {
        args,
        store,
        http,
        native_base,
        messages,
        tools,
        transcript: Vec::new(),
        rendered_request_tokens: Vec::new(),
        server_prompt_tokens: Vec::new(),
        tool_calls: 0,
        tool_engagement: ToolEngagement::default(),
        evidence_tokens: 0,
        evidence_bytes: 0,
        exposed_source_ids: BTreeSet::new(),
        started: Instant::now(),
    };
    let intervention = broker.run()?;
    validate_tool_engagement(broker.args.condition, &broker.tool_engagement)?;
    validate_intervention(&intervention, &broker.store, &broker.exposed_source_ids)?;
    atomic_write(
        &broker.args.output.join("intervention.json"),
        &serde_json::to_vec_pretty(&intervention)?,
    )?;
    write_jsonl(
        &broker.args.output.join("transcript.jsonl"),
        &broker.transcript,
    )?;
    let ledger = Ledger {
        condition: broker.args.condition,
        source_store_sha256: broker.store.index.source_store_sha256.clone(),
        raw_ids_sha256: broker.store.index.raw_ids_sha256.clone(),
        model_sha256,
        rendered_request_tokens: broker.rendered_request_tokens,
        server_prompt_tokens: broker.server_prompt_tokens,
        tool_calls: broker.tool_calls,
        current_workspace_tool_calls: broker.tool_engagement.current_workspace_tool_calls,
        raw_history_tool_calls: broker.tool_engagement.raw_history_tool_calls,
        trajectory_relation_tool_calls: broker.tool_engagement.trajectory_relation_tool_calls,
        tool_response_tokens: broker.evidence_tokens,
        tool_response_bytes: broker.evidence_bytes,
        exposed_source_ids: broker.exposed_source_ids.into_iter().collect(),
        elapsed_ms: broker.started.elapsed().as_millis(),
        completed: true,
    };
    atomic_write(
        &broker.args.output.join("ledger.json"),
        &serde_json::to_vec_pretty(&ledger)?,
    )?;
    eprintln!(
        "[research-supervisor] {:?}: {} tool calls, {} tokens / {} bytes -> {}",
        broker.args.condition,
        ledger.tool_calls,
        ledger.tool_response_tokens,
        ledger.tool_response_bytes,
        broker.args.output.display()
    );
    Ok(())
}

fn verify_broker_configuration(
    args: SupervisorArgs,
    store: StoreData,
    model_sha256: String,
) -> Result<(), AnyError> {
    let condition = args.condition;
    let output = args.output.clone();
    let tools = tool_schemas(condition);
    let messages = initial_messages(&store);
    let native_base = args
        .base_url
        .trim_end_matches('/')
        .strip_suffix("/v1")
        .unwrap_or(args.base_url.trim_end_matches('/'))
        .to_string();
    let broker = Broker {
        args,
        store,
        http: ureq::AgentBuilder::new().build(),
        native_base,
        messages: messages.clone(),
        tools: tools.clone(),
        transcript: Vec::new(),
        rendered_request_tokens: Vec::new(),
        server_prompt_tokens: Vec::new(),
        tool_calls: 0,
        tool_engagement: ToolEngagement::default(),
        evidence_tokens: 0,
        evidence_bytes: 0,
        exposed_source_ids: BTreeSet::new(),
        started: Instant::now(),
    };
    let mut requests = vec![
        ("list_current", json!({})),
        ("search_current", json!({"query": "state", "k": 2})),
    ];
    if let Some(record) = broker.store.records.iter().find(|record| {
        record.source_type == "snapshot_file"
            && broker
                .current_scope()
                .is_some_and(|scope| record.scope_id == scope)
    }) {
        requests.push((
            "read_current",
            json!({"path": snapshot_record_path(&record.source_path)}),
        ));
    }
    if !matches!(condition, Condition::Generic) {
        requests.push(("list_sources", json!({})));
        requests.push(("search", json!({"query": "state", "k": 2})));
        if let Some(record) = broker.store.records.first() {
            requests.push(("read_record", json!({"raw_id": record.id})));
            requests.push((
                "read_range",
                json!({
                    "scope": record.scope_id,
                    "start_raw_id": record.id,
                    "end_raw_id": record.id,
                }),
            ));
        }
    }
    if matches!(condition, Condition::Trajectory) {
        let first_path = broker
            .store
            .index
            .scopes
            .last()
            .and_then(|scope| broker.store.index.boundaries.get(&scope.id))
            .and_then(|rows| rows.iter().find(|row| row.entry.kind == "file"))
            .map(|row| row.entry.path.clone())
            .ok_or("Trajectory verification requires at least one current file")?;
        let from = broker.store.index.scopes[0].id.clone();
        let to = broker.store.index.scopes[1].id.clone();
        requests.push(("artifact_history", json!({"path": first_path})));
        requests.push((
            "session_diff",
            json!({"from_session": from, "to_session": to}),
        ));
        if let Some(action) = broker.store.actions.first() {
            requests.push(("effects", json!({"action_id": action.id})));
        }
    }
    let mut responses = Vec::new();
    for (name, arguments) in requests {
        let response = broker.execute_tool(name, &arguments);
        if response.get("ok").and_then(Value::as_bool) != Some(true)
            || response.pointer("/result/error").is_some()
        {
            return Err(format!("dry broker request {name} failed: {response}").into());
        }
        responses.push(json!({"tool": name, "arguments": arguments, "response": response}));
    }
    let tool_names = tools
        .iter()
        .filter_map(|tool| tool.pointer("/function/name").and_then(Value::as_str))
        .collect::<Vec<_>>();
    let verification = json!({
        "schema": "agent-nebula-broker-verification-v1",
        "condition": condition,
        "model_sha256": model_sha256,
        "source_store_sha256": broker.store.index.source_store_sha256,
        "raw_ids_sha256": broker.store.index.raw_ids_sha256,
        "messages_sha256": hex::encode(Sha256::digest(serde_json::to_vec(&messages)?)),
        "tool_schema_sha256": hex::encode(Sha256::digest(serde_json::to_vec(&tools)?)),
        "tool_names": tool_names,
        "frozen_args": {
            "seed": broker.args.seed,
            "context_tokens": broker.args.context_tokens,
            "reserve_output_tokens": broker.args.reserve_output_tokens,
            "evidence_tokens": broker.args.evidence_tokens,
            "evidence_bytes": broker.args.evidence_bytes,
            "response_tokens": broker.args.response_tokens,
            "response_bytes": broker.args.response_bytes,
            "max_tool_calls": broker.args.max_tool_calls,
            "timeout_seconds": broker.args.timeout_seconds,
        },
        "dry_responses": responses,
        "model_calls": 0,
    });
    atomic_write(
        &output.join("verification.json"),
        &serde_json::to_vec_pretty(&verification)?,
    )?;
    eprintln!(
        "[research-supervisor] verified {:?}: {} tools, 0 model calls -> {}",
        condition,
        tool_names.len(),
        output.display()
    );
    Ok(())
}

impl Broker {
    fn run(&mut self) -> Result<Intervention, AnyError> {
        loop {
            if self.started.elapsed() > Duration::from_secs(self.args.timeout_seconds) {
                return Err("supervisor wall timeout exceeded".into());
            }
            let request = self.request_body();
            let rendered = self.post_native("/apply-template", &request)?;
            let prompt = rendered["prompt"]
                .as_str()
                .ok_or("llama-server /apply-template omitted prompt")?;
            let prompt_tokens = self.count_tokens(prompt)?;
            if prompt_tokens + self.args.reserve_output_tokens > self.args.context_tokens {
                return Err(format!(
                    "rendered request exceeds context: {prompt_tokens} + {} > {}",
                    self.args.reserve_output_tokens, self.args.context_tokens
                )
                .into());
            }
            self.rendered_request_tokens.push(prompt_tokens);
            let response = self.post_openai("/chat/completions", &request)?;
            let server_tokens = response
                .pointer("/usage/prompt_tokens")
                .and_then(Value::as_u64)
                .ok_or("chat response omitted usage.prompt_tokens")?
                as usize;
            self.server_prompt_tokens.push(server_tokens);
            if server_tokens != prompt_tokens {
                return Err(format!(
                    "token-accounting mismatch: apply-template/tokenize={prompt_tokens}, server={server_tokens}"
                )
                .into());
            }
            self.transcript.push(json!({
                "kind": "model_turn",
                "rendered_prompt_tokens": prompt_tokens,
                "request": request,
                "response": response,
            }));
            let message = response
                .pointer("/choices/0/message")
                .cloned()
                .ok_or("chat response omitted choices[0].message")?;
            let calls = message
                .get("tool_calls")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            if calls.is_empty() {
                let content = message
                    .get("content")
                    .and_then(Value::as_str)
                    .ok_or("final supervisor message omitted JSON content")?;
                let intervention: Intervention = serde_json::from_str(content)?;
                if self.count_tokens(&intervention.message)? > 512 {
                    return Err("supervisor advice exceeds the frozen 512-token cap".into());
                }
                return Ok(intervention);
            }
            self.messages.push(message);
            for call in calls {
                if self.tool_calls >= self.args.max_tool_calls {
                    return Err("supervisor exhausted the frozen tool-call ceiling".into());
                }
                self.tool_calls += 1;
                let call_id = call["id"]
                    .as_str()
                    .ok_or("tool call omitted id")?
                    .to_string();
                let name = call
                    .pointer("/function/name")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                let arguments_text = call
                    .pointer("/function/arguments")
                    .and_then(Value::as_str)
                    .unwrap_or("{}");
                let arguments = serde_json::from_str(arguments_text)
                    .unwrap_or_else(|_| json!({"invalid_arguments": arguments_text}));
                let full = self.execute_tool(name, &arguments);
                let tool_succeeded = full.get("ok").and_then(Value::as_bool) == Some(true)
                    && full.pointer("/result/error").is_none();
                let offset = arguments["offset_bytes"].as_u64().unwrap_or(0) as usize;
                let content = self.page_response(name, full, offset)?;
                let response_tokens = self.count_tokens(&content)?;
                let response_bytes = content.len();
                if response_tokens > self.args.response_tokens
                    || response_bytes > self.args.response_bytes
                    || self.evidence_tokens + response_tokens > self.args.evidence_tokens
                    || self.evidence_bytes + response_bytes > self.args.evidence_bytes
                {
                    return Err("bounded tool response violated the frozen budget".into());
                }
                self.evidence_tokens += response_tokens;
                self.evidence_bytes += response_bytes;
                let exposed_registered_source = self
                    .store
                    .records
                    .iter()
                    .any(|record| content.contains(&record.id));
                for record in &self.store.records {
                    if content.contains(&record.id) {
                        self.exposed_source_ids.insert(record.id.clone());
                    }
                }
                if tool_succeeded {
                    self.tool_engagement
                        .record_success(name, exposed_registered_source);
                }
                self.transcript.push(json!({
                    "kind": "tool_turn",
                    "tool_call_id": call_id,
                    "name": name,
                    "arguments": arguments,
                    "response_tokens": response_tokens,
                    "response_bytes": response_bytes,
                    "content": content,
                }));
                self.messages.push(json!({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                }));
            }
        }
    }

    fn request_body(&self) -> Value {
        json!({
            "model": self.args.model.to_string_lossy(),
            "messages": self.messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "parallel_tool_calls": false,
            "temperature": 0,
            "top_p": 1,
            "seed": self.args.seed,
            "max_tokens": self.args.reserve_output_tokens,
            "chat_template_kwargs": {"enable_thinking": false},
            "response_format": prediction_response_format(
                &self.exposed_source_ids.iter().cloned().collect::<Vec<_>>()
            ),
        })
    }

    fn post_openai(&self, endpoint: &str, body: &Value) -> Result<Value, AnyError> {
        let url = format!("{}{}", self.args.base_url.trim_end_matches('/'), endpoint);
        Ok(self.http.post(&url).send_json(body.clone())?.into_json()?)
    }

    fn post_native(&self, endpoint: &str, body: &Value) -> Result<Value, AnyError> {
        let url = format!("{}{}", self.native_base, endpoint);
        Ok(self.http.post(&url).send_json(body.clone())?.into_json()?)
    }

    fn count_tokens(&self, text: &str) -> Result<usize, AnyError> {
        let value = self.post_native(
            "/tokenize",
            &json!({
                "content": text,
                "add_special": false,
                "parse_special": true,
            }),
        )?;
        value["tokens"]
            .as_array()
            .map(Vec::len)
            .ok_or_else(|| "llama-server /tokenize omitted tokens".into())
    }

    fn execute_tool(&self, name: &str, args: &Value) -> Value {
        match name {
            "list_current" => self.list_current(),
            "search_current" => self.search_current(args),
            "read_current" => self.read_current(args),
            "list_sources" if !matches!(self.args.condition, Condition::Generic) => {
                json!({"ok": true, "scopes": self.store.index.scopes, "source_files": self.store.index.source_files})
            }
            "search" if !matches!(self.args.condition, Condition::Generic) => self.search(args),
            "read_record" if !matches!(self.args.condition, Condition::Generic) => {
                self.read_record(args)
            }
            "read_range" if !matches!(self.args.condition, Condition::Generic) => {
                self.read_range(args)
            }
            "artifact_history" if matches!(self.args.condition, Condition::Trajectory) => {
                let path = args["path"].as_str().unwrap_or("");
                json!({"ok": true, "result": artifact_history(&self.store, path)})
            }
            "session_diff" if matches!(self.args.condition, Condition::Trajectory) => {
                let from = args["from_session"].as_str().unwrap_or("");
                let to = args["to_session"].as_str().unwrap_or("");
                json!({"ok": true, "result": session_diff(&self.store, from, to)})
            }
            "effects" if matches!(self.args.condition, Condition::Trajectory) => {
                let action = args["action_id"].as_str().unwrap_or("");
                json!({"ok": true, "result": action_effects(&self.store, action)})
            }
            _ => json!({"ok": false, "error": format!("unknown or unavailable tool {name}")}),
        }
    }

    fn current_scope(&self) -> Option<&str> {
        self.store
            .index
            .scopes
            .last()
            .map(|scope| scope.id.as_str())
    }

    fn list_current(&self) -> Value {
        let Some(scope) = self.current_scope() else {
            return json!({"ok": false, "error": "source store has no current scope"});
        };
        let files = self
            .store
            .index
            .boundaries
            .get(scope)
            .into_iter()
            .flatten()
            .map(|row| json!({"entry": row.entry, "raw_ids": [row.evidence_id.clone()]}))
            .collect::<Vec<_>>();
        json!({"ok": true, "scope": scope, "files": files})
    }

    fn search_current(&self, args: &Value) -> Value {
        let Some(query) = args["query"].as_str().filter(|value| !value.is_empty()) else {
            return json!({"ok": false, "error": "query must be non-empty"});
        };
        let Some(scope) = self.current_scope() else {
            return json!({"ok": false, "error": "source store has no current scope"});
        };
        let k = args["k"].as_u64().unwrap_or(5).clamp(1, 10) as usize;
        let mut rows = self
            .store
            .records
            .iter()
            .filter(|record| record.scope_id == scope && record.source_type == "snapshot_file")
            .map(|record| (rouge_l_recall(query, &record.payload), record))
            .collect::<Vec<_>>();
        rows.sort_by(|left, right| {
            right
                .0
                .partial_cmp(&left.0)
                .unwrap_or(Ordering::Equal)
                .then_with(|| left.1.id.cmp(&right.1.id))
        });
        json!({
            "ok": true,
            "query": query,
            "matches": rows.into_iter().take(k).map(|(score, record)| json!({
                "raw_id": record.id,
                "path": snapshot_record_path(&record.source_path),
                "rouge_l_recall": score,
                "snippet": first_words(&record.payload, 150),
            })).collect::<Vec<_>>(),
        })
    }

    fn read_current(&self, args: &Value) -> Value {
        let Some(path) = args["path"].as_str().filter(|value| !value.is_empty()) else {
            return json!({"ok": false, "error": "path is required"});
        };
        let Some(scope) = self.current_scope() else {
            return json!({"ok": false, "error": "source store has no current scope"});
        };
        let Some(record) = self.store.records.iter().find(|record| {
            record.scope_id == scope
                && record.source_type == "snapshot_file"
                && snapshot_record_path(&record.source_path) == path
        }) else {
            return json!({"ok": false, "error": format!("unknown current file {path}")});
        };
        json!({"ok": true, "record": record})
    }

    fn search(&self, args: &Value) -> Value {
        let Some(query) = args["query"].as_str().filter(|value| !value.is_empty()) else {
            return json!({"ok": false, "error": "query must be non-empty"});
        };
        let scope = args["scope"].as_str();
        let source_types = args["source_types"]
            .as_array()
            .map(|values| values.iter().filter_map(Value::as_str).collect::<Vec<_>>())
            .unwrap_or_default();
        let k = args["k"].as_u64().unwrap_or(5).clamp(1, 10) as usize;
        let mut scored = self
            .store
            .records
            .iter()
            .filter(|record| scope.is_none_or(|scope| scope == "all" || record.scope_id == scope))
            .filter(|record| {
                source_types.is_empty() || source_types.contains(&record.source_type.as_str())
            })
            .map(|record| (rouge_l_recall(query, &record.payload), record))
            .collect::<Vec<_>>();
        scored.sort_by(|left, right| {
            right
                .0
                .partial_cmp(&left.0)
                .unwrap_or(Ordering::Equal)
                .then_with(|| left.1.id.cmp(&right.1.id))
        });
        let matches = scored
            .into_iter()
            .take(k)
            .map(|(score, record)| {
                json!({
                    "raw_id": record.id,
                    "supporting_action_ids": supporting_action_ids(&self.store.actions, &record.id),
                    "scope_id": record.scope_id,
                    "source_type": record.source_type,
                    "source_path": record.source_path,
                    "rouge_l_recall": score,
                    "snippet": first_words(&record.payload, 150),
                })
            })
            .collect::<Vec<_>>();
        json!({"ok": true, "query": query, "matches": matches})
    }

    fn read_record(&self, args: &Value) -> Value {
        let Some(raw_id) = args["raw_id"].as_str() else {
            return json!({"ok": false, "error": "raw_id is required"});
        };
        let Some(record) = self.store.records.iter().find(|record| record.id == raw_id) else {
            return json!({"ok": false, "error": format!("unknown Raw ID {raw_id}")});
        };
        json!({
            "ok": true,
            "record": record,
            "supporting_action_ids": supporting_action_ids(&self.store.actions, &record.id),
        })
    }

    fn read_range(&self, args: &Value) -> Value {
        let Some(scope) = args["scope"].as_str() else {
            return json!({"ok": false, "error": "scope is required"});
        };
        let Some(start_id) = args["start_raw_id"].as_str() else {
            return json!({"ok": false, "error": "start_raw_id is required"});
        };
        let end_id = args["end_raw_id"].as_str().unwrap_or(start_id);
        let rows = self
            .store
            .records
            .iter()
            .filter(|record| record.scope_id == scope)
            .collect::<Vec<_>>();
        let Some(start) = rows.iter().position(|record| record.id == start_id) else {
            return json!({"ok": false, "error": "start_raw_id is not in scope"});
        };
        let Some(end) = rows.iter().position(|record| record.id == end_id) else {
            return json!({"ok": false, "error": "end_raw_id is not in scope"});
        };
        if start > end {
            return json!({"ok": false, "error": "range is reversed"});
        }
        let terminal = end.min(start + 4);
        let records = rows[start..=terminal]
            .iter()
            .map(|record| {
                json!({
                    "record": record,
                    "supporting_action_ids": supporting_action_ids(&self.store.actions, &record.id),
                })
            })
            .collect::<Vec<_>>();
        json!({
            "ok": true,
            "scope": scope,
            "records": records,
            "next_start_raw_id": (terminal < end).then(|| rows[terminal + 1].id.clone()),
        })
    }

    fn page_response(&self, name: &str, value: Value, offset: usize) -> Result<String, AnyError> {
        let full = serde_json::to_string(&value)?;
        let available_tokens = self
            .args
            .evidence_tokens
            .saturating_sub(self.evidence_tokens)
            .min(self.args.response_tokens);
        let available_bytes = self
            .args
            .evidence_bytes
            .saturating_sub(self.evidence_bytes)
            .min(self.args.response_bytes);
        if available_tokens == 0 || available_bytes == 0 {
            return Err("tool-response budget exhausted".into());
        }
        if offset == 0
            && full.len() <= available_bytes
            && self.count_tokens(&full)? <= available_tokens
        {
            return Ok(full);
        }
        if offset > full.len() || !full.is_char_boundary(offset) {
            return Ok(
                json!({"ok": false, "error": "offset_bytes is not a UTF-8 boundary"}).to_string(),
            );
        }
        let mut low = offset;
        let mut high = full.len();
        let mut best = None;
        while low <= high {
            let mut end = low + (high - low) / 2;
            while end > offset && !full.is_char_boundary(end) {
                end -= 1;
            }
            let next = (end < full.len()).then_some(end);
            let envelope = json!({
                "ok": true,
                "tool": name,
                "result_encoding": "utf8_json_segment",
                "offset_bytes": offset,
                "next_offset_bytes": next,
                "result_bytes": full.len(),
                "segment": &full[offset..end],
            })
            .to_string();
            let fits = envelope.len() <= available_bytes
                && self.count_tokens(&envelope)? <= available_tokens;
            if fits {
                best = Some(envelope);
                if end == full.len() {
                    break;
                }
                low = end + 1;
            } else if end == offset {
                break;
            } else {
                high = end - 1;
            }
        }
        best.ok_or_else(|| "remaining budget cannot hold a pagination envelope".into())
    }
}

fn supporting_action_ids<'a>(actions: &'a [crate::research::Action], raw_id: &str) -> Vec<&'a str> {
    actions
        .iter()
        .filter(|action| {
            action.raw_ids.iter().any(|id| id == raw_id)
                || action
                    .effects
                    .iter()
                    .flat_map(|effect| &effect.evidence_ids)
                    .any(|id| id == raw_id)
        })
        .map(|action| action.id.as_str())
        .collect()
}

fn snapshot_record_path(source_path: &str) -> &str {
    source_path
        .split_once("/tree/")
        .map(|(_, path)| path)
        .unwrap_or(source_path)
}

fn validate_frozen_args(args: &SupervisorArgs) -> Result<(), AnyError> {
    let expected = [
        (args.seed == 20260721, "--seed must be 20260721"),
        (
            args.context_tokens == 65_536,
            "--context-tokens must be 65536",
        ),
        (
            args.reserve_output_tokens == 2_048,
            "--reserve-output-tokens must be 2048",
        ),
        (
            args.evidence_tokens == 16_384,
            "--evidence-tokens must be 16384",
        ),
        (
            args.evidence_bytes == 65_536,
            "--evidence-bytes must be 65536",
        ),
        (
            args.response_tokens == 2_048,
            "--response-tokens must be 2048",
        ),
        (
            args.response_bytes == 8_192,
            "--response-bytes must be 8192",
        ),
        (args.max_tool_calls == 24, "--max-tool-calls must be 24"),
        (
            args.timeout_seconds == 1_200,
            "--timeout-seconds must be 1200",
        ),
    ];
    if let Some((_, message)) = expected.into_iter().find(|(valid, _)| !valid) {
        return Err(message.into());
    }
    Ok(())
}

fn initial_messages(store: &StoreData) -> Vec<Value> {
    let next_prompt = store
        .records
        .iter()
        .find(|record| record.source_type == "next_prompt")
        .map(|record| record.payload.as_str())
        .unwrap_or("");
    let completed = store
        .index
        .scopes
        .iter()
        .map(|scope| format!("{} ({})", scope.id, scope.session_id))
        .collect::<Vec<_>>()
        .join(", ");
    vec![
        json!({
            "role": "system",
            "content": concat!(
                "You are an automatic supervisor for a long-running Agent workspace. ",
                "Decide whether one short, evidence-grounded message can improve the worker's next task. ",
                "Before deciding, inspect at least one successful tool from the required evidence family, including before abstaining. ",
                "A current-workspace call satisfies a current-only interface; an interface exposing Raw history must inspect Raw history; ",
                "an interface also exposing trajectory relations must inspect a trajectory relation. One successful required-family call is sufficient. ",
                "Use only facts returned by available tools; never infer file effects from shell text. ",
                "source_ids must contain only IDs actually returned by a tool in this run; use an empty list when no tool evidence was used. ",
                "Do not mention benchmarks, evaluators, conditions, hidden files, scores, or supervisor tool names. ",
                "If no supported and actionable advice is needed, ABSTAIN. Otherwise INTERVENE with one concise ",
                "worker-facing message and cite the exact source IDs used. Return only the required JSON object."
            )
        }),
        json!({
            "role": "user",
            "content": format!(
                "Workspace episode: {}\nCompleted prefix sessions: {}\n\nNext official worker prompt:\n{}\n\nReturn a bounded intervention or abstain.",
                store.index.episode_id, completed, next_prompt
            )
        }),
    ]
}

fn tool_schemas(condition: Condition) -> Vec<Value> {
    let offset = json!({
        "offset_bytes": {
            "type": "integer",
            "minimum": 0,
            "description": "Continue a paginated UTF-8 JSON result at this exact byte offset."
        }
    });
    let mut tools = vec![
        function_tool(
            "list_current",
            "List the exact current workspace manifest with source IDs.",
            json!({"type": "object", "properties": {}, "additionalProperties": false}),
            &[],
        ),
        function_tool(
            "search_current",
            "Search exact current-workspace file payloads by deterministic ROUGE-L recall.",
            json!({
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "minimum": 1, "maximum": 10},
                    "offset_bytes": offset["offset_bytes"],
                },
                "required": ["query"],
                "additionalProperties": false,
            }),
            &["query"],
        ),
        function_tool(
            "read_current",
            "Read one exact current-workspace file by relative path.",
            json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset_bytes": offset["offset_bytes"],
                },
                "required": ["path"],
                "additionalProperties": false,
            }),
            &["path"],
        ),
    ];
    if !matches!(condition, Condition::Generic) {
        tools.extend([
            function_tool(
                "list_sources",
                "List every allowlisted Raw source and completed session scope.",
                json!({"type": "object", "properties": {}, "additionalProperties": false}),
                &[],
            ),
            function_tool(
                "search",
                "Search complete allowlisted Raw-record payloads by deterministic ROUGE-L recall.",
                json!({
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "scope": {"type": "string"},
                        "source_types": {"type": "array", "items": {"type": "string"}},
                        "k": {"type": "integer", "minimum": 1, "maximum": 10},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["query"],
                    "additionalProperties": false,
                }),
                &["query"],
            ),
            function_tool(
                "read_record",
                "Read one exact Raw record and its supporting action IDs.",
                json!({
                    "type": "object",
                    "properties": {
                        "raw_id": {"type": "string"},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["raw_id"],
                    "additionalProperties": false,
                }),
                &["raw_id"],
            ),
            function_tool(
                "read_range",
                "Read at most five contiguous exact Raw records within one scope.",
                json!({
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                        "start_raw_id": {"type": "string"},
                        "end_raw_id": {"type": "string"},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["scope", "start_raw_id", "end_raw_id"],
                    "additionalProperties": false,
                }),
                &["scope", "start_raw_id", "end_raw_id"],
            ),
        ]);
    }
    if matches!(condition, Condition::Trajectory) {
        tools.extend([
            function_tool(
                "artifact_history",
                "Return source-backed observed/unknown history and rename continuity for one artifact path.",
                json!({
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["path"],
                    "additionalProperties": false,
                }),
                &["path"],
            ),
            function_tool(
                "session_diff",
                "Return exact added, removed, and changed artifacts between two immutable post-round snapshots.",
                json!({
                    "type": "object",
                    "properties": {
                        "from_session": {"type": "string"},
                        "to_session": {"type": "string"},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["from_session", "to_session"],
                    "additionalProperties": false,
                }),
                &["from_session", "to_session"],
            ),
            function_tool(
                "effects",
                "Return the closure, observed effects, unknown candidates, and supporting Raw IDs for one action.",
                json!({
                    "type": "object",
                    "properties": {
                        "action_id": {"type": "string"},
                        "offset_bytes": offset["offset_bytes"],
                    },
                    "required": ["action_id"],
                    "additionalProperties": false,
                }),
                &["action_id"],
            ),
        ]);
    }
    tools
}

fn function_tool(name: &str, description: &str, parameters: Value, _required: &[&str]) -> Value {
    json!({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "strict": true,
            "parameters": parameters,
        }
    })
}

fn prediction_schema(raw_ids: &[String]) -> Value {
    let source_ids = if raw_ids.is_empty() {
        json!({"type": "array", "maxItems": 0, "items": {"type": "string"}})
    } else {
        json!({
            "type": "array",
            "items": {"type": "string", "enum": raw_ids},
        })
    };
    json!({
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["INTERVENE", "ABSTAIN"]
            },
            "message": {"type": "string"},
            "source_ids": source_ids,
        },
        "required": ["decision", "message", "source_ids"],
        "additionalProperties": false,
    })
}

fn prediction_response_format(raw_ids: &[String]) -> Value {
    json!({
        "type": "json_schema",
        "json_schema": {
            "name": "intervention",
            "strict": true,
            "schema": prediction_schema(raw_ids),
        }
    })
}

fn validate_intervention(
    intervention: &Intervention,
    store: &StoreData,
    exposed_source_ids: &BTreeSet<String>,
) -> Result<(), AnyError> {
    if !["INTERVENE", "ABSTAIN"].contains(&intervention.decision.as_str()) {
        return Err("intervention decision must be INTERVENE or ABSTAIN".into());
    }
    if intervention.decision == "ABSTAIN" && !intervention.message.is_empty() {
        return Err("ABSTAIN requires an empty message".into());
    }
    if intervention.decision == "INTERVENE" && intervention.message.trim().is_empty() {
        return Err("INTERVENE requires a non-empty message".into());
    }
    let raw_ids = store
        .records
        .iter()
        .map(|record| record.id.as_str())
        .collect::<std::collections::HashSet<_>>();
    for source_id in &intervention.source_ids {
        if !raw_ids.contains(source_id.as_str()) {
            return Err(format!("intervention cites unknown source ID {source_id}").into());
        }
        if !exposed_source_ids.contains(source_id) {
            return Err(format!("intervention cites unexposed source ID {source_id}").into());
        }
    }
    let lowered = intervention.message.to_ascii_lowercase();
    for forbidden in [
        "benchmark",
        "oracle",
        "ground truth",
        "trajectory condition",
        "raw condition",
        "generic condition",
        "list_current",
        "read_current",
        "search_current",
        "list_sources",
        "read_record",
        "read_range",
        "artifact_history",
        "session_diff",
        "effects",
    ] {
        if lowered.contains(forbidden) {
            return Err(
                format!("intervention message contains forbidden term {forbidden:?}").into(),
            );
        }
    }
    Ok(())
}

pub(crate) fn rouge_l_recall(target: &str, prediction: &str) -> f64 {
    let target = rouge_tokens(target);
    if target.is_empty() {
        return 0.0;
    }
    let prediction = rouge_tokens(prediction);
    let mut previous = vec![0usize; prediction.len() + 1];
    let mut current = vec![0usize; prediction.len() + 1];
    for left in &target {
        for (offset, right) in prediction.iter().enumerate() {
            current[offset + 1] = if left == right {
                previous[offset] + 1
            } else {
                current[offset].max(previous[offset + 1])
            };
        }
        std::mem::swap(&mut previous, &mut current);
        current.fill(0);
    }
    previous[prediction.len()] as f64 / target.len() as f64
}

fn rouge_tokens(text: &str) -> Vec<String> {
    let normalized = text
        .to_ascii_lowercase()
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch } else { ' ' })
        .collect::<String>();
    normalized
        .split_whitespace()
        .filter(|token| !token.is_empty())
        .map(str::to_string)
        .collect()
}

fn first_words(text: &str, limit: usize) -> String {
    text.split_whitespace()
        .take(limit)
        .collect::<Vec<_>>()
        .join(" ")
}

fn sha256_file(path: &Path) -> Result<String, AnyError> {
    let mut file = fs::File::open(path)?;
    let mut hash = Sha256::new();
    let mut buffer = vec![0u8; 1024 * 1024];
    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hash.update(&buffer[..count]);
    }
    Ok(hex::encode(hash.finalize()))
}

fn write_jsonl(path: &Path, rows: &[Value]) -> Result<(), AnyError> {
    let mut bytes = Vec::new();
    for row in rows {
        serde_json::to_writer(&mut bytes, row)?;
        bytes.push(b'\n');
    }
    atomic_write(path, &bytes)?;
    Ok(())
}

fn atomic_write(path: &Path, bytes: &[u8]) -> Result<(), AnyError> {
    let name = path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or("atomic output path has no UTF-8 filename")?;
    let temporary = path.with_file_name(format!(".{name}.{}.tmp", std::process::id()));
    fs::write(&temporary, bytes)?;
    fs::rename(temporary, path)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rouge_l_matches_retained_official_conformance_fixture() {
        let fixture: Value =
            serde_json::from_str(include_str!("../research/rouge-l-conformance.json")).unwrap();
        for case in fixture["cases"].as_array().unwrap() {
            let actual = rouge_l_recall(
                case["target"].as_str().unwrap(),
                case["prediction"].as_str().unwrap(),
            );
            let expected = case["recall"].as_f64().unwrap();
            assert!((actual - expected).abs() < 1e-12, "{case}");
        }
    }

    #[test]
    fn snippet_is_first_150_whitespace_words() {
        let text = (0..200)
            .map(|value| value.to_string())
            .collect::<Vec<_>>()
            .join(" ");
        assert_eq!(first_words(&text, 150).split_whitespace().count(), 150);
    }

    #[test]
    fn schema_exposes_only_three_additional_workspace_relations() {
        let generic = tool_schemas(Condition::Generic);
        let raw = tool_schemas(Condition::Raw);
        let trajectory = tool_schemas(Condition::Trajectory);
        assert_eq!(generic.len(), 3);
        assert_eq!(raw.len(), 7);
        assert_eq!(trajectory.len(), 10);
        let names = trajectory
            .iter()
            .filter_map(|tool| tool.pointer("/function/name").and_then(Value::as_str))
            .collect::<Vec<_>>();
        assert_eq!(&names[7..], ["artifact_history", "session_diff", "effects"]);
    }

    #[test]
    fn current_workspace_calls_do_not_satisfy_raw_or_trajectory_engagement() {
        let engagement = ToolEngagement {
            current_workspace_tool_calls: 1,
            ..ToolEngagement::default()
        };
        assert!(validate_tool_engagement(Condition::Generic, &engagement).is_ok());
        assert!(validate_tool_engagement(Condition::Raw, &engagement).is_err());
        assert!(validate_tool_engagement(Condition::Trajectory, &engagement).is_err());
    }

    #[test]
    fn each_condition_requires_its_registered_tool_family() {
        let raw = ToolEngagement {
            raw_history_tool_calls: 1,
            ..ToolEngagement::default()
        };
        assert!(validate_tool_engagement(Condition::Raw, &raw).is_ok());
        assert!(validate_tool_engagement(Condition::Trajectory, &raw).is_err());

        let trajectory = ToolEngagement {
            trajectory_relation_tool_calls: 1,
            ..ToolEngagement::default()
        };
        assert!(validate_tool_engagement(Condition::Trajectory, &trajectory).is_ok());
    }

    #[test]
    fn empty_success_does_not_count_as_evidence_engagement() {
        let mut engagement = ToolEngagement::default();
        engagement.record_success("search", false);
        engagement.record_success("artifact_history", false);
        assert!(validate_tool_engagement(Condition::Raw, &engagement).is_err());
        assert!(validate_tool_engagement(Condition::Trajectory, &engagement).is_err());

        engagement.record_success("artifact_history", true);
        assert!(validate_tool_engagement(Condition::Trajectory, &engagement).is_ok());
    }

    #[test]
    fn raw_evidence_maps_to_the_same_canonical_action_namespace() {
        let actions = vec![crate::research::Action {
            id: "a0000001".into(),
            ts_ns: 1,
            end_ns: 2,
            scope_id: "g2".into(),
            kind: "exec".into(),
            status: "ok".into(),
            closure: "observed".into(),
            raw_ids: vec!["r-call".into()],
            effects: vec![crate::research::Effect {
                operation: "write".into(),
                path: "result.json".into(),
                previous_path: None,
                evidence_ids: vec!["r-syscall".into()],
            }],
        }];
        assert_eq!(supporting_action_ids(&actions, "r-call"), ["a0000001"]);
        assert_eq!(supporting_action_ids(&actions, "r-syscall"), ["a0000001"]);
        assert!(supporting_action_ids(&actions, "r-other").is_empty());
    }

    #[test]
    fn llama_cpp_receives_the_frozen_schema_at_the_required_nested_path() {
        let raw_ids = vec!["r000000001".to_string(), "r000000002".to_string()];
        let response_format = prediction_response_format(&raw_ids);
        assert_eq!(response_format["type"], "json_schema");
        assert_eq!(
            response_format.pointer("/json_schema/schema"),
            Some(&prediction_schema(&raw_ids))
        );
        assert_eq!(response_format["json_schema"]["strict"], true);
        assert_eq!(
            response_format.pointer("/json_schema/schema/properties/source_ids/items/enum"),
            Some(&json!(raw_ids))
        );
        let empty = prediction_response_format(&[]);
        assert_eq!(
            empty.pointer("/json_schema/schema/properties/source_ids/maxItems"),
            Some(&json!(0))
        );
    }
}
