//! Unified Analyzer - high-level entry point for analysis
//!
//! This module provides a unified interface for analyzing parsed and aggregated data.
//! It combines AuditAnalyzer, TokenParser, and MessageParser into a single entry point.
//!
//! # Example
//! ```rust,ignore
//! use agentsight::analyzer::Analyzer;
//! use agentsight::aggregator::AggregatedResult;
//!
//! let analyzer = Analyzer::new();
//! 
//! // Analyze aggregated result
//! for result in analyzer.analyze_aggregated(&aggregated_result) {
//!     match result {
//!         AnalysisResult::Audit(record) => { /* handle audit record */ }
//!         AnalysisResult::Token(record) => { /* handle token record */ }
//!         AnalysisResult::Message(msg) => { /* handle parsed API message */ }
//!     }
//! }
//! ```

use crate::aggregator::AggregatedResult;
use crate::parser::sse::ParsedSseEvent;
use crate::tokenizer::LlmTokenizer;
use crate::tokenizer::get_global_tokenizer;
use crate::analyzer::token::extract_response_content;

use super::{AuditAnalyzer, TokenParser, MessageParser, AuditRecord, TokenRecord, TokenUsage, ParsedApiMessage, AnalysisResult, PromptTokenCount, HttpRecord};
use super::result::{TokenConsumptionBreakdown, MessageTokenCount, OutputTokenCount};

/// Token count result for request messages
#[derive(Debug, Clone)]
pub struct RequestTokenCount {
    /// Total input tokens
    pub total_tokens: usize,
    /// Token count by role (system, user, assistant, tool)
    pub by_role: std::collections::HashMap<String, usize>,
    /// Per-message token counts with role information
    pub per_message: Vec<MessageTokenCount>,
    /// Tool definitions token count
    pub tools_tokens: usize,
    /// System prompt token count
    pub system_prompt_tokens: usize,
}

/// Token count result for response content
#[derive(Debug, Clone)]
pub struct ResponseTokenCount {
    /// Total output tokens
    pub total_tokens: usize,
    /// Output token count by content type (text, reasoning, tool_calls)
    pub by_type: std::collections::HashMap<String, usize>,
    /// Per-content-block token counts
    pub per_block: Vec<OutputTokenCount>,
}

/// Count tokens in a request JSON using the provided tokenizer and chat template
///
/// # Arguments
/// * `request_json` - The request JSON (OpenAI format with "messages" array)
/// * `tokenizer` - The tokenizer to use for counting
/// * `chat_template` - The chat template for formatting messages
///
/// # Returns
/// `Some(RequestTokenCount)` if successful, `None` if the request has no messages
///
/// # Example
/// ```rust,ignore
/// let request = serde_json::json!({
///     "model": "qwen3.5-plus",
///     "messages": [
///         {"role": "system", "content": "You are helpful"},
///         {"role": "user", "content": "Hello"}
///     ]
/// });
/// let count = count_request_tokens(&request, tokenizer.as_ref(), template.as_ref())?;
/// println!("Total: {} tokens", count.total_tokens);
/// ```
pub fn count_request_tokens(
    request_json: &serde_json::Value,
    tokenizer: &LlmTokenizer,
    chat_template: &LlmTokenizer,
) -> Option<RequestTokenCount> {
    // Extract messages
    let messages = request_json.get("messages")
        .and_then(|m| m.as_array())?;
    
    if messages.is_empty() {
        return None;
    }

    let mut by_role: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    let mut per_message: Vec<MessageTokenCount> = Vec::new();

    // Prepare messages for apply_chat_template
    let template_messages: Vec<serde_json::Value> = messages.to_vec();

    // Extract tools JSON array for passing to template
    let tools_json: Option<Vec<serde_json::Value>> = request_json.get("tools")
        .and_then(|t| t.as_array())
        .map(|arr| arr.to_vec());

    // Count tools tokens separately (for informational breakdown)
    let mut tools_tokens: usize = tools_json.as_ref()
        .map(|arr| arr.iter()
            .filter_map(|t| serde_json::to_string(t).ok())
            .filter_map(|s| tokenizer.count(&s).ok())
            .sum())
        .unwrap_or(0);

    // Use apply_chat_template_with_tools to format all messages WITH tools
    // This ensures the tools instruction text is included in the total count
    let tools_slice = tools_json.as_deref();
    let total_tokens = match chat_template.apply_chat_template_with_tools(&template_messages, tools_slice, true) {
        Ok(formatted) => tokenizer.count(&formatted).unwrap_or(0),
        Err(e) => {
            log::warn!("Failed to apply chat template with tools: {}", e);
            // Fallback: count raw content + tools separately
            0
        }
    };

    // Count per-message tokens: first calculate raw token counts, then distribute total_tokens by percentage
    // Step 1: Calculate raw token count for each message
    let mut raw_per_message: Vec<(String, usize)> = Vec::new();
    for msg in messages.iter() {
        // Count tokens by serializing entire message (includes content, reasoning_content, etc.)
        let mut tokens = serde_json::to_string(msg)
            .ok()
            .and_then(|s| tokenizer.count(&s).ok())
            .unwrap_or(0);
        let role = msg.get("role").and_then(|r| r.as_str()).unwrap_or("unknown").to_string();
        if role == "tool" {
            tokens += tools_tokens;
            tools_tokens = 0;
        }
        raw_per_message.push((role, tokens));
    }
    
    // Step 2: Calculate total raw tokens and distribute total_tokens by percentage
    let raw_total: usize = raw_per_message.iter().map(|(_, t)| *t).sum();
    
    if raw_total > 0 {
        // Distribute total_tokens proportionally based on raw token percentages
        for (role, raw_tokens) in raw_per_message.iter() {
            let actual_tokens = ((*raw_tokens as f64 / raw_total as f64) * total_tokens as f64).round() as usize;
            *by_role.entry(role.clone()).or_insert(0) += actual_tokens;
            per_message.push(MessageTokenCount {
                role: role.clone(),
                tokens: actual_tokens,
            });
        }
    } else {
        // Fallback: if no raw tokens, just use zeros
        for (role, _) in raw_per_message.iter() {
            per_message.push(MessageTokenCount {
                role: role.clone(),
                tokens: 0,
            });
        }
    }
    let system_prompt_tokens = by_role.get("system").cloned().unwrap_or(0);
    let tools_tokens = by_role.get("tool").cloned().unwrap_or(0);
    Some(RequestTokenCount {
        total_tokens,
        by_role,
        per_message,
        tools_tokens,
        system_prompt_tokens,
    })
}

