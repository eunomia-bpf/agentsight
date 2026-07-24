# Tool-first natural-case checkpoint

Date: 2026-07-23

## Decision

The exact-fact benchmark is a conformance suite, not the product story. The
current gate is whether a local tool can turn live Claude, Codex, and Gemini
records into a compact, source-linked process brief that another Agent can use
to investigate a long-running workspace.

The intended division of labour is:

1. deterministic code discovers native sessions and computes exact
   source-linked relations;
2. the brief ranks candidate process patterns and exposes evidence endpoints;
3. an Agent interprets the evidence, follows a small number of native anchors,
   and states uncertainty.

The Agent is a report consumer, not an oracle and not a gold label.

## What the tool now does

`agentsight diagnose [PATH]` and the standalone
`agentvis diagnose [PATH]` produce one Markdown or JSON process brief. The
current relations are:

- non-overlapping native-root pre-mutation inspection;
- module-focus transitions over evolution sessions;
- successful worktree-validation association after mutation;
- mutations carried across a native-session boundary, with exact later
  validation-association, supersession, or open-at-cutoff endpoint;
- validation sequences without an intervening confirmed source mutation,
  including command diversity, outcome transitions, and identical streaks;
- repeated mutation of one artifact across sessions;
- artifact re-access after gaps in evolution sessions;
- created artifacts not observed again;
- later reads of written documentation;
- root-external exact-path access under `--global`;
- read/search spans ranked by read Tool calls rather than arbitrary event
  thresholds;
- collapsed inspect–mutate–validate transitions and mutation bursts closed by
  successful recognized validation;
- explicit Skill-associated session footprints.

Every evidence row retains the native transcript, Tool-call ID, event ID,
command, path, timestamp, and associated user-prompt preview when available.
The report labels signals as candidates and states their interpretation
boundary.

### Measurement corrections made during the tool-first audit

- A leading `cd /tmp/...` now changes path resolution before repository
  scoping. A dynamic `cd "$var"` rejects unresolved relative paths instead of
  silently falling back to the repository root.
- Directory scope is assigned from action-time path evidence, so a later
  file-to-directory conversion does not rewrite earlier actions. An
  unobserved recursive-delete target can remain type-unknown.
- Generated/scratch artifacts are classified separately.
- Repository-specific check/verify/lint/smoke scripts are recognized as
  validation commands.
- A successful worktree check is reported as a temporal association, not proof
  that every pending file was covered.
- Broad inventory commands remain one read Tool call even when they yield many
  file effects.
- Root-external read-only sessions no longer alter evolution-session
  pre-mutation inspection or module transitions.
- `--global` uses ripgrep only to select native session files, then sends each
  whole file through `agent-session`; Tool results, prompts, status and native
  root identity are no longer lost.
- Continued/archive transcript files are not treated as independent evidence.
  Repeated source-native Tool-call/event identities are deduplicated before
  pattern computation. Coverage reports both raw parsed Tool/LLM records and
  unique retained Tool calls.
- Every output records a source-snapshot fingerprint so live runs are not
  silently compared as if they were the same input.
- The diagnostic invocation itself is excluded so the observer does not add a
  self-reference.

These corrections were motivated by source inspection, then covered by unit
tests. They are not hidden post-hoc filters.

## Five live-workspace observations

The native history is live, so these are 2026-07-23 snapshots rather than a
frozen population. Counts are exact under the current parser and admission
rules; they are not estimates of effort, quality, or causal effect.

| Workspace | Snapshot | Workspace / root-external sessions | Durable mutation hotspot | Handoff (pending / later validation / later supersession) | Top root-external read footprint |
|---|---|---:|---|---:|---|
| AgentSight | `8255c3575153455b` | 301 / 16 | `docs/agentpprof-paper/main.tex`: 879 mutations in 6 sessions | 359 / 138 / 242 | same paper: 65 read actions / 2 root sessions |
| ActPlane | `5ac7945ec04d01d0` | 139 / 16 | `docs/papers/sections/04-design.tex`: 558 mutations in 20 sessions | 163 / 443 / 107 | `bpf/process.bpf.c`: 19 / 2 |
| eunomia.dev | `ff21eb6af145c2e1` | 51 / 26 | `docs/blog/posts/actplane.md`: 167 mutations in 5 sessions | 89 / 87 / 20 | `mkdocs.yaml`: 29 / 6 |
| bpf-developer-tutorial | `d9ca824225f71720` | 42 / 6 | `src/54-exec-image-inspector/README.zh.md`: 49 mutations in 3 sessions | 176 / 151 / 47 | one tutorial chapter: 15 / 1 |
| academic-writing-skills | `1f4ccf558b73b2c5` | 17 / 109 | `auto-research-orchestrator/SKILL.md`: 139 mutations in 10 sessions | 76 / 84 / 65 | `research-state-machine.md`: 845 / 14 |

