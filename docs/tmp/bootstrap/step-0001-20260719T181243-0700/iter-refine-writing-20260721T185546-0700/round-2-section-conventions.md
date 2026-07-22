# Round 2 — Section Conventions

## Independent review

Reviewer: `writing_round2_conventions` (read-only).

The paper was close to convention-clean. The reviewer required an explicit
abstract hypothesis, a distinction between prospective protocol and realized
P0 configuration, corrected `unanswered` wording for RQ2/RQ3, separation of the
mechanics run from the headroom screen, and removal of the red result placeholder.

## Applied changes

- mirrored the Introduction's bounded-access hypothesis in the abstract;
- opened the prior-work paragraph with its actual gap;
- distinguished construction invariants from protocol controls and empirical
  utility in Design;
- moved treatment engagement ownership to Evaluation;
- compressed auxiliary media details in Implementation;
- made RQ3 explicitly conditional on a supported RQ1 effect;
- renamed the shared block `Prospective Experimental Protocol and Analysis`;
- added the actual P0 worker/supervisor models, revisions, budgets, request
  sizes, latency, continuation count, and oracle count;
- stated that RQ2 never opened because the RQ1 matrix was not admitted;
- converted the RQ3 result placeholder into ordinary evidence-required prose;
- split privacy from intervention-harm ethics; and
- separated the mechanics validation from the independent headroom stop in the
  conclusion.

## Validation

- no result placeholder remains;
- no text says RQ1 was unsupported by a completed effect test;
- LaTeX compile: PASS;
- compiled length: 6 pages;
- undefined citations/references: none reported.
