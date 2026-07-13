# Round 2: Section Conventions

## Node identity

- **Started:** 2026-07-11 22:59:05 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-1-micro-structure.md`
- **Review skill:** `check-paper-structure-flow`, section conventions
- **Entry paper:** 9 pages; References begins on content page 7
- **Protected invariants:** four RQs, three contributions, all quantitative values,
  59 citation commands, and the read-only paper submodule

## Objective and method

The reviewer read the complete current paper as a compact AAAI full paper and
checked abstract/Introduction conventions, Design goals and overview,
Implementation ownership, the exact RQ overview and evidence blocks, Setup,
orphan experiments, floats, Related Work grouping, and Conclusion structure. It
made no edits or Git operations.

The reviewer reported that the requested common-pitfalls file was absent, which
is factually incorrect at the supplied absolute path. The main agent had already
read and applied that file in this run; the section-convention findings below are
accepted only where independently supported by the current paper and rendered PDF.

## Raw findings

### Writing and format Must-fix

1. The 197-word abstract has nine sentences but three LaTeX paragraphs and lacks
   strict one-sentence correspondence for root cause and realization challenge.
   Make it one paragraph with nine role sentences.
2. The shared setup lacks final hardware/runtime/repetition detail. Current
   non-performance methods are stated, but the controlled release setup belongs
   to the missing RQ4 experiment and must not be invented.

### Scientific Must-fix carried to later gates

1. RQ1 lineage correctness, complete RQ2 hierarchy tests, frozen induced identity
   for RQ3, and end-to-end RQ4 cost are unanswered. A full empirical submission
   cannot pass until all four receive direct evidence-backed answers.
2. The frozen-identity labeler and cost-bounded navigator promised by Contribution
   2 are not implemented. They must be implemented and evaluated; the paper must
   not relabel the existing substrate as the complete contribution.
3. The final shared hardware/software setup can be written only after the complete
   experiments run. Current disclosure of absence is correct for a Day-1 paper.

These findings route to the next EXPERIMENT gate after the writing/review loop.
They do not authorize smaller RQs or contributions.

### Should-fix

1. Remove current backend/inducer implementation status from Design and make
   Implementation map its mechanisms to G1--G3.
2. State the representation checks in RQ1 and boundary audit in RQ3 as explicit
   prerequisite controls so they are not orphan experiments.
3. Ensure the RQ2 table and RQ3 figure appear after their subsection question,
   rather than floating above the evidence-block header.
4. Make Figure 1's labels readable at print scale, state its motivation/design
   role, and reference it in the Introduction system paragraph.
5. Bound the RQ1 figure caption to conservation/category separation rather than
   lineage correctness.

### Consider

- Rename the architecture's solid candidate-identity node so it cannot be mistaken
  for the proposed frozen reusable identity.
- Do not compress further merely because total length is nine pages; References
  already starts on page 7. Future results should replace evidence-TODO prose.

## Fix plan

Apply all writing/format findings now. Record scientific Must-fix items as active
experiment blockers. Use `paper-figures` to crop the existing full-width profiles
through LaTeX layout only, preserving the source images and full artifact. Test
float placement after compilation. Do not introduce hardware facts, claim that a
proposed component is implemented, or change any RQ.

## Completion evidence

### Applied fixes

1. Rebuilt the Abstract as one LaTeX paragraph with nine explicit role sentences:
   background, problem, root cause, existing approaches, insight, realization
   challenge, system/model, methodology, and combined current result. It retains
   36.7%, 84.4%, the negative held-out result, and the complete failure/safety/
   redundancy open scope.
2. Removed current backend and inducer implementation status from Design. Design
   now states qualification and interface rules; Implementation owns concrete
   regex/tagger/clustering/inducer choices and the implemented/proposed boundary.
3. Added an explicit G1--G3 implementation map without claiming that frozen
   identity or navigation exists.
4. Marked field-selection/multi-measure checks as prerequisite representation-
   validity controls in RQ1 and the boundary audit as a derivation-coverage control
   in RQ3. Their limited evidentiary roles are explicit.
5. Extended the RQ1 caption with the boundary that the figure supports
   conservation and declared-category separation, not lineage correctness.
6. Renamed the architecture's solid node to `Candidate / Trace-Local Scope Tree`,
   preventing confusion with the dashed proposed `Frozen Cross-Run Identity`.
7. Applied `paper-figures` to Figure 1: the original images remain untouched, while
   LaTeX now shows readable left-side representative crops side by side, points to
   the full artifact, defines each width measure, and states the motivation/design
   claim. The Introduction system paragraph explicitly interprets the figure.
8. Moved Figure 1's source after the this-paper/results paragraph so it no longer
   splits root cause from insight in source order.
9. Changed the RQ floats to strong local placement and recompiled. The RQ2 table
   follows the RQ2 question in the left-column reading order; the RQ3 figure follows
   the RQ3 question; RQ1 begins in the left column before its figure in the right
   column. No float was pushed past content page 7.

### Scientific blockers carried, not papered over

- RQ1 independent lineage correctness remains unrun.
- RQ2 complete-hierarchy failure, safety, and redundancy experiments remain unrun.
- RQ3 frozen induced-identity transfer remains unrun.
- RQ4 complete controlled cost remains unrun.
- The frozen labeler and navigator remain unimplemented.
- Consequently, the final hardware/runtime setup and final contribution/result
  language cannot yet be written. Current status language remains honest.

These route to REVIEW and the next EXPERIMENT gate. They cannot be resolved by
smaller wording, removing an RQ, or relabeling trace-local behavior as frozen.

### Deferred final-state wording

The contribution paragraph still says “The completed paper targets” and the
Conclusion reports the current negative result. This is intentional in a Day-1
paper: replacing them with delivered-final wording before the mechanisms and
experiments exist would be false. They must be synchronized after evidence is
admitted.

### Compilation and invariants

Completed 2026-07-11 23:11:16 -0700.

- 9 US-Letter pages; References begins on page 7 and occupies pages 7--9.
- 59 citation commands before and after.
- Four RQ subsections with unchanged meaning.
- Three contributions preserved.
- 4,716 counted words.
- No undefined citations or references.
- Figure 1 was visually inspected at 150 dpi; the cropped prompt/session labels are
  materially more readable and the two views occupy one row.
- Two overfull boxes remain (8.10556 pt and 0.99261 pt) for later language/format
  rounds.
- No Git operation or submodule edit occurred.

## Round verdict and next node

**ROUND 2 PASS FOR CURRENT RESEARCH STATE.** Section conventions, RQ ownership,
float order, figure responsibility, and format are coherent. The paper is not a
submission-ready empirical paper because the scientific blockers above are real.
Continue to Round 3 logic flow; preserve those blockers as experiment obligations.
