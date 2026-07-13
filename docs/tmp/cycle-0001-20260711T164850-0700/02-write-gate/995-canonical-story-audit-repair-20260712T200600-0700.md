# Canonical Story Fidelity Audit Repair

**Completed:** 2026-07-12T20:06:00-07:00  
**Parent audit:** `990-independent-canonical-story-audit-20260712T195900-0700.md`  
**Status:** M1--M5 repaired; independent re-audit pending

## Repairs

1. **M1 matched-view residue:** replaced the global three-structure Evaluation
   setup with RQ-specific controls. RQ1 uses four grouping projections, RQ2 uses
   hidden-annotation localization baselines, RQ3 uses a fixed held-out tagger,
   and RQ4 measures complete release-build cost. Visible inputs remain fixed
   within each comparison and annotations are scoring-only except explicit
   oracle upper bounds.
2. **M2 AgentSight ingestion:** corrected Implementation to say AgentSight
   recordings enter after conversion to a supported operation or trace input.
3. **M3 RQ3 historical positives:** removed the RQ3 figure, 7/9, 6/7, and 4/5
   results, and the rendered positive answer. The paper now specifies only the
   clean frozen target-blind held-out protocol and contamination checks.
4. **M4 RQ1 provenance:** added `docs/evaluation.md`'s admitted RQ1 mechanism
   evidence entry. It records the R170 collection command/path, R224 ablation
   command and raw paths, R251 permutation path, R225 measure-sensitivity path,
   exact metric interpretations, and dirty-provenance/construct boundaries.
5. **M5 zero weights:** stated that admitted results use positive integer
   weights and that imported zeros are currently normalized to one, excluding
   zero-valued-measure claims.

## Verification

The repaired paper was rebuilt through BibTeX and repeated pdflatex passes. It
is 7 US-Letter pages, with references beginning on page 6. The final log has no
undefined citation, undefined reference, changed-label warning, LaTeX error, or
emergency stop. `docs/paper/README.md` now records the current page layout.

No title, thesis, problem, contribution, RQ, or conclusion changed during these
repairs. No Git command, shared-skill edit, or submodule operation ran.
