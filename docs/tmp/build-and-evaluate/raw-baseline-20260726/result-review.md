# Independent result review

The run is complete and valid under its frozen terminal-status rules, but the tested representation-superiority hypothesis remains inconclusive. Five of 18 Raw cells exceeded the retrieval-byte cap and produced no scoreable response; the predeclared invalid-cell veto therefore applies.

## Evidence audited

I reviewed the frozen [protocol.md](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/protocol.md), both plan reviews, [runner.py](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/runner.py), runtime freeze, boundary controls, preflight artifacts, [result.md](/home/yunwei37/workspace/agentsight-agent-nebula-research/docs/tmp/build-and-evaluate/raw-baseline-20260726/result.md), run summary, effects, and every summary/cost/result CSV.

I also parsed all 18 atomic corrected-v4 checkpoints, their 18 answer-blind intermediate checkpoints, all event streams, all 13 final responses, prompts, and recorded commands.

## Freeze, oracle, and comparison inputs

The registered hashes match the current artifacts and their referenced originals:

- runner: `a54ecbd…12f4`
- frozen measurement implementation: `e50adb5c…9240`
- source freeze: `838b814a…e35`
- question semantics: `484d1c9a…de83e`
- corrected-v4 answers: `bea810e0…e254`
- repaired Trajectory results: `dd89048d…eac`

The copied corrected-v4 and repaired-Trajectory files are byte-identical to the external paths referenced by the runner.

Independent joins found:

- 120 unique gold IDs;
- exactly 24 corrections: 17 A and 7 C;
- 120 unique repaired-Trajectory rows, all joined to corrected-v4;
- repaired Trajectory = 102/120 overall and 60/60 B+C;
- 360 unique Raw cell/ID rows, with every gold ID appearing exactly three times;
- every Raw `expected` value equals corrected-v4, while every `original_frozen_expected` preserves the obsolete freeze value;
- all `correct` and `wrong` flags recompute from exact canonical equality.

The repaired Trajectory uses the same frozen 72 native files and question semantics. It is nevertheless a post-repair, same-corpus result, so this remains a fixed-corpus comparison rather than blind held-out validation.

## Completion and mechanism engagement

Every registered cell has exactly one `attempt-1`, one event stream, one model thread, one intermediate checkpoint, and one atomic corrected-v4 checkpoint. There are no full-matrix `attempt-2` directories or evidence of scientific retries. The separate preflight passed on its first attempt: 20/20 scoreable, 19 correct, 12 retrieval calls, 326,412 returned bytes, and 229.18 seconds.

All 18 cells engaged raw-evidence retrieval: every event stream contains completed commands reading native files under `sources/`, including the five cap-stopped cells.

| Project | Rep | Terminal status | Scoreable | All correct | B+C C/W/A | Calls | Returned bytes | Seconds |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| agentsight | 1 | complete | 20 | 16 | 8/2/0 | 14 | 500,656 | 202.65 |
| agentsight | 2 | complete | 20 | 15 | 8/2/0 | 18 | 254,081 | 341.15 |
| agentsight | 3 | byte cap | 0 | 0 | 0/0/10 | 10 | 1,420,969 | 70.59 |
| ActPlane | 1 | complete | 20 | 12 | 7/3/0 | 12 | 513,555 | 223.03 |
| ActPlane | 2 | complete | 20 | 12 | 7/0/3 | 25 | 540,277 | 384.75 |
| ActPlane | 3 | complete | 20 | 12 | 7/3/0 | 19 | 758,452 | 284.41 |
| bpf-developer-tutorial | 1 | byte cap | 0 | 0 | 0/0/10 | 9 | 1,695,314 | 84.66 |
| bpf-developer-tutorial | 2 | byte cap | 0 | 0 | 0/0/10 | 4 | 1,060,157 | 26.17 |
| bpf-developer-tutorial | 3 | byte cap | 0 | 0 | 0/0/10 | 6 | 1,256,841 | 37.89 |
| eunomia.dev | 1 | complete | 20 | 11 | 5/5/0 | 28 | 207,312 | 491.27 |
| eunomia.dev | 2 | complete | 20 | 13 | 5/3/2 | 18 | 294,508 | 364.35 |
| eunomia.dev | 3 | complete | 20 | 15 | 7/0/3 | 30 | 554,873 | 357.24 |
| agentskill-observability-paper | 1 | byte cap | 0 | 0 | 0/0/10 | 11 | 1,243,208 | 82.34 |
| agentskill-observability-paper | 2 | complete | 20 | 19 | 10/0/0 | 10 | 363,622 | 224.74 |
| agentskill-observability-paper | 3 | complete | 20 | 19 | 10/0/0 | 17 | 120,298 | 234.30 |
| academic-writing-skills | 1 | complete | 20 | 15 | 6/4/0 | 13 | 646,692 | 233.34 |
| academic-writing-skills | 2 | complete | 20 | 16 | 7/3/0 | 21 | 277,971 | 296.29 |
| academic-writing-skills | 3 | complete | 20 | 16 | 7/3/0 | 17 | 167,459 | 283.26 |

