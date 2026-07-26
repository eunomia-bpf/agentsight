# WRITE task: add Case Study 3 — profiling the agents that built the profiler

Edit EXACTLY ONE file: `docs/paper/main.tex` in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
No git commands. Verify every number against
`docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/results.md`
(and cost-record.md / aggregate-summary.md) before inserting. House style:
each English sentence followed by a Chinese %-comment. Keep thesis x3,
RQ titles, and all existing content unchanged. Do not worry about page
count; information completeness first.

## Insertion — new subsection after Case Study 2

`\subsection{Case Study 3: Profiling the Agents that Built This Profiler}`
inserted immediately after the Case Study 2 subsection ends (before
\subsection{RQ3...}). Content (adapt wording; numbers exact):

- Population: all 42 long-horizon development sessions from the authors'
  workstation for this very project (18 Codex, 24 Claude Code) — the
  agents that built \sys{} and this paper; the longest sessions run tens
  of hours and hundreds of prompts. This is the native no-sudo
  local-history scenario: one `--workspace-out` invocation initializes
  the standard annotation workspace from the raw session logs.
- Scale: 10,423 source nodes (42 sessions, 1,252 prompts, 5,620 LLM
  calls, 3,509 tool calls) carrying 1,380,863,014 bounded provider token
  components.
- Annotation: the fixed automatic instruction (identical to the
  AgentRewardBench run), one pass, 1,737 semantic annotations at depths
  two through four, all 1,294 mandatory session/prompt scopes covered,
  zero backend failures across 42 batches; both operation-count and
  token profiles conserve exact mass (3,509 and 1,380,863,014) and load
  in stock pprof.
- Findings: development work is broad rather than concentrated — the
  largest token path (refine paper -> align evaluation) holds only
  1.735% of token mass; token mass sits mostly at the mandatory prompt
  depth (70.4%) while operation mass resolves deeper (43.9% at depths
  three and four); the three longest sessions carry distinct dominant
  responsibilities (evaluation alignment, evidence inspection, and
  merge/conflict resolution), so long-session responsibility structure
  is preserved rather than averaged away.
- Cost (RQ4-consistent): three-worker critical path 44.6 minutes,
  15,231,328 reported input tokens of which 13,112,320 cached, 311,097
  output tokens, sub-second validation.
- One scope sentence: descriptive feasibility on real long-horizon
  sessions without outcome labels.

## Validation

`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` — no
errors, no undefined references; thesis x3; unique cite keys unchanged.
write-report.md in THIS directory: inserted LaTeX, verified sources,
compile result and page count.
