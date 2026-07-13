# AgentProf AAAI-27 Paper Workspace

This is the active, editable paper workspace for the AAAI-27 submission target.

## Provenance

- English source snapshot: tracked files from
  `docs/agentpprof-paper/` at commit `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.
- Snapshot date: 2026-07-11.
- The source repository remains read-only. Changes in this directory are not
  synchronized back into it.
- Previous Chinese LaTeX paper snapshot:
  `docs/tmp/agentpprof-paper-zh-20260711/source/`.

## Venue and Build

The paper uses the official AAAI-27 anonymous-submission style from the
AAAI-27 Author Kit published at <https://aaai.org/authorkit27/>.

```bash
cd docs/paper
make
```

AAAI-27 Main Track permits seven pages of main content and at most nine pages
total; pages after page seven may contain references only. The paper must remain
anonymous and use the unmodified `aaai2027.sty` and `aaai2027.bst` files.

## Current Status

The current restored-story draft compiles to seven US-Letter pages; references
begin on page six. This is a format baseline, not a scientific
readiness verdict. Existing result claims must be reconciled against the real
experiment artifacts and rerun where provenance, baseline fairness, hidden-label
separation, source fidelity, or cost measurement is not yet strong enough.
