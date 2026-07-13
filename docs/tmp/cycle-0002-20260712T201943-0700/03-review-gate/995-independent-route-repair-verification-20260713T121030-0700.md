# Independent REVIEW Source-Route Repair Verification

**Node:** `995-independent-route-repair-verification-20260713T121030-0700`  
**Started:** 2026-07-13T12:06:52-07:00  
**Completed:** 2026-07-13T12:10:30-07:00  
**Phase / cycle / gate:** BUILD_AND_EVALUATE / cycle 0002 / REVIEW  
**Role:** fresh independent REVIEW outer-repair verifier; not the original 990
outer auditor, review-002 selector/reviewer/verifier, meta-reviewer, or root  
**Parent:**
[`990-independent-outer-audit-20260713T112434-0700.md`](990-independent-outer-audit-20260713T112434-0700.md)  
**Status:** **PASS**  
**Git operations:** none  
**Files changed by this node:** this report only

## Executive Verdict

**PASS.** The bounded repair closes both source-route defects that prevented
REVIEW exit:

1. the original 990 blocker is closed because AgentTelemetry is no longer the
   selected localization source; it is retained accurately as a fault-detection,
   telemetry-taxonomy, and OTel baseline precedent whose accepted artifact does
   not release official fault-bearing step/span gold; and
2. the later report-300 target-accounting blocker is closed because the repaired
   HINTBench handoff distinguishes 978 annotation records from 938 distinct
   target pairs, keeps the 935 mappable pairs, and treats the three official
   absent targets in records 170, 233, and 516 as common terminal misses without
   remapping or dropping them.

The next route is exactly one fresh, complete experiment inside fixed RQ2. It
uses the current official HINTBench snapshot, defines FULL as all 536 currently
enumerable records rather than the unavailable advertised 629, and compares one
target-blind semantic-responsibility profile with the smallest strong
same-information baseline positions at matched 80% macro recall. The route does
not add RQ3 or RQ4, change the exact thesis or any RQ, edit the paper, or wait for
a human.

The REVIEW gate may now write its `999` gate report and transition to one
ordinary `research-experiment-design` EXPERIMENT gate for fixed RQ2.

## Prior-Verdict And Priming Disclosure

This verifier was intentionally given the original `REPAIR CURRENT GATE`
verdict, the bounded HINTBench source selection, report 300's proposed
target-accounting repair, report 400's PASS, and the root's canonical-memory
repair. I therefore knew the expected closure argument before verification.

I did not treat any of those verdicts as primary evidence. I independently:

- enumerated the current official HINTBench JSON in full;
- inspected the current official evaluator's target-union and input-schema
  behavior;
- checked the three absent target identities against released step IDs;
- checked historical cycle-0001 FULL reports for prior AgentRx/TELBench target
  use;
- searched the repository for pre-existing HINTBench target consumption;
- read both live canonical frontier files and checked their local links; and
- compared current paper/submodule hashes and post-990 file modifications with
  the completed WRITE handoff and original outer audit.

This was a verification of the one source-route blocker, not a new whole-paper
review or a new benchmark search.

## Question And Declared Boundary

The node asks only whether the bounded source-route repair is valid enough for
the REVIEW gate to choose its next action under the outer-audit, gate-exit, and
canonical-memory rules.

The declared checks are:

1. AgentTelemetry selection is removed while its legitimate precedent remains;
2. HINTBench's live population and target counts match the repaired handoff;
3. the three absent official targets receive a symmetric, non-handmade terminal
   rule;
4. HINTBench is fresh while AgentRx/TELBench are correctly treated as already
   target-consumed evidence;
5. the handoff remains one fixed-RQ2, matched-recall inspection experiment with
   strong same-information alternatives;
6. `docs/evaluation.md` and `docs/background-related-work.md` agree on the
   source, population, target accounting, RQ boundary, and next action;
7. the exact thesis, four RQs, story, paper, submodule, skills, and code remain
   unchanged; and
