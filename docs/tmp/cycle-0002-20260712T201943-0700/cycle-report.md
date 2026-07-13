# Cycle 0002 Report — Canonical-Story Evidence Program

**Started:** 2026-07-12T20:19:43-07:00
**Status:** EXPERIMENT gate active; revision-6 plan reflects the complete
verified-source audit; end-to-end REAL PREFLIGHT passed; independent
implementation re-review and full controls remain before the full run

## Objective

Preserve the untouched submodule story and generate complete positive evidence
for its four fixed RQs, beginning with RQ2 hidden-annotation localization.

## Inherited Authority

- exact thesis: **Agent observability needs profiling, not only debugging.**
- exact four RQs: attribution, real-problem localization, tag accuracy, cost;
- canonical story source: read-only `docs/agentpprof-paper/main.tex`;
- cycle 0001 REVIEW PASS:
  `../cycle-0001-20260711T164850-0700/03-review-gate/999-gate-report-20260712T202030-0700.md`.

The old intervention route and hierarchy-centered story are historical only.
This cycle changes evidence and mechanisms, not story.

## Current Route

1. completed official-source/protocol/baseline refresh: CodeTraceBench verified
   subset selected as the primary RQ2 condition;
2. corrected source identity: verified is an exact subset of full; the source
   has 3,316 unique manifest rows, 3,291 released raw archives, and 992
   raw-available verified rows;
3. completed source-unit audit over all 992 raw-available verified rows: 911
   align exactly, including 405 failed trajectories that define the primary
   target population; 89 rows remain explicit source exclusions;
4. completed one real end-to-end preflight through source extraction, release
   AgentProf, task-held-out reference profiles, pre-label predictions, terminal
   label join, and primary metrics; implementation re-review is next;
5. one full `research-experiment-design` loop over all released raw trajectories
   through complete result review, with each target scored from other tasks;
6. light evidence propagation under the canonical story lock;
7. REVIEW reflection and next fixed RQ.

## Current Reports

- gate entry:
  `01-experiment-gate/000-gate-entry-20260712T201943-0700.md`;
- source/protocol/baseline decision:
  `01-experiment-gate/literature-20260712T203001-0700/source-protocol-baseline-report.md`;
- current experiment plan and serial review:
  `01-experiment-gate/loop-rq2-codetracebench/experiment-plan.md` and
  `01-experiment-gate/loop-rq2-codetracebench/plan-review.md`;
- source identity/availability audit:
  `01-experiment-gate/loop-rq2-codetracebench/source-identity-and-availability-audit.md`;
- source-only semantic engagement audit:
  `01-experiment-gate/loop-rq2-codetracebench/source-only-semantic-engagement-audit.md`.
- complete verified-source audit:
  `../../visexp/out/codetracebench-rq2/verified-source-alignment-audit.md`;
- auditable REAL PREFLIGHT report:
  `01-experiment-gate/loop-rq2-codetracebench/preflight-report.md`;
- end-to-end output:
  `../../visexp/out/codetracebench-rq2/real-preflight/report.md`; implementation:
  `../../../script/codetracebench_agentprof_eval.py`.
