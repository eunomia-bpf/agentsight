# Deep Research: Agent Trace Semantic Clustering And Aggregation

Last updated: 2026-06-16

Scope: this note studies how industry systems and academic papers cluster,
aggregate, label, and visualize LLM/agent traces. The focus is not generic
observability, but the specific question: if AgentFlame needs good semantic
clusters for sessions, tasks, prompts, and LLM calls, what should the clustering
pipeline be?

## Executive Conclusion

Semantic clustering itself is common. A modern production pipeline often looks
like:

```text
raw trace/session
  -> readable compact representation
  -> LLM structured summary
  -> embedding
  -> UMAP/HDBSCAN or graph clustering
  -> LLM cluster labeling
  -> dashboard with drilldown
```

PostHog describes almost exactly this pipeline for LLM traces. LangSmith
Insights exposes a productized version as hierarchical trace categories and
subcategories. BERTopic and Top2Vec provide the classic text-topic modeling
version of the same idea. AgentLens, AgentDiagnose, Landscape of Thoughts,
Insights Generator, and TraceSIR show academic variants for behavior timelines,
trajectory diagnosis, reasoning-state projection, and corpus-level trace
diagnostics.

Therefore, AgentFlame should not claim novelty for "semantic clustering of
agent traces." The useful design is:

```text
task segmentation first
  -> cluster task segments, not raw prompts
  -> label clusters after clustering
  -> keep cluster_id separate from one-word display_label
  -> use system effects as projection payload and merge veto, not as the
     primary semantic representation
  -> evaluate with pairwise same-task labels, label adequacy, stability,
     long-tail behavior, and downstream profile usefulness
```

The best default for AgentFlame is a hybrid:

```text
offline: task-segment embeddings + kNN graph + Leiden community detection
baseline: UMAP + HDBSCAN / BERTopic-style pipeline
labeling: small LLM labels cluster medoids, not every prompt
online: nearest-cluster assignment with strict similarity and margin gates
display: reversible one-word label layer with raw cluster drilldown
```

## What Industry Systems Do

### LangSmith Insights

Sources:

- https://docs.langchain.com/langsmith/insights
- https://www.langchain.com/blog/from-traces-to-insights-understanding-agent-behavior-at-scale
- https://www.langchain.com/blog/insights-agent-multiturn-evals-langsmith

What it clusters:

- Production traces and uploaded chat histories.
- User conversations / agent runs, not OS-level system effects.
- It can be scoped by filters, feedback, or user-provided analysis intent.

How it presents results:

- Hierarchical categorization: top-level categories, subcategories, and
  individual traces.
- Executive summary with percentages and trace references.
- Per-category metrics such as error rate, latency, cost, and evaluator scores.
- Drilldown from category to traces and annotation/dataset workflows.

What is known about the algorithm:

- Public docs do not expose the full clustering internals.
- The product description emphasizes unsupervised discovery of usage patterns,
  common agent behaviors, and failure modes.
- It supports arbitrary prompts / guided questions, which implies clustering is
  not a fixed taxonomy; users can ask for different dimensions.

Key lesson for AgentFlame:

- Hierarchical clustering is product-friendly. Users like `category ->
  subcategory -> trace`.
- The clustering job should be steerable: "cluster usage intents", "cluster
  failures", "cluster expensive tool use", or "cluster repeated file reads" are
  different questions.
- The UI must connect clusters to concrete evidence: representative traces,
  percentages, and metrics.

Limit relative to AgentFlame:

- LangSmith clusters traces/conversations, then reports trace-level metrics. It
  does not appear to construct a system-effect event graph with process/file/
  network/resource lineage and then profile those effects by cluster.

### PostHog LLM Trace Clustering

Source:

- https://posthog.com/blog/llm-analytics-clustering-how-it-works

This is the most explicit public industrial pipeline found in this survey.

Pipeline:

```text
1. Ingest traces/generations as events
2. Convert JSON trace blobs to readable text
3. Sample N traces/generations periodically
4. Use an LLM for structured summarization
5. Embed summaries
6. Run UMAP dimensionality reduction
7. Run HDBSCAN clustering
8. Use a labeling agent to name and describe clusters
9. Display scatter plot, distribution chart, and drilldown
```

Important details:

- They do not embed raw JSON directly. They first render traces into a readable
  text representation, then summarize.
- They use structured summaries, including title, flow diagram, bullets, and
  line references.
- They embed the summary rather than the raw trace because raw traces contain
  repeated system prompts, model versions, token counts, and other noise.
- They use UMAP twice: one reduced representation for clustering and a 2D
  representation for visualization.
