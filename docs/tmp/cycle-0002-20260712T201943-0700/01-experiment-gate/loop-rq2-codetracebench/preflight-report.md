# REAL PREFLIGHT Report: CodeTraceBench RQ2 Differential Profiling

**Started:** 2026-07-12T21:28:00-07:00
**Completed:** 2026-07-12T22:50:35-07:00
**Cycle/gate:** cycle 0002 / EXPERIMENT
**Parent plan:** `experiment-plan.md` revision 6
**Runner:** `../../../../../script/codetracebench_agentprof_eval.py`
**Source-only dependency check:** PASS on six selected source variants
**Complete verified-source audit:** PARTIAL PASS with explicit exclusions
**End-to-end REAL PREFLIGHT:** PASS
**Scientific result:** not yet available; full run has not started

## Purpose And Decision Boundary

This node asks whether the approved CodeTraceBench experiment can execute on
real public inputs through the same deterministic path intended for the full
run. It is not a smoke substitute and it does not answer RQ2. A favorable
metric is deliberately not a preflight condition.

REAL PREFLIGHT requires:

1. public source operations reconstructed without step annotations;
2. source steps aligned one-to-one with the public manifest count, with
   mismatches excluded rather than count-fitted;
3. release AgentProf invoked on semantic, raw-action, and phase organizations;
4. AgentProf output matched exactly by an independent counter;
5. task-held-out failed-minus-successful reference profiles constructed;
6. target scores and a human-readable prediction file written before labels;
7. `incorrect_stages` loaded only at the terminal metric step; and
8. pooled tie-block AP, recall at 30% work, and work to 50% recall computed.

All eight conditions completed on real data.

## Public Inputs

- CodeTraceBench full manifest: 3,316 trajectories, 147,628 declared steps.
- Verified manifest: 1,000 trajectories, 46,539 declared steps; an exact subset
  of the full manifest.
- Downloaded official raw archives: 3,291 full rows and 992 verified rows.
- Official CodeTracer checkout:
  `2d302191dd07e7c0c2da6f7a5e9451c7cbb62d34`.
- Release AgentProf: `0.2.37`.

The source and scoring phases projected only trajectory identity,
agent/model/task/category/difficulty metadata, outcome, public `step_count`, and
raw-artifact paths. They did not project `stages`, `incorrect_stages`, label
reasoning, or annotation-generated step files. Verified outcome selected the
failed target population but was not a step feature or score.

## Commands

Complete verified-source audit:

```bash
python3 script/codetracebench_agentprof_eval.py source-audit \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --out docs/visexp/out/codetracebench-rq2
```

End-to-end REAL PREFLIGHT:

```bash
python3 script/codetracebench_agentprof_eval.py real-preflight \
  --full-manifest .agentsight/experiments/codetracebench-rq2/manifests/full.parquet \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --codetracer-root .agentsight/experiments/codetracebench-rq2/CodeTracer \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/codetracebench-rq2
```

## Complete Verified-Source Audit

The runner inspected all 992 raw-available verified archives. It retained 911
with exact public operation-count alignment and excluded 89 missing, mismatched,
or adapter-error rows. The 911 source-valid rows comprise 483 solved, 405
failed, and 23 missing-outcome trajectories. The 405 failed rows contain 20,866
declared source steps and define the primary full-run population.

| Framework | Source layout | Available | Exact | Mismatch | Error | Missing |
|---|---|---:|---:|---:|---:|---:|
| OpenHands | native | 199 | 185 | 14 | 0 | 8 |
| OpenHands | SWE raw | 313 | 313 | 0 | 0 | 0 |
| SWE-agent | SWE raw | 108 | 106 | 2 | 0 | 0 |
| Terminus2 | native | 222 | 174 | 46 | 2 | 0 |
| mini-SWE-agent | native | 82 | 65 | 17 | 0 | 0 |
| mini-SWE-agent | SWE raw | 68 | 68 | 0 | 0 | 0 |

