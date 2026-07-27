# P1-v2 Independent Result Review

## Required judgments

- **Run status:** valid.
- **Tested hypothesis:** contradicted.
- **Research value:** decisive.
- **Paper impact:** mechanism/workload boundary.
- **Next paper decision:** retain the repair-corpus limitation and make no
  general exact-conformance claim.  Before relying on projection-sensitive
  RQ1--RQ4 values, audit whether the compound shell/wrapper cases identified
  here affect those estimands.

The review was performed read-only with Codex CLI 0.145.0,
`gpt-5.6-sol`, `xhigh` reasoning, and no approval or write capability.  It
read the protocol, attempt records, freeze and code seals, checker outputs,
complete question results, complete edge ledgers and diffs, and the frozen
native calls needed to adjudicate discrepancies.  It independently
recomputed the results below.

## Run and independence audit

The corpus recomputes to \(S=70\) roots: agentsight 12/258 eligible,
ActPlane 12/115, bpf-developer-tutorial 10/10, eunomia.dev 12/31,
bpf-benchmark 12/102, and bpftime 12/50.  It contains 40 Claude and 30 Codex
roots.  The registered formula gives
\(F=\lfloor30\cdot70/72+0.5\rfloor=29\) questions per family and \(Q=116\)
questions total.  Hamilton allocation gives five templates per family to
each project except bpf-developer-tutorial, which receives four.

All 70 source hashes and semantic roots are unique.  The three exclusion
manifests and their archived files revalidate, and the held-out corpus has
zero file-hash, native-root, and native-root/call overlap with them.  The 116
new question instances have zero exact-instance and zero full-row overlap
with the 120 repair-corpus questions.  Public question rows contain no
answers.  The source-direct checker independently covers 116 selected
questions, recomputes all 120 available templates, and verifies 1,999 oracle
edges and 6,524 calls.

Exactly one append-only attempt exists for each stage.  Their timestamps and
seals establish the required non-overlapping order
`freeze -> build -> preflight -> full`; every stage completed.  Preflight
materialized its expected 80 rows, and full materialized all six traces,
464/464 method rows, 116 trajectory decisions, and 24/24 completed
project-method cost cells.

## Score audit

The independent score is A 13/29, B 25/29, C 29/29, and D 29/29, with no
abstentions.  Thus the registered B+C gate is **54/58**, with four wrong
rows: bpf-developer-tutorial B1/B2 and eunomia.dev B1/B2.  The old **60/60**
uses 60 B+C questions over 72 separate repair-corpus files; it is regression
evidence only and cannot be pooled, rescaled, or denominator-matched with
the held-out 54/58.

## Edge-ledger audit

| Ledger | Expected | Actual | Matched | Missing | Extra | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Attempted edges | 1,999 | 2,017 | 1,998 | 1 | 19 | 0.990580 | 0.999500 | 0.995020 |
| Confirmed-effect edges | 1,845 | 1,862 | 1,844 | 1 | 18 | 0.990333 | 0.999458 | 0.994875 |
| Edge-call statuses | 1,865 | 1,865 | 1,865 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| Session order, corrected | 70 | 70 | 70 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |

The 20 row-level edge differences are one confirmed missing edge, 18
confirmed extra edges, and one failed extra edge.  They arise from
multi-source copy, recursive `git rm`, process substitution, a
shell-rejected leading backslash, and static/custom exec wrappers.  Call
statuses retain and exactly match the registered edge-call population.

The raw overall session-order summary is a reporting-layer aggregation bug:
it counts all 6,524 production-call rows instead of unique registered session
pairs.  Deduplicating the sealed events on
`(native_session_id, session_ordinal)` yields exactly 70/70; every project
and vendor partition independently agrees.  The correction is valid and
does not change the verdict because B+C and both edge ledgers fail
independently.

The full projection loads the registered Git blob.  The current tree differs
from the registration tree only in one plot-caption line, which is outside
the fixture and projection execution paths; this provenance difference
cannot affect the run.

## Conclusion

This is a valid negative held-out result.  It refutes exact conformance on
the registered workload while localizing the remaining gap to compound
shell/wrapper path admission rather than session identity, session order, or
call status.  The paper should keep the old 60/60 explicitly labeled as a
repair-corpus regression result, report this held-out contradiction, and
avoid a general exact-conformance statement until the boundary cases and
their RQ1--RQ4 impact have been audited.
