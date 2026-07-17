# Step 0043 — Independent AAAI-27 Format, Figure, and Table Review

## Review identity

- **Gate:** REVIEW
- **Scope:** read-only format, figure, and table audit of
  `docs/paper/main.tex` and the already-built `docs/paper/main.pdf`.
- **Rules used:** the official AAAI-27 author-kit requirements recorded in
  Step 0041 and the complete `paper-figures` skill, including both
  `references/design-diagrams.md` and `references/result-plots.md`.
- **Scientific invariants:** preserve the exact thesis, “Agent observability
  needs profiling, not only debugging.”, and the four RQs in their fixed order:
  attribution, localization, tag accuracy, and cost.
- **Mutations:** none to the paper, figures, tables, bibliography, experiments,
  or submodule. This review performed no Git operation.

## Material inspected

I read the complete nine-page compiled manuscript and its complete LaTeX
source, visually inspected every technical page at 150 dpi, inspected each
figure and table at its final placement, checked the PDF metadata and embedded
fonts, searched the paper and architecture source for forbidden constructs,
and compared all three paper flamegraphs node by node with their exact SVG
sources under `docs/flamegraph-example/`.

The authoritative format rules used here are:

1. at most seven pages of technical content and at most nine pages total, with
   pages after page seven containing references only;
2. anonymous two-column US-Letter submission with embedded Type 1 or TrueType
   fonts;
3. no `float` package or `[H]`, no `\\resizebox`, no LaTeX
   `trim`/`clip`/`viewport`, table text at least 9 pt, and figure labels at
   least 9 pt; and
4. the separate reproducibility checklist remains a separate artifact rather
   than entering the nine-page manuscript.

## Official-format audit

### Pagination and paper geometry — PASS

- `pdfinfo` reports **9 pages** and a page size of **612 × 792 pt**, exactly US
  Letter.
- Pages 1–7 contain the complete technical paper. Page 7 ends with the full
  Conclusion; no sentence, float, footnote, appendix, or other technical
  material spills to page 8.
- Page 8 begins with the `References` heading and pages 8–9 contain references
  only.
- The two-column layout, margins, title block, and anonymous author block render
  normally. No page numbers or acknowledgments appear.
- The checked-in `aaai2027.sty` and `aaai2027.bst` retain the official hashes
  recorded in Step 0041:
  `391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`
  and
  `5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`.

### Fonts and build diagnostics — PASS

- `pdffonts` reports only embedded, subset Type 1 fonts. There are no Type 3
  fonts and no unembedded fonts.
- The existing build log contains no overfull boxes, undefined references,
  undefined citations, or fatal errors. It has several underfull-box notices,
  but visual inspection shows no collision, clipping, or margin violation;
  underfull boxes are not a format blocker.

### Forbidden constructs — PASS

A source search over `main.tex` and `fig-architecture.tex` is empty for:

- the `float` package and `[H]` placements;
- `\\resizebox`, `\\scalebox`, and explicit `\\fontsize` overrides;
- LaTeX `trim`, `clip`, or `viewport` image cropping;
- `\\tiny`, `\\scriptsize`, and `\\footnotesize`; and
- negative spacing or page-geometry manipulation.

The architecture and flamegraph figures use normal `[t]` placement, and all
four tables use normal `[tb]` placement.

## Figure audit under `paper-figures`

### Figure 1: architecture/pipeline — PASS

- **Claim and role:** the figure explains the concrete end-to-end AgentProf
  pipeline used by the Design/Implementation text: local or public histories
  become uniform operations, fields are derived, stacks are constructed and
  folded, and profiles are exported.
- **Text linkage:** the Introduction explicitly cites Figure 1 when introducing
  the implementation; the caption and surrounding implementation prose explain
  what enters, what each stage does, and what exits.
- **Abstraction and complexity:** the diagram has six reader-facing components,
  below the skill's eight-component limit. It presents the system pipeline,
  not code-level APIs or experimental numbers. A security/trust boundary is not
  part of the claimed mechanism, so omitting one does not hide a design claim.
- **Terminology:** `Local Histories`, `Operation JSONL`, `Uniform Operations`,
  `Field Derivation`, `Stack Construction + Folding`, and `Profiles` match the
  paper's prose and caption.
- **Placement and scale:** it is a native-size `figure*` at the top of page 4;
  no shrinking command is used. All nodes, annotations, and arrow labels use
  `\\small`, which is 9 pt under the 10-pt AAAI body size. At 100% scale the
  labels and arrows are clear and do not collide.
