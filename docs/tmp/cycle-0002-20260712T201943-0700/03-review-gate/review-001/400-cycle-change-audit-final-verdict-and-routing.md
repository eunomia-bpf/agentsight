# Review 001 / Node 400: Cycle-Change Audit, Final Verdict, and Routing

## Context and status

- **Timestamp:** started 2026-07-13T11:00:00-07:00; completed 2026-07-13T11:06:00-07:00.
- **Phase / step / gate:** `BUILD_AND_EVALUATE` / cycle 0002 / `REVIEW_GATE`.
- **Parent:** `300-full-paper-reread-and-scientific-assessment.md`.
- **Node status:** complete for the requested whole-paper review, cycle audit, capability audit, final verdict, and routing scope.
- **Scientific-isolation rule:** the paper-only and source-grounded verdict in Nodes 100–300 was fixed before the internal materials below were opened. Internal reports explain how the project reached the current manuscript; they do not change the scientific judgment.

## Objective

This final node does four things:

1. audits what cycle 0002 actually changed in experiments, writing, evidence, and paper readiness;
2. checks drift from the fixed thesis, four fixed RQs, and original story;
3. identifies procedural violations and repeated low-yield work without proposing any skill, AGENTS, paper, or code change;
4. gives one final scientific verdict and routes exactly one highest-paper-value next experiment.

The fixed contract is preserved verbatim:

> **Agent observability needs profiling, not only debugging.**

The four RQs remain resource attribution, real-problem localization, tag accuracy, and profiling cost. No finding below narrows, merges, deletes, replaces, or silently weakens one.

## Internal inputs and provenance

Only after completing Node 300, I read:

- all of `docs/idea-story.md`, including the permanent Initial Narrative and E000–E008;
- all of `docs/evaluation.md`;
- all of `docs/background-related-work.md`;
- all of `docs/questions-for-author.md`;
- the current cycle's EXPERIMENT gate entry, source/literature reports, branch plans, plan/implementation/preflight/full/result reviews, outer audit, and raw-result summaries for CodeTraceBench, ToolSafe, AgentNet, AgentProcessBench mean-risk, and AgentProcessBench Wilson;
- the current cycle's WRITE entry, three idea discussions and root disposition, writing-round reports, recovery report, targeted repairs, three outer audits, and final `999` report.

I also rechecked `docs/user-instruction.md` for the explicit one-experiment/one-claim rule, fixed-RQ constraint, no-Git rule for writing/review, prohibition on per-node Git/hash-bound freeze protocols, original-story authority, no negative-results paper story, and current `BUILD_AND_EVALUATE` phase.

No internal artifact was edited.

## Audit method

The audit compares four states:

1. **fixed intended state:** exact thesis, original two-object model, positive four-RQ program;
2. **paper-visible state:** what an AAAI reviewer sees in `main.pdf`;
3. **evidence state:** what current raw experiments actually authorize;
4. **process state:** whether the orchestrated gate sequence followed the user's one-experiment, phase, Git, reporting, and transition rules.

For every discrepancy, I classify whether it is scientific, writing-only, process-only, or a capability/orchestration issue. Process defects do not retroactively invalidate valid raw results; valid raw results do not cure scientific construct defects.

## Internal-state confirmation of the independent review

The internal frontier strongly confirms, rather than weakens, Nodes 100–300:

- `docs/evaluation.md` explicitly says current RQ1 evidence supports mass conservation, declared-category separation, and association beyond session membership, but **not** semantic intent correctness, causal lineage, developer utility, or the final RQ1 answer.
- It classifies both AgentProcessBench constructions as valid but conjunctively **INCONCLUSIVE** because AP improves while work-to-50 intervals cross zero.
- It records CodeTraceBench as mixed, ToolSafe as contradicted for the tested construction, and AgentNet's intended comparison as invalid because its semantic key dropped the visible target field.
- It closes the same-target AgentProcessBench score branch and prohibits a third variant.
- `docs/background-related-work.md` already recognizes Data Cube/trace-query/pprof lineage, Pivot Tracing, Datadog Patterns, AgentTelemetry, AgentRx/TELBench, Hodoscope, and the need for independent cross-layer responsibility truth.
- WRITE audits already list essentially the same unresolved scientific objections: independent RQ1 attribution, fixed/matched RQ2, actual RQ3 backend coverage, integrated RQ4 cost, and closest-work defense.

