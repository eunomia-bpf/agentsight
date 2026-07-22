# RQ7 Experiment Plan — Matched-Benchmark Readiness and Source Contract

**Revised:** 2026-07-22 after independent Round-1 BLOCK  
**State:** preregistration draft; no baseline accuracy comparison will be run in this step

## 1. Narrow question and claim boundary

This step asks a prerequisite question: **does the already frozen RQ1 corpus
contain the immutable source universe required to run a matched, independently
scored comparison of Final State, Counts, pinned ProcGrep, bounded Raw-log LLM,
and Artifact Trajectory?**

It does not estimate method accuracy, trajectory advantage, evidence precision,
or query cost.  If any required source contract is absent, F10 records a
coverage stop and renders the affected method/template as N/A.  The result is a
benchmark-readiness audit, not the canonical RQ7 capability answer.

## 2. Authoritative inputs and executable command

The audit reads only:

1. frozen `projects.json` at cutoff `1784708569241`;
2. the six frozen normalized `events/*.json.gz` files;
3. the frozen RQ1 artifact and mutation tables;
4. the pinned ProcGrep revision recorded in this plan,
   `2e8277003dacaa774b5ef61ba150ae03a4f06693`; and
5. repository file-presence and SHA-256 checks under the RQ1 frozen directory.

The single command is:

```bash
python3 agentvis/research/plot_rq7.py \
  --rq1-root docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq1-20260722T003659-0700/full-six-projects/raw \
  --output docs/tmp/build-and-evaluate/step-0002-20260722T003659-0700/experiment-rq7-20260722T013003-0700
```

The script writes `raw/rq7-source-contract.csv`,
`raw/rq7-method-readiness.csv`, `raw/rq7-template-readiness.csv`, `result.md`,
and F10 PDF/PNG.  Missing inputs are rows with status `N/A`; they are never
encoded as zero performance.

## 3. Machine-checkable source contract

For every project the audit checks these distinct requirements:

- **normalized action spine:** an immutable gzip and SHA-256 exists;
- **normalized source linkage:** project/vendor/session/event/source-call IDs
  are present and counted, with missing values reported rather than imputed;
- **native admitted-prefix manifest:** every admitted session has native path,
  admitted record/byte boundary, exact-prefix SHA-256, vendor, session ID, and
  cutoff;
- **native prefix archive:** the manifest's content-addressed native prefixes
  exist under the frozen experiment or a declared immutable archive;
- **worktree revision manifest:** every RQ1 worktree ID maps to root and exact
  cutoff Git revision/tree;
- **cutoff untracked snapshot:** untracked final-state content at cutoff is
  explicitly captured or declared unavailable.

An aggregate repository `revision`, root path, or count of available worktrees
does not satisfy a per-worktree cutoff manifest.  A normalized
`RepositoryTrace` is not relabeled as a native raw prefix.

## 4. Conditional method admission

The readiness rules are deterministic:

- **Counts (normalized):** admitted for descriptive counts when normalized
  events and their hashes are present.  It is not an oracle and cannot answer
  artifact lineage merely because RQ1 tables coexist.
- **Artifact Trajectory (normalized):** admitted for replaying the already
  reviewed trajectory queries when normalized events plus RQ1 identity tables
  are present.  It cannot be accuracy-scored against those same tables.
- **Final State:** admitted to a matched comparison only with every relevant
  worktree cutoff revision/tree and an explicit untracked-state disposition.
- **ProcGrep:** admitted only with the native admitted-prefix manifest/archive
  plus a recorded real preflight for Claude, Codex, and Gemini at the pinned
  revision.  Its official condition remains `trace_id + atoms + metadata`; no
  path or native evidence crosswalk may leak into answer logic.
- **Raw-log LLM:** admitted only after the native prefix contract and a frozen
  model/provider/version, prompt, deterministic retriever, context/output
  budgets, retry/cache policy, maximum calls, and token/dollar cap all exist.

`measured` means the prerequisite is present and machine checked;
`coverage-only` means a normalized method can run but no independent matched
oracle exists; `N/A` means the matched condition cannot be executed.

## 5. Template-family readiness

F10 audits four planned template families without generating questions:

- **action-only:** requires the native prefix contract and independent native
  oracle before Counts/ProcGrep/Raw-log/Trajectory can be scored together;
- **artifact-linked:** additionally requires declarative source-explicit
  identity semantics; Bash-inferred effects, directory scope, and missing
  status cannot become gold;
- **cross-session:** additionally requires source-explicit session identity and
  ordering; overlapping sessions cannot be forced into a serial boundary;
- **final-state:** requires cutoff worktree revisions and untracked-state
  disposition.

The template-level `30 scored questions × 4 projects` gate is reported as
`not evaluated` in this audit.  It cannot be borrowed across template families;
the 66 explicit rename rows spanning only three projects remain a disclosed
future coverage limit.

## 6. F10 rendering contract

F10 contains only measured readiness facts:

1. project-by-source-contract matrix with `present`, `partial`, and `N/A`;
2. method admission matrix with status and a short blocking requirement;
3. template-family readiness matrix;
4. an explicit `MATCHED COMPARISON STOPPED` panel listing missing contracts.

Every cell is labeled; gray N/A is visually distinct from observed zero or
partial coverage.  The figure contains no accuracy, coverage delta, latency,
token, cost, or evidence-sufficiency value because none has been validly run.

## 7. Completion and stop rules

- All frozen input hashes must be recorded before plotting.
- CSVs and PNG must be byte-identical across consecutive runs.
- Any attempt to infer native-prefix availability from normalized events, or
  cutoff worktree state from a current checkout, invalidates the audit.
- Independent result review must confirm every readiness cell against the
  filesystem and manifest schemas before F10 enters the paper.
- The future matched comparison requires a new reviewed plan implementing the
  Round-1 review's oracle dispositions (`TRUE`, `FALSE`, `UNAVAILABLE`,
  `AMBIGUOUS_EXCLUDED`), typed templates, exact method interfaces, citation
  validity/sufficiency/burden, and cold/warm cost accounting.
