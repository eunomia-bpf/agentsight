# Experiment 001 plan: aggregate-aware local revision on two real cases

Timestamp: 2026-07-23T23:36:16-07:00
Status: PROPOSED
Research questions: RQ1 — resource attribution; RQ4 — construction cost

## Scientific question

> Holding the source traces and automatic backend fixed, does exposing the
> generated aggregate's structural problems and rereading only implicated
> local contexts produce more reusable and useful operation profiles than the
> same backend's first pass, without losing evidence or requiring another
> full-corpus read?

This experiment tests one primary mechanism hypothesis:

> Relative to the same automatic backend's fixed first pass,
> aggregate-diagnosed local revision improves independently audited
> answerability of the two fixed case-study questions without erasing
> source-supported semantic distinctions.

Source coverage, evidence preservation, stock-pprof readability, and mass
conservation are validity checks. Tag reuse, singleton fraction, warning
counts, unique stacks, and depth distribution are explanatory measurements.
Cumulative revision time and tokens relative to a measured fresh full pass are
the coupled RQ4 secondary endpoint, not part of a composite success score.

It does not test automatic boundary accuracy against hidden human stages; that
is a separate RQ3 experiment after the mechanism and prompts are fixed.

## Fixed populations and user questions

### Case A: long-horizon Git deployment

Use the existing three complete `git-multibranch` sessions and accepted
workspace under
`docs/visexp/out/codex-agent-long-horizon-v1/annotation-workspace-git-v1`.
The fixed user question is:

> Across independent attempts at the same deployment task, where did the
> agents spend their work and tokens, and which shared responsibility explains
> repeated high-cost failure?

The retained paper result identifies an SSH-related responsibility, but that
result, prior figure, narrative, expected path name, and numerical answer are
hidden from the automatic annotation and revision backends. Revisions may not
select a different population or discard an inconvenient operation.

### Case B: AgentReward mixed outcomes

Use all 440 real traces, 125 mixed-outcome tasks, and 338 success/failure
pairs already adopted by `agentreward-diff-pprof-v1`. The fixed user question
is:

> Across many real success/failure pairs for the same tasks, which operation
> paths accumulate on failed executions and which paths characterize
> successful completion?

The same success/failure labels and pairing are retained. Revisions may
canonicalize operation names and repair local hierarchy, but may not use the
outcome label to decide a boundary or name.

## Compared conditions

1. **Iteration 0:** a fresh complete pass by the fixed automatic backend,
   generated without aggregate diagnostics.
2. **Iteration N:** the final aggregate-aware annotation after repeated
   diagnose/reread/revise/regenerate cycles.

Both conditions use the same source nodes, metrics, view, current AgentPProf
binary, and deterministic pprof writer. There is no manual annotation
condition and no new algorithmic backend.

The retained Git workspace is mixed-provenance product evidence and is not
misrepresented as the automatic iteration-0 baseline. The retained
AgentReward workspaces are prior automatic evidence, but are likewise not used
as the within-backend baseline or cost measurement.

## Fixed automatic backend

Both the full first pass and every local revision use a fresh Codex subagent
with model `gpt-5.6-sol`, high reasoning effort, and no forked conversation
history. The exact instruction is retained in
`automatic-backend-instruction.md`. The backend receives only paths inside its
assigned experiment workspace and may edit only that workspace's
`annotation.json`.

The first-pass payload contains the source-only `trace.jsonl`, an empty
`annotation.json`, the one-to-three-word tag rule, and the fixed user profiling
question without its expected answer. During the measured first-pass call, the
same automatic backend creates and names every mandatory session/prompt
annotation as well as any optional refinements. No retained semantic seed or
unmeasured root/prompt naming step is used.
AgentReward is processed in the existing complete source batches with at most
two backend workers active concurrently. The same batch assignment,
instruction, model surface, and concurrency are used for the fresh baseline
and any whole-population comparison.

The backend may use ordinary read-only shell queries to inspect its assigned
trace. A failed invocation is retried once with the identical payload and is
recorded as a failure plus retry; a second failure leaves that batch incomplete
and prevents a complete-run claim. The root agent never inserts, renames,
removes, or reparents an annotation.

## CLI diagnostics