The crucial consequence is that the paper-visible result claims are intentionally being carried as ambitious targets, while canonical memory knows that several are not currently authorized. That is acceptable as a work-in-progress state, but it makes the manuscript categorically **not submission-ready**.

## What cycle 0002 accomplished

### Scientific and experimental progress

Cycle 0002 ran substantial real external work rather than toy proxies:

| Branch | Complete population | Validity | Scientific outcome | Durable lesson |
|---|---:|---|---|---|
| CodeTraceBench | 405 source-valid failed targets after full source audit; four coding frameworks | Valid | **Mixed** | Semantic organization beats arbitrary coarsening, but failed-vs-success outcome excess does not identify incorrect steps; AP intervals versus raw/phase cross zero. |
| ToolSafe / TS-Bench | 7,182 released records; 6,786 real tool operations; three families | Valid | **Contradicted construction** | Three-field causal decomposition compresses groups but does not stably beat scalar risk; family and unsafe-only directions reverse. |
| AgentNet | 17,625 trajectories; 339,005 operations; Windows/macOS reciprocal transfer | Valid run; intended comparison invalid for “semantic refinement” | AP adverse, work-to-50 favorable | Dropping `target` destructively merges label-relevant local identity; semantic context must preserve the raw leaf. |
| AgentProcessBench mean risk | 1,000 trajectories; 8,509 steps; four families | Valid | **Inconclusive** | Semantic AP gain +0.031522 with positive interval and shuffle control; work-to-50 +0.016320 but interval crosses zero. |
| AgentProcessBench Wilson-shaped score | same full population | Valid; adaptive reused target | **Inconclusive** | AP gain +0.024515 and all-family favorable work point estimates; work interval still crosses zero; no third variant. |

This evidence is useful. It establishes concrete mechanism boundaries, validates real AgentProf execution and accounting paths, and prevents repetition of target-dropping or unchanged score variants. It does **not** complete RQ2 or authorize the paper's current headline.

### Writing and artifact progress

The active paper became structurally clearer and source-friendlier:

- the exact thesis remains in Abstract, Introduction, and Conclusion;
- Evaluation explicitly announces and organizes the four RQs;
- design requirements are separated from RQs as DR1–DR3;
- operation stacks are described as query-time paths rather than recovered runtime stacks;
- implementation is separated into input reconstruction, taggers, and outputs;
- RQ2 visible/oracle boundaries and statistical-control prose are clearer;
- RQ3 says “applicable” metrics where boundary F1 is unavailable;
- real-world scale wording was corrected to match primary OpenAI sources;
- the AAAI-27 artifact compiles, fits seven content pages plus two reference pages, uses embedded Type 1 fonts, and has no unresolved citations or overfull boxes.

These are real improvements. They do not close the evidence chain or novelty gap.

### Story fidelity

**No scientific-story shrinkage occurred in the final paper.** The permanent Initial Narrative, exact thesis, two-object model, broad quality/safety/cost/waste stakes, and fixed four-RQ program survived. Negative and inconclusive development results stayed out of the reader-facing positive story, as the user required.

The correct classification is therefore:

- **scientific story drift:** no;
- **evidence-to-claim mismatch:** yes, severe;
- **process drift:** yes, material;
- **submission readiness:** no.

## Cycle-level scientific gap

The cycle concentrated almost all empirical work on RQ2, yet the paper still displays the older six-task Table 1 and associated 9.4%/45% claims. None of the five current-cycle branches supplies a complete positive replacement because:

- CodeTraceBench's identification signal fails its outcome null;
- ToolSafe reverses by family and unsafe-only target;
- AgentNet changes information rather than testing a nested refinement;
- both AgentProcessBench variants improve AP but not inspection work with a zero-excluding interval;
- the second AgentProcessBench variant is adaptive on a reused target.

Thus cycle 0002 improved knowledge more than it improved the paper's reader-visible evidence. The next action must change the external evidence source and experimental identification, not run another score tweak or another prose pass.

