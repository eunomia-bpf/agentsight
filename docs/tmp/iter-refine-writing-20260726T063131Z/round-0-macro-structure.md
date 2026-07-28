# Round 0 — Macro structure

Started: 2026-07-26 06:31 UTC.  
Objective: compress the AAAI-27 submission to at most seven content pages and
two reference-only pages while transferring every removed claim to a
standalone supplement.

## Entry evidence and constraints

The entry paper was `docs/paper/main.tex` (SHA-256
`50a909f19d349ca8e641e45333cfd82f336d0cf2726e032648c90fc447721be1`)
and compiled to 17 pages: 16 content pages and one reference page.
`docs/evaluation.md` is the authoritative quantitative record. The user
forbids Git commands, so this run uses the entry hash, the unchanged extended
paper in `supplement.tex`, and a claim-transfer audit instead of a Git
baseline.

The scientific contract contains six fixed RQs. Although the generic writing
workflow prefers two to five, this user-authorized set is read-only and will
not be merged, split, renamed, or dropped.

## Findings and target outline

Must-fix:

- Eleven large result figures consume approximately nine content pages,
  including pages containing only delayed floats. Keep at most two compact,
  claim-central figures in the main paper and move every other figure and its
  detailed interpretation to the supplement.
- Problem Setting, Method, and Implementation repeat the same source-projection
  boundary. Merge them into one approximately 1.25-page method section.
- The empirical section repeats protocols and qualifications for every RQ.
  Preserve the six RQs but compress each answer to its strongest result and
  state the shared coverage/causality boundary once.
- The conformance experiment is currently embedded after all RQs. Give it a
  distinct short section with the required frozen failure, taxonomy, and
  repaired result.
- Force the bibliography to a new page after all floats have been flushed so
  no content can spill onto pages 8–9.

Should-fix:

- Compress the case table and detailed inclusion protocol into prose in the
  main paper; retain the full table in the supplement.
- Merge threats and ethics into a compact final section while retaining the
  exact “author-associated local projects” anonymity framing.
- Consolidate repeated novelty disclaimers into one related-work paragraph and
  one validity paragraph.

Target allocation:

| Main block | Pages |
|---|---:|
| Abstract + introduction | 1.2 |
| Workspace projection and source-linked protocol | 1.25 |
| Corpus, RQs, and strongest findings | 2.7 |
| Measurement-capability conformance | 0.7 |
| Threats + ethics | 0.45 |
| Related work + conclusion | 0.45 |
| Float/layout allowance | 0.25 |

Retain in main: `rq1-activity-progress.pdf` and the compact
`rq7-measurement-capability.pdf`. Move all other empirical and schematic
figures to the supplement. The supplement will be the unchanged extended
paper with a supplementary title, making the claim-transfer mapping
lossless by construction.

## Application plan

1. Preserve the entry paper as `supplement.tex`, changing only its title.
2. Build a compact `main.tex` in section-sized blocks: opening; method; study;
   conformance; threats/ethics; related work; conclusion.
3. Compile both entrypoints and use per-page text extraction to classify
   content and reference pages.

No quantitative value or RQ meaning is authorized to change. No claims are
scheduled for deletion.
