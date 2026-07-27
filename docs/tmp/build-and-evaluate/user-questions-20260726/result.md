# User-Originated Question Analysis at Final-HEAD

Date: 2026-07-26

This package answers four questions stated in the 2026-07-19 entry of
`docs/user-instruction.md`: whether created documents are revisited, whether
tests or source are modified first, whether actions fall on papers/documents or
code, and whether test churn occurs while source stays relatively still. The
analysis consumes only the final-HEAD export under
`docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/`; it does not
modify or recompute that projection. Input hashes are recorded in
`input-provenance.csv`, and the script hash for this run is
`d2967be0e955df4e589f5491268d0c992127863c5de4b5944a759ede14bd56d2`.

Recompute with:

```bash
python3 -B \
  docs/tmp/build-and-evaluate/user-questions-20260726/analyze_user_questions.py
```

## Definitions fixed before interpretation

### Artifact type rules

All classifications use workspace-relative paths and the following precedence.
The rules deliberately distinguish executable tests from test data, fixtures,
logs, and generated binaries.

1. **Test:** a file with a recognized code/script extension and either a
   canonical path segment (`test`, `tests`, `testing`, `__tests__`, `spec`, or
   `specs`) or a strict executable-test basename (`test_*`, `*_test`,
   `*_tests`, `*.test.*`, or `*.spec.*`). Benchmark, fixture, corpus, result,
   log, `__pycache__`, and extensionless binary paths are not tests merely
   because their path mentions testing.
2. **Paper/docs:** `README`, `CHANGELOG`, `LICENSE`, `CONTRIBUTING`, document
   extensions (`.md`, `.mdx`, `.rst`, `.adoc`, `.org`, `.txt`, `.tex`, `.bib`,
   `.typ`, `.pdf`), and image assets under a `paper` or `papers` path.
3. **Config:** recognized build/config names (`Cargo.toml`, `package.json`,
   `Makefile`, `pyproject.toml`, lock files, and similar), config extensions
   (`.toml`, `.yaml`, `.yml`, `.ini`, `.cfg`, `.lock`), then otherwise
   unclassified paths under `.github`, `.gitlab`, `.circleci`, `config`, or
   `ci`.
4. **Code:** recognized programming/script extensions, including C/C++, Rust,
   Python, JavaScript/TypeScript, shell, CSS/HTML, Go, Java, SQL, and related
   source formats. Code extensions take precedence over a generic `docs/`
   directory, so `docs/analyze.py` is code.
5. **Other:** data, result, figure, log, generated, binary, or otherwise
   unclassified files. In particular, `.json` is data/other unless its basename
   or path satisfies the preceding config rules. A generic `doc`, `docs`,
   `note`, or `research` path is a final paper/docs fallback only after
   recognizable code, config, and data/result extensions have been handled.
   Only unambiguous cache/dependency segments (`__pycache__`, `.pytest_cache`,
   and `node_modules`) override a source extension and remain other; generic
   names such as `output`, `result`, `build`, or `target` do not, because they
   can be real source modules.

Analysis A merges config and other into the requested four strata:
paper/docs, code, test, and other. Analyses B and D use the strict executable
test definition above. `classification-audit.csv` exposes 534 conflict
classifications spanning 503 paths: its action counts include 4,474
code-extension accesses under document
paths, 152 non-code accesses under test paths, 81 benchmark/fixture accesses,
and 94 paper-asset accesses; these are assigned by the stated precedence.
There are no confirmed-created artifacts whose nonempty final path changes
between the four A strata.

### Common event, episode, and pooling rules

- **Confirmed file action:** an event with `status=ok` and a file action with
  `scope=false`. Distinct file effects within one Tool event retain their
  action order, so create followed by delete in the same call counts as a
  post-create revisit. A failed or `observed` event does not create a confirmed
  lifecycle effect. `rename_from` helper records are excluded to avoid
  double-counting one rename.
- **Read/write action for C:** `read` is a read; `create`, `write`, `rename`,
  and `delete` are writes. C reports both the lifecycle-consistent `ok` primary
  view and an `ok+observed` attempt sensitivity because `observed` means the
  parser lacks a definite success/failure result, not that the action failed.
