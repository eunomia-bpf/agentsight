# Implementation Frontier

## Existing artifact

- `agent-session` parses native Claude, Codex, and Gemini sessions.
- `agentvis` discovers repository-related sessions, projects file actions, orders them by agent action time, computes the dynamic layout, and exports standalone HTML, SVG, PNG, GIF, and MP4 artifacts.
- `agentsight vis` delegates to the same `agentvis` library.
- The current implementation preserves no-file tool actions on the timeline and uses Git commits only as visual flashes.

## Current research-only mechanism and remaining gaps

- `agentvis research-store` constructs the registered Harness Bench checkpoint
  store directly from native Codex sessions and immutable post-round workspace
  snapshots. It accepts any completed prefix-round count and retains prior
  prompts, native tool actions, exact per-round `lstat` manifests, and source
  records needed to recompute every derived relation.
- `agentvis research-supervisor` implements exactly three automatic conditions.
  Generic can list, read, and search only the current checkpoint; Full Raw can
  retrieve the allowlisted source store; Workspace Trajectory retains those Raw
  tools and adds source-linked artifact history, snapshot-derived session
  transitions, and effects. All use one pinned model, prompt, seed, output
  schema, and returned-byte/token budget. The only output is a bounded
  `INTERVENE|ABSTAIN` decision, worker-facing message, and source IDs actually
  exposed during that call.
- The old semantic `research-score` path is not compiled or used. No human
  labels, Agent substitute labels, pathology classes, semantic scorer, or LLM
  judge participates in H6. Truth comes only from executing each continuation
  and invoking the official deterministic benchmark oracle.
- The query layer now builds explicit artifact identities and mutation revisions
  from the `h0` boundary and ordered effects. Read preserves a revision, write
  advances it, rename preserves identity while changing path, delete terminates
  the active identity, and recreate allocates a new identity. Each explicit
  scope is then reconciled against its complete exact boundary manifest. An
  observed mutation is anchored without a second revision increment; a content,
  create, or delete discrepancy without an owned mutation is retained as
  `unknown`, splits uncertain identity where necessary, and prevents the frozen
  supervisor path from starting. Boundary absence cites the manifest hash/count
  proof. This is an ephemeral deterministic projection over `agent-session`
  data, not another stored general event IR.
- `agentvis/research/harnessbench_intervention.py` is a thin driver around the
  pinned official Harness Bench Codex adapter, prompts, fixtures, hooks, and
  oracle. It snapshots after every prefix `after_round`, restores every
  condition into the same stable worker-visible execution slot, obtains one
  bounded supervisor intervention, starts a fresh worker session, and invokes
  only the unmodified executable oracle. The named Codex permission profile
  permits workspace tools while denying benchmark sources, sibling conditions,
  retained evidence, credentials, DNS, and network egress.
- Every condition writes its intervention, supervisor ledger, transcript,
  verification record, workspace manifest, worker logs, and two repeated oracle
  results atomically or is rerun as a whole block. A condition cannot cite an
  unexposed source ID. Full Raw recomputation, model/source identity, budgets,
  argv, environment, checkpoint, and worker-visible paths are checked before a
  report is admitted.
- The admitted research preflight binds native Codex calls to successful
  retained `strace` effects through exact argv/CWD, process-subtree, interval,
  and syscall-result rules. The production `agentsight vis` path does not yet
  consume AgentSight's live eBPF file observations; that product integration is
  separate from the verified research stores.
- The two admitted development episodes intentionally use Codex. Although
  `agent-session` parses Claude, Codex, and Gemini for the visualization path,
  exact source-record/action/effect binding has not yet been qualified for
  Claude or Gemini research captures. Cross-Agent generalization therefore
  remains an evaluation requirement, not a current implementation result.
- The current process tracer observes file opens and can enable aggregated
  writes, deletes, renames, directory creation, truncation, and directory
  changes. It is not yet an action-effect oracle: open and several mutation
  events are recorded at syscall entry, mutation success is not paired with the
  return value, rename does not retain both paths, relative `*at` paths are not
  fully resolved against `dirfd`, and aggregation/late file-descriptor
  resolution can erase exact action timing or ownership. Research construction
  must mark such cases `unknown` rather than treat them as successful effects.
