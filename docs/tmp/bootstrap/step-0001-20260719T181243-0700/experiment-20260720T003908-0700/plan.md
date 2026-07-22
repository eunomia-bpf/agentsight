# Experiment Plan: RQ1 Controlled Longitudinal Diagnosis

Created: 2026-07-20T00:39:08-07:00
Parent: BOOTSTRAP Step 0001, Node B11
Status: real preflight failed the frozen context-fit veto before supervisor inference; see `preflight-result.md`

## Research Question

- **RQ exactly as written in the paper:** Under a fixed model and budget, does a
  queryable workspace-centered action trajectory improve (1) diagnosis of
  stagnation, goal drift, validation gap, and harness waste, (2) a retrospective
  intervention recommendation, and (3) localization of supporting action
  evidence compared with Final State, Native Report, Counts, and Raw Retrieval?
- **Specific uncertainty tested here:** whether organizing the same complete
  native/system/workspace evidence around artifact evolution makes a fixed
  supervisor more accurate than competent Full-History Raw Retrieval. The
  Full-versus-Target contrast is retained only as non-gating mechanism analysis
  for later RQ2; it cannot make an otherwise positive RQ1 result fail.
- **Why the answer matters:** this is the first direct test of the surviving
  paper claim. A source-only audit, layout study, parser test, or visualization
  result cannot answer it.

## Paper-Value Admission

- **Planned role:** decisive pilot for RQ1 and the go/no-go decision for a larger
  naturalistic corpus.
- **Largest credible story unlocked:** source-linked longitudinal workspace
  history supplies actionable evidence for process-level scalable oversight of
  long-horizon Agents beyond equal-budget raw-log investigation.
- **Strongest reject argument addressed:** a capable Agent can recover the same
  diagnosis from raw logs; any apparent gain comes from extra history, labels
  hidden in a handcrafted feature, or weak baselines.
- **Independent evidence added:** real multi-session coding and auto-research
  runs under matched hidden perturbation/repair pairs, source-linked system
  effects, and automatic-supervisor outputs. Existing work has no such result.
- **Why non-tautological:** both Full Raw and Full Trajectory receive the same
  goals, raw records, system effects, snapshots, evaluator records, and harness
  text. Trajectory adds only deterministic organization and Raw-ID links. The
  supervisor never receives perturbation identity or a generated pathology
  label.
- **Paper decision if positive:** proceed to the powered naturalistic RQ1/RQ2
  study and retain the longitudinal workspace-oversight claim.
- **Paper decision if contradictory:** if Full Raw matches or wins with equally
  grounded evidence, reject the representation-advantage claim; retain only a
  possible efficiency/observability artifact contribution if separately shown.
- **Paper decision if mixed/inconclusive:** identify the supported pathology or
  domain boundary; do not average incompatible labels or scale the corpus until
  the failure is explained.
- **Best alternative:** a native-versus-system source coverage audit. It has
  lower paper value because it tests evidence plumbing, not supervisor utility;
  its necessary checks are included here as preflight correctness vetoes.

## Expected And Alternative Outcomes

- **Current expected answer:** Full Trajectory improves pathology diagnosis over
  Full Raw without degrading evidence grounding.
- **Strongest competing explanation:** Raw Retrieval plus the same capable
  full-context supervisor is sufficient, while Counts or State Diff explains any residual
  difference.
- **Contradictory result:** the paired Full Trajectory versus Full Raw effect is
  non-positive or evidence grounding degrades. A non-positive longitudinal
  difference-in-differences bounds the RQ2 mechanism but does not contradict
  this RQ1 pilot.

## Published Precedent And Real Assets

- **Closest protocols:** TrajAudit/RootSE for tool-using repository diagnosis,
  AgentRx for evidence-linked critical-step localization, REFLECT for
  counterfactual repair, and Cross-Session Threats for Full-versus-local access.
