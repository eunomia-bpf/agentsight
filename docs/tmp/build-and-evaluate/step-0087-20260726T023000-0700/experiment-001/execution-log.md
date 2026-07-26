# Execution log

Run date: 2026-07-26 (America/Vancouver)

## Constraints

- No Git command was run.
- No file under `docs/paper/` or `docs/agentpprof-paper/` was touched.
- All new experiment deliverables remain in this `experiment-001` directory.
- The backend saw only one source-only packet per call and emitted only the
  response-schema JSON; raw events contain no prohibited tool event.

## Recipe check

The interrupted attempt's ordinal-396 raw mark was reused after validation.
The first replay accidentally used the workspace virtual environment and
stopped at import time because it lacked pandas; no scorer or result ran.
The authoritative replay used:

```text
/usr/bin/python3 direct_annotation/postprocess.py preflight
```

It completed root repair, fixed canonicalization, operation/token pprof
materialization, stock-pprof readback, and the unchanged scorer over one real
trajectory. Its metrics are diagnostic only.

## Pilot

```text
/usr/bin/python3 direct_annotation/annotate.py pilot --workers 4 --timeout-seconds 1200
/usr/bin/python3 direct_annotation/postprocess.py pilot
```

The pilot selected ordinals 1--40 from the packet index's sorted session IDs.
Seven valid cached marks were reused. The interrupted ordinal-5 event was
invalid, consumed its single format retry, and then passed. The complete
40-trajectory pilot passed the binding B³ gate.

## Authorized full backend run

```text
/usr/bin/python3 direct_annotation/annotate.py full --workers 4 --timeout-seconds 1200
```

The full command reused the 40 pilot marks and the valid ordinal-396 recipe
mark. It attempted every remaining trajectory. Terminal status was 404 valid
and one failed after retry.

The required full packager was invoked:

```text
/usr/bin/python3 direct_annotation/annotate.py package
```

It failed closed on ordinal 53's missing exact-session annotation. Therefore
`direct_annotation/postprocess.py full` was not invoked: doing so would either
fail coverage or score an unauthorized partial population.

## Terminal reporting

```text
/usr/bin/python3 direct_annotation/postprocess.py incomplete
```

This command validates all retained raw marks, recomputes call/cost totals, and
writes the terminal machine-readable and Markdown reports. It does not open
official stages or compute a partial scientific score.
