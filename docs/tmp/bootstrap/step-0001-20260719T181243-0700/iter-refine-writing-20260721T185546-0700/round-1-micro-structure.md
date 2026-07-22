# Round 1 — Micro Structure

## Independent review

Reviewer: `writing_round1_micro` (read-only).

The reviewer found no contract drift. Main issues were paragraph-role and flow:
the Introduction ended on evaluation status after the contribution list; RQ
subsections did not restate their question; RQ1 compressed the zero-tool-call
and headroom stops; RQ2 used completed-experiment tense; RQ3 ended on a result
placeholder; and the protocol defined its unit twice.

## Applied changes

- moved the negative evaluation-status paragraph before the contribution list;
- opened every RQ subsection with its explicit question;
- separated the P0 treatment-engagement failure from the independent headroom
  stop in the RQ1 conclusion;
- changed RQ2 ablations to prospective conditional tense;
- moved the RQ3 placeholder before its explicit unanswered conclusion;
- defined `(C,F)` once and then described its instantiation;
- foregrounded executable-oracle truth before the estimands;
- clarified that only a Trajectory tie with Raw at lower Trajectory retrieval
  cost supports compression; and
- split intervention-message and benchmark-external-validity limitations.

The abstract now says `no treatment-effect estimate`, avoiding the false
implication of a measured null effect.

## Validation

- no literal patch artifacts remain;
- LaTeX compile: PASS;
- compiled length: 6 pages;
- undefined citations/references: none reported.
