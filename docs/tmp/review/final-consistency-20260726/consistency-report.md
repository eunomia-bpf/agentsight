# Final Consistency Report

Date: 2026-07-26  
Target: `docs/paper/main.tex`  
Mode: read-only audit; the paper was not edited

## Verdict

**FAIL.** The four requested numerical blocks match their experiment records at
the precision printed in the paper, all references resolve, the thesis occurs
exactly three times, and a fresh build succeeds. However, the paper has three
Case Study 3 consistency defects and the four RQ subsection titles do not match
the author-fixed titles verbatim.

## 1. Inconsistencies found

### Major: Case Study 3 population is misqualified

- **Paper:** `docs/paper/main.tex:772`
- **Actual:** “all **42 long-horizon development sessions**”
- **Expected:** 42 development-session records, **10 of which are classified as
  long-horizon**, or wording that does not qualify all 42 as long-horizon.
- **Source:** `docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/000-step-entry.md:11-15`
  records 42 local sessions and 10 long-horizon sessions. The independent
  review also notes that the 42 frozen records contain 31 distinct native
  `source_session` strings.

### Major: abstract still counts only two population case studies

- **Paper:** `docs/paper/main.tex:52-54`
- **Actual:** “two population case studies” / “两个 population case study”
- **Expected:** three population case studies / 三个 population case study,
  because the paper contains Case Studies 1, 2, and 3 at lines 530, 707, and
  769.

### Major: evaluation population inventory omits Case Study 3

- **Paper:** `docs/paper/main.tex:501-503` and the mirrored comment at line 511
- **Actual:** the “real inputs (RQ1, cases)” inventory lists only 41
  long-horizon benchmark trajectories and 440 mixed-outcome web-agent
  trajectories.
- **Expected:** it must also list the separate 42-record author-workstation
  development population used by Case Study 3. It should not silently add 41
  and 42 because they are different populations.
- **Source:** Step 0086 `results.md:54-70` records 42 frozen sessions
  (18 Codex, 24 Claude), 10,423 nodes, and the complete Case Study 3 population.

### Major: all four RQ subsection titles differ from the author-fixed titles

The expected titles are recorded in `docs/idea-story.md:183-197`; RQ3 is
reaffirmed as exact at `docs/idea-story.md:621`.

| Paper location | Actual | Expected |
|---|---|---|
| `docs/paper/main.tex:514` | `RQ1: Multi-Resource Attribution` | `RQ1: Does Semantic Profiling Improve Resource Attribution?` |
| `docs/paper/main.tex:602` | `RQ2: Problem Correspondence` | `RQ2: Does Profiler Output Correspond to Real Problems?` |
| `docs/paper/main.tex:819` | `RQ3: Automatic Operation Structure` | `RQ3: How Accurate Are the Tags?` |
| `docs/paper/main.tex:916` | `RQ4: Profiling Cost` | `RQ4: What Is the Profiling Cost?` |

The current headings preserve the four broad subjects, but they do not satisfy
the requested verbatim “unchanged titles” check.

## 2. Numerical source audit

Citation years embedded in citation keys are not experimental claims and are
excluded from this comparison.

### RQ1 tau-b paragraph — PASS

Paper: `docs/paper/main.tex:582-596`  
Source: Step 0078 `experiment-001/results.md`, `raw-results.json`, and
`result-review.md`

All printed values match, including:

- 440 sessions, 125 tasks, 7,229 operations, and 51,904,621 tokens;
- 77 rankable tasks with at least three distinct operations;
- Kendall tau-b 0.886 with 95% interval [0.857, 0.915];
- Spearman rho 0.935 with interval [0.917, 0.953];
- 10,000 task-cluster bootstrap draws;
- pooled tau-b 0.929;
- 10 of 77 tasks below tau-b 0.7.

The paper's three-decimal values are correct roundings of the source values
0.8863098, [0.8568203, 0.9147109], 0.9349872,
[0.9165994, 0.9527056], and 0.9285739.

### Profile-guided reading paragraph — PASS

Paper: `docs/paper/main.tex:673-705`  
Sources: Steps 0079, 0080, and 0081 result and review records

All printed values match:

- 220 target-bearing queries and a five-group selection budget;
- full-reader MAP .502 versus .209 and .326, with 12,615 mean input tokens;
- semantic profile reader MAP .455 and 53.0% source content opened;
- raw-action reader MAP .465 and paired delta +.010
  [-.021, +.042];
