# AgentProf AAAI-27 Paper Workspace

This is the active, editable paper workspace for the AAAI-27 submission target.

## Provenance

- Canonical scientific content: tracked files from
  `docs/agentpprof-paper/` at commit `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.
- Canonical content restored: 2026-07-13. The abstract, introduction,
  background, model, design, implementation, evaluation, related work, and
  conclusion begin from that source; only the LaTeX venue wrapper was
  mechanically converted from ACM `sigconf` to the official AAAI-27
  anonymous-submission wrapper.
- The source repository remains read-only. Changes in this directory are not
  synchronized back into it.
- Previous Chinese LaTeX paper snapshot:
  `docs/tmp/agentpprof-paper-zh-20260711/source/`.
- The superseded pre-restore AAAI draft is preserved at
  `docs/tmp/agentpprof-paper-pre-canonical-restore-20260713T023645-0700/source/`.

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
The official deadlines are July 21, 2026 for the abstract, July 28 for the full
paper, and July 31 for supplement/code, all at 23:59 UTC-12. AAAI-27 also
requires the reproducibility checklist as a separate upload.

## Current Status

The paper again uses the original AgentProf thesis---agent observability needs
profiling, not only debugging---and its four fixed RQs: resource attribution,
real-problem localization, tag accuracy, and profiling cost. This restoration
is a content baseline, not a scientific-readiness verdict. Existing numerical
claims still require reconciliation with complete real experiments. New
evidence may strengthen those claims, but experiments do not silently replace
the thesis, story, hypotheses, or RQs.

As of 2026-07-17, a forced build produces nine US-letter pages with all main
content ending on page seven; References begin on page eight and are the only
content on pages eight and nine. All fonts are embedded Type 1,
and the anonymous source contains no author or affiliation identity.
`ReproducibilityChecklist.tex` is filled from the current experiment and paper
state and compiles separately to a two-page US-letter PDF; items not yet
supported are marked `partial` or `no` rather than overstated. Page-limit
pressure must not be resolved by narrowing the scientific contribution.
