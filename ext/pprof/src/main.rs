mod profile;
mod session;
mod tagger;

use anyhow::{Result, bail};
use clap::{Parser, ValueEnum};
use serde_json::json;
use std::collections::HashMap;
use std::path::PathBuf;
use std::time::Duration;

use profile::{
    OperationStackConfig, OutputFormat, ProfileView, build_profile_with_options,
    infer_output_format, parse_operation_filters, parse_stack_rules, parse_stack_rules_with_flag,
    parse_stack_spec, profile_to_stacks, write_projection,
};
use session::{SessionRecord, default_claude_root, discover_sessions};
use tagger::{
    LlamaTagger, RegexTagger, TagDiagnostics, annotate_sessions, annotate_sessions_regex,
    annotate_sessions_with_declared_tasks, default_tag_cache_path, parse_declared_tag_choices,
};

const DEFAULT_LLAMA_URL: &str = "http://127.0.0.1:8080";

const TAGGING_HELP: &str = r#"
TAGGING WORKFLOW:
  Flamegraphs require semantic tags to aggregate meaningfully. Without --tag-rule,
  prompts are marked 'unmatched' and won't aggregate well.

  1. Run with no rules to see diagnostics:
     agentpprof --project-root . -o out.json --format json --include-previews

  2. Examine unmatched prompts in the JSON output, identify patterns

  3. Add --tag-rule arguments for your project:
     agentpprof --project-root . -o out.svg \
       --tag-rule prompt:review='(?i)review|diff|pr' \
       --tag-rule prompt:debug='(?i)fix|bug|error' \
       --tag-rule prompt:test='(?i)test|cargo test'

  4. Iterate until coverage is acceptable (diagnostics show matched/unmatched counts)

  --preset enables built-in keyword rules (profile, debug, test, etc.) for quick
  testing, but these are generic and unlikely to match your project's prompts well.

OPERATION STACK:
  Samples are field bags. --op-map derives/overwrites fields, --where filters them,
  and --stack chooses how those fields become flamegraph frames.

  Defaults: task,skill,phase,action,object,repeat,result,outcome[,token]

  Examples:
     agentpprof --project-root . -o out.pb.gz \
       --op-map task:verify='(?i)cmd=cargo' \
       --where 'task=verify' \
       --stack task,action,result
"#;

#[derive(Parser)]
#[command(name = "agentpprof")]
#[command(version)]
#[command(about = "pprof-compatible operation-stack profiler for local AI coding-agent sessions")]
#[command(after_help = TAGGING_HELP)]
struct Cli {
    /// Output file. Use .pb.gz for Go pprof, .folded for folded stacks, .svg for an SVG flamegraph, or .json.
    #[arg(short, long)]
    output: PathBuf,
    #[arg(long, default_value = ".")]
    project_root: PathBuf,
    #[arg(long)]
    project_name: Option<String>,
    #[arg(long, value_enum, default_value_t = CliOutputFormat::Pprof)]
    format: CliOutputFormat,
    #[arg(long, value_enum, default_value_t = CliProfileView::Tokens)]
    view: CliProfileView,
    /// Override the operation stack, e.g. task,skill,phase,action,object,repeat,result,outcome.
    #[arg(long, value_name = "FRAME[,FRAME...]")]
    stack: Option<String>,
    /// Add a deterministic operation-stack rule, e.g. task:verify='(?i)effect=test|cmd=cargo'.
    /// Rules are evaluated in order for each stack frame; first match wins.
    #[arg(long = "stack-rule", value_name = "FRAME:LABEL=REGEX")]
    stack_rules: Vec<String>,
    /// Derive or overwrite an operation field before stacking, e.g. task:verify='(?i)cmd=cargo'.
    /// Rules are evaluated in order against updated fields; first match wins for each field.
    #[arg(long = "op-map", value_name = "FIELD:LABEL=REGEX")]
    op_maps: Vec<String>,
    /// Select operations after --op-map field derivation and before stacking, e.g. task=verify.
    /// Multiple predicates are ANDed. Use FIELD!=REGEX to exclude matching operations.
    #[arg(long = "where", value_name = "FIELD=REGEX")]
    where_rules: Vec<String>,
    /// Read operation-field mapping rules from a file. Blank lines and lines starting with '#' are ignored.
    /// Inline --op-map rules run before file rules, so command-line rules can override defaults.
    #[arg(long = "op-map-file", value_name = "PATH")]
    op_map_files: Vec<PathBuf>,
    #[arg(long, value_enum, default_value_t = TaggerKind::Regex)]
    tagger: TaggerKind,
    /// Add a deterministic tag rule, for example prompt:review='(?i)review|diff'.
    /// Rules are evaluated in order; first match wins.
    #[arg(long = "tag-rule", value_name = "KIND:TAG=REGEX")]
    tag_rules: Vec<String>,
    /// Add one category to an optional LLM-assigned task taxonomy while preserving the raw tag.
    #[arg(long = "task-choice", value_name = "TAG=DESCRIPTION")]
    task_choices: Vec<String>,
    /// Enable built-in keyword rules (profile, debug, test, review, etc.).
    /// These are generic and may not match your project well. For testing only.
    #[arg(long)]
    preset: bool,
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
    /// Maximum session files to scan per source (Claude, Codex). Default: unlimited (0 = no limit).
    #[arg(long, default_value_t = 0)]
    scan_files: usize,
    /// Maximum sessions to include after filtering by project. Default: unlimited (0 = no limit).
    #[arg(long, default_value_t = 0)]
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
    /// SVG width in pixels (default: 1200, narrower for better readability)
    #[arg(long, default_value_t = 1200)]
    svg_width: u32,
}

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
enum CliOutputFormat {
    Pprof,
    Folded,
    Svg,
    Json,
}