- 65.0% versus 53.0% opened content, paired delta +.120
  [+.103, +.137];
- 2.80 [1.96, 3.60] additional evidence operations;
- the 4,558,192-token Git context-window example.

The 53.0%/65.0% comparison is repeated consistently in the abstract
(`main.tex:60-64`), introduction (`main.tex:179-184`), and body.

### RQ4 annotation-cost paragraph — PASS

Paper: `docs/paper/main.tex:947-958`  
Source: Step 0077 `first-pass-cost-and-aggregate.md` and
`git-convergence-result.md`

All printed values match or are correctly rounded:

- 440 sessions, 12 outcome-blind batches, and a fixed two-worker schedule;
- 3,521.6 s / 58.7 min critical path and 6,661.7 s summed worker time;
- 12,039,417 actual input tokens, 10,929,408 cached input tokens, and
  312,433 output tokens;
- 27,362 input and 710 output tokens per session;
- three-session Git pass: 466.9 s and 832,544 input tokens;
- deterministic materialization: 0.26 s for operation width and 0.25 s for
  token width.

The adjacent 54.36-minute artifact-envelope paragraph is consistently repeated
in the scope appendix and is explicitly distinguished from model latency.

### Case Study 3 detailed values — PASS except the long-horizon qualification

Paper: `docs/paper/main.tex:769-816`  
Source: Step 0086 `results.md`, `aggregate-summary.md`, `cost-record.md`, and
`independent-result-review.md`

The following values all match:

- 42 records split as 18 Codex and 24 Claude;
- 10,423 nodes: 42 session, 1,252 prompt, 5,620 LLM, and 3,509 tool nodes;
- 1,380,863,014 bounded token mass;
- 1,737 annotations at semantic depths 2--4;
- 1,294 mandatory scopes, zero backend failures, and 42 completed batches;
- exact profile masses 3,509 and 1,380,863,014;
- largest token path share 1.735%;
- depth shares 70.4% and 43.9%, correctly rounded from 70.363% and 43.859%;
- three workers, 44.6-minute critical path, 15,231,328 input tokens,
  13,112,320 cached tokens, 311,097 output tokens, and 0.211 s validation.

The only defect inside the case is attaching “long-horizon” to all 42 records;
the source records 10 long-horizon sessions.

## 3. Thesis and RQ checks

- **Thesis count: PASS.** The exact sentence
  `Agent observability needs profiling, not only debugging.` occurs exactly
  three times, at `main.tex:44`, `main.tex:144`, and `main.tex:1018`.
- **Four-RQ count and order: PASS.** Exactly four RQ subsections occur, in the
  required attribution, problem-correspondence, tag/structure, and cost order.
- **RQ title wording: FAIL.** See the four verbatim mismatches above.

## 4. References, appendix pointers, and build

- **Checked-in `docs/paper/main.log`: PASS.** It is newer than `main.tex` and
  contains zero undefined-reference, undefined-citation, multiply-defined,
  or rerun-needed warnings.
- **Reference targets: PASS.** All 13 unique `\ref` targets in `main.tex` have
  matching `\label` definitions and `main.aux` entries.
- **Appendix pointers: PASS.** All nine appendix pointers resolve:
  `app:canonicalization`, `app:recurrence`, `app:rq2-scoring`,
  `app:osworld`, `app:partition`, `app:literal`, `app:cost`,
  `app:a2-reconstruction`, and `app:scope`.
- **Fresh build: PASS.** `latexmk -pdf -interaction=nonstopmode
  -halt-on-error -file-line-error` completed from scratch in
  `/tmp/agentprof-final-consistency.1tZuIM`, producing a 12-page PDF with exit
  status 0 and zero undefined references or citations in the final log.
- The final checked-in and fresh logs each contain 15 nonfatal underfull-box
  diagnostics and zero overfull boxes. These do not block compilation, but the
  build is not literally free of all typesetting diagnostics.

## 5. Minimal corrections

No correction was applied because this audit is read-only. The minimal paper
changes are:

1. restore the four exact author-fixed RQ titles;
2. change the abstract's case-study count from two to three in both English and
   Chinese;
3. add the Step 0086 42-record population to the evaluation inventory in both
   English and Chinese;
4. replace “42 long-horizon development sessions” with “42 development-session
   records, including 10 long-horizon sessions,” or remove the universal
   long-horizon qualification and retain the 31-distinct-native-session caveat
   where scope is discussed.

After those edits, rerun the same source-number, reference, and clean-build
checks.
