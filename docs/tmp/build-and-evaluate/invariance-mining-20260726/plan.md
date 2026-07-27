# Invariance-Mining Analysis Plan

## Research question and role

- Question: Which final-HEAD behavioral patterns recur across local
  project×vendor strata and, where measurement-compatible, in the independent
  RQ6 public traces?
- Specific uncertainty: whether apparently pooled findings reflect a stable
  structural relation, a vendor/tool-interface effect, a project effect, or
  an interaction/idiosyncratic case.
- Planned role: supporting external-validity audit across RQ1--RQ6.
- Largest credible result: a short list of relation-level general-claim
  candidates, never a population prevalence estimate or causal vendor claim.
- Contradictory/mixed result: retain the heterogeneity as a boundary and do not
  promote the pooled local number.

## Frozen inputs

The run reads, but does not modify:

- `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/`
- `docs/tmp/build-and-evaluate/toolcall-behavior-20260726/`
- `docs/tmp/build-and-evaluate/toolcall-profile-20260726/`
- `docs/tmp/build-and-evaluate/session-dynamics-20260726/`
- `docs/tmp/build-and-evaluate/user-questions-20260726/`
- `docs/tmp/build-and-evaluate/rq-extensions-final-20260726/`
- `docs/tmp/build-and-evaluate/rq2-crosscase-20260726/`
- `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq6-external-boundary/full/`

The last source contains the frozen 320-selection RQ6 sample: 64 IdeaTrail
topics and 64 task instances in each of four Open-SWE strata. The script
records SHA-256 digests of every direct aggregate input and verifies the 320
selected cached rows against `sample-manifest.csv`.

## Local grid and estimands

The reporting grid is the Cartesian product of six projects and three vendors
(18 cells), including explicit N/A cells. Eligibility is metric-specific:

| Metric | Estimand | Minimum eligible denominator |
|---|---|---:|
| `artifact_reuse_access_share` | stable-identity event×artifact touches whose identity was seen earlier in the worktree; the current touch supplies vendor attribution | 100 touches and 10 sessions |
| `top10_session_call_share` | call share carried by the largest ceil(10%) sessions | 10 sessions |
| `path_locality_share` | within-session adjacent path calls split into same exact path, same-module-only, and cross-module; primary value is the first two combined | 100 transitions and 10 sessions |
| `same_prompt_repeat_read_share` | repeated registered-identity reads in one source-stream prompt | 50 reads and 10 sessions |
| `shell_share` | shell-family calls / all calls | 100 calls and 10 sessions |
| `shell_shell_bigram_share` | shell→shell / all same-prompt family bigrams | 100 bigrams and 10 sessions |
| `zero_decisive_validation_session_share` | sessions with no recognized `test` call having `ok` or `fail` | 10 sessions |
| `startup_extended_excess_median` | median first-10 minus calls-11--20 contrast for the frozen extended orientation proxy | 10 complete 20-call prefixes |
| `late_reread_delta_median` | median paired late-minus-early resolved-artifact reread share | 10 long sessions |
| `dormant_revival_transition_share` | repeat stable-identity touches after >100 intervening worktree actions, attributed by the current touch | 100 repeat-touch transitions and 10 sessions |
| `decisive_failure_rate` | fail / (`ok` + `fail`), excluding `observed`; decisive coverage is reported beside it | 100 decisive calls and 10 sessions |
| `bigram_entropy_bits` | Miller--Madow-corrected Shannon entropy over the fixed global tool-family-pair alphabet | 100 bigrams and 10 sessions |
| `shell_burst_p90` | p90 length of same-prompt consecutive shell runs | 50 shell runs and 10 sessions |
| `module_return_call_share` | path calls returning to any previously left module after at least one intervening path call; a multi-module call counts at most once | 100 path calls and 10 sessions |
| `session_top_path_share_median` | median per-session top exact-path access share | 10 path-bearing sessions |

Every “10 sessions” rule means 10 denominator-contributing sessions, not 10
arbitrary sessions in the project×vendor cell: artifact/path metrics require
artifact/path-bearing sessions; repeated reads require registered-identity-read
sessions; bigrams require same-prompt transitions; shell bursts require
shell-run sessions; decisive failure requires sessions with decisive statuses;
and the startup/late metrics require complete prefixes/paired windows. Each
metric row reports both its event denominator and contributing-session count.

