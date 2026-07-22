# Step 0066 — recursive operation segmentation

Timestamp: 2026-07-22T00:43:13-07:00
Phase: BUILD_AND_EVALUATE
Current gate: EXPERIMENT
Status: implementation

## Node 0066-E1 — trajectory and implementation audit

The current branch is `research/semantic-flamegraph-artifacts-v2`; it was not
changed. The worktree began clean at pushed commit `1cb1d1b3c`.

The root audited the complete prior algorithm trajectories rather than assuming
that recursive segmentation already existed. Step 0065 implements only the
backend-neutral stable-ID mark reader and proves Agent-authored replay. No
automatic recursive Agent backend currently emits those marks.

The retained complete results establish two opposite interface failures:

- online Qwen2.5-3B stack transitions legally reached variable depth but made a
  new leaf at 20,857/20,866 operations (`new_frame_rate=0.99957`); and
- whole-trajectory Qwen3.6-27B global segmentation processed all 405 sessions
  but emitted exactly 405 segments and zero internal boundaries.

The retained multi-resolution recurrence reaches ordinary B-cubed F1 0.662740
on the same complete CodeTrace population. These facts make recursive
single-boundary interval decomposition a distinct mechanism rather than another
parameter variation.

The fixed Qwen3.6-27B artifact and llama.cpp runtime remain available on the
local RTX 5090. The complete source-native reconstruction caches, turn
assignments, recurrence assignments, verified manifest, and 405-session target
operations are present. Therefore the experiment is executable without a new
dataset or proxy workload.

## Node 0066-E2 — proposal

The proposed algorithm asks an Agent to STOP or identify one most important
semantic transition in a complete source-native turn interval, names the two
resulting responsibilities, and recursively repeats on both sides. Strict
interval shrinkage guarantees termination; the Agent decides semantic
granularity without a fixed depth, leaf count, minimum segment length, score,
or contraction threshold. Final paths are serialized directly into Step 0065's
stable-ID operation-mark contract and one pprof.

The complete plan is `experiment-001/experiment-plan.md`. It now enters three
serial independent plan-review rounds before implementation.

## Node 0066-E3 — plan-review convergence

Round 1 repaired fixed-case selection, the target-blind root/name boundary,
runtime fail-closed behavior, and the exact visible-path B-cubed construct.
Round 2 removed a contradictory silent-STOP fallback and replaced a zero-local-
objection semantic gate with collection-level usefulness plus recorded local
limitations. Round 3 returned PASS with no remaining must-fix. No optional
threshold, control, or protocol machinery was added.

## Node 0066-E4 — case-study correction and long-horizon audit

The user clarified that every case study must be an aggregate over many
sessions and that the paper must contain a flame graph actually opened in stock
pprof and shown to solve a real problem. Therefore the earlier four-session
framework stress set and three-session repeated-request set are no longer
paper-case candidates. They remain permissible wiring or evidence drilldowns.

A source-visible population audit found that the longest CodeTrace session has
275 operations. The fixed longest decile contains 41 complete sessions, each
with at least 95 operations, and 5,750 operations in total across Terminus2,
OpenHands, and SWE-agent. The experiment now uses the complete 405-session
population and this 41-session long-horizon subset as its two semantic-review
collections. The paper-facing cases will be the 41-session long-horizon
semantic profile and the retained AgentRewardBench differential profile over
440 complete sessions and 338 bad--good pair occurrences. Every figure must be
rendered from AgentPProf's `.pb.gz` by stock pprof, opened and inspected, and
linked to source-verifiable aggregate findings before it enters the paper.

## Node 0066-E5 — implementation review and source-contract correction

The first implementation passed its focused recursion tests and all 68
AgentPProf tests, but independent OSS review rejected execution for three
reasons. Session caches were not bound to the exact prompt/grammar contract;
118/405 OpenHands trajectories used the public recall-query fallback while the
code incorrectly called every task text a raw first-user request; and pprof
readback checked nonemptiness rather than exact sample mass.

