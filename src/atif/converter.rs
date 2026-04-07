//! Converter from AgentSight SQLite GenAI data to ATIF v1.6 format.
//!
//! Reconstructs an incremental step sequence from a series of LLM call records.
//! Each LLM call maps to an agent step, with system/user steps extracted from
//! the first call's context. Tool call observations are correlated across
//! consecutive calls.

use std::collections::HashMap;

use crate::genai::semantic::{
    GenAISemanticEvent, LLMCall, MessagePart, InputMessage, OutputMessage,
};
use crate::storage::sqlite::genai::TraceEventDetail;

use super::schema::*;

/// Convert a single trace (one user query's call chain) into an ATIF document.
pub fn convert_trace_to_atif(
    trace_id: &str,
    events: Vec<TraceEventDetail>,
) -> Result<AtifDocument, Box<dyn std::error::Error>> {
    if events.is_empty() {
        return Err("no events found for trace".into());
    }

    let parsed = parse_all_events(&events);
    let agent = build_agent_metadata(&events, &parsed);

    let mut step_counter: u32 = 0;
    let mut steps = Vec::new();

    // 1. System prompt step
    if let Some(system_text) = extract_system_prompt(&events[0], parsed[0].as_ref()) {
        if !system_text.is_empty() {
            step_counter += 1;
            steps.push(AtifStep {
                step_id: step_counter,
                timestamp: Some(ns_to_iso8601(events[0].start_timestamp_ns as u64)),
                source: "system".to_string(),
                message: Some(system_text),
                model_name: None,
                reasoning_content: None,
                tool_calls: None,
                observation: None,
                metrics: None,
                extra: None,
            });
        }
    }

    // 2. User query step
    if let Some(user_text) = extract_user_query(&events[0], parsed[0].as_ref()) {
        if !user_text.is_empty() {
            step_counter += 1;
            steps.push(AtifStep {
                step_id: step_counter,
                timestamp: Some(ns_to_iso8601(events[0].start_timestamp_ns as u64)),
                source: "user".to_string(),
                message: Some(user_text),
                model_name: None,
                reasoning_content: None,
                tool_calls: None,
                observation: None,
                metrics: None,
                extra: None,
            });
        }
    }

    // 3. Agent steps
    for i in 0..events.len() {
        step_counter += 1;
        let step = build_agent_step(
            step_counter,
            &events[i],
            parsed.get(i).and_then(|p| p.as_ref()),
            // Next event for observation correlation
            if i + 1 < events.len() {
                Some((&events[i + 1], parsed.get(i + 1).and_then(|p| p.as_ref())))
            } else {
                None
            },
        );
        steps.push(step);
    }

    // 4. Final metrics
    let final_metrics = compute_final_metrics(&events, steps.len() as u32);

    Ok(AtifDocument {
        schema_version: SCHEMA_VERSION.to_string(),
        session_id: trace_id.to_string(),
        agent,
        steps,
        final_metrics: Some(final_metrics),
        extra: None,
    })
}

