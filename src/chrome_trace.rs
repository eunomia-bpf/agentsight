use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicU64, Ordering};

/// Global flow ID counter for generating unique flow identifiers
static FLOW_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

/// Get the next flow ID (auto-incrementing)
pub fn next_flow_id() -> u64 {
    FLOW_ID_COUNTER.fetch_add(1, Ordering::Relaxed)
}

/// Trait for converting data to Chrome Trace Event args
///
/// Implement this trait for types that need to be serialized as args
/// in Chrome Trace Events for Perfetto visualization.
///
/// # Example
/// ```rust,ignore
/// impl TraceArgs for ParsedRequest {
///     fn to_trace_args(&self) -> serde_json::Value {
///         json!({
///             "method": self.method,
///             "path": self.path,
///         })
///     }
/// }
/// ```
pub trait TraceArgs {
    /// Convert the data to a JSON value for Chrome Trace Event args
    fn to_trace_args(&self) -> serde_json::Value;
}

/// Trait for converting data to complete Chrome Trace Events
///
/// Implement this trait for types that can be directly converted
/// to one or more Chrome Trace Events for Perfetto visualization.
///
/// # Example
/// ```rust,ignore
/// impl ToChromeTraceEvent for HttpPair {
///     fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
///         vec![ChromeTraceEvent {
///             name: format!("{} {}", self.request.method, self.request.path),
///             cat: "http".to_string(),
///             ph: "X".to_string(),
///             ts: ns_to_us(self.request_timestamp_ns),
///             dur: Some(ns_to_us(self.duration_ns())),
///             pid: self.connection_id.pid,
///             tid: self.connection_id.ssl_ptr,
///             args: Some(self.to_trace_args()),
///             id: Some(self.flow_id.to_string()),
///             bp: None,
///         }]
///     }
/// }
/// ```
pub trait ToChromeTraceEvent {
    /// Convert the data to one or more Chrome Trace Events
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent>;
}

/// Chrome Trace Event format for Perfetto visualization
/// See: https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKcasNAojs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChromeTraceEvent {
    /// Event name (displayed in the timeline)
    pub name: String,
    /// Event category (used for filtering and coloring)
    pub cat: String,
    /// Event type: B=begin, E=end, X=complete, i=instant, C=counter, s=start flow, f=flow step, t=end flow
    pub ph: String,
    /// Timestamp in microseconds
    pub ts: u64,
    /// Duration in microseconds (only for 'X' type events)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dur: Option<u64>,
    /// Process ID
    pub pid: u32,
    /// Thread ID
    pub tid: u64,
    /// Additional event arguments
    #[serde(skip_serializing_if = "Option::is_none")]
    pub args: Option<serde_json::Value>,
    /// Flow ID for associating events (used with s/f/t phases)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<u64>,
    /// Binding point for flow events: "e" = end, "s" = start
    /// Used with ph="f" to specify where the arrow attaches
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bp: Option<String>,
}

impl ChromeTraceEvent {
    /// Create a new instant event
    pub fn instant(
        name: impl Into<String>,
        cat: impl Into<String>,
        pid: u32,
        tid: u64,
        ts_us: u64,
    ) -> Self {
        ChromeTraceEvent {
            name: name.into(),
            cat: cat.into(),
            ph: "i".to_string(),
            ts: ts_us,
            dur: None,
            pid,
            tid,
            args: None,
            id: None,
            bp: None,
        }
    }

    /// Create a new complete event (with duration)
    pub fn complete(
        name: impl Into<String>,
        cat: impl Into<String>,
        pid: u32,
        tid: u64,
        ts_us: u64,
        dur_us: u64,
    ) -> Self {
        ChromeTraceEvent {
            name: name.into(),
            cat: cat.into(),
            ph: "X".to_string(),
            ts: ts_us,
            dur: Some(dur_us),
            pid,
            tid,
            args: None,
            id: None,
            bp: None,
        }
    }

    /// Create a flow start event (s phase)
    /// This marks the beginning of a flow that can be visualized as an arrow in Perfetto
    pub fn flow_start(
        name: impl Into<String>,
        cat: impl Into<String>,
        pid: u32,
        tid: u64,
        ts_us: u64,
        flow_id: u64,
    ) -> Self {
        ChromeTraceEvent {
            name: name.into(),
            cat: cat.into(),
            ph: "s".to_string(),
            ts: ts_us,
            dur: None,
            pid,
            tid,
            args: None,
            id: Some(flow_id),
            bp: None,
        }
    }

