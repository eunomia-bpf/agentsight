# Independent Result Review: 27B AgentBoard Task Identity

**Reviewed:** 2026-07-16T00:05:09-07:00
**Reviewer role:** fresh result reviewer; no experiment execution, scorer reuse,
paper editing, product editing, or story editing
**Skill used:** complete `research-experiment-design` RESULT REVIEW protocol
**Verdict:** **VALID RUN; REGISTERED HYPOTHESIS CONTRADICTED; BOUNDED
SUPPORTING RQ3 EVIDENCE**

## Separate Judgments

```text
run status: valid
tested hypothesis: contradicted
research value: supporting
paper impact: additional RQ evidence plus a named-backend/workload boundary
next paper decision: do not claim the registered >=0.80 result; return the
  complete measurement to the orchestrator, which may report it only as a
  bounded Qwen3.6-27B closed-taxonomy AgentBoard result
```

The three complete profiles independently recompute to **0.695127 macro-F1**
and **0.733202 accuracy** in every repetition. They exceed the fixed majority
control by large margins but miss both registered 0.80 thresholds. Therefore
the strong tested hypothesis is contradicted. The threshold miss determines
the hypothesis verdict; it does not invalidate or make the complete result
scientifically inadmissible.

## Inputs and Independent Method

I read the approved plan, its full plan review and revision, the real preflight
report, the complete 1,012-row scorer manifest, all 3,036 raw session records
in the three durable 27B profiles, the declared-task inference path, and only
the runtime logs needed to distinguish failed prefixes from completed runs. I
did not call, import, or use values from `scored-results.json` while deriving
this review.

The independently reviewed raw inputs were:

| Artifact | SHA-256 |
|---|---|
| `scorer-manifest.json` | `59a584e9e6ac8139e6f314065345136afa450bfbb03fe2e569642ba88fef63d2` |
| `27b/full-profile-r1.json` | `4eac2481bad27ed4d998e810f8e8e477ee20ec77d4c90ae1838b9b684382e2c8` |
| `27b/full-profile-r2.json` | `4fece20530efd7a80f470476a3a9ec2e6d48e9367982814391c4b1a3b7ac519c` |
| `27b/full-profile-r3.json` | `53f0d02d96eba9ea33a1c08bd45be81b430bc231f72de64abfa0338d28a27f59` |

