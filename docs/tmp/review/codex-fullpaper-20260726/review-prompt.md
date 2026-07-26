# Task: Adversarial full-paper review (ICSE/FSE empirical-SE standard)

Read-only review. Do NOT modify any file. Write your review to docs/tmp/review/codex-fullpaper-20260726/review.md.

You are reviewing this paper as a tough ICSE/FSE empirical software engineering reviewer (simulated reject-leaning PC member):

- Paper: docs/paper/main.tex (AAAI-27 format currently; venue may switch to ICSE 2027 — deadline 2026-10-23 — or FSE 2027 — ~2026-10-02; review the CONTENT, not the template)
- Study status and evidence frontier: docs/evaluation.md
- Recent repair chain (trust these, they are the current evidence base):
  - docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/taxonomy.md
  - docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/result.md
  - docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/delta-report.md

The paper is a longitudinal empirical study of AI-agent workspace activity across 6 projects (all author-associated), with a source-linked trajectory projection, RQ1-RQ6, and a measurement-capability benchmark whose frozen implementation failed (32/60 B+C) and was repaired to 60/60 B+C on the same corpus.

Attack it on, in priority order:

1. **Overclaims and claim-evidence mismatch**: every sentence in abstract/intro/conclusion vs what the evidence sections actually support. Flag any place the repair-corpus 60/60 is phrased as general capability.
2. **Number consistency**: cross-check headline numbers between main.tex, docs/evaluation.md, and the delta-report (551 sessions, 181,303/175,619 actions, 5,792 artifacts, 13,905 mutations, 89.29-97.02%, rho 0.2000, 60/60, per-project values). Report every inconsistency with line numbers.
3. **Methodology holes a reviewer will poke**: 6 author-projects corpus, confounding (skill/harness/model/task covary), gate threshold arbitrariness, A-family 12/30 explanation, RQ4 data-limited stop, negative RQ5 framing, rho interpretation at 0.2000, session-semantics change (2,049 files -> 551 roots) and whether the paper explains it.
4. **Venue-fit gaps for ICSE/FSE**: missing data-availability statement, double-anonymous leaks (author-identifying project names/repos!), related-work positioning vs ASE'25/ICSE trajectory studies, artifact/replication package.
5. **Writing/structure**: only the top 5 issues that most hurt acceptance.

Format: findings ordered by severity (blocker / major / minor), each with file:line evidence and a one-sentence fix suggestion. End with a simulated verdict (reject / weak reject / borderline / weak accept / accept) and the 3 highest-leverage fixes before submission.
