# Round 4 — Abstract and Introduction

**Started:** 2026-07-20T00:08:51-07:00  
**Step / parent:** Step 0049 / WRITE gate / iter-refine-writing  
**Skills:** `iter-refine-writing`, `rewrite-abstract-intro`  
**Completed:** 2026-07-20T00:12:17-07:00  
**Status:** complete

## Immutable source contract

The complete paper body is the source of truth. The thesis, four RQs, claims,
numbers, citations, mechanisms, terminology, canonical story, and positive-only
paper boundary cannot change. This round cannot invent or import Qwen evidence.

## Entry mapping and reorganization plan

| Current opening unit | Role | Planned action |
|---|---|---|
| Abstract S1 | domain/background | retain |
| Abstract S2 | population-level problem | retain |
| Abstract S3 | structural root cause | retain |
| Abstract S4 | existing approaches and missing conjunction | retain |
| Abstract S5 | exact thesis | retain verbatim |
| Abstract S6 | system/model realization | retain unless correspondence defect |
| Abstract S7 | evaluation setup | retain |
| Abstract result sentences | capture, attribution/localization, tags/groups/cost | preserve every number; compress only if sentence-count convention requires |
| Intro ¶1 | background/context | retain |
| Intro ¶2 | problem/consequence | retain |
| Intro ¶3 | structural root cause | retain |
| Intro ¶4 | existing solutions/limitation | retain |
| Intro ¶5 | exact insight and model | retain |
| Intro ¶6 | system and mechanisms | retain |
| Intro ¶7 | results | retain every result and citation |
| Intro ¶8 | three deliverable contributions | retain |

No paragraph movement is currently planned. A fresh reviewer will determine
whether strict correspondence, topic-sentence roles, or abstract sentence count
requires a minimal repair. Under the orchestrated exception, the plan is logged
here and execution continues without waiting for human confirmation.

## Independent verdict

The fresh `rewrite-abstract-intro` reviewer passed the role mapping, strict
causal chain, insight-to-mechanism link, all body-backed numbers, and every
abstract-to-introduction correspondence except one. The abstract explicitly
attributes the three MAP gains to semantic grouping over raw action, while the
Introduction said only that MAP “rises.” This was a terminology omission, not
a claim defect.

The reviewer advised against a broad rewrite. The abstract is 232 words and 10
sentences; although the reference prefers 7--9 sentences, its final three
sentences cleanly distribute evidence across the four immutable RQs. Combining
them would create an overloaded result sentence. Intro paragraph 1 is concise
but complete and should not be padded.

## Fix

Changed the Introduction result sentence to state that semantic grouping raises
MAP over raw action, retaining all three values and citations verbatim. No other
opening prose changed.

## Self-check

- Background → problem → root cause → existing limitation → exact thesis →
  model/system → results → contributions is explicit and causal.
- Abstract terminology and results now correspond to the Introduction.
- Every opening number and claim occurs in the paper body.
- Exact thesis, four RQs, citations, mechanisms, and positive-only boundary are
  unchanged.
- Official build: 9 pages; complete Conclusion on page 7; references only on
  pages 8--9.
- No undefined citation/reference or overfull box; citation-command count 62.
- No writing/review Git operation was performed.
