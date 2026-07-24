# RQ2 Baseline and Closest-Work Audit

**Search date:** 2026-07-23  
**Purpose:** determine which current external systems are valid numerical
baselines for the Step 0072 RQ2 mechanism test

## Closest current systems

### Hodoscope

Primary sources:

- <https://hodoscope.dev/>
- <https://hodoscope.dev/blog/announcement.html>

Hodoscope summarizes each action with an LLM, embeds summaries in a shared
space, and visualizes clusters or density differences across agent
configurations. It is a strong product and related-work baseline for
cross-trajectory behavior discovery. Its output is a 2-D action-density map,
not one score per source operation under the same fixed local diagnostic
signal. Converting it into a local-first MAP baseline would require inventing a
new retrieval/scoring adapter and would no longer compare native outputs.

### TraceProbe

Primary source:

- <https://arxiv.org/abs/2607.06184>

TraceProbe maps coding trajectories to nine deterministic action types, detects
single-run anti-patterns, and aligns controlled run pairs. It is a close
conceptual baseline for process-level coding-agent diagnosis and motivates the
paper's raw-action comparator. It does not emit the same general cross-run
operation hierarchy or RQ2 per-operation group score.

### AgentRx

Primary source:

- <https://arxiv.org/abs/2602.02475>

AgentRx localizes the critical failure step and category in failed
trajectories through constraint extraction and judging. It is a direct
failure-localization neighbor, but its output is one critical step/category per
failed run rather than a selectable additive profile over all operations.
AgentRx therefore belongs in related work and target-definition context, not as
an information-matched group-score baseline.

### AgentLocate and HarnessFix

Primary sources:

- <https://arxiv.org/abs/2607.07989>
- <https://arxiv.org/abs/2606.06324>

AgentLocate identifies a responsible agent and earliest decisive step in
multi-agent failures. HarnessFix attributes trajectory evidence to harness
layers and validates repairs. Both strengthen the state of the art for
localization and downstream repair, but neither exposes the same RQ2 output
contract as AgentProf.

## Numerical baseline decision

The Step 0072 numerical comparison must keep:

1. identical source operations;
2. identical local diagnostic scores;
3. identical retained source-kind/tool/outcome evidence;
4. identical rank composition; and
5. only the operation prefix changed.

Only `local-only` and `local + raw action + identical source evidence` satisfy
that contract. AgentProf-only is a component ablation. Hodoscope, TraceProbe,
AgentRx, AgentLocate, and HarnessFix remain cited closest work, not forced
through an invented adapter merely to add rows.

This decision keeps the experiment small while making the strongest available
same-information objection explicit.

