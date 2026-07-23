# Step 0067: external-Agent sparse operation marks

Timestamp: 2026-07-22T13:50:05-07:00
Gate: EXPERIMENT
Status: complete — route to targeted WRITE

## Node 0067-E1 — correct the product/Agent boundary

The user clarified that the active Agent, not a built-in Qwen backend, should
read source trajectories and mark transitions. The interrupted Qwen3.6-27B
full run is retained only as a non-authoritative candidate baseline at 259/405
complete sessions. It is not the default annotator and will not authorize a
case-study or paper claim.

AgentPProf already exposes the required small product interface:
`--operation-file` plus `--operation-mark-file` produces one standard pprof.
The annotation file supplies complete paths at replay-stable source-operation
boundaries. AgentPProf does not infer stack actions or call any model.

## Node 0067-E2 — fixed source-only annotation packets

The next experiment uses the already registered 41-session long-horizon
collection: the top decile by source-visible operation count, trajectory-ID
tie-break, totaling 5,750 operations. A research-only exporter reconstructs
source-native turns and emits balanced packets for independent subagents. An
Agent may inspect the task, summaries, selected intervals, and raw source refs
adaptively; it is not required to read every turn before marking. The exporter
does not read stages, scores, manifests, recurrence outputs, or outcomes. Each
subagent returns sparse marks with complete semantic paths; the root Agent
audits every session, reconciles shared names, and invokes the existing CLI.
The subagent is an automatic annotation backend outside AgentPProf. Its
Agent-produced configuration is an automatic algorithm output, not a
human reference or an unscored case-study aid. It must be scored against
independent annotations under the same standard RQ protocols as admitted
non-LLM and automatic-LLM constructors.

## Node 0067-E3 — preserve and refine the native hierarchy

Read-only inspection of `origin/master` found that the product input is already
hierarchical. The shared prefix is `project -> agent -> session -> prompt`;
time/token/file/network views then attach source-native prompt, LLM, tool,
command/process, path/domain, effect, model, and status frames. The current
research branch additionally carries explicit request/event `task_path` values
and normalized `phase/action/object/result` evidence.

Automatic annotation therefore does not invent an unrelated tree from a flat
log. It operates on ordered child ranges inside the existing session/request
hierarchy. A complete semantic path refines responsibility between the native
task/request context and its source evidence; adjacent work with the same path
inherits one sparse mark and folds together. The CLI can retain lower-level
phase/action/evidence frames after the semantic path. Depth remains an observed
property: the backend targets no minimum, maximum, or distribution.

## Node 0067-E4 — user-value figure acceptance

Producing a valid `.pb.gz` is not completion. The root Agent must open the
multi-session profile with stock `go tool pprof`, inspect the rendered flame
graph, and include the actual profile figure in the paper. The figure must
exhibit source-supported uneven paths, including genuinely deep regions where
the automatic backend finds them, without enforcing a depth quota. The case
analysis must use pprof focus/drilldown plus source evidence to explain useful
task decomposition, recurring/returned work, and expensive paths that fail to
reach a supported conclusion. A syntactically valid but operationally
uninformative profile returns to algorithm iteration.

## Node 0067-E5 — native ancestry and independent resource width

The product path previously defaulted an external operation-mark file to the
semantic `operation` field alone and rejected every resource view except
operation count. That behavior contradicted the source hierarchy and made the
same automatic segmentation impossible to reuse for token, duration, or
effect-count attribution. The minimal correction keeps the annotation path
independent from the additive measure. A marked profile now defaults to the
available `project -> agent -> source_session -> prompt -> operation -> call -> tool`
ancestry and accepts every existing pprof view on normalized resource-weighted
operations. The normalized input retains zero-weight source operations so
sparse resources participate in mark propagation without gaining false width.
Population profiles may explicitly omit unique session/prompt/call
frames so identical semantic paths fold across runs; source identifiers remain
pprof evidence labels for drilldown.

## Node 0067-E6 — complete long-horizon case and visual audit

Three independent automatic Agent annotation batches cover all 41 sessions,
3,146 source-native turns, and 5,750 operations with 565 sparse marks after one
adjacent no-op mark was contracted. The merged path depths are 1--3 without a target; native and evidence frames make
the population stacks 6--8 levels deep. The same paths conserve 5,750 operation
counts and 117,303,194 provider-reported tokens in two standard pprofs.

