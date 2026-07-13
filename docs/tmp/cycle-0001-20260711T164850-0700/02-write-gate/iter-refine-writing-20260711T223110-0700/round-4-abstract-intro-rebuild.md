# Round 4: Abstract and Introduction Rebuild

## Node identity

- **Started:** 2026-07-11 23:26:39 -0700
- **Completed:** 2026-07-11 23:29:39 -0700
- **Cycle/Gate:** `cycle-0001-20260711T164850-0700` / `WRITE_GATE`
- **Parent:** `round-3-logic-flow.md` (`PASS`)
- **Entry paper:** 9 pages; seven content pages; References begins page 8
- **Entry invariants:** four fixed RQs; three target contributions; 59 citation commands

## Objective and sources

This round uses `rewrite-paper-section` in its mandatory
Abstract/Introduction mode. The main agent read the complete
`rewrite-paper-section/SKILL.md`, `references/abstract-intro-revision.md`,
and `references/abstract-intro-structure.md`, then reread the paper body as
the source of truth. Project-memory documents were intentionally not used
to source opening claims or numbers. The current Abstract is one LaTeX
paragraph, nine sentences, and approximately 235 words; the Introduction
including contributions is approximately 679 words.

The scientific meaning of RQ1--RQ4, all quantitative values, citations,
and the three ambitious target contributions are read-only. This writing
round may clarify status but may not repair missing evidence by narrowing
the thesis.

## Mapping diagnosis before edits

### Abstract sentence map

| Sentence | Current role | Target intro source | Diagnosis |
|---|---|---|---|
| S1 | Background | paragraph 1 | Correct. |
| S2 | Problem | paragraph 2 | Correct. |
| S3 | Root cause | paragraph 3 | Correct and warranted for this mechanism paper. |
| S4 | Existing solutions | paragraph 4 | Correct, although the corresponding intro has more concrete tool categories. |
| S5 | Insight | paragraph 5 | Correct and states the dominant thesis independently of the artifact. |
| S6 | Realization challenges | paragraph 5b | Correct, but the intro currently compresses all three challenges into one sentence. |
| S7 | This paper/system | paragraph 6 | Correct in content, but mixes model, achieved substrate, and proposed navigator in one long sentence. |
| S8 | Methodology | paragraph 6 | The Abstract contains the fair-comparison method, but the current intro paragraph does not state it explicitly; strict correspondence is incomplete. |
| S9 | Current results/status | paragraph 6 | Correct evidence boundary, but dense; it must remain one result sentence in the Abstract. |

### Introduction paragraph map

| Current paragraph | Current role | Target role | Planned action |
|---|---|---|---|
| paragraph 1 | Background | Background | Split the long first sentence so the paragraph has a clear topic sentence and a separate two-layer prerequisite; retain the workload-growth sentence. |
| paragraph 2 | Problem | Problem | Preserve content and quantitative example; tighten only if needed after recompilation. |
| paragraph 3 | Root cause | Root cause | Keep as a separate required paragraph because the insight directly answers the stable-identity/execution-tree mismatch. |
| paragraph 4 | Existing solutions | Existing solutions | Keep the focused alternatives and precise missing capability. |
| paragraph 5 | Insight/model | Insight | Keep the thesis before the artifact; tighten the link from recurrence to a diagnostic index. |
| paragraph 5b | Challenges | Challenges | Expand the single compound sentence into an opening plus three explicit challenges: frozen transferable identity, lossless/nonduplicating inheritance, and fair query-independent comparison under full budgets. All are already in Design/Evaluation. |
| paragraph 6 | This paper + method + results | This paper | Rebuild top-down: system and achieved/proposed boundary; one-for-one response to challenges; decisive comparison method; current positive/negative/proxy evidence; joint unmet obligation. Preserve the figure reference and every number. |
| paragraph 7 | Contributions | Contributions | Preserve the three-item scope and order. Keep target-status wording until experiments establish achieved contribution voice. |

## Causal-chain diagnosis

