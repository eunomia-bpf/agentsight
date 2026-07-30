# Iteration Log

## v1: model router plus local refinement

The real 60-turn preflight completed on 2026-07-29.

- FULL: 31,611 provider-token volume, B³ F1 0.7601, boundary F1 0.4800.
- SPLIT v1: 46,722 provider-token volume, B³ F1 0.8367, boundary F1
  0.6316.
- SPLIT/FULL token ratio: 1.478.

The selective evidence improved this one case's scores but failed the cost
hypothesis because two separate `codex exec` calls repeated the backend's large
fixed context. This is a development result, not paper evidence. Its raw cells
and pipeline outputs are retained under names containing
`split-v1-two-call`.

## v2: deterministic selection plus one direct annotation call

The selector remains source-only but is now mechanical, and FULL/SPLIT each
make one annotation call. This directly addresses the measured fixed-overhead
cause while simplifying the algorithm. v2 must pass another real preflight
before the 12-family pilot.

The v2 preflight reduced provider-token volume from 31,611 to 23,918 (24.3%)
while covering all 60 operations. The 12-cluster pilot then reduced tokens from
358,030 to 286,511 (20.0%), with lower token volume in all 12 pairs and no
quality loss under the planned point-estimate gate. An independent result
review passed v2 to confirmation.

## v2 confirmation

The unchanged v2 method ran once on 32 different exact `task_name` clusters
(eight per framework), with no exact session or `task_name` overlap with
preflight or pilot:

- FULL: 984,321 provider tokens;
- SPLIT: 783,121 provider tokens, a ratio of 0.7956 (20.44% lower);
- B³ F1: 0.7320 FULL versus 0.7580 SPLIT;
- adjacent-boundary F1: 0.4294 FULL versus 0.4533 SPLIT;
- coverage: 1,639/1,639 operations in both arms.

The task-cluster bootstrap 95% intervals were `[0.7339, 0.8628]` for the token
ratio, `[0.0049, 0.0486]` for the B³ delta, and
`[-0.0184, 0.0676]` for the boundary delta. All planned confirmation gates
passed. Both arms made 33 calls, including one format retry per arm; every
attempt's input and output tokens are included.

An independent final reviewer returned PASS for an RQ4 supporting result. The
paper claim is limited to provider token volume and non-inferior annotation
quality on these exact task-name clusters. It is not a dollar-cost or latency
claim, does not imply project-level independence, and does not generalize
beyond this model/backend and historically studied benchmark.
