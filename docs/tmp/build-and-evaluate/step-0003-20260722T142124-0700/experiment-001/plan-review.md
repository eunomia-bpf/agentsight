# RQ7 Measurement-Capability Plan Review

## Initial verdict: BLOCK

The experiment is admitted on paper value, but the current plan cannot yet
produce an interpretable matched result. The blocking defects are the
unfrozen/underspecified Raw-log condition, question-selection and oracle
ambiguity, incomplete specification of official ProcGrep engagement, and an
undefined primary contrast across stochastic repetitions. These are scientific
or execution-validity defects, not requests for wider scope or cosmetic polish.

This review is read-only with respect to the plan, paper, and code. I reviewed
the complete `docs/user-instruction.md`, `docs/idea-story.md`,
`docs/evaluation.md`, `docs/background-related-work.md`,
`docs/paper/main.tex`, and this experiment's `plan.md`. I also inspected the
official ProcGrep checkout at commit
`2e8277003dacaa774b5ef61ba150ae03a4f06693`, including its canonical types,
Claude/Codex/Gemini adapters, pattern matcher, CLI, README, and paper's episodic
search description.

## Admission and RQ fit

**PASS.** The experiment directly tests RQ7: it asks which fact families can be
answered from a common frozen source universe and checks answers against source
evidence rather than human annotations, an LLM judge, or the proposed method's
own output. It addresses the open, load-bearing tool claim left by the RQ1--RQ6
study. A positive result retains a narrow source-correct artifact/cross-session
coverage claim; a tie, loss, or invalid representation drops or bounds that
claim. Those are different paper decisions. Another local observational
correlation would not resolve this uncertainty.

The experiment is non-tautological only in this narrow sense: independent
source checking can expose parser, path, lineage, status, and abstention errors.
ProcGrep's lack of path identity makes some *representational availability*
differences expected by construction, so a ProcGrep abstention on an
artifact-linked item cannot by itself establish broad superiority or “better
understanding.” The defensible result is correct factual coverage on the frozen
fact families, plus an efficiency claim against Raw only if its accuracy and
cost rules are fixed and met.

## Blocking defects and exact repairs

### B1. The bounded Raw-log model is neither frozen nor executable as specified

The model and reasoning configuration are to be “selected in preflight,” while
the input is variously described as project bundles, native records, and a
“relevant cutoff-state slice.” No rule defines that slice, the prompt, the
context/output/tool-call/returned-byte/time limits, the command, or what happens
when a project archive exceeds the context window. Choosing configuration after
seeing preflight answers is adaptive. Selecting a relevant slice using question
witnesses can leak the answer; serializing every native record can be
infeasible. The earlier project history already records that a static Raw prompt
exceeded its input ceiling. Under the current plan, a Raw loss could therefore
mean truncation or bad retrieval rather than lack of reconstruction capability,
and a Raw cost number would not be comparable.

Required repair before preflight:

1. Freeze in the plan the exact Codex model identifier, reasoning effort, CLI
   version, prompt, output format, context/output limit, maximum model/tool
   calls, returned-byte limit, wall-clock timeout, and failure/abstention rule.
   Do not select any of them from preflight performance.
2. Give Raw the complete same-source membership through a real executable path.
   The preferred simple path is a read-only sandbox containing only the hashed
   native archives and cutoff workspace manifest, with ordinary source-native
   `rg`/`jq`/`sed`-style access. It must not contain normalized trajectory rows,
   oracle witnesses, expected answers, proposed-method indices, or selected
   evidence snippets. If static serialization is retained instead, specify the
   deterministic serialization/truncation rule and demonstrate before question
   scoring that every project bundle fits the frozen input ceiling; otherwise
   the static design is invalid.
3. State whether one call answers all 20 questions for a project or whether
   calls are per question, and use the same unit for accuracy and amortized
   cost. Preserve the three repetitions without majority voting, but define
   their primary estimand as required in B4.
4. Define cost instrumentation: distinguish source bytes scanned, bytes
   returned to the model, rendered input/output tokens, tool/model calls,
   latency, and any cached work. Do not claim an efficiency result from metrics
   that the chosen execution path cannot measure.

