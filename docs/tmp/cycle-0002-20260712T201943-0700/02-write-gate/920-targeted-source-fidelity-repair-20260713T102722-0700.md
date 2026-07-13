# Targeted Production-Scale Source-Fidelity Repair

- Completed: `2026-07-13T10:27:22-07:00`
- Cycle: `cycle-0002-20260712T201943-0700`
- Phase: `BUILD_AND_EVALUATE`
- Gate: `WRITE` re-entry
- Parent: `915-independent-outer-audit-20260713T102313-0700.md`
- Scope: one source-subject correction, one discovered bibliography metadata
  completion, full citation/build/page/font verification
- Git operations: none
- Submodule edits: none
- Scientific-contract changes: none
- Verdict: **COMPLETE; REQUEST FRESH OUTER AUDIT**

## Question and authority

The independent audit found that the paper attributed the surrounding support
service's annual request volume directly to an agent system. This node asks
whether the same real-world stakes can be stated exactly as the primary source
supports them, without changing the title, thesis, four RQs, model, claims,
results, section structure, or story.

The exact thesis remains:

> **Agent observability needs profiling, not only debugging.**

## Paper repair

The Abstract and Introduction now say that production agent deployments operate
within services that handle millions of requests per year. This matches the
first-party OpenAI case study's two facts without collapsing them:

- the support organization handles millions of requests annually;
- its production stack uses Agents SDK step-level traces, tool-call inspection,
  Responses API classifiers, and continuous evals.

The separate Codex source continues to support agent projects spanning hours,
days, or weeks and one single-prompt run exceeding seven million tokens. The
English and Chinese comments now share the same subject and scope.

This wording preserves million-request production stakes but no longer claims
that every request was itself served by an agent. No number or scientific
result changed.

## Citation-verifier discovery and repair

During verification, a nondeterministic DBLP lookup exposed that the V-measure
`booktitle` omitted the official parenthetical venue abbreviation. The ACL
Anthology's authoritative metadata names:

> Proceedings of the 2007 Joint Conference on Empirical Methods in Natural
> Language Processing and Computational Natural Language Learning
> (EMNLP-CoNLL)

The bibliography now includes `({EMNLP}-{CoNLL})`. Authors, title, pages,
publisher, address, year, and URL were already correct. This is a primary-source
metadata completion unrelated to the paper's story.

The final verifier reports:

```text
Found 54 bib entries (44 active)
Total entries checked: 44
Errors (must fix): 0
Warnings (should review): 2
OK: No VERIFIED entries have mismatches
```

The two warnings are false-positive generated-title heuristics for the official
API-Bank and GUIOdyssey titles.

## Build and rendered verification

`make -B` completed the full `pdflatex -> bibtex -> pdflatex -> pdflatex`
sequence. The current hashes are:

- `docs/paper/main.tex`:
  `c924bb7af782ef21083451c0ac1ebc906715dd3e4c861f72b8eb1815c3e22fb1`;
- `docs/paper/references.bib`:
  `27d34fb5db7c500def494ba93bcd9d3babf704325ebc8ebcf3d6aff7bc8a4ae6`;
- `docs/paper/main.pdf`:
  `9f6451143ac3ac1ed2d6d464003980abbb7efc89cdc443e8e77de3aa680d3048`.

The final artifact remains nine US-letter pages, PDF 1.5, unencrypted, and uses
only embedded Type 1 fonts. Page 7 contains the complete RQ4, Related Work, and
Conclusion before References; pages 8--9 contain references only. The log has:

- zero undefined citations/references;
- zero multiply-defined labels;
- zero overfull boxes;
- three cosmetic underfull horizontal boxes.

The abstract contains zero citation commands. The exact thesis occurs three
times. Exactly four RQ subsection headings remain, in the fixed order.

## Scientific impact and next action

This node closes the only blocker from the second outer audit and improves one
classic citation's official venue metadata. It does not authorize any empirical
headline or make the paper submission-ready. Independent RQ1 evidence,
target-blind/matched-decision RQ2 evidence, RQ3 backend coverage, integrated RQ4
cost, and closest-work defense remain for ordinary REVIEW and later complete
experiments.

A fresh independent auditor must now verify this exact snapshot. On a clean
WRITE verdict, transition to ordinary whole-paper REVIEW under
`iter-review-critique`, not milestone acceptance or another story rewrite.
