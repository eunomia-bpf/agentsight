# Case Study 2 deterministic recomputation

All quantities were recomputed from the version-pinned frozen workspace,
pair-occurrence inputs, fixed pair manifest, and consensus expert labels. No
model was called and no annotation was changed.

## Quantity comparison

| Quantity | Paper value | Recomputed value | Match/mismatch |
|---|---:|---:|---|
| Bad--good pair occurrences | 338 | 338 | match |
| Bad-side operation occurrences | 7,366 | 7,366 | match |
| Good-side operation occurrences | 3,780 | 3,780 | match |
| Bad-side recovery occurrences | 3,286 | 3,286 | match |
| Good-side recovery occurrences | 455 | 455 | match |
| Bad-side completion occurrences | 135 | 135 | match |
| Good-side completion occurrences | 191 | 191 | match |
| Bad-side recovery share | 44.6% | 44.6% | match |
| Good-side recovery share | 12.0% | 12.0% | match |
| Bad-side completion share | 1.8% | 1.8% | match |
| Good-side completion share | 5.1% | 5.1% | match |
| Consensus expert-looping labels | 435 | 435 | match |
| Expert-looping prevalence | .398 | .398 | match |
| Recovery-exposure AP | .634 | .634 | match |
| AP minus prevalence, 95% task-cluster interval | [.181,.293] | [.181,.293] | match |
| Fixed-chain projection AP | .656 | .656 | match |
| Recursive minus fixed, 95% task-cluster interval | [-.107,.061] | [-.107,.061] | match |

No quantity mismatches the paper at its currently displayed precision.

Full-precision AP values are `0.6336880791837327` (recursive) and
`0.6559621177236952` (fixed); prevalence is
`0.3977011494252873`. The bootstrap uses seed
`20260722` and retains `10,000` draws
over `125` task clusters. The 435 consensus trajectories contain
`173` positive and `262`
negative labels.

## Exact responsibility path prefixes

The occurrence selector follows the registered harness semantics: it tests
exact component membership in each CLI-applied tool path. The following tables
make every contextual prefix through the selected responsibility explicit.

### Recovery

Exact selector: an applied operation path contains the exact component
`recover interaction`. For auditability, the prefix is the complete
path from its root through the first occurrence of that component (inclusive);
this preserves the registered membership predicate when a nested path repeats
the same label.

| Exact contextual prefix | Bad occurrences | Good occurrences |
|---|---:|---:|
| `execute browser task` → `answer information request` → `compare` → `recover interaction` | 2 | 2 |
| `execute browser task` → `answer information request` → `inspect` → `recover interaction` | 14 | 33 |
| `execute browser task` → `answer information request` → `recover interaction` | 373 | 20 |
| `execute browser task` → `answer information request` → `search` → `recover interaction` | 18 | 0 |
| `execute browser task` → `execute enterprise workflow` → `recover interaction` | 1,258 | 305 |
| `execute browser task` → `execute visual task` → `research` → `recover interaction` | 0 | 10 |
| `execute browser task` → `execute visual task` → `search` → `recover interaction` | 7 | 0 |
| `execute browser task` → `execute website task` → `recover interaction` | 1,614 | 85 |

### Completion

Exact selector: an applied operation path contains the exact component
`report completion`. For auditability, the prefix is the complete
path from its root through the first occurrence of that component (inclusive);
this preserves the registered membership predicate when a nested path repeats
the same label.

| Exact contextual prefix | Bad occurrences | Good occurrences |
|---|---:|---:|
| `execute browser task` → `answer information request` → `report completion` | 10 | 24 |
| `execute browser task` → `execute enterprise workflow` → `recover interaction` → `report completion` | 0 | 17 |
| `execute browser task` → `execute enterprise workflow` → `report completion` | 39 | 58 |
| `execute browser task` → `execute visual task` → `post` → `report completion` | 36 | 0 |
| `execute browser task` → `execute website task` → `report completion` | 50 | 92 |

## Frozen-artifact and input identity

| ID | Repository-relative path | SHA-256 | Bytes |
|---|---|---|---:|
| `task_spec` | `docs/tmp/build-and-evaluate/step-0085-20260725T200000-0700/experiment-001/task-spec.md` | `ba79ee633200995cb568223a7785545558d53df54db373c3d3fdfa92f8e5a710` | 2,334 |
| `workspace_trace` | `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/trace.jsonl` | `9cc7227c9db5dae7a4e9e2866f62b1c344cc2ac23917a23d35698837b2abd7fd` | 18,774,161 |
| `workspace_annotation` | `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/annotation.json` | `38f83665712404329dd1210d8083b0618b61fec130f3b78f796605d780a2fa6d` | 590,230 |
| `workspace_stacks` | `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/stacks.folded` | `92e380d59ec1823022c2ccb6d7179be14f16be04a71da7a1d82aa5ca0e25e67d` | 418,709 |
| `pair_manifest` | `.agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/pairs.json` | `784e4f8a87b16aa5b07b9f859cb915146a7a5f13d3088163af1135e4f3398410` | 489,596 |
| `bad_operations` | `.agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/aggregate/bad.operations.jsonl` | `6829076beee8b9440d0f95215e449d3945933418d5441b70ab02d95e9fa57fe6` | 4,463,631 |
| `good_operations` | `.agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/aggregate/good.operations.jsonl` | `56cd9f56101bfc6dff2cfafbedeb392e8c5167e82dc5daa022306b466a19324b` | 2,277,127 |
| `expert_labels` | `.agentsight/external/agentreward-full/data/annotations.csv` | `155be0e6530d190c14a056f0195aaafa081c2a45a36e8f72b922c9fdc6838367` | 265,137 |
| `pair_harness` | `script/agentreward_diff_pprof_eval.py` | `f7fcbb660b2e0de9ba08956f3a6ceb1d97295052cd5ba1bc57e14857889bbe93` | 34,935 |
| `registered_scorer` | `script/agentreward_recursive_diff_eval.py` | `265737bb3bae229a557b2d5b2fb556946e9a613e5d3810934915dd2b284b26a1` | 16,362 |
| `recompute_script` | `docs/tmp/build-and-evaluate/step-0085-20260725T200000-0700/experiment-001/recompute_cs2.py` | `6a4cbde57c8f43d94f33150e2c5808ac80cfd5f99e69911c5735d15ec6e50387` | 30,857 |

`trace.jsonl` is the computational source of applied paths. `annotation.json`
and `stacks.folded` are also pinned above to identify the complete terminal
recursive workspace, although the registered endpoint scorer does not reread
them. The pair-expanded bad/good operation files supply occurrence weights;
`pairs.json` supplies the fixed task/pair relation; and `annotations.csv`
supplies only the post-annotation consensus looping endpoint.

## Method

- Pair totals are sums of integer `value` over the fixed pair-expanded side.
- Responsibility totals include a row iff its applied path contains the exact
  registered component; shares divide that total by the same side's total.
- Recovery exposure is computed on unique trajectories after deduplicating
  pair reuse: recovery operations divided by all operations in that trajectory.
- The registered fixed-chain score is the fraction whose `result` starts with
  `error:` or equals `repeated`.
- AP is scikit-learn's ordinary non-interpolated `average_precision_score`.
  The scorer sorts eligible sessions, resamples the sorted task IDs with
  NumPy `default_rng(20260722)`, includes every trajectory for each sampled
  task, and takes NumPy's 2.5% and 97.5% quantiles.