/// Convert a full session (all traces) into an ATIF document.
pub fn convert_session_to_atif(
    session_id: &str,
    events: Vec<TraceEventDetail>,
) -> Result<AtifDocument, Box<dyn std::error::Error>> {
    if events.is_empty() {
        return Err("no events found for session".into());
    }

    let parsed = parse_all_events(&events);
    let agent = build_agent_metadata(&events, &parsed);

    let mut step_counter: u32 = 0;
    let mut steps = Vec::new();
    let mut last_system_text: Option<String> = None;

    // Group events by trace_id, preserving order
    let trace_groups = group_by_trace(&events, &parsed);

    for (trace_events, trace_parsed) in &trace_groups {
        if trace_events.is_empty() {
            continue;
        }

        // System prompt: emit if changed or first time
        if let Some(system_text) =
            extract_system_prompt(trace_events[0], trace_parsed.first().and_then(|p| p.as_ref()))
        {
            if !system_text.is_empty() && last_system_text.as_deref() != Some(&system_text) {
                step_counter += 1;
                steps.push(AtifStep {
                    step_id: step_counter,
                    timestamp: Some(ns_to_iso8601(
                        trace_events[0].start_timestamp_ns as u64,
                    )),
                    source: "system".to_string(),
                    message: Some(system_text.clone()),
                    model_name: None,
                    reasoning_content: None,
                    tool_calls: None,
                    observation: None,
                    metrics: None,
                    extra: None,
                });
                last_system_text = Some(system_text);
            }
        }

        // User query step
        if let Some(user_text) =
            extract_user_query(trace_events[0], trace_parsed.first().and_then(|p| p.as_ref()))
        {
            if !user_text.is_empty() {
                step_counter += 1;
                steps.push(AtifStep {
                    step_id: step_counter,
                    timestamp: Some(ns_to_iso8601(
                        trace_events[0].start_timestamp_ns as u64,
                    )),
                    source: "user".to_string(),
                    message: Some(user_text),
                    model_name: None,
                    reasoning_content: None,
                    tool_calls: None,
                    observation: None,
                    metrics: None,
                    extra: None,
                });
            }
        }

        // Agent steps
        for i in 0..trace_events.len() {
            step_counter += 1;
            let next = if i + 1 < trace_events.len() {
                Some((
                    trace_events[i + 1],
                    trace_parsed.get(i + 1).and_then(|p| p.as_ref()),
                ))
            } else {
                None
            };
            let step = build_agent_step(
                step_counter,
                trace_events[i],
                trace_parsed.get(i).and_then(|p| p.as_ref()),
                next,
            );
            steps.push(step);
        }
    }

    let final_metrics = compute_final_metrics(&events, steps.len() as u32);

    Ok(AtifDocument {
        schema_version: SCHEMA_VERSION.to_string(),
        session_id: session_id.to_string(),
        agent,
        steps,
        final_metrics: Some(final_metrics),
        extra: None,
    })
}

// ─── Internal helpers ────────────────────────────────────────────────────────

/// Parse event_json for all events upfront. Returns a Vec of Option<LLMCall>.
fn parse_all_events(events: &[TraceEventDetail]) -> Vec<Option<LLMCall>> {
    events
        .iter()
        .map(|e| parse_event_json(e))
        .collect()
}

/// Try to deserialize event_json into an LLMCall.
fn parse_event_json(event: &TraceEventDetail) -> Option<LLMCall> {
    let json_str = event.event_json.as_deref()?;
    // event_json is stored as GenAISemanticEvent enum
    let semantic: GenAISemanticEvent = serde_json::from_str(json_str).ok()?;
    match semantic {
        GenAISemanticEvent::LLMCall(call) => Some(call),
        _ => None,
    }
}

/// Group events by trace_id, preserving chronological order.
/// Returns Vec of (events_in_trace, parsed_in_trace).
fn group_by_trace<'a>(
    events: &'a [TraceEventDetail],
    parsed: &'a [Option<LLMCall>],
) -> Vec<(Vec<&'a TraceEventDetail>, Vec<&'a Option<LLMCall>>)> {
    // Maintain insertion order using a Vec of (trace_id, indices)
    let mut order: Vec<String> = Vec::new();
    let mut groups: HashMap<String, Vec<usize>> = HashMap::new();

    for (i, event) in events.iter().enumerate() {
        let tid = event.trace_id.clone().unwrap_or_default();
        if !groups.contains_key(&tid) {
            order.push(tid.clone());
        }
        groups.entry(tid).or_default().push(i);
    }

    order
        .into_iter()
        .filter_map(|tid| {
            let indices = groups.remove(&tid)?;
            let evts: Vec<_> = indices.iter().map(|&i| &events[i]).collect();
            let prs: Vec<_> = indices.iter().map(|&i| &parsed[i]).collect();
            Some((evts, prs))
        })
        .collect()
}

/// Build agent metadata from events.
fn build_agent_metadata(
    events: &[TraceEventDetail],
    parsed: &[Option<LLMCall>],
) -> AtifAgent {
    // Agent name: first non-None agent_name, fallback to process_name
    let name = events
        .iter()
        .find_map(|e| e.agent_name.clone())
        .or_else(|| events.iter().find_map(|e| e.process_name.clone()))
        .unwrap_or_else(|| "unknown".to_string());

    // Model name: most frequent model
    let model_name = most_frequent_model(events);

    // Collect tool definitions from parsed calls
    let tool_definitions = collect_tool_definitions(parsed);

    AtifAgent {
        name,
        version: "1.0.0".to_string(),
        model_name,
        tool_definitions,
        extra: None,
    }
}

