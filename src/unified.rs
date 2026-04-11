//! AgentSight - Unified entry point for AI Agent observability
//!
//! This module provides the main `AgentSight` struct that orchestrates the entire
//! data pipeline: probes → parser → aggregator → analyzer → storage.
//!
//! # Architecture
//!
//! ```text
//! ┌─────────────────────────────────────────────────────────────────────┐
//! │                            AgentSight                                │
//! ├─────────────────────────────────────────────────────────────────────┤
//! │   probes     parser    aggregator    analyzer    genai    storage    │
//! │     ↓          ↓           ↓            ↓          ↓        ↓       │
//! │   Event   ParsedMessage  Aggregated   Analysis  Semantic  持久化    │
//! │                          Result       Result    Events              │
//! │                                                  ↓                  │
//! │                                            GenAI Storage            │
//! └─────────────────────────────────────────────────────────────────────┘
//! ```

use anyhow::{Context, Result};
use std::path::Path;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

use crate::aggregator::Aggregator;
use crate::analyzer::Analyzer;
use crate::config::{self, AgentsightConfig};
use crate::discovery::AgentScanner;
use crate::event::Event;
use crate::genai::{GenAIBuilder, GenAIExporter, GenAIStore, SlsUploader};
use crate::parser::Parser;
use crate::probes::{Probes, ProbesPoller};
use crate::storage::{
    SqliteConfig, Storage, StorageBackend, TimePeriod, TokenQuery, TokenQueryResult,
};
use crate::storage::sqlite::GenAISqliteStore;
use crate::tokenizer::LlmTokenizer;

/// Main AgentSight struct for tracing AI agent activity
///
/// This is the unified entry point that orchestrates:
/// - `Probes`: eBPF-based event capture
/// - `Parser`: Message parsing
/// - `Aggregator`: Event aggregation
/// - `Analyzer`: Analysis and record extraction
/// - `Storage`: Persistence
/// - `AgentScanner`: Process lifecycle tracking
pub struct AgentSight {
    /// BPF probes manager
    probes: Probes,
    /// Message parser (unified)
    parser: Parser,
    /// Event aggregator (unified)
    aggregator: Aggregator,
    /// Unified analyzer
    analyzer: Analyzer,
    /// GenAI semantic builder
    genai_builder: GenAIBuilder,
    /// Pluggable GenAI event exporters (JSONL, SLS, etc.)
    genai_exporters: Vec<Box<dyn GenAIExporter>>,
    /// Unified storage
    storage: Storage,
    /// Agent scanner for process lifecycle tracking
    scanner: AgentScanner,
    /// Poller handle
    _poller: ProbesPoller,
    /// Running flag
    running: Arc<AtomicBool>,
    /// Event counter
    event_count: u64,
}

/// Result of processing an event
#[derive(Debug)]
pub struct ProcessResult {
    /// Number of events processed so far
    pub event_count: u64,
}

