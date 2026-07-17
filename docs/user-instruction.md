看看有没有一个 worktree 是 research 的? 里面的论文符合 AI 顶会的水平了吗? review 分析一下? agent pprof 的那个

---

计划一下这些怎么修改? 我们你觉得按照我们的 skills 继续迭代能不能解决这个问题? 能不能用 agentsight 自己仓库里面的 skills 分析一下实验轨迹, 看看能不能发现什么 agent 在不断犯错的地方, 能改进 skills? 详细分析看看

---

我必须明确说一下, 任何情况都禁止这个 research pipeline 等待人工介入, 你觉得需要人工判断的东西你需要记录一下, 这个不确定, 然后选一个你觉得最合适的继续做.

---

禁止缩窄或移出论文贡献. 强 claim 无法授权应该你要想办法坚持该 claim, 找到更多证据而不是更小. 要让 insight 越吸引人越大越好

---

禁止保守, research 要大胆假设, 小心求证. 最保守是绝对不对的

---

还有一个重要的事情, 尽可能用别人的真实世界的论文或者 benchmark, 真实世界的 software, 真实的系统, 真实的数据集, 测试工具, 不要自己写脚本测试, 最好实验设计都能直接 cite 对吧? 最好不要自己设计小实验. 有实验一定要完整跑完而不是跑两三个 smoke 就停下来了?

---

简单、完整、激进, 不应该套用乱七八糟的词汇, 吸引人, 好的 research 应该是有原则性的东西, 简单但不直观的, challenge 当前belive 的想法但能长远解决许多问题对吧? 你先想想好的 reserach 是什么? 糟糕的 research 是什么?

---

paper 是不是一开始就开始写比较好? 怎么让写作 skills 也加入进来?

---

段落流；
terminology；也得从 day 1 开始做吧? 你再想想整一套流水线?

---

应该是论文负责维护当前最终状态, 除了论文之外的文档负责维护演进历史, 这样合理吗? 论文从 Day 1 开始维护? 你再设计一下 loop?

---

能不能让 loop 尽量简单, 不要太复杂?

---

experiment 每一次应该只做一个实验, 只验证一个 claim, 最多修改这个 claim 两次, 第 3 次就应该返回记录写进 apper 里面或者让 reviewer / writing 帮忙想办法更换 claim

---

不对, exp plan 输入应该是要是明确的 RQ

---

exp 不能更改 RQ, 只能更改结论的 claim

---

所有 write skills 都不能 commit push 或者做任何 git 操作

---

可以在每一步有实质进展时 commit/push；
不创建、不切换 branch；
遵守目标仓库自己的发布规则；
commit/push 成败绝不参与 EXPERIMENT、WRITE、REVIEW 的通过判断，也不阻塞研究循环；
不做逐节点 Git 状态审计、hash 绑定或冻结协议。只有顶层状态机和实验, 或者 literarure survay 可以 git, 写作/review不能改任何 

---

我们的论文 writing / idea 是不是要明确要求指出 RQ？我们的 writing struct 是不是也要求 eval 按照 rq 组织，并且明确写出 RQ？RQ 应该不需要太多吧，几个比较好？

---

可以是 2-5 个吧？不应该少于 2 个。我觉得这些要求应该明确加入 skills

---

auto reseach skill 是不是也要注意不要偏离/窄化用户的意思？加一两句 review 的时候的注意？

---

这个的 idea 是不是也被整的越来越小越来越不 interesting 了?为啥会发生这种事情? 分析这个 repo 里面的完整执行轨迹? 看看具体是什么带来的问题; 也要看看文档和不必要的约束

---

检查一下 skills, 分析现在的 skills 会不会导致这个缩小 idea 问题, 然后把 idea 修改到原先的情况, 所有相关的文档都需要更新或者恢复之前的版本。,论文也需要改, 糟糕的文档也要改, 确保不会出现这样的问题, 旧的不必要的修改和文档要归档, 然后按照当前的判断出来的合理思路和方向和 skills 继续迭代

---

别改当前 skills

---

我们的 agentpprof 论文能发顶会了吗? 还有啥要迭代? 你想想? 怎么改? 先分析设计一下, 别动 submodule 里面的内容, 把旧的中文论文备份到 docs/tmp 里面去, 然后把 submodule 里面的 agentpprof 的内容复制到 docs/paper 里面开始继续迭代写作? 是不是可以 target AAAI? 搜索 CFP, 更换模板, 注意格式. 然后继续按照 research skills 迭代改进, 包括做实验, 包括把仓库里面的实验放进去。你重新从 submodule 恢复那个 story 和叙事，确保所有文档一致，不会走偏，然后思考一下如何继续完善实验或者要不要微调。

