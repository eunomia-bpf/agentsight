# Step 0065 — Agent-addressed operation stacks and collection case studies

Timestamp: 2026-07-21T23:48:09-07:00
Phase: BUILD_AND_EVALUATE
Current gate: EXPERIMENT
Status: coherent interface-and-case increment complete; automatic-backend
comparison remains in the EXPERIMENT gate

## Gate entry and authoritative intent

The root read `docs/user-instruction.md`, `docs/questions-for-author.md`, the
complete current `docs/idea-story.md` frontier, `docs/evaluation.md`,
`docs/design.md`, `docs/implementation.md`, the latest completed Step 0064,
and the Step 0061 review that opened nested task/subtask construction under
RQ3. The active user instructions require a simple recursive segmentation
framework, Agent-produced stable-ID boundary marks, a reusable operation-name
pool, no regex-selected semantic boundary, variable depth, pprof-only product
output, no frontend, at least two useful case studies, and a collection of many
complete sessions as the primary unit of every case study.

The thesis and four paper RQs remain unchanged. This step does not replace the
paper story or claim that a product case validates automatic hierarchy
accuracy. It implements the common mark interface first and completes two
collection-level cases. The matched automatic CodeTrace comparison remains the
next inner EXPERIMENT action rather than being hidden by the case results.

## Node 0065-E1 — paper-value admission and experiment plan

- **Question:** Can one stable-ID interface accept task-boundary decisions from
  an Agent or a traditional algorithm and produce variable-depth operation
  stacks without building a second visualization product?
- **Inputs:** Existing normalized operations and source evidence IDs; retained
  recurrence, Qwen, AgentCap, CodeTraceBench, and AgentRewardBench artifacts;
  the product rule that AgentPProf emits only `.pb`/`.pb.gz`.
- **Method:** A Markdown experiment plan selected RQ3 for the flat-partition
  accuracy question, separated exact mark replay from scientific accuracy, and
  defined pprof-only collection cases. Three serial independent plan-review
  rounds repaired the plan's initial overreach and ended in PASS.
- **Decision:** Admit the interface and collection cases. Do not treat mark
  replay as nested-boundary accuracy. Do not change the fixed RQ or thesis if an
  automatic backend fails.
- **Record:** `experiment-001/experiment-plan.md` and
  `experiment-001/plan-review.md`.

## Node 0065-E2 — stable-ID operation-mark implementation

- **Question:** What is the smallest product contract that lets an Agent mark
  transition locations and name the resulting operation path?
- **Input:** One normalized operation JSONL plus one read-only JSON mark file.
  JSON is an input data format, not a pipeline gate or second product output.
- **Implementation:** The mark file declares a sequence field, replay-stable
  source ID field, one shared semantic operation-name pool, and sparse marks
  `(sequence, start source ID, full semantic operation-ID path)`. AgentPProf
  applies field mappings, expands marks over the complete source sequence,
  applies query filters, and folds the repeated `operation` field into the one
  pprof output.
- **Fail-closed behavior:** Missing/multivalued sequence or IDs, duplicate IDs,
  absent first marks, unknown/out-of-order marks, empty paths, unknown semantic
  IDs, post-normalization display/source-sequence/source-ID collisions, stacks
  that omit `operation`, recurrence induction, non-operation views, local
  expanded inputs, and marked signed differences are rejected rather than
  approximated.
- **Evidence preservation:** The configured source sequence and source ID are
  carried as `source_session` and `evidence_id` pprof labels.
- **Scope:** No frontend, renderer, SVG, folded stack, HTML, JSON profile, cache
  output, Git protocol, or new paper term was introduced.

## Node 0065-E3 — collection case 1: repeated AgentCap reviews

- **Question:** Can one semantic profile answer effort, repair evolution,
  conclusion, recurrence, and exception questions across complete reviews?
- **Population:** Four complete real AgentCap Codex review sessions (R024,
  R025, R035, and R081), 326 operations total. No one session is presented as a
  case study.
- **Method:** The root Agent read all indexed operation summaries and emitted
  64 sparse marks using a shared pool of 29 semantic operation names. The
  resulting one pprof contains 62 unique stacks at depth three through five.
- **Fixed protocol:** `experiment-001/case-study-protocol.md` was fixed after
  readability and conservation smoke checks and before focused interpretation.
