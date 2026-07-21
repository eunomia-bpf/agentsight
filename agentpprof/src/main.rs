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
    OperationStackConfig, OperationStackInductionConfig, OutputFormat, ProfileView, StackRankMode,
    build_profile_from_operation_records, build_profile_with_options, infer_output_format,
    parse_operation_filters, parse_operation_rank_rules, parse_stack_rank_rules, parse_stack_rules,
    parse_stack_rules_with_flag, parse_stack_spec, profile_to_stacks, read_operation_record_values,
    write_pprof_difference, write_projection,
};
use session::{
    SessionRecord, default_claude_root, discover_agent_sessions, load_agent_trace_files,
    session_records_from_agent_sessions, write_agent_trace,
};
use tagger::{
    LlamaTagger, RegexTagger, TagDiagnostics, annotate_sessions_regex,
    annotate_sessions_with_declared_tasks, default_tag_cache_path, parse_declared_tag_choices,
};

const DEFAULT_LLAMA_URL: &str = "http://127.0.0.1:8080";

const TAGGING_HELP: &str = r#"
FIELD DERIVATION WORKFLOW:
  agentpprof has two core profiling abstractions: operations and operation
  stacks. Tags and mappings derive operation fields before folding; prompts,
  sessions, tools, processes, and trace spans are fields or input containers,
  not separate profiler objects.

  For local free-form prompts, deterministic tags are one field-derivation
  mechanism. Without --tag-rule or --preset, prompts are marked 'unmatched' and
  prompt-tag frames will not aggregate well.

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

OPERATION STACK QUERY WORKFLOW:
  --view chooses which operation samples are measured. --stack chooses how those
  operations fold into a stack. Use --op-map to derive reusable operation
  fields, --where to select an operation subset, then --stack chooses how those
  fields recursively fold. Use
  --op-map-file to load reusable mappings, and --stack-rule for one-off
  stack-frame overrides. JSON output can also include visible stack-ranking
  rules with --rank-rule, operation-field ranking rules with --rank-op-rule,
  and --rank-mode.

     agentpprof --view files -o files.json --format json \
       --stack 'project,agent,task,phase,op,tool,path,status' \
       --op-map-file operation-map.txt \
       --op-map 'task:verify=(effect=test|cmd=cargo)' \
       --op-map 'phase:inspect=(effect=read)' \
       --where 'task=verify' \
       --rank-mode rule-score \
       --rank-rule 'verify-risk:2=phase:execute|status:error' \
       --rank-op-rule 'error-density:3=status=error'

  For repeatable external-trace experiments, put output, view, operation files,
  op-map files, predicates, rank rules, stack, and local-session tagging rules
  in a JSON file and run:

     agentpprof --profile-spec agentnet-diagnostic-spec.json

  --induce-operation-stack derives recurring operation identities before
  folding. Each operation must provide one visible session and action. The
  inducer learns adjacent-action NPMI across sessions, separates recurring from
  non-recurring transitions with deterministic two-means, and names each
  segment from its run-length-compressed action motif. An optional label-free
  --induce-reference-operation-file supplies a separate recurrence corpus.
  When independently grouped history exists, add
  --induce-calibration-operation-file to select one supervised scalar cutoff
  by operation-weighted B-cubed partition F1 while keeping the same NPMI score.
"#;

