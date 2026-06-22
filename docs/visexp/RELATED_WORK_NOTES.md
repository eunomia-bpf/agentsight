# Related Work Notes: Agent Visualization, Debugging, And Semantic Effect Profiling

Last updated: 2026-06-16
Completeness: working scan, not a final systematic review

## Main Takeaway

Existing work already covers agent trace trees, duration flamegraphs, multi-agent
timeline visualization, interactive software-agent debugging, and LLM reasoning
trajectory aggregation. AgentFlame should not claim any of those broad areas as
new.

The defensible gap is narrower:

> Post-hoc semantic effect profiling for coding agents: build an event graph
> from sessions, prompts, LLM calls, tool calls, shell/process trees, and
> file/network/resource effects; then generate projection-specific folded views
> that aggregate system effects by semantic intent while preserving drilldown to
> raw events.

The hard research problem is not "can we draw a flamegraph?" It is whether the
projection is faithful, readable, and useful:

1. Faithful: projection functions conserve input weights and preserve drilldown.
2. Semantically adequate: small-model tags are useful enough and do not collapse
   into generic labels.
3. Readable: long-tail display compaction removes noise without hiding real task
   diversity.
4. Useful: developers can answer questions about repeated work, heavy tasks,
   expensive LLM calls, and surprising system effects faster than with raw traces
   or span-duration views.

## Existing Span-Duration / Workflow Views

These systems already cover agent traces, span trees, timelines, or
flamegraph-style views. AgentFlame should treat them as baselines, not novelty.

| System | Public reference | Relevant capability | Implication for AgentFlame |
|--------|------------------|---------------------|----------------------------|
| SigNoz + Inkeep | https://signoz.io/blog/inkeep-ai-agent-monitoring/ | Explicit "Flamegraph for Debugging" for multi-agent workflows; each horizontal bar is a span and width is duration; used for sequential/parallel execution, error cascades, tool overhead, and sub-agent boundaries. | Do not claim agent flamegraphs or span-duration workflow debugging as new. |
| OpenSearch Agent Traces | https://docs.opensearch.org/latest/observing-your-data/agent-traces/agent-tracing/ | Agent graph, trace tree view, and Gantt-style timeline over agent spans. | Treat trace tree/timeline/graph as standard baselines. |
| Datadog Trace View | https://docs.datadoghq.com/tracing/trace_explorer/trace_view/ | Waterfall and Flamegraph visualizations with span search and span metadata. | Span flamegraph and span search are prior art. |
| LangSmith | https://www.langchain.com/langsmith/observability | Agent tracing, cost/latency/error monitoring, trajectory monitoring, OpenTelemetry support. | Baseline for agent/LLM/tool trace observability. |
| Langfuse | https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse | Agent observability for LangGraph, OpenAI Agents, Pydantic AI, CrewAI, n8n; industry convergence around OpenTelemetry. | Baseline for production agent tracing and evaluation workflow. |
| Phoenix / OpenInference | https://arize-ai.github.io/openinference/ and https://arize.com/docs/phoenix/integrations/python/agentspec/agentspec-tracing | OpenInference semantic conventions and Agent Spec tracing over agent workflows. | Baseline for portable LLM/agent span conventions. |
| Agentrial | https://github.com/marketplace/actions/agentrial-ci | Trajectory flame graphs across agent trials, plus multi-agent evaluation metrics. | Baseline for trajectory/run comparison, not exact system-effect provenance. |
| Braintrust | https://www.braintrust.dev/articles/agent-observability-tracing-tool-calls-memory | Traces, spans, and sessions for LLM calls, tool invocations, memory retrieval, and evaluation loops. | Baseline for agent trace/eval integration. |

## Academic Agent Visualization And Debugging Papers

### AgentLens

Reference: https://arxiv.org/html/2402.08995v1

Question addressed:

- How can users inspect and understand complex behavior evolution in
  LLM-based autonomous systems with many agents?

Data model:

- Abstracts LLMAS into four layers: system states, agents, tasks, and
  operations.
- Groups raw execution events into agent behaviors over time.
- Task categories are perceive, think, and act.

Core method:

- Collect raw execution logs from an LLMAS.
- Convert raw events into structured behaviors.
- Use an external summarization model to produce concise behavior descriptions.
- Embed behavior summaries and run change-point segmentation to split timelines
  into hierarchical behavior segments.
- Trace causes in two ways:
  - Explicit causes from logged provenance links, such as memory references.
  - Implicit causes from text-similarity links among prior operations.

