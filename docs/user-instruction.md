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

---

token-weighted B³ 是场景化变体，不应出现在论文中；普通 B³ 才是标准主指标。Recall@20% 和固定 top-3 reader 是实验协议，不是通用 metric，也不应出现在论文中。论文的主指标必须采用已有论文或官方 benchmark 定义的标准指标，并引用定义它们的论文；这些自定义加权、预算 cutoff 和 model-reader 协议最多只能作为内部诊断，不能替代论文主指标。

---

看看 claude 的 claude --resume df98b0b9-b883-41ad-a193-92cd8fe62eca 这个会话的聊天记录, 接下来告诉我要做啥. 另外能不能去搜索搜索更多 related work? 看看别人怎么说的?

---

看看有没有更好的 eval 方式?

---

继续迭代, 然后要让不同模型, 比如说 grok 来完整审稿

---

是不是算法太复杂了? 我们是不是有一个更简单的做法, 比如说保存当前 stack, 让 llm 去看下一个 prompt, 决定这是一个新的子任务, 应该 append 进去, 还是不属于当前 stack 顶端的任务, 应该pop 一个, 还是不 append 也不 pop? 你觉得这样是不是更好? 然后 stack 也应该是更加语义相关的, 比如说 "write a paper" 是一个 operation, write abstract 是一个 operation

---

你可以用 llm / llama.cpp qwen 3b来做?

---

depth 应该是可变的吧

---

深度应该是可以参差很大吧?

---

目前最重要的科学观察是：Qwen 3B 虽然能合法维护可变 depth，但几乎每一步都创建新 leaf，new-frame rate = 1.0，所以很可能严重过度分段。这说明简单 stack 状态机本身没坏，具体 3B transition policy 可能不够好。现在还没有打开 stage 标注或算 B³；要等 20,866 个 operation 全部固定后才评分。是不是 prompt 不好? 如果后面你丢弃一些比如说叶子节点呢? 不要限制深度?

---

为什么设计 semantic operation 现在来看清晰吗

---

对。你说得对，当前图最大的偏差就是：它按“系统字段”堆栈，而不是按“具体任务”堆栈。
现在的：
agent → session → prompt → tool → command → path → status
更像运行日志的分组方式。它能看资源分布，但不能回答论文真正关心的问题：Agent 为了完成一个任务，如何拆解、推进、反复和失败。
更合理的主栈应该是：
具体任务 → 子任务 → 阶段/策略 → 语义动作 → 操作对象 → 结果
例如：
审查 semantic flamegraph 论文证据
└── 核验“能表达任务结构”的 claim
    └── 收集证据
        └── 检查实验结果
            └── results_summary.md
                └── 结论：证据不足
另一条可能是：
审查 semantic flamegraph 论文证据
└── 核验实现与论文是否一致
    └── 检查实现
        └── 定位 stack 构造逻辑
            └── semantic_tag_flamegraph.py
                └── 结论：当前按系统字段分层
这样火焰图才能分析：
一个任务主要消耗在哪个子任务；
Agent 是否在某个阶段反复尝试；
高 Token 路径是否产生了有效结论；
哪些子任务失败、被放弃或没有证据；
不同 Agent 采用的任务分解策略有什么区别。
而 agent/model/tool/status 不应该占据主要 stack 层级，更适合作为：
颜色：Agent、成功/失败、语义动作；
筛选器：模型、session、工具；
宽度指标：事件数、时间、Token；
侧边详情：原始命令、文件、调用证据。
所以之前从图里得到的“shell 很多、读取很多”只是运行行为结论，还不是论文级的任务结论。下一版应把“任务—子任务—结果”作为主结构，命令和文件仅作为底层证据。否则它更接近分类调用图，还不能真正称为 task-semantic flamegraph。

---

先着重考虑解决用户问题，不止是做 research。不要做额外的前端。

---

差分火焰图既要有一个真实 good/bad trace 的详细 case study，也要在真实 benchmark 上完成大范围评测，不能只停在一个例子或 smoke run。

---

