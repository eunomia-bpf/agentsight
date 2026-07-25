# Write report — RQ2 mechanism scoping + TraceElephant reader-study paragraph

Timestamp: 2026-07-25 (UTC-07:00 post-edit)
Target file: `docs/paper/main.tex` (only file edited)
No git commands run.

## Edit 1 — mechanism scoping in the matched-tie paragraph

Locating paragraph: the RQ2 paragraph beginning "The information-matched
Direct+Raw+Evidence refinement reaches .893, .518, and .324." Two sentences
were inserted immediately after "...not specifically to its semantic prefix."
and before the existing "Separately, that prefix supplies..." sentence. All
other sentences in the paragraph are unchanged.

Exact inserted LaTeX (after the period following "semantic prefix"):

```latex
This tie is the expected mechanism boundary: per-operation
anomaly signal resides in the retained source evidence, which both views share
by construction.
% 这一持平是预期的机制边界：per-operation 异常信号位于保留的 source evidence 中，两种视图在构造上共享这些 evidence。
The semantic prefix's distinct, separately measured roles are cross-run
attribution (RQ1) and directing a reader's attention, which the following
study measures.
% semantic prefix 的独立、分别测量的角色是 cross-run attribution（RQ1）与引导读者注意力，后者由下文研究测量。
```

Edit 1 introduces no numbers and modifies no existing numbers, RQ wording,
table, figure, or thesis sentence.

## Edit 2 — new `\paragraph{Profile-guided reading on TraceElephant.}` block

Inserted immediately before `\subsection{Case Study 2: Differential Profiling
at Scale}` (now at line 799 of `docs/paper/main.tex`). Exact inserted LaTeX:

```latex
\paragraph{Profile-guided reading on TraceElephant.}
On the complete 220 target-bearing TraceElephant queries, a fixed external
Grok-family CLI reader receives target-blind packets---task text, operation
IDs, and source-visible content---with unranked operations appended in
original order deterministically and one single-turn call per stage.
% 在完整的 220 个带 target 的 TraceElephant query 上，一个固定的外部 Grok 家族 CLI reader 接收 target-blind packet——任务文本、operation ID 与 source-visible 内容——未排名 operation 按原始顺序确定性附加，每个 stage 单轮调用。
Full-trace reading reaches MAP .502 versus .209 for the benchmark's
Direct-only diagnostic and .326 for Direct+AgentProf, at a mean 12{,}615
input tokens per query.
% 全 trace 阅读达到 MAP .502，而 benchmark 的 Direct-only 诊断为 .209、Direct+AgentProf 为 .326，平均每个 query 12,615 输入 token。
A two-stage profile-guided variant first shows only the semantic operation
skeleton, with no source content, and the reader selects at most five groups;
stage two then opens only the selected groups' evidence.
% 两阶段 profile-guided 变体首先只展示 semantic operation 骨架（无 source 内容），reader 最多选择 5 个 group；第二阶段只打开所选 group 的 evidence。
It reaches MAP .455 while opening 53.0\% of the source content, and its
stage-one selections never fell back to a default.
% 它达到 MAP .455，同时只打开 53.0\% 的 source 内容，且第一阶段选择从未回退到默认值。
Under an information-matched raw-action skeleton, ranking quality is
statistically unchanged (MAP .465; paired delta $+.010$ [$-.021$, $+.042$]).
% 在信息匹配的 raw-action 骨架下，排名质量在统计上不变（MAP .465；配对差异 +.010 [-.021, +.042]）。
But the reader opens significantly more content: 65.0\% versus 53.0\%, paired
delta $+.120$ [$+.103$, $+.137$], and $2.80$ [$1.96$, $3.60$] more evidence
operations.
% 但 reader 打开显著更多的内容：65.0\% 对 53.0\%，配对差异 +.120 [+.103, +.137]，且多 2.80 [1.96, 3.60] 个 evidence operation。
Semantic naming's measured contribution in this regime is attention
concentration at equal quality.
% 在此机制下 semantic naming 测得的贡献是同等质量下的注意力集中。
A per-query full read is bounded by the model context window: populations
such as the 4{,}558{,}192-token repeated Git task cannot be read whole,
whereas skeleton-guided drilldown remains available at any trace length.
% 单 query 全量阅读受限于模型上下文窗口：诸如 4,558,192-token 的重复 Git 任务这类种群无法整体阅读，而骨架引导的下钻在任何 trace 长度下都可用。
The reader is query-specific---it re-reads each trajectory per
question---whereas the hierarchy is constructed once and replayed across
queries and measures.
% reader 是 query-specific——每个问题都重新阅读整条轨迹——而层次结构只构造一次，跨 query 与 measure 复用。
```

