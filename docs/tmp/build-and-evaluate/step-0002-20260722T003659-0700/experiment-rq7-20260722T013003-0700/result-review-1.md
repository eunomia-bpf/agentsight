# RQ7/F10 Independent Result Review — Round 1

**Reviewed:** 2026-07-22  
**Reviewed scope:** dependency-only matched-benchmark readiness audit approved
by `plan-review-2.md`; no canonical RQ7 capability comparison  
**Verdict:** **BLOCK pending execution-record and figure-legibility repair**

## Formal judgment

```text
run status: incomplete
tested hypothesis: supported within the dependency-only scope
research value: dependency-only
paper impact: measurement/workload boundary; canonical RQ7 remains open
next paper decision: preserve the stopped comparison, complete its run record,
                     repair the sub-7pt labels, then rerun the same audit
```

The reported readiness state is independently reproducible and does not contain
fabricated baseline performance.  The BLOCK is not about the 12/24 counts or
the stopped interpretation.  It is because the experiment's `commands.log` is
zero bytes despite a preregistered consecutive-run determinism gate, and one
class of figure annotations is drawn below the paper's 7 pt legibility floor.
Both are bounded repairs that preserve the approved estimand and require no new
baseline, oracle, question set, or model call.

## Materials audited

- Approved Round-2 plan and both plan reviews.
- `agentvis/research/plot_rq7.py` in full.
- Authoritative RQ1 `commands.log`, `projects.json`, six normalized event
  archives, artifact table, mutation table, and summary table.
- RQ7 source-contract, method-readiness, and template-readiness CSVs.
- RQ7 `result.md`, PDF, PNG, and `commands.log`.
- Two fresh independent executions into separate temporary output directories.

## Independent source and hash verification

The script's ten `EXPECTED_HASHES` values are not runtime self-baselines.  I
parsed them from the implementation, parsed the previously recorded expected
hashes from the authoritative RQ1 `commands.log`, and recomputed every file
hash.  For all ten inputs:

```text
implementation constant == prior RQ1 expected hash == current file SHA-256
```

This includes `projects.json`, `rq1-artifacts.csv`, `rq1-mutations.csv`,
`rq1-summary.csv`, and all six `events/*.json.gz` files.  The audit therefore
uses pre-recorded expectations rather than calculating and accepting a new hash
in the same run.

The contract paths are fixed in code beneath the frozen RQ1 root:

```text
contracts/native-prefix-manifest.json
contracts/native-prefixes.tar.zst
contracts/worktree-revisions.json
contracts/cutoff-untracked-state.json
contracts/procgrep-preflight.json
contracts/raw-log-llm.json
```

None exists.  No similarly named file was substituted.

## Source-contract reconciliation

I independently parsed all output rows and all six normalized gzip payloads.
The output has exactly six projects by six requirements:

| Requirement | Present | Partial | N/A | Independent check |
|---|---:|---:|---:|---|
| normalized action spine | 6 | 0 | 0 | all six files match prior RQ1 hashes |
| normalized source linkage | 6 | 0 | 0 | all 206,249 events carry nonempty `id`, `source_call_id`, `session_id`, `vendor`, and `ts_ms` |
| native-prefix manifest | 0 | 0 | 6 | exact contract absent |
| native-prefix archive | 0 | 0 | 6 | exact contract absent |
| worktree cutoff revisions | 0 | 0 | 6 | exact contract absent |
| cutoff untracked disposition | 0 | 0 | 6 | exact contract absent |

Total: **12 present, 0 partial, 24 N/A**, matching the CSV and `result.md`.

The implementation imports no subprocess/Git runner and contains no home,
Claude, Codex, Gemini, or repository-root traversal.  All source-contract reads
are beneath the supplied frozen RQ1 root.  It does not inspect a live checkout,
live native session, or current final state.

## Method and template reconciliation

The method CSV exactly contains:

| Condition | Status | Review interpretation |
|---|---|---|
| Counts (normalized) | measured | prerequisite availability for descriptive counts only; no method accuracy |
| Artifact Trajectory | coverage-only | normalized projection exists; RQ1 tables are not used as its oracle |
| Final State | N/A | cutoff worktree/untracked contracts absent |
| ProcGrep | N/A | native prefixes and pinned three-vendor preflight absent |
| Raw-log LLM | N/A | native prefixes and frozen model/budget contract absent |

The template CSV has exactly four families.  Every family is `N/A`, and every
`30 x 4` gate is literally `not evaluated`.  No event, artifact, mutation, or
session count is relabeled as a sampled question.  The 66/three-project rename
limit is not converted into a scored template result.

