//! Process Event Aggregator
//!
//! Aggregates process events (exec, stdout, exit) by PID into complete process lifecycles.

use std::collections::HashMap;
use crate::probes::proctrace::VariableEvent;
use crate::parser::proctrace::{ParsedProcEvent, ProcEventType};
use super::process::AggregatedProcess;

/// Process Event Aggregator - aggregates process events by PID
#[derive(Debug, Clone)]
pub struct ProcessEventAggregator {
    /// Map of PID to aggregated process data
    pub aggregates: HashMap<u32, AggregatedProcess>,
}

impl ProcessEventAggregator {
    /// Create a new aggregator
    pub fn new() -> Self {
        ProcessEventAggregator {
            aggregates: HashMap::new(),
        }
    }

    /// Process a single variable-length event
    ///
    /// Returns Some(AggregatedProcess) if this event completes an aggregation (process exited),
    /// None otherwise.
    pub fn process_event(&mut self, event: &VariableEvent) -> Option<AggregatedProcess> {
        match event {
            VariableEvent::Exec { header, filename, args } => {
                let pid = header.pid;
                let aggregated = self.aggregates
                    .entry(pid)
                    .or_insert_with(|| {
                        AggregatedProcess::new(
                            pid,
                            header.tid,
                            header.ppid,
                            header.ptid,
                            event.comm_str(),
                            header.timestamp_ns,
                        )
                    });
                aggregated.add_exec(filename.clone(), args.clone(), header.timestamp_ns);
                None
            }
            VariableEvent::Stdout { header, fd, payload } => {
                let pid = header.pid;
                if let Some(aggregated) = self.aggregates.get_mut(&pid) {
                    if *fd == 2 {
                        aggregated.add_stderr(payload, header.timestamp_ns);
                    } else {
                        aggregated.add_stdout(payload, header.timestamp_ns);
                    }
                }
                None
            }
            VariableEvent::Exit { header, .. } => {
                let pid = header.pid;
                if let Some(mut aggregated) = self.aggregates.remove(&pid) {
                    aggregated.mark_complete(header.timestamp_ns);
                    Some(aggregated)
                } else {
                    None
                }
            }
            VariableEvent::Unknown(_) => None,
        }
    }

    /// Process multiple events
    pub fn process_events(&mut self, events: &[VariableEvent]) -> Vec<AggregatedProcess> {
        events.iter().filter_map(|e| self.process_event(e)).collect()
    }

    /// Process a parsed process event
    ///
    /// Returns Some(AggregatedProcess) if this event completes an aggregation (process exited),
    /// None otherwise.
    pub fn process_parsed_event(&mut self, event: &ParsedProcEvent) -> Option<AggregatedProcess> {
        match event.event_type {
            ProcEventType::Exec => {
                let aggregated = self.aggregates
                    .entry(event.pid)
                    .or_insert_with(|| {
                        AggregatedProcess::new(
                            event.pid,
                            event.tid,
                            event.ppid,
                            event.ptid,
                            event.comm.clone(),
                            event.timestamp_ns,
                        )
                    });
                if let Some(ref args) = event.args {
                    let filename = event.comm.clone();
                    aggregated.add_exec(filename, args.clone(), event.timestamp_ns);
                }
                None
            }
            ProcEventType::Stdout => {
                if let Some(aggregated) = self.aggregates.get_mut(&event.pid) {
                    if let Some(ref data) = event.stdout_data {
                        aggregated.add_stdout(data.as_bytes(), event.timestamp_ns);
                    }
                }
                None
            }
            ProcEventType::Exit => {
                if let Some(mut aggregated) = self.aggregates.remove(&event.pid) {
                    aggregated.mark_complete(event.timestamp_ns);
                    Some(aggregated)
                } else {
                    None
                }
            }
        }
    }

    /// Get all incomplete aggregations (running processes)
    pub fn get_incomplete(&self) -> Vec<&AggregatedProcess> {
        self.aggregates.values().filter(|agg| !agg.is_complete).collect()
    }

    /// Clear all aggregations
    pub fn clear(&mut self) {
        self.aggregates.clear();
    }

    /// Check if there are any pending aggregations
    pub fn has_pending(&self) -> bool {
        !self.aggregates.is_empty()
    }

    /// Get the number of pending aggregations
    pub fn pending_count(&self) -> usize {
        self.aggregates.len()
    }
}

impl Default for ProcessEventAggregator {
    fn default() -> Self {
        Self::new()
    }
}
