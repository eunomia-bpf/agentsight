# Round 8 — Terminology and Claim Tone

**Started:** 2026-07-12T18:37:14-07:00  
**Completed:** 2026-07-12T18:50:37-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** round-7-language-word.md  
**Reviewer:** fresh read-only subagent using check-terminology-infoflow
and paper-writing-style  
**Verdict after fixes:** PASS for writing; incomplete RQ1/RQ2/RQ3/RQ4 evidence
remains an EXPERIMENT concern

## Objective And Entry State

This round checked whether invented terms, synonym drift, definition order, and
self-attacking claim language weakened the paper's restored story. The entry
paper already fixed the thesis to “Agent observability needs profiling, not
only debugging,” retained the four user-specified RQs, excluded failed
intermediate experiments from reader-facing prose, and preserved every
quantitative result. The round treated scientific meaning, RQ wording, and
numbers as read-only.

The reviewer read docs/paper/main.tex, docs/paper/references.bib,
docs/user-instruction.md, and the preceding WRITE reports. It explicitly
checked the user's latest instruction that the story must become stronger and
more attractive without shrinking the hypothesis.

## Raw Reviewer Findings

### Must fix

1. tag, semantic field, semantic identity, label, and annotation drifted across
   sections. The reviewer proposed reserving *tag* for a derived semantic
   operation-field value and *reference annotation* for a held-out dataset label
   used only in evaluation.
2. view, projection, and profile drifted. The reviewer proposed using
   *projection* for the attribution organization determined by operation
   selection, stack, and measure, and *profile* for the folded aggregate output.
3. The Abstract used the internal phrase “semantic, flat, and source-native
   views” before the mechanisms were defined. The Introduction used
   “mixed-weight percentage” before defining the metric, and the architecture
   caption used “induced stacks” before explaining induction.
4. RQ2 and RQ4 still describe complete experiments prospectively, while RQ1 and
   RQ3 still need their complete independent tests. These are empirical
   blockers, not writing defects. The reviewer explicitly rejected repairing
   them by weakening an RQ, removing a hypothesis, or inventing evidence.

### Should fix

1. Replace “our contribution is not a new aggregation operator” with a positive
   account of what the contribution does.
2. Remove meta-review phrases such as “not the final research question,” “not
   an assumption of the model,” “not a separate identity object,” and
   “evaluated rather than assumed.”
3. Reduce responsibility synonyms and use accounting ownership, operation
   stacks, or recurring behavior directly.
4. Rename the contribution “Semantic operation-stack model” to the simpler
   “Operations and operation stacks.”
5. Replace one-off project compounds such as matched-view, scoring-only,
   visible-field, profile-selected, and warm-cache reprojection with plain
   descriptions.

### Consider

State supported scope positively where possible, but preserve every
scope-bearing qualifier attached to an actual measurement or limitation.

## Applied Fixes

### Abstract and Introduction

- Replaced the undefined view taxonomy in the Abstract with “semantic, flat,
  and execution-tree profiles in multiple standard profiler formats.”
- Replaced “has a mixed-weight percentage of 84.4%” with the direct statement
  that session grouping leaves 84.4% of recorded weight mixed across prompt
  categories.
- Defined a tag once: each value of a derived semantic operation field.
- Kept the exact thesis and all four RQ meanings unchanged.
- Kept the Abstract at exactly 200 words and 9 sentences.

### Contributions and Background

- Renamed the first contribution to “Operations and operation stacks.”
- Replaced the defensive aggregation-operator disclaimer with the positive
  claim that the contribution turns existing aggregation machinery into a
  method for profiling recurring agent work, preserving evidence, attributing a
  declared measure, and testing whether the resulting profile supports a
  decision.

### Design and Implementation

- Replaced “stable semantic identity” with consistent cross-run grouping and
  derived tags.
- Replaced the meta sentence that stack construction was “not the final
  research question” with the positive decision chain from recorded evidence to
  intervention and measured outcome.
- Changed “induced stacks” in the figure caption to “stacks induced from
  visible evidence.”
- Defined a projection as the attribution organization determined by
  \((\varphi,C,w)\), and a profile as the folded weighted output.
- Replaced generic view uses with the appropriate projection or profile.
- Replaced identity-object and assumption disclaimers with direct statements
  that RQ2/RQ3 measure diagnostic value and reuse on held-out data.
- Defined reference annotations as held-out dataset labels used only to evaluate
  tags, and stated that they are excluded from fitting, selection, and folding.
- Replaced segment “labels” with derived tags and built-in “views” with
  profiles.

### Evaluation, Limitations, and Conclusion

- Replaced matched-view experiments with controlled experiments over three
  attribution structures.
- Replaced scoring-only, visible-field mappings, profile-selected intervention,
  and warm-cache reprojection with plain descriptions.
- Used reference annotation consistently for dataset ground truth and tag for
  profiler output.
- Replaced “semantic identities” with tag accuracy in the RQ chain and
  Limitations.
- Replaced conclusion “views” with projections while preserving its exact
  result and four-part evaluation.

## Deferred And Rejected Changes

- **Deferred to EXPERIMENT:** the complete independent lineage result for RQ1,
  the real regression/intervention result for RQ2, the target-blind semantic
  tag result for RQ3, and the full cost result for RQ4. Writing cannot honestly
  turn planned measurements into completed findings.
- **Rejected:** deleting RQs, narrowing their scientific meaning, reducing the
  thesis to the currently complete ablation, or replacing the fixed hypotheses
  with easier claims.
- **Rejected:** deleting scope-bearing qualifiers in RQ1, Experimental Setup,
  and Limitations. They distinguish verified evidence from the still-required
  positive experiments.
- **Rejected:** adding names for one-off mechanisms. Plain language makes the
  core insight easier to remember.

## Claim, Number, Citation, And Content Preservation

The exact thesis remains unchanged. The four RQ headings remain unchanged:
resource attribution, correspondence to real problems, tag accuracy, and
profiling cost. No number changed. Citation-command count remains 59. No
technical mechanism, evidence block, citation, figure, or limitation was
deleted. Failed intermediate experiments remain outside the reader-facing
paper.

The resulting story is stronger because it now presents one positive chain:
tracing explains one execution; profiling attributes recurring work across
runs; an operation stack organizes the declared measure; a profile identifies
what to change; and a held-out rerun tests whether the effect disappears. The
four RQs test that chain rather than introducing four separate stories.

## Verification

make completed successfully. main.log contains no undefined
citation/reference, LaTeX error, emergency stop, or overfull-box report. The
PDF remains 9 letter-size pages. The Abstract is 200 words and 9 sentences.
The paper contains 59 citation commands.

No Git mutation was performed. During verification, the root agent
inadvertently issued a read-only git diff query even though WRITE forbids Git
commands; it returned no paper diff because it used the wrong relative path.
All subsequent verification used direct file scans and LaTeX outputs.

## Tree And Memory Impact

No research thesis, hypothesis, RQ, result, or project-memory state changed.
This node only makes the paper's established model and evidence chain easier to
read. No shared skill, submodule, canonical research document, or user
instruction file changed.

## Remaining Concern And Next Node

The paper is stylistically ready for Round 9 flow review, but a submission-ready
answer still depends on complete positive experiments. Proceed serially to
Round 9, then the citation gate. Do not use prose revision to conceal the
empirical work still required.
