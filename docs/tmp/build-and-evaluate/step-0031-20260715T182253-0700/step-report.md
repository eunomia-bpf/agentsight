# Step 0031 — Literal Task Identity on AgentBoard

**Entered:** 2026-07-15T18:22:53-07:00

**Recovered:** 2026-07-15T21:28:12-07:00

**Phase:** `BUILD_AND_EVALUATE`

**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`

**Current state:** complete; next step remains in `BUILD_AND_EVALUATE`

**Fixed thesis:** **Agent observability needs profiling, not only debugging.**

**Selected paper question:** **RQ3 — How Accurate Are the Tags?**

## Scientific And Repository Boundary

The active paper remains the AAAI-27 workspace under `docs/paper/`. The exact
four RQs remain resource attribution, real-problem localization, tag accuracy,
and profiling cost. The read-only story source remains
`docs/agentpprof-paper` at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`; Step 0031 has not edited it.

This step may test and improve the literal-task component of RQ3 through an
implementation detail. It may not replace the thesis, story, operation and
operation-stack abstractions, RQs, contributions, recurrence constructor, or
the admitted RQ1/RQ2/RQ4 evidence. One experiment judges its tested hypothesis,
not the whole RQ. Only a valid positive result may enter the reader-facing
paper as supporting RQ3 evidence. Complete development failures remain in this
history and canonical evaluation memory rather than becoming the paper story.

At gate entry and recovery, the root read the complete
`docs/user-instruction.md`, `docs/questions-for-author.md`, the intact
`docs/idea-story.md` Initial Narrative and evolution history, the current RQ3
paper text, the current evaluation frontier, and all Experiment 001 and 002
owner files. There are no unanswered author questions. The current experiment
is aligned with the user's requirements to preserve the larger original story,
keep the four RQs, use a complete real public benchmark, improve the mechanism
before changing a viable hypothesis, avoid branch changes, and never pause for
human research judgment.

## EXPERIMENT_GATE

### Gate Entry And Paper-Value Selection

Step 0030 left RQ3 with positive public evidence for task partitions and
operation-group boundaries but no direct literal task-name result. Another
boundary cutoff or another run on the retained OSWorld/CodeTrace development
labels would not change that evidence gap. Step 0031 therefore selected one
literal task-family assignment experiment on the complete official AgentBoard
test population: 1,012 real benchmark goals across nine released task
families. The model receives only each natural-language goal; the official
task identity and every other source field remain scorer-only.

The source-fidelity screen and plan are preserved under
`literature-20260715T182253-0700/` and `experiment-001/`. This experiment is
supporting evidence inside RQ3, not a new paper contribution or replacement
classifier story.

### Node E31.1 — Shared Declared-Task Product Path

**Question and entry.** Can the existing local tagger assign a separately
declared canonical task field while preserving its raw open-vocabulary tag and
using the same request, retry, grammar, sanitation, and cache path?

**Method and implementation.** Before scoring, the existing Rust path gained
an optional repeated `--task-choice TAG=DESCRIPTION` input. It emits a separate
`task_tag` while retaining the existing raw `session_tag`; `--no-cache` now
disables cache reads, in-memory hits, and writes. The same fields flow through
`SessionRecord`, JSON, standard trace, and operation-stack projection. The
thin AgentBoard adapter loads official rows and scores stored product output;
it contains no parallel model request, synonym map, training, label cleanup,
or prediction rewrite.

**Verification.** The shared path passed 48 Rust unit tests, 10 profile CLI
tests, and 3 standard-trace CLI tests. The actual nine-row AgentBoard preflight
engaged all nine declared choices through the real llama.cpp and Rust profile
path. These checks establish implementation and executability only; they are
not paper results.

**Outer-audit correction.** Both model runs used the same implementation, and
their registered `task_tag` request was the approved goal-only declared-label
request. The outer audit later found that the auxiliary `session_tag` in this
optional branch did not preserve the old raw request semantics: it used
`task`, prompt-only input, and no hints rather than `session`,
title/CWD/prompt input, and source/model hints. The scorer never reads
`session_tag`, so the scientific `task_tag` result remains valid, but the
product contract required repair before step closure. The repaired path always
computes the old raw session request first and computes the declared task
request separately; a focused test distinguishes both inputs while leaving the
declared request unchanged.

