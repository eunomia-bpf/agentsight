# Independent result review

Timestamp: 2026-07-21T02:31:00-07:00
Final decision: PASS after repair and complete rerun

## First review: invalid adapter, experiment not accepted

The first independent review rejected the initial run despite its 676
tool-readable pprof files. It found two blocking adapter errors:

1. Every official trajectory ends in an actionless observation. The adapter
   had converted all 440 such observations into a false `action:unknown →
   result:terminal` operation and assigned each one an artificial token.
2. The claimed exact repeat signature had dropped native target IDs and used
   only action class, accessible object, and URL domain. It therefore marked
   different `Upvote` targets as repeats in a successful
   `visualwebarena.resized.322` trace.

The reviewer also required the report to separate broad operational coverage
from localization evidence and to state accurately that outcome labels select
and pair trajectories before label-free stack construction. The initial run's
metrics were declared invalid and were not retained.

## Minimal repair

The tested hypothesis, workload, stack, pair set, and evaluation statistics did
not change. The adapter was repaired to:

- discard observations without a native action;
- preserve zero reported tokens by omitting only zero-weight token samples;
- define an exact repeat as two adjacent operations with identical complete
  native action, complete URL, and SHA-256 of the pre-action accessibility
  tree;
- correct the reports' leakage and evidence-boundary wording.

The fixed preflight and the entire 125-task/338-pair run were then executed
again from raw official traces.

## Independent fixed-run checks

The reviewer independently verified:

- 440 trajectories, 125 mixed tasks, 338 pairs, and 676 existing pprof files;
- 7,229 real action records, with zero empty actions, `action:unknown` frames,
  or artificial terminal operations;
- the case now contains the official three native actions and 18,716 versus
  22,173 reported tokens, with no artificial token;
- the previous VisualWebArena 322 counterexample now has seven real actions and
  zero false repeats for its different-target `Upvote` sequence;
- aggregate candidate/base conservation for operation and token weights on all
  338 pairs;
- readback of both case pprof files and reproduction of error/conclusion paths
  through ordinary `go tool pprof` filters;
- no success, looping, model, agent, or session outcome field in the 7,229
  stack records;
- byte identity between the retained compact case pprof files and the fixed raw
  run.

The reviewer recomputed all descriptive metrics. Pairwise results matched the
run exactly. Standard trajectory ROC AUC values were 0.751726 for steps,
0.698665 for tokens, 0.506781 for error rate, 0.668660 for exact action-state
repetition, and 0.633060 for non-progress rate. Independently rebuilding 435
looping-consensus trajectories produced repeat-rate ROC AUC 0.766712.

## Scientific interpretation

The fixed result supports the tested hypothesis for the source-verified real
case and supplies broad operational coverage: one standard signed pprof
localizes wrong-object review work, timeout, and `report_infeasible` in the bad
trace against correct-product review work and `send_msg_to_user` in the good
trace, while every planned real pair produces a readable profile.

The scalar scores do not establish a new failure detector and are weaker than
simple step count. The broad run has no gold semantic path, so it does not
measure localization accuracy or universal task-decomposition quality. The 338
pairs also reuse 440 trajectories across 125 tasks and remain descriptive.

Final reviewer judgment:

```text
run status: valid
tested hypothesis: supported for the source-verified real case, with broad operational coverage
research value: supporting
paper impact: additional bounded RQ1 evidence
next paper decision: return to the orchestrator without promoting scalar scores or universal localization claims
```
