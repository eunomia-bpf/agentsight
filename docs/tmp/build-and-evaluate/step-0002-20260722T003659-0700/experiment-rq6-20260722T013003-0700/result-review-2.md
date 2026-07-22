# RQ6/F9 Independent Result Review — Round 2

**Reviewed:** 2026-07-22  
**Scope:** targeted follow-up of the Round-1 figure blockers, regenerated CSVs,
PDF/PNG, implementation, and updated command/hash record  
**Verdict:** **PASS**

## Decision

The repair closes both Round-1 blocking defects without changing the frozen
corpus, signal extraction, counts, or stop decision. F9 now distinguishes
unavailable vendor strata from observed zero-event cells, exposes its exact
event-count color mapping, remains legible at paper width, and regenerates
deterministically from the frozen CSVs. It is valid for paper integration as a
coverage-only measurement-boundary figure, not as a skill/harness association
result.

## Round-1 closure

| Round-1 finding | Repaired behavior | Judgment |
|---|---|---|
| Missing project/vendor strata rendered as zero | Availability is derived from positive admitted-session rows; unavailable cells are masked gray and labeled `gray=N/A` | Closed |
| No event-count mapping in Panel B | Available cells encode `log1p(unique_event_ids)` and a labeled colorbar maps ticks back to counts 0, 1, 3, 10, 30, 100, and 300 | Closed |
| Duplicate top-level in-figure title | Removed; panel labels and stop banner remain | Closed |
| Regeneration/hashes needed after repair | Four CSVs, result report, and PNG reproduce byte-identically; hashes in `commands.log` match current artifacts | Closed |

## Independent checks

### N/A versus observed zero — pass

The session-coverage table has exactly seven absent project/vendor strata:

- ActPlane/Gemini;
- eunomia.dev/Claude and eunomia.dev/Gemini;
- AgentSkill paper/Codex and AgentSkill paper/Gemini; and
- Writing skills/Codex and Writing skills/Gemini.

The implementation masks all nine kind-by-status cells for each absent stratum,
for 63 N/A cells total. Visual inspection of both PNG and PDF confirms that
these form the expected seven gray vendor blocks. Available zero-count cells
remain the lightest blue rather than gray. The axis explanation states
`gray=N/A`, so unavailable coverage is no longer presented as observed absence.

### Event-count color scale — pass

Panel B uses `np.log1p` on the exact `unique_event_ids` values, masks N/A before
rendering, and labels the colorbar `unique events (log1p color)`. The displayed
tick positions are computed with the same transform and the tick labels report
the corresponding raw counts. The scale reaches 300 within the observed range;
the darkest cells and genuine zero cells are visually distinct. No association
effect or outcome quantity is implied.

### Readability and stop language — pass

The duplicate figure-level title is gone. Panel A retains exact session
numerators/denominators; Panel B identifies vendor, kind, status, N/A, and the
count scale; Panel C retains row totals and says its 60 bins are merged action
order rather than wall-clock time. The PDF remains exactly 7.05 inches wide
with embedded TrueType fonts and declared labels at or above 7 pt. At full-size
PNG inspection, the colorbar, gray N/A blocks, axis key, row labels, and red
`ASSOCIATION ANALYSIS STOPPED`/unavailable-field notice are readable and do not
overlap.

### Hashes and determinism — pass

Current files match the updated `commands.log` hashes:

- CSVs remain
  `3f132177...`, `199f994d...`, `01a4d5e2...`, and `fddd3dcb...`;
- repaired PDF: `ffc4cca8...`;
- repaired PNG: `9e59d003...`;
- result report: `c7fc6ef5...`; and
- implementation: `27cf0322...`.

A fresh authoritative rerun produced byte-identical four CSVs, PNG, and result
report. The review rerun used 416,636 KiB peak RSS and 1.67 seconds wall time.
The already-disclosed PDF creation-metadata variation does not affect the
byte-stable CSV/PNG evidence anchors.

## Scope of the PASS

This PASS preserves the preregistered negative measurement result: Skill
names/arguments, model/configuration fields, repository-external instructions,
and proof of actual non-exposure remain unavailable, so no exposed/unexposed
comparison, association estimate, process outcome, bootstrap, causal claim, or
forest plot is admissible. F9 supports only the source-coverage stop and the
design requirement for a future enriched export.

## Result-review judgments

```text
run status: valid
tested hypothesis: supported — the frozen source fields are insufficient for a valid skill/harness association analysis
research value: supporting
paper impact: measurement/workload boundary for RQ6
next paper decision: integrate F9 with an explicit coverage-stop caption and retain all no-association limitations
```

