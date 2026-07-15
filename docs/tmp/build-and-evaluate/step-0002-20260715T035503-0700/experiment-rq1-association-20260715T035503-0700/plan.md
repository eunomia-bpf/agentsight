# Experiment Plan: RQ1 Evidence Recoverability and Association Accuracy

## Research Question

- RQ exactly as written in the paper: What does each evidence layer omit, and
  how accurately can agent events be associated with durable and surviving
  outcomes?
- Specific uncertainty tested here: Whether path/time/lifetime and, where
  available, edit-hunk evidence can recover calibrated candidate associations
  from native Claude, Codex, and Gemini histories to actual Git file changes,
  while correctly preserving null, ambiguous, and lineage-failure cases.
- Why the answer matters: Every joined event-to-outcome claim in RQ2/RQ3 and
  every line overlay depends on this association chain. If no stratum passes,
  the artifact must remain a descriptive process/Git/mismatch gallery.

## Paper-Value Admission

- Planned role: decisive.
- Largest credible paper story this experiment could unlock: Native cross-
  vendor session histories can support at least one uncertainty-bounded path-
  level observation layer over actual Git history, while line claims remain
  separately gated.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  Timestamp/path joins are too ambiguous to support durable-outcome or survival
  claims and merely create false provenance.
- Independent evidence added beyond existing runs and published results:
  No existing result measures this repository's native-event-to-actual-Git
  association and Git-to-current lineage with explicit null and ambiguity
  states across the three locally available vendor schemas.
- Why the result is not tautological, already settled, or dominated: The oracle
  is created independently in controlled histories and by blinded naturalistic
  annotation; it is not the proposed ranker's output. RECAP's instrumented
  shadow repository does not settle accuracy for weaker native logs and actual
  commits.
- Paper decision if positive: Permit only passing confidence/granularity strata
  in RQ2/RQ3 and linked views; report the rest descriptively.
- Paper decision if contradictory, mixed, or inconclusive: If no path stratum
  passes, remove event-to-outcome claims and keep mismatch/process/Git views. If
  path passes but line fails, ship path-level coordination without line overlay.
- Best alternative experiment and why this one has higher decision value: A
  gallery usability or scale experiment would be premature because attractive
  interaction cannot validate the joined evidence it visualizes.

## Expected And Alternative Outcomes

- Current expected answer: Exact normalized write paths within continuous file
  lifetimes will yield a supported path-level stratum; edit-hunk evidence will
  be sparse and line-level support may remain inconclusive.
- Strongest competing explanation: Multiple sessions, delayed/squashed commits,
  and incomplete payloads make even exact-path candidates poorly calibrated.
- Result that would contradict the expectation: No held-out path stratum meets
  the frozen support, precision, unmatched-classification, and calibration
  bounds.

## Published Precedent And Real Assets

- Closest published protocol: RECAP's parallel conversation/edit streams for
  recoverability framing, and CLSA's refactoring-sensitive matching for the
  separate Git-to-current-line stage.
- Official system/model/data/benchmark/tool and version: AgentSight Git history
  at the frozen experiment revision; native local Claude/Codex/Gemini records;
  `agent-session` 0.4.18; Git 2.54.0; Rust/Cargo 1.90.0.
- What is reused: Existing source-native parsers, actual Git plumbing, native
  timestamps and paths, official Git rename/diff/blame behavior, and current
  repository state.
- Necessary deviations or custom glue: A product exporter, rename-aware file-
  lifetime collector, candidate ranker, optional exact-edit/hunk comparison,
  privacy-safe artifact, and metric analysis. No experiment-only control schema
  or promotion API will be added.

## Comparison

- Proposed system or method: Preserve all path-resolvable events; evaluate only
  write-capable event--path pairs for durable-change correspondence. Retrieve
  zero/one/many compatible candidates in the frozen 24-hour retrieval window.
  Rank candidates lexicographically by (1) exact normalized edit/hunk match,
  (2) direct lifetime path over rename/pre-birth compatibility, (3) commit at
  or after the event over the 15-minute clock-skew allowance, (4) absolute
  committer-time distance, then (5) commit hash. Read/search events remain
  ordered process evidence, not edit-to-commit truth.
- Main baseline and competing position: Nearest same-literal-path Git change by
  absolute committer-time distance in the same retrieval window, forced to one
  candidate when any exists, with commit hash as the deterministic tie break.
  It represents the claim that sophisticated uncertainty/evidence handling adds
  nothing beyond current-practice temporal proximity.