8. no Git/integrity ceremony or human wait has entered the scientific route.

No new benchmark family, broader literature program, experiment, paper review,
paper edit, skill audit, or source-code review was performed. External access
was limited to the current official HINTBench test JSON and evaluator.

## Inputs Read

### Required repair chain

- [`990-independent-outer-audit-20260713T112434-0700.md`](990-independent-outer-audit-20260713T112434-0700.md)
- [`review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md`](review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md)
- [`review-002/300-independent-source-selection-review-20260713T115642-0700.md`](review-002/300-independent-source-selection-review-20260713T115642-0700.md)
- [`review-002/400-independent-source-repair-verification-20260713T120251-0700.md`](review-002/400-independent-source-repair-verification-20260713T120251-0700.md)
- [`950-root-source-route-repair-and-memory-update-20260713T120535-0700.md`](950-root-source-route-repair-and-memory-update-20260713T120535-0700.md)

### Current canonical state and human intent

- [`docs/evaluation.md`](../../../evaluation.md)
- [`docs/background-related-work.md`](../../../background-related-work.md)
- [`docs/user-instruction.md`](../../../user-instruction.md)
- [`docs/questions-for-author.md`](../../../questions-for-author.md)

### Historical freshness evidence

- [`cycle-0001 AgentRx/TELBench FULL execution`](../../cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-00/full-execution-report.md)
- [`cycle-0001 AgentRx/TELBench result review`](../../cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-00/result-review.md)
- [`cycle-0001 grouping result review`](../../cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-00/grouping-result-review.md)

### Primary artifact opened

- current official HINTBench test JSON:
  <https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json>
- current official HINTBench evaluator:
  <https://anonymous.4open.science/api/repo/HINTBench-B841/file/eval/evaluate.py>

The complete `auto-research-orchestrator/SKILL.md` and complete
`hierarchical-research-state-machine.md` were read before verification, with
particular attention to evidence precedence, outer audit, gate exit, canonical
memory, non-blocking human questions, and the prohibition on additional control
artifacts.

## Independent Primary-Artifact Recalculation

I streamed the current JSON directly from the paper-linked 4open endpoint and
enumerated every record and `risk_labels` entry. For each annotation I used its
official numeric `risk_origin_step` when present or official numeric `step_id`
otherwise. A target was mappable only if the exact value occurred in the same
record's released `trajectory[].step_id` set. No annotation description, array
position, neighboring step, or inferred range participated.

| Property | Independent current value | Repaired route | Result |
|---|---:|---:|---|
| Current test records | 536 | 536 | Match |
| Risky records | 400 | 400 | Match |
| Safe records | 136 | 136 | Match |
| Official annotation records | 978 | 978 | Match |
| `risk_origin_step` annotations | 464 | 464 | Match |
| `step_id` annotations | 514 | 514 | Match |
| Distinct `(record, target step)` pairs | 938 | 938 | Match |
| Mappable annotation records | 975 | 975 in report 300/400 | Match |
| Distinct mappable target pairs | 935 | 935 | Match |
| Distinct absent target pairs | 3 | 3 | Match |
| Risky records without official targets | 0 | 0 | Match |
| Risky records without any mappable target | 0 | 0 | Match |
| Safe records with non-empty target lists | 0 | 0 | Match |

The three independently recovered absent targets are exactly:

| Record `id` | `task_id` | Official target | Released-step result |
|---:|---|---:|---|
| 170 | `propertyRisk_task_0009_risk_v7` | 7 | absent; common terminal miss |
| 233 | `publicTransit_task_0006_risk_v6` | 9 | absent; common terminal miss |
| 516 | `sportsIntelligence_v11_task_0012_risk_v1` | 13 | absent; common terminal miss |