### B2. Question selection is not reproducible and can be representation-aware

The plan fixes “five questions” per project/family, says only that vendors are
stratified and Booleans are balanced “where source support permits,” and allows
candidates to be proposed from normalized rows. That conflicts with the rule
that no method output may define eligibility. It leaves the candidate universe,
vendor allocation, negative construction, duplicate handling, and substitution
for an unsupported stratum unspecified. Independent verification of an answer
does not remove selection bias: a generator can select unusually easy proposed-
method facts or unusually hard Raw/ProcGrep facts while every answer remains
true.

Required repair before any method output:

1. Freeze the complete question-template grammar and candidate-universe rules
   for all four families. Specify the exact project/vendor/session allocation,
   count-versus-predicate allocation, Boolean positive/negative construction,
   duplicate policy, minimum support, N/A rule, and seeded sampling algorithm.
   Resolve the contradiction between “five per project/family,” possible N/A
   cells, and the completion requirement of 30 eligible items per family: either
   deterministically obtain all 30 before methods run or stop the family/run.
2. Enumerate and sample candidates from the immutable native archives and
   cutoff workspace snapshot through an oracle-only path, not from ProcGrep,
   RQ1 tables, the artifact-linked projection, or their normalized outputs.
   Candidate selection may use source fields named by the frozen template but
   may not use a condition's answerability or answer.
3. Freeze the fact semantics needed by the oracle: action ordering and ties,
   worktree identity, path normalization and symlinks, explicit rename,
   delete--recreate identity, multi-path calls, failed/unknown status, session
   identity/boundaries, cutoff state, and the definition of “same artifact” and
   “cross-session reuse.” These are currently essential but implicit.
4. Identify the two independent direct-source implementations/checks, their
   allowed shared code, and disagreement handling. Neither may import the
   proposed query implementation. Eligibility and the answer must be frozen
   only after both reproduce the same result; disagreements become N/A before
   any method runs. Every retained item needs a common method-independent ID,
   exact answer, and immutable native call/line or cutoff-manifest witness.

This remains deterministic source verification, not human or model-generated
gold.

### B3. “Official ProcGrep” engagement and the shared action spine are not yet an executable baseline

The pinned checkout does provide official Claude Code, Codex, and Gemini CLI
adapters and represents each session as an ordered `Trace.atoms` sequence. Its
official Level-1 matcher is a regex over the space-joined atom sequence. It does
not retain stable paths in the atom spine and does not provide variable binding,
temporal windows, or artifact lineage. The official paper's episodic experiment
takes its deterministic structural match as ground truth; that truth protocol
must not replace this plan's independent native-source oracle.

The plan currently says it will import ProcGrep and join an “exact” shared spine
to `agent-session` effects, but provides no adapter invocation, pattern/query
mapping, per-atom source alignment, or mechanism-engagement check. A custom
reimplementation of canonicalization or a path-aware query labeled ProcGrep
would invalidate the external baseline; simply feeding a precomputed homemade
spine would not establish official adapter engagement.

Required repair before preflight:

1. For every action-only question template, state the exact executable official
   adapter and atom/pattern operation used. Use the pinned source directly and
   retain its canonical trace output, adapter coverage, unknown/`other` atoms,
   and failures. Keep Aggregate Counts separate from ProcGrep.
2. For artifact-linked, cross-session, or final-state templates outside official
   ProcGrep semantics, require an explicit ProcGrep abstention/out-of-scope
   result. Do not add project-authored path extraction or lineage to the
   ProcGrep arm. Such relations belong only to the proposed arm.
3. Define and test the proposed arm's source-call-to-atom join. Its action-only
   projection must be byte-for-byte identical to the pinned ProcGrep output on
   admitted records before artifact relations are added; a mismatch invalidates
   the claimed isolation rather than becoming a proposed-method win.
4. Expand the real preflight from one Claude session to the smallest real
   three-vendor path: at least one closed Claude, Codex, and Gemini session,
   using each official loader/adapter, plus one real question from every family
   and one actual Raw model execution. Parser-specific failures cannot be
   discovered by a Claude-only preflight.

