# Step 0041 — AAAI-27 Format Audit

## Node identity

- **Started:** 2026-07-17T14:29:38-07:00
- **Parent:** Step 0040 WRITE
- **Gate:** REVIEW
- **Scope:** submission-format compliance only; no scientific or narrative
  review is authorized in this node.
- **Paper entrypoint:** `docs/paper/main.tex`
- **Entry PDF:** `docs/paper/main.pdf`
- **Repository HEAD:** `cfe62570412f90dc024beb34a458e6481404f1aa`
- **Branch:** `research/semantic-flamegraph-artifacts-v2`; this REVIEW node does
  not stage, commit, push, create, or switch branches.
- **Read-only story source:** `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

## Fixed scientific contract

This node preserves the exact thesis, **“Agent observability needs profiling,
not only debugging.”**, the four RQs and their order (attribution,
localization, tag accuracy, and cost), every claim, every number, every
qualifier, and the original submodule story. It may route the paper back to a
minimal WRITE repair for formatting, but it may not alter the paper's
scientific content.

The user-directed metric boundary is already satisfied: token-weighted
B$^3$, Recall@20\%, and fixed top-3/model-reader protocols are absent from the
paper. Paper-facing primary metrics are standard metrics with citations.

## Authoritative format sources

The audit uses only the official AAAI-27 sources:

1. [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/): seven pages of technical content and no
   more than nine pages total, with pages after page seven containing only
   references.
2. [AAAI-27 Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/): anonymous two-column US-Letter submission,
   embedded Type 1 or TrueType fonts, and the reproducibility checklist as a
   separate upload.
3. [AAAI-27 Author Kit](https://aaai.org/authorkit27/), especially
   `AnonymousSubmission2027.tex`: no `float` package or `[H]` placement, no
   `\resizebox`, no LaTeX `trim`/`clip`/`viewport` cropping, table text no
   smaller than 9 pt, and figure labels no smaller than 9 pt.

The checked-in `aaai2027.sty` and `aaai2027.bst` exactly match the official
kit. Their SHA-256 values are respectively
`391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`
and
`5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`.

## Entry audit

### Passing requirements

- `main.pdf` is nine US-Letter pages.
- All technical content, including the conclusion, ends on page seven; pages
  eight and nine contain only references.
- The submission is anonymous and contains no acknowledgments.
- `pdffonts` reports embedded Type 1 fonts and no Type 3 fonts.
- The official style and bibliography files are used unchanged.
- The separate reproducibility-checklist PDF exists.

### Must-fix violations

The source has five mechanical author-kit violations:

1. `\usepackage{float}` and four forced `[H]` placements;
2. `\resizebox{\linewidth}{!}` around the architecture diagram;
3. four result tables set in `\scriptsize`, below the 9-pt minimum;
4. three flamegraph panels cropped with LaTeX `trim` and `clip`; and
5. architecture annotations set in `\footnotesize` or `\scriptsize`, below
   the 9-pt figure-label minimum.

The flamegraph panels have exact vector sources under
`docs/flamegraph-example/`, generated from the same 325-history profiles and
matching the totals and visible structure in the checked-in PNGs. Therefore a
format-only repair can reuse those existing sources; no experiment or data
regeneration is needed.

## Routing decision

The REVIEW gate is **not complete**. Route to a minimal format-only WRITE node
that:

- removes `float` and replaces `[H]` with normal AAAI float placement;
- places the architecture figure at native size and raises every annotation
  to at least 9 pt;
- raises table text to 9 pt;
- creates externally cropped, paper-ready flamegraph assets from the existing
  exact vector sources and removes LaTeX cropping; and
- rebuilds and reruns page-count, font, overflow, forbidden-command, and
  submodule-integrity checks.

The repair must not change prose, claims, RQs, evidence, numbers, citations,
algorithms, or the read-only submodule. A fresh independent format review is
required after the repair.
