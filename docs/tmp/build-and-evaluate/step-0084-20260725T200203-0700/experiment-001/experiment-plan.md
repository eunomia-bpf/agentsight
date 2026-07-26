# Experiment plan — source-only shared-parent synthesis

Timestamp: 2026-07-25T20:02:03-07:00
Status: proposed for serial independent review

## RQ and tested hypothesis

Paper-level subjects remain fixed.

- RQ1: cross-run multi-resource attribution.
- RQ2: correspondence with real problems and source-drillable usefulness.
- RQ3: automatic operation structure and reusable naming.
- RQ4: token, time, and system cost.

This experiment tests one hypothesis inside those RQs:

> After a complete source-visible hierarchy exists, an automatic backend can
> insert reusable shared responsibility parents over recurring but distinct
> child operations, improving population-level pprof answerability while
> preserving child detail, source evidence, additive mass, and ordinary
> structure quality.

The experiment does not test whether another boundary detector, benchmark, or
larger language model is better.

## Fixed population and inputs

- Complete AgentRewardBench mixed-outcome population already materialized in
  the Step 0077 workspace: 440 sessions, 15,338 source nodes, 7,229 operation
  leaves, and 51,904,621 provider-reported trace tokens.
- Starting annotation: frozen iteration-007 terminal annotation with 2,228
  marks.
- Constructor-visible inputs:
  - current `trace.jsonl`;
  - current `annotation.json`;
  - CLI aggregate diagnostics and a compact Markdown catalog of current full
    paths with representative bounded source contexts;
  - the generic user question: which recurring responsibilities consume
    resources across runs, and where does repeated or unfinished work
    concentrate?
- Scorer-only inputs, hidden until annotation is final:
  - success/failure outcomes and 338 bad--good pairs;
  - expert looping labels;
  - the prior paper hierarchy, figures, case prose, recovery/completion names,
    and all prior answerability verdicts.

## Minimal mechanism change

Keep all current validation, local fingerprints, and annotation format. Add one
source-only synthesis action to the revision protocol:

- a backend may insert the same short parent tag around multiple source-grounded
  occurrences that share a broader responsibility;
- it must preserve the existing detailed child tags when those children remain
  useful;
- it may not merge unrelated child evidence merely to increase reuse;
- a proposed parent must occur in at least two sessions and have at least two
  distinct child paths in the population catalog before local application;
- those numeric conditions are eligibility checks, not quality scores or
  targets.

No new product file or non-pprof output is introduced. The backend still edits
only `annotation.json`; the CLI still regenerates `trace.jsonl`,
`stacks.folded`, diagnostics, and one requested `.pb.gz`.

## Execution

### Phase 1: source-only global synthesis

One independent automatic backend reads the current path catalog and bounded
representative contexts. It writes a detailed Markdown decision report with:

- proposed shared parent tag;
- member full paths and representative source IDs;
- source-visible semantic justification;
- explicit distinctions that must remain child operations;
- rejected candidate families.

The report is an experiment record, not a product contract. It must not contain
or infer outcome, reward, expert, or prior-paper information.

### Phase 2: local application

Independent backend workers receive only one proposed family, its affected
session intervals, current annotations, and bounded source context. They either
insert a noncrossing shared parent while retaining useful children or reject
the proposal with a source-grounded reason. They edit only their assigned
`annotation.json`.

The root merges validated disjoint changes, regenerates the complete workspace,
and runs the full test suite. Stable fingerprints reopen only source intervals
changed by the inserted parent.

### Phase 3: outcome-blind convergence check

A fresh source-only reviewer reads the regenerated path catalog and the fixed
generic user question. It may request one more local synthesis/application pass
only for a concrete missing or misleading shared responsibility. Unchanged
accepted families remain cached. Stop when a complete catalog review makes no
annotation change or an exact annotation state repeats.

Convergence of source review is necessary but not sufficient for a positive
scientific result.

### Phase 4: fixed scoring

After the annotation and both pprof widths are fixed:

1. a masked reviewer compares the candidate with the frozen latest-terminal and
   paper-hierarchy profiles on the same population question;
2. the existing expert-looping evaluator computes ordinary AP and a
   task-cluster bootstrap interval;
3. the existing first-pass/terminal structural diagnostics are recomputed;
4. all token/time/system costs are summarized.

## Primary and secondary measurements

### Primary product measurement

Masked answerability rubric, five fields scored 0/1/2:

1. complete operation paths are semantically interpretable;
2. failed-side recurring responsibilities are supported;
3. successful-side recurring responsibilities are supported;
4. exact source session/evidence drilldown is available;
5. operation-count versus token-width comparison is answerable.

The candidate passes only with no field regression and at least one strict
improvement over the latest terminal profile. Comparison with the paper
hierarchy determines whether the new automatic mechanism has recovered the
existing product quality rather than merely beating a weak first pass.

### Standard scientific endpoint

- Expert-looping correspondence: non-interpolated average precision over all
  435 consensus-labeled trajectories.
- Baselines: prevalence, the existing fixed-chain repeated/error projection,
  the frozen paper hierarchy, and the latest terminal hierarchy.
- Uncertainty: 10,000-draw task-cluster bootstrap for candidate-minus-prevalence
  and candidate-minus-each hierarchy baseline.

AP measures correspondence, not causality or detector superiority.

### Structural and validity measurements

- Exact operation/token mass conservation.
- Source-session and evidence-ID coverage.
- Annotation count; semantic depth distribution; unique full stacks.
- Cross-session tag reuse and singleton counts as explanations only.
- Complete-path parent/child examples; no depth or warning-count target.

If a compatible independent boundary/partition scorer exists for this
population, report ordinary B-cubed and exact boundary P/R/F1. AgentReward has
no gold nested hierarchy, so absence of that scorer must not be replaced by a
bespoke topology score.

## Cost measurement

Record every automatic call and report:

- provider input, cached input, derived uncached input, output, and reasoning
  output tokens;
- exact logical request and annotation tokens;
- end-to-end elapsed time and summed worker-seconds;
- backend calls, retries, failures, and fixed concurrency;
- unique source nodes read and fraction of the complete trace;
- deterministic regeneration/replay wall time and peak RSS;
- per-session and per-1,000-source-node normalization.

The final RQ4 presentation must keep five rows separate:

1. fresh source-only construction;
2. shared-parent convergence/revision;
3. later local incremental update;
4. deterministic pprof replay;
5. query-aware direct trace reading.

The current 191.8M-token seven-pass history is a failed whole-review policy, not
the cost of the corrected algorithm. A clean fresh-to-terminal rerun is
authorized only after this experiment shows that shared-parent synthesis
improves the fixed product/scientific endpoints.

## Decision

- **Positive:** masked answerability has no regression and a strict improvement
  over the latest terminal profile, shared recurring parents retain source
  drilldown, and expert-looping AP is above prevalence with a positive
  task-cluster interval.
- **Iterate mechanism:** any of those conditions fails. Revise the synthesis or
  local-application instruction using source-only evidence and rerun this same
  population; do not change the scientific endpoint, expected answer, or
  benchmark.
- **Paper disposition:** only a positive final mechanism and its complete
  measured cost enter the paper. All other runs remain in this auditable
  history.

