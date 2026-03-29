use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};

// ==================== Default Constants ====================

/// Default LRU cache capacity for HTTP connections
pub const DEFAULT_CONNECTION_CAPACITY: usize = 24;

/// Default poll timeout for ring buffer polling (milliseconds)
pub const DEFAULT_POLL_TIMEOUT_MS: u64 = 100;

/// Default minimum duration threshold for HTTP requests (microseconds)
pub const DEFAULT_MIN_DUR_US: u64 = 10_000;

/// Default maximum body length for audit analyzer
pub const DEFAULT_MAX_BODY_LEN: usize = 64 * 1024;

/// Default maximum headers for HTTP parser
pub const DEFAULT_MAX_HEADERS: usize = 64;

/// Default database filename (shared for all data types)
pub const DEFAULT_DB_NAME: &str = "agentsight.db";

/// Default audit table name
pub const DEFAULT_AUDIT_TABLE: &str = "audit_events";

/// Default token table name
pub const DEFAULT_TOKEN_TABLE: &str = "token_records";

/// Default HTTP table name
pub const DEFAULT_HTTP_TABLE: &str = "http_records";

/// Default data retention period in days (0 = no limit)
pub const DEFAULT_RETENTION_DAYS: u64 = 30;

/// Default purge check interval (every N inserts)
pub const DEFAULT_PURGE_INTERVAL: u64 = 1000;

// ==================== Global Verbose State ====================

static VERBOSE: AtomicBool = AtomicBool::new(false);

pub fn set_verbose(v: bool) {
    VERBOSE.store(v, Ordering::SeqCst);
    if std::env::var("RUST_LOG").is_err() {
        let level = if v { "debug" } else { "warn" };
        unsafe {
            std::env::set_var("RUST_LOG", level);
        }
    }
    env_logger::init();
}

pub fn verbose() -> bool {
    VERBOSE.load(Ordering::SeqCst)
}

// ==================== Chrome Trace Export ====================

/// Check if chrome trace export is enabled (set once at startup)
pub fn chrome_trace() -> bool {
    static CHROME_TRACE: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CHROME_TRACE.get_or_init(|| std::env::var("AGENTSIGHT_CHROME_TRACE").is_ok())
}

// ==================== AgentsightConfig ====================

/// Unified configuration for AgentSight
///
/// This struct contains all configuration parameters for the AgentSight system,
/// including storage, probing, parsing, aggregation, and analysis settings.
#[derive(Debug, Clone)]
pub struct AgentsightConfig {
    // --- Storage Configuration ---
    /// Base directory for database files
    pub storage_base_path: PathBuf,
    /// Database filename (shared for all data types)
    pub db_name: String,
    /// Audit table name
    pub audit_table: String,
    /// Token table name
    pub token_table: String,
    /// HTTP table name
    pub http_table: String,

    // --- Retention Configuration ---
    /// Data retention period in days (0 = no limit, records older than this are purged)
    pub retention_days: u64,
    /// Purge check interval (run purge every N inserts, 0 = never auto-purge)
    pub purge_interval: u64,

    // --- Probe Configuration ---
    /// Optional UID filter for process tracing
    pub target_uid: Option<u32>,
    /// Poll timeout for ring buffer polling (milliseconds)
    pub poll_timeout_ms: u64,

    // --- HTTP/Aggregation Configuration ---
    /// LRU cache capacity for HTTP connections
    pub connection_capacity: usize,
    /// Minimum duration threshold for HTTP requests (microseconds)
    pub min_duration_us: u64,

    // --- Parser Configuration ---
    /// Maximum number of HTTP headers to parse
    pub max_headers: usize,

    // --- Analyzer Configuration ---
    /// Maximum body length for audit analysis
    pub max_body_len: usize,

    // --- Logging Configuration ---
    /// Enable verbose logging
    pub verbose: bool,

    // --- SLS (Aliyun Log Service) Configuration ---
    /// SLS endpoint (e.g. "cn-hangzhou.log.aliyuncs.com")
    pub sls_endpoint: Option<String>,
    /// SLS access key ID
    pub sls_access_key_id: Option<String>,
    /// SLS access key secret
    pub sls_access_key_secret: Option<String>,
    /// SLS project name
    pub sls_project: Option<String>,
    /// SLS logstore name
    pub sls_logstore: Option<String>,

    // --- Tokenizer Configuration ---
    /// Path to tokenizer file for accurate token counting (e.g., "/path/to/tokenizer.json")
    pub tokenizer_path: Option<PathBuf>,
    /// URL to download tokenizer from (e.g., "https://modelscope.cn/.../tokenizer.json")
    pub tokenizer_url: Option<String>,
}

