use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, Utc};
use clap::{Parser, Subcommand};
use normalize_chat_sessions::{
    parse_session, ClaudeCodeFormat, CodexFormat, ContentBlock, LogFormat, Role,
    Session as NormalizedSession,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::fs;
use std::io::{BufRead, BufReader};
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
#[command(name = "agentflame")]
#[command(about = "Rust local AI-agent session tagger and semantic flamegraph generator")]
struct Cli {
    #[command(subcommand)]
    command: Option<CommandKind>,
}

#[derive(Subcommand)]
enum CommandKind {
    Run(RunArgs),
    Render(RenderArgs),
    Bench(BenchArgs),
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
    #[arg(long, default_value = ".agentsight/agentflame/latest")]
    out: PathBuf,
}

#[derive(Parser, Clone)]
struct BenchArgs {
    #[arg(long, default_value = "llama-server")]
    llama_server: PathBuf,
    #[arg(long = "server-arg", allow_hyphen_values = true)]
    server_args: Vec<String>,
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
        let mut out = Vec::new();
        if self.input_tokens > 0 {
            out.push(("input", self.input_tokens));
        }
        if self.output_tokens > 0 {
            out.push(("output", self.output_tokens));
        }
        if self.cache_tokens > 0 {
            out.push(("cache", self.cache_tokens));
        }
        if self.estimated_tokens > 0 {
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
            "created_by": "agentflame-rust",
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
         Choose the most specific short action or topic word. Prefer common words such as debug, test, refactor, docs, trace, review, design, build, render, network, or research when they fit.\n\
         Do not concatenate multiple words into one string. Do not output fragments like codingupdate, testdebug, or flamegraphfix.\n\
         Do not use generic words like task, work, misc, thing, stuff, or other.\n\
         Examples:\n\
         Fragment: Fix failing Rust tests and inspect compiler errors.\n\
         Tag: debug\n\
         Fragment: Add a CLI option and update argument parsing.\n\
         Tag: cli\n\
         Fragment: Render semantic flamegraph charts for session history.\n\
         Tag: render\n\
         Fragment: Discuss paper novelty and evaluation design.\n\
         Tag: research\n\
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

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli
        .command
        .unwrap_or(CommandKind::Run(RunArgs::parse_from(["agentflame"])))
    {
        CommandKind::Run(args) => command_run(args),
        CommandKind::Render(args) => command_render(args),
        CommandKind::Bench(args) => command_bench(args),
    }
}

fn command_run(args: RunArgs) -> Result<()> {
    let project_root = args
        .project_root
        .canonicalize()
        .unwrap_or(args.project_root);
    let out_dir = args
        .out
        .unwrap_or_else(|| project_root.join(".agentsight/agentflame/latest"));
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
    let mut sessions = discover_sessions(
        &project_root,
        &codex_root,
        &claude_root,
        &args.session_files,
        args.scan_files,
        args.max_sessions,
    )?;
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
    )?;
    write_dashboard(&out_dir, &payload)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "status": "ok",
            "out": out_dir,
            "dashboard": out_dir.join("index.html"),
            "agentflame_json": out_dir.join("agentflame.json"),
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
    let payload_path = args.out.join("agentflame.json");
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

fn discover_sessions(
    project_root: &Path,
    codex_root: &Path,
    claude_root: &Path,
    session_files: &[PathBuf],
    scan_files: usize,
    max_sessions: usize,
) -> Result<Vec<SessionRecord>> {
    let explicit_files = !session_files.is_empty();
    let mut candidates = if explicit_files {
        session_files.to_vec()
    } else {
        let mut discovered = Vec::<PathBuf>::new();
        discovered.extend(find_jsonl(claude_root, scan_files));
        discovered.extend(find_jsonl(codex_root, scan_files));
        discovered.sort_by_key(|path| {
            std::cmp::Reverse(
                path.metadata()
                    .and_then(|m| m.modified())
                    .ok()
                    .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                    .map(|d| d.as_millis())
                    .unwrap_or(0),
            )
        });
        discovered
    };
    candidates.truncate(scan_files);
    let mut out = Vec::new();
    for path in candidates {
        let Some(source) = source_from_path(&path) else {
            continue;
        };
        if !explicit_files && source == "codex" && !raw_mentions_project(&path, project_root) {
            continue;
        }
        let normalized = parse_session(&path).ok();
        let mut session = if let Some(normalized) = normalized.as_ref() {
            convert_normalized_session(normalized, source, project_root)?
        } else if let Some(raw) = raw_session_minimal(&path, source, project_root, !explicit_files)?
        {
            raw
        } else {
            continue;
        };
        enrich_from_raw(&mut session, project_root)?;
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
    Ok(out)
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
    let text = path.to_string_lossy();
    if text.contains("/.codex/") {
        Some("codex")
    } else if text.contains("/.claude/") {
        Some("claude")
    } else if text.contains("/codex/") && text.contains("sessions") {
        Some("codex")
    } else if text.contains("/claude/") && text.contains("projects") {
        Some("claude")
    } else {
        None
    }
}

fn raw_mentions_project(path: &Path, project_root: &Path) -> bool {
    fs::read_to_string(path)
        .map(|text| text.contains(&project_root.to_string_lossy().to_string()))
        .unwrap_or(false)
}

fn convert_normalized_session(
    session: &NormalizedSession,
    source: &str,
    project_root: &Path,
) -> Result<SessionRecord> {
    let session_id = session
        .metadata
        .session_id
        .clone()
        .or_else(|| {
            session
                .path
                .file_stem()
                .and_then(|v| v.to_str())
                .map(str::to_string)
        })
        .unwrap_or_else(|| short_hash(&session.path.to_string_lossy(), 12));
    let mut record = SessionRecord {
        source: if session.is_subagent() {
            format!("{source}-subagent")
        } else {
            source.to_string()
        },
        path: session.path.clone(),
        session_id,
        cwd: session.metadata.project.clone().unwrap_or_default(),
        agent_role: session
            .subagent_type
            .clone()
            .unwrap_or_else(|| "agent".to_string()),
        model: session.metadata.model.clone().unwrap_or_default(),
        title: String::new(),
        start_ts_ms: session.metadata.timestamp.as_deref().and_then(parse_ts_ms),
        user_requests: Vec::new(),
        tools: Vec::new(),
        llm_calls: Vec::new(),
        session_tag: String::new(),
    };
    let mut tool_status = HashMap::<String, bool>::new();
    for turn in &session.turns {
        for message in &turn.messages {
            for block in &message.content {
                if let ContentBlock::ToolResult {
                    tool_use_id,
                    is_error,
                    ..
                } = block
                {
                    tool_status.insert(tool_use_id.clone(), *is_error);
                }
            }
        }
    }
    for (turn_idx, turn) in session.turns.iter().enumerate() {
        let user_text = turn
            .messages
            .iter()
            .find(|m| m.role == Role::User)
            .map(message_text)
            .unwrap_or_default();
        if !user_text.trim().is_empty() {
            record.user_requests.push(UserRequest {
                index: turn_idx,
                ts_ms: turn
                    .messages
                    .iter()
                    .find(|m| m.role == Role::User)
                    .and_then(|m| m.timestamp.as_deref())
                    .and_then(parse_ts_ms),
                text_hash: short_hash(&user_text, 12),
                preview: truncate_clean(&user_text, 180),
                tag: String::new(),
            });
        }
        for message in &turn.messages {
            if message.role == Role::Assistant {
                for block in &message.content {
                    if let ContentBlock::ToolUse { id, name, input } = block {
                        let mut event = tool_event_from_input(
                            project_root,
                            message.timestamp.as_deref().and_then(parse_ts_ms),
                            turn_idx,
                            name,
                            input,
                            Some(id.clone()),
                        );
                        if let Some(is_error) = tool_status.get(id) {
                            event.status = if *is_error { "fail" } else { "ok" }.to_string();
                        }
                        record.tools.push(event);
                    }
                }
            }
        }
        let assistant_text = turn
            .messages
            .iter()
            .filter(|m| m.role == Role::Assistant)
            .map(message_text)
            .collect::<Vec<_>>()
            .join(" ");
        if let Some(usage) = &turn.token_usage {
            if usage.input > 0 || usage.output > 0 || !assistant_text.trim().is_empty() {
                record.llm_calls.push(LlmEvent {
                    ts_ms: turn
                        .messages
                        .iter()
                        .find(|m| m.role == Role::Assistant)
                        .and_then(|m| m.timestamp.as_deref())
                        .and_then(parse_ts_ms),
                    request_index: turn_idx,
                    model: usage
                        .model
                        .clone()
                        .or_else(|| session.metadata.model.clone())
                        .unwrap_or_else(|| source.to_string()),
                    text_hash: short_hash(&assistant_text, 12),
                    preview: truncate_clean(
                        if assistant_text.trim().is_empty() {
                            "llm response"
                        } else {
                            &assistant_text
                        },
                        140,
                    ),
                    input_tokens: usage.input,
                    output_tokens: usage.output,
                    cache_tokens: usage.cache_read.unwrap_or(0) + usage.cache_create.unwrap_or(0),
                    estimated_tokens: 0,
                    tag: String::new(),
                });
            }
        }
    }
    Ok(record)
}

fn raw_session_minimal(
    path: &Path,
    source: &str,
    project_root: &Path,
    enforce_project_filter: bool,
) -> Result<Option<SessionRecord>> {
    if enforce_project_filter && source == "codex" && !raw_mentions_project(path, project_root) {
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
        "warnings": [],
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
        config.out_dir.join("agentflame.json"),
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
        "<!doctype html><html><head><meta charset='utf-8'><title>AgentFlame Report</title>\
         <style>body{{font-family:system-ui;margin:0;background:#f7f7f2;color:#17202a}}header{{padding:24px;background:#17202a;color:white}}main{{padding:24px}}.panel{{background:white;border:1px solid #ddd8ca;border-radius:8px;padding:12px;margin:12px 0;overflow:auto}}img{{max-width:none}}</style></head>\
         <body><header><h1>AgentFlame Report</h1><div>Generated {}</div></header><main>\
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
        .unwrap_or_else(|| PathBuf::from(".agentsight/agentflame/benchmarks.json"));
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent)?;
    }
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
                    std::env::temp_dir().join(format!("agentflame-bench-{port}.tags.json")),
                    base_url.clone(),
                    "local".to_string(),
                    Duration::from_secs(args.request_timeout),
                    -1,
                );
                let mut run_rows = Vec::new();
                for run_idx in 0..args.runs {
                    let prompt = format!(
                        "Benchmark run {run_idx}. Label this coding-agent fragment: Fix failing Rust tests and update semantic flamegraph stacks."
                    );
                    let req_started = Instant::now();
                    let result = tagger.tag_uncached("prompt", &prompt);
                    let latency_ms = req_started.elapsed().as_millis() as u64;
                    run_rows.push(match result {
                        Ok(tag) => json!({
                            "run": run_idx,
                            "latency_ms": latency_ms,
                            "ok": true,
                            "tag": tag,
                        }),
                        Err(error) => json!({
                            "run": run_idx,
                            "latency_ms": latency_ms,
                            "ok": false,
                            "error": error.to_string(),
                        }),
                    });
                }
                model_result["runs"] = Value::Array(run_rows);
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
        "models": results,
    });
    fs::write(&out, serde_json::to_vec_pretty(&payload)?)?;
    println!("{}", serde_json::to_string_pretty(&payload)?);
    Ok(())
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
    } else if ["collector", "frontend", "docs", "bpf", "agentflame"].contains(&parts[0].as_str()) {
        parts.into_iter().take(3).collect::<Vec<_>>().join("/")
    } else {
        parts.into_iter().take(2).collect::<Vec<_>>().join("/")
    }
}

fn message_text(message: &normalize_chat_sessions::Message) -> String {
    message
        .content
        .iter()
        .map(|block| match block {
            ContentBlock::Text { text } | ContentBlock::Thinking { text } => text.clone(),
            ContentBlock::ToolUse { name, .. } => format!("tool {name}"),
            ContentBlock::ToolResult { .. } => String::new(),
        })
        .filter(|text| !text.trim().is_empty())
        .collect::<Vec<_>>()
        .join("\n")
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
    let format = ClaudeCodeFormat;
    Ok(format.sessions_dir(Some(project_root)))
}

#[allow(dead_code)]
fn _codex_root_from_crate() -> PathBuf {
    let format = CodexFormat;
    format.sessions_dir(None)
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
    fn model_specs_accept_explicit_labels_or_path_stems() {
        let (label, path) = parse_model_spec("0.6b=/models/qwen.gguf").unwrap();
        assert_eq!(label, "0.6b");
        assert_eq!(path, PathBuf::from("/models/qwen.gguf"));

        let (label, path) = parse_model_spec("/models/localmodel.gguf").unwrap();
        assert_eq!(label, "localmodel");
        assert_eq!(path, PathBuf::from("/models/localmodel.gguf"));
    }
}
