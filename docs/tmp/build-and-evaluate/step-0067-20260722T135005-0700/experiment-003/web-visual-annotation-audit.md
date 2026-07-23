# AgentReward automatic annotation audit: WebArena + VisualWebArena

**Verdict: REVISE.**

Scope was limited to the eight requested batch directories and to each
`trace.jsonl`, `annotation.json`, and `backend-report.md`.  No
`backend-instruction.md` exists in any of the eight directories, so instruction
conformance could not be audited.  No annotations or other experiment inputs
were modified.

## Method

I independently reconstructed the annotation tree from `annotation.json` and
the source event sequence from `trace.jsonl`.

- Schema checks require exactly `parent`, `next`, and nonempty `tag` fields.
- Each annotation ID and non-null parent/next ID must exist in the trace.
  A non-root parent must itself be annotated; its trace path must be the exact
  prefix of its child's path.  `next` must be an annotated later LLM node in
  the same prompt.  Parent-cycle, cross-prompt-next, and path/tag checks were
  also performed.
- Coverage requires an annotation for every source session and prompt.
- Depth is the number of semantic path elements on source LLM events.  A
  coarse-leaf recomputation treats a leaf interval of at least eight LLM steps
  as coarse.  This independently reproduces seven of eight reported coarse
  counts exactly.

## 1. Structure, coverage, and depth

All eight annotation objects have the same valid schema and all structural
checks pass: no dangling IDs, bad path prefixes, parent cycles, cross-prompt
`next` links, or non-increasing `next` links.  Every source session and prompt
is annotated exactly once.  The number of LLM boundary entries also equals the
report's `Added LLM boundaries` for every WebArena batch.

| batch | sessions/prompts | annotations (session/prompt/LLM) | LLM path depth 3 / 4 | reported max depth |
|---|---:|---:|---:|---:|
| web-00 | 44 / 44 | 244 (44 / 44 / 156) | 465 / 145 | 4 |
| web-01 | 44 / 44 | 214 (44 / 44 / 126) | 506 / 50 | 4 |
| web-02 | 44 / 44 | 260 (44 / 44 / 172) | 548 / 56 | 4 |
| web-03 | 43 / 43 | 251 (43 / 43 / 165) | 737 / 17 | 4 |
| visual-00 | 39 / 39 | 131 (39 / 39 / 53) | 317 / 88 | 4 |
| visual-01 | 39 / 39 | 122 (39 / 39 / 44) | 611 / 55 | 4 |
| visual-02 | 39 / 39 | 123 (39 / 39 / 45) | 531 / 58 | 4 |
| visual-03 | 36 / 36 | 111 (36 / 36 / 39) | 526 / 29 | 4 |

Thus the reported maximum depth of four is correct everywhere.  There are no
unary or flat source-path cases in the reconstructed trees, consistent with
all eight reports.

## 2. Coarse leaves versus backend reports

The eight-step leaf-span recomputation matches the reported coarse count for
seven batches.  This is strong evidence that the reports used the same
coarseness boundary.

| batch | reported coarse / unary / flat | recomputed coarse leaves | result |
|---|---:|---:|---|
| web-00 | 14 / 0 / 0 | 14 | match |
| web-01 | 20 / 0 / 0 | 20 | match |
| web-02 | 18 / 0 / 0 | 18 | match |
| web-03 | 27 / 0 / 0 | 27 | match |
| visual-00 | 12 / 0 / 0 | 12 | match |
| visual-01 | 24 / 0 / 0 | **25** | **mismatch** |
| visual-02 | 24 / 0 / 0 | 24 | match |
| visual-03 | 22 / 0 / 0 | 22 | match |

`visual-01/backend-report.md` must be regenerated or corrected.  The two
threshold-edge leaves that require reconciliation against the profiler output
are:

- `llm:visualwebarena__visualwebarena.resized.292__GenericAgent-anthropic_claude-3.7-sonnet:step-0000` (8 LLM steps);
- `llm:visualwebarena__visualwebarena.620__GenericAgent-gpt-4o-2024-11-20:step-0022` (8 LLM steps).

At least one is omitted by the prose count of 24.  The second is independently
incorrectly named as completion work (below), so its annotation must be
revised regardless of the final warning count.

## 3. Tag leakage and taxonomy

No tag directly exposes a benchmark name, reward, pass/fail score, benchmark
outcome, or raw tool-call name.  Terms such as `filter ... by status` name a
user-visible field, and `fill contact details` names the responsibility rather
than copying a raw tool event.  The word `failed` appears only in the generic
local-recovery label; source reasoning explicitly describes the local failed
or repeated interaction, so it is not benchmark-outcome leakage.