The complete profile was opened in stock pprof. Its full overview is valid but
too dense for a paper figure. Standard focus over all three `git-multibranch`
sessions produces a genuinely aggregated case: repeated SSH
authentication diagnosis dominates the OpenHands path, substitute validation
paths remain narrow, and operation-count versus token width reverses the
framework-level cost ordering. A semantic-only stock-pprof projection improves
overview readability, but the current paper panels still need a narrower
stock-pprof drilldown before the WRITE gate may claim that the static image
itself exposes temporal returns. Detailed source-grounded analysis is recorded
in `experiment-001/full-results.md`.

## Node 0067-E7 — approved complete automatic-backend run

Independent plan review approved one complete 405-session A0 run against two
non-LLM explanations: native-tree folding and the strongest adopted
multi-resolution recurrence constructor. It excluded the interrupted recursive
Qwen run because A0 is already an automatic Agent backend and finishing an
incomplete third method would not change the paper decision.

The scorer now assigns a fresh contiguous occurrence identity to each sparse
mark while pprof continues to fold equal visible semantic paths. Thus a return
to an earlier operation aggregates for profiling but does not incorrectly
merge noncontiguous workflow stages under B-cubed. The fixed 41-session output
covers 3,146 turns and 5,750 operations. Twelve balanced, non-overlapping
source-only batches cover the remaining 364 sessions, 14,002 turns, and 15,116
operations. Their union is exactly 405 sessions, 17,148 turns, and 20,866
operations. All automatic annotations and root validation completed before
official stages were opened.

## Node 0067-E8 — independent case and implementation audits

One independent reviewer recomputed every long-horizon and Git-case total from
the automatic annotations and pprof artifacts without opening official stages
or outcomes. It classified the case as valid supporting evidence. It also found
one synonymous SSH-return label that fragmented the aggregate; root
reconciliation now folds it into the same diagnosis responsibility, which has
105 operations and 2,103,587 tokens across the two OpenHands executions.

The same review routed four local corrections to the later WRITE gate: use
“sparse complete-path marks” rather than paths, name source-session and
call/evidence IDs precisely, replace the obsolete architecture figure's
SVG/JSON outputs with the pprof-only product boundary, and use a readable
stock-pprof drilldown rather than claiming temporal order from a dense static
overview. No paper narrative, RQ, or thesis change is authorized.

A separate implementation reviewer reproduced sparse-resource and custom
sequence failures in the first product patch. The corrected product now lets
zero-weight carrier operations receive marks before removing their pprof
width, derives native occurrence ancestry from `source_session`, rejects source
order mismatches, contracts adjacent no-op marks, and distinguishes visible
pprof identity from contiguous scorer occurrence identity. Four focused Rust
tests and three Python regression tests pass; the review rerun reports zero
remaining must-fix issues.

## Node 0067-E9 — complete blind scoring and result review

The completed A0 constructor emits 5,901 sparse marks with observed semantic
depth 1--3 and conserves 20,866 operations plus 494,862,929 provider-reported
tokens. Ordinary operation-level B-cubed F1 is 0.699974, compared with 0.662740
for the adopted recurrence constructor and 0.361145 for source-native turns.
The paired 251-task bootstrap delta over recurrence is +0.036957 with 95%
interval `[+0.016986, +0.056883]`. Exact boundary F1 is 0.389103 versus
0.265571 for recurrence.

A fresh independent reviewer reconstructed the gold partition and every metric
from raw files without invoking the experiment scorer's metric functions. It
matched all values and issued PASS for this CodeTrace result. The effect is
heterogeneous: positive on Terminus2 and OpenHands but negative on SWE-agent
and mini-SWE-agent. A0 also remains oversegmented, with 5,901 occurrences for
2,948 official stages and boundary precision 0.284571. The result therefore
routes to RQ3 as flat partition/structure fidelity; it does not by itself prove
nested topology, semantic-name accuracy, universal dominance, localization, or
constructor practicality.

The actual `native_turn` row is only a direct source-turn diagnostic. The
separate N0 row uses every source hierarchy field available on this corpus:
`phase -> action_kind -> raw_action_key`, contracting adjacent equal paths. It
has 15,813 groups, B-cubed F1 0.396530, and boundary F1 0.259373. A follow-up
independent reviewer reconstructed all N0 occurrences and metrics exactly and
issued PASS. N0 is the structurally matched native-tree baseline, while N1
remains the stronger registered comparator.

## Node 0067-E10 — full standard-pprof replay

The fixed automatic marks replay through the product as two complete standard
profiles: 20,866 operation counts and 494,862,929 tokens. Stock
`go tool pprof` reads both and exposes source-session, call, and evidence labels.
The function stack omits high-cardinality source identifiers only for the
cross-session aggregate; their labels remain available for drilldown.

