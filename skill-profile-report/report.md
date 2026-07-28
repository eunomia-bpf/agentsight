# AgentPProf Skill-Scope Profile Report

## Result

The profile identifies **`paper-writing-style` as the first skill to inspect and improve**. It is the largest named skill scope by both additive token budget and operation count:

- **29,143,650 tokens** across **20 sessions** and **37 exact invocations**
- **523 operations**: 228 LLM completions, 111 Bash calls, 82 edits, 59 reads, 37 Skill calls, and 6 grep calls
- **15.80% of all named-skill tokens** and **16.91% of all named-skill operations**

This is a prioritization finding, not a causal efficiency claim. The profile shows that more observed budget passes through this exact skill than any other named skill. It does not prove that the skill causes the cost or that changing it will reduce cost.

The top scope is dominated by cache-token traffic: 28,987,950 of its 29,143,650 tokens (99.47%) are cache tokens. A concrete follow-up is therefore to inspect whether `paper-writing-style`'s multi-pass workflow causes unnecessarily long repeated contexts or excess read/edit/LLM cycles.

## Scope rule

Only a literal Claude tool-use object with `name == "Skill"` and a nonempty string `input.skill` starts a scope. `skill_listing`, `invoked_skills`, `command-name`, and other availability or command metadata never start one.

The rule is:

1. The LLM completion that emits the Skill call remains in the prior scope, normally `unscoped`, because it chose the skill before the invocation occurred.
2. The Skill tool operation itself starts the named scope.
3. Later LLM and tool events with the same Claude `promptId` inherit that skill.
4. A later exact Skill call replaces the current skill (latest wins).
5. The first genuine user record with a different `promptId` resets the scope to `unscoped`.

Tool results, `isMeta:true` skill payloads, `sourceToolUseID`/`sourceToolAssistantUUID` records, same-prompt command metadata, explicitly marked attachment-only records, and `last-prompt` snapshots do not reset scope. A missing-`promptId` record cannot interrupt an active modern prompt. For legacy sessions without prompt IDs, known internal wrappers such as local-command output, system reminders, IDE selections, and attachment-only payloads are excluded; a remaining non-meta, non-tool-result user message is the reset boundary.

Latest-wins replacement creates disjoint, noncrossing intervals. `unscoped` covers every event outside a named interval, so attribution remains additive.

The frame order is:

`project -> agent -> semantic task path -> skill -> phase/action/object/result/outcome -> LLM/tool evidence`

The skill is below semantic responsibility because one task can invoke different skills, and above LLM/tool evidence so its width includes governed work rather than only the near-zero Skill call. Every sample also carries a `skill` pprof label; stock `go tool pprof -tagfocus='skill=paper-writing-style'` selects the same scope.

### Known mis-attribution

- It **over-counts** later work in the same prompt after the agent has stopped following the skill.
- It **under-counts** skill work that genuinely continues into a later user prompt.
- Latest-wins loses an earlier still-active or nested outer skill because Claude records invocation but no return event.
- It cannot distinguish “skill caused this work” from “this work happened after skill invocation.”

## Corpus

The final run used a byte-frozen snapshot of every Claude JSONL present under `/home/yunwei37/.claude/projects` at 2026-07-27 22:41 local time. The temporary copies were removed after both views ran; `snapshot-manifest.tsv` retains every original path, byte size, and SHA-256.

| Item | Count |
| --- | ---: |
| Discovered JSONL files | 1,407 |
| Readable files | 1,407 |
| Parseable/emitted sessions | 1,394 |
| Excluded files with no parseable session signal | 13 |
| Sessions with exact Skill invocation | 105 |
| Distinct exact skills | 27 |
| Exact Skill invocations | 136 |
| Distinct recorded working directories | 77 |

The source census found 89,550 Claude assistant JSONL rows but only 47,129 unique completions. Stable `message.id`/`requestId`/`uuid` merging removed 42,421 repeated fragments; no counted LLM row lacked a stable source ID. This matters because split Claude rows repeat usage and would otherwise substantially inflate token totals.

The operation source total is exactly 7,961 prompt records + 50,422 tool invocations + 47,129 unique LLM completions = 105,512 operations.

## Top skills

### By additive token budget

Tokens include reported input, output, cache-creation, and cache-read components.

| Rank | Skill | Tokens | Named share | Sessions | Invocations |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `paper-writing-style` | 29,143,650 | 15.80% | 20 | 37 |
| 2 | `rewrite-abstract-intro` | 23,232,845 | 12.59% | 3 | 3 |
| 3 | `oss-change-workflow` | 19,598,745 | 10.62% | 1 | 3 |
| 4 | `check-paper-structure-flow` | 18,968,234 | 10.28% | 8 | 21 |
| 5 | `rewrite-paper-section` | 18,214,949 | 9.87% | 2 | 2 |

