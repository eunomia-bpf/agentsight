# Automatic annotation cost record

## Configuration

- Backend: `codex-cli 0.145.0`, model `gpt-5.6-sol`
- Instruction: fixed Step 0077 automatic-backend instruction, unchanged,
  followed only by the batch execution scope
- Population: 42 frozen sessions, one deterministic session block per batch
- Passes: one complete first pass; no aggregate-aware revision
- Worker pattern: one isolated preflight worker, then three parallel isolated
  workers over the remaining 41 batches
- Validation: AgentPProf operation-view validation immediately after every
  batch

The backend could write only its batch `annotation.json`. The orchestrator
verified that `trace.jsonl` and `stacks.folded` were unchanged before validation
and that no fourth workspace file was created.

## Complete cost

| Measure | Value |
| --- | ---: |
| Batches completed | 42 / 42 |
| Backend failures or reruns | 0 |
| Summed backend wall time | 7,740.107 s (129.002 min) |
| Three-worker critical-path wall plus preflight | 2,674.314 s (44.572 min) |
| Summed CLI validation wall time | 0.211 s |
| Maximum single-batch backend wall time | 1,028.946 s |
| Reported input tokens | 15,231,328 |
| Reported cached input tokens | 13,112,320 |
| Derived noncached input tokens | 2,119,008 |
| Reported output tokens | 311,097 |
| Reported reasoning-output tokens | 107,830 |
| Final annotations | 1,737 |

The critical path is reconstructed from every measured batch span under the
fixed FIFO three-worker schedule, plus the separately measured preflight. It
excludes the idle setup gap between preflight and the full worker launch.

The 42 frozen records contain 31 distinct native `source_session` strings.
Accordingly, the per-session quantities below are per frozen record/batch, not
estimates from 42 statistically independent agent runs.

## Step 0077 reference

| Quantity | Step 0077 reference | This run |
| --- | ---: | ---: |
| Reported input tokens per session / frozen record | 27,362 | 362,651 |
| Reported cached input tokens per session / frozen record | not retained in the reference | 312,198 |
| Derived noncached input tokens per session / frozen record | not retained in the reference | 50,453 |
| Output tokens per session / frozen record | not stated in the reference | 7,407 |
| Reasoning-output tokens per session / frozen record | not stated in the reference | 2,567 |

This run's reported input counter per record is 13.254x the Step 0077
per-session reference. Because
312,198 of 362,651 input tokens per session are reported as cached, the derived
noncached component is 1.844x the reference. The reference does not expose the
same cache split, so the noncached comparison is informative but not
strictly like-for-like.

The increase is concentrated in the longest sessions. The largest batch
contains 3,899 trace nodes, takes 1,028.946 seconds, and reports 2,788,383
input tokens. The fixed instruction required reading enough complete source
context to annotate every mandatory prompt and responsibility change, rather
than truncating that session.

## Per-batch record

The complete machine-readable source is
`annotation-pass/run-records.jsonl`. Input counts below are the Codex CLI's
reported counters and include the cached-input column.