I joined each profile session to the manifest by exact `session_id`, treated
manifest `target_tag` as the independent truth, and used the stored
`task_tag` as the prediction. For each of the nine registered labels I
computed

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2 * precision * recall / (precision + recall)
```

and averaged the nine per-label F1 values without support weighting. Accuracy
is the exact-correct count divided by all 1,012 rows. The majority control
predicts `webshop` for every row. This calculation does not use a model output
to define correctness and is not circular.

The manifest has 1,012 unique session IDs and 1,012 unique ordinals. Its goal
hashes all recompute exactly. The 100 apparent differences between manifest
`task` and `target_tag` are only the registered canonicalizations
`tool-operation` to `toolop` (40 rows) and `tool-query` to `toolquery` (60
rows); the canonical target remains fixed and predictor-hidden.

## Completion, Mechanism Engagement, and Grammar

Each repetition independently satisfies all completion checks:

| Check | R1 | R2 | R3 |
|---|---:|---:|---:|
| sessions | 1,012 | 1,012 | 1,012 |
| unique session IDs | 1,012 | 1,012 | 1,012 |
| missing / extra manifest IDs | 0 / 0 | 0 / 0 | 0 / 0 |
| sessions in manifest order | yes | yes | yes |
| profile total weight | 1,012 | 1,012 | 1,012 |
| one prompt per session | 1,012 | 1,012 | 1,012 |
| prompt text equals manifest goal | 1,012 | 1,012 | 1,012 |
| prompt hash matches goal hash prefix | 1,012 | 1,012 | 1,012 |
| nonempty raw session / prompt tags | 1,012 / 1,012 | 1,012 / 1,012 | 1,012 / 1,012 |
| nonempty declared task tags | 1,012 | 1,012 | 1,012 |
| declared tags in nine-label grammar | 1,012 | 1,012 | 1,012 |
| run-log status / warnings | `ok` / none | `ok` / none | `ok` / none |

Thus grammar validity is **3,036/3,036**. This is a path-engagement and
correctness check, not semantic evidence: the enumerated decoder constrains
the output vocabulary, while semantic accuracy comes only from comparison to
the predictor-hidden manifest target.

The source path confirms that declared assignment receives the prompt text
and the nine user-declared tag descriptions, not manifest task, filename, ID,
subgoals, difficulty, or targets. `--no-cache` clears and disables the loaded
tag cache. Runtime evidence is also consistent with uncached execution: the
fresh R3 server recorded exactly 3,036 completed request markers, while the
server used for the durable R1 and R2 profiles contains both complete
three-call-per-row runs in addition to separately identifiable preflight and
failed-prefix traffic.

## Independently Recomputed Results

All three repetitions produce the same values:

| Repetition | Correct / total | Accuracy | Macro precision | Macro recall | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| R1 | 742 / 1,012 | 0.733202 | 0.735816 | 0.747990 | 0.695127 |
| R2 | 742 / 1,012 | 0.733202 | 0.735816 | 0.747990 | 0.695127 |
| R3 | 742 / 1,012 | 0.733202 | 0.735816 | 0.747990 | 0.695127 |

Per-family metrics, recomputed separately for each repetition and identical
across all three, are:

| True family | Support | Predicted | TP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| `alfworld` | 134 | 178 | 126 | 0.707865 | 0.940299 | 0.807692 |
| `babyai` | 112 | 126 | 100 | 0.793651 | 0.892857 | 0.840336 |
| `jericho` | 20 | 22 | 14 | 0.636364 | 0.700000 | 0.666667 |
| `pddl` | 60 | 60 | 60 | 1.000000 | 1.000000 | 1.000000 |
| `scienceworld` | 90 | 34 | 29 | 0.852941 | 0.322222 | 0.467742 |
| `toolop` | 40 | 65 | 22 | 0.338462 | 0.550000 | 0.419048 |
| `toolquery` | 60 | 109 | 60 | 0.550459 | 1.000000 | 0.710059 |
| `webbrowse` | 245 | 80 | 80 | 1.000000 | 0.326531 | 0.492308 |
| `webshop` | 251 | 338 | 251 | 0.742604 | 1.000000 | 0.852292 |

The complete confusion matrix is below. Rows are true labels and columns are
predicted labels.

| True \ Pred. | alf | baby | jeri | pddl | sci | op | query | browse | shop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `alfworld` | 126 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| `babyai` | 12 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `jericho` | 4 | 1 | 14 | 0 | 0 | 0 | 0 | 0 | 1 |
| `pddl` | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 |
| `scienceworld` | 36 | 25 | 0 | 0 | 29 | 0 | 0 | 0 | 0 |
| `toolop` | 0 | 0 | 0 | 0 | 5 | 22 | 13 | 0 | 0 |
| `toolquery` | 0 | 0 | 0 | 0 | 0 | 0 | 60 | 0 | 0 |
| `webbrowse` | 0 | 0 | 0 | 0 | 0 | 43 | 36 | 80 | 86 |
| `webshop` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 251 |

The main error structure is not random noise. `scienceworld` is often mapped
to embodied or navigation families, and `webbrowse` is often mapped to
`webshop`, `toolop`, or `toolquery`. Conversely, `pddl`, `toolquery`, and
`webshop` have perfect recall on this population. This supports a bounded
closed-taxonomy signal but not uniformly accurate identity across families.

## Stability

All 1,012 declared predictions are exactly equal across R1, R2, and R3:

- R1 versus R2 differences: 0;
- R1 versus R3 differences: 0;
- R2 versus R3 differences: 0; and
- rows with one common declared prediction across all three: 1,012/1,012.

The raw session and raw prompt tags are also pairwise identical across all
repetitions. Therefore run-to-run exact stability is **1.000** for the tested
runtime and decoding configuration. This establishes determinism, not
semantic correctness or robustness to a different model artifact, prompt,
machine, or taxonomy.

## Controls and Context

The fixed `webshop` majority control has:

| Accuracy | Macro precision | Macro recall | Macro-F1 |
|---:|---:|---:|---:|
| 0.248024 | 0.027558 | 0.111111 | 0.044163 |

The 27B candidate exceeds it by 0.485178 accuracy and 0.650964 macro-F1. The
majority row is a valid lower-bound control on the same population, but not a
strong external classifier baseline.

As registered context rather than a fair causal baseline, I also independently
recomputed the existing three 3B profiles: every repetition gives 0.394269
accuracy and 0.191195 macro-F1. The 27B-backed path is higher by 0.338933
accuracy and 0.503932 macro-F1. Because model generation, training,
architecture, and compute all differ, this comparison establishes backend
sensitivity and the performance of the named artifact; it does not identify
parameter count as the cause or establish a scaling law.

The raw open-vocabulary session and prompt outputs have zero exact matches to
the nine canonical family strings, but this is not a meaningful baseline: that
path was instructed to emit local action/topic words rather than one of the
nine family names. It must not be used to claim declared-taxonomy superiority.

## Registered Decision Rule

| Registered condition | Recomputed outcome | Pass? |
|---|---:|:---:|
| all 1,012 rows in each repetition | 1,012 in R1, R2, R3 | yes |
| macro-F1 at least 0.80 | 0.695127 | **no** |
| accuracy at least 0.80 | 0.733202 | **no** |
| exceed majority on both metrics | +0.650964 F1; +0.485178 accuracy | yes |
| 3,036/3,036 declared outputs grammar-valid | 3,036/3,036 | yes |

Because both absolute performance conditions are conjunctive and both fail,
the registered tested hypothesis is **contradicted**, not supported or
inconclusive. Stability, grammar, and majority improvement cannot substitute
for either 0.80 bar.

## Runtime Failures and Deviations

The durable R1, R2, and R3 output timestamps are respectively
`2026-07-16T06:39:50Z`, `06:46:54Z`, and `06:57:52Z`; their adjacent run logs
each report 1,012 sessions, 1,012 samples, `status: ok`, and no warnings.

Earlier runtime-lifetime and CUDA failures ended with `Unexpected EOF` after
partial request prefixes. They produced no completed status log or profile
eligible for scoring. The executor restarted the affected repetition from the
beginning. The final R3 used a fresh server whose log contains exactly 3,036
completed requests and a clean exit. These failures change wall-clock cost but
not the fixed model, prompt, taxonomy, population, scorer, or durable
predictions. Excluding partial prefixes is required by the approved completion
rule and introduces no row selection.

## Validity, Leakage, Fairness, and Uncertainty

- **Metric correctness:** independently labelled manifest targets define the
  nine-class accuracy and macro-F1. The constrained grammar is not used as a
  semantic oracle.
- **Coverage and exclusions:** the full released 1,012-row population is
  scored; there are no exclusions, deduplications, missing IDs, or result-
  selected families.
- **Information boundary:** the predictor sees the natural-language goal and
  fixed taxonomy descriptions. It does not see source task, filename, row ID,
  target, subgoals, difficulty, or scorer fields.
- **Adaptivity:** moving from the failed 3B backend to one already-used 27B
  backend is an adaptive follow-up, but no row label was used to tune a prompt,
  example, description, alias, threshold, or cleanup rule.
- **Baseline fairness:** majority is only a null/lower-bound control and the 3B
  row is only backend context. This experiment cannot claim superiority over
  a strong supervised or official AgentBoard classifier.
- **Population uncertainty:** these values are exact for the complete released
  AgentBoard test population. Three identical runs show no decoding variance,
  but they are not three independent data samples and must not be used to
  shrink a population confidence interval.
- **External validity:** unknown foundation-model exposure to public
  AgentBoard data remains possible. The test is closed-set assignment into
  nine described families, not open-vocabulary name induction, undeclared-
  family generalization, or transfer to new benchmark families.
- **Class balance:** macro-F1 appropriately prevents the 245 `webbrowse` and
  251 `webshop` rows from dominating accuracy, but the 20-row `jericho` family
  remains a small family-specific estimate.

## Scientific Admissibility and Paper Scope

This is a valid, complete, target-blind measurement with a substantial margin
over the lower-bound control. It is therefore scientifically admissible as
**bounded supporting RQ3 evidence despite missing the 0.80 bar**. A
predeclared threshold separates supported from contradicted hypotheses; it is
not a rule for suppressing a valid measurement.

The admissible statement is narrow and exact: on all 1,012 released AgentBoard
test goals from nine declared families, the fixed Qwen3.6-27B-backed declared
taxonomy path reaches 0.695 macro-F1 and 0.733 accuracy, with 1.000 exact
three-run stability, versus 0.044 and 0.248 for the majority control. It may
also state that performance varies materially by family.

The result does **not** support the registered claim of at least 0.80 accuracy,
uniformly accurate literal tags, open-vocabulary naming, phase or action
identity, group-boundary quality, unseen-family generalization, a capacity
causal effect, or all of RQ3. It is one experiment inside fixed RQ3 and does
not challenge the thesis, change an RQ, alter the recurrence algorithm, or
authorize a story rewrite.

The approved plan predeclared no automatic paper insertion for a threshold
miss, and a result reviewer cannot edit or authorize edits to the paper. Return
the measurement to the orchestrator. If the orchestrator routes it to WRITE,
the paper must report the bounded numbers and named backend without calling
the registered hypothesis supported. If it remains internal, the paper must
retain its current boundary that literal tag-name accuracy is outside the
reported evidence; it cannot silently rely on this experiment for a broader
claim.