**Decision.** After this bounded repair, the shared product path satisfies the
fixed experiment contract. Its scientific value still depends on the complete
registered population and result review.

### Node E31.2 — Experiment 001, Qwen2.5-3B Complete Result

**Plan and review.** The approved plan and its complete two-stage review are
`experiment-001/experiment-plan.md` and `experiment-001/plan-review.md`. The
fixed hypothesis required at least 0.80 nine-class macro-F1 and 0.80 micro
accuracy, improvement over majority, complete coverage, and 3,036 grammar-valid
declared outputs. The candidate used the existing Qwen2.5-3B-Instruct Q4_K_M
backend, all 1,012 official rows, three no-cache repetitions, fixed labels and
descriptions, and target-blind goal-only input.

**Complete result.** All 1,012 rows and three repetitions completed. Candidate
accuracy was `399/1,012 = 0.3942687747` and macro-F1 was `0.1911946041`, versus
majority accuracy `0.2480237154` and macro-F1 `0.0441629278`. All 3,036 declared
outputs were grammar-valid, and both declared and raw outputs were identical
across all three repetitions. The failure was semantic assignment collapse,
not syntax, cache, adapter, or nondeterminism.

**Independent result review.** A fresh reviewer independently joined the raw
profiles to the scorer manifest and reproduced every population count,
prediction, stability value, confusion cell, and metric. The result is
`VALID / CONTRADICTED / decisive for the tested mechanism / mechanism-workload
boundary`. Details are in `experiment-001/result-report.md` and
`experiment-001/result-review.md`; raw output is under
`.agentsight/experiments/step-0031-agentboard-task-identity/`.

**Scientific impact and decision.** Enumerated decoding plus short family
glosses is insufficient for this 3B backend. This does not challenge RQ3, the
paper thesis, or existing partition/boundary evidence. No negative number is
admitted to `docs/paper/`. The strongest non-contaminating follow-up is the
already-used fixed 27B backend on the exact same path; labels, descriptions,
prompt, grammar, input, population, scorer, and positive rule remain unchanged.

### Node E31.3 — Experiment 002 Plan And Real Preflight

**Question.** Does the already-used local Qwen3.6-27B artifact make the
unchanged declared-taxonomy AgentProf path accurate on the same complete
AgentBoard population?

**Plan and review.** `experiment-002/experiment-plan.md` changes only the fixed
model backend from Qwen2.5-3B-Instruct Q4_K_M to Qwen3.6-27B Q4_K_M. The plan
does not claim an isolated parameter-capacity cause because the model
generations, training, and architectures also differ. The independent reviewer
first requested that causal correction and distinct `27b/` raw filenames, then
approved the revised plan. The complete discussion is in
`experiment-002/plan-review.md`; the minimal disposition is in
`experiment-002/plan-revision.md`.

**Real path.** The server uses the declared 17,984,872,960-byte model artifact
with SHA-256
`8739a0cbb80036e5dbdced2085f142b8ba86e3235db8b8039b3769fe5fc70843`,
llama.cpp version 9870, GPU offload, Jinja, and reasoning disabled. `/v1/models`
reported alias `qwen3.6-27b`. The actual nine-row preflight completed through
the then-current auxiliary raw tag, declared task tag, profile, and JSON paths,
producing `27b/preflight-profile.json`. It was not scored and did not change any
experiment field. The focused evidence is recorded in
`experiment-002/preflight-report.md`.

**Decision.** REAL PREFLIGHT passed. Proceed with all three complete no-cache
repetitions; no source, prompt, taxonomy, model setting, or metric change is
authorized.

### Node E31.4 — Recovery During Experiment 002 Full Run

**Context and status.** At 2026-07-15T21:28:12-07:00 the dedicated server and
first full AgentProf repetition were still live. The server PID was `336026`,
and the first repetition PID was `342664`. The server log contained 911
completed prompt-evaluation timing records. Each complete repetition requires
3,036 model requests because every one of 1,012 rows receives a raw prompt tag,
a declared task tag, and a raw session tag through the fixed product path. The
profile JSON is written atomically at command completion, so the absence of
`full-profile-r1.json` while the PID is live is expected and is not a failed or
partial scientific result.

