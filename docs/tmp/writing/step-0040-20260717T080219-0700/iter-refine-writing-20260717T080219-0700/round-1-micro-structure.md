# Round 1 — Micro Structure and Paragraph Roles

## Node identity

- **Started:** 2026-07-17T08:16:00-07:00
- **Completed:** 2026-07-17T13:05:03-07:00
- **Parent:** Step 0040 WRITE gate
- **Objective:** repair paragraph roles and repetition while recovering the
  AAAI seven-page body budget without changing the thesis, RQs, mechanisms, or
  standard quantitative evidence.
- **Entry baseline:** Round 0 paper state.
- **Reviewer:** independent read-only subagent invoking
  `check-paper-structure-flow` at paragraph-role level.

## Independent findings

The reviewer found that the 10-page Round 0 build needed roughly 260--300 words
of meaning-preserving compression. The highest-value edits were:

1. reduce the 265-word, 11-sentence abstract to 7--9 sentences;
2. state the Introduction's structural cause before its details;
3. collapse the Introduction's repeated result inventory;
4. compress the Evaluation overview and repeated RQ1 setup;
5. place RQ2's direct answer after, rather than before, its post-hoc mechanism
   analysis; and
6. make RQ3's opening map each evaluated construct to its standard metric.

The reviewer also suggested compacting RQ3 controls and metric setup and
removing repeated RQ3 result restatement once every value remained visible in
its table or result paragraph.

## Applied fixes

### Abstract and Introduction

The abstract now has nine sentences. It retains the exact thesis, operation and
operation-stack model, complete workload inventory, scoped capture result,
ordinary B$^3$ result, three-workload MAP result, OSWorld-Human result, and
27{,}765-operation construction result. The Introduction now begins the causal
paragraph with the two missing structures and reports one compact result
paragraph rather than repeating intervals, secondary comparators, memory, and
relative overhead already reported in Evaluation.

### Evaluation organization

The data overview now describes three explicitly non-pooled data classes in one
paragraph. RQ1's capture protocol and result were compressed without deleting
the complete-task count, precision, recall, control rejection, sample count,
stack count, or conservation result. The flamegraph and standard ordinary B$^3$
evidence remain unchanged.

RQ2 now gives its direct answer after the primary and adaptive analyses. The
primary semantic-versus-raw comparison still answers RQ2 positively on all
three complete workloads; the local-first analysis remains explicitly adaptive
and supports only refinement of operation-local evidence.

RQ3 now states the construct-to-metric mapping at entry: literal fields use
accuracy/macro-F1, partitions use V-measure or ordinary B$^3$, and adjacent
boundaries use exact precision/recall/F1. Its OSWorld setup, controls, and
metric prose were compacted without changing folds, populations, methods,
controls, or values.

### Direct user correction: standard metrics only

The user explicitly rejected token-weighted B$^3$, Recall@20\%, and fixed top-3
reader protocols as paper-facing metrics. The resulting paper policy is:

- ordinary operation-level B$^3$ is the only RQ1 partition metric;
- AP/MAP is the only RQ2 ranking metric;
- V-measure, ordinary B$^3$, standard accuracy/macro-F1, and exact boundary
  precision/recall/F1 cover their corresponding RQ3 constructs; and
- Recall@20\%, fixed-reader results, and project-defined metric variants remain
  internal diagnostics and do not appear in the manuscript.

The token-weighted B$^3$ column, values, prose, and bibliography entry were
removed. Standard metric definitions now cite Bagga--Baldwin for B$^3$,
Robertson for AP, Rosenberg--Hirschberg for V-measure, Lewis et al. for
accuracy/macro-F1, and Ruokolainen et al. for exact boundary
precision/recall/F1. The direct instruction and its internal-diagnostic boundary
were appended verbatim in substance to `docs/user-instruction.md`.

## Rejected or deferred findings

- No table was deleted merely to save space; each table carries a distinct RQ
  answer.
- RQ2's adaptive qualifier and AgentProcessBench null comparison were retained.
- RQ3's supervised, label-free, and reference-calibrated modes were not merged
  because they have different information contracts.
- Broader sentence-level polish remains assigned to later rounds.

## Preservation audit

- Exact thesis unchanged.
- Exactly four RQs remain in the fixed order.
- No RQ, algorithm, dataset, result, or story was replaced or narrowed.
- No custom budget or reader metric appears in the paper.
- `docs/agentpprof-paper` remains untouched.
- Writing performed no Git staging, commit, push, branch creation, or branch
  switch.

## Compilation and page evidence

`make` completed all LaTeX and BibTeX passes. The final build is nine pages on
US Letter with no undefined citation, undefined reference, or overfull box.
After the final conclusion compression, the paper body ends on page 7 and
references begin on page 8. The added metric citations resolve in the
bibliography.

## Next node

Round 2 performs a fresh section-convention audit of Abstract, Introduction,
Background, Design, Implementation, Evaluation, Related Work, and Conclusion.
