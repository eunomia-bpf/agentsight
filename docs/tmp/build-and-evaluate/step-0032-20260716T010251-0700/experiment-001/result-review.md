# Independent Result Review: Literal Action Identity

**Reviewed:** 2026-07-16T16:07:05-07:00

**Role:** fresh read-only reviewer with no execution role in this experiment
**Selected paper question:** **RQ3 — How Accurate Are the Tags?**

## Review method

The reviewer read the complete `research-experiment-design` skill, approved
plan, consolidated plan review, and preflight report. It then reconstructed the
population and recomputed every planned result directly from the scorer
manifest, visible inputs, two prediction files, and adapter before opening
`full/scored-results.json` or `result-report.md`. The later comparison found no
disagreement with either file.

The official ASE source checkout is at
`e84f66f8d494e46ef336edfa137db25a629614fb`. The review independently verified:

- 120 trajectories and 2,737 labeled iterations out of 2,751 visible
  iterations, for 99.491% published-label coverage;
- 218 AutoCodeRover, 1,108 OpenHands/CodeActAgent, and 1,411 RepairAgent rows;
- class counts of 606 Explore, 196 Locate, 364 Search, 153 Reproduce, 883
  Generate Fix, 294 Run tests, 23 Refactor, and 218 Explain;
- exactly 2,737 unique, source-hash-matched predictions in each repetition,
  all from the fixed eight-label grammar and all 5,474 requests succeeding on
  the first attempt; and
- 2,522 unique normalized source windows, 215 duplicate rows, and no identical
  source window with conflicting gold labels.

The target separation is sound. Visible rows contain only opaque `row_id`,
`source`, and `source_sha256`; manifest rows contain gold and provenance but no
source. Run mode rejects extra input fields, does not send row IDs to the
model, and sends only source text. Every source hash matches the manifest and
both prediction files.

## Independent recomputation

| Metric | Fixed tagger | Majority control | Difference |
|---|---:|---:|---:|
| Eight-class macro-F1 | 0.498425 | 0.060981 | +0.437444 |
| Accuracy | 0.627695 | 0.322616 | +0.305079 |

The independently recomputed 10,000-replicate stratified whole-trajectory
bootstrap used Python RNG seed 32025, resampled 40 trajectories with
replacement separately within each framework, retained the fixed eight-class
support, and recomputed both candidate and control macro-F1. It yielded a 95%
interval of `[+0.380168, +0.494079]`, median `+0.433125`, and zero non-positive
replicates. This exactly matches the stored scorer output.

Both repetitions agree on 2,737/2,737 predictions. Per-framework results also
match the raw reconstruction: AutoCodeRover macro-F1/accuracy
`0.753757/0.935780`, OpenHands `0.399871/0.439531`, and RepairAgent
`0.676583/0.727853` over each framework's published label support.

The principal class F1 values are Explore 0.2483, Locate 0.3869, Search 0.9057,
Reproduce 0.2176, Generate Fix 0.8877, Run tests 0.2604, Refactor 0.1935, and
Explain 0.8873. The dominant confusions are Explore to Locate (444), Run tests
to Reproduce (219), Reproduce to Generate Fix (101), Generate Fix to Reproduce
(32), and Refactor to Generate Fix (19). These boundaries prevent a uniform
accuracy claim but do not invalidate the positive primary effect.

The fixed Generate Fix majority comparison is fair for its declared role as a
no-semantic-signal lower-bound control. Selecting the population majority from
gold favors that control. It does not establish classifier state of the art,
and neither the report nor the permitted paper interpretation may claim that
it does.

## Findings and disposition

There are no result-invalidating must-fix items. Two documentation findings do
not affect validity:

1. `extract_response_text()` strips surrounding whitespace, so the earlier
   report statement that no output was normalized after inference was too
   strong. The result report now omits that statement.
2. The approved plan promised exact full-run and scoring commands. They are now
   included in the result report; this was reproducibility cleanup, not a new
   experiment or validity repair.

```text
run status: valid
tested hypothesis: supported
research value: decisive
paper impact: additional RQ evidence
next paper decision: add one concise RQ3 literal-action result with the stated
  class and framework boundaries; replace only the claim that literal action
  identity lacks direct evidence; preserve the thesis, four RQs, two
  abstractions, three contributions, and original paper story unchanged
```

**Final verdict:** **VALID RUN / TESTED HYPOTHESIS SUPPORTED / DECISIVE
ADDITIONAL RQ3 EVIDENCE / ZERO RESULT-INVALIDATING MUST-FIX ITEMS.**

## Outer-audit correction

The later fresh outer audit found a source condition that this result review
missed: 39 model-visible AutoCodeRover action fields are exactly the gold
literal `Locate`. The category column remains scorer-only, but the earlier
blanket statement that target separation is sound was therefore too broad.
The root independently excluded those 39 rows from the already durable
predictions and recomputed macro-F1 `0.490445` and accuracy `0.622313`, versus
majority `0.061645/0.327279`, over the remaining 2,698 rows. This correction
does not invalidate or rerun the experiment; it narrows the source-separation
description and is recorded in the result report and canonical evaluation.