- **Artifact-mutation episode for D:** one
  `(project, worktree, artifact identity, Tool event)` group, matching the
  current RQ3 collapse. The 13,906 mutation rows collapse to 13,860 episodes.
  For the 46 compound create/delete groups, raw action order is checked against
  `action_ordinal`, and validation is evaluated from the last mutation.
- **Pairing episode for B:** within the same project, worktree, native session,
  source stream, prompt index, and module anchor, a strict normalized-basename
  match pairs `test_X.py` with `X.py`, `X_test.rs` with `X.rs`, or
  `X.test.ts` with `X.ts`. Ambiguous many-to-many stems are rejected. If no
  reliable basename pair exists, the conservative module fallback requires
  test and code mutation in the same Tool event; such an episode is a tie.
- **Module anchor:** the first path segment, except root-level generic
  `src`/`source`/`lib` and `test`/`tests`/`spec` roots, which map to
  `repo-root`. This makes `collector/src` and `collector/tests` co-module while
  keeping unrelated top-level components separate.
- **Validation association:** a recognized `effect=test,status=ok` event in the
  same worktree before that artifact's next mutation. It is temporal
  association only; it does not establish that the validation exercised the
  file, prove correctness, or measure test quality.
- **Summary:** `ALL_POOLED` rows are micro-weighted by artifacts, actions,
  episodes, or blocks as appropriate. They are not an average project and do
  not turn the six selected cases into a population estimate.

## A. Created artifacts that are never revisited

Eligibility is `birth_state=confirmed_create`. “Never revisited” means no
confirmed in-scope file effect after the create, including a later effect in
the same Tool event. Operationally, a revisit is a later event, any confirmed
read, or more than one confirmed mutation on that identity; “reread” means at
least one confirmed read after the create. The export contains no same-event
read ambiguity, and raw action order confirms the compound same-event cases.
`NR` is the never-revisited fraction and `RR` the later-reread fraction.

| Project | Paper/docs: n; NR; RR | Code: n; NR; RR | Test: n; NR; RR | Other: n; NR; RR |
|---|---:|---:|---:|---:|
| AgentSight | 923; 28.1%; 64.5% | 92; 10.9%; 77.2% | 12; 0.0%; 58.3% | 15; 53.3%; 6.7% |
| ActPlane | 81; 44.4%; 48.1% | 30; 13.3%; 83.3% | 2; 100.0%; 0.0% | 126; 10.3%; 80.2% |
| bpf-developer-tutorial | 18; 0.0%; 72.2% | 0; N/A | 0; N/A | 0; N/A |
| eunomia.dev | 26; 19.2%; 69.2% | 1; 0.0%; 0.0% | 0; N/A | 3; 33.3%; 66.7% |
| agentskill-observability-paper | 18; 100.0%; 0.0% | 0; N/A | 0; N/A | 0; N/A |
| academic-writing-skills | 0; N/A | 1; 0.0%; 100.0% | 0; N/A | 0; N/A |
| **ALL_POOLED** | **1,066; 29.8%; 62.4%** | **124; 11.3%; 78.2%** | **14; 14.3%; 50.0%** | **144; 15.3%; 72.2%** |

Across the 1,066 created paper/document artifacts, 318 (29.8%) had no later
confirmed action and 665 (62.4%) were later read. Created code was revisited
more often: 14/124 (11.3%) had no later confirmed action and 97/124 (78.2%)
were reread, a 15.8 percentage-point reread difference from documents.
Project behavior was heterogeneous: document reread ranged from 0/18 in
agentskill-observability-paper to 13/18 (72.2%) in
bpf-developer-tutorial. The export has no reliable flag for “this document was
required by an instruction,” so 62.4% is the answer for all created
paper/document artifacts and only a proxy for the specifically requested
subset; that semantic subset remains unidentified.

### For the paper (4 sentences)