AgentPProf 禁止增加或依赖自定义前端。每次运行唯一的产品 artifact 是一个标准 `.pb`/`.pb.gz` pprof profile；禁止把 folded stack、SVG、PNG、HTML、JSON、dashboard 或 Web UI 发展成另一条用户输出路径。任务层级、语义 operation、资源权重、证据标签和 good/bad 差异都编码进 pprof 的 sample、label 和 stack frame。火焰图、搜索、focus、下钻、比较和其他可视化全部复用现有 pprof-compatible 工具。这是 hard rule。实验所需的 Markdown 报告和 raw evaluation data 只是研究记录，不是 AgentPProf 产品输出。

---

recursive operaion segamentation 现在是怎么实现的? 应该在什么上面做? 我们之前设计的还没有完全对应吧? 接下来应该怎么设计对应这样的算法? 能不能实现框架, 然后几种不同的方案来实现? 重新跑 eval? 默认可以是 LLM Agent assist annotation? 做一下尝试

用户能从图里看出任务如何拆解、哪里反复、哪些路径耗费高但没有结论”——目前是部分达到，不是端到端解决, 你要想办法先解决用户问题, 让这个工具有用, 而不仅仅是实验数据看起来好? 做一下尝试, 你得找出几个例子和火焰图, 火焰图要有深度变化而且比较深, 就类似从原先的 tool / session / user request / llm call / tool call 这样开始折叠和切分, 举一些例子, 讲解给我真实解决了用户什么问题, 也要有 case study

---

系统应该设计成接受人工标记的 ID 来进行切分对吧? 你也要维护一个对应的标记池子? 去做实现?

---

case study 至少 2 个；每一个 case study 都必须以许多完整 session
组成的集合为主要分析单位。单条 trace 只能作为集合结论的证据下钻，不能把一个
session 或一个 good/bad pair 包装成完整 case study。

火焰图必须放进论文, 真实打开看, 确实像是解决了真实问题的火焰图, 堆栈深度有参差并且能有比较深的. 再来看看一个 case study 做做 long horizon agent, 有没有非常长的 agent 的

---

不是让你自己作为 Agent 手动去标注1

---

谁是 agent? 谁在做?

---

你可以让 subagent 标注

---

框架不需要支持多个 backend, 框架是不是只需要是命令行工具, 允许输入标注配置文件

---

生成的名称再对当前 active stack 做统一解析：
名称等于栈顶：stay，当前任务继续。
名称等于较早祖先：pop，返回上层任务。
名称不在栈中：push，进入新子任务。
例如： 这个是啥啥意思

---

我们是不是本身就在一个层次结构上做? 你看看主线上是什么层次结构, 我们只是在那个层次结构上面继续做折叠?

---

我们是不是本身就在一个层次结构上做? 你看看主线上是什么层次结构, 我们只是在那个层次结构上面继续做折叠? 让堆栈参差不齐

---

除了 Agent 标注, 我们是不是还可以 propose 一两个非 LLM 的算法, 或者刚刚 LLM 标注的算法 (非 Agent 标注?) 然后所有 RQ 都跑一遍

---

我刚刚的要求记录到一个特定的文档里面了吗? 我记得和你说过一个特定的文档专门记录 user reques?

---

Agent 标注就是自动算法。你也得计算它的质量

---

user instruction 里面要放我的原话对吧

---

我们的 skills 里面有没有强调要原话?

---

每个必须读完整 session、只输出完整路径 marks，不需要要求它们读完整 session

---

subagent 不就是 automatic backend

---

最好深度要有足够的, 比如说 3-4 ? 你想想?

---

不要强制深度

---

火焰图必须放进论文, 做好之后真实打开看, 确实像是解决了真实用户问题的火焰图, 堆栈深度有参差并且能有比较深的, 并且你能从里面分析出有价值的信息

---

project → agent → session → prompt -> LLM call -> tool call 从这个形态开始折叠对吧? 宽度实际上对应叶子节点的各种, 比如说token, time, 文件读取写入次数等等

---

session/prompt/call/tool 不应该给他们assign operation, 这就可以通过 operation 聚合了?

---

你先把图画出来给我看看

---

session S1
└── prompt P1
    └── LLM call C7
        ├── tool call T8: inspect file
        └── tool call T9: run test 火焰图的深度应该比这个深吧? toolcall / llmcall 这样的叶子节点是不是还是用 regex 或者别的方式做 tag 标记? 有必要吗

