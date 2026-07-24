# Independent Result Review — Recursive Operation Segmentation v4

**Review status:** complete
**Run status:** **VALID** for the registered complete-population comparison
**Tested hypothesis:** **CONTRADICTED**
**Research value:** **SUPPORTING** negative mechanism evidence
**Paper impact:** **mechanism/workload boundary**, not a thesis challenge
**Next paper decision:** do not adopt recursive-operation-segmentation-v4, do
not use its profiles or timing as the paper's current positive backend result,
and retain the result in research history without changing RQ3 or the thesis.

## Review method

This review used the approved Step 0066 plan, the Step 0074 resume report, the
complete inference and scoring artifacts, the recursive adapter source, the 405
per-session inference caches, and stock `go tool pprof`. It did not rely on the
root interpretation.

The scoring metrics and bootstrap were independently reimplemented from the
raw operation and pair rows. Prediction-to-score, prediction-to-mark, cache
identity, model usage, long-horizon selection, profile hashes, and profile mass
were independently reconstructed. The experiment script was read to audit its
information boundary and execution semantics, but its scoring functions were
not called for recomputation.

## Completion and artifact integrity

The raw artifacts form one complete, internally consistent run:

- 405 unique sessions, 17,148 source-native turns, and 20,866 operations;
- framework counts of 213 OpenHands, 28 SWE-agent, 93 Terminus2, and 71
  mini-SWE-agent sessions;
- 20,461 within-session adjacent pairs, exactly `20,866 - 405`;
- 2,948 official contiguous stages and 251 task-name clusters;
- 20,866 unique prediction keys and 20,866 unique score-row keys with exact
  key-set equality;
- every scored candidate occurrence and candidate path exactly equals the
  corresponding prediction's `task_occurrence_instance` and `semantic_stack`;
- all operations sharing a source-native turn have the same predicted path;
- independently regenerating a mark whenever a prediction path changes yields
  exactly the stored 1,068 marks, in the same order;
- all 752 operation-name IDs equal the registered
  `op-<sha256(label)[:24]>` mapping, with no collision;
- the 405 session caches are nonempty, complete, and unique, and all carry the
  same v4 algorithm, model SHA-256, and inference-contract SHA-256
  `73dd70e987d6f573bfaab2c13e4c91f8294cdc4a5ccd176e2d2c970ad27ae853`.

The cache reconstruction also exactly reproduces:

| Inference quantity | Recomputed value |
|---|---:|
| Root calls | 405 |
| Recursive calls | 1,585 |
| Model STOP calls | 638 |
| Raw SPLIT calls | 947 |
| Effective splits | 922 |
| Degenerate-current split stops | 25 |
| Canonical leaves / marks | 1,068 |
| Sessions with more than one emitted segment | 73 |
| Sessions with exactly one emitted segment | 332 |
| Semantic-depth counts | 1: 492; 2: 353; 3: 186; 4: 33; 5: 4 |

The resumed execution reused 256 complete cache files written on July 22 and
created the remaining 149 on July 23, exactly matching the resume report.
Every session cache predates the completed inference summary; the inference
summary predates the scored operation rows by approximately 91 seconds.

## Source-only and scoring-order audit

The available evidence supports the declared source-only execution boundary:

1. `infer` reconstructs target-visible source material and writes predictions,
   marks, pprof files, and a complete inference summary without accepting an
   official manifest, recurrence assignment, causal baseline, or score.
2. The separate `score` command requires the completed predictions and
   inference summary before it accepts and opens the verified manifest and
   baseline rows.
3. The 405 caches use one fixed v4 inference contract and model identity. Their
   recorded model responses, predictions, and marks contain no official-stage,
   task-cluster, recurrence, or causal-score field.
4. File ordering is consistent with all predictions, marks, and profiles being
   completed before the score artifacts were produced.
5. The task source is recorded as 287 raw first-user messages and 118 public
   OpenHands recall queries, matching the registered fallback.

This provenance is strong enough for the negative result. Two limitations
should remain explicit:

- `official_manifest_opened=false` and `official_stages_opened=false` are
  literal summary fields written by the inference code, not an external access
  monitor.
- The score command checks completion and key coverage but does not bind the
  inference summary to a cryptographic hash of `predictions.jsonl`. Exact raw
  prediction/score equality and temporal ordering mitigate this for the
  preserved run, but the flags alone should not be described as tamper-proof
  provenance.

No score-driven inference modification is evident. The tokenizer correction
described in the resume report is execution-only in full mode: the removed
value is used only for preflight session selection, while full mode processes
all sessions in sorted order. The cache contract remained identical.

## Independent metric reconstruction

Ordinary B-cubed was recomputed directly. For each operation, precision is its
candidate/reference intersection divided by candidate-cluster size, recall is
the same intersection divided by official-stage size, and corpus P/R are
unweighted means over all operations. Reported F1 is the harmonic mean of
those corpus means. Boundary metrics were recomputed from the raw pair
booleans.

### Complete population

