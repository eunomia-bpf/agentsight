//! Metrics subcommand — print per-agent token usage in Prometheus text format

use agentsight::storage::sqlite::GenAISqliteStore;
use structopt::StructOpt;

/// Print per-agent token usage metrics in Prometheus text format
#[derive(Debug, StructOpt, Clone)]
pub struct MetricsCommand {
    /// Custom database path (defaults to the genai_events.db written by `agentsight trace`)
    #[structopt(long)]
    pub db: Option<String>,
}

impl MetricsCommand {
    pub fn execute(&self) {
        let db_path = self
            .db
            .as_ref()
            .map(|p| std::path::PathBuf::from(p))
            .unwrap_or_else(GenAISqliteStore::default_path);

        let store = match GenAISqliteStore::new_with_path(&db_path) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Error opening database {:?}: {}", db_path, e);
                std::process::exit(1);
            }
        };

        let summaries = match store.get_agent_token_summary() {
            Ok(v) => v,
            Err(e) => {
                eprintln!("Error querying metrics: {}", e);
                std::process::exit(1);
            }
        };

        // ── Prometheus text format output ──────────────────────────────────

        println!("# HELP agentsight_token_input_total Total input tokens consumed by agent (all-time)");
        println!("# TYPE agentsight_token_input_total counter");
        for s in &summaries {
            println!(
                "agentsight_token_input_total{{agent=\"{}\"}} {}",
                escape_label(&s.agent_name),
                s.input_tokens
            );
        }

        println!();
        println!("# HELP agentsight_token_output_total Total output tokens consumed by agent (all-time)");
        println!("# TYPE agentsight_token_output_total counter");
        for s in &summaries {
            println!(
                "agentsight_token_output_total{{agent=\"{}\"}} {}",
                escape_label(&s.agent_name),
                s.output_tokens
            );
        }

        println!();
        println!("# HELP agentsight_token_total_total Total tokens (input+output) consumed by agent (all-time)");
        println!("# TYPE agentsight_token_total_total counter");
        for s in &summaries {
            println!(
                "agentsight_token_total_total{{agent=\"{}\"}} {}",
                escape_label(&s.agent_name),
                s.total_tokens
            );
        }

        println!();
        println!("# HELP agentsight_llm_requests_total Total LLM requests made by agent (all-time)");
        println!("# TYPE agentsight_llm_requests_total counter");
        for s in &summaries {
            println!(
                "agentsight_llm_requests_total{{agent=\"{}\"}} {}",
                escape_label(&s.agent_name),
                s.request_count
            );
        }
    }
}

/// Escape Prometheus label value: backslash → \\, double-quote → \", newline → \n
fn escape_label(s: &str) -> String {
    s.replace('\\', "\\\\")
     .replace('"', "\\\"")
     .replace('\n', "\\n")
}
