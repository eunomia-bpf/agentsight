# Complete Existing-Trajectory Run

**Completed:** 2026-07-15T06:45:00-07:00  
**Execution status:** valid and complete  
**Fixed scientific verdict:** **MIXED**  
**Release disposition:** reject candidate; retain Step 0024

## Complete Populations

| Population | Sessions | Operations | Adjacent decisions | Official groups/stages |
|---|---:|---:|---:|---:|
| OSWorld-Human | 287 | 3,978 | 3,691 | 2,042 |
| CodeTraceBench | 405 | 20,866 | 20,461 | 2,948 |

Both populations reuse the exact Step 0024 inputs and scorer keys. No new
trajectory, annotation, mapping, field, or baseline was introduced.

## Primary Fixed Verdict

| Population | Step 0024 B$^3$ F1 | Candidate B$^3$ F1 | Delta | Relation |
|---|---:|---:|---:|---|
| OSWorld-Human | 0.786170 | 0.746958 | -0.039212 | lower |
| CodeTraceBench | 0.649173 | 0.671671 | +0.022498 | higher |

The predeclared rule requires no lower B-cubed F1 on both populations and
strictly higher on at least one. The candidate is lower on OSWorld-Human and
higher on CodeTraceBench, so the exact verdict is MIXED and the Pareto
hypothesis is contradicted.

## Boundary And Partition Diagnostics

On OSWorld-Human, boundary F1 falls from 0.679922 to 0.547227. The candidate
suppresses 842 of 2,369 Step 0024 boundaries, leaving 1,527 boundaries and 1,814
predicted groups. B-cubed precision/recall changes from 0.855872/0.726966 to
0.714704/0.782261: merging raises recall but loses too much precision.

On CodeTraceBench, boundary F1 falls from 0.287106 to 0.272388 while B-cubed F1
rises. The candidate suppresses 2,067 of 6,492 Step 0024 boundaries, leaving
4,425 boundaries and 4,830 predicted groups. B-cubed precision/recall changes
from 0.828579/0.533630 to 0.792278/0.582933. B-cubed improves within all four
frameworks:

| Framework | Step 0024 | Candidate |
|---|---:|---:|
| OpenHands | 0.661593 | 0.681565 |
| SWE-agent | 0.707955 | 0.711136 |
| Terminus2 | 0.593876 | 0.627414 |
| mini-SWE-agent | 0.683439 | 0.702016 |

These diagnostics identify a real workload-dependent precision/recall tradeoff;
they cannot override the fixed two-population primary verdict.

## Validity And Equivalence

- Every final boundary is a Step 0024 threshold boundary.
- Every same-action decision is unchanged.
- Rust and Python agree on all 3,691 OSWorld decisions, 3,978 assignments,
  1,814 segments, 139 motifs, and all 3,978 units of mass.
- Raw NPMI is exact across implementations; the maximum cutoff difference is
  `6.58e-15`, below the existing `1e-12` equivalence tolerance.
- CodeTraceBench construction uses only unit weight, `session`, and `action`
  from the 2,229-session/87,703-operation disjoint reference; official stages
  and visible phase are unavailable until scoring.
- Every OSWorld scorer field is excluded from construction, every target is
  assigned once, and both profile masses are exactly conserved.

## Decision

Do not adopt sequence-local suppression as the release operation-stack
constructor. Restore only this candidate's implementation and tests, retain the
complete result as research history, and keep Step 0024 as the current release
algorithm. This local mechanism result does not change RQ3, its positive
hypothesis, the exact thesis, the four-RQ architecture, or the paper story.

Raw summaries:

- `.agentsight/experiments/rq3-contextual-recurrence-v1/full/summary.json`
- `.agentsight/experiments/rq3-contextual-recurrence-rust-equivalence-v1/full/summary.json`
- `.agentsight/experiments/rq3-contextual-recurrence-codetracebench-v1/full/summary.json`
