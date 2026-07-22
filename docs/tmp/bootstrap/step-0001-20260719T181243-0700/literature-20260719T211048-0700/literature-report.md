# Closest-Mechanism And Baseline-Closure Report

Completed: 2026-07-19T21:10:48-07:00
Parent: BOOTSTRAP Step 0001, re-entered EXPERIMENT_GATE
Node: B6 — object-/artifact-centric mechanism and harness-baseline closure
Repository revision at entry: `957675252011d9cf86d2b28b17414951684f3931`

## Question

Does object-/artifact-centric process mining or the strongest harness-diagnosis
literature already supply the proposed workspace-lifecycle mechanism, and what
state-diff, session-local, retrieval, process-mining, and harness baselines are
required to isolate the remaining claim?

## Search And Verification Method

The node searched primary papers, official specifications, and official tool
repositories. It then downloaded retained PDFs and checked their full text with
`pdftotext` rather than relying on search snippets. The search covered:

- object-centric event logs, object lifecycle, relationships, and changing
  object attributes;
- object-centric discovery, conformance checking, performance/root-cause
  analysis, and feature extraction;
- artifact-centric process discovery and interacting lifecycles;
- process mining over software-repository and fine-grained developer events;
- Agent use of deterministic process-mining artifacts;
- HarnessFix representations, diagnostic labels, ablations, and released code.

Primary sources retained locally are:

| Work | Local PDF | Decisive evidence |
|---|---|---|
| OCEL 2.0 specification | `docs/reference/2024-berti-ocel-2-spec.pdf` | A standardized event/object model already supports event-to-object and object-to-object relations, object attribute histories, timestamps, and multiple object types. |
| OC-PM | `docs/reference/2022-berti-ocpm.pdf` | Existing tools discover object lifecycles and interactions, filter event/object views, construct object-centric DFGs/Petri nets, and expose feature extraction. |
| Object-Centric Conformance Alignments with Synchronization | `docs/reference/2024-gianola-object-centric-conformance.pdf` | Conformance checking already localizes deviations between observed multi-object execution and a normative model while retaining object identity and dependencies. |
| PM4AA | `docs/reference/2026-bala-process-mining-agents.pdf` | Object-centric, imperative, and declarative process mining has already been applied to GitHub software-process records to synthesize project-specific Agent roles. |
| PMAx | `docs/reference/2026-antonov-pmax.pdf` | An Agent can already invoke deterministic process-mining analyses and interpret their artifacts instead of reasoning directly over a giant raw event log. |
| HarnessFix | `docs/reference/2026-chen-harnessfix.pdf` | Full HTIR combines step order, data/control flow, artifact/state effects, and harness implementation anchors; its diagnosis study directly compares progressively structured representations with raw traces. |

Official artifacts were verified for PM4Py
(`process-intelligence-solutions/pm4py`), OCPM (`ocpm.info`), PM4AA
(`liorlimonad/pmaa`), PMAx/ProMoAI (`fit-process-mining/ProMoAI`), and
HarnessFix (`HarnessFix/HarnessFix`). The last repository is named by the paper;
its anonymous-release stability must be checked again before execution.

## Findings

### 1. Artifact lifecycle is prior mechanism, not our novelty

Object-centric process mining was created precisely because a single case or
session cannot represent events that affect several co-evolving objects. OCEL
2.0 already records typed events and objects, many-to-many event/object links,
object/object relations, qualifiers, and changing object attributes. OC-PM and
PM4Py already support lifecycle discovery, object-centric directly-follows
graphs, performance analysis, conformance constraints, graph-based features,
and filtering.

Therefore the following claims are rejected as standalone novelty:

- events should be organized around persistent artifacts instead of one case;
- artifacts have create/change/delete lifecycles and interact;
- a process model can be discovered from an event/object log;
- lifecycle or interaction views can expose bottlenecks and deviations;
- OCEL is a novel internal representation for Agent work.

The implementation should continue to use `agent-session` as its native source
abstraction. An OCEL 2.0 export may be used as an evaluation adapter to run
established process-mining baselines, but it must not become a second production
event IR or a claimed contribution.

### 2. Applying object-centric mining to software or giving its output to an Agent is also prior work

