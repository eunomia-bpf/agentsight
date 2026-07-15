# Idea And Hypothesis History

## Initial Narrative

### Problem and stakes

Long-horizon coding agents can modify a repository across many sessions, days,
and models. The resulting commits show what snapshots survived, while native
agent logs show a large event stream that no reviewer can read end to end. The
development rationale can therefore disappear as soon as a session ends:
humans inherit code without having observed the exploration, false starts,
verification gaps, or cross-file information flow that produced it.

### Challenged belief

Software-evolution visualization has usually treated commits as the natural
unit of observation and people as the persistent authors of a system. The
project challenges the belief that simply applying existing commit-centric
views to agent-authored repositories is sufficient.

### Central thesis

Agent events and version-control history are complementary evidence. Joining
timestamped read/edit/tool/model events with commits, file births and deaths,
blame, and the current tree exposes process structure that commits cannot
contain while retaining the durable outcome that agent logs cannot prove. A
stable set of coordinated views can compress this joined history into a form
that supports both exploratory discovery and concrete review decisions.

### Proposed system

Extend `agent-session` with a longitudinal exporter that joins native Claude,
Codex, and Gemini sessions to Git history and the current repository state. A
static, locally served visualization gallery reuses established browser
libraries and interchange formats to provide pixel/line views, evolution
matrices, stable repository maps, animated growth replays, survival strata,
forensic hotspots and coupling, ownership/storyline views, and coordinated
long-horizon navigation. Every view states the review decision it supports.

### Intended contributions

1. An event-resolved longitudinal representation that preserves both agent
   process evidence and Git-grounded software outcomes.
2. A coordinated visualization design that adapts seven established software
   evolution traditions to multi-session coding agents while preserving stable
   layouts and time navigation.
3. An empirical evaluation of information loss at commit granularity,
   behavior-pattern observability, diagnostic usefulness, and scalability on
   real multi-day development histories.

### Scope

The first artifact targets local coding-agent transcripts and Git repositories.
It does not claim that temporal order alone proves semantic causality, that a
session event proves a change was committed, or that inferred agent authorship
is equivalent to signed provenance. These distinctions are explicit fields in
the joined representation.

### Provisional research questions

- **RQ1 — Recoverability:** What development-process evidence is present in
  agent events but absent from commits, and how reliably can events be joined
  to Git-grounded outcomes?
- **RQ2 — Behavioral structure:** Which recurring exploration, churn,
  verification, coupling, and survival patterns become observable at event
  granularity, and are they stable across sessions and agents?
- **RQ3 — Review utility:** Do coordinated event-plus-history views improve
  the accuracy and time required to answer realistic process-review questions
  compared with logs and commit-centric views?
- **RQ4 — Long-horizon scalability:** Can the representation and interactions
  remain responsive and interpretable across days to months and large event
  volumes?

### Evaluation promise

The paper will report real multi-day repositories, an explicit join-quality
audit, commit-only and log/table baselines, controlled diagnostic tasks, and
runtime/interaction measurements. All missing values, plots, and
result-dependent claims remain placeholders until complete final runs.

## Belief And Principle Evolution

| Date | Prior belief/model | External evidence | Updated principle | Paper impact |
|---|---|---|---|---|
| 2026-07-15 | Commits are the default evolution unit. | Pending literature grounding and real-data audit. | Test events and commits as complementary evidence. | Defines RQ1 and the joined representation. |
| 2026-07-15 | Fine-grained replay might itself be a novel contribution. | RECAP already joins Copilot conversations with observed shadow-repository edits over a two-week project. | Replay is a baseline capability; the differentiator must be cross-vendor native events, candidate associations to actual Git outcomes, and separately labeled endpoint survival. | Narrows the thesis and makes RECAP the highest-risk closest work. |
| 2026-07-15 | Timestamped reads and edits might reveal causal coupling or agent authorship. | Native schemas and actual Git history do not provide signed identity or causal intervention evidence. | Treat read-before-edit as ordered evidence and event-to-Git links as zero/one/many candidates with confidence. | Removes causal/authorship claims and makes ambiguity visible. |
| 2026-07-15 | Path survival and line survival could share one join. | Rename/refactoring work and CLSA show that event-to-Git matching and Git-to-current lineage fail for different reasons. | Evaluate event-to-Git association separately from Git hunk-to-current-line lineage; unsupported events remain path-level. | RQ1 becomes a gate for downstream claims. |
| 2026-07-15 | A broad gallery can establish utility by inspection. | Software-visualization evaluation work and Githru use real systems and controlled tasks; a gallery alone does not show decision value. | Freeze four task-facing core combinations and treat other views as exploratory/communicative support. | RQ3 separates information content from coordinated interaction. |

