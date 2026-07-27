# Task spec: cross-run identity validation (investigate, then measure)

Autonomous agent in /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Deterministic computation only. Deliverables in THIS
directory.

## The gap (round-2 review, concern 1)

B3/boundary score partitions per trajectory; canonicalization preserves
those vectors exactly, so 0.764 cannot validate whether the 783 canonical
IDs merge the RIGHT operations ACROSS sessions (false merges pool
unrelated work; synonym splits fragment aggregation).

## Phase 1: gold availability investigation (fast, decisive)

Determine whether CodeTraceBench's released gold carries any cross-
trajectory identity signal: do the 2,948 human stages have stage TYPE/NAME
labels that recur across trajectories (e.g. reproduce/localize/edit/test),
or only per-trajectory contiguous segmentations? Inspect the released
data the step-0087 pipeline read (packet/scorer inputs under
.agentsight/experiments/ and the archives referenced by step-0071/0075
records). Report exactly what label fields exist, their vocabulary size,
and cross-trajectory recurrence.

## Phase 2A (if stage-type labels exist): pairwise identity scoring

Score the complete annotation+canonicalization pipeline's cross-run
identity on the step-0087 artifacts: for operation pairs from DIFFERENT
trajectories, predicted-same-ID vs gold-same-stage-type. Report standard
pairwise precision/recall/F1, false-merge and false-split counts, the
strongest confusions, and a majority/random baseline. Use every
trajectory (no sampling); document any within-type granularity mismatch
honestly.

## Phase 2B (if no such labels): document impossibility + strongest proxy

State plainly that no public gold defines cross-run identity for these
trajectories; then compute the best available proxy: e.g. agreement
between canonical-ID sharing and gold stage POSITION-type correlates, or
cross-framework name-reuse statistics with examples of the top merged
IDs and their member diversity (for qualitative audit). Do not invent a
bespoke score presented as a standard metric.

## Deliverables

phase1-gold-report.md, and per the branch: identity-results.md with
metrics and baselines (2A) or impossibility-and-proxy.md (2B);
raw JSON; execution-log.md.
