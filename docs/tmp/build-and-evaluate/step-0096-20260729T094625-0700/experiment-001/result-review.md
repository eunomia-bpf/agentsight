# Independent Result Review

## Verdict

PASS as supporting evidence for RQ4.

## Evidence checked

- Confirmation contains 32 unique sessions and 32 unique exact `task_name`
  clusters, balanced at eight per framework. Exact session and `task_name`
  overlap with preflight and pilot is zero.
- Selection used framework, length, and scorer-side task name only. The
  model-visible-input audit covered 20,866 operations and 2,948 target-label
  strings and found zero exact or substring label collisions.
- FULL used 984,321 provider tokens and SPLIT used 783,121, including all
  attempts' input and output tokens. The ratio is 0.795595, or 20.44% lower.
- Both arms made 33 calls and each incurred one counted format retry.
- Both arms cover all 1,639 operations. B³ F1 is 0.7320 FULL versus 0.7580
  SPLIT; adjacent-boundary F1 is 0.4294 versus 0.4533.
- The task-cluster bootstrap 95% intervals are `[0.7339, 0.8628]` for the
  token ratio, `[0.0049, 0.0486]` for the B³ delta, and
  `[-0.0184, 0.0676]` for the boundary delta. These pass every planned
  confirmation gate.
- The failed two-call v1 is retained as development evidence. The one-call v2
  method, schema, selector, and confirmation population were set before
  confirmation; the reviewed records show no post-confirmation revision.

## Strongest supported claim

On 32 pre-separated CodeTraceBench exact `task_name` clusters comprising 1,639
operations, a one-call complete skeleton plus source-only-selected local result
evidence reduced provider token volume (input plus output, including retries)
by 20.4% relative to one-call full-session annotation
(SPLIT/FULL 0.796; task-cluster bootstrap 95% CI `[0.734, 0.863]`), retained
100% operation coverage, and met the predeclared −0.03 non-inferiority margins
for B³ and adjacent-boundary F1.

## Required limitations

- Provider token volume is not cached/uncached price-weighted dollar cost.
- This is not a latency result: recorded aggregate SPLIT wall time is higher
  than FULL wall time.
- The 32 units are exact task-name clusters, not independent software
  projects. Some broader project families occur in both development and
  confirmation and more than once within confirmation.
- Each task has one paired generation, so run-to-run model variance is not
  separately estimated.
- The result covers one model/backend on a historically studied benchmark,
  not an untouched external benchmark.
- Quality is a non-inferiority claim. In particular, the boundary-delta
  interval crosses zero.
- SPLIT retains a compact skeleton for every turn and selectively omits full
  `visible_result`; it is not accurately described as reading only 15% of a
  session.
- These flat-stage metrics do not establish nested topology quality,
  cross-session equivalence, or end-user utility.
- The reused scorer writes the legacy internal label `preflight`; the wrapper
  and selection record establish that this population's experimental role is
  confirmation.