Initial replay correctly rejected 17 case-only semantic-label variants that
would normalize to duplicate pprof frames. The research assembler now
case-folds labels before assigning semantic IDs. A regression test covers this
condition; mark count, occurrence partition, resource mass, and every score
remain unchanged. The fix is source-only product compatibility work, not
gold-driven method tuning.

The complete profile still has an open naming limitation. Among 102 repeated
task families, 90 have multiple near-synonymous root phrases; only the five
case-study roots and one SSH child phrase were explicitly reconciled. The Git
case is a valid cross-session aggregate, but general automatic name equivalence
remains unproven. Experiment-001 therefore remains in progress for complete
RQ2 and RQ4 runs and the second differential case.

## Node 0067-E11 — current-A0 construction cost

The independently reviewed Step 0005 four-workload and union experiment remains
the primary RQ4 scaling evidence. A release-mode supplement replays the actual
fixed 20,866-operation, 5,901-mark A0 input. Three operation-width runs each
took 0.62 seconds; largest peak RSS was 314,032 KiB (306.67 MiB). Three
token-width runs took 0.63, 0.65, and 0.64 seconds; largest peak RSS was
314,140 KiB (306.78 MiB). Both standard pprofs preserve exact mass and source
drilldown labels.

Independent review issued PASS for fixed-input profile construction. Agent
annotation elapsed time and provider/model usage are unavailable and are not
estimated, so the result does not characterize end-to-end automatic
construction. Exact commands and all observations are recorded in
`experiment-001/a0-cost-supplement.md`. No further cost workload is required;
the open matrix work is RQ2.

## Node 0067-E12 — retained differential case with source drilldown

The retained AgentRewardBench case is already the required second complete
multi-session case rather than a pending experiment. It covers all 440 eligible
real trajectories, 125 mixed-outcome tasks, and 338 bad--good pair occurrences.
An independent reviewer reconstructed the pair population and signed profile:
7,366 bad-side and 3,780 good-side operations produce 7,103 positive and 3,517
negative occurrences over 4,140 nonzero stacks. The previously reported excess
paths—progress +1,825, repeated +1,261, repeated click/no-op/scroll
+639/+356/+277, stopped +92, terminal -92, conclusion -67, and
`send_msg_to_user` -100—match stock-pprof readback.

One local product-integration gap was real: the old aggregate profile retained
the signed side but not the source session and step identity. The existing
evaluation script now emits the aggregate directly from the unchanged 338
pairs, records the executable AgentPProf command, and writes `agent`,
`source_session`, and per-step `evidence_id` as pprof labels outside the
semantic function stack. Release and debug binaries produce the same
deterministic SHA-256
`0d6a7e80fbc805d374ad6bd4b668241584150a317049a45b4d0045f473b7495d`.
All old top values remain identical; only reversible evidence labels change.
The root also opened this exact profile in stock Go pprof. A repeated-work focus
shows 1,485 bad-side versus 224 good-side occurrences, while a combined
terminal/conclusion/user-report focus shows 373 good-side versus 183 bad-side
occurrences. Both retain the full six-frame semantic evidence path. The two
screenshots are paper/inspection derivatives, not a product format.

The canonical artifact is
`docs/visexp/out/agentreward-diff-pprof-v1/agentreward-338-pairs-bad-minus-good.operations.pb.gz`.
It supports collection-level localization of failed-side excess and
successful-side missing paths with real source drilldown. It does not establish
causality, an automatic failure classifier, A0 accuracy, nested-topology
accuracy, semantic-name accuracy, or human utility. The differential case and
RQ4 supplement are therefore complete; only the registered RQ2 localization
matrix remains open in this EXPERIMENT gate.

## Node 0067-E13 — advisory hierarchy-shape checks

Opening the first aggregate figures exposed a product problem that ordinary
profile validity cannot detect: a syntactically valid annotation can still
produce a redundant unary chain, a very broad flat fan-out, or one optional
semantic leaf that absorbs many source tool calls. AgentPProf now reports all
three shapes as advisory warnings. A semantic refinement node with one child
is suspicious because the refinement introduced no choice; a leaf with zero
children remains valid. Mandatory session- and prompt-level operations are
exempt because one source child is ordinary there. The warnings never block
profile generation, set a target depth, or enter a scientific metric.

The full AgentReward workspace has zero unary and zero flat-fan-out warnings.
It has 260 coarse-leaf warnings among 7,229 source operations, which correctly
identifies the remaining under-refined regions instead of hiding them. This
diagnostic does not invalidate the complete profile or force artificial
children. All 77 AgentPProf tests and six focused Python tests pass.

