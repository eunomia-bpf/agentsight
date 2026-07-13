# AgentProcessBench RQ2 implementation report

**Implemented and corrected:** 2026-07-13T05:35:01-07:00  
**Outer gate:** EXPERIMENT  
**Plan implemented:** `experiment-plan.md`, Revision 3  
**Status after review-round-1 corrections:** IMPLEMENTED; independent
re-review required; REAL PREFLIGHT not started

## Scope

This node implements only the already-approved AgentProcessBench experiment.
It does not edit the paper, canonical submodule, research question, positive
RQ2 hypothesis, story, or shared skills. The tested hypothesis remains one
construction inside fixed RQ2.

Implemented files:

- `script/agentprocessbench_profile_eval.py`;
- `script/test_agentprocessbench_profile_eval.py`.

No generated result artifact is tracked. The official source checkout and all
preflight/full outputs remain under the existing ignored
`docs/visexp/out/agentprocessbench-rq2/` path.

## Implemented pipeline

### Complete official-source conversion

The converter reads the four official JSONL files and validates the complete
released population before selecting a preflight subset:

- four families;
- 1,000 trajectories;
- 200 distinct `(family, query_index)` tasks;
- five rollouts per task;
- 8,509 assistant-message operations;
- exact assistant-message and official-label key alignment.

It clusters all 200 unique task descriptions once using AgentProf's existing
`cluster_tagger.py` implementation. The existing implementation selects 7
clusters on this source. Preflight then selects the first 10 query IDs in each
family without changing the global clustering result.

The visible converter emits only the predeclared fields: `intent`, `phase`,
`action`, `target`, `repeat_state`, session/task/step identity, and the constant
flat field. This visible pass checks only that the released label keys match
assistant-message identities; it never accesses a human-label value. After all
five fixed AgentProf views exist and pass conservation checks, a separate
scorer loader rereads the official files and accesses the human-label values.
Labels never enter an AgentProf operation file.

### Released blind-judge risk

The loader discovers exactly 20 complete official result directories and
requires one aligned prediction slot from every judge for every released step.
It computes equal-weight consensus risk from non-null `-1` predictions. The
three globally all-null steps receive exactly 0.5. Risk is also represented on
the exact integer scale `lcm(1..20)` so equivalent rational risks produce
identical score tiers.

The source-only integration check recovered the previously audited release
accounting:

- 6,914 operations have all 20 predictions non-null;
- exactly three operations have fewer than 15 non-null predictions;
- those same three operations have all 20 predictions null;
- the 40-task preflight subset contains 1,630 aligned visible operations and
  released risks.

No localization metric or human-label result was computed in this
implementation check.

### Real AgentProf views

The implementation invokes the release binary and requires the exact version
string `agentpprof 0.2.37`. It creates the four grouped views with the approved
stack fields:

1. flat;
2. session;
3. `action -> target -> repeat_state`;
4. `intent -> phase -> action -> target -> repeat_state`.

The ungrouped external-risk reference is represented as one operation-ID frame
per step. For each of all five views, the implementation independently computes
the expected folded stack counter and rejects the run unless the real AgentProf
JSON profile is exactly equal in group keys and operation counts.

The implementation also sends the same operations through real AgentProf with
exact integer `risk_units`. Because AgentProf interprets a zero operation value
as the default count one, the file encodes each value as `risk_units + 1`; the
scorer subtracts the already verified operation count from every emitted group.
It then requires exact per-group risk equality and exact global risk-sum
equality for flat, session, raw action, semantic, and ungrouped views. A single
lost, duplicated, or altered risk unit raises an execution error before labels
are loaded.

### Atomic scoring and controls

Each operation receives only its complete group's mean released risk. The
metric implementation first collapses equal group scores into one complete
tier. AP, work-to-50, recall-at-30, groups-to-50, and top-five measurements
therefore cannot use operation ID, individual risk, human label, or another
secondary order inside a group or equal-score tier.

The binary threshold remains strictly `risk > 0.5`. Adapted FirstErrAcc scans
the original step order inside every trajectory and compares the first
threshold-crossing operation with the first human `-1`; absence on either side
is represented as no error.

The matched control jointly shuffles observed `(intent, phase)` pairs inside
each raw `(family, action, target, repeat_state)` leaf. It verifies that the
pair multiset is preserved in every leaf and that the complete semantic group-
size multiset is unchanged. It runs exactly 200 deterministic permutations
from seed 4204 and uses the predeclared empirical p-value.

The cluster bootstrap samples original query IDs with replacement separately
inside every family. Every sampled task retains all five rollouts. Each draw
recomputes every group mean over the resampled multiset, uses one paired draw
for all views, and discards the complete draw only when any family has no
harmful positive. Preflight and full limits are enforced by the CLI.

