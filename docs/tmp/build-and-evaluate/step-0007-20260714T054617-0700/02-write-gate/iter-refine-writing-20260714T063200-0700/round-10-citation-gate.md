# Round 10 — Citation Gate

- Timestamp: 2026-07-14T07:45:50-07:00
- Scope: complete-paper citation placement, key integrity, source reality, and
  claim-to-source fit
- Review method: three-pass `check-paper-citations` audit, including an
  independent read-only missing-citation pass

## Pass 1 — Bibliography integrity

- `references.bib` contains 57 entries.
- All 57 entries have `VERIFIED`, `REAL: yes`, `PDF`, `ABSTRACT`, and
  `USED_FOR` annotations.
- The compiled paper uses 47 unique entries; every cited key exists in the
  bibliography.
- Added the primary Wilson score-interval source and the primary McCallum--Nigam
  Bernoulli Naive Bayes source. The latter PDF is stored under
  `docs/reference/`.
- The mechanical verifier checked all 47 active entries. It reported no error
  for either newly added source. It also repeated three metadata-API conflicts
  on two previously verified papers: a CoRR fallback for the COLM 2025
  AgentRewardBench paper, and the 2024 arXiv posting year/truncated venue for
  the ICLR 2025 AgentTrek paper. These are verifier false positives, not
  bibliography corrections: COLM's official 2025 accepted-paper list contains
  the AgentRewardBench OpenReview record, and the AgentTrek PDF states
  `Published as a conference paper at ICLR 2025`. Explicit verification notes
  now preserve that resolution next to both entries.

## Pass 2 — Citation accuracy

- Checked each citation in context against its annotated use.
- No inaccurate, contradictory, or decorative citation required removal.
- The paper does not attribute AgentSight 0.2.43 to the RQ1 experiment; it
  preserves the tested R114-compatible AgentSight 0.2.37 scope.
- No number, RQ, thesis, mechanism, or experiment conclusion changed.

## Pass 3 — Missing-citation audit

The independent reviewer found seven must-fix source placements and two method
placements. All were fixed:

1. traditional profilers and pprof-compatible profiles cite pprof/flame graphs;
2. the Introduction's public RQ2 workload and OSWorld-Human results cite their
   benchmark sources;
3. typical agent activity and linked effects cite real agent/observability
   systems;
4. the profile-construction pipeline cites pprof/flame graphs;
5. the evaluation overview and HINTBench counts cite the released benchmarks;
6. AgentProcessBench composition/counts cite AgentProcessBench;
7. Wilson lower bounds cite Wilson's primary paper;
8. Bernoulli Naive Bayes cites McCallum--Nigam's primary paper.

The paper now has 64 citation commands and 47 unique active keys, up from 52
commands and 45 keys. The added citations support existing statements; they do
not expand the experimental contract.

## Build verification

- `git diff --check`: clean.
- Full `make` plus final `pdflatex`: PASS.
- PDF: 10 pages total (7 content plus 3 references).
- Undefined citations/references: 0.
- Overfull boxes: 0.
- Exit `main.tex` SHA-256:
  `8be7c401e2b1a3965abc367ac2b4b9f6392c3fb02e6e64a6bcfa9db8f89dca2e`.
- Exit `references.bib` SHA-256:
  `05209a8aedec1b8b5e3268d008e47b72864b01d3a37eb83fb3e5d2f5a2512429`.
- Exit `main.pdf` SHA-256:
  `837a85a0273c5b0fab739b0cac18b92e904b804f70de052c1bf59334829a7df5`.

## Round decision

PASS. The citation gate is complete; all 11 serial writing rounds are complete.
