//! ATIF (Agent Trajectory Interchange Format) module
//!
//! Provides ATIF v1.6 data structures and conversion logic for exporting
//! AgentSight GenAI data to the standardized trajectory format.
//!
//! This module is independent from the `genai` module — it only depends on
//! storage query result types and `genai::semantic` types for deserialization.

pub mod schema;
pub mod converter;

pub use schema::{
    AtifDocument, AtifAgent, AtifStep, AtifToolCall,
    AtifObservation, AtifObservationResult,
    AtifStepMetrics, AtifFinalMetrics,
    SCHEMA_VERSION,
};
pub use converter::{convert_trace_to_atif, convert_session_to_atif};