The paragraph contains 9 English sentences (each immediately followed by its
Chinese `%`-comment translation, per task house style). It makes no
cross-workload generalization claim (explicitly scoped to "the complete 220
target-bearing TraceElephant queries"), no total-token or dollar savings
claim, and no MAP-superiority claim for the semantic skeleton (wording is
"statistically unchanged" and "attention concentration at equal quality").
"Content opened" is consistently described as source-evidence volume ("opens
only the selected groups' evidence", "opening 53.0\% of the source content"),
not total request tokens.

## Verified source values

Every inserted number was checked against the named source records before
insertion. Mapping (paper value → source value → file path):

| Paper value | Source value | File |
|---|---|---|
| 220 target-bearing queries | "Trajectories / target-bearing queries scored: 220" | `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/results.md:6` (also step-0080 results.md:12) |
| Full-trace reader MAP .502 | `Direct reader (this experiment) 0.501967` | `step-0079.../experiment-001/results.md:38` |
| Direct-only MAP .209 | `Direct-only (stored) 0.208713` | `step-0079.../experiment-001/results.md:39` |
| Direct+AgentProf MAP .326 | `Direct+AgentProf (stored) 0.325504` | `step-0079.../experiment-001/results.md:40` |
| mean 12,615 input tokens per query (full-trace) | "full-trace 12,615 mean input tokens/query" | `step-0080-20260725T004136-0700/result-review.md:56` (tiktoken o200k_base supplement) |
| Profile-guided reader MAP .455 | `Profile reader (this experiment) 0.455333` | `step-0080.../experiment-001/results.md:41` |
| 53.0% source content opened | "Mean content-opened fraction ... 0.5301" | `step-0080.../experiment-001/results.md:77` |
| stage-one selections never fell back to a default | "Stage-1 largest-groups fallbacks: 0"; "Stage-1 OK first attempt: 220" | `step-0080.../experiment-001/results.md:55,57` |
| raw-action skeleton MAP .465 | "0.465129" (raw_action MAP, independent recomputation); "MAP 0.455 vs 0.465" | `step-0081-20260725T012438-0700/independent-review.md:23`; `step-0081.../result-review.md:13-15` |
| paired delta +.010 [-.021, +.042] | "paired delta +0.0098 [-0.0208, +0.0424]"; bootstrap reproduced "[-0.02076671, +0.04241655]" | `step-0081.../result-review.md:14-16`; `step-0081.../independent-review.md:30-32` |
| 65.0% vs 53.0%, paired delta +.120 [+.103, +.137] | "content-opened fraction 53.0% vs 65.0%, paired delta +0.120 [+0.103, +0.137]"; independent: mean 0.6501 vs 0.5301, Δ +0.1200 [+0.1034, +0.1367], 0/10000 nonpos. | `step-0081.../result-review.md:16-18`; `step-0081.../independent-review.md:42-48` |
| 2.80 [1.96, 3.60] more evidence operations | "2.80 [1.96, 3.60] fewer evidence operations opened"; independent: "+2.80 ... [+1.96, +3.60] ... 0/10000" | `step-0081.../result-review.md:18`; `step-0081.../independent-review.md:46` |
| 4,558,192-token repeated Git task | "4,558,192 provider-reported trace tokens"; "Git/tokens ... 4,558,192" | `step-0077-20260723T233616-0700/experiment-001/git-convergence-result.md:19`; `step-0077.../experiment-001/code-review-001.md:37` |

Rounding convention follows the surrounding RQ2 paragraph and Table 3
(`.893`, `.518`, `.324`, etc.): MAP values to three decimals with no leading
zero, intervals as `[lo,hi]` with no internal spaces; non-MAP values
(percentages, token counts, operation counts) keep their natural form. Signs
are kept on the deltas because both directions appear in the same sentence.

## Compile verification

Command: `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex`

Result: **clean build**, `Output written on main.pdf (13 pages, 1078044
bytes)`. `latexmk: All targets (main.pdf) are up-to-date.`

Post-compile scan of `main.log` for `Citation`, `Reference.*undefined`,
`There were undefined`, and case-insensitive `error` (excluding stock
Underfull/Overfull hbox warnings and font-spec warnings): **no matches**. No
new `\cite{}` keys were introduced, no `.bib` entries were added, no undefined
references remain.
