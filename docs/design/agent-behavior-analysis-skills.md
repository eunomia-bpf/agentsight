# Agent Behavior Analysis Skills 设计

日期：2026-06-20（America/Vancouver）。本文是产品/设计草案，不是当前 CLI 行为说明。当前用户文档仍以 [README](../../README.md)、[Usage](../usage.md)、[OpenTelemetry GenAI Export](../otel.md) 和 [agent-session](../agent-session.md) 为准。

## 结论

第一版不拆成 `inventory -> friction -> artifact` 三个 pipeline skills，也不做一个什么都读的大 skill。更合理的是按 **证据边界** 拆成两个：

```text
agent-interaction-insights
  读对话、session logs、LLM traces
  分析用户交互、目标漂移、loop、summary trust、validation claim

agentsight-system-friction
  读 AgentSight/system evidence
  分析进程、命令、文件、网络、资源、side effects、cleanup
```

核心原则：两个 skill 可以协作，但不要都去读 raw conversation。`agent-interaction-insights` 负责语义和用户交互；`agentsight-system-friction` 负责机器上真实发生了什么，并输出 join keys 供后续关联。

如果 AgentSight export 或 SQLite 里带有 LLM prompt/response payload，`agentsight-system-friction` 也不读取这些 payload；它只使用 system rows、metadata、ids、timestamps、statuses、token counts 和 join keys。

## 为什么不是一个 Skill

一个大 skill 的体验很顺，但边界会糊：

- 它既读对话又读系统 DB，容易过度收集隐私数据。
- 它会同时承担语义判断和系统取证，scope 太大。
- AgentSight 的独特价值会被压成“另一个数据源”，而不是系统边界事实层。
- 两类 evidence 的隐私规则不同：raw prompt/response 和 raw path/host/header 的风险不同。

所以，一个 skill 产品心智简单，但工程和隐私边界不够清楚。

## 为什么不是三个 Pipeline Skills

三层架构仍然成立：

```text
facts -> diagnosis -> expression
```

但这不应该成为三个用户入口。用户不会说“先 inventory，再 friction，再 artifact”。用户会说：

```text
看看最近 agent 哪里不对，生成个报告。
```

因此不要按 pipeline 阶段拆 skill。`inventory` 和 `artifact` 应该是每个 skill 内部的工作方式和输出形态，而不是用户必须理解的独立入口。

## 两个 Skill 的边界

### `agent-interaction-insights`

输入：

- Claude Code / Codex / Gemini CLI 本地日志
- OpenTelemetry GenAI spans
- LangSmith / Langfuse traces
- Datadog MCP query results
- plain transcripts
- 已经摘要过的 AgentSight system findings（可选）

不直接读取：

- AgentSight record DB
- AgentSight monitor DB
- raw system snapshots

输出：

- session / model / tool / token / cost usage
- interaction loops and retries
- user corrections and interruptions
- final summary vs visible validation
- AGENTS.md / CLAUDE.md / tooling improvement suggestions
- Markdown / PR comment / team brief / HTML artifact

### `agentsight-system-friction`

输入：

- AgentSight report exports
- saved SQLite sessions
- monitor DBs under `~/.agentsight/monitor`
- process tree, command, file, network, resource rows
- session/process/timestamp join keys
- 已经摘要过的 interaction findings（可选）

不直接读取：

- raw Claude/Codex/Gemini transcripts
- raw prompt/response history

输出：

- long-running processes
- failed/repeated commands
- file scope risks
- network scope risks
- CPU/RSS/IO/time waste
- capture gaps and correlation gaps
- cleanup actions
- system-level Markdown / incident brief / HTML artifact

## 与 Claude `/insights` 的关系

Claude Code `/insights` 更像 Claude Code 自己的 session 复盘入口。它分析 Claude Code sessions，生成 project areas、interaction patterns、friction points 一类报告。

这两个 skills 借鉴 `/insights` 的“判断报告”体验，但做出差异：

- `agent-interaction-insights` 是跨 agent、跨 trace backend 的交互分析，不绑定 Claude Code。
- `agentsight-system-friction` 是 AgentSight 的系统证据分析，不读 raw conversation。
- 两者都强调 observed fact、inference、missing evidence。
- Dashboard-like output 是按问题生成的结果，不是预先定义的产品页面。

## 目录结构

```text
skills/
  README.md
  agent-interaction-insights/
    SKILL.md
    agents/openai.yaml
    references/
      data-source-routing.md
      common-evidence-model.md
      friction-taxonomy.md
      report-shapes.md
      privacy-modes.md
      example-patterns.md
  agentsight-system-friction/
    SKILL.md
    agents/openai.yaml
    references/
      agentsight-sources.md
      system-evidence-model.md
      system-friction-taxonomy.md
      report-shapes.md
      privacy-modes.md
      example-patterns.md
```

第一版不放 scripts。只有当 adapter 逻辑重复出现、需要 deterministic behavior，才考虑加入：

```text
scripts/export-claude-usage-data.py
scripts/export-agentsight-snapshot.py
scripts/otel-genai-to-evidence.py
```

HTML renderer 暂时不做成脚本，因为 artifact 形态变化快，交给 agent 按问题生成更合适。

## 典型组合方式

交互问题：

```text
Use agent-interaction-insights on my last 20 Claude/Codex sessions. Which interaction patterns wasted time?
```

系统问题：

```text
Use agentsight-system-friction on this monitor DB. Which sessions left processes running or touched unexpected paths?
```

组合问题：

```text
Use agentsight-system-friction to summarize system findings, then use agent-interaction-insights to compare them with the agent's final summary.
```

这里第二步消费的是 system findings summary，不是让两个 skills 都打开 raw conversation 和 raw system DB。

跨 skill 的最小 handoff 是 `SystemFinding`：`source_skill`、`finding_id`、`severity`、`claim`、`evidence_summary`、`join_keys`、`privacy_mode`、`raw_data_included: false`。这样 interaction skill 可以用 system finding 做语义关联，而不需要重新打开 AgentSight DB。

## 验证标准

- 普通 transcript / Langfuse / LangSmith 请求触发 `agent-interaction-insights`。
- AgentSight DB / monitor / process-file-network-resource 请求触发 `agentsight-system-friction`。
- 两个 skills 都能输出 Markdown 或 HTML artifact，但 artifact 只是一种输出形态。
- AgentSight skill 不读取 raw transcripts。
- Interaction skill 不读取 raw AgentSight DB。
- 重要 finding 有 evidence、inference 和 next action。
- 缺失证据不被写成行为不存在。
- 隐私模式明确。
