# ToolSafe RQ2 Real Preflight Review — Round 2

**Review method:** serial independent `research-experiment-design` REAL
PREFLIGHT review  
**Reviewed plan:** `experiment-plan.md`, Revision 3  
**Prior review:** `preflight-review.md` — REVISE  
**Verdict:** **PASS**  
**Full run authorized:** **YES**

## Decision

All five Round-1 must-fix items are closed in the repaired runner and fresh
128-neutral-prefix preflight. Representative direct checks also show no
regression in target-label isolation, real AgentProf execution, profile-count
verification, matched fallback, paired bootstrap construction, or conservative
metrics.

The preflight remains dependency evidence only. Its partial-data diagnostic
numbers are correctly marked `NOT_EVALUATED_PREFLIGHT` and cannot support,
contradict, narrow, or rewrite RQ2, the four-RQ program, positive hypothesis,
thesis, canonical story, or paper.

## Round-1 Closure Audit

| Round-1 must-fix | Status | Direct Round-2 evidence |
|---|---|---|
| Preserve exact raw-tool identity | **CLOSED** | `parse_tool()` now returns the case-sensitive parsed string after only the approved surrounding cleanup. The source projection contains the original mixed-case values; for example, `CovertFundReallocation` remains exactly that string in the scientific `risk_tool` key. Only operation files encode tool strings as lowercase-safe `utf8hex_<UTF-8 bytes>`. The runner checks decoding equality, equal raw/encoded unique counts, injectivity, and reversibility for every target/reference and primary/compatibility profile. Fresh profile reports contain `one_to_one: true` and `reversible: true`; the encoding therefore preserves the exact-identity partition at the AgentProf boundary. |
| Use the approved neutral-prefix enlargement | **CLOSED** | `selected_rows()` now selects `ordered[family][:clusters_per_family]`, not equal intervals. The fresh command uses the first 128 clusters in each family. This is the approved enlargement of the failing first-32 neutral prefix; order is unchanged, the preflight report records why 32 and 64 did not exercise both AgentHarm strict classes, and every bootstrap header contains exactly 128 target clusters. The full run omits this subset argument and remains complete-data. |
| Record the actual AgentProf version | **CLOSED** | The runner invokes the supplied binary with `--version`, validates the response, requires all fold versions to agree, and records `agentpprof 0.2.37` in each fold profile/status, combined `metrics.json`, generated report, and terminal `execution-status.json`. |
| Implement the exact decision branches and evidence | **CLOSED** | `score_all()` now records the full decision evidence: point raw-profile gain, family positivity/reversal, paired AP CIs, work metrics, compression, compatibility-only gain, risk-only stability, unsafe-only reversal, source coverage, official reproduction, AgentProf counts, and label isolation. A full strict family reversal or failure to beat raw tool is `CONTRADICTED`; full strict support plus unsafe-only reversal is `MIXED`; `SUPPORTED` is reachable only after all strong-support conditions and complete-run checks. A subset is unconditionally `NOT_EVALUATED_PREFLIGHT`. The fresh output records both family and unsafe-only reversals without misclassifying the preflight as a scientific result. |
| Produce a clean terminal output directory | **CLOSED** | The coordinator removes stale `need-more.json`, terminal status, metrics, and report files before a fresh run; successful scoring also removes `need-more.json`. The fresh top-level preflight directory contains exactly `report.md`, `metrics.json`, and `execution-status.json`; no contradictory stale terminal artifact remains. |

## Regression Audit

### Target-label isolation

- The 7,182-row source projection retains one allowlisted key set and no
  `score`, full `meta_sample`, `attack_success`, `aggressive`, or
  `attacker_tool` field. Labels remain in three separate family tables.
- Each prediction file contains one held-out target family and no label field.
  `predict-fold` still requires exactly the two complementary reference-family
  label files, rejects a wrong reference-family set, and rejects target-ID
  overlap.
- Bootstrap densities, fallback choices, and label-blind target draws remain
  predictor outputs. `score-all` receives held-out labels only after ordinary
  and bootstrap predictions exist.
- One combined scoring process still loads all three target-family tables only
  after every fold has completed. This is scientifically equivalent to three
  serial scorers and does not reintroduce a prediction path from target labels.

### Real AgentProf and exact grouping

- Fresh artifacts contain real AgentProf JSON profiles for all seven declared
  stack views, target/reference sides, two populations, and three folds.
- The supplied binary is invoked through `--operation-file`, `--view
  operations`, explicit stack fields, JSON output, and deterministic output.
- The runner compares every emitted stack counter with a separately rebuilt
  operation-file counter. Representative fresh inspection confirmed the
  profile total equals the operation-file row count and the profile group count
  equals the saved independent count.
- Raw scientific keys use exact strings, while the AgentProf operation file
  contains their reversible UTF-8 hex boundary representation. Fresh reports
  show equal raw and encoded unique counts in every inspected profile, so the
  baseline is neither lowercased nor merged.

### Matched baselines and fallback

- Semantic, risk-conditioned raw-tool, and risk-only views still use identical
  reference labels, Laplace smoothing, and risk-level information.
- Seen refined keys use their own reference density. Unseen semantic and
  risk/tool keys both back off to the corresponding risk density; only a
  missing risk key can use global prevalence.
- Fresh primary/strict fallback counts include semantic exact/risk-backoff,
  risk/tool exact/risk-backoff, and risk exact paths. A representative unseen
  risk/tool key received exactly the same risk-level score and support as its
  risk-only entry.
- Exact-tool-only remains a lower-bound control, and interaction/direct views
  remain descriptive; neither can change the main verdict.

### Bootstrap and metrics

- Every fold bootstrap artifact has seed 4203, 128 target clusters, attempts
  0--199, and 200 replicates. Every checked target draw has multiplicity sum
  128.
- Family draws remain deterministic in `(seed, attempt, family)`, shared across
  methods and reused consistently when a family is target versus reference.
- All primary/compatibility and strict/unsafe-only cells reached 200 valid
  paired replicates.
- The whole-tie-block AP, complete-block R@30%, and whole-crossing-block
  work-to-50% implementation is unchanged. Fresh generated Markdown values
  match `metrics.json`, and profile/group totals agree with the selected
  1,081-operation primary sample.
- Group count, top-five work/recall, maximum group share, family tables,
  paired intervals, unsafe-only results, and fallback reports remain present.

## Accepted Preflight-Only Repair

The approved first-32 neutral prefix could not exercise a two-class AgentHarm
strict scoring path. Enlarging the same prefix to 128 is a legitimate REAL
PREFLIGHT path repair: it changes neither ordering nor the full-run population,
and it is not interpreted as a result. The prior equal-interval sampler has
been removed.

## Must-fix Items

None.

## Authorization

The full Revision 3 command over all 7,182 released rows is authorized. It must
retain the approved seed, both populations, both label mappings, all three
folds, both matched baselines, declared controls, exact source/AgentProf checks,
10,000 valid paired replicates per required cell, and full official TS-Guard
metric reproduction. Any execution defect should repair and rerun only the
affected stage; no result from this experiment authorizes changing the fixed
RQ2, four RQs, positive hypothesis, thesis, canonical story, or paper during
the EXPERIMENT gate.
