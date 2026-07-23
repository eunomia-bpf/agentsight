# Plan review: automatic Agent operation marks

Timestamp: 2026-07-22T14:37:12-07:00
Verdict: approved with the simplifications and scorer correction below

## Scope and scientific value

The complete 405-session CodeTraceBench run directly tests whether automatic
Agent marks recover independently annotated workflow partitions better than the
source-native hierarchy and the strongest adopted non-LLM recurrence
constructor. It is not another prompt probe or a new RQ. The 41-session result
is reused as the fixed product case; the remaining 364 sessions use the same
source-only packets and annotation instructions.

Two non-LLM comparisons are sufficient:

- N0 native-tree folding tests whether the Agent adds value beyond the source
  hierarchy already present.
- N1 multi-resolution recurrence tests the strongest adopted competing
  constructor.

The incomplete recursive Qwen run is not necessary. A0 is already an automatic
Agent backend, and finishing Qwen only to populate another row would add cost
without a distinct paper decision.

## Full-run boundary

The annotation backend receives task text, source-native turn summaries,
operation IDs, and source references. It receives no official stages, scores,
outcomes, or recurrence output. Batches exist only for context capacity. The
root validates coverage, source order, sparse-boundary legality, and supported
name reconciliation. Once all 405 sessions and 20,866 operations are covered,
the automatic output stops changing; only then may the stage scorer read gold.

No repeated inference, stability study, hash protocol, seal, or additional gate
is required.

## Scoring correction

Pprof and the stage scorer intentionally use different identities:

- pprof folds the complete visible `semantic_path`, so the same responsibility
  can aggregate after an Agent leaves and later returns to it, including across
  sessions when occurrence frames are omitted from the function stack;
- the stage scorer assigns a fresh contiguous occurrence identity to every
  sparse mark. Returning to a previous visible path creates a new predicted
  stage occurrence rather than merging two noncontiguous intervals.

The primary metric is ordinary unweighted operation-level B-cubed P/R/F1 over
all 20,866 operations. The secondary metric is exact adjacent-boundary P/R/F1.
Also report predicted group count, the four framework rows, and the existing
251-task paired-cluster interval for A0 minus N1. Do not add token weighting,
depth rewards, span scores, or a custom composite metric. Flat stage labels
test partitions and boundaries; they do not by themselves validate semantic
names, nested topology, cross-session equivalence, or user utility.

## RQ reuse

The same fixed A0 marks support RQ1/RQ3 profile construction and standard stage
scoring without rerunning inference. RQ2 requires one source-only A0 run on each
of its own complete workloads before query targets are opened; CodeTrace marks
cannot substitute for those workloads. RQ4 separates constructor elapsed/model
usage from the common AgentPProf CLI cost and reuses marks when changing the
additive measure.
