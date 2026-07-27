# Pilot results: frozen direct backend on OSWorld-Human

Status: **COMPLETE**

Selection: the first 40 session IDs in lexicographically sorted order.

## Same-slice metrics and gate

| Method | Boundary P | Boundary R | Boundary F1 | B³ P | B³ R | B³ F1 |
|---|---:|---:|---:|---:|---:|---:|
| Direct multi-level | 0.487179 | 0.133803 | 0.209945 | 0.521693 | 0.886352 | 0.656803 |
| Supervised OOF | 0.639175 | 0.873239 | 0.738095 | 0.933961 | 0.717532 | 0.811565 |
| Reference-calibrated | 0.460145 | 0.894366 | 0.607656 | 0.955193 | 0.553549 | 0.700910 |
| Label-free recurrence | 0.464945 | 0.887324 | 0.610169 | 0.948241 | 0.558881 | 0.703266 |
| Always-boundary | 0.396648 | 1.000000 | 0.568000 | 1.000000 | 0.457286 | 0.627586 |

Direct minus label-free recurrence B³ F1: `-0.046464`; paired session-cluster 95% interval `[-0.180038, +0.084110]`.

Direct minus label-free recurrence boundary F1 paired session-cluster 95% interval: `[-0.536288, -0.267644]`.

Binding gate (`direct B³ F1 >= recurrence-on-slice B³ F1 - 0.05`): **PASS**.

The full 287-session run is authorized.

## Cost and validity

- Codex calls: 40 (0 format retries).
- Summed backend wall: 418.635 s.
- Active backend wall: 110.450 s.
- Usage counters: `{"cache_write_input_tokens": 0, "cached_input_tokens": 184320, "input_tokens": 752427, "output_tokens": 9249, "reasoning_output_tokens": 6047}`.
- Coverage: 40 sessions, 398 operations, 358 adjacent pairs.
- Marks: 79; path depths: `{"1": 21, "2": 47, "3": 10, "4": 1}`.
- Validity: **PASS**.

Raw marks, parsed responses, complete Codex JSON event streams, score rows, bootstrap draws, and machine-readable results are retained in this experiment directory.
