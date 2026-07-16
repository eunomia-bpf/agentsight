# Independent Plan Review: 27B AgentBoard Task Identity

**Reviewed:** 2026-07-15T21:05:01-07:00
**Reviewer role:** fresh scientific plan reviewer; no experiment execution,
plan editing, product editing, or paper editing
**Skill used:** complete `research-experiment-design` PLAN REVIEW protocol
**Verdict:** **REVISE**

## Inputs And Scope

I read the complete `research-experiment-design` skill and plan template, the
current Experiment 002 plan, the final approved Experiment 001 plan, and the
fresh independent Experiment 001 result review. I also checked the local 27B
artifact and its prior complete Step 0019 use, the reused AgentBoard trace and
scorer paths, the current AgentProf CLI surface, and the existence of the
completed Experiment 001 outputs.

The proposed follow-up is scientifically decision-relevant and substantially
well controlled. It keeps the complete 1,012-row official population, predictor
input, scorer manifest, taxonomy, descriptions, prompt, grammar, decoding,
three repetitions, shared Rust product path, metrics, and positive decision
rule unchanged. The local 27B artifact exists at the stated size and SHA-256,
and the same llama.cpp version and model artifact already completed the real
Step 0019 workflow with Jinja and reasoning disabled. No AgentBoard target,
filename, ID, subgoal, difficulty, or additional-info field is made visible to
the model.

The experiment is also a legitimate one-shot follow-up after the valid 3B
contradiction. Selecting one previously used, fixed 27B backend after observing
the aggregate 3B failure is an adaptive scientific follow-up, but it is not
row-label training, prompt tuning, example construction, or prediction cleanup.
The plan discloses that sequence and forbids changing any label description,
prompt, taxonomy, model setting, or threshold after approval. Unknown public
AgentBoard exposure during foundation-model pretraining is already bounded.
No new split, benchmark, evaluator, or reproducibility protocol is needed.

Two small defects remain. One affects the causal interpretation and one makes
the real run/output path ambiguous. Both can be repaired entirely in the plan
without changing any experimental cell.

## Must-Fix Items

### 1. Treat the intervention as a fixed model-backend substitution, not an identified capacity effect

At the system level the plan changes one component: the model artifact. That is
a clean comparison of the 3B and 27B-backed versions of the same declared-
taxonomy mechanism. It is **not**, however, a controlled causal test of
parameter capacity alone. Qwen2.5-3B-Instruct and Qwen3.6-27B differ in model
generation, training data and recipe, architecture details, and capacity. The
current title and phrases such as “model-capacity hypothesis,” “capacity
context,” and “replacing only model capacity” over-identify the cause of any
difference.

Revise only the interpretation wording:

- name the manipulated component as the fixed **model backend/artifact**;
- describe greater capacity as the motivation or one plausible explanation,
  not the experimentally isolated cause; and
- keep the already correct paper boundary that a passing result supports this
  named 27B-backed AgentProf cell, not a scaling law or a universal larger-model
  claim.

The hypothesis, population, requests, metrics, thresholds, and run matrix do
not need to change.

### 2. Name a separate 27B raw-output path and the exact existing command path

The plan identifies the reused input trace and scorer manifest, but it does not
identify the Experiment 002 profile/result filenames or give the concrete
AgentProf invocation. The reused directory already contains
`full-profile-r1.json` through `full-profile-r3.json` and
`scored-results.json` for the 3B run. “Run the full trace three times” therefore
leaves open whether the executor overwrites the valid Experiment 001 evidence,
which files constitute the three completed 27B repetitions, and what exact
artifacts the independent result reviewer must recompute.

Add one compact execution block that:

- gives the copy-pastable llama.cpp server command (or its exact arguments),
  including the stated 27B artifact, alias, Jinja mode, and reasoning-off
  configuration;
- gives the unchanged AgentProf preflight/full command shape with the fixed
  nine `--task-choice` values, trace, model alias, cache disabled, and output;
- writes the 27B preflight, three full profiles, and scored summary to distinct
  Experiment 002 filenames or a distinct subdirectory, leaving every 3B file
  untouched; and
- makes those named three 1,012-session profiles plus the unchanged manifest
  the input to the existing thin scorer and later result review.

This is ordinary executable plan detail required by the skill, not a new
runner, manifest, freeze protocol, checker, or provenance layer. No AgentProf
source change is required or allowed.

## Findings That Do Not Block Execution After Revision

- **Single changed system component:** yes. Once causal wording is corrected,
  the only manipulated component is the fixed model artifact; every experiment
  input and AgentProf mechanism remains matched.
- **Population and scorer:** fair and byte-reused. The full official census is
  used without filtering, deduplication, or result-conditioned exclusions.
- **Target-label leakage:** none enters the predictor or configuration. The
  follow-up is adaptively motivated by the reported 3B failure, but there is no
  test-label-derived rule, example, glossary change, prompt change, or model
  setting change.
- **Comparison fairness:** adequate for the actual question. The 3B row is
  context, not a compute-matched baseline or superiority claim; the primary
  decision is the predeclared absolute 0.80 macro-F1 and accuracy criterion for
  the 27B-backed mechanism.
- **Controls and metrics:** the majority control, raw-tag context row, complete
  confusion matrix, per-family metrics, grammar validity, coverage, and
  stability retain their approved roles. No additional baseline is needed.
- **Repetitions and completion:** three complete no-cache repetitions and the
  1,012-session/1,012-sample rule are scientifically sufficient. Partial runs
  are correctly excluded and execution failures are repairs, not scientific
  observations.
- **Paper impact:** correctly bounded to one literal AgentBoard task-family
  identity cell inside RQ3. Neither outcome changes the thesis, four RQs,
  recurrence algorithm, or existing RQ1/RQ2/RQ4 evidence.

## Approval Condition

Approval requires only the two textual/execution repairs above. Do not add a
new benchmark, train/reference split, evaluator, model sweep, prompt variant,
implementation review, checker, or reproducibility contract. After the plan
calls the intervention a fixed backend substitution and names a non-overwriting
real command/output path, proceed directly to the declared real preflight and
complete run.

## Revision Review

**Re-reviewed:** 2026-07-15
**Inputs:** revised `experiment-plan.md` and `plan-revision.md`
**Final verdict:** **APPROVE**

Both original must-fix items are closed without changing the experiment:

1. The revised plan consistently defines the intervention as substitution of
   one fixed model backend/artifact. It explicitly records that generation,
   training, architecture, and parameter count differ, treats greater capacity
   only as motivation or one plausible explanation, and forbids a capacity-
   causal, scaling-law, or universal larger-model conclusion. The operational
   hypothesis remains the predeclared accuracy of the named 27B-backed
   AgentProf path.
2. The revised plan now provides the real llama.cpp command, the unchanged
   AgentProf command shape and all nine fixed task choices, and distinct
   `27b/` paths for preflight, three complete profiles, and scored output. The
   existing 3B files cannot be overwritten, and the exact raw inputs for the
   later independent result review are unambiguous.

The approved experiment therefore changes one system component while holding
the population, visible input, scorer, taxonomy, descriptions, prompt,
grammar, decoding, AgentProf path, repetitions, metrics, and decision rule
fixed. No test-label-derived rule, example, prompt, glossary, or configuration
enters the 27B candidate. The fixed majority control and completed 3B result
retain their declared lower-bound/context roles, and support still requires
the complete `1,012 x 3` run, grammar-valid output, both absolute `0.80` bars,
and improvement over majority.

Proceed directly to the stated real preflight and complete run. No additional
plan change, benchmark, evaluator, split, checker, or review layer is needed.
