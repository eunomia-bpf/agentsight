# Agent reader review of two workspace trajectory briefs

## Review protocol

I first read only:

- `agentvis/output/academic-writing-skills-trajectory-brief.md`
- `agentvis/output/ActPlane-trajectory-brief.md`

I formed the process diagnoses below before opening any native session. I did
not read `diagnose.rs` or any other implementation file. I then followed
report-provided `source_file` and `call_id` anchors for exactly six spot checks.

## Overall verdict

The brief is substantially more useful than a linear log as a **triage index
for an Agent**. It compresses tens of thousands of Tool events, joins work
across native-session boundaries, names persistent artifacts, and supplies
source anchors. I could decide where to investigate next without scanning the
underlying logs.

It is not yet a sufficient handoff artifact on its own. Several prominent
numbers measure normalized file effects rather than Agent decisions, elapsed
time, or independent work episodes. Generated files, synthetic smoke-test
workspaces, broad file-listing commands, and unrecognized validators can
materially distort the apparent diagnosis. The report should therefore be
consumed as:

> candidate pattern → exact source anchors → targeted verification

and not as:

> candidate pattern → established cause, waste, correctness, or progress.

## Most important actionable process diagnoses

### 1. ActPlane has a sustained paper/design hotspot that must be reconciled with the implementation

**Exact report facts under the current detector.** Documentation accounts for
9,198 reads and 4,896 confirmed mutations, compared with 4,829 reads and 613
confirmed mutations for code. `docs/papers/sections/04-design.tex` is the top
cross-session artifact with 558 confirmed mutations across 20 native sessions.
The `docs` module dominates 91 sessions. These are action counts, not elapsed
time.

**Interpretation.** The project repeatedly revisited its design account across
many contexts. This may be legitimate paper convergence, but it creates a high
risk that the prose, implementation, and evaluation assumptions have drifted
apart. The counts alone do not show that the work was wasteful.

**Action for the takeover Agent.** Treat
`docs/papers/sections/04-design.tex` as the first audit anchor. Compare its
current mechanism claims with the corresponding `bpf`, `collector`, and
`crates` behavior, then inspect the 20-session mutation sequence by coarse
episodes rather than reading all 558 edits. Before further prose work, identify
which design claims are already implemented, experimentally supported, or
still aspirational.

### 2. ActPlane contains a large validation/debugging regime, but “test treadmill” is not established

**Exact report facts under the current detector.** The report recognizes 1,558
successful and 203 failed validations. It identifies 1,668 validation calls
without an intervening confirmed repository mutation and a longest such run of
632 calls. One highlighted Codex session has 890 successful and 146 failed
validations but only 18 confirmed repository mutations.

**Interpretation.** There is enough repeated validation to justify inspecting
the workflow. However, the spot check shows that this regime includes repair of
corrupted build artifacts and rebuilds that change generated/system state
without changing a repository source file. Consequently, “632 validations
without mutation” does not mean 632 identical or useless tests, nor does it mean
that the Agent made no state-changing progress.

**Action for the takeover Agent.** Partition the run by command family,
outcome transition, and generated-state repair:

1. repeated identical checks with unchanged outcomes;
2. fail → environment cleanup/rebuild → pass;
3. fail → source mutation → pass;
4. deliberate coverage matrices or flake repetitions.

Only category 1 is a credible harness-waste candidate. Preserve the existing
environment diagnosis if the corrupt incremental cache recurs; otherwise avoid
re-running the full validation matrix before a relevant change.

### 3. ActPlane carries unresolved change state across sessions and needs a concrete handoff queue

**Exact report facts under the current detector.** The report counts 230
pending mutations at session ends, 159 later-session supersessions, and 340
later-session validations. It also reports 123 artifacts mutated in more than
one native session. These relations are conditional on the recognized
validation classifier.

**Interpretation.** Work regularly crosses context boundaries instead of being
closed inside one session. This is a real long-horizon coordination concern,
but it does not imply that every pending mutation is defective.

