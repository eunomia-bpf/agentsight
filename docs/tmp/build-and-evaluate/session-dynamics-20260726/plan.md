# Experiment Plan: Session Dynamics and Harness Overhead

## Research Question

- RQ exactly as written in the current study contract: how do rework and continuity evolve across session boundaries, and what source-verifiable behavioral facts become measurable from ordered native tool actions?
- Specific uncertainty tested here: whether behavior changes systematically from early to late session; how much of the first calls reconstruct context; how much observable file activity targets harness bookkeeping artifacts; and how often repeated failures form costly retry cascades.
- Why the answer matters: these measurements can distinguish productive long-horizon work from context re-grounding, harness-maintenance, and retry overhead without converting them into an opaque progress score.

## Paper-Value Admission

- Planned role: supporting.
- Largest credible paper story this experiment could unlock: long sessions and repeated native roots expose measurable, project-dependent overhead and late-session behavioral drift that aggregate action counts conceal.
- Strongest reviewer reject argument or load-bearing uncertainty addressed: the apparent patterns may be vendor/tool-interface artifacts, project composition, or a few extremely long sessions rather than within-session dynamics.
- Independent evidence added beyond existing runs and published results: within-session progress curves, startup-call attribution, bookkeeping read/write follow-up, and retry-chain outcomes are not reported by the existing RQ1--RQ4 recompute.
- Why the result is not tautological, already settled, or dominated: every pattern is tested within native sessions and reported by project × vendor with session-level distributions; no claim follows merely from longer sessions containing more calls.
- Paper decision if positive: prioritize robust within-case effects and bounded overhead estimates for the empirical paper, with causal language excluded.
- Paper decision if contradictory, mixed, or inconclusive: report project/vendor boundaries and treat “context aging” or “harness tax” as unsupported outside the observed strata.
- Best alternative experiment and why this one has higher decision value: another aggregate artifact-lifecycle summary would duplicate RQ1--RQ4; reanalysis of the existing 181,303 calls directly addresses the user's open behavioral questions at no new collection cost.

## Expected And Alternative Outcomes

- Current expected answer: rereads and near-term same-target edits rise late in at least some long-session strata; startup reconstruction is right-skewed and gap-dependent; bookkeeping is a small call share but has a higher write/read ratio than ordinary files; failure cascades are rare overall but locally expensive.
- Strongest competing explanation: any aggregate effect is created by project/vendor mix, extremely long composite roots, status semantics (`observed` vs `fail`), or imperfect path/target extraction.
- Result that would contradict the expectation: phase distributions are stable within project × vendor; startup tax does not increase across gap bins; bookkeeping is revisited at least as often as ordinary files; or strict retry chains consume negligible calls without recurring patterns.

## Published Precedent And Real Assets

- Closest published protocol: boundary-aligned longitudinal analysis from AgingBench / Plans Don't Persist, with action-procedure precedent from ProcGrep; this run remains a source-native descriptive reanalysis.
- Official system/model/data/benchmark/tool and version: six final-HEAD event exports under `rq1-rq4-recompute-final/rq1-raw/events/`, repository revision recorded in each JSON header.
- What is reused: the admitted 551 native root sessions and 181,303 tool calls, their timestamps, statuses, vendors, source roles, worktrees, paths, effects, and commands.
- Necessary deviations or custom glue: deterministic Python classification and plotting only; ambiguous intent is never labeled as ground truth.

## Comparison

- Proposed system or method: session-blocked descriptive statistics and progress curves over the source-linked event export.
- Main baselines and the competing position each represents: no intervention or system baseline is applicable; the relevant contrast is early vs middle vs late within the same session and bookkeeping vs ordinary project-file accesses.
- Why each main baseline needs a matched run instead of citation alone: N/A; this is observational corpus analysis.
- Controls or ablations, labeled separately: session-length threshold sensitivity; startup prefixes N=5/10/20; strict vs broad bookkeeping definition; strict all-call failure rate vs resolved-status failure rate; exact-target retry chains vs coarse-pattern summaries.
- Conclusion if each main baseline matches or wins: phase stability or ordinary-file parity narrows/contradicts the proposed overhead interpretation.
- Information, tuning, and compute fairness: all strata use one frozen classifier and identical metrics; pooled event-weighted numbers are labeled and never substitute for session-level distributions.
- Split or leakage rule when relevant: a startup predecessor must be the latest completed session in the same project/worktree before the focal session starts; overlapping/future sessions are not used.

## Workloads And Metrics

- Real workloads or tasks: AgentSight, ActPlane, bpf-developer-tutorial, eunomia.dev, agentskill-observability-paper, and academic-writing-skills, separately by Claude, Codex, and Gemini where observed.
- Primary metrics: category mix; repeated-read share; recorded-fail share; same-path near-term edit share; parsed patch lines; startup reconstruction-call share; session-gap bins and Spearman association; bookkeeping-call lower bound; write/read and post-write revisit rates; retry-chain length, call share, and outcome.
- Correctness check or ground truth: invariant counts must reproduce 551 sessions and 181,303 calls; all case excerpts retain session ID, ordinal, command, and source event ID for lookup; derived tables are regenerated from one script.
- Repetitions, seeds, and uncertainty: deterministic full-corpus run; session-level median, IQR, p90 and empirical distributions; bootstrap is not used where tiny strata make exchangeability implausible.
- Cost estimate when material: local scan of approximately 300 MB uncompressed JSON plus plots.

