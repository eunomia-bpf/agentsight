# Real Preflight Report

**Timestamp:** 2026-07-23T20:39:00-07:00
**Status:** PASS; authorize full run
**Paper result:** no

## Command

The exact approved `preflight` command in `experiment-plan.md` was run with the
new scorer after Python compilation.

## Checks

| Check | Result |
|---|---:|
| Follow-on sessions | 364 |
| Excluded initial sessions | 41 |
| Follow-on operations | 15,116 |
| Follow-on adjacent pairs | 14,752 |
| Task-name clusters | 238 |
| Operation/session join | complete |
| Pair/session join | complete |
| Initial/follow-on overlap | zero |
| OpenHands sessions | 202 |
| mini-SWE-agent sessions | 71 |
| Terminus2 sessions | 65 |
| SWE-agent sessions | 26 |
| Complete candidate/baseline/reference fields | pass |
| Unique operation and pair keys | pass |

The manifest population, current A2 score rows, and current baseline rows join
exactly. No target metric was retained as paper evidence during preflight.

## Decision

The implementation can execute the approved complete experiment without
changing the method, population, or inputs. Proceed to the 10,000-resample full
run.
