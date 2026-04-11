//! Trace subcommand - eBPF-based agent activity tracing

use agentsight::{AgentSight, AgentsightConfig};
use structopt::StructOpt;
use daemonize::Daemonize;

/// Trace subcommand
#[derive(Debug, StructOpt, Clone)]
pub struct TraceCommand {
    /// Enable verbose/debug output.
    #[structopt(short, long)]
    pub verbose: bool,

    /// Run as daemon in background
    #[structopt(long)]
    pub daemon: bool,
    /// PID file path for daemon mode
    #[structopt(long, default_value = "/tmp/agentsight.pid")]
    pub pid_file: String,

    // --- SLS (Aliyun Log Service) Configuration ---
    /// SLS endpoint (e.g. cn-hangzhou.log.aliyuncs.com)
    #[structopt(long, env = "SLS_ENDPOINT")]
    pub sls_endpoint: Option<String>,
    /// SLS access key ID
    #[structopt(long, env = "SLS_ACCESS_KEY_ID")]
    pub sls_access_key_id: Option<String>,
    /// SLS access key secret
    #[structopt(long, env = "SLS_ACCESS_KEY_SECRET")]
    pub sls_access_key_secret: Option<String>,
    /// SLS project name
    #[structopt(long, env = "SLS_PROJECT")]
    pub sls_project: Option<String>,
    /// SLS logstore name
    #[structopt(long, env = "SLS_LOGSTORE")]
    pub sls_logstore: Option<String>,
}

impl TraceCommand {
    pub fn execute(&self) {
        // Daemonize if requested
        if self.daemon {
            self.run_as_daemon();
            return;
        }
        
        self.run_tracing();
    }
    
    /// Run as daemon process
    fn run_as_daemon(&self) {
        println!("Starting agentsight in daemon mode...");
        println!("PID file: {}", self.pid_file);
        
        let daemonize = Daemonize::new()
            .pid_file(&self.pid_file)
            .chown_pid_file(true)
            .working_directory("/tmp");
        
        match daemonize.start() {
            Ok(_) => {
                // We're now in the daemon process
                self.run_tracing();
            }
            Err(e) => {
                eprintln!("Failed to daemonize: {}", e);
                std::process::exit(1);
            }
        }
    }
    
    /// Run the actual tracing logic using AgentSight
    fn run_tracing(&self) {
        // Build AgentSight config (empty target_pids means trace all processes)
        let config = AgentsightConfig::new()
            .set_verbose(self.verbose)
            .set_sls_endpoint(self.sls_endpoint.clone())
            .set_sls_access_key(self.sls_access_key_id.clone(), self.sls_access_key_secret.clone())
            .set_sls_project(self.sls_project.clone())
            .set_sls_logstore(self.sls_logstore.clone());
        
        // Create AgentSight (auto-attaches probes and starts polling)
        let mut sight = match AgentSight::new(config) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Failed to create AgentSight: {}", e);
                std::process::exit(1);
            }
        };

        // Register Ctrl+C handler for graceful shutdown.
        // This ensures AgentSight is dropped normally, which triggers
        // Storage::drop → WAL checkpoint, flushing data to the main db file.
        let running = sight.running_flag();
        ctrlc::set_handler(move || {
            log::info!("Ctrl+C received, shutting down gracefully...");
            running.store(false, std::sync::atomic::Ordering::SeqCst);
        })
        .expect("Failed to set Ctrl+C handler");

        // Run event loop (blocks until running flag is set to false)
        match sight.run() {
            Ok(count) => {
                println!("\nReceived {} events total", count);
                println!("Token usage data saved. Use 'agentsight token' to query.");
            }
            Err(e) => {
                eprintln!("Error during tracing: {}", e);
                std::process::exit(1);
            }
        }
        // `sight` drops here → Storage::drop → checkpoint
    }
}