The current evaluator independently confirms the relevant published scoring
primitive: within each sample it unions official risk-step identities before
computing step precision, recall, and F1. It reads `injected_risks` and falls
back from `risk_steps` to `risk_origin_step` plus `affected_steps`; the current
test JSON instead uses `risk_labels` and may use `step_id`. The repaired handoff
therefore correctly permits thin deterministic field normalization and
correctly forbids claiming that the evaluator runs unchanged.

This source mismatch is fully disclosed and bounded. It does not authorize a
new label: exact official target identities remain the only gold.

## Original 990 Blocker Closure

The original audit found one transition-invalidating defect: AgentTelemetry
did not supply official target step/span identities for the selected RQ2
localization experiment.

The repaired state closes that defect cleanly:

- `docs/evaluation.md` records AgentTelemetry only as the first rejected source
  choice and explains that its accepted artifact has run/cell fault-detection
  outcomes but no official step/span localization gold.
- `docs/background-related-work.md` retains AgentTelemetry under standards and
  production observability as an agent-specific span-taxonomy,
  fault-detection-benchmark, toolkit, and OTel baseline precedent. It explicitly
  says AgentTelemetry is not the localization source.
- both canonical frontiers select the current official HINTBench 536-record
  snapshot as the next and only experiment source.
- no live passage selects, recommends, or defers to AgentTelemetry for the next
  experiment. Historical mention of the failed first route remains appropriate
  provenance rather than stale routing authority.

AgentTelemetry is thus neither erased nor misused: its supported precedent is
preserved, while the unsupported localization role is removed.

## Report-300 Target-Accounting Blocker Closure

The independent report 300 issued four bounded must-fixes. The current repaired
report 200, verification 400, root handoff, and canonical memory agree on every
closure:

| Report-300 must-fix | Current repaired state | Verdict |
|---|---|---|
| Separate annotation count from unique step targets | 978 annotations and 938 distinct target pairs are stated separately | Closed |
| Remove the false all-targets-map requirement | 935 distinct pairs map; three exact absent targets are retained | Closed |
| Score primary recall over each trajectory's union of official step IDs | Duplicate annotations at one step count once; all official identities remain | Closed |
| Do not call the current file the published 629-record FULL set | FULL is all 536 records currently enumerable from the official endpoint | Closed |

The terminal rule is information-neutral: records 170, 233, and 516 miss the
same absent target for every method. Their annotations and trajectories remain
in the primary intent-to-treat accounting, and a 935-mappable-target analysis is
only a declared sensitivity. Nothing is moved to an adjacent step, inferred
from prose, or deleted.

## Freshness And Reserve Audit

### HINTBench is fresh

A repository-wide exact search for `HINTBench`, `risk_origin_step`, the three
specific `task_id` values, and their target identities found no occurrence
outside the bounded source-repair reports and the two canonical updates created
from them. There is no earlier AgentProf HINTBench implementation, outcome,
target-consumption report, or result path. The 536-record target population has
not informed prior AgentProf mechanism selection.

### AgentRx and TELBench are not fresh confirmation targets

The cycle-0001 FULL and result reports show that AgentProf already evaluated:

- all 73/73 publicly aligned AgentRx trajectories, 3,265 operations, and all 73
  annotated critical-step positives; and
- all 1,000/1,000 TELBench cases, 11,934 spans, and 2,552 harmful-span positives,
  including complete native bare/DRIFT rows.

Those official failure locations and harmful-span labels entered the completed
scoring and then informed the mechanism-diagnosis report. AgentRx and TELBench
remain strong protocol, metric, and baseline precedents, but reusing them as
fresh confirmation would relabel observed targets as untouched evidence. The
root repair's reason for excluding them from the fresh route is therefore
correct and evidence-backed.

Who&When remains an eligible 184-trajectory reserve whose prior plan never
reached implementation or FULL. It is not mixed with the selected source. The
route makes one source choice, not a benchmark bundle.

## One-Experiment And Baseline Audit

The handoff remains one experiment within the exact fixed question:

> **RQ2: Does Profiler Output Correspond to Real Problems?**

