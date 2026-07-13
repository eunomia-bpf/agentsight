# AgentProcessBench source, protocol, and baseline screen

**Recorded:** 2026-07-13T04:45:00-07:00  
**Outer gate:** EXPERIMENT  
**Skill:** `research-literature-novelty`  
**Research question held fixed:** RQ2 — Does Profiler Output Correspond to
Real Problems?  
**Decision:** suitable for a complete external RQ2 experiment plan; do not
change the paper, thesis, hypothesis, or four-RQ architecture at this node

## Why this source is worth a full experiment

AgentProcessBench is a materially stronger source for the current RQ2 evidence
search than another home-written microbenchmark. It is a KDD 2026 benchmark
whose exact scientific purpose is diagnosing step-level process quality in
realistic tool-using agent trajectories. It supplies complete trajectories,
tool schemas and returns, and consensus human labels for every assistant step.
Its published FirstErrAcc metric directly treats localization of the first
critical error as distinct from generic step classification.

The benchmark therefore lets AgentProf answer the original, larger question:
whether a cross-run semantic profile can concentrate real human-annotated
problems into inspectable recurring groups. It does not ask whether a toy
classifier can recognize a synthetic fault.

## Primary sources and identities

1. **Peer-reviewed paper:** Shengda Fan et al., “AgentProcessBench:
   Diagnosing Step-Level Process Quality in Tool-Using Agents,” KDD 2026,
   DOI `10.1145/3770855.3817494`, arXiv `2603.14465v2`.
   - Official page: <https://rucbm.github.io/AgentProcessBench-Homepage/>
   - Paper: <https://arxiv.org/abs/2603.14465>
   - Locally inspected PDF SHA-256:
     `b81148ad9bfe63a86117951cdb7149670a966bbc3a40bfc4ffaac45805a48eb6`
2. **Official code/data repository:**
   <https://github.com/RUCBM/AgentProcessBench>
   - inspected commit:
     `0a42606b178a8c69d40c5765dc05c342f921e578`
   - the repository has no numbered release; the commit is therefore the
     concrete source identity for this experiment.
3. **Official Hugging Face dataset:**
   <https://huggingface.co/datasets/LulaCola/AgentProcessBench>
   - inspected repository revision:
     `cd81f326aece8b0a3f6359e20df370690d3a98bf`
   - the published data card identifies the same four subsets and links the
     same paper.

The GitHub files are the local execution source because they include the
official evaluation code and annotation guide beside the data. The 80 MB
checkout and downloaded PDF are local inputs under
`docs/visexp/out/agentprocessbench-rq2/` and are intentionally ignored rather
than committed as repository blobs.

## Complete population

The release has 200 unique tasks and five generated trajectories for each
task, for 1,000 trajectories and 8,509 assistant steps. All four family files
contain exactly 250 trajectories, 50 query IDs, and sample indices 0–4.

| Family | Trajectories | Unique tasks | Assistant steps | Steps with tool calls | Steps without tool calls | File SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| BFCL | 250 | 50 | 2,590 | 1,459 | 1,131 | `6aee0b71eff7feb872c6b54d962f8831b56f7bebf770cba9cb657f219afb6fe5` |
| GAIA dev | 250 | 50 | 1,628 | 1,269 | 359 | `f7b75c668fc1e6ad943e8f6d93a21a9a8f5f076841e1230e1ed2fc6d05ce8192` |
| HotpotQA | 250 | 50 | 734 | 456 | 278 | `160eef2ded872d8dc6ddf4cee5752295fda691b6a9e99b5bafc2d484e6309c57` |
| tau2 | 250 | 50 | 3,557 | 1,880 | 1,677 | `6f22818ff88822512767fe735f56e7b78bed4b9aaf26959144feb92f127e1e95` |
| **Total** | **1,000** | **200** | **8,509** | **5,064** | **3,445** | — |

The count of `step_labels` keys equals the count of assistant messages in each
family. No trajectory or step needs to be sampled away. The full experiment
should process all 1,000 trajectories and all 8,509 steps.

The five rollout generators reported by the paper are
Qwen3-4B-Instruct-2507, Qwen3-30B-A3B-Instruct-2507, DeepSeek-V3.2,
GPT-5-mini, and GPT-5. The public JSONL exposes `sample_index` 0–4 but does not
reliably identify which index maps to which model. The experiment must not
guess this mapping and does not need model identity for its primary analysis.

## Published task and annotation protocol

The source trajectories are drawn from four established agent benchmarks:

- HotpotQA: multi-hop retrieval and reasoning;
- GAIA: open-world retrieval, browsing, and local-file work;
- BFCL: multi-turn function composition in stateful tool environments;
- tau2: policy-constrained business-process interaction.

The paper preserves all five model trajectories for each selected task and
uses the task-specific tool environment from the originating benchmark. It
selects equal numbers of tasks from each family, using E5 representations to
favor diverse tasks rather than a convenient error-only slice.

One scorable step is exactly one `role="assistant"` message, even when that
message contains multiple tool calls. Every such step receives one of three
labels:

- `+1`: correct and effective;
- `0`: neutral or exploratory;
- `-1`: incorrect or harmful.

The error-propagation rule labels later steps `-1` while they remain causally
dependent on an earlier error, but permits recovery after explicit correction
or an independent new subtask. This makes an earliest harmful step especially
important and makes a first-error metric necessary alongside pooled step
localization.

Each trajectory was independently reviewed by two qualified annotators;
disagreements were resolved by discussion. The paper reports 89.1% step-level
agreement and Cohen's kappa 0.767. It also reports that final human labels
agree with the three auxiliary LLM suggestions only 66.9%–72.1%, evidence that
the released labels are not merely copied judge-model outputs.

## Published metrics and baselines to reuse

The official evaluation defines:

