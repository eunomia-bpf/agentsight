# R142 User-Task Preregistration

Status: `frozen_before_collection`
Generated: 2026-06-15T10:00:42+00:00

## Frozen Inputs

- `bundle`: `docs/visexp/out/user-task-benchmark.json` (`4d7536c025ae`)
- `assignments`: `docs/visexp/out/user-task-assignments.csv` (`50adc55106c8`)
- `answer_key`: `docs/visexp/out/user-task-answer-key.csv` (`f8c9fc0ee23d`)
- `response_template`: `docs/visexp/out/user-task-response-template.csv` (`087a6577bd2a`)
- `scorer`: `docs/visexp/score_user_task_results.py` (`738e911eca48`)

## Conditions

- Semantic condition: `semantic-stack`.
- Baselines: `trace-tree`, `event-count-proxy`, `flat-summary`, `nonsemantic-stack`.
- Order in packets: `trace-tree`, `event-count-proxy`, `flat-summary`, `nonsemantic-stack`, `semantic-stack`.
- Boundary: event-count-proxy is an event/count-weight view, not a span-duration baseline; a true span-duration baseline requires measured timestamp/duration reconstruction.

## Tasks And Assignment

- Tasks: 14.
- Primary utility tasks: 8 (UT01, UT04, UT05, UT06, UT07, UT08, UT09, UT10).
- Pilot participants in assignment template: 5.
- Assignment rows: 70.
- Complete task-condition coverage: True.

## Analysis Plan

- Response unit: one participant x task x condition row.
- Pilot minimum participants: 5.
- Paper minimum participants: 12.
- Minimum primary pairs per baseline: 8.
- Primary endpoints: `exact_accuracy_pct`, `log_time_seconds`.
- Guardrail: `false_positive_response_share_pct`.
- Diagnostic test: paired task-level sign-flip permutation.
- Paper-scale test: participant-task-order fixed-effect blocked permutation.
- Holm family: primary baseline comparisons x accuracy/time endpoints.
- Success rule: Semantic-stack must beat every baseline on primary utility tasks by >=10 pp exact accuracy or >=20% median task-time reduction, with Holm-corrected p<=0.05 and no >5 pp false-positive increase.

## Exclusion Rules

- Reject a response CSV with missing required columns.
- Reject duplicate participant/task/condition/packet assignment rows.
- Reject rows outside the committed assignment file when assignments are provided.
- Reject partial real-response files once any assigned row is scorable.
- Reject nonpositive or non-finite task_time_seconds.
- Reject confidence values outside 1..5.
- Do not drop tasks or participants after seeing outcomes unless the exclusion is documented before scoring.

## Claim Boundaries

- Pilot results can validate task wording and instrumentation but cannot support paper-scale C5.
- C5 remains unsupported while user-task-results.json is participant_results_empty.
- Subagent, LLM, or author-filled mock responses do not count as participant evidence.
- A true span-duration comparison must be registered as a new condition if reconstructed later.

## Validation

- Status: `ok`.
- Errors: none.
- Answer-key rows: 14.
- Response-template rows: 70.
