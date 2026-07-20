# Independent Result Review

## Verdict

**APPROVE.** Must-fix: **0**.

- reviewer: fresh and independent of Step 0055 planning, implementation, and
  execution
- skill explicitly used: `research-experiment-design`
- mode: read-only; no model call or file modification

## Independent Reconstruction

The reviewer ignored evaluator-computed metrics and reconstructed the experiment
from fixed Step 0054 predictions, fixed operation-score rows, and new raw score
and bootstrap artifacts. It retained the complete ordered `task_path` label
tuple, including adjacent duplicates; applied session only as an external
occurrence namespace; and reconstructed adjacent contraction separately as a
secondary diagnostic.

Coverage and joins reproduce exactly:

| Item | Count |
|---|---:|
| sessions | 405 |
| operations | 20,866 |
| adjacent pairs | 20,461 |
| session-local stage occurrences | 2,948 |
| task clusters | 251 |
| OpenHands operations / sessions | 10,030 / 213 |
| SWE-agent operations / sessions | 1,460 / 28 |
| Terminus2 operations / sessions | 7,201 / 93 |
| MiniSWE operations / sessions | 2,175 / 71 |

All prediction, Step 0054, and Step 0055 keys match. Session step IDs are
contiguous, and every materialized operation path and boundary decision matches
the independent construction.

## Independently Recomputed Metrics

| Identity/method | Groups | B³ P | B³ R | B³ F1 | Boundary F1 | Span F1 |
|---|---:|---:|---:|---:|---:|---:|
| hidden frame instance | 13,041 | 0.931958 | 0.333171 | 0.490861 | 0.261643 | 0.032768 |
| **exact complete visible path** | **9,585** | **0.822397** | **0.432771** | **0.567111** | **0.262350** | **0.034995** |
| adjacent-label contraction | 6,290 | 0.741428 | 0.550438 | 0.631815 | 0.264670 | 0.047913 |
| multi-resolution recurrence | 6,018 | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

All seven Step 0054 controls reproduce within numerical tolerance. The exact
visible path gains 0.076250 B-cubed F1 over hidden occurrence identity through
higher recall with the expected precision reduction.

Both independently rebuilt 251-task, 10,000-resample bootstraps match every
stored delta:

| Comparison | Mean delta | 95% interval | Positive fraction |
|---|---:|---:|---:|
| exact visible minus hidden instance | +0.076239 | [+0.060647,+0.092940] | 1.0000 |
| exact visible minus recurrence | -0.096019 | [-0.123890,-0.068765] | 0.0000 |

The construct correction is supported and the fixed online constructor is not
adopted.

## Framework And Folding Checks

| Framework | Hidden | Exact visible | Recurrence | Visible minus recurrence |
|---|---:|---:|---:|---:|
| OpenHands | 0.377918 | 0.469636 | 0.676295 | -0.206659 |
| SWE-agent | 0.271718 | 0.550365 | 0.708893 | -0.158528 |
| Terminus2 | 0.627902 | 0.654087 | 0.605471 | +0.048615 |
| MiniSWE-agent | 0.556650 | 0.615879 | 0.691523 | -0.075644 |

AgentProf's folded-stack implementation joins the complete frame sequence and
performs no adjacent-frame deduplication; pprof and flame-tree construction
likewise traverse every frame. Therefore `task -> install -> install` and
`task -> install` are distinct visible paths.

The reviewer finds 8,757 operations containing at least one adjacent repeated
label and 49,938 repeated-frame positions. Contraction improves the diagnostic
score but is neither standard folding nor proof that same-named nested
responsibilities are interchangeable.

Global behavior counts also reproduce: 9,109 exact paths, 183 seen in multiple
sessions, maximum 31 sessions; adjacent contraction gives 5,890 paths, 132
multi-session paths, maximum 31. These counts show recurring strings only, not
cross-run semantic correctness.

## Claim Boundary And Direction

The result supports exact visible path as the evaluated profile output and
rejects adopting this fixed online Qwen2.5-3B constructor against recurrence.
It does not validate cross-run semantic equality, ancestor topology, variable
depth, label meaning, root canonicalization, or the lower semantic suffix.
Thesis, RQ3, its positive hypothesis, and the intended hierarchy remain
unchanged.

If the branch continues, the only clean next test is the bounded causal
invariant: an exact same-leaf `push` or `replace` is applied as `stay`; every
other mechanism remains fixed. If that complete replay still loses or retains
the phase/no-pop/runaway-depth pathology, close this online 3B branch.
