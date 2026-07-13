# AgentProf Idea-Regression Audit And Recovery Plan

## Context

- **Created:** 2026-07-12T02:17:23-07:00
- **Cycle:** `cycle-0001-20260711T164850-0700`
- **Gate/node:** REVIEW / idea-regression recovery
- **Status:** active plan; no paper or canonical-document recovery edits have yet been made under this node
- **Decision:** restore the paper's simple, ambitious scientific center without restoring claims contradicted by real experiments, then resume the research loop with one decisive experiment at a time.

The user observed that the idea had become smaller and less interesting while the paper accumulated more mechanisms, contracts, controls, and evidence obligations. This node determines whether the skills and their execution trajectory created that regression, separates valid scientific corrections from reviewer-driven accretion, and defines how to recover the project without editing the current shared skills.

## Authority, Scope, And Frozen Files

The active authority is the user's instruction to preserve a bold research objective, avoid conservative narrowing, use real published work and real systems or benchmarks, complete experiments rather than stop at smoke tests, avoid branch switching, and now recover the original idea while updating the paper and all related project documents.

This recovery may edit:

- `docs/paper/`;
- `docs/idea-story.md`;
- `docs/evaluation.md`;
- `docs/design.md`;
- `docs/implementation.md`;
- `docs/background-related-work.md`;
- `docs/user-instruction.md`, but only to restore a verbatim user-authored prompt log;
- timestamped Markdown reports under this node;
- experiment code and raw-result paths only after an approved experiment plan exists.

The following remain frozen:

- `docs/agentpprof-paper/` is read-only and must not be edited, reset, cleaned, staged, committed, or otherwise mutated;
- every current skill in `/home/yunwei37/workspace/my-paper-work/academic-writing-skills/`, including writing and non-writing skills;
- current Git branches; no branch may be created or switched;
- admitted raw experimental outcomes, including negative results.

The skills repository receives no edits, staging, commits, or pushes. Skill-level risks and possible future improvements are analysis findings only.

## Evidence Coverage

| Stratum | Source | Coverage used here | Valid use | Limitation |
|---|---|---|---|---|
| Current Codex parent session | `~/.codex/sessions/2026/07/11/` and current task lineage | One paper-recovery parent session, approximately 58.8 MB and 15,017 parsed records in the prior trajectory audit | Ordering user corrections, orchestrator decisions, delegated work, and file changes | A single parent task is not cross-project evidence for globally changing a skill |
| Codex delegated sessions | Same Codex source root, preserved parent-child lineage | 34 paper-relevant children: 2 bootstrap audits, 17 experiment, 5 idea, and 10 writing sessions | Comparing stage behavior and locating where mechanisms entered the paper | Children are repeated trials within one task, not 34 independent user tasks |
| Claude project history | `~/.claude/projects/-home-yunwei37-workspace-agentsight-research-semantic-flamegraph/` | 9 parent and 62 child sessions from 2026-07-06 through 2026-07-09 in the prior audit | Reconstructing the earlier idea, implementation, and review history | Different runtime and earlier skill versions; conclusions must preserve chronology |
| Current cycle reports | `docs/tmp/cycle-0001-20260711T164850-0700/` | 41 Markdown reports, approximately 272 KB before this node | Primary auditable record of plan growth, idea attacks, writing rounds, and admitted results | Reports can repeat reviewer interpretations; raw results outrank their verdicts |
| Canonical project documents | `docs/{idea-story,evaluation,design,implementation,background-related-work}.md` | Complete current files | Detecting stale authority, contract accumulation, and paper/document drift | Several files are history dumps rather than current frontier documents |
| Current and prior paper sources | `docs/paper/main.tex`, read-only `docs/agentpprof-paper/main.tex`, and `docs/tmp/agentpprof-paper-zh-20260711/source/main.tex` | Complete paper sources | Comparing the original scientific center with the current proposal-like paper | The old paper contains positive empirical language that later evidence may contradict |
| Raw/current experiment evidence | Active cycle result reports and linked artifacts, especially `loop-rq2-00/result-review.md` | Complete admitted RQ2 revision-0 result | Preserving valid negative evidence and rejecting unsupported positive claims | It tests induced semantic leaves, not every possible operation-stack construction |
| AgentSight databases | Locally available AgentSight sessions ending 2026-06-13 | Checked previously for overlap | Establishing that they do not cover the 2026-07-11 paper cycle | Cannot serve as source-native observation of the current cycle |

