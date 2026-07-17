# Round 4 — Abstract and Introduction

**Started:** 2026-07-16T21:55:21-07:00

**Parent:** Step 0035 `WRITE_GATE / EVIDENCE INTEGRATION`

**Skill:** `rewrite-abstract-intro`, invoked serially by
`iter-refine-writing`.

**Objective:** Rebuild the paper opening as one causal argument while
preserving the canonical thesis, four RQs, semantic operation stack model,
algorithm, citations, experimental populations, comparisons, numbers, and
evidence boundaries. No body section, experiment, or Git state may change in
this round.

## Source of Truth

Per the skill, the current complete paper body—not project planning documents—
is the source of truth. The current Abstract and Introduction were mapped
against the current Design, Implementation, Evaluation, Scope, Related Work,
and Conclusion before any edit. The source has 52 distinct citation keys; no
citation may be removed.

## Existing Introduction Mapping

| Current paragraph | Current role | Diagnosis | Target |
|---|---|---|---|
| ¶1 | Background/context | Correct order and content; only two sentences, but both establish the cross-layer workload and multi-run setting. | Keep as ¶1; tighten no claim. |
| ¶2 | Problem | Correct: cross-run quality/safety/cost questions, then the cost of manual or per-run inspection. | Keep as ¶2 with a stronger topic sentence only if wording can be reused. |
| ¶3 | Structural root cause | Necessary for this mechanism paper and causally answers why traditional profiling does not transfer directly. It is seven short sentences and repeats `lack`. | Compress to 4–5 sentences while retaining stable-identity and runtime-nesting causes and both profiler citations. |
| ¶4 | Existing solutions | Correct and focused, but its final sentence must remain causally tied to both missing linkage and selectable semantic aggregation. | Keep as ¶4. |
| ¶5 | Insight/model | Correct dominant thesis, but eight sentences mix the transferable profiling insight with detailed model definition. | Keep as ¶5; compress to 4–5 sentences and ensure the model answers ¶3 rather than appearing as an adjacent invention. |
| ¶6 | This paper/system | Correct artifact and two mechanisms. The stable-tag answer is explicit; the hierarchy answer is present but can be made parallel. | Keep as ¶6; make the two mechanism→cause answers syntactically parallel. |
| ¶7 | Evaluation/results | Correct populations and values. Standard B-cubed and MAP are primary; token-weighted B-cubed is a sensitivity analysis. | Keep as ¶7; preserve every value and explicit evidence scope. |
| ¶8 | Contributions | Correct three concrete deliverables in design/system/evaluation order. | Keep as ¶8; preserve deliverables and values. |

The optional structural-cause paragraph is warranted: the contribution is a
model and mechanism whose insight directly answers the absence of stable
semantic identity and runtime nesting. A separate fabricated challenges
paragraph is not warranted; the same two difficulties are already the root
cause and are answered one-for-one by intent attribution and stack
construction.

## Existing Abstract Sentence Mapping

| Sentence | Current role | Diagnosis |
|---|---|---|
| 1 | Background | Correct. |
| 2 | Problem | Correct. |
| 3 | Root cause | Correct. |
| 4 | Existing-solutions limitation | Correct. |
| 5 | Thesis | Correct exact canonical sentence. |
| 6 | This paper/system | Correct. |
| 7 | RQ1 result plus CodeTraceBench attribution result | Correct evidence, but occupies the methodology slot and mixes two result families. |
| 8 | RQ2 and RQ3 results | Correct evidence, but creates a second results sentence. |
| 9 | RQ4 result | Correct evidence, but creates a third results sentence. |

The abstract has the right causal prefix but lacks a distinct methodology
sentence. Its last three sentences are result lists rather than an
introduction-in-miniature. It also needs to make explicit that ordinary
B-cubed is the primary standard partition metric and token weighting is a
sensitivity result, without adding terminology absent from the Introduction.

## Reorganization Plan

1. Edit Introduction ¶3 as one compact cause chain: classic profilers rely on
   stable code identity and runtime nesting; agent responsibility is semantic,
   natural-language intent lacks identity, and events lack nesting.
2. Edit ¶5 so the exact thesis introduces the transferable method and the two
   model components answer those causes directly. Retain all established
   terms and Figure reference.
3. Edit ¶6 so intent attribution supplies stable semantic identity and stack
   construction supplies query-time hierarchy. Do not add a new mechanism.
4. Preserve ¶7's complete numerical evidence. Clarify the standard-primary
   versus sensitivity distinction using only wording already established in
   Evaluation.
5. Derive an eight-sentence abstract from the resulting eight introduction
   roles: background, problem, cause, existing limitations, thesis, system,
   evaluation methodology, and results. Consolidate, rather than delete, all
   existing result values.
6. Compile and check abstract↔intro correspondence, causal links, citations,
   numbers, terminology, page count, and the read-only submodule.

## Preservation Ledger Before Edits

- Exact thesis: `Agent observability needs profiling, not only debugging.`
- Four paper-level RQs remain unchanged in Evaluation.
- Opening citation keys remain a subset of the same 52 paper keys.
- Abstract populations: 20 real Codex tasks, 405 CodeTraceBench trajectories,
  three complete localization benchmarks, 287 OSWorld-Human sessions, and
  27,765 cost operations.
