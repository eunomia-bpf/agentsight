# Independent WRITE Consistency Audit

## Node record

- Completed: 2026-07-14T02:57:41-07:00
- Reviewer: independent subagent explicitly applying
  `check-terminology-infoflow` in paper-consistency mode
- Scope: complete `docs/paper/main.tex`, Step 0005 evidence, R160, build log,
  user instructions, and idea story
- Verdict: **PASS**
- Must-fix: zero

## Verified current-binary evidence

- exact union: 27,765 operations;
- semantic median: 1.17 s;
- raw-action median: 0.99 s;
- semantic largest peak RSS: 464.5 MiB;
- semantic overhead: 180 ms / 18.2% time and 6.0 MiB / 1.3% RSS;
- semantic descriptive scaling: 0.0422 ms/operation,
  R-squared 0.9997, and 23,731 operations/s;
- all five table rows match the source artifacts.

## Verified cache boundary

The paper consistently describes R160 as one identical-input predecessor
AgentFlame pair: clean 1.64 s and 60 model calls versus cached 0.11 s, 76/76
hits, and zero calls. It explicitly says this is not current
`agentpprof 0.2.37` timing or a repeated estimate.

## Stale-claim and story audit

The old 76-configuration, 1.6/2.8/4.3-s, 118,021-request, 70%-hit,
35,136-call, and 31-ms-p95 claims are absent from `main.tex`. The exact thesis,
four RQs, story, and operations/operation-stack model did not drift.

Two unreferenced legacy table helpers still contain old R327/R328 numbers, but
`main.tex` does not include them. They do not affect the compiled paper and are
not modified in this targeted WRITE step.

The current PDF is eight pages with no undefined citation/reference, overfull
box, or LaTeX warning. Underfull warnings are non-blocking.