**Action for the takeover Agent.** Before starting new work, request or derive a
ranked table of the currently unresolved artifacts with:

- last mutation session and call;
- first later validation or supersession;
- current cutoff presence/status;
- module and artifact kind;
- exact validator command and result.

The present brief gives the aggregate and a few recent witnesses, but not the
full actionable queue. The queue, not the aggregate `230`, should drive the
handoff.

### 4. `academic-writing-skills` has a real orchestration-specification hotspot, but the sample looks like deliberate refinement

**Exact report facts under the current detector.** The repository has 255
confirmed mutations, of which 244 are documentation mutations. Ten artifacts
are mutated across sessions. The top artifact,
`skills/auto-research-orchestrator/references/hierarchical-research-state-machine.md`,
has 68 mutations across three native sessions.

**Interpretation.** The state-machine specification is the durable center of
work and should be treated as a high-risk consistency surface. The checked edit
adds a precise backward-compatibility rule for historical step directories; it
supports continued refinement, not by itself “churn” or failed work.

**Action for the takeover Agent.** Review this file together with
`skills/auto-research-orchestrator/SKILL.md` and its scripts for duplicated or
contradictory rules. Collapse adjacent edit calls into semantic change episodes,
then ask whether each episode resolved a distinct requirement. Do not use the
raw count of 68 as a defect signal.

### 5. The apparent absence of validation in `academic-writing-skills` is primarily a measurement blind spot

**Exact report facts under the current detector.** Across 17 included sessions,
the report recognizes zero successful and zero failed validations, while
recording 255 confirmed mutations. It therefore classifies all 255 mutations as
unvalidated or superseded.

**Interpretation.** This does **not** establish that the repository was never
validated. The checked native evidence contains an explicit
`check_progress.py` smoke test over a synthetic repository; it returned the
expected warning and `exit=1`, yet the brief reports no recognized validation.
For a skill/documentation repository, useful checks may not resemble
`cargo test`, `pytest`, or a conventional build.

**Action for the takeover Agent.** Define repository-specific validators before
acting on validation-lag:

- script smoke tests with their expected exit semantics;
- Markdown/link/schema checks;
- skill-package structure checks;
- scenario fixtures for state-machine transitions.

Until then, report “no recognized validation,” never “no validation.”

### 6. Skill-associated footprints are useful audit targets, not causal diagnoses

**Exact report facts under the current detector.** In ActPlane,
`paper-writing-style` is associated with five sessions containing 568
documentation mutations and zero recognized validations; `deep-research` is
associated with three sessions containing 1,478 documentation mutations and 23
recognized validations. In `academic-writing-skills`,
`agent-friction-analysis` is observed in one session with no confirmed
repository mutation.

**Interpretation.** These are same-session associations. They do not establish
that a skill caused the mutations, prevented validation, or wasted effort. The
academic-writing spot also shows that a skill can launch broad analysis and
subagent work whose outputs do not become mutations in the current repository.

**Action for the takeover Agent.** Use the footprint to select sessions for an
audit of the harness:

- Did the skill prescribe concrete exit criteria?
- Did generated documents get consulted in a later decision?
- Did the session run the validator appropriate to its artifact type?
- Did repeated skill invocations rewrite the same claim without new evidence?

Do not rank skills by mutation volume alone.

## Signals that are misleading, too coarse, or not directly actionable

### Coverage is prominent but unexplained

ActPlane includes 139 of 602 parsed / 604 candidate sessions; the academic
repository includes 17 of 25 parsed / 26 candidate sessions. This is an exact
coverage fact, but the report does not explain exclusions or show whether
excluded sessions cluster in particular dates, vendors, or work phases. A
takeover Agent cannot tell whether the summary covers the decisive work.

**Needed:** exclusion-reason counts and a chronological coverage strip.

### “Reads before first mutation” can be inflated by one enumeration command

