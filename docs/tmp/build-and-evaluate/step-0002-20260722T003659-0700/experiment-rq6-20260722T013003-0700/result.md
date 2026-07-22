# RQ6 Source-Signal Coverage Stop

**Association analysis stopped.** The frozen export lacks Skill names/arguments, model/configuration fields, repository-external instructions, and proof that sessions with no visible signal were unexposed.

| Project | Sessions | Skill Tool | Instruction read | Instruction mutation | Any visible signal |
|---|---:|---:|---:|---:|---:|
| agentsight | 1363 | 21 | 118 | 17 | 137 |
| ActPlane | 524 | 16 | 116 | 13 | 131 |
| bpf-developer-tutorial | 58 | 3 | 4 | 1 | 6 |
| eunomia.dev | 48 | 0 | 11 | 6 | 11 |
| agentskill-observability-paper | 36 | 12 | 1 | 0 | 13 |
| academic-writing-skills | 20 | 0 | 18 | 7 | 18 |

The exact rule yields 1762 signal rows across 1525 native Tool events. Vendor/status/source-call-ID coverage is in `raw/rq6-source-coverage.csv`; 60-bin support is action-order coverage, not time spent or duration.

These counts do not show that a skill was used, helpful, harmful, ignored, or causally related to any process outcome.
