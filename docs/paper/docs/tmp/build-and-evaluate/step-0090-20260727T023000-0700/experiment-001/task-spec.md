# Task spec: multi-measure replay demonstration (time / file / network widths)

Autonomous agent in /home/yunwei37/workspace/agentsight-research-semantic-flamegraph.
No git commands. Deliverables in THIS directory. Deterministic replay only —
no LLM annotation calls.

## Why

The paper claims the same hierarchy replays under token, time, file-effect,
and network-effect measures (~10 mentions) but the Evaluation shows only
token and operation-count widths. Produce the real demonstration.

## Step 1: capability inventory (fast, factual)

Determine which additive measures the CURRENT agentpprof binary actually
populates for each input family:
(a) local Codex/Claude sessions (the frozen Git-case workspace
    docs/visexp/out/codex-agent-long-horizon-v1/annotation-workspace-git-v1
    and the step-0086 self-profile workspace) — timestamps exist, so a
    time/duration measure should be derivable; check what metrics the
    session adapter and workspace emit (agentpprof/src/session.rs,
    annotation_workspace.rs, profile.rs);
(b) AgentSight eBPF recordings with real process/file/network effects —
    the R114 suite artifacts (step-0007 records name them; look in
    .agentsight/experiments/ and docs/visexp/out/) hold 1,520 scoped real
    Codex effects with lineage.
Report exactly which measures are materializable today per family, and
whether small PRODUCT additions are needed (a missing time or file counter
in the adapter may be implemented as product code with a cargo test, like
the step-0086 --workspace-out work; keep it minimal).

## Step 2: demonstration on the frozen Git case (priority)

Replay the UNCHANGED Git-case hierarchy under every additional measure
available (target: time; file effects; network effects if the data
carries them). For each: exact conservation check, stock-pprof load, and
the shared `diagnose authentication` subtree's share of the focused task
under that measure (the paper reports 21.47% by count and 46.15% by
tokens; extend that table). Render each new width in the r221 paper style
into docs/visexp/out/r221-pprof-renderer-v1/ as git-multibranch.<measure>.png.
If local sessions cannot carry file/network effects, do the effect-width
demonstration on the R114 AgentSight population instead and say so.

## Deliverables

capability-inventory.md, the new .pb.gz profiles, rendered PNGs,
results.md (per-measure conservation + subtree shares + provenance),
execution-log.md. If product code changed: tests pass, changes listed.