- Why the main baseline needs a matched run instead of citation alone: Its
  error depends on this repository's commit cadence, session concurrency,
  squash behavior, and schema coverage; published datasets do not provide the
  matched native records.
- Controls or ablations, labeled separately: Proposed method without exact edit-
  hunk evidence; without rename/lifetime tracking; and source-coverage tables
  for Git only, events only, joined without endpoint, and full endpoint data.
- Confidence mapping: For each method, calibration data assigns the top
  candidate to preregistered evidence bins. Proposed bins are exact-hunk unique,
  unique direct-lifetime, unique rename/pre-birth, multi-candidate with a top
  distance ratio of at most 1:4, and other multi-candidate. Baseline bins are
  nearest distance at most 15 minutes, 1 hour, 6 hours, or 24 hours. Each bin's
  confidence is Laplace-smoothed empirical correctness `(correct + 1) / (n +
  2)`; an empty bin backs off to the method-wide calibration rate. A method
  predicts null when its calibrated top confidence is below 0.5.
- Conclusion if the main baseline matches or wins: Absolute support is method-
  independent. If only one method passes every gate, use it. If both pass, use
  the proposed method only when the paired 95% bootstrap interval shows lower
  Brier score or higher candidate-set recall without violating the precision
  gate; otherwise choose the simpler nearest-change method. If neither passes,
  keep associations descriptive.
- Information, tuning, and compute fairness: Both methods receive identical
  event paths/timestamps, Git history, frozen windows, target revision, and
  calibration split. Exact edit payload is a proposed-method mechanism and is
  separately ablated. Neither method sees held-out truth.
- Split or leakage rule: Scenario templates, dates, rank order, evidence bins,
  and thresholds are frozen before full results. Confidence values use
  controlled calibration cases only. Held-out scenario variants and
  naturalistic days are evaluated once. Naturalistic annotation receives every
  eligible Git change in the independent audit horizon, randomized and without
  method score, rank, or retrieval-window labels.

## Workloads And Metrics

- Real workloads or tasks: (1) an actual one-day AgentSight/native-session/Git
  preflight; (2) scripted Git histories with exact match, event-unmatched, Git-
  unmatched, ambiguity, squash, split, merge, rename, delete/recreate, moved or
  rewritten lines, pathless events, clock skew, and concurrent sessions for
  each supported native schema; and (3) stratified calendar days 2026-06-02,
  2026-06-23, and 2026-07-14 from the real AgentSight history, with July 14
  including locally available Gemini records.
- Primary metrics: Top-1 precision among non-null predictions, candidate-set
  recall over non-null oracle targets, positive-target recall, null-target
  specificity, candidate-set size/ambiguity, Brier score, and ten fixed equal-
  width-bin expected calibration error. Use per-class Wilson 95% intervals and
  a paired 10,000-resample bootstrap with seed 1729 for method differences;
  balanced accuracy is reported without a Wilson interval. Event-to-Git and
  Git-hunk-to-current-line metrics remain separate.
- Correctness check or ground truth: Fixture truth records observed write-to-
  commit IDs independently of either retrieval method. For events in each
  naturalistic calendar day `[D0,D1)`, the oracle packet contains every Git file
  change with a literal or rename-connected path in `[D0-24h,D1+7d]`, including
  merge-stratum changes and future same-path additions. Two annotators
  independently label a target set, null-within-seven-days, or unadjudicable.
  Primary metrics use reconciled labels; agreement and a disagreement-as-error
  sensitivity are reported before reconciliation. The 24-hour retrieval window
  never defines truth.
- Git semantics: Use committer timestamp, `git rev-list --first-parent --reverse
  <HEAD>` as the primary integration traversal, `git diff -M50%` against each
  first parent with copy detection disabled, and a separate merge-diff stratum.
  A lifetime starts at add and follows detected renames to deletion. A write in
  a pre-birth or post-deletion gap may associate only with the next same-path
  add in the audit horizon; it never inherits the ended lifetime. Same-path
  recreation receives a new lifetime ID.
- Repetitions, seeds, and uncertainty: Deterministic controlled cases use at
  least 50 positive and 50 null event--path pairs per evaluated path stratum
  across held-out variants. A line stratum requires at least 100 independently
  adjudicated links and still must meet its Wilson bound; insufficient payload
  is an inconclusive line result. Naturalistic sampling is fixed by day and
  stratified by schema/action/rename state.
