# RQ7 Error Taxonomy — 28 wrong trajectory answers (B/C families)

Date: 2026-07-25
Experiment: `docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/`
Code under audit: `agentvis` + `agent-session` at experiment revision `56fc7d6d`
(trajectory projection), experiment-time oracle embedded in `private/freeze.json`
(`oracle_edges`, self-consistent with `rq7_source_oracle_check.py` @ `7e5464eca`).

## Method

1. Re-extracted the 28 wrong rows from `raw/method-results.csv`
   (`awk -F, '$5=="trajectory" && ($3=="B"||$3=="C") && $11==1'`) — matches the
   task list exactly (28 rows, 5 projects; agentsight has zero wrong B/C answers).
2. Re-ran the experiment-time trajectory computation
   (`proposed_edges` + `relation_values` from `rq7_measurement.py` @ `7e5464eca`,
   extracted read-only to a scratch dir) over the frozen projection intermediates
   (`private/deterministic/projection/raw/events/*.json`). It reproduces **all 28
   wrong answers exactly**, so the audited pipeline is the one that produced the
   results.
3. Diffed production edges against the frozen `oracle_edges` keyed by
   `(session_id, call_id, path, access)`, mapped every divergent edge back to its
   native source row in `private/frozen-home/`, and bucketed the mechanism.
4. Attributed each wrong answer causally: P0-path edge decomposition for B1–B5,
   and counterfactual recomputation of `relation_values` with each extra-edge
   bucket removed (and oracle sed-program artifacts removed) for C1–C5.
   Scripts preserved in `scripts/` (diff_analysis.py, bucket.py, attribute.py,
   drill2.py, drill3.py, evidence.py).

## Taxonomy classes

- **(a) path-extraction bug** — projection drops real spec-eligible shell paths.
- **(b) attempted-action bug** — projection drops actions of failed tool calls
  (spec: "Tool invocations are attempted actions regardless of result status").
- **(c) native-root/session-join bug** — projection drops whole sessions at the
  candidate filter.
- **(d) deliberate broader shell/scope design** — projection intentionally counts
  evidence the frozen oracle excludes (git operands, redirection/heredoc
  segments, operands of non-spec commands such as grep/rg/wc/ls/find/make).
- **(e) action-grammar drift** — label drift with no answer impact
  (Write → `create` oracle vs `write` production; both are `mutate`).
- **(f) oracle-side artifact** — frozen oracle counts sed program text as a path,
  and cannot see apply_patch headers inside codex exec JS string wrappers.

## The 28 rows