/// Count tokens in response SSE chunks using the provided tokenizer
///
/// This function applies the Qwen ChatML template format to the response content
/// for accurate token counting, including special tokens like:
/// - `<|im_start|>assistant\n` - response start
/// - `<think>\n...\n</think>\n\n` - reasoning content wrapper  
/// - `<|im_end|>` - response end
/// - Tool call XML format markers
///
/// # Arguments
/// * `response_jsons` - Array of SSE response chunks (each line parsed as JSON)
/// * `tokenizer` - The tokenizer to use for counting
///
/// # Returns
/// `Some(ResponseTokenCount)` if successful, `None` if no content found
///
/// # Example
/// ```rust,ignore
/// // Read response file line by line and parse each line as JSON
/// let lines: Vec<serde_json::Value> = content.lines()
///     .filter_map(|line| serde_json::from_str(line).ok())
///     .collect();
/// let count = count_response_tokens(&lines, tokenizer.as_ref())?;
/// println!("Total: {} tokens", count.total_tokens);
/// ```
pub fn count_response_tokens(
    response_jsons: &[serde_json::Value],
    tokenizer: &LlmTokenizer,
) -> Option<ResponseTokenCount> {
    let mut by_type: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    let mut per_block: Vec<OutputTokenCount> = Vec::new();

    // Accumulate content from all SSE chunks
    let mut all_content = String::new();
    let mut all_reasoning = String::new();
    let mut all_tool_calls = Vec::new();

    for chunk in response_jsons {
        if let Some((content, reasoning, tool_calls)) = extract_response_content(Some(chunk)) {
            if !content.is_empty() {
                all_content.push_str(&content);
            }
            if let Some(r) = reasoning {
                if !r.is_empty() {
                    all_reasoning.push_str(&r);
                }
            }
            for tc in tool_calls {
                if !tc.is_empty() {
                    all_tool_calls.push(tc);
                }
            }
        }
    }

    let mut has_content = false;
    
    // NOTE: API output token count includes:
    // - Model-generated text markers like <think>...</think> (these ARE counted)
    // - NOT special control tokens like <|im_start|>, <|im_end|> (these are NOT counted)
    
    // Add reasoning content with <think> wrapper (model generates these markers)
    if !all_reasoning.is_empty() {
        has_content = true;
        
        // Format: <think>\n{reasoning}\n</think>\n\n
        let reasoning_with_tags = format!("<think>\n{}\n</think>\n\n", all_reasoning);
        let tokens = tokenizer.count(&reasoning_with_tags).unwrap_or(all_reasoning.len() / 4);
        *by_type.entry("reasoning".to_string()).or_insert(0) += tokens;
        per_block.push(OutputTokenCount {
            content_type: "reasoning".to_string(),
            tokens,
        });
    }

    // Add text content
    if !all_content.is_empty() {
        has_content = true;
        
        let tokens = tokenizer.count(&all_content).unwrap_or(all_content.len() / 4);
        *by_type.entry("text".to_string()).or_insert(0) += tokens;
        per_block.push(OutputTokenCount {
            content_type: "text".to_string(),
            tokens,
        });
    }

    // Add tool calls with Qwen template format
    // According to tokenizer_config.json, <tool_call>, <function=...>, <parameter=...> are NOT special tokens,
    // so they ARE counted as output tokens by the API
    //
    // NOTE: For SSE streaming, tool_calls come in chunks:
    // - First chunk: "exec: " (function name + colon)
    // - Following chunks: ": {...}" (colon + arguments fragments)
    // We need to aggregate all chunks first to get the complete tool call
    if !all_tool_calls.is_empty() {
        
        // Aggregate all chunks: first chunk has "name: ", rest have ": fragment"
        let mut aggregated = String::new();
        for tc in &all_tool_calls {
            if aggregated.is_empty() {
                // First chunk contains "name: " or just "name:"
                aggregated.push_str(tc);
            } else {
                // Subsequent chunks start with ": ", skip the leading ": "
                let fragment = tc.strip_prefix(": ").unwrap_or(tc);
                aggregated.push_str(fragment);
            }
        }
        
        // Now parse the aggregated "name: arguments" string
        let (name, arguments) = if let Some(pos) = aggregated.find(": ") {
            (&aggregated[..pos], &aggregated[pos + 2..])
        } else if let Some(pos) = aggregated.find(':') {
            // Handle case where there's no space after colon
            (&aggregated[..pos], &aggregated[pos + 1..])
        } else {
            ("", aggregated.as_str())
        };
        
        // Build Qwen tool_call template format:
        // <tool_call>
        // <function={name}>
        // <parameter={arg_name}>
        // {arg_value}
        // </parameter>
        // </function>
        // </tool_call>
        let mut tool_call_str = String::new();
        tool_call_str.push_str("<tool_call>\n<function=");
        tool_call_str.push_str(name);
        tool_call_str.push_str(">\n");
        
        // Parse arguments JSON and format each parameter
        if let Ok(args_json) = serde_json::from_str::<serde_json::Value>(arguments) {
            if let Some(obj) = args_json.as_object() {
                for (arg_name, arg_value) in obj {
                    tool_call_str.push_str("<parameter=");
                    tool_call_str.push_str(arg_name);
                    tool_call_str.push_str(">\n");
                    // Format value: if string use as-is, otherwise use JSON
                    let value_str = if let Some(s) = arg_value.as_str() {
                        s.to_string()
                    } else {
                        arg_value.to_string()
                    };
                    tool_call_str.push_str(&value_str);
                    tool_call_str.push_str("\n</parameter>\n");
                }
            }
        } else {
            // Fallback: use raw arguments string
            tool_call_str.push_str(arguments);
            tool_call_str.push_str("\n");
        }
        
        tool_call_str.push_str("</function>\n</tool_call>");
        
        has_content = true;
        
        let tokens = tokenizer.count(&tool_call_str).unwrap_or(tool_call_str.len() / 4);
        *by_type.entry("tool_calls".to_string()).or_insert(0) += tokens;
        per_block.push(OutputTokenCount {
            content_type: "tool_calls".to_string(),
            tokens,
        });
    }

    if has_content {
        let total_tokens: usize = by_type.values().sum();
        Some(ResponseTokenCount {
            total_tokens,
            by_type,
            per_block,
        })
    } else {
        None
    }
}

