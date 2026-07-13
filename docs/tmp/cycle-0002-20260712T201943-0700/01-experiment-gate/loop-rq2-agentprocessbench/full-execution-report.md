# AgentProcessBench RQ2 FULL execution report

**Executed:** 2026-07-13T05:46:00-07:00  
**Outer gate:** EXPERIMENT  
**Plan:** `experiment-plan.md`, Revision 3  
**REAL PREFLIGHT review:** PASS, zero must-fix  
**Execution status:** **VALID**  
**Scientific verdict:** **INCONCLUSIVE**

## Verdict scope

This is the only scientific verdict for the predeclared AgentProcessBench
construction. It evaluates one tested hypothesis inside fixed RQ2; it does not
answer all of RQ2 and cannot change the paper-level positive hypothesis,
author-fixed thesis, canonical story, or four RQs.

`INCONCLUSIVE` is not `CONTRADICTED`. The complete result contains specific
positive evidence for semantic localization precision, but the second
co-primary inspection-work interval includes zero. Because the hypothesis was
predeclared as conjunctive, the program does not relabel partial support as
`SUPPORTED`.

No result from this run has been inserted into the paper.

## Exact command and completion

```bash
python3 script/agentprocessbench_profile_eval.py full \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2/full \
  --permutations 200 --bootstraps 10000 \
  --max-bootstrap-attempts 50000 --seed 4204
```

The command exited successfully after approximately eighteen seconds. It met
every full-population completion condition:

| Item | Required | Observed |
|---|---:|---:|
| Families | 4 | 4 |
| Tasks | 200 | 200 |
| Trajectories | 1,000 | 1,000 |
| Assistant operations | 8,509 | 8,509 |
| Released judge models | 20 | 20 |
| All-null judge steps | 3 | 3 |
| Fixed result views | 5 | 5 |
| Matched shuffles | 200 | 200 |
| Valid query-cluster bootstraps | 10,000 | 10,000 |
| Maximum bootstrap attempts | 50,000 | 10,000 examined |

No bootstrap draw lacked a harmful positive in any family, so zero draws were
discarded. All output artifacts use seed 4204.

## Source, label, and released-risk boundary

The official source remained commit
`0a42606b178a8c69d40c5765dc05c342f921e578`. The complete operation counts were
2,590 BFCL, 1,628 GAIA dev, 734 HotpotQA, and 3,557 tau2.

The visible converter used task text, message roles, tool calls, and step order
only. It clustered all 200 task descriptions into seven intent tags using the
fixed existing AgentProf implementation. It checked label keys without reading
label values. The released-risk loader then joined exactly 20 official judge
slots to every operation; 6,914 steps had 20 non-null predictions, all but the
three predeclared GAIA all-null steps had at least 15, and the three all-null
steps received risk 0.5.

Only after every fixed profile passed did the separate scorer loader read the
8,509 human-label values. Operation IDs matched exactly across projection,
released risks, profile assignments, and labels.

## Five AgentProf views and conservation

The exact binary was `agentpprof 0.2.37`. Every view conserved exactly 8,509
operations and exactly 290,601,555,244 integer risk units, globally and in each
group:

| View | Groups | Operation exact | Global risk exact | Per-group risk exact |
|---|---:|---|---|---|
| Flat | 1 | yes | yes | yes |
| Raw action | 259 | yes | yes | yes |
| Semantic | 419 | yes | yes | yes |
| Session | 1,000 | yes | yes | yes |
| Ungrouped risk | 8,509 | yes | yes | yes |

The semantic stack retained the complete raw
`action -> target -> repeat_state` leaf and added only `intent -> phase`. The
same saved released risk scored every view.

## Co-primary results

The equal-family macro results were:

| View | Macro AP | Macro work-to-50 |
|---|---:|---:|
| Raw action | 0.556133 | 0.329920 |
| Semantic | 0.587655 | 0.313600 |

The predeclared paired effects were:

| Effect | Point estimate | 95% percentile interval | Condition |
|---|---:|---:|---|
| Semantic minus raw AP | +0.031522 | [+0.015138, +0.053514] | favorable |
| Raw minus semantic work-to-50 | +0.016320 | [-0.022550, +0.074214] | crosses zero |

Thus semantic has a complete-population AP improvement whose paired interval is
entirely positive. The complete-population work-to-50 point estimate is also in
the favorable direction, but the query-cluster interval includes small adverse
and favorable values. This work interval is neither entirely favorable nor
entirely adverse.

The family point estimates expose the source of uncertainty without becoming
new verdict quotas:

| Family | Raw AP | Semantic AP | Delta AP | Raw work50 | Semantic work50 | Raw − semantic work50 |
|---|---:|---:|---:|---:|---:|---:|
| BFCL | 0.392090 | 0.424146 | +0.032057 | 0.313127 | 0.297297 | +0.015830 |
| GAIA dev | 0.761772 | 0.793278 | +0.031507 | 0.417690 | 0.380221 | +0.037469 |
| HotpotQA | 0.377033 | 0.399956 | +0.022923 | 0.348774 | 0.354223 | -0.005450 |
| tau2 | 0.693640 | 0.733240 | +0.039601 | 0.240090 | 0.222660 | +0.017430 |

AP improves in all four families. Work-to-50 improves in three families and is
slightly worse in HotpotQA. The valid paired bootstrap, not this 3/4 count,
determines uncertainty.

## Matched semantic-specificity control

All 200 shuffles jointly permuted `(intent, phase)` pairs only within each raw
`(family, action, target, repeat_state)` leaf. Every permutation preserved the
exact semantic subgroup sizes. The observed macro AP delta was 0.031522. The
matched-shuffle deltas ranged from 0.009031 to 0.035184, with median 0.018215.
Only one shuffled delta was at least as large as observed:

```text
p_shuffle = (1 + 1) / 201 = 0.009950
```

The complete result therefore passes the predeclared semantic-specificity
condition. The AP gain is not explained by refinement granularity alone under
this matched control.

## Supporting measurements

Semantic also improves the equal-family macro recall at 30% inspection from
0.358487 to 0.435248. Binary harmful accuracy changes from 0.706045 to
0.706173, and adapted FirstErrAcc from 0.404 to 0.405. These supporting metrics
describe the result but do not alter the predeclared conjunctive verdict.

Session grouping achieves AP 0.598611 and work-to-50 0.273997; ungrouped risk
achieves AP 0.776683 and work-to-50 0.194959. They remain diagnostic references,
not post-hoc pass conditions. They show that the released local risk contains
additional information and that the next experiment should improve how a
semantic profile concentrates early inspection work rather than replace the
fixed RQ or positive hypothesis.

## Mechanical verdict derivation

The plan requires all three conditions for `SUPPORTED`:

1. semantic-minus-raw AP interval lower bound above zero: **yes**;
2. raw-minus-semantic work-to-50 interval lower bound above zero: **no**;
3. matched-shuffle `p <= 0.05`: **yes**.

The plan assigns `CONTRADICTED` only when either interval is entirely adverse.
Neither interval is entirely adverse. Therefore the only plan-consistent
verdict is **INCONCLUSIVE**.

## Artifact set

The complete ignored output is under:

```text
docs/visexp/out/agentprocessbench-rq2/full/
```

It includes visible projection, released risks, count/risk AgentProf inputs,
ten AgentProf profile JSONs, assignments, post-profile labels, 200 shuffle rows,
10,000 compressed bootstrap rows, `profile-report.json`, `summary.json`, and
generated `report.md`. These ordinary machine artifacts permit independent
recalculation; they are not contracts, freezes, manifests, or Git gates.

## Research disposition

This completed run must remain in research history. It does not authorize a
paper edit because the complete conjunctive construction is not yet supported.
It also does not authorize a smaller claim, a different RQ, a weaker story, or
negative-result prose in the paper.

After independent result review, the next EXPERIMENT node should retain RQ2 and
the positive hypothesis and propose a second construction focused on making the
already-positive semantic AP concentration translate into stable lower
work-to-50. Any new construction requires a new Markdown plan and independent
plan review before execution. The current full result, metrics, fields, and
verdict must not be silently revised.

No paper, canonical submodule, story, RQ, hypothesis, or shared skill was
edited in this execution node.

## Independent FULL result review

**Reviewed:** 2026-07-13T05:51:00-07:00  
**Required skill:** `research-experiment-design`  
**Verdict:** **PASS**  
**Must-fix:** **zero**

The independent reviewer recalculated the complete joins; all five AgentProf
operation/risk profiles; all family and macro point estimates; all 200 matched
shuffles and their within-raw-leaf subgroup sizes; and every one of the 10,000
query-cluster bootstrap rows and percentile intervals. Its recalculated values
match the machine summary and this report exactly.

The reviewer confirmed the mechanical disposition:

```text
run status: valid
tested hypothesis: inconclusive
research value: supporting
paper impact: no paper edit yet
```

The AP interval is entirely favorable and the semantic-specificity control
passes. The work-to-50 interval crosses zero but is not entirely adverse.
Therefore the result cannot be called either `SUPPORTED` or `CONTRADICTED`.
The next experiment must keep fixed RQ2 and the positive hypothesis and target
stable inspection-work improvement rather than narrowing the story.
