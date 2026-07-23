# Step 0069 / WRITE 001 — Restore RQ and Evidence Attribution

- **Timestamp:** 2026-07-22T23:14:46-07:00
- **Parent review:** `step-0068-20260722T223854-0700`
- **Skill:** `rewrite-paper-section`
- **Scope:** source-faithful corrections only; no story, thesis, RQ-count,
  algorithm, experiment, table-value, or figure change
- **Input:** `docs/paper/main.tex` at commit `828428e0`

## Trigger

The Step 0068 review and independent outer audit established two bounded
writing defects:

1. fixed RQ1 asks whether semantic profiling improves resource attribution,
   whereas the paper had narrowed it to whether one hierarchy exposes
   different bottlenecks;
2. RQ2 prose did not name whether each result came from the target-blind
   declared/reference semantic hierarchy or the automatic Agent+Evidence
   backend.

## Changes

### RQ1

- Restored the exact fixed RQ:
  **“Does semantic profiling improve resource attribution?”**
- Preserved the existing multi-resource case as a necessary consequence and
  positive repeated-task result rather than redefining the whole RQ.
- Replaced the over-broad “RQ1 therefore answers yes” sentence with the exact
  supported conclusion: the shared responsibility path reunites SSH work across
  executions and changing the additive measure changes its attributed
  importance.

### RQ2

- The abstract and introduction now name the target-blind declared semantic
  hierarchy before reporting its all-three-workload MAP gains.
- The automatic Agent+Evidence result is separately reported as `.773/.414/.252`
  at table precision.
- The table caption defines `Sem.` as the target-blind declared/reference
  hierarchy fixed before evaluator target labels are loaded.
- The body retains the registered declared/reference gains and confidence
  intervals, then reports automatic-versus-Raw at full precision:
  `-0.0007`, `+0.1328`, and `+0.1307`.
- The contribution and conclusion now state that automatic problem ranking
  improves on two of three complete localization workloads.

## Invariants

- Exact thesis unchanged.
- Exactly four RQs remain.
- RQ2 itself unchanged.
- All table values unchanged.
- Abstract and introduction retain their architecture and claim surface.
- No result is renamed an oracle.
- No new negative-result story, new backend, or smaller paper thesis was
  introduced.

## Validation

- `git diff --check`: PASS.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: PASS.
- Output remains 10 pages.
- Output file: `docs/paper/main.pdf`.
- Build emitted only pre-existing underfull box warnings; no undefined
  citation/reference or fatal error.

## Completion

**WRITE status: complete; independent complete-paper consistency review
PASS after two bounded corrections.** The review verified the exact
full-precision deltas, declared/reference provenance, RQ1 restoration,
abstract/introduction/conclusion alignment, bilingual synchronization, and
absence of story drift.
