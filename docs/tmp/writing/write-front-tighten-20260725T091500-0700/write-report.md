# WRITE report — pass 3b: front-matter and Design/RW tightening

Edited file: `docs/paper/main.tex` only. No git commands run.

## 1. Per-section before/after source-line counts

"Before" = state at start of pass 3b (post-3a). "After" = current.

| Section             | Before | After | Delta | Target | Met? |
|---------------------|-------:|------:|------:|-------:|------|
| Abstract (front-matter bonus) | 44 | 38 | -6 | front | n/a |
| Introduction       | 135    | 127   | -8   | -12    | partial |
| Design             | 131    | 125   | -6   | -10    | partial |
| Implementation     | 57     | 51    | -6   | -8     | close |
| Related Work       | 45     | 41    | -4   | -8     | partial |
| **Total (4 sections)** | **368** | **344** | **-24** | **-38** | |
| **Total (with abstract)** | **412** | **382** | **-30** | — | |

The source-line deltas understate the actual prose compression because the
two-column AAAI body wraps at ~80 source columns; many edits removed words
inside a wrapped line without collapsing the line count. Measured by
non-comment English characters, the four sections shrank by ~2000 chars
(roughly -50 rendered column-lines, ~half a page of two-column body).

## 2. What was compressed

**Tighten A — Introduction.** Fused ¶1 background+trajectories into one
sentence; fused ¶2's three separate questions into a clause list and dropped
"At scale"; fused ¶3's two-structure sentences and removed the trailing
restatement sentence ("Adapting profiling therefore requires..."); fused ¶4's
"These systems establish...but do not combine" into a single "None combines"
clause; removed ¶5's model-preview sentence ("provides this structure through
source nodes, recursive operation annotations, and operation stacks") that
restated the three components immediately listed after it; fused ¶6's last two
sentences. ¶7/¶8 lost only filler words ("all", "also", "significantly", "used
for protocol development"); all numbers and the enumerate structure are intact.

**Tighten B — Design.** Fused the "three explicit objects" paragraph's three
short sentences into one semicolon-joined sentence; removed the D1-D3 mapping
paragraph's redundant "LLM/tool frames preserve visible evidence" clause
(already stated in the preceding paragraph); removed the coarse-to-fine
paragraph's "Branches stop independently, so depth is neither fixed nor
optimized directly" (restated by the Agent-backend paragraph's "There is no
depth cap..."); kept the formal binary-policy sentence ("A child name equal to
the current frame stays, one equal to an ancestor pops...") verbatim; fused the
post-policy stopping/depth/materializer sentences; moved the CodeTraceBench A2
representation-repair detail to appendix `app:canonicalization` (appended a new
paragraph there) and kept one summary clause in the body.

**Tighten C — Implementation.** Fused the Input-reconstruction enumeration
into one sentence; fused the Annotation-workspace contract + validation
sentences; removed the replay-capability sentence (a verbatim restatement of
the Design D1-D3 mapping paragraph's last sentence); tightened the
hierarchy-warning sentence; folded the redundant standalone opening sentence
("\sys is an offline Rust CLI...") into the Input-reconstruction paragraph.
Profile-export paragraph kept verbatim (product-boundary statement). The
three-file contract (trace.jsonl / annotation.json / pprof), validation
guarantees (nested, noncrossing, full cover), and the three warning types
(one-child, flat fan-out, eight-tool-call leaf) are all preserved.

**Tighten D — Related Work.** Fused each paragraph's system-list sentences
into semicolon/comma-joined lists; removed the "Together, these systems
establish..." summary sentences that restated the preceding system
descriptions; every citation key retained; no comparison changed polarity or
strength.

**Abstract (front-matter).** Fused sentences 1+2 (background+need) and
sentences 3+4 (gap+existing-tools) into two sentences; trimmed "conserved
resource measures"→"conserved measures", "compose those responsibilities"→
"compose them", "Used as a reading index"→"As a reading index", "context-window
bound"→"context window". Thesis sentence and every number kept verbatim.

## 3. Validation gate results

| Gate | Result |
|------|--------|
| Compiles clean (latexmk -pdf) | PASS |
| Undefined refs/citations | 0 |
| Overfull hboxes | 0 |
| Thesis sentence "Agent observability needs profiling, not only debugging." | 3 locations (abstract, intro ¶5, conclusion) — verbatim |
| Unique \cite keys preserved | 60 unique keys; 0 lost, 0 added vs. pre-3b |
| RQ1–RQ4 titles | all 4 present and unchanged |
| Tables | 4 (all intact) |
| Figures | 3 (all intact) |
| Contributions enumerate | 1 (3 items, unchanged) |

## 4. Page-layout report

Total pages: **12**.

| Page | Content (first / last line) |
|------|------------------------------|
| 1 | Title + Abstract + Introduction ¶1–¶6 start |
| 2 | Introduction ¶6 end + Background + Design start |
| 3 | Design (model, stacks, annotation) |
| 4 | Implementation + Figure 1 (architecture) caption |
| 5 | Evaluation RQ1 + Figure 2 (git flamegraph) caption |
| 6 | RQ1 cont. + Case Study 1 + Table 1 |
| 7 | Case Study 2 + Figure 3 (agentreward diff) + Table 2 + RQ3 start |
| 8 | RQ3 + RQ4 + Table 3 + Table 4 |
| 9 | RQ4 end + Scope/Limitations + Related Work + Conclusion + References start |
| 10 | References (middle batch) |
| 11 | References (final batch) — **References end here** |
| 12 | Technical Appendix |

**References end on page 11** (target was ≤ page 10; not fully met).

**Figure/table pages still sharing with body:** all of them.
- Figure 1 (architecture): page 4 (shares with Implementation body)
- Figure 2 (git-multibranch flamegraph): page 5 (shares with RQ1 body)
- Figure 3 (agentreward differential): page 7 (shares with Case Study 2 / RQ3 body)
- Table 1 (RQ2 localization): page 6; Table 2 (RQ3 CodeTrace): page 7;
  Table 3 (RQ3 boundary): page 8; Table 4 (RQ4 cost): page 8

## 5. Why References still end on page 11

The bibliography block spans ~2.6 two-column pages (60 cited keys in the AAAI
`natbib`/`aaai2027.bst` style, many multi-line entries). For References to end
on page 10, body text would need to end by roughly page 7.4 so the ~2.6-page
reference block fits in pages 8–10. The Evaluation section alone occupies
pages 4–8 (~5 pages) and was explicitly out of scope for this pass
(Tighten A–D cover only Introduction, Design, Implementation, Related Work,
plus the front-matter abstract). The ~30 source-line / ~half-page compression
achieved in the in-scope sections pulls the Conclusion and References start
earlier on page 9 (References now begin on page 9 instead of later on page 9)
and packs more reference entries onto pages 9–10, but cannot eliminate the
final reference column on page 11 without either compressing the Evaluation
section (out of scope) or dropping citations (forbidden).
