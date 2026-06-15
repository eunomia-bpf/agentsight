# R114 Lineage Analysis

Last updated: 2026-06-14
Source: `docs/visexp/out/live-record-r114.json`

## Gate Summary

- Tasks: 20 target_statuses={'completed': 20}
- In-scope effects: 1273; precision=100.0%; recall=100.0%
- Negative controls: tasks_observed=20/20, observed=3170, joined=0
- Raw join: 1273 / 5772 = 22.055%
- Redaction: {'files_scanned': 6, 'home_path_occurrences': 0, 'secret_pattern_occurrences': 0, 'status': 'ok'}

## Child Depth

| Depth from related agent pid | Joined effects |
|---:|---:|
| 0 | 95 |
| 1 | 688 |
| 2 | 447 |
| 3 | 43 |

## Joined Process Commands

| Process | Count |
|---|---:|
| `getopt` | 252 |
| `lsb_release` | 249 |
| `git` | 238 |
| `getconf` | 186 |
| `bwrap` | 166 |
| `codex` | 95 |
| `codex-linux-san` | 50 |
| `git-remote-http` | 25 |
| `true` | 12 |

## Joined Effect Targets

| Target group | Count |
|---|---:|
| `usr/bin` | 531 |
| `exit code 0 (0ms)` | 257 |
| `$HOME` | 100 |
| `exit code 0 (1ms)` | 43 |
| `usr/lib` | 40 |
| `exit code 128 (0ms)` | 27 |
| `exit code 0 (4ms)` | 23 |
| `exit code 0 (8ms)` | 20 |
| `exit code 0 (6ms)` | 19 |
| `exit code 0 (7ms)` | 17 |

## Joined Effects

| Effect | Count |
|---|---:|
| `process.exec` | 611 |
| `process.exit` | 585 |
| `file.write` | 77 |

## Out-of-Scope Targets

| Target group | Count |
|---|---:|
| `usr/bin` | 582 |
| `exit code 0 (0ms)` | 450 |
| `exit code 0 (1ms)` | 99 |
| `dev/tty0` | 38 |
| `dev/console` | 38 |
| `$HOME` | 20 |
| `dev/tty` | 19 |
| `exit code 1 (0ms)` | 16 |
| `exit code 0` | 10 |
| `exit code 0 (221ms)` | 7 |

## Out-of-Scope Processes

| Process | Count |
|---|---:|
| `tr` | 630 |
| `cut` | 424 |
| `clear_console` | 133 |
| `bwrap` | 36 |
| `node` | 30 |
| `bash` | 29 |
| `python3` | 29 |
| `locale-check` | 8 |
| `locale` | 8 |
| `true` | 2 |