/// Find the most frequently used model across events.
fn most_frequent_model(events: &[TraceEventDetail]) -> Option<String> {
    let mut counts: HashMap<&str, usize> = HashMap::new();
    for e in events {
        if let Some(ref m) = e.model {
            *counts.entry(m.as_str()).or_default() += 1;
        }
    }
    counts
        .into_iter()
        .max_by_key(|&(_, c)| c)
        .map(|(m, _)| m.to_string())
}

/// Collect unique tool definitions from all parsed LLM calls.
fn collect_tool_definitions(parsed: &[Option<LLMCall>]) -> Option<Vec<serde_json::Value>> {
    let mut seen_names = std::collections::HashSet::new();
    let mut defs = Vec::new();

    for call in parsed.iter().filter_map(|p| p.as_ref()) {
        if let Some(ref tools) = call.request.tools {
            for tool in tools {
                if seen_names.insert(tool.name.clone()) {
                    // Build OpenAI function calling schema format
                    let def = serde_json::json!({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                        }
                    });
                    defs.push(def);
                }
            }
        }
    }

    if defs.is_empty() { None } else { Some(defs) }
}

/// Extract system prompt text from event data.
fn extract_system_prompt(
    event: &TraceEventDetail,
    parsed: Option<&LLMCall>,
) -> Option<String> {
    // Strategy 1: from parsed LLMCall request messages
    if let Some(call) = parsed {
        let text = extract_text_by_role(&call.request.messages, "system");
        if !text.is_empty() {
            return Some(text);
        }
    }

    // Strategy 2: from system_instructions column (JSON array of InputMessage)
    if let Some(ref json) = event.system_instructions {
        if let Ok(msgs) = serde_json::from_str::<Vec<InputMessage>>(json) {
            let text = extract_text_from_input_messages(&msgs, "system");
            if !text.is_empty() {
                return Some(text);
            }
        }
        // Might be a plain string
        if let Ok(s) = serde_json::from_str::<String>(json) {
            if !s.is_empty() {
                return Some(s);
            }
        }
    }

    None
}

/// Extract user query text from event data.
fn extract_user_query(
    event: &TraceEventDetail,
    parsed: Option<&LLMCall>,
) -> Option<String> {
    // Strategy 1: user_query column (already cleaned by builder)
    if let Some(ref q) = event.user_query {
        if !q.is_empty() {
            return Some(q.clone());
        }
    }

    // Strategy 2: from parsed LLMCall — last user message text
    if let Some(call) = parsed {
        let text = extract_last_user_text(&call.request.messages);
        if let Some(t) = text {
            return Some(t);
        }
    }

    // Strategy 3: from input_messages column
    if let Some(ref json) = event.input_messages {
        if let Ok(msgs) = serde_json::from_str::<Vec<InputMessage>>(json) {
            let text = extract_last_user_text_from_input(&msgs);
            if let Some(t) = text {
                return Some(t);
            }
        }
    }

    None
}

