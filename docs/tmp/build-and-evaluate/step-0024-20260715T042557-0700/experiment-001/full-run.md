# Full Run — Monotone Cross-Action Calibration

**Run status:** VALID
**Completeness:** COMPLETE
**Fixed verdict:** SUPPORTED

No code, plan, metric, population, or candidate changed after REAL PREFLIGHT.
All three approved commands ran once on the existing complete trajectories.

## Complete Populations

| Population | Sessions | Operations | Adjacent pairs | Oracle groups/stages |
|---|---:|---:|---:|---:|
| OSWorld-Human | 287 | 3,978 | 3,691 | 2,042 |
| CodeTraceBench | 405 | 20,866 | 20,461 | 2,948 |

## Primary Result

| Population | Current B$^3$ F1 | Candidate B$^3$ F1 | Exact relation |
|---|---:|---:|---|
| OSWorld-Human | 0.786170 | 0.786170 | equal |
| CodeTraceBench | 0.475008 | 0.649173 | higher |

The fixed rule requires no lower B-cubed F1 on either complete population and
strictly higher B-cubed F1 on at least one. The candidate is exactly equal on
OSWorld-Human and strictly higher on CodeTraceBench. The result is therefore
SUPPORTED with no tolerance or aggregate substitution.

## Boundary And Mechanism Diagnostics

| Population | Current boundary F1 | Candidate boundary F1 | Removed current boundaries | Added current boundaries |
|---|---:|---:|---:|---:|
| OSWorld-Human | 0.679922 | 0.679922 | 0 | 0 |
| CodeTraceBench | 0.268506 | 0.287106 | 5,974 | 0 |

OSWorld candidate and current decisions are identical on all 3,691 pairs. Its
candidate confusion counts are TP/FP/FN/TN = 1,402/967/353/969.
CodeTraceBench candidate counts are 1,297/5,195/1,246/12,723. The monotone rule
reduces the CodeTraceBench predicted groups from 12,871 to 6,897 while never
adding a current-relative boundary. B-cubed F1 improves in OpenHands,
SWE-agent, Terminus2, and mini-SWE-agent.

## Rust/Python Equivalence

The release Rust path and fixed Python evaluator agree on:

- all 3,691 boundary decisions, including current and candidate outcomes;
- all global, raw cross-action, and applied cutoffs within `1e-12`;
- all 3,978 motif assignments;
- all 2,656 segments and 44 unique motifs;
- all 3,978 units of profile mass;
- every legacy/global calibration alias.

The CodeTraceBench Rust inputs contain only unit-weight `session` and `action`.
The target is disjoint from the 2,229-session, 87,703-operation reference.
Official stages and historical scored summaries load only after prediction.

## Evidence Boundary And Adoption

The candidate is adopted as the release operation-stack induction rule. This
is supporting post-hoc implementation-selection evidence on two reused
complete populations. It is not untouched confirmation, literal motif-name
validation, cross-family generalization of every tag type, or an answer to all
of RQ3. The thesis, positive RQ3 hypothesis, four RQs, contribution, and paper
story do not change.

Raw roots:

- `.agentsight/experiments/rq3-monotone-recurrence-v1/full/`
- `.agentsight/experiments/rq3-monotone-recurrence-rust-equivalence-v1/full/`
- `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`