The detailed exclusion ledger is
`../../../../visexp/out/codetracebench-rq2/verified-source-alignment-audit.md`.
No mismatch was truncated, padded, reordered, synthesized, or recovered from
annotation text.

## Source Rules Established By The Complete Audit

- MiniSWE prefers the released `.traj.json` assistant bash-action stream. Its
  terminal-log fallback strips ANSI, uses visible agent-step markers, and reads
  only an assistant bash fence before the next user prompt.
- Native OpenHands uses chronological agent-source actions except `system` and
  `message`; it keeps real `think`, run, read, edit, and finish actions and
  pairs observations only through integer `cause`.
- SWE-raw OpenHands selects the request with maximum complete visible assistant
  tool-call history, ties by later timestamp/path, and excludes that request's
  response. This aligned 313/313 archives, including 57 with context decreases
  and 137 with tied maxima across 14,070 request records.
- Terminus2 uses string records from released `commands.txt`, including empty
  strings; list records are harness actions, and episode-response JSON is not a
  benchmark step stream.
- SWE-agent uses one operation per released `.traj` `trajectory[]` element.

These are source-structural rules. Manifest count is only an assertion and
never an optimization target.

## End-To-End REAL PREFLIGHT Result

The deterministic selector chose one source-valid failed target from each of
the six released source variants. The shared path then:

- loaded 3,316 full-manifest and 1,000 verified safe-projection rows;
- retained 1,077 of 1,328 candidate references after source validation;
- retained all 6/6 selected targets;
- processed 36,125 reference operations and 270 target operations;
- excluded each target and every same-`task_name` reference;
- used support levels `(agent, model, difficulty, category)`,
  `(agent, model, category)`, and `(agent, model)` for 1, 4, and 1 targets;
- invoked release AgentProf for semantic, raw-action, and phase reference and
  target organizations;
- matched every AgentProf stack count exactly to an independent Python count;
- wrote `predictions-pre-label.md`; and
- loaded `incorrect_stages` only afterward and computed terminal metrics.

| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall |
|---|---:|---:|---:|
| semantic | 0.053306 | 0.083333 | 0.670370 |
| raw-action | 0.062097 | 0.083333 | 0.403704 |
| phase | 0.063779 | 0.166667 | 0.666667 |

These six targets contain 270 steps, 12 hidden incorrect steps, and three
zero-positive trajectories. Semantic profiling loses this tiny deterministic
preflight. That sign is recorded but cannot change the fixed hypothesis, RQ,
or paper story and is not treated as scientific evidence.

Primary artifacts:

- `../../../../visexp/out/codetracebench-rq2/real-preflight/report.md`
- `../../../../visexp/out/codetracebench-rq2/real-preflight/predictions-pre-label.md`
- `../../../../visexp/out/codetracebench-rq2/real-preflight/reference-operations.jsonl`
- `../../../../visexp/out/codetracebench-rq2/real-preflight/target-operations.jsonl`

## Integration Repairs Made Before PASS

1. CodeTracer raises on whitespace-only action strings; only whitespace
   emptiness is normalized to `""`, while every non-empty action is preserved.
2. AgentProf lowercases and sanitizes frame values. Per-trajectory exact checks
   use a stable lowercase SHA-256 key instead of raw trajectory IDs.
3. Raw-action baseline keys use the same release-AgentProf `safe_frame`
   normalization in both emitted operations and the independent scorer.
4. AgentProf mismatch diagnostics are concise counter diffs rather than full
   population dumps.

## Decision And Next Step

REAL PREFLIGHT is **PASS**. The source boundary, release-AgentProf path,
matching, pre-label prediction, terminal label join, and primary metric path are
executable on real CodeTraceBench inputs.

The full experiment must not start until independent implementation review
checks this runner against revision 6. The declared frequency-matched control,
2,000 outcome-null trials, and 10,000 task-clustered bootstraps are not yet
implemented; they remain required before the full scientific result can be
reviewed. No paper or canonical story file was changed in this node.
