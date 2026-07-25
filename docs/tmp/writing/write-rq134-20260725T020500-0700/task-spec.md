# WRITE task: three bounded positive-evidence insertions (RQ1/RQ3/RQ4)

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
You may edit EXACTLY TWO files: `docs/paper/main.tex` and
`docs/paper/references.bib`. Nothing else. No git commands ever. Never touch
`docs/agentpprof-paper/` (submodule). Do not change any existing sentence,
claim, number, table, figure, RQ wording, or the thesis sentence — you are
ONLY inserting the three additions below and updating one limitation clause.

House style: every inserted English sentence is followed by a `%`-comment
line with its Chinese translation, matching the file's existing bilingual
convention. Keep each insertion tight; do not pad.

## Insertion 1 — RQ1 population-scale rank agreement

VERIFY numbers first against
`docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/experiment-001/results.md`
(and its result-review.md for the admissible-claim scope).

Location: in `\subsection{RQ1: Multi-Resource Attribution}`, insert a new
short paragraph immediately AFTER the paragraph ending
"We do not claim that one resource measure universally dominates another."
(and its Chinese comment line).

Content to express (adapt wording, keep all numbers exact):
- Replaying the frozen 440-session AgentRewardBench hierarchy (7,229
  operations, 51,904,621 provider-reported tokens, both conserved exactly)
  ranks the same operations once by operation count and once by tokens.
- Mean per-task Kendall's tau-b 0.886 (10,000-draw task-cluster bootstrap
  95% interval [0.857, 0.915]) and Spearman rho 0.935 [0.917, 0.953] over
  the 77 of 125 tasks with at least three distinct operations; pooled
  tau-b 0.929.
- Reading: one fixed hierarchy replays across measures with exact
  conservation and stable dominant responsibilities for most web-scale
  tasks, while 10 of 77 tasks fall below tau-b 0.7 and the long-horizon Git
  case shifts attributed importance by more than a factor of two — the
  regimes where selecting the measure changes the engineering decision are
  exactly where multi-measure replay pays.
- Cite standard metric definitions: add bib entries (if absent) for
  Kendall 1938 (Biometrika, "A new measure of rank correlation") and
  Spearman 1904 (Am. J. Psychology) and cite them at first mention.

## Insertion 2 — RQ3 model-capacity sentence

VERIFY the 3B numbers first against the step-0031 records under
`docs/tmp/build-and-evaluate/step-0031-*/` (expected: Qwen2.5-3B task-family
accuracy 0.394, macro-F1 0.191 on the same 1,012 AgentBoard goals; if the
records differ, use the recorded values).

Location: in the RQ3 paragraph about AgentBoard task families, insert ONE
sentence (plus Chinese comment) immediately after the sentence ending
"...and produces identical assignments across three runs." Content: the
identical protocol with a 3B backend reaches only the verified lower
macro-F1, so literal task-family identity emerges with backend capacity
rather than prompt design.

## Insertion 3 — RQ4 end-to-end automatic annotation cost

VERIFY numbers first against
`docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`
and `.../git-convergence-result.md` (fresh full pass column only).

Location: in `\subsection{RQ4: Profiling Cost}`, insert a new paragraph
immediately BEFORE the paragraph beginning "The existing automatic-Agent
annotations were produced in two disjoint workflow waves...". Then update
that following paragraph and the Scope-and-Limitations clause as described
below.

Content to express (numbers exact from the records):
- A fully instrumented end-to-end automatic annotation now exists. On the
  complete 440-session AgentRewardBench population, the fixed automatic
  backend completes all 12 outcome-blind batches in 3,521.6 s end-to-end on
  a fixed two-worker schedule (58.7 min; summed worker time 6,661.7 s),
  consuming 12,039,417 actual input tokens (10,929,408 reported cached) and
  312,433 output tokens — 27,362 input and 710 output tokens per session.
- On the three-session Git population, one fresh complete pass takes
  466.9 s and 832,544 actual input tokens.
- Deterministic materialization of the full 440-session population takes
  0.26 s (operations) / 0.25 s (tokens); construction cost is dominated by
  the automatic backend, and replay remains sub-second.
- In the existing following paragraph ("two disjoint workflow waves ...
  54.36 minutes"), keep it but add a short clause noting the newly
  instrumented AgentRewardBench pass above supersedes the envelope as the
  reportable annotation cost.
- In `\subsection{Scope and Limitations}`, the sentence currently claiming
  RQ4 "excludes ... instrumented model/provider annotation timing" is now
  partially stale: revise minimally so it instead says capture and
  raw-to-normalized conversion remain excluded, while automatic annotation
  cost is instrumented on the named AgentRewardBench and Git populations.

## Validation and deliverables

1. After editing, run `cd docs/paper && latexmk -pdf main.tex` and confirm
   it compiles with no errors (warnings acceptable). If compilation fails,
   fix YOUR insertion, not existing text.
2. Write `write-report.md` in THIS directory: the exact inserted LaTeX for
   each insertion, the verified source values with file paths, and the
   compile result (page count, no-error confirmation).
3. Do not stage, commit, or push anything.