impl Default for AgentsightConfig {
    fn default() -> Self {
        Self {
            // Storage defaults
            storage_base_path: default_base_path(),
            db_name: DEFAULT_DB_NAME.to_string(),
            audit_table: DEFAULT_AUDIT_TABLE.to_string(),
            token_table: DEFAULT_TOKEN_TABLE.to_string(),
            http_table: DEFAULT_HTTP_TABLE.to_string(),
            retention_days: DEFAULT_RETENTION_DAYS,
            purge_interval: DEFAULT_PURGE_INTERVAL,

            // Probe defaults
            target_uid: None,
            poll_timeout_ms: DEFAULT_POLL_TIMEOUT_MS,

            // HTTP/Aggregation defaults
            connection_capacity: DEFAULT_CONNECTION_CAPACITY,
            min_duration_us: DEFAULT_MIN_DUR_US,

            // Parser defaults
            max_headers: DEFAULT_MAX_HEADERS,

            // Analyzer defaults
            max_body_len: DEFAULT_MAX_BODY_LEN,

            // Logging defaults
            verbose: false,

            // SLS defaults (read from env vars)
            sls_endpoint: std::env::var("SLS_ENDPOINT").ok(),
            sls_access_key_id: std::env::var("SLS_ACCESS_KEY_ID").ok(),
            sls_access_key_secret: std::env::var("SLS_ACCESS_KEY_SECRET").ok(),
            sls_project: std::env::var("SLS_PROJECT").ok(),
            sls_logstore: std::env::var("SLS_LOGSTORE").ok(),

            // Tokenizer defaults (read from env vars)
            tokenizer_path: std::env::var("AGENTSIGHT_TOKENIZER_PATH").ok().map(PathBuf::from),
            tokenizer_url: Some("https://www.modelscope.cn/models/Qwen/Qwen3.5-27B/resolve/master/tokenizer.json".to_owned()),
        }
    }
}

impl AgentsightConfig {
    /// Create a new configuration with default values
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a new configuration with custom storage base path
    pub fn with_storage_path(base_path: PathBuf) -> Self {
        Self {
            storage_base_path: base_path,
            ..Default::default()
        }
    }

    /// Get the full path to the database
    pub fn db_path(&self) -> PathBuf {
        self.storage_base_path.join(&self.db_name)
    }

    /// Get the audit table name
    pub fn audit_table_name(&self) -> &str {
        &self.audit_table
    }

    /// Get the token table name
    pub fn token_table_name(&self) -> &str {
        &self.token_table
    }

    /// Set verbose mode
    pub fn set_verbose(mut self, verbose: bool) -> Self {
        self.verbose = verbose;
        self
    }

    /// Set storage base path
    pub fn set_storage_path(mut self, path: PathBuf) -> Self {
        self.storage_base_path = path;
        self
    }

    /// Set target UID
    pub fn set_target_uid(mut self, uid: Option<u32>) -> Self {
        self.target_uid = uid;
        self
    }

    /// Set connection capacity
    pub fn set_connection_capacity(mut self, capacity: usize) -> Self {
        self.connection_capacity = capacity;
        self
    }

    /// Apply verbose setting to the global state
    pub fn apply_verbose(&self) {
        set_verbose(self.verbose);
    }

    /// Check if SLS configuration is complete
    pub fn sls_enabled(&self) -> bool {
        self.sls_endpoint.is_some()
            && self.sls_access_key_id.is_some()
            && self.sls_access_key_secret.is_some()
            && self.sls_project.is_some()
            && self.sls_logstore.is_some()
    }

    /// Set SLS endpoint
    pub fn set_sls_endpoint(mut self, endpoint: Option<String>) -> Self {
        if endpoint.is_some() {
            self.sls_endpoint = endpoint;
        }
        self
    }

    /// Set SLS access key
    pub fn set_sls_access_key(mut self, key_id: Option<String>, key_secret: Option<String>) -> Self {
        if key_id.is_some() {
            self.sls_access_key_id = key_id;
        }
        if key_secret.is_some() {
            self.sls_access_key_secret = key_secret;
        }
        self
    }

    /// Set SLS project
    pub fn set_sls_project(mut self, project: Option<String>) -> Self {
        if project.is_some() {
            self.sls_project = project;
        }
        self
    }

    /// Set SLS logstore
    pub fn set_sls_logstore(mut self, logstore: Option<String>) -> Self {
        if logstore.is_some() {
            self.sls_logstore = logstore;
        }
        self
    }

    /// Set tokenizer path
    pub fn set_tokenizer_path(mut self, path: Option<PathBuf>) -> Self {
        self.tokenizer_path = path;
        self
    }

    /// Set tokenizer URL
    pub fn set_tokenizer_url(mut self, url: Option<String>) -> Self {
        self.tokenizer_url = url;
        self
    }
}

/// Get the default base path for storage
///
/// Returns `$HOME/.agentsight` or `/tmp/.agentsight` if HOME is not set
pub fn default_base_path() -> PathBuf {
    let home = "/var/log/sysak/";
    PathBuf::from(home).join(".agentsight")
}

/// Convert BPF ktime (nanoseconds since boot) to Unix timestamp (nanoseconds since epoch)
///
/// BPF's bpf_ktime_get_ns() returns nanoseconds since system boot.
/// This function converts it to a proper Unix timestamp.
///
/// # How it works
/// 1. Reads system uptime from /proc/uptime
/// 2. Calculates boot_time = current_unix_time - uptime
/// 3. Returns boot_time + ktime
///
/// # Performance
/// Boot time is calculated once and cached, so subsequent calls are O(1).
pub fn ktime_to_unix_ns(ktime_ns: u64) -> u64 {
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    static BOOT_TIME_NS: std::sync::OnceLock<u64> = std::sync::OnceLock::new();

    let boot_time_ns = *BOOT_TIME_NS.get_or_init(|| {
        let now_unix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64;

        // Read /proc/uptime to get system uptime in seconds
        let uptime_ns = match fs::read_to_string("/proc/uptime") {
            Ok(content) => {
                // Format: "123456.67 456.78" (uptime, idle_time)
                let uptime_secs: f64 = content
                    .split_whitespace()
                    .next()
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0.0);
                (uptime_secs * 1_000_000_000.0) as u64
            }
            Err(_) => return 0,
        };

        // boot_time = current_unix_time - uptime
        now_unix.saturating_sub(uptime_ns)
    });

    boot_time_ns.saturating_add(ktime_ns)
}
