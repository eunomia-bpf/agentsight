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
