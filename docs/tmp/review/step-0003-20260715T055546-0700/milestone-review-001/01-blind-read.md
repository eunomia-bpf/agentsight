# Blind Full-Paper Read and Attack Map

Timestamp: 2026-07-15T05:55:46-07:00
Parent: REVIEW step 0003 / milestone 001
Objective: judge the complete paper before using prior experiment verdicts
Inputs: `docs/paper/main.tex`, rendered six-page PDF, bibliography, Figure 1

## Provenance and reviewer context

The contribution is primarily a software-visualization/measurement system;
VISSOFT or a TVCG-style application/design-study track is the most plausible
venue. A systems bar is also relevant to the exporter, evidence semantics, and
performance claims. I loaded the research-taste and systems-review references.
The target venue is not named, which is itself an ambiguity: the present paper
is too incomplete for SOSP/OSDI and under-evaluated for a full visualization
paper, but stronger than a tool-demo paper in evidence discipline.

This reviewer is unavoidably contaminated: the same root agent implemented the
artifact and already knew the RQ1 result. I therefore treat the following as a
paper-only reconstruction, not a genuinely independent blind review.

## Paper perceived by a reviewer

- **Problem and stakes:** long-running coding agents produce fine-grained
  trajectories that neither Git nor a persistent human retains; raw histories
  are too large to review.
- **Challenged belief:** commits and human authors are sufficient units for
  software-evolution analysis.
- **Simple principle:** recorded process, durable outcome, and current endpoint
  are complementary evidence and must be visualized together without being
  conflated.
- **Artifact:** a Rust native-history/Git exporter plus a coordinated browser
  atlas that adapts seven established visualization families.
- **Causal connection:** the three-layer model supplies common selections and
  evidence boundaries; the gallery makes different structural units
  perceptible.
- **Claimed contributions:** evidence representation, coordinated atlas, and an
  RQ1 association evaluation with a negative naturalistic boundary.

## RQ map

1. RQ1 asks whether native events can be associated with Git and endpoint
   lines. It is answered: controlled exact-hunk evidence passes, naturalistic
   calibration/support and line transfer do not.
2. The paper renames the intended behavioral-structure RQ into an “atlas
   experience” RQ. It offers author observation, not a held-out behavioral
   analysis.
3. The paper calls local browser latency RQ3 although the project contract's
   RQ3 is human review utility and RQ4 is scalability. This is honest in prose
   but is still a silent RQ substitution at the paper-architecture level.

## Initial verdict

**Reject as a full research paper; promising as an artifact/experience paper.**
The paper's strongest property is claim calibration: it refuses to turn
temporal adjacency into provenance. Its strongest reject hypothesis is that it
is a well-engineered gallery of known encodings whose only rigorous experiment
evaluates an enabling join rather than the visualization's scientific value.

## Ranked attack map

1. **Blocker — evidence/evaluation:** no human or in-situ evidence shows that
   the coordinated views recover theory, improve a review decision, or beat
   Git-only/event-table baselines.
2. **Blocker — global consistency:** original behavioral RQ2 and review-utility
   RQ3 are replaced by qualitative author experience and latency. A full
   empirical paper does not answer all promised RQs.
3. **Major — novelty/taste:** all charts are explicitly inherited; the common
   three-layer model is sensible but the paper does not yet show a new
   falsifiable consequence beyond “show layers separately.”
4. **Major — external validity:** one repository, three sparse observation
   days, only two mature, and no naturalistic Gemini writes cannot support
   “long-horizon agentic software evolution” broadly.
5. **Major — systems scale:** 6.13 MB and 6,535 path rows are small; seven local
   repetitions do not test days-to-months growth, burst load, data chunking, or
   interaction tails at promised scale.
6. **Minor — implementation detail:** the paper gives versions and core rules
   but lacks exporter throughput and memory methodology, and does not compare
   its Perfetto compatibility output with the custom timeline.

## Completion and next node

The blind attack map is complete. External search must now attack the closest
same-claim systems, expected evaluation protocols, stronger baselines, and the
reality of invisible/fragmented agent identity.
