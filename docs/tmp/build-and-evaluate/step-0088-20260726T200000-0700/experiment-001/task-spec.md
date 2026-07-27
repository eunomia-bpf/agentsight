# Task spec: frozen direct backend on OSWorld-Human (independent population)

Autonomous agent in /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Deliverables in THIS directory only. RQ3 subject: tag accuracy.

## Hypothesis

The direct multi-level annotation backend, with its instruction UNCHANGED
from step 0087, recovers human group structure on an independent population
(OSWorld-Human GUI sessions) competitively with the specialized backends
already reported there.

## Setup

- Population: all 287 OSWorld-Human task-instance sessions with complete
  human group annotations (3,978 operations, 2,042 groups). Locate the
  frozen data and gold via step-0006 and step-0024/0030 records
  (docs/tmp/build-and-evaluate/) and .agentsight/experiments/.
- Backend: codex CLI gpt-5.6-sol, the step-0087 instruction VERBATIM
  (docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/
  holds it; adapt ONLY input packet formatting to OSWorld's source-visible
  fields — the same nine visible fields the supervised predictor reads, no
  gold labels). One call per session, one format retry.
- Score with the exact metrics of the existing OSWorld table rows:
  per-operation ordinary B-cubed P/R/F1 and exact adjacent-boundary
  P/R/F1 against the human groups; compare to stored rows (supervised
  0.739/0.816 boundary/B3; reference-calibrated 0.734/0.801; label-free
  recurrence 0.680/0.786; always-boundary 0.645/0.678).
- PILOT FIRST: deterministic 40-session slice (sorted IDs), paired
  comparison vs label-free recurrence on the same slice. Gate: pilot B3 F1
  >= recurrence-on-slice - 0.05 -> run all 287; else STOP after
  pilot-results.md.
- Record cost (calls, wall, tokens) and validity (coverage, conservation).

## Deliverables

pilot-results.md, raw marks/responses, raw-results.json, results.md with
paired session-cluster bootstrap intervals, cost-record.md, execution-log.md.
