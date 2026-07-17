# Round 11 — Meaning Preservation

## Node identity

- **Started:** 2026-07-17T14:50:00-07:00
- **Completed:** 2026-07-17T15:05:00-07:00
- **Parent:** Step 0040 WRITE gate
- **Entry baseline:** read-only dangling commit
  `4f9106a8dd91edd54815f5dccc73c2c54fdbe071`
- **Procedure:** a fresh independent read-only subagent read the complete user
  instructions, idea story, paper, bibliography, Round 0--10 reports, and full
  paper diff from the entry baseline. After one restoration, a second fresh
  read-only subagent repeated the complete meaning audit. No agent performed a
  Git operation.

## First audit verdict

The first audit returned **REVISE: 1 MUST-RESTORE, 0 SHOULD-RESTORE**. Round 1
compression had silently removed three nonredundant population qualifiers from
the Evaluation overview:

1. the 325 local histories were collected over multiple months;
2. the 15 annotated families are real-agent or human execution families; and
3. their domains include mobile/GUI, not only generic GUI.

No prior round finding authorized those deletions. The root restored all three
qualifiers compactly and synchronized the Chinese comment. It did not restore
redundant “concurrent control” wording because the full RQ1 protocol already
states and tests that condition immediately below.

The first reviewer classified every other change as authorized: direct removal
of nonstandard metrics; relocation rather than deletion of the flamegraph;
standard-MAP RQ2 expansion; source-fidelity corrections in RQ3; meaning-
preserving algorithm prose compression; closest-work additions; and the
recorded sentence, terminology, flow, and citation repairs.

## Fresh post-restoration verdict

The second independent audit returned **PASS with zero MUST-RESTORE items**.
It verified:

- the exact thesis appears unchanged in Abstract, Introduction, and Conclusion;
- exactly four byte-identical RQs remain in the fixed attribution,
  localization, tag-accuracy, and cost order;
- operations and operation stacks remain the only core abstractions;
- the multi-month, real-agent/human, and web/API/coding/mobile/GUI population
  qualifiers are restored;
- no story, mechanism, algorithm step, evidence, number, baseline, population,
  protocol, citation, or necessary claim qualifier was unintentionally lost;
- token-weighted B$^3$, Recall@20\%, fixed top-3 reader, and model-reader
  protocols remain absent;
- paper-facing metrics are the cited standard outcomes; and
- `docs/agentpprof-paper` is absent from the diff, clean, and remains at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

This PASS concerns meaning preservation, not the absence of scientific
objections. A fresh whole-paper REVIEW gate remains mandatory.

## Final build

The restored paper compiles to nine US-Letter pages. All body content ends on
page 7, references begin on page 8, and there is no undefined citation/
reference, multiply-defined label, or overfull warning.

## WRITE gate disposition

All twelve `iter-refine-writing` rounds, numbered 0--11, are complete. The
WRITE gate closes with no open must-fix item. The next outer state is REVIEW:
first verify the current official AAAI format constraints and read-only
submodule state, then run a fresh cross-domain full-paper review.
