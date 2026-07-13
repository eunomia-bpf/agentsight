# Round 7 — Language: Word Choice

**Completed:** 2026-07-12T18:37:13-07:00  
**Cycle/gate:** cycle 0001 / full WRITE  
**Parent:** `round-6-language-sentence.md`  
**Reviewer:** fresh read-only subagent using `paper-writing-style`, word focus  
**Verdict after fixes:** PASS

## Raw Findings

The reviewer found seven must-fix semantic/wording defects: activities “growing
into systems,” a profile “testing” its own effect, vague “joint engineering
consequence/consequential frame,” opaque “inclusive membership,” an unclear
“this responsibility,” an incomplete 90% denominator, and “checking a
decision.” It also flagged dense compounds, project-report phrasing, vague
subjects, nominalizations, slash constructions, compressed top-10 prose, and
artifact-style “rows/backend leads” wording.

## Applied Fixes

- Replaced activities with agent deployments as the thing that grows.
- Made later runs—not the profile—test a predicted effect.
- Rewrote the Design flow with concrete actors: accurate attribution and
  reusable identities improve a decision; a profile highlights recurring
  behavior; retained records identify the prompt/tool/workflow; a held-out rerun
  verifies the intervention.
- Replaced “inclusive membership” with the operations contributing to inclusive
  mass.
- Rewrote the central prediction around measurements fragmented across runs and
  an intervention that per-run trees do not reveal.
- Specified “90% of the group's weight.”
- Replaced checking a decision with checking an intervention outcome against an
  independently recorded effect.
- Simplified the Abstract to corpora, recurring behaviors, validated
  attribution, weight folding, and four RQs. It ends on the verified RQ1 result.
- Replaced project-report verbs in Introduction, contributions, Evaluation
  overview, Setup, RQ1, and RQ3 with direct scientific statements while
  preserving explicit experiment status.
- Improved background verbs (`identify`, `encodes`), implementation input/output
  phrasing, profiling `weight` terminology, and high-ranked-category prose.
- Replaced `oracle` and slash construction with “reference” and “accounting and
  compression.”
- Replaced RQ3 “rows” with boundary tasks and “leads” with “outperforms the
  strongest simple baseline.”

## Consider Findings

The strong title, exact thesis, four exact RQ headings, and scope-bearing
Limitations qualifiers remain unchanged. Removing those qualifiers would make
the paper less accurate, not more attractive.

## Preservation And Intent Check

No number or citation changed; citation-command count remains 59. Exact thesis
and four RQs are unchanged. Abstract is exactly 200 words and 9 sentences. The
revision makes the story more active and concrete without adding terminology,
negative intermediate results, or unsupported evidence.

## Build Evidence

`make` completed successfully. The log has no undefined citation/reference,
LaTeX error, emergency stop, or overfull box. The PDF remains 9 letter-size
pages.

## Next Node

Proceed to Round 8 terminology and claim tone.