No aggregate percentage in this report treats child reviewers as independent projects. Reviewer verdicts are diagnostic evidence only. Raw experiment outputs, source paper text, and direct user corrections have higher authority.

## Observed Regression

### Original scientific center

The original work is organized around two compact profiling abstractions:

1. an **operation**, a fielded and weighted observation of agent behavior; and
2. an **operation stack**, a query-time recursive frame sequence derived from operation fields.

The memorable scientific challenge is that an agent trajectory's execution tree records where events happened during one run, but that tree is not necessarily the best index for finding behavior that recurs across runs. A semantic profiling view can reorganize recorded behavior by reusable meaning while retaining weighted context.

This is a broad position about the diagnostic index for agent behavior. It does not require a separate stable-identity contribution, a navigator contribution, a bundle-emulation contribution, or a new cost taxonomy to be interesting.

### Current regressed state

The current paper repeatedly presents frozen stable identity, semantic scope trees, a cross-run-prior navigator, best-matched policies, exact bundle emulation, and several cost classes as obligations of the target system. It openly admits that central pieces are unimplemented. The paper therefore grew nominally broader while the implemented and supported contribution became smaller: the original profiling abstraction is treated as substrate, and reviewer-created mechanisms occupy the scientific center.

The current canonical documents amplify this state. `docs/evaluation.md` is approximately 360 KB and contains large amounts of gate, packet, freeze, hash, checker, and recovery machinery. `docs/idea-story.md` still points to an older G0--G8-style recovery. `docs/design.md` and `docs/implementation.md` include experiment/checker history instead of only the current mechanism and artifact reality. These documents can cause a resumed agent to reconstruct obsolete constraints as current scientific truth.

## Causal Findings

### F1 — Reviewer objection accretion became mechanism design

The old idea loop used repeated attacks and re-attacks. Each objection was treated as something that had to be made true inside the paper rather than classified as one of: fatal counterexample, evidence need, optional robustness, alternative explanation, or future work. Concrete trajectory transitions include:

- SQL/grouping equivalence objection -> stable cross-run identity;
- SDBL/local-scope objection -> frozen cross-run prior;
- attention objection -> multiple cost classes;
- point-coverage objection -> change of primary outcome;
- bundle-equivalence objection -> navigator demotion plus exact bundle-emulation control;
- leakage objection -> frozen identity and tree membership contracts.

This is primarily `concept_churn`, `claim_evidence_drift`, and `checker_theater`. The old execution pattern optimized for surviving every reviewer attack, not for preserving one explanatory principle.

### F2 — Experiment review had no simplicity pressure

RQ2 revision 0 completed a real experiment and returned a scientifically useful negative result. Revision 1 then expanded into a roughly 470-line plan, about eleven comparator types, five serial review rounds, and estimated 100--300M tokens plus 24--96 GPU-hours. The fifth review still returned `REVISE`, and no real preflight or full run followed.

Each reviewer could add a scientifically plausible comparison or control, but the process lacked a rule that the plan must resolve one decisive uncertainty with one primary outcome and a minimal set of strongest comparators. As a result, plan review increased surface area faster than it resolved blocking validity defects. This is `premature_downstream_work`, `skill_bloat` in the instantiated plan, and `outcome_blindness` because review completeness displaced real execution.

### F3 — The negative result was interpreted too broadly and then compensated with new machinery

The valid result showed that the tested induced semantic leaves did not significantly beat prevalence on AgentRx or TELBench, with width-only stronger on TELBench. It invalidates a positive leaf-localization claim for that setup. It does not by itself invalidate all multi-resolution operation stacks or the larger claim that execution trees are not always the best diagnostic index.

Instead of preserving this distinction, the trajectory attempted to rescue a positive story by specifying stable identities, whole-scope navigation, transfer, and cost-normalized controls. That changed the method before evidence existed. The correct response is to keep the negative result, restore the broad scientific question, and design a new experiment that directly discriminates execution-tree indexing from a frozen cross-run semantic profile.

### F4 — Writing faithfully propagated the upstream problem