`zero_decisive_validation_session_share` is an observability/cadence measure,
not “validation quality”; recognized-test and decisive-status coverage are
reported beside it. `startup_extended_excess_median` is a matched prefix/later
orientation-density contrast, not elapsed-time cost or causal tax. Multi-path
Tool calls are collapsed to one call for path transitions and module returns.
Stable-identity touches remain one event×artifact instance. The public-compatible
path metrics use exact normalized paths and do not masquerade as lineage
identity. Project names are canonicalized by the frozen map
`eunomia-dev→eunomia.dev`, `AgentSight→agentsight`; session joins use exact
`(project, session_id)`, and lifecycle joins use exact
`(project, worktree_id, event_index, event_id, artifact_id)`.

## Stability and classification rules

For each metric:

1. Report the raw cross-cell coefficient of variation
   `sample SD / |mean|` over eligible observed cells. If the eligible mean is
   zero, CV is infinite. A bootstrap over eligible case cells is reported only
   as a case-composition sensitivity; it is not substituted for within-cell
   uncertainty. Because a uniform session-level sufficient-statistic schema is
   unavailable for all 15 reused estimands, vendor/project labels remain
   explicitly limited rather than receiving a spurious sampling-stability
   upgrade.
2. Direction is evaluated only for a frozen, falsifiable contrast:
   - path locality minus cross-module share;
   - observed shell→shell share minus the prompt-local independence expectation
     from shell origin/destination marginals;
   - first-10 minus calls-11--20 extended orientation share;
   - late-minus-early reread share.
   Top-10% concentration and top-path share are reported only as unsigned
   magnitudes: subtracting their finite-support uniform minima would be
   tautologically nonnegative and therefore is not a direction test.
   Nonnegative prevalence, entropy, raw failure, raw shell share, raw reuse,
   revival, and burst measures have direction `N/A`; they may show magnitude
   stability but cannot satisfy an invariant direction gate by construction.
3. On the complete paired Claude/Codex subgrid (AgentSight, ActPlane,
   eunomia.dev), report:
   - Spearman project-rank correlation between vendors;
   - consistency of the Codex-minus-Claude sign;
   - two-way additive project, vendor, and interaction shares of transformed
     sum of squares. Bounded shares use a clipped logit, positive unbounded
     measures use log, and signed deltas remain untransformed.
   The 3×2 decomposition is descriptive only. Claude/Codex-shaped and
   project-shaped labels report leave-one-project-out sensitivity where
   defined, but remain `evidence_sufficiency=limited` because three paired
   projects cannot support a decisive session-cluster attribution. Even a stable result means
   “Claude--Codex shaped in the three paired projects,” never vendor causality
   or a Gemini claim.
4. Classify with this precedence:
   - `invariant-candidate`: at least six eligible local cells spanning at least
     four projects, both Claude and Codex, and two complete vendor pairs;
     CV < 0.30; a valid contrast with direction consistency >= 0.80; leave-one-cell-out
     stability >= 0.80; and, for an RQ6-compatible metric, actual public
     replication rather than absence of contradiction;
   - `vendor-shaped`: not invariant, all six paired cells eligible, vendor
     sum-of-squares share >= 0.50, vendor-direction consistency = 1.0, and the
     same label survives at least two of three leave-one-project-out fits;
   - `project-shaped`: not above, all six paired cells eligible, project
     sum-of-squares share >= 0.50, project-rank Spearman rho >= 0.50, and the
     same label survives at least two of three leave-one-project-out fits;
   - `idiosyncratic`: remaining coverage-sufficient heterogeneous or
     interaction-dominated cases.

Every row also carries `evidence_sufficiency=sufficient|limited`.
Under-covered metrics retain a provisional one-of-four label to satisfy the
requested table schema, but `classification_status=limited` prevents that
label from being used as evidence that a pattern is personal or general.
These labels are descriptive evidence classes, not causal attribution.
Gemini has only three sessions and 44 calls across the corpus and is retained
in the 18-cell table but will normally fail eligibility.

## Distribution comparison

Three positive count distributions are fitted separately in every eligible
local cell and public RQ6 stratum:

- Tool calls per native session / public task trajectory;
- exact-path access counts per `(native session, exact path)` / public
  `(trajectory, exact path)`;
- consecutive same-prompt shell-run lengths / public trajectory.