## Procedural and capability audit

### P1 — Material violation: five experiments ran inside one EXPERIMENT gate

The user requires one experiment per step, one claim per experiment, and at most two modifications before returning to review/writing. Cycle 0002 serially ran CodeTraceBench, ToolSafe, AgentNet, AgentProcessBench mean-risk, and AgentProcessBench Wilson under one EXPERIMENT gate.

Each branch is individually auditable, but the outer orchestration did not stop after one completed result and re-enter paper-level REVIEW. This caused a long local RQ2 search to outrun whole-paper prioritization and delayed RQ1/RQ3/RQ4.

**Capability response, not a skill edit:** the next EXPERIMENT gate admits exactly one RQ, one hypothesis, one external artifact, one reviewed plan, one real preflight, one full matrix, and one result review; it then closes and returns to REVIEW regardless of sign.

### P2 — Material phase violation: full idea and writing loops ran during `BUILD_AND_EVALUATE`

The WRITE gate invoked `iter-refine-ideas` and a full 11-round `iter-refine-writing` run even though the current phase permits evidence work and narrowly targeted writing, not new idea discussion or a full prose loop. Later source-fidelity repairs also edited Abstract/Introduction while describing themselves too broadly as phase-permitted. The final outer audit correctly preserved the useful source fixes but recorded the violation.

**Capability response:** do not invoke idea refinement or a full writing loop in this phase. After the next experiment, permit only a targeted WRITE node tied to newly authorized evidence, closest-work accuracy, and submission mechanics.

### P3 — Gate-order defect: EXPERIMENT did not close before WRITE began

The WRITE gate entered at 07:10. The EXPERIMENT gate's independent outer audit is timestamped 10:54, after the WRITE `999` at 10:39, and no EXPERIMENT `999` report exists in the current directory. Therefore the formal experiment-to-write transition was temporally inverted even though raw branch results are valid.

**Capability response:** a gate's outer audit and one concise `999` report must exist before the next gate entry. This is ordinary transition bookkeeping, not a new freeze/authorization apparatus.

### P4 — Material reporting violation: writing/review used Git and per-node hash snapshots

The user explicitly forbids Git operations in writing/review and says not to perform per-node Git-state audits, hash binding, or freeze protocols. Writing Rounds 8 and 9 ran `git diff --check` and initially falsely reported no Git operation; later corrections preserved the violation. WRITE entry/round/audit reports repeatedly recorded paper, bibliography, PDF, log, auxiliary, and submodule hashes as gate evidence.

The distinction required for future work is:

- **Allowed and scientifically useful:** an ordinary Markdown experiment plan fixes the RQ, hypothesis, source, visible fields, metric, split, and success criterion before target scoring; a source revision/checksum may identify the external dataset actually used; saved raw outputs and independent recalculation establish the result.
- **Unnecessary/prohibited control pattern:** binding every writing/review node to repository or paper hashes, treating digests as authorization, running Git-state checks, or creating seals, packets, manifests, attestations, or freeze ceremonies.

Likewise, a clean prediction-before-label data-flow boundary is a valid scientific control; it does not need a hash-attested packet architecture. Future reports should state inputs, commands, results, and evidence paths in prose/tables and stop there.

### P5 — Report chronology and reviewer freshness were not reliable

The 11 writing rounds cannot be chronologically reconstructed from their timestamps, and a recovery node reports edits not cleanly placed in the supposed serial order. Several CodeTraceBench plan reviews identify the same reviewer rather than demonstrating fresh serial independence. Outer audits correctly found that useful edits/results survived, but provenance claims were overstated.

**Capability response:** record actual start/completion time once per node, never backfill a serial chronology, and use a genuinely fresh reviewer when a protocol calls for one. If chronology is uncertain, say so immediately rather than adding a recovery hierarchy.

### P6 — Repeated low-yield control work crowded out scientific discrimination

The reports exceed roughly fourteen thousand lines for one cycle and contain many repeated source counts, plan locks, invariance checks, build/hash checks, and declarations that thesis/RQs did not change. Much of the experiment-level source and label auditing was valuable; the repetition across multiple plans, reviews, preflights, result reports, and outer audits was not.