/// Build an agent step from a single LLM call event.
fn build_agent_step(
    step_id: u32,
    event: &TraceEventDetail,
    parsed: Option<&LLMCall>,
    next: Option<(&TraceEventDetail, Option<&LLMCall>)>,
) -> AtifStep {
    let mut message_text = String::new();
    let mut reasoning_text = String::new();
    let mut tool_calls: Vec<AtifToolCall> = Vec::new();

    // Extract from parsed response messages
    if let Some(call) = parsed {
        for msg in &call.response.messages {
            for part in &msg.parts {
                match part {
                    MessagePart::Text { content } => {
                        if !content.is_empty() {
                            if !message_text.is_empty() {
                                message_text.push('\n');
                            }
                            message_text.push_str(content);
                        }
                    }
                    MessagePart::Reasoning { content } => {
                        if !content.is_empty() {
                            if !reasoning_text.is_empty() {
                                reasoning_text.push('\n');
                            }
                            reasoning_text.push_str(content);
                        }
                    }
                    MessagePart::ToolCall { id, name, arguments } => {
                        let tc_id = id
                            .clone()
                            .unwrap_or_else(|| format!("auto_{}", tool_calls.len()));
                        tool_calls.push(AtifToolCall {
                            tool_call_id: tc_id,
                            function_name: name.clone(),
                            arguments: arguments
                                .clone()
                                .unwrap_or(serde_json::Value::Object(Default::default())),
                        });
                    }
                    _ => {}
                }
            }
        }
    } else {
        // Fallback: parse output_messages column directly
        if let Some(ref json) = event.output_messages {
            if let Ok(msgs) = serde_json::from_str::<Vec<OutputMessage>>(json) {
                for msg in &msgs {
                    for part in &msg.parts {
                        match part {
                            MessagePart::Text { content } => {
                                if !content.is_empty() {
                                    if !message_text.is_empty() {
                                        message_text.push('\n');
                                    }
                                    message_text.push_str(content);
                                }
                            }
                            MessagePart::Reasoning { content } => {
                                if !content.is_empty() {
                                    if !reasoning_text.is_empty() {
                                        reasoning_text.push('\n');
                                    }
                                    reasoning_text.push_str(content);
                                }
                            }
                            MessagePart::ToolCall { id, name, arguments } => {
                                let tc_id = id
                                    .clone()
                                    .unwrap_or_else(|| format!("auto_{}", tool_calls.len()));
                                tool_calls.push(AtifToolCall {
                                    tool_call_id: tc_id,
                                    function_name: name.clone(),
                                    arguments: arguments
                                        .clone()
                                        .unwrap_or(serde_json::Value::Object(Default::default())),
                                });
                            }
                            _ => {}
                        }
                    }
                }
            }
        }
    }

    // Observation: correlate tool_calls with responses from next event
    let observation = if !tool_calls.is_empty() {
        build_observation(&tool_calls, next)
    } else {
        None
    };

    // Metrics
    let metrics = Some(AtifStepMetrics {
        prompt_tokens: if event.input_tokens > 0 {
            Some(event.input_tokens as u32)
        } else {
            None
        },
        completion_tokens: if event.output_tokens > 0 {
            Some(event.output_tokens as u32)
        } else {
            None
        },
        cached_tokens: event.cache_read_tokens.and_then(|v| {
            if v > 0 { Some(v as u32) } else { None }
        }),
        extra: None,
    });

    // Timestamp: prefer end_timestamp (when response arrived)
    let timestamp_ns = event
        .end_timestamp_ns
        .unwrap_or(event.start_timestamp_ns);

    AtifStep {
        step_id,
        timestamp: Some(ns_to_iso8601(timestamp_ns as u64)),
        source: "agent".to_string(),
        message: if message_text.is_empty() {
            None
        } else {
            Some(message_text)
        },
        model_name: event.model.clone(),
        reasoning_content: if reasoning_text.is_empty() {
            None
        } else {
            Some(reasoning_text)
        },
        tool_calls: if tool_calls.is_empty() {
            None
        } else {
            Some(tool_calls)
        },
        observation,
        metrics,
        extra: None,
    }
}

/// Build observation by looking for ToolCallResponse in the next event's input.
fn build_observation(
    tool_calls: &[AtifToolCall],
    next: Option<(&TraceEventDetail, Option<&LLMCall>)>,
) -> Option<AtifObservation> {
    let (next_event, next_parsed) = next?;

    let tc_ids: HashMap<&str, usize> = tool_calls
        .iter()
        .enumerate()
        .map(|(i, tc)| (tc.tool_call_id.as_str(), i))
        .collect();

    let mut results: Vec<AtifObservationResult> = Vec::new();
    let mut matched_by_id = vec![false; tool_calls.len()];

    // Strategy 1: from parsed LLMCall's full request messages
    if let Some(call) = next_parsed {
        collect_tool_responses(&call.request.messages, &tc_ids, &mut results, &mut matched_by_id);
    } else {
        // Strategy 2: from event_json parsed as LLMCall
        if let Some(call) = parse_event_json(next_event) {
            collect_tool_responses(
                &call.request.messages,
                &tc_ids,
                &mut results,
                &mut matched_by_id,
            );
        }
    }

    // Strategy 3: from input_messages column (incremental messages)
    if results.is_empty() {
        if let Some(ref json) = next_event.input_messages {
            if let Ok(msgs) = serde_json::from_str::<Vec<InputMessage>>(json) {
                collect_tool_responses(&msgs, &tc_ids, &mut results, &mut matched_by_id);
            }
        }
    }

    if results.is_empty() {
        None
    } else {
        Some(AtifObservation { results })
    }
}

