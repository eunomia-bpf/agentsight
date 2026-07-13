# Round 3 — Logic Flow

**Started:** 2026-07-12T14:56:00-07:00  
**Completed:** 2026-07-12T15:08:00-07:00  
**Cycle/gate:** cycle 0001 / WRITE

## Review Method And Findings

A fresh read-only reviewer checked the complete paper's argument without
external search or milestone critique. It confirmed that the exact thesis is
consistent and that negative results do not refute it. Must-fix logic defects
were: hierarchy validation still dominated the abstract/background; Setup
falsely implied ranker-capacity matching for official Hodoscope; “missing
failure signal” overinterpreted AgentRx/TELBench; RQ3 conflated failed semantic
transfer with native sufficiency; and flat/native/declared/induced views were
defined inconsistently. The reviewer also confirmed that decisive positive
empirical support remains missing and must route to EXPERIMENT.

## Applied Fixes

- Ended the abstract on the broad profiling goal and explicit open decision
  value rather than hierarchy selection. Qualified local percentages as
  separation of declared prompt-tag categories.
- Distinguished the Rust substrate evaluation on local histories from fixed
  model-level adapters on public benchmarks in Abstract and Introduction.
- Corrected Setup: adapter-based views match terminal operations, visible
  inputs, scoring policy, and inspection budget; official Hodoscope retains its
  density-gap/FPS ranker and is a complete-bundle comparator, not a
  ranker-matched projection.
- Replaced every rendered empirical “missing failure signal” conclusion with
  the supported result: tested induced leaves/semantic grouping did not supply
  independently validated diagnostic signal or reliably outperform simple
  controls. The conceptual accounting-versus-diagnosis distinction remains.
- Separated RQ3 outcomes: semantic failure alone means absent transfer or an
  unresolved constructor/ranker; equality with matched grouping supports
  grouping sufficiency; only a native-view win supports native sufficiency.
- Defined flat explicitly as the one-frame manual-constructor special case;
  defined source-native as a declared path over available native fields; and
  distinguished declared and induced semantic construction.
- Made the Operation field list illustrative. The arbitrary-field schema can
  retain source IDs and native path fields when supplied; the paper explicitly
  says current evidence does not verify lineage.
- Added the Design-to-Evaluation bridge: preservation and conservation make a
  profile auditable, while RQ2 separately tests utility with an external
  decision criterion and matched alternatives.
- Marked the distributed-additive-regression regime as an untested hypothesis;
  current evidence covers only one sparse-anomaly condition.
- Added an explicit Conclusion qualification that positive decision value and
  unchanged transfer remain open.
- Softened the Profile Construction premise so free-form strings are often,
  not universally, sparse and structured native fields remain first-class.

Adapter details were retained because their exact construction is necessary to
interpret the Hodoscope negative result, but their paragraphs now open and close
on the narrow decision and bundle-level boundary.

## Scientific Routing

The thesis remains a position with an implemented substrate, not a completed
positive empirical result. RQ1 lineage, RQ2 directly measured additive decision
value and total cost, and RQ3 unchanged transfer remain experiment work. No
writing edit upgraded conservation, category separation, mapping proxy, or
negative conditions into proof of the thesis.

## Verification

All 57 citation commands, all quantitative values, all RQ meanings, and the
exact thesis were preserved. `make` in `docs/paper/` completed with exit code 0.
The PDF is nine US-Letter pages; technical content ends on page 7 and pages
8--9 contain references only. Round 4 next performs the required dedicated
abstract/Introduction rebuild procedure.
