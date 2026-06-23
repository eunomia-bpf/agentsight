// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Portable session IR, parsers, discovery, and process matching for local AI
//! coding-agent transcripts.
//!
//! The crate currently normalizes Claude Code, Codex, and Gemini CLI sessions.
//! It intentionally stops at session data and process/session correlation; UI,
//! database storage, eBPF collection, and OpenTelemetry export belong in
//! applications that consume this crate.

mod parser;
mod process_match;
mod types;

// Re-export constants
pub const AGENT_CLAUDE: &str = "claude";
pub const AGENT_CODEX: &str = "codex";
pub const AGENT_GEMINI: &str = "gemini";

pub const TRACE_EBPF_FILE: &str = "ebpf_file";
pub const TRACE_PROC_FD: &str = "proc_fd";
pub const TRACE_STICKY_BINDING: &str = "sticky";
pub const TRACE_RECENT_CWD: &str = "cwd_recent";
pub const SOURCE_SESSION_PROCESS_MATCH: &str = "agent_session.process_match";

// Re-export types
pub use types::{AgentSession, SessionCache, SessionCandidate, SessionDirStat, TokenUsage};

// Re-export parser functions
pub use parser::{
    agent_source_for_path, codex_exec_prompt, count_session_dirs, discover_session_files,
    discover_session_files_in_home, fixture_session_path, is_codex_cli_entrypoint,
    normalize_session_log_path, parse_session_content, parse_session_file, parse_session_path,
    session_log_path_from_str,
};

// Re-export process matching types and functions
pub use process_match::{
    LiveProcessCandidate, ProcessKey, ProcessTree, SessionProcessInput, SessionProcessMatch,
    SessionProcessMatcher, SessionProcessMatches,
};
