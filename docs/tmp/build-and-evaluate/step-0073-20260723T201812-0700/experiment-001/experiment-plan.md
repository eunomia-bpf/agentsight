# Experiment 001 Plan — Fixed-Instruction Follow-On Structure Fidelity

**Timestamp:** 2026-07-23T20:18:12-07:00
**Outer gate:** EXPERIMENT
**RQ:** RQ3 — How accurately do automatic backends recover operation
structure?
**Status:** proposed for independent review

## Explicit RQ and tested hypothesis

The experiment receives the fixed paper-level RQ above. It does not change the
RQ.

It tests one hypothesis:

> On the 364 CodeTrace sessions annotated after the initial 41-session product
> collection under the same source-only instruction, the current automatic
> Agent A2 predictions retain higher ordinary operation-level B-cubed F1 than
> the multi-resolution recurrence baseline, with a task-cluster paired 95%
> interval wholly above zero.

The experiment judges only this tested hypothesis. It does not answer every
semantic-name, nested-topology, cross-session-equivalence, user-utility, or
cross-family part of RQ3.

## Fixed population

The population is the complete
`.agentsight/experiments/codex-agent-remaining-v1/packets/manifest.json`
selection:

- 364 sessions;
- 15,116 operations;
- 238 task-name clusters;
- 202 OpenHands, 71 mini-SWE-agent, 65 Terminus2, and 26 SWE-agent sessions.

The initial 41 long-horizon sessions and 5,750 operations are excluded. No
session, framework, task, or result-based filtering is permitted.

## Fixed inputs

- Current A2 assignments:
  `.agentsight/experiments/a2-canonical-v1/score/operation-score-rows.jsonl`.
- Current exact-boundary rows:
  `.agentsight/experiments/a2-canonical-v1/score/pair-score-rows.jsonl`.
- Follow-on session IDs:
  `.agentsight/experiments/codex-agent-remaining-v1/packets/manifest.json`.
- Full-population summary used only for equality/context checks:
  `.agentsight/experiments/a2-canonical-v1/score/summary.json`.

No annotation, canonicalization, recurrence assignment, or official stage is
regenerated. The scorer only filters existing complete rows by the session IDs
fixed above and recomputes metrics.

## Methods

- `candidate`: latest automatic Agent A2 temporal occurrences; current short
  canonical names do not change occurrence membership.
- `multires_recurrence`: strongest adopted non-LLM recurrence baseline.
- `native_tree`: source-native phase/action/raw-action hierarchy.
- `native_turn`: diagnostic fragmentation control.

All methods share exactly the same operations and official stage reference.

## Metrics and inference

Primary metric:

- ordinary unweighted per-operation B-cubed F1.

B-cubed follows Bagga and Baldwin's entity-based partition metric, applied to
operation memberships. Exact adjacent-boundary precision/recall/F1 is the
paper's registered protocol induced from changes in CodeTraceBench's released
human stage IDs; it is not described as an official CodeTraceBench leaderboard
metric.

Secondary metrics:

- B-cubed precision and recall;
- exact adjacent-boundary precision, recall, and F1;
- predicted/official group counts;
- per-framework rows.

Statistical comparison:

- paired 10,000-resample bootstrap over the 238 task-name clusters;
- each draw samples task clusters with replacement and includes every
  follow-on session belonging to the sampled task;
- report the mean A2-minus-recurrence B-cubed F1 delta and percentile 95%
  interval;
- fixed seed `20260723`.

No custom weighted score, token weighting, depth reward, top-k protocol, or
multiple benchmark search enters the primary result.

## Preflight

Before scoring:

1. manifest contains exactly 364 unique sessions and 15,116 operations;
2. operation rows join exactly those 364 sessions and 15,116 operations;
3. pair rows contain exactly
   `15,116 - 364 = 14,752` adjacent pairs;
4. no initial 41-session ID is present;
5. operation sessions have complete method/reference assignments;
6. pair sessions have complete method/reference boundary booleans;
7. operation and pair session sets are identical;
8. framework counts match the declared population.
9. the joined population contains exactly 238 distinct task-name clusters.

Preflight may score one task cluster only to prove execution. Its numbers are
not paper evidence.

## Reproducible execution

The only new scorer is
`script/rq3_fixed_instruction_followon_eval.py`. It accepts no annotation
packet, prompt, model, or tunable scoring parameter.

```bash
python3 script/rq3_fixed_instruction_followon_eval.py preflight \
  --manifest .agentsight/experiments/codex-agent-remaining-v1/packets/manifest.json \
  --excluded-manifest .agentsight/experiments/codex-agent-long-horizon-v1/packets/manifest.json \
  --operation-rows .agentsight/experiments/a2-canonical-v1/score/operation-score-rows.jsonl \
  --pair-rows .agentsight/experiments/a2-canonical-v1/score/pair-score-rows.jsonl \
  --out .agentsight/experiments/rq3-fixed-instruction-followon-v1/preflight

python3 script/rq3_fixed_instruction_followon_eval.py full \
  --manifest .agentsight/experiments/codex-agent-remaining-v1/packets/manifest.json \
  --excluded-manifest .agentsight/experiments/codex-agent-long-horizon-v1/packets/manifest.json \
  --operation-rows .agentsight/experiments/a2-canonical-v1/score/operation-score-rows.jsonl \
  --pair-rows .agentsight/experiments/a2-canonical-v1/score/pair-score-rows.jsonl \
  --bootstrap-resamples 10000 \
  --seed 20260723 \
  --out .agentsight/experiments/rq3-fixed-instruction-followon-v1/full
```

For each bootstrap draw, Python's `random.Random(20260723).choices` samples
exactly 238 task names with replacement from their sorted unique list. A
sampled task contributes all of its follow-on sessions; repeated task draws
repeat all of those rows. The scorer computes candidate and recurrence B-cubed
on the same sampled rows and writes one delta per draw in draw order.

## Full-run outputs

Under
`.agentsight/experiments/rq3-fixed-instruction-followon-v1/full/`:

- `summary.json`;
- `operation-score-rows.jsonl`;
- `pair-score-rows.jsonl`;
- `bootstrap-candidate-minus-recurrence.jsonl`;
- `result-report.md`.

The report must disclose that this is a follow-on subset of an already observed
CodeTrace development family, not an untouched external test family.

## Decision rule

- **Supported:** A2 B-cubed F1 exceeds recurrence and the paired interval lower
  endpoint is above zero.
- **Contradicted:** the paired interval upper endpoint is at or below zero.
- **Inconclusive:** otherwise.

Regardless of outcome, report all methods, all frameworks, oversegmentation,
and the exact scope. A negative or heterogeneous result changes the tested
answer, not the fixed RQ or thesis.

## Result review

An independent reviewer must reconstruct the subset from the manifest and raw
full-population rows without importing the new scorer. It must reproduce:

- population and join counts;
- every aggregate and per-framework metric;
- the paired bootstrap interval and decision from the same declared seed and
  resampling unit, without requiring byte-for-byte equality of every draw;
- decision-rule status;
- exclusion of all initial 41 sessions.

## Paper-facing claim if supported

> Excluding the 41 sessions used for the initial product case, the fixed
> automatic Agent backend remains more faithful than recurrence over the
> complete 364-session population annotated later under the same source-only
> instruction.

The exact metrics and heterogeneity must accompany this sentence. The result
does not establish universal semantic-name accuracy, correct nested topology,
or cross-family generalization.