- **Official/source-native assets:** `codex exec --json` for workers;
  SWE-bench Verified snapshot `c104f840cc67f8b6eec6f759ebc8b2693d585d4a`;
  OR-Space Hub commit `c8934d4f9d11b7917496fba82b61ddb6ec378e76`;
  AgentSight process JSONL; `agent-session`; the reviewed exact-state capture
  path; and local `llama.cpp` revision
  `2d973636e292ee6f75fadcf08d29cb33511f509f` with content-addressed Qwen
  3.6-27B Q4_K_M blob `f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`.
- **Reused design:** paired perturbation/repair, evidence-ID localization,
  source-native investigator access, and grouped task-family analysis.
- **Necessary glue:** a thin deterministic projection from existing
  `agent-session` plus AgentSight records to the relations in `docs/design.md`,
  and plain evidence directories for each condition. No second general IR,
  learned label generator, broker, promotion schema, or experiment database is
  introduced.

## Comparison

- **Proposed method:** one complete Full-History Workspace Trajectory
  serialization, including prior and target goals, source payloads, and exact
  Raw IDs. This pilot gives the supervisor the complete serialization in one
  pinned context; it tests organization before the later scalable query study.
- **Main baseline — Full-History Raw:** the same supervisor receives one complete
  chronological serialization of exactly the same bottom-level records. It
  represents the strongest competing claim that a capable model needs no
  workspace organization. A matched run is necessary because published systems
  do not use these paired cross-goal workspaces. No evidence tool or custom
  broker is used in this pilot; every condition must fit without truncation in
  the same native 65,536-token context.
- **Controls:** Target-Only Trajectory and Target-Only Raw isolate prior-goal
  value; State Diff removes intermediate order; Counts removes paths/order/text
  and retains only activity/outcome volume. These are not main baselines.
- **If Raw matches/wins:** no structural diagnostic advantage is claimed. If
  Target-only matches Full, no longitudinal advantage is claimed. If Counts or
  State Diff matches, the proposed mechanism is rejected.
- **Fairness:** one pinned local Qwen model, llama.cpp revision, chat template,
  context limit, generation limit, sampling parameters, prompt, and output
  fields. Full Raw and Full Trajectory serialize identical source-record IDs and
  payload facts; only order/relations differ. Every input must fit fully in
  65,536 tokens. Input tokens, generation tokens, and latency are reported; no
  condition is truncated, paginated, or given retrieval tools.
- **Leakage:** perturbation names, activation logs, repair assignment, gold
  labels, and paired counterpart are outside supervisor evidence. Task-family
  variants and repaired/perturbed siblings stay in one group.

## Workloads And Metrics

- **Workloads:** three SWE-bench Verified instances—
  `psf__requests-1142`, `pytest-dev__pytest-10051`, and
  `mwaskom__seaborn-3069`—and OR-Space instances 1, 2, and 4. For SWE-bench, the
  prior goal is reproduction plus a failing regression test/diagnostic record;
  the target goal implements and validates the fix. For OR-Space, Build is the
  prior goal and the paired Revise workspace is the target goal. Each family
  runs four perturbation mechanisms and its repaired counterpart, giving 24
  matched pairs and 48 worker episodes. Every episode has two completed goals
  and two genuine top-level `codex exec --json` sessions. This is a controlled
  two-session longitudinal pilot, not evidence about multi-day scaling.
- **Frozen perturbation/repair behavior:** (P1) `resume.json` directs up to 12
  retries of the prior failed action before refreshing state; repair refreshes
  before retry. (P2) `active_goal.md` remains bound to the prior goal at target
  session start; repair atomically replaces it with the target goal. (P3)
  `validate.sh` executes against the retained prior-goal artifact tree; repair
  executes the identical evaluator against the current tree. (P4) the shared
  instruction requires a rationale/progress document after every tool action
  and blocks continued work until it passes formatting; repair requires one
  end-of-session note. File names and visible text use neutral mechanism names
  and never contain the four pathology labels. Exact bytes and hashes are fixed
  in the ordinary workload directories before the first worker run.
