# Round 1 — Micro Structure and Local Flow

Started: 2026-07-19T19:29:22-07:00
Completed: 2026-07-19T19:40:58-07:00
Parent: BOOTSTRAP step 0001 / WRITE_GATE
Objective: align paragraph roles and local argument order while preserving the fixed automatic-supervision claim and the absence of experimental results.

## Baseline and method

Round 1 began from the compiled Round-0 AAAI draft with SHA-256 `0c59534d10c3fa50e4fda30d1b984d5261cd55154f1e6d8c4495c6f530073845`. A fresh read-only reviewer read the complete paper and applied Levels 2--3 of `check-paper-structure-flow`: paragraph role, why-before-what ordering, old-to-new sentence flow, topic-sentence placement, and local overload. The root inspected every finding, applied bounded edits, rebuilt the paper, and checked the diff and citations.

## Raw findings

The reviewer identified seven must-fix issues: abstract and Introduction role order; unsupported present-tense claims that the closed evaluation had run; an action tuple lacking the source payload needed to derive artifact effects; use of `id_i` before definition; Design subsections beginning with mechanism rather than motivation; accidental derived state in the raw-log path; and RQ3 lacking an operational harness-localization protocol. Secondary issues included dense unreferenced requirements, overloaded implementation and metric paragraphs, RQ2 rationale after its controls, repeated result-interpretation prose, mixed limitations, list-like Related Work openings, and disproportionate visual-export detail.

## Applied fixes

1. Reordered the abstract into problem, closest-method gap, workspace insight, representation, supervisor use, and planned matched-budget evaluation. Removed the trailing generic reframing sentence.
2. Reassembled the Introduction into longitudinal setting, supervision failure and structural cause, closest work and exact gap, workspace insight, method/evaluation, and contributions.
3. Replaced `we evaluate` and `specify and execute` with future or protocol language. The manuscript now states no completed automatic-diagnosis experiment.
4. Added native source record $r_i$ to the action tuple and stated that artifact projection dereferences its tool arguments and result. Defined $id_i=(s_i,c_i)$ before the trajectory sort.
5. Added why-before-what openings to all three Design mechanisms: retaining no-file actions, maintaining lifecycle state, and bounding query access.
6. Changed `each path has state` to a workspace-only state. The raw condition remains bounded retrieval over native records.
7. Grouped six inline requirements into continuity, evidentiary fidelity, and fair bounded comparison.
8. Split workspace affiliation from episode construction and removed a full paragraph on global path matching from the evaluated implementation.
9. Reduced visual replay to one auxiliary sentence that explicitly excludes it from diagnostic inputs and outcomes.
10. Split metrics from uncertainty/sampling; moved RQ2's confounding rationale before controls and ablations.
11. Expanded RQ3 with harness mechanism, artifact/version, canonical evidence, and earliest-intervention outputs and corresponding metrics before grouped generalization.
12. Separated evidence coverage from episode-boundary ambiguity, moved optional system evidence to Evaluation Limitations, removed duplicated possible-result prose from Discussion, and added synthesis openings to Related Work groups.

## Rejected or deferred changes

- The post-table interpretation remains because its new role is to justify the matched raw-log comparison, not merely restate the table.
- Implementation and query names remain concrete rather than being compressed further; they define the mechanism needed for a reproducible paper.
- Underfull boxes around the long canonical evidence identifier remain non-blocking and will be considered in sentence-level rounds.
- No result placeholder was filled, and no scientific RQ, pathology definition, consumer, or comparison condition changed.

## Preservation audit

The automatic diagnoser/supervisor remains the sole evaluated consumer. Human experts only create and adjudicate reference labels. RQ1--RQ3 retain their fixed meanings; RQ3 is more operational but not broader. The experiment remains closed and contributes no evidence. The motivating counts remain descriptive. Citation commands remain 20 and the verified bibliography remains 12 entries.

## Validation

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: success.
- PDF: 7 pages, 242,369 bytes.
- No overfull box, negative label-width, undefined citation, or undefined reference warning.
- `git diff --check`: success.
- Exit `main.tex` SHA-256: `fc724112f6d1df561b71751a252ef533dc3f80bb1baea00707e085d3fb3c95c6`.

## Next node

Round 2 checks venue and section conventions: abstract/Introduction correspondence, motivation, Design, Implementation, RQ-shaped Evaluation, Related Work, limitations, ethics, and conclusion roles. It must report rather than repair any scientific-contract defect.
