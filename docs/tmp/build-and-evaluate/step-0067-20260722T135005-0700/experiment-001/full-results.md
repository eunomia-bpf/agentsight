# Full result: automatic Agent operation marks

Timestamp: 2026-07-22T15:53:45-07:00
Status: complete and independently reviewed for CodeTrace structure fidelity,
the 41-session long-horizon product case, the fixed-input cost supplement, and
the retained 338-pair differential case; RQ2 remains in progress

## Tested result

Automatic Codex subagents received source-only packets for all 405
CodeTraceBench sessions. They emitted 5,901 sparse complete-path marks over
17,148 source-native turns and all 20,866 operations. No prompt requested a
target depth. Observed semantic-path depth is one for 200 marks, two for 5,608,
and three for 93. The assembled inputs conserve exactly 20,866 operation
counts and 494,862,929 provider-reported tokens.

The constructor output was complete before official stages were opened. After
scoring, one product replay issue was found: 17 independently generated labels
differed only by case and collided under pprof's case-insensitive frame
normalization. The source-only assembler now case-folds semantic labels before
assigning IDs. This changed 5,554 names to 5,537 names but changed no mark,
occurrence partition, metric, or resource weight. Both completed pprofs then
loaded in stock `go tool pprof`.

## Standard flat-partition result

The primary metric is ordinary unweighted operation-level B-cubed. Exact
adjacent-boundary precision, recall, and F1 are secondary. The `native_turn`
row groups operations by their source-native turn and remains a diagnostic
rather than a planned baseline. N0 uses the source fields actually available
on every operation: `phase -> action_kind -> raw_action_key`. It contracts only
adjacent identical complete paths; task/session ancestry is implicit in its
session-qualified occurrence ID. This dataset does not expose separate object
or result fields.

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 |
|---|---:|---:|---:|---:|---:|---:|
| source-native turn (diagnostic) | 0.983154 | 0.221199 | 0.361145 | 0.141910 | 0.934330 | 0.246396 |
| native tree (N0) | 0.974547 | 0.248903 | 0.396530 | 0.151090 | 0.915454 | 0.259373 |
| multi-resolution recurrence (N1) | 0.782026 | 0.575029 | 0.662740 | 0.192945 | 0.425875 | 0.265571 |
| automatic Agent marks (A0) | 0.841742 | 0.599076 | **0.699974** | 0.284571 | 0.615022 | **0.389103** |

The automatic Agent improves B-cubed F1 over recurrence by 0.0372. A paired
10,000-resample bootstrap over 251 task clusters gives mean delta 0.0370 and a
95% interval `[0.0170, 0.0569]`. Boundary F1 improves by 0.1235. The tested
hypothesis is therefore supported for flat workflow partition and boundary
fidelity on this complete population.

The result is heterogeneous. Relative to recurrence, Agent B-cubed F1 changes
by +0.1204 on Terminus2, +0.0063 on OpenHands, -0.0207 on SWE-agent, and
-0.0397 on mini-SWE-agent. Across 251 tasks it wins on 140 and loses on 111.
It also remains oversegmented: 5,901 predicted occurrences versus 2,948
official stages, with 3,932 boundary false positives and boundary precision
0.2846. The supported conclusion is that A0 is the better adopted constructor
on this population, not that it universally dominates or has recovered the
true nested hierarchy.

Official flat stages score only the leaf partition induced by complete visible
operation paths. They do not score nested topology, semantic-name accuracy,
cross-session name equivalence, localization utility, or construction cost.
Those properties require their predeclared separate evaluations.

## Source-native hierarchy and resource widths

The evidence model starts from
`project -> agent -> source_session -> prompt -> LLM call -> tool call`.
Automatic marks insert a variable-depth semantic `operation` path while the
source IDs remain pprof labels. A source-specific view may retain all native
frames. A cross-session population view omits high-cardinality
session/prompt/call frames from the function stack so equal semantic paths can
fold, while retaining `source_session`, `call_id`, and `evidence_id` labels for
drilldown.

One profile width represents one additive measure. The same marks successfully
produce operation-count and token-count pprofs, with exact masses 20,866 and
494,862,929. The code also admits duration, file, and network weighted
normalized inputs by carrying zero-weight source operations through mark
propagation and removing them before folding. This experiment directly
validated only operation and token widths; it does not claim empirical time,
file-read/write, or network results.

## Long-horizon product case

The fixed top-decile long-horizon subset contains 41 sessions, 3,146 turns,
5,750 operations, and 117,303,194 tokens. It has 565 sparse marks with observed
semantic depth one for 14 marks, two for 468, and three for 83. The complete
overview is valid but too dense for a paper panel, so the accepted stock-pprof
views focus all sessions belonging to repeated real task families rather than
one favorable trace.

### Git deployment diagnosis

The three `git-multibranch` sessions used OpenHands/Claude,
OpenHands/DeepSeek, and Terminus2/DeepSeek. Terminus2 contributes 275/489
operations (56.24%) but only 609,801/4,558,192 tokens (13.38%). The two
OpenHands runs contribute 214/489 operations (43.76%) but 3,948,391 tokens
(86.62%). Switching only the pprof width therefore exposes a cost distinction
that action counts hide.

