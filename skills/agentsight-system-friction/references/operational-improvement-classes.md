# Operational Improvement Classes

Start from the observed system effect and the concrete change to the user's existing workflow. Use AgentSight system evidence to justify the change.

## 1. Reduce Blast Radius Without Slowing The User

Questions:

- Which paths, hosts, commands, ports, or process types caused avoidable risk, noise, or cleanup work?
- Which existing command wrapper, config, or hook should set default cwd, environment, path masking, localhost binding, or TTL?
- Did the run access home, secret-adjacent, external network, or workspace-external resources?
- Did containerized or sandboxed agents stay inside the expected namespace and mount/network boundaries?

Outputs: path impact board, network binding changes, service lease changes, secret-adjacent handling.

## 2. Reduce System Waste

Questions:

- Which repeated commands, wait states, CPU/RSS/IO outliers, or long windows produced little progress?
- Which tests or commands need timeout, retry budget, narrow-first strategy, caching, or automatic downgrade?

Outputs: resource heatmap, repeated command board, timeout candidates, rerun budget, cache candidates.

## 3. Lower Cleanup And Recovery Cost

Questions:

- Which processes, listeners, temp files, or workspace mutations need lifecycle management?
- What should be cleaned automatically at task end, and what should be rollback-ready?

Outputs: cleanup queue, process lifetime board, temp file lifecycle board, rollback targets.

## 4. Verify Tool, MCP, Or Runtime Policy Claims

Questions:

- Did a tool claiming read-only, no-network, workspace-local, or no-secret-access actually behave that way?
- Which controls are pass, fail, or unknown from available capture modes?

Outputs: dynamic verification matrix, behavior verdict board, workflow or configuration changes.

## 5. Improve Next-Run Evidence Quality

Questions:

- Which capture modes, join keys, schemas, or export fields were missing?
- What should be captured next time so interaction and system reports correlate cleanly?
- Were AgentSight sessions joinable with agent-native session ids, process ids, and timestamps?

Outputs: capture quality board, evidence gap map, join-key coverage board, export field changes.
