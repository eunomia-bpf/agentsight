# RQ7 Deterministic Matrix — Rerun at HEAD (2026-07-25)

Rerun of the frozen experiment-001 deterministic conformance matrix with the
**current HEAD** `agentvis`/`agent-session` projection (post-`69afb4866`
hardening) against the **same frozen data**
(`experiment-001/private/frozen-home`, `workspace`, `freeze.json`, cutoff
1784758608524). Frozen artifacts under `experiment-001/` were not modified.

## Method and caveats

1. HEAD binary (`agentvis/target/release/agentvis`, HEAD = `c47532d38`) was run
   as `research-rq1 --cutoff-ms 1784758608524 <6 roots>` with
   `HOME=experiment-001/private/frozen-home`, output in `projection/raw/`
   (this directory). Candidate recovery: **12/12 sessions for every project**
   (frozen run had eunomia.dev 6, academic-writing-skills 11).
2. HEAD traces changed two envelope semantics vs the frozen run:
   `session_id`/ordinals are per **native root** (subagent transcripts and
   continuation rollouts merge into their root), and codex roots prefer
   `parent_thread_id` over the rollout `id`. The frozen oracle's session model
   is per **source file**. The HEAD `deterministic` subcommand also cannot
   consume the v2 freeze (`semantic_session_id` KeyError). The matrix was
   therefore replayed as: **HEAD traces + the experiment's own answer layer**
   (`proposed_edges`/`relation_values`/`ArtifactTracker` from
   `rq7_measurement.py` @ `7e5464eca`, extracted read-only), with each HEAD
   event mapped to its frozen source session through the native call ledger
   (`call_id → source file`; 0 unmapped, 0 ambiguous across all 6 projects).
   Session ordinals and artifact identities thus use the frozen semantics; only
   the parser/projection behavior (what the fixes actually changed) varies.
3. Non-trajectory rows (procgrep/counts/final_state, 360 of 480) are
   byte-identical to the frozen `raw/method-results.csv` (verified: 0 changes);
   the rerun is written to `method-results.csv` / `rerun-rows.json` here.
4. As with any rerun, `git worktree list` state is read live from the six
   repositories; all worktree attributions matched the frozen target worktrees.

## Summary table (same format as experiment-001/result.md)

| Method | Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |
|---|---:|---:|---:|---:|---:|---:|
| final_state | A | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | B | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | C | 0 | 0 | 30 | 0.000 | 0.000 |
| final_state | D | 30 | 0 | 0 | 1.000 | 1.000 |
| counts | A | 7 | 11 | 12 | 0.233 | 0.389 |
| counts | B | 0 | 0 | 30 | 0.000 | 0.000 |
| counts | C | 0 | 0 | 30 | 0.000 | 0.000 |
| counts | D | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | A | 18 | 12 | 0 | 0.600 | 0.600 |
| procgrep | B | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | C | 0 | 0 | 30 | 0.000 | 0.000 |
| procgrep | D | 0 | 0 | 30 | 0.000 | 0.000 |
| trajectory | A | 18 | 12 | 0 | 0.600 | 0.600 |
| trajectory | B | 28 | 2 | 0 | 0.933 | 0.933 |
| trajectory | C | 23 | 7 | 0 | 0.767 | 0.767 |
| trajectory | D | 30 | 0 | 0 | 1.000 | 1.000 |

Frozen-run trajectory rows for comparison: B 16/30, C 16/30, D 28/30 (+2 abstain).

## Headline numbers

- **Trajectory B+C: 51/60 correct, 9/60 wrong, 60/60 answered** (frozen run:
  32/60, 28/60, 60/60).
- Per-project Trajectory B+C conditional accuracy:
  **agentsight=0.800, ActPlane=0.700, bpf-developer-tutorial=0.700,
  eunomia.dev=1.000, agentskill-observability-paper=1.000,
  academic-writing-skills=0.900**
  (frozen run: 1.000, 0.400, 0.700, 0.000, 0.600, 0.500).
- Trajectory − ProcGrep B+C contrast (per-project conditional-accuracy
  difference, project-block bootstrap, seed 20260722, 10k draws):
  **0.850, 95% interval [0.750, 0.950]** (frozen run: 0.533 [0.283, 0.767]).
- Trajectory D: **30/30** (frozen run 28/30 + 2 abstain; eunomia.dev D3/D5 are
  now answered and correct because the Claude sessions are present).