| # | Question | traj/exp | Primary | Secondary | Evidence |
|---|----------|----------|---------|-----------|----------|
| 1 | ActPlane-B1 | 79/75 | (d) broader design (+6: 4 `git diff/status/log`, 2 grep reads on P0) | (b) fail-drop −2 | P0 extra {E-git 4, E-nonspec 2}, missing {M-fail 2}; cf. `git status docs/papers/sections/01-introduction.tex` counted as read |
| 2 | ActPlane-B2 | 28/22 | (d) broader design (+6 reads) | — | removing all extra edges → 22 exactly |
| 3 | ActPlane-B3 | 51/53 | (b) fail-drop (−2) | — | failed `Edit` on `docs/papers/main.tex`, failed `Read` on PDF: trace `status=fail, actions=[]` |
| 4 | ActPlane-C1 | 3/1 | (d) broader design | — | removing all extra edges → 1 exactly |
| 5 | ActPlane-C2 | 3/1 | (d) broader design | — | removing all extra edges → 1 exactly |
| 6 | ActPlane-C5 | 17/4 | (d) broader design | — | removing all extra edges → 4 exactly (E-nonspec −4, E-redir −2, E-git −1, rest combined) |
| 7 | bpf-developer-tutorial-C1 | 8/6 | (d) broader design | — | removing all extra edges → 6 exactly (E-nonspec −1, rest combined) |
| 8 | bpf-developer-tutorial-C2 | 9/7 | (d) broader design | — | removing all extra edges → 7 exactly |
| 9 | bpf-developer-tutorial-C5 | 29/17 | (d) broader design (+12 gross) | (a)/(b) missing-edge residual −1 | removing extras → 16 vs expected 17: one legit multi-session artifact lost to M-fail/M-sedext edges |
| 10 | eunomia.dev-B1 | 10/43 | (a) sed/ext filter (−26) | (c) candidate-drop (−7) | P0 missing {M-sedext 26, M-cand 7}; `sed -n '1,280p' mkdocs.yaml` → trace `actions: []` |
| 11 | eunomia.dev-B2 | 0/32 | (a) sed/ext filter (−26 reads) | (c) candidate-drop (−6 reads) | all shell reads of `mkdocs.yaml` dropped: bare filename, `.yaml` not in `plausible_path_token` suffix whitelist, no `/` |
| 12 | eunomia.dev-B3 | 10/11 | (c) candidate-drop (−1 mutation) | — | the one missing mutation is in dropped Claude session `b908e505…` |
| 13 | eunomia.dev-B4 | mutate/read | (a) sed/ext filter | (c) candidate-drop | every early P0 read is a `sed`/`nl` shell read dropped by the filter, so the first surviving P0 edge is an apply_patch write |
| 14 | eunomia.dev-B5 | 1/2 | (c) candidate-drop | — | P0's second session (Claude `b908e505…`) absent from trace |
| 15 | eunomia.dev-C1 | 0/1 | (c) candidate-drop | — | the P0-sharing adjacent pair involves dropped session ordinal 2 |
| 16 | eunomia.dev-C2 | 1/5 | (c) candidate-drop (−4) | (d) broader design (+1) | removing extras → 0; the 4 missing revisits live in the 6 dropped Claude sessions |
| 17 | eunomia.dev-C3 | 0/1 | (c) candidate-drop | — | P0 return episode spans dropped session |
| 18 | eunomia.dev-C4 | 0/2 | (c) candidate-drop | — | P0 last-first ordinal gap collapses when session 2 vanishes |
| 19 | eunomia.dev-C5 | 3/17 | (c) candidate-drop (−17 vs oracle) | (d) broader design (+3: all 3 surviving multi-session artifacts come from extra edges) | removing extras → 0 |
| 20 | agentskill-observability-paper-B1 | 220/237 | (b) fail-drop (−18) | (a) sed/ext filter (−8), (d) broader design (+9) | P0 missing {M-fail 18, M-sedext 8}, extra {E-nonspec 8, E-git 1} |
| 21 | agentskill-observability-paper-B2 | 126/125 | (d) broader design (+9 reads: grep/wc on paper.tex/references.bib, 1 `git add`) | (a) sed/ext filter (−8 reads) | net +1; `sed -n '/\\begin{abstract}/,/\\end{abstract}/p' paper.tex` dropped (`paper.tex` fails suffix whitelist) |
| 22 | agentskill-observability-paper-B3 | 94/112 | (b) fail-drop (−18 exactly) | — | 18 failed `Edit` calls on `docs/paper/paper.tex` with `actions: []` |
| 23 | agentskill-observability-paper-C5 | 3/2 | (d) broader design (+1 exactly) | — | removing E-nonspec → 2 exactly |
| 24 | academic-writing-skills-B1 | 101/90 | (d) broader design (+17: 8 git, 7 grep/wc/ls, 2 redir) | (b) fail-drop (−6) | P0 extra {E-git 8, E-nonspec 7, E-redir 2}, missing {M-fail 6} |
| 25 | academic-writing-skills-B2 | 33/16 | (d) broader design (+17 exactly) | — | removing all extra edges → 16 exactly |
| 26 | academic-writing-skills-B3 | 68/74 | (b) fail-drop (−6 exactly) | — | e.g. failed `Edit` on `skills/iter-refine-ideas/SKILL.md` |
| 27 | academic-writing-skills-C1 | 7/6 | (d) broader design (+1 exactly, E-git) | — | removing E-git → 6 exactly |
| 28 | academic-writing-skills-C5 | 24/23 | (d) broader design (+1) | — | removing all extra edges → 23 exactly; bogus artifact `master..docs/no-default-worktree` (git rev-range token counted as path) among extras |