The writing loop did not invent the mechanisms. It improved structure, consistency, terminology, and claim tone while correctly exposing unimplemented components and unanswered RQs. Its success made the proposal-like state internally coherent. This is not a writing-stage failure, and no writing skill should change.

### F5 — Canonical-document bloat made obsolete recovery machinery authoritative

The project paper should hold the current scientific story, while canonical documents should hold concise current frontiers and timestamped reports should hold history. Instead, large history/checker documents remained in canonical locations. On resume, an agent reading them could reasonably infer that frozen packets, G0--G8 recovery, hash bindings, or extensive checker protocols remained required. This is `stale_state_edit` risk and `premature_downstream_work` encoded as project memory.

## Current-Skill Assessment Without Modification

The current `iter-refine-ideas` is materially improved relative to the version that generated this trajectory. It now requires three open research discussions, explicitly rejects repeated reviewer attacks, forbids narrowing for easy defense, distinguishes discussant input from edit authority, rejects non-core concept stacking, and stops after three rounds rather than iterating until reviewers approve. Used as written, it should reduce the direct mechanism-accretion failure.

The current orchestrator also contains important anti-drift rules and places scientific synthesis in the idea skill. The current literature and full-paper review skills explicitly search for larger framing and prohibit default claim shrinkage. These are directionally correct.

Residual recurrence risks remain even without editing the skills:

1. `research-experiment-design` says to review until no blocking defect remains but does not explicitly require the reviewed plan to become simpler or cap each experiment at one decisive uncertainty, one primary outcome, and a minimal comparator set. A project-level reviewer can still label many optional controls as blockers.
2. `iter-review-critique` asks for every major issue and a decisive experiment but does not force a ranking of exactly one fatal scientific objection versus optional robustness. A caller can still promote all major findings into one next experiment.
3. The orchestrator's detailed reporting and outer-audit requirements are useful for provenance but can become process theater if node boundaries follow shell actions or reviewer comments instead of meaningful scientific decisions.
4. An untracked progress-monitor script in the skills repository increases maintenance surface and is not needed to recover this paper. Because the current skills are frozen, this report records the concern but does not remove or alter it.

These are project-level risk controls for this recovery, not proposed skill edits. The evidence comes mainly from one parent research project, so it supports a local recovery procedure and future cross-project evaluation, not automatic global promotion.

## Recovery Invariants

1. **Restore the scientific question, not disproven answers.** The paper may again center operation and operation stack, but it must retain the negative induced-leaf result and must not revive unsupported localization wins.
2. **One plain-sentence center.** A reader must be able to state the paper without project-coined terms: an execution tree is not necessarily the best index for diagnosing behavior that recurs across agent runs.
3. **Two core abstractions at most.** `operation` and `operation stack` may remain if the idea discussions find both load-bearing. Stable identity, navigator, scope tree, bundles, and cost categories are mechanisms, experimental choices, or future hypotheses unless implementation and evidence elevate one later.
4. **Implemented/evidenced distance is explicit.** Contributions must distinguish implemented profiling substrate, observed empirical results, and future experiments. The current contribution list cannot be dominated by unimplemented target mechanisms.
5. **Negative evidence narrows an answer, not automatically the problem.** A failed method triggers a competing construction or discriminating experiment before any reduction of the paper's central problem.
6. **Reviewer suggestions are classified.** Every concern is marked fatal scientific defect, required validity repair, optional robustness, alternative explanation, or future work. Only the first two enter the immediate experiment.
7. **One experiment, one decisive uncertainty.** The next experiment uses one primary outcome, the strongest minimal baselines, real public assets, and a complete run. It cannot become a venue-sized matrix before the first decisive result exists.
8. **Current state stays concise.** Canonical documents contain only the current frontier. Superseded machinery moves to the timestamped archive and remains linkable for provenance.
9. **No human wait state.** Uncertainty is recorded with the chosen default and revisit trigger; the loop continues with the highest-information safe action.

## Document Recovery Procedure

Before rewriting canonical files, preserve exact copies under a timestamped archive inside this node. Archive at least:

- `docs/user-instruction.md` because it currently contains assistant-authored summaries rather than a strictly verbatim prompt log;
- `docs/idea-story.md`;
- `docs/evaluation.md`;
- `docs/design.md`;
- `docs/implementation.md`;
- `docs/background-related-work.md`.

Then rebuild:

- `docs/user-instruction.md` from relevant verbatim user messages only;
- `docs/idea-story.md` as the current one-sentence center, core abstractions, competing explanations, admitted negative result, unresolved decisions, and short dated evolution summary;
- `docs/evaluation.md` as the current RQs, admitted results, raw artifact links, next one-experiment plan, and open uncertainty;
- `docs/design.md` as the current operation/operation-stack model, mapping/aggregation semantics, implementation boundary, and candidate future mechanisms clearly marked as such;
- `docs/implementation.md` as only what exists, how to run it, artifact boundaries, and known gaps;
- `docs/background-related-work.md` as a concise claim-oriented map of closest profiling, agent-debugging, trace-abstraction, and benchmark work, with verified primary-source links and baseline implications.

Do not delete timestamped cycle reports or raw results. They are the historical archive. Do not move or edit the read-only paper submodule.

## Idea And Paper Recovery Procedure

Run the current `iter-refine-ideas` exactly as written, using three fresh serial discussants. Each discussant reads the complete current paper, the read-only original source, the archived Chinese source, the admitted negative result, the cleaned verbatim user instructions, and the current idea story. Do not show prior reviewer verdicts or this plan's preferred final wording as an expected answer.

The three questions remain:

1. What is the largest, most interesting, and most faithful version of the idea?
2. What academic architecture and system direction follow if that position is true?
3. What published work and real experimental evidence would make researchers believe, limit, or change it?

After every round, the main agent records accepted, rejected, combined, and unresolved suggestions; edits the paper and idea story; and compiles the paper. A round is rejected and repeated if it introduces new central mechanisms merely to answer reviewer objections, hides the negative result, narrows the user objective, or makes unimplemented behavior a present contribution.

The resulting paper should normally contain two to five explicit RQs. The exact count and wording are outputs of the discussions, not fixed by this plan. Evaluation must be organized by those RQs, and every RQ must have an evidence-backed answer or an explicit unresolved experiment need.

## Independent Recovery Audit

After the three discussions and paper edit, a fresh reviewer receives the recovered paper, verbatim user instructions, original source, admitted result, and canonical documents, but not the desired verdict. It checks:

- whether the plain-sentence idea is at least as ambitious as the original;
- whether the paper has become simpler rather than merely shorter;
- whether every current contribution is implemented, evidenced, or explicitly proposed;
- whether the valid negative result is preserved without overgeneralization;
- whether stable identity, navigation, bundles, freeze rules, and cost taxonomies remain only when scientifically load-bearing;
- whether the paper, idea story, evaluation, design, implementation, and related work describe the same current state;
- whether stale gate/checker machinery can still control a resumed agent.

Must-fix findings are repaired and the audit is repeated until no must-fix remains. Reviewer comfort, exhaustive robustness, and optional comparisons do not block the recovery.

## Next Decisive Experiment

Only after the idea recovery determines the RQs, select one paper-level RQ and one uncertainty. A likely high-information comparison is:

- freeze a semantic mapping/profile on development trajectories;
- use one untouched real public benchmark family;
- compare flat/per-step ranking, the source-native execution tree, and the frozen cross-run semantic profile;
- add at most one matched or shuffled semantic control if needed to distinguish semantic grouping from arbitrary grouping;
- use one benchmark-native diagnostic outcome under matched visible information and a declared cost budget;
- run every planned cell and repetition to completion.

This is a candidate, not a pre-authorized plan. Literature grounding and the recovered RQ determine the exact benchmark, metric, and baseline artifacts. The plan review may repair validity, but it may not append unrelated RQs, multiple new mechanism contributions, or a comprehensive venue matrix. A materially different scientific question returns to idea synthesis rather than expanding this experiment.

## Completion Conditions

This recovery node completes when:

1. skills have been audited read-only and no skills-repository file was changed by this recovery;
2. obsolete canonical documents are archived and concise current versions replace them;
3. all three idea discussions and main-agent dispositions are recorded;
4. the paper and idea story restore a simple, ambitious, falsifiable center while preserving admitted negative evidence;
5. the paper compiles and an independent audit has no must-fix finding;
6. one next decisive real experiment is selected from an explicit paper RQ with a concise Markdown plan ready for scientific review.

The broader research cycle then resumes at EXPERIMENT rather than continuing to polish an incomplete proposal.