---

idea story 是不是要记录每次任何idea/叙事层面的发生变化的原因？这个有记录吗？

---

改一下。另外一开始的叙事也要完整保留在 idea story 里面，每次修改叙事都得读完整的 idea story，仔细思考原始的好还是现在的好。

---

当前 thesis 是不是要和 submodule 里面完全一样，而不是什么Agent observability 需要跨运行 profiling recurring behavior 和 measured effects，不只是单次 tracing/debugging。

---

什么情况会导致你改写或者替代 thesis？auto reseach 和我们的 agents。md 是不是需要检查防止这种漂移

---

dea 已恢复为更大的原始方向：execution location、cross-run similarity、decision-oriented aggregation 是三种不同结构；execution tree 和 semantic tree 都不能自动获得权威。方向是啥? 和 submodule 里面有啥差异

---

现在进度如何了

---

现在进度如何了? 和 submodule 里面现在有啥差异? 接下来应该做什么

---

RQs4 个：attribution、localization、tag accuracy、cost 四个 RQ 也不应该改, 论文也不应该放负面结果, 故事越吸引人越好. 这些偏好记录在 user instruction 里面.

---

论文也不应该放负面结果, 故事越吸引人越好, 我们应该根据 hyposis 改实验尝试能不能证明, 而不是根据实验目前的设计问题修改 hyposis / claim, 除非这个 hyposis 本身完全不可能成立, 不然不应该改变 我们的 hyposis

---

故事要变得更强更吸引人

---

对比 submodule, submodule 的故事我觉得更好

---

直接恢复到 submodule 的情况. 禁止随便改变 syory

---

从 submodule 的开始, 所有的 sbtarct / intro / 系统设计, background / motivation 都应该恢复

---

我们的 skills 状态机应该怎么改?

---

你现在应该是 evaluation 阶段对不对? 按照我们新的状态机

---

我们的论文回到原始的 submodule 的版本了吧? 那个是权威版本

---

submodule 的原始 AgentProf 版本 是啥?

---

这个版本吧

---

实验有改进了啥? 你跑了这么久实验有啥新的进展吗? 回答了什么 RQ 吗

---

继续做实验

---

实验能复用就复用, 别把实验搞得太复杂

---

是不是做一下, 并且要测试? 做了吗

---

你的这个算法想法记录一下

---

我们的 agentpprof 论文能发顶会了吗? 还有啥要迭代? 你想想? 别动 submodul,  可以在 docs/paper 里面开始继续迭代实验? 是不是可以 target AAAI? 注意格式. 然后继续按照 research skills 迭代改进, 包括做实验.

---

实验做了吗? 进度如何?

---

算法能改进一下吗

---

能不能直接在现有的已经泡过的轨迹上面改进一下算法, 而不是做一个新的?

---

自己写的 harness 出错也消耗次数这句话是不是可以删除Experiment plan review 当前最多两轮，而我之前明确说过应允许 3 轮? [research-experiment-design (line 262)](/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/research-experiment-design/SKILL.md:262) 默认要求矛盾结果返回一个 redesigned experiment；[iter-review-critique (line 90)](/home/yunwei37/workspace/my-paper-work/academic-writing-skills/skills/iter-review-critique/SKILL.md:90) 又强制每次给出“下一个决定性实验”。 这里面把强制性要求删掉, 净减少信息? 额外 implementation review、多个 evaluator、重复 checker、过多等价性证明，并不是当前 experiment skill 强制要求。Skill 实际只要求一个 plan、合并的 plan review、raw results 和一个 result review。这里应该改执行习惯，而不是继续扩充 skill。 这里面你应该在你的 agent.md 里面加上防止过多的. skill 文本应该最小修改并且少量净减少

---

你现在的符合 AAAI 要求吗

---

我不太理解这两个算法, 你得详细讲讲? 你尝试过的算法代码和不足也都得写成文档放在 Doc 里面记录下来

---

我们真正想要知道什么样的信息? 怎么判断不同的算法好还是差?固定深度版本：boundary F1 0.4231，B³ F1 0.6165
去掉深度上限后：0.4720 / 0.6720
当前跨运行 recurrence：0.6799 / 0.7862
加独立 grouped-reference scalar calibration：约 0.7340 / 0.8011这些啥意思?

---

OS world 标注了什么? Label-free recurrence 是啥?Grouped-reference calibration 是有额外标注时的可选模式。
Information gain 的问题不是不够复杂，而是“字段纯度”并不等于“operation 连续性”。 你再详细解释

---

我们的合理的指标应该是什么?

---

你这个 metrics 是标准 metrics 吗? 是不是应该要标准的 metroics
