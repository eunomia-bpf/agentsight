# RQ6/F9 Independent Result Review — Round 1

**Reviewed:** 2026-07-22  
**Scope:** approved coverage-only plan, both plan reviews, authoritative command,
implementation, four CSV outputs, result report, and PDF/PNG figure  
**Verdict:** **BLOCK**

## Decision

The source extraction and tabulation are valid and independently reproducible,
but F9 is not yet safe to enter the paper. Panel B converts seven unavailable
project-by-vendor strata into the same visual zero used for an available stratum
with no matching event. It also calls the cells event counts while providing no
colorbar or annotations from which a count can be read. This violates the
approved N/A-versus-observed-zero rule and makes the central coverage figure
ambiguous. The raw CSVs and `result.md` need not be discarded; the figure
encoding must be repaired and regenerated from those CSVs.

## Independent recomputation

I reran the authoritative command into a fresh directory and independently
parsed the six frozen gzip event files without importing `plot_rq6.py`.

- The frozen corpus contains 206,249 Tool events and 2,049 unique admitted
  sessions. Every project and project/vendor session denominator exactly equals
  `projects.json` and `rq6-session-coverage.csv`.
- All 1,762 rows in `rq6-observed-events.csv` map to exactly one frozen
  `RepositoryEvent.id`. Vendor, session, event index, timestamp, status,
  `source_call_id`, operation, path, and previous path all match the source.
- An independent implementation of the exact case-insensitive Tool/basename
  rules produced exactly the same 1,762 rows: 67 `skill_tool`, 1,303
  `instruction_read`, and 392 `instruction_mutation`. There were no missing or
  extra action-ordinal keys.
- The rows cover 1,525 unique native Tool events. Every row and every unique
  event has a nonempty source call ID in this corpus; the source-coverage table
  reports the same coverage.
- Native status is preserved: 1,670 `ok`, 91 `observed`, and one `fail`. Empty
  count cells remain explicit zeros in the CSV, and no unavailable process
  outcome was synthesized.
- The 1,080 action-bin rows are complete (six projects by three kinds by 60
  bins). Every unique-event count independently recomputes under
  `min(59, floor(event_index * 60 / N))`. All six event streams are monotonic in
  timestamp, and the figure correctly says this is merged action order rather
  than wall-clock time.
- Re-execution produced byte-identical four CSVs, PNG, and result report. The
  observed peak RSS was 414,236 KiB and wall time was 1.61 seconds, consistent
  with `commands.log`. The recorded hashes for implementation and all outputs
  match the current files. PDF metadata nondeterminism is correctly disclosed.

## Rule-specific audit

### Exact Tool and path rules — pass

`tool_name` is compared case-insensitively to exact `skill`. Instruction paths
are non-scope actions whose case-insensitive basename is exactly `AGENTS.md`,
`CLAUDE.md`, or `SKILL.md`. Reads and mutations are kept as distinct,
non-exclusive source kinds. Multi-path events remain multiple signal rows but
collapse to unique Tool events where the figure says “events.”

### Rename endpoint rule — implemented but corpus-unengaged

The implementation checks both destination and previous path and de-duplicates
the case where both endpoints qualify. The built-in check exercises this rule.
The frozen corpus contains **zero** qualifying rename rows, so this is a code
sanity check rather than empirical evidence; the result makes no rename claim.

### Denominators, source IDs, status, and N/A — tables pass; Panel B fails

The CSV denominators and source-ID/status accounting pass. The plot creates a
27-column matrix for Claude, Codex, and Gemini, but fills a missing lookup with
zero. Seven project/vendor combinations have no admitted session and are absent
from the CSV by design:

- ActPlane/Gemini;
- eunomia.dev/Claude and eunomia.dev/Gemini;
- AgentSkill paper/Codex and AgentSkill paper/Gemini; and
- Writing skills/Codex and Writing skills/Gemini.

These cells are **N/A**, not observed zeros. In the current PNG/PDF they are
indistinguishable from valid zero-count cells. Panel B must use an availability
mask (or equivalent explicit N/A encoding) derived from session coverage. It
must also expose the log-color mapping with a labeled colorbar or print compact
counts; otherwise “unique signal events” cannot be recovered from color.

### Non-exclusive accounting and 60 bins — pass

Session-kind numerators regenerate from the raw signal ledger and may sum above
the number of sessions, as declared. Panel A labels exact numerators and
denominators. Panel C uses row-max color only after printing each row's total
unique-event count, so its normalization is explicit and does not masquerade as
cross-project magnitude.

### Figure language and legibility — partial pass

The figure consistently says source-signal coverage, prints
`ASSOCIATION ANALYSIS STOPPED`, lists unavailable fields, and avoids any effect,
confidence interval, or forest plot. The PDF is exactly 7.05 inches wide, has
embedded TrueType fonts, and the minimum declared label size is 7 pt; the PNG is
readable at full size. Panel subtitles and stop banner are useful. The large
top-level `RQ6/F9` title should move to the LaTeX caption before paper inclusion,
because result plots should not spend plot area on a duplicate in-figure title;
this is secondary to the N/A/count-encoding defect.

## Required repair before PASS

1. Derive project/vendor availability from `rq6-session-coverage.csv`; display
   absent vendor strata as explicit N/A, visually distinct from available
   zero-count cells.
2. Add a labeled event-count color scale or unobtrusive count annotations to
   Panel B. Preserve the log or log-like mapping and state it exactly.
3. Regenerate both PDF and PNG only from the frozen CSVs, rerun the byte-level
   CSV/PNG determinism check, and update hashes in `commands.log`.
4. Prefer removing the duplicate top-level in-figure title when F9 is copied to
   the paper; retain the panel labels and stop banner.

No new corpus, association analysis, outcome metric, bootstrap, baseline, or
human/LLM annotation is required.

## Result-review judgments

```text
run status: valid (numeric outputs); paper figure incomplete
tested hypothesis: supported — the frozen source fields are insufficient for a valid skill/harness association analysis
research value: supporting
paper impact: measurement/workload boundary for RQ6
next paper decision: retain the explicit association stop and coverage result, but do not embed F9 until N/A and event-count encoding are repaired and independently rechecked
```

