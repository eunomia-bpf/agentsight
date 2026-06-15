# AgentFlame Experiment Audit

Last updated: 2026-06-15
Stage at update: audit / supplement
Source/command: OSDI rubric audit over `docs/visexp/STATE.md`, `docs/visexp/CLAIM_VERDICT.md`, `docs/visexp/out/evaluation.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/model-benchmarks-r123.json`, `docs/visexp/out/tag-adequacy-results-r124.json`, and `docs/visexp/out/user-task-results.json`
Completeness: partial

## Audit Verdict

Current maturity: Level 3 conference-paper mechanism evidence, not Level 4
systems narrative yet.

AgentFlame now has a credible systems mechanism story:

- local LLM semantic control-plane labeling at full-history scale;
- deterministic folded-stack projections and semantic/nonsemantic ablations;
- fixed command-mode exact lineage with negative controls;
- executable but empty user-task and tag-adequacy gates.

It is not OSDI weak accept yet because two reviewer-facing claims remain
unsupported by outcome data:

1. C5 user utility has no participant responses.
2. C6 tag adequacy has no human labels.

The paper can be written as a strong mechanism/measurement-tooling paper only
if those gaps are made explicit. It cannot claim improved developer outcomes or
semantic correctness yet.

## Claim-Evidence Alignment

| Claim | Evidence status | Result files | Audit decision |
|-------|-----------------|--------------|----------------|
| C1 semantic folded stacks over real histories | supported for this local repository | `.agentsight/agentflame/latest/agentflame.json`, `docs/visexp/out/evaluation.json` | pass |
| C2 local one-word tagging feasibility | supported for available 3B model; partial for 0.6B/1B | `docs/visexp/out/model-benchmarks-r123.json`, `.agentsight/agentflame/latest/agentflame.json` | warn |
| C3 semantic partitioning beyond baselines | supported as mechanism | `docs/visexp/out/semantic-ablation-r131.json`, `.agentsight/agentflame/latest/agentflame.json` | pass |
| C4 exact semantic-effect lineage | supported for fixed 20-task Codex command-mode suite; partial broadly | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | warn |
| C5 developer utility | unsupported | `docs/visexp/out/user-task-results.json` | fail for outcome claim |
| C6 tag adequacy | partial; syntax/stability only | `docs/visexp/out/tag-adequacy-results-r124.json`, `docs/visexp/out/tag-adequacy-label-packet-r122.csv` | fail for adequacy claim |
| C7 open-source usefulness | partial | generated CLI/dashboard artifacts and `artifact_usability_r160.py` verifier; no committed fresh-clone smoke | warn |

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
| 0.6B/1B small-model claims | no local real 0.6B/1B weights/results currently exist | fail if claimed |

## Reviewer-Risk Ranking

### Must Fix: C5 User Utility

Reviewer concern: semantic flamegraphs may look plausible but not help users
answer real forensic questions.

Concrete fix: run R142 pilot using the committed participant packets and score
the resulting CSV with `score_user_task_results.py`.

Decision gate: current paper cannot claim utility unless
`claim_analysis.claim_gate.c5_supported=true` for a paper-scale run, or a
narrower expert-pilot claim is explicitly labeled as pilot evidence.

### Must Fix: C6 Human Adequacy

Reviewer concern: one-word tags may be syntactically valid but noisy,
over-specific, or misleading.

Concrete fix: collect human labels for R122/R124 packet rows using the
adequate/generic-noisy/misleading rubric, then rerun
`score_tag_adequacy.py`.

Decision gate: adequacy claim requires >=80% adequate labels, <=20%
generic/noisy labels, and agreement/adjudication evidence. If labels fail,
paper wording must call tags lossy navigation hints.

### Should Fix: RQ6 Artifact Usability

Reviewer concern: the project may be a one-off local analysis rather than a
community developer tool.

Concrete fix: run R160 as a fresh-clone or clean-worktree smoke using the
documented CLI command, connect to a llama.cpp-compatible server, write
`.agentsight/agentflame/r160-smoke`, verify expected outputs with
`artifact_usability_r160.py`, and record runtime/cache behavior.

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

Disallowed:

- AgentFlame proves developers debug faster or more accurately.
- One-word tags are semantically correct.
- AgentSight/AgentFlame has complete exact provenance for arbitrary
  full-history traces.
- AgentFlame is novel because it is a flamegraph for agents.

## Next Tracker Rows

| Run ID | Claim | Purpose | Command/config | Seed/reps | Oracle | Decision gate | Result path | Status |
|--------|-------|---------|----------------|-----------|--------|---------------|-------------|--------|
| R124-labels | C6 | Human adequacy labeling for one-word tags. | collect labels over `docs/visexp/out/tag-adequacy-label-packet-r122.csv`; rerun `python3 docs/visexp/score_tag_adequacy.py --labels docs/visexp/out/tag-adequacy-label-packet-r122.csv --out-json docs/visexp/out/tag-adequacy-results-r124.json --out-csv docs/visexp/out/tag-adequacy-results-r124.csv --out-md docs/visexp/out/tag-adequacy-results-r124.md` | 300 fragments, >=2 labelers preferred | adequate/generic-noisy/misleading rubric plus agreement/adjudication | >=80% adequate, <=20% generic/noisy, kappa >=0.6 or narrowed wording | `docs/visexp/out/tag-adequacy-results-r124.json` | planned |
| R142-pilot | C5 | Pilot developer forensic task benchmark. | fill a pilot copy of `docs/visexp/out/user-task-response-template.csv` with real participant responses; rerun `python3 docs/visexp/score_user_task_results.py --responses <pilot-response.csv> --bundle docs/visexp/out/user-task-benchmark.json --answer-key docs/visexp/out/user-task-answer-key.csv --out docs/visexp/out/user-task-pilot-r142` | 5 participants for complete condition coverage | hidden answer key, timing, false positives, confidence, response-contract checker | pilot only; protocol must work before paper-scale C5 claim | `docs/visexp/out/user-task-pilot-r142/user-task-results.json` | planned |
| R160 | C7 | Fresh-clone/open-source usability smoke. | `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/r160-smoke`; then `python3 docs/visexp/artifact_usability_r160.py --agentflame-dir .agentsight/agentflame/r160-smoke --out docs/visexp/out/artifact-usability-r160.json` | one clean run plus cached rerun | expected files, runtime/cache summary, no raw-trace commit, no writes outside output dir | project can be evaluated as a community tool artifact | `docs/visexp/out/artifact-usability-r160.json` | planned; verifier script exists and passed on existing `.agentsight/agentflame/latest` output only |
