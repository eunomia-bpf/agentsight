# Idea Round 5 — Top-Conference Reviewer Stress Test

## Context

- **Started:** 2026-07-11T21:36:00-07:00.
- **Completed:** 2026-07-11T22:03:43-07:00.
- **Cycle / gate / node:** cycle 0001 / WRITE_GATE /
  `iter-refine-ideas` Round 5.
- **Parent:** `round-04-cross-alignment.md`.
- **Final status:** `HARDENED/PASS` after four adversarial
  review/fix/re-attack iterations.

A new subagent with no prior conversation read the complete current paper,
bibliography, research-taste rubric, and idea checklist. It was instructed to
write the strongest AAAI/top-conference idea reject, not to improve prose or
excuse missing experiments. It did not read `docs/tmp`, edit files, or run Git.
The main agent repaired the paper and rebuilt it between attacks.

The active user constraint remained decisive: do not narrow the paper to leaf
grouping or one failure benchmark; preserve the cross-run profiling thesis,
full hierarchy, failures, safety, wasted work, and complete cost. Repairs could
make claims falsifiable or reject unsupported mechanisms, but could not silently
replace the intended problem with an easier one. The admitted RQ2 wording—“Does
Profiler Output Correspond to Real Problems?”—also remained immutable; its
construct was made explicit immediately beside it.

## Attack 1 — “SQL/pprof Plus an Ordinary Ranker”

### Reject argument

The reviewer first reconstructed a direct rejection:

- manual stacks are already `GROUP BY`/`ROLLUP`, arbitrary trees are path keys,
  and pprof/Perfetto already aggregate tags;
- the only risky mechanism appeared to be a query-specific risk/prior attached
  to any tree;
- SDBL already established scope-before-localization;
- therefore accounting and future diagnostic retrieval looked like two attached
  papers rather than one non-obvious principle.

It also found that old RQ1 tested self-defined grouping and mass conservation,
not correct cross-layer attribution; old RQ4 merely asked for a cost number and
could not fail; the three RQ2 outcomes used query-specific localizers without a
shared explanation; the belief that attribution trees are execution-fixed was
weak given the paper's own SQL/label concession; substrate terminology obscured
the scientific unit; and the generic “claim-facing evaluation” contribution did
not promise independently rejectable knowledge.

### Repair

The paper now centers one thesis:

> Stable semantic scopes recurring across runs may retain enough diagnostic
> structure to make a pooled profile a better index for an untouched trace than
> that trace's own execution tree.

The challenged tradeoff is no longer whether tags can be regrouped. It is the
belief that diagnosis must remain trace-local because pooling destroys order and
context. Weighted records, path keys, SQL/pprof aggregation, and rendering are
explicit substrate. **Stable semantic scope** is the scientific unit.

The original three contributions remain, but their roles are stronger:

1. semantic scope-tree model and stable-scope contract;
2. AgentProf plus its whole-scope navigation policy;
3. cross-domain empirical characterization of representation gains, policy
   boundaries, outcome transfer, cost, and failure regions.

RQ1 now asks whether recorded-correlation inheritance assigns effects to an
independently verified semantic parent while conserving mass. It reports current
conservation evidence only as a partial answer and requires an independent
native tool/span plus sandbox-process-lineage oracle with attribution
precision/recall, unassigned effects, duplicates, and mass loss.

RQ4 now asks whether the diagnostic-work advantage survives complete end-to-end
cost and has a fixed-budget/fixed-diagnostic-outcome failure rule. The paper also
grounds importance with its real 325-trajectory workload: session-only grouping
leaves 84.4% of effect weight mixed, and `cargo test` recurs 2,903 times across
review/debug/refactor/test contexts.

Failure, safety, and redundancy now share one query-independent stable scope
vocabulary. Each may use an outcome-specific query/risk function, but within an
outcome every representation receives the same risk features, labels, priors,
capacity, and budget. A result must hold separately for all three outcomes.

## Attack 2 — Point Coverage Makes Whole-Scope Navigation Dominated

### Reject argument

The first repaired design still used external gold operation/span coverage at a
fixed content budget as the primary outcome. The reviewer showed that an atomic
method with the same scope prior could reproduce every selected scope by giving
its score to each member, then omit low-value members. Whole-scope emission could
only tie or lose. Denying the atomic method the prior would make the baseline
unfair. Thus the proposed identity × structure × navigation interaction was
unidentifiable under the paper's own metric.

### Repair

The paper changed the primary construct rather than hiding the control:

- primary outcome: benchmark-native diagnostic accuracy from the same fixed
  downstream localizer after it sees selected content;
- co-primary where published: completion of an independently defined
  multi-operation diagnostic context;
- secondary only: point/span coverage, which explicitly cannot establish a
  whole-scope advantage.

The fresh RQ2 program uses published tasks: failure attribution/localization on
Who&When and TRAIL, unsafe-tool diagnosis on ToolSafe/TS-Bench, and redundant
step diagnosis on RedundancyBench. Existing SATraj-OS, AgentRewardBench, and
AgentNet assets remain development sources, not fresh confirmation.

