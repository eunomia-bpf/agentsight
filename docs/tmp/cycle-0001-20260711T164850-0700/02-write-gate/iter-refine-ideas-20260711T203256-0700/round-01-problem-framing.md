# Iter-Refine-Ideas Round 1 — Problem Framing

## Node identity

- Cycle: `0001`
- Gate: `WRITE_GATE`
- Loop: `iter-refine-ideas`
- Round: `01 — problem framing`
- Started from paper: `docs/paper/main.tex` after the admitted RQ2
  revision-0 experiment and the revision-1 plan-review return
- Review mode: independent full-paper read, followed by main-agent revision
- Paper target: AAAI-27 full paper
- Immutable RQ2: “Does Profiler Output Correspond to Real Problems?”

## Inputs read

The reviewer read the complete paper, `docs/user-instruction.md`, the
`iter-refine-ideas` skill and its research-taste references, and the admitted
experiment reports:

- `01-experiment-gate/loop-rq2-00/result-review.md`;
- `01-experiment-gate/999-gate-report-20260711T202112-0700.md`;
- the current paper and bibliography under `docs/paper/`.

The review received the paper and evidence rather than a desired verdict.  It
made no edits.

## Independent verdict

**Promising and important, but the framing was not scientifically sound before
revision.**  The durable problem is that run/span execution structure does not
provide cross-run semantic responsibility at the multiple granularities needed
for profiling.  The draft only implied this abstraction mismatch and instead
used an overly absolute “agents have no hierarchy” argument.  More seriously,
the abstract, introduction, RQ1, RQ2, and conclusion still presented the old
positive leaf-localization results even though the admitted held-out experiment
contradicted them.

This was a source-fidelity defect, not a reason to narrow the paper.  The
reviewer required the paper to retain the larger multi-resolution hypothesis
and explicitly mark it as the next decisive test.

## Must-fix findings

1. Replace every unsupported positive RQ2 leaf-localization claim with the
   admitted AgentRx/TELBench result.
2. State the root cause as an abstraction mismatch: execution spans answer
   where an event occurred in one run, while profiling asks which semantic role
   owns it across runs and granularities.
3. Explicitly challenge the belief that the emitted run/span tree is the one
   authoritative attribution hierarchy.
4. Replace generic questions-as-motivation with the operational consequence of
   recurring behavior being fragmented across hundreds of run trees.
5. Stop claiming that current observability tools cannot aggregate semantic
   attributes.  Acknowledge their per-run causal context and identify the
   missing end-to-end semantic identity, cross-layer inheritance, and
   query-time hierarchy mechanism.

The reviewer also identified three source-fidelity defects that would leave the
paper internally dishonest if only RQ2 were repaired:

- RQ1’s supported comparison is session-only mixed weight `84.4%` versus
  prompt-tag mixed weight `36.7%`, not “over 90% separated.”
- RQ3 has seven datasets above `0.7` V-measure but only six above `0.7` on both
  V-measure and applicable boundary F1.
- RQ4 combines the fresh-call count from one corpus run with p95 latency from a
  separate 900-request benchmark and treats a debug-build timing study as a
  full-pipeline cost experiment.

## Revisions made

### Problem and insight

- Reframed the operational pain as cross-run fragmentation that prevents teams
  from ranking optimization, failure-triage, and safety-review targets by
  aggregate impact.
- Replaced “no runtime hierarchy” with the more precise execution-structure
  versus semantic-responsibility mismatch.
- Added the challenged belief: an attribution hierarchy need not be fixed at
  execution time; semantic identity and cross-layer inheritance allow it to be
  projected at query time.
- Scoped AgentProf as offline, post-hoc semantic attribution rather than causal
  diagnosis, prevention, or online control.

### Existing work

- Replaced the straw-man comparison with a qualified statement: span systems
  provide valuable per-run context and can aggregate supplied attributes, but
  do not by themselves derive stable cross-run semantic identity, propagate it
  to downstream effects, and reconstruct alternative attribution hierarchies.

### Evidence and claims

- Replaced the old six-task RQ2 table with the admitted held-out result:
  - AgentRx AP `.02584` versus prevalence `.02236`, paired interval
    `[-.00035,.00798]`, and recall `.3425` at 30% work;
  - TELBench AP `.21487` versus prevalence `.21384`, paired interval
    `[-.00718,.01804]`, and recall `.1900` at 30% work.
- Recorded the stronger visible controls, including TELBench width-only
  AP `.27730` and the session baseline’s `.236` versus induced `.646` work at
  25% recall.
- Declared that flattened induced leaves contradict the positive leaf
  mechanism claim.
- Preserved the larger RQ2 as an explicit unanswered evidence TODO: test
  query-conditioned, coarse-to-fine, complete terminal scopes under bounded
  operation and token work against semantic-leaf, chronological, fixed-field,
  native-tree, and matched-shape baselines.
- Corrected RQ1 and RQ3 numerical wording.
- Reclassified RQ4 as unanswered and specified the missing release-build scale
  matrix instead of presenting incomparable timings as one result.

## Ambition and user-intent audit

The revision does **not** delete RQ2, remove problem localization from the
paper’s intended contribution, or retreat to resource attribution as the final
paper.  It distinguishes admitted evidence from the larger hypothesis and
requires the next experiment to exercise the actual hierarchy.  This remains
faithful to `docs/user-instruction.md`: bold hypothesis, careful validation, no
silent narrowing, and no unsupported positive statement.

## Build and format evidence

Commands:

```text
make clean
make all
pdfinfo main.pdf
```

Results:

- LaTeX build completed successfully.
- Final PDF: 8 US-Letter pages.
- Scientific content ends on page 7; references begin on page 7 and continue
  through page 8, within AAAI’s seven-content-page plus references layout.
- No undefined citation, undefined reference, or LaTeX error remained in the
  final log.
- One minor `0.99261pt` table overfull box remains for the writing/layout loop.

## Round decision

**PASS TO ROUND 2.**  The problem framing is now source-faithful and states a
larger, testable principle.  The full idea layer is not yet approved: the next
round must adversarially attack novelty, mechanism necessity, and whether the
contribution/RQ set is coherent after admitting the negative RQ2 result.
