# Step 0072 Report — Current RQ2 Information-Matched Baseline

**Timestamp:** 2026-07-23T20:17:00-07:00  
**Status:** complete; transition to RQ3 EXPERIMENT Gate

## Objective

Re-evaluate RQ2 with the current automatic AgentProf representation and the
strongest fair baseline, without changing the paper's thesis, story, four RQs,
or contribution scope.

## Experiment

All 1,756 trajectories and 27,346 operations from AgentProcessBench,
HINTBench, and TraceElephant were scored. The candidate lexicographically
combines an operation-local diagnostic score with the current fixed
Agent+Evidence group score, so the profile can only refine exact local-score
ties. The strongest control replaces the semantic prefix with raw action while
retaining identical source-kind/tool/outcome evidence and aggregation.

| Workload | Local+AgentProf | Local+Raw+Evidence | Local | AgentProf only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .894270 | .893071 | .863171 | .790615 |
| HINTBench | .517489 | .518022 | .410559 | .432392 |
| TraceElephant | .325504 | .323927 | .208713 | .259313 |

Candidate-minus-local differences are +.031099 [.023695,.039306], +.106930
[.093354,.120374], and +.116792 [.087611,.147876]. Candidate-minus-matched-raw
intervals all include zero.

## Interpretation

The complete AgentProf profile clearly complements a fixed local diagnostic
signal on all three populations. This experiment does not attribute that gain
specifically to the semantic prefix when source evidence is matched. The
result is adaptive mechanism evidence on previously observed populations, not
untouched backend generalization.

This result does not change or shrink the thesis. It closes this scoring branch
and redirects the scientific search toward settings where cross-run semantic
responsibility should matter: population-level recurrence, attribution, and
review decisions under lexical or structural variation.

## Verification

- Two independent plan reviews: PASS.
- Complete full-population run: PASS.
- Independent implementation and exact numerical reconstruction: PASS.
- Label/evidence leakage and information-parity audit: PASS.
- Current scorer compile and assertions: PASS.
- Existing canonical-tag tests: 7/7 PASS.
- LaTeX build and revised table visual inspection: PASS.
- Whole-paper source-grounded review: Step PASS, paper routes to another
  EXPERIMENT cycle.

## Material changes

- Added `script/rq2_current_agent_local_first.py`.
- Replaced the RQ2 body comparison with the local-first matched design.
- Corrected CodeTrace A2 provenance from an incomplete Qwen run to the actual
  independent Codex Agent batches plus root validation.
- Updated `docs/evaluation.md`, `docs/background-related-work.md`, and
  `docs/idea-story.md`.
- Added the author's three newest instructions verbatim to
  `docs/user-instruction.md`.
- Added complete plan, reviews, preflight, full-run, write, whole-paper review,
  and outer-audit reports under this step directory.

## Remaining evidence frontier

1. RQ3: isolate recursive structure from naming/evidence effects and evaluate
   the fixed method beyond its initial 41-session product-design subset;
   investigate ACT*ONOMY as closest work and possible public baseline.
2. RQ4: include source adaptation and automatic annotation latency, tokens,
   failures, profile construction, and quality/cost tradeoff.
3. RQ1: test comparative population-level attribution or explicitly position
   the current multi-resource result as motivation/capability rather than
   algorithmic superiority.
4. Final WRITE: synchronize abstract/introduction/conclusion with the strongest
   matched controls only after these experiments stabilize.
