# RQ7/F10 Independent Plan Review — Round 1

**Reviewed:** 2026-07-22  
**Reviewer role:** independent experiment-plan reviewer; no implementation or
result was changed  
**Verdict:** **BLOCK**

## Bottom line

The narrow scientific question is useful: measure which source-verifiable facts
are recoverable from final state, counts, an official action-only
representation, bounded raw-log access, and an artifact-linked trajectory.  The
plan also correctly refuses human/LLM gold and correctly expects ProcGrep to win
or tie on questions native to its action alphabet.

The current draft cannot yet produce a valid matched comparison.  It does not
freeze the raw source universe needed by the oracle and Raw-log LLM, does not
specify executable query interfaces, mixes resolvable negatives with
unresolvable/ambiguous cases, and requests evidence precision/recall without a
unique reference evidence set.  Most importantly, code independence alone does
not make same-artifact lineage an independent oracle: both implementations
would still infer the same non-native relation from the same ambiguous shell
commands.  These defects can change every reported F10 value and therefore
block execution rather than merely requiring presentation polish.

## Evidence checked

- The reviewed plan is
  `experiment-rq7-20260722T013003-0700/plan.md`.
- The frozen RQ1 corpus contains 2,049 admitted sessions and 206,249 Tool
  actions, but its committed per-project event files are normalized
  `RepositoryTrace` exports, not frozen native JSONL/JSON records.  The RQ1
  `projects.json` records aggregate session counts and one repository revision;
  it does not record every native source path, source-prefix hash, worktree
  root, and worktree revision needed to replay the same raw universe.
- I independently checked the pinned ProcGrep revision
  `2e8277003dacaa774b5ef61ba150ae03a4f06693`.  It does contain Claude Code,
  Codex, and Gemini CLI adapters.  Its official `Trace` contains a `trace_id`,
  an ordered list of canonical atoms, and metadata; it does not retain native
  source IDs or file paths.  Its official pattern matcher evaluates regular
  expressions over the space-joined atom sequence.  Thus ProcGrep is runnable
  on all three vendors in principle, but native evidence-ID and artifact-path
  scoring are not part of the pinned representation.
- The frozen RQ1 mutation table contains 66 explicit rename rows, but they occur
  in only three projects (AgentSight 27, ActPlane 35, and eunomia.dev 4).  A
  stratum-wide 30-question/four-project gate therefore cannot justify a rename
  result even if other artifact-linked templates make the aggregate stratum
  pass.  This is exactly why the gate must be evaluated per template family as
  well as per stratum.

## Blocking findings and minimal repairs

### 1. The matched raw source universe is not frozen

Lines 15--16 promise the same admitted sessions and cutoff, but only the
normalized RQ1 exports are frozen.  Re-reading live native files later can
include appended events, rewritten files, or a different final workspace.  It
also prevents a third party from reproducing Raw-log LLM retrieval or the
claimed source-only oracle.

**Required minimal repair:** freeze one machine-readable source manifest before
question generation.  For every admitted session it must contain project,
vendor, session ID, native path, admitted byte prefix or admitted record
indices, SHA-256 of that exact prefix, and cutoff.  Preserve the exact admitted
native prefixes in a content-addressed compressed archive (or a declared
external archive plus immutable hashes).  Also freeze every worktree ID to its
root and Git revision.  Final-state questions must query those revisions; do
not query a later mutable checkout.  If untracked final state was not captured
at the cutoff, mark it unavailable rather than reconstructing it from the
current filesystem.

### 2. The five method interfaces are names, not executable baselines

The plan gives no commands, input/output schemas, or permitted information for
any method.  In particular:

- Final State must be pinned to a worktree revision/tree and cannot silently
  consume RQ1 artifact output.
- Counts needs a frozen count schema and can answer only templates expressed in
  that schema.
- ProcGrep needs the pinned install command, official vendor loaders/adapters,
  the exact official atom/pattern operation used for each action-only template,
  and a statement that paths and cross-session lineage are unavailable.  A
  wrapper may preserve `(trace_id, atom ordinal)` only for output alignment; it
  must not add file paths, source arguments, or cross-session state to the
  ProcGrep condition.
- Artifact Trajectory needs exact query functions and must read the same frozen
  native manifest, not its own differently filtered discovery pass.
