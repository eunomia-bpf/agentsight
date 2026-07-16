# Experiment 002 Result: Qwen3.6-27B Declared AgentBoard Task Identity

**Completed:** 2026-07-15T23:57:58-07:00
**Scored:** 2026-07-15T23:59:00-07:00
**State:** complete and valid; independent result review complete
**Paper question:** **RQ3 — How Accurate Are the Tags?**

## Tested Hypothesis And Decision

The approved experiment asked whether the unchanged AgentProf declared-task
path, backed by the fixed local Qwen3.6-27B Q4_K_M artifact, would classify all
1,012 official AgentBoard goals into the nine declared task families with at
least 0.80 macro-F1 and 0.80 accuracy, above majority, with complete grammar
validity and exact stability across three repetitions.

The complete result is:

- **accuracy:** `742 / 1,012 = 0.7332015810`;
- **nine-class macro-F1:** `0.6951270608`;
- **majority accuracy / macro-F1:** `0.2480237154 / 0.0441629278`;
- **declared-tag stability:** `1.0` across all three repetitions;
- **grammar validity:** `3,036 / 3,036` declared outputs; and
- **coverage:** all `1,012 / 1,012` registered rows in every repetition.

The named 27B-backed path therefore substantially exceeds the majority control
and is fully stable and executable, but it misses both pre-registered 0.80
absolute bars. The tested strong hypothesis is **not supported**. This is a
valid, informative moderate positive result, not an invalid run and not a
complete positive answer to RQ3.

## Complete Population And Product-Path Validity

Each durable profile contains exactly:

- 1,012 sessions and 1,012 unique source session IDs;
- 1,012 nonempty raw `session_tag` values;
- 1,012 nonempty `task_tag` values in the exact nine-tag grammar;
- profile total weight 1,012; and
- 434 unique `session,task,prompt` stacks.

The ordered declared-tag vectors have the same SHA-256 in R1, R2, and R3:
`4ed0dcc8565c0f70bd8d7fc7393e557b6e760ca9f6ca29b47b58a60833918da5`.
The ordered raw-tag vectors likewise share
`6c9886bab0e840c035a1d212fbb92c726df8176e81a0a3eb7c6f2d22ab1fd8a3`.
Thus both candidate and raw outputs are exactly stable across repetitions;
different whole-profile hashes arise from generated metadata rather than tag
changes.

The three scored profile hashes are:

| Repetition | SHA-256 |
|---|---|
| R1 | `4eac2481bad27ed4d998e810f8e8e477ee20ec77d4c90ae1838b9b684382e2c8` |
| R2 | `4fece20530efd7a80f470476a3a9ec2e6d48e9367982814391c4b1a3b7ac519c` |
| R3 | `53f0d02d96eba9ea33a1c08bd45be81b430bc231f72de64abfa0338d28a27f59` |

The registered scorer summary is
`.agentsight/experiments/step-0031-agentboard-task-identity/27b/scored-results.json`
with SHA-256
`c7b5b6cc3db16822bf5ac977bf90781f1ecdc1ba1d425a7a0ccb2f2f16e207a5`.
It was run only after all three complete profiles passed the non-scoring
population, grammar, and weight checks.

## Per-Family Results

| Official family | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| `alfworld` | 134 | 0.708 | 0.940 | 0.808 |
| `babyai` | 112 | 0.794 | 0.893 | 0.840 |
| `jericho` | 20 | 0.636 | 0.700 | 0.667 |
| `pddl` | 60 | 1.000 | 1.000 | 1.000 |
| `scienceworld` | 90 | 0.853 | 0.322 | 0.468 |
| `toolop` | 40 | 0.338 | 0.550 | 0.419 |
| `toolquery` | 60 | 0.550 | 1.000 | 0.710 |
| `webbrowse` | 245 | 1.000 | 0.327 | 0.492 |
| `webshop` | 251 | 0.743 | 1.000 | 0.852 |

The path is perfect on PDDL and strong on ALFWorld, BabyAI, ToolQuery, and
WebShop. The main errors are systematic rather than random:

- 165 of 245 WebBrowse rows are assigned to WebShop (86), ToolOp (43), or
  ToolQuery (36), while all 80 predicted WebBrowse rows are correct;
- 61 of 90 ScienceWorld rows are assigned to ALFWorld (36) or BabyAI (25);
- 18 of 40 ToolOp rows are assigned to ToolQuery (13) or ScienceWorld (5).

These confusions explain why micro accuracy is materially higher than the
class-balanced macro-F1. They also show why grammar validity and determinism
cannot substitute for semantic accuracy.

