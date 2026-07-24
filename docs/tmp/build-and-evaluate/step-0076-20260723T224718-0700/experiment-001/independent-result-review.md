# Independent Result Review — Step 0076 Experiment 001

**Review method:** `research-experiment-design` RESULT REVIEW  
**Run status:** **VALID**  
**Descriptive matched contrast:** **ESTABLISHED**  
**Independent superiority hypothesis:** not tested by design  
**Must-fix:** none

## Independent judgment

The complete run satisfies the approved same-input contract. The count and
token files are exact filters of the authoritative adopted A2 inputs; they
contain the same 489 unique evidence IDs in the same order and conserve 489
operations and 4,558,192 provider-reported tokens. The fixed mechanical mark
adapter expands 79 tool-level path transitions to the accepted workspace path
for all 489 operations with zero mismatches or missing assignments. All six
profiles report successful completion without warnings, load in stock
`go tool pprof`, and conserve exact mass.

The fixed `diagnose authentication` projection also recomputes exactly: 105
operations, 2,103,587 tokens, two source sessions, and 105 distinct source
calls. Its source and coarse-action composition matches the result report.
The evidence therefore establishes the registered **descriptive matched
organization contrast**.

This is not a supported/contradicted independent superiority experiment. The
semantic result defined both the post-hoc case and the responsibility members.
The valid conclusion is that, for those fixed candidate-defined members and
unchanged weights, the three registered stack organizations expose different
axes while retaining the same evidence. The report maintains that boundary.

## Approved design and execution status

I read the complete approved plan, all three plan-review rounds and final
approval, the real preflight report, and the full-run report before examining
the raw artifacts.

The plan-review repairs are present in the executed design:

- the Git family and SSH-authentication responsibility are explicitly
  post-hoc selections;
- all three organizations are regenerated from the same two filtered files
  with the same `agentpprof 0.2.37` binary;
- native source and coarse action are correctly controls, not claimed as the
  strongest no-label competitor;
- the common prefix is `project,agent`, the common suffix is `call,tool`, and
  only the registered middle treatment changes;
- recurrence remains the stronger existing population-level no-label
  comparison and is not redundantly rerun;
- validity depends on faithful replay, readability, and exact mass rather than
  the circular claim that the candidate independently rediscovers its own
  selected members.

The real preflight used the first approved source session. Its raw count input
has 119 rows, 119 unique evidence IDs, and mass 119. Producer stdout reports
status `ok`, no warnings, the final semantic stack, 119 samples, and 119 unique
stacks. A fresh stock-pprof read reports exactly 119 operations. The preflight
therefore exercised the real final path and correctly contributed no result
number.

## Independent input and population recomputation

I independently filtered the authoritative
`a2-rootfix-v1/profile-inputs/operations-{count,tokens}.jsonl` files by the
three literal registered source-session IDs and compared the resulting ordered
rows with the Step 0076 files.

| Check | Count width | Token width |
|---|---:|---:|
| Rows | 489 | 489 |
| Unique evidence IDs | 489 | 489 |
| Additive mass | 489 | 4,558,192 |
| Equal to authoritative literal-session filter | yes | yes |
| Evidence-ID order equal across widths | yes | yes |

All 489 count rows have value one. The two widths contain the same evidence
IDs and factual fields; only their additive value differs as planned.

The population has three source sessions and 240 distinct source calls:

| Source session | Operations | Tokens | Distinct calls |
|---|---:|---:|---:|
| OpenHands / Claude Sonnet 4 Thinking | 119 | 2,264,980 | 119 |
| OpenHands / DeepSeek V3.2 | 95 | 1,683,411 | 95 |
| Terminus2 / DeepSeek V3.2 | 275 | 609,801 | 26 |
| **Total** | **489** | **4,558,192** | **240** |

This independently confirms that every execution in the selected Git family
is retained. No operation is dropped after the post-hoc case selection.

## Accepted-path adapter audit

The accepted trace workspace contains exactly 489 `kind == "tool"` rows for
the three source sessions and 489 unique stable evidence IDs. Independently
collapsing adjacent equal tool paths within each session gives:

| Source session | Tool-path transitions |
|---|---:|
| OpenHands / Claude | 25 |
| OpenHands / DeepSeek | 31 |
| Terminus2 / DeepSeek | 23 |
| **Total** | **79** |

Including the session, prompt, and LLM levels gives 29, 37, and 30 transitions,
or 96 mixed-level annotations. The report's statement that 79 tool-level
marks mechanically compress the workspace's 96 mixed-level annotations is
therefore correct.

I expanded the 79 stored marks independently by:

1. grouping marks by the declared `source_session` sequence;
2. applying each mark from its declared `start_operation_id`;
3. resolving every stored operation ID through `operation_names`; and
4. comparing the resulting path for each evidence ID with the corresponding
   accepted trace tool row.

| Expansion check | Recomputed |
|---|---:|
| Expected evidence rows | 489 |
| Expanded evidence rows | 489 |
| Path mismatches | 0 |
| Missing path assignments | 0 |

The adapter therefore changes neither names, paths, boundaries, nor
membership. Its 66-name dictionary and sparse representation are mechanical
serialization details, not a new annotation method.

## Six-profile execution and stock-pprof audit

All six stdout records report `status: ok`, no warnings, and the registered
input, view, and stack. Native and coarse conditions have no operation-mark
file; only the semantic condition reads the accepted marks. Each organization
uses the same count file for its operation profile and the same token file for
its token profile.

I freshly ran `go tool pprof -top` on all six `.pb.gz` files:

| Organization | Width | Producer samples | Stock-pprof total | Unique full stacks | Recomputed SHA-256 |
|---|---|---:|---:|---:|---|
| Native source | operations | 489 | 489 | 396 | `d4be76ac05c7a7d598ab220e62d206a07363862681ea1edcb6ed0ee76af8e879` |
| Native source | tokens | 4,558,192 | 4,558,192 | 396 | `f7bc87257260df40a3bbd84a31026917c97249d48dd2166c0079c056f515e4a2` |
| Coarse action | operations | 489 | 489 | 403 | `90a0e6795de8b1ad1aa4b235ac1dca11f39170ab60c96b227be62c260baddab6` |
| Coarse action | tokens | 4,558,192 | 4,558,192 | 403 | `f2cdc3f8cc29243d5c0a86d576c88db39332af07451e3a51863b84968680ce76` |
| AgentProf semantic | operations | 489 | 489 | 396 | `498b1397827a425e9cd58b5e202ae63c38447e08c9ebf6e09b710e83d8efcd9b` |
| AgentProf semantic | tokens | 4,558,192 | 4,558,192 | 396 | `9c03920916ac701bcd6d43f15e20a6c23928cd3aa6f6e921e271a1cd312bf6b9` |

Every digest matches the full-run report. Stock pprof's
`Main binary filename not available` message is expected for
language-agnostic profiles and does not prevent decoding the sample type,
frames, labels, or total.

Fresh `pprof -tags` reads show the same source-session mass in every
organization:

| Source session | Operation label mass | Token label mass |
|---|---:|---:|
| OpenHands / Claude | 119 | 2,264,980 |
| OpenHands / DeepSeek | 95 | 1,683,411 |
| Terminus2 / DeepSeek | 275 | 609,801 |

Thus all organizations preserve the same source labels even when
`source_session` is not a displayed stack frame. The unique-full-stack values
remain descriptive only: the common call suffix is a major contributor, so
the report correctly avoids treating 396 versus 403 as a quality or compactness
score.

## Fixed responsibility recomputation

The stored diagnose set contains 105 unique evidence IDs. Every ID exists in
both fixed widths, and all 105 corresponding accepted workspace paths contain
`diagnose authentication`.

| Fixed responsibility property | Recomputed |
|---|---:|
| Operation rows / mass | 105 / 105 |
| Share of complete operations | 21.472393% |
| Token rows / mass | 105 / 2,103,587 |
| Share of complete tokens | 46.149592% |
| Source sessions | 2 |
| Distinct source calls | 105 |
| Distinct call/tool pairs | 105 |

