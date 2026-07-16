# Full Result: Literal Action Identity on Published Agent Trajectories

**Completed:** 2026-07-16T02:30:00-07:00

**State:** complete; fresh independent result review passed
**Paper question:** **RQ3 — How Accurate Are the Tags?**

## Tested hypothesis and root verdict

The approved hypothesis asked whether the fixed Qwen3.6-27B closed-taxonomy
tagger has higher eight-class operation-macro F1 than a fixed majority control
over the complete published ASE action-label population, with uncertainty
estimated by resampling whole trajectories within each of the three agent
frameworks.

The complete result is:

| Metric | Fixed tagger | Majority control | Difference |
|---|---:|---:|---:|
| Eight-class macro-F1 | **0.4984** | 0.0610 | **+0.4374** |
| Accuracy | **0.6277** | 0.3226 | +0.3051 |

The 10,000-replicate stratified whole-trajectory bootstrap interval for the
macro-F1 difference is **[+0.3802, +0.4941]**, with median +0.4331. Its lower
bound is above zero, so the tested hypothesis is **supported**.

This is direct positive evidence that the fixed closed-taxonomy tagger recovers
literal action identity substantially better than a no-semantic-signal control
on real software-engineering agent trajectories. The absolute macro-F1 is
moderate rather than near-perfect, and its class/framework boundaries remain
material.

## Complete population and execution validity

The official artifact contributes 120 real trajectories and 2,737 published
action labels: 218 AutoCodeRover, 1,108 OpenHands/CodeActAgent, and 1,411
RepairAgent iterations. All 2,737 labeled rows were scored. The source contains
2,751 visible iterations, so published-label coverage is 99.49%; the 14
unlabeled iterations were not guessed or removed with their trajectories.

The source labels are publication-derived rather than uniformly manual. The
ASE methodology first maps known agent tools to categories, then manually
inspects the remaining actions; one author performs the initial labeling and
ambiguous cases are resolved collaboratively. The eight output names come from
that ASE artifact. The fixed operational descriptions supplied to the tagger
come from the TraceView companion labeling guide.

Both complete repetitions emitted exactly 2,737 unique predictions from the
eight-value grammar:

- R1 completed in 693.20 seconds;
- R2 completed in 698.88 seconds;
- all 5,474 requests succeeded on their first attempt;
- no output was missing, duplicated, retried, or outside the grammar; and
- the two ordered prediction vectors agree on **2,737/2,737 rows (1.000)**.

Mean request time was 0.253 seconds in R1 and 0.255 seconds in R2; p95 was
0.331 and 0.335 seconds. These timings document the experiment runtime, not
RQ4 product overhead.

The visible-input file contains only opaque row ID, normalized thought/action
source, and source hash. Category, agent, trajectory, iteration, outcome, and
class counts occur only in the scorer manifest. `run` mode rejects any extra
visible-input field and has no source-root or category-file argument. This
separates the category column from inference, but it does not imply that every
visible action string is label-free; the sensitivity audit below records the
one exact-label exposure.

## Per-class result

| Published action | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Explore | 606 | 0.717 | 0.150 | 0.248 |
| Locate | 196 | 0.254 | 0.816 | 0.387 |
| Search | 364 | 0.877 | 0.937 | **0.906** |
| Reproduce | 153 | 0.160 | 0.340 | 0.218 |
| Generate Fix | 883 | 0.827 | 0.958 | **0.888** |
| Run tests | 294 | 1.000 | 0.150 | 0.260 |
| Refactor | 23 | 0.375 | 0.130 | 0.194 |
| Explain | 218 | 0.953 | 0.830 | **0.887** |

The tagger is strong on Search, Generate Fix, and Explain. Its main systematic
confusions are:

- 444 Explore rows predicted as Locate;
- 219 Run tests rows predicted as Reproduce;
- 101 Reproduce rows predicted as Generate Fix;
- 32 Generate Fix rows predicted as Reproduce; and
- 19 Refactor rows predicted as Generate Fix.

These errors are semantically coherent boundaries in the published taxonomy:
broad inspection versus target localization, pre-fix reproduction versus
post-fix validation, and behavior-preserving refactoring versus solution edits.
They explain why accuracy is higher than class-balanced macro-F1. They do not
invalidate the positive primary effect, but they prohibit describing the
tagger as uniformly accurate.

## Per-framework result

Per-framework macro-F1 is computed only over labels actually published for
that framework, so the rows expose transfer boundaries but are not numerically
identical label sets.

| Agent framework | Rows | Macro-F1 | Accuracy |
|---|---:|---:|---:|
| AutoCodeRover | 218 | **0.754** | **0.936** |
| OpenHands/CodeActAgent | 1,108 | 0.400 | 0.440 |
| RepairAgent | 1,411 | **0.677** | **0.728** |

