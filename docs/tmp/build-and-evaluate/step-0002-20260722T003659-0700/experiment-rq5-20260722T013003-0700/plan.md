# RQ5 Experiment Plan — Attention Allocation and Migration

**Created:** 2026-07-22T01:30:03-07:00  
**State:** preregistration draft; no RQ5 statistic has been computed

## 1. Question and boundary

RQ5 asks where path-resolved non-scope file-directed activity in the
RQ1 projection is allocated across artifact types and repository modules, and
how those hotspots move over the native action sequence. It does not recover
failed attempted paths, files examined by directory-scope search, operation
duration, internal attention, effort, or time spent. File size, force-layout
coordinates, Git commit time, and LLM token volume do not define this activity.

## 2. Frozen source and classification

Reuse the authoritative RQ1 event rows at cutoff `1784708569241`. Include
path-resolved non-scope actions whose enclosing event status is either `ok` or
`observed`, and report the two status strata separately. Here, "resolved"
describes path resolution only: it does not upgrade an `observed` event to a
confirmed effect. Each included action contributes one primary unit per
distinct `(event_id, worktree_id, artifact_id, operation)`; retain operation so
the two exact strata remain **read** and **mutation = {write, create, rename,
delete}**. The Tool-call sensitivity assigns one unit independently within
each present operation stratum. After deduplicating lineage IDs, each lineage
in that call and stratum receives weight `1 / number_of_distinct_lineage_ids`;
weights are then summed by artifact class. A mixed read/mutation call therefore
contributes one unit to each separate stratum. The analysis reconciles each
stratum's total fractional weight to its number of eligible calls and repeats
the primary allocation on `ok` events alone as a status sensitivity. It never
orders paths inside a call. RQ5
consumes the independently reconciled RQ4 per-access identity replay; if that
replay fails review, lineage transitions stop and only path-class allocation
remains.

Use classifier version `artifact-path-v1`. Rules are applied in this frozen
order, case-insensitively, and the first match wins:

1. **test/benchmark:** a path component in `test`, `tests`, `spec`, `specs`,
   `bench`, `benches`, `benchmark`, `benchmarks`, `fixture`, `fixtures`; or a
   basename matching `test_*`, `*_test.*`, `*.test.*`, or `*.spec.*`;
2. **paper/documentation/research note:** a component in `doc`, `docs`, `paper`,
   `papers`, `note`, `notes`, or `research`; a basename matching
   `^(readme|changelog|license)(\.[^.]+)?$`;
   or extension `.md`, `.mdx`, `.rst`, `.tex`, `.bib`;
3. **configuration/build:** a component in `.github`, `.gitlab`, `config`,
   `.config`, `ci`, or `scripts`; exact basename `cargo.toml`, `cargo.lock`,
   `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
   `makefile`, `cmakelists.txt`, `dockerfile`, `pyproject.toml`, `setup.py`,
   `requirements.txt`, `go.mod`, `go.sum`, `build.gradle`, or `pom.xml`; or
   extension `.toml`, `.yaml`, `.yml`, `.ini`, `.cfg`;
4. **data/input:** a component in `data`, `dataset`, `datasets`, `input`, or
   `inputs`; or extension `.csv`, `.tsv`, `.jsonl`, `.parquet`, `.sqlite`, `.db`;
5. **result/figure/log:** a component in `result`, `results`, `output`,
   `outputs`, `figure`, `figures`, `plot`, `plots`, `log`, or `logs`; or
   extension `.png`, `.jpg`, `.jpeg`, `.svg`, `.gif`, `.mp4`, `.log`;
6. **source code:** extension `.c`, `.h`, `.cc`, `.cpp`, `.rs`, `.go`, `.py`,
   `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, `.kt`, `.swift`, `.rb`, `.php`,
   `.sh`, `.bash`, `.css`, `.scss`, or `.html`; and
7. **other/unknown:** every remaining retained file, including ambiguous
   extensionless and generic `.json` paths.

All names and regular expressions above are exhaustive, case-insensitive, and
applied after repository-relative normalization with no `.` or `..`. Rename
uses the destination path for allocation and exports the source/destination
module pair; explicit RQ1 lineage remains one artifact.

The default module is the first repository-relative path component; root files
form a named `repo-root-files` module, not `/` or `(root)`. Worktrees remain
separate identities but use the same path classification. Generated files that
are ignored by the repository projection remain outside the source universe.

## 3. Deterministic measurements

Report per project and operation:

1. exact action and Tool-call allocation by artifact type;
2. exact module access/mutation counts, distinct active sessions, and first/last
   action time;
