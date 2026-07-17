# Independent RQ3 Construct and Metric Audit

## Scope and Independence

The reviewer performed a read-only reconstruction from the original submodule,
the raw R285 leave-dataset-out summary, the current paper, and the implementation
scripts. The reviewer was instructed to use the auto-research orchestrator,
experiment-admission, and whole-paper review principles, to recompute rather
than accept the root's interpretation, and to modify no files.

## Verdict

**Scientific route: PASS after two bounded corrections. Do not admit a new
literal-phase experiment.** The original RQ3 evaluates mapping-derived phase
structure, not independent literal phase names. The current standard-metric
evidence is sufficient to route to targeted WRITE and then an unprimed
whole-paper REVIEW. The proposed correction preserves the thesis, the four RQs,
the two core abstractions, and the positive RQ3 program.

The reviewer identified two must-fix items in the draft:

1. explicitly cross-reference the existing complete phase-structure result in
   RQ3; and
2. classify token-weighted B-cubed as a published weighted extension with a
   non-default provider-token application, not as a purely project-invented
   metric.

Both corrections were applied before final verification.

## Original RQ3 Reconstruction

The read-only original paper compares mapping-derived `phase` with native
`action` through V-measure and compares their transition locations through
boundary F1. The implementation confirms that:

- `PHASE_FAMILIES` supplies the phase taxonomy in
  `script/operation_map_infer.py`;
- leave-dataset-out fitting retains predicates observed in other datasets;
- `script/operation_leaveout_eval.py` explicitly scores `phase` against
  `action`.

The protocol therefore evaluates an action-to-phase coarsening and its
transition structure. It has no independent human phase-name truth and cannot
authorize a literal phase-name accuracy claim.

## Independent Raw-Result Recalculation

The raw summary contains 9 datasets and 13,265 operations:

| Dataset | Operations | Mapped V | Boundary F1 | No-map V | No-map boundary |
|---|---:|---:|---:|---:|---:|
| AgentTrek | 200 | 0.8617 | N/A | 1.0000 | N/A |
| AndroidControl | 9 | 0.7157 | 0.7273 | 1.0000 | 1.0000 |
| API-Bank | 48 | 0.0000 | N/A | 0.0000 | N/A |
| GUI-Odyssey | 7,868 | 0.8105 | 0.8416 | 1.0000 | 1.0000 |
| Mind2Web | 774 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| SWE-agent | 496 | 0.9264 | 0.9622 | 1.0000 | 1.0000 |
| ToolBench | 866 | 0.1342 | 0.3533 | 0.1342 | 0.3533 |
| WebLINX | 500 | 0.8717 | 0.8598 | 1.0000 | 1.0000 |
| WebShop | 2,504 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

The independent counts are:

- V-measure greater than 0.7: 7/9;
- both numeric metrics greater than 0.7: 6/9;
- datasets with an applicable boundary measurement: 7;
- applicable datasets with both metrics greater than 0.7: 6/7.

AgentTrek and API-Bank have no adjacent reference pairs; their raw zero sentinel
must not be treated as a measured boundary score. The original caption and
prose saying “seven of nine exceed both” is therefore incorrect. Mapping also
improves neither metric over the no-map representation: mapped V decreases on
five datasets and ties on four; mapped boundary F1 decreases on four and ties
on five. This supports the coarsening interpretation, not phase-name accuracy.

The value 0.7 is an author-selected descriptive threshold, not a standard
accuracy criterion.

## Metric Findings

- AP/MAP are standard ranking metrics and are appropriate as the RQ2 primary.
- Macro-F1 and accuracy are standard closed-set multiclass metrics; macro-F1 is
  the stronger primary under class imbalance.
- V-measure is a standard permutation-invariant clustering metric and cannot
  prove literal label names.
- Ordinary unweighted B-cubed is a standard partition/coreference metric.
- Exact-boundary precision/recall/F1 uses standard binary formulas on the
  project's declared adjacent-pair unit; it is not an official universal
  benchmark protocol.
- Recall at a 20% operation-inspection budget is a protocol-specific secondary
  analysis, not fixed-rank `Recall@20`.
- Per-object weighted B-cubed has published precedent. Provider-token weights
  are a non-default application and stay secondary to ordinary B-cubed.

## Reused Phase Evidence

The reviewer found that a new phase experiment is unnecessary even for an
explicit phase-structure result. The complete Step 0035 CodeTraceBench run
already evaluates the deterministic phase field against independent human
stages:

- 405 complete source-valid failed trajectories;
- 20,866 operations;
- 2,948 human-verified contiguous stage intervals;
- ordinary unweighted B-cubed F1 of 0.654445 for phase-only grouping.

The current paper already reports this result in RQ1. RQ3 now cross-references
it and states that the remainder of the section tests literal labels, other
partitions, and boundaries. This closes the only opening-to-result consistency
gap without inventing a new experiment or taxonomy.

## Experiment Admission Decision

GUIDE/GuideBench remains a scientifically credible optional future source, but
its data are access-gated in the current environment. OpenDiscoveryTrace phases
are elicited from the acting model itself and are not independent gold. Neither
source justifies blocking the autonomous loop.

A new literal-phase experiment would currently add a taxonomy cell without
changing the constructor or the paper-level RQ3 answer. It fails the
paper-value admission test. The correct next outer action is an unprimed
whole-paper review with external novelty search; that review may select a new
experiment only if it can change a paper-level RQ answer or improve the actual
system.

## Final Disposition

The root incorporated both reviewer findings:

- RQ3 now explicitly reuses the 0.654 ordinary B-cubed phase-structure result;
- the weighted-B-cubed classification is corrected.

No thesis, RQ title, contribution, algorithm, experimental value, abstract,
introduction, background, motivation, system design, or submodule file was
changed as part of the construct correction.

The second convergence audit also found and then cleared a one-line AAAI page
spill introduced by the new cross-reference. The final PDF is nine US-letter
pages; the complete Conclusion ends on page seven, page eight begins with
References, the log has no undefined citation/reference or overfull box, and
all fonts are embedded Type 1. This formatting repair changed no claim.

Final convergence verdict: **PASS; 0 must-fix items; proceed to unprimed
whole-paper review.**