The tested positive hypothesis remains ambitious: across the complete current
official HINTBench test snapshot, target-blind grouping by stable semantic
responsibility should require less atomic-step inspection to recover at least
80% of official risky-step targets than the strongest comparator with the same
raw steps and non-label fields.

The primary decision is matched recall, not a low-work point at lower recall:

- population: all current 536 records, including 400 risky and 136 safe;
- target unit: each risky trajectory's union of official target step IDs;
- outcome: minimum atomic-step inspection fraction and count at at least 80%
  macro recall over the 400 risky trajectories;
- support condition: reach the recall target and obtain a paired work-reduction
  interval excluding zero against the strongest admitted same-information
  non-oracle comparator; and
- completion: every approved record/method/repetition cell reaches a terminal
  outcome; smoke runs and successful prefixes are not results.

The three baseline positions test the smallest load-bearing competing
explanations rather than creating three experiments:

1. native sequential inspection tests whether source order alone is enough;
2. flat independent-step ranking tests whether the target-blind score alone
   explains the gain; and
3. flat same-information multidimensional aggregation tests whether ordinary
   grouping over all fields visible to AgentProf captures the benefit without
   ordered stacks.

Every position receives the same raw steps, allowed non-label fields, ranking
budget, and tuning opportunity. The future plan review may admit the smallest
strong subset that preserves these scientific positions. It may not introduce
target labels, a stronger hidden localizer, or a weaker run-level substitute.

Safe records remain negative controls within this RQ2 population. They do not
enter the risky-target recall denominator and do not become a second research
program.

## Scientific-Contract And Human-Intent Audit

The repair preserves the exact thesis:

> **Agent observability needs profiling, not only debugging.**

It also preserves the exact four-question program:

1. resource attribution;
2. correspondence to real problems / localization;
3. tag accuracy; and
4. profiling cost.

Only RQ2 is selected for the next experiment. The repair adds no RQ3 tagger
accuracy work and no RQ4 cold/warm cost work. RQ1, RQ3, and RQ4 remain ranked
sibling evidence branches for later whole-paper decisions.

The repair changes a source edge, not the paper's problem, motivation, thesis,
story, operations, operation stacks, RQ meaning, positive hypothesis,
contribution scope, or evaluation promise. It follows the active user
instructions to keep the large story, use real published artifacts, complete
experiments rather than stop at smoke, and improve evidence/mechanism rather
than narrow the idea.

`docs/questions-for-author.md` has no open question. No research judgment is
waiting on a human; ordinary REAL PREFLIGHT is already the selected next
action.

## Canonical-Memory Consistency And Link Audit

The two live canonical documents agree on the complete current frontier:

| State item | `docs/evaluation.md` | `docs/background-related-work.md` | Result |
|---|---|---|---|
| First AgentTelemetry route | rejected for no official localization gold | retained only as precedent, not source | Consistent |
| Selected source | HINTBench current official snapshot | HINTBench current official snapshot | Consistent |
| FULL population | 536 = 400 risky + 136 safe | current 536, not advertised 629 | Consistent |
| Target accounting | 978 annotations / 938 distinct / 935 mappable / three absent | same counts and terminal rule | Consistent |
| Primary decision | inspection work at 80% macro recall | same | Consistent |
| Baseline boundary | strongest same-information non-oracle comparison | same-information baselines | Consistent |
| RQ boundary | fixed RQ2 only; no RQ3/RQ4 program | next gate owns only RQ2; siblings remain | Consistent |
| Next outer state | EXPERIMENT | EXPERIMENT | Consistent |

Every relative Markdown link in both current canonical files resolves to an
existing local target. Their detailed historical branches remain linked rather
than being silently deleted, while their next-action passages are current.

At 202 and 191 lines respectively, the files remain close to the orchestrator's
soft one-to-two-hundred-line current-frontier budget. The two-line overage in
`docs/evaluation.md` is not a route or memory validity defect and does not
justify another housekeeping loop before the selected experiment.

