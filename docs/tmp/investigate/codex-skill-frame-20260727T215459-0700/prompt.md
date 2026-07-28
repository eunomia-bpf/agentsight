# Task: make agent *skills* a level in the AgentPProf hierarchy, then render it

Implement skill recognition as a hierarchy level in `agentpprof`, produce a real
profile over real local sessions, and render it. Then report what the profile
actually shows.

## Why

The paper needs an **actionable** finding: the profile should point a developer
at *which skill to improve*, without requiring a before/after intervention
experiment. If skills are a frame in the stack, that answer is read directly off
the flame graph instead of guessed.

The scientific hook to preserve: the finding should be one that is **only
visible in aggregate** — no single trajectory makes it obvious. That is exactly
the paper's thesis ("agent observability needs profiling, not only debugging"),
so quantify aggregate-only visibility wherever you can.

## What I already verified (do not redo, but do sanity-check)

Skill invocations are recorded literally in Claude Code session JSONL — this is
an **exact machine-readable field, not an inferred tag**, which is a major
advantage over LLM-annotated operations:

```json
"name":"Skill","input":{"skill":"check-paper-citations","args":"..."}
```

Prevalence, measured over `/home/yunwei37/.claude/projects`:

| signal | files |
| --- | ---: |
| total session JSONL files | 1406 |
| contain `"name":"Skill"` tool call | 105 |
| contain `command-name` (slash-command invocation) | 113 |
| contain `invoked_skills` | 16 |
| contain `skill_listing` (availability attachment, NOT an invocation) | 1245 |

**Important:** the frozen 42-session paper corpus at
`docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/frozen-sessions/`
has only **3 of 42** files with Skill tool calls and 10 of 42 with
`command-name`. That corpus is too thin for a skill profile. Use the **full
local history** instead, and report exact counts for whatever corpus you pick.

Do not count `skill_listing` as an invocation — it is the list of available
skills injected into context, present almost everywhere, and counting it would
be a serious measurement error.

## The design decision you must make and justify

A skill invocation is literally a tool call, so the naive placement is a leaf
frame next to other tool calls. **That is almost certainly useless**: it would
measure only the cost of the `Skill` call itself (near zero), not the work the
skill governs.

The useful reading is skill as a **scope**: once invoked, a skill governs the
subsequent work until some boundary. Then the frame width answers "how much
budget went through this skill".

You must decide and defend the scope rule — e.g. until the next skill
invocation, until the end of the enclosing prompt/turn, or until the enclosing
semantic operation ends. State the rule, state what it over- and under-counts,
and verify exact additive conservation under it. If a skill scope would overlap
or cross another, resolve it explicitly (the model requires nested, noncrossing,
covering intervals).

Also decide where the skill frame sits relative to the existing frames
(`project`, `agent`, semantic operation path, LLM call, tool call) and say why.
Consider emitting a pprof **label** as well as a frame, so `-tagfocus` works.

## Code

- `agentpprof/` — the CLI. Frame construction: `src/profile.rs` (`stack_frames`,
  around line 1115; `stack_frame_values` around 2016) and
  `src/annotation_workspace.rs` (around line 1332).
- `agent-session/` — the shared Codex/Claude session parser. If the skill field
  is not surfaced yet, add it here.
- `cargo test` in both crates must pass. Add tests for the new behavior,
  including a conservation test.

## Hard product boundary (from CLAUDE.md — do not violate)

AgentPProf has **exactly one product artifact per run: one standard pprof
`.pb`/`.pb.gz`**. Encode the skill level in pprof **frames and labels only**. Do
**not** add a frontend, dashboard, bespoke viewer, or a second user-facing
export format. Rendering for the paper goes through existing pprof tooling
(`go tool pprof`) plus the paper-only renderer under `docs/visexp/`, exactly as
the existing `selfprofile.*` / `git-multibranch.*` figures were produced.

## Deliverables, all inside this directory

1. The code change in `agentpprof/` (and `agent-session/` if needed), with tests
   passing.
2. A real profile over a real corpus, plus the rendered flame graph(s) written
   here (PNG/SVG produced through the existing renderer path).
3. `report.md` with:
   - the scope rule you chose and why, including what it mis-counts
   - exact corpus counts: sessions, sessions with skills, distinct skills,
     invocations
   - **the top skills by token and by operation count, with real numbers** —
     this is the actionable finding
   - conservation verification (source total = folded total = pprof total)
   - an explicit assessment of **aggregate-only visibility**: would any single
     session have surfaced the top finding? Quantify (e.g. max single-session
     share of the top skill).
   - honest limitations: how many sessions carry the signal, whether recurrence
     is strong enough to claim anything, what you could not verify

## Rules

- Real data and real runs only. Never invent a number.
- **Do not touch `docs/agentpprof-paper/`** — it is a submodule another process
  is actively editing right now. Do not edit `docs/paper/` either.
- Do not commit, do not push, do not modify git state.
- Outside of `agentpprof/`, `agent-session/`, and this report directory, do not
  modify files.
- If the honest conclusion is "the skill level is not worth adding because the
  signal is too thin", say that plainly and show the numbers that prove it.
