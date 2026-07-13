# Serial plan review: AgentProcessBench RQ2 experiment

## Round 1 — independent construction audit

**Reviewed:** 2026-07-13T05:10:00-07:00  
**Reviewer:** independent subagent  
**Required skill:** `research-experiment-design`  
**Mode:** read-only; no file edits, Git operations, web search, or additional
human-label inspection  
**Plan reviewed:** Revision 1  
**Verdict:** **REVISE**

### What already passes

- The experiment tests one construction inside fixed RQ2 and does not claim to
  answer the whole research question.
- AgentProcessBench is a real, public, peer-reviewed source with a complete
  1,000-trajectory and 8,509-step population.
- One assistant message is the correct published operation unit.
- Neutral steps remain in the population rather than being discarded.
- The semantic stack preserves `action → target → repeat_state` and adds
  `intent → phase`, directly repairing the completed AgentNet construction.
- Real AgentProf, flat/session/raw/semantic/ungrouped views, clustered
  bootstrap, family-stratified reporting, and the story/RQ lock should remain.

### Must-fix 1: remove the self-conditioning risk model

Revision 1 trains a logistic risk model from
`intent, phase, action, target, repeat_state`, then groups the semantic view by
those same fields. Every view receives the same predictions, so semantic is not
mathematically guaranteed to win, but the comparison is still circular:
semantic explicitly preserves the predictor's own conditioning variables while
raw action averages over two of them. A win would not cleanly show that
semantic context has diagnostic value.

Replace the logistic model with the official repository's 20 released blind
judge predictions. For operation `i`, fix risk to:

```text
number of non-null official predictions equal to -1
----------------------------------------------------
number of non-null official predictions
```

All 20 models have equal weight; published accuracy does not choose or weight a
model. The three steps with all 20 predictions null receive the predeclared
uninformative value 0.5. No human-label training remains, and the four families
become result strata rather than train/test folds.

### Must-fix 2: control semantic refinement granularity

Semantic is a strict refinement of raw action. A finer partition can approach
individual-step risk even when its extra fields are meaningless. Add a
group-size-matched shuffled-refinement control:

1. start inside each `(family, action, target, repeat_state)` raw leaf;
2. jointly shuffle the observed `(intent, phase)` pairs among its operations;
3. preserve the exact pair multiset, so semantic subgroup count and subgroup-
   size multiset remain identical inside every raw leaf;
4. run 200 predeclared seed-derived permutations without retraining or changing
   risk.

This is a mechanism control, not a new headline contribution or a dynamically
selected baseline.

### Must-fix 3: simplify the verdict

AP and work-to-50 are co-primary measurements of the one conjunctive
hypothesis. The additional Revision 1 requirement that at least three of four
families favor semantic on both metrics is a redundant, overly conservative
gate. Use only the macro paired intervals plus the matched-shuffle specificity
check:

- `SUPPORTED`: semantic-minus-raw macro AP interval is above zero,
  raw-minus-semantic macro work-to-50 interval is above zero, and observed
  macro AP gain exceeds the 95th percentile of matched shuffled refinements;
- `CONTRADICTED`: either co-primary macro interval is entirely adverse;
- `INCONCLUSIVE`: every other valid outcome.

Per-family heterogeneity remains fully reported but does not become an extra
quota.

### Must-fix 4: make completion executable

Revision 2 must name preflight/full commands, input and output paths, and the
full completion rule. This should remain a simple ordinary experiment plan,
not a freeze, manifest, seal, or Git-dependent protocol.

### Should-fix

- Describe the role as a decisive RQ2 construction test, not a complete answer
  to RQ2.
- Rename the binary `0/+1` metric from StepAcc to
  `binary harmful-step accuracy`.
- Describe FirstErrAcc as a binary adaptation of the official first-`-1`
  definition.
- Use `risk > 0.5` as the harmful prediction threshold, so the all-null value
  0.5 remains uninformative.
- Verify one human label, 20 prediction slots, and one risk per step; exact
  three-step all-null handling; profile operation/risk conservation; and exact
  group-size preservation in every shuffled raw leaf.
- State that the experiment uses released outputs and incurs no API cost.

### Exposure disposition

The recorded partial human-label exposure remains acceptable for a valid
predeclared external test after adopting the already-published blind ensemble:
the risk signal is independent of human labels, the stack comes from the prior
AgentNet mechanism diagnosis, no exposed value selected a threshold or
comparator, and the complete population remains fixed. The source must not be
called a pristine never-viewed holdout. This residual risk does not justify
discarding families, narrowing RQ2, or changing the paper.

### Minimum Revision 2 hypothesis

> Using the same externally published, target-label-blind step-risk signal,
> target-preserving semantic context `(intent, phase)` improves
> human-harmful-step localization over the raw
> `(action, target, repeat_state)` profile—yielding higher macro AP and lower
> work-to-50—and its AP gain exceeds a group-size-matched shuffled refinement
> of the same raw profile.
