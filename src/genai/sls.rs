//! SLS (Aliyun Log Service) uploader for GenAI semantic events
//!
//! This module provides a non-blocking uploader that sends GenAI semantic events
//! to Aliyun SLS via a background thread with its own tokio runtime.

use crossbeam_channel::{Sender, Receiver, bounded};
use std::thread;

use crate::config::AgentsightConfig;
use super::semantic::GenAISemanticEvent;
use super::exporter::GenAIExporter;

/// SLS uploader that sends GenAI events to Aliyun Log Service
///
/// Uses a background thread with a dedicated tokio runtime to handle
/// async SLS SDK calls without blocking the main sync pipeline.
pub struct SlsUploader {
    sender: Sender<Vec<GenAISemanticEvent>>,
}

impl SlsUploader {
    /// Create a new SLS uploader from configuration
    ///
    /// Spawns a background thread with a tokio runtime that consumes
    /// events from a channel and uploads them to SLS.
    pub fn new(config: &AgentsightConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let endpoint = config.sls_endpoint.clone()
            .ok_or("SLS endpoint not configured")?;
        let access_key_id = config.sls_access_key_id.clone()
            .ok_or("SLS access key ID not configured")?;
        let access_key_secret = config.sls_access_key_secret.clone()
            .ok_or("SLS access key secret not configured")?;
        let project = config.sls_project.clone()
            .ok_or("SLS project not configured")?;
        let logstore = config.sls_logstore.clone()
            .ok_or("SLS logstore not configured")?;

        // Bounded channel to apply backpressure if SLS is slow
        let (sender, receiver): (Sender<Vec<GenAISemanticEvent>>, Receiver<Vec<GenAISemanticEvent>>) =
            bounded(256);

        // Spawn background thread with its own tokio runtime
        thread::Builder::new()
            .name("sls-uploader".to_string())
            .spawn(move || {
                Self::run_upload_loop(endpoint, access_key_id, access_key_secret, project, logstore, receiver);
            })?;

        log::info!("SLS uploader started (project={}, logstore={})", 
            config.sls_project.as_deref().unwrap_or("?"),
            config.sls_logstore.as_deref().unwrap_or("?"));

        Ok(SlsUploader { sender })
    }

    /// Send events to the background upload thread (non-blocking)
    ///
    /// If the channel is full, the events are dropped with a warning log.
    pub fn send(&self, events: Vec<GenAISemanticEvent>) {
        if events.is_empty() {
            return;
        }
        match self.sender.try_send(events) {
            Ok(_) => {}
            Err(crossbeam_channel::TrySendError::Full(dropped)) => {
                log::warn!("SLS upload channel full, dropping {} events", dropped.len());
            }
            Err(crossbeam_channel::TrySendError::Disconnected(_)) => {
                log::error!("SLS upload thread has disconnected");
            }
        }
    }
}

impl GenAIExporter for SlsUploader {
    fn name(&self) -> &str {
        "aliyun-sls"
    }

    fn export(&self, events: &[GenAISemanticEvent]) {
        self.send(events.to_vec());
    }
}

impl SlsUploader {
    fn run_upload_loop(
        endpoint: String,
        access_key_id: String,
        access_key_secret: String,
        project: String,
        logstore: String,
        receiver: Receiver<Vec<GenAISemanticEvent>>,
    ) {
        use aliyun_log_rust_sdk::{Client, Config, FromConfig};

        // Build tokio runtime for this thread
        let rt = match tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
        {
            Ok(rt) => rt,
            Err(e) => {
                log::error!("Failed to create tokio runtime for SLS uploader: {}", e);
                return;
            }
        };

        // Create SLS client
        let sls_config = match Config::builder()
            .endpoint(&endpoint)
            .access_key(&access_key_id, &access_key_secret)
            .build()
        {
            Ok(c) => c,
            Err(e) => {
                log::error!("Failed to build SLS config: {}", e);
                return;
            }
        };

        let client = match Client::from_config(sls_config) {
            Ok(c) => c,
            Err(e) => {
                log::error!("Failed to create SLS client: {}", e);
                return;
            }
        };

        log::debug!("SLS upload thread started, waiting for events...");

        // Process events from channel
        while let Ok(events) = receiver.recv() {
            let log_group = Self::events_to_log_group(&events);

            rt.block_on(async {
                match client.put_logs(&project, &logstore)
                    .log_group(log_group)
                    .send()
                    .await
                {
                    Ok(_) => {
                        log::debug!("Uploaded {} GenAI events to SLS", events.len());
                    }
                    Err(e) => {
                        log::warn!("Failed to upload to SLS: {}", e);
                    }
                }
            });
        }

        log::info!("SLS upload thread exiting (channel closed)");
    }

