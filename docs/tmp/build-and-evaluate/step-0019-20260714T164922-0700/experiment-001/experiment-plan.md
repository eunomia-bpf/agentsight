# Experiment Plan: RQ2 Fixed-Reader Problem Prioritization

## Research Question

- **RQ exactly as written in the paper:** RQ2: Does profiler output correspond
  to real problems?
- **Specific uncertainty tested here:** Under the same rank-hidden packet and
  three-group selection budget, does one fixed deterministic LLM reader recover
  more independently hidden problem-bearing operations from operation-stack
  profiles than from execution-local fixed-session profiles?
- **Why the answer matters:** Existing RQ2 experiments score concentration and
  inspection curves, but a skeptical reviewer can still argue that the groups
  do not help an actual diagnostic decision. This experiment directly tests
  one bounded decision without changing the RQ, profile construction, or
  benchmark population.

## Paper-Value Admission

- **Planned role:** decisive within the disputed RQ2 evidence chain.
- **Largest credible paper story this experiment could unlock:** AgentProf's
  recurring operation-stack view not only concentrates hidden problem labels;
  it helps a fixed AI reader prioritize problem-bearing groups better than an
  execution-local view under the same inspection budget.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:**
  Current AP/work curves may reflect a scorer and grouping granularity rather
  than downstream diagnostic usefulness.
- **Independent evidence added beyond existing runs and published results:** The
  same frozen reader makes rank-hidden selections on paired operation-stack and
  fixed-session packets under a position-balanced presentation; hidden labels
  are read only after all selections are collected.
- **Why the result is not tautological, already settled, or dominated:** The
  existing R316 control merely takes the first visible groups. It does not test
  whether a reader can use group content after rank is removed. AgentRx and
  AgentDiagnose establish the importance of structured trajectory diagnosis but
  do not compare these views on this population.
- **Paper decision if positive:** Add bounded fixed-reader evidence to RQ2 and
  use it to support the claim that recurring profiles improve one downstream
  prioritization decision. Do not claim human productivity, remediation, or
  universal view dominance.
- **Paper decision if contradictory, mixed, or inconclusive:** Keep the fixed
  positive RQ2 hypothesis, record that this packet/reader construction is
  insufficient, and route to a stronger profile signal or independently
  grounded decision protocol. Do not change RQ2 or the thesis.
- **Best alternative experiment and why this one has higher decision value:** A
  new annotated RQ3 dataset could confirm another tag component, but the latest
  whole-paper review identifies downstream RQ2 usefulness as the stronger
  acceptance risk. A NeMo matched replay is not currently fair because NeMo's
  profiler instruments its own workflows rather than importing these traces.

## Expected And Alternative Outcomes

- **Current expected answer:** The operation-stack reader has positive median
  paired recall and precision deltas and improves each on at least four of six
  tasks relative to the fixed-session reader.
- **Strongest competing explanation:** Existing query-aware order, group size,
  or the reader alone explains apparent gains; after order hiding, fixed-session
  content is equally or more useful.
- **Result that would contradict the expectation:** Neither recall nor precision
  meets its complete positive-median-plus-four-task condition after
  position-balanced within-task aggregation.
- **Paper-impact boundary:** A contradiction bounds the tested packet and fixed
  reader. It is not a direct challenge to the necessary paper-level thesis that
  agent observability needs profiling.

## Published Precedent And Real Assets

- **Closest published protocol:** AgentRx uses an LLM judge over structured
  trajectory evidence to localize critical failure steps; AgentDiagnose connects
  trajectory diagnostics to externally evaluated downstream selection.
- **Order-bias precedent:** Shi et al., IJCNLP-AACL 2025, show material position
  bias in list-wise LLM judging, motivating removal of existing rank and ordinal
  cues.
- **Official system/model/data/benchmark/tool and version:** Existing R315
  packets cover six tasks from Agent Reward Bench, SATraj OS Safety, AgentNet,
  and OSWorld-Human. The reader is the already running local
  `Qwen3.6-27B-Q4_K_M` model through llama.cpp's OpenAI-compatible API.
- **What is reused:** All 18 unique R315 task-view packets, the existing hidden
  scoring key, the R316 top-three visible-order control, and the local model
  endpoint. The twelve non-flat packets are each presented in five fixed cyclic
  rotations; the six one-group flat packets need one presentation each.
