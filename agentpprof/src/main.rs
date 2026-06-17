use agent_session::{AGENT_CLAUDE, AGENT_CODEX, AgentSession, SessionCandidate};
use anyhow::{Context, Result, anyhow, bail};
use chrono::{DateTime, Utc};
use clap::{Parser, Subcommand, ValueEnum};
use flate2::{Compression, write::GzEncoder};
use prost::Message;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};
use walkdir::WalkDir;

const DEFAULT_LLAMA_URL: &str = "http://127.0.0.1:8080";
const TAG_CACHE_VERSION: &str = "v3";
const TAG_GRAMMAR: &str =
    "root ::= [a-z] [a-z] [a-z] [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]?";

#[derive(Parser)]
#[command(name = "agentpprof")]
#[command(about = "pprof-compatible semantic profiler for local AI coding-agent sessions")]
struct Cli {
    #[command(flatten)]
    export: ExportArgs,
    #[command(subcommand)]
    command: Option<CommandKind>,
}

#[derive(Subcommand)]
enum CommandKind {
    /// Write one semantic profile file. This is the same as calling agentpprof without a subcommand.
    Export(ExportArgs),
    /// Write the older multi-file research/dashboard bundle.
    Bundle(RunArgs),
    Render(RenderArgs),
    Bench(BenchArgs),
}

#[derive(Parser, Clone)]
struct ExportArgs {
    /// Output file. Use .pb.gz for Go pprof, .folded for folded stacks, .svg for an SVG flamegraph, or .json.
    #[arg(short, long)]
    output: Option<PathBuf>,
    #[arg(long, default_value = ".")]
    project_root: PathBuf,
    #[arg(long)]
    project_name: Option<String>,
    #[arg(long, value_enum, default_value_t = OutputFormat::Pprof)]
    format: OutputFormat,
    #[arg(long, value_enum, default_value_t = ProfileView::Tasks)]
    view: ProfileView,
    #[arg(long, value_enum, default_value_t = TaggerKind::Regex)]
    tagger: TaggerKind,
    #[arg(long)]
    codex_root: Option<PathBuf>,
    #[arg(long)]
    claude_root: Option<PathBuf>,
    #[arg(long = "session-file")]
    session_files: Vec<PathBuf>,
    #[arg(long)]
    session_id: Option<String>,
    #[arg(long)]
    session_tag: Option<String>,
    #[arg(long)]
    prompt_tag: Option<String>,
    #[arg(long)]
    agent: Option<String>,
    #[arg(long, default_value_t = 160)]
    scan_files: usize,
    #[arg(long, default_value_t = 36)]
    max_sessions: usize,
    #[arg(long, default_value = DEFAULT_LLAMA_URL)]
    llama_url: String,
    #[arg(long, default_value = "local")]
    model: String,
    #[arg(long, default_value_t = 30)]
    timeout: u64,
    #[arg(long, default_value_t = -1)]
    max_uncached_tags: isize,
    #[arg(long)]
    cache: Option<PathBuf>,
    #[arg(long)]
    no_cache: bool,
    #[arg(long)]
    include_previews: bool,
    #[arg(long, default_value_t = true, action = clap::ArgAction::Set)]
    tag_llm_calls: bool,
}

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
enum OutputFormat {
    Pprof,
    Folded,
    Svg,
    Json,
}

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
enum ProfileView {
    Tasks,
    Tools,
    Tokens,
    Files,
    Network,
}

#[derive(Clone, Copy, Debug, ValueEnum)]
enum TaggerKind {
    Regex,
    Llm,
}

#[derive(Parser, Clone)]
struct RunArgs {
    #[arg(long, default_value = ".")]
    project_root: PathBuf,
    #[arg(long)]
    project_name: Option<String>,
    #[arg(long)]
    out: Option<PathBuf>,
    #[arg(long)]
    codex_root: Option<PathBuf>,
    #[arg(long)]
    claude_root: Option<PathBuf>,
    #[arg(long = "session-file")]
    session_files: Vec<PathBuf>,
    #[arg(long, default_value_t = 160)]
    scan_files: usize,
    #[arg(long, default_value_t = 36)]
    max_sessions: usize,
    #[arg(long, default_value = DEFAULT_LLAMA_URL)]
    llama_url: String,
    #[arg(long, default_value = "local")]
    model: String,
    #[arg(long, default_value_t = 30)]
    timeout: u64,
    #[arg(long, default_value_t = -1)]
    max_uncached_tags: isize,
    #[arg(long)]
    include_previews: bool,
    #[arg(long, default_value_t = true, action = clap::ArgAction::Set)]
    tag_llm_calls: bool,
}

#[derive(Parser, Clone)]
struct RenderArgs {
    #[arg(long, default_value = ".agentsight/agentpprof/latest")]
    out: PathBuf,
}

#[derive(Parser, Clone)]
struct BenchArgs {
    #[arg(long, default_value = "llama-server")]
    llama_server: PathBuf,
    #[arg(long = "server-arg", allow_hyphen_values = true)]
    server_args: Vec<String>,
    /// Repeats per fragment for stability measurement.
    #[arg(long, default_value_t = 2)]
    runs: usize,
    #[arg(long, default_value_t = 240)]
    load_timeout: u64,
    #[arg(long, default_value_t = 60)]
    request_timeout: u64,
    #[arg(long)]
    out: Option<PathBuf>,
    #[arg(long = "model", required = true)]
    models: Vec<String>,
    /// Fixed fragment to repeat for stability measurement. May be repeated.
    #[arg(long = "fragment")]
    fragments: Vec<String>,
    /// File with one fixed fragment per line. May be repeated.
    #[arg(long = "fragment-file")]
    fragment_files: Vec<PathBuf>,
    /// Include fragment previews in benchmark output. Off by default for privacy.
    #[arg(long = "include-fragment-previews")]
    include_fragment_previews: bool,
}

#[derive(Debug, Clone)]
struct UserRequest {
    index: usize,
    ts_ms: Option<i64>,
    text_hash: String,
    preview: String,
    tag: String,
}

#[derive(Debug, Clone)]
struct ToolEvent {
    ts_ms: Option<i64>,
    request_index: usize,
    tool_name: String,
    category: String,
    command: String,
    command_name: String,
    effect: String,
    process_chain: Vec<String>,
    status: String,
    path_groups: Vec<String>,
    domains: Vec<String>,
    call_id: Option<String>,
}

#[derive(Debug, Clone)]
struct LlmEvent {
    ts_ms: Option<i64>,
    request_index: usize,
    model: String,
    text_hash: String,
    preview: String,
    input_tokens: u64,
    output_tokens: u64,
    cache_tokens: u64,
    estimated_tokens: u64,
    tag: String,
}

impl LlmEvent {
    fn token_components(&self) -> Vec<(&'static str, u64)> {
        const MAX_REPORTED_TOKEN_COMPONENT: u64 = 10_000_000;
        const MAX_ESTIMATED_TOKEN_COMPONENT: u64 = 200_000;
        let mut out = Vec::new();
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.input_tokens) {
            out.push(("input", self.input_tokens));
        }
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.output_tokens) {
            out.push(("output", self.output_tokens));
        }
        if (1..=MAX_REPORTED_TOKEN_COMPONENT).contains(&self.cache_tokens) {
            out.push(("cache", self.cache_tokens));
        }
        if out.is_empty() && (1..=MAX_ESTIMATED_TOKEN_COMPONENT).contains(&self.estimated_tokens) {
            out.push(("estimate", self.estimated_tokens));
        }
        if out.is_empty() {
            out.push(("unknown", 1));
        }
        out
    }
}

#[derive(Debug, Clone)]
struct SessionRecord {
    source: String,
    path: PathBuf,
    session_id: String,
    cwd: String,
    agent_role: String,
    model: String,
    title: String,
    start_ts_ms: Option<i64>,
    user_requests: Vec<UserRequest>,
    tools: Vec<ToolEvent>,
    llm_calls: Vec<LlmEvent>,
    session_tag: String,
}

impl SessionRecord {
    fn request_by_index(&self, index: usize) -> &UserRequest {
        self.user_requests
            .get(index)
            .or_else(|| self.user_requests.last())
            .expect("session has bootstrap prompt")
    }

    fn ensure_prompt(&mut self) {
        if self.user_requests.is_empty() {
            self.user_requests.push(UserRequest {
                index: 0,
                ts_ms: self.start_ts_ms,
                text_hash: "bootstrap".to_string(),
                preview: "session bootstrap".to_string(),
                tag: String::new(),
            });
        }
    }
}

#[derive(Default, Serialize, Clone)]
struct TagStats {
    requests: usize,
    cache_hits: usize,
    llm_calls: usize,
    llm_successes: usize,
    failures: Vec<String>,
}

#[derive(Serialize, Deserialize, Clone)]
struct TagEntry {
    tag: String,
    kind: String,
    source_hash: String,
    created_at: String,
    llm: LlmInfo,
}

#[derive(Serialize, Deserialize, Clone)]
struct LlmInfo {
    provider: String,
    base_url: String,
    model: String,
}

#[derive(Deserialize)]
struct ExistingCache {
    tags: Option<BTreeMap<String, TagEntry>>,
}

struct LlamaTagger {
    cache_path: PathBuf,
    base_url: String,
    model: String,
    timeout: Duration,
    max_uncached: isize,
    stats: TagStats,
    cache: BTreeMap<String, TagEntry>,
    agent: ureq::Agent,
}

impl LlamaTagger {
    fn new(
        cache_path: PathBuf,
        base_url: String,
        model: String,
        timeout: Duration,
        max_uncached: isize,
    ) -> Self {
        let cache = fs::read_to_string(&cache_path)
            .ok()
            .and_then(|text| serde_json::from_str::<ExistingCache>(&text).ok())
            .and_then(|payload| payload.tags)
            .unwrap_or_default();
        let agent = ureq::AgentBuilder::new()
            .timeout_read(timeout)
            .timeout_write(timeout)
            .build();
        Self {
            cache_path,
            base_url: base_url.trim_end_matches('/').to_string(),
            model,
            timeout,
            max_uncached,
            stats: TagStats::default(),
            cache,
            agent,
        }
    }

    fn tag(&mut self, kind: &str, text: &str, hints: &[String]) -> Result<String> {
        self.stats.requests += 1;
        let source = truncate_clean(&format!("{} {}", hints.join(" "), text), 1800);
        let key = short_hash(
            &format!(
                "{}\nllama.cpp\n{}\n{}\n{}\n{}\n{}",
                TAG_CACHE_VERSION, self.base_url, self.model, kind, TAG_GRAMMAR, source
            ),
            32,
        );
        if let Some(entry) = self.cache.get(&key) {
            if valid_tag(&entry.tag) {
                self.stats.cache_hits += 1;
                return Ok(entry.tag.clone());
            }
        }
        if self.max_uncached >= 0 && self.stats.llm_calls as isize >= self.max_uncached {
            bail!(
                "LLM tag budget exhausted after {} uncached calls",
                self.stats.llm_calls
            );
        }
        let tag = self.tag_uncached(kind, &source)?;
        self.cache.insert(
            key,
            TagEntry {
                tag: tag.clone(),
                kind: kind.to_string(),
                source_hash: short_hash(&source, 24),
                created_at: now_iso(),
                llm: LlmInfo {
                    provider: "llama.cpp".to_string(),
                    base_url: self.base_url.clone(),
                    model: self.model.clone(),
                },
            },
        );
        Ok(tag)
    }

    fn tag_uncached(&mut self, kind: &str, source: &str) -> Result<String> {
        let mut previous = String::new();
        for attempt in 0..2 {
            let prompt = tag_prompt(kind, source, if attempt == 0 { "" } else { &previous });
            let raw = self.call_llm(&prompt)?;
            if let Some(tag) = sanitize_tag(&raw) {
                if valid_tag(&tag) {
                    self.stats.llm_successes += 1;
                    return Ok(tag);
                }
            }
            previous = raw;
        }
        let detail = truncate_clean(&previous, 200);
        self.stats
            .failures
            .push(format!("invalid_output kind={kind} output={detail}"));
        bail!("LLM returned invalid one-word tag for {kind}: {detail:?}");
    }

    fn call_llm(&mut self, prompt: &str) -> Result<String> {
        self.stats.llm_calls += 1;
        let url = format!("{}/v1/chat/completions", self.base_url);
        let body = json!({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You output exactly one lowercase English word."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 8,
            "grammar": TAG_GRAMMAR,
            "stream": false
        });
        let response = self
            .agent
            .post(&url)
            .timeout(self.timeout)
            .send_json(body)
            .map_err(|error| anyhow!("llama.cpp request failed at {url}: {error}"))?;
        let payload: Value = response
            .into_json()
            .map_err(|error| anyhow!("invalid llama.cpp JSON response: {error}"))?;
        extract_llm_text(&payload).ok_or_else(|| anyhow!("llama.cpp response had no text content"))
    }

    fn save(&self) -> Result<()> {
        if let Some(parent) = self.cache_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let payload = json!({
            "schema_version": 2,
            "created_by": "agentpprof-rust",
            "updated_at": now_iso(),
            "llm": {
                "provider": "llama.cpp",
                "base_url": self.base_url,
                "model": self.model,
            },
            "stats": self.stats,
            "tags": self.cache,
        });
        fs::write(&self.cache_path, serde_json::to_vec_pretty(&payload)?)?;
        Ok(())
    }
}

fn tag_prompt(kind: &str, source: &str, invalid_previous: &str) -> String {
    let retry = if invalid_previous.is_empty() {
        String::new()
    } else {
        format!(
            "\nPrevious invalid answer: {invalid_previous:?}\nReturn only one valid word now.\n"
        )
    };
    format!(
        "You label local AI coding-agent session fragments.\n\
         Return exactly one lowercase English word, 3 to 12 letters.\n\
         No spaces, punctuation, quotes, markdown, or explanation.\n\
         Choose the most specific short action or topic word from the fragment itself.\n\
         Do not concatenate multiple words into one string. Do not output fragments like codingupdate, testdebug, or flamegraphfix.\n\
         Do not use generic words like task, work, misc, thing, stuff, or other.\n\
         {retry}\nFragment kind: {kind}\nFragment:\n{}\n\nTag:",
        truncate_clean(source, 1600)
    )
}

