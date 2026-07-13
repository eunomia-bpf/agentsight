# Round 2 — Section and AAAI-27 Conventions

- Reviewer completed: `2026-07-13T07:56:06-07:00`
- Root edits completed: `2026-07-13T08:03:30-07:00`
- Reviewer skill: `check-paper-structure-flow`
- Asset skill additionally used: `paper-figures`
- Verdict: `REVISE`
- Post-round paper SHA-256: `ad50d729e0ad46c3f6e30cd3c97a0ad7ee52149b812745420f84e1ec3cf9d6ab`

## Reviewer findings

The reviewer read the complete current paper/bibliography, venue files, user and idea locks, prior round reports, current PDF layout/fonts, and current official AAAI-27 submission/double-blind instructions.

The paper already passed title, anonymity, one-paragraph abstract, section order, two-object model, exact four-RQ count, main-content/total page limits, Letter size, embedded fonts, no page numbers, and exact-thesis conclusion opening.

It found the following must-fixes:

1. AAAI disables section numbering by default, so every `\S\ref` rendered as an empty `§`.
2. `pgfplots` is disallowed by the official template and was unused by the paper.
3. Result PDFs embedded CID/Identity-H fonts; the in-source architecture figure was scaled below the minimum readable font size.
4. RQ subsection headings were questions instead of descriptive noun phrases.
5. Design requirements structurally lived inside Background rather than opening Design.
6. Table 1 placed its caption above the table and scoped `\small` over the caption.
7. Evaluation lacks verified hardware/software/run-protocol setup needed for final reproducibility packaging.

Should-fixes included float-reference order, a more descriptive Algorithms title, thematic Related Work paragraphs, acronym introductions, and parallel RQ closes.

## Applied paper changes

- Enabled section/subsection numbering with `\setcounter{secnumdepth}{2}` in the paper source; no style file changed.
- Removed the unused `tikz` and forbidden `pgfplots` imports from `main.tex`.
- Moved the unchanged `Design Requirements for Agent Profiling` subsection to the beginning of Design.
- Renamed `Algorithms` to `Intent Attribution and Stack Construction`.
- Converted the four RQ headings to noun phrases:
  - `RQ1: Resource Attribution`;
  - `RQ2: Real-Problem Localization`;
  - `RQ3: Tag Accuracy`;
  - `RQ4: Profiling Cost`.
- Restated each complete fixed question in its opening prose, preserving number, order, and meaning.
- Moved the Table 1 caption and label below the tabular; scoped `\small` to the tabular only.
- Moved the existing Table 1 and RQ3-figure introduction sentences before their floats.
- Added a neutral pre-float introduction for the three population-level flame graphs.
- Split Related Work at its three existing thematic boundaries without changing comparison sentences or citations.
- Expanded first main-text `LLM` and `TF-IDF` uses once.

## Figure compliance work

`paper-figures` required both design-diagram and result-plot guidance because all paper figures were audited.

### Result plots

`figures/make_rq_figures.py` remains the single source of the two numerical plots. It still uses the same hard-coded historical data values; no plotted value, label meaning, axis, baseline, or claim changed.

Changes:

- enabled LaTeX text rendering so output uses embedded Type 1 fonts rather than CID/Identity-H fonts;
- regenerated near the measured single-column width;
- raised tick/legend sizes so effective printed text remains above 7 pt;
- retained vector PDF and matching PNG outputs.

Generated hashes:

- RQ1: `b62f691e728b8a2caa66a007b35187a79d06796f14321058fcfc43fac9c8a95f`;
- RQ3: `e54844e87558eba61541ed0bb54c49092b629d9531cfac07615886e2bd6a60cc`.

### Architecture diagram

The design diagram retains the same pipeline but is now a normal, pre-generated vector PDF at final two-column scale. It contains five ordinary stages already described in the text:

> Agent histories/public datasets → parse to operations → intent attribution → stack construction → folded profiles

The figure introduces no mechanism, boundary, claim, result, or abstraction. Its source is `figures/fig-architecture.tex`, wrapped by `figures/fig-architecture-standalone.tex`; `main.tex` imports `figures/fig-architecture.pdf` as `figure*`. Effective labels are at least 9 pt and fonts are embedded Type 1.

Generated architecture hash: `f90eb23d2744eb07076ea0e8f533598ef28d7f2ccd0ec5c95966307eece80abd`.

Visual inspection of compiled pages 5–7 confirmed that the architecture, both plots, labels, captions, and Table 1 are legible at normal page scale.

## Deferred submission items

- Verified hardware/software/run protocol: not fabricated. It must be populated from complete experiment records after the scientific evidence is reconciled.
- Reproducibility checklist: the supplied separate checklist remains to be completed at submission packaging time.
- PDF metadata cleaning: defer to final anonymous-submission packaging.
- Discussion/Limitations: defer to whole-paper REVIEW; no internal negative result or invented limitation enters during writing.
- Parallel RQ close and abstract/conclusion RQ4 coverage: routed to later writing rounds.

These deferred packaging/evidence items do not authorize a scientific rewrite and do not invalidate the completed presentation fixes.

## Compliance verification

`cd docs/paper && make` succeeded.

- PDF: 8 pages, US Letter, 1,641,886 bytes;
- page 8: references only;
- main content and conclusion end on page 7;
- section references render with numbers such as `§2`;
- every font in the compiled PDF is embedded Type 1;
- no CID/Identity-H or Type 3 fonts remain;
- no unresolved citation/reference or undefined-control-sequence warning;
- bibliography hash unchanged;
- no style/spacing/font-size modification.

## Scientific-lock audit

- Thesis unchanged verbatim.
- Four RQs unchanged in count, order, meaning, and evidence.
- No number, dataset, baseline, metric, hypothesis, conclusion, evidence status, or citation changed.
- No new abstraction or fifth RQ.
- No negative intermediate result.
- No citation or bibliography deletion.
- Submodule, idea history, user instructions, and shared skills untouched.
- No Git operation.
