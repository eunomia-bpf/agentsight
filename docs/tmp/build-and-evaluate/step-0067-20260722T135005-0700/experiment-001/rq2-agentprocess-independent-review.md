# Independent result review: AgentProcessBench method matrix

Timestamp: 2026-07-22T16:58:52-07:00
Reviewer role: independent result reviewer
Scope: AgentProcessBench only; no TraceElephant or HINTBench result is used in
this verdict.

## Verdict

- **run status:** valid
- **tested hypothesis:** inconclusive at the workload level: supported against
  recurrence and for the A1 source-preservation component, but contradicted by
  the strongest native-tree comparison on AgentProcessBench
- **research value:** supporting
- **paper impact:** additional RQ2 evidence and a mechanism/workload boundary,
  not a direct thesis challenge
- **next paper decision:** retain the complete AgentProcessBench row and state
  that source preservation materially improves automatic-Agent grouping, while
  native-tree folding remains stronger on this benchmark. Do not claim that A1
  universally dominates native structure, every family, or every query.

The run is complete and numerically reproducible. I found no coverage, mass,
metric, target-leakage, or A1-construction defect that invalidates it. The
scientific outcome is nevertheless mixed: A1 is better than A0 and N1, but N0
has higher MAP than A1.

## Evidence reviewed

I reviewed and cross-checked:

- `method-matrix-plan.md`;
- `script/rq2_agent_segmentation_eval.py`, including packet expansion, N0/N1
  construction, A0/A1 construction, the group/target boundary, group-mean
  scoring, and per-query AP;
- `script/rq2_standard_localization_metrics.py`, particularly the established
  AgentProcessBench per-query MAP and family-stratified task-cluster bootstrap;
- all 12 source-only packet files and all 12 annotation files under
  `.agentsight/experiments/rq2-a0-v1/full/agentprocess/`;
- `script/annotate_rq2_agentprocess_source_only.py`;
- the authoritative AgentProcessBench root
  `docs/visexp/out/agentprocessbench-rq2/full`, including group assignments,
  labels, reports, and profile-accounting results;
- every artifact under
  `.agentsight/experiments/rq2-a0-v1/full/agentprocess/results`, including
  fixed groups, source operations, per-query rows, commands, pprof profiles,
  and summaries.

I did not invoke the experiment scorer to obtain the verdict. I independently
rebuilt group scores from the authoritative per-operation `risk_units`, then
called `sklearn.metrics.average_precision_score` per target-bearing trajectory.

## Completion, coverage, and mass

The source and result populations agree exactly:

| Check | Independent result |
|---|---:|
| packet files / annotation files | 12 / 12 |
| source sessions | 1,000 |
| source operations | 8,509 |
| sparse A0 marks | 4,654 |
| fixed-group rows | 8,509 |
| authoritative label rows | 8,509 |
| mapped positive operations | 2,710 |
| total queries / target-bearing queries | 1,000 / 614 |
| task clusters | 200: 50 in each of four families |
| input `risk_units` | 290,601,555,244 |
| source-operation rows / unit mass | 8,509 / 8,509 |

Packet IDs, annotation-expanded IDs, authoritative signal IDs, fixed-group
IDs, and source-operation IDs are identical sets. Every annotation begins at
its session's first operation, marks are strictly ordered, and expansion
covers each operation exactly once.

I opened each product profile independently with `go tool pprof -raw` rather
than trusting only the JSON status:

| Method | Raw sample rows | Raw operation mass | Unique evidence IDs | Unique stacks | Path depths |
|---|---:|---:|---:|---:|---|
| N0 native tree | 8,509 | 8,509 | 8,509 | 459 | 8,509 at depth 6 |
| N1 recurrence | 8,509 | 8,509 | 8,509 | 29 | 8,509 at depth 2 |
| A0 automatic Agent | 8,509 | 8,509 | 8,509 | 115 | 7,086 at depth 3; 1,423 at depth 4 |
| A1 source-preserving Agent | 8,509 | 8,509 | 8,509 | 317 | 7,086 at depth 5; 1,423 at depth 6 |

Thus every method ranks the same operation population with exact unit-mass
conservation. Differences cannot be explained by missing operations or dropped
profiles.

## Metric recomputation

For each method I independently performed the following computation:

1. group all 8,509 operations by the method's complete fixed path;
2. assign each group the arithmetic mean of its members' authoritative
   `risk_units`;