fn extract_llm_text(payload: &Value) -> Option<String> {
    payload
        .pointer("/choices/0/message/content")
        .and_then(Value::as_str)
        .or_else(|| payload.pointer("/choices/0/text").and_then(Value::as_str))
        .or_else(|| payload.get("content").and_then(Value::as_str))
        .map(str::to_string)
}

#[derive(Serialize)]
struct CounterSummary {
    total_weight: u64,
    unique_stacks: usize,
    compression_ratio: f64,
    max_stack_reuse: u64,
    top: Vec<WeightedStack>,
}

#[derive(Serialize)]
struct WeightedStack {
    stack: String,
    weight: u64,
}

type Counter = BTreeMap<String, u64>;

#[derive(Serialize)]
struct ProfileProjection {
    view: String,
    sample_type: &'static str,
    unit: &'static str,
    stacks: Counter,
}

#[derive(Clone, PartialEq, Message)]
struct PprofProfile {
    #[prost(message, repeated, tag = "1")]
    sample_type: Vec<PprofValueType>,
    #[prost(message, repeated, tag = "2")]
    sample: Vec<PprofSample>,
    #[prost(message, repeated, tag = "4")]
    location: Vec<PprofLocation>,
    #[prost(message, repeated, tag = "5")]
    function: Vec<PprofFunction>,
    #[prost(string, repeated, tag = "6")]
    string_table: Vec<String>,
    #[prost(int64, tag = "9")]
    time_nanos: i64,
    #[prost(int64, tag = "10")]
    duration_nanos: i64,
    #[prost(int64, tag = "14")]
    default_sample_type: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofValueType {
    #[prost(int64, tag = "1")]
    type_: i64,
    #[prost(int64, tag = "2")]
    unit: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofSample {
    #[prost(uint64, repeated, tag = "1")]
    location_id: Vec<u64>,
    #[prost(int64, repeated, tag = "2")]
    value: Vec<i64>,
    #[prost(message, repeated, tag = "3")]
    label: Vec<PprofLabel>,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLabel {
    #[prost(int64, tag = "1")]
    key: i64,
    #[prost(int64, tag = "2")]
    str_value: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLocation {
    #[prost(uint64, tag = "1")]
    id: u64,
    #[prost(message, repeated, tag = "4")]
    line: Vec<PprofLine>,
}

#[derive(Clone, PartialEq, Message)]
struct PprofLine {
    #[prost(uint64, tag = "1")]
    function_id: u64,
    #[prost(int64, tag = "2")]
    line: i64,
}

#[derive(Clone, PartialEq, Message)]
struct PprofFunction {
    #[prost(uint64, tag = "1")]
    id: u64,
    #[prost(int64, tag = "2")]
    name: i64,
    #[prost(int64, tag = "3")]
    system_name: i64,
    #[prost(int64, tag = "4")]
    filename: i64,
}

#[derive(Default)]
struct StringInterner {
    items: Vec<String>,
    index: BTreeMap<String, i64>,
}

impl StringInterner {
    fn with_pprof_root() -> Self {
        let mut out = Self::default();
        out.intern("");
        out
    }

    fn intern(&mut self, value: &str) -> i64 {
        if let Some(existing) = self.index.get(value) {
            return *existing;
        }
        let id = i64::try_from(self.items.len()).unwrap_or(i64::MAX);
        self.items.push(value.to_string());
        self.index.insert(value.to_string(), id);
        id
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Some(CommandKind::Export(args)) => command_export(args),
        Some(CommandKind::Bundle(args)) => command_run(args),
        Some(CommandKind::Render(args)) => command_render(args),
        Some(CommandKind::Bench(args)) => command_bench(args),
        None => command_export(cli.export),
    }
}

fn command_export(args: ExportArgs) -> Result<()> {
    let output = args.output.clone().ok_or_else(|| {
        anyhow!("missing output path; pass -o profile.pb.gz, -o profile.folded, -o profile.svg, or -o profile.json")
    })?;
    let format = infer_output_format(args.format, &output);
    let project_root = args
        .project_root
        .canonicalize()
        .unwrap_or(args.project_root.clone());
    let project_name = args.project_name.clone().unwrap_or_else(|| {
        project_root
            .file_name()
            .and_then(|v| v.to_str())
            .unwrap_or("project")
            .to_string()
    });
    let codex_root = args.codex_root.clone().unwrap_or_else(|| {
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".codex/sessions")
    });
    let claude_root = if let Some(root) = args.claude_root.clone() {
        root
    } else {
        default_claude_root(&project_root)?
    };
    let discovery = discover_sessions(
        &project_root,
        &codex_root,
        &claude_root,
        &args.session_files,
        args.scan_files,
        args.max_sessions,
    )?;
    let mut sessions = discovery.sessions;
    filter_sessions_before_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!(
            "no local Codex or Claude sessions matched {}",
            project_root.display()
        );
    }
    annotate_sessions_with(&mut sessions, &args)?;
    filter_sessions_after_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!("sessions were found, but none matched the requested tag filters");
    }
    let projection = build_profile_projection(&sessions, &project_name, args.view);
    if projection.stacks.is_empty() {
        bail!("selected view {:?} produced no samples", args.view);
    }
    write_projection(
        &projection,
        format,
        &output,
        args.include_previews,
        &sessions,
    )?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "ok",
            "output": output,
            "format": format!("{:?}", format).to_ascii_lowercase(),
            "view": projection.view,
            "sample_type": projection.sample_type,
            "unit": projection.unit,
            "sessions": sessions.len(),
            "samples": projection.stacks.values().sum::<u64>(),
            "unique_stacks": projection.stacks.len(),
            "warnings": discovery.warnings,
        }))?
    );
    Ok(())
}

fn infer_output_format(requested: OutputFormat, output: &Path) -> OutputFormat {
    if requested != OutputFormat::Pprof {
        return requested;
    }
    match output.extension().and_then(|ext| ext.to_str()) {
        Some("folded") | Some("foldedtxt") => OutputFormat::Folded,
        Some("svg") => OutputFormat::Svg,
        Some("json") => OutputFormat::Json,
        _ => OutputFormat::Pprof,
    }
}

fn filter_sessions_before_tagging(sessions: &mut Vec<SessionRecord>, args: &ExportArgs) {
    if let Some(agent) = args.agent.as_deref() {
        sessions.retain(|session| session.source.starts_with(agent));
    }
    if let Some(session_id) = args.session_id.as_deref() {
        sessions.retain(|session| session.session_id.contains(session_id));
    }
}

fn filter_sessions_after_tagging(sessions: &mut Vec<SessionRecord>, args: &ExportArgs) {
    if let Some(tag) = args.session_tag.as_deref() {
        sessions.retain(|session| session.session_tag == tag);
    }
    if let Some(tag) = args.prompt_tag.as_deref() {
        for session in sessions.iter_mut() {
            let keep = session
                .user_requests
                .iter()
                .filter(|req| req.tag == tag)
                .map(|req| req.index)
                .collect::<BTreeSet<_>>();
            session
                .tools
                .retain(|event| keep.contains(&event.request_index));
            session
                .llm_calls
                .retain(|call| keep.contains(&call.request_index));
            session
                .user_requests
                .retain(|req| keep.contains(&req.index));
        }
        sessions.retain(|session| {
            !session.user_requests.is_empty()
                || !session.tools.is_empty()
                || !session.llm_calls.is_empty()
        });
    }
}

fn annotate_sessions_with(sessions: &mut [SessionRecord], args: &ExportArgs) -> Result<()> {
    match args.tagger {
        TaggerKind::Regex => {
            let tagger = RegexTagger;
            annotate_sessions_regex(sessions, &tagger, args.tag_llm_calls);
            Ok(())
        }
        TaggerKind::Llm => {
            let cache_path = args.cache.clone().unwrap_or_else(default_tag_cache_path);
            let mut tagger = LlamaTagger::new(
                cache_path,
                args.llama_url.clone(),
                args.model.clone(),
                Duration::from_secs(args.timeout),
                args.max_uncached_tags,
            );
            annotate_sessions(sessions, &mut tagger, args.tag_llm_calls)?;
            if !args.no_cache {
                tagger.save()?;
            }
            Ok(())
        }
    }
}

struct RegexTagger;

impl RegexTagger {
    fn tag(&self, kind: &str, text: &str, hints: &[String]) -> String {
        let haystack = format!("{} {}", hints.join(" "), text).to_ascii_lowercase();
        let picked = keyword_tag(&haystack)
            .or_else(|| sanitize_tag(&one_word(text, "")))
            .filter(|tag| valid_tag(tag))
            .unwrap_or_else(|| fallback_tag(kind).to_string());
        if valid_tag(&picked) {
            picked
        } else {
            fallback_tag(kind).to_string()
        }
    }
}

fn annotate_sessions_regex(
    sessions: &mut [SessionRecord],
    tagger: &RegexTagger,
    tag_llm_calls: bool,
) {
    for session in sessions {
        let prompt_text = session
            .user_requests
            .iter()
            .take(8)
            .map(|req| req.preview.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        session.session_tag = tagger.tag(
            "session",
            &truncate_clean(
                &format!("{} {} {}", session.title, session.cwd, prompt_text),
                1500,
            ),
            &[session.source.clone(), session.model.clone()],
        );
        for req in &mut session.user_requests {
            req.tag = tagger.tag(
                "prompt",
                &req.preview,
                &[session.session_tag.clone(), session.source.clone()],
            );
        }
        for idx in 0..session.llm_calls.len() {
            if tag_llm_calls {
                let call = &session.llm_calls[idx];
                session.llm_calls[idx].tag = tagger.tag(
                    "llm",
                    &call.preview,
                    &[
                        session.session_tag.clone(),
                        session.source.clone(),
                        call.model.clone(),
                    ],
                );
            } else {
                let tag = session
                    .user_requests
                    .get(session.llm_calls[idx].request_index)
                    .or_else(|| session.user_requests.last())
                    .map(|req| req.tag.clone())
                    .unwrap_or_else(|| session.session_tag.clone());
                session.llm_calls[idx].tag = tag;
            }
        }
    }
}

fn keyword_tag(text: &str) -> Option<String> {
    let rules: &[(&str, &[&str])] = &[
        (
            "profile",
            &[
                "pprof",
                "flamegraph",
                "trace",
                "otel",
                "span",
                "observability",
                "火焰图",
            ],
        ),
        (
            "research",
            &[
                "paper",
                "osdi",
                "novelty",
                "evaluation",
                "literature",
                "论文",
                "调研",
            ],
        ),
        (
            "design",
            &[
                "design",
                "architecture",
                "visualization",
                "schema",
                "projection",
                "设计",
                "可视化",
            ],
        ),
        (
            "debug",
            &["debug", "failing", "failed", "error", "panic", "bug", "fix"],
        ),
        (
            "test",
            &["test", "cargo test", "pytest", "unit test", "coverage"],
        ),
        ("review", &["review", "audit", "pr", "diff", "regression"]),
        (
            "release",
            &["release", "publish", "crates.io", "version", "tag"],
        ),
        (
            "build",
            &["build", "compile", "cargo check", "npm run build"],
        ),
        (
            "docs",
            &["readme", "docs", "documentation", "latex", "markdown"],
        ),
        ("git", &["branch", "commit", "push", "rebase", "merge"]),
        (
            "network",
            &["network", "github.com", "curl", "wget", "fetch"],
        ),
        ("frontend", &["frontend", "react", "css", "html", "svg"]),
        ("parser", &["parse", "parser", "jsonl", "session"]),
        ("cli", &["cli", "argument", "option", "subcommand", "flag"]),
    ];
    rules
        .iter()
        .find(|(_, needles)| needles.iter().any(|needle| text.contains(needle)))
        .map(|(tag, _)| (*tag).to_string())
}

fn fallback_tag(kind: &str) -> &'static str {
    match kind {
        "session" => "analyze",
        "prompt" => "inspect",
        "llm" => "answer",
        _ => "analyze",
    }
}

fn default_tag_cache_path() -> PathBuf {
    dirs::cache_dir()
        .or_else(|| dirs::home_dir().map(|home| home.join(".cache")))
        .unwrap_or_else(|| PathBuf::from("."))
        .join("agentpprof/tags.json")
}

fn build_profile_projection(
    sessions: &[SessionRecord],
    project_name: &str,
    view: ProfileView,
) -> ProfileProjection {
    let stacks = match view {
        ProfileView::Tasks => build_task_stacks(sessions, project_name),
        ProfileView::Tools => {
            let (system, _, _) = build_folded_stacks(sessions, project_name);
            system
        }
        ProfileView::Tokens => build_token_profile_stacks(sessions, project_name),
        ProfileView::Files => build_file_stacks(sessions, project_name),
        ProfileView::Network => build_network_stacks(sessions, project_name),
    };
    let (sample_type, unit) = match view {
        ProfileView::Tasks => ("events", "count"),
        ProfileView::Tools => ("tool_events", "count"),
        ProfileView::Tokens => ("tokens", "count"),
        ProfileView::Files => ("file_events", "count"),
        ProfileView::Network => ("network_events", "count"),
    };
    ProfileProjection {
        view: format!("{:?}", view).to_ascii_lowercase(),
        sample_type,
        unit,
        stacks,
    }
}

fn build_task_stacks(sessions: &[SessionRecord], project_name: &str) -> Counter {
    let mut out = Counter::new();
    for session in sessions {
        let agent = safe_frame(&session.source, Some("agent"));
        let session_tag = safe_frame(&session.session_tag, Some("session"));
        for event in &session.tools {
            let req = session.request_by_index(event.request_index);
            folded_add(
                &mut out,
                vec![
                    safe_frame(project_name, Some("project")),
                    agent.clone(),
                    "kind:tool".to_string(),
                    safe_frame(&format!("tool/{}", event.category), Some("call")),
                    safe_frame(&event.effect, Some("effect")),
                    safe_frame(&event.status, Some("status")),
                    session_tag.clone(),
                    safe_frame(&req.tag, Some("prompt")),
                ],
                1,
            );
        }
        for call in &session.llm_calls {
            let req = session.request_by_index(call.request_index);
            folded_add(
                &mut out,
                vec![
                    safe_frame(project_name, Some("project")),
                    agent.clone(),
                    "kind:llm".to_string(),
                    safe_frame(last_model_segment(&call.model), Some("model")),
                    safe_frame(&format!("llm/{}", call.tag), Some("call")),
                    session_tag.clone(),
                    safe_frame(&req.tag, Some("prompt")),
                ],
                1,
            );
        }
    }
    out
}

