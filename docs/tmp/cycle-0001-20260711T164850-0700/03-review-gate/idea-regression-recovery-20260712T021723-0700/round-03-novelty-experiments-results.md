# Round 03 — Novelty, Experiments, And Results

**Node timestamp:** 2026-07-12T02:58:01-07:00  
**Parent:** `idea-regression-recovery-20260712T021723-0700`  
**Skill:** `iter-refine-ideas`, discussion 3 of 3  
**Scope:** complete current paper, current canonical project documents, admitted
RQ2 result, closest primary literature, and one next decisive experiment  
**Repository policy:** no skill changes, no Git operations, and no edits to
`docs/agentpprof-paper/`

## Question Given To The Independent Discussant

Read the complete recovered paper and project state without prior-round
verdicts. Determine whether the large position is actually novel, identify the
strongest same-claim work and experimental precedent, propose unexpected
larger directions, and specify one complete real experiment that can resolve a
paper-level uncertainty without introducing another system.

## Independent Interpretation

The paper's strongest position is not that agents need another flamegraph
renderer, hierarchy constructor, or failure detector. An execution tree records
where activity occurred in one run, but is not necessarily the best index for
comparing recurring behavior across runs. AgentProf makes hierarchy and measure
selectable, preserves native structure as evidence and a baseline, and asks
empirically when flat, native, or semantic profiles best support a real
decision.

The admitted AgentRx/TELBench result remains decisive for the tested mechanism:
flattened induced leaves did not significantly beat prevalence and simpler
controls sometimes won. That evidence does not authorize shrinking the RQs.
It establishes a sharper principle: a representation can attribute a signal
that exists in the observations or cohorts; grouping alone cannot manufacture
diagnostic signal.

## Primary-Source Verification

The main agent independently opened the following primary or official sources
after receiving the discussion memo.

### Domain-specific program profiling

- Primary publication record and metadata:
  <https://doi.org/10.1016/j.scico.2014.02.011>
- Author-hosted paper:
  <https://inkytonik.github.io/assets/papers/scp14.pdf>
- Verified content: Sloane and Roberts model execution as a stream of
  domain-level events, construct a hierarchical execution model, and summarize
  it along developer-chosen dimensions.
- Classification: **same-mechanism novelty threat**. Operations, arbitrary
  dimensions, hierarchical models, and developer-selected aggregation are not
  independently novel.
- Boundary: the work does not study real AI-agent traces or compare semantic,
  native, and flat indices under a common decision task.

### pprof

- Official documentation:
  <https://github.com/google/pprof/blob/main/doc/README.md>
- Verified content: a profile is a collection of samples associated with a
  location hierarchy, numeric values, and labels; pprof is agnostic to profile
  semantics; tags can be rendered as pseudo stack frames; profiles can be
  aggregated or compared.
- Classification: **same-mechanism novelty threat and computational baseline**.
  Weighted stacks, multiple measures, labels, tag-derived frames, profile diff,
  and flamegraph output are infrastructure, not the scientific contribution.

### Pivot Tracing

- Primary publication page and author version:
  <https://www.microsoft.com/en-us/research/publication/pivot-tracing-dynamic-causal-monitoring-for-distributed-systems/>
- DOI: <https://doi.org/10.1145/2815400.2815415>
- Verified content: runtime metrics can be defined at one point and selected,
  filtered, and grouped by causally related events elsewhere using a
  happened-before join.
- Classification: **same-problem conceptual precedent and novelty threat** for
  query-time cross-layer attribution.
- Consequence: mass conservation alone is not lineage fidelity. Any positive
  cross-layer claim needs an independently recorded parent or causal relation.

### Aggregate distributed traces

- Primary preprint: <https://arxiv.org/abs/2412.07036>
- Verified content: traces are grouped by shared services, depth, structural
  similarity, or latency, then summarized with an aggregate trace structure.
- Classification: **partial same-problem novelty threat**. Cross-run aggregate
  trace analysis is not new; its focus is structural trace similarity rather
  than the empirical choice between semantic and execution indices.

### Differential flame graphs

- Primary paper:
  <https://asgaard.ece.ualberta.ca/papers/Conference/SANER_2015_Bezemer_Understanding_Software_Performance_Regressions_using_Differential_Flame_Graphs.pdf>
- DOI: <https://doi.org/10.1109/SANER.2015.7081872>
- Verified content: profiles of two software versions are compared directly to
  expose regressions and improvements.
- Classification: **published experimental precedent**. Differential profiling
  itself is not AgentProf's novelty.

### Hodoscope

- Primary preprint: <https://arxiv.org/abs/2604.11072>
- Official artifact and annotated replication:
  <https://hodoscope.dev/blog/announcement.html>
- Verified protocol: the official SWE-bench example compares four public
  leaderboard cohorts—o3, GPT-4.1, Qwen3-Coder, and
  DeepSeek-v3.2-Reasoner—with iQuest-Coder-V1; it samples 50 trajectories per
  model with seed 42. The official page provides exact Docent collection IDs,
  a pinned iQuest trajectory archive, commands, and a runnable example.
- Verified result: the walkthrough reports 79 `git log` actions among 4,006
  actions and identifies an iQuest-specific cluster. The paper reports a
  6--23x estimated reduction in review effort over uniform sampling across its
  studies.
- Classification: **serious same-problem novelty threat and mandatory baseline**
  for behavior-difference discovery. Hodoscope already performs semantic
  cross-run behavioral comparison over real agents.
- Boundary: Hodoscope produces a flat continuous behavior space and density
  difference for human review. It does not isolate whether recursive semantic,
  native execution, or flat representations win when the information and
  decision rule are matched.

