# RQ5 Source-Explicit Skill And Instruction Footprints

This is an observational multi-case analysis. `attributionSkill` is source-native evidence; it does not prove that a Skill caused a useful or harmful outcome. A transcript file is not an independent session: all rows are blocked by native root session.

## Coverage

| Project | Tool events | Native roots | Skill calls (roots) | Attributed actions (roots) | Contiguously preceded actions (roots) | Not contiguously preceded | Args >300 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ActPlane | 65699 | 176 | 23 (11) | 157 (8) | 102 (8) | 55 | 9 |
| academic-writing-skills | 658 | 15 | 0 (0) | 0 (0) | 0 (0) | 0 | 0 |
| agentsight | 127957 | 397 | 28 (9) | 900 (12) | 241 (9) | 659 | 5 |
| agentskill-observability-paper | 991 | 8 | 13 (4) | 596 (8) | 133 (3) | 463 | 1 |
| bpf-developer-tutorial | 1911 | 45 | 3 (3) | 22 (2) | 0 (0) | 22 | 0 |
| eunomia-dev | 10683 | 29 | 0 (0) | 0 (0) | 0 (0) | 0 | 0 |

The contiguous same-stream count is only a conservative coverage diagnostic: a matching Skill call immediately precedes an attributed run with no intervening unattributed Tool event. It is not an exact invocation join or episode boundary. Parent invocation and delegated execution may occupy different streams, so primary footprints use source-native attribution only.

## Qualified footprints

A named Skill qualifies only with attribution in at least three distinct native root sessions inside one exact project/vendor/model/source-role stratum.

| Project | Vendor/model/role | Skill | Native roots | Attributed actions |
|---|---|---|---:|---:|
| ActPlane | claude/claude-opus-4-5-20251101/root | paper-writing-style | 5 | 39 |
| agentsight | claude/claude-opus-4-6/root | check-terminology-infoflow | 3 | 107 |
| agentskill-observability-paper | claude/claude-opus-4-6/root | iter-refine-ideas | 3 | 83 |
| agentskill-observability-paper | claude/claude-opus-4-6/root | rewrite-paper-section | 4 | 157 |
| agentskill-observability-paper | claude/claude-opus-4-6/subagent | iter-refine-ideas | 3 | 23 |

Only agentskill-observability-paper contains at least two qualified Skills in one exact project/vendor/model/source-role stratum. Within that case, median JSD is 0.116 for same-Skill pairs (n=9) and 0.123 for different-Skill pairs (n=10). This is a within-case descriptive association, not evidence for a cross-project fingerprint or causal effect.

The root-block randomization statistic (median same minus median different) is -0.007; one-sided exact p=0.750 over 12 admissible assignments (4 unique statistic values). Action-only medians are 0.165/0.174 (same/different); artifact-only medians are 0.000/0.000. Leave-one-project-out is N/A when only one project passes the exact comparison gate. Boundary-only membership is N/A because delegated execution crosses source streams and the source exposes no defensible per-invocation end boundary.

## Instruction focal events

Instruction reads/mutations are reported separately and never treated as proof of harness exposure or compliance. The primary plot uses only independently source-recomputed, high-confidence successful focal events; the CSV retains the broader parser set as sensitivity rows. Immediate following actions are counted at most once per focal event and only before a native prompt-index change.

| Project | Read ok/observed/fail | Mutation ok/observed/fail | Roots |
|---|---:|---:|---:|
| ActPlane | 480/1/17 | 78/8/3 | 54 |
| academic-writing-skills | 81/1/0 | 144/1/8 | 14 |
| agentsight | 1772/0/13 | 69/73/5 | 132 |
| agentskill-observability-paper | 5/0/0 | 5/0/0 | 2 |
| bpf-developer-tutorial | 22/0/0 | 3/0/0 | 9 |
| eunomia-dev | 26/0/1 | 1/5/0 | 7 |

## Interpretation stop

These six author-associated projects are selected natural cases, not a representative sample of agents, repositories, or tasks. Repository-direct source streams were used (`global=false`). The study can characterize recoverable structure and expose measurement failures; it cannot estimate prevalence, productivity, waste, or causal Skill/harness effects.