- **Caption:** self-contained and explains both input routes, the shared
  representation, the processing path, and output.

### Figure 2: three flamegraph panels — PASS

- **Claim and role:** the figure supports RQ1's claim that selectable stack
  fields and additive measures expose different responsibility and bottleneck
  views over the same operation corpus. The prose defines the three measures
  before interpreting their differences; the caption identifies the corpus,
  panel order, width semantics, and controlled differences.
- **Text linkage:** it is cited in both the conceptual introduction to operation
  stacks and the RQ1 analysis. The RQ1 prose interprets the time-versus-token
  differences rather than duplicating the picture.
- **Final readability:** the three panels span both columns on page 5. Their
  broad hierarchy labels and rows are legible at 100% zoom; labels that cannot
  fit inside narrow rectangles are omitted or shortened rather than printed
  below the legibility floor. `pdfimages` reports 476 ppi, above the skill's
  300-dpi floor for a genuinely dense raster visualization.
- **Effective label size:** the paper SVG uses 24-unit labels at width 1200,
  rasterized to 3000 pixels. At the PDF's measured 476 ppi, this is
  `24 × (3000/1200) × 72/476 = 9.076 pt`, satisfying the official 9-pt figure
  label minimum.
- **No misleading visual encoding:** widths carry the additive measure; colors
  distinguish hierarchy nodes but are not claimed as an extra quantitative
  scale. The panels do not require an axis or error bars because they are
  exact folded profiles rather than estimates of repeated measurements.
- **Dense-raster exception:** the skill prefers vector PDF for ordinary result
  plots but explicitly permits high-resolution raster for genuinely dense
  visuals. These 940-, 865-, and 2,051-node flamegraphs qualify, and the exact
  SVG sources plus the rendering script remain adjacent to the paper assets.

### Flamegraph geometry and data preservation — PASS

I compared each source group with the corresponding group in the paper SVG.
For every node, the complete `<title>` text (including hierarchy, value, unit,
and percentage), rectangle `x`, rectangle `width`, fill, stroke, stroke width,
and corner radii are identical:

| Panel | Source nodes | Paper nodes | identity mismatches | row remap |
|---|---:|---:|---:|---|
| tokens | 940 | 940 | 0 | one-to-one, monotone |
| time | 865 | 865 | 0 | one-to-one, monotone |
| files | 2,051 | 2,051 | 0 | one-to-one, monotone |

The canvas width remains 1200 in every pair. The only geometric change is the
documented row mapping from each old y coordinate to a uniformly expanded
24-unit row with a one-unit gap; row ordering is unchanged. The transformation
removes title/metadata bands and changes label presentation, but it does not
add, remove, reorder, resize, or reweight any flamegraph node. The PNGs included
by LaTeX visually match these transformed SVGs and have the expected 3000-pixel
widths and row-derived aspect ratios.

## Table audit — PASS

- All four tables use `\\small`, i.e. the permitted 9-pt table size; no table
  uses `\\scriptsize` or a resize command.
- Tables 1–4 are fully inside their columns, with no clipped rule, cell, header,
  value, or caption. All decimal values and confidence intervals remain
  readable at 100% zoom.
- Table 1 presents exact B³ precision/recall/F1 values for RQ1; Table 2 presents
  exact MAP values for RQ2; Table 3 presents exact boundary and partition
  agreement for RQ3; and Table 4 presents exact operations, time, and peak-RSS
  values for RQ4. Exact lookup is therefore more useful than replacing these
  compact discrete comparisons with plots.
- Captions identify the RQ, population or measurement, metric meaning, and
  comparison direction where needed. The tables do not duplicate a plotted
  version of the same data.

## Scientific-invariant check

- The exact thesis appears unchanged in the Abstract, Introduction, and
  Conclusion.
- The evaluation still states exactly four RQs in the fixed order:
  1. resource attribution;
  2. correspondence to real problems;
  3. tag accuracy; and
  4. profiling cost.
- This format review made no scientific or narrative edit.

## Verdict

**PASS.** There are **zero format, figure, or table must-fix items** under the
official AAAI-27 rules recorded in Step 0041 and the `paper-figures` audit
criteria. The five Step 0041 violations are repaired without changing the
paper's thesis, RQs, claims, evidence, or flamegraph geometry/data. The format
REVIEW node may close and the manuscript may proceed to the independent
whole-paper AAAI scientific review.
