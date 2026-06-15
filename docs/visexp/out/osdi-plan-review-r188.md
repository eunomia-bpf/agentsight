# R188 OSDI Plan Review After R187

Date: 2026-06-15
Reviewer: Jason subagent, read-only
Stage at update: supplement / experiment-design
Source/command: OSDI review over `docs/visexp/STATE.md`,
`docs/visexp/RESEARCH_PLAN.md`, `docs/visexp/FOLLOWUP_PLAN.md`,
`docs/visexp/EXPERIMENT_TRACKER.md`, `docs/visexp/CLAIM_VERDICT.md`,
`docs/visexp/EXPERIMENT_AUDIT.md`,
`docs/visexp/out/user-task-pilot-r142/launch/manifest.json`,
`docs/visexp/out/weak-accept-gate-r184.json`,
`docs/visexp/out/osdi-plan-review-r186.md`, and
`docs/visexp/paper/main.tex`
Completeness: complete for read-only plan review; not C5/C6 outcome evidence

## Verdict

Maturity: Level 3 conference-paper mechanism evidence. Not OSDI weak accept.

R187 improves execution readiness by packaging the R142 pilot launch materials,
but it records `real_response_count=0`, `pilot_ready=false`, and
`c5_supported=false`. R184 remains authoritative: weak accept is blocked while
C5 has no real participant responses and C6 has no independent human labels.

## Claim Coverage

| Claim | Review status | Reason |
|-------|---------------|--------|
| C1-C3 | supportable | Real local-session folded stacks, semantic/nonsemantic mixing, and R131 ablation support the mechanism story. |
| C4 | fixed-suite supported only | R114 is strong for fixed command-mode Codex tasks; R182 still has 0/0 target-specific loopback/child-process rows. |
| C5 | unsupported | R187 is launch material only; no developer responses exist. |
| C6 | partial | R180 is syntax/latency/stability evidence; R124 human labels are still empty. |
| C7 | partial | R160 is bounded local artifact evidence, not community/fresh-clone evidence. |

## Must-Fix Gaps

1. C5 developer utility remains the highest-risk gap. Run R142 with real
   participants using the R187 P01-P05 launch packets and score the completed
   response CSV.
2. C6 adequacy remains unproven. Collect two independent human labeler sheets
   for R124, adjudicate disagreements, and run the existing scorer.
3. C4 must stay scoped. Do not claim broad network, full-history exact
   provenance, arbitrary-agent provenance, or HTTP URL/payload reconstruction
   from R182.
4. Keep paper wording centered on semantic attribution of agent system effects:
   `sessionTag;promptTag;llmcall/tool;process*;effect`, not "flamegraphs for
   agents."

## Required Wording Fixes

- Clarify R142 versus R151: R142 is the five-participant pilot; R151 is the
  paper-scale 12-20 participant run or a deliberately narrowed expert study.
- Keep `event-count-proxy` everywhere unless a true timestamp-derived
  span-duration baseline is generated and preregistered.
- Treat "improved information organization" as the current claim, not
  "developers are faster or more accurate."
- Keep C6 as lossy navigation tags with measured syntax/stability until R124
  human labels pass.
- Fix stale R122 wording from 290 parsed sessions to 294 parsed sessions.

## Exact Next Rows

| Run ID | Claim | Purpose | Seed/reps | Oracle | Gate | Result path |
|--------|-------|---------|-----------|--------|------|-------------|
| R142-pilot | C5 | Real developer pilot using R187 P01-P05 packets. | 5 participants, P01-P05 once each | hidden answer key, timing, false positives, confidence, response-contract checker | valid pilot protocol; still not paper-scale C5 unless scorer says so | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` |
| R124-labels | C6 | Human adequacy labels over R122/R124 fragments. | 300 fragments x 2 labelers | adequate/generic-noisy/misleading rubric plus agreement/adjudication | >=80% adequate, <=20% generic/noisy, <=5% misleading, kappa >=0.6 or narrowed claim | `docs/visexp/out/tag-adequacy-results-r124.json` |
| R151 | C5 | Paper-scale user utility run after R142 passes. | 12-20 developers or scoped expert study | frozen answer key plus Holm-corrected participant/task/order blocked test | C5 gate passes and false positives do not increase by >5 pp | `docs/visexp/out/user-task-results.json` |

## Evidence Boundary

Subagent reviews, LLM-filled labels, author mock responses, placeholder rows,
syntax-only tag validity, and blank templates cannot count for C5 or C6. They
can only audit protocol quality. Real C5 requires real participant responses;
real C6 requires independent human labels.
