# Task: Sweep final-HEAD values into main.tex and evaluation.md

The compressed paper (docs/paper/main.tex, 5 content + 1 refs pages) currently carries the 20260725 recompute numbers. The FINAL authoritative values are in docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/delta-report.md (read it first).

## Number sweep (old → final)

- worktree-attributed sessions/actions: 550/175,619 → **551/176,288**
- observed artifacts: 5,792 → **5,746**
- confirmed mutations: 13,905 → **13,906**
- reuse range: 89.29–97.02% → **89.29–97.11%**
- RQ4 totals: → **121 components / 111 boundaries** (per-project: agentsight 31/28, ActPlane 24/22, bpf 29/28, eunomia.dev 18/16, agentskill 2/1, academic 17/16)
- agentsight recognized validation success: 3,230 → **3,288** (if mentioned)
- UNCHANGED (verify but don't touch): 551 admitted sessions, 181,303 total actions, rho 0.2000, persistence 6/6, F5 6/6, eunomia 82.7% repeat fraction, 0 unknown-create births, RQ5/RQ6 values.

Apply to docs/paper/main.tex AND docs/evaluation.md (and docs/paper/supplement.tex if it cites any of these). Search for every occurrence of the old values (175,619 / 5,792 / 13,905 / 97.02 / 175850 / 175,850 variants) in both files.

## Also insert (texts already drafted in docs/tmp/build-and-evaluate/aaai-compress-20260726/merge-drafts.md — use them)

1. The Data Availability paragraph (place it per AAAI conventions — end of conclusion or a short unnumbered section before references; it must fit within content pages).
2. The one-sentence "progress" framing clarification in the intro.

## Constraints

- Do NOT change any other claim, structure, or section. Do NOT re-expand the paper.
- After edits: recompile main.tex AND supplement.tex; verify main.pdf stays ≤9 pages with references-only on the last page(s), zero LaTeX errors, no undefined references; verify the new values appear and no old value remains (grep).
- No git commands.

Final message: list of changed lines per file, final page counts, grep proof no stale value remains.
