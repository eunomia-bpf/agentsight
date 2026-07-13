# Source And Protocol Audit — RQ2 Revision 1

## Context And Question

- **Cycle/gate/loop:** cycle 0001 / EXPERIMENT_GATE / RQ2 revision 1.
- **Status:** completed independent read-only source audit.
- **Question:** Which official real-world data, baselines, information regimes,
  metrics, and declared deviations make the scope-before-localization experiment
  scientifically comparable without narrowing the immutable RQ?

## Sources Inspected

- Who&When official repository commit
  `b2bae5c5b06d681d04ea5e9b63b7a30525c04925`: all 184 released trajectories,
  local/GPT all-at-once, step-by-step, and binary-search prompts, parser, and
  evaluator.
- TRAIL official repository commit
  `0ffbed9db859b4a66250dc783fa4dccf86869595`: all 148 raw OTel traces, processed
  annotations, official full-context prompt, and evaluator.
- SDBL official linked repository commit
  `9734e4c26b34e677997df2f750a74ae69dd21e41` and AAAI-26 paper. The repository
  contains only `We will release it soon`; RSD can follow the paper definition,
  while SSD/EASD are paper-faithful replications rather than official runs.

## Source Findings

Who&When's released runners always insert `ground_truth` into the prompt, while
the paper also studies a no-answer setting. Its evaluator uses substring
containment for actor and step, so actual step `1` can match prediction `12`.
The scientifically primary regime is therefore a thin no-answer adapter with
exact integer-step and normalized-actor equality; the released with-answer and
substring results remain labeled compatibility rows. The release contains 126
algorithm-generated and 58 handcrafted traces. Repeated `question_ID` and exact
questions require clustered rather than trajectory-independent bootstrap.
Because actor strings disagree with the labeled responsible actor in a material
minority, decisive-step accuracy is primary and actor/joint accuracy secondary.

TRAIL contains 117 GAIA and 31 SWE-Bench traces. Its official `location accuracy`
is gold-location recall and its aggregate may skip missing/unparseable outputs;
exact location precision/recall/F1 with all-148 intent-to-treat coverage is the
primary scientific metric. Unique LLM/TOOL spans are atomic candidates; native
CHAIN/AGENT nodes are structural scopes. All raw annotation arrays are empty.
The pinned release needs only three declared corrections: permissive parsing of
one trailing-comma annotation, deduplication of one byte-identical repeated span,
and exclusion of two literal `Span ID not found for this shard` error records
while retaining both traces and their other labels.

Three GAIA and one SWE-Bench annotation files contain no gold errors. They remain
part of all inference and no-error/false-positive evaluation but are not assigned
an invented denominator in gold-conditional scope recall or work-to-gold metrics.

An additional full-source pass found that TRAIL's nominally raw inputs contain
offline dataset answers: every GAIA trace has `true_answer` and human `Annotator
Metadata`, while 30 of 31 SWE-Bench traces have reference `patch` and
`test_patch`. The primary deployment-style projection removes those source-record
metadata fields for every method while retaining topology and genuine traced
agent outputs. Unmodified official raw input is compatibility-only.

The structural comparison must hold operation risk and visible information
constant while varying structure: proposed hierarchy, semantic leaf-only, flat,
fixed windows, fixed fields, source-native hierarchy, query-free hierarchy,
non-risk navigation, and matched random hierarchy. The downstream judge must be
identical within a dataset. A full-context TRAIL model overflow is a terminal
miss in all-trace results, not an excluded case.

## Scientific Impact And Decision

The audit strengthens rather than shrinks the claim: it tests the complete
two-stage mechanism on 332 fresh real traces and four source-native strata. It
also prevents answer leakage, weak substring scoring, giant-root scope wins,
pooled-average masking, and false claims of official SDBL execution. These rules
were integrated into the single current `experiment-plan.md` before Round 2.

## Completion And Next Action

The official-data/protocol source boundary is complete for plan review. Round 2
must independently judge whether the revised baselines, data handling, and
leakage rules are sufficient; no preflight is authorized yet.