- Absolute support gates: A path stratum requires a 95% Wilson lower bound of
  0.90 for non-null prediction precision, 0.85 for positive-target recall, and
  0.85 for null-target specificity, plus ECE at most 0.10. A line stratum
  requires a 0.95 Wilson lower bound for joint event-to-hunk and hunk-to-current-
  line precision. Sample support is necessary but never sufficient.
- Cost estimate when material: Local CPU only; under two hours compute and up
  to four hours independent annotation/reconciliation. No model/API spend.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | dependency | One real session day + actual Git | Proposed exporter/join | 1 valid attempt, at most 2 total | Establishes only that the authoritative path runs |
| controlled-main | proposed | All scripted scenario variants and schemas | Candidate-set ranker | 50 positive + 50 null minimum per path stratum | Tests known-link accuracy/calibration |
| controlled-baseline | baseline | Identical scripted histories | Nearest same-path change | Same pairs | Tests whether uncertainty/evidence adds value |
| controlled-ablation | ablation | Rename, payload, recreation, ambiguity subsets | Remove one mechanism | Same affected pairs | Explains mechanism engagement |
| naturalistic-main | proposed | Three frozen real calendar days | Frozen ranker | One blinded evaluation | Tests transfer to actual history |
| lineage | supporting control | Exact-edit/hunk subset through selected HEAD | Git lineage stage | At least 100 or inconclusive | Gates line overlays independently |

## Execution

- Authoritative command or workflow: `cargo run --manifest-path agent-session/Cargo.toml --bin agent-session-export -- --repo <repo> --since <RFC3339> --until <RFC3339> --output <artifact.json>` and `python3 vis-gallery/analysis/rq1_metrics.py --predictions <artifact.json> --truth <truth.json> --calibration <calibration.json> --output <metrics.json> --bootstrap-seed 1729`. Controlled repositories use ordinary non-interactive Git commands and source-native session fixtures.
- Real preflight case: Export 2026-07-14 from the actual AgentSight repository
  and native local records, then recompute a sampled event, candidate, file
  lifetime, and endpoint row directly from Git/session sources.
- Full completion rule: Every planned method/workload cell reaches terminal
  status; frozen truth and predictions are preserved; both event-to-Git and
  line-stage metrics are recomputable; failures/exclusions are retained; the
  naturalistic sample has two independent annotations and agreement reporting.
- Raw-result path: Private exports and annotation packets go under `docs/tmp/build-and-evaluate/step-0002-20260715T035503-0700/experiment-rq1-association-20260715T035503-0700/raw/private/`, which is ignored by the tracked experiment `.gitignore`; sanitized aggregate metrics go under `raw/public/`.
- Privacy default: The exporter emits no prompt, command, edit/read body,
  secret, or absolute home path unless an explicit non-experiment debugging
  flag is supplied. The RQ1 workflow never supplies that flag.
- Checkpoint or recovery approach: The exporter writes deterministic artifacts
  atomically; each ordinary run records command, revision, time range, and
  checksums. Resume by rerunning only incomplete cells with unchanged settings.

## Interpretation

- Positive result: At least one method's held-out path stratum crosses every
  frozen absolute gate. Select the method using the preregistered paired rule;
  only the passing stratum advances to joined views/RQ2/RQ3.
- Negative or contradictory result: No path stratum passes; the central joined-
  outcome mechanism is bounded to descriptive mismatch analysis and downstream
  tasks cannot claim event-to-outcome evidence.
- Mixed or inconclusive result: Report passing path/vendor/payload strata and
  failing/undersupported strata separately; line failure removes only line
  overlays, while inadequate naturalistic support blocks generalization.
- Target paper figure or table: One association-state confusion/calibration
  figure plus a table of source coverage, candidate ambiguity, path accuracy,
  and separate line-lineage accuracy by schema/confidence stratum.

## Reproducibility Notes

- Software and data versions: Branch `codex/vis-gallery`, experiment base
  `1d6497a4`; `agent-session` 0.4.18; Git 2.54.0; Rust/Cargo 1.90.0; selected
  repository HEAD and native file checksums recorded at execution.
- Config and seed notes: Frozen windows and thresholds come from the BOOTSTRAP
  contract. Deterministic fixture timestamps and any resampling seed are
  recorded in raw outputs.
- Known deviations: Native histories are private and cannot be committed;
  sanitized aggregate artifacts and fixture histories will be public. A missing
  vendor/date cell is reported rather than imputed.
