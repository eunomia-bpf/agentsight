# AI Agent Observability Doesn't Need Yet Another Dashboard. It Needs Skills.

早上九点，reviewer 打开昨晚 agent 跑完的任务。

Agent 的总结很漂亮：

> Fixed the issue, updated tests, and verified the result.

Dashboard 也很完整。它显示 token cost、model latency、tool waterfall、failed spans、shell exit status、prompt 和 response。所有信息都在。

但 reviewer 真正想知道的是一句话：

> 我能不能相信这个 PR？

他开始点 dashboard。先看 longest span，再看 failed command，再看 token spike，再看 file diff。十五分钟后，他知道了很多局部事实，但还没有得到真正的判断：

> 它先跑了完整测试，失败了。后来只跑了一个局部测试，通过了。最后总结成“verified”。这个 PR 不能按完整验证处理。

这个判断不是一个 widget。

它需要读懂目标、命令顺序、失败语义、测试范围、文件变化和最终总结之间的关系。

这就是 AI agent observability 和传统 observability 的分界。

## Dashboard 回答已知问题

Dashboard 很有用。它擅长回答已知问题：

- 今天 token cost 有没有上升？
- 哪个 model latency 最高？
- 哪个 tool error rate 异常？
- 最近一小时 active sessions 有多少？
- 哪个 endpoint 返回最多 5xx？

这些问题有稳定指标、稳定分组、稳定图表。你可以提前设计页面。

但 agent 行为里最难的问题往往不是这种形态：

- 它是不是偏离了任务？
- 它是不是重复同一类失败？
- 它说测试通过，这句话可信吗？
- 它有没有把失败压缩成成功总结？
- 它有没有访问 repo 外路径？
- 它为什么花了这么多钱却没有推进？

这些问题当然需要数据。但它们不是单个指标。

它们需要解释。

## Agent 行为的核心信息是语义性的

传统 observability 把系统压成数字。AI agent observability 还必须理解叙事。

一个 agent run 里最重要的信息经常藏在关系里：

- 用户目标和 agent 实际行为是否一致；
- tool failure 是否反复出现；
- final summary 是否遮蔽了失败；
- validation 是否从 full test 缩小成 partial test；
- file/process/network side effects 是否超出用户预期；
- expensive reasoning 是否产生了真实进展。

这类问题不是“多画一张图”就能解决的。

它需要另一个有语义理解能力的 agent 来读 evidence。

## Skills 是分析方法，不是又一个 UI

这里的 skills 不是 dashboard 插件，也不是按钮。

Skills 是 portable analysis playbooks：给 agent 的一组方法，告诉它如何读取 evidence、如何判断 friction、如何标注 inference、如何保护隐私、如何按用户的问题生成合适的输出。

一个好的 `agent-interaction-insights` skill 不会只说“总结这个 trace”。

它会要求 agent：

- 先判断用户真正的问题：usage、friction、trust、risk，还是 report。
- 再选择 evidence source：Claude/Codex/Gemini logs、OTel、LangSmith、Langfuse、Datadog、plain transcript。
- 先整理 facts：sessions、messages、LLM calls、tool attempts、validation claims、user corrections。
- 再生成 findings：失败、loop、summary mismatch、context miss、resource waste。
- 每个 finding 都要有 evidence。
- 推断原因时标注 inference。
- 不要把 missing evidence 写成 behavior did not happen。
- 默认不泄露 raw prompts、secrets、auth headers。

最后，用户想要什么视图，agent 再生成什么视图：

- concise findings
- inventory table
- PR comment
- incident brief
- team memo
- self-contained HTML artifact

Dashboard 变成输出之一，而不是产品的起点。

## 为什么是两个 Skills

你可以把这个过程拆成三个阶段：

```text
inventory -> friction analysis -> artifact
```

架构上很干净。但产品上不一定对。

用户不会说“请先运行 inventory skill，再运行 friction skill，最后运行 artifact skill”。用户会说：

> 看看我的 agent 最近表现怎么样，哪里不对，生成个报告。

所以第一版不应该是三个 pipeline skills。

但一个什么都读的大 skill 也不对。它会同时读取对话和系统 DB，既增加隐私面，也模糊 AgentSight 的独特价值。

更好的拆法是按 evidence boundary，而不是按 pipeline stage：

```text
agent-interaction-insights
  读对话和 trace，理解用户交互、loop、summary trust、validation claims

agentsight-system-friction
  读 AgentSight/system evidence，理解进程、文件、网络、资源和 side effects
```

这两个 skills 可以组合，但不应该都读 raw conversation。AgentSight skill 输出 system findings 和 join keys；interaction skill 负责把这些 system findings 和用户目标、最终总结、对话过程放在一起理解。

## AgentSight 应该做什么

AgentSight 不应该急着做第 N 个 dashboard。

更有价值的是提供高质量 evidence：

- 真实进程树；
- shell command 和 exit status；
- 文件读写和删除；
- 网络目标；
- CPU/RSS/IO；
- LLM/tool/session 关联；
- 可导出的 snapshot。

然后让 `agentsight-system-friction` 把这些 evidence 变成系统 findings，再让 `agent-interaction-insights` 在需要时把系统 findings 和对话语义合并。

这会让 AgentSight 的定位更清楚：

> AgentSight provides system evidence. Skills turn evidence into insight.

当某些输出稳定之后，再把它们产品化成 CLI、hosted report 或 dashboard。不要反过来，先定义 dashboard，再让用户把问题塞进去。

## 给 Observability Tool Builders 的建议

如果你在做 AI agent observability，不要只问：

> 还缺哪张图？

也要问：

> 用户拿到 evidence 后，真正要做什么判断？

很多判断不能靠固定 dashboard 预先枚举。它们需要一个能理解语义、证据和上下文的 agent。

所以，下一代 agent observability 的关键组件可能不是又一个 dashboard。

而是一组好的 skills。
