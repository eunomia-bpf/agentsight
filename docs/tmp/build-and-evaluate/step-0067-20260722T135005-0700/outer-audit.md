# Independent Outer Audit — Step 0067 EXPERIMENT Gate

**Verdict: REVISE.**

The experiment evidence is sufficient to leave the EXPERIMENT inner loop and
enter targeted WRITE. No new experiment, benchmark, metric, hierarchy-depth
target, or warning-free rerun is required. The outer transition is not yet
auditable, however, because the step report is still marked `in progress`, the
declared real preflight is not recorded as an executed node, and the
long-horizon case README/reproduction path is stale relative to the reconciled
profile and the current three-warning product contract. These are bounded
handoff and documentation repairs, not scientific blockers.

## Independence and reviewed material

This was a read-only outer audit. I did not edit code, annotations, profiles, or
the paper. I read the complete Step 0067 report, experiment-003 plan, all three
rounds of its plan review, its independent result review, both current case
READMEs, the AgentPProf hierarchy-warning diff and tests, the complete verbatim
user-instruction log, and the frozen idea-story contract. I also checked the
current RQ frontier, the paper's thesis/RQ statements, and loaded the retained
case profiles with stock `go tool pprof`.

I was exposed to the plan review's `REVISE / REVISE / APPROVE` history, the
result review's `PASS`, and the step report's intended WRITE route. I did not
treat those verdicts as authority. The conclusions below come from the
registered decision rule, the independently reconstructed result quantities,
the current pprof artifacts, the warning implementation, and the frozen
thesis/RQs. No expected outer verdict or proposed fix was supplied.

The user's final relevant words are:

> “我觉得看起来还是不太对, 很明显没有层次感? 比原先的还差了>”
>
> “我们是不是要一个机械检查和 warning? 比如说一个 stack 的 chlid 应该 >=2”

They must be read together with the user's earlier explicit instructions
“不要强制深度,” “深度应该是可以参差很大吧?”, and the requirement that semantic
operations refine the native trace hierarchy while LLM/tool calls remain
evidence leaves.

## EXPERIMENT inner-loop completion

### Scientific loop: PASS / complete

Experiment-003 completed the `research-experiment-design` scientific loop:

- **Paper-value admission:** the experiment addresses the fixed RQ2 reject
  argument that the old differential picture might merely render a post-hoc
  six-field taxonomy. It adds a complete source-only automatic hierarchy and
  an independent expert-looping endpoint over an already admitted real case.
- **Fixed RQ:** the plan quotes RQ2 exactly as “Does profiler output correspond
  to real problems?” and does not replace attribution, tag accuracy, or cost.
- **Plan review:** two blocking rounds repaired the missing independent
  endpoint, outcome separation, executable common-source replay, and visual
  gate. Round 3 approved the actual source-only materializer and separate
  post-annotation evaluator.
- **Real/full execution:** all 440 trajectories and 7,229 distinct source tool
  evidence IDs are present. The 125 task clusters expand to the registered 338
  bad--good pair occurrences, with 7,366 bad-side and 3,780 good-side operation
  occurrences. Candidate and fixed-chain inputs preserve the same
  `(source_session, evidence_id, value)` multisets.
- **Registered endpoint:** 435 consensus-scored trajectories contain 173
  expert-looping positives and 262 negatives. Recovery exposure obtains AP
  `0.613735` versus prevalence `0.397701`; the 10,000-draw task-cluster interval
  for AP minus prevalence is `[+0.162023,+0.273910]`. This supports the
  preregistered correspondence hypothesis.
- **Comparison boundary:** fixed-chain AP is `0.655962`, and recursive minus
  fixed has interval `[-0.127370,+0.041557]`. The correct conclusion is
  correspondence plus recursive context, not incremental detector superiority.
- **Independent result review:** the population, multisets, consensus labels,
  AP values, bootstrap intervals, target isolation, and both signed profiles
  were independently reconstructed from retained inputs. The review found no
  scientific must-fix.

The complete run supersedes smoke-only uncertainty: this is a real,
full-population result, not a prefix or synthetic proxy. The inner experiment
question is resolved well enough to make the next paper decision.

### Outer handoff record: REVISE

The Step 0067 report does not yet satisfy the outer gate-exit record:

