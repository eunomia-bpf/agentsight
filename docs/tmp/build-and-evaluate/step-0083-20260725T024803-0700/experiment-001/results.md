# Results — step 0083 experiment-001: index-study replication on HINTBench (v2, opencode reader)

Scope: three reader conditions on the complete HINTBench workload, compared
against the two stored step-0072 baselines (Direct-only / `local_only` and
Direct+AgentProf / `local_agentprof`). 400 target-bearing queries out of 536
test trajectories are scored; the 136 zero-positive trajectories are consumed
for coverage and excluded from MAP, exactly as the paper protocol states.

This is the **v2** run. Per addendum-001 (kimi quota exhausted at ~440/1,200
work items) and addendum-002 (prescriptive reader recipe), the reader for ALL
conditions on this workload is `opencode run --pure` (default model glm-5.2).
The kimi partials in `raw-responses-*` (no `-v2`) are **set aside, not scored
and not deleted**; only the `raw-responses-*-v2` opencode outputs are scored.
No existing file was modified; no git command was run; no CLI-tool
configuration or home directory was inspected or touched.

## Reader recipe (addendum-002, followed exactly)

- Invocation: `opencode run --pure "<packet+instruction>"`, via `subprocess`
  with `cwd=experiment-001/reader-jail` (fresh EMPTY directory), `stdin=/dev/null`.
  No `-m`/`--agent`/`--command`/`--format` flags added.
- Default model: **glm-5.2** (observed stderr banner `> build · glm-5.2`).
- Every packet instruction ends with the addendum-002 sentence: "Answer
  directly in strict JSON only. Do not use any tools, do not read or write any
  files, do not run any commands."
- Parser: FIRST JSON object in stdout (balanced-brace scan, ANSI stripped);
  one format retry per call; deterministic fallbacks (stage-1 fail → largest 5
  groups; stage-2/full fail → original-order ranking), all tallied.
- argv delivery for every call (all prompts < 30 KiB ≪ 128 KiB single-argv
  limit); the prescribed `prompt.txt` fallback was never triggered.
- Worker pool: 8 concurrent `opencode` processes per phase; conditions run
  **sequentially** (full → semantic → raw), each a complete 400-query phase
  with resume support.

### Reader-family disclosure

This workload's reader family (**opencode / glm-5.2**) differs from the
TraceElephant index study (**grok**). Every condition on THIS workload uses the
SAME opencode reader, so within-workload comparability is preserved. **No
number from this step is pooled with any TraceElephant number into one
statistic.** The original step plan named kimi as the reader; addendum-001
changed it to opencode after kimi's billing-cycle quota exhausted mid-run.

## Validation (≤3 queries, never a result)

`validate --workers 3` on the first 3 full-trace queries: **3/3 parsed OK on
the first attempt** (no retries, no fallbacks), `recipe_pass=True` (≥2/3),
61.5 s wall. Raw responses scanned for repository paths / target identifiers:
0 leakage hits.

## Completeness and integrity

- All three conditions ran to completion: **400/400** each, **0 errors**.
- Failure tally (deterministic fallbacks): 0 full-trace original-order
  failures; 0 stage-1 largest-groups fallbacks; 0 stage-2 original-order
  failures. 1 query in full-trace and 1 in raw needed the single format retry
  and then parsed (`ok_after_retry`); semantic parsed first-try on all 400.
- Stored-MAP reproduction check passed exactly: `local_only` 0.4105587754001585
  and `local_agentprof` 0.5174888725910552 both reproduced to < 1e-12.
- Leakage spot-check (addendum-001 point 1): 12 responses sampled across the
  three `-v2` directories; **0** referenced repository paths, target files, or
  benchmark identifiers. The jail worked; the packet was the only input.
- Harness wall: 7,627.6 s (~2.12 h) for the full three-condition run + scoring.

## Primary result — MAP over the 400 target-bearing queries

| Condition | MAP |
|---|---|
| Full-trace reader | **0.6235** |
| Raw-action-skeleton reader | 0.5545 |
| Semantic-skeleton reader | 0.5273 |
| Direct+AgentProf (stored) | 0.5175 |
| Direct-only (stored) | 0.4106 |

## Pairwise comparisons

Paired 10,000-draw trajectory-cluster bootstrap within HINTBench environment
strata (frozen seeds). `eff` = first − second MAP; `nonpos` = draws ≤ 0 out of
10,000.

| First − Second | eff | 95% CI | nonpos/10000 |
|---|---|---|---|
| full-trace − Direct-only | +0.2129 | [+0.1880, +0.2371] | 0 |
| full-trace − Direct+AgentProf | +0.1060 | [+0.0801, +0.1318] | 0 |
| full-trace − semantic-skeleton | +0.0962 | [+0.0690, +0.1237] | 0 |
| full-trace − raw-action-skeleton | +0.0689 | [+0.0438, +0.0939] | 0 |
| Direct+AgentProf − Direct-only | +0.1069 | [+0.0935, +0.1210] | 0 |
| raw-action-skeleton − Direct-only | +0.1440 | [+0.1154, +0.1722] | 0 |
| semantic-skeleton − Direct-only | +0.1167 | [+0.0862, +0.1461] | 0 |
| raw-action-skeleton − Direct+AgentProf | +0.0371 | [+0.0077, +0.0658] | 68 |
| semantic-skeleton − Direct+AgentProf | +0.0098 | [−0.0194, +0.0388] | 2579 |
| semantic-skeleton − raw-action-skeleton | −0.0273 | [−0.0531, −0.0022] | 9833 |