Primary-class counts (28 rows): **(d) deliberate broader design 14** ·
**(c) native-root/session-join 7** · **(b) attempted-action/fail-drop 4** ·
**(a) path-extraction 3**. Secondary contributions: (a) ×3, (b) ×2, (c) ×2,
(d) ×2. No row is primarily oracle-side; no row is UNRESOLVED.

## Root causes (genuine bugs)

### BUG-A — native-root/session-join: Claude candidate filter drops sessions (class c)

Experiment-revision `agentvis/src/repository.rs:467-475` (`candidate_may_match_repo`,
AGENT_CLAUDE arm) matched a Claude transcript to a repository **only** by
comparing its `~/.claude/projects/<dir>` name against
`encoded_claude_root(root)` (`agentvis/src/repository.rs:500-502`), which is
`root.replace('/', "-")`. Claude Code's real encoding also replaces `.` with `-`,
so for `/home/yunwei37/workspace/eunomia.dev` the projection computed
`-home-yunwei37-workspace-eunomia.dev` while the actual directory is
`-home-yunwei37-workspace-eunomia-dev` — **no match, and there was no cwd
fallback**. All 6 frozen Claude sessions for eunomia.dev (580 tool calls,
207 oracle edges) were dropped before parsing; the trace reports
`candidate_sessions: 6, all codex` (`projects.json`). The same defect dropped one
academic-writing-skills subagent session filed under the **parent** project dir
`-home-yunwei37-workspace-my-paper-work` (`agent-aae2948544d296d41`, 20 tool
calls) — zero spec-eligible edges, so no answer impact, but a live instance.

Verified directly: `rg` discovery finds the files and their `cwd` fields name
the worktree; the filter just never looked at file content.

**Status in HEAD:** fixed by `candidate_cwd_matches` (`agentvis/src/repository.rs:1002`,
with regression test `claude_candidate_cwd_handles_dotted_repository_names` at
:1433) added in `69afb4866`. Re-running `research-rq1` (HEAD) on the frozen home
yields 12 eunomia.dev candidates (6 claude + 6 codex) and **43 mkdocs.yaml
actions (32 read / 11 write) — exactly the expected B1/B2/B3**. Caveat:
`encoded_claude_root` itself still only replaces `/`; the fix relies on cwd
content, so transcripts with no cwd rows would still be dropped.

### BUG-B — attempted-action semantics: failed tool calls lose all actions (class b)

Experiment-revision `agentvis/src/repository.rs:363`:
`let actions = if tool.status == "fail" { BTreeSet::new() } else { … }`.
The frozen spec says tool invocations are attempted actions regardless of result
status, and the oracle counts them. The projection emitted the event with
`status: "fail", actions: []`, so every failed Edit/Write/Read/shell mutation
vanished from the artifact ledger. Evidence: 18 failed `Edit` calls on
`docs/paper/paper.tex` (agentskill B3 = 94 vs 112, exactly −18), 6 failed edits
(academic B3 = 68 vs 74, exactly −6), 2 failed calls (ActPlane B3 = 51 vs 53).
**Status in HEAD:** fixed in `69afb4866` (the fail branch was removed).

### BUG-C — path-extraction: `plausible_path_token` suffix whitelist + length cap (class a)

Experiment-revision `agent-session/src/parser.rs` (`plausible_path_token`,
~:2125-2165; sed arm ~:1570) accepts a shell path token only if it contains `/`
or ends in one of `{rs,py,md,json,ts,tsx,toml,lock,js,c,h,svg,html,css}`, and
rejects tokens > 140 chars. Consequences observed in the frozen trace
(`actions: []` on the corresponding events):

- `sed -n '1,280p' mkdocs.yaml` — bare `mkdocs.yaml` has `.yaml` (not
  whitelisted) and no `/`: **all 26 shell reads of P0 dropped** (eunomia.dev
  B1/B2/B4). Same mechanism: `sed -n '1,220p' .gitmodules` (bpf),
  `sed -n … paper.tex` reads (agentskill, 8 edges).