## Frozen Operational Definitions (after independent plan review)

- Population: the primary stratum unit is `(repository, session_id)`, preserving all joined `root`, `subagent`, and `user` source roles. This is 551 project-root memberships, not 551 globally distinct IDs. Corpus-wide shares are reported both over 181,303 project-event rows and after deduplication by event `id` (180,764 unique events); project × vendor analyses retain project membership.
- Ordering: a root is flattened by `(ts_ms, source_stream_id, source_tool_ordinal, id)`, with tied timestamps reported as a limitation. Strict retry adjacency is never taken from this flattening: it is defined within `(repository, session_id, source_stream_id)` ordered by `(source_tool_ordinal, ts_ms, id)`.
- Drift: all roots with at least three calls receive exact rank phases `min(2, floor(3*i/L))`. The long-session primary population is `L>=30`, with `L>=60` and `L>=100` sensitivities; deciles use normalized rank `(i+0.5)/L`. Repeated reads use non-failed worktree `actions` and `artifact_id`; edit fragmentation uses resolved paths/artifacts, paths per edit call, edits per unique artifact, and same-artifact re-edit within the prior ten flattened calls. Patch-line size is a coverage-labeled Codex/apply-patch sensitivity only. Roots with maximum internal gap above eight hours are excluded in a resumed/composite-root sensitivity.
- Startup: each `N in {5,10,20}` uses the first `min(N,L)` calls and records whether the prefix is complete. The narrow proxy is the union of exact `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` reads and parsed `git status`/`git log`; the extended proxy adds repository-root README reads and resolved reads of artifacts accessed by the strict predecessor. Prior mutation overlap is a separate stricter tag. A predecessor is the greatest-ended non-overlapping root in the same repository and unique worktree. Gap is between included roots, not true agent idle time, and uses frozen bins `<1h`, `1–6h`, `6–24h`, `1–3d`, `3–7d`, and `≥7d`.
- Bookkeeping: the narrow, disjoint path classes are instruction, memory, task/plan/status, Skill definition/reference, and experiment/process status; a broad regex sensitivity is separate. Both worktree `actions` and external `source_paths` are retained with a `layer` field. Gross footprint is any matching file or explicit plan/Skill tool call; exclusive bookkeeping has no ordinary in-worktree target in the same call; mixed calls remain separate. `attribution_skill` is provenance, never overhead by itself. File ratios use `status != fail` accesses; every matched path/rule is exported. Project-local Skill artifacts in `academic-writing-skills` are removed in an adjusted sensitivity.
- Revisit: each write is checked for a strictly later same-root read at fixed 10/50/100-call horizons only when that horizon is observable, for any later same-root read and distance, and for a read in the next strict same-worktree root when one exists. No-read writes without adequate opportunity are censored rather than labeled unused.
- Failure cascades: the exact target key prefers `(category, sorted artifact_id/access set)` from actions, then normalized source paths, then `(tool_name, command_name, whitespace-normalized exact command)`. A strict cascade is a maximal same-key run of at least three adjacent `fail` calls in one source stream; `ok`, `observed`, another key, or stream end terminates it. Full-stream and next-10/50 mechanical outcomes are `exact-target recovered`, `exact-target observed unresolved`, `exact-target failed again`, `modified route observed`, or `no observed return`; the last is censored and is not called abandonment. Raw chain rows retain failed-return flags. Coarse families are used only to group examples.
- Sparse cells: every output carries eligible `n`. The full 6 × 3 grid is materialized; empty cells are N/A, and cells below ten sessions receive points/descriptive rows but no correlation or generalized trend claim.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| schema preflight | dependency | one small project | full classifier and plot path | 1 | verifies execution only |
| main | observational | all six projects | frozen primary definitions | full corpus | supports or bounds each requested finding |
| sensitivity | control | all eligible strata | thresholds/definitions above | deterministic | tests robustness to operational choices |

## Execution

- Authoritative command or workflow: `python analysis.py` from the experiment directory.
- Real preflight case: `academic-writing-skills.json`, using the same parser and metric functions as the full run.
- Full completion rule: all six files load once; invariant counts pass; every requested section has raw tables, at least one PNG, interpretation, and source-linked anomaly cases.
- Raw-result path: `raw/`; figures: `figures/`; final synthesis: `report.md`.
- Checkpoint or recovery approach: deterministic CSV/JSON outputs are overwritten only inside this experiment directory.

## Interpretation

- Positive result: a directional effect recurs in multiple adequately sized project × vendor strata and is visible in session-level distributions, not only event-pooled averages.
- Negative or contradictory result: distributions are stable/reverse, or the effect disappears under length/definition sensitivity.
- Mixed or inconclusive result: effects occur only in one project/vendor, tiny strata, or depend on a classifier boundary.
- Target paper figure or table: four section-specific figures plus compact project × vendor quantile tables.

## Reproducibility Notes

- Software and data versions: repository and per-export revisions recorded at run time; Python, NumPy, pandas, SciPy, and Matplotlib versions saved in `manifest.json`.
- Config and seed notes: deterministic analysis; fixed thresholds are recorded in code and report.
- Known deviations: “context reconstruction,” “bookkeeping,” “reroute,” and “abandonment” are transparent behavioral proxies, not intent or causal labels; Claude `Edit` exports do not contain patch text, so patch-line granularity is a coverage-limited sensitivity.
