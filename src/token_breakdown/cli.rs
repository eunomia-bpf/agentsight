//! CLI subcommand for ChatML token breakdown analysis from Chrome Trace
//!
//! Usage:
//! ```bash
//! agentsight analyze-chatml --chrome-trace <trace.json> [--tokenizer-path <path>] [--model <name>] [--pretty]
//! ```

use std::path::Path;
use structopt::StructOpt;

use crate::chrome_trace::ChromeTraceEvent;
use crate::tokenizer::LlmTokenizer;

use super::breakdown::compute_breakdown;
use super::classifier::classify_document;
use super::lexer::parse_chatml;
use super::types::ResponseData;

/// Analyze ChatML token breakdown from Chrome Trace events
#[derive(Debug, StructOpt)]
pub struct AnalyzeChatmlCommand {
    /// Path to Chrome Trace file to read events from
    #[structopt(long = "chrome-trace", parse(from_os_str))]
    pub chrome_trace: std::path::PathBuf,

    /// Path to tokenizer.json file (defaults to ./tokenizer.json, supports TOKENIZER_PATH env var)
    #[structopt(
        long = "tokenizer-path",
        env = "TOKENIZER_PATH",
        default_value = "tokenizer.json"
    )]
    pub tokenizer_path: String,

    /// Model name for display in output
    #[structopt(long, default_value = "qwen3.5-plus")]
    pub model: String,

    /// Pretty-print JSON output
    #[structopt(long)]
    pub pretty: bool,
}