/// Unified analyzer for extracting records from parsed/aggregated data
///
/// This analyzer provides a unified entry point for analysis, combining:
/// - `AuditAnalyzer`: Extracts audit records from aggregated results
/// - `TokenParser`: Extracts token usage from SSE events
/// - `MessageParser`: Parses LLM API request/response bodies
/// - Optional tokenizer for computing prompt token counts
pub struct Analyzer {
    audit: AuditAnalyzer,
    token: TokenParser,
    message: MessageParser,
    /// Optional tokenizer for computing prompt token counts
    tokenizer: Option<LlmTokenizer>,
    /// Optional chat template for formatting messages
    chat_template: Option<LlmTokenizer>,
}

impl Default for Analyzer {
    fn default() -> Self {
        Self::new()
    }
}

impl Analyzer {
    /// Create a new unified analyzer without tokenizer
    pub fn new() -> Self {
        Analyzer {
            audit: AuditAnalyzer::new(),
            token: TokenParser::new(),
            message: MessageParser::new(),
            tokenizer: None,
            chat_template: None,
        }
    }

    /// Create a new unified analyzer with tokenizer for prompt token counting
    ///
    /// # Arguments
    /// * `tokenizer` - The tokenizer to use for computing prompt token counts
    /// * `chat_template` - The chat template to use for formatting messages
    ///
    /// # Example
    /// ```rust,ignore
    /// use agentsight::analyzer::Analyzer;
    /// use agentsight::tokenizer::{QwenTokenizer, ChatTemplateType};
    ///
    /// let tokenizer = QwenTokenizer::from_file("/path/to/tokenizer.json", "Qwen3.5")?;
    /// let chat_template = ChatTemplateType::Qwen.create_template();
    /// let analyzer = Analyzer::with_tokenizer(Box::new(tokenizer), chat_template);
    /// ```
    pub fn with_tokenizer(
        tokenizer: LlmTokenizer,
        chat_template: LlmTokenizer,
    ) -> Self {
        Analyzer {
            audit: AuditAnalyzer::new(),
            token: TokenParser::new(),
            message: MessageParser::new(),
            tokenizer: Some(tokenizer),
            chat_template: Some(chat_template),
        }
    }

    /// Analyze an aggregated result
    ///
    /// Returns `AnalysisResult::Audit` for LLM calls and process actions,
    /// `AnalysisResult::Token` for SSE streams containing token usage,
    /// or `AnalysisResult::Message` for parsed LLM API request/response bodies.
    pub fn analyze_aggregated(&self, result: &AggregatedResult) -> Vec<AnalysisResult> {
        log::debug!("Analyzing aggregated result({})", result.result_type());
        let mut results = Vec::new();

        // 1. Audit analysis
        if let Some(record) = self.audit.analyze(result) {
            results.push(AnalysisResult::Audit(record));
        }

        // 2. Token analysis - extract from SSE events
        let token_result = match result {
            AggregatedResult::SseComplete(pair) => {
                let pid = pair.request.source_event.pid;
                let comm = pair.request.source_event.comm_str();
                self.extract_token_from_sse(&pair.response.sse_events, pid, &comm)
            }
            AggregatedResult::ResponseOnly { response, .. } if !response.sse_events.is_empty() => {
                let pid = response.pid();
                let comm = response.parsed.source_event.comm_str();
                self.extract_token_from_sse(&response.sse_events, pid, &comm)
            }
            _ => None,
        };
        
        if let Some(record) = token_result {
            results.push(AnalysisResult::Token(record));
        } else {
            // Fallback: manually compute tokens using get_global_tokenizer
            if let Some(record) = self.compute_tokens_manually(result) {
                results.push(AnalysisResult::Token(record));
            }
        }

        // 5. Token consumption analysis - breakdown by message role
        // This runs for any HTTP request with messages (not just SSE responses)
        // if let Some(breakdown) = self.analyze_token_consumption(result) {
        //     results.push(AnalysisResult::TokenConsumption(breakdown));
        // }

        // 3. Message analysis - parse LLM API request/response bodies
        // if let Some(msg_result) = self.extract_message_from_http(result) {
        //     // 3.1 Compute prompt tokens if tokenizer is available
        //     if let Some(ref tokenizer) = self.tokenizer {
        //         if let Some(ref chat_template) = self.chat_template {
        //             if let Some(prompt_tokens) = self.compute_prompt_tokens(&msg_result, tokenizer.as_ref(), chat_template.as_ref()) {
        //                 results.push(AnalysisResult::PromptTokens(prompt_tokens));
        //             }
        //         }
        //     }
        //     results.push(msg_result);
        // }

        // 4. HTTP data export - extract raw HTTP request/response data
        if let Some(http_record) = self.extract_http_record(result) {
            results.push(AnalysisResult::Http(http_record));
        }

        

        results
    }

