# Shell-boundary repair: paper-number delta report

Date: 2026-07-27
Projection: repaired `agentvis` from repository commit
`51f7cece251888a0bf559044b62188d499222e9a`
Baseline: the values currently printed in `docs/paper/`, backed by
`rq1-rq4-recompute-final`, `rq-extensions-final-20260726`, and the older
RQ3/RQ6 anchors cited below
New output: `rq1-rq4-recompute-v2-20260727`

## Classification

- **M (material):** a paper-visible exact count, numerator/denominator,
  one-decimal percentage, rank, gate, definedness, or provenance changed.
- **I (immaterial):** exact support rows may move, but the value at the
  precision printed in the paper, its ordering, and its gate/conclusion do not.
- **P (pending):** the sensitivity check found enough movement, or a downstream
  contract failure, to require the corresponding stage-three recompute.

This is a synchronization classification, not a claim that every `M` change
alters the paper's qualitative conclusion.

## Executive delta

| Item | Old | New | Class | Consequence |
|---|---:|---:|:---:|---|
| Included native roots | 551 | 551 | I | Corpus roots unchanged. |
| Tool actions | 181,303 | 181,303 | I | Corpus action count unchanged. |
| Attributed roots/actions | 551 / 176,288 | 551 / 176,288 | I | Attribution coverage unchanged. |
| Observed artifact identities | 5,746 | 5,676 | M | `-70`; RQ1/RQ3 figures and identity analyses must be synchronized. |
| Confirmed mutation rows | 13,906 | 13,809 | M | `-97`. |
| Mutation episodes | 13,860 | 13,766 | M | `-94`. |
| Mutated identities | 2,431 | 2,318 | M | `-113`. |
| RQ1 reuse range | 89.29--97.11% | 89.29--96.94% | M | Upper endpoint changes. |
| RQ1 action-volume Spearman rho | 0.2000 | 0.0286 | M | Association is even closer to zero. |
| RQ1 reuse rank, AgentSight vs. BPF tutorial | AgentSight 91.18% > BPF 91.13% | BPF 91.13% > AgentSight 90.95% | M | **One adjacent rank flips.** |
| RQ2 zero-mutation interval range | 29.3--86.1% | 29.3--86.5% | M | Upper endpoint changes; 1--817 maximum range is stable. |
| RQ3 Case D paper/docs mutation allocation, all/ok | 39.2% / 88.2% | 60.7% / 86.8% | M | Large provenance-sensitive shift: `+21.5 / -1.4 pp`. |
| RQ3 local-anchor locality range | 79.8--97.9% | 76.8--100.0% | M | Old RQ6 anchor was stale; exact local evidence is now regenerated from repaired events. |
| RQ4 components/boundaries | 121 / 111 | 121 / 111 | I | **Headline and 3/6 gate are stable.** |
| RQ4 confirmed accesses | 57,792 | 57,819 | M | `+27`; affects conditional prefix/overlap support, not component formation. |

The RQ1 persistence, reuse, and validation gates remain 6/6. RQ4 remains a
stopped cross-case estimator and a within-case/coverage result. RQ3's
path-local qualitative direction remains, but its paper numbers and the claim
that all six cases carry return evidence require stage-three synchronization.

## RQ1: persistence, reuse, validation, and repeated mutation

Project order below follows the paper's Case A--F mapping. Percentage deltas
are new minus old in percentage points.