3. use `human_label == -1` as the relevant-operation label;
4. compute non-interpolated `sklearn.metrics.average_precision_score` within
   each trajectory containing at least one relevant operation;
5. take the arithmetic mean over the same 614 target-bearing trajectories.

The independently recomputed value for every one of the 614 by 4 stored
per-query cells is byte-for-number identical to `per-query.jsonl`: maximum
absolute difference is `0.0`. The recomputed MAP values also differ from
`summary.json` by `0.0`.

| Method | Independently recomputed MAP |
|---|---:|
| N0 native tree | **0.7889194040** |
| N1 recurrence | 0.5125845328 |
| A0 automatic Agent | 0.7295813658 |
| A1 source-preserving Agent | 0.7725053134 |

### Historical AgentProf reproduction

I separately rebuilt the historical groups as
`(family, groups.semantic)` from the authoritative AgentProcessBench root. The
recomputed historical MAP is exactly `0.788919404004148`, with absolute error
`0.0` relative to the scorer's registered historical value.

On this workload, N0 and historical AgentProf are more than MAP-equivalent:
they induce 459 groups, their per-operation group-mean scores have maximum
absolute difference `0.0`, and all 614 per-query AP values are identical.
This is an important workload property. The source-native AgentProcessBench
projection already carries phase, intent, action, tool target, and repeat
structure sufficient to reproduce its historical semantic partition. N0 is
therefore a strong and unusually information-rich baseline here, not a weak
flat or session control.

The older authoritative report's `0.587655` macro profile AP is a different
earlier aggregation and must not be substituted for the current standard
per-target-bearing-query MAP of `0.788919`.

## Paired uncertainty

The result directory did not contain paired intervals for the four-method
matrix, so I recomputed them from the independently verified per-query AP
values. I used the existing AgentProcessBench uncertainty structure from
`rq2_standard_localization_metrics.py`: 10,000 paired draws, seed `20260716`,
stratification by the four families, resampling all 50 task clusters per family
with replacement, and nearest-rank 95% percentile intervals. Trajectories with
no positive operation remain excluded from AP; their task clusters remain in
the resampling universe.

| Paired effect | Mean MAP delta | 95% task-cluster interval | Query W/T/L |
|---|---:|---:|---:|
| A1 − A0 | **+0.042924** | **[+0.028668, +0.057886]** | 193 / 371 / 50 |
| A1 − N0 | **−0.016414** | **[−0.030479, −0.001937]** | 101 / 304 / 209 |
| A1 − N1 | **+0.259921** | **[+0.232082, +0.286965]** | 470 / 80 / 64 |
| A0 − N0 | −0.059338 | [−0.076432, −0.042267] | 70 / 271 / 273 |
| A0 − N1 | +0.216997 | [+0.187918, +0.245447] | 436 / 89 / 89 |
| N0 − N1 | +0.276335 | [+0.251489, +0.301304] | 487 / 75 / 52 |

The A1-over-A0 improvement is a real average effect under the benchmark's
paired task-cluster uncertainty: none of 10,000 overall draws was nonpositive.
It should not be described as universal query-level improvement: 371 of 614
queries tie exactly and 50 favor A0. A1 also clearly beats N1, but it does not
beat N0; the A1-minus-N0 interval is entirely negative.

## A1 construction and target independence

A1 is exactly the pre-existing A0 grouping plus two visible source frames. I
independently reconstructed this relation for all 8,509 operations:

```text
A0 = task_family -> automatic semantic path
A1 = A0 -> source_kind -> source_call/tool
```

There are zero mismatches for the A0 prefix, `source_kind`, or source-call
suffix. The A0 and A1 operation-mark files are byte-identical, with the same
SHA-256:

```text
c8e9eee7019bc42fa0590134e0e1a6f22407975ae55c8f78b19cd8952986d78f
```

Their commands use the same 8,509-row source operation file and the same marks.
The only substantive stack change is:

```text
A0: project,operation
A1: project,operation,source_kind,tool
```

The fixed scoring path uses the same suffix derived directly from the packet's
`native_path`: `native[-3]` and `native[-2]`, with the documented fallback to
`native[-4]` when the call frame is `none`. This exactly explains the depth
shift from A0's 3/4 to A1's 5/6 and the increase from 115 to 317 unique stacks.

The packet source summaries contain only:

```text
action, intent, message_index, phase, query_index, repeat_state, target
```

Here `target` is the source-visible tool target such as `mkdir`, not the
benchmark's human mistake label. Packets and annotations contain no
`human_label`, `risk_units`, localizer score, judge output, or existing group.
The scorer constructs N0/N1/A0/A1 and writes `fixed-groups.jsonl` before it
opens `group-assignments.jsonl` and `labels.jsonl`. The fixed file itself has no
label or local-signal field. Therefore A1 is target-independent in both its
definition and its realized 8,509 assignments.

A1 was added after A0 exposed a product-contract mismatch, so it is a post-A0
source-preservation correction rather than a prospectively blind new method.
That fact does not invalidate the measured component effect, because the
transformation is exact and target-independent, but it argues for presenting
the result as supporting mechanism evidence rather than as a preregistered
headline win.

## Family heterogeneity

The overall effect hides meaningful variation:

| Family | Target queries | N0 MAP | N1 MAP | A0 MAP | A1 MAP | A1 − A0 | A1 − N0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BFCL | 184 | 0.643040 | 0.451394 | 0.519076 | 0.625391 | **+0.106314** | −0.017649 |
| GAIA-dev | 183 | 0.887424 | 0.570730 | 0.859987 | 0.878088 | +0.018100 | −0.009336 |
| HotpotQA | 104 | 0.920147 | 0.506891 | 0.887107 | 0.900225 | +0.013118 | −0.019921 |
| Tau2 | 143 | 0.755128 | 0.521050 | 0.718994 | 0.733796 | +0.014803 | −0.021332 |

Family-specific task-cluster intervals for A1 − A0 are:

- BFCL: `[+0.063812, +0.148790]`;
- GAIA-dev: `[+0.008070, +0.027413]`;
- HotpotQA: `[−0.010638, +0.039759]`;
- Tau2: `[+0.005525, +0.025299]`.

Thus the overall A1 gain is not merely one anomalous query, and three families
have positive 95% intervals. It is nevertheless highly uneven: BFCL supplies
the largest effect, while HotpotQA has only 5 A1 wins, 97 ties, and 2 losses and
its interval crosses zero.

Every family mean favors N0 over A1. The family-specific A1 − N0 intervals are
`[−0.057443, +0.022951]` for BFCL, `[−0.028378, +0.010317]` for GAIA-dev,
`[−0.029513, −0.009869]` for HotpotQA, and
`[−0.039940, −0.002504]` for Tau2. HotpotQA and Tau2 show a clear N0 advantage;
BFCL and GAIA-dev are individually inconclusive even though their means favor
N0.

## Scientific interpretation

The valid AgentProcessBench result supports three bounded conclusions:

1. Keeping source-kind and source-call evidence below the same automatic
   semantic path materially improves localization relative to semantic paths
   alone. Because A1 and A0 have identical marks, this is a clean component
   result rather than an annotation-quality confound.
2. Both automatic variants outperform the recurrence-only constructor on this
   benchmark, with positive paired intervals.
3. The source-native hierarchy remains the strongest matrix method here and
   exactly reproduces the historical AgentProf ranking. The automatic method
   has not demonstrated universal superiority over available source structure.

The third result is a workload/mechanism boundary, not a reason to discard the
paper thesis or RQ2. AgentProcessBench exposes unusually rich source-native
semantic fields. The appropriate paper statement is that automatic semantics
remain useful when source evidence is retained, while already-semantic native
projections can match or exceed the automatic grouping. Other workloads must
determine whether that boundary generalizes.

## Required claim discipline

The following claims are supported:

- “On AgentProcessBench, source-preserving automatic grouping improves MAP over
  semantic-only A0 by 0.0429.”
- “A1 substantially outperforms recurrence-only N1 on AgentProcessBench.”
- “The benefit is heterogeneous and largest on BFCL.”

The following claims are not supported by this result:

- “A1 outperforms native-tree folding on AgentProcessBench.”
- “Adding source leaves improves every family or every query.”
- “Automatic semantic grouping universally dominates native hierarchy.”
- “This single benchmark completes or answers the entire paper-level RQ2.”

No rerun is required for AgentProcessBench. The next valid research action is
to preserve this mixed row, complete the same registered matrix on HINTBench
and TraceElephant, and synthesize the three workloads without erasing their
heterogeneity.
