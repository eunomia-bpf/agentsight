# Step 0048 — Evaluation-Protocol Search, Minimal Paper Repair, and Heterogeneous Full Review

**Started:** 2026-07-19 18:57:09 -0700
**Step report completed:** 2026-07-19 19:40:00 -0700
**Outer route:** EXPERIMENT triage → WRITE → REVIEW
**Paper:** `docs/paper/`
**Branch:** `research/semantic-flamegraph-artifacts-v2`
**Starting revision:** `89c77e8bd`
**Status:** inner work complete; awaiting independent outer audit

## User instructions carried into this step

The current requests were appended verbatim to `docs/user-instruction.md`:

- inspect the specified Claude session and determine the next action;
- search for stronger related work and better evaluation methods;
- continue iterating and obtain complete reviews from different models,
  including Grok.

Standing authority remained unchanged:

- preserve the thesis **“Agent observability needs profiling, not only
  debugging.”**;
- preserve the four RQs: attribution, problem correspondence, tag accuracy,
  and cost;
- do not narrow the contribution merely because a reviewer attacks a strong
  claim;
- prefer complete real workloads, released signals, standard citable metrics,
  and published protocols over small handmade tests;
- do not hide scientific uncertainty, but do not wait for human intervention;
- do not switch branches;
- do not touch `docs/agentpprof-paper/`;
- do not modify the shared skills repository in this paper iteration.

## Entry state

- All four fixed RQs had evidence-backed scoped answers in
  `docs/evaluation.md`.
- The paper used standard ordinary B-cubed, boundary F1, V-measure, macro-F1,
  accuracy, AP, and MAP as its active scientific metrics.
- The most recent baseline availability audit had already closed a proposed
  common process/phase baseline because HINTBench alone has a natural phase
  field; AgentProcessBench's phase is project-derived and TraceElephant has no
  published phase field.
- The starting PDF compiled in nine pages.
- No experiment was running at step entry.

## EXPERIMENT_GATE node: better-evaluation search and admission decision

### Question

Is there a stronger released evaluation protocol that can test RQ2 without
changing the four RQs, inventing a localizer, loading gold targets into the
profile score, or repeating a weak benchmark swap?

### Search performed

Primary papers, official repositories, and released artifacts were inspected
for four recent evaluation directions:

1. **MP-Bench** — 289 failed multi-agent executions, 121 configurations, three
   expert perspectives, and graded nDCG evaluation;
2. **AgentLens / Lucky Pass** — 2,614 OpenHands trajectories and
   context-sensitive intent-stage analysis;
3. **ProcBench** — 200 annotated trajectories over AndroidBench,
   TerminalBench, and SWE-bench Verified;
4. **AgentLocate** — responsible-agent and earliest-decisive-step localization.

The full source and protocol analysis is recorded in:

`literature-20260719T185709-0700/source-and-evaluation-review.md`.

### Decision

No experiment was admitted.

MP-Bench provides the strongest future protocol because graded nDCG is standard
and its three perspectives directly challenge single-target localization. Its
repository releases annotations and links to source logs, but it does not
release fixed target-blind prediction/localizer outputs. Using the gold expert
annotations to score AgentProf groups would leak the target; writing a new
localizer would create a second mechanism and a handmade experiment. AgentLens
states that its release is planned but its named repository is not currently
available. ProcBench and AgentLocate add useful positioning but do not provide
an immediately reusable fixed signal for the current RQ2 grouping question.

The reopen condition is explicit: admit MP-Bench when a released target-blind
prediction path or another fixed external diagnostic signal becomes available.

## WRITE_GATE node: source-backed minimal repair

### Canonical literature update

`docs/background-related-work.md` now records and verifies MP-Bench, AgentLens,
ProcBench, and AgentLocate, including their populations, metrics, closest-claim
relationship, and current artifact availability.

`docs/paper/references.bib` now contains verified entries for those four works.
The active paper cites MP-Bench in the diagnosis/localization positioning;
uncited verified entries remain available for a future longer version or
rebuttal rather than forcing every source into a nine-page manuscript.

### Minimal paper corrections after the full reviews

Only four scientific clarifications were accepted:

1. **RQ2 signal timing.** The paper now states that the matched views use the
   same precomputed benchmark judge/localizer predictions and that predictions,
   group scores, profiles, fields, and scoring rules are fixed before
   human/scorer target labels are loaded.
2. **Elapsed time.** The paper now states that span time is elapsed rather than
   active CPU time and may include idle or user wait.
3. **Tagger roles.** The RQ3 task-family evaluation explicitly distinguishes
   its fixed Qwen3.6-27B backend from the 3B CLI backend.
4. **Pivot Tracing.** The paper now cites and positions Pivot Tracing as a
   dynamic cross-causal-event selection and grouping precedent.

