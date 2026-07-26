# Task: Compress the AAAI-27 paper to 7 content pages + 2 reference pages

Hard constraint (from the official AAAI-27 submission instructions): the submission PDF may have at most 9 pages; pages 8-9 are REFERENCES ONLY. Current docs/paper/main.pdf is 17 pages (~16 content + 1 refs). You must restructure docs/paper/main.tex so the compiled main.pdf is ≤7 content pages + ≤2 reference pages. Full paper deadline: July 28, 2026 23:59 UTC-12 (about 3 days). Supplementary material (due July 31) is allowed and is where cut content goes.

## Rules

- Keep the aaai2027 style, title, and abstract materially unchanged (the abstract is already registered on OpenReview; only minimal numeric updates allowed).
- Keep double-anonymous: no author-identifying info. IMPORTANT: the six corpus projects are the authors' own public repositories (agentsight etc.) — keep the existing neutral framing ("author-associated local projects") and do not add repo URLs or author hints.
- Preserve the repaired evidence story and the current numbers (authoritative source: docs/evaluation.md — 551 native-root sessions, 181,303 total / 175,619 attributed actions, 5,792 artifacts, 13,905 mutations, reuse 89.29–97.02%, Spearman rho 0.2000, persistence 6/6, validation coverage 6/6, RQ4 data-limited stop, RQ5 negative Skill fingerprint, RQ6 external boundary, conformance: frozen 32/60 B+C (dated) → repaired 60/60 B+C vs corrected v4 oracle, A-family 12/30 by deliberate grammar difference, no general exact-fact capability claim).
- Ethics statement must fit inside the 7 content pages.

## Structure guidance (target ≈7 content pages)

- Intro ~1p; method (workspace projection + source-linked protocol) ~1.25p; RQ highlights ~2.5–3p (keep only the strongest figure or two in main text; per-RQ details move to supplement); measurement-capability conformance ~0.75p (three-stage story: frozen failure → taxonomy → repaired 60/60, plainly stated); threats to validity + ethics ~0.5p; related work compressed ~0.5p; conclusion ~0.25p.
- Move ALL cut content (extra figures, per-RQ detail, full gate/coverage tables) into a NEW file docs/paper/supplement.tex (same aaai2027 style, its own compile target, references can repeat via the same .bib). Every claim removed from the main text must land in the supplement, not vanish.
- Main text should explicitly point to the supplement for details (one line per RQ section max).

## Process

1. Read docs/paper/main.tex fully and docs/evaluation.md first.
2. Restructure main.tex; create supplement.tex.
3. Compile both (latexmk or the repo's existing build path in docs/paper) and verify: main.pdf ≤ 9 pages total with nothing but references on pages 8-9; supplement compiles; zero LaTeX errors and no undefined references.
4. Iterate until page limits pass. Do not delete figures from docs/paper/figures — just stop including the moved ones in main.tex (include them in supplement.tex instead).
5. Do not run git commands.

Final message: resulting page counts (content/refs) for main and supplement, list of what moved, any claim that had to be dropped entirely (should be none or few — list them explicitly).
