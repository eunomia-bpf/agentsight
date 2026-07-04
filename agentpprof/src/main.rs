mod profile;
mod session;
mod standard_trace;
mod tagger;

use anyhow::{Context, Result, bail};
use clap::{Parser, ValueEnum};
use serde::Deserialize;
use serde_json::json;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::Duration;

use profile::{
    OperationStackConfig, OutputFormat, ProfileView, build_profile_from_operation_files,
    build_profile_from_operation_records, build_profile_with_options, infer_output_format,
    parse_operation_filters, parse_stack_rules, parse_stack_rules_with_flag, parse_stack_spec,
    profile_to_stacks, write_projection,
};
use session::{
    SessionRecord, default_claude_root, discover_agent_sessions, load_agent_trace_files,
    session_records_from_agent_sessions, write_agent_trace,
};
use tagger::{
    LlamaTagger, RegexTagger, TagDiagnostics, annotate_sessions, annotate_sessions_regex,
    default_tag_cache_path,
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

OPERATION STACK WORKFLOW:
  --view chooses which operation samples are measured. --stack chooses how those
  operations fold into a stack. Use --op-map to derive reusable operation
  fields, --where to select an operation subset, then --stack chooses how those
  fields recursively fold. Use
  --op-map-file to load reusable mappings, and --stack-rule for one-off
  stack-frame overrides.

     agentpprof --view files -o files.folded \
       --stack 'project,agent,task,phase,op,tool,path,status' \
       --op-map-file operation-map.txt \
       --op-map 'task:verify=(effect=test|cmd=cargo)' \
       --op-map 'phase:inspect=(effect=read)' \
       --where 'task=verify'

  For repeatable external-trace experiments, put output, view, operation files,
  op-map files, and stack in a JSON file and run:

     agentpprof --profile-spec agentnet-diagnostic-spec.json
"#;

#[derive(Parser)]
#[command(name = "agentpprof")]
#[command(version)]
#[command(about = "pprof-compatible semantic profiler for local AI coding-agent sessions")]
#[command(after_help = TAGGING_HELP)]
struct Cli {
    /// Output file. Use .pb.gz for Go pprof, .folded for folded stacks, .svg for an SVG flamegraph, or .json.
    /// Required unless --profile-spec provides output.
    #[arg(short, long)]
    output: Option<PathBuf>,
    #[arg(long, default_value = ".")]
    project_root: PathBuf,
    #[arg(long)]
    project_name: Option<String>,
    #[arg(long, value_enum)]
    format: Option<CliOutputFormat>,
    #[arg(long, value_enum)]
    view: Option<CliProfileView>,
    /// Load a reusable JSON profile specification. Later specs override scalar
    /// fields, while list fields are appended. CLI flags override spec defaults.
    #[arg(long = "profile-spec", value_name = "PATH")]
    profile_specs: Vec<PathBuf>,
    /// Override the operation stack, e.g. project,agent,task,phase,op,tool,path.
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
    /// Read portable agent-session trace JSON instead of local Codex/Claude discovery.
    #[arg(long = "trace-file", value_name = "PATH")]
    trace_files: Vec<PathBuf>,
    /// Read Chrome/Perfetto Trace Event JSON as imported operations.
    #[arg(long = "standard-trace-file", value_name = "PATH")]
    standard_trace_files: Vec<PathBuf>,
    /// Export matched local sessions as portable agent-session trace JSON.
    /// If no -o/--output is provided, export the trace and exit.
    #[arg(long = "export-trace", value_name = "PATH")]
    export_trace: Option<PathBuf>,
    /// Export matched local sessions as Chrome/Perfetto Trace Event JSON.
    /// If no -o/--output is provided, export the trace and exit.
    #[arg(long = "export-standard-trace", value_name = "PATH")]
    export_standard_trace: Option<PathBuf>,
    /// Read already-normalized operation JSONL instead of local Codex/Claude sessions.
    #[arg(long = "operation-file")]
    operation_files: Vec<PathBuf>,
    /// Copy non-AgentSight Chrome trace args into imported operation fields.
    #[arg(long = "include-standard-trace-args")]
    include_standard_trace_args: bool,
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

#[derive(Default, Debug)]
struct ProfileSpec {
    output: Option<PathBuf>,
    project_name: Option<String>,
    format: Option<CliOutputFormat>,
    view: Option<CliProfileView>,
    stack: Option<String>,
    stack_rules: Vec<String>,
    op_maps: Vec<String>,
    where_rules: Vec<String>,
    op_map_files: Vec<PathBuf>,
    operation_files: Vec<PathBuf>,
}

#[derive(Default, Deserialize)]
struct RawProfileSpec {
    output: Option<PathBuf>,
    project_name: Option<String>,
    format: Option<String>,
    view: Option<String>,
    stack: Option<String>,
    #[serde(default)]
    stack_rules: Vec<String>,
    #[serde(default)]
    op_maps: Vec<String>,
    #[serde(default)]
    where_rules: Vec<String>,
    #[serde(default)]
    op_map_files: Vec<PathBuf>,
    #[serde(default)]
    operation_files: Vec<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    command_export(cli)
}

fn command_export(args: Cli) -> Result<()> {
    let spec = load_profile_specs(&args.profile_specs)?;
    let output = args.output.clone().or_else(|| spec.output.clone());
    if output.is_none() && args.export_trace.is_none() && args.export_standard_trace.is_none() {
        bail!(
            "missing output path; pass -o/--output, set output in --profile-spec, --export-trace, or --export-standard-trace"
        );
    }
    let requested_format = args
        .format
        .or(spec.format)
        .unwrap_or(CliOutputFormat::Pprof);
    let project_root = args
        .project_root
        .canonicalize()
        .unwrap_or(args.project_root.clone());
    let project_name = args
        .project_name
        .clone()
        .or_else(|| spec.project_name.clone())
        .unwrap_or_else(|| {
            project_root
                .file_name()
                .and_then(|v| v.to_str())
                .unwrap_or("project")
                .to_string()
        });
    let cli_view = args.view.or(spec.view).unwrap_or(CliProfileView::Tokens);
    let view = cli_view.into();
    let mut profile_options = OperationStackConfig::for_view(view);
    let stack = args.stack.as_deref().or(spec.stack.as_deref());
    if let Some(stack) = stack {
        profile_options = profile_options.with_stack(parse_stack_spec(stack)?);
    }
    let op_map_files = merge_cli_first(&args.op_map_files, &spec.op_map_files);
    let op_maps = load_effective_op_map_rules(
        &args.op_maps,
        &args.op_map_files,
        &spec.op_maps,
        &spec.op_map_files,
    )?;
    let stack_rules = merge_cli_first(&args.stack_rules, &spec.stack_rules);
    let where_rules = effective_where_rules(&args.where_rules, &spec.where_rules);
    profile_options = profile_options
        .with_field_rules(parse_stack_rules_with_flag(&op_maps, "--op-map")?)
        .with_filters(parse_operation_filters(&where_rules)?)
        .with_rules(parse_stack_rules(&stack_rules)?);
    let operation_files = merge_spec_first(&spec.operation_files, &args.operation_files);
    validate_input_modes(&args, &operation_files)?;
    if !args.standard_trace_files.is_empty() {
        let output = output
            .as_ref()
            .context("missing output path; pass -o/--output or set output in --profile-spec")?;
        let format = infer_output_format(requested_format.into(), output);
        let operation_records = standard_trace::operation_records_from_chrome_trace_files(
            &args.standard_trace_files,
            &project_name,
            args.include_standard_trace_args,
        )?;
        let profile =
            build_profile_from_operation_records(&operation_records, view, &profile_options)?;
        let stacks = profile_to_stacks(&profile);
        if stacks.is_empty() {
            bail!("standard trace input produced no folded stacks");
        }
        write_projection(
            &profile,
            format,
            output,
            args.include_previews,
            &[],
            args.svg_width,
        )?;
        let result = json!({
            "status": "ok",
            "output": output,
            "format": format!("{:?}", format).to_ascii_lowercase(),
            "view": profile.view,
            "sample_type": profile.sample_type,
            "unit": profile.unit,
            "profile_specs": args.profile_specs,
            "stack": stack.unwrap_or("default"),
            "op_maps": op_maps,
            "op_map_files": op_map_files,
            "where_rules": where_rules,
            "stack_rules": stack_rules,
            "standard_trace_files": args.standard_trace_files,
            "standard_trace_format": standard_trace::CHROME_TRACE_FORMAT,
            "operations": operation_records.len(),
            "samples": stacks.values().sum::<u64>(),
            "unique_stacks": stacks.len(),
            "warnings": [],
        });
        println!("{}", serde_json::to_string_pretty(&result)?);
        return Ok(());
    }
    if !operation_files.is_empty() {
        let output = output
            .as_ref()
            .context("missing output path; pass -o/--output or set output in --profile-spec")?;
        let format = infer_output_format(requested_format.into(), output);
        let profile = build_profile_from_operation_files(&operation_files, view, &profile_options)?;
        let stacks = profile_to_stacks(&profile);
        if stacks.is_empty() {
            bail!("operation input produced no folded stacks");
        }
        write_projection(
            &profile,
            format,
            &output,
            args.include_previews,
            &[],
            args.svg_width,
        )?;
        let result = json!({
            "status": "ok",
            "output": output,
            "format": format!("{:?}", format).to_ascii_lowercase(),
            "view": profile.view,
            "sample_type": profile.sample_type,
            "unit": profile.unit,
            "profile_specs": args.profile_specs,
            "stack": stack.unwrap_or("default"),
            "op_maps": op_maps,
            "op_map_files": op_map_files,
            "where_rules": where_rules,
            "stack_rules": stack_rules,
            "operation_files": operation_files,
            "samples": stacks.values().sum::<u64>(),
            "unique_stacks": stacks.len(),
            "warnings": [],
        });
        println!("{}", serde_json::to_string_pretty(&result)?);
        return Ok(());
    }
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
    let mut agent_sessions = if !args.trace_files.is_empty() {
        load_agent_trace_files(&args.trace_files)?
    } else {
        discover_agent_sessions(
            &project_root,
            &codex_root,
            &claude_root,
            &args.session_files,
            args.scan_files,
            args.max_sessions,
        )?
    };
    filter_agent_sessions_before_export(&mut agent_sessions, &args);
    if agent_sessions.is_empty() {
        bail!(
            "no local Codex/Claude sessions or imported traces matched {}",
            project_root.display()
        );
    }
    if let Some(trace_path) = args.export_trace.as_ref() {
        write_agent_trace(trace_path, &agent_sessions)?;
    }
    let standard_trace_events = if let Some(trace_path) = args.export_standard_trace.as_ref() {
        let export_sessions = session_records_from_agent_sessions(&agent_sessions);
        Some(standard_trace::write_chrome_trace(
            trace_path,
            &export_sessions,
            &project_name,
            args.include_previews,
        )?)
    } else {
        None
    };
    if output.is_none() {
        let result = json!({
            "status": "ok",
            "trace_output": args.export_trace,
            "trace_schema": if args.export_trace.is_some() {
                Some(agent_session::AGENT_TRACE_SCHEMA)
            } else {
                None
            },
            "standard_trace_output": args.export_standard_trace,
            "standard_trace_format": if args.export_standard_trace.is_some() {
                Some(standard_trace::CHROME_TRACE_FORMAT)
            } else {
                None
            },
            "standard_trace_events": standard_trace_events,
            "sessions": agent_sessions.len(),
            "trace_files": args.trace_files,
            "warnings": [],
        });
        println!("{}", serde_json::to_string_pretty(&result)?);
        return Ok(());
    }
    let mut sessions = session_records_from_agent_sessions(&agent_sessions);
    filter_sessions_before_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!(
            "no local Codex/Claude sessions or imported traces matched {}",
            project_root.display()
        );
    }
    let diagnostics = annotate_sessions_with(&mut sessions, &args)?;
    filter_sessions_after_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!("sessions were found, but none matched the requested tag filters");
    }
    let output = output
        .as_ref()
        .context("missing output path; pass -o/--output or set output in --profile-spec")?;
    let format = infer_output_format(requested_format.into(), output);
    let profile = build_profile_with_options(&sessions, &project_name, view, &profile_options);
    let stacks = profile_to_stacks(&profile);
    if stacks.is_empty() {
        bail!("selected view {:?} produced no samples", cli_view);
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
        "profile_specs": args.profile_specs,
        "trace_files": args.trace_files,
        "trace_output": args.export_trace,
        "standard_trace_output": args.export_standard_trace,
        "standard_trace_format": if args.export_standard_trace.is_some() {
            Some(standard_trace::CHROME_TRACE_FORMAT)
        } else {
            None
        },
        "standard_trace_events": standard_trace_events,
        "stack": stack.unwrap_or("default"),
        "op_maps": op_maps,
        "op_map_files": op_map_files,
        "where_rules": where_rules,
        "stack_rules": stack_rules,
        "sessions": sessions.len(),
        "samples": stacks.values().sum::<u64>(),
        "unique_stacks": stacks.len(),
        "warnings": [],
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

fn merge_cli_first<T: Clone>(cli_values: &[T], spec_values: &[T]) -> Vec<T> {
    cli_values
        .iter()
        .chain(spec_values.iter())
        .cloned()
        .collect()
}

fn merge_spec_first<T: Clone>(spec_values: &[T], cli_values: &[T]) -> Vec<T> {
    spec_values
        .iter()
        .chain(cli_values.iter())
        .cloned()
        .collect()
}

fn effective_where_rules(cli_values: &[String], spec_values: &[String]) -> Vec<String> {
    if cli_values.is_empty() {
        spec_values.to_vec()
    } else {
        cli_values.to_vec()
    }
}

fn load_effective_op_map_rules(
    cli_inline_rules: &[String],
    cli_rule_files: &[PathBuf],
    spec_inline_rules: &[String],
    spec_rule_files: &[PathBuf],
) -> Result<Vec<String>> {
    let mut rules = load_op_map_rules(cli_inline_rules, cli_rule_files)?;
    rules.extend(load_op_map_rules(spec_inline_rules, spec_rule_files)?);
    Ok(rules)
}

fn validate_input_modes(args: &Cli, operation_files: &[PathBuf]) -> Result<()> {
    if !operation_files.is_empty() && !args.trace_files.is_empty() {
        bail!("--trace-file cannot be used with --operation-file");
    }
    if !args.standard_trace_files.is_empty() {
        if !operation_files.is_empty() {
            bail!("--standard-trace-file cannot be used with --operation-file");
        }
        if !args.trace_files.is_empty() {
            bail!("--standard-trace-file cannot be used with --trace-file");
        }
        if args.export_trace.is_some() || args.export_standard_trace.is_some() {
            bail!(
                "--standard-trace-file cannot be used with --export-trace or --export-standard-trace"
            );
        }
    }
    if args.export_trace.is_some() || args.export_standard_trace.is_some() {
        if !operation_files.is_empty() {
            bail!("trace export cannot be used with --operation-file");
        }
        if args.session_tag.is_some() || args.prompt_tag.is_some() {
            bail!("trace export cannot be combined with --session-tag or --prompt-tag");
        }
    }
    Ok(())
}

fn load_profile_specs(paths: &[PathBuf]) -> Result<ProfileSpec> {
    let mut merged = ProfileSpec::default();
    for path in paths {
        let contents = fs::read_to_string(path)
            .with_context(|| format!("failed to read --profile-spec {}", path.display()))?;
        let raw: RawProfileSpec = serde_json::from_str(&contents)
            .with_context(|| format!("invalid --profile-spec {}", path.display()))?;
        let base = path.parent().unwrap_or_else(|| Path::new("."));
        let next = normalize_profile_spec(raw, base)
            .with_context(|| format!("invalid --profile-spec {}", path.display()))?;
        merged.merge(next);
    }
    Ok(merged)
}

fn normalize_profile_spec(raw: RawProfileSpec, base: &Path) -> Result<ProfileSpec> {
    Ok(ProfileSpec {
        output: raw.output.map(|path| resolve_spec_path(base, path)),
        project_name: raw.project_name,
        format: raw
            .format
            .as_deref()
            .map(parse_spec_output_format)
            .transpose()?,
        view: raw.view.as_deref().map(parse_spec_view).transpose()?,
        stack: raw.stack,
        stack_rules: raw.stack_rules,
        op_maps: raw.op_maps,
        where_rules: raw.where_rules,
        op_map_files: raw
            .op_map_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        operation_files: raw
            .operation_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
    })
}

fn resolve_spec_path(base: &Path, path: PathBuf) -> PathBuf {
    if path.is_absolute() {
        path
    } else {
        base.join(path)
    }
}

fn parse_spec_output_format(raw: &str) -> Result<CliOutputFormat> {
    match raw.trim().to_ascii_lowercase().replace('_', "-").as_str() {
        "pprof" | "pb" | "pb-gz" | "pb.gz" => Ok(CliOutputFormat::Pprof),
        "folded" | "foldedtxt" | "folded-txt" => Ok(CliOutputFormat::Folded),
        "svg" => Ok(CliOutputFormat::Svg),
        "json" => Ok(CliOutputFormat::Json),
        other => bail!("unsupported profile spec format '{other}'"),
    }
}

fn parse_spec_view(raw: &str) -> Result<CliProfileView> {
    match raw.trim().to_ascii_lowercase().replace('_', "-").as_str() {
        "operations" | "operation" | "ops" => Ok(CliProfileView::Operations),
        "tokens" | "token" => Ok(CliProfileView::Tokens),
        "files" | "file" => Ok(CliProfileView::Files),
        "network" => Ok(CliProfileView::Network),
        "time" => Ok(CliProfileView::Time),
        other => bail!("unsupported profile spec view '{other}'"),
    }
}

impl ProfileSpec {
    fn merge(&mut self, next: ProfileSpec) {
        if next.output.is_some() {
            self.output = next.output;
        }
        if next.project_name.is_some() {
            self.project_name = next.project_name;
        }
        if next.format.is_some() {
            self.format = next.format;
        }
        if next.view.is_some() {
            self.view = next.view;
        }
        if next.stack.is_some() {
            self.stack = next.stack;
        }
        self.stack_rules.extend(next.stack_rules);
        self.op_maps.extend(next.op_maps);
        self.where_rules.extend(next.where_rules);
        self.op_map_files.extend(next.op_map_files);
        self.operation_files.extend(next.operation_files);
    }
}

fn load_op_map_rules(inline_rules: &[String], rule_files: &[PathBuf]) -> Result<Vec<String>> {
    let mut rules = inline_rules.to_vec();
    for path in rule_files {
        let contents = fs::read_to_string(path)
            .with_context(|| format!("failed to read --op-map-file {}", path.display()))?;
        for (line_idx, line) in contents.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('#') {
                continue;
            }
            parse_stack_rules_with_flag(&[trimmed.to_string()], "--op-map").with_context(|| {
                format!(
                    "invalid --op-map-file {} line {}",
                    path.display(),
                    line_idx + 1
                )
            })?;
            rules.push(trimmed.to_string());
        }
    }
    Ok(rules)
}

fn filter_agent_sessions_before_export(
    sessions: &mut Vec<agent_session::AgentSession>,
    args: &Cli,
) {
    if let Some(agent) = args.agent.as_deref() {
        sessions.retain(|session| session.agent_type.starts_with(agent));
    }
    if let Some(session_id) = args.session_id.as_deref() {
        sessions.retain(|session| session.session_id.contains(session_id));
    }
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
            annotate_sessions(sessions, &mut tagger)?;
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
    fn op_map_file_rules_ignore_comments_and_follow_inline_rules() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("operation-map.txt");
        std::fs::write(
            &path,
            "\n# default mappings\nphase:inspect=(effect=read)\nphase:execute=(effect=test)\n",
        )
        .unwrap();

        let rules = load_op_map_rules(&["phase:verify=(cmd=cargo)".to_string()], &[path]).unwrap();

        assert_eq!(
            rules,
            vec![
                "phase:verify=(cmd=cargo)",
                "phase:inspect=(effect=read)",
                "phase:execute=(effect=test)"
            ]
        );
    }

    #[test]
    fn profile_spec_resolves_paths_and_keeps_cli_rules_first() {
        let dir = tempfile::tempdir().unwrap();
        let spec_path = dir.path().join("agentnet-spec.json");
        let op_map_path = dir.path().join("maps").join("operation-map.txt");
        let cli_op_map_path = dir.path().join("cli-operation-map.txt");
        std::fs::create_dir_all(op_map_path.parent().unwrap()).unwrap();
        std::fs::write(&op_map_path, "phase:execute=(action=click)\n").unwrap();
        std::fs::write(&cli_op_map_path, "phase:cli=(action=click)\n").unwrap();
        std::fs::write(
            &spec_path,
            r#"{
  "output": "out/agent.folded",
  "format": "folded",
  "view": "operations",
  "project_name": "external-agent-traces",
  "operation_files": ["inputs/agentnet.jsonl"],
  "stack": "project,dataset,task,phase,op,tool,action,status",
  "op_maps": ["phase:inspect=(action=screenshot)"],
  "where_rules": ["phase!=noise"],
  "op_map_files": ["maps/operation-map.txt"],
  "stack_rules": ["task:desktop=(tool=computer)"]
}"#,
        )
        .unwrap();

        let spec = load_profile_specs(&[spec_path]).unwrap();
        assert_eq!(spec.format, Some(CliOutputFormat::Folded));
        assert_eq!(spec.view, Some(CliProfileView::Operations));
        assert_eq!(
            spec.output,
            Some(dir.path().join("out").join("agent.folded"))
        );
        assert_eq!(
            spec.operation_files,
            vec![dir.path().join("inputs").join("agentnet.jsonl")]
        );

        let op_maps = load_effective_op_map_rules(
            &["phase:verify=(cmd=cargo)".to_string()],
            &[cli_op_map_path],
            &spec.op_maps,
            &spec.op_map_files,
        )
        .unwrap();
        assert_eq!(
            op_maps,
            vec![
                "phase:verify=(cmd=cargo)",
                "phase:cli=(action=click)",
                "phase:inspect=(action=screenshot)",
                "phase:execute=(action=click)"
            ]
        );

        let where_rules = effective_where_rules(&["task=desktop".to_string()], &spec.where_rules);
        assert_eq!(where_rules, vec!["task=desktop".to_string()]);
        assert_eq!(
            effective_where_rules(&[], &spec.where_rules),
            vec!["phase!=noise".to_string()]
        );
    }

    #[test]
    fn trace_file_and_operation_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--trace-file",
            "trace.json",
            "--operation-file",
            "operations.jsonl",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--trace-file cannot be used with --operation-file"));
    }

    #[test]
    fn standard_trace_file_and_operation_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--standard-trace-file",
            "trace.json",
            "--operation-file",
            "operations.jsonl",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--standard-trace-file cannot be used with --operation-file"));
    }

    #[test]
    fn standard_trace_file_and_trace_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--standard-trace-file",
            "standard-trace.json",
            "--trace-file",
            "agent-trace.json",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--standard-trace-file cannot be used with --trace-file"));
    }

    #[test]
    fn export_trace_rejects_tag_filters() {
        let args = Cli::parse_from([
            "agentpprof",
            "--session-file",
            "missing.jsonl",
            "--export-trace",
            "trace.json",
            "--prompt-tag",
            "review",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("trace export cannot be combined with --session-tag"));
    }

    #[test]
    fn export_standard_trace_rejects_tag_filters() {
        let args = Cli::parse_from([
            "agentpprof",
            "--session-file",
            "missing.jsonl",
            "--export-standard-trace",
            "trace.json",
            "--prompt-tag",
            "review",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("trace export cannot be combined with --session-tag"));
    }

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
                    text_hash: "h0".to_string(),
                    preview: "review prompt".to_string(),
                    tag: "review".to_string(),
                },
                UserRequest {
                    index: 0,
                    ts_ms: Some(2),
                    text_hash: "h1".to_string(),
                    preview: "test prompt".to_string(),
                    tag: "test".to_string(),
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
                    domains: Vec::new(),
                    call_id: None,
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
                    domains: Vec::new(),
                    call_id: None,
                },
            ],
            llm_calls: vec![
                LlmEvent {
                    ts_ms: Some(5),
                    prompt_index: 0,
                    model: "claude".to_string(),
                    text_hash: "l0".to_string(),
                    preview: "review answer".to_string(),
                    input_tokens: 1,
                    output_tokens: 1,
                    cache_tokens: 0,
                    total_tokens: 0,
                    tag: "answer".to_string(),
                },
                LlmEvent {
                    ts_ms: Some(6),
                    prompt_index: 1,
                    model: "claude".to_string(),
                    text_hash: "l1".to_string(),
                    preview: "test answer".to_string(),
                    input_tokens: 2,
                    output_tokens: 3,
                    cache_tokens: 0,
                    total_tokens: 0,
                    tag: "answer".to_string(),
                },
            ],
            session_tag: "review".to_string(),
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
