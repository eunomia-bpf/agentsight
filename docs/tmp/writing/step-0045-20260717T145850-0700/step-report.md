# Step 0045 — Source-Grounded AAAI Argument Repair

**Gate:** WRITE
**Started:** 2026-07-17 14:58:50 -0700
**Last updated:** 2026-07-17 15:36:18 -0700
**Status:** complete; independent scientific, preservation, and format reviews PASS

## Immutable research contract

This step preserves the exact thesis:

> **Agent observability needs profiling, not only debugging.**

It also preserves exactly four RQs, in order: resource attribution, problem
correspondence/localization, tag accuracy, and profiling cost. It does not
change the operation model, operation-stack algorithm, experiment population,
metric value, or result interpretation. The read-only authoritative submodule
`docs/agentpprof-paper` remains at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c` and was not modified.

## Inputs

- Step 0044 independent blind read, external search, and full review under
  `docs/tmp/review/step-0044-20260717T150000-0700/`.
- Current paper source and compiled PDF.
- `docs/background-related-work.md`.
- The primary OOPSLA 2026 paper *Process-Centric Analysis of Agentic Software
  Systems*, DOI `10.1145/3798271`. The 28-page author preprint at arXiv
  `2512.02393` is downloaded to `docs/reference/2026-liu-graphectory.pdf` with SHA-256
  `a05088ae93a2536790040ecad9828231bc8e3804c79a92eb46fc52ccd2fe355f`.

## Step 0044 defects addressed

1. The paper omitted the closest archival process-centric agent-trajectory
   comparison, Graphectory.
2. RQ1 compressed effect lineage, conservation, and partition agreement into a
   sentence that could make the roles of the measurements ambiguous.
3. RQ2 named AP/MAP but did not state how tied scores enter AP or how query APs
   are averaged.
4. RQ3 named literal-label, partition, and boundary metrics without explicitly
   saying that they evaluate distinct output types; macro-F1 averaging was not
   defined locally.
5. The strongest residual capability relative to adjacent systems was present
   but not stated as a single conjunction in Related Work.
6. RQ4's fixed-input construction-cost scope was already explicit and required
   no edit.

## Changes

### Literature and novelty frontier

- Added the verified Graphectory primary source to `references.bib`, including
  authors, PACMPL/OOPSLA1 bibliographic data, pages, DOI, local PDF provenance,
  and intended use.
- Added a concise closest-work entry to `docs/background-related-work.md`.
- Added Graphectory to the Introduction and Related Work comparison without
  claiming that process graphs, semantic grouping, cross-run analysis, or
  intervention are independently novel.
- Kept AgentProf's positive residual capability as one conjunction over one
  heterogeneous operation corpus: source-linked agent/system effects,
  conservation of arbitrary additive measures, and selectable query-time pprof
  operation stacks.

### Evaluation definitions

- RQ1 now assigns each measurement one job: scoped controls test effect
  lineage, exact totals test conservation, and ordinary B-cubed tests agreement
  with human responsibility partitions.
- RQ2 now states tie-threshold non-interpolated AP per query and arithmetic-mean
  MAP across all target-bearing queries. The reported values and scorer are
  unchanged.
- RQ3 now defines macro-F1 as the unweighted mean of per-class F1 and explicitly
  distinguishes literal labels, permutation-invariant partitions, and adjacent
  boundaries. The metric suite and values are unchanged.

No experiment, algorithm, claim, RQ, or result value changed in this WRITE step.

## Validation

- `make clean && make all`, followed by one settling `pdflatex` pass: PASS.
- Final PDF: 9 pages, US Letter. The complete main text and Conclusion end on
  page 7; References start on page 8.
- No undefined citations or references, changed labels, LaTeX errors, or
  overfull boxes in the final log.
- All embedded fonts are Type 1; no Type 3 fonts.
- Exact thesis occurs three times, and the four RQ headings remain unchanged.
- `git diff --check`: PASS.
- `docs/agentpprof-paper`: clean at the immutable commit above.

During validation, the first local PDF path was found to contain a zero-byte
placeholder even though its intended page count and hash had been recorded.
The placeholder was not accepted as evidence: it was replaced from the public
arXiv source, then independently checked with `pdfinfo` (title, authors, 28
pages, 3,737,273 bytes), `sha256sum`, and text extraction. The DOI publication
metadata was verified separately against ACM/Crossref. The hash above now
matches the actual local file.

An initial verbose formulation pushed the Conclusion to page 8. It was replaced
with shorter, meaning-equivalent definitions; no formatting workaround or font
shrinkage was introduced.

## Experiment decision

Step 0044 found no paper-level fatal evidence gap that justifies a new benchmark
or another custom metric. The current RQ2 comparison already uses complete
released populations, standard MAP, and an information-matched raw-action
organization. A further same-trajectory process/phase comparison remains only
an optional diagnostic if its data is naturally available and it could change
the paper-level conclusion. It is not required to close this WRITE step.

## Pending independent audit

The independent scientific review closed all Step 0044 defects and scored the
paper 6/10 borderline Weak Accept with zero must-fix. The preservation review
passed after two precise source/terminology repairs. The format review initially
rejected four `arraystretch` overrides; they were removed, repetitive prose was
meaning-preservingly compacted, and the final format re-review passed with zero
must-fix. Full records are under
`docs/tmp/review/step-0047-20260717T153618-0700/`.
