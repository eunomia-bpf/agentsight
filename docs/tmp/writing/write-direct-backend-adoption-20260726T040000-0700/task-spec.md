# WRITE task: adopt the direct multi-level backend in the paper

Edit EXACTLY ONE file: `docs/paper/main.tex` in
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
No git commands. Verify every number against
`docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/results.md`
(and its cost-record.md) before use. House style: bilingual %-comments.
Keep thesis x3, the four RQ question titles, and all other content intact.
Information completeness first; page count is not a constraint.

## Edit 1 — Design: replace the recursive-policy description

In `\section{Design}`, the paragraph beginning "The evaluated Agent backend
instantiates this contract with a fixed binary recursive policy." describes
the old protocol. Replace that paragraph with a direct-protocol
description (3-4 sentences): the evaluated Agent backend reads each
trajectory's complete source-only packet once and directly emits sparse
complete-path marks at the transition points it identifies, naming each
enclosing responsibility; depth is chosen freely per branch with no cap or
threshold; one format retry is allowed and the deterministic root-prefix
repair and canonicalization replay are unchanged downstream. Note in one
clause that an earlier interval-recursive protocol is retained in the
research record and was outperformed by this direct protocol.
Update the following A2-run paragraph ("The complete CodeTraceBench A2 run
uses independent Codex Agent workers...") to describe the direct backend
run instead (independent workers, one fixed source-only instruction, no
stage/outcome access before materialization), keeping the
representation-repair sentence pointer to the appendix.

## Edit 2 — RQ3 table and prose

In Table `tab:rq3-codetrace`, replace the "Automatic Agent (A2)" row with
"Direct Agent annotation" and values: B3 P 0.793, R 0.736, F1 0.764;
Boundary F1 0.480. Update the prose: reaches 0.764 B3 F1, improving over
recurrence by 0.101 [0.087, 0.116] and over the prior interval-protocol
Agent artifact (0.704) by 0.059 [0.048, 0.073]; boundary F1 0.480 versus
0.266 for recurrence; marks conserve 20,866 operations and 494,862,929
tokens. Keep the prior 0.704/0.394 result in one sentence as the earlier
Agent protocol for continuity (or move it to the appendix literal-detail
subsection with a pointer — your choice, but the number must remain in
the document).

## Edit 3 — abstract, intro, and any other 0.704 mentions

Abstract: "raises ordinary B$^3$ F1 against human stages from 0.541 for
raw action and 0.663 for recurrence to 0.704" -> "to 0.764". Intro
results paragraph: same replacement, and boundary mentions 0.394 -> 0.480
wherever the current-backend value is stated. Search the whole document
for remaining 0.704/0.394 occurrences and update each to either the new
value (when describing the current backend) or explicit prior-protocol
attribution (when historical). The A2 replay/cost numbers in RQ4 and the
appendix stay historical and unchanged, labeled as the prior artifact
where ambiguity exists.

## Edit 4 — RQ3/RQ4 cost sentence

Add one sentence with the direct backend's measured cost from
cost-record.md (complete 405-trajectory annotation tokens and wall time),
next to the existing annotation-cost reporting, labeled per-population.

## Validation

Compile clean; no undefined refs; thesis x3; cite keys unchanged;
write-report.md in THIS directory with before/after for every changed
number and the compile result.