Visual design:

- Outline View: multi-agent timeline curves, location changes, interactions,
  topic search, and hierarchical timeline summaries.
- Agent View: details for one agent, behavior summaries, memory, causal links,
  and minimap navigation.
- Monitor View: synchronized replay-style view to validate the current visual
  finding against the underlying simulation state.

Evaluation:

- Uses task-based analysis and interviews on a multi-agent simulation setting.
- Reports large reductions in task completion time for several analysis tasks
  compared with a baseline log/video interface, including 33% to 78.3% time
  reductions on individual and multi-agent behavior tasks.
- Reports a 71.6% improvement on a difficult behavior-cause task.
- For emergent phenomena tasks, users could identify topic propagation,
  agent congregation, and unexpected behavior that baseline users often found
  impractical.
- SUS usability score reported as 67.5.

What it already covers:

- Hierarchical semantic summarization of agent event histories.
- Multi-agent temporal visualization.
- Cause/provenance-style links among agent behaviors.
- Search and drilldown over summarized behavior timelines.

Limitations relative to AgentFlame:

- Focuses on LLMAS/social or simulated agent behavior, not coding-agent system
  effects.
- The unit being summarized is an agent behavior timeline, not a
  prompt/tool/process/effect event graph.
- Causality is partly explicit logs and partly text similarity; it is not exact
  shell/process/file/network lineage.
- It does not produce folded flamegraph-style profiles across many local coding
  sessions by semantic task and system effect.
- It does not evaluate one-word open-vocabulary tags or long-tail display
  governance.

Implication:

- We cannot claim "hierarchical agent behavior visualization" or
  "LLM-assisted event summarization" as novel.
- We can contrast against AgentLens by saying AgentLens summarizes agent
  behaviors over time, while AgentFlame profiles concrete system effects by
  semantic intent across coding-agent histories.

### AgentStepper

Reference: https://arxiv.org/html/2602.06593v1

Question addressed:

- How can developers interactively understand and debug software development
  agents?

Data model:

- Represents a software-agent trajectory as structured conversations among:
  LLM, agent program, and tools.
- Captures LLM queries/responses, tool invocations/outputs, and
  repository-level code changes.

Core method:

- Adds a small API to agent programs around LLM calls and tool calls.
- Supports post-hoc trajectory inspection and live debugging.
- Generates short event summaries for LLM queries, LLM responses, tool calls,
  and tool outputs.
- Records intermediate code changes as commit-like snapshots after tool
  invocations.

Visual/debugging interface:

- Conversation-style trajectory view.
- Full message inspector with diff support for prompts and structured messages.
- Side panel for repository-level changes and diffs.
- Breakpoints before/after LLM calls and tool calls.
- Stepwise execution.
- Live editing of prompts, LLM responses, tool invocation arguments, and tool
  outputs.

Evaluation:

- Integrated into SWE-Agent, RepairAgent, and ExecutionAgent.
- Required 5 to 7 API calls, 3 to 5 modified files, and 39 to 42 changed lines
  per agent.
- User study with 12 participants.
- Trajectory comprehension improved only modestly, from 64% to 67% median
  performance.
- Bug identification improved from 17% to 60% success.
- Perceived frustration decreased from 5.4/7.0 to 2.4/7.0.

What it already covers:

- Interactive debugger for software development agents.
- Breakpoints and stepping at agent-level abstractions.
- Prompt/tool live editing.
- Intermediate code-change visibility.
- One-sentence event summaries for trajectory browsing.

Limitations relative to AgentFlame:

- It is primarily a debugger for one trajectory, not a profiler over many
  sessions.
- It requires in-agent instrumentation/API calls.
- It does not observe out-of-process system effects below tool invocations.
- It does not aggregate file/network/resource effects by semantic prompt or LLM
  call tag.
- It does not address open-vocabulary tag compaction, projection correctness, or
  flamegraph profile construction.

Implication:

- We cannot claim "interactive debugging of coding agents" as novel.
- We should position AgentFlame as complementary: AgentStepper helps a developer
  step through and edit one run; AgentFlame helps a developer summarize where
  many runs spend effort and which intents caused which system effects.

### Landscape of Thoughts

Reference: https://arxiv.org/html/2503.22165

Question addressed:

- How can practitioners aggregate and visualize large collections of LLM
  reasoning trajectories instead of manually reading chains of thought?

Data model:

- Targets multiple-choice reasoning tasks.
- A trajectory is a sequence of intermediate textual thoughts ending in a final
  answer.
