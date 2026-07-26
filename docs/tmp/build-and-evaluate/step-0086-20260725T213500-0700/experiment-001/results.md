# Results: complete frozen-population semantic profiles

Status: **COMPLETE; Phases 1--4 valid**

## Outcome

The continuation resolved the exact Phase 2 product gap identified by the
previous run. AgentPProf can now initialize its standard three-file annotation
workspace directly from local Codex and Claude sessions through the existing
`agent-session` IR. The complete frozen 42-session population was converted,
annotated once with the fixed automatic-backend instruction, and materialized
as both operation-count and token-width standard pprof profiles.

The experiment's operational hypothesis is supported: the repository-native
session IR contains enough structure and additive resource data to produce a
deterministic semantic workspace and mass-conserving pprof profiles for this
real, long-horizon population. This is feasibility and descriptive evidence;
it is not a controlled comparison of debugging and profiling, nor a
measurement of annotation accuracy.

## Product result

The new local-session option is:

```text
agentpprof --workspace-out <dir> [local-session input options]
```

It emits only the established product workspace:

```text
<dir>/trace.jsonl
<dir>/annotation.json
<dir>/stacks.folded
```

The adapter reuses `discover_agent_sessions`, `load_agent_trace_files`, and
the existing `SessionRecord` conversion over the `agent-session` IR. It emits
stable, parent-before-child session, prompt, LLM, and tool nodes; preserves
bounded source previews; assigns tokens only to LLM nodes and one operation
unit to every tool; and attaches each tool to its nearest same-prompt LLM.
Initialization refuses to overwrite any existing workspace file.

The integration test covers the three-file contract, all four node kinds,
stable trace bytes and IDs, parent order, metrics, previews, tool attachment,
and overwrite refusal. The complete AgentPProf test suite passed:

```text
90 tests passed; 0 failed
```

The release build and formatting check also passed.

## Population and workspace

| Check | Result |
| --- | ---: |
| Frozen sessions | 42 |
| Codex / Claude sessions | 18 / 24 |
| Frozen bytes | 55,000,887 |
| Frozen copies at recorded byte length | 42 / 42 |
| Trace nodes | 10,423 |
| Session nodes | 42 |
| Prompt nodes | 1,252 |
| LLM nodes | 5,620 |
| Tool nodes | 3,509 |
| Missing or forward parent references | 0 |
| Tools parented by LLM nodes | 3,509 / 3,509 |
| Tool-operation mass | 3,509 |
| Bounded LLM token mass | 1,380,863,014 |

These counts exactly reproduce the previous direct-ingestion probes. Relative
to the coarse step-0084 inventory, the richer parser materializes 120 more
prompts, 80 more LLM calls, and 58 more tools. The token totals are different
constructs: the inventory used session-level cumulative/deduplicated provider
totals, while AgentPProf sums bounded per-LLM input, output, and cache
components. The difference is documented rather than treated as a failed
conservation check.

## Automatic annotation

The product-generated trace was split into 42 deterministic one-session
standard workspaces. The fixed Step 0077 instruction was used verbatim with
`codex-cli 0.145.0` and `gpt-5.6-sol`. A real one-session preflight preceded
three isolated workers over the remaining sessions.

| Check | Result |
| --- | ---: |
| Batches completed | 42 / 42 |
| Backend failures or reruns | 0 |
| Aggregate-aware revision passes | 0 |
| Final semantic annotations | 1,737 |
| Mandatory session/prompt scopes covered | 1,294 / 1,294 |
| Semantic depth | 2--4 |
| Advisory warnings | 72 |
| Structured advisory issue intervals | 70 |

Every batch passed AgentPProf validation immediately after its first backend
call. Each backend could edit only `annotation.json`; the orchestrator verified
that `trace.jsonl` and `stacks.folded` were unchanged and that no extra
workspace file appeared.

The warnings identify one-pass quality boundaries: coarse spans, flat fan-out,
one unary refinement, singleton fragmentation, and near-name candidates. They
do not indicate missing mandatory annotations, invalid interval nesting, or
resource loss. Per the fixed protocol, they were recorded without an
aggregate-aware cleanup pass.

## Final profiles

| Check | `operation-count.pb.gz` | `token-width.pb.gz` |
| --- | ---: | ---: |
| Exact total mass | 3,509 | 1,380,863,014 |
| Expected total mass | 3,509 | 1,380,863,014 |
| Unique stacks | 3,236 | 5,620 |
| Semantic depth | 2--4 | 2--4 |
| `go tool pprof -top` | loads; total 3,509 | loads; total 1,380,863,014 |