1. **StepAcc:** micro-averaged agreement over every assistant step.
2. **FirstErrAcc:** exact agreement on the index of the first `-1` step in a
   trajectory; a trajectory with no `-1` is correct only when the prediction
   also contains no `-1`.

The paper evaluates 20 API and open-source judge models with these metrics.
The strongest reported average result, Gemini-3-Flash-Preview-Thinking,
obtains 81.6% StepAcc but only 65.8% FirstErrAcc. This published gap supports
the premise that root-error localization is harder than recognizing downstream
bad steps.

### Released blind judge predictions

The official repository also releases the actual blind step predictions used
for Table 3 under `eval/results/`: four complete JSONL files for each of all 20
evaluated judge models. Every model directory contains 1,000 aligned trajectory
records, and every one of the 8,509 official assistant-step keys occurs once
for every model. The files identify themselves as blind evaluation outputs and
were produced by the repository's published judge prompt and evaluator.

Some API or parse failures are represented by `null`, not a fabricated label.
Across models, 6,914 steps have all 20 non-null predictions. Of the remaining
steps, all but three still have at least 15 non-null predictions. The same
three-step GAIA trajectory `(query_index=19, sample_index=4)` is null for all 20
models. These are source-availability facts; no human target label is involved.

This release provides a cleaner target-label-blind risk signal than fitting a
new classifier from the same fields being evaluated. A fixed ensemble risk can
be defined as the fraction of available official judge predictions equal to
`-1`; the three all-null steps receive a predeclared uninformative value of
0.5. This uses every trajectory, avoids target-label training, does not
cherry-pick one judge, and imports a large external variable into the profiling
test. Independent plan review must decide whether to adopt this signal before
implementation.

For AgentProf, the published metrics should be retained where their semantics
fit, but classification accuracy alone is insufficient. The experiment plan
should also retain the paper's existing RQ2 inspection metrics:
operation-weighted AP, recall at a fixed inspection budget, work to recover a
fixed share of harmful steps, and group count. These measure whether a profile
organizes the same predictions into useful cross-run diagnostic groups.

The mandatory non-oracle comparators are:

- flat summary;
- per-trajectory/session grouping;
- raw action/target/repetition grouping;
- individual-step risk ranking;
- the tested semantic operation stack.

Hidden human labels may score results. If a plan uses reference-family
training, they may train only the explicitly declared reference-family
predictor; the preferred released-ensemble design requires no human-label
training at all. Human labels may not define stack fields, intent tags, ranking
rules, thresholds, or comparator choice.

## Proposed scientific use, before plan review

The plan tests one decisive construction-level hypothesis and keeps RQ2 fixed:

> Across the complete four-family AgentProcessBench population, a target-preserving
> semantic operation stack built from intent, workflow phase, action, target,
> and repetition will localize human-annotated harmful steps more effectively
> and with less inspection work than raw-action and per-session profiles under
> the same target-label-blind risk signal.

This construction directly repairs the diagnosed AgentNet defect. The raw
leaf information `action → target → repeat_state` remains intact; semantic
context is a refinement rather than a replacement. Candidate intent tags come
from AgentProf's existing label-blind TF-IDF/K-Means prompt tagger over the 200
unique task descriptions. Candidate phase tags come only from visible message
and tool-interaction structure. Neither source uses human labels.

Revision 1 proposed four leave-one-family-out fitted predictors. Independent
review rejected that choice because the predictor used the same semantic fields
that defined the tested stack. The approved direction instead uses the one
fixed released 20-model blind-consensus risk described above, with human labels
read only by the final scorer. The four families remain complete result strata.
Bootstrap clusters are original query IDs so the five rollouts for one task
remain dependent. Exact stack fields, the group-size-matched shuffled control,
metrics, and verdict belong in the approved experiment plan rather than being
improvised during execution.

## Label-exposure incident and consequence

During source screening, an `rg` command intended to find model-name metadata
was scoped too broadly and printed part of `data/AnswerOnly/*.jsonl`, including
some HotpotQA and tau2 per-row label values. No label distribution, group
metric, threshold, model mapping, or candidate-stack result was calculated
from those values. The target-preserving construction, leave-one-family-out
direction, and candidate fields had already been selected from the AgentNet
mechanism diagnosis and the published schema.

This is recorded rather than hidden. The plan cannot describe the benchmark as
a pristine never-viewed target. It can still provide a valid predeclared
external test if all design choices are fixed now, the implementation never
uses human labels before scoring, no result-driven revision occurs, and the
independent plan reviewers accept the residual exposure risk. If reviewers
judge that standard too weak, AgentProcessBench remains a complete development
benchmark and the same fixed construction must be tested on a new external
source; the paper story and RQ2 do not change.

## Known limitations that do not narrow the research question

- The source is text-only tool use; it does not cover multimodal GUI
  trajectories.
- The 1,000 trajectories are benchmark rollouts, not production telemetry.
- Error propagation makes pooled harmful-step counts partly dependent on an
  earlier mistake, so FirstErrAcc must accompany operation-level AP.
- Family-specific tool vocabularies create a real distribution shift. Report
  all four complete family strata separately rather than hiding a difficult
  family inside the macro result.
- Rollout model identity is not recoverable from the released row schema and
  will not be invented.

These limits affect interpretation and future breadth. They do not authorize
changing the thesis, replacing RQ2, shrinking the positive hypothesis, or
putting negative development outcomes into the paper.

## Transition

Proceed to an ordinary Markdown experiment plan:

```text
PROPOSE
→ at least three serial independent REVIEW rounds
→ REAL PREFLIGHT
→ complete FULL RUN
→ independent RESULT REVIEW
```

Do not implement or score before the plan converges. The active paper remains
the exact attachment/submodule scientific body in the AAAI workspace.
