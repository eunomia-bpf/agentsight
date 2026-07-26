# WRITE report — front-matter compression round 2 + reference field trim

Task: `docs/tmp/writing/write-front-round2-20260725T234500-0700/task-spec.md`
Files edited: `docs/paper/main.tex`, `docs/paper/references.bib`. No git commands.
Build: `pdflatex ×3 + bibtex`, clean (0 errors, 0 undefined citations/references,
0 bibtex warnings/duplicates).

## Invariants (all verified)
- Thesis sentence `Agent observability needs profiling, not only debugging.`
  appears verbatim **x3** (abstract, intro ¶5, conclusion).
- RQ1–RQ4 titles unchanged; contributions `\begin{enumerate}` (3 items) intact.
- All tables (4) and figures (3) retained; every number and `\cite` key preserved.
- Unique cite keys in `main.tex`: **44 before == 44 after**. Bib entries: 86 (none
  removed/renamed); only the named fields were deleted.
- All sigma/lambda symbol definitions retained: $A(n), g(n), E(n), \sigma(n), \|,
  \lambda(n), \varphi, w_r$.

## Per-section source-line deltas (baseline → current)
Measured on exact edited regions (baseline via `git show HEAD`).

| Section | Baseline | Current | Δ | Target Δ |
|---|---:|---:|---:|---:|
| Introduction ¶1–6 | 71 | 66 | **−5** | −10 |
| Background (System Profiling + Challenges) | 53 | 49 | **−4** | −6 |
| Design — Semantic Operation Stack Model | 35 | 33 | **−2** | −8 (model+A2) |
| Design — A2/CodeTraceBench paragraph | 11 | 11 | **0** | (part of −8) |
| Related Work | 41 | 39 | **−2** | −5 |
| Conclusion | 15 | 14 | **−1** | −4 |
| **main.tex total** | **1221** | **1207** | **−14** | −33 |
| **references.bib total** | **1308** | **1290** | **−18** | — |

The round-1 pass had already removed most connective tissue, so round-2 fusions
(fusing topic sentences via colons, folding the redundant "Profiling applies…"
bridge into the model sentence, merging the two intro mechanism definitions,
fusing the System-Profiling pipeline/tools sentences, the AgentSight sentence,
the sigma/lambda+consequence sentences, and the A2 worker/merge sentences) now
mostly re-flow rather than drop whole wrapped source lines; hence the realized
deltas land below the aspirational targets without cutting any claim, number,
citation, table, or figure.

## Fusions applied (as specified)
- Intro ¶3: standalone topic sentence folded into the responsibility sentence
  (colon). Intro ¶4: opening sentence folded into the tools sentence; dropped the
  elaborative "for monitoring and recovery" (covered in Related Work).
- Intro ¶5: removed the redundant bridge "Profiling applies to agents once a
  profiler projects…" by folding its mechanism clause into the model sentence.
- Intro ¶6: fused the two mechanism-definition sentences into one, keeping both
  `\emph{Operation annotation}` and `\emph{stack construction}` terms.
- Intro ¶7: filler-only ("compared with"→"vs.", dropped "materially"); numbers
  and citations untouched (¶7/¶8 otherwise untouched per spec).
- Background System Profiling: definition folded into the sample/attach/fold
  sentence; the tools sentence fused with "These tools start from…".
- Background Challenges: the two existing-tool / AgentSight sentences fused.
- Design sigma/lambda: collapsed the repeated "let … be", fused the
  $\sigma$/concatenation sentence with the $\lambda$ label sentence, and folded
  the trailing consequence sentence into it — all symbol definitions kept.
- Design A2: fused the worker/merge sentence with the "official stages remain
  hidden" sentence (405 / 5,537 / 1,434 / appendix ref all kept).
- Related Work: dropped the wordy "complements these grouping/rollup/…systems"
  recapitulations in all three paragraphs (citations all kept).
- Conclusion: fused to 4 sentences (≤6); thesis kept verbatim; tightened
  "folds covered source evidence under shared operation stacks across runs" →
  "folding covered evidence under shared cross-run operation stacks" and
  "After marks are fixed" → "With marks fixed".

## references.bib field trim
Removed `publisher`, `address`, `month`, and `series` from the
@inproceedings/@article entries that carry a `booktitle`/`journal` (venue
identity preserved): `kgent`, `weblinx`, `bagga-baldwin-1998-entity-based`,
`rosenberg-hirschberg-2007-v-measure`, `macqueen1967`, `mccallum-nigam-1998`,
`scienceworld`, `agentboard`, `bouzenia-pradel-2025-trajectories`,
`robertson2008ap`, `bouma2009npmi`, and `graphectory2026` (`month`). No `editor`
fields existed. The remaining `month` (apr) is in `@misc{qwen36}`, correctly
retained (task scopes removal to @inproceedings/@article).

## Page outcome (final PDF)
- **Total pages: 12** (appendix on pp. 11–12).
- **Body end page: 8** (Conclusion closes at page-8 lines ~71–79).
- **References start page: 8** ("References" heading at page-8 line ~81).
- **References end page: 10.**

### Target "body ends on page 7": NOT met (body ends on page 8)
The target is infeasible under the task's edit scope. Page 8 currently carries
~80 lines of body — RQ4 (most of it), Scope & Limitations, Related Work, and the
Conclusion — after which References begin near the foot of page 8. The largest
block on page 8 (RQ4 + Scope) belongs to the **Evaluation** section, which the
spec explicitly places out of scope (it names only Introduction ¶1–6 / ¶7–8
filler, Background, Design, Related Work, Conclusion). Pulling the body end from
page 8 onto page 7 requires removing roughly a full page of body content
(~80 source lines); the in-scope ceiling is far lower (−14 achieved; even the
targets' combined −33 would leave the Conclusion on page 8).

What did shift: round-2 compression moved the **RQ4 heading and its first
sentences up onto page 7** (page 7's tail now begins RQ4), and References now
start ~6 entries higher on page 8 than at baseline (baseline: References began at
the very foot of page 8 with only ~3 entries on the page).
