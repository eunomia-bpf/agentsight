# R204 OSDI Gate Review After Long-Tail Promotion Integration

Date: 2026-06-15
Reviewer: read-only subagent using the OSDI-style gate rubric
Scope: R203/R193/R194/R195/R202 integration plus the current research docs and
claim boundaries.

## Verdict

Current state remains Level 3 and is not OSDI weak accept.

R203/R193/R194/R195/R202 do not clear the weak-accept gate. The strongest
blocker is still C5 developer utility because no real participant responses
exist. C6 human adequacy is the second must-fix blocker because no human labels
exist.

## Findings

High severity: C5 and C6 are still missing outcome evidence. The project has a
credible mechanism/system artifact, but the utility and tag-adequacy outcome
claims remain unsupported.

Medium severity: no overclaim was found for R203/R193/R194/R195/R202. The
review found that the docs consistently keep these artifacts scoped as
logistics, protocol, regeneration-smoke, or promotion-gate artifacts. They do
not claim developer utility, tag adequacy, canonicalization quality, or a
canonical-map update.

Low severity wording nit: some tables list R202/R203 under C6 partial evidence.
The surrounding text correctly says these are protocol/gate artifacts, but the
tables should prefer the phrase "C6 protocol/gate artifacts" to reduce reviewer
ambiguity.

## Minimum Next Evidence

The smallest non-fabricated next artifacts remain:

- real R142/R151 participant responses scored through the frozen C5 gate;
- independent/adjudicated R124 human adequacy labels;
- R190 and R203 labels only if the paper claims canonicalized long-tail quality
  or regenerated-tag promotion quality.

## Gate Effect

This review does not change any claim gate. It reinforces the current boundary:
R203 and the human-evidence pipeline are useful infrastructure, but subagent
review, LLM-generated labels, mock responses, placeholder rows, and empty
review packets cannot substitute for human evidence.
