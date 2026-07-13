# Round 5 — Paper And Artifact Consistency

**Started:** 2026-07-12T14:54:00-07:00  
**Completed:** 2026-07-12T15:11:13-07:00  
**Cycle/gate:** cycle 0001 / WRITE  
**Entry paper:** `docs/paper/main.tex` after Round 4  
**Method:** fresh read-only `check-terminology-infoflow` review in
paper-consistency scope, followed by source checks and subsection-sized root
fixes

> **Provenance correction — 2026-07-12T16:41:15-07:00.** The recorded
> Round 4--6 timestamps were reconstructed and overlap, so they do not prove
> strict serial execution. This report remains a content record, not a reliable
> chronological boundary. A fresh consistency repair and independent outer
> re-audit after all round outputs establish the final artifact state.

## Scope And Authoritative Inputs

The reviewer read the complete paper, `docs/idea-story.md`, the current design,
implementation, evaluation, and literature frontiers, the Rust implementation,
and the admitted experiment reports. The root checked each proposed fix against
the exact author-fixed thesis, the three fixed RQs, the artifact source, and raw
result provenance. No Git command or submodule operation ran.

## Must-Fix Findings And Disposition

| Finding | Evidence | Disposition |
|---|---|---|
| The paper implied direct AgentSight-recording ingestion and verified triggered-effect lineage. | Implemented inputs are Codex/Claude histories, operation JSONL, portable agent-session traces, and Chrome/Perfetto containers; RQ1 leaves trigger lineage open. | Corrected Implementation and `docs/implementation.md`; AgentSight evidence must enter a supported input and no verified trigger lineage is claimed. |
| The Rust inducer was called TF-IDF based. | `agentpprof/src/profile.rs` uses token-set Jaccard shift; TF-IDF/K-Means belongs to the optional Python rule-authoring backend. | Corrected the paper, Chinese source comment, and implementation frontier. |
| The time view was described as operation duration. | The artifact weights a timestamped event by elapsed time to the next event. | Corrected the paper and implementation frontier. |
| The RQ3 leave-one-out direction was reversed. | Each fold learns a deterministic mapping from eight datasets and applies it unchanged to the held-out ninth. | Corrected the method and its Chinese source comment. |
| Three rendered system names bypassed `\sys`. | Paper macro policy. | Replaced the rendered occurrences with `\sys{}`. |
| Canonical evaluation text retained the overbroad “manufacture failure signal” interpretation. | AgentRx/TELBench show unresolved AP gains and stronger controls, not global absence of visible failure signal. | Replaced it with the exact tested result in `docs/evaluation.md` and the paper comments. |

## Applied Should-Fix And Consider Findings

The architecture and Design now say that *available source-native path fields*
form a stack choice; the artifact does not reconstruct missing native lineage.
The architecture input includes operation JSONL. Hodoscope wording now refers
to the first published iQuest oracle-positive action. The RQ3 figure is
referenced, AgentRx/TELBench matching scope is explicit, and the Discussion
separates tested failure/anomaly localization from the untested additive
regression condition. The RQ1 caption now says “selected values.”

The formal model permits nonnegative weights, but imported zero is currently
normalized to one. The paper, Design, and Implementation now disclose that
artifact gap and state that admitted experiments use positive integer weights.
No reported result changes. The suggestion to add artifact version `0.2.37` to
the paper was rejected because the version is already bound in
`docs/implementation.md`, while the paper claim is about the audited current
artifact and page space is constrained.

## Narrative And Canonical-Document Audit

One residual story drift was found outside the paper:
`docs/background-related-work.md` still described hierarchy choice as the
paper-level Current Question and “strongest live position.” It now preserves
the author-fixed thesis—agent observability needs profiling, not only
debugging—as the broad literature question and classifies hierarchy choice as a
mechanism hypothesis inside it. This prevents a resume from promoting a
negative hierarchy result into a replacement thesis. `docs/design.md` now calls
the planned comparison the next decisive RQ2 experiment rather than the central
paper claim.

## Preservation And Build Evidence

- `make` completed with exit code 0.
- `main.pdf` is nine US-Letter pages.
- Technical content ends with the Conclusion on page 7; references occupy pages
  8--9.
- There are no undefined citations, references, controls, or fatal LaTeX
  errors.
- The paper retains 57 citation commands.
- The exact thesis appears verbatim three times: Abstract, Introduction, and
  Conclusion.
- No quantitative value or RQ meaning changed in this round.

BibTeX retains one non-blocking metadata warning because the `sdbl` entry has
both volume and number; Round 10 owns that citation-record repair.

## Remaining Scientific Gaps And Next Node

RQ1 independent source lineage, RQ2 real additive decision value and end-to-end
cost, and RQ3 unchanged transfer remain honestly unresolved. These are
EXPERIMENT work, not consistency edits. Round 6 now examines sentence
structure without changing scientific meaning, numbers, citations, or RQs.