    /// Create a flow end event (f phase with bp="e")
    /// This marks the end of a flow, connecting back to the start via flow_id
    /// Uses ph="f" with bp="e" for proper Perfetto arrow rendering
    pub fn flow_end(
        name: impl Into<String>,
        cat: impl Into<String>,
        pid: u32,
        tid: u64,
        ts_us: u64,
        flow_id: u64,
    ) -> Self {
        ChromeTraceEvent {
            name: name.into(),
            cat: cat.into(),
            ph: "f".to_string(), // Use 'f' instead of 't'
            ts: ts_us,
            dur: None,
            pid,
            tid,
            args: None,
            id: Some(flow_id),
            bp: Some("e".to_string()), // Binding point at end
        }
    }

    /// Create a flow step event (f phase)
    /// Used for intermediate steps in a flow
    pub fn flow_step(
        name: impl Into<String>,
        cat: impl Into<String>,
        pid: u32,
        tid: u64,
        ts_us: u64,
        flow_id: u64,
    ) -> Self {
        ChromeTraceEvent {
            name: name.into(),
            cat: cat.into(),
            ph: "f".to_string(),
            ts: ts_us,
            dur: None,
            pid,
            tid,
            args: None,
            id: Some(flow_id),
            bp: None,
        }
    }

    /// Create flow events connecting two Chrome Trace Events
    /// 
    /// This generates a pair of flow events (s and f phases) that create
    /// an arrow in Perfetto from the start event to the end event.
    /// 
    /// Flow events only carry the arrow connection, no args.
    /// The semantic information should be in the accompanying complete/instant events.
    /// 
    /// Flow ID is automatically generated using a global atomic counter.
    /// 
    /// # Arguments
    /// * `start` - The source event (arrow starts here)
    /// * `end` - The target event (arrow ends here)
    /// 
    /// # Returns
    /// A tuple of (flow_start, flow_end, flow_id) events
    /// 
    /// # Example
    /// ```rust,ignore
    /// let request_event = ChromeTraceEvent::complete("GET /api", "http", pid1, tid1, ts1, dur1);
    /// let response_event = ChromeTraceEvent::complete("200 OK", "http", pid2, tid2, ts2, dur2);
    /// let (flow_s, flow_f, flow_id) = ChromeTraceEvent::flow_from_events(&request_event, &response_event);
    /// ```
    pub fn flow_from_events(start: &ChromeTraceEvent, end: &ChromeTraceEvent) -> (Self, Self, u64) {
        let flow_id = next_flow_id();
        let (flow_start, flow_end) = Self::flow_from_events_with_id(start, end, flow_id);
        (flow_start, flow_end, flow_id)
    }

    /// Create flow events connecting two Chrome Trace Events with a given flow_id
    /// 
    /// This generates a pair of flow events (s and f phases) that create
    /// an arrow in Perfetto from the start event to the end event.
    /// 
    /// Flow events only carry the arrow connection, no args.
    /// The semantic information should be in the accompanying complete/instant events.
    /// 
    /// # Arguments
    /// * `start` - The source event (arrow starts here)
    /// * `end` - The target event (arrow ends here)
    /// * `flow_id` - Unique identifier to link the flow events
    /// 
    /// # Returns
    /// A tuple of (flow_start, flow_end) events
    pub fn flow_from_events_with_id(start: &ChromeTraceEvent, end: &ChromeTraceEvent, flow_id: u64) -> (Self, Self) {
        let flow_start = ChromeTraceEvent {
            name: "flow".to_string(),
            cat: "flow".to_string(),
            ph: "s".to_string(),
            ts: start.ts,
            dur: None,
            pid: start.pid,
            tid: start.tid,
            args: None,
            id: Some(flow_id),
            bp: None,
        };
        
        let flow_end = ChromeTraceEvent {
            name: "flow".to_string(),
            cat: "flow".to_string(),
            ph: "f".to_string(),
            ts: end.ts,
            dur: None,
            pid: end.pid,
            tid: end.tid,
            args: None,
            id: Some(flow_id),
            bp: Some("e".to_string()),
        };
        
        (flow_start, flow_end)
    }

