//! AgentSight CLI - AI Agent observability tool
//!
//! This binary provides commands to:
//! - `token`: Query token consumption data
//! - `trace`: Trace agent activity via eBPF
//! - `audit`: Query audit events
//! - `discover`: Discover running AI agents

use structopt::StructOpt;

mod cli;
use cli::{token::TokenCommand, trace::TraceCommand, audit::AuditCommand, discover::DiscoverCommand};
#[cfg(feature = "server")]
use cli::serve::ServeCommand;
use agentsight::token_breakdown::AnalyzeChatmlCommand;

#[derive(Debug, StructOpt)]
#[structopt(name = "agentsight", about = "AI Agent observability tool - trace processes, SSL traffic, and LLM API calls via eBPF")]
pub enum Command {
    /// Query token consumption data
    Token(TokenCommand),
    /// Trace agent activity (default)
    Trace(TraceCommand),
    /// Query audit events
    Audit(AuditCommand),
    /// Discover running AI agents on the system
    Discover(DiscoverCommand),
    /// Analyze a ChatML file and output token consumption breakdown
    AnalyzeChatml(AnalyzeChatmlCommand),
    /// Start the API server
    #[cfg(feature = "server")]
    Serve(ServeCommand),
}

fn main() {
    let cmd = Command::from_args();
    
    match cmd {
        Command::Token(token_cmd) => token_cmd.execute(),
        Command::Trace(trace_cmd) => trace_cmd.execute(),
        Command::Audit(audit_cmd) => audit_cmd.execute(),
        Command::Discover(discover_cmd) => discover_cmd.execute(),
        Command::AnalyzeChatml(cmd) => cmd.execute(),
        #[cfg(feature = "server")]
        Command::Serve(serve_cmd) => serve_cmd.execute(),
    }
}
