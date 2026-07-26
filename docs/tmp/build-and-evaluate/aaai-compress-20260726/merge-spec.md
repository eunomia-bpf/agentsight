# Merge spec: review fixes to apply after the three codex runs land

## Verified already-clean (2026-07-26, checked against current docs)

- RQ2 "6/6 vs 3/6 contradiction": current docs/evaluation.md and main.tex are consistent — 6/6 is the current value, 3/6 appears only as dated history. The reviewer's hit was the hardcoded canned header in the 20260725 recompute result.md (known artifact, not paper text). NO PAPER FIX NEEDED.
- RQ4 "121/108 vs 120/110": the strings 121/108 no longer exist in main.tex/evaluation.md/implementation.md. Current text only says "three of six projects reach 20 eligible boundaries", consistent with the recompute table (28/22/28 pass, 16/1/15 fail; totals 120 components/110 boundaries). NO PAPER FIX NEEDED beyond whatever the final-HEAD rerun confirms.

## Still to apply (after bash-qh3e4fa2 compression + bash-hq8m44rk final rerun land)

1. If final-HEAD rerun changes ANY headline number → update main.tex + evaluation.md to the final values (compression must use them).
2. Data Availability statement: add 2-3 sentences (exported rows + benchmark question set + analysis code released; raw native sessions not redistributable, privacy) — placement per AAAI (inside content pages or supplement pointer).
3. "Progress" construct framing: one tightening sentence in intro + title-adjacent text — the paper measures workspace-activity consolidation/continuity, not outcome quality; keep the descriptive stance, do NOT add outcome claims.
4. Fold in rq-extensions results (dormant→revived, rank-turnover, spot-checks) into supplement.tex + at most one line each in main text.
5. Final: compile, verify 7+2 pages, verify no undefined refs, commit+push.

## Explicitly NOT doing (per author instruction: no ritual, no self-weakening)

- No edge-ledger reconciliation program.
- No held-out validation program (noted as future work at most).
- No extra hedging of the 60/60 beyond the existing plain "repair-corpus conformance" statement.