- its header still says `Status: in progress`;
- it has no explicit EXPERIMENT gate-exit/transition section that links the
  approved plan, final result review, raw artifacts, canonical-memory updates,
  and exact WRITE handoff;
- the plan declares a ten-real-trajectory preflight spanning at least two
  benchmarks, but neither the step report nor the owner reports identify an
  executed preflight command/output. The full run proves real-path engagement
  and the scientific result remains valid, but an unrecorded preflight cannot
  retrospectively be claimed as completed.

This is the first must-fix below. It does not justify rerunning the full
experiment.

## Mechanical hierarchy warnings

### Advisory status: PASS

The current implementation faithfully turns the user's request into diagnostic
pressure rather than a scientific gate:

- `degenerate unary refinement` warns when an optional semantic refinement has
  exactly one direct semantic child;
- `flat fan-out` warns on a large, weakly refined set of direct children;
- `coarse unrefined span` warns when an optional semantic leaf covers at least
  eight tool calls without a semantic child.

Mandatory session/prompt operations are exempt where appropriate, and an
operation with zero semantic children remains a legal leaf. The new test
asserts that a coarse warning is emitted while the command succeeds and writes
the pprof. The README/design diff explicitly says warnings never block
`.pb`/`.pb.gz` output and never force artificial depth.

The scientific path is also clean. The final plan makes depth and warning
counts descriptive QA; the AP/bootstrap endpoint alone decides correspondence.
The independent result review confirms that `score_looping()` does not consume
pprof warning or status output. Step E13 likewise reports 260 coarse-leaf
warnings in the 7,229-operation AgentReward workspace while still accepting
the complete result. Therefore warning absence is not being optimized or
misrepresented as proof.

There is no contradiction between the workspace's 260 annotation warnings and
the signed operation profiles' empty warning arrays: hierarchy warnings are
computed by annotation-workspace replay, whereas the signed candidate/baseline
profiles are emitted from already materialized operation inputs. The handoff
should keep this distinction explicit.

### Documentation mismatch: REVISE

The long-horizon case README still says AgentPProf has only two warning classes.
The current product has three, including the coarse-leaf diagnostic. This does
not invalidate the profile, but it is stale documentation at the exact point
where the user asked for a mechanical hierarchy check.

## Case evidence and WRITE routing

### Case 1 — long-horizon Git deployment: PASS with one handoff repair

The case has enough evidence for targeted WRITE:

- it uses all three complete available executions of the same real
  `git-multibranch` task, inside a fixed 41-session / 5,750-operation
  long-horizon population, rather than presenting one trace as a case;
- the focused profiles conserve 489 operations and 4,558,192
  provider-reported tokens and load in stock pprof;
- the same hierarchy supports two independent additive widths: Terminus2
  accounts for 56.24% of operations, while OpenHands accounts for 86.62% of
  tokens;
- source drilldown supports the scoped finding that repeated SSH password
  diagnosis dominates the expensive OpenHands path and that none of the three
  executions establishes the requested password-authenticated
  `git@localhost` endpoint;
- variable semantic depth and retained LLM/tool leaves answer the user's
  hierarchy and evidence-drilldown requirement without a depth quota.

The current reconciled semantic profiles show the SSH-diagnosis parent with
**105 cumulative operations and 2,103,587 cumulative tokens**. Its direct
exclusive frame remains 97 operations and 1,936,828 tokens. The case README's
text and reproduction commands point to the older focused workspace profiles,
where the parent has only the latter 97 / 1,936,828 cumulative totals. Thus the
README currently conflates exclusive and inclusive totals and does not
reproduce Step E8's shared-name reconciliation. WRITE may use the case only
after this provenance is made unambiguous.

The case supports a resource-dependent bottleneck and source-grounded
diagnosis for this repeated real task. It does not support universal token
ratios, causal failure attribution, or cross-task semantic-name accuracy.

### Case 2 — AgentRewardBench differential profile: PASS

This case is ready for targeted WRITE:

- the primary analysis unit is the complete 440-trajectory,
  125-mixed-outcome-task, 338-pair collection, not one selected pair;
- the automatic hierarchy is persisted before outcomes/expert labels are
  opened, and the post-annotation target isolation was independently checked;
- the recursive signed pprof and unsigned 440-trajectory profile both load in
  stock pprof, retain source-session/evidence labels, and match their documented
  SHA-256 values;
