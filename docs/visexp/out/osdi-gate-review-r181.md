# R181 OSDI Gate Review

Last updated: 2026-06-15
Stage at update: audit / supplement
Source/command: read-only subagent review after R180 local multi-model benchmark
Completeness: complete

## Verdict

Maturity: Level 3 conference-paper mechanism evidence, not Level 4 systems
narrative.

OSDI weak accept: not reached.

## Highest-Risk Gap

C5 user utility remains unsupported. The artifacts correctly say there are
packets, preregistration, and scorers, but no participant responses. Any claim
that AgentFlame makes developers faster or more accurate is still an overclaim.

## R180 Scope Check

R180 is correctly scoped. It supports local syntax, latency, and repeated-input
stability only:

- 2700/2700 valid one-word outputs.
- 0.6b exact stability 299/300, p95 23 ms.
- 1.1b exact stability 279/300, p95 18 ms.
- 3b exact stability 285/300, p95 32 ms.

The R180 artifact explicitly says the compared GGUFs use different model
families or quantization paths, so it is not a controlled same-family scaling
result. It also explicitly says R180 does not measure human adequacy.

The paper mirrors this boundary and names the TinyLlama 1.1B localization-like
collapse as evidence that grammar/stability is not adequacy.

## Must-Fix Gaps

- C6 tag adequacy is still partial. R124 has 300 candidate rows but 0 final
  human labels and `adequacy_supported=false`. Independent human labels,
  adjudication, and scoring are required before claiming semantic adequacy.
- Controlled model scaling is not supported. The paper must continue avoiding
  claims such as "scaling curve", "smaller models are adequate", or "model size
  improves quality" unless same-family 0.6B/1B/3B models are rerun.

## Decision

Keep the R180 wording. Do not upgrade C5 or C6. The decisive missing evidence
remains human tag adequacy plus scored developer-task utility.