| Project | Persistence old -> new (delta pp) | Reuse old -> new (delta pp) | Validation old -> new (delta pp) | Class |
|---|---|---|---|:---:|
| agentsight | 973/1042 (93.38%) -> 994/1068 (93.07%), `-0.31` | 5573/6112 (91.18%) -> 5601/6158 (90.95%), `-0.23` | 2450/6112 (40.09%) -> 2499/6158 (40.58%), `+0.50` | M |
| ActPlane | 28/239 (11.72%) -> 30/243 (12.35%), `+0.63` | 5442/5604 (97.11%) -> 5450/5622 (96.94%), `-0.17` | 1210/5604 (21.59%) -> 1217/5622 (21.65%), `+0.06` | M |
| eunomia.dev | 18/30 (60.00%) -> 24/39 (61.54%), `+1.54` | 650/694 (93.66%) -> 653/704 (92.76%), `-0.90` | 141/694 (20.32%) -> 149/704 (21.16%), `+0.85` | M |
| bpf-developer-tutorial | 8/18 (44.44%) -> 8/18 (44.44%), `0.00` | 257/282 (91.13%) -> 257/282 (91.13%), `0.00` | 47/282 (16.67%) -> 47/282 (16.67%), `0.00` | I |
| agentskill-observability-paper | 18/18 (100.00%) -> 18/18 (100.00%), `0.00` | 175/196 (89.29%) -> 175/196 (89.29%), `0.00` | 9/196 (4.59%) -> 9/196 (4.59%), `0.00` | I |
| academic-writing-skills | 1/1 (100.00%) -> 1/1 (100.00%), `0.00` | 234/247 (94.74%) -> 234/247 (94.74%), `0.00` | 33/247 (13.36%) -> 33/247 (13.36%), `0.00` | I |

The paper's persistence list therefore changes from
`973/1042, 28/239, 18/30, 8/18, 18/18, 1/1` to
`994/1068, 30/243, 24/39, 8/18, 18/18, 1/1`.

The reuse ordering changes from

`ActPlane > writing > eunomia > agentsight > bpf > AgentSkill`

to

`ActPlane > writing > eunomia > bpf > agentsight > AgentSkill`.

Only the AgentSight/BPF adjacent pair flips. The descriptive cross-project
rho changes from `0.2000` to `0.0286`; the inference remains “action volume
does not meaningfully order reuse,” but the printed coefficient is material.

### Mutation episodes and concentration

| Project | Mutated/all identities old -> new | Episodes/raw rows old -> new | Repeat fraction old -> new | Top-10% share old -> new | Max load old -> new | Class |
|---|---|---|---|---|---|:---:|
| agentsight | 1666/3267 -> 1640/3271 | 6556/6588 -> 6540/6568 | 74.6% -> 74.9% | 68.4% -> 68.5% | 1084 -> 1085 | M |
| ActPlane | 561/1809 -> 469/1725 | 5836/5849 -> 5751/5765 | 90.4% -> 91.8% | 77.6% -> 75.7% | 558 -> 558 | M |
| bpf-developer-tutorial | 32/170 -> 32/170 | 283/283 -> 283/283 | 88.7% -> 88.7% | 42.0% -> 42.0% | 39 -> 39 | I |
| eunomia.dev | 128/360 -> 131/368 | 738/739 -> 743/744 | 82.7% -> 82.4% | 71.4% -> 71.2% | 165 -> 165 | M |
| agentskill-observability-paper | 21/24 -> 21/24 | 196/196 -> 196/196 | 89.3% -> 89.3% | 86.7% -> 86.7% | 151 -> 151 | I |
| academic-writing-skills | 23/116 -> 25/118 | 251/251 -> 253/253 | 90.8% -> 90.1% | 57.0% -> 58.7% | 68 -> 68 | M |

Paper-facing ranges:

| Metric | Old | New | Class |
|---|---:|---:|:---:|
| Repeat-observed episode fraction | 74.6--90.8% | 74.9--91.8% | M |
| Exact top-10% episode share | 42.0--86.7% | 42.0--86.7% | I |
| Figure identity/episode/source-row caption | 5,746 / 2,431 / 13,860 / 13,906 | 5,676 / 2,318 / 13,766 / 13,809 | M |

Birth-state rows change from
`1042/2224/0/1, 239/1570/0/0, 18/152/0/0, 30/330/0/0,
18/6/0/0, 1/115/0/0`
to
`1068/2202/0/1, 243/1482/0/0, 18/152/0/0, 39/329/0/0,
18/6/0/0, 1/117/0/0`
(`confirmed-create / left-censored / unknown-create / unknown-rename`).
Unknown-create remains zero; that qualitative result is stable.

## RQ2: recognized-validation dynamics

Recognized success/failure/observed counts and complete-interval counts remain
unchanged for every project. The sole coverage-row change is ActPlane's
co-observed mutation rows, `48 -> 47`. Project success coverage remains 6/6,
complete inter-success coverage 5/6, and recognized-failure coverage 4/6.