- **Necessary deviations or custom glue:** One small Python adapter removes
  rank/view/original-ID cues, invokes the reader, validates aliases, and scores
  locked responses. No dataset, profile, tag, ranking signal, label, metric, or
  benchmark is created.

## Comparison

- **Proposed system or method:** The fixed reader on six operation-stack
  packets, one per task.
- **Main baseline and competing position:** The identical reader on six
  fixed-session packets. It represents the directly matched claim that
  execution-local organization is sufficient for prioritization.
- **Why the main baseline needs a matched run instead of citation alone:** The
  response depends on this reader, prompt, packet content, and task; no paper
  reports the paired result.
- **Controls:** The six flat packets are a non-selective lower bound. The
  existing R316 visible-order top-three results are an existing-ranker control,
  deduplicated to one row per packet rather than treating 144 assignment rows
  as observations. The five cyclic presentations provide the position-bias
  control for the new reader; R316 is not used for that purpose.
- **Conclusion if the main baseline matches or wins:** The tested
  operation-stack packet does not improve this downstream reader decision even
  if its static concentration metrics are favorable.
- **Information, tuning, and compute fairness:** Both non-flat views expose five
  groups, use the same visible field categories, prompt, opaque aliases, five
  cyclic positions per packet, model, decoding, and exactly-three-group budget.
  Every group appears once in every prompt position. The hidden key is absent
  during collection. No prompt, threshold, model, metric, task, packet, base
  order, or rotation is selected from results.
- **Raw-action boundary:** Existing six-task static evidence keeps raw action as
  a paper-level counterpoint. No matched R315 raw-action packet exists, so this
  run cannot support superiority to raw action or universal view dominance.

## Workloads And Metrics

- **Real workloads or tasks:** Six complete R315 tasks from four public dataset
  families; three views per task; 18 unique packets and 66 fixed presentations
  (12 non-flat packets x five rotations plus six flat packets). The 144
  human-assignment rows are not independent LLM cases and are not executed.
- **Primary metrics:** Selected-positive operation recall and selected-positive
  operation precision at exactly three groups, paired by task between
  operation-stack and fixed-session.
- **Correctness check or ground truth:** Existing hidden R315 per-group positive
  operation counts; only the score phase reads them.
- **Secondary outcomes:** Inspected operation work fraction, positive lift,
  any-positive hit, high-lift hit, and the existing visible-order control.
- **Repetitions, seeds, and uncertainty:** One deterministic response per fixed
  presentation at temperature zero and seed `20260714`. For each non-flat
  task/view, average metrics across its five rotations before computing the
  operation-stack-minus-fixed-session task delta. The six tasks remain the
  paired scientific units; report every task delta, median delta, and
  win/tie/loss count. No p-value or bootstrap generalization claim is made from
  six tasks.
- **Cost estimate:** 66 local calls over the same small tracked packets, plus one
  score pass; no monetary API cost. The unique tracked packet payloads are
  3.4--14.7 KB each (189 KB total before rotations).

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | path check | `satraj_unsafe::operation_stack` | rank-hidden Qwen3.6 reader | all 5 rotations | Proves the real endpoint, balanced presentation, response, and artifact path only. |
| main | proposed | six operation-stack packets | rank-hidden Qwen3.6 reader | 5 rotations per packet | Paired RQ2 candidate evidence after within-task aggregation. |
| main | baseline | six fixed-session packets | identical rank-hidden Qwen3.6 reader | 5 rotations per packet | Tests execution-local competing position after the same aggregation. |
| control | lower bound | six flat packets | identical Qwen3.6 reader selecting the sole group | 1 per packet | Reports completeness without selectivity. |
| control | existing ranker | 18 R316 packet rows after deterministic deduplication | visible-order top three | existing | Separates reader content use from the prior ranker; it is not the position-bias control. |

## Reader Presentation And Fixed Protocol

For each non-flat packet, collection retains the natural-language problem and
existing visible group summaries, removes the view label and rank field, and
defines one hidden-key-blind base order by sorting the five original
12-hex-character group IDs lexicographically. It then emits all five cyclic
rotations of that base order. Thus every visible group occupies each prompt
position exactly once. After each rotation is fixed, the collector replaces
original IDs with fresh sequential opaque aliases `G01`--`G05` and exposes only
those aliases. A flat packet has one presentation and one alias.

