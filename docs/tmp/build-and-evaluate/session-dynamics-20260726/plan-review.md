# Fresh Plan Review: Session Dynamics and Harness Overhead

## Verdict

**Round 1 verdict: blocking repairs required before the plan is treated as
frozen.**

The proposed reanalysis is scientifically admissible and has clear supporting
value for the active study. It reuses the authoritative corpus, does not need a
new system baseline, and can produce decision-relevant positive, negative, or
mixed evidence. The current plan, however, does not yet define the population,
ordering, classifiers, denominators, or retry outcomes precisely enough for two
independent implementations to produce the same numbers. Several omissions
would change the substantive answer, especially for the corpus-wide call share,
late-session drift, startup predecessors, bookkeeping follow-up, and strict
failure cascades. These are executability/scientific-validity defects rather
than requests for optional polish.

No new data collection or additional baseline is required. Once the repairs
below are frozen in the plan/code, the full-corpus run is appropriate.

## Evidence checked

I read the experiment plan, the complete corpus and inclusion contract in
`docs/evaluation.md`, and enough exported events to verify the available
ordering, identity, path, status, edit, and Skill-attribution fields. The
following facts matter to the operational design:

- There are six logical exports, but each is present as both `.json` and
  `.json.gz`. The run must choose exactly one representation per project.
- The project headers sum to 551 project-root memberships:

  | Project | Claude | Codex | Gemini | Total |
  |---|---:|---:|---:|---:|
  | AgentSight | 123 | 176 | 2 | 301 |
  | ActPlane | 62 | 77 | 0 | 139 |
  | bpf-developer-tutorial | 31 | 3 | 1 | 35 |
  | eunomia.dev | 24 | 27 | 0 | 51 |
  | agentskill-observability-paper | 8 | 0 | 0 | 8 |
  | academic-writing-skills | 17 | 0 | 0 | 17 |
  | **Total** | **265** | **283** | **3** | **551** |

- Those 551 memberships contain only 550 globally unique `session_id` values.
  Root `claude:0ee9082c-0794-444d-8dba-022dcfb5f370` occurs in both
  AgentSight and ActPlane. Correspondingly, the exports contain 181,303 event
  rows but 180,764 unique event IDs; 539 event IDs are duplicated across those
  two project views.
- `session_id` identifies the joined native root within a project view.
  `session_ordinal` is a session rank repeated on all of that root's events and
  is not a call ordinal. Calls from a root and its subagents can occupy
  different `source_stream_id` values, each with its own
  `source_tool_ordinal`. `ts_ms` is available in the inspected exports and can
  flatten streams by observed wall-clock order, but that flattening does not
  establish a causal adjacency between concurrent streams.
- The exports retain `source_role` values such as `root`, `subagent`, and
  `user`. Subagent actions are deliberately joined to the root. Excluding them
  silently would no longer analyze the contracted complete root session.
- File evidence has two materially different layers. `actions` supplies
  worktree-normalized artifact paths, whereas `source_paths` also exposes
  paths outside the selected worktree. In the three small inspected exports,
  1,273 events had nonempty `actions`, while 1,473 had nonempty
  `source_paths`; 462 events had source paths but no actions. A bookkeeping
  classifier using only `actions` would therefore miss many external Skill and
  harness-file reads.
- The available statuses include `ok`, `fail`, and `observed`. The corpus
  contract forbids converting `observed` to either success or failure. Failed
  shell calls often have no `actions` or `source_paths`, so path-only retry
  matching would systematically drop them.
- Edit payload coverage is vendor/tool dependent. Codex `apply_patch` commands
  can expose patch lines and multi-file hunks, while inspected Claude `Edit`
  and `Write` rows expose target paths but not the edited text. There were no
  Gemini edit rows in the inspected Gemini-covered export. A cross-vendor
  line-count comparison is therefore not available from these exports.
- Direct fields such as `skill_name`, `skill_args`, and
  `attribution_skill` exist. A Skill invocation is observable, but downstream
  calls attributed to a Skill are not automatically bookkeeping overhead.

## Blocking defect 1: population, root grouping, and call ordering are not frozen

The plan says “native sessions” and “calling order” without specifying the
actual keys or resolving cross-project duplication. Grouping globally by
`session_id` would incorrectly merge the one dual-project root. Conversely,
calling all 181,303 rows independent calls would double-count 539 source
events in corpus-wide shares. Sorting a joined root by
`source_tool_ordinal` would also be invalid because that ordinal resets for
each source stream.

