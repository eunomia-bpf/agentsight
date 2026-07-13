# Independent Canonical Story Fidelity Audit

**Completed:** 2026-07-12T19:59:00-07:00  
**Reviewer:** fresh read-only subagent  
**Fixed source:** `docs/agentpprof-paper/main.tex`  
**Verdict:** **REPAIR**

## Scope And Disclosure

The reviewer read the complete user instructions, idea story, read-only
submodule paper, active paper, evaluation, literature, design, implementation,
AGENTS, and direct user disposition. It performed no edit, Git operation,
compilation, skill change, or submodule operation. This was a fidelity audit,
not an idea review; it proposed no replacement story.

## Overall Finding

The active paper has restored the canonical scientific spine. The title,
abstract, introduction, Background and Motivation, two-object Design, three
contributions, exact four RQs, and conclusion are faithful to the untouched
submodule. The paper is no longer centered on intervention or hierarchy
selection.

One residual matched-view framing block, one implementation overclaim, and
positive-number provenance still require bounded repair. These defects do not
authorize another story rewrite.

## Component Findings

| Component | Verdict | Finding |
|---|---|---|
| Title | PASS | Exact submodule title restored. |
| Abstract | PASS | Preserves long-running stakes, profiling gap, semantic challenge, operations, operation stacks, AgentProf, and four evaluation dimensions. |
| Introduction | PASS | Preserves context, stakes, debugging/profiling gap, challenge, transferable profiling method, two-object model, system, and four RQs. |
| Background and Motivation | PASS | Preserves two layers, aggregate profiling distinction, single-run tracing limit, two challenges, and three requirements. |
| Design | PASS | Operations and operation stacks are the only core abstractions; other elements are mechanisms. |
| Implementation | REPAIR | Direct AgentSight ingestion is overstated. |
| Contributions | PASS | Exact model/system/evaluation chain. |
| RQs | PASS | Exact four headings and restored attribution/localization/tag/cost meaning. |
| Conclusion | PASS | Exact thesis, two-object model, four dimensions, and profiling/debugging complementarity. |

## Must-fix Repairs

### M1 — Residual global matched-view framing

The Evaluation setup globally says every complete experiment compares three
attribution structures. That belongs to the superseded hierarchy-selection
story and is false for RQ1, RQ3, and RQ4. Replace it with RQ-specific controls:
hold visible inputs fixed within each comparison; use reference annotations
only for scoring; state each RQ's distinct baseline/protocol.

### M2 — Direct AgentSight-reader overclaim

The paper says AgentProf reads AgentSight recordings directly, while the
implementation frontier says AgentSight evidence must first be converted to a
supported operation or trace input. Correct the paper.

### M3 — Historical RQ3 positive transfer claims

The active paper renders 7/9 V-measure, 6/7 boundary-F1, and 4/5 backend-win
claims and says they establish transfer. Development-history contamination
means these are not yet the clean frozen target-blind experiment required by
the current RQ3. Remove the rendered numbers/figure and keep only the positive
held-out protocol until a clean experiment completes.

### M4 — Provenance for retained RQ1 numbers

The RQ1 interpretation is safely narrowed to conservation and declared-category
separation, but the canonical frontier lacks exact raw paths for its numeric
values. Add an admitted-evidence entry with input, commands/configuration,
metrics, oracle relationship, baselines, and raw paths, or remove the numbers.

### M5 — Zero-weight boundary

The model permits nonnegative weights but the current importer normalizes zero
to one. State that admitted results use positive integer weights and exclude
zero-valued measures.

## Final Determination

The canonical story itself is restored and must not be rewritten again. Repair
only M1--M5, then rerun a bounded fidelity audit against the same fixed source.
