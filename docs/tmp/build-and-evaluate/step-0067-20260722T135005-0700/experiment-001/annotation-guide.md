# Agent annotation guide: long-horizon operation stacks

Timestamp: 2026-07-22T13:50:05-07:00

## Product boundary

AgentPProf is only a command-line consumer of an annotation configuration. It
does not call a model, infer `stay`/`pop`/`push`, or reinterpret names. The
annotating Agent reads source evidence and directly supplies the complete
semantic path that begins at each sparse boundary.

## Fixed collection and question

Annotate the fixed 41-session longest-decile CodeTrace collection selected by
descending source-visible operation count with trajectory-ID tie-break. The
selection contains 5,750 operations. Do not select sessions, boundaries, or
paths by outcome.

The collection-level question is:

> How did these long-horizon agents decompose their assigned tasks, where did
> they repeat or return to earlier work, and which expensive paths ended
> without a supported conclusion?

## Required annotation

For every assigned session:

1. Read the task, session-level evidence, and whichever source-native turn
   summaries are needed to decide useful boundaries. The Agent chooses which
   intervals to expand and may follow `source_refs` when summaries are
   insufficient; exhaustive turn-by-turn reading is not required.
2. The first mark starts at the session's first `first_operation_id`.
3. Every mark contains a **complete path**, not one transition name. Example:
   `['configure git deployment', 'validate branch deployment']`.
4. Add a boundary only when the responsibility or task-progress state changes
   in a way that helps answer the fixed question. A tool, file, command, error,
   or retry alone is not a boundary.
5. All operation IDs in one source-native turn remain together. A boundary may
   use only a turn's `first_operation_id`.
6. Continuing the same complete path requires no mark. Returning to a parent
   writes the shorter complete path. Entering a child writes the longer path.
   Moving to a sibling writes the new sibling's complete path.
7. Depth is unconstrained. Do not target a minimum, maximum, distribution, or
   preferred depth. Add a level only when source evidence supports a distinct,
   persistent responsibility useful to the collection question; never use a
   tool, file, command, status, or cosmetic hierarchy to fill depth.
8. Reuse the same concise operation phrase when the same responsibility recurs
   within or across assigned sessions. Do not encode agent, model, session,
   tool, command, file, status, or outcome in an operation name.

Return one JSON file containing:

```json
{
  "batch": "batch-01",
  "sessions": [
    {
      "session": "exact source session ID",
      "marks": [
        {
          "start_operation_id": "1",
          "semantic_path": ["root responsibility"]
        }
      ],
      "findings": [
        "source-grounded observation useful for the case study"
      ]
    }
  ]
}
```

Do not emit operation IDs, turns, or sessions not present in the assigned
packet. Do not read official stages, scores, manifests, or outcome labels.