Concrete repair:

1. Define the primary project-stratified session unit as
   `(repository, session_id)`, yielding the contracted 551 project-root
   memberships. Never use `source_file`, `native_session_id`,
   `session_ordinal`, or `source_stream_id` alone as the session key.
2. Define project-stratified event analyses over the rows in that project
   view. For every corpus-wide “all calls” share, report both:
   (a) the 181,303 project-event-row estimand required by the existing
   project views and (b) a global unique-event sensitivity deduplicated by
   event `id` (180,764 unique events). Label the former as rows/memberships,
   not independent calls.
3. Read exactly the six `.json` files or exactly the six `.json.gz` files and
   assert one basename per project. Do not glob and ingest both encodings.
4. For progress phases, flatten all source roles inside a project-root by the
   deterministic key
   `(ts_ms, source_stream_id, source_tool_ordinal, id)`. Report the fraction
   of tied timestamps and use the final fields only as deterministic
   tie-breakers, not evidence of causality.
5. For a strict consecutive retry chain, use adjacency within
   `(repository, session_id, source_stream_id)` ordered by
   `source_tool_ordinal`. A flattened-root retry result may be reported only
   as a sensitivity because parallel subagent calls can interleave.
6. Retain all joined source roles in the primary root-session analysis.
   Provide root-only and no-subagent sensitivities if needed to show whether a
   drift effect is driven by delegation, but do not substitute them for the
   contracted population.

## Blocking defect 2: within-session drift metrics and the “long-session” population are underspecified

“Early/middle/late,” “repeated read,” “same-path near-term edit,” and “parsed
patch lines” currently admit several incompatible implementations. The plan
also predicts “context aging” without defining long sessions or separating a
call-progress association from elapsed-time/resumed-root effects.

Concrete repair:

1. Freeze phase assignment. A reproducible choice is, for the flattened call
   rank `i=0..L-1`, `phase=min(2, floor(3*i/L))`; require `L>=3` for the
   all-session tertile analysis. Report the actual calls in each phase.
2. Freeze the long-session primary gate before looking at effects. A reasonable
   gate is `L>=30` calls (at least ten calls per tertile), with `L>=60` and
   `L>=100` as sensitivity gates. Always report eligible session counts by
   project × vendor; do not silently drop short sessions.
3. Build progress curves from normalized rank `(i+0.5)/L` in ten fixed bins.
   Compute each session's bin metric first and then summarize sessions within
   a project × vendor stratum. Event-pooled curves are supplementary and must
   be labeled as such.
4. Define tool composition from the exported `category` field over all calls.
   Preserve `subagent`, `plan`, `tool`, and other categories rather than
   forcing every event into read/edit/shell.
5. Define the primary repeated-read metric at resolved artifact-access level:
   a non-failed `actions.access == "read"` of an `artifact_id` is a reread if
   that artifact had an earlier resolved read in the same project-root.
   Denominator: all eligible resolved read actions in that phase. Add a
   call-level “any reread target” version and report path-resolution coverage;
   do not treat unresolved shell reads as confirmed artifact rereads.
6. Report failure two ways without relabeling `observed`: recorded-fail share
   `fail / all calls` and resolved-status failure rate
   `fail / (ok + fail)`. The former is the conservative primary behavior
   share; the latter is the status-resolution sensitivity.
7. Do not use parsed patch lines as a cross-vendor edit-granularity primary
   metric. Use comparable path-level fragmentation proxies for all supported
   strata, such as files touched per edit call, edit calls per unique edited
   artifact, and same-artifact repeat edit within a fixed next-10-call window.
   Patch additions/deletions and hunk size may be a separate coverage-labeled
   Codex/tool sensitivity only. Missing Gemini edits are `N/A`, not zero.
8. Show distributions of per-session phase values and paired
   `(late - early)` differences (median, IQR, p90 and empirical plot), not
   merely ratios of pooled totals.
9. Report root duration and maximum internal inter-call gap. Repeat the
   long-session result after excluding clearly resumed/composite roots under a
   frozen gap threshold (for example, maximum internal gap over eight hours).
   Call-order drift can be described as consistent with a context-aging
   signature, but these traces cannot establish that latent context actually
   degraded.