- HDBSCAN is chosen because it does not require picking `k` and can assign
  outliers to a noise cluster.
- A labeling agent performs bulk labeling first for coverage, then drills into
  ambiguous clusters for refinement.
- Clustering jobs can be steered by analysis level and filters.

Why this matters:

- This confirms the obvious industrial baseline:

```text
summary-first embedding + UMAP + HDBSCAN + LLM labels
```

- It also confirms two practical truths:
  - Trace representation matters more than the clustering algorithm.
  - Labeling should happen after cluster discovery, not before.

Limit relative to AgentFlame:

- The output is product analytics over traces/generations. It is not a
  projection of process/file/network/resource effects.
- It samples traces for cost control, which is sensible for SaaS analytics but
  may hide rare but important local coding-agent behaviors.

### W&B Weave

Sources:

- https://docs.wandb.ai/weave/guides/tracking/tracing
- https://docs.wandb.ai/weave/guides/tracking/trace-tree
- https://wandb.ai/site/weave/

What it models:

```text
Thread -> Trace -> Call
```

- Ops are tracked functions.
- Calls are executions of ops, similar to spans.
- Traces are trees of calls.
- Threads group traces into a session/conversation.

What it visualizes:

- Trace tree.
- Timeline navigation.
- Code composition view.
- Flame graph view, where width is duration.
- Graph view of parent/child relationships.
- Metrics such as cost, tokens, and latency.

Clustering / aggregation:

- Public docs emphasize trace/session structure and analytics, not automatic
  semantic clustering as the central method.
- Weave is still important as a baseline because it already provides trace tree,
  graph, duration flame graph, cost/tokens/latency views, and agentic session
  organization.

Key lesson for AgentFlame:

- We cannot claim trace tree, span flamegraph, thread/session abstraction, or
  cost/latency trace analytics as novel.
- We should treat Weave-style trace and flame graph views as baseline views.

### Langfuse

Sources:

- https://langfuse.com/docs/observability/data-model
- https://langfuse.com/docs/observability/features/sessions
- https://langfuse.com/docs/observability/features/tags
- https://langfuse.com/docs/evaluation/scores/overview

What it models:

- Traces.
- Observations, including generations, tool calls, retrieval steps, and nested
  observations.
- Sessions, which group traces across multi-turn interactions.
- Scores and tags over traces, observations, sessions, and dataset runs.

Clustering / aggregation:

- Public docs emphasize observability, filtering, tags, score analytics, and
  sessions.
- There is no strong public claim that Langfuse performs automatic semantic
  trace clustering like LangSmith Insights or PostHog Clustering.

Key lesson for AgentFlame:

- Tags and metadata are a basic layer. They are useful for filtering and
  grouping, but manual tags are not a clustering solution.
- Score analytics is complementary: after clusters are built, scores and system
  metrics can be rolled up by cluster.

### Braintrust

Sources:

- https://www.braintrust.dev/articles/agent-observability-tracing-tool-calls-memory
- https://www.braintrust.dev/docs/observe
- https://www.braintrust.dev/docs/observe/filter

What it models:

- Traces as end-to-end agent runs.
- Spans for LLM calls, tool invocations, memory retrieval, etc.
- Sessions across related traces.
- Scores, metrics, filters, SQL queries, dashboards, and evaluation workflows.

Clustering / aggregation:

- Braintrust has strong trace/eval/dashboard primitives.
- Public docs emphasize aggregation by metrics, filters, scores, and custom
  dashboards rather than an exposed semantic clustering algorithm.

Key lesson for AgentFlame:

- Production users expect SQL/filter-style drilldown and metric rollups.
- Semantic clusters should become queryable attributes, not only pixels in a
  visualization.

### NVIDIA NeMo Agent Toolkit

Source:

- https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html

What it does:

- Profiles workflows down to tool and agent level.
- Tracks input/output tokens and timings.
- Integrates with LangSmith, Phoenix, Weave, Langfuse, and OpenTelemetry.

Clustering / aggregation:

- It is more workflow/profiling/evaluation infrastructure than a semantic
  clustering system.

Key lesson for AgentFlame:

- Tool/agent-level profiling is already expected. AgentFlame's clusters should
  add semantic grouping over this lower-level profile, not replace it.

## Academic Work

### AgentLens

Source:

- https://arxiv.org/html/2402.08995v1

Problem:

- Visual analysis of behaviors in LLM-based multi-agent autonomous systems.

Method:

- Abstracts LLMAS into system states, agents, tasks, and operations.
- Builds hierarchical behavior structure from raw execution events.
- Uses behavior summarization to aggregate event sequences over time.
- Uses cause tracing to connect behaviors to possible causes.
- Provides Outline View, Agent View, and Monitor View.

