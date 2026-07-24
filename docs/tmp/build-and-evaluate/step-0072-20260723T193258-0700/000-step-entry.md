# Step 0072 Entry — Close the Four RQs with Current Automatic Operations

**Entered:** 2026-07-23 19:32:58 -0700  
**Phase:** BUILD_AND_EVALUATE  
**Outer gate:** EXPERIMENT  
**Current experiment:** RQ2 only

## Why this step exists

The current paper has complete evidence for all four fixed research questions,
but two scientific gaps remain visible:

1. RQ2 compares a group score with raw-action grouping, while the strongest
   practical question is whether profiling adds information to an existing
   operation-local diagnostic signal.
2. RQ4 measures only deterministic profile construction after operation marks
   already exist; it does not include automatic operation annotation.

The latest RQ3 automatic-operation result also has a provenance mismatch in the
paper: the reported A2 result was produced by independent Codex subagents and
root validation, not by the incomplete Qwen3.6-27B development branch. This
must be corrected before measuring end-to-end annotation cost.

## Fixed outer sequence

This step will not combine multiple hypotheses into one experiment. The root
agent will close the fixed RQs in separate experiments/outer steps:

1. **RQ2:** test whether the current automatic AgentProf view improves a fixed
   local diagnostic score under a matched local-first comparison.
2. **RQ3:** test automatic operation construction on a separate published
   labeled corpus or held-out operation-label task, using standard metrics.
3. **RQ4:** measure the actual automatic backend end to end, including
   annotation, profile construction, wall time, and token use.
4. **RQ1:** synthesize the latest automatic-operation structure result with
   exact resource conservation and the real Git case; add a new experiment
   only if this cumulative answer still does not establish useful attribution.

The paper thesis, four RQs, abstract, introduction, motivation, contributions,
and story remain fixed.

## Repository and publication policy

- Remain on the current branch.
- Git is independent of scientific pass/fail.
- Commit and push only after a complete outer step has passed result review,
  targeted writing, and whole-paper review.
- No writing or review subskill may perform Git operations.

