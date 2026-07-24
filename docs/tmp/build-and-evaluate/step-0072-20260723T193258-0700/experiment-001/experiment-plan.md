# RQ2 Experiment Plan — Does the Current AgentProf View Add Diagnostic Information?

**Plan status:** APPROVED AFTER TWO INDEPENDENT REVIEW ROUNDS  
**Research question:** RQ2 — Does profiler output correspond to real problems?  
**One tested hypothesis:** H72-RQ2  
**Candidate:** local diagnostic score with the current fixed source-only
Agent+Evidence group score as an exact-tie refinement

## 1. Scientific question

The paper already shows that an AgentProf group score has higher standard MAP
than matched raw-action grouping on three complete public workloads. That
comparison does not isolate the most important systems claim: whether a
cross-run operation profile adds information after a debugger or benchmark
localizer has already assigned each operation a local score.

This experiment therefore asks:

> Holding trajectories, target labels, local diagnostic signals, and all
> source-only operation paths fixed, does the current AgentProf operation view
> improve standard trajectory-level MAP when it may refine only exact ties in
> the local diagnostic score?

The candidate cannot reorder two operations whose local diagnostic scores
differ. It can only distinguish operations that the local signal treats as
equal.

## 2. Hypothesis

On the complete AgentProcessBench, HINTBench, and TraceElephant populations
already used by RQ2, lexicographic ranking by

\[
(\text{local diagnostic score},\ \text{current AgentProf group score})
\]

will have higher workload MAP than:

1. the local diagnostic score alone; and
2. the same local diagnostic score refined by information-matched raw-action
   plus source-evidence grouping.

The current AgentProf group score alone is reported as the incumbent component
ablation, not as a third main baseline. The primary paper-level result is the
three-workload portfolio, not success on one chosen benchmark. Point estimates
and paired intervals will be reported per workload.

## 3. Why this experiment is necessary

- It directly tests the paper thesis that profiling complements rather than
  merely renames debugging evidence.
- It uses the latest fixed source-only paths from Step 0071 rather than the
  historical recurrence grouping. These RQ2 paths are benchmark-specific
  source-only adapters, not an untouched evaluation of the CodeTrace A2 Agent
  backend.
- It changes no benchmark, target, localizer, cutoff, model output, or
  operation annotation.
- It uses standard per-query average precision and workload MAP; it introduces
  no custom primary metric.

## 4. Complete public workloads

| Workload | Complete population | Operations | Target-bearing queries | Local signal |
|---|---:|---:|---:|---|
| AgentProcessBench | 1,000 trajectories | 8,509 | 614 | released per-operation risk units |
| HINTBench | 536 test trajectories | 12,877 | 400 | fixed released/reproduced localizer hit |
| TraceElephant | 220 traces | 5,960 | 220 | fixed released/reproduced localizer hit |

The run must consume every listed trajectory and operation. No smoke subset may
be reported as a result.

## 5. Fixed candidate and baselines

### Candidate: Local + AgentProf

1. Use the fixed `source_preserving_agent` paths from
   `.agentsight/experiments/rq2-canonical-tags-v2-current/`.
2. Aggregate the unchanged local signal over those paths using the same
   benchmark-specific group scoring already used in Step 0071:
   - arithmetic mean risk units for AgentProcessBench;
   - Wilson lower support over every path prefix, taking the maximum prefix
     support for HINTBench and TraceElephant.
3. Rank operations lexicographically by `(local, agentprof_group)`.

### Baseline B1: Local only

Rank by `(local,)`.

### Baseline B2: Local + raw action + identical source evidence

Replace only the candidate's semantic-operation prefix with the historical
raw-action identity. Append the exact same source-kind, source-call/tool, and
outcome suffix used by `source_preserving_agent`, then apply the identical
benchmark-specific aggregation and maximum-prefix rule. Use the same local
score and refine only exact ties with this information-matched group score.
Thus any difference between candidate and B2 is attributable to the semantic
operation prefix, not to source evidence retained by only one side.

### Component ablation: AgentProf only

Rank by the current AgentProf group score alone. This reproduces the current
Step 0071 RQ2 MAP values within numerical tolerance.

These are the only two main baselines plus one component ablation. Native trace
trees, session grouping, and recurrence remain contextual results already
available in Step 0071; they are not needed to answer this mechanism question.

### Method provenance and adaptive scope

This is an adaptive mechanism experiment on three previously observed
populations. The local-first rule was first evaluated on these workloads in
Step 0037. The current paths were subsequently fixed in Step 0071:

- AgentProcessBench and TraceElephant paths are reproducible from their
  benchmark-aware source-only helper programs;
- HINTBench paths are fixed source-only annotations over the retained packets;
- none of these three results constitutes untouched validation of a general
  online LLM annotator;
- the separate CodeTrace A2 result in RQ3 was produced by independent Codex
  Agent batches and root validation.

The admissible RQ2 claim is therefore that the fixed source-only AgentProf view
adds ranking information to the fixed local signal on these complete
populations. It is not a claim of untouched cross-dataset generalization or of
one universal LLM backend.

## 6. Target-blind construction boundary

The following objects are fixed before correctness labels are opened:

- operation IDs and sequence membership;
- current fixed source-only AgentProf paths;
- local diagnostic signals;
- raw-action group identities;
- candidate and baseline rank-key definitions.

The rank-key constructor accepts only `local`, `agentprof_group`, and
`raw_action_group` scores. It must not accept target labels, target operation
IDs, benchmark answers, or correctness fields. Labels are opened only by the
scorer after all score vectors exist.

