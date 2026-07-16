# Experiment Plan Revision Disposition

**Revised:** 2026-07-15T18:40:55-07:00
**Input:** independent `REVISE` verdict in `plan-review.md`
**State:** revised; awaiting the same independent plan reviewer

The root accepted all three must-fix items without adding another benchmark,
evaluator, implementation review, or protocol layer.

1. The candidate now has to exist in the shared Rust `LlamaTagger` before any
   scored run. It returns the established raw open-vocabulary tag and an
   additional declared canonical/task tag separately; the thin adapter only
   invokes that path.
2. The intervention is explicitly one ontology-plus-prompt-plus-grammar
   bundle. Open-vocabulary exact match is context, not a fair classifier
   baseline or grammar ablation. Positive support requires both macro-F1 and
   micro accuracy of at least 0.80, in addition to beating the majority
   control.
3. The claim is bounded to assignment into AgentBoard's official task-family
   taxonomy. The plan now records the project-authored glossary, possible
   domain/template fingerprinting, unknown foundation-pretraining exposure,
   and the absence of broader phase/action, open-semantic, or unseen-family
   authorization.

These changes strengthen the literal task-identity cell inside fixed RQ3. They
do not change the thesis, four RQs, contributions, story, recurrence algorithm,
or any admitted result.