Evaluation:

- Usage scenarios and a 14-participant user study.
- Reports meaningful improvements for behavior analysis tasks.

Relevance:

- AgentLens is strong prior art for hierarchical agent behavior visualization.
- It shows that "LLM summarization + hierarchical behavior timeline + cause
  tracing" is already a known research direction.

Difference:

- It targets multi-agent simulation and behavior evolution, not coding-agent
  system effects.
- It summarizes behaviors over time; it does not fold file/network/resource
  effects into profile-like stacks by semantic intent.

### AgentDiagnose

Source:

- https://aclanthology.org/2025.emnlp-demos.15/

Problem:

- Diagnose LLM agent trajectories beyond final task success.

Method:

- Evaluation module for competencies such as backtracking/exploration, task
  decomposition, observation reading, self-verification, and objective quality.
- Visualization module with t-SNE action embeddings, interactive word clouds,
  and state-transition timelines.
- Filters a large trajectory dataset to choose better training examples.

Evaluation:

- On 30 manually annotated trajectories, automatic metrics have mean Pearson
  correlation 0.57 with human judgments, and 0.78 for task decomposition.
- Filtering 46k examples to top 6k improves WebArena success despite using only
  13% of the data.

Relevance:

- This is evidence that trajectory-derived semantic/behavioral metrics can be
  useful downstream.
- It also shows a common visualization pattern: project action/trajectory
  embeddings, summarize with word clouds, and inspect timelines.

Difference:

- It is not clustering coding-agent tasks into semantic effect profiles.
- It uses competency metrics more than open-vocabulary intent clusters.

### Landscape of Thoughts

Source:

- https://arxiv.org/html/2503.22165

Problem:

- Aggregate and visualize many LLM reasoning trajectories.

Method:

- Represents reasoning states using likelihood/perplexity distances to answer
  choices.
- Projects states into 2D for landscape visualization.
- Adds consistency, uncertainty, and perplexity metrics.
- Trains a lightweight random-forest verifier over derived state features.

Evaluation lesson:

- A visualization projection is more credible when it is tied to measurable
  features and downstream prediction, not just an attractive scatter plot.
- For AgentFlame, UMAP/t-SNE pictures should not be treated as proof. We need
  projection invariants, human labels, stability tests, and downstream utility.

Difference:

- LoT is about reasoning trajectories and answer choice geometry, not
  agent/tool/process/system effects.

### AgentStepper

Source:

- https://arxiv.org/html/2602.06593v1

Problem:

- Interactive debugging of software development agents.

Method:

- Adds hooks around LLM calls and tool calls.
- Records trajectory, prompts, tool outputs, and code changes.
- Supports breakpoints, stepwise execution, prompt/tool editing, and diff
  inspection.

Relevance:

- Strong prior art for single-run software-agent debugging.

Difference:

- It is not a cross-session clustering/profile system.
- It does not address open-vocabulary semantic clustering or system-effect
  profile aggregation.

### Agent Trajectory Explorer

Sources:

- https://ojs.aaai.org/index.php/AAAI/article/view/35350
- https://research.ibm.com/publications/agent-trajectory-explorer-visualizing-and-providing-feedback-on-agent-trajectories

Problem:

- Raw agent trajectories are not an ideal format for human analysis and
  oversight.

Method:

- Visualize, annotate, and demonstrate agent trajectories.

Relevance:

- More evidence that agent trajectory visualization and annotation tooling is
  already a crowded area.

Difference:

- It is about trajectory review and feedback, not semantic clustering into
  system-effect profiles.

### Insights Generator

Source:

- https://arxiv.org/html/2605.21347v3

Problem:

- Corpus-level trace diagnostics for LLM agents.
- Given a corpus of execution traces and a diagnostic question, produce grounded
  natural-language insights that characterize systematic patterns across trace
  groups.

Method:

- Multi-agent scout-investigator architecture.
- Proposes and tests hypotheses across trace corpora.
- Generates evidence-backed insight reports.
- Uses union-gold clusters for evaluation: findings are clustered by underlying
  phenomenon, then reports are scored against those clusters.

Evaluation:

- Evaluates detection coverage, mechanism, evidence, specificity, and
  actionability.
- Reports downstream scaffold improvement after implementing generated
  insights.

Relevance:

- This is very close in spirit to "trace aggregation with evidence."
- It makes naive cluster dashboards look weak. A serious system should generate
  insights tied to supporting trace IDs and evidence.

Difference:

- It outputs natural-language diagnostic reports, not interactive folded
  profiles over system effects.