- the recovery and completion focuses were preregistered, not selected by
  observed signed effect;
- the expert-looping AP and clustered interval provide independent scientific
  support, while the fixed-chain interval correctly prevents an unsupported
  superiority claim.

WRITE can present this as a complete differential profiling case whose
outcome-blind recovery exposure corresponds to expert looping and whose
standard pprof supports source drilldown. It must not present it as an
automatic failure classifier, causal diagnosis, universal hierarchy
superiority, nested-topology accuracy, or semantic-name-accuracy result.

## Thesis and RQ integrity

### PASS: no Step 0067 drift

The frozen paper-level thesis remains exactly:

> **Agent observability needs profiling, not only debugging.**

Step 0067 does not replace that thesis with “recursive annotation,”
“hierarchy warnings,” or “AgentReward looping detection.” Operations and
operation stacks remain the two core abstractions; automatic annotation,
differential comparison, pprof focus, and mechanical warnings remain supporting
mechanisms.

The four fixed questions remain attribution, real-problem correspondence,
automatic operation/tag structure, and construction cost. Experiment-003
stays inside RQ2, while the long-horizon case supplies scoped RQ1/user-value
evidence and the AgentReward case supplies additional RQ2/product evidence.
Neither case closes the still-open independent nested-topology part of RQ3.

The result also preserves the positive program without hiding the evidence
boundary: recursive recovery exposure corresponds to expert looping, but it
does not beat the fixed-chain detector under the registered interval. WRITE
should claim the former and avoid the latter claim; this is honest scoping, not
thesis or RQ shrinkage.

## Must-fix before WRITE

1. **Close the EXPERIMENT handoff honestly in `step-report.md`.** Change the
   stale `in progress` status, add an explicit gate-exit/WRITE-transition
   section with direct links to plan, approved plan review, result review, and
   raw artifacts, and record canonical-memory updates. For the declared
   ten-trajectory preflight, either link the actual command/output and record
   its completion or state that it was not separately retained and that the
   later complete run supplies the real-path evidence. Do not rerun the full
   experiment or fabricate a preflight record.

2. **Reconcile the long-horizon case documentation and artifact path.** Make
   the README reproduce the post-name-merge profile, distinguish the direct
   97 / 1,936,828 frame from the cumulative 105 / 2,103,587 subtree, and update
   the mechanical-audit section from two warning classes to the current three.
   Regenerate only derivatives that still point at the stale pre-merge
   artifact; no scientific experiment is required.

3. **Update canonical evaluation memory before the transition.** Record Step
   0067's admitted case/RQ2 evidence and boundaries in `docs/evaluation.md`,
   which currently still ends the relevant frontier at Step 0061. Preserve the
   existing statement that independently scored nested task/subtask topology
   remains open under RQ3; do not turn either case or the advisory warning
   count into an RQ3 score.

After these bounded repairs, the correct route is **targeted WRITE**, not
EXPERIMENT re-entry. WRITE should integrate the two case artifacts, the positive
AgentReward correspondence result, and the stated limitations without changing
the frozen thesis, four RQs, or paper organization.

## Limited Re-Audit — PASS

This re-audit was limited to the three must-fix items above; it did not reopen
the experiment or reassess the scientific verdict.

1. **PASS — Step report gate exit and preflight.** `step-report.md` now marks
   the EXPERIMENT gate complete, records the retained real preflight and its
   limited purpose, provides the auditable evidence chain, preserves the RQ3
   boundary, and identifies the targeted WRITE handoff.
2. **PASS — Long-horizon README reconciliation.** The case README now
   distinguishes the 97-operation / 1,936,828-token direct frame from the
   105-operation / 2,103,587-token reconciled subtree, documents all three
   advisory warning classes, and points reproduction to the reconciled parent
   profiles while explaining the local pre-merge snapshots.
3. **PASS — Canonical evaluation memory.** `docs/evaluation.md` now records
   the admitted Step 0067 RQ2 evidence and intervals, treats warning counts as
   product QA rather than scientific evidence, and explicitly leaves
   variable-depth nested topology and cross-run identity open under RQ3.

All three must-fixes are closed. The Step 0067 EXPERIMENT gate is auditable and
may proceed to targeted WRITE; no experiment re-entry or warning-free rerun is
required.