The resume audit confirmed the approved plan, live processes, healthy
`/health` endpoint, retained preflight artifacts, exact current code, unchanged
paper and submodule, and no newer raw contradiction. It resumes this innermost
FULL RUN node rather than restarting the project or interpreting its prefix.

**Persistence deviation.** During this still-open step, direct user requests
to explain the two induction algorithms produced a separate documentation
commit `b9127a8d9`. The current orchestrator policy expects one Git publication
unit only after step closure. The commit contains only
`docs/operation-stack-induction-algorithms.md` and verbatim user instructions;
it does not contain Step 0031 code, experiment output, paper edits, or submodule
changes. Published local history will not be rewritten. Step 0031's remaining
coherent code, results, paper disposition, reports, and audits will be
persisted once at its completed boundary, and this deviation will be included
in the outer audit.

Later direct user questions extended the same algorithm record with the exact
OSWorld-Human annotation meaning and the metric hierarchy: B³ F1 for partition
membership, boundary P/R/F1 and group counts for merge/fragmentation diagnosis,
macro-F1 for literal labels, and fixed real inspection work for downstream
profiling usefulness. These documentation-only additions change no runtime
algorithm, RQ, hypothesis, story, or paper claim and are included in this
step's remaining publication unit.

**Next action and completion condition.** Complete `full-profile-r1.json`,
rerun the identical command from the start for R2 and R3, score only after all
three contain exactly 1,012 sessions/samples, and obtain one fresh independent
result review. No partial prefix may enter WRITE or the paper.

### Node E31.5 — External Process Interruption And Durable Restart

**Observed:** 2026-07-15T22:17:32-07:00
**Restarted:** 2026-07-15T22:49:48-07:00

The first R1 attempt ended before command completion when both PTY-owned
processes—the llama.cpp server and AgentProf client—were terminated together
by the surrounding tool-session lifecycle. The server log ended after a
successfully completed request, contained no model error or request timeout,
and the host kernel recorded no OOM kill. AgentProf emitted no
`full-profile-r1.json`, so this interrupted prefix is neither a repetition nor
a scientific result and will never be scored. Its server log is retained as
`27b/server-interrupted-attempt1.log` for auditability.

The same approved server and AgentProf commands were restarted from the
beginning as independent user services. This changes only process lifetime:
the model artifact, release binary, complete trace, taxonomy, prompt, grammar,
cache setting, metrics, and output filename are unchanged. R1 now writes to
the originally approved `27b/full-profile-r1.json` only after all 1,012 rows
complete. R2 and R3 remain pending and will use the identical command with
their approved output names.

### Node E31.6 — CUDA Runtime Failure And Execution-Only Repair

**Failed:** 2026-07-15T23:26:38-07:00
**Repaired preflight:** 2026-07-15T23:33:56-07:00
**R1 restarted:** 2026-07-15T23:33:59-07:00

The independently hosted second R1 attempt isolated a different failure. After
1,804 completed server requests, llama.cpp exited with `SIGSEGV` inside
`libcuda.so.575.57.08`; the kernel recorded a general-protection fault, and
systemd measured a 31.8-GiB process-memory peak. AgentProf then received an
unexpected EOF and exited without writing `full-profile-r1.json`. The server
log before the fault contained normal completed requests and no model or
request error. This prefix is retained as
`27b/server-cuda-segv-attempt2.log` plus
`27b/run-r1-cuda-segv-attempt2.log`, is not a repetition, and will not be
scored.

The runtime repair keeps llama.cpp version 9870 at source commit `2d973636e`,
the same 27B GGUF, full GPU layer offload, context size, Jinja template,
reasoning mode, and all AgentProf inputs unchanged. It recompiles that source
with `GGML_CUDA_GRAPHS=OFF` and starts the server with context checkpoints and
the server RAM cache disabled. These switches affect CUDA execution and
request-result reuse only; they do not alter model weights, predictor-visible
text, decoding temperature, grammar, output budget, taxonomy, scorer, or any
paper variable.

