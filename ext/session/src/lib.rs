// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Portable session IR and parsers for local AI coding-agent transcripts.
//!
//! The crate currently normalizes Claude Code, Codex, and Gemini CLI sessions.
//! It intentionally stops at session data; process correlation, UI, database
//! storage, eBPF collection, and OpenTelemetry export belong in extensions that
//! consume this crate.

mod parser;
mod types;
#[cfg(target_arch = "wasm32")]
mod component;

pub const AGENT_CLAUDE: &str = "claude";
pub const AGENT_CODEX: &str = "codex";
pub const AGENT_GEMINI: &str = "gemini";
pub const AGENT_CURSOR: &str = "cursor";

pub use types::{
    AgentSession, LlmResponse, PlanStep, SessionCache, SessionCandidate, SessionDirStat,
    SessionEvents, TokenUsage, ToolEvent, ToolPath, UserPrompt,
};

pub use parser::{
    agent_source_for_path, codex_exec_prompt, codex_latest_plan, codex_total_token_usage,
    collapse_project_path, command_process_chain, contains_private_marker, count_session_dirs,
    count_session_dirs_in_home, discover_session_files, discover_session_files_in_dir,
    discover_session_files_in_home, fixture_session_path, is_codex_cli_entrypoint,
    normalize_session_log_path, parse_session_content, parse_session_file, parse_session_path,
    path_component_strings, path_group, semantic_task_label, session_candidate_from_path,
    session_log_path_from_str, short_hash, tool_category, truncate_clean,
};