- `sed -n '1,90p' /home/yunwei37/workspace/ActPlane/docs/corpus-evaluated/…/README.md`
  — 143-char absolute path exceeds the 140-char cap (ActPlane, 4 edges).

**Status in HEAD:** the sed path was rewritten (arity-table driven operand
skipping, `agent-session/src/parser.rs:1567`); the HEAD re-run recovers all 32
mkdocs.yaml reads. The whitelist/length cap in `plausible_path_token` itself is
unchanged in HEAD — spot-check bare-name operands of other commands
(`cat Makefile`, `head file.yaml`) before trusting HEAD fully.

### Oracle-side artifacts (class f) — latent, zero impact on the 28

- **Sed-program-as-path:** the experiment-time oracle
  (`rq7_source_oracle_check.py` @ `7e5464eca`, 629 lines) parsed
  `find DIR … | sed 's#^DIR/##' | sort` as a **read on the literal program text**
  `s#^DIR/##`, fabricating repo-internal artifacts (bpf 15 edges, ActPlane 3,
  eunomia 2 — some from directories *outside* the worktree). The production
  projection instead recorded a directory-scope read (filtered out by
  `proposed_edges`). Verified: the current checker (spec
  `native-root-conformance-v3`) returns no edge for these commands; the frozen
  expected answers embed the old behavior. Counterfactual: removing every
  `s#…` artifact from the oracle changes **none** of the 28 expected values
  (they are all single-session artifacts), so no row is oracle-caused — but any
  future freeze must be regenerated with the v3 checker.
- **Exec-wrapper patches:** codex `exec` calls carrying
  `const patch = "*** Begin Patch\n*** Update File: …"` (JS string with escaped
  `\n`) are invisible to the frozen oracle (`unwrap_exec` cannot evaluate the JS
  variable; `PATCH_RE` needs real newlines), while the production parser
  correctly unescapes and counts them (ActPlane: 428 edges). These are real
  mutations the oracle misses; they affect none of the 28 answers (all on
  non-P0, single-session artifacts). The current v3 checker still cannot see
  them.

### Grammar drift (class e) — no answer impact

The oracle maps the `Write`/`write_file` tools to `create`, the projection to
`write` (agentskill 11 pairs, bpf 7 pairs of identical (session, call, path)
edges differing only in access label). Both are `mutate`, so B/C answers are
unaffected; it inflates edge-level conformance diffs only.

## Class summary

| Class | Primary rows | Rows touched (incl. secondary) | Nature |
|-------|--------------|-------------------------------|--------|
| (d) deliberate broader shell/scope design | 14 | 16 | admitted projection semantics; RQ7 quantifies the inflation (C5 up to 17 vs 4) |
| (c) native-root/session-join (BUG-A) | 7 | 9 | genuine bug, fixed in HEAD |
| (b) attempted-action/fail-drop (BUG-B) | 4 | 6 | genuine bug, fixed in HEAD |
| (a) path-extraction filter (BUG-C) | 3 | 6 | genuine bug, sed path fixed in HEAD; whitelist/length cap remain |
| (f) oracle-side artifact | 0 | 0 answers; 20 latent edges | frozen-oracle defects; sed case fixed in v3 checker, exec-wrapper patch case open |
| (e) action-grammar drift | 0 | 0 | cosmetic |

## Bug-fix list, ordered by impact

1. **BUG-A candidate filter** (`agentvis/src/repository.rs:467-475,500-502` @
   `56fc7d6d`; fixed at HEAD :1002). Explains all 10 eunomia.dev rows (7
   primary, plus secondary on B1/B2) — the project's B+C conditional accuracy
   was 0.000. Also make `encoded_claude_root` replace `.` (and other Claude
   encoding rules) so the cheap path check works without the cwd fallback.