---

另外还要支持多个后端

---

你先把用户友好的路径找到

---

不应该source adapter 解析出的结构化事件? 你想想你的火焰图例子能看出来什么

---

举一个例子, 现在到底生成了什么.

---

我们论文有啥数据了? 还差啥数据

---

Agent 给这一步标记的 operation path 是：
Repair software regression
└── Reproduce issue
    └── Run reproducer 这个是怎么标记出来的?

---

我们的 stack 也不应该到     └── operation:repair_software_regression
        └── operation:reproduce_issue
            └── operation:run_reproducer 就停了吧? 单个的 LLM call 或者 toolcall 是不是底层的叶子单元? 无论如何都得有吧?

---

等等, 我觉得过于复杂了....是不是内部应该保留成类似 trace 一样的层次数据结构? 然后 operation 在 trace 上面某些位置划分和断开和命名?

---

你应该是每一层分别标记吧? 比如说 session 级别做 session 的标记, prompt 级别做 prompt 标记, llm call 级别做 llm call 级别标记? 每一层都可以额外折叠? 这样好还是直接开始折叠好?

---

你觉得从 trace 开始做还是全部拍平了做好? 你分析一下?

---

是不是应该让命令行工具维护 json? 比如说 agent 标记完, 调用命令行工具去更新 json 里面每个 node 的 path. 底层 trace 单独保存：
{"id":"S1","parent_id":null,"kind":"session"}
{"id":"P1","parent_id":"S1","kind":"prompt"}
{"id":"C1","parent_id":"P1","kind":"llm_call","metrics":{"tokens":1240}}
{"id":"T1","parent_id":"C1","kind":"tool_call","attributes":{"tool":"view"}}
{"id":"C2","parent_id":"P1","kind":"llm_call","metrics":{"tokens":830}}
{"id":"T2","parent_id":"C2","kind":"tool_call","attributes":{"tool":"grep"}} 这里面每一个都加一个 path, 但是由命令行生成, 这样 agent 可以直观的看到现在的形状是什么样的, 正不正确. 包括原始的 prompt, llm response,  session 名称, 工具调用也得留下吧? 这可以帮忙对照是否正确.

---

乱七八糟, 再来梳理一下: 我们有一个工作区, 工作区有 3 个文件怎样? 一个是当前在工作的 trace, 一个是 annotation, 一个是当前所有的聚合起来的 stack fold format. agent 或者无论什么backend 的目标就是输出 annotation, 然后 cli 会从 annotation 计算出当前在工作的 trace, 并且更新 trace 里面的 path field 和更新 stack fold format. 你作为 agent 可以不断迭代 annotation 找到最好的表达形式, 或者别的算法也可以, 这合适吗

---

原始 trace 不是单独文件, 不在工作区.

---

这是一个可以不断迭代并且不断增加切分的模型对吧

---

算法 backend 可以是什么

---

你把这个记录到一个文件, 然后 commit push 所有更改, 顺便把之前的旧的整理到 docs/tmp 之类的地方

---

先写文件

---

修改代码, 去实现, 去测试, 然后先给我看看你手动标注出来的效果, 是不是很像真实的的火焰图? 能不能解决我们讨论过的 case study 的用户问题? 告诉我完整的 case stidy, 类似 blog 一样写出来

---

之后不一定要审查了

---

你就把我要的 case study 做出了

---

能不能直接复用之前的 casestudy 和之前的框架?

---

不要自己做一套

---

你之前是不是做过两个 casedtudy

---

codex-agent-long-horizon-v1：41 条长期 session 的总体 profile，并对三条 git-multibranch 运行做同任务下钻，回答任务如何拆解、SSH 诊断为何反复、哪些路径高 token 但没有完成要求。
agentreward-diff-pprof-v1：440 条真实 trace、125 个 mixed-outcome task、338 个成功/失败配对，用差分 pprof 看失败侧重复/无进展路径与成功侧 terminal/conclusion 路径。之前的结果有了吗? 看起来怎样?

---

你就直接改工具然后去改进旧的两个图和结论, 然后把两个 casestudy 放进论文

---

现在 RQ1-4 分别是啥? 仔细讲解一下? 符合 NIPS/AAAi 水平吗

