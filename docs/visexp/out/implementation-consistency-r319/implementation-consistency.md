# Implementation Consistency R319

R319 checks that the maintained Rust semantic-profiler path, canonical docs, and Chinese paper agree on the current implementation boundary. It is not a dataset sync, not a new profiling run, and not a human/agent analyst-task result.

- Overall: `implementation_consistent`
- Checks passed: 12 / 12
- Commit at generation: `6ed97417a2faf497a5475e22b91a23062014f478`

## Checks

| Check | Status | Evidence |
|---|---|---|
| `rust_profile_spec_cli_present` | pass | agentpprof/src/main.rs defines --profile-spec, RawProfileSpec, operation_files, op_map_files, where_rules, rank_rules, rank_op_rules, and rank_mode. |
| `rust_profile_spec_override_contract` | pass | Profile specs provide operation inputs while CLI stack/rule overrides remain explicit. |
| `rust_standard_trace_cli_present` | pass | Rust CLI exposes standard trace import/export and routes imports into operation records. |
| `standard_trace_cli_test_present` | pass | agentpprof has a CLI test for standard trace export and import. |
| `rust_operation_stack_source_of_truth` | pass | Operation mapping, query predicates, stack folding, and visible rank summaries live in the Rust profile path used by operation files and trace imports. |
| `operation_predicate_documented_as_query_not_object` | pass | Docs record --where/where_rules as a query predicate over operation fields, with R321 as the implementation probe. |
| `operation_rank_policy_documented_as_projection_not_object` | pass | Docs record --rank-rule/rank_rules, --rank-op-rule/rank_op_rules, and --rank-mode/rank_mode as visible operation-stack group ranking projections, with R322/R323/R324 as implementation probes and R324 using a scrubbed visible profiler input. |
| `implementation_doc_records_current_rust_surface` | pass | docs/implementation.md records profile specs and standard trace support as current implementation. |
| `profile_spec_not_stale_pending_task` | pass | Profile-spec support is no longer listed as a pending implementation task. |
| `two_abstraction_boundary_in_docs` | pass | Design, paper, and claim setup preserve operation plus operation stack as the core model. |
| `third_abstraction_guarded` | pass | Any third-abstraction language is guarded as a non-claim. |
| `remaining_gates_are_real_research_gaps` | pass | Remaining implementation/evaluation gates are analyst utility, real trace producer import, and deeper boundary adequacy. |

## Remaining Gates

- Execute the controlled human/agent analyst study before claiming accuracy, time-to-answer, productivity, or user utility.
- Add stronger calibrated boundary/backends before claiming automatic or universal intent-boundary discovery.
- Import a real OpenTelemetry GenAI, OpenInference, or Perfetto trace producer before claiming trace-platform compatibility.
