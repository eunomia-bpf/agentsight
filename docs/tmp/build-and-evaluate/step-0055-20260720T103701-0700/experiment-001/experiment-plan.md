# Experiment Plan: RQ3 Visible Task-Semantic Profile Identity

## Research Question

- RQ exactly as written in the paper: **RQ3 — How accurate are the tags?**
- Specific uncertainty: whether the identity actually folded by a task-semantic
  profiler—the complete visible semantic label path—gives a more faithful
  session-local workflow partition than Step 0054's hidden frame-instance key.
- Why it matters: scoring hidden controller occurrences can reject or adopt a
  different object from the semantic flamegraph presented to an analyst.

## Paper-Value Admission

- Planned role: retrospective construct-correction audit over fixed complete
  outputs, not a fresh algorithm discovery.
- Largest credible consequence: authorize the correct output identity for the
  task-semantic profile and quantify how much of Step 0054's loss came from
  hidden identity churn.
- Strongest reviewer objection addressed: equal visible semantic paths were
  prevented from folding only because the evaluator attached unique internal
  IDs, contrary to ordinary profiler aggregation.
- Independent evidence added: a fixed full-population standard score and
  paired uncertainty result for the profiler-visible object, independently
  recomputed from frozen predictions and score-only stages.
- Decision if favorable: visible path becomes the task-stack profile identity;
  adopt the fixed constructor only if it also clears the recurrence comparison.
- Decision if below recurrence: retain visible path as the correct profile
  identity, do not adopt the fixed online constructor, and allow at most the
  outer-audit-authorized exact-same-leaf causal invariant run.
- Why this is not redundant with the inspected diagnostic: the direction is
  already known, but the registered Step 0054 conclusion refers to a different
  construct. A reviewed and independently checked score is necessary to close
  that interpretation defect. No claim of preregistration will be made.

## Hypothesis And Fixed Outcome Disclosure

- One tested hypothesis: replacing hidden occurrence identity with canonical
  visible semantic-path identity materially improves ordinary B-cubed task-
  stage partition fidelity and evaluates the identity an actual profiler folds.
- The expected numeric direction has already been inspected and is disclosed:
  material improvement over hidden instance identity, but a remaining deficit
  versus recurrence.
- This experiment cannot establish that labels with the same text are globally
  equivalent across sessions or that the complete hierarchy is correct.

## Fixed Inputs And Candidate

- Fixed outputs from the completed Step 0054 run:
  `.agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/predictions.jsonl`.
- Fixed Step 0054 score rows and inference summary are reused without any model
  call or transition replay.
- Score-only gold: the same verified CodeTraceBench stage manifest, opened only
  by the scorer.
- Population: all 405 source-valid trajectories, 251 task clusters, 17,148
  native turns, 20,866 operations, and 2,948 session-local stage occurrences.
- Primary candidate identity: the complete ordered sequence of visible labels
  in `task_path`, namespaced by session for this occurrence-partition score.
  Every frame and its depth are retained, including adjacent identical labels.
  This is the exact identity an ordinary folded-stack/flamegraph representation
  exposes.
- Secondary mechanism diagnostic: idempotently contract only adjacent
  identical task labels, so `task -> install -> install` becomes
  `task -> install`. This is not standard flamegraph folding and is not part of
  the primary construct correction. It tests whether directly nested repeated
  labels expose a constructor pathology. No non-adjacent label, fuzzy match, or
  phase-like label is removed.

## Controls And Comparison

1. Step 0054 hidden active-frame instance identity isolates internal occurrence
   churn.
2. Adjacent-identical-label contraction is a secondary mechanism diagnostic,
   not the profiler identity or an adoption candidate.
3. Multi-resolution recurrence is the strongest current constructor on the
   same fixed population.

No fuzzy matching, case normalization, stemming, embedding, label clustering,
phase deletion, path pruning, depth cap, status/tool/system-field key, target
label, or score-selected parameter is permitted.

## Metrics And Decision

- Primary standard metric: ordinary operation-level B-cubed precision, recall,
  and F1 against session-local verified workflow stages.
- Primary construct-correction effect: exact visible path minus hidden frame-
  instance identity, using a paired 10,000-resample bootstrap over the same 251
  task clusters. A 95% interval above zero establishes material improvement in
  stage fidelity for the user-visible construct.
- Constructor adoption comparison: exact visible path minus recurrence, using
  a separate paired 10,000-resample bootstrap over the same task clusters.
- Standard secondary diagnostic: exact adjacent-boundary precision, recall,
  and F1. Exact-span F1 may be retained for comparability but is not an extra
  decision gate.
- Adoption condition for the online constructor: exact visible-path B-cubed F1
  exceeds recurrence and the constructor-comparison 95% interval is above
  zero. The already-inspected result is expected not to satisfy this condition.
- Per-framework results describe heterogeneity and do not add vetoes.

## Namespace And Claim Boundary

- Session is used only to namespace CodeTrace's session-specific stage
  occurrences during accuracy scoring. It is not a semantic stack frame.
- The scorer must also report the number of distinct global exact visible paths
  without session namespace as a profiling-fold behavior statistic, not as an
  accuracy score against session-unique stages. Adjacent-label contraction is
  reported separately and never called the actual flamegraph identity.
- This experiment does not validate cross-run semantic equality, ancestor
  topology, variable-depth correctness, task-label meaning, root
  canonicalization, or the lower phase/action/object/result suffix.
- It does not change the thesis, RQ3, its positive hypothesis, or the intended
  hierarchy.

## Execution

- Implement one thin score-only evaluator that reads fixed prediction and
  existing score rows, verifies exact key/coverage/order equality, constructs
  the two visible-path identities, and calls the existing standard B-cubed,
  boundary, span, and paired-bootstrap routines.
- Real preflight: five complete real trajectories, one per source layout, to
  validate joins, exact path construction, adjacent idempotence, and score
  output. Gold may be read only inside this scoring path because no inference
  occurs.
- Full run: all 405 trajectories and all 20,866 operations; no sampling.
- Output:
  `.agentsight/experiments/rq3-stateful-visible-path-identity-v1/`.
- Full completion requires exact coverage, fixed-control reproduction, primary
  metrics, uncertainty, framework diagnostics, global fold counts, and an
  independent raw recomputation.

## Interpretation

- Exact visible label path is the represented profiler construct; the first
  comparison quantifies its stage fidelity relative to the incorrect hidden-ID
  score. It does not make hidden IDs a visible path if the accuracy effect is
  small.
- Only a positive exact-visible-path comparison against recurrence would adopt
  this fixed online constructor within the stated flat-stage boundary. The
  expected below-recurrence result leaves it unadopted. The next causal
  experiment, if admitted, changes only exact same-leaf
  `push`/`replace` application to identity-preserving `stay` and reruns the full
  online sequence because future prompts change.
- If that final causal run also loses or retains phase/no-pop/depth pathology,
  the online Qwen2.5-3B branch closes without shrinking the research program.
