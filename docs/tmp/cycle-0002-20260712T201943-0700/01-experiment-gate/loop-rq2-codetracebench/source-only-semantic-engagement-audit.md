# Source-Only Semantic Engagement Audit

**Started:** 2026-07-12T21:08:00-07:00  
**Completed:** 2026-07-12T21:12:32-07:00  
**Cycle/gate:** cycle 0002 / EXPERIMENT  
**Parent:** `experiment-plan.md` revision 2  
**Status:** complete; supplies revision-3 frozen mapping

## Question

Can the planned target-blind semantic mapping execute under the runner's regex
engine and engage all four real CodeTraceBench framework formats before any
hidden label is read?

Round-3 review found that revision 2 used POSIX whitespace classes unsupported
by Python `re` and omitted SWE-agent's released `str_replace_editor` syntax.
That would collapse ordinary SWE-agent inspection and editing into the fallback
`explore -> execute` stack.

## Inputs And Information Boundary

The audit uses the four official raw archives downloaded during source
selection, one per framework. Selection used framework, outcome, manifest order,
and length only; it did not use incorrect/unuseful step IDs. The audit extracts
raw actions with:

- official `MinisweParser.parse`;
- official `OpenHandsParser.parse`;
- official `Terminus2Parser.parse`;
- a thin read of the released SWE-agent `.traj` `trajectory[].action` field.

It applies official CodeTracer commit
`2d302191dd07e7c0c2da6f7a5e9451c7cbb62d34`'s
`ClassificationStore.classify` with an empty store and no LLM. No manifest
annotation field or generated annotation file is opened.

## Revision-3 Repair

All action-kind rules now explicitly use Python 3 `re` with `re.IGNORECASE` and
valid `\s`/noncapturing-group syntax. Two target-blind SWE-agent rules precede
the generic fallbacks:

```text
str_replace_editor\s+view
    -> inspect

str_replace_editor\s+(?:str_replace|create|insert|undo_edit)
    -> edit
```

The full ordered rule table is authoritative in `experiment-plan.md`. This
audit does not create a second mapping contract.

## Real Source Engagement

| Framework | Raw steps | Action kinds exercised | Distinct semantic stacks |
|---|---:|---|---:|
| MiniSWE | 69 | inspect, edit, version-control, execute, search, install | 10 |
| OpenHands | 213 | inspect, execute, search, install | 5 |
| Terminus2 | 141 | inspect, search, execute, other, edit, version-control | 9 |
| SWE-agent | 123 | inspect, search, edit, execute, test, other | 9 |

SWE-agent specifically maps 33 steps to `inspect`, 12 to `edit`, 40 to
`search`, 15 to `test`, 20 to `execute`, and three empty actions to `other`.
The official CodeTracer phase classifier still assigns many SWE-agent tool
actions to `explore`; that is the released phase baseline's behavior, while the
second semantic frame recovers the visible action distinction without labels.

No framework collapses entirely to fallback and every framework exercises at
least four action kinds and five semantic stacks in its real source sample.
Preflight must reproduce a per-framework coverage table from its selected raw
archives. Later full execution reports coverage over all raw-available rows; it
cannot modify the frozen mapping in response.

This audit also finds that the seed parsers' grouping unit is not always the
benchmark step unit: MiniSWE emits 69 records for a 73-step manifest row,
OpenHands 213 for 217, and Terminus2 141 for 327; SWE-agent is exactly 123/123.
For Terminus2, the 141 episode responses contain exactly 327 individual
`commands[]`, demonstrating that the seed parser merges benchmark steps. This
does not authorize annotation access. REAL PREFLIGHT must implement thin
source-schema adapters that preserve/split visible raw actions and achieve the
declared step count before hidden step IDs are loaded.

## Decision

The revision-2 engine mismatch and SWE-agent non-engagement are closed by the
revision-3 mapping. This is source-schema adaptation before label join, not
target-label tuning. The fixed RQ, tested hypothesis, and paper story remain
unchanged.
