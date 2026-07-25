# WRITE task: abstract and intro results-paragraph rework (two replacements)

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
You may edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands ever.
Never touch `docs/agentpprof-paper/`. Do not change the thesis sentence, any
RQ wording, any table, or any number other than through the two exact
replacements below. Every inserted English sentence gets a following
Chinese `%`-comment line. Net length must not increase: each replacement
must be no longer than what it replaces (in lines) plus at most one line.

Numbers you may use are already verified in the RQ2 section you can read at
the `\paragraph{Profile-guided reading on TraceElephant.}` paragraph; do
not introduce any number not present in the current paper body.

## Replacement 1 — abstract

Find in the abstract the sentence:
"On three complete localization workloads used for protocol development,
AgentProf raises MAP over benchmark-native direct diagnostics by 0.031,
0.107, and 0.117, but is statistically indistinguishable from an
information-matched raw-action plus source-evidence refinement."
(and its Chinese comment line).

Replace with (adapt phrasing minimally if needed; keep both facts):
"On three complete localization workloads, AgentProf raises MAP over
benchmark-native direct diagnostics by 0.031, 0.107, and 0.117. Used as a
reading index on TraceElephant, the semantic hierarchy guides a strong
trajectory reader to equal ranking quality while opening 53.0% of the
source evidence, versus 65.0% under an information-matched raw-action
grouping, and skeleton-guided drilldown remains available beyond the
context-window bound where whole-trace reading fails."
Plus matching Chinese comment lines.

## Replacement 2 — introduction results paragraph (¶7)

Find in the introduction the two sentences:
"Across three complete public workloads used for protocol development,
AgentProf refines benchmark-native direct diagnostic ties and raises MAP by
0.031, 0.107, and 0.117, respectively~\cite{agentprocessbench,hintbench,traceelephant}.
An information-matched raw-action plus source-evidence refinement is
statistically tied on all three workloads."
(and their Chinese comment lines).

Replace the SECOND sentence only with:
"On TraceElephant, the same fixed hierarchy also serves as a reading index:
a strong reader reaches statistically equal ranking quality while opening
significantly less source evidence (53.0% versus 65.0%) than with an
information-matched raw-action grouping."
Plus its Chinese comment line. Keep the first sentence and its citation
exactly as is.

## Validation and deliverables

1. `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` must
   compile with no errors; page count must not exceed the current count.
2. Confirm the thesis sentence "Agent observability needs profiling, not
   only debugging." still appears exactly at its three existing locations,
   unmodified.
3. Write `write-report.md` in THIS directory: exact before/after LaTeX for
   both replacements and the compile result.