A new nine-row real preflight through the repaired runtime produced nine
unique sessions, nine nonempty raw tags, nine allowed declared tags, nine
stacks, and total weight nine. Its profile is retained as
`27b/preflight-profile-runtime-repair.json`. Server RSS after preflight was
about 1.4 GiB rather than the failed service's 31.8-GiB peak. The complete R1
was then restarted from the beginning under the same fixed scientific cell.

### Node E31.7 — Three Complete Repetitions And Registered Result

**R1 completed:** 2026-07-15T23:39:48-07:00
**R2 completed:** 2026-07-15T23:46:58-07:00
**R3 completed:** 2026-07-15T23:57:58-07:00

The repaired runtime completed R1 and R2 consecutively. During an initial R3
prefix, the long-lived server encountered another driver-level general
protection fault after 6,679 cumulative requests. R1 and R2 were already
durable and complete; the R3 prefix emitted no profile. Restarting the
identical repaired server before R3 kept each server lifetime below the
observed two-run stability window, and R3 then completed from the beginning.
The excluded prefix remains in
`27b/server-stable-runtime-cuda-segv-after-r2.log` and
`27b/run-r3-server-lifetime-attempt.log`.

Every durable repetition contains 1,012 unique sessions, nonempty raw and
declared tags, only the nine allowed task tags, and total profile weight 1,012.
The registered scorer was run only after all three passed these checks.
Qwen3.6-27B reaches accuracy `0.7332015810` and nine-class macro-F1
`0.6951270608`, versus majority `0.2480237154` and `0.0441629278`. All 3,036
declared outputs are grammar-valid, and both raw and declared vectors are
exactly identical across repetitions.

The result substantially improves over both majority and the unchanged 3B
backend, but misses the registered 0.80 accuracy and macro-F1 bars. The strong
tested hypothesis is therefore contradicted. The complete root report is
[`experiment-002/result-report.md`](experiment-002/result-report.md).

### Node E31.8 — Independent Raw Result Review

**Reviewed:** 2026-07-16T00:05:09-07:00
**Status:** complete

A fresh reviewer read the complete experiment skill, plan, review, manifest,
all 3,036 stored session rows, source path, and only the runtime evidence needed
to distinguish completed profiles from failed prefixes. Without using the
registered scorer output, it independently recomputed `742/1,012 = 0.733202`
accuracy and `0.695127` macro-F1 in each repetition, majority `0.248024` and
`0.044163`, all per-family rows and confusion cells, `3,036/3,036` grammar
validity, and exact three-run stability.

The review verdict is `VALID RUN / REGISTERED HYPOTHESIS CONTRADICTED /
BOUNDED SUPPORTING RQ3 EVIDENCE`. Missing the two `0.80` bars controls the
registered hypothesis verdict but does not erase the complete positive margin
over the majority control. The admissible paper statement is limited to the
named Qwen3.6-27B backend, the complete released AgentBoard goal population,
and assignment among nine declared families. It does not authorize
open-vocabulary, phase/action, unknown-family, model-scaling, or all-RQ3 claims.
The full review is
[`experiment-002/result-review.md`](experiment-002/result-review.md).

### EXPERIMENT Gate Transition

EXPERIMENT_GATE is complete and transitions to targeted WRITE. Paper-value
admission passed; the real product path and complete `1,012 x 3` population ran;
the result review links raw outputs and separately reports run validity, tested
hypothesis, research value, and paper impact. The `0.80` hypothesis verdict is
not relaxed after observation. WRITE may report the complete bounded effect
with its actual metrics while preserving the exact thesis, four RQs, original
story, and existing recurrence evidence.

## WRITE_GATE

### Gate Entry And Alignment

WRITE entered after the independent review. The root reread the complete
`docs/user-instruction.md`, `docs/idea-story.md`, current paper, and result
review. BUILD_AND_EVALUATE permits only a targeted implementation and RQ3
evidence sync. The title, abstract, introduction, motivation, insight,
contributions, four RQs, section structure, related-work position, conclusion,
and read-only submodule were explicitly excluded.

### Node W31.1 — Targeted RQ3 Evidence Sync

**Written and verified:** 2026-07-16T00:22:28-07:00
**Status:** complete

