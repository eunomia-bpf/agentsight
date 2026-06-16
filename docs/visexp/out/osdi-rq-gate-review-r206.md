# R206 OSDI RQ Gate Review

Last updated: 2026-06-15
Stage at update: supplement / experiment-design gate
Source/command: read-only subagent review over revised `docs/visexp/RESEARCH_PLAN.md`, `docs/visexp/EXPERIMENT_PLAN.md`, `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/STATE.md`, `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/EXPERIMENT_AUDIT.md`, and `docs/visexp/paper/main.tex`, using the OSDI experiment-design rubric.
Completeness: complete review; no new human evidence

## Findings

1. Evidence blocker: C5 user utility is still empty. R142/R187/R193/R195
   provide packets, launch materials, contracts, and ingestion only; there are
   no participant responses. This is the top weak-accept blocker.
2. Evidence blocker: C6 tag adequacy is still unproven. R180 supports
   syntax/stability only; R124/R190/R203 remain empty human-label gates.
   Grammar validity, stability, canonicalization, and regeneration do not imply
   semantic adequacy.
3. No major wording blocker on novelty. The revised plan frames novelty as
   semantic attribution of system effects, not visualization or "flamegraphs
   for agents."
4. Baselines and falsifiers are clear enough for execution. RQ4 names trace
   tree, `event-count-proxy`, flat summary, nonsemantic stack, and semantic
   stack, while avoiding a false span-duration claim.
5. C4 is properly scoped. R114 supports fixed command-mode exact lineage, while
   R182 is only record-mode `--trace-net` implementation evidence because
   target-specific network rows remain 0/0.

## Maturity

Level 3: conference-paper mechanism evidence, not Level 4 systems narrative and
not OSDI weak accept. The blocker is evidence, not plan wording. Current
acceptable positioning is "semantic attribution mechanism plus measurement and
artifact prototype," not proven user utility or validated community tool.

## Reviewer-Required Next Rows

| Run | Required for | Reviewer gate |
|---|---|---|
| R142-pilot | C5/RQ4 | Real P01-P05 participant responses scored under frozen preregistration; response contract valid; task-level deltas interpretable. |
| R124-labels | C6/RQ5 | Two independent human label sheets over 300 rows, adjudication, adequate/generic/misleading rates, agreement threshold. |
| R151 | paper-scale C5 | 12-20 developers or clearly scoped expert study; Holm-corrected participant/task/order gate passes; false positives not worse. |
| R190-labels + R203-labels | canonical/long-tail quality only | Paired labels for merge risk and regenerated-tag promotion; over/under-merge and promotion thresholds pass; no automatic map update. |
| R191 | broader C4 network claims only | Target-specific loopback/child-process network rows observed and joined; 0 joined negative controls. |
| External fresh-clone smoke | C7/artifact strength | Clean setup on another machine, bounded writes, no raw-trace leakage, expected report artifacts, public setup docs. |

## Verdict

Plan-wording blockers: none material.

Evidence blockers: C5 responses and C6 human labels are mandatory. C4/RQ6 are
scope-strengthening work, but cannot substitute for C5/C6.