fn build_token_profile_stacks(sessions: &[SessionRecord], project_name: &str) -> Counter {
    let mut out = Counter::new();
    for session in sessions {
        for call in &session.llm_calls {
            let req = session.request_by_index(call.request_index);
            for (kind, value) in call.token_components() {
                folded_add(
                    &mut out,
                    vec![
                        safe_frame(project_name, Some("project")),
                        safe_frame(&session.source, Some("agent")),
                        safe_frame(last_model_segment(&call.model), Some("model")),
                        safe_frame(kind, Some("kind")),
                        safe_frame(&session.session_tag, Some("session")),
                        safe_frame(&req.tag, Some("prompt")),
                        safe_frame(&format!("llm/{}", call.tag), Some("call")),
                    ],
                    value,
                );
            }
        }
    }
    out
}

fn build_file_stacks(sessions: &[SessionRecord], project_name: &str) -> Counter {
    let mut out = Counter::new();
    for session in sessions {
        for event in &session.tools {
            if event.path_groups.is_empty() {
                continue;
            }
            let req = session.request_by_index(event.request_index);
            for group in &event.path_groups {
                folded_add(
                    &mut out,
                    vec![
                        safe_frame(project_name, Some("project")),
                        safe_frame(&session.source, Some("agent")),
                        safe_frame(&session.session_tag, Some("session")),
                        safe_frame(&req.tag, Some("prompt")),
                        safe_frame(group, Some("path")),
                        safe_frame(&event.effect, Some("effect")),
                        safe_frame(&event.status, Some("status")),
                    ],
                    1,
                );
            }
        }
    }
    out
}

fn build_network_stacks(sessions: &[SessionRecord], project_name: &str) -> Counter {
    let mut out = Counter::new();
    for session in sessions {
        for event in &session.tools {
            if event.effect != "network" && event.domains.is_empty() {
                continue;
            }
            let req = session.request_by_index(event.request_index);
            let domains = if event.domains.is_empty() {
                vec!["unknown".to_string()]
            } else {
                event.domains.clone()
            };
            for domain in domains {
                let mut frames = vec![
                    safe_frame(project_name, Some("project")),
                    safe_frame(&session.source, Some("agent")),
                    safe_frame(&session.session_tag, Some("session")),
                    safe_frame(&req.tag, Some("prompt")),
                    safe_frame(&domain, Some("domain")),
                ];
                for process in &event.process_chain {
                    frames.push(safe_frame(process, Some("process")));
                }
                frames.push(safe_frame(&event.status, Some("status")));
                folded_add(&mut out, frames, 1);
            }
        }
    }
    out
}

fn write_projection(
    projection: &ProfileProjection,
    format: OutputFormat,
    output: &Path,
    include_previews: bool,
    sessions: &[SessionRecord],
) -> Result<()> {
    ensure_parent_dir(output)?;
    match format {
        OutputFormat::Pprof => write_pprof_projection(projection, output),
        OutputFormat::Folded => write_folded(output, &projection.stacks),
        OutputFormat::Svg => fs::write(
            output,
            flamegraph_svg(
                &projection.stacks,
                &format!("agentpprof {} profile", projection.view),
                projection.unit,
            ),
        )
        .map_err(Into::into),
        OutputFormat::Json => fs::write(
            output,
            serde_json::to_vec_pretty(&json!({
                "schema_version": 1,
                "generated_at": now_iso(),
                "profile": {
                    "view": projection.view,
                    "sample_type": projection.sample_type,
                    "unit": projection.unit,
                    "summary": summarize_counter(&projection.stacks, 20),
                    "stacks": projection.stacks,
                },
                "sessions": sessions.iter().map(|s| session_to_json(s, include_previews)).collect::<Vec<_>>(),
            }))?,
        )
        .map_err(Into::into),
    }
}

fn ensure_parent_dir(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent()
        && !parent.as_os_str().is_empty()
    {
        fs::create_dir_all(parent)?;
    }
    Ok(())
}

fn write_pprof_projection(projection: &ProfileProjection, output: &Path) -> Result<()> {
    let mut strings = StringInterner::with_pprof_root();
    let sample_type = PprofValueType {
        type_: strings.intern(projection.sample_type),
        unit: strings.intern(projection.unit),
    };
    let label_view = strings.intern("view");
    let label_view_value = strings.intern(&projection.view);
    let filename = strings.intern("agentpprof");
    let mut functions = Vec::new();
    let mut locations = Vec::new();
    let mut frame_locations = BTreeMap::<String, u64>::new();
    let mut samples = Vec::new();

    for (stack, weight) in &projection.stacks {
        let mut location_ids = Vec::new();
        for frame in stack.split(';').rev() {
            let id = if let Some(id) = frame_locations.get(frame) {
                *id
            } else {
                let id = u64::try_from(frame_locations.len() + 1).unwrap_or(u64::MAX);
                let name = strings.intern(frame);
                functions.push(PprofFunction {
                    id,
                    name,
                    system_name: name,
                    filename,
                });
                locations.push(PprofLocation {
                    id,
                    line: vec![PprofLine {
                        function_id: id,
                        line: 0,
                    }],
                });
                frame_locations.insert(frame.to_string(), id);
                id
            };
            location_ids.push(id);
        }
        samples.push(PprofSample {
            location_id: location_ids,
            value: vec![i64::try_from(*weight).unwrap_or(i64::MAX)],
            label: vec![PprofLabel {
                key: label_view,
                str_value: label_view_value,
            }],
        });
    }

    let default_sample_type = sample_type.type_;
    let profile = PprofProfile {
        sample_type: vec![sample_type],
        sample: samples,
        location: locations,
        function: functions,
        string_table: strings.items,
        time_nanos: Utc::now().timestamp_nanos_opt().unwrap_or(0),
        duration_nanos: 0,
        default_sample_type,
    };
    let bytes = profile.encode_to_vec();
    if output.extension().and_then(|ext| ext.to_str()) == Some("gz") {
        let file = fs::File::create(output)?;
        let mut encoder = GzEncoder::new(file, Compression::default());
        encoder.write_all(&bytes)?;
        encoder.finish()?;
    } else {
        fs::write(output, bytes)?;
    }
    Ok(())
}

fn command_run(args: RunArgs) -> Result<()> {
    let project_root = args
        .project_root
        .canonicalize()
        .unwrap_or(args.project_root);
    let out_dir = args
        .out
        .unwrap_or_else(|| project_root.join(".agentsight/agentpprof/latest"));
    fs::create_dir_all(&out_dir)?;
    let project_name = args.project_name.unwrap_or_else(|| {
        project_root
            .file_name()
            .and_then(|v| v.to_str())
            .unwrap_or("project")
            .to_string()
    });
    let codex_root = if let Some(root) = args.codex_root {
        root
    } else {
        dirs::home_dir()
            .ok_or_else(|| anyhow!("cannot determine home directory"))?
            .join(".codex/sessions")
    };
    let claude_root = if let Some(root) = args.claude_root {
        root
    } else {
        default_claude_root(&project_root)?
    };
    let discovery = discover_sessions(
        &project_root,
        &codex_root,
        &claude_root,
        &args.session_files,
        args.scan_files,
        args.max_sessions,
    )?;
    let mut sessions = discovery.sessions;
    if sessions.is_empty() {
        bail!(
            "no local Codex or Claude sessions found for {}",
            project_root.display()
        );
    }
    let mut tagger = LlamaTagger::new(
        out_dir.join("tags.json"),
        args.llama_url.clone(),
        args.model.clone(),
        Duration::from_secs(args.timeout),
        args.max_uncached_tags,
    );
    annotate_sessions(&mut sessions, &mut tagger, args.tag_llm_calls)?;
    tagger.save()?;
    let payload = build_report(
        ReportConfig {
            project_root: &project_root,
            project_name: &project_name,
            codex_root: &codex_root,
            claude_root: &claude_root,
            session_files: &args.session_files,
            scan_files: args.scan_files,
            max_sessions: args.max_sessions,
            include_previews: args.include_previews,
            tag_llm_calls: args.tag_llm_calls,
            out_dir: &out_dir,
        },
        &sessions,
        &tagger.stats,
        &discovery.warnings,
    )?;
    write_dashboard(&out_dir, &payload)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "ok",
            "out": out_dir,
            "dashboard": out_dir.join("index.html"),
            "agentpprof_json": out_dir.join("agentpprof.json"),
            "tags_json": out_dir.join("tags.json"),
            "sessions": payload["summary"]["session_count"],
            "system_unique_stacks": payload["summary"]["system"]["unique_stacks"],
            "llm_tag_calls": payload["llm_tagger"]["llm_calls"],
            "cache_hits": payload["llm_tagger"]["cache_hits"],
        }))?
    );
    Ok(())
}

fn command_render(args: RenderArgs) -> Result<()> {
    let payload_path = args.out.join("agentpprof.json");
    let payload: Value = serde_json::from_slice(
        &fs::read(&payload_path).with_context(|| format!("missing {}", payload_path.display()))?,
    )?;
    write_dashboard(&args.out, &payload)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "ok",
            "dashboard": args.out.join("index.html"),
        }))?
    );
    Ok(())
}

struct DiscoveryResult {
    sessions: Vec<SessionRecord>,
    warnings: Vec<String>,
}

fn discover_sessions(
    project_root: &Path,
    codex_root: &Path,
    claude_root: &Path,
    session_files: &[PathBuf],
    scan_files: usize,
    max_sessions: usize,
) -> Result<DiscoveryResult> {
    let explicit_files = !session_files.is_empty();
    let mut candidates = if explicit_files {
        session_files
            .iter()
            .filter_map(|path| candidate_from_path(path))
            .collect::<Vec<_>>()
    } else {
        let mut discovered = Vec::<SessionCandidate>::new();
        discovered.extend(
            find_jsonl(claude_root, scan_files)
                .into_iter()
                .filter_map(|path| candidate_from_path(&path)),
        );
        discovered.extend(
            find_jsonl(codex_root, scan_files)
                .into_iter()
                .filter_map(|path| candidate_from_path(&path)),
        );
        discovered
    };
    candidates.sort_by_key(|candidate| {
        std::cmp::Reverse(
            candidate
                .updated
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_millis())
                .unwrap_or(0),
        )
    });
    candidates.truncate(scan_files);
    let mut out = Vec::new();
    let mut warnings = Vec::new();
    for candidate in candidates {
        let path = candidate.path.clone();
        let summary = agent_session::parse_session_file(&candidate);
        if !explicit_files
            && !summary
                .as_ref()
                .map(|session| session_matches_project(session, project_root))
                .unwrap_or(false)
            && !raw_mentions_project(&path, project_root)
        {
            continue;
        }
        let mut session = if let Some(summary) = summary.as_ref() {
            record_from_agent_session(summary)
        } else if let Some(raw) = raw_session_minimal(&path, candidate.agent, project_root, false)?
        {
            raw
        } else {
            continue;
        };
        if let Err(error) = enrich_from_raw(&mut session, project_root) {
            warnings.push(format!(
                "skipped_session path={} error={error}",
                path.display()
            ));
            continue;
        }
        if let Some(summary) = summary.as_ref() {
            apply_agent_session_fallbacks(&mut session, summary);
        }
        session.ensure_prompt();
        if !session.user_requests.is_empty()
            || !session.tools.is_empty()
            || !session.llm_calls.is_empty()
        {
            out.push(session);
        }
        if out.len() >= max_sessions {
            break;
        }
    }
    Ok(DiscoveryResult {
        sessions: out,
        warnings,
    })
}

fn candidate_from_path(path: &Path) -> Option<SessionCandidate> {
    let agent = source_from_path(path)?;
    let updated = path
        .metadata()
        .and_then(|metadata| metadata.modified())
        .unwrap_or(std::time::UNIX_EPOCH);
    Some(SessionCandidate {
        agent,
        path: path.to_path_buf(),
        updated,
    })
}

fn find_jsonl(root: &Path, max_files: usize) -> Vec<PathBuf> {
    if !root.exists() {
        return Vec::new();
    }
    let mut files = WalkDir::new(root)
        .into_iter()
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.file_type().is_file())
        .map(|entry| entry.into_path())
        .filter(|path| path.extension().and_then(|v| v.to_str()) == Some("jsonl"))
        .collect::<Vec<_>>();
    files.sort_by_key(|path| {
        std::cmp::Reverse(
            path.metadata()
                .and_then(|m| m.modified())
                .ok()
                .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                .map(|d| d.as_millis())
                .unwrap_or(0),
        )
    });
    files.truncate(max_files);
    files
}

fn source_from_path(path: &Path) -> Option<&'static str> {
    if let Some(agent) = agent_session::agent_source_for_path(path) {
        return Some(agent);
    }
    let text = path.to_string_lossy();
    if text.contains("/.codex/") {
        Some(AGENT_CODEX)
    } else if text.contains("/.claude/") {
        Some(AGENT_CLAUDE)
    } else if text.contains("/codex/") && text.contains("sessions") {
        Some(AGENT_CODEX)
    } else if text.contains("/claude/") && text.contains("projects") {
        Some(AGENT_CLAUDE)
    } else {
        None
    }
}

fn session_matches_project(session: &AgentSession, project_root: &Path) -> bool {
    session
        .cwd
        .as_deref()
        .map(|cwd| path_text_matches_project(cwd, project_root))
        .unwrap_or(false)
}

fn path_text_matches_project(raw: &str, project_root: &Path) -> bool {
    let raw = raw.trim();
    if raw.is_empty() {
        return false;
    }
    let project = project_root.to_string_lossy();
    if raw == project || raw.starts_with(&format!("{project}/")) {
        return true;
    }
    Path::new(raw)
        .canonicalize()
        .map(|path| path == project_root)
        .unwrap_or(false)
}

fn raw_mentions_project(path: &Path, project_root: &Path) -> bool {
    fs::read_to_string(path)
        .map(|text| text.contains(&project_root.to_string_lossy().to_string()))
        .unwrap_or(false)
}