Within OpenHands, `diagnose rejected SSH password authentication` accounts for
105 operations (21.47%) but 2,103,587 tokens (46.15% of the three-session task
family). Source marks show one run returning after a key-authentication control
and the other returning after both a key control and an HTTP fallback. All
three sessions validate substitutes, but none establishes the requested
password-authenticated `git@localhost` path. The profile answers a real user
question: why three attempts were costly although the requested deployment was
not demonstrated. The static flame graph locates aggregate cost; source-mark
drilldown, not left-to-right flame-graph order, establishes temporal returns
and the unsupported terminal conclusion.

### Other actionable paths

The long-horizon profile also surfaces 134 operations and 8,031,679 tokens in
ad-hoc password guessing, 75 operations and 2,883,364 tokens recovering a
stuck QEMU terminal after repeated boot failure, and 75 operations and
2,526,810 tokens in a redesign/benchmark loop with no candidate satisfying all
thresholds. These are diagnostic findings, not outcome-causality claims.

## Cross-session naming boundary

The complete flat-partition score uses a fresh contiguous occurrence identity
for every mark, so it does not depend on equal text names. The full pprof has a
separate open-vocabulary aggregation issue: 102 of 251 task families contain
multiple sessions, but only 12 currently share exactly one automatically
generated root phrase. Ninety have two to four near-synonymous roots. Five
case-study roots and one SSH child label were reconciled source-only; therefore
the Git case is a valid aggregate, but the full 405-session profile is not yet
evidence of universal automatic cross-session name equivalence.

## RQ4 fixed-input construction supplement

The primary RQ4 scaling evidence remains the independently reviewed Step 0005
run over four complete public workloads and their 27,765-operation union. To
verify the current product path, release AgentPProf also replayed the fixed
20,866-operation A0 input three times for each accepted width. Operation-width
construction took 0.62/0.62/0.62 seconds (median 0.62) with largest peak RSS
314,032 KiB (306.67 MiB). Token-width construction took 0.63/0.65/0.64 seconds
(median 0.64) with largest peak RSS 314,140 KiB (306.78 MiB). Stock pprof
recovered exact masses 20,866 and 494,862,929.

Independent review issued PASS for the scoped fixed-input construction claim.
Automatic-subagent elapsed time and provider/model usage are unavailable and
are not estimated. The result does not measure capture, source adaptation,
automatic annotation, model calls, or live-agent overhead. Exact commands and
all six observations are in `a0-cost-supplement.md`.

## Retained aggregate differential case

The second case reuses the complete AgentRewardBench population rather than
running another constructor: 440 real trajectories in 125 mixed-outcome tasks
form 338 pair occurrences. Their signed operation profile contains 7,366
bad-side and 3,780 good-side source operations. Exact stack cancellation leaves
7,103 positive bad-only/excess occurrences and 3,517 negative
good-only/excess occurrences over 4,140 nonzero stacks.

Independent reconstruction matches the previously fixed path results:
`progress` +1,825, `repeated` +1,261, repeated click/no-op/scroll
+639/+356/+277, `stopped` +92, `terminal` -92, `conclusion` -67, and
`send_msg_to_user` -100. The profile therefore answers what kind of work is in
excess or missing across all eligible failed/successful same-task comparisons;
one VisualWebArena pair remains only a source drilldown, not the case study.

The same 338 pairs were rematerialized without changing their semantic stack or
weights so each pprof sample now carries `agent`, `source_session`, and
per-step `evidence_id` labels. The release command is generated by
`script/agentreward_diff_pprof_eval.py --aggregate-only`; the raw execution is
under `.agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/`.
The canonical standard profile is
`docs/visexp/out/agentreward-diff-pprof-v1/agentreward-338-pairs-bad-minus-good.operations.pb.gz`
with SHA-256
`0d6a7e80fbc805d374ad6bd4b668241584150a317049a45b4d0045f473b7495d`.
Stock `go tool pprof -top`, `-tree`, and `-tags` read it; all old top values are
identical and source drilldown is now internal to the pprof.

The root opened this exact profile in Go pprof's stock `/ui/flamegraph` view.
The focused `result:repeated` screenshot shows 1,485 bad-side versus 224
good-side occurrences and retains six semantic levels down to the result. The
focused `result:terminal|result:conclusion|action:send_msg_to_user` screenshot
reverses direction, with 373 good-side versus 183 bad-side occurrences. The
screenshots are retained beside the profile as paper/inspection derivatives;
they are not an AgentPProf output format.

This supports pair-occurrence-weighted differential path localization, not
causal diagnosis, automatic classification, A0 accuracy, nested hierarchy,
semantic-name fidelity, or measured human utility.

## Decision and remaining matrix work

The independently reviewed CodeTrace result is valid and supports adopting A0
for the current constructor. It routes to RQ3 as additional flat
partition/structure-fidelity evidence; the operation/token and differential
cases supply bounded RQ1/RQ2 product evidence. RQ4 replay and both product cases
are complete. Remaining predeclared work is the complete RQ2 localization
workloads. The paper may use the accepted Git and differential figures and the
standard accuracy result only with the heterogeneity, oversegmentation, metric,
naming, and claim boundaries above.
