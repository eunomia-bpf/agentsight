# Independent Plan Review 001

**Timestamp:** 2026-07-23T23:58:00-07:00  
**Plan:** `experiment-plan.md`  
**Verdict:** **REVISE**

## Scope reviewed

I reviewed the complete experiment plan, Step 0077 entry, complete
`docs/user-instruction.md`, the fixed RQ1/RQ4 definitions and current evidence
in `docs/idea-story.md` and `docs/evaluation.md`, and the implemented
annotation-workspace path in:

- `agentpprof/src/annotation_workspace.rs`;
- the `--annotation-file` path in `agentpprof/src/main.rs`;
- `agentpprof/tests/annotation_workspace_cli.rs`;
- `agentpprof/README.md`; and
- `docs/design/visexp/agentpprof-annotation-workspace.md`.

I also checked the provenance and current contents of both retained case-study
workspaces. This is a plan review only. I did not edit the plan, implementation,
paper, skills, or Git state.

## Overall assessment

The proposed feedback loop is small, user-directed, and worth running:

```text
generate -> diagnose aggregate -> reread implicated context
-> revise annotation -> regenerate
```

It uses two complete real populations, preserves the existing three-file
workspace and pprof-only product boundary, treats a subagent as an automatic
backend, keeps depth unconstrained, and records token/time cost. The selected
first-pass comparison is also the right mechanism ablation; another list of
weak baselines is unnecessary.

The current plan is not yet scientifically interpretable or executable,
however. The blocking problems are narrow:

1. the Git iteration-0 artifact is not the same automatic backend's first
   pass;
2. the full-pass automatic cost comparator is not actually run or recoverable
   from the retained artifacts;
3. “more useful” and convergence are selected by the revising backend without
   a fixed decision rule; and
4. the current CLI does not expose several pieces of the issue packet that the
   procedure assumes.

These are repairable without adding a frontend, another backend abstraction,
another workload, or another paper metric.

## What is already correct

### Research and user constraints

- Both populations are real and complete for the adopted cases: all three
  repeated Git-deployment executions and all 440 AgentReward trajectories /
  125 mixed-outcome tasks / 338 pairs.
- Outcome and human-stage labels are excluded from annotation-time inputs.
- The backend edits only `annotation.json`; the CLI owns derived paths, folded
  stacks, and pprof.
- The plan does not prescribe depth or optimize depth itself.
- The existing CLI rejects tags longer than three words. The backend
  instruction still needs to enforce the semantic “verb, optional object,
  optional qualifier” preference because the CLI cannot mechanically determine
  whether the first word is a meaningful verb.
- Warnings are advisory. The plan correctly rejects “zero warnings,” fewer
  singletons, or greater depth as sufficient success conditions.
- The only user-facing artifact remains `.pb`/`.pb.gz`; the existing offline
  renderer is used only for paper inspection.
- Standard B-cubed/boundary F1 and MAP remain in their RQ3/RQ2 experiments;
  this case experiment does not replace them with a new aggregate score.

### Current implementation

The implemented workspace already:

- validates `tag/parent/next` regions, complete source-root/prompt coverage,
  nesting, and the one-to-three-word maximum;
- computes variable-depth paths;
- conserves the selected additive width;
- emits source session, prompt, kind, and evidence-ID labels;
- retains LLM/tool/effect evidence leaves below semantic operations;
- reports semantic-tag, cross-session-tag, singleton-tag, and minimum/maximum
  depth counts;
- emits nonblocking unary, coarse-span, flat-fanout, fragmentation, and uneven-
  depth warnings; and
- atomically rewrites the derived trace/folded files and emits standard pprof.

The integration tests cover variable depth, exact mass, source-leaf stacks,
atomic failure, coarse-span warnings, cross-session reuse, and the three-word
limit. The experiment should reuse this path rather than create another
annotator or visualization system.

## Exact must-fix items

### Must-fix 1 — Make iteration 0 a real same-backend comparison

The plan calls the retained Git workspace “the current one-pass automatic
annotation” and compares it with a later pass by “the same backend” (lines
59–66). That provenance is not true for the focused Git artifact. The original
workspace was introduced in Step 0067 Experiment 002 as a **manual root-Agent
annotation**, and the later A3 record explicitly classifies the four
main-Agent revisions as manual product-case evidence. AgentReward, by contrast,
was produced by automatic Codex subagent workers.

Before execution, the plan must do one of the following:

1. **Preferred:** name one fixed automatic Agent backend and instruction, run a
   fresh outcome-blind full first pass on each fixed population, and use those
   outputs as iteration 0 before applying the local-revision loop; or
2. describe the retained workspaces honestly as mixed-provenance starting
   artifacts and remove every “same backend's first pass” and automatic
   first-pass comparison claim.

Because the experiment also targets RQ4 automatic-construction cost, option 1
is the scientifically useful repair. The fixed backend record must identify
the Agent/model surface available to the experiment, its exact instruction,
the source-only payload format, concurrency, failure/retry treatment, and the
fact that no manual/root edit is inserted into `annotation.json`.

This is not a request for another backend. It is the minimum needed to make the
declared within-backend ablation true.

### Must-fix 2 — Measure the actual automatic cost boundary

Lines 141–159 request iteration-0 backend time and tokens, but step 2 merely
replays an already-existing annotation through the CLI. Historical artifacts
do not contain the adopted backend's inference time or token usage, as Step
0075 already established. Replaying iteration 0 therefore cannot produce the
claimed automatic first-pass cost.

The revised plan must predeclare and report, for both complete cases:

- fresh first-pass automatic-backend wall time, calls, failures/retries,
  serialized logical input/output tokens under one named tokenizer, and
  parallelism;