fn record_from_agent_session(session: &AgentSession) -> SessionRecord {
    SessionRecord {
        source: session.agent.clone(),
        path: session.path.clone(),
        session_id: session.session_id.clone(),
        cwd: session.cwd.clone().unwrap_or_default(),
        agent_role: "agent".to_string(),
        model: session.model.clone().unwrap_or_default(),
        title: String::new(),
        start_ts_ms: session
            .start_timestamp_ms
            .and_then(|value| i64::try_from(value).ok()),
        user_requests: Vec::new(),
        tools: Vec::new(),
        llm_calls: Vec::new(),
        session_tag: String::new(),
    }
}

fn apply_agent_session_fallbacks(record: &mut SessionRecord, session: &AgentSession) {
    if record.user_requests.is_empty() {
        if let Some(prompt) = session.prompt_preview.as_deref() {
            let ts_ms = record.start_ts_ms;
            upsert_prompt(record, ts_ms, prompt);
        }
    }
    if record.tools.is_empty() {
        for (tool, count) in &session.tools {
            for _ in 0..*count {
                record.tools.push(ToolEvent {
                    ts_ms: record.start_ts_ms,
                    request_index: 0,
                    tool_name: tool.clone(),
                    category: tool_category(tool, ""),
                    command: String::new(),
                    command_name: "none".to_string(),
                    effect: "process".to_string(),
                    process_chain: Vec::new(),
                    status: "observed".to_string(),
                    path_groups: session
                        .files
                        .keys()
                        .take(8)
                        .map(|path| path_group(path, Path::new(&record.cwd)))
                        .collect(),
                    domains: Vec::new(),
                    call_id: None,
                });
            }
        }
    }
    if record.llm_calls.is_empty() {
        for (model, usage) in &session.model_usage {
            if usage.total_tokens <= 0 {
                continue;
            }
            record.llm_calls.push(LlmEvent {
                ts_ms: record.start_ts_ms,
                request_index: 0,
                model: model.clone(),
                text_hash: short_hash(&format!("{}:{:?}", session.session_id, usage), 12),
                preview: "session token summary".to_string(),
                input_tokens: nonnegative_u64(usage.input_tokens),
                output_tokens: nonnegative_u64(usage.output_tokens),
                cache_tokens: nonnegative_u64(usage.cache_creation_tokens)
                    + nonnegative_u64(usage.cache_read_tokens),
                estimated_tokens: nonnegative_u64(usage.total_tokens),
                tag: String::new(),
            });
        }
    }
}

fn nonnegative_u64(value: i64) -> u64 {
    u64::try_from(value).unwrap_or(0)
}

fn raw_session_minimal(
    path: &Path,
    source: &str,
    project_root: &Path,
    enforce_project_filter: bool,
) -> Result<Option<SessionRecord>> {
    if enforce_project_filter && source == AGENT_CODEX && !raw_mentions_project(path, project_root)
    {
        return Ok(None);
    }
    Ok(Some(SessionRecord {
        source: source.to_string(),
        path: path.to_path_buf(),
        session_id: path
            .file_stem()
            .and_then(|v| v.to_str())
            .unwrap_or("session")
            .to_string(),
        cwd: String::new(),
        agent_role: "agent".to_string(),
        model: String::new(),
        title: String::new(),
        start_ts_ms: None,
        user_requests: Vec::new(),
        tools: Vec::new(),
        llm_calls: Vec::new(),
        session_tag: String::new(),
    }))
}

fn enrich_from_raw(record: &mut SessionRecord, project_root: &Path) -> Result<()> {
    let file = fs::File::open(&record.path)?;
    let reader = BufReader::new(file);
    let mut current_request = record.user_requests.len().saturating_sub(1);
    let mut call_index = HashMap::<String, usize>::new();
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let Ok(value) = serde_json::from_str::<Value>(&line) else {
            continue;
        };
        let ts_ms = value
            .get("timestamp")
            .and_then(Value::as_str)
            .and_then(parse_ts_ms);
        if record.start_ts_ms.is_none() {
            record.start_ts_ms = ts_ms;
        }
        if record.cwd.is_empty() {
            if let Some(cwd) = value
                .get("cwd")
                .and_then(Value::as_str)
                .or_else(|| value.pointer("/payload/cwd").and_then(Value::as_str))
            {
                record.cwd = cwd.to_string();
            }
        }
        if record.source.starts_with("codex") {
            enrich_codex(
                record,
                project_root,
                &value,
                ts_ms,
                &mut current_request,
                &mut call_index,
            );
        } else if record.source.starts_with("claude") {
            enrich_claude(
                record,
                project_root,
                &value,
                ts_ms,
                &mut current_request,
                &mut call_index,
            );
        }
    }
    if record.user_requests.is_empty() {
        record.ensure_prompt();
    }
    Ok(())
}

fn enrich_codex(
    record: &mut SessionRecord,
    project_root: &Path,
    value: &Value,
    ts_ms: Option<i64>,
    current_request: &mut usize,
    call_index: &mut HashMap<String, usize>,
) {
    let typ = value.get("type").and_then(Value::as_str).unwrap_or("");
    let payload = value.get("payload").unwrap_or(&Value::Null);
    if typ == "session_meta" {
        if let Some(id) = payload
            .get("id")
            .or_else(|| payload.get("session_id"))
            .and_then(Value::as_str)
        {
            record.session_id = id.to_string();
        }
        if let Some(model) = payload.get("model").and_then(Value::as_str) {
            record.model = model.to_string();
        }
        if let Some(cwd) = payload.get("cwd").and_then(Value::as_str) {
            record.cwd = cwd.to_string();
        }
    }
    let ptype = payload.get("type").and_then(Value::as_str).unwrap_or("");
    match (typ, ptype) {
        ("event_msg", "user_message") => {
            let text = payload
                .get("message")
                .or_else(|| payload.get("content"))
                .and_then(Value::as_str)
                .unwrap_or("");
            if !text.trim().is_empty() {
                *current_request = upsert_prompt(record, ts_ms, text);
            }
        }
        ("response_item", "function_call") => {
            let name = payload
                .get("name")
                .or_else(|| payload.get("tool_name"))
                .and_then(Value::as_str)
                .unwrap_or("tool");
            let args = parse_tool_args(payload.get("arguments").unwrap_or(&Value::Null));
            let call_id = payload
                .get("call_id")
                .and_then(Value::as_str)
                .map(str::to_string);
            let event = tool_event_from_input(
                project_root,
                ts_ms,
                *current_request,
                name,
                &args,
                call_id.clone(),
            );
            if let Some(id) = call_id {
                call_index.insert(id, record.tools.len());
            }
            record.tools.push(event);
        }
        ("response_item", "function_call_output") => {
            if let Some(call_id) = payload.get("call_id").and_then(Value::as_str) {
                if let Some(index) = call_index.get(call_id).copied() {
                    let output = payload.get("output").and_then(Value::as_str).unwrap_or("");
                    record.tools[index].status = status_from_output(output).to_string();
                }
            }
        }
        ("response_item", "message") => {
            let text = content_to_text(payload.get("content").unwrap_or(&Value::Null));
            if !text.trim().is_empty() {
                record.llm_calls.push(LlmEvent {
                    ts_ms,
                    request_index: *current_request,
                    model: if record.model.is_empty() {
                        "codex".to_string()
                    } else {
                        record.model.clone()
                    },
                    text_hash: short_hash(&text, 12),
                    preview: truncate_clean(&text, 140),
                    input_tokens: 0,
                    output_tokens: 0,
                    cache_tokens: 0,
                    estimated_tokens: (text.len() as u64 / 4).max(1),
                    tag: String::new(),
                });
            }
        }
        ("event_msg", "token_count") | ("event_msg", "token_usage") => {
            let usage = payload
                .get("usage")
                .or_else(|| payload.get("info"))
                .unwrap_or(payload);
            let total = json_u64(usage, "total_tokens")
                .max(json_u64(usage, "tokens"))
                .max(json_u64(
                    usage.get("total_token_usage").unwrap_or(&Value::Null),
                    "total_tokens",
                ));
            if total > 0 {
                record.llm_calls.push(LlmEvent {
                    ts_ms,
                    request_index: *current_request,
                    model: if record.model.is_empty() {
                        "codex".to_string()
                    } else {
                        record.model.clone()
                    },
                    text_hash: short_hash(&usage.to_string(), 12),
                    preview: "codex token report".to_string(),
                    input_tokens: json_u64(usage, "input_tokens"),
                    output_tokens: json_u64(usage, "output_tokens"),
                    cache_tokens: json_u64(usage, "cached_input_tokens"),
                    estimated_tokens: total,
                    tag: String::new(),
                });
            }
        }
        _ => {}
    }
}

fn enrich_claude(
    record: &mut SessionRecord,
    project_root: &Path,
    value: &Value,
    ts_ms: Option<i64>,
    current_request: &mut usize,
    call_index: &mut HashMap<String, usize>,
) {
    let typ = value.get("type").and_then(Value::as_str).unwrap_or("");
    if let Some(id) = value.get("sessionId").and_then(Value::as_str) {
        record.session_id = id.to_string();
    }
    if let Some(title) = value.get("aiTitle").and_then(Value::as_str) {
        record.title = title.to_string();
    }
    match typ {
        "user" => {
            let content = value.pointer("/message/content").unwrap_or(&Value::Null);
            if claude_is_tool_result(content) {
                let is_error = value
                    .get("toolUseResult")
                    .and_then(|v| v.get("is_error"))
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                for id in claude_tool_result_ids(content) {
                    if let Some(index) = call_index.get(&id).copied() {
                        record.tools[index].status =
                            if is_error { "fail" } else { "ok" }.to_string();
                    }
                }
            } else {
                let text = content_to_text(content);
                if !text.trim().is_empty() {
                    *current_request = upsert_prompt(record, ts_ms, &text);
                }
            }
        }
        "assistant" => {
            if let Some(model) = value.pointer("/message/model").and_then(Value::as_str) {
                record.model = model.to_string();
            }
            let content = value.pointer("/message/content").unwrap_or(&Value::Null);
            if let Some(items) = content.as_array() {
                for item in items {
                    if item.get("type").and_then(Value::as_str) == Some("tool_use") {
                        let name = item.get("name").and_then(Value::as_str).unwrap_or("tool");
                        let input = item.get("input").unwrap_or(&Value::Null);
                        let id = item.get("id").and_then(Value::as_str).map(str::to_string);
                        let event = tool_event_from_input(
                            project_root,
                            ts_ms,
                            *current_request,
                            name,
                            input,
                            id.clone(),
                        );
                        if let Some(id) = id {
                            call_index.insert(id, record.tools.len());
                        }
                        record.tools.push(event);
                    }
                }
            }
            let text = content_to_text(content);
            let usage = value.pointer("/message/usage").unwrap_or(&Value::Null);
            if !text.trim().is_empty() || usage.is_object() {
                record.llm_calls.push(LlmEvent {
                    ts_ms,
                    request_index: *current_request,
                    model: if record.model.is_empty() {
                        "claude".to_string()
                    } else {
                        record.model.clone()
                    },
                    text_hash: short_hash(&(text.clone() + &usage.to_string()), 12),
                    preview: truncate_clean(
                        if text.trim().is_empty() {
                            "claude response"
                        } else {
                            &text
                        },
                        140,
                    ),
                    input_tokens: json_u64(usage, "input_tokens"),
                    output_tokens: json_u64(usage, "output_tokens"),
                    cache_tokens: json_u64(usage, "cache_creation_input_tokens")
                        + json_u64(usage, "cache_read_input_tokens"),
                    estimated_tokens: 0,
                    tag: String::new(),
                });
            }
        }
        "last-prompt" => {
            if record.user_requests.is_empty() {
                if let Some(text) = value.get("lastPrompt").and_then(Value::as_str) {
                    *current_request = upsert_prompt(record, ts_ms, text);
                }
            }
        }
        _ => {}
    }
}

fn upsert_prompt(record: &mut SessionRecord, ts_ms: Option<i64>, text: &str) -> usize {
    let hash = short_hash(text, 12);
    if let Some(existing) = record
        .user_requests
        .iter()
        .position(|req| req.text_hash == hash)
    {
        return existing;
    }
    let index = record.user_requests.len();
    record.user_requests.push(UserRequest {
        index,
        ts_ms,
        text_hash: hash,
        preview: truncate_clean(text, 180),
        tag: String::new(),
    });
    index
}

fn annotate_sessions(
    sessions: &mut [SessionRecord],
    tagger: &mut LlamaTagger,
    tag_llm_calls: bool,
) -> Result<()> {
    for session in sessions {
        let prompt_text = session
            .user_requests
            .iter()
            .take(8)
            .map(|req| req.preview.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        session.session_tag = tagger.tag(
            "session",
            &truncate_clean(
                &format!("{} {} {}", session.title, session.cwd, prompt_text),
                1500,
            ),
            &[session.source.clone(), session.model.clone()],
        )?;
        for req in &mut session.user_requests {
            req.tag = tagger.tag(
                "prompt",
                &req.preview,
                &[session.session_tag.clone(), session.source.clone()],
            )?;
        }
        if tag_llm_calls {
            for call in &mut session.llm_calls {
                call.tag = tagger.tag(
                    "llm",
                    &call.preview,
                    &[
                        session.session_tag.clone(),
                        session.source.clone(),
                        call.model.clone(),
                    ],
                )?;
            }
        } else {
            for idx in 0..session.llm_calls.len() {
                let tag = session
                    .user_requests
                    .get(session.llm_calls[idx].request_index)
                    .or_else(|| session.user_requests.last())
                    .map(|req| req.tag.clone())
                    .unwrap_or_else(|| session.session_tag.clone());
                session.llm_calls[idx].tag = tag;
            }
        }
    }
    Ok(())
}

struct ReportConfig<'a> {
    project_root: &'a Path,
    project_name: &'a str,
    codex_root: &'a Path,
    claude_root: &'a Path,
    session_files: &'a [PathBuf],
    scan_files: usize,
    max_sessions: usize,
    include_previews: bool,
    tag_llm_calls: bool,
    out_dir: &'a Path,
}

