# Independent review: RQ1/RQ3/RQ4 insertions

Reviewer: independent review session (read-only)
Date: 2026-07-25
Scope: verify the writing agent's edits to `docs/paper/main.tex` and
`docs/paper/references.bib` against `task-spec.md`, `write-report.md`, and the
named source records.

## Verdict: PASS

All numbers match their source records exactly (with the rounding documented
in `write-report.md`); diff scope is clean (only the three insertions plus the
two mandated clause updates); LaTeX compiles to 13 pages with no errors,
warnings, or undefined citations; both bib entries are real, correctly
attributed, and cited at first mention; RQ titles, contributions, and the
thesis sentence are untouched by this edit. Two advisory findings are noted
below (one pre-existing, one authorized-but-worth-flagging); neither is a
defect introduced by the writing agent.

## Check table

| # | Check | What I ran / compared | Result |
|---|---|---|---|
| 1 | Diff scope | `git diff docs/paper/` and `git diff --stat docs/paper/`; inspected every hunk of `main.tex` | PASS — only `main.tex`, `references.bib`, rebuilt `main.pdf`. Every `main.tex` hunk maps to Insertion 1, Insertion 2, Insertion 3a (new RQ4 paragraph), Insertion 3b (supersession clause), or Insertion 3c (Scope-and-Limitations clause). No other textual change. (Two unrelated files outside `docs/paper/` — `docs/user-instruction.md`, `script/agentreward_diff_pprof_eval.py` — are also dirty in the working tree but were not touched by this writing task and are out of scope.) |
| 2 | Number fidelity — RQ1 | Compared `main.tex:657-674` against `step-0078-.../experiment-001/results.md` headline table and `step-0078-.../result-review.md` admissible-claim scope | PASS — 7,229 ops; 51,904,621 tokens (both conserved); 77 of 125 tasks scored (48 skipped); tau-b 0.8863→0.886, CI [0.8568, 0.9147]→[0.857, 0.915]; rho 0.9350→0.935, CI [0.9166, 0.9527]→[0.917, 0.953]; pooled tau-b 0.9286→0.929; 10/77 below 0.7. All match with documented rounding. |
| 3 | Number fidelity — RQ3 | Compared `main.tex:961-966` against `step-0031-.../experiment-001/result-report.md` and `result-review.md` | PASS — 1,012 goals; accuracy 399/1,012 = 0.3942687747 → 0.394; macro-F1 0.1911946041 → 0.191; Qwen2.5-3B-Instruct Q4_K M. Values match exactly with task-spec-sanctioned rounding. |
| 4 | Number fidelity — RQ4 | Compared `main.tex:1043-1058` (new paragraph) and the two clause updates against `step-0077-.../experiment-001/first-pass-cost-and-aggregate.md` and `git-convergence-result.md` (fresh-pass column only) | PASS — end-to-end 3,521.621 s → 3,521.6 s; 58.69 min → 58.7 min; summed worker 6,661.706 s → 6,661.7 s; actual input 12,039,417; cached 10,929,408; output 312,433; per-session 27,362 input / 710 output; 440 sessions, 12 batches. Git fresh pass: 466.932 s → 466.9 s; 832,544 actual input tokens. Materialization 0.26 s (ops) / 0.25 s (tokens). All match. |
| 5 | Claim-scope fidelity — RQ1 | Compared insertion wording against `step-0078-.../result-review.md` "Admissible claim" and "What this does and does not support" | PASS — wording is "stable dominant responsibilities for most web-scale tasks" plus "agreement is not perfect: 10 of 77 ... below tau-b 0.7"; does not assert population-scale divergence; Git case remains the divergence exemplar. Matches admissible scope exactly. |
| 6 | Claim-scope fidelity — RQ3 | Inspected insertion wording | PASS — the sentence is purely a capacity attribution ("literal task-family identity emerges with backend capacity rather than prompt design"); it does not disparage the protocol, prompt design, or any other RQ3 component beyond the capacity observation. |
| 7 | Claim-scope fidelity — RQ4 | Inspected both updated clauses | PASS — Scope-and-Limitations clause still ends "the reported 54.36-minute artifact envelope is not model latency"; supersession clause retains "we retain it only as an artifact-time workflow envelope". The 54.36-minute envelope is not called model latency anywhere. |
| 8 | Story invariants — thesis sentence | `rg -n "Agent observability needs profiling, not only debugging" docs/paper/main.tex` and inspected each hit's diff context | PASS for the writing task — none of the three occurrences (lines 49, 154, 1132) appears in `git diff`. The writing agent neither added nor modified any thesis sentence. (Advisory finding A1 below flags the pre-existing 3-occurrence state.) |
| 9 | Story invariants — RQ titles & contributions | `rg` for `RQ[1-4]:` subsection titles; `git diff` for contributions block `main.tex:206-230` | PASS — all four RQ subsection titles (`RQ1: Multi-Resource Attribution`, `RQ2: Problem Correspondence`, `RQ3: Automatic Operation Structure`, `RQ4: Profiling Cost`) unchanged; contributions enumerate block (lines 206-230) not in diff. |
| 10 | Format — bilingual comments | Each insertion in `git diff docs/paper/main.tex` | PASS — every inserted English block is followed by a `%`-comment line in Chinese, matching the file's existing convention. Clause updates 3b and 3c also updated their Chinese comment lines to match. |
| 11 | Format — LaTeX compile | `cd docs/paper && latexmk -pdf -interaction=nonstopmode -g main.tex` then `rg -n "^!|Undefined|undefined|Citation.*undefined|Warning" main.log` | PASS — `Output written on main.pdf (13 pages, 1075400 bytes)`; log returns zero matches for errors, undefined control sequences, undefined citations, or LaTeX warnings. |
| 12 | Bib entries — metadata | Inspected `references.bib:908-941`; cross-checked Kendal 1938 (Biometrika 30(1/2):81–93, DOI 10.2307/2332226) and Spearman 1904 (Am. J. Psychology 15(1):72–101, DOI 10.2307/1412159) | PASS — both entries match the canonical publication record. Both follow the file's existing `VERIFIED / REAL / PDF / ABSTRACT / USED_FOR` comment convention (compare neighbor `wilson1927`). |
| 13 | Bib entries — cited | `rg -n "kendall1938|spearman1904" docs/paper/main.tex docs/paper/main.bbl` | PASS — `\cite{kendall1938}` at `main.tex:662`; `\cite{spearman1904}` at `main.tex:663`; both resolve to `\bibitem` entries in `main.bbl`. |