| Lane | Zero-mutation old -> new | Median old -> new | P90 old -> new | Maximum old -> new | Class |
|---|---:|---:|---:|---:|:---:|
| ActPlane/3dae89cd06ae | 84.4% -> 85.2% | 0 -> 0 | 1 -> 1 | 817 -> 817 | M |
| writing/4725c74bf420 | 62.5% -> 62.5% | 0 -> 0 | 10 -> 10 | 140 -> 143 | M |
| agentsight/b5bc34dabe6a | 29.3% -> 29.3% | 2 -> 2 | 17 -> 17 | 291 -> 291 | I |
| agentsight/e58fce112c6e | 86.1% -> 86.5% | 0 -> 0 | 1 -> 1 | 95 -> 95 | M |
| agentsight/f2407a7d66d5 | 66.7% -> 66.7% | 0 -> 0 | 1 -> 1 | 1 -> 1 | I |
| bpf/a192f642f3ee | 47.6% -> 47.6% | 2 -> 2 | 43 -> 43 | 69 -> 69 | I |
| eunomia/30e8a01e495d | 56.9% -> 58.8% | 0 -> 0 | 21 -> 21 | 361 -> 371 | M |

The paper range is `29.3--86.1% -> 29.3--86.5%`; the maximum range remains
`1--817`. The six validation-before-supersession fractions are reported in the
RQ1 table above.

## RQ3: allocation, migration, and repaired RQ6 local anchor

### Allocation status sensitivity

The old values come from
`step-0002-20260722T003659-0700/experiment-rq5-20260722T013003-0700`;
the new values are rebuilt from the repaired event projection through the
status-preserving access ledger in `rq3-input/rq4-accesses.csv`.

| Project | All resolved old -> new | Ok-only old -> new | TV shift old -> new | Class |
|---|---:|---:|---:|:---:|
| agentsight | 64.1% -> 64.1% | 75.3% -> 74.9% | 11.4% -> 11.1% | M |
| ActPlane | 72.7% -> 72.6% | 85.4% -> 85.1% | 13.4% -> 13.4% | M |
| bpf-developer-tutorial | 89.0% -> 89.0% | 98.9% -> 98.9% | 10.0% -> 10.0% | I |
| eunomia.dev (Case D) | **39.2% -> 60.7%** | **88.2% -> 86.8%** | **49.7% -> 26.7%** | M |
| agentskill-observability-paper | 100.0% -> 100.0% | 100.0% -> 100.0% | 0.0% -> 0.0% | I |
| academic-writing-skills | 97.2% -> 96.1% | 97.2% -> 96.0% | 0.0% -> 0.0% | M |

Case D is the largest paper-visible allocation delta: the all-status rate
moves `+21.5 pp`, the ok-only rate `-1.4 pp`, and their TV shift `-23.0 pp`.
This is primarily closure of the stale-input/provenance gap identified by the
audit, not evidence of a scientific reversal: all six dominant classes remain
paper/docs, and status sensitivity remains substantive in Case D.

### Native-call transitions and returns

| Metric | Old paper range | New range | Class |
|---|---:|---:|:---:|
| Same artifact | 29.3--81.6% | 25.6--82.6% | M |
| Same module | 17.5--64.6% | 17.4--68.0% | M |
| Cross module | 0.9--20.8% | 0.0--23.2% | M |
| Qualified return-gap medians | 2--4 calls | 2--4 calls | I |

The new per-project same-artifact/same-module/cross-module triples are:
AgentSight `38.7/48.4/13.0%`, ActPlane `46.4/42.5/11.1%`, BPF
`25.6/68.0/6.4%`, eunomia `35.0/41.8/23.2%`, AgentSkill
`82.6/17.4/0.0%`, and writing `35.9/56.8/7.3%`.

Five projects remain return-gap qualified, but AgentSkill changes from three
observed returns to zero. Therefore the main-paper sentence “all six cases now
carry return evidence” is no longer supported and is a stage-three wording
fix, even though the five-case median range stays 2--4.

### RQ6 local anchor: provenance closure

