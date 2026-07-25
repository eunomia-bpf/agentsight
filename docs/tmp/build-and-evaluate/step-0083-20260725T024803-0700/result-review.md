# Step 0083 result review (root disposition)

Timestamp: 2026-07-25T06:20:00-07:00
Root disposition: VALID EXECUTION; hypothesis 2 NOT replicated; index study
papered with TraceElephant scope only.

## Execution validity

All three conditions completed the full 400-query HINTBench population with
the opencode/GLM reader (sequential conditions, resume, 0 fallback-scored
queries, 1 benign retry in full/raw each). Leakage spot-check: 0 hits in 12
sampled responses; reader jail remained empty. Kimi partial responses set
aside unscored. MAPs: full-trace 0.623, raw skeleton 0.555, semantic
skeleton 0.527, stored Direct+AgentProf 0.517, stored Direct-only 0.411.

## Hypothesis outcomes

1. Ladder direction replicates: full-trace > skeleton conditions >
   Direct+AgentProf > Direct-only.
2. Content-efficiency does NOT replicate: semantic opens slightly less
   content than raw (+0.0143, significant but small; 24.3% vs 25.8%), while
   raw reaches significantly higher MAP (semantic-minus-raw -0.0273, CI
   entirely negative). Raw dominates both axes on this workload.

## Disposition

- The paper's profile-guided reading study is scoped to the complete
  TraceElephant workload (steps 0079-0081, grok reader), where the ladder
  and the semantic content-efficiency effect are complete, positive, and
  independently verified. No cross-workload reader-study sentence.
- No selective reporting from this step: neither the HINT ladder nor the
  HINT semantic-vs-raw comparison enters the paper, because using one half
  of one experiment while omitting the other half is not honest scoping.
- Cross-workload pooling is additionally confounded by the forced reader
  change (grok exhausted; GLM here), reinforcing the single-workload scope.
- AgentProcessBench extension cancelled: with the cross-workload claim
  closed, further reader-study quota spend has no paper value.
- Future iteration recorded for the research log: HINT's raw identities are
  more discriminative than its current semantic annotation; improving the
  semantic naming there is an algorithm-improvement lever, not a paper task
  now.