## Per-question diff vs the frozen run (31 changed trajectory rows)

| Question | frozen → HEAD | expected | now |
|---|---|---|---|
| eunomia.dev-B1 | 10 → 43 | 43 | FIXED |
| eunomia.dev-B2 | 0 → 32 | 32 | FIXED |
| eunomia.dev-B3 | 10 → 11 | 11 | FIXED |
| eunomia.dev-B4 | mutate → read | read | FIXED |
| eunomia.dev-B5 | 1 → 2 | 2 | FIXED |
| eunomia.dev-C1 | 0 → 1 | 1 | FIXED |
| eunomia.dev-C2 | 1 → 5 | 5 | FIXED |
| eunomia.dev-C3 | 0 → 1 | 1 | FIXED |
| eunomia.dev-C4 | 0 → 2 | 2 | FIXED |
| eunomia.dev-C5 | 3 → 17 | 17 | FIXED |
| eunomia.dev-D3 | abstain → tracked | tracked | FIXED (covered) |
| eunomia.dev-D5 | abstain → untracked | untracked | FIXED (covered) |
| ActPlane-B1 | 79 → 75 | 75 | FIXED |
| ActPlane-B2 | 28 → 22 | 22 | FIXED |
| ActPlane-B3 | 51 → 53 | 53 | FIXED |
| ActPlane-C5 | 17 → 12 | 4 | still wrong (narrower) |
| agentskill-observability-paper-B1 | 220 → 237 | 237 | FIXED |
| agentskill-observability-paper-B2 | 126 → 125 | 125 | FIXED |
| agentskill-observability-paper-B3 | 94 → 112 | 112 | FIXED |
| agentskill-observability-paper-C5 | 3 → 2 | 2 | FIXED |
| academic-writing-skills-B1 | 101 → 90 | 90 | FIXED |
| academic-writing-skills-B2 | 33 → 16 | 16 | FIXED |
| academic-writing-skills-B3 | 68 → 74 | 74 | FIXED |
| academic-writing-skills-C1 | 7 → 6 | 6 | FIXED |
| academic-writing-skills-C5 | 24 → 23 | 23 | FIXED |
| academic-writing-skills-C2 | 9 → 8 | 9 | NEW wrong (oracle-side) |
| bpf-developer-tutorial-C1 | 8 → 7 | 6 | still wrong (narrower) |
| bpf-developer-tutorial-C2 | 9 → 8 | 7 | still wrong (narrower) |
| bpf-developer-tutorial-C5 | 29 → 22 | 17 | still wrong (narrower) |
| agentsight-B1 | 21 → 22 | 21 | NEW wrong (oracle-side) |
| agentsight-B2 | 17 → 18 | 17 | NEW wrong (oracle-side) |

(ActPlane-C1 3/1 and ActPlane-C2 3/1 are unchanged and still wrong; 24 changed
rows became correct, 7 changed rows remain/become wrong, 2 wrong rows unchanged
→ 9 wrong rows total.)

## Answers to the verification questions

### Do the 14 genuine-bug rows now pass?

**Yes, all 14.** eunomia.dev B1–B5/C1–C5 (10 rows, session-join + sed
extraction), ActPlane-B3, agentskill-B1/B3, academic-B3 (fail-drop). None of
the noted residual risks materialized on these rows: the
`candidate_cwd_matches` fallback (agentvis/src/repository.rs:1002) recovered
every dotted/parent-dir session despite `encoded_claude_root` still not
replacing `.` (:1050-1052), and the rewritten sed operand extraction
(agent-session/src/parser.rs:1567) recovered all `.yaml`/`.tex` shell reads.

### Are exactly the 14 deliberate-design rows still wrong?

**No — 6 of the 14 persist, 8 were absorbed, and 3 new rows appeared.**
Persisting design rows: ActPlane-C1/C2/C5, bpf-C1/C2/C5 (HEAD still counts
redirection-segment, git-operand, and non-spec-command evidence the frozen
oracle excludes — e.g. 117 redir + 73 git + 642 JS-wrapper shell extras in
ActPlane). Absorbed: ActPlane-B1/B2, agentskill-B2/C5,
academic-B1/B2/C1/C5 — the `69afb4866` hardening narrowed the broader
extraction itself (ActPlane git-operand extras fell 434 → 73), bringing those
answers into exact agreement with the oracle. The design class is therefore
smaller at HEAD, not identical.

### New per-project B+C accuracy and coverage contrast

