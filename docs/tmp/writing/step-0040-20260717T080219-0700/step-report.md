# Step 0040 — AAAI WRITE Gate After Full-Paper Review

## Node identity

- **Started:** 2026-07-17T08:02:19-07:00
- **Parent:** Step 0039 full-paper REVIEW
- **Gate:** WRITE
- **Target:** AAAI-27 Main Technical Track, anonymous submission
- **Paper entrypoint:** `docs/paper/main.tex`
- **Entry PDF:** `docs/paper/main.pdf`
- **Entry paper baseline:** dangling read-only stash commit
  `4f9106a8dd91edd54815f5dccc73c2c54fdbe071`; the repository was already dirty
  only because Step 0039 had updated the canonical literature map and added
  review reports. `docs/paper/` itself had no source modification at entry.
- **Entry repository HEAD:** `cfe62570412f90dc024beb34a458e6481404f1aa`
- **Branch:** `research/semantic-flamegraph-artifacts-v2`; this node will not
  create, switch, stage, commit, or push any branch or revision.
- **Read-only story source:** `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`; this node will not modify it.

## Fixed scientific contract

The root read `docs/user-instruction.md`, the complete `docs/idea-story.md`,
the complete current paper, and the complete Step 0039 independent review
before authorizing this node. The permanent contract is:

1. preserve the exact thesis, **“Agent observability needs profiling, not only
   debugging.”**;
2. preserve exactly four RQs and their order: attribution, localization, tag
   accuracy, and cost;
3. preserve operations and operation stacks as the only core abstractions;
4. preserve the original submodule problem, gap, insight, system direction,
   and contribution chain;
5. treat all quantitative values as read-only unless an existing independently
   reviewed result is copied exactly from its source report; and
6. introduce no new algorithm, RQ, metric, benchmark, experiment, or coined
   concept during WRITE.

No narrative change is authorized. The initial, immediately previous, and
proposed narratives are therefore identical at the scientific level: this
node improves the visibility and organization of already accepted evidence.

## Why WRITE is the correct next node

The Step 0039 blind read, primary-source novelty search, source-informed
reread, and independent cross-domain AAAI review agree on a 5/10 borderline
weak-reject assessment. The paper retains AAAI-level significance and uses
standard construct-matched primary metrics. The independent reviewer rejected
a new matched-reader experiment because the complete standard-MAP populations
and the completed local-first matched comparison are larger and more direct.

Three acceptance-changing defects remain, all writable from existing evidence:

1. the manuscript does not visibly defend its surviving composite against
   TraceProbe, WebGraphEval, Hodoscope, TraceGraph, Datadog/LangSmith, and
   OpenTelemetry Profiles;
2. the RQ2 headline table hides the already completed local-plus-semantic,
   local-plus-raw, and local-only comparison; and
3. the manuscript does not synthesize how each standard metric authorizes only
   its measured construct while the four RQs jointly support the thesis.

## Entry format evidence

- nine pages total on US Letter;
- pages 1--7 contain the paper body and pages 8--9 contain references;
- all fonts reported by `pdffonts` are embedded Type 1 fonts;
- the anonymous author line and AAAI-27 submission wrapper are present;
- 54 citation commands reference 40 distinct bibliography keys.

## Writing procedure

This node runs a fresh complete `iter-refine-writing` cycle with twelve serial
rounds. Each review round is read-only; the root applies accepted changes one
subsection at a time, compiles after every round, checks the paper/source diff,
and records accepted, rejected, and deferred findings in the corresponding
round report. The final round diffs the complete paper against the entry
baseline and restores any unintentional meaning loss.

Round reports live under
`iter-refine-writing-20260717T080219-0700/`. A fresh complete full-paper REVIEW
will follow this WRITE node; this report does not pre-authorize acceptance or a
new experiment.

## Current status

Rounds 0--2 are complete. The macro round surfaced and repaired the
closest-work, RQ2-table, evidence-synthesis, and conclusion defects. The micro
round recovered the page budget, moved direct RQ answers to their evidence
endpoints, made RQ3's construct-to-metric mapping explicit, and applied the
user's standard-metrics-only correction. The section-convention round repaired
RQ1's metric-to-construct wording, restored physical RQ order around the wide
figure, and aligned execution-tree wording with the cross-run semantic gap. The
current build is nine US-Letter pages and the main text concludes within page
7. Round 3 then repaired RQ2 definition order, removed an orphaned token
quantity, and clarified integrated versus standalone RQ3 field backends. Round
4 rebuilt the opening by explicit paragraph/sentence roles, separated root
cause from the closest-work gap, and added existing literal-tag results to the
summary without changing evidence. Round 5 then repaired the RQ3 input-boundary
qualifier, distinguished integrated task fields from the standalone action
backend, scoped the RQ2 answer to its actual comparisons, and separated the
nine-dataset depth sweep from 15-family adapter coverage. The user-directed
standard-metric boundary is clean: token-weighted B$^3$, Recall@20\%, and fixed
top-3 reader results are absent. The conclusion has slipped to page 8, so
Rounds 6--9 recovered the original seven-page body through meaning-preserving
sentence, word, terminology, and flow tightening. Round 10 mechanically verified
all 76 annotated bibliography entries and fixed two missing citation placements.
Round 11 restored three population qualifiers that had been lost during early
compression, after which a second fresh meaning audit returned PASS with zero
must-restore items. All twelve rounds are complete, the body ends on page 7,
and the WRITE gate is closed. The next outer state is a fresh REVIEW gate.