- Raw-log LLM needs a model identifier/version, provider/CLI, temperature/seed
  behavior where exposed, fixed prompt, deterministic source-only retriever,
  per-question retrieved-byte/context/output limits, retry/cache policy,
  maximum calls, token/dollar cap, and an output schema with answer,
  abstention, and cited IDs.

**Required minimal repair:** add one real command, output paths, completion rule,
and failure/N/A rule for each condition.  Run one real Claude, Codex, and Gemini
adapter preflight before admitting ProcGrep.  If no reproducible model is
available, predeclare Raw-log LLM as an optional condition and render it as N/A;
do not let its absence stop the deterministic comparison or silently replace it
with an informal Agent answer.

### 3. The proposed oracle is independent in code only, not in truth

Lines 31--47 prohibit shared aggregation code, which is necessary but
insufficient.  Native records directly establish tool calls, explicit
arguments, timestamps, statuses when present, session membership, and source
order.  They do not directly establish all Bash-induced file effects or a
stable file identity across arbitrary rename/delete/recreate sequences.  A
second parser implementing the same inferred semantics is not an external
oracle, and selecting questions from the proposed trajectory would be
circular.

**Required minimal repair:** write a declarative, method-neutral fact
specification first, then implement the oracle directly over frozen native
records without importing `agent-session`, `agentvis`, RQ1 CSVs, or ProcGrep.
Restrict scored lineage questions to source-explicit operations whose paths and
operation are present in the native record and whose identity follows the
declared rules.  Bash-inferred effects, ambiguous path resolution, directory
scope, and missing status stay `UNAVAILABLE` or are excluded as ambiguity; they
must not become gold through another shell parser.  Candidate anchors and
question sampling must come only from this source-only oracle frame, before any
method output is read.  The resulting claim is conformance to declared
source-visible artifact semantics, not completeness of real system effects.

### 4. Positive, negative, unavailable, ambiguity, and abstention currently
contradict one another

Lines 43--45 say to include unavailable and ambiguity cases and then drop every
case that cannot be independently resolved.  If all unavailable cases are
dropped, `correct abstention` has no denominator.  A negative fact is also not
the same thing as missing evidence.

**Required minimal repair:** freeze four oracle dispositions:

1. `TRUE` and `FALSE`: resolvable closed-world answers at the cutoff; both enter
   exact-answer scoring.
2. `UNAVAILABLE`: the frozen admitted source lacks a required field or horizon;
   only abstention is correct.
3. `AMBIGUOUS_EXCLUDED`: competing parses or an unfrozen state prevent a unique
   answer; report counts but do not sample or score it.

Define the method answer schema and exact match for Boolean, categorical,
integer, event-ID, path, and ordered-list answers.  Never turn no answer into
`FALSE`; accuracy is undefined when a method attempts zero questions.

### 5. Templates and sampling are not frozen, and the 30 x 4 gate can hide
unsupported subclaims

The four bullets are broad families, not fixed questions.  Sampling source IDs
first does not define eligible anchors, balance positive/negative/unavailable
cases, prevent one large project from dominating, or keep template authors
blind to method outputs.  It also allows abundant next-access questions to mask
rename/delete--recreate coverage.  RQ1 already shows that rename cannot meet a
four-project gate.

**Required minimal repair:** enumerate every template with:

- natural-language question and typed answer;
- eligible source-only anchor frame;
- look-back/look-ahead horizon and cutoff behavior;
- required evidence and unavailable condition;
- methods that are expected to support it by interface, not by hoped-for
  output.

Use one published seed and sampling without replacement.  For each admitted
stratum require at least 30 scored questions drawn from at least four projects,
with per-project counts shown; additionally report the same eligibility gate
for every constituent template.  An under-covered template remains
coverage-only and may not borrow another template's rows.  Freeze quotas before
running methods, keep all sampled failures/abstentions, and do not backfill a
hard question after seeing an answer.

### 6. Evidence precision/recall is undefined for these facts

There is generally no unique “all and only relevant” source-ID set.  For a
negative next-access answer, proving absence may require scanning an entire
suffix; a method can cite a sufficient minimal pair, a larger valid interval,
or a final-state tree.  Treating one arbitrary oracle set as all relevant IDs
would make precision/recall an implementation-agreement score.  ProcGrep also
returns trace/atom positions rather than native evidence IDs.

