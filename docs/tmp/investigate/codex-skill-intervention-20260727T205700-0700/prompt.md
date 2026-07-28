# Task: can we build a "profile → optimize skills → re-profile" case study from EXISTING data only?

You are investigating a feasibility question for the AgentProf paper. Do not
write paper text. Produce one report. Be honest: "not feasible from existing
data" is a fully acceptable and useful answer.

## The question

The paper's thesis is **"Agent observability needs profiling, not only
debugging."** Every evidence chain currently stops at *correspondence* (the
profile matches independently annotated real problems, RQ2). Nothing closes the
classic profiler loop:

> measure → change something → re-measure under the same hierarchy → the
> attributed share moved.

We want a Case Study 4 / RQ5 that closes that loop by using AgentProf's own
self-profile to **optimize the agent's skills or `CLAUDE.md` rules**, then
showing the targeted responsibility's share change.

**The decisive question for you: can this be derived from data that already
exists on disk, with NO new agent sessions run?**

## The natural-experiment angle to test first

The 42-session self-profile corpus (Case Study 3) covers the agents that built
this very repository, spanning the project's own history. During that history
`CLAUDE.md` and `.claude/skills/` were repeatedly changed — those change points
have exact commit timestamps:

```
git log --follow --format='%H %ad %s' --date=iso -- CLAUDE.md
git log --format='%H %ad %s' --date=iso -- .claude/skills
```

So a natural experiment may already exist: split the 42 sessions by timestamp
around one such change, **replay both halves under the SAME frozen semantic
hierarchy** (this is exactly what AgentProf's measure-projection design allows —
the boundaries and names do not change, only which sessions are folded), and ask
whether the responsibility targeted by that rule change dropped its share.

Test this angle seriously, then look for any better one you find in the data.

## Where the data is

Repo root: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`

- `.agentsight/experiments/*/` — annotation workspaces (`trace.jsonl`,
  `annotation.json`, `stacks.folded`). Find the one behind the 42-session
  self-profile; if it is not there, find where the self-profile was produced.
- `docs/visexp/out/r221-pprof-renderer-v1/selfprofile.*` — the rendered
  self-profile figures (tokens, operations, file-read, file-write, network).
- `agentpprof/` — the Rust CLI (`cargo run` / built binary). No sudo needed. It
  reads local Codex/Claude session logs and emits standard pprof.
- `~/.claude/projects/` and `~/.codex/` — the raw local session histories the
  self-profile was built from (18 Codex + 24 Claude Code sessions).
- `docs/evaluation.md` — the running evidence log. **Read Step 0013 and Step
  0014 first**: a "downstream intervention" claim has already been explicitly
  rejected once as a rebrand of existing results. Do not repeat that mistake.
- `docs/idea-story.md` — the story invariants.

## What a valid answer must handle

1. **Which responsibility?** Name a concrete operation/subtree from the actual
   self-profile that is (a) recurring across sessions and (b) plausibly
   removable by a skill or `CLAUDE.md` rule. Report its real measured share.
   Avoid ones that are merely large-but-necessary work.

2. **Is there a real change point?** Give the commit, date, and what the rule
   change actually said. It must plausibly target the responsibility from (1).

3. **The task-mix confound — this is the killer.** Sessions before and after a
   change do different work, so a share drop may just mean the task mix changed.
   State explicitly whether the existing data supports any control:
   matched tasks, per-task normalized share, a placebo responsibility that the
   rule should NOT have affected, or anything else the data actually permits. If
   no credible control is available from existing data, say so plainly.

4. **Sample size.** How many sessions land on each side of the split? If one
   side has a handful of sessions, say the result would be anecdotal.

5. **Conservation.** Any replay must preserve exact additive conservation.
   Verify it rather than asserting it.

## Deliverable

Write `report.md` in **this directory**
(`docs/tmp/investigate/codex-skill-intervention-20260727T205700-0700/`) with:

- **VERDICT** on the first line: `FEASIBLE FROM EXISTING DATA`,
  `FEASIBLE ONLY WITH NEW SESSIONS`, or `NOT FEASIBLE`
- What data you actually found and inspected (exact paths, exact counts)
- Any real numbers you computed, with the command that produced them
- If feasible: the concrete design, the control for the confound, and the
  expected strength of the claim
- If not: precisely what is missing, and the cheapest real experiment that
  would supply it
- A short list of anything you could not verify

## Rules

- Real data only. Never invent a number. If you cannot compute something, say
  so.
- Read-only with respect to the paper: do **not** edit `docs/paper/` or
  `docs/agentpprof-paper/` (the latter is a submodule another process is
  editing). Do not commit anything, do not touch git state.
- You may create files only inside your own report directory above.
- Prefer computing over guessing: run `agentpprof`, parse `stacks.folded`, count
  sessions.