impl AnalyzeChatmlCommand {
    pub fn execute(&self) {
        if let Err(e) = self.run() {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    }

    fn run(&self) -> anyhow::Result<()> {
        // Read and parse Chrome Trace file
        let events = Self::parse_chrome_trace(&self.chrome_trace)?;
        // Process each request/response as independent events
        self.process_trace_events(&events)?;

        Ok(())
    }

    /// Process trace events - each http.request and http.response is an independent event
    fn process_trace_events(&self, events: &[ChromeTraceEvent]) -> anyhow::Result<()> {
        // Load tokenizer and chat template
        let p = Path::new(&self.tokenizer_path);
        let (tokenizer, chat_template): (LlmTokenizer, LlmTokenizer) =
            if p.exists() {
                let llm_tok = LlmTokenizer::from_file(p, p)?;
                // Use the same tokenizer for both tokenization and chat template
                (llm_tok.clone(), llm_tok)
            } else {
                // Fallback: use default template
                let chat_template = LlmTokenizer::from_file("tokenizer.json", "tokenizer_config.json")?;
                (chat_template.clone(), chat_template)
            };

        // Sort events by timestamp to ensure correct order
        let mut sorted_events: Vec<ChromeTraceEvent> = events.to_vec();
        sorted_events.sort_by_key(|e| e.ts);

        // Process each event directly (no intermediate extraction)
        let mut breakdowns = Vec::new();
        let mut event_idx = 0;

        for event in &sorted_events {
            let classified = match event.cat.as_str() {
                "http.request" => {
                    // Extract messages and tools from request body and process directly
                    if let Some(ref args) = event.args {
                        if let Some(body) = args.get("body") {
                            let (messages, tools) = if let Some(body_str) = body.as_str() {
                                serde_json::from_str::<serde_json::Value>(body_str)
                                    .ok()
                                    .map(|v| {
                                        let msgs = v.get("messages").cloned();
                                        let tools = v.get("tools").and_then(|t| t.as_array().cloned());
                                        (msgs, tools)
                                    })
                                    .unwrap_or((None, None))
                            } else {
                                let msgs = body.get("messages").cloned();
                                let tools = body.get("tools").and_then(|t| t.as_array().cloned());
                                (msgs, tools)
                            };

                            if let Some(msgs) = messages.and_then(|v| v.as_array().cloned()) {
                                event_idx += 1;
                                let chatml_text = if let Some(tools_arr) = tools {
                                    chat_template.apply_chat_template_with_tools(&msgs, Some(&tools_arr), true)?
                                } else {
                                    chat_template.apply_chat_template(&msgs, true)?
                                };
                                println!("{}", chatml_text);
                                let doc = parse_chatml(&chatml_text)?;
                                Some(classify_document(&doc.blocks, None))
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                }
                "http.response" => {
                    // Extract response data from SSE events
                    if let Some(ref args) = event.args {
                        if let Some(sse_events) = args.get("sse_events").and_then(|v| v.as_array())
                        {
                            event_idx += 1;
                            let response = Self::extract_response_from_sse(sse_events);
                            Some(classify_document(&[], Some(response)))
                        } else {
                            None
                        }
                    } else {
                        None
                    }
                }
                _ => None, // Ignore other event types
            };

            if let Some(classified) = classified {
                let source_path = format!("{}_{}", event.cat, event_idx);
                let breakdown = compute_breakdown(&classified, &tokenizer, &source_path)?;
                breakdowns.push(breakdown);
            }
        }

        if breakdowns.is_empty() {
            return Err(anyhow::anyhow!(
                "No valid http.request or http.response events found in Chrome Trace."
            ));
        }

        // Output JSON array of all breakdowns
        let json = if self.pretty {
            serde_json::to_string_pretty(&breakdowns)?
        } else {
            serde_json::to_string(&breakdowns)?
        };
        println!("{}", json);

        Ok(())
    }

    /// Parse Chrome Trace file and return list of events
    fn parse_chrome_trace(path: &std::path::Path) -> anyhow::Result<Vec<ChromeTraceEvent>> {
        let content = std::fs::read_to_string(path).map_err(|e| {
            anyhow::anyhow!("Failed to read Chrome Trace file '{}': {}", path.display(), e)
        })?;

        // Chrome trace files are JSON arrays, but may have trailing commas
        // Try standard JSON array parsing first
        match serde_json::from_str::<Vec<ChromeTraceEvent>>(&content) {
            Ok(events) => Ok(events),
            Err(e) => {
                // Try to parse with relaxed format (handle trailing commas)
                Self::parse_trace_relaxed(&content).map_err(|_| {
                    anyhow::anyhow!("Failed to parse Chrome Trace file '{}': {}", path.display(), e)
                })
            }
        }
    }

    /// Parse Chrome Trace file with relaxed format (handle trailing commas)
    fn parse_trace_relaxed(content: &str) -> anyhow::Result<Vec<ChromeTraceEvent>> {
        // Remove trailing commas before ] to handle non-standard JSON
        let cleaned = content
            .trim()
            .trim_start_matches('[')
            .trim_end_matches(']')
            .trim();

        if cleaned.is_empty() {
            return Ok(Vec::new());
        }

        // Split by lines and parse each event
        let mut events = Vec::new();
        for line in cleaned.lines() {
            let line = line.trim().trim_end_matches(',');
            if line.is_empty() {
                continue;
            }
            match serde_json::from_str::<ChromeTraceEvent>(line) {
                Ok(event) => events.push(event),
                Err(e) => {
                    eprintln!("Warning: Failed to parse trace event: {}", e);
                }
            }
        }

        Ok(events)
    }

    /// Extract response data from SSE events array
    fn extract_response_from_sse(sse_events: &[serde_json::Value]) -> ResponseData {
        let mut content_parts = Vec::new();
        let mut reasoning_parts = Vec::new();
        let mut tool_calls = Vec::new();

        for event in sse_events {
            // Parse the data field which contains JSON string
            if let Some(data_str) = event.get("data").and_then(|v| v.as_str()) {
                // Skip [DONE] marker
                if data_str == "[DONE]" {
                    continue;
                }

                // Parse the JSON data
                if let Ok(data_json) = serde_json::from_str::<serde_json::Value>(data_str) {
                    // Extract content and reasoning_content from choices[].delta
                    if let Some(choices) = data_json.get("choices").and_then(|v| v.as_array()) {
                        for choice in choices {
                            if let Some(delta) = choice.get("delta") {
                                // Extract content
                                if let Some(content) = delta.get("content").and_then(|v| v.as_str()) {
                                    if !content.is_empty() {
                                        content_parts.push(content.to_string());
                                    }
                                }
                                // Extract reasoning_content
                                if let Some(reasoning) = delta.get("reasoning_content").and_then(|v| v.as_str()) {
                                    if !reasoning.is_empty() {
                                        reasoning_parts.push(reasoning.to_string());
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        ResponseData {
            content: content_parts,
            reasoning_content: if reasoning_parts.is_empty() {
                None
            } else {
                Some(reasoning_parts.join(""))
            },
            tool_calls,
        }
    }
}
