# RQ2 Official Source, Protocol, And Baseline Selection

**Started:** 2026-07-12T20:20:10-07:00  
**Completed:** 2026-07-12T20:30:01-07:00  
**Cycle/gate:** cycle 0002 / EXPERIMENT  
**Parent:** `../000-gate-entry-20260712T201943-0700.md`  
**Owner:** `research-literature-novelty`  
**Status:** complete; handoff to `research-experiment-design`

## Question And Entry

The fixed paper question is:

> **RQ2: Does Profiler Output Correspond to Real Problems?**

This node asks which official public source can support one complete,
target-blind experiment of the positive hypothesis: a semantic operation-stack
profile should concentrate independently annotated real problems and reduce the
amount of trajectory material an analyst must inspect. The source must expose
real raw agent operations before any target annotation is read, preserve a
defensible native structure, and provide independent step-level labels for
terminal scoring. This node does not reconsider the thesis, story, or RQ.

## Inputs And Provenance

The selection read the current paper-level RQ and source controls in
`docs/evaluation.md`, the canonical story in `docs/idea-story.md`, the current
closest-work map in `docs/background-related-work.md`, the complete user prompt
log, and the cycle entry report. It also audited the existing R410 AgentRx and
TELBench artifacts. R410 is already the recorded Revision-0 negative mechanism
boundary; it is not an unclaimed positive result and was not reopened.

Primary external sources inspected:

- [CodeTracer paper](https://arxiv.org/abs/2604.11641), its
  [official implementation](https://github.com/NJU-LINK/CodeTracer), and the
  [official CodeTraceBench dataset](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench);
- [ToolSafe paper](https://aclanthology.org/2026.findings-acl.1850.pdf) and
  [official repository](https://github.com/MurrayTom/ToolSafe);
- [RedundancyBench paper](https://arxiv.org/abs/2605.29893) and its linked
  anonymous artifact;
- [AgentRx](https://github.com/microsoft/AgentRx), already executed in this
  project;
- [ATBench](https://arxiv.org/abs/2604.02022) and its official dataset card;
- AgentRewardBench, SATraj-OS, OSWorld-Human, AgentNet, TRAIL, Who&When, and
  TELBench sources already mapped in `docs/background-related-work.md`.

Dataset availability was checked through the official Hugging Face Dataset
Viewer API. Four raw CodeTraceBench archives, one for each framework in the
verified split, were downloaded to `/tmp/codetrace-source-preflight/` and listed
without modifying the repository.

## Method

Candidates were compared on five decision-bearing properties:

1. a real executed-agent trajectory rather than a generated fixture or isolated
   classification prompt;
2. independent step- or span-level labels for a meaningful real problem;
3. raw visible operations available separately from target labels;
4. an official published evaluation unit and metric;
5. enough framework, model, and task diversity for a complete paper experiment.

The source screen did not reward the number of available datasets. It selected
the one source that most directly tests the paper's profiling claim, then kept
other sources only as possible later replications.

## Candidate Decisions

### Selected Primary Condition: CodeTraceBench

CodeTraceBench is the strongest current primary condition.

- The official dataset contains 4,316 executed coding-agent trajectories with
  human-verified step-level `incorrect` and `unuseful` annotations. The paper
  reports both stage- and step-level supervision and a 15% independent
  double-annotation study with Cohen's kappa of 0.73 on the error-critical step.
- Its verified evaluation split has 1,000 trajectories and 46,539 steps across
  four real frameworks: 520 OpenHands, 108 SWE-agent, 222 Terminus2, and 150
  mini-SWE-agent trajectories. It includes six model identifiers in the dataset
  card and spans SWE-bench-family and TerminalBench tasks.
- The 1,000-row verified manifest is directly accessible as a 984,091-byte
  Parquet file. Each row points to a separately downloadable raw `tar.zst`
  artifact. Source preflight downloaded and opened one long trajectory per
  framework: 217-step OpenHands, 123-step SWE-agent, 327-step Terminus2, and
  73-step mini-SWE-agent runs.
- Raw archives contain source-native event streams, `.traj` records, episode
  logs, commands, observations, and result files. The annotation manifest is a
  separate object. A runner can therefore generate every non-oracle profile
  from raw archives and a label-free manifest projection, then join
  `incorrect_step_ids` and `unuseful_step_ids` only in terminal scoring.
- The paper's published protocol reports macro step-level Precision, Recall,
  and F1 plus token cost. It publishes Bare-LLM, Mini-CodeTracer, and CodeTracer
  results under matched budgets. These provide an externally anchored direct
  diagnosis reference, while AgentProf tests the different question of whether
  a cross-run resource profile concentrates independently annotated problems.

The source is not treated as evidence that CodeTracer's human stage segmentation
is target-blind. The paper says stages are assigned during annotation. Those
stage boundaries may appear only as an oracle analysis or as the official
diagnostic reference, not as an equally informed native baseline. The fair
source-native view must instead come from the raw framework's event, episode,
checkpoint, or chronological structure.

### Secondary Replication Candidate: ToolSafe TS-Bench

TS-Bench is official, published, accessible, and supplies step-level
`safe/controversial/unsafe` tool-invocation labels over AgentHarm, ASB, and
AgentDojo-derived trajectories. Its paper reports 7,188 evaluation samples and
publishes guardrail accuracy/F1-style comparisons. It is a strong later safety
replication.

It is not the first condition because its released unit is a candidate tool
call with preceding history, optimized for pre-execution classification. That
structure is less direct for comparing cross-run profile organization and
analyst inspection than CodeTraceBench's complete raw trajectories. Running
ToolSafe first would risk turning RQ2 into a guardrail-classification paper.

### Secondary Replication Candidate: RedundancyBench

RedundancyBench directly labels every trajectory step as redundant or necessary
and publishes three representative detectors, making its construct highly
relevant. It remains a good second-family replication after the first complete
condition.

It is not selected first because the paper is a May 2026 arXiv release and the
linked code/data are still hosted under an anonymous 4open artifact rather than
a stable identified project repository. Its full raw-schema accessibility and
source-native structure have not yet passed the same four-format preflight as
CodeTraceBench. This is an access/provenance ordering decision, not a claim that
redundancy is scientifically unimportant.

### Rejected As Primary Conditions

- **ATBench, SATraj-OS, and AgentRewardBench:** useful real trajectory corpora,
  but the currently verified public labels are primarily trajectory-level.
  They cannot alone score the step-level concentration and inspection claim.
- **AgentRx and TELBench:** their labels are suitable, but the current project
  already ran a complete fixed construction on them and obtained the recorded
  negative Revision-0 boundary. Reusing the same labels for another tuned
  construction would compromise the target-blind claim.
- **OSWorld-Human and AgentNet:** rich action sequences and task structure, but
  the current source audit has not established independent incorrect/unuseful
  step labels comparable to CodeTraceBench.
- **TRAIL and Who&When:** scientifically relevant localization datasets, but a
  complete official raw artifact and stable executable protocol were not more
  accessible than CodeTraceBench in this screen.

## Published Protocol And Fair Comparison Handoff

The next experiment should use the complete 1,000-trajectory CodeTraceBench
verified split for confirmatory scoring. The 3,316-row full split may be used
only for label-free format development and operation-schema validation. Neither
split's `incorrect_stages`, `incorrect_step_ids`, `unuseful_step_ids`, label
reasoning, or annotation-derived stage boundaries may reach extraction,
tagging, grouping, ranking, threshold selection, or profile construction.

All non-oracle views must consume the same successfully extracted raw steps and
the same resource weight. The smallest interpretable comparison is:

1. **flat/global control:** no useful grouping;
2. **per-session view:** trajectory identity over identical steps;
3. **source-native view:** raw framework event/episode/action structure, with no
   human annotation stages;
4. **raw-action view:** source action/tool identity without semantic folding;
5. **AgentProf semantic operation stack:** one fixed cross-framework mapping
   from visible operation fields, aggregated by the real AgentProf binary.

The official CodeTracer published result is a direct-diagnosis reference, not a
matched grouping baseline. It should be cited rather than rerun unless the plan
can reproduce its exact model and token budget on the same official split.
Annotation-derived stage/error groupings are oracle upper bounds only.

The primary outcome should be hidden-label concentration as a function of
inspection work. Reuse the official macro step-level Precision/Recall/F1 for a
predeclared, target-blind profile cutoff, and add average precision plus
recall-at-fixed-inspection and work-to-fixed-recall to express the profiler's
ranked output. Report incorrect and unuseful labels separately before any
combined real-problem result. Bootstrap uncertainty over trajectories, stratify
or report by framework, and preserve the complete 1,000-trajectory result.

The plan must specify the profile's measured signal and ranking without reading
step labels. A high-value candidate is differential resource profiling between
source-reported unsuccessful and successful runs, stratified by task/framework,
because it uses an operational run outcome rather than the hidden step target.
The plan reviewer must decide whether this is equally informed and whether a
plain resource-hotspot ranking is the cleaner primary protocol. That choice is
an experiment-design question; this literature node does not tune it on labels.

## Scientific Impact And Decision

CodeTraceBench materially improves the experiment opportunity without changing
the paper story. It tests AgentProf on real software agents, real executed
tasks, multiple frameworks and frontier backbones, and independent human
problem annotations. A positive result would directly support the original RQ2
claim that profiler output corresponds to real problems and reduces inspection.
A negative result would reject the tested signal/mapping/ranking on this family,
not replace the RQ, thesis, or four-contribution story.

Decision: admit CodeTraceBench to `research-experiment-design` as the primary
RQ2 condition. Keep ToolSafe and RedundancyBench as later independent-family
replications only after the primary condition reaches complete result review.

## Artifacts And Reproduction

- Official verified Parquet:
  `https://huggingface.co/datasets/NJU-LINK/CodeTraceBench/resolve/refs%2Fconvert%2Fparquet/default/verified/0000.parquet`
- Official full Parquet:
  `https://huggingface.co/datasets/NJU-LINK/CodeTraceBench/resolve/refs%2Fconvert%2Fparquet/default/full/0000.parquet`
- Source-preflight archives: `/tmp/codetrace-source-preflight/` (ephemeral;
  source eligibility only, not paper evidence)
- Existing negative boundary:
  `docs/visexp/out/rq2-family-heldout-r410/full/full-results.json`

## Uncertainty, Revisit Conditions, And Next Node

The main unresolved design question is not source eligibility; it is the exact
target-blind measured signal and cutoff that turn a resource profile into a
step-level prediction without borrowing hidden labels. The experiment plan must
resolve that scientifically before execution. It must also prove extraction
coverage across all four raw formats and identify any archive whose raw steps
cannot be aligned to official step IDs.

Reopen source selection only if the complete raw verified split is unavailable,
raw-to-step alignment fails for a material framework, or the approved ranking
cannot be computed without target annotations. Otherwise proceed directly to
one complete `research-experiment-design` loop for this RQ and source.