impl From<CliOutputFormat> for OutputFormat {
    fn from(val: CliOutputFormat) -> Self {
        match val {
            CliOutputFormat::Pprof => OutputFormat::Pprof,
            CliOutputFormat::Folded => OutputFormat::Folded,
            CliOutputFormat::Svg => OutputFormat::Svg,
            CliOutputFormat::Json => OutputFormat::Json,
        }
    }
}

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
enum CliProfileView {
    Operations,
    Tokens,
    Files,
    Network,
    Time,
}

impl From<CliProfileView> for ProfileView {
    fn from(val: CliProfileView) -> Self {
        match val {
            CliProfileView::Operations => ProfileView::Operations,
            CliProfileView::Tokens => ProfileView::Tokens,
            CliProfileView::Files => ProfileView::Files,
            CliProfileView::Network => ProfileView::Network,
            CliProfileView::Time => ProfileView::Time,
        }
    }
}

#[derive(Clone, Copy, Debug, ValueEnum)]
enum TaggerKind {
    Regex,
    Llm,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    command_export(cli)
}

fn command_export(args: Cli) -> Result<()> {
    let output = args.output.clone();
    let format = infer_output_format(args.format.into(), &output);
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
    let diagnostics = annotate_sessions_with(&mut sessions, &args)?;
    filter_sessions_after_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!("sessions were found, but none matched the requested tag filters");
    }
    let view = args.view.into();
    let mut profile_options = OperationStackConfig::for_view(view);
    if let Some(stack) = args.stack.as_deref() {
        profile_options = profile_options.with_stack(parse_stack_spec(stack)?);
    }
    let op_maps = load_op_map_rules(&args.op_maps, &args.op_map_files)?;
    profile_options = profile_options
        .with_field_rules(parse_stack_rules_with_flag(&op_maps, "--op-map")?)
        .with_filters(parse_operation_filters(&args.where_rules)?)
        .with_rules(parse_stack_rules(&args.stack_rules)?);
    let profile = build_profile_with_options(&sessions, &project_name, view, &profile_options)?;
    let stacks = profile_to_stacks(&profile);
    if stacks.is_empty() {
        bail!("selected view {:?} produced no samples", args.view);
    }
    write_projection(
        &profile,
        format,
        &output,
        args.include_previews,
        &sessions,
        args.svg_width,
    )?;

    let mut result = json!({
        "status": "ok",
        "output": output,
        "format": format!("{:?}", format).to_ascii_lowercase(),
        "view": profile.view,
        "sample_type": profile.sample_type,
        "unit": profile.unit,
        "sessions": sessions.len(),
        "samples": stacks.values().sum::<u64>(),
        "unique_stacks": stacks.len(),
        "warnings": discovery.warnings,
    });

    if let Some(diag) = diagnostics {
        let total = diag.total_sessions + diag.total_prompts + diag.total_llm_calls;
        let matched = diag.matched_sessions + diag.matched_prompts + diag.matched_llm_calls;
        result["tagging"] = json!({
            "sessions": {
                "total": diag.total_sessions,
                "matched": diag.matched_sessions,
                "unmatched": diag.unmatched_sessions,
            },
            "prompts": {
                "total": diag.total_prompts,
                "matched": diag.matched_prompts,
                "unmatched": diag.unmatched_prompts,
            },
            "llm_calls": {
                "total": diag.total_llm_calls,
                "matched": diag.matched_llm_calls,
                "unmatched": diag.unmatched_llm_calls,
            },
            "coverage_pct": if total > 0 {
                (matched as f64 / total as f64 * 100.0).round()
            } else {
                0.0
            },
            "tag_counts": diag.tag_counts,
        });
        if !diag.unmatched_samples.is_empty() {
            result["tagging"]["unmatched_samples"] = json!(
                diag.unmatched_samples
                    .iter()
                    .map(|s| json!({
                        "kind": s.kind,
                        "preview": s.preview,
                        "session_id": s.session_id,
                    }))
                    .collect::<Vec<_>>()
            );
            result["tagging"]["hint"] = json!(
                "Add --tag-rule arguments to match unmatched items. Example: --tag-rule session:research='(?i)research|paper' or --tag-rule prompt:debug='(?i)fix|bug|error'"
            );
        }
    }

    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