#[derive(Parser)]
#[command(name = "agentpprof")]
#[command(version)]
#[command(
    about = "pprof-compatible operation-stack profiler for local sessions and labeled agent traces"
)]
#[command(after_help = TAGGING_HELP)]
#[derive(Clone)]
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
    /// Rank JSON stack groups by visible folded-stack text, e.g. risk:2='phase:execute|status:error'.
    /// Ranking runs after operation stacking and never reads hidden labels unless the stack includes them.
    #[arg(long = "rank-rule", value_name = "LABEL:WEIGHT=REGEX")]
    rank_rules: Vec<String>,
    /// Rank JSON operation-stack groups using visible per-operation field matches aggregated inside each group.
    /// Unlike --rank-rule, these regexes run on mapped operation fields before folding.
    #[arg(long = "rank-op-rule", value_name = "LABEL:WEIGHT=REGEX")]
    rank_op_rules: Vec<String>,
    /// Choose how JSON rank rules order stack groups.
    #[arg(long = "rank-mode", value_enum)]
    rank_mode: Option<CliRankMode>,
    /// Derive recurring operation identities from visible session/action transitions.
    #[arg(long = "induce-operation-stack")]
    induce_operation_stack: bool,
    /// Deprecated compatibility alias for --induce-operation-stack.
    #[arg(long = "induce-task-stack")]
    induce_task_stack: bool,
    /// Legacy information-gain option; rejected by recurrence induction.
    #[arg(long = "induce-allow-session")]
    induce_allow_session: bool,
    /// Legacy information-gain option; rejected by recurrence induction.
    #[arg(long = "induce-max-depth")]
    induce_max_depth: Option<usize>,
    /// Legacy information-gain option; rejected by recurrence induction.
    #[arg(long = "induce-query-term", value_name = "TERM")]
    induce_query_terms: Vec<String>,
    /// Learn operation recurrence from a separate label-free operation corpus.
    #[arg(long = "induce-reference-operation-file", value_name = "PATH")]
    induce_reference_operation_files: Vec<PathBuf>,
    /// Fit one recurrence cutoff from grouped reference operations.
    #[arg(long = "induce-calibration-operation-file", value_name = "PATH")]
    induce_calibration_operation_files: Vec<PathBuf>,
    /// Write byte-stable profiles by replacing output timestamps with fixed values.
    #[arg(long = "deterministic-output")]
    deterministic_output: bool,
    /// Read operation-field mapping rules from a file. Blank lines and lines starting with '#' are ignored.
    /// Inline --op-map rules run before file rules, so command-line rules can override defaults.
    #[arg(long = "op-map-file", value_name = "PATH")]
    op_map_files: Vec<PathBuf>,
    #[arg(long, value_enum)]
    tagger: Option<TaggerKind>,
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
    /// Subtract these normalized operation records from --operation-file and
    /// write one signed candidate-minus-base pprof profile.
    #[arg(long = "diff-base-operation-file", value_name = "PATH")]
    diff_base_operation_files: Vec<PathBuf>,
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

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
enum CliRankMode {
    WidthBoost,
    RuleScore,
}

