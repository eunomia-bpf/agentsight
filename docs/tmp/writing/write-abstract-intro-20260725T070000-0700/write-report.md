# WRITE report: abstract and intro results-paragraph rework

Task: `docs/tmp/writing/write-abstract-intro-20260725T070000-0700/task-spec.md`
File edited: `docs/paper/main.tex` (only). No git commands run.

## Replacement 1 — abstract

### Before (target sentence, spanning the end of one source line through a full
### line plus its Chinese comment; original main.tex lines 61–66)

```latex
0.541 for raw action and 0.663 for recurrence to 0.704. On three complete
localization workloads used for protocol development, AgentProf raises MAP over
benchmark-native direct diagnostics by 0.031, 0.107, and 0.117, but is
statistically indistinguishable from an information-matched raw-action plus
source-evidence refinement.
% 自动 Agent 标注将相对人工 stage partition 的普通 B$^3$ F1 从 raw action 的 0.541 和 recurrence 的 0.663 提升到 0.704。在用于协议开发的三个完整 localization workload 上，AgentProf 相对 benchmark-native direct diagnostic 将 MAP 分别提高 0.031、0.107 和 0.117，但与信息量匹配的 raw-action 加 source-evidence refinement 在统计上不可区分。
```

### After (new main.tex lines 60–70; the preceding sentence ending
### ``...to 0.704. On three complete'' is retained verbatim)

```latex
0.541 for raw action and 0.663 for recurrence to 0.704. On three complete
localization workloads, AgentProf raises MAP over benchmark-native direct
diagnostics by 0.031, 0.107, and 0.117. Used as a reading index on
TraceElephant, the semantic hierarchy guides a strong trajectory reader to
equal ranking quality while opening 53.0\% of the source evidence, versus
65.0\% under an information-matched raw-action grouping, and skeleton-guided
drilldown remains available beyond the context-window bound where whole-trace
reading fails.
% 在三个完整 localization workload 上，AgentProf 相对 benchmark-native direct diagnostic 将 MAP 分别提高 0.031、0.107 和 0.117。
% 在 TraceElephant 上作为阅读索引时，语义层次引导强 trajectory reader 达到同等排名质量，只打开 53.0\% 的 source evidence，而信息匹配的 raw-action 分组需打开 65.0\%；且骨架引导的下钻可超越整条轨迹阅读失效的上下文窗口边界。
```

Both facts retained (0.031/0.107/0.117 MAP lift; the TraceElephant reading-index
contrast with 53.0% vs 65.0% source-evidence opening and skeleton drilldown past
the context-window bound). All numbers are already present in the RQ2 paragraph
`\paragraph{Profile-guided reading on TraceElephant.}` (53.0% / 65.0% /
context-window-bound language at main.tex lines ~784–793) and the RQ2 bootstrap
deltas (lines ~736–737); no new number introduced.

## Replacement 2 — introduction ¶7

The first sentence and its citation are kept byte-for-byte unchanged; only the
second sentence and the (previously combined) Chinese comment were replaced.

### Before (original main.tex lines 191–196)

```latex
Across three complete public workloads used for protocol development,
AgentProf refines benchmark-native direct diagnostic ties and raises MAP by
0.031, 0.107, and 0.117, respectively~\cite{agentprocessbench,hintbench,traceelephant}.
An information-matched raw-action plus source-evidence refinement is
statistically tied on all three workloads.
% 在用于协议开发的三个完整公开 workload 上，AgentProf 细化 benchmark-native direct diagnostic 的并列，并将 MAP 分别提高 0.031、0.107 和 0.117；信息量匹配的 raw-action 加 source-evidence refinement 在三个 workload 上均与其统计持平。
```

### After (new main.tex lines 195–203)

```latex
Across three complete public workloads used for protocol development,
AgentProf refines benchmark-native direct diagnostic ties and raises MAP by
0.031, 0.107, and 0.117, respectively~\cite{agentprocessbench,hintbench,traceelephant}.
On TraceElephant, the same fixed hierarchy also serves as a reading index:
a strong reader reaches statistically equal ranking quality while opening
significantly less source evidence (53.0\% versus 65.0\%) than with an
information-matched raw-action grouping.
% 在用于协议开发的三个完整公开 workload 上，AgentProf 细化 benchmark-native direct diagnostic 的并列，并将 MAP 分别提高 0.031、0.107 和 0.117。
% 在 TraceElephant 上，同一固定层次也作为阅读索引：强 reader 达到统计持平的排名质量，同时打开的 source evidence 明显更少（53.0\% 对 65.0\%）。
```

The first sentence (including `~\cite{agentprocessbench,hintbench,traceelephant}`)
is identical to the original. The previously combined Chinese comment was split
so the first sentence keeps its documentation and the new second sentence gets
its own `%`-comment line, matching the repo's "every English sentence gets a
following Chinese comment" rule.

## Validation

1. Compile: `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex`
   — succeeded, no `!`/Error/Undefined lines in `main.log`.
   Output: `main.pdf (13 pages, 1078194 bytes)`.
2. Page count: 13 pages before and after — unchanged (does not exceed prior
   count).
3. Thesis sentence `"Agent observability needs profiling, not only debugging."`
   still present, unmodified, at exactly three locations (now lines 49, 158,
   and 1179; previously 49, 154, 1172 — the offsets shifted by the net added
   lines but the text is verbatim).
4. Scope: only `docs/paper/main.tex` edited, via exactly the two replacements
   above. No tables, no other numbers, no RQ wording, no other files touched.
   `docs/agentpprof-paper/` untouched. No git commands run.