Every regeneration reports:

- number of distinct optional semantic tags;
- number reused across at least two source sessions;
- number appearing in only one source session;
- minimum and maximum semantic depth among weighted leaves;
- weighted sample mass at each semantic depth;
- every optional tag's occurrence count and source-session membership;
- lexically near-name candidates for Agent inspection; and
- structured issue records with kind, tag, session, start node, exclusive end
  node, child counts, and covered tool-call count;
- existing unary-refinement, flat-fanout, and coarse-span warnings.

Warnings are candidate reread locations, not correctness verdicts. A singleton
may be a genuine task-specific operation; uneven depth may be appropriate.
The automatic backend must read the implicated local trace context before
deciding whether to merge, rename, refine, or leave the annotation unchanged.

## Iterative procedure

Before the first backend call, record the exact visible-field audit. A Git
backend request may contain only source IDs and ordering, source parent/kind,
session/prompt text, LLM/tool content, additive metrics, current paths, seed
annotations, and mechanical diagnostics. An AgentReward request uses the same
allowlist over the unsigned union population and additionally excludes task
pair IDs, pair side, success/failure/outcome/reward fields, expert labels,
prior signed profiles, human stages, prior case narratives/figures, named
expected focal paths, and answerability-rubric expected answers.

For each case:

1. Materialize a fresh source-only workspace from the fixed external source.
   Start with an empty annotation file; do not copy any semantic annotation
   from retained cases.
2. Run the fixed automatic backend over the complete population without
   aggregate diagnostics. Merge its outcome-blind batch annotations, run the
   CLI, and freeze this result as iteration 0. Capture the complete backend
   usage record, CLI JSON diagnostics, pprof mass, folded stacks, and resource
   measurements.
3. Produce a compact issue list from the mechanical diagnostics. For name
   reuse, show tag, source-session membership, and nearby names. For structural
   warnings, show source node IDs and only the covered local interval.
4. Give one automatic Agent backend the current annotation, issue list, and
   implicated local trace contexts. Do not give it outcome labels, human stage
   labels, or a target depth.
5. The backend records each accepted or rejected issue in a Markdown iteration
   report and edits only `annotation.json`.
6. Rerun the same CLI. Assert that the source node set, total operations,
   token mass, and source-evidence labels are unchanged.
7. Process all issues in deterministic order by
   `(kind, tag, session_id, start_node_id)`. The backend must record an
   evidence-grounded `change` or `keep` decision for every issued item.
8. Start another complete diagnostic pass after regeneration. Stop at the first
   pass in which every issue was considered and the backend accepts no
   annotation change. There is no target depth or arbitrary iteration cap. If
   an exact annotation state repeats, stop and report non-convergence; do not
   select a favorable earlier state.
9. Freeze the terminal annotation. Only then open the Git expected-answer
   record and AgentReward pair/outcome files, construct the final pprof/diff,
   and apply the independent answerability comparison.
10. Retain every iteration's annotation, diagnostics, actual backend usage,
    and Markdown report. The terminal state, never a retrospectively
    best-looking iteration, is the candidate.

## Measurements

### Product-facing aggregate measurements

- optional semantic tag count;
- cross-session reused tag count and fraction;
- singleton tag count and fraction;
- unique root-to-leaf stack count;
- weighted semantic-depth distribution;
- warning categories and counts;
- exact operation/token mass under the paper's focal operation paths;
- source-session coverage and source-evidence preservation.

These measurements explain the aggregate but are not combined into a custom
score.

### User-problem evidence

Before revision begins, freeze this answerability rubric. A read-only
independent reviewer receives iteration identities in masked order and uses
only each profile plus source drilldown.

For the Git case, the reviewer must:

- identify the highest-cost responsibility shared across the repeated runs;
- give its rank, contributing sessions, direct and cumulative operation/token
  mass, and supporting evidence IDs; and
- determine from those source records whether it reached the user's requested
  terminal condition.

For AgentReward, after both annotations are frozen and outcome weights are
revealed, the reviewer must:

- identify the strongest failed-side and successful-side paths in the complete
  signed 338-pair profile;
- give their signed mass/share and contributing sessions; and
- reproduce each claim from the corresponding evidence IDs.