The aggregate rate does not show numerical overuse of recovery: 54 of 800 LLM
boundary annotations (6.8%) use `recover from failed or repeated interaction`.
Completion-labelled LLM boundaries are 94 of 800 (11.8%).  WebArena's 87 such
boundaries are generally terminal reporting/verification spans.  The Visual
set has a more serious qualitative problem: all seven occurrences of the
completion label collapse distinct, non-completion responsibilities.  This is
an **different-responsibility/same-name** error, not outcome leakage.

The sampled recovery labels (`recover`, `retry`, `wait`, and `try alternate`)
track distinguishable local strategies rather than the same duty under random
synonyms.  No must-fix same-duty/different-name case was found in the sample.

### Must-fix VisualWebArena node IDs

Retag or split these nodes before using the annotations.  In every case, the
current tag is `verify or report task completion`, but the source reasoning and
action show an unfinished mutation, candidate inspection, submission, or cart
operation.  The tag should state the observed operation and a later boundary
should be added only when verification actually begins.

| batch | node ID | source evidence at boundary | required revision |
|---|---|---|---|
| visual-00 | `llm:visualwebarena__visualwebarena.4__GenericAgent-gpt-4o-2024-11-20:step-0003` | fills the listing description; later repeatedly clicks Save | retag this start as description editing; add a save/retry boundary at step 6 rather than calling the whole span completion verification |
| visual-00 | `llm:visualwebarena__visualwebarena.600__GenericAgent-gpt-4o-2024-11-20:step-0007` | opens/inspects an HP printer candidate to check its criteria | retag as candidate-product inspection; it is not completion reporting |
| visual-01 | `llm:visualwebarena__visualwebarena.620__GenericAgent-gpt-4o-2024-11-20:step-0022` | identifies a matching Sony headphone and repeatedly clicks Add to Cart | retag as add matching product to cart / retry cart addition; do not call it verification |
| visual-01 | `llm:visualwebarena__visualwebarena.76__GenericAgent-gpt-4o-2024-11-20:step-0003` | fills the listing description and then searches/retries Save | retag as description editing and split before the save/retry work |
| visual-02 | `llm:visualwebarena__visualwebarena.resized.31__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0011` | clicks Send to submit the offer; source-visible verification begins at step 12 | retag as submit offer comment and add a verification boundary at step 12 |
| visual-02 | `llm:visualwebarena__visualwebarena.resized.4__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0006` | price and description are changed; the next work is finding/clicking Save | retag as save/submit updated listing, not verification |
| visual-03 | `llm:visualwebarena__visualwebarena.resized.76__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0003` | begins price-field and description editing, then save/retry work | retag and split into price/description editing followed by save/retry; no completion evidence appears at this boundary |

The affected visual reports should be revised after the annotations.  In
particular, visual-01's claim of search-to-verification for task 620,
visual-02's claim that the offer trace reaches completion verification at this
boundary, and visual-03's claim that task 76 has a completion-check sibling
are not supported by the current source paths.

## 4. Random multi-step source audit

I made a deterministic random sample (seed label `20260722`) of two sessions
per batch from sessions with at least eight LLM steps: 16 sessions total.  For
each, I compared every annotated boundary in the session with the boundary
LLM's source reasoning, its paired tool action, and the subsequent path.
Anthropic entries that contain only serialized `<action>` reasoning were
checked against those actions and page-state progression.

| batch | sampled session (task/model) | result | evidence summary |
|---|---|---|---|
| web-00 | 295 / Llama | pass | repository location followed by repeated clone-control attempts; recovery span is source-supported |
| web-00 | 15 / Qwen | pass | review navigation → term filter → local recovery/retry → extra-page inspection |
| web-01 | 468 / GPT-4o | pass | wish-list navigation, repeated unavailable control attempts, then further control inspection |
| web-01 | 419 / Llama | pass | profile access attempts and retry-navigation span agree with repeated clicks/reasoning |
| web-02 | 593 / Llama | pass | one repeated milestone-navigation responsibility; retained coarse recovery is supported |
| web-02 | 593 / Claude | pass | milestone navigation → title → start date → due date → description → submit follows the action sequence |
| web-03 | 718 / Qwen | pass | community navigation → top-post selection → downvotes → post inspection aligns with reasoning and click/scroll actions |
| web-03 | 718 / Claude | pass | navigation then downvote action is consistent with the two recorded semantic spans |
| visual-00 | 4 / GPT-4o | **fail** | boundary at step 3 begins description editing, not completion verification (must-fix above) |
| visual-00 | 331 / GPT-4o | pass | long forum/image-detail investigation remains one source-visible inspection/reporting responsibility |
| visual-01 | resized.292 / Claude | pass | homogeneous fact-lookup action sequence; it is coarse but its activity tag matches the trace |
| visual-01 | resized.302 / Qwen | pass | repeated fact research/tab navigation has no evidenced responsibility transition |
| visual-02 | resized.331 / Qwen | pass | image-detail investigation path matches repeated navigation/inspection reasoning |
| visual-02 | resized.389 / Claude | pass | matching-post/comment navigation is consistent with the source action sequence |
| visual-03 | resized.876 / Claude | pass | product/cart search-and-add remains one source-visible responsibility |
| visual-03 | resized.98 / Qwen | pass | listing-detail search/inspection matches the full repeated source trace |

