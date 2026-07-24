# Independent Result Review

## Verdict

**PASS only as a narrow negative/mixed implementation result.**

The experiment supports reporting that the current artifact/cross-session
projection did not pass the source-direct correctness check. It does not
support a complete tool-capability, Raw-reader, cost, efficiency, or
superiority claim.

## Reconciled Evidence

- The source-direct checker reparsed 72 archived native session files from six
  projects, reconstructed 1,721 artifact edges, and reproduced all 120 oracle
  answers.
- The deterministic matrix contains 480 rows: four methods by 120 questions,
  with 80 rows for each project.
- Trajectory and ProcGrep return identical answers on all 30 action questions,
  but those answers agree with the experiment's source-direct action grammar
  on only 18/30 questions.
- Trajectory answers all 60 artifact-linked and cross-session questions, with
  32 correct and 28 wrong. Project-level conditional accuracy is 1.000, 0.400,
  0.700, 0.000, 0.600, and 0.500.
- Final State answers all 30 final-state questions. Trajectory answers 28 and
  abstains on two.

These values are sufficient to reject the current implementation's narrow
exact-fact capability claim. They do not refute workspace-centered trajectories
as a research abstraction.

## Required Interpretation Boundaries

1. The source-direct action grammar is not identical to ProcGrep's official
   adapter grammar. In particular, the checker admits terminal reads that the
   Claude adapter intentionally leaves unclassified. The action result is
   therefore a disagreement with the experiment's source grammar, not a
   failure to preserve ProcGrep. ProcGrep preservation passed exactly.
2. The exact numeric B+C veto thresholds were inherited from the superseded
   Step 0003 plan and were not restated prospectively in Step 0004. The
   conclusion is nevertheless robust because 28/60 answered B+C facts are
   wrong; the thresholds must not be described as newly frozen in this step.
3. Raw is N/A. The Terra reader made 11 local retrieval calls and received
   117,184 bytes, but the boundary monitor stopped the single allowed preflight
   after an original absolute path embedded in evidence appeared in a command.
   This is a harness/contract incompatibility, not a model-capability result.
4. The completed deterministic preflight covered all six projects and is
   reused as the final deterministic matrix. The integrated 840-row comparison
   is incomplete because none of the 360 Raw rows ran.
5. The same per-project loop duration was assigned to all four deterministic
   methods. Those timing rows cannot be compared as method-specific inference
   costs.

## Impact On Existing Empirical Results

RQ1--RQ6 are not automatically disproved, but the shared projection means they
cannot simply be declared unchanged. Under the RQ7 grammar, source/projection
edge counts are respectively 86/101, 206/2,308, 277/436, 501/408, 262/253, and
389/474 across the six projects. RQ1, RQ3, and RQ4 are most exposed; RQ2 is
exposed where mutation linkage matters. RQ5 has a separate 2,063-stream source
checker, and RQ6 uses an independent public-data reconstruction, so those two
are better protected. A follow-up error taxonomy must distinguish deliberate
broader shell/scope admission from path, artifact-identity, and native-root
session-join errors before treating local projection counts as source truth.

## Impact On Agent Nebula

Do not visually rebuild Agent Nebula. Keep file stars, stable directory colors,
dynamic directory clustering, action-order halos, and native-root session
semantics. First settle the projection contract:

- distinguish direct structured file effects from weaker shell/scope
  inference;
- verify artifact identity and native-root session joins;
- exclude inferred effects from paper measurements unless explicitly admitted;
- never use force-layout coordinates as research evidence.

The current result is a measurement-validity finding, not evidence that the
file-star visual grammar is wrong.
