# Result Report: Declared AgentBoard Task Identity

**Completed:** 2026-07-15T20:50:42-07:00
**Experiment state:** complete; awaiting independent result review
**Paper admission:** prohibited unless a later improved mechanism supplies
positive complete evidence

## Question And Fixed Decision Rule

This experiment tests one component inside fixed **RQ3 — How Accurate Are the
Tags?**: whether the shared AgentProf local tagger can assign all goals in the
official AgentBoard test release to a user-declared nine-family task taxonomy.
It does not test phase or action identity and cannot change RQ3.

The predeclared support rule required all 1,012 rows, 100% grammar validity,
better macro-F1 and accuracy than the majority control, and absolute candidate
macro-F1 and micro accuracy of at least 0.80. Open-vocabulary exact match was a
context ablation rather than a fair generic classification baseline; the
post-audit disclosure below further excludes it as a characterization of the
legacy raw session-tag path.

## Completed Execution

- Population: all 1,012 official test rows in canonical file and row order.
- Family counts: 134 AlfWorld, 112 BabyAI, 20 Jericho, 60 PDDL, 90
  ScienceWorld, 40 tool-operation, 60 tool-query, 245 webbrowse, and 251
  WebShop.
- Predictor input: goal text only. The official `task`, filename, row ID,
  subgoals, difficulty, and additional fields remained scorer-only.
- Mechanism: the approved ontology-plus-prompt-plus-grammar bundle in the
  shared Rust `LlamaTagger`, retaining raw and canonical fields separately.
- Model: Qwen2.5-3B-Instruct Q4_K_M through local llama.cpp, temperature zero.
- Repetitions: three complete independent no-cache runs.
- Completed profiles: 1,012/1,012 sessions and 1,012/1,012 operation samples
  in each repetition.
- Output validity: 3,036/3,036 declared predictions were in the exact grammar.
- Stability: both canonical and raw tags were identical in 1,012/1,012 rows
  across the three repetitions.

**Post-audit raw-path disclosure.** The declared `task_tag` request used the
approved goal-only input and is the only field used by the registered scorer.
The optional branch did keep a separate `session_tag`, but during these runs
that raw tag used the task request's kind, prompt-only input, and empty hints
rather than the pre-existing session request's title/CWD input and
source/model hints. Consequently the stored raw exact-match row and raw-tag
stability describe that run's auxiliary output, not preservation of the legacy
raw session-tagger semantics. They are not paper evidence. The outer audit
found this product-contract defect; the release path was repaired afterward
without changing the declared request or any `task_tag` result.

An earlier process was interrupted before it produced a profile and left a
zero-byte output. It was an execution interruption, not a scientific result;
the output was overwritten by the first complete no-cache repetition. No
partial prediction enters any metric below.

## Primary Results

| Method | Accuracy | Macro-F1 | Role |
|---|---:|---:|---|
| Declared-taxonomy AgentProf tagger | **0.3943** | **0.1912** | candidate |
| Raw open-vocabulary exact match | 0.0000 | 0.0000 | context ablation |
| Majority `webshop` | 0.2480 | 0.0442 | simple control |

The candidate improves substantially over the majority control but misses both
absolute 0.80 requirements. The tested hypothesis is therefore
**contradicted** for this mechanism.

## Per-Family Candidate Results

| Official emitted family | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| `alfworld` | 134 | 0.3822 | 0.6418 | 0.4791 |
| `babyai` | 112 | 0.0000 | 0.0000 | 0.0000 |
| `jericho` | 20 | 0.0000 | 0.0000 | 0.0000 |
| `pddl` | 60 | 0.0000 | 0.0000 | 0.0000 |
| `scienceworld` | 90 | 0.0769 | 0.0111 | 0.0194 |
| `toolop` | 40 | 0.0418 | 0.2500 | 0.0717 |
| `toolquery` | 60 | 0.1786 | 0.0833 | 0.1136 |
| `webbrowse` | 245 | 0.5517 | 0.1959 | 0.2892 |
| `webshop` | 251 | 0.6000 | 0.9920 | 0.7477 |

The candidate output distribution was heavily concentrated: `webshop` 415,
`toolop` 239, `alfworld` 225, `webbrowse` 87, `toolquery` 28,
`scienceworld` 13, `jericho` 2, `pddl` 2, and `babyai` 1. This is not a
grammar or nondeterminism failure; it is an assignment failure under weak
category grounding. The raw tagger produced meaningful open words such as
`pickup`, `visitredball`, `directions`, and `shopping`, but none was exactly
an official family alias.

## Interpretation Boundary

The complete result establishes that an enumerated grammar and short
project-authored family descriptions do not by themselves make the existing
3B local tagger an accurate literal task-family assigner. The result does not
challenge the paper thesis, the operation/operation-stack model, RQ3 itself,
the already supported boundary evidence, or the usefulness of raw semantic
tags. It also does not establish that a reference-grounded classifier,
supervised mapping, larger model, phase tagger, or action tagger would fail.

No negative number or narrower replacement claim is admitted to
`docs/paper/`. The next mechanism decision, if taken, must preserve the same
RQ3 hypothesis and public population while adding a principled source of
identity grounding rather than tuning labels or prompt wording against these
test answers.

## Raw Evidence

Raw machine outputs are under
`.agentsight/experiments/step-0031-agentboard-task-identity/`:

- full trace SHA-256:
  `f02ffbe334c067a2325504f33068f585872f2dbf71a4fcd97c536c1482eb4a81`
- scorer manifest SHA-256:
  `59a584e9e6ac8139e6f314065345136afa450bfbb03fe2e569642ba88fef63d2`
- repetition profile SHA-256 values:
  `613d5536ecd09e04f78e85df787ce33d61da5f29c9a5367e7978f936528acb4b`,
  `55b12da13ed6e90a904ee2161ef05f457291774953e1be1ba3c10b5b5a9b44c6`,
  and
  `e789f273842e1f8ff2769437eb2c7a22301e28550c6afb04c28fbcc2c7f4843e`
- scored result SHA-256:
  `5cb19615d2c60fbefb260f1b65c44fb26e151b2562c5620012a255d63b9b7f34`

The scoring adapter contains no model request, synonym map, label cleanup,
training, or evaluator. It validates the official population, invokes only
stored AgentProf output, and computes the predeclared confusion metrics.
