# AAAI-27 Reproducibility Checklist — DRAFT (fill into the official Author Kit form at submission)

Paper: "Are Long-Running Agents Making Progress? A Longitudinal Study of Artifact Progress, Repeated Mutation, and Continuity"

## Method description
- Conceptual outline of the measurement method: YES — §Method (source-linked projection, artifact identity, lifecycle effects, session boundaries) plus supplement pseudocode of the extraction pipeline.
- No trained models, no theory, no hyperparameter search. The only learned/LLM component (bounded Raw-log reader) is N/A and reported as such.

## Claims and experiments
- Every empirical claim (RQ1–RQ6, measurement capability) is backed by a deterministic, recomputable pipeline. Claims explicitly limited by coverage gates are stated with their stop conditions (RQ4 estimator gate: data-limited).

## Data
- Corpus: native Claude/Codex/Gemini session records + Git state from six author-associated local projects (551 native-root sessions, 181,303 actions at the cutoff).
- Raw session records contain private prompts/paths and are NOT redistributable; the released artifact contains: exported per-project rows (source-linked CSV/JSON), question set + expected answers for the 120-question conformance benchmark, and all analysis code. Project identities are already disclosed in the paper as author-associated.
- Public external corpora used for RQ6: Open-SWE-Traces (256 task selections) and IdeaTrail (64 topics) — publicly available.

## Code
- Extraction/projection: `agent-session/` (Rust), `agentvis/` (Rust) in the repository.
- Analysis/figures: `agentvis/research/plot_rq1.py`–`plot_rq7.py`, `rq7_measurement.py`, `rq7_source_oracle_check.py` (v4 oracle).
- Conformance benchmark scripts + corrected answers: `docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/` (will move to a stable artifact path).
- RQ1–RQ4 recompute rows + commands: `docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/` (incl. commands.log).
- Environment: Python 3 + matplotlib; Rust stable; no GPU, no external API. Deterministic: all statistics recomputable from exported rows (independent audit regenerated main figures byte-identically).

## Known limits (state honestly, one line each)
- Six author-associated projects: selection bias acknowledged; external boundary (RQ6) separates replicable within-attempt relations from non-exportable longitudinal ones.
- Conformance 60/60 B+C is repair-corpus conformance on the frozen question set; no general exact-fact capability claim.