The current order already follows background -> problem -> root cause ->
existing limitations -> insight -> challenges -> system -> contributions.
The remaining jumps are local rather than structural:

1. paragraph 5b names three hard requirements without giving each its own
   sentence, making the one-for-one answer in paragraph 6 hard to inspect;
2. paragraph 6 reports outcomes without first stating the decisive matched
   comparison that appears in Abstract S8 and Evaluation;
3. current implemented candidate profiles and the proposed frozen navigator
   need an even cleaner grammatical boundary;
4. Abstract S7 must be derived from the rebuilt system paragraph rather than
   independently mixing model, implementation, and proposal status.

## Reorganization plan

The optional root-cause and challenge paragraphs remain: both are warranted
because the contribution is a mechanism whose insight answers a structural
identity/tree mismatch and whose novelty depends on satisfying three
nontrivial realization conditions. No paragraph is moved, merged, or removed.
Edits proceed paragraph by paragraph. The Introduction is rebuilt first;
the Abstract is then derived last as exactly nine role sentences in the same
order. No citation, number, technical mechanism, or evidence TODO may be
deleted. The figure remains illustrative rather than RQ evidence.

## Applied edits and completion evidence

### Introduction rebuild

- **Background:** split the original compound opening into a domain topic
  sentence and a separate two-layer prerequisite sentence. The paragraph now
  contains three sentences without adding facts.
- **Problem, root cause, existing solutions, and insight:** retained their
  already-correct paragraph boundaries and order. Each has a topic sentence,
  and the insight directly answers the stable-identity/execution-tree cause.
- **Challenges:** replaced one compressed compound sentence with a topic
  sentence followed by the three body-backed obligations: frozen transfer,
  exact inheritance, and query-independent fair comparison.
- **This paper:** rebuilt the paragraph from the artifact boundary outward.
  It now first identifies AgentProf and the implemented substrate, then maps
  current and completed-system mechanisms to the challenges, states the
  matched-policy methodology, reports positive, negative, and proxy evidence,
  and closes with the joint unmet thesis obligation. The implemented candidate
  profiles remain grammatically separate from the future frozen identity and
  navigator.
- **Contributions:** retained all three target contributions in model,
  system/navigation, and empirical-characterization order. No contribution was
  narrowed or removed.

### Abstract derivation

The Abstract was regenerated last from the rebuilt Introduction. It is one
LaTeX paragraph, nine sentences, and approximately 223 prose words (the 225-word
`detex` count includes two environment labels). Its order is exactly:
background, problem, root cause, existing limitations, insight, challenges,
system/status, methodology, and current result/status. Abstract S7 and S8 now
use the same candidate-profile, completed-system, matched-policy, pointwise,
and exact-bundle terms as Introduction paragraph 6. S9 preserves the 36.7% and
84.4% values, the held-out negative result, and all three central unestablished
obligations.

### Self-check

The causal chain passes end to end: accumulated cross-run workloads create a
fragmentation problem; missing stable identity and execution-only nesting cause
it; existing trace/aggregation tools do not establish the missing inheritance;
stable recurrence supplies the insight; the three challenges explain why it is
not a trivial regrouping; AgentProf's substrate and planned mechanism answer
those challenges; the contributions deliver the model, mechanism target, and
decisive characterization. No term is required before introduction, and the
Abstract introduces no claim, number, or mechanism absent from the corresponding
Introduction paragraph.

A fresh `make` and final `pdflatex` pass produced a 9-page PDF with seven content
pages and References beginning on page 8. Page 1 and page 2 were rendered and
visually inspected: the title, one-paragraph Abstract, Introduction flow, page
break, contribution list, and transition to Background are intact. The source
still contains 59 citation commands and four RQ subsections; the log contains no
undefined citation or reference. The same two pre-existing overfull boxes remain
for later local language/layout repair.

### Open items and next node

No opening-structure defect remains. The explicit evidence obligations remain
scientific blockers rather than writing defects. Round 5 next performs a fresh
paper-consistency audit across architecture, claims, figures, contributions,
RQ wording, numbers, and the newly aligned opening and conclusion.
