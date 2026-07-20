# REAL PREFLIGHT — Single-Frame Semantic Task Stack V2

**Completed:** 2026-07-19T21:52:00-07:00  
**State:** Complete; fixed full run authorized  
**RQ:** RQ3 — tag accuracy

## Scope And Isolation

The V2 evaluator ran one complete public CodeTraceBench trajectory from each of
mini-SWE-agent, OpenHands, SWE-agent, and Terminus2: 47, 95, 32, and 22 source
operations, or 196/196 total. It opened no verified stage manifest, stage
range, target score, future action, current action result, or resource weight.
The only model inputs were the de-slugged public task identity, complete current
stack, preceding observation, and current source action registered by the
plan.

## Implementation Checks

The evaluator and local model completed all 196 transitions under
`qwen-semantic-task-stack-v2` and
`direct-gbnf-single-frame-v2`. The grammar admitted only a legal current-depth
prefix and either one bounded lowercase label or null. Synthetic parser checks
covered stay, push, arbitrary multi-pop, and sibling replacement. Two
label-free local-model probes produced valid first-push and sibling-replacement
JSON. There is no V1 array field, unbounded same-step generation, retry,
repair, clamp, default, or fallback.

Every resulting stack was non-empty and every created frame had a fresh
within-trajectory identity. Observed depth ranged from 1 to 5 with mean 2.898:
4 operations at depth 1, 82 at depth 2, 47 at depth 3, 56 at depth 4, and 7 at
depth 5. The model used 107,127 prompt and 3,674 completion tokens. Wall time
was 14.23 seconds with four concurrent sessions. No output truncation, context
overflow, source mismatch, invalid transition, or missing operation occurred.

The prediction file SHA-256 is
`be4bfed2f92b6d7c3ad27311c68560233db98a8c6eade0ca9d069c20993d52ea`.
A second invocation used only fixed caches, completed in 1.42 seconds, and
reproduced the same prediction file.

## Visible Semantic Diagnostic

The transition distribution was 51 pushes, 145 sibling replacements, zero
stays, and zero ancestor-only pops. Thus new-frame rate was 1.0. The bounded
single-frame contract fixed V1's execution failure, but this Qwen 3B policy
still appears to create a fresh leaf for every source operation.

The approved plan explicitly registers new-frame rate as a diagnostic rather
than an accuracy gate. The preflight therefore neither rejects nor retunes the
model based on this source-visible behavior. The complete ordinary B-cubed
score must determine whether the fixed candidate is contradicted. No third
prompt variant is permitted inside this experiment.

## Decision

Archive extraction, causal evidence ordering, single-frame grammar, state
transition, variable depth, context capacity, full operation coverage, model
identity, cache identity, deterministic resume, and stage isolation all pass.
Proceed from empty V2 full-run caches over all 405 trajectories, then open the
official stages exactly once in the separate scorer.
