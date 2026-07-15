# AgentSight Market Research Index

调研时间：2026-06-02。

这组文档是 AgentSight 产品化前的市场调研，不是单纯产品假设。它的核心问题是：

> 现在大家都在做什么？什么已经是红海？什么可能还没人做好？AgentSight
> 真正值得写成产品代码的部分是什么？

## Documents

1. [00-market-map-and-whitespace.md](00-market-map-and-whitespace.md)

   总览：市场地图、红海、可能无人区、AgentSight 的窄定位。

2. [01-competitive-landscape.md](01-competitive-landscape.md)

   竞品全景：LangSmith、Langfuse、Helicone、Phoenix、Braintrust、W&B
   Weave、AgentOps、Traceloop/OpenLLMetry、Datadog/New Relic/Honeycomb、
   OpenTelemetry GenAI，以及 Claude/Codex/Cursor/CodeBurn 等 coding-agent
   transcript/cost 工具。

3. [02-user-scenarios-and-icp.md](02-user-scenarios-and-icp.md)

   用户场景与 ICP：个人开发者、PR reviewer、skill/MCP/plugin 作者、
   企业安全/平台团队、agent 产品团队、成本/资源管理者。

4. [03-agent-security-and-governance.md](03-agent-security-and-governance.md)

   Agent 安全与治理：prompt injection、tool misuse、data exfiltration、
   MCP 风险、DLP/EDR/SIEM 覆盖边界、eBPF/OS boundary tracing 的差异。

5. [04-mcp-skill-plugin-verification.md](04-mcp-skill-plugin-verification.md)

   MCP/skill/plugin 验收：registry、marketplace、权限声明、动态行为证明、
   badge/report 最小实验。

6. [05-open-source-devtools-and-go-to-market.md](05-open-source-devtools-and-go-to-market.md)

   开源开发者工具与 GTM：eBPF/root/Linux 安装阻力、可接受用户、CLI/CI/Docker/enterprise runner 入口、30/60/90 天验证路线。

7. [06-user-pain-academic-and-ai-usage.md](06-user-pain-academic-and-ai-usage.md)

   用户痛点、研究工具和 AI-facing 产品形态：社区投诉、permission/autonomy、recovery、cost/loop、debugging、CLI/MCP/HTML 入口。

8. [07-academic-data-collection-pain.md](07-academic-data-collection-pain.md)

   学术界数据采集痛点：研究者正在收集 agent PR、真实会话、失败 trace、permission gate、tool/command bug、依赖可复现性和 MCP/skill 攻击数据，但缺少跨 agent 的系统行为采集层。

## Blog Drafts

- [blog-agent-observability-wrong-object.md](blog-agent-observability-wrong-object.md)

  对外博客草稿：挑战“agent observability = prompt/tool trace”的默认理解，主张先观察真实状态变化，再解释 agent 叙事。

- [blog-agent-observability-just-skills.md](blog-agent-observability-just-skills.md)

  对外博客草稿：主张 AI agent observability 不需要再多一个固定 dashboard，而需要按证据边界拆分的 skills 来生成语义化判断和 artifact。

## What Everyone Is Doing

市场已经拥挤的方向：

- **LLM application tracing**：prompt、response、tool call、RAG、latency、
  token/cost、evals、prompt management。
- **LLM gateway/proxy**：统一 provider gateway、routing、fallback、caching、
  request/cost observability。
- **OpenTelemetry GenAI standardization**：GenAI spans、tool spans、MCP spans、
  provider metadata。
- **Coding-agent transcript/cost tools**：读取 Claude/Codex/Cursor/Gemini 等本地日志，
  做 token/cost/session/report。
- **Hook-based coding-agent audit**：通过 agent hooks 统一记录 prompt、tool call、
  file edit、command、policy。
- **Agent security/firewall**：prompt injection、DLP、MCP gateway、tool policy、
  sandbox、SIEM/EDR integration。

这些方向不是 AgentSight 的主战场。

## What Looks Under-Covered

更可能成立的空白：

1. **OS-level behavior receipt**

   一次 agent run 结束后，生成独立行为收据：进程树、命令、文件读写/删除、
   网络目标、token/cost、risk flags。

2. **Intent-to-effect correlation**

   把 LLM/tool decision 和真实 OS side effects 关联起来：哪个模型输出、
   哪个 tool call、哪个 shell、哪个子进程导致了哪个文件/网络行为。

3. **MCP/skill/plugin dynamic verification**

   对第三方 tool 的声明做动态验收：read-only、workspace-local、no network、
   no secret access、no destructive ops。

4. **Incident forensics**

   Agent 把东西弄坏后，独立复盘：哪个动作造成损坏、碰了哪些文件、
   是否访问敏感路径、是否外连。

5. **Behavior regression testing**

   比较新旧模型/prompt/skill/MCP 版本的系统足迹，而不只是比较输出质量。