    /// Extract parsed API message from HTTP request/response bodies
    fn extract_message_from_http(&self, result: &AggregatedResult) -> Option<AnalysisResult> {
        match result {
            AggregatedResult::HttpComplete(pair) => {
                let req_body = pair.request.json_body();
                let resp_body = pair.response.parsed.json_body();
                self.analyze_message(&pair.request.path, req_body.as_ref(), resp_body.as_ref())
            }
            AggregatedResult::SseComplete(pair) => {
                let req_body = pair.request.json_body();
                // For SSE responses, parse from SSE events
                self.analyze_message_with_sse(
                    &pair.request.path,
                    req_body.as_ref(),
                    &pair.response.sse_events,
                )
            }
            AggregatedResult::RequestOnly { request, .. } => {
                let req_body = request.json_body();
                self.analyze_message(&request.path, req_body.as_ref(), None)
            }
            AggregatedResult::ResponseOnly { .. } 
            | AggregatedResult::ProcessComplete(_) 
            | AggregatedResult::Http2Frames { .. }
            | AggregatedResult::Http2StreamComplete(_) => None,
        }
    }

    /// Parse API message from HTTP request body and SSE events
    ///
    /// This method parses LLM API request body and SSE response events
    /// to reconstruct the complete message.
    pub fn analyze_message_with_sse(
        &self,
        path: &str,
        request_body: Option<&serde_json::Value>,
        sse_events: &[ParsedSseEvent],
    ) -> Option<AnalysisResult> {
        self.message.parse_by_path_with_sse(path, request_body, sse_events)
            .map(AnalysisResult::Message)
    }

    /// Extract token usage from SSE events (reverse search, first match wins)
    fn extract_token_from_sse(
        &self,
        sse_events: &[ParsedSseEvent],
        pid: u32,
        comm: &str,
    ) -> Option<TokenRecord> {
        let usage = sse_events.iter().rev()
            .find_map(|e| self.token.parse_event(e))?;

        let mut record = TokenRecord::new(
            pid,
            comm.to_string(),
            usage.provider.to_string(),
            usage.input_tokens,
            usage.output_tokens,
        )
        .with_model(usage.model.clone().unwrap_or_default())
        .with_cache_tokens(
            usage.cache_creation_input_tokens.unwrap_or(0),
            usage.cache_read_input_tokens.unwrap_or(0),
        );

        // NOTE: tool_calls and reasoning_content extraction from SSE events
        // is handled in genai::builder via direct SSE response body parsing.

        if record.total_tokens() ==0 {
            return None;
        }

        Some(record)
    }