- Each intermediate thought/state is represented by model-derived features:
  relative perplexity-based distances from that state to each answer choice.

Core method:

- Sample multiple reasoning trajectories.
- Parse trajectories into thought units.
- Compute state features using the same open-source LLM as a likelihood
  estimator.
- Project states into 2D with t-SNE, while defining core claims in the original
  answer-distance feature space.
- Draw density landscapes for successful and failed trajectories.
- Add quantitative metrics: consistency, uncertainty, and perplexity.

Evaluation:

- Compares across model scales, reasoning tasks, and reasoning methods.
- Datasets include AQuA, MMLU, StrategyQA, and CommonsenseQA.
- Methods include CoT, least-to-most, tree-of-thought, and MCTS.
- Reports observations such as:
  - Larger models converge more efficiently to correct regions.
  - Incorrect trajectories often converge early to wrong answers.
  - Correct trajectories have higher intermediate consistency.
  - Similar reasoning tasks produce similar landscape patterns.
- Builds a lightweight random-forest verifier over state features and
  consistency; evaluates it against unweighted voting and reports improved
  test-time scaling.
- Includes ablations showing consistency plus 2D/state information performs
  better than either alone.

What it already covers:

- Scalable aggregation of reasoning trajectories.
- Visualization plus quantitative metrics.
- A learned lightweight model over visualization-derived features.
- Evaluation of whether the visual projection reflects measurable structure,
  including robustness checks across dimensionality reduction methods.

Limitations relative to AgentFlame:

- It is about internal reasoning trajectories, not agent system behavior.
- It assumes multiple-choice answers and access to token probabilities from
  open-source LLMs.
- It has no tool calls, shell processes, file/network effects, or repository
  mutations.
- It does not perform intent-to-effect attribution.
- Its projection correctness is grounded in answer-choice distance features;
  AgentFlame needs different invariants because our inputs are event graphs and
  system-effect weights.

Implication:

- LoT is an important warning: a strong visualization paper must show that the
  projection encodes real measurable structure, not just pretty plots.
- For AgentFlame, the analogous evidence should be:
  - projection weight conservation and drilldown invariants;
  - same-fragment tag ablations;
  - human adequacy labels for semantic tags;
  - downstream task usefulness compared with trace/log baselines.

## What These Papers Already Make Non-Novel

AgentFlame should not claim novelty for:

1. Agent trace trees, timelines, or span-duration flamegraphs.
2. Multi-agent timeline visualization.
3. Hierarchical LLM summarization of agent events.
4. Cause links among agent behaviors.
5. Interactive software-agent debugging with breakpoints and stepping.
6. Prompt/tool-call inspection and live editing.
7. Aggregated visualization of LLM reasoning trajectories.
8. Using visualization-derived features for a lightweight predictor.

## Remaining Defensible AgentFlame Delta

AgentFlame should be framed as semantic effect profiling, not generic agent
visualization:

```text
event graph:
  session/run -> prompt/turn -> {llm_call, tool_call, subagent_session}
  tool_call -> process* -> effect/resource/error

projection examples:
  prompt_tag -> tool_kind -> process_chain -> io_kind -> target_group -> status
  prompt_tag -> llm_call_tag -> model -> token_kind
  process/resource -> prompt_tag/session_tag
```

The claimable delta is the combination of:

1. Open-vocabulary one-word semantic indices for session, prompt, and LLM-call
   context, generated locally by a small model.
2. Deterministic lineage from tool calls through shell/child processes to
   file/network/resource effects.
3. Projection-specific folded profiles over many sessions, where width can mean
   effect count, bytes, duration, tokens, cost, or resource usage depending on
   the question.
4. Reversible display governance for long-tail tags: compact display without
   hiding raw tags or losing drilldown.
5. Projection correctness tests that separate event-graph integrity,
   projection invariants, tag adequacy, and user-task utility.

R114-style exact lineage is therefore an integrity check, not the main
contribution. The main experiments must show that semantic projections reveal
structure that raw traces, span flamegraphs, and ordinary process summaries do
not reveal.

## Paper Positioning Sentence

Prior systems help users inspect agent workflows, debug individual software
agent trajectories, or visualize reasoning states. AgentFlame instead treats
agent histories as profileable event graphs: it uses semantic tags as compact
indices over prompts and LLM calls, then folds concrete system effects into
projection-specific profiles so developers can see which kinds of work caused
which file, network, resource, token, and process costs across many coding-agent
sessions.