**Required minimal repair:** replace evidence precision/recall with fully
automatic checks that the data supports:

- **citation validity:** every returned reference exists in the admitted source
  universe (ProcGrep may cite trace ID plus atom ordinal);
- **answer sufficiency:** a template-specific deterministic checker can replay
  the answer from the returned references, where such a checker is defined;
- **evidence burden:** number and bytes of returned references and total source
  records/bytes examined.

Report sufficiency as N/A where the method's official interface cannot expose
supporting evidence.  Missing native IDs from ProcGrep must not globally block
the comparison, and an external ordinal-to-source crosswalk must not leak path
information into its answer logic.

### 7. Accuracy/coverage and cost comparisons need fixed estimands

“Without materially reducing accuracy” (lines 74--75) has no threshold.  The
plan also omits offline build/index time and size, so trajectory lookup could
appear cheaper than raw reading after excluding its preprocessing.  Bootstrap
over 30 correlated questions or only four to six author-associated projects
would not support a population claim.

**Required minimal repair:** make exact answer correctness a gate for the
deterministic proposed method: any wrong attempted answer invalidates that
template until repaired and rerun.  Then report coverage differences as paired
descriptive counts/rates on the identical sampled questions, separately by
project and stratum, with no broad population inference.  For every method
record cold build time, index/output bytes, peak RSS, warm query latency,
records/bytes examined, and total wall time; for the LLM additionally report
calls and input/output tokens.  Freeze whether costs are one-time or per-query
and use the same hardware.  Do not bootstrap unless a defensible independent
block and estimand are explicitly named; a six-case table is preferable to a
misleading confidence interval.

### 8. F10 has no non-fabrication/N/A rendering contract

The four requested panels cannot all be populated if the LLM is unavailable,
ProcGrep returns no native evidence IDs, or a template misses the gate.  The
current plan would either drop rows invisibly or invite zeros that look like
measurements.

**Required minimal repair:** freeze F10 as a conditional figure:

- Panel A: attempted accuracy versus answer coverage, with denominators and
  `N/A` when no attempt is possible;
- Panel B: citation validity/sufficiency and evidence burden only where defined;
- Panel C: cold preprocessing plus warm-query costs, with the optional LLM
  clearly marked unavailable if not run;
- Panel D: paired Artifact Trajectory minus ProcGrep coverage on the common
  sampled questions, showing action-only positive controls and
  artifact/cross-session capability gaps separately.

Every cell must carry `n`, project coverage, and status (`measured`,
`coverage-only`, or `N/A`).  F10 may be generated only from frozen result rows;
no illustrative or imputed values are allowed.

## Minimal executable redesign

The smallest defensible experiment remains one integrated RQ7 run:

1. Freeze the exact six-project native prefixes, worktree revisions, and a
   source manifest tied to the RQ1 cutoff.
2. Freeze a compact source-only fact specification and oracle dispositions.
   Use only explicit native facts for gold; retain ambiguous shell effects as
   coverage facts.
3. Generate a seeded question table before method execution.  Keep four
   strata, but gate and report each template separately.
4. Preflight official ProcGrep adapters on one real session per vendor, then use
   only its canonical atoms and official pattern semantics.  Preserve no path
   information in this condition.
5. Run Final State, Counts, ProcGrep, and Artifact Trajectory on the same
   question IDs.  Run the Raw-log LLM only if model, retriever, budgets, and
   total cost are frozen and available; otherwise retain an explicit N/A row.
6. Score exact answers, abstention, citation validity/sufficiency where defined,
   and full cold/warm cost.  Preserve all negative and unavailable cases.
7. Require an oracle audit before method execution and an independent result
   audit before copying F10 into the paper.

This redesign preserves the intended contribution while avoiding human gold,
a new general IR, or a large benchmark framework.  If exact native prefixes or
cutoff-matched worktree state cannot be frozen, RQ7 must stop at a source
coverage report; it cannot claim an accuracy comparison.

## Decision

**BLOCK.** Revise the same plan once to freeze the source universe, fact
templates/dispositions, method commands and budgets, evidence scoring, costs,
template-level 30/four-project gates, and conditional F10 contract.  A second
review can pass without demanding new workloads or more baselines if those
items are executable and the Raw-log LLM is either fully frozen or explicitly
optional/N/A.