For each cell, choose an integer tail cutoff `xmin` by minimizing the discrete
power-law KS distance subject to at least 50 tail observations from at least
10 distinct native-session/public-trajectory clusters. Fit a
normalized discrete power law and lower-truncated discretized lognormal on
that identical integer tail. The main likelihood-ratio uncertainty resamples
native session / public trajectory clusters, so path counts and shell runs
nested in one unit are never treated as independent. BH-adjusted exploratory
q-values across the selected-`xmin` fit family select a relative family only
when the cluster-bootstrap LR interval also excludes zero; otherwise the
families are indistinguishable. The signed statistic is
`sum(log p_powerlaw - log p_lognormal)`, so positive favors power law. A frozen
common-`xmin=1` sensitivity removes the power-law-selected-cutoff advantage.
All cluster bootstraps use 2,000 resamples and seed `20260726` plus a
deterministic stratum offset.
The output reports tail size, selected and common cutoffs, Pareto alpha,
lognormal mu/sigma, LR, cluster interval/p/q, and KS diagnostics. No visual
straight-line judgment is used, and relative family preference is not an
absolute goodness-of-fit claim.

“Shape-stable, parameter-drifting” requires the same decisive family in at
least 70% of all eligible fits (not merely decisive fits), coverage across at
least three local projects, and common-support parameter drift: Pareto alpha
CV or lognormal sigma CV >= 0.30, with lognormal mu SD and `xmin` drift also
reported. Indistinguishable fits count in the denominator and do not vote.
The 64-unit public strata can distinguish only broad full-support shapes; they
are not described as high-resolution tail estimates.

## External replication

The RQ6 sample is re-read from the cached, hash-checked public rows. Eight
compatible/analogous metrics are recomputed separately in five strata:

- within-attempt path locality;
- module-return call share;
- repeated exact-path explore/read share;
- any exact-path reuse share;
- shell tool share;
- top-10% trajectory-call share;
- median top-target share;
- median late-minus-early exact-path reread share.

The metric-level mapping is frozen as follows:

| Public metric | Local counterpart | Compatibility and role |
|---|---|---|
| `top10_unit_call_share` | `top10_session_call_share` | same raw concentration magnitude; descriptive only because there is no non-tautological direction anchor |
| `path_locality_excess` | `path_locality_share` contrast | exact within-unit path projection and the only path metric eligible to satisfy the external invariant gate |
| `module_return_call_share` | `module_return_call_share` | compatible recurrence form; `replicated_presence` only because zero is a tautological prevalence anchor |
| `path_reuse_share` | no identity-compatible core metric | exact-path analogue only; does not gate a local invariant |
| `repeat_path_read_share` | `same_prompt_repeat_read_share` | exact-path/public-tool analogue to registered-identity local reads; does not gate a local invariant |
| `shell_share` | `shell_share` | same broad tool family, but IdeaTrail lacks a shell interface; `harness-shaped` modifier and no invariant gate |
| `unit_top_path_share_median` | `session_top_path_share_median` | same raw concentration magnitude; descriptive only |
| `late_path_reread_delta_median` | `late_reread_delta_median` | direction analogue (exact path versus stable identity); may gate only if every local coverage/stability rule also passes |

Local comparison values use the corresponding within-native-session exact-path
projection. The 320 cached raw rows are re-read and hash-checked; aggregate
tables are not used to infer missing shell/repeat/return-call fields. Public
replication treats IdeaTrail and Open-SWE as two corpus families, not five
independent populations: the bootstrap CI must lie on the same contrast side
in IdeaTrail and in at least three of four Open-SWE harness/model strata.
IdeaTrail's enforced workflow and lack of shell interface are explicit
harness boundaries; shell share therefore receives `harness-shaped` as an
external modifier, not a fifth classification class or a behavioral
contradiction. `replicated_presence` and `descriptive_magnitude` likewise do
not satisfy the invariant gate. Magnitude differences remain visible and do
not invalidate recurrence of form. Public exact-path rereads are analogous to,
not exact replications of, local stable-identity rereads. Stable artifact
lineage, dormancy/revival, cross-session continuity, and prompt-scoped identity
rereads remain N/A when RQ6 lacks the required source semantics.

## Execution and completion

- Preflight: `python3 -B analysis.py --preflight --output-dir preflight`,
  against two local projects and the first two rows
  of each public stratum, checking schema, hash, grid, and metric invariants.
- Full command: `python3 -B analysis.py --full`
- Completion: 18×15 local metric rows; 320 public rows reconciled; all
  compatible external strata present; fit and summary tables produced; every
  figure regenerated from CSV; report numbers mechanically reconciled.
- Outputs: CSV tables, PNG figures, `input-manifest.csv`, `report.md`, and a
  read-only result review in this directory.

## Scope guards

- No modification under `docs/paper/`.
- No git write operation.
- No access to or write under `rq7-heldout-20260726/`.
- The script uses an explicit input allow-list and aborts if any resolved input
  path contains `rq7-heldout-20260726`.
- No causal vendor/model interpretation, productivity label, or population
  prevalence claim.
