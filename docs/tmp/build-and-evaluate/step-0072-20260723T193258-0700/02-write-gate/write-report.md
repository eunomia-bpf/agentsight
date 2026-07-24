# Step 0072 WRITE Gate Report

**Timestamp:** 2026-07-23T20:28:00-07:00  
**Parent:** Step 0072 / EXPERIMENT Gate / Experiment 001  
**Objective:** Integrate the independently verified RQ2 local-first experiment
without changing the paper's thesis, four RQs, contribution scope, or story.

## Inputs and provenance

- The complete experiment plan and two plan reviews in
  `../experiment-001/`.
- Full-population raw outputs and the independent reconstruction in
  `../experiment-001/independent-result-review.md`.
- The complete paper source under `docs/paper/`.
- The complete author-intent log in `docs/user-instruction.md`.
- The complete narrative history and invariants in `docs/idea-story.md`.
- The current evidence ledger in `docs/evaluation.md`.

The write did not introduce or recompute any experimental number. The table,
intervals, query counts, and scope qualifiers all come from the independently
verified full run.

## Method

The revision used a narrow evidence-first pass:

1. retain the fixed RQ2 question and all complete public populations;
2. replace the previous grouping-only comparison with the stronger
   local-first, information-matched design;
3. expose the local-only, matched raw+evidence, and AgentProf-only baselines in
   one table;
4. state both the positive result against local-only and the non-result against
   matched raw+evidence;
5. connect the supported result to the existing design principle—profiling
   complements local diagnosis and retains source evidence—without claiming
   semantic-prefix ranking superiority;
6. correct the unrelated but material A2 provenance error discovered during
   the evidence audit.

No title, abstract, introduction, motivation, contribution list, thesis, RQ,
section structure, or conclusion was rewritten in this gate.

## Results

The RQ2 subsection now reports standard per-query AP/MAP over all 1,756
trajectories and 27,346 operations:

| Workload | Local+AgentProf | Local+Raw+Evidence | Local | AgentProf only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .894 | .893 | .863 | .791 |
| HINTBench | .517 | .518 | .411 | .432 |
| TraceElephant | .326 | .324 | .209 | .259 |

The prose records that Local+AgentProf improves over Local by .031
[.024,.039], .107 [.093,.120], and .117 [.088,.148]. It also records that all
three intervals against the information-matched raw+evidence baseline include
zero. The admitted result is therefore deliberately two-part:

- an AgentProf profile adds clear ranking information to operation-local
  diagnosis on all three complete populations; and
- this adaptive experiment does not show that a semantic-operation prefix
  ranks targets better than a raw-action prefix when both preserve identical
  source evidence.

The same evidence and boundary are synchronized into `docs/evaluation.md`,
`docs/background-related-work.md`, and an evidence-only entry in
`docs/idea-story.md`.

The CodeTrace A2 implementation paragraph now names its actual provenance:
independent Codex Agent workers under one fixed source-only instruction,
followed by root merge and validation. It no longer attributes the complete A2
run to the incomplete Qwen3.6-27B experiment.

## Validation

- `python3 -m py_compile script/rq2_current_agent_local_first.py`: PASS.
- `python3 -m unittest script/test_rq2_canonical_tag_compare.py`: 7 tests PASS.
- Full scorer replay over all three populations: PASS.
- Independent raw-input reconstruction of every AP, MAP, paired difference,
  bootstrap draw, join count, and predecessor result: exact match.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: PASS,
  12-page PDF.
- Visual inspection of the revised table and surrounding page: no clipping,
  overlap, or unreadable column.

## Paper and claim impact

This write strengthens the evidence for the existing RQ2 answer without
changing the story. It replaces a weaker comparison with a fairer test of what
the profile contributes after a local diagnostic signal exists. The matched
raw baseline also prevents the paper from attributing source-evidence value to
semantic names.

The strongest remaining limitation is explicit: the current RQ2 experiment is
adaptive evidence on already observed populations. A future RQ2 experiment
would need a genuinely different user decision or untouched population, not
another score, cutoff, or name retuning on these workloads.

## Alternatives and decision

Rejected alternatives were:

- keeping only the favorable local-only comparison, because that would hide
  the strongest information-matched baseline;
- interpreting the matched-raw tie as a reason to shrink the thesis, because
  RQ2 tests one downstream ranking consequence rather than the complete
  profiling abstraction;
- opening another RQ2 benchmark immediately, because the current cycle already
  answers its tested hypothesis and further benchmark substitution would not
  resolve the matched-information mechanism question.

The decision is to preserve the ambitious thesis, report the complete result,
and route the next experiment to a different fixed RQ.

## Tree, search, and project-memory updates

- The evidence tree now distinguishes profile-plus-local complementarity from
  semantic-prefix target-ranking superiority.
- The closest-work ledger now treats Hodoscope, TraceProbe, AgentRx,
  AgentLocate, and related diagnostic systems as adjacent product/design
  precedents rather than pretending they expose a directly comparable
  operation-level MAP output.
- The project memory records that Step 0072 is evidence-only and does not
  authorize narrative change.

## Completion assessment, uncertainty, and next node

The WRITE inner loop is complete. All experiment results admitted to the paper
are independently verified and the visual build is clean. The unresolved
scientific uncertainty is not a writing defect: semantic names have not shown
extra target-ranking value over raw names when source evidence is matched.

Next node: whole-paper REVIEW Gate, followed by the outer audit. If that review
finds no Step 0072 blocker, transition to a separate RQ3 experiment rather than
continuing to tune RQ2.