2. **BUG-B fail-drop** (`agentvis/src/repository.rs:363` @ `56fc7d6d`; fixed in
   `69afb4866`). Primary in 4 rows, secondary in 2; systematically undercounts
   attempted mutations (largest single effect: −18 on agentskill B3).
3. **BUG-C extraction filter** (`agent-session/src/parser.rs`
   `plausible_path_token` + sed arm; sed fixed at HEAD :1567). Primary in 3
   rows, secondary in 3; drops reads of `.yaml`/`.tex`/extension-less bare
   filenames and >140-char paths. Finish the job: drop the suffix whitelist and
   length cap for operand positions of known file commands.
4. **Oracle-side (f)**: regenerate any future freeze with the v3 checker
   (sed-program artifact already fixed there); extend the checker's
   `unwrap_exec` to resolve simple `const var = "…"; …exec_command({cmd: var})`
   wrappers so real patch writes are not missed.

## Impact on RQ1–RQ4 (shared projection)

`docs/evaluation.md` states RQ1, RQ3, RQ4 need this taxonomy and RQ2 needs it
"where mutation linkage matters". Concretely:

- **BUG-A (c):** any RQ1–RQ4 quantity for a repository whose path contains `.`
  (eunomia.dev) or whose sessions are filed under a parent Claude project dir
  is computed from a session subset: 6 of 12 sessions and 580 tool calls
  invisible for eunomia.dev. Session counts, vendor mix (Claude share biased to
  zero for dotted repos), cross-session artifact sharing, revisit/return
  episodes, and per-project longitudinal rankings are all distorted.
- **BUG-B (b):** attempted-but-failed edits/reads vanish — RQ1 mutation/attempt
  counts are biased low and RQ2 mutation linkage loses edges (agentskill P0
  mutations −16%).
- **BUG-C (a):** shell reads of non-whitelisted bare filenames
  (`mkdocs.yaml`, `paper.tex`, `Makefile`, `.gitmodules`) and long paths vanish —
  read:mutate ratios, first-action-class statistics, and artifact popularity
  rankings are biased toward mutations and toward structured-tool usage.
- **(d) broader design:** RQ1–RQ4 quantities that use the projection's shell
  evidence (cross-session sharing C1/C2/C5 analogues, read counts) are inflated
  relative to the source-direct spec — by design, not by bug; RQ7 quantifies the
  gap (C5: 17 vs 4 ActPlane, 29 vs 17 bpf; B2 reads +6..+17 where git/grep
  operands are counted). These rows of the 28 do **not** indicate RQ1–RQ4
  defects; they indicate the projection and the oracle measure different things.
- **(f) oracle-side:** no effect on the 28 expected values; future freezes must
  use the v3 checker.

Bottom line: 14 of 28 errors are the admitted broader shell/scope semantics the
audit was meant to separate; 14 are genuine bugs (7 session-join, 4 fail-drop,
3 path-extraction), all three bug classes already fixed at HEAD, with the HEAD
re-run reproducing the expected eunomia.dev B1/B2/B3 exactly.

## Reproduction

- `scripts/diff_analysis.py` — replays experiment-time `proposed_edges` +
  `relation_values`; reproduces all 28 wrong answers and the edge-level diff
  (saves `diff.pkl`).
- `scripts/bucket.py` — buckets every divergent edge by mechanism (`buckets.pkl`).
- `scripts/attribute.py` — per-question decomposition + counterfactuals
  (output quoted in the table above).
- `scripts/drill2.py`, `scripts/drill3.py`, `scripts/evidence.py` — native-row
  evidence for each mechanism.
- HEAD check: `HOME=<exp>/private/frozen-home agentvis/target/release/agentvis
  research-rq1 --output <tmp> --cutoff-ms 1784758608524 <6 roots>` → eunomia.dev
  12 candidates (6 claude + 6 codex); mkdocs.yaml 43 actions (32 read / 11 write).
- Neither `agentvis/research/rq7_measurement.py` nor
  `agentvis/research/rq7_source_oracle_check.py` was modified; the
  experiment-time code was extracted read-only from git revs `7e5464eca` /
  `56fc7d6d` into a scratch directory for replay.