### Finding 1: root-external access is concentrated, but is not automatically consumption

`academic-writing-skills` is the clearest case. Its own lineage contains 17
native workspace sessions. `--global` finds 109 additional native root sessions
whose Tool effects contain exact paths into the repository; 24 of them have
observed mutation effects, so calling the whole set "read-only consumers" is
wrong. A delegated subagent can be rooted elsewhere while intentionally editing
this repository.

The strongest control-artifact footprint is still non-trivial:
`research-state-machine.md` has 845 later root-external read actions, spread
across 14 native root sessions and 29 source files. The median is 27 reads per
root session and the maximum is 257. Those 845 actions are **not** 845
independent consumers and do not prove that the content affected behaviour.
They do locate a concentrated repeated-access regime that a harness auditor can
inspect.

The smaller external-reference populations in the other four projects show
that exact cross-root access is not unique to a Skill repository. The cases do
not estimate a population rate or establish cross-project reuse.

### Finding 2: action order distinguishes work strategies that totals collapse

The brief now collapses adjacent equal states and counts transitions between
inspection, confirmed mutation and recognized validation. It also groups
confirmed mutation events until the next successful recognized validation.

| Workspace | Mutating sessions | Validation before first mutation / only after / none | Closed-cycle median / maximum mutation events |
|---|---:|---:|---:|
| AgentSight | 52 | 23 / 12 / 17 | 2 / 218 |
| ActPlane | 52 | 16 / 11 / 25 | 2 / 653 |
| eunomia.dev | 24 | 1 / 9 / 14 | 2 / 144 |
| bpf-developer-tutorial | 34 | 8 / 2 / 24 | 3 / 53 |
| academic-writing-skills | 24 | 1 / 5 / 18 | 5 / 142 |

This directly answers "test first or write first?" and identifies unusually
large change-before-validation episodes for source inspection. It does not say
that a session with no recognized validator did no checking: documentation,
research and external validation can fall outside the validator grammar.

### Finding 3: persistent hotspots are process entry points, not defect labels

All five workspaces have artifacts mutated in multiple native sessions. The
hotspot type differs: papers/design specifications in AgentSight and ActPlane,
a blog article in eunomia.dev, a tutorial chapter in
bpf-developer-tutorial, and an orchestration state machine in
academic-writing-skills.

The raw-log Agent found that the academic hotspot reflects a four-stage
evolution with repeated user correction and specification compression. The
brief locates the exact artifact and sessions; prompt previews and source
anchors make the semantic follow-up bounded. Mutation count alone cannot tell
healthy refinement from rework.

### Finding 4: "many tests" is not a test treadmill

ActPlane's longest sequence has 634 recognized validation calls without an
intervening confirmed repository source mutation. It also has 150 distinct
command signatures, 179 outcome transitions, and a longest identical-command,
same-outcome streak of only four. Source inspection found corrupted generated
state, cleanup, and rebuild activity.

The useful signal is therefore a ranked validation episode with diversity and
state-transition evidence. Labelling all 634 calls as waste would be wrong.

### Finding 5: native-session boundaries leave actionable workspace state

Every case contains mutation generations that cross the end of their producing
session. The report now exposes an artifact-level handoff queue with the
mutation endpoint and the first observed later worktree validation,
supersession, or open cutoff. This is more actionable than an aggregate count:
a takeover Agent can inspect open state before starting unrelated work.

A later worktree check is only temporally associated with all pending
mutations in that worktree. The tool does not claim per-file test coverage.

### Finding 6: documentation reread must be split by origin and deduplicated

A single "documentation reread" number hides whether the authoring lineage
revisited its own specification, a delegated external-root Agent edited it, or
another root repeatedly opened it. The useful report therefore separates
workspace and root-external access, then reports actions, native root sessions
and source files rather than presenting Tool-call count as "users".

This supports the user's question about Skills and harnesses that create
documentation nobody later consults. A zero or low observed access footprint is
an inspection candidate, not proof that the document is useless.

## Agent-reader comparison

Two independent Agent reads were run without treating either output as truth.

### Brief-first reader

