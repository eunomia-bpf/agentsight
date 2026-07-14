# Independent Outer Audit — Step 0015 WRITE Gate

## Audit metadata

- **Audited:** `2026-07-14`
- **Step:** `0015`, WRITE gate
- **Target:** the local RQ2 integration of admitted Step 0014 R337 evidence
- **Audit action:** read-only inspection of the paper source/PDF, the Step 0014
  result and reviews, the Step 0015 writing report, canonical research memory,
  the raw replay summaries, the current source diff, and the LaTeX build log
- **Verdict:** **PASS**
- **Must-fix findings:** **none**
- **Authorized next outer state:** **REVIEW_GATE**

The WRITE gate made the intended small paper update. It integrated only the
bounded, already admitted R337 result into RQ2, retained the counter-evidence
needed to interpret that result, and did not promote the reuse audit into a new
experiment, universal semantic advantage, Pareto result, matched-granularity
result, analyst-utility result, or intervention claim.

## 1. Prior-information disclosure and evidence precedence

This audit was not blind to the earlier verdicts. I read the Step 0014 full
result, its independent result review, its independent outer audit and gate
exit, all of which reported PASS, as well as the Step 0015 writing report,
which claimed a bounded integration. I treated those verdicts as assertions to
check rather than as authority. I then compared the paper directly with:

- the fresh R337 replay's `policy-target-summary.csv`;
- the fresh R337 replay's `default-target-comparisons.csv`;
- the Step 0014 independently recomputed task/source totals;
- the actual source diff from the Step 0014 paper state; and
- the rendered PDF and current LaTeX log.

No proposed wording fix was supplied in advance. The task supplied the
scientific and repository boundaries that this audit had to test.

## 2. Admitted evidence and numerical fidelity

Step 0014 authorizes one supporting secondary RQ2 statement over the existing
fixed R337 input: six labeled tasks from four public dataset families, 34,539
task-operation instances, and the existing 25% positive-recall operating
point. It is a reconstruction of pre-existing evidence, not a new independent
observation or a complete standalone answer to RQ2.

The paper now states:

> A secondary six-task analysis (34,539 task-operation instances) reaches 25%
> recall at 20.00% work and 16 groups versus fixed-session's 24.95% and 50;
> flat needs 100% work, while raw reaches 19.93% and 13 groups.

Every number is faithful to the admitted replay:

| Quantity | R337 replay / Step 0014 review | Paper | Audit |
|---|---:|---:|---|
| Task slices | 6 | 6 | exact |
| Task-operation instances | 34,539 | 34,539 | exact |
| Fixed operating point | 25% positive recall | 25% recall | same fixed target |
| Operation-stack tasks reached | 6/6 | stated as reaching the target on the six-task analysis | faithful |
| Operation-stack median work | 0.2000 | 20.00% | exact |
| Operation-stack median groups | 16.0 | 16 | exact |
| Fixed-session median work | 0.2495 | 24.95% | exact |
| Fixed-session median groups | 50.0 | 50 | exact |
| Flat work | 1.0000 | 100% | exact |
| Raw-action median work | 0.1993 | 19.93% | exact |
| Raw-action median groups | 13.0 | 13 | exact |

The paper does not add a new statistic, average incompatible metrics, or turn
the six tasks into six independent benchmark families. It uses the precise
`task-operation instances` wording required by Step 0014 rather than implying
34,539 unique source rows.

## 3. Baseline context and allowed interpretation

The three required comparison contexts remain visible and correct:

- **Fixed session:** both policies reach the six tasks, while operation stacks
  have lower median work (20.00% versus 24.95%) and substantially fewer median
  groups (16 versus 50). The paper's conclusion—reduced session
  fragmentation—is exactly the admitted result.
- **Flat:** the flat view uses one coarse group in the raw evidence but needs
  100% work at the target. The paper reports the relevant full-work endpoint
  and does not call flat a defeated fragmentation baseline.
- **Raw action:** raw is slightly stronger by both reported medians (19.93%
  work and 13 groups). The paper exposes those values immediately before its
  conclusion and therefore does not manufacture semantic dominance.

The RQ2 prose contains no Pareto claim, matched-granularity claim,
intervention claim, analyst-productivity claim, automatic-diagnosis claim, or
universal advantage claim. It explicitly ends with “without claiming
universal semantic dominance.” The word `matched` elsewhere in the paper
belongs to the pre-existing RQ4 fixed-input cost description, not this result.

The integration also remains compact: no new table, figure, benchmark,
experiment narrative, metric, cutoff, model, policy, label set, or method was
introduced. This is consistent with the user's current instruction to reuse
experiments and avoid unnecessary experimental complexity.

## 4. Preservation of the existing RQ2 evidence boundaries

The nearby page-fit edits preserve the material interpretation of all three
complete RQ2 workloads:

### AgentProcessBench

