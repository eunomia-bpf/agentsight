# BUILD_AND_EVALUATE Step 0004 Report

## Question

Can the current artifact-linked trajectory recover source-verifiable
action-only, artifact-linked, cross-session, and final-state facts more
completely than Final State, Counts, and ProcGrep, while remaining correct?
Can a bounded Raw-log model reader recover the same facts?

## Reviewed Plan

- Experiment:
  `experiment-001/plan.md`
- Independent plan review:
  `experiment-001/plan-review.md`
- Initial verdict: BLOCK because the inherited checker trusted intermediate
  edges, shell redirects/heredocs became fake artifacts, the changed Raw
  baseline had not been reviewed, and its filesystem boundary was incomplete.
- Final verdict: PASS after adding a source-direct checker, rederiving all
  questions, excluding redirect/heredoc segments, independently deriving
  cutoff state, and isolating Raw with Bubblewrap.
- Reader amendment: `gpt-5.6-sol` produced no scoreable answer in three
  transport attempts. A separately reviewed one-time change to
  `gpt-5.6-terra` retained all other budgets and allowed one preflight only.

## Evidence

The new experiment reuses the same 72 archived native session files and cutoff
workspace evidence as Step 0003. It does not rediscover live sessions. A
standalone Python checker imports neither the primary experiment script nor
`agent-session`; it reparses Claude, Codex, and Gemini records, reconstructs
1,721 artifact edges, reselects anchors, independently checks archived Git
index/presence evidence, and reproduces all 120 oracle answers.

The deterministic comparison is complete:

- 6 projects;
- 120 questions, 30 per family;
- 4 methods;
- 480 scored rows;
- 24 recorded method/project cost rows, which are not method-specific timing
  evidence because one project loop supplies all four deterministic times.

The bounded Raw reader is N/A. The single Terra preflight made 11 local
retrieval calls and received 117,184 bytes, but the frozen boundary monitor
stopped it when an original absolute path embedded in the evidence appeared in
a command. No Raw answer was scored. The planned 360 Raw rows therefore did not
run, and the integrated 840-row comparison is incomplete.

## Result

| Method | A action-only | B artifact-linked | C cross-session | D final-state |
|---|---:|---:|---:|---:|
| Final State | 0 correct, 30 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain | 30/30 correct |
| Counts | 7 correct, 11 wrong, 12 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain |
| ProcGrep | 18 correct, 12 wrong | 30 abstain | 30 abstain | 30 abstain |
| Trajectory | 18 correct, 12 wrong | 16 correct, 14 wrong | 16 correct, 14 wrong | 28 correct, 2 abstain |

Trajectory preserves ProcGrep's A answers exactly. The A disagreement is
between ProcGrep's official adapter grammar and the experiment's broader
source-direct grammar, not a failure to preserve ProcGrep.

Trajectory's B+C correct coverage exceeds ProcGrep by 0.533 on the frozen
denominator, with project-block interval [0.283, 0.767], but this is not a
positive result: 28/60 answered B+C facts are wrong. Project-level B+C
conditional accuracy is 1.000, 0.400, 0.700, 0.000, 0.600, and 0.500.

## Decision

- **Current exact-fact tool capability:** rejected.
- **ProcGrep action preservation:** passed.
- **Raw-model comparison:** N/A; no model-performance inference.
- **Efficiency/cost superiority:** not tested.
- **Workspace-centered research abstraction:** not refuted.

The independent result review passes the run only as a narrow negative/mixed
implementation result. It blocks any complete capability, Raw-reader, cost,
efficiency, or superiority interpretation.

## Impact On The Empirical Study

The shared local projection cannot be treated as source truth. RQ1, RQ3, and
RQ4 are most exposed; RQ2 is exposed where mutation linkage matters. RQ5 is
better protected by its separate 2,063-stream checker, and RQ6 by an
independent public-data reconstruction. The paper now reports RQ1--RQ4 as
measurements under the declared projection and makes the source-conformance
limitation explicit.

The next measurement step is an error taxonomy separating:

1. direct structured file effects;
2. weaker shell/path-scope inference;
3. path/worktree normalization;
4. create/rename/delete artifact identity;
5. native-root session joins.

## Impact On Agent Nebula

No wholesale visual redesign is justified. Keep file stars, stable directory
colors, dynamic directory clustering, action-order halos, and native-root
session semantics. Projection conformance must precede new trajectory
decoration. Weaker inferred effects may remain useful for replay only if their
evidence strength is visibly distinct; they cannot silently enter paper
measurements. Force-layout coordinates remain presentation-only.

## Artifacts

- Result: `experiment-001/result.md`
- Independent result review: `experiment-001/result-review.md`
- Source-direct checker:
  `../../../../agentvis/research/rq7_source_oracle_check.py`
- Sanitized rows and decisions: `experiment-001/raw/`
- Figure: `experiment-001/figures/rq7-measurement-capability.pdf`
