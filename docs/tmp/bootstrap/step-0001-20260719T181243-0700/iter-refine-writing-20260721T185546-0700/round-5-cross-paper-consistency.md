# Round 5 — Cross-Paper Consistency

## Independent review

Reviewer: `writing_round5_consistency` (read-only).

The audit found material drift between the paper and the registered plan/code:
No-op had been promoted to a third co-primary contrast; Full Raw omitted prompts,
logs, and snapshots; `unknown` and `no_effect` were collapsed; the paper listed
unimplemented timeline/transition/hotspot tools; and future oracle/credential
repairs were written as completed-run behavior.

## Applied changes

- restored the registered primary Trajectory-minus-Raw estimand and mandatory
  `Gain(Trajectory)-Gain(Generic)` contrast; kept No-op as benefit/harm reference;
- defined the complete Raw universe as sanitized sessions, prior prompts,
  worker-visible logs, and immutable snapshot/checkpoint bytes and manifests;
- added the independent action-effect closure
  `observed | no_effect | unknown`, with coverage and boundary rules;
- replaced the prospective region-transition treatment with the actual pilot
  queries: `artifact_history`, `session_diff`, and `effects`;
- documented the actual current-workspace and Raw tool surfaces and the absence
  of hotspot/importance/recurrence/validation/semantic queries;
- stated that multi-vendor parsing/visualization exists but research-grade
  source/effect binding is qualified only for Codex;
- recorded the completed-run oracle evidence gap (first payload plus count) and
  the unrepeated future dual-payload/joint-hash repair;
- recorded the historical credential-retention mistake, unread removal, and
  future purge path without claiming it had already protected the completed run;
- required separate structural, No-op headroom, and tool-engagement gates in
  coding and scientific domains; and
- synchronized `docs/evaluation.md`, `docs/design.md`, and the current narrative
  in `docs/idea-story.md`, including `list_sources` and the separation between
  query ablation and earlier-session source scope.

Historical superseded label-based entries were retained as provenance.

## Validation

- actual P0 models, budgets, scores, zero-tool status, and headroom decision
  remain unchanged;
- LaTeX compile: PASS;
- compiled length: 6 pages;
- undefined citations/references: none reported.
