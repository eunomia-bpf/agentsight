# BOOTSTRAP Step 0002 — Empirical-Study Reconstruction

**Started:** 2026-07-22T18:20:00-07:00
**Parent:** BUILD_AND_EVALUATE Step 0003, Node E19
**Status:** active; scientific contract reopened by explicit author direction

## BOOTSTRAP_GATE

### Node B28 — Recover the actual source boundary

**Question.** Which earlier conclusions are source facts, which are properties
of a lossy projection, and which empirical questions remain non-obvious after
the closest 2025--2026 trajectory studies?

**Inputs.** The root reread the complete user instructions, idea story,
empirical-study contract, paper, design/evaluation frontiers, Step 0002 results,
and Step 0003's incomplete RQ7 record. It inspected `agent-session` parsing,
the repository projection, native Claude Skill records, and public trajectory
dataset schemas. The associated literature report is
`literature-20260722T182000-0700/literature-report.md`.

**Findings.** Native Claude source records retain exact Skill names and
arguments plus attribution metadata. `agent-session::ToolEvent.command` keeps
only a display-oriented, possibly truncated projection and
`RepositoryEvent` drops it entirely. Consequently the old claim that the
corpus omits Skill names/arguments is false. The claim “activity is not
progress” is also too obvious and too occupied to stand alone. The scientific
unit that survives is how artifact lineages consolidate, move, validate,
resume, and respond to explicit process mechanisms across native sessions.

The six author-associated repositories contain broad natural longitudinal
work but do not estimate population prevalence. Public data provide a
complementary boundary: Open-SWE-Traces exposes 207,489 single-attempt coding
trajectories in a 2-harness by 2-model design; IdeaTrail exposes 1,170
synthetic scientific-ideation trajectories with explicit artifact updates.
Neither is a substitute for natural cross-session workspace evolution.

**Decision.** Replace the seven-RQ sprawl with six empirical questions. Merge
old RQ1 and RQ3 into artifact consolidation; sharpen validation and focus
evolution; compare real source-session boundaries with matched within-session
boundaries; replace the old RQ6 coverage stop with explicit skill/instruction
footprints; and add an external-boundary RQ that tests which within-session
relations replicate in public task trajectories. Demote the unfinished
measurement-capability comparison from the main empirical paper rather than
letting it dominate the study.

### Candidate scientific contract for review

1. **Artifact consolidation.** How do introduced and repeatedly mutated
   artifact lineages become retained, reused, validation-associated, dormant,
   or revived over action time?
2. **Validation response.** How are exploration, mutation, and validation
   ordered, and how does the observed artifact trajectory change after
   recognized success or failure?
3. **Focus evolution.** How do artifact/module hotspots form, migrate, cool,
   and revive across code, tests, papers, data, results, and documentation?
4. **Cross-session continuity.** What re-grounding and prior-artifact overlap
   precede the first mutation after a source-session component boundary,
   relative to matched within-session pseudo-boundaries?
5. **Skill/instruction footprints.** What source-explicit process footprints
   can be attributed to named Skill invocations, are repeated named-Skill
   footprints more similar than matched different-Skill footprints across
   independent root sessions, and what focal activity follows explicit
   instruction-read events?
6. **External boundary.** Which within-session relations from RQ1--RQ3
   replicate in public coding and scientific-research trajectories, and which
   observations require natural persistent multi-session workspaces?

These questions are descriptive and relational. They do not infer intent from
file movement, label low-revisit documents as useless, or claim causal
skill/harness effects. Project is the main natural case unit; session is not
treated as an independent project sample.

### Figure contract

Every retained RQ has one decision-bearing figure:

- F3 artifact-state/competing-risk curves and revival intervals;
- F4 validation-aligned state transitions and event-distance response curves;
- F5 hotspot rank turnover, module migration, and revival small multiples;
- F6 true-boundary versus matched pseudo-boundary re-grounding contrasts;
- F7 separate Skill-attributed footprint and instruction-focal panels, including
  root-session support and within/between-Skill distance;
- F8 local-versus-public replication map with explicit N/A cells.

Agent Nebula is not a result plot. Its redesign decision will be derived after
F3--F7 show which structures matter; no visualization code changes are admitted
in this bootstrap node.

### Next gate

RQ5 is first because it corrects a known false stop and tests whether the
source abstraction is adequate. The experiment plan is
`experiment-rq5-skill-footprints/plan.md` and requires fresh independent review
before implementation or a full run.

### Node B29 — RQ5 plan review

**Status:** complete; approved for implementation and real preflight.

The fresh reviewer first blocked the plan because source files for nested
agents are not independent sessions, the primary episode was ambiguous, the
matched null used a post-invocation outcome, eligibility gates were too weak,
and the thin projection lacked the identities required to prove joins. The
revised plan closes all five blockers: native root session is the independent
block; source stream remains nested; primary Skill membership requires a
unique native invocation-to-`attributionSkill` join; instruction reads are
separate focal events; null restrictions use pre-invocation fields; support
gates produce N/A rather than pooled estimates; and an independent checker
must recompute every source anchor and join. The follow-up verdict is PASS and
is recorded in `experiment-rq5-skill-footprints/plan-review.md`.

The next node may minimally extend the existing Rust abstraction and execute
the declared real preflight. No result interpretation is allowed before the
source checker and eligibility tables pass.

### Node B30 — Corrected Skill/instruction source run

**Status:** real six-case run complete; corrected result independently reviewed PASS.

The minimal `agent-session` and repository extension preserves exact Skill
name/arguments, source attribution, model, native root-session identity,
source-stream identity, role and prompt index without adding a second general
event IR. Regression tests include an argument longer than the
display-oriented 300-character command field and two transcript files sharing
one native root session.

A fresh cutoff (`1784760000000`) projected all six selected projects. The
focused analyzer finds 67 explicit Skill invocations and 1,675 native
attributed Tool actions. An independent source checker reread all 2,063
included native streams and reconciled all 7,304 projected Skill/instruction
signal rows plus 205,836 adjacent Tool boundaries with zero failures. Five
exact-context Skill strata meet the three-root support gate, but only
agentskill-observability-paper contains two or more qualified Skills in one
exact project/vendor/model/source-role stratum. Its 9 same-Skill and 10
different-Skill pairs have median distances 0.116 and 0.123; the one-sided
exact root-block randomization gives p=0.750 over 12 admissible assignments
(four distinct statistic values). This does not support a stable or repeatable Skill
fingerprint. Instruction reads/mutations remain separate
focal events and never define harness exposure.

Preflight also refined the source topology: a parent stream may contain the
explicit invocation while delegated execution carries native attribution in a
child stream under the same root. The primary descriptive unit is therefore
root-session x source-attributed Skill; same-stream invocation linkage remains
a coverage audit, not an invented episode boundary. The revised estimator is
strictly weaker than the planned causal-sounding episode interpretation.

For Agent Nebula, this evidence supports the existing spatial skeleton but
changes session semantics: short-term trajectory state resets only at a native
root-session boundary, not at every subagent transcript stream. The design
frontier now recommends clearer fading action-order focus and a small external
role/Skill legend, without permanent edges or a new layout family.