See headline numbers above: 0.800/0.700/0.700/1.000/1.000/0.900, contrast
0.850 [0.750, 0.950] vs frozen 0.533 [0.283, 0.767].

## The 9 remaining wrong rows — all (d) deliberate design or (f) oracle-side

| Row | HEAD vs frozen-expected | Class | Mechanism (evidence) |
|---|---|---|---|
| ActPlane-C1/C2/C5 | 3/1, 3/1, 12/4 | (d) + (f) | 1297 extra edges: 642 non-spec shell operands in codex exec JS wrappers, 465 apply_patch writes inside `const patch = "*** Begin Patch\n…"` JS strings the frozen oracle cannot parse, 117 redirection segments, 73 git operands |
| bpf-C1/C2/C5 | 7/6, 8/7, 22/17 | (f) + (d) | 18 extra edges: 15 exec-wrapper patch writes (real mutations invisible to the frozen oracle), 2 git, 1 redir. The 15 missing edges are all frozen-oracle sed-program artifacts (`s#^/…##`) in one session — no answer effect |
| academic-C2 | 8/9 | (f) + (d) | Frozen oracle resolves `cd third_party/openreviewer && cat README.md` against the session cwd (no inline-`cd` tracking), fabricating bare paths (`README.md`, `llm_training/generate.py`, …) that form a revisit; it also counts `rmdir` (not in the spec's MUTATORS) and resolves a `cd /tmp/…` create into the repo (`fake/docs/…`). HEAD resolves all of these correctly. 1 extra `git rm` delete (design) |
| agentsight-B1/B2 | 22/21, 18/17 | (f) | Frozen oracle's `plain_operands` (rq7_source_oracle_check.py @ `7e5464eca`, :306-318) unconditionally treats `-n`/`-c`/`-f`/`-e` as argument-taking for **every** command, so `cat -n collector/src/view/mod.rs` lost its only operand and the expected counts (21/17) are one read short. HEAD's 22/18 matches reality; the v3 checker's per-command arity table (:447-455) fixes this |

**No genuine projection bug remains in these 9 rows.** Every residual is
either the admitted broader shell/scope semantics or a frozen-oracle artifact.

## Remaining issues list (none genuine in the HEAD projection)

1. **Oracle-side, fixed in v3 checker:** `plain_operands` unconditional
   option-argument skip (`-n`/`-c`/`-f`/`-e`) — eats operands of `cat -n` and
   similar (agentsight-B1/B2 expected too low). Fixed by per-command arity in
   current `rq7_source_oracle_check.py:447-475`.
2. **Oracle-side, fixed in v3 checker:** sed program text counted as a path
   (`find … | sed 's#^DIR/##'`), 20 frozen edges; v3 checker returns no edge.
3. **Oracle-side, open in v3:** `unwrap_exec`
   (`rq7_source_oracle_check.py:159-200`) cannot evaluate codex exec JS string
   variables, so real apply_patch mutations inside
   `const patch = "*** Begin Patch\n…"` wrappers are missed (ActPlane ~465,
   bpf 15 edges). Drives ActPlane/bpf C-family residuals; affects any future
   freeze's expected values.
4. **Oracle-side, open in v3:** no inline-`cd` tracking in shell path
   resolution (`repo_path`, :563-575) — relative operands after `cd dir &&`
   resolve against the session cwd, fabricating wrong-repo-root paths
   (academic-C2); `rmdir` accepted as a mutator by the old oracle although the
   spec's MUTATORS = {touch, rm, mv, cp}.
5. **Projection, latent:** `encoded_claude_root`
   (`agentvis/src/repository.rs:1050-1052`) still only replaces `/`; Claude
   transcripts without cwd rows would still be dropped for dotted roots. The
   `plausible_path_token` suffix whitelist / 140-char cap
   (`agent-session/src/parser.rs`) still guards non-sed shell extraction —
   spot-check `cat Makefile`-style bare operands before the next freeze.

## Reproduction

- `projection/raw/` — HEAD `research-rq1` output (traces, projects.json).
- `method-results.csv`, `rerun-rows.json` — 480-row matrix at HEAD.
- `scripts/rerun_head2.py` — matrix replay (HEAD traces + frozen answer layer,
  call-ledger session join); `scripts/summarize_head.py` — tables + residual
  edge diff; `scripts/head_buckets.py` — residual edge bucketing.
- Frozen comparison: `experiment-001/raw/method-results.csv` (untouched).