> Across 1,066 observation-born paper and documentation artifacts, 29.8% had
> no later confirmed in-scope action and 62.4% were subsequently read. In
> comparison, 11.3% of 124 created code artifacts had no later confirmed action
> and 78.2% were subsequently read. The document reread fraction varied from
> 0% to 72.2% across the five cases with created documents, so the pooled rate
> does not describe a uniform practice. Because the export does not identify
> which documents were explicitly required by an instruction, these values
> describe all created documents rather than a causal effect of documentation
> requirements.

## B. Test-first or code-first

There are 28 eligible conservative pairs, all from AgentSight: 13 reliable
basename pairs and 15 same-Tool-event module fallbacks. No other project has an
eligible pair under these rules. Same-event fallbacks can only be tied and do
not manufacture an order from a broad module-level co-occurrence.

| Project | Eligible | Basename pair | Same-event fallback | Test first | Code first | Tied |
|---|---:|---:|---:|---:|---:|---:|
| AgentSight | 28 | 13 | 15 | 0 (0.0%) | 7 (25.0%) | 21 (75.0%) |
| ActPlane | 0 | 0 | 0 | 0 | 0 | 0 |
| bpf-developer-tutorial | 0 | 0 | 0 | 0 | 0 | 0 |
| eunomia.dev | 0 | 0 | 0 | 0 | 0 | 0 |
| agentskill-observability-paper | 0 | 0 | 0 | 0 | 0 | 0 |
| academic-writing-skills | 0 | 0 | 0 | 0 | 0 | 0 |
| **ALL_POOLED** | **28** | **13** | **15** | **0 (0.0%)** | **7 (25.0%)** | **21 (75.0%)** |

Among the 13 reliable basename pairs, seven were code-first and six tied; none
were test-first. The 15 fallback episodes all modified test and code artifacts
inside one Tool event and are therefore tied by construction. This supports a
narrow observation that the eligible AgentSight pairs were code-first or
co-modified, not a six-project estimate of development strategy. The full
paths, streams, prompts, pairing methods, and first event indices are in
`b-module-session-episodes.csv`.

### For the paper (4 sentences)

> Conservative source--test pairing yielded 28 mutation episodes, all in
> AgentSight: 13 unambiguous normalized-basename pairs and 15 same-event
> module fallbacks. Seven episodes (25.0%) modified source first, none modified
> the test first, and 21 (75.0%) modified both in the same Tool event. The
> same-event fallback intentionally avoids inferring order from temporally
> distant mutations in a broad module. Because five cases had no eligible
> pairs, this result is a within-case description rather than evidence that
> long-running Agents generally follow a code-first strategy.

## C. Artifact-type allocation of read and write actions

The tables report within-project shares in the fixed order
**paper/docs, code, test, config, other**. These are action counts, not elapsed
time or internal attention.

### Confirmed actions (`status=ok`)

| Project | Mode | n | Paper/docs | Code | Test | Config | Other |
|---|---|---:|---:|---:|---:|---:|---:|
| AgentSight | Read | 25,522 | 46.3% | 45.2% | 2.0% | 1.5% | 5.1% |
| AgentSight | Write | 6,588 | 72.1% | 22.5% | 1.6% | 0.3% | 3.5% |
| ActPlane | Read | 14,711 | 38.1% | 40.8% | 1.7% | 8.4% | 11.0% |
| ActPlane | Write | 5,849 | 61.5% | 12.2% | 0.1% | 21.1% | 5.1% |
| bpf-developer-tutorial | Read | 496 | 55.6% | 29.4% | 3.4% | 10.1% | 1.4% |
| bpf-developer-tutorial | Write | 283 | 98.9% | 0.0% | 0.0% | 1.1% | 0.0% |
| eunomia.dev | Read | 2,147 | 33.8% | 47.4% | 6.8% | 11.3% | 0.7% |
| eunomia.dev | Write | 739 | 85.4% | 7.6% | 1.8% | 2.4% | 2.8% |
| agentskill-observability-paper | Read | 242 | 99.6% | 0.0% | 0.0% | 0.4% | 0.0% |
| agentskill-observability-paper | Write | 196 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| academic-writing-skills | Read | 204 | 88.2% | 7.8% | 0.0% | 3.4% | 0.5% |
| academic-writing-skills | Write | 251 | 96.8% | 2.8% | 0.0% | 0.0% | 0.4% |
| **ALL_POOLED** | **Read** | **43,322** | **43.5%** | **43.2%** | **2.1%** | **4.4%** | **6.8%** |
| **ALL_POOLED** | **Write** | **13,906** | **69.8%** | **16.3%** | **0.9%** | **9.2%** | **4.0%** |