The targeted pass used `rewrite-paper-section` and touched only the
Implementation tagger paragraph, RQ1's pointer to RQ3, the RQ3 evidence block,
its local scope paragraph, and `references.bib`. It adds the product's
user-declared task-label capability and one concise AgentBoard result: all
1,012 goals, nine families, Qwen3.6-27B, `0.695` macro-F1 and `0.733` accuracy
versus majority `0.044` and `0.248`, with identical assignments across three
complete runs. The official NeurIPS 2024 AgentBoard proceedings entry is the
source citation.

The first build showed that simply appending the result moved Related Work and
Conclusion onto page eight. The pass therefore compressed redundant RQ3
result narration rather than altering the scientific story: the table and
default recurrence results remain, the optional scalar's detailed tradeoff
remains in canonical experiment memory, and the reader-facing RQ3 block keeps
the primary B-cubed, boundary, task-partition, and literal task-family evidence.
No result threshold, RQ, claim, contribution, or story changed.

`check-paper-structure-flow` found the AAAI seven-page paper's macro sequence,
merged Background and Motivation, architecture figure, Design/Implementation
separation, and four explicit RQ evidence blocks structurally sound.
`check-terminology-infoflow` found three local drifts: low-frequency `task
taxonomy`, the stacked phrase `closed-taxonomy task-family assignment`, and an
RQ1 pointer saying RQ3 covered only group construction. The minimal fixes use
`declared task labels`, `assignment among declared task families`, and `tags
and group construction`; the Qwen model citation now appears beside the RQ3
measurement. No named concept was added.

The authoritative AgentBoard result was propagated to `docs/evaluation.md`,
`docs/implementation.md`, `docs/design.md`, and
`docs/background-related-work.md`. `docs/idea-story.md` was not changed because
the scientific contract did not change.

### Node W31.2 — AAAI Paper And Checklist Verification

The official AAAI-27 Main Technical Track page, updated July 14, 2026, permits
seven main-content pages and nine total pages, reserves pages after seven for
references, and requires the reproducibility checklist. A full `make` produces
nine US-letter pages. Page seven ends with the exact thesis sentence in
Conclusion; page eight begins with References. All fonts are embedded, the PDF
contains no author identity or unresolved citation, and the log has no
overfull box or undefined-reference warning.

Every actual checklist response is now filled using only listed options. The
standalone checklist compiles to a two-page US-letter PDF. Existing support is
marked `yes`; absent theory is `no/NA`; incomplete code-appendix,
hyperparameter, infrastructure, metric, and all-run disclosures are marked
honestly as `partial/no` for submission follow-up rather than converted into
unsupported claims.

### WRITE Gate Transition

WRITE_GATE completes and transitions to REVIEW_GATE. The paper compiles, the
four fixed RQs remain explicit, the bounded result reaches every permitted
affected section, the ambitious thesis remains verbatim, no intermediate
runtime or 3B development failure entered the paper, and the result scope
matches the independent review. REVIEW must now perform the scientific-contract
unchanged audit, one fresh step-level outer audit and meta-review, and route the
next paper-level action.

## REVIEW_GATE

### Node R31.1 — Scientific-Contract Audit And Independent Outer Audit

The scientific contract is unchanged: the exact thesis, original submodule
story, two abstractions, three contributions, and four RQs are identical to
gate entry. A fresh reviewer with no Step 0031 execution, writing, canonical
memory, Git, or prior review role audited EXPERIMENT and WRITE and performed
the Direction, Efficiency, and Maintenance meta-review. Its only output is
[`outer-audit-20260716T004151-0700.md`](outer-audit-20260716T004151-0700.md).

The auditor independently joined the manifest and all three raw 27B profiles
without relying on the registered scorer values. Every repetition contains all
1,012 rows and recomputes to `742/1,012 = 0.7332015810` accuracy and
`0.6951270608` macro-F1, with identical predictions. It confirms the run as
scientifically valid, the strong `0.80` hypothesis as contradicted, and the
bounded named-backend result as paper-admissible supporting RQ3 evidence. It
also confirms that the paper reports the actual result without answering all
of RQ3, and that the exact thesis, four RQs, original story, two abstractions,
three contributions, page allocation, anonymity, and read-only submodule are
preserved.

