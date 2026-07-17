# Round 7 — Language: Word Choice

**Started:** 2026-07-16T22:42:14-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skill:** `paper-writing-style`, word-choice scope.

**Objective:** Review the complete paper for jargon inflation, compound-term
overload, nominalizations, vague referents, redundant hedging, verbose phrases,
unnecessary adverbs, and project-report wording. Preserve the exact thesis,
four RQ meanings, algorithm, evidence scope, protected hedges, all numbers, and
all citations.

## Entry State and Method

The entry is the compiled Round 6 paper: 251-word nine-sentence abstract, four
fixed RQ subsections, 53 unique citation keys, nine US-letter pages, main
content ending on physical page 7, and no build warning or error. A fresh
read-only subagent was instructed to invoke `paper-writing-style`, read the
verbatim user-instruction log and complete paper, and report severity-ranked
word-choice findings only. It may not edit, run experiments, perform Git
operations, revisit Round 6 mechanics, assess novelty, change the story, or
reinterpret RQ3's recorded evidence gap.

No edit will be applied until the independent findings arrive.

## Independent Review Verdict

**REVISE: 5 Must-fix, 26 Should-fix, and 4 Consider findings.** The
reviewer completed Abstract, Introduction, Background, Design, Implementation,
all four RQs, Scope, Related Work, Conclusion, and captions. It did not propose
a story, RQ, algorithm, number, citation, or protected-scope change.

### Raw Must-fix Findings

| ID | Location | Problem and repair |
|---|---|---|
| M1 | Abstract model sentence | A stacked noun phrase makes `for pprof-compatible profiles` attach ambiguously. Make `\sys` the actor for model implementation and export, and name the label-free constructor's visible-action transitions directly. |
| M2 | Abstract results | `scoped path`, `raw action`, `simple controls`, and `comparator` read as internal shorthand. Name the AgentSight capture/join stage, `\sys` folding, raw-action grouping, strongest simple control, and supervised predictor. |
| M3 | RQ1 protocol | Repeated `fixed suite` and `existing/current/once` read as an execution log. State one task/control pairing and the AgentSight-to-adapter-to-`agentpprof` method. |
| M4 | RQ3 opening | Stacked modifiers obscure which annotations are independent and which families are unseen. State that methods are specified before evaluation and target-blind, then separate the tested objects. |
| M5 | Conclusion | `They` has multiple antecedents and one verb list mixes mechanism and evidence. Name the model/`\sys` relation and begin the measured result with `Across the evaluated datasets`. |

### Raw Should-fix Findings

| IDs | Areas | Main problems |
|---|---|---|
| S1--S5 | Introduction | Abstract `operational behavior`, `semantic identity`, `realizes/instantiate`, released-source pipeline shorthand, and `operation-producing tokens leave the gain`. |
| S6--S7 | Background | Ambiguous `this` after pprof/flame graphs and the triple noun phrase `semantic responsibility fields`. |
| S8--S11 | Design and Stack Construction | Requirement-trace wording, nominalized stack selection, colloquial `gets for free`, project-like `later rule authoring`, unnecessary `explicitly`, and stiff `The reference`. |
| S12 | Implementation | Verbose rerun phrase and ambiguous `both paths`. |
| S13--S14 | Evaluation overview | `fixed paper-level`/protocol-management wording and ambiguous `readable histories`/`multi-month project`. |
| S15--S19 | RQ1 | Experiment-history `unchanged`, redundant `standard primary`, compressed bootstrap/mass terminology, abstract interpretation, and dense field-projection noun chains. |
| S20--S21 | RQ2 | Mutable `current`, contract-like `fixed choices`, vague `same direction/same reader`, and gate-like `RQ2 is positive`. |
| S22--S23 | RQ3 | Vague `principle`/internal `mechanism-development evidence` and anthropomorphic `consumes annotations`. |
| S24--S25 | RQ4 | `identical-input raw action`, subjective `practical`, and `semantic-profile peak` noun stacking. |
| S26 | Related Work | Internal pipeline noun phrase instead of explicit declared scope and folding actors. |

### Consider Disposition

1. **Manual inspection `scales poorly`: rejected.** The current `slow and
   expensive` claim stays because changing it would require checking whether
   the cited source directly supports the stronger scaling formulation; that
   belongs to Round 10 citation verification.