impl AgentSight {
    /// Create a new AgentSight instance from configuration
    ///
    /// # Arguments
    /// * `config` - AgentsightConfig containing all configuration parameters
    ///
    /// # Example
    /// ```rust,ignore
    /// use agentsight::{AgentSight, AgentsightConfig};
    ///
    /// let config = AgentsightConfig::new();
    /// let mut sight = AgentSight::new(config)?;
    /// ```
    pub fn new(config: AgentsightConfig) -> Result<Self> {
        config.apply_verbose();

        // Create probes - agent discovery is handled by AgentScanner via ProcMon events
        let mut probes =
            Probes::new(&[], config.target_uid).context("Failed to create probes")?;

        // Attach procmon for process monitoring
        probes.attach().context("Failed to attach probes")?;

        // Create scanner and scan for existing agent processes
        let mut scanner = AgentScanner::new();
        let existing_agents = scanner.scan();

        // Attach SSL probes to already-running agents
        for agent in &existing_agents {
            Self::attach_process_internal(&mut probes, agent.pid, &agent.agent_info.name);
        }

        // Start polling (non-blocking)
        let _poller = probes.run().context("Failed to start probe poller")?;

        // Initialize unified storage based on config
        let storage = Self::create_storage(&config)?;

        // Build GenAI exporters
        let mut genai_exporters: Vec<Box<dyn GenAIExporter>> = Vec::new();

        // Always add local JSONL exporter
        genai_exporters.push(Box::new(GenAIStore::new(&GenAIStore::default_path())));

        // Add SLS exporter if configured, otherwise fallback to SQLite
        if config.sls_enabled() {
            match SlsUploader::new(&config) {
                Ok(uploader) => {
                    log::info!("SLS exporter enabled");
                    genai_exporters.push(Box::new(uploader));
                }
                Err(e) => {
                    log::warn!("Failed to initialize SLS exporter: {}", e);
                }
            }
        } else {
            // No SLS credentials configured, use SQLite as local storage
            match GenAISqliteStore::new() {
                Ok(store) => {
                    log::info!("SQLite GenAI exporter enabled (SLS not configured)");
                    genai_exporters.push(Box::new(store));
                }
                Err(e) => {
                    log::warn!("Failed to initialize SQLite GenAI exporter: {}", e);
                }
            }
        }

        // Create analyzer with tokenizer if configured
        let analyzer = if let Some(ref tokenizer_path) = config.tokenizer_path {
            if Path::new(tokenizer_path).exists() {
                // Assume tokenizer_config.json is in the same directory
                let config_path = Path::new(tokenizer_path)
                    .parent()
                    .map(|p| p.join("tokenizer_config.json"))
                    .unwrap_or_else(|| Path::new("tokenizer_config.json").to_path_buf());
                
                match LlmTokenizer::from_file(tokenizer_path, &config_path) {
                    Ok(tokenizer) => {
                        log::info!(
                            "Tokenizer loaded from: {:?}",
                            tokenizer_path
                        );
                        Analyzer::with_tokenizer(tokenizer.clone(), tokenizer)
                    }
                    Err(e) => {
                        log::warn!("Failed to load tokenizer from {:?}: {}. Using analyzer without tokenizer.", tokenizer_path, e);
                        Analyzer::new()
                    }
                }
            } else {
                log::warn!("Tokenizer file not found: {:?}. Using analyzer without tokenizer.", tokenizer_path);
                Analyzer::new()
            }
        } else {
            Analyzer::new()
        };

        log::info!(
            "AgentSight initialized: {} existing agent(s), {} GenAI exporter(s)",
            existing_agents.len(),
            genai_exporters.len(),
        );

        Ok(AgentSight {
            probes,
            parser: Parser::new(),
            aggregator: Aggregator::new(),
            analyzer,
            genai_builder: GenAIBuilder::new(),
            genai_exporters,
            storage,
            scanner,
            _poller,
            running: Arc::new(AtomicBool::new(true)),
            event_count: 0,
        })
    }

    /// Create storage backend from configuration
    fn create_storage(config: &AgentsightConfig) -> Result<Storage> {
        let sqlite_config = SqliteConfig {
            base_path: config.storage_base_path.clone(),
            db_name: config.db_name.clone(),
            audit_table: config.audit_table.clone(),
            token_table: config.token_table.clone(),
            http_table: config.http_table.clone(),
            token_consumption_table: "token_consumption".to_string(),
            retention_days: config.retention_days,
            purge_interval: config.purge_interval,
        };
        Storage::with_sqlite_config(&sqlite_config)
    }

    /// Check if running
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// Get a clone of the running flag for use in signal handlers
    pub fn running_flag(&self) -> Arc<AtomicBool> {
        Arc::clone(&self.running)
    }

    /// Get event count
    pub fn event_count(&self) -> u64 {
        self.event_count
    }

    /// Attach SSL probes to a specific agent process
    pub fn attach_process(&mut self, pid: u32, agent_name: &str) {
        Self::attach_process_internal(&mut self.probes, pid, agent_name);
    }

    /// Internal helper to attach SSL probes to a process
    fn attach_process_internal(probes: &mut Probes, pid: u32, agent_name: &str) {
        log::debug!("Attaching to pid {}, agent name: {}", pid, agent_name);
        if let Err(e) = probes.attach_process(pid as i32) {
            log::error!("Failed to attach SSL probe to pid {}: {}", pid, e);
        } else {
            log::info!("Attached to agent: {} (pid={})", agent_name, pid);
        }
    }

    /// Detach SSL probes from a specific agent process
    pub fn detach_process(&mut self, pid: u32, agent_name: &str) {
        log::debug!("Detaching from pid {}, agent name: {}", pid, agent_name);
        let _ = self.probes.remove_traced_pid(pid).inspect_err(|e| {
            log::error!("failed to delete {pid} from traced pid map: {e}");
        });
    }