### Attempt sensitivity (`status=ok` or `observed`)

| Project | Mode | n | Paper/docs | Code | Test | Config | Other |
|---|---|---:|---:|---:|---:|---:|---:|
| AgentSight | Read | 25,548 | 46.3% | 45.2% | 2.0% | 1.5% | 5.1% |
| AgentSight | Write | 12,544 | 56.5% | 37.6% | 2.7% | 0.9% | 2.4% |
| ActPlane | Read | 14,720 | 38.1% | 40.8% | 1.7% | 8.4% | 11.0% |
| ActPlane | Write | 10,307 | 49.2% | 28.4% | 1.6% | 14.4% | 6.3% |
| bpf-developer-tutorial | Read | 496 | 55.6% | 29.4% | 3.4% | 10.1% | 1.4% |
| bpf-developer-tutorial | Write | 345 | 89.0% | 7.8% | 0.0% | 3.2% | 0.0% |
| eunomia.dev | Read | 2,149 | 33.8% | 47.4% | 6.8% | 11.3% | 0.7% |
| eunomia.dev | Write | 1,258 | 59.9% | 24.6% | 7.1% | 6.7% | 1.7% |
| agentskill-observability-paper | Read | 242 | 99.6% | 0.0% | 0.0% | 0.4% | 0.0% |
| agentskill-observability-paper | Write | 196 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| academic-writing-skills | Read | 208 | 88.5% | 7.7% | 0.0% | 3.4% | 0.5% |
| academic-writing-skills | Write | 252 | 96.8% | 2.8% | 0.0% | 0.0% | 0.4% |
| **ALL_POOLED** | **Read** | **43,363** | **43.5%** | **43.2%** | **2.1%** | **4.4%** | **6.8%** |
| **ALL_POOLED** | **Write** | **24,902** | **54.8%** | **32.1%** | **2.4%** | **6.8%** | **3.9%** |

The direct answer is that paper/document actions exceed code actions in the
pooled data, but the margin depends on mode and status. Confirmed reads are
nearly balanced (43.5% paper/docs versus 43.2% code), whereas confirmed writes
are document-heavy (69.8% versus 16.3%). Including `observed` attempts preserves
both directions while narrowing the write gap to 54.8% versus 32.1%; this
sensitivity matters because it adds 10,996 write-shaped attempts. At the
project level, ActPlane and eunomia.dev have more code than paper/document
reads, while all six projects have more paper/document than code writes under
both status views.

### For the paper (4 sentences)

> Confirmed read actions were nearly balanced between paper/document artifacts
> (43.5%) and code (43.2%), whereas confirmed writes were concentrated on
> paper/documents (69.8%) rather than code (16.3%). Including actions with an
> `observed` rather than definite status preserved these directions but reduced
> the write contrast to 54.8% versus 32.1%. ActPlane and eunomia.dev had more
> code than document reads, but all six cases had more document than code writes
> in both status views. These quantities count normalized file actions and do
> not estimate elapsed time, effort, importance, or progress.

## D. Test churn versus code churn

`R` is the fraction of artifact-mutation episodes after that identity's first
episode; `V` is the temporal validation-association fraction. The CSV also
reports episodes per mutated identity, the repeated-identity fraction, and all
three validation outcomes (`observed_validation`, `competing_supersede`, and
`censored_end`).

| Project | Test: identities/episodes; R; V | Code: identities/episodes; R; V |
|---|---:|---:|
| AgentSight | 24/99; 75.8%; 63.6% | 228/1,483; 84.6%; 47.1% |
| ActPlane | 4/4; 0.0%; 75.0% | 66/711; 90.7%; 52.9% |
| bpf-developer-tutorial | 0/0; N/A | 0/0; N/A |
| eunomia.dev | 5/13; 61.5%; 38.5% | 21/56; 62.5%; 42.9% |
| agentskill-observability-paper | 0/0; N/A | 0/0; N/A |
| academic-writing-skills | 0/0; N/A | 1/7; 85.7%; 28.6% |
| **ALL_POOLED** | **33/116; 71.6%; 61.2%** | **316/2,257; 86.0%; 48.7%** |

