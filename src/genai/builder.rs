//! GenAI Semantic Builder
//!
//! This module builds GenAI semantic events from AnalysisResult.
//! It reuses already-extracted data to avoid redundant parsing.

use crate::analyzer::{
    AnalysisResult, TokenRecord, ParsedApiMessage, HttpRecord,
};
use crate::analyzer::message::types::OpenAIChatMessage;
use crate::discovery::matcher::{ProcessContext, AgentMatcher};
use crate::discovery::registry::known_agents;
use super::semantic::{
    GenAISemanticEvent, LLMCall, LLMRequest, LLMResponse,
    InputMessage, OutputMessage, MessagePart, TokenUsage,
};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

/// Builder that constructs GenAI semantic events from AnalysisResult
pub struct GenAIBuilder {
    /// Session ID prefix (timestamp-based, unique per agentsight run)
    session_prefix: String,
    /// Counter for generating unique IDs within a session
    call_counter: AtomicU64,
}

impl Default for GenAIBuilder {
    fn default() -> Self {
        Self::new()
    }
}

impl GenAIBuilder {
    /// Create a new GenAI builder
    pub fn new() -> Self {
        let ts = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis())
            .unwrap_or(0);
        let pid = std::process::id();
        GenAIBuilder {
            session_prefix: format!("{:x}_{:x}", ts, pid),
            call_counter: AtomicU64::new(0),
        }
    }

    /// Build GenAI semantic events from analysis results
    ///
    /// This method reuses already-extracted data (Token, Message, HttpRecord)
    /// to construct higher-level GenAI semantic events without redundant parsing.
    pub fn build(&self, results: &[AnalysisResult]) -> Vec<GenAISemanticEvent> {
        let mut events = Vec::new();

        // Group related results by building LLMCall from multiple sources
        // TokenRecord + HttpRecord + ParsedApiMessage -> LLMCall
        if let Some(llm_call) = self.build_llm_call(results) {
            events.push(GenAISemanticEvent::LLMCall(llm_call));
        }

        events
    }

    /// Build LLMCall from analysis results
    ///
    /// Combines data from TokenRecord, HttpRecord, and ParsedApiMessage
    fn build_llm_call(&self, results: &[AnalysisResult]) -> Option<LLMCall> {
        // Extract components from analysis results
        let token_record = results.iter().find_map(|r| match r {
            AnalysisResult::Token(t) => Some(t.clone()),
            _ => None,
        });

        let http_record = results.iter().find_map(|r| match r {
            AnalysisResult::Http(h) => Some(h.clone()),
            _ => None,
        });

        let parsed_message = results.iter().find_map(|r| match r {
            AnalysisResult::Message(m) => Some(m.clone()),
            _ => None,
        });

        // Need at least HttpRecord to build LLMCall
        let http = http_record?;
        
        // Check if this is an LLM API call
        if !self.is_llm_api_path(&http.path) {
            return None;
        }

        let call_id = self.generate_id();

        // Build request from parsed message or HTTP record
        let request = self.build_request(&parsed_message, &http);
        
        // Build response from parsed message or HTTP record
        let response = self.build_response(&parsed_message, &http, &token_record);

        // Build token usage from TokenRecord
        let token_usage = token_record.as_ref().map(|t| TokenUsage {
            input_tokens: t.input_tokens as u32,
            output_tokens: t.output_tokens as u32,
            total_tokens: (t.input_tokens + t.output_tokens) as u32,
            cache_creation_input_tokens: t.cache_creation_tokens.map(|v| v as u32),
            cache_read_input_tokens: t.cache_read_tokens.map(|v| v as u32),
        });

        // Determine provider and model
        let provider = token_record.as_ref()
            .map(|t| t.provider.clone())
            .or_else(|| self.extract_provider_from_path(&http.path))
            .unwrap_or_else(|| "unknown".to_string());

        let model = token_record.as_ref()
            .and_then(|t| t.model.as_ref().filter(|m| !m.is_empty()).cloned())
            .or_else(|| self.extract_model_from_message(&parsed_message))
            .unwrap_or_else(|| "unknown".to_string());

        Some(LLMCall {
            call_id,
            start_timestamp_ns: http.timestamp_ns,
            end_timestamp_ns: http.timestamp_ns + http.duration_ns,
            duration_ns: http.duration_ns,
            provider,
            model,
            request,
            response,
            token_usage,
            error: None,
            pid: http.pid as i32,
            process_name: http.comm.clone(),
            agent_name: Self::resolve_agent_name(&http.comm),
            metadata: {
                let mut meta = HashMap::new();
                meta.insert("method".to_string(), http.method);
                meta.insert("path".to_string(), http.path.clone());
                meta.insert("status_code".to_string(), http.status_code.to_string());
                meta.insert("is_sse".to_string(), http.is_sse.to_string());
                meta.insert("sse_event_count".to_string(), http.sse_event_count.to_string());
                // Extract server.address and server.port from Host header
                if let Ok(headers) = serde_json::from_str::<HashMap<String, String>>(&http.request_headers) {
                    if let Some(host) = headers.get("host").or_else(|| headers.get("Host")) {
                        if let Some((addr, port)) = host.rsplit_once(':') {
                            meta.insert("server.address".to_string(), addr.to_string());
                            meta.insert("server.port".to_string(), port.to_string());
                        } else {
                            meta.insert("server.address".to_string(), host.clone());
                        }
                    }
                }
                // Derive gen_ai.operation.name from path
                if http.path.contains("/chat/completions") || http.path.contains("/v1/messages") {
                    meta.insert("operation_name".to_string(), "chat".to_string());
                } else if http.path.contains("/completions") {
                    meta.insert("operation_name".to_string(), "text_completion".to_string());
                }
                meta
            },
        })
    }

    /// Build LLMRequest from parsed message or HTTP record
    fn build_request(&self, message: &Option<ParsedApiMessage>, http: &HttpRecord) -> LLMRequest {
        match message {
            Some(ParsedApiMessage::OpenAICompletion { request, .. }) => {
                if let Some(req) = request.as_ref() {
                    let msgs = req.messages.iter().map(|m| {
                        Self::openai_msg_to_input(m)
                    }).collect();
                    return LLMRequest {
                        messages: msgs,
                        temperature: req.temperature,
                        max_tokens: req.max_tokens,
                        frequency_penalty: req.frequency_penalty,
                        presence_penalty: req.presence_penalty,
                        top_p: req.top_p,
                        top_k: None,
                        seed: req.seed,
                        stop_sequences: req.stop.clone(),
                        stream: req.stream.unwrap_or(false),
                        tools: None,
                        raw_body: http.request_body.clone(),
                    };
                }
            }
            Some(ParsedApiMessage::AnthropicMessage { request, .. }) => {
                if let Some(req) = request.as_ref() {
                    let msgs = req.messages.iter().map(|m| {
                        let role = format!("{:?}", m.role).to_lowercase();
                        InputMessage {
                            role,
                            parts: vec![MessagePart::Text { content: m.content.as_text() }],
                            name: None,
                        }
                    }).collect();
                    return LLMRequest {
                        messages: msgs,
                        temperature: req.temperature,
                        max_tokens: Some(req.max_tokens),
                        frequency_penalty: None,
                        presence_penalty: None,
                        top_p: req.top_p,
                        top_k: req.top_k.map(|v| v as f64),
                        seed: None,
                        stop_sequences: req.stop_sequences.clone(),
                        stream: req.stream.unwrap_or(false),
                        tools: None,
                        raw_body: http.request_body.clone(),
                    };
                }
            }
            _ => {}
        }

        // Fallback: no parsed message — parse request_body directly
        if let Some(ref body) = http.request_body {
            if let Some(req) = Self::parse_request_body(body) {
                return req;
            }
        }
        LLMRequest {
            messages: vec![],
            temperature: None,
            max_tokens: None,
            frequency_penalty: None,
            presence_penalty: None,
            top_p: None,
            top_k: None,
            seed: None,
            stop_sequences: None,
            stream: false,
            tools: None,
            raw_body: http.request_body.clone(),
        }
    }

    /// 从 HTTP request body 直接解析 LLMRequest（OpenAI/Anthropic 格式）
    fn parse_request_body(body: &str) -> Option<LLMRequest> {
        let v: serde_json::Value = serde_json::from_str(body).ok()?;
        let obj = v.as_object()?;

        // 解析 messages 数组
        let messages = obj.get("messages")
            .and_then(|m| m.as_array())
            .map(|arr| {
                arr.iter().filter_map(|msg| {
                    let role = msg.get("role")?.as_str()?.to_string();
                    let mut parts = Vec::new();

                    // content 可以是字符串或数组
                    if let Some(content) = msg.get("content") {
                        if let Some(s) = content.as_str() {
                            if !s.is_empty() {
                                parts.push(MessagePart::Text { content: s.to_string() });
                            }
                        } else if let Some(arr) = content.as_array() {
                            for item in arr {
                                if let Some(text) = item.get("text").and_then(|t| t.as_str()) {
                                    parts.push(MessagePart::Text { content: text.to_string() });
                                }
                            }
                        }
                    }

                    // tool_call 结果 (role=tool)
                    if role == "tool" {
                        if let Some(content) = msg.get("content") {
                            let id = msg.get("tool_call_id").and_then(|v| v.as_str()).map(|s| s.to_string());
                            parts = vec![MessagePart::ToolCallResponse {
                                id,
                                response: content.clone(),
                            }];
                        }
                    }

                    // tool_calls (role=assistant 发起的 tool calls)
                    if let Some(tool_calls) = msg.get("tool_calls").and_then(|v| v.as_array()) {
                        for tc in tool_calls {
                            let id = tc.get("id").and_then(|v| v.as_str()).map(|s| s.to_string());
                            let func = tc.get("function").unwrap_or(&serde_json::Value::Null);
                            let name = func.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            let arguments = func.get("arguments").map(|v| v.clone());
                            parts.push(MessagePart::ToolCall { id, name, arguments });
                        }
                    }

                    Some(InputMessage { role, parts, name: None })
                }).collect::<Vec<_>>()
            })
            .unwrap_or_default();

        if messages.is_empty() {
            return None;
        }

        Some(LLMRequest {
            messages,
            temperature: obj.get("temperature").and_then(|v| v.as_f64()),
            max_tokens: obj.get("max_tokens").and_then(|v| v.as_u64()).map(|v| v as u32),
            frequency_penalty: obj.get("frequency_penalty").and_then(|v| v.as_f64()),
            presence_penalty: obj.get("presence_penalty").and_then(|v| v.as_f64()),
            top_p: obj.get("top_p").and_then(|v| v.as_f64()),
            top_k: obj.get("top_k").and_then(|v| v.as_f64()),
            seed: obj.get("seed").and_then(|v| v.as_i64()),
            stop_sequences: obj.get("stop").and_then(|v| {
                v.as_array().map(|arr| arr.iter().filter_map(|s| s.as_str().map(String::from)).collect())
            }),
            stream: obj.get("stream").and_then(|v| v.as_bool()).unwrap_or(false),
            tools: None,
            raw_body: Some(body.to_string()),
        })
    }

    /// Build LLMResponse from parsed message or HTTP record
    fn build_response(&self, message: &Option<ParsedApiMessage>, http: &HttpRecord, _token_record: &Option<TokenRecord>) -> LLMResponse {
        // Try to extract from parsed message first
        let (messages, finish_reason): (Vec<OutputMessage>, Option<String>) = match message {
            Some(ParsedApiMessage::OpenAICompletion { response, .. }) => {
                response.as_ref().map(|resp| {
                    let msgs: Vec<OutputMessage> = resp.choices.iter().map(|c| {
                        Self::openai_msg_to_output(&c.message, c.finish_reason.as_deref())
                    }).collect();
                    let finish = resp.choices.first().and_then(|c| c.finish_reason.clone());
                    (msgs, finish)
                }).unwrap_or_else(|| (vec![], None))
            }
            Some(ParsedApiMessage::AnthropicMessage { response, .. }) => {
                response.as_ref().map(|resp| {
                    let mut parts = Vec::new();
                    for block in &resp.content {
                        match block {
                            crate::analyzer::message::AnthropicContentBlock::Text { text, .. } => {
                                if !text.is_empty() {
                                    parts.push(MessagePart::Text { content: text.clone() });
                                }
                            }
                            _ => {}
                        }
                    }
                    let msgs = vec![OutputMessage {
                        role: "assistant".to_string(),
                        parts,
                        name: None,
                        finish_reason: resp.stop_reason.clone(),
                    }];
                    let finish = resp.stop_reason.clone();
                    (msgs, finish)
                }).unwrap_or_else(|| (vec![], None))
            }
            _ => (vec![], None),
        };

        // For SSE responses, extract from response_body when no parsed message
        let messages = if messages.is_empty() && http.is_sse {
            // No parsed response — reconstruct from SSE response body directly
            if let Some(ref body) = http.response_body {
                Self::parse_sse_response_body(body, finish_reason.as_deref())
                    .unwrap_or(messages)
            } else {
                messages
            }
        } else if http.is_sse {
            // Has parsed response but may be missing reasoning/tool_calls — enrich from SSE body
            let mut msgs = messages;
            if let Some(ref body) = http.response_body {
                if let Some(msg) = msgs.first_mut() {
                    if msg.role == "assistant" {
                        let has_reasoning = msg.parts.iter().any(|p| matches!(p, MessagePart::Reasoning { .. }));
                        let has_tool_calls = msg.parts.iter().any(|p| matches!(p, MessagePart::ToolCall { .. }));
                        if let Some((extra, sse_finish)) = Self::extract_parts_from_sse_body(body) {
                            if !has_reasoning {
                                if let Some(r) = extra.iter().find(|p| matches!(p, MessagePart::Reasoning { .. })) {
                                    msg.parts.insert(0, r.clone());
                                }
                            }
                            if !has_tool_calls {
                                for p in extra.into_iter().filter(|p| matches!(p, MessagePart::ToolCall { .. })) {
                                    msg.parts.push(p);
                                }
                            }
                            // Enrich finish_reason if missing
                            if msg.finish_reason.is_none() {
                                msg.finish_reason = sse_finish;
                            }
                        }
                    }
                }
            }
            msgs
        } else {
            messages
        };

        LLMResponse {
            messages,
            streamed: http.is_sse,
            raw_body: http.response_body.clone(),
        }
    }

    /// Check if the path indicates an LLM API call
    fn is_llm_api_path(&self, path: &str) -> bool {
        path.contains("/v1/chat/completions") ||
        path.contains("/v1/completions") ||
        path.contains("/v1/messages") ||
        path.contains("/chat/completions") ||
        path.contains("/completions")
    }

    /// Extract provider from path
    fn extract_provider_from_path(&self, path: &str) -> Option<String> {
        if path.contains("anthropic") || path.contains("/v1/messages") {
            Some("anthropic".to_string())
        } else if path.contains("/v1/chat/completions") || path.contains("/v1/completions") {
            Some("openai".to_string())
        } else {
            None
        }
    }

    /// Extract model from parsed message
    fn extract_model_from_message(&self, message: &Option<ParsedApiMessage>) -> Option<String> {
        match message {
            Some(ParsedApiMessage::OpenAICompletion { request, .. }) => {
                request.as_ref().map(|r| r.model.clone())
            }
            Some(ParsedApiMessage::AnthropicMessage { request, .. }) => {
                request.as_ref().map(|r| r.model.clone())
            }
            _ => None,
        }
    }

    /// Generate globally unique ID (unique across restarts)
    fn generate_id(&self) -> String {
        let seq = self.call_counter.fetch_add(1, Ordering::Relaxed);
        format!("{}_{}", self.session_prefix, seq)
    }

    /// 通过进程名匹配 agent registry，返回已知 agent 名称
    fn resolve_agent_name(comm: &str) -> Option<String> {
        let ctx = ProcessContext {
            comm: comm.to_string(),
            cmdline_args: vec![],
            exe_path: String::new(),
        };
        known_agents()
            .iter()
            .find(|m| m.matches(&ctx))
            .map(|m| m.info().name.clone())
    }

    /// Convert OpenAI ChatMessage to parts-based InputMessage
    fn openai_msg_to_input(m: &OpenAIChatMessage) -> InputMessage {
        let role = format!("{:?}", m.role).to_lowercase();
        let mut parts = Vec::new();

        // Reasoning content first
        if let Some(ref rc) = m.reasoning_content {
            if !rc.is_empty() {
                parts.push(MessagePart::Reasoning { content: rc.clone() });
            }
        }

        // For tool role: content is tool_call_response
        if role == "tool" {
            let response_val = m.content.as_ref()
                .map(|c| {
                    let text = c.as_text();
                    // Try to parse as JSON, fall back to string
                    serde_json::from_str::<serde_json::Value>(&text)
                        .unwrap_or_else(|_| serde_json::Value::String(text))
                })
                .unwrap_or(serde_json::Value::Null);
            parts.push(MessagePart::ToolCallResponse {
                id: m.tool_call_id.clone(),
                response: response_val,
            });
        } else {
            // Text content
            if let Some(ref c) = m.content {
                let text = c.as_text();
                if !text.is_empty() {
                    parts.push(MessagePart::Text { content: text });
                }
            }
        }

        // Tool calls
        if let Some(ref tcs) = m.tool_calls {
            for tc in tcs {
                if let Some(part) = Self::parse_openai_tool_call_value(tc) {
                    parts.push(part);
                }
            }
        }

        InputMessage { role, parts, name: m.name.clone() }
    }

    /// Convert OpenAI ChatMessage to parts-based OutputMessage
    fn openai_msg_to_output(m: &OpenAIChatMessage, finish_reason: Option<&str>) -> OutputMessage {
        let role = format!("{:?}", m.role).to_lowercase();
        let mut parts = Vec::new();

        // Reasoning content first
        if let Some(ref rc) = m.reasoning_content {
            if !rc.is_empty() {
                parts.push(MessagePart::Reasoning { content: rc.clone() });
            }
        }

        // Text content
        if let Some(ref c) = m.content {
            let text = c.as_text();
            if !text.is_empty() {
                parts.push(MessagePart::Text { content: text });
            }
        }

        // Tool calls
        if let Some(ref tcs) = m.tool_calls {
            for tc in tcs {
                if let Some(part) = Self::parse_openai_tool_call_value(tc) {
                    parts.push(part);
                }
            }
        }

        OutputMessage {
            role,
            parts,
            name: m.name.clone(),
            finish_reason: finish_reason.map(|s| s.to_string()),
        }
    }

    /// Parse a serde_json::Value tool_call into MessagePart::ToolCall
    fn parse_openai_tool_call_value(tc: &serde_json::Value) -> Option<MessagePart> {
        let func = tc.get("function")?;
        let name = func.get("name")?.as_str()?.to_string();
        let id = tc.get("id").and_then(|v| v.as_str()).map(|s| s.to_string());
        // Parse arguments as JSON object (not string)
        let arguments = func.get("arguments").and_then(|v| {
            match v {
                serde_json::Value::String(s) => serde_json::from_str(s).ok(),
                other => Some(other.clone()),
            }
        });
        Some(MessagePart::ToolCall { id, name, arguments })
    }

    // NOTE: token_record_to_parts and parse_tool_call_strings removed.
    // Tool calls and reasoning are now extracted directly from SSE response body
    // via extract_parts_from_sse_body / parse_sse_response_body.

    /// Parse SSE response body (JSON array of chunks) into a complete OutputMessage.
    ///
    /// Merges content/reasoning deltas and tool_call argument fragments by index.
    /// Extracts finish_reason from the last SSE chunk that has one.
    fn parse_sse_response_body(body: &str, fallback_finish_reason: Option<&str>) -> Option<Vec<OutputMessage>> {
        let (parts, sse_finish_reason) = Self::extract_parts_from_sse_body(body)?;
        if parts.is_empty() {
            return None;
        }
        // Prefer finish_reason from SSE, fall back to caller-supplied value
        let finish_reason = sse_finish_reason
            .or_else(|| fallback_finish_reason.map(|s| s.to_string()));
        Some(vec![OutputMessage {
            role: "assistant".to_string(),
            parts,
            name: None,
            finish_reason,
        }])
    }

    /// Extract MessageParts + finish_reason by aggregating all SSE chunks in response_body.
    ///
    /// Handles OpenAI SSE delta format:
    /// - content deltas → single Text part
    /// - reasoning_content deltas → single Reasoning part
    /// - tool_calls deltas (fragmented by index) → merged ToolCall parts
    /// - finish_reason from the last non-null value in choices
    ///
    /// Returns (parts, finish_reason) or None if no content found.
    fn extract_parts_from_sse_body(body: &str) -> Option<(Vec<MessagePart>, Option<String>)> {
        let chunks: Vec<serde_json::Value> = serde_json::from_str(body).ok()?;

        let mut content_buf = String::new();
        let mut reasoning_buf = String::new();
        let mut finish_reason: Option<String> = None;
        // tool_call delta merging: index -> (id, name, arguments_accumulated)
        let mut tc_map: HashMap<u32, (String, String, String)> = HashMap::new();

        for chunk in &chunks {
            let choices = chunk.get("choices").and_then(|c| c.as_array());
            let choices = match choices {
                Some(c) => c,
                None => continue,
            };
            for choice in choices {
                let delta = match choice.get("delta") {
                    Some(d) => d,
                    None => continue,
                };
                // Content
                if let Some(c) = delta.get("content").and_then(|v| v.as_str()) {
                    content_buf.push_str(c);
                }
                // Reasoning
                if let Some(r) = delta.get("reasoning_content").and_then(|v| v.as_str()) {
                    reasoning_buf.push_str(r);
                }
                // Tool call deltas — merge by index
                if let Some(calls) = delta.get("tool_calls").and_then(|v| v.as_array()) {
                    for tc in calls {
                        let idx = tc.get("index").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
                        let entry = tc_map.entry(idx)
                            .or_insert_with(|| (String::new(), String::new(), String::new()));
                        if let Some(id) = tc.get("id").and_then(|v| v.as_str()) {
                            entry.0 = id.to_string();
                        }
                        if let Some(func) = tc.get("function") {
                            if let Some(name) = func.get("name").and_then(|v| v.as_str()) {
                                entry.1 = name.to_string();
                            }
                            if let Some(args) = func.get("arguments").and_then(|v| v.as_str()) {
                                entry.2.push_str(args);
                            }
                        }
                    }
                }
                // Finish reason — take the last non-null value
                if let Some(fr) = choice.get("finish_reason").and_then(|v| v.as_str()) {
                    finish_reason = Some(fr.to_string());
                }
            }
        }

        let mut parts = Vec::new();

        // Reasoning first
        if !reasoning_buf.is_empty() {
            parts.push(MessagePart::Reasoning { content: reasoning_buf });
        }
        // Text content
        if !content_buf.is_empty() {
            parts.push(MessagePart::Text { content: content_buf });
        }
        // Merged tool calls
        if !tc_map.is_empty() {
            let mut indices: Vec<u32> = tc_map.keys().cloned().collect();
            indices.sort();
            for idx in indices {
                if let Some((id, name, arguments)) = tc_map.remove(&idx) {
                    let parsed_args: Option<serde_json::Value> = if arguments.is_empty() {
                        None
                    } else {
                        serde_json::from_str(&arguments).ok()
                    };
                    parts.push(MessagePart::ToolCall {
                        id: if id.is_empty() { None } else { Some(id) },
                        name,
                        arguments: parsed_args,
                    });
                }
            }
        }

        if parts.is_empty() { None } else { Some((parts, finish_reason)) }
    }
}