    /// Try to receive and process the next event (non-blocking)
    /// Returns None if no event is available
    pub fn try_process(&mut self) -> Option<ProcessResult> {
        if !self.running.load(Ordering::SeqCst) {
            return None;
        }

        let event = self.probes.try_recv()?;
        self.event_count += 1;

        log::debug!("Processing event: {:?}", event.event_type());

        // Handle ProcMon events for agent lifecycle tracking
        if let Event::ProcMon(ref procmon_event) = event {
            self.handle_procmon_event(procmon_event);
            return None;
        }

        // Parse the event
        let result = self.parser.parse_event(event);

        // Process messages through aggregator
        let aggregated_results = self.aggregator.process_result(result);

        // Analyze and store results
        for agg_result in &aggregated_results {
            // Original analysis and storage pipeline
            let analysis_results = self.analyzer.analyze_aggregated(agg_result);

            // Build GenAI semantic events from analysis results (reuse extracted data)
            let genai_events = self.genai_builder.build(&analysis_results);

            // Export GenAI semantic events to all registered exporters
            if !genai_events.is_empty() {
                for exporter in &self.genai_exporters {
                    exporter.export(&genai_events);
                    log::debug!("Exported {} GenAI events via '{}'", genai_events.len(), exporter.name());
                }
            }
            
            // Store analysis results
            for analysis_result in &analysis_results {
                if let Err(e) = self.storage.store(analysis_result) {
                    log::warn!("Failed to store analysis result: {}", e);
                } else {
                    log::debug!("Analysis result saved");
                }
            }
        }

        Some(ProcessResult {
            event_count: self.event_count,
        })
    }

    /// Handle ProcMon event for agent lifecycle tracking
    fn handle_procmon_event(&mut self, event: &crate::probes::procmon::Event) {
        use crate::probes::procmon::Event as ProcMonEvent;

        match event {
            ProcMonEvent::Exec { pid, comm, .. } => {
                // Check if this is a known agent and start tracking
                if let Some(agent) = self.scanner.on_process_create(*pid, comm) {
                    let agent_name = agent.agent_info.name.clone();
                    self.attach_process(*pid, &agent_name);
                }
            }
            ProcMonEvent::Exit { pid, .. } => {
                // Remove from tracking if it was an agent
                if let Some(agent) = self.scanner.on_process_exit(*pid) {
                    let agent_name = agent.agent_info.name.clone();
                    self.detach_process(*pid, &agent_name);
                }
            }
        }
    }

    /// Run the event loop (blocking)
    pub fn run(&mut self) -> Result<u64> {
        log::debug!("Agent discovery running via ProcMon events");

        // Main event loop
        while self.running.load(Ordering::SeqCst) {
            if let Some(result) = self.try_process() {
                log::trace!("[Event {}] Processed", result.event_count);
            } else {
                // No event available, sleep briefly
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
        }

        Ok(self.event_count)
    }

    /// Shutdown gracefully
    pub fn shutdown(&mut self) {
        self.running.store(false, Ordering::SeqCst);
        // poller will be dropped automatically when AgentSight is dropped
    }

    /// Get reference to aggregator
    pub fn aggregator(&self) -> &Aggregator {
        &self.aggregator
    }

    /// Get mutable reference to aggregator
    pub fn aggregator_mut(&mut self) -> &mut Aggregator {
        &mut self.aggregator
    }

    /// Get reference to analyzer
    pub fn analyzer(&self) -> &Analyzer {
        &self.analyzer
    }

    /// Get reference to storage
    pub fn storage(&self) -> &Storage {
        &self.storage
    }

    /// Get reference to GenAI exporters
    pub fn genai_exporters(&self) -> &[Box<dyn GenAIExporter>] {
        &self.genai_exporters
    }

    /// Add a custom GenAI exporter at runtime
    pub fn add_genai_exporter(&mut self, exporter: Box<dyn GenAIExporter>) {
        log::info!("Registered GenAI exporter: '{}'", exporter.name());
        self.genai_exporters.push(exporter);
    }

    /// Get reference to agent scanner
    pub fn scanner(&self) -> &AgentScanner {
        &self.scanner
    }

    /// Get mutable reference to agent scanner
    pub fn scanner_mut(&mut self) -> &mut AgentScanner {
        &mut self.scanner
    }

    /// Query token usage by time period
    pub fn query_tokens(&self, period: TimePeriod) -> TokenQueryResult {
        let query = TokenQuery::new(self.storage.token());
        query.by_period(period)
    }

    /// Query token usage by last N hours
    pub fn query_tokens_by_hours(&self, hours: u64) -> TokenQueryResult {
        let query = TokenQuery::new(self.storage.token());
        query.by_hours(hours)
    }

    /// Query token usage with comparison
    pub fn query_tokens_with_compare(&self, period: TimePeriod) -> TokenQueryResult {
        let query = TokenQuery::new(self.storage.token());
        query.by_period_with_compare(period)
    }

    /// Query token usage with breakdown
    pub fn query_tokens_with_breakdown(&self, period: TimePeriod) -> TokenQueryResult {
        let query = TokenQuery::new(self.storage.token());
        query.by_period_with_breakdown(period)
    }

    /// Full token query with comparison and breakdown
    pub fn query_tokens_full(&self, period: TimePeriod) -> TokenQueryResult {
        let query = TokenQuery::new(self.storage.token());
        query.full_query(period)
    }
}

impl Drop for AgentSight {
    fn drop(&mut self) {
        self.shutdown();
    }
}