- It does not build an OS/process/file/network effect model.

### TraceSIR

Source:

- https://arxiv.org/html/2603.00623v1

Problem:

- Long agent execution traces exceed LLM context limits and make root-cause
  analysis hard.

Method:

- StructureAgent transforms raw OpenAI message traces into TraceFormat, a compact
  thought/action/observation representation.
- InsightAgent performs per-instance diagnosis.
- ReportAgent aggregates per-instance insights into cross-case analysis reports.
- Evaluation uses TraceBench and ReportEval over deep research, function
  calling, and agentic coding scenarios.

Important warning:

- TraceSIR explicitly argues that naive summarization and clustering-style
  aggregation can lose trace-level evidence and produce coarse reports.

Relevance:

- This is a strong warning for AgentFlame: clustering must preserve drilldown and
  evidence. A cluster label without representative events and metrics is not
  enough.

Difference:

- TraceSIR is a report generator over thought/action/observation traces; it is
  not a profile visualization or system-effect attribution/projection system.

### XAI For Coding Agent Failures

Source:

- https://arxiv.org/html/2603.05941v1

Problem:

- Transform raw coding-agent execution traces into actionable failure
  explanations.

Method:

- Domain-specific failure taxonomy.
- Automatic annotation/classification.
- Visual execution flows, natural-language explanations, and recommendations.

Evaluation:

- User study with 20 participants.
- Reports faster root-cause identification and better fix suggestions compared
  with raw traces and ad-hoc LLM explanations.

Relevance:

- A taxonomy can be useful for failure clustering, but it is different from
  open-vocabulary task clustering.
- Visual flow plus structured explanation is an important baseline for failure
  analysis.

### Understanding Code Agent Behaviour

Source:

- https://arxiv.org/html/2511.00197v1

Problem:

- Empirical study of success/failure trajectories from code agents on SWE-Bench.

Method:

- Analyzes trajectories from OpenHands, SWE-agent, and Prometheus.
- Identifies behaviors such as defensive programming and context gathering.
- Compares success/failure trajectory length, variance, localization behavior,
  and patterns.

Relevance:

- Provides useful behavior categories and metrics for coding-agent trajectory
  analysis.

Difference:

- It is an empirical study, not a reusable clustering algorithm or profile UI.

### AgentOps And AgentTrace

Sources:

- https://arxiv.org/html/2411.05285v2
- https://arxiv.org/html/2602.10133v1

What they contribute:

- AgentOps provides a taxonomy of artifacts and observability features for LLM
  agents.
- AgentTrace proposes structured logging for agent observability.

Relevance:

- These papers are schema/taxonomy baselines. They define what should be traced,
  not how semantic clusters should be constructed.

## General Text-Clustering Baselines

### BERTopic

Source:

- https://ar5iv.labs.arxiv.org/html/2203.05794

Pipeline:

```text
document embeddings
  -> dimensionality reduction, typically UMAP
  -> HDBSCAN clustering
  -> c-TF-IDF topic representation
```

Why it matters:

- It is a standard baseline for embedding-based topic modeling.
- It separates cluster discovery from topic representation.
- It evaluates with topic coherence and topic diversity, while warning that
  these are only proxies for subjective usefulness.

AgentFlame lesson:

- Use BERTopic-style pipeline as a baseline, not as final design.
- c-TF-IDF-like descriptors can help explain clusters, but one-word labels still
  need LLM/human governance.

### Top2Vec

Source:

- https://arxiv.org/abs/2008.09470

Pipeline:

- Jointly embeds documents and words.
- Finds dense semantic regions/topics.
- Automatically estimates the number of topics.

AgentFlame lesson:

- Useful baseline, but less attractive for agent traces because task segments
  contain structured metadata, tool names, code paths, and trace context that do
  not behave like ordinary documents.

### UMAP + HDBSCAN

Sources:

- https://umap-learn.readthedocs.io/en/latest/clustering.html
- https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html
- https://hdbscan.readthedocs.io/en/latest/basic_hdbscan.html

Why people use it:

- UMAP can make high-dimensional embeddings more clusterable.
- HDBSCAN does not require a fixed number of clusters.
- HDBSCAN has a noise notion, which is valuable for long-tail trace data.

Cautions:

- UMAP for clustering is common but must be used carefully.
- HDBSCAN can return too much noise or one giant cluster depending on density
  and parameters.
- 2D UMAP/t-SNE plots are visualization aids, not correctness evidence.

### kNN Graph + Leiden

Source:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/

Pipeline:

```text
embedding vectors
  -> approximate nearest neighbor index
  -> weighted kNN similarity graph
  -> community detection with Leiden
```

Why it is attractive for AgentFlame:

- Better fit for incremental assignment: new items can compare against cluster
  medoids and local neighbors.
- Supports graph edges with multiple signals: semantic similarity, same repo,
  shared files, same task segment, or temporal adjacency.
- Communities can be made more conservative by thresholding edges.
- Leiden improves on Louvain by avoiding badly connected communities.

Tradeoff:

- Requires choosing graph construction parameters: embedding model, `k`, minimum
  similarity, edge weighting, and resolution.
- Less off-the-shelf as a product analytics pipeline than BERTopic/HDBSCAN.

## Algorithmic Patterns Found

### Pattern A: Prompt-First Tagging

```text
prompt -> LLM one-word tag -> group by tag
```

Pros:

- Extremely simple.
- Cheap if using a small local model.
- Produces directly readable labels.

Cons:

- Collapses to generic labels such as `review`, `refactor`, `debug`, `test`.
- Fails on continuation prompts like "继续", "这个呢", "再画几个".
- One word is too small to be a stable cluster identity.
- Bad labels directly become bad clusters.

Use in AgentFlame:

- Only as a baseline or as a secondary display label.
- Do not use as the main clustering algorithm.

### Pattern B: Summary-First Embedding Clustering

```text
trace/task -> structured summary -> embedding -> HDBSCAN/BERTopic -> cluster
```

Pros:

- Strong industrial precedent: PostHog.
- Reduces noisy raw trace structure.
- Works with ordinary text-clustering tools.
- Allows LLM summaries to include line/event references.

Cons:

- Summaries may hallucinate or hide low-level details.
- Cost can be high if every trace is summarized by a large model.
- Generic schemas may not fit coding-agent tasks.

Use in AgentFlame:

- Good baseline and likely good first production version.
- Use local/small summary/tag model where possible.
- Keep event IDs and evidence references in every summary.

### Pattern C: Hierarchical Categorization

```text
trace corpus + question -> top-level categories -> subcategories -> traces
```

Pros:

- Product-friendly.
- Supports different analysis questions.
- Matches LangSmith Insights and Insights Generator.

Cons:

- Often LLM-heavy and harder to make deterministic.
- More report-like than profile-like.
- Can generate plausible but weakly grounded categories unless evidence is
  enforced.

Use in AgentFlame:

- Good for "insight reports" and review queues.
- For flamegraphs, use clusters as stable IDs and labels, not free-form report
  categories only.

### Pattern D: Graph Clustering

```text
task segments -> embeddings -> kNN graph -> community detection
```

Pros:

- Good for incremental systems.
- Easy to add conservative edge gates.
- Supports multi-signal edges.
- Does not force everything into clusters if edges are thresholded.

Cons:

- Needs more engineering.
- Parameter tuning matters.
- Requires separate cluster labeling.

Use in AgentFlame:

- Best candidate for the real product path.
- HDBSCAN/BERTopic should be kept as baselines.

### Pattern E: Taxonomy Classification

```text
trace -> predefined failure / competency / behavior taxonomy
```

Pros:

- Easier to evaluate.
- Good for known failure modes.
- Useful for dashboards and alerts.

Cons:

- Does not discover unexpected tasks.
- Poor fit for open-vocabulary coding sessions where user goals vary.

Use in AgentFlame:

- Use for failure-mode views, not primary task clustering.

## What Should Be Clustered

### Bad Unit: Raw Prompt

Raw prompts are often not self-contained:

```text
继续
这个呢？
再画一些图
commit push
```

Clustering these directly causes nonsense clusters or excessive dependence on
nearby context. Prompt-level tags can exist, but they should be derived from a
resolved context.

### Best Unit: Task Segment

A task segment is a contiguous block of turns inside a session that shares one
user intent.

Example:

```text
session
  task segment: literature survey
    prompt: 有对应论文吗？
    prompt: agent flamegraph 有人做过了？
    prompt: agent visualization aggregation 的有吗？
  task segment: git checkpoint
    prompt: research/semantic-flamegraph-artifacts commit push
  task segment: clustering design
    prompt: 聚类怎么聚类好？
    prompt: 去仔细调研别人怎么做的
```

Why this is better:

- It resolves short continuation prompts.
- It groups tool calls and LLM calls under a meaningful local intent.
- It avoids making one prompt carry the burden of an entire workflow.

### Secondary Units

Session cluster:

- Useful for "what kind of session was this?"
- Too coarse for profiling fine-grained effects.

LLM-call cluster:

- Useful for token/cost analysis.
- Should be labeled by call purpose: planning, summarizing, reviewing, editing,
  debugging, reporting.

Tool-call/process cluster:

- Usually structural, not semantic.
- Better handled as projection payload: shell/read/write/test/network/process.

## Representation Design

Do not embed raw traces directly. Use a compact, grounded representation:

```text
task_segment_id: stable id
session_context: 1-2 sentences
resolved_user_intent: short self-contained sentence
turns: selected user prompts
assistant_actions: compact summary
llm_calls: count, models, rough purposes
tool_calls: kind counts and notable commands
files: mentioned/touched top paths
effects: file/network/test/resource summary
evidence_refs: event ids / turn ids / line refs
```

Weighting:

```text
primary: resolved user intent and nearby conversation context
secondary: assistant actions and LLM-call purposes
tertiary: files and tool kinds
veto metadata: system effect profile
```

Why system effects should not dominate:

- `cargo test` occurs in many tasks.
- `rg` and `sed` are generic coding-agent behavior.
- If system effects dominate embeddings, unrelated tasks merge because they use
  the same tools.

But system effects are still useful as merge vetoes:

```text
If two clusters have similar text labels but very different effect profiles,
do not auto-merge high-support clusters without review.
```

## Recommended AgentFlame Clustering Pipeline

### Step 1: Build Task Segments

Inputs:

- Session turns.
- User prompts.
- LLM calls and tool calls.
- Files/effects under each turn.

Algorithm:

```text
for adjacent turns:
  compute text similarity over resolved prompt/context
  compute file/topic overlap
  detect continuation prompts
  ask small model same_task/new_task when uncertain

start a new segment if:
  user explicitly changes objective
  adjacent semantic similarity below threshold
  tool/file focus changes strongly and prompt is not continuation
  long time gap or commit/push/checkpoint boundary
```

Small model prompt should be binary, not open-ended:

```text
Given previous task summary and current user turn, answer same or new.
Return exactly one token: same or new.
```

Reason:

- Segmentation is easier than full labeling.
- Errors can be bounded by conservative thresholds and manual review.

### Step 2: Generate Grounded Segment Summaries

Use a small/local model or deterministic template plus optional LLM polish.

Output schema:

```json
{
  "resolved_intent": "...",
  "actions": ["..."],
  "objects": ["..."],
  "evidence_refs": ["turn:...", "tool:...", "effect:..."],
  "candidate_words": ["..."]
}
```

Rules:

- Do not ask for a final cluster label yet.
- Keep evidence references.
- Use short summaries; embeddings should not include huge raw logs.

### Step 3: Embed Task Segments

Practical choices:

- Local default: `bge-small`, `bge-base`, `e5-small`, or `all-MiniLM-L6-v2`.
- Cloud optional: OpenAI/Cohere embeddings for higher quality.
- Store embedding model name and version in artifacts.

Important:

- Use the same embedding input across ablations.
- Normalize vectors for cosine similarity.
- Cache embeddings by summary hash.

### Step 4: Cluster

Recommended default:

```text
build approximate kNN graph over normalized embeddings
keep edge i-j only if cosine >= threshold
weight edge = semantic similarity
optionally add small bonuses for temporal adjacency or shared files
run Leiden with resolution parameter
mark weakly connected/small clusters as pending/noise
```

Why not only HDBSCAN:

- HDBSCAN is a great baseline, but incremental assignment is awkward.
- It can create large noise mass or one giant cluster depending on density.
- kNN graph clustering gives more direct control over conservative merge gates.

Baselines to keep:

```text
B0 prompt-first one-word tag
B1 no-segmentation prompt embeddings + HDBSCAN
B2 task-segment embeddings + HDBSCAN
B3 BERTopic-style UMAP/HDBSCAN/c-TF-IDF
B4 task-segment kNN + Leiden
B5 task-segment kNN + Leiden + effect-profile veto
```

### Step 5: Label Clusters After Clustering

Do not label every prompt first. Label clusters.

Cluster labeling input:

```text
cluster_id
support count
medoid summaries, 3-7 examples
top user-intent phrases
top files/actions
top effect kinds, shown as supporting context
negative neighbor examples if available
```

LLM output:

```json
{
  "display_label": "review",
  "description": "short hidden description",
  "confidence": 0.0,
  "too_broad": false,
  "needs_split": false
}
```

One-word label rules:

- Exactly one lowercase word for the visible label.
- No fixed preferred vocabulary in the raw prompt.
- Avoid `work`, `task`, `misc`, `other`, `update`, `change`, `code` unless truly
  unavoidable.
- If no good word exists, produce a specific neologism only if the cluster is
  coherent; otherwise mark `needs_split`.