    /// Add arguments to the event
    pub fn with_args(mut self, args: serde_json::Map<String, serde_json::Value>) -> Self {
        self.args = Some(serde_json::Value::Object(args));
        self
    }

    /// Add arguments from a JSON Value (must be an object)
    pub fn with_trace_args_value(mut self, args: serde_json::Value) -> Self {
        if let serde_json::Value::Object(map) = args {
            self.args = Some(serde_json::Value::Object(map));
        }
        self
    }

    /// Add a single argument
    pub fn with_arg(mut self, key: impl Into<String>, value: impl Into<serde_json::Value>) -> Self {
        let mut args = match self.args.take() {
            Some(serde_json::Value::Object(map)) => map,
            _ => serde_json::Map::new(),
        };
        args.insert(key.into(), value.into());
        self.args = Some(serde_json::Value::Object(args));
        self
    }

    /// Add arguments from a TraceArgs implementor
    ///
    /// # Example
    /// ```rust,ignore
    /// let event = ChromeTraceEvent::instant("HTTP Request", "http", pid, tid, ts)
    ///     .with_trace_args(&request);
    /// ```
    pub fn with_trace_args<T: TraceArgs>(mut self, args: &T) -> Self {
        let trace_args = args.to_trace_args();
        // Only set args if it's not null and not an empty object
        let should_set = match &trace_args {
            serde_json::Value::Null => false,
            serde_json::Value::Object(map) => !map.is_empty(),
            _ => true,
        };
        if should_set {
            self.args = Some(trace_args);
        }
        self
    }
}

/// Helper function to convert nanoseconds to microseconds
pub fn ns_to_us(ns: u64) -> u64 {
    ns / 1000
}

/// Helper function to format a trace file header
pub fn trace_file_header() -> &'static str {
    "[\n"
}

/// Helper function to format a trace file footer
pub fn trace_file_footer() -> &'static str {
    "\n]"
}

// ==================== Trace File Export ====================

use std::fs::OpenOptions;
use std::io::Write;
use std::sync::OnceLock;

/// Chrome trace output file path (includes date and time to minute)
fn trace_file_path() -> &'static std::path::PathBuf {
    static PATH: OnceLock<std::path::PathBuf> = OnceLock::new();
    PATH.get_or_init(|| {
        let datetime = chrono::Local::now().format("%Y-%m-%d_%H-%M");
        std::env::current_dir().unwrap_or_default().join(format!("trace-{}.json", datetime))
    })
}

/// Initialize trace file with opening bracket and register exit hook
fn init_trace_file() {
    let path = trace_file_path();
    if let Ok(mut file) = std::fs::File::create(path) {
        let _ = file.write_all(b"[\n");
    }

    // Register exit hook to close the JSON array
    extern "C" fn close_trace_file() {
        let path = trace_file_path();
        if let Ok(mut file) = OpenOptions::new().append(true).open(path) {
            let _ = file.write_all(b"]\n");
        }
    }
    unsafe {
        libc::atexit(close_trace_file);
    }
}

/// Track if first write (no comma needed)
static FIRST_WRITE: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(true);

/// Append a trace event to the file
pub fn append_trace_event(event: &ChromeTraceEvent) {
    let path = trace_file_path();
    if let Ok(mut file) = OpenOptions::new().append(true).create(false).open(path) {
        // Add comma before event (except first one)
        if !FIRST_WRITE.swap(false, std::sync::atomic::Ordering::SeqCst) {
            let _ = file.write_all(b",");
        }
        let _ = file.write_all(serde_json::to_string(event).unwrap_or_default().as_bytes());
        let _ = file.write_all(b"\n");
    }
}

/// Export trace events to file if enabled
/// 
/// This function checks if chrome trace export is enabled via environment variable
/// AGENTSIGHT_CHROME_TRACE, and if so, writes the events to trace.json.
pub fn export_trace_events<T: ToChromeTraceEvent>(result: &T) {
    if !crate::config::chrome_trace() {
        return;
    }

    // Initialize trace file once
    static INIT: OnceLock<()> = OnceLock::new();
    INIT.get_or_init(|| {
        init_trace_file();
    });

    for event in result.to_chrome_trace_events() {
        append_trace_event(&event);
    }
}
