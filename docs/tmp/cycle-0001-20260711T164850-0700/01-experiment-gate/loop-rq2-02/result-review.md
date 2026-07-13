# Independent RQ2 Result Review

**Timestamp:** 2026-07-12T04:46:18-07:00  
**Reviewer:** fresh independent subagent; read-only  
**Scope:** approved plan, plan reviews, preflight, full report, runner,
official Hodoscope sources, and all saved full-run rankings and summaries

**run status: valid**

**RQ answer: contradicts**

This is a complete, interpretable negative result. Under the tested Hodoscope
iQuest/SWE-bench condition, the prespecified recursive-positive rule fails
against Hodoscope, flat, and native baselines. It contradicts the expectation
that the tested recursive semantic stack would reliably reduce inspection
effort. It does not justify narrowing RQ2 or the paper's larger contribution.

## Independent Audit Scope

The reviewer read:

- `experiment-plan.md`;
- `plan-review.md`;
- `preflight-report.md`;
- `full-execution-report.md`;
- `script/hodoscope_representation_eval.py`;
- official `run_table2.py`, `dataset_stats.py`, and Hodoscope sampling code;
- 20 Phase A/B seed directories, 80 metric cells, and all 160 scored and
  unscored rankings;
- both paired summaries, the official Table 2 log, and official data/version
  metadata.

The reviewer changed no files, paper text, skills, or Git state.

## Validity Checks That Passed

- Phase A has ten seeds and Phase B has ten seeds, with all four methods per
  seed complete and no missing, no-hit, or excluded cell.
- Each Phase A permutation contains exactly 2,003 unique target actions; each
  Phase B permutation contains exactly 4,006.
- Within each paired seed, all four methods have identical action sets, action
  metadata, character lengths, and t-SNE coordinates.
- Flat and recursive views have identical terminal fine-cluster assignments for
  every action and seed. Recursive paths have three levels, so the hierarchy
  mechanism was exercised.
- No unscored ranking contains `oracle_positive`. Each scored copy differs only
  by the joined oracle field, and timestamps show that the unscored copy was
  written first.
- Independently rebuilding action keys from official iQuest JSON yields 4,006
  target actions and 132 `git log|git show` positives. Raw character counts and
  oracle labels match source actions exactly.
- Official `dataset_stats.py` independently yields 11,855 total actions, 7,849
  reference actions, 4,006 target actions, and 132 positives.
- Every first-hit rank, inspected fraction, inspected-character count, and
  hits-at-20 value recomputes exactly from the saved permutations.
- Every Hodoscope seed retains exactly 500 unchanged official-prefix actions;
  every first hit occurs within that prefix, so the deterministic tail extension
  cannot affect the outcome.
- Paired deltas, win rates, and 10,000-resample bootstrap confidence intervals
  reproduce exactly using the runner's random-number order.
- The official Table 2 command completed ten seeds for all three testbeds with
  exit status zero; the report agrees with its log.
- The 226 HDBSCAN `no defined clusters` warnings arise from the official
  HDBSCAN sweep, not the density-contrast Hodoscope row used as the primary
  baseline.
- Software versions, Hugging Face revision `17c395...`, five input hashes, and
  official Hodoscope source content are recoverable. Neither comparison path
  calls a model or external API.

## Independently Verified Results

### Phase A: Published 50%-Per-Cohort Sampling

| View | First-hit rank | Characters | Hits@20 | Runtime after shared t-SNE |
|---|---:|---:|---:|---:|
| Hodoscope | 2.9 +/- 0.3 | 6,403.4 +/- 3,856.9 | 1.2 +/- 0.4 | 1.003 +/- 0.153 s |
| Flat | 55.4 +/- 95.7 | 205,746.9 +/- 336,667.1 | 0.6 +/- 0.66 | 27.046 +/- 2.346 s |
| Native | 36.8 +/- 31.8 | 88,563.0 +/- 75,584.0 | 0.5 +/- 0.67 | 0.290 +/- 0.038 s |
| Recursive | 24.9 +/- 15.8 | 61,671.8 +/- 45,158.4 | 0.5 +/- 0.67 | 25.971 +/- 3.359 s |

Prespecified recursive deltas (`recursive rank - baseline rank`):

- versus Hodoscope: `+22.0`, 95% CI `[12.3, 31.8]`, win rate `0.0`;
- versus flat: `-30.5`, 95% CI `[-97.3025, 13.3]`, win rate `0.5`;
- versus native: `-11.9`, 95% CI `[-36.5, 9.0]`, win rate `0.5`.

### Phase B: Complete 250-Trajectory Corpus

