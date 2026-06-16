# R210 OSDI Gate Review: Reversible Display Map

Date: 2026-06-15

Scope: read-only review of `docs/visexp/r209_reversible_display_map.py`, the
R209 generated artifacts, verifier checks, unit tests, paper text, and claim
audit text.

## Review Findings

1. The R209 mechanism itself is correctly scoped as a reversible display-map
   contract: it reads generated R196/R203/R205 artifacts, keeps raw traces and
   the canonical map untouched, uses only existing `auto_canonicalize_existing`
   overlays for active labels, and keeps regenerated labels candidate-only.

2. The initial verifier was too aggregate-heavy. It checked global coverage and
   support totals, but did not recompute every display row from R196/R203. This
   was a medium-risk gap because a row-level active-tag or candidate-provenance
   bug could pass the old summary checks.

3. The initial drilldown CSV used a top-k raw-tag string even though the text
   described raw-tag drilldown. This was a medium-risk artifact-boundary issue:
   full reversibility existed through `active-display-map-r209.csv`, but not
   inside the drilldown row itself.

4. The initial future diff path trusted `promotion_label == promote` too much.
   A strong promotion should require final consensus or adjudicated R203
   evidence before a reviewed display-map diff is emitted.

5. No material overclaim was found in the claim/paper text. The risky wording
   was around "strengthens aggregation" and "increases aggregation coverage";
   the defensible wording is display-layer auditability, not semantic quality or
   user utility.

## Applied Revisions

- R209 drilldown rows now store complete raw-tag membership for each display
  bucket, while profile fields remain top-k summaries.
- R209 reviewed diffs now require `promotion_label=promote`,
  `promotion_final_source in {consensus, adjudicated}`, and
  `label_state=final`.
- R209 exposes only grammar-valid regenerated outputs as candidate display tags.
- `verify_artifacts.py` now recomputes row-level active display labels,
  active source, support, review flags, long-tail flags, candidate provenance,
  complete drilldown membership, and strong-review backing for diff rows.
- Unit tests cover candidate-only behavior, complete raw-tag drilldown beyond
  top-k, strong reviewed diffs, and weak single-label rejection.
- Paper and audit wording now frame R209 as an auditable display overlay and
  explicitly avoid adequacy, merge-quality, promotion-quality, or utility claims.

## Gate Decision

R209 is a defensible mechanism artifact for C3's display-layer aggregation
contract, but it is not standalone OSDI novelty and does not upgrade C5 or C6.
It remains useful only as part of the broader lifecycle:

`raw tag -> governance action -> candidate regeneration -> strong promotion review -> reviewed display-map diff -> canonical display overlay`

The project still needs real C5 participant responses and C6/R190/R203 human
labels before any weak-accept claim.