- **Result:** Fix verification accounts for 125/326 operations and decomposes
  into scope recovery, artifact validation, fix inspection, documentation
  audit, focused tests, and task-specific branches. Large evidence-gathering
  paths remain separate from eight terminal reporting operations. Shared names
  aggregate recurrence without deleting R024, R035, and R081 exceptions.
- **Artifact:**
  `docs/visexp/out/agentcap-agent-recursive-v1/agentcap-review-operations.pb.gz`,
  7,410 bytes, SHA-256
  `6c086ac1f33cb5b6d85ad20a0bdb0939ae66d0c19b55a040c11f9a1e686835c9`.

## Node 0065-E4 — collection case 2: aggregate differential profiling

- **Question:** Across a broad real workload, what bad-side and good-side
  operation paths survive aggregation beyond a scalar trace score?
- **Population:** The complete independently repaired Step 0063
  AgentRewardBench population: 440 real trajectories, 125 mixed-outcome tasks,
  and 338 complete bad-good pairs spanning AssistantBench, VisualWebArena,
  WebArena, and WorkArena. The 202 successful and 238 unsuccessful sessions are
  reused within task pairings, so the report is pair-occurrence weighted.
- **Method:** Fold all 338 bad members and all 338 good members into one signed
  operation-count pprof. Individual pair profiles remain evidence drilldowns,
  not case studies.
- **Fixed protocol:** `experiment-001/case-study-2-protocol.md` records the
  collection questions, sign convention, weighting, and evidence boundary.
- **Result:** The profile contains 7,366 bad-side and 3,780 good-side operation
  occurrences. Bad-side excess exposes continuing work, exact repetition,
  stopped work, invisible-element clicks, timeouts, wrong-widget operations,
  and missing elements. Good-side excess exposes terminal, conclusion, and
  user-reporting paths. Simple step count remains the best tested scalar; the
  pprof's additional role is localization, not classification.
- **Artifact:**
  `docs/visexp/out/agentreward-diff-pprof-v1/agentreward-338-pairs-bad-minus-good.operations.pb.gz`,
  125,865 bytes, SHA-256
  `cb7a9b6f63c6ad88d2c88dca35312d6463f33308391710e876d08f8db9b13ccc`.

## Node 0065-W1 — paper integration

- **Input:** The unchanged paper and the two reviewed result boundaries.
- **Action:** Add two explicitly numbered case-study subsections. Case Study 1
  states that the Agent selected the marks and therefore does not claim
  independent nested accuracy. Case Study 2 states the pair-occurrence
  weighting, scalar baseline, absence of semantic-hierarchy gold, and
  diagnostic rather than causal/classification interpretation.
- **Narrative audit:** Abstract, introduction, motivation, design thesis, and
  four RQs were not rewritten. The new prose supports the existing
  profiling-not-only-debugging story and does not substitute a smaller thesis.
- **Artifact:** `docs/paper/main.tex` and the rebuilt `docs/paper/main.pdf`.

## Node 0065-R1 — verification and independent review

- `cargo fmt --check`: PASS.
- `cargo test --locked`: PASS, 68/68 tests (54 unit, 3 diff CLI, 9 profile-spec
  CLI, and 2 standard-trace CLI).
- `cargo clippy --locked --all-targets -- -D warnings`: PASS.
- `git diff --check`: PASS.
- Paper build: PASS, 10 pages, no unresolved citation/reference or LaTeX error.
- First independent code review found four P1 and one P2 contract issues. The
  implementation was narrowed and repaired: marked operation paths are
  authoritative over operation regex rules; post-normalization names and IDs
  fail closed; configured source evidence is preserved; unsupported views and
  differences are rejected; and unknown sequences fail.
- A convergence review then found one remaining P1: normalized source sequence
  names could collide. A global check and regression test were added, followed
  by the complete verification suite. Final convergence review is recorded by
  the outer audit.

## Scientific boundary and unresolved work

This increment establishes a useful Agent-addressed construction interface and
two source-complete, many-session product cases. It does not yet answer whether
the recursive automatic backend improves ordinary B-cubed over retained
recurrence on all 405 CodeTraceBench trajectories. AgentRewardBench provides
outcome and loop labels but no gold hierarchy. AgentCap boundaries and names
were produced by the same Agent that interprets the case. These are explicit
limits, not reasons to narrow the thesis or RQs.

The EXPERIMENT gate therefore remains active. The next action is the already
planned automatic-backend real preflight and complete CodeTrace comparison,
reusing this mark interface and retaining all sessions if admitted.