| Method | Pred./official groups | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Native turn | 17,148 / 2,948 | .983154 | .221199 | .361145 | .141910 | .934330 | .246396 |
| Native tree | 15,813 / 2,948 | .974547 | .248903 | .396530 | .151090 | .915454 | .259373 |
| Multi-resolution recurrence | 6,018 / 2,948 | .782026 | .575029 | .662740 | .192945 | .425875 | .265571 |
| Recursive v4 candidate | 863 / 2,948 | .242532 | .945422 | .386034 | .218703 | .057019 | .090455 |
| Causal Qwen control | 5,972 / 2,948 | .735681 | .581999 | .649878 | .183990 | .423909 | .256606 |

The candidate boundary confusion counts are `TP=145`, `FP=518`, `FN=2,398`,
and `TN=17,400`. Its high B-cubed recall and very low precision, only 863
predicted groups for 2,948 official stages, and 5.7% boundary recall all point
to severe undersegmentation. This is not an ambiguous precision/recall
tradeoff: recurrence has much higher B-cubed F1 and nearly five times the
candidate's boundary recall.

### Per-framework candidate comparison

| Framework | Candidate B³ F1 | Recurrence B³ F1 | Candidate boundary F1 | Recurrence boundary F1 |
|---|---:|---:|---:|---:|
| OpenHands | .370054 | .676295 | .047393 | .274646 |
| SWE-agent | .326488 | .708893 | .000000 | .297362 |
| Terminus2 | .388566 | .605471 | .140871 | .247162 |
| mini-SWE-agent | .478301 | .691523 | .142558 | .276013 |

The candidate loses both metrics in every framework. In SWE-agent it predicts
only 34 groups for 28 sessions and recovers zero exact official boundaries.
There is no favorable framework cell that could support a narrower positive
claim.

## Independent task-cluster bootstrap

The review independently computed per-operation B-cubed precision and recall
contributions, grouped them by the 251 sorted task names, and used
`random.Random(20260720).choices(tasks, k=251)` for 10,000 paired draws. Each
sampled task contributes all of its sessions and operations with sampling
multiplicity. Corpus P/R and their harmonic-mean F1 are recomputed on each
draw.

| Comparison | Mean candidate delta | 95% percentile interval | Positive draws |
|---|---:|---:|---:|
| Candidate − recurrence | −.276707 | [−.306589, −.245664] | 0 / 10,000 |
| Candidate − causal Qwen | −.263632 | [−.293000, −.233085] | 0 / 10,000 |

All independently generated draws match the two stored files to a maximum
absolute difference below `7.3e-16`. The report and summary therefore state
the correct registered comparison and decision.

The bootstrap seed is inherited from
`rq3_source_native_task_progress_boundary_eval.py` (`20260720`), not the
inference seed (`20260722`). The score summary and result report omit this
bootstrap seed. This is a reproducibility-reporting omission, not a numerical
or decision error.

## Main-baseline fairness

Multi-resolution recurrence is a valid main baseline for the registered
question. It covers the same 20,866 operations, uses the same official
reference only at scoring time, and engages its intended visible-action
recurrence mechanism. There is no missing row, interface failure, or unfair
candidate disadvantage in scoring. The candidate also loses to the reused
causal-Qwen control, so the result is not an artifact of recurrence alone.

Native turn and native tree behave as fragmentation controls, not headline
competitors. Their strong precision and weak recall are consistent with their
registered roles. The result does not depend on counting either weak control
as a candidate loss.

## Degeneracy and semantic-usefulness audit

The candidate technically avoids the two absolute previous endpoint failures:
it neither creates one leaf per turn nor emits exactly one segment for every
session. That weak statement is insufficient for the registered hypothesis:

- 332 of 405 sessions (82.0%) still emit exactly one segment;
- only 73 sessions contain any internal split;
- 1,068 emitted leaves collapse to 863 distinct session-scoped path groups;
- only 37 leaves reach semantic depth four or greater;
- only four leaves in the entire population reach semantic depth five.

The fixed 41-session long-horizon collection contains 5,750 operations and is
reconstructed exactly by descending operation count with session-ID tie-break.
It has 301 emitted leaves, but 25 of its 41 sessions remain one segment. Its
semantic depth distribution is 80 depth-one, 124 depth-two, 86 depth-three,
and 11 depth-four leaves; **no long-horizon path reaches five semantic frames**.
The plan explicitly says the collection-level semantic-usefulness contract
fails if either fixed collection has no path reaching five semantic frames
including the root. The long-horizon collection therefore fails that
predeclared condition.

No separate source-drilldown review answering all four fixed user questions is
present in the supplied Step 0074 artifacts. Because the primary registered
comparison is already conclusively negative, this missing positive semantic
review does not make the negative result incomplete or invalid; it prevents
any attempt to salvage a semantic-usefulness or case-study claim from the
profiles.

## Pprof mass and readability

Both product-control artifacts are valid standard pprof files:

| Collection | Bytes | SHA-256 | Stock-pprof mass |
|---|---:|---|---:|
| Complete 405 sessions | 745,697 | `60ebeeebc11f49ab2834ca19a1cb70e513a74c7d80cf562a6cebe7bb4ed0087f` | 20,866 |
| Long-horizon 41 sessions | 141,469 | `0d6a9abae94ee67a64364faa005f249730f67690fe3a473749db223961f00e3d` | 5,750 |

The hashes and sizes match `inference-summary.json`. Both files load
successfully with stock `go tool pprof`, conserve exactly one operation sample
per input operation, contain no AgentPProf warning, and retain reversible
`source_session` and `call_id` labels.

Default `pprof -top` is dominated by leaf tool frames, as expected from the
registered full stack. A stock operation-focused tree with metadata/tool
frames hidden is mechanically readable and exposes some genuine parent-child
paths—for example, hidden-secret recovery splits into core-dump analysis and
deleted-source recovery, and Doom cross-compilation contains a VMJS repair
child. This verifies serialization and drilldown capability.

It does not establish collection-level semantic usefulness. Most sessions are
unsplit, the long-horizon collection fails the registered depth condition, and
no completed aggregate source-grounded review is supplied. These profiles must
not become paper figures or replace the accepted current backend merely
because stock pprof can render them.

## RQ4 timing and model-usage audit

The 405 raw session caches independently sum to:

- 1,990 model calls: 405 root plus 1,585 recursive;
- 6,761,329 prompt tokens;
- 39,357 completion tokens;
- 6,800,686 total server-reported tokens.

These exactly match `inference-summary.json`. They correspond to averages of
3,398 prompt tokens, 19.8 completion tokens, and 3,417 total tokens per call,
or 16,792 total tokens per session. The per-call recorded elapsed times sum to
3,070.96 seconds across the two execution periods.

The reported direct wall components are arithmetically consistent:

| Component | Seconds | Minutes |
|---|---:|---:|
| Source adaptation | 503.422 | 8.39 |
| Annotation/cache loop | 1,240.609 | 20.68 |
| Two-profile materialization | 12.438 | .21 |
| Component subtotal | 1,756.469 | 29.27 |
| Total resumed wall time | 1,762.629 | 29.38 |
| Unattributed setup/reporting overhead | 6.160 | .10 |

The usage totals are valid full logical usage because they aggregate the
stored server responses for all 405 sessions. The 1,762.6-second wall time is
**not** a clean from-empty-cache end-to-end annotation latency: 256 sessions
were cache hits and only 149 were inferred during the resumed execution.
Conversely, the 3,070.96-second sum of stored request latencies spans the
original and resumed periods and is not one directly observed end-to-end wall
run. Any RQ4 report must distinguish:

1. full logical call/token usage;
2. resumed wall time with 256 cache hits;
3. source-adaptation time; and
4. pprof replay/materialization time.

The run provides useful development-cost diagnostics, but it does not
authorize a fresh full-population wall-time claim for automatic annotation.
Because v4 is not adopted, these numbers also cannot be presented as the
current AgentPProf product cost or the paper's positive RQ4 result.

## Deviations and process observations

The plan header says it was approved after eleven serial review rounds. The
research-experiment-design skill permits one plan review plus at most two
follow-ups. That historical review expansion violates the workflow's
minimality rule, although it does not change the raw predictions, metrics, or
negative verdict.

The final output location also differs from the old plan's Step 0066 expected
report location because execution resumed under Step 0074. This is documented
and has no scientific effect. The product boundary remains intact: each
AgentPProf invocation emits one `.pb.gz`, and no custom renderer is used.

## Verdict and exact admissible interpretation

The registered positive hypothesis requires a useful variable-depth partition,
avoidance of collapse/fragmentation, superiority to recurrence with a wholly
positive paired interval, and passing both fixed semantic-review collections.
The candidate instead has a wholly negative interval, loses both standard
metrics in every framework, leaves 82% of sessions unsplit, and fails the
long-horizon depth contract. The correct verdict is therefore
**CONTRADICTED**, not mixed or inconclusive.

The exact admissible interpretation is:

> On all 405 CodeTrace trajectories, the fixed source-only recursive Qwen
> v4 backend completed and emitted mass-conserving, stock-pprof-readable
> profiles, but it substantially undersegmented operation structure. It
> produced 863 predicted groups for 2,948 official stages, ordinary B-cubed
> F1 of .386 versus .663 for multi-resolution recurrence, and exact-boundary
> F1 of .090 versus .266. The paired task-cluster B-cubed interval was
> [−.307, −.246], and 332 of 405 sessions remained one segment. Thus recursive
> single-split prompting plus this STOP policy does not provide an accurate
> automatic operation constructor on this population. This is a boundary of
> the tested backend, not evidence against operation stacks, RQ3, or the thesis
> that agent observability needs profiling, not only debugging.

No paper-story, thesis, RQ, or contribution change follows. The v4 backend
should remain non-adopted research history. Its negative profile should not be
promoted as a paper case, and its resumed timing should not replace the
paper's current RQ4 cost evidence.