PM4AA converts GitHub commits, issues, pull requests, users, and messages into
an OCEL and combines object-centric DFGs, imperative models, and declarative
constraints to derive Agent roles. PMAx separates deterministic local process
computations from an Agent that interprets the resulting artifacts. Earlier
developer-interaction work also mines fine-grained IDE traces.

Thus neither “object-centric process mining for software repositories” nor “an
LLM/Agent interprets process-mining artifacts” is a sufficient contribution.
PM4AA is commit/platform-record centered and generates role specifications;
PMAx answers business-process questions. Neither reconstructs native Agent
actions across replaced sessions to diagnose ongoing autonomous work, but both
must appear in closest work and constrain the mechanism claim.

### 3. HarnessFix is a direct mechanism and RQ3 baseline, not merely related work

HarnessFix maps failed trajectory steps to harness layers and implementation
artifacts through HTIR. Its full representation includes step order,
data/control-flow links, artifact/state effects, and implementation anchors. On
80 human-annotated failed trajectories across GAIA, SWE-Bench, AppWorld, and
Terminal-Bench, the paper reports a progression from raw trace to Full HTIR:
step accuracy 55.0% to 85.0%, root-cause accuracy 53.8% to 83.8%, anchor accuracy
50.0% to 81.3%, harness-layer score 58.4% to 86.2%, and repair-operator accuracy
51.3% to 82.5%.

This result is direct same-mechanism pressure: a structured trace with
artifact/state effects can improve automatic diagnosis over raw traces.
HarnessFix also spans open-ended research QA, coding, stateful applications, and
terminal workflows, so a generic non-coding or harness-attribution claim is not
enough.

The remaining difference is narrower but meaningful. HarnessFix starts from
known failed executions and repairs a concrete harness using run-level
provenance. This project studies a persistent workspace that outlives sessions
and individual goals, including nominally successful or still-running work, and
asks whether an offline supervisor can detect progress pathologies and decide
when intervention becomes warranted. RQ3 must compare against Full HTIR on a
compatible failed-trajectory slice and separately test longitudinal recurrence
across episodes. If the released implementation cannot ingest our traces, the
paper must use its published raw/data-flow/data-control/full-HTIR ladder and
annotation targets as a faithful reproduction, disclose incompatibilities, and
avoid direct end-to-end superiority claims.

### 4. Process mining supplies strong controls but not the target diagnosis by itself

Traditional/object-centric process mining separates discovery, conformance,
performance analysis, and prediction. Conformance requires an expected model or
constraint set. The proposed pathologies—stagnation, drift, validation gap, and
harness waste—are not universally invalid transitions: repeated tests may be
correct, documentation may be the goal, and exploration may legitimately revisit
files. A discovered common process also cannot serve as independent truth for a
new task.

Consequently object-centric conformance is not a drop-in automatic supervisor.
It is, however, a strong deterministic baseline and feature family:

- OC-DFG/eventually-follows frequencies and duration/performance annotations;
- per-object lifecycle variants, revisitation, waiting time, and interaction
  features;
- declarative candidate constraints such as “write is eventually followed by
  validation,” used only when independently specified;
- alignment/deviation cost against task- or harness-specific normative models
  when such models exist.

If these conventional features plus the same supervisor match the proposed
workspace queries, the paper cannot claim that its custom representation is
scientifically necessary.

### 5. The surviving claim is about longitudinal supervision, not representation invention

The defensible claim is now:

> Across goals and replaced sessions, does evidence-linked evolution of a
> persistent workspace expose ongoing progress pathologies and retrospective
> intervention points that remain less reliably accessible from state changes,
> session-local evidence, established object-centric process features, Full
> HTIR-style run structure, or equal-budget raw retrieval?

The novelty candidate is the problem/measurement unit and empirical result:

1. the unit is a persistent workspace interval that may span many session and
   goal boundaries, not one failed run;
2. the target includes successful-but-wasteful and not-yet-failed process states;
3. evidence includes realized artifact transitions plus zero-file-effect actions,
   without inferring intent from file motion;
4. the output includes evidence localization and the earliest supported
   retrospective intervention recommendation;
5. the evaluation asks for incremental value over established lifecycle,
   state-diff, session-local, HTIR, and retrieval controls at enforced access
   parity.

This position survives the search, but its same-claim risk is **medium-high**.
It is an empirical oversight claim, not a new event-log formalism.