## Hypothesis Frontier

| ID | Parent | Prediction | Falsifier | Evidence for/against | Status | Decisive next test | Reopen condition |
|---|---|---|---|---|---|---|---|
| H1 | root | Event-plus-Git views expose review-relevant process structures that commit-only views omit. | Process questions are answered equally well from commit-only views, or event joins are too unreliable. | Pending. | leading | Build joined dataset and measure recoverability on real history. | Revisit after RQ1 final run. |
| H2 | root | Most useful longitudinal insight comes from durable Git outcomes; fine-grained agent events add little beyond animation. | Event-only structures materially improve diagnosis and remain stable across histories. | Pending. | competing | Compare matched tasks across commit, event table, and coordinated views. | Revisit after RQ3 protocol. |
| H3 | H1 | Stable layout plus semantic zoom makes weeks of events usable without discarding local detail. | Interaction latency or visual crowding prevents task completion at target scale. | Pending. | stronger generalization | Benchmark aggregated frames and task navigation at increasing history sizes. | Revisit after RQ4 final run. |

## Claim Evolution

| Date | Ambitious target claim | Evidence status | Unresolved uncertainty | Next evidence program |
|---|---|---|---|---|
| 2026-07-15 | Joined event and Git history forms a practical observation layer for long-horizon agentic software evolution. | Hypothesis only. | Join fidelity, generality, human utility, and scale. | Literature grounding, implementation, and RQ1 preflight. |
| 2026-07-15 | Uncertainty-preserving cross-vendor event-to-actual-Git evidence plus endpoint survival supports review decisions unavailable from either source alone. | Literature-differentiated hypothesis; no artifact result yet. | Candidate-link accuracy, line-lineage accuracy, stable pattern replication, task effect, and tested scale. | Controlled and naturalistic RQ1 ground truth before any event-to-outcome claim. |

## Rejected Or Dormant Paths

| Path | Why rejected/dormant | Raw evidence | Revisit trigger |
|---|---|---|---|
| 3D-only code city | Depth and camera motion are not yet justified by a review task. | User discussion and pending literature verification. | A task study shows unique value over stable 2D maps. |
| Replay-first novelty | RECAP already supplies high-resolution conversation/edit replay. | Closest-work audit and full-text review. | New evidence shows a materially different replay task not covered by the joined representation. |
| First agent-code survival study | Recent survival studies already analyze agent-associated code at scale. | Will It Survive? and CLSA. | The project produces a distinct validated survival construct rather than an endpoint projection. |
| Timestamp-as-causality or authorship | Temporal proximity cannot establish why a change occurred or who authored the durable Git outcome. | Native schema and Git evidence audit. | Signed provenance or an intervention-based causal protocol becomes available. |
| One association state | Pathless, ambiguous, event-unmatched, Git-unmatched, path-level, and line-level records have different semantics. | Writing consistency and meaning-preservation audits. | RQ1 shows a safe deterministic collapse within a validated stratum. |

## Narrative Evolution

- **2026-07-15 — closest-work narrowing.** The Initial Narrative's joined-
  evidence thesis remains, but replay and agent-code survival are no longer
  novelty targets. The central empirical object is disagreement among recorded
  process events, candidate actual-Git outcomes, and separately derived current-
  tree endpoint survival.
- **2026-07-15 — evidence boundary.** The representation now distinguishes
  association eligibility, zero/one/many candidate Git changes, Git-side
  unmatched changes, optional event-to-hunk association, Git line lineage, and
  endpoint survival. Recorded verification actions do not establish correctness,
  and ordered read-before-edit does not establish causality.
- **2026-07-15 — task-facing core.** Four coordinated view combinations are
  frozen around concrete review decisions. The remaining seven-family gallery
  remains a broad exploratory and communication surface and is still an
  explicit artifact commitment.