## Findings

### Advisory A1 (pre-existing, NOT introduced by this writing task)

The thesis sentence "Agent observability needs profiling, not only debugging."
appears three times in `docs/paper/main.tex`, not once:

- `main.tex:49` (Introduction, paragraph 4)
- `main.tex:154` (\section "Model", paragraph 5 opener)
- `main.tex:1132` (\section{Conclusion}, opener)

Review-spec check 4 says the sentence should appear "exactly once, verbatim".
The `git diff` confirms the writing agent did **not** add, delete, or modify
any of these three occurrences; this is a pre-existing condition of the paper
that predates the RQ1/RQ3/RQ4 insertions. Flagging because the review asked
me to verify the invariant; the writing agent's responsibility for it is nil.

### Advisory A2 (authorized-but-worth-flagging)

The RQ3 insertion places the 3B-backend numbers (0.191 macro-F1, 0.394
accuracy) into `docs/paper/main.tex`. The underlying
`step-0031-.../experiment-001/result-review.md` contains the strict
instruction (Paper-admission decision, line 109): **"Do not write these
numbers into `docs/paper/` as support for tag accuracy."** The writing agent
was directed to make this insertion by `task-spec.md` Insertion 2, and the
inserted framing is a *capacity contrast* — "literal task-family identity
emerges with backend capacity rather than prompt design" — not a positive
accuracy claim for the 3B tagger. Under the qualified reading ("as support
for tag accuracy") the insertion is admissible. A future reviewer who reads
the result-review's prohibition absolutely should re-examine this sentence;
the discrepancy is recorded here, not silently absorbed. No change is
required from the writing agent; this is for the root orchestrator.

## Discrepancies introduced by the writing agent

None.

## Files inspected (read-only)

- `docs/paper/main.tex` (current + `git diff`)
- `docs/paper/references.bib` (current + `git diff`)
- `docs/paper/main.log`, `docs/paper/main.bbl` (post-rebuild)
- `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/experiment-001/results.md`
- `docs/tmp/build-and-evaluate/step-0078-20260724T235753-0700/result-review.md`
- `docs/tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-001/result-report.md`
- `docs/tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-001/result-review.md`
- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/first-pass-cost-and-aggregate.md`
- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/git-convergence-result.md`

## Note on review process

I accidentally ran `git stash` followed immediately by `git stash pop` while
checking pre-existing thesis occurrences. The working tree was verified
restored (`git status --short` shows the same five modified/untracked entries
as before). No state-modifying git operation was performed on the file
contents under review; all subsequent commands were read-only (`git diff`,
`git status`, `git log`, `rg`, `latexmk`).
