# Round 0 — Macro Structure

## Node identity

- **Started:** 2026-07-17T08:04:00-07:00
- **Completed:** 2026-07-17T08:15:50-07:00
- **Parent:** Step 0040 WRITE gate
- **Objective:** audit and repair Level-1 paper structure without changing the
  thesis, four RQs, technical model, quantitative evidence, or story.
- **Entry baseline:** `4f9106a8dd91edd54815f5dccc73c2c54fdbe071`
- **Reviewer:** independent read-only subagent invoking
  `check-paper-structure-flow` in Level-1 macro scope.
- **Format interpretation:** AAAI-27 is a seven-content-page full conference
  paper rather than a workshop paper. The full-paper section roles were used,
  while the official 7+2 page budget governed space decisions.

## Material read

The root and reviewer read the complete `docs/paper/main.tex`, rendered
`main.pdf`, all figures and tables, the full `check-paper-structure-flow`
instructions and full-paper reference, `docs/user-instruction.md`, the complete
`docs/idea-story.md`, and the Step 0039 independent AAAI review. Existing
Step 0037 result reviews supplied the only newly surfaced RQ2 values.

## Raw independent findings

### Must-fix

1. **Related Work was structurally starved.** Its roughly 83 words did not
   position AgentProf against the closest observability, cross-run grouping,
   profiling, and diagnosis work. The reviewer requested three compact
   claim-oriented topic paragraphs rather than a paper list.
2. **The Conclusion omitted empirical synthesis.** Its 13-word body repeated
   the thesis and mechanism but did not close the evidence chain.
3. **RQ2 buried its strongest completed baseline analysis.** Table 2 showed
   only semantic-only versus raw action, while local-plus-semantic,
   local-plus-raw, and local-only remained in prose.

### Should-fix

1. Move the empirical flamegraph figure out of the Design-page opening so that
   the architecture diagram is the first visual inside Design.
2. Compress repeated RQ1 setup and answer prose and spend the space on the
   acceptance-changing comparison and conclusion.
3. Add a compact end-of-Evaluation synthesis and explicit RQ2/RQ4 scope instead
   of creating a large new Discussion section.
4. Let the RQ1 attribution table float rather than forcing a blank region with
   `[H]`.

### Consider

1. Merge the short `LLMs and AI Agents` background subsection into `System
   Profiling`.
2. Add a representative-operation walkthrough to Design.

## Applied fixes

### RQ2 evidence block

Table 2 now reports one standard primary metric, MAP, for semantic-only, raw
action, local-plus-semantic, local-plus-raw, and local-only rankings. The
semantic/raw columns remain the primary comparison; the local-first columns
are explicitly labeled post-hoc. Exact values came from the independently
reconstructed Step 0037 report:

| Workload | Semantic | Raw | Local+semantic | Local+raw | Local-only |
|---|---:|---:|---:|---:|---:|
| AgentProcessBench | .789 | .773 | .896 | .893 | .863 |
| HINTBench | .452 | .281 | .545 | .506 | .411 |
| TraceElephant | .230 | .121 | .322 | .249 | .209 |

The prose retains the three primary paired intervals, the HINTBench and
TraceElephant matched local-plus-raw gains, the AgentProcessBench
indistinguishable interval, and the adaptive qualifier. No Recall@20, reader
metric, or new score was promoted.

### Closest-work structure

The existing three-topic Related Work organization was retained and expanded
into `Agent observability`, `Cross-run agent analysis`, and `Profiling and
diagnosis`. Five verified sources were added with annotated bibliography
entries: TraceProbe, WebGraphEval, Hodoscope, TraceGraph, and OpenTelemetry
Profiles. The text explicitly concedes that semantic grouping, metric rollups,
profile naming, pprof compatibility, trace linkage, canonical actions, and
cross-run graph structure are established components. It defends the surviving
combination: source-linked heterogeneous effects, exact conservation of
arbitrary additive measures, and selectable operation-stack projections over
one corpus. This makes the original story more visible; it does not replace it.

The Introduction's existing-solutions paragraph received the same concise
boundary so the contribution is not discoverable only on the final page.

### Evidence synthesis and conclusion

An `Evidence synthesis` paragraph now states the four distinct construct links:
RQ1 lineage/conservation plus responsibility partitions, RQ2 standard problem
ranking plus local-evidence refinement, RQ3 literal and structural field modes,
and RQ4 fixed-input construction. Scope and Limitations now states the RQ2
population/adaptive-analysis boundary and RQ4's construction-only boundary.

The Conclusion is one evidence-bearing paragraph. It preserves the exact
thesis, the two core objects, existing positive RQ1/RQ2 results, the existing
OSWorld-Human result, and the existing 1.17-second construction result.

### Layout and balance

The flamegraph block moved from the Introduction/Design boundary to RQ1's
multi-weight evidence, without changing any image, caption, number, or
cross-reference. The RQ1 table changed from `[H]` to `[tb]`. Repeated RQ1 view
and answer prose was tightened while retaining all nine named families, all
five group counts, the 7/10 overlap, Spearman correlation, 8th/93rd rank
reversal, all three token-allocation support, and the direct RQ answer.

## Rejected or deferred findings

- **Background subsection merge — rejected.** `LLMs and AI Agents` establishes
  the two activity layers consumed by the later AgentSight/source-linkage path,
  whereas `System Profiling` establishes folding and call-stack semantics.
  Merging them would mix two load-bearing concepts for negligible space gain.
- **Representative-operation walkthrough — deferred.** The four-stage pipeline,
  architecture caption, and operation/operation-stack subsections already
  explain the path. Adding another walkthrough before later micro review would
  duplicate rather than clarify it.
- **Standalone Discussion — rejected.** The seven-page AAAI budget does not
  justify a new section; the evidence synthesis and scope block supply its
  required logical role.

## Preservation audit

- The exact thesis remains unchanged.
- The four explicit RQs remain byte-identical and in the fixed order.
- Operations and operation stacks remain the only core abstractions.
- No algorithm, experiment, dataset, metric, or result value was changed.
- Citation commands increased from 54 to 57; none was removed.
- `docs/agentpprof-paper` and all skills remain untouched.

## Compilation and page evidence

`make` completed all four LaTeX/BibTeX passes. The final pass reports no
undefined citation, undefined reference, or overfull box, and the PDF remains
US Letter. All new references resolve.

The first build is **10 pages**, not the required nine: the manuscript body now
extends into page 8 before references. This is an explicit unresolved Round 0
space defect, caused by making the acceptance-changing closest-work and
evidence synthesis visible. Later micro, section-convention, and language
rounds must recover roughly one column of body space through meaning-preserving
compression; they may not drop the new novelty boundary, RQ2 table, or evidence
chain. The final WRITE gate cannot pass until the body again ends on page 7 and
references fit on pages 8--9.

### Subsequent direct-instruction supersession

During Round 1, the user explicitly prohibited token-weighted B$^3$ and
project-specific reader/budget metrics from the paper. The root therefore
removed the token-weighted RQ1 analysis and its citation rather than preserving
the Round 0 state described above. Recall@20\% and fixed-reader results had not
entered the paper and remain absent. Ordinary B$^3$, MAP, V-measure,
macro-F1/accuracy, exact boundary precision/recall/F1, and construction cost
remain. This note preserves the historical Round 0 decision without presenting
it as the current manuscript state.

## Next node

Round 1 performs a fresh micro-structure and paragraph-role review. It should
prioritize duplicate setup/result restatement and paragraph-role violations
that can recover page space without deleting evidence or narrowing claims.
