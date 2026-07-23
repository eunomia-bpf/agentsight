# Automatic Backend Instruction — AgentReward Recursive Operations

## Input And Output

Read only the assigned source-session nodes from the provided `trace.jsonl`.
The trace contains source-visible goal, reasoning, page state, action, visible
tool error, and additive measurements. It contains no expert success, looping,
optimality, reward, pair-side, or bad/good label.

Write one JSON object mapping selected source node IDs to:

```json
{"tag": "semantic operation name", "parent": "parent annotation node ID", "next": "next source node ID or null"}
```

Do not change the trace, source text, code, paper, or another worker's fragment.
Do not infer or record whether a trajectory is a benchmark success or failure.

## Segmentation

The materializer already supplies the required session-level and prompt-level
operations. Refine each assigned prompt as follows:

1. Inspect enough contiguous source steps to understand responsibility changes.
2. Mark the start of each coherent operation span at a source LLM node.
3. Name the work performed in that span, not the benchmark, model, tool, page,
   or outcome.
4. Recursively subdivide a span only when its children express at least two
   meaningful responsibilities. Do not create one operation per source step.
5. Reuse the same concise operation name across sessions when the
   responsibility is the same.

When supported by source-visible behavior, use these exact shared names:

- `recover from failed or repeated interaction`
- `verify or report task completion`

These shared names may be parent operations. A long recovery span should still
be subdivided when its source trace shows at least two distinct
responsibilities, such as returning to a page, changing a query, dismissing an
obstruction, or retrying the intended edit. The shared parent enables
cross-session aggregation; its children explain what the Agent actually did.

Other names should be simple verb phrases such as `locate the requested item`,
`edit the requested record`, or `compare candidate answers`. Avoid synonyms for
an existing shared operation, invented terminology, fixed depth, and names that
encode success/failure.

## Annotation Semantics

- `parent` is the source node ID where the enclosing semantic operation starts.
- `next` is the first source node after this operation's contiguous span.
- Sibling spans share a semantic parent and have disjoint ranges.
- Nested spans must remain inside their parent's range.
- A final sibling may use `null` only when it should inherit its parent's end.

The backend is complete when all assigned sessions retain their mandatory
session/prompt coverage, meaningful responsibility changes are represented by
valid nested or disjoint spans, and the fragment passes the AgentPProf
annotation-workspace validator after the root merge. Hierarchy warnings are
diagnostic prompts for reconsideration, not reasons to force depth.
