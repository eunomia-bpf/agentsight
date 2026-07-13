# Round 7 — Language: Word Choice

- Started: `2026-07-13T09:04:18-07:00`
- Completed: `2026-07-13T09:13:46-07:00`
- Parent: `cycle-0002-20260712T201943-0700 / WRITE / iter-refine-writing-20260713T073140-0700`
- Governing skills: `iter-refine-writing`, `paper-writing-style`
- Mode: serial independent read-only whole-paper word-choice review, root
  disposition, subsection-scoped fixes, full build, and rendered-page audit
- Verdict: `PASS`
- Scientific/story verdict: `NO DRIFT`
- Git operations: none

## Objective and entry

Round 7 checked jargon inflation, compound-term repetition, nominalizations,
vague referents, redundant hedging, verbose phrases, unnecessary adverbs,
imprecise idiom, and project-report prose. It did not authorize renaming the
two core abstractions, changing an RQ, weakening a claim to fit current
evidence, changing a number, or editing the read-only submodule.

The reviewer reread the complete `docs/user-instruction.md` and current
`docs/paper/main.tex`. The root compared every recommendation against the
complete paper, the permanent Initial Narrative and current frontier in
`docs/idea-story.md`, and the user-selected AgentProf authority.

## Mechanical scan and terminology frequency

The paper contains none of the standard verbose constructions `in order to`,
`utilize`, `due to the fact that`, `it is important to note`, `a number of`,
`is able to`, `with respect to`, or `in terms of`. The reviewer found no
high-confidence redundant-hedging problem.

Selected live-term counts at entry were:

| Term | Count | Decision |
|---|---:|---|
| `operation stack` | 39 | Retain. It is one of the two locked core abstractions, including headings, captions, comments, and compound use. |
| `semantic profiling` | 8 | Retain. It names the paper's method and claim surface. |
| `intent attribution` | 9 | Retain. It is a stable mechanism name. |
| `stack construction` | 9 | Retain. It is a stable mechanism name. |
| `per-session` | 18 | Retain. It is a repeated baseline/contrast, not a renamed concept. |
| `query-time` | 7 | Retain where it distinguishes the operation stack from a runtime call stack. |
| `population-level` | 6 | Retain where it carries the debugging-versus-profiling distinction. |

Reducing these counts by introducing synonyms would create terminology drift
rather than improve prose.

## Independent findings and root disposition

The independent reviewer returned 4 Must-fix, 14 Should-fix, and 2 Consider
items.

### Must-fix

1. **Background referent.** `We quantify this in RQ1` could refer to missing
   boundaries, hierarchy, or attribution granularity. **Applied:** the sentence
   now names how the missing reusable hierarchy affects resource attribution.
2. **RQ1 evidence wording.** `correctly separates effects` may outrun what the
   mixed-weight scorer alone establishes. **Rejected as a writing edit:** the
   proposed replacement would narrow the frozen positive RQ1 claim in response
   to an evidence objection. The wording remains, and the Round-5 RQ1
   independent-reference obligation remains routed to EXPERIMENT. Only stronger
   external evidence may resolve it.
3. **RQ2 antecedent.** `recover them` grammatically referred to annotations,
   not annotated positives. **Applied:** top-ranked groups now `contain the
   corresponding positives`.
4. **Related Work idiom.** `center per-execution tracing` was unidiomatic.
   **Applied:** `center on per-execution tracing`.

### Should-fix

All 14 Should-fix items were accepted, with one local wording adjustment that
avoids a new categorical claim:

- `Realizing profiling requires` became the concrete subject `Agent profiling
  requires`.
- The scale/cost sentence now starts with `Across many trajectories` and uses
  `by manual inspection or per-trajectory LLM evaluation`.
- The observability comparison now says interfaces generally target
  per-execution analysis rather than population-level attribution. This is
  clearer than `emphasize questions other than` without claiming that every
  system lacks every aggregation feature.
- `aggregate responsibility view` became the established `aggregate
  attribution view`.
- `Realizing this insight requires ... recover` became `An agent profiler must
  reconstruct`.
- The profiling definition now says it aggregates consumption by responsible
  entity, unlike single-execution debugging and tracing.
- The operation-stack sentence no longer repeats `serving/serves`.
- `gets for free from function names` became `function names provide in
  traditional profiling`.
- `offline, post-hoc ... codebase` became `offline profiler implemented as a
  Rust CLI and parser`; the 9.8K-LOC scope remains unchanged.
- The implementation now says an AI agent `refine[s] the rules`, not `iterate[s]
  the regex`.
- The clustering sentence now uses the concrete verb `groups` and states that
  it guides rule authoring.
- `different field selections for the operation stack` became `different
  operation-stack fields`.
- `complete comparison defined below` became `full localization comparison`.
- `Specifically` and `actually` were removed from the RQ2 entry sentence.

### Consider

- **Accepted:** `exposes useful tuning axes` was jargon-heavy. The sentence now
  states directly that the tested configuration choices improve localization
  on the reported tasks.
- **Rejected:** replacing `\sys realizes this thesis` with `supports this form
  of profiling` would weaken the deliberate thesis-forward conclusion without
  improving precision. The original strong closing remains.

Round 7 changed 18 sentence groups: 3 accepted Must-fix items, 14 Should-fix
items, and 1 Consider item.

## Preservation and intent audit

- Exact thesis: unchanged and present in Abstract, Introduction, and
  Conclusion.
- Four RQs: unchanged in count, order, wording, and meaning.
- Quantitative values: unchanged.
- Citations: unchanged at 44 commands and 71 cited-key occurrences.
- Scope-bearing qualifiers: retained.
- Core abstractions: unchanged; no synonym set was introduced.
- RQ1 positive hypothesis: not narrowed in response to the scorer objection.
- Conclusion strength: retained.
- Internal negative/inconclusive experiments: absent from the paper.
- Submodule, `docs/idea-story.md`, and canonical scientific memory: unmodified.

## Build and rendered evidence

The complete `pdflatex -> bibtex -> pdflatex -> pdflatex` build succeeds.

- `docs/paper/main.tex` SHA-256:
  `867c82da723ee88eec8c2367cea0206b6ca404b6f0aa6394e2b4dfa42f5090bb`.
- `docs/paper/main.pdf` SHA-256:
  `0a61d625461ab8e43e180d47cbb2503fb2342eeb9f78f55a86c7a9fc88438ad6`.
- Bibliography SHA-256 remains
  `f044ea5eb5a5e3dba7aee92e2bbb8e634cad484b60428ae379e10cf48eca70c3`.
- PDF: nine US-letter pages.
- Main content and complete Conclusion: end on page 7.
- References begin at the bottom of page 7; pages 8--9 contain bibliography
  material only.
- Undefined citations/references: none.
- Overfull boxes: none.
- Remaining warnings: five cosmetic underfull boxes.

## Scientific impact and next action

The paper now uses more concrete actors, verbs, antecedents, and comparison
objects while retaining its strong original story. No idea, experiment,
literature, design, implementation, or search-tree state changed.

Next, Round 8 uses one serial read-only reviewer with
`check-terminology-infoflow` for invented terms, definition order, synonym
drift, and cross-section concept consistency, then `paper-writing-style` for
self-attacking sentences and claim-tone mechanics. The reviewer must not remove
scope-bearing qualifiers or convert an evidence objection into a weaker RQ or
claim. Completion requires root disposition, local fixes only, a full build,
and the same story/RQ/number/citation/page checks.
