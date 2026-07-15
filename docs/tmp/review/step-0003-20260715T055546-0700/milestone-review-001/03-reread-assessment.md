# Full-Paper Reread and Provisional Assessment

Timestamp: 2026-07-15T06:05:00-07:00
Parent: `02-external-search.md`
Objective: reassess every section and claim-bearing figure after source verification

## Reread results

The problem remains real rather than a strawman. The multi-method census shows
that repository-level agent identity is fragmented across channels, and the
trajectory literature shows that process contains procedural information not
captured by outcome scores. The paper's central principle is coherent and
memorable: **process, outcome, and endpoint are complementary evidence, and a
visual instrument must preserve their disagreements.**

The artifact realizes that principle consistently. Lifetime discontinuities,
right censoring, zero/one/many candidate sets, separate Git co-change and
read-before-write graphs, separate native vendor and Git author, and removal of
line attribution after the failed gate all follow from it. The negative RQ1
result strengthens rather than weakens the evidence contract.

The paper nevertheless fails the full-paper evaluation bar. Figure 1 proves
that a polished interface exists, not that its visual coordination supports a
decision. Table 1 maps views to questions but no case study, task experiment,
or usage trace answers them. The “RQ2 experience” paragraphs are author
interpretation of expected visual affordances. The “RQ3 responsiveness” result
is valid implementation evidence but corresponds to the project contract's
RQ4, not review utility.

## Ranked findings

### Blocker 1 — visualization value is unevaluated

- **Claim/location:** abstract/contributions describe a working visual
  instrument; RQ2 says the atlas exposes layer disagreement.
- **Failed inference:** rendering several inherited encodings from one model
  does not show theory recovery or decision value.
- **External evidence:** Merino distinguishes design-study/case evidence from
  task experiments; Githru grounds requirements and evaluates real history
  tasks; RECAP supplies a 41-person deployment.
- **Route:** EXPERIMENT_GATE.
- **Repair:** execute the frozen four-condition review-task study or, at
  minimum for a design-study venue, an in-situ multi-reviewer case study with
  recorded discoveries, answer keys, and negative-control tasks.

### Blocker 2 — promised RQs were substituted

- **Claim/location:** Evaluation announces three paper RQs, but project memory
  promised behavioral replication, review utility, and long-horizon scale.
- **Failed inference:** renaming qualitative inspection and latency as RQ2/RQ3
  does not complete the empirical program.
- **Route:** EXPERIMENT_GATE, then WRITE_GATE.
- **Repair:** retain the original four-RQ architecture and mark RQ2/RQ3
  explicitly unexecuted in an artifact/experience submission, or complete them
  before presenting a full empirical paper.

### Major 1 — closest systems outscale the study

- RECAP has a multi-week, 41-student deployment; the atlas has three sparse
  days from one repository and two mature days. “Long-horizon” is currently a
  span property, not continuous observation.
- The decisive repair is a second repository and at least one continuous
  matured week with usable writes from every claimed vendor.

### Major 2 — scale baseline is missing

- Perfetto supports the exported format and large-trace acceleration; the paper
  does not compare load/navigation or disclose exporter throughput.
- Add equivalent-input Perfetto and raw-table baselines, export throughput,
  p95 interaction latency, artifact inflation, and synthetic scaling clearly
  separated from semantic real-history evidence.

### Minor findings

- The exact-hunk experiment occupies substantial space relative to the visual
  contribution, yet real-history selection is descriptive only.
- Heuristic astronomy labels are memorable but have no fixed statistical
  validation; the current “inspection vocabulary” caveat is correct.
- The monolithic 6.13 MB JSON and 606 KB gzip JS bundle are appropriately
  disclosed; code splitting is a product improvement, not a paper blocker.

## Larger-claim opportunity

The biggest credible story is not “we built many charts.” It is: **when
software is produced by ephemeral agents, trustworthy review must shift from a
single artifact to disagreement-aware process/outcome/endpoint evidence, and
coordinated views let humans detect failures that any single layer hides.**
The current system nearly instantiates this claim but has not tested the human
half.

## Decisive experiment

Run the frozen four tasks under Git-only, native-event table, complete joined
table, and coordinated-atlas conditions on multiple mature repositories. The
primary test is an interaction between task evidence requirement and condition:
the atlas should improve accuracy/time only for tasks spanning layers, while
the Git-only negative-control task should show no benefit. This single design
would distinguish information gain from visual coordination and establish the
larger principle.

## Provisional verdict

**Incomplete but promising; reject as a full research submission, acceptable
as a transparent artifact/experience report if labeled accordingly.** The next
node audits cycle changes and user intent before final routing.
