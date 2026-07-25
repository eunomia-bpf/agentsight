# WRITE task: RQ2 mechanism scoping + TraceElephant reader-study paragraph

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
You may edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands ever
(including `git stash`). Never touch `docs/agentpprof-paper/`. Do not change
any existing number, table, figure, RQ wording, or the thesis sentence.
House style: every inserted English sentence is followed by a `%`-comment
line with its Chinese translation.

VERIFY every number you insert against these records first:
- `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/results.md`
  and `.../step-0079-20260724T235753-0700/result-review.md`
- `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/results.md`
  and `.../step-0080-20260725T004136-0700/result-review.md`
- `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/result-review.md`
  (admissible claim wording) and `.../independent-review.md` (content-delta
  interval)

## Edit 1 — extend the matched-tie paragraph (mechanism scoping)

Locate the RQ2 paragraph beginning "The information-matched
Direct+Raw+Evidence refinement reaches .893, .518, and .324." Immediately
after the sentence "The matched result attributes the ranking gain to
group/evidence refinement in the complete profile, not specifically to its
semantic prefix." insert TWO sentences (plus Chinese comments):

1. This tie is the expected mechanism boundary: per-operation anomaly
   signal resides in the retained source evidence, which both views share
   by construction.
2. The semantic prefix's distinct, separately measured roles are cross-run
   attribution (RQ1) and directing a reader's attention, which the
   following study measures.

Keep the paragraph's remaining sentences unchanged.

## Edit 2 — new paragraph before Case Study 2

Insert a `\paragraph{Profile-guided reading on TraceElephant.}` immediately
before `\subsection{Case Study 2: Differential Profiling at Scale}`,
expressing exactly (tight, ~9-11 sentences, numbers exact):

- Setup: on the complete 220 target-bearing TraceElephant queries, a fixed
  external Grok-family CLI reader receives target-blind packets (task text,
  operation IDs, and source-visible content; one single-turn call per
  stage; unranked operations appended in original order deterministically).
- Full-trace reading reaches MAP 0.502 versus 0.209 for the benchmark's
  Direct-only diagnostic and 0.326 for Direct+AgentProf, at a mean 12,615
  input tokens per query.
- Two-stage profile-guided reading: stage one shows only the semantic
  operation skeleton (no source content) and the reader selects at most
  five groups; stage two opens only the selected groups' evidence. It
  reaches MAP 0.455 while opening 53.0% of the source content, and its
  stage-one selections never fell back to a default.
- Semantic-versus-raw skeleton control: with the information-matched
  raw-action skeleton, ranking quality is statistically unchanged (0.465;
  paired delta +0.010 [-0.021, +0.042]) but the reader opens significantly
  more content: 65.0% versus 53.0%, paired delta +0.120 [+0.103, +0.137],
  and 2.80 [1.96, 3.60] more evidence operations. Semantic naming's
  measured contribution in this regime is attention concentration at equal
  quality.
- Feasibility close: a per-query full read is bounded by the model context
  window; populations like the 4,558,192-token repeated Git task cannot be
  read whole, whereas skeleton-guided drilldown remains available at any
  trace length.
- Disclose in one clause: the reader is query-specific, whereas the
  hierarchy is constructed once and replayed across queries and measures.

Do NOT claim: any cross-workload generalization of this study; any total
token or dollar savings; any MAP superiority of the semantic skeleton.
"Content opened" means source-evidence volume, not total request tokens.

## Validation and deliverables

1. `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` must
   compile with no errors and no undefined citations (no new citations are
   needed; do not add bib entries).
2. Write `write-report.md` in THIS directory: the exact inserted LaTeX, the
   verified source values with file paths, and the compile result.