### B4. The primary contrasts and stochastic Raw decision rule are undefined

“The artifact trajectory's project-block interval is above zero” does not name
the comparator. “Accuracy is comparable,” “not worse,” “fair Raw win,” and “no
accuracy veto fails” have no numerical or finite-sample rule. The denominator
must also be common: method-specific “eligible” questions would let each method
discard hard items. Finally, three Raw repetitions are reported as a
distribution, but the plan does not say whether the primary Raw comparison uses
their mean, each repetition, or another statistic. These choices can reverse a
positive/mixed/negative verdict after results are seen.

Required repair before preflight:

1. Define one common oracle-eligible denominator per family for every method.
   An unsupported interface is an abstention, not method-specific ineligibility.
   Retain the separate `correct`, `wrong`, and `abstain` outcomes.
2. Name every claim-matched primary paired contrast, at minimum artifact
   trajectory minus official ProcGrep correct factual coverage for the
   artifact-linked and cross-session families, with action-only preservation as
   a veto. Define separately the trajectory-versus-Raw accuracy/cost contrast;
   do not use Final State or Counts as headline competitors outside their
   control roles.
3. Predeclare the Raw repetition estimand (for example, the mean correct-
   coverage probability across the three independent repetitions) and an
   uncertainty calculation that keeps question pairing, project clustering,
   and model repetition distinct. Show all six project effects regardless of
   the aggregate.
4. Give numerical non-inferiority/comparability margins and exact interval or
   finite-sample rules for “above zero,” “not worse,” accuracy veto, Raw parity,
   and cost superiority. State the positive, negative, mixed, and inconclusive
   decision from those rules. With only six fixed projects, scope inference to
   this frozen corpus; a project-block interval must not be presented as a
   population estimate.

### B5. The plan lacks the authoritative run contract and auditable private/release artifacts

The proposed Python entrypoint has no path or runnable command, no environment
lock command, no timeout/terminal-status convention, and no material cost
estimate. Raw native archives, plaintext questions/prompts, and model responses
are merely described as local and ignored. Hash-only public aggregates cannot
support result review or recomputation, while committing private trajectories
would violate the stated privacy boundary.

Required repair before preflight:

1. Add the exact entrypoint path and literal preflight/full/score commands,
   environment creation command and lock hash, input/output paths, timeouts,
   exit-status rules, expected upper-bound calls/tokens/time, and the condition
   that a failed or partial cell is retained rather than silently replaced.
2. Freeze native files by copying immutable bytes and hashing them; “closed ten
   minutes” alone is not immutability. Freeze each worktree's revision, tracked
   state, untracked-state snapshot, and filesystem bytes needed by final-state
   questions at the same declared cutoff. Reject or re-freeze a source whose
   hash changes. Record the temporal relation between native-prefix cutoff and
   workspace cutoff.
3. Preserve an access-controlled local audit bundle containing immutable raw
   archives, plaintext questions, oracle witnesses, exact prompts, every model
   response, deterministic outputs, and cost logs, all covered by a manifest
   hash. Produce a release-safe per-question artifact with pseudonymous IDs,
   template/form, expected answer, method answer/correct-wrong-abstain outcome,
   cost, and witness hashes. This permits audit without publishing prompts,
   paths, secrets, or native text.

## Baseline roles, privacy, and paper decisions that already pass

- ProcGrep and bounded Raw-log analysis are two distinct, credible main
  baselines; Final State and Counts are correctly labeled controls. No extra
  baseline is required.
- The prospective source freeze, pinned ProcGrep commit, fixed six-project
  scope, source-linked abstention, and refusal to use an LLM or human as truth
  are appropriate in intent.
- Privacy is treated as a real constraint, and the six author-associated cases
  are correctly scoped as a frozen-corpus capability study rather than a
  population estimate. B5 requires an auditable way to implement that intent.
- Positive, negative, mixed, and inconclusive outcomes would change the RQ7
  tool claim. The repairs above make those outcomes decidable without changing
  the RQ, adding workloads, or expanding the claim.

## Review disposition

Do not begin real preflight under this version. Revise the same plan with the
five repairs above and return it for the first follow-up review. The experiment
does not need more baselines, more projects, human annotation, or a broader
claim.