- the same fields for every local-revision pass;
- **cumulative** local-revision cost, not only the cheapest individual pass;
- deterministic diagnosis/materialization time and peak RSS separately; and
- the ratio of cumulative local-revision input/time to an actual fresh
  same-backend full pass.

If provider billing tokens are unavailable, the plan's logical-token rule is
sound. It must name the tokenizer and serialization before the run. A
full-trace character count alone can support only an input-volume statement;
it cannot support “materially less time than a fresh full annotation pass.”

### Must-fix 3 — Predeclare convergence and outcome interpretation

“Repeat while a concrete high-value issue remains” and “select the final
iteration from the case evidence” (lines 105–110) allow the same backend to
revise, judge, and choose among its own outputs after seeing all aggregate
diagnostics. This makes the before/after usefulness claim circular and gives
the full run no terminal completion rule.

Keep the user's no-fixed-depth and no-fixed-iteration-count requirements, but
define the minimal semantic stopping rule:

> Process diagnostics in a fixed recorded order and stop at the first complete
> pass in which the backend, after reading every implicated local context,
> accepts no annotation change. The final result is that converged output, not
> the best-looking iteration chosen retrospectively.

Also predeclare the integrated outcome matrix:

- useful aggregate evidence improves **and** cumulative local cost is below a
  fresh full pass: supports the tested mechanism and its incremental-cost
  prediction;
- aggregate evidence improves but cost does not: supports the RQ1 mechanism
  only and contradicts the cost prediction;
- cost is lower but the aggregate does not improve: dependency/practicality
  result, not evidence that revision is useful;
- neither improves, or evidence is erased: contradicts the tested mechanism;
- the two cases disagree: mixed, case-bounded result.

The independent result reviewer—not the revising backend—must compare
iteration 0 and the converged output against the two fixed user questions,
verify every claimed path from source evidence, and audit that reductions in
singletons/warnings did not come from indiscriminate merging. This is a
read-only scientific assessment, not a new human annotation condition.

### Must-fix 4 — Close the gap between planned issue packets and current CLI

The current CLI summary contains global counts and warning strings. It does
**not** currently emit:

- each tag's source-session membership;
- candidate nearby/near-synonymous names;
- the exclusive end of each warned local interval; or
- the weighted semantic-depth distribution requested at line 120.

For example, the fragmentation warning exposes only up to five tag names, and
unary/coarse/fan-out warnings expose a start node but no bounded context packet.
Thus plan steps 3–4 cannot yet be executed from the promised mechanical output
without an unspecified one-off analysis path.

Before real preflight, the plan must specify one minimal path:

- extend the existing CLI diagnostic JSON with the needed membership and
  bounded-interval fields, deriving the depth histogram from the same current
  paths; or
- explicitly define a deterministic read-only derivation from
  `trace.jsonl`/`annotation.json` and record its command and output.

The first option better matches the Step 0077 user request. It needs only
focused tests that the reported session memberships and interval boundaries
match the annotations. Do not add a schema framework, backend registry,
custom renderer, UI, or separate product artifact.

## RQ and paper-value classification

The experiment should declare **RQ1 supporting mechanism evidence** as its
primary role and **RQ4 measured cost** as its coupled secondary endpoint. This
is one integrated run because the cost belongs to the exact revision mechanism
whose aggregate effect is being evaluated; it should not be split into two
experiment directories.

The Git question and SSH responsibility were selected after the prior profile
was inspected. The AgentReward case is also a retained, previously analyzed
population. Therefore even a positive result is a strong product case and
mechanism ablation, not an independent population-level RQ1 attribution test,
not automatic boundary accuracy, and not automatic-backend generalization.
State that scope in the plan. This preserves the fixed ambitious RQ1/RQ4
questions without pretending that one local-revision experiment answers them
entirely.

## Baseline assessment

No extra main baseline is required.

- Iteration 0 from the same fixed automatic backend is the correct alternative
  mechanism: one-pass annotation without aggregate feedback.
- A fresh full pass by that same backend is the necessary RQ4 cost comparator.
- Mass/source coverage and warning counts are controls or diagnostics, not
  baselines.
- Source-native, recurrence, and fixed-chain comparisons already answer other
  RQ1/RQ2/RQ3 questions. Adding them here would not isolate the local-revision
  mechanism.

The must-fix is to make the two declared comparisons real, not to increase the
baseline count.

## Executability checklist after revision

The revised plan will be runnable when it names:

1. the fixed backend instruction/model surface and outcome-blind payload;
2. the authoritative first-pass and local-revision invocation workflow;
3. the tokenizer and time/call/failure accounting method;
4. the exact issue-packet derivation supported by the current CLI or its
   minimal extension;
5. a real preflight using one complete session through that exact path;
6. the convergence rule and complete two-population terminal condition; and
7. the raw artifact paths for every iteration and cost record.

## Scope-creep audit

The following are explicitly **not** required and should not be added:

- a frontend, dashboard, annotation editor, or product renderer;
- a second annotation workspace or output format;
- a backend plugin framework or model registry;
- a fixed or minimum semantic depth;
- forced elimination of singleton, unary, coarse-span, or uneven-depth
  warnings;
- a hand-labeled/manual condition;
- another benchmark or a broad baseline matrix;
- a new custom paper metric replacing B-cubed, boundary F1, MAP, or AP;
- outcome labels or human stages in annotation-time packets;
- Git hashes, frozen manifests, attestations, or other experiment-control
  infrastructure; or
- repeated paper/skill/Git changes during this experiment.

## Final verdict

**REVISE.**

The idea, populations, product boundary, and minimal feedback mechanism are
approved. Execution is blocked only until the four items above make the
same-backend comparison truthful, the RQ4 cost complete, the convergence
decision non-circular, and the planned local issue packets actually
executable. No wider experiment or additional baseline is necessary.
