# Independent Plan Review 002

**Plan:** `experiment-plan.md`  
**Verdict:** **REVISE**

## Blocking concern

The experiment does not yet have one predeclared, independently measurable
primary outcome. Its current hypothesis requires all of the following:

- reduced “avoidable” cross-session fragmentation;
- repaired “clearly” coarse or degenerate regions;
- preservation of coverage and additive mass; and
- incremental time and token/input cost “materially” below a fresh full pass.

The first two properties are undefined judgments, the third is a validity
check, and the fourth is a separate RQ4 cost endpoint. The plan then allows
repetition while a “high-value issue” remains and selects the final iteration
“from the case evidence.” Consequently, almost any mixture of fewer
singletons, fewer warnings, deeper stacks, cleaner figures, or lower per-round
input can be chosen retrospectively as success.

This is not fixed by the statement that fewer singletons or greater depth alone
is insufficient. The plan still does not say what *is* sufficient.

## Must-fix 1 — Separate the primary effect, controls, and cost

Use one primary mechanism hypothesis:

> Relative to the same automatic backend's fixed first pass,
> aggregate-diagnosed local revision improves independently audited
> answerability of the two fixed case-study questions without erasing
> source-supported semantic distinctions.

Classify the remaining measurements before execution:

- source coverage, evidence-label preservation, stock-pprof readability, and
  per-view additive-mass conservation are validity checks;
- tag reuse, singleton fraction, warning counts, unique stacks, and depth
  distribution are explanatory mechanism measurements;
- cumulative revision tokens and elapsed time relative to a measured fresh
  full pass are the coupled RQ4 secondary endpoint.

Do not combine these into an undeclared score. Predeclare separate judgments
for primary usefulness and cost. A quality improvement with excessive cost
supports only the primary mechanism; cheap revision without quality
improvement supports only a practicality/input-volume observation; disagreement
between the two cases is mixed and case-bounded.

## Must-fix 2 — Operationalize the fixed user questions

Before any revision, freeze a compact answerability rubric and apply it
identically to iteration 0 and the terminal revised profile.

At minimum:

- **Git:** using only the profile and its source drilldown, identify the shared
  responsibility, its rank, the contributing sessions, direct and cumulative
  operation/token mass, the supporting evidence IDs, and whether that
  responsibility reached the requested terminal condition.
- **AgentReward:** after annotations are frozen and outcome weights are applied,
  use the complete signed 338-pair profile to identify the strongest
  failed-side and successful-side paths, their signed mass/share, contributing
  sessions, and supporting evidence IDs.

The independent result reviewer should score completeness, numerical
reproducibility, and source support for those required answer fields. A reduced
warning or singleton count with no improvement in those fields is explanatory,
not a positive primary result. A source-unsupported merge, an erased
distinction needed to answer the question, or an outcome-derived operation name
vetoes a usefulness claim.

This rubric is a read-only assessment of the two already-fixed questions. It
does not require a new benchmark, another workload, a hand-annotation
condition, or a custom paper metric.

## Must-fix 3 — Prevent result-aware revision and final-iteration selection

The retained cases already have known SSH-authentication and
recovery/completion narratives. In the proposed procedure, the same backend
that revises annotations also opens each generated profile, decides whether the
user question is answerable, decides whether another “high-value” issue
remains, and chooses the final candidate. Even with AgentReward outcome labels
hidden, this is post-selection against known case conclusions.

Before execution:

1. Freeze and retain the exact backend-visible payload.
2. Exclude outcome labels, human stages, prior case narratives and figures,
   named expected focal paths, the answerability rubric's expected answers,
   and result-review judgments.
3. Feed only the current annotation, deterministic diagnostics, and the
   implicated source interval for the current issue.
4. Process issues in a fixed recorded order.
5. Stop at the first complete pass in which every issued item has been
   considered after local rereading and the backend accepts no annotation
   change.
6. Treat that converged output as final. Do not select an earlier or later
   “best-looking” iteration after comparing figures or user-question answers.
7. If no no-change pass is reached, report the run incomplete rather than
   promoting a favorable prefix.
8. Reveal AgentReward outcome labels and construct the signed profile only
   after both iteration-0 and revised annotations are frozen.
9. Give iteration identities in masked order to the independent result reviewer
   when applying the answerability rubric, then unmask for interpretation.

The backend may inspect the aggregate and implicated source context—that is the
mechanism being tested. It must not see or optimize against the answer used to
judge that mechanism.

## Predeclared interpretation

The revised plan should state:

- both cases improve on the fixed rubric with no validity veto: primary
  hypothesis supported for these two cases;
- neither improves, or either becomes source-invalid: contradicted;
- one improves and one does not: mixed, case-bounded;
- masked review cannot distinguish them or required artifacts are incomplete:
  inconclusive;
- cumulative local revision cost below the measured fresh full pass: RQ4 cost
  prediction supported;
- cumulative cost equal to or above it: RQ4 cost prediction contradicted.

## Final decision

**REVISE.**

The aggregate-feedback mechanism remains worth running, but execution should
not begin until “more useful” is a fixed, source-grounded primary comparison
and the revising backend can no longer choose the final artifact using the same
case conclusions later reported as success.

---

## Round 2 review

**Round 2 verdict: REVISE**

The revision closes most of both reviews:

- It now states one primary mechanism hypothesis and separates validity
  checks, explanatory diagnostics, and the RQ4 cost endpoint.
- It rejects the inherited workspaces as iteration-0 evidence and names the
  same fresh Codex backend, model, reasoning effort, instruction, batch
  assignment, concurrency, and retry rule for the complete first pass.
