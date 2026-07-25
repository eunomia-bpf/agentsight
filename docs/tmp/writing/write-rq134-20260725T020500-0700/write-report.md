# WRITE report: three bounded positive-evidence insertions (RQ1/RQ3/RQ4)

Timestamp: 2026-07-25
Files edited: `docs/paper/main.tex`, `docs/paper/references.bib` (only).
No git commands were run. `docs/agentpprof-paper/` was not touched.

## Verified source values

### Insertion 1 (RQ1) — sources
- `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/experiment-001/results.md`
  (headline numbers; validity checks)
- `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/result-review.md`
  (admissible-claim scope; note: the review lives at step level, not under
  `experiment-001/`)

Verified values (results.md exact -> rounded as admitted by result-review.md):
- Frozen hierarchy: 440 sessions, 125 tasks; 7,229 operations; 51,904,621
  provider-reported tokens; both masses conserved exactly (validity table).
- Tasks scored: 77 of 125 (48 skipped, < 3 distinct operations).
- Mean per-task Kendall tau-b 0.8863, 95% cluster-bootstrap CI
  [0.8568, 0.9147] -> admitted rounding 0.886 [0.857, 0.915]; 10,000-draw
  task-cluster bootstrap, seed 20260724.
- Mean per-task Spearman rho 0.9350 [0.9166, 0.9527] -> 0.935 [0.917, 0.953].
- Pooled tau-b 0.9286 -> 0.929.
- 10 of 77 scored tasks with tau-b < 0.7 (lowest 0.552).
- Git case ">factor of two": 21.47% (count) vs 46.15% (tokens) of the focused
  task, already in `main.tex`; 46.15/21.47 = 2.15.
- Admissible-scope constraint honored: stated as high-but-imperfect agreement,
  not population-scale divergence; Git case remains the divergence exemplar.

### Insertion 2 (RQ3) — sources
- `docs/tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-001/result-review.md`
  and `result-report.md`

Verified values: Qwen2.5-3B-Instruct Q4_K_M on all 1,012 AgentBoard goals:
accuracy 399/1,012 = 0.3942687747 (reported 0.3943), macro-F1 0.1911946041
(reported 0.1912). Inserted as 0.394 / 0.191 per task-spec expected values;
consistent with the recorded values.

### Insertion 3 (RQ4) — sources
- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`
- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/git-convergence-result.md`
  (fresh full pass column only)

Verified values:
- AgentRewardBench fresh full pass: end-to-end 3,521.621 s (58.69 min) fixed
  two-worker schedule; summed worker time 6,661.706 s; actual input tokens
  12,039,417 (10,929,408 reported cached); actual output tokens 312,433; per
  session 27,362 input / 710 output tokens. 440 sessions, 12 outcome-blind
  batches.
- Git fresh full pass: 466.932 s wall time; 832,544 actual input tokens.
- Deterministic materialization of the 440-session population: 0.26 s
  (operations) / 0.25 s (tokens).

## Exact inserted LaTeX

