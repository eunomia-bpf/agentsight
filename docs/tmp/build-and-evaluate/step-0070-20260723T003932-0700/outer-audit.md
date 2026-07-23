# Step 0070 Outer Audit

## Verdict

**PASS.** EXPERIMENT, WRITE, and REVIEW completed without changing the thesis or
the four author-fixed RQs.

## User-Intent Audit

- Operation tags are mechanically limited to one to three words.
- The implemented and evaluated convention is action-first
  `verb + object + optional qualifier`; names are reusable rather than
  benchmark-, task-, model-, tool-, repository-, or file-specific.
- The fixed canonical mapping supports first-verb roll-up without discarding
  the complete operation identity.
- AgentPProf still emits only `.pb`/`.pb.gz`. The R221 script is an isolated
  paper/inspection renderer that reads standard pprof through
  `go tool pprof`; no product frontend was added.
- The paper includes two complete multi-session case studies and five
  pprof-derived figures with variable-depth semantic operations and source
  LLM/tool leaves.
- No branch was created or switched.

## Story And RQ Audit

The authority remains:

> Agent observability needs profiling, not only debugging.

The four RQs remain attribution, real-problem correspondence, automatic
structure accuracy, and cost. The recursive source-tree/operation-stack model
is unchanged. This cycle clarifies the evaluated A2 algorithm and evidence
boundaries; it does not replace the story, narrow an RQ, or invent a new
construct.

## Evidence Audit

- **RQ1:** The real Git case retains 41-session population context and three
  repeated executions. It demonstrates one necessary multi-resource
  attribution capability under a fixed hierarchy: operation count and token
  width expose different bottlenecks. The paper does not generalize its ratios
  beyond this population.
- **RQ2:** Complete, fair current-algorithm replay covers 1,756 sessions and
  27,346 operations. Final automatic Agent+Evidence MAP is
  0.791/0.432/0.259 and exceeds raw action on all three workloads. Canonical
  naming alone improves HINT; the other two paired intervals include zero.
  Source-evidence effects are positive on all three.
- **RQ3:** The latest adopted A2 result remains 0.704 ordinary B-cubed F1 and
  0.394 boundary F1 over all 405 CodeTraceBench trajectories. No naming-only
  change was incorrectly treated as a new structure experiment.
- **RQ4:** The latest fixed-input core cost remains 1.17 seconds and 464.5 MiB
  for 27,765 operations; direct A2 replay remains 0.61 seconds and at most
  308.9 MiB for 20,866 operations. Every headline now states that marks are
  fixed before this timing begins.

The invalid first AgentProcess naming comparison is retained only as audit
history and is not used by the paper.

## Case-Study Audit

### Git deployment

The count and token profiles use identical boundaries over 489 operations and
4,558,192 provider-reported tokens. The shared `diagnose authentication`
subtree contains 105 operations (21.47%) but 2,103,587 tokens (46.15%).
Source drilldown shows that none of the three runs established the requested
password-authenticated `git@localhost` endpoint.

### AgentReward differential

The signed profile aggregates all 338 bad-good pair occurrences from 440 real
trajectories over 125 mixed-outcome tasks. `recover interaction` accounts for
44.6% of bad-side versus 12.0% of good-side occurrences; `report completion`
accounts for 1.8% versus 5.1%. Recovery exposure corresponds to independent
expert looping at AP 0.634 versus prevalence 0.398, without a causal claim or
unsupported recursive-over-fixed superiority claim.

Both cases answer explicit user questions and preserve source evidence for
drilldown.

## Validation Audit

- independent experiment review: final `PASS`;
- independent Grok complete-paper review: final `PASS`, 97/100;
- `cargo test --manifest-path agentpprof/Cargo.toml`: 78 tests passed;
- canonical comparison tests: 7 passed;
- AgentReward Python tests: 6 passed;
- all three current comparison artifacts rerun under complete fairness checks;
- stock pprof reads the Git operations, Git tokens, and AgentReward signed
  profiles;
- `latexmk` produces the 12-page `docs/paper/main.pdf` with all five current
  case figures and no LaTeX error.

## Transition

Step 0070 is complete. Any future experiment must start from the current paper
and target a paper-level uncertainty; it must not reopen canonical naming or
replace these complete runs merely to search for a larger number.