The academic re-grounding witness is a single `find ... -name '*.md'` plus a
directory listing. It can yield many per-file read effects from one Tool call.
The ActPlane maximum begins with `rg --files`. Thus 14 or 767 file reads do not
directly measure 14 or 767 Agent decisions, nor proportional restart cost.

**Needed:** report Tool calls, distinct files, returned bytes, and elapsed Agent
action time separately. A broad inventory command should remain one interaction
episode even if it discovers hundreds of paths.

### “Validation repetition” ignores relevant generated/system state

The ActPlane witness starts with a build failure caused by a corrupt
incremental artifact and later removes generated BPF outputs before a
successful rebuild. Both are meaningful state transitions without a confirmed
repository source mutation.

**Needed:** distinguish “no source mutation” from “no relevant state change,”
and group validation calls by command signature and result transition.

### “Unrevisited created artifact” contains a concrete false workspace attribution

The sole academic example,
`fake/docs/tmp/cycle-0001-x/03-review-gate/idea-unchanged-skip.md`, was created
inside a Claude scratchpad under `/tmp/.../scratchpad/fake` for a smoke test. It
was not created in the target Git workspace. Reporting it as a repository
artifact makes the one-touch-clutter signal misleading.

In ActPlane, many examples are under `target/`, which are generated test
fixtures or build artifacts. Even when physically inside the repository
directory, they should be classified separately from persistent authored
artifacts.

**Needed:** enforce target-worktree containment using the effective command
working directory, and add a `generated/scratch` artifact class.

### Mutation counts are not time, effort, semantic size, or progress

The report can support “more normalized mutation actions touched docs than
code.” It cannot support “the Agent spent more time on the paper,” “the paper
received more effort,” or “more progress occurred.” One large write and many
small edits are incomparable without size, duration, and episode grouping.

### Module migration is descriptive but often trivial

Modules are first path components, so root files such as `README.md`,
`Makefile`, and `CLAUDE.md` appear as modules beside directories. JSD 1.0 can
arise whenever two narrow sessions touch disjoint singleton regions. It is not
automatically an abrupt strategic pivot.

**Needed:** duration/action mass of each phase, parent-directory rollups, and
the goal/session prompt before treating a shift as consequential.

### Evidence lists are repetitive and sometimes show only one endpoint

Validation-lag and cross-session-carryover repeat the same recent mutations.
Revival shows several events but does not explicitly label the previous and
return endpoints or the exact intervening-session denominator. The Agent still
has to reconstruct the relation.

**Needed:** one compact witness tuple per relation:
`before → gap/condition → after`, plus a retrieval command or stable event IDs.

### “Rework,” “revival,” and skill “footprint” are interpretations in their headings

The underlying exact relations are repeated mutation, absence followed by
access, and same-session association. The words can invite causal or evaluative
readings that the stated boundaries correctly disclaim.

**Needed:** make neutral relation names primary and place diagnostic hypotheses
in a separate field.

## Exact facts versus interpretations

### Source-exact facts

These can be checked directly in native records:

- a Tool call ID, session ID, timestamp, source file, command, and native result;
- a successful `Edit`, a reported failed build, or a successful rebuild;
- the concrete path named by a structured file operation;
- session ordering by recorded Agent-action timestamp.

### Detector-exact facts

These are exactly reproducible **under the report's definitions**, but are not
unqualified ground truth:

- file-action, mutation, and recognized-validation counts;
- artifact kind and first-component module;
- “reads before first mutation”;
- pending/superseded/validated relations;
- cross-session recurrence and revival gaps;
- same-session skill footprints.

Each depends on path extraction, command classification, repository admission,
session lineage, and validation recognition. They should retain labels such as
“recognized,” “observed,” and “under the admitted records.”

### Interpretations requiring more evidence

The following are not exact facts:

