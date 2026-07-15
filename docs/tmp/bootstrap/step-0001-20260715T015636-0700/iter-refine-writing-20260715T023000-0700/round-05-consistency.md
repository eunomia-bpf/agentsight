# Round 05: Terminology And Cross-Document Consistency

Skill: `check-terminology-infoflow`, paper-consistency mode
Reviewer mode: independent read-only subagent

## Reviewer Findings

### Must-fix

1. Present-tense exporter and renderer language implied implementation even
   though only the existing vendor-neutral parser is currently available.
2. The walkthrough treated every normalized event as path-association eligible.
3. Candidate association was upgraded to “provenance” before RQ1 validation.
4. RQ1 conflated event-to-Git accuracy with Git-to-current-line lineage and
   used unclear denominators.
5. RQ2's question omitted cross-session and cross-agent stability.
6. RQ3 task terminology drifted from the canonical association states and
   omitted the full-data noncoordinated table condition.
7. “Churn” referred to both repeated event edits and Git change frequency.

### Should-fix

The reviewer requested a named core view for association-state tasks, explicit
path-referencing events instead of undefined touch events, and consistent
matched-run/ghost and vendor/model identity terms.

### Consider

Perfetto's RQ3 and RQ4 roles needed an explicit distinction.

## Root Decisions And Applied Fixes

- Added an explicit status statement and changed planned exporter, join,
  rendering, and interaction mechanisms to future tense. The existing parser
  remains the only completed component claimed in the paper.
- Added a not-association-eligible state. Unmatched now refers only to eligible
  events for which the join finds no Git change.
- Replaced event-to-line provenance with candidate event-to-hunk association
  followed by Git hunk-to-current-line lineage. Line overlays require an
  RQ1-supported confidence stratum.
- Split RQ1 targets and denominators for event association versus Git lineage,
  and report pathless, ambiguous, and unmatched records separately.
- Restored cross-session and cross-agent stability to RQ2. Distinguished
  repeated edit attempts from Git change frequency and expanded ordered
  coupling to ordered read-before-edit coupling.
- Replaced candidate-durable event wording with the canonical eligible,
  candidate, and unmatched states. The RQ3 condition list now includes the
  noncoordinated full-data table.
- Designated a matrix/detail core view for the association-state task, replaced
  touch events with path-referencing process events, grouped agent sessions by
  vendor/model, and bridged the matched-run (ghost) name.
- Assigned Perfetto to RQ3 as an interface ablation and to RQ4 only when inputs
  are equivalent.

## Deferred Canonical Sync

The more precise eligibility, association, and lineage vocabulary must be
propagated to `docs/design.md`, `docs/implementation.md`, and
`docs/evaluation.md` during the BOOTSTRAP review gate. The paper is the current
candidate contract until that audit accepts or rejects the refinements.

## Verification

`make -C docs/paper` completed successfully and produced a six-page PDF. The
cumulative snapshot diff contains 398 insertions and 151 deletions. Targeted
searches found no remaining rejected candidate-durable, generic churn, touch-
event, validated-provenance, or present-tense exporter/rendering claims.