- Abstract values: 100.0%, 96.6%, 1,629/1,629, 1,520, 0.541→0.649,
  0.076–0.085, 0.680/0.786, 0.645/0.678, 0.739/0.816, and 1.17 s.
- Introduction-only values and intervals remain read-only, including
  0.108 [0.087, 0.129], the three MAP pairs and query counts, 464.5 MiB,
  18.2%, and 1.3%.

Edits may now proceed paragraph by paragraph under this plan.

## Applied Introduction Reorganization

1. **¶1 Background:** retained unchanged. Its two sentences are compact but
   complete: cross-layer agent activity and the accumulating multi-run setting.
2. **¶2 Problem:** retained unchanged. It names the quality, safety, and cost
   questions before the expense of manual and per-run judging.
3. **¶3 Structural cause:** compressed seven short sentences into five. The
   paragraph now begins with profiling's cross-run aggregation method, then
   states its two missing prerequisites in agent trajectories: stable semantic
   identity and runtime nesting. It ends with the exact two requirements that
   the model must supply.
4. **¶4 Existing solutions:** retained unchanged. Its limitations now follow
   directly from the two requirements in ¶3.
5. **¶5 Insight/model:** compressed eight sentences into five without changing
   the exact thesis. The transferable profiling method is stated before the
   semantic operation stack model; operations supply uniform additive records,
   and selected operation-stack fields supply query-time hierarchy.
6. **¶6 System:** made the two mechanisms parallel. Intent attribution supplies
   stable semantic identity; stack construction supplies hierarchy without
   runtime call nesting. No new mechanism or claim was introduced.
7. **¶7 Results:** retained all populations, comparisons, values, intervals,
   and citations. Ordinary per-operation B-cubed is the primary partition
   result, token-weighted B-cubed is explicitly a secondary sensitivity
   analysis, and MAP is identified as the standard ranking measure.
8. **¶8 Contributions:** retained unchanged in model/system/evaluation order.

## Abstract Derivation

The former nine-sentence abstract had the correct causal prefix but used its
last three slots as independent result lists. It is now an eight-sentence,
241-word miniature of the Introduction:

| Abstract sentence | Introduction source | Role |
|---|---|---|
| 1 | ¶1 | Background and domain |
| 2 | ¶2 | Cross-run operational problem |
| 3 | ¶3 | Stable-identity and hierarchy root cause |
| 4 | ¶4 | Existing-tools limitation |
| 5 | ¶5 | Exact canonical thesis |
| 6 | ¶6 | AgentProf and the semantic operation stack model |
| 7 | ¶7 | Evaluation populations and conditions |
| 8 | ¶7 | Complete key results |

The last three former result sentences were consolidated, not discarded.
Every preserved result remains in sentence 8, separated by semicolons; the
new sentence 7 provides the previously missing evaluation methodology. The
CodeTraceBench text now says that ordinary B-cubed is measured against its
human stage partitions, while token weighting is secondary. It does not call
B-cubed the official CodeTraceBench faulty-step metric.

## End-to-End Logic Check

The argument now reads continuously:

1. agents generate cross-layer, accumulating trajectories;
2. teams need cross-run quality, safety, and cost answers;
3. profiling offers the aggregation method but assumes stable identity and
   runtime nesting, which agent trajectories lack;
4. tracing and metadata dashboards do not supply the missing linked,
   selectable semantic profiles;
5. profiling therefore transfers through semantic responsibility and
   query-time hierarchy;
6. AgentProf realizes those two requirements through intent attribution and
   stack construction;
7. the evaluation tests source linkage, partition attribution, problem
   localization, grouping/tag fidelity, and construction cost;
8. the contributions deliver the model, system, and evidence.

No paragraph presupposes a mechanism or term that is introduced later. No
abstract claim lacks a corresponding Introduction statement.

## Preservation and Build Verification

- `make`: pass.
- PDF: 9 pages, US letter, official `aaai2027` submission style.
- Abstract: 241 words, 8 sentences, within the 200–300 word full-paper rule.
- Every abstract number occurs in the Introduction; none was invented.
- Exact fixed thesis: 3 occurrences, unchanged.
- Explicit paper-level RQs: exactly 4, unchanged.
- Distinct paper citation keys: 52, equal to the pre-writing baseline.
- Final `main.log`: no `Warning`, `Overfull`, `undefined`, or `Error` match.
- `git diff --check`: pass.
- Rendered first page inspected: title, abstract, and opening columns remain
  legible with no collision or overflow.
- `docs/agentpprof-paper`: clean and untouched.
- No Git operation was performed by this writing skill.

## Open Items and Next Node

No abstract/Introduction writing defect remains from this round. The known
literal-phase evidence gap is scientific, not an opening-rewrite license; it
remains recorded for the outer gate without narrowing RQ3. Round 5 must now
audit terminology, information flow, figure/table consistency, claim/number
consistency, and source ownership across the complete paper.

**Completed:** 2026-07-16T21:59:09-07:00