6. **OTel bridge for OS side effects**

   不替代 Langfuse/Datadog/Honeycomb/Phoenix，而是把 AgentSight 的 OS 证据输出给这些后端。

7. **Research-grade behavior data collection**

   学术界和工业研究都在收集 agent PR、execution trace、permission benchmark、tool bug、dependency reproducibility、MCP/skill attack data。空白不是“再做一个研究 UI”，而是让真实 agent run 自动生成可导出、可标注、可复跑的 evidence bundle。

## Key Product Judgment

AgentSight 不应该定位为：

> 又一个 agent observability dashboard。

但也不应该只定位为：

> Agent 审计工具。

“审计”只是其中一个用户场景。更准确的判断是：AgentSight 的底层能力是
**independent evidence**，但用户购买/安装它不是为了“审计”这个抽象词，而是为了完成
更具体的工作。

更窄、更可验证的定位是：

> A local-first behavior receipt and forensic evidence layer for agents that
> operate on real codebases and machines.

中文说法：

> AgentSight 是用户把真实系统任务委托给 agent 时的信任与恢复层。

这句话比“独立行为证据层”更接近用户场景：证据是手段，用户真正要的是放心委托、减少
盲目信任、出了问题能恢复、团队能接受结果。

## Jobs To Be Done

这些才是更接近用户的场景：

| Job | 用户问题 | AgentSight 价值 |
| --- | --- | --- |
| 放心委托 | 我能不能让 agent 多做一点，而不是每一步都盯着？ | 给出边界、风险和事后收据，让用户逐步提高自动化程度。 |
| 减少确认疲劳 | 这个 action 到底该不该让我确认？ | 用真实路径、命令、网络目标和风险分级，让确认更少但更有意义。 |
| 恢复现场 | Agent 把东西弄坏了，我怎么知道要恢复什么？ | 从文件、命令、进程、网络证据生成 recovery context。 |
| 团队接受结果 | 这个 agent-generated PR 能不能进 review / merge？ | 给 reviewer 一份过程证据，而不只是最终 diff。 |
| 验收第三方工具 | 这个 MCP/skill/plugin 能不能安装、上架、进入 allowlist？ | 动态证明 read-only、workspace-local、no secret access 等声明。 |
| 比较 agent/模型/工具 | 新模型或新 skill 有没有扩大行为边界？ | 对比系统 footprint，而不只是对比输出质量。 |
| 成本和效率复盘 | 为什么这次 agent 又慢又贵？ | 关联 token、循环、重复命令、文件扫描和资源消耗。 |
| 合规/安全审计 | 出事后谁做了什么、证据是什么？ | 输出可保全、可导出、可接入安全流程的证据。 |

所以，AgentSight 不只是 audit。更大的用户问题是：

> Agent delegation is useful, but users need confidence, control, and recovery
> when delegation touches real systems.

## Strongest Initial Wedges

优先验证顺序：

1. **Run receipt**

   最小可用产品。用户运行 agent 后得到一份可信报告。它不只是审计，也是下一次
   放心委托的依据。

2. **MCP/skill/plugin verification**

   比普通 run receipt 更有明确决策点：这个工具能不能安装、上架、进入企业 allowlist。

3. **PR due diligence**

   Agent-generated PR 附一份运行证据：跑了什么、读了什么、有没有危险行为。

4. **Incident forensics**

   当 agent 出事后，用证据帮用户复盘和恢复。

5. **Behavior diffing**

   适合后续进入 CI / agent 产品团队。

6. **Permission/autonomy tuning**

   适合后续做，但很有产品潜力：根据历史证据调节哪些动作自动允许、哪些动作要确认、
   哪些动作要阻断。这个场景不是“看报告”，而是让 agent 更可放手。

## Risks

最大的风险不是技术做不出来，而是产品复杂度跑偏：

- 做成通用 LLM observability，会被 LangSmith/Langfuse/Phoenix/Datadog 淹没。
- 做成 prompt firewall，会进入 Lakera/Prompt Security/Lasso/Guardrails 的战场。
- 做成 EDR/SIEM，会被企业安全平台吞掉。
- 做成完整 dashboard，会先消耗工程时间，但用户未必需要。
- 过度依赖 root/eBPF/Linux，会限制个人开发者采用，需要 CI/runner 入口补位。

## Next Validation Steps

30 天内最有价值的验证：

1. 做一个静态 run receipt，不先做大 UI。
2. 找 10-20 个高频 coding-agent 用户试用。
3. 找 3-5 个 MCP/skill/plugin 作者生成 verification report。
4. 做一个 GitHub Action demo，把 report 作为 PR artifact/comment。
5. 记录用户是否真的发现了 git diff / agent transcript / CI logs 看不到的信息。

成功标准不是“报告很酷”，而是：

> 用户能指出：没有 AgentSight，我无法证明这件事。
