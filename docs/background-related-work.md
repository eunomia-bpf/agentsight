# Background And Related Work

Last updated: 2026-07-22T00:22:00-07:00
Source/command: claim-oriented web search, primary papers, official artifact
repositories, and full-text checks recorded in the active BOOTSTRAP literature
reports
Completeness: sufficient to bound the six empirical RQs, identify ProcGrep as
the strongest action-only baseline, and admit an RQ1 plan; public-corpus and
model-based metric searches reopen after the local source-coverage result

## Search Log

| Date | Query/source branch | Purpose | Decision |
|---|---|---|---|
| 2026-07-19 | automated Agent diagnosis, trajectory retrieval, intervention, and harness repair | Test the original supervision claim | AgentRx, TrajAudit, AgentForesight, REFLECT, HarnessFix, AgentTether, and AggAgent occupy generic diagnosis, intervention, harness attribution, graph diagnosis, and scalable Raw access. The withdrawn H1/H6 history remains in the step reports. |
| 2026-07-19 | object-centric process mining, software repository process mining, persistent multi-artifact workspaces | Test representation/workspace novelty | OCEL/OCPM, PM4AA/PMAx, and OR-Space establish lifecycle/process structures and persistent workspaces. Do not claim a new IR, lifecycle model, or workspace premise. |
| 2026-07-21 | coding-Agent trajectory empirical studies | Bound action-pattern novelty | ASE 2025, the ICSE behavior study, *Beyond Resolution Rates*, and TRAJEVAL already cover action sequences, validation, context gathering, repeated actions, and coherence collapse. |
| 2026-07-21 | long-horizon and cross-session Agent behavior | Bound longitudinal novelty | HORIZON, AgingBench, and *Plans Don't Persist* establish long-horizon degradation, LLM-judge diagnosis, and context/session effects. The remaining question is observable workspace continuity, not hidden memory state. |
| 2026-07-21 | persistent file workspaces for Agent research | Bound mechanism novelty | AiScientist and FS-Researcher use durable file workspaces as external state. Persistence is a setting, not the contribution. |
| 2026-07-21 | Agent-authored open-source evolution | Bound empirical scope | AIDev and Agentic-PR studies cover very large GitHub PR populations and repository outcomes but lack native reads, transient files, failed validation, and session lineage. |
| 2026-07-21 | *Agent Trajectories as Programs* and official ProcGrep repository | Find strongest tool baseline | ProcGrep `2e8277003dacaa774b5ef61ba150ae03a4f06693` supports local Claude/Codex ingest, canonical actions, learned procedures, fingerprints, JSD/entropy, and exact queries. Its standard spine omits stable artifact identity and cross-session lineage. |

The complete current search, source verification, query revisions, and baseline
handoff are in
`docs/tmp/bootstrap/step-0001-20260719T181243-0700/literature-20260721T235934-0700/literature-report.md`.
Earlier intervention searches remain preserved in their timestamped literature
reports but no longer define the current frontier.

## PDF Corpus

| Work | Local PDF/source | Verification | Why retained |
|---|---|---|---|
| Understanding Software Engineering Agents | `https://software-lab.org/publications/ase2025_trajectories.pdf` | Primary author publication page and PDF verified | Closest action-sequence, repeated-action, and validation-pattern empirical precedent. |
| TRAJEVAL / Coherence Collapse | `docs/reference/2026-kim-trajeval.pdf` | Full PDF checked | Intermediate useful state, overwrite, rework, and stage-metric precedent. |
| Beyond Resolution Rates | `docs/reference/2026-mehtiyev-behavioral-drivers.pdf` | Full PDF checked | Task/model confounds and validation/context behavior over 9,374 traces. |
| Agent Trajectories as Programs | `docs/reference/agent-trajectories-programs.pdf` | arXiv and official repository verified | Strongest action-only procedure/query/fingerprint baseline. |
| HORIZON | `https://arxiv.org/abs/2604.11978` | Primary arXiv verified | Cross-domain long-horizon diagnosis and bounded LLM-judge precedent. |
| AgingBench | `docs/reference/2026-zhu-agent-aging.pdf` | Full PDF checked | Multi-session degradation and longitudinal analysis precedent. |
| Plans Don't Persist | `docs/reference/2026-mehta-plans-dont-persist.pdf` | Full PDF checked | Context-loss mechanism boundary. |
| AiScientist | `https://arxiv.org/abs/2604.13018` | Primary arXiv verified | Durable workspace mechanism boundary for autonomous research. |
| OR-Space | `docs/reference/2026-zhou-or-space.pdf` | Full PDF checked | Persistent heterogeneous-artifact workload precedent. |

