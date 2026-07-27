# P1-v2 Held-Out Question and Full Edge-Ledger Conformance

## Outcome

- Run status: **valid**.
- Tested hypothesis: **contradicted**.
- Strict held-out conformance decision: **fail**.
- Held-out B+C: **54/58 correct**, 4 wrong, 0 abstain.
- Held-out D: **29/29 correct**, 0 wrong, 0 abstain.
- Full attempted edge ledger: oracle=1999, projection=2017, missing=1, extra=19.

The earlier **60/60** is retained as repair-corpus regression evidence over the original 72 files and original 60 B+C rows.  The number above uses 58 newly instantiated B+C rows from 70 root-disjoint held-out files.  The results are reported separately, are not pooled or rescaled, and have different denominators whenever the v2 proportional rule yields fewer than 60 held-out B+C questions.

## Corpus composition

| Project | Eligible roots | Selected roots | Questions/family | Total questions | Vendors |
|---|---:|---:|---:|---:|---|
| agentsight | 258 | 12 | 5 | 20 | claude,codex |
| ActPlane | 115 | 12 | 5 | 20 | claude,codex |
| bpf-developer-tutorial | 10 | 10 | 4 | 16 | claude |
| eunomia.dev | 31 | 12 | 5 | 20 | claude,codex |
| bpf-benchmark | 102 | 12 | 5 | 20 | claude,codex |
| bpftime | 50 | 12 | 5 | 20 | claude,codex |

## Question-family scores

| Family | Correct | Wrong | Abstain |
|---|---:|---:|---:|
| A | 13/29 | 16 | 0 |
| B | 25/29 | 4 | 0 |
| C | 29/29 | 0 | 0 |
| D | 29/29 | 0 | 0 |

## Post-run metric audit

The completed runner's raw overall `session_order` aggregation counted one
row per production call, yielding an uncorrected `actual=6524` and 6,454
spurious extras in `raw/full/summary.json` and `edge-summary.csv`.  That is an
analysis bug: the frozen protocol defines session order as the unique pair
`(native_session_id, session_ordinal)`, not as one pair per call.  The same
runner already applies the unique-pair definition in every project and vendor
group.  Summing those disjoint groups gives oracle=70, projection=70,
matched=70, missing=0, extra=0, so protocol-defined overall session-order
precision=recall=F1=1.0.  The raw runner output is preserved unchanged for
auditability; the corrected protocol value is reported below.  This correction
does not change the valid-fail decision because B+C and both edge ledgers fail
their frozen gates independently.

## Edge-level ledger

The exact attempted-edge key includes final `display_path` in addition to semantic root, source stream/tool ordinal, call/event/action order, path/access/previous path, and artifact generation. Confirmed effects and edge-call statuses are separately exact-gated.