The second AgentProcessBench score was within the user's two-modification limit and was transparently classified as adaptive. It nevertheless produced the same scientific state—positive AP, unresolved work interval—as the first. The branch is correctly closed; repeating it would be waste.

**Capability response:** keep one complete node report under the orchestrator contract, reference raw artifacts rather than restating every count, and reserve multiple reviews for material scientific revisions. Use one outer audit, with a repair/audit rerun only when it finds a genuine must-fix.

### P7 — Strong-hypothesis preservation was sometimes confused with result authorization

Writing reports explicitly rejected evidence-calibrated wording because it would “weaken” the positive RQ1 claim, while canonical memory simultaneously says the evidence does not establish semantic intent or causal lineage. The user's instruction is to preserve a strong viable hypothesis and attractive story, not to present an unverified result as established fact.

**Capability response:** keep the exact thesis, positive RQ hypotheses, and broad story; route evidence gaps to stronger experiments; do not insert negative development results. At the same time, a quantitative sentence becomes submission-authorized only when its exact construct and numerator/denominator are supported. The preferred remedy now is stronger evidence, not a smaller hypothesis or another prose hedge.

### P8 — Canonical memory briefly lagged completed branches

The EXPERIMENT outer audit found `docs/background-related-work.md` still describing CodeTraceBench as the next condition and omitting the later branches, creating a repetition hazard. The current file has since been reduced to a concise, accurate frontier with typed outcomes and the third-AgentProcessBench prohibition.

**Capability response:** update the concise frontier once at gate closure, after result review. Do not update it after every child node or duplicate experiment histories into canonical memory.

## Capability-response summary

No skill, AGENTS file, state-machine file, or plugin change is proposed or authorized. The next root run should simply apply these existing capabilities more cleanly:

1. one experiment per EXPERIMENT gate;
2. one ordinary Markdown scientific plan, not a freeze protocol;
3. one real preflight and complete full run;
4. one independent result review and one outer audit;
5. close the gate before entering the next;
6. no Git or node-level hash binding in REVIEW/WRITE;
7. no idea/full-writing loop in `BUILD_AND_EVALUATE`;
8. one concise canonical-frontier update at gate closure.

This is a simplification, not another control system.

## Final scientific verdict

### Recommendation

**Reject in current form for AAAI-27 Main Track; high confidence; incomplete-but-promising.**

### Why

The exact thesis is important and should remain. The plain principle—profile populations of agent activity by recurring semantic responsibility—is attractive. But the submitted paper currently fails four load-bearing tests:

1. operation stacks are not distinguished from established Data Cube/Pivot Tracing/Perfetto/pprof mechanisms or current Datadog semantic resource profiles;
2. RQ1 does not validate cross-layer responsibility and uses a partly circular separation measure;
3. RQ2 does not show improved real-problem localization at matched recall under a frozen external protocol;
4. RQ3 evaluates structured remapping rather than the natural-language tagger, and RQ4 excludes full cold-path cost.

Internal results do not rescue the paper: they correctly remain mixed, contradicted, invalid-as-comparison, or inconclusive. They improve future experiment design but do not authorize the abstract's current positive claims.

### Scientific character

- **Plain-language principle:** treat accumulated agent runs as profiling samples, preserve additive measured effects, and aggregate them under recurring semantic responsibility paths.
- **Challenged belief:** application-level traces and dashboards are sufficient even when responsibility crosses prompts, model calls, tools, processes, and OS effects.
- **Strongest alternative explanation:** conventional multidimensional trace aggregation over curated fields plus task-specific ranking explains the reported gains; AgentProf has not isolated a cross-layer or representation-specific advantage.
- **Classification:** incomplete-but-promising, not complicated-but-shallow; it becomes simple-but-deep only if responsibility conservation and real-problem outcome are validated.

## Largest gaps and strongest opportunity