## Required disposition

Do not mark this eight-batch set PASS until the seven Visual completion nodes
are retagged/split and the visual-01 coarse-warning discrepancy is regenerated
or explained from the profiler.  After those fixes, rerun the parent/next and
coarse-leaf checks; the remaining structural, coverage, depth, recovery, and
outcome-leakage checks are currently PASS.

## Follow-up must-fix re-review

**Follow-up verdict: REVISE.**  This re-review was deliberately limited to the
previous seven completion-label findings, the visual-01 coarse count, and the
four VisualWebArena trees.  It re-read only the updated `annotation.json`,
`backend-report.md`, and source `trace.jsonl` files; it made no annotation
changes.

### Re-review result

Six of the seven prior findings are now supported by the source event at their
updated boundary:

- visual-00 task 4 step 3 is `edit the listing description`, followed by a
  new step-6 `save or retry the updated listing` boundary; the source actions
  are respectively `fill` and Save-directed `click`.
- visual-00 task 600 step 7 is `inspect a candidate product`, matching the
  source click to inspect the candidate HP printer.
- visual-01 task 620 step 22 is `add a matching product to cart`, matching
  the Add-to-Cart click; task 76 now separates description editing at step 3
  from saving/retrying at step 6.
- visual-02 resized task 31 now separates `submit the offer comment` at step
  11 from actual source-visible completion verification at step 12.  Resized
  task 4 step 6 is correctly `save or submit the updated listing`.

One correction remains semantically misplaced and must be revised:

- `llm:visualwebarena__visualwebarena.resized.76__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0006`
  is now labelled `save or retry the updated listing`, but its source action is
  `fill` and its reasoning says that the description field is focused and will
  be edited.  Save discovery begins at **step 7** (a `scroll` action looking
  for Save), not step 6.  Remove/move this step-6 save boundary; let the
  step-3 price/description-editing span cover step 6, and add the
  save/retry boundary at step 7.  Update `visual-03/backend-report.md`'s
  audit-revision sentence accordingly.

### Coarse count and tree validity after the updates

The visual-01 report now says 25 coarse leaves and the source-tree
recomputation also yields **25**, so that prior discrepancy is resolved.
The other recomputed coarse counts remain visual-00 12, visual-02 24, and
visual-03 22, matching their reports.

All four trees remain schema- and linkage-valid after the updates: each has
zero malformed node/tag records, dangling/non-prefix parents, invalid/cross-
prompt/non-increasing `next` links, or parent cycles.  Their maximum source
semantic depth remains four and their reports continue to emit no unary or
flat-hierarchy warning.  The remaining visual-03 source/tag mismatch above is
therefore a semantic-boundary error, not a structural one.

## Final follow-up: visual-03 resized.76 save/retry boundary

**Final follow-up verdict: REVISE.**  The requested annotation-boundary repair
is correct, but the report still contains one contradictory task-76 statement.
This final check was limited to that Qwen trace, its annotation links, and the
visual-03 profile/report text.

The source-supported repair is present:

- step 6 remains under `edit the listing price and description`; its action is
  `fill` and its reasoning explicitly says to edit the focused description;
- `llm:visualwebarena__visualwebarena.resized.76__GenericAgent-Qwen_Qwen2.5-VL-72B-Instruct:step-0007`
  starts `save or retry the updated listing`; its reasoning says the price and
  description are updated and that it must scroll to find Save, and its action
  is `scroll`;
- step 8 remains in that save/retry span and continues the Save/Submit search.

The visual-03 annotation tree is structurally valid (112 entries, zero schema,
parent-path, `next`, or cycle violations; maximum depth 4).  Its report still
records profile `status: ok`, 22 coarse leaves, and no unary or flat warnings,
which remain consistent with this boundary move.

Before marking the follow-up PASS, revise the first paragraph of
`visual-03/backend-report.md`: it says task 76 has
`editor-location, price-editing, and completion checking` sibling spans.  The
updated paths and the report's own Audit revision instead show editor-location,
price/description editing, and save/retry work, with **no** completion-checking
span.  Replace that stale completion-checking wording; then this limited
follow-up can be marked PASS.

**Final status: PASS.** `visual-03/backend-report.md` now describes task 76 as
editor-location, price-editing, and source-supported save/retry work; the
stale completion-checking wording is removed.