fn build_report(
    config: ReportConfig<'_>,
    sessions: &[SessionRecord],
    tag_stats: &TagStats,
    warnings: &[String],
) -> Result<Value> {
    let (system, token, prompt_rows) = build_folded_stacks(sessions, config.project_name);
    let nonsemantic = build_nonsemantic_system(&system);
    let dimensions = build_dimension_views(&system, &token);
    write_folded(&config.out_dir.join("semantic-system.folded.txt"), &system)?;
    write_folded(&config.out_dir.join("semantic-token.folded.txt"), &token)?;
    write_folded(
        &config.out_dir.join("nonsemantic-system.folded.txt"),
        &nonsemantic,
    )?;
    for (name, stacks) in &dimensions {
        write_folded(&config.out_dir.join(format!("{name}.folded.txt")), stacks)?;
    }

    let mut tag_counts = BTreeMap::<String, u64>::new();
    for row in &prompt_rows {
        *tag_counts.entry(row.prompt_tag.clone()).or_default() += 1;
    }
    let mut source_counts = BTreeMap::<String, u64>::new();
    for session in sessions {
        *source_counts.entry(session.source.clone()).or_default() += 1;
    }
    let mut top_prompt_tags = tag_counts
        .into_iter()
        .map(|(tag, count)| json!({ "tag": tag, "count": count }))
        .collect::<Vec<_>>();
    top_prompt_tags.sort_by_key(|row| std::cmp::Reverse(row["count"].as_u64().unwrap_or(0)));

    let payload = json!({
        "schema_version": 2,
        "generated_at": now_iso(),
        "project": {
            "name": config.project_name,
            "root": config.project_root,
        },
        "inputs": {
            "scan_files": config.scan_files,
            "max_sessions": config.max_sessions,
            "tag_llm_calls": config.tag_llm_calls,
            "codex_root": config.codex_root,
            "claude_root": config.claude_root,
            "session_files": config.session_files,
        },
        "llm_tagger": tag_stats,
        "warnings": warnings,
        "sessions": sessions.iter().map(|s| session_to_json(s, config.include_previews)).collect::<Vec<_>>(),
        "summary": {
            "session_count": sessions.len(),
            "source_counts": source_counts,
            "raw_tool_events": sessions.iter().map(|s| s.tools.len() as u64).sum::<u64>(),
            "raw_llm_events": sessions.iter().map(|s| s.llm_calls.len() as u64).sum::<u64>(),
            "system": summarize_counter(&system, 12),
            "nonsemantic_system": summarize_counter(&nonsemantic, 12),
            "token": summarize_counter(&token, 12),
            "dimensions": dimensions.iter().map(|(name, stacks)| (name.clone(), summarize_counter(stacks, 8))).collect::<BTreeMap<_, _>>(),
            "top_prompt_tags": top_prompt_tags,
            "command_summary": command_summary(sessions),
            "timeline": timeline_summary(sessions),
            "semantic_mixing": semantic_mixing(&system),
        },
        "prompt_tags": prompt_rows.into_iter().map(|row| row.into_json(config.include_previews)).collect::<Vec<_>>(),
        "artifacts": artifact_map(),
    });
    fs::write(
        config.out_dir.join("agentpprof.json"),
        serde_json::to_vec_pretty(&payload)?,
    )?;
    Ok(payload)
}

struct PromptRow {
    source: String,
    session_id: String,
    agent_sight_session_id: String,
    session_tag: String,
    prompt_index: usize,
    prompt_tag: String,
    prompt_hash: String,
    preview: String,
}

impl PromptRow {
    fn into_json(self, include_preview: bool) -> Value {
        json!({
            "source": self.source,
            "session_id": self.session_id,
            "agent_sight_session_id": self.agent_sight_session_id,
            "session_tag": self.session_tag,
            "prompt_index": self.prompt_index,
            "prompt_tag": self.prompt_tag,
            "prompt_hash": self.prompt_hash,
            "preview": if include_preview { self.preview } else { "redacted".to_string() },
        })
    }
}

fn build_folded_stacks(
    sessions: &[SessionRecord],
    project_name: &str,
) -> (Counter, Counter, Vec<PromptRow>) {
    let mut system = Counter::new();
    let mut token = Counter::new();
    let mut prompt_rows = Vec::new();
    for session in sessions {
        let agent_frame = safe_frame(&session.source, Some("agent"));
        let session_frame = safe_frame(&session.session_tag, Some("session"));
        for req in &session.user_requests {
            prompt_rows.push(PromptRow {
                source: session.source.clone(),
                session_id: session.session_id.clone(),
                agent_sight_session_id: agent_sight_session_id(
                    &session.source,
                    &session.session_id,
                ),
                session_tag: session.session_tag.clone(),
                prompt_index: req.index,
                prompt_tag: req.tag.clone(),
                prompt_hash: req.text_hash.clone(),
                preview: req.preview.clone(),
            });
        }
        for event in &session.tools {
            let req = session.request_by_index(event.request_index);
            let mut base = vec![
                safe_frame(project_name, Some("project")),
                agent_frame.clone(),
                session_frame.clone(),
                safe_frame(&req.tag, Some("prompt")),
                safe_frame(&format!("tool/{}", event.category), Some("call")),
            ];
            for process in &event.process_chain {
                base.push(safe_frame(process, Some("process")));
            }
            base.push(safe_frame(&event.effect, Some("effect")));
            if !event.path_groups.is_empty() {
                for group in &event.path_groups {
                    let mut frames = base.clone();
                    frames.push(safe_frame(group, Some("path")));
                    frames.push(safe_frame(&event.status, Some("status")));
                    folded_add(&mut system, frames, 1);
                }
            } else if !event.domains.is_empty() {
                for domain in &event.domains {
                    let mut frames = base.clone();
                    frames.push(safe_frame(domain, Some("domain")));
                    frames.push(safe_frame(&event.status, Some("status")));
                    folded_add(&mut system, frames, 1);
                }
            } else {
                let mut frames = base;
                frames.push(safe_frame(&event.status, Some("status")));
                folded_add(&mut system, frames, 1);
            }
        }
        for call in &session.llm_calls {
            let req = session.request_by_index(call.request_index);
            for (kind, value) in call.token_components() {
                folded_add(
                    &mut token,
                    vec![
                        safe_frame(project_name, Some("project")),
                        agent_frame.clone(),
                        session_frame.clone(),
                        safe_frame(&req.tag, Some("prompt")),
                        safe_frame(&format!("llm/{}", call.tag), Some("call")),
                        safe_frame(last_model_segment(&call.model), Some("model")),
                        safe_frame(kind, Some("kind")),
                    ],
                    value,
                );
            }
        }
    }
    (system, token, prompt_rows)
}

fn folded_add(counter: &mut Counter, frames: Vec<String>, weight: u64) {
    let stack = frames
        .into_iter()
        .filter(|frame| !frame.is_empty())
        .collect::<Vec<_>>()
        .join(";");
    if !stack.is_empty() {
        *counter.entry(stack).or_default() += weight.max(1);
    }
}

fn build_nonsemantic_system(system: &Counter) -> Counter {
    let mut out = Counter::new();
    for (stack, weight) in system {
        let frames = stack
            .split(';')
            .filter(|frame| !frame.starts_with("session:") && !frame.starts_with("prompt:"))
            .collect::<Vec<_>>()
            .join(";");
        *out.entry(frames).or_default() += weight;
    }
    out
}

fn build_dimension_views(system: &Counter, token: &Counter) -> BTreeMap<String, Counter> {
    BTreeMap::from([
        (
            "session-system".to_string(),
            project_folded(
                system,
                &[
                    "project:", "agent:", "session:", "call:", "process:", "effect:", "path:",
                    "domain:", "status:",
                ],
            ),
        ),
        (
            "prompt-system".to_string(),
            project_folded(
                system,
                &[
                    "project:", "agent:", "prompt:", "call:", "process:", "effect:", "path:",
                    "domain:", "status:",
                ],
            ),
        ),
        (
            "session-token".to_string(),
            project_folded(
                token,
                &["project:", "agent:", "session:", "model:", "kind:"],
            ),
        ),
        (
            "prompt-token".to_string(),
            project_folded(token, &["project:", "agent:", "prompt:", "model:", "kind:"]),
        ),
        (
            "llm-token".to_string(),
            project_folded(token, &["project:", "agent:", "call:", "model:", "kind:"]),
        ),
    ])
}

fn project_folded(source: &Counter, prefixes: &[&str]) -> Counter {
    let mut out = Counter::new();
    for (stack, weight) in source {
        let frames = stack
            .split(';')
            .filter(|frame| prefixes.iter().any(|prefix| frame.starts_with(prefix)))
            .collect::<Vec<_>>()
            .join(";");
        if !frames.is_empty() {
            *out.entry(frames).or_default() += weight;
        }
    }
    out
}

fn summarize_counter(counter: &Counter, limit: usize) -> CounterSummary {
    let total_weight = counter.values().sum::<u64>();
    let unique_stacks = counter.len();
    let max_stack_reuse = counter.values().copied().max().unwrap_or(0);
    CounterSummary {
        total_weight,
        unique_stacks,
        compression_ratio: if unique_stacks == 0 {
            0.0
        } else {
            round3(total_weight as f64 / unique_stacks as f64)
        },
        max_stack_reuse,
        top: top_stacks(counter, limit),
    }
}

fn top_stacks(counter: &Counter, limit: usize) -> Vec<WeightedStack> {
    let mut rows = counter
        .iter()
        .map(|(stack, weight)| WeightedStack {
            stack: stack.clone(),
            weight: *weight,
        })
        .collect::<Vec<_>>();
    rows.sort_by_key(|row| (std::cmp::Reverse(row.weight), row.stack.clone()));
    rows.truncate(limit);
    rows
}

fn command_summary(sessions: &[SessionRecord]) -> Vec<Value> {
    let mut counts = BTreeMap::<(String, String, String, String, String, String), u64>::new();
    for session in sessions {
        let family = agent_family(&session.source);
        let cohort = if session.source.contains("subagent") {
            "subagent"
        } else {
            "top"
        };
        for event in &session.tools {
            *counts
                .entry((
                    family.clone(),
                    cohort.to_string(),
                    event.category.clone(),
                    event.command_name.clone(),
                    event.effect.clone(),
                    event.status.clone(),
                ))
                .or_default() += 1;
        }
    }
    let mut rows = counts
        .into_iter()
        .map(|((agent, cohort, tool, cmd, effect, status), count)| {
            json!({
                "agent": agent,
                "cohort": cohort,
                "tool": tool,
                "cmd": cmd,
                "effect": effect,
                "status": status,
                "count": count,
            })
        })
        .collect::<Vec<_>>();
    rows.sort_by_key(|row| std::cmp::Reverse(row["count"].as_u64().unwrap_or(0)));
    rows.truncate(40);
    rows
}

fn timeline_summary(sessions: &[SessionRecord]) -> Vec<Value> {
    let mut counts = BTreeMap::<String, u64>::new();
    for session in sessions {
        let key = session
            .start_ts_ms
            .and_then(DateTime::<Utc>::from_timestamp_millis)
            .map(|dt| dt.format("%Y-%m-%d").to_string())
            .unwrap_or_else(|| "unknown".to_string());
        *counts.entry(key).or_default() += 1;
    }
    counts
        .into_iter()
        .map(|(date, sessions)| json!({ "date": date, "sessions": sessions }))
        .collect()
}

fn semantic_mixing(system: &Counter) -> Value {
    let mut groups = BTreeMap::<String, BTreeMap<String, u64>>::new();
    let mut flat_groups = BTreeMap::<String, BTreeMap<String, u64>>::new();
    for (stack, weight) in system {
        let frames = stack.split(';').collect::<Vec<_>>();
        let semantic = frames
            .iter()
            .filter(|frame| frame.starts_with("session:") || frame.starts_with("prompt:"))
            .copied()
            .collect::<Vec<_>>()
            .join("/");
        let nonsemantic = frames
            .iter()
            .filter(|frame| !frame.starts_with("session:") && !frame.starts_with("prompt:"))
            .copied()
            .collect::<Vec<_>>()
            .join(";");
        let flat = frames
            .iter()
            .filter(|frame| {
                !frame.starts_with("project:")
                    && !frame.starts_with("agent:")
                    && !frame.starts_with("session:")
                    && !frame.starts_with("prompt:")
            })
            .copied()
            .collect::<Vec<_>>()
            .join(";");
        *groups
            .entry(nonsemantic)
            .or_default()
            .entry(semantic.clone())
            .or_default() += weight;
        *flat_groups
            .entry(flat)
            .or_default()
            .entry(semantic)
            .or_default() += weight;
    }
    json!({
        "nonsemantic": mixing_summary(&groups, system.values().sum()),
        "flat": mixing_summary(&flat_groups, system.values().sum()),
    })
}

fn mixing_summary(groups: &BTreeMap<String, BTreeMap<String, u64>>, total: u64) -> Value {
    let mut examples = Vec::new();
    let mut mixed_buckets = 0u64;
    let mut mixed_weight = 0u64;
    for (baseline_stack, variants) in groups {
        if variants.len() < 2 {
            continue;
        }
        mixed_buckets += 1;
        let weight = variants.values().sum::<u64>();
        mixed_weight += weight;
        let mut top_semantic_variants = variants
            .iter()
            .map(|(semantic, weight)| json!({ "semantic": semantic, "weight": weight }))
            .collect::<Vec<_>>();
        top_semantic_variants
            .sort_by_key(|row| std::cmp::Reverse(row["weight"].as_u64().unwrap_or(0)));
        top_semantic_variants.truncate(8);
        examples.push(json!({
            "kind": "nonsemantic_without_session_prompt",
            "baseline_stack": baseline_stack,
            "weight": weight,
            "semantic_variant_count": variants.len(),
            "top_semantic_variants": top_semantic_variants,
        }));
    }
    examples.sort_by_key(|row| std::cmp::Reverse(row["weight"].as_u64().unwrap_or(0)));
    examples.truncate(20);
    json!({
        "mixed_buckets": mixed_buckets,
        "mixed_weight": mixed_weight,
        "mixed_weight_pct": if total == 0 { 0.0 } else { round3(100.0 * mixed_weight as f64 / total as f64) },
        "examples": examples,
    })
}