## Controls And Backend Context

The majority `webshop` control has accuracy 0.2480 and macro-F1 0.0442. The
27B declared path improves those values by 0.4852 and 0.6510 absolute,
respectively.

Experiment 001's unchanged 3B-backed path reached accuracy 0.3943 and
macro-F1 0.1912. The fixed 27B backend therefore improves the same declared
mechanism by 0.3389 accuracy and 0.5039 macro-F1. This comparison identifies a
backend substitution, not parameter count as the isolated cause, because the
models also differ in generation, architecture, and training.

The 27B raw open-vocabulary exact-match context scores zero against official
task-family strings. It is not a generic classifier baseline: its prompt asks
for a useful one-word description, not an official family identifier. It
shows only that a declared vocabulary is necessary when literal canonical IDs
are the requested product field.

## Runtime Incidents And Valid Output Boundary

Three infrastructure prefixes were excluded before scoring:

1. the original PTY-owned server and client were terminated together by the
   surrounding tool-session lifecycle and emitted no profile;
2. the first independent server build later faulted inside
   `libcuda.so.575.57.08`, after which AgentProf received an unexpected EOF and
   emitted no profile; and
3. after the repaired runtime completed R1 and R2, its long-lived CUDA process
   faulted during an initial R3 prefix; restarting the same runtime before R3
   allowed the complete third repetition to finish.

No partial profile exists for any failed prefix, and no prefix was scored. The
repair retained llama.cpp version 9870 at commit `2d973636e`, the same model
artifact, full offload, context size, Jinja template, and reasoning settings,
but compiled with CUDA graphs disabled and disabled server-side context
checkpoint/RAM caches. These execution-only changes reduced process RSS after
preflight from the failed service's 31.8-GiB peak to about 1.4 GiB and did not
change any predictor-visible input, model weight, decoding rule, taxonomy,
AgentProf binary, or metric. R1/R2 used one repaired server lifetime; R3 used a
fresh process with the identical repaired binary and arguments. Exact tag
identity across all three repetitions confirms output stability across that
process restart.

## Scientific Interpretation And Paper Boundary

This experiment directly measures literal task-family identity, filling a
different part of RQ3 from OSWorld's session-local operation partition. It
supports four bounded statements:

1. a user-declared canonical taxonomy is materially more useful for literal
   task IDs than unconstrained one-word tags;
2. the named 27B-backed AgentProf path is deterministic, grammar-valid, and
   substantially above a majority control on the complete public population;
3. backend quality materially changes assignment accuracy for this unchanged
   mechanism; and
4. the current short-gloss zero-shot path does not yet reach the experiment's
   strong 0.80 accuracy standard across all nine families.

It does not establish phase labels, action labels, operation boundaries,
open-vocabulary semantic names, unknown-taxonomy generalization, or all of
RQ3. It also does not authorize changing the fixed thesis, four RQs, paper
story, or recurrence constructor.

The pre-registered strong support rule is binding for the hypothesis verdict,
but missing it does not erase the observed complete-population effect relative
to controls. Whether the moderate positive result belongs in the reader-facing
paper should be decided after the independent raw-result review and whole-paper
evidence synthesis. If admitted, the paper must report the actual 0.733
accuracy and 0.695 macro-F1 and must not call the task assignment uniformly
accurate or claim that RQ3 is completely solved.

## Root Result Verdict

**VALID / STRONG HYPOTHESIS NOT SUPPORTED / MODERATE POSITIVE MECHANISM
EVIDENCE / INDEPENDENT REVIEW COMPLETED.**

The independent reviewer reconstructed every population and metric directly
from the three raw profiles and scorer manifest. It confirmed the run as valid,
the registered `0.80` hypothesis as contradicted, and the complete measurement
as scientifically admissible bounded RQ3 evidence. See
[`result-review.md`](result-review.md).

## Post-Audit Product Repair

The step-level outer audit independently confirmed every `task_tag` metric but
found that the optional branch's auxiliary raw `session_tag` did not preserve
the pre-existing session request semantics: it used the task kind, goal-only
text, and no source/model hints. The scorer never reads that field, and the
declared-task request remained exactly the approved goal-only request, so the
reported accuracy, macro-F1, grammar validity, and stability remain valid.

The release implementation now computes the legacy raw session tag through
the original `session` kind, title/CWD/prompt input, and source/model hints,
then computes `task_tag` separately through the byte-equivalent declared-task
request. A focused contract test distinguishes those inputs. No complete
AgentBoard rerun is required because no predictor-visible declared input,
choice, prompt, grammar, model setting, output, or scorer changed.
