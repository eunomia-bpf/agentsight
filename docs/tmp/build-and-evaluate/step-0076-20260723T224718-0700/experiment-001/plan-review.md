# Independent Plan Review — Step 0076

**Method:** `research-experiment-design` PLAN REVIEW  
**Reviewer position:** independent of Step 0076 design  
**Current status:** Round 1 complete; later rounds pending revision

## Round 1 — Scientific Question and Same-Input Baseline Fairness

**Verdict:** **REVISE**

### Scientific value

The proposed comparison is relevant to fixed RQ1. It uses a real multi-run
task family, two additive measures, the accepted A2 annotations, and standard
pprof rather than a new visualization path. It also fills a concrete gap:
the paper currently shows the semantic Git case but has not materialized the
native-source and coarse-action organizations over the same source samples.
Its appropriate role is **supporting matched case evidence**, not a
population-level or headline attribution experiment.

The experiment is also close to the smallest useful design. It should not add
another workload, model, annotation run, user study, significance test, or
custom metric.

Three blocking issues prevent the current plan from supporting its stated
hypothesis fairly.

### Must-fix 1: remove the circular success test

The plan selects the 105-operation evidence set from the already accepted
`diagnose authentication` semantic subtree and then declares success if
AgentProf places that evidence in `diagnose authentication`. That statement is
true by selection: the candidate output defines both the tested set and the
expected candidate grouping. Projecting those members into native and coarse
views can be useful descriptively, but it is not independent evidence that
AgentProf discovered a better responsibility.

The minimum repair is to choose one of these two honest interpretations before
execution:

1. **Preferred minimal repair:** explicitly make this a fixed, adaptive,
   explanatory case projection. State that the task family and responsibility
   were discovered in the prior semantic case; the present run asks only how
   the *same candidate-defined members* appear in matched alternative
   organizations. Validity is then exact membership/mass preservation and
   faithful pprof projection. Do not use `supported/contradicted` language to
   present this as independent superiority or new attribution accuracy.
2. If a hypothesis test is required, define and freeze the SSH-authentication
   evidence IDs from an annotation-independent source criterion before
   opening any of the three profile organizations. That would require a real
   external/source oracle and is not necessary for this bounded case.

Also replace “does not ... choose a favorable subset.” The three-session Git
family is complete within that task family, but both the task family and the
authentication responsibility were selected after the prior semantic result
was observed. The correct description is **post hoc fixed case, complete
within the selected task family, with no row dropping after selection**.

### Must-fix 2: construct all three views from one auditable row/mass contract

The controls are freshly generated from filtered A2 operation files, while the
AgentProf condition reuses a pre-existing paper `.pb.gz`. Equal reported totals
alone do not establish that all conditions have identical
`(source_session, evidence_id, value)` multisets, source leaves, stack prefix,
and release behavior.

For a genuine same-input comparison, replay the accepted marks through the
same `agentpprof 0.2.37` binary from the exact same filtered count and token
files used by both controls. No annotation changes or inference are needed.
Require equality of the full `(source_session, evidence_id, value)` multiset
across all three conditions and verify the replay against the accepted paper
profile.

Pin the stack treatment so only the intended organization differs:

- use one common outer prefix, at least `project,agent`;
- use native occurrence fields only as the native treatment;
- use `action_kind,raw_action_key` only as the coarse treatment;
- use accepted `operation` marks only as the semantic treatment;
- retain the same source evidence as labels in every condition;
- include `tool`/source-kind leaf frames either in every condition or in none.

Otherwise extra `tool`, call, session, or agent frames can mechanically create
more stacks in one control, and “fragmentation” would partly be a command-line
choice rather than the organization being tested.

### Must-fix 3: correct the baseline role and avoid a redundant run

The plan calls coarse action the “strongest available deterministic
no-annotation semantic control,” but the adopted multi-resolution recurrence
constructor is the stronger existing no-label organization and has already
been evaluated on the complete CodeTrace population. The current wording is
factually and scientifically misleading.

Do not expand this case with another recurrence run merely to add a row.
Instead:

- label native source and coarse action as the two **missing case
  organization controls**;
- cite the existing complete same-input recurrence-versus-raw/A2 evidence as
  the stronger automatic comparison already available elsewhere in RQ1/RQ3;
- state that Step 0076 is not intended to replace that population comparison.

This preserves the plan's minimal scope while satisfying baseline-selection
honesty.

### Round 1 disposition

The experiment remains admitted as a compact supporting case-control
materialization. Execution should wait for the three minimal revisions above:
honest adaptive-case interpretation, one identical replay/input contract with
matched stack treatment, and corrected control/baseline roles. After revision,
Round 2 will review standard pprof measurement and leakage only; Round 3 will
review executability and unnecessary complexity/scope expansion.

---

## Round 2 — Standard pprof Measurement and Leakage

**Verdict:** **APPROVE**

