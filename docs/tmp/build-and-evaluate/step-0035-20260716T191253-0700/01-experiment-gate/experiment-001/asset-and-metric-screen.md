# RQ1 Existing-Asset And Standard-Metric Screen

**Completed:** 2026-07-16T19:55:22-07:00

**State:** `EXPERIMENT_GATE / PAPER-VALUE ADMISSION AND EXISTING-ASSET SCREEN`

**Decision:** **ADMIT ONE REUSE-ONLY EXPERIMENT PLAN.** The already-downloaded,
already-executed CodeTraceBench source-valid target population contains an
independent human stage partition and real per-call token usage for every one
of its 405 trajectories. No new agent run, new dataset, new operation-stack
algorithm, or invented label is necessary.

## Fixed Research Question And Scope

This screen serves the author-fixed question:

> **RQ1 — Does Semantic Profiling Improve Resource Attribution?**

It does not change the fixed thesis, any RQ, or the current Step 0024 recurrence
operation-stack constructor. It asks whether the current semantic partition
assigns *observed resource mass* to independently defined human stages more
faithfully than non-semantic views on exactly the same operations.

The measured resource is provider-reported LLM token consumption. The primary
weight is `total_tokens = prompt_tokens + completion_tokens`. This is a real
consumption measurement attached to the call that produced an observed agent
operation; it is not a score derived from the proposed partition. Calls that
produced no benchmark operation are outside the official operation/stage
population and are not silently attached to an arbitrary stage.

## Why CodeTraceBench Is Admissible