These changes preserve the thesis, the four RQs, every reported number, the
operation/operation-stack model, and the positive scoped conclusions.

### Page-budget handling

The first complete build reached ten pages because the stronger publication
reference and clarification text displaced five bibliography lines. The repair
did not delete scientific claims. It removed redundant active citations to
WebGraphEval, Phoenix, and Laminar Signals from the nine-page paper while
retaining their verified entries and analysis in the canonical literature map
and bibliography source. The resulting active citation set prioritizes Pivot
Tracing and MP-Bench.

### Build verification

The full `pdflatex → BibTeX → pdflatex → pdflatex`, followed by one settling
`pdflatex` pass, succeeds. The final PDF is nine pages. The build log contains:

- no undefined citation;
- no multiply defined label;
- no overfull box;
- no LaTeX error.

`git diff --check` passes.

## REVIEW_GATE node: two independent complete reviews

### Grok 4.5

Grok completed the full four-stage review and wrote:

- `milestone-review-001/grok-4.5/01-blind-full-read.md`
- `milestone-review-001/grok-4.5/02-external-search.md`
- `milestone-review-001/grok-4.5/03-full-reread-assessment.md`
- `milestone-review-001/grok-4.5/04-final-verdict.md`

Its final verdict is **Reject**, confidence 0.82. Its main case is that the paper
lacks a same-claim process/phase or hierarchical-rollup baseline and a
profile-to-decision outcome experiment.

### Claude Opus 4.8

Claude completed the same protocol and wrote:

- `milestone-review-001/claude-opus/01-blind-full-read.md`
- `milestone-review-001/claude-opus/02-external-search.md`
- `milestone-review-001/claude-opus/03-full-reread-assessment.md`
- `milestone-review-001/claude-opus/04-final-verdict.md`

Its final verdict is **Reject / AAAI score 3 trending 4**, confidence 0.85. Its
main case is that the system conjunction is tested across decomposed
populations, the automatic constructor lacks another untouched population,
RQ2 signal timing was underspecified, construction cost excludes tag
generation, and Pivot Tracing/process-mining/OLAP positioning was absent.

Both reviewers were read-only for paper, code, canonical documents, and Git.
They did not read one another's reports.

### Root scientific disposition

Every finding is dispositioned in:

`milestone-review-001/root-synthesis/reviewer-disposition.md`.

The root accepted the four writing clarifications listed above and rejected the
new experiment proposals as current blockers for the following reasons:

- Step 0046 already demonstrates that no published information-matched common
  phase/process baseline exists across all three RQ2 workloads.
- The proposed TF-IDF hierarchy, external-system imitation, budget policy, and
  reader protocol would be project-designed experiments rather than direct
  reuse of published evaluation.
- A downstream intervention adds an outcome contract beyond the fixed four
  RQs; the available Step 0019 protocol uses a custom top-three reader metric
  that the user explicitly excluded from the paper.
- The paper already scopes constructor evidence to named populations and labels
  its reused constructor evidence as post-hoc.
- RQ4 explicitly defines the 1.17-second result as fixed-field offline profile
  construction and excludes field/tag generation.
- Component evaluation across appropriate real populations is valid; every
  backend need not run on one universal corpus.

The two Reject verdicts remain visible and are not rewritten as acceptance.
They establish a likely reviewer-perception risk, while the root disposition
explains why eliminating every objection would produce unfair or out-of-scope
experiments.

## Files changed by Step 0048

Canonical files:

- `docs/background-related-work.md`
- `docs/paper/main.tex`
- `docs/paper/references.bib`
- `docs/paper/main.pdf`
- `docs/user-instruction.md`

Step provenance:

- `docs/tmp/writing/step-0048-20260719T185709-0700/`

Explicitly untouched:

- `docs/agentpprof-paper/`
- shared `academic-writing-skills` repository
- source code and experiment scripts

## Paper-level state after the step

- Thesis: unchanged.
- RQ1–RQ4: unchanged.
- Reported experimental numbers: unchanged.
- Story: unchanged.
- New active scientific context: MP-Bench and Pivot Tracing.
- New admitted experiment: none.
- Best future RQ2 evaluation: MP-Bench graded nDCG when a fixed target-blind
  signal becomes reusable.
- Model-review state: two complete independent Reject reviews with a detailed
  root disposition; no claim of model consensus acceptance.

## Recommended next outer transition

Proceed to an independent outer audit of this step. If the audit finds no
source-fidelity, state-machine, or unauthorized-scope defect, commit and push
the bounded literature/paper/review update. Do not open another benchmark or
invent another baseline solely to satisfy the two model verdicts. The next
scientific experiment should be triggered by a newly available published
target-blind signal capable of changing a paper-level RQ answer.