## Content efficiency and index-hit (skeleton conditions, ≤5-group budget)

| Metric | Semantic skeleton | Raw-action skeleton |
|---|---|---|
| Mean content opened (fraction of full-trace packet) | 0.2433 | 0.2576 |
| Mean selected-evidence operations | 6.49 | 7.04 |
| Mean stage-2 evidence chars | (see delta) | +154.4 chars vs semantic |
| Index-hit rate (target group among selected) | 0.8300 (332/400) | 0.8550 (342/400) |
| Mean group count per query | 20.5 | 17.4 |

Content delta (raw − semantic), paired bootstrap seed 20260927:
- `content_opened_fraction`: +0.0143, CI [+0.0090, +0.0195], 0 nonpos (raw opens
  ~1.4 percentage points MORE content than semantic).
- `selected_evidence_operation_count`: +0.5500, CI [+0.3800, +0.7225], 0 nonpos.
- `stage2_evidence_chars`: +154.36, CI [+89.84, +218.21], 0 nonpos.

## Costs (per condition, 400 queries)

| Condition | total wall | mean wall/call | total o200k tokens | mean tokens/call | mean chars |
|---|---|---|---|---|---|
| Full-trace | 12,180 s | 30.4 s | 1,239,128 | 3,098 | 11,382 |
| Semantic-skeleton (2 stages) | 24,201 s | 60.5 s | 2,581,557 | 6,454 | 21,673 |
| Raw-action-skeleton (2 stages) | 22,783 s | 57.0 s | 2,294,476 | 5,736 | 18,102 |

## Evaluation of the two registered hypotheses (from 000-step-entry.md)

**Hypothesis 1 — Ladder replication: "full-trace reader MAP > stored
Direct+AgentProf, and the semantic-skeleton reader lands between them."**
**Partially supported (non-replication of the middle rung).**
- full-trace (0.6235) > Direct+AgentProf (0.5175): **replicates strongly**
  (eff +0.1060, CI [+0.0801, +0.1318], 0/10000 nonpositive).
- semantic-skeleton (0.5273) is point-wise between Direct+AgentProf (0.5175)
  and full-trace (0.6235), but it is **not statistically distinguishable**
  from Direct+AgentProf (eff +0.0098, CI [−0.0194, +0.0388], 2579/10000
  nonpositive). The clean three-rung ladder seen on TraceElephant
  (Direct+AgentProf ≪ semantic-skeleton ≪ full-trace) is **compressed** on
  HINTBench: both skeleton readers only marginally clear Direct+AgentProf,
  while full-trace clears everything by a wide margin. (raw-action-skeleton
  0.5545 does clear Direct+AgentProf, eff +0.0371 CI [+0.0077, +0.0658], but
  with 68/10000 nonpositive draws — a marginal separation.)

**Hypothesis 2 — Content-efficiency replication: "at the fixed 5-group budget,
the semantic skeleton opens significantly less content than the raw-action
skeleton at statistically indistinguishable MAP."**
**Not replicated.**
- Direction of the content effect replicates: semantic opens significantly
  LESS content than raw (raw − semantic content_opened_fraction +0.0143, CI
  [+0.0090, +0.0195], 0/10000 nonpositive; semantic 0.2433 vs raw 0.2576).
- The "statistically indistinguishable MAP" precondition **fails**: raw-action
  skeleton achieves significantly HIGHER MAP than semantic-skeleton
  (semantic − raw eff −0.0273, CI [−0.0531, −0.0022], 9833/10000 nonpositive).
- Therefore on HINTBench the raw-action skeleton **dominates** the semantic
  skeleton (higher MAP, only ~1.4 pp more content opened, higher index-hit
  rate 0.855 vs 0.830). The TraceElephant finding — semantic is cheaper at
  equal accuracy — does **not** reproduce; here raw is both more accurate and
  only marginally more expensive.

## Interpretation and disposition

This is a genuine non-replication of both registered hypotheses as stated
(the middle ladder rung; the equal-MAP content-efficiency advantage of the
semantic skeleton). Consistent with the no-negative-results policy recorded in
`000-step-entry.md`, this does **not** enter the paper as a positive
cross-workload claim; it feeds iteration / scopes the semantic
content-efficiency claim to the TraceElephant workload until a third workload
or a revised mechanism explains the gap. The one robust cross-workload
regularity so far is that the **full-trace reader dominates every profile-only
condition and both stored Direct baselines** on both workloads.

Caveat: the reader family changed twice relative to the original plan
(planned kimi → opencode/glm-5.2 after quota; TraceElephant used grok). All
within-workload comparisons are valid (same reader for all five conditions on
HINTBench), but the absolute MAP levels are not comparable across workloads
and are not pooled.

## Artifacts (all inside this experiment-001 directory)

- `hint_index_study_eval_v2.py` — v2 harness (opencode reader).
- `packets-full-v2/`, `packets-{semantic,raw}-stage{1,2}-v2/` — reader packets.
- `raw-responses-{full,semantic,raw}-v2/` — scored opencode responses
  (`raw-responses-*` without `-v2` are the set-aside kimi partials).
- `raw-results-v2.json`, `summary-v2.json` — scored per-query + summary.
- `bootstrap-deltas-*-v2.json` (10), `bootstrap-content-delta-*-v2.json` (3) —
  raw bootstrap draws.
- `validate-summary-v2.json` — 3-query reader-recipe validation.
- `validate-v2.stdout.log`, `full-run-v2.stdout.log`, `*.stderr.log` — logs.
- `execution-log-v2.md` — v2-phase execution log (the kimi-phase
  `execution-log.md` is left untouched).