The paper also made every identity/tree cell constructible: trace-local and
frozen identities are metadata on flat/native/matched structures and determine
membership only in their corresponding semantic tree; matched trees preserve
size/depth while permuting membership without labels.

## Attack 3 — Bundle Emulation and RQ4 Outcome Drift

### Reject argument

Fixed-localizer accuracy removed the point-coverage dominance, but a
bundle-capable atomic control could still reproduce every whole-scope output.
Without that control, navigation could win only because the atomic baseline was
forced to fragment context. In parallel, RQ4 accidentally reverted to point
coverage, so RQ2 and RQ4 would test different constructs.

### Repair

The central informational test is now **frozen identity × semantic structure**,
not navigation. For each representation, the experiment compares its best fair
selection policy. Navigation remains Contribution 2's mechanism and is evaluated
in a separate policy ablation:

- pointwise ranking;
- whole-scope traversal;
- bundle emulation that may emit exactly the same bundles, in the same order,
  under the same information and budget.

Identical bundle output plus the fixed localizer must produce identical
diagnostic accuracy. Only selector cost or implementation behavior may differ.
If whole-scope beats pointwise but ties bundle emulation, it is reported as a
useful policy restriction under a decomposable selector, not as new information.
The scientific thesis survives only if the best development-selected policy on
the frozen semantic representation beats the best policies on alternative
representations.

RQ4 was aligned with RQ2: it now fixes diagnostic accuracy or independent context
completion and compares complete cost, or fixes total model-token/wall-time
budgets and compares those same diagnostic outcomes. Point coverage remains
secondary.

## Attack 4 — Query-Dependent Identity and Target-Policy Leakage

### Reject argument

The formal identity function still appeared as `g_theta(segment, q)`, contradicting
the claimed query-independent vocabulary across failure, safety, and redundancy.
Also, “best fair policy” could be selected after target labels were visible,
creating policy-selection leakage. Finally, Contribution 3 implied whole-scope
accuracy might beat output-equivalent bundle emulation, which is logically
impossible with the same fixed localizer.

### Repair

- The identity function is now `g_theta(segment)`. Diagnostic query `q` never
  changes identities or tree boundaries; it affects only risk, prior, and
  navigation priority.
- For every representation, policy family, selection rule, and hyperparameters
  are selected only on development trajectories and frozen before untouched
  target-family scoring. Target labels only score the already selected policy.
- Bundle emulation is an expected-equivalence accuracy control. Contribution 3
  asks when whole-scope beats pointwise and how selector cost compares with the
  output-equivalent bundle control; it does not predict an accuracy win over
  identical output.

## Final Independent Verdict

The fourth re-attack returned **HARDENED/PASS** with zero easy idea-layer
rejections. It confirmed:

- one query-independent stable identity and frozen tree boundary definition;
- central novelty in reusable identity × semantic structure under a fair,
  development-selected policy;
- navigation honestly retained as a system policy with pointwise and exact
  bundle-equivalence controls;
- aligned RQ2 and RQ4 primary outcomes;
- explicit falsifiers for RQ1, RQ3, and RQ4;
- one frozen vocabulary across failure, safety, and redundancy, with separate
  outcome success requirements;
- independently assessable empirical knowledge in Contribution 3;
- substrate demotion and acceptable concept economy;
- direct real-workload importance grounding;
- no negative result converted into support and no ambitious dimension removed.

The final reviewer noted one writing-only sentence that still credited the
navigator with making the central prediction falsifiable. It was immediately
corrected to credit the best-policy representation comparison and describe the
navigator as one tested policy.

## Compilation, Protected State, and Remaining Gaps

The complete paper was rebuilt after the final change:

```text
cd docs/paper
make clean
make all
pdflatex -interaction=nonstopmode main
```

The build exits successfully with resolved citations and references, US-Letter
format, and two known overfull boxes (8.11 pt in G3; 0.99 pt around the RQ2
table). The paper is now 11 pages. Scientific content exceeds AAAI's seven-page
content allowance by several pages; this is a mandatory writing/layout problem,
not a reason to remove the model, outcome breadth, falsifiers, or honest status.

The read-only `docs/agentpprof-paper/` subproject remains unchanged at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. No branch, stage, commit, push,
submodule, `docs/evaluation.md`, or `docs/idea-story.md` mutation occurred in
this round.

The idea layer is hardened but the paper is emphatically not submission-ready.
The following are experiment/implementation blockers, not framing defects:

- implement the frozen induced-identity labeler and navigator;
- complete RQ1 independent lineage correctness;
- complete fresh RQ2 failure/safety/redundancy representation and policy tests;
- complete RQ3 frozen transfer across agents and problem types;
- complete RQ4 release-scale end-to-end cost.

## Next Action

Round 5 completes the five mandatory idea rounds. The next node is the
independent idea outer audit, which must verify the reports against the current
paper and admitted evidence without prior verdict priming. If it passes, the
WRITE gate proceeds to the complete `iter-refine-writing` cycle. The writing
loop must compress the current 11-page scientific story to AAAI's seven content
pages without changing RQ meaning, deleting ambitious contributions, or turning
unrun experiments into results.