- **Largest evidence gap:** no fresh, target-blind, same-information RQ2 experiment shows lower inspection work at fixed real-fault localization recall.
- **Largest writing-only gap:** claims conflate responsibility reconstruction, semantic tag derivation, multidimensional projection, and problem ranking, while Related Work understates existing population semantic metrics.
- **Largest claim current evidence almost supports:** **A uniform operation record lets heterogeneous agent telemetry be reprojected into multiple additive population resource views while retaining per-session drilldown as a special case.**
- **Potential larger claim:** **Agent profiling is the semantic continuation of causal tracing: a conserved responsibility record links intent to model, tool, process, and OS effects, then supports query-time resource and failure hierarchies across runs.** This is an evidence target, not a current paper conclusion.

## One highest-value next experiment

### Route

**Next gate: `EXPERIMENT_GATE`. Assigned RQ: RQ2 — real-problem localization.**

Use the official AgentTelemetry benchmark/toolkit and its accepted AIware 2026 protocol. Do not build another custom AgentProcessBench variant and do not reuse any completed current-cycle target for confirmatory scoring.

### One hypothesis

On held-out fault families and held-out agent frameworks from AgentTelemetry, a frozen AgentProf semantic profile reduces the fraction of telemetry inspected to recover official fault-bearing runs/spans at a predeclared fixed macro recall relative to the strongest same-information non-oracle trace/aggregation baseline.

### Why AgentTelemetry wins the selection

- It is an external accepted benchmark/toolkit rather than a home-built variant.
- It spans 14 faults, five observability conditions, seven framework adapters, and six repetitions (2,940 configurations).
- It includes vanilla OTel and OTel+GenAI controls, agent-specific metadata/full views, cost aggregation, decision attribution, and fault-analysis modules.
- It is structurally different from the current custom six-task table and AgentProcessBench score search.
- It simultaneously pressures the AI semantic policy, systems trace representation, and real observability outcome.

The internal WRITE idea discussion suggested ClawTrace/profile-to-intervention. That is an attractive later direction, but its runnable artifact and exact protocol were not independently verified in the source-search node. AgentTelemetry has stronger current source/protocol/artifact grounding and lower risk of becoming another speculative branch.

### Minimal complete experiment contract

1. **Source preflight within this one experiment:** verify the official package/repository can reproduce or export the declared matrix, exposes OTel spans and official fault targets, and provides enough target granularity for the claimed localization unit. If only run-level fault labels exist, either predeclare run triage with exact wording or classify the source as insufficient for span localization; do not manufacture labels.
2. **Split:** predeclare development frameworks and fault families, then test on disjoint held-out frameworks **and** held-out fault families. Human/injected target values do not select fields, scores, thresholds, or fallbacks.
3. **Freeze scientifically, not procedurally:** write one normal Markdown plan fixing tagger/prompt/rules, fields/order/depth, ranker, metric, split, and success criterion. Do not create Git/hash/seal/packet/manifest freeze artifacts.
4. **Same-information baselines:** chronological/native trace; per-session grouping; vanilla OTel; OTel+GenAI; equal-information PerfettoSQL/Data-Cube grouping over every field AgentProf sees; and AgentTelemetry's strongest applicable analysis. Use an oracle only as an upper bound.
5. **Primary metric:** fraction of operations/spans and weighted work inspected to reach 80% macro recall of official fault targets, with the recall threshold fixed before results. If source granularity forces run-level triage, use fraction of runs inspected and state that limitation.
6. **Secondary metrics:** macro precision/recall/F1, first-fault rank when official targets permit it, per-fault/per-framework results, abstention, group count, and cold/warm cost. Report uncertainty over fault × framework cells.
7. **Success:** the interval for inspection-work reduction excludes zero against the strongest same-information non-oracle baseline while the fixed recall target is met. Lower work caused by lower recall is failure.
8. **Terminal behavior:** run the complete approved matrix after one real preflight. Whatever the sign, close the EXPERIMENT gate and return to whole-paper REVIEW. Do not start a second experiment inside the same gate.

### Source-feasibility uncertainty

The main uncertainty is whether the public AgentTelemetry artifact exposes fault-bearing span/first-anomaly identities rather than only run-level fault-detection labels. This is an ordinary source-preflight question. If the source fails that predeclared eligibility condition, record `NOT RUNNABLE FOR CLAIMED GRANULARITY`, close the gate, and return to REVIEW for the next official artifact; do not silently convert the step into a custom dataset.

