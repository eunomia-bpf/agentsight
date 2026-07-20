# Step 0049 Chronology Correction

- correction persisted: 2026-07-20T02:08:00-07:00
- scope: Experiment 003, Experiment 004, and the milestone REVIEW reports
- reason: several reports used file-persistence times as if they were exact
  execution times, which made the causal order appear impossible
- scientific data changed: none

## Evidence Policy

The exact wall-clock time of every inference transition was not retained. This
correction therefore distinguishes three kinds of evidence:

1. explicit stop times written by the running experiment;
2. filesystem persistence times, which establish only that a report existed by
   that time;
3. causal order established by report contents and referenced inputs.

No timestamp is reconstructed more precisely than the retained evidence
supports. The raw outputs, populations, predictions, and scores are unchanged.

## Reconstructed Causal Order

| Order | Event | Retained evidence |
|---:|---|---|
| 1 | Experiment 003 received three serial plan reviews and an approved V2 plan. | plan/review files persisted from 21:37:56 through 21:48:10 |
| 2 | The initial real preflight completed. | `real-preflight.md` persisted at 21:52:44 |
| 3 | Full-run attempt 1 stopped after the unbounded-whitespace failure. | report records stop at 22:11:12; report persisted at 22:19:50 |
| 4 | The compact-output repair was reviewed and rereviewed. | review files persisted from 22:12:43 through 22:22:18 |
| 5 | The V2.2 real preflight completed. | `real-preflight-v2.2.md` persisted at 22:23:21 |
| 6 | Full-run attempt 2 stopped after the cross-field non-empty failure. | report records stop at 22:47:57; report persisted at 22:52:34 |
| 7 | Experiment 004 was proposed to test the V2.3 repair, then its plan was approved. | prompt followed attempt 2; plan and review persisted at 22:57:43 |
| 8 | The V2.3 migrated-cache preflight completed after approval. | exact execution time unknown; its report originally existed before the implementation review and was later edited during this correction |
| 9 | The complete implementation was independently reviewed. | prompt persisted at 23:05:37; review persisted at 23:13:31 |
| 10 | The complete V2.3 population was materialized and scored. | exact completion time unknown; `full-run.md` originally existed before the result-review prompt and was later edited during this correction |
| 11 | Independent result review reconstructed the complete result. | prompt persisted at 23:14:48; review persisted at 23:26:07 |
| 12 | The diagnostic figure was reported. | report persisted at 23:56:32 |
| 13 | Full-paper Grok and Codex reviews, the failed Claude attempt, and the four-node synthesis were produced. | prompt persisted at 01:11:39; exact model completion times were not retained; reports were assembled before this correction |

The current mtimes of `real-preflight-v2.3.md`, `full-run.md`, and the REVIEW
reports reflect this documentation repair and must not be interpreted as their
original execution times.

## Corrected Interpretation

Experiment 003 ended after two invalid but scientifically unscored runs.
Experiment 004 began only after the second failure, approved a strict V2.3
language, completed a real preflight and implementation review, then completed
and scored all 405 trajectories. The independent result review occurred only
after that complete result existed.

The REVIEW gate occurred after the experiment and WRITE material was available.
Its exact per-model timestamps are unknown, so the reports now use persistence
or unknown-time wording instead of asserting false precision.

## Effect On Scientific Conclusions

None. The correction changes provenance language only:

- Experiment 001 remains supported and adopted as a bounded RQ3 mechanism
  improvement.
- Experiment 004 remains a complete contradiction of only the tested Qwen 3B
  transition-policy-plus-contraction hypothesis.
- The paper thesis, four RQs, and positive story remain unchanged.
- The next routed question remains RQ3 hierarchy fidelity.

