//! Audit query subcommand

use agentsight::{AuditEventType, AuditStore, SqliteConfig};
use structopt::StructOpt;

/// Audit query subcommand
#[derive(Debug, StructOpt, Clone)]
pub struct AuditCommand {
    /// Query last N hours (e.g. 24)
    #[structopt(long)]
    pub last: Option<u64>,

    /// Filter by PID
    #[structopt(long)]
    pub pid: Option<u32>,

    /// Filter by event type: "llm" or "process"
    #[structopt(long, name = "type")]
    pub event_type: Option<String>,

    /// Output as JSON
    #[structopt(long)]
    pub json: bool,

    /// Show summary statistics
    #[structopt(long)]
    pub summary: bool,

    /// Custom audit database path
    #[structopt(long)]
    pub db: Option<String>,
}

impl AuditCommand {
    pub fn execute(&self) {
        let db_path = self.db
            .as_ref()
            .map(|p| std::path::PathBuf::from(p))
            .unwrap_or_else(|| SqliteConfig::default().db_path());

        let store = match AuditStore::new(&db_path) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Failed to open audit database {:?}: {}", db_path, e);
                std::process::exit(1);
            }
        };

        let event_type = self.event_type.as_ref().and_then(|t| t.parse::<AuditEventType>().ok());

        if self.summary {
            self.print_summary(&store);
            return;
        }

        if let Some(pid) = self.pid {
            self.query_by_pid(&store, pid, event_type);
        } else {
            self.query_by_time(&store, event_type);
        }
    }

    fn query_by_time(&self, store: &AuditStore, event_type: Option<AuditEventType>) {
        let hours = self.last.unwrap_or(24);
        let since_ns = super::hours_ago_ns(hours);

        match store.query_since(since_ns, event_type) {
            Ok(records) => self.output_records(&records, &format!("Last {} hours", hours)),
            Err(e) => eprintln!("Query failed: {}", e),
        }
    }

    fn query_by_pid(&self, store: &AuditStore, pid: u32, event_type: Option<AuditEventType>) {
        match store.query_by_pid(pid, event_type) {
            Ok(records) => self.output_records(&records, &format!("PID {}", pid)),
            Err(e) => eprintln!("Query failed: {}", e),
        }
    }

    fn output_records(&self, records: &[agentsight::AuditRecord], scope: &str) {
        if self.json {
            let json_records: Vec<serde_json::Value> = records.iter().map(|r| {
                serde_json::json!({
                    "id": r.id,
                    "event_type": r.event_type.to_string(),
                    "timestamp_ns": r.timestamp_ns,
                    "pid": r.pid,
                    "ppid": r.ppid,
                    "comm": r.comm,
                    "duration_ns": r.duration_ns,
                    "extra": r.extra,
                })
            }).collect();
            println!("{}", serde_json::to_string_pretty(&json_records).unwrap());
        } else {
            println!("{}: {} audit events", scope, records.len());
            println!();
            for record in records {
                let json_record = serde_json::json!({
                    "id": record.id,
                    "event_type": record.event_type.to_string(),
                    "timestamp_ns": record.timestamp_ns,
                    "pid": record.pid,
                    "ppid": record.ppid,
                    "comm": record.comm,
                    "duration_ns": record.duration_ns,
                    "extra": record.extra,
                });
                println!("{}", serde_json::to_string(&json_record).unwrap());
            }
        }
    }

    fn print_summary(&self, store: &AuditStore) {
        let hours = self.last.unwrap_or(24);
        let since_ns = super::hours_ago_ns(hours);

        match store.summary(since_ns) {
            Ok(summary) => {
                if self.json {
                    println!("{}", serde_json::to_string_pretty(&summary).unwrap());
                } else {
                    println!("=== Audit Summary (last {} hours) ===", hours);
                    println!();
                    println!("LLM calls:        {}", summary.total_llm_calls);
                    println!("Process actions:  {}", summary.total_process_actions);

                    if !summary.providers.is_empty() {
                        println!();
                        println!("Providers:");
                        for (provider, count) in &summary.providers {
                            println!("  {}: {} calls", provider, count);
                        }
                    }

                    if !summary.top_commands.is_empty() {
                        println!();
                        println!("Top commands:");
                        for (cmd, count) in &summary.top_commands {
                            println!("  {}: {} times", cmd, count);
                        }
                    }
                }
            }
            Err(e) => eprintln!("Summary query failed: {}", e),
        }
    }
}
