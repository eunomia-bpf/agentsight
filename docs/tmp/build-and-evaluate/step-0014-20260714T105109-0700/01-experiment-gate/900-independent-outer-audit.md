# Independent Outer Audit — Step 0014 EXPERIMENT Gate

## Audit metadata

- **Audited:** `2026-07-14`
- **Step:** `0014`, EXPERIMENT gate
- **Experiment loop:** `loop-001-rq2-r337-reuse-audit`
- **Audit role:** independent gate-exit audit using the
  `research-experiment-design` completion and evidence boundaries
- **Audit action:** read-only inspection and recomputation; this Markdown is
  the only repository file written
- **Verdict:** **PASS**
- **Must-fix findings:** **none**
- **Authorized next outer state:** **WRITE_GATE**

Step 0014 completed the promised small reuse experiment. It did not create a
new benchmark, model, label set, metric, cutoff, partition, resample, policy,
human study, or experiment implementation. It reconstructed one existing RQ2
result from four public-data operation sources and correctly classifies the
result as supporting evidence rather than a new independent observation.

## 1. State-machine completion

The required sequence completed in order:

| Phase | Evidence | Audit result |
|---|---|---|
| PROPOSE | `100-proposed-experiment-plan.md` | Complete; one RQ2 hypothesis and one fixed-input reuse audit |
| PLAN REVIEW 1 | `110-plan-review-round-1.md` | Independent BLOCK with three bounded fixes |
| Plan revision | proposed plan updated after round 1 | Only a real preflight, truthful replay topology, and source-lineage check were added |
| PLAN REVIEW 2 | `120-plan-review-round-2.md` | Independent PASS; all three blockers closed without scope expansion |
| PLAN REVIEW 3 | `130-plan-review-round-3.md` | Independent PASS; final scientific and executable review |
| Approval | `140-approved-experiment-plan.md` | Approved for REAL PREFLIGHT |
| REAL PREFLIGHT | `200-real-preflight.md` and raw preflight output | Real R337 command completed; six tasks, 25% target, and all required policies present |
| PREFLIGHT REVIEW | `210-real-preflight-review.md` | Independent PASS for executability only |
| FULL RUN | `300-full-result.md` and R333/R337 replay directories | Both commands reached complete terminal output |
| RESULT REVIEW | `400-independent-result-review.md` | Independent PASS after source-count, leakage, equivalence, median, and paired-result recomputation |
| Loop completion | `500-loop-completion.md` | Valid/supporting result routed to WRITE |

Filesystem timestamps also preserve the serial order: round 1 completed before
the plan revision; rounds 2 and 3 followed the revision; approval preceded the
real preflight; preflight review preceded both full replay commands; and the
independent result review followed the full result. No smoke output was
promoted into the result.

## 2. One RQ and one tested hypothesis

The selected question remains verbatim:

> **RQ2: Does Profiler Output Correspond to Real Problems?**

The loop tests one bounded hypothesis only: at the existing 25% positive-recall
point on the six existing public labeled tasks, the existing
`operation_stack:query_aware` view reaches all tasks with lower median
inspection work and fewer median inspected groups than
`fixed_session:query_aware`, while raw-action and flat remain explicit
counterpoints.

The plan fixes the target, views, ranker, tasks, measurements, and decision rule
before execution. It explicitly prevents this experiment from changing RQ2,
the four-RQ structure, the positive paper hypothesis, the thesis, or the story.
Positive, contradictory, and inconclusive results would have made different
decisions about one secondary RQ2 statement, so the reuse audit is
decision-relevant rather than an activity-only rerun.

## 3. Public scope, existing assets, and absence of new complexity

The full replay uses the four existing operation files derived from these
public sources:

| Task family | Public source identifier | Existing target field(s) used only for scoring |
|---|---|---|
| AgentRewardBench | `McGill-NLP/agent-reward-bench` | `looping`, `side_effect` |
| SATraj-OS | `AI45Research/SATraj-OS` | `safety` |
| AgentNet | `xlangai/AgentNet` | `step_correct`, `step_redundant` |
| OSWorld-Human | `WukLab/osworld-human` | `group_position` |

