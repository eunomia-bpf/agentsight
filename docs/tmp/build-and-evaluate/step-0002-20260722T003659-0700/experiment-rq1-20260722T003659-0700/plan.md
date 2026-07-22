# RQ1 Experiment Plan — Activity to Observable Artifact Progress

**Created:** 2026-07-22T00:36:59-07:00  
**State:** preregistration draft; no RQ1 result has been computed  
**Selected experiment:** one complete real run over six fixed local projects

## 1. Question and claim boundary

RQ1 asks:

> How much long-running Agent activity becomes artifact change that persists,
> is later reused, and is followed by successful validation?

This experiment is descriptive and multi-case. It does not claim that a
surviving path preserves the bytes of a particular write, that a later test
covers a particular mutation, that reuse implies usefulness, or that the six
author-associated projects estimate a population rate. It does not interpret
rework, session-reset cost, attention migration, harness effects, or tool
superiority; those belong to RQ2--RQ7.

## 2. Fixed cases and source admission

The cases and repository roots are fixed before extraction:

| Case | Repository root |
|---|---|
| AgentSight | `/home/yunwei37/workspace/agentsight` |
| ActPlane | `/home/yunwei37/workspace/ActPlane` |
| bpf-developer-tutorial | `/home/yunwei37/workspace/bpf-developer-tutorial` |
| eunomia.dev | `/home/yunwei37/workspace/eunomia.dev` |
| agentskill-observability-paper | `/home/yunwei37/workspace/agentskill-observability-paper` |
| academic-writing-skills | `/home/yunwei37/workspace/my-paper-work/academic-writing-skills` |

The primary corpus admits complete native Claude, Codex, and Gemini sessions
whose native project directory, cwd/worktree, or Git remote matches a case.
All timed Tool actions in an admitted session stay on the action timeline,
including no-path actions and failures. Global path-only matches are not mixed
into primary denominators; an optional `--global` run is a separately labeled
coverage sensitivity analysis.

## 3. Minimal implementation

Reuse `agent-session` and `agentvis::build_repository_trace` directly.

1. Retain `ToolEvent.effect` as `RepositoryEvent.effect`; retain a hashed
   worktree ID on each existing `FileAction`, and resolve relative paths from
   the Tool call's `workdir` before falling back to session cwd.
2. Add candidate/parsed/included session coverage counters to the existing
   `RepositoryTrace`; this is source qualification, not another event model.
3. Add one research-only `research-rq1` entrypoint that accepts an output
   directory followed by repository roots.
4. Write plain JSON/CSV/Markdown using existing Rust/serde dependencies.
5. Add one Python/matplotlib script that reads only the frozen CSV files and
   produces vector PDF plus PNG previews for F3 and F4.

No SQLite, web application, canonical evidence artifact, semantic labels,
human gold, new event abstraction, or new runtime dependency is admitted.

## 4. Units and deterministic derivations

### 4.1 Action and effect units

- **Action:** one timed native Tool call in an admitted session.
- **File effect:** one non-scope repository-relative file action emitted by an
  adapter. All statuses remain in coverage. Only `status == ok` contributes to
  confirmed-success mutation endpoints; `observed` is unknown rather than
  success or failure.
- **Mutation:** create, write, rename, or delete. Read is an access, not a
  mutation. Directory-scope arguments are retained as scope coverage and
  excluded from artifact reuse/mutation numerators.
- **Recognized successful validation:** the current adapter-derived
  `effect == test && status == ok`. The frozen recognizer covers test/check/
  build/clippy words for its enumerated cargo, pytest, npm, pnpm, yarn, go, and
  make command families. Failed, status-unknown, and unrecognized experiment or
  validation commands stay on the timeline but do not satisfy this endpoint;
  they are coverage unknown, never evidence of no validation.

### 4.2 Artifact identity

Events are processed in `(ts_ms, source ID)` order. An artifact key is
`(worktree_id, relative_path)`. The worktree ID is a stable short hash of the
canonical worktree root; absolute roots are not needed in shareable media. A
first observed path starts an identity. It is marked `observed_birth` only when
the first confirmed-success effect is create; otherwise it is
`left_censored_existing` because its true creation predates observation. An
explicit rename transfers identity only inside the same worktree. Delete closes
it; a later create/write at that key starts a new identity.

An occupied rename destination closes the old destination identity before the
source identity moves. An unseen or unresolvable source produces a new
destination identity with `rename_lineage=unknown`; it never guesses a source.
No same-path link crosses worktrees, and no similarity, content, intent, merge,
or Git rename is inferred. Final existence and tracked state are queried from
the corresponding worktree. If that worktree no longer exists or cannot be
queried, final state is `unknown`; the artifact is excluded from persistence
rather than treated as absent.

### 4.3 Outcome dimensions

For every confirmed-success non-delete mutation episode, report:

- next later non-scope access to the same artifact identity, with event-step,
  wall-clock, and same/cross-session distance;
- next later read and next later mutation separately;
- next later recognized successful validation before the same artifact's next
  mutation/delete, with event-step and wall-clock distance;
- the same artifact's next mutation/delete as a competing outcome;
- arbitrary later recognized successful validation as a separately named
  secondary global association, never mutation validation;
- right-censoring only at the last admitted action when no endpoint or
  competing outcome occurs; and
- final existence and Git tracked state of the identity's final path.