---

# Follow-up Review 1

## Verdict: BLOCK — B2, B3, and B5 closed; residual B1 and B4 defects remain

I reread the complete revised `plan.md` and checked every original B1--B5
repair. I also checked the locally installed Codex CLI `0.145.0` help and
feature list against the literal Raw command. The current flags
`--ignore-user-config`, `--ignore-rules`, `--strict-config`, `--ephemeral`,
`--skip-git-repo-check`, `--sandbox`, `--cd`, `--model`, `--config`,
`--output-schema`, `--json`, and `--output-last-message` are available. The
disabled feature names `shell_tool`, `code_mode_host`, `apps`, `browser_use`,
`browser_use_external`, `image_generation`, and `multi_agent_v2` are present in
this CLI. Together with the frozen prompt instruction, JSONL audit, and the
rule that any tool call invalidates that repetition, this is a valid zero-tool
Raw execution contract.

The revised plan is substantially stronger and does not need new projects,
questions, baselines, or control infrastructure. The remaining blockers below
are narrow repairs to the already chosen experiment.

## Closure audit

### B1 — Partially closed

Closed portions:

- Model `gpt-5.6-sol`, medium reasoning, CLI version, zero-tool configuration,
  prompt/output schema, one 20-question call per project, three repetitions,
  byte and time ceilings, terminal failure behavior, and cost fields are fixed
  before preflight.
- Raw receives complete selected native files and the cutoff slice statically,
  with no normalized rows, oracle witnesses/answers, ProcGrep atoms, proposed
  indices, or external tools.
- The current literal Codex command is syntactically supported by the pinned
  local CLI and the requested zero-tool mechanism is auditable.

Two defects remain:

1. **The source-selection algorithm does not actually enforce its claimed
   cumulative 160-KiB bundle limit.** It currently says to skip a file “whose
   complete UTF-8 bytes would exceed” the 160-KiB raw-bundle ceiling. Read
   literally, this excludes an individually oversized file but permits several
   individually small files whose sum exceeds 160 KiB. The later assertion that
   complete raw bytes plus boundaries are at most 160 KiB and the 192-KiB stdin
   ceiling can therefore be false. This can make the frozen selection
   impossible to render or cause post-selection truncation, which would
   invalidate Raw fairness.

   **Required repair:** define the admission check cumulatively: a candidate is
   accepted only when `current selected native bytes + exact frozen boundary
   bytes + candidate bytes <= 163840`. Continue the fixed vendor round-robin
   without replacement; if the six-file/all-available-vendor minimum cannot be
   met under this cumulative ceiling, stop the project freeze. Assert the raw
   section byte count and total rendered stdin byte count before every call;
   never truncate or substitute a file.

2. **Raw is not explicitly given the fact semantics used by the deterministic
   methods and oracle.** The quoted fixed instruction tells the model to answer
   the listed questions from source bytes, but the plan does not require the
   rendered prompt to include the frozen vendor-to-atom definitions, attempted-
   action/status treatment, ordering/tie rules, artifact path/rename/delete--
   recreate semantics, session ordering, and exact definitions of P0--P4 and
   the five cross-session templates. ProcGrep, the oracle, and the proposed arm
   receive those exact semantics in code. Asking Raw to infer them from names
   would measure semantic guessing as well as raw reconstruction and could
   manufacture a Raw loss.

   **Required repair:** include a fixed natural-language rendering of the full
   measurement semantics and all 20 template definitions in every Raw prompt,
   including the vendor action mapping needed for A1--A5 and the concrete
   P0--P4 path bindings. Freeze and manifest the prompt-template hash. It must
   still exclude instantiated answers, witnesses, selected evidence excerpts,
   normalized rows, and method outputs, and must remain inside the existing
   32-KiB instructions/questions and 192-KiB total ceilings.

### B2 — CLOSED

