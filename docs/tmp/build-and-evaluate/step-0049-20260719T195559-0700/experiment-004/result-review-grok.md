# Experiment 004 Independent Result Review — Grok

**Reviewer:** Grok 4.5, read-only  
**Verdict:** **PASS**  
**Registered scientific outcome:** tested mechanism hypothesis contradicted  
**Must-fix:** None  
**Release candidate:** Experiment 001 multi-resolution recurrence remains

## Independent reconstruction

The reviewer rebuilt the result from raw predictions, contracted assignments,
operation assignments, pair decisions, and task-cluster bootstrap deltas rather
than trusting summary booleans.

- Population: 405 sessions, 20,866 operations, 20,461 adjacent pairs, 2,948
  official stages, 251 task clusters, and four frameworks. Coverage was exact;
  rebuilt pair fields had zero mismatches.
- Contraction: 20,857 generated frames, 1,678 retained frames, 19,179
  contracted singletons, 1,690 effective leaf groups, and 20 root-assigned
  operations. Reconstructed leaves had zero mismatches with both contracted
  predictions and score assignments.
- Candidate ordinary B-cubed: precision 0.290890, recall 0.853010, F1
  0.433835. Candidate boundary F1: 0.109949.
- Registered multi-resolution comparator: B-cubed F1 0.662740 and boundary F1
  0.265571. All stored metric deltas matched exactly.
- Candidate minus comparator B-cubed F1 by framework: OpenHands −0.173921,
  SWE-agent −0.262172, Terminus2 −0.320564, and mini-SWE-agent −0.218667.
- Independently reconstructed 10,000-resample task-cluster bootstrap: mean
  −0.228651, median −0.228744, 95% interval [−0.246012, −0.210910], positive
  fraction 0.0, and zero difference from stored raw deltas.

## Interpretation audit

The registered `contradicted` outcome is correct. It rejects only the fixed
Qwen2.5-3B transition policy plus immutable-root/support-at-least-two
contraction as a better CodeTraceBench partition. It does not answer the whole
RQ3, invalidate variable-depth operation stacks, alter the thesis “Agent
observability needs profiling, not only debugging,” or alter the four RQs.

Experiment 004 must remain in research provenance and must not become a paper
negative result. Experiment 001 remains the release mechanism because its
independent result was `SUPPORTED / ADOPT` and it outperforms the current
constructor with a wholly positive bootstrap interval and non-negative effects
in all four frameworks.

## Bounded decision

Close Experiment 004 as complete and contradicted; retain Experiment 001 as the
release candidate. No new benchmark, metric, weaker story, or mandatory
follow-on experiment is warranted by this result review.