- the Agent forgot context or had to rediscover work;
- a repeated edit is rework, churn, or a defect;
- a validation sequence is wasteful or a test treadmill;
- documentation is useless because it was not reread;
- a skill caused document load or validation absence;
- a module transition is goal drift;
- repeated activity represents progress, correctness, importance, or elapsed
  effort.

## Six source-anchor spot checks

| # | Report signal | Source anchor | Verification |
|---:|---|---|---|
| 1 | Academic session re-grounding | `toolu_01VzwxQhaU5JCbi3WcixArE9` | **Verified with qualification.** One successful Bash call enumerated Markdown files and skill directories. It supports an initial inventory action, but also shows why per-file read counts can greatly exceed Agent decisions. |
| 2 | Academic cross-session hotspot | `toolu_01XJ63dzwvQVQNJU6x91RJh9` | **Verified.** A successful `Edit` changed `hierarchical-research-state-machine.md`, adding a backward-compatibility rule for historical step layouts. It verifies the mutation, not problematic rework. |
| 3 | Academic unrevisited artifact | `toolu_017rZueG82wNmxqQEfUszauJ` | **Contradicted as a target-workspace artifact.** The file was intentionally created under a `/tmp/.../scratchpad/fake` smoke-test repository. The smoke test executed `check_progress.py` and got the expected warning path. |
| 4 | ActPlane repeated-validation start | `call_jskJPF6ng72QmCxs3OdSMsNo` | **Verified with a different likely cause.** `cargo build` failed because of corrupt incremental compilation metadata and a zero-length `.rlib`, evidence of generated build-state corruption rather than a demonstrated source defect. |
| 5 | ActPlane repeated-validation end | `call_UyL750dgq3LqlpQXks0fJzwW` | **Verified with qualification.** The command removed generated BPF outputs and rebuilt successfully. No source mutation occurred, but relevant generated state changed. |
| 6 | ActPlane artifact revival endpoint | `call_Uz3R1n6T0hrw2UnPfArXjDWK` | **Endpoint verified.** One successful patch added `docs/feedback-design.md`, modified `docs/tmp/harness-survey.md` and `docs/tmp/eval-plan.md`, and deleted two temporary docs. This confirms the later `eval-plan.md` mutation, but this single check does not independently verify the reported 88-session gap. |

## Is the brief better than a linear log for Agent consumption?

**Yes, as a first-pass index.** It is better for:

- finding cross-session hotspots;
- noticing validation/mutation rhythms;
- identifying candidate harness or skill audits;
- locating exact native evidence without scanning 66,238 Tool events;
- preserving explicit boundaries between observation and interpretation.

**Not yet as a standalone diagnosis.** A linear log still supplies context that
the brief discards:

- why a command was run;
- what changed between two validations outside source files;
- whether a synthetic/generated artifact belongs to the deliverable;
- semantic size and purpose of edits;
- expected versus unexpected non-zero exits;
- the precise fail → intervention → recovery chain.

The best Agent-facing interface is therefore a layered artifact:

1. a short ranked candidate list;
2. neutral exact relations and coverage;
3. grouped source episodes rather than repeated individual actions;
4. a current actionable queue;
5. stable links to the minimal native evidence needed to confirm or reject each
   interpretation.

My qualitative assessment is that the current brief reduces orientation cost
dramatically, but a controlled task-based comparison would still be required
to claim that Agents diagnose more accurately than when using a bounded linear
log.

## Post-fix review of the three original blockers

**Verdict: PASS — all three blockers are closed in the regenerated reports.**

The release binary timestamp is `2026-07-23 23:36:44 -0700`; the ActPlane and
academic reports were generated afterward at `23:36:58` and `23:37:02`.
Therefore this disposition applies to reports produced by the latest release
binary, not stale output.

### 1. Inline `/tmp` fake repositories no longer become target-workspace artifacts — PASS

The previously misattributed
`fake/docs/tmp/cycle-0001-x/03-review-gate/idea-unchanged-skip.md` is absent
from both regenerated reports and from every file currently under
`agentvis/output/`. The academic report no longer emits an
`unrevisited-created-artifacts` candidate for that smoke-test file.

