# Task spec: hierarchical vs flat semantic skeleton, one reader family

Autonomous agent in /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Never write outside the repository (no /tmp). Deliverables
in THIS directory only.

## Hypothesis (the review's "why hierarchy" question)

With the reader family held fixed, the HIERARCHICAL semantic skeleton
directs a reader to responsible operations at least as well as a FLAT
skeleton of the same leaf tags, while opening less source content — i.e.,
the nesting itself carries navigation value beyond the names.

## Setup (mirror step 0080's two-stage protocol exactly, except the arms)

- Population: the complete 220 target-bearing TraceElephant queries; reuse
  step 0080's frozen inputs and provenance
  (docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/).
- Reader for BOTH arms: opencode CLI (GLM), run from an empty jail
  directory with the instruction to answer directly in strict JSON, no
  tools (exactly the step-0083 addendum-002 recipe). Both arms same
  flags, one format retry, deterministic fallbacks, sequential arms with
  resume.
- Arm H (hierarchical): stage-1 skeleton = full semantic paths grouped by
  path (as in step 0080), select <=5 groups; stage 2 opens selected
  groups' evidence.
- Arm F (flat): stage-1 skeleton = the SAME operations grouped by leaf
  tag only, parent paths stripped (pure flat tag list); same <=5-group
  budget; stage 2 identical.
- Score: sklearn non-interpolated AP -> MAP over 220; content-opened
  fraction; paired 10,000-draw trajectory-cluster bootstrap between arms
  (document seed). Also report index-hit rate per arm.
- PILOT: 40 queries per arm, gate: proceed to full 220 only if the
  harness runs clean (parse-failure rate < 10%); this gate is operational,
  not score-based, because both arms are new conditions.

## Deliverables

pilot note inside execution-log.md, packets-*/, raw-responses-*/,
raw-results.json, results.md (hypothesis verdict, paired deltas, costs),
execution-log.md.