The revised plan removes candidate sampling and normalized-row selection. It
uses one source-only, deterministic set of 20 templates per project, fixes the
project/vendor/file selection order, requires exactly 30 questions per family
or stops before methods run, and defines P0--P4 without final-state or method
outputs. The primary Python source enumerator and separate `jq`/POSIX-shell
checker have a narrow declared sharing boundary and must agree before method
execution. Ordering, paths, worktrees, renames, delete--create generations,
multi-path calls, status treatment, sessions, and cutoff witnesses are fixed.
This closes the selection, independent-oracle, and common-eligibility defects
without human or model gold.

### B3 — CLOSED

The plan now names every official Claude/Codex/Gemini loader and adapter,
defines official atom counts and literal `Pattern`/`match_patterns` operations
for A1--A5, records B/C/D as explicit ProcGrep out-of-scope abstentions, and
forbids a path-aware ProcGrep extension. The proposed arm retains ProcGrep's
atom arrays unmodified and must establish byte identity before joining every
artifact edge to a frozen source call. The preflight exercises at least one
real closed session from all three vendors, all four fact families, every
method, the independent checker, and an actual Raw call. Official mechanism
engagement and isolation are now sufficient.

### B4 — Partially closed

Closed portions:

- All methods use the same 30-item denominator per family; unsupported methods
  abstain rather than exclude questions.
- The plan names trajectory-minus-ProcGrep and trajectory-minus-Raw B+C
  contrasts, keeps Final State and Counts as controls, defines the Raw score as
  the mean of three complete project calls, uses project/repetition-aware
  resampling, reports all projects, and numerically defines superiority,
  non-inferiority, Raw win, parity, and cost intervals.

Two decision defects remain:

1. **There is no accuracy veto for the proposed method on its claimed B+C fact
   families.** Correct factual coverage gives a wrong answer the same zero
   credit as abstention. Because official ProcGrep necessarily abstains on all
   B/C questions, even a low-accuracy method that answers or guesses broadly can
   have a positive coverage interval and satisfy the current “Positive versus
   ProcGrep” rule. Conditional exact accuracy and wrong rate are reported but do
   not constrain the paper verdict. That does not support a claim of reliable
   source-verifiable measurement.

   **Required repair:** add a numerical B+C selective-accuracy/wrong-rate veto
   for the trajectory arm to the positive ProcGrep decision. Freeze either an
   absolute conditional exact-accuracy floor with its finite-sample interval or
   an exact maximum wrong-answer rule. If the veto fails, the coverage contrast
   is mixed/invalid for a measurement-capability claim, not positive. Preserve
   all errors and abstentions.

2. **The efficiency gate tests non-inferiority in the wrong direction.** With
   `delta = trajectory - Raw`, the condition `lower bound >= -0.05` proves that
   the trajectory is not materially worse than Raw. It does not prove that Raw
   accuracy is comparable to the trajectory; it also passes when the trajectory
   is much more accurate. A lower-cost claim at “comparable accuracy” would then
   compare unlike outputs.

   **Required repair:** gate the Raw-versus-trajectory efficiency claim on the
   already defined symmetric parity condition—the entire accuracy interval lies
   in `[-0.05,+0.05]`—or an equivalent frozen two-one-sided equivalence rule.
   If trajectory accuracy is superior but parity fails, report cost
   descriptively only; do not claim efficiency at comparable accuracy.

### B5 — CLOSED

The revised plan supplies entrypoint paths, literal freeze/preflight/full/score
commands, environment and lock hashes, timeouts, terminal exit meanings,
recovery, and an upper-bound budget. Selected native bytes are copied and
hashed; source and later workspace cutoffs are ordered; revision/status checks,
untracked state, content/absence markers, and re-freeze rules are explicit.
The ignored access-controlled audit bundle preserves plaintext source,
questions, witnesses, prompts, responses, deterministic outputs, and costs
under one manifest, while the release bundle preserves pseudonymous
per-question answers/outcomes/costs/witness hashes sufficient to recompute
aggregates without disclosing native text or paths. This closes execution,
atomic-freeze, privacy, and auditability defects.

## Follow-up disposition

Do not begin preflight yet. Repair only the two residual B1 items and two
residual B4 items above, then return the same plan for the second and final
follow-up review. B2, B3, and B5 should not be reopened unless those repairs
change their contracts.

---

# Follow-up Review 2 — Final

## Verdict: PASS