## No circular oracle or pseudo-performance result

The audit generates no questions and calls no method under comparison.  It
does not score an RQ1 identity, persistence, reuse, or validation label as truth
for another method.  RQ1 artifact/mutation hashes establish only that the
normalized Artifact Trajectory condition is available, which is then labeled
`coverage-only`.

The result CSVs contain only readiness status and explanatory text.  They have
no accuracy, coverage advantage, evidence precision/recall, score, latency,
token, or cost field.  `result.md` and the figure explicitly state that no such
result was produced.  N/A is stored as the literal string `N/A`; the plotting
code uses an internal categorical color index but displays gray `N/A` text, no
numeric zero, no ratio, and no performance axis.

## Independent determinism run

I executed the approved command twice into two new temporary directories.  The
following outputs were byte-identical between the two runs and byte-identical
to the experiment directory:

| Output | SHA-256 |
|---|---|
| `rq7-source-contract.csv` | `f236880339d484a090b219c975f2fccdc1518b28621072b021f9038457148808` |
| `rq7-method-readiness.csv` | `3a546a3bcbd8946ee7695feb6c4fa5969af6ec240520a0fa4ab6c83177521adc` |
| `rq7-template-readiness.csv` | `f4ed2d7065a1a2f834955b45a6c0e6e61cc51ee12b49a04b27b2a466f60f6d0a` |
| `result.md` | `fa5c2fa392203e377a3a2c9b517b37ce71876ffa8eaa3cfe6f4492ada271fc19` |
| `rq7-benchmark-readiness.png` | `3c26b1a3d2a3617d7ed4a3ae065034bf3dc09e674a1cd7b1548aa5a4f6610b22` |

The runs took 1.26 s / 1.13 s and 385,144 / 385,316 KiB maximum RSS in this
review environment.  The PDFs differed only because Matplotlib embeds creation
metadata; the approved plan requires byte identity for CSVs and PNG, not PDF.

## Figure audit

The figure is a 7.05 in x 7.25 in vector PDF with embedded TrueType fonts and a
1410 x 1450 PNG.  At full two-column width it is visually clear:

- the 6 x 6 matrix shows `present` text on green and `N/A` text on gray;
- `coverage-only` is amber and is not confused with measured or N/A;
- every method remains on the axis, including the three stopped conditions;
- all four template families retain explicit `N/A` and `30 x 4 not evaluated`;
- the red `MATCHED COMPARISON STOPPED` statement and its no-result qualifier are
  prominent; and
- color is not the sole encoding, so the statuses remain distinguishable in
  grayscale.

There is no performance curve or fake numeric panel.  The only readability
defect is that the 36 matrix cell annotations use `fontsize=6.5`.  The PDF is
already generated at approximately final two-column width, so those labels
print below the 7 pt hard floor.  All other main labels are 7 pt or larger.

## Blocking defects

### B1. Empty execution record

`experiment-rq7-20260722T013003-0700/commands.log` is **0 bytes**.  It therefore
does not record the approved command, environment, input/output hashes,
resource use, or the required two-run CSV/PNG determinism check.  A reviewer can
reproduce the outputs, as above, but that does not make the submitted run
complete.

**Repair:** run the same approved command twice, record the command, Python and
Matplotlib versions, both run resource lines, prior expected-input hashes,
actual input hashes, output hashes, and explicit CSV/PNG equality.  Record PDF
metadata nondeterminism as non-gating rather than falsely claiming PDF byte
identity.  Do not change any result cell.

### B2. Matrix annotations below the legibility floor

`plot_rq7.py:290` draws the source-contract cell text at 6.5 pt.  This is below
the 7 pt minimum at the figure's intended printed width.

**Repair:** increase those annotations to at least 7 pt, regenerate PDF/PNG,
visually inspect at final paper width, and update the recorded output hashes.
No layout, status, color, or data change is required.

## Non-blocking implementation limitation

The currently absent native archive path would be marked present from archive
existence plus declared member names without opening the tar.zst and verifying
each member hash.  This does not affect the reviewed 24 N/A cells because the
archive is absent.  Before a future audit can ever return `present` for that
contract, the checker must validate actual archive membership and content
hashes.  It is not authorization to create or backfill the missing historical
archive in this run.

## Decision

**BLOCK this result artifact, not its stopped scientific interpretation.** The
readiness counts, statuses, N/A handling, lack of live-state leakage, and
non-performance conclusion all independently reproduce.  Complete the bounded
run-record and font-size repairs, rerun the unchanged readiness audit, and
request one follow-up result review.  The follow-up needs no new scientific
plan and must not expand into the canonical RQ7 benchmark.