These sources provide exactly six task slices. Independent result review
reloaded those slices from the operation files and recomputed four datasets,
six tasks, **34,539 task-operation instances**, and **3,699 positive
task-operation instances**. The term `task-operation instances` is retained
because AgentReward and AgentNet rows participate in multiple task-specific
label queries; the total is not presented as a count of unique source rows.

The experiment reused the existing R320/R333 grouping and scoring path and the
existing R337 fixed-target summarizer. The source scripts, four operation
files, and tracked R333/R337 reference outputs all predate Step 0014. No file
under `script/`, `agentpprof/`, `collector/`, or `docs/visexp/` was modified
during the gate. The only new machine artifacts are ordinary replay outputs
under `.agentsight/experiments/rq2-r337-reuse-audit-v1/`.

The gate added no dataset download, generated fixture, agent or model call,
new annotation, learned ranker, new policy, new target, matched-cardinality
construction, interpolation, Pareto aggregate, cross-metric score, statistical
resample, or human dependency. It also did not create a custom replay or audit
script. The existing 10% and 50% rows were emitted by the unchanged R337 path
as context and were not alternative success criteria.

## 4. REAL PREFLIGHT and complete FULL RUN

The preflight ran the actual existing target-extraction path:

```bash
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/preflight-r337
```

Its `run-result.json` reports `R337`, terminal status `ok`, six tasks, six
existing policies, three existing recall targets, and 108 target rows. The
required four policies each have six rows at 25% recall. The preflight report
and its independent review correctly limit this result to executability.

The full run then executed both approved commands to completion:

```bash
python3 script/operation_inspection_frontier_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r333-replay
python3 script/operation_inspection_target_eval.py \
  --out-dir .agentsight/experiments/rq2-r337-reuse-audit-v1/r337-replay
```

R333 completed six tasks and four datasets, producing 144 scored-policy rows,
90 visible-policy rows, 36 grouped views, 810 inspection points, and 252 curve
rows. R337 completed all six tasks, six policies, and all three unchanged
targets. No task, policy, workload, or target stopped at a partial prefix.

The plan truthfully treats this as an equivalence audit rather than claiming
that temporary R333 output is piped into R337. R333 reconstructs the grouping,
visible ranking, and inspection curves from the four operation sources; after
that scientific equivalence passes, R337's fixed R333 input is treated as an
equivalent reconstruction.

## 5. Replay equivalence and label boundary

Direct comparison confirms that every CSV emitted by the fresh replay is
byte-identical to the corresponding existing result:

- R333: `core-policy-scores.csv`, `task-policy-curves.csv`,
  `policy-curve-summary.csv`, `default-vs-baselines.csv`, and
  `curve-win-summary.csv`;
- R337: `inspection-targets.csv`, `policy-target-summary.csv`,
  `task-target-best.csv`, and `default-target-comparisons.csv`.

The selected claim-bearing JSON fields are also identical: R333
`input_policy`, `core_policies`, `work_grids`, `totals`, and `leakage_check`;
and R337 `input_policy`, `default_policy`, `baseline_policies`,
`recall_targets`, and `summary`. Runtime and commit metadata are not used as
scientific evidence.

The source and implementation audit confirms the approved information
boundary. Grouping and visible query-aware ranking use `action`, `environment`,
`phase`, `repeat_signal`, and `status`. The repeat signal is computed from
adjacent action/target signatures; the other visible fields derive from
actions, source metadata, and separate execution or task outcomes. The task
loader converts `looping`, `side_effect`, `safety`, `step_correct`,
`step_redundant`, or `group_position` into `target_positive` only for offline
scoring. Hidden label fields are excluded from visible policies, and the fresh
R333 leakage report has an empty visible/hidden field-name intersection.

This establishes the approved target-blind execution boundary; it does not
promote the fixed task-aware heuristic into a held-out learned-policy claim.

## 6. Exact 25%-recall result

All four required policies reach the existing 25% target on all six tasks:

| Policy | Tasks reached | Median inspection work | Median groups inspected |
|---|---:|---:|---:|
| `operation_stack:query_aware` | 6/6 | **0.2000** | **16.0** |
| `fixed_session:query_aware` | 6/6 | 0.2495 | 50.0 |
| `raw_action_stack:query_aware` | 6/6 | 0.1993 | 13.0 |
| `flat:width` | 6/6 | 1.0000 | 1.0 |

The replayed paired comparisons reproduce the result report exactly:

| Operation stack versus | Work W/T/L | Median work delta | Group W/T/L | Median group delta |
|---|---:|---:|---:|---:|
| fixed session | **4/1/1** | **-0.0731** | **5/0/1** | **-37.5** |
| raw action | 3/1/2 | -0.0230 | 2/0/4 | +9.0 |
| flat | 6/0/0 | -0.8000 | 0/0/6 | +15.0 |

The exact approved support rule therefore passes: operation stack and fixed
session both reach all six tasks, both median inequalities favor operation
stack, the complete paired outcomes are reported, and the raw/flat
counterpoints are retained. Raw action has slightly lower median work and
fewer median groups, while flat obtains one group only by requiring complete
inspection work. The result does not imply universal semantic dominance.

## 7. Scientific interpretation and paper boundary

The correct result classification is:

```text
run status: valid
tested hypothesis: supported
research value: supporting
paper impact: additional bounded RQ2 evidence
next paper decision: WRITE may add one compact six-task, 25%-recall statement with fixed-session, raw-action, and flat context
```

This is a current reconstruction of pre-existing evidence, not a new
independent observation and not the complete answer to RQ2. It supports one
secondary operating-point statement: on these six public labeled tasks at the
existing 25%-recall point, recurring operation stacks reduce fixed-session
fragmentation while retaining lower typical inspection work; they save work
relative to flat, while raw action remains mixed and slightly stronger by the
two medians. It does not authorize a matched-granularity or Pareto proof,
universal superiority, analyst productivity, automatic diagnosis, downstream
intervention, or a new paper story.

`docs/evaluation.md` records the same exact numbers, supporting-only role, raw
and flat counterpoints, raw-artifact paths, and remaining boundary. The current
paper's RQ2 section does not yet contain this R337 statement, so routing to
WRITE is necessary rather than duplicative.

## 8. Paper, story, RQ, submodule, and skill integrity

The author-fixed thesis remains exactly:

> **Agent observability needs profiling, not only debugging.**

The active paper, `docs/idea-story.md`, and `docs/user-instruction.md` all
retain the four fixed RQs: resource attribution, correspondence to real
problems, tag accuracy, and profiling cost. Step 0014 neither rewrote nor
narrowed them.

Filesystem inspection finds no paper, idea-story, user-instruction, canonical
submodule, or shared-skill file newer than the Step 0014 start time
(`2026-07-14T10:51:09-07:00`). In particular:

- `docs/paper/main.tex` and `main.pdf` predate the gate;
- `docs/idea-story.md` and `docs/user-instruction.md` predate the gate;
- every file under the read-only `docs/agentpprof-paper/` canonical submodule
  predates the gate; and
- every file under the shared academic-writing skills directory predates the
  gate.

The only repository file outside the Step 0014 report tree and replay-artifact
directory modified during this experiment was `docs/evaluation.md`, which is
the required experiment-frontier update. The paper, thesis, story, RQs,
canonical submodule, and shared skills therefore stayed within their declared
boundaries.

## Gate-exit decision

**PASS.** PROPOSE, three serial plan reviews, REAL PREFLIGHT and independent
review, complete FULL RUN, independent RESULT REVIEW, evaluation-frontier
update, and experiment-loop completion are all present and scientifically
consistent. The run is valid, the one bounded hypothesis is supported, and the
result is correctly limited to supporting RQ2 evidence.

The next state is **WRITE_GATE**. Its scope should remain one compact RQ2
statement that reports the six-task and existing-25%-recall boundary, the
fixed-session improvement, and the raw-action/flat counterpoints. No thesis,
story, RQ, contribution, method, or additional experiment change is authorized
by this gate.

