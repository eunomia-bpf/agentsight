# Experiment Plan: Literal Action Identity on Published Agent Trajectories

**Proposed:** 2026-07-16T01:47:00-07:00

**State:** proposed; awaiting one fresh plan review
**Paper question:** **RQ3 — How Accurate Are the Tags?**

## Uncertainty and tested hypothesis

The missing RQ3 evidence is literal action identity: can the fixed local
closed-taxonomy tagger assign a semantically comparable action label to a
visible agent iteration, rather than merely recover a partition or task ID?

> Across the complete published labeled population of 120 real software-
> engineering agent trajectories, the fixed Qwen3.6-27B closed-taxonomy tagger
> has higher eight-class operation-macro F1 than a majority-label control when
> uncertainty is estimated by resampling whole trajectories within each of the
> three agent frameworks.

The expected result is a positive macro-F1 difference whose stratified
trajectory-bootstrap 95% interval excludes zero. A non-positive estimate or an
interval containing zero contradicts this tested hypothesis. Per-class or
per-agent failures bound where the mechanism works but do not independently
rewrite RQ3 or challenge the paper thesis.

## Published source and full population

The experiment uses the official artifact for the ASE 2025 Distinguished
Paper *Understanding Software Engineering Agents: A Study of Thought-Action-
Result Trajectories*, at repository commit
`e84f66f8d494e46ef336edfa137db25a629614fb`.

The complete scored population is every published action-category row:

| Agent | Trajectories | Labeled iterations |
|---|---:|---:|
| AutoCodeRover | 40 | 218 |
| OpenHands/CodeActAgent | 40 | 1,108 |
| RepairAgent | 40 | 1,411 |
| **Total** | **120** | **2,737** |

The source contains 2,751 visible iterations. The 14 iterations without a
published category remain unscored and enter only the source-coverage result,
giving 2,737/2,751 (99.49%) label coverage. No trajectory, class, or published
label is sampled away.

## Candidate and scorer boundary

For each published labeled iteration, the candidate sees only:

1. the current visible action text;
2. the current visible thought text; and
3. the eight fixed category definitions from the TraceView companion labeling
   artifact.

Action is placed before thought so the current operation remains visible if the
combined fragment exceeds the tagger's fixed 1,600-character source window.
The candidate does not receive the category CSV, trajectory outcome,
resolved/unresolved status, neighboring labels, class counts, filename, or a
worked example. The prompt and field order are identical for all agents and
both repetitions.

The eight output names and targets come from the ASE artifact; the operational
meanings below come from the TraceView companion labeling guide:

| Output | Meaning |
|---|---|
| `Explore` | Broadly inspect the task, repository, environment, or available context. |
| `Locate` | Identify the specific file, symbol, function, or code area to change. |
| `Search` | Run a targeted search for text, references, examples, or related behavior. |
| `Reproduce` | Run commands or checks to observe, reproduce, or isolate the problem. |
| `Generate Fix` | Create or edit code intended to solve the task. |
| `Run tests` | Run tests, linters, or validation commands after a change. |
| `Refactor` | Reorganize or simplify code without changing intended behavior. |
| `Explain` | Reason, summarize, or plan without directly changing or validating code. |

Gold is joined only after predictions are written, using agent, trajectory ID,
and published iteration ID. The experiment adapter prepares inputs, calls the
existing local llama.cpp endpoint with an exact eight-value grammar, and
scores outputs. It does not train a classifier, derive labels, or implement a
new induction algorithm.

The fixed backend is the already-used local
`Qwen_Qwen3.6-27B-Q4_K_M.gguf` model with llama.cpp, temperature zero,
reasoning disabled, an eight-token output budget, and no prediction cache. Two
complete repetitions measure exact assignment agreement without adding a model
or prompt sweep.

## Comparison and metrics

The only control predicts the population-majority published class, `Generate
Fix`, for every labeled iteration. It represents absence of semantic signal.
The experiment does not claim classifier SOTA, and the source paper publishes
no trained action classifier to rerun; project-authored keyword rules would be
a weaker and less independent comparison.

Primary outcome:

- eight-class operation-macro F1 over all 2,737 published labels.

Primary effect and uncertainty:

- candidate macro-F1 minus majority macro-F1;
- 10,000 deterministic bootstrap replicates that resample 40 whole
  trajectories with replacement within each agent framework and retain the
  fixed eight-label metric support.

Secondary diagnostics:

- micro accuracy;
- per-class precision, recall, F1, and support;
- the complete eight-by-eight confusion matrix;
- per-agent accuracy and macro-F1 over the classes published for that agent;
- exact valid-output coverage;
- exact agreement between the two complete repetitions; and
- published-label coverage over all visible source iterations.

There is no composite score and no universal `.80` threshold. Accuracy cannot
override macro-F1 because `Refactor` has only 23 examples. Secondary results
may invalidate a broad interpretation—for example zero output coverage—but do
not replace the primary effect.

## Real preflight, full command, and completion

The thin adapter will live at
`experiment-001/literal_action_identity.py`. It has three explicit modes:
`prepare`, `run`, and `score`. Raw artifacts live under
`.agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/`.

The real preflight uses eight official labeled iterations, one scorer-selected
row per published class, and executes the actual source parser, model request,
exact grammar, majority control, and scorer. It proves only that the path runs;
its results cannot change the prompt, model, taxonomy, population, metric, or
plan, and all eight rows remain in the full run.

After preflight, the full run executes both complete repetitions over all 2,737
labeled iterations. Each repetition must reach terminal status with exactly
2,737 unique predictions, all drawn from the eight published values. Partial
prefixes are resumed or rerun but never scored. The full run is complete only
when the scorer produces the primary effect, bootstrap interval, every
secondary diagnostic, and raw per-row predictions for both repetitions.

Planned paths:

```text
.agentsight/experiments/rq3-literal-phase-action-source-v1/
  source-cache/llm-agents-study/
  ase-action-identity/
    visible-inputs.jsonl
    scorer-manifest.json
    preflight/predictions.jsonl
    preflight/score.json
    full/predictions-r1.jsonl
    full/predictions-r2.jsonl
    full/scored-results.json
```

The approved server will run on a dedicated local port. The exact commands and
runtime duration are recorded in the preflight/result reports after execution,
not promoted into an additional protocol artifact.

## Interpretation and paper boundary

A supported result adds independent literal action-label evidence to RQ3 and
may support one concise evaluation table row. It does not replace OSWorld and
CodeTrace partition evidence, establish cross-run identity, prove every tagger
backend, or answer RQ1, RQ2, or RQ4.

A contradicted or mixed result identifies a limitation of this fixed local
closed-taxonomy tagger on the published action taxonomy. It does not authorize
changing the four RQs, shrinking the thesis, weakening the hypothesis, or
rewriting the paper story. The fixed thesis remains: **Agent observability
needs profiling, not only debugging.**
