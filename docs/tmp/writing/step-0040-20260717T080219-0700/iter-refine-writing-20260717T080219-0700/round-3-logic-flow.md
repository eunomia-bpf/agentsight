# Round 3 — Full-Paper Logic Flow

## Node identity

- **Started:** 2026-07-17T13:14:45-07:00
- **Completed:** 2026-07-17T13:24:00-07:00
- **Parent:** Step 0040 WRITE gate
- **Objective:** reread the complete rendered paper for claim/use order and the
  causal chain from root problem through the four RQ answers.
- **Reviewer:** fresh read-only subagent invoking `check-paper-structure-flow`
  in global logic-flow scope.

## Independent verdict

The central chain is coherent:

`cross-run questions -> missing stable semantic identity and reusable semantic
responsibility hierarchy -> operations and operation stacks -> AgentProf
implementation -> attribution/localization/tag-accuracy/cost evidence`.

The reviewer confirmed that Round 2 fixed both the execution-hierarchy wording
and ordinary-B$^3$ construct mapping. It found three remaining must-fix ordering
or provenance gaps:

1. Table 2 used `local+semantic`, `local+raw`, and `local only` before defining
   those methods.
2. Scope and Limitations introduced 494.9 million mapped tokens for the first
   time after token-weighted B$^3$ had left the paper.
3. RQ3 did not distinguish the integrated declared-task interface from the
   standalone action-label backend evaluation, leaving the D2-to-evidence
   interface provenance ambiguous.

It also flagged the unsupported phrase `statistically indistinguishable` for
the 0.654 phase-only versus 0.649 recurrence values because the paper did not
show that comparison's interval or test.

## Applied fixes

### Definition before use in RQ2

Before Table 2, the paper now defines the post-hoc columns. `Local only` ranks
by the fixed benchmark-provided operation-local diagnostic score.
`Local+semantic` and `local+raw` preserve every strict local-score ordering and
use only the corresponding semantic or raw-action group score to refine exact
ties. The post-table paragraph now reports outcomes without redefining the
method. The primary semantic-versus-raw comparison remains primary and the
local-first comparison remains explicitly post-hoc.

### Removed orphaned token quantity

The 494.9-million mapped-token sentence was deleted from Scope and Limitations
and its Chinese comment. It no longer supports a paper-facing metric and was
not introduced by RQ1. The valid scope remains: 20 controlled tasks, all 405
reconstructable failed CodeTraceBench trajectories, and the post-hoc
constructor-selection qualifier.

### Field-backend provenance

The RQ3 opening now defines a tag as an operation field consumed by the
pluggable field interface; a backend can run through the CLI or a standalone
adapter before its output maps to that field.

- The AgentBoard task-family result now explicitly exercises AgentProf's
  integrated declared-task field interface with a fixed Qwen3.6-27B llama.cpp
  backend.
- The ASE action-label result now explicitly uses a standalone backend-level
  adapter with the fixed Qwen3.6-27B closed-label configuration. It is not
  presented as an integrated CLI path.

These statements were verified against the Step 0031 and Step 0032 plans,
commands, result reports, `agentpprof` README, and Rust tagger path before
editing the paper.

### Removed unsupported test language

The paper now reports phase-only at 0.654 and recurrence at 0.649 directly. It
concludes that the evidence supports semantic responsibility partitioning over
raw action identity, not recurrence alone or universal view dominance. It no
longer claims statistical indistinguishability without showing the test.

## Deferred findings

- Literal task/action results are less visible than OSWorld group results in
  the Abstract and Conclusion. Round 4 owns summary rebuilding and will decide
  whether an existing literal-tag value should replace a lower-value detail.
- RQ3 has several constructs in sequence. Noun-phrase navigation may help, but
  terminology and paragraph-flow rounds own that decision.
- The RQ1 figure now remains within RQ1 and before RQ2. A sentence crosses the
  page boundary around the figure, but the evidence order is understandable;
  no further float movement is authorized unless a later rendered-flow review
  finds a clear improvement without page regression.

## Preservation audit

- Exact thesis and four RQs unchanged.
- No story, abstraction, experiment, metric, result, or benchmark changed.
- All RQ2 qualifiers and exact intervals remain.
- Both RQ3 results remain; only their integration provenance is clearer.
- Custom paper metrics remain absent.
- Read-only subagent and writing round performed no Git operation.

## Compilation and rendered evidence

`make` completed all passes. The PDF remains nine US-Letter pages with main
text through page 7 and references beginning on page 8. It has no undefined
citation, undefined reference, or overfull warning. Figure 2 remains at the top
of page 5 inside RQ1 and before RQ2. Searches find no token-weighted B$^3$,
Recall@20\%, fixed-reader protocol, or 494.9-million orphan quantity.

## Next node

Round 4 invokes the complete `rewrite-abstract-intro` procedure without a
fork: role mapping, logic-chain diagnosis, paragraph-by-paragraph plan, and
abstract derivation last.