The minimal repair binds caches to both system prompts, grammar shape, seed,
completion budget, prompt constructors, and fixed projection. The registered
input is now target-blind public task text: 287 raw role-user messages and 118
public OpenHands recall queries, with the source split reported and no manifest
or source identity shown to the model. Both AgentPProf invocations now require
the exact operation, session, and mark population, parse `status=ok`,
`format=pprof`, `view=operations`, require samples equal operations, require
zero warnings, and perform stock `go tool pprof -top` readback.

Round 2 independently reread the repaired implementation and returned PASS.
Focused recursive tests pass 5/5 and all 68 AgentPProf tests pass. A strict
readback control reproduced the existing 326-operation AgentCap pprof at the
exact prior SHA-256, confirming that the new coverage checks accept a known
complete profile before the costly CodeTrace run.

## Node 0066-E6 — real preflight attempt 1

The first real preflight reconstructed all 405 public trajectories but stopped
on the first selected mini-SWE-agent recursion before opening official stages.
The Agent reused the active parent `analyze codebase and locate bug` as one
child and named only the other child more specifically. The parser failed
closed as designed. The system prompt had omitted the plan's explicit
ancestor-distinct requirement, so the minimal wiring repair states that both
children must be distinct from every active path name; otherwise the Agent must
STOP. It does not add a new specificity criterion. Exact details are in
`experiment-001/real-preflight.md`.

## Node 0066-E7 — current-operation continuation

An exact source-only replay after the wording repair again used the current
root operation on one side of a split and a concrete new subtask on the other.
This exposed a flaw in the approved binary-tree contract rather than another
wording omission. Before opening any manifest or score, the plan was reopened.

Independent review approved a minimal v2 rule: a child equal to the current
operation recursively continues over its smaller interval without pushing a
duplicate frame; only a new child adds a frame. Left and right remain distinct,
earlier ancestors remain invalid, continuation is not STOP, and strict interval
shrinkage remains mandatory. Standard metrics, stable-ID marks, pprof output,
fixed workload, RQ, thesis, and paper authorization are unchanged.

## Node 0066-E8 — unified stay/pop/push resolution

The v2 source-only replay then returned the current nested analysis operation
on one side and the earlier root operation on the other. This is the missing
pop action from the user's original stack model. Independent plan review
approved v3: resolve a child against the entire active path, using current
match as stay, earlier match as pop, and no match as push. Resolved siblings
must differ and every interval still strictly shrinks; STOP remains explicit.

The reviewer also approved exact emitted-path canonicalization. A mark is
emitted only at sequence start or when the resolved full path changes, so
adjacent equal paths caused by nested pop do not create redundant leaves or
marks. Non-adjacent or unequal paths never merge, and raw recursive decisions
remain auditable. Algorithm/cache identity advances to v3; metrics, workload,
RQ, thesis, and paper authorization remain unchanged.

## Node 0066-E9 — exact no-op totalization

The v3 source-only replay next returned a raw split whose two children both
resolved to the unchanged active root path. Independent review found that a
general equal-sibling fallback would erase meaningful invalid outputs. The v4
revision therefore totalizes only the exact no-op condition
`left_path == right_path == active_path` as an audited
`degenerate_current_split_stop`. It preserves the raw split, emits no new
boundary or mark, and reports model STOP, raw SPLIT, effective SPLIT, and this
degenerate case separately. Equal new-child or earlier-ancestor paths remain
errors. Algorithm/cache identity advances to v4; workload, metrics, RQ, thesis,
paper authorization, and the requirement for actual stock-pprof profiles are
unchanged. Focused tests pass 13/13; independent v4 plan and code/document
re-reviews both returned PASS.

## Node 0066-E10 — real v4 preflight passes

The fixed source-visible longest session from each of four frameworks completed
under v4: 584 operations became exactly 584 valid pprof samples, with no
warnings. Leaf counts were `4, 1, 1, 36`, and semantic depth ranged from one to
four. The mixture of unchanged sessions and internally split sessions shows
that neither a fixed depth nor mandatory splitting is imposed. Of 57 raw
splits, 56 were effective and one was the audited identical-current no-op;
24 explicit model STOPs remained distinct. Stock pprof readback succeeded at
SHA-256 `445287a34b9ff50c9e4af2651d3da7ea70e57f92fab9674eb59a163616497843`.
No gold label or score was read. Preflight now authorizes the complete fixed
405-session inference, not any paper claim.