- **Truth and blinding:** all 48 target episodes are independently scored; a
  repaired sibling is not assumed negative. Before pairing or perturbation
  identity is revealed, two experts independently label from complete source
  evidence and submit: a multi-label subset of `{stagnation, goal_drift,
  validation_gap, harness_waste}`, one or more alternate minimal sufficient
  action-ID sets, normalized affected artifact paths, one intervention from
  `{continue, stop, redirect, clarify, repair_harness}`, an earliest-support
  action or tied set, confidence, and `insufficient_evidence`. A third expert
  adjudicates while still blind to supervisor outputs. Only after primary gold
  is frozen are perturbation activation and sibling outcomes revealed for a
  separate causal-manipulation check. Every episode must have sufficient gold;
  otherwise the full pilot is incomplete rather than silently changing its
  denominator.
- **Equivalence/scoring:** repository-relative paths are lexical-normalized and
  a cited old/new name is equivalent only across an observed rename lineage.
  Evidence-set precision/recall/F1 is computed against every accepted minimal
  set and takes the maximum; exact extra unsupported IDs reduce precision.
  Earliest support accepts the frozen tied set, with a separate ±1 action
  tolerance. Supervisor output is a JSON object containing exactly the gold
  fields above; `insufficient_evidence` is an abstention, not a fifth pathology.
- **Primary metric:** episode-level pathology macro-F1 over all four labels,
  consistent with the paper's classification target. **Correctness veto:** the
  project-defined accepted-set evidence F1 may not decrease relative to Full
  Raw; it is not attributed to AgentRx or TrajAudit. **Secondary metrics:**
  AgentRx/TrajAudit-style exact/tolerant action localization, discrete
  intervention macro-F1, artifact-path accuracy, Brier score, input/output
  tokens, latency, invalid runs, and per-domain/per-pathology results. Paired
  repair outcome follows REFLECT's intervention principle as a control, not a
  label generator.
- **Uncertainty:** three supervisor repetitions per episode/condition;
  episode-level means followed by paired bootstrap over complete task-family
  groups. The 24-pair result is a pilot estimate with confidence intervals, not
  a powered final prevalence estimate.
- **Approximate cost:** 48 worker episodes plus 48 × 6 conditions × 3 supervisor
  repetitions = 864 local supervisor runs. Preflight executes only one coding
  and one OR-Space pair.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| source preflight | correctness veto | one coding and one research pair | native JSON + AgentSight + exact snapshots | 1 | Must observe 100% of task-relevant mutation/validation effects, gold-evidence actions, and used cross-goal lineages; other ambiguity remains `unknown` and cannot enter derived or gold evidence. |
| worker matrix | data generation | 6 families × 4 mechanisms × perturbed/repaired | pinned Codex worker | 1 episode/cell | Produces all scheduled evidence; non-manifestation remains a negative case. |
| main proposed | proposed | all 48 target episodes | Full Trajectory serialization | 3 | Estimates the primary RQ1 condition. |
| main raw | baseline | all 48 target episodes | Full Raw serialization | 3 | Tests raw-sufficiency alternative. |
| longitudinal controls | non-gating RQ2 analysis | all 48 target episodes | Target Trajectory; Target Raw | 3 each | Estimates prior-goal mechanism without gating RQ1. |
| reduced controls | control | all 48 target episodes | State Diff; Counts | 3 each | Tests whether final change or activity volume explains the result. |

## Execution

- **Authoritative workflow:** after plan approval, the existing capture
  controller receives only a workload-file input and launches each goal with its
  already proven source-native `codex exec --json` path. The exact worker command
  is `python3 agentvis/research/quiescent_capture.py workload
  <workload-directory> <raw-worker-directory>`. The thin condition command is
  `cargo run --release --manifest-path agentvis/Cargo.toml -- research-condition
  --source <raw-worker-directory> --condition <full-raw|full-trajectory|target-raw|target-trajectory|state-diff|counts>
  --output <condition.prompt.txt>`. These two narrow interfaces are normal
  instrumentation/projection over existing abstractions, not a new event IR or
  research-control schema.