The old paper anchor came from
`bootstrap/step-0002-20260722T182000-0700/experiment-rq6-external-boundary/local-anchor.csv`.
The new anchor is generated in this directory from the same repaired,
status-preserving ledger used by RQ3. Its input SHA-256 is
`372584e828f1f46b8ae68b5381fcf90042a28397383f8adfa74ec3f638268ab0`.

| Project | Local share old -> new | Delta pp | Cross-module old -> new | Class |
|---|---:|---:|---:|:---:|
| ActPlane | 89.38% -> 88.97% | -0.41 | 10.62% -> 11.03% | M |
| academic-writing-skills | 88.50% -> 92.67% | +4.17 | 11.50% -> 7.33% | M |
| agentsight | 87.50% -> 87.01% | -0.49 | 12.50% -> 12.99% | M |
| agentskill-observability-paper | 97.87% -> 100.00% | +2.13 | 2.13% -> 0.00% | M |
| bpf-developer-tutorial | 93.01% -> 93.61% | +0.59 | 6.99% -> 6.39% | M |
| eunomia.dev | 79.82% -> 76.80% | -3.03 | 20.18% -> 23.20% | M |

Thus the paper headline changes from `79.8--97.9%` local and `2.1--20.2%`
cross-module to `76.8--100.0%` local and `0.0--23.2%` cross-module.

The audit independently reconstructed the final-HEAD pre-repair local shares
as `88.96, 87.21, 76.90, 93.61, 92.65, 100.00%` for
ActPlane/AgentSight/eunomia/BPF/writing/AgentSkill. Compared at the audit's
two-decimal precision, the repaired values move by at most about `0.20 pp`.
Therefore most of the old-paper-to-new-anchor movement above closes the stale
anchor provenance problem; the shell-boundary repair itself makes only a small
additional locality change.

## RQ4: accesses, components, and boundaries

| Project | Components old -> new | Boundaries old -> new | With first mutation old -> new | Artifact/module overlap defined old -> new | Class |
|---|---:|---:|---:|---:|:---:|
| agentsight | 31 -> 31 | 28 -> 28 | 17 -> 16 | 15/15 -> 14/14 | M |
| ActPlane | 24 -> 24 | 22 -> 22 | 14 -> 14 | 14/14 -> 14/14 | I |
| bpf-developer-tutorial | 29 -> 29 | 28 -> 28 | 21 -> 21 | 19/19 -> 19/19 | I |
| eunomia.dev | 18 -> 18 | 16 -> 16 | 8 -> 7 | 7/7 -> 6/6 | M |
| agentskill-observability-paper | 2 -> 2 | 1 -> 1 | 1 -> 1 | 1/1 -> 1/1 | I |
| academic-writing-skills | 17 -> 17 | 16 -> 16 | 7 -> 6 | 5/5 -> 5/5 | M |
| **Total** | **121 -> 121** | **111 -> 111** | **68 -> 65** | **61/61 -> 59/59** | M support / I headline |

Confirmed access rows change `57,792 -> 57,819` (`+27`). Component and
boundary formation does not depend on the repaired path identity, so the
per-project 121/111 breakdown is exactly stable. The three projects with at
least 20 boundaries are unchanged; the preregistered four-project gate still
stops.

## RQ1 extension: dormancy and revival

| Project | Action-gap revived n/N (%) old -> new; transitions; gap median/p90 | Time-gap revived n/N (%) old -> new; transitions; gap median/p90 | Class |
|---|---|---|:---:|
| Case A / agentsight | 1271/3267 (38.9) -> 1300/3271 (39.7); 6856 -> 6947; 349/4965.5 -> 351/4975 | 526/3267 (16.1) -> 533/3271 (16.3); 1086 -> 1098; 83.1/409.6 -> 82.9/409.7 | M |
| Case B / ActPlane | 662/1809 (36.6) -> 664/1725 (38.5); 3518 -> 3517; 469.5/5014 -> 468/4954.8 | 382/1809 (21.1) -> 380/1725 (22.0); 801 -> 795; 81.0/279.2 -> 80.8/279.4 | M |
| Case C / bpf | 42/170 (24.7) -> same; 73 -> 73; 271/661.2 -> same | 21/170 (12.4) -> same; 26 -> 26; 682.9/3234.8 -> same | I |
| Case D / eunomia | 174/360 (48.3) -> 175/368 (47.6); 805 -> 809; 449/2339 -> 448/2352.4 | 144/360 (40.0) -> 145/368 (39.4); 349 -> 351; 267.8/1800.4 -> 267.8/1800.4 | M |
| Case E / AgentSkill | 2/24 (8.3) -> same; 3 -> 3; 105/120.2 -> same | 0/24 (0.0) -> same; 0 -> 0; undefined -> undefined | I |
| Case F / writing | 13/116 (11.2) -> 13/118 (11.0); 16 -> 16; 167.5/360.5 -> same | 18/116 (15.5) -> 18/118 (15.3); 23 -> 23; 60.2/605.3 -> same | M |

