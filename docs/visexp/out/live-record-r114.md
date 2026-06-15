# R114 Live Record Suite

Last updated: 2026-06-14
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r114_live_record_suite.py --out docs/visexp/out`
Completeness: ok

This suite wraps real `codex exec` tasks with `agentsight record`, runs concurrent
negative-control processes, exports each SQLite DB, and checks lineage precision
and recall from prompt/tool ancestry to effect rows when present.

Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed.

## Aggregate

- Tasks: 20 ({'lineage_precision_ok': 20})
- Record status: {'ok': 20}; target status: {'completed': 20}; lineage status: {'precision_ok': 20}
- Effects: joined=1273 / 5772 = 22.055%
- Scope accounting: in_scope=1273, out_of_scope=1329
- Precision/recall: precision=100.0%, recall=100.0%
- Negative controls: tasks_observed=20/20, observed=3170, joined=0, statuses={'observed': 20}
- Join methods: {'none': 4499, 'pid_family_time_window': 1273}

## Per Task

| Task | Cat | Record | Target | Lineage | Effects | Joined | Orphans | In scope | Out scope | Precision | Recall | Neg observed | Neg joined | Answer |
|------|-----|--------|--------|---------|--------:|-------:|--------:|---------:|----------:|----------:|-------:|-------------:|-----------:|--------|
| `r114-read-state` | read | ok | completed | precision_ok | 426 | 44 | 382 | 44 | 58 | 100.0% | 100.0% | 324 | 0 | fix B5x identical-fragment tag stability, prepare R122 adequacy labels, then run |
| `r114-read-verdict` | read | ok | completed | precision_ok | 466 | 51 | 415 | 51 | 64 | 100.0% | 100.0% | 351 | 0 | c4=supported |
| `r114-read-related` | read | ok | completed | precision_ok | 90 | 46 | 44 | 46 | 43 | 100.0% | 100.0% | 1 | 0 | SigNoz + Inkeep |
| `r114-rg-baseline` | read | ok | completed | precision_ok | 99 | 49 | 50 | 49 | 49 | 100.0% | 100.0% | 1 | 0 | span_duration_lines=18 |
| `r114-agentflame-readme` | read | ok | completed | precision_ok | 417 | 35 | 382 | 35 | 64 | 100.0% | 100.0% | 318 | 0 | bench |
| `r114-paper-search` | read | ok | completed | precision_ok | 86 | 46 | 40 | 46 | 39 | 100.0% | 100.0% | 1 | 0 | paper_agentflame=yes |
| `r114-json-check` | read | ok | completed | precision_ok | 412 | 48 | 364 | 48 | 62 | 100.0% | 100.0% | 302 | 0 | json_ok=yes |
| `r114-claim-list` | read | ok | completed | precision_ok | 418 | 59 | 359 | 59 | 49 | 100.0% | 100.0% | 310 | 0 | C5 |
| `r114-edit-python-bug` | edit | ok | completed | precision_ok | 569 | 115 | 454 | 115 | 122 | 100.0% | 100.0% | 332 | 0 | tests=passed |
| `r114-edit-doc-note` | edit | ok | completed | precision_ok | 500 | 98 | 402 | 98 | 100 | 100.0% | 100.0% | 302 | 0 | note_updated=yes |
| `r114-test-debug` | test | ok | completed | precision_ok | 236 | 122 | 114 | 122 | 113 | 100.0% | 100.0% | 1 | 0 | unittest=passed |
| `r114-edit-rust-text` | edit | ok | completed | precision_ok | 170 | 94 | 76 | 94 | 75 | 100.0% | 100.0% | 1 | 0 | typo_fixed=yes |
| `r114-dependency-inspect` | dependency | ok | completed | precision_ok | 353 | 39 | 314 | 39 | 66 | 100.0% | 100.0% | 248 | 0 | agentflame-r114-fixture |
| `r114-failure-retry` | failure | ok | completed | precision_ok | 410 | 52 | 358 | 52 | 48 | 100.0% | 100.0% | 310 | 0 | missing_file.py |
| `r114-network-docs` | dependency | ok | completed | precision_ok | 135 | 65 | 70 | 65 | 69 | 100.0% | 100.0% | 1 | 0 | 20 |
| `r114-ablation-read` | read | ok | completed | precision_ok | 109 | 40 | 69 | 40 | 39 | 100.0% | 100.0% | 30 | 0 | .agentsight/agentflame/ablations-r131/summary.json |
| `r114-process-read` | read | ok | completed | precision_ok | 86 | 46 | 40 | 46 | 39 | 100.0% | 100.0% | 1 | 0 | root_pid_refs=24 |
| `r114-write-json` | edit | ok | completed | precision_ok | 174 | 84 | 90 | 84 | 73 | 100.0% | 100.0% | 17 | 0 | result_json=created |
| `r114-fix-shell-script` | test | ok | completed | precision_ok | 540 | 114 | 426 | 114 | 108 | 100.0% | 100.0% | 318 | 0 | check=passed |
| `r114-summary-read` | read | ok | completed | precision_ok | 76 | 26 | 50 | 26 | 49 | 100.0% | 100.0% | 1 | 0 | AgentFlame: semantic attribution of agent system effects |

## Claim Boundary

R114 supports C4 for this fixed task suite: in-scope effects meet the precision/recall threshold and concurrent negative controls were not attributed.
