# Reviewer-requested same-model flat-segmentation ablation

Work in `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
First read `AGENTS.md`, the complete `docs/user-instruction.md`,
`docs/idea-story.md`, `docs/evaluation.md`, and the complete
`research-experiment-design` skill. Preserve the exact four fixed RQs and the
thesis **“Agent observability needs profiling, not only debugging.”**

Execute one admitted RQ3 ablation requested by a reviewer. Do not edit
`docs/agentpprof-paper/`, `docs/paper/`, `docs/idea-story.md`, or
`docs/user-instruction.md`. Do not run Git commands. Preserve all concurrent
work. Keep the plan, plan review, code, logs, raw outputs, results, and result
review under this `experiment-001` directory, except for the
`docs/evaluation.md` update required by the experiment-design workflow.

## Scientific question

On the complete 405-trajectory CodeTraceBench population, how much of the
adopted GPT-5.6 result comes from producing a variable-depth hierarchy rather
than a flat contiguous semantic partition?

The reviewer requests two same-model controls:

1. flat segmentation over the complete trajectory;
2. direct generation of the complete multi-level hierarchy without recursive
   refinement.

The existing adopted condition is Step 0087 direct multi-level annotation:
Codex CLI with `gpt-5.6-sol`, one isolated source-only request per trajectory,
followed by the frozen canonicalization and RQ3 scorer. Its reported complete
result is B-cubed F1 0.763539 and exact adjacent-boundary F1 0.479952.

Before spending calls on control 2, audit the frozen Step 0087 instruction,
raw run records, model/configuration, inputs, and result rows. Determine
whether it already exactly implements direct complete-hierarchy generation
without an external STOP/SPLIT controller or iterative mark-refinement
workflow. If it does, reuse its complete population and per-operation/per-pair
rows as control 2 and document the evidence; do not rerun an identical
condition. If it does not, run a fresh same-model direct-hierarchy arm matched
to the main condition in model, input, request budget, isolation, decoding,
retry policy, and scoring, changing only the instruction to return the complete
multi-level hierarchy directly without recursive or iterative refinement.
Never infer equivalence merely from both conditions using one backend request.

## New ablation: same-model flat segmentation

Run a fresh flat annotation arm using:

- the exact 405 Step 0087 source-only trajectory packets, with no stage,
  outcome, score, reward, or target fields visible;
- the same Codex CLI model `gpt-5.6-sol`, reasoning configuration, decoding
  defaults, isolation, one-request-per-trajectory policy, timeout, format retry
  policy, and worker pattern as Step 0087;
- the same sparse-mark format and action-first one-to-three-word naming rules;
- one semantic partition level only: every complete path must contain the
  mandatory session root plus exactly one non-root semantic interval name.
  The root is constant within a trajectory; adjacent spans may change only the
  single flat semantic name. The model must read the complete trajectory and
  choose contiguous responsibility boundaries directly. It must not first
  generate a hierarchy and project it after the fact.

Change only the hierarchy-depth contract needed to create this flat arm.
Reuse the unchanged downstream assembly, canonicalization where applicable,
population, oracle loading order, correctness checks, and scoring definitions.
If exact reuse requires a small adapter, keep it minimal and document it.

## Comparison and outputs

Primary comparisons are the reviewer-requested matched ablations: hierarchy
minus flat, and recursive/refined hierarchy minus direct hierarchy whenever
the audited artifacts contain two genuinely distinct conditions. Use ordinary
operation-level B-cubed F1 and exact adjacent-boundary F1, with 10,000 paired
task-cluster bootstrap resamples and documented seeds. Do not manufacture a
second comparison by assigning two names to the same frozen condition.
Also report precision, recall, group/mark counts, depth distribution, format
failures/retries, model calls, input/output/reasoning tokens, active request
time, and end-to-end wall time.

Before the full run:

1. Write a concise experiment plan and obtain one fresh plan review following
   the skill.
2. Run the smallest real end-to-end preflight on actual Step 0087 packets and
   the actual GPT-5.6 backend. Preflight is operational only, never a paper
   result.
3. If the path is valid, run all 405 trajectories to terminal status with
   resumable raw outputs. Do not interpret a partial prefix.
4. Perform one fresh result review that independently checks completion,
   leakage, mechanism engagement, score reconstruction, paired uncertainty,
   fairness against Step 0087, and paper-claim scope.

Keep negative or mixed results. Do not tune the prompt, depth rule,
canonicalization, scorer, oracle, exclusions, or bootstrap based on observed
scores. A format-only repair may be made within the declared retry policy and
must be recorded. Finish with a self-contained result report and the next
paper decision, but do not edit the paper.