The reader first saw only the compact academic and ActPlane briefs, then
spot-checked six report-provided native anchors. It judged the brief
substantially more useful than a linear log as a triage index and identified:

- the ActPlane paper/design hotspot;
- a large but heterogeneous validation regime;
- the need for an artifact-level cross-session handoff queue;
- the academic orchestration-specification hotspot;
- a repository-specific validation blind spot;
- Skill footprints that require non-causal language.

It also found three implementation defects or ambiguities: a `/tmp` scratch
path falsely projected into the repository, broad inventory effects presented
as many reads, and a generated-state repair episode that looked like a
validation treadmill. The implementation was corrected and the same reader
confirmed the three blockers were closed.

A later ActPlane takeover pass checked eight more anchors. It found the
action-strategy summary materially faster for deciding where testing preceded
or followed mutation, while rejecting the claim that 634 diverse validations
were one identical treadmill. It also caught a compound-shell defect:
`git rm` was displayed as read and its own delete operands were missing.
`agent-session` now recognizes `git rm`/`git mv` workspace mutation effects and
has a regression test.

Full review:
`docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/agent-reader-review.md`.

### Raw-log reader

The raw baseline was forbidden from reading the brief or implementation. It
searched native histories and deeply read representative records. It recovered
semantic phases and user corrections that counts alone cannot establish:

- establishment, expansion, orchestration refactoring, and later compression;
- suggestions being upgraded into mandatory process;
- repeated user concern about lost constraints and excess artifact ceremony;
- text/syntax checks without a held-out behavioural loop for the Skills.

It also required manual candidate discovery over very large native stores and
deep reading of selected sessions. Its output is richer semantically but is
not an exhaustive denominator for every cross-session relation.

The same reader then consumed the revised brief and followed ten anchors. It
ranked the handoff queue, action sequencing and root-external access
concentration as the most actionable views. It rejected two tempting
overclaims: a long-lived parent root spanning transcript files and days is not
a "restart re-grounding cost", and a Skill footprint observed in one
same-session cleanup cannot establish a harness effect. The product now calls
the former pre-mutation inspection and explicitly states that native roots can
span files, compactions, goals, subagents and days.

Full review:
`docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/raw-agent-baseline-review.md`.

### Interpretation

The comparison does not support "brief beats raw logs" or the reverse.

- The brief contributes exhaustive local computation, cross-session joins,
  explicit denominators, and source retrieval anchors.
- Raw evidence contributes intent, failure reasons, user correction, and
  semantic phase interpretation.
- Prompt previews narrow this gap but do not turn the deterministic tool into
  a semantic judge.
- Skill/harness overhead is currently a bounded source-inspection question:
  repeated reads, document production and validation skew can be located, but
  only a real harness change or executable outcome supports causal attribution.

The useful product is therefore an evidence index an Agent can query and
verify, not an autonomous verdict generator.

## Closest-work boundary

AgentTrails (arXiv:2607.18816, 2026-07-21) is the closest newly found system.
It reconstructs action–artifact provenance from raw traces, distinguishes
exact from semantic dependency evidence, aligns multiple provenance graphs,
extracts patterns and reusable skills, and provides an LLM copilot. Generic
provenance graphs, artifact reuse, multi-trace pattern extraction, and an Agent
reader are occupied.

The remaining exploratory distinction is narrower:

> Reconstruct the continuing state of one persistent workspace across
> independent native sessions, expose its inspect–mutate–validate strategy,
> and separately follow exact-path access from Agents rooted elsewhere.

AgentTrails' published exact dependency rule connects earlier entities to later
actions within one trace, then aligns graphs across traces. Its current
four-page paper does not report this persistent-workspace action-strategy and
handoff measurement. This is a search-supported gap, not yet a novelty claim.

## Research direction after the tool-first checkpoint

The next paper question should be smaller than generic diagnosis:

> What process-continuity and action-strategy relations become observable when
> native Agent histories are organized around persistent workspaces rather
> than isolated task traces?

Candidate empirical contributions are:

1. a source-valid descriptive study of artifact evolution, action strategy,
   cross-session handoff and cross-root exact-path access;
2. a compact local process brief that makes these relations retrievable by an
   Agent without estimating counts from logs;
3. case evidence showing where the relations expose useful intervention
   points, with source anchors and explicit non-causal boundaries.

Before any stronger claim, the tool should be run on independent workspaces
not authored by the same user, cross-root admission should be audited for
aliases, delegated subagents and copied workspaces, and prospective cases
should test whether a takeover Agent actually uses the handoff queue.
