# Implementation Review: Minimal RQ3 Tag-Fidelity Adapter

- Completed: `2026-07-14T09:11:52-07:00`
- Scope: `script/agent_trace_datasets.py` and
  `script/operation_tag_accuracy_eval.py`
- Shared skills, paper, and AgentProf core: unchanged

## Round 1

- Reviewer: fresh independent subagent using `research-experiment-design`
- Verdict: **REVISE**

The reviewer verified session-deduplicated task clustering, scorer-only
references, literal `unmatched` inside V-measure, the matched constant control,
and real per-cell/union AgentProf conservation checks. One blocker remained:
the implementation did not execute the approved source-field audit before
action inference, so a structured gold label copied into visible text could
still enter an action score.

### Root disposition

Added one read-only pre-inference audit. It recognizes only explicit structured
serialization: an `action`/`action_type` field, an arrow-suffixed gold label, or
an exact uppercase enum. Ordinary natural-language action words remain valid
visible evidence. A hit marks the cell `unavailable`, records the audit, skips
prediction/profile generation, and contributes no rows to the union. No
predictor parser, model, metric, benchmark, cutoff, or sweep was added.

## Round 2

- Reviewer: second fresh independent subagent using
  `research-experiment-design`
- Verdict: **PASS**
- Blocking findings: none

The reviewer confirmed with small temporary fixtures that:

- structured copies are rejected before action inference;
- natural-language instructions such as `click the button`, `Open Settings`,
  and `Click` are not rejected;
- an unavailable cell generates no predictions/profile and cannot enter the
  union;
- an available fixture completes the existing scorer and AgentProf path;
- unmatched weight remains inside scoring support, coverage is correct, and
  row/weight conservation is exact; and
- the implementation adds no learner, metric, cutoff, sweep, or experimental
  protocol beyond the approved adapter.

`py_compile`, both relevant CLI help paths, leakage fixtures, and the available
end-to-end fixture passed. A Hugging Face Viewer probe returned HTTP 503; this
is external preflight state rather than an implementation defect and does not
change the approved same-source retry path.
