# Experiment 001 REAL PREFLIGHT — Complete Causal v7

- completed: 2026-07-20T03:49:49-07:00
- status: **PASS; proceed to the registered full run**
- algorithm: `task-rooted-causal-stage-alignment-v7`
- external output: `.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/preflight/`
- stage manifest opened: **no**
- scorer run: **no**

## Scope And Coverage

The final preflight reconstructed all 405 public CodeTraceBench source archives
and verified the complete 20,866-operation population without opening human
stages. It then completed one selected trajectory per framework:

| Framework | Operations | Plan items | Candidate boundary rate | Plan-free boundary rate |
|---|---:|---:|---:|---:|
| mini-SWE-agent | 22 | 5 | 0.380952 | 0.904762 |
| OpenHands | 72 | 7 | 0.169014 | 1.000000 |
| SWE-agent | 24 | 6 | 0.260870 | 1.000000 |
| Terminus2 | 43 | 3 | 0.119048 | 0.952381 |
| **Pooled** | **161** | mean 5.25 | **0.197452** | **0.974522** |

All 161 operations received exactly one candidate plan index and one plan-free
stage instance. The run made 326 model calls including four planners. The
maximum actual prompt length was 3,310 tokens, below the registered 8,192-token
limit. The retained model hash, exact request evidence, outputs, usage, and
transport attempts are present in four per-session caches.

## Source-Only Scientific Check

The causal candidate no longer has the old one-operation fragmentation failure.
Its four boundary rates range from 0.119 to 0.381, compared with 0.905 to 1.000
for the matched plan-free 3B policy. This is not a score against human stages;
it only establishes that the fixed task plan produces a materially different,
non-singleton state trajectory worth evaluating on the complete population.

Example retained plans include:

- `analyze codebase for object detection -> create script to reproduce object
  detection issue -> edit source code to fix object detection -> verify fix
  works with script -> test edge cases for object detection fix`;
- `design primers -> verify primers -> assemble primers`;
- `explore repository structure -> create reproduce script -> edit source code
  -> rerun reproduce script -> confirm error fixed -> think about edgecases`.

## Label Audit And Interpretation Boundary

The candidate plans contain one system-detail violation among 21 normalized
plan items (`test with maze_1.txt`). The plan-free arm contains 14 violating
switch labels. All are the first syntax-valid outputs, retained without retry or
rewriting. No exact duplicate plan item occurred in these four final caches.

These counts do not authorize generated-name accuracy. CodeTraceBench supplies
only unlabeled human workflow-stage intervals, so the full run tests span
fidelity. Candidate label violations will remain visible as a separate audit of
the larger task-semantic hierarchy contract.

## Isolation Checks

- Candidate and plan-free arms share byte-identical task and current-operation
  evidence before their algorithm-specific plan/state suffixes.
- Each operation sees only the initial task, current action, and preceding
  observation; no future operation or current result is visible.
- Visible operation fields are exactly `step`, `action_kind`, `raw_action_key`,
  `source_action`, and `preceding_observation`.
- Human stage ranges, stage count, scorer outputs, solved state, and paper
  weights remain unopened.
- No output was selected for semantic quality; raw semantic violations are
  retained and counted.

The preflight therefore passes implementation, coverage, isolation, context,
and non-degeneracy checks. It does not evaluate or preview the registered
primary, secondary, or bootstrap outcomes.