The serialized model request is constructed from an explicit allowlist:
natural-language problem, opaque alias, operation/session counts, stack text
and frames, visible feature summaries, field examples, and operation/session
examples. It excludes `packet_id`, `view`, `ranker`, `response_prompt`, `rank`,
original `group_id`, the alias-to-original-ID map, and every hidden-key field.
The alias map remains only in the surrounding collection record used later by
scoring.

The running server configuration observed at plan time is:

```text
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server
-m /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf
--alias qwen3.6-27b --host 127.0.0.1 --port 8012 --ctx-size 65536
--parallel 1 --n-gpu-layers 99 --cache-type-k q8_0 --cache-type-v q8_0
--jinja --reasoning off --reasoning-budget 0
```

Requests use endpoint `http://127.0.0.1:8012/v1`, API model ID
`qwen3.6-27b`, temperature `0`, seed `20260714`, maximum 1024 output tokens,
and `chat_template_kwargs={"enable_thinking": false}`. A non-flat response
must return exactly three distinct valid aliases ordered by diagnostic
priority, plus a short visible-field rationale; flat returns its sole alias.
During the full run, at most three identical requests are permitted for a
transport, JSON, or schema failure. Retries are repairs, never observations. A
presentation still invalid after the attempt limit makes the complete matrix
invalid; no cell is dropped, imputed, or manually repaired.

## Execution

- **Adapter:** `script/r315_llm_reader_eval.py`
- **Authoritative collection workflow:** `collect` reads only visible packets,
  calls the model, validates aliases, and writes raw requests/responses.
- **Authoritative scoring workflow:** `score` reads the completed response file,
  hidden key, and existing R316 CSV; it performs no model call.
- **Real preflight case:** all five rotations of
  `satraj_unsafe::operation_stack` in a separate preflight directory. One
  command is one real preflight attempt; at most two attempts are allowed. The
  preflight command permits at most two identical requests per presentation.
- **Full completion rule:** All 66 fixed presentations produce valid responses
  under the fixed protocol, then the score pass emits presentation-level,
  task/view-aggregated, and paired-task rows.
- **Raw-result path:**
  `.agentsight/experiments/r315-llm-reader-rq2-v2/{preflight,full}/`
- **Checkpoint or recovery approach:** Collection appends one complete raw JSONL
  record per presentation and safely resumes only missing presentations with
  the same command. The full score is recomputed from the complete 66-row
  response file.

Planned commands are:

```bash
python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 --model qwen3.6-27b \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/preflight \
  --packet-id satraj_unsafe::operation_stack \
  --order-scheme cyclic-5 \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 2

python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 --model qwen3.6-27b \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/full \
  --order-scheme cyclic-5 \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 3

python3 script/r315_llm_reader_eval.py score \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --hidden-key docs/visexp/out/analyst-study-protocol-r315/hidden-scoring-key.json \
  --ranker-scores docs/visexp/out/analyst-study-readout-r316/trial-scores.csv \
  --responses .agentsight/experiments/r315-llm-reader-rq2-v2/full/responses.jsonl \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/full
```

## Interpretation

- Define one primary metric as **passing** only when its median paired delta is
  positive and it improves on at least four of six tasks after the five
  rotations are averaged within each task/view.
- **Supported:** Both recall and precision pass.
- **Mixed:** Exactly one of recall and precision passes.
- **Contradicted:** Neither recall nor precision passes.
- **Invalid:** The real path or complete 66-presentation matrix cannot finish under the
  fixed protocol.
- **Target paper figure or table:** One six-row paired task table with recall,
  precision, and work for operation-stack and fixed-session, plus a compact
  aggregate row and clearly labeled flat/order controls.

## Reproducibility Notes

- **Software and data versions:** Current tracked R315/R316 artifacts; the
  observed llama.cpp server and GGUF path above; API model ID
  `qwen3.6-27b`.
- **Config and seed notes:** Temperature zero, seed `20260714`, reasoning off,
  maximum 1024 output tokens, five fixed cyclic presentations for every
  non-flat packet, and one presentation for every flat packet.
- **Known deviations:** This is a fixed AI-reader study rather than the original
  24-participant human R315 design. It uses 66 deterministic presentations of
  18 unique packets rather than 144 repeated assignment rows. Original rank is
  hidden and position is balanced, unlike the human-facing R315 presentation.
  One reader and six tasks limit generalization.
