# R248 OSDI Gate Review

Status: `not_weak_accept_after_review`

Two read-only subagents reviewed the current paper/evidence state after R247.
One reviewed paper claim/evidence alignment; one reviewed artifact/community
readiness. Both kept the project at OSDI Level 3, not weak accept.

## Highest-Risk Blocker

C5 still has 0 real participant responses, and C6 still has 0 real human
adequacy labels. No review, install smoke, static form, synthetic export, or
subagent finding can replace those outcomes.

## Paper Review

Must-fix boundaries:

- Do not claim developer utility without scored C5 accuracy/time/false-positive
  and confidence data.
- Do not claim tag adequacy, canonicalization quality, or promotion quality
  without R124/R190/R203 human labels.
- Keep C4 scoped to fixed and controlled workloads; broad exact lineage remains
  partial.

Applied revision:

- Tightened the abstract so it summarizes scoped lineage evidence instead of
  reading like a run log.
- Reworded the case study as a candidate decomposition that C5 must later test,
  not as proven user utility.

## Artifact Review

Must-fix boundaries:

- Make `agentpprof` discoverable from the top-level docs without changing the
  eBPF AgentSight Quick Start.
- Verify an installed `agentpprof` binary, not only `cargo run` from source.
- Provide a committed public fixture and explicit `--session-file` smoke path
  that avoids private-history discovery.

Applied revision:

- Added top-level README and CLAUDE/AGENTS guidance for no-sudo `agentpprof`.
- Added an `agentpprof` public fixture and README smoke command.
- Added R248 install smoke: `cargo install --path agentpprof --locked --force`,
  installed CLI execution, pprof readback, projection checks, privacy scan, and
  false C5/C6/weak-accept gates.

## Verdict

R248 improves paper hygiene and C7 local artifact readiness. It does not add
participant responses, human labels, external community adoption, or weak-accept
evidence.
