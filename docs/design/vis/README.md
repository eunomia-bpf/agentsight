# AgentSight Visualization Design

AgentSight 的可视化不应该只是 LLM trace，也不应该只是系统事件浏览器。

如果一张图只展示 prompt、tool call、token、latency，它会变成 LangSmith/Langfuse 式的 agent trace。如果一张图只展示 process、file、network、syscall，它会变成 strace/eBPF dashboard。AgentSight 真正特别的地方在中间：

> 把 agent 的语义意图，和它在机器上造成的真实动作连成一条可读的因果链。

这套文档把可视化拆成一个总纲和几张具体图。每张图都必须同时包含三层：

```text
Semantic layer: 用户目标、LLM turn、plan step、tool intent
Execution layer: tool call、process tree、command、cwd、argv
Effect layer: file / network / resource / test / generated output / failure
```

一张合格的 AgentSight 图不是问：

```text
这个 agent 说了什么？
这个进程做了什么？
这个文件变了什么？
```

而是问：

```text
哪个语义意图触发了哪个系统动作，最后造成了什么结果？
```

## 总原则

第一，图的主语是一次 run，不是一个 telemetry category。

用户不是来分别看 “LLM events”、“process events”、“file events”。用户想知道这次 agent 工作是怎么展开的：它为什么行动、怎么行动、碰了哪里、失败在哪里、结果是否可信。

第二，每个系统动作都尽量向上归因。

一个 `npm test` 不只是一个 process。它应该能连回上游：

```text
user asks "fix failing API test"
  -> LLM turn proposes running tests
    -> tool call Bash("npm test")
      -> npm -> node -> jest
        -> read tests/api.test.ts
        -> fail assertion
```

第三，每个语义动作都尽量向下落地。

一个 tool intent 不能只停留在 “Bash: npm test”。它应该展开到进程、文件、网络、资源和结果：

```text
Bash("npm test")
  -> process: npm, node
  -> files: package.json, package-lock.json, tests/*
  -> network: registry.npmjs.org
  -> outcome: exit 1, then retry exit 0
```

第四，无法归因的动作要单独显示。

这是 AgentSight 的差异点之一。agent transcript 没说，SDK trace 没记，但 OS 里确实发生了的动作，应该出现在图里，而不是被吞掉。

第五，少用安全、合规、事后追责类词作为产品主语。

AgentSight 可以支持调查、复盘、团队 review、policy tuning，但第一表达应该是帮助用户理解和推进 agent 工作，而不是把产品收窄成事后追责工具。更好的用户问题是：

- 我能不能放心让它继续做？
- 它到底把任务推进到了哪一步？
- 它在哪里绕路、重试、浪费成本？
- 它改动的范围是不是合理？
- 它声称成功时，真实系统有没有发生对应结果？

## 推荐命名

不建议继续使用：

- Behavior Proof Layer
- Compliance Panel
- Incident Console
- Security Review Dashboard

这些词技术上可能准确，但用户感受偏安全、合规、事后追责，容易把 AgentSight 的使用场景收窄。

更建议使用：

- **Agent Run Map**：总图，回答一次 run 如何从目标走到结果。
- **Intent-to-Effect Flame Graph**：火焰图，回答哪些意图造成了最大的系统 effect。
- **Causal Timeline**：时间图，回答每一步发生顺序和跨层因果。
- **Run Impact Map**：结果图，回答这次 run 的影响范围。
- **Agent Workspace Map**：工作区图，回答 agent 如何探索和修改 repo/workspace。
- **Multi-Agent Causal Map**：多 agent 图，回答多个 agent 如何互相影响、冲突或协作。

## 文档索引

- [Agent Run Map](agent-run-map.md)：总入口图，适合 run 结束后的第一屏。
- [Intent-to-Effect Flame Graph](intent-to-effect-flame-graph.md)：语义 flamegraph 的形式模型（operation / operation stack / view-as-query），已由 `agentpprof` 实现。
- [Causal Timeline](causal-timeline.md)：按时间展开语义、工具、进程、文件、网络和结果。
- [Run Impact Map](run-impact-map.md)：把一次 run 的改动、网络、资源、测试和异常活动聚成 impact summary。
- [Agent Workspace Map](agent-workspace-map.md)：专门看 repo/workspace 内的探索、读写和 patch 生成过程。
- [Multi-Agent Causal Map](multi-agent-causal-map.md)：看多个 agent、sub-agent、MCP server、tool worker 的交互和冲突。

## 不是文件系统中心，而是 run 中心

文件系统很重要，尤其对 coding agent。但它不应该成为唯一中心。

一个 agent run 的真实影响还包括：

- 进程和子进程
- shell command 和 exit status
- 网络目的地
- token 和模型调用
- resource usage
- test result
- package install
- generated output
- background activity
- multi-agent handoff
- policy decision
- user approval / rejection

所以总图应该以 run 为中心。文件系统图只是其中一个投影。

```text
Run
├─ semantic intent
├─ tool decisions
├─ process execution
├─ workspace changes
├─ network movement
├─ resource cost
├─ test/outcome
└─ unattributed activity
```

这也是 AgentSight 和普通 trace UI 的区别：它不是把事件堆出来，而是把 agent 的工作过程还原成跨语义层和系统层的因果路径。
