# Round 2 — Section Conventions

**Completed:** 2026-07-12T18:25:00-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `round-1-micro-structure.md`  
**Reviewer:** fresh read-only subagent using `check-paper-structure-flow`  
**Verdict after fixes:** convention PASS; empirical completion remains open

## Review Scope And Passing Checks

The reviewer reread the user instructions, complete paper, structure skill and
section references, and PDF. It confirmed a 211-word, nine-sentence Abstract;
all required Introduction roles; separate Design and Implementation; four
requirements and an architecture walkthrough; an explicit exact four-RQ
Evaluation with one block per RQ; and correctly ordered Limitations, Discussion,
Related Work, and Conclusion. It made no edit and ran no Git operation.

## Findings And Fixes

### Applied must-fix

- The AAAI style suppresses section numbering, so rendered `Section~\ref{}` and
  `Sections~\ref{}--\ref{}` text produced blank section names. Replaced every
  reader-facing section-number reference with direct names such as “Background
  and Motivation,” “Design,” “Implementation,” and “Evaluation.”
- Conclusion previously stated only the thesis and planned questions. Added the
  already verified positive result: 325 real trajectories, conservation of all
  183,714 units, and separation of recurring declared work that session-only
  organization mixes.

### Applied should-fix

- Connected RQ1 representation coverage explicitly to heterogeneous resource
  attribution, and connected cross-measure ranking divergence to the need to
  declare the attributed resource.
- Expanded the formerly orphan RQ3 boundary result into a minimal independent
  evidence paragraph: five rows across three named datasets, labels hidden
  during field derivation, adjacent-boundary F1 scored afterward, strongest
  simple per-row baseline, and four-of-five leading result.
- Made all four Related Work groups parallel with noun-phrase topic labels.
- Replaced the Limitations experiment-plan ending with a direct scope statement
  covering offline profiles, supplied source fields, declared measures,
  evaluated identities, non-causal ownership, and measured populations.

### Deferred or rejected

- Full RQ2/RQ4 and final RQ1/RQ3 results remain mandatory EXPERIMENT work. They
  cannot be fabricated by section editing.
- Naming the four Design requirements was rejected because the author forbids
  unnecessary terminology and concept stacking. Their parallel prose already
  makes them traceable without new labels.

## Preservation And Intent Check

The exact thesis and four RQ meanings/headings are unchanged. No number changed.
The citation-command count remains 59. No negative intermediate result entered
the paper. The fixes strengthen the positive profiling story and remove a real
AAAI rendering defect without introducing a new concept.

## Build Evidence And Deviation

An initial verification command was accidentally launched from the repository
root and invoked the unrelated top-level AgentSight Makefile; it stopped because
the local libbpf source path was absent. It changed no paper or submodule file and
is not paper evidence. The root immediately reran `make` from `docs/paper/`.
That build completed successfully. The paper log has no undefined citation or
reference, LaTeX error, or emergency stop. The PDF remains 9 letter-size pages.

## Next Node

Proceed to Round 3 whole-paper logic flow. The remaining submission blocker is
complete positive empirical evidence, not section convention or authority to
change the RQs.