## Routing after the next experiment

```text
now: EXPERIMENT_GATE
  -> one AgentTelemetry RQ2 experiment
  -> independent result review + outer audit + gate close
  -> whole-paper REVIEW
       -> targeted WRITE only for newly authorized claims, closest-work accuracy,
          reproducibility, and exact RQ wording
       -> sibling evidence gate for whichever of RQ1/RQ3/RQ4 is then most decisive
  -> submission-completion audit only after all four fixed RQs are credible
```

The next targeted WRITE must not be another full prose loop. It should replace or reauthorize quantitative headlines from completed evidence, accurately position Data Cube/Pivot/Perfetto/Datadog/AgentTelemetry/AgentRx/TELBench, separate the four mechanisms in claims, complete reproducibility material, and preserve the exact thesis and RQs.

Submission completion remains blocked by RQ1 responsibility truth, RQ3 actual prompt-tagger accuracy, RQ4 integrated cold/warm cost, reproducibility checklist completion, and a source-grounded novelty comparison. These are stronger-evidence obligations, not permission to shrink the story.

## Alternatives considered and rejected

### RQ3 on CLINC150/MASSIVE now

Scientifically clean and necessary, but it validates only tag accuracy. It would not decide whether the profiler changes a real observability outcome or distinguish AgentProf from current semantic dashboards.

### RQ1 concurrency/injected ownership now

Important for the most defensible systems novelty, but an internal attribution microbenchmark can be dismissed unless coupled to an external operational outcome. It should be a later sibling experiment if RQ2 establishes value.

### AgentRx/TELBench now

They offer strong critical-step/span protocols, but they resemble the current trajectory-localization family and risk another homogeneous benchmark iteration. They remain secondary protocol/baseline anchors.

### ClawTrace intervention now

Potentially highest upside, but source availability and exact official artifacts were not independently verified in this review's primary-source search. It should not outrank a runnable accepted benchmark on internal suggestion alone.

### Writing or idea refinement now

Rejected. Prose cannot create missing evidence, and `BUILD_AND_EVALUATE` does not authorize idea refinement. The original story is already the right one.

## Tree and search-strategy updates

Suggested non-canonical updates for the owning root:

- mark AgentProcessBench score variants closed;
- mark target-dropping semantic keys prohibited unless the comparison explicitly studies information loss;
- retain CodeTraceBench/ToolSafe/AgentNet as typed mechanism boundaries, not paper results;
- add `AgentTelemetry / held-out faults × frameworks / fixed-recall work` as the single selected experiment node;
- attach same-information PerfettoSQL/Data-Cube and AgentTelemetry analysis baselines;
- keep RQ1 responsibility correctness, RQ3 actual tagger, and RQ4 cold/warm cost as sibling blockers for later REVIEW selection;
- preserve `H-alt: cube + curated fields + tuned ranking` as the leading competing explanation.

## Paper and claim impact

No paper edit is authorized by this review. The exact thesis, four RQs, original story, title, model, and positive hypotheses remain intact. The next experiment is meant to earn the bold RQ2 claim, not replace it with a smaller one.

When targeted WRITE eventually resumes, it must distinguish hypothesis from established result without adding negative development history. Current unsupported numbers should be replaced only by complete positive evidence for the same RQ or withheld from a submission until such evidence exists.

## Project-memory updates

No canonical memory, paper, source code, experiment artifact, skill, AGENTS file, or state-machine file was modified. This report only proposes the typed updates and routing above for the owning root to accept or reject after the review gate closes.

## Completion, uncertainty, and next node

All requested review work is complete: blind read, separate systems/AI/bridging source search, post-search full reread, figure/table audit, internal cycle-change audit, procedural/capability audit, final verdict, and one next experiment.

Uncertainty remains about AgentTelemetry's exact public target granularity and importer effort; the one-experiment source preflight resolves it. It does not alter the final current-paper verdict.

**Final route:** `EXPERIMENT_GATE` for the single RQ2 AgentTelemetry fixed-recall experiment. No idea refinement, no full writing loop, no third AgentProcessBench variant, no Git/hash/seal/packet freeze protocol, and no submission-completion claim until the four fixed RQs have credible evidence.