## Claim-Oriented Novelty Map

| Plain claim | Closest work | Same-claim risk | Current disposition |
|---|---|---:|---|
| Agent actions reveal useful behavior beyond final success. | ASE/ICSE studies, TRAJEVAL, HORIZON | High | Reject as novelty. |
| Edit loops, validation gaps, or behavior fingerprints diagnose Agents. | ASE study, Beyond Resolution Rates, TRAJEVAL, ProcGrep | High | Reuse metrics or compare; do not claim discovery in general. |
| Persistent file workspaces help long-horizon Agents. | AiScientist, FS-Researcher, OR-Space | High | Treat as premise and setting. |
| Deterministic procedure queries outperform LLM trace reading. | ProcGrep | High | Reject blanket claim; run a fact-class comparison. |
| Git/PR metadata omits native Agent process. | AIDev and Agentic-PR studies | Low novelty and low centrality | Use only as an observability contrast. |
| Days-long activity should be measured through artifact durability, reuse, validation association, rework, and re-grounding across native session resets. | TRAJEVAL, AgingBench, Plans Don't Persist | Medium | Retain as central empirical question; test in complete persistent-project lineages. |
| Stable artifact identity and cross-session lineage add source-verifiable fact coverage beyond standard action-only procedures. | ProcGrep, OCEL/OCPM | Medium | Retain as narrow RQ7; compare with official ProcGrep and include facts it should answer. |
| Skill/harness use causes progress or waste. | HarnessFix and harness-optimization work | High without control | Do not claim causality from local cases; report temporal association only. |

## Closest Work

| Work | Existing result/method | Gap relevant to this project |
|---|---|---|
| Bouzenia and Pradel, ASE 2025 | 120 repair trajectories; action distributions, 4-grams, repeated behavior, testing, qualitative reasoning analysis | One benchmark attempt is the unit; no persistent artifact lineage across independent native sessions. |
| Beyond Resolution Rates | 9,374 trajectories; validation/context behavior with task/model confound analysis | No artifact survival or session re-grounding in continuing projects. |
| TRAJEVAL | 16,758 traces; intermediate correctness, overwrite, search/read/edit metrics, thrashing | Reference-patch attempts rather than open-ended multi-artifact project evolution. |
| ProcGrep | Canonical action atoms, learned procedures, fingerprints, deterministic queries, local Claude/Codex adapters | Standard action spine drops stable path/artifact identity and cross-session lineage; matcher lacks temporal windows and variable binding. |
| HORIZON | 3,100+ long-horizon trajectories and LLM-as-judge failure attribution | Generic diagnosis is occupied; no persistent workspace-evolution measurement and uses semantic judge/human validation excluded here. |
| AgingBench and Plans Don't Persist | Session-scale aging and plan-signal decay | Study internal/context reliability rather than observable artifact re-grounding and progress. |
| AiScientist and FS-Researcher | Durable file workspaces improve autonomous research systems | System construction and outcomes, not an observational study of artifact progress, rework, and continuity. |
| AIDev / Agentic-PR studies | Large-scale Agent-authored PR outcomes and metadata | No native action-time reads, transient artifacts, validation timing, or session lineage. |

## Mandatory Baselines

| Baseline | Official artifact/version | Input information | Role and fairness |
|---|---|---|---|
| Final workspace/diff | Git and filesystem commands pinned with the study revision | Final bytes/tracked state only | Lower-information control; should answer final-state facts. |
| Aggregate Counts | Same admitted actions, paths removed after counting | Action/category/session totals | Lower-information control for the belief that activity telemetry is sufficient. |
| ProcGrep | `hamidahoderinwale/procgrep@2e8277003d...` | Official standard action representation from supported native logs | Strongest runnable action-only baseline; should tie or win action-only facts. Report any adapter boundary rather than substitute a homemade n-gram. |
| Bounded Raw-log LLM | Frozen model, source membership, retrieval/context/output budgets | Same native records without artifact-linked convenience | Requested comparison of on-demand reconstruction; not truth. Must cite sources or abstain. |
| Artifact-linked trajectory | Current `agent-session` plus thin repository projection | Same source universe plus deterministic identity/effect/session relations | Proposed measurement. May claim only incremental fact coverage at comparable accuracy and reported cost. |