## Ownership, Artifact, And Simplicity Audit

Current hashes remain identical to the completed WRITE handoff and REVIEW
entry:

- `docs/paper/main.tex`:
  `c924bb7af782ef21083451c0ac1ebc906715dd3e4c861f72b8eb1815c3e22fb1`
- `docs/paper/references.bib`:
  `27d34fb5db7c500def494ba93bcd9d3babf704325ebc8ebcf3d6aff7bc8a4ae6`
- untouched submodule `docs/agentpprof-paper/main.tex`:
  `430d94ba7714c328c4583aa4991326601ceef55ba1f01b59807a8beb6aa4bb91`

A bounded modification-time inventory after the original 990 audit found only
the source-repair reports plus `docs/evaluation.md` and
`docs/background-related-work.md`. It found no changed paper file, shared skill
file, source-code file, experiment-result file, AGENTS file, or submodule file.
The repaired root report's ownership declaration is therefore consistent with
the observable filesystem state.

The route introduces no non-Markdown control contract, Git/hash binding, seal,
packet, attestation, finalizer, private key, immutable manifest, checker gate,
or human approval requirement. The recorded source counts, target identity,
visible-information boundary, and terminal behavior are ordinary scientific
plan facts. This verifier performed no Git operation.

## Evidence Precedence And Residual Caveats

Primary artifact enumeration overrides summaries and agrees with the repaired
reports. The current 536-versus-advertised-629 discrepancy and the three absent
step IDs remain material source limitations, but neither invalidates the route:

- the executable population is explicitly the finite current official 536;
- no unavailable paper-era record is claimed as executed;
- the three absent targets remain in symmetric primary accounting; and
- REAL PREFLIGHT must return to REVIEW, rather than improvise, if the official
  endpoint no longer reproduces the verified facts.

The broader paper still has unresolved RQ1, RQ2, RQ3, RQ4, novelty, and
submission-readiness objections ranked by the original outer audit. Those are
later paper-wide research branches. They do not invalidate this bounded source
route or require zero objections, another current-gate review, or a smaller
story.

## Research-Tree And Transition Decision

The repaired edge is evidence-backed and finite:

```text
RQ2 real-problem localization
└── official target-bearing source
    ├── AgentTelemetry -> closed as source; retained as precedent
    ├── AgentRx/TELBench -> protocol precedents; targets already consumed
    ├── Who&When -> eligible unselected reserve
    └── HINTBench -> selected fresh current 536-record snapshot
        ├── 978 annotations -> 938 distinct target pairs
        ├── 935 mappable pairs
        └── records 170/233/516 -> common terminal misses
```

No source-search branch remains open for the current selection. The justified
transition is:

```text
REVIEW 999
  -> EXPERIMENT_GATE, fixed RQ2 only
  -> ordinary Markdown plan and 3--5 scientific plan reviews
  -> REAL PREFLIGHT on the current official HINTBench path
  -> FULL over every approved 536-record/method/repetition cell
  -> result review and independent outer audit
  -> whole-paper REVIEW regardless of result sign
```

This transition remains reversible only on direct source evidence: if REAL
PREFLIGHT obtains a different official population, target count, mapping count,
or absent-target identity, the source returns to REVIEW. Ordinary empirical
support, contradiction, or inconclusiveness closes the experiment and returns
to whole-paper REVIEW without changing the fixed thesis, story, RQ, or positive
hypothesis.

## Final Verdict

**PASS.** The original 990 AgentTelemetry source-route blocker and report 300's
bounded HINTBench target-accounting blocker are both closed. The canonical
frontiers are current, linked, and mutually consistent. The paper, skills,
code, submodule, exact thesis, original story, and four fixed RQs remain
unchanged.

The root may write the REVIEW `999` gate report and enter one complete,
same-information, matched-80%-recall HINTBench localization experiment for
fixed RQ2. No additional search, checker, process ceremony, story change, or
human intervention is required.