- The 1,000-trajectory / 8,509-step scope remains.
- AP remains 0.556 to 0.588, with gain 0.0315 and interval
  `[0.0151, 0.0535]`.
- The within-raw-action, subgroup-size-preserving shuffle remains, with
  `p=0.00995` and the semantic-specific interpretation.
- The 419 semantic, 259 raw-action, 1,000 session, and 8,509 per-step group
  counts remain.
- The higher AP of the finer session/per-step references remains explicit and
  is used to preclude uniform dominance.

### HINTBench

- The complete 536-test-trajectory scope remains.
- Work@80 remains 41.57% versus 46.29% raw, 57.93% native, 59.14% session, and
  100% independent step.
- The interval versus raw remains `[-0.2937, 0.0086]` and therefore crosses
  zero.
- The conclusion remains assigned to the complete profile/prefix/scorer
  pipeline rather than to the hierarchy alone.

### TraceElephant

- The complete 220-failure scope remains.
- The descriptive early result remains 19.55% versus 46.64% work at 50%
  recall, and 52.57% versus 23.79% recall at 20% work.
- The prose still labels this region descriptive.
- The large tied tier, full work at prospective 80% recall, and interval that
  crosses zero all remain explicit.

The new secondary paragraph does not overwrite any of these boundaries. It
adds a recurring-versus-session compactness result after them and keeps raw
action as the immediate counterpoint.

## 5. Scientific-contract and narrative-drift audit

The source diff from the Step 0014 paper state modifies only
`docs/paper/main.tex` and its rebuilt `main.pdf`. In `main.tex`, the substantive
edits are confined to local compression inside the RQ2 subsection, the admitted
R337 sentence, and page-fit compression of the Conclusion. There is no diff in
the abstract, introduction, background/motivation, Design, Implementation,
Evaluation setup, RQ statements, RQ1, RQ3, RQ4, related work, bibliography, or
figures.

The author-fixed thesis remains verbatim in the paper:

> **Agent observability needs profiling, not only debugging.**

The paper retains exactly the same four explicit questions:

1. RQ1: Does semantic profiling improve resource attribution?
2. RQ2: Does profiler output correspond to real problems?
3. RQ3: How accurate are the tags?
4. RQ4: What is the profiling cost?

`docs/idea-story.md` remains unchanged and retains its permanent Initial
Narrative, two-object operation/operation-stack model, restored thesis, four
fixed RQs, and instruction that experiments may improve evidence but may not
silently weaken or replace the fixed hypothesis. `docs/user-instruction.md`
also remains unchanged and includes the current reuse/simplicity instruction.

The Conclusion was compressed to recover page legality, but it preserves all
four RQ result roles and ends on the unchanged central thesis: scoped lineage
and mass preservation for RQ1, problem concentration across the three public
RQ2 benchmarks, held-out boundary fidelity for RQ3, and construction cost for
RQ4. Its final clause still presents cross-trajectory semantic profiling as a
complement to run-local debugging. It does not introduce the R337 result as a
new headline contribution or alter the abstract, introduction, or design
story.

## 6. PDF, page legality, and build health

Direct PDF inspection confirms:

- the document is US Letter (`612 x 792` points);
- the PDF has nine pages;
- all manuscript prose, including the complete Conclusion and its final
  sentence, ends on page 7;
- page 8 begins with `References`; and
- pages 8 and 9 contain references only.

The rendered RQ2 paragraph is fully visible on page 6, including the six-task
scope, 34,539 task-operation count, 25% target, fixed-session comparison,
flat/raw context, and non-universal conclusion.

The current LaTeX log contains no LaTeX error, fatal/emergency stop, overfull
box, undefined citation, or undefined reference. The only reported layout
warnings are pre-existing/non-critical underfull boxes. The rebuilt PDF is
therefore suitable for this gate transition.

## 7. Protected repository boundaries

The current source diff contains no change to the canonical
`docs/agentpprof-paper/` submodule or its recorded pointer. Filesystem checks
also find no submodule or shared academic-writing skill file modified after
the Step 0015 gate began. No shared skill, repository instruction, experiment
script, raw artifact, canonical memory file, or dataset was changed by this
WRITE gate.

The writing node itself performed no Git persistence action. This audit made no
paper, canonical-memory, submodule, shared-skill, or Git-state change; this
Markdown report is its only repository write.

## Gate-exit decision

**PASS, with zero must-fix findings.** The paper contains the one admitted
R337 consequence at the right level of strength; its numbers and scopes are
faithful; the fixed-session, flat, and raw-action context is intact; the
AgentProcessBench, HINTBench, and TraceElephant limitations remain visible;
the thesis, four RQs, abstract, introduction, design, and story have not
drifted; and the paper remains page-legal and cleanly built.

The WRITE gate may transition to **REVIEW_GATE**. Any broader objection about
novelty or paper-level decision value remains a later whole-paper review issue,
not a defect in this bounded writing node.