3. transitions between consecutive resolved file-directed Tool calls, sequenced
   independently within each `(project, worktree_id)` lane. An event touching
   multiple worktrees appears once in each affected lane; no cross-worktree
   adjacency is formed. Within a lane, each call has sets of RQ1 artifact IDs
   and module keys; classify mutually exclusively as same artifact if lineage
   sets intersect, otherwise same module if module sets intersect, otherwise
   cross-module. Report singleton-only calls as sensitivity. These transitions
   describe movement of merged observed workspace activity, not a single
   Agent's serial cognitive path, because concurrent native sessions may
   interleave;
4. module-return episodes on each worktree-lane resolved Tool-call sequence.
   After a call containing module `m`, open a return-risk interval only at the
   first subsequent resolved call that does not contain `m`, retaining the last
   containing call as the distance origin. Close it at the next call containing
   `m`; this is a return. Export exact call-step and wall-time distance plus same
   versus different native session ID. At observation end, right-censor only
   intervals still open. A module present in the final call has no terminal
   interval. Export observed/censored status explicitly; and
5. cumulative leader-change sequences for accumulation plus exact
   return/terminal-gap distributions for inactivity, without treating Nebula
   force positions as data. Within each worktree lane, a module receives at
   most one cumulative count per resolved call. Export a leader-change row
   whenever the lexically sorted set of maximum-count modules changes; retain
   ties rather than breaking them arbitrarily.

No ordinal session distance, transition entropy, local-window hotspot, cooling
score, or forgetting claim is included.

## 4. Figure F8

F8 is emitted as two paper-width vector figures so every printed label remains
at least 7 pt: F8a isolates status sensitivity; F8b carries spatial dynamics.

- **Panel A — artifact allocation:** per-project 100% stacked bars for read and
  mutation actions across the fixed artifact classes, with exact totals.
- **Panel B — module activity over action time:** one small-multiple heatmap per
  project. Select the top 8 `(worktree_id,module)` keys by full-trace resolved
  Tool-call count, with each multi-file call counting at most once per module
  key; break ties lexically, aggregate all others into `remainder`, then order
  displayed rows lexically. Partition calls into 60 nearly equal-count columns
  using `floor(call_index * 60 / N)`, capped at 59; cells count calls. For
  color, divide every cell by the maximum cell count in its row; an all-zero row
  remains zero, and `remainder` uses the same rule. Exact counts remain in CSV
  and labels. This is display compaction, not a cooling metric.
- **Panel C — spatial transition summary:** same-artifact, same-module, and
  cross-module transition proportions plus exact module-revisit distance
  summaries. This is source-path space, not 2-D force-layout space.

Directory colors in Agent Nebula may reuse the stable classifier palette, but
the statistical figure is generated directly from source rows.

## 5. Verification and stop rules

- Run:

  ```bash
  python3 agentvis/research/plot_rq5.py \
    --rq1-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw \
    --rq4-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq4-20260722T013003-0700/raw \
    --output docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq5-20260722T013003-0700
  ```

  Verify frozen hashes; write `raw/rq5-actions.csv`, `rq5-calls.csv`,
  `rq5-transitions.csv`, `rq5-module-returns.csv`, `rq5-coverage.csv`,
  `rq5-summary.csv`, `rq5-module-summary.csv`, `rq5-leader-changes.csv`, and
  render `figures/rq5-artifact-allocation.pdf/.png` plus
  `figures/rq5-activity-migration.pdf/.png` by rereading those rows.
- Unit-test all classifier precedence/basename/rename cases, fractional fan-out,
  set-valued transition precedence, singleton sensitivity, return/terminal gap,
  top-8 ties, 60-bin boundaries and root module. Report unknown.
- Reconcile primary file actions by `ok`/`observed` status, distinct calls,
  per-stratum fractional weights and their eligible-call denominators,
  scope-only calls, failed calls with unavailable paths and vendor/project
  coverage against frozen RQ1 rows.
- Apply the four-project gate separately: allocation requires 100 resolved
  non-scope file actions; transition requires 100 eligible adjacent resolved
  calls and at least two modules; revisit requires 20 returns and at least two
  modules. Undefined dimensions remain coverage-only.
- Report sensitivity at Tool-call rather than file-action weighting.
- Do not call a module “important” solely because it is frequently accessed;
  report activity/hotspot, not value or correctness.

The possible result is descriptive heterogeneity or homogeneity among six
observed projects. Neither explains cause nor estimates an Agent population.

Independent plan and result reviews are required before F8 enters the paper.
