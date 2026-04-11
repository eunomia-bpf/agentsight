//! GenAI Semantic Event Storage
//!
//! This module provides storage capabilities for GenAI semantic events,
//! including LLM calls, tool uses, and agent interactions.

use std::path::PathBuf;
use std::fs::{File, OpenOptions};
use std::io::{Write, BufWriter, BufRead, BufReader};
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};

use super::semantic::GenAISemanticEvent;
use super::exporter::GenAIExporter;

/// Storage for GenAI semantic events
pub struct GenAIStore {
    /// Path to the storage file
    path: PathBuf,
}

impl GenAIStore {
    /// Create a new GenAI store with the given path
    pub fn new(path: &PathBuf) -> Self {
        // Ensure parent directory exists
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).ok();
        }
        
        GenAIStore {
            path: path.clone(),
        }
    }

    /// Get default storage path
    pub fn default_path() -> PathBuf {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        PathBuf::from(home).join(".agentsight/genai_events.jsonl")
    }

    /// Add a GenAI semantic event to storage
    pub fn add(&self, event: &GenAISemanticEvent) -> Result<(), Box<dyn std::error::Error>> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        
        let mut writer = BufWriter::new(file);
        let json_line = serde_json::to_string(event)?;
        writeln!(writer, "{}", json_line)?;
        writer.flush()?;
        
        Ok(())
    }

    /// Add multiple events
    pub fn add_batch(&self, events: &[GenAISemanticEvent]) -> Result<(), Box<dyn std::error::Error>> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        
        let mut writer = BufWriter::new(file);
        for event in events {
            let json_line = serde_json::to_string(event)?;
            writeln!(writer, "{}", json_line)?;
        }
        writer.flush()?;
        
        Ok(())
    }

    /// Read all events from storage
    pub fn read_all(&self) -> Result<Vec<GenAISemanticEvent>, Box<dyn std::error::Error>> {
        if !self.path.exists() {
            return Ok(Vec::new());
        }

        let file = File::open(&self.path)?;
        let reader = BufReader::new(file);
        let mut events = Vec::new();

        for line in reader.lines() {
            let line = line?;
            if line.trim().is_empty() {
                continue;
            }
            let event: GenAISemanticEvent = serde_json::from_str(&line)?;
            events.push(event);
        }

        Ok(events)
    }

    /// Query LLM calls within a time range
    pub fn query_llm_calls(
        &self,
        start_time: Option<DateTime<Utc>>,
        end_time: Option<DateTime<Utc>>,
    ) -> Result<Vec<super::semantic::LLMCall>, Box<dyn std::error::Error>> {
        let events = self.read_all()?;
        let mut calls = Vec::new();

        for event in events {
            if let GenAISemanticEvent::LLMCall(call) = event {
                let call_time = DateTime::from_timestamp_nanos(call.start_timestamp_ns as i64);
                
                if let Some(start) = start_time {
                    if call_time < start {
                        continue;
                    }
                }
                
                if let Some(end) = end_time {
                    if call_time > end {
                        continue;
                    }
                }
                
                calls.push(call);
            }
        }

        Ok(calls)
    }

    /// Query events by process ID
    pub fn query_by_pid(&self, pid: i32) -> Result<Vec<GenAISemanticEvent>, Box<dyn std::error::Error>> {
        let events = self.read_all()?;
        Ok(events.into_iter().filter(|event| {
            match event {
                GenAISemanticEvent::LLMCall(call) => call.pid == pid,
                GenAISemanticEvent::ToolUse(tool) => tool.pid == pid,
                GenAISemanticEvent::AgentInteraction(interaction) => interaction.pid == pid,
                GenAISemanticEvent::StreamChunk(chunk) => chunk.pid == pid,
            }
        }).collect())
    }

    /// Get statistics about stored events
    pub fn get_stats(&self) -> Result<GenAIStoreStats, Box<dyn std::error::Error>> {
        let events = self.read_all()?;
        
        let mut stats = GenAIStoreStats {
            total_events: events.len(),
            llm_calls: 0,
            tool_uses: 0,
            agent_interactions: 0,
            stream_chunks: 0,
            total_input_tokens: 0,
            total_output_tokens: 0,
        };

        for event in events {
            match event {
                GenAISemanticEvent::LLMCall(call) => {
                    stats.llm_calls += 1;
                    if let Some(usage) = &call.token_usage {
                        stats.total_input_tokens += usage.input_tokens as u64;
                        stats.total_output_tokens += usage.output_tokens as u64;
                    }
                }
                GenAISemanticEvent::ToolUse(_) => stats.tool_uses += 1,
                GenAISemanticEvent::AgentInteraction(_) => stats.agent_interactions += 1,
                GenAISemanticEvent::StreamChunk(_) => stats.stream_chunks += 1,
            }
        }

        Ok(stats)
    }

    /// Clear all events
    pub fn clear(&self) -> Result<(), Box<dyn std::error::Error>> {
        if self.path.exists() {
            std::fs::remove_file(&self.path)?;
        }
        Ok(())
    }
}

/// Statistics about stored GenAI events
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenAIStoreStats {
    /// Total number of events
    pub total_events: usize,
    /// Number of LLM calls
    pub llm_calls: usize,
    /// Number of tool uses
    pub tool_uses: usize,
    /// Number of agent interactions
    pub agent_interactions: usize,
    /// Number of stream chunks
    pub stream_chunks: usize,
    /// Total input tokens
    pub total_input_tokens: u64,
    /// Total output tokens
    pub total_output_tokens: u64,
}

impl GenAIExporter for GenAIStore {
    fn name(&self) -> &str {
        "jsonl-file"
    }

    fn export(&self, events: &[GenAISemanticEvent]) {
        if let Err(e) = self.add_batch(events) {
            log::warn!("Failed to store GenAI events to JSONL: {}", e);
        }
    }
}