Round 1 is closed. The revised plan explicitly treats the Git task family and
`diagnose authentication` membership as a post-hoc, candidate-defined case;
retains every operation in all three selected executions; regenerates all six
profiles from the same filtered count/token rows with the same current binary;
uses a common `project,agent` prefix and `call,tool` suffix; and limits the
middle treatment to native occurrence, coarse action, or accepted operation
marks. Recurrence is now correctly cited as the stronger existing
population-level no-label comparison rather than omitted by calling coarse
action strongest.

The measurements are appropriate for this bounded explanatory projection:
pprof cumulative sample mass, exact total mass, source labels, and the full
composition of the fixed evidence set by source/action fields. Count and token
widths are additive pprof sample types, not new metrics. Stock-pprof readback
and exact `(source_session, evidence_id, value)` equality are valid
correctness checks. No statistical test is needed for a deterministic
three-execution case.

Leakage is now honestly bounded. Accepted semantic annotations define the
responsibility members and are used only after native/coarse construction to
project those same members. Consequently the result may describe how a prior
semantic finding appears under matched organizations, but may not establish
independent discovery, annotation accuracy, universal superiority, or a
population effect. The revised acceptance and paper authorization respect that
boundary.

The reported “unique stack count” must remain descriptive because the common
`call,tool` suffix contributes to full-stack cardinality; it is not an
independent compactness or quality score. This does not block the planned
cumulative-mass and composition result.

---

## Round 3 — Executability, Complexity, and Scope

**Verdict:** **REVISE**

The scientific scope is now minimal and coherent. Two widths by three
organizations form one integrated same-input case, and reusing accepted marks
avoids a redundant annotation or recurrence run. No new workload, model,
frontend, renderer, significance test, or custom score is warranted.

One blocking executability issue remains: the plan still specifies only a
procedure, not a runnable authoritative workflow. In particular, it does not
name the mechanical workspace-path-to-operation-mark adapter or give its
command, the three exact source-session IDs, fixed input/output paths, the six
`agentpprof` commands, stock-pprof inspection commands, or a real preflight.
The skill requires one runnable command and a real end-to-end preflight before
the full run; leaving these choices to implementation could silently change
the row filter, stack contract, or accepted-path replay after approval.

### Minimal blocking repair

Add one compact Execution section that freezes:

1. the three literal source-session IDs and authoritative count/token input,
   accepted workspace, binary, and output-directory paths;
2. either one named measurement-script command that deterministically emits
   the filtered rows, equivalent operation marks, six profiles, projection
   table, and inspection logs, or the explicit adapter plus six CLI commands;
3. the exact stack strings already approved:
   `project,agent,source_session,prompt,call,tool`,
   `project,agent,action_kind,raw_action_key,call,tool`, and
   `project,agent,operation,call,tool`;
4. one real one-session/one-width end-to-end preflight using the same adapter,
   binary, mark replay, stock pprof, and raw-output path; its observations are
   diagnostic only;
5. a completion rule requiring 489 unique evidence IDs per width, identical
   `(source_session,evidence_id,value)` multisets, exact 489/4,558,192 masses,
   exact accepted-path expansion for all rows, six readable pprofs, and
   reproduction of the fixed 105/2,103,587 responsibility membership/mass.

This is ordinary reproducibility glue, not a new experiment-control interface.
After this single execution repair, no scientific or scope blocker remains and
the plan can be approved without further expansion.

---

## Round 3 — Final Convergence Check

**Verdict:** **APPROVE**

The Round 3 executability blocker is closed. The revised plan now freezes:

- the three literal source-session IDs;
- existing authoritative count/token inputs, accepted trace workspace,
  current release binary, and one raw-output directory;
- one identical anchored `jq` row filter for both widths;
- a fixed mechanical accepted-path-to-operation-mark conversion that covers
  the 489 tool/evidence rows without inference, renaming, or boundary changes;
- one excluded real one-session semantic-count preflight using the final mark
  interface, stack, binary, and stock pprof;
- all six final count/token-by-native/coarse/semantic pprof invocations with
  the approved common prefix/suffix and middle treatments;
- stock `go tool pprof -top` and `-tags` inspection; and
- completion checks for unique evidence coverage, identical row/value
  multisets, exact 489 and 4,558,192 masses, accepted-path expansion, six
  readable profiles, and the fixed 105-operation/2,103,587-token explanatory
  projection.

The authoritative inputs exist and their fixed Git subset contains exactly 489
unique evidence IDs in each width with masses 489 and 4,558,192; the accepted
trace contains exactly 489 corresponding tool/evidence rows across the three
sessions. The workflow is therefore executable without changing the approved
scientific question or leakage boundary.

No scientific, measurement, fairness, leakage, executability, complexity, or
scope blocker remains. Step 0076 Experiment 001 is approved for real preflight
and full execution as a post-hoc matched explanatory RQ1 case projection.