Each required answer field is classified as complete/incomplete,
numerically reproducible/not reproducible, and source-supported/unsupported.
This is an answerability checklist, not a new scalar paper metric. A
source-unsupported merge, erased distinction required by the question, or
outcome-derived operation name vetoes a positive usefulness judgment.

A revised case improves only if it has no regression on any required field or
dimension and at least one strict improvement. Any tradeoff is mixed for that
case; identical field matrices are no change. The masked reviewer returns the
complete field matrix before iteration identities are unmasked, and the root
applies this relation mechanically.

### Cost

Record separately for the fresh complete pass and every revision:

- backend wall time;
- backend calls, failures/retries, and concurrency;
- number of trace nodes and local intervals presented;
- serialized input characters and tokenizer-counted input tokens;
- tokenizer-counted output tokens;
- number of annotations added, removed, renamed, or reparented;
- CLI diagnosis and deterministic pprof regeneration wall time;
- peak RSS for CLI regeneration;
- final stock-pprof replay time.

For Codex subagents, retain the rollout session ID and compute actual
`input_tokens`, `cached_input_tokens`, `output_tokens`, and
`reasoning_output_tokens` as the final cumulative counter minus the cumulative
counter immediately before that invocation in the same rollout. For a new
rollout whose first event already describes the first completed invocation,
the documented zero origin is used; an absent or ambiguous origin is reported
rather than guessed. Sum per-invocation deltas across every call, including
failed calls and retries, while keeping cached input, total input, output, and
reasoning output separate. Separately tokenize the exact serialized
source-visible request and response with `tiktoken 0.12.0` `o200k_base`; label
those as logical payload tokens rather than provider billing.

Report cumulative values across all revision passes. Compare cumulative
revision wall time, actual tokens, and logical payload tokens against the
measured fresh same-backend complete pass. “Lower cost” means strictly lower
cumulative value for the named measure; no arbitrary percentage threshold is
introduced. Record the start before the first call and the completion after the
last call for each complete condition under fixed concurrency; cumulative
revision wall time is the sum of complete revision-pass elapsed times. CLI
diagnosis/materialization time and RSS remain separate from backend inference.

## Validity and interpretation

- Outcome labels are used only after AgentReward annotations are fixed, when
  constructing the signed difference.
- Existing human stage labels are never visible during case revision.
- The same deterministic AgentPProf binary constructs every compared profile.
- Every final profile must open in stock pprof and conserve all additive mass.
- Fewer singleton names alone is not success: indiscriminate merging that
  erases meaningful distinctions is a failure.
- A deeper profile alone is not success: depth must correspond to a useful
  task decomposition and retain evidence leaves.
- The result may support usefulness and cost claims for these two complete
  real populations. It may not claim population-wide boundary accuracy; RQ3
  supplies that test.

## Preflight

Before the complete run, execute the exact fixed backend, issue packet,
annotation edit, CLI regeneration, invariant checks, and cost capture on one
complete real Git session. The structured diagnostics must name the correct
source session and exclusive interval endpoints, and their depth-mass sum must
equal the selected pprof sample mass. The preflight output contributes no paper
number and is discarded before the full first pass.

## Predeclared interpretation

- Both cases improve on the masked answerability rubric with no validity veto:
  the primary mechanism hypothesis is supported for these two cases.
- Neither improves, or either becomes source-invalid: the primary hypothesis
  is contradicted.
- One improves and one does not: the result is mixed and case-bounded.
- Masked review cannot distinguish them or required artifacts are incomplete:
  the primary result is inconclusive.
- Cumulative local revision cost is below the measured fresh full pass: the
  RQ4 incremental-cost prediction is supported for that cost measure.
- Cumulative cost equals or exceeds the fresh pass: the RQ4 prediction is
  contradicted for that measure even if answerability improves.
- Lower cost without improved answerability is a practicality/input-volume
  observation, not evidence that the revision mechanism is useful.

## Expected outputs

- two copied iterative workspaces, one per case;
- one `.pb.gz` per retained iteration and width;
- CLI diagnostic JSON and resource measurements per iteration;
- automatic-backend Markdown report per iteration;
- final paper-quality pprof figures and case narratives;
- one full result report and one independent result review.