## Experimental Precedents And External Assets

| RQ | Reused precedent | Reused design element | Required correction |
|---|---|---|---|
| RQ1 | TRAJEVAL; software survival analysis | Intermediate-to-final survival and outcome-independent process measurement | Separate file-level durability, reuse, and validation association; no opaque weighted score. |
| RQ2 | ASE study; Beyond Resolution Rates | Test-after-edit and validation investment | Use native effect/status and call it association, not test coverage. |
| RQ3 | TRAJEVAL; ProcGrep | Repeated patterns and edit/validation cycles | Preserve artifact identity; report distributions and sensitivity, not one thrash cutoff. |
| RQ4 | AgingBench; Plans Don't Persist | Boundary-aligned longitudinal analysis | Measure pre-mutation re-grounding and prior-artifact overlap; do not infer memory. |
| RQ5 | ProcGrep; process mining | Procedure distribution, transitions, entropy/JSD | Separate action-only variation from artifact/module attention. |
| RQ6 | Beyond Resolution Rates; HarnessFix | Model/framework confounds and harness-visible mechanisms | Observational association only in local cases. |
| RQ7 | ProcGrep episodic search; HORIZON judge | Exact queries, bounded model reader, fact accuracy/cost | Independent source-verifiable facts; no human/LLM semantic gold. |

The fixed first assets are six local repositories with native Agent sessions:
AgentSight, ActPlane, bpf-developer-tutorial, eunomia.dev,
agentskill-observability-paper, and academic-writing-skills. They are supporting
case evidence. Public AIDev-style corpora and prospective trace capture are
external-validity candidates after the source audit identifies stable metrics.

## Adjacent Communities

| Community | Relevance | Absorbed constraint |
|---|---|---|
| Empirical software engineering / MSR | repository evolution, survival, developer/Agent behavior | Separate case findings from method contribution and control repository/task confounds. |
| Process mining / OCEL | object lifecycles, transition and conformance analysis | Do not rename established lifecycle/event machinery as novelty. |
| Dynamic graph visualization | temporal stability and mental maps | Layout is an auxiliary interface, not a measurement claim. |
| AI-agent evaluation | long-horizon diagnosis, trajectory judges, behavioral fingerprints | Use objective source facts and strongest official procedural baseline. |

## Venue Evaluation Patterns

AAAI is plausible if the paper contributes consequential empirical knowledge
about long-horizon Agent behavior and a validated measurement capability, not
only a polished visualization. A competitive full paper needs a source-audited
corpus, strong process baselines, uncertainty/confound analysis, and external
validation beyond six author-associated local cases. AAAI Demo is a secondary
route for the standalone Agent Nebula artifact but cannot substitute for the
empirical and measurement evidence.

## Must-Read List

1. Understanding Software Engineering Agents (ASE 2025).
2. Beyond Resolution Rates.
3. TRAJEVAL / Coherence Collapse.
4. Agent Trajectories as Programs / ProcGrep.
5. HORIZON.
6. AgingBench and Plans Don't Persist.
7. AiScientist and FS-Researcher.
8. AIDev and Agentic-PR studies.
9. Object-centric process mining and PM4AA/PMAx.

## Novelty Verdict

- **Overall risk:** high for generic trajectory, motif, validation-gap,
  fingerprint, persistent-workspace, and deterministic-search claims; medium
  for longitudinal artifact progress across independent native sessions.
- **Surviving empirical position:** activity volume is not itself a process
  measure. Study durability, later reuse, successful-validation association,
  rework, attention, and observable session re-grounding as separate dimensions.
- **Surviving tool position:** stable artifact identity and session lineage may
  add source-verifiable fact coverage beyond ProcGrep's action-only spine; it is
  not a new general event or procedure language.
- **Required scope discipline:** local cases support deep descriptive findings,
  not population rates or skill/harness causality. Broad AAAI claims require an
  independent public or prospective corpus.
- **Next action:** review and run RQ1 over every qualified native session in the
  six fixed repositories, then use its source-coverage result to freeze RQ7's
  stratified fact set. ProcGrep must be run officially for action-only facts.