| Scope | Ledger | Expected | Actual | Matched | Missing | Extra | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| overall | session_order | 70 | 70 | 70 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| overall | attempted_edges | 1999 | 2017 | 1998 | 1 | 19 | 0.990580 | 0.999500 | 0.995020 |
| overall | confirmed_effect_edges | 1845 | 1862 | 1844 | 1 | 18 | 0.990333 | 0.999458 | 0.994875 |
| overall | edge_call_statuses | 1865 | 1865 | 1865 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:agentsight | session_order | 12 | 12 | 12 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:agentsight | attempted_edges | 46 | 46 | 46 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:agentsight | confirmed_effect_edges | 42 | 42 | 42 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:agentsight | edge_call_statuses | 45 | 45 | 45 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:ActPlane | session_order | 12 | 12 | 12 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:ActPlane | attempted_edges | 689 | 693 | 689 | 0 | 4 | 0.994228 | 1.000000 | 0.997106 |
| project:ActPlane | confirmed_effect_edges | 598 | 602 | 598 | 0 | 4 | 0.993355 | 1.000000 | 0.996667 |
| project:ActPlane | edge_call_statuses | 660 | 660 | 660 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpf-developer-tutorial | session_order | 10 | 10 | 10 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpf-developer-tutorial | attempted_edges | 138 | 139 | 138 | 0 | 1 | 0.992806 | 1.000000 | 0.996390 |
| project:bpf-developer-tutorial | confirmed_effect_edges | 134 | 134 | 134 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpf-developer-tutorial | edge_call_statuses | 139 | 139 | 139 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:eunomia.dev | session_order | 12 | 12 | 12 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:eunomia.dev | attempted_edges | 391 | 403 | 391 | 0 | 12 | 0.970223 | 1.000000 | 0.984887 |
| project:eunomia.dev | confirmed_effect_edges | 362 | 374 | 362 | 0 | 12 | 0.967914 | 1.000000 | 0.983696 |
| project:eunomia.dev | edge_call_statuses | 301 | 301 | 301 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpf-benchmark | session_order | 12 | 12 | 12 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpf-benchmark | attempted_edges | 673 | 674 | 672 | 1 | 2 | 0.997033 | 0.998514 | 0.997773 |
| project:bpf-benchmark | confirmed_effect_edges | 651 | 652 | 650 | 1 | 2 | 0.996933 | 0.998464 | 0.997698 |
| project:bpf-benchmark | edge_call_statuses | 658 | 658 | 658 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpftime | session_order | 12 | 12 | 12 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpftime | attempted_edges | 62 | 62 | 62 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpftime | confirmed_effect_edges | 58 | 58 | 58 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| project:bpftime | edge_call_statuses | 62 | 62 | 62 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| vendor:claude | session_order | 40 | 40 | 40 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| vendor:claude | attempted_edges | 910 | 915 | 909 | 1 | 6 | 0.993443 | 0.998901 | 0.996164 |
| vendor:claude | confirmed_effect_edges | 882 | 886 | 881 | 1 | 5 | 0.994357 | 0.998866 | 0.996606 |
| vendor:claude | edge_call_statuses | 902 | 902 | 902 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| vendor:codex | session_order | 30 | 30 | 30 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| vendor:codex | attempted_edges | 1089 | 1102 | 1089 | 0 | 13 | 0.988203 | 1.000000 | 0.994067 |
| vendor:codex | confirmed_effect_edges | 963 | 976 | 963 | 0 | 13 | 0.986680 | 1.000000 | 0.993296 |
| vendor:codex | edge_call_statuses | 963 | 963 | 963 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |

Row-level attempted-edge differences: **20**. The complete ledgers are in `raw/full/edge-ledger.csv`; differences are in `raw/full/edge-diff.csv`.

## Failure localization

All 1,865 edge-call statuses and all 70 protocol-defined session-order pairs
match.  The conformance failures are path/action admission differences:

- ActPlane has 4 extra attempted and confirmed edges.
- bpf-developer-tutorial has 1 extra attempted failed-read edge; because it is
  failed, it creates no confirmed-effect difference.
- eunomia.dev has 12 extra attempted and confirmed edges.
- bpf-benchmark has 1 missing and 2 extra attempted edges; the same 1 missing
  and 2 extra appear in confirmed effects.
- agentsight and bpftime are exact on all four ledgers.

The four B errors are concentrated in two P0 identities.  For
bpf-developer-tutorial, projection admits one additional failed read of
`src/52-fsession-latency/README.md`, changing B1/B2 from 29/9 to 30/10.  For
eunomia.dev, projection admits one additional wrapped read of
`docs/blog/posts/ebpf-ai-agent-policy-enforcement.zh.md`, changing B1/B2 from
44/21 to 45/22.  C remains 29/29 and D remains 29/29.

Inspection of the seven native calls responsible for the 20 edge differences
indicates that the boundary is concentrated in compound shell/wrapper
constructs: multi-source copy and recursive `git rm`, process substitution,
a leading backslash rejected by the shell path, and static/custom `exec`
envelopes.  This is a post-run error-class inference from the frozen native
calls, not a change to the oracle or score.

## Per-question decisions