    /// 获取实例ID：优先请求阿里云 ECS metadata（超时1秒），失败则回退到 hostname
    pub fn get_instance_id() -> String {
        // 尝试从 ECS metadata service 获取 instance-id
        match ureq::get("http://100.100.100.200/latest/meta-data/instance-id")
            .timeout(std::time::Duration::from_secs(1))
            .call()
        {
            Ok(resp) => {
                if let Ok(body) = resp.into_string() {
                    let id = body.trim().to_string();
                    if !id.is_empty() {
                        log::debug!("Got ECS instance-id: {}", id);
                        return id;
                    }
                }
            }
            Err(e) => {
                log::debug!("ECS metadata not available, falling back to hostname: {}", e);
            }
        }
        // 回退: /etc/hostname -> $HOSTNAME -> "unknown"
        std::fs::read_to_string("/etc/hostname")
            .map(|s| s.trim().to_string())
            .or_else(|_| std::env::var("HOSTNAME"))
            .unwrap_or_else(|_| "unknown".to_string())
    }

    /// Convert GenAI semantic events to SLS LogGroup
    ///
    /// One LLM request = one SLS log entry, all fields flattened with OTel GenAI naming.
    /// No nested JSON wrappers.
    fn events_to_log_group(events: &[GenAISemanticEvent]) -> aliyun_log_sdk_protobuf::LogGroup {
        use aliyun_log_sdk_protobuf::{Log, LogGroup};

        let mut log_group = LogGroup::new();

        // 获取实例ID：优先从阿里云 ECS metadata 获取 instance-id，失败则用 hostname
        let hostname = Self::get_instance_id();

        for event in events {
            let timestamp = chrono::Utc::now().timestamp() as u32;
            let mut log = Log::from_unixtime(timestamp);

            // 每条日志都写入 instance (hostname)
            log.add_content_kv("instance", &hostname);

            match event {
                GenAISemanticEvent::LLMCall(call) => {
                    // ── OTel GenAI Required ──
                    log.add_content_kv("gen_ai.provider.name", &call.provider);
                    log.add_content_kv("gen_ai.request.model", &call.model);
                    log.add_content_kv("gen_ai.operation.name",
                        call.metadata.get("operation_name").map(|s| s.as_str()).unwrap_or("chat"));

                    // ── OTel GenAI Conditionally Required ──
                    if let Some(ref error) = call.error {
                        log.add_content_kv("error.type", error);
                    }
                    if let Some(port) = call.metadata.get("server.port") {
                        log.add_content_kv("server.port", port);
                    }

                    // ── OTel GenAI Recommended ──
                    log.add_content_kv("gen_ai.response.id", &call.call_id);
                    log.add_content_kv("gen_ai.response.model", &call.model);
                    // finish_reason is now inside OutputMessage, extract from first output
                    if let Some(reason) = call.response.messages.first().and_then(|m| m.finish_reason.as_ref()) {
                        log.add_content_kv("gen_ai.response.finish_reasons", &format!("[\"{}\"]", reason));
                    }
                    if let Some(temp) = call.request.temperature {
                        log.add_content_kv("gen_ai.request.temperature", &temp.to_string());
                    }
                    if let Some(max) = call.request.max_tokens {
                        log.add_content_kv("gen_ai.request.max_tokens", &max.to_string());
                    }
                    if let Some(fp) = call.request.frequency_penalty {
                        log.add_content_kv("gen_ai.request.frequency_penalty", &fp.to_string());
                    }
                    if let Some(pp) = call.request.presence_penalty {
                        log.add_content_kv("gen_ai.request.presence_penalty", &pp.to_string());
                    }
                    if let Some(tp) = call.request.top_p {
                        log.add_content_kv("gen_ai.request.top_p", &tp.to_string());
                    }
                    if let Some(tk) = call.request.top_k {
                        log.add_content_kv("gen_ai.request.top_k", &tk.to_string());
                    }
                    if let Some(seed) = call.request.seed {
                        log.add_content_kv("gen_ai.request.seed", &seed.to_string());
                    }
                    if let Some(ref stops) = call.request.stop_sequences {
                        if let Ok(json) = serde_json::to_string(stops) {
                            log.add_content_kv("gen_ai.request.stop_sequences", &json);
                        }
                    }
                    if let Some(ref usage) = call.token_usage {
                        log.add_content_kv("gen_ai.usage.input_tokens", &usage.input_tokens.to_string());
                        log.add_content_kv("gen_ai.usage.output_tokens", &usage.output_tokens.to_string());
                        if let Some(cache_create) = usage.cache_creation_input_tokens {
                            log.add_content_kv("gen_ai.usage.cache_creation.input_tokens", &cache_create.to_string());
                        }
                        if let Some(cache_read) = usage.cache_read_input_tokens {
                            log.add_content_kv("gen_ai.usage.cache_read.input_tokens", &cache_read.to_string());
                        }
                    }
                    if let Some(addr) = call.metadata.get("server.address") {
                        log.add_content_kv("server.address", addr);
                    }
                    // Output type
                    log.add_content_kv("gen_ai.output.type", "text");

                    // ── gen_ai.system_instructions (system role messages) ──
                    let system_msgs: Vec<&super::semantic::InputMessage> = call.request.messages.iter()
                        .filter(|m| m.role == "system")
                        .collect();
                    if !system_msgs.is_empty() {
                        if let Ok(json) = serde_json::to_string(&system_msgs) {
                            log.add_content_kv("gen_ai.system_instructions", &json);
                        }
                    }

                    // ── gen_ai.input.messages (增量：只取最新一轮) ──
                    // 从后往前找最后一条 user message，取它及之后的所有非 system 消息
                    let non_system: Vec<&super::semantic::InputMessage> = call.request.messages.iter()
                        .filter(|m| m.role != "system")
                        .collect();
                    let latest_msgs = if let Some(last_user_idx) = non_system.iter().rposition(|m| m.role == "user") {
                        &non_system[last_user_idx..]
                    } else {
                        &non_system[..]
                    };
                    if !latest_msgs.is_empty() {
                        if let Ok(json) = serde_json::to_string(&latest_msgs) {
                            log.add_content_kv("gen_ai.input.messages", &json);
                        }
                    }

                    // ── gen_ai.output.messages (parts-based with finish_reason) ──
                    if !call.response.messages.is_empty() {
                        if let Ok(json) = serde_json::to_string(&call.response.messages) {
                            log.add_content_kv("gen_ai.output.messages", &json);
                        }
                    }

                    // ── AgentSight extensions ──
                    log.add_content_kv("agentsight.pid", &call.pid.to_string());
                    log.add_content_kv("agentsight.process_name", &call.process_name);
                    if let Some(ref name) = call.agent_name {
                        log.add_content_kv("agentsight.agent.name", name);
                    }
                    log.add_content_kv("agentsight.duration_ns", &call.duration_ns.to_string());
                    log.add_content_kv("agentsight.start_timestamp_ns", &call.start_timestamp_ns.to_string());
                    log.add_content_kv("agentsight.end_timestamp_ns", &call.end_timestamp_ns.to_string());
                    if let Some(method) = call.metadata.get("method") {
                        log.add_content_kv("agentsight.http.method", method);
                    }
                    if let Some(path) = call.metadata.get("path") {
                        log.add_content_kv("agentsight.http.path", path);
                    }
                    if let Some(status) = call.metadata.get("status_code") {
                        log.add_content_kv("agentsight.http.status_code", status);
                    }
                    if call.request.stream || call.metadata.get("is_sse").map(|v| v == "true").unwrap_or(false) {
                        log.add_content_kv("agentsight.stream", "true");
                        if let Some(cnt) = call.metadata.get("sse_event_count") {
                            log.add_content_kv("agentsight.sse_event_count", cnt);
                        }
                    }
                    if let Some(cid) = call.metadata.get("conversation_id") {
                        log.add_content_kv("traceId", cid);
                    }
                    if let Some(uq) = call.metadata.get("user_query") {
                        log.add_content_kv("agentsight.user_query", uq);
                    }
                    if let Some(sid) = call.metadata.get("session_id") {
                        log.add_content_kv("gen_ai.session.id", sid);
                    }
                }
                GenAISemanticEvent::ToolUse(tool) => {
                    log.add_content_kv("gen_ai.operation.name", "tool_use");
                    log.add_content_kv("gen_ai.tool.name", &tool.tool_name);
                    if let Some(ref parent_id) = tool.parent_llm_call_id {
                        log.add_content_kv("gen_ai.response.id", parent_id);
                    }
                    if let Ok(json) = serde_json::to_string(&tool.arguments) {
                        log.add_content_kv("gen_ai.tool.call.arguments", &json);
                    }
                    if let Some(ref result) = tool.result {
                        log.add_content_kv("gen_ai.tool.call.result", result);
                    }
                    log.add_content_kv("agentsight.tool.success", &tool.success.to_string());
                    log.add_content_kv("agentsight.pid", &tool.pid.to_string());
                    if let Some(ref dur) = tool.duration_ns {
                        log.add_content_kv("agentsight.duration_ns", &dur.to_string());
                    }
                    if let Some(ref error) = tool.error {
                        log.add_content_kv("error.type", error);
                    }
                }
                GenAISemanticEvent::AgentInteraction(interaction) => {
                    log.add_content_kv("gen_ai.operation.name", "agent_interaction");
                    log.add_content_kv("agentsight.agent.name", &interaction.agent_name);
                    log.add_content_kv("agentsight.agent.interaction_type", &interaction.interaction_type);
                    log.add_content_kv("agentsight.pid", &interaction.pid.to_string());
                }
                GenAISemanticEvent::StreamChunk(chunk) => {
                    log.add_content_kv("gen_ai.operation.name", "stream_chunk");
                    log.add_content_kv("agentsight.stream.id", &chunk.stream_id);
                    log.add_content_kv("agentsight.stream.chunk_index", &chunk.chunk_index.to_string());
                    log.add_content_kv("agentsight.pid", &chunk.pid.to_string());
                }
            }

            log_group.add_log(log);
        }

        log_group
    }
}