---

AgentSight 能否把系统副作用连接到正确 agent operation？20 个真实 Codex 任务及并发 control。
1,574 个目标 effect 中恢复 1,520 个。
precision 100%，recall 96.57%。
1,629 个 control effect 全部拒绝。 正确性不需要评估吧

---

我们刚刚讨论的这些记录到 user instructuin' 了吗

---

RQ1–RQ4 效果能不能大幅度提高? 你来手动标注?

---

新的 casestudy 的图生成了吗? 给我看看

---

session / prompt 不应该是被 operation 覆盖了吗

---

堆栈应该是 agent -> operation (session) -> operation (user prompt) -> operation -> operation .... -> LLM call -> toolcall?

---

我没有这样的要求吧? 栈中继续保留 session → prompt → LLM call → tool call，可以从聚合 operation 下钻到原始证据。这个句话是不是删掉? 误导你了?

---

确保把文档和论文清理好

---

做好重新给我看看图

---

能不能更好的方式生成更好看的火焰图?

---

看看有没有啥工具从 pprof 生成

---

我觉得看起来还是不太对, 很明显没有层次感? 比原先的还差了>

---

我们是不是要一个机械检查和 warning? 比如说一个 stack 的 chlid 应该 >=2

---

最多 3 个有意义的词, 不需要任务特定, 最好是 1-3 个, 形式为 动词 (+ 对象) (+ 可选限定词), 这样我们大范围聚合还可以进一步通过动词聚合之类的? 你快看之前的单个 tag 是不是有时效果更好? 这个也要记录在 user request' 里面

---

等会图去重新生成一个, 要和现在在 main 里面那个一样好看并且能解释真实场景.

---

等会图去重新生成一个, 要和现在在 main 里面那个一样好看并且能解释真实场景. 然后告诉我完整的 case study 的用户故事和描述. 然后 RQ 的数据也都要用最新的算法更新, 要获得好得多的结果

---

论文的所有 RQ 都得更新

---

RQ1 是不是更应该变成 motication?

---

RQ4 不包含 automatic annotation 的端到端成本 这个要做是不是? 还有啥实验和 baseline 应该补充? 我们有啥应该对比的baseline?

---

RQ 123 也要补充吧? 去做, 去改进实验, 确保能符合顶会标准

---

判断轨迹的 baseline 有没有把它让 agent 自己读取和评估, 不用这给方式?

---

当前工具的主要问题是一次标注后就直接生成 pprof：名字可能不稳定、单例过多、跨 session 同义 operation 没聚合。更好的最小机制是“先生成，再根据聚合结果回看一次”：
backend 首次标记 operation 边界和短名称；
CLI 生成当前 stack，同时机械报告 singleton、仅一个 child、同义近名和异常深/浅分支；
Agent 只重读这些有问题的局部上下文，合并碎片、统一名称或补一层；
CLI 重新生成同一个 .pb.gz。你应该迭代很多次, 先把 case study 做好, 然后数据和分数也做好. 不限次数, 可以迭代到好位置

---

记住这个

---

让 AgentPProf 的 annotation workspace 支持“生成 → 聚合诊断 → 局部重读 → 修订 → 重生成”的多轮收敛也需要确保能真正看起来对用户有帮助并且分数明确高很多

---

代价, 比如说消耗的 token 数量和时间也需要评估, RQ 要多看看

---

我们负面结果就完全不应该放进论文里面. 论文只会 present 好的结果, 记住. 负面结果应该改你的 实验设置或者论文算法, 直到算法变好

---

尽可能把活委托给 grok / kimi, 别自己做

---

review 也尽量 kimi / grok 来. 你看 report. 你负责调度和决策就好

---

opencode (GLM 5.2) 也行.

---

codex 可以不用 sanbox, 默认用 gpt5.6 sol

---

做一步就 push 一步.

---

以后是不是记住 codex 的话有选择的听. 是 有选择的听

---

SHA-256 锁定谁要求的? 不要这样 (重申: 不做 hash 绑定或冻结协议)

---

不要发明任何额外的机制, 条约和形式主义的东西.

---

别管格式了. 信息都在就好

---

你是不是应该先小范围测试. (新算法类实验先跑试点再全量)