The associated aggregate also moves in the expected direction:
academic documentation mutations change from 244 to 243, touched documents
from 22 to 21, and documents never reread from 7 to 6. This is consistent with
excluding the one `/tmp/.../scratchpad/fake` artifact rather than merely hiding
its witness.

This closes the original false target-workspace attribution.

### 2. Re-grounding is Tool-call-primary and separates file effects/artifacts — PASS

Both reports now state:

> The primary count is read Tool calls; file effects and distinct artifacts are
> separate.

The academic maximum reports:

- 14 read Tool calls;
- 14 file-read effects;
- 14 distinct artifacts;
- 11 prior-artifact read effects;
- 137,505 ms Agent-action time to first mutation.

ActPlane reports the independently visible dimensions:

- 754 read Tool calls;
- 767 file-read effects;
- 53 distinct artifacts;
- 583 prior-artifact read effects;
- 69,521,428 ms Agent-action time to first mutation.

The evidence endpoint for the academic case is now a concrete structured
`Read` of `README.md`, rather than the broad `find` inventory command that
triggered the original concern. For ActPlane, the large value remains a
legitimate candidate for investigation, but the report no longer equates
hundreds of file effects with hundreds of distinct artifacts or leaves the
reader unable to distinguish Tool interactions from fan-out.

This closes the measurement/communication blocker. The high ActPlane count may
still deserve process investigation, but that is a result, not the original
aggregation defect.

### 3. Validation runs expose heterogeneity and no longer imply a treadmill — PASS

The section heading is now neutral:

> Validation calls occur without an intervening confirmed repository mutation

For the longest ActPlane run, the report exposes:

- 634 validation calls;
- 150 distinct command signatures;
- 179 outcome transitions;
- a longest identical-command, same-outcome streak of only 4.

The explanation explicitly says these fields distinguish environment diagnosis
or a deliberate matrix from an identical-check treadmill. Its boundary also
states that no confirmed source mutation does not imply no state change because
generated files, caches, services, and external dependencies may change.

The four displayed `cargo test` successes provide a direct witness for the
reported maximum identical same-outcome streak, while the 150 signatures and
179 transitions prevent a reader from treating the full 634-call span as that
same pattern.

This closes the original overinterpretation blocker. The report still
identifies a validation-heavy episode worth inspecting, but it now provides
the exact evidence needed to reject the simplistic “634 repeated identical
tests” reading.

## Addendum: external reuse, internal revival, and prompt previews

**Overall verdict: BLOCK on the interpretation of
`external-workspace-reuse`; PASS on internal-evolution revival and the sampled
prompt previews.**

I checked all five external anchors displayed by the report, spanning two
Codex sessions, plus both displayed internal-revival anchors and one mutation
anchor with a prompt preview.

### External exact-path admission — mechanically PASS

For all five displayed external anchors:

- the source session metadata has root `cwd=/home/yunwei37/workspace`, which is
  outside the target repository
  `/home/yunwei37/workspace/my-paper-work/academic-writing-skills`;
- the native `exec_command` specifies the target repository as `workdir`;
- the `sed`/`nl` operand resolves to the exact reported
  `skills/auto-research-orchestrator/SKILL.md` path;
- neither source session contains `agentvis`, `diagnose`, or
  `trajectory-brief`, so these samples are not the diagnostic run rereading its
  own inputs.

The five verified call IDs are:

- `call_fOgJkC0Gk4q8vi9y1H6E2uvB`
- `call_rnBGSH5xXMuVQ9fWhYr6WDG6`
- `call_Rhq4mqBz6KRgeMqdf4LJ5Zu5`
- `call_LSKRKR5K4ZWr0VJ8kOUsSBMC`
- `call_kgGwDnHrH8RY6TyrHk7KwQAk`

