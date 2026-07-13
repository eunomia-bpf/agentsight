# AgentNet RQ2 implementation report

**Node completed:** 2026-07-13T03:32:52-07:00  
**Outer gate:** EXPERIMENT  
**Inner stage:** approved-plan implementation  
**Execution status:** `VALID`  
**Scientific status:** `NOT_EVALUATED_IMPLEMENTATION`

## Research object preserved

This implementation evaluates one construction under RQ2: whether a
target-label-blind cross-run semantic AgentProf profile localizes official
AgentNet step-quality problems better than fixed raw-action grouping and
ungrouped transferred risk across reciprocal Windows/macOS transfer.

It does not edit or reinterpret the paper thesis, the four RQs, the positive
RQ2 hypothesis, or the canonical story. No file under `docs/paper/`, the
read-only `docs/agentpprof-paper` submodule, or the shared skill repository was
changed.

## Implemented path

`script/agentnet_cross_platform_eval.py` implements the approved ordinary
Markdown plan as five concrete stages:

1. `prepare` verifies the two official AgentNet files at revision
   `d76ee50a63fad81cfdbe576416757d7c2091ed50`, joins the complete metadata and
   trajectory populations, preserves original domain/application names, and
   writes one visible projection plus separate Windows and Darwin label files.
2. `predict-fold` receives the visible projection and exactly one reference
   platform label file. Its parser has no target-label argument. It fits the
   fixed logistic model, saves held-out predictions and every group assignment,
   runs real AgentProf 0.2.37, verifies exact view counts, and writes the entire
   deterministic bootstrap attempt sequence before target scoring can begin.
3. `score-fold` receives only saved label-blind artifacts plus one held-out
   label file. It rechecks prediction/group/risk/profile conservation, applies
   the fixed truth table, and evaluates the first required valid paired task
   draws. It never modifies the fold artifacts.
4. `preflight` defaults to exactly 256 tasks per platform and always reports
   `NOT_EVALUATED_PREFLIGHT`; it cannot emit a scientific verdict.
5. `full` rejects subsets and any settings other than 10,000 valid draws,
   50,000 maximum attempts, seed 4204, AgentProf 0.2.37, and the complete
   12,364-Windows/5,168-Darwin projection with exact label operation coverage.

Only the four approved pure AgentNet helpers are reused:
`agentnet_code_action`, `agentnet_action_target`,
`agentnet_action_phase`, and `repeat_features_for_signatures`.
`normalize_agentnet()` is never called. `sanitize_label` only normalizes the
approved visible source strings and does not inspect any outcome.

## Metrics and controls

The implementation constructs flat, fixed-session, source-native, raw-action,
and semantic views through AgentProf. Exact-repeat and ungrouped transferred
risk remain fixed controls. Primary grouped ranking uses predicted problem
density with complete exact-score tie blocks. The scientific verdict uses only
the separately bootstrapped within-fold semantic-vs-raw and
semantic-vs-ungrouped comparisons declared in the plan; independently fitted
Windows and macOS risks are never pooled into one ranking.

Base-only diagnostics report group count, complete-tie groups-to-50% positives,
sessions per hot group, annotation coverage and domain distribution, and
eligible per-domain disaggregation. Additive risk mass is strictly a
group-opening diagnostic; it reports no operation AP, recall@30, or
work-to-50 and cannot affect the verdict.

## Boundary and failure checks

- Projection validation rejects any outcome, reflector, completion, post-hoc
  score, or other forbidden key and rejects duplicate operation IDs.
- The predictor CLI rejects a target-label argument.
- Predictions, group assignments, group summaries, bootstrap draws, model
  reports, and profile reports are hashed before scoring.
- Correct, alternate, wrong-platform, and withheld target labels cannot alter
  any label-blind fold artifact.
- Every saved group risk sum and density is recomputed before labels are used;
  totals must match predictions and real AgentProf operation/group counts.
- All maximum-attempt draw specifications are saved before scoring. The scorer
  processes them in deterministic batches and stops after the first required
  valid draws, so labels can discard a draw but cannot create or append one.
- An incomplete bootstrap population returns execution `INCOMPLETE`, never a
  scientific negative.

## Verification completed

The following command completed with 9/9 tests passing:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 script/test_agentnet_cross_platform_eval.py
```

The tests cover the combined-label truth table, conservative complete-tie
metrics, forbidden-field separation, predictor CLI isolation, full-population
and fixed-setting rejection, exact AgentProf version rejection, real
AgentProf profile conservation, alternate-label scoring, wrong-platform label
rejection, withheld-label rejection, unchanged label-blind digests, and the
group-opening-only mass diagnostic.

The related agent-trace regression selection also completed with 16/16 tests
passing. `pyflakes`, Python byte compilation, and `git diff --check` completed
without a code or patch error. Local `flake8` could not start because its
installed configuration references an unavailable optional
`wemake_python_styleguide` plugin; this environment issue is not used as a
research or preflight gate.

## Next transition

The independent implementation review converged to `PASS`. The next legal
stage is official source preparation followed by the fixed 256-task-per-platform
REAL PREFLIGHT. No scientific result exists at this node.