/// Scan input messages for ToolCallResponse parts, matching by tool_call_id.
fn collect_tool_responses(
    messages: &[InputMessage],
    tc_ids: &HashMap<&str, usize>,
    results: &mut Vec<AtifObservationResult>,
    matched: &mut [bool],
) {
    let mut positional_idx: usize = 0;
    for msg in messages {
        if msg.role != "tool" {
            continue;
        }
        for part in &msg.parts {
            if let MessagePart::ToolCallResponse { id, response } = part {
                let content_str = match response {
                    serde_json::Value::String(s) => s.clone(),
                    other => serde_json::to_string(other).unwrap_or_default(),
                };

                // Try to match by ID first
                if let Some(tc_id) = id {
                    if let Some(&idx) = tc_ids.get(tc_id.as_str()) {
                        if !matched[idx] {
                            matched[idx] = true;
                            results.push(AtifObservationResult {
                                source_call_id: Some(tc_id.clone()),
                                content: Some(content_str),
                            });
                            continue;
                        }
                    }
                }

                // Fallback: positional matching
                while positional_idx < matched.len() && matched[positional_idx] {
                    positional_idx += 1;
                }
                if positional_idx < matched.len() {
                    matched[positional_idx] = true;
                    results.push(AtifObservationResult {
                        source_call_id: Some(
                            id.clone()
                                .unwrap_or_else(|| format!("auto_{}", positional_idx)),
                        ),
                        content: Some(content_str),
                    });
                    positional_idx += 1;
                }
            }
        }
    }
}

/// Compute aggregated final metrics.
fn compute_final_metrics(events: &[TraceEventDetail], total_steps: u32) -> AtifFinalMetrics {
    let mut total_prompt: u64 = 0;
    let mut total_completion: u64 = 0;
    let mut total_cached: u64 = 0;

    for e in events {
        total_prompt += e.input_tokens as u64;
        total_completion += e.output_tokens as u64;
        if let Some(c) = e.cache_read_tokens {
            total_cached += c as u64;
        }
    }

    AtifFinalMetrics {
        total_prompt_tokens: Some(total_prompt),
        total_completion_tokens: Some(total_completion),
        total_cached_tokens: if total_cached > 0 {
            Some(total_cached)
        } else {
            None
        },
        total_steps: Some(total_steps),
        extra: None,
    }
}

// ─── Text extraction helpers ─────────────────────────────────────────────────

/// Extract concatenated text from messages with a specific role.
fn extract_text_by_role(messages: &[InputMessage], role: &str) -> String {
    let mut parts = Vec::new();
    for msg in messages {
        if msg.role == role {
            for part in &msg.parts {
                if let MessagePart::Text { content } = part {
                    if !content.is_empty() {
                        parts.push(content.as_str());
                    }
                }
            }
        }
    }
    parts.join("\n")
}

/// Extract text from InputMessage array filtered by role.
fn extract_text_from_input_messages(messages: &[InputMessage], role: &str) -> String {
    extract_text_by_role(messages, role)
}

/// Extract the last user message text from InputMessage array.
fn extract_last_user_text(messages: &[InputMessage]) -> Option<String> {
    messages
        .iter()
        .rev()
        .filter(|m| m.role == "user")
        .find_map(|m| {
            let text: Vec<&str> = m
                .parts
                .iter()
                .filter_map(|p| match p {
                    MessagePart::Text { content } if !content.is_empty() => Some(content.as_str()),
                    _ => None,
                })
                .collect();
            if text.is_empty() {
                None
            } else {
                Some(text.join("\n"))
            }
        })
}

/// Same as extract_last_user_text but for InputMessage slice.
fn extract_last_user_text_from_input(messages: &[InputMessage]) -> Option<String> {
    extract_last_user_text(messages)
}

/// Convert nanosecond timestamp to ISO 8601 string.
fn ns_to_iso8601(ns: u64) -> String {
    use chrono::DateTime;

    let dt = DateTime::from_timestamp_nanos(ns as i64);
    dt.to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}
