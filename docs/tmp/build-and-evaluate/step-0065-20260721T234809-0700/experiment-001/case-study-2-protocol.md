# Case-study protocol 2: aggregate bad-good differential profile

Timestamp: 2026-07-22T02:10:00-07:00
Status: fixed for collection-level interpretation

## Scope

This case uses the complete fixed AgentRewardBench population from Step 0063:
440 real consensus-labeled trajectories across 125 tasks with at least one
successful and one unsuccessful run. The population yields 338 complete
bad-good pairs: 24 pair occurrences over 7 AssistantBench tasks, 102 over 51
VisualWebArena tasks, 144 over 46 WebArena tasks, and 68 over 21 WorkArena
tasks. The 202 distinct successful and 238 distinct unsuccessful sessions are
reused across pairs when a task has multiple runs.

All 338 unsuccessful members are aggregated as the candidate side and all 338
successful members as the base side in one signed operation-count pprof.
Therefore the profile is pair-occurrence weighted: it contains 7,366 bad-side
and 3,780 good-side operation occurrences, not 11,146 distinct source
operations. This case is a many-session collection analysis. One pair may be
opened only to trace a collection-level path back to source evidence; no single
pair is the case study.

The protocol was written after complete-run validation and aggregate pprof
readback plus an initial `top` sanity query, and before paper prose and
representative-source drilldown. It is an exploratory fixed case protocol, not
a blind preregistration.

## Fixed user questions

1. **Collection-level excess work.** Across all 338 pairs, which operation
   results and actions occur more on unsuccessful trajectories, and which occur
   more on successful trajectories?
2. **Repetition and failure concentration.** Do exact repeated-state paths,
   stopped paths, and concrete tool errors accumulate on the unsuccessful side
   rather than disappearing inside a scalar trace score?
3. **Completion paths.** Do terminal, conclusion, and user-reporting paths
   accumulate on the successful side, and can the profile retain their child
   evidence rather than only reporting a success label?
4. **Value beyond a scalar.** Given that simple step count is the strongest
   tested scalar discriminator, what additional failure families and source
   paths does the aggregate differential profile expose for diagnosis?

## Evidence and interpretation rules

- Use the one aggregate `.pb.gz` and stock `go tool pprof` queries. The 676
  already validated pair profiles remain source drilldowns, not separate case
  studies.
- Positive values mean bad-only or bad-side excess operation occurrences;
  negative values mean good-only or good-side excess occurrences. Percentages
  shown by pprof use total absolute signed mass and must not be read as a
  probability or success rate.
- Report pair-occurrence weighting and the reuse of 440 trajectories explicitly.
- AgentRewardBench provides independent success and looping labels, but no gold
  semantic hierarchy. The case can demonstrate broad differential profiling
  and diagnostic path exposure; it cannot establish semantic-stack accuracy or
  causality.
- The hidden outcome labels select and pair trajectories. They are absent from
  stack frames and do not label an individual operation as erroneous.
- Retain all 338 pairs. Do not select a benchmark, model, or favorable pair as
  the collection conclusion.

## Planned queries

1. Whole-profile `top` and `tree`.
2. Focus on repeated, stopped, terminal, conclusion, and user-reporting paths.
3. Focus on the largest concrete click, fill, selection, and missing-element
   error families.
4. Use one or more pair profiles only to recover source context for a path
   already found in the aggregate profile.