| Question | Family | Expected | Trajectory | Status | Judgment |
|---|---:|---:|---:|---:|---:|
| ActPlane-A1 | A | 354 | 375 | answer | wrong |
| ActPlane-A2 | A | 303 | 303 | answer | correct |
| ActPlane-A3 | A | 70 | 46 | answer | wrong |
| ActPlane-A4 | A | 5 | 5 | answer | correct |
| ActPlane-A5 | A | 3 | 2 | answer | wrong |
| ActPlane-B1 | B | 119 | 119 | answer | correct |
| ActPlane-B2 | B | 42 | 42 | answer | correct |
| ActPlane-B3 | B | 77 | 77 | answer | correct |
| ActPlane-B4 | B | read | read | answer | correct |
| ActPlane-B5 | B | 2 | 2 | answer | correct |
| ActPlane-C1 | C | 4 | 4 | answer | correct |
| ActPlane-C2 | C | 10 | 10 | answer | correct |
| ActPlane-C3 | C | 1 | 1 | answer | correct |
| ActPlane-C4 | C | 2 | 2 | answer | correct |
| ActPlane-C5 | C | 26 | 26 | answer | correct |
| ActPlane-D1 | D | untracked | untracked | answer | correct |
| ActPlane-D2 | D | untracked | untracked | answer | correct |
| ActPlane-D3 | D | untracked | untracked | answer | correct |
| ActPlane-D4 | D | untracked | untracked | answer | correct |
| ActPlane-D5 | D | absent | absent | answer | correct |
| agentsight-A1 | A | 39 | 40 | answer | wrong |
| agentsight-A2 | A | 8 | 8 | answer | correct |
| agentsight-A3 | A | 9 | 3 | answer | wrong |
| agentsight-A4 | A | 1 | 1 | answer | correct |
| agentsight-A5 | A | 0 | 0 | answer | correct |
| agentsight-B1 | B | 3 | 3 | answer | correct |
| agentsight-B2 | B | 1 | 1 | answer | correct |
| agentsight-B3 | B | 2 | 2 | answer | correct |
| agentsight-B4 | B | read | read | answer | correct |
| agentsight-B5 | B | 1 | 1 | answer | correct |
| agentsight-C1 | C | 0 | 0 | answer | correct |
| agentsight-C2 | C | 0 | 0 | answer | correct |
| agentsight-C3 | C | 0 | 0 | answer | correct |
| agentsight-C4 | C | 0 | 0 | answer | correct |
| agentsight-C5 | C | 0 | 0 | answer | correct |
| agentsight-D1 | D | tracked | tracked | answer | correct |
| agentsight-D2 | D | tracked | tracked | answer | correct |
| agentsight-D3 | D | tracked | tracked | answer | correct |
| agentsight-D4 | D | tracked | tracked | answer | correct |
| agentsight-D5 | D | tracked | tracked | answer | correct |
| bpf-benchmark-A1 | A | 470 | 479 | answer | wrong |
| bpf-benchmark-A2 | A | 168 | 168 | answer | correct |
| bpf-benchmark-A3 | A | 30 | 7 | answer | wrong |
| bpf-benchmark-A4 | A | 9 | 9 | answer | correct |
| bpf-benchmark-A5 | A | 4 | 3 | answer | wrong |
| bpf-benchmark-B1 | B | 96 | 96 | answer | correct |
| bpf-benchmark-B2 | B | 20 | 20 | answer | correct |
| bpf-benchmark-B3 | B | 76 | 76 | answer | correct |
| bpf-benchmark-B4 | B | read | read | answer | correct |
| bpf-benchmark-B5 | B | 3 | 3 | answer | correct |
| bpf-benchmark-C1 | C | 6 | 6 | answer | correct |
| bpf-benchmark-C2 | C | 8 | 8 | answer | correct |
| bpf-benchmark-C3 | C | 0 | 0 | answer | correct |
| bpf-benchmark-C4 | C | 2 | 2 | answer | correct |
| bpf-benchmark-C5 | C | 30 | 30 | answer | correct |
| bpf-benchmark-D1 | D | tracked | tracked | answer | correct |
| bpf-benchmark-D2 | D | absent | absent | answer | correct |
| bpf-benchmark-D3 | D | tracked | tracked | answer | correct |
| bpf-benchmark-D4 | D | untracked | untracked | answer | correct |
| bpf-benchmark-D5 | D | absent | absent | answer | correct |
| bpf-developer-tutorial-A1 | A | 75 | 75 | answer | correct |
| bpf-developer-tutorial-A2 | A | 73 | 73 | answer | correct |
| bpf-developer-tutorial-A3 | A | 11 | 0 | answer | wrong |
| bpf-developer-tutorial-A4 | A | 8 | 8 | answer | correct |
| bpf-developer-tutorial-B1 | B | 29 | 30 | answer | wrong |
| bpf-developer-tutorial-B2 | B | 9 | 10 | answer | wrong |
| bpf-developer-tutorial-B3 | B | 20 | 20 | answer | correct |
| bpf-developer-tutorial-B4 | B | read | read | answer | correct |
| bpf-developer-tutorial-C1 | C | 3 | 3 | answer | correct |
| bpf-developer-tutorial-C2 | C | 5 | 5 | answer | correct |
| bpf-developer-tutorial-C3 | C | 1 | 1 | answer | correct |
| bpf-developer-tutorial-C4 | C | 4 | 4 | answer | correct |
| bpf-developer-tutorial-D1 | D | tracked | tracked | answer | correct |
| bpf-developer-tutorial-D2 | D | tracked | tracked | answer | correct |
| bpf-developer-tutorial-D3 | D | tracked | tracked | answer | correct |
| bpf-developer-tutorial-D4 | D | tracked | tracked | answer | correct |
| bpftime-A1 | A | 163 | 182 | answer | wrong |
| bpftime-A2 | A | 18 | 18 | answer | correct |
| bpftime-A3 | A | 52 | 8 | answer | wrong |
| bpftime-A4 | A | 3 | 3 | answer | correct |
| bpftime-A5 | A | 2 | 2 | answer | correct |
| bpftime-B1 | B | 10 | 10 | answer | correct |
| bpftime-B2 | B | 8 | 8 | answer | correct |
| bpftime-B3 | B | 2 | 2 | answer | correct |
| bpftime-B4 | B | read | read | answer | correct |
| bpftime-B5 | B | 2 | 2 | answer | correct |
| bpftime-C1 | C | 1 | 1 | answer | correct |
| bpftime-C2 | C | 5 | 5 | answer | correct |
| bpftime-C3 | C | 1 | 1 | answer | correct |
| bpftime-C4 | C | 11 | 11 | answer | correct |
| bpftime-C5 | C | 7 | 7 | answer | correct |
| bpftime-D1 | D | tracked | tracked | answer | correct |
| bpftime-D2 | D | absent | absent | answer | correct |
| bpftime-D3 | D | tracked | tracked | answer | correct |
| bpftime-D4 | D | tracked | tracked | answer | correct |
| bpftime-D5 | D | tracked | tracked | answer | correct |
| eunomia.dev-A1 | A | 176 | 196 | answer | wrong |
| eunomia.dev-A2 | A | 98 | 48 | answer | wrong |
| eunomia.dev-A3 | A | 78 | 25 | answer | wrong |
| eunomia.dev-A4 | A | 4 | 3 | answer | wrong |
| eunomia.dev-A5 | A | 2 | 1 | answer | wrong |
| eunomia.dev-B1 | B | 44 | 45 | answer | wrong |
| eunomia.dev-B2 | B | 21 | 22 | answer | wrong |
| eunomia.dev-B3 | B | 23 | 23 | answer | correct |
| eunomia.dev-B4 | B | read | read | answer | correct |
| eunomia.dev-B5 | B | 2 | 2 | answer | correct |
| eunomia.dev-C1 | C | 7 | 7 | answer | correct |
| eunomia.dev-C2 | C | 9 | 9 | answer | correct |
| eunomia.dev-C3 | C | 0 | 0 | answer | correct |
| eunomia.dev-C4 | C | 1 | 1 | answer | correct |
| eunomia.dev-C5 | C | 23 | 23 | answer | correct |
| eunomia.dev-D1 | D | tracked | tracked | answer | correct |
| eunomia.dev-D2 | D | tracked | tracked | answer | correct |
| eunomia.dev-D3 | D | tracked | tracked | answer | correct |
| eunomia.dev-D4 | D | tracked | tracked | answer | correct |
| eunomia.dev-D5 | D | untracked | untracked | answer | correct |

## Interpretation boundary

This run tests deterministic native-record conformance, not complete system effects or population generalization.  A-family rows are reported but do not gate the preregistered B/C/D and full-ledger decision.

The result contradicts exact held-out conformance despite exact C, D,
call-status, and session-order results.  The original 60/60 must remain
repair-corpus regression evidence.  Before using projection-sensitive exact
RQ1--RQ4 counts as generally conformant, the paper should retain the
repair-corpus limitation and audit whether the compound shell/wrapper path
classes above occur in those estimands.