I reread the complete current `plan.md` and checked the four residual repairs
from Follow-up Review 1. All original B1--B5 blockers are now closed. The
experiment remains directly matched to RQ7, uses no human or model-generated
gold, and is executable as a real three-vendor preflight followed by the frozen
full run.

## Final closure audit

### B1 — CLOSED

The source selector now applies the 163,840-byte limit to the cumulative exact
serialization: already selected native bytes, literal boundary bytes, and the
next complete file. It stops rather than truncating or substituting when the
fixed six-file/vendor requirements cannot fit. This makes the claimed 160-KiB
raw section and 192-KiB total stdin ceiling executable.

Every Raw prompt now embeds the same complete, answer-free measurement contract
used by the oracle and deterministic methods: vendor action mappings, ordering
and tie breaks, attempted-action/status and multi-path treatment, path and
artifact generation rules, session semantics, P0--P4 selection, all A1--D5
templates, canonical answer formats, and the concrete queried paths. The
definition is frozen as `question-spec.md`, bound by SHA-256 in prompts and
deterministic rows, and excludes answers, witnesses, normalized events, atom
sequences, and method outputs. Raw therefore tests reconstruction from complete
bounded source bytes rather than guessing the benchmark semantics.

The previously verified Codex `0.145.0` command and current feature disables
still establish the declared zero-tool condition; model, reasoning, call unit,
repetitions, byte/output/time ceilings, failure behavior, and cost accounting
remain frozen.

### B2 — CLOSED

No regression. The 20 templates per project remain fixed and source-only; no
ProcGrep, `agent-session`, model, prior result, or normalized row participates
in selection, eligibility, or truth. Exactly 30 items per family are required
before method execution. The two direct-source implementations must agree on
the fully specified artifact/session/cutoff semantics and immutable witnesses.

### B3 — CLOSED

No regression. Official ProcGrep is engaged through its pinned
Claude/Codex/Gemini loaders, adapters, atom arrays, and literal pattern
operations. Unsupported B/C/D facts are abstentions rather than a homemade
ProcGrep extension. The proposed arm must preserve the action spine byte for
byte and join artifact edges to frozen calls. The real preflight exercises all
three vendor paths, four fact families, five methods, independent checker, and
one actual bounded model call.

### B4 — CLOSED

The positive artifact/cross-session verdict now has explicit finite-corpus
reliability vetoes in addition to the positive coverage contrast: B+C correct
coverage must be at least 0.80, conditional exact accuracy at least 0.95,
wrong-answer rate at most 0.05, and each project's conditional accuracy at
least 0.80. A sparse or broadly wrong method therefore cannot beat ProcGrep's
out-of-scope abstentions merely by guessing.

The efficiency rule is also corrected. A formal lower-cost claim is permitted
only when the entire 95% interval for `trajectory - mean(Raw repetitions)` lies
inside the symmetric `[-0.05,+0.05]` accuracy-equivalence region and the
predeclared log wall-time interval is positive. One-sided trajectory
non-inferiority or accuracy superiority alone cannot be relabeled as a
parity-conditioned efficiency win. The common denominator, Raw repetition
estimand, hierarchical/project-block uncertainty, action-isolation veto, and
negative/mixed decisions remain fixed.

### B5 — CLOSED

No regression. Literal commands, versions and lock hashes, timeout and exit
semantics, upper-bound cost, immutable native copies, ordered source/workspace
cutoffs, worktree state, recovery rules, and the private-versus-release audit
artifacts remain fully specified. The private bundle supports direct result
audit while the pseudonymous release rows support aggregate recomputation
without publishing native text, paths, prompts, secrets, or rationale.

## Final disposition

**PASS for REAL PREFLIGHT.** No scientific or executability defect remains that
would invalidate the planned RQ7 result. Preflight may now test the frozen path;
it is mechanics evidence only, not a paper result. Any execution repair must
preserve the approved source universe, question specification, oracle,
baseline interfaces, budgets, metrics, and decision rules, and affected cells
must be rerun after a recorded deviation.

This is the second and final permitted follow-up review for this plan. The
approved scope does not require additional baselines, projects, annotations,
or claims.
