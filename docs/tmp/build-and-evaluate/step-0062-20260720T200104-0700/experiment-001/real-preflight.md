# Real Preflight — Source-Native Task Stack

## Run

- completed: 2026-07-20T20:59:12-07:00
- input census: 6,355 real Codex JSONL sessions, 46,426,046,398 bytes
- eligibility population discovered before selection: 1,967 root families
- selected family: first lexicographic eligible root,
  `019a3d9b-5016-77e3-8dd0-bce50f49f6a2`
- included operations: 147
- explicit task-control transitions: 15
- maximum visible task depth: 2

## Source-Fidelity Result

- operation-level exact-path accuracy: **147/147 = 1.000000**
- task-transition precision/recall/F1: **1.000000 / 1.000000 / 1.000000**
- missing, extra, or path-mismatched candidate operations: **0 / 0 / 0**
- event and token conservation: **exact / exact**
- unresolved parent links, unresolved operations, plan conflicts: **0 / 0 / 0**

The selected family contains a concrete task root and multiple source-native
plan items. It does not contain a child delegation, so the already passing
parent/child concurrency regression fixture covers that ordering invariant
until the complete population run exercises real child families.

## Profile Inspection And Minimal Repair

The first profile preserved the correct task paths but exposed two semantic
frame defects. A fixed task depth would be false when native plan and
delegation depth varies, and the result field used generic observation status
where a source-visible conclusion existed. Before the complete run, repeated
`task` values were kept as a variable-length pprof prefix and result fields were
changed to prefer source-visible progress or conclusion text. Tool calls
without one say so explicitly. Raw command and status remain evidence/detail
rather than persistent task frames. Command arrays are normalized before
extracting an operation object.

The repaired projection was rerun over the same real family and read with
`go tool pprof`. Exact-path, transition, and conservation results remained
unchanged. No inferred task, model classification, threshold, depth limit,
custom renderer, or frontend was added.

## Decision

**PASS to full run.** The preflight validates the parser, source-coordinate
identity, plan-state transition, operation attachment, independent raw replay,
resource folding, and variable-depth pprof path. It does not answer
whether the source-declared task structure is an ideal decomposition, and it
does not complete paper-level RQ3.

Codex JSONL does not expose a uniform active-runtime duration for every LLM and
tool operation. The run therefore conserves operation count and token count
only; it does not invent elapsed-time weights from inter-event
wall-clock gaps that would include user idle time.
