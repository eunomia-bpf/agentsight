# Independent Capture-Dependency Result Review

Reviewer: independent research reviewer `capture_result_review`
Scope: capture mechanics and four excluded development workloads only
Paper effect: none

## Round 1 — BLOCK

The reviewer independently confirmed that the first mechanics fixture and four
development workloads genuinely ran, retained eight distinct top-level Codex
sessions, changed both goal states, and leaked no credential. The evidence did
not satisfy the approved exact-state protocol:

1. the outside-writer check did not prove mount identity, writable mount-handle
   isolation, privileged-writer scope, or fail-closed `/proc` access;
2. boundary records were not made durable before thaw;
3. unfinished-effect rejection depended only on a cooperative in-flight flag;
4. M1/M2/audit/freeze/sync/command provenance and the executed controller were
   not independently retained and content-bound;
5. a partial freeze failure could skip thaw;
6. `RuntimeDirectoryPreserve=yes` could retain a copied credential after a
   controller crash;
7. outputs were not access-restricted; and
8. the aggregate session-ID check had a false-PASS path.

The reviewer admitted only repair followed by a complete mechanics and four-
workload rerun. The original outputs remain failed development provenance, not
scientific evidence.

## Repair

The controller now mounts a private ext4 image with systemd `MountImages` inside
the writer mount namespace. A root capture helper joins that namespace while
remaining outside the frozen writer cgroup. It binds the mount path to one ext4
device/mountinfo row, proves that only frozen writers plus the capture helper
share the namespace, audits outside same-UID processes and path handles, and
states the host-root/PID-1/capture-helper TCB explicitly.

Every accepted boundary separately retains M1, M2, archive reconstruction,
freeze, mount, outside-writer, `syncfs`, and source/effect records. The archive,
boundary, and acceptance seal are fsynced before thaw; thaw has a separate
record. Freeze cleanup is armed before the freeze write. The exact controller
bytes/hash and every systemd/capture command's stdout, stderr, return code, and
hashes are retained.

Credentials are injected by systemd `LoadCredential`, copied only into a
non-preserved DynamicUser RuntimeDirectory, and excluded from outputs. A canary
unit is killed with `SIGKILL` and must leave neither runtime nor credential
directory. Outputs use `0700` directories, `0600` files, and a `0500` retained
controller. The session check requires exactly one thread ID in each native
session file and uniqueness across the pair.

## Round 2 — PASS

The reviewer independently recomputed all 16 new accepted boundaries: four in
the final mechanics run and three in each of four real development workloads.
M1, M2, archive manifests, tar modes/bytes, canonical hashes, archive hashes,
acceptance seals, freeze/thaw order, mount/audit/sync/effect records, command
hashes, and controller bindings all match.

The final mechanics output is:

- `raw/capture-mechanics/preflight-repair-final-20260719T232531-0700/`

The four new excluded development outputs are:

- `raw/agent-workloads/repaired-coding-1-20260719T232655-0700/`;
- `raw/agent-workloads/repaired-coding-2-20260719T233038-0700/`;
- `raw/agent-workloads/repaired-research-1-20260719T233038-0700/`; and
- `raw/agent-workloads/repaired-research-2-20260719T233038-0700/`.

They contain eight distinct completed `codex_exec` sessions and meaningful
non-cache workspace changes after both goals. The deliberately unfinished
asynchronous write is rejected from a pending source/effect transcript entry
and appears only after completion. No credential/token pattern, runtime,
credential directory, ext4 image, transient unit, supervisor inference, or
paper-effect inference remains.

**Disposition:** the repaired capture-mechanics/development dependency passes.
This PASS does not admit target truth, tested views, broker/baseline execution,
supervisor inference, diagnosis claims, or paper-effect claims.

## Full-HTIR Dependency Review — Terminal BLOCK

A separate independent reviewer inspected the deterministic Full-HTIR baseline
constructor in three rounds. Round 1 rejected the arbitrary-path official
HarnessFix runtime because it could consume evaluator output and infer effects
from command text; the route was deleted. Round 2 confirmed the leak removal but
rejected self-attested registry compatibility, shallow flow/anchor semantics,
and a nominal rather than executable four-level ladder. The replacement then
read and hashed the registry, validated exact spans/reuse/support, bound anchor
identity to snapshots, rejected call conflicts, and projected equal Raw
membership across all four levels.

Round 3 confirmed those repairs and the eight fail-closed unit tests, then found
two remaining validity defects. Model TraceSteps could still omit the required
explicit effect/no-effect/unknown record, and effects/anchors/snapshots were not
fully constrained to the source call's boundary, time, and effective goal.
Both defects can create stale or misattributed harness evidence. Because this is
the third BLOCK, the proposal is terminally closed under the review contract.

**Disposition:** capture mechanics remain a valid dependency result, but the
overall B9 feasibility experiment fails its mandatory Full-HTIR dependency and
returns to the idea gate. The registry is not frozen, registered capture is not
started, and supervisor inference remains forbidden. There is no fourth review
of this proposal.