The initial overall verdict was `RETURN FOR BOUNDED REPAIR` for two concrete
non-scientific-contract defects:

1. the optional branch stored a separate raw `session_tag` but generated it
   from the task request rather than the legacy session request; and
2. the checklist marked the private 325-trajectory corpus's two novel-dataset
   questions `NA`, inconsistent with the paper and canonical implementation
   memory.

Neither defect entered the AgentBoard scorer or invalidates its `task_tag`
numbers.

### Node R31.2 — Bounded Deterministic Repair

The release path now always computes the raw session tag through the original
contract—kind `session`, title/CWD/prompt text, and source/model hints—then
computes the declared `task_tag` through the same `task`, goal-only, no-hint
request used in all completed profiles. The obsolete combined helper was
removed. A focused test asserts both distinct request contracts. Because the
declared request, choices, model, grammar, settings, predictions, and scorer
are unchanged, the outer audit explicitly states that the complete
`1,012 x 3` experiment need not be rerun. Both experiment result reports now
disclose the run-time auxiliary raw-tag deviation and exclude its raw exact
match from paper evidence.

The two checklist answers are now honestly `no`: the private corpus is neither
included in a data appendix nor promised for public release. The adjacent
unavailable-dataset answer remains `partial`. No unsupported release promise
was added.

### Node R31.3 — Repair Verification

The repaired implementation passes:

- `cargo fmt --check`;
- 49 Rust unit tests, including the new request-contract test;
- 10 profile CLI tests and 3 standard-trace CLI tests; and
- `cargo clippy --all-targets -- -D warnings`.

The main paper rebuilds to nine US-letter pages. Page seven ends with the exact
thesis in Conclusion, page eight begins References, all fonts are embedded,
and the final log has no unresolved citation, undefined reference, overfull
box, multiply-defined label, or changed-label warning. The corrected checklist
rebuilds to two US-letter pages. The template's standalone conditional warning
is nonfatal and inherited from its supplied wrapper. `git diff --check` passes.
The active branch remains `research/semantic-flamegraph-artifacts-v2`; the
submodule remains clean and unchanged at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

### Meta-Review Disposition

**Direction:** pass. Step 0031 adds a real complete public task-identity
measurement while keeping classification subordinate to the simple
operation/operation-stack profiling model. It neither shrinks nor replaces the
ambitious thesis.

**Efficiency:** close AgentBoard after this named 27B measurement. Do not add a
prompt variant, model sweep, taxonomy-description sweep, arbitrary threshold
chase, another recurrence cutoff, or another reader packet. Runtime failures
produced no scored prefix and do not create research results.

**Maintenance:** the raw-tag finding is a focused product-test gap, not evidence
for another skill or AGENTS rule. The test is sufficient. Canonical memory is
too long—especially `docs/evaluation.md`—but compaction is deferred to the next
step as a net-reduction maintenance node so this completed scientific step does
not grow into an unrelated rewrite. `docs/idea-story.md` remains intact.

### Ranked Remaining Objections And Route

1. RQ3 remains partial under its fixed promise: literal phase/action identity
   and truly unseen-family transfer remain unestablished.
2. The AAAI code/data package is not submission-ready while several checklist
   items remain honestly `partial/no` and private raw histories cannot ship.
3. AgentBoard macro-F1 `0.695` is bounded named-backend evidence, not uniform
   accuracy or a strong-baseline win.
4. RQ2 supports prioritization rather than universal work reduction; do not
   reopen another packet or score variant.
5. OSWorld/CodeTrace recurrence results remain development/post-hoc evidence.

REVIEW_GATE now closes Step 0031 and routes to the next
`BUILD_AND_EVALUATE -> EXPERIMENT_GATE`. The next step first performs a bounded
source-fidelity screen over already-held CodeTraceBench solved/failed
trajectories and official stage intervals. It admits one literal phase-identity
experiment only if the official stage vocabulary and visible fields support a
non-circular target-blind label test. Otherwise it records the rejection and
screens another already-held official trajectory source. It may not use B³ or
boundary F1 as a substitute for literal label accuracy, change the fixed RQ,
shrink the story, reopen constructor tuning, or enter milestone review before
the remaining promised evidence and submission package are complete.