For every artifact, report worktree ID, observation-birth state, first/last
path, first/last event, read and mutation counts, explicit rename/delete state,
later-session reuse, final existence, and final tracked state. Only an identity
whose birth event is a confirmed-success create on an unoccupied key is
eligible for **introduced-artifact persistence**. Rename always inherits the
source identity's birth state, even when the destination is unoccupied. An
unseen/unresolvable rename source has unknown birth and lineage and is excluded
from persistence and the three-way conjunction. Optional introduced-path
persistence is separate and cannot enter the artifact metric. Existing-file
writes report `final_path_exists` and `content_durability=unknown`; they never
enter persistence or the three-way conjunction. A deletion is reported
separately as a lifecycle outcome; absence after delete is not mislabeled as
failed progress.

The three primary RQ1 dimensions remain separate:

1. introduced-artifact persistence among observation-born introductions;
2. competing-risk cumulative incidence of later reuse after a confirmed
   non-delete mutation (delete before reuse is competing); and
3. competing-risk cumulative incidence of recognized successful validation
   before the same artifact's next mutation/delete.

Their conjunction is reported only for eligible observation-born introduction
episodes: final artifact exists, later reuse is observed, and recognized
successful validation precedes supersession. There is no weighted score and no
fixed 24-step, 30-second, or commit-aligned window.

## 5. Frozen outputs

The command writes to the experiment directory:

```text
raw/
  projects.json
  events/<project>.json
  rq1-artifacts.csv
  rq1-mutations.csv
  rq1-summary.csv
figures/
  rq1-progress-curves.pdf
  rq1-progress-curves.png
  rq1-activity-progress.pdf
  rq1-activity-progress.png
result.md
commands.log
```

Every mutation row retains project, event/source-call/session IDs, native time,
artifact ID, path, operation, endpoint IDs/distances/censoring, and final-state
fields. Project summaries are recomputable from the row tables.

## 6. Figures

**F3 — RQ1 progress dimensions.** A three-panel project-faceted figure:

1. introduced-artifact persistence proportion with its exact eligible
   denominator (deletes shown separately);
2. Aalen--Johansen cumulative incidence of later reuse over event-step distance,
   with delete as the competing outcome; and
3. Aalen--Johansen cumulative incidence of recognized successful validation
   before supersession, with later mutation/delete as competing outcomes.

The estimator is implemented directly from the mutation rows; only
end-of-observation rows are right-censored. Curves show complete horizons,
eligible denominator, and risk-count ticks without a chosen success window.
Projects with no eligible rows are marked unavailable.

**F4 — Activity versus progress.** Three aligned scatter panels use Tool
actions whose Tool-level workdir/session cwd resolves to a retained worktree on
the x-axis and, respectively, introduced-artifact persistence,
observed later-reuse proportion, and recognized validation-before-supersession
proportion on the y-axis. Every summary row exposes the exact numerator and
denominator, observation span, session count, and source coverage from which a
point is recomputed. Each point is one project and is labeled. All admitted but
unattributed Tool actions are reported as source coverage rather than silently
added to the x-axis. Spearman rank correlation is descriptive only; with six
cases, no population p-value or causal inference is reported.

## 7. Qualification, preflight, and stop conditions

Before the full run, the exporter must pass unit tests for Tool-level workdir,
worktree separation, rename into an occupied destination, unseen or unresolved
rename source, left-censored existing artifact rename to a new path, confirmed
create eligibility, delete then recreate, directory scope exclusion, failed mutation
exclusion, vendor-specific ok/fail/observed status coverage, recognized and
unrecognized validation, competing outcomes, end censoring, and cross-session
reuse.

A real AgentSight-only preflight then checks:

- the repository and revision resolve;
- candidate, parsed, included, and excluded direct sessions reconcile, with
  exclusion reason buckets and vendor/worktree strata;
- included and worktree-attributed session/action counts are both reported;
- at least two worktree-attributed native sessions and one confirmed-success non-scope
  mutation are admitted, and observation span is reported;
- vendor/session/effect/status/path coverage sums to the emitted totals;
- every CSV source ID resolves to an exported event row;
- recomputing summary counts from mutation/artifact CSVs is exact; and
- both figures render without substituting fixture values.

The full command always scans all six fixed cases because coverage failure is a
result. A case qualifies as longitudinal only with at least two worktree-attributed
sessions and one confirmed-success non-scope mutation; the validation panel
additionally requires one recognized successful validation. It must not
substitute global path matches, fabricated status, or another repository. If
fewer than four projects qualify, all RQ1 cross-case interpretation stops and
only source coverage is reported. A dimension also stops if fewer than four
projects have eligible rows. Any source-ID mismatch, inconsistent summary,
parser panic, nonzero figure script exit, or use of data outside the frozen
output directory blocks interpretation and requires repair plus a fresh run.

## 8. Verification and review

Required commands and evidence:

```bash
cd agent-session && cargo test
cd ../agentvis && cargo test
cargo run --manifest-path agentvis/Cargo.toml -- research-rq1 \
  --output <preflight>/raw /home/yunwei37/workspace/agentsight
# then the fixed six-project command
python3 <plot-script> --input <full>/raw --output <full>/figures
```

The full run freezes a fresh wall-clock cutoff immediately before extraction;
only events at or before that cutoff enter the trace, and final workspace state
is queried in the same read-only run. The exact commands, revisions, tool
versions, cutoff, wall time, and stdout/stderr are captured in `commands.log`.
A fresh reviewer must approve this plan before
implementation, and another fresh reviewer must inspect raw rows, aggregation,
plots, and claims after the full run. Only the reviewed full run may update the
paper's RQ1 result placeholders.
