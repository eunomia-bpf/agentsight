# Experiment Plan: RQ5 Explicit Skill And Instruction Footprints

## Research Question
- RQ exactly as written in the revised candidate contract: What source-explicit process footprints can be attributed to named Skill invocations, are repeated named-skill footprints more similar than matched different-skill episodes, and what focal activity follows explicit instruction-read events?
- Specific uncertainty tested here: whether complete native records support exact, unambiguous Skill attribution and whether named Skill mechanisms leave stable action/artifact footprints beyond root-session context. Instruction reads are analyzed separately because they have no equivalent attribution boundary.
- Why the answer matters: it directly tests the user's concern that a skill or harness may induce document-heavy, test-heavy, or otherwise distorted work without pretending that such a footprint is automatically waste or causal harm.

## Paper-Value Admission
- Planned role: decisive correction and supporting empirical finding.
- Largest credible paper story this experiment could unlock: in these observed contexts, source-attributed named Skills have bounded, repeated workspace footprints across independent native root sessions.
- Strongest reviewer reject argument or load-bearing uncertainty addressed: the earlier study reported N/A because its own exporter dropped source-native Skill arguments; alternatively, any apparent signature may be project/task leakage from a small self-selected corpus.
- Independent evidence added beyond existing runs and published results: exact source-native invocation names/arguments/attribution, native root-session and nested-stream identity, separately defined instruction focal events, artifact-class lineage outcomes, and root-session-blocked distance tests.
- Why the result is not tautological, already settled, or dominated: a Skill call existing is tautological; a repeated named skill having a source-grounded, cross-context footprint distinguishable from matched other episodes is not. Generic ProcGrep fingerprints do not segment on explicit Skill/instruction mechanisms or retain artifact lineage.
- Paper decision if positive: retain RQ5 as descriptive evidence that mechanism use is recoverable and behaviorally structured; use specific footprints only as hypotheses for later controlled harness experiments.
- Paper decision if contradictory, mixed, or inconclusive: report exact coverage and footprint heterogeneity, remove any repeatability claim, and keep only qualitative case navigation with no “skill effect” language.
- Best alternative experiment and why this one has higher decision value: a prospective randomized skill ablation would support causality, but it would no longer study the existing natural long-running work and would require new tasks/runs. The current source correction is necessary before designing such an intervention.

## Expected And Alternative Outcomes
- Current expected answer: a qualified subset of explicit invocations has an unambiguous attribution-linked footprint; common named Skills show some recurring action/artifact composition, but between-project variance remains large and causal usefulness is not identifiable.
- Strongest competing explanation: skill name is a proxy for project, task, model, or development phase, so same-name similarity disappears after project/session matching.
- Result that would contradict the expectation: source joins fail, explicit episodes have insufficient repeated cross-context support, or matched same-skill distances are no smaller than different-skill distances.

## Published Precedent And Real Assets
- Closest published protocol: ProcGrep's within-group noise floor/JSD and controlled procedural comparisons; Beyond Resolution Rates' task/model confound discipline; HarnessFix for source-visible harness mechanisms.
- Official system/model/data/benchmark/tool and version: complete local Claude/Codex/Gemini native records through one declared cutoff; current `agent-session` and repository projection; ProcGrep `2e8277003dacaa774b5ef61ba150ae03a4f06693` only for action-atom sensitivity, not as the data source.
- What is reused: exact native tool-call order, source call IDs, action atoms, JSD/permutation reasoning, stable artifact identity/classification, and recognized validation adapters.
- Necessary deviations or custom glue: extend the existing `agent-session` and repository types—without a new IR—to retain exact Skill name/arguments, attribution, native root-session ID, source-stream/file ID, agent/subagent ID, native event and parent-event IDs, model, source role, prompt/turn boundary, and original Tool paths. Display-oriented `command` remains separate and may stay truncated.