fn load_op_map_rules(inline_rules: &[String], rule_files: &[PathBuf]) -> Result<Vec<String>> {
    let mut rules = inline_rules.to_vec();
    for path in rule_files {
        let contents = std::fs::read_to_string(path).map_err(|error| {
            anyhow::anyhow!("failed to read --op-map-file {}: {error}", path.display())
        })?;
        for line in contents.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            rules.push(line.to_string());
        }
    }
    Ok(rules)
}

fn filter_sessions_before_tagging(sessions: &mut Vec<SessionRecord>, args: &Cli) {
    if let Some(agent) = args.agent.as_deref() {
        sessions.retain(|session| session.source.starts_with(agent));
    }
    if let Some(session_id) = args.session_id.as_deref() {
        sessions.retain(|session| session.session_id.contains(session_id));
    }
}

fn filter_sessions_after_tagging(sessions: &mut Vec<SessionRecord>, args: &Cli) {
    if let Some(tag) = args.session_tag.as_deref() {
        sessions.retain(|session| session.session_tag == tag);
    }
    if let Some(tag) = args.prompt_tag.as_deref() {
        for session in sessions.iter_mut() {
            filter_session_by_prompt_tag(session, tag);
        }
        sessions.retain(|session| {
            !session.user_requests.is_empty()
                || !session.tools.is_empty()
                || !session.llm_calls.is_empty()
        });
    }
}

fn filter_session_by_prompt_tag(session: &mut SessionRecord, tag: &str) {
    let selected = session
        .user_requests
        .iter()
        .cloned()
        .enumerate()
        .filter(|(_, req)| req.tag == tag)
        .collect::<Vec<_>>();
    if selected.is_empty() {
        session.user_requests.clear();
        session.tools.clear();
        session.llm_calls.clear();
        return;
    }

    let row_map = selected
        .iter()
        .enumerate()
        .map(|(new_ordinal, (old_ordinal, _))| (*old_ordinal, new_ordinal))
        .collect::<HashMap<_, _>>();

    session.tools = std::mem::take(&mut session.tools)
        .into_iter()
        .filter_map(|mut event| {
            let new_ordinal = row_map.get(&event.prompt_index).copied()?;
            event.prompt_index = new_ordinal;
            Some(event)
        })
        .collect();
    session.llm_calls = std::mem::take(&mut session.llm_calls)
        .into_iter()
        .filter_map(|mut call| {
            let new_ordinal = row_map.get(&call.prompt_index).copied()?;
            call.prompt_index = new_ordinal;
            Some(call)
        })
        .collect();
    session.user_requests = selected.into_iter().map(|(_, req)| req).collect();
}

