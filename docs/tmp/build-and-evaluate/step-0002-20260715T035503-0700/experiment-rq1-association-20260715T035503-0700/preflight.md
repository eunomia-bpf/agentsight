# RQ1 Real Preflight

Status: valid dependency; no paper result

## Attempt 1

The authoritative exporter ran over the actual AgentSight repository and local
2026-07-14 native histories. It completed in 168.01 seconds with 722,456 KiB
peak RSS, producing 145 sessions and 695,961 events. The output contained
Claude and Codex but omitted Gemini because its native schema identifies the
project by `SHA256(cwd)` rather than a literal `cwd`. Repeated Codex usage
updates also produced hundreds of thousands of redundant response rows.

This was a source-path defect, not an oracle or metric failure. The repair added
Gemini project-hash matching, preserved relative Gemini paths, coalesced Codex
usage updates within a prompt, and recognized read/write tool-name families.
The retrieval window, Git semantics, truth, metrics, and gates did not change.

## Attempt 2

The repaired exporter reran the same real repository, native inputs, and local-
time interval. It completed in 58.82 seconds with 218,584 KiB peak RSS. The
privacy-safe artifact contained 149 sessions (22 Claude, 123 Codex, and 4
Gemini), 121,143 normalized events, 117 Git changes, 652 continuous file
lifetimes, and 495 lifetimes surviving to the selected HEAD. The artifact is
63,064,364 bytes and is ignored under `raw/private/`.

This day contained one path-resolved write association row and no candidate in
the frozen retrieval window. The preflight therefore engages ingestion,
lifetime construction, null candidate handling, and endpoint projection, but
does not establish association accuracy or research value.

## Independent source recomputation

- Direct `git log --first-parent --no-merges` over the sampled event/path/window
  also returned zero candidate commits.
- Direct `git cat-file -s HEAD:<sample-path>` matched the exported current blob
  size for a surviving lifetime.
- Direct first-parent Git log counting matched all 17 commits in the artifact's
  audit interval.
- Literal scans found zero occurrences of command/preview/content/edit-body
  keys and zero absolute home paths.

## Completion decision

The second and final permitted preflight attempt is valid. Continue to the
approved controlled and naturalistic full run. Performance and low write-event
yield remain implementation/data risks, not preflight results.