## Comparison
- Proposed system or method: one explicit `Skill(S)` invocation anchors a Skill footprint; the primary footprint contains only subsequent Tool events in the same native root session and source stream whose source-native `attributionSkill` equals `S`. A later explicit Skill invocation or attribution change closes ambiguity. Invocation or attribution rows without a unique one-to-one join enter coverage only. Instruction reads are successful focal events, never Skill episodes or proof of harness exposure; their following activity may be summarized only to the next native prompt/turn boundary. Instruction mutations remain a separate event class.
- Null controls and the competing position each represents: (1) root-session aggregate composition, representing “the Skill-conditioned subset adds no local structure”; (2) eligible different-Skill footprints restricted by project, vendor, model, source role and pre-invocation prompt/turn position, representing observed task/phase context. These are null controls, not product baselines.
- Why each null needs a matched run instead of citation alone: similarity and support depend on this corpus's projects, Skills, source versions, nested-agent structure and session composition.
- Controls or ablations, labeled separately: action-only features; artifact-only features; boundary-only membership for unambiguous invocations as a sensitivity analysis; exclude single-project support; leave-one-project-out. Boundary-only rows never contribute to the primary repeatability conclusion.
- Conclusion if each null matches or wins: no stable named-Skill footprint claim; retain exact coverage and heterogeneous per-case descriptions only.
- Information, tuning, and compute fairness: every primary comparison uses only uniquely attribution-joined calls. Matching and label permutations use pre-invocation fields only; observed footprint length may be shown as an outcome and used only in an explicitly labeled sensitivity analysis.
- Split or leakage rule when relevant: the independent block is `(project, vendor, native_root_session_id)`, not the session file. Nested subagent streams remain inside that root block. Qualifying repeatability requires at least three different root sessions and at least two Skill names in the eligible control stratum. Cross-project wording additionally requires the same Skill to qualify in at least two projects. Features and labels are first aggregated within root-session/Skill; permutations are restricted by project/vendor/model/source role. Skill arguments are never input features.

## Workloads And Metrics
- Real workloads or tasks: all source-eligible records for the six fixed natural projects through a fresh cutoff, not the 72-session RQ7 subcorpus. Claude explicit Skill calls and attribution, plus all-vendor exact successful reads and mutations of `AGENTS.md`, `CLAUDE.md`, and `SKILL.md`. Repository-direct and global source streams are reported separately because surrounding no-path calls are not equally observable in the current projection.
- Primary metrics: invocation/orphan/join coverage; root-session and nested-stream support; action/effect and artifact-class composition; mutation/read/recognized-validation shares; path transition mix; later same-root-session and later-root-session reuse of footprint-touched artifacts; Jensen--Shannon distance between root-session/Skill aggregates; matched same-Skill minus different-Skill distance under restricted root-session-block label permutation. Instruction focal events receive separate source counts, next-turn action/artifact composition and reuse coverage, never pooled Skill distances.
- Correctness check or ground truth: independent recomputation directly from immutable native source lines and call IDs for every Skill invocation, every attribution row, every instruction read/mutation, every root/stream join, and every episode boundary; row-count, call-order and artifact-join invariants must all reconcile.
- Repetitions, seeds, and uncertainty: deterministic extraction; 10,000 restricted root-session-block permutations with fixed seed 20260722; project-level leave-one-out sensitivity; exact support counts and intervals only where the root-session resampling unit is defensible.
- Cost estimate when material: local parsing and plotting only; expected under two minutes and under 2 GiB RAM based on the prior six-project run.

## Planned Runs
| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| source preflight | dependency | one AgentSight session with Skill, one Codex instruction read, one no-signal session | enhanced `agent-session` + repository join + independent source checker | 1 | Any field/join/boundary mismatch blocks the full run. |
| six-project full | proposed | all qualified source records through cutoff | exact attribution-linked Skill footprints plus separate instruction focal events | 1 | Provides coverage and descriptive footprints. |
| matched null | null control | supported root-session/Skill aggregates | pre-invocation-restricted different-Skill labels within project/vendor/model/source-role strata | 10,000 permutations | Tests repeatability against observed contextual heterogeneity without a causal interpretation. |
| action-only ablation | ablation | identical episodes | action/effect features only | 1 | Bounds incremental descriptive value of artifact linkage. |
| membership sensitivity | ablation | uniquely joined Claude invocations | primary attribution membership vs next-Skill/prompt-boundary membership | 1 | Large disagreement restricts claims to exact source attribution only. |

## Execution
- Authoritative command or workflow: extend the existing Rust types minimally, run `cargo test` for `agent-session` and `agentvis`, execute one fresh six-project source projection, then run a focused Python RQ5 analyzer/plotter. The exact command and cutoff are recorded before interpretation. The projection must preserve full surrounding Tool events for repository-direct streams; global streams with only repository-linked events remain a separate coverage stratum unless the full source stream is unambiguously joined.
- Real preflight case: a native Claude Skill call whose arguments exceed the old 300-character display limit and has attributed Tool calls; a nested subagent stream sharing its root `sessionId`; a Codex `SKILL.md` read with a native prompt/turn boundary; one orphan attribution; and one no-signal root session.
- Full completion rule: all six projects parsed; exact full-source checker passes; every primary Skill footprint has one unambiguous invocation/root/stream join; orphan invocation/attribution and nested-stream counts are reported; eligibility gates are enforced as N/A; all tables reconcile; F7 PDF/PNG render and pass visual inspection; a fresh reviewer audits result/claim alignment.
- Raw-result path: this experiment directory under `raw/`, `figures/`, `result.md`, and `commands.log`; private source excerpts remain outside committed release artifacts.
- Checkpoint or recovery approach: extraction, source audit, metric tables, permutation output, and plotting are separate deterministic commands; existing immutable Step 0002 results remain untouched.