fn session_to_json(session: &SessionRecord, include_previews: bool) -> Value {
    json!({
        "source": session.source,
        "session_id": session.session_id,
        "agent_sight_session_id": agent_sight_session_id(&session.source, &session.session_id),
        "session_file": session.path.file_name().and_then(|v| v.to_str()).unwrap_or("session"),
        "cwd_hash": if session.cwd.is_empty() { String::new() } else { short_hash(&session.cwd, 16) },
        "agent_role": session.agent_role,
        "model": session.model,
        "session_tag": session.session_tag,
        "start_ts_ms": session.start_ts_ms,
        "prompt_count": session.user_requests.len(),
        "tool_count": session.tools.len(),
        "llm_count": session.llm_calls.len(),
        "prompts": session.user_requests.iter().map(|req| json!({
            "index": req.index,
            "ts_ms": req.ts_ms,
            "hash": req.text_hash,
            "tag": req.tag,
            "preview": if include_previews { req.preview.clone() } else { "redacted".to_string() },
        })).collect::<Vec<_>>(),
        "tool_events": session.tools.iter().map(|event| {
            let request = session.request_by_index(event.request_index);
            json!({
                "ts_ms": event.ts_ms,
                "prompt_index": request.index,
                "prompt_tag": request.tag,
                "tool_name": event.tool_name,
                "category": event.category,
                "command_name": event.command_name,
                "command_hash": if event.command.is_empty() { String::new() } else { short_hash(&event.command, 16) },
                "command_preview": if include_previews { event.command.clone() } else { "redacted".to_string() },
                "process_chain": event.process_chain,
                "effect": event.effect,
                "status": event.status,
                "path_groups": event.path_groups,
                "domains": event.domains,
                "call_id_hash": event.call_id.as_ref().map(|id| short_hash(id, 16)),
            })
        }).collect::<Vec<_>>(),
        "llm_events": session.llm_calls.iter().map(|call| {
            let request = session.request_by_index(call.request_index);
            json!({
                "ts_ms": call.ts_ms,
                "prompt_index": request.index,
                "prompt_tag": request.tag,
                "llm_tag": call.tag,
                "model": call.model,
                "hash": call.text_hash,
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "cache_tokens": call.cache_tokens,
                "estimated_tokens": call.estimated_tokens,
                "preview": if include_previews { call.preview.clone() } else { "redacted".to_string() },
            })
        }).collect::<Vec<_>>()
    })
}

fn write_folded(path: &Path, stacks: &Counter) -> Result<()> {
    let mut text = String::new();
    for (stack, weight) in stacks {
        text.push_str(stack);
        text.push(' ');
        text.push_str(&weight.to_string());
        text.push('\n');
    }
    fs::write(path, text)?;
    Ok(())
}

fn artifact_map() -> Value {
    json!({
        "tag_cache": "tags.json",
        "semantic_system_folded": "semantic-system.folded.txt",
        "semantic_token_folded": "semantic-token.folded.txt",
        "nonsemantic_system_folded": "nonsemantic-system.folded.txt",
        "session_system_folded": "session-system.folded.txt",
        "prompt_system_folded": "prompt-system.folded.txt",
        "session_token_folded": "session-token.folded.txt",
        "prompt_token_folded": "prompt-token.folded.txt",
        "llm_token_folded": "llm-token.folded.txt",
        "dashboard": "index.html",
        "system_flamegraph": "system-flamegraph.svg",
        "token_flamegraph": "token-flamegraph.svg",
        "session_system": "session-system.svg",
        "prompt_system": "prompt-system.svg",
        "session_token": "session-token.svg",
        "prompt_token": "prompt-token.svg",
        "llm_token": "llm-token.svg",
        "tag_bars": "tag-bars.svg",
        "command_bars": "command-bars.svg",
        "timeline": "timeline.svg",
    })
}

fn write_dashboard(out_dir: &Path, payload: &Value) -> Result<()> {
    let folded_specs = [
        (
            "system-flamegraph.svg",
            "semantic-system.folded.txt",
            "System Footprint Flamegraph",
            "events",
        ),
        (
            "token-flamegraph.svg",
            "semantic-token.folded.txt",
            "Token Footprint Flamegraph",
            "tokens",
        ),
        (
            "session-system.svg",
            "session-system.folded.txt",
            "Session-System Projection",
            "events",
        ),
        (
            "prompt-system.svg",
            "prompt-system.folded.txt",
            "Prompt-System Projection",
            "events",
        ),
        (
            "session-token.svg",
            "session-token.folded.txt",
            "Session-Token Projection",
            "tokens",
        ),
        (
            "prompt-token.svg",
            "prompt-token.folded.txt",
            "Prompt-Token Projection",
            "tokens",
        ),
        (
            "llm-token.svg",
            "llm-token.folded.txt",
            "LLM-Token Projection",
            "tokens",
        ),
    ];
    for (svg_name, folded_name, title, metric) in folded_specs {
        let stacks = read_folded(&out_dir.join(folded_name))?;
        fs::write(
            out_dir.join(svg_name),
            flamegraph_svg(&stacks, title, metric),
        )?;
    }
    fs::write(
        out_dir.join("tag-bars.svg"),
        bar_svg(
            payload
                .pointer("/summary/top_prompt_tags")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default(),
            "tag",
            "count",
            "Top Prompt Tags",
        ),
    )?;
    fs::write(
        out_dir.join("command-bars.svg"),
        bar_svg(
            payload
                .pointer("/summary/command_summary")
                .and_then(Value::as_array)
                .map(|rows| {
                    rows.iter()
                        .map(|row| {
                            json!({
                                "label": format!(
                                    "{}:{}:{}:{}",
                                    row["agent"].as_str().unwrap_or("agent"),
                                    row["cmd"].as_str().unwrap_or("cmd"),
                                    row["effect"].as_str().unwrap_or("effect"),
                                    row["status"].as_str().unwrap_or("status")
                                ),
                                "count": row["count"].as_u64().unwrap_or(0),
                            })
                        })
                        .collect::<Vec<_>>()
                })
                .unwrap_or_default(),
            "label",
            "count",
            "Top Commands And Effects",
        ),
    )?;
    fs::write(
        out_dir.join("timeline.svg"),
        bar_svg(
            payload
                .pointer("/summary/timeline")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default(),
            "date",
            "sessions",
            "Session Timeline",
        ),
    )?;
    let html = format!(
        "<!doctype html><html><head><meta charset='utf-8'><title>agentpprof Report</title>\
         <style>body{{font-family:system-ui;margin:0;background:#f7f7f2;color:#17202a}}header{{padding:24px;background:#17202a;color:white}}main{{padding:24px}}.panel{{background:white;border:1px solid #ddd8ca;border-radius:8px;padding:12px;margin:12px 0;overflow:auto}}img{{max-width:none}}</style></head>\
         <body><header><h1>agentpprof Report</h1><div>Generated {}</div></header><main>\
         <div class='panel'><img src='tag-bars.svg'></div><div class='panel'><img src='command-bars.svg'></div><div class='panel'><img src='timeline.svg'></div>\
         <div class='panel'><img src='system-flamegraph.svg'></div><div class='panel'><img src='token-flamegraph.svg'></div>\
         <div class='panel'><img src='session-system.svg'></div><div class='panel'><img src='prompt-system.svg'></div>\
         <div class='panel'><img src='session-token.svg'></div><div class='panel'><img src='prompt-token.svg'></div><div class='panel'><img src='llm-token.svg'></div>\
         </main></body></html>",
        html_escape(payload["generated_at"].as_str().unwrap_or(""))
    );
    fs::write(out_dir.join("index.html"), html)?;
    Ok(())
}

fn read_folded(path: &Path) -> Result<Counter> {
    let mut out = Counter::new();
    if !path.exists() {
        return Ok(out);
    }
    for line in fs::read_to_string(path)?.lines() {
        if let Some((stack, weight)) = line.rsplit_once(' ') {
            if let Ok(weight) = weight.parse::<u64>() {
                *out.entry(stack.to_string()).or_default() += weight;
            }
        }
    }
    Ok(out)
}

fn flamegraph_svg(stacks: &Counter, title: &str, metric: &str) -> String {
    let width = 1400.0;
    let total = stacks.values().sum::<u64>();
    if total == 0 {
        return format!(
            "<svg xmlns='http://www.w3.org/2000/svg' width='1400' height='120'><text x='16' y='40'>{}</text></svg>",
            html_escape(title)
        );
    }
    let levels = stacks
        .keys()
        .map(|stack| stack.split(';').count())
        .max()
        .unwrap_or(1);
    let height = 80.0 + levels as f64 * 22.0 + 24.0;
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='1400' height='{height}' viewBox='0 0 1400 {height}'>\
         <style>text{{font-family:ui-monospace,Menlo,monospace;font-size:11px}}.title{{font-family:system-ui,sans-serif;font-size:18px;font-weight:700}}</style>\
         <rect width='1400' height='{height}' fill='#fbfbf7'/><text class='title' x='16' y='28'>{}</text><text x='16' y='48'>width = {}; total = {}</text>",
        html_escape(title),
        html_escape(metric),
        total
    );
    let mut x = 16.0;
    for WeightedStack { stack, weight } in top_stacks(stacks, 2000) {
        let w = (width - 32.0) * weight as f64 / total as f64;
        if w < 0.5 {
            continue;
        }
        for (depth, frame) in stack.split(';').enumerate() {
            let y = 64.0 + depth as f64 * 22.0;
            let color = color_for(frame, depth);
            svg.push_str(&format!(
                "<rect x='{x:.2}' y='{y:.2}' width='{w:.2}' height='21' fill='{color}' stroke='#fff' stroke-width='.7'><title>{} | {} {}</title></rect>",
                html_escape(frame),
                weight,
                html_escape(metric)
            ));
            if w > 60.0 {
                let label = truncate_clean(frame, 32);
                svg.push_str(&format!(
                    "<text x='{:.2}' y='{:.2}'>{}</text>",
                    x + 4.0,
                    y + 15.0,
                    html_escape(&label)
                ));
            }
        }
        x += w;
    }
    svg.push_str("</svg>");
    svg
}

fn bar_svg(rows: Vec<Value>, label_key: &str, value_key: &str, title: &str) -> String {
    let rows = rows.into_iter().take(12).collect::<Vec<_>>();
    let max_value = rows
        .iter()
        .filter_map(|row| row.get(value_key).and_then(Value::as_u64))
        .max()
        .unwrap_or(1);
    let height = 70 + rows.len() * 24;
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='760' height='{height}' viewBox='0 0 760 {height}'>\
         <style>text{{font-family:system-ui,sans-serif;font-size:12px}}.title{{font-size:16px;font-weight:700}}</style>\
         <rect width='760' height='{height}' fill='#fbfbf7'/><text class='title' x='16' y='26'>{}</text>",
        html_escape(title)
    );
    for (idx, row) in rows.iter().enumerate() {
        let y = 46 + idx * 24;
        let value = row.get(value_key).and_then(Value::as_u64).unwrap_or(0);
        let label = row
            .get(label_key)
            .and_then(Value::as_str)
            .map(str::to_string)
            .unwrap_or_else(|| value.to_string());
        let w = 480.0 * value as f64 / max_value as f64;
        svg.push_str(&format!(
            "<text x='16' y='{}'>{}</text><rect x='230' y='{}' width='{:.1}' height='18' fill='#3b82f6' rx='2'/><text x='{:.1}' y='{}'>{}</text>",
            y + 13,
            html_escape(&truncate_clean(&label, 32)),
            y,
            w,
            235.0 + w,
            y + 13,
            value
        ));
    }
    svg.push_str("</svg>");
    svg
}

fn command_bench(args: BenchArgs) -> Result<()> {
    let out = args
        .out
        .unwrap_or_else(|| PathBuf::from(".agentsight/agentpprof/benchmarks.json"));
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent)?;
    }
    let fragments = bench_fragments(&args.fragments, &args.fragment_files)?;
    let mut results = Vec::new();
    for spec in &args.models {
        let (label, path) = parse_model_spec(spec)?;
        let port = free_port()?;
        let base_url = format!("http://127.0.0.1:{port}");
        let started = Instant::now();
        let mut child = spawn_llama_server(&args.llama_server, &args.server_args, &path, port)
            .with_context(|| format!("starting llama-server for {label}"))?;
        let loaded = wait_for_llama(&base_url, Duration::from_secs(args.load_timeout));
        let load_ms = started.elapsed().as_millis() as u64;
        let mut model_result = json!({
            "label": label,
            "path": path,
            "base_url": base_url,
            "load_ms": load_ms,
            "runs": [],
        });
        match loaded {
            Ok(()) => {
                let mut tagger = LlamaTagger::new(
                    std::env::temp_dir().join(format!("agentpprof-bench-{port}.tags.json")),
                    base_url.clone(),
                    "local".to_string(),
                    Duration::from_secs(args.request_timeout),
                    -1,
                );
                let mut run_rows = Vec::new();
                let mut fragment_rows = Vec::new();
                for (fragment_idx, prompt) in fragments.iter().enumerate() {
                    let mut fragment_run_rows = Vec::new();
                    let mut ok_tags = Vec::new();
                    for repeat_idx in 0..args.runs {
                        let req_started = Instant::now();
                        let result = tagger.tag_uncached("prompt", prompt);
                        let latency_ms = req_started.elapsed().as_millis() as u64;
                        let run_row = match result {
                            Ok(tag) => {
                                ok_tags.push(tag.clone());
                                json!({
                                    "fragment_id": format!("f{fragment_idx}"),
                                    "fragment_hash": short_hash(prompt, 16),
                                    "repeat": repeat_idx,
                                    "latency_ms": latency_ms,
                                    "ok": true,
                                    "tag": tag,
                                })
                            }
                            Err(error) => json!({
                                "fragment_id": format!("f{fragment_idx}"),
                                "fragment_hash": short_hash(prompt, 16),
                                "repeat": repeat_idx,
                                "latency_ms": latency_ms,
                                "ok": false,
                                "error": error.to_string(),
                            }),
                        };
                        fragment_run_rows.push(run_row.clone());
                        run_rows.push(run_row);
                    }
                    let summary = stability_summary(&ok_tags, args.runs);
                    let mut fragment_row = json!({
                        "fragment_id": format!("f{fragment_idx}"),
                        "fragment_hash": short_hash(prompt, 16),
                        "runs": fragment_run_rows,
                        "ok_runs": ok_tags.len(),
                        "failed_runs": args.runs.saturating_sub(ok_tags.len()),
                        "tags": ok_tags,
                        "modal_tag": summary.modal_tag,
                        "distinct_tags": summary.distinct_tags,
                        "exact_stable": summary.exact_stable,
                    });
                    if args.include_fragment_previews {
                        fragment_row["preview"] = Value::String(truncate_clean(prompt, 140));
                    }
                    fragment_rows.push(fragment_row);
                }
                model_result["runs"] = Value::Array(run_rows);
                model_result["fragments"] = Value::Array(fragment_rows.clone());
                model_result["stability"] =
                    serde_json::to_value(model_stability_summary(&fragment_rows, args.runs))?;
                model_result["tagger_stats"] = serde_json::to_value(&tagger.stats)?;
            }
            Err(error) => {
                model_result["error"] = Value::String(error.to_string());
            }
        }
        stop_child(&mut child);
        results.push(model_result);
    }
    let payload = json!({
        "schema_version": 1,
        "generated_at": now_iso(),
        "llama_server": args.llama_server,
        "server_args": args.server_args,
        "runs_per_model": args.runs,
        "repeats_per_fragment": args.runs,
        "fragments_per_model": fragments.len(),
        "fragment_previews_included": args.include_fragment_previews,
        "models": results,
    });
    fs::write(&out, serde_json::to_vec_pretty(&payload)?)?;
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
}