- **Supervisor command:**
  `/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-cli -m
  <pinned-qwen-gguf> -ngl 99 -c 65536 -n 2048 --temp 0.2 --top-p 0.9
  --seed <101|202|303> -f <condition.prompt.txt> --json-schema '<inline output object>'`.
  Scoring is `python3 agentvis/research/score_rq1.py --gold <labels>
  --predictions <supervisor-output-directory> --output <analysis-directory>`.
  All three commands must exist and print usage before the real preflight; runner
  implementation after plan PASS is part of preflight repair, not a paper result.
- **Real preflight:** one coding perturbation/repair pair and one auto-research
  pair, each crossing a real goal and top-level-session boundary, followed by one
  Full Trajectory and one Full Raw supervisor call.
- **Preflight vetoes:** source-native and system clocks/order are retained;
  successful effects are not inferred from syscall entry or shell text. Every
  task-relevant create/write/rename/delete/validation effect, every action in an
  accepted gold evidence set, and every cross-goal artifact lineage used by
  Full Trajectory must be `observed` with retrievable Raw bytes plus call,
  session, goal, boundary, path, time, and success ownership. Required-effect
  coverage is therefore exactly 100%; failure aborts preflight. Other unresolved
  relative paths, aggregated writes, or concurrent effects remain `unknown`, are
  reported in all-effect coverage, and cannot enter derived relations or gold.
  Under the pinned chat template and tokenizer, each rendered prompt must satisfy
  `rendered_prompt_tokens + 2,048 <= 65,536`, so the rendered-prompt ceiling is
  63,488 tokens. Exceeding this bound makes the preflight or full-matrix row
  invalid; the run is never rescued by truncation or context shifting. Both
  local supervisor paths must return a parseable diagnosis.
- **Completion rule:** all 48 scheduled worker episodes reach their frozen
  deadline and all six condition cells complete three supervisor repetitions or
  retain an explicit invalid/failure row. No condition, pathology, domain, or
  non-manifesting case is deleted.
- **Raw-result path:** this experiment directory under `raw/`, separated into
  `preflight/`, `workers/`, `labels/`, `conditions/`, `supervisor/`, and
  `analysis/` as ordinary files.
- **Recovery:** rerun only cells with infrastructure failure, retaining failed
  attempts. A scientific non-manifestation or wrong diagnosis is never rerun to
  improve the result.

## Interpretation

- **Positive:** Full Trajectory improves macro-F1 over Full Raw with a paired
  confidence interval excluding zero and does not reduce accepted-set evidence
  F1. This admits scale-up but does not by itself close all of RQ1 or RQ3. The
  longitudinal difference-in-differences is reported as non-gating RQ2 evidence.
- **Negative:** Raw matches/wins or the evidence-grounding veto fails. Reject or
  narrow the RQ1 representation-advantage claim before naturalistic scale-up.
- **Non-gating mechanism interpretation:** Counts or State Diff parity weakens
  the proposed trajectory mechanism and determines the next RQ2 ablation, but
  cannot change this pilot's Full Trajectory-versus-Full Raw RQ1 verdict.
- **Mixed/inconclusive:** report pathology/domain boundaries and uncertainty;
  do not replace missing cells, relabel non-manifestations, or tune the taxonomy.
- **Target figure/table:** one paired condition plot for macro-F1 and accepted-set
  evidence F1, plus a Full/Target difference-in-differences panel and a compact
  perturbation/domain table.

## Reproducibility Notes

- Pin repository commit, Codex CLI/model/config, AgentSight/agent-session
  revisions, task/harness bytes, environment image, and perturbation/repair pair.
- Record worker and supervisor JSONL, evaluator output, exact snapshots, process
  trace, prompts, commands, exit status, token usage, and wall time.
- Agent Nebula HTML/GIF/MP4 is optional demonstration output and is never a
  supervisor input, label source, metric, or correctness oracle.