- Its AgentReward visible-field allowlist excludes pair IDs, pair side,
  outcome/reward fields, expert/human labels, signed profiles, expected paths,
  prior narratives/figures, and answer-review results. Outcomes are opened only
  after both annotations are frozen.
- It processes issues in deterministic order, stops on the first complete
  no-change pass, reports repeated states as non-convergence, imposes neither a
  target depth nor an arbitrary iteration cap, and forbids retrospective
  candidate selection.
- It records actual Codex token fields, logical payload tokens under a named
  tokenizer, failures/retries/concurrency, per-pass wall time, cumulative
  revision values, CLI time/RSS, and stock-pprof replay time.
- It masks iteration identity for an independent answerability review and
  predeclares positive, mixed, contradicted, inconclusive, and separate-cost
  interpretations.
- The structured CLI diagnostics are implemented, not merely promised:
  depth-mass, tag occurrence/session membership, lexical near-name candidates,
  and bounded hierarchy issues are present in CLI JSON. The relevant
  annotation-workspace unit and integration tests pass.

Three narrow ambiguities remain blocking because each can change the declared
primary or cost verdict.

### Remaining must-fix 1 — Make the semantic seed provenance truthful

The plan says a fresh first-pass payload already contains “seed
session/prompt annotations,” while `automatic-backend-instruction.md` tells the
backend to preserve every mandatory session and prompt annotation. Their tag
values and provenance are not defined.

If those semantic tags come from either retained case workspace, the baseline
is not a fresh complete pass and can expose prior case conclusions. If they are
created outside the measured backend call, the claimed complete automatic
construction cost omits part of annotation construction.

Before preflight, specify one of these source-only paths:

1. the fixed backend creates and names every mandatory session/prompt
   annotation during the measured first pass; or
2. a named deterministic source adapter creates fixed generic seeds, list
   their exact rule and tags, use the identical seeds in both conditions, and
   narrow the claimed backend scope and cost boundary accordingly.

Do not preserve unexplained semantic tags from an accepted workspace.

### Remaining must-fix 2 — Define the masked improvement relation

The rubric now classifies every required field along completeness, numerical
reproducibility, and source support, but the plan still says a case “improves”
without defining how mixed field changes are resolved. For example, the
revision could make one rank answer complete while making one mass answer
non-reproducible. The current text leaves that case available for
post-selection.

Use a fixed non-scalar rule, such as:

> A revised case improves only if it has no regression on any required rubric
> field or dimension and has at least one strict improvement. Any tradeoff is
> mixed/inconclusive for that case; any source-unsupported field triggers the
> existing validity veto.

The masked reviewer must return the field matrix before iteration identities
are unmasked; the root then applies this mechanical relation. This closes the
original primary-outcome blocker without inventing a paper metric.

### Remaining must-fix 3 — State the actual Codex counter calculation

The plan names the correct Codex fields but says only that they are computed
“from the session's first and final `token_count` events.” State the arithmetic
so cumulative session counters cannot be mistaken for per-run usage:

- for each rollout and each cumulative token field, record the final counter
  minus its pre-invocation/first-event counter, with absent initial values
  treated only according to the documented event semantics;
- sum those rollout deltas across all revision calls, including failed calls
  and retries;
- record elapsed wall-clock boundaries for each complete condition under the
  fixed concurrency, then sum revision-pass elapsed times for the cumulative
  comparison; and
- keep cached, uncached/input, output, and reasoning-output fields separate
  rather than collapsing them into an undocumented total.

With those three clarifications, the truthful baseline, leakage control,
convergence, masked primary comparison, cost accounting, and executable
diagnostic path will be sufficiently fixed for real preflight. No new
workload, backend, depth rule, annotation interface, or baseline is needed.

---

## Round 3 review

**Round 3 verdict: PASS**

The revised plan and fixed backend instruction close all three remaining
blockers:

1. **Fresh automatic baseline:** each case now materializes a source-only
   workspace with an empty `annotation.json`; no semantic annotation is copied
   from a retained case. The measured fixed-backend first pass creates and
   names every mandatory session and prompt annotation from source evidence,
   along with optional recursive annotations. The inherited workspaces remain
   excluded from iteration 0.
2. **Masked primary relation:** every required answer field is evaluated for
   completeness, numerical reproducibility, and source support before
   iteration identities are unmasked. A revised case improves only with no
   regression in any field or dimension and at least one strict improvement;
   a tradeoff is mixed, an identical matrix is no change, and the existing
   source-validity veto remains in force. This removes retrospective choice
   from the primary verdict.
3. **Actual cumulative Codex cost:** each rollout records the final cumulative
   token counter minus the counter immediately before the invocation, uses a
   documented zero origin only when valid, and reports ambiguous origins
   instead of guessing. Deltas include failed calls and retries and keep input,
   cached input, output, and reasoning output separate. Each complete
   condition has fixed start/completion wall-clock boundaries, and cumulative
   revision wall time is the sum of complete revision-pass elapsed times under
   the fixed concurrency.

The earlier blockers also remain closed: the AgentReward annotation payload is
outcome-blind under an explicit field allowlist; convergence is the first
complete no-change pass or a reported repeated-state non-convergence, with no
target depth or arbitrary iteration cap; outcomes and expected answers remain
sealed until annotations are frozen; and the structured CLI diagnostics have
an executable, tested path.

The plan now has a truthful same-backend comparison, a non-post-selected
primary decision, exact auditable cost accounting, validity checks, terminal
completion rules, and a real preflight. It may proceed to real preflight
without adding another backend, workload, baseline, depth rule, or control
interface.
