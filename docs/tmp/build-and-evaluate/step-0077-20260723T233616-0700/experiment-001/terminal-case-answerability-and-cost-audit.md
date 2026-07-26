# Terminal case-answerability and cost audit

Timestamp: 2026-07-25T20:02:03-07:00
Status: complete result audit; terminal hierarchy rejected as the paper case

## Product adapter repair

The existing AgentReward signed-difference harness now accepts a frozen
annotation-workspace `trace.jsonl` and projects it into the existing complete
338-pair evaluation. It:

- preserves dynamic operation depth;
- keeps `agent` as the requested root and LLM/tool calls as source leaves;
- emits both operation-count and provider-token signed pprof;
- retains source session and evidence IDs as pprof labels;
- normalizes mechanical `llm:step N` names to `llm:call`, avoiding false
  cross-session aggregation by ordinal;
- rejects duplicate source IDs, ancestry cycles, non-session roots, duplicate
  per-view evidence IDs, metric-bearing nodes without applied operation paths,
  and per-session operation/token mass mismatches.

Seven focused Python tests and the complete 89-test Rust suite pass. An
independent code reviewer initially raised agent-root cancellation and
conservation concerns. After inspecting pprof frame interning and the added
validation, it withdrew the former, verified that shared operation nodes still
net across agent callers while full stacks retain side attribution, and returned
PASS.

## Complete signed populations

All three compared hierarchies use the same:

- 440 real trajectories over 125 mixed-outcome tasks;
- 338 bad--good pair occurrences;
- 7,366 failed-side and 3,780 successful-side operation occurrences; and
- 49,525,543 failed-side provider-token occurrences before subtraction.

Every generated operation and token profile opens through stock
`go tool pprof`.

## First-pass versus latest terminal blind review

The reviewer received masked profiles A and B and no annotations, code,
iteration identity, outcomes beyond the declared signed sides, paper, figures,
or prior verdict.

- A was the latest iteration-007 terminal hierarchy.
- B was the fresh iteration-000 hierarchy.

Both profiles answered failed-side, successful-side, source-evidence, and
cross-width questions. The reviewer scored A 9/10 and B 10/10 and selected B:
the terminal revision generalized several names so broadly that isolated pprof
node views mixed unrelated contexts without adding a useful shared parent
structure. This is a strict product-answerability regression, not a depth or
singleton-count complaint.

## Paper hierarchy comparison

A follow-up masked profile C was regenerated from the existing outcome-blind
paper annotation through the same new operations/tokens harness. The reviewer
was instructed to assess complete paths rather than isolated frame names.

It selected C over B with no rubric regression and one strict improvement:
shared responsibility parents expose the population answer directly while
distinct children and exact evidence remain available.

Examples from C, reported as complete-path-prefix signed cumulative mass:

| Path prefix | Operations | Provider tokens |
|---|---:|---:|
| website task / recover interaction | +1,529 | +9,117,033 |
| enterprise workflow / recover interaction | +953 | +5,134,294 |
| visual task / navigate | +377 | +3,362,219 |
| enterprise workflow / sort | -132 | -1,534,809 |
| enterprise workflow / edit | -144 | -1,057,350 |

Positive values are failed-side excess and negative values are successful-side
excess. The common vocabulary does not erase distinctions: visual-task editing
is positive (+157 operations / +1,508,178 tokens), whereas enterprise editing
is negative (-144 / -1,057,350). Source-session and evidence-ID drilldown
remains present at each path.

The paper hierarchy has 406 unique failed-side operation stacks after folding,
versus 977 for the fresh hierarchy and 951 for the terminal hierarchy. Lower
stack count is descriptive only; the masked complete-path answer is the
product result.

## Independent expert endpoint

After the terminal annotations were fixed, the existing scorer was allowed to
read consensus expert-looping labels:

- scored trajectories: 435;
- expert-looping prevalence: 0.397701;
- frozen paper hierarchy recovery exposure AP: 0.634;
- fixed-chain repeated/error AP: 0.655962;
- latest terminal exact recovery exposure AP: 0.397701.

The terminal annotation contains no shared `recover interaction` parent, so
the unchanged exact scorer assigns zero recovery exposure and returns
prevalence. This does not say that detailed terminal paths contain no retry
work. It says the automatic revision mechanism failed to construct the shared
responsibility required for population-level correspondence.

## Root cause and disposition

The complete revision request supplies structural warnings, exact tag reuse,
near-name pairs, singleton contexts, and local evidence. It authorizes merges
and renames but never asks a backend to insert a shared parent around several
different but related child operations. Seven passes therefore optimized local
names without being able to recover the missing hierarchical aggregation.

Disposition:

- keep the adapter, LLM-leaf normalization, conservation checks, both pprof
  widths, and source evidence;
- reject iteration-007 as a replacement for the current paper case;
- do not edit the paper from this terminal result;
- route to Step 0084 shared-parent synthesis, then repeat masked answerability,
  expert correspondence, and complete token/time measurement.

## RQ4 consequence

The current paper-facing 3,521.621 seconds and 12,039,417 provider input tokens
measure the fresh pass only. They are not a clean fresh-to-terminal cost.
Historical fresh plus seven nonconvergent reviews consumed 191,838,723 provider
input tokens and 21,166.766 seconds of summed critical paths; the final
incremental no-change check added 3,691,400 provider input tokens and 387.202
seconds. Those values diagnose the failed policy and must not be presented as
the corrected algorithm's cost.

The corrected algorithm requires a clean fresh-to-terminal run only after
shared-parent synthesis first restores positive usefulness on this same
population.