Thus the narrow fact “a root-external native session performed an exact-path
read of this target artifact” is supported.

### “External workspace reuse” and “read-only consumers working elsewhere” — BLOCK

The stronger interpretation is not supported by the sampled evidence.

First, `/home/yunwei37/workspace` is a broad parent directory. A session rooted
there can explicitly work on the target repository by setting the Tool
`workdir`; root metadata alone does not establish that the Agent was pursuing a
different workspace task.

Second, session
`codex:rollout-2026-06-13T12-36-08-019ec27c-04e6-7793-9491-304c321390ac`
was explicitly instructed to review and improve files in the target repository.
After the two displayed reads, it successfully applied patches to:

- `skills/auto-research-orchestrator/SKILL.md`;
- `skills/auto-research-orchestrator/references/research-state-machine.md`;
- `docs/auto-research-operating-model.md`.

Nevertheless, its reads appear as external-reuse witnesses while the report
states `external_mutating_sessions: 0`. This materially conflicts with the
native evidence and with the explanation that these are read-only consumers
“working elsewhere.”

The safe interpretation of
`most_externally_reread_artifact =
skills/auto-research-orchestrator/SKILL.md` is only:

> Among admitted exact-path read effects from sessions whose root `cwd` is
> outside the repository, this artifact has the largest read-effect count.

It does **not** establish:

- 1,275 distinct consumers or sessions;
- semantic use or influence;
- reuse by unrelated projects;
- a read-only consumer population;
- work performed primarily outside the target repository.

The three near-consecutive reads in the first sampled session also show that
`external_reads_of_top_artifact: 1275` is an event count, not a unique-consumer
count. The report's existing “access, not influence” boundary is good but does
not repair the evolution-versus-external misclassification.

### Internal evolution revival — PASS with the stated boundary

Both displayed internal-revival endpoints are native structured `Read` calls
of the exact target file:

- `toolu_01LqcRamM8vG4Bc35eDZpknS`
- `toolu_01QHLnVv2ZeP7RQ23S71kLtM`

Their native session `cwd` is the target repository, and their prompts ask to
review or improve that repository. The report therefore correctly keeps these
events in internal workspace/evolution revival rather than treating the
read-only external population as intervening evolution. The stated boundary
also correctly limits “absence” to no observed repository file action and does
not infer forgetting.

This spot check verifies the two endpoints and their internal admission; it
does not independently recount all eight intervening evolution sessions.

### Prompt previews — sampled content PASS, coverage boundary noted

Three sampled previews match the nearest substantive native user prompt:

- `toolu_01LqcRamM8vG4Bc35eDZpknS` correctly previews the long request beginning
  “You are reviewing a shared Agent Skills repository...”;
- `toolu_01QHLnVv2ZeP7RQ23S71kLtM` correctly previews
  “你看看我们的 auto research skill 有没有问题?”;
- `toolu_01XJ63dzwvQVQNJU6x91RJh9` correctly previews
  “检查一下, 有米有删除不应该删除的, 可能会触发坑的?”.

The preview is useful context but remains a truncated prompt, not an intent
label or causal explanation. The external-reuse witness rows currently do not
show prompt previews even though their source sessions contain task prompts;
therefore the prompt feature is correct where sampled, but not uniformly
available for auditing the external-reuse interpretation.

## Addendum: does action strategy answer takeover questions faster?

**Verdict: yes for orientation, not yet for an unverified diagnosis.** I read
the latest lower-case `actplane-trajectory-brief.md` and checked exactly eight
native anchors. The action-strategy summary answered the three takeover
questions in minutes; reconstructing the same cross-session picture from
67,764 Tool events would require substantially more log navigation. One
classification error, however, directly affects the strategy sequence and
must remain visible in any claim based on its counts.

### Four actionable process patterns