| View | First-hit rank | Characters | Hits@20 | Runtime after shared t-SNE |
|---|---:|---:|---:|---:|
| Hodoscope | 3.0 +/- 0.0 | 5,312.6 +/- 136.3 | 1.0 +/- 0.0 | 3.058 +/- 0.037 s |
| Flat | 94.5 +/- 65.2 | 322,554.8 +/- 225,430.0 | 0.1 +/- 0.3 | 32.910 +/- 1.731 s |
| Native | 71.3 +/- 14.3 | 144,818.9 +/- 31,432.1 | 0.0 +/- 0.0 | 0.981 +/- 0.040 s |
| Recursive | 76.3 +/- 58.4 | 203,676.4 +/- 159,633.3 | 0.2 +/- 0.4 | 33.413 +/- 1.797 s |

Prespecified recursive deltas:

- versus Hodoscope: `+73.3`, 95% CI `[40.5, 112.0025]`, win rate `0.0`;
- versus flat: `-18.2`, 95% CI `[-83.1, 44.3025]`, win rate `0.7`;
- versus native: `+5.0`, 95% CI `[-26.3, 39.7025]`, win rate `0.5`.

## Must-Fix Reporting Boundaries

### 1. Disclose the Phase B seed deviation

The plan says `s=0..9`, whereas the runner used seeds `1..10`. Therefore the
statement that no full-run plan deviation occurred is inaccurate. The ten runs
come from a mechanically predetermined range and show no sign of post-result
seed selection, so this does not invalidate the result. No rerun is required
unless the paper insists on claiming literal execution of seeds `0..9`; that
claim would require replacing seed 10 with a new seed-0 Phase B run and
recomputing its summary.

### 2. Do not present Hodoscope's raw `contrast` field as observed zero

The Hodoscope permutation is produced by its official KDE density-gap and FPS
functions, but the adapter subsequently writes `contrast: 0.0` for every raw
Hodoscope row. That is not the actual score. The field must be removed, written
as `null`, or documented as unavailable; alternatively, the real official score
can be exported. This metadata defect does not affect order or metrics and does
not require an experimental rerun.

### 3. Preserve the measured cost boundary

The per-method runtime is construction plus ranking after the shared t-SNE; it
is not full end-to-end time and is not split into construction and query. The
comparison command's 37,922.76 user CPU seconds is not preserved in the cited
raw log, although peak RSS is recoverable from metrics and approximately 31
minutes of wall time is consistent with artifact timestamps. The existing
inspection-effort result is valid. A complete or component-separated
end-to-end cost claim would require new instrumentation and execution.

### 4. Keep Phase A percentage denominators distinct

Official Table 2's `0.07%` uses the complete 4,006-action target corpus as its
denominator even though each seed samples 2,003 target actions. The matched
runner's fraction uses 2,003. These values cannot share a table column without
an explicit denominator definition.

### 5. Do not infer a flatness or continuous-geometry cause

Hodoscope differs in both representation and continuous KDE density-gap
normalization. The comparison that isolates the addition of recursive parents
is flat versus recursive, and both phases have confidence intervals crossing
zero. The supported statement is:

> The official Hodoscope bundle decisively outperforms the tested discrete
> hierarchical bundle, while adding recursive parents produces no stable
> advantage over its matched flat terminal partition.

Discrete quantization destroying local geometry is a plausible next hypothesis,
not an established mechanism from this run.

### 6. Name the native baseline precisely

The native view groups exact released `turn_id`/turn positions across
trajectories. It is not a complete `trajectory -> turn -> action` execution
tree. It is valid for the approved comparison, but the paper must not claim
that every source-native hierarchy has been evaluated.

## Optional Reporting Improvements

- Report standard deviations for characters, hits@20, and post-t-SNE runtime if
  those metrics appear in a paper table.
- State that Phase B bootstrap variation is algorithmic randomness on one full
  corpus, not uncertainty across tasks or datasets.
- A paired-seed plot would expose the high variance of flat, native, and
  recursive methods more clearly than means alone.
- Retain the explanation of the 226 official HDBSCAN warnings; do not modify the
  unrelated official sweep for this experiment.

## Final Scientific Interpretation

The full run is valid and complete, and its expected recursive advantage is
contradicted. The tested fixed recursive hierarchy does not reliably reduce
inspection effort, while Hodoscope's official density-comparison bundle finds
the published effect much earlier. The valid response is to retain the broad
RQ2, record the negative condition, and test a stronger explanation or a
different real profiling question later. It is not to delete the result,
narrow the contribution, or treat the failed hierarchy as evidence that agent
profiling has no larger representation problem.
