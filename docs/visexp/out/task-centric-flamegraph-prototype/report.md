# Task-centric semantic flamegraph prototype

This artifact replaces the system-field stack with a concrete-task stack:

```text
task -> subtask -> phase -> semantic action -> observed outcome
```

- task: `Order a loaner laptop and provide a reason`
- source task id: `workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2`
- source: `docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl`
- operations: 204
- input + output tokens: 1112192
- attempts: 4 (4 failed)
- repeated operations: 54
- action-error operations: 2

| Phase | Operations | Repeated operations | Tokens |
|---|---:|---:|---:|
| Choose options | 26 | 0 | 127408 |
| Enter details | 30 | 14 | 162326 |
| Finish | 26 | 20 | 149044 |
| Navigate | 120 | 20 | 667448 |
| Observe | 2 | 0 | 5966 |

## Construction boundary

The concrete task is selected by the trace session identifier. A declared `phase -> subtask` map turns source phases into readable task decomposition. The remaining frames use visible `phase`, `action`, `repeat_state`, and `step_error` fields. Agent/model identity is an interactive filter, not a stack level. Opaque DOM target IDs and oracle/diagnostic labels are excluded.

**Limit:** The phase-to-subtask map is declared in the generator. This artifact tests the task-centric visual shape; it does not count as evidence that task/subtask labels were inferred automatically.

Open `index.html` for metric switching, agent filtering, issue filtering, search, hover details, and click-to-zoom. The two SVG files are deterministic vector snapshots for paper/design review.