The OpenHands gap is the dominant framework boundary. It contains all
Reproduce and Refactor labels and nearly all Run tests labels, and uses
general-purpose shell/editor actions whose intent depends more heavily on
thought context. The result therefore supports literal action tagging across
all three real frameworks in aggregate, not equal accuracy for every
framework.

## Input identifiability and metric interpretation

After the fixed AgentProf-compatible whitespace normalization and 1,600-
character window, the 2,737 scored rows contain 2,522 unique visible sources
and 215 duplicate rows. No identical normalized source window has conflicting
published labels. Thus a deterministic input-only tagger is not structurally
prevented from matching the released targets.

The full-release macro-F1 0.4984 is the exact point estimate for all published
labels. The bootstrap interval characterizes sensitivity/generalization across
the 120 trajectory units; it is not uncertainty about whether the complete
release was fully scored. Operations are never resampled as if independent.

An outer-audit source scan found 39 AutoCodeRover rows whose model-visible
action field is exactly the gold literal `Locate`. All 39 were predicted as
`Locate`. Excluding these rows without changing any prediction leaves 2,698
rows and yields macro-F1 `0.490445` and accuracy `0.622313`, versus majority
macro-F1 `0.061645` and accuracy `0.327279`. The positive conclusion therefore
does not depend on those exact-label rows, but the full-population result must
not be described as having blanket semantic target separation.

## Raw artifacts

| Artifact | SHA-256 |
|---|---|
| adapter | `489330f7ad11f8ac75dd65f82a628b2e98ed6d2675f2ebaee57069ed1dda1a0f` |
| visible inputs | `7842f94dadff01442f293174d19eb13839189f2f63b7e7c1db4214c3733a92ed` |
| scorer manifest | `1d514ae21eb2f863a55e2996841f3a04fdfc9b740dc24c19201bde34e7f8ddad` |
| R1 predictions | `90cd287c13b0cb521999471bacc9b4091e3fc307e30a0150e7a98a25f09a0d69` |
| R2 predictions | `d7c3a0b5dfa049d7258d5489470cd29e657e9c12dd058308fdf67edfa2249ebe` |
| scored result | `e0831b57500c5212e2605dcdc68d1ed1d5b6deb4475a2d3e9cb11dce0287468f` |

Raw files are under
`.agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/`.
The ASE source checkout is at
`e84f66f8d494e46ef336edfa137db25a629614fb`; the TraceView labeling companion
is at `4b55f40efb495b9f7801ce9d25f473ed5ee2dffb`.

The full commands below run from the repository root while the fixed model
server recorded in `preflight-report.md` is available:

```bash
python3 -B docs/tmp/build-and-evaluate/step-0032-20260716T010251-0700/experiment-001/literal_action_identity.py run \
  --inputs .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/visible-inputs.jsonl \
  --output .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/full/predictions-r1.jsonl \
  --url http://127.0.0.1:18083 --model qwen3.6-27b

python3 -B docs/tmp/build-and-evaluate/step-0032-20260716T010251-0700/experiment-001/literal_action_identity.py run \
  --inputs .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/visible-inputs.jsonl \
  --output .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/full/predictions-r2.jsonl \
  --url http://127.0.0.1:18083 --model qwen3.6-27b

python3 -B docs/tmp/build-and-evaluate/step-0032-20260716T010251-0700/experiment-001/literal_action_identity.py score \
  --manifest .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/scorer-manifest.json \
  --predictions \
    .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/full/predictions-r1.jsonl \
    .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/full/predictions-r2.jsonl \
  --output .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/full/scored-results.json \
  --bootstrap-replicates 10000 --bootstrap-seed 32025
```

## Scientific interpretation and paper boundary

Separate judgments required by the experiment skill are:

```text
run status: valid and complete
tested hypothesis: supported
research value: decisive additional literal-action evidence within RQ3
paper impact: additional RQ3 evidence; no thesis or story change
next paper decision: add one concise literal-action result to RQ3 and replace
  only the statement that action labels are wholly outside current evidence
```

The result is a standalone named-backend measurement through the experiment's
llama.cpp adapter, not a demonstration of an integrated AgentProf CLI tagging
path. It may support only the named zero-shot Qwen3.6-27B closed-taxonomy path,
published eight-action vocabulary, fixed current-thought/action input, and
three released software-engineering agent frameworks. It does not establish
phase-label accuracy, open-set labels, arbitrary taxonomy transfer, the
recurrence constructor, downstream localization, or every tagger backend.

No outcome in this experiment changes the fixed four RQs, operations and
operation stacks, three contributions, or the thesis: **Agent observability
needs profiling, not only debugging.**

## Root disposition

**VALID COMPLETE RUN / TESTED HYPOTHESIS SUPPORTED / DIRECT RQ3 LITERAL-ACTION
EVIDENCE / FRESH RESULT REVIEW PASSED.**