### By operation count

| Rank | Skill | Operations | Named share | Sessions | Invocations |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `paper-writing-style` | 523 | 16.91% | 20 | 37 |
| 2 | `oss-change-workflow` | 438 | 14.17% | 1 | 3 |
| 3 | `deep-research` | 380 | 12.29% | 5 | 13 |
| 4 | `check-paper-structure-flow` | 276 | 8.93% | 8 | 21 |
| 5 | `rewrite-abstract-intro` | 251 | 8.12% | 3 | 3 |

Named skill scopes cover 184,468,961 of 6,890,216,049 tokens (**2.68%**) and 3,092 of 105,512 operations (**2.93%**). The low global coverage is expected from the sparse signal: only 105 of 1,394 parsed sessions (7.53%) invoke a Skill.

## Aggregate-only visibility

The aggregate establishes a real cross-session priority:

- The largest single session contributes only **31.23%** of `paper-writing-style` tokens; **68.77%** lies in the other 19 sessions.
- The largest single session contributes only **15.30%** of its operations; **84.70%** lies elsewhere.
- The skill appears in 20 sessions (1.43% of the full corpus) through 37 invocations.
- Among those 20 contributing sessions, it ranks first by local named-skill tokens in 13, second in 3, third in 2, and fourth in 2. For operations it ranks first in 13, second in 5, third in 1, and fourth in 1.

Therefore, no single session contains a majority of the evidence or can establish that this is the **corpus-wide leading recurrent skill**. That global ranking is only visible after aggregation.

The stronger literal claim that no single trajectory could make the skill look locally important is **not supported**: it is locally rank 1 in 13 contributing sessions. The defensible aggregate-only finding is global prioritization and recurrence, not total absence of per-session salience. This still directly supports the fixed thesis: **“Agent observability needs profiling, not only debugging.”**

## Conservation

| View | Raw unique source | Parsed source samples | Folded total | Decoded pprof total |
| --- | ---: | ---: | ---: | ---: |
| Tokens | 6,890,216,049 | 6,890,216,049 | 6,890,216,049 | 6,890,216,049 |
| Operations | 105,512 | 105,512 | 105,512 | 105,512 |

Both equalities are exact. The raw oracle runs on the frozen JSONL bytes; folded totals come from AgentPProf; decoded totals come from `go tool pprof -raw`.

## Artifacts

The two product runs each emit exactly one standard pprof:

- `full-history.tokens.pb.gz`
- `full-history.operations.pb.gz`

The paper-only existing renderer produced:

- `full-history.tokens.named-skills.svg` / `.png`
- `full-history.operations.named-skills.svg` / `.png`
- `paper-writing-style.tokens.svg` / `.png`
- `paper-writing-style.operations.svg` / `.png`

`profile-analysis.json`, `source-oracle.json`, the run JSON, tag summaries, and the snapshot manifest are research audit records, not alternative AgentPProf product outputs.

## Validation and limitations

- `agent-session`: 19 tests passed.
- `agentpprof`: 91 unit/integration tests passed.
- The new conservation test serializes and decodes pprof for both tokens and operations.
- `cargo fmt --check` passed in both crates.
- `cargo clippy --all-targets -- -D warnings` passed for `agentpprof`. Running it directly in `agent-session` remains blocked by three pre-existing warnings in `process_match.rs` and the pre-existing portable-trace sanitizer; those unrelated lines were not changed.
- The standard pprof tag filter and existing renderer both reproduced the measured leading scope.
- A fresh experiment-plan reviewer admitted the run after prompt-boundary and source-identity fixes. An independent final code reviewer initially found UUID-only deduplication, attachment-boundary wording, and audit-JSON substantiation gaps; all were fixed, and the re-review returned **NO BLOCKERS**.

Limitations:

- Only 105 sessions carry the exact invocation signal, and named scopes cover less than 3% of full-corpus mass. Claims must be restricted to skill-using local Claude history.
- The 20-session / 37-invocation recurrence for `paper-writing-style` is strong enough to name a local prioritization target, but not to generalize to other users or prove an optimization benefit.
- Cache tokens dominate the token metric; operation count is the more vendor-neutral corroboration.
- The 13 excluded files were readable but did not contain enough recognized session signal to emit a profile session.
- Twelve malformed JSONL rows were skipped consistently by both parser and oracle.
- This run cannot verify causal benefit, true skill termination, nested skill return, or whether changing `paper-writing-style` improves quality or cost.