## Fixed Baseline Consequences

### RQ1 — Diagnosis and intervention

The replacement feasibility plan must preserve these conditions:

1. Final State/Outcome;
2. Native Report;
3. Counts and coarse time series;
4. $W_0\rightarrow W_T$ workspace State Diff;
5. Session-Local/Batched Reader that cannot see cross-session continuity;
6. equal-budget Raw Retrieval over the same native evidence;
7. established OCPM Features, generated deterministically from an OCEL adapter;
8. proposed Workspace Trajectory queries.

The headline comparison remains Workspace Trajectory versus Raw Retrieval, but
support requires that State Diff, Session Local, and OCPM Features do not explain
the result. Every tool-mediated condition must be constrained by returned bytes
and model-visible tokens at the interface, not lines or post-hoc accounting.

### RQ2 — Mechanism

Required ablations are cross-session links, event order, artifact lifecycle,
object relationships/workspace hierarchy, validation candidates, and evidence
indexing. OCPM Features are the “established process structure” control. Raw
Retrieval is the “structure can be reconstructed by a capable Agent” control.
State Diff is the “only realized change matters” control. Counts are the “volume
and duration explain the signal” control.

### RQ3 — Harness diagnosis and generalization

HarnessFix Full HTIR is mandatory on compatible failed trajectories. The
longitudinal part must aggregate repeated evidence over multiple executions and
include nominally successful but wasteful episodes; otherwise RQ3 is already
subsumed by HarnessFix. A diagnosed harness flaw should be tested by a scoped
intervention or replay where feasible, following HarnessFix/REFLECT rather than
judge agreement alone.

### Non-coding feasibility

At least one real auto-research or OR-Space path must pass capture, goal-boundary,
artifact typing, label prevalence, evidence-ID, and intervention-label checks
before the taxonomy is frozen. HarnessFix's GAIA evaluation prevents merely
claiming “non-code” as novelty; the distinction must be cross-session persistent
artifact evolution.

## Reuse And Implementation Consequences

- Keep the production path `agent-session -> thin deterministic workspace
  projection -> supervisor queries`; do not add a general event IR.
- Add an evaluation-only OCEL 2.0 exporter so PM4Py/OCPM algorithms are reused
  rather than reimplemented. The adapter maps action to event, file/session/goal
  to typed objects, source call ID to event ID, and create/modify/rename/delete to
  explicit lifecycle/relationship updates.
- Use PM4Py's official OC-DFG, lifecycle, feature, and conformance functions in
  the baseline harness. Do not vendor or depend on PM4Py in the shipping Rust
  binary.
- Reuse HarnessFix's released code only if its trace and harness-artifact inputs
  can be adapted without changing the scientific task. Otherwise implement the
  published representation ladder as a named reproduction and score only shared
  diagnosis targets.
- Build one budget-enforcing response broker shared by all query conditions.
  It truncates/denies results before they reach the supervisor, accounting for
  UTF-8 bytes and model tokenizer units; no condition receives arbitrary shell
  access.

## Same-Claim Disposition

**Reject** representation novelty, generic artifact lifecycle, generic
object-centric analysis, generic structured-trace diagnosis, and generic harness
attribution. **Retain** the ambitious automatic-oversight direction as a
medium-high-risk empirical claim about longitudinal workspace process state and
earliest intervention across session/goal boundaries.

No current paper result supports that claim. The next node must test whether
truth construction, positive prevalence, access parity, and one coding plus one
non-coding path are executable before any full pilot or query-service build.

## Decisive Next Node

Create a scientifically distinct truth-and-fairness feasibility experiment. It
must:

1. select one real coding and one real non-coding persistent-workspace interval
   without using pathology labels;
2. independently annotate the four pathologies, minimal action evidence,
   affected artifacts, and earliest retrospective intervention;
3. report positive prevalence and inter-annotator feasibility before fixing the
   main sample size;
4. instantiate State Diff, Session Local, Raw Retrieval, OCPM Features, Full
   HTIR-compatible, and Workspace Trajectory views from the same source actions;
5. enforce equal returned-byte/token and query budgets through one broker;
6. run only a dependency-level engagement check after independent plan review.

This is a new experiment node. The terminally closed RQ1 plan remains historical
and receives no fourth review.