## Blocking defect 3: startup “tax,” predecessor, and gap estimands are not sufficiently defined

The planned union of instruction reads, repository status commands, README
reads, and predecessor-file overlap is not self-interpreting. A root README
may be the task artifact, and rereading a prior-session file may be productive
continuation rather than tax. Short sessions and overlapping roots can also
distort both the prefix denominator and predecessor gap.

Concrete repair:

1. For each `N in {5,10,20}`, define the observed prefix as the first
   `min(N,L)` flattened calls and use that observed count as the denominator.
   Report a second distribution restricted to `L>=N`; otherwise short roots
   are not comparable to complete prefixes.
2. Use mutually auditable component tags and their union:
   - instruction read: exact basenames such as `AGENTS.md`, `CLAUDE.md`, and
     `GEMINI.md`;
   - repository-state query: parsed `git status` or `git log` subcommand
     (compound commands count once and are marked mixed);
   - repository-root README read, kept as its own component because it is often
     project work;
   - prior-access overlap: a resolved read whose worktree artifact/path
     appeared in the predecessor root;
   - prior-mutation overlap: the stricter subset whose predecessor access was
     create/write/delete.
   Report component shares and the non-additive union. Do not sum overlapping
   tags.
3. Call the instruction plus git component the **narrow startup-context
   proxy**, and the union including README and predecessor overlap the
   **extended proxy**. Neither establishes calls spent “instead of new work,”
   so the report must not present either as causal ground-truth tax.
4. Derive a session's worktree from its set of non-null event
   `worktree_id` values. Admit it to predecessor analysis only when that set
   has exactly one member; report zero-member and multi-member exclusions
   rather than filling them silently.
5. Define the predecessor as the session in the same
   `(repository, worktree_id)` with the greatest end time satisfying
   `predecessor_end < focal_start`, where start/end are min/max `ts_ms` over
   the joined root. Record predecessor vendor. Overlapping roots, the first
   observed root, and roots lacking a unique worktree have no strict
   predecessor. A same-vendor predecessor is a useful sensitivity, not a
   replacement for the primary repository-state predecessor.
6. State explicitly that the gap is the interval between eligible included
   roots, not necessarily true agent idle time: excluded/non-repository
   sessions and concurrent roots are outside the estimator.
7. Freeze gap bins before running (for example `<1h`, `1–24h`, `1–7d`,
   `>7d`), report every bin's session distribution and `n`, and compute
   Spearman association within adequately sized project × focal-vendor strata.
   A pooled correlation across projects/vendors would be composition
   confounding and cannot be primary.

## Blocking defect 4: bookkeeping files, call share, and read-after-write opportunity are not operationalized

The plan's “strict vs broad bookkeeping” statement does not contain an
enumerated classifier. This matters because `skills/` is the core product in
academic-writing-skills, Skill files can be project deliverables in other
repositories, status/report documents can be the requested research artifact,
and many external Skill reads appear only in `source_paths`. A high write/read
ratio also does not by itself show “write once and never return”; later-read
opportunity is censored near the corpus end.

Concrete repair:

1. Freeze an auditable path/tool classifier in the plan or a versioned config,
   and emit every matched path and rule to a raw table. At minimum keep these
   disjoint classes:
   - explicit control-plane tool calls (`Skill`/non-null `skill_name`,
     plan/TODO tools where observable);
   - agent instructions (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`);
   - memory/checkpoint files;
   - TODO/task/plan/status files;
   - Skill definitions and references;
   - experiment/process status reports;
   - ordinary project files;
   - ambiguous/mixed.
2. Define a narrow classifier from exact basenames/directories and a broader
   regex classifier. Generic tokens such as `task`, `status`, `plan`, or
   `memory` must not match arbitrary source-code names. Publish the top matched
   paths and a per-rule count so project-specific false positives are visible.
3. Report two different quantities:
   - **gross harness-shaped footprint**: any call targeting one of the frozen
     path/control classes;
   - **exclusive bookkeeping proxy**: a matched call with no ordinary
     in-worktree project target in the same call.
   Mixed calls remain a separate category. Neither quantity should be called a
   causal counterfactual overhead.
4. Use both path layers deliberately. Worktree `actions`/`artifact_id` are
   authoritative for project-file identity and later reuse; normalized
   `source_paths` are necessary for external Skill/harness reads. Report
   extraction coverage and never compare a source-path numerator with an
   action-only denominator without saying so.
5. Treat `attribution_skill != null` as provenance, not overhead. Cross-tab it
   with the path classifier to distinguish “a Skill caused a bookkeeping-file
   access” from “a Skill-guided call did ordinary project work.”
6. Count call share once per event even if it touches multiple paths. Separately
   report access-level and unique-file distributions. Define create/write as a
   write-side access. Keep failed attempts separate; use `status != fail`
   recorded accesses as primary and `status == ok` as a sensitivity so Codex
   `observed` writes are not silently converted to successes.
7. Compare bookkeeping and ordinary files at the same unit:
   per project × vendor distributions of reads per file, writes per file,
   write/read ratio (including explicitly defined zero-read handling), and
   call-level shares. Aggregate write/read totals alone are insufficient.
8. Define post-write revisit directly. For each eligible write, test for a
   strictly later read of the same artifact/path within the same root, within
   the next eligible root, and within fixed call horizons such as 10/50/100.
   Report time/call distance to first later read and right-censor writes with
   no adequate future observation. Use the same opportunity rule for ordinary
   project files. This is the measurement that can address “written but almost
   never looked at again.”
9. Because academic-writing-skills and some `.agents/skills` paths are
   themselves project deliverables, report a sensitivity that excludes
   in-repository Skill files in Skill-development task roots (or, minimally,
   reports them as “project Skill artifact” rather than overhead). The gross
   classifier may retain them, but it cannot support the overhead claim alone.

## Blocking defect 5: strict failure target, chain adjacency, outcomes, and cost are undefined

“Same target,” “continuous,” “reroute,” and “abandonment” cannot be recovered
unambiguously from the current prose. This is not a minor implementation
detail: many failed shell events have no resolved file path, and joined
subagent streams are concurrent. A semantic “same goal” label is not present
in the export.

Concrete repair:

1. Define a deterministic exact target key:
   - first choice: `(category, sorted artifact_id/access target set)` from
     nonempty `actions`;
   - second choice: `(category, sorted normalized source-path set)` from
     `source_paths`;
   - fallback: `(tool_name, command_name, whitespace-normalized exact command)`.
   Keep the key-source field so path-resolved and command-fallback chains can
   be reported separately.
2. A **strict failure cascade** is a maximal run of at least three immediately
   adjacent calls within one source stream, all with `status == fail` and the
   same exact target key. `ok`, `observed`, a different target, or the end of
   the stream terminates the run. Do not bridge over edits, reads, or calls in
   another subagent.
3. Build a separate coarse signature only for pattern discovery (for example,
   command family plus normalized target paths). It must not change the strict
   chain counts and should not use semantic/LLM goal labels.
4. Replace unobservable outcome names with mechanical outcomes:
   - exact-target recovered: a later exact-target call in the same stream has
     `status == ok`;
   - modified-route observed: no exact-target recovery occurs, but a later
     call in the same frozen coarse family uses a different exact target;
   - no observed return/recovery before stream/root end;
   - unresolved `observed` status, reported separately.
   “No observed return” is right-censored and must not be called abandonment
   as a fact. “Modified route” is a behavioral proxy, not proof of the same
   latent goal.
5. Freeze the search horizon. The full remaining source stream is the clearest
   primary horizon; add fixed next-10/50-call outcomes so long roots do not
   automatically have more recovery opportunity.
6. Report two costs: strict chain-member calls divided by all calls, and the
   distribution of chain lengths. If reporting an episode span through
   recovery, define its endpoint and resolve overlap before summing. Do not
   silently count all calls to session end as cascade cost.
7. Select anomaly cases deterministically after classification (for example,
   longest chains within each of the top coarse signatures, with no duplicate
   root) and retain repository, vendor, `session_id`, `source_stream_id`,
   call ordinal, event ID, status, target key, and command excerpt. Two or
   three real cases per major pattern are then source-verifiable rather than
   hand-picked anecdotes.

## Blocking defect 6: sparse strata and distribution outputs need explicit gates

The plan promises project × vendor distributions but does not specify how
empty and tiny cells are handled. Only three Gemini root memberships exist
across the entire corpus, and several project × vendor cells have one to three
roots. Reporting a smooth curve or directional claim for those cells would be
misleading.

Concrete repair:

- Materialize the full 6 × 3 grid for every section, with `n_sessions`,
  `n_calls`, metric-specific eligible units, and missingness. Empty cells and
  no-edit/no-predecessor cells are `N/A`, never zero.
- Always emit empirical per-session data and median/IQR/p90 for eligible cells.
  Show individual points for `n<10`; suppress smoothed curves, correlation
  claims, and directional generalization for such cells.
- Any cross-project/vendor synthesis must be a distribution of stratum or
  session effects with explicit weighting. It cannot treat 181,303 event rows
  as independent evidence.
- Every figure and table must state whether it uses all roots, long roots,
  predecessor-eligible roots, resolved-path accesses, edit-capable calls, or
  strict-chain-capable streams.

## Nonblocking improvements

- The cited precedent names in the plan are not bibliographically identified,
  and none defines these custom primary metrics. This does not block an
  exploratory descriptive reanalysis, but paper-facing use should cite the
  actual longitudinal precedents and describe these measures as
  study-defined, source-verifiable proxies rather than standard benchmark
  metrics.
- Saving package versions and deterministic raw tables is sufficient; a random
  seed is unnecessary unless resampling is later added. If bootstrap or
  permutation uncertainty is added, it must block by project-root/stream as
  appropriate and exclude the one cross-project duplicate from an independence
  claim.
- The proposed no-bootstrap choice for tiny strata is sound. Empirical points
  and eligibility counts are more honest than unstable confidence intervals.
- Four section-specific PNGs meet the minimum request, but the plan may produce
  more than one per section when one graphic cannot legibly show progress
  curves and project × vendor distributions. This is presentation, not a
  scientific blocker.

## Approval condition for a follow-up review

A follow-up can approve execution once the plan (or a referenced frozen
analysis specification) explicitly contains:

1. the 551-membership/550-unique-root and
   181,303-row/180,764-unique-event population policy;
2. root flattening and source-stream retry ordering;
3. exact phase, long-session, reread, failure, and comparable edit proxies;
4. prefix denominators, startup tags, predecessor eligibility, and gap bins;
5. an enumerated narrow/broad bookkeeping classifier plus censored
   read-after-write follow-up;
6. the exact strict target key, chain termination, outcome, horizon, and cost
   definitions; and
7. sparse-stratum/N/A reporting rules.

These repairs narrow ambiguity; they do not broaden the experiment or require
another dataset. With them, the analysis can validly provide project × vendor
distributions and source-linked cases while keeping “context aging,” “startup
tax,” “harness overhead,” “reroute,” and “abandonment” explicitly at the level
of observable behavioral proxies.

## Round 2 Follow-up Review

**Verdict: one residual blocker; the other five blocking categories are
closed.**

The repaired population/root ordering, drift metrics, startup
predecessor/prefix definitions, bookkeeping classifier and censored revisit
metrics, and sparse-cell rules are sufficiently frozen and executable. The
existing real preflight also exercises all four analysis paths and passes its
17-root/948-call invariants.

The sole remaining blocker is the failure-outcome metric in
`classify_chain_outcome()` (`analysis.py`, approximately lines 1587--1620).
The function searches future calls for an exact-key `ok` or `observed`, but
does not detect a later exact-key `fail`. Consequently, a target that is
retried and fails again after an intervening call can be labeled
`no_observed_return`, even though an exact-target return was observed. That
invalidates the requested recovery/reroute/no-return outcome distribution.

Concrete repair: before returning `no_observed_return`, detect later
exact-target failures and either (a) emit a distinct
`exact_target_failed_again` outcome, updating the frozen outcome list, or
(b) rename and define the terminal category as `no_observed_recovery` so it
explicitly includes later failed returns. The raw output must retain whether
an exact failed return occurred. No other plan or implementation change is
required for approval.

## Round 3 Final Follow-up Review

**Final verdict: PASS. No blocking defect remains.**

The frozen plan now includes `exact-target failed again` as a mechanical
outcome. `classify_chain_outcome()` detects a later exact-key `fail` before
falling through to modified-route or no-return, chain rows retain the full,
next-10, and next-50 failed-return indicators, and the plot recognizes the new
outcome. This closes the sole Round 2 blocker. Together with the previously
accepted repairs, all six original blocking categories are sufficiently
specified and executable for the full run.
