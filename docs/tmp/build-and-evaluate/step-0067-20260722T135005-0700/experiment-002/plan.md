# Experiment Plan: RQ2 multi-session user-value case

## Research Question

- **RQ exactly as written in the paper:** RQ2 asks whether target-blind profiles
  place independently annotated problems earlier than alternative
  organizations.
- **Specific uncertainty tested here:** before another population score is
  meaningful, can the approved three-file annotation workspace express a real
  multi-session agent task as a variable-depth semantic profile that lets a
  user locate repeated expensive work and distinguish it from terminal work,
  while retaining the concrete source calls underneath?
- **Why the answer matters:** the existing complete-path mark experiment proves
  replay and partition quality but uses a superseded interface and a dense
  figure. If the simplified `tag/parent/next` workspace cannot produce a
  readable, useful stock-pprof profile, further backend comparisons optimize
  the wrong artifact.

## Paper-Value Admission

- **Planned role:** supporting.
- **Largest credible paper story this experiment could unlock:** AgentPProf can
  turn many real agent sessions into a conventional profile over persistent
  task responsibilities, so a user can answer where agents repeatedly spend
  resources and which terminal-looking work fails to establish the requested
  outcome.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:**
  semantic stacks may be benchmark groupings that score acceptably but do not
  form a useful profiler view over real source evidence.
- **Independent evidence added:** a fresh manual root-Agent annotation using the
  new minimal contract, executed through the implemented CLI and inspected in
  stock Go pprof. Existing marks are evidence and source material, not imported
  as the new annotation.
- **Why the result is not tautological or already settled:** a syntactically
  valid pprof and a B-cubed score do not establish that the final aggregate is
  readable or answers the fixed user questions.
- **Paper decision if positive:** retain the three-file workspace as the product
  annotation boundary and proceed to automatic backends and full RQ scoring.
- **Paper decision if contradictory, mixed, or inconclusive:** repair the
  workspace projection or annotation relation without changing RQ2, the thesis,
  or the four-RQ structure; do not scale a representation that users cannot
  inspect.
- **Best alternative experiment:** scoring another backend on all three RQ2
  workloads. It has lower decision value until the user-facing profile
  representation is shown to work.

## Expected And Alternative Outcomes

- **Current expected answer:** a small number of manually chosen nested
  boundaries will make the repeated Git-deployment sessions readable and expose
  the already source-supported SSH diagnosis concentration.
- **Strongest competing explanation:** any apparent insight comes only from
  prose written after inspecting the trace; the flame graph itself remains a
  dense restatement of session/tool fields.
- **Contradictory result:** stock pprof cannot aggregate shared tags across all
  sessions, cannot retain source drilldown, or does not make the fixed repeated
  and terminal paths visible without reading the post-hoc explanation.

## Published Precedent And Real Assets

- **Closest protocol/tool:** standard pprof stack aggregation and stock
  `go tool pprof` focus/drilldown.
- **Real assets:** the existing complete long-horizon CodeTraceBench-derived
  collection and all three complete `git-multibranch` sessions already selected
  from it; the repository's release AgentPProf binary; stock Go pprof.
- **Reused:** source-visible turns, provider-reported token weights, stable
  source IDs, the three-session task-family selection, and the already verified
  task totals.
- **Necessary glue:** one source adapter that materializes the three-file
  workspace and the minimal Rust annotation-workspace implementation. No custom
  renderer, frontend, benchmark, metric, or synthetic trace is admitted.

## Comparison

- **Proposed method:** manually produced `tag/parent/next` annotations applied
  recursively to the current working trace.
- **Main baseline:** the already generated source-native profile over the same
  sessions and weights, representing the competing position that the emitted
  session/turn/action hierarchy is sufficient.
- **Why a matched view is needed:** both profiles must cover exactly the same
  source nodes and token mass; otherwise readability could come from selecting
  different data rather than the semantic organization.
- **Controls:** operation-count and token-width profiles from the same
  annotation; exact mass conservation; source-node drilldown; invalid crossing
  annotation rejection.
- **Conclusion if baseline matches or wins:** the new semantic annotation has
  not yet added user value and should not be scaled merely because it is more
  expressive.
- **Fairness:** identical three sessions, source evidence, and additive weights;
  only the semantic annotation differs.

## Workloads And Metrics

- **Real workload:** all three complete `git-multibranch` sessions in the
  registered 41-session long-horizon collection.
- **Primary assessment:** answer three fixed case questions directly from stock
  pprof plus its source labels: where work repeats, which shared responsibility
  dominates tokens relative to operation count, and whether terminal validation
  supports the original task.
- **Correctness:** exact source-node coverage and mass conservation against the
  existing verified 489 operations and 4,558,192 provider-reported tokens.
- **Readability:** the opened graph must show a shared semantic prefix across
  multiple sessions, naturally uneven depth, and concrete source leaves; depth
  itself is not optimized or scored.
- **Repetitions:** deterministic construction; one complete run per width is
  sufficient, followed by independent recomputation and visual inspection.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | dependency | one complete Git session | new workspace CLI | 1 | prove real trace, annotation, folded, and pprof path runs |
| case-count | proposed | all three Git sessions | manual recursive annotation | 1 deterministic | test shared structure and source drilldown |
| case-token | proposed | all three Git sessions | same annotation, token width | 1 deterministic | test resource-concentration explanation |
| native | baseline | same three sessions | existing source-native profile | reused | test whether semantic organization adds visible information |

## Execution

- **Authoritative workflow:** build and test the Rust CLI, materialize the real
  workspace from existing source artifacts, edit only `annotation.json`, then
  run `agentpprof --annotation-file ... --view operations|tokens -o *.pb.gz`.
- **Real preflight:** one full Git session, not a generated fixture.
- **Full completion:** all three sessions represented; both widths conserve
  mass; CLI tests pass; stock pprof opens both profiles; the root Agent opens the
  rendered graph and writes a source-grounded case analysis answering all three
  fixed questions.
- **Raw-result path:** `docs/visexp/out/annotation-workspace-git-case-v1/` and
  this experiment directory.
- **Recovery:** workspace files are deterministic and may be regenerated from
  the existing external source artifacts; no new control state is introduced.

## Interpretation

- **Positive:** the profile itself exposes shared repeated and terminal work,
  with source drilldown supporting the explanation.
- **Negative:** the semantic frames fragment by session, obscure source leaves,
  or require the prose to invent a pattern that stock pprof does not display.
- **Mixed:** one width is useful but another fragments, or the paths read well
  but source evidence cannot be recovered.
- **Target artifact:** one readable stock-pprof token flame graph, an optional
  operation-count companion for the resource-order reversal, and a detailed
  Markdown case study. Figures are inspection derivatives; `.pb.gz` remains the
  product output.

## Reproducibility Notes

- Use the current branch's release AgentPProf and the installed Go pprof.
- Preserve exact source session IDs and additive weights.
- The manual annotation is a product/user-value case, not an automatic-backend
  accuracy result and not a replacement for the later full RQ2/RQ3 matrices.