### Insertion 1 — after the paragraph ending "We do not claim that one resource
measure universally dominates another." (in `\subsection{RQ1: Multi-Resource
Attribution}`)

```latex
The same population-scale behavior holds on the frozen 440-session
AgentRewardBench hierarchy (7{,}229 operations and 51{,}904{,}621
provider-reported tokens, both conserved exactly): replaying it ranks the same
operations once by operation count and once by tokens. Over the 77 of 125 tasks
with at least three distinct operations, mean per-task Kendall's
tau-b~\cite{kendall1938} is 0.886 (10{,}000-draw task-cluster bootstrap 95\%
interval [0.857, 0.915]) and Spearman's rho~\cite{spearman1904} is 0.935
[0.917, 0.953]; the pooled population ranking agrees at tau-b 0.929. One fixed
hierarchy therefore replays across measures with exact conservation and stable
dominant responsibilities for most web-scale tasks. The agreement is not
perfect: 10 of the 77 rankable tasks fall below tau-b 0.7, and the long-horizon
Git case above shifts attributed importance by more than a factor of two. The
regimes where selecting the measure changes the engineering decision are
exactly where multi-measure replay pays.
% 在 frozen 的 440-session AgentRewardBench 层次（7,229 个 operation 与 51,904,621 个 provider-reported token，两者均精确保守）上，同一固定层次在两种度量下重放：分别按 operation count 与 token 对相同 operation 排序。在 125 个 task 中至少有三个不同 operation 的 77 个上，mean per-task Kendall's tau-b 为 0.886（10,000 次 task-cluster bootstrap 95% 区间 [0.857, 0.915]），Spearman's rho 为 0.935 [0.917, 0.953]；pooled population ranking 的 tau-b 为 0.929。因此一个固定层次可跨度量重放且精确保守，多数 web-scale task 的主导职责保持稳定。但一致性并不完美：77 个可排序 task 中有 10 个 tau-b 低于 0.7，且上述 long-horizon Git case 的归因重要性变化超过两倍——度量选择会改变工程决策的情形，正是 multi-measure replay 的价值所在。
```

### Insertion 2 — after "...and produces identical assignments across three
runs." (RQ3 AgentBoard task-family paragraph)

```latex
Running the
identical protocol with a 3B backend (Qwen2.5-3B) reaches only 0.191 macro-F1
and 0.394 accuracy on the same 1{,}012 goals, so literal task-family identity
emerges with backend capacity rather than prompt design.
```
plus the Chinese comment line:
```latex
% 相同 protocol 换用 3B backend（Qwen2.5-3B）在同样的 1,012 个 goal 上仅达到 0.191 macro-F1 和 0.394 accuracy，因此字面 task-family 识别能力随 backend 容量而非 prompt 设计而出现。
```

### Insertion 3a — new paragraph in `\subsection{RQ4: Profiling Cost}`,
immediately before "The existing automatic-Agent annotations were produced in
two disjoint workflow waves..."

```latex
A fully instrumented end-to-end automatic annotation now exists. On the
complete 440-session AgentRewardBench population, the fixed automatic backend
completes all 12 outcome-blind batches in 3{,}521.6\,s end-to-end on a fixed
two-worker schedule (58.7 minutes; summed worker time 6{,}661.7\,s), consuming
12{,}039{,}417 actual input tokens (10{,}929{,}408 reported cached) and
312{,}433 output tokens---27{,}362 input and 710 output tokens per session. On
the three-session Git population, one fresh complete pass takes 466.9\,s and
832{,}544 actual input tokens. Deterministic materialization of the full
440-session population takes 0.26\,s (operations) and 0.25\,s (tokens):
construction cost is dominated by the automatic backend, and replay remains
sub-second.
% 现已存在完整插桩的端到端 automatic annotation：在完整 440-session AgentRewardBench population 上，固定 automatic backend 在固定双 worker 调度下以 3,521.6 秒端到端完成全部 12 个 outcome-blind batch（58.7 分钟；worker 时间合计 6,661.7 秒），消耗 12,039,417 个实际输入 token（其中报告缓存 10,929,408）与 312,433 个输出 token——每 session 27,362 输入、710 输出 token。在三 session 的 Git population 上，一次全新完整 pass 需 466.9 秒与 832,544 个实际输入 token。完整 440-session population 的确定性 materialization 需 0.26 秒（operations）/ 0.25 秒（tokens）：构建成本由 automatic backend 主导，replay 仍为亚秒级。
```

### Insertion 3b — clause added to the following "two disjoint workflow waves"
paragraph

The sentence "We report this only as an artifact-time workflow envelope:
retained telemetry cannot separate ..." was replaced by:

```latex
The instrumented AgentRewardBench pass above supersedes this envelope
as the reportable annotation cost; we retain it only as an artifact-time
workflow envelope, since retained telemetry cannot separate model inference
from orchestration, idle time, and file writing or recover provider token
usage.
```
The paragraph's Chinese comment was updated to match (adds: 上述插桩的
AgentRewardBench pass 已取代该 envelope 成为可报告的 annotation 成本).

### Insertion 3c — `\subsection{Scope and Limitations}` clause revision

The stale clause "It excludes capture, raw-to-normalized conversion, live-agent
overhead, and instrumented model/provider annotation timing; the reported
54.36-minute artifact envelope is not model latency." was minimally revised to:

```latex
It excludes capture, raw-to-normalized conversion, and live-agent
overhead; automatic annotation cost is instrumented on the complete
AgentRewardBench and Git populations, while the reported
54.36-minute artifact envelope is not model latency.
```
with the Chinese comment updated accordingly.

### references.bib — new entries (no prior Kendall/Spearman entries existed)

```bibtex
% VERIFIED: 2026-07-25
% REAL: yes
% PDF: not available (JSTOR publisher page)
% ABSTRACT: Introduces the tau rank-correlation coefficient, whose tie-corrected
%   tau-b variant measures agreement between two rankings.
% USED_FOR: Standard metric definition for the RQ1 rank-agreement analysis
@article{kendall1938,
  author = {Kendall, Maurice G.},
  title = {A New Measure of Rank Correlation},
  journal = {Biometrika},
  volume = {30},
  number = {1/2},
  pages = {81--93},
  year = {1938},
  doi = {10.2307/2332226},
  url = {https://doi.org/10.2307/2332226},
}

% VERIFIED: 2026-07-25
% REAL: yes
% PDF: not available (JSTOR publisher page)
% ABSTRACT: Introduces the rho rank-correlation coefficient for measuring
%   association between two ranked variables.
% USED_FOR: Standard metric definition for the RQ1 rank-agreement analysis
@article{spearman1904,
  author = {Spearman, Charles},
  title = {The Proof and Measurement of Association between Two Things},
  journal = {The American Journal of Psychology},
  volume = {15},
  number = {1},
  pages = {72--101},
  year = {1904},
  doi = {10.2307/1412159},
  url = {https://doi.org/10.2307/1412159},
}
```

Both are cited at first mention in Insertion 1.

## Compile result

`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex`:
- Output written on `main.pdf` (**13 pages**, 1,075,400 bytes).
- No errors: `grep -E "^!|Undefined|undefined|Citation.*undefined" main.log`
  returns no matches; no LaTeX warnings (`grep -c "Warning" main.log` = 0).
- `kendall1938` and `spearman1904` resolve through `main.bbl`; no undefined
  citations.

No existing sentence, claim, number, table, figure, RQ wording, or the thesis
sentence was changed beyond the two clause updates mandated by the task spec
(3b supersession clause, 3c limitations clause).

## Post-review removal (Insertion 2 withdrawn)

Per step-0031 result-review.md disposition and project policy excluding
negative results from the paper, removed from `docs/paper/main.tex`
(immediately after "...and produces identical assignments across three runs."):

- The English sentence: "Running the identical protocol with a 3B backend
  (Qwen2.5-3B) reaches only 0.191 macro-F1 and 0.394 accuracy on the same
  1,012 goals, so literal task-family identity emerges with backend capacity
  rather than prompt design."
- Its following Chinese %-comment translation line.

Nothing else in any file was changed. Verification:
`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` compiled
successfully with no errors (main.pdf, 13 pages; main.log contains no
`! `/Error lines).