| Paper-facing aggregate | Old | New | Class |
|---|---:|---:|:---:|
| Action-gap revived share, all identities | 8.3--48.3% | 8.3--47.6% | M |
| Action-gap revived share, multi-touch identities | 42.9--75.1% | 42.9--75.1% | I |
| Time-gap revived share, all identities | 0.0--40.0% | 0.0--39.4% | M |
| Time-gap revived share, multi-touch identities | 0.0--60.0% | 0.0--60.0% | I |
| Revival transitions, action/time thresholds | 11,271 / 2,285 | 11,365 / 2,293 | M |
| Mutation revivals, action/time thresholds | 348 / 41 | 345 / 31 | M |

The “revival is mostly renewed access, not necessarily editing” interpretation
is unchanged.

## RQ3 extension: rank turnover and cooling

### Turnover

| Paper-facing statistic | Old | New | Class |
|---|---:|---:|:---:|
| Primary adjacent window pairs | 3,372 | 3,367 | M |
| Micro top-1 change, artifact/module | 49.6 / 13.6% | 49.6 / 13.5% | M |
| Micro any-top-5 change, artifact/module | 91.5 / 42.0% | 91.5 / 41.9% | M |
| Micro mean replacement, artifact/module | 43.5 / 17.4% | 43.5 / 17.4% | I |
| Project-median top-1, artifact/module | 50.8 / 12.5% | 51.1 / 12.8% | M |
| Project-median any-top-5, artifact/module | 88.7 / 40.8% | 88.8 / 40.8% | M |
| Project-median replacement, artifact/module | 42.9 / 20.6% | 43.0 / 20.7% | M |
| Sensitivity adjacent pairs | 1,666 | 1,665 | M |
| Sensitivity micro top-1, artifact/module | 72.1 / 19.1% | 72.1 / 19.3% | M |
| Sensitivity micro any-top-5, artifact/module | 97.5 / 60.4% | 97.5 / 60.5% | M |

### Cooling

| Paper-facing statistic | Old | New | Class |
|---|---:|---:|:---:|
| Primary lag-1 endpoint, artifact/module | 57.0 / 84.9% | 56.9 / 84.8% | M |
| Primary lag-8 endpoint, artifact/module | 20.4 / 62.7% | 20.4 / 62.6% | M |
| Primary lag-8 continuous, artifact/module | 4.5 / 41.1% | 4.5 / 41.0% | M |
| Sensitivity lag-8 endpoint, artifact/module | 17.1 / 58.5% | 17.0 / 58.3% | M |
| Sensitivity lag-8 continuous, artifact/module | 1.9 / 32.1% | 1.9 / 31.9% | M |

All artifact-versus-module orderings and the cooling interpretation are
stable. These are synchronization-level numeric changes, not a qualitative
reversal.

## Sensitivity-only checks outside the requested full recompute

No full RQ7, user-question, or session-dynamics bundle was run here. The
spot-check script recomputes only the identity-dependent headline estimands
from the old and repaired projections and records them in
`sensitivity-spotcheck.json`.

### RQ7 workload

| Metric | Old | New | Class |
|---|---:|---:|:---:|
| Shell / all calls | 124,342 / 181,303 | unchanged | I |
| Native read/edit/write calls | 27,468 | 27,468 | I |
| Artifact-identity reads | 43,878 | 43,889 | P |
| Repeat reads | 20,482 (46.6794%) | 20,484 (46.6723%) | M count / I 46.7% |
| Unchanged repeats | 15,609 (76.2084%) | 15,610 (76.2058%) | M count / I 76.2% |
| Identity groups / repeated groups | 23,396 / 6,841 | 23,405 / 6,841 | M count |
| Actionable prefetches / exact hits / precision | 2,911 / 633 / 21.7451% | unchanged | I |