### Outputs and verdict

The program writes ordinary JSON/JSONL/GZip evidence plus one Markdown report.
The Markdown experiment plan and report remain the human-auditable contracts;
the machine artifacts are result data, not seals or frozen manifests.

The full-run verdict implements only the predeclared three outcomes:

- `SUPPORTED` when both co-primary paired intervals are entirely favorable and
  matched-shuffle `p <= 0.05`;
- `CONTRADICTED` when either co-primary interval is entirely adverse;
- `INCONCLUSIVE` otherwise.

Preflight can return only `PREFLIGHT_ONLY` after complete execution, or
`INCOMPLETE`. No result changes the RQ, paper thesis, canonical story, or four-
RQ program.

## Verification completed before independent review

Commands:

```bash
python3 -m py_compile \
  script/agentprocessbench_profile_eval.py \
  script/test_agentprocessbench_profile_eval.py

python3 -m unittest -v \
  script/test_agentprocessbench_profile_eval.py
```

Result: nine focused tests passed; the joint AgentNet/AgentProcessBench
regression run passed 20 tests.

The tests cover:

- visible action/target/phase derivation;
- atomic equal-score AP and work-to-50;
- valid all-positive bootstrap populations while retaining the plan's
  no-positive discard rule;
- deterministic matched shuffle and exact group-size preservation;
- equal-weight 20-judge consensus and the all-null 0.5 rule;
- real `agentpprof 0.2.37` output equality for all five fixed views;
- real AgentProf operation and exact integer risk conservation for all five
  views;
- rejection of a one-unit risk loss;
- enforced call order in which human-label values load only after profiles;
- absence of human labels from both AgentProf operation files and absence of
  risk from the count operation file;
- exactly the predeclared scientific-verdict conditions.

The source-only integration check then loaded the complete official source and
all released judge outputs and confirmed the population/risk counts above.

## Independent-review request

The independent reviewer should read the complete Revision 3 plan and inspect
both implementation files. It should specifically recalculate or challenge:

1. source/message/label alignment without using target values to revise the
   construction;
2. visible-field and human-label separation;
3. real AgentProf stack-key equality;
4. exact rational risk and equal-score tier behavior;
5. atomic AP, work-to-50, recall-at-30, and top-five semantics;
6. within-raw-leaf shuffle preservation and empirical p direction;
7. query-cluster bootstrap multiplicities, recomputed group means, paired
   effects, discard rule, and completion limits;
8. full versus preflight CLI enforcement and verdict routing.

The reviewer must not edit files, run Git, modify the plan, inspect human-label
distributions, or compute the preflight result. `PASS` authorizes the fixed
REAL PREFLIGHT command; `REVISE` must identify a concrete implementation defect
against the approved plan.

## Independent implementation review — Round 1

**Reviewed:** 2026-07-13T05:32:00-07:00  
**Required skill:** `research-experiment-design`  
**Verdict:** **REVISE**

The reviewer found two must-fix defects:

1. `load_source()` accessed and retained human-label values before constructing
   the fixed AgentProf views, even though those values did not enter visible
   fields.
2. `construct_profiles()` proved operation conservation but did not prove or
   record exact released-risk conservation through every view.

Both findings were accepted. The first was fixed by separating visible source
conversion from `load_human_labels()` and calling the latter only after
`construct_profiles()`. The second was fixed with the real-AgentProf integer
risk pass and exact per-group/global checks described above. Focused regression
tests now fail on reversed label/profile order and on a one-unit risk loss.

No scientific plan, data selection, field, baseline, metric, threshold,
verdict, RQ, paper text, story, submodule, or skill changed. Round 2 must review
the corrected implementation independently before REAL PREFLIGHT.

## Independent implementation review — Round 2

**Reviewed:** 2026-07-13T05:38:00-07:00  
**Reviewer:** second independent subagent  
**Required skill:** `research-experiment-design`  
**Verdict:** **PASS**  
**Must-fix:** **zero**

The reviewer independently confirmed that the visible converter compares only
label keys, `load_human_labels()` runs only after every fixed AgentProf view
returns, and all five views enforce exact operation and integer-risk equality
both per group and globally. It also checked the reversible zero-risk encoding,
atomic equal-score metrics, released 20-judge/all-null handling, matched
shuffle, query-cluster bootstrap, CLI contract, and verdict routing. All nine
focused tests passed in the review.

The implementation has converged and is authorized to run the exact REAL
PREFLIGHT command from Revision 3. No paper, submodule, story, RQ, hypothesis,
or skill was reviewed or changed in this node.
