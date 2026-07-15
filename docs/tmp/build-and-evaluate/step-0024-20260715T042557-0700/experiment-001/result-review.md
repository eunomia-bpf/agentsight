# Independent Raw-Result Review

**Validity:** VALID
**Completeness:** COMPLETE
**Fixed scientific verdict:** SUPPORTED
**Must-fix findings:** none

The independent reviewer explicitly used `research-experiment-design`, read
the approved plan and all preflight/review records, and reconstructed the
complete results from retained raw decision and assignment outputs. It made no
edit and requested no additional experiment.

## Independent Reconstruction

OSWorld-Human contains exactly 287 sessions, 3,978 operations, 3,691 scored
pairs, and 2,042 human groups. Candidate B-cubed F1 is
0.7861695437481889 under the independent reconstruction and equals the current
0.7861695437481895 up to the scorer's floating accumulation order; all 3,691
candidate/current decisions are exactly identical. Candidate boundary counts
are TP/FP/FN/TN = 1,402/967/353/969, with 0 removed and 0 added current
boundaries.

CodeTraceBench contains exactly 405 targets, 20,866 operations, 20,461 scored
pairs, and 2,948 official stages. Candidate B-cubed F1 is
0.6491731039323719 versus current 0.4750077514434528. Candidate boundary counts
are TP/FP/FN/TN = 1,297/5,195/1,246/12,723, with 5,974 removed current
boundaries and 0 added. B-cubed F1 improves independently in all four agent
frameworks and exactly matches the already-observed Step 0022/0023 component
output.

Under the predeclared exact relation, OSWorld is equal and CodeTraceBench is
higher. Thus B-cubed F1 is no lower on both populations and strictly higher on
one: the fixed verdict is SUPPORTED.

## Validity And Equivalence

The reviewer confirms complete source identity, coverage, conservation,
reference/target disjointness, and scorer isolation. Rust/Python equivalence
covers all 3,691 OSWorld decisions, 3,978 assignments, 2,656 segments, 44
motifs, and 3,978 mass. Raw global, raw cross-action, and applied cutoffs agree
within `1e-12`; current and candidate decisions agree exactly. CodeTraceBench
construction sees only unit-weight `session` and `action`, and labels load only
after prediction.

## Adoption Boundary

The reviewer approves adopting the monotone candidate as the release
implementation. The result is supporting post-hoc implementation-selection
evidence on reused trajectories, not a new benchmark discovery, untouched
confirmation, literal tag-name validation, or a complete answer to RQ3. Only
design, implementation, canonical evaluation, and paper text owned by the
release algorithm/result may change. The fixed thesis, four RQs, positive RQ3
hypothesis, contribution, and AgentProf story must remain intact.
