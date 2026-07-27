# Independent Result Review

Date: 2026-07-26

## Verdict

**PASS.** The package is internally consistent and valid for its declared
descriptive estimands. No blocking discrepancy remains between `result.md`,
`analyze_user_questions.py`, the generated CSVs, and the final-HEAD raw inputs.

## Evidence checked

- Read the 2026-07-19 user instruction, the final report and script, every
  generated CSV, `projects.json`, both raw RQ1 CSVs, and all six event payloads.
- Verified script SHA-256
  `d2967be0e955df4e589f5491268d0c992127863c5de4b5944a759ede14bd56d2`.
- Verified `sha256sum *.csv | sha256sum` as
  `02c3bc7246adcdd0deb8a95c20e8432856d044e9bf9c3f2263c64248c460bf59`.
- Verified all nine input hashes and byte counts in `input-provenance.csv`.
- Reproduced 6 projects, 5,746 artifacts, 1,348 confirmed-created artifacts,
  13,906 mutation rows, 13,860 collapsed episodes, 28 B pairs, 31 D blocks,
  and 534 classification-audit rows.
- Confirmed that all 28 B rows contain nonempty, deterministically sorted
  `test_paths` and `code_paths`.

## Numerical and claim checks

- **A:** The report matches 1,066 created paper/docs artifacts, of which 318
  (29.8%) were never revisited and 665 (62.4%) were reread. The code comparison
  is 124 artifacts, 14 (11.3%) never revisited, and 97 (78.2%) reread.
  Same-event create followed by delete is correctly counted as a revisit.
- **B:** The 28 eligible pairs are all from AgentSight: 13 basename pairs and
  15 same-event fallbacks, with 0 test-first, 7 code-first, and 21 tied. The
  fallback ties are explicitly ties by construction. Independent timestamp
  inspection found a maximum first-modification gap of about 0.356 hours among
  basename pairs, confirming that cross-stream mutations are not paired.
- **C:** Confirmed totals reconcile to 43,322 reads and 13,906 writes. Pooled
  reads are nearly tied between paper/docs (18,828; 43.5%) and code (18,727;
  43.2%); confirmed writes are document-heavy (9,701; 69.8% versus 2,261;
  16.3%). The `ok+observed` view adds 11,037 attempts and preserves both
  directions.
- **D:** The 46 compound groups are all ordered create then delete and use the
  last action's validation outcome. Outcomes partition exactly into 4,649
  `observed_validation`, 9,111 `competing_supersede`, and 100 `censored_end`.
  Tests have 116 episodes, 71.6% repeat episodes, and 61.2% validation
  association; code has 2,257, 86.0%, and 48.7%. None of the 16 repeat-test
  blocks has zero code episodes; only one has more test than code episodes,
  with counts 2 versus 1.

Each “For the paper” passage contains four sentences and agrees with its
tables. The report avoids elapsed-time, quality, progress, waste, and causal
claims. Script outputs are confined to the requested package directory; it
does not target `docs/paper/` or `docs/evaluation.md`.

## Residual limitations

- A cannot identify documents explicitly required by an instruction, so its
  answer is a proxy over all created paper/docs artifacts.
- B has eligible evidence from only one project. Its 15 fallback ties establish
  same-event module co-occurrence, not semantic source--test correspondence.
- C's pooled read difference is only 101 actions, about 0.23 percentage points;
  it must remain described as nearly balanced rather than a meaningful
  document preference.
- Classification is a declared path heuristic. Generic directories such as
  `dist`, `target`, or `output` do not override source extensions, so generated
  code-shaped artifacts can remain classified as code.
- D's validation metric is temporal association only. The paired-block result
  does not establish test relevance, quality, wasted work, or causal source
  stasis.
- Pooled values are micro-weighted over six selected cases and are not
  population estimates.

```text
run status: valid
tested hypothesis: inconclusive as a general claim; B is one-case-only, while the exact D repeat-test/code-zero pattern was not observed
research value: supporting
paper impact: additional user-question evidence suitable for the supplement
next paper decision: report A-D with the stated limitations, emphasizing the near-tie in C reads and narrow coverage of B; make no time, quality, progress, waste, or causal claim
```