The source-session projection is exact:

| Source session | Operations | Tokens |
|---|---:|---:|
| OpenHands / Claude | 58 | 1,283,188 |
| OpenHands / DeepSeek | 47 | 820,399 |
| **Total** | **105** | **2,103,587** |

Fresh stock-pprof focus on
`operation:diagnose_authentication` reports 105 operations, 21.47% of 489,
and 2,103,587 tokens, 46.15% of 4,558,192. Focused pprof tags reproduce the
same 58/47 operation split and 1,283,188/820,399 token split. The focused
semantic profile retains 105 distinct calls and both source-session labels,
so the reported source drilldown is real rather than inferred from the
projection summary.

## Independent coarse-action recomputation

Joining the fixed 105 IDs to the raw token rows gives:

| Coarse action kind | Operations | Tokens | Share of responsibility tokens |
|---|---:|---:|---:|
| execute | 44 | 829,239 | 39.4202% |
| version-control | 20 | 464,038 | 22.0594% |
| edit | 19 | 401,247 | 19.0744% |
| inspect | 12 | 244,428 | 11.6196% |
| search | 9 | 155,397 | 7.3872% |
| install | 1 | 9,238 | 0.4392% |
| **Total** | **105** | **2,103,587** | **100%** |

The report's rounded percentages are correct, and the largest branch is
strictly below 40% of responsibility tokens.

At the raw-action-key level:

| Raw action key | Operations | Tokens | Share of responsibility tokens |
|---|---:|---:|---:|
| run | 102 | 2,036,582 | 96.8147% |
| think | 2 | 47,291 | 2.2481% |
| edit | 1 | 19,714 | 0.9372% |

The complete three-session input has 199 `run` operations. Subtracting the 102
fixed responsibility members leaves exactly 97 unrelated case operations
under the same generic key. This verifies every coarse-composition number and
the report's narrow observation that these labels describe mechanism but do
not directly name the selected SSH-authentication responsibility.

## Post-hoc interpretation and leakage audit

The interpretation stays within the approved boundary:

- The report opens by stating that both task family and responsibility were
  selected after observing the prior semantic case.
- The 105-member set is used as a fixed projection key, not as an independent
  oracle for annotation correctness.
- Native and coarse profiles are built without accepted marks; membership is
  joined afterward by stable evidence ID.
- All three selected executions and all 489 rows are retained after selection.
- The result is called an organization contrast, not independent discovery,
  accuracy, universal superiority, or a population effect.
- Native and coarse views are treated as missing case controls. The stronger
  recurrence comparison remains explicitly attributed to the complete
  405-trajectory RQ3 experiment.
- The semantic conclusion is limited to a representation property: the
  accepted path adds a focusable responsibility axis while preserving the
  same source evidence. It does not claim the selected responsibility was
  independently proven correct by this replay.

The contrast is partly structural by design—only the semantic stack receives
the accepted operation frame—but it is not presented as a causal superiority
test. Its non-tautological contribution is the matched materialization showing
that the previously reported 46.15% focus uses unchanged rows and weights and
still retains exact source-call drilldown. That is legitimate supporting case
evidence.

## Required result-review judgments

- **Run status:** **VALID**. Every planned cell completed; all correctness,
  path, mass, and stock-reader checks pass with no deviation found.
- **Tested hypothesis:** no independent superiority hypothesis was registered.
  The approved **DESCRIPTIVE MATCHED CONTRAST IS ESTABLISHED**.
- **Research value:** **supporting**. It strengthens one existing RQ1 case with
  matched organization controls; it is neither decisive nor a standalone RQ
  answer.
- **Paper impact:** **additional bounded RQ1 case evidence**. It does not alter
  the population-level RQ3 result or directly challenge/establish the paper's
  full thesis.
- **Next paper decision:** the paper may use the matched organization contrast
  with its explicit post-hoc qualifier and unchanged-sample claim. It must
  retain the prohibition on discovery-accuracy, population-effect, and
  universal-interface-superiority claims.

## Must-fix

None.