The main-paper RQ7 headline percentages, shell composition, and actionable
prefetch conclusion are immaterial at printed precision. However, the
supplement's exact “43,878 reads” count must become 43,889 when stage three
synchronizes RQ7. Event/command/timing estimands that do not depend on
artifact identity have unchanged input rows and are not candidates for a
repair-driven rerun.

### Supplement: user-originated artifact questions

| Spot-checked metric | Old | New | Class |
|---|---:|---:|:---:|
| Created documents | 1,066 | 1,093 | P |
| No later document action | 318 (29.8%) | 332 (30.4%) | P |
| Later-read documents | 665 (62.4%) | 682 (62.4%) | P count / I rate |
| Created code | 124 | 125 | P |
| No later code action | 14 (11.3%) | 14 (11.2%) | P |
| Later-read code | 97 (78.2%) | 97 (77.6%) | P |
| Confirmed reads, docs/code | 18,828/18,727 (43.5/43.2%) | 18,985/18,764 (43.5/43.0%) | P |
| Confirmed writes, docs/code | 9,701/2,261 (69.8/16.3%) | 9,691/2,239 (70.2/16.2%) | P |
| Ok+observed writes, docs/code | 13,653/7,982 (54.8/32.1%) | 13,645/7,960 (55.0/32.1%) | P |

These moves are material at paper precision, so the user-question section is
a stage-three full-recompute item. In addition, the old episode-collapse
contract aborts on repaired identity
`('ActPlane', '3dae89cd06ae', 'ActPlane:a00001076',
'a7ef88e1ee014ecd')` because one compound mutation now legitimately crosses
paths. Consequently source--test ordering and test/source churn are **not
declared stable** by this spot check; stage three must update that collapse
contract and rerun those subsections.

### Supplement: session dynamics and harness-shaped work

| Metric | Old | New | Class |
|---|---:|---:|:---:|
| Long roots | 233 | 233 | I |
| Five qualified reread medians | 16.7--28.9 pp | unchanged exactly | I |
| Non-composite reread sensitivity | five medians unchanged exactly | unchanged | I |
| Startup complete/predecessor roots | 362 / 348 | 362 / 348 | I |
| Startup narrow median/IQR | 10%; 0--10% | unchanged | I |
| Startup extended median/IQR/p90 | 20%; 10--30%; 60% | unchanged | I |
| Strict gross calls/share | 11,743 / 6.4770% | 11,744 / 6.4776% | M count / I 6.48% |
| Strict exclusive share | 5.9199% | unchanged | I |
| Broad share | 7.0357% | 7.0363% | I at 7.04% |
| Ordinary h50 opportunities/share | 22,779 / 52.289% | 22,794 / 52.259% | M count / I 52.3% |
| Bookkeeping h50 opportunities/share | 3,221 / 50.512% | unchanged | I |
| Failure chains/member calls | 16 / 58 | unchanged | I |

The session-dynamics paper headlines and conclusions are immaterial at printed
precision. Its exact raw bookkeeping counts should be regenerated if stage
three republishes the supporting bundle, but this repair alone does not
require a separate full scientific rerun.

## Stage-three handoff

Stage three may proceed for RQ1--RQ4 because the repaired projection,
downstream estimands, extensions, and RQ6 local anchor are complete and
repeatable. It must:

1. synchronize the material RQ1--RQ4 and extension numbers above;
2. replace the stale RQ3/RQ6 local-anchor provenance and remove the unsupported
   “all six return evidence” wording;
3. run the full user-question bundle after repairing the cross-path compound
   mutation collapse contract;
4. update the RQ7 exact artifact-read count (the printed percentages and
   prefetch result remain stable);
5. optionally regenerate session-dynamics raw support while retaining its
   unchanged paper-level conclusions.

No file under `docs/paper/` or `docs/evaluation.md` was modified in this stage.
