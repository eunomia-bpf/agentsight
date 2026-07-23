# Independent result review: AgentReward recursive differential profile

**Verdict: PASS.  Must-fix: none.**

This is a read-only audit of experiment-003's completed AgentReward result.
I read the registered [plan](plan.md), its review history
([plan-review.md](plan-review.md)), the post-annotation evaluator
[`script/agentreward_recursive_diff_eval.py`](../../../../../../script/agentreward_recursive_diff_eval.py),
the retained [summary](../../../../../.agentsight/experiments/agentreward-recursive-diff-v1/full-result/summary.json),
and [results](../../../../../.agentsight/experiments/agentreward-recursive-diff-v1/full-result/results.md).
I then independently recomputed and compared the relevant quantities from the
frozen pair list, raw bad/good operation inputs, source-only workspace trace,
official `annotations.csv`, and the four emitted operation inputs.  No code,
paper text, input, or result artifact was changed.

## Registered question and endpoint

The plan registers a trajectory-level, outcome-blind recovery-path exposure
score against AgentRewardBench's consensus `trajectory_looping` label, with
ordinary non-interpolated AP and a 10,000-draw task-cluster bootstrap over 125
task IDs.  Its decision rule is correctly separate from signed-profile shape:
the recovery AP minus expert-label prevalence interval must be wholly positive
to support correspondence; the recursive-minus-fixed interval separately tests
incremental detector performance.  The final plan review's Round 3 approval
correctly identifies this as an executable post-annotation scorer rather than
an outcome-aware annotation step.

## Population and source accounting

All reported population values reproduce from raw inputs.

| check | independent reconstruction | reported | result |
|---|---:|---:|---|
| unique source trajectories | 440 | 440 | match |
| mixed-outcome task clusters | 125 | 125 | match |
| bad--good pair occurrences | 338 | 338 | match |
| bad-side operation occurrences | 7,366 | 7,366 | match |
| good-side operation occurrences | 3,780 | 3,780 | match |
| source-only manifest / workspace sessions / prompts | 440 / 440 / 440 | 440 population | match |
| distinct source tool evidence IDs | 7,229 | annotation-input audit: 7,229 | match |

The apparent difference between 7,229 unique evidence IDs and 11,146 signed
operation occurrences is accounted for by the registered pair-occurrence unit:
3,155 evidence IDs are reused, the maximum multiplicity is three, and the
resulting extra occurrence count is 3,917.  This is expected pair expansion,
not a missing-source or double-projection defect.

## Candidate/baseline source-multiset equality

I compared the raw aggregate bad and good operation files independently with
all four retained full-result inputs.  The result is stronger than the summary
boolean alone:

- separate bad- and good-side `Counter(source_session, evidence_id, value)`
  multisets match from raw input to recursive input and from recursive input to
  fixed-chain input;
- the fixed bad and good files are exact JSON multisets of the corresponding
  raw files;
- every recursive row preserves the raw fields and value, and adds an
  `operation` path exactly equal to the source-only workspace tool path plus
  `call_id=evidence_id`, `tool=action`, and `source_kind=tool`;
- all raw evidence IDs occur in the source workspace (zero missing).

Therefore the candidate and baseline differ in stack projection, not source
population, pair multiplicity, or signed weight.  This validates the
evaluator's pre-pprof equality check and the summary's
`same_source_multiset: true`.

## Consensus labels, AP, and clustered uncertainty

I independently grouped official `data/annotations.csv` rows by the evaluator's
sanitized source-session ID, retained only unanimous `Yes`/`No` looping labels,
reconstructed per-trajectory recovery and fixed-chain fractions from the raw
operations and applied workspace paths, and reran the deterministic bootstrap
with seed `20260722`.

| endpoint quantity | independent value | summary/results value |
|---|---:|---:|
| consensus-scored trajectories | 435 | 435 |
| positives / negatives | 173 / 262 | 173 / 262 |
| excluded consensus conflicts | 5 | 5 |
| task clusters | 125 | 125 |
| recursive recovery AP | 0.6137351576471328 | 0.613735 |
| fixed repeated/error AP | 0.6559621177236952 | 0.655962 |
| looping prevalence | 0.39770114942528734 | 0.397701 |
| bootstrap draws retained | 10,000 | 10,000 |
| recursive minus prevalence 95% interval | [+0.1620230028, +0.2739098135] | [+0.162023, +0.273910] |
| recursive minus fixed 95% interval | [-0.1273700639, +0.0415569755] | [-0.127370, +0.041557] |

The result interpretation is correct and appropriately limited: the positive
recursive-minus-prevalence interval supports the registered correspondence
hypothesis; the recursive-minus-fixed interval crosses zero, so the result is
**indistinguishable**, not evidence that the recursive hierarchy outperforms
the fixed-chain detector.

## Pprof readability and warnings

Both retained `.pb.gz` artifacts are accepted by `go tool pprof -top` and
produce readable `Type: operations` output.  The summary records AgentPProf
`status: ok` for both recursive and fixed profiles, deterministic output, and
empty warning arrays.  The observed signed totals are readable as a
bad-minus-good operation profile; cancellation in the fixed profile's positive
and negative difference counts is not a population mismatch and is not used
as a scientific endpoint.

The plan and `results.md` correctly isolate hierarchy warnings from the RQ2
claim: pprof depth/warnings are product QA, while the AP/cluster-bootstrap
endpoint determines correspondence.  In the evaluator, `score_looping()` uses
only source paths, source operation fields, consensus labels, and task groups;
it does not consume pprof warning/status output.  Thus warning-free output is
not being used as evidence for the scientific conclusion.

## Annotation-time versus endpoint-label isolation

The source-only workspace audit records the 440-session source boundary and
the model-visible schema: session identity/benchmark/agent, prompt text, LLM
reasoning/state/URL, tool action/evidence/visible error, and additive
measurements.  It excludes `summary_info`, rewards, pair side/membership/IDs,
success, looping, side-effect, and optimality labels.

I independently confirmed that the source workspace trace exposes only the
documented field keys, and that neither its trace nor `annotation.json`
contains an exact registered expert-label literal (`Successful`,
`Unsuccessful`, `Complete Failure`, `Suboptimal`, `Somewhat Optimal`, `Yes`, or
`No`).  The evaluator opens `annotations.csv` only in `consensus_looping()`,
after it has read the persisted workspace and emitted/validated both pprof
inputs.  The post-annotation pair/outcome join is therefore consistent with
the registered outcome-blind construction boundary.

## Final disposition

All requested result-facing checks reproduce from retained raw inputs: the
440/125/338 population, source multisets, 435-label endpoint, AP values,
10,000-draw task-cluster intervals, pprof readability, empty warnings, and
the warning/endpoint separation.  **PASS; no must-fix is required.**
