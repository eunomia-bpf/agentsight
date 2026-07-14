# Round 5 — Cross-Paper Consistency

- Time: 2026-07-14T07:09:22-07:00
- Reviewer: independent subagent, read-only
- Reviewer method: complete-paper factual, terminology, ownership, figure, table, and repeated-number audit using `check-terminology-infoflow`
- Scope contract: local consistency only; no thesis, RQ, claim, result, experiment, or story change

## Independent verdict

MUST-FIX LOCALLY. The reviewer confirmed that the exact thesis, four fixed RQs, all claims, all reported results, and the positive story are consistent. The remaining defects concerned component ownership, the implementation map, and one architecture-figure input.

## Must-fix findings and actions

1. **AgentSight–AgentProf ownership contradiction.**
   - Finding: the RQ1 protocol and first Related Work paragraph correctly assign scoped capture/source lineage to AgentSight and semantic propagation/folding to \sys, but Operations, Input Reconstruction, and another Related Work sentence could imply that \sys discovers effect linkage.
   - Action: stated that source-linked tool invocations/effects enter as operations; \sys propagates semantic fields over those linked effects; Input Reconstruction reads source-linked AgentSight recordings. No end-to-end capability was removed.
2. **Operation-stack implementation mapping.**
   - Finding: the overview incorrectly mapped operation stacks to optional boundary construction plus serialization.
   - Action: mapped operation stacks to stack construction and folding, and mapped profile export only to serialization. Renamed the implementation paragraph to `Stack construction and folding` and described the already-existing direct field-list, supplied group-field, and automatic-boundary paths.
3. **Architecture figure omitted AgentSight.**
   - Finding: the caption named AgentSight recordings, but the active diagram showed only Local Histories and Operation JSONL.
   - Action: added an `AgentSight-Linked Effects` input into Uniform Operations; preserved the existing downstream pipeline. The compiled page was visually inspected and has no overlap or clipping.

## Should-fix findings and actions

- Replaced internal protocol phrases with reader-facing wording while retaining the fixed R114 identity, AgentSight 0.2.37 version, scoped process/tool definition, and source-lineage checker.
- Standardized the process as `concurrent negative-control process` and its observations as `negative-control effects` across Abstract, Introduction, RQ1, and Conclusion.
- Restored `session-held-out` in the Evaluation contribution.
- Identified `agentpprof` as the \sys executable at first RQ1 and RQ4 use, distinguishing it from AgentSight 0.2.37.
- Replaced the unexplained `agent-session parsing` caption phrase with `local-history parsing`.
- Used the full `AgentProcessBench` name in the RQ2 table.
- Standardized RQ3 prose and Conclusion to `operation-weighted B$^3$ partition F1`; the compact table header remains `B$^3$ F1`, with the caption defining its full meaning.

## Confirmed repeated facts

- R114: 20 tasks; 1,520 TP; 0 FP; 54 FN; 100.0% precision; 96.6% recall; 1,629 rejected negative-control effects; five preserved manifest categories.
- RQ2: workload totals and AP/work metrics agree across prose and table.
- RQ3: 287 sessions, 3,978 operations, 3,691 adjacent pairs, 2,042 groups, boundary and partition values, five folds, 2,249 stacks, and mass preservation agree.
- RQ4: 27,765 operations, 1.17 s, 464.5 MiB, 18.2% time, and 1.3% memory agree.

## Preservation audit

- Exact thesis unchanged.
- Four fixed RQs unchanged.
- RQ1 positive cumulative answer unchanged.
- No measured value, dataset, baseline, metric, mechanism, or experiment changed.
- Ownership is clearer without narrowing the paper's end-to-end result.

## Build and visual verification

- `make` and final `pdflatex` completed.
- PDF: 9 pages total (7 content plus 2 references).
- Citation commands: 52.
- Undefined citations/references: 0.
- Overfull boxes: 0 in the final pass.
- `git diff --check`: clean.
- Architecture figure visually inspected on compiled page 4: three inputs are readable and all arrows/pipeline boxes are intact.
- Exit `main.tex` SHA-256: `f0fdcfca2811d0a76ded9190381e136b3a167a3d33a50bf55084cb82862b6d91`.
- Exit `main.pdf` SHA-256: `97ba1ff079aa211810108faf701db386346e05f16ac8ef240e7cefb13e7aa315`.
- Exit architecture source SHA-256: `c848d5fb57da3769f6307c3f7519ed2279b6551ff381d67488d6020e3c78e234`.

## Round decision

PASS after local fixes. Proceed serially to the first sentence-level style round.
