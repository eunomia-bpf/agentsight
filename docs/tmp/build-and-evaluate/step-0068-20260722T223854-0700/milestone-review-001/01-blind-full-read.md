# 01 — Blind Full-Paper Read

- **Timestamp:** 2026-07-22T22:56:00-07:00
- **Parent:** `step-0068-20260722T223854-0700/milestone-review-001`
- **Objective:** obtain independent paper-only assessments before exposing reviewers to project history, user instructions, experiment reports, or prior reviews
- **Paper input:** `docs/paper/main.pdf`
- **Paper SHA-256:** `8e7c05e950b1ca3fd350b3b07873b300092c815ae77c4b90c991f037981ed7e3`
- **Reviewers:** Grok 4.5 and Claude Opus, each in a fresh non-resumed session

## Method and provenance

Both reviewers received `reviewer-brief.md`. The brief required a complete
AAAI-level read spanning AI/ML and systems standards, an attack map, a second
read after external source verification, exact routing of findings to
EXPERIMENT or WRITE, and protection of the largest ambitious claim worth
defending. Neither reviewer received `docs/idea-story.md`,
`docs/user-instruction.md`, experiment logs, Git history, or earlier review
reports in the explicit prompt before its initial verdict. Grok's complete
transcript is the confirmed clean paper-only review. Claude was run in a fresh
session, but its final report refers to a `CLAUDE.md` invariant, showing that
repository instructions entered its context automatically; Claude is therefore
an independent fresh-model review with disclosed repository-context
contamination, not a second clean blind vote.

The complete Grok interaction is retained in
`reviewer-grok-4.5-transcript.md`. Claude's final report is retained in
`reviewer-claude-opus.md`. This report records the shared paper-only reading;
it does not treat agreement between language models as ground truth.

## Paper-only reconstruction

Both reviewers reconstructed the same core paper:

1. per-run tracing explains one execution, whereas fleet-scale agent
   engineering also needs recurring cross-run attribution;
2. AgentProf annotates an ordered source tree with reusable semantic
   responsibilities;
3. it folds additive measures under those responsibilities and emits standard
   pprof profiles rather than a custom visualization frontend;
4. four RQs address multi-resource attribution, correspondence to real
   problems, automatic operation structure, and profile-construction cost.

Both independently retained the thesis **“Agent observability needs profiling,
not only debugging.”** Neither judged the right repair to be shrinking the work
to “a pprof exporter.” Grok called the paper *incomplete-but-promising* and
scored it 5/10; Claude used the same class and scored it 4/10.

## Initial strengths

- The profiling analogy is memorable and has durable systems content:
  recurring semantic responsibility plus conserved additive measures.
- The artifact is real, produces standard profiles, and cleanly avoids a
  paper-specific frontend.
- The paper is unusually explicit about evaluation boundaries, including the
  difference between core profile-construction cost and annotation cost.
- The two complete-population cases are more persuasive than cherry-picked
  traces: one compares resource measures over repeated long-horizon work, and
  one aggregates all 338 bad--good pair occurrences.
- Headline numbers, except for the attribution issue below, were internally
  consistent across abstract, tables, and conclusion.

## Initial reject map

### B1 — The paper has not yet forced the thesis empirically

Both reviewers concluded that the evaluation shows useful grouping and profile
construction but does not yet demonstrate, against the closest hierarchical
or process-analysis alternatives, that the *profiling abstraction* changes a
real population-level decision. This is an evidence gap, not permission to
weaken the thesis.

### B2 — RQ2's prose conflates the declared/reference hierarchy with the
automatic backend

Claude identified a concrete paper-only inconsistency. Table 1 reports:

| Workload | Declared semantic | Raw | Automatic Agent + evidence | Automatic Agent only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .789 | .773 | .773 | .730 |
| HINTBench | .452 | .281 | .414 | .284 |
| TraceElephant | .230 | .121 | .252 | .194 |

The following prose calls `+.016`, `+.171`, and `+.109` AgentProf's gains over
raw action. Those are the **target-blind declared/reference semantic hierarchy
minus raw** differences, not the automatic Agent+Evidence differences. At full
precision, the automatic differences are `-0.000665`, `+0.132752`, and
`+0.130656`. The declared hierarchy is not a human-label oracle: its grouping
and scores were fixed before evaluator targets entered. This remains a
WRITE-level scientific-attribution defect. Fixing it does not alter the thesis
or any RQ; it makes the declared and automatic AgentProf configurations
impossible to confuse.

### B3 — RQ1 wording is narrower than the fixed RQ

The project memory fixes RQ1 as “Does Semantic Profiling Improve Resource
Attribution?” The current paper asks only whether one hierarchy “expose[s]
different resource bottlenecks.” A resource-dependent rank shift is relevant
evidence, but the narrower wording is not an authorized replacement for the
fixed attribution question.

### Major concerns

- The closest product and research alternatives are discussed but not tested
  head-to-head on the same diagnostic question.
- RQ1's strongest resource-shift evidence is one repeated Git task, even
  though the source collection contains more sessions.
- RQ3 combines several protocols and backend types; the one automatic
  recursive constructor obtains strong partition agreement relative to
  controls but only modest exact-boundary F1.
- The figures are authentic stock-profiler outputs, but dense labels and
  shallow shared prefixes make the collection-scale differential panel harder
  to read at paper size.
- Terms such as semantic operation stack, recursive annotation,
  responsibility, stage, and group are individually meaningful but compete for
  the same limited reader vocabulary.

## Decisions

- Preserve the exact thesis and the four RQs.
- Treat B2 and the RQ1 wording drift as mandatory corrections at the next
  WRITE gate.
- Do not mechanically accept every requested experiment. The external-search
  and reread nodes may identify a decisive same-input comparison as a
  high-value candidate, but the EXPERIMENT gate must select one fixed RQ, one
  claim, one runnable baseline, and one accepted metric.
- Keep hierarchy warnings as product-quality diagnostics. They do not
  constitute evidence for B1 and must not become depth or acceptance gates.

## Completion and uncertainty

**Status: complete after provenance correction.** One confirmed clean
paper-only review and one fresh-model review with disclosed repository-context
contamination agree on the durable idea and the main evidence gap. Their scores
are advisory. The exact RQ2 arithmetic can be checked directly and is therefore
promoted from reviewer opinion to a verified must-fix candidate. Novelty and
closest-work claims remain pending external source verification in node 02.
