# Results: direct multi-level annotation vs A2

Status: **FULL RUN INCOMPLETE / INVALID FOR FULL-POPULATION SCORING**

## Pilot gate

The binding first-40 pilot is complete and valid. Direct annotation reaches
B³ F1 `0.752235`
versus same-slice A2
`0.661825`, a point
delta of `+0.090410`. The
paired task-cluster 95% interval is
`[+0.048443,
+0.128938]`.
Boundary F1 is
`0.516616` versus
`0.443570`. The
binding `within 0.03` B³ gate therefore passed and authorized the full run.
Complete pilot details are in `pilot-results.md`.

## Full backend outcome

All 405 trajectories reached terminal backend status. Exactly 404 produced
valid raw marks. Ordinal 53 failed both allowed calls because each response
copied its long session ID without the final `-f7c2004c` suffix. Its semantic
marks otherwise passed the structural checks, but the exact A2 mark contract
requires the session string to match. The first failed response and its one
format retry are preserved under `raw-events/0053-attempt-{1,2}.jsonl`.

The 404 valid outputs cover 17,126/17,148 turns,
20,844/20,866 operations, and
494,533,683/494,862,929 source tokens. The missing trajectory
contains 22 turns,
22 operations, and
329,246 tokens.

## Scientific verdict

The complete-population hypothesis is **not tested**. Per the task
specification and experiment workflow, the 404-trajectory subset was not
packaged, canonicalized, scored, or reported as the full result. No full B³,
boundary, conservation, collision, or pprof claim is authorized. The positive
pilot remains a valid gate result, not a paper result.

```text
run status: incomplete / invalid for full-population scoring
tested hypothesis: inconclusive (complete population not scored)
research value: dependency-only full-run failure record; supporting pilot
paper impact: none
next paper decision: do not promote the pilot or partial population
```

## Validity checks

- all 405 backend trajectories reached terminal status;
- all 404 retained raw-mark files independently pass the fixed response
  validator;
- nine trajectories used the one allowed format retry: eight succeeded and one
  failed;
- no trajectory received a third call;
- the full packager rejected the missing annotation before downstream work;
- no 404-trajectory score or profile was generated.

## Deliverables

- `direct_annotation/`: fixed source-only backend and downstream harness;
- `raw-marks/`: 404 valid raw mark files;
- `raw-events/`: every backend event stream, including both terminal-failure
  attempts;
- `annotation-run-records.jsonl`: complete call, retry, timing, usage, and
  failure record;
- `pilot-results.md` and `pilot/`: valid binding pilot result and raw paths;
- `raw-results.json`: machine-readable terminal disposition;
- `cost-record.md` and `execution-log.md`: complete accounting and commands.
