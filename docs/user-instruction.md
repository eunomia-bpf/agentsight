# User Instructions

The entries below preserve only verbatim user-authored research instructions.

## 2026-07-19

> 你的研究分支你觉得 story 是什么? 仔细思考完整说一下, 先开始调研

> 不是只关注于 coding 吧?

> 我最近许多个软件开发和 auto research 的实验, 都是开头设置好简单的目标和 idea, 让一个 Agent 在一个 repo 里面自我迭代 2-3 天时间, 我再回来看一眼. 我想要在 30s 内理解 Agent 大致做了什么, 迭代改进了什么文件, 是怎么迭代改进的过程? 比如说是根据什么样的做法去迭代代码, 是先测试还是先写代码? 主要改了什么模块? 在论文还是代码上面花的时间多? 热点是什么?  我还在想具体怎么做, 大概的思路是按 Agent 的真实读写时间回放仓库演化：文件是星点，目录用稳定色系聚类，访问触发短暂亮起与放大，新建、重命名、删除改变星域结构，Git commit 作为外框闪烁的里程碑。它的价值是把长期运行 Agent 原本不可读的事件日志压缩成可观察的软件生长过程，让人直观看到 Agent 的注意力如何移动、代码如何形成，以及异常反复、遗忘区域和结构漂移发生在哪里。是不是vibecoding用的多，我们现在写的代码，很多ai写完之后也不太管，不知道写些什么，除了结果的测试和功能验证外，是不是在写的过程中也要记录（后面可以回放）他编写的轨迹，写这个代码的意图，尝试过什么，失败的原因是什么，当初踩过什么坑，后来怎么避免的，或者过程中反思是什么记录下来。然后我也可以看到, 是不是我skill 设计不合理导致了一些步骤过于复杂不合理? 比如说要求 agent 记录了一堆文档, 但实际上几乎不会回头看; 或者 skill / harness 设计不合理导致 agent 花了大量时间迭代无意义的垃圾测试用例而不去写代码.

> 时间轴不需要和 commit 对齐, 时间轴应该完全和 agent session 的操作对齐. commit 除了边框闪烁不应该作为别的作用.

> AAAI ? 是不是 demo 什么的
>
> 你觉得贡献定位成什么最有用?

> 记录下来. 我们只考虑自动诊断或者让 agent 来用这个工具帮助诊断

> 我们建立了一种面向长期 Agent 的过程级可观测与监督方法，使人能够跨 session 重建 Agent 如何改变持久 workspace，并识别偏航、空转、验证缺失和无效 harness 行为。
>
> 核心研究问题可以是：
> 相比最终产物、session summary 和线性日志，workspace-centered action trajectory 能否让人或自动诊断器更可靠地判断长期 Agent 是否在取得进展、陷入空转、偏离目标，以及何时需要干预？
>
> 这就是 **process-level scalable oversight for long-horizon agents**。它比“可视化软件演化”更重要，也不限于 coding。
>
> 记录下来. 我们只考虑自动诊断或者让 agent 来用这个工具帮助诊断

> 按照 research 流程不断迭代, target AAAI

## 2026-07-21

> 不要考虑人工标注, 想别的方案实验

> 独立 gold：需要两位专家独立标注，再由第三位专家盲审裁决。材料和具体要求见 [questions-for-author.md](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/questions-for-author.md)。这不要. 你可以想办法用别的轨迹或者 benchmark 来饰演

> 我们一定要改善吗

> 能不能减少一些 claim, 之分析轨迹

> 这样实验简单一点

> 我们的 claim 是什么? 能解决什么用户问题? 分析出来什么?

> 重建 claim：能够从原始 Agent 记录和 workspace 状态忠实重建跨 session 轨迹 这个是 by design 的吧

> RQ 分别是什么

> 我们 empirical study 开源项目的演化过程是一个贡献吗? 能分析出来什么?

> 我们就是案例实证研究和 contribution 分开?

> commit-level 历史遗漏的过程信息不是最关心的对吧? 核心的什么样的东西会让人最关心?

> user prompt 记录下来了吗

> 这些也记录? 还有没有有趣的问题? 多记录一下? 记录一个 empirical study 的文档? 然后去做, 分析五六个本地项目?  按照 research 流程不断迭代, target AAAI,  empirical study 至少 5 个 RQ, 然后工具本身再来一个 RQ, 证明测量 claim：该表示能够产生最终 diff 和简单事件计数无法表达的过程指标, 也能比起单独的 LLM as judge 或者别的方案更好的理解长期的 Agent 轨迹导致的项目演化过程? 前面 case study 的是不是可以用一些模型里面的指标来表达 (不过不一定要和模型完全绑定)?

## 2026-07-22

> 写一个 asbtract / title 给我先

> 该画图的要画出来图

> skill/harness 的访问能也从轨迹里面看出来吧

> 现有冻结数据 是什么? 我们可以从轨迹上获得啊? 谁让你冻结数据了?

> 我们不需要改可视化, 你现在先把 empirical study 做好? RQ6 修一下? 能不能想想更有趣的问题, 再来几个 RQ? 我觉得有一些是显然的吗比如说 RQ1, 也有一些数据不一定具有代表性, 因为是我们自己的开发数据? 另外 empirical study 也需要画图对吧?

> 以及你也可以帮助想想我们的星云图有没有必要重新设计

## 2026-07-23

> 能不能先把研究变得更好? 你可以随意改算法, 把论文先弄好? 去做