impl From<CliRankMode> for StackRankMode {
    fn from(val: CliRankMode) -> Self {
        match val {
            CliRankMode::WidthBoost => StackRankMode::WidthBoost,
            CliRankMode::RuleScore => StackRankMode::RuleScore,
        }
    }
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

#[derive(Clone, Copy, Debug, ValueEnum, PartialEq, Eq)]
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
    rank_rules: Vec<String>,
    rank_op_rules: Vec<String>,
    rank_mode: Option<CliRankMode>,
    induce_operation_stack: Option<bool>,
    induce_task_stack: Option<bool>,
    induce_allow_session: Option<bool>,
    induce_max_depth: Option<usize>,
    induce_query_terms: Vec<String>,
    induce_reference_operation_files: Vec<PathBuf>,
    induce_calibration_operation_files: Vec<PathBuf>,
    tag_rules: Vec<String>,
    preset: Option<bool>,
    tagger: Option<TaggerKind>,
    deterministic_output: Option<bool>,
    include_standard_trace_args: Option<bool>,
    op_map_files: Vec<PathBuf>,
    operation_files: Vec<PathBuf>,
    diff_base_operation_files: Vec<PathBuf>,
    session_files: Vec<PathBuf>,
    trace_files: Vec<PathBuf>,
    standard_trace_files: Vec<PathBuf>,
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
    rank_rules: Vec<String>,
    #[serde(default)]
    rank_op_rules: Vec<String>,
    rank_mode: Option<String>,
    induce_operation_stack: Option<bool>,
    induce_task_stack: Option<bool>,
    induce_allow_session: Option<bool>,
    induce_max_depth: Option<usize>,
    #[serde(default)]
    induce_query_terms: Vec<String>,
    #[serde(default)]
    induce_reference_operation_files: Vec<PathBuf>,
    #[serde(default)]
    induce_calibration_operation_files: Vec<PathBuf>,
    #[serde(default)]
    tag_rules: Vec<String>,
    preset: Option<bool>,
    tagger: Option<String>,
    deterministic_output: Option<bool>,
    include_standard_trace_args: Option<bool>,
    #[serde(default)]
    op_map_files: Vec<PathBuf>,
    #[serde(default)]
    operation_files: Vec<PathBuf>,
    #[serde(default)]
    diff_base_operation_files: Vec<PathBuf>,
    #[serde(default)]
    session_files: Vec<PathBuf>,
    #[serde(default)]
    trace_files: Vec<PathBuf>,
    #[serde(default)]
    standard_trace_files: Vec<PathBuf>,
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
    let requested_operation_induction =
        args.induce_operation_stack || spec.induce_operation_stack.unwrap_or(false);
    let requested_legacy_task_induction =
        args.induce_task_stack || spec.induce_task_stack.unwrap_or(false);
    let induce_operation_stack = requested_operation_induction || requested_legacy_task_induction;
    let induced_stack_field = if requested_operation_induction {
        "operation"
    } else {
        "task"
    };
    let induce_query_terms = merge_cli_first(&args.induce_query_terms, &spec.induce_query_terms);
    let legacy_induction_options_requested = args.induce_allow_session
        || spec.induce_allow_session.is_some()
        || args.induce_max_depth.is_some()
        || spec.induce_max_depth.is_some()
        || !induce_query_terms.is_empty();
    if induce_operation_stack && legacy_induction_options_requested {
        bail!(
            "recurrence-based --induce-operation-stack does not accept --induce-allow-session, --induce-max-depth, or --induce-query-term"
        );
    }
    let induce_reference_operation_files = merge_spec_first(
        &spec.induce_reference_operation_files,
        &args.induce_reference_operation_files,
    );
    let induce_calibration_operation_files = merge_spec_first(
        &spec.induce_calibration_operation_files,
        &args.induce_calibration_operation_files,
    );
    if !induce_operation_stack && !induce_reference_operation_files.is_empty() {
        bail!("--induce-reference-operation-file requires --induce-operation-stack");
    }
    if !induce_operation_stack && !induce_calibration_operation_files.is_empty() {
        bail!("--induce-calibration-operation-file requires --induce-operation-stack");
    }
    if !induce_calibration_operation_files.is_empty() && induce_reference_operation_files.is_empty()
    {
        bail!("--induce-calibration-operation-file requires --induce-reference-operation-file");
    }
    let effective_stack_name = if induce_operation_stack {
        if let Some(stack) = stack
            && stack.trim() != induced_stack_field
        {
            bail!(
                "--induce-operation-stack derives recurring operation identities; omit --stack or use --stack {induced_stack_field}"
            );
        }
        profile_options = profile_options.with_stack(parse_stack_spec(induced_stack_field)?);
        induced_stack_field
    } else if let Some(stack) = stack {
        profile_options = profile_options.with_stack(parse_stack_spec(stack)?);
        stack
    } else {
        "default"
    };
    let op_map_files = merge_cli_first(&args.op_map_files, &spec.op_map_files);
    let op_maps = load_effective_op_map_rules(
        &args.op_maps,
        &args.op_map_files,
        &spec.op_maps,
        &spec.op_map_files,
    )?;
    let stack_rules = merge_cli_first(&args.stack_rules, &spec.stack_rules);
    let where_rules = effective_where_rules(&args.where_rules, &spec.where_rules);
    let rank_rules = merge_cli_first(&args.rank_rules, &spec.rank_rules);
    let rank_op_rules = merge_cli_first(&args.rank_op_rules, &spec.rank_op_rules);
    let rank_mode = args
        .rank_mode
        .or(spec.rank_mode)
        .unwrap_or(CliRankMode::WidthBoost);
    let tag_rules = merge_cli_first(&args.tag_rules, &spec.tag_rules);
    let preset = args.preset || spec.preset.unwrap_or(false);
    let tagger = args.tagger.or(spec.tagger).unwrap_or(TaggerKind::Regex);
    let deterministic_output =
        args.deterministic_output || spec.deterministic_output.unwrap_or(false);
    let include_standard_trace_args =
        args.include_standard_trace_args || spec.include_standard_trace_args.unwrap_or(false);
    profile_options = profile_options
        .with_field_rules(parse_stack_rules_with_flag(&op_maps, "--op-map")?)
        .with_filters(parse_operation_filters(&where_rules)?)
        .with_rules(parse_stack_rules(&stack_rules)?)
        .with_rank_rules(parse_stack_rank_rules(&rank_rules)?)
        .with_rank_operation_rules(parse_operation_rank_rules(&rank_op_rules)?)
        .with_rank_mode(rank_mode.into());
    if induce_operation_stack {
        let mut induction =
            OperationStackInductionConfig::new().with_derived_field(induced_stack_field);
        if !induce_reference_operation_files.is_empty() {
            let reference_records =
                read_operation_record_values(&induce_reference_operation_files)?;
            induction = induction.with_reference_operation_records(&reference_records)?;
        }
        if !induce_calibration_operation_files.is_empty() {
            let calibration_records =
                read_operation_record_values(&induce_calibration_operation_files)?;
            induction = induction.with_calibration_operation_records(&calibration_records)?;
        }
        profile_options = profile_options.with_operation_stack_induction(induction);
    }
    let operation_files = merge_spec_first(&spec.operation_files, &args.operation_files);
    let diff_base_operation_files = merge_spec_first(
        &spec.diff_base_operation_files,
        &args.diff_base_operation_files,
    );
    let session_files = merge_spec_first(&spec.session_files, &args.session_files);
    let trace_files = merge_spec_first(&spec.trace_files, &args.trace_files);
    let standard_trace_files =
        merge_spec_first(&spec.standard_trace_files, &args.standard_trace_files);
    validate_input_modes(
        &args,
        &operation_files,
        &diff_base_operation_files,
        &session_files,
        &trace_files,
        &standard_trace_files,
    )?;
    if !standard_trace_files.is_empty() {
        let output = output
            .as_ref()
            .context("missing output path; pass -o/--output or set output in --profile-spec")?;
        let format = infer_output_format(requested_format.into(), output);
        let operation_records = standard_trace::operation_records_from_chrome_trace_files(
            &standard_trace_files,
            &project_name,
            include_standard_trace_args,
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
            deterministic_output,
        )?;
        let result = json!({
            "status": "ok",
            "output": output,
            "format": format!("{:?}", format).to_ascii_lowercase(),
            "view": profile.view,
            "sample_type": profile.sample_type,
            "unit": profile.unit,
            "profile_specs": args.profile_specs,
            "stack": effective_stack_name,
            "induce_operation_stack": induce_operation_stack,
            "induce_task_stack": induce_operation_stack,
            "induced_stack_field": induced_stack_field,
            "induce_reference_operation_files": induce_reference_operation_files,
            "induce_calibration_operation_files": induce_calibration_operation_files,
            "op_maps": op_maps,
            "op_map_files": op_map_files,
            "where_rules": where_rules,
            "rank_rules": rank_rules,
            "rank_op_rules": rank_op_rules,
            "rank_mode": cli_rank_mode_name(rank_mode),
            "deterministic_output": deterministic_output,
            "stack_rules": stack_rules,
            "standard_trace_files": standard_trace_files,
            "standard_trace_format": standard_trace::CHROME_TRACE_FORMAT,
            "include_standard_trace_args": include_standard_trace_args,
            "operations": operation_records.len(),
            "samples": stacks.values().sum::<u64>(),
            "unique_stacks": stacks.len(),
            "warnings": [],
        });
        println!("{}", serde_json::to_string_pretty(&result)?);
        return Ok(());
    }
    if !operation_files.is_empty() {
        let operation_records = read_operation_record_values(&operation_files)?;
        if !diff_base_operation_files.is_empty() && induce_operation_stack {
            bail!(
                "--diff-base-operation-file cannot be combined with --induce-operation-stack; provide explicit shared stack fields for both inputs"
            );
        }
        let standard_trace_events = if let Some(trace_path) = args.export_standard_trace.as_ref() {
            Some(standard_trace::write_chrome_trace_from_operation_records(
                trace_path,
                &operation_records,
                &project_name,
            )?)
        } else {
            None
        };
        if output.is_none() {
            let result = json!({
                "status": "ok",
                "standard_trace_output": args.export_standard_trace,
                "standard_trace_format": if args.export_standard_trace.is_some() {
                    Some(standard_trace::CHROME_TRACE_FORMAT)
                } else {
                    None
                },
                "standard_trace_events": standard_trace_events,
                "operation_files": operation_files,
                "operations": operation_records.len(),
                "warnings": [],
            });
            println!("{}", serde_json::to_string_pretty(&result)?);
            return Ok(());
        }
        let output = output
            .as_ref()
            .context("missing output path; pass -o/--output or set output in --profile-spec")?;
        let format = infer_output_format(requested_format.into(), output);
        let profile =
            build_profile_from_operation_records(&operation_records, view, &profile_options)?;
        let stacks = profile_to_stacks(&profile);
        if stacks.is_empty() {
            bail!("operation input produced no folded stacks");
        }
        let difference = if diff_base_operation_files.is_empty() {
            write_projection(
                &profile,
                format,
                output,
                args.include_previews,
                &[],
                args.svg_width,
                deterministic_output,
            )?;
            None
        } else {
            if format != OutputFormat::Pprof {
                bail!(
                    "--diff-base-operation-file only writes standard pprof; use a .pb or .pb.gz output and omit non-pprof --format values"
                );
            }
            let base_records = read_operation_record_values(&diff_base_operation_files)?;
            let base_profile =
                build_profile_from_operation_records(&base_records, view, &profile_options)?;
            let base_stacks = profile_to_stacks(&base_profile);
            Some(write_pprof_difference(
                &profile,
                &stacks,
                &base_stacks,
                output,
                deterministic_output,
            )?)
        };
        let positive_difference = difference.as_ref().map(|samples| {
            samples
                .values()
                .filter(|value| **value > 0)
                .map(|value| *value as u64)
                .sum::<u64>()
        });
        let negative_difference = difference.as_ref().map(|samples| {
            samples
                .values()
                .filter(|value| **value < 0)
                .map(|value| value.unsigned_abs())
                .sum::<u64>()
        });
        let result = json!({
            "status": "ok",
            "output": output,
            "format": format!("{:?}", format).to_ascii_lowercase(),
            "view": profile.view,
            "sample_type": profile.sample_type,
            "unit": profile.unit,
            "profile_specs": args.profile_specs,
            "stack": effective_stack_name,
            "induce_operation_stack": induce_operation_stack,
            "induce_task_stack": induce_operation_stack,
            "induced_stack_field": induced_stack_field,
            "induce_reference_operation_files": induce_reference_operation_files,
            "induce_calibration_operation_files": induce_calibration_operation_files,
            "op_maps": op_maps,
            "op_map_files": op_map_files,
            "where_rules": where_rules,
            "rank_rules": rank_rules,
            "rank_op_rules": rank_op_rules,
            "rank_mode": cli_rank_mode_name(rank_mode),
            "deterministic_output": deterministic_output,
            "stack_rules": stack_rules,
            "operation_files": operation_files,
            "diff_base_operation_files": diff_base_operation_files,
            "comparison": difference.as_ref().map(|_| "candidate-minus-base"),
            "operations": operation_records.len(),
            "standard_trace_output": args.export_standard_trace,
            "standard_trace_format": if args.export_standard_trace.is_some() {
                Some(standard_trace::CHROME_TRACE_FORMAT)
            } else {
                None
            },
            "standard_trace_events": standard_trace_events,
            "samples": stacks.values().sum::<u64>(),
            "unique_stacks": stacks.len(),
            "difference_unique_stacks": difference.as_ref().map(|samples| samples.len()),
            "positive_difference": positive_difference,
            "negative_difference": negative_difference,
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
    let mut agent_sessions = if !trace_files.is_empty() {
        load_agent_trace_files(&trace_files)?
    } else {
        discover_agent_sessions(
            &project_root,
            &codex_root,
            &claude_root,
            &session_files,
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
            "session_files": session_files,
            "trace_files": trace_files,
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
    let mut tagging_args = args.clone();
    tagging_args.tag_rules = tag_rules.clone();
    tagging_args.preset = preset;
    tagging_args.tagger = Some(tagger);
    let diagnostics = annotate_sessions_with(&mut sessions, &tagging_args)?;
    filter_sessions_after_tagging(&mut sessions, &args);
    if sessions.is_empty() {
        bail!("sessions were found, but none matched the requested tag filters");
    }
    let output = output
        .as_ref()
        .context("missing output path; pass -o/--output or set output in --profile-spec")?;
    let format = infer_output_format(requested_format.into(), output);
    let profile = build_profile_with_options(&sessions, &project_name, view, &profile_options)?;
    let stacks = profile_to_stacks(&profile);
    if stacks.is_empty() {
        bail!("selected view {:?} produced no samples", cli_view);
    }
    write_projection(
        &profile,
        format,
        output,
        args.include_previews,
        &sessions,
        args.svg_width,
        deterministic_output,
    )?;

    let mut result = json!({
        "status": "ok",
        "output": output,
        "format": format!("{:?}", format).to_ascii_lowercase(),
        "view": profile.view,
        "sample_type": profile.sample_type,
        "unit": profile.unit,
        "profile_specs": args.profile_specs,
        "trace_files": trace_files,
        "trace_output": args.export_trace,
        "standard_trace_output": args.export_standard_trace,
        "standard_trace_format": if args.export_standard_trace.is_some() {
            Some(standard_trace::CHROME_TRACE_FORMAT)
        } else {
            None
        },
        "standard_trace_events": standard_trace_events,
        "stack": effective_stack_name,
        "induce_operation_stack": induce_operation_stack,
        "induce_task_stack": induce_operation_stack,
        "induced_stack_field": induced_stack_field,
        "induce_reference_operation_files": induce_reference_operation_files,
        "induce_calibration_operation_files": induce_calibration_operation_files,
        "op_maps": op_maps,
        "op_map_files": op_map_files,
        "where_rules": where_rules,
        "rank_rules": rank_rules,
        "rank_op_rules": rank_op_rules,
        "rank_mode": cli_rank_mode_name(rank_mode),
        "tagger": cli_tagger_name(tagger),
        "tag_rules": tag_rules,
        "preset": preset,
        "deterministic_output": deterministic_output,
        "stack_rules": stack_rules,
        "sessions": sessions.len(),
        "session_files": session_files,
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

fn validate_input_modes(
    args: &Cli,
    operation_files: &[PathBuf],
    diff_base_operation_files: &[PathBuf],
    session_files: &[PathBuf],
    trace_files: &[PathBuf],
    standard_trace_files: &[PathBuf],
) -> Result<()> {
    if !diff_base_operation_files.is_empty() && operation_files.is_empty() {
        bail!("--diff-base-operation-file requires --operation-file");
    }
    if !diff_base_operation_files.is_empty()
        && (args.export_trace.is_some() || args.export_standard_trace.is_some())
    {
        bail!(
            "--diff-base-operation-file cannot be combined with trace export; it writes one signed pprof comparison"
        );
    }
    if !operation_files.is_empty() && !trace_files.is_empty() {
        bail!("--trace-file cannot be used with --operation-file");
    }
    if !operation_files.is_empty() && !session_files.is_empty() {
        bail!("--session-file cannot be used with --operation-file");
    }
    if !trace_files.is_empty() && !session_files.is_empty() {
        bail!("--session-file cannot be used with --trace-file");
    }
    if !standard_trace_files.is_empty() {
        if !operation_files.is_empty() {
            bail!("--standard-trace-file cannot be used with --operation-file");
        }
        if !session_files.is_empty() {
            bail!("--standard-trace-file cannot be used with --session-file");
        }
        if !trace_files.is_empty() {
            bail!("--standard-trace-file cannot be used with --trace-file");
        }
        if args.export_trace.is_some() || args.export_standard_trace.is_some() {
            bail!(
                "--standard-trace-file cannot be used with --export-trace or --export-standard-trace"
            );
        }
    }
    if args.export_trace.is_some() || args.export_standard_trace.is_some() {
        if args.export_trace.is_some() && !operation_files.is_empty() {
            bail!("--export-trace cannot be used with --operation-file");
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
        rank_rules: raw.rank_rules,
        rank_op_rules: raw.rank_op_rules,
        rank_mode: raw
            .rank_mode
            .as_deref()
            .map(parse_spec_rank_mode)
            .transpose()?,
        induce_operation_stack: raw.induce_operation_stack,
        induce_task_stack: raw.induce_task_stack,
        induce_allow_session: raw.induce_allow_session,
        induce_max_depth: raw.induce_max_depth,
        induce_query_terms: raw.induce_query_terms,
        induce_reference_operation_files: raw
            .induce_reference_operation_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        induce_calibration_operation_files: raw
            .induce_calibration_operation_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        tag_rules: raw.tag_rules,
        preset: raw.preset,
        tagger: raw.tagger.as_deref().map(parse_spec_tagger).transpose()?,
        deterministic_output: raw.deterministic_output,
        include_standard_trace_args: raw.include_standard_trace_args,
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
        diff_base_operation_files: raw
            .diff_base_operation_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        session_files: raw
            .session_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        trace_files: raw
            .trace_files
            .into_iter()
            .map(|path| resolve_spec_path(base, path))
            .collect(),
        standard_trace_files: raw
            .standard_trace_files
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

fn parse_spec_rank_mode(raw: &str) -> Result<CliRankMode> {
    match raw.trim().to_ascii_lowercase().replace('_', "-").as_str() {
        "width-boost" | "widthboost" => Ok(CliRankMode::WidthBoost),
        "rule-score" | "rulescore" => Ok(CliRankMode::RuleScore),
        other => bail!("unsupported profile spec rank_mode '{other}'"),
    }
}

fn parse_spec_tagger(raw: &str) -> Result<TaggerKind> {
    match raw.trim().to_ascii_lowercase().replace('_', "-").as_str() {
        "regex" => Ok(TaggerKind::Regex),
        "llm" | "llama" | "llama-cpp" => Ok(TaggerKind::Llm),
        other => bail!("unsupported profile spec tagger '{other}'"),
    }
}

fn cli_rank_mode_name(mode: CliRankMode) -> &'static str {
    match mode {
        CliRankMode::WidthBoost => "width-boost",
        CliRankMode::RuleScore => "rule-score",
    }
}

fn cli_tagger_name(tagger: TaggerKind) -> &'static str {
    match tagger {
        TaggerKind::Regex => "regex",
        TaggerKind::Llm => "llm",
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
        if next.rank_mode.is_some() {
            self.rank_mode = next.rank_mode;
        }
        if next.induce_task_stack.is_some() {
            self.induce_task_stack = next.induce_task_stack;
        }
        if next.induce_operation_stack.is_some() {
            self.induce_operation_stack = next.induce_operation_stack;
        }
        if next.induce_allow_session.is_some() {
            self.induce_allow_session = next.induce_allow_session;
        }
        if next.induce_max_depth.is_some() {
            self.induce_max_depth = next.induce_max_depth;
        }
        if next.preset.is_some() {
            self.preset = next.preset;
        }
        if next.tagger.is_some() {
            self.tagger = next.tagger;
        }
        if next.deterministic_output.is_some() {
            self.deterministic_output = next.deterministic_output;
        }
        if next.include_standard_trace_args.is_some() {
            self.include_standard_trace_args = next.include_standard_trace_args;
        }
        self.stack_rules.extend(next.stack_rules);
        self.op_maps.extend(next.op_maps);
        self.where_rules.extend(next.where_rules);
        self.rank_rules.extend(next.rank_rules);
        self.rank_op_rules.extend(next.rank_op_rules);
        self.induce_query_terms.extend(next.induce_query_terms);
        self.induce_reference_operation_files
            .extend(next.induce_reference_operation_files);
        self.induce_calibration_operation_files
            .extend(next.induce_calibration_operation_files);
        self.tag_rules.extend(next.tag_rules);
        self.op_map_files.extend(next.op_map_files);
        self.operation_files.extend(next.operation_files);
        self.diff_base_operation_files
            .extend(next.diff_base_operation_files);
        self.session_files.extend(next.session_files);
        self.trace_files.extend(next.trace_files);
        self.standard_trace_files.extend(next.standard_trace_files);
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
    match args.tagger.unwrap_or(TaggerKind::Regex) {
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
            if args.no_cache {
                tagger.disable_cache();
            }
            let task_choices = parse_declared_tag_choices(&args.task_choices)?;
            annotate_sessions_with_declared_tasks(sessions, &mut tagger, &task_choices)?;
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
    use clap::CommandFactory;
    use std::path::PathBuf;

    #[test]
    fn cli_help_describes_operation_stack_model() {
        let mut command = Cli::command();
        let mut output = Vec::new();
        command.write_long_help(&mut output).unwrap();
        let help = String::from_utf8(output).unwrap();

        assert!(help.contains("operation-stack profiler"));
        assert!(help.contains("two core profiling abstractions"));
        assert!(help.contains("Tags and mappings derive operation fields before folding"));
        assert!(help.contains("OPERATION STACK QUERY WORKFLOW"));
        assert!(!help.contains("semantic profiler for local AI coding-agent sessions"));
        assert!(!help.contains("Flamegraphs require semantic tags"));
    }

    #[test]
    fn declared_task_taxonomy_requires_llm_tagger() {
        let args = Cli::parse_from([
            "agentpprof",
            "-o",
            "out.json",
            "--task-choice",
            "alfworld=household tasks",
            "--task-choice",
            "webshop=shopping tasks",
        ]);
        let err = annotate_sessions_with(&mut [], &args)
            .unwrap_err()
            .to_string();

        assert!(err.contains("--task-choice requires --tagger llm"));
    }

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
  "diff_base_operation_files": ["inputs/agentnet-good.jsonl"],
  "session_files": ["sessions/codex.jsonl"],
  "trace_files": ["traces/agent-trace.json"],
  "standard_trace_files": ["traces/chrome-trace.json"],
  "include_standard_trace_args": true,
  "stack": "project,dataset,task,phase,op,tool,action,status",
  "op_maps": ["phase:inspect=(action=screenshot)"],
  "where_rules": ["phase!=noise"],
  "rank_rules": ["unsafe-risk:2=phase:execute|status:error"],
  "rank_op_rules": ["failure-density:3=status=error"],
  "rank_mode": "rule-score",
  "tagger": "regex",
  "preset": true,
  "tag_rules": ["prompt:review=(?i)review|diff"],
  "deterministic_output": true,
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
        assert_eq!(
            spec.diff_base_operation_files,
            vec![dir.path().join("inputs").join("agentnet-good.jsonl")]
        );
        assert_eq!(
            spec.session_files,
            vec![dir.path().join("sessions").join("codex.jsonl")]
        );
        assert_eq!(
            spec.trace_files,
            vec![dir.path().join("traces").join("agent-trace.json")]
        );
        assert_eq!(
            spec.standard_trace_files,
            vec![dir.path().join("traces").join("chrome-trace.json")]
        );
        assert_eq!(spec.include_standard_trace_args, Some(true));

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
        assert_eq!(
            spec.rank_rules,
            vec!["unsafe-risk:2=phase:execute|status:error".to_string()]
        );
        assert_eq!(
            spec.rank_op_rules,
            vec!["failure-density:3=status=error".to_string()]
        );
        assert_eq!(spec.rank_mode, Some(CliRankMode::RuleScore));
        assert_eq!(spec.tagger, Some(TaggerKind::Regex));
        assert_eq!(spec.preset, Some(true));
        assert_eq!(
            spec.tag_rules,
            vec!["prompt:review=(?i)review|diff".to_string()]
        );
        assert_eq!(spec.deterministic_output, Some(true));
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
    fn session_file_and_operation_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--session-file",
            "session.jsonl",
            "--operation-file",
            "operations.jsonl",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--session-file cannot be used with --operation-file"));
    }

    #[test]
    fn session_file_and_trace_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--session-file",
            "session.jsonl",
            "--trace-file",
            "trace.json",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--session-file cannot be used with --trace-file"));
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
    fn standard_trace_file_and_session_file_are_mutually_exclusive() {
        let args = Cli::parse_from([
            "agentpprof",
            "--standard-trace-file",
            "standard-trace.json",
            "--session-file",
            "session.jsonl",
            "-o",
            "out.folded",
        ]);
        let err = command_export(args).unwrap_err().to_string();

        assert!(err.contains("--standard-trace-file cannot be used with --session-file"));
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
    fn deterministic_output_makes_json_profiles_byte_stable() {
        let dir = tempfile::tempdir().unwrap();
        let operations = dir.path().join("operations.jsonl");
        let out1 = dir.path().join("one.json");
        let out2 = dir.path().join("two.json");
        std::fs::write(
            &operations,
            r#"{"value":1,"fields":{"task":"verify","status":"ok"}}
{"value":2,"fields":{"task":"verify","status":"error"}}
"#,
        )
        .unwrap();

        for output in [&out1, &out2] {
            let args = Cli::parse_from([
                "agentpprof",
                "--operation-file",
                operations.to_str().unwrap(),
                "--view",
                "operations",
                "--format",
                "json",
                "--stack",
                "task,status",
                "--deterministic-output",
                "-o",
                output.to_str().unwrap(),
            ]);
            command_export(args).unwrap();
        }

        let first = std::fs::read_to_string(&out1).unwrap();
        let second = std::fs::read_to_string(&out2).unwrap();
        assert_eq!(first, second);
        assert!(first.contains(r#""generated_at": "1970-01-01T00:00:00Z""#));
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