Changing an operation mark, canonical name, aggregation rule, or
rank-key definition after scoring invalidates the experiment and requires a
new plan.

## 7. Metric and inference

### Primary metric

For every target-bearing trajectory:

1. compute non-interpolated average precision with
   `sklearn.metrics.average_precision_score`;
2. take the arithmetic mean over all target-bearing trajectories in that
   workload to obtain MAP.

AP and MAP are standard information-retrieval metrics. No token-weighted,
budget-specific, top-k, or custom metric is a paper-level outcome.
AP follows Robertson's standard ranked-retrieval definition
(`robertson2008ap`, SIGIR 2008), already verified in the paper bibliography.
All zero-positive trajectories are loaded and counted for complete population
coverage, but they are excluded from MAP because average precision is undefined
when a query has no relevant item.

### Uncertainty

Use 10,000 paired bootstrap resamples of per-query AP differences:

- preserve the existing family/task cluster structure for AgentProcessBench;
- preserve environment strata and resample complete trajectories for
  HINTBench;
- preserve benchmark cell strata and resample complete trajectories for
  TraceElephant;
- fixed seed `20260723`.

Report point difference and the percentile 95% interval for candidate minus
each baseline. An interval is evidence strength, not a gate requiring zero
objections.

## 8. Real preflight

The preflight must use real retained artifacts and exactly one target-bearing
query from each workload. It may verify only:

- full operation-ID alignment between fixed paths and benchmark projections;
- rank construction cannot read target fields;
- strict local ordering is preserved;
- equal rank keys remain tied;
- AgentProf-only MAP reproduces Step 0071 for the selected queries.

The preflight is not a scientific result.

## 9. Authoritative inputs and operation join

| Workload | Benchmark/local-signal root | Fixed path root |
|---|---|---|
| AgentProcessBench | `docs/visexp/out/agentprocessbench-rq2/full` | `.agentsight/experiments/rq2-canonical-tags-v2-current/agentprocess/results` |
| HINTBench | `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full` | `.agentsight/experiments/rq2-canonical-tags-v2-current/hint/results` |
| TraceElephant | `.agentsight/experiments/traceelephant-rq2-v1` | `.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results` |

Join only on the replay-stable `operation_id`. The full run must observe an
exact one-to-one join with no missing or duplicate operation IDs:

- AgentProcessBench: 8,509;
- HINTBench: 12,877;
- TraceElephant: 5,960;
- union: 27,346.

The fixed path input is each root's `fixed-groups.jsonl`. The corresponding
benchmark root supplies local signals, historical raw-action identities, query
IDs, strata/clusters, and labels only at scoring time.

## 10. Full execution

Proposed implementation:

`script/rq2_current_agent_local_first.py`

Proposed outputs:

`.agentsight/experiments/rq2-current-agent-local-first-v1/{preflight,full}/`

Each output directory contains only ordinary analysis artifacts:

- `summary.json`
- `per-query.jsonl`
- `bootstrap-deltas.json` for the full run
- `report.md`

The experiment report under this step records the exact command, population
counts, duration, and result interpretation. Git state, hashes, seals,
attestations, manifests, or finalizers are not scientific conditions.

### Exact preflight command

```bash
python3 script/rq2_current_agent_local_first.py preflight \
  --agentprocess-root docs/visexp/out/agentprocessbench-rq2/full \
  --agentprocess-groups .agentsight/experiments/rq2-canonical-tags-v2-current/agentprocess/results \
  --hint-root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
  --hint-groups .agentsight/experiments/rq2-canonical-tags-v2-current/hint/results \
  --trace-root .agentsight/experiments/traceelephant-rq2-v1 \
  --trace-groups .agentsight/experiments/rq2-canonical-tags-v2-current/trace/results \
  --out .agentsight/experiments/rq2-current-agent-local-first-v1/preflight
```

### Exact full command

```bash
python3 script/rq2_current_agent_local_first.py full \
  --agentprocess-root docs/visexp/out/agentprocessbench-rq2/full \
  --agentprocess-groups .agentsight/experiments/rq2-canonical-tags-v2-current/agentprocess/results \
  --hint-root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
  --hint-groups .agentsight/experiments/rq2-canonical-tags-v2-current/hint/results \
  --trace-root .agentsight/experiments/traceelephant-rq2-v1 \
  --trace-groups .agentsight/experiments/rq2-canonical-tags-v2-current/trace/results \
  --bootstraps 10000 \
  --seed 20260723 \
  --out .agentsight/experiments/rq2-current-agent-local-first-v1/full
```

## 11. Interpretation policy

- **Strong support:** candidate point MAP exceeds both main baselines on all
  three workloads, with positive paired intervals against local-only and
  information-matched local+raw on at least two workloads.
- **Partial support:** candidate improves point MAP across the portfolio but
  one or more workload intervals include zero.
- **Contradiction:** candidate is lower than local-only or local+raw on most
  workloads, or a paired interval is wholly negative.

Regardless of outcome, the result answers only this tested mechanism inside
RQ2. It does not modify the paper thesis or the four fixed RQs.

## 12. Paper consequence if validated

During the WRITE gate:

- replace the weaker RQ2 table with the current matched local-first MAP matrix;
- state that AgentProf refines exact local-score ties and does not replace the
  local diagnostic signal;
- retain the existing complete-population and target-coverage disclosures;
- do not modify title, abstract, introduction, motivation, contributions,
  thesis, section structure, or conclusion in BUILD_AND_EVALUATE.
