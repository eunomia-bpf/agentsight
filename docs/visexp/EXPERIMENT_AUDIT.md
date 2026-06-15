# AgentFlame Experiment Audit

Last updated: 2026-06-15
Stage at update: audit / supplement
Source/command: OSDI rubric audit over `docs/visexp/STATE.md`, `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/out/evaluation.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/model-benchmarks-r123.json`, `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-label-join-r124.json`, `docs/visexp/out/user-task-results.json`, and `docs/visexp/out/artifact-usability-r160.json`
Completeness: partial

## Audit Verdict

Current maturity: Level 3 conference-paper mechanism evidence, not Level 4
systems narrative yet.

AgentFlame now has a credible systems mechanism story:

- local LLM semantic control-plane labeling at full-history scale;
- deterministic folded-stack projections and semantic/nonsemantic ablations;
- fixed command-mode exact lineage with negative controls;
- executable but empty user-task and tag-adequacy gates;
- bounded artifact-usability smoke with a verified cached rerun.

It is not OSDI weak accept yet because two reviewer-facing claims remain
unsupported by outcome data:

1. C5 user utility has no participant responses.
2. C6 tag adequacy has no human labels.

The paper can be written as a strong mechanism/measurement-tooling paper only
if those gaps are made explicit. It cannot claim improved developer outcomes or
semantic correctness yet.

R143 adds an independent read-only subagent gate review, recorded in
`docs/visexp/out/osdi-gate-review-r143.md`. The review agrees with this audit:
current maturity is Level 3, weak accept is not yet supported, C5/C6 are
correctly blocked, and the smallest next outcome artifacts are scored R142 pilot
responses and scored R124 human adequacy labels. The review also found a
residual `span flamegraph` matrix label in `EXPERIMENT_PLAN.md`; this pass
renamed it to the explicit `event-count proxy` baseline.

## Claim-Evidence Alignment

| Claim | Evidence status | Result files | Audit decision |
|-------|-----------------|--------------|----------------|
| C1 semantic folded stacks over real histories | supported for this local repository | `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/evaluation.json` | pass |
| C2 local one-word tagging feasibility | supported for available 3B model; partial for 0.6B/1B | `docs/visexp/out/model-benchmarks-r123.json`, `.agentsight/agentflame/latest/agentflame.json` | warn |
| C3 semantic partitioning beyond baselines | supported as mechanism | `docs/visexp/out/semantic-ablation-r131.json`, `.agentsight/agentflame/latest/agentflame.json` | pass |
| C4 exact semantic-effect lineage | supported for fixed 20-task Codex command-mode suite; partial broadly | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | warn |
| C5 developer utility | unsupported | `docs/visexp/out/user-task-preregistration-r142.json`, `docs/visexp/out/user-task-results.json` | fail for outcome claim |
| C6 tag adequacy | partial; syntax/stability only | `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-label-packet-r122.csv`, `docs/visexp/out/tag-adequacy-label-join-r124.json` | fail for adequacy claim |
| C7 open-source usefulness | partial | `docs/visexp/out/artifact-usability-r160.json`: bounded fixed-session smoke passed, with expected artifacts, redacted previews, folded-total checks, generated report path containment, sanitized input manifest `11ae4fb2c96a2d1478aa1525`, clean/cached input equality, and a 76/76 cached rerun | warn |

## Result Integrity Checks

| Check | Evidence | Status |
|-------|----------|--------|
| Full-run scale is not sampled-pipeline scale | `evaluation-summary.md` separates sampled audit scope from full Rust run; headline values come from `.agentsight/agentflame/latest/agentflame.json` | pass |
| Full-run raw traces are not committed | committed artifacts contain redacted previews, hashes, tags, counts, folded stacks, and summaries | pass |
| C3 ablation preserves totals | R131 records preserved system/token totals and folded-file projection matches | pass |
| C4 precision is not raw join rate | R114 reports scoped in-scope precision/recall plus observed negative controls; raw out-of-scope effects remain orphaned | pass |
| C5 empty participant template cannot support utility | `user-task-results.json` is `participant_results_empty`, `c5_supported=false`, `pilot_ready=false` | pass |
| C5 future real response CSV contract is enforced | scorer validates assignments, packets, duplicate rows, partial files, timing, and confidence | pass |
| C6 empty human-label packet cannot support adequacy | R124 is `human_labels_empty`, `adequacy_supported=false` | pass |
| C6 label join path does not fabricate labels | R124-join status is `ready_for_independent_label_collection`, records 0 labeler rows, exposes no joined-label output, and writes an empty adjudication template by default | pass |
| C7 bounded artifact smoke is not a community result | R160 uses 8 fixed historical sessions and records `claim_boundary`; it does not replace fresh-clone install testing or external developer feedback | pass |
| C7 local report privacy boundary | R160 records that `.agentsight/agentflame/*/agentflame.json` is local/private and not public-release-ready because it contains trace roots/session metadata; the committed artifact is the redacted audit JSON | pass |
| C7 write-set scope is not overclaimed | R160 records raw-trace git hygiene and report path containment, but explicitly does not claim full pre/post write-set containment | pass |
| 0.6B/1B small-model claims | no local real 0.6B/1B weights/results currently exist | fail if claimed |

## Reviewer-Risk Ranking

### Must Fix: C5 User Utility

Reviewer concern: semantic flamegraphs may look plausible but not help users
answer real forensic questions.

