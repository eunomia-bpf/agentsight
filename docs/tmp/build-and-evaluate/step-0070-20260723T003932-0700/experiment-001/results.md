# Experiment Result: RQ2 Canonical Operation Identity

## Verdict

**VALID after one independently detected fairness repair.** The final
comparison changes only operation names. All 1,756 sessions, 27,346 operations,
14,238 sparse marks, source-evidence rows, targets, signals, metrics, and
bootstrap units are fixed within each workload.

The one-to-three-word action-first identity improves HINTBench MAP by 0.008;
its paired intervals include zero on AgentProcessBench and TraceElephant. It
reduces 876 open-vocabulary tags to 239
reusable identities without deleting a boundary. The final automatic
Agent+Evidence profile remains above raw action on all three workloads.

## Complete Inputs

| Workload | Sessions | Operations | Marks | Target-bearing queries |
|---|---:|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 4,654 | 614 |
| HINTBench | 536 | 12,877 | 5,887 | 400 |
| TraceElephant | 220 | 5,960 | 3,697 | 220 |
| **Total** | **1,756** | **27,346** | **14,238** | **1,234** |

Every candidate pprof opens through stock `go tool pprof`; operation count,
sample mass, evidence-ID coverage, session order, mark count, mark start, and
semantic depth are preserved. The fixed mapping contains 781 two-word and 95
three-word source-tag mappings and produces 239 distinct canonical identities.
Seventy-five old tags receive the deterministic boundary-preserving head-noun
refinement. The final mapping has zero adjacent complete-path collisions.

## Fairness Failure And Repair

The first AgentProcessBench comparison used the retained Step 0067 current
rows. Independent result review found that those rows had two source-evidence
frames while the candidate produced three by adding `outcome`. The apparent
`+.018` naming effect was therefore invalid.

The repair did not change the candidate, mapping, mark, target, signal, or
metric. It reran the preceding automatic names through the same evaluator and
the same three-frame source suffix. The final score command now mechanically
requires the two `source-operations.jsonl` inputs to be byte-identical; a unit
test covers the rejected mismatch. Under this fair comparison,
AgentProcessBench changes from 0.794635 to 0.790615 and its paired interval
crosses zero.

HINTBench current and candidate likewise use the same source rows and exact
`0.0` for zero-hit Wilson groups. TraceElephant's retained current rows were
already identical to the candidate source rows.

## Primary Result

| Workload | Current names | Canonical names | Canonical minus current | 95% paired cluster interval | Classification |
|---|---:|---:|---:|---:|---|
| AgentProcessBench | 0.794635 | 0.790615 | -0.004020 | [-0.011363, 0.002817] | Inconclusive |
| HINTBench | 0.424437 | 0.432392 | +0.007955 | [0.002436, 0.013734] | Positive |
| TraceElephant | 0.260070 | 0.259313 | -0.000758 | [-0.002273, 0] | Inconclusive |

The metric is standard non-interpolated per-query average precision,
arithmetically averaged as MAP. AgentProcess uses 10,000 family-stratified
task-cluster draws (seed 20260716), HINT uses 100,000
environment-stratified query draws (seed 20260722), and Trace uses 100,000
five-cell-stratified trace draws (seed 20260713).

## Source Evidence And Paper Context

The final canonical Agent+Evidence MAP values are 0.790615, 0.432392, and
0.259313. The matched Agent-only values are 0.734213, 0.281314, and 0.194094.
Keeping source evidence beneath the same marks therefore adds 0.056402
`[0.039368,0.072793]`, 0.151077 `[0.135603,0.166746]`, and 0.065218
`[0.043649,0.088906]`; all three task-cluster intervals exclude zero.

Relative to raw action, the final automatic profiles improve MAP by 0.017,
0.151, and 0.138. Relative to the declared/reference semantic hierarchy, the
canonical results are statistically indistinguishable on all three workloads.
The paper may therefore claim that short reusable names preserve localization
quality while making the cross-run profile readable, with a small positive
HINT effect. It may not claim an AgentProcess naming gain.

## Current Four-RQ Frontier

This step changes only RQ2 operation identity. The other current-algorithm
results were audited rather than rerun:

- **RQ1 / attribution and hierarchy:** Automatic Agent A2 reaches ordinary
  B-cubed F1 0.704 and boundary F1 0.394 on all 405 CodeTraceBench
  trajectories and 20,866 operations, versus 0.663/0.266 for recurrence and
  0.541 B-cubed F1 for raw action.
- **RQ2 / real-problem correspondence:** Final automatic Agent+Evidence MAP is
  0.791/0.432/0.259 across the three complete public workloads. In the
  440-trajectory AgentReward population, the outcome-blind recovery exposure
  has AP 0.634 versus 0.398 expert-looping prevalence.
- **RQ3 / structure and tags:** A2's CodeTraceBench structure result is
  0.704 B-cubed F1 and 0.394 boundary F1; OSWorld label-free recurrence is
  0.786/0.680; task-family and action taggers reach 0.695 and 0.498 macro-F1.
- **RQ4 / cost:** The 27,765-operation public union builds in 1.17 seconds
  median with 464.5 MiB maximum RSS. Direct A2 replay over 20,866 operations
  builds operation and token profiles in 0.61 seconds median with at most
  308.9 MiB observed RSS.

No new benchmark, metric, or RQ was introduced to improve a number.

## Case-Study Artifacts

The current paper renderings are derived from standard pprof and preserve the
variable-depth semantic hierarchy plus source LLM/tool leaves:

- `docs/visexp/out/r221-pprof-renderer-v1/git-multibranch.operations.png`
- `docs/visexp/out/r221-pprof-renderer-v1/git-multibranch.tokens.png`
- `docs/visexp/out/r221-pprof-renderer-v1/git-authentication.tokens.png`
- `docs/visexp/out/r221-pprof-renderer-v1/agentreward-recovery-bad-excess.operations.png`
- `docs/visexp/out/r221-pprof-renderer-v1/agentreward-completion-good-excess.operations.png`

AgentPProf itself continues to emit only `.pb`/`.pb.gz`; the renderer is a
paper/inspection tool that reads profiles through stock `go tool pprof`.

## Interpretation Boundary

This is an adaptive supporting replay over previously observed populations,
not untouched confirmation. The evidence supports reusable operation identity,
real-problem ranking, and source-preserving drilldown. It does not establish
that canonical naming alone improves every workload, that one recursive
constructor dominates every baseline, or that a visible differential path is
causal.