Critical design point:

```text
cluster_id != display_label
```

Two clusters may both display as `review`. Internally they remain different.
The default flamegraph may merge same display labels, but drilldown must reveal
cluster IDs and raw examples.

### Step 6: Online Assignment

For a new task segment:

```text
embed segment
find nearest cluster medoids and nearest examples
assign automatically only if:
  top_similarity >= hard threshold
  top_similarity - second_similarity >= margin
  cluster is not high-risk/pending
  effect-profile veto does not fire
otherwise:
  create pending cluster or noise bucket
```

Periodic offline job:

- Re-cluster pending/noise.
- Check cluster drift.
- Recompute medoids.
- Re-label changed clusters.
- Produce review queue for large merges/splits.

### Step 7: Display Governance

Display governance is not semantic truth. It is a safety layer:

```text
raw cluster -> display label -> merged display bucket -> drilldown
```

Rules:

- All merges must be reversible.
- Large-support merges need stronger evidence or review.
- Do not auto-merge semantically distinct high-level tasks such as `debug`,
  `test`, `review`, `refactor`, `design`, `research`.
- Long-tail items can be rolled into a visible "pending" or "rare" lane, but raw
  tags and cluster IDs must remain visible on drilldown.

## Evaluation Plan

### E1: Pairwise Same-Task Labels

Create a labeled set of task-segment pairs:

```text
same intent / different intent / ambiguous
```

Sampling:

- Near-neighbor pairs from embeddings.
- Same display-label pairs.
- Different display-label but same files/effects pairs.
- Random negatives.
- Continuation-prompt cases.

Metrics:

- Pairwise precision/recall/F1.
- B-cubed precision/recall/F1.
- False-merge rate for high-support clusters.
- False-split rate for obvious same tasks.

Why this is the central evaluation:

- Clustering correctness is fundamentally pairwise/similarity-based.
- It avoids pretending there is one universal gold taxonomy.

### E2: Label Adequacy

Human asks:

```text
Given cluster examples and display_label, is the label adequate?
```

Labels:

- adequate
- too generic
- misleading
- too narrow
- needs split
- needs merge

Metrics:

- Adequacy rate.
- Generic-label rate.
- Misleading-label rate.
- Inter-annotator agreement.

### E3: Stability

Run clustering under:

- Different random seeds.
- Bootstrap samples.
- Slightly different embedding inputs.
- Different embedding models.
- New sessions appended.

Metrics:

- Adjusted Rand Index / NMI across runs.
- Cluster survival rate.
- Label stability.
- Top cluster support drift.

### E4: Long-Tail Quality

Metrics:

- Effective cluster count.
- Top-1 and top-5 support share.
- Tail mass below support thresholds.
- Number of singleton clusters.
- Percent of tail judged meaningful vs noise.
- Number of display buckets after reversible compaction.

Goal:

- Not "fewer clusters."
- The target is high semantic diversity with low meaningless fragmentation.

### E5: Projection Utility

User tasks:

- Find which task categories caused most file reads.
- Find repeated testing/debug loops.
- Find token-heavy tasks with little system effect.
- Find clusters with high network or build/test cost.
- Find likely over-merged labels.

Baselines:

- Raw trace list.
- Span-duration flamegraph.
- Process/effect summary without semantic clustering.
- Prompt-first one-word grouping.

Metrics:

- Task completion time.
- Accuracy against an answer key.
- Confidence.
- False insight rate.
- Qualitative usefulness.

### E6: Evidence Retention

Every cluster-level claim must link to:

- Representative task segments.
- Original prompts.
- Tool/process/effect event IDs.
- Weight totals used in the projection.

Metrics:

- Drilldown completeness.
- Projection weight conservation.
- Percent of cluster insights with at least N concrete evidence examples.

This is where AgentFlame should differ from ordinary semantic dashboards.

## What To Build Next

### R223: Same-Fragment Clustering Ablation

Dataset:

- Use existing local Codex/Claude sessions.
- Build task segments from the same frozen session corpus.
- Include continuation-heavy user turns.

Compared systems:

```text
B0 prompt-first one-word tags
B1 raw prompt embeddings + HDBSCAN
B2 task-segment summaries + HDBSCAN
B3 task-segment summaries + BERTopic-style c-TF-IDF labels
B4 task-segment summaries + kNN/Leiden
B5 kNN/Leiden + effect-profile merge veto
```

Outputs:

```text
docs/visexp/out/clustering-ablation-r223/
  task-segments-r223.csv
  pairwise-label-packet-r223.csv
  cluster-summary-*.csv
  cluster-labels-*.csv
  metrics-r223.json
  report-r223.md
```