fn bench_fragments(custom: &[String], fragment_files: &[PathBuf]) -> Result<Vec<String>> {
    let mut fragments = Vec::new();
    for path in fragment_files {
        let contents = fs::read_to_string(path)
            .with_context(|| format!("reading fragment file {}", path.display()))?;
        for line in contents.lines() {
            let fragment = line.trim();
            if fragment.is_empty() {
                continue;
            }
            fragments.push(fragment.to_string());
        }
    }
    fragments.extend(custom.iter().cloned());
    if !fragments.is_empty() {
        return Ok(fragments);
    }
    Ok(vec![
        "User asks the coding agent to fix a failing Rust unit test, edit source code, and rerun cargo test.".to_string(),
        "User asks the agent to summarize research evidence and update an OSDI experiment plan without changing source code.".to_string(),
        "An assistant LLM call compares span-duration traces with semantic system-effect attribution for a paper draft.".to_string(),
    ])
}

#[derive(Serialize)]
struct FragmentStability {
    exact_stable: bool,
    modal_tag: Option<String>,
    distinct_tags: usize,
}

fn stability_summary(tags: &[String], expected_runs: usize) -> FragmentStability {
    let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
    for tag in tags {
        *counts.entry(tag.as_str()).or_default() += 1;
    }
    let modal_tag = counts
        .iter()
        .max_by_key(|(_, count)| *count)
        .map(|(tag, _)| (*tag).to_string());
    FragmentStability {
        exact_stable: tags.len() == expected_runs && counts.len() == 1,
        modal_tag,
        distinct_tags: counts.len(),
    }
}

#[derive(Serialize)]
struct ModelStability {
    requested_runs: usize,
    fragment_count: usize,
    exact_stable_fragments: usize,
    exact_stability_pct: f64,
    valid_run_pct: f64,
}

fn model_stability_summary(fragment_rows: &[Value], runs_per_fragment: usize) -> ModelStability {
    let fragment_count = fragment_rows.len();
    let exact_stable_fragments = fragment_rows
        .iter()
        .filter(|row| {
            row.get("exact_stable")
                .and_then(Value::as_bool)
                .unwrap_or(false)
        })
        .count();
    let ok_runs: usize = fragment_rows
        .iter()
        .map(|row| row.get("ok_runs").and_then(Value::as_u64).unwrap_or(0) as usize)
        .sum();
    let requested_runs = fragment_count * runs_per_fragment;
    ModelStability {
        requested_runs,
        fragment_count,
        exact_stable_fragments,
        exact_stability_pct: if fragment_count > 0 {
            round3(100.0 * exact_stable_fragments as f64 / fragment_count as f64)
        } else {
            0.0
        },
        valid_run_pct: if requested_runs > 0 {
            round3(100.0 * ok_runs as f64 / requested_runs as f64)
        } else {
            0.0
        },
    }
}

fn parse_model_spec(spec: &str) -> Result<(String, PathBuf)> {
    if let Some((label, path)) = spec.split_once('=') {
        Ok((label.to_string(), PathBuf::from(path)))
    } else {
        let path = PathBuf::from(spec);
        let label = path
            .file_stem()
            .and_then(|v| v.to_str())
            .unwrap_or("model")
            .to_string();
        Ok((label, path))
    }
}

fn free_port() -> Result<u16> {
    let listener = TcpListener::bind("127.0.0.1:0")?;
    Ok(listener.local_addr()?.port())
}

fn spawn_llama_server(
    server: &Path,
    server_args: &[String],
    model: &Path,
    port: u16,
) -> Result<Child> {
    let use_path_lookup = server.components().count() == 1 && !server.is_absolute();
    if !use_path_lookup && !server.exists() {
        bail!("llama-server not found: {}", server.display());
    }
    if !model.exists() {
        bail!("model not found: {}", model.display());
    }
    let mut command = Command::new(server);
    command
        .arg("-m")
        .arg(model)
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg(port.to_string())
        .args(server_args)
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    Ok(command.spawn()?)
}

fn wait_for_llama(base_url: &str, timeout: Duration) -> Result<()> {
    let deadline = Instant::now() + timeout;
    let agent = ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(2))
        .timeout_write(Duration::from_secs(2))
        .build();
    while Instant::now() < deadline {
        if agent.get(&format!("{base_url}/v1/models")).call().is_ok() {
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    bail!(
        "llama-server did not become ready within {}s",
        timeout.as_secs()
    )
}

fn stop_child(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

fn tool_event_from_input(
    project_root: &Path,
    ts_ms: Option<i64>,
    request_index: usize,
    name: &str,
    input: &Value,
    call_id: Option<String>,
) -> ToolEvent {
    let command = command_from_tool_input(input);
    let category = tool_category(name, &command);
    let domains = extract_domains(&command);
    let command_name = if category == "shell" {
        basename_from_command(&command)
    } else if category == "network" && !domains.is_empty() {
        domains[0]
            .split(':')
            .next()
            .unwrap_or("network")
            .to_string()
    } else {
        one_word(name, "tool")
    };
    let effect = if name == "apply_patch" || command.contains("*** ") {
        "write".to_string()
    } else {
        command_effect(&command)
    };
    let path_groups = extract_path_groups(project_root, name, input, &command);
    let process_chain = if category == "shell" {
        command_process_chain(&command)
    } else {
        Vec::new()
    };
    ToolEvent {
        ts_ms,
        request_index,
        tool_name: name.to_string(),
        category,
        command,
        command_name,
        effect,
        process_chain,
        status: "observed".to_string(),
        path_groups,
        domains,
        call_id,
    }
}

fn command_from_tool_input(input: &Value) -> String {
    for key in ["cmd", "command", "pattern", "file_path", "path", "text"] {
        if let Some(value) = input.get(key).and_then(Value::as_str) {
            if !value.is_empty() {
                return if key == "pattern" {
                    format!("search {value}")
                } else {
                    value.to_string()
                };
            }
        }
    }
    if input.is_null() {
        String::new()
    } else {
        truncate_clean(&input.to_string(), 300)
    }
}

fn parse_tool_args(value: &Value) -> Value {
    if let Some(text) = value.as_str() {
        serde_json::from_str(text).unwrap_or_else(|_| json!({ "text": text }))
    } else {
        value.clone()
    }
}

fn status_from_output(output: &str) -> &'static str {
    let lowered = output.to_ascii_lowercase();
    if lowered.contains("process exited with code 0") || lowered.contains("\"is_error\":false") {
        "ok"
    } else if lowered.contains("process exited with code")
        || lowered.contains("\"is_error\":true")
        || lowered.contains("error")
    {
        "fail"
    } else {
        "observed"
    }
}

fn tool_category(name: &str, command: &str) -> String {
    let n = name.to_ascii_lowercase();
    if n.ends_with("exec_command") || n == "bash" {
        "shell"
    } else if ["apply_patch", "edit", "write", "multiedit", "notebookedit"].contains(&n.as_str()) {
        "edit"
    } else if ["read", "grep", "glob", "ls"].contains(&n.as_str()) {
        "read"
    } else if n.contains("web")
        || n.contains("browser")
        || n.contains("search")
        || command.contains("http")
    {
        "network"
    } else if n.contains("plan") || n.contains("todo") {
        "plan"
    } else if n.contains("task") || n.contains("agent") {
        "subagent"
    } else {
        "tool"
    }
    .to_string()
}

fn command_effect(command: &str) -> String {
    let cmd = basename_from_command(command);
    let text = command.to_ascii_lowercase();
    if ["cargo", "pytest", "npm", "pnpm", "yarn", "go", "make"].contains(&cmd.as_str())
        && any_word(&text, &["test", "check", "build", "clippy"])
    {
        "test"
    } else if cmd == "git"
        && any_word(
            &text,
            &["commit", "push", "add", "checkout", "merge", "rebase"],
        )
    {
        "repo"
    } else if ["curl", "wget", "ssh", "scp", "git"].contains(&cmd.as_str())
        && (any_word(
            &text,
            &["clone", "fetch", "pull", "push", "curl", "wget", "ssh"],
        ) || text.contains("http://")
            || text.contains("https://"))
    {
        "network"
    } else if [
        "tee", "cp", "mv", "rm", "mkdir", "touch", "python", "python3", "node", "npm",
    ]
    .contains(&cmd.as_str())
        && (text.contains('>')
            || text.contains("--write")
            || text.contains(" rm ")
            || text.contains(" mkdir ")
            || text.contains(" touch ")
            || text.contains(" cp ")
            || text.contains(" mv "))
    {
        "write"
    } else if [
        "rg", "grep", "sed", "cat", "head", "tail", "find", "ls", "nl", "wc", "jq", "git",
    ]
    .contains(&cmd.as_str())
    {
        "read"
    } else if text.contains("http://")
        || text.contains("https://")
        || text.contains("crates.io")
        || text.contains("github.com")
    {
        "network"
    } else {
        "process"
    }
    .to_string()
}

fn any_word(text: &str, words: &[&str]) -> bool {
    text.split(|c: char| !c.is_ascii_alphanumeric() && c != '_')
        .any(|part| words.contains(&part))
}

fn basename_from_command(command: &str) -> String {
    let parts = split_shell(command);
    let mut idx = 0;
    while idx < parts.len()
        && ["sudo", "env", "command", "time", "timeout", "nice", "nohup"].contains(
            &Path::new(&parts[idx])
                .file_name()
                .and_then(|v| v.to_str())
                .unwrap_or(""),
        )
    {
        idx += 1;
        if idx < parts.len() && parts[idx].starts_with('-') {
            idx += 1;
        }
    }
    parts
        .get(idx)
        .and_then(|part| Path::new(part).file_name().and_then(|v| v.to_str()))
        .unwrap_or("none")
        .to_string()
}

fn command_process_chain(command: &str) -> Vec<String> {
    process_chain_from_parts(&split_shell(command))
}

fn process_chain_from_parts(parts: &[String]) -> Vec<String> {
    if parts.is_empty() {
        return Vec::new();
    }
    let mut idx = 0;
    while idx < parts.len()
        && ["sudo", "env", "command", "time", "timeout", "nice", "nohup"].contains(
            &Path::new(&parts[idx])
                .file_name()
                .and_then(|v| v.to_str())
                .unwrap_or(""),
        )
    {
        idx += 1;
        if idx < parts.len() && parts[idx].starts_with('-') {
            idx += 1;
        }
    }
    let Some(proc_name) = parts
        .get(idx)
        .and_then(|part| Path::new(part).file_name().and_then(|v| v.to_str()))
    else {
        return Vec::new();
    };
    let mut chain = vec![proc_name.to_string()];
    if ["bash", "sh", "zsh"].contains(&proc_name) {
        for flag_idx in idx + 1..parts.len().saturating_sub(1) {
            if ["-c", "-lc", "-cl"].contains(&parts[flag_idx].as_str()) {
                chain.extend(command_process_chain(&parts[flag_idx + 1]));
                break;
            }
        }
    }
    chain.truncate(6);
    chain
}

fn split_shell(command: &str) -> Vec<String> {
    shell_words::split(command)
        .unwrap_or_else(|_| command.split_whitespace().map(str::to_string).collect())
}

fn extract_domains(text: &str) -> Vec<String> {
    let mut domains = BTreeSet::new();
    for part in text.split(|c: char| c.is_whitespace() || ['"', '\'', ')', '('].contains(&c)) {
        let stripped = part
            .strip_prefix("https://")
            .or_else(|| part.strip_prefix("http://"));
        if let Some(rest) = stripped {
            if let Some(domain) = rest.split('/').next() {
                if !domain.is_empty() {
                    domains.insert(domain.to_ascii_lowercase());
                }
            }
        }
        for known in [
            "github.com",
            "crates.io",
            "huggingface.co",
            "hf.co",
            "openai.com",
            "anthropic.com",
        ] {
            if part.contains(known) {
                domains.insert(known.to_string());
            }
        }
    }
    domains.into_iter().take(8).collect()
}

fn extract_path_groups(
    project_root: &Path,
    name: &str,
    input: &Value,
    command: &str,
) -> Vec<String> {
    let mut groups = BTreeSet::new();
    if ["write", "edit", "multiedit", "notebookedit", "read"]
        .contains(&name.to_ascii_lowercase().as_str())
    {
        for key in ["file_path", "path"] {
            if let Some(path) = input.get(key).and_then(Value::as_str) {
                groups.insert(path_group(path, project_root));
            }
        }
    }
    for part in split_shell(command) {
        if plausible_path_token(&part) {
            groups.insert(path_group(&part, project_root));
        }
    }
    groups.into_iter().filter(|v| v != "none").take(8).collect()
}

fn plausible_path_token(part: &str) -> bool {
    let part = part.trim_matches(['"', '\'']);
    if part.is_empty()
        || part.starts_with('-')
        || part.starts_with('$')
        || part.starts_with("http://")
        || part.starts_with("https://")
        || part.len() > 140
        || part.chars().any(|c| "{}()=;<>|`".contains(c))
    {
        return false;
    }
    let suffix = Path::new(part)
        .extension()
        .and_then(|v| v.to_str())
        .unwrap_or("");
    part.contains('/')
        || [
            "rs", "py", "md", "json", "ts", "tsx", "toml", "lock", "js", "c", "h", "svg", "html",
            "css",
        ]
        .contains(&suffix)
}

fn path_group(path: &str, project_root: &Path) -> String {
    let path = path.trim_matches(['"', '\'']);
    if path.is_empty() {
        return "none".to_string();
    }
    let p = Path::new(path);
    let parts = if p.is_absolute() {
        p.strip_prefix(project_root)
            .ok()
            .map(|rel| {
                rel.components()
                    .map(|c| c.as_os_str().to_string_lossy().to_string())
                    .collect::<Vec<_>>()
            })
            .unwrap_or_else(|| {
                p.components()
                    .map(|c| c.as_os_str().to_string_lossy().to_string())
                    .rev()
                    .take(3)
                    .collect::<Vec<_>>()
                    .into_iter()
                    .rev()
                    .collect()
            })
    } else {
        p.components()
            .map(|c| c.as_os_str().to_string_lossy().to_string())
            .collect::<Vec<_>>()
    };
    let parts = parts
        .into_iter()
        .filter(|part| part != "." && !part.is_empty())
        .map(|part| {
            if part.chars().count() > 48 {
                format!("{}...", part.chars().take(45).collect::<String>())
            } else {
                part
            }
        })
        .collect::<Vec<_>>();
    if parts.is_empty() {
        "repo".to_string()
    } else if ["collector", "frontend", "docs", "bpf", "agentpprof"].contains(&parts[0].as_str()) {
        parts.into_iter().take(3).collect::<Vec<_>>().join("/")
    } else {
        parts.into_iter().take(2).collect::<Vec<_>>().join("/")
    }
}

fn content_to_text(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        Value::Array(items) => items
            .iter()
            .filter_map(|item| {
                if let Some(text) = item.as_str() {
                    return Some(text.to_string());
                }
                let typ = item.get("type").and_then(Value::as_str).unwrap_or("");
                if typ == "tool_result" {
                    return None;
                }
                item.get("text")
                    .or_else(|| item.get("content"))
                    .and_then(Value::as_str)
                    .map(str::to_string)
            })
            .collect::<Vec<_>>()
            .join("\n"),
        Value::Object(_) => value
            .get("text")
            .or_else(|| value.get("content"))
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string(),
        _ => String::new(),
    }
}