    /// Manually compute token counts using get_global_tokenizer
    ///
    /// This method is called when token extraction from SSE events fails.
    /// It uses the global tokenizer to compute input and output tokens
    /// from the request messages and response content.
    fn compute_tokens_manually(&self, result: &AggregatedResult) -> Option<TokenRecord> {
        // Extract context from the aggregated result (only SseComplete has request info)
        let (pid, comm, request_json, sse_events, path) = match result {
            AggregatedResult::SseComplete(pair) => (
                pair.request.source_event.pid,
                pair.request.source_event.comm_str(),
                pair.request.json_body(),
                &pair.response.sse_events,
                pair.request.path.as_str(),
            ),
            // ResponseOnly doesn't have request info, cannot compute tokens
            _ => return None,
        };

        // Get request JSON
        let request_json_ref = request_json.as_ref()?;

        // Extract model name
        let model = request_json_ref.get("model")
            .and_then(|m| m.as_str())
            .unwrap_or("unknown");

        // Try to get tokenizer for the model
        let tokenizer = match get_global_tokenizer(model) {
            Ok(t) => t,
            Err(e) => {
                log::debug!("Failed to get tokenizer for model '{}': {}", model, e);
                return None;
            }
        };

        // Extract provider from path
        let provider = if path.contains("anthropic") {
            "anthropic"
        } else {
            "openai"
        };

        // Count input tokens from request messages using chat template
        let input_tokens = if let Some(messages) = request_json_ref.get("messages").and_then(|m| m.as_array()) {
            if messages.is_empty() {
                0
            } else {
                // Clone messages for in-place modification of tool_calls.arguments
                let mut msgs = messages.clone();
                
                // Process tool_calls arguments: parse JSON string to object in place
                for msg in msgs.iter_mut() {
                    if let Some(tool_calls) = msg.get_mut("tool_calls").and_then(|tc| tc.as_array_mut()) {
                        for tool_call in tool_calls.iter_mut() {
                            if let Some(func) = tool_call.get_mut("function") {
                                if let Some(args) = func.get("arguments") {
                                    if let Some(args_str) = args.as_str() {
                                        // Try to parse arguments string as JSON object
                                        if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(args_str) {
                                            func["arguments"] = parsed;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Extract tools JSON array for passing to template
                let tools_json: Option<Vec<serde_json::Value>> = request_json_ref.get("tools")
                    .and_then(|t| t.as_array())
                    .map(|arr| arr.to_vec());
                let tools_slice = tools_json.as_deref();
                
                // Apply chat template with tools to get the actual prompt sent to LLM
                match tokenizer.apply_chat_template_with_tools(&msgs, tools_slice, true) {
                    Ok(formatted) => tokenizer.count(&formatted).unwrap_or(0) as u64,
                    Err(e) => {
                        log::warn!("Failed to apply chat template: {}, falling back to raw count", e);
                        // Fallback: count raw message content
                        let mut total = 0u64;
                        for msg in &msgs {
                            if let Ok(msg_str) = serde_json::to_string(msg) {
                                total += tokenizer.count(&msg_str).unwrap_or(0) as u64;
                            }
                        }
                        total
                    }
                }
            }
        } else {
            0
        };

        // Count output tokens from SSE events content
        let output_tokens = {
            let mut all_content = String::new();
            let mut all_reasoning = String::new();
            let mut all_tool_calls = Vec::new();

            for event in sse_events {
                if let Some(chunk) = event.json_body() {
                    if let Some((content, reasoning, tool_calls)) = extract_response_content(Some(&chunk)) {
                        if !content.is_empty() {
                            all_content.push_str(&content);
                        }
                        if let Some(r) = reasoning {
                            if !r.is_empty() {
                                all_reasoning.push_str(&r);
                            }
                        }
                        for tc in tool_calls {
                            if !tc.is_empty() {
                                all_tool_calls.push(tc);
                            }
                        }
                    }
                }
            }

            let mut total = 0u64;

            // Count reasoning tokens
            if !all_reasoning.is_empty() {
                let reasoning_with_tags = format!("<think>\n{}\n</think>\n\n", all_reasoning);
                total += tokenizer.count(&reasoning_with_tags).unwrap_or(0) as u64;
            }

            // Count text tokens
            if !all_content.is_empty() {
                total += tokenizer.count(&all_content).unwrap_or(0) as u64;
            }

            // Count tool call tokens
            if !all_tool_calls.is_empty() {
                let aggregated_tool_calls = all_tool_calls.join("");
                total += tokenizer.count(&aggregated_tool_calls).unwrap_or(0) as u64;
            }

            total
        };

        // Create TokenRecord
        let record = TokenRecord::new(
            pid,
            comm.to_string(),
            provider.to_string(),
            input_tokens,
            output_tokens,
        )
        .with_model(model.to_string());

        Some(record)
    }

    /// Extract HTTP request/response record from an aggregated result
    ///
    /// Exports the raw HTTP exchange data including method, path, headers,
    /// body, status code, and SSE event payloads for persistence.
    fn extract_http_record(&self, result: &AggregatedResult) -> Option<HttpRecord> {
        match result {
            AggregatedResult::HttpComplete(pair) => {
                let req = &pair.request;
                let resp = &pair.response;

                let request_body = req.json_body()
                    .map(|v| serde_json::to_string(&v).unwrap_or_default())
                    .or_else(|| {
                        let body = req.body();
                        if body.is_empty() { None }
                        else { Some(String::from_utf8_lossy(body).to_string()) }
                    });

                let response_body = resp.parsed.json_body()
                    .map(|v| serde_json::to_string(&v).unwrap_or_default())
                    .or_else(|| {
                        let body = resp.parsed.body();
                        if body.is_empty() { None }
                        else { Some(String::from_utf8_lossy(body).to_string()) }
                    });

                Some(HttpRecord {
                    timestamp_ns: req.source_event.timestamp_ns,
                    pid: req.source_event.pid,
                    comm: req.source_event.comm_str(),
                    method: req.method.clone(),
                    path: req.path.clone(),
                    status_code: resp.status_code(),
                    request_headers: serde_json::to_string(&req.headers).unwrap_or_default(),
                    request_body,
                    response_headers: serde_json::to_string(&resp.parsed.headers).unwrap_or_default(),
                    response_body,
                    duration_ns: resp.end_timestamp_ns().saturating_sub(req.source_event.timestamp_ns),
                    is_sse: false,
                    sse_event_count: 0,
                })
            }
            AggregatedResult::SseComplete(pair) => {
                let req = &pair.request;
                let resp = &pair.response;

                let request_body = req.json_body()
                    .map(|v| serde_json::to_string(&v).unwrap_or_default())
                    .or_else(|| {
                        let body = req.body();
                        if body.is_empty() { None }
                        else { Some(String::from_utf8_lossy(body).to_string()) }
                    });

                // For SSE responses, aggregate all SSE event JSON payloads
                let sse_json_bodies = resp.json_body();
                let response_body = if sse_json_bodies.is_empty() {
                    None
                } else {
                    serde_json::to_string(&sse_json_bodies).ok()
                };

                Some(HttpRecord {
                    timestamp_ns: req.source_event.timestamp_ns,
                    pid: req.source_event.pid,
                    comm: req.source_event.comm_str(),
                    method: req.method.clone(),
                    path: req.path.clone(),
                    status_code: resp.status_code(),
                    request_headers: serde_json::to_string(&req.headers).unwrap_or_default(),
                    request_body,
                    response_headers: serde_json::to_string(&resp.parsed.headers).unwrap_or_default(),
                    response_body,
                    duration_ns: resp.duration_ns(),
                    is_sse: true,
                    sse_event_count: resp.sse_event_count(),
                })
            }
            AggregatedResult::RequestOnly { request, .. } => {
                let request_body = request.json_body()
                    .map(|v| serde_json::to_string(&v).unwrap_or_default())
                    .or_else(|| {
                        let body = request.body();
                        if body.is_empty() { None }
                        else { Some(String::from_utf8_lossy(body).to_string()) }
                    });

                Some(HttpRecord {
                    timestamp_ns: request.source_event.timestamp_ns,
                    pid: request.source_event.pid,
                    comm: request.source_event.comm_str(),
                    method: request.method.clone(),
                    path: request.path.clone(),
                    status_code: 0,
                    request_headers: serde_json::to_string(&request.headers).unwrap_or_default(),
                    request_body,
                    response_headers: String::new(),
                    response_body: None,
                    duration_ns: 0,
                    is_sse: false,
                    sse_event_count: 0,
                })
            }
            AggregatedResult::Http2StreamComplete(stream) => {
                let request_body = stream.request_body_str();

                // Try SSE parsing first, fallback to regular text if it fails
                // This is more robust than checking content-type header (which may fail due to HPACK)
                let (response_body, sse_event_count) = if let Some(sse_json) = stream.response_sse_json_array() {
                    // Successfully parsed as SSE
                    let event_count = sse_json.as_array().map(|a| a.len()).unwrap_or(0);
                    (Some(serde_json::to_string(&sse_json).unwrap_or_default()), event_count)
                } else {
                    // Not SSE, try regular JSON or raw text
                    let body = stream.response_json_body()
                        .map(|v| serde_json::to_string(&v).unwrap_or_default())
                        .or_else(|| stream.response_body_str());
                    (body, 0)
                };

                Some(HttpRecord {
                    timestamp_ns: stream.start_timestamp_ns,
                    pid: stream.pid(),
                    comm: stream.comm(),
                    method: stream.method(),
                    path: stream.path(),
                    status_code: stream.status_code(),
                    request_headers: stream.request_headers_json(),
                    request_body,
                    response_headers: stream.response_headers_json(),
                    response_body,
                    duration_ns: stream.end_timestamp_ns.saturating_sub(stream.start_timestamp_ns),
                    is_sse: sse_event_count > 0,
                    sse_event_count,
                })
            }
            // ProcessComplete and ResponseOnly don't have request info, skip
            _ => None,
        }
    }

    /// Analyze an SSE event for token usage
    ///
    /// Returns `TokenUsage` if the event contains usage information.
    /// Use `analyze_sse_event_full` to get a complete `TokenRecord`.
    pub fn analyze_sse_event(&self, event: &ParsedSseEvent) -> Option<TokenUsage> {
        self.token.parse_event(event)
    }

    /// Analyze an SSE event and build a complete TokenRecord
    ///
    /// This method extracts token usage and combines it with process metadata
    /// to create a complete record suitable for storage.
    pub fn analyze_sse_event_full(
        &self,
        event: &ParsedSseEvent,
        pid: u32,
        comm: &str,
    ) -> Option<TokenRecord> {
        let usage = self.token.parse_event(event)?;
        
        Some(TokenRecord::new(
            pid,
            comm.to_string(),
            usage.provider.to_string(),
            usage.input_tokens,
            usage.output_tokens,
        )
        .with_model(usage.model.clone().unwrap_or_default())
        .with_cache_tokens(
            usage.cache_creation_input_tokens.unwrap_or(0),
            usage.cache_read_input_tokens.unwrap_or(0),
        ))
    }

    /// Analyze an SSE event and return AnalysisResult
    ///
    /// Convenience method that wraps the result in `AnalysisResult::Token`.
    pub fn analyze_sse_as_result(
        &self,
        event: &ParsedSseEvent,
        pid: u32,
        comm: &str,
    ) -> Option<AnalysisResult> {
        self.analyze_sse_event_full(event, pid, comm)
            .map(AnalysisResult::Token)
    }

    /// Compute prompt tokens for a parsed API message
    ///
    /// This method uses the tokenizer to compute the actual prompt token count
    /// from the request messages.
    fn compute_prompt_tokens(
        &self,
        msg_result: &AnalysisResult,
        tokenizer: &LlmTokenizer,
        chat_template: &LlmTokenizer,
    ) -> Option<PromptTokenCount> {
        let messages = match msg_result {
            AnalysisResult::Message(ParsedApiMessage::OpenAICompletion { request, .. }) => {
                request.as_ref()?.messages.clone()
            }
            _ => return None,
        };

        let provider = match msg_result {
            AnalysisResult::Message(msg) => msg.provider().to_string(),
            _ => "unknown".to_string(),
        };

        let model = match msg_result {
            AnalysisResult::Message(msg) => msg.model().unwrap_or("unknown").to_string(),
            _ => "unknown".to_string(),
        };

        let message_count = messages.len();

        // Convert messages to JSON values
        let messages_json: Vec<serde_json::Value> = messages
            .iter()
            .filter_map(|m| serde_json::to_value(m).ok())
            .collect();

        // Apply chat template and count tokens
        match chat_template.apply_chat_template(&messages_json, true) {
            Ok(formatted_prompt) => {
                match tokenizer.count(&formatted_prompt) {
                    Ok(prompt_tokens) => {
                        // Compute per-message token counts
                        let per_message_tokens: Vec<usize> = messages
                            .iter()
                            .filter_map(|m| {
                                let msg_json = serde_json::to_value(m).ok()?;
                                let content = msg_json.get("content")?.as_str()?.to_string();
                                tokenizer.count(&content).ok()
                            })
                            .collect();

                        Some(PromptTokenCount {
                            provider,
                            model,
                            message_count,
                            prompt_tokens,
                            per_message_tokens,
                            formatted_prompt,
                        })
                    }
                    Err(e) => {
                        log::warn!("Failed to count tokens: {}", e);
                        None
                    }
                }
            }
            Err(e) => {
                log::warn!("Failed to apply chat template: {}", e);
                None
            }
        }
    }

    /// Get reference to the audit analyzer
    pub fn audit_analyzer(&self) -> &AuditAnalyzer {
        &self.audit
    }

    /// Get reference to the token parser
    pub fn token_parser(&self) -> &TokenParser {
        &self.token
    }

    /// Get reference to the message parser
    pub fn message_parser(&self) -> &MessageParser {
        &self.message
    }

    /// Parse API message from HTTP request/response bodies
    ///
    /// This method parses LLM API request and response bodies based on the
    /// HTTP path to detect the provider (OpenAI or Anthropic).
    ///
    /// # Arguments
    /// * `path` - The HTTP request path (e.g., "/v1/chat/completions")
    /// * `request_body` - Optional JSON body from the HTTP request
    /// * `response_body` - Optional JSON body from the HTTP response
    ///
    /// # Returns
    /// * `Some(AnalysisResult::Message)` if parsing succeeds
    /// * `None` if the path doesn't match a known LLM API endpoint
    pub fn analyze_message(
        &self,
        path: &str,
        request_body: Option<&serde_json::Value>,
        response_body: Option<&serde_json::Value>,
    ) -> Option<AnalysisResult> {
        self.message.parse_by_path(path, request_body, response_body)
            .map(AnalysisResult::Message)
    }

    /// Parse API message and return the raw ParsedApiMessage
    ///
    /// Use this method when you need direct access to the parsed message
    /// without the AnalysisResult wrapper.
    pub fn parse_message(
        &self,
        path: &str,
        request_body: Option<&serde_json::Value>,
        response_body: Option<&serde_json::Value>,
    ) -> Option<ParsedApiMessage> {
        self.message.parse_by_path(path, request_body, response_body)
    }

    /// Compute token consumption using apply_chat_template for accurate counting
    ///
    /// This function directly uses the Jinja2 template to format messages and count tokens,
    /// avoiding intermediate conversions and providing more accurate results.
    fn compute_token_consumption_with_template(
        &self,
        messages: &[serde_json::Value],
        model: &str,
        provider: &str,
        tools: Vec<String>,
        system_prompt: Option<String>,
        response_jsons: &[serde_json::Value],
        pid: u32,
        comm: String,
    ) -> Option<TokenConsumptionBreakdown> {
        let (tokenizer, chat_template) = match (&self.tokenizer, &self.chat_template) {
            (Some(t), Some(ct)) => (t, ct),
            _ => {
                log::warn!("Tokenizer or chat template not available, cannot compute accurate token consumption");
                return None;
            }
        };

        let mut by_role: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
        let mut per_message: Vec<MessageTokenCount> = Vec::new();

        // Prepare messages for apply_chat_template
        let mut template_messages: Vec<serde_json::Value> = messages.to_vec();
        
        // Add system prompt as first message if present and not already in messages
        if let Some(ref system) = system_prompt {
            if !template_messages.is_empty() && template_messages[0].get("role") != Some(&serde_json::Value::String("system".to_string())) {
                let system_msg = serde_json::json!({
                    "role": "system",
                    "content": system
                });
                template_messages.insert(0, system_msg);
            }
        }

        // Count tools tokens
        let tools_tokens: usize = tools.iter()
            .filter_map(|tool| tokenizer.count(tool).ok())
            .sum();

        // Use apply_chat_template to format all messages and count total tokens
        let total_msg_tokens = match chat_template.apply_chat_template(&template_messages, true) {
            Ok(formatted) => tokenizer.count(&formatted).unwrap_or(0),
            Err(e) => {
                log::warn!("Failed to apply chat template: {}", e);
                // Fallback: count raw content
                messages.iter()
                    .filter_map(|m| m.get("content").and_then(|c| c.as_str()))
                    .filter_map(|c| tokenizer.count(c).ok())
                    .sum()
            }
        };

        // Count per-message tokens using incremental approach
        for (i, msg) in messages.iter().enumerate() {
            let partial_messages: Vec<serde_json::Value> = template_messages.iter().take(i + 1).cloned().collect();
            let tokens = match chat_template.apply_chat_template(&partial_messages, false) {
                Ok(formatted) => tokenizer.count(&formatted).unwrap_or(0),
                Err(_) => {
                    // Fallback: count content only
                    msg.get("content").and_then(|c| c.as_str())
                        .and_then(|c| tokenizer.count(c).ok())
                        .unwrap_or(0)
                }
            };
            
            // Calculate this message's tokens by subtracting previous total
            let prev_total: usize = per_message.iter().map(|m| m.tokens).sum();
            let msg_tokens = tokens.saturating_sub(prev_total);
            
            let role = msg.get("role").and_then(|r| r.as_str()).unwrap_or("unknown").to_string();
            *by_role.entry(role.clone()).or_insert(0) += msg_tokens;
            
            per_message.push(MessageTokenCount {
                role,
                tokens: msg_tokens,
            });
        }

        // Count system prompt tokens separately
        let system_prompt_tokens = if let Some(ref system) = system_prompt {
            tokenizer.count(system).unwrap_or(system.len() / 4)
        } else {
            0
        };

        // Total input = tools + all messages (system is included in messages)
        let total_input = tools_tokens + total_msg_tokens;

        // Compute output token breakdown from response
        let (output_by_type, output_per_block) = self.compute_output_token_breakdown_from_json(
            response_jsons,
            tokenizer,
            chat_template,
        );

        let total_output_tokens: usize = output_by_type.values().sum();

        Some(TokenConsumptionBreakdown {
            timestamp_ns: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0),
            pid,
            comm,
            provider: provider.to_string(),
            model: model.to_string(),
            total_input_tokens: total_input,
            total_output_tokens,
            by_role,
            per_message,
            tools_tokens,
            system_prompt_tokens,
            output_by_type,
            output_per_block,
        })
    }

    /// Compute output token breakdown from SSE response JSONs
    ///
    /// Directly processes SSE chunks using extract_response_content which now supports
    /// both "message" and "delta" formats, eliminating the need for aggregate_sse_chunks.
    fn compute_output_token_breakdown_from_json(
        &self,
        response_jsons: &[serde_json::Value],
        tokenizer: &LlmTokenizer,
        _chat_template: &LlmTokenizer,
    ) -> (std::collections::HashMap<String, usize>, Vec<OutputTokenCount>) {
        let mut output_by_type: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
        let mut output_per_block: Vec<OutputTokenCount> = Vec::new();

        // Accumulate content from all SSE chunks (extract_response_content now supports delta format)
        let mut all_content = String::new();
        let mut all_reasoning = String::new();
        let mut all_tool_calls = Vec::new();

        for chunk in response_jsons {
            if let Some((content, reasoning, tool_calls)) = extract_response_content(Some(chunk)) {
                if !content.is_empty() {
                    all_content.push_str(&content);
                }
                if let Some(r) = reasoning {
                    if !r.is_empty() {
                        all_reasoning.push_str(&r);
                    }
                }
                for tc in tool_calls {
                    if !tc.is_empty() {
                        all_tool_calls.push(tc);
                    }
                }
            }
        }

        // Handle text content
        if !all_content.is_empty() {
            let tokens = tokenizer.count(&all_content).unwrap_or(all_content.len() / 4);
            *output_by_type.entry("text".to_string()).or_insert(0) += tokens;
            output_per_block.push(OutputTokenCount {
                content_type: "text".to_string(),
                tokens,
            });
        }

        // Handle reasoning content
        if !all_reasoning.is_empty() {
            let tokens = tokenizer.count(&all_reasoning).unwrap_or(all_reasoning.len() / 4);
            *output_by_type.entry("reasoning".to_string()).or_insert(0) += tokens;
            output_per_block.push(OutputTokenCount {
                content_type: "reasoning".to_string(),
                tokens,
            });
        }

        // Handle tool calls - aggregate all tool calls and count once
        if !all_tool_calls.is_empty() {
            let aggregated_tool_calls = all_tool_calls.join("");
            let tokens = tokenizer.count(&aggregated_tool_calls).unwrap_or(aggregated_tool_calls.len() / 4);
            *output_by_type.entry("tool_calls".to_string()).or_insert(0) += tokens;
            output_per_block.push(OutputTokenCount {
                content_type: "tool_calls".to_string(),
                tokens,
            });
        }

        (output_by_type, output_per_block)
    }

    /// Analyze AggregatedResult and extract token consumption breakdown
    ///
    /// This is a convenience method that combines extract_token_data and
    /// compute_token_consumption into a single call.
    pub fn analyze_token_consumption(&self, result: &AggregatedResult) -> Option<TokenConsumptionBreakdown> {
        // Extract context (pid, comm) from the aggregated result (SseComplete only)
        let (pid, comm, request_json, response_jsons, path) = match result {
            AggregatedResult::SseComplete(pair) => (
                pair.request.source_event.pid,
                pair.request.source_event.comm_str(),
                pair.request.json_body(),
                // For SSE responses, get all SSE event JSONs for aggregation
                {
                    let mut res = pair.response.parsed.json_body().map_or(vec![], |x| vec![x]);
                    res.extend(pair.response.json_body());
                    res
                },
                pair.request.path.clone(),
            ),
            _ => return None,
        };

        // Get tokenizer and chat template
        let (tokenizer, chat_template) = match (&self.tokenizer, &self.chat_template) {
            (Some(t), Some(ct)) => (t, ct),
            _ => {
                log::warn!("Tokenizer or chat template not available, cannot compute accurate token consumption");
                return None;
            }
        };

        // Get request JSON reference
        let request_json_ref = request_json.as_ref()?;

        // Extract model
        let model = request_json_ref.get("model")
            .and_then(|m| m.as_str())
            .unwrap_or("unknown")
            .to_string();

        // Extract provider from path
        let provider = if path.contains("anthropic") {
            "anthropic"
        } else {
            "openai"
        }.to_string();

        // Count request tokens
        let request_count = count_request_tokens(request_json_ref, tokenizer, chat_template)?;

        // Count response tokens
        let response_count = count_response_tokens(&response_jsons, tokenizer)?;

        // Build TokenConsumptionBreakdown from request and response counts
        Some(TokenConsumptionBreakdown {
            timestamp_ns: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0),
            pid,
            comm,
            provider,
            model,
            total_input_tokens: request_count.total_tokens,
            total_output_tokens: response_count.total_tokens,
            by_role: request_count.by_role,
            per_message: request_count.per_message,
            tools_tokens: request_count.tools_tokens,
            system_prompt_tokens: request_count.system_prompt_tokens,
            output_by_type: response_count.by_type,
            output_per_block: response_count.per_block,
        })
    }
}