Primary metrics:

- Pairwise same-task F1.
- High-support false-merge rate.
- Label adequacy rate.
- Top-1 collapse rate.
- Effective cluster count.
- Tail meaningful/noise ratio.
- Runtime and model cost.

### Product Defaults

Default user experience:

```text
agentflame cluster --input .agentsight/agentflame/latest/agentflame.json
agentflame view --projection semantic-effects
```

Default outputs:

- Semantic flamegraph.
- Cluster table.
- Tag/cluster long-tail view.
- Drilldown to task segments and raw prompts.
- Profile rollups by cluster: file reads/writes, test runs, network, token cost,
  process count, duration.

Default model behavior:

- Local embeddings by default.
- Local small LLM for cluster labels if available.
- Cloud labeler optional.
- No preferred word list in raw labeling prompt.
- One-word labels visible; descriptions hidden in drilldown.

## Research Positioning

Weak claim:

```text
We cluster agent traces semantically.
```

This is not enough. It is common.

Stronger claim:

```text
AgentFlame builds task-level semantic clusters over coding-agent histories and
uses them as stable, evidence-preserving indices for system-effect profiles.
```

Even stronger:

```text
AgentFlame separates cluster discovery, cluster labeling, effect projection, and
display compaction, and evaluates each layer independently: same-task clustering
quality, label adequacy, projection invariants, long-tail readability, and
developer utility.
```

The novelty is not the clustering algorithm. The novelty has to be the combined
system:

```text
task-segment semantic clustering
  + exact-ish agent event graph
  + system-effect projection
  + reversible display governance
  + evidence-grounded profile drilldown
```

## Practical Recommendation

Use this design unless experiments falsify it:

```text
1. Segment sessions into task segments.
2. Generate grounded summaries with evidence refs.
3. Embed summaries.
4. Cluster with kNN graph + Leiden.
5. Compare against HDBSCAN/BERTopic baselines.
6. Label clusters after clustering with a small LLM.
7. Keep cluster_id and one-word display_label separate.
8. Use system-effect profile only as payload and merge veto.
9. Evaluate with pairwise same-task labels before claiming correctness.
10. Render semantic profiles by cluster/display label with reversible drilldown.
```

This is the Pareto point:

- Better than prompt-first one-word tags.
- More stable than pure LLM taxonomy generation.
- Easier to productize incrementally than fully agentic report generation.
- More defensible academically because clustering, labeling, projection, and
  display are separately testable.

## Source Index

Industry:

- LangSmith Insights docs: https://docs.langchain.com/langsmith/insights
- LangSmith trace insights blog: https://www.langchain.com/blog/from-traces-to-insights-understanding-agent-behavior-at-scale
- LangSmith Insights launch: https://www.langchain.com/blog/insights-agent-multiturn-evals-langsmith
- PostHog LLM trace clustering: https://posthog.com/blog/llm-analytics-clustering-how-it-works
- W&B Weave trace concepts: https://docs.wandb.ai/weave/guides/tracking/tracing
- W&B Weave trace view: https://docs.wandb.ai/weave/guides/tracking/trace-tree
- Langfuse data model: https://langfuse.com/docs/observability/data-model
- Braintrust agent observability: https://www.braintrust.dev/articles/agent-observability-tracing-tool-calls-memory
- NVIDIA NeMo Agent Toolkit: https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html

Academic:

- AgentLens: https://arxiv.org/html/2402.08995v1
- AgentDiagnose: https://aclanthology.org/2025.emnlp-demos.15/
- Landscape of Thoughts: https://arxiv.org/html/2503.22165
- AgentStepper: https://arxiv.org/html/2602.06593v1
- Agent Trajectory Explorer: https://ojs.aaai.org/index.php/AAAI/article/view/35350
- Insights Generator: https://arxiv.org/html/2605.21347v3
- TraceSIR: https://arxiv.org/html/2603.00623v1
- XAI for Coding Agent Failures: https://arxiv.org/html/2603.05941v1
- Understanding Code Agent Behaviour: https://arxiv.org/html/2511.00197v1
- AgentOps: https://arxiv.org/html/2411.05285v2
- AgentTrace: https://arxiv.org/html/2602.10133v1

General clustering:

- BERTopic paper: https://ar5iv.labs.arxiv.org/html/2203.05794
- Top2Vec: https://arxiv.org/abs/2008.09470
- UMAP clustering guide: https://umap-learn.readthedocs.io/en/latest/clustering.html
- HDBSCAN docs: https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html
- Leiden algorithm paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC6435756/
