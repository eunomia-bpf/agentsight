# Step 0075 Entry — End-to-End RQ4 Accounting

**Timestamp:** 2026-07-23T21:44:59-07:00

**Parent:** Step 0074 outer audit

**Outer gate:** EXPERIMENT

**RQ:** RQ4 — What is the cost of constructing a semantic profile?

## Objective

Close the paper's largest remaining cost gap by measuring the complete offline
path from an exported real trace to one standard pprof:

```text
source adaptation → automatic annotation → pprof materialization
```

The current paper reports only fixed-operation and fixed-mark construction.
This step keeps those measurements as replay cost and separately reports the
dominant automatic annotation component.

## Boundaries

- The paper thesis, story, four RQs, and adopted A2 backend do not change.
- Live agent execution and trace capture are outside this offline experiment.
- Existing complete expensive runs are reused; no model backend is rerun only
  to improve bookkeeping.
- Quality and cost stay paired by backend. A failed backend cannot supply the
  positive product cost, and A2 cannot inherit another model's usage.
- The experiment produces Markdown reports and ordinary measurement artifacts;
  AgentPProf still emits only `.pb`/`.pb.gz`.

## Next node

Review and approve one minimal plan, then run the shared source adapter and the
raw-action, recurrence, and fixed-mark pprof paths on the complete
20,866-operation CodeTrace population.

