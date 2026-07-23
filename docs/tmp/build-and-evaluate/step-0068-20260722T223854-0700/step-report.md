# Step 0068 — Full-Paper Milestone Review

- **Timestamp:** 2026-07-22T23:12:30-07:00
- **Outer gate:** REVIEW
- **Status:** complete — paper verdict `REVISE`; review artifact independently
  audited `PASS`
- **Paper input:** `docs/paper/main.pdf`
- **Paper SHA-256:** `8e7c05e950b1ca3fd350b3b07873b300092c815ae77c4b90c991f037981ed7e3`

## Work completed

1. Grok 4.5 performed a fresh, confirmed paper-only read, primary-source
   search, full reread, and final AAAI/systems verdict.
2. Claude Opus performed a fresh-model full-paper review. Its final reference
   to a repository instruction is disclosed as context contamination, so it is
   not counted as a second clean blind vote.
3. The root reviewer independently verified official pprof, OpenTelemetry
   Profiles, LangSmith Insights, and primary papers for Graphectory,
   TraceProbe, Hodoscope, TraceGraph, AgentProcessBench, HINTBench,
   TraceElephant, and CodeTracer/CodeTraceBench.
4. Four required review reports separated blind read, external search, full
   reread, and cycle-change audit.
5. An independent outer audit reconstructed Table 1 at full precision, found
   four bounded issues in the review reports, and passed their corrections.

## Scientific result

The exact thesis remains strong and unchanged:

> **Agent observability needs profiling, not only debugging.**

The paper is currently a 4–5/10 weak reject / major revision, not because the
idea is too small, but because two writing-level defects obscure its evidence:

- RQ2 does not clearly separate the target-blind declared/reference hierarchy
  from the automatic Agent+Evidence backend. At full precision, automatic
  versus Raw is `-0.000665`, `+0.132752`, and `+0.130656`, whereas the reported
  `+.016`, `+.171`, and `+.109` belong to declared/reference versus Raw.
- The current paper narrows fixed RQ1 from “Does Semantic Profiling Improve
  Resource Attribution?” to whether one hierarchy exposes different
  bottlenecks.

The closest-capability gap against hierarchical trace categorization and
process-analysis tools remains a major risk. A same-input experiment is a
high-value candidate, not a pre-authorized mandatory gate. Any next experiment
must start from one fixed RQ and one claim.

## Product result

The hierarchy checker has the correct advisory semantics:

- zero semantic children is a legal leaf;
- one child under an optional semantic refinement emits a unary warning;
- broad unrefined leaves and large weakly recursive fan-outs emit separate
  warnings;
- session/prompt source scope is exempt where appropriate;
- warnings never block `.pb/.pb.gz` generation or determine a scientific gate.

This mechanical QA catches degenerate shape but does not manufacture semantic
depth. A flat-looking graph can pass the checker if its few shared levels are
genuine; improving that graph requires better cross-session operation
structure, not a larger minimum-depth constant.

## Next gate

Run targeted WRITE first:

1. restore the fixed RQ1 wording and bound the current evidence precisely;
2. make every RQ2 declared/reference-versus-automatic claim unambiguous at full
   precision;
3. keep the thesis, four RQs, abstract/introduction architecture, and table
   values unchanged;
4. perform a complete consistency reread before selecting another experiment.

## Artifact index

- `milestone-review-001/reviewer-grok-4.5-transcript.md`
- `milestone-review-001/reviewer-claude-opus.md`
- `milestone-review-001/01-blind-full-read.md`
- `milestone-review-001/02-external-search-source-verification.md`
- `milestone-review-001/03-full-paper-reread-assessment.md`
- `milestone-review-001/04-cycle-audit-final-verdict.md`
- `milestone-review-001/outer-audit.md`