The official [CodeTraceBench dataset](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench)
contains heterogeneous real trajectories from four agent frameworks and human-
verified step/stage annotations. The accompanying
[CodeTracer paper](https://arxiv.org/abs/2604.11641) describes stage- and
step-level supervision for failure localization. The local target is the same
complete pre-existing source-valid target population fixed in Steps
0022--0030, before this token analysis:

- 405 trajectories from OpenHands, mini-SWE-agent, SWE-agent, and Terminus2;
- 20,866 official operations;
- 2,948 human-verified contiguous stage intervals;
- 87,703 operations from 2,229 disjoint solved/reference trajectories used by
  the unchanged recurrence constructor;
- current operation-stack assignments already materialized in
  `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/operation-assignments.jsonl`.

The verified manifest contains 468 failed trajectories. The existing target
includes 405/468 and excludes 63 whose released source did not satisfy the
earlier source-valid operation contract. This experiment does not revisit that
selection or reconstruct excluded runs:

| Population | Sessions | Distinct tasks | OpenHands | Terminus2 | mini-SWE-agent | SWE-agent | Operations/steps | Median per session | Range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| included source-valid target | 405 | 251 | 213 | 93 | 71 | 28 | 20,866 | 39 | 20--275 |
| excluded from the pre-existing target | 63 | 51 | 19 | 31 | 13 | 0 | 4,107 | 47 | 20--327 |

The result therefore describes the complete 405-trajectory source-valid target
population, not every failed trajectory in the release.

The human stage partition is independent of AgentProf's phase, action, raw-
action, recurrence, and profile outputs. It therefore avoids the circularity of
scoring a grouping label against the same label that created the grouping.

## Complete Token-Recovery Screen

The local source cache contains all 3,291 official raw archives (438 MiB
compressed). A read-only source screen traced each target operation back to the
provider response that produced it. The result is complete coverage:

| Framework/source form | Sessions | Operations | Alignment source |
|---|---:|---:|---|
| OpenHands native events | 118 | 6,454 | `tool_call_metadata.model_response.usage` on the chronological agent event |
| OpenHands SWE raw | 95 | 3,576 | response `usage` and tool-call identity in the selected complete request/response history |
| mini-SWE-agent native | 47 | 1,590 | assistant message `extra.response.usage` |
| mini-SWE-agent SWE raw | 24 | 585 | assistant message `extra.response.usage` |
| SWE-agent | 28 | 1,460 | final trajectory tool-call IDs joined to `ModelResponse ... usage=Usage(...)` in the released debug log |
| Terminus2 | 93 | 7,201 | official string commands joined, in order, to response `keystrokes` and `original_response.usage` |
| **Total** | **405** | **20,866** | **complete source-valid target population** |

The two apparent format problems were resolved from released evidence rather
than by excluding sessions:

1. Twelve SWE-agent logs concatenate retries or earlier attempts, so counting
   every `Response` line produced 39--340 responses for 22--123 final
   operations. The tool-call IDs preserved in the final `.traj` history select
   the exact response span. Empty/retry trajectory elements are the intervening
   responses; where several calls produce one retry element, their usage is
   summed into that element. This retains every final operation and does not
   count abandoned earlier runs.
2. Terminus2 `response.txt` can contain malformed outer JSON or an unexecuted
   command. Reading JSON string literals for `keystrokes` recovers the command
   text. Across all 93 targets, the official `commands.txt` string stream is an
   exact ordered subsequence of the response command stream. Two extra response
   commands (one malformed unclosed command and one empty command) are absent
   from the official execution stream and are therefore not fabricated into
   operations.

For an LLM response that produces several official operations, the default
projection divides the response's token count equally among those operations.
This deterministic projection preserves the provider-reported call total and
does not use the human stage or predicted partition. The full experiment must
report the number and token mass of multi-operation responses and whether their
operations cross gold, recurrence, or raw-action partitions. If none crosses,
the allocation cannot affect the score. If crossings exist, equal,
all-to-first, and all-to-last allocations must be reported; an allocation-
dependent primary verdict is inconclusive.

## Standard Metric Decision

The primary metric will not be the existing custom mixed-weight score.

[B-cubed precision, recall, and F1](https://aclanthology.org/P98-1012/)
are established element-wise external partition metrics. They are appropriate
because CodeTraceBench stages are session-local partition identities rather
than a shared named class taxonomy. There is no scientifically valid global
stage-label accuracy to compute.

The primary metric is ordinary operation-level B-cubed. The experiment also
applies the published
[weighted B-cubed formulation](https://pmc.ncbi.nlm.nih.gov/articles/PMC5103821/),
using observed token counts as object weights. Uniform weights reduce to
ordinary B-cubed. Token weighting is a resource-sensitive extension, not a
community-standard token-attribution metric, and cannot decide the primary
hypothesis by itself.

The mandatory reported metrics are:

1. ordinary unit-operation B-cubed precision, recall, and F1 (primary RQ1
   result, already independently reproducible from Step 0024);
2. total-token-weighted B-cubed precision, recall, and F1 (resource-sensitive
   secondary analysis);
3. exact token-mass conservation and covered operations/sessions (measurement
   validity, not a paper-performance score).

Exact boundary precision/recall/F1 remains an RQ3 segmentation diagnostic. It
does not answer resource attribution and will not decide RQ1. ARI is not added:
it would duplicate partition agreement without measuring resource mass, while
the required ordinary B-cubed result already supplies the standard unweighted
cross-check.

## Same-Input Comparisons

Every view receives the same 20,866 operations and token weights:

- **current recurrence operation stack** — unchanged Step 0024 result;
- **raw-action-key change** — contiguous changes in the already-materialized
  source-native `raw_action_key`; this is the main baseline;
- **one session block** — no within-run hierarchy;
- **one operation per block** — maximally fragmented control;
- **action-kind change** — the existing normalized `action_change` assignment,
  reported only as a semantic action-kind ablation;
- **phase change** — source-visible phase-only ablation.

The plan must make recurrence versus raw-action-key the primary same-input
comparison. Action-kind and phase-only rows are not hidden if stronger; they
are ablations used to explain which visible structure carries agreement.

## Rejected Alternative

The public artifact for
[How Do AI Agents Spend Your Money?](https://arxiv.org/abs/2604.22750)
was screened as a possible external token benchmark. Its released phase
analysis divides interaction rounds into equal temporal quintiles. Those
quintiles are useful published cost-analysis precedent but are not independent
semantic responsibility truth. The artifact also exposes only final aggregate
usage for the inspected mini-SWE-agent files rather than complete per-call
usage. It is therefore rejected as the RQ1 oracle, not converted into a custom
experiment.

## Admission Outcome

The next node may propose exactly one experiment that replays the current
assignments over this complete source-valid measured population and computes
the declared standard metrics. No algorithm tuning, threshold search, new
benchmark, manual annotation, or paper-story change is admitted in this
experiment.
