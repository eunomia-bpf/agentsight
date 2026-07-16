# Independent Result Review: AgentBoard Declared Task Identity

**Reviewed:** 2026-07-15
**Reviewer role:** fresh result reviewer; no experiment execution, product edit,
or paper edit
**Skill used:** `research-experiment-design` RESULT REVIEW
**Verdict:** **VALID RUN; TESTED HYPOTHESIS CONTRADICTED; NOT ADMITTED AS
POSITIVE PAPER EVIDENCE**

## Scope and independent recomputation

I reviewed the approved `experiment-plan.md`, its independent
`plan-review.md`, `preflight-report.md`, and `result-report.md`. I then
recomputed the registered metrics directly by joining `scorer-manifest.json`
to each of `full-profile-r1.json`, `full-profile-r2.json`, and
`full-profile-r3.json` on `session_id`. I did not use the reported metric
summary as an input to that recomputation.

The reviewed raw inputs have the recorded SHA-256 values:

- scorer manifest:
  `59a584e9e6ac8139e6f314065345136afa450bfbb03fe2e569642ba88fef63d2`;
- profiles R1/R2/R3:
  `613d5536ecd09e04f78e85df787ce33d61da5f29c9a5367e7978f936528acb4b`,
  `55b12da13ed6e90a904ee2161ef05f457291774953e1be1ba3c10b5b5a9b44c6`,
  and
  `e789f273842e1f8ff2769437eb2c7a22301e28550c6afb04c28fbcc2c7f4843e`.

## Completion and population

- The scorer manifest contains exactly 1,012 rows, 1,012 unique session IDs,
  and ordinals `0..1011` without a gap.
- Every profile contains exactly the same 1,012 unique session IDs. There is
  no missing, duplicate, or excluded scored row.
- The independently counted target population is: AlfWorld 134, BabyAI 112,
  Jericho 20, PDDL 60, ScienceWorld 90, tool-operation 40, tool-query 60,
  webbrowse 245, and WebShop 251.
- All 3,036 declared predictions are one of the nine allowed tags. Candidate
  grammar validity is therefore **3,036/3,036 = 1.000**.
- Candidate task tags are identical across R1/R2/R3 for **1,012/1,012** rows.
  Raw open-vocabulary session tags are also identical for **1,012/1,012**
  rows. These repetitions establish deterministic stability under the fixed
  run, not a sampling confidence interval for accuracy.

## Independently recomputed results

Using R1, with the predeclared nine-class macro average:

| Condition | Correct | Accuracy | Macro-F1 | Interpretation |
|---|---:|---:|---:|---|
| Declared-taxonomy candidate | 399/1,012 | 0.3942687747 | 0.1911946041 | candidate |
| Majority `webshop` control | 251/1,012 | 0.2480237154 | 0.0441629278 | lower-bound control |
| Raw open-vocabulary exact match | 0/1,012 | 0.0000000000 | 0.0000000000 | context only |

These values exactly match `result-report.md`. The candidate beats the simple
majority control on both registered metrics, but it misses both predeclared
absolute requirements, 0.80 macro-F1 and 0.80 micro accuracy, by a large
margin. Exact open-vocabulary matching remains only a context ablation and is
not treated as a fair classifier baseline.

The per-family recomputation also matches the report:

| Target | TP / support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| `alfworld` | 86 / 134 | 0.3822 | 0.6418 | 0.4791 |
| `babyai` | 0 / 112 | 0.0000 | 0.0000 | 0.0000 |
| `jericho` | 0 / 20 | 0.0000 | 0.0000 | 0.0000 |
| `pddl` | 0 / 60 | 0.0000 | 0.0000 | 0.0000 |
| `scienceworld` | 1 / 90 | 0.0769 | 0.0111 | 0.0194 |
| `toolop` | 10 / 40 | 0.0418 | 0.2500 | 0.0717 |
| `toolquery` | 5 / 60 | 0.1786 | 0.0833 | 0.1136 |
| `webbrowse` | 48 / 245 | 0.5517 | 0.1959 | 0.2892 |
| `webshop` | 249 / 251 | 0.6000 | 0.9920 | 0.7477 |

The key confusion pattern is not invalid syntax or instability. Predictions
collapse toward `webshop` (415 outputs), `toolop` (239), and `alfworld` (225).
In particular, 57/112 BabyAI goals map to `toolop` and 53/112 to `alfworld`;
52/90 ScienceWorld goals map to `toolop`; 31/60 PDDL goals map to `toolop`;
128/245 webbrowse goals map to `webshop`; and 48/134 AlfWorld goals map to
`toolop`. Conversely, 249/251 WebShop rows are correct. This is direct evidence
of weak nine-family grounding, not a malformed-output failure.

## Scientific judgment

The run is complete and valid for the approved, bounded hypothesis. The shared
declared task field engaged on every row, the raw field remained separately
available, the two controls have their predeclared roles, no row was excluded,
and the registered metrics are non-circular comparisons against the official
task-family target in the scorer manifest.

The result **contradicts the tested hypothesis**: the current fixed
ontology-plus-prompt-plus-grammar bundle with the local Qwen2.5-3B tagger does
not accurately assign the complete AgentBoard population to the declared
nine-family taxonomy. This is a decisive result for that tested mechanism, but
only a mechanism/workload boundary inside RQ3. It does not answer all of RQ3,
does not test phase or action identity, and is not a direct challenge to the
paper thesis or the existing operation-stack evidence.

```text
run status: valid
tested hypothesis: contradicted
research value: decisive for the tested declared-taxonomy mechanism
paper impact: mechanism/workload boundary; the literal-task component of RQ3 remains unsupported
next paper decision: do not present this run as positive RQ3 evidence; preserve the thesis and RQs, and require a materially better identity-grounding mechanism on the same public population before claiming accurate literal task identities
```

## Paper-admission decision

**Do not write these numbers into `docs/paper/` as support for tag accuracy.**
The experiment fails its approved positive admission rule. The valid internal
lesson is that enumerated decoding plus short family glosses is insufficient;
it does not authorize weakening the hypothesis, changing the RQ, narrowing the
paper story, or searching for an easier benchmark. A later experiment may
reuse the same official population and scorer to test a principled improvement,
but this review neither requires nor authorizes a particular redesign.