1. **Validation strategy differs sharply across mutating sessions.** Of 52
   mutating sessions, 16 have a recognized successful validation before the
   first mutation, 11 validate only after the first mutation, and 25 have no
   recognized validation. Twenty-six have a successful validation after their
   first mutation, so testing before and after is not mutually exclusive. This
   is immediately more useful than a raw log for answering “先测还是先改”.
   The next action is to inspect the 25-session no-recognized-validation set by
   artifact kind and validator family, prioritizing source-code sessions; it
   is not to declare all 25 unvalidated.

2. **A validation-heavy regime deserves command-family analysis, but is not a
   demonstrated treadmill.** The longest mutation-free validation run has 634
   calls, but also 150 command signatures, 179 outcome transitions, and a
   maximum identical-command/same-outcome streak of only four. Two checked
   anchors are consecutive successful `cargo test` calls, confirming that
   local repetition exists. The aggregate simultaneously rules out the much
   stronger reading that all 634 calls were the same useless check. The
   actionable next step is to rank repeated command families by unchanged
   outcome and intervening generated/environment state, then inspect only the
   top unchanged families.

3. **Open work crosses session boundaries and needs a current handoff queue.**
   The report shows 40 mutation bursts still open at a session or snapshot end
   and 163 pending mutation generations carried across sessions, alongside 439
   later-session worktree-validation associations. This makes unresolved
   source artifacts a concrete takeover target. The queue must exclude or
   separately classify `target/`, build outputs, temporary PR bodies, and
   snapshot-end work still in progress; the aggregate alone is not a defect
   count.

4. **`docs/papers/sections/04-design.tex` is the clearest durable audit
   hotspot, not a proven rework hotspot.** It receives 558 mutations across 20
   sessions. The checked native edit merely synchronizes a Chinese caption
   with the English text, demonstrating legitimate refinement. The useful
   action is therefore a claim-to-implementation consistency audit across this
   file and the corresponding `bpf`, `collector`, and `crates` mechanisms,
   grouped into semantic episodes. The count cannot establish churn, waste, or
   defect density.

### Speed versus raw logs

- **“先测还是先改” — substantially faster.** The session partition gives the
  answer directly, subject to recognized-validator coverage and action
  classification.
- **“是否验证空转” — faster for rejection and triage, not for final judgment.**
  The diversity and outcome fields quickly reject a single 634-call identical
  treadmill and identify the small identical streaks worth opening. Raw
  context is still required to decide whether a rerun was redundant.
- **“主要返工点” — faster only after renaming the question.** The brief reliably
  finds repeated-mutation hotspots; it does not know which recurrence is
  rework. Source intent and semantic diffs are required for that label.

### Remaining aggregation artifacts and unsupported conclusions

- `call_wmZcZPQQWzpaRZVeKOimOzEj` is reported as `read:ok`, but the native
  command successfully executes `git rm` followed by `rm -f` and `rm -rf`.
  Compound-shell classification can therefore alter the collapsed transition
  counts, first-mutation boundary, burst sizes, and validation-cycle lengths.
- A Tool effect count is not elapsed time, semantic edit size, independent
  reasoning effort, or progress. In particular, the maximum 653 mutations in
  one closed validation cycle may be a bulk/document transformation.
- A later recognized worktree validation is only a temporal association. It
  does not prove that each pending artifact was exercised or correct, and
  repository-specific validators may be unrecognized.
- Repeated mutation can be translation synchronization or deliberate paper
  refinement; no-revisit can mean a final deliverable; an open burst can be a
  snapshot cutoff; and documentation dominance does not establish where Agent
  time or importance concentrated.
- The 155 admitted sessions are not the full 604 direct candidates. Results
  describe the admitted native records, and long sessions may also combine
  several user goals. Neither coverage nor session-level aggregation supports
  population-level claims about Agent behavior.

The action-strategy view is therefore already a useful Agent-facing index: it
compresses the search space and names the next source episodes to inspect.
Before using it as an empirical strategy measure, compound command
classification and artifact-aware validator coverage need to be treated as
measurement validity conditions.
