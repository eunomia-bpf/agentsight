# Real preflight

## Attempt 1 — fail closed on a repeated ancestor

The fixed one-slot Qwen3.6-27B server loaded the registered model at the exact
SHA-256 with a 32,768-token context. The adapter reconstructed and tokenized
all 405 public trajectories, then selected the source-visible longest prompt
in each framework. Before any official stage was opened, the first selected
mini-SWE-agent trajectory failed the recursive semantic contract.

The root was `fix ocaml garbage collector crash`. The first recursive split
produced `analyze codebase and locate bug` versus `implement and verify fix`.
When recursively decomposing the left interval, the Agent returned the parent
name itself as the left child and `examine shared heap sweep implementation` as
the right child. The parser correctly rejected the repeated ancestor rather
than emitting a redundant stack or silently converting the decision to STOP.

This was a prompt-wiring defect, not a scientific result: the implementation
and plan required child names to differ from every ancestor, but the actual
system prompt had stated only that child names must be semantic and distinct
responsibilities. The minimal repair makes the existing non-collision rule
explicit: both children must be distinct from all names in the active path; if
the Agent cannot name both without repeating an active name, it must return
STOP. No new specificity criterion, parser rule, dataset, metric, model, depth
policy, scientific hypothesis, or score was introduced. The inference-contract
hash changes automatically, so no stale response can enter the rerun.