fn annotate_sessions_with(
    sessions: &mut [SessionRecord],
    args: &Cli,
) -> Result<Option<TagDiagnostics>> {
    match args.tagger {
        TaggerKind::Regex => {
            if !args.task_choices.is_empty() {
                bail!("--task-choice requires --tagger llm");
            }
            let tagger = RegexTagger::new(&args.tag_rules, args.preset)?;
            let diagnostics = annotate_sessions_regex(sessions, &tagger);
            Ok(Some(diagnostics))
        }
        TaggerKind::Llm => {
            if !args.tag_rules.is_empty() {
                bail!("--tag-rule is only supported with --tagger regex");
            }
            let cache_path = args.cache.clone().unwrap_or_else(default_tag_cache_path);
            let mut tagger = LlamaTagger::new(
                cache_path,
                args.llama_url.clone(),
                args.model.clone(),
                Duration::from_secs(args.timeout),
                args.max_uncached_tags,
            );
            let task_choices = parse_declared_tag_choices(&args.task_choices)?;
            if task_choices.is_empty() {
                annotate_sessions(sessions, &mut tagger)?;
            } else {
                annotate_sessions_with_declared_tasks(sessions, &mut tagger, &task_choices)?;
            }
            if !args.no_cache {
                tagger.save()?;
            }
            Ok(None)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::session::{LlmEvent, ToolEvent, UserRequest};
    use std::path::PathBuf;

    #[test]
    fn prompt_tag_filter_uses_prompt_row_ordinal_not_bare_index() {
        let mut session = SessionRecord {
            source: "claude".to_string(),
            path: PathBuf::from("session.jsonl"),
            session_id: "s1".to_string(),
            cwd: "/repo".to_string(),
            agent_role: "agent".to_string(),
            model: "claude".to_string(),
            title: "duplicate indexes".to_string(),
            start_ts_ms: Some(1),
            user_requests: vec![
                UserRequest {
                    index: 0,
                    ts_ms: Some(1),
                    text: "review prompt".to_string(),
                    text_hash: "h0".to_string(),
                    preview: "review prompt".to_string(),
                    tag: "review".to_string(),
                    task_path: Vec::new(),
                },
                UserRequest {
                    index: 0,
                    ts_ms: Some(2),
                    text: "test prompt".to_string(),
                    text_hash: "h1".to_string(),
                    preview: "test prompt".to_string(),
                    tag: "test".to_string(),
                    task_path: Vec::new(),
                },
            ],
            tools: vec![
                ToolEvent {
                    ts_ms: Some(3),
                    prompt_index: 0,
                    tool_name: "Read".to_string(),
                    category: "read".to_string(),
                    command: String::new(),
                    command_name: String::new(),
                    effect: "read".to_string(),
                    process_chain: Vec::new(),
                    status: "ok".to_string(),
                    path_groups: Vec::new(),
                    paths: Vec::new(),
                    domains: Vec::new(),
                    call_id: None,
                    invoked_skill: String::new(),
                    skill: String::new(),
                    task_path: Vec::new(),
                },
                ToolEvent {
                    ts_ms: Some(4),
                    prompt_index: 1,
                    tool_name: "Bash".to_string(),
                    category: "shell".to_string(),
                    command: "cargo test".to_string(),
                    command_name: "cargo".to_string(),
                    effect: "test".to_string(),
                    process_chain: vec!["cargo".to_string()],
                    status: "ok".to_string(),
                    path_groups: Vec::new(),
                    paths: Vec::new(),
                    domains: Vec::new(),
                    call_id: None,
                    invoked_skill: String::new(),
                    skill: String::new(),
                    task_path: Vec::new(),
                },
            ],
            llm_calls: vec![
                LlmEvent {
                    ts_ms: Some(5),
                    prompt_index: 0,
                    model: "claude".to_string(),
                    source_id: String::new(),
                    text: "review answer".to_string(),
                    text_hash: "l0".to_string(),
                    preview: "review answer".to_string(),
                    input_tokens: 1,
                    output_tokens: 1,
                    cache_tokens: 0,
                    total_tokens: 0,
                    tag: "answer".to_string(),
                    response_phase: String::new(),
                    skill: String::new(),
                    task_path: Vec::new(),
                },
                LlmEvent {
                    ts_ms: Some(6),
                    prompt_index: 1,
                    model: "claude".to_string(),
                    source_id: String::new(),
                    text: "test answer".to_string(),
                    text_hash: "l1".to_string(),
                    preview: "test answer".to_string(),
                    input_tokens: 2,
                    output_tokens: 3,
                    cache_tokens: 0,
                    total_tokens: 0,
                    tag: "answer".to_string(),
                    response_phase: String::new(),
                    skill: String::new(),
                    task_path: Vec::new(),
                },
            ],
            session_tag: "review".to_string(),
            task_tag: String::new(),
        };

        filter_session_by_prompt_tag(&mut session, "test");

        assert_eq!(session.user_requests.len(), 1);
        assert_eq!(session.user_requests[0].text_hash, "h1");
        assert_eq!(session.user_requests[0].index, 0);
        assert_eq!(session.tools.len(), 1);
        assert_eq!(session.tools[0].prompt_index, 0);
        assert_eq!(session.tools[0].effect, "test");
        assert_eq!(session.llm_calls.len(), 1);
        assert_eq!(session.llm_calls[0].prompt_index, 0);
        assert_eq!(session.llm_calls[0].text_hash, "l1");

        let payload = profile::session_to_json(&session, false);
        let tool = &payload["tool_events"].as_array().expect("tool events")[0];
        assert_eq!(tool["prompt_key"], "0:h1");
        assert_eq!(tool["prompt_tag"], "test");
    }
}
