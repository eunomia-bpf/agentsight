# Addendum 002: prescriptive reader recipe (final attempt)

Timestamp: 2026-07-25T05:35:00-07:00
Author: root orchestrator
Supersedes the reader-invocation part of addendum-001. Everything else in
task-spec.md and addendum-001 (v2 response dirs, sequential conditions,
resume, set-aside kimi partials) stands.

The previous executor stalled investigating opencode configuration. This
addendum removes all discretion:

1. DO NOT inspect, read, or modify any opencode/kimi/grok configuration,
   home directory, or installation. No `find`/`ls`/`cat` outside the
   repository and your jail directory. Zero exceptions.
2. Create the jail once: `mkdir -p <this experiment-001 dir>/reader-jail`.
3. Reader invocation is EXACTLY this shape, executed from the harness via
   subprocess with cwd set to the jail:

   ```
   opencode run --pure "<PACKET AND INSTRUCTION TEXT>"
   ```

   with cwd=<reader-jail>. Nothing else: no flags you invent, no config
   changes, no agent files. If the packet text is too long for one argv,
   write it to `<reader-jail>/prompt.txt` and run
   `opencode run --pure "$(cat prompt.txt)"` via `bash -c` with cwd=jail.
4. The instruction inside every packet must end with: "Answer directly in
   strict JSON only. Do not use any tools, do not read or write any files,
   do not run any commands." The harness parses the FIRST JSON object/array
   in stdout; one retry with a format reminder on parse failure; then the
   frozen deterministic fallback, tallied.
5. Before the full run, validate the recipe on exactly 3 queries of the
   full-trace condition; if the reader cannot produce parseable JSON on at
   least 2 of 3, STOP and write results.md reporting that, instead of
   burning quota.
6. Then run conditions sequentially to completion: full-trace (400),
   semantic skeleton, raw skeleton, with resume support and progress lines
   in full-run-v2.stdout.log.
