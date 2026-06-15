# R183 OSDI Gate Review

Date: 2026-06-15
Reviewer: Goodall subagent, read-only
Scope: R182 network lineage supplement plus current C4/C5/C6 evidence boundary

## Verdict

Level 3 / not weak accept.

R182 is useful implementation evidence for record-mode network tracing, but it
does not prove target-specific network workload capture. The smallest
non-fabricated path toward weak accept is still: collect human tag adequacy
labels for R124 and run the preregistered R142 developer task benchmark.

## Findings

1. **P1: R182 initially overclaimed network workload coverage.** The joined
   network rows were all low-level `codex` process rows. The observed target
   groups were `0.0.0.0:0`, `172.64.155.209:65535`,
   `104.18.32.47:65535`, `172.64.155.209:443`, and `family=10`; no
   `127.0.0.1`/localhost or expected Python/http.server child-process network
   rows were observed.

2. **P2: Exact lineage remains strongest for the fixed command-mode suite.**
   R114 remains the valid C4 anchor: 20/20 tasks completed, 1,273/1,273
   in-scope effects joined, precision/recall 100.0%/100.0%, and 0/3,170
   observed negative-control effects joined. R182 can only extend the
   implementation story unless target-specific network rows are observed and
   joined.

3. **P3: C5 and C6 remain blockers.** Subagent or LLM review cannot substitute
   for human tag adequacy labels or developer task outcomes.

## Accepted Revision

The R182 gate now requires target-specific loopback or expected child-process
network rows to be observed and joined before reporting `ok`. With the stricter
oracle, the committed R182 artifact is `partial`: 2/2 target tasks completed,
35/35 low-level `codex` process network rows joined, 0 network orphans,
0/604 negative-control joins, and 0/0 target-specific loopback/expected
child-process network rows.

The paper and claim ledger were revised so R182 is described as a partial
record-mode `--trace-net` smoke, not as proof of child-process loopback capture,
HTTP payload/URL reconstruction, or broad full-history provenance.
