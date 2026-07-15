# Round 10: Citation Verification

Reviewer mode: full mechanical and manual citation gate followed by an
independent read-only claim-alignment review

## Mechanical Verification

The mandatory `verify_bib.py` pre-check was run before manual annotation and
again after every active entry had been verified. The final run checked 20
entries and reported zero errors and zero warnings. All 20 entries carry
`VERIFIED`, `REAL`, `PDF`, `ABSTRACT`, and `USED_FOR` annotations. The paper
cites all 20 entries, and every cited key resolves to an entry.

Open-access copies of eight high-risk or method-relevant papers were retained
under the ignored `docs/reference/` directory for local full-text checks. The
BibTeX annotations remain the single source of truth; this round report records
the writing workflow rather than duplicating an entry-level citation ledger.

## Independent Reviewer Findings

### High risk

The paper called RECAP's shadow-repository edit evidence `ground truth` and
stated the closest-work boundary too broadly. RECAP observes higher-resolution
local edits, but its prompt-to-edit association is not causal truth and it also
studies a multi-week final product.

### Medium risk

The reviewer found an overly broad commit-centric characterization of all
historical visualizations, an inaccurate umbrella description of two
trajectory papers, a software-code generalization of History Flow's document
persistence encoding, an overly broad description of CLSA as a complete
lineage protocol, and several borrowed design mechanisms lacking nearby
citations.

### Low risk

`closest` baseline wording and the description of the evaluation-guidance
source were more categorical than the cited papers alone could establish.

## Root Decisions And Applied Fixes

- Replaced RECAP `ground truth` with higher-resolution observed shadow-
  repository edit evidence and narrowed the novelty boundary to cross-vendor
  native histories, candidate actual-Git associations, and a separately
  labeled endpoint-survival projection.
- Replaced the blanket commit-observation claim with repository-version or
  change-history language and developer identities.
- Described the trajectory papers as analyses and comparisons of trajectories
  and action sequences.
- Described History Flow as authored-content persistence and cited Hercules for
  software code-age burndown.
- Described CLSA as an AST-aware matching pipeline for separating deletion from
  migration and rewrite, not as this system's complete event-to-Git lineage.
- Added nearby citations for burndown, forensic hotspots, ownership/storylines,
  and refactoring-sensitive matching.
- Recast Githru as a strong baseline and tied task wording to general software-
  visualization evaluation guidance without attributing a fixed phrase to the
  source.

## Missing-Citation And Retraction Checks

The full paper was scanned for uncited historical mechanisms, adopted methods,
closest-work claims, baselines, and study guidance. The independent review did
not identify an uncited claim that blocks the current design paper after the
fixes above. DOI, arXiv, proceedings, and official-project metadata exposed no
retraction or withdrawal notice during verification; this is a metadata check,
not a guarantee about future status.

## Verification

The final mechanical run reported 20 checked entries, zero errors, zero
warnings, zero uncited entries, and zero missing entries. BibTeX plus three
LaTeX passes completed without undefined citations or references and produced
a seven-page PDF.