No cell crossed the 64-call, 900-second, or 65,536-byte final-output limits. Complete cells remained below 1 MiB returned-tool bytes. Each stopped cell crossed 1 MiB when a completed tool result caused the cumulative counter to overshoot, consistent with the frozen monitor semantics.

## Scoring and terminal semantics

Independent aggregation reproduced every row in `aggregate.csv`, `cell-summary.csv`, `project-family.csv`, and `baseline-comparison.csv`:

| Family | Registered | Scoreable | Correct | Wrong | Abstain | Coverage | Scoreable exact | Answered accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 90 | 65 | 32 | 28 | 30 | 35.6% | 49.2% | 53.3% |
| B | 90 | 65 | 55 | 10 | 25 | 61.1% | 84.6% | 84.6% |
| C | 90 | 65 | 39 | 18 | 33 | 43.3% | 60.0% | 68.4% |
| D | 90 | 65 | 65 | 0 | 25 | 72.2% | 100.0% | 100.0% |
| All | 360 | 260 | 191 | 56 | 113 | 53.1% | 73.5% | 77.3% |
| B+C | 180 | 130 | 94 | 28 | 58 | 52.2% | 72.3% | 77.0% |

The semantics are correctly separated:

- the 13 complete responses contribute 260 scoreable rows, including 13 explicit scoreable abstentions;
- the five invalid cells contribute 100 unscoreable denominator abstentions;
- B+C contains 50 unscoreable plus 8 explicit abstentions;
- conditional accuracy uses answered rows only: 191/247 overall and 94/122 B+C.

Thus `191/360`, `191/260`, `94/180`, `94/130`, and the proposed 53.1%, 52.2%, and 72.2% paper-table values are numerically correct.

## Leakage, isolation, and retries

The model-visible sandboxes contain only the project’s 12 hash-matched native files, source index, question semantics, questions, cutoff manifest, and output schema. Corrected answers, Trajectory results, paper results, repository contents, other projects, and earlier responses are not mounted.

The boundary controls establish that an inert original path string is permitted while the parent oracle path is absent. Actual event commands contain no corrected-answer, gold, Trajectory, experiment-result, browser, or remote-network invocation. Apps, browser, image generation, and multi-agent features were disabled.

The answer-blind intermediate checkpoint uses the obsolete frozen expected values only after the model call. The corrected-v4 join occurs in the outer runner, and atomic checkpoints carry both the corrected-v4 tag and oracle hash. No observed path permits the model to read either checkpoint before answering.

## Effect and invalid-cell veto

The independently reconstructed Raw B+C repetitions are:

- agentsight: 0.8, 0.8, 0.0
- ActPlane: 0.7, 0.7, 0.7
- bpf-developer-tutorial: 0.0, 0.0, 0.0
- eunomia.dev: 0.5, 0.5, 0.7
- agentskill-observability-paper: 0.0, 1.0, 1.0
- academic-writing-skills: 0.6, 0.7, 0.7

Reimplementing the seeded two-level bootstrap reproduces Trajectory-minus-Raw = `+0.4777778`, with the fixed-corpus interval `[+0.2722222, +0.7277778]`.

That interval is denominator-inclusive and heavily affected by five invalid cells. The frozen veto is present in the runner and correctly changes the decision to `mixed_or_inconclusive`. It cannot support superiority or parity.

## Baseline fairness and resource accounting

The accuracy comparison is fair only for the declared fixed reader, corpus, questions, and budgets: Raw and repaired Trajectory use matching source hashes and corrected-v4 IDs. It is not a general comparison of LLMs or representations, and the repaired Trajectory row is not held-out evidence.

There is no matched, method-specific Trajectory time or cost measurement. Consequently, the cost conjunct of the hypothesis is untested, and no speedup, cost ratio, or efficiency superiority is supportable.

The following observed totals reproduce exactly:

- summed call wall time: 4,222.41 seconds;
- retrieval calls: 282;
- returned tool bytes: 11,876,245;
- median complete-cell time: 284.41 seconds;
- returned bytes in the five stopped cells: 6,676,489.

The token sums also reproduce—13,434,834 input, 12,344,832 cached, 193,206 output, and 81,959 reasoning—but they are not full 18-cell resource totals. The five cap-stopped calls emitted no terminal usage record and are stored as zero-token rows. Any paper use must call these “recorded usage for the 13 complete calls,” not total tokens consumed by the matrix.

The runtime manifests total 221,487,880 logical source bytes. The protocol’s prose description of “224 MiB on disk” is not exactly reproducible from that manifest; the manifest total should be used if archive size becomes paper-facing.

Historical State Diff, Session Local, and OCPM definitions are correctly treated as compatibility scope. Their absence from this exact-fact matrix is not a missing-baseline defect.

run status: valid  
tested hypothesis: inconclusive  
research value: supporting  
paper impact: mechanism or workload boundary  
next paper decision: Replace Raw=N/A only with the explicitly bounded measurements—53.1% overall coverage, 52.2% B+C coverage, and 72.2% scoreable rows—while disclosing all five cap-stopped cells and retaining the mixed/inconclusive verdict. Make no representation-necessity, superiority, speed, or cost claim; qualify token figures as usage reported by the 13 complete calls. A decisive representation claim would require a separately frozen matched or held-out evaluation, not retries of these registered cells.