The global class totals do not by themselves establish relative stasis because
test and code episodes may occur in different tasks. The following paired
view therefore groups test-bearing blocks by the same project, worktree,
native session, source stream, prompt, and module. A “repeat-test block” has at
least one test identity mutated more than once inside that block; “repeat +
code zero” is the exact form of repeated test iteration with no source-code
mutation, without inventing a “large churn” threshold.

| Project | Test-bearing blocks | Code-zero blocks | Repeat-test blocks | Repeat + code zero | Repeat-test blocks with test > code | Maximum repeat-block test/code ratio | Test/code episodes | Median code episodes in repeat-test blocks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AgentSight | 24 | 1 | 14 | 0 | 1 | 2.0 | 99/466 | 7 |
| ActPlane | 3 | 2 | 0 | 0 | 0 | N/A | 4/1 | N/A |
| bpf-developer-tutorial | 0 | 0 | 0 | 0 | 0 | N/A | 0/0 | N/A |
| eunomia.dev | 4 | 2 | 2 | 0 | 0 | 0.6 | 13/26 | 13 |
| agentskill-observability-paper | 0 | 0 | 0 | 0 | 0 | N/A | 0/0 | N/A |
| academic-writing-skills | 0 | 0 | 0 | 0 | 0 | N/A | 0/0 | N/A |
| **ALL_POOLED** | **31** | **5** | **16** | **0** | **1** | **2.0** | **116/493** | **9** |

The observed data do not show the proposed pattern of repeatedly mutating a
test identity while source code remains untouched: none of 16 repeat-test
blocks had zero code episodes. Five of 31 test-bearing blocks had no code
mutation, but none repeated a test identity; six blocks had more test than code
episodes overall. Only one of the 16 repeat-test blocks had more test than
code episodes, and its counts were 2 versus 1 rather than a large test-only
loop. In the pooled artifact view, code had 2,257 episodes versus 116 for
tests and a higher repeat-episode fraction (86.0% versus 71.6%). Test episodes
had a higher temporal validation-association rate (61.2% versus 48.7%), but
this indicates only that a recognized successful validation occurred before
the artifact's next mutation.

### For the paper (4 sentences)

> We observed 116 executable-test mutation episodes and 2,257 source-code
> episodes, with repeat-episode fractions of 71.6% and 86.0%, respectively.
> Within 31 test-bearing stream--prompt--module blocks, 16 contained repeated
> mutation of a test identity, but none of those 16 had zero source-code
> episodes. Five blocks had no code mutation, yet none repeatedly mutated the
> same test identity; the only repeat-test block with more test than code
> episodes contained two versus one. Test episodes had a higher temporal
> association with a recognized successful validation (61.2% versus 48.7%),
> which does not imply
> that the validation exercised or established the quality of those files.

## Reconciliation and result judgment

The six event payloads reconcile to 181,303 Tool events. The action allocation
admits 57,228 confirmed read/write actions (43,322 reads and 13,906 writes) and
adds 11,037 `observed` attempts in sensitivity (41 reads and 10,996 writes).
The CSV bundle was regenerated twice in place. From the output directory, the
exact command `sha256sum *.csv | sha256sum` remained
`02c3bc7246adcdd0deb8a95c20e8432856d044e9bf9c3f2263c64248c460bf59`.
Output invariants independently verify 1,348 confirmed-created artifacts,
13,906 mutation rows, 13,860 artifact-mutation episodes, outcome-partition
reconciliation, B order totals, and zero repeat-test/code-zero blocks.

```text
run status: valid for the declared descriptive estimands
tested hypothesis: not applicable; B is data-limited to one project
research value: supporting
paper impact: additional user-question evidence for the supplement
next paper decision: report the descriptive answers and limitations; make no time, quality, progress, waste, or causal claim
```
