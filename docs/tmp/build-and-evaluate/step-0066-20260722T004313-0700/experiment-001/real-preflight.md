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

## Attempt 2 — repeated parent reveals a contract flaw

The repaired wording still produced a source-only root split whose left child
was `analyze gc sweep code` and whose right child exactly repeated the current
root `fix ocaml garbage collector crash`. This is not meaningless output: the
left interval enters a concrete subtask while the right interval continues the
root responsibility. Requiring a new right-hand name would manufacture a
synonym rather than improve the stack.

The plan was therefore reopened before any label or score was read. Independent
review approved one semantic correction. A child equal to the current operation
means continuation: recurse over the strictly smaller interval without pushing
a duplicate frame. A new child pushes a genuine operation frame. Left and right
must remain distinct, and equality with any earlier ancestor remains invalid.
The algorithm identity advances from v1 to v2; no response under the old
contract is eligible for cache reuse. Dataset, model, metrics, fixed 405-session
run, RQ, and paper authorization remain unchanged.

## Attempt 3 — nested output reveals the missing pop action

Under v2, the same source-only trajectory progressed through root continuation
and a new `analyze ocaml gc code` child. Inside that child, the Agent returned
the current analysis operation on one side and the earlier root
`fix ocaml garbage collector crash` on the other. The full decision chain was
root stay/push, child stay/push, then child stay/root-pop. This precisely matches
the append/stay/pop stack behavior in the user design; rejecting the earlier
frame made the recursive interface incomplete.

Independent review approved v3 before any manifest, stage, or score was opened.
Child resolution now matches against the complete active path: current match is
stay, earlier match is pop, and no match is push. Resolved sibling paths must
differ, intervals still strictly shrink, and only explicit STOP/base case ends
recursion. Exact adjacent equal resolved paths emit one canonical segment/mark,
while all raw decisions remain cached for audit. The algorithm/cache identity
advances to v3 and v1/v2 responses are ineligible for reuse.

## Attempt 4 — identical current paths reveal a controller no-op

The direct v3 source-only replay advanced further through the same mini-SWE
trajectory. It produced root stay/push and nested stay/pop decisions, then a
raw split whose left and right labels both resolved to the unchanged root
operation. No manifest, official stage, score, or outcome had been opened.

Independent review rejected a broad "equal siblings become STOP" rule because
equal new children and equal earlier ancestors have different semantics. The
minimal v4 controller rule recognizes only
`left_path == right_path == active_path` as
`degenerate_current_split_stop`. The raw decision is preserved and counted;
it creates no boundary or additional mark and is not reported as a model STOP.
All other equal resolved siblings still fail closed. The algorithm/cache
identity advances to v4, so no v1--v3 response is eligible for reuse.

## Attempt 5 — PASS on all four fixed framework cases

The exact v4 implementation completed the fixed source-visible longest session
from OpenHands, SWE-agent, Terminus2, and mini-SWE-agent. It covered all 584
turns/operations and produced 42 canonical leaves with per-session counts
`4, 1, 1, 36`. Semantic depths ranged from one to four, with counts
`15, 18, 8, 1`; leaf lengths ranged from one to 191 turns. Two sessions
therefore remained intentionally unsplit while two received internal semantic
boundaries. This rejects both uniform one-leaf-per-turn fragmentation and a
controller-imposed fixed depth without requiring every session to split.

The controller made 57 raw SPLIT decisions: 56 effective splits and one
`degenerate_current_split_stop`; it also recorded 24 explicit model STOPs.
The four roots plus recursive calls consumed 365,661 prompt tokens and 2,199
completion tokens under the fixed one-slot server. No manifest, official stage,
score, outcome, or prior prediction was opened.

AgentPProf replayed the exact 584 operations into 584 pprof samples and 24
unique stacks without warning. Stock `go tool pprof -top` read the output
successfully. The profile is 3,182 bytes, SHA-256
`445287a34b9ff50c9e4af2651d3da7ea70e57f92fab9674eb59a163616497843`.
This preflight establishes executability only; it does not score accuracy or
authorize a paper claim. The next action is the registered full 405-session
run, followed by scoring and the 41-session long-horizon stock-pprof case.