fn claude_is_tool_result(content: &Value) -> bool {
    content.as_array().is_some_and(|items| {
        !items.is_empty()
            && items
                .iter()
                .all(|item| item.get("type").and_then(Value::as_str) == Some("tool_result"))
    })
}

fn claude_tool_result_ids(content: &Value) -> Vec<String> {
    content
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|item| {
            item.get("tool_use_id")
                .and_then(Value::as_str)
                .map(str::to_string)
        })
        .collect()
}

fn default_claude_root(project_root: &Path) -> Result<PathBuf> {
    let _ = project_root;
    dirs::home_dir()
        .map(|home| home.join(".claude/projects"))
        .ok_or_else(|| anyhow!("cannot determine home directory"))
}

fn json_u64(value: &Value, key: &str) -> u64 {
    value.get(key).and_then(Value::as_u64).unwrap_or(0)
}

fn parse_ts_ms(value: &str) -> Option<i64> {
    DateTime::parse_from_rfc3339(value)
        .ok()
        .map(|dt| dt.timestamp_millis())
}

fn now_iso() -> String {
    Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

fn short_hash(text: &str, n: usize) -> String {
    let digest = Sha256::digest(text.as_bytes());
    hex::encode(digest).chars().take(n).collect()
}

fn truncate_clean(text: &str, limit: usize) -> String {
    let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if text.chars().count() <= limit {
        return text;
    }
    text.chars()
        .take(limit.saturating_sub(1))
        .collect::<String>()
        + "."
}

fn safe_frame(text: &str, prefix: Option<&str>) -> String {
    let mut out = String::new();
    for ch in text.to_ascii_lowercase().chars() {
        if ch.is_ascii_alphanumeric() || "._:/+-".contains(ch) {
            out.push(ch);
        } else if !out.ends_with('_') {
            out.push('_');
        }
    }
    let trimmed = out.trim_matches(['_', ';']).to_string();
    let value = if trimmed.is_empty() {
        "unknown".to_string()
    } else {
        trimmed
    };
    match prefix {
        Some(prefix) => format!("{prefix}:{value}"),
        None => value,
    }
}

fn one_word(text: &str, default: &str) -> String {
    let mut cur = String::new();
    for ch in text.to_ascii_lowercase().chars() {
        if ch.is_ascii_alphanumeric() {
            cur.push(ch);
        } else if cur.len() >= 2 {
            break;
        } else {
            cur.clear();
        }
    }
    if cur.len() >= 2 {
        cur
    } else {
        default.to_string()
    }
}

fn sanitize_tag(text: &str) -> Option<String> {
    let trimmed = text
        .trim()
        .trim_matches(|c: char| {
            c.is_whitespace() || ['"', '\'', '`', '*', '_', '.', '>'].contains(&c)
        })
        .to_ascii_lowercase();
    let words = trimmed
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();
    if words.len() == 1 {
        Some(words[0].to_string())
    } else {
        None
    }
}

fn valid_tag(tag: &str) -> bool {
    let mut chars = tag.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    first.is_ascii_lowercase()
        && (3..=12).contains(&tag.len())
        && tag.chars().all(|c| c.is_ascii_lowercase())
        && !["task", "work", "misc", "thing", "stuff", "other"].contains(&tag)
}

fn agent_family(source: &str) -> String {
    if source.starts_with("codex") {
        "codex".to_string()
    } else if source.starts_with("claude") {
        "claude".to_string()
    } else {
        source.to_string()
    }
}

fn short_session_id(session_id: &str) -> String {
    let compact = session_id
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or(session_id)
        .trim_end_matches(".jsonl");
    if compact.is_empty() {
        "session".to_string()
    } else if compact.chars().count() <= 12 {
        compact.to_string()
    } else {
        let head = compact.chars().take(6).collect::<String>();
        let tail = compact
            .chars()
            .rev()
            .take(5)
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect::<String>();
        format!("{head}.{tail}")
    }
}

fn agent_sight_session_id(source: &str, session_id: &str) -> String {
    let family = agent_family(source);
    format!("local:{family}:{family}:{}", short_session_id(session_id))
}

fn last_model_segment(model: &str) -> &str {
    model.rsplit('/').next().unwrap_or(model)
}

fn round3(value: f64) -> f64 {
    (value * 1000.0).round() / 1000.0
}

fn html_escape(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn color_for(text: &str, depth: usize) -> String {
    let digest = Sha256::digest(text.as_bytes());
    let hue = (digest[0] as usize + depth * 19) % 360;
    let sat = 48 + digest[1] % 20;
    let light = 62 + digest[2] % 12;
    format!("hsl({hue} {sat}% {light}%)")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn command_process_chain_keeps_shell_wrapper_nesting() {
        assert_eq!(
            command_process_chain("bash -lc 'cargo test --manifest-path collector/Cargo.toml'"),
            vec!["bash".to_string(), "cargo".to_string()]
        );
    }

    #[test]
    fn tag_validation_has_no_label_fallback() {
        assert!(valid_tag("debug"));
        assert!(!valid_tag("two words"));
        assert!(!valid_tag("task"));
        assert_eq!(sanitize_tag("debug."), Some("debug".to_string()));
        assert_eq!(sanitize_tag("debug tests"), None);
        assert!(!valid_tag("codingupdateflamegraph"));
    }

    #[test]
    fn agent_sight_session_id_matches_collector_shape() {
        assert_eq!(
            agent_sight_session_id("codex", "019ec561-a99a-7a81-a344-6d898f7615ab"),
            "local:codex:codex:019ec5.615ab"
        );
    }

    #[test]
    fn folded_stacks_keep_semantic_call_process_effect_order() {
        let session = SessionRecord {
            source: "codex".to_string(),
            path: PathBuf::from("session.jsonl"),
            session_id: "s1".to_string(),
            cwd: "/repo".to_string(),
            agent_role: "agent".to_string(),
            model: "gpt-5".to_string(),
            title: "fix tests".to_string(),
            start_ts_ms: Some(1),
            user_requests: vec![UserRequest {
                index: 0,
                ts_ms: Some(1),
                text_hash: "h1".to_string(),
                preview: "fix rust tests".to_string(),
                tag: "debug".to_string(),
            }],
            tools: vec![ToolEvent {
                ts_ms: Some(2),
                request_index: 0,
                tool_name: "exec_command".to_string(),
                category: "shell".to_string(),
                command: "bash -lc 'cargo test'".to_string(),
                command_name: "cargo".to_string(),
                effect: "test".to_string(),
                process_chain: vec!["bash".to_string(), "cargo".to_string()],
                status: "ok".to_string(),
                path_groups: vec!["repo".to_string()],
                domains: Vec::new(),
                call_id: Some("call-1".to_string()),
            }],
            llm_calls: vec![LlmEvent {
                ts_ms: Some(3),
                request_index: 0,
                model: "gpt-5".to_string(),
                text_hash: "l1".to_string(),
                preview: "ran tests".to_string(),
                input_tokens: 11,
                output_tokens: 7,
                cache_tokens: 0,
                estimated_tokens: 0,
                tag: "summarize".to_string(),
            }],
            session_tag: "rustfix".to_string(),
        };
        let (system, token, prompts) = build_folded_stacks(&[session], "agentsight");
        assert_eq!(prompts.len(), 1);
        assert_eq!(
            system.get(
                "project:agentsight;agent:codex;session:rustfix;prompt:debug;call:tool/shell;process:bash;process:cargo;effect:test;path:repo;status:ok"
            ),
            Some(&1)
        );
        assert_eq!(
            token.get(
                "project:agentsight;agent:codex;session:rustfix;prompt:debug;call:llm/summarize;model:gpt-5;kind:input"
            ),
            Some(&11)
        );
        assert_eq!(
            token.get(
                "project:agentsight;agent:codex;session:rustfix;prompt:debug;call:llm/summarize;model:gpt-5;kind:output"
            ),
            Some(&7)
        );
    }

    #[test]
    fn token_components_do_not_stack_estimates_on_reported_tokens() {
        let mut call = LlmEvent {
            ts_ms: None,
            request_index: 0,
            model: "model".to_string(),
            text_hash: "h".to_string(),
            preview: "preview".to_string(),
            input_tokens: 10,
            output_tokens: 5,
            cache_tokens: 0,
            estimated_tokens: 1_000,
            tag: "answer".to_string(),
        };
        assert_eq!(call.token_components(), vec![("input", 10), ("output", 5)]);

        call.input_tokens = 0;
        call.output_tokens = 0;
        call.estimated_tokens = 500_000;
        assert_eq!(call.token_components(), vec![("unknown", 1)]);
    }

    #[test]
    fn pprof_writer_emits_gzip_profile() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("profile.pb.gz");
        let projection = ProfileProjection {
            view: "tasks".to_string(),
            sample_type: "events",
            unit: "count",
            stacks: BTreeMap::from([("project:test;agent:codex;prompt:debug".to_string(), 7)]),
        };
        write_pprof_projection(&projection, &path).unwrap();
        let bytes = fs::read(path).unwrap();
        assert_eq!(&bytes[..2], &[0x1f, 0x8b]);
    }

    #[test]
    fn model_specs_accept_explicit_labels_or_path_stems() {
        let (label, path) = parse_model_spec("0.6b=/models/qwen.gguf").unwrap();
        assert_eq!(label, "0.6b");
        assert_eq!(path, PathBuf::from("/models/qwen.gguf"));

        let (label, path) = parse_model_spec("/models/localmodel.gguf").unwrap();
        assert_eq!(label, "localmodel");
        assert_eq!(path, PathBuf::from("/models/localmodel.gguf"));
    }

    #[test]
    fn bench_fragments_use_stable_defaults_unless_overridden() {
        let defaults = bench_fragments(&[], &[]).unwrap();
        assert_eq!(defaults.len(), 3);
        assert!(
            defaults
                .iter()
                .all(|fragment| !fragment.contains("Benchmark run"))
        );

        let custom = vec!["repeat exactly this prompt".to_string()];
        assert_eq!(bench_fragments(&custom, &[]).unwrap(), custom);
    }

    #[test]
    fn bench_fragments_accept_file_inputs() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("fragments.txt");
        fs::write(
            &path,
            "\n# markdown heading fragment\nfirst fixed fragment\nsecond fixed fragment\n",
        )
        .unwrap();
        let custom = vec!["third fixed fragment".to_string()];
        assert_eq!(
            bench_fragments(&custom, &[path]).unwrap(),
            vec![
                "# markdown heading fragment".to_string(),
                "first fixed fragment".to_string(),
                "second fixed fragment".to_string(),
                "third fixed fragment".to_string(),
            ]
        );
    }

    #[test]
    fn stability_summary_requires_all_repeats_same_tag() {
        let stable = stability_summary(
            &[
                "debug".to_string(),
                "debug".to_string(),
                "debug".to_string(),
            ],
            3,
        );
        assert!(stable.exact_stable);
        assert_eq!(stable.modal_tag, Some("debug".to_string()));
        assert_eq!(stable.distinct_tags, 1);

        let changed = stability_summary(
            &["debug".to_string(), "test".to_string(), "debug".to_string()],
            3,
        );
        assert!(!changed.exact_stable);
        assert_eq!(changed.distinct_tags, 2);

        let failed_repeat = stability_summary(&["debug".to_string(), "debug".to_string()], 3);
        assert!(!failed_repeat.exact_stable);
        assert_eq!(failed_repeat.distinct_tags, 1);
    }

    #[test]
    fn model_stability_summary_counts_exact_stable_fragments() {
        let fragments = vec![
            json!({
                "ok_runs": 3,
                "exact_stable": true,
            }),
            json!({
                "ok_runs": 2,
                "exact_stable": false,
            }),
        ];
        let summary = model_stability_summary(&fragments, 3);
        assert_eq!(summary.requested_runs, 6);
        assert_eq!(summary.fragment_count, 2);
        assert_eq!(summary.exact_stable_fragments, 1);
        assert_eq!(summary.exact_stability_pct, 50.0);
        assert_eq!(summary.valid_run_pct, 83.333);
    }
}