- An earlier, now-superseded RQ1 preflight exposed two implementation errors in
  the research-only condition builder. Numeric decoded `dirfd` paths were
  resolved against workspace CWD, creating false workspace reads, and
  controller-side JSONL arrival times were used as approximate action starts,
  leaving fast syscalls outside their owning action. The repair already in this
  branch reuses `agent-session` native call IDs/timestamps and attaches system
  effects only when decoded `dirfd`, syscall result, time interval, and ownership
  close. Unresolved effects remain `unknown`; no parallel general event IR was
  added.

### Source-contract repair after the blocked preflight

The first repair now exists on the research branch:

- `agent-session::ToolEvent` retains the source-native result timestamp as
  `end_ts_ms`; Claude and Codex pair it by native call ID;
- Codex array-valued tool outputs are parsed without discarding completion
  state;
- the research adapter reads the retained native rollout through
  `agent-session`, not the controller's `codex exec --json` arrival sidecar;
- `openat`, `renameat`, `unlinkat`, `mkdirat`, `symlinkat`, and `linkat` resolve
  relative paths against their decoded directory FD, never against process CWD
  merely because the path is relative; and
- non-decoded numeric directory FDs cannot create workspace effects.

On the retained blocked coding episode, a development replay after this repair
produced 31 tool/environment actions and 1,505 selected Raw records, retained
all 78 manifest-changed paths, and reported zero unbound selected system
effects. Seventeen `agentvis`, ten `agent-session`, and fourteen `agentpprof`
tests pass. This is a source-contract development check only. It does not repair
the missing process-subtree ownership proof for shell effects, blinded
gold/scorer, treatment-name leak in retained runtime paths, incomplete
full-trace store, or the invalid static interface, and it is not RQ1 evidence.

## Closed dependency implementation

An earlier human-gold/Full-HTIR branch built an exact-state capture controller
and a fixed-reproduction constructor. Independent review found unresolved
model-step effects and cross-record boundary, time, and goal consistency, and
the author subsequently closed the human-label experiment before inference.
Those implementations are not part of the active H6 system and have been
removed from the published tree. Their dependency-only conclusions remain in
the timestamped experiment reports and the BOOTSTRAP step report; they provide
no label, diagnosis, or paper effect.

## Build and verification entrypoints

```bash
cd agent-session && cargo test
cd ../agentvis && cargo test
cd ../collector && cargo test
```

The static-full-context RQ1 preflight is terminally blocked. Its independently
reviewed queryable successor under `experiment-20260720T021317-0700/` produced
two verified stores, versioned lifecycle projection, exact-boundary replay, and
a clean unused blind archive. On 2026-07-21 the author closed that experiment
before inference and rejected human annotation. Those artifacts remain
provenance for source and broker mechanics only.

The independently accepted Harness Bench task-058 pause/fork/inject plan is
implemented under
`docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/`.
The no-model preparation gate and strict real P0 have passed. P0 parsed two
independent prefix sessions into 133 Raw records and seven actions, proved
checkpoint/fork/configuration parity and actual worker-tool isolation, and
obtained identical repeated official-oracle results. No intervention, Full Raw,
and Workspace Trajectory each scored 0.8594; Generic scored 0.9219. All three
supervisors made zero retrieval calls, so the strict provenance schema required
empty source lists. This validates execution mechanics but gives no evidence of
a trajectory mechanism on that checkpoint.

The preregistered six-task no-intervention headroom gate is complete. Its scores
were 0.6154, 0.8594, 1.0, 1.0, 1.0, and 0.4994; only 3/6 were below 0.95, so the
full four-condition matrix is not admitted. The current implementation must not
run only the three lower-scoring tasks or weaken the threshold after observing
the result. The next implementation target depends on an independently reviewed,
scientifically distinct objective workload plan. No new general event IR,
diagnosis stack, semantic scorer, or LLM grader is needed.

The development driver removes any controller credential file that Codex copies
into its runtime home immediately after every adapter call, including failed
calls. All such files from the retained prepare/P0/headroom directories were
deleted without being read, and a repository-wide check under `docs/tmp` found
none remaining.

The future-run path also rejects any supervisor decision made before at least
one available evidence-tool call, rejects supervisor-only tool names in
worker-facing advice, retains both official-oracle payloads plus their joint
hash, and deletes redundant runtime homes after successful archival. These are
protocol/auditability repairs identified by the independent result review. They
were not rerun on the inspected Harness Bench tasks and do not alter the closed
headroom result.
Prototype visuals, source capture, packaging, and mechanism tests do not close
any paper RQ.
