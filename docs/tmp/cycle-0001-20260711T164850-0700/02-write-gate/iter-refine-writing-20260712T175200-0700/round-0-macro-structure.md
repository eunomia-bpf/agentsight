# Round 0 — Macro Structure

**Started:** 2026-07-12T17:52:00-07:00  
**Completed:** 2026-07-12T18:04:00-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `050-root-disposition-application-20260712T175200-0700.md`  
**Reviewer:** fresh read-only subagent using `check-paper-structure-flow`, Level 1  
**Verdict after fixes:** writing structure PASS; empirical completion deferred to EXPERIMENT

## Inputs And Method

The reviewer reread `docs/user-instruction.md`, the complete structure-flow
skill and full-paper/abstract-introduction references, all of
`docs/paper/main.tex`, paper build guidance, build log, and the current PDF. It
did not edit files or run Git. It checked section order, design/implementation
separation, architecture figure, exact four-RQ organization, balance, AAAI page
shape, and whether the ambitious profiling story remained visible.

## Raw Findings

### Must-fix

1. The opening and closing stated the strong profiling thesis, but Background,
   Design, and RQ1 still let hierarchy/projection machinery displace the
   profiling-to-problem-to-intervention story.
2. RQ1--RQ4 were structurally present but not submission-complete: RQ1 had only
   necessary attribution evidence, RQ2 and RQ4 were protocols, and RQ3 had only
   a mapping proxy.
3. Reader-facing project-status and intermediate-problem language remained in
   the implementation caveat, RQ3 dataset discussion, RQ endings, and
   Limitations.
4. Background lacked one concrete recurring case that connected per-run
   fragmentation to the need for a profile-guided intervention.

### Should-fix

- compress the Abstract to fewer sentence roles;
- make the architecture figure show cross-run folding, drilldown, and an
  intervention loop;
- rebalance the long operation-stack/RQ1 material toward RQ2 and RQ4;
- give Implementation a clearer component mapping;
- replace exact RQ question headings with noun phrases;
- update README page status after the writing pass stabilizes.

### Consider

- keep merged Background and Motivation for the AAAI page budget;
- retain Discussion but make it intervention-centered;
- remove repeated hierarchy/accounting qualifications.

## Applied Fixes

1. Added the existing real `cargo test` recurrence as a compact motivating
   case in Background. It now distinguishes one-invocation debugging from the
   need to fold 2,903 invocations by recurring responsibility and select a
   change for later runs. No new number or claim was introduced.
2. Added an explicit Design-overview use path:
   `many runs -> recurring measured profile -> consequential frame -> native
   drilldown -> intervention -> held-out verification`. It says stack
   construction is the mechanism, not the research destination.
3. Extended the existing architecture figure with an `Inspect / Intervene /
   Rerun` node and dashed feedback edge to later traces. The caption labels this
   as the evaluation path rather than falsely claiming the intervention is an
   implemented profiler stage.
4. Rewrote the RQ1 closing positively around the achieved conservation and
   declared-category separation evidence, then named the independent lineage
   measurement needed for the complete answer.
5. Removed the rendered imported-zero implementation defect from the paper. It
   remains in `docs/implementation.md` and is not relevant to the positive-
   integer workloads currently described.
6. Removed named RQ3 dataset failures and reframed the six-of-nine and four-of-
   five observations as preliminary structured-field transfer supporting the
   complete target-blind tagger evaluation.

## Deferred Or Rejected Findings

- **Empirical completion — deferred, mandatory.** Writing cannot manufacture
  RQ2 intervention, held-out RQ3 tag accuracy, or complete RQ4 cost results.
  The four questions and positive hypotheses remain fixed; the following
  EXPERIMENT gate must run complete real experiments and replace the honest
  unresolved-result TODOs.
- **Hide all TODOs in comments — rejected for the current research draft.** The
  orchestrator requires each RQ to have an evidence-backed answer or an honest
  unresolved-result TODO. Removing those markers before results exist would
  make the paper appear complete without evidence. They are not negative
  intermediate results.
- **Replace exact question headings with noun phrases — rejected.** The author
  explicitly fixed the four RQs, and the active writing/orchestration rules
  require Evaluation to be explicitly organized by them. Each heading remains
  verbatim.
- **Add the final motivating regression — deferred.** No exact published agent
  revision/configuration pair is yet verified. The paper uses the existing
  recurrence example and does not invent a regression.
- **Abstract compression, detailed paragraph balance, and Implementation prose
  structure — accepted for later assigned rounds.** Round 4 owns the opening;
  Rounds 1--3 and 6--9 will handle local balance and flow.
- **README page count — deferred until the final writing build.** Intermediate
  pagination is not stable.

## Preservation And User-Intent Check

- Exact thesis unchanged.
- Exactly four RQs unchanged in wording, order, and meaning.
- No quantitative value changed.
- No citation was removed in Round 0.
- No negative intermediate experiment reentered the paper. AgentRx, TELBench,
  and Hodoscope appear only as neutral closest-work references.
- The middle now follows the larger profiling and intervention story rather
  than promoting hierarchy selection.
- No new named abstraction, taxonomy, or mechanism was added.

## Compile Evidence

`make` completed successfully after the edits. `main.log` contains no undefined
citation/reference, LaTeX error, or emergency stop. The PDF is 9 letter-size
pages including references. The architecture figure compiles with the feedback
path.

## Remaining Concern And Next Node

The paper is structurally coherent but not empirically submission-complete.
That is a ranked experiment blocker, not a reason to shrink the story. Proceed
to Round 1 micro structure; after the complete WRITE pass and independent audit,
reopen literature novelty and then run the decisive real RQ2 regression and
intervention experiment.
