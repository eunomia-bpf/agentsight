# Step 0071 WRITE consistency review

Timestamp: 2026-07-23T03:12:00-07:00
Verdict: PASS

## Numeric checks

- RQ1 count/token mass in paper: 489 / 4,558,192 — matches current pprof.
- RQ1 authentication subtree: 105 / 2,103,587 and 21.47% / 46.15% — matches
  stock-pprof recomputation.
- RQ2 final automatic MAP: 0.790615 / 0.432392 / 0.259313 — matches all three
  current-binary summaries.
- RQ3 A2 B-cubed and boundary F1: 0.704113 / 0.393916 — matches complete
  scorer output.
- RQ3 recurrence: 0.662740 / 0.265571 — matches the fixed baseline.
- RQ3 name counts: 5,537 to 1,434; 717 to zero adjacent collisions — matches
  the canonicalization report.
- RQ4 union semantic/raw medians: 1.16 / 0.97 seconds — matches 30-run matrix.
- RQ4 union RSS: 465.16 MiB — paper rounds to 465.2 MiB.
- RQ4 throughput and overhead: 23,935 operations/s; 19.6% time and 1.14% RSS —
  matches recomputation.
- RQ4 current A2: 0.79 / 0.81 seconds and at most 307.3 MiB — matches six
  complete runs.

## Terminology and scope checks

- “operation,” “mark,” “canonical identity,” “temporal occurrence,” and
  “source evidence” retain one meaning across design, implementation, and
  evaluation.
- The paper distinguishes automatic Agent marks from deterministic name
  canonicalization.
- RQ2 declared/reference semantic hierarchy remains distinct from the final
  automatic Agent+Evidence candidate.
- “Current binary” names `agentpprof 0.2.37`; no stale JSON-output path is
  described as a product interface.
- The renderer is explicitly paper-only; AgentPProf still emits only pprof.

## Figure checks

- Both case figures are cited before or beside interpretation.
- Captions state population, width, focus, and the intended takeaway.
- The focused Git panel was regenerated from the current profile and is
  byte-identical to the included artifact.
- LLM and tool leaves are present below semantic operations.
- Variable depth is visible; it is not simulated by adding fixed phase fields.

No factual, numeric, terminology, or figure mismatch remains in the changed
paper sections.