2. **`intent-effect cycles` to `cycles`: accepted.** This removes a one-use
   compound without losing its immediately preceding antecedent.
3. **Normative representation sentence to direct system behavior: accepted.**
   It states the same design decision more directly.
4. **Completion/status wording and `false positive`: accepted.** The full-run
   completion fact remains, while plural agreement and scientific prose
   improve.

All 26 Should-fix findings are accepted, with protected metric hierarchy and
scope retained in more compact wording. Edits proceed subsection by
subsection.

## Applied Repairs

All 5 Must-fix and all 26 Should-fix findings were repaired in
`docs/paper/main.tex`. Three of four Consider suggestions were applied; the
unsupported `scales poorly` strengthening was rejected as recorded above.

- The Abstract now makes `\sys` the actor, separates label-free construction
  from profile export, names the AgentSight capture/join and `\sys` folding
  stages, and replaces internal comparator shorthand with named controls.
- The Introduction, Background, Design, and Implementation now use direct
  actors and verbs for agent behavior, semantic identifiers, source
  reconstruction, stack selection, rule authoring, and tagging modes. One-use
  compounds and project-log wording were removed.
- RQ1 now states the task/control pairing and AgentSight-to-adapter-to-profiler
  path directly. It keeps ordinary operation-level B$^3$ as the sole primary
  partition metric and token-weighted B$^3$ as secondary. The confidence
  interval, exact token conservation, phase-only comparison, post-hoc scope,
  five field hierarchies, every population, and every result remain intact.
- RQ2 now names the released 536-trajectory snapshot, identical operation and
  evidence inputs, pre-target choices, pooled operation-level AP, and the one
  fixed blinded reader. Its conclusion directly states the matched raw-action
  result without gate/status language.
- RQ3 now separates the paper-level question from the tested partitions,
  literal labels, and boundaries. It explicitly explains why recurrence is
  development evidence and why reference calibration is not label-free.
- RQ4 now names raw-action grouping on identical inputs, defines RSS without a
  noun stack, and answers the RQ with the measured time and memory deltas.
- Related Work and Conclusion now name responsible actors and declared scope.
  The exact thesis remains unchanged, and the final evidence sentence begins
  with `Across the evaluated datasets`.

The edit ledger contains 34 accepted finding-level repairs: 31 Must/Should
findings and 3 Consider findings. Some findings required more than one source
sentence; no unsupported sentence-level count is inferred from that ledger.

## Preservation and Build Verification

- A multiset comparison against the read-only Round 5 snapshot
  `8edf11e7282f6fb3f1cd1b5c1643cda0e0d077dc` found no changed numeric token and
  no changed citation key. Round 6 had independently recorded that it changed
  neither numbers nor citations, so this comparison covers the complete Round
  7 edits as well.
- The exact thesis, `Agent observability needs profiling, not only debugging.`,
  still appears in the Abstract, Introduction, and Conclusion.
- All four fixed RQ subsections remain present and retain attribution,
  localization, tag accuracy, and cost meanings.
- `make` completed successfully with official `aaai2027`, producing a
  nine-page US-letter PDF. Main content and the start of References share
  physical page 7; physical pages 8--9 contain references only.
- `main.log` contains no LaTeX/package warning, overfull box, undefined
  reference/citation, or error matched by the project audit. Benign underfull
  box diagnostics remain.
- The paper submodule remains clean at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c` and was not touched.

## Alternatives and Decision

Adding ARI, AMI, or NMI merely to increase the number of familiar metrics was
considered during the intervening metric audit and rejected. Ordinary B$^3$
already provides the standard primary partition comparison, exact boundary F1
provides a distinct transition diagnostic, and additional correlated metrics
would weaken the paper with metric proliferation. No algorithm, experiment,
claim, RQ, number, citation, or evidence scope changed in this language round.

## Tree, Memory, Remaining Concerns, and Next Node

This round changes only the paper and its auditable round report. It does not
change project memory, idea-story history, experiment state, or the research
tree. Scientific concerns remain exactly those already stated in the paper,
including the incomplete independent literal-phase and family-held-out part of
RQ3; they are not writing defects and are not silently repaired here.

**Completed:** 2026-07-17T02:18:59-07:00

**Next node:** Round 8, terminology and jargon consistency, with a fresh
read-only reviewer invoking both `check-terminology-infoflow` and
`paper-writing-style` on the complete paper.