Coverage, parent structure, annotation nesting, and both conservation checks
pass.

## Descriptive findings

The resource distributions are broad rather than dominated by one semantic
path. The largest token path, `refine paper > align evaluation`, contains
23,959,384 tokens, or 1.735% of total token mass. The largest count path,
`refine paper > translate paper`, contains 48 tools, or 1.368% of all tool
operations.

Most token mass remains at mandatory depth two (70.363%), while optional
refinements account for 29.637% at depths three and four. Operation mass is
more deeply resolved: 43.859% lies at depths three and four. The deepest
token-heavy paths distinguish ablation inspection, tag-alignment inspection,
and profiling-cost inspection beneath a shared evidence-audit hierarchy.

Optional semantic-name reuse is low under independent per-record first
passes: 18 of 353 distinct optional names recur across workspace records
(5.099%).
This is observed vocabulary fragmentation under the fixed protocol; the run
does not establish that independent batching caused it, and it is not a
tag-accuracy result. Claude sessions contribute 99.286% of token mass and
93.445% of operation mass, so agent-level comparisons are not balanced.

The three longest-horizon sessions have different dominant paths: evaluation
alignment, evidence inspection, and merge/conflict resolution. Their variation
shows that the profiles preserve distinct long-session responsibility
structures, but no causal or quality claim follows from three examples.

Full coarse-path tables and distributions are in `aggregate-summary.md`.

## Annotation cost

| Measure | Result |
| --- | ---: |
| Summed backend wall time | 7,740.107 s (129.002 min) |
| Reconstructed three-worker critical path plus preflight | 2,674.314 s (44.572 min) |
| Summed validation wall time | 0.211 s |
| Reported input tokens | 15,231,328 |
| Reported cached input tokens | 13,112,320 |
| Derived noncached input tokens | 2,119,008 |
| Reported output tokens | 311,097 |
| Reported reasoning-output tokens | 107,830 |

Reported input averages 362,651 tokens per record, 13.254x the Step 0077
27,362-token reference. Derived noncached input averages 50,453 tokens per
record, 1.844x that per-session reference, but Step 0077 did not retain the same cache
split, so this is not a strictly like-for-like comparison. The largest
record dominates the increase with 3,899 nodes and 2,788,383 reported input
tokens. Complete per-batch measurements are in `cost-record.md` and
`annotation-pass/run-records.jsonl`.

The 42 frozen records contain 31 distinct native `source_session` strings.
Therefore, these averages are per record/batch, not estimates from 42
statistically independent runs.

## Validity and research disposition

```text
phase 1 frozen population: valid
phase 2 repository-native workspace adapter: implemented and tested
phase 2 complete workspace: valid
phase 3 fixed one-pass annotation: complete; 42/42 batches valid
phase 4 operation profile: valid; exact mass conserved; stock pprof loads
phase 4 token profile: valid; exact mass conserved; stock pprof loads
```

The run provides supporting evidence for product feasibility, real-history
resource attribution, long-session structure, and the measured cost of
automatic semantic annotation. It does not establish tag correctness,
good-versus-bad correspondence, or superiority over debugging tools. The
conservation result validates the adapter-to-pprof path rather than providing
an independent reimplementation check of raw-session parsing. Tool ancestry is
inferred from nearest same-prompt LLM timestamps, and the workspace retains
tool status rather than full tool output as `result_preview`; those choices can
limit drill-down fidelity without affecting mass.

The author-fixed thesis remains exactly: **“Agent observability needs profiling,
not only debugging.”** This run supports that story but does not replace its
four fixed research questions.

The paper-level decision should be to retain this result as supporting
real-history feasibility and profiling-cost evidence, subject to the
independent result review. Do not use the low optional-name reuse rate as a
negative accuracy conclusion, and do not elevate descriptive top paths into
causal claims. The next decisive experiment remains a controlled evaluation
of correctness and problem correspondence rather than another annotation
cleanup pass.

## Deliverables

- `frozen-population.json` and `frozen-sessions/`: retained frozen population;
- `workspace/`: final standard trace, annotation, and derived folded stacks;
- `operation-count.pb.gz` and `token-width.pb.gz`: final standard profiles;
- `aggregate-summary.md`: aggregate semantic results;
- `cost-record.md`: complete automatic-annotation cost;
- `annotation-pass/`: deterministic batch workspaces, validations, and raw
  execution records;
- `execution-log.md`: implementation and phase-by-phase commands;
- `independent-result-review.md`: separate read-only validity review.

The earlier `phase2-direct-ingestion-*.pb.gz` files remain diagnostics from the
pre-continuation gap analysis and are not final annotated results.