| Batch | Backend wall (s) | Input | Cached input | Output | Reasoning output | Annotations | Max depth | Warnings |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 01 | 250.109 | 471,946 | 414,976 | 9,415 | 4,232 | 31 | 3 | 1 |
| 02 | 446.488 | 651,161 | 557,568 | 22,368 | 5,131 | 141 | 3 | 4 |
| 03 | 74.380 | 212,080 | 176,384 | 3,249 | 1,305 | 8 | 3 | 0 |
| 04 | 269.293 | 469,709 | 407,296 | 9,817 | 4,881 | 17 | 4 | 2 |
| 05 | 186.285 | 224,355 | 179,712 | 6,985 | 3,691 | 16 | 3 | 1 |
| 06 | 152.135 | 252,685 | 215,040 | 5,247 | 2,454 | 10 | 4 | 0 |
| 07 | 124.617 | 263,410 | 215,552 | 4,575 | 2,331 | 8 | 3 | 1 |
| 08 | 100.904 | 187,918 | 166,144 | 3,570 | 1,609 | 5 | 3 | 0 |
| 09 | 54.223 | 123,044 | 106,240 | 1,940 | 608 | 5 | 3 | 0 |
| 10 | 70.722 | 181,662 | 145,152 | 3,115 | 1,292 | 8 | 3 | 0 |
| 11 | 64.032 | 100,424 | 71,936 | 2,435 | 1,289 | 5 | 3 | 0 |
| 12 | 171.856 | 324,401 | 262,656 | 7,628 | 2,740 | 39 | 3 | 1 |
| 13 | 310.956 | 1,011,511 | 916,480 | 14,075 | 4,016 | 71 | 3 | 4 |
| 14 | 297.882 | 562,803 | 511,488 | 9,197 | 1,723 | 59 | 3 | 5 |
| 15 | 233.243 | 636,063 | 539,904 | 9,313 | 3,921 | 41 | 3 | 3 |
| 16 | 366.248 | 584,448 | 504,320 | 15,962 | 5,177 | 89 | 3 | 13 |
| 17 | 122.257 | 271,984 | 202,240 | 4,743 | 2,526 | 16 | 3 | 2 |
| 18 | 1,028.946 | 2,788,383 | 2,636,032 | 48,582 | 9,577 | 451 | 3 | 14 |
| 19 | 71.837 | 151,080 | 131,584 | 2,629 | 1,097 | 7 | 4 | 0 |
| 20 | 88.780 | 202,244 | 170,240 | 2,602 | 1,075 | 6 | 3 | 0 |
| 21 | 21.004 | 119,821 | 92,160 | 1,134 | 407 | 2 | 2 | 0 |
| 22 | 636.896 | 580,829 | 469,760 | 33,057 | 6,805 | 257 | 3 | 3 |
| 23 | 171.635 | 317,616 | 285,184 | 6,927 | 2,219 | 27 | 2 | 1 |
| 24 | 816.950 | 1,482,565 | 1,168,896 | 25,147 | 9,195 | 298 | 3 | 5 |
| 25 | 159.333 | 251,299 | 206,336 | 6,838 | 3,230 | 25 | 3 | 2 |
| 26 | 125.181 | 161,626 | 122,880 | 4,419 | 2,723 | 10 | 3 | 3 |
| 27 | 81.643 | 199,146 | 179,200 | 3,028 | 1,208 | 4 | 3 | 0 |
| 28 | 121.719 | 253,629 | 219,904 | 3,903 | 1,648 | 5 | 3 | 0 |
| 29 | 54.394 | 121,655 | 93,184 | 1,652 | 740 | 3 | 2 | 0 |
| 30 | 64.379 | 123,859 | 95,232 | 2,224 | 1,026 | 5 | 3 | 0 |
| 31 | 69.117 | 123,771 | 107,264 | 2,426 | 1,388 | 4 | 3 | 0 |
| 32 | 46.970 | 96,994 | 81,920 | 1,497 | 697 | 3 | 2 | 0 |
| 33 | 65.519 | 148,024 | 129,536 | 2,110 | 1,098 | 3 | 2 | 0 |
| 34 | 83.786 | 176,124 | 155,904 | 2,918 | 1,365 | 5 | 3 | 0 |
| 35 | 55.865 | 96,987 | 81,920 | 1,593 | 736 | 4 | 3 | 0 |
| 36 | 50.555 | 98,040 | 69,888 | 1,714 | 829 | 5 | 3 | 0 |
| 37 | 54.549 | 98,169 | 69,632 | 2,006 | 1,047 | 5 | 3 | 0 |
| 38 | 112.430 | 206,462 | 185,344 | 3,419 | 1,650 | 4 | 3 | 0 |
| 39 | 43.936 | 97,519 | 69,888 | 1,527 | 727 | 3 | 2 | 0 |
| 40 | 71.854 | 151,513 | 119,552 | 2,198 | 1,170 | 3 | 2 | 0 |
| 41 | 162.228 | 361,211 | 322,048 | 6,330 | 3,223 | 11 | 3 | 4 |
| 42 | 184.972 | 293,158 | 255,744 | 7,583 | 4,024 | 18 | 4 | 3 |

The warning total is 72, matching the final merged workspace. Warnings are
advisory and did not change coverage, nesting validity, or either profile's
mass.