## Node 0067-E14 — complete recursive AgentReward endpoint

Three disjoint automatic-Agent batches annotated all 440 source-only
trajectories before any outcome or expert label was opened. The merged
workspace has 2,131 sparse annotations, 7,229 operation samples,
51,904,621 provider-reported tokens, and observed semantic depth four before
the LLM-call and tool-call evidence leaves. The 440 trajectories cover 125
mixed-outcome tasks and expand to 338 bad--good pair occurrences: 7,366
bad-side and 3,780 good-side operation occurrences. Candidate and fixed-chain
profiles use exactly the same source multiset.

On the independent expert `trajectory_looping` endpoint, 435 trajectories have
consensus labels: 173 positive and 262 negative. The preregistered recursive
recovery-path score is AP 0.613735 versus prevalence 0.397701. Its 10,000-draw
task-cluster interval over prevalence is
`[+0.162023, +0.273910]`, so the tested correspondence hypothesis is
supported. The fixed-chain score is AP 0.655962; recursive minus fixed has
interval `[-0.127370, +0.041557]`, so incremental superiority is
indistinguishable rather than supported.

An independent result reviewer rebuilt the population, source-multiset check,
consensus labels, both AP values, and both bootstrap intervals from the stored
inputs; it also loaded both signed profiles with stock Go pprof. The review
issued PASS with no must-fix. The source-only workspace contains none of the
registered expert-result literals, and scientific scoring occurs only in the
post-annotation evaluator.

The recursive signed profile is now the primary Case Study 2 artifact:
`docs/visexp/out/agentreward-diff-pprof-v1/agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz`.
The root opened the preregistered recovery and completion focuses in stock
pprof. Both show the automatic recursive hierarchy plus source LLM/tool leaves;
the screenshots are documentation and paper derivatives, not product output.
The earlier fixed-chain profile remains the registered comparator. The
EXPERIMENT evidence is complete and routes to WRITE without changing the
paper's thesis or RQs.

## Node 0067-E15 — retained real preflight

The declared real preflight was executed and retained; it was omitted from the
earlier step narrative, not skipped. The fixed source list is
`.agentsight/experiments/agentreward-recursive-diff-v1/preflight-session-ids.json`.
It covers ten real trajectories from four benchmarks and 186 source
operations. The source-only materialization, 63 automatic annotations,
operation/token replay reports, and backend report are under
`.agentsight/experiments/agentreward-recursive-diff-v1/preflight-workspace/`.
The separate post-annotation evaluator outputs are under
`.agentsight/experiments/agentreward-recursive-diff-v1/preflight-result/`.
Both pprofs load in stock Go pprof. The preflight AP happened to be 1.0, but the
ten-trajectory sample was unbalanced and is not used as scientific evidence;
only the complete run authorizes the result above.

## EXPERIMENT gate exit and WRITE transition

The Step 0067 EXPERIMENT inner loop is complete. The auditable chain is:

1. [approved experiment plan](experiment-003/plan.md);
2. [three-round plan review ending APPROVE](experiment-003/plan-review.md);
3. [source-only annotation instructions](experiment-003/backend-instruction.md);
4. [independent Web/Visual annotation audit](experiment-003/web-visual-annotation-audit.md)
   and [Other audit](experiment-003/other-annotation-audit.md);
5. full raw results under
   `.agentsight/experiments/agentreward-recursive-diff-v1/full-result/`;
6. [independent full-result PASS](experiment-003/result-review.md);
7. [independent outer audit](outer-audit.md), whose bounded documentation
   must-fix items are resolved in this report, both case READMEs, and
   `docs/evaluation.md`.

Canonical evaluation memory now records the Step 0067 RQ2 correspondence
result, fixed-chain comparison boundary, warning/product-QA separation, and
the still-open RQ3 nested-topology boundary. The long-horizon case README now
distinguishes the direct SSH frame (97 operations / 1,936,828 tokens) from the
reconciled subtree (105 / 2,103,587), points reproduction at the reconciled
profiles, and documents all three advisory warning classes.

The exact WRITE handoff is deliberately narrow:

- insert the two complete multi-session case studies and their real stock-pprof
  figures;
- add the positive AgentReward AP correspondence result and the
  fixed-comparison boundary;
- update stale automatic-construction numbers already independently reviewed;
- preserve the frozen thesis, all four RQs, and the existing paper
  organization.

No new benchmark, metric, hierarchy-depth target, warning-free rerun, or
experiment re-entry is required before this targeted WRITE.