## Interpretation
- Positive result: within the observed and qualified contexts, named Skill footprints show smaller matched within-Skill distance and interpretable, source-grounded artifact/action composition. This remains skill-conditioned association and may be mediated by task or phase.
- Negative or contradictory result: explicit mechanisms are visible but their natural-work footprints are too heterogeneous or confounded to generalize.
- Mixed or inconclusive result: report per-skill/per-project support and N/A cells, with no pooled claim.
- Target paper figure or table: F7 separates Skill and instruction evidence. Skill panels show exact invocation/attribution/orphan/root-session coverage, normalized action/artifact footprints, and within-Skill versus restricted between-Skill distances. A separate instruction panel shows successful focal reads/mutations and next-turn composition. Reuse/validation appears only for source-covered projects with denominators and explicit N/A cells.

## Reproducibility Notes
- Software and data versions: record Git revisions, parser schema version, cutoff, source-file SHA-256 manifest, and ProcGrep pin if the sensitivity arm is used.
- Config and seed notes: seed 20260722; no semantic labels, LLM judge, human annotation, or arbitrary fixed post-invocation event window.
- Known deviations: implicit instructions that a harness injects without a native source record are not observable non-exposure; instruction access and Skill invocation are different estimands; attribution coverage is Claude-specific unless another source exposes equivalent native fields; observational footprints are not causal harness effects and cannot exclude task/phase mediation.

## Executed Preflight Amendment

The complete-source preflight exposed a source topology that the planned
per-invocation membership rule would misrepresent: the explicit `Skill(S)` call
often appears in a parent transcript stream while source-native
`attributionSkill=S` Tool actions appear in delegated child streams under the
same native root session.  The primary descriptive unit is therefore narrowed
to `(project, vendor, native_root_session_id, attributionSkill)`.  It includes
only rows carrying the native attribution label and requires no inferred
episode boundary.  Explicit invocation-to-attribution same-stream links remain
a separately reported coverage audit.  They are not used to discard delegated
attribution or to synthesize an invocation episode.

This amendment weakens rather than broadens the claim: the result may describe
source-attributed Skill-conditioned footprints, but cannot estimate a causal
invocation effect or an exact episode duration.  Independence, n>=3 root
session qualification, exact project/vendor/model/source-role matching, and
the selected-case interpretation stop remain unchanged.  Immediate activity
after an instruction focal event is limited to the first subsequent Tool
action before a prompt-index change; overlapping arbitrary windows are not
used.

## Executed Final Estimand And Deviations

This section is the authoritative record of what was executed and supersedes
conflicting prospective wording above.

- The primary Skill unit is
  `(project, vendor, model, source_role, native_root_session_id, Skill)` and
  contains every Tool action carrying that source-native attribution. It is
  not a uniquely joined invocation episode. The same-stream contiguous count
  is retained only as a conservative coverage diagnostic.
- A Skill qualifies with at least three distinct native root sessions inside
  one exact project/vendor/model/source-role stratum. A same/different-Skill
  comparison additionally requires two qualified Skill names in that same
  stratum. Only one project meets the latter gate.
- The planned 10,000-draw Monte Carlo test was replaced by enumeration because
  the observed support admits only 12 root-block-preserving label assignments
  and four distinct statistic values. The one-sided exact p-value is 0.750.
- Action-only and artifact-only feature ablations were executed. The planned
  leave-one-project-out comparison is N/A because only one project passes the
  exact comparison gate. Boundary-only per-invocation membership is N/A
  because delegated execution crosses transcript streams and the source does
  not expose a defensible invocation end boundary. Later artifact reuse,
  recognized validation, and path-transition outcomes were not run after the
  primary repeatability claim failed its support test; they cannot rescue it.
- The executed projection uses repository-direct source streams
  (`global=false`). The source checker validates all 2,063 streams included by
  those projections; it does not claim to enumerate an independent universe
  of every transcript that may mention the repository.
- Instruction access remains a separate focal-event estimand. The CSV retains
  5,581 parser-detected rows as a sensitivity set, while the primary figure
  uses 2,822 independently recomputed, high-confidence direct/simple-shell
  accesses and then restricts bars and next-action composition to successful
  accesses. Arbitrary script bodies and unexpanded shell globs are outside the
  completeness claim.
- The six projects are selected author-associated natural cases. The result is
  descriptive within-case evidence and cannot estimate population prevalence,
  productivity, waste, or causal Skill/harness effects. External
  relation-level triangulation is a separate RQ6 and was not executed in this
  experiment.