Concrete fix: run R142 pilot under the frozen C5 preregistration using the
committed participant packets and score the resulting CSV with
`score_user_task_results.py`.

Decision gate: current paper cannot claim utility unless
`claim_analysis.claim_gate.c5_supported=true` for a paper-scale run, or a
narrower expert-pilot claim is explicitly labeled as pilot evidence.

### Must Fix: C6 Human Adequacy

Reviewer concern: one-word tags may be syntactically valid but noisy,
over-specific, or misleading.

Concrete fix: collect human labels with independent blank copies of
`docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`, join frozen labels
with `docs/visexp/r124_join_blinded_labels.py`, adjudicate disagreements using
`docs/visexp/out/tag-adequacy-adjudication-template-r124.csv`, then rerun
`score_tag_adequacy.py` on
`docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv`.

Decision gate: adequacy claim requires >=80% adequate labels, <=20%
generic/noisy labels, and agreement/adjudication evidence. If labels fail,
paper wording must call tags lossy navigation hints.

### Should Fix: RQ6 Artifact Usability

Reviewer concern: the project may be a one-off local analysis rather than a
community developer tool.

Current status: R160 now passes as a bounded fixed-session local smoke. It
connects to a llama.cpp-compatible server, writes
`.agentsight/agentflame/r160-smoke-fixed`, verifies expected outputs with
`artifact_usability_r160.py`, records clean/cached runtime behavior, records a
sanitized fixed-input manifest, checks clean/cached input equality, and proves
that a fixed-input rerun is fully cached.

Remaining concrete fix: run a fresh-clone or clean-install smoke with public
setup instructions, choose a stable default sampling mode, and collect feedback
from external developers. The failed 36-session cached attempt is informative:
dynamic discovery can see new live Codex session fragments between runs, so
cache experiments must pin `--session-file` inputs. A future release artifact
also needs sanitized public reports and a real pre/post write-set audit if it
wants to claim no writes outside the output directory.

Decision gate: needed for artifact strength and open-source positioning, but
not a substitute for C5/C6 evidence.

## Claim Wording Boundary

Allowed:

- AgentFlame emits semantic folded-stack artifacts over real local Codex/Claude
  histories for this repository.
- A local 3B llama.cpp model can produce syntactically valid one-word tags at
  this full-history scale, with R123 showing 900/900 valid tags and 95.000%
  identical-fragment stability on a 300-fragment redacted sample.
- Semantic frames partition system-effect buckets that nonsemantic folded
  stacks and flat summaries merge in this local workload.
- R114 validates exact semantic-effect lineage for a fixed 20-task Codex
  command-mode suite with 100.0% precision/recall and 0/3170
  negative-control effects attributed.
- R160 verifies an auditable bounded local artifact path with fixed historical
  sessions, a sanitized input manifest, expected output files, redacted
  previews, and a fully cached rerun.

Disallowed:

- AgentFlame proves developers debug faster or more accurately.
- One-word tags are semantically correct.
- AgentSight/AgentFlame has complete exact provenance for arbitrary
  full-history traces.
- AgentFlame is already validated as a community developer tool.
- AgentFlame is novel because it is a flamegraph for agents.

## Next Tracker Rows

| Run ID | Claim | Purpose | Command/config | Seed/reps | Oracle | Decision gate | Result path | Status |
|--------|-------|---------|----------------|-----------|--------|---------------|-------------|--------|
| R124-labels | C6 | Human adequacy labeling for one-word tags. | collect labels over independent copies of `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`; join frozen labels with `python3 docs/visexp/r124_join_blinded_labels.py --labeler-1 ... --labeler-2 ... --adjudication ...`; rerun `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r124-joined.csv --out-json docs/visexp/out/tag-adequacy-results-r124.json --out-csv docs/visexp/out/tag-adequacy-results-r124.csv --out-md docs/visexp/out/tag-adequacy-results-r124.md` | 300 fragments, >=2 labelers preferred | adequate/generic-noisy/misleading rubric plus agreement/adjudication | >=80% adequate, <=20% generic/noisy, <=5% misleading, kappa >=0.6 or narrowed wording | `docs/visexp/out/tag-adequacy-results-r124.json` | planned |
| R142-pilot | C5 | Pilot developer forensic task benchmark. | using the frozen preregistration in `docs/visexp/out/user-task-preregistration-r142.json`, fill a pilot copy of `docs/visexp/out/user-task-response-template.csv` with real participant responses; rerun `python3 docs/visexp/score_user_task_results.py --responses <pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --assignments docs/visexp/out/user-task-assignments.csv --out docs/visexp/out/user-task-pilot-r142` | 5 participants for complete condition coverage | hidden answer key, timing, false positives, confidence, response-contract checker, prereg source-hash lock | pilot only; protocol must work before paper-scale C5 claim | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` | planned |
| R160 | C7 | Bounded fixed-session open-source usability smoke. | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke-fixed --session-file <8 fixed historical Codex sessions>`; repeat same command; verify with `artifact_usability_r160.py` and clean-run report. | 8 fixed historical Codex sessions; one clean run plus cached rerun | expected files, runtime/cache summary, fully cached rerun, sanitized input manifest, clean/cached input equality, no raw-trace git dirt, generated report path containment | bounded local artifact path is audited; fresh-clone/community claim still open | `docs/visexp/out/artifact-usability-r160.json` | done/bounded |