### Causal profiling

- Primary paper: <https://arxiv.org/abs/1608.03676>
- Verified content: Coz tests intervention impact because the code where time
  accumulates need not be the code whose optimization improves the program.
- Classification: **future conceptual branch**, not a required component or
  baseline for the next experiment.
- Consequence: mass concentration is weaker evidence than a correct analyst
  decision or successful intervention.

## Novelty Boundary After Verification

AgentProf must not claim novelty for:

- representing weighted fielded observations;
- selecting aggregation dimensions;
- constructing hierarchical profiles;
- turning labels into stack frames;
- aggregating traces across runs;
- comparing two profiles;
- semantic embedding or cohort-density differences;
- generic failure localization.

The remaining potentially novel and important claim is empirical:

> For stochastic agent behavior, execution structure, flat semantic behavior,
> and recursive semantic hierarchy are competing profiling indices. AgentProf
> makes them comparable over one evidence substrate and determines which index
> improves a real decision, under what workload and query conditions.

This is larger than a new renderer and more defensible than claiming the two
mechanical abstractions have no precedent. It also creates an honest negative
outcome: source-native or flat semantic analysis may be sufficient.

## One Decisive Experiment Proposed By The Discussant

Answer RQ2 verbatim by reproducing Hodoscope's published SWE-bench Verified
comparison:

- five public model cohorts;
- 50 trajectories per model, seed 42;
- all 250 trajectories processed;
- the known real effect is iQuest-Coder-V1's git-history “time travel” behavior.

Construct four views over the same source actions:

1. flat per-action differential ranking;
2. source-native `trajectory -> turn/tool` hierarchy;
3. one semantic operation stack fixed before iQuest scoring, such as
   `workflow phase -> action family -> behavior cluster`;
4. official Hodoscope density-difference output as an end-to-end external
   comparator.

For views 1--3, use the same action contents, summaries, cohort labels,
development data, and differential scoring rule. Fit any semantic mapping on
the four non-iQuest cohorts and apply it unchanged to iQuest. Do not use the
known exploit labels to construct or rank any view.

**Single primary outcome:** number of raw actions inspected before the first
independently confirmed git-history exploit.

Materialize every ranking before applying exploit annotations. Complete all
250 trajectories and every prespecified view even if preflight or an early row
already reveals the exploit. Report construction, model, and review cost; do
not pretend the Hodoscope end-to-end comparator has the same cost structure as
views 1--3.

## Outcome Interpretation

- Semantic stack beats flat, native, and Hodoscope: recursive structure adds
  decision value on this real task.
- Semantic stack approximately matches Hodoscope and beats native: semantic
  reindexing is supported, but the novelty is limited to structured profiling
  or cost rather than semantic discovery itself.
- Hodoscope wins: a flat semantic population difference is sufficient here.
- Flat or native wins: the current operation stack adds no value on this task.
- All views fail: the current negative evidence generalizes beyond induced
  leaves.

Each outcome answers the RQ without changing it.

## Main-Agent Disposition

### Accepted

- Preserve three RQs and the challenge to execution-tree primacy.
- Make representation choice and decision value the scientific center.
- Add domain-specific profiling, Pivot Tracing, aggregate traces, differential
  flame graphs, and Hodoscope to the closest-work frontier.
- Select the full Hodoscope SWE-bench replication as the next RQ2 experiment,
  subject only to a real preflight confirming source access and executable
  artifacts.
- Keep the negative AgentRx/TELBench result.

### Demoted or rejected

- Do not claim the operation/operation-stack mechanisms are unprecedented.
- Do not add Hodoscope, causal profiling, a navigator, or a new hierarchy
  constructor as an AgentProf component.
- Do not resume the superseded eleven-comparator experiment.
- Do not use “differential profiling” itself as the novelty claim.
- Do not expand RQ3 before one complete RQ2 experiment.

### Open

- Whether the final contribution is a winning semantic hierarchy or a
  representation-sensitivity result.
- Whether the semantic stack can match Hodoscope with less construction or
  review cost.
- Which independent decision or intervention determines legitimacy when two
  label-free representations disagree.

## Applied Changes

The main agent updated:

- `docs/background-related-work.md` with the verified closest-work classes,
  Hodoscope boundary, and concrete baseline handoff;
- `docs/idea-story.md` with the mechanism novelty boundary, representation-choice
  center, and selected 250-trajectory experiment;
- `docs/evaluation.md` with the exact population, development/target separation,
  four views, primary outcome, label timing, and completion rule;
- `docs/paper/main.tex` so the introduction, contribution list, RQ2 next step,
  related work, and conclusion state the same novelty boundary and experiment;
- `docs/paper/references.bib` with verified entries for domain-specific
  profiling, Pivot Tracing, aggregate traces, differential flame graphs, and
  Hodoscope.

The paper was compiled with `pdflatex -> bibtex -> pdflatex -> pdflatex`.
The final pass produced `main.pdf` with 9 pages and 721,244 bytes, no undefined
citation/reference warning, and no overfull box. Fifteen underfull boxes remain
as non-blocking typography diagnostics. A residual use of the old generic
“scope tree” vocabulary in the mathematical model was found mechanically and
replaced with the existing `operation stack`, `stack constructor`, `prefix
tree`, and `frame` vocabulary.

No current skill was changed. No Git operation was performed. The dirty
`docs/agentpprof-paper/` submodule was not edited.

An independent recovery audit was then started with no desired verdict and no
access to the earlier recovery verdicts. Its findings are recorded in a
separate sibling report.